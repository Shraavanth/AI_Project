"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AuditLog } from "@/lib/types";
import {
  History as HistoryIcon,
  Filter,
  Search,
  Clock,
  CheckCircle,
  AlertTriangle,
  Zap,
  PowerOff,
  Flame,
  Radio,
  FileText,
  Download,
  ChevronDown,
  ChevronRight
} from "lucide-react";

export default function SystemHistoryPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [category, setCategory] = useState<string>("ALL");
  const [search, setSearch] = useState<string>("");
  const [expandedLogId, setExpandedLogId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const CATEGORIES = [
    "ALL",
    "EVENT",
    "ANOMALIES",
    "CONSENSUS",
    "FAILURES",
    "RECOVERY",
    "NETWORK",
    "AGENTS",
  ];

  const fetchLogs = async () => {
    try {
      const data = await api.getHistory(category, 150);
      setLogs(data);
    } catch (err) {
      console.error("Failed to load history logs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category]);

  const filteredLogs = logs.filter((log) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      log.title.toLowerCase().includes(q) ||
      log.message.toLowerCase().includes(q) ||
      (log.agent_id && log.agent_id.toLowerCase().includes(q))
    );
  });

  const handleExportCSV = () => {
    const headers = "id,category,agent_id,title,message,timestamp\n";
    const rows = filteredLogs
      .map(
        (l) =>
          `${l.id},"${l.category}","${l.agent_id || ""}",` +
          `"${l.title.replace(/"/g, '""')}","${l.message.replace(/"/g, '""')}","${l.timestamp}"`
      )
      .join("\n");
    const blob = new Blob([headers + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cascade-transect-audit-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportJSON = () => {
    const blob = new Blob([JSON.stringify(filteredLogs, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cascade-transect-audit-${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case "EVENT":
        return "bg-critical-incident/15 text-critical-incident border-critical-incident/30";
      case "FAILURES":
        return "bg-warning-amber/15 text-warning-amber border-warning-amber/30";
      case "RECOVERY":
        return "bg-muted-sage text-forest-green border-border";
      case "CONSENSUS":
        return "bg-botanical/20 text-forest-green border-botanical/40";
      case "NETWORK":
        return "bg-surface-muted text-secondary-text border-border";
      case "AGENTS":
        return "bg-muted-sage/60 text-forest-green border-border";
      default:
        return "bg-surface-muted text-secondary-text border-border";
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-border pb-5">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="editorial-tag text-secondary-text mb-1 tracking-widest">
              PERSISTENT FIELD ARCHIVE
            </div>
            <h1 className="editorial-title text-3xl md:text-4xl font-serif font-bold text-forest-green tracking-tight leading-none">
              System Audit Log & Telemetry Archive.
            </h1>
            <p className="mt-2 text-sm text-secondary-text max-w-2xl leading-relaxed">
              Immutable ledger of field node state transitions, peer-to-peer consensus deliberations,
              topological network self-healing events, and classified environmental anomalies.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto">
            <button
              onClick={handleExportCSV}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface hover:bg-surface-muted text-secondary-text hover:text-forest-green border border-border transition text-xs font-mono"
            >
              <Download className="w-3.5 h-3.5" />
              <span>CSV</span>
            </button>
            <button
              onClick={handleExportJSON}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-forest-green hover:bg-forest-green-light text-surface transition text-xs font-mono shadow-sm"
            >
              <Download className="w-3.5 h-3.5 text-botanical" />
              <span>JSON</span>
            </button>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
        {/* Category Pills */}
        <div className="flex items-center gap-1.5 self-start sm:self-auto overflow-x-auto pb-1 sm:pb-0 w-full sm:w-auto">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className={`px-3 py-1 rounded text-xs font-mono transition ${
                category === c
                  ? "bg-forest-green text-surface font-semibold"
                  : "bg-surface text-secondary-text hover:text-forest-green border border-border"
              }`}
            >
              {c}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-secondary-text" />
          <input
            type="text"
            placeholder="Search records by title, node, text..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded bg-surface border border-border text-xs text-forest-green focus:outline-none focus:border-forest-green font-mono placeholder:text-secondary-text/60"
          />
        </div>
      </div>

      {/* Main Historical Timeline Table */}
      <div className="bg-surface rounded border border-border shadow-editorial overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-surface-muted border-b border-border text-[10px] text-secondary-text uppercase tracking-wider font-mono">
                <th className="py-3 px-4 w-28">Timestamp</th>
                <th className="py-3 px-4 w-28">Category</th>
                <th className="py-3 px-4 w-24">Node</th>
                <th className="py-3 px-4">Event Title & Narrative</th>
                <th className="py-3 px-4 w-12 text-right"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-secondary-text font-serif italic">
                    No log entries matching filter criteria.
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => {
                  const isExpanded = expandedLogId === log.id;
                  const dateStr = log.timestamp ? log.timestamp.split("T")[0] : "";
                  const timeStr = log.timestamp ? log.timestamp.split("T")[1]?.slice(0, 8) : "";

                  return (
                    <tr
                      key={log.id}
                      className="hover:bg-surface-muted/50 transition cursor-pointer"
                      onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                    >
                      {/* Timestamp */}
                      <td className="py-3 px-4 font-mono text-[10px] text-secondary-text tabular-nums whitespace-nowrap">
                        <div className="text-forest-green font-semibold">{timeStr}</div>
                        <div className="text-secondary-text/70">{dateStr}</div>
                      </td>

                      {/* Category */}
                      <td className="py-3 px-4">
                        <span
                          className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-mono border font-semibold ${getCategoryBadge(
                            log.category
                          )}`}
                        >
                          {log.category}
                        </span>
                      </td>

                      {/* Node ID */}
                      <td className="py-3 px-4 font-mono font-bold text-forest-green text-xs">
                        {log.agent_id ? (
                          <span className="px-1.5 py-0.5 rounded bg-surface-muted border border-border">
                            {log.agent_id}
                          </span>
                        ) : (
                          <span className="text-secondary-text font-normal">—</span>
                        )}
                      </td>

                      {/* Title & Message */}
                      <td className="py-3 px-4">
                        <div className="font-serif font-bold text-forest-green text-[13px] mb-0.5">
                          {log.title}
                        </div>
                        <p className="text-[11px] text-secondary-text leading-relaxed">
                          {log.message}
                        </p>

                        {isExpanded && log.details && (
                          <div className="mt-2.5 p-2.5 rounded bg-surface-muted border border-border font-mono text-[10px] text-forest-green overflow-x-auto">
                            <span className="editorial-tag text-[8px] text-secondary-text block mb-1">
                              PAYLOAD METADATA JSON
                            </span>
                            <pre>{JSON.stringify(log.details, null, 2)}</pre>
                          </div>
                        )}
                      </td>

                      {/* Expand indicator */}
                      <td className="py-3 px-4 text-right text-secondary-text">
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 ml-auto" />
                        ) : (
                          <ChevronRight className="w-4 h-4 ml-auto opacity-50" />
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        <div className="px-4 py-2.5 bg-surface-muted border-t border-border flex items-center justify-between text-xs text-secondary-text font-mono">
          <span>SHOWING {filteredLogs.length} OF {logs.length} AUDIT RECORDS</span>
          <span>IMMUTABLE DATABASE LEDGER</span>
        </div>
      </div>
    </div>
  );
}
