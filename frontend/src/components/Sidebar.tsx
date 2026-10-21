"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Compass,
  Cpu,
  Share2,
  Flame,
  LineChart,
  History,
  ShieldCheck,
  AlertTriangle,
  Radio,
  Sparkles
} from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { SystemStatus } from "@/lib/types";

const NAV_ITEMS = [
  {
    name: "Command Center",
    href: "/command-center",
    icon: Compass,
    tag: "LIVE TRANSECT",
  },
  {
    name: "Agent Operations",
    href: "/agents",
    icon: Cpu,
    tag: "FLEET",
  },
  {
    name: "Network Intelligence",
    href: "/network",
    icon: Share2,
    tag: "MESH",
  },
  {
    name: "Incident Management",
    href: "/incidents",
    icon: Flame,
    tag: "CONSENSUS",
  },
  {
    name: "Environmental Analytics",
    href: "/analytics",
    icon: LineChart,
    tag: "TELEMETRY",
  },
  {
    name: "System History",
    href: "/history",
    icon: History,
    tag: "ARCHIVE",
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [status, setStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await api.getStatus();
        setStatus(data);
      } catch (_) {}
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const total = status?.total_agents || 20;
  const active = status?.active_agents || 20;
  const isHealthy = status?.network_connected ?? true;

  return (
    <aside className="w-64 bg-surface border-r border-border flex flex-col justify-between shrink-0 select-none shadow-editorial z-20">
      {/* Brand Header */}
      <div>
        <div className="p-5 border-b border-border bg-surface-muted/60">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded bg-forest-green text-botanical flex items-center justify-center font-serif text-lg font-bold shadow-sm">
              <span className="text-botanical">☵</span>
            </div>
            <div>
              <div className="font-serif text-base font-bold tracking-tight text-forest-green flex items-center gap-1.5">
                Eco-Intelligence
              </div>
              <p className="text-[10px] font-mono uppercase tracking-wider text-secondary-text">
                Autonomous MAS Transect
              </p>
            </div>
          </div>
        </div>

        {/* Section Label */}
        <div className="px-5 pt-4 pb-1">
          <span className="editorial-tag text-[10px] text-secondary-text tracking-widest">
            MONITORING PLATFORM
          </span>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive =
              pathname === item.href ||
              (pathname === "/" && item.href === "/command-center");

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center justify-between px-3.5 py-2.5 rounded text-xs font-medium transition-all ${
                  isActive
                    ? "bg-forest-green text-surface font-semibold shadow-sm"
                    : "text-secondary-text hover:text-forest-green hover:bg-surface-muted"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon
                    className={`w-4 h-4 ${
                      isActive ? "text-botanical" : "text-secondary-green"
                    }`}
                  />
                  <span>{item.name}</span>
                </div>
                {isActive && (
                  <span className="w-1.5 h-1.5 rounded-full bg-botanical animate-pulse"></span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Persistent System Status Widget */}
      <div className="p-4 m-3 rounded bg-surface-muted border border-border">
        <div className="flex items-center justify-between mb-2.5 pb-2 border-b border-border/80">
          <span className="editorial-tag text-[9px] text-secondary-text tracking-wider">
            TRANSECT STATUS
          </span>
          <span className="flex items-center gap-1 text-[10px] font-mono font-medium text-forest-green">
            <span className="w-1.5 h-1.5 rounded-full bg-secondary-green inline-block"></span>
            CASCADE-01
          </span>
        </div>

        <div className="space-y-2 text-xs">
          <div className="flex items-center justify-between text-secondary-text">
            <span className="text-[11px]">Fleet Nodes:</span>
            <span className="font-mono font-semibold tabular-nums text-forest-green">
              <span className="text-secondary-green">{active}</span> / {total} ACTIVE
            </span>
          </div>

          <div className="flex items-center justify-between text-secondary-text">
            <span className="text-[11px]">Mesh Health:</span>
            <span
              className={`font-mono text-[10px] font-semibold flex items-center gap-1 ${
                isHealthy ? "text-forest-green" : "text-warning-amber"
              }`}
            >
              {isHealthy ? (
                <>
                  <ShieldCheck className="w-3.5 h-3.5 text-secondary-green" />
                  STABLE
                </>
              ) : (
                <>
                  <AlertTriangle className="w-3.5 h-3.5 text-warning-amber" />
                  DEGRADED
                </>
              )}
            </span>
          </div>

          <div className="pt-2 border-t border-border/70 flex items-center justify-between">
            <span className="editorial-tag text-[9px] text-secondary-text">
              DATA MODE
            </span>
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-muted-sage/60 text-forest-green border border-border">
              SIMULATION DATA
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
