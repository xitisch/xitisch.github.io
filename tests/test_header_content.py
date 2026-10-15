import re
import unittest
from pathlib import Path


INDEX_HTML = Path(__file__).resolve().parents[1] / "index.html"


class HeaderContentTests(unittest.TestCase):
    def test_page_title_contains_only_the_name(self):
        html = INDEX_HTML.read_text(encoding="utf-8")

        self.assertIn("<title>Xiangtian Shi</title>", html)
        self.assertNotIn("<title>Xiangtian Shi | Robotics and Control</title>", html)

    def test_cv_link_uses_minimal_label(self):
        html = INDEX_HTML.read_text(encoding="utf-8")

        self.assertIn("<span>CV</span>", html)
        self.assertNotIn("<span>View CV</span>", html)

    def test_cv_link_points_to_the_committed_pdf(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        link = re.search(r'<a class="primary-link" href="([^"]+)"', html)

        self.assertIsNotNone(link)
        self.assertEqual(link.group(1), "CV_Xiangtian_Shi.pdf")
        pdf = INDEX_HTML.parent / link.group(1)
        self.assertTrue(pdf.is_file())
        self.assertEqual(pdf.read_bytes()[:5], b"%PDF-")

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

    def _about_section(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        about = re.search(
            r'<section id="about">(.*?)</section>', html, flags=re.DOTALL
        )

        self.assertIsNotNone(about)
        return about.group(1)

    def test_research_interests_stand_in_their_own_paragraph(self):
        about = self._about_section()

        self.assertRegex(
            about,
            r"<p>\s*I'm interested in physics-based modeling and simulation,"
            r".*?sim-to-real robotics\.\s*</p>",
        )

    def test_personal_interests_and_esports_close_the_about_section(self):
        about = self._about_section()

        self.assertRegex(
            about,
            r"Outside my studies, I enjoy hiking, skiing, jogging,"
            r".*?professional PUBG Mobile player.*?competing internationally\."
            r"\s*</p>\s*</div>\s*</div>\s*$",
        )

    def test_esports_paragraph_states_the_result_from_the_cv(self):
        about = self._about_section()

        self.assertIn("PUBG Mobile Pro League Western Europe Spring 2021", about)
        self.assertIn("two years", about)

    def test_esports_title_links_to_the_liquipedia_tournament_page(self):
        about = self._about_section()

        self.assertRegex(
            about,
            r'<a href="https://liquipedia\.net/pubgmobile/PUBG_Mobile_Pro_League'
            r'/Western_Europe/Season_1">'
            r"PUBG Mobile Pro League Western Europe Spring 2021</a>",
        )

    def test_about_copy_has_no_stray_blank_lines_inside_paragraphs(self):
        about = self._about_section()

        for paragraph in re.findall(r"<p>(.*?)</p>", about, flags=re.DOTALL):
            self.assertNotRegex(paragraph, r"\n\s*\n")

    def test_footer_lists_locations_without_duplicate_email(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        footer = re.search(r"<footer>(.*?)</footer>", html, flags=re.DOTALL)

        self.assertIsNotNone(footer)
        self.assertIn("Zürich, Switzerland &middot; Oslo, Norway", footer.group(1))
        self.assertNotIn("mailto:", footer.group(1))
        self.assertNotIn("xiangtian.shi@outlook.com", footer.group(1))


if __name__ == "__main__":
    unittest.main()
