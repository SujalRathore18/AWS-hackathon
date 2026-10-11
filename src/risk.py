import math

LEVELS = ["Low", "Moderate", "High", "Extreme"]
ACTIVITY_OFFSET = {"commute": 1, "walking": 2, "outdoor_work": 5, "sports": 6}
ACTIVITY_FACTOR = {"commute": 1.0, "walking": 0.8, "outdoor_work": 0.5, "sports": 0.4}
BASE_MINUTES = [240, 120, 45, 15]
ALERT_FLOOR = {"none": 0, "green": 0, "yellow": 1, "orange": 2, "red": 3}
ACTIONS = {
    0: ["Carry water and sip regularly.", "Normal outdoor plans are fine."],
    1: ["Drink water every 20-30 minutes.", "Take breaks in shade.", "Wear light, loose clothes and a cap."],
    2: ["Move outdoor tasks to early morning or evening.", "Carry at least 1 litre of water; add ORS if sweating a lot.", "Rest in shade or indoors every 30 minutes."],
    3: ["Avoid outdoor activity if you can.", "If you must go out, keep trips very short and stay in shade.", "Stop at once if you feel dizzy, sick or confused and seek help."],
}


def c_to_f(c):
    return c * 9.0 / 5.0 + 32.0


def f_to_c(f):
    return (f - 32.0) * 5.0 / 9.0


def heat_index_c(temp_c, rh):
    t = c_to_f(temp_c)
    simple = 0.5 * (t + 61.0 + ((t - 68.0) * 1.2) + (rh * 0.094))
    if (simple + t) / 2.0 < 80.0:
        return round(f_to_c(simple), 1)
    hi = (-42.379 + 2.04901523 * t + 10.14333127 * rh
          - 0.22475541 * t * rh - 0.00683783 * t * t
          - 0.05481717 * rh * rh + 0.00122874 * t * t * rh
          + 0.00085282 * t * rh * rh - 0.00000199 * t * t * rh * rh)
    if rh < 13 and 80 <= t <= 112:
        hi -= ((13 - rh) / 4.0) * math.sqrt((17 - abs(t - 95.0)) / 17.0)
    elif rh > 85 and 80 <= t <= 87:
        hi += ((rh - 85) / 10.0) * ((87 - t) / 5.0)
    return round(f_to_c(hi), 1)


def level_for(effective_c):
    if effective_c >= 51:
        return 3
    if effective_c >= 39:
        return 2
    if effective_c >= 32:
        return 1
    return 0


def assess(temp_c, rh, activity, minutes, hour, alert="none", vulnerable=False):
    hi = heat_index_c(temp_c, rh)
    why = [f"Heat index is {hi}C ({temp_c}C at {rh}% humidity)."]
    extra = ACTIVITY_OFFSET.get(activity, 1)
    why.append(f"{activity.replace('_', ' ').title()} adds +{extra}C of effort.")
    if minutes >= 240:
        extra += 2
        why.append("Exposure of 4 hours or more adds +2C.")
    elif minutes >= 120:
        extra += 1
        why.append("Exposure of 2 hours or more adds +1C.")
    if 11 <= hour < 16:
        extra += 1
        why.append("Midday sun (11:00-16:00) adds +1C.")
    if vulnerable:
        extra += 2
        why.append("Your heat-sensitive profile adds +2C.")
    level = level_for(hi + extra)
    floor = ALERT_FLOOR.get(str(alert).lower(), 0)
    if floor > level:
        level = floor
        why.append(f"An official IMD {alert} alert raises the level to {LEVELS[level]}.")
    safe = int(BASE_MINUTES[level] * ACTIVITY_FACTOR.get(activity, 1.0))
    return {"level_index": level, "level": LEVELS[level], "heat_index_c": hi, "why": why, "actions": ACTIONS[level], "safe_minutes": safe}


def best_windows(forecast, activity, minutes, alert="none", vulnerable=False):
    hours = []
    for item in forecast:
        hour = int(item["time"][11:13])
        result = assess(item["temp_c"], item["humidity"], activity, minutes, hour, alert, vulnerable)
        hours.append({"hour": hour, "level": result["level"], "idx": result["level_index"]})
    if not hours:
        return [], []
    best = min(item["idx"] for item in hours)
    best_hours = [f"{item['hour']:02d}:00" for item in hours if item["idx"] == best]
    return hours, best_hours
