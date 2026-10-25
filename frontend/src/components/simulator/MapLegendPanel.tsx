"use client";

import React from "react";
import { AgentGlyph } from "@/components/AgentGlyph";
import { HAZARD_COLOR } from "@/lib/format";
import type { AgentType } from "@/lib/types";

const TYPES: [AgentType, string, string][] = [
  ["MONITOR_DRONE", "Circle", "Monitor drone (surveillance)"],
  ["FIRE_DRONE", "Triangle", "Fire suppression drone"],
  ["SPRINKLER", "Square", "Sprinkler station unit"],
  ["POLLUTION_UNIT", "Hexagon", "Pollution scrubber unit"],
  ["COOLING_UNIT", "Diamond", "Cooling mitigation unit"],
];

const STATUSES: [string, string, string][] = [
  ["#398C69", "Normal", "Nominal patrol / idle"],
  ["#D99A39", "Detecting", "Sensor anomaly flag & voting"],
  ["#397FB8", "Moving / Coordinating", "Transit & cluster coordination"],
  ["#E96C4B", "Responding", "Active mitigation work"],
  ["#7F8992", "Failed", "Hardware crash / link lost"],
  ["#866CC5", "Recovering", "Sector rebalancing"],
];

export function MapLegendPanel() {
  return (
    <div className="space-y-3 text-2xs">
      {/* 1. Shapes / Agent Types */}
      <div>
        <div className="text-2xs font-bold uppercase tracking-wider text-ink-2 pb-1 border-b border-line mb-2">
          Agent Shapes:
        </div>
        <div className="space-y-1.5">
          {TYPES.map(([t, shape, label]) => (
            <div key={t} className="flex items-center justify-between text-ink-2">
              <div className="flex items-center gap-2">
                <AgentGlyph type={t} color="#397FB8" size={13} />
                <span className="text-ink font-semibold">{label}</span>
              </div>
              <span className="font-mono text-ink-3 text-3xs font-medium">{shape}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 2. Status Colors */}
      <div>
        <div className="text-2xs font-bold uppercase tracking-wider text-ink-2 pb-1 border-b border-line mb-2">
          Operational Status Colors:
        </div>
        <div className="grid grid-cols-2 gap-x-2 gap-y-1.5">
          {STATUSES.map(([c, label, desc]) => (
            <div key={label} className="flex items-center gap-1.5 text-ink font-medium" title={desc}>
              <span className="h-2 w-2 rounded-full shrink-0 shadow-2xs" style={{ background: c }} />
              <span className="truncate">{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Map Layers & Indicators */}
      <div>
        <div className="text-2xs font-bold uppercase tracking-wider text-ink-2 pb-1 border-b border-line mb-2">
          Map Layer Indicators:
        </div>
        <div className="space-y-1.5 text-ink-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="h-0.5 w-4 bg-[#397FB8]" />
              <span className="text-ink">Mesh communication link</span>
            </div>
            <span className="text-3xs text-ink-3 font-medium">Peer-to-peer</span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="h-0.5 w-4 border-t border-dashed border-[#D99A39]" />
              <span className="text-ink">Multihop relay link</span>
            </div>
            <span className="text-3xs text-ink-3 font-medium">Routed</span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full border border-[#397FB8] border-dashed" />
              <span className="text-ink">Surveillance boundary</span>
            </div>
            <span className="text-3xs text-ink-3 font-medium">Fleet radius</span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ background: HAZARD_COLOR.FIRE }} />
              <span className="h-2 w-2 rounded-full" style={{ background: HAZARD_COLOR.POLLUTION }} />
              <span className="h-2 w-2 rounded-full" style={{ background: HAZARD_COLOR.EXTREME_HEAT }} />
              <span className="text-ink">Hazard zone perimeters</span>
            </div>
            <span className="text-3xs text-ink-3 font-medium">Ground truth</span>
          </div>
        </div>
      </div>
    </div>
  );
}
