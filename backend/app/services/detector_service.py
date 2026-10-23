"""
SMART ECO BIN — Multi-Object Waste Detection Engine
===================================================
Provides modular, decoupled object detection for photographs containing multiple
mixed waste items. Extracts individual bounding boxes, confidence scores, and
class labels while preserving original image aspect ratios and coordinates.

Design & Architectural Invariants:
- Zero fake detections: If model weights are not configured, reports status honestly.
- Singleton pattern: Model weights are loaded once into CPU/GPU memory and reused.
- Resilient image processing: Rejects corrupted, oversized, or non-image payloads safely.
- Pluggable backends: Supports Ultralytics YOLO, TorchVision Faster-RCNN/SSDLite, or custom PyTorch.
- Testable: Supports backend substitution for deterministic unit testing.
"""

import os
import io
import logging
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import torch

from app.models.schemas import BoundingBox, ObjectDetectionItem, DetectionSummary, WasteDetectionResponse
from app.services.waste_routing_service import waste_routing_service

logger = logging.getLogger("ecosort.detector")

DEFAULT_CONFIDENCE_THRESHOLD = float(os.getenv("DETECTION_CONFIDENCE_THRESHOLD", "0.25"))
DEFAULT_IOU_THRESHOLD = float(os.getenv("DETECTION_IOU_THRESHOLD", "0.45"))


class BaseDetectorBackend:
    """Abstract interface for object detection backends."""

    def is_available(self) -> bool:
        raise NotImplementedError

    def detect(
        self,
        image: Image.Image,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45
    ) -> List[Dict[str, Any]]:
        """
        Runs inference on PIL Image and returns list of detections:
        [
            {
                "label": "cardboard_box",
                "confidence": 0.94,
                "bbox": {"x1": 120.0, "y1": 80.0, "x2": 360.0, "y2": 280.0},
                "mask": None
            }, ...
        ]
        """
        raise NotImplementedError

    def get_model_info(self) -> Dict[str, Any]:
        return {"backend": "base", "model_type": "abstract"}


class UltralyticsYOLOBackend(BaseDetectorBackend):
    """
    Ultralytics YOLO backend for real waste-object detection.
    Loads fine-tuned YOLO weights (e.g., trained on TACO or ZeroWaste).
    """

    def __init__(self, weights_path: str, device: str = "cpu"):
        self.weights_path = weights_path
        self.device = device
        self.model = None
        self._load()

    def _load(self):
        try:
            from ultralytics import YOLO
            if os.path.exists(self.weights_path):
                self.model = YOLO(self.weights_path)
                logger.info(f"Ultralytics YOLO model loaded from {self.weights_path} onto {self.device}.")
            else:
                logger.warning(f"Ultralytics YOLO weights path does not exist: {self.weights_path}")
                self.model = None
        except ImportError:
            logger.debug("Ultralytics library not installed in current environment.")
            self.model = None
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None

    def is_available(self) -> bool:
        return self.model is not None

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "backend": "ultralytics_yolo",
            "weights_path": os.path.basename(self.weights_path) if self.weights_path else None,
            "device": self.device,
            "classes": getattr(self.model, "names", {}) if self.model else {}
        }

    def detect(
        self,
        image: Image.Image,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45
    ) -> List[Dict[str, Any]]:
        if not self.is_available():
            return []

        results = self.model.predict(
            source=image,
            conf=conf_threshold,
            iou=iou_threshold,
            device=self.device,
            verbose=False
        )

        detections = []
        if not results:
            return detections

        first_res = results[0]
        boxes = first_res.boxes
        if boxes is None or len(boxes) == 0:
            return detections

        names = getattr(self.model, "names", {})

        for box in boxes:
            xyxy = box.xyxy[0].tolist()
            conf = float(box.conf[0].item())
            cls_id = int(box.cls[0].item())
            label = names.get(cls_id, f"class_{cls_id}")

            detections.append({
                "label": label,
                "confidence": round(conf, 4),
                "bbox": {
                    "x1": round(xyxy[0], 1),
                    "y1": round(xyxy[1], 1),
                    "x2": round(xyxy[2], 1),
                    "y2": round(xyxy[3], 1)
                },
                "mask": None
            })

        return detections


