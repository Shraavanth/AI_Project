"use client";

import { X } from "lucide-react";
import { useSim } from "./SimulationProvider";

const COLOR = { ok: "#5FB37C", error: "#E0533D", info: "#5B9BD5" };

export function Toasts() {
  const { toasts, dismiss } = useSim();
  return (
    <div className="pointer-events-none fixed left-1/2 top-3 z-[1300] flex w-[min(420px,calc(100vw-2rem))] -translate-x-1/2 flex-col gap-2" aria-live="polite">
      {toasts.map((t) => (
        <div
          key={t.id}
          role={t.kind === "error" ? "alert" : "status"}
          className="pointer-events-auto flex items-start gap-3 rounded-md border border-line bg-raised px-3 py-2.5 text-sm shadow-lg shadow-black/30"
          style={{ borderLeft: `3px solid ${COLOR[t.kind]}` }}
        >
          <span className="flex-1 text-ink">{t.text}</span>
          <button onClick={() => dismiss(t.id)} aria-label="Dismiss" className="text-ink-3 hover:text-ink">
            <X size={15} />
          </button>
        </div>
      ))}
    </div>
  );
}
