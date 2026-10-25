"use client";

import React, { useState } from "react";
import {
  Play,
  Pause,
  RotateCcw,
  StepForward,
  MapPin,
  Wifi,
  Radio,
  PanelRightClose,
  PanelRightOpen,
  Activity,
  Compass,
} from "lucide-react";
import { useSim } from "@/components/SimulationProvider";
import { Button, cx } from "@/components/ui";
import type { Site } from "@/lib/types";

const SOURCE_TEXT: Record<string, string> = {
  GEOLOCATION: "Automatically located",
  SEARCH: "Searched place",
  MAP_PICK: "Manually selected",
  DEMO: "Demo site",
  MANUAL: "Set manually",
};

interface SimulationHeaderProps {
  site: Site;
  geoStatus: string;
  onOpenLocationPanel: () => void;
  panelOpen: boolean;
  panelCollapsed: boolean;
  onTogglePanel: () => void;
}

export function SimulationHeader({
  site,
  geoStatus,
  onOpenLocationPanel,
  panelOpen,
  panelCollapsed,
  onTogglePanel,
}: SimulationHeaderProps) {
  const { snapshot, act, connection } = useSim();
  const [confirmReset, setConfirmReset] = useState(false);

  if (!snapshot) return null;
  const sim = snapshot.simulation;
  const stats = snapshot.stats;
  const disabled = connection === "offline";

  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-line bg-panel/95 px-4 py-2.5 backdrop-blur-md shadow-xs z-20 shrink-0 text-ink">
      {/* Left: Location & Area Telemetry */}
      <div className="flex items-center gap-2 min-w-0">
        <button
          onClick={onOpenLocationPanel}
          className="group flex items-center gap-2.5 rounded-lg border border-line bg-surface px-3 py-1.5 text-left text-xs transition-all hover:border-primary/50 hover:bg-selected/40 shadow-2xs"
          title="Click to configure surveillance center and monitoring radius"
        >
          <div className="flex h-6 w-6 items-center justify-center rounded bg-primary/20 text-primary group-hover:scale-105 transition-transform shrink-0">
            <MapPin size={14} />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-ink truncate max-w-[150px] sm:max-w-[220px]">
                {site.label}
              </span>
              <span className="rounded bg-primary/15 px-1.5 py-0.5 text-2xs font-medium text-primary shrink-0 border border-primary/25">
                {(site.radius_m / 1000).toFixed(1)} km radius
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-2xs text-ink-2">
              <span>{SOURCE_TEXT[site.source] ?? site.source}</span>
              <span>·</span>
              <span className="font-mono">{site.lat.toFixed(4)}°, {site.lng.toFixed(4)}°</span>
            </div>
          </div>
        </button>

        {geoStatus === "requesting" && (
          <span className="rounded-md bg-amber/15 border border-amber/40 px-2 py-1 text-2xs text-amber font-medium animate-pulse">
            Acquiring GPS fix...
          </span>
        )}
      </div>

      {/* Middle: Compact Simulation Controls */}
      <div className="flex items-center gap-2">
        {/* Status Indicator */}
        <div className="flex items-center gap-1.5 rounded-md border border-line bg-surface px-2.5 py-1 text-xs">
          <span
            className={cx(
              "h-2 w-2 rounded-full",
              sim.running ? "bg-green animate-pulse" : "bg-amber"
            )}
          />
          <span className="font-cond font-semibold uppercase tracking-wider text-ink text-2xs">
            {sim.running ? "Active" : "Paused"}
          </span>
          <span className="font-mono text-2xs text-ink-2">t={sim.tick}s</span>
        </div>

        {/* Play/Pause */}
        {sim.running ? (
          <Button
            size="sm"
            onClick={() => act("/api/simulation/pause")}
            disabled={disabled}
            className="h-8 gap-1 font-semibold"
            title="Pause simulation"
          >
            <Pause size={13} />
            <span className="hidden sm:inline">Pause</span>
          </Button>
        ) : (
          <Button
            size="sm"
            variant="primary"
            onClick={() => act("/api/simulation/resume")}
            disabled={disabled}
            className="h-8 gap-1 font-semibold"
            title="Resume simulation"
          >
            <Play size={13} />
            <span className="hidden sm:inline">Resume</span>
          </Button>
        )}

        {/* Step Forward (when paused) */}
        {!sim.running && (
          <Button
            size="sm"
            onClick={() => act("/api/simulation/step", { ticks: 1 })}
            disabled={disabled}
            className="h-8"
            title="Step forward 1 second"
          >
            <StepForward size={13} />
            <span className="hidden sm:inline">Step</span>
          </Button>
        )}

        {/* Speed Selector Group */}
        <div
          className="flex overflow-hidden rounded-md border border-line bg-input"
          role="group"
          aria-label="Simulation speed"
        >
          {sim.allowed_speeds.map((s) => (
            <button
              key={s}
              onClick={() => act("/api/simulation/speed", { speed: s })}
              disabled={disabled}
              aria-pressed={sim.speed === s}
              className={cx(
                "h-8 px-2.5 text-xs font-medium tabular-nums transition-all",
                sim.speed === s
                  ? "bg-primary font-bold text-white shadow-xs"
                  : "text-ink-2 hover:bg-selected/40 hover:text-ink"
              )}
              title={`Set simulation speed to ${s}x`}
            >
              {s}x
            </button>
          ))}
        </div>

        {/* Reset Button */}
        {confirmReset ? (
          <div className="flex items-center gap-1">
            <Button
              size="sm"
              variant="danger"
              className="h-8"
              onClick={async () => {
                setConfirmReset(false);
                await act("/api/simulation/reset", undefined, "Simulation reset: fresh fleet deployed.");
              }}
            >
              Confirm
            </Button>
            <Button size="sm" variant="ghost" className="h-8" onClick={() => setConfirmReset(false)}>
              Cancel
            </Button>
          </div>
        ) : (
          <Button
            size="sm"
            variant="ghost"
            className="h-8 text-ink-2 hover:text-ink"
            onClick={() => setConfirmReset(true)}
            disabled={disabled}
            title="Reset simulation and deploy fresh fleet"
          >
            <RotateCcw size={13} />
            <span className="hidden sm:inline">Reset</span>
          </Button>
        )}
      </div>

      {/* Right: Operational Stats & Panel Toggle */}
      <div className="flex items-center gap-3">
        <div className="hidden xl:flex items-center gap-3 text-xs border-r border-line pr-3">
          <div className="flex items-center gap-1.5" title="Operational Agents">
            <span className="h-1.5 w-1.5 rounded-full bg-green" />
            <span className="text-ink-2">Fleet:</span>
            <span className="font-mono font-medium text-ink">
              {stats.operational_agents}/{stats.total_agents}
            </span>
          </div>

          <div className="flex items-center gap-1.5" title="Radio Mesh Links">
            <Wifi size={12} className="text-primary" />
            <span className="text-ink-2">Links:</span>
            <span className="font-mono font-medium text-ink">{stats.links}</span>
          </div>

          <div className="flex items-center gap-1.5" title="Network Topology State">
            <span
              className={cx(
                "text-2xs font-semibold uppercase tracking-wider",
                stats.network_connected ? "text-green" : "text-amber"
              )}
            >
              {stats.network_connected ? "Mesh Connected" : `${stats.network_components} Clusters`}
            </span>
          </div>
        </div>

        {/* Control Panel Toggle Button */}
        <button
          onClick={onTogglePanel}
          className={cx(
            "flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-semibold transition-all shadow-2xs",
            panelCollapsed
              ? "border-primary bg-selected text-ink hover:bg-selected/80 shadow-xs"
              : "border-line bg-surface text-ink-2 hover:border-primary/50 hover:bg-selected/40 hover:text-ink"
          )}
          title={panelCollapsed ? "Expand side control panel" : "Collapse side control panel for full map"}
        >
          {panelCollapsed ? (
            <>
              <PanelRightOpen size={15} />
              <span className="hidden sm:inline">Open Controls</span>
            </>
          ) : (
            <>
              <PanelRightClose size={15} />
              <span className="hidden sm:inline">Hide Controls</span>
            </>
          )}
        </button>
      </div>
    </header>
  );
}
