import type { AgentType } from "@/lib/types";

/**
 * Shape encodes the agent TYPE, colour encodes its STATUS.
 * circle = monitor drone, triangle = fire drone, square = sprinkler,
 * hexagon = pollution unit, diamond = cooling unit.
 */
export function glyphPath(type: AgentType, s = 14): string {
  const c = s / 2;
  switch (type) {
    case "MONITOR_DRONE":
      return `M ${c} 1 A ${c - 1} ${c - 1} 0 1 1 ${c - 0.01} 1 Z`;
    case "FIRE_DRONE":
      return `M ${c} 0.5 L ${s - 0.5} ${s - 1} L 0.5 ${s - 1} Z`;
    case "SPRINKLER":
      return `M 1.5 1.5 H ${s - 1.5} V ${s - 1.5} H 1.5 Z`;
    case "POLLUTION_UNIT": {
      const pts = Array.from({ length: 6 }, (_, i) => {
        const a = (Math.PI / 3) * i + Math.PI / 6;
        return `${(c + (c - 0.8) * Math.cos(a)).toFixed(2)} ${(c + (c - 0.8) * Math.sin(a)).toFixed(2)}`;
      });
      return `M ${pts.join(" L ")} Z`;
    }
    case "COOLING_UNIT":
      return `M ${c} 0.5 L ${s - 0.5} ${c} L ${c} ${s - 0.5} L 0.5 ${c} Z`;
  }
}

export function glyphSvg(type: AgentType, color: string, opts: { failed?: boolean; ring?: string | null; size?: number } = {}) {
  const s = opts.size ?? 14;
  const fill = opts.failed ? "#14181A" : color;
  const stroke = opts.failed ? color : "#101416";
  const cross = opts.failed
    ? `<path d="M3.5 3.5 L${s - 3.5} ${s - 3.5} M${s - 3.5} 3.5 L3.5 ${s - 3.5}" stroke="${color}" stroke-width="1.6" stroke-linecap="round"/>`
    : "";
  const ring = opts.ring
    ? `<circle cx="${s / 2}" cy="${s / 2}" r="${s / 2 + 3.5}" fill="none" stroke="${opts.ring}" stroke-width="1.5" stroke-dasharray="3 2"/>`
    : "";
  return `<svg width="${s}" height="${s}" viewBox="0 0 ${s} ${s}">${ring}<path d="${glyphPath(type, s)}" fill="${fill}" stroke="${stroke}" stroke-width="1.5" stroke-linejoin="round"/>${cross}</svg>`;
}

export function AgentGlyph({ type, color, failed = false, size = 14 }: { type: AgentType; color: string; failed?: boolean; size?: number }) {
  return (
    <span
      aria-hidden
      className="inline-flex shrink-0 items-center justify-center"
      style={{ width: size, height: size }}
      dangerouslySetInnerHTML={{ __html: glyphSvg(type, color, { failed, size }) }}
    />
  );
}
