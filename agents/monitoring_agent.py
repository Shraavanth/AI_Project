import sys
import os


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

AI_PATH = os.path.join(PROJECT_ROOT, "ai")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if AI_PATH not in sys.path:
    sys.path.insert(0, AI_PATH)


try:
    from ai.event_classifier import classify_event
except (ImportError, ModuleNotFoundError):
    try:
        from event_classifier import classify_event
    except (ImportError, ModuleNotFoundError):
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai")))
        from event_classifier import classify_event


# ============================================================
# IMPORT COMMUNICATION
# ============================================================

try:
    # Works when project is run as a package
    from agents.communication import CommunicationManager
except ModuleNotFoundError:
    # Works when test files are run directly from agents/
    from communication import CommunicationManager


# ============================================================
# MONITORING AGENT
# ============================================================

class MonitoringAgent:

    def __init__(
        self,
        agent_id,
        x,
        y,
        temperature,
        humidity,
        smoke,
        co2,
        air_quality,
        soil_moisture,
        battery=100
    ):

        self.agent_id = agent_id

        self.x = x
        self.y = y
        self.deployed_latitude = None
        self.deployed_longitude = None
        self.deployment_area_label = None

        self.temperature = temperature
        self.humidity = humidity
        self.smoke = smoke
        self.co2 = co2
        self.air_quality = air_quality
        self.soil_moisture = soil_moisture

        self.battery = battery
        self.status = "ACTIVE"

        self.neighbors = []

        self.ai_result = None

        self.messages = []

    # ========================================================
    # ENVIRONMENTAL READINGS
    # ========================================================

    def get_readings(self):

        return {
            "temperature": self.temperature,
            "humidity": self.humidity,
            "smoke": self.smoke,
            "co2": self.co2,
            "air_quality": self.air_quality,
            "soil_moisture": self.soil_moisture
        }

    # ========================================================
    # AI ANALYSIS
    # ========================================================

    def analyze_environment(self):

        self.ai_result = classify_event(
            temperature=self.temperature,
            humidity=self.humidity,
            smoke=self.smoke,
            co2=self.co2,
            air_quality=self.air_quality,
            soil_moisture=self.soil_moisture
        )

        return self.ai_result

    # ========================================================
    # NEIGHBORS
    # ========================================================

    def add_neighbor(self, agent):

        if agent not in self.neighbors:
            self.neighbors.append(agent)

    def remove_neighbor(self, agent):

        if agent in self.neighbors:
            self.neighbors.remove(agent)

    # ========================================================
    # RECEIVE MESSAGE
    # ========================================================

    def receive_message(self, sender, message):

        self.messages.append({
            "sender": sender.agent_id,
            "message": message
        })

        print(
            f"[RECEIVED] "
            f"{self.agent_id} received from "
            f"{sender.agent_id}: {message}"
        )

    # ========================================================
    # BROADCAST ALERT
    # ========================================================

    def broadcast_alert(self):

        # Run AI analysis if necessary
        if self.ai_result is None:
            self.analyze_environment()

        # Only anomalous agents send alerts
        if self.ai_result["status"] != "ANOMALY":
            return

        message = {
            "type": "ENVIRONMENTAL_ALERT",
            "event": self.ai_result["event"],
            "score": self.ai_result["score"]
        }

        # Send alert to active neighbors
        for neighbor in self.neighbors:

            if neighbor.status == "ACTIVE":

                CommunicationManager.send_message(
                    self,
                    neighbor,
                    message
                )

    # ========================================================
    # HEALTH & RELIABILITY METRICS
    # ========================================================

    @property
    def health(self):
        if self.status == "FAILED":
            return 0
        # Health score based on battery and operating parameters
        base = 100
        if self.battery < 30:
            base -= 20
        elif self.battery < 60:
            base -= 10
        if self.temperature > 45 or self.smoke > 0.8:
            base -= 15
        return max(0, min(100, base))

    @property
    def connectivity(self):
        if self.status == "FAILED":
            return 0
        active_neighbors = len([n for n in self.neighbors if n.status == "ACTIVE"])
        # 3 or more active neighbors = 100% connectivity mesh rating
        return min(100, int(active_neighbors * 33.4))

    @property
    def reliability(self):
        if self.status == "FAILED":
            return 0
        return int((self.health * 0.6) + (self.battery * 0.4))

    def get_ai_explanation(self):
        if not self.ai_result:
            self.analyze_environment()

        status = self.ai_result.get("status", "NORMAL")
        event = self.ai_result.get("event", "None")

        temp_eval = "HIGH" if self.temperature >= 40 else "NORMAL" if self.temperature >= 20 else "LOW"
        smoke_eval = "VERY HIGH" if self.smoke >= 0.7 else "HIGH" if self.smoke >= 0.4 else "NORMAL"
        hum_eval = "LOW" if self.humidity <= 30 else "NORMAL"
        co2_eval = "HIGH" if self.co2 >= 800 else "NORMAL"
        aq_eval = "HAZARDOUS" if self.air_quality >= 150 else "MODERATE" if self.air_quality >= 80 else "GOOD"

        if status == "NORMAL":
            narrative = "All sensor values are within baseline environmental parameters."
        elif event == "FIRE":
            narrative = "Elevated temperature and high smoke levels indicate an active combustion hazard."
        elif event == "POLLUTION":
            narrative = "High CO2 and degraded air quality indicate atmospheric particulate pollution."
        elif event == "EXTREME_HEAT":
            narrative = "Critical ambient temperature detected without combustion particulates."
        else:
            narrative = "Unusual combination of sensor values detected outside baseline distribution."

        return {
            "temperature_level": temp_eval,
            "smoke_level": smoke_eval,
            "humidity_level": hum_eval,
            "co2_level": co2_eval,
            "air_quality_level": aq_eval,
            "soil_moisture_level": "DRY" if self.soil_moisture < 25 else "NORMAL",
            "narrative": narrative,
            "model_status": status,
            "likely_event": event
        }

    # ========================================================
    # GEOGRAPHIC & ECOLOGICAL METRICS
    # ========================================================

    @property
    def latitude(self):
        if self.deployed_latitude is not None:
            return self.deployed_latitude
        # Deterministic simulation placement in Cascade Biosphere Reserve Transect
        return round(45.3820 + (self.y - 10) * 0.0065, 6)

    @property
    def longitude(self):
        if self.deployed_longitude is not None:
            return self.deployed_longitude
        return round(-121.7530 + (self.x - 10) * 0.0090, 6)

    @property
    def zone(self):
        if self.y >= 14:
            return "North Ridge Transect"
        elif self.y <= 6:
            return "South Lowland Scrub"
        elif self.x <= 6:
            return "West Wetland Sanctuary"
        elif self.x >= 14:
            return "East Alpine Forest"
        return "Central Riparian River Basin"

    @property
    def simple_name(self):
        digits = "".join(ch for ch in str(self.agent_id) if ch.isdigit())
        idx = int(digits) if digits else 1
        return f"Drone {idx}"

    @property
    def agent_type(self):
        digits = "".join(ch for ch in str(self.agent_id) if ch.isdigit())
        idx = int(digits) if digits else 1
        types = [
            "Canopy Thermal Drone",
            "Atmospheric Sentry Node",
            "Riparian Hydrology Sensor",
            "Sub-Canopy Soil Probe",
            "Autonomous Mesh Relay"
        ]
        return types[(idx - 1) % len(types)]

    def get_assignment(self):
        if self.status == "FAILED":
            return "Offline — Telemetry Link Lost (Awaiting Mesh Recovery)"

        event = self.ai_result.get("event") if self.ai_result else "None"
        status = self.ai_result.get("status") if self.ai_result else "NORMAL"

        if status == "ANOMALY":
            if event == "FIRE":
                return "Active Hazard: Thermal Boundary Containment & Combustion Profiling"
            elif event == "POLLUTION":
                return "Active Hazard: Particulate Plume Dispersion & CO2 Trajectory"
            elif event == "EXTREME_HEAT":
                return "Active Hazard: Canopy Micro-Climate Thermal Stress Monitoring"
            return "Active Hazard: Sensor Inconsistency Anomaly Investigation"

        if self.battery < 30:
            return "Conserving Power: Low-Frequency Passive Ecological Sentry"

        t = self.agent_type
        if "Drone" in t:
            return "Autonomous Forest Canopy Transect Patrol"
        elif "Atmospheric" in t:
            return "Continuous Greenhouse Gas & Ambient Aerosol Profiling"
        elif "Hydrology" in t:
            return "Riparian Stream Basin & Watershed Hydrological Flux"
        elif "Soil" in t:
            return "Sub-Canopy Soil Moisture & Microbial Thermal Survey"
        return "Decentralized P2P Mesh Routing & Consensus Aggregation"

    @property
    def risk_score(self):
        if self.status == "FAILED":
            return 0
        score = 8.0
        if self.temperature > 35:
            score += min(35.0, (self.temperature - 35) * 3.5)
        if self.smoke > 0.2:
            score += min(40.0, (self.smoke - 0.2) * 60.0)
        if self.co2 > 600:
            score += min(20.0, (self.co2 - 600) / 25.0)
        if self.air_quality > 80:
            score += min(20.0, (self.air_quality - 80) / 4.0)
        if self.ai_result and self.ai_result.get("status") == "ANOMALY":
            score = max(score, (self.ai_result.get("score", 0.8) * 100))
        return min(100, int(score))

    # ========================================================
    # AGENT INFORMATION
    # ========================================================

    def get_info(self):
        from datetime import datetime

        return {
            "id": self.agent_id,
            "name": self.simple_name,
            "position": (self.x, self.y),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "agent_type": self.agent_type,
            "assignment": self.get_assignment(),
            "zone": self.zone,
            "risk_score": self.risk_score,
            "battery": self.battery,
            "health": self.health,
            "connectivity": self.connectivity,
            "reliability": self.reliability,
            "status": self.status,
            "readings": self.get_readings(),
            "neighbors": [
                neighbor.agent_id
                for neighbor in self.neighbors
            ],
            "ai_result": self.ai_result,
            "ai_explanation": self.get_ai_explanation(),
            "messages_received": len(self.messages),
            "observations_count": getattr(self, "observations_count", 48),
            "last_seen": datetime.utcnow().isoformat() + "Z",
            "simulation_mode": True,
            "simulation_area": self.deployment_area_label or "Cascade Biosphere Reserve — Demonstration Transect",
            "deployed": self.deployed_latitude is not None and self.deployed_longitude is not None,
        }