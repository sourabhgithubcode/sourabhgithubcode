from enum import Enum


class WorkMode(str, Enum):
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    ONSITE = "On-site"
    UNKNOWN = "Unknown"


class VisaCategory(str, Enum):
    HIGH = "High"
    MID = "Mid"
    LOW = "Low"
    NO_HISTORY = "No history so far"


class ConfidenceBand(str, Enum):
    HIGH = "High"
    MID = "Mid"
    LOW = "Low"
    NO_HISTORY = "No history so far"


class SourceStatus(str, Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    DISABLED = "disabled"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
