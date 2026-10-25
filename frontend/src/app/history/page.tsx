"use client";

import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  Flame,
  CloudFog,
  Thermometer,
  ShieldAlert,
  Users,
  Radio,
  CheckCircle2,
  Clock,
  ArrowRight,
  TrendingDown,
  Activity,
  Layers,
  ChevronRight,
  Sparkles,
  MessageSquare,
} from "lucide-react";
import { AXIS, ChartTooltip, GRID, LegendRow, SERIES } from "@/components/charts";
import { Button, Empty, PageHeader, Panel, cx } from "@/components/ui";
import { CATEGORY_COLOR, HAZARD_COLOR, HAZARD_LABEL, INCIDENT_STATUS_LABEL, TASK_LABEL, fmtTime, sentence } from "@/lib/format";
import type { IncidentType } from "@/lib/types";
import { usePolling } from "@/lib/usePolling";

interface HistoryEntry {
  id: number; run_id: number; tick: number; category: string; title: string; message: string;
  agent_id: string | null; incident_id: string | null; timestamp: string;
}
interface StoredMessage {
  message_id: string; run_id: number; tick: number; sender: string; receiver: string; type: string;
  incident_id: string | null; hops: number | null; delivered: boolean; timestamp: string;
}
interface FailureRow {
  failure_id: string; agent_id: string; reason: string; status_before: string; task_id: string | null; incident_id: string | null;
  failed_tick: number; detected_tick: number | null; detected_by: string | null; detection_method: string | null;
  reassigned_to: string | null; reassigned_tick: number | null; restored_tick: number | null; failed_at: string;
}
interface TaskEvent {
  task_id: string; incident_id: string; task_type: string; event: string; from_agent: string | null; to_agent: string | null;
  reason: string; tick: number; timestamp: string;
}
interface StoredIncidentTask {
  id: string;
  incident_id: string;
  task_type: string;
  capability: string;
  status: string;
  owner_id: string;
  previous_owner_id: string | null;
  reassign_count: number;
  progress: number;
  work_done: number;
  optional: boolean;
}
interface StoredIncidentTimeline {
  tick: number;
  stage: string;
  text: string;
}
interface StoredIncident {
  id: string;
  run_id: number;
  type: IncidentType;
  origin: string;
  physical: boolean;
  status: string;
  lat: number;
  lng: number;
  radius_m: number;
  initial_severity: number;
  severity: number;
  peak_severity: number;
  coordinator_id: string | null;
  consensus_confidence: number | null;
  supporters: number;
  opposers: number;
  detectors: string[];
  tasks: StoredIncidentTask[];
  timeline: StoredIncidentTimeline[];
  rejections: number;
  created_tick: number;
  detected_tick: number | null;
  confirmed_tick: number | null;
  response_started_tick: number | null;
  resolved_tick: number | null;
  resolution_note: string | null;
  created_at: string;
}
interface Analytics {
  run_id: number;
  incidents: { total: number; by_type: Record<string, number>; by_status: Record<string, number> };
  resolution_times: { incident_id: string; type: IncidentType; total_s: number; detection_s: number | null; confirmation_s: number | null; response_start_s: number | null; physical: boolean }[];
  average_resolution_s: number | null;
  average_detection_s: number | null;
  tasks: { by_status: Record<string, number>; reassigned: number; total: number };
  response_durations: { task_id: string; task_type: string; owner_id: string; travel_s: number | null; total_s: number; reassigned: boolean }[];
  failures: { total: number; by_reason: Record<string, number>; by_detection_method: Record<string, number>; restored: number; reassigned: number; average_detection_delay_s: number | null; average_reassignment_delay_s: number | null };
  network: { reorganizations: number; average_compute_ms: number | null; stayed_connected: number };
  messages_by_type: Record<string, number>;
  environment_series: { tick: number; avg_temperature: number; max_temperature: number; avg_smoke: number; max_smoke: number; avg_co2: number; max_co2: number; max_aqi: number; anomalous: number }[];
  availability_series: { tick: number; operational: number; offline: number }[];
  severity_series: Record<string, { tick: number; severity: number; acting: number }[]>;
}

const CATEGORIES = ["ALL", "INCIDENT", "DETECTION", "CONSENSUS", "COORDINATION", "TASK", "RESPONSE", "FAILURE", "RECOVERY", "NETWORK", "AGENT", "SIMULATION"];
const MESSAGE_TYPES = ["", "INCIDENT_ALERT", "SENSOR_EVIDENCE", "CONSENSUS_UPDATE", "COORDINATOR_CHANGE", "TASK_PROPOSAL", "TASK_ACCEPTED", "FAILURE_ALERT", "TASK_REASSIGNED", "RESPONSE_PROGRESS", "TASK_COMPLETED"];
const TABS = ["Incident reports", "Timeline", "Messages", "Failures and reassignment", "Analytics"] as const;

