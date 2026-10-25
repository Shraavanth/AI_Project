"use client";

import React, { useState } from "react";
import {
  ShieldAlert,
  Radio,
  Activity,
  AlertTriangle,
  RotateCcw,
  ZapOff,
  Crosshair,
  CheckCircle2,
  ChevronRight,
  TrendingUp,
  Info,
  X,
} from "lucide-react";
import type { Agent, CoverageSummary } from "@/lib/types";

interface CoveragePanelProps {
  coverage?: CoverageSummary;
  agents: Agent[];
  onFailDrone: (droneId: string) => void;
  onRestoreDrone: (droneId: string) => void;
  onSelectAgent?: (id: string) => void;
}

export function CoveragePanel({
  coverage,
  agents,
  onFailDrone,
  onRestoreDrone,
  onSelectAgent,
}: CoveragePanelProps) {
  const [minimized, setMinimized] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const monitorDrones = agents.filter((a) => a.type === "MONITOR_DRONE");

  const total = coverage?.total_monitors ?? monitorDrones.length;
  const active = coverage?.active_monitors ?? monitorDrones.filter((a) => a.status !== "FAILED").length;
  const failed = coverage?.failed_monitors ?? monitorDrones.filter((a) => a.status === "FAILED").length;
  const offline = coverage?.offline_monitors ?? 0;
  const investigating = coverage?.investigating_monitors ?? 0;
  const coveragePct = coverage?.coverage_pct ?? (total > 0 ? Math.round((active / total) * 100) : 100);
  const uncoveredCount = coverage?.uncovered_count ?? 0;
  const reassignedTasksCount = coverage?.reassigned_tasks_count ?? 0;
  const boundaryDetectionsCount = coverage?.boundary_detections_count ?? 0;
  const provisionalCount = coverage?.provisional_incidents?.length ?? 0;
  const notifications = coverage?.notifications ?? [];
  const operationalWarning = coverage?.operational_warning;

  return (
    <div className="rounded-xl border border-line bg-surface p-3.5 shadow-md transition-all">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-line pb-2.5">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/20 text-primary">
            <Radio size={16} className="animate-pulse" />
          </div>
          <div>
            <h3 className="font-cond text-sm font-bold tracking-wide text-ink uppercase">
              Drone Health & Coverage Engine
            </h3>
            <p className="text-2xs text-ink-2 font-medium">Fault-tolerant heartbeat surveillance</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowInfo((s) => !s)}
            className={`rounded p-1 text-xs transition-colors flex items-center gap-1 ${
              showInfo ? "bg-selected text-ink font-semibold" : "text-ink-2 hover:bg-selected/40 hover:text-ink"
            }`}
            title="What does this engine do?"
          >
            <Info size={13} />
            <span className="hidden sm:inline">Info</span>
          </button>
          <button
            onClick={() => setMinimized((m) => !m)}
            className="rounded p-1 text-ink-2 hover:bg-selected/40 hover:text-ink text-xs"
          >
            {minimized ? "Expand" : "Collapse"}
          </button>
        </div>
      </div>

      {showInfo && !minimized && (
        <div className="my-2.5 rounded-lg border border-primary/40 bg-selected/40 p-3 text-xs leading-relaxed text-ink shadow-2xs">
          <div className="flex items-center justify-between pb-1.5 border-b border-line">
            <span className="font-semibold text-primary text-xs flex items-center gap-1.5">
              <Activity size={13} className="text-primary" /> How the Coverage Engine Works
            </span>
            <button
              onClick={() => setShowInfo(false)}
              className="text-ink-2 hover:text-ink"
              title="Close info"
            >
              <X size={13} />
            </button>
          </div>
          <p className="mt-2 text-2xs text-ink-2 font-medium">
            The <strong>Drone Health & Coverage Engine</strong> ensures continuous, gap-free aerial surveillance across the entire disaster zone even during hardware failures or link drops:
          </p>
          <ul className="mt-2 space-y-1.5 text-2xs text-ink list-disc list-inside">
            <li>
              <strong className="text-ink font-semibold">Heartbeat Health Monitoring:</strong> Active monitor drones stream periodic heartbeats (battery, telemetry, status). Missing heartbeats trigger instant failure detection.
            </li>
            <li>
              <strong className="text-ink font-semibold">Blind Spot Prevention:</strong> If a drone fails, its 450m sector is automatically marked as a coverage deficit to prevent undetected incidents.
            </li>
            <li>
              <strong className="text-ink font-semibold">Dynamic Reassignment:</strong> The engine automatically instructs the closest available monitor drone to expand its patrol path and cover the orphaned sector.
            </li>
            <li>
              <strong className="text-ink font-semibold">Boundary Cross-Verification:</strong> Incidents detected within an 80m boundary margin between sectors trigger peer validation between adjacent drones before dispatch.
            </li>
            <li>
              <strong className="text-ink font-semibold">Seamless Reintegration:</strong> Restored drones automatically resume patrolling their sectors with smooth rebalancing.
            </li>
          </ul>
        </div>
      )}

      {!minimized && (
        <div className="mt-3 space-y-3">
          {/* Operational Warning Alert */}
          {operationalWarning && (
            <div className="flex items-start gap-2 rounded-lg border border-amber/40 bg-amber/10 p-2 text-xs text-amber animate-pulse shadow-2xs">
              <AlertTriangle size={15} className="mt-0.5 shrink-0 text-amber" />
              <div className="min-w-0">
                <span className="font-semibold">Coverage Deficit Warning</span>
                <p className="text-2xs opacity-90">{operationalWarning}</p>
              </div>
            </div>
          )}

          {/* Primary Coverage Metric Banner */}
          <div className="grid grid-cols-2 gap-2 rounded-lg bg-panel border border-line p-2.5">
            <div>
              <div className="flex items-center justify-between text-2xs text-ink-2">
                <span className="font-medium">Surveillance Coverage</span>
                <span className="font-mono font-bold text-ink">{coveragePct}%</span>
              </div>
              <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-line/60">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${coveragePct}%`,
                    backgroundColor:
                      coveragePct >= 95 ? "#398C69" : coveragePct >= 75 ? "#D99A39" : "#E96C4B",
                  }}
                />
              </div>
            </div>
            <div className="border-l border-line pl-2.5">
              <div className="text-2xs text-ink-2">Tolerance Buffer</div>
              <div className="flex items-baseline gap-1">
                <span className="font-mono text-xs font-semibold text-primary">
                  {coverage?.nominal_radius_m ?? 450}m
                </span>
                <span className="text-2xs text-ink-3">
                  (+{coverage?.boundary_tolerance_m ?? 80}m buffer)
                </span>
              </div>
            </div>
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-3 gap-1.5 text-center text-xs">
            <div className="rounded-lg border border-line bg-input p-2 shadow-2xs">
              <div className="text-2xs text-ink-2">Active Monitors</div>
              <div className="font-cond text-sm font-bold text-green tabular-nums">
                {active} <span className="text-2xs font-normal text-ink-3">/ {total}</span>
              </div>
            </div>
            <div className="rounded-lg border border-line bg-input p-2 shadow-2xs">
              <div className="text-2xs text-ink-2">Failed / Offline</div>
              <div
                className={`font-cond text-sm font-bold tabular-nums ${
                  failed > 0 || offline > 0 ? "text-red" : "text-ink"
                }`}
              >
                {failed} <span className="text-2xs font-normal text-ink-3">({offline} off)</span>
              </div>
            </div>
            <div className="rounded-lg border border-line bg-input p-2 shadow-2xs">
              <div className="text-2xs text-ink-2">Investigating</div>
              <div className="font-cond text-sm font-bold text-purple tabular-nums">
                {investigating}
              </div>
            </div>
            <div className="rounded-lg border border-line bg-input p-2 shadow-2xs">
              <div className="text-2xs text-ink-2">Uncovered Areas</div>
              <div
                className={`font-cond text-sm font-bold tabular-nums ${
                  uncoveredCount > 0 ? "text-amber" : "text-ink"
                }`}
              >
                {uncoveredCount}
              </div>
            </div>
            <div className="rounded-lg border border-line bg-input p-2 shadow-2xs">
              <div className="text-2xs text-ink-2">Reassigned Tasks</div>
              <div className="font-cond text-sm font-bold text-primary tabular-nums">
                {reassignedTasksCount}
              </div>
            </div>
            <div className="rounded-lg border border-line bg-input p-2 shadow-2xs">
              <div className="text-2xs text-ink-2">Boundary Checks</div>
              <div className="font-cond text-sm font-bold text-primary tabular-nums">
                {boundaryDetectionsCount}
                {provisionalCount > 0 && (
                  <span className="text-2xs font-normal text-amber"> ({provisionalCount} prov)</span>
                )}
              </div>
            </div>
          </div>

          {/* Monitor Drone Health Table & Quick Fault Injection Controls */}
          <div>
            <div className="mb-1.5 flex items-center justify-between text-2xs font-bold uppercase tracking-wider text-ink-2">
              <span>Active Monitor Fleet & Fault Injection</span>
              <span>Heartbeat / Status</span>
            </div>
            <div className="max-h-36 overflow-y-auto rounded-lg border border-line bg-input divide-y divide-line/60 text-xs scroll-thin shadow-2xs">
              {monitorDrones.map((drone) => {
                const isFailed = drone.status === "FAILED";
                const isRecovering = drone.status === "RECOVERING";
                return (
                  <div
                    key={drone.id}
                    className="flex items-center justify-between px-2.5 py-1.5 hover:bg-selected/40 transition-colors"
                  >
                    <button
                      onClick={() => onSelectAgent?.(drone.id)}
                      className="flex items-center gap-2 text-left"
                    >
                      <span
                        className={`h-2 w-2 rounded-full ${
                          isFailed
                            ? "bg-red animate-ping"
                            : isRecovering
                            ? "bg-amber"
                            : "bg-green"
                        }`}
                      />
                      <span className="font-mono text-xs font-semibold text-ink">{drone.id}</span>
                      <span className="text-2xs text-ink-2">
                        {Math.round(drone.battery)}% batt
                      </span>
                    </button>

                    <div className="flex items-center gap-1.5">
                      <span className="text-2xs font-mono uppercase text-ink-2 font-medium">
                        {drone.status}
                      </span>
                      {isFailed ? (
                        <button
                          onClick={() => onRestoreDrone(drone.id)}
                          className="flex items-center gap-1 rounded bg-green/15 px-2 py-0.5 text-2xs font-medium text-green hover:bg-green/25 border border-green/30"
                          title="Restore drone health and reintegrate"
                        >
                          <RotateCcw size={11} /> Restore
                        </button>
                      ) : (
                        <button
                          onClick={() => onFailDrone(drone.id)}
                          disabled={isRecovering}
                          className="flex items-center gap-1 rounded bg-red/15 px-2 py-0.5 text-2xs font-medium text-red hover:bg-red/25 border border-red/30 disabled:opacity-40"
                          title="Simulate drone failure to test automatic coverage recovery"
                        >
                          <ZapOff size={11} /> Fail
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Real-time Recovery & Reassignment Notification Stream */}
          <div>
            <div className="mb-1 flex items-center justify-between text-2xs font-bold uppercase tracking-wider text-ink-2">
              <span>Coverage Recovery Event Stream</span>
              <span className="font-mono text-2xs text-ink-3">REAL-TIME</span>
            </div>
            <div className="max-h-28 overflow-y-auto rounded-lg border border-line bg-input p-2 text-xs font-mono text-ink space-y-1 scroll-thin shadow-2xs">
              {notifications.length === 0 ? (
                <div className="text-center text-2xs text-ink-3 py-2">
                  All monitor drones operating nominally.
                </div>
              ) : (
                notifications.slice(-6).map((notif, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-1.5 text-2xs leading-relaxed"
                  >
                    <ChevronRight size={11} className="mt-0.5 shrink-0 text-primary" />
                    <span
                      className={
                        notif.message.includes("FAILURE DETECTED")
                          ? "text-red font-semibold"
                          : notif.message.includes("reassignment") || notif.message.includes("assigned")
                          ? "text-primary font-medium"
                          : notif.message.includes("restored") || notif.message.includes("reintegrated")
                          ? "text-green font-medium"
                          : "text-ink"
                      }
                    >
                      {notif.message}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
