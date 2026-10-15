import re
import struct
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "index.html"
STYLE_CSS = ROOT / "style.css"

THESIS_FIGURES = [
    "images/thesis/three-obstacles.png",
    "images/thesis/circle-vs-square.png",
    "images/thesis/euler-lagrange-y.png",
]


class FigureImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_figure = False
        self.images = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "figure" and "project-figure" in attributes.get("class", ""):
            self.in_figure = True
        elif tag == "img" and self.in_figure:
            self.images.append(attributes)

    def handle_endtag(self, tag):
        if tag == "figure":
            self.in_figure = False


def png_size(path):
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"{path} is not a PNG")
    return struct.unpack(">II", data[16:24])


class ProjectFigureTests(unittest.TestCase):
    def setUp(self):
        self.html = INDEX_HTML.read_text(encoding="utf-8")
        parser = FigureImageParser()
        parser.feed(self.html)
        self.images = [image for image in parser.images if image["src"].endswith(".png")]

    def _thesis_article(self):
        article = re.search(
            r'<article class="project">(?:(?!</article>).)*?Bachelor Thesis.*?</article>',
            self.html,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(article)
        return article.group(0)

    def test_thesis_shows_one_figure_and_tucks_the_rest_behind_details(self):
        article = self._thesis_article()
        visible, _, hidden = article.partition('<details class="project-more">')

        self.assertIn(THESIS_FIGURES[0], visible)
        self.assertIn("<summary>More figures</summary>", hidden)
        for src in THESIS_FIGURES[1:]:
            self.assertIn(src, hidden)
            self.assertNotIn(src, visible)

    def test_figure_images_are_web_sized_pngs_matching_their_markup(self):
        self.assertEqual([image["src"] for image in self.images], THESIS_FIGURES)

        for image in self.images:
            path = ROOT / image["src"]
            self.assertTrue(path.is_file(), image["src"])
            self.assertLess(path.stat().st_size, 300 * 1024, image["src"])
            width, height = png_size(path)
            self.assertLessEqual(width, 1600)
            self.assertEqual((image.get("width"), image.get("height")), (str(width), str(height)))

    def test_figure_images_are_accessible_and_lazy(self):
        for image in self.images:
            self.assertGreater(len(image.get("alt", "")), 40, image["src"])
            self.assertEqual(image.get("loading"), "lazy")
            self.assertEqual(image.get("decoding"), "async")

    def test_every_figure_has_a_caption(self):
        figures = re.findall(
            r'<figure class="project-figure[^"]*">(.*?)</figure>', self.html, flags=re.DOTALL
        )

        self.assertGreaterEqual(len(figures), len(THESIS_FIGURES))
        for figure in figures:
            self.assertRegex(figure, r"<figcaption>\S.*?</figcaption>")

    def test_plots_sit_on_white_cards_in_both_themes(self):
        css = STYLE_CSS.read_text(encoding="utf-8")
        frame = re.search(r"\.project-frame \{(.*?)\}", css, flags=re.DOTALL)

        self.assertIsNotNone(frame)
        self.assertIn("background: #fff;", frame.group(1))
        for src in THESIS_FIGURES:
            self.assertIn(f'<div class="project-frame"><img src="{src}"', self.html)

    def test_media_scales_with_the_page_but_keeps_its_aspect_ratio(self):
        css = STYLE_CSS.read_text(encoding="utf-8")
        rule = re.search(
            r"\.project-frame img \{(.*?)\}", css, flags=re.DOTALL
        )

        self.assertIsNotNone(rule)
        self.assertIn("width: 100%;", rule.group(1))
        self.assertIn("height: auto;", rule.group(1))
        self.assertIn("object-fit: contain;", rule.group(1))
        # Padding or a fixed height on the media itself would distort its ratio.
        self.assertNotIn("padding", rule.group(1))
        self.assertNotRegex(rule.group(1), r"(?<!-)height: \d")


if __name__ == "__main__":
    unittest.main()
