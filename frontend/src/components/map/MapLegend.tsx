import { AgentGlyph } from "@/components/AgentGlyph";
import { HAZARD_COLOR } from "@/lib/format";
import type { AgentType } from "@/lib/types";

const TYPES: [AgentType, string][] = [
  ["MONITOR_DRONE", "Monitor drone"],
  ["FIRE_DRONE", "Fire drone"],
  ["SPRINKLER", "Sprinkler"],
  ["POLLUTION_UNIT", "Pollution unit"],
  ["COOLING_UNIT", "Cooling unit"],
];

const STATUSES: [string, string][] = [
  ["#5FB37C", "Normal"],
  ["#E0A43A", "Detecting"],
  ["#5B9BD5", "Moving / coordinating"],
  ["#A98BE0", "Responding"],
  ["#6B7276", "Failed"],
];

export function MapLegend() {
  return (
    <div className="grid grid-cols-[auto_auto] gap-x-5 gap-y-1 rounded-md border border-line bg-surface/95 px-3 py-2.5 text-2xs text-ink-2 shadow-lg shadow-black/30">
      <div className="space-y-1">
        <div className="pb-0.5 text-ink-3">Shape = type</div>
        {TYPES.map(([t, label]) => (
          <div key={t} className="flex items-center gap-2">
            <AgentGlyph type={t} color="#C9D1CC" size={11} />
            {label}
          </div>
        ))}
      </div>
      <div className="space-y-1">
        <div className="pb-0.5 text-ink-3">Colour = status</div>
        {STATUSES.map(([c, label]) => (
          <div key={label} className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full" style={{ background: c }} />
            {label}
          </div>
        ))}
        <div className="flex items-center gap-2 pt-1">
          <span className="h-px w-4 bg-[#6E9CC4]" /> Radio link
        </div>
        <div className="flex items-center gap-2">
          <span className="h-px w-4 border-t border-dashed border-[#E0A43A]" /> Relay link
        </div>
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ background: HAZARD_COLOR.FIRE }} />
          <span className="h-2 w-2 rounded-full" style={{ background: HAZARD_COLOR.POLLUTION }} />
          <span className="h-2 w-2 rounded-full" style={{ background: HAZARD_COLOR.EXTREME_HEAT }} />
          Hazard zones
        </div>
      </div>
    </div>
  );
}
