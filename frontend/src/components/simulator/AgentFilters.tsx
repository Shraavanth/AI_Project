"use client";

import React from "react";
import { RotateCcw, Filter, Check } from "lucide-react";
import { STATUS_COLOR } from "@/lib/format";
import type { Agent, AgentType } from "@/lib/types";
import { cx } from "@/components/ui";

const AGENT_TYPE_OPTIONS: { type: AgentType; label: string }[] = [
  { type: "MONITOR_DRONE", label: "Monitoring Drones" },
  { type: "FIRE_DRONE", label: "Fire Response Drones" },
  { type: "SPRINKLER", label: "Sprinkler Units" },
  { type: "POLLUTION_UNIT", label: "Pollution Units" },
  { type: "COOLING_UNIT", label: "Cooling Units" },
];

const STATUS_OPTIONS: { status: string; label: string; color: string }[] = [
  { status: "NORMAL", label: "Normal", color: "#398C69" },
  { status: "DETECTING", label: "Detecting", color: "#D99A39" },
  { status: "MOVING", label: "Moving", color: "#397FB8" },
  { status: "COORDINATING", label: "Coordinating", color: "#397FB8" },
  { status: "RESPONDING", label: "Responding", color: "#E96C4B" },
  { status: "FAILED", label: "Failed", color: "#7F8992" },
];

interface AgentFiltersProps {
  agents: Agent[];
  selectedTypes: AgentType[];
  onToggleType: (t: AgentType) => void;
  selectedStatuses: string[];
  onToggleStatus: (s: string) => void;
  onResetFilters: () => void;
  filteredCount: number;
  totalCount: number;
}

export function AgentFilters({
  agents,
  selectedTypes,
  onToggleType,
  selectedStatuses,
  onToggleStatus,
  onResetFilters,
  filteredCount,
  totalCount,
}: AgentFiltersProps) {
  const isFiltered = selectedTypes.length > 0 || selectedStatuses.length > 0;

  // Counts by type
  const typeCounts = React.useMemo(() => {
    const map: Record<string, number> = {};
    for (const a of agents) {
      map[a.type] = (map[a.type] || 0) + 1;
    }
    return map;
  }, [agents]);

  // Counts by status
  const statusCounts = React.useMemo(() => {
    const map: Record<string, number> = {};
    for (const a of agents) {
      map[a.status] = (map[a.status] || 0) + 1;
    }
    return map;
  }, [agents]);

  return (
    <div className="space-y-3.5">
      {/* Header Summary & Reset */}
      <div className="flex items-center justify-between text-xs pb-1 border-b border-line">
        <span className="text-ink-2">
          Showing <span className="font-semibold text-ink">{filteredCount}</span> of{" "}
          <span className="font-semibold text-ink">{totalCount}</span> agents
        </span>
        {isFiltered && (
          <button
            type="button"
            onClick={onResetFilters}
            className="flex items-center gap-1 text-2xs text-primary hover:text-primary-hover font-semibold"
          >
            <RotateCcw size={11} /> Reset
          </button>
        )}
      </div>

      {/* 1. Filter by Agent Type */}
      <div>
        <label className="text-2xs font-bold uppercase tracking-wider text-ink-2 block mb-1.5">
          Agent Type:
        </label>
        <div className="space-y-1">
          {AGENT_TYPE_OPTIONS.map((opt) => {
            const isSelected = selectedTypes.includes(opt.type);
            const count = typeCounts[opt.type] || 0;

            return (
              <button
                key={opt.type}
                type="button"
                onClick={() => onToggleType(opt.type)}
                className={cx(
                  "w-full flex items-center justify-between rounded-md px-2.5 py-1.5 text-xs text-left transition-all border shadow-2xs",
                  isSelected
                    ? "bg-selected text-ink border-primary font-semibold"
                    : "bg-surface text-ink hover:bg-selected/40 border-line"
                )}
              >
                <div className="flex items-center gap-2">
                  <div
                    className={cx(
                      "h-3.5 w-3.5 rounded border flex items-center justify-center text-white",
                      isSelected ? "bg-primary border-primary" : "border-line bg-input"
                    )}
                  >
                    {isSelected && <Check size={10} />}
                  </div>
                  <span>{opt.label}</span>
                </div>
                <span className="font-mono text-2xs tabular-nums text-ink-3">
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. Filter by Agent Status */}
      <div>
        <label className="text-2xs font-bold uppercase tracking-wider text-ink-2 block mb-1.5">
          Operational Status:
        </label>
        <div className="grid grid-cols-2 gap-1.5">
          {STATUS_OPTIONS.map((opt) => {
            const isSelected = selectedStatuses.includes(opt.status);
            const count = statusCounts[opt.status] || 0;

            return (
              <button
                key={opt.status}
                type="button"
                onClick={() => onToggleStatus(opt.status)}
                className={cx(
                  "flex items-center justify-between rounded-md px-2 py-1.5 text-2xs text-left transition-all border shadow-2xs",
                  isSelected
                    ? "bg-selected text-ink border-primary font-semibold"
                    : "bg-surface text-ink hover:bg-selected/40 border-line"
                )}
              >
                <div className="flex items-center gap-1.5 min-w-0">
                  <span
                    className="h-2 w-2 rounded-full shrink-0"
                    style={{ backgroundColor: opt.color }}
                  />
                  <span className="truncate">{opt.label}</span>
                </div>
                <span className="font-mono tabular-nums text-ink-3 shrink-0 ml-1">
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
