"""Natural-language ad intake tests; no provider or renderer calls."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from studio.intake import parse_ad_prompt
from studio.models import StudioError
from studio.service import StudioService


class PromptIntakeTests(unittest.TestCase):
    def test_complete_labelled_prompt_becomes_a_valid_brief(self):
        result = parse_ad_prompt(
            """Create a 15-second vertical ad.
            Product: SkillMe
            Description: An open-source internship platform where students ship real engineering work.
            Audience: College students building a software portfolio
            Benefits: Real projects; Public GitHub proof; Career support
            CTA: Apply to SkillMe
            Color: #c99a4e
            """
        )
        self.assertTrue(result.complete)
        self.assertEqual(result.brief["name"], "SkillMe")
        self.assertEqual(result.brief["duration"], 15)
        self.assertEqual(result.brief["aspect"], "9:16")
        self.assertEqual(result.brief["benefits"], ["Real projects", "Public GitHub proof", "Career support"])

    def test_sentence_prompt_extracts_conveniences_without_inventing_facts(self):
        result = parse_ad_prompt(
            "Create a 15-second ad for SkillMe. It helps students build public proof of work. "
            "Target audience: college students. Benefits include real projects, GitHub proof. CTA is Apply now."
        )
        self.assertTrue(result.complete)
        self.assertEqual(result.brief["name"], "SkillMe")
        self.assertEqual(result.brief["audience"], "college students")
        self.assertEqual(result.brief["duration"], 15)
        self.assertEqual(result.brief["benefits"], ["real projects", "GitHub proof"])

    def test_incomplete_prompt_reports_missing_facts(self):
        result = parse_ad_prompt("Make an ad for SkillMe.")
        self.assertFalse(result.complete)
        self.assertIn("product description", result.missing)
        self.assertIn("target audience", result.missing)
        self.assertIn("verified product benefit", result.missing[2])

    def test_incomplete_prompt_does_not_create_a_project(self):
        with tempfile.TemporaryDirectory() as directory:
            service = StudioService(Path(directory), load_environment=False)
            with self.assertRaisesRegex(StudioError, "product description"):
                service.create_prompt_project("Make an ad for SkillMe.")
            self.assertEqual(service.list_projects(), [])

    def test_complete_prompt_uses_template_mode_without_network(self):
        with tempfile.TemporaryDirectory() as directory, patch("studio.providers.requests.post") as post:
            service = StudioService(Path(directory), load_environment=False)
            project = service.create_prompt_project(
                "Product: SkillMe\nDescription: Open-source engineering internships.\n"
                "Audience: College students\nBenefits: Real projects; GitHub proof\nCTA: Apply now"
            )
            post.assert_not_called()
            self.assertEqual(project["copy_mode"], "template")
            self.assertEqual(project["brief"]["name"], "SkillMe")


if __name__ == "__main__":
    unittest.main()
