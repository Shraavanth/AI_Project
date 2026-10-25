"""
Communication network (NetworkX graph) and self-organization.

Every tick the graph is rebuilt from the agents' real positions:

1. Range links  - two operational agents closer than COMM_RANGE_M (Haversine)
                  are linked automatically.
2. Relay links  - self-organization. If the graph has split into separate
                  clusters (for example because an agent failed or drones flew
                  apart), the closest pair of agents in two different clusters
                  raise their transmit power and form a relay link, as long as
                  they are within MAX_RELAY_RANGE_M. This repeats until the
                  graph is connected or no bridge is possible.

If no bridge is possible the network stays partitioned, and that is reported
honestly (connected = False, number of components).
"""

import time
from itertools import combinations

import networkx as nx

from simulation import config
from simulation.geo import haversine_m


def _edge_key(a: str, b: str):
    return tuple(sorted((a, b)))


class NetworkManager:

    def __init__(self):
        self.graph = nx.Graph()
        self._path_cache = {}

    # --------------------------------------------------------------
    # Build / self-organize
    # --------------------------------------------------------------

    def rebuild(self, agents) -> dict:
        started = time.perf_counter()
        old_edges = {_edge_key(a, b) for a, b in self.graph.edges()}

        operational = [a for a in agents if a.operational]
        graph = nx.Graph()
        for agent in operational:
            graph.add_node(agent.agent_id)

        distances = {}
        for a, b in combinations(operational, 2):
            d = haversine_m(a.lat, a.lng, b.lat, b.lng)
            distances[_edge_key(a.agent_id, b.agent_id)] = d
            if d <= config.COMM_RANGE_M:
                graph.add_edge(a.agent_id, b.agent_id, distance_m=round(d), kind="range")

        components_before = nx.number_connected_components(graph) if operational else 0
        relay_links = self._bridge_components(graph, distances)

        self.graph = graph
        self._path_cache = {}

        new_edges = {_edge_key(a, b) for a, b in graph.edges()}
        return {
            "added": sorted(new_edges - old_edges),
            "removed": sorted(old_edges - new_edges),
            "relay_links": relay_links,
            "components_before_bridging": components_before,
            "components": self.component_count(),
            "connected": self.is_connected(),
            "edges": graph.number_of_edges(),
            "compute_ms": round((time.perf_counter() - started) * 1000, 3),
        }

    def _bridge_components(self, graph, distances) -> list:
        created = []
        while graph.number_of_nodes() > 1 and not nx.is_connected(graph):
            component_of = {}
            for index, component in enumerate(nx.connected_components(graph)):
                for node in component:
                    component_of[node] = index
            best = None
            for (a, b), d in distances.items():
                if component_of[a] != component_of[b] and d <= config.MAX_RELAY_RANGE_M:
                    if best is None or d < best[0]:
                        best = (d, a, b)
            if best is None:
                break  # clusters are too far apart: network stays partitioned
            d, a, b = best
            graph.add_edge(a, b, distance_m=round(d), kind="relay")
            created.append([a, b, round(d)])
        return created

    # --------------------------------------------------------------
    # Queries
    # --------------------------------------------------------------

    def neighbors(self, agent_id: str) -> list:
        if agent_id not in self.graph:
            return []
        return sorted(self.graph.neighbors(agent_id))

    def hops(self, source: str, target: str):
        """Number of hops between two agents, or None if there is no route."""
        if source not in self.graph or target not in self.graph:
            return None
        if source == target:
            return 0
        lengths = self._path_cache.get(source)
        if lengths is None:
            lengths = nx.single_source_shortest_path_length(self.graph, source)
            self._path_cache[source] = lengths
        return lengths.get(target)

    def is_connected(self) -> bool:
        if self.graph.number_of_nodes() <= 1:
            return True
        return nx.is_connected(self.graph)

    def component_count(self) -> int:
        if self.graph.number_of_nodes() == 0:
            return 0
        return nx.number_connected_components(self.graph)

    def components(self) -> list:
        return [sorted(c) for c in nx.connected_components(self.graph)]

    def edges(self) -> list:
        return [
            {"source": a, "target": b,
             "distance_m": data.get("distance_m"), "kind": data.get("kind", "range")}
            for a, b, data in self.graph.edges(data=True)
        ]
