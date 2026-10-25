"use client";

import React, { useState } from "react";
import {
  Flame,
  Map as MapIcon,
  Layers,
  Filter,
  Info,
  Activity,
  PanelRightClose,
  Sparkles,
  ChevronRight,
  Shield,
  X,
} from "lucide-react";
import { CollapsibleSection } from "./CollapsibleSection";
import { IncidentPanel } from "./IncidentPanel";
import { MapViewSelector } from "./MapViewSelector";
import { LayerControls } from "./LayerControls";
import { AgentFilters } from "./AgentFilters";
import { MapLegendPanel } from "./MapLegendPanel";
import { AgentInspector } from "@/components/AgentInspector";
import { IncidentInspector } from "@/components/IncidentInspector";
import { CoveragePanel } from "@/components/CoveragePanel";
import type { Agent, AgentType, CoverageSummary, Incident, IncidentType, Site } from "@/lib/types";
import type { MapTypeOption } from "@/components/map/AreaMap";
import { cx } from "@/components/ui";

interface SimulatorControlPanelProps {
  collapsed: boolean;
  onToggleCollapse: () => void;

  // Inspector
  agent: Agent | null;
  incident: Incident | null;
  tick: number;
  onCloseInspector: () => void;
  movingAgent: boolean;
  onMoveAgent?: () => void;
  onSelectAgent?: (id: string | null) => void;

  // Start an incident
  site: Site;
  activeIncidentType: IncidentType | null;
  onSelectIncidentType: (t: IncidentType | null) => void;
  pendingIncidentLocation: { lat: number; lng: number } | null;
  onCancelPendingLocation: () => void;
  severity: number | null;
  onSeverityChange: (v: number) => void;
  customRadius: number | null;
  onRadiusChange: (v: number) => void;
  onSubmitIncident: () => Promise<void>;
  isSubmittingIncident?: boolean;
  lastCreatedIncidentId?: string | null;

  // Map View
  mapType: MapTypeOption;
  onMapTypeChange: (t: MapTypeOption) => void;
  provider: "google" | "leaflet";
  onProviderChange: (p: "google" | "leaflet") => void;
  hasGoogleApiKey: boolean;

  // Layers
  showMesh: boolean;
  onToggleMesh: () => void;
  showCoverageZones: boolean;
  onToggleCoverageZones: () => void;
  showRanges: boolean;
  onToggleRanges: () => void;
  showTrails: boolean;
  onToggleTrails: () => void;
  showHazardZones: boolean;
  onToggleHazardZones: () => void;
  showCoverageEngine: boolean;
  onToggleCoverageEngine: () => void;

  // Coverage Summary & Fault Injection
  coverage?: CoverageSummary;
  allAgents: Agent[];
  onFailDrone: (id: string) => void;
  onRestoreDrone: (id: string) => void;

  // Agent Filters
  selectedAgentTypes: AgentType[];
  onToggleAgentType: (t: AgentType) => void;
  selectedAgentStatuses: string[];
  onToggleAgentStatus: (s: string) => void;
  onResetAgentFilters: () => void;
  filteredAgentCount: number;
  totalAgentCount: number;
}