class TorchVisionDetectorBackend(BaseDetectorBackend):
    """
    TorchVision detection backend (e.g., SSDLite320-MobileNetV3 or Faster-RCNN).
    Loads native PyTorch state dicts (.pt / .pth) and runs evaluation on CPU/CUDA.
    """

    def __init__(self, weights_path: str, device: str = "cpu"):
        self.weights_path = weights_path
        self.device = device
        self.model = None
        self.classes: List[str] = []
        self._load()

    def _load(self):
        try:
            import torchvision.models.detection as d
            if not os.path.exists(self.weights_path):
                logger.warning(f"TorchVision weights path does not exist: {self.weights_path}")
                self.model = None
                return

            try:
                # Attempt safe weights-only loading if supported by checkpoint format
                checkpoint = torch.load(self.weights_path, map_location=self.device, weights_only=True)
            except Exception:
                # Fallback to full object deserialization for legacy TorchVision bundled model module
                checkpoint = torch.load(self.weights_path, map_location=self.device, weights_only=False)
            # Support structured checkpoint dict, direct state_dict, or pickled nn.Module
            if isinstance(checkpoint, dict) and "model" in checkpoint and hasattr(checkpoint["model"], "eval"):
                self.model = checkpoint["model"]
                self.classes = checkpoint.get("classes", [])
                self.model.to(self.device).eval()
                if not self.classes:
                    self.classes = d.SSDLite320_MobileNet_V3_Large_Weights.COCO_V1.meta.get("categories", [])
                logger.info(f"TorchVision model module loaded directly from checkpoint['model'].")
                return
            elif isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                arch = checkpoint.get("architecture", "ssdlite320_mobilenet_v3_large")
                num_classes = checkpoint.get("num_classes", 91)
                self.classes = checkpoint.get("classes", [])
                state_dict = checkpoint["model_state_dict"]
            elif isinstance(checkpoint, dict) and any(k.startswith("backbone.") or k.startswith("head.") or k.startswith("rpn.") for k in checkpoint.keys()):
                arch = "ssdlite320_mobilenet_v3_large"
                num_classes = 91
                self.classes = d.SSDLite320_MobileNet_V3_Large_Weights.COCO_V1.meta.get("categories", [])
                state_dict = checkpoint
            elif hasattr(checkpoint, "eval"):
                self.model = checkpoint
                self.model.to(self.device).eval()
                self.classes = getattr(self.model, "classes", d.SSDLite320_MobileNet_V3_Large_Weights.COCO_V1.meta.get("categories", []))
                logger.info(f"TorchVision model module loaded directly from {self.weights_path}.")
                return
            else:
                arch = "ssdlite320_mobilenet_v3_large"
                num_classes = 91
                self.classes = d.SSDLite320_MobileNet_V3_Large_Weights.COCO_V1.meta.get("categories", [])
                state_dict = checkpoint

            if not self.classes:
                try:
                    self.classes = d.SSDLite320_MobileNet_V3_Large_Weights.COCO_V1.meta.get("categories", [])
                except Exception:
                    self.classes = [f"class_{i}" for i in range(num_classes)]

            if "fasterrcnn" in arch.lower():
                self.model = d.fasterrcnn_mobilenet_v3_large_320_fpn(num_classes=num_classes)
            else:
                self.model = d.ssdlite320_mobilenet_v3_large(num_classes=num_classes)

            self.model.load_state_dict(state_dict)
            self.model.to(self.device).eval()
            logger.info(f"TorchVision {arch} detector loaded from {self.weights_path} onto {self.device}.")
        except Exception as e:
            logger.error(f"Failed to load TorchVision detector from {self.weights_path}: {e}")
            self.model = None

    def is_available(self) -> bool:
        return self.model is not None

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "backend": "torchvision_detector",
            "weights_path": os.path.basename(self.weights_path) if self.weights_path else None,
            "device": self.device,
            "architecture": "ssdlite320_mobilenet_v3_large",
            "num_classes": len(self.classes) if self.classes else 91
        }

    def detect(
        self,
        image: Image.Image,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45
    ) -> List[Dict[str, Any]]:
        if not self.is_available():
            return []

        import torchvision.transforms.functional as F
        import torchvision.ops as ops

        img_tensor = F.to_tensor(image).to(self.device)
        with torch.no_grad():
            predictions = self.model([img_tensor])[0]

        boxes = predictions["boxes"].cpu()
        scores = predictions["scores"].cpu()
        labels = predictions["labels"].cpu()

        # Filter by conf_threshold
        mask = scores >= conf_threshold
        boxes = boxes[mask]
        scores = scores[mask]
        labels = labels[mask]

        if len(boxes) == 0:
            return []

        # Apply NMS if iou_threshold provided
        if iou_threshold > 0 and len(boxes) > 1:
            keep = ops.nms(boxes, scores, iou_threshold)
            boxes = boxes[keep]
            scores = scores[keep]
            labels = labels[keep]

        detections = []
        for box, score, label_id in zip(boxes, scores, labels):
            lid = int(label_id.item())
            class_name = self.classes[lid] if (self.classes and lid < len(self.classes)) else f"class_{lid}"
            if class_name in ("__background__", "N/A"):
                continue

            xyxy = box.tolist()
            detections.append({
                "label": class_name,
                "confidence": round(float(score.item()), 4),
                "bbox": {
                    "x1": round(xyxy[0], 1),
                    "y1": round(xyxy[1], 1),
                    "x2": round(xyxy[2], 1),
                    "y2": round(xyxy[3], 1)
                },
                "mask": None
            })

        return detections


