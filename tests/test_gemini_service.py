import asyncio
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

backend_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "backend")
)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from google import genai

from app.ai.gemini_client import (
    DEFAULT_GEMINI_MODEL,
    GeminiAIService,
    GeminiServiceUnavailable,
)


class FakeModels:
    def __init__(self):
        self.calls = []
        self.response_text = "A concise generated explanation."
        self.error = None
        self.delay_seconds = 0

    async def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        if self.error:
            raise self.error
        return SimpleNamespace(text=self.response_text)


class TestGeminiAIService(unittest.TestCase):
    @staticmethod
    def run_immediate(awaitable, wait_for=None):
        async def resolve_immediately(operation, timeout):
            return await operation

        with patch(
            "app.ai.gemini_client.asyncio.wait_for",
            wait_for or resolve_immediately,
        ):
            try:
                awaitable.send(None)
            except StopIteration as completed:
                return completed.value
            finally:
                awaitable.close()
        raise AssertionError("Expected the mocked async operation to finish immediately.")

    def create_service(self, **environment):
        models = FakeModels()
        client = SimpleNamespace(aio=SimpleNamespace(models=models))
        env = {
            "GEMINI_API_KEY": "test-key-not-a-real-credential",
            "GEMINI_MODEL": DEFAULT_GEMINI_MODEL,
            "GEMINI_REQUEST_TIMEOUT_SECONDS": "20",
            **environment,
        }
        with patch.dict(os.environ, env, clear=False), patch.object(
            genai, "Client", return_value=client
        ) as client_factory:
            service = GeminiAIService()

        return service, models, client_factory

    def test_client_uses_supported_model_and_bounded_http_timeout(self):
        service, _, client_factory = self.create_service()

        self.assertEqual(service.model_name, DEFAULT_GEMINI_MODEL)
        self.assertTrue(service.client_available)
        options = client_factory.call_args.kwargs["http_options"]
        self.assertEqual(options.timeout, 20_000)

    def test_missing_key_leaves_service_unavailable_without_client_creation(self):
        with patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "",
                "GEMINI_REQUEST_TIMEOUT_SECONDS": "20",
            },
            clear=False,
        ), patch.object(genai, "Client") as client_factory:
            service = GeminiAIService()

        self.assertFalse(service.client_available)
        client_factory.assert_not_called()
        with self.assertRaisesRegex(GeminiServiceUnavailable, "not configured"):
            self.run_immediate(service.query_waste_ai("How do I recycle a battery?"))

    def test_classification_explanation_sends_metadata_not_image(self):
        service, models, _ = self.create_service()
        classification = {
            "predicted_class": "battery",
            "confidence": 92.5,
            "waste_type": "Hazardous / E-Waste",
            "recommendation": "Use a designated battery collection point.",
            "disposal_bin": "Hazardous Waste Depot",
            "requires_manual_review": True,
        }

        reply = self.run_immediate(
            service.query_waste_ai(
                "Explain the classifier result.",
                classification,
            )
        )

        self.assertEqual(reply, models.response_text)
        call = models.calls[0]
        self.assertEqual(call["model"], DEFAULT_GEMINI_MODEL)
        self.assertIn('"predicted_class": "battery"', call["contents"])
        self.assertNotIn("image", call["contents"].lower())
        self.assertIn("without changing", call["config"].system_instruction)
        self.assertEqual(call["config"].max_output_tokens, 512)

    def test_sanitation_explanation_uses_only_provided_telemetry(self):
        service, models, _ = self.create_service()
        telemetry = {
            "analytics": {"totalClassifications": 4},
            "sanitation": {"currentStatus": "UNAVAILABLE"},
            "anomalies": [],
        }

        result = self.run_immediate(
            service.query_sanitation_ai("Summarize sanitation status.", telemetry)
        )

        self.assertEqual(result["reply"], models.response_text)
        self.assertIsNone(result["function_called"])
        self.assertTrue(result["telemetry_grounded"])
        self.assertIn('"currentStatus": "UNAVAILABLE"', models.calls[0]["contents"])
        self.assertIn("no physical sensors", models.calls[0]["config"].system_instruction)

    def test_provider_errors_are_sanitized(self):
        service, models, _ = self.create_service()
        models.error = RuntimeError("private provider response with credential detail")

        with self.assertRaises(GeminiServiceUnavailable) as error:
            self.run_immediate(service.query_waste_ai("How do I recycle a battery?"))

        self.assertNotIn("private provider response", str(error.exception))

    def test_request_timeout_is_reported_without_provider_details(self):
        service, _, _ = self.create_service()

        def time_out(awaitable, timeout):
            awaitable.close()
            raise asyncio.TimeoutError

        with self.assertRaisesRegex(GeminiServiceUnavailable, "too long"):
            self.run_immediate(
                service.query_waste_ai("How do I recycle a battery?"),
                wait_for=time_out,
            )

    def test_empty_model_response_is_not_replaced_with_fake_content(self):
        service, models, _ = self.create_service()
        models.response_text = "  "

        with self.assertRaisesRegex(GeminiServiceUnavailable, "empty response"):
            self.run_immediate(service.query_waste_ai("How do I recycle a battery?"))


if __name__ == "__main__":
    unittest.main()
