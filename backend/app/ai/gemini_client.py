import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

from google import genai
from google.genai import types

logger = logging.getLogger("ecosort.gemini")

DEFAULT_GEMINI_MODEL = "gemini-flash-latest"
DEFAULT_REQUEST_TIMEOUT_SECONDS = 20
MAX_PROMPT_LENGTH = 2000
MAX_RESPONSE_LENGTH = 4000


class GeminiServiceUnavailable(RuntimeError):
    """Raised when a configured Gemini request cannot return a genuine response."""


class GeminiAIService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
        self.timeout_seconds = int(
            os.getenv(
                "GEMINI_REQUEST_TIMEOUT_SECONDS",
                str(DEFAULT_REQUEST_TIMEOUT_SECONDS),
            )
        )
        if not 1 <= self.timeout_seconds <= 120:
            raise ValueError("GEMINI_REQUEST_TIMEOUT_SECONDS must be between 1 and 120.")
        if not self.model_name:
            raise ValueError("GEMINI_MODEL must not be empty.")

        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(timeout=self.timeout_seconds * 1000),
                )
            except Exception as error:
                logger.error(
                    "Could not initialize Gemini client (%s).",
                    type(error).__name__,
                )

    @property
    def client_available(self) -> bool:
        return self.client is not None

    async def _generate(self, system_instruction: str, contents: str) -> str:
        if not self.client:
            raise GeminiServiceUnavailable("Gemini is not configured on the backend.")

        try:
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                        max_output_tokens=512,
                    ),
                ),
                timeout=self.timeout_seconds,
            )
            text = (response.text or "").strip()
        except asyncio.TimeoutError as error:
            logger.warning("Gemini request timed out.")
            raise GeminiServiceUnavailable(
                "Gemini took too long to respond. Please try again."
            ) from error
        except Exception as error:
            logger.warning(
                "Gemini request failed (%s).",
                type(error).__name__,
            )
            raise GeminiServiceUnavailable(
                "Gemini could not complete the request. Please try again later."
            ) from error

        if not text:
            raise GeminiServiceUnavailable("Gemini returned an empty response.")

        return text[:MAX_RESPONSE_LENGTH]

    async def query_waste_ai(
        self,
        prompt: str,
        classification_result: Optional[Dict[str, Any]] = None,
    ) -> str:
        if len(prompt) > MAX_PROMPT_LENGTH:
            raise GeminiServiceUnavailable("The question is too long.")

        system_instruction = (
            "You are WasteAI, an AI-generated waste segregation and recycling "
            "explanation assistant. Give concise, cautious, actionable guidance. "
            "Do not claim knowledge of local collection rules unless supplied. "
            "If classification metadata is provided, explain it without changing "
            "the model's predicted class, confidence, or disposal directive. "
            "Do not present your explanation as a new classification or verified "
            "local rule. No image is provided to you."
        )
        context = (
            "Classification metadata (JSON; this is the existing classifier output, "
            "not a Gemini prediction):\n"
            f"{json.dumps(classification_result, ensure_ascii=True, sort_keys=True)}\n\n"
            if classification_result is not None
            else ""
        )
        return await self._generate(
            system_instruction,
            f"{context}User question:\n{prompt}",
        )

    async def query_sanitation_ai(
        self,
        prompt: str,
        telemetry: Dict[str, Any],
    ) -> Dict[str, Any]:
        if len(prompt) > MAX_PROMPT_LENGTH:
            raise GeminiServiceUnavailable("The question is too long.")

        system_instruction = (
            "You are SanitationAI, an AI-generated explanation assistant. Use only "
            "the verified telemetry JSON supplied by the backend. Do not invent "
            "counts, percentages, locations, sensor readings, classifications, "
            "or operational facts. This application has no physical sensors. If "
            "data is absent or insufficient, say it is unavailable. Distinguish "
            "your explanation from observed analytics."
        )
        telemetry_json = json.dumps(telemetry, ensure_ascii=True, sort_keys=True, default=str)
        reply = await self._generate(
            system_instruction,
            f"Verified backend telemetry (JSON):\n{telemetry_json}\n\n"
            f"User question:\n{prompt}",
        )
        return {
            "reply": reply,
            "function_called": None,
            "telemetry_grounded": True,
        }


gemini_service = GeminiAIService()
