"""Explicit Groq brief assistance; all provider requests are mocked."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from studio.models import StudioError
from studio.providers import GROQ_DEFAULT_MODEL, suggest_brief_fields
from studio.service import StudioService

FACTS = ("Product", "A workspace that keeps project tasks and notes together.", "Small teams")
SUGGESTION = {"problem": "Project tasks and notes get scattered across tools.",
              "benefits": ["Keep tasks and notes in one workspace"]}


def response(content):
    result = Mock(status_code=200)
    result.json.return_value = {"choices": [{"message": {"content": content}}]}
    return result


class GroqTests(unittest.TestCase):
    def test_missing_or_invalid_config_does_not_contact_any_provider(self):
        for config in ({"GROQ_API_KEY": " "}, {"GROQ_API_KEY": "test-only", "GROQ_MODEL": "https://wrong.example/model"}):
            with self.subTest(config=config), patch.dict(os.environ, config), patch("studio.providers.requests.post") as post:
                with self.assertRaises(StudioError):
                    suggest_brief_fields(*FACTS)
                post.assert_not_called()

    def test_json_suggestions_use_only_groq_and_do_not_save_projects(self):
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, {"GROQ_API_KEY": "test-only", "GROQ_MODEL": " "}), \
                patch("studio.providers.requests.post", return_value=response(json.dumps(SUGGESTION))) as post:
            service = StudioService(Path(td), load_environment=False)
            result = service.suggest_brief_fields(*FACTS, language="Hindi")
            self.assertEqual(result["problem"], SUGGESTION["problem"])
            self.assertEqual(result["benefits"], SUGGESTION["benefits"][0])
            self.assertEqual(result["model"], GROQ_DEFAULT_MODEL)
            self.assertEqual(service.list_projects(), [])
            self.assertEqual(service.list_products(), [])
            post.assert_called_once()
            self.assertEqual(post.call_args.args[0], "https://api.groq.com/openai/v1/chat/completions")
            self.assertEqual(post.call_args.kwargs["timeout"], (5, 35))
            payload = post.call_args.kwargs["json"]
            self.assertEqual(payload["response_format"], {"type": "json_object"})
            self.assertIn("Hindi", payload["messages"][1]["content"])
            self.assertLessEqual(payload["max_completion_tokens"], 1000)

    def test_bad_response_cannot_replace_a_valid_brief(self):
        invalid = ["not JSON", "[]", json.dumps({**SUGGESTION, "benefits": []}),
                   json.dumps({**SUGGESTION, "problem": "p" * 181}),
                   json.dumps({**SUGGESTION, "benefits": ["b" * 121]}),
                   json.dumps({**SUGGESTION, "benefits": ["Repeated", "repeated"]}),
                   json.dumps({**SUGGESTION, "benefits": "not an array"}),
                   json.dumps({**SUGGESTION, "unexpected": "field"})]
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-only", "GROQ_MODEL": GROQ_DEFAULT_MODEL}):
            for raw in invalid:
                with self.subTest(raw=raw), patch("studio.providers.requests.post", return_value=response(raw)):
                    with self.assertRaises(StudioError):
                        suggest_brief_fields(*FACTS)

    def test_retries_are_bounded_and_errors_do_not_expose_provider_content(self):
        failure = Mock(status_code=429, text="secret provider response")
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-only"}), \
                patch("studio.providers.requests.post", return_value=failure) as post, patch("studio.providers.time.sleep"):
            with self.assertRaisesRegex(StudioError, "Groq is busy or rate-limited") as raised:
                suggest_brief_fields(*FACTS)
            self.assertEqual(post.call_count, 2)
            self.assertNotIn("secret", str(raised.exception))
