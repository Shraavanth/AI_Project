"use client";

import React from "react";
import { Map as MapIcon, Globe, Mountain, Satellite, Layers, Compass } from "lucide-react";
import { cx } from "@/components/ui";
import type { MapTypeOption } from "@/components/map/AreaMap";

interface MapViewSelectorProps {
  mapType: MapTypeOption;
  onMapTypeChange: (type: MapTypeOption) => void;
  provider: "google" | "leaflet";
  onProviderChange: (p: "google" | "leaflet") => void;
  hasGoogleApiKey: boolean;
}

const MAP_OPTIONS: { id: MapTypeOption; label: string; desc: string; icon: typeof MapIcon }[] = [
  {
    id: "tactical",
    label: "Tactical Dark Green (Original)",
    desc: "Dark-green military terrain & vegetation surveillance",
    icon: Compass,
  },
  {
    id: "roadmap",
    label: "Default (Street Map)",
    desc: "OpenStreetMap vector street layout & landmarks",
    icon: MapIcon,
  },
  {
    id: "satellite",
    label: "Satellite Imagery",
    desc: "High-resolution orbital satellite photography",
    icon: Satellite,
  },
  {
    id: "terrain",
    label: "Topographic Terrain",
    desc: "Elevation contours, hillshading & landforms",
    icon: Mountain,
  },
  {
    id: "hybrid",
    label: "Hybrid (Satellite + Labels)",
    desc: "Satellite photography with road & city overlays",
    icon: Layers,
  },
];

export function MapViewSelector({
  mapType,
  onMapTypeChange,
  provider,
  onProviderChange,
  hasGoogleApiKey,
}: MapViewSelectorProps) {
  return (
    <div className="space-y-3">
      {/* Tile View Selector Cards (Arctic Blue Theme) */}
      <div className="space-y-1.5">
        {MAP_OPTIONS.map((opt) => {
          const active = mapType === opt.id;
          const Icon = opt.icon;

          return (
            <button
              key={opt.id}
              type="button"
              onClick={() => onMapTypeChange(opt.id)}
              className={cx(
                "w-full flex items-center justify-between rounded-lg border p-2.5 text-left transition-all",
                active
                  ? "border-primary bg-selected text-ink shadow-sm ring-1 ring-primary/40"
                  : "border-line bg-surface text-ink hover:border-primary/50 hover:bg-selected/40"
              )}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <div
                  className={cx(
                    "flex h-7 w-7 items-center justify-center rounded-md shrink-0 transition-colors",
                    active ? "bg-primary text-white" : "bg-input text-ink-2"
                  )}
                >
                  <Icon size={14} />
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-ink leading-tight">
                    {opt.label}
                  </div>
                  <p className="text-2xs text-ink-2 truncate">{opt.desc}</p>
                </div>
              </div>

              {/* Radio Indicator */}
              <div
                className={cx(
                  "h-4 w-4 rounded-full border flex items-center justify-center shrink-0 ml-2",
                  active ? "border-primary bg-primary" : "border-line bg-input"
                )}
              >
                {active && <span className="h-1.5 w-1.5 rounded-full bg-white" />}
              </div>
            </button>
          );
        })}
      </div>

      {/* Provider Switcher / Status */}
      <div className="pt-2 border-t border-line">
        <div className="flex items-center justify-between text-2xs text-ink-2">
          <span>Tile Engine Provider:</span>
          {hasGoogleApiKey ? (
            <button
              type="button"
              onClick={() => onProviderChange(provider === "google" ? "leaflet" : "google")}
              className="flex items-center gap-1 font-semibold text-primary hover:text-primary-hover"
            >
              <Globe size={11} />
              <span>{provider === "google" ? "Google Maps JS" : "Leaflet Engine"}</span>
            </button>
          ) : (
            <span className="font-mono text-ink flex items-center gap-1">
              <Globe size={11} className="text-primary" />
              OpenStreetMap / Esri
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
