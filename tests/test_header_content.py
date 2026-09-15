import unittest
from pathlib import Path


INDEX_HTML = Path(__file__).resolve().parents[1] / "index.html"


class HeaderContentTests(unittest.TestCase):
    def test_research_area_kicker_is_removed(self):
        html = INDEX_HTML.read_text(encoding="utf-8")

        self.assertNotIn("Robotics &middot; Control &middot; Physical AI", html)
        self.assertNotIn('class="header-kicker"', html)


if __name__ == "__main__":
    unittest.main()
