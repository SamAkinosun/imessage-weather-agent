import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from imessage_weather.config import load_config


def write_config(dirpath, body):
    p = Path(dirpath) / "config.yaml"
    p.write_text(textwrap.dedent(body))
    return p


class LoadConfigTests(unittest.TestCase):
    def test_minimal_valid_config(self):
        with TemporaryDirectory() as d:
            p = write_config(
                d,
                """
                recipient: "+15555550100"
                location:
                  latitude: 45.0
                  longitude: -93.0
                """,
            )
            cfg = load_config(p)
            self.assertEqual(cfg.recipient, "+15555550100")
            self.assertEqual(cfg.latitude, 45.0)
            self.assertEqual(cfg.longitude, -93.0)
            self.assertEqual(cfg.units, "metric")
            self.assertEqual(cfg.greeting, "Good morning")
            self.assertIsNone(cfg.wardrobe)

    def test_full_config(self):
        with TemporaryDirectory() as d:
            p = write_config(
                d,
                """
                recipient: "+15555550100"
                units: imperial
                greeting: Hey
                location:
                  name: Brooklyn
                  latitude: 40.65
                  longitude: -73.95
                wardrobe:
                  warm:
                    - "linen shirt"
                    - "shorts"
                """,
            )
            cfg = load_config(p)
            self.assertEqual(cfg.units, "imperial")
            self.assertEqual(cfg.greeting, "Hey")
            self.assertEqual(cfg.location_name, "Brooklyn")
            self.assertEqual(cfg.wardrobe, {"warm": ["linen shirt", "shorts"]})

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_config("/tmp/nonexistent/_imessage_weather_no_such.yaml")

    def test_missing_recipient_raises(self):
        with TemporaryDirectory() as d:
            p = write_config(
                d,
                """
                location:
                  latitude: 1.0
                  longitude: 2.0
                """,
            )
            with self.assertRaises(ValueError):
                load_config(p)

    def test_invalid_units_raises(self):
        with TemporaryDirectory() as d:
            p = write_config(
                d,
                """
                recipient: "+15555550100"
                units: kelvin
                location:
                  latitude: 1.0
                  longitude: 2.0
                """,
            )
            with self.assertRaises(ValueError):
                load_config(p)

    def test_invalid_wardrobe_shape_raises(self):
        with TemporaryDirectory() as d:
            p = write_config(
                d,
                """
                recipient: "+15555550100"
                location:
                  latitude: 1.0
                  longitude: 2.0
                wardrobe:
                  warm: "shorts"
                """,
            )
            with self.assertRaises(ValueError):
                load_config(p)

    def test_root_must_be_mapping(self):
        with TemporaryDirectory() as d:
            p = Path(d) / "x.yaml"
            p.write_text("- a\n- b\n")
            with self.assertRaises(ValueError):
                load_config(p)


if __name__ == "__main__":
    unittest.main()
