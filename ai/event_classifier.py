"""
Environmental event classification (step 2 of the AI pipeline).

The Isolation Forest only says "this reading is unusual". It does NOT know what
a fire is. When a reading is anomalous, these simple, documented rules decide
which hazard the pattern matches:

    FIRE          temperature >= 40 C  AND humidity <= 30 %  AND smoke >= 0.50
    POLLUTION     CO2 >= 800 ppm       AND AQI >= 120        AND smoke >= 0.30
    EXTREME_HEAT  temperature >= 40 C  AND smoke < 0.30
    OTHER_ANOMALY anything else the detector flagged

Rules are checked top to bottom, so a hot, smoky, dry reading is FIRE rather
than EXTREME_HEAT.
"""

try:
    from ai.anomaly_detector import predict_batch, validate_readings
except ImportError:
    from anomaly_detector import predict_batch, validate_readings

RULES = {
    "FIRE": "temperature >= 40, humidity <= 30, smoke >= 0.50",
    "POLLUTION": "co2 >= 800, air_quality >= 120, smoke >= 0.30",
    "EXTREME_HEAT": "temperature >= 40 and smoke < 0.30",
    "OTHER_ANOMALY": "flagged by Isolation Forest, matches no hazard rule",
}


def classify_readings(r: dict) -> str:
    """Rule-based hazard type for a reading that is already known to be anomalous."""
    if r["temperature"] >= 40 and r["humidity"] <= 30 and r["smoke"] >= 0.50:
        return "FIRE"
    if r["co2"] >= 800 and r["air_quality"] >= 120 and r["smoke"] >= 0.30:
        return "POLLUTION"
    if r["temperature"] >= 40 and r["smoke"] < 0.30:
        return "EXTREME_HEAT"
    return "OTHER_ANOMALY"


def analyze_batch(readings_list: list) -> list:
    """Detector + classifier for a list of readings. Returns one result per reading."""
    detections = predict_batch(readings_list)
    results = []
    for readings, det in zip(readings_list, detections):
        if det["status"] == "NORMAL":
            results.append({"status": "NORMAL", "event": "None", "score": det["score"]})
        else:
            results.append({
                "status": "ANOMALY",
                "event": classify_readings(readings),
                "score": det["score"],
            })
    return results


def classify_event(temperature, humidity, smoke, co2, air_quality, soil_moisture) -> dict:
    """Single-reading helper (kept compatible with the first version of the project)."""
    readings = validate_readings({
        "temperature": temperature,
        "humidity": humidity,
        "smoke": smoke,
        "co2": co2,
        "air_quality": air_quality,
        "soil_moisture": soil_moisture,
    })
    return analyze_batch([readings])[0]
