import pytest
from ai.anomaly_detector import predict_environment
from ai.event_classifier import classify_event


def test_normal_environment():
    res = predict_environment(
        temperature=28.0,
        humidity=60.0,
        smoke=0.10,
        co2=420.0,
        air_quality=50.0,
        soil_moisture=55.0
    )
    assert res["status"] == "NORMAL"
    assert "score" in res


def test_fire_classification():
    res = classify_event(
        temperature=46.0,
        humidity=15.0,
        smoke=0.88,
        co2=950.0,
        air_quality=85.0,
        soil_moisture=18.0
    )
    assert res["status"] == "ANOMALY"
    assert res["event"] == "FIRE"


def test_pollution_classification():
    res = classify_event(
        temperature=30.0,
        humidity=40.0,
        smoke=0.55,
        co2=1100.0,
        air_quality=180.0,
        soil_moisture=45.0
    )
    assert res["status"] == "ANOMALY"
    assert res["event"] == "POLLUTION"


def test_extreme_heat_classification():
    res = classify_event(
        temperature=44.0,
        humidity=35.0,
        smoke=0.08,
        co2=430.0,
        air_quality=50.0,
        soil_moisture=20.0
    )
    assert res["status"] == "ANOMALY"
    assert res["event"] == "EXTREME_HEAT"
