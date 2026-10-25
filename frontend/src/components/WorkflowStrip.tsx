import { Check } from "lucide-react";
import { HAZARD_COLOR, HAZARD_LABEL, fmtTicks } from "@/lib/format";
import type { Incident } from "@/lib/types";
import { cx } from "./ui";

type StageState = "done" | "current" | "todo" | "problem";

/** The real lifecycle stages of one incident, derived from backend fields. */
export function incidentStages(i: Incident, tick: number) {
  const responseTasks = i.tasks.filter((t) => t.task_type !== "INVESTIGATE");
  const reassigned = responseTasks.reduce((n, t) => n + t.reassign_count, 0);
  const interrupted = responseTasks.some((t) => t.status === "INTERRUPTED");
  const unassigned = responseTasks.some((t) => t.status === "UNASSIGNED");
  const moving = responseTasks.some((t) => t.status === "ASSIGNED");
  const acting = responseTasks.filter((t) => t.status === "IN_PROGRESS").length;
  const verifying = i.status === "DETECTED";
  const confirmed = i.confirmed_tick !== null;
  const resolved = i.status === "RESOLVED";
  const rejected = i.status === "REJECTED";

  const stages: { label: string; detail: string; state: StageState }[] = [
    {
      label: "Detected",
      detail: i.detected_tick !== null ? `${i.detectors.slice(0, 3).join(", ")}${i.detectors.length > 3 ? "..." : ""} after ${fmtTicks(i.detected_tick - i.created_tick)}` : i.rejections ? `Rejected ${i.rejections}x, still monitoring` : "Waiting for sensors",
      state: i.detected_tick !== null ? "done" : "current",
    },
    {
      label: "Local consensus",
      detail: i.consensus
        ? `${i.consensus.supporters.length} support · ${i.consensus.opposers.length} oppose · ${Math.round(i.consensus.confidence * 100)}%`
        : "Collecting evidence",
      state: rejected ? "problem" : confirmed ? "done" : verifying ? "current" : "todo",
    },
    {
      label: "Tasks assigned",
      detail: responseTasks.length ? responseTasks.map((t) => t.owner_id ?? "unassigned").join(", ") : "-",
      state: unassigned ? "problem" : responseTasks.length && confirmed ? "done" : confirmed ? "current" : "todo",
    },
    {
      label: "Moving",
      detail: moving ? `${responseTasks.filter((t) => t.status === "ASSIGNED").map((t) => t.owner_id).join(", ")} en route` : acting ? "On site" : "-",
      state: acting || resolved ? "done" : moving ? "current" : "todo",
    },
    {
      label: "Responding",
      detail: acting ? `${acting} acting · severity ${Math.round(i.severity)}` : interrupted ? "Responder lost" : reassigned ? `Reassigned ${reassigned}x` : "-",
      state: resolved ? "done" : interrupted ? "problem" : acting ? "current" : "todo",
    },
    {
      label: i.status === "NEEDS_INTERVENTION" ? "Needs intervention" : "Resolved",
      detail: resolved ? `after ${fmtTicks((i.resolved_tick ?? tick) - i.created_tick)}` : i.status === "NEEDS_INTERVENTION" ? "No capable agent available" : "-",
      state: resolved ? "done" : i.status === "NEEDS_INTERVENTION" ? "problem" : "todo",
    },
  ];
  return { stages, reassigned };
}

const DOT: Record<StageState, string> = {
  done: "bg-[#398C69] border-[#398C69]",
  current: "bg-transparent border-[#397FB8] ring-2 ring-[#397FB8]/30",
  todo: "bg-transparent border-line",
  problem: "bg-[#E96C4B] border-[#E96C4B]",
};

export function WorkflowStrip({ incident, tick }: { incident: Incident; tick: number }) {
  const { stages, reassigned } = incidentStages(incident, tick);
  const color = HAZARD_COLOR[incident.type];
  return (
    <div className="rounded-lg border border-line bg-surface/95 px-4 py-3 shadow-md backdrop-blur-md">
      <div className="mb-2.5 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="flex items-center gap-2 font-cond text-[15px] font-bold text-ink">
          <span className="h-2.5 w-2.5 rounded-full" style={{ background: color }} />
          {incident.id} · {HAZARD_LABEL[incident.type]}
        </span>
        <span className="text-xs text-ink-2 font-medium">
          Severity {Math.round(incident.severity)} / 100{incident.coordinator_id ? ` · coordinator ${incident.coordinator_id}` : ""}
          {reassigned ? ` · ${reassigned} reassignment${reassigned > 1 ? "s" : ""}` : ""}
        </span>
      </div>
      <ol className="grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-3 xl:grid-cols-6">
        {stages.map((s, idx) => (
          <li key={s.label} className="min-w-0">
            <div className="flex items-center gap-2">
              <span className={cx("flex h-4 w-4 shrink-0 items-center justify-center rounded-full border-2", DOT[s.state])}>
                {s.state === "done" && <Check size={10} strokeWidth={3} className="text-white" />}
              </span>
              <span className={cx("text-xs font-semibold", s.state === "todo" ? "text-ink-3" : "text-ink")}>
                {idx + 1}. {s.label}
              </span>
            </div>
            <p className="ml-6 truncate text-2xs text-ink-2" title={s.detail}>{s.detail}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}
