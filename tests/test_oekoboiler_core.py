import unittest
import importlib.util
from pathlib import Path

from PIL import Image, ImageDraw

MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "oekoboiler"
    / "oekoboiler.py"
)
SPEC = importlib.util.spec_from_file_location("oekoboiler_module", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load oekoboiler module for tests")

MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
Oekoboiler = MODULE.Oekoboiler


class TestOekoboilerCore(unittest.TestCase):
    def test_image_is_none_before_processing(self):
        oekoboiler = Oekoboiler()

        self.assertIsNone(oekoboiler.image)

    def test_parsed_frame_exposes_current_public_state(self):
        oekoboiler = Oekoboiler()

        oekoboiler._parsed_frame.time = "12:34"
        oekoboiler._parsed_frame.set_temperature = 52
        oekoboiler._parsed_frame.quality["set_temperature"].status = "ok"
        oekoboiler._parsed_frame.alignment.shift_x = 3

        self.assertEqual(oekoboiler.time, "12:34")
        self.assertEqual(oekoboiler.setTemperature, 52)
        self.assertEqual(oekoboiler.get_quality("set_temperature")["status"], "ok")
        self.assertEqual(oekoboiler.get_alignment()["shift_x"], 3)

    def test_image_byte_array_does_not_fail_without_debug_tiles(self):
        oekoboiler = Oekoboiler()
        source = Image.new("RGB", (900, 500), "black")

        oekoboiler.updatedProcessedImage(source)

        image_bytes = oekoboiler.imageByteArray

        self.assertIsInstance(image_bytes, bytes)
        self.assertGreater(len(image_bytes), 0)

    def test_level_is_clamped_to_valid_percentage_range(self):
        oekoboiler = Oekoboiler()
        level_img = Image.new("RGB", (25, 208), "white")

        level, confidence = oekoboiler._getLevel(level_img)

        self.assertGreaterEqual(level, 0)
        self.assertLessEqual(level, 100)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_level_uses_contiguous_bottom_bars(self):
        oekoboiler = Oekoboiler()
        h = 180
        w = 24
        img = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(img)

        slot = h / 9.0
        # Light bottom 3 bars.
        for idx in range(3):
            y_top = int(h - ((idx + 1) * slot)) + 2
            y_bottom = int(h - (idx * slot)) - 2
            draw.rectangle((2, y_top, w - 3, y_bottom), fill=255)
        # Add isolated noise in a higher bar that should be ignored.
        y_top = int(h - (6 * slot)) + 3
        y_bottom = int(h - (5 * slot)) - 3
        draw.rectangle((2, y_top, w - 3, y_bottom), fill=255)

        level, _ = oekoboiler._getLevel(img.convert("RGB"))

        self.assertAlmostEqual(level, (3 / 9) * 100, delta=12)

    def test_level_heating_suppresses_decrease(self):
        oekoboiler = Oekoboiler()
        oekoboiler._last_level_bars = 5
        oekoboiler._parsed_frame.state = "Heating"

        adjusted = oekoboiler._apply_level_state_rules(3)

        self.assertEqual(adjusted, 5)

    def test_level_warm_suppresses_large_jump(self):
        oekoboiler = Oekoboiler()
        oekoboiler._last_level_bars = 4
        oekoboiler._parsed_frame.state = "Warm"

        adjusted = oekoboiler._apply_level_state_rules(8)

        self.assertEqual(adjusted, 4)

    def test_decode_segments_exact_match_has_full_confidence(self):
        oekoboiler = Oekoboiler()

        digit, confidence = oekoboiler._decode_segments((1, 1, 1, 1, 1, 1, 1))

        self.assertEqual(digit, 8)
        self.assertEqual(confidence, 1.0)

    def test_decode_segments_close_unique_match_is_accepted(self):
        oekoboiler = Oekoboiler()

        digit, confidence = oekoboiler._decode_segments((0, 1, 1, 0, 1, 1, 1))

        self.assertEqual(digit, 0)
        self.assertGreater(confidence, 0.8)

    def test_decode_segments_ambiguous_match_returns_unknown(self):
        oekoboiler = Oekoboiler()

        # Equidistant to multiple templates -> keep unknown instead of forcing a digit.
        digit, confidence = oekoboiler._decode_segments((1, 1, 1, 0, 0, 0, 1))

        self.assertIsNone(digit)
        self.assertGreaterEqual(confidence, 0.0)

    def test_find_digit_rois_from_components_detects_expected_count(self):
        oekoboiler = Oekoboiler()
        img = Image.new("L", (80, 24), 0)
        draw = ImageDraw.Draw(img)

        draw.rectangle((4, 3, 16, 20), fill=255)
        draw.rectangle((24, 3, 36, 20), fill=255)

        rois = oekoboiler._find_digit_rois_from_components(img, numDigits=2)

        self.assertIsNotNone(rois)
        assert rois is not None
        self.assertEqual(len(rois), 2)

    def test_find_digit_rois_ignores_separator_columns_for_time(self):
        oekoboiler = Oekoboiler()
        img = Image.new("L", (120, 32), 0)
        draw = ImageDraw.Draw(img)

        # Four synthetic digits around center separator.
        draw.rectangle((4, 4, 20, 27), fill=255)
        draw.rectangle((28, 4, 44, 27), fill=255)
        draw.rectangle((76, 4, 92, 27), fill=255)
        draw.rectangle((100, 4, 116, 27), fill=255)

        # Colon-like separator dots in the middle.
        draw.rectangle((58, 10, 61, 13), fill=255)
        draw.rectangle((58, 18, 61, 21), fill=255)

        rois = oekoboiler._find_digit_rois_from_components(
            img,
            numDigits=4,
            withSeperator=True,
        )

        self.assertIsNotNone(rois)
        assert rois is not None
        self.assertEqual(len(rois), 4)

    def test_find_digit_rois_returns_none_when_components_unreliable(self):
        oekoboiler = Oekoboiler()
        img = Image.new("L", (60, 24), 0)
        draw = ImageDraw.Draw(img)

        # Single wide block does not reliably represent 2 distinct digits.
        draw.rectangle((5, 3, 55, 21), fill=255)

        rois = oekoboiler._find_digit_rois_from_components(img, numDigits=2)

        self.assertIsNone(rois)

    def test_estimate_frame_shift_detects_translated_frame(self):
        oekoboiler = Oekoboiler()

        base = Image.new("RGB", (320, 180), "black")
        draw = ImageDraw.Draw(base)
        # Border-anchored blocks so alignment uses stable regions.
        draw.rectangle((8, 8, 35, 35), fill="white")
        draw.rectangle((280, 140, 312, 172), fill="white")

        shifted = Image.new("RGB", (320, 180), "black")
        shifted.paste(base, (6, -4))

        first_shift, _ = oekoboiler._estimate_frame_shift(base)
        second_shift, _ = oekoboiler._estimate_frame_shift(shifted)

        self.assertEqual(first_shift, (0, 0))
        self.assertAlmostEqual(second_shift[0], 6, delta=3)
        self.assertAlmostEqual(second_shift[1], -4, delta=3)

    def test_stabilize_alignment_shift_applies_deadband(self):
        oekoboiler = Oekoboiler()

        stabilized = oekoboiler._stabilize_alignment_shift((1, -1), error=1.0)

        self.assertEqual(stabilized, (0, 0))

    def test_stabilize_alignment_shift_rejects_high_error(self):
        oekoboiler = Oekoboiler()

        stabilized = oekoboiler._stabilize_alignment_shift((5, -4), error=999.0)

        self.assertEqual(stabilized, (0, 0))

    def test_stabilize_alignment_shift_limits_large_jump(self):
        oekoboiler = Oekoboiler()
        oekoboiler._alignment_shift = (3, -2)

        stabilized = oekoboiler._stabilize_alignment_shift((40, -30), error=1.0)

        self.assertEqual(stabilized, (3, -2))

    def test_shift_boundry_for_image_clamps_to_image(self):
        oekoboiler = Oekoboiler()

        shifted = oekoboiler._shift_boundary_for_image((90, 80, 120, 110), (100, 100), (20, 20))

        self.assertEqual(shifted, (70, 70, 100, 100))


if __name__ == "__main__":
    unittest.main()
