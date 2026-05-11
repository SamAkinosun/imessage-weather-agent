"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_config
from .imessage import IMessageError, send_imessage
from .message import format_message
from .outfit import suggest_outfit
from .weather import fetch_weather


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="imessage-weather",
        description="Send a daily weather and outfit iMessage on macOS.",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        required=True,
        help="path to the YAML config file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the message instead of sending it",
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    try:
        cfg = load_config(args.config)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2

    snapshot = fetch_weather(cfg.latitude, cfg.longitude, units=cfg.units)
    outfit = suggest_outfit(snapshot, wardrobe=cfg.wardrobe)
    body = format_message(
        snapshot=snapshot,
        outfit=outfit,
        location_name=cfg.location_name,
        greeting=cfg.greeting,
    )

    if args.dry_run:
        print(body)
        return 0

    try:
        send_imessage(cfg.recipient, body)
    except IMessageError as e:
        print(f"send failed: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
