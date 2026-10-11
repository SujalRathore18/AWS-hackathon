import json
import os
from datetime import datetime, timedelta, timezone

import boto3

import risk

table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
IST = timezone(timedelta(hours=5, minutes=30))
HEADERS = {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}
DISCLAIMER = "Awareness tool only. Not medical advice and not a substitute for official IMD warnings."


def reply(code, body):
    return {"statusCode": code, "headers": HEADERS, "body": json.dumps(body)}


def handler(event, context):
    query = event.get("queryStringParameters") or {}
    activity = query.get("activity", "commute")
    if activity not in risk.ACTIVITY_OFFSET:
        return reply(400, {"error": "activity must be commute, walking, outdoor_work, or sports."})
    try:
        minutes = int(query.get("minutes", "60"))
    except (TypeError, ValueError):
        return reply(400, {"error": "minutes must be a whole number from 5 to 600."})
    if not 5 <= minutes <= 600:
        return reply(400, {"error": "minutes must be a whole number from 5 to 600."})
    vulnerable = query.get("vulnerable") == "1"
    item = table.get_item(Key={"city": "Indore"}).get("Item")
    if not item:
        return reply(503, {"error": "Weather data is not ready yet. Try again shortly."})
    try:
        weather = json.loads(item["payload"])
        temp_c = float(weather["temp_c"])
        humidity = float(weather["humidity"])
        forecast = weather["forecast"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return reply(502, {"error": "Weather data is unavailable. Try again shortly."})
    alert_item = table.get_item(Key={"city": "IMD_Indore"}).get("Item")
    alert = alert_item.get("color", "none").lower() if alert_item else "none"
    if alert in ("none", "green"):
        official = "No active heat alert entered. Always check IMD (mausam.imd.gov.in) for official warnings."
    else:
        official = f"IMD {alert.upper()} alert is active for Indore. Follow official guidance."
    hour = datetime.now(IST).hour
    try:
        result = risk.assess(temp_c, humidity, activity, minutes, hour, alert, vulnerable)
        hours, best_hours = risk.best_windows(forecast, activity, minutes, alert, vulnerable)
        fetched = datetime.fromisoformat(item["fetched_at"])
    except (KeyError, TypeError, ValueError):
        return reply(502, {"error": "Weather data is unavailable. Try again shortly."})
    age = int((datetime.now(timezone.utc) - fetched).total_seconds() // 60)
    state = "STALE" if age > 90 else "LIVE"
    return reply(200, {
        "level": result["level"],
        "why": result["why"],
        "actions": result["actions"],
        "safe_minutes": result["planning_limit_minutes"],
        "planning_limit_minutes": result["planning_limit_minutes"],
        "temp_c": temp_c,
        "humidity": humidity,
        "apparent_c": weather["apparent_c"],
        "heat_index_c": result["heat_index_c"],
        "hours": [{"hour": value["hour"], "level": value["level"]} for value in hours],
        "best_hours": best_hours,
        "official_alert": official,
        "source": "Open-Meteo (weather) + HeatShield risk model",
        "updated": item["fetched_at"],
        "age_minutes": age,
        "data_state": state,
        "model_note": result["model_note"],
        "disclaimer": DISCLAIMER,
    })
