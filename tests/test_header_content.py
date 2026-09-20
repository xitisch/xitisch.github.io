import re
import unittest
from pathlib import Path


INDEX_HTML = Path(__file__).resolve().parents[1] / "index.html"


class HeaderContentTests(unittest.TestCase):
    def test_page_title_contains_only_the_name(self):
        html = INDEX_HTML.read_text(encoding="utf-8")

        self.assertIn("<title>Xiangtian Shi</title>", html)
        self.assertNotIn("<title>Xiangtian Shi | Robotics and Control</title>", html)

    def test_research_area_kicker_is_removed(self):
        html = INDEX_HTML.read_text(encoding="utf-8")

        self.assertNotIn("Robotics &middot; Control &middot; Physical AI", html)
        self.assertNotIn('class="header-kicker"', html)

    def test_degree_tagline_is_removed_from_header(self):
        html = INDEX_HTML.read_text(encoding="utf-8")

        self.assertNotIn('class="tagline"', html)

    def test_about_heading_uses_natural_wording(self):
        html = INDEX_HTML.read_text(encoding="utf-8")

        self.assertIn("<h2>About Me</h2>", html)
        self.assertNotIn("<h2>About Myself</h2>", html)

    def test_personal_interests_end_the_about_section(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        about = re.search(
            r'<section id="about">(.*?)</section>', html, flags=re.DOTALL
        )

        self.assertIsNotNone(about)
        self.assertRegex(
            about.group(1),
            r"sim-to-real robotics\. I enjoy hiking, skiing and jogging\.\s*</p>\s*</div>\s*</div>\s*$",
        )


if __name__ == "__main__":
    unittest.main()
