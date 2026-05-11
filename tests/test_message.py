import unittest
from datetime import datetime

from imessage_weather.message import format_message
from imessage_weather.weather import WeatherSnapshot


def snap(**overrides):
    base = dict(
        temperature=14.2,
        feels_like=12.0,
        precipitation=0.0,
        precipitation_probability=10,
        wind_speed=8.0,
        weather_code=2,
        is_day=True,
        unit_temp="C",
        unit_precip="mm",
        unit_wind="km/h",
    )
    base.update(overrides)
    return WeatherSnapshot(**base)


FIXED_NOW = datetime(2026, 5, 10, 7, 30)


class FormatMessageTests(unittest.TestCase):
    def test_basic_message_structure(self):
        body = format_message(
            snapshot=snap(),
            outfit=["light jacket", "long sleeves"],
            location_name="Saint Paul",
            greeting="Good morning",
            now=FIXED_NOW,
        )
        self.assertIn("Good morning.", body)
        self.assertIn("partly cloudy in Saint Paul.", body)
        self.assertIn("14C", body)
        self.assertIn("Suggested: light jacket, long sleeves.", body)

    def test_feels_like_shown_when_difference_significant(self):
        body = format_message(
            snapshot=snap(temperature=20.0, feels_like=10.0),
            outfit=[],
            now=FIXED_NOW,
        )
        self.assertIn("(feels like 10C)", body)

    def test_feels_like_omitted_when_close(self):
        body = format_message(
            snapshot=snap(temperature=15.0, feels_like=14.0),
            outfit=[],
            now=FIXED_NOW,
        )
        self.assertNotIn("feels like", body)

    def test_precipitation_chance_only_above_30(self):
        low = format_message(snapshot=snap(precipitation_probability=20), outfit=[], now=FIXED_NOW)
        self.assertNotIn("Precipitation chance", low)

        high = format_message(snapshot=snap(precipitation_probability=60), outfit=[], now=FIXED_NOW)
        self.assertIn("Precipitation chance: 60%.", high)

    def test_no_outfit_section_when_empty(self):
        body = format_message(snapshot=snap(), outfit=[], now=FIXED_NOW)
        self.assertNotIn("Suggested:", body)

    def test_no_location_label_when_blank(self):
        body = format_message(snapshot=snap(), outfit=[], location_name="", now=FIXED_NOW)
        self.assertNotIn(" in ", body)

    def test_custom_greeting_used_verbatim(self):
        body = format_message(
            snapshot=snap(), outfit=[], greeting="Morning sunshine", now=FIXED_NOW
        )
        self.assertTrue(body.startswith("Morning sunshine."))


if __name__ == "__main__":
    unittest.main()
