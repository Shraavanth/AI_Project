"use client";

/* Shared Recharts styling: recessive grid/axes, text in ink tokens, hover tooltip on every chart. */

export const AXIS = {
  stroke: "#B2C9DC",
  tick: { fill: "#71879B", fontSize: 11 },
  tickLine: false,
  axisLine: { stroke: "#B2C9DC" },
} as const;

export const GRID = { stroke: "#C9DDED", strokeDasharray: "3 3", vertical: false } as const;

export const SERIES = { blue: "#397FB8", orange: "#E96C4B", teal: "#36A6B5", amber: "#D99A39", green: "#398C69" };

interface TooltipPayload {
  name?: string;
  value?: number | string;
  color?: string;
  dataKey?: string | number;
  payload?: Record<string, unknown>;
}

export function ChartTooltip({
  active, payload, label, labelPrefix = "t = ", labelSuffix = " s", format,
}: {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string | number;
  labelPrefix?: string;
  labelSuffix?: string;
  format?: (v: number | string, name?: string) => string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-line bg-raised px-3 py-2 text-xs shadow-lg shadow-black/40">
      <div className="mb-1 text-ink-3">{labelPrefix}{label}{labelSuffix}</div>
      {payload.map((p) => (
        <div key={String(p.dataKey)} className="flex items-center gap-2 text-ink">
          <span className="h-2 w-2 rounded-full" style={{ background: p.color }} />
          <span className="text-ink-2">{p.name}</span>
          <span className="ml-auto pl-3 tabular-nums">{p.value !== undefined && format ? format(p.value, p.name) : p.value}</span>
        </div>
      ))}
    </div>
  );
}

export function LegendRow({ items }: { items: { color: string; label: string; dashed?: boolean }[] }) {
  return (
    <div className="flex flex-wrap gap-4 text-xs text-ink-2">
      {items.map((i) => (
        <span key={i.label} className="flex items-center gap-1.5">
          <span className="inline-block h-0.5 w-4" style={{ background: i.dashed ? "transparent" : i.color, borderTop: i.dashed ? `2px dashed ${i.color}` : undefined }} />
          {i.label}
        </span>
      ))}
    </div>
  );
}
