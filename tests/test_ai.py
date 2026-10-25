"""Anomaly detection (Isolation Forest) and rule-based event classification."""

import pytest

from ai.anomaly_detector import model_info, predict_batch, predict_environment, validate_readings
from ai.event_classifier import analyze_batch, classify_event, classify_readings

NORMAL = dict(temperature=28, humidity=60, smoke=0.10, co2=420, air_quality=50, soil_moisture=55)
FIRE = dict(temperature=45, humidity=15, smoke=0.90, co2=950, air_quality=80, soil_moisture=20)
POLLUTION = dict(temperature=31, humidity=40, smoke=0.60, co2=1200, air_quality=180, soil_moisture=50)
HEAT = dict(temperature=43, humidity=40, smoke=0.15, co2=450, air_quality=60, soil_moisture=35)


def test_model_metadata():
    info = model_info()
    assert info["n_estimators"] == 200
    assert info["features"] == ["temperature", "humidity", "smoke", "co2", "air_quality", "soil_moisture"]


def test_normal_reading_is_normal():
    assert predict_environment(**NORMAL)["status"] == "NORMAL"
    assert classify_event(**NORMAL) == {"status": "NORMAL", "event": "None", "score": classify_event(**NORMAL)["score"]}


@pytest.mark.parametrize("readings,expected", [(FIRE, "FIRE"), (POLLUTION, "POLLUTION"), (HEAT, "EXTREME_HEAT")])
def test_hazards_are_anomalies_with_correct_class(readings, expected):
    result = classify_event(**readings)
    assert result["status"] == "ANOMALY"
    assert result["event"] == expected
    assert result["score"] < 0


def test_detector_and_classifier_are_separate():
    # The classifier rules alone say FIRE, but the detector decides whether it is anomalous at all.
    assert classify_readings(FIRE) == "FIRE"
    assert predict_batch([FIRE])[0]["status"] == "ANOMALY"


def test_batch_matches_single():
    batch = analyze_batch([NORMAL, FIRE, POLLUTION])
    assert [r["event"] for r in batch] == ["None", "FIRE", "POLLUTION"]


def test_low_false_alarm_rate_on_normal_variation():
    import random
    rng = random.Random(3)
    samples = [{k: v + rng.gauss(0, s) for (k, v), s in zip(NORMAL.items(), [1.5, 3, 0.01, 10, 3, 4])} for _ in range(500)]
    anomalies = sum(1 for r in predict_batch(samples) if r["status"] == "ANOMALY")
    assert anomalies / len(samples) < 0.03


@pytest.mark.parametrize("bad", [{**NORMAL, "smoke": 2.0}, {**NORMAL, "temperature": float("nan")},
                                 {k: v for k, v in NORMAL.items() if k != "co2"}, {**NORMAL, "humidity": "wet"}])
def test_invalid_readings_rejected(bad):
    with pytest.raises(ValueError):
        validate_readings(bad)
