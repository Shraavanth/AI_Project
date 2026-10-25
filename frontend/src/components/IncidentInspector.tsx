"use client";

import Link from "next/link";
import { X } from "lucide-react";
import { HAZARD_COLOR, HAZARD_LABEL, INCIDENT_STATUS_COLOR, INCIDENT_STATUS_LABEL, TASK_LABEL, TASK_STATUS_COLOR, fmtTicks, sentence } from "@/lib/format";
import type { Incident } from "@/lib/types";
import { KeyValue, Meter, Tag } from "./ui";

export function IncidentInspector({ incident, tick, onClose, onSelectAgent }: { incident: Incident; tick: number; onClose: () => void; onSelectAgent?: (id: string) => void }) {
  const color = HAZARD_COLOR[incident.type];
  const c = incident.consensus;
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 font-cond text-lg font-bold leading-tight text-ink">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: color }} />
            {HAZARD_LABEL[incident.type]} {incident.id}
          </div>
          <div className="mt-1"><Tag color={INCIDENT_STATUS_COLOR[incident.status] ?? "#71879B"}>{INCIDENT_STATUS_LABEL[incident.status] ?? incident.status}</Tag></div>
        </div>
        <button onClick={onClose} aria-label="Close" className="text-ink-3 hover:text-ink"><X size={16} /></button>
      </div>
      <dl>
        <KeyValue label="Severity"><Meter value={incident.severity} color={color} unit="" label="Severity" /></KeyValue>
        <KeyValue label="Radius">{incident.radius_m} m</KeyValue>
        <KeyValue label="Age">{fmtTicks((incident.resolved_tick ?? tick) - incident.created_tick)}</KeyValue>
        <KeyValue label="Origin">{incident.origin === "OPERATOR" ? "Created on the map" : "Reported by an agent"}</KeyValue>
        <KeyValue label="Coordinator">{incident.coordinator_id ?? "-"}</KeyValue>
        {incident.estimate_error_m !== null && <KeyValue label="Estimate error">{incident.estimate_error_m} m</KeyValue>}
      </dl>
      {c && (
        <div className="rounded-md border border-line bg-input p-3 text-xs shadow-2xs">
          <div className="mb-1.5 flex justify-between text-ink font-medium">
            <span>Consensus round {c.round}</span>
            <span className="text-ink font-bold">{Math.round(c.confidence * 100)}% · {sentence(c.decision)}</span>
          </div>
          <div className="space-y-1 text-ink-2">
            <div><span className="text-green font-semibold">Support</span> {c.supporters.join(", ") || "none"}</div>
            <div><span className="text-red font-semibold">Oppose</span> {c.opposers.join(", ") || "none"}</div>
            <div>Abstain {c.abstained.length}</div>
          </div>
        </div>
      )}
      {incident.tasks.length > 0 && (
        <table className="w-full text-xs">
          <thead>
            <tr className="text-left text-ink-2 border-b border-line"><th className="pb-1 font-semibold">Task</th><th className="pb-1 font-semibold">Agent</th><th className="pb-1 text-right font-semibold">Status</th></tr>
          </thead>
          <tbody>
            {incident.tasks.map((t) => (
              <tr key={t.id} className="border-t border-line">
                <td className="py-1.5 text-ink">{TASK_LABEL[t.task_type] ?? t.task_type}</td>
                <td className="py-1.5">
                  {t.owner_id ? <button className="text-ink font-semibold hover:underline" onClick={() => onSelectAgent?.(t.owner_id!)}>{t.owner_id}</button> : <span className="text-red">none</span>}
                  {t.reassign_count > 0 && <span className="ml-1 text-ink-3">(was {t.previous_owner_id})</span>}
                </td>
                <td className="py-1.5 text-right"><span style={{ color: TASK_STATUS_COLOR[t.status] }} className="font-semibold">{sentence(t.status)}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {incident.resolution_note && <p className="text-xs text-ink-2">{incident.resolution_note}</p>}
      <Link href={`/incidents?id=${incident.id}`} className="inline-block text-sm text-primary font-medium underline-offset-4 hover:text-primary-hover hover:underline">Open timeline and evidence</Link>
    </div>
  );
}