class WasteDetectorService:
    """
    Central Multi-Object Detection Service with explicit configuration,
    dimension validation, coordinate normalization, and waste disposal routing.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(WasteDetectorService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_path: Optional[str] = None):
        if getattr(self, "_initialized", False):
            return

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.confidence_threshold = DEFAULT_CONFIDENCE_THRESHOLD
        self.iou_threshold = DEFAULT_IOU_THRESHOLD
        self.backend: Optional[BaseDetectorBackend] = None
        self.model_status = "not_configured"
        self.model_path = model_path or os.getenv("WASTE_DETECTOR_MODEL_PATH")

        # Discover default weights paths
        if not self.model_path:
            candidate_paths = [
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "model", "waste_detector.pt"),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "model", "waste_detector.pth"),
                "ml/model/waste_detector.pt",
                "ml/model/waste_detector.pth"
            ]
            for p in candidate_paths:
                if os.path.exists(p):
                    self.model_path = os.path.abspath(p)
                    break

        if self.model_path and os.path.exists(self.model_path):
            self._init_real_backend(self.model_path)
        else:
            self.model_status = "not_configured"
            logger.info("Waste detector weights not found. Service initialized in unconfigured mode.")

        self._initialized = True

    def _init_real_backend(self, weights_path: str):
        """Initializes compatible detection backend with found weights."""
        # 1. Try native TorchVision backend (standard PyTorch .pt state dict)
        try:
            tv_backend = TorchVisionDetectorBackend(weights_path, device=self.device)
            if tv_backend.is_available():
                self.backend = tv_backend
                self.model_status = "loaded"
                logger.info(f"Waste detector loaded with TorchVision backend: {weights_path}")
                return
        except Exception as e:
            logger.debug(f"TorchVision backend could not load {weights_path}: {e}")

        # 2. Try Ultralytics YOLO backend (if ultralytics is installed)
        try:
            import ultralytics
            yolo_backend = UltralyticsYOLOBackend(weights_path, device=self.device)
            if yolo_backend.is_available():
                self.backend = yolo_backend
                self.model_status = "loaded"
                logger.info(f"Waste detector loaded with Ultralytics backend: {weights_path}")
                return
        except Exception as e:
            logger.debug(f"Ultralytics backend could not load {weights_path}: {e}")

        self.backend = None
        self.model_status = "not_configured"

    def set_backend(self, backend: Optional[BaseDetectorBackend]):
        """Injects a custom or test detector backend (for test isolation)."""
        self.backend = backend
        if backend is not None and backend.is_available():
            self.model_status = "loaded"
        elif backend is not None:
            self.model_status = "not_configured"
        else:
            self.model_status = "not_configured"

    @property
    def is_loaded(self) -> bool:
        return self.backend is not None and self.backend.is_available()

    def detect_image_bytes(
        self,
        image_bytes: bytes,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None
    ) -> WasteDetectionResponse:
        """
        Validates input image, runs multi-object detection, scales coordinates,
        and assigns authoritative waste disposal decisions.
        """
        if not image_bytes:
            raise ValueError("Empty image payload provided.")

        if len(image_bytes) > 10 * 1024 * 1024:
            raise ValueError("Image size exceeds 10MB limit.")

        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Verify and convert to RGB
            image.load()
            orig_width, orig_height = image.size
            if orig_width <= 0 or orig_height <= 0:
                raise ValueError("Image dimensions must be greater than zero.")
            image_rgb = image.convert("RGB")
        except Exception as e:
            raise ValueError(f"Invalid or corrupted image format: {e}")

        conf = conf_threshold if conf_threshold is not None else self.confidence_threshold
        iou = iou_threshold if iou_threshold is not None else self.iou_threshold

        # If model is not configured or loaded, return clean unconfigured response (never fabricate fake detections)
        if not self.is_loaded or self.backend is None:
            return WasteDetectionResponse(
                success=True,
                model_status=self.model_status,
                message=(
                    "Waste object detector weights are not yet deployed or configured in this environment. "
                    "Single-image classification remains active via /api/predict."
                ),
                model_info={"status": self.model_status, "device": self.device},
                image_dimensions={"width": orig_width, "height": orig_height},
                detections=[],
                summary=DetectionSummary()
            )

        # Execute object-level inference
        try:
            raw_detections = self.backend.detect(image_rgb, conf_threshold=conf, iou_threshold=iou)
        except Exception as e:
            logger.error(f"Inference error during object detection: {e}")
            return WasteDetectionResponse(
                success=False,
                model_status="inference_failed",
                message=f"Object detection inference failed: {str(e)}",
                model_info={"error": str(e)},
                image_dimensions={"width": orig_width, "height": orig_height},
                detections=[],
                summary=DetectionSummary()
            )

        # Assemble and validate detected items with disposal routing
        processed_detections: List[ObjectDetectionItem] = []
        wet_count = 0
        dry_count = 0
        hazardous_count = 0
        review_count = 0

        for idx, det in enumerate(raw_detections, start=1):
            label = det.get("label", "unknown")
            confidence = float(det.get("confidence", 0.0))
            raw_bbox = det.get("bbox", {})

            # Coordinate bounds clamping
            x1 = max(0.0, min(float(raw_bbox.get("x1", 0.0)), float(orig_width)))
            y1 = max(0.0, min(float(raw_bbox.get("y1", 0.0)), float(orig_height)))
            x2 = max(0.0, min(float(raw_bbox.get("x2", 0.0)), float(orig_width)))
            y2 = max(0.0, min(float(raw_bbox.get("y2", 0.0)), float(orig_height)))

            # Ensure valid box dimensions
            if x2 < x1:
                x1, x2 = x2, x1
            if y2 < y1:
                y1, y2 = y2, y1

            # Compute normalized coordinates [0.0, 1.0]
            norm_x1 = round(x1 / orig_width, 4) if orig_width > 0 else 0.0
            norm_y1 = round(y1 / orig_height, 4) if orig_height > 0 else 0.0
            norm_x2 = round(x2 / orig_width, 4) if orig_width > 0 else 0.0
            norm_y2 = round(y2 / orig_height, 4) if orig_height > 0 else 0.0

            bbox_obj = BoundingBox(
                x1=round(x1, 1),
                y1=round(y1, 1),
                x2=round(x2, 1),
                y2=round(y2, 1),
                norm_x1=norm_x1,
                norm_y1=norm_y1,
                norm_x2=norm_x2,
                norm_y2=norm_y2
            )

            # Route to municipal disposal category
            disposal = waste_routing_service.route_detected_item(
                label=label,
                confidence=confidence,
                min_confidence=conf
            )

            # Accumulate summary counts
            if disposal.category == "wet":
                wet_count += 1
            elif disposal.category == "dry":
                dry_count += 1
            elif disposal.category == "hazardous":
                hazardous_count += 1
            else:
                review_count += 1

            processed_detections.append(ObjectDetectionItem(
                detection_id=idx,
                label=label,
                confidence=round(confidence, 4),
                bbox=bbox_obj,
                mask=det.get("mask"),
                disposal=disposal
            ))

        summary = DetectionSummary(
            total_detections=len(processed_detections),
            wet_items=wet_count,
            dry_items=dry_count,
            hazardous_items=hazardous_count,
            manual_review_items=review_count
        )

        model_info = self.backend.get_model_info() if self.backend else {}

        return WasteDetectionResponse(
            success=True,
            model_status="loaded",
            message=f"Successfully detected {len(processed_detections)} waste item(s)." if processed_detections else "No waste items detected above confidence threshold.",
            model_info=model_info,
            image_dimensions={"width": orig_width, "height": orig_height},
            detections=processed_detections,
            summary=summary
        )


# Global singleton detector service
detector_service = WasteDetectorService()
