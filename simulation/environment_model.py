import random
import sys
import os


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# IMPORTS
# ============================================================

from agents.monitoring_agent import MonitoringAgent
from agents.consensus import ConsensusManager
from network.network_manager import NetworkManager


# ============================================================
# ENVIRONMENTAL MODEL
# ============================================================

class EnvironmentalModel:

    def __init__(
        self,
        width=20,
        height=20,
        num_agents=20
    ):

        self.width = width
        self.height = height
        self.num_agents = num_agents

        self.agents = []

        self.network = NetworkManager()

        # Create agents
        self.create_agents()

        # Create initial communication network
        self.create_network()

    # ========================================================
    # CREATE AGENTS
    # ========================================================

    def create_agents(self):

        for i in range(self.num_agents):

            agent_id = f"A{i + 1}"

            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)

            # Normal environmental values
            temperature = random.normalvariate(28, 3)
            humidity = random.normalvariate(60, 8)
            smoke = random.normalvariate(0.10, 0.03)
            co2 = random.normalvariate(420, 30)
            air_quality = random.normalvariate(50, 8)
            soil_moisture = random.normalvariate(55, 10)

            # Limit values
            temperature = max(
                10,
                min(50, temperature)
            )

            humidity = max(
                10,
                min(100, humidity)
            )

            smoke = max(
                0,
                min(1, smoke)
            )

            co2 = max(
                300,
                min(2000, co2)
            )

            air_quality = max(
                0,
                min(500, air_quality)
            )

            soil_moisture = max(
                0,
                min(100, soil_moisture)
            )

            # Create agent
            agent = MonitoringAgent(
                agent_id=agent_id,
                x=x,
                y=y,
                temperature=temperature,
                humidity=humidity,
                smoke=smoke,
                co2=co2,
                air_quality=air_quality,
                soil_moisture=soil_moisture
            )

            self.agents.append(agent)

            self.network.add_agent(agent)

    # ========================================================
    # CREATE NETWORK
    # ========================================================

    def create_network(self, max_distance=4):

        for i in range(len(self.agents)):

            for j in range(i + 1, len(self.agents)):

                agent_a = self.agents[i]
                agent_b = self.agents[j]

                distance = (
                    abs(agent_a.x - agent_b.x)
                    + abs(agent_a.y - agent_b.y)
                )

                if distance <= max_distance:

                    self.network.connect_agents(
                        agent_a,
                        agent_b
                    )

    # ========================================================
    # REBUILD NETWORK
    # ========================================================

    def rebuild_network(self, max_distance=4):

        # Remove existing edges
        self.network.graph.remove_edges_from(
            list(self.network.graph.edges())
        )

        # Clear neighbors
        for agent in self.agents:
            agent.neighbors.clear()

        # Rebuild
        self.create_network(
            max_distance=max_distance
        )

    # ========================================================
    # DEMONSTRATION LAYOUT
    # ========================================================

    def create_demo_layout(self):

        demo_positions = [
            (2, 3),    # A1
            (5, 6),    # A2
            (7, 8),    # A3

            # Fire epicenter cluster
            (9, 10),   # A4
            (10, 9),   # A5
            (10, 10),  # A6
            (11, 10),  # A7
            (10, 11),  # A8
            (12, 11),  # A9

            (13, 12),  # A10
            (16, 15),  # A11
            (5, 14),   # A12
            (13, 8),   # A13
            (4, 4),    # A14

            # Fire perimeter & bridges
            (8, 10),   # A15
            (12, 10),  # A16

            (6, 12),   # A17
            (14, 14),  # A18
            (15, 6),   # A19
            (4, 16)    # A20
        ]

        for agent, position in zip(
            self.agents,
            demo_positions
        ):

            agent.x = position[0]
            agent.y = position[1]

            # Update NetworkX node position
            self.network.graph.nodes[
                agent.agent_id
            ]["position"] = position

        # Rebuild network after moving agents
        self.rebuild_network()

    # ========================================================
    # CREATE FIRE EVENT
    # ========================================================

    def create_fire_event(
        self,
        center_x,
        center_y,
        radius=3
    ):

        affected_agents = []

        print(
            f"[ENVIRONMENT] Fire event created at "
            f"({center_x}, {center_y})"
        )

        print(
            f"[ENVIRONMENT] Fire radius: {radius}"
        )

        for agent in self.agents:

            distance = (
                abs(agent.x - center_x)
                + abs(agent.y - center_y)
            )

            if distance <= radius:

                # Simulated fire conditions
                agent.temperature = random.uniform(
                    42,
                    48
                )

                agent.humidity = random.uniform(
                    10,
                    25
                )

                agent.smoke = random.uniform(
                    0.70,
                    1.00
                )

                agent.co2 = random.uniform(
                    850,
                    1200
                )

                agent.air_quality = random.uniform(
                    70,
                    120
                )

                agent.soil_moisture = random.uniform(
                    10,
                    30
                )

                affected_agents.append(agent)

        print(
            f"[ENVIRONMENT] "
            f"{len(affected_agents)} agents affected"
        )

        return affected_agents

    # ========================================================
    # ANALYZE ENVIRONMENT
    # ========================================================

    def analyze_environment(self):

        results = {}

        for agent in self.agents:

            if agent.status != "ACTIVE":
                continue

            result = agent.analyze_environment()

            results[agent.agent_id] = result

        return results

    # ========================================================
    # BROADCAST ALERTS
    # ========================================================

    def broadcast_alerts(self):

        fire_agents = self.get_fire_agents()

        print(
            f"\n[COMMUNICATION] "
            f"{len(fire_agents)} agents detected FIRE"
        )

        for agent in fire_agents:

            agent.broadcast_alert()

        return fire_agents

    # ========================================================
    # LOCAL / DISTRIBUTED CONSENSUS
    # ========================================================

    def determine_consensus(self):

        return ConsensusManager.determine_network_consensus(
            self.get_active_agents(),
            threshold=0.5
        )

    # ========================================================
    # ACTIVE AGENTS
    # ========================================================

    def get_active_agents(self):

        return [
            agent
            for agent in self.agents
            if agent.status == "ACTIVE"
        ]

    # ========================================================
    # FAILED AGENTS
    # ========================================================

    def get_failed_agents(self):

        return [
            agent
            for agent in self.agents
            if agent.status == "FAILED"
        ]

    # ========================================================
    # CREATE POLLUTION EVENT
    # ========================================================

    def create_pollution_event(
        self,
        center_x=10,
        center_y=10,
        radius=3
    ):
        affected_agents = []

        for agent in self.agents:
            distance = (
                abs(agent.x - center_x)
                + abs(agent.y - center_y)
            )

            if distance <= radius:
                agent.temperature = round(random.uniform(28, 33), 1)
                agent.humidity = round(random.uniform(35, 45), 1)
                agent.smoke = round(random.uniform(0.35, 0.65), 2)
                agent.co2 = round(random.uniform(850, 1300), 1)
                agent.air_quality = round(random.uniform(140, 220), 1)
                agent.soil_moisture = round(random.uniform(40, 60), 1)
                affected_agents.append(agent)

        return affected_agents

    # ========================================================
    # CREATE EXTREME HEAT EVENT
    # ========================================================

    def create_extreme_heat_event(
        self,
        center_x=10,
        center_y=10,
        radius=3
    ):
        affected_agents = []

        for agent in self.agents:
            distance = (
                abs(agent.x - center_x)
                + abs(agent.y - center_y)
            )

            if distance <= radius:
                agent.temperature = round(random.uniform(42, 49), 1)
                agent.humidity = round(random.uniform(15, 30), 1)
                agent.smoke = round(random.uniform(0.05, 0.20), 2)
                agent.co2 = round(random.uniform(400, 520), 1)
                agent.air_quality = round(random.uniform(40, 75), 1)
                agent.soil_moisture = round(random.uniform(10, 25), 1)
                affected_agents.append(agent)

        return affected_agents

    # ========================================================
    # AGENT MANAGEMENT & CONTROLS
    # ========================================================

    def get_agent(self, agent_id):
        for agent in self.agents:
            if agent.agent_id == agent_id:
                return agent
        return None

    def add_custom_agent(
        self,
        agent_id=None,
        x=0,
        y=0,
        temperature=28.0,
        humidity=60.0,
        smoke=0.10,
        co2=420.0,
        air_quality=50.0,
        soil_moisture=55.0,
        battery=100
    ):
        if agent_id is None:
            agent_id = f"A{len(self.agents) + 1}"

        if self.get_agent(agent_id):
            raise ValueError(f"Agent {agent_id} already exists")

        new_agent = MonitoringAgent(
            agent_id=agent_id,
            x=int(x),
            y=int(y),
            temperature=float(temperature),
            humidity=float(humidity),
            smoke=float(smoke),
            co2=float(co2),
            air_quality=float(air_quality),
            soil_moisture=float(soil_moisture),
            battery=int(battery)
        )

        self.agents.append(new_agent)
        self.network.add_agent(new_agent)
        self.rebuild_network()
        return new_agent

    def move_agent(self, agent_id, new_x, new_y):
        agent = self.get_agent(agent_id)
        if not agent:
            return None

        agent.x = int(new_x)
        agent.y = int(new_y)

        if agent_id in self.network.graph:
            self.network.graph.nodes[agent_id]["position"] = (agent.x, agent.y)

        self.rebuild_network()
        return agent

    def remove_agent(self, agent_id):
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        self.network.remove_agent_connections(agent)
        if agent_id in self.network.graph:
            self.network.graph.remove_node(agent_id)

        self.agents.remove(agent)
        self.rebuild_network()
        return True

    def fail_agent(self, agent_id):
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        if agent.status == "FAILED":
            return agent

        agent.status = "FAILED"
        agent.battery = 0
        self.network.remove_agent_connections(agent)
        return agent

    def restore_agent(self, agent_id):
        agent = self.get_agent(agent_id)
        if not agent:
            return None

        agent.status = "ACTIVE"
        agent.battery = 100
        self.rebuild_network()
        return agent

    def update_agent_sensors(self, agent_id, readings: dict):
        agent = self.get_agent(agent_id)
        if not agent:
            return None

        if "temperature" in readings and readings["temperature"] is not None:
            agent.temperature = float(readings["temperature"])
        if "humidity" in readings and readings["humidity"] is not None:
            agent.humidity = float(readings["humidity"])
        if "smoke" in readings and readings["smoke"] is not None:
            agent.smoke = float(readings["smoke"])
        if "co2" in readings and readings["co2"] is not None:
            agent.co2 = float(readings["co2"])
        if "air_quality" in readings and readings["air_quality"] is not None:
            agent.air_quality = float(readings["air_quality"])
        if "soil_moisture" in readings and readings["soil_moisture"] is not None:
            agent.soil_moisture = float(readings["soil_moisture"])
        if "battery" in readings and readings["battery"] is not None:
            agent.battery = int(readings["battery"])

        # Re-run local AI
        agent.analyze_environment()
        return agent

    def move_agent_direction(self, agent_id, direction):
        agent = self.get_agent(agent_id)
        if not agent or agent.status != "ACTIVE":
            return None

        dx, dy = 0, 0
        direction = direction.upper()
        if direction == "UP":
            dy = -1
        elif direction == "DOWN":
            dy = 1
        elif direction == "LEFT":
            dx = -1
        elif direction == "RIGHT":
            dx = 1

        new_x = max(0, min(self.width - 1, agent.x + dx))
        new_y = max(0, min(self.height - 1, agent.y + dy))
        return self.move_agent(agent_id, new_x, new_y)

    def step_patrol(self):
        """Autonomous drone patrol movement: active agents perform small drift movements."""
        for agent in self.get_active_agents():
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            agent.x = max(0, min(self.width - 1, agent.x + dx))
            agent.y = max(0, min(self.height - 1, agent.y + dy))
            if agent.agent_id in self.network.graph:
                self.network.graph.nodes[agent.agent_id]["position"] = (agent.x, agent.y)

        self.rebuild_network()
        return self.get_statistics()


    # ========================================================
    # FIRE DETECTORS
    # ========================================================

    def get_fire_agents(self):

        return [
            agent
            for agent in self.get_active_agents()
            if (
                agent.ai_result
                and agent.ai_result["event"] == "FIRE"
            )
        ]

    # ========================================================
    # STATISTICS
    # ========================================================

    def get_statistics(self):

        active_agents = self.get_active_agents()

        failed_agents = self.get_failed_agents()

        anomalies = [
            agent
            for agent in active_agents
            if (
                agent.ai_result
                and agent.ai_result["status"] == "ANOMALY"
            )
        ]

        fire_agents = self.get_fire_agents()
        pollution_agents = [
            a for a in active_agents
            if a.ai_result and a.ai_result["event"] == "POLLUTION"
        ]
        extreme_heat_agents = [
            a for a in active_agents
            if a.ai_result and a.ai_result["event"] == "EXTREME_HEAT"
        ]

        return {
            "total_agents": len(self.agents),
            "active_agents": len(active_agents),
            "failed_agents": len(failed_agents),
            "anomalies": len(anomalies),
            "fire_detections": len(fire_agents),
            "pollution_detections": len(pollution_agents),
            "extreme_heat_detections": len(extreme_heat_agents),
            "connections": self.network.graph.number_of_edges(),
            "network_connected": self.network.is_connected()
        }