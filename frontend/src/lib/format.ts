import type { AgentType, IncidentType } from "./types";

export const STATUS_COLOR: Record<string, string> = {
  IDLE: "#398C69",
  PATROLLING: "#398C69",
  COMPLETED: "#398C69",
  DETECTING: "#D99A39",
  COORDINATING: "#397FB8",
  MOVING: "#397FB8",
  RETURNING: "#536F86",
  RESPONDING: "#E96C4B",
  FAILED: "#7F8992",
  RECOVERING: "#866CC5",
};

export const STATUS_HELP: Record<string, string> = {
  IDLE: "Parked at base, ready",
  PATROLLING: "Following its patrol route",
  DETECTING: "Own sensors see a hazard / observing on site",
  COORDINATING: "Coordinating an incident or accepting a task",
  MOVING: "Travelling to a task",
  RESPONDING: "Performing a response action on site",
  RETURNING: "Going back to base",
  FAILED: "Stopped - no movement, sensing or radio",
  RECOVERING: "Rebooting after restore",
  COMPLETED: "Just finished a task",
};

export const HAZARD_COLOR: Record<IncidentType, string> = {
  FIRE: "#E96C4B",
  POLLUTION: "#36A6B5",
  EXTREME_HEAT: "#D99A39",
};

export const HAZARD_LABEL: Record<IncidentType, string> = {
  FIRE: "Fire",
  POLLUTION: "Pollution",
  EXTREME_HEAT: "Extreme heat",
};

export const INCIDENT_STATUS_LABEL: Record<string, string> = {
  UNDETECTED: "Not yet detected",
  DETECTED: "Verifying",
  CONFIRMED: "Confirmed - dispatching",
  RESPONDING: "Response under way",
  NEEDS_INTERVENTION: "Needs intervention",
  RESOLVED: "Resolved",
  REJECTED: "False alarm rejected",
  CLOSED_BY_RESTART: "Closed (restart)",
};

export const INCIDENT_STATUS_COLOR: Record<string, string> = {
  UNDETECTED: "#71879B",
  DETECTED: "#D99A39",
  CONFIRMED: "#397FB8",
  RESPONDING: "#E96C4B",
  NEEDS_INTERVENTION: "#E96C4B",
  RESOLVED: "#398C69",
  REJECTED: "#71879B",
  CLOSED_BY_RESTART: "#71879B",
};

export const TYPE_SHORT: Record<AgentType, string> = {
  MONITOR_DRONE: "Monitor drone",
  FIRE_DRONE: "Fire drone",
  SPRINKLER: "Sprinkler",
  POLLUTION_UNIT: "Pollution unit",
  COOLING_UNIT: "Cooling unit",
};

export const TASK_LABEL: Record<string, string> = {
  INVESTIGATE: "Investigate",
  FIRE_SUPPRESSION: "Fire suppression",
  WATER_SPRAY: "Water spray",
  POLLUTION_CLEANUP: "Pollution clean-up",
  COOLING: "Cooling",
};

export const TASK_STATUS_COLOR: Record<string, string> = {
  UNASSIGNED: "#E96C4B",
  ASSIGNED: "#397FB8",
  IN_PROGRESS: "#866CC5",
  INTERRUPTED: "#D99A39",
  COMPLETED: "#398C69",
  CANCELLED: "#71879B",
};

export function sentence(value: string | null | undefined): string {
  if (!value) return "-";
  const s = value.replace(/_/g, " ").toLowerCase();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function fmtTicks(ticks: number | null | undefined): string {
  if (ticks === null || ticks === undefined) return "-";
  if (ticks < 60) return `${ticks} s`;
  const m = Math.floor(ticks / 60);
  const s = ticks % 60;
  return `${m} min ${s.toString().padStart(2, "0")} s`;
}

export function fmtDistance(m: number | null | undefined): string {
  if (m === null || m === undefined) return "-";
  return m >= 1000 ? `${(m / 1000).toFixed(2)} km` : `${Math.round(m)} m`;
}

export function fmtTime(iso: string): string {
  const d = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : iso + "Z");
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function haversine(a: [number, number], b: [number, number]): number {
  const R = 6371000;
  const toRad = (x: number) => (x * Math.PI) / 180;
  const dLat = toRad(b[0] - a[0]);
  const dLng = toRad(b[1] - a[1]);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(a[0])) * Math.cos(toRad(b[0])) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
}

export const CATEGORY_COLOR: Record<string, string> = {
  INCIDENT: "#d95926", DETECTION: "#E0A43A", CONSENSUS: "#5B9BD5", COORDINATION: "#5B9BD5", TASK: "#A98BE0",
  RESPONSE: "#A98BE0", FAILURE: "#E0533D", RECOVERY: "#5FB37C", NETWORK: "#6E9CC4", AGENT: "#A3ADA8", SIMULATION: "#76807B",
};
