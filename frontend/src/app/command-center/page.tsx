"use client";

import { useEffect, useState, useMemo } from "react";
import { api } from "@/lib/api";
import { Agent, SystemStatus, AuditLog, Incident, AnalyticsData, formatAgentName } from "@/lib/types";
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
  RefreshCw,
  Battery,
  Zap,
  ShieldCheck,
  X
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

  // Automated Incident Resolution & Communication States
  const [autoResolvingId, setAutoResolvingId] = useState<string | null>(null);
  const [autoStep, setAutoStep] = useState<number>(0);
  const [autoStepLabel, setAutoStepLabel] = useState<string>("");
  const [resolutionReport, setResolutionReport] = useState<any | null>(null);
  const [liveComms, setLiveComms] = useState<
    Array<{
      id: string;
      sender: string;
      receiver: string;
      message: string;
      step: number;
      time: string;
    }>
  >([]);
  const [isRecharging, setIsRecharging] = useState<boolean>(false);

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

  // Automated Multi-Agent Resolution & Near-Agent Communication Loop
  useEffect(() => {
    if (activeIncidents.length === 0) {
      if (autoResolvingId) {
        setAutoResolvingId(null);
        setAutoStep(0);
      }
      return;
    }

    const current = activeIncidents[0];
    if (autoResolvingId === current.event_id) return;

    setAutoResolvingId(current.event_id);
    setAutoStep(1);
    setAutoStepLabel("Detecting hazard & broadcasting emergency telemetry to near drones...");

    // Determine responding drones with simple names
    const affected = current.affected_agents || [];
    const r1 = formatAgentName(affected[0] || "A1", agents.find((a) => a.id === affected[0])?.name);
    const r2 = formatAgentName(affected[1] || affected[0] || "A2", agents.find((a) => a.id === affected[1])?.name);
    const r3 = formatAgentName(affected[2] || affected[0] || "A3", agents.find((a) => a.id === affected[2])?.name);

    const now = new Date().toLocaleTimeString();

    // Step 1: Emergency Transmission to Near Agents (immediate)
    setLiveComms((prev) => [
      {
        id: `comms-${Date.now()}-1`,
        sender: r1,
        receiver: r2,
        message: `🚨 Emergency telemetry: ${current.event_type} anomaly detected at sector coordinates. Initiating P2P broadcast.`,
        step: 1,
        time: now,
      },
      ...prev.slice(0, 8),
    ]);

    // Step 2: Near-Agent Verification & Consensus (after 1200ms)
    const t1 = setTimeout(() => {
      setAutoStep(2);
      setAutoStepLabel(`Neighbor consensus quorum verified by ${r2} & ${r3}...`);
      setLiveComms((prev) => [
        {
          id: `comms-${Date.now()}-2`,
          sender: r2,
          receiver: r1,
          message: `✅ Quorum verified (${Math.round((current.confidence || 0.88) * 100)}% consensus). Committing perimeter containment.`,
          step: 2,
          time: new Date().toLocaleTimeString(),
        },
        {
          id: `comms-${Date.now()}-3`,
          sender: r3,
          receiver: r1,
          message: `🤝 Formation locked with ${r2}. Synchronizing suppression countermeasures.`,
          step: 2,
          time: new Date().toLocaleTimeString(),
        },
        ...prev.slice(0, 8),
      ]);
    }, 1200);

    // Step 3: Autonomous Suppression Countermeasures (after 2500ms)
    const t2 = setTimeout(() => {
      setAutoStep(3);
      setAutoStepLabel(`Autonomous suppression active: ${r1} & ${r2} deploying cooling & scrubbers...`);
      setLiveComms((prev) => [
        {
          id: `comms-${Date.now()}-4`,
          sender: `${r1} & ${r2}`,
          receiver: "Hazard Epicenter",
          message: `🛡️ Autonomous suppression payload deployed: aerosol cooling & high-efficiency particulate scrubbers active.`,
          step: 3,
          time: new Date().toLocaleTimeString(),
        },
        ...prev.slice(0, 8),
      ]);
    }, 2500);

    // Step 4: Automatic Resolution & Health Assessment (after 4000ms)
    const t3 = setTimeout(async () => {
      setAutoStep(4);
      setAutoStepLabel("Neutralizing hazard & auditing post-incident drone health...");
      try {
        const res = await api.resolveEvent(current.event_id);
        const report = res.resolution_report || res;
        setResolutionReport(report);
        setLiveComms((prev) => [
          {
            id: `comms-${Date.now()}-5`,
            sender: "Decentralized Quorum",
            receiver: "Command Center",
            message: `✅ Incident Neutralized! Sector restored to baseline. Drones audited for post-hazard health.`,
            step: 4,
            time: new Date().toLocaleTimeString(),
          },
          ...prev.slice(0, 8),
        ]);
        setActionMsg(`✅ Incident ${current.event_id} autonomously resolved by ${r1} & ${r2}. Telemetry restored.`);
        setTimeout(() => setActionMsg(""), 6000);
        await fetchData();
      } catch (err) {
        console.error("Auto resolution error:", err);
      } finally {
        setTimeout(() => setAutoStep(0), 1200);
      }
    }, 4000);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [activeIncidents, autoResolvingId, agents]);

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
      const res = await api.resolveEvent(eventId);
      setResolutionReport(res.resolution_report || res);
      setActionMsg(`Incident ${eventId} neutralized. Drone health audited.`);
      setTimeout(() => setActionMsg(""), 4000);
      fetchData();
    } catch (e: any) {
      alert(`Resolution failed: ${e.message}`);
    }
  };

  const handleRechargeFleet = async () => {
    setIsRecharging(true);
    try {
      await api.rechargeFleet();
      setActionMsg("⚡ All drones recharged to 100% capacity and recalibrated.");
      setTimeout(() => setActionMsg(""), 4000);
      await fetchData();
      if (resolutionReport?.agent_health_breakdown) {
        setResolutionReport((prev: any) => ({
          ...prev,
          agent_health_breakdown: prev.agent_health_breakdown.map((a: any) => ({
            ...a,
            battery_after: 100,
            battery_delta: 0,
            health_after: 100,
            diagnosis: "Recalibrated and fully recharged to 100%.",
          })),
          fleet_health_summary: {
            ...prev.fleet_health_summary,
            average_battery_level: 100,
            average_health_score: 100,
            maintenance_recommended: false,
          },
        }));
      }
    } catch (err: any) {
      alert(`Recharge failed: ${err.message}`);
    } finally {
      setIsRecharging(false);
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

      {/* Post-Hazard Fleet Health Assessment Banner (Displays when hazard is resolved) */}
      {resolutionReport && (
        <div className="bg-surface rounded border border-border shadow-elevated p-4 animate-fade-in border-l-4 border-l-forest-green">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-border gap-2">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-secondary-green" />
              <div>
                <h3 className="font-serif font-bold text-sm text-forest-green">
                  Incident Neutralized: Responding Drone Health & Battery Audit
                </h3>
                <p className="text-[11px] text-secondary-text font-mono">
                  Autonomous suppression successful. Telemetry returned to nominal baseline.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleRechargeFleet}
                disabled={isRecharging}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-forest-green text-surface hover:bg-forest-green-light transition text-xs font-mono font-bold shadow-sm"
              >
                <Zap className="w-3.5 h-3.5 text-botanical" />
                {isRecharging ? "Recharging Drones…" : "⚡ Recharge All Drones"}
              </button>
              <button
                onClick={() => setResolutionReport(null)}
                className="text-secondary-text hover:text-forest-green p-1 rounded"
                title="Dismiss health audit"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Quick Metrics Bar */}
          {resolutionReport.fleet_health_summary && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 py-3 border-b border-border text-xs">
              <div className="bg-surface-muted p-2 rounded border border-border/60">
                <span className="text-[9px] font-mono text-secondary-text block">PRIMARY RESPONDERS</span>
                <span className="font-mono font-bold text-forest-green text-sm">
                  {resolutionReport.fleet_health_summary.total_responders_count || 1} Drones
                </span>
              </div>
              <div className="bg-surface-muted p-2 rounded border border-border/60">
                <span className="text-[9px] font-mono text-secondary-text block">TOTAL BATTERY DRAW</span>
                <span className="font-mono font-bold text-warning-amber text-sm">
                  -{resolutionReport.fleet_health_summary.total_battery_expended_pct || 18}%
                </span>
              </div>
              <div className="bg-surface-muted p-2 rounded border border-border/60">
                <span className="text-[9px] font-mono text-secondary-text block">AVERAGE FLEET HEALTH</span>
                <span className="font-mono font-bold text-forest-green text-sm">
                  {resolutionReport.fleet_health_summary.average_health_score || 94}%
                </span>
              </div>
              <div className="bg-surface-muted p-2 rounded border border-border/60">
                <span className="text-[9px] font-mono text-secondary-text block">FLEET STATUS</span>
                <span className="font-mono font-bold text-forest-green text-sm">
                  NOMINAL (READY)
                </span>
              </div>
            </div>
          )}

          {/* Responder Drones Breakdown Cards */}
          {resolutionReport.agent_health_breakdown && (
            <div className="mt-3">
              <span className="text-[10px] font-mono font-bold text-secondary-text uppercase tracking-wider block mb-2">
                Individual Drone Performance & Wear Breakdown:
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5 max-h-52 overflow-y-auto pr-1">
                {resolutionReport.agent_health_breakdown
                  .filter((a: any) => a.role !== "STANDBY_MONITOR" && a.role !== "FAILED_NODE")
                  .slice(0, 6)
                  .map((agent: any) => {
                    const simpleName = formatAgentName(agent.agent_id, agent.name);
                    return (
                      <div
                        key={agent.agent_id}
                        className="p-2.5 rounded bg-surface border border-border text-xs space-y-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <strong className="font-mono text-forest-green font-bold text-[11px]">
                            {simpleName}
                          </strong>
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-muted-sage text-forest-green font-mono">
                            {agent.role.replace("_", " ")}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                          <div>
                            <span className="text-secondary-text block">Battery:</span>
                            <span className="font-bold text-forest-green">
                              {agent.battery_after}%{" "}
                              <span className="text-critical-incident">({agent.battery_delta}%)</span>
                            </span>
                          </div>
                          <div>
                            <span className="text-secondary-text block">Health:</span>
                            <span className="font-bold text-forest-green">
                              {agent.health_after}%{" "}
                              {agent.health_delta !== 0 && (
                                <span className="text-warning-amber">({agent.health_delta}%)</span>
                              )}
                            </span>
                          </div>
                        </div>
                        <p className="text-[10px] text-secondary-text italic leading-tight">
                          {agent.diagnosis}
                        </p>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}
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
            onHazardTriggered={() => {
              fetchData();
            }}
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
                activeIncidents.map((inc) => {
                  const responderNames = (inc.affected_agents || [])
                    .slice(0, 3)
                    .map((id) => formatAgentName(id, agents.find((a) => a.id === id)?.name))
                    .join(", ");

                  return (
                    <div
                      key={inc.event_id}
                      className="p-3 rounded bg-critical-incident/5 border border-critical-incident/25 text-xs space-y-2.5"
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
                        Responding: <strong className="text-forest-green font-mono">{responderNames || "Near Drones"}</strong> in {inc.zone_name || "Central Basin"}.
                      </p>

                      {/* Autonomous Resolution Stepper */}
                      {autoStep > 0 && autoResolvingId === inc.event_id && (
                        <div className="p-2 rounded bg-surface border border-forest-green/30 text-[10px] font-mono space-y-1 animate-pulse">
                          <div className="flex items-center justify-between text-forest-green font-bold">
                            <span className="flex items-center gap-1">
                              <Radio className="w-3 h-3 text-secondary-green animate-pulse" />
                              AUTONOMOUS RESOLUTION (STEP {autoStep}/4)
                            </span>
                            <span>{autoStep * 25}%</span>
                          </div>
                          <div className="w-full bg-border rounded-full h-1.5 overflow-hidden">
                            <div
                              className="bg-forest-green h-full transition-all duration-500 rounded-full"
                              style={{ width: `${autoStep * 25}%` }}
                            ></div>
                          </div>
                          <p className="text-[9px] text-secondary-text italic truncate">
                            {autoStepLabel}
                          </p>
                        </div>
                      )}

                      <div className="pt-2 border-t border-critical-incident/20 flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleAcknowledge(inc.event_id)}
                          className="px-2.5 py-1 rounded bg-surface hover:bg-surface-muted border border-border text-[10px] font-mono text-forest-green transition"
                        >
                          Acknowledge
                        </button>
                        <button
                          onClick={() => handleResolve(inc.event_id)}
                          className="px-2.5 py-1 rounded bg-forest-green hover:bg-forest-green-light text-[10px] font-mono text-surface font-bold transition flex items-center gap-1"
                        >
                          <Zap className="w-3 h-3 text-botanical" />
                          Resolve Immediately
                        </button>
                      </div>
                    </div>
                  );
                })
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
              <span className="text-[9px] font-mono text-secondary-green font-bold flex items-center gap-1">
                <Radio className="w-2.5 h-2.5 animate-pulse" /> LIVE RADIO
              </span>
            </div>

            <div className="mt-3 space-y-2.5 max-h-72 overflow-y-auto pr-1">
              {/* Real-time Streaming Peer Packets */}
              {liveComms.map((packet) => (
                <div
                  key={packet.id}
                  className="p-2 rounded bg-botanical/10 border border-secondary-green/30 text-[11px] space-y-1 animate-fade-in"
                >
                  <div className="flex items-center justify-between text-[10px] font-mono text-forest-green font-bold">
                    <span className="flex items-center gap-1">
                      <Radio className="w-2.5 h-2.5 text-secondary-green" />
                      {packet.sender} → {packet.receiver}
                    </span>
                    <span className="text-[9px] text-secondary-text font-normal">{packet.time}</span>
                  </div>
                  <p className="text-[10px] text-forest-green leading-tight font-mono">
                    {packet.message}
                  </p>
                </div>
              ))}

              {/* Historical Logs */}
              {agentComms.map((log) => {
                const nodeName = log.agent_id ? formatAgentName(log.agent_id) : "FLEET MESH";
                return (
                  <div
                    key={log.id}
                    className="text-[11px] border-b border-border/60 pb-2 last:border-0 last:pb-0"
                  >
                    <div className="flex items-center justify-between text-[10px] text-secondary-text mb-0.5">
                      <span className="font-mono text-forest-green font-semibold">
                        {nodeName}
                      </span>
                      <span className="font-mono text-[9px]">
                        {log.timestamp ? log.timestamp.split("T")[1]?.slice(0, 8) : "just now"}
                      </span>
                    </div>
                    <p className="text-forest-green text-[11px] leading-tight font-serif">
                      {log.title}
                    </p>
                  </div>
                );
              })}
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
