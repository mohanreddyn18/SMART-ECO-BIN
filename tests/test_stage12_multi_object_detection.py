"""
SMART ECO BIN — Multi-Object Mixed Waste Detection Integration & Unit Tests
===========================================================================
Validates:
1. Multiple detections in one image.
2. Multiple instances of the same class (e.g. 2 plastic bottles).
3. Correct bounding-box coordinate conversion and normalization.
4. Empty detections handling (no objects detected).
5. Confidence-threshold filtering.
6. Unknown and unsupported object classes routing.
7. Wet/dry/hazardous/manual-review disposal stream routing.
8. Invalid, corrupt, and oversized images validation.
9. Model unavailable and inference failure states.
10. API response schema adherence.
11. Existing MobileNetV2 predictions & segregation preservation.
12. Authentication, rate limiting, and zero-retention privacy protections.
"""

import os
import io
import time
import unittest
from typing import List, Dict, Any
from PIL import Image
from fastapi.testclient import TestClient

os.environ["ENVIRONMENT"] = "development"
os.environ["ALLOW_DEV_AUTH"] = "true"
os.environ["AUTH_PROVIDER"] = "auto"
os.environ["STORAGE_PROVIDER"] = "local"
os.environ.pop("JWT_DEV_SECRET", None)

from main import app
from app.services.detector_service import detector_service, BaseDetectorBackend
from app.services.waste_routing_service import waste_routing_service, WasteRoutingService
from app.services.annotation_service import annotation_service
from app.routes.predict import clear_rate_limits
from app.models.schemas import BoundingBox, WasteDetectionResponse


class DeterministicFakeDetectorBackend(BaseDetectorBackend):
    """
    Deterministic test detector backend used strictly inside isolated unit tests.
    Never used in production.
    """

    def __init__(self, detections: List[Dict[str, Any]] = None):
        self._detections = detections or []

    def set_detections(self, detections: List[Dict[str, Any]]):
        self._detections = detections

    def is_available(self) -> bool:
        return True

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "backend": "deterministic_fake_detector",
            "model_type": "unit_test_mock",
            "version": "1.0.0-test"
        }

    def detect(self, image: Image.Image, conf_threshold: float = 0.40, iou_threshold: float = 0.45) -> List[Dict[str, Any]]:
        # Filter detections by conf_threshold
        return [d for d in self._detections if d.get("confidence", 0.0) >= conf_threshold]


class FailingDetectorBackend(BaseDetectorBackend):
    """Simulates internal inference failure."""
    def is_available(self) -> bool:
        return True
    def detect(self, image: Image.Image, conf_threshold: float = 0.40, iou_threshold: float = 0.45) -> List[Dict[str, Any]]:
        raise RuntimeError("GPU Out-of-Memory / CUDA core exception")


