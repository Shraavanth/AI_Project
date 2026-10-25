"use client";

import Link from "next/link";
import { AgentGlyph } from "@/components/AgentGlyph";
import { SimControls } from "@/components/SimControls";
import { useSim } from "@/components/SimulationProvider";
import { Empty, Meter, PageHeader, Panel, StatusPill, Tag, cx } from "@/components/ui";
import {
  HAZARD_COLOR, HAZARD_LABEL, INCIDENT_STATUS_COLOR, INCIDENT_STATUS_LABEL, STATUS_COLOR, TASK_LABEL,
  TASK_STATUS_COLOR, CATEGORY_COLOR, fmtTicks, sentence,
} from "@/lib/format";


function Figure({ label, value, note, tone }: { label: string; value: React.ReactNode; note?: string; tone?: string }) {
  return (
    <div className="min-w-[132px] flex-1 border-b border-r border-line bg-surface px-4 py-3 transition-colors hover:bg-selected/20">
      <div className="text-xs font-semibold text-ink-2">{label}</div>
      <div className="font-cond text-2xl font-bold tabular-nums leading-tight text-ink" style={tone ? { color: tone } : undefined}>{value}</div>
      {note && <div className="text-2xs text-ink-3 font-medium">{note}</div>}
    </div>
  );
}

