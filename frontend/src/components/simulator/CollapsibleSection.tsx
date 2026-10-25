"use client";

import React, { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cx } from "@/components/ui";

export interface CollapsibleSectionProps {
  id?: string;
  title: string;
  icon?: React.ReactNode;
  badge?: React.ReactNode;
  defaultOpen?: boolean;
  isOpen?: boolean;
  onToggle?: () => void;
  children: React.ReactNode;
  className?: string;
}

export function CollapsibleSection({
  title,
  icon,
  badge,
  defaultOpen = false,
  isOpen,
  onToggle,
  children,
  className,
}: CollapsibleSectionProps) {
  const [internalOpen, setInternalOpen] = useState(defaultOpen);
  const open = isOpen !== undefined ? isOpen : internalOpen;

  const handleToggle = () => {
    if (onToggle) {
      onToggle();
    } else {
      setInternalOpen((o) => !o);
    }
  };

  return (
    <div className={cx("rounded-lg border border-line bg-surface shadow-xs transition-all", className)}>
      <button
        type="button"
        onClick={handleToggle}
        className="flex w-full items-center justify-between px-3.5 py-2.5 text-left transition-colors hover:bg-selected/40 rounded-t-lg"
        aria-expanded={open}
      >
        <div className="flex items-center gap-2 min-w-0">
          {icon && <span className="text-primary shrink-0">{icon}</span>}
          <span className="font-cond text-sm font-bold tracking-wide text-ink uppercase truncate">
            {title}
          </span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {badge}
          <ChevronDown
            size={15}
            className={cx("text-ink-3 transition-transform duration-200", open && "rotate-180 text-primary")}
          />
        </div>
      </button>

      {open && (
        <div className="border-t border-line/60 p-3.5 space-y-3 animate-in fade-in duration-150">
          {children}
        </div>
      )}
    </div>
  );
}
