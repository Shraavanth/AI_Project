import {
  Agent,
  AgentDeployment,
  SystemStatus,
  Incident,
  NetworkData,
  AuditLog,
  AnalyticsData,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

async function fetchJSON<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    let errorDetail = `HTTP Error ${res.status}`;
    try {
      const err = await res.json();
      errorDetail = err.detail || errorDetail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  // Status
  getStatus: () => fetchJSON<SystemStatus>("/api/status"),

  // Agents
  getAgents: async (): Promise<Agent[]> => {
    const data = await fetchJSON<{ agents: Agent[] }>("/api/agents");
    return data.agents;
  },

  getAgentDetail: (id: string) => fetchJSON<Agent>(`/api/agents/${id}`),

  getAgentDeployment: async (): Promise<AgentDeployment | null> => {
    const data = await fetchJSON<{ deployment: AgentDeployment | null }>("/api/agents/deployment");
    return data.deployment;
  },

  deployAgents: (deployment: Omit<AgentDeployment, "updated_at">) =>
    fetchJSON<{
      success: boolean;
      deployment: AgentDeployment;
      deployed_count: number;
      agents: Agent[];
    }>("/api/agents/deploy", {
      method: "POST",
      body: JSON.stringify(deployment),
    }),

  createAgent: (agentData: any) =>
    fetchJSON<{ success: boolean; agent: Agent }>("/api/agents", {
      method: "POST",
      body: JSON.stringify(agentData),
    }),

  updateAgent: (id: string, updates: any) =>
    fetchJSON<Agent>(`/api/agents/${id}`, {
      method: "PATCH",
      body: JSON.stringify(updates),
    }),

  moveAgent: (id: string, x: number, y: number) =>
    fetchJSON<Agent>(`/api/agents/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ x, y }),
    }),

  moveAgentDirection: (id: string, direction: "UP" | "DOWN" | "LEFT" | "RIGHT") =>
    fetchJSON<{ success: boolean; agent: Agent }>(`/api/agents/${id}/move-direction?direction=${direction}`, {
      method: "POST",
    }),

  stepPatrol: () =>
    fetchJSON<{ success: boolean; statistics: any; agents: Agent[] }>("/api/simulation/patrol-step", {
      method: "POST",
    }),

  deleteAgent: (id: string) =>
    fetchJSON<{ success: boolean; message: string }>(`/api/agents/${id}`, {
      method: "DELETE",
    }),

  failAgent: (id: string) =>
    fetchJSON<{ success: boolean; agent: Agent }>(`/api/agents/${id}/fail`, {
      method: "POST",
    }),

  restoreAgent: (id: string) =>
    fetchJSON<{ success: boolean; agent: Agent }>(`/api/agents/${id}/restore`, {
      method: "POST",
    }),

  restartAgent: (id: string) =>
    fetchJSON<{ success: boolean; restarted_agent: string; agent: Agent }>(`/api/agents/${id}/restart`, {
      method: "POST",
    }),

  analyzeAgent: (id: string) =>
    fetchJSON<{ agent_id: string; ai_result: any; ai_explanation: any }>(`/api/agents/${id}/analyze`, {
      method: "POST",
    }),

  // Events & Incidents
  createFireEvent: (params?: any) =>
    fetchJSON<Incident>("/api/events/fire", {
      method: "POST",
      body: JSON.stringify(params || {}),
    }),

  createPollutionEvent: (params?: any) =>
    fetchJSON<Incident>("/api/events/pollution", {
      method: "POST",
      body: JSON.stringify(params || {}),
    }),

  createExtremeHeatEvent: (params?: any) =>
    fetchJSON<Incident>("/api/events/extreme-heat", {
      method: "POST",
      body: JSON.stringify(params || {}),
    }),

  getEvents: async (): Promise<Incident[]> => {
    const data = await fetchJSON<{ events: Incident[] }>("/api/events");
    return data.events;
  },

  getEventCommunications: (eventId: string) =>
    fetchJSON<{ event_id: string; communications: any[] }>(`/api/events/${eventId}/communications`),

  resolveEvent: (eventId: string) =>
    fetchJSON<{
      success: boolean;
      event_id: string;
      status: string;
      resolution_report: any;
      fleet_health_summary: any;
      agent_health_breakdown: any[];
    }>(`/api/events/${eventId}/resolve`, {
      method: "POST",
    }),

  acknowledgeEvent: (eventId: string) =>
    fetchJSON<{ success: boolean; event_id: string; status: string }>(`/api/events/${eventId}/acknowledge`, {
      method: "POST",
    }),

  rechargeFleet: () =>
    fetchJSON<{ success: boolean; message: string; agents: Agent[] }>("/api/agents/recharge", {
      method: "POST",
    }),

  // Network & Self-Organization
  getNetwork: () => fetchJSON<NetworkData>("/api/network"),

  recoverNetwork: () =>
    fetchJSON<{ success: boolean; recovery: any; network: NetworkData }>("/api/network/recover", {
      method: "POST",
    }),

  resetSimulation: () =>
    fetchJSON<SystemStatus>("/api/simulation/reset", {
      method: "POST",
    }),

  failFireAgentHelper: () =>
    fetchJSON<{ success: boolean; failed_agent?: string }>("/api/agents/fail-fire-agent", {
      method: "POST",
    }),

  // Audit Logs & Analytics
  getHistory: async (category: string = "ALL", limit: number = 100): Promise<AuditLog[]> => {
    const data = await fetchJSON<{ history: AuditLog[] }>(`/api/history?category=${category}&limit=${limit}`);
    return data.history;
  },

  getAnalytics: () => fetchJSON<AnalyticsData>("/api/analytics"),
};
