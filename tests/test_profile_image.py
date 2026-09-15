import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "index.html"


class ProfileImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.profile_images = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = attributes.get("class", "").split()
        if tag == "img" and "profile-photo" in classes:
            self.profile_images.append(attributes)


class ProfileImageTests(unittest.TestCase):
    def setUp(self):
        parser = ProfileImageParser()
        parser.feed(INDEX_HTML.read_text(encoding="utf-8"))
        self.assertEqual(len(parser.profile_images), 1)
        self.image = parser.profile_images[0]

    def test_profile_image_has_accessible_markup(self):
        self.assertEqual(self.image.get("src"), "images/portrait.jpg")
        self.assertEqual(self.image.get("alt"), "Portrait of Xiangtian Shi")
        self.assertEqual(self.image.get("width"), "900")
        self.assertEqual(self.image.get("height"), "1200")
        self.assertEqual(self.image.get("decoding"), "async")

    def test_profile_image_asset_exists_and_is_jpeg(self):
        image_path = ROOT / self.image["src"]
        self.assertTrue(image_path.is_file())
        image_bytes = image_path.read_bytes()
        self.assertEqual(image_bytes[:3], b"\xff\xd8\xff")
        self.assertLess(len(image_bytes), 1024 * 1024)
        self.assertNotIn(b"Exif\x00\x00", image_bytes)


if __name__ == "__main__":
    unittest.main()
