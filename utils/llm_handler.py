"""
LLM Handler - Manages Groq API interactions with retry logic.
"""
import os
import json
import time
import logging
from groq import Groq
from dotenv import load_dotenv
from utils.validation import validate_itinerary_response, ValidationError

load_dotenv()
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
                    max_tokens=3000,
                )

                raw = response.choices[0].message.content.strip()

                # Strip accidental code fences if the model adds them despite instructions
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                    raw = raw.strip()

                try:
                    parsed = json.loads(raw)
                    # Validate response schema
                    validated = validate_itinerary_response(parsed)
                    logger.info(f"Itinerary generated successfully on attempt {attempt + 1}")
                    return validated
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"The AI returned malformed output. Please try again. (Detail: {e})"
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
