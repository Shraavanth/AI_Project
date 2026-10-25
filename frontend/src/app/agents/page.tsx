"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { Move, Power, RotateCcw, Search } from "lucide-react";
import { AgentGlyph } from "@/components/AgentGlyph";
import { AiBadge, ReadingsGrid, SENSOR_META } from "@/components/AgentInspector";
import { useSim } from "@/components/SimulationProvider";
import { Button, Empty, KeyValue, Meter, PageHeader, Panel, StatusPill, cx } from "@/components/ui";
import { HAZARD_LABEL, STATUS_COLOR, TASK_LABEL, TYPE_SHORT, fmtDistance, sentence } from "@/lib/format";
import type { AgentDetail, AgentType, Message } from "@/lib/types";
import { usePolling } from "@/lib/usePolling";
import { api } from "@/lib/api";

const TYPE_FILTERS: (AgentType | "ALL")[] = ["ALL", "MONITOR_DRONE", "FIRE_DRONE", "SPRINKLER", "POLLUTION_UNIT", "COOLING_UNIT"];

function MessageList({ messages, self }: { messages: Message[]; self: string }) {
  if (!messages.length) return <p className="py-4 text-center text-sm text-ink-3">No messages yet.</p>;
  return (
    <ul className="divide-y divide-line">
      {messages.map((m) => (
        <li key={m.message_id + m.receiver} className="py-2 text-xs">
          <div className="flex items-baseline justify-between gap-2">
            <span className="font-medium text-ink">{sentence(m.type)}</span>
            <span className="tabular-nums text-ink-3">t = {m.tick}</span>
          </div>
          <div className="text-ink-2">
            {m.sender === self ? `to ${m.receiver}` : `from ${m.sender}`}
            {m.incident_id ? ` · ${m.incident_id}` : ""}
            {m.hops && m.hops > 1 ? ` · ${m.hops} hops` : ""}
            {!m.delivered && <span className="text-[#f0a597]"> · not delivered (no route)</span>}
          </div>
        </li>
      ))}
    </ul>
  );
}

function SensorOverrideForm({ agent }: { agent: AgentDetail }) {
  const { act, notify } = useSim();
  const [values, setValues] = useState<Record<string, string>>({});
  const [duration, setDuration] = useState(20);
  useEffect(() => setValues({}), [agent.id]);

  const firePreset = { temperature: "47", humidity: "15", smoke: "0.85", co2: "900", air_quality: "95", soil_moisture: "20" };

  async function apply() {
    const body: Record<string, number> = { duration_ticks: duration };
    for (const m of SENSOR_META) {
      const raw = values[m.key];
      if (raw !== undefined && raw !== "") body[m.key] = Number(raw);
    }
    if (Object.keys(body).length === 1) return;
    await act(`/api/agents/${agent.id}/sensors`, body, `Sensor readings of ${agent.id} overridden for ${duration} s.`);
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-ink-3">
        Force this agent&apos;s readings to simulate a faulty or tampered sensor. Neighbours still read their real environment, so a single fake fire should be rejected by consensus.
      </p>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {SENSOR_META.map((m) => (
          <label key={m.key} className="text-2xs text-ink-2 font-medium">
            {m.label} {m.unit && `(${m.unit})`}
            <input
              type="number"
              step="any"
              value={values[m.key] ?? ""}
              placeholder={agent.readings[m.key].toFixed(m.digits)}
              onChange={(e) => setValues((v) => ({ ...v, [m.key]: e.target.value }))}
              className="mt-0.5 h-8 w-full rounded border border-line bg-input px-2 text-sm text-ink placeholder:text-ink-3 focus:border-primary focus:outline-none font-mono"
            />
          </label>
        ))}
      </div>
      <div className="flex flex-wrap items-end gap-2">
        <label className="text-2xs text-ink-2 font-medium">
          Duration (s)
          <input type="number" min={1} max={300} value={duration} onChange={(e) => setDuration(Number(e.target.value))} className="mt-0.5 h-8 w-20 rounded border border-line bg-input px-2 text-sm text-ink font-mono" />
        </label>
        <Button size="sm" variant="ghost" onClick={() => setValues(firePreset)}>Fill fire-like values</Button>
        <Button size="sm" onClick={apply} disabled={agent.status === "FAILED"}>Apply override</Button>
        {agent.sensor_override && (
          <Button size="sm" variant="ghost" onClick={async () => {
            try { await api.del(`/api/agents/${agent.id}/sensors`); notify("ok", `${agent.id} is reading its real environment again.`); }
            catch (e) { notify("error", e instanceof Error ? e.message : "Could not clear override"); }
          }}>Clear override</Button>
        )}
      </div>
    </div>
  );
}


