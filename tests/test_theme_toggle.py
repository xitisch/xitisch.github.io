import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ThemeToggleTests(unittest.TestCase):
    def test_theme_toggle_has_accessible_markup(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        button = re.search(
            r'<button class="theme-toggle".*?</button>', html, re.DOTALL
        )

        self.assertEqual(html.count('<script src="theme.js"></script>'), 1)
        self.assertEqual(html.count('class="theme-toggle"'), 1)
        self.assertIsNotNone(button)
        self.assertIn('type="button"', button.group(0))
        self.assertIn('aria-label="Switch to dark theme"', button.group(0))
        self.assertIn('aria-pressed="false"', button.group(0))
        self.assertIn(" hidden", button.group(0))
        self.assertEqual(button.group(0).count('aria-hidden="true"'), 2)
        self.assertIn('<meta name="color-scheme" content="light dark">', html)
        self.assertLess(html.index('src="theme.js"'), html.index('href="style.css"'))

    def test_theme_script_detects_and_persists_preference(self):
        script = (ROOT / "theme.js").read_text(encoding="utf-8")

        self.assertIn("(prefers-color-scheme: dark)", script)
        self.assertIn("storedTheme === 'light' || storedTheme === 'dark'", script)
        self.assertIn("readStoredTheme() || systemTheme()", script)
        self.assertIn("localStorage.getItem(storageKey)", script)
        self.assertIn("localStorage.setItem(storageKey, nextTheme)", script)
        self.assertIn("colorPreference.addEventListener('change'", script)
        self.assertIn("if (!hasStoredPreference)", script)
        self.assertIn("'aria-label'", script)
        self.assertIn("'aria-pressed'", script)
        self.assertIn('meta[name="theme-color"]', script)

    def test_dark_palette_is_defined(self):
        css = (ROOT / "style.css").read_text(encoding="utf-8")
        dark_theme = re.search(
            r':root\[data-theme="dark"\]\s*\{(.*?)\}', css, re.DOTALL
        )
        expected_tokens = {
            "--bg",
            "--surface",
            "--text",
            "--text-muted",
            "--border",
            "--border-strong",
            "--accent",
            "--accent-hover",
            "--accent-soft",
            "--accent-solid",
            "--accent-solid-hover",
            "--current",
            "--link-decoration",
            "--focus-ring",
            "--selection",
        }

        self.assertIsNotNone(dark_theme)
        dark_tokens = set(re.findall(r"(--[\w-]+)\s*:", dark_theme.group(1)))
        self.assertTrue(expected_tokens.issubset(dark_tokens))
        self.assertIn("color-scheme: dark", dark_theme.group(1))
        self.assertIn(".theme-toggle:focus-visible", css)
        self.assertIn(".theme-toggle { display: none; }", css)


if __name__ == "__main__":
    unittest.main()
