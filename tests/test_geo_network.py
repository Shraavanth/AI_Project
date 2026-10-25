"""Geographic maths and the self-organizing network."""

import networkx as nx

from agents.agent import Agent
from network.network_manager import NetworkManager
from simulation import config
from simulation.environment import random_baseline
from simulation.geo import haversine_m, move_towards, offset

import random


def test_haversine_known_distance():
    # Chennai -> Bengaluru is roughly 290 km in a straight line
    d = haversine_m(13.0827, 80.2707, 12.9716, 77.5946)
    assert 285_000 < d < 295_000


def test_offset_round_trip():
    lat, lng = offset(12.97, 79.15, north_m=300, east_m=400)
    assert abs(haversine_m(12.97, 79.15, lat, lng) - 500) < 2


def test_move_towards_steps_and_arrives():
    target = offset(12.97, 79.15, 0, 100)
    lat, lng, moved, arrived = move_towards(12.97, 79.15, *target, step_m=30)
    assert not arrived and abs(moved - 30) < 0.01
    assert abs(haversine_m(lat, lng, *target) - 70) < 1
    _, _, _, arrived = move_towards(lat, lng, *target, step_m=100)
    assert arrived


def _agents_in_line(spacing_m, count=4):
    rng = random.Random(1)
    agents = []
    for i in range(count):
        lat, lng = offset(12.97, 79.15, 0, i * spacing_m)
        agents.append(Agent(f"MD-{i+1:02d}", "MONITOR_DRONE", lat, lng, random_baseline(rng)))
    return agents


def test_range_links_follow_geographic_distance():
    agents = _agents_in_line(500)
    net = NetworkManager()
    info = net.rebuild(agents)
    assert info["edges"] == 3 and info["connected"]
    assert all(e["kind"] == "range" for e in net.edges())


def test_failure_splits_network_and_relay_bridges_it():
    agents = _agents_in_line(500)
    net = NetworkManager()
    net.rebuild(agents)
    agents[1].status = "FAILED"
    info = net.rebuild(agents)
    # MD-01 and MD-03 are 1000 m apart: too far for a normal link, but within relay range
    assert ("MD-01", "MD-02") in info["removed"]
    assert info["components_before_bridging"] == 2
    assert info["relay_links"] and info["connected"]
    assert "MD-02" not in net.graph


def test_network_reports_partition_honestly():
    agents = _agents_in_line(700)   # 1400 m gap once the middle agent fails
    net = NetworkManager()
    net.rebuild(agents)
    agents[1].status = "FAILED"
    info = net.rebuild(agents)
    assert info["connected"] is False
    assert info["components"] == 2
    assert net.hops("MD-01", "MD-03") is None


def test_hops_multi_hop():
    agents = _agents_in_line(500)
    net = NetworkManager()
    net.rebuild(agents)
    assert net.hops("MD-01", "MD-04") == 3
