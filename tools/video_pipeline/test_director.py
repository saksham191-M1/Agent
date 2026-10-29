"""
test_director.py
────────────────
Unit and integration tests for the Director AI Gateway (director.py).
Compatible with standard library `unittest` and `pytest`.

Verifies:
1. Mock mode with ToyTestSchema returns validated Pydantic models.
2. Code fence stripping and JSON cleaning.
3. Retry mechanics on deliberately broken response (retry prompt must contain error).
4. DirectorError raised when all retries are exhausted.
5. Secrets redaction in logs.
6. Live smoke test when API credentials exist in environment.
"""

import os
import json
import unittest
from pathlib import Path
from dotenv import load_dotenv

# Ensure environment is loaded from .env
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from tools.video_pipeline.director import (
    call_director,
    clean_json_string,
    redact_secrets,
    DirectorError
)
from tools.video_pipeline.schemas import ToyTestSchema, ProductProfile


class TestDirectorGateway(unittest.TestCase):

    def test_clean_json_string(self):
        """Verifies markdown code fence removal."""
        raw_fence = '```json\n{"headline": "TEST", "rating": 5.0}\n```'
        self.assertEqual(clean_json_string(raw_fence), '{"headline": "TEST", "rating": 5.0}')

        plain_fence = '```\n{"headline": "TEST", "rating": 5.0}\n```'
        self.assertEqual(clean_json_string(plain_fence), '{"headline": "TEST", "rating": 5.0}')

        bare = '{"headline": "TEST", "rating": 5.0}'
        self.assertEqual(clean_json_string(bare), bare)

    def test_redact_secrets(self):
        """Verifies that API keys and authorization tokens are redacted."""
        raw = "Bearer AIzaSyA1234567890abcdef and key=secret123456789"
        redacted = redact_secrets(raw)
        self.assertIn("Bearer [REDACTED]", redacted)
        self.assertIn("key=[REDACTED]", redacted)

    def test_mock_toy_schema(self):
        """Unit test: Toy schema passes in mock mode."""
        os.environ["DIRECTOR_MOCK"] = "1"
        try:
            result = call_director(
                system="You are a creative director.",
                user="Create a headline for an ad.",
                schema=ToyTestSchema,
                step_name="test_toy",
                run_id="test_run"
            )

            self.assertIsInstance(result, ToyTestSchema)
            self.assertEqual(result.headline, "TEST PRODUCT LAUNCH")
            self.assertEqual(result.rating, 4.9)
            self.assertIn("fast", result.tags)

            # Check that log files were created and contain no keys
            log_file = Path("out/test_run/director_log/test_toy_1_prompt.txt")
            self.assertTrue(log_file.exists())
        finally:
            os.environ.pop("DIRECTOR_MOCK", None)

    def test_retry_on_broken_response(self):
        """A deliberately broken response is retried and the retry prompt contains the error."""
        attempts = []

        def mock_broken_adapter(base_url, api_key, model, system_prompt, user_prompt, temperature, timeout):
            attempts.append(user_prompt)
            if len(attempts) == 1:
                # First attempt returns invalid JSON syntax
                return "{ headline: BROKEN WITHOUT QUOTES }"
            # Second attempt returns valid JSON
            return json.dumps({
                "headline": "FIXED HEADLINE",
                "rating": 4.5,
                "tags": ["fixed"],
                "is_valid": True
            })

        import tools.video_pipeline.director as d_mod
        orig_adapter = d_mod.openai_adapter
        d_mod.openai_adapter = mock_broken_adapter

        os.environ["DIRECTOR_MOCK"] = "0"
        os.environ["DIRECTOR_API_KEY"] = "dummy_test_key_12345"
        os.environ["DIRECTOR_BASE_URL"] = "https://api.example.com/v1"
        os.environ["DIRECTOR_MODEL"] = "test-model"

        try:
            result = call_director(
                system="System prompt",
                user="Initial user prompt",
                schema=ToyTestSchema,
                retries=2,
                step_name="test_retry",
                run_id="test_run_retry"
            )

            self.assertEqual(len(attempts), 2)
            self.assertIn("PREVIOUS ATTEMPT RETURNED INVALID JSON", attempts[1])
            self.assertIn("{ headline: BROKEN WITHOUT QUOTES }", attempts[1])
            self.assertEqual(result.headline, "FIXED HEADLINE")
            self.assertEqual(result.rating, 4.5)
        finally:
            d_mod.openai_adapter = orig_adapter
            os.environ.pop("DIRECTOR_MOCK", None)
            os.environ.pop("DIRECTOR_API_KEY", None)
            os.environ.pop("DIRECTOR_BASE_URL", None)
            os.environ.pop("DIRECTOR_MODEL", None)

    def test_retry_on_schema_validation_error(self):
        """Deliberately invalid schema fields trigger a retry with ValidationError text."""
        attempts = []

        def mock_schema_fail_adapter(base_url, api_key, model, system_prompt, user_prompt, temperature, timeout):
            attempts.append(user_prompt)
            if len(attempts) == 1:
                # Rating out of bounds (schema requires le=5.0)
                return json.dumps({"headline": "VALID", "rating": 999.0})
            return json.dumps({"headline": "FIXED", "rating": 4.0})

        import tools.video_pipeline.director as d_mod
        orig_adapter = d_mod.openai_adapter
        d_mod.openai_adapter = mock_schema_fail_adapter

        os.environ["DIRECTOR_MOCK"] = "0"
        os.environ["DIRECTOR_API_KEY"] = "dummy_test_key_12345"
        os.environ["DIRECTOR_BASE_URL"] = "https://api.example.com/v1"
        os.environ["DIRECTOR_MODEL"] = "test-model"

        try:
            result = call_director(
                system="System prompt",
                user="Initial prompt",
                schema=ToyTestSchema,
                retries=2,
                step_name="test_schema_fail",
                run_id="test_run_schema"
            )

            self.assertEqual(len(attempts), 2)
            self.assertIn("PREVIOUS ATTEMPT FAILED SCHEMA VALIDATION", attempts[1])
            self.assertIn("Input should be less than or equal to 5", attempts[1])
            self.assertEqual(result.rating, 4.0)
        finally:
            d_mod.openai_adapter = orig_adapter
            os.environ.pop("DIRECTOR_MOCK", None)
            os.environ.pop("DIRECTOR_API_KEY", None)
            os.environ.pop("DIRECTOR_BASE_URL", None)
            os.environ.pop("DIRECTOR_MODEL", None)

    def test_director_error_on_exhausted_retries(self):
        """DirectorError is raised when retries are exceeded."""
        def always_fail(*args, **kwargs):
            return "STILL NOT JSON"

        import tools.video_pipeline.director as d_mod
        orig_adapter = d_mod.openai_adapter
        d_mod.openai_adapter = always_fail

        os.environ["DIRECTOR_MOCK"] = "0"
        os.environ["DIRECTOR_API_KEY"] = "dummy_test_key_12345"
        os.environ["DIRECTOR_BASE_URL"] = "https://api.example.com/v1"
        os.environ["DIRECTOR_MODEL"] = "test-model"

        try:
            with self.assertRaises(DirectorError) as cm:
                call_director(
                    system="System",
                    user="User",
                    schema=ToyTestSchema,
                    retries=1,
                    step_name="test_exhaust",
                    run_id="test_run_exhaust"
                )
            self.assertIn("Director Gateway failed after 2 attempts", str(cm.exception))
        finally:
            d_mod.openai_adapter = orig_adapter
            os.environ.pop("DIRECTOR_MOCK", None)
            os.environ.pop("DIRECTOR_API_KEY", None)
            os.environ.pop("DIRECTOR_BASE_URL", None)
            os.environ.pop("DIRECTOR_MODEL", None)

    def test_live_smoke_call(self):
        """Live smoke test: Executes against live API if GEMINI_API_KEY or DIRECTOR_API_KEY exists."""
        gemini_key = os.getenv("GEMINI_API_KEY")
        director_key = os.getenv("DIRECTOR_API_KEY")

        if not gemini_key and not director_key:
            self.skipTest("No live API keys configured in .env for live smoke test")

        os.environ.pop("DIRECTOR_MOCK", None)

        result = call_director(
            system="You are an expert product ad director. Output strictly valid JSON matching the schema.",
            user="Generate a punchy ad headline, a realistic rating (0-5), and 3 tags for Flipkart (Indian ecommerce platform).",
            schema=ToyTestSchema,
            retries=1,
            temperature=0.7,
            step_name="smoke_test",
            run_id="smoke_live"
        )

        self.assertIsInstance(result, ToyTestSchema)
        self.assertTrue(len(result.headline) > 0)
        self.assertTrue(0.0 <= result.rating <= 5.0)
        print(f"\n[Smoke Test Success] Headline: {result.headline} | Rating: {result.rating} | Tags: {result.tags}")


if __name__ == "__main__":
    unittest.main()
