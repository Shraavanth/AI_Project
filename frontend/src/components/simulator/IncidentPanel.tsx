"use client";

import React from "react";
import { Flame, Factory, ThermometerSun, MapPin, X, Check, Crosshair } from "lucide-react";
import { HAZARD_COLOR, HAZARD_LABEL, haversine } from "@/lib/format";
import type { IncidentType, Site } from "@/lib/types";
import { Button, cx } from "@/components/ui";

const INCIDENT_BUTTONS: { type: IncidentType; icon: typeof Flame; label: string }[] = [
  { type: "FIRE", icon: Flame, label: "Fire" },
  { type: "POLLUTION", icon: Factory, label: "Pollution" },
  { type: "EXTREME_HEAT", icon: ThermometerSun, label: "Extreme Heat" },
];

const DEFAULT_RADIUS: Record<IncidentType, number> = { FIRE: 400, POLLUTION: 450, EXTREME_HEAT: 700 };
const DEFAULT_SEVERITY: Record<IncidentType, number> = { FIRE: 70, POLLUTION: 70, EXTREME_HEAT: 80 };

interface IncidentPanelProps {
  site: Site;
  activeType: IncidentType | null;
  onSelectType: (type: IncidentType | null) => void;
  pendingLocation: { lat: number; lng: number } | null;
  onCancelPending: () => void;
  severity: number | null;
  onSeverityChange: (v: number) => void;
  customRadius: number | null;
  onRadiusChange: (v: number) => void;
  onSubmitIncident: () => Promise<void>;
  isSubmitting?: boolean;
  disabled?: boolean;
  lastCreatedIncidentId?: string | null;
}

