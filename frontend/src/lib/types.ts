export interface Agent {
  id: string;
  name?: string;
  position: [number, number];
  latitude?: number;
  longitude?: number;
  agent_type?: string;
  assignment?: string;
  zone?: string;
  risk_score?: number;
  battery: number;
  health: number;
  connectivity: number;
  reliability: number;
  status: "ACTIVE" | "FAILED" | string;
  readings: {
    temperature: number;
    humidity: number;
    smoke: number;
    co2: number;
    air_quality: number;
    soil_moisture: number;
  };
  neighbors: string[];
  ai_result?: {
    status: "NORMAL" | "ANOMALY" | string;
    event: "None" | "FIRE" | "POLLUTION" | "EXTREME_HEAT" | "OTHER_ANOMALY" | string;
    score: number;
  } | null;
  ai_explanation?: {
    temperature_level: string;
    smoke_level: string;
    humidity_level: string;
    co2_level: string;
    air_quality_level: string;
    soil_moisture_level: string;
    narrative: string;
    model_status: string;
    likely_event: string;
  } | null;
  messages_received: number;
  observations_count?: number;
  last_seen?: string;
  simulation_mode?: boolean;
  simulation_area?: string;
  deployed?: boolean;
}

export interface AgentDeployment {
  latitude: number;
  longitude: number;
  radius_km: number;
  area_label: string;
  updated_at?: string | null;
}

export interface SystemStatus {
  total_agents: number;
  active_agents: number;
  failed_agents: number;
  anomalies: number;
  fire_detections: number;
  pollution_detections?: number;
  extreme_heat_detections?: number;
  connections: number;
  network_connected: boolean;
  last_event?: Incident | null;
  last_recovery?: RecoveryMetrics | null;
}

export interface EventTriggerParams {
  center_x?: number;
  center_y?: number;
  radius?: number;
  target_agent_id?: string;
  latitude?: number;
  longitude?: number;
  zone_name?: string;
}

export interface CommunicationPacket {
  id: string;
  timestamp: string;
  step: number;
  sender_id: string;
  receiver_id: string;
  type: string;
  hazard_type: string;
  content: string;
  vote?: string;
  confidence?: number;
}

export interface AgentHealthBreakdown {
  agent_id: string;
  role: string;
  zone: string;
  battery_before: number;
  battery_after: number;
  battery_delta: number;
  health_before: number;
  health_after: number;
  health_delta: number;
  thermal_wear: string;
  filter_status: string;
  status: string;
  diagnosis: string;
  readings?: Record<string, number>;
}

export interface ResolutionStep {
  step: number;
  phase: string;
  description: string;
}

export interface ResolutionReport {
  event_id: string;
  resolved_at: string;
  status: string;
  resolution_steps: ResolutionStep[];
  fleet_health_summary: {
    average_health_score: number;
    average_battery_level: number;
    total_responders_count: number;
    total_battery_expended_pct: number;
    maintenance_recommended: boolean;
  };
  agent_health_breakdown: AgentHealthBreakdown[];
}

export interface Incident {
  event_id: string;
  event_type: "FIRE" | "POLLUTION" | "EXTREME_HEAT" | "OTHER_ANOMALY" | string;
  location: { x: number; y: number };
  latitude?: number;
  longitude?: number;
  geo_radius_meters?: number;
  zone_name?: string;
  radius: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | string;
  affected_count: number;
  detecting_count: number;
  consensus_state: "CONFIRMED" | "UNCERTAIN" | string;
  confidence: number;
  status: "ACTIVE" | "RESOLVED" | "ACKNOWLEDGED" | string;
  affected_agents: string[];
  communications?: CommunicationPacket[];
  resolution_report?: ResolutionReport | null;
  timestamp: string;
}

export interface NetworkData {
  agents_count: number;
  connections_count: number;
  is_connected: boolean;
  nodes: Array<{
    id: string;
    x: number;
    y: number;
    status: string;
    health: number;
    event: string;
    ai_status: string;
  }>;
  links: Array<{
    source: string;
    target: string;
  }>;
  last_recovery?: RecoveryMetrics | null;
}

export interface RecoveryMetrics {
  failed_agent: string;
  connections_removed: number;
  connections_created: number;
  recovery_time_ms: number;
  active_agents: number;
  network_connected: boolean;
  timestamp: string;
}

export interface AuditLog {
  id: number;
  category: "EVENT" | "ANOMALIES" | "CONSENSUS" | "FAILURES" | "RECOVERY" | "NETWORK" | "AGENTS" | string;
  agent_id?: string | null;
  title: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}

export interface AnalyticsData {
  temperature_trend: Array<{ time: string; agent: string; value: number }>;
  smoke_trend: Array<{ time: string; agent: string; value: number }>;
  co2_trend: Array<{ time: string; agent: string; value: number }>;
  air_quality_trend: Array<{ time: string; agent: string; value: number }>;
  active_vs_failed: {
    active: number;
    failed: number;
  };
  event_distribution: Record<string, number>;
  recovery_history: Array<{ time: string; duration_ms: number; agent: string }>;
  total_connections: number;
  network_connected: boolean;
}

export const formatAgentName = (id?: string | null, name?: string | null): string => {
  if (name && name.trim()) return name;
  if (!id) return "Agent";
  const num = id.replace(/[^0-9]/g, "");
  return num ? `Drone ${num}` : id;
};
