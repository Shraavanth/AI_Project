class SelfOrganizationManager:

    @staticmethod
    def detect_failed_agents(agents):
        """
        Return agents whose status is FAILED.
        """
        return [
            agent for agent in agents
            if agent.status == "FAILED"
        ]

    @staticmethod
    def reorganize_network(agents):
        """
        Reorganize the communication network after
        an agent failure.
        """

        failed_agents = SelfOrganizationManager.detect_failed_agents(agents)

        if not failed_agents:
            print("[SELF-ORGANIZATION] No failed agents detected.")
            return

        print("\n[SELF-ORGANIZATION] Failed agents detected:")

        for failed in failed_agents:
            print(f"- {failed.agent_id}")

        # Remove failed agents from all neighbor lists
        for agent in agents:
            for failed in failed_agents:
                if failed in agent.neighbors:
                    agent.remove_neighbor(failed)

        # Find active agents
        active_agents = [
            agent for agent in agents
            if agent.status == "ACTIVE"
        ]

        # Reconnect active agents that are geographically close
        for i in range(len(active_agents)):

            for j in range(i + 1, len(active_agents)):

                agent_a = active_agents[i]
                agent_b = active_agents[j]

                # Manhattan distance
                distance = (
                    abs(agent_a.x - agent_b.x)
                    + abs(agent_a.y - agent_b.y)
                )

                # Connect nearby agents
                if distance <= 2:

                    agent_a.add_neighbor(agent_b)
                    agent_b.add_neighbor(agent_a)

                    print(
                        f"[SELF-ORGANIZATION] "
                        f"New connection: "
                        f"{agent_a.agent_id} <-> {agent_b.agent_id}"
                    )