function Timeline() {
  const [category, setCategory] = useState("ALL");
  const { data, error, reload, loading } = usePolling<{ history: HistoryEntry[] }>(`/api/history?category=${category}&limit=300`, 5000);
  return (
    <Panel
      title="Activity timeline"
      aside={<Button size="sm" variant="ghost" onClick={reload} disabled={loading}>Refresh</Button>}
      bodyClassName=""
    >
      <div className="flex flex-wrap gap-1.5 border-b border-line bg-panel/30 px-4 py-2.5">
        {CATEGORIES.map((c) => (
          <button
            key={c}
            onClick={() => setCategory(c)}
            aria-pressed={category === c}
            className={cx(
              "rounded px-2.5 py-1 text-xs font-medium transition-colors border",
              category === c
                ? "bg-primary text-white border-primary shadow-xs"
                : "bg-input text-ink-2 border-line hover:bg-selected/40 hover:text-ink"
            )}
          >
            {c === "ALL" ? "All" : sentence(c)}
          </button>
        ))}
      </div>
      {error ? <Empty title="History unavailable">{error}</Empty> : !data ? <p className="p-4 text-sm text-ink-3">Loading...</p> : data.history.length === 0 ? (
        <Empty title="Nothing recorded in this category yet" />
      ) : (
        <ol className="divide-y divide-line">
          {data.history.map((h) => (
            <li key={h.id} className="grid grid-cols-[70px_10px_minmax(0,1fr)] gap-3 px-4 py-2.5 hover:bg-selected/20 transition-colors sm:grid-cols-[90px_10px_minmax(0,1fr)_auto]">
              <span className="text-xs tabular-nums text-ink-3">{fmtTime(h.timestamp)}</span>
              <span className="mt-1.5 h-2 w-2 rounded-full" style={{ background: CATEGORY_COLOR[h.category] ?? "#71879B" }} />
              <div className="min-w-0">
                <div className="text-sm font-semibold text-ink">{h.title}</div>
                <p className="text-xs leading-relaxed text-ink-2">{h.message}</p>
              </div>
              <span className="hidden text-2xs tabular-nums text-ink-3 sm:block">run {h.run_id} · t {h.tick}</span>
            </li>
          ))}
        </ol>
      )}
    </Panel>
  );
}

