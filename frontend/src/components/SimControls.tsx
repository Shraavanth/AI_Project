"use client";

import { Pause, Play, RotateCcw, StepForward } from "lucide-react";
import { useState } from "react";
import { useSim } from "./SimulationProvider";
import { Button, cx } from "./ui";

export function SimControls({ compact = false }: { compact?: boolean }) {
  const { snapshot, act, connection } = useSim();
  const [confirmReset, setConfirmReset] = useState(false);
  if (!snapshot) return null;
  const sim = snapshot.simulation;
  const disabled = connection === "offline";

  return (
    <div className="flex flex-wrap items-center gap-2">
      {sim.running ? (
        <Button size={compact ? "sm" : "md"} onClick={() => act("/api/simulation/pause")} disabled={disabled}>
          <Pause size={15} /> Pause
        </Button>
      ) : (
        <Button size={compact ? "sm" : "md"} variant="primary" onClick={() => act("/api/simulation/resume")} disabled={disabled}>
          <Play size={15} /> Resume
        </Button>
      )}
      {!sim.running && (
        <Button size={compact ? "sm" : "md"} onClick={() => act("/api/simulation/step", { ticks: 1 })} disabled={disabled} title="Advance one simulated second">
          <StepForward size={15} /> Step
        </Button>
      )}
      <div className="flex overflow-hidden rounded-md border border-line" role="group" aria-label="Simulation speed">
        {sim.allowed_speeds.map((s) => (
          <button
            key={s}
            onClick={() => act("/api/simulation/speed", { speed: s })}
            disabled={disabled}
            aria-pressed={sim.speed === s}
            className={cx(
              compact ? "h-7 px-2 text-xs" : "h-9 px-2.5 text-sm",
              "tabular-nums transition-colors",
              sim.speed === s ? "bg-ink text-ground" : "bg-raised text-ink-2 hover:text-ink",
            )}
          >
            {s}x
          </button>
        ))}
      </div>
      {confirmReset ? (
        <span className="flex items-center gap-1.5">
          <Button size={compact ? "sm" : "md"} variant="danger" onClick={async () => { setConfirmReset(false); await act("/api/simulation/reset", undefined, "Simulation reset - fresh fleet deployed. History is kept."); }}>
            Reset now
          </Button>
          <Button size={compact ? "sm" : "md"} variant="ghost" onClick={() => setConfirmReset(false)}>Cancel</Button>
        </span>
      ) : (
        <Button size={compact ? "sm" : "md"} variant="ghost" onClick={() => setConfirmReset(true)} disabled={disabled} title="Redeploy the fleet and clear live incidents">
          <RotateCcw size={15} /> Reset
        </Button>
      )}
    </div>
  );
}
