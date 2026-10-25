"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import { Crosshair, X, Sun, Navigation } from "lucide-react";
import { LocationPanel, useGeolocation } from "@/components/LocationPanel";
import { useSim } from "@/components/SimulationProvider";
import { WorkflowStrip } from "@/components/WorkflowStrip";
import { SimulationHeader } from "@/components/simulator/SimulationHeader";
import { SimulatorControlPanel } from "@/components/simulator/SimulatorControlPanel";
import { HAZARD_COLOR, HAZARD_LABEL, haversine } from "@/lib/format";
import type { AgentType, IncidentType } from "@/lib/types";
import type { MapTypeOption } from "@/components/map/AreaMap";

const AreaMap = dynamic(() => import("@/components/map/AreaMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center text-sm text-ink-3">
      Loading map engine...
    </div>
  ),
});

const GoogleAreaMap = dynamic(
  () => import("@/components/map/GoogleAreaMap").then((m) => m.GoogleAreaMap),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full items-center justify-center text-sm text-ink-3">
        Loading Google Maps SDK...
      </div>
    ),
  }
);

const DEFAULT_RADIUS: Record<IncidentType, number> = { FIRE: 400, POLLUTION: 450, EXTREME_HEAT: 700 };
const DEFAULT_SEVERITY: Record<IncidentType, number> = { FIRE: 70, POLLUTION: 70, EXTREME_HEAT: 80 };