function Messages() {
  const [type, setType] = useState("");
  const { data, error } = usePolling<{ messages: StoredMessage[] }>(`/api/history/messages?limit=300${type ? `&type=${type}` : ""}`, 5000);
  return (
    <Panel
      title="Agent-to-agent messages"
      aside={
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="h-7 rounded border border-line bg-input px-2 text-xs text-ink focus:border-primary focus:outline-none"
          aria-label="Message type"
        >
          {MESSAGE_TYPES.map((t) => <option key={t} value={t}>{t ? sentence(t) : "All types"}</option>)}
        </select>
      }
      bodyClassName="overflow-x-auto"
    >
      {error ? <Empty title="Messages unavailable">{error}</Empty> : !data ? <p className="p-4 text-sm text-ink-3">Loading...</p> : data.messages.length === 0 ? (
        <Empty title="No messages stored yet">Messages are exchanged when agents detect, vote on and respond to incidents.</Empty>
      ) : (
        <table className="w-full min-w-[640px] text-sm">
          <thead>
            <tr className="border-b border-line bg-header text-left text-xs text-ink font-semibold">
              <th className="px-4 py-2 font-semibold">Time</th><th className="px-2 py-2 font-semibold">Type</th><th className="px-2 py-2 font-semibold">From</th>
              <th className="px-2 py-2 font-semibold">To</th><th className="px-2 py-2 font-semibold">Incident</th><th className="px-4 py-2 text-right font-semibold">Route</th>
            </tr>
          </thead>
          <tbody>
            {data.messages.map((m) => (
              <tr key={m.message_id + m.run_id} className="border-b border-line/60 hover:bg-selected/20 transition-colors last:border-0">
                <td className="px-4 py-1.5 text-xs tabular-nums text-ink-3">{fmtTime(m.timestamp)}</td>
                <td className="px-2 py-1.5 font-medium text-ink">{sentence(m.type)}</td>
                <td className="px-2 py-1.5 font-mono text-primary font-medium">{m.sender}</td>
                <td className="px-2 py-1.5 font-mono text-primary font-medium">{m.receiver}</td>
                <td className="px-2 py-1.5 text-ink-2">{m.incident_id ?? "-"}</td>
                <td className="px-4 py-1.5 text-right text-xs">{m.delivered ? <span className="text-ink-3">{m.hops === 1 ? "direct" : `${m.hops} hops`}</span> : <span className="font-semibold text-respond">dropped</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Panel>
  );
}
function Failures() {
  const failures = usePolling<{ failures: FailureRow[] }>("/api/history/failures", 5000);
  const events = usePolling<{ events: TaskEvent[] }>("/api/history/task-events?limit=200", 5000);
  return (
    <div className="grid gap-4 2xl:grid-cols-2">
      <Panel title="Agent failures" bodyClassName="overflow-x-auto">
        {!failures.data ? <p className="p-4 text-sm text-ink-3">Loading...</p> : failures.data.failures.length === 0 ? (
          <Empty title="No failures recorded">Fail an agent from the simulator, fleet or network page.</Empty>
        ) : (
          <table className="w-full min-w-[620px] text-sm">
            <thead>
              <tr className="border-b border-line bg-header text-left text-xs text-ink font-semibold">
                <th className="px-4 py-2 font-semibold">Agent</th><th className="px-2 py-2 font-semibold">Was doing</th><th className="px-2 py-2 font-semibold">Detected by</th>
                <th className="px-2 py-2 font-semibold">Task taken over by</th><th className="px-4 py-2 font-semibold">Restored</th>
              </tr>
            </thead>
            <tbody>
              {failures.data.failures.map((f) => (
                <tr key={f.failure_id} className="border-b border-line/60 align-top hover:bg-selected/20 transition-colors last:border-0">
                  <td className="px-4 py-2 font-mono font-medium text-ink">{f.agent_id}<div className="text-2xs text-ink-3">{sentence(f.reason)} · t {f.failed_tick}</div></td>
                  <td className="px-2 py-2 text-ink-2">{f.task_id ? `${f.task_id} (${f.incident_id})` : sentence(f.status_before)}</td>
                  <td className="px-2 py-2 text-ink-2">
                    {f.detected_by ? <><span className="font-mono text-primary">{f.detected_by}</span><div className="text-2xs text-ink-3">{sentence(f.detection_method)} · after {(f.detected_tick ?? 0) - f.failed_tick} s</div></> : <span className="text-ink-3">not detected yet</span>}
                  </td>
                  <td className="px-2 py-2 text-ink-2">{f.reassigned_to ? <><span className="font-mono text-primary">{f.reassigned_to}</span><div className="text-2xs text-ink-3">after {(f.reassigned_tick ?? 0) - f.failed_tick} s</div></> : <span className="text-ink-3">{f.task_id ? "no replacement" : "-"}</span>}</td>
                  <td className="px-4 py-2 text-ink-2">{f.restored_tick !== null ? `t ${f.restored_tick}` : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
      <Panel title="Task events" bodyClassName="max-h-[560px] overflow-y-auto scroll-thin">
        {!events.data ? <p className="p-4 text-sm text-ink-3">Loading...</p> : events.data.events.length === 0 ? (
          <Empty title="No task events yet" />
        ) : (
          <ul className="divide-y divide-line">
            {events.data.events.map((e, idx) => (
              <li key={idx} className="px-4 py-2 text-sm hover:bg-selected/20 transition-colors">
                <div className="flex justify-between gap-2">
                  <span className={cx("font-medium", e.event === "REASSIGNED" && "text-respond font-semibold", (e.event === "INTERRUPTED" || e.event === "UNASSIGNED") && "text-respond font-semibold")}>
                    {sentence(e.event)} · {TASK_LABEL[e.task_type] ?? e.task_type}
                  </span>
                  <span className="text-2xs tabular-nums text-ink-3">{fmtTime(e.timestamp)}</span>
                </div>
                <div className="text-xs text-ink-2">
                  <span className="font-mono">{e.task_id}</span> · <span className="font-mono">{e.incident_id}</span>
                  {e.from_agent && e.to_agent ? ` · ${e.from_agent} → ${e.to_agent}` : e.to_agent ? ` · ${e.to_agent}` : e.from_agent ? ` · ${e.from_agent}` : ""}
                  {e.reason ? ` · ${e.reason}` : ""}
                </div>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  );
}

function Figure({ label, value, note }: { label: string; value: React.ReactNode; note?: string }) {
  return (
    <div className="min-w-[150px] flex-1 border-b border-r border-line bg-surface px-4 py-3 hover:bg-selected/20 transition-colors">
      <div className="text-2xs font-semibold uppercase tracking-wider text-ink-3">{label}</div>
      <div className="font-cond text-2xl font-bold tabular-nums text-ink leading-tight">{value}</div>
      {note && <div className="text-2xs text-ink-2 truncate">{note}</div>}
    </div>
  );
}

function TwoSeriesChart({ data, avgKey, maxKey, unit, digits = 1 }: { data: Analytics["environment_series"]; avgKey: keyof Analytics["environment_series"][number]; maxKey: keyof Analytics["environment_series"][number]; unit: string; digits?: number }) {
  return (
    <>
      <div className="h-44">
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 6, right: 8, bottom: 0, left: -12 }}>
            <CartesianGrid {...GRID} />
            <XAxis dataKey="tick" {...AXIS} type="number" domain={["dataMin", "dataMax"]} tickFormatter={(t) => `${t}s`} />
            <YAxis {...AXIS} domain={["auto", "auto"]} />
            <Tooltip content={<ChartTooltip format={(v) => `${Number(v).toFixed(digits)} ${unit}`} />} />
            <Line type="monotone" dataKey={avgKey} name="Fleet average" stroke={SERIES.blue} strokeWidth={2} dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey={maxKey} name="Highest reading" stroke={SERIES.orange} strokeWidth={2} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2"><LegendRow items={[{ color: SERIES.blue, label: "Fleet average" }, { color: SERIES.orange, label: "Highest reading" }]} /></div>
    </>
  );
}

function AnalyticsView() {
  const { data, error, reload, loading } = usePolling<Analytics>("/api/analytics", 10000);
  if (error) return <Panel><Empty title="Analytics unavailable">{error}</Empty></Panel>;
  if (!data) return <p className="p-4 text-sm text-ink-3">Loading...</p>;
  const typeData = (["FIRE", "POLLUTION", "EXTREME_HEAT"] as IncidentType[]).map((t) => ({ type: HAZARD_LABEL[t], key: t, count: data.incidents.by_type[t] ?? 0 }));
  const resolution = data.resolution_times.filter((r) => r.physical).slice(-14);
  const f = data.failures;

  return (
    <div className="space-y-4">
      <div className="flex justify-end"><Button size="sm" variant="ghost" onClick={reload} disabled={loading}>Refresh</Button></div>
      <div className="-mr-px flex flex-wrap overflow-hidden rounded-lg border-l border-t border-line bg-surface shadow-xs">
        <Figure label="Incidents recorded" value={data.incidents.total} note={Object.entries(data.incidents.by_status).map(([k, v]) => `${v} ${(INCIDENT_STATUS_LABEL[k] ?? k).toLowerCase()}`).join(", ") || "none yet"} />
        <Figure label="Average resolution" value={data.average_resolution_s !== null ? `${Math.round(data.average_resolution_s)} s` : "-"} note="creation to resolved" />
        <Figure label="Average detection" value={data.average_detection_s !== null ? `${data.average_detection_s} s` : "-"} note="creation to first local alert" />
        <Figure label="Failures" value={f.total} note={`${f.reassigned} tasks taken over · ${f.restored} restored`} />
        <Figure label="Failure detected after" value={f.average_detection_delay_s !== null ? `${f.average_detection_delay_s} s` : "-"} note={Object.entries(f.by_detection_method).map(([k, v]) => `${v} ${sentence(k).toLowerCase()}`).join(", ") || "-"} />
        <Figure label="Task taken over after" value={f.average_reassignment_delay_s !== null ? `${f.average_reassignment_delay_s} s` : "-"} note="failure to new owner" />
        <Figure label="Response tasks" value={data.tasks.total} note={`${data.tasks.by_status.COMPLETED ?? 0} completed · ${data.tasks.reassigned} reassigned · ${data.tasks.by_status.CANCELLED ?? 0} cancelled`} />
      </div>

      <div className="grid gap-4 2xl:grid-cols-2">
        <Panel title="Temperature this run (°C)" aside={<span>sampled every 5 s</span>}>
          {data.environment_series.length < 2 ? <p className="py-8 text-center text-sm text-ink-3">Telemetry samples appear after a few seconds.</p> : <TwoSeriesChart data={data.environment_series} avgKey="avg_temperature" maxKey="max_temperature" unit="°C" />}
        </Panel>
        <Panel title="Smoke this run (0-1)">
          {data.environment_series.length < 2 ? <p className="py-8 text-center text-sm text-ink-3">Telemetry samples appear after a few seconds.</p> : <TwoSeriesChart data={data.environment_series} avgKey="avg_smoke" maxKey="max_smoke" unit="" digits={2} />}
        </Panel>
        <Panel title="CO₂ this run (ppm)">
          {data.environment_series.length < 2 ? <p className="py-8 text-center text-sm text-ink-3">Telemetry samples appear after a few seconds.</p> : <TwoSeriesChart data={data.environment_series} avgKey="avg_co2" maxKey="max_co2" unit="ppm" digits={0} />}
        </Panel>
        <Panel title="Operational agents this run">
          {data.availability_series.length < 2 ? <p className="py-8 text-center text-sm text-ink-3">No samples yet.</p> : (
            <div className="h-44">
              <ResponsiveContainer>
                <LineChart data={data.availability_series} margin={{ top: 6, right: 8, bottom: 0, left: -18 }}>
                  <CartesianGrid {...GRID} />
                  <XAxis dataKey="tick" {...AXIS} type="number" domain={["dataMin", "dataMax"]} tickFormatter={(t) => `${t}s`} />
                  <YAxis {...AXIS} allowDecimals={false} domain={[0, "dataMax"]} />
                  <Tooltip content={<ChartTooltip />} />
                  <Line type="stepAfter" dataKey="operational" name="Operational" stroke={SERIES.blue} strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </Panel>
        <Panel title="Incidents by hazard (all runs)">
          <div className="h-44">
            <ResponsiveContainer>
              <BarChart data={typeData} margin={{ top: 6, right: 8, bottom: 0, left: -18 }} barCategoryGap="35%">
                <CartesianGrid {...GRID} />
                <XAxis dataKey="type" {...AXIS} />
                <YAxis {...AXIS} allowDecimals={false} />
                <Tooltip cursor={{ fill: "#397FB815" }} content={<ChartTooltip labelPrefix="" labelSuffix="" />} />
                <Bar dataKey="count" name="Incidents" radius={[4, 4, 0, 0]} isAnimationActive={false}>
                  {typeData.map((d) => <Cell key={d.key} fill={HAZARD_COLOR[d.key]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel title="Time to resolve (seconds)" aside={<span>resolved hazards, latest {resolution.length}</span>}>
          {resolution.length === 0 ? <p className="py-8 text-center text-sm text-ink-3">No resolved incidents yet.</p> : (
            <div className="h-44">
              <ResponsiveContainer>
                <BarChart data={resolution} margin={{ top: 6, right: 8, bottom: 0, left: -12 }} barCategoryGap="30%">
                  <CartesianGrid {...GRID} />
                  <XAxis dataKey="incident_id" {...AXIS} tick={{ fill: "#71879B", fontSize: 10 }} />
                  <YAxis {...AXIS} />
                  <Tooltip cursor={{ fill: "#397FB815" }} content={<ChartTooltip labelPrefix="" labelSuffix="" format={(v) => `${v} s`} />} />
                  <Bar dataKey="total_s" name="Created to resolved" radius={[4, 4, 0, 0]} isAnimationActive={false}>
                    {resolution.map((r) => <Cell key={r.incident_id} fill={HAZARD_COLOR[r.type]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Panel>
      </div>

      <div className="grid gap-4 2xl:grid-cols-2">
        <Panel title="Response durations" bodyClassName="overflow-x-auto max-h-80 overflow-y-auto scroll-thin">
          {data.response_durations.length === 0 ? <Empty title="No completed response tasks yet" /> : (
            <table className="w-full text-sm">
              <thead><tr className="border-b border-line bg-header text-left text-xs text-ink font-semibold"><th className="px-4 py-2 font-semibold">Task</th><th className="px-2 py-2 font-semibold">Agent</th><th className="px-2 py-2 text-right font-semibold">Travel</th><th className="px-4 py-2 text-right font-semibold">Assigned to done</th></tr></thead>
              <tbody>
                {data.response_durations.map((r) => (
                  <tr key={r.task_id} className="border-b border-line/60 hover:bg-selected/20 transition-colors last:border-0">
                    <td className="px-4 py-1.5 font-medium text-ink">{TASK_LABEL[r.task_type] ?? r.task_type}{r.reassigned && <span className="ml-1.5 text-2xs text-respond font-semibold">reassigned</span>}</td>
                    <td className="px-2 py-1.5 font-mono text-primary">{r.owner_id}</td>
                    <td className="px-2 py-1.5 text-right tabular-nums text-ink-2">{r.travel_s !== null ? `${r.travel_s} s` : "-"}</td>
                    <td className="px-4 py-1.5 text-right tabular-nums font-semibold text-ink">{r.total_s} s</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>
        <Panel title="Detection pipeline per incident" bodyClassName="overflow-x-auto max-h-80 overflow-y-auto scroll-thin">
          {data.resolution_times.length === 0 ? <Empty title="No resolved incidents yet" /> : (
            <table className="w-full text-sm">
              <thead><tr className="border-b border-line bg-header text-left text-xs text-ink font-semibold"><th className="px-4 py-2 font-semibold">Incident</th><th className="px-2 py-2 text-right font-semibold">To detect</th><th className="px-2 py-2 text-right font-semibold">To confirm</th><th className="px-2 py-2 text-right font-semibold">To act</th><th className="px-4 py-2 text-right font-semibold">Total</th></tr></thead>
              <tbody>
                {data.resolution_times.map((r) => (
                  <tr key={r.incident_id} className="border-b border-line/60 hover:bg-selected/20 transition-colors last:border-0">
                    <td className="px-4 py-1.5 font-mono font-medium text-ink"><span className="mr-2 inline-block h-2 w-2 rounded-full" style={{ background: HAZARD_COLOR[r.type] }} />{r.incident_id}{!r.physical && <span className="ml-1 text-2xs text-ink-3">sensor fault</span>}</td>
                    <td className="px-2 py-1.5 text-right tabular-nums text-ink-2">{r.detection_s ?? "-"} s</td>
                    <td className="px-2 py-1.5 text-right tabular-nums text-ink-2">{r.confirmation_s ?? "-"} s</td>
                    <td className="px-2 py-1.5 text-right tabular-nums text-ink-2">{r.response_start_s ?? "-"} s</td>
                    <td className="px-4 py-1.5 text-right tabular-nums font-semibold text-ink">{r.total_s} s</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>
      </div>
      <p className="text-xs text-ink-3">
        All figures are computed from records stored in the database (incidents, tasks, failures, telemetry samples). Nothing on this page is estimated or invented.
        Network reorganizations: {data.network.reorganizations}{data.network.average_compute_ms !== null ? `, average recomputation ${data.network.average_compute_ms} ms` : ""}.
      </p>
    </div>
  );
}

function IncidentReports() {
  const { data, error, reload, loading } = usePolling<{ incidents: StoredIncident[] }>(
    "/api/history/incidents?limit=100",
    5000
  );
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [showComms, setShowComms] = useState(false);

  const incidents = data?.incidents ?? [];
  const filtered = incidents.filter((inc) => {
    if (typeFilter !== "ALL" && inc.type !== typeFilter) return false;
    return true;
  });

  const selectedIncident =
    filtered.find((i) => i.id === selectedId) ??
    (incidents.find((i) => i.id === selectedId) || filtered[0] || null);

  const incidentMessages = usePolling<{ messages: StoredMessage[] }>(
    selectedIncident ? `/api/history/messages?limit=100&incident_id=${selectedIncident.id}` : "/api/history/messages?limit=0",
    5000
  );

  return (
    <div className="space-y-4">
      {/* Top Filter and Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-2xs font-semibold uppercase tracking-wider text-ink-3 mr-1">
            Hazard:
          </span>
          {(["ALL", "FIRE", "POLLUTION", "EXTREME_HEAT"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={cx(
                "rounded px-2.5 py-1 text-xs font-medium transition-colors border",
                typeFilter === t
                  ? "bg-primary font-semibold text-white border-primary shadow-xs"
                  : "bg-surface text-ink-2 border-line hover:bg-selected/40 hover:text-ink"
              )}
            >
              {t === "ALL" ? "All Incidents" : HAZARD_LABEL[t]}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-ink-3">
            {filtered.length} incident{filtered.length === 1 ? "" : "s"} recorded
          </span>
          <Button size="sm" variant="ghost" onClick={reload} disabled={loading}>
            Refresh
          </Button>
        </div>
      </div>

      {error ? (
        <Panel><Empty title="Incidents history unavailable">{error}</Empty></Panel>
      ) : !data ? (
        <p className="p-4 text-sm text-ink-3">Loading incident history...</p>
      ) : filtered.length === 0 ? (
        <Panel><Empty title="No incidents recorded yet">Place a fire, pollution, or heat incident on the simulator map to see agent response flow.</Empty></Panel>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
          {/* Left Column: Incidents List */}
          <div className="lg:col-span-4 xl:col-span-4 space-y-2 max-h-[780px] overflow-y-auto scroll-thin pr-1">
            {filtered.map((inc) => {
              const active = selectedIncident?.id === inc.id;
              const isResolved = inc.status === "RESOLVED";
              const durS =
                inc.resolved_tick && inc.created_tick
                  ? inc.resolved_tick - inc.created_tick
                  : null;

              return (
                <button
                  key={inc.id}
                  onClick={() => setSelectedId(inc.id)}
                  className={cx(
                    "w-full text-left rounded-lg border p-3 transition-all",
                    active
                      ? "border-primary bg-selected shadow-sm border-l-4 border-l-primary"
                      : "border-line bg-surface hover:bg-selected/30"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 rounded-full"
                        style={{ backgroundColor: HAZARD_COLOR[inc.type] }}
                      />
                      <span className="font-mono text-xs font-semibold text-ink">
                        {inc.id}
                      </span>
                      <span
                        className="rounded px-1.5 py-0.5 text-2xs font-medium"
                        style={{
                          backgroundColor: `${HAZARD_COLOR[inc.type]}20`,
                          color: HAZARD_COLOR[inc.type],
                        }}
                      >
                        {HAZARD_LABEL[inc.type]}
                      </span>
                    </div>
                    <span
                      className={cx(
                        "rounded px-1.5 py-0.5 text-2xs font-semibold uppercase tracking-wider",
                        isResolved
                          ? "bg-ok/15 text-ok"
                          : "bg-heat/15 text-heat animate-pulse"
                      )}
                    >
                      {inc.status}
                    </span>
                  </div>

                  <div className="mt-2 grid grid-cols-2 gap-1 text-2xs text-ink-3">
                    <div>
                      <span>Peak: </span>
                      <span className="font-medium text-ink">
                        {Math.round(inc.peak_severity)} → {Math.round(inc.severity)}
                      </span>
                    </div>
                    <div className="text-right">
                      {durS ? <span>Resolved in {durS}s</span> : <span>Active response</span>}
                    </div>
                    <div>
                      <span>Coord: </span>
                      <span className="font-mono text-primary font-medium">
                        {inc.coordinator_id ?? "electing..."}
                      </span>
                    </div>
                    <div className="text-right tabular-nums">
                      {fmtTime(inc.created_at)}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Right Column: Detailed Incident Response Flow & Task Report */}
          <div className="lg:col-span-8 xl:col-span-8 space-y-4">
            {selectedIncident && (
              <>
                {/* Header Card */}
                <div className="rounded-xl border border-line bg-surface p-4 shadow-sm space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line pb-3">
                    <div className="flex items-center gap-2.5">
                      <div
                        className="flex h-9 w-9 items-center justify-center rounded-lg"
                        style={{ backgroundColor: `${HAZARD_COLOR[selectedIncident.type]}25` }}
                      >
                        {selectedIncident.type === "FIRE" ? (
                          <Flame size={20} style={{ color: HAZARD_COLOR.FIRE }} />
                        ) : selectedIncident.type === "POLLUTION" ? (
                          <CloudFog size={20} style={{ color: HAZARD_COLOR.POLLUTION }} />
                        ) : (
                          <Thermometer size={20} style={{ color: HAZARD_COLOR.EXTREME_HEAT }} />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h2 className="font-cond text-lg font-bold text-ink">
                            {selectedIncident.id} · {HAZARD_LABEL[selectedIncident.type]}
                          </h2>
                          <span
                            className={cx(
                              "rounded px-2 py-0.5 text-xs font-semibold uppercase",
                              selectedIncident.status === "RESOLVED"
                                ? "bg-ok/15 text-ok"
                                : "bg-heat/15 text-heat"
                            )}
                          >
                            {selectedIncident.status}
                          </span>
                        </div>
                        <p className="text-2xs text-ink-3">
                          Deployed at {fmtTime(selectedIncident.created_at)} · Radius: {selectedIncident.radius_m}m · Origin: {selectedIncident.origin}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant={showComms ? "primary" : "secondary"}
                        onClick={() => setShowComms((v) => !v)}
                        className="text-xs"
                      >
                        <MessageSquare size={13} className="mr-1" />
                        {showComms ? "Hide Radio Comms" : "Show Radio Comms"}
                      </Button>
                    </div>
                  </div>

                  {/* High-level metrics */}
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 text-xs">
                    <div className="rounded-lg bg-panel/60 border border-line/60 p-2.5">
                      <div className="text-2xs text-ink-3">Severity Reduction</div>
                      <div className="mt-0.5 font-cond text-base font-bold text-ink">
                        {Math.round(selectedIncident.peak_severity)} → {selectedIncident.severity.toFixed(1)}
                      </div>
                      <div className="text-2xs font-medium text-ok">
                        -{Math.max(0, Math.round(selectedIncident.peak_severity - selectedIncident.severity))} points neutralized
                      </div>
                    </div>

                    <div className="rounded-lg bg-panel/60 border border-line/60 p-2.5">
                      <div className="text-2xs text-ink-3">Elected Coordinator</div>
                      <div className="mt-0.5 font-mono text-base font-bold text-primary">
                        {selectedIncident.coordinator_id ?? "None"}
                      </div>
                      <div className="text-2xs text-ink-3">
                        {selectedIncident.supporters} votes / {selectedIncident.opposers} against
                      </div>
                    </div>

                    <div className="rounded-lg bg-panel/60 border border-line/60 p-2.5">
                      <div className="text-2xs text-ink-3">Response Tasks</div>
                      <div className="mt-0.5 font-cond text-base font-bold text-ink">
                        {selectedIncident.tasks.length} Assigned
                      </div>
                      <div className="text-2xs text-ink-3">
                        {selectedIncident.tasks.filter((t) => t.status === "COMPLETED").length} Completed
                      </div>
                    </div>

                    <div className="rounded-lg bg-panel/60 border border-line/60 p-2.5">
                      <div className="text-2xs text-ink-3">Total Time</div>
                      <div className="mt-0.5 font-cond text-base font-bold text-ink">
                        {selectedIncident.resolved_tick && selectedIncident.created_tick
                          ? `${selectedIncident.resolved_tick - selectedIncident.created_tick}s`
                          : "Ongoing"}
                      </div>
                      <div className="text-2xs text-ink-3">
                        Detect: {selectedIncident.detected_tick && selectedIncident.created_tick ? `+${selectedIncident.detected_tick - selectedIncident.created_tick}s` : "-"}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Step-by-Step Flow of Agents Responding and Doing Tasks */}
                <div className="rounded-xl border border-line bg-surface p-4 shadow-sm space-y-3">
                  <div className="flex items-center justify-between border-b border-line pb-2">
                    <h3 className="font-cond text-sm font-semibold tracking-wide text-ink uppercase flex items-center gap-1.5">
                      <Activity size={15} className="text-primary" />
                      Agent Response & Task Execution Flow
                    </h3>
                    <span className="text-2xs text-ink-3">Autonomous Consensus & Action</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-2 relative">
                    {/* Stage 1: Detection */}
                    <div className="rounded-lg border border-line bg-panel/40 p-2.5 flex flex-col justify-between hover:bg-selected/20 transition-colors">
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="text-2xs font-bold text-primary uppercase">1. Detect</span>
                          <Radio size={13} className="text-primary" />
                        </div>
                        <div className="mt-1 font-semibold text-xs text-ink">
                          Anomaly Flagged
                        </div>
                        <p className="mt-0.5 text-2xs text-ink-3 leading-relaxed">
                          {selectedIncident.detectors?.length > 0
                            ? `Spotted by ${selectedIncident.detectors.slice(0, 3).join(", ")}`
                            : "Local drone sensors"}
                        </p>
                      </div>
                      <div className="mt-2 text-2xs font-mono text-ink-3 border-t border-line/60 pt-1">
                        t={selectedIncident.detected_tick ?? selectedIncident.created_tick}s
                      </div>
                    </div>

                    {/* Stage 2: Consensus */}
                    <div className="rounded-lg border border-line bg-panel/40 p-2.5 flex flex-col justify-between hover:bg-selected/20 transition-colors">
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="text-2xs font-bold text-indigo-600 uppercase">2. Consensus</span>
                          <Users size={13} className="text-indigo-600" />
                        </div>
                        <div className="mt-1 font-semibold text-xs text-ink">
                          Quorum Vote
                        </div>
                        <p className="mt-0.5 text-2xs text-ink-3 leading-relaxed">
                          {selectedIncident.supporters} in favor · {selectedIncident.coordinator_id} elected coordinator
                        </p>
                      </div>
                      <div className="mt-2 text-2xs font-mono text-ink-3 border-t border-line/60 pt-1">
                        {Math.round((selectedIncident.consensus_confidence ?? 1) * 100)}% confidence
                      </div>
                    </div>

                    {/* Stage 3: Task Dispatch */}
                    <div className="rounded-lg border border-line bg-panel/40 p-2.5 flex flex-col justify-between hover:bg-selected/20 transition-colors">
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="text-2xs font-bold text-heat uppercase">3. Dispatch</span>
                          <ShieldAlert size={13} className="text-heat" />
                        </div>
                        <div className="mt-1 font-semibold text-xs text-ink">
                          Tasks Formulated
                        </div>
                        <p className="mt-0.5 text-2xs text-ink-3 leading-relaxed">
                          {selectedIncident.tasks.length} specialized task{selectedIncident.tasks.length === 1 ? "" : "s"} allocated
                        </p>
                      </div>
                      <div className="mt-2 text-2xs font-mono text-ink-3 border-t border-line/60 pt-1">
                        By {selectedIncident.coordinator_id}
                      </div>
                    </div>

                    {/* Stage 4: Responding */}
                    <div className="rounded-lg border border-line bg-panel/40 p-2.5 flex flex-col justify-between hover:bg-selected/20 transition-colors">
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="text-2xs font-bold text-purple-600 uppercase">4. Action</span>
                          <Activity size={13} className="text-purple-600" />
                        </div>
                        <div className="mt-1 font-semibold text-xs text-ink">
                          Active Mitigation
                        </div>
                        <p className="mt-0.5 text-2xs text-ink-3 leading-relaxed">
                          {Array.from(new Set(selectedIncident.tasks.map((t) => t.owner_id))).join(", ") || "Responders"} on site
                        </p>
                      </div>
                      <div className="mt-2 text-2xs font-mono text-ink-3 border-t border-line/60 pt-1">
                        {selectedIncident.tasks.filter((t) => t.status === "COMPLETED").length}/{selectedIncident.tasks.length} tasks done
                      </div>
                    </div>

                    {/* Stage 5: Resolved */}
                    <div className="rounded-lg border border-line bg-panel/40 p-2.5 flex flex-col justify-between hover:bg-selected/20 transition-colors">
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="text-2xs font-bold text-ok uppercase">5. Resolved</span>
                          <CheckCircle2 size={13} className="text-ok" />
                        </div>
                        <div className="mt-1 font-semibold text-xs text-ink">
                          Threat Neutralized
                        </div>
                        <p className="mt-0.5 text-2xs text-ink-3 leading-relaxed">
                          Severity &lt; 5.0 safe baseline
                        </p>
                      </div>
                      <div className="mt-2 text-2xs font-mono text-ink-3 border-t border-line/60 pt-1">
                        {selectedIncident.status === "RESOLVED" ? "Complete" : "In Progress"}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Assigned Agents and Tasks Detail */}
                <div className="rounded-xl border border-line bg-surface p-4 shadow-sm space-y-3">
                  <h3 className="font-cond text-sm font-semibold tracking-wide text-ink uppercase flex items-center gap-1.5">
                    <Users size={15} className="text-ok" />
                    Assigned Agents & Response Tasks
                  </h3>

                  {selectedIncident.tasks.length === 0 ? (
                    <p className="text-xs text-ink-3">No tasks assigned for this incident yet.</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-line bg-header text-ink font-semibold">
                            <th className="py-2 px-3 font-semibold">Task ID</th>
                            <th className="py-2 px-3 font-semibold">Task Type</th>
                            <th className="py-2 px-3 font-semibold">Assigned Agent</th>
                            <th className="py-2 px-3 font-semibold">Status</th>
                            <th className="py-2 px-3 font-semibold text-right">Work Done</th>
                            <th className="py-2 px-3 font-semibold text-right">Progress</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-line/60">
                          {selectedIncident.tasks.map((task) => (
                            <tr key={task.id} className="hover:bg-selected/20 transition-colors">
                              <td className="py-2 px-3 font-mono font-medium text-ink">
                                {task.id}
                              </td>
                              <td className="py-2 px-3">
                                <span className="font-medium text-ink">
                                  {TASK_LABEL[task.task_type] ?? task.task_type}
                                </span>
                                {task.optional && (
                                  <span className="ml-1 text-2xs text-ink-3">(support)</span>
                                )}
                              </td>
                              <td className="py-2 px-3">
                                <div className="flex items-center gap-1.5">
                                  <span className="font-mono font-semibold text-primary">
                                    {task.owner_id}
                                  </span>
                                  {task.previous_owner_id && (
                                    <span className="text-2xs text-heat font-medium">
                                      (reassigned from {task.previous_owner_id})
                                    </span>
                                  )}
                                </div>
                              </td>
                              <td className="py-2 px-3">
                                <span
                                  className={cx(
                                    "rounded px-1.5 py-0.5 text-2xs font-semibold uppercase",
                                    task.status === "COMPLETED"
                                      ? "bg-ok/15 text-ok"
                                      : task.status === "IN_PROGRESS"
                                      ? "bg-primary/15 text-primary"
                                      : "bg-ink-3/15 text-ink-2"
                                  )}
                                >
                                  {task.status}
                                </span>
                              </td>
                              <td className="py-2 px-3 text-right tabular-nums text-ink-2">
                                {task.work_done > 0 ? `${task.work_done} pts` : "-"}
                              </td>
                              <td className="py-2 px-3 text-right">
                                <div className="flex items-center justify-end gap-2">
                                  <span className="tabular-nums font-mono text-2xs text-ink font-semibold">
                                    {Math.round((task.progress ?? 0) * 100)}%
                                  </span>
                                  <div className="h-1.5 w-16 overflow-hidden rounded-full bg-line/40">
                                    <div
                                      className="h-full bg-primary"
                                      style={{ width: `${Math.round((task.progress ?? 0) * 100)}%` }}
                                    />
                                  </div>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                {/* Step-by-Step Chronological Event Log */}
                <div className="rounded-xl border border-line bg-surface p-4 shadow-sm space-y-3">
                  <h3 className="font-cond text-sm font-semibold tracking-wide text-ink uppercase flex items-center gap-1.5">
                    <Clock size={15} className="text-heat" />
                    Incident Chronological Response Timeline
                  </h3>

                  {selectedIncident.timeline?.length === 0 ? (
                    <p className="text-xs text-ink-3">No timeline events recorded.</p>
                  ) : (
                    <ol className="divide-y divide-line/60">
                      {selectedIncident.timeline.map((evt, idx) => (
                        <li key={idx} className="flex items-start gap-3 py-2 text-xs hover:bg-selected/20 transition-colors">
                          <span className="font-mono text-2xs text-ink-3 shrink-0 pt-0.5 tabular-nums">
                            t={evt.tick}s
                          </span>
                          <span
                            className={cx(
                              "rounded px-1.5 py-0.5 text-2xs font-semibold shrink-0 uppercase tracking-wide",
                              evt.stage === "RESOLVED"
                                ? "bg-ok/15 text-ok"
                                : evt.stage === "RESPONDING" || evt.stage === "RESPONSE"
                                ? "bg-primary/15 text-primary"
                                : evt.stage === "CONFIRMED" || evt.stage === "TASKS_ASSIGNED"
                                ? "bg-indigo-500/15 text-indigo-600"
                                : evt.stage === "DETECTED"
                                ? "bg-heat/15 text-heat"
                                : "bg-ink-3/15 text-ink-2"
                            )}
                          >
                            {evt.stage}
                          </span>
                          <span className="text-ink-2 leading-relaxed">{evt.text}</span>
                        </li>
                      ))}
                    </ol>
                  )}
                </div>

                {/* Optional Radio Comms Drawer */}
                {showComms && (
                  <div className="rounded-xl border border-line bg-surface p-4 shadow-sm space-y-3">
                    <h3 className="font-cond text-sm font-semibold tracking-wide text-ink uppercase flex items-center gap-1.5">
                      <Radio size={15} className="text-purple-600" />
                      Agent Radio Communications for {selectedIncident.id}
                    </h3>

                    {incidentMessages.error ? (
                      <p className="text-xs text-respond">{incidentMessages.error}</p>
                    ) : !incidentMessages.data || incidentMessages.data.messages.length === 0 ? (
                      <p className="text-xs text-ink-3">No radio messages recorded for this incident.</p>
                    ) : (
                      <div className="max-h-60 overflow-y-auto scroll-thin">
                        <table className="w-full text-left text-xs">
                          <thead>
                            <tr className="border-b border-line bg-header text-ink font-semibold">
                              <th className="py-1.5 px-2 font-semibold">Time</th>
                              <th className="py-1.5 px-2 font-semibold">Type</th>
                              <th className="py-1.5 px-2 font-semibold">From</th>
                              <th className="py-1.5 px-2 font-semibold">To</th>
                              <th className="py-1.5 px-2 font-semibold text-right">Route</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-line/60">
                            {incidentMessages.data.messages.map((m) => (
                              <tr key={m.message_id} className="hover:bg-selected/20 transition-colors">
                                <td className="py-1 px-2 font-mono text-2xs text-ink-3">
                                  {fmtTime(m.timestamp)}
                                </td>
                                <td className="py-1 px-2 text-ink font-medium">{sentence(m.type)}</td>
                                <td className="py-1 px-2 font-mono text-primary font-medium">{m.sender}</td>
                                <td className="py-1 px-2 font-mono text-primary font-medium">{m.receiver}</td>
                                <td className="py-1 px-2 text-right text-2xs text-ink-3">
                                  {m.hops === 1 ? "direct" : `${m.hops} hops`}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function HistoryPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("Incident reports");
  return (
    <div className="pb-8">
      <PageHeader
        title="History and analytics"
        subtitle="Stored incident reports, multi-agent response flows, task assignments, and telemetry."
      />
      <div className="mb-4 flex gap-1 overflow-x-auto border-b border-line px-5 lg:px-6" role="tablist">
        {TABS.map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            onClick={() => setTab(t)}
            className={cx(
              "whitespace-nowrap px-3 py-2 text-xs font-semibold rounded-t-md transition-all",
              tab === t
                ? "bg-primary text-white shadow-sm"
                : "bg-surface/80 text-ink-2 border border-b-0 border-line hover:bg-selected/40 hover:text-ink"
            )}
          >
            {t}
          </button>
        ))}
      </div>
      <div className="px-5 lg:px-6">
        {tab === "Incident reports" && <IncidentReports />}
        {tab === "Timeline" && <Timeline />}
        {tab === "Messages" && <Messages />}
        {tab === "Failures and reassignment" && <Failures />}
        {tab === "Analytics" && <AnalyticsView />}
      </div>
    </div>
  );
}

