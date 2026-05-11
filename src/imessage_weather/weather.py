"""Open-Meteo weather client.

Open-Meteo is free and does not require an API key.
Docs: https://open-meteo.com/en/docs
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class WeatherSnapshot:
    """A point-in-time weather reading."""

    temperature: float
    feels_like: float
    precipitation: float
    precipitation_probability: int
    wind_speed: float
    weather_code: int
    is_day: bool
    unit_temp: str
    unit_precip: str
    unit_wind: str


# WMO weather interpretation codes. Reference: https://open-meteo.com/en/docs
WEATHER_DESCRIPTIONS = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "dense freezing drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "light snow",
    73: "moderate snow",
    75: "heavy snow",
    77: "snow grains",
    80: "light rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "light snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with light hail",
    99: "thunderstorm with heavy hail",
}

RAIN_CODES = frozenset({51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99})
SNOW_CODES = frozenset({71, 73, 75, 77, 85, 86})


def describe_weather(code: int) -> str:
    return WEATHER_DESCRIPTIONS.get(code, "unknown conditions")


def fetch_weather(
    latitude: float,
    longitude: float,
    units: str = "metric",
    timeout: float = 10.0,
    fetcher: Optional[Callable[[str], dict]] = None,
) -> WeatherSnapshot:
    """Fetch the current-weather snapshot from Open-Meteo.

    Pass `fetcher` to inject a stub for tests; it must accept a URL and
    return the decoded JSON payload.
    """
    if units not in ("metric", "imperial"):
        raise ValueError(f"units must be 'metric' or 'imperial', got {units!r}")

    params: dict = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,apparent_temperature,precipitation,"
            "precipitation_probability,wind_speed_10m,weather_code,is_day"
        ),
    }
    if units == "imperial":
        params["temperature_unit"] = "fahrenheit"
        params["precipitation_unit"] = "inch"
        params["wind_speed_unit"] = "mph"

    url = f"{OPEN_METEO_URL}?{urllib.parse.urlencode(params)}"

    if fetcher is None:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    else:
        data = fetcher(url)

    return parse_weather(data)


def parse_weather(payload: dict) -> WeatherSnapshot:
    """Parse the JSON payload returned by Open-Meteo's current endpoint."""
    if not isinstance(payload, dict) or "current" not in payload:
        raise ValueError("payload missing 'current' field")

    current = payload["current"]
    units = payload.get("current_units", {})

    return WeatherSnapshot(
        temperature=float(current["temperature_2m"]),
        feels_like=float(current.get("apparent_temperature", current["temperature_2m"])),
        precipitation=float(current.get("precipitation", 0.0)),
        precipitation_probability=int(current.get("precipitation_probability") or 0),
        wind_speed=float(current.get("wind_speed_10m", 0.0)),
        weather_code=int(current.get("weather_code", 0)),
        is_day=bool(current.get("is_day", 1)),
        unit_temp=units.get("temperature_2m", "C"),
        unit_precip=units.get("precipitation", "mm"),
        unit_wind=units.get("wind_speed_10m", "km/h"),
    )
