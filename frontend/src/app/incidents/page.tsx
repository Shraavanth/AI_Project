"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Incident } from "@/lib/types";
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
  AlertTriangle
} from "lucide-react";
import { getEventCoordinates } from "@/components/LiveMonitoringMap";

export default function IncidentManagementPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [actionNotice, setActionNotice] = useState<string>("");

  // Trigger parameters
  const [params, setParams] = useState({
    center_x: 10,
    center_y: 10,
    radius: 3,
  });

  const fetchIncidents = async () => {
    try {
      const data = await api.getEvents();
      setIncidents(data);
      if (data.length > 0 && !selectedIncident) {
        setSelectedIncident(data[0]);
      } else if (selectedIncident) {
        const found = data.find((i) => i.event_id === selectedIncident.event_id);
        if (found) setSelectedIncident(found);
      }
    } catch (err) {
      console.error("Failed to fetch incidents:", err);
    }
  };

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 3000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleTrigger = async (type: "FIRE" | "POLLUTION" | "EXTREME_HEAT") => {
    setLoading(true);
    try {
      let res: Incident;
      if (type === "FIRE") res = await api.createFireEvent(params);
      else if (type === "POLLUTION") res = await api.createPollutionEvent(params);
      else res = await api.createExtremeHeatEvent(params);

      setSelectedIncident(res);
      setActionNotice(`${type} incident triggered. Neighbor consensus reached!`);
      setTimeout(() => setActionNotice(""), 3500);
      await fetchIncidents();
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
      fetchIncidents();
    } catch (e: any) {
      alert(`Acknowledgment failed: ${e.message}`);
    }
  };

  const handleResolve = async (eventId: string) => {
    try {
      await api.resolveEvent(eventId);
      setActionNotice(`Incident ${eventId} resolved. Field sensors normalized.`);
      setTimeout(() => setActionNotice(""), 3500);
      fetchIncidents();
    } catch (e: any) {
      alert(`Resolution failed: ${e.message}`);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-border pb-5">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="editorial-tag text-secondary-text mb-1 tracking-widest">
              AUTONOMOUS ANOMALY VERIFICATION & CONSENSUS
            </div>
            <h1 className="editorial-title text-3xl md:text-4xl font-serif font-bold text-forest-green tracking-tight leading-none">
              Incident Management & Verification.
            </h1>
            <p className="mt-2 text-sm text-secondary-text max-w-2xl leading-relaxed">
              Decentralized multi-agent hazard detection and consensus verification.
              Agents share sensor anomaly tokens with neighboring peers to validate wildfires,
              pollution plumes, and extreme heatwaves without a central authority.
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-secondary-text">
            <span>ACTIVE INCIDENTS:</span>
            <span className="font-bold text-forest-green">
              {incidents.filter((i) => i.status === "ACTIVE").length}
            </span>
          </div>
        </div>
      </div>

      {actionNotice && (
        <div className="p-3 bg-muted-sage text-forest-green rounded border border-border text-xs font-mono flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-secondary-green" />
            <span>{actionNotice}</span>
          </div>
          <button onClick={() => setActionNotice("")} className="text-secondary-text hover:text-forest-green">✕</button>
        </div>
      )}

      {/* Incident Trigger Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Fire Trigger Card */}
        <div className="bg-surface border border-border hover:border-critical-incident/60 rounded p-4 flex flex-col justify-between shadow-editorial transition">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono font-bold text-critical-incident flex items-center gap-1.5 text-xs">
                <Flame className="w-4 h-4 text-critical-incident" />
                WILDFIRE / COMBUSTION
              </span>
              <span className="editorial-tag text-[9px] px-1.5 py-0.2 rounded bg-critical-incident/15 text-critical-incident">
                CRITICAL
              </span>
            </div>
            <p className="text-[11px] text-secondary-text leading-relaxed mb-3">
              Generates thermal flare (&gt;45°C), dense smoke particulates (&gt;0.8), and rapid humidity drop across affected canopy.
            </p>
          </div>

          <button
            onClick={() => handleTrigger("FIRE")}
            disabled={loading}
            className="w-full py-1.5 rounded bg-surface hover:bg-critical-incident/10 text-critical-incident border border-critical-incident/40 font-mono text-xs transition"
          >
            Simulate Wildfire
          </button>
        </div>

        {/* Pollution Trigger Card */}
        <div className="bg-surface border border-border hover:border-warning-amber/60 rounded p-4 flex flex-col justify-between shadow-editorial transition">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono font-bold text-warning-amber flex items-center gap-1.5 text-xs">
                <Wind className="w-4 h-4 text-warning-amber" />
                ATMOSPHERIC POLLUTION
              </span>
              <span className="editorial-tag text-[9px] px-1.5 py-0.2 rounded bg-warning-amber/15 text-warning-amber">
                HIGH CONCERN
              </span>
            </div>
            <p className="text-[11px] text-secondary-text leading-relaxed mb-3">
              Generates elevated carbon dioxide (&gt;850 ppm) and degraded particulate air quality (AQI &gt;180) across the river basin.
            </p>
          </div>

          <button
            onClick={() => handleTrigger("POLLUTION")}
            disabled={loading}
            className="w-full py-1.5 rounded bg-surface hover:bg-warning-amber/10 text-warning-amber border border-warning-amber/40 font-mono text-xs transition"
          >
            Simulate Pollution
          </button>
        </div>

        {/* Extreme Heat Trigger Card */}
        <div className="bg-surface border border-border hover:border-forest-green/60 rounded p-4 flex flex-col justify-between shadow-editorial transition">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono font-bold text-forest-green flex items-center gap-1.5 text-xs">
                <Thermometer className="w-4 h-4 text-secondary-green" />
                CANOPY HEATWAVE
              </span>
              <span className="editorial-tag text-[9px] px-1.5 py-0.2 rounded bg-muted-sage text-forest-green">
                ECOLOGICAL
              </span>
            </div>
            <p className="text-[11px] text-secondary-text leading-relaxed mb-3">
              Generates high ambient temperature (&gt;42°C) without combustion smoke, inducing vegetative thermal stress.
            </p>
          </div>

          <button
            onClick={() => handleTrigger("EXTREME_HEAT")}
            disabled={loading}
            className="w-full py-1.5 rounded bg-surface hover:bg-surface-muted text-forest-green border border-border font-mono text-xs transition"
          >
            Simulate Heatwave
          </button>
        </div>
      </div>

      {/* Main Grid: Incident Chronicle & Detailed Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Chronological Incident List (7 cols) */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-border">
            <span className="editorial-tag text-[9px] text-secondary-text">
              CHRONOLOGICAL HAZARD ARCHIVE
            </span>
            <span className="text-xs font-mono text-secondary-text">
              {incidents.length} Records Logged
            </span>
          </div>

          {incidents.length === 0 ? (
            <div className="bg-surface p-12 rounded border border-border text-center text-xs text-secondary-text font-serif italic shadow-editorial">
              No historical incident events logged in database. Trigger a simulation above to observe consensus.
            </div>
          ) : (
            incidents.map((evt) => {
              const [lat, lng] = getEventCoordinates(evt);
              const isSelected = selectedIncident?.event_id === evt.event_id;

              return (
                <div
                  key={evt.event_id}
                  onClick={() => setSelectedIncident(evt)}
                  className={`bg-surface p-4 rounded border transition shadow-editorial cursor-pointer ${
                    isSelected
                      ? "border-forest-green bg-surface-muted/50 ring-1 ring-forest-green"
                      : "border-border hover:border-secondary-green/40"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
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

                    <div className="text-[10px] font-mono text-secondary-text">
                      {evt.timestamp ? evt.timestamp.split("T")[0] : ""}
                    </div>
                  </div>

                  <p className="text-xs text-secondary-text mb-3">
                    Detected across {evt.affected_count} sensor nodes in {evt.zone_name || "Cascade Transect"} ({lat}° N, {lng}° W).
                  </p>

                  <div className="flex items-center justify-between text-[11px] font-mono pt-2 border-t border-border">
                    <span className="text-forest-green font-medium">
                      Consensus: {evt.consensus_state} ({Math.round(evt.confidence * 100)}%)
                    </span>
                    <span className="text-secondary-text">ID: {evt.event_id}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right: Selected Incident Inspector (5 cols) */}
        <div className="lg:col-span-5">
          {selectedIncident ? (
            <div className="bg-surface p-5 rounded border border-border shadow-editorial text-xs space-y-4 sticky top-20">
              <div className="pb-3 border-b border-border flex items-center justify-between">
                <div>
                  <span className="editorial-tag text-[9px] text-secondary-text">
                    INCIDENT DOSSIER
                  </span>
                  <h3 className="font-serif font-bold text-base text-forest-green">
                    {selectedIncident.event_type}
                  </h3>
                </div>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${
                    selectedIncident.status === "ACTIVE"
                      ? "bg-critical-incident/15 text-critical-incident"
                      : "bg-muted-sage text-forest-green"
                  }`}
                >
                  {selectedIncident.status}
                </span>
              </div>

              {/* Geographic Coordinates */}
              <div className="p-3 rounded bg-surface-muted border border-border space-y-1 font-mono text-[11px]">
                <div className="flex justify-between">
                  <span className="text-secondary-text">Transect Coordinates:</span>
                  <span className="text-forest-green">
                    {getEventCoordinates(selectedIncident)[0]}° N,{" "}
                    {getEventCoordinates(selectedIncident)[1]}° W
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondary-text">Sector Zone:</span>
                  <span className="text-forest-green">
                    {selectedIncident.zone_name || "Central Riparian River Basin"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-secondary-text">Hazard Radius:</span>
                  <span className="text-forest-green">
                    {selectedIncident.radius * 650} meters
                  </span>
                </div>
              </div>

              {/* Consensus Quorum Verification */}
              <div className="space-y-2">
                <span className="editorial-tag text-[9px] text-secondary-text block">
                  NEIGHBOR CONSENSUS EVIDENCE
                </span>
                <p className="text-xs text-secondary-text leading-relaxed">
                  {selectedIncident.detecting_count} of {selectedIncident.affected_count} field nodes
                  in proximity reached mutual agreement via peer-to-peer evidence exchange.
                </p>

                <div className="w-full bg-border h-2 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-secondary-green rounded-full"
                    style={{ width: `${Math.round(selectedIncident.confidence * 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] font-mono text-secondary-text">
                  <span>Confidence: {Math.round(selectedIncident.confidence * 100)}%</span>
                  <span>Threshold: 75% required</span>
                </div>
              </div>

              {/* Affected Agents list */}
              <div>
                <span className="editorial-tag text-[9px] text-secondary-text block mb-1.5">
                  AFFECTED FIELD NODES
                </span>
                <div className="flex flex-wrap gap-1">
                  {(selectedIncident.affected_agents || []).map((aId) => (
                    <span
                      key={aId}
                      className="px-2 py-0.5 rounded bg-surface-muted border border-border text-forest-green font-mono text-[10px]"
                    >
                      {aId}
                    </span>
                  ))}
                </div>
              </div>

              {/* Working Controls */}
              <div className="pt-3 border-t border-border flex items-center gap-2">
                {selectedIncident.status === "ACTIVE" && (
                  <>
                    <button
                      onClick={() => handleAcknowledge(selectedIncident.event_id)}
                      className="flex-1 py-1.5 rounded bg-surface hover:bg-surface-muted text-forest-green border border-border font-mono text-xs transition"
                    >
                      Acknowledge
                    </button>
                    <button
                      onClick={() => handleResolve(selectedIncident.event_id)}
                      className="flex-1 py-1.5 rounded bg-forest-green hover:bg-forest-green-light text-surface font-mono text-xs transition shadow-sm"
                    >
                      Resolve Incident
                    </button>
                  </>
                )}
                {selectedIncident.status !== "ACTIVE" && (
                  <div className="w-full py-1.5 text-center text-xs text-secondary-text font-serif italic bg-surface-muted rounded border border-border">
                    This incident has been verified and resolved.
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-surface p-8 rounded border border-border text-center text-xs text-secondary-text font-serif italic shadow-editorial">
              Select an incident record to review consensus evidence and operational actions.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
