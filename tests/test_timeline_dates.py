import re
import unittest
from pathlib import Path


INDEX_HTML = Path(__file__).resolve().parents[1] / "index.html"


class TimelineDateTests(unittest.TestCase):
    def test_all_experiences_use_month_and_year(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        timeline = re.search(r'<section id="timeline">(.*?)</section>', html, re.DOTALL)

        self.assertIsNotNone(timeline)
        dates = re.findall(
            r'<div class="timeline-date">(.*?)</div>', timeline.group(1), re.DOTALL
        )
        self.assertEqual(
            dates,
            [
                '<time datetime="2026-09">Sep 2026</time> &ndash; Present',
                '<time datetime="2026-06">Jun 2026</time> &ndash; '
                '<time datetime="2026-08">Aug 2026</time>',
                '<time datetime="2023-08">Aug 2023</time> &ndash; '
                '<time datetime="2026-06">Jun 2026</time>',
            ],
        )


if __name__ == "__main__":
    unittest.main()
