"use client";

import { useEffect, useState, useMemo } from "react";
import { api } from "@/lib/api";
import { Incident, Agent, CommunicationPacket, ResolutionReport, AgentHealthBreakdown } from "@/lib/types";
import {
  Flame,
  Wind,
  Thermometer,
  ShieldAlert,
  CheckCircle2,
  Users,
  ShieldCheck,
  Clock,
  Play,
  Activity,
  Compass,
  Check,
  AlertTriangle,
  Radio,
  Battery,
  Heart,
  Zap,
  Crosshair,
  MapPin,
  Sparkles,
  RefreshCw,
  Send,
  ArrowRight,
  Sliders,
  ChevronRight,
  Info
} from "lucide-react";
import { getEventCoordinates } from "@/components/LiveMonitoringMap";

const SECTOR_PRESETS = [
  { name: "North Ridge Transect", x: 10, y: 16, desc: "High elevation alpine canopy & pine forest" },
  { name: "South Lowland Scrub", x: 10, y: 4, desc: "Dry vegetative shrubland with high flammability" },
  { name: "West Wetland Sanctuary", x: 4, y: 10, desc: "Riparian marshes & moist ecological basin" },
  { name: "East Alpine Forest", x: 16, y: 10, desc: "Dense coniferous forest & migratory wildlife corridor" },
  { name: "Central Riparian River Basin", x: 10, y: 10, desc: "Central monitoring hub & river confluence" },
];

