from event_classifier import classify_event


scenarios = {
    "Normal": {
        "temperature": 28,
        "humidity": 60,
        "smoke": 0.10,
        "co2": 420,
        "air_quality": 50,
        "soil_moisture": 55
    },

    "Fire": {
        "temperature": 45,
        "humidity": 15,
        "smoke": 0.90,
        "co2": 950,
        "air_quality": 80,
        "soil_moisture": 20
    },

    "Pollution": {
        "temperature": 31,
        "humidity": 40,
        "smoke": 0.60,
        "co2": 1200,
        "air_quality": 180,
        "soil_moisture": 50
    },

    "Extreme Heat": {
        "temperature": 43,
        "humidity": 40,
        "smoke": 0.15,
        "co2": 450,
        "air_quality": 60,
        "soil_moisture": 35
    }
}


for name, values in scenarios.items():

    result = classify_event(**values)

    print("=" * 50)
    print(f"Scenario: {name}")
    print(f"Status:   {result['status']}")
    print(f"Event:    {result['event']}")
    print(f"Score:    {result['score']}")