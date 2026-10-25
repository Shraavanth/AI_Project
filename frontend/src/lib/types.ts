export type AgentType = "MONITOR_DRONE" | "FIRE_DRONE" | "SPRINKLER" | "POLLUTION_UNIT" | "COOLING_UNIT";
export type IncidentType = "FIRE" | "POLLUTION" | "EXTREME_HEAT";

export interface Readings {
  temperature: number;
  humidity: number;
  smoke: number;
  co2: number;
  air_quality: number;
  soil_moisture: number;
}

export interface AiResult {
  status: "NORMAL" | "ANOMALY";
  event: string;
  score: number;
}

export interface Agent {
  id: string;
  type: AgentType;
  type_label: string;
  mobile: boolean;
  capabilities: string[];
  operating_radius_m: number;
  lat: number;
  lng: number;
  home: [number, number];
  status: string;
  battery: number;
  health: number;
  charging: boolean;
  speed_mps: number;
  readings: Readings;
  sensor_override: boolean;
  ai: AiResult;
  neighbors: string[];
  task_id: string | null;
  task_type: string | null;
  incident_id: string | null;
  task_progress: number | null;
  destination: [number, number] | null;
  destination_label: string | null;
  coordinator_of: string[];
  last_comm_tick: number | null;
  last_telemetry_tick: number | null;
  failure_reason: string | null;
  trail: [number, number][];
  distance_travelled_m: number;
  messages_sent: number;
  messages_received: number;
}

export interface Message {
  message_id: string;
  tick: number;
  timestamp: string;
  sender: string;
  receiver: string;
  type: string;
  incident_id: string | null;
  payload: Record<string, unknown>;
  hops: number | null;
  delivered: boolean;
}

export interface CandidateRow {
  agent_id: string;
  agent_type: string;
  distance_m: number;
  battery: number;
  eligible: boolean;
  score: number | null;
  reason: string;
}

export interface TaskOwner {
  agent_id: string;
  from_tick: number;
  to_tick: number | null;
  end: string | null;
}

export interface TaskSummary {
  id: string;
  incident_id: string;
  task_type: string;
  capability: string;
  status: string;
  owner_id: string | null;
  previous_owner_id: string | null;
  reassign_count: number;
  progress: number;
  work_done: number;
  optional: boolean;
}

export interface TaskDetail extends TaskSummary {
  target: [number, number] | null;
  owners: TaskOwner[];
  created_tick: number;
  assigned_tick: number | null;
  started_tick: number | null;
  completed_tick: number | null;
  interrupted_tick: number | null;
  last_decision: CandidateRow[];
  outcome: string | null;
}

export interface Vote {
  agent_id: string;
  agent_type: string;
  ai_status: string;
  ai_event: string;
  score: number;
  distance_m: number;
  vote: "SUPPORT" | "OPPOSE" | "ABSTAIN";
  reason: string;
}

export interface Consensus {
  supporters: string[];
  opposers: string[];
  abstained: string[];
  confidence: number;
  confirmed: boolean;
  rule: string;
  round: number;
  tick: number;
  coordinator_id: string;
  votes: Vote[];
  decision: string;
}

export interface Incident {
  id: string;
  type: IncidentType;
  status: string;
  origin: string;
  physical: boolean;
  is_boundary?: boolean;
  provisional?: boolean;
  lat: number;
  lng: number;
  radius_m: number;
  severity: number;
  initial_severity: number;
  peak_severity: number;
  estimated_location: [number, number] | null;
  estimate_error_m: number | null;
  detectors: string[];
  alert_recipients: string[];
  coordinator_id: string | null;
  consensus: Consensus | null;
  consensus_rounds: number;
  rejections: number;
  task_ids: string[];
  tasks: TaskSummary[];
  created_tick: number;
  detected_tick: number | null;
  confirmed_tick: number | null;
  response_started_tick: number | null;
  resolved_tick: number | null;
  resolution_note: string | null;
}

export interface TimelineEntry {
  tick: number;
  stage: string;
  text: string;
}

export interface IncidentDetail extends Omit<Incident, "tasks"> {
  tasks: TaskDetail[];
  timeline: TimelineEntry[];
  consensus_history: (Omit<Consensus, "confirmed" | "rule"> & { incident_id: string })[];
  severity_history: { tick: number; severity: number }[];
  messages: Message[];
  affected_agents: { agent_id: string; influence: number; distance_m: number }[];
}

