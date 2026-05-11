"""Format the message body sent to the recipient."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from .weather import WeatherSnapshot, describe_weather


def format_message(
    snapshot: WeatherSnapshot,
    outfit: List[str],
    location_name: str = "",
    greeting: str = "Good morning",
    now: Optional[datetime] = None,
) -> str:
    """Compose the multi-line message body."""
    when = now if now is not None else datetime.now()

    where = f" in {location_name}" if location_name else ""
    conditions = describe_weather(snapshot.weather_code)
    temp = round(snapshot.temperature)
    feels = round(snapshot.feels_like)

    feels_part = ""
    if abs(snapshot.feels_like - snapshot.temperature) >= 3:
        feels_part = f" (feels like {feels}{snapshot.unit_temp})"

    # Use platform-portable day/month formatting.
    date_str = when.strftime("%A, %B %d").replace(" 0", " ")

    lines = [
        f"{greeting}.",
        f"{date_str}: {conditions}{where}.",
        f"{temp}{snapshot.unit_temp}{feels_part}.",
    ]

    if snapshot.precipitation_probability >= 30:
        lines.append(f"Precipitation chance: {snapshot.precipitation_probability}%.")

    if outfit:
        lines.append("")
        lines.append("Suggested: " + ", ".join(outfit) + ".")

    return "\n".join(lines)
