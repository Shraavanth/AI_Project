import networkx as nx


class NetworkManager:

    def __init__(self):
        self.graph = nx.Graph()

    def add_agent(self, agent):
        self.graph.add_node(
            agent.agent_id,
            agent=agent,
            position=(agent.x, agent.y)
        )

    def connect_agents(self, agent_a, agent_b):
        if agent_a.status != "ACTIVE" or agent_b.status != "ACTIVE":
            return

        self.graph.add_edge(
            agent_a.agent_id,
            agent_b.agent_id
        )

        agent_a.add_neighbor(agent_b)
        agent_b.add_neighbor(agent_a)

    def remove_agent_connections(self, agent):
        """
        Remove all communication links of a failed agent.
        """

        if agent.agent_id in self.graph:
            self.graph.remove_edges_from(
                list(self.graph.edges(agent.agent_id))
            )

        agent.neighbors.clear()

    def reorganize_network(self, agents, max_distance=2):
        """
        Automatically reconnect nearby active agents
        after failures.
        """

        active_agents = [
            agent for agent in agents
            if agent.status == "ACTIVE"
        ]

        print("\n[NETWORK RECOVERY] Searching for replacement links...")

        for i in range(len(active_agents)):
            for j in range(i + 1, len(active_agents)):

                agent_a = active_agents[i]
                agent_b = active_agents[j]

                distance = (
                    abs(agent_a.x - agent_b.x)
                    + abs(agent_a.y - agent_b.y)
                )

                if distance <= max_distance:

                    if not self.graph.has_edge(
                        agent_a.agent_id,
                        agent_b.agent_id
                    ):
                        self.connect_agents(
                            agent_a,
                            agent_b
                        )

                        print(
                            f"[NETWORK RECOVERY] "
                            f"{agent_a.agent_id} <-> "
                            f"{agent_b.agent_id}"
                        )

    def get_neighbors(self, agent):
        if agent.agent_id not in self.graph:
            return []

        return [
            self.graph.nodes[node]["agent"]
            for node in self.graph.neighbors(agent.agent_id)
        ]

    def is_connected(self):
        active_nodes = [
            node for node, data in self.graph.nodes(data=True)
            if data.get("agent") and data["agent"].status == "ACTIVE"
        ]
        if len(active_nodes) <= 1:
            return True

        subgraph = self.graph.subgraph(active_nodes)
        return nx.is_connected(subgraph)

    def get_network_info(self):
        return {
            "agents": self.graph.number_of_nodes(),
            "connections": self.graph.number_of_edges(),
            "connected": self.is_connected()
        }