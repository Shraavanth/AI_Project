"use client";

import Link from "next/link";
import { Move, Power, RotateCcw, X } from "lucide-react";
import { AgentGlyph } from "./AgentGlyph";
import { useSim } from "./SimulationProvider";
import { Button, KeyValue, Meter, StatusPill, Tag } from "./ui";
import { STATUS_COLOR, TASK_LABEL, fmtDistance } from "@/lib/format";
import type { Agent } from "@/lib/types";

export const SENSOR_META: { key: keyof Agent["readings"]; label: string; unit: string; digits: number }[] = [
  { key: "temperature", label: "Temperature", unit: "°C", digits: 1 },
  { key: "humidity", label: "Humidity", unit: "%", digits: 0 },
  { key: "smoke", label: "Smoke", unit: "", digits: 2 },
  { key: "co2", label: "CO₂", unit: "ppm", digits: 0 },
  { key: "air_quality", label: "Air quality", unit: "AQI", digits: 0 },
  { key: "soil_moisture", label: "Soil moisture", unit: "%", digits: 0 },
];

export function AiBadge({ ai }: { ai: Agent["ai"] }) {
  if (ai.status === "NORMAL") return <Tag color="#398C69">Normal · {ai.score.toFixed(3)}</Tag>;
  return <Tag color="#D99A39">Anomaly · {ai.event.replace("_", " ").toLowerCase()} · {ai.score.toFixed(3)}</Tag>;
}

export function ReadingsGrid({ agent }: { agent: Agent }) {
  return (
    <dl className="grid grid-cols-3 gap-px overflow-hidden rounded-md border border-line bg-line shadow-2xs">
      {SENSOR_META.map((m) => (
        <div key={m.key} className="bg-surface px-2.5 py-2">
          <dt className="text-2xs text-ink-2 font-medium">{m.label}</dt>
          <dd className="font-cond text-base font-bold tabular-nums text-ink">
            {agent.readings[m.key].toFixed(m.digits)}
            <span className="ml-0.5 text-2xs font-normal text-ink-3">{m.unit}</span>
          </dd>
        </div>
      ))}
    </dl>
  );
}

export function AgentInspector({ agent, onClose, onMove, moving }: { agent: Agent; onClose: () => void; onMove?: () => void; moving?: boolean }) {
  const { act, connection } = useSim();
  const failed = agent.status === "FAILED";
  const offline = connection === "offline";
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <AgentGlyph type={agent.type} color={STATUS_COLOR[agent.status] ?? "#71879B"} failed={failed} size={18} />
          <div>
            <div className="font-cond text-lg font-bold leading-tight text-ink">{agent.id}</div>
            <div className="text-xs text-ink-2 font-medium">{agent.type_label}</div>
          </div>
        </div>
        <button onClick={onClose} aria-label="Close" className="text-ink-3 hover:text-ink">
          <X size={16} />
        </button>
      </div>

      <dl>
        <KeyValue label="Status"><StatusPill status={agent.status} /></KeyValue>
        <KeyValue label="Battery"><Meter value={agent.battery} label="Battery" /></KeyValue>
        <KeyValue label="Local AI"><AiBadge ai={agent.ai} /></KeyValue>
        <KeyValue label="Neighbours">{agent.neighbors.length ? agent.neighbors.length : <span className="text-[#f0a597]">none</span>}</KeyValue>
        {agent.coordinator_of.length > 0 && <KeyValue label="Coordinating">{agent.coordinator_of.join(", ")}</KeyValue>}
        <KeyValue label="Task">
          {agent.task_id ? (
            <span>{TASK_LABEL[agent.task_type ?? ""] ?? agent.task_type} · {agent.incident_id}</span>
          ) : (
            <span className="text-ink-3">{agent.destination_label ?? "None"}</span>
          )}
        </KeyValue>
        {agent.task_progress !== null && <KeyValue label="Task progress"><Meter value={agent.task_progress * 100} color="#A98BE0" /></KeyValue>}
        {failed && agent.failure_reason && <KeyValue label="Failure">{agent.failure_reason.replace(/_/g, " ").toLowerCase()}</KeyValue>}
        <KeyValue label="Travelled">{fmtDistance(agent.distance_travelled_m)}</KeyValue>
      </dl>

      <ReadingsGrid agent={agent} />
      {agent.sensor_override && <p className="text-xs text-[#ecd29b]">Sensor readings are being overridden by the operator.</p>}

      <div className="flex flex-wrap gap-2">
        {failed ? (
          <Button onClick={() => act(`/api/agents/${agent.id}/restore`, undefined, `${agent.id} restored - rebooting.`)} disabled={offline}>
            <RotateCcw size={15} /> Restore
          </Button>
        ) : (
          <Button variant="danger" onClick={() => act(`/api/agents/${agent.id}/fail`, undefined, `${agent.id} failed. Watch the neighbours detect it.`)} disabled={offline || agent.status === "RECOVERING"}>
            <Power size={15} /> Fail agent
          </Button>
        )}
        {agent.mobile && onMove && !failed && !agent.task_id && (
          <Button onClick={onMove} variant={moving ? "primary" : "secondary"} disabled={offline}>
            <Move size={15} /> {moving ? "Click destination" : "Move"}
          </Button>
        )}
        <Link href={`/agents?id=${agent.id}`} className="inline-flex h-9 items-center px-2 text-sm text-ink-2 underline-offset-4 hover:text-ink hover:underline">
          Full details
        </Link>
      </div>
    </div>
  );
}
