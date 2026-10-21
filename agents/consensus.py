from collections import Counter


class ConsensusManager:

    @staticmethod
    def collect_local_evidence(agent):
        """
        Collect the local environmental decision from:
        1. The agent itself
        2. Its active neighbors
        """

        evidence = []

        # ----------------------------------------------------
        # Agent's own decision
        # ----------------------------------------------------

        if agent.ai_result is None:
            agent.analyze_environment()

        evidence.append({
            "agent_id": agent.agent_id,
            "event": agent.ai_result["event"],
            "status": agent.ai_result["status"],
            "score": agent.ai_result["score"]
        })

        # ----------------------------------------------------
        # Neighbor decisions
        # ----------------------------------------------------

        for neighbor in agent.neighbors:

            if neighbor.status != "ACTIVE":
                continue

            if neighbor.ai_result is None:
                neighbor.analyze_environment()

            evidence.append({
                "agent_id": neighbor.agent_id,
                "event": neighbor.ai_result["event"],
                "status": neighbor.ai_result["status"],
                "score": neighbor.ai_result["score"]
            })

        return evidence

    @staticmethod
    def local_consensus(agent, threshold=0.5):
        """
        Calculate consensus using only the local neighborhood.
        """

        evidence = ConsensusManager.collect_local_evidence(agent)

        if not evidence:
            return {
                "consensus": False,
                "event": "NO_DATA",
                "confidence": 0.0,
                "evidence": []
            }

        # ----------------------------------------------------
        # Collect environmental events
        # ----------------------------------------------------

        events = [
            item["event"]
            for item in evidence
            if item["event"] != "None"
        ]

        # ----------------------------------------------------
        # All agents report normal
        # ----------------------------------------------------

        if not events:
            return {
                "consensus": True,
                "event": "NORMAL",
                "confidence": 1.0,
                "evidence": evidence
            }

        # ----------------------------------------------------
        # Count events
        # ----------------------------------------------------

        event_counts = Counter(events)

        event, count = event_counts.most_common(1)[0]

        confidence = count / len(evidence)

        consensus_reached = confidence >= threshold

        return {
            "consensus": consensus_reached,
            "event": event if consensus_reached else "UNCERTAIN",
            "confidence": round(confidence, 2),
            "evidence": evidence
        }

    @staticmethod
    def determine_network_consensus(
        agents,
        threshold=0.5
    ):
        """
        Determine network-level consensus from local
        neighborhood decisions.

        Each active agent independently calculates its
        own local consensus.
        """

        local_results = []

        # ----------------------------------------------------
        # Calculate local consensus for every active agent
        # ----------------------------------------------------

        for agent in agents:

            if agent.status != "ACTIVE":
                continue

            result = ConsensusManager.local_consensus(
                agent,
                threshold=threshold
            )

            local_results.append({
                "agent_id": agent.agent_id,
                "result": result
            })

        # ----------------------------------------------------
        # Extract locally confirmed non-normal events
        # ----------------------------------------------------

        confirmed_events = [
            item["result"]["event"]
            for item in local_results
            if (
                item["result"]["consensus"]
                and item["result"]["event"] != "NORMAL"
            )
        ]

        # ----------------------------------------------------
        # No local event consensus
        # ----------------------------------------------------

        if not confirmed_events:
            return {
                "consensus": False,
                "event": "UNCERTAIN",
                "confidence": 0.0,
                "local_results": local_results
            }

        # ----------------------------------------------------
        # Find strongest event
        # ----------------------------------------------------

        event_counts = Counter(confirmed_events)

        event, count = event_counts.most_common(1)[0]

        confidence = count / len(local_results)

        return {
            "consensus": True,
            "event": event,
            "confidence": round(confidence, 2),
            "local_results": local_results
        }