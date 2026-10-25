"""Helpers shared by the tests (import as: from tests.helpers import ...)."""

from simulation.engine import SimulationEngine
from simulation.geo import offset

CENTER = (12.9692, 79.1559)


def make_engine(seed=7, warmup=5):
    engine = SimulationEngine(seed=seed)
    engine.deploy(CENTER[0], CENTER[1], 1200, "Test area", "DEMO")
    for _ in range(warmup):
        engine.step()
    return engine


def run_until(engine, condition, max_ticks=300):
    for _ in range(max_ticks):
        engine.step()
        if condition():
            return True
    return False


def fire_near_sprinkler(engine):
    lat, lng = offset(CENTER[0], CENTER[1], 300, 250)
    return engine.create_incident("FIRE", lat, lng)
