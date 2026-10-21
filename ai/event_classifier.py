try:
    from ai.anomaly_detector import predict_environment
except ImportError:
    from anomaly_detector import predict_environment


def classify_event(
    temperature,
    humidity,
    smoke,
    co2,
    air_quality,
    soil_moisture
):
    """
    Detect anomaly and classify the likely environmental event.
    """

    # First run the AI anomaly detector
    result = predict_environment(
        temperature=temperature,
        humidity=humidity,
        smoke=smoke,
        co2=co2,
        air_quality=air_quality,
        soil_moisture=soil_moisture
    )

    # If conditions are normal, no event classification is needed
    if result["status"] == "NORMAL":
        return {
            "status": "NORMAL",
            "event": "None",
            "score": result["score"]
        }

    # Fire-like conditions
    if (
        temperature >= 40
        and humidity <= 30
        and smoke >= 0.50
    ):
        event = "FIRE"

    # Pollution-like conditions
    elif (
        co2 >= 800
        and air_quality >= 120
        and smoke >= 0.30
    ):
        event = "POLLUTION"

    # Extreme heat
    elif temperature >= 40:
        event = "EXTREME_HEAT"

    # Any other unusual condition
    else:
        event = "OTHER_ANOMALY"

    return {
        "status": "ANOMALY",
        "event": event,
        "score": result["score"]
    }