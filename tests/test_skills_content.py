import re
import unittest
from pathlib import Path


INDEX_HTML = Path(__file__).resolve().parents[1] / "index.html"


class LanguageSkillTests(unittest.TestCase):
    def setUp(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        languages = re.search(
            r"<dt>Languages</dt>\s*<dd>(.*?)</dd>", html, flags=re.DOTALL
        )

        self.assertIsNotNone(languages)
        self.languages = languages.group(1)

    def test_languages_state_proficiency_without_test_scores(self):
        self.assertEqual(
            self.languages,
            "Norwegian (native), Chinese (native), English (fluent), "
            "Swedish (professional proficiency)",
        )

    def test_languages_omit_certificates_and_cefr_levels(self):
        self.assertNotIn("IELTS", self.languages)
        self.assertNotRegex(self.languages, r"\b[ABC][12]\b")


if __name__ == "__main__":
    unittest.main()