export default function CommandCenterPage() {
  const { snapshot } = useSim();
  if (!snapshot) return <div className="p-6 text-sm text-ink-3">Connecting to the simulation...</div>;
  const { stats, tick } = snapshot;
  const open = snapshot.incidents.filter((i) => !["RESOLVED", "REJECTED"].includes(i.status));
  const tasks = snapshot.incidents
    .flatMap((i) => i.tasks)
    .filter((t) => ["UNASSIGNED", "ASSIGNED", "IN_PROGRESS", "INTERRUPTED"].includes(t.status));
  const silent = snapshot.agents.filter((a) => a.status !== "FAILED" && a.last_telemetry_tick !== null && tick - a.last_telemetry_tick > 2);

  return (
    <div className="pb-8">
      <PageHeader
        title="Central Command Center"
        subtitle="What every agent reports: telemetry, incidents, task ownership and network health. Agents make decisions locally; this view monitors and records."
        actions={<SimControls compact />}
      />

      <div className="mx-5 -mb-px -mr-px flex flex-wrap overflow-hidden rounded-lg border-l border-t border-line bg-surface shadow-xs lg:mx-6">
        <Figure label="Operational agents" value={`${stats.operational_agents}/${stats.total_agents}`} note={`${stats.patrolling_agents} patrolling · ${stats.moving_agents} moving`} />
        <Figure label="Failed" value={stats.failed_agents} tone={stats.failed_agents ? "#E96C4B" : undefined} note={stats.recovering_agents ? `${stats.recovering_agents} rebooting` : "agents offline"} />
        <Figure label="Responding" value={stats.responding_agents} tone={stats.responding_agents ? "#E96C4B" : undefined} note="acting on site" />
        <Figure label="Active incidents" value={stats.active_incidents} tone={stats.incidents_needing_intervention ? "#E96C4B" : undefined} note={stats.incidents_needing_intervention ? `${stats.incidents_needing_intervention} need intervention` : `${stats.resolved_incidents} resolved this run`} />
        <Figure label="Radio links" value={stats.links} note={stats.relay_links ? `${stats.relay_links} relay links` : "all within normal range"} />
        <Figure label="Network" value={stats.network_connected ? "Connected" : `${stats.network_components} clusters`} tone={stats.network_connected ? undefined : "#E96C4B"} note={`${stats.messages_delivered} messages delivered`} />
        <Figure label="Average battery" value={`${Math.round(stats.average_battery)}%`} note={`${stats.anomalous_agents} agents reading anomalies`} />
      </div>

      <div className="mt-4 grid gap-4 px-5 lg:px-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
        <div className="flex min-w-0 flex-col gap-4">
          <Panel title="Incidents" aside={<Link href="/incidents" className="text-primary hover:text-primary-hover font-semibold">All incidents</Link>} bodyClassName="">
            {open.length === 0 ? (
              <Empty title="No open incidents">All operational agents report normal conditions. Start an incident from the Area Simulator.</Empty>
            ) : (
              <ul className="divide-y divide-line">
                {open.map((i) => {
                  const responders = i.tasks.filter((t) => t.task_type !== "INVESTIGATE");
                  return (
                    <li key={i.id}>
                      <Link href={`/incidents?id=${i.id}`} className="grid grid-cols-[auto_1fr_auto] items-center gap-x-4 gap-y-1 px-4 py-3 transition-colors hover:bg-selected/40 sm:grid-cols-[auto_minmax(0,1.2fr)_minmax(0,1fr)_auto]">
                        <span className="h-2.5 w-2.5 rounded-full" style={{ background: HAZARD_COLOR[i.type] }} />
                        <div className="min-w-0">
                          <div className="font-semibold text-ink">{HAZARD_LABEL[i.type]} {i.id}</div>
                          <div className="text-xs text-ink-3">
                            {i.coordinator_id ? `Coordinator ${i.coordinator_id}` : "Not detected yet"} · open {fmtTicks(tick - i.created_tick)}
                          </div>
                        </div>
                        <div className="hidden min-w-0 truncate text-xs text-ink-2 sm:block">
                          {responders.length ? responders.map((t) => `${t.owner_id ?? "unassigned"}`).join(", ") : "No responders yet"}
                        </div>
                        <div className="flex flex-col items-end gap-1">
                          <Tag color={INCIDENT_STATUS_COLOR[i.status] ?? "#71879B"}>{INCIDENT_STATUS_LABEL[i.status] ?? i.status}</Tag>
                          <Meter value={i.severity} color={HAZARD_COLOR[i.type]} label="Severity" unit="" />
                        </div>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            )}
          </Panel>

          <Panel title="Task ownership" aside={<span className="text-ink-2 font-semibold">{tasks.length} active</span>} bodyClassName="overflow-x-auto">
            {tasks.length === 0 ? (
              <Empty title="No active tasks">Tasks appear when local consensus confirms an incident.</Empty>
            ) : (
              <table className="w-full min-w-[560px] text-sm">
                <thead>
                  <tr className="border-b border-line bg-header text-left text-xs text-ink font-semibold">
                    <th className="px-4 py-2">Task</th>
                    <th className="px-2 py-2">Incident</th>
                    <th className="px-2 py-2">Owner</th>
                    <th className="px-2 py-2">Status</th>
                    <th className="px-4 py-2 text-right">Progress</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map((t) => (
                    <tr key={t.id} className="border-b border-line/60 last:border-0 hover:bg-selected/30 transition-colors">
                      <td className="px-4 py-2 font-medium text-ink">{TASK_LABEL[t.task_type] ?? t.task_type}<div className="text-2xs text-ink-3">{t.id}</div></td>
                      <td className="px-2 py-2 text-ink-2">{t.incident_id}</td>
                      <td className="px-2 py-2 text-ink font-mono font-medium">
                        {t.owner_id ?? <span className="text-red">none</span>}
                        {t.reassign_count > 0 && <div className="text-2xs text-ink-3 font-sans">reassigned from {t.previous_owner_id}</div>}
                      </td>
                      <td className="px-2 py-2 font-semibold"><span style={{ color: TASK_STATUS_COLOR[t.status] }}>{sentence(t.status)}</span></td>
                      <td className="px-4 py-2 text-right"><Meter value={t.progress * 100} color="#866CC5" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Panel>

          <Panel title="Telemetry" aside={<span className="text-ink-2">{silent.length ? `${silent.length} agents silent` : `all operational agents reporting · t = ${tick} s`}</span>} bodyClassName="overflow-x-auto">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="border-b border-line bg-header text-left text-xs text-ink font-semibold">
                  <th className="px-4 py-2">Agent</th>
                  <th className="px-2 py-2">Status</th>
                  <th className="px-2 py-2">Battery</th>
                  <th className="px-2 py-2 text-right">Temp °C</th>
                  <th className="px-2 py-2 text-right">Smoke</th>
                  <th className="px-2 py-2 text-right">CO₂</th>
                  <th className="px-2 py-2">Local AI</th>
                  <th className="px-4 py-2 text-right">Last report</th>
                </tr>
              </thead>
              <tbody>
                {snapshot.agents.map((a) => {
                  const age = a.last_telemetry_tick === null ? null : tick - a.last_telemetry_tick;
                  return (
                    <tr key={a.id} className={cx("border-b border-line/60 last:border-0 hover:bg-selected/30 transition-colors", a.status === "FAILED" && "text-ink-3")}>
                      <td className="px-4 py-1.5 font-medium text-ink font-mono">
                        <Link href={`/agents?id=${a.id}`} className="flex items-center gap-2 hover:underline">
                          <AgentGlyph type={a.type} color={STATUS_COLOR[a.status]} failed={a.status === "FAILED"} size={11} />
                          {a.id}
                        </Link>
                      </td>
                      <td className="px-2 py-1.5"><StatusPill status={a.status} /></td>
                      <td className="px-2 py-1.5"><Meter value={a.battery} /></td>
                      <td className="px-2 py-1.5 text-right tabular-nums text-ink">{a.readings.temperature.toFixed(1)}</td>
                      <td className="px-2 py-1.5 text-right tabular-nums text-ink">{a.readings.smoke.toFixed(2)}</td>
                      <td className="px-2 py-1.5 text-right tabular-nums text-ink">{Math.round(a.readings.co2)}</td>
                      <td className="px-2 py-1.5 text-xs">{a.ai.status === "NORMAL" ? <span className="text-ink-3">Normal</span> : <span className="text-warn font-semibold">{sentence(a.ai.event)}</span>}</td>
                      <td className={cx("px-4 py-1.5 text-right text-xs tabular-nums", age !== null && age > 2 ? "text-red font-semibold" : "text-ink-3")}>
                        {age === null ? "-" : age <= 1 ? "now" : `${age} s ago`}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Panel>
        </div>

        <Panel title="Recent activity" aside={<Link href="/history" className="text-primary hover:text-primary-hover font-semibold">Full history</Link>} className="xl:sticky xl:top-4 xl:max-h-[calc(100vh-7rem)]" bodyClassName="overflow-y-auto scroll-thin">
          {snapshot.activity.length === 0 ? (
            <Empty title="Nothing yet" />
          ) : (
            <ol className="divide-y divide-line">
              {snapshot.activity.map((e, idx) => (
                <li key={`${e.timestamp}-${idx}`} className="flex gap-3 px-4 py-2.5">
                  <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full" style={{ background: CATEGORY_COLOR[e.category] ?? "#76807B" }} />
                  <div className="min-w-0">
                    <div className="flex items-baseline justify-between gap-2">
                      <span className="text-sm font-medium text-ink">{e.title}</span>
                      <span className="shrink-0 text-2xs tabular-nums text-ink-3">t = {e.tick}</span>
                    </div>
                    <p className="text-xs leading-relaxed text-ink-2">{e.message}</p>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </Panel>
      </div>
    </div>
  );
}