export default function SimulatorPage() {
  const { snapshot, act, connection } = useSim();
  const [radius, setRadius] = useState(1200);
  const geo = useGeolocation(radius);
  const [locationPanelOpen, setLocationPanelOpen] = useState(false);
  const [panelCollapsed, setPanelCollapsed] = useState(false);

  // Inspector state
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<string | null>(null);
  const [moveAgentMode, setMoveAgentMode] = useState<string | null>(null);

  // Incident creation state
  const [activeIncidentType, setActiveIncidentType] = useState<IncidentType | null>(null);
  const [pendingIncidentLocation, setPendingIncidentLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [severity, setSeverity] = useState<number | null>(null);
  const [customRadius, setCustomRadius] = useState<number | null>(null);
  const [isSubmittingIncident, setIsSubmittingIncident] = useState(false);
  const [lastCreatedIncidentId, setLastCreatedIncidentId] = useState<string | null>(null);

  // Map view & tile engine state
  const hasGoogleApiKey = Boolean(process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY);
  const [provider, setProvider] = useState<"google" | "leaflet">(hasGoogleApiKey ? "google" : "leaflet");
  const [mapType, setMapType] = useState<MapTypeOption>("tactical");

  // Layer visibility state
  const [showMesh, setShowMesh] = useState(false);
  const [showCoverageZones, setShowCoverageZones] = useState(false);
  const [showRanges, setShowRanges] = useState(false);
  const [showTrails, setShowTrails] = useState(true);
  const [showHazardZones, setShowHazardZones] = useState(true);
  const [showCoverageEngine, setShowCoverageEngine] = useState(false);

  // Agent filtering state
  const [selectedAgentTypes, setSelectedAgentTypes] = useState<AgentType[]>([]);
  const [selectedAgentStatuses, setSelectedAgentStatuses] = useState<string[]>([]);

  // Sync radius on first snapshot
  useEffect(() => {
    if (snapshot?.site) {
      setRadius((r) => (r === 1200 ? snapshot.site.radius_m : r));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [snapshot?.site?.run_id]);

  // Keyboard shortcut (Escape cancels picking/inspector)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (pendingIncidentLocation) setPendingIncidentLocation(null);
        else if (activeIncidentType) setActiveIncidentType(null);
        else if (moveAgentMode) setMoveAgentMode(null);
        else {
          setSelectedAgent(null);
          setSelectedIncident(null);
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [pendingIncidentLocation, activeIncidentType, moveAgentMode]);

  // Trigger map resize invalidation whenever the control panel expands or collapses
  useEffect(() => {
    const delays = [0, 50, 100, 200, 350, 500];
    const timers = delays.map((ms) =>
      setTimeout(() => {
        window.dispatchEvent(new Event("resize"));
      }, ms)
    );
    return () => timers.forEach((t) => clearTimeout(t));
  }, [panelCollapsed]);

  const agent = snapshot?.agents.find((a) => a.id === selectedAgent) ?? null;
  const incident = snapshot?.incidents.find((i) => i.id === selectedIncident) ?? null;
  const focusIncident = useMemo(() => {
    if (!snapshot) return null;
    if (incident) return incident;
    return (
      snapshot.incidents.find((i) => !["RESOLVED", "REJECTED"].includes(i.status)) ??
      snapshot.incidents[0] ??
      null
    );
  }, [snapshot, incident]);

  // Filtered agents list for map rendering
  const filteredAgents = useMemo(() => {
    if (!snapshot) return [];
    return snapshot.agents.filter((a) => {
      if (selectedAgentTypes.length > 0 && !selectedAgentTypes.includes(a.type)) {
        return false;
      }
      if (selectedAgentStatuses.length > 0 && !selectedAgentStatuses.includes(a.status)) {
        return false;
      }
      return true;
    });
  }, [snapshot, selectedAgentTypes, selectedAgentStatuses]);

  if (!snapshot) {
    return (
      <div className="flex h-full min-h-[60vh] items-center justify-center text-sm text-ink-3">
        {connection === "offline"
          ? "Waiting for the backend simulation server..."
          : "Connecting to autonomous multi-agent simulation..."}
      </div>
    );
  }

  // Handle map clicks
  async function handleMapClick(lat: number, lng: number) {
    if (!snapshot) return;

    // 1. Moving an agent
    if (moveAgentMode) {
      const ok = await act(
        `/api/agents/${moveAgentMode}/move`,
        { latitude: lat, longitude: lng },
        `Agent ${moveAgentMode} rerouted to chosen coordinates.`
      );
      if (ok) setMoveAgentMode(null);
      return;
    }

    // 2. Incident target point pick
    if (activeIncidentType) {
      setPendingIncidentLocation({ lat, lng });
      return;
    }

    // 3. Normal map click clears inspector selection
    setSelectedAgent(null);
    setSelectedIncident(null);
  }

  // Submit incident creation to backend API
  async function handleCreateIncident() {
    if (!activeIncidentType || !pendingIncidentLocation || !snapshot) return;

    setIsSubmittingIncident(true);
    try {
      const sev = severity ?? DEFAULT_SEVERITY[activeIncidentType];
      const rad = customRadius ?? DEFAULT_RADIUS[activeIncidentType];

      const res = await act<{ id: string }>(
        "/api/incidents",
        {
          type: activeIncidentType,
          latitude: pendingIncidentLocation.lat,
          longitude: pendingIncidentLocation.lng,
          severity: sev,
          radius_m: rad,
        },
        `${HAZARD_LABEL[activeIncidentType]} deployed (radius ${rad}m, severity ${sev}). Monitoring drones will spot anomaly.`
      );

      if (res) {
        setLastCreatedIncidentId(res.id);
        setSelectedIncident(res.id);
        setSelectedAgent(null);
        setPendingIncidentLocation(null);
        setActiveIncidentType(null);
      }
    } finally {
      setIsSubmittingIncident(false);
    }
  }

  // Agent filter toggles
  function handleToggleAgentType(t: AgentType) {
    setSelectedAgentTypes((prev) =>
      prev.includes(t) ? prev.filter((item) => item !== t) : [...prev, t]
    );
  }

  function handleToggleAgentStatus(s: string) {
    setSelectedAgentStatuses((prev) =>
      prev.includes(s) ? prev.filter((item) => item !== s) : [...prev, s]
    );
  }

  function handleResetAgentFilters() {
    setSelectedAgentTypes([]);
    setSelectedAgentStatuses([]);
  }

  // Dynamic preview circle on map during incident targeting
  const pickPreview =
    activeIncidentType && pendingIncidentLocation
      ? {
          lat: pendingIncidentLocation.lat,
          lng: pendingIncidentLocation.lng,
          radius_m: customRadius ?? DEFAULT_RADIUS[activeIncidentType],
          color: HAZARD_COLOR[activeIncidentType],
        }
      : null;

  const site = snapshot.site;

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] lg:h-screen lg:overflow-hidden bg-ground">
      {/* 1. TOP SIMULATION & TELEMETRY TOOLBAR */}
      <SimulationHeader
        site={site}
        geoStatus={geo.status}
        onOpenLocationPanel={() => setLocationPanelOpen(true)}
        panelOpen={locationPanelOpen}
        panelCollapsed={panelCollapsed}
        onTogglePanel={() => setPanelCollapsed((c) => !c)}
      />

      {/* 2. MAIN WORKSPACE (MAP + COLLAPSIBLE CONTROL PANEL) */}
      <div className="flex flex-1 min-h-0 overflow-hidden relative">
        {/* CENTER / LEFT: MAIN GEOGRAPHICAL MAP */}
        <div className="flex-1 min-w-0 h-full relative overflow-hidden bg-ground">
          {provider === "google" && hasGoogleApiKey ? (
            <GoogleAreaMap
              site={site}
              agents={filteredAgents}
              incidents={snapshot.incidents}
              links={snapshot.links}
              coverage={snapshot.coverage}
              tickMs={snapshot.simulation.running ? snapshot.simulation.tick_interval_s * 1000 : 300}
              selectedAgentId={selectedAgent}
              selectedIncidentId={focusIncident?.id ?? null}
              onSelectAgent={(id) => {
                setSelectedAgent(id);
                if (id) setSelectedIncident(null);
              }}
              onSelectIncident={(id) => {
                setSelectedIncident(id);
                setSelectedAgent(null);
              }}
              pickMode={activeIncidentType || moveAgentMode ? "incident" : null}
              onPick={handleMapClick}
              pickPreview={pickPreview}
              mapType={mapType}
              onMapTypeChange={setMapType}
              showLinks={showMesh}
              showCoverageZones={showCoverageZones}
              showRanges={showRanges}
              showTrails={showTrails}
              showHazardZones={showHazardZones}
            />
          ) : (
            <AreaMap
              site={site}
              agents={filteredAgents}
              incidents={snapshot.incidents}
              links={snapshot.links}
              coverage={snapshot.coverage}
              tickMs={snapshot.simulation.running ? snapshot.simulation.tick_interval_s * 1000 : 300}
              selectedAgentId={selectedAgent}
              selectedIncidentId={focusIncident?.id ?? null}
              onSelectAgent={(id) => {
                setSelectedAgent(id);
                if (id) setSelectedIncident(null);
              }}
              onSelectIncident={(id) => {
                setSelectedIncident(id);
                setSelectedAgent(null);
              }}
              pickMode={activeIncidentType || moveAgentMode ? "incident" : null}
              onPick={handleMapClick}
              pickPreview={pickPreview}
              mapType={mapType}
              showLinks={showMesh}
              showCoverageZones={showCoverageZones}
              showRanges={showRanges}
              showTrails={showTrails}
              showHazardZones={showHazardZones}
            />
          )}

          {/* Active Targeting / Move Notification Banner (Top Center of Map) */}
          {activeIncidentType && !pendingIncidentLocation && (
            <div className="absolute left-1/2 top-4 z-[450] flex -translate-x-1/2 items-center gap-2.5 rounded-lg border border-primary bg-surface/95 px-4 py-2 text-xs font-medium text-ink shadow-2xl backdrop-blur-md animate-in fade-in slide-in-from-top-2">
              <Crosshair size={15} className="text-primary animate-pulse" />
              <span>
                Click anywhere on the map to set location for{" "}
                <strong className="text-ink font-bold">{HAZARD_LABEL[activeIncidentType]}</strong>.
              </span>
              <button
                onClick={() => setActiveIncidentType(null)}
                className="ml-1 text-ink-3 hover:text-ink"
                title="Cancel targeting"
              >
                <X size={14} />
              </button>
            </div>
          )}

          {moveAgentMode && (
            <div className="absolute left-1/2 top-4 z-[450] flex -translate-x-1/2 items-center gap-2.5 rounded-lg border border-primary bg-surface/95 px-4 py-2 text-xs font-medium text-ink shadow-md backdrop-blur-md animate-in fade-in slide-in-from-top-2">
              <Navigation size={15} className="text-primary animate-pulse" />
              <span>
                Click the map destination for agent{" "}
                <strong className="text-ink font-mono font-bold">{moveAgentMode}</strong>.
              </span>
              <button
                onClick={() => setMoveAgentMode(null)}
                className="ml-1 text-ink-3 hover:text-ink"
                title="Cancel movement order"
              >
                <X size={14} />
              </button>
            </div>
          )}

          {/* Bottom Workflow Strip (Tracks Lifecycle of Active Incident) */}
          <div className="absolute bottom-3 left-3 right-3 z-[450] pointer-events-none">
            <div className="pointer-events-auto max-w-4xl mx-auto">
              {focusIncident ? (
                <WorkflowStrip incident={focusIncident} tick={snapshot.tick} />
              ) : (
                <div className="rounded-xl border border-line bg-surface/95 px-4 py-2.5 text-xs text-ink shadow-md backdrop-blur-md flex items-center justify-between">
                  <span className="flex items-center gap-2 font-semibold text-ink">
                    <Sun size={15} className="text-green shrink-0" />
                    All {snapshot.stats.operational_agents} operational agents reporting normal environmental conditions
                  </span>
                  <span className="text-2xs text-ink-2 hidden sm:inline">
                    Autonomous monitor drones are continuously patrolling their sectors
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* RIGHT: DEDICATED COLLAPSIBLE CONTROL PANEL */}
        <SimulatorControlPanel
          collapsed={panelCollapsed}
          onToggleCollapse={() => setPanelCollapsed(true)}
          // Inspector
          agent={agent}
          incident={incident}
          tick={snapshot.tick}
          onCloseInspector={() => {
            setSelectedAgent(null);
            setSelectedIncident(null);
          }}
          movingAgent={Boolean(moveAgentMode)}
          onMoveAgent={() =>
            setMoveAgentMode(moveAgentMode ? null : agent?.id ?? null)
          }
          onSelectAgent={(id) => {
            setSelectedAgent(id);
            setSelectedIncident(null);
          }}
          // Start an Incident
          site={site}
          activeIncidentType={activeIncidentType}
          onSelectIncidentType={(t) => {
            setActiveIncidentType(t);
            setPendingIncidentLocation(null);
            setSeverity(null);
            setCustomRadius(null);
          }}
          pendingIncidentLocation={pendingIncidentLocation}
          onCancelPendingLocation={() => setPendingIncidentLocation(null)}
          severity={severity}
          onSeverityChange={setSeverity}
          customRadius={customRadius}
          onRadiusChange={setCustomRadius}
          onSubmitIncident={handleCreateIncident}
          isSubmittingIncident={isSubmittingIncident}
          lastCreatedIncidentId={lastCreatedIncidentId}
          // Map View
          mapType={mapType}
          onMapTypeChange={setMapType}
          provider={provider}
          onProviderChange={setProvider}
          hasGoogleApiKey={hasGoogleApiKey}
          // Map Layers
          showMesh={showMesh}
          onToggleMesh={() => setShowMesh((v) => !v)}
          showCoverageZones={showCoverageZones}
          onToggleCoverageZones={() => setShowCoverageZones((v) => !v)}
          showRanges={showRanges}
          onToggleRanges={() => setShowRanges((v) => !v)}
          showTrails={showTrails}
          onToggleTrails={() => setShowTrails((v) => !v)}
          showHazardZones={showHazardZones}
          onToggleHazardZones={() => setShowHazardZones((v) => !v)}
          showCoverageEngine={showCoverageEngine}
          onToggleCoverageEngine={() => setShowCoverageEngine((v) => !v)}
          // Drone Health & Coverage Engine
          coverage={snapshot.coverage}
          allAgents={snapshot.agents}
          onFailDrone={(id) =>
            act(
              `/api/agents/${id}/fail`,
              undefined,
              `MONITOR DRONE ${id} FAILURE DETECTED. Reassigning coverage.`
            )
          }
          onRestoreDrone={(id) =>
            act(
              `/api/agents/${id}/restore`,
              undefined,
              `MONITOR DRONE ${id} RESTORED. Reintegrating into network.`
            )
          }
          // Agent Filters
          selectedAgentTypes={selectedAgentTypes}
          onToggleAgentType={handleToggleAgentType}
          selectedAgentStatuses={selectedAgentStatuses}
          onToggleAgentStatus={handleToggleAgentStatus}
          onResetAgentFilters={handleResetAgentFilters}
          filteredAgentCount={filteredAgents.length}
          totalAgentCount={snapshot.agents.length}
        />
      </div>

      {/* Surveillance Area Selection Modal Panel */}
      <LocationPanel
        open={locationPanelOpen}
        onClose={() => setLocationPanelOpen(false)}
        geoStatus={geo.status}
        onLocate={geo.locate}
        onPickOnMap={() => {
          setLocationPanelOpen(false);
          // Allow picking new site center
        }}
        picking={false}
        radius={radius}
        setRadius={setRadius}
      />
    </div>
  );
}
