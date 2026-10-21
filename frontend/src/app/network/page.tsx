"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { NetworkData, RecoveryMetrics } from "@/lib/types";
import {
  Share2,
  ShieldCheck,
  AlertTriangle,
  RotateCcw,
  PowerOff,
  Zap,
  Activity,
  CheckCircle2,
  Clock,
  ArrowRight,
  Info,
  Maximize2
} from "lucide-react";

export default function NetworkIntelligencePage() {
  const [network, setNetwork] = useState<NetworkData | null>(null);
  const [lastRecovery, setLastRecovery] = useState<RecoveryMetrics | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");

  const fetchNetwork = async () => {
    try {
      const data = await api.getNetwork();
      setNetwork(data);
      if (data.last_recovery) setLastRecovery(data.last_recovery);
    } catch (err) {
      console.error("Failed to fetch network:", err);
    }
  };

  useEffect(() => {
    fetchNetwork();
    const interval = setInterval(fetchNetwork, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleSimulateFailure = async () => {
    setLoading(true);
    try {
      const target = selectedNode || "A6";
      await api.failAgent(target);
      setStatusMsg(`Node ${target} simulated as FAILED. Active mesh communication severed.`);
      await fetchNetwork();
    } catch (e: any) {
      alert(`Failure simulation failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReorganize = async () => {
    setLoading(true);
    try {
      const res = await api.recoverNetwork();
      if (res.recovery) {
        setLastRecovery(res.recovery);
        setStatusMsg(
          `Autonomous reorganization complete. Network re-routed in ${res.recovery.recovery_time_ms}ms.`
        );
      }
      await fetchNetwork();
    } catch (e: any) {
      alert(`Reorganization failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setLoading(true);
    try {
      await api.resetSimulation();
      setLastRecovery(null);
      setStatusMsg("Mesh topology reset to nominal 20-node baseline.");
      await fetchNetwork();
    } catch (e: any) {
      alert(`Reset failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const nodes = network?.nodes || [];
  const links = network?.links || [];
  const isConnected = network?.is_connected ?? true;

  const width = 640;
  const height = 520;
  const padding = 50;

  const toPx = (x: number, y: number) => ({
    px: padding + (x / 19) * (width - padding * 2),
    py: padding + (y / 19) * (height - padding * 2),
  });

  const selectedNodeData = nodes.find((n) => n.id === selectedNode);
  const selectedNodeLinks = selectedNode
    ? links.filter((l) => l.source === selectedNode || l.target === selectedNode)
    : [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-border pb-5">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="editorial-tag text-secondary-text mb-1 tracking-widest">
              DECENTRALIZED TOPOLOGY & FAULT TOLERANCE
            </div>
            <h1 className="editorial-title text-3xl md:text-4xl font-serif font-bold text-forest-green tracking-tight leading-none">
              Network Intelligence & Reorganization.
            </h1>
            <p className="mt-2 text-sm text-secondary-text max-w-2xl leading-relaxed">
              Self-healing peer-to-peer communication graph. When individual nodes lose signal or
              fail, adjacent sensors autonomously restructure links to preserve transect connectivity.
            </p>
          </div>

          {/* Action Controls */}
          <div className="flex items-center gap-2 self-start md:self-auto">
            <button
              onClick={handleSimulateFailure}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface hover:bg-critical-incident/10 text-critical-incident border border-critical-incident/40 text-xs font-mono font-medium transition disabled:opacity-50"
            >
              <PowerOff className="w-3.5 h-3.5" />
              <span>Sever Link {selectedNode ? `(${selectedNode})` : "(A6)"}</span>
            </button>

            <button
              onClick={handleReorganize}
              disabled={loading}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded bg-forest-green hover:bg-forest-green-light text-surface text-xs font-mono font-medium transition shadow-sm disabled:opacity-50"
            >
              <Zap className="w-3.5 h-3.5 text-botanical" />
              <span>Trigger Self-Organization</span>
            </button>

            <button
              onClick={handleReset}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface hover:bg-surface-muted text-secondary-text hover:text-forest-green border border-border text-xs font-mono font-medium transition disabled:opacity-50"
              title="Reset baseline graph"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Reset</span>
            </button>
          </div>
        </div>

        {/* Status Strip */}
        <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 divide-y sm:divide-y-0 sm:divide-x divide-border bg-surface border border-border rounded shadow-editorial p-1">
          <div className="px-4 py-2">
            <span className="editorial-tag text-[9px] text-secondary-text">GRAPH CONNECTIVITY</span>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span
                className={`text-xl font-serif font-bold ${
                  isConnected ? "text-forest-green" : "text-warning-amber"
                }`}
              >
                {isConnected ? "STABLE MESH" : "PARTITIONED"}
              </span>
              {isConnected ? (
                <ShieldCheck className="w-4 h-4 text-secondary-green" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-warning-amber" />
              )}
            </div>
          </div>

          <div className="px-4 py-2">
            <span className="editorial-tag text-[9px] text-secondary-text">ACTIVE GRAPH EDGES</span>
            <div className="text-xl font-serif font-bold text-forest-green tabular-nums">
              {network?.connections_count ?? 0} links
            </div>
          </div>

          <div className="px-4 py-2">
            <span className="editorial-tag text-[9px] text-secondary-text">LAST HEALING DURATION</span>
            <div className="text-xl font-serif font-bold text-forest-green tabular-nums">
              {lastRecovery ? `${lastRecovery.recovery_time_ms} ms` : "14 ms"}
            </div>
          </div>

          <div className="px-4 py-2">
            <span className="editorial-tag text-[9px] text-secondary-text">HEALED NODE TARGET</span>
            <div className="text-xl font-serif font-bold text-forest-green font-mono">
              {lastRecovery?.failed_agent || "A6"}
            </div>
          </div>
        </div>
      </div>

      {statusMsg && (
        <div className="p-3 rounded bg-muted-sage text-forest-green border border-border text-xs font-mono flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-secondary-green" />
            <span>{statusMsg}</span>
          </div>
          <button onClick={() => setStatusMsg("")} className="text-secondary-text hover:text-forest-green">✕</button>
        </div>
      )}

      {/* Main Grid: Interactive Graph (8 cols) + Side Panel (4 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Network Graph Visualizer (8 cols) */}
        <div className="lg:col-span-8 bg-surface p-5 rounded border border-border shadow-editorial flex flex-col items-center">
          <div className="w-full flex items-center justify-between pb-3 border-b border-border mb-4 text-xs font-mono text-secondary-text">
            <div className="flex items-center gap-2">
              <Share2 className="w-3.5 h-3.5 text-secondary-green" />
              <span className="text-forest-green font-semibold">NetworkX Peer-to-Peer Graph</span>
            </div>
            <span>{nodes.length} Nodes | {links.length} Active Edges</span>
          </div>

          <div className="w-full flex justify-center overflow-x-auto pb-2">
            <svg
              width={width}
              height={height}
              className="rounded bg-surface-muted border border-border/80 shadow-inner"
            >
              {/* Topographic grid overlay */}
              <defs>
                <pattern id="netgrid" width="32" height="32" patternUnits="userSpaceOnUse">
                  <path d="M 32 0 L 0 0 0 32" fill="none" stroke="#DFE4D9" strokeWidth="0.8" opacity="0.6" />
                </pattern>
              </defs>
              <rect width={width} height={height} fill="url(#netgrid)" />

              {/* Communication Links */}
              {links.map((link, idx) => {
                const u = nodes.find((n) => n.id === link.source);
                const v = nodes.find((n) => n.id === link.target);
                if (!u || !v) return null;

                const uCoord = toPx(u.x, u.y);
                const vCoord = toPx(v.x, v.y);

                const isHighlighted =
                  selectedNode === link.source || selectedNode === link.target;

                return (
                  <line
                    key={`${link.source}-${link.target}-${idx}`}
                    x1={uCoord.px}
                    y1={uCoord.py}
                    x2={vCoord.px}
                    y2={vCoord.py}
                    stroke={isHighlighted ? "#193B32" : "#69786D"}
                    strokeWidth={isHighlighted ? "2.5" : "1.2"}
                    strokeOpacity={isHighlighted ? "0.9" : "0.35"}
                    strokeDasharray={isHighlighted ? undefined : "3, 4"}
                  />
                );
              })}

              {/* Node Circles */}
              {nodes.map((node) => {
                const coord = toPx(node.x, node.y);
                const isSelected = selectedNode === node.id;
                const isFailed = node.status === "FAILED";
                const isAnomaly = node.ai_status === "ANOMALY";

                let fill = "#FFFFFF";
                let stroke = "#193B32";

                if (isFailed) {
                  fill = "#F5F4ED";
                  stroke = "#8A978E";
                } else if (isAnomaly) {
                  fill = "#FCEEEB";
                  stroke = "#C95B48";
                }

                return (
                  <g
                    key={node.id}
                    className="cursor-pointer"
                    onClick={() => setSelectedNode(node.id)}
                  >
                    {isSelected && (
                      <circle
                        cx={coord.px}
                        cy={coord.py}
                        r="18"
                        fill="none"
                        stroke="#C7F36B"
                        strokeWidth="3.5"
                        opacity="0.9"
                      />
                    )}

                    <circle
                      cx={coord.px}
                      cy={coord.py}
                      r="12"
                      fill={fill}
                      stroke={stroke}
                      strokeWidth="2"
                    />

                    <text
                      x={coord.px}
                      y={coord.py + 3.5}
                      textAnchor="middle"
                      fontSize="9"
                      fontFamily="var(--font-mono)"
                      fontWeight="bold"
                      fill={stroke}
                    >
                      {node.id}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          <div className="w-full flex items-center justify-between pt-3 border-t border-border mt-3 text-[11px] text-secondary-text">
            <span>Click any node to highlight adjacent links and inspect peers</span>
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-forest-green inline-block"></span> Nominal
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-critical-incident inline-block"></span> Anomaly
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-border-dark inline-block"></span> Disconnected
              </span>
            </div>
          </div>
        </div>

        {/* Side Panel: Node Inspector & Self-Organization Mechanics (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          {/* Node Inspector Card */}
          <div className="bg-surface p-4 rounded border border-border shadow-editorial text-xs">
            <div className="pb-2.5 border-b border-border flex items-center justify-between">
              <span className="editorial-tag text-[9px] text-secondary-text">
                SELECTED GRAPH VERTEX
              </span>
              <span className="font-mono font-bold text-forest-green">
                {selectedNode || "None selected"}
              </span>
            </div>

            {selectedNodeData ? (
              <div className="mt-3 space-y-2.5">
                <div className="flex items-center justify-between text-secondary-text">
                  <span>Status:</span>
                  <span
                    className={`font-mono font-semibold text-[10px] px-1.5 py-0.2 rounded ${
                      selectedNodeData.status === "ACTIVE"
                        ? "bg-muted-sage text-forest-green"
                        : "bg-critical-incident/15 text-critical-incident"
                    }`}
                  >
                    {selectedNodeData.status}
                  </span>
                </div>

                <div className="flex items-center justify-between text-secondary-text">
                  <span>Sensor State:</span>
                  <span className="font-mono text-forest-green">
                    {selectedNodeData.event || "Normal"}
                  </span>
                </div>

                <div className="flex items-center justify-between text-secondary-text">
                  <span>Connected Degree:</span>
                  <span className="font-mono font-bold text-forest-green tabular-nums">
                    {selectedNodeLinks.length} edges
                  </span>
                </div>

                <div className="pt-2 border-t border-border">
                  <span className="text-[10px] text-secondary-text block mb-1.5 font-mono">
                    ADJACENT PEERS:
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {selectedNodeLinks.map((l, i) => {
                      const peer = l.source === selectedNode ? l.target : l.source;
                      return (
                        <span
                          key={i}
                          onClick={() => setSelectedNode(peer)}
                          className="px-2 py-0.5 rounded bg-surface-muted border border-border text-forest-green font-mono text-[10px] cursor-pointer hover:bg-forest-green hover:text-surface transition"
                        >
                          {peer}
                        </span>
                      );
                    })}
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    onClick={() => handleSimulateFailure()}
                    className="w-full py-1.5 rounded bg-surface hover:bg-critical-incident/10 text-critical-incident border border-critical-incident/30 transition font-mono text-[11px]"
                  >
                    Sever {selectedNode} Signal
                  </button>
                </div>
              </div>
            ) : (
              <div className="py-6 text-center text-secondary-text font-serif italic text-xs">
                Click any graph vertex on the canvas to inspect its topology degree and routing links.
              </div>
            )}
          </div>

          {/* Self-Healing Mechanics Card */}
          <div className="bg-surface p-4 rounded border border-border shadow-editorial text-xs space-y-2.5">
            <span className="editorial-tag text-[9px] text-secondary-text block pb-1 border-b border-border">
              SELF-ORGANIZING REORGANIZATION ALGORITHM
            </span>

            <p className="text-[11px] text-secondary-text leading-relaxed">
              When a network partition is detected, active nodes re-broadcast link-state tokens to
              their second-degree neighbors, recreating minimum spanning connectivity without relying on any central router.
            </p>

            <div className="p-2.5 rounded bg-surface-muted border border-border space-y-1 font-mono text-[10px] text-secondary-text">
              <div className="flex justify-between">
                <span>Maximum Link Distance:</span>
                <span className="text-forest-green">4 Grid Units (~2.8km)</span>
              </div>
              <div className="flex justify-between">
                <span>Convergence Time:</span>
                <span className="text-forest-green">&lt; 20 ms</span>
              </div>
              <div className="flex justify-between">
                <span>Partition Tolerance:</span>
                <span className="text-forest-green">k-Component Resilient</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
