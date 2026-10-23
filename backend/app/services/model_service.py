import os
import io
import logging
from typing import Dict, Any, Tuple
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms

from app.utils.helpers import CLASS_NAMES, get_metadata_for_class, get_current_iso_time, determine_routing

logger = logging.getLogger("ecosort.model")

class WasteClassifierService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(WasteClassifierService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_path: str = None):
        if getattr(self, '_initialized', False):
            return

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.classes = CLASS_NAMES
        self.model = None
        self.is_loaded = False

        # Exact preprocessing discovered from Colab metadata
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        # Resolve model path
        default_paths = [
            model_path,
            os.environ.get("MODEL_PATH"),
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "model", "waste_model.pth"),
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "RJ147_Antigravity_Package (1)", "waste_model.pth"),
            "ml/model/waste_model.pth"
        ]

        resolved_path = None
        for p in default_paths:
            if p and os.path.exists(p):
                resolved_path = os.path.abspath(p)
                break

        if resolved_path:
            self._load_model(resolved_path)
        else:
            logger.warning("Trained model file waste_model.pth not found in default paths.")

        self._initialized = True

    def _load_model(self, model_path: str):
        try:
            logger.info(f"Loading trained MobileNetV2 from {model_path} onto {self.device}...")
            # Instantiate MobileNetV2
            model = models.mobilenet_v2(weights=None)
            # Exact 5-layer classifier discovered from checkpoint state_dict
            model.classifier = nn.Sequential(
                nn.Dropout(p=0.2),
                nn.Linear(1280, 128),
                nn.ReLU(),
                nn.Dropout(p=0.2),
                nn.Linear(128, len(self.classes))
            )
            # Load state dict safely using weights_only=True
            state_dict = torch.load(model_path, map_location=self.device, weights_only=True)
            model.load_state_dict(state_dict)
            model.to(self.device)
            model.eval()

            self.model = model
            self.is_loaded = True
            logger.info("MobileNetV2 (12 Classes) successfully loaded and initialized for inference.")
        except Exception as e:
            logger.error(f"Failed to load PyTorch state dict: {e}")
            self.model = None
            self.is_loaded = False

    def predict_image_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """Runs validation, preprocessing, and forward pass on uploaded image bytes."""
        if not self.is_loaded or self.model is None:
            raise RuntimeError("Model weights are not loaded. Cannot perform inference.")

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        except Exception as e:
            raise ValueError(f"Invalid or corrupted image format: {e}")

        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
            conf, pred_idx = torch.max(probabilities, dim=0)

        predicted_class = self.classes[pred_idx.item()]
        confidence = round(conf.item() * 100.0, 2)

        routing = determine_routing(predicted_class, confidence)

        return {
            "predictedClass": predicted_class,
            "confidence": confidence,
            "wasteType": routing["category"],
            "recommendation": routing["recommendation"],
            "disposalBin": routing["disposalBin"],
            "destinationCompartment": routing["destinationCompartment"],
            "compartmentId": routing["compartmentId"],
            "routingStatus": routing["routingStatus"],
            "routingReason": routing["routingReason"],
            "requiresManualReview": routing["requiresManualReview"],
            "simulationStatus": "READY",
            "timestamp": get_current_iso_time(),
            "model": "MobileNetV2 (12-class image classifier)",
            "isDemo": False
        }

classifier_service = WasteClassifierService()
