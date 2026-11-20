# --- ORCHESTRATION AND RECOVERY ---
"""Transaction history and error log for orchestration audit trail.

Records every operator invocation and error that passes through the
orchestration layer. Useful for debugging workflows, reproducing bugs,
and understanding what happened during a complex session.

Public API:
    log_operation(op_id, success, detail, elapsed_ms)
    log_error(source, message, traceback_str)
    get_history(limit)    — recent operations
    get_errors(limit)     — recent errors
    get_stats()           — aggregate session stats
    clear_history()       — wipe operation log
    clear_errors()        — wipe error log
    clear_all()           — wipe everything
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Any

from .logging import get_logger

__all__ = [
    "OperationRecord",
    "ErrorRecord",
    "set_limits",
    "log_operation",
    "log_error",
    "get_history",
    "get_errors",
    "get_stats",
    "clear_history",
    "clear_errors",
    "clear_all",
]

_log = get_logger(__name__)


@dataclass
class OperationRecord:
    """One logged operator invocation."""
    op_id: str
    timestamp: float
    success: bool
    detail: str = ""
    elapsed_ms: float = 0.0


@dataclass
class ErrorRecord:
    """One logged error."""
    source: str
    message: str
    traceback_str: str = ""
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


# ---------------------------------------------------------------------------
# Audit state namespace
# ---------------------------------------------------------------------------

class _AuditState:
    """Namespace for module-level audit state."""

    def __init__(self) -> None:
        self.max_history: int = 100
        self.max_errors: int = 100
        self.history: deque[OperationRecord] = deque(maxlen=self.max_history)
        self.errors: deque[ErrorRecord] = deque(maxlen=self.max_errors)
        # Aggregate counters (survive clear_history)
        self.total_ops: int = 0
        self.total_failures: int = 0
        self.session_start: float = time.time()


_state = _AuditState()


def set_limits(max_history: int = 100, max_errors: int = 100) -> None:
    """Reconfigure buffer sizes."""
    _state.max_history = max(10, min(max_history, 500))
    _state.max_errors = max(10, min(max_errors, 500))
    # Rebuild deques with new maxlen
    _state.history = deque(_state.history, maxlen=_state.max_history)
    _state.errors = deque(_state.errors, maxlen=_state.max_errors)


def log_operation(
    op_id: str,
    success: bool = True,
    detail: str = "",
    elapsed_ms: float = 0.0,
) -> None:
    """Record an operator invocation."""
    _state.total_ops += 1
    if not success:
        _state.total_failures += 1

    record = OperationRecord(
        op_id=op_id,
        timestamp=time.time(),
        success=success,
        detail=detail,
        elapsed_ms=elapsed_ms,
    )
    _state.history.append(record)
    _log.debug("Audit: %s %s (%.1fms) %s",
               op_id, "OK" if success else "FAIL", elapsed_ms, detail)


def log_error(source: str, message: str, traceback_str: str = "") -> None:
    """Record an error."""
    record = ErrorRecord(
        source=source,
        message=message,
        traceback_str=traceback_str,
    )
    _state.errors.append(record)
    _log.debug("Audit error: [%s] %s", source, message)


def get_history(limit: int = 50) -> list[dict[str, Any]]:
    """Return recent operation records as dicts (newest first)."""
    items = list(reversed(_state.history))[:limit]
    return [
        {
            "op_id": r.op_id,
            "timestamp": r.timestamp,
            "success": r.success,
            "detail": r.detail,
            "elapsed_ms": r.elapsed_ms,
        }
        for r in items
    ]


def get_errors(limit: int = 50) -> list[dict[str, Any]]:
    """Return recent error records as dicts (newest first)."""
    items = list(reversed(_state.errors))[:limit]
    return [
        {
            "source": r.source,
            "message": r.message,
            "traceback_str": r.traceback_str,
            "timestamp": r.timestamp,
        }
        for r in items
    ]


def get_stats() -> dict[str, Any]:
    """Return aggregate session statistics."""
    return {
        "total_operations": _state.total_ops,
        "total_failures": _state.total_failures,
        "success_rate": (
            (_state.total_ops - _state.total_failures) / _state.total_ops * 100.0
            if _state.total_ops > 0 else 100.0
        ),
        "buffered_operations": len(_state.history),
        "buffered_errors": len(_state.errors),
        "session_uptime_s": time.time() - _state.session_start,
    }


def clear_history() -> None:
    """Wipe the operation history buffer."""
    _state.history.clear()
    _log.debug("Audit history cleared")


def clear_errors() -> None:
    """Wipe the error log."""
    _state.errors.clear()
    _log.debug("Audit errors cleared")


def clear_all() -> None:
    """Wipe everything and reset counters."""
    _state.history.clear()
    _state.errors.clear()
    _state.total_ops = 0
    _state.total_failures = 0
    _state.session_start = time.time()
    _log.debug("Audit fully reset")
