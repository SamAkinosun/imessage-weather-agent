import io
import textwrap
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

from imessage_weather import cli


SAMPLE_PAYLOAD = {
    "current_units": {"temperature_2m": "C", "precipitation": "mm", "wind_speed_10m": "km/h"},
    "current": {
        "temperature_2m": 14.0,
        "apparent_temperature": 12.0,
        "precipitation": 0.0,
        "precipitation_probability": 10,
        "wind_speed_10m": 5.0,
        "weather_code": 2,
        "is_day": 1,
    },
}


def write_min_config(dirpath):
    p = Path(dirpath) / "config.yaml"
    p.write_text(
        textwrap.dedent(
            """
            recipient: "+15555550100"
            location:
              name: Brooklyn
              latitude: 40.65
              longitude: -73.95
            """
        )
    )
    return p


class CliDryRunTests(unittest.TestCase):
    def test_dry_run_prints_message_and_does_not_send(self):
        with TemporaryDirectory() as d:
            cfg_path = write_min_config(d)
            with mock.patch(
                "imessage_weather.cli.fetch_weather",
                return_value=cli.fetch_weather.__wrapped__ if False else None,
            ):
                pass

            with mock.patch("imessage_weather.cli.fetch_weather") as fw, mock.patch(
                "imessage_weather.cli.send_imessage"
            ) as send:
                # Make fetch_weather return a real WeatherSnapshot
                from imessage_weather.weather import parse_weather

                fw.return_value = parse_weather(SAMPLE_PAYLOAD)
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = cli.main(["--config", str(cfg_path), "--dry-run"])
                self.assertEqual(rc, 0)
                self.assertIn("partly cloudy in Brooklyn.", buf.getvalue())
                send.assert_not_called()

    def test_missing_config_file_returns_2(self):
        buf = io.StringIO()
        with redirect_stderr(buf):
            rc = cli.main(["--config", "/tmp/no_such_config_xyz.yaml"])
        self.assertEqual(rc, 2)
        self.assertIn("config error", buf.getvalue())

    def test_send_failure_returns_1(self):
        with TemporaryDirectory() as d:
            cfg_path = write_min_config(d)
            from imessage_weather.imessage import IMessageError
            from imessage_weather.weather import parse_weather

            with mock.patch("imessage_weather.cli.fetch_weather") as fw, mock.patch(
                "imessage_weather.cli.send_imessage"
            ) as send:
                fw.return_value = parse_weather(SAMPLE_PAYLOAD)
                send.side_effect = IMessageError("nope")
                buf = io.StringIO()
                with redirect_stderr(buf):
                    rc = cli.main(["--config", str(cfg_path)])
                self.assertEqual(rc, 1)
                self.assertIn("send failed", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
