# imessage-weather-agent

A small Python CLI that sends a daily weather and outfit-suggestion iMessage from your Mac. Uses [Open-Meteo](https://open-meteo.com) for weather (no API key, no signup) and macOS Messages.app for delivery.

Designed to be run from `launchd` once a day. The whole thing is about 400 lines of Python, has 47 tests, and depends on one third-party package (`pyyaml`).

## Why this exists

I wanted a daily forecast in the same place I already get every other notification. Email is too slow to look at in the morning. Push notifications get swiped away. iMessage shows up in the lock screen, the Mac, the watch, and the iPad without me thinking about it.

There are weather widgets and weather Shortcuts, but I wanted something I could version-control and tweak. So this exists.

## What it sends

Run it with `--dry-run` and you get something like this in your terminal:

```
$ imessage-weather --config config.yaml --dry-run
Good morning.
Sunday, May 10: mainly clear in Brooklyn.
60°F.
Precipitation chance: 30%.

Suggested: long sleeves, light layer.
```

Without `--dry-run` the same body is sent to your `recipient` via iMessage.

## Install

```bash
git clone https://github.com/SamAkinosun/imessage-weather-agent.git
cd imessage-weather-agent
pip install -e .
```

This installs the `imessage-weather` console script.

You need:

- macOS (the script shells out to `osascript` to talk to Messages.app)
- Python 3.10 or newer
- Messages.app signed into iMessage

The first time you run it, macOS will ask whether your terminal can control Messages. Approve it, otherwise the AppleScript will silently fail.

## Configure

Copy `examples/config.example.yaml` to `config.yaml` and edit:

```yaml
recipient: "+15555550100"          # E.164 phone or Apple ID email
location:
  name: Brooklyn                    # optional, appears in the message
  latitude: 40.6501
  longitude: -73.9496
units: imperial                     # 'imperial' or 'metric'
greeting: "Good morning"
```

Look up coordinates at https://www.latlong.net or by Cmd-clicking a place in Apple Maps.

## Schedule it

The included `examples/launchd.plist.example` runs the CLI every day at 7:00 AM local time. To install:

```bash
# Edit the paths inside the plist first
cp examples/launchd.plist.example ~/Library/LaunchAgents/com.example.imessage-weather.plist
launchctl load ~/Library/LaunchAgents/com.example.imessage-weather.plist
```

Trigger it once now to verify, without waiting until tomorrow:

```bash
launchctl start com.example.imessage-weather
```

Logs are written to `/tmp/imessage-weather.{out,err}.log`. Tail those if a delivery silently fails.

If you prefer cron, the equivalent is:

```cron
0 7 * * * /usr/local/bin/imessage-weather --config /path/to/config.yaml >> /tmp/imessage-weather.log 2>&1
```

`launchd` is the recommended path on macOS because cron does not survive sleep cycles reliably on modern macOS.

## Customizing the wardrobe

The default outfit suggestions are intentionally bland. Override them per band in your config:

```yaml
wardrobe:
  cold:
    - "wool coat"
    - "scarf"
    - "boots"
  warm:
    - "linen shirt"
    - "shorts"
  rainy:
    - "rain shell"
    - "waterproof shoes"
```

Bands you can override: `freezing`, `cold`, `cool`, `mild`, `warm`, `hot`, `rainy`, `snowy`, `windy`. Bands you do not override fall back to the defaults in `src/imessage_weather/outfit.py`.

The temperature thresholds (in Celsius, normalized internally regardless of units) are:

| Band     | Range          |
| -------- | -------------- |
| freezing | below -5C      |
| cold     | -5C to 5C      |
| cool     | 5C to 12C      |
| mild     | 12C to 18C     |
| warm     | 18C to 25C     |
| hot      | 25C and above  |

Suggestions are based on the *feels-like* temperature, not the raw reading, so wind chill is reflected.

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -v tests
```

47 tests, no external dependencies, no network calls in the test suite. The tests pass on Python 3.10, 3.11, 3.12, and 3.13.

## How it works

```
fetch_weather(lat, lon)        Open-Meteo current-weather endpoint
       |
       v
parse_weather()                produces a WeatherSnapshot dataclass
       |
       v
suggest_outfit()               maps band + precipitation + wind to items
       |
       v
format_message()               composes the multi-line body
       |
       v
send_imessage()                osascript -> Messages.app
```

Each module is independently testable. The Open-Meteo fetch accepts an injectable `fetcher` for tests; `send_imessage` accepts an injectable `runner`.

## Limitations and known issues

- **macOS only.** Linux and Windows can use the weather and outfit modules as a library, but the iMessage send path will refuse to run. There is no SMS fallback baked in; if you want one, swap `send_imessage` for a Twilio call in `cli.py`.
- **No multi-day forecast.** Only the current snapshot. The Open-Meteo API supports daily forecast easily; this is a deliberate choice to keep the morning message short.
- **Time zones.** Open-Meteo returns UTC by default. The current code does not pass a timezone parameter, which is fine for "right now" but would matter if you extended this to a multi-day forecast.
- **AppleScript escaping.** The body is escaped for AppleScript string literals (`\` and `"` only). If you put exotic characters in your greeting, you may run into AppleScript quoting edge cases.
- **macOS Privacy prompt.** First run requires you to grant your terminal Automation access for Messages.app. There is no way to script around this; it is a system-level consent.

## FAQ

**Why Open-Meteo and not OpenWeather, Tomorrow.io, etc.?**

Open-Meteo is free with no signup, no API key, and no rate-limiting headaches for personal use. The data quality is good enough for "what should I wear today". If you want hyper-local nowcasts, swap the implementation in `weather.py`; the rest of the code does not care which provider you use.

**Why not Shortcuts?**

Shortcuts is great until you want to put it under git, run tests, or have it work the same way on a fresh machine. This is what I reach for when I want repeatability.

**Why iMessage and not push notifications?**

I send to my own phone. iMessage threads it cleanly with the rest of my morning, and I can search the history. A push notification would disappear after I dismissed it.

**The launchd job did not fire. What now?**

In order, check:
1. `launchctl list | grep imessage-weather` shows the job
2. `/tmp/imessage-weather.err.log` for stderr
3. The plist `ProgramArguments` paths are absolute and correct
4. Messages.app is allowed to be controlled by your shell (System Settings > Privacy and Security > Automation)

**Can it send to multiple people?**

Not yet. Loop over recipients in `cli.py` if you want to fan out. PRs welcome.

**Why is the wardrobe so plain by default?**

Because clothes are personal. The defaults are meant to look reasonable for anyone and to make it obvious how to override them.

## Tested with

- macOS 14 (Sonoma), macOS 15 (Sequoia)
- Python 3.10, 3.11, 3.12, 3.13
- Open-Meteo current-weather endpoint as of May 2026

## Contributing

Issues and PRs welcome. Small things to keep in mind:

- Tests live in `tests/`. New behavior needs new test coverage.
- Run `PYTHONPATH=src python3 -m unittest discover tests` before opening a PR.
- Keep the dependency footprint to one or zero. If you find yourself adding `requests`, the standard library probably already covers your case.

## License

MIT, see [LICENSE](LICENSE).
