"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AXIS, ChartTooltip, GRID } from "@/components/charts";
import { useSim } from "@/components/SimulationProvider";
import { Empty, KeyValue, Meter, PageHeader, Panel, Tag, cx } from "@/components/ui";
import { WorkflowStrip } from "@/components/WorkflowStrip";
import {
  HAZARD_COLOR, HAZARD_LABEL, INCIDENT_STATUS_COLOR, INCIDENT_STATUS_LABEL, TASK_LABEL, TASK_STATUS_COLOR,
  fmtDistance, fmtTicks, sentence,
} from "@/lib/format";
import type { IncidentDetail, Incident } from "@/lib/types";
import { usePolling } from "@/lib/usePolling";

const STAGE_COLOR: Record<string, string> = {
  CREATED: "#71879B", REPORTED: "#D99A39", DETECTED: "#D99A39", INVESTIGATING: "#397FB8", CONFIRMED: "#397FB8",
  TASKS_ASSIGNED: "#866CC5", RESPONSE: "#E96C4B", RESPONDING: "#E96C4B", TASK_INTERRUPTED: "#E96C4B",
  COORDINATOR: "#D99A39", REASSIGNED: "#866CC5", NO_REPLACEMENT: "#E96C4B", TASK_CANCELLED: "#71879B",
  NEEDS_INTERVENTION: "#E96C4B", PAUSED: "#D99A39", DISPATCHED: "#397FB8", RESOLVED: "#398C69", REJECTED: "#71879B",
};

const VOTE_COLOR = { SUPPORT: "#398C69", OPPOSE: "#E96C4B", ABSTAIN: "#71879B" };

interface StoredIncident {
  id: string;
  run_id: number;
  type: Incident["type"];
  status: string;
  peak_severity: number;
  resolved_tick: number | null;
  created_tick: number;
  created_at: string;
  resolution_note: string | null;
}

