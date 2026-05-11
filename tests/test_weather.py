import unittest

from imessage_weather.weather import (
    RAIN_CODES,
    SNOW_CODES,
    WeatherSnapshot,
    describe_weather,
    fetch_weather,
    parse_weather,
)


SAMPLE_PAYLOAD = {
    "current_units": {
        "temperature_2m": "C",
        "precipitation": "mm",
        "wind_speed_10m": "km/h",
    },
    "current": {
        "temperature_2m": 14.2,
        "apparent_temperature": 12.0,
        "precipitation": 0.3,
        "precipitation_probability": 40,
        "wind_speed_10m": 8.5,
        "weather_code": 61,
        "is_day": 1,
    },
}


class ParseWeatherTests(unittest.TestCase):
    def test_parses_full_payload(self):
        snap = parse_weather(SAMPLE_PAYLOAD)
        self.assertEqual(snap.temperature, 14.2)
        self.assertEqual(snap.feels_like, 12.0)
        self.assertEqual(snap.precipitation, 0.3)
        self.assertEqual(snap.precipitation_probability, 40)
        self.assertEqual(snap.wind_speed, 8.5)
        self.assertEqual(snap.weather_code, 61)
        self.assertTrue(snap.is_day)
        self.assertEqual(snap.unit_temp, "C")

    def test_missing_current_raises(self):
        with self.assertRaises(ValueError):
            parse_weather({"foo": "bar"})

    def test_non_dict_payload_raises(self):
        with self.assertRaises(ValueError):
            parse_weather("not a dict")  # type: ignore[arg-type]

    def test_apparent_temperature_falls_back_to_temperature(self):
        payload = {
            "current_units": {"temperature_2m": "C"},
            "current": {"temperature_2m": 20.0, "weather_code": 0},
        }
        snap = parse_weather(payload)
        self.assertEqual(snap.feels_like, 20.0)

    def test_null_precipitation_probability_becomes_zero(self):
        payload = {
            "current": {
                "temperature_2m": 10.0,
                "precipitation_probability": None,
                "weather_code": 0,
            }
        }
        snap = parse_weather(payload)
        self.assertEqual(snap.precipitation_probability, 0)


class FetchWeatherTests(unittest.TestCase):
    def test_metric_url_does_not_set_unit_overrides(self):
        captured = {}

        def stub(url):
            captured["url"] = url
            return SAMPLE_PAYLOAD

        fetch_weather(45.0, -93.0, units="metric", fetcher=stub)
        self.assertIn("latitude=45.0", captured["url"])
        self.assertIn("longitude=-93.0", captured["url"])
        self.assertNotIn("temperature_unit=fahrenheit", captured["url"])

    def test_imperial_url_sets_unit_overrides(self):
        captured = {}

        def stub(url):
            captured["url"] = url
            return SAMPLE_PAYLOAD

        fetch_weather(45.0, -93.0, units="imperial", fetcher=stub)
        self.assertIn("temperature_unit=fahrenheit", captured["url"])
        self.assertIn("precipitation_unit=inch", captured["url"])
        self.assertIn("wind_speed_unit=mph", captured["url"])

    def test_invalid_units_raises(self):
        with self.assertRaises(ValueError):
            fetch_weather(0.0, 0.0, units="kelvin", fetcher=lambda url: SAMPLE_PAYLOAD)


class DescribeTests(unittest.TestCase):
    def test_known_code(self):
        self.assertEqual(describe_weather(0), "clear sky")
        self.assertEqual(describe_weather(63), "moderate rain")

    def test_unknown_code(self):
        self.assertEqual(describe_weather(9999), "unknown conditions")


class CodeSetTests(unittest.TestCase):
    def test_rain_and_snow_codes_disjoint(self):
        self.assertEqual(RAIN_CODES & SNOW_CODES, set())


if __name__ == "__main__":
    unittest.main()
