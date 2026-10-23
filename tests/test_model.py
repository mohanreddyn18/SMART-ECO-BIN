import io
import os
import sys
import unittest
from PIL import Image
import torch

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.services.model_service import classifier_service, WasteClassifierService
from app.utils.helpers import CLASS_NAMES, CLASS_METADATA, get_metadata_for_class


class TestWasteClassifierModel(unittest.TestCase):
    """Baseline tests for MobileNetV2 waste classification service."""

    @classmethod
    def setUpClass(cls):
        # Ensure model is initialized
        cls.service = classifier_service

    def test_model_initialization(self):
        """Verify that the model service is loaded with the expected PyTorch MobileNetV2 architecture."""
        self.assertTrue(self.service.is_loaded, "Model should be loaded from waste_model.pth")
        self.assertIsNotNone(self.service.model, "Model instance must not be None")
        self.assertIsInstance(self.service.model, torch.nn.Module, "Model must be a PyTorch nn.Module")

        # Verify classifier head structure: 5 layers with 12 outputs
        classifier = self.service.model.classifier
        self.assertEqual(len(classifier), 5, "Classifier head must have 5 layers")
        # Final linear layer: index 4
        final_layer = classifier[4]
        self.assertIsInstance(final_layer, torch.nn.Linear, "Final layer must be Linear")
        self.assertEqual(final_layer.out_features, 12, "Final linear layer must output 12 classes")
        self.assertEqual(final_layer.in_features, 128, "Final linear layer must take 128 features")

    def test_expected_12_class_output_mapping(self):
        """Verify that the 12 class names and their metadata mappings are complete and correct."""
        expected_classes = [
            'battery', 'biological', 'brown-glass', 'cardboard', 'clothes',
            'green-glass', 'metal', 'paper', 'plastic', 'shoes', 'trash', 'white-glass'
        ]
        self.assertEqual(len(CLASS_NAMES), 12, "There must be exactly 12 waste classes")
        self.assertEqual(CLASS_NAMES, expected_classes, "Class names and order must match metadata")
        self.assertEqual(self.service.classes, expected_classes, "Service classes must match expected classes")

        # Verify every class has valid metadata mapping
        for cls_name in CLASS_NAMES:
            meta = get_metadata_for_class(cls_name)
            self.assertIn('category', meta, f"Metadata for '{cls_name}' must include 'category'")
            self.assertIn('disposalBin', meta, f"Metadata for '{cls_name}' must include 'disposalBin'")
            self.assertIn('recommendation', meta, f"Metadata for '{cls_name}' must include 'recommendation'")
            self.assertTrue(len(meta['category']) > 0)
            self.assertTrue(len(meta['disposalBin']) > 0)
            self.assertTrue(len(meta['recommendation']) > 0)

    def test_image_preprocessing(self):
        """Verify that the transformation pipeline produces a tensor of shape [3, 224, 224]."""
        dummy_img = Image.new("RGB", (320, 240), color=(128, 64, 32))
        tensor = self.service.transform(dummy_img)

        self.assertEqual(tensor.shape, torch.Size([3, 224, 224]), "Preprocessed tensor shape must be [3, 224, 224]")
        self.assertEqual(tensor.dtype, torch.float32, "Preprocessed tensor must be float32")

    def test_invalid_image_rejection(self):
        """Verify that non-image bytes or corrupted data are rejected with a ValueError."""
        # Non-image random bytes
        with self.assertRaises(ValueError):
            self.service.predict_image_bytes(b"not-an-image-data-stream")

        # Empty bytes
        with self.assertRaises(ValueError):
            self.service.predict_image_bytes(b"")

        # Partial header without valid image body
        with self.assertRaises(ValueError):
            self.service.predict_image_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00corrupt")

    def test_prediction_response_structure(self):
        """Verify that inference returns the expected contract and schema keys."""
        # Deterministic dummy RGB image fixture (224x224)
        img = Image.new("RGB", (224, 224), color=(80, 120, 160))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        image_bytes = buf.getvalue()

        result = self.service.predict_image_bytes(image_bytes)

        # Assert schema keys
        required_keys = [
            "predictedClass", "confidence", "wasteType",
            "recommendation", "disposalBin", "timestamp",
            "model", "isDemo"
        ]
        for key in required_keys:
            self.assertIn(key, result, f"Result must contain key '{key}'")

        # Validate types and ranges without asserting an arbitrary class
        self.assertIn(result["predictedClass"], CLASS_NAMES, "predictedClass must be one of the 12 valid classes")
        self.assertIsInstance(result["confidence"], (int, float), "confidence must be numeric")
        self.assertTrue(0.0 <= result["confidence"] <= 100.0, "confidence must be between 0 and 100")
        self.assertIsInstance(result["wasteType"], str)
        self.assertIsInstance(result["recommendation"], str)
        self.assertIsInstance(result["disposalBin"], str)
        self.assertIsInstance(result["timestamp"], str)
        self.assertFalse(result["isDemo"], "isDemo must be False when real weights are loaded")

    def test_unloaded_model_raises_runtime_error(self):
        """Verify that an uninitialized/unloaded model raises RuntimeError rather than returning fake predictions."""
        # Create an isolated mock instance with is_loaded=False (without mutating the singleton)
        unloaded_service = object.__new__(WasteClassifierService)
        unloaded_service.is_loaded = False
        unloaded_service.model = None

        img = Image.new("RGB", (224, 224), color=(50, 50, 50))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        with self.assertRaises(RuntimeError) as ctx:
            unloaded_service.predict_image_bytes(buf.getvalue())
        self.assertIn("Model weights are not loaded", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
