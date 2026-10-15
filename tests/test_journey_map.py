import importlib.util
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "index.html"
STYLE_CSS = ROOT / "style.css"
GENERATOR = ROOT / "tools" / "build_journey_map.py"

EXPECTED_STOPS = [
    ("China", "Where it started"),
    ("Oslo, Norway", "Home"),
    ("Stockholm, Sweden", "B.Sc. at KTH"),
    ("Beijing, China", "Research at Tsinghua"),
    ("Zürich, Switzerland", "M.Sc. at ETH"),
]


def load_generator():
    spec = importlib.util.spec_from_file_location("build_journey_map", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class JourneyMapTests(unittest.TestCase):
    def setUp(self):
        self.html = INDEX_HTML.read_text(encoding="utf-8")
        journey = re.search(
            r'<section id="journey">(.*?)</section>', self.html, flags=re.DOTALL
        )

        self.assertIsNotNone(journey)
        self.journey = journey.group(1)

    def test_journey_sits_between_about_and_timeline(self):
        about = self.html.index('<section id="about">')
        journey = self.html.index('<section id="journey">')
        timeline = self.html.index('<section id="timeline">')

        self.assertLess(about, journey)
        self.assertLess(journey, timeline)
        self.assertIn("<h2>Journey</h2>", self.journey)

    def test_legend_lists_the_stops_in_order_without_years(self):
        stops = re.findall(
            r'<span class="journey-stop-place">(.*?)</span> '
            r'<span class="journey-stop-note">(.*?)</span>',
            self.journey,
        )

        self.assertEqual(stops, EXPECTED_STOPS)
        self.assertNotRegex(self.journey, r"\b(19|20)\d\d\b")

    def test_map_pins_match_the_legend_and_mark_the_current_stop(self):
        labels = re.findall(r'<span class="journey-pin-label">(.*?)</span>', self.journey)
        numbers = re.findall(r'<span class="journey-pin-number">(\d+)</span>', self.journey)
        routes = re.findall(r'<path class="journey-route" d="[^"]+"/>', self.journey)

        self.assertEqual(labels, [place.split(",")[0] for place, _ in EXPECTED_STOPS])
        self.assertEqual(numbers, ["1", "2", "3", "4", "5"])
        self.assertEqual(len(routes), len(EXPECTED_STOPS) - 1)
        self.assertRegex(
            self.journey,
            r'<span class="journey-pin journey-pin-\w+ current"[^>]*>'
            r'<span class="journey-pin-number">5</span>',
        )
        self.assertIn('<li class="journey-stop current">', self.journey)

    def test_pins_are_placed_where_the_generator_projects_them(self):
        generator = load_generator()
        project, height = generator.make_projection()
        positions = [
            tuple(map(float, match))
            for match in re.findall(
                r'style="left: ([\d.]+)%; top: ([\d.]+)%"', self.journey
            )
        ]

        self.assertEqual(len(positions), len(generator.STOPS))
        for (left, top), stop in zip(positions, generator.STOPS):
            x, y = project(stop[2], stop[3])
            self.assertAlmostEqual(left, x / generator.WIDTH * 100, places=1)
            self.assertAlmostEqual(top, y / height * 100, places=1)
            self.assertTrue(0 < left < 100 and 0 < top < 100)
        self.assertIn(f'viewBox="0 0 {generator.WIDTH} {height}"', self.journey)

    def test_map_is_decorative_and_the_ordered_list_carries_the_content(self):
        self.assertIn('<div class="journey-map" aria-hidden="true">', self.journey)
        self.assertIn('<ol class="journey-stops">', self.journey)
        self.assertIn('<figcaption class="visually-hidden">', self.journey)
        self.assertEqual(self.journey.count("<!-- journey-map:start -->"), 1)
        self.assertEqual(self.journey.count("<!-- journey-map:end -->"), 1)

    def test_inline_map_keeps_the_page_light(self):
        self.assertLess(len(self.html.encode("utf-8")), 60 * 1024)

    def test_map_colours_follow_both_themes(self):
        css = STYLE_CSS.read_text(encoding="utf-8")
        light = re.search(r":root\s*\{(.*?)\}", css, re.DOTALL).group(1)
        dark = re.search(r':root\[data-theme="dark"\]\s*\{(.*?)\}', css, re.DOTALL).group(1)

        for palette in (light, dark):
            self.assertIn("--map-land:", palette)
            self.assertIn("--map-visited:", palette)
        self.assertIn("vector-effect: non-scaling-stroke", css)


if __name__ == "__main__":
    unittest.main()
