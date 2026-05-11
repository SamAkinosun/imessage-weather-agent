"""Outfit suggestions derived from weather conditions.

The default wardrobe is intentionally generic. Override it via the
`wardrobe` block in your YAML config to match your closet.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .weather import RAIN_CODES, SNOW_CODES, WeatherSnapshot

DEFAULT_WARDROBE: Dict[str, List[str]] = {
    "freezing": ["heavy coat", "thermal base layer", "gloves", "warm hat", "boots"],
    "cold": ["warm coat", "long sleeves", "scarf"],
    "cool": ["light jacket or cardigan", "long sleeves"],
    "mild": ["long sleeves", "light layer"],
    "warm": ["short sleeves", "comfortable pants"],
    "hot": ["short sleeves", "shorts or breathable pants", "sunglasses"],
    "rainy": ["rain jacket or umbrella", "waterproof shoes"],
    "snowy": ["waterproof boots", "warm socks", "insulated outer layer"],
    "windy": ["windbreaker"],
}

# Wind threshold above which we recommend a wind layer.
# Open-Meteo returns km/h for metric, mph for imperial. The threshold below
# is meant to feel right under both units; a steady 20 mph or 20 km/h is
# noticeable on most outfits.
WIND_THRESHOLD = 20.0


def temperature_band(temp: float, unit_temp: str) -> str:
    """Map a temperature to a band name. Accepts unit strings containing 'C' or 'F'."""
    upper = unit_temp.upper()
    is_fahrenheit = "F" in upper and "C" not in upper
    celsius = (temp - 32) * 5 / 9 if is_fahrenheit else temp

    if celsius < -5:
        return "freezing"
    if celsius < 5:
        return "cold"
    if celsius < 12:
        return "cool"
    if celsius < 18:
        return "mild"
    if celsius < 25:
        return "warm"
    return "hot"


def suggest_outfit(
    snapshot: WeatherSnapshot,
    wardrobe: Optional[Dict[str, List[str]]] = None,
) -> List[str]:
    """Return an ordered list of outfit items for the given weather.

    Items are deduplicated while preserving order.
    """
    closet = wardrobe if wardrobe is not None else DEFAULT_WARDROBE

    items: List[str] = []
    seen = set()

    def add_from(key: str) -> None:
        for item in closet.get(key, []):
            if item not in seen:
                items.append(item)
                seen.add(item)

    band = temperature_band(snapshot.feels_like, snapshot.unit_temp)
    add_from(band)

    if snapshot.weather_code in SNOW_CODES:
        add_from("snowy")
    elif (
        snapshot.weather_code in RAIN_CODES
        or snapshot.precipitation_probability >= 50
    ):
        add_from("rainy")

    if snapshot.wind_speed >= WIND_THRESHOLD:
        add_from("windy")

    return items
