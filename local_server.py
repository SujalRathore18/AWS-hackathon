"""Local demo server for HeatShield AI.

This uses the same risk engine as the Lambda and fetches live Open-Meteo data.
It has no AWS dependency, so it can be demonstrated when deployment is blocked.
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
import risk

ROOT = Path(__file__).parent
WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=22.7196&longitude=75.8577"
    "&current=temperature_2m,relative_humidity_2m,apparent_temperature"
    "&hourly=temperature_2m,relative_humidity_2m,apparent_temperature"
    "&forecast_days=2&timezone=Asia%2FKolkata"
)


def get_weather():
    with urllib.request.urlopen(WEATHER_URL, timeout=10) as response:
        data = json.load(response)
    current = data["current"]
    hourly = data["hourly"]
    start = next(
        (i for i, value in enumerate(hourly["time"]) if value >= current["time"][:13] + ":00"),
        0,
    )
    forecast = [
        {
            "time": hourly["time"][i],
            "temp_c": hourly["temperature_2m"][i],
            "humidity": hourly["relative_humidity_2m"][i],
        }
        for i in range(start, min(start + 12, len(hourly["time"])))
    ]
    return {
        "temp_c": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "apparent_c": current["apparent_temperature"],
        "observed_at": current["time"],
        "forecast": forecast,
    }


def make_response(query):
    activity = query.get("activity", ["commute"])[0]
    if activity not in risk.ACTIVITY_OFFSET:
        activity = "commute"
    try:
        minutes = max(5, min(int(query.get("minutes", ["60"])[0]), 600))
    except (TypeError, ValueError):
        minutes = 60
    vulnerable = query.get("vulnerable", ["0"])[0] == "1"
    alert = os.environ.get("IMD_ALERT", "none").lower()
    weather = get_weather()
    result = risk.assess(
        weather["temp_c"],
        weather["humidity"],
        activity,
        minutes,
        datetime.now().hour,
        alert,
        vulnerable,
    )
    hours, best_hours = risk.best_windows(
        weather["forecast"], activity, minutes, alert, vulnerable
    )
    official = (
        "No active heat alert entered. Always check IMD (mausam.imd.gov.in)."
        if alert in ("none", "green")
        else f"IMD {alert.upper()} alert is active for Indore. Follow official guidance."
    )
    return {
        "level": result["level"],
        "why": result["why"],
        "actions": result["actions"],
        "safe_minutes": result["safe_minutes"],
        "temp_c": weather["temp_c"],
        "humidity": weather["humidity"],
        "apparent_c": weather["apparent_c"],
        "heat_index_c": result["heat_index_c"],
        "hours": [{"hour": item["hour"], "level": item["level"]} for item in hours],
        "best_hours": best_hours,
        "official_alert": official,
        "source": "Open-Meteo (weather) + HeatShield risk model",
        "updated": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "Awareness tool only. Not medical advice and not a substitute for official IMD warnings.",
    }


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/risk":
            try:
                body = json.dumps(make_response(urllib.parse.parse_qs(parsed.query))).encode()
                self.send_response(200)
            except Exception as exc:
                body = json.dumps({"error": f"Unable to fetch weather: {exc}"}).encode()
                self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


if __name__ == "__main__":
    os.chdir(ROOT / "frontend")
    port = int(os.environ.get("PORT", "8080"))
    print(f"HeatShield local demo: http://localhost:{port}/index.html")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
