"use client";

import { useEffect, useState, useMemo } from "react";
import { api } from "@/lib/api";
import { Agent } from "@/lib/types";
import AgentDetailModal from "@/components/AgentDetailModal";
import { getAgentCoordinates } from "@/components/LiveMonitoringMap";
import {
  Cpu,
  Plus,
  Search,
  Filter,
  Sliders,
  Battery,
  Heart,
  Wifi,
  Shield,
  PowerOff,
  CheckCircle,
  Eye,
  RefreshCw,
  Download,
  RotateCcw,
  Compass,
  AlertTriangle,
  Play
} from "lucide-react";

export default function AgentOperationsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [filter, setFilter] = useState<string>("ALL");
  const [search, setSearch] = useState<string>("");
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [actionNotice, setActionNotice] = useState<string>("");

  // New Agent Form State
  const [newAgent, setNewAgent] = useState({
    id: "",
    x: 10,
    y: 10,
    temperature: 28,
    humidity: 60,
    smoke: 0.1,
    co2: 420,
    air_quality: 50,
    soil_moisture: 55,
    battery: 100,
  });

  const fetchAgents = async () => {
    try {
      const data = await api.getAgents();
      setAgents(data);
      if (selectedAgent) {
        const updated = data.find((a) => a.id === selectedAgent.id);
        if (updated) setSelectedAgent(updated);
      }
    } catch (err) {
      console.error("Failed to fetch agents:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
    const interval = setInterval(fetchAgents, 3000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCreateAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createAgent(newAgent);
      setShowAddModal(false);
      setNewAgent({
        id: "",
        x: 10,
        y: 10,
        temperature: 28,
        humidity: 60,
        smoke: 0.1,
        co2: 420,
        air_quality: 50,
        soil_moisture: 55,
        battery: 100,
      });
      setActionNotice("New autonomous node deployed to transect mesh.");
      setTimeout(() => setActionNotice(""), 3500);
      fetchAgents();
    } catch (err: any) {
      alert(`Agent deployment failed: ${err.message}`);
    }
  };

  const handleToggleFail = async (agent: Agent) => {
    try {
      if (agent.status === "ACTIVE") {
        await api.failAgent(agent.id);
        setActionNotice(`Node ${agent.id} simulated as FAILED`);
      } else {
        await api.restoreAgent(agent.id);
        setActionNotice(`Node ${agent.id} signal restored to ACTIVE`);
      }
      setTimeout(() => setActionNotice(""), 3500);
      fetchAgents();
    } catch (e: any) {
      alert(`Action failed: ${e.message}`);
    }
  };

  const handleRestart = async (agentId: string) => {
    try {
      await api.restartAgent(agentId);
      setActionNotice(`Node ${agentId} rebooted and recalibrated.`);
      setTimeout(() => setActionNotice(""), 3500);
      fetchAgents();
    } catch (e: any) {
      alert(`Reboot failed: ${e.message}`);
    }
  };

  const handleStepPatrol = async () => {
    try {
      await api.stepPatrol();
      setActionNotice("Drone patrol stepped across grid transect.");
      setTimeout(() => setActionNotice(""), 3500);
      fetchAgents();
    } catch (e: any) {
      alert(`Patrol step failed: ${e.message}`);
    }
  };

  const handleExportCSV = () => {
    const headers =
      "id,type,assignment,status,latitude,longitude,zone,battery,health,connectivity,reliability,temperature,humidity,smoke,co2,air_quality,soil_moisture,event\n";
    const rows = filteredAgents
      .map((a) => {
        const [lat, lng] = getAgentCoordinates(a);
        return (
          `"${a.id}","${a.agent_type || "Sensor Node"}","${(a.assignment || "").replace(/"/g, '""')}","${a.status}",` +
          `${lat},${lng},"${a.zone || "Transect"}",${a.battery},${a.health},` +
          `${a.connectivity},${a.reliability},${a.readings?.temperature ?? 28},${a.readings?.humidity ?? 60},` +
          `${a.readings?.smoke ?? 0.1},${a.readings?.co2 ?? 420},${a.readings?.air_quality ?? 50},${a.readings?.soil_moisture ?? 55},` +
          `"${a.ai_result?.event || "None"}"`
        );
      })
      .join("\n");

    const blob = new Blob([headers + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `cascade-transect-fleet-${new Date().toISOString().split("T")[0]}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const filteredAgents = useMemo(() => {
    return agents.filter((a) => {
      const isAnomalous = a.ai_result?.status === "ANOMALY";
      const isWarning =
        !isAnomalous &&
        (a.battery < 30 ||
          a.readings?.temperature > 35 ||
          a.readings?.smoke > 0.25 ||
          a.readings?.co2 > 650);

      if (filter === "ACTIVE" && a.status !== "ACTIVE") return false;
      if (filter === "OFFLINE" && a.status !== "FAILED") return false;
      if (filter === "ANOMALIES" && !isAnomalous) return false;
      if (filter === "WARNINGS" && !isWarning) return false;

      if (search) {
        const q = search.toLowerCase();
        return (
          a.id.toLowerCase().includes(q) ||
          (a.agent_type && a.agent_type.toLowerCase().includes(q)) ||
          (a.zone && a.zone.toLowerCase().includes(q)) ||
          (a.assignment && a.assignment.toLowerCase().includes(q))
        );
      }
      return true;
    });
  }, [agents, filter, search]);

  const activeCount = agents.filter((a) => a.status === "ACTIVE").length;
  const offlineCount = agents.filter((a) => a.status === "FAILED").length;
  const anomalyCount = agents.filter((a) => a.ai_result?.status === "ANOMALY").length;
  const warningCount = agents.filter(
    (a) =>
      a.ai_result?.status !== "ANOMALY" &&
      (a.battery < 30 || a.readings?.temperature > 35 || a.readings?.smoke > 0.25)
  ).length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-border pb-5">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="editorial-tag text-secondary-text mb-1 tracking-widest">
              FLEET TELEMETRY & FIELD INVENTORY
            </div>
            <h1 className="editorial-title text-3xl md:text-4xl font-serif font-bold text-forest-green tracking-tight leading-none">
              Field Agent Operations.
            </h1>
            <p className="mt-2 text-sm text-secondary-text max-w-2xl leading-relaxed">
              Real-time roster of autonomous monitoring drones, high-altitude gas sentries,
              riparian hydrology probes, and sub-canopy soil sensors deployed across the Cascade transect.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto">
            <button
              onClick={handleStepPatrol}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface hover:bg-surface-muted text-forest-green border border-border transition text-xs font-mono"
            >
              <Play className="w-3 h-3 text-secondary-green" />
              <span>Patrol Step</span>
            </button>

            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded bg-forest-green hover:bg-forest-green-light text-surface transition text-xs font-medium shadow-sm"
            >
              <Plus className="w-3.5 h-3.5 text-botanical" />
              <span>Deploy Node</span>
            </button>

            <button
              onClick={handleExportCSV}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface hover:bg-surface-muted text-secondary-text hover:text-forest-green border border-border transition text-xs"
              title="Export roster to CSV"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Export CSV</span>
            </button>
          </div>
        </div>

        {/* Status Strip */}
        <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 divide-y sm:divide-y-0 sm:divide-x divide-border bg-surface border border-border rounded shadow-editorial p-1">
          <div className="px-4 py-2">
            <span className="editorial-tag text-[9px] text-secondary-text">TOTAL ROSTER</span>
            <div className="text-xl font-serif font-bold text-forest-green tabular-nums">
              {agents.length} nodes
            </div>
          </div>
          <div className="px-4 py-2">
            <span className="editorial-tag text-[9px] text-secondary-text">ONLINE ACTIVE</span>
            <div className="text-xl font-serif font-bold text-forest-green tabular-nums">
              {activeCount}
            </div>
          </div>
          <div className="px-4 py-2">
            <span className="editorial-tag text-[9px] text-secondary-text">ANOMALIES / HAZARDS</span>
            <div className="text-xl font-serif font-bold text-critical-incident tabular-nums">
              {anomalyCount}
            </div>
          </div>
          <div className="px-4 py-2">
            <span className="editorial-tag text-[9px] text-secondary-text">OFFLINE DISCONNECTED</span>
            <div className="text-xl font-serif font-bold text-warning-amber tabular-nums">
              {offlineCount}
            </div>
          </div>
        </div>
      </div>

      {actionNotice && (
        <div className="p-3 bg-muted-sage text-forest-green rounded border border-border text-xs font-mono flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-secondary-green" />
            <span>{actionNotice}</span>
          </div>
          <button onClick={() => setActionNotice("")} className="text-secondary-text hover:text-forest-green">
            Dismiss
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 self-start sm:self-auto overflow-x-auto pb-1 sm:pb-0 w-full sm:w-auto">
          {["ALL", "ACTIVE", "WARNINGS", "ANOMALIES", "OFFLINE"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded text-xs font-mono transition ${
                filter === f
                  ? "bg-forest-green text-surface font-semibold"
                  : "bg-surface text-secondary-text hover:text-forest-green border border-border"
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-secondary-text" />
          <input
            type="text"
            placeholder="Search by ID, type, sector..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded bg-surface border border-border text-xs text-forest-green focus:outline-none focus:border-forest-green font-mono placeholder:text-secondary-text/60"
          />
        </div>
      </div>

      {/* Main Roster Table */}
      <div className="bg-surface rounded border border-border shadow-editorial overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-surface-muted border-b border-border text-[10px] text-secondary-text uppercase tracking-wider font-mono">
                <th className="py-3 px-4">Node / Asset</th>
                <th className="py-3 px-4">Sector & Coordinates</th>
                <th className="py-3 px-4">Current Assignment</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Sensor Telemetry</th>
                <th className="py-3 px-4">Power / Health</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredAgents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-secondary-text font-serif italic">
                    No field agents matching filter criteria.
                  </td>
                </tr>
              ) : (
                filteredAgents.map((agent) => {
                  const [lat, lng] = getAgentCoordinates(agent);
                  const isAnomalous = agent.ai_result?.status === "ANOMALY";
                  const isWarning =
                    !isAnomalous &&
                    (agent.battery < 30 || agent.readings?.temperature > 35);

                  return (
                    <tr
                      key={agent.id}
                      className="hover:bg-surface-muted/60 transition group cursor-pointer"
                      onClick={() => setSelectedAgent(agent)}
                    >
                      {/* Node / Asset */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded bg-forest-green text-botanical flex items-center justify-center font-mono font-bold text-xs shrink-0">
                            {agent.id}
                          </div>
                          <div>
                            <div className="font-mono font-bold text-forest-green">
                              {agent.id}
                            </div>
                            <div className="text-[11px] text-secondary-text font-medium">
                              {agent.agent_type || "Sensor Node"}
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Sector & Coordinates */}
                      <td className="py-3.5 px-4">
                        <div className="font-medium text-forest-green">
                          {agent.zone || "Cascade Sector"}
                        </div>
                        <div className="text-[10px] font-mono text-secondary-text tabular-nums">
                          {lat}° N, {lng}° W
                        </div>
                      </td>

                      {/* Current Assignment */}
                      <td className="py-3.5 px-4 max-w-xs">
                        <p className="text-[11px] text-forest-green italic leading-tight truncate">
                          {agent.assignment || "Surveillance"}
                        </p>
                        <span className="text-[10px] font-mono text-secondary-text">
                          Neighbors: {agent.neighbors?.length || 0} peers
                        </span>
                      </td>

                      {/* Status */}
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                            agent.status === "ACTIVE"
                              ? isAnomalous
                                ? "bg-critical-incident/15 text-critical-incident"
                                : isWarning
                                ? "bg-warning-amber/15 text-warning-amber"
                                : "bg-muted-sage text-forest-green"
                              : "bg-surface-muted text-secondary-text border border-border"
                          }`}
                        >
                          {agent.status === "ACTIVE"
                            ? isAnomalous
                              ? "ANOMALY"
                              : isWarning
                              ? "WARNING"
                              : "ACTIVE"
                            : "OFFLINE"}
                        </span>
                      </td>

                      {/* Sensor Telemetry */}
                      <td className="py-3.5 px-4 font-mono text-[11px] text-forest-green tabular-nums">
                        <div>
                          <span>{agent.readings?.temperature}°C</span>
                          <span className="text-secondary-text mx-1">|</span>
                          <span>SMK: {agent.readings?.smoke}</span>
                        </div>
                        <div className="text-[10px] text-secondary-text">
                          CO2: {Math.round(agent.readings?.co2)} ppm | AQI: {Math.round(agent.readings?.air_quality)}
                        </div>
                      </td>

                      {/* Power / Health */}
                      <td className="py-3.5 px-4 font-mono text-[11px] tabular-nums">
                        <div className="flex items-center gap-1.5 text-forest-green">
                          <Battery className="w-3.5 h-3.5 text-secondary-green" />
                          <span>{agent.battery}%</span>
                        </div>
                        <div className="text-[10px] text-secondary-text">
                          Health: {agent.health}%
                        </div>
                      </td>

                      {/* Actions */}
                      <td
                        className="py-3.5 px-4 text-right"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => setSelectedAgent(agent)}
                            className="p-1 rounded hover:bg-surface-muted text-secondary-text hover:text-forest-green transition"
                            title="Inspect Node"
                          >
                            <Eye className="w-4 h-4" />
                          </button>

                          <button
                            onClick={() => handleToggleFail(agent)}
                            className="p-1 rounded hover:bg-surface-muted text-secondary-text hover:text-critical-incident transition"
                            title={agent.status === "ACTIVE" ? "Simulate Disconnection" : "Restore Node"}
                          >
                            <PowerOff className="w-4 h-4" />
                          </button>

                          <button
                            onClick={() => handleRestart(agent.id)}
                            className="p-1 rounded hover:bg-surface-muted text-secondary-text hover:text-forest-green transition"
                            title="Reboot Node"
                          >
                            <RotateCcw className="w-4 h-4 text-secondary-green" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        <div className="px-4 py-2.5 bg-surface-muted border-t border-border flex items-center justify-between text-xs text-secondary-text font-mono">
          <span>SHOWING {filteredAgents.length} OF {agents.length} AGENT ASSETS</span>
          <span>TRANSECT ALPHA — SECURE MESH</span>
        </div>
      </div>

      {/* Selected Agent Inspector Modal */}
      {selectedAgent && (
        <AgentDetailModal
          agent={selectedAgent}
          onClose={() => setSelectedAgent(null)}
          onUpdate={fetchAgents}
        />
      )}

      {/* Deploy Agent Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-forest-green/40 backdrop-blur-sm p-4 animate-fade-in select-none">
          <div className="bg-surface border border-border rounded w-full max-w-md shadow-elevated p-6 relative">
            <div className="flex items-center justify-between pb-3 border-b border-border mb-4">
              <div>
                <span className="editorial-tag text-[9px] text-secondary-text">TRANSECT COMMISSIONING</span>
                <h3 className="font-serif font-bold text-base text-forest-green">
                  Deploy Autonomous Field Node
                </h3>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-secondary-text hover:text-forest-green"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateAgent} className="space-y-3 text-xs">
              <div>
                <label className="block text-secondary-text text-[11px] mb-1">
                  Node Identifier
                </label>
                <input
                  type="text"
                  placeholder={`A${agents.length + 1}`}
                  value={newAgent.id}
                  onChange={(e) => setNewAgent({ ...newAgent, id: e.target.value })}
                  className="w-full px-3 py-1.5 rounded bg-surface-muted border border-border text-forest-green font-mono text-xs focus:outline-none focus:border-forest-green"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-secondary-text text-[11px] mb-1">
                    Grid Coordinate X (0-19)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="19"
                    value={newAgent.x}
                    onChange={(e) => setNewAgent({ ...newAgent, x: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-1.5 rounded bg-surface-muted border border-border text-forest-green font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block text-secondary-text text-[11px] mb-1">
                    Grid Coordinate Y (0-19)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="19"
                    value={newAgent.y}
                    onChange={(e) => setNewAgent({ ...newAgent, y: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-1.5 rounded bg-surface-muted border border-border text-forest-green font-mono text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-secondary-text text-[11px] mb-1">
                    Initial Temp (°C)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={newAgent.temperature}
                    onChange={(e) => setNewAgent({ ...newAgent, temperature: parseFloat(e.target.value) || 28 })}
                    className="w-full px-3 py-1.5 rounded bg-surface-muted border border-border text-forest-green font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block text-secondary-text text-[11px] mb-1">
                    Initial Smoke Index
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={newAgent.smoke}
                    onChange={(e) => setNewAgent({ ...newAgent, smoke: parseFloat(e.target.value) || 0.1 })}
                    className="w-full px-3 py-1.5 rounded bg-surface-muted border border-border text-forest-green font-mono text-xs"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-border flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 rounded bg-surface hover:bg-surface-muted text-secondary-text border border-border text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded bg-forest-green hover:bg-forest-green-light text-surface text-xs font-medium shadow-sm"
                >
                  Deploy Node
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