function IncidentDetailView({ id }: { id: string }) {
  const { snapshot } = useSim();
  const { data, error } = usePolling<IncidentDetail>(`/api/incidents/${id}`, 2000);
  const live = snapshot?.incidents.find((i) => i.id === id);
  if (error) return <Empty title="Incident not in the live simulation">{error}. Incidents from earlier runs are listed under &quot;Stored history&quot;.</Empty>;
  if (!data || !snapshot) return <p className="p-6 text-sm text-ink-3">Loading {id}...</p>;
  const color = HAZARD_COLOR[data.type];
  const cons = data.consensus;
  const series = data.severity_history;

  return (
    <div className="space-y-4">
      {live && <WorkflowStrip incident={live} tick={snapshot.tick} />}

      <div className="grid gap-4 2xl:grid-cols-2">
        <Panel title="Severity over time" aside={<span>peak {Math.round(data.peak_severity)} · now {Math.round(data.severity)}</span>}>
          {series.length < 2 ? (
            <p className="py-8 text-center text-sm text-ink-3">Not enough samples yet.</p>
          ) : (
            <div className="h-48">
              <ResponsiveContainer>
                <LineChart data={series} margin={{ top: 6, right: 8, bottom: 0, left: -18 }}>
                  <CartesianGrid {...GRID} />
                  <XAxis dataKey="tick" {...AXIS} type="number" domain={["dataMin", "dataMax"]} tickFormatter={(t) => `${t}s`} />
                  <YAxis domain={[0, 100]} {...AXIS} />
                  <Tooltip content={<ChartTooltip format={(v) => Number(v).toFixed(1)} />} />
                  <Line type="monotone" dataKey="severity" name="Severity" stroke={color} strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          <p className="mt-2 text-xs text-ink-3">
            {data.type === "FIRE" ? "An untreated fire grows by 0.12 per second; each responder on site removes severity every second." : "This hazard does not fade on its own; only response actions reduce it."}
          </p>
        </Panel>

        <Panel title="Summary">
          <dl>
            <KeyValue label="Status"><Tag color={INCIDENT_STATUS_COLOR[data.status] ?? "#76807B"}>{INCIDENT_STATUS_LABEL[data.status] ?? data.status}</Tag></KeyValue>
            <KeyValue label="Severity"><Meter value={data.severity} color={color} unit="" label="Severity" /></KeyValue>
            <KeyValue label="Location">{data.lat.toFixed(5)}, {data.lng.toFixed(5)} · radius {data.radius_m} m</KeyValue>
            <KeyValue label="Agents' estimate">{data.estimated_location ? `${data.estimated_location[0].toFixed(5)}, ${data.estimated_location[1].toFixed(5)}${data.estimate_error_m !== null ? ` (${data.estimate_error_m} m off)` : ""}` : "-"}</KeyValue>
            <KeyValue label="Origin">{data.origin === "OPERATOR" ? "Created on the map (real hazard)" : "Reported by an agent (no known hazard)"}</KeyValue>
            <KeyValue label="Detected after">{data.detected_tick !== null ? fmtTicks(data.detected_tick - data.created_tick) : "-"}</KeyValue>
            <KeyValue label="Confirmed after">{data.confirmed_tick !== null && data.detected_tick !== null ? fmtTicks(data.confirmed_tick - data.detected_tick) : "-"}</KeyValue>
            <KeyValue label="Resolved after">{data.resolved_tick !== null ? fmtTicks(data.resolved_tick - data.created_tick) : "-"}</KeyValue>
            <KeyValue label="Coordinator">{data.coordinator_id ?? "-"}</KeyValue>
          </dl>
          {data.resolution_note && <p className="mt-2 text-sm text-ink-2">{data.resolution_note}</p>}
        </Panel>
      </div>

      <Panel title="Timeline" bodyClassName="px-4 py-3">
        <ol className="relative space-y-3 border-l border-line pl-5">
          {data.timeline.map((t, idx) => (
            <li key={idx} className="relative">
              <span className="absolute -left-[25px] top-1.5 h-2.5 w-2.5 rounded-full border-2 border-surface" style={{ background: STAGE_COLOR[t.stage] ?? "#76807B" }} />
              <div className="flex flex-wrap items-baseline gap-x-2">
                <span className="text-sm font-medium">{sentence(t.stage)}</span>
                <span className="text-2xs tabular-nums text-ink-3">t = {t.tick} s</span>
              </div>
              <p className="text-sm text-ink-2">{t.text}</p>
            </li>
          ))}
        </ol>
      </Panel>

      <Panel title="Consensus evidence" aside={cons ? <span>round {cons.round} · {Math.round(cons.confidence * 100)}% · {sentence(cons.decision)}</span> : null} bodyClassName="overflow-x-auto">
        {!cons ? (
          <Empty title="No consensus round yet">Consensus starts when an agent&apos;s own sensors raise an alert.</Empty>
        ) : (
          <>
            <p className="border-b border-line px-4 py-2.5 text-xs text-ink-3">
              Rule: {cons.rule}. Votes come from each agent&apos;s own sensors: support = same hazard type, oppose = normal and within 300 m, abstain = too far, different pattern or unreachable.
            </p>
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="border-b border-line bg-header text-left text-xs text-ink font-semibold">
                  <th className="px-4 py-2">Agent</th>
                  <th className="px-2 py-2">Vote</th>
                  <th className="px-2 py-2 text-right">Distance</th>
                  <th className="px-2 py-2">Own AI</th>
                  <th className="px-4 py-2">Reason</th>
                </tr>
              </thead>
              <tbody>
                {cons.votes.map((v) => (
                  <tr key={v.agent_id} className="border-b border-line/60 last:border-0">
                    <td className="px-4 py-1.5">{v.agent_id}{v.agent_id === cons.coordinator_id && <span className="ml-1.5 text-2xs text-warn">coordinator</span>}</td>
                    <td className="px-2 py-1.5"><span style={{ color: VOTE_COLOR[v.vote] }}>{sentence(v.vote)}</span></td>
                    <td className="px-2 py-1.5 text-right tabular-nums text-ink-2">{fmtDistance(v.distance_m)}</td>
                    <td className="px-2 py-1.5 text-xs text-ink-2">{v.ai_status === "NORMAL" ? "Normal" : sentence(v.ai_event)} ({v.score.toFixed(3)})</td>
                    <td className="px-4 py-1.5 text-xs text-ink-3">{v.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </Panel>

      <Panel title="Tasks and ownership" aside={<span>{data.tasks.length} tasks</span>} bodyClassName="divide-y divide-line">
        {data.tasks.length === 0 ? (
          <Empty title="No tasks yet">The coordinator assigns tasks once the incident is confirmed.</Empty>
        ) : (
          data.tasks.map((t) => (
            <div key={t.id} className="px-4 py-3">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="font-medium">{TASK_LABEL[t.task_type] ?? t.task_type} <span className="text-xs font-normal text-ink-3">{t.id}{t.optional ? " · optional" : ""}</span></span>
                <span className="text-sm" style={{ color: TASK_STATUS_COLOR[t.status] }}>{sentence(t.status)}</span>
              </div>
              <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs">
                {t.owners.length === 0 && <span className="text-[#f0a597]">Never assigned - no suitable agent</span>}
                {t.owners.map((o, idx) => (
                  <span key={idx} className="flex items-center gap-1.5">
                    {idx > 0 && <span className="text-ink-3">then</span>}
                    <span className={cx("rounded border px-1.5 py-0.5", o.end === "INTERRUPTED" ? "border-[#5a3029] text-[#f0a597] line-through decoration-1" : "border-line text-ink")}>
                      {o.agent_id}
                    </span>
                    <span className="text-ink-3">t {o.from_tick}-{o.to_tick ?? "now"}{o.end ? ` · ${o.end.toLowerCase()}` : ""}</span>
                  </span>
                ))}
              </div>
              {t.task_type !== "INVESTIGATE" && <div className="mt-1.5 text-xs text-ink-3">Severity removed by this task: {t.work_done.toFixed(1)}</div>}
              {t.last_decision.length > 0 && (
                <details className="mt-2 text-xs">
                  <summary className="cursor-pointer text-ink-2 hover:text-ink">Candidates considered ({t.last_decision.length})</summary>
                  <table className="mt-1.5 w-full">
                    <tbody>
                      {t.last_decision.map((r) => (
                        <tr key={r.agent_id} className="border-t border-line">
                          <td className="py-1 pr-2">{r.agent_id}</td>
                          <td className="py-1 pr-2 text-right tabular-nums text-ink-2">{fmtDistance(r.distance_m)}</td>
                          <td className="py-1 pr-2 text-right tabular-nums text-ink-2">{Math.round(r.battery)}%</td>
                          <td className="py-1 pr-2 text-right tabular-nums text-ink-2">{r.score ?? "-"}</td>
                          <td className="py-1 text-ink-3">{r.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </details>
              )}
            </div>
          ))
        )}
      </Panel>

      <div className="grid gap-4 2xl:grid-cols-2">
        <Panel title="Agents affected by the hazard" aside={<span>simulated influence on sensors</span>} bodyClassName="overflow-x-auto">
          {data.affected_agents.length === 0 ? (
            <Empty title="No agent currently affected" />
          ) : (
            <table className="w-full text-sm">
              <tbody>
                {data.affected_agents.map((a) => (
                  <tr key={a.agent_id} className="border-b border-line/60 last:border-0">
                    <td className="px-4 py-1.5">{a.agent_id}</td>
                    <td className="px-2 py-1.5 text-right tabular-nums text-ink-2">{fmtDistance(a.distance_m)}</td>
                    <td className="px-4 py-1.5"><Meter value={a.influence * 100} color={color} unit="" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>
        <Panel title="Messages about this incident" aside={<span>{data.messages.length} recent</span>} bodyClassName="max-h-80 overflow-y-auto scroll-thin">
          {data.messages.length === 0 ? (
            <Empty title="No messages yet" />
          ) : (
            <ul className="divide-y divide-line">
              {data.messages.map((m) => (
                <li key={m.message_id} className="flex items-baseline gap-3 px-4 py-1.5 text-xs">
                  <span className="w-10 shrink-0 tabular-nums text-ink-3">t {m.tick}</span>
                  <span className="w-36 shrink-0 font-medium text-ink">{sentence(m.type)}</span>
                  <span className="text-ink-2">{m.sender} to {m.receiver}{!m.delivered && <span className="text-[#f0a597]"> (dropped)</span>}</span>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </div>
  );
}

function IncidentsPage() {
  const { snapshot } = useSim();
  const params = useSearchParams();
  const router = useRouter();
  const [showStored, setShowStored] = useState(false);
  const stored = usePolling<{ incidents: StoredIncident[] }>(showStored ? "/api/history/incidents" : null, 0);
  if (!snapshot) return <div className="p-6 text-sm text-ink-3">Connecting to the simulation...</div>;
  const selected = params.get("id") ?? snapshot.incidents[0]?.id ?? null;
  const select = (id: string) => router.replace(`/incidents?id=${id}`, { scroll: false });

  return (
    <div className="pb-8">
      <PageHeader title="Incidents and response" subtitle="Each incident's full lifecycle: what the agents sensed, how they voted, who was dispatched, failures and reassignments, and how severity changed." />
      <div className="grid gap-4 px-5 lg:px-6 xl:grid-cols-[300px_minmax(0,1fr)]">
        <Panel
          title={showStored ? "Stored history" : "This run"}
          aside={<button onClick={() => setShowStored((s) => !s)} className="hover:text-ink">{showStored ? "Show live" : "Stored history"}</button>}
          className="xl:sticky xl:top-4 xl:max-h-[calc(100vh-7rem)]"
          bodyClassName="overflow-y-auto scroll-thin"
        >
          {!showStored ? (
            snapshot.incidents.length === 0 ? (
              <Empty title="No incidents yet">Start one from the Area Simulator by choosing a hazard and clicking the map.</Empty>
            ) : (
              <ul className="divide-y divide-line">
                {snapshot.incidents.map((i) => (
                  <li key={i.id}>
                    <button onClick={() => select(i.id)} className={cx("flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors hover:bg-selected/40", selected === i.id ? "bg-selected border-l-4 border-l-primary font-semibold" : "hover:bg-selected/30")}>
                      <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: HAZARD_COLOR[i.type] }} />
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm font-semibold text-ink">{HAZARD_LABEL[i.type]} {i.id}</span>
                        <span className="block text-xs font-medium" style={{ color: INCIDENT_STATUS_COLOR[i.status] }}>{INCIDENT_STATUS_LABEL[i.status] ?? i.status}</span>
                      </span>
                      <span className="text-xs font-mono tabular-nums text-ink-2">{Math.round(i.severity)}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )
          ) : stored.error ? (
            <Empty title="History unavailable">{stored.error}</Empty>
          ) : !stored.data ? (
            <p className="p-4 text-sm text-ink-3">Loading...</p>
          ) : (
            <ul className="divide-y divide-line">
              {stored.data.incidents.map((i) => (
                <li key={i.id} className="px-4 py-2.5">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    <span className="h-2 w-2 rounded-full" style={{ background: HAZARD_COLOR[i.type] }} />
                    {HAZARD_LABEL[i.type]} {i.id}
                  </div>
                  <div className="text-xs text-ink-3">
                    Run {i.run_id} · {INCIDENT_STATUS_LABEL[i.status] ?? i.status} · peak {Math.round(i.peak_severity)}
                    {i.resolved_tick !== null ? ` · ${fmtTicks(i.resolved_tick - i.created_tick)}` : ""}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Panel>
        <div className="min-w-0">
          {selected ? <IncidentDetailView id={selected} /> : (
            <Panel><Empty title="Nothing to show yet">When you create an incident, its detection, consensus votes, task assignments and severity appear here.</Empty></Panel>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<div className="p-6 text-sm text-ink-3">Loading...</div>}>
      <IncidentsPage />
    </Suspense>
  );
}
