"""
Task records.

A task is one unit of work for one agent on one incident, for example
"FIRE_SUPPRESSION at INC-0002". The owner can change (reassignment) while the
task keeps its id, so the history of who worked on it is preserved.
"""

UNASSIGNED = "UNASSIGNED"     # needed, but no suitable agent is available right now
ASSIGNED = "ASSIGNED"         # owner accepted and is travelling
IN_PROGRESS = "IN_PROGRESS"   # owner is on site performing the action
INTERRUPTED = "INTERRUPTED"   # owner failed / lost contact; waiting for reassignment
COMPLETED = "COMPLETED"
CANCELLED = "CANCELLED"

ACTIVE_TASK_STATUSES = {UNASSIGNED, ASSIGNED, IN_PROGRESS, INTERRUPTED}


class Task:

    def __init__(self, task_id, incident_id, task_type, capability, target, tick, optional=False):
        self.task_id = task_id
        self.incident_id = incident_id
        self.task_type = task_type
        self.capability = capability
        self.optional = optional
        self.target = target
        self.status = UNASSIGNED
        self.owner_id = None
        self.previous_owner_id = None
        self.owners = []              # [{agent_id, from_tick, to_tick, end}]
        self.reassign_count = 0
        self.created_tick = tick
        self.assigned_tick = None
        self.started_tick = None
        self.arrived_tick = None
        self.completed_tick = None
        self.interrupted_tick = None
        self.unassigned_since = tick
        self.owner_missing_ticks = 0
        self.work_done = 0.0          # severity points removed by this task
        self.ineffective_ticks = 0
        self.start_distance_m = None
        self.travel_progress = 0.0
        self.last_decision = []       # candidate table from the latest selection
        self.outcome = None
        self.search_points = []       # investigation search pattern
        self.search_index = 0

    @property
    def active(self) -> bool:
        return self.status in ACTIVE_TASK_STATUSES

    @property
    def progress(self) -> float:
        if self.status in (COMPLETED,):
            return 1.0
        if self.started_tick is None:
            return round(self.travel_progress * 0.5, 3)
        return 0.5 + min(0.5, self.work_done / 100.0)

    def end_current_owner(self, tick: int, end: str):
        if self.owners and self.owners[-1]["to_tick"] is None:
            self.owners[-1]["to_tick"] = tick
            self.owners[-1]["end"] = end

    def to_summary(self) -> dict:
        return {
            "id": self.task_id,
            "incident_id": self.incident_id,
            "task_type": self.task_type,
            "capability": self.capability,
            "status": self.status,
            "owner_id": self.owner_id,
            "previous_owner_id": self.previous_owner_id,
            "reassign_count": self.reassign_count,
            "progress": round(self.progress, 3),
            "work_done": round(self.work_done, 2),
            "optional": self.optional,
        }

    def to_dict(self) -> dict:
        data = self.to_summary()
        data.update({
            "target": [round(self.target[0], 6), round(self.target[1], 6)] if self.target else None,
            "owners": self.owners,
            "created_tick": self.created_tick,
            "assigned_tick": self.assigned_tick,
            "started_tick": self.started_tick,
            "completed_tick": self.completed_tick,
            "interrupted_tick": self.interrupted_tick,
            "last_decision": self.last_decision,
            "outcome": self.outcome,
        })
        return data
