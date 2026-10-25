import sys
from simulation.environment_model import EnvironmentalModel

def test_partition_and_recovery():
    print("\n--- Verifying Agent Disconnection, Partition & Recovery ---")
    
    # 1. Initialize environment model with 20 demo agents
    model = EnvironmentalModel(20, 20, 20)
    model.create_demo_layout()
    
    assert model.network.is_connected(), "Initial demo mesh should be fully connected"
    initial_edge_count = model.network.graph.number_of_edges()
    print(f"Initial Connected Mesh: {model.network.graph.number_of_nodes()} nodes, {initial_edge_count} edges, Connected={model.network.is_connected()}")
    
    # 2. Identify key central node A6 in fire cluster
    a6 = model.get_agent("A6")
    a6_neighbors_before = [n.agent_id for n in a6.neighbors]
    print(f"Agent A6 initial neighbors: {a6_neighbors_before}")
    
    # 3. Simulate sudden hardware failure / node disconnection of A6
    failed = model.fail_agent("A6")
    assert failed.status == "FAILED"
    assert len(a6.neighbors) == 0, "Failed node must have 0 active neighbors"
    
    # Also disconnect neighboring bridge node A5 to test partition
    model.fail_agent("A5")
    
    edges_after_fail = model.network.graph.number_of_edges()
    print(f"After failing A6 & A5: {edges_after_fail} active edges (Lost {initial_edge_count - edges_after_fail} links)")
    
    # 4. Trigger Autonomous Self-Organizing Mesh Reorganization
    print("Initiating autonomous self-organizing mesh recovery with max_distance=4...")
    model.rebuild_network(max_distance=4)
    edges_after_heal = model.network.graph.number_of_edges()
    is_reconnected = model.network.is_connected()
    
    print(f"After self-healing: {edges_after_heal} edges, Network Connected={is_reconnected}")
    assert is_reconnected, "Mesh topology must autonomously re-establish global connectivity"
    assert "A6" not in [n.agent_id for a in model.get_active_agents() for n in a.neighbors], "Failed A6 must remain excluded from active links"
    
    # 5. Restore node and verify reintegration
    print("Restoring Agent A6...")
    restored = model.restore_agent("A6")
    assert restored.status == "ACTIVE"
    assert model.network.is_connected()
    print(f"Agent A6 re-integrated with {len(restored.neighbors)} peer links: {[n.agent_id for n in restored.neighbors]}")
    
    print("[PASS] Agent disconnection, partition, self-organization, and reintegration verified successfully.")
    return True

if __name__ == "__main__":
    success = test_partition_and_recovery()
    sys.exit(0 if success else 1)
