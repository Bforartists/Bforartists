"""Driver targets from the current editor, without falling back to an Action."""
from __future__ import annotations


def in_driver_editor(context) -> bool:
    space = getattr(context, "space_data", None)
    return bool(space and space.type == "GRAPH_EDITOR" and space.mode == "DRIVERS")


def driver_curves(context, *, selected=False, editable=False) -> list:
    """Respect native editor visibility, channel selection, locks and ID editability."""
    if not in_driver_editor(context):
        return []
    curves = getattr(context, "visible_fcurves", ()) or ()
    return [fc for fc in curves if fc.driver is not None and not fc.hide
            and (not selected or fc.select)
            and (not editable or (not fc.lock and fc.id_data.is_editable))]


def active_driver(context):
    """Inspect the active curve, or the sole selected visible driver.

    Native active_editable_fcurve disappears on lock. Retain the explicitly
    selected driver so its right-sidebar lock control can still unlock it.
    """
    if not in_driver_editor(context):
        return None
    fc = getattr(context, "active_editable_fcurve", None)
    visible = driver_curves(context)
    if fc is not None and fc in visible:
        return fc
    selected = [curve for curve in visible if curve.select]
    return selected[0] if len(selected) == 1 else None


def driver_issues(fc, context) -> list[str]:
    """Read-only checks for a single driver; run on request, never on redraw."""
    driver = fc.driver
    issues = []
    if not driver.is_valid:
        issues.append("Driver evaluation failed; check the expression and targets, then refresh dependencies.")
    if not fc.id_data.is_editable:
        issues.append("Owner is linked or read-only.")
    if fc.lock:
        issues.append("Channel is locked.")
    if fc.mute:
        issues.append("Driver is muted.")
    for variable in driver.variables:
        for target in variable.targets:
            label = f"Variable {variable.name}"
            if variable.type == "CONTEXT_PROP":
                owner = context.scene if target.context_property == "ACTIVE_SCENE" else context.view_layer
            else:
                owner = target.id
            if owner is None:
                issues.append(f"{label}: missing target.")
                continue
            if variable.type in {"SINGLE_PROP", "CONTEXT_PROP"}:
                try:
                    if not target.data_path:
                        raise ValueError("Empty property path")
                    owner.path_resolve(target.data_path)
                except (ValueError, AttributeError, KeyError, TypeError):
                    if not target.use_fallback_value:
                        issues.append(f"{label}: unresolved property path {target.data_path!r}.")
            elif target.bone_target:
                pose = getattr(owner, "pose", None)
                if pose is None or pose.bones.get(target.bone_target) is None:
                    issues.append(f"{label}: missing bone {target.bone_target!r}.")
    return issues
