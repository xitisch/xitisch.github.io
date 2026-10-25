import re
import unittest
from pathlib import Path


INDEX_HTML = Path(__file__).resolve().parents[1] / "index.html"

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


class TimelineDateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = INDEX_HTML.read_text(encoding="utf-8")

    def section(self, name):
        found = re.search(rf'<section id="{name}">(.*?)</section>', self.html, re.DOTALL)
        self.assertIsNotNone(found, f"no <section id=\"{name}\"> in index.html")
        return found.group(1)

    def dates(self, section, css_class):
        return re.findall(
            rf'<div class="{css_class}">(.*?)</div>', section, re.DOTALL
        )

    def stamps(self, date):
        return re.findall(r'<time datetime="([^"]+)">(.*?)</time>', date, re.DOTALL)

    def test_timeline_entries_use_years_alone(self):
        dates = self.dates(self.section("timeline"), "timeline-date")

        self.assertEqual(len(dates), 3)
        for date in dates:
            stamps = self.stamps(date)
            self.assertTrue(stamps, f"no <time> in timeline date {date!r}")
            for datetime_attr, text in stamps:
                self.assertRegex(datetime_attr, r"^\d{4}$")
                self.assertEqual(text, datetime_attr)
            self.assertNotIn(
                "Present",
                "".join(text for _, text in stamps),
                "Present belongs outside the <time> element",
            )

    def test_project_entries_use_month_and_year(self):
        dates = self.dates(self.section("projects"), "project-date")

        self.assertEqual(len(dates), 5)
        for date in dates:
            stamps = self.stamps(date)
            self.assertTrue(stamps, f"no <time> in project date {date!r}")
            for datetime_attr, text in stamps:
                self.assertRegex(datetime_attr, r"^\d{4}-(0[1-9]|1[0-2])$")
                self.assertTrue(
                    text.startswith(MONTHS[int(datetime_attr[-2:]) - 1]),
                    f"{text!r} does not name the month in {datetime_attr!r}",
                )

    def test_every_date_closes_its_time_elements(self):
        for css_class in ("timeline-date", "project-date"):
            for date in self.dates(self.html, css_class):
                self.assertEqual(
                    date.count("<time"), date.count("</time>"),
                    f"unbalanced <time> tags in {date!r}",
                )


if __name__ == "__main__":
    unittest.main()
