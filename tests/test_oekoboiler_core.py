import unittest
import importlib.util
from pathlib import Path

from PIL import Image

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

        level = oekoboiler._getLevel(level_img)

        self.assertGreaterEqual(level, 0)
        self.assertLessEqual(level, 100)


if __name__ == "__main__":
    unittest.main()
