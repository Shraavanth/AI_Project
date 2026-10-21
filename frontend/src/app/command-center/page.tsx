"use client";

import { useEffect, useState, useMemo } from "react";
import { api } from "@/lib/api";
import { Agent, SystemStatus, AuditLog, Incident, AnalyticsData } from "@/lib/types";
import LiveMonitoringMap from "@/components/LiveMonitoringMap";
import AgentDetailModal from "@/components/AgentDetailModal";
import {
  Compass,
  AlertTriangle,
  Flame,
  CheckCircle2,
  Share2,
  Clock,
  ArrowRight,
  ShieldAlert,
  Radio,
  Activity,
  Layers,
  Thermometer,
  CloudFog,
  Cpu,
  ChevronRight,
  Check,
  RefreshCw
} from "lucide-react";
import Link from "next/link";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from "recharts";

export default function CommandCenterPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [lastUpdateTime, setLastUpdateTime] = useState<string>("Syncing...");
  const [actionMsg, setActionMsg] = useState<string>("");

  const fetchData = async () => {
    try {
      const [statusData, agentsData, eventsData, historyData, analyticsData] =
        await Promise.all([
          api.getStatus(),
          api.getAgents(),
          api.getEvents(),
          api.getHistory("ALL", 25),
          api.getAnalytics(),
        ]);

      setStatus(statusData);
      setAgents(agentsData);
      setIncidents(eventsData);
      setLogs(historyData);
      setAnalytics(analyticsData);

      const now = new Date();
      setLastUpdateTime(now.toTimeString().split(" ")[0] + " UTC");

      // Keep selectedAgent synchronized if updated
      if (selectedAgent) {
        const found = agentsData.find((a) => a.id === selectedAgent.id);
        if (found) setSelectedAgent(found);
      }
    } catch (err) {
      console.error("Failed to load command center data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Compute Environmental Risk Score across transect
  const transectRisk = useMemo(() => {
    if (agents.length === 0) return { score: 12, label: "LOW BASELINE" };
    const avgRisk =
      agents.reduce((acc, a) => acc + (a.risk_score || 8), 0) / agents.length;
    const rounded = Math.round(avgRisk);
    if (rounded >= 65) return { score: rounded, label: "CRITICAL HAZARD" };
    if (rounded >= 35) return { score: rounded, label: "ELEVATED CONCERN" };
    return { score: rounded, label: "NORMAL BASELINE" };
  }, [agents]);

  // Derive recent peer-to-peer agent communications from log events
  const agentComms = useMemo(() => {
    return logs
      .filter(
        (l) =>
          l.category === "EVENT" ||
          l.category === "CONSENSUS" ||
          l.category === "NETWORK" ||
          l.category === "RECOVERY"
      )
      .slice(0, 5);
  }, [logs]);

  // Active Critical Incidents
  const activeIncidents = useMemo(() => {
    return incidents.filter((i) => i.status === "ACTIVE");
  }, [incidents]);

  // Acknowledge / Resolve Incident Handlers
  const handleAcknowledge = async (eventId: string) => {
    try {
      await api.acknowledgeEvent(eventId);
      setActionMsg(`Incident ${eventId} acknowledged.`);
      setTimeout(() => setActionMsg(""), 3000);
      fetchData();
    } catch (e: any) {
      alert(`Acknowledgment failed: ${e.message}`);
    }
  };

  const handleResolve = async (eventId: string) => {
    try {
      await api.resolveEvent(eventId);
      setActionMsg(`Incident ${eventId} marked as resolved.`);
      setTimeout(() => setActionMsg(""), 3000);
      fetchData();
    } catch (e: any) {
      alert(`Resolution failed: ${e.message}`);
    }
  };

  const activeAgentsCount = status?.active_agents ?? agents.filter((a) => a.status === "ACTIVE").length;
  const offlineAgentsCount = status?.failed_agents ?? agents.filter((a) => a.status === "FAILED").length;
  const openIncidentsCount = activeIncidents.length;

  return (
    <div className="space-y-7 max-w-7xl mx-auto">
      {/* 1. EDITORIAL PAGE HEADER */}
      <div className="border-b border-border pb-5">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="editorial-tag text-secondary-text mb-1 tracking-widest">
              FIELD OBSERVATORY TRANSECT ALPHA
            </div>
            <h1 className="editorial-title text-3xl md:text-4xl font-serif font-bold text-forest-green tracking-tight leading-none">
              Listening to the environment.
            </h1>
            <p className="mt-2 text-sm text-secondary-text max-w-2xl leading-relaxed">
              A distributed network of autonomous agents observing environmental change,
              sharing evidence, and adapting without a central decision-maker.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-secondary-text self-start md:self-auto">
            <span className="w-2 h-2 rounded-full bg-secondary-green animate-pulse"></span>
            <span>Cascade Biosphere Reserve</span>
          </div>
        </div>

        {/* 2. COMPACT SYSTEM STATUS STRIP */}
        <div className="mt-6 grid grid-cols-2 sm:grid-cols-5 divide-y sm:divide-y-0 sm:divide-x divide-border bg-surface border border-border rounded shadow-editorial p-1">
          {/* Active Agents */}
          <div className="px-4 py-2.5 flex flex-col justify-center">
            <span className="editorial-tag text-[9px] text-secondary-text">ACTIVE AGENTS</span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-xl font-serif font-bold text-forest-green tabular-nums">
                {activeAgentsCount}
              </span>
              <span className="text-[11px] font-mono text-secondary-text">
                / {status?.total_agents ?? agents.length}
              </span>
            </div>
          </div>

          {/* Offline Agents */}
          <div className="px-4 py-2.5 flex flex-col justify-center">
            <span className="editorial-tag text-[9px] text-secondary-text">OFFLINE AGENTS</span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span
                className={`text-xl font-serif font-bold tabular-nums ${
                  offlineAgentsCount > 0 ? "text-warning-amber" : "text-forest-green"
                }`}
              >
                {offlineAgentsCount}
              </span>
              <span className="text-[11px] font-mono text-secondary-text">
                {offlineAgentsCount > 0 ? "Signal severed" : "All connected"}
              </span>
            </div>
          </div>

          {/* Open Incidents */}
          <div className="px-4 py-2.5 flex flex-col justify-center">
            <span className="editorial-tag text-[9px] text-secondary-text">OPEN INCIDENTS</span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span
                className={`text-xl font-serif font-bold tabular-nums ${
                  openIncidentsCount > 0 ? "text-critical-incident" : "text-forest-green"
                }`}
              >
                {openIncidentsCount}
              </span>
              <span className="text-[11px] font-mono text-secondary-text">
                {openIncidentsCount > 0 ? "Active consensus" : "Nominal transect"}
              </span>
            </div>
          </div>

          {/* Environmental Risk */}
          <div className="px-4 py-2.5 flex flex-col justify-center">
            <span className="editorial-tag text-[9px] text-secondary-text">ENVIRONMENTAL RISK</span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span
                className={`text-xl font-serif font-bold tabular-nums ${
                  transectRisk.score >= 50
                    ? "text-critical-incident"
                    : transectRisk.score >= 30
                    ? "text-warning-amber"
                    : "text-forest-green"
                }`}
              >
                {transectRisk.score}%
              </span>
              <span className="text-[10px] font-mono uppercase text-secondary-text">
                {transectRisk.label}
              </span>
            </div>
          </div>

          {/* Last Update */}
          <div className="px-4 py-2.5 flex flex-col justify-center col-span-2 sm:col-span-1">
            <span className="editorial-tag text-[9px] text-secondary-text">LAST UPDATE</span>
            <div className="flex items-center gap-1.5 mt-0.5 text-xs font-mono text-forest-green">
              <Clock className="w-3.5 h-3.5 text-secondary-text" />
              <span className="tabular-nums">{lastUpdateTime}</span>
            </div>
          </div>
        </div>
      </div>

      {actionMsg && (
        <div className="p-3 bg-muted-sage text-forest-green rounded border border-border text-xs font-mono flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-secondary-green" />
            <span>{actionMsg}</span>
          </div>
          <button onClick={() => setActionMsg("")} className="text-secondary-text hover:text-forest-green">
            Dismiss
          </button>
        </div>
      )}

      {/* 3. MAIN SECTION: MAP (68%) + NARROW SIDE PANEL (32%) */}
      <div className="flex flex-col lg:flex-row gap-6 items-stretch">
        {/* MAP COLUMN (68% width on desktop) */}
        <div className="w-full lg:w-[68%] flex flex-col">
          <LiveMonitoringMap
            agents={agents}
            lastEvent={status?.last_event || (activeIncidents[0] ?? null)}
            selectedAgentId={selectedAgent?.id || null}
            onSelectAgent={(agent) => {
              setSelectedAgent(agent);
            }}
            onRefresh={fetchData}
          />
        </div>

        {/* NARROW SIDE PANEL (32% width on desktop) */}
        <div className="w-full lg:w-[32%] flex flex-col gap-4">
          {/* Panel Card 1: Current Critical Incidents */}
          <div className="bg-surface rounded border border-border shadow-editorial p-4 flex flex-col">
            <div className="flex items-center justify-between pb-2.5 border-b border-border">
              <div className="flex items-center gap-1.5">
                <Flame className="w-4 h-4 text-critical-incident" />
                <span className="editorial-tag text-[10px] text-forest-green">
                  CURRENT CRITICAL INCIDENTS
                </span>
              </div>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-surface-muted text-secondary-text border border-border">
                {activeIncidents.length} ACTIVE
              </span>
            </div>

            <div className="mt-3 flex-1 space-y-3">
              {activeIncidents.length === 0 ? (
                <div className="py-6 text-center text-xs text-secondary-text">
                  <p className="font-serif italic text-forest-green">
                    Transect atmosphere quiescent.
                  </p>
                  <p className="text-[11px] mt-1 text-secondary-text/80">
                    No active hazard alerts across the 20 monitoring stations.
                  </p>
                </div>
              ) : (
                activeIncidents.map((inc) => (
                  <div
                    key={inc.event_id}
                    className="p-3 rounded bg-critical-incident/5 border border-critical-incident/25 text-xs space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 font-mono font-bold text-critical-incident">
                        <span>{inc.event_type}</span>
                        <span className="text-[9px] px-1 py-0.2 rounded bg-critical-incident/15 text-critical-incident">
                          {inc.severity}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-secondary-text">
                        {inc.consensus_state} ({Math.round(inc.confidence * 100)}%)
                      </span>
                    </div>

                    <p className="text-[11px] text-secondary-text leading-tight">
                      Affecting {inc.affected_count} field nodes in {inc.zone_name || "Central Basin"}.
                    </p>

                    <div className="pt-2 border-t border-critical-incident/20 flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleAcknowledge(inc.event_id)}
                        className="px-2.5 py-1 rounded bg-surface hover:bg-surface-muted border border-border text-[10px] font-mono text-forest-green transition"
                      >
                        Acknowledge
                      </button>
                      <button
                        onClick={() => handleResolve(inc.event_id)}
                        className="px-2.5 py-1 rounded bg-forest-green hover:bg-forest-green-light text-[10px] font-mono text-surface transition"
                      >
                        Resolve Hazard
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Panel Card 2: Recent Agent Communications */}
          <div className="bg-surface rounded border border-border shadow-editorial p-4 flex flex-col">
            <div className="flex items-center justify-between pb-2.5 border-b border-border">
              <div className="flex items-center gap-1.5">
                <Share2 className="w-3.5 h-3.5 text-secondary-green" />
                <span className="editorial-tag text-[10px] text-forest-green">
                  AGENT P2P COMMUNICATIONS
                </span>
              </div>
              <span className="text-[9px] font-mono text-secondary-text">PEER MESH</span>
            </div>

            <div className="mt-3 space-y-2.5">
              {agentComms.length === 0 ? (
                <div className="py-4 text-center text-xs text-secondary-text">
                  Awaiting inter-agent transmissions...
                </div>
              ) : (
                agentComms.map((log) => (
                  <div
                    key={log.id}
                    className="text-[11px] border-b border-border/60 pb-2 last:border-0 last:pb-0"
                  >
                    <div className="flex items-center justify-between text-[10px] text-secondary-text mb-0.5">
                      <span className="font-mono text-forest-green font-semibold">
                        {log.agent_id ? `NODE ${log.agent_id}` : "MESH TOPOLOGY"}
                      </span>
                      <span className="font-mono text-[9px]">
                        {log.timestamp ? log.timestamp.split("T")[1]?.slice(0, 8) : "just now"}
                      </span>
                    </div>
                    <p className="text-forest-green text-[11px] leading-tight font-serif">
                      {log.title}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Panel Card 3: Environmental Risk Summary */}
          <div className="bg-surface rounded border border-border shadow-editorial p-4 flex flex-col">
            <div className="flex items-center justify-between pb-2.5 border-b border-border">
              <div className="flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-secondary-green" />
                <span className="editorial-tag text-[10px] text-forest-green">
                  TRANSECT RISK SUMMARY
                </span>
              </div>
              <span className="text-[10px] font-mono font-bold text-forest-green tabular-nums">
                {transectRisk.score}%
              </span>
            </div>

            <div className="mt-3 space-y-2 text-xs">
              <div className="flex items-center justify-between text-secondary-text">
                <span className="text-[11px]">Mean Ambient Temp:</span>
                <span className="font-mono text-forest-green font-semibold tabular-nums">
                  {agents.length > 0
                    ? (
                        agents.reduce((sum, a) => sum + (a.readings?.temperature || 28), 0) /
                        agents.length
                      ).toFixed(1)
                    : "28.0"}
                  °C
                </span>
              </div>

              <div className="flex items-center justify-between text-secondary-text">
                <span className="text-[11px]">Smoke Particulate Index:</span>
                <span className="font-mono text-forest-green font-semibold tabular-nums">
                  {agents.length > 0
                    ? (
                        agents.reduce((sum, a) => sum + (a.readings?.smoke || 0.1), 0) /
                        agents.length
                      ).toFixed(2)
                    : "0.10"}
                </span>
              </div>

              <div className="flex items-center justify-between text-secondary-text">
                <span className="text-[11px]">Average CO2 Concentration:</span>
                <span className="font-mono text-forest-green font-semibold tabular-nums">
                  {agents.length > 0
                    ? Math.round(
                        agents.reduce((sum, a) => sum + (a.readings?.co2 || 420), 0) /
                          agents.length
                      )
                    : 420}{" "}
                  ppm
                </span>
              </div>

              <div className="flex items-center justify-between text-secondary-text">
                <span className="text-[11px]">Active Mesh Edges:</span>
                <span className="font-mono text-forest-green font-semibold tabular-nums">
                  {status?.connections ?? 0} links
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. LOWER SECTION: RESTRAINED TELEMETRY SECTION + INCIDENT FEED */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
        {/* Telemetry Curves Card */}
        <div className="bg-surface rounded border border-border shadow-editorial p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-border mb-4">
              <div>
                <span className="editorial-tag text-[9px] text-secondary-text">
                  ENVIRONMENTAL TELEMETRY
                </span>
                <h3 className="font-serif font-bold text-base text-forest-green">
                  Ambient Temperature & Particulate Curves
                </h3>
              </div>
              <Link
                href="/analytics"
                className="text-xs font-mono text-secondary-green hover:text-forest-green flex items-center gap-1"
              >
                Full Analytics <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <p className="text-xs text-secondary-text mb-4 leading-relaxed">
              Continuous sensor observations logged across the Cascade Biosphere transect grid.
            </p>

            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={analytics?.temperature_trend?.slice(-10) || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#DFE4D9" opacity={0.6} />
                  <XAxis dataKey="time" stroke="#69786D" fontSize={10} tickLine={false} />
                  <YAxis stroke="#69786D" fontSize={10} domain={[15, 50]} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#FFFFFF",
                      borderColor: "#DFE4D9",
                      borderRadius: "4px",
                      fontSize: "11px",
                      fontFamily: "var(--font-mono)",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#193B32"
                    strokeWidth={1.8}
                    dot={{ r: 2, fill: "#C7F36B" }}
                    name="Temp (°C)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="pt-3 border-t border-border flex items-center justify-between text-[11px] text-secondary-text font-mono">
            <span>BASELINE: 28.0°C</span>
            <span>CRITICAL THRESHOLD: 42.0°C</span>
          </div>
        </div>

        {/* Chronological Incident Feed Card */}
        <div className="bg-surface rounded border border-border shadow-editorial p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-border mb-4">
              <div>
                <span className="editorial-tag text-[9px] text-secondary-text">
                  HAZARD LOG
                </span>
                <h3 className="font-serif font-bold text-base text-forest-green">
                  Chronological Environmental Incident Feed
                </h3>
              </div>
              <Link
                href="/incidents"
                className="text-xs font-mono text-secondary-green hover:text-forest-green flex items-center gap-1"
              >
                Manage Incidents <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="space-y-3">
              {incidents.slice(0, 4).length === 0 ? (
                <div className="py-12 text-center text-xs text-secondary-text font-serif italic">
                  No incident records in the database archive.
                </div>
              ) : (
                incidents.slice(0, 4).map((evt) => (
                  <div
                    key={evt.event_id}
                    className="p-3 rounded bg-surface-muted border border-border flex items-start justify-between gap-3 text-xs"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-forest-green text-[11px]">
                          {evt.event_type}
                        </span>
                        <span
                          className={`text-[9px] font-mono px-1.5 py-0.2 rounded font-semibold ${
                            evt.status === "ACTIVE"
                              ? "bg-critical-incident/15 text-critical-incident"
                              : "bg-muted-sage text-forest-green"
                          }`}
                        >
                          {evt.status}
                        </span>
                        <span className="text-[10px] text-secondary-text font-mono">
                          {evt.consensus_state} ({Math.round(evt.confidence * 100)}%)
                        </span>
                      </div>
                      <p className="text-[11px] text-secondary-text">
                        Transect sector: {evt.zone_name || "Cascade Sector"} | {evt.affected_count} nodes in proximity
                      </p>
                    </div>

                    <span className="text-[10px] font-mono text-secondary-text whitespace-nowrap">
                      {evt.timestamp ? evt.timestamp.split("T")[0] : ""}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="pt-3 border-t border-border flex items-center justify-between text-[11px] text-secondary-text">
            <span>CONSENSUS QUORUM: LOCAL REACHABLE NEIGHBORS</span>
            <Link href="/history" className="hover:text-forest-green underline font-mono text-[10px]">
              View All Audit History
            </Link>
          </div>
        </div>
      </div>

      {/* Selected Agent Modal if requested */}
      {showDetailModal && selectedAgent && (
        <AgentDetailModal
          agent={selectedAgent}
          onClose={() => setShowDetailModal(false)}
          onUpdate={fetchData}
        />
      )}
    </div>
  );
}