export default function IncidentManagementPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [actionNotice, setActionNotice] = useState<string>("");

  // Area Selection State
  const [selectionMode, setSelectionMode] = useState<"SECTOR" | "AGENT" | "COORDINATES">("SECTOR");
  const [selectedSector, setSelectedSector] = useState<string>("Central Riparian River Basin");
  const [selectedCenterAgentId, setSelectedCenterAgentId] = useState<string>("");
  const [params, setParams] = useState({
    center_x: 10,
    center_y: 10,
    radius: 3,
  });

  // Resolution simulation state
  const [resolvingStep, setResolvingStep] = useState<number>(0);
  const [resolutionResult, setResolutionResult] = useState<ResolutionReport | null>(null);
  const [activeTab, setActiveTab] = useState<"COMMUNICATIONS" | "HEALTH_ASSESSMENT" | "INCIDENT_DETAILS">("COMMUNICATIONS");

  const fetchData = async () => {
    try {
      const [eventsData, agentsData] = await Promise.all([
        api.getEvents(),
        api.getAgents(),
      ]);
      setIncidents(eventsData);
      setAgents(agentsData);

      if (eventsData.length > 0 && !selectedIncident) {
        setSelectedIncident(eventsData[0]);
        if (eventsData[0].resolution_report) {
          setResolutionResult(eventsData[0].resolution_report);
        }
      } else if (selectedIncident) {
        const found = eventsData.find((i) => i.event_id === selectedIncident.event_id);
        if (found) {
          setSelectedIncident(found);
          if (found.resolution_report && !resolutionResult) {
            setResolutionResult(found.resolution_report);
          }
        }
      }
    } catch (err) {
      console.error("Failed to fetch incidents or agents:", err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update center_x and center_y when sector or center agent changes
  const handleSelectSector = (sectorName: string) => {
    setSelectedSector(sectorName);
    const sector = SECTOR_PRESETS.find((s) => s.name === sectorName);
    if (sector) {
      setParams((prev) => ({ ...prev, center_x: sector.x, center_y: sector.y }));
    }
  };

  const handleSelectCenterAgent = (agentId: string) => {
    setSelectedCenterAgentId(agentId);
    const ag = agents.find((a) => a.id === agentId);
    if (ag && ag.position) {
      setParams((prev) => ({ ...prev, center_x: ag.position[0], center_y: ag.position[1] }));
    }
  };

  // Preview agents that fall within the selected area & radius
  const agentsInSelectedPerimeter = useMemo(() => {
    return agents.filter((ag) => {
      if (!ag.position) return false;
      const dist = Math.abs(ag.position[0] - params.center_x) + Math.abs(ag.position[1] - params.center_y);
      return dist <= params.radius;
    });
  }, [agents, params]);

  const handleTrigger = async (type: "FIRE" | "POLLUTION" | "EXTREME_HEAT") => {
    setLoading(true);
    setResolutionResult(null);
    try {
      const payload = {
        center_x: params.center_x,
        center_y: params.center_y,
        radius: params.radius,
        target_agent_id: selectionMode === "AGENT" && selectedCenterAgentId ? selectedCenterAgentId : undefined,
        zone_name: selectionMode === "SECTOR" ? selectedSector : undefined,
      };

      let res: Incident;
      if (type === "FIRE") res = await api.createFireEvent(payload);
      else if (type === "POLLUTION") res = await api.createPollutionEvent(payload);
      else res = await api.createExtremeHeatEvent(payload);

      setSelectedIncident(res);
      setActiveTab("COMMUNICATIONS");
      setActionNotice(`🚨 ${type} incident triggered at (${params.center_x}, ${params.center_y})! Peer alert broadcast & neighbor consensus reached.`);
      setTimeout(() => setActionNotice(""), 4500);
      await fetchData();
    } catch (e: any) {
      alert(`Failed to trigger ${type}: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (eventId: string) => {
    try {
      await api.acknowledgeEvent(eventId);
      setActionNotice(`Incident ${eventId} acknowledged by field operator.`);
      setTimeout(() => setActionNotice(""), 3500);
      fetchData();
    } catch (e: any) {
      alert(`Acknowledgment failed: ${e.message}`);
    }
  };

  const handleResolve = async (eventId: string) => {
    setLoading(true);
    setResolvingStep(1);

    // Step 1: Alert convergence animation
    setTimeout(async () => {
      setResolvingStep(2);
      // Step 2: Suppression payload
      setTimeout(async () => {
        setResolvingStep(3);
        // Step 3: Sensor normalization
        setTimeout(async () => {
          setResolvingStep(4);
          try {
            const result = await api.resolveEvent(eventId);
            if (result.resolution_report) {
              setResolutionResult(result.resolution_report);
            }
            setActiveTab("HEALTH_ASSESSMENT");
            setActionNotice(`Incident ${eventId} neutralized. Post-hazard fleet health assessment completed.`);
            setTimeout(() => setActionNotice(""), 5000);
            await fetchData();
          } catch (e: any) {
            alert(`Resolution failed: ${e.message}`);
          } finally {
            setResolvingStep(0);
            setLoading(false);
          }
        }, 900);
      }, 900);
    }, 900);
  };

  const handleRechargeFleet = async () => {
    setLoading(true);
    try {
      const res = await api.rechargeFleet();
      setActionNotice(res.message);
      setTimeout(() => setActionNotice(""), 4000);
      await fetchData();
    } catch (e: any) {
      alert(`Recharge failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="border-b border-border pb-5">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="editorial-tag text-secondary-text mb-1 tracking-widest flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-forest-green animate-pulse" />
              AUTONOMOUS ANOMALY VERIFICATION & DECENTRALIZED CONSENSUS
            </div>
            <h1 className="editorial-title text-3xl md:text-4xl font-serif font-bold text-forest-green tracking-tight leading-none">
              Incident Management & Mitigation.
            </h1>
            <p className="mt-2 text-sm text-secondary-text max-w-3xl leading-relaxed">
              Target environmental hazard areas across the transect. Observe how autonomous edge nodes detect anomalies, 
              broadcast peer-to-peer radio alerts, form neighbor consensus, coordinate autonomous suppression, and report post-hazard health.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleRechargeFleet}
              disabled={loading}
              className="px-3 py-1.5 rounded bg-muted-sage hover:bg-forest-green/15 text-forest-green border border-border text-xs font-mono flex items-center gap-1.5 transition"
              title="Replenish all agents' battery to 100% and recalibrate sensors"
            >
              <Zap className="w-3.5 h-3.5 text-secondary-green" />
              Recharge Fleet
            </button>

            <div className="flex items-center gap-2 text-xs font-mono text-secondary-text bg-surface px-3 py-1.5 rounded border border-border">
              <span>ACTIVE HAZARDS:</span>
              <span className="font-bold text-critical-incident">
                {incidents.filter((i) => i.status === "ACTIVE").length}
              </span>
            </div>
          </div>
        </div>
      </div>

      {actionNotice && (
        <div className="p-3 bg-muted-sage text-forest-green rounded border border-border text-xs font-mono flex items-center justify-between shadow-sm animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-secondary-green shrink-0" />
            <span>{actionNotice}</span>
          </div>
          <button onClick={() => setActionNotice("")} className="text-secondary-text hover:text-forest-green">✕</button>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SECTION 1: TARGET AREA SELECTION & HAZARD TRIGGER PANEL                  */}
      {/* ========================================================================= */}
      <div className="bg-surface border border-border rounded-lg p-5 shadow-editorial space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b border-border gap-2">
          <div className="flex items-center gap-2">
            <Crosshair className="w-4 h-4 text-forest-green" />
            <h2 className="font-serif font-bold text-base text-forest-green">
              1. Select Area of Incident to Occur
            </h2>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center gap-1 bg-surface-muted p-1 rounded border border-border text-xs font-mono">
            <button
              onClick={() => setSelectionMode("SECTOR")}
              className={`px-3 py-1 rounded transition ${
                selectionMode === "SECTOR"
                  ? "bg-forest-green text-surface font-semibold shadow-xs"
                  : "text-secondary-text hover:text-forest-green"
              }`}
            >
              Ecological Sector
            </button>
            <button
              onClick={() => setSelectionMode("AGENT")}
              className={`px-3 py-1 rounded transition ${
                selectionMode === "AGENT"
                  ? "bg-forest-green text-surface font-semibold shadow-xs"
                  : "text-secondary-text hover:text-forest-green"
              }`}
            >
              Agent Epicenter
            </button>
            <button
              onClick={() => setSelectionMode("COORDINATES")}
              className={`px-3 py-1 rounded transition ${
                selectionMode === "COORDINATES"
                  ? "bg-forest-green text-surface font-semibold shadow-xs"
                  : "text-secondary-text hover:text-forest-green"
              }`}
            >
              Grid Sliders (X/Y)
            </button>
          </div>
        </div>

        {/* Mode A: Sector Presets */}
        {selectionMode === "SECTOR" && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
            {SECTOR_PRESETS.map((s) => {
              const isSelected = selectedSector === s.name;
              return (
                <button
                  key={s.name}
                  onClick={() => handleSelectSector(s.name)}
                  className={`p-2.5 rounded border text-left transition flex flex-col justify-between ${
                    isSelected
                      ? "border-forest-green bg-muted-sage/60 ring-1 ring-forest-green"
                      : "border-border bg-surface-muted hover:border-secondary-green/50"
                  }`}
                >
                  <div>
                    <div className="font-mono font-bold text-xs text-forest-green">{s.name}</div>
                    <div className="text-[10px] text-secondary-text mt-1 leading-tight">{s.desc}</div>
                  </div>
                  <div className="mt-2 text-[9px] font-mono text-secondary-text/80 flex items-center justify-between">
                    <span>X: {s.x}, Y: {s.y}</span>
                    {isSelected && <span className="text-secondary-green font-bold">✓ SELECTED</span>}
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {/* Mode B: Agent Epicenter Picker */}
        {selectionMode === "AGENT" && (
          <div className="space-y-2">
            <span className="text-xs text-secondary-text block">
              Choose an active agent to anchor the incident epicenter:
            </span>
            <div className="grid grid-cols-5 sm:grid-cols-10 gap-1.5">
              {agents.map((ag) => {
                const isSelected = selectedCenterAgentId === ag.id;
                return (
                  <button
                    key={ag.id}
                    onClick={() => handleSelectCenterAgent(ag.id)}
                    className={`py-1.5 px-2 rounded font-mono text-xs text-center border transition ${
                      isSelected
                        ? "bg-forest-green text-surface font-bold border-forest-green shadow-xs"
                        : "bg-surface-muted text-forest-green border-border hover:border-secondary-green/60"
                    }`}
                  >
                    {ag.id}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Mode C: Sliders for Coordinates & Radius */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t border-border/60">
          <div>
            <div className="flex justify-between text-xs font-mono mb-1">
              <span className="text-secondary-text">Epicenter Grid X:</span>
              <span className="font-bold text-forest-green">{params.center_x} / 20</span>
            </div>
            <input
              type="range"
              min={0}
              max={20}
              value={params.center_x}
              onChange={(e) => setParams({ ...params, center_x: parseInt(e.target.value) })}
              className="w-full accent-forest-green cursor-pointer"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs font-mono mb-1">
              <span className="text-secondary-text">Epicenter Grid Y:</span>
              <span className="font-bold text-forest-green">{params.center_y} / 20</span>
            </div>
            <input
              type="range"
              min={0}
              max={20}
              value={params.center_y}
              onChange={(e) => setParams({ ...params, center_y: parseInt(e.target.value) })}
              className="w-full accent-forest-green cursor-pointer"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs font-mono mb-1">
              <span className="text-secondary-text">Hazard Radius:</span>
              <span className="font-bold text-forest-green">{params.radius} units ({params.radius * 650}m)</span>
            </div>
            <input
              type="range"
              min={1}
              max={6}
              value={params.radius}
              onChange={(e) => setParams({ ...params, radius: parseInt(e.target.value) })}
              className="w-full accent-forest-green cursor-pointer"
            />
          </div>
        </div>

        {/* Selected Area Target HUD & Blast Zone Preview */}
        <div className="p-3 bg-surface-muted rounded border border-border flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-forest-green/10 text-forest-green flex items-center justify-center font-bold">
              ◎
            </div>
            <div>
              <span className="text-secondary-text text-[10px] block">CURRENT TARGET EPICENTER</span>
              <span className="text-forest-green font-bold">
                ({params.center_x}, {params.center_y}) — {selectedSector}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-secondary-text text-[11px]">
              Proximate Nodes in Blast Zone ({agentsInSelectedPerimeter.length}):
            </span>
            {agentsInSelectedPerimeter.length > 0 ? (
              agentsInSelectedPerimeter.map((ag) => (
                <span
                  key={ag.id}
                  className="px-1.5 py-0.5 rounded bg-forest-green/10 text-forest-green font-bold text-[10px] border border-forest-green/20"
                >
                  {ag.id}
                </span>
              ))
            ) : (
              <span className="text-warning-amber text-[10px] italic">No agents within radius</span>
            )}
          </div>
        </div>

        {/* Trigger Action Buttons */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
          {/* Wildfire */}
          <button
            onClick={() => handleTrigger("FIRE")}
            disabled={loading}
            className="p-3 rounded bg-critical-incident/10 hover:bg-critical-incident/15 text-critical-incident border border-critical-incident/40 font-mono text-xs flex items-center justify-center gap-2 transition font-bold"
          >
            <Flame className="w-4 h-4 text-critical-incident animate-bounce" />
            Simulate Wildfire at Area
          </button>

          {/* Pollution */}
          <button
            onClick={() => handleTrigger("POLLUTION")}
            disabled={loading}
            className="p-3 rounded bg-warning-amber/10 hover:bg-warning-amber/15 text-warning-amber border border-warning-amber/40 font-mono text-xs flex items-center justify-center gap-2 transition font-bold"
          >
            <Wind className="w-4 h-4 text-warning-amber" />
            Simulate Pollution at Area
          </button>

          {/* Extreme Heat */}
          <button
            onClick={() => handleTrigger("EXTREME_HEAT")}
            disabled={loading}
            className="p-3 rounded bg-forest-green/10 hover:bg-forest-green/15 text-forest-green border border-forest-green/40 font-mono text-xs flex items-center justify-center gap-2 transition font-bold"
          >
            <Thermometer className="w-4 h-4 text-forest-green" />
            Simulate Heatwave at Area
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* SECTION 2 & 3: COMMUNICATION, RESOLUTION & POST-HAZARD HEALTH             */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Interactive Incident Inspector & Protocol Views (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {selectedIncident ? (
            <div className="bg-surface border border-border rounded-lg shadow-editorial overflow-hidden">
              {/* Incident Header Banner */}
              <div className="p-4 bg-surface-muted border-b border-border flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-sm text-forest-green">
                      {selectedIncident.event_type} INCIDENT
                    </span>
                    <span className="text-xs font-mono text-secondary-text">({selectedIncident.event_id})</span>
                    <span
                      className={`text-[9px] font-mono px-2 py-0.5 rounded font-bold ${
                        selectedIncident.status === "ACTIVE"
                          ? "bg-critical-incident/15 text-critical-incident animate-pulse"
                          : "bg-muted-sage text-forest-green"
                      }`}
                    >
                      {selectedIncident.status}
                    </span>
                  </div>
                  <div className="text-xs text-secondary-text mt-0.5">
                    Sector: {selectedIncident.zone_name || "Cascade Transect"} • Epicenter: ({selectedIncident.location.x}, {selectedIncident.location.y})
                  </div>
                </div>

                {/* Resolve Action Button */}
                {selectedIncident.status === "ACTIVE" && (
                  <button
                    onClick={() => handleResolve(selectedIncident.event_id)}
                    disabled={loading || resolvingStep > 0}
                    className="px-4 py-2 rounded bg-forest-green hover:bg-forest-green-light text-surface font-mono text-xs font-bold transition shadow-sm flex items-center gap-2"
                  >
                    <Sparkles className="w-4 h-4 text-secondary-green" />
                    {resolvingStep > 0 ? "Resolving..." : "Resolve Hazard"}
                  </button>
                )}
              </div>

              {/* Resolving Progress Stepper (Animated) */}
              {resolvingStep > 0 && (
                <div className="p-4 bg-muted-sage/40 border-b border-border space-y-2 animate-in fade-in">
                  <div className="flex items-center justify-between text-xs font-mono text-forest-green font-bold">
                    <span>⚡ Autonomous Hazard Suppression In Progress...</span>
                    <span>Phase {resolvingStep} of 4</span>
                  </div>
                  <div className="w-full bg-border h-2 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-secondary-green transition-all duration-500 rounded-full"
                      style={{ width: `${resolvingStep * 25}%` }}
                    />
                  </div>
                  <div className="text-[11px] text-secondary-text font-mono">
                    {resolvingStep === 1 && "1/4: Forming localized mitigation cluster & electing leader..."}
                    {resolvingStep === 2 && "2/4: Drones deploying aerosol cooling & particulate filtration..."}
                    {resolvingStep === 3 && "3/4: Field telemetry normalizing back to baseline (28°C)..."}
                    {resolvingStep === 4 && "4/4: Assessing post-hazard battery draw & sensor health on all nodes..."}
                  </div>
                </div>
              )}

              {/* View Tabs */}
              <div className="flex border-b border-border text-xs font-mono bg-surface">
                <button
                  onClick={() => setActiveTab("COMMUNICATIONS")}
                  className={`flex-1 py-2.5 px-3 text-center border-b-2 transition flex items-center justify-center gap-1.5 ${
                    activeTab === "COMMUNICATIONS"
                      ? "border-forest-green text-forest-green font-bold bg-surface-muted/40"
                      : "border-transparent text-secondary-text hover:text-forest-green"
                  }`}
                >
                  <Radio className="w-3.5 h-3.5" />
                  Peer Communications ({selectedIncident.communications?.length || 4})
                </button>

                <button
                  onClick={() => setActiveTab("HEALTH_ASSESSMENT")}
                  className={`flex-1 py-2.5 px-3 text-center border-b-2 transition flex items-center justify-center gap-1.5 ${
                    activeTab === "HEALTH_ASSESSMENT"
                      ? "border-forest-green text-forest-green font-bold bg-surface-muted/40"
                      : "border-transparent text-secondary-text hover:text-forest-green"
                  }`}
                >
                  <Heart className="w-3.5 h-3.5 text-critical-incident" />
                  Post-Hazard Agent Health
                </button>

                <button
                  onClick={() => setActiveTab("INCIDENT_DETAILS")}
                  className={`flex-1 py-2.5 px-3 text-center border-b-2 transition flex items-center justify-center gap-1.5 ${
                    activeTab === "INCIDENT_DETAILS"
                      ? "border-forest-green text-forest-green font-bold bg-surface-muted/40"
                      : "border-transparent text-secondary-text hover:text-forest-green"
                  }`}
                >
                  <Info className="w-3.5 h-3.5" />
                  Consensus Quorum
                </button>
              </div>

              {/* Tab 1: Live Peer-to-Peer Agent Communications */}
              {activeTab === "COMMUNICATIONS" && (
                <div className="p-4 space-y-3">
                  <div className="flex items-center justify-between text-xs text-secondary-text">
                    <span className="font-mono">P2P RADIO TRANSMISSION TRACE</span>
                    <span className="font-mono text-[10px]">P2P MESH BROADCAST</span>
                  </div>

                  <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
                    {(selectedIncident.communications && selectedIncident.communications.length > 0
                      ? selectedIncident.communications
                      : [
                          {
                            id: "PKT-001",
                            timestamp: "12:00:01",
                            step: 1,
                            sender_id: selectedIncident.affected_agents[0] || "A5",
                            receiver_id: "LOCAL_INFERENCE_CORE",
                            type: "ANOMALY_EVALUATION",
                            content: `Isolation Forest flagged ${selectedIncident.event_type} anomaly. Ambient parameters exceeded normal threshold.`,
                            vote: "ANOMALY_CONFIRMED",
                            confidence: 0.88,
                          },
                          {
                            id: "PKT-002",
                            timestamp: "12:00:02",
                            step: 2,
                            sender_id: selectedIncident.affected_agents[0] || "A5",
                            receiver_id: selectedIncident.affected_agents[1] || "A6",
                            type: "ENVIRONMENTAL_ALERT",
                            content: `Broadcast ${selectedIncident.event_type} alert packet to active neighbor. Requesting corroboration.`,
                            vote: "ALERT_TRANSMITTED",
                            confidence: 0.85,
                          },
                          {
                            id: "PKT-003",
                            timestamp: "12:00:03",
                            step: 3,
                            sender_id: selectedIncident.affected_agents[1] || "A6",
                            receiver_id: selectedIncident.affected_agents[0] || "A5",
                            type: "CONSENSUS_VOTE",
                            content: `Neighbor verified elevated temperature and smoke particulates. Voted AGREE_HAZARD.`,
                            vote: "AGREE_HAZARD",
                            confidence: 0.92,
                          },
                          {
                            id: "PKT-004",
                            timestamp: "12:00:04",
                            step: 4,
                            sender_id: "P2P_MESH_QUORUM",
                            receiver_id: "FLEET_BROADCAST",
                            type: "CONSENSUS_COMMIT",
                            content: `Decentralized neighbor consensus confirmed ${selectedIncident.event_type} with ${Math.round(selectedIncident.confidence * 100)}% confidence.`,
                            vote: "HAZARD_VERIFIED",
                            confidence: selectedIncident.confidence,
                          },
                        ]
                    ).map((pkt: any, i: number) => (
                      <div
                        key={pkt.id || i}
                        className="p-3 bg-surface-muted rounded border border-border text-xs font-mono space-y-1 hover:border-forest-green/40 transition"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="px-1.5 py-0.2 rounded bg-forest-green text-surface font-bold text-[10px]">
                              {pkt.sender_id}
                            </span>
                            <ArrowRight className="w-3 h-3 text-secondary-text" />
                            <span className="px-1.5 py-0.2 rounded bg-secondary-green/20 text-forest-green font-bold text-[10px]">
                              {pkt.receiver_id}
                            </span>
                          </div>
                          <span className="text-[10px] text-secondary-text">{pkt.timestamp || `T+${i}s`}</span>
                        </div>

                        <p className="text-xs text-forest-green leading-relaxed pt-1">
                          {pkt.content}
                        </p>

                        <div className="flex items-center justify-between text-[10px] text-secondary-text pt-1 border-t border-border/50">
                          <span className="font-semibold text-forest-green">
                            TOKEN: {pkt.vote || "VERIFIED"}
                          </span>
                          <span>Confidence: {Math.round((pkt.confidence || 0.85) * 100)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 2: Post-Hazard Agent Health Assessment */}
              {activeTab === "HEALTH_ASSESSMENT" && (
                <div className="p-4 space-y-4">
                  {resolutionResult ? (
                    <div className="space-y-4">
                      {/* Summary Banner */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs font-mono">
                        <div className="p-2.5 bg-surface-muted rounded border border-border">
                          <span className="text-[10px] text-secondary-text block">AVG FLEET HEALTH</span>
                          <span className="text-base font-bold text-forest-green">
                            {resolutionResult.fleet_health_summary.average_health_score}%
                          </span>
                        </div>
                        <div className="p-2.5 bg-surface-muted rounded border border-border">
                          <span className="text-[10px] text-secondary-text block">AVG FLEET BATTERY</span>
                          <span className="text-base font-bold text-forest-green">
                            {resolutionResult.fleet_health_summary.average_battery_level}%
                          </span>
                        </div>
                        <div className="p-2.5 bg-surface-muted rounded border border-border">
                          <span className="text-[10px] text-secondary-text block">RESPONDERS</span>
                          <span className="text-base font-bold text-critical-incident">
                            {resolutionResult.fleet_health_summary.total_responders_count} Agents
                          </span>
                        </div>
                        <div className="p-2.5 bg-surface-muted rounded border border-border">
                          <span className="text-[10px] text-secondary-text block">TOTAL POWER DRAW</span>
                          <span className="text-base font-bold text-warning-amber">
                            -{resolutionResult.fleet_health_summary.total_battery_expended_pct}% kWh
                          </span>
                        </div>
                      </div>

                      {/* Agent Breakdown List */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs font-mono text-secondary-text">
                          <span>AGENT HEALTH & BATTERY POST-MITIGATION AUDIT</span>
                          <button
                            onClick={handleRechargeFleet}
                            className="text-xs text-forest-green hover:underline flex items-center gap-1 font-bold"
                          >
                            <Zap className="w-3 h-3 text-secondary-green" /> Recharge Fleet
                          </button>
                        </div>

                        <div className="max-h-[340px] overflow-y-auto space-y-2 pr-1">
                          {resolutionResult.agent_health_breakdown.map((item) => (
                            <div
                              key={item.agent_id}
                              className="p-3 bg-surface-muted rounded border border-border text-xs space-y-2"
                            >
                              <div className="flex items-center justify-between font-mono">
                                <div className="flex items-center gap-2">
                                  <span className="font-bold text-forest-green text-sm">{item.agent_id}</span>
                                  <span
                                    className={`text-[9px] px-1.5 py-0.2 rounded font-bold ${
                                      item.role === "PRIMARY_RESPONDER"
                                        ? "bg-critical-incident/15 text-critical-incident"
                                        : item.role === "ZONE_DETECTOR"
                                        ? "bg-warning-amber/15 text-warning-amber"
                                        : item.role === "RELAY_NEIGHBOR"
                                        ? "bg-secondary-green/20 text-forest-green"
                                        : "bg-surface text-secondary-text"
                                    }`}
                                  >
                                    {item.role}
                                  </span>
                                </div>

                                <div className="text-[10px] text-secondary-text">
                                  Wear: <span className="font-semibold text-forest-green">{item.thermal_wear}</span>
                                </div>
                              </div>

                              {/* Progress Bars for Health and Battery */}
                              <div className="grid grid-cols-2 gap-3 text-[11px] font-mono">
                                <div>
                                  <div className="flex justify-between text-secondary-text mb-0.5">
                                    <span>Battery:</span>
                                    <span className="text-forest-green font-bold">
                                      {item.battery_after}%{" "}
                                      <span className="text-critical-incident text-[10px]">({item.battery_delta}%)</span>
                                    </span>
                                  </div>
                                  <div className="w-full bg-border h-1.5 rounded-full overflow-hidden">
                                    <div
                                      className={`h-full rounded-full ${
                                        item.battery_after < 50 ? "bg-warning-amber" : "bg-forest-green"
                                      }`}
                                      style={{ width: `${item.battery_after}%` }}
                                    />
                                  </div>
                                </div>

                                <div>
                                  <div className="flex justify-between text-secondary-text mb-0.5">
                                    <span>Health:</span>
                                    <span className="text-forest-green font-bold">
                                      {item.health_after}%{" "}
                                      {item.health_delta !== 0 && (
                                        <span className="text-critical-incident text-[10px]">({item.health_delta}%)</span>
                                      )}
                                    </span>
                                  </div>
                                  <div className="w-full bg-border h-1.5 rounded-full overflow-hidden">
                                    <div
                                      className="h-full bg-secondary-green rounded-full"
                                      style={{ width: `${item.health_after}%` }}
                                    />
                                  </div>
                                </div>
                              </div>

                              <p className="text-[11px] text-secondary-text italic pt-1 border-t border-border/50">
                                {item.diagnosis}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="p-8 text-center text-xs text-secondary-text font-serif italic bg-surface-muted rounded border border-border">
                      <p>This incident is still actively hazarding the area.</p>
                      <p className="mt-1">
                        Click <strong className="text-forest-green">"Resolve Hazard"</strong> above to trigger autonomous suppression and view the post-hazard health impact of each agent.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 3: Consensus Details */}
              {activeTab === "INCIDENT_DETAILS" && (
                <div className="p-4 space-y-3 text-xs">
                  <div className="p-3 bg-surface-muted rounded border border-border space-y-1.5 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-secondary-text">Consensus Quorum:</span>
                      <span className="text-forest-green font-bold">
                        {selectedIncident.consensus_state} ({Math.round(selectedIncident.confidence * 100)}%)
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-secondary-text">Agreement Distribution:</span>
                      <span className="text-forest-green">
                        {selectedIncident.detecting_count} of {selectedIncident.affected_count} proximate nodes confirmed
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-secondary-text">Blast Radius:</span>
                      <span className="text-forest-green">
                        {selectedIncident.radius * 650} meters ({selectedIncident.radius} grid units)
                      </span>
                    </div>
                  </div>

                  <div>
                    <span className="text-[10px] font-mono text-secondary-text block mb-1">
                      AFFECTED SENSOR NODES:
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {(selectedIncident.affected_agents || []).map((id) => (
                        <span
                          key={id}
                          className="px-2 py-0.5 rounded bg-surface-muted border border-border text-forest-green font-mono text-[10px] font-bold"
                        >
                          {id}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-surface p-12 rounded border border-border text-center text-xs text-secondary-text font-serif italic shadow-editorial">
              Select or trigger an incident above to review live multi-agent communication and post-hazard health.
            </div>
          )}
        </div>

        {/* Right Column: Historical Incidents Archive (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-border">
            <span className="editorial-tag text-[9px] text-secondary-text">
              CHRONOLOGICAL INCIDENT ARCHIVE
            </span>
            <span className="text-xs font-mono text-secondary-text">
              {incidents.length} Records Logged
            </span>
          </div>

          <div className="space-y-2 max-h-[640px] overflow-y-auto pr-1">
            {incidents.length === 0 ? (
              <div className="bg-surface p-8 rounded border border-border text-center text-xs text-secondary-text font-serif italic shadow-editorial">
                No incidents recorded yet. Trigger one above to observe the system!
              </div>
            ) : (
              incidents.map((evt) => {
                const isSelected = selectedIncident?.event_id === evt.event_id;
                return (
                  <div
                    key={evt.event_id}
                    onClick={() => {
                      setSelectedIncident(evt);
                      if (evt.resolution_report) {
                        setResolutionResult(evt.resolution_report);
                      }
                    }}
                    className={`bg-surface p-3.5 rounded border transition shadow-editorial cursor-pointer ${
                      isSelected
                        ? "border-forest-green bg-surface-muted/60 ring-1 ring-forest-green"
                        : "border-border hover:border-secondary-green/40"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-xs text-forest-green">
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
                      </div>

                      <span className="text-[10px] font-mono text-secondary-text">
                        {evt.timestamp ? evt.timestamp.split("T")[0] : ""}
                      </span>
                    </div>

                    <p className="text-xs text-secondary-text leading-snug mb-2">
                      {evt.zone_name || "Cascade Transect"} ({evt.affected_count} nodes in blast zone).
                    </p>

                    <div className="flex items-center justify-between text-[10px] font-mono text-secondary-text pt-1.5 border-t border-border">
                      <span className="text-forest-green font-medium">
                        Consensus: {Math.round(evt.confidence * 100)}%
                      </span>
                      <span>ID: {evt.event_id}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
