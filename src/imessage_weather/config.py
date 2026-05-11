"""Load configuration from a YAML file."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

try:
    import yaml
except ImportError:  # pragma: no cover - import-time guard
    yaml = None  # type: ignore[assignment]


@dataclass
class Config:
    recipient: str
    latitude: float
    longitude: float
    location_name: str = ""
    units: str = "metric"
    greeting: str = "Good morning"
    wardrobe: Optional[Dict[str, List[str]]] = None


def load_config(path: Union[str, Path]) -> Config:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"config file not found: {file_path}")

    if yaml is None:
        raise RuntimeError(
            "pyyaml is required to load YAML configs. install with: pip install pyyaml"
        )

    with file_path.open() as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(
            f"config root must be a mapping, got {type(data).__name__}"
        )

    location = data.get("location") or {}
    if not isinstance(location, dict):
        raise ValueError("'location' must be a mapping with latitude and longitude")

    return Config(
        recipient=_required(data, "recipient"),
        latitude=float(_required_in(location, "latitude", "location.latitude")),
        longitude=float(_required_in(location, "longitude", "location.longitude")),
        location_name=str(location.get("name", "")),
        units=_validate_units(data.get("units", "metric")),
        greeting=str(data.get("greeting", "Good morning")),
        wardrobe=_validate_wardrobe(data.get("wardrobe")),
    )


def _required(data: dict, key: str):
    if key not in data or data[key] in (None, ""):
        raise ValueError(f"config missing required key: {key}")
    return data[key]


def _required_in(data: dict, key: str, dotted: str):
    if key not in data or data[key] is None:
        raise ValueError(f"config missing required key: {dotted}")
    return data[key]


def _validate_units(units) -> str:
    if units not in ("metric", "imperial"):
        raise ValueError(f"units must be 'metric' or 'imperial', got {units!r}")
    return units


def _validate_wardrobe(wardrobe):
    if wardrobe is None:
        return None
    if not isinstance(wardrobe, dict):
        raise ValueError("wardrobe must be a mapping of band -> list of items")
    cleaned: Dict[str, List[str]] = {}
    for band, items in wardrobe.items():
        if not isinstance(items, list) or not all(isinstance(i, str) for i in items):
            raise ValueError(f"wardrobe['{band}'] must be a list of strings")
        cleaned[str(band)] = list(items)
    return cleaned
