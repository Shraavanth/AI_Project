"use client";

import { Power, RotateCcw } from "lucide-react";
import { useMemo, useState } from "react";
import { glyphPath } from "@/components/AgentGlyph";
import { useSim } from "@/components/SimulationProvider";
import { Button, Empty, KeyValue, PageHeader, Panel, StatusPill, cx } from "@/components/ui";
import { STATUS_COLOR, fmtDistance, sentence } from "@/lib/format";
import type { NetworkEvent } from "@/lib/types";
import { usePolling } from "@/lib/usePolling";

interface NetworkResponse {
  components: string[][];
  connected: boolean;
  comm_range_m: number;
  max_relay_range_m: number;
  events: NetworkEvent[];
  link_churn: number;
}

const SIZE = 1000;

export default function NetworkPage() {
  const { snapshot, act } = useSim();
  const { data: net } = usePolling<NetworkResponse>("/api/network", 2000);
  const [selected, setSelected] = useState<string | null>(null);
  const [eventIndex, setEventIndex] = useState<number | null>(0);

  const proj = useMemo(() => {
    if (!snapshot) return null;
    const { lat, lng, radius_m } = snapshot.site;
    const half = radius_m * 1.18;
    const k = Math.cos((lat * Math.PI) / 180) * 111320;
    return (pLat: number, pLng: number): [number, number] => {
      const x = (pLng - lng) * k;
      const y = (pLat - lat) * 111320;
      return [((x + half) / (2 * half)) * SIZE, ((half - y) / (2 * half)) * SIZE];
    };
  }, [snapshot]);

  if (!snapshot || !proj) return <div className="p-6 text-sm text-ink-3">Connecting to the simulation...</div>;

  const byId = new Map(snapshot.agents.map((a) => [a.id, a]));
  const events = net?.events ?? (snapshot.network.last_event ? [snapshot.network.last_event] : []);
  const focusEvent = eventIndex !== null ? events[eventIndex] ?? null : null;
  const recent = focusEvent;
  const createdSet = new Set((recent?.links_created ?? []).map(([a, b]) => [a, b].sort().join("|")));
  const sel = selected ? byId.get(selected) : null;
  const scale = SIZE / (snapshot.site.radius_m * 2.36);
  const [cx0, cy0] = proj(snapshot.site.lat, snapshot.site.lng);

  return (
    <div className="pb-8">
      <PageHeader
        title="Network and self-organization"
        subtitle={`Agents link automatically when within ${fmtDistance(snapshot.network.comm_range_m)} (Haversine distance). If the network splits, the closest agents of separate clusters form a relay link up to ${fmtDistance(snapshot.network.max_relay_range_m)}.`}
      />
      <div className="grid gap-4 px-5 lg:px-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Panel
          title="Communication graph"
          aside={
            <span className={snapshot.network.connected ? "text-green font-semibold" : "text-red font-semibold"}>
              {snapshot.network.connected ? "Connected" : `Partitioned into ${snapshot.network.components} clusters`} · {snapshot.network.edges} links
            </span>
          }
          bodyClassName="p-2"
        >
          <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="mx-auto block max-h-[calc(100vh-14rem)] w-full rounded-lg bg-panel/60 border border-line" role="img" aria-label="Communication graph of all agents placed by their real positions">
            <circle cx={cx0} cy={cy0} r={snapshot.site.radius_m * scale} fill="none" stroke="#B2C9DC" strokeDasharray="3 6" strokeWidth={1.5} />
            {/* Links removed by the selected reorganization (ghosted) */}
            {recent?.links_removed.map(([a, b]) => {
              const A = byId.get(a);
              const B = byId.get(b);
              if (!A || !B) return null;
              const [x1, y1] = proj(A.lat, A.lng);
              const [x2, y2] = proj(B.lat, B.lng);
              return <line key={`rm-${a}-${b}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#E96C4B" strokeWidth={1.8} strokeDasharray="4 5" opacity={0.85} />;
            })}
            {snapshot.links.map((l) => {
              const A = byId.get(l.source);
              const B = byId.get(l.target);
              if (!A || !B) return null;
              const [x1, y1] = proj(A.lat, A.lng);
              const [x2, y2] = proj(B.lat, B.lng);
              const isNew = createdSet.has([l.source, l.target].sort().join("|"));
              const touchesSel = selected && (l.source === selected || l.target === selected);
              return (
                <line
                  key={`${l.source}-${l.target}`}
                  x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke={isNew ? "#398C69" : l.kind === "relay" ? "#D99A39" : touchesSel ? "#397FB8" : "#397FB8"}
                  strokeWidth={isNew || touchesSel ? 2.4 : l.kind === "relay" ? 2 : 1.3}
                  strokeDasharray={l.kind === "relay" ? "6 4" : undefined}
                  opacity={selected && !touchesSel && !isNew ? 0.25 : isNew ? 1 : touchesSel ? 0.95 : 0.65}
                >
                  <title>{`${l.source} - ${l.target}: ${fmtDistance(l.distance_m)} (${l.kind})`}</title>
                </line>
              );
            })}
            {snapshot.agents.map((a) => {
              const [x, y] = proj(a.lat, a.lng);
              const failed = a.status === "FAILED";
              const color = STATUS_COLOR[a.status] ?? "#71879B";
              const s = selected === a.id ? 20 : 15;
              return (
                <g
                  key={a.id}
                  transform={`translate(${x - s / 2} ${y - s / 2})`}
                  onClick={() => setSelected(a.id === selected ? null : a.id)}
                  onKeyDown={(e) => e.key === "Enter" && setSelected(a.id)}
                  tabIndex={0}
                  role="button"
                  aria-label={`${a.id}, ${a.status}, ${a.neighbors.length} links`}
                  className="cursor-pointer outline-none"
                >
                  <circle cx={s / 2} cy={s / 2} r={s} fill="transparent" />
                  {a.coordinator_of.length > 0 && <circle cx={s / 2} cy={s / 2} r={s / 2 + 5} fill="none" stroke="#D99A39" strokeWidth={1.8} strokeDasharray="3 2" />}
                  <path d={glyphPath(a.type, s)} fill={failed ? "#EDF4F9" : color} stroke={failed ? color : "#18344D"} strokeWidth={1.8} strokeLinejoin="round" />
                  {failed && <path d={`M3.5 3.5 L${s - 3.5} ${s - 3.5} M${s - 3.5} 3.5 L3.5 ${s - 3.5}`} stroke={color} strokeWidth={2} strokeLinecap="round" />}
                  <text x={s + 5} y={s / 2 + 4} fontSize={13} fontWeight={700} fill={failed ? "#71879B" : "#18344D"} fontFamily="'Barlow Semi Condensed', Barlow, sans-serif" paintOrder="stroke" stroke="#FFFFFF" strokeWidth={3.5}>
                    {a.id}
                  </text>
                </g>
              );
            })}
          </svg>
          <div className="flex flex-wrap gap-x-5 gap-y-1.5 px-3 py-2 text-xs text-ink-2">
            <span className="flex items-center gap-1.5"><span className="h-0.5 w-4 bg-[#397FB8]" /> Radio link (≤ {fmtDistance(snapshot.network.comm_range_m)})</span>
            <span className="flex items-center gap-1.5"><span className="w-4 border-t-2 border-dashed border-[#D99A39]" /> Relay link (self-organized)</span>
            <span className="flex items-center gap-1.5"><span className="h-0.5 w-4 bg-[#398C69]" /> Created by selected reorganization</span>
            <span className="flex items-center gap-1.5"><span className="w-4 border-t-2 border-dashed border-[#E96C4B]" /> Removed by it</span>
            <span className="flex items-center gap-1.5"><span className="h-3 w-3 rounded-full border border-dashed border-[#D99A39]" /> Incident coordinator</span>
          </div>
        </Panel>

        <div className="flex min-w-0 flex-col gap-4">
          <Panel title={sel ? sel.id : "Selected agent"}>
            {sel ? (
              <div className="space-y-3">
                <dl>
                  <KeyValue label="Status"><StatusPill status={sel.status} /></KeyValue>
                  <KeyValue label="Type">{sel.type_label}</KeyValue>
                  <KeyValue label="Links">{sel.neighbors.length}</KeyValue>
                  {sel.coordinator_of.length > 0 && <KeyValue label="Coordinates">{sel.coordinator_of.join(", ")}</KeyValue>}
                </dl>
                {sel.neighbors.length > 0 && <p className="text-xs text-ink-2">Neighbours: {sel.neighbors.join(", ")}</p>}
                {sel.status === "FAILED" ? (
                  <Button onClick={() => act(`/api/agents/${sel.id}/restore`, undefined, `${sel.id} restored - it rejoins after rebooting.`)}><RotateCcw size={15} /> Restore</Button>
                ) : (
                  <Button variant="danger" disabled={sel.status === "RECOVERING"} onClick={async () => { await act(`/api/agents/${sel.id}/fail`, undefined, `${sel.id} failed - see the links removed and the new ones formed.`); setEventIndex(0); }}>
                    <Power size={15} /> Fail this agent
                  </Button>
                )}
              </div>
            ) : (
              <p className="text-sm text-ink-3">Click a node to see its links, then fail it to watch the network reorganize.</p>
            )}
          </Panel>

          <Panel title="Clusters" aside={<span>{net?.components.length ?? snapshot.network.components}</span>}>
            {net ? (
              <ul className="space-y-1.5 text-xs">
                {net.components.map((c, idx) => (
                  <li key={idx} className="text-ink-2"><span className="text-ink">Cluster {idx + 1}</span> ({c.length}): {c.join(", ")}</li>
                ))}
              </ul>
            ) : <p className="text-sm text-ink-3">Loading...</p>}
            <p className="mt-2 text-2xs text-ink-3">Failed and rebooting agents are not part of the network.</p>
          </Panel>

          <Panel title="Reorganizations" aside={<span>{events.length}</span>} bodyClassName="max-h-[420px] overflow-y-auto scroll-thin">
            {events.length === 0 ? (
              <Empty title="No reorganization yet">Fail an agent to see which links disappear and which relay links form.</Empty>
            ) : (
              <ul className="divide-y divide-line">
                {events.map((e, idx) => (
                  <li key={`${e.tick}-${idx}`}>
                    <button onClick={() => setEventIndex(idx)} className={cx("w-full px-4 py-2.5 text-left transition-colors hover:bg-selected/30", eventIndex === idx ? "bg-selected border-l-4 border-l-primary font-medium" : "hover:bg-selected/20")}>
                      <div className="flex items-baseline justify-between gap-2">
                        <span className="text-sm font-semibold text-ink">{sentence(e.trigger)} of {e.agent_id}</span>
                        <span className="text-2xs font-mono tabular-nums text-ink-3">t = {e.tick}</span>
                      </div>
                      <div className="text-xs text-ink-2">
                        {e.links_removed.length} removed · {e.links_created.length} created ({e.relay_links.length} relay) · {e.edges_after} links
                      </div>
                      <div className={cx("text-xs font-medium", e.connected_after ? "text-green" : "text-red")}>
                        {e.connected_after ? "Network connected" : `Partitioned: ${e.components_after} clusters (no bridge within range)`} · computed in {e.compute_ms} ms
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
