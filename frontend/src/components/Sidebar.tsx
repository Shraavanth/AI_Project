"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Boxes, History, Map, Network, Siren, X, Menu } from "lucide-react";
import { useState } from "react";
import { useSim } from "./SimulationProvider";
import { cx } from "./ui";

const NAV = [
  { href: "/simulator", label: "Area simulator", icon: Map },
  { href: "/command-center", label: "Command center", icon: Activity },
  { href: "/agents", label: "Agent fleet", icon: Boxes },
  { href: "/incidents", label: "Incidents & response", icon: Siren },
  { href: "/network", label: "Network", icon: Network },
  { href: "/history", label: "History & analytics", icon: History },
];

const CONNECTION_TEXT = {
  live: { text: "Live", color: "#398C69" },
  polling: { text: "Reconnecting - polling", color: "#D99A39" },
  connecting: { text: "Connecting", color: "#397FB8" },
  offline: { text: "Backend unreachable", color: "#E96C4B" },
};

export function Sidebar() {
  const pathname = usePathname();
  const { snapshot, connection } = useSim();
  const [open, setOpen] = useState(false);
  const conn = CONNECTION_TEXT[connection];
  const activeIncidents = snapshot?.stats.active_incidents ?? 0;

  const nav = (
    <nav className="flex flex-1 flex-col gap-1 px-2.5" aria-label="Main">
      {NAV.map(({ href, label, icon: Icon }) => {
        const active = pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            onClick={() => setOpen(false)}
            className={cx(
              "group flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
              active
                ? "bg-[#B8D2E8] text-[#18344D] font-semibold border-l-4 border-[#397FB8] shadow-xs"
                : "text-[#18344D]/90 hover:bg-[#B8D2E8]/60 hover:text-[#18344D] font-medium",
            )}
            aria-current={active ? "page" : undefined}
          >
            <Icon size={17} strokeWidth={active ? 2.2 : 1.8} className={active ? "text-[#397FB8]" : "text-[#536F86] group-hover:text-[#18344D]"} />
            <span className="flex-1">{label}</span>
            {href === "/incidents" && activeIncidents > 0 && (
              <span className="rounded bg-[#E96C4B]/20 px-1.5 py-0.5 text-2xs font-bold text-[#E96C4B] border border-[#E96C4B]/40">{activeIncidents}</span>
            )}
          </Link>
        );
      })}
    </nav>
  );

  const footer = (
    <div className="space-y-2.5 border-t border-[#B2C9DC] bg-[#C9DDED] px-4 py-3 text-xs">
      <div className="flex items-center gap-2">
        <span className="h-2.5 w-2.5 rounded-full ring-2 ring-white/50" style={{ background: conn.color }} />
        <span className="text-[#18344D] font-semibold">{conn.text}</span>
      </div>
      {snapshot && (
        <div className="space-y-1.5 text-[#536F86]">
          <div className="flex justify-between">
            <span>Simulation</span>
            <span className="text-[#18344D] font-medium">
              {snapshot.simulation.running ? "Running" : "Paused"} · {snapshot.simulation.speed}x
            </span>
          </div>
          <div className="flex justify-between">
            <span>Sim time</span>
            <span className="tabular-nums text-[#18344D] font-medium">t = {snapshot.tick} s</span>
          </div>
          <div className="flex justify-between">
            <span>Storage</span>
            <span className={snapshot.database.ok ? "text-[#18344D] font-medium" : "text-[#E96C4B] font-semibold"}>
              {snapshot.database.ok ? snapshot.database.label : "Write errors"}
            </span>
          </div>
        </div>
      )}
    </div>
  );

  const brand = (
    <div className="px-5 pb-5 pt-5">
      <div className="flex items-center gap-2">
        <div className="h-3 w-3 rounded-full bg-[#397FB8] shadow-xs" />
        <div className="font-cond text-xl font-bold leading-none tracking-tight text-[#18344D]">EnvMAS</div>
      </div>
      <div className="mt-1.5 text-xs leading-snug text-[#536F86]">Self-organizing environmental monitoring</div>
    </div>
  );

  return (
    <>
      {/* Mobile top bar */}
      <div className="flex h-12 items-center justify-between border-b border-[#B2C9DC] bg-[#C9DDED] px-4 lg:hidden">
        <div className="flex items-center gap-2">
          <div className="h-2.5 w-2.5 rounded-full bg-[#397FB8]" />
          <span className="font-cond text-base font-semibold text-[#18344D]">EnvMAS</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="h-2 w-2 rounded-full" style={{ background: conn.color }} title={conn.text} />
          <button onClick={() => setOpen(true)} aria-label="Open navigation" className="text-[#18344D]">
            <Menu size={20} />
          </button>
        </div>
      </div>
      {open && (
        <div className="fixed inset-0 z-[1200] flex lg:hidden">
          <div className="absolute inset-0 bg-[#18344D]/40 backdrop-blur-xs" onClick={() => setOpen(false)} />
          <aside className="relative flex w-64 flex-col bg-[#C9DDED] border-r border-[#B2C9DC] shadow-xl">
            <button onClick={() => setOpen(false)} aria-label="Close navigation" className="absolute right-3 top-4 text-[#536F86] hover:text-[#18344D]">
              <X size={18} />
            </button>
            {brand}
            {nav}
            {footer}
          </aside>
        </div>
      )}
      <aside className="hidden w-60 shrink-0 flex-col border-r border-[#B2C9DC] bg-[#C9DDED] lg:flex shadow-xs">
        {brand}
        {nav}
        {footer}
      </aside>
    </>
  );
}
