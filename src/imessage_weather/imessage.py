"""Send an iMessage on macOS via osascript.

Requires macOS with Messages.app signed into iMessage. The recipient
can be a phone number (E.164 preferred) or an email address tied to an
Apple ID.
"""

from __future__ import annotations

import platform
import subprocess
from typing import Callable, Optional


class IMessageError(RuntimeError):
    """Raised when a message could not be sent."""


def send_imessage(
    recipient: str,
    body: str,
    runner: Optional[Callable] = None,
    require_macos: bool = True,
    timeout: float = 30.0,
) -> None:
    """Send `body` to `recipient` via iMessage.

    `runner` defaults to :func:`subprocess.run` and is overridable for tests.
    Set `require_macos=False` only when injecting a runner in tests.
    """
    if require_macos and platform.system() != "Darwin":
        raise IMessageError(
            f"iMessage sending requires macOS. Detected platform: {platform.system()}"
        )

    if not recipient or not recipient.strip():
        raise IMessageError("recipient is required")
    if not body or not body.strip():
        raise IMessageError("body is required")

    safe_body = body.replace("\\", "\\\\").replace('"', '\\"')
    safe_recipient = recipient.replace("\\", "\\\\").replace('"', '\\"')

    script = (
        'tell application "Messages"\n'
        '    set targetService to 1st service whose service type = iMessage\n'
        f'    set targetBuddy to buddy "{safe_recipient}" of targetService\n'
        f'    send "{safe_body}" to targetBuddy\n'
        "end tell"
    )

    run = runner or subprocess.run
    result = run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        raise IMessageError(
            f"osascript failed (exit {result.returncode}): {result.stderr.strip()}"
        )