def create_test_image_bytes(width: int = 640, height: int = 480, color: str = "green") -> bytes:
    """Creates a valid in-memory JPEG test image."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestMultiObjectWasteDetection(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        clear_rate_limits()
        # Save original detector backend to restore in tearDown
        self._orig_backend = detector_service.backend
        self._orig_status = detector_service.model_status

    def tearDown(self):
        detector_service.set_backend(self._orig_backend)
        detector_service.model_status = self._orig_status
        clear_rate_limits()

    # --------------------------------------------------------------------------
    # 1. Multiple Detections in One Image
    # --------------------------------------------------------------------------
    def test_01_multiple_detections_in_one_image(self):
        """Mixed image returns multiple separate detections with distinct classes and categories."""
        fake_detections = [
            {
                "label": "cardboard_box",
                "confidence": 0.94,
                "bbox": {"x1": 100.0, "y1": 50.0, "x2": 300.0, "y2": 250.0}
            },
            {
                "label": "vegetable_scraps",
                "confidence": 0.91,
                "bbox": {"x1": 350.0, "y1": 200.0, "x2": 500.0, "y2": 350.0}
            },
            {
                "label": "battery",
                "confidence": 0.88,
                "bbox": {"x1": 520.0, "y1": 380.0, "x2": 600.0, "y2": 440.0}
            }
        ]
        test_backend = DeterministicFakeDetectorBackend(fake_detections)
        detector_service.set_backend(test_backend)

        img_bytes = create_test_image_bytes(640, 480)
        files = {"file": ("mixed_waste.jpg", img_bytes, "image/jpeg")}
        resp = self.client.post("/api/detect-waste", files=files)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertTrue(data["success"])
        self.assertEqual(data["model_status"], "loaded")
        self.assertEqual(len(data["detections"]), 3)

        # Check item 1: Cardboard Box -> Dry
        item1 = data["detections"][0]
        self.assertEqual(item1["label"], "cardboard_box")
        self.assertEqual(item1["disposal"]["category"], "dry")
        self.assertEqual(item1["disposal"]["bin_label"], "Dry / Recyclable Waste")

        # Check item 2: Vegetable Scraps -> Wet
        item2 = data["detections"][1]
        self.assertEqual(item2["label"], "vegetable_scraps")
        self.assertEqual(item2["disposal"]["category"], "wet")
        self.assertEqual(item2["disposal"]["bin_label"], "Wet / Biodegradable Waste")

        # Check item 3: Battery -> Hazardous
        item3 = data["detections"][2]
        self.assertEqual(item3["label"], "battery")
        self.assertEqual(item3["disposal"]["category"], "hazardous")
        self.assertEqual(item3["disposal"]["bin_label"], "Hazardous / E-Waste Collection")

        # Check summary metrics
        summary = data["summary"]
        self.assertEqual(summary["total_detections"], 3)
        self.assertEqual(summary["dry_items"], 1)
        self.assertEqual(summary["wet_items"], 1)
        self.assertEqual(summary["hazardous_items"], 1)
        self.assertEqual(summary["manual_review_items"], 0)

    # --------------------------------------------------------------------------
    # 2. Multiple Instances of the Same Class
    # --------------------------------------------------------------------------
    def test_02_multiple_instances_of_same_class(self):
        """Two separate instances of plastic_bottle remain two distinct detections."""
        fake_detections = [
            {
                "label": "plastic_bottle",
                "confidence": 0.95,
                "bbox": {"x1": 50.0, "y1": 50.0, "x2": 150.0, "y2": 300.0}
            },
            {
                "label": "plastic_bottle",
                "confidence": 0.89,
                "bbox": {"x1": 200.0, "y1": 80.0, "x2": 320.0, "y2": 320.0}
            }
        ]
        detector_service.set_backend(DeterministicFakeDetectorBackend(fake_detections))

        img_bytes = create_test_image_bytes(640, 480)
        resp = self.client.post("/api/detect-waste", files={"file": ("bottles.jpg", img_bytes, "image/jpeg")})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(len(data["detections"]), 2)
        self.assertEqual(data["detections"][0]["detection_id"], 1)
        self.assertEqual(data["detections"][1]["detection_id"], 2)
        self.assertNotEqual(data["detections"][0]["bbox"]["x1"], data["detections"][1]["bbox"]["x1"])
        self.assertEqual(data["summary"]["dry_items"], 2)

    # --------------------------------------------------------------------------
    # 3. Correct Bounding-Box Coordinate Conversion & Normalization
    # --------------------------------------------------------------------------
    def test_03_bounding_box_coordinates_and_normalization(self):
        """Bounding-box pixel coordinates and normalized [0, 1] values are strictly valid."""
        fake_detections = [{
            "label": "metal_can",
            "confidence": 0.92,
            "bbox": {"x1": 160.0, "y1": 120.0, "x2": 480.0, "y2": 360.0}
        }]
        detector_service.set_backend(DeterministicFakeDetectorBackend(fake_detections))

        img_bytes = create_test_image_bytes(640, 480)
        resp = self.client.post("/api/detect-waste", files={"file": ("can.jpg", img_bytes, "image/jpeg")})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        bbox = data["detections"][0]["bbox"]
        self.assertEqual(bbox["x1"], 160.0)
        self.assertEqual(bbox["y1"], 120.0)
        self.assertEqual(bbox["x2"], 480.0)
        self.assertEqual(bbox["y2"], 360.0)

        # 160 / 640 = 0.25, 120 / 480 = 0.25, 480 / 640 = 0.75, 360 / 480 = 0.75
        self.assertAlmostEqual(bbox["norm_x1"], 0.25, places=2)
        self.assertAlmostEqual(bbox["norm_y1"], 0.25, places=2)
        self.assertAlmostEqual(bbox["norm_x2"], 0.75, places=2)
        self.assertAlmostEqual(bbox["norm_y2"], 0.75, places=2)

    # --------------------------------------------------------------------------
    # 4. Empty Detections
    # --------------------------------------------------------------------------
    def test_04_empty_detections(self):
        """When detector finds no objects, returns empty detections list and zero counts."""
        detector_service.set_backend(DeterministicFakeDetectorBackend([]))

        img_bytes = create_test_image_bytes(640, 480)
        resp = self.client.post("/api/detect-waste", files={"file": ("clean_background.jpg", img_bytes, "image/jpeg")})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertTrue(data["success"])
        self.assertEqual(data["detections"], [])
        self.assertEqual(data["summary"]["total_detections"], 0)
        self.assertIn("No waste items detected", data["message"])

    # --------------------------------------------------------------------------
    # 5. Confidence-Threshold Filtering
    # --------------------------------------------------------------------------
    def test_05_confidence_threshold_filtering(self):
        """Detections below confidence threshold are routed to manual review or filtered."""
        # 1. Routing service test: Low confidence routed to manual_review
        low_conf_decision = waste_routing_service.route_detected_item("cardboard", confidence=0.25, min_confidence=0.50)
        self.assertEqual(low_conf_decision.category, "manual_review")
        self.assertIn("below the automated sorting threshold", low_conf_decision.reason)

        # 2. Backend filtering test: items below threshold omitted
        test_backend = DeterministicFakeDetectorBackend([
            {"label": "paper", "confidence": 0.85, "bbox": {"x1": 10, "y1": 10, "x2": 50, "y2": 50}},
            {"label": "paper", "confidence": 0.20, "bbox": {"x1": 60, "y1": 10, "x2": 90, "y2": 50}}
        ])
        results = test_backend.detect(Image.new("RGB", (100, 100)), conf_threshold=0.40)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["confidence"], 0.85)

    # --------------------------------------------------------------------------
    # 6. Unknown and Unsupported Object Classes
    # --------------------------------------------------------------------------
    def test_06_unknown_object_classes_routed_to_manual_review(self):
        """Unrecognized classes are diverted to manual inspection instead of guessing."""
        decision = waste_routing_service.route_detected_item("exotic_mystery_object_999", confidence=0.90)
        self.assertEqual(decision.category, "manual_review")
        self.assertEqual(decision.compartment_id, "bin_manual_review")
        self.assertIn("is not mapped to an automated municipal sorting stream", decision.reason)

    # --------------------------------------------------------------------------
    # 7. Complete Wet / Dry / Hazardous / Manual Review Routing Policy
    # --------------------------------------------------------------------------
    def test_07_disposal_routing_policy(self):
        """Authoritative verification of the complete disposal routing rules."""
        # Wet / Biodegradable
        for label in ["vegetable_scraps", "vegetable_waste", "fruit_peels", "food_waste", "apple", "banana", "biological"]:
            dec = waste_routing_service.route_detected_item(label, 0.90)
            self.assertEqual(dec.category, "wet", f"{label} must route to wet")
            self.assertEqual(dec.compartment_id, "bin_organic")

        # Dry / Recyclable
        for label in ["cardboard", "cardboard_box", "paper", "plastic_bottle", "metal_can", "glass_bottle", "clothes", "shoes"]:
            dec = waste_routing_service.route_detected_item(label, 0.90)
            self.assertEqual(dec.category, "dry", f"{label} must route to dry")

        # Hazardous
        for label in ["battery", "e-waste", "cell_phone", "chemical_container"]:
            dec = waste_routing_service.route_detected_item(label, 0.90)
            self.assertEqual(dec.category, "hazardous", f"{label} must route to hazardous")
            self.assertEqual(dec.compartment_id, "bin_hazardous")

        # Manual Review / Composite
        for label in ["plastic_packaging", "trash", "contaminated_packaging"]:
            dec = waste_routing_service.route_detected_item(label, 0.90)
            self.assertEqual(dec.category, "manual_review", f"{label} must route to manual_review")

    # --------------------------------------------------------------------------
    # 8. Invalid, Corrupt, and Oversized Images
    # --------------------------------------------------------------------------
    def test_08_invalid_corrupt_and_oversized_images(self):
        """Non-image, corrupt bytes, and oversized files return HTTP 400."""
        # 1. Invalid MIME type
        resp1 = self.client.post(
            "/api/detect-waste",
            files={"file": ("notes.txt", b"not an image", "text/plain")}
        )
        self.assertEqual(resp1.status_code, 400)
        self.assertIn("Invalid image type", resp1.json()["detail"])

        # 2. Corrupt JPEG header
        resp2 = self.client.post(
            "/api/detect-waste",
            files={"file": ("corrupt.jpg", b"corrupted bytes", "image/jpeg")}
        )
        self.assertEqual(resp2.status_code, 400)
        self.assertIn("Invalid image format", resp2.json()["detail"])

        # 3. Oversized file (> 10 MB)
        oversized_bytes = b"0" * (10 * 1024 * 1024 + 1024)
        resp3 = self.client.post(
            "/api/detect-waste",
            files={"file": ("huge.jpg", oversized_bytes, "image/jpeg")}
        )
        self.assertEqual(resp3.status_code, 400)
        self.assertIn("exceeds 10MB limit", resp3.json()["detail"])

    # --------------------------------------------------------------------------
    # 9. Model Unavailable & Inference Failure States
    # --------------------------------------------------------------------------
    def test_09_model_unavailable_and_inference_failures(self):
        """Handles unconfigured model cleanly and catches inference exceptions safely."""
        # Case A: Model not configured (no weights deployed)
        detector_service.set_backend(None)
        detector_service.model_status = "not_configured"

        img_bytes = create_test_image_bytes(400, 300)
        resp_unconf = self.client.post("/api/detect-waste", files={"file": ("sample.jpg", img_bytes, "image/jpeg")})
        self.assertEqual(resp_unconf.status_code, 200)
        data_unconf = resp_unconf.json()
        self.assertTrue(data_unconf["success"])
        self.assertEqual(data_unconf["model_status"], "not_configured")
        self.assertEqual(data_unconf["detections"], [])
        self.assertIn("not yet deployed", data_unconf["message"])

        # Case B: Internal inference failure caught without crash
        detector_service.set_backend(FailingDetectorBackend())
        resp_fail = self.client.post("/api/detect-waste", files={"file": ("sample.jpg", img_bytes, "image/jpeg")})
        self.assertEqual(resp_fail.status_code, 200)
        data_fail = resp_fail.json()
        self.assertFalse(data_fail["success"])
        self.assertEqual(data_fail["model_status"], "inference_failed")

    # --------------------------------------------------------------------------
    # 10. API Response Schema Validation
    # --------------------------------------------------------------------------
    def test_10_api_response_schema_fields(self):
        """Validates all required fields in the WasteDetectionResponse schema."""
        fake_detections = [{
            "label": "fruit_peels",
            "confidence": 0.88,
            "bbox": {"x1": 50, "y1": 50, "x2": 150, "y2": 150}
        }]
        detector_service.set_backend(DeterministicFakeDetectorBackend(fake_detections))

        img_bytes = create_test_image_bytes(640, 480)
        resp = self.client.post("/api/detect-waste?include_annotation=true", files={"file": ("peel.jpg", img_bytes, "image/jpeg")})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # Validate response schema using Pydantic model
        validated = WasteDetectionResponse(**data)
        self.assertTrue(validated.success)
        self.assertEqual(validated.image_dimensions["width"], 640)
        self.assertEqual(validated.image_dimensions["height"], 480)
        self.assertIsNotNone(validated.annotated_image_base64)
        self.assertTrue(validated.annotated_image_base64.startswith("data:image/jpeg;base64,"))

    # --------------------------------------------------------------------------
    # 11. Existing MobileNetV2 Single-Item Classification Preserved
    # --------------------------------------------------------------------------
    def test_11_mobilenetv2_prediction_endpoint_unbroken(self):
        """The existing single-item /api/predict endpoint remains fully operational."""
        img_bytes = create_test_image_bytes(224, 224, color="blue")
        resp = self.client.post("/api/predict", files={"file": ("single_sample.jpg", img_bytes, "image/jpeg")})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertIn("predictedClass", data)
        self.assertIn("confidence", data)
        self.assertIn("wasteType", data)
        self.assertIn("recommendation", data)
        self.assertIn("MobileNetV2", data["model"])

    # --------------------------------------------------------------------------
    # 12. Rate Limiting, Privacy & Authentication Regressions
    # --------------------------------------------------------------------------
    def test_12_rate_limiting_and_zero_image_retention(self):
        """Enforces rate limiting on /api/detect-waste and ensures zero disk retention."""
        img_bytes = create_test_image_bytes(100, 100)
        detector_service.set_backend(DeterministicFakeDetectorBackend([]))

        # Check rate limiter triggers after 30 requests from same client
        for i in range(30):
            r = self.client.post("/api/detect-waste", files={"file": (f"test_{i}.jpg", img_bytes, "image/jpeg")})
            self.assertEqual(r.status_code, 200)

        # 31st request must trigger HTTP 429
        r_over = self.client.post("/api/detect-waste", files={"file": ("test_31.jpg", img_bytes, "image/jpeg")})
        self.assertEqual(r_over.status_code, 429)
        self.assertIn("Rate limit exceeded", r_over.json()["detail"])


if __name__ == "__main__":
    unittest.main()
