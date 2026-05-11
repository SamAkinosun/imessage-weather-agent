import unittest

from imessage_weather.outfit import (
    DEFAULT_WARDROBE,
    suggest_outfit,
    temperature_band,
)
from imessage_weather.weather import WeatherSnapshot


def snap(
    temp=15.0,
    feels=15.0,
    precip=0.0,
    precip_prob=0,
    wind=5.0,
    code=0,
    unit_temp="C",
):
    return WeatherSnapshot(
        temperature=temp,
        feels_like=feels,
        precipitation=precip,
        precipitation_probability=precip_prob,
        wind_speed=wind,
        weather_code=code,
        is_day=True,
        unit_temp=unit_temp,
        unit_precip="mm",
        unit_wind="km/h",
    )


class TemperatureBandTests(unittest.TestCase):
    def test_celsius_bands(self):
        self.assertEqual(temperature_band(-10, "C"), "freezing")
        self.assertEqual(temperature_band(0, "C"), "cold")
        self.assertEqual(temperature_band(8, "C"), "cool")
        self.assertEqual(temperature_band(15, "C"), "mild")
        self.assertEqual(temperature_band(22, "C"), "warm")
        self.assertEqual(temperature_band(30, "C"), "hot")

    def test_fahrenheit_bands_match_celsius_equivalents(self):
        # 32F = 0C should land in 'cold'
        self.assertEqual(temperature_band(32, "F"), "cold")
        # 75F ~= 24C should land in 'warm'
        self.assertEqual(temperature_band(75, "F"), "warm")
        # 90F ~= 32C should land in 'hot'
        self.assertEqual(temperature_band(90, "F"), "hot")

    def test_unit_string_with_degree_symbol(self):
        # Open-Meteo can return units like '°C'; we accept any string with C or F.
        self.assertEqual(temperature_band(20, "°C"), "warm")
        self.assertEqual(temperature_band(70, "°F"), "warm")


class SuggestOutfitTests(unittest.TestCase):
    def test_warm_clear_day(self):
        items = suggest_outfit(snap(temp=22, feels=22, code=0))
        self.assertIn("short sleeves", items)
        self.assertNotIn("rain jacket or umbrella", items)
        self.assertNotIn("windbreaker", items)

    def test_rain_adds_rain_layer(self):
        items = suggest_outfit(snap(temp=14, feels=12, code=63))
        self.assertIn("rain jacket or umbrella", items)

    def test_snow_adds_snow_layer_not_rain(self):
        items = suggest_outfit(snap(temp=-2, feels=-5, code=73))
        self.assertIn("waterproof boots", items)
        self.assertNotIn("rain jacket or umbrella", items)

    def test_high_wind_adds_windbreaker(self):
        items = suggest_outfit(snap(temp=15, feels=12, wind=25.0))
        self.assertIn("windbreaker", items)

    def test_high_precip_probability_adds_rain_layer_even_with_clear_code(self):
        items = suggest_outfit(snap(temp=18, feels=18, code=2, precip_prob=70))
        self.assertIn("rain jacket or umbrella", items)

    def test_low_precip_probability_does_not_add_rain_layer(self):
        items = suggest_outfit(snap(temp=18, feels=18, code=1, precip_prob=20))
        self.assertNotIn("rain jacket or umbrella", items)

    def test_results_are_deduped(self):
        wardrobe = {
            "warm": ["shirt", "pants"],
            "rainy": ["pants", "umbrella"],
        }
        items = suggest_outfit(snap(temp=22, feels=22, code=63), wardrobe=wardrobe)
        self.assertEqual(items.count("pants"), 1)
        self.assertEqual(items, ["shirt", "pants", "umbrella"])

    def test_uses_feels_like_for_band(self):
        # Real temp warm but feels like cold (e.g., wind chill)
        items = suggest_outfit(snap(temp=20, feels=2, code=0, unit_temp="C"))
        self.assertIn("warm coat", items)

    def test_default_wardrobe_used_when_none_passed(self):
        items = suggest_outfit(snap(temp=22, feels=22))
        # Pull from DEFAULT_WARDROBE['warm']
        self.assertEqual(items, DEFAULT_WARDROBE["warm"])


if __name__ == "__main__":
    unittest.main()
