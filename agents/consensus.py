"""
Local consensus for one incident.

Only agents that know about the alert take part: the agents that detected it,
the neighbours that received the INCIDENT_ALERT and any investigators sent to
the area. Each of them votes using its OWN latest sensor analysis:

    SUPPORT  - its AI classified the same hazard type
    OPPOSE   - its readings are NORMAL and it is within OPPOSE_RANGE_M of the alert
    ABSTAIN  - its readings are anomalous but match a different pattern,
               it is too far from the alert point to observe it, or the
               coordinator cannot reach it over the network

    confidence = support / (support + oppose)

The incident is CONFIRMED when support >= CONSENSUS_MIN_SUPPORT and
confidence >= CONSENSUS_THRESHOLD. A single agent can therefore never confirm
an incident by itself, which suppresses isolated sensor faults.
"""

from simulation import config


def collect_votes(incident, participants, coordinator, network, evidence_point):
    """Return a list of vote dicts, one per participant."""
    votes = []
    lat, lng = evidence_point
    for agent in participants:
        vote = {
            "agent_id": agent.agent_id,
            "agent_type": agent.agent_type,
            "ai_status": agent.ai_result["status"],
            "ai_event": agent.ai_result["event"],
            "score": agent.ai_result["score"],
            "distance_m": round(agent.distance_to(lat, lng)),
        }
        if not agent.operational:
            vote.update(vote="ABSTAIN", reason="agent not operational")
        elif coordinator is not None and agent is not coordinator and network.hops(agent.agent_id, coordinator.agent_id) is None:
            vote.update(vote="ABSTAIN", reason="no network route to coordinator")
        elif vote["distance_m"] > config.EVIDENCE_RANGE_M:
            vote.update(vote="ABSTAIN", reason="outside sensing range")
        elif agent.ai_result["event"] == incident.incident_type:
            vote.update(vote="SUPPORT", reason=f"own readings classified {incident.incident_type}")
        elif agent.ai_result["status"] == "NORMAL" and vote["distance_m"] <= config.OPPOSE_RANGE_M:
            vote.update(vote="OPPOSE", reason="own readings are normal")
        elif agent.ai_result["status"] == "NORMAL":
            vote.update(vote="ABSTAIN", reason="normal, but too far to rule the hazard out")
        else:
            vote.update(vote="ABSTAIN", reason=f"anomalous but classified {agent.ai_result['event']}")
        votes.append(vote)
    return votes


def evaluate(votes) -> dict:
    support = [v["agent_id"] for v in votes if v["vote"] == "SUPPORT"]
    oppose = [v["agent_id"] for v in votes if v["vote"] == "OPPOSE"]
    abstain = [v["agent_id"] for v in votes if v["vote"] == "ABSTAIN"]
    counted = len(support) + len(oppose)
    confidence = round(len(support) / counted, 3) if counted else 0.0
    confirmed = len(support) >= config.CONSENSUS_MIN_SUPPORT and confidence >= config.CONSENSUS_THRESHOLD
    return {
        "supporters": support,
        "opposers": oppose,
        "abstained": abstain,
        "confidence": confidence,
        "confirmed": confirmed,
        "rule": f"support >= {config.CONSENSUS_MIN_SUPPORT} and support/(support+oppose) >= {config.CONSENSUS_THRESHOLD}",
    }
