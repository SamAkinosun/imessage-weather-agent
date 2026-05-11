import unittest
from types import SimpleNamespace
from unittest import mock

from imessage_weather.imessage import IMessageError, send_imessage


def fake_runner(returncode=0, stderr=""):
    def runner(cmd, capture_output=True, text=True, timeout=30.0):
        runner.last_cmd = cmd
        runner.last_kwargs = {
            "capture_output": capture_output,
            "text": text,
            "timeout": timeout,
        }
        return SimpleNamespace(returncode=returncode, stdout="", stderr=stderr)

    runner.last_cmd = None  # type: ignore[attr-defined]
    runner.last_kwargs = None  # type: ignore[attr-defined]
    return runner


class SendIMessageTests(unittest.TestCase):
    def test_sends_via_osascript_with_recipient_and_body(self):
        runner = fake_runner()
        send_imessage(
            "+15555550100",
            "hello",
            runner=runner,
            require_macos=False,
        )
        self.assertEqual(runner.last_cmd[0], "osascript")
        self.assertEqual(runner.last_cmd[1], "-e")
        script = runner.last_cmd[2]
        self.assertIn('"+15555550100"', script)
        self.assertIn('"hello"', script)
        self.assertIn("tell application \"Messages\"", script)

    def test_escapes_double_quotes_in_body(self):
        runner = fake_runner()
        send_imessage(
            "+15555550100",
            'she said "hi"',
            runner=runner,
            require_macos=False,
        )
        script = runner.last_cmd[2]
        self.assertIn('she said \\"hi\\"', script)
        # Make sure no raw unescaped quote slipped through
        self.assertNotIn('she said "hi"', script)

    def test_escapes_backslashes_before_quotes(self):
        runner = fake_runner()
        send_imessage(
            "+15555550100",
            r"path: C:\Users",
            runner=runner,
            require_macos=False,
        )
        script = runner.last_cmd[2]
        self.assertIn(r"C:\\Users", script)

    def test_empty_recipient_raises(self):
        with self.assertRaises(IMessageError):
            send_imessage("", "hi", runner=fake_runner(), require_macos=False)

    def test_whitespace_only_body_raises(self):
        with self.assertRaises(IMessageError):
            send_imessage("+15555550100", "   ", runner=fake_runner(), require_macos=False)

    def test_nonzero_exit_raises(self):
        runner = fake_runner(returncode=1, stderr="execution error")
        with self.assertRaises(IMessageError) as ctx:
            send_imessage(
                "+15555550100",
                "hello",
                runner=runner,
                require_macos=False,
            )
        self.assertIn("execution error", str(ctx.exception))

    def test_non_macos_platform_raises_when_required(self):
        with mock.patch("imessage_weather.imessage.platform.system", return_value="Linux"):
            with self.assertRaises(IMessageError) as ctx:
                send_imessage(
                    "+15555550100",
                    "hi",
                    runner=fake_runner(),
                    require_macos=True,
                )
            self.assertIn("requires macOS", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
