import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "index.html"
STYLE_CSS = ROOT / "style.css"
IMAGES = ROOT / "images"

SECTIONS = {"about", "logos", "orca-hand", "flapping-wing", "thesis", "rocket"}


def tracked_media():
    return {
        path.relative_to(ROOT).as_posix()
        for path in IMAGES.rglob("*")
        if path.is_file() and not path.name.startswith(".") and path.suffix != ".JPG"
    }


class MediaLayoutTests(unittest.TestCase):
    def setUp(self):
        self.html = INDEX_HTML.read_text(encoding="utf-8")
        self.referenced = set(re.findall(r'(?:src|srcset)="(images/[^"]+)"', self.html))

    def test_media_lives_in_one_folder_per_section(self):
        folders = {path.name for path in IMAGES.iterdir() if path.is_dir()}

        self.assertEqual(folders, SECTIONS)
        for path in tracked_media():
            self.assertRegex(path, r"^images/[a-z-]+/[a-z0-9-]+\.(png|jpg|gif|html)$")

    def test_every_referenced_file_exists_and_every_file_is_used(self):
        self.assertEqual(self.referenced, tracked_media())

    def test_media_with_two_themes_comes_in_pairs(self):
        # The class sits on <picture> or <iframe>; take the first path after it.
        light = re.findall(r'class="theme-light-only".*?(?:src|srcset)="([^"]+)"', self.html)
        dark = re.findall(r'class="theme-dark-only".*?(?:src|srcset)="([^"]+)"', self.html)

        self.assertEqual(len(light), 2)
        self.assertEqual([path.replace("light", "dark") for path in light], dark)
        css = STYLE_CSS.read_text(encoding="utf-8")
        self.assertIn(
            ':root[data-theme="dark"] .theme-light-only,\n'
            ':root:not([data-theme="dark"]) .theme-dark-only { display: none; }',
            css,
        )

    def test_rocket_claims_match_the_apogee_animation(self):
        article = re.search(
            r'<article class="project">(?:(?!</article>).)*?Rocket Avionics.*?</article>',
            self.html,
            flags=re.DOTALL,
        ).group(0)

        # Settled errors read from the GIF labels (t = 8.5 s onward).
        self.assertIn("about 1.5&nbsp;s after burnout", article)
        self.assertIn("within <strong>0.6%</strong> of the true apogee", article)
        self.assertIn("up to <strong>4.2%</strong>", article)
        self.assertNotIn("10% to 1.3%", article)

        # Airbrake controller result from the nominal RocketPy simulation.
        self.assertIn("Apogee Prediction &amp; Airbrake Control", article)
        self.assertIn("EuRoC 2025", article)
        self.assertIn("In a nominal RocketPy simulation, it brought the apogee within", article)
        self.assertIn("within <strong>0.2%</strong> of the 3,000&nbsp;m target", article)

        # Prediction came first, so its paragraph and figures precede the controller's.
        paragraphs = re.findall(r'<p class="project-description">(.*?)</p>', article, flags=re.DOTALL)
        self.assertEqual(len(paragraphs), 2)
        self.assertIn("apogee prediction", paragraphs[0])
        self.assertIn("airbrake controller", paragraphs[1])
        self.assertLess(article.index(paragraphs[0]), article.index("apogee-light.gif"))
        self.assertLess(article.index("trajectory-light.html"), article.index(paragraphs[1]))
        for text in paragraphs + re.findall(r"<figcaption>(.*?)</figcaption>", article):
            self.assertNotIn(":", text)
        self.assertNotIn("2.7%", article)
        for detail in ("CFD", "rate-limited"):
            self.assertNotIn(detail, article)

    def test_trajectory_embeds_are_lazy_and_load_only_pinned_plotly(self):
        iframes = re.findall(r"<iframe [^>]*></iframe>", self.html)
        self.assertEqual(len(iframes), 2)
        trajectory = self.html.index("<summary>Interactive 3D trajectory</summary>")
        for iframe in iframes:
            self.assertGreater(self.html.index(iframe), trajectory)
            self.assertIn('loading="lazy"', iframe)
            self.assertRegex(iframe, r'title="[^"]{30,}"')

        for theme in ("light", "dark"):
            page = (IMAGES / "rocket" / f"trajectory-{theme}.html").read_text(encoding="utf-8")
            scripts = re.findall(r'<script[^>]*src="([^"]+)"[^>]*>', page)
            self.assertEqual(scripts, ["https://cdn.plot.ly/plotly-4.1.1.min.js"])
            self.assertIn('integrity="sha256-', page)
            self.assertIn("margin: 0;", page)


if __name__ == "__main__":
    unittest.main()
