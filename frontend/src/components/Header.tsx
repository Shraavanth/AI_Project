"use client";

import { useState, useEffect } from "react";
import { RotateCcw, Play, Activity, Clock, CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";

export default function Header() {
  const [time, setTime] = useState<string>("");
  const [isResetting, setIsResetting] = useState(false);
  const [demoStep, setDemoStep] = useState<number | null>(null);
  const [demoMessage, setDemoMessage] = useState<string>("");

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTime(now.toTimeString().split(" ")[0]);
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleReset = async () => {
    setIsResetting(true);
    try {
      await api.resetSimulation();
      window.location.reload();
    } catch (e: any) {
      alert(`Reset failed: ${e.message}`);
    } finally {
      setIsResetting(false);
    }
  };

  const runDemoScenario = async () => {
    try {
      setDemoStep(1);
      setDemoMessage("1/5 Triggering FIRE anomaly event at center (10, 10)...");
      await api.createFireEvent({ center_x: 10, center_y: 10, radius: 3 });
      await new Promise((r) => setTimeout(r, 2000));

      setDemoStep(2);
      setDemoMessage("2/5 Local consensus reached. Simulating primary agent failure...");
      await api.failFireAgentHelper();
      await new Promise((r) => setTimeout(r, 2000));

      setDemoStep(3);
      setDemoMessage("3/5 Failure detected. Triggering self-organizing mesh recovery...");
      await api.recoverNetwork();
      await new Promise((r) => setTimeout(r, 1500));

      setDemoStep(4);
      setDemoMessage("4/5 Autonomous network reorganization verified. State updated!");
      await new Promise((r) => setTimeout(r, 1500));

      setDemoStep(5);
      setDemoMessage("Demo completed! Browse tabs to inspect the full self-organizing workflow.");
      setTimeout(() => {
        setDemoStep(null);
        setDemoMessage("");
      }, 4000);
    } catch (e: any) {
      setDemoMessage(`Demo error: ${e.message}`);
      setTimeout(() => {
        setDemoStep(null);
      }, 3000);
    }
  };

  return (
    <header className="h-16 bg-surface border-b border-border px-6 flex items-center justify-between sticky top-0 z-30 shadow-sm">
      {/* Left: Operational Title / Status */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-secondary-green animate-pulse"></span>
          <span className="editorial-tag text-[10px] tracking-wider text-forest-green">
            AUTONOMOUS ENVIRONMENTAL INTELLIGENCE
          </span>
        </div>
        <div className="h-4 w-px bg-border"></div>
        <div className="flex items-center gap-1.5 text-xs text-secondary-text font-mono">
          <Clock className="w-3.5 h-3.5 text-secondary-text" />
          <span className="tabular-nums">{time || "00:00:00"} UTC</span>
        </div>
      </div>

      {/* Center: Live Demo Workflow Banner if Active */}
      {demoStep !== null && (
        <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-muted-sage/70 border border-secondary-green/30 text-forest-green text-xs font-mono">
          {demoStep === 5 ? (
            <CheckCircle2 className="w-4 h-4 text-forest-green" />
          ) : (
            <div className="w-3 h-3 rounded-full border-2 border-forest-green border-t-transparent animate-spin" />
          )}
          <span>{demoMessage}</span>
        </div>
      )}

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        <button
          onClick={runDemoScenario}
          disabled={demoStep !== null}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded bg-forest-green hover:bg-forest-green-light text-surface text-xs font-medium transition shadow-sm disabled:opacity-50"
        >
          <Play className="w-3 h-3 fill-current text-botanical" />
          <span>Run Guided Demo</span>
        </button>

        <button
          onClick={handleReset}
          disabled={isResetting}
          className="flex items-center gap-2 px-3 py-1.5 rounded bg-surface hover:bg-surface-muted text-forest-green text-xs font-medium border border-border transition shadow-editorial disabled:opacity-50"
          title="Reset Simulation to Initial State"
        >
          <RotateCcw
            className={`w-3.5 h-3.5 ${
              isResetting ? "animate-spin text-secondary-green" : "text-secondary-green"
            }`}
          />
          <span>Reset Baseline</span>
        </button>
      </div>
    </header>
  );
}