export function SimulatorControlPanel({
  collapsed,
  onToggleCollapse,
  agent,
  incident,
  tick,
  onCloseInspector,
  movingAgent,
  onMoveAgent,
  onSelectAgent,
  site,
  activeIncidentType,
  onSelectIncidentType,
  pendingIncidentLocation,
  onCancelPendingLocation,
  severity,
  onSeverityChange,
  customRadius,
  onRadiusChange,
  onSubmitIncident,
  isSubmittingIncident,
  lastCreatedIncidentId,
  mapType,
  onMapTypeChange,
  provider,
  onProviderChange,
  hasGoogleApiKey,
  showMesh,
  onToggleMesh,
  showCoverageZones,
  onToggleCoverageZones,
  showRanges,
  onToggleRanges,
  showTrails,
  onToggleTrails,
  showHazardZones,
  onToggleHazardZones,
  showCoverageEngine,
  onToggleCoverageEngine,
  coverage,
  allAgents,
  onFailDrone,
  onRestoreDrone,
  selectedAgentTypes,
  onToggleAgentType,
  selectedAgentStatuses,
  onToggleAgentStatus,
  onResetAgentFilters,
  filteredAgentCount,
  totalAgentCount,
}: SimulatorControlPanelProps) {
  // Independent open state for each accordion
  const [openIncident, setOpenIncident] = useState(true);
  const [openMapView, setOpenMapView] = useState(false);
  const [openLayers, setOpenLayers] = useState(false);
  const [openFilters, setOpenFilters] = useState(false);
  const [openLegend, setOpenLegend] = useState(false);

  // If incident type is active, make sure incident accordion is expanded
  React.useEffect(() => {
    if (activeIncidentType) {
      setOpenIncident(true);
    }
  }, [activeIncidentType]);

  if (collapsed) {
    return null;
  }

  const isInspecting = Boolean(agent || incident);

  return (
    <aside
      className={cx(
        "h-full w-full sm:w-[330px] lg:w-[350px] shrink-0 border-l border-line bg-panel flex flex-col z-20 transition-all duration-300 shadow-xs"
      )}
    >
      {/* Control Panel Header */}
      <div className="flex items-center justify-between border-b border-line px-4 py-2.5 bg-header shrink-0">
        <div className="flex items-center gap-2">
          <div className="flex h-5 w-5 items-center justify-center rounded bg-primary/20 text-primary">
            <Activity size={13} />
          </div>
          <span className="font-cond text-xs font-bold tracking-wider uppercase text-ink">
            Area Operations
          </span>
        </div>
        <button
          onClick={onToggleCollapse}
          className="rounded p-1 text-ink-2 hover:bg-selected/60 hover:text-ink transition-colors"
          title="Collapse side panel"
        >
          <PanelRightClose size={15} />
        </button>
      </div>

      {/* Scrollable Control Stack */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5 scroll-thin">
        {/* 0. Inspector Card (Appears whenever an agent or incident is selected on the map) */}
        {isInspecting && (
          <div className="rounded-xl border border-primary/40 bg-surface p-3.5 shadow-md shadow-[#18344D]/5 ring-1 ring-primary/20 animate-in fade-in duration-200 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-line">
              <span className="font-cond text-xs font-bold uppercase tracking-wider text-primary flex items-center gap-1.5">
                <Sparkles size={13} />
                {agent ? "Agent Telemetry & Inspector" : "Incident Inspector"}
              </span>
              <button
                onClick={onCloseInspector}
                className="rounded p-1 text-ink-3 hover:bg-selected/40 hover:text-ink text-xs"
                title="Close inspector"
              >
                <X size={14} />
              </button>
            </div>

            {agent ? (
              <AgentInspector
                agent={agent}
                onClose={onCloseInspector}
                moving={movingAgent}
                onMove={onMoveAgent}
              />
            ) : incident ? (
              <IncidentInspector
                incident={incident}
                tick={tick}
                onClose={onCloseInspector}
                onSelectAgent={onSelectAgent}
              />
            ) : null}
          </div>
        )}

        {/* 1. START AN INCIDENT */}
        <CollapsibleSection
          title="Start an Incident"
          icon={<Flame size={15} className="text-rose-400" />}
          badge={
            activeIncidentType ? (
              <span className="rounded bg-rose-500/15 text-rose-300 font-semibold px-1.5 py-0.5 text-2xs uppercase">
                Active
              </span>
            ) : undefined
          }
          isOpen={openIncident}
          onToggle={() => setOpenIncident((v) => !v)}
        >
          <IncidentPanel
            site={site}
            activeType={activeIncidentType}
            onSelectType={onSelectIncidentType}
            pendingLocation={pendingIncidentLocation}
            onCancelPending={onCancelPendingLocation}
            severity={severity}
            onSeverityChange={onSeverityChange}
            customRadius={customRadius}
            onRadiusChange={onRadiusChange}
            onSubmitIncident={onSubmitIncident}
            isSubmitting={isSubmittingIncident}
            lastCreatedIncidentId={lastCreatedIncidentId}
          />
        </CollapsibleSection>

        {/* 2. MAP VIEW SELECTOR */}
        <CollapsibleSection
          title="Map View"
          icon={<MapIcon size={15} className="text-sky-500" />}
          badge={
            <span className="font-mono text-2xs text-slate-500 uppercase">
              {mapType}
            </span>
          }
          isOpen={openMapView}
          onToggle={() => setOpenMapView((v) => !v)}
        >
          <MapViewSelector
            mapType={mapType}
            onMapTypeChange={onMapTypeChange}
            provider={provider}
            onProviderChange={onProviderChange}
            hasGoogleApiKey={hasGoogleApiKey}
          />
        </CollapsibleSection>

        {/* 3. MAP LAYERS */}
        <CollapsibleSection
          title="Map Layers"
          icon={<Layers size={15} className="text-emerald-500" />}
          badge={
            <span className="rounded bg-slate-100 px-1.5 py-0.5 text-2xs text-slate-700 font-medium border border-slate-200">
              {[showMesh, showCoverageZones, showRanges, showTrails, showHazardZones].filter(Boolean).length}/5
            </span>
          }
          isOpen={openLayers}
          onToggle={() => setOpenLayers((v) => !v)}
        >
          <LayerControls
            showMesh={showMesh}
            onToggleMesh={onToggleMesh}
            showCoverageZones={showCoverageZones}
            onToggleCoverageZones={onToggleCoverageZones}
            showRanges={showRanges}
            onToggleRanges={onToggleRanges}
            showTrails={showTrails}
            onToggleTrails={onToggleTrails}
            showHazardZones={showHazardZones}
            onToggleHazardZones={onToggleHazardZones}
            showCoverageEngine={showCoverageEngine}
            onToggleCoverageEngine={onToggleCoverageEngine}
          />
        </CollapsibleSection>

        {/* 4. AGENT FILTERS */}
        <CollapsibleSection
          title="Agent Filters"
          icon={<Filter size={15} className="text-amber-500" />}
          badge={
            <span className="font-mono text-2xs text-slate-700 font-medium rounded bg-slate-100 px-1.5 py-0.5 border border-slate-200">
              {filteredAgentCount}/{totalAgentCount}
            </span>
          }
          isOpen={openFilters}
          onToggle={() => setOpenFilters((v) => !v)}
        >
          <AgentFilters
            agents={allAgents}
            selectedTypes={selectedAgentTypes}
            onToggleType={onToggleAgentType}
            selectedStatuses={selectedAgentStatuses}
            onToggleStatus={onToggleAgentStatus}
            onResetFilters={onResetAgentFilters}
            filteredCount={filteredAgentCount}
            totalCount={totalAgentCount}
          />
        </CollapsibleSection>

        {/* 5. MAP LEGEND */}
        <CollapsibleSection
          title="Map Legend"
          icon={<Info size={15} className="text-purple-400" />}
          isOpen={openLegend}
          onToggle={() => setOpenLegend((v) => !v)}
        >
          <MapLegendPanel />
        </CollapsibleSection>

        {/* 6. DRONE HEALTH & COVERAGE ENGINE (when toggled on) */}
        {showCoverageEngine && (
          <div className="pt-1">
            <CoveragePanel
              coverage={coverage}
              agents={allAgents}
              onFailDrone={onFailDrone}
              onRestoreDrone={onRestoreDrone}
              onSelectAgent={onSelectAgent}
            />
          </div>
        )}
      </div>
    </aside>
  );
}
