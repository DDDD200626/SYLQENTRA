from dataclasses import dataclass, field


STATUSES = (
    "pending",
    "planning",
    "running",
    "reviewing",
    "completed",
    "failed",
    "cancelled",
    "awaiting_approval",
)

_TRANSITIONS = {
    "pending": {"planning", "cancelled"},
    "planning": {"running", "failed", "cancelled"},
    "running": {"reviewing", "failed", "cancelled", "awaiting_approval"},
    "reviewing": {"completed", "failed"},
    "awaiting_approval": {"running", "cancelled"},
    "completed": set(),
    "failed": set(),
    "cancelled": set(),
}


@dataclass
class OrchestrationState:
    request: str
    status: str = "pending"
    plan: list[str] = field(default_factory=list)
    outputs: dict[str, str] = field(default_factory=dict)
    final_output: str = ""
    error: str = ""

    def transition(self, status: str) -> None:
        if status not in STATUSES:
            raise ValueError(f"Unknown status '{status}'")
        if status not in _TRANSITIONS[self.status]:
            raise ValueError(f"Cannot move from {self.status} to {status}")
        self.status = status