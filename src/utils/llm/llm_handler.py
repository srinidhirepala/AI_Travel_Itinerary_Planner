"""
LLM Handler - Manages Groq API interactions with retry logic.
"""
import os
import json
import re
import time
import logging
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv
from src.utils.common.validation import validate_itinerary_response, ValidationError

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_CANDIDATES = [
    _PROJECT_ROOT / "config" / ".env",
    _PROJECT_ROOT / ".env",
]
for _env_path in _ENV_CANDIDATES:
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path, override=False)
        break
logger = logging.getLogger(__name__)


class LLMHandler:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY is not set. Add it to your .env file. "
                "Get a free key at https://console.groq.com"
            )
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self.max_retries = 3
        self.base_delay = 1  # seconds

    def _exponential_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self.base_delay * (2 ** attempt)
        # Add jitter to prevent thundering herd
        import random
        delay += random.uniform(0, delay * 0.1)
        return min(delay, 30)  # Cap at 30 seconds

    @staticmethod
    def _strip_code_fences(raw: str) -> str:
        """Remove markdown code fences when present."""
        text = raw.strip()
        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        return text

    @staticmethod
    def _extract_json_object(raw: str) -> str:
        """Extract the outermost JSON object from raw text."""
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            return raw[start:end + 1]
        return raw

    def _parse_json_response(self, raw: str) -> dict:
        """Parse JSON robustly against minor LLM formatting issues."""
        normalized = raw.strip().replace("\ufeff", "")
        candidates = [
            normalized,
            self._strip_code_fences(normalized),
            self._extract_json_object(normalized),
            self._extract_json_object(self._strip_code_fences(normalized)),
        ]

        seen = set()
        unique_candidates = []
        for candidate in candidates:
            key = candidate.strip()
            if key and key not in seen:
                seen.add(key)
                unique_candidates.append(key)

        last_error = None
        for candidate in unique_candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError as e:
                last_error = e

            repaired = candidate
            repaired = repaired.replace("“", '"').replace("”", '"')
            repaired = repaired.replace("’", "'").replace("‘", "'")
            repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError as e:
                last_error = e

        if last_error:
            raise last_error
        raise ValueError("Empty or unparsable model response")

    def _repair_json_with_llm(self, raw: str) -> str:
        """Ask the model to repair malformed JSON and return valid JSON only."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict JSON repair utility. "
                        "Return ONLY valid JSON. Do not add markdown or explanations."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Fix the following malformed JSON. Keep original structure/content as much as possible. "
                        "Return only corrected JSON object.\n\n"
                        f"{raw}"
                    ),
                },
            ],
            temperature=0,
            max_tokens=4500,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content.strip()

    def generate_itinerary(self, prompt: str, temperature: float = 0.7) -> dict:
        """
        Generate itinerary using Groq API with exponential backoff retry logic.
        Returns a parsed dict with keys: days, budget_breakdown, practical_tips.
        Raises exceptions on failure - never returns error strings.
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert travel planner with deep local knowledge worldwide. "
                                "You MUST respond with valid JSON only - no markdown, no extra text, no code fences. "
                                "Follow the schema given in the user prompt exactly."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=temperature,
                    max_tokens=4500,
                    response_format={"type": "json_object"},
                )

                raw = response.choices[0].message.content.strip()

                try:
                    parsed = self._parse_json_response(raw)
                    # Validate response schema
                    validated = validate_itinerary_response(parsed)
                    logger.info(f"Itinerary generated successfully on attempt {attempt + 1}")
                    return validated
                except json.JSONDecodeError as e:
                    try:
                        repaired_raw = self._repair_json_with_llm(raw)
                        repaired_parsed = self._parse_json_response(repaired_raw)
                        validated = validate_itinerary_response(repaired_parsed)
                        logger.info(f"Itinerary repaired successfully on attempt {attempt + 1}")
                        return validated
                    except Exception as repair_error:
                        raise ValueError(
                            f"The AI returned malformed output. Please try again. (Detail: {e}; repair failed: {repair_error})"
                        ) from e
                except ValidationError as e:
                    raise ValueError(f"Invalid itinerary structure: {e}") from e

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                continue
        
        # All retries exhausted
        logger.error(f"Failed to generate itinerary after {self.max_retries} attempts")
        raise last_error or ValueError("Failed to generate itinerary")

    def stream_itinerary(self, prompt: str, temperature: float = 0.7):
        """
        Stream itinerary text using Groq API.
        Yields text chunks as they arrive.
        Used for plain-text streaming display.
        """
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert travel planner with deep local knowledge worldwide. "
                        "Write clear, well-structured travel itineraries."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=3000,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    
    def generate_recommendations(self, prompt: str, temperature: float = 0.7) -> dict:
        """
        Generate destination recommendations using Groq API.
        Returns a parsed dict with recommendations array.
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert travel curator with global destination knowledge. "
                                "You MUST respond with valid JSON only - no markdown, no extra text, no code fences. "
                                "Follow the schema given in the user prompt exactly."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=temperature,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                )

                raw = response.choices[0].message.content.strip()

                try:
                    parsed = self._parse_json_response(raw)
                    logger.info(f"Recommendations generated successfully on attempt {attempt + 1}")
                    return parsed
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"The AI returned malformed output. Please try again. (Detail: {e})"
                    ) from e

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                continue
        
        # All retries exhausted
        logger.error(f"Failed to generate recommendations after {self.max_retries} attempts")
        raise last_error or ValueError("Failed to generate recommendations")