export function IncidentPanel({
  site,
  activeType,
  onSelectType,
  pendingLocation,
  onCancelPending,
  severity,
  onSeverityChange,
  customRadius,
  onRadiusChange,
  onSubmitIncident,
  isSubmitting = false,
  disabled = false,
  lastCreatedIncidentId,
}: IncidentPanelProps) {
  const currentRadius = activeType ? (customRadius ?? DEFAULT_RADIUS[activeType]) : 400;
  const currentSeverity = activeType ? (severity ?? DEFAULT_SEVERITY[activeType]) : 70;

  const distanceKm = pendingLocation
    ? (haversine([pendingLocation.lat, pendingLocation.lng], [site.lat, site.lng]) / 1000).toFixed(2)
    : null;

  return (
    <div className="space-y-3">
      {/* 1. Incident Type Selection Buttons */}
      <div>
        <label className="text-2xs font-bold uppercase tracking-wider text-ink-2 block mb-1.5">
          Select Hazard Type:
        </label>
        <div className="grid grid-cols-3 gap-1.5">
          {INCIDENT_BUTTONS.map(({ type, icon: Icon, label }) => {
            const active = activeType === type;
            const color = HAZARD_COLOR[type];

            return (
              <button
                key={type}
                type="button"
                onClick={() => onSelectType(active ? null : type)}
                disabled={disabled}
                className={cx(
                  "flex flex-col items-center justify-center gap-1.5 rounded-lg border p-2.5 text-xs font-semibold transition-all disabled:opacity-40 shadow-2xs",
                  active
                    ? "border-transparent text-white shadow-md font-bold scale-[1.02]"
                    : "border-line bg-surface text-ink hover:border-primary/50 hover:bg-selected/40"
                )}
                style={active ? { backgroundColor: color } : undefined}
                title={`Select ${label}`}
              >
                <Icon size={16} style={active ? { color: "#ffffff" } : { color }} />
                <span className="text-2xs leading-tight">{label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. When Hazard Type is selected */}
      {activeType && (
        <div className="space-y-3 rounded-lg border border-line bg-panel p-3 animate-in fade-in duration-150 shadow-2xs">
          {/* Target Location State */}
          <div className="rounded-md border border-line bg-surface p-2.5 shadow-2xs">
            {pendingLocation ? (
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-ink flex items-center gap-1.5">
                    <MapPin size={13} className="text-primary" />
                    Target Selected
                  </span>
                  <button
                    type="button"
                    onClick={onCancelPending}
                    className="text-2xs text-primary hover:text-primary-hover underline font-medium"
                  >
                    Repick
                  </button>
                </div>
                <div className="text-2xs font-mono text-ink font-medium">
                  {pendingLocation.lat.toFixed(4)}° N, {pendingLocation.lng.toFixed(4)}° E
                </div>
                <div className="text-2xs text-ink-2">
                  {distanceKm} km from surveillance origin
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs text-ink bg-selected/60 p-2.5 rounded border border-primary/30">
                <Crosshair size={15} className="shrink-0 text-primary animate-pulse" />
                <span className="leading-tight text-2xs font-medium">
                  Click a target point on the geographical map to place this {HAZARD_LABEL[activeType].toLowerCase()}.
                </span>
              </div>
            )}
          </div>

          {/* Configuration Parameters (Severity & Radius) */}
          <div className="space-y-2.5">
            {/* Severity */}
            <div>
              <div className="flex justify-between text-xs text-ink">
                <span className="font-medium text-ink-2">Starting Severity:</span>
                <span className="font-bold tabular-nums text-ink">{currentSeverity}</span>
              </div>
              <input
                type="range"
                min={30}
                max={100}
                step={5}
                value={currentSeverity}
                onChange={(e) => onSeverityChange(Number(e.target.value))}
                className="mt-1 w-full accent-[#397FB8] h-1.5 rounded-lg bg-line/60 cursor-pointer"
              />
            </div>

            {/* Radius */}
            <div>
              <div className="flex items-center justify-between text-xs text-ink">
                <span className="font-medium text-ink-2">Incident Radius:</span>
                <div className="flex items-center gap-1">
                  <input
                    type="number"
                    min={50}
                    max={1500}
                    step={25}
                    value={currentRadius}
                    onChange={(e) => {
                      const v = Number(e.target.value);
                      if (!isNaN(v) && v >= 50 && v <= 2000) onRadiusChange(v);
                    }}
                    className="w-16 rounded border border-line bg-input px-1.5 py-0.5 text-right font-mono text-xs tabular-nums text-ink focus:border-primary focus:outline-none shadow-2xs font-medium"
                  />
                  <span className="text-2xs text-ink-2">m</span>
                </div>
              </div>
              <input
                type="range"
                min={100}
                max={1000}
                step={25}
                value={currentRadius}
                onChange={(e) => onRadiusChange(Number(e.target.value))}
                className="mt-1 w-full accent-[#397FB8] h-1.5 rounded-lg bg-line/60 cursor-pointer"
              />
            </div>

            <p className="text-2xs text-ink-2">
              Radius: <span className="font-semibold text-ink">{currentRadius} m</span>.{" "}
              {activeType === "FIRE" ? "Untreated fires expand." : "Does not dissipate spontaneously."}
            </p>
          </div>

          {/* Submit / Cancel Action Buttons */}
          <div className="pt-1 flex items-center gap-2">
            <button
              type="button"
              onClick={onSubmitIncident}
              disabled={!pendingLocation || isSubmitting || disabled}
              className={cx(
                "flex-1 flex items-center justify-center gap-2 rounded-lg py-2 px-3 text-xs font-semibold text-white shadow-md transition-all",
                !pendingLocation || isSubmitting || disabled
                  ? "bg-line/50 text-ink-3 cursor-not-allowed border border-line"
                  : "hover:opacity-95 active:scale-[0.99]"
              )}
              style={
                pendingLocation && !isSubmitting && !disabled
                  ? { backgroundColor: HAZARD_COLOR[activeType] }
                  : undefined
              }
            >
              {isSubmitting ? (
                "Deploying Incident..."
              ) : (
                <>
                  <Check size={14} />
                  CREATE INCIDENT
                </>
              )}
            </button>

            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                onCancelPending();
                onSelectType(null);
              }}
              className="text-xs"
              title="Cancel incident creation"
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {/* Success Notification / Compact Status */}
      {lastCreatedIncidentId && !activeType && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-2.5 text-xs text-emerald-800 animate-in fade-in shadow-2xs">
          <div className="font-semibold flex items-center gap-1.5">
            <Check size={13} className="text-emerald-600" />
            Incident {lastCreatedIncidentId} Active
          </div>
          <p className="mt-0.5 text-2xs text-emerald-700">
            Agents have begun local consensus and response dispatch.
          </p>
        </div>
      )}
    </div>
  );
}
