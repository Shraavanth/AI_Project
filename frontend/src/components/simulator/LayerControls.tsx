"use client";

import React from "react";
import { Radio, Shield, Layers, Navigation, AlertTriangle, Activity } from "lucide-react";
import { cx } from "@/components/ui";

interface LayerControlsProps {
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
}

export function LayerControls({
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
}: LayerControlsProps) {
  const LAYERS = [
    {
      id: "mesh",
      label: "Communication Mesh",
      desc: "Peer-to-peer radio links and multihop routes",
      icon: Radio,
      active: showMesh,
      onToggle: onToggleMesh,
      color: "text-sky-400",
      activeBg: "bg-sky-500",
    },
    {
      id: "coverage",
      label: "Drone Coverage Areas",
      desc: "450m surveillance radii, 80m buffer & blind spots",
      icon: Shield,
      active: showCoverageZones,
      onToggle: onToggleCoverageZones,
      color: "text-emerald-400",
      activeBg: "bg-emerald-500",
    },
    {
      id: "ranges",
      label: "Operating Ranges",
      desc: "Sprinkler & fixed-responder action perimeters",
      icon: Layers,
      active: showRanges,
      onToggle: onToggleRanges,
      color: "text-purple-400",
      activeBg: "bg-purple-500",
    },
    {
      id: "trails",
      label: "Movement Trails",
      desc: "Historical flight paths and waypoint tracks",
      icon: Navigation,
      active: showTrails,
      onToggle: onToggleTrails,
      color: "text-amber-400",
      activeBg: "bg-amber-500",
    },
    {
      id: "hazards",
      label: "Incident Hazard Zones",
      desc: "Severity outlines for active fire, pollution & heat",
      icon: AlertTriangle,
      active: showHazardZones,
      onToggle: onToggleHazardZones,
      color: "text-rose-400",
      activeBg: "bg-rose-500",
    },
    {
      id: "engine",
      label: "Health & Coverage Engine",
      desc: "Fault-tolerant heartbeat monitor & recovery panel",
      icon: Activity,
      active: showCoverageEngine,
      onToggle: onToggleCoverageEngine,
      color: "text-indigo-400",
      activeBg: "bg-indigo-500",
    },
  ];

  return (
    <div className="space-y-2">
      {LAYERS.map((layer) => {
        const Icon = layer.icon;

        return (
          <div
            key={layer.id}
            className="flex items-center justify-between gap-3 rounded-lg border border-line bg-surface p-2.5 transition-colors hover:border-primary/50 hover:bg-selected/40 shadow-2xs"
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <div className={cx("flex h-7 w-7 items-center justify-center rounded-md bg-input shrink-0", layer.color)}>
                <Icon size={14} />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-ink leading-tight">
                  {layer.label}
                </div>
                <div className="text-2xs text-ink-2 truncate">{layer.desc}</div>
              </div>
            </div>

            {/* Toggle Switch */}
            <button
              type="button"
              role="switch"
              aria-checked={layer.active}
              onClick={layer.onToggle}
              className={cx(
                "relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none",
                layer.active ? layer.activeBg : "bg-line/70 border-line"
              )}
            >
              <span
                className={cx(
                  "pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-md ring-0 transition duration-200 ease-in-out",
                  layer.active ? "translate-x-4" : "translate-x-0"
                )}
              />
            </button>
          </div>
        );
      })}
    </div>
  );
}