export interface Link {
  source: string;
  target: string;
  distance_m: number;
  kind: "range" | "relay";
}

export interface NetworkEvent {
  tick: number;
  timestamp: string;
  trigger: string;
  agent_id: string | null;
  links_removed: [string, string][];
  links_created: [string, string][];
  relay_links: [string, string, number][];
  components_before_bridging: number;
  components_after: number;
  connected_after: boolean;
  edges_after: number;
  operational_agents: number;
  compute_ms: number;
}

export interface Activity {
  tick: number;
  timestamp: string;
  category: string;
  title: string;
  message: string;
  agent_id: string | null;
  incident_id: string | null;
}

export interface Site {
  lat: number;
  lng: number;
  radius_m: number;
  label: string;
  source: string;
  run_id: number;
  deployed_at: string;
}

export interface Stats {
  total_agents: number;
  operational_agents: number;
  failed_agents: number;
  recovering_agents: number;
  responding_agents: number;
  moving_agents: number;
  patrolling_agents: number;
  status_counts: Record<string, number>;
  active_incidents: number;
  resolved_incidents: number;
  incidents_needing_intervention: number;
  active_tasks: number;
  unassigned_tasks: number;
  links: number;
  relay_links: number;
  network_connected: boolean;
  network_components: number;
  messages_delivered: number;
  messages_dropped: number;
  average_battery: number;
  anomalous_agents: number;
}

export interface SimState {
  tick: number;
  running: boolean;
  speed: number;
  tick_interval_s: number;
  allowed_speeds: number[];
  run_id: number;
  last_step_ms: number;
}

export interface Snapshot {
  tick: number;
  simulation: SimState;
  site: Site;
  agents: Agent[];
  incidents: Incident[];
  links: Link[];
  network: {
    connected: boolean;
    components: number;
    edges: number;
    comm_range_m: number;
    max_relay_range_m: number;
    last_event: NetworkEvent | null;
  };
  stats: Stats;
  activity: Activity[];
  coverage?: CoverageSummary;
  database: { label: string; ok: boolean; last_error: string | null; errors: number };
  websocket_clients: number;
}

export interface CoverageSector {
  original_owner: string;
  name: string;
  center_angle: number;
  start_angle: number;
  end_angle: number;
  radius_m: number;
  status: string;
}

export interface OverlappingRegion {
  drone_a: string;
  drone_b: string;
  distance_m: number;
  overlap_width_m: number;
  midpoint: [number, number];
}

export interface BoundaryDetection {
  incident_id: string;
  agent_id: string;
  distance_m: number;
  tier: "NOMINAL" | "BOUNDARY";
  tick: number;
}

export interface CoverageNotification {
  message: string;
  tick: number;
  time?: number;
}

export interface CoverageReassignment {
  sector_id: string;
  sector_name: string;
  original_owner: string;
  assigned_to: string;
  tick: number;
}

export interface CoverageSummary {
  total_monitors: number;
  active_monitors: number;
  failed_monitors: number;
  offline_monitors: number;
  investigating_monitors: number;
  coverage_pct: number;
  uncovered_count: number;
  uncovered_areas: CoverageSector[];
  reassigned_tasks_count: number;
  reassigned_tasks: TaskSummary[];
  reassignments: CoverageReassignment[];
  boundary_detections_count: number;
  boundary_detections: BoundaryDetection[];
  provisional_incidents: string[];
  overlapping_regions: OverlappingRegion[];
  nominal_radius_m: number;
  boundary_tolerance_m: number;
  notifications: CoverageNotification[];
  recent_notifications: CoverageNotification[];
  operational_warning: string | null;
  operational_warnings: string[];
}

export interface AgentDetail extends Agent {
  type_description: string;
  baseline: Readings;
  task: TaskDetail | null;
  task_history: {
    task_id: string;
    incident_id: string;
    task_type: string;
    assigned_tick: number;
    reassigned_from: string | null;
    ended_tick: number | null;
    outcome: string | null;
  }[];
  inbox: Message[];
  sent: Message[];
  failures: Record<string, unknown>[];
  patrol_route: [number, number][];
  neighbor_distances: Record<string, number>;
}
