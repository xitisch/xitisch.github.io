import re
import struct
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "index.html"
MEDIA_JS = ROOT / "media.js"

EXPECTED_VIDEOS = {
    "images/orca-hand.mp4": (576, 720),
    "images/flapping-wing.mp4": (960, 540),
}


class VideoParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.videos = []

    def handle_starttag(self, tag, attrs):
        if tag == "video":
            self.videos.append(dict(attrs))


def top_level_box(data, name):
    offset = 0
    while offset + 8 <= len(data):
        size, kind = struct.unpack(">I4s", data[offset:offset + 8])
        if size == 1:
            size = struct.unpack(">Q", data[offset + 8:offset + 16])[0]
        if kind == name:
            return data[offset:offset + size]
        if size == 0:
            break
        offset += size
    raise AssertionError(f"no {name!r} box")


def track_dimensions(moov):
    index = moov.index(b"tkhd")
    version = moov[index + 4]
    offset = index + 4 + (88 if version == 1 else 76)
    width, height = struct.unpack(">II", moov[offset:offset + 8])
    return width >> 16, height >> 16


class ProjectVideoTests(unittest.TestCase):
    def setUp(self):
        self.html = INDEX_HTML.read_text(encoding="utf-8")
        parser = VideoParser()
        parser.feed(self.html)
        self.videos = {video["src"]: video for video in parser.videos}

    def test_expected_videos_are_on_the_page(self):
        self.assertEqual(set(self.videos), set(EXPECTED_VIDEOS))
        orca = self.html.index("images/orca-hand.mp4")
        flapping = self.html.index("images/flapping-wing.mp4")
        self.assertLess(self.html.index("ORCA Robotic Hand"), orca)
        self.assertLess(self.html.index("Biomimetic Flapping-Wing Robot"), flapping)

    def test_videos_are_small_silent_h264_files_without_camera_metadata(self):
        for src, (width, height) in EXPECTED_VIDEOS.items():
            data = (ROOT / src).read_bytes()
            self.assertLess(len(data), 4 * 1024 * 1024, src)
            self.assertEqual(data[4:8], b"ftyp", src)
            moov = top_level_box(data, b"moov")
            self.assertEqual(track_dimensions(moov), (width, height), src)
            self.assertIn(b"avc1", moov, src)
            self.assertNotIn(b"soun", moov, src)
            self.assertNotIn(b"\xa9xyz", moov, src)
            self.assertNotIn(b"location", moov, src)
            # moov before mdat lets browsers start playing before the download ends.
            self.assertLess(data.index(b"moov"), data.index(b"mdat"), src)

    def test_video_markup_matches_files_and_degrades_gracefully(self):
        for src, (width, height) in EXPECTED_VIDEOS.items():
            video = self.videos[src]
            self.assertEqual((video.get("width"), video.get("height")), (str(width), str(height)))
            for attribute in ("muted", "loop", "playsinline", "controls", "data-autoplay"):
                self.assertIn(attribute, video, f"{src} lacks {attribute}")
            self.assertNotIn("autoplay", video)
            self.assertEqual(video.get("preload"), "metadata")
            self.assertGreater(len(video.get("aria-label", "")), 30)
            poster = ROOT / video["poster"]
            self.assertTrue(poster.is_file())
            self.assertEqual(poster.read_bytes()[:3], b"\xff\xd8\xff")
            self.assertLess(poster.stat().st_size, 200 * 1024)

    def test_media_script_respects_reduced_motion(self):
        script = MEDIA_JS.read_text(encoding="utf-8")

        self.assertEqual(self.html.count('<script src="media.js" defer></script>'), 1)
        self.assertIn("(prefers-reduced-motion: reduce)", script)
        self.assertIn("video[data-autoplay]", script)
        self.assertIn("video.controls = false", script)
        self.assertIn("video.muted = true", script)

    def test_original_camera_files_are_not_committed(self):
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").split()

        self.assertIn("*.MOV", ignored)
        self.assertIn("*.mov", ignored)


if __name__ == "__main__":
    unittest.main()
