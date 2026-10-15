import re
import struct
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "index.html"

EXPECTED_ANIMATIONS = {
    "images/orca-hand.gif": (320, 400),
    "images/flapping-wing.gif": (640, 360),
}

# Loop length in seconds. The flapping clip is trimmed so the wings never rest.
EXPECTED_DURATIONS = {
    "images/orca-hand.gif": 11.1,
    "images/flapping-wing.gif": 5.6,
}


class PictureParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_picture = False
        self.pictures = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "picture":
            self.in_picture = True
            self.pictures.append({"sources": []})
        elif tag == "source" and self.in_picture:
            self.pictures[-1]["sources"].append(attributes)
        elif tag == "img" and self.in_picture:
            self.pictures[-1]["img"] = attributes

    def handle_endtag(self, tag):
        if tag == "picture":
            self.in_picture = False


def gif_frame_delays(data):
    """Walk the GIF block structure and return each frame's delay in centiseconds."""

    def skip_sub_blocks(offset):
        while data[offset]:
            offset += data[offset] + 1
        return offset + 1

    flags = data[10]
    offset = 13 + (3 * 2 ** ((flags & 7) + 1) if flags & 0x80 else 0)
    delays = []
    while data[offset] != 0x3B:
        if data[offset] == 0x21:
            if data[offset + 1] == 0xF9:
                delays.append(struct.unpack("<H", data[offset + 4:offset + 6])[0])
            offset = skip_sub_blocks(offset + 2)
        elif data[offset] == 0x2C:
            local = data[offset + 9]
            offset += 10 + (3 * 2 ** ((local & 7) + 1) if local & 0x80 else 0)
            offset = skip_sub_blocks(offset + 1)
        else:
            raise AssertionError(f"unexpected GIF block 0x{data[offset]:02x}")
    return delays


def jpeg_size(data):
    offset = 2
    while offset < len(data):
        marker, length = struct.unpack(">2sH", data[offset:offset + 4])
        if marker[1] in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(">HH", data[offset + 5:offset + 9])
            return width, height
        offset += 2 + length
    raise AssertionError("no JPEG frame header")


class ProjectAnimationTests(unittest.TestCase):
    def setUp(self):
        self.html = INDEX_HTML.read_text(encoding="utf-8")
        parser = PictureParser()
        parser.feed(self.html)
        self.pictures = {picture["img"]["src"]: picture for picture in parser.pictures}

    def test_animations_sit_in_their_projects(self):
        self.assertEqual(set(self.pictures), set(EXPECTED_ANIMATIONS))
        self.assertLess(self.html.index("ORCA Robotic Hand</h3>"), self.html.index("images/orca-hand.gif"))
        self.assertLess(
            self.html.index("Biomimetic Flapping-Wing Robot"), self.html.index("images/flapping-wing.gif")
        )

    def test_gifs_loop_forever_and_match_their_markup(self):
        for src, (width, height) in EXPECTED_ANIMATIONS.items():
            data = (ROOT / src).read_bytes()
            self.assertEqual(data[:6], b"GIF89a", src)
            self.assertEqual(struct.unpack("<HH", data[6:10]), (width, height), src)
            self.assertIn(b"NETSCAPE2.0\x03\x01\x00\x00", data, f"{src} does not loop forever")
            self.assertGreater(len(gif_frame_delays(data)), 50, f"{src} has too few frames")
            self.assertLess(len(data), 10 * 1024 * 1024, src)

            img = self.pictures[src]["img"]
            self.assertEqual((img.get("width"), img.get("height")), (str(width), str(height)))
            self.assertGreater(len(img.get("alt", "")), 30)
            self.assertEqual(img.get("loading"), "lazy")

    def test_gifs_have_the_expected_loop_length(self):
        for src, seconds in EXPECTED_DURATIONS.items():
            duration = sum(gif_frame_delays((ROOT / src).read_bytes())) / 100
            self.assertAlmostEqual(duration, seconds, delta=0.15, msg=src)

    def test_reduced_motion_gets_a_still_frame_with_the_same_shape(self):
        for src, (width, height) in EXPECTED_ANIMATIONS.items():
            sources = self.pictures[src]["sources"]
            self.assertEqual(len(sources), 1, src)
            self.assertEqual(sources[0].get("media"), "(prefers-reduced-motion: reduce)")
            poster = ROOT / sources[0]["srcset"]
            data = poster.read_bytes()
            self.assertEqual(data[:3], b"\xff\xd8\xff")
            self.assertLess(len(data), 200 * 1024)
            poster_width, poster_height = jpeg_size(data)
            self.assertAlmostEqual(poster_width / poster_height, width / height, places=2)

    def test_no_video_players_or_scripts_remain(self):
        self.assertNotIn("<video", self.html)
        self.assertNotIn("media.js", self.html)
        self.assertFalse((ROOT / "media.js").exists())

    def test_orca_entry_names_the_course_its_term_and_the_learning_work(self):
        article = re.search(
            r'<article class="project">(?:(?!</article>).)*?ORCA Robotic Hand</h3>.*?</article>',
            self.html,
            flags=re.DOTALL,
        ).group(0)

        self.assertIn(
            '<div class="project-date"><time datetime="2026-09">Sep</time> &ndash; '
            '<time datetime="2026-12">Dec 2026</time></div>',
            article,
        )
        self.assertIn("Real-World Robotics Project Course &middot; ETH Z&uuml;rich", article)
        for topic in ("imitation learning", "reinforcement learning", "reward model",
                      "long-horizon task", "robotic arm", "locate and grasp"):
            self.assertIn(topic, article)
        self.assertNotIn("Real World Robotics", article)

    def test_original_camera_files_are_not_committed(self):
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").split()

        self.assertIn("*.MOV", ignored)
        self.assertIn("*.mov", ignored)


if __name__ == "__main__":
    unittest.main()
