"use client";

import { forwardRef } from "react";
import { STATUS_COLOR, STATUS_HELP, sentence } from "@/lib/format";

export function cx(...parts: (string | false | null | undefined)[]) {
  return parts.filter(Boolean).join(" ");
}

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md";
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "secondary", size = "md", className, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      {...props}
      className={cx(
        "inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-40",
        size === "sm" ? "h-7 px-2.5 text-xs" : "h-9 px-3.5 text-sm",
        variant === "primary" && "bg-primary text-white hover:bg-primary-hover shadow-xs font-semibold",
        variant === "secondary" && "border border-line bg-surface text-ink hover:bg-selected/50 hover:border-primary/50 shadow-xs",
        variant === "ghost" && "text-ink-2 hover:bg-selected/40 hover:text-ink",
        variant === "danger" && "border border-red/40 bg-red/10 text-red hover:bg-red/20",
        className,
      )}
    />
  );
});

export function StatusPill({ status, title }: { status: string; title?: string }) {
  const color = STATUS_COLOR[status] ?? "#71879B";
  return (
    <span
      title={title ?? STATUS_HELP[status]}
      className="inline-flex items-center gap-1.5 whitespace-nowrap text-xs text-ink-2"
    >
      <span className="h-2 w-2 rounded-full" style={{ background: color }} />
      {sentence(status)}
    </span>
  );
}

export function Tag({ color, children }: { color: string; children: React.ReactNode }) {
  return (
    <span
      className="inline-flex items-center gap-1 whitespace-nowrap rounded px-1.5 py-0.5 text-2xs font-medium"
      style={{ background: `${color}22`, color, boxShadow: `inset 0 0 0 1px ${color}44` }}
    >
      {children}
    </span>
  );
}

export function Meter({ value, color, label, unit = "%" }: { value: number; color?: string; label?: string; unit?: string }) {
  const v = Math.max(0, Math.min(100, value));
  const c = color ?? (v < 25 ? "#E96C4B" : v < 50 ? "#D99A39" : "#398C69");
  return (
    <span className="inline-flex items-center gap-2" aria-label={label ? `${label} ${Math.round(v)}${unit}` : undefined}>
      <span className="relative h-1.5 w-14 overflow-hidden rounded-full bg-line/60">
        <span className="absolute inset-y-0 left-0 rounded-full" style={{ width: `${v}%`, background: c }} />
      </span>
      <span className="w-8 text-right text-xs tabular-nums text-ink-2">{Math.round(v)}{unit}</span>
    </span>
  );
}

export function Panel({
  title,
  aside,
  children,
  className,
  bodyClassName,
}: {
  title?: React.ReactNode;
  aside?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section className={cx("flex min-h-0 flex-col rounded-lg border border-line bg-surface shadow-xs", className)}>
      {(title || aside) && (
        <header className="flex items-center justify-between gap-3 border-b border-line bg-header px-4 py-2.5 rounded-t-lg">
          <h2 className="font-cond text-[15px] font-semibold text-ink">{title}</h2>
          {aside && <div className="flex items-center gap-2 text-xs text-ink-2">{aside}</div>}
        </header>
      )}
      <div className={cx("min-h-0", bodyClassName ?? "p-4")}>{children}</div>
    </section>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 px-5 pb-4 pt-5 lg:px-6">
      <div>
        <h1 className="font-cond text-2xl font-semibold leading-tight text-ink">{title}</h1>
        {subtitle && <p className="mt-1 max-w-2xl text-sm text-ink-2">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Empty({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-1.5 px-6 py-10 text-center">
      <p className="font-cond text-base font-semibold text-ink">{title}</p>
      {children && <div className="max-w-sm text-sm text-ink-2">{children}</div>}
    </div>
  );
}

export function KeyValue({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-1 text-sm">
      <dt className="text-ink-3">{label}</dt>
      <dd className="text-right text-ink">{children}</dd>
    </div>
  );
}
