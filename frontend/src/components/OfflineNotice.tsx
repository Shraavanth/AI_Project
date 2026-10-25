"use client";

import { API_URL } from "@/lib/api";
import { useSim } from "./SimulationProvider";

/** Full-width notice shown when the backend cannot be reached at all. */
export function OfflineNotice() {
  const { connection, snapshot } = useSim();
  if (connection !== "offline") return null;
  return (
    <div role="alert" className="border-b border-[#5a3029] bg-[#2a1b18] px-5 py-2.5 text-sm text-[#f3b7aa]">
      Cannot reach the backend at <span className="text-ink">{API_URL}</span>.{" "}
      {snapshot ? "Showing the last state received - controls are disabled until it reconnects." : "Start it with: uvicorn backend.main:app --port 8000"}
    </div>
  );
}