function MoveForm({ agent }: { agent: AgentDetail }) {
  const { act, snapshot } = useSim();
  const [target, setTarget] = useState("home");
  if (!snapshot) return null;
  const options: { value: string; label: string; lat: number; lng: number }[] = [
    { value: "home", label: "Home base", lat: agent.home[0], lng: agent.home[1] },
    { value: "centre", label: "Area centre", lat: snapshot.site.lat, lng: snapshot.site.lng },
    ...snapshot.incidents
      .filter((i) => !["RESOLVED", "REJECTED"].includes(i.status))
      .map((i) => ({ value: i.id, label: `${i.id} (${HAZARD_LABEL[i.type]})`, lat: i.lat, lng: i.lng })),
  ];
  const chosen = options.find((o) => o.value === target) ?? options[0];
  const disabled = !agent.mobile || agent.status === "FAILED" || agent.status === "RECOVERING" || !!agent.task_id;
  return (
    <div className="flex flex-wrap items-end gap-2">
      <label className="text-2xs text-ink-2 font-medium">
        Send to
        <select value={target} onChange={(e) => setTarget(e.target.value)} className="mt-0.5 block h-8 rounded border border-line bg-input px-2 text-sm text-ink focus:border-primary focus:outline-none">
          {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </label>
      <Button size="sm" disabled={disabled} onClick={() => act(`/api/agents/${agent.id}/move`, { latitude: chosen.lat, longitude: chosen.lng }, `${agent.id} is moving to ${chosen.label.toLowerCase()}.`)}>
        <Move size={14} /> Move
      </Button>
      {!agent.mobile && <span className="text-xs text-ink-3">Fixed unit - cannot move.</span>}
      {agent.mobile && agent.task_id && <span className="text-xs text-ink-3">Busy with a task.</span>}
      <span className="w-full text-2xs text-ink-3">Tip: on the Area Simulator you can click any point on the map instead.</span>
    </div>
  );
}

function AgentDetailPanel({ id }: { id: string }) {
  const { act, snapshot } = useSim();
  const { data: agent, error } = usePolling<AgentDetail>(`/api/agents/${id}`, 1500);
  const [tab, setTab] = useState<"overview" | "messages" | "tasks" | "controls">("overview");
  if (error) return <Empty title="Agent not available">{error}</Empty>;
  if (!agent) return <p className="p-6 text-sm text-ink-3">Loading {id}...</p>;
  const failed = agent.status === "FAILED";
  const messages = [...agent.inbox, ...agent.sent].sort((a, b) => b.tick - a.tick).slice(0, 40);

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-line bg-header px-5 py-4 rounded-t-lg">
        <div className="flex items-center gap-3">
          <AgentGlyph type={agent.type} color={STATUS_COLOR[agent.status]} failed={failed} size={22} />
          <div>
            <h2 className="font-cond text-xl font-bold leading-tight text-ink">{agent.id}</h2>
            <p className="text-xs text-ink-2">{agent.type_label} · {agent.type_description}</p>
          </div>
        </div>
        {failed ? (
          <Button onClick={() => act(`/api/agents/${agent.id}/restore`, undefined, `${agent.id} restored - rebooting.`)}><RotateCcw size={15} /> Restore</Button>
        ) : (
          <Button variant="danger" disabled={agent.status === "RECOVERING"} onClick={() => act(`/api/agents/${agent.id}/fail`, undefined, `${agent.id} failed.`)}><Power size={15} /> Fail agent</Button>
        )}
      </div>
      <div className="flex gap-1 border-b border-line bg-panel/50 px-3 pt-1" role="tablist">
        {(["overview", "tasks", "messages", "controls"] as const).map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)} className={cx("px-3 py-2 text-sm font-semibold transition-colors", tab === t ? "border-b-2 border-primary text-primary bg-surface rounded-t" : "text-ink-2 hover:text-ink hover:bg-selected/30 rounded-t")}>
            {t === "overview" ? "Overview" : t === "tasks" ? "Tasks" : t === "messages" ? `Messages (${agent.messages_received + agent.messages_sent})` : "Controls"}
          </button>
        ))}
      </div>
      <div className="space-y-5 p-5">
        {tab === "overview" && (
          <>
            <dl className="grid gap-x-8 sm:grid-cols-2">
              <KeyValue label="Status"><StatusPill status={agent.status} /></KeyValue>
              <KeyValue label="Battery"><Meter value={agent.battery} label="Battery" /></KeyValue>
              <KeyValue label="Health"><Meter value={agent.health} label="Health" /></KeyValue>
              <KeyValue label="Local AI"><AiBadge ai={agent.ai} /></KeyValue>
              <KeyValue label="Position">{agent.lat.toFixed(5)}, {agent.lng.toFixed(5)}</KeyValue>
              <KeyValue label="Speed">{agent.mobile ? `${agent.speed_mps} m/s (scaled)` : "Fixed"}</KeyValue>
              <KeyValue label="Heading to">{agent.destination_label ?? "-"}</KeyValue>
              <KeyValue label="Travelled">{fmtDistance(agent.distance_travelled_m)}</KeyValue>
              <KeyValue label="Capabilities">{agent.capabilities.filter((c) => c !== "SENSE").map(sentence).join(", ") || "Sensing"}</KeyValue>
              <KeyValue label="Last telemetry">{agent.last_telemetry_tick !== null && snapshot ? `${snapshot.tick - agent.last_telemetry_tick} s ago` : "-"}</KeyValue>
            </dl>
            <div>
              <h3 className="mb-2 text-sm font-medium">Sensor readings</h3>
              <ReadingsGrid agent={agent} />
              <p className="mt-1.5 text-2xs text-ink-3">Normal background here: {agent.baseline.temperature.toFixed(1)} °C, {agent.baseline.humidity.toFixed(0)} % humidity, smoke {agent.baseline.smoke.toFixed(2)}.</p>
            </div>
            <div>
              <h3 className="mb-2 text-sm font-medium">Radio neighbours ({agent.neighbors.length})</h3>
              {agent.neighbors.length ? (
                <div className="flex flex-wrap gap-1.5">
                  {agent.neighbors.map((n) => (
                    <span key={n} className="rounded border border-line px-2 py-0.5 text-xs text-ink-2">{n} · {fmtDistance(agent.neighbor_distances[n])}</span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-ink-3">{failed ? "Radio off - no links." : "No agent within radio range."}</p>
              )}
            </div>
          </>
        )}

        {tab === "tasks" && (
          <>
            {agent.task ? (
              <div className="rounded-md border border-line p-4">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="font-medium">{TASK_LABEL[agent.task.task_type]} · {agent.task.incident_id}</h3>
                  <span className="text-xs text-ink-2">{sentence(agent.task.status)} · {agent.task.id}</span>
                </div>
                <div className="mt-2"><Meter value={agent.task.progress * 100} color="#A98BE0" label="Progress" /></div>
                {agent.task.last_decision.length > 0 && (
                  <div className="mt-3 overflow-x-auto">
                    <p className="mb-1 text-xs text-ink-3">Why this agent was chosen (score = distance km + (100 - battery)/100, lowest wins)</p>
                    <table className="w-full text-xs">
                      <tbody>
                        {agent.task.last_decision.map((r) => (
                          <tr key={r.agent_id} className={cx("border-t border-line", r.agent_id === agent.id && "text-ink")}>
                            <td className="py-1 pr-2">{r.agent_id}</td>
                            <td className="py-1 pr-2 text-right tabular-nums">{fmtDistance(r.distance_m)}</td>
                            <td className="py-1 pr-2 text-right tabular-nums">{Math.round(r.battery)}%</td>
                            <td className="py-1 pr-2 text-right tabular-nums">{r.score ?? "-"}</td>
                            <td className="py-1 text-ink-3">{r.reason}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-ink-3">No current task.</p>
            )}
            <div>
              <h3 className="mb-2 text-sm font-medium">Task history</h3>
              {agent.task_history.length ? (
                <table className="w-full text-sm">
                  <thead><tr className="text-left text-xs text-ink-3"><th className="pb-1 font-normal">Task</th><th className="pb-1 font-normal">Incident</th><th className="pb-1 font-normal">From</th><th className="pb-1 text-right font-normal">Outcome</th></tr></thead>
                  <tbody>
                    {agent.task_history.map((h) => (
                      <tr key={h.task_id + h.assigned_tick} className="border-t border-line">
                        <td className="py-1.5">{TASK_LABEL[h.task_type] ?? h.task_type}{h.reassigned_from && <div className="text-2xs text-ink-3">took over from {h.reassigned_from}</div>}</td>
                        <td className="py-1.5 text-ink-2">{h.incident_id}</td>
                        <td className="py-1.5 tabular-nums text-ink-2">t = {h.assigned_tick}</td>
                        <td className="py-1.5 text-right text-ink-2">{h.outcome ? sentence(h.outcome) : "In progress"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-sm text-ink-3">This agent has not been assigned any task yet.</p>
              )}
            </div>
          </>
        )}

        {tab === "messages" && <MessageList messages={messages} self={agent.id} />}

        {tab === "controls" && (
          <>
            <section>
              <h3 className="mb-2 text-sm font-medium">Move</h3>
              <MoveForm agent={agent} />
            </section>
            <section>
              <h3 className="mb-2 text-sm font-medium">Override sensor readings</h3>
              <SensorOverrideForm agent={agent} />
            </section>
          </>
        )}
      </div>
    </div>
  );
}

function FleetPage() {
  const { snapshot } = useSim();
  const params = useSearchParams();
  const router = useRouter();
  const selected = params.get("id");
  const [typeFilter, setTypeFilter] = useState<AgentType | "ALL">("ALL");
  const [query, setQuery] = useState("");

  const agents = useMemo(() => {
    if (!snapshot) return [];
    return snapshot.agents.filter(
      (a) => (typeFilter === "ALL" || a.type === typeFilter) && (!query || a.id.toLowerCase().includes(query.toLowerCase()) || a.status.toLowerCase().includes(query.toLowerCase())),
    );
  }, [snapshot, typeFilter, query]);

  if (!snapshot) return <div className="p-6 text-sm text-ink-3">Connecting to the simulation...</div>;
  const select = (id: string) => router.replace(`/agents?id=${id}`, { scroll: false });

  return (
    <div className="pb-8">
      <PageHeader title="Agent fleet" subtitle={`${snapshot.stats.operational_agents} of ${snapshot.stats.total_agents} agents operational. Select an agent to inspect its sensors, messages and tasks, or to fail, restore and move it.`} />
      <div className="grid gap-4 px-5 lg:px-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(360px,1fr)]">
        <Panel
          title="Agents"
          aside={
            <label className="relative">
              <Search size={13} className="absolute left-2 top-1/2 -translate-y-1/2 text-ink-3" />
              <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Filter by id or status" className="h-7 w-44 rounded border border-line bg-input pl-7 pr-2 text-xs text-ink placeholder:text-ink-3 focus:outline-none focus:border-primary" />
            </label>
          }
          bodyClassName=""
        >
          <div className="flex flex-wrap gap-1.5 border-b border-line bg-panel/40 px-4 py-2.5">
            {TYPE_FILTERS.map((t) => (
              <button key={t} onClick={() => setTypeFilter(t)} aria-pressed={typeFilter === t} className={cx("flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold transition-all shadow-2xs", typeFilter === t ? "bg-primary text-white" : "border border-line bg-input text-ink hover:bg-selected/40")}>
                {t !== "ALL" && <AgentGlyph type={t} color={typeFilter === t ? "#ffffff" : "#397FB8"} size={10} />}
                {t === "ALL" ? "All types" : TYPE_SHORT[t]}
              </button>
            ))}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-sm">
              <thead>
                <tr className="border-b border-line bg-header text-left text-xs text-ink font-semibold">
                  <th className="px-4 py-2">Agent</th>
                  <th className="px-2 py-2">Status</th>
                  <th className="px-2 py-2">Battery</th>
                  <th className="px-2 py-2">Task</th>
                  <th className="px-2 py-2">Local AI</th>
                  <th className="px-4 py-2 text-right">Links</th>
                </tr>
              </thead>
              <tbody>
                {agents.map((a) => (
                  <tr
                    key={a.id}
                    onClick={() => select(a.id)}
                    onKeyDown={(e) => e.key === "Enter" && select(a.id)}
                    tabIndex={0}
                    aria-selected={selected === a.id}
                    className={cx("cursor-pointer border-b border-line/60 last:border-0 hover:bg-selected/30 transition-colors", selected === a.id && "bg-selected border-l-4 border-l-primary font-medium", a.status === "FAILED" && "text-ink-3")}
                  >
                    <td className="px-4 py-2">
                      <div className="flex items-center gap-2.5">
                        <AgentGlyph type={a.type} color={STATUS_COLOR[a.status]} failed={a.status === "FAILED"} size={12} />
                        <div>
                          <div className="font-medium">{a.id}</div>
                          <div className="text-2xs text-ink-3">{TYPE_SHORT[a.type]}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-2 py-2"><StatusPill status={a.status} /></td>
                    <td className="px-2 py-2"><Meter value={a.battery} /></td>
                    <td className="px-2 py-2 text-xs text-ink-2">{a.task_id ? `${TASK_LABEL[a.task_type ?? ""] ?? a.task_type} · ${a.incident_id}` : <span className="text-ink-3">-</span>}</td>
                    <td className="px-2 py-2 text-xs">{a.ai.status === "NORMAL" ? <span className="text-ink-3">Normal</span> : <span className="text-warn">{sentence(a.ai.event)}</span>}</td>
                    <td className="px-4 py-2 text-right tabular-nums text-ink-2">{a.neighbors.length}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {agents.length === 0 && <Empty title="No agents match this filter" />}
          </div>
        </Panel>
        <Panel className="xl:sticky xl:top-4 xl:max-h-[calc(100vh-7rem)]" bodyClassName="overflow-y-auto scroll-thin">
          {selected ? <AgentDetailPanel id={selected} /> : <Empty title="Select an agent">Choose a row to see its live sensors, radio neighbours, messages, task history and controls.</Empty>}
        </Panel>
      </div>
    </div>
  );
}

export default function AgentsPage() {
  return (
    <Suspense fallback={<div className="p-6 text-sm text-ink-3">Loading...</div>}>
      <FleetPage />
    </Suspense>
  );
}
