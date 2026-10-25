"""A single faulty sensor must not be able to confirm an incident."""

from tests.helpers import make_engine, run_until


def test_single_faulty_sensor_is_rejected_by_consensus():
    engine = make_engine()
    faulty = engine.agents_by_id["SP-02"]
    engine.override_sensors("SP-02", {"temperature": 47, "humidity": 15, "smoke": 0.85, "co2": 900,
                                       "air_quality": 95, "soil_moisture": 20}, duration_ticks=40)

    def reported():
        return any(i.origin == "AGENT_REPORT" for i in engine.incidents.values())
    assert run_until(engine, reported, 10)
    incident = next(i for i in engine.incidents.values() if i.origin == "AGENT_REPORT")
    assert incident.physical is False and incident.detectors == [faulty.agent_id]

    assert run_until(engine, lambda: incident.status == "REJECTED", 40)
    assert incident.confirmed_tick is None
    assert incident.consensus["decision"] == "REJECTED"
    assert len(incident.consensus["supporters"]) < 2 or incident.consensus["confidence"] < 0.6
    # no response units were dispatched for the false alarm
    assert not [t for t in incident.task_ids if engine.tasks[t].task_type != "INVESTIGATE"]


def test_votes_explain_each_agent():
    engine = make_engine()
    engine.override_sensors("SP-02", {"temperature": 47, "humidity": 15, "smoke": 0.85}, duration_ticks=40)
    run_until(engine, lambda: any(i.consensus for i in engine.incidents.values()), 15)
    incident = next(i for i in engine.incidents.values() if i.consensus)
    for vote in incident.consensus["votes"]:
        assert vote["vote"] in ("SUPPORT", "OPPOSE", "ABSTAIN")
        assert vote["reason"]
