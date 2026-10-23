import io
import os
import sys
import unittest
from PIL import Image
from fastapi.testclient import TestClient

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import main
from app.utils.helpers import (
    CLASS_NAMES,
    COMPARTMENTS,
    CLASS_METADATA,
    determine_routing,
    get_metadata_for_class
)
from app.services.analytics_service import analytics_service


class TestSegregationRoutingPolicy(unittest.TestCase):
    """
    Automated test suite for the authoritative 12-class digital software segregation policy,
    quarantine diversion, and configurable uncertainty routing.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app)

    def test_all_12_classes_have_authoritative_compartment_mapping(self):
        """Verify that every supported class maps to a valid, distinct software compartment."""
        self.assertEqual(len(CLASS_NAMES), 12, "Must support exactly 12 classes")

        for cls_name in CLASS_NAMES:
            routing = determine_routing(cls_name, confidence=95.0)
            self.assertEqual(routing["routingStatus"], "AUTOMATED_ROUTED", f"Class '{cls_name}' must be routed automatically when confident")
            self.assertFalse(routing["requiresManualReview"], f"Class '{cls_name}' should not require manual review at 95% confidence")
            self.assertIn(routing["compartmentId"], COMPARTMENTS, f"Compartment ID '{routing['compartmentId']}' must be in COMPARTMENTS dictionary")
            self.assertEqual(routing["destinationCompartment"], COMPARTMENTS[routing["compartmentId"]]["name"])
            self.assertTrue(len(routing["routingReason"]) > 0, f"Routing reason must be provided for '{cls_name}'")

    def test_battery_hazardous_isolation_policy(self):
        """Verify that batteries are routed strictly to hazardous waste isolation, never to general or standard recycling."""
        routing = determine_routing("battery", confidence=96.0)
        self.assertEqual(routing["compartmentId"], "bin_hazardous")
        self.assertIn("Hazardous", routing["destinationCompartment"])
        self.assertEqual(routing["category"], "Hazardous / Other")
        self.assertIn("toxic chemistries", routing["routingReason"])

    def test_biological_organic_compost_policy(self):
        """Verify that biological waste is routed to the organic composting compartment."""
        routing = determine_routing("biological", confidence=92.5)
        self.assertEqual(routing["compartmentId"], "bin_organic")
        self.assertIn("Organic", routing["destinationCompartment"])
        self.assertEqual(routing["category"], "Organic / Wet Waste")

    def test_glass_subtypes_preserved(self):
        """Verify that brown, green, and white glass are preserved as distinct color-sorted streams."""
        brown = determine_routing("brown-glass", confidence=94.0)
        green = determine_routing("green-glass", confidence=91.0)
        white = determine_routing("white-glass", confidence=93.0)

        # Ensure all 3 have distinct compartment IDs
        self.assertEqual(brown["compartmentId"], "bin_glass_brown")
        self.assertEqual(green["compartmentId"], "bin_glass_green")
        self.assertEqual(white["compartmentId"], "bin_glass_white")

        self.assertNotEqual(brown["destinationCompartment"], green["destinationCompartment"])
        self.assertNotEqual(green["destinationCompartment"], white["destinationCompartment"])
        self.assertNotEqual(brown["destinationCompartment"], white["destinationCompartment"])

    def test_dry_recyclables_policy(self):
        """Verify that plastic, metal, paper, cardboard, clothes, and shoes route to their dry streams."""
        plastic = determine_routing("plastic", confidence=95.0)
        self.assertEqual(plastic["compartmentId"], "bin_plastic")

        metal = determine_routing("metal", confidence=98.0)
        self.assertEqual(metal["compartmentId"], "bin_metal")

        paper = determine_routing("paper", confidence=90.0)
        self.assertEqual(paper["compartmentId"], "bin_paper")

        cardboard = determine_routing("cardboard", confidence=92.0)
        self.assertEqual(cardboard["compartmentId"], "bin_cardboard")

        clothes = determine_routing("clothes", confidence=88.0)
        self.assertEqual(clothes["compartmentId"], "bin_textile")

        shoes = determine_routing("shoes", confidence=89.0)
        self.assertEqual(shoes["compartmentId"], "bin_footwear")

    def test_trash_residual_policy(self):
        """Verify that trash routes to the non-recyclable general residual compartment."""
        trash = determine_routing("trash", confidence=85.0)
        self.assertEqual(trash["compartmentId"], "bin_residual")
        self.assertEqual(trash["category"], "Non-Recyclable")

    def test_unsupported_or_unknown_class_rejected_to_quarantine(self):
        """Verify that unknown/unsupported classes are never silently routed into normal bins."""
        unknown_inputs = ["radioactive", "medical-syringe", "uranium", "random_unseen_item", ""]
        for unk in unknown_inputs:
            routing = determine_routing(unk, confidence=99.0)
            self.assertEqual(routing["routingStatus"], "UNSUPPORTED_CLASS", f"Unknown class '{unk}' must have UNSUPPORTED_CLASS status")
            self.assertTrue(routing["requiresManualReview"], f"Unknown class '{unk}' must require manual review")
            self.assertEqual(routing["compartmentId"], "bin_manual_review")
            self.assertEqual(routing["destinationCompartment"], COMPARTMENTS["bin_manual_review"]["name"])

    def test_configurable_uncertainty_threshold_routing(self):
        """Verify that predictions below a configured uncertainty threshold divert to quarantine."""
        # When threshold is set to 70.0% and prediction is 55.0%
        uncertain = determine_routing("plastic", confidence=55.0, uncertainty_threshold=70.0)
        self.assertEqual(uncertain["routingStatus"], "UNCERTAIN_MANUAL_REVIEW")
        self.assertTrue(uncertain["requiresManualReview"])
        self.assertEqual(uncertain["compartmentId"], "bin_manual_review")
        self.assertIn("below operational threshold", uncertain["routingReason"])

        # When threshold is set to 70.0% and prediction is 85.0%
        confident = determine_routing("plastic", confidence=85.0, uncertainty_threshold=70.0)
        self.assertEqual(confident["routingStatus"], "AUTOMATED_ROUTED")
        self.assertFalse(confident["requiresManualReview"])
        self.assertEqual(confident["compartmentId"], "bin_plastic")

    def test_api_predict_returns_complete_routing_and_simulation_schema(self):
        """POST /api/predict must return all routing metadata and simulation directives."""
        img = Image.new("RGB", (224, 224), color=(40, 150, 90))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        response = self.client.post(
            "/api/predict",
            files={"file": ("test_routing_sample.jpg", buf, "image/jpeg")}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check all required routing and simulation schema fields
        self.assertIn("destinationCompartment", data)
        self.assertIn("compartmentId", data)
        self.assertIn("routingStatus", data)
        self.assertIn("routingReason", data)
        self.assertIn("simulationStatus", data)
        self.assertIn("requiresManualReview", data)

        self.assertIn(data["compartmentId"], COMPARTMENTS)
        self.assertIsInstance(data["requiresManualReview"], bool)
        self.assertEqual(data["simulationStatus"], "READY")

    def test_analytics_history_records_routing_outcome(self):
        """Verify that classification records stored in analytics include the routing outcome."""
        history = analytics_service.get_history(limit=5)
        self.assertTrue(len(history) > 0)
        latest = history[0]

        # Verify extended history schema
        self.assertIn("predictedClass", latest)
        self.assertIn("destinationCompartment", latest)
        self.assertIn("routingStatus", latest)
        self.assertIn("simulationStatus", latest)


if __name__ == "__main__":
    unittest.main()
