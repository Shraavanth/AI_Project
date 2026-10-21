import pytest
from simulation.environment_model import EnvironmentalModel


def test_network_creation_and_failure_recovery():
    model = EnvironmentalModel(width=20, height=20, num_agents=20)
    model.create_demo_layout()

    initial_stats = model.get_statistics()
    assert initial_stats["total_agents"] == 20
    assert initial_stats["active_agents"] == 20
    assert initial_stats["failed_agents"] == 0
    assert initial_stats["connections"] > 0

    # Fail agent A6 (in center)
    failed = model.fail_agent("A6")
    assert failed.status == "FAILED"
    assert len(failed.neighbors) == 0

    # Self-organize and rebuild
    model.rebuild_network(max_distance=4)
    stats_after = model.get_statistics()
    assert stats_after["failed_agents"] == 1
    assert stats_after["active_agents"] == 19
    assert stats_after["connections"] > 0
