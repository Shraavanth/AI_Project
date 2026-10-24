import sys
import os
import time
import json
import asyncio
import random
import math
from datetime import datetime
from typing import Optional, List, Dict, Any

# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from simulation.environment_model import EnvironmentalModel
from backend.database import SessionLocal, init_db
from backend.models import (
    AgentRecord,
    EnvironmentalReadingRecord,
    EnvironmentalEventRecord,
    AgentDeploymentRecord,
    DeploymentSiteRecord,
    ConsensusRecord,
    NetworkReorganizationRecord,
    SystemAuditLogRecord
)
from backend.websocket_manager import ws_manager


class SimulationService:

    def __init__(self):
        init_db()
        self.model = EnvironmentalModel(
            width=20,
            height=20,
            num_agents=20
        )
        self.last_event = None
        self.last_recovery = None
        self.deployment_site = None
        self.last_communications = []
        self.last_resolution_report = None
        saved_deployments = {}

        # Check if database already has persisted state
        db = SessionLocal()
        saved_agents = []
        try:
            saved_agents = db.query(AgentRecord).all()
            latest_event = db.query(EnvironmentalEventRecord).order_by(EnvironmentalEventRecord.timestamp.desc()).first()
            if latest_event:
                self.last_event = {
                    "event_id": latest_event.event_id,
                    "event_type": latest_event.event_type,
                    "location": {"x": latest_event.center_x, "y": latest_event.center_y},
                    "radius": latest_event.radius,
                    "severity": latest_event.severity,
                    "affected_count": latest_event.affected_count,
                    "detecting_count": latest_event.detecting_count,
                    "consensus_state": latest_event.consensus_state,
                    "confidence": latest_event.confidence,
                    "status": latest_event.status,
                    "affected_agents": json.loads(latest_event.affected_agents_json or "[]"),
                    "timestamp": latest_event.timestamp.isoformat()
                }

            latest_rec = db.query(NetworkReorganizationRecord).order_by(NetworkReorganizationRecord.timestamp.desc()).first()
            if latest_rec:
                self.last_recovery = {
                    "failed_agent": latest_rec.failed_agent_id,
                    "connections_removed": latest_rec.connections_removed,
                    "connections_created": latest_rec.connections_created,
                    "recovery_time_ms": latest_rec.recovery_time_ms,
                    "active_agents": latest_rec.active_agents_count,
                    "network_connected": latest_rec.network_connected,
                    "timestamp": latest_rec.timestamp.isoformat()
                }
            site = db.query(DeploymentSiteRecord).filter_by(id=1).first()
            if site:
                self.deployment_site = {
                    "latitude": site.latitude,
                    "longitude": site.longitude,
                    "radius_km": site.radius_km,
                    "area_label": site.area_label,
                    "updated_at": site.updated_at.isoformat() if site.updated_at else None,
                }
            saved_deployments = {
                deployment.agent_id: deployment
                for deployment in db.query(AgentDeploymentRecord).all()
            }
        except Exception as e:
            print(f"[DB INIT READ ERROR] {e}")
        finally:
            db.close()

        if saved_agents and len(saved_agents) > 0:
            # Reconstruct model from persistent DB records
            from agents.monitoring_agent import MonitoringAgent
            self.model.agents = []
            self.model.network.graph.clear()
            for r in saved_agents:
                db_read = SessionLocal()
                latest_reading = None
                try:
                    latest_reading = db_read.query(EnvironmentalReadingRecord).filter_by(agent_id=r.agent_id).order_by(EnvironmentalReadingRecord.timestamp.desc()).first()
                except Exception:
                    pass
                finally:
                    db_read.close()

                temp = latest_reading.temperature if latest_reading else 28.0
                hum = latest_reading.humidity if latest_reading else 60.0
                smk = latest_reading.smoke if latest_reading else 0.10
                co2_val = latest_reading.co2 if latest_reading else 420.0
                aq = latest_reading.air_quality if latest_reading else 50.0
                sm = latest_reading.soil_moisture if latest_reading else 55.0

                agent = MonitoringAgent(
                    agent_id=r.agent_id,
                    x=r.x,
                    y=r.y,
                    temperature=temp,
                    humidity=hum,
                    smoke=smk,
                    co2=co2_val,
                    air_quality=aq,
                    soil_moisture=sm,
                    battery=r.battery
                )
                agent.status = r.status
                deployment = saved_deployments.get(r.agent_id)
                if deployment:
                    agent.deployed_latitude = deployment.latitude
                    agent.deployed_longitude = deployment.longitude
                    agent.deployment_area_label = deployment.area_label
                self.model.agents.append(agent)
                self.model.network.add_agent(agent)

            # Reconnect communication mesh
            self.model.rebuild_network(max_distance=4)
            self.model.analyze_environment()

            self.log_audit(
                category="NETWORK",
                title="System Resumed from Database",
                message=f"Environmental Multi-Agent System restored {len(self.model.agents)} agents from persistent database storage.",
                agent_id=None
            )
        else:
            self.model.create_demo_layout()
            self._sync_all_agents_to_db()
            self.log_audit(
                category="NETWORK",
                title="System Initialized",
                message="Environmental Multi-Agent System booted with 20 active agents in grid topology.",
                agent_id=None
            )

    # ========================================================
    # AUDIT LOGGING HELPER
    # ========================================================

    def log_audit(self, category: str, title: str, message: str, agent_id: str = None, details: dict = None):
        db = SessionLocal()
        try:
            log_entry = SystemAuditLogRecord(
                category=category,
                agent_id=agent_id,
                title=title,
                message=message,
                details_json=json.dumps(details or {}),
                timestamp=datetime.utcnow()
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[DB LOG ERROR] {e}")
        finally:
            db.close()

    def _sync_all_agents_to_db(self):
        db = SessionLocal()
        try:
            for agent in self.model.agents:
                # Update or create AgentRecord
                record = db.query(AgentRecord).filter_by(agent_id=agent.agent_id).first()
                if not record:
                    record = AgentRecord(
                        agent_id=agent.agent_id,
                        x=agent.x,
                        y=agent.y,
                        status=agent.status,
                        battery=agent.battery,
                        health=agent.health,
                        connectivity=agent.connectivity,
                        reliability=agent.reliability
                    )
                    db.add(record)
                else:
                    record.x = agent.x
                    record.y = agent.y
                    record.status = agent.status
                    record.battery = agent.battery
                    record.health = agent.health
                    record.connectivity = agent.connectivity
                    record.reliability = agent.reliability
                    record.updated_at = datetime.utcnow()

                # Save reading snapshot
                reading = EnvironmentalReadingRecord(
                    agent_id=agent.agent_id,
                    temperature=round(agent.temperature, 2),
                    humidity=round(agent.humidity, 2),
                    smoke=round(agent.smoke, 3),
                    co2=round(agent.co2, 1),
                    air_quality=round(agent.air_quality, 1),
                    soil_moisture=round(agent.soil_moisture, 1),
                    ai_status=agent.ai_result.get("status", "NORMAL") if agent.ai_result else "NORMAL",
                    event_classified=agent.ai_result.get("event", "None") if agent.ai_result else "None",
                    anomaly_score=round(agent.ai_result.get("score", 0.0), 4) if agent.ai_result else 0.0,
                    timestamp=datetime.utcnow()
                )
                db.add(reading)

            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[DB SYNC ERROR] {e}")
        finally:
            db.close()

    # ========================================================
    # STATUS & SYSTEM OVERVIEW
    # ========================================================

    def get_status(self):
        stats = self.model.get_statistics()
        stats["last_event"] = self.last_event
        stats["last_recovery"] = self.last_recovery
        return stats

    # ========================================================
    # AGENT QUERIES & CRUD
    # ========================================================

    def get_agents(self):
        agents = []
        for agent in self.model.agents:
            agents.append(agent.get_info())
        return agents

    def get_agent(self, agent_id: str):
        agent = self.model.get_agent(agent_id)
        if not agent:
            return None
        return agent.get_info()

    def get_deployment(self):
        return self.deployment_site

    def deploy_agents(self, latitude: float, longitude: float, radius_km: float, area_label: str):
        agents = self.model.agents
        if not agents:
            raise ValueError("There are no agents available to deploy.")

        label = area_label.strip()
        if not label:
            raise ValueError("A deployment area name is required.")

        deployment_by_id = {}
        longitude_scale = max(abs(math.cos(math.radians(latitude))), 0.01)
        golden_angle = math.pi * (3 - math.sqrt(5))
        agent_count = len(agents)

        for index, agent in enumerate(agents):
            distance_km = radius_km * 0.9 * math.sqrt((index + 0.5) / agent_count)
            angle = index * golden_angle
            north_offset = distance_km * math.sin(angle)
            east_offset = distance_km * math.cos(angle)
            agent_latitude = round(max(
                -90.0,
                min(90.0, latitude + north_offset / 111.32)
            ), 6)
            agent_longitude = round((
                longitude + east_offset / (111.32 * longitude_scale) + 180.0
            ) % 360.0 - 180.0, 6)
            deployment_by_id[agent.agent_id] = (
                agent_latitude,
                agent_longitude,
            )

        db = SessionLocal()
        try:
            site = db.query(DeploymentSiteRecord).filter_by(id=1).first()
            if site is None:
                site = DeploymentSiteRecord(id=1)
                db.add(site)
            site.latitude = latitude
            site.longitude = longitude
            site.radius_km = radius_km
            site.area_label = label
            site.updated_at = datetime.utcnow()

            existing_records = {
                record.agent_id: record
                for record in db.query(AgentDeploymentRecord).all()
            }
            for agent_id, (agent_latitude, agent_longitude) in deployment_by_id.items():
                record = existing_records.get(agent_id)
                if record is None:
                    record = AgentDeploymentRecord(agent_id=agent_id)
                    db.add(record)
                record.latitude = agent_latitude
                record.longitude = agent_longitude
                record.area_label = label

            for stale_agent_id in set(existing_records) - set(deployment_by_id):
                db.delete(existing_records[stale_agent_id])

            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        for agent in agents:
            agent_latitude, agent_longitude = deployment_by_id[agent.agent_id]
            agent.deployed_latitude = agent_latitude
            agent.deployed_longitude = agent_longitude
            agent.deployment_area_label = label

        self.deployment_site = {
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": radius_km,
            "area_label": label,
            "updated_at": datetime.utcnow().isoformat(),
        }
        self.log_audit(
            category="AGENTS",
            title="Agent Fleet Deployed",
            message=f"{agent_count} agents deployed around {label} within a {radius_km:.1f} km radius.",
            details={
                "latitude": latitude,
                "longitude": longitude,
                "radius_km": radius_km,
                "agent_count": agent_count,
            },
        )

        return {
            "success": True,
            "deployment": self.deployment_site,
            "deployed_count": agent_count,
            "agents": self.get_agents(),
        }

    def add_agent(self, agent_data: dict):
        agent_id = agent_data.get("id") or f"A{len(self.model.agents) + 1}"
        agent = self.model.add_custom_agent(
            agent_id=agent_id,
            x=agent_data.get("x", 0),
            y=agent_data.get("y", 0),
            temperature=agent_data.get("temperature", 28.0),
            humidity=agent_data.get("humidity", 60.0),
            smoke=agent_data.get("smoke", 0.10),
            co2=agent_data.get("co2", 420.0),
            air_quality=agent_data.get("air_quality", 50.0),
            soil_moisture=agent_data.get("soil_moisture", 55.0),
            battery=agent_data.get("battery", 100)
        )
        self._sync_all_agents_to_db()
        self.log_audit(
            category="AGENTS",
            title=f"Agent Added: {agent.agent_id}",
            message=f"New agent {agent.agent_id} deployed at coordinates ({agent.x}, {agent.y}).",
            agent_id=agent.agent_id
        )
        if self.deployment_site:
            self.deploy_agents(
                latitude=self.deployment_site["latitude"],
                longitude=self.deployment_site["longitude"],
                radius_km=self.deployment_site["radius_km"],
                area_label=self.deployment_site["area_label"],
            )
        return agent.get_info()

    def move_agent(self, agent_id: str, x: int, y: int):
        agent = self.model.move_agent(agent_id, x, y)
        if not agent:
            return None
        self._sync_all_agents_to_db()
        self.log_audit(
            category="AGENTS",
            title=f"Agent Moved: {agent_id}",
            message=f"Agent {agent_id} relocated to ({x}, {y}). Network mesh reconnected.",
            agent_id=agent_id
        )
        return agent.get_info()

    def move_agent_direction(self, agent_id: str, direction: str):
        agent = self.model.move_agent_direction(agent_id, direction)
        if not agent:
            return None
        self._sync_all_agents_to_db()
        self.log_audit(
            category="AGENTS",
            title=f"Agent Moved {direction}: {agent_id}",
            message=f"Agent {agent_id} navigated {direction} to ({agent.x}, {agent.y}).",
            agent_id=agent_id
        )
        return agent.get_info()

    def step_patrol(self):
        stats = self.model.step_patrol()
        self._sync_all_agents_to_db()
        return {
            "success": True,
            "statistics": stats,
            "agents": self.get_agents()
        }


    def remove_agent(self, agent_id: str):
        success = self.model.remove_agent(agent_id)
        if success:
            db = SessionLocal()
            try:
                db.query(AgentRecord).filter_by(agent_id=agent_id).delete()
                db.query(AgentDeploymentRecord).filter_by(agent_id=agent_id).delete()
                db.commit()
            except Exception:
                db.rollback()
            finally:
                db.close()

            self.log_audit(
                category="AGENTS",
                title=f"Agent Removed: {agent_id}",
                message=f"Agent {agent_id} decommissioned and removed from active monitoring topology.",
                agent_id=agent_id
            )
        return success

    def fail_agent(self, agent_id: str):
        agent = self.model.fail_agent(agent_id)
        if not agent:
            return None
        self._sync_all_agents_to_db()
        self.log_audit(
            category="FAILURES",
            title=f"Agent Failure: {agent_id}",
            message=f"Hardware/comm link failure detected on agent {agent_id}. Agent is offline.",
            agent_id=agent_id,
            details={"position": [agent.x, agent.y]}
        )
        return agent.get_info()

    def restore_agent(self, agent_id: str):
        agent = self.model.restore_agent(agent_id)
        if not agent:
            return None
        self._sync_all_agents_to_db()
        self.log_audit(
            category="RECOVERY",
            title=f"Agent Restored: {agent_id}",
            message=f"Agent {agent_id} restored to full active operational state and re-established peer links.",
            agent_id=agent_id
        )
        return agent.get_info()

    def update_agent_sensors(self, agent_id: str, readings: dict):
        agent = self.model.update_agent_sensors(agent_id, readings)
        if not agent:
            return None
        self._sync_all_agents_to_db()
        self.log_audit(
            category="ANOMALIES" if agent.ai_result and agent.ai_result.get("status") == "ANOMALY" else "AGENTS",
            title=f"Sensor Override: {agent_id}",
            message=f"Manual sensor update on {agent_id}: Temp={agent.temperature}°C, Smoke={agent.smoke}, Status={agent.ai_result.get('status')}.",
            agent_id=agent_id,
            details=readings
        )
        return agent.get_info()

    # ========================================================
    # EVENT TRIGGER WORKFLOWS (FIRE, POLLUTION, EXTREME HEAT)
    # ========================================================

    def trigger_event(
        self,
        event_type: str,
        center_x: int = 10,
        center_y: int = 10,
        radius: int = 3,
        target_agent_id: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        zone_name: Optional[str] = None
    ):
        start_time = time.time()

        # Sector zone coordinates mapping
        sector_coords = {
            "North Ridge Transect": (10, 16),
            "South Lowland Scrub": (10, 4),
            "West Wetland Sanctuary": (4, 10),
            "East Alpine Forest": (16, 10),
            "Central Riparian River Basin": (10, 10),
        }

        # 1. Resolve targeted area coordinates
        if target_agent_id:
            target_agent = self.model.get_agent(target_agent_id)
            if target_agent:
                center_x = target_agent.x
                center_y = target_agent.y
        elif latitude is not None and longitude is not None:
            center_y = max(0, min(20, int(round(10 + (latitude - 45.3820) / 0.0065))))
            center_x = max(0, min(20, int(round(10 + (longitude - (-121.7530)) / 0.0090))))
        elif zone_name and zone_name in sector_coords:
            center_x, center_y = sector_coords[zone_name]

        # 2. Trigger hazard conditions across environmental model
        if latitude is not None and longitude is not None:
            # Check geographic proximity for deployed agents
            geo_radius_km = max(0.8, radius * 0.65)
            geo_affected = []
            for ag in self.model.agents:
                if ag.latitude is not None and ag.longitude is not None:
                    d_lat = (ag.latitude - latitude) * 111.32
                    scale = max(0.01, math.cos(math.radians(latitude)))
                    d_lng = (ag.longitude - longitude) * 111.32 * scale
                    dist = math.sqrt(d_lat * d_lat + d_lng * d_lng)
                    if dist <= geo_radius_km:
                        geo_affected.append(ag)
            if geo_affected:
                for ag in geo_affected:
                    if event_type == "FIRE":
                        ag.temperature = round(random.uniform(43.5, 49.0), 1)
                        ag.humidity = round(random.uniform(12.0, 24.0), 1)
                        ag.smoke = round(random.uniform(0.72, 0.98), 2)
                        ag.co2 = round(random.uniform(880.0, 1250.0), 1)
                        ag.soil_moisture = round(random.uniform(10.0, 25.0), 1)
                    elif event_type == "POLLUTION":
                        ag.co2 = round(random.uniform(900.0, 1400.0), 1)
                        ag.air_quality = round(random.uniform(150.0, 250.0), 1)
                        ag.smoke = round(random.uniform(0.35, 0.65), 2)
                    else:
                        ag.temperature = round(random.uniform(42.5, 48.5), 1)
                        ag.humidity = round(random.uniform(15.0, 28.0), 1)
                affected = geo_affected
                severity = "CRITICAL" if event_type == "FIRE" else "HIGH" if event_type == "POLLUTION" else "MEDIUM"
            else:
                if event_type == "FIRE":
                    affected = self.model.create_fire_event(center_x, center_y, radius)
                elif event_type == "POLLUTION":
                    affected = self.model.create_pollution_event(center_x, center_y, radius)
                else:
                    affected = self.model.create_extreme_heat_event(center_x, center_y, radius)
                severity = "HIGH"
        elif event_type == "FIRE":
            affected = self.model.create_fire_event(center_x, center_y, radius)
            severity = "CRITICAL"
        elif event_type == "POLLUTION":
            affected = self.model.create_pollution_event(center_x, center_y, radius)
            severity = "HIGH"
        elif event_type == "EXTREME_HEAT":
            affected = self.model.create_extreme_heat_event(center_x, center_y, radius)
            severity = "MEDIUM"
        else:
            affected = self.model.create_fire_event(center_x, center_y, radius)
            severity = "HIGH"

        # 3. Local AI Analysis on each active agent
        self.model.analyze_environment()

        # 4. Broadcast alerts among affected agents
        self.model.broadcast_alerts()

        # 5. Decentralized Consensus
        consensus = self.model.determine_consensus()

        detecting_agents = [
            a.agent_id for a in self.model.get_active_agents()
            if a.ai_result and a.ai_result.get("event") == event_type
        ]

        event_id = f"EVT-{int(time.time())}"
        lat = latitude if latitude is not None else round(45.3820 + (center_y - 10) * 0.0065, 6)
        lng = longitude if longitude is not None else round(-121.7530 + (center_x - 10) * 0.0090, 6)
        
        computed_zone = (
            zone_name if zone_name
            else "North Ridge Transect" if center_y >= 14
            else "South Lowland Scrub" if center_y <= 6
            else "West Wetland Sanctuary" if center_x <= 6
            else "East Alpine Forest" if center_x >= 14
            else "Central Riparian River Basin"
        )

        # 6. Generate detailed P2P communication trace packets using simple friendly names
        communications = []
        msg_idx = 1
        now_ts = datetime.utcnow().strftime("%H:%M:%S")

        # Step 1: Anomaly evaluations on detecting agents
        for agent in affected:
            if agent.status != "ACTIVE":
                continue
            s_name = getattr(agent, "simple_name", agent.agent_id)
            readings = agent.get_readings()
            narrative = f"Temp={readings['temperature']}°C, Smoke={readings['smoke']}, CO2={readings['co2']}ppm"
            score_val = agent.ai_result.get("score", 0.88) if agent.ai_result else 0.88
            communications.append({
                "id": f"PKT-{msg_idx:03d}",
                "timestamp": now_ts,
                "step": 1,
                "sender_id": s_name,
                "receiver_id": "Onboard AI",
                "type": "ANOMALY_EVALUATION",
                "hazard_type": event_type,
                "content": f"{s_name} flagged {event_type} anomaly ({narrative}).",
                "vote": "ANOMALY_CONFIRMED",
                "confidence": round(score_val, 2)
            })
            msg_idx += 1

        # Step 2: Peer-to-Peer Alert Broadcasts to active proximate neighbors
        for agent in affected:
            s_name = getattr(agent, "simple_name", agent.agent_id)
            for neighbor in agent.neighbors:
                if neighbor.status != "ACTIVE":
                    continue
                n_name = getattr(neighbor, "simple_name", neighbor.agent_id)
                communications.append({
                    "id": f"PKT-{msg_idx:03d}",
                    "timestamp": now_ts,
                    "step": 2,
                    "sender_id": s_name,
                    "receiver_id": n_name,
                    "type": "ENVIRONMENTAL_ALERT",
                    "hazard_type": event_type,
                    "content": f"{s_name} -> {n_name}: Transmitted {event_type} alert packet. Requesting verification quorum.",
                    "vote": "ALERT_TRANSMITTED",
                    "confidence": round(consensus.get("confidence", 0.85), 2)
                })
                msg_idx += 1

        # Step 3: Neighbor Consensus Voting
        for agent in self.model.get_active_agents():
            contacted_by = [n for n in agent.neighbors if n in affected]
            if contacted_by:
                a_name = getattr(agent, "simple_name", agent.agent_id)
                target_peer = contacted_by[0]
                tp_name = getattr(target_peer, "simple_name", target_peer.agent_id)
                is_agreeing = agent in affected or (agent.ai_result and agent.ai_result.get("event") == event_type)
                vote_status = "AGREE_HAZARD" if is_agreeing else "NEUTRAL_CORROBORATION"
                conf_score = 0.92 if is_agreeing else 0.55
                communications.append({
                    "id": f"PKT-{msg_idx:03d}",
                    "timestamp": now_ts,
                    "step": 3,
                    "sender_id": a_name,
                    "receiver_id": tp_name,
                    "type": "CONSENSUS_VOTE",
                    "hazard_type": event_type,
                    "content": f"{a_name} -> {tp_name}: Returned vote {vote_status} based on local sensor evidence.",
                    "vote": vote_status,
                    "confidence": conf_score
                })
                msg_idx += 1

        # Step 4: Quorum Consensus Commit
        first_rep = getattr(affected[0], "simple_name", "Drone 1") if affected else "Drone 1"
        communications.append({
            "id": f"PKT-{msg_idx:03d}",
            "timestamp": now_ts,
            "step": 4,
            "sender_id": "P2P Quorum",
            "receiver_id": "Fleet Broadcast",
            "type": "CONSENSUS_COMMIT",
            "hazard_type": event_type,
            "content": f"Neighbor consensus confirmed {event_type} hazard with {int(consensus.get('confidence', 0.85)*100)}% confidence across {len(affected)} nodes. {first_rep} coordinating response.",
            "vote": "HAZARD_VERIFIED",
            "confidence": round(consensus.get("confidence", 0.85), 2)
        })

        self.last_communications = communications

        self.last_event = {
            "event_id": event_id,
            "event_type": event_type,
            "location": {"x": center_x, "y": center_y},
            "latitude": lat,
            "longitude": lng,
            "geo_radius_meters": radius * 650,
            "zone_name": computed_zone,
            "radius": radius,
            "severity": severity,
            "affected_count": len(affected),
            "detecting_count": len(detecting_agents),
            "consensus_state": "CONFIRMED" if consensus.get("consensus") else "UNCERTAIN",
            "confidence": consensus.get("confidence", 0.0),
            "status": "ACTIVE",
            "affected_agents": [a.agent_id for a in affected],
            "communications": communications,
            "resolution_report": None,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Save to database
        db = SessionLocal()
        try:
            evt_record = EnvironmentalEventRecord(
                event_id=event_id,
                event_type=event_type,
                center_x=center_x,
                center_y=center_y,
                radius=radius,
                severity=severity,
                affected_count=len(affected),
                detecting_count=len(detecting_agents),
                consensus_state="CONFIRMED" if consensus.get("consensus") else "UNCERTAIN",
                confidence=consensus.get("confidence", 0.0),
                status="ACTIVE",
                affected_agents_json=json.dumps([a.agent_id for a in affected]),
                timestamp=datetime.utcnow()
            )
            db.add(evt_record)

            cons_record = ConsensusRecord(
                event_id=event_id,
                event_type=event_type,
                consensus_reached=consensus.get("consensus", False),
                confidence=consensus.get("confidence", 0.0),
                total_voters=len(self.model.get_active_agents()),
                agreeing_voters=len(detecting_agents),
                evidence_summary=f"{len(detecting_agents)} of {len(self.model.get_active_agents())} agents reached neighbor consensus on {event_type}",
                timestamp=datetime.utcnow()
            )
            db.add(cons_record)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[DB EVENT ERROR] {e}")
        finally:
            db.close()

        self._sync_all_agents_to_db()

        # Audit log entries
        self.log_audit(
            category="EVENT",
            title=f"Incident Detected: {event_type}",
            message=f"{event_type} incident triggered at ({center_x}, {center_y}) in {computed_zone} radius {radius}. {len(affected)} agents in zone.",
            agent_id=affected[0].agent_id if affected else None,
            details=self.last_event
        )

        self.log_audit(
            category="CONSENSUS",
            title=f"Consensus: {event_type} Confirmed",
            message=f"Local neighbor consensus confirmed {event_type} with confidence {int(consensus.get('confidence', 0)*100)}%.",
            details=consensus
        )

        return self.last_event

    def create_fire(self):
        return self.trigger_event("FIRE", 10, 10, 3)

    def create_pollution(self):
        return self.trigger_event("POLLUTION", 10, 10, 3)

    def create_extreme_heat(self):
        return self.trigger_event("EXTREME_HEAT", 10, 10, 3)

    def fail_fire_agent(self):
        fire_agents = self.model.get_fire_agents()
        if not fire_agents:
            return {
                "success": False,
                "message": "No active FIRE-detecting agent available."
            }

        agent = fire_agents[0]
        return self.fail_agent(agent.agent_id)

    # ========================================================
    # NETWORK TOPOLOGY & SELF-ORGANIZING RECOVERY
    # ========================================================

    def get_network(self):
        graph = self.model.network.graph
        nodes = []
        for node_id in graph.nodes():
            agent = self.model.get_agent(node_id)
            if agent:
                nodes.append({
                    "id": agent.agent_id,
                    "x": agent.x,
                    "y": agent.y,
                    "status": agent.status,
                    "health": agent.health,
                    "event": agent.ai_result.get("event", "None") if agent.ai_result else "None",
                    "ai_status": agent.ai_result.get("status", "NORMAL") if agent.ai_result else "NORMAL"
                })

        links = []
        for u, v in graph.edges():
            links.append({"source": u, "target": v})

        return {
            "agents_count": len(nodes),
            "connections_count": len(links),
            "is_connected": self.model.network.is_connected(),
            "nodes": nodes,
            "links": links,
            "last_recovery": self.last_recovery
        }

    def recover_network(self):
        start_time = time.time()
        before_links_count = self.model.network.graph.number_of_edges()

        # Identify failed agents
        failed_agents = self.model.get_failed_agents()
        failed_id = failed_agents[0].agent_id if failed_agents else "None"

        # Reorganize and self-heal network
        self.model.rebuild_network(max_distance=4)
        after_links_count = self.model.network.graph.number_of_edges()

        recovery_ms = int((time.time() - start_time) * 1000) + 12

        self.last_recovery = {
            "failed_agent": failed_id,
            "connections_removed": max(0, before_links_count - after_links_count) if before_links_count > after_links_count else 4,
            "connections_created": max(0, after_links_count - before_links_count) if after_links_count >= before_links_count else 5,
            "recovery_time_ms": recovery_ms,
            "active_agents": len(self.model.get_active_agents()),
            "network_connected": self.model.network.is_connected(),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Save to DB
        db = SessionLocal()
        try:
            rec_log = NetworkReorganizationRecord(
                failed_agent_id=failed_id,
                connections_removed=self.last_recovery["connections_removed"],
                connections_created=self.last_recovery["connections_created"],
                active_agents_count=self.last_recovery["active_agents"],
                network_connected=self.last_recovery["network_connected"],
                recovery_time_ms=recovery_ms,
                timestamp=datetime.utcnow()
            )
            db.add(rec_log)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[DB RECOVERY LOG ERROR] {e}")
        finally:
            db.close()

        self._sync_all_agents_to_db()

        self.log_audit(
            category="RECOVERY",
            title="Self-Organizing Network Recovery Complete",
            message=f"Autonomous topology reorganization completed in {recovery_ms}ms. Connectivity restored={self.last_recovery['network_connected']}.",
            agent_id=failed_id,
            details=self.last_recovery
        )

        return {
            "success": True,
            "recovery": self.last_recovery,
            "network": self.get_network()
        }

    # ========================================================
    # RESET
    # ========================================================

    def reset(self):
        db = SessionLocal()
        try:
            db.query(AgentRecord).delete()
            db.query(AgentDeploymentRecord).delete()
            db.query(DeploymentSiteRecord).filter_by(id=1).delete()
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[DB RESET ERROR] {e}")
        finally:
            db.close()

        self.model = EnvironmentalModel(
            width=20,
            height=20,
            num_agents=20
        )
        self.model.create_demo_layout()
        self.last_event = None
        self.last_recovery = None
        self.deployment_site = None
        self._sync_all_agents_to_db()

        self.log_audit(
            category="NETWORK",
            title="System Simulation Reset",
            message="Environment baseline reset to default 20-agent layout.",
            agent_id=None
        )

        return self.get_status()

    # ========================================================
    # HISTORY & ANALYTICS QUERIES
    # ========================================================

    def get_events(self):
        db = SessionLocal()
        try:
            records = db.query(EnvironmentalEventRecord).order_by(EnvironmentalEventRecord.timestamp.desc()).limit(50).all()
            events = []
            for r in records:
                lat = round(45.3820 + (r.center_y - 10) * 0.0065, 6)
                lng = round(-121.7530 + (r.center_x - 10) * 0.0090, 6)
                zone_name = (
                    "North Ridge Transect" if r.center_y >= 14
                    else "South Lowland Scrub" if r.center_y <= 6
                    else "West Wetland Sanctuary" if r.center_x <= 6
                    else "East Alpine Forest" if r.center_x >= 14
                    else "Central Riparian River Basin"
                )
                events.append({
                    "event_id": r.event_id,
                    "event_type": r.event_type,
                    "location": {"x": r.center_x, "y": r.center_y},
                    "latitude": lat,
                    "longitude": lng,
                    "geo_radius_meters": r.radius * 650,
                    "zone_name": zone_name,
                    "radius": r.radius,
                    "severity": r.severity,
                    "affected_count": r.affected_count,
                    "detecting_count": r.detecting_count,
                    "consensus_state": r.consensus_state,
                    "confidence": r.confidence,
                    "status": r.status,
                    "affected_agents": json.loads(r.affected_agents_json or "[]"),
                    "timestamp": r.timestamp.isoformat()
                })
            return events
        except Exception as e:
            print(f"[DB GET EVENTS ERROR] {e}")
            return [self.last_event] if self.last_event else []
        finally:
            db.close()

    def get_event_communications(self, event_id: Optional[str] = None):
        return self.last_communications

    def recharge_fleet(self):
        for agent in self.model.agents:
            if agent.status == "ACTIVE":
                agent.battery = 100
        self._sync_all_agents_to_db()

        self.log_audit(
            category="AGENTS",
            title="Fleet Maintenance & Solar Recharge Completed",
            message="All autonomous monitoring agents replenished to 100% battery capacity and sensor arrays recalibrated.",
            details={"fleet_size": len(self.model.agents)}
        )

        return {
            "success": True,
            "message": "All 20 agents fully recharged and recalibrated to 100% capacity.",
            "agents": self.get_agents()
        }

    def resolve_event(self, event_id: str):
        db = SessionLocal()
        affected_ids = []
        event_record = None
        try:
            event_record = db.query(EnvironmentalEventRecord).filter_by(event_id=event_id).first()
            if event_record:
                event_record.status = "RESOLVED"
                try:
                    affected_ids = json.loads(event_record.affected_agents_json or "[]")
                except Exception:
                    affected_ids = []
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"[DB RESOLVE EVENT ERROR] {e}")
        finally:
            db.close()

        if self.last_event and self.last_event.get("event_id") == event_id:
            self.last_event["status"] = "RESOLVED"
            if not affected_ids:
                affected_ids = self.last_event.get("affected_agents", [])

        # Step 1-4: Coordinated resolution phases
        resolution_steps = [
            {
                "step": 1,
                "phase": "AUTONOMOUS_ALERT_CONVERGENCE",
                "description": f"Decentralized consensus validated hazard. Cluster coordinator selected among nearest active nodes: {', '.join(affected_ids[:3]) if affected_ids else 'Local Agents'}."
            },
            {
                "step": 2,
                "phase": "COORDINATED_SUPPRESSION_DISPATCH",
                "description": "Responding drone and sensor agents deployed localized aerosol cooling and high-efficiency particulate scrubbers across the hazard boundary."
            },
            {
                "step": 3,
                "phase": "REALTIME_TELEMETRY_DISSIPATION",
                "description": "Combustion particulates and ambient heat dissipated. Sensor readings verified returning to baseline (Temp: 28°C, Smoke: 0.08)."
            },
            {
                "step": 4,
                "phase": "POST_INCIDENT_HEALTH_ASSESSMENT",
                "description": "Hardware diagnostic sweep executed across all 20 nodes. Battery consumption and operating health audited."
            }
        ]

        # Calculate agent health & battery impact
        agent_health_breakdown = []
        total_battery_loss = 0

        for agent in self.model.agents:
            battery_before = agent.battery
            health_before = agent.health

            if agent.status == "FAILED":
                role = "FAILED_NODE"
                battery_delta = 0
                health_delta = 0
                thermal_wear = "OFFLINE"
                filter_status = "OFFLINE"
                diagnosis = "Node unresponsive or hardware severed."
            elif agent.agent_id in affected_ids:
                role = "PRIMARY_RESPONDER" if (affected_ids and agent.agent_id == affected_ids[0]) else "ZONE_DETECTOR"
                battery_delta = -random.randint(14, 22)
                agent.battery = max(15, agent.battery + battery_delta)
                health_delta = -random.randint(8, 15)
                thermal_wear = "MODERATE"
                filter_status = "PARTICULATE FOULING (CLEANING RECOMMENDED)"
                diagnosis = "Dispatched aerosol suppression & active cooling payload. Operating with post-hazard wear."
            elif any(n.agent_id in affected_ids for n in agent.neighbors):
                role = "RELAY_NEIGHBOR"
                battery_delta = -random.randint(5, 8)
                agent.battery = max(20, agent.battery + battery_delta)
                health_delta = -random.randint(2, 4)
                thermal_wear = "LOW"
                filter_status = "NOMINAL"
                diagnosis = "High-frequency radio transmitter draw while relaying neighbor consensus packets."
            else:
                role = "STANDBY_MONITOR"
                battery_delta = -1
                agent.battery = max(20, agent.battery + battery_delta)
                health_delta = 0
                thermal_wear = "NONE"
                filter_status = "OPTIMAL"
                diagnosis = "Autonomous baseline monitoring; no thermal or particulate stress incurred."

            total_battery_loss += abs(battery_delta)

            agent_health_breakdown.append({
                "agent_id": agent.agent_id,
                "name": getattr(agent, "simple_name", agent.agent_id),
                "role": role,
                "zone": agent.zone,
                "battery_before": battery_before,
                "battery_after": agent.battery,
                "battery_delta": battery_delta,
                "health_before": health_before,
                "health_after": agent.health,
                "health_delta": health_delta,
                "thermal_wear": thermal_wear,
                "filter_status": filter_status,
                "status": agent.status,
                "diagnosis": diagnosis,
                "readings": agent.get_readings()
            })

        # Normalize sensors of affected agents
        for agent in self.model.agents:
            if agent.status == "ACTIVE":
                agent.temperature = round(random.normalvariate(28, 1.8), 2)
                agent.humidity = round(random.normalvariate(60, 3.5), 2)
                agent.smoke = 0.08
                agent.co2 = 415.0
                agent.air_quality = 46.0
                agent.soil_moisture = 55.0
                agent.ai_result = {"status": "NORMAL", "event": "None", "score": 0.04}

        self._sync_all_agents_to_db()

        # Compute summary
        active_list = self.model.get_active_agents()
        avg_health = round(sum(a.health for a in active_list) / max(len(active_list), 1), 1)
        avg_battery = round(sum(a.battery for a in active_list) / max(len(active_list), 1), 1)
        needs_maint = any(a.battery < 65 or a.health < 80 for a in active_list)

        fleet_health_summary = {
            "average_health_score": avg_health,
            "average_battery_level": avg_battery,
            "total_responders_count": len(affected_ids),
            "total_battery_expended_pct": total_battery_loss,
            "maintenance_recommended": needs_maint
        }

        resolution_report = {
            "event_id": event_id,
            "resolved_at": datetime.utcnow().isoformat(),
            "status": "RESOLVED",
            "resolution_steps": resolution_steps,
            "fleet_health_summary": fleet_health_summary,
            "agent_health_breakdown": agent_health_breakdown
        }

        self.last_resolution_report = resolution_report
        if self.last_event and self.last_event.get("event_id") == event_id:
            self.last_event["resolution_report"] = resolution_report

        self.log_audit(
            category="EVENT",
            title=f"Incident Resolved & Fleet Health Audited: {event_id}",
            message=f"Environmental incident {event_id} neutralized by {len(affected_ids)} responding nodes. Fleet average health: {avg_health}%, battery: {avg_battery}%.",
            details=resolution_report
        )

        return {
            "success": True,
            "event_id": event_id,
            "status": "RESOLVED",
            "resolution_report": resolution_report,
            "fleet_health_summary": fleet_health_summary,
            "agent_health_breakdown": agent_health_breakdown
        }

    def acknowledge_event(self, event_id: str):
        db = SessionLocal()
        try:
            record = db.query(EnvironmentalEventRecord).filter_by(event_id=event_id).first()
            if record:
                record.status = "ACKNOWLEDGED"
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"[DB ACK EVENT ERROR] {e}")
        finally:
            db.close()

        if self.last_event and self.last_event.get("event_id") == event_id:
            self.last_event["status"] = "ACKNOWLEDGED"

        self.log_audit(
            category="EVENT",
            title=f"Incident Acknowledged: {event_id}",
            message=f"Environmental hazard alert {event_id} acknowledged. Sensor priority raised.",
            details={"event_id": event_id, "status": "ACKNOWLEDGED"}
        )

        return {"success": True, "event_id": event_id, "status": "ACKNOWLEDGED"}

    def restart_agent(self, agent_id: str):
        agent = self.model.get_agent(agent_id)
        if not agent:
            return None
        agent.status = "ACTIVE"
        agent.battery = max(agent.battery, 85)
        self.model.rebuild_network(max_distance=4)
        self._sync_all_agents_to_db()

        self.log_audit(
            category="AGENTS",
            title=f"Agent Rebooted: {agent_id}",
            message=f"Field node {agent_id} rebooted, calibrated, and re-integrated into communication mesh.",
            agent_id=agent_id
        )
        return agent.get_info()

    def get_history(self, category: str = "ALL", limit: int = 100):
        db = SessionLocal()
        try:
            query = db.query(SystemAuditLogRecord)
            if category and category != "ALL":
                query = query.filter(SystemAuditLogRecord.category == category.upper())
            records = query.order_by(SystemAuditLogRecord.timestamp.desc()).limit(limit).all()
            logs = []
            for r in records:
                logs.append({
                    "id": r.id,
                    "category": r.category,
                    "agent_id": r.agent_id,
                    "title": r.title,
                    "message": r.message,
                    "details": json.loads(r.details_json or "{}"),
                    "timestamp": r.timestamp.isoformat()
                })
            return logs
        except Exception as e:
            print(f"[DB GET HISTORY ERROR] {e}")
            return []
        finally:
            db.close()

    def get_analytics(self):
        db = SessionLocal()
        try:
            readings = db.query(EnvironmentalReadingRecord).order_by(EnvironmentalReadingRecord.timestamp.desc()).limit(200).all()

            # Group trends
            temp_trend = []
            smoke_trend = []
            co2_trend = []
            aq_trend = []

            for r in reversed(readings[:30]):
                t_str = r.timestamp.strftime("%H:%M:%S")
                temp_trend.append({"time": t_str, "agent": r.agent_id, "value": r.temperature})
                smoke_trend.append({"time": t_str, "agent": r.agent_id, "value": r.smoke})
                co2_trend.append({"time": t_str, "agent": r.agent_id, "value": r.co2})
                aq_trend.append({"time": t_str, "agent": r.agent_id, "value": r.air_quality})

            stats = self.model.get_statistics()
            reorganizations = db.query(NetworkReorganizationRecord).order_by(NetworkReorganizationRecord.timestamp.desc()).limit(10).all()

            rec_history = []
            for rec in reorganizations:
                rec_history.append({
                    "time": rec.timestamp.strftime("%H:%M:%S"),
                    "duration_ms": rec.recovery_time_ms,
                    "agent": rec.failed_agent_id
                })

            return {
                "temperature_trend": temp_trend,
                "smoke_trend": smoke_trend,
                "co2_trend": co2_trend,
                "air_quality_trend": aq_trend,
                "active_vs_failed": {
                    "active": stats["active_agents"],
                    "failed": stats["failed_agents"]
                },
                "event_distribution": {
                    "FIRE": stats.get("fire_detections", 0),
                    "POLLUTION": stats.get("pollution_detections", 0),
                    "EXTREME_HEAT": stats.get("extreme_heat_detections", 0),
                    "ANOMALIES": stats.get("anomalies", 0)
                },
                "recovery_history": rec_history,
                "total_connections": stats["connections"],
                "network_connected": stats["network_connected"]
            }
        except Exception as e:
            print(f"[DB GET ANALYTICS ERROR] {e}")
            stats = self.model.get_statistics()
            return {
                "temperature_trend": [],
                "smoke_trend": [],
                "co2_trend": [],
                "air_quality_trend": [],
                "active_vs_failed": {"active": stats["active_agents"], "failed": stats["failed_agents"]},
                "event_distribution": {"FIRE": 0, "POLLUTION": 0, "EXTREME_HEAT": 0, "ANOMALIES": 0},
                "recovery_history": [],
                "total_connections": stats["connections"],
                "network_connected": stats["network_connected"]
            }
        finally:
            db.close()


# ============================================================
# SINGLE SERVICE INSTANCE
# ============================================================

simulation_service = SimulationService()