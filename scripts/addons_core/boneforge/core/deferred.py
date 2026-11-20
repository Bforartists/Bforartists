"""Deferred-mutation operator pattern (v3.3.0).

Operators that mutate Blender's registration state — register_class,
unregister_class, addon enable/disable, anything that touches bpy.types
class slots — cannot do that work directly inside ``execute``. The
operator's own class instance is on the call stack; tearing it down
mid-call causes a use-after-free in Blender's C++ layer, which
manifests as a hard segfault.

The official Blender pattern is to schedule the dangerous work via
``bpy.app.timers.register``. The timer callback runs AFTER the operator
returns and its class instance has been GC'd, so by the time the
mutation happens, no operator is on the stack.

This module exposes:

* :func:`schedule_after` — thin wrapper that catches & logs exceptions
  inside the deferred callback so a single failure can't disable the
  timer dispatcher.
* :class:`DeferredMutationOperator` — base class for any operator that
  needs to mutate registration state. Subclasses override
  ``_deferred_work(args)`` as a ``@staticmethod`` that does NOT touch
  ``self``. ``execute`` always returns ``{'FINISHED'}`` immediately.
"""

from __future__ import annotations

import logging
import traceback
from typing import Callable, Optional

import bpy

logger = logging.getLogger(__name__)


def schedule_after(
    func: Callable[[], Optional[float]],
    *,
    delay: float = 0.05,
    label: str = "deferred-task",
) -> None:
    """Schedule *func* to run after the current operator returns.

    *func* must accept zero args. Returning ``None`` runs the callback
    once; returning a float schedules a re-fire at that interval (rare
    in practice — most BoneCraft use cases are one-shot).

    Errors raised inside *func* are caught + logged, NEVER propagated.
    Letting an exception escape the timer dispatcher silently disables
    the timer system for the whole Blender session — a foot-gun we do
    not need.
    """
    def _wrapper():
        try:
            return func()
        except Exception:
            logger.error("[BoneCraft] deferred task %r raised:", label)
            traceback.print_exc()
            return None  # do not re-fire on error
    bpy.app.timers.register(_wrapper, first_interval=delay)


class DeferredMutationOperator(bpy.types.Operator):
    """Base class for operators that mutate registration state.

    Usage:

    .. code-block:: python

        class BF_OT_MyMutation(DeferredMutationOperator):
            bl_idname = "boneforge.my_mutation"
            bl_label = "My Mutation"

            def _capture(self):
                # Snapshot any operator props or context we need
                # inside the deferred work — by the time the timer
                # fires, ``self`` may be invalid.
                return {"target_id": self.target_id}

            def _scheduled_message(self):
                return f"Mutating {self.target_id}…"

            @staticmethod
            def _deferred_work(args):
                # No ``self`` here. Plain Python code with no
                # operator-instance lifetime concerns.
                do_the_dangerous_thing(args["target_id"])

    The base class handles:
    * scheduling via :func:`schedule_after`,
    * informational ``self.report`` to the user at scheduling time,
    * graceful reporting of scheduling failures.
    """

    def execute(self, context):
        try:
            captured_args = self._capture()
        except Exception as exc:
            self.report({"ERROR"}, f"Could not capture state: {exc}")
            return {"CANCELLED"}

        try:
            schedule_after(
                lambda: self._run_deferred(captured_args),
                label=self.bl_idname,
            )
        except Exception as exc:
            self.report({"ERROR"}, f"Could not schedule: {exc}")
            return {"CANCELLED"}

        self.report({"INFO"}, self._scheduled_message())
        return {"FINISHED"}

    def _capture(self) -> dict:
        """Return a dict of state to pass into ``_deferred_work``.

        Override if your deferred work needs operator props or context
        snapshots — anything captured here is safe to use after ``self``
        is GC'd. Default returns an empty dict.
        """
        return {}

    @classmethod
    def _run_deferred(cls, args: dict) -> None:
        """Static dispatch from the timer to the subclass's work fn."""
        cls._deferred_work(args)

    @staticmethod
    def _deferred_work(args: dict) -> None:
        """Override with the actual mutation work.

        Must be a ``@staticmethod`` — accessing ``self`` here is a bug
        because the operator instance has been GC'd by the time the
        timer fires.
        """
        raise NotImplementedError(
            "DeferredMutationOperator subclasses must override "
            "_deferred_work(args) as a @staticmethod that does not "
            "touch self.",
        )

    def _scheduled_message(self) -> str:
        """Override to customise the user-facing report at schedule time."""
        return "Scheduled — running shortly…"
