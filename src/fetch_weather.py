import json
import os
import urllib.request
from datetime import datetime, timezone

import boto3

table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=22.7196&longitude=75.8577"
    "&current=temperature_2m,relative_humidity_2m,apparent_temperature"
    "&hourly=temperature_2m,relative_humidity_2m,apparent_temperature"
    "&forecast_days=2&timezone=Asia%2FKolkata"
)


def handler(event, context):
    with urllib.request.urlopen(URL, timeout=10) as response:
        data = json.load(response)
    current = data["current"]
    hourly = data["hourly"]
    now_hour = current["time"][:13] + ":00"
    start = next((i for i, value in enumerate(hourly["time"]) if value >= now_hour), 0)
    end = min(start + 12, len(hourly["time"]))
    forecast = [
        {
            "time": hourly["time"][i],
            "temp_c": hourly["temperature_2m"][i],
            "humidity": hourly["relative_humidity_2m"][i],
            "apparent_c": hourly["apparent_temperature"][i],
        }
        for i in range(start, end)
    ]
    payload = {
        "temp_c": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "apparent_c": current["apparent_temperature"],
        "observed_at": current["time"],
        "forecast": forecast,
    }
    table.put_item(Item={
        "city": "Indore",
        "payload": json.dumps(payload),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True, "observed_at": current["time"]}
