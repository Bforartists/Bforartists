"""Pure planning rules for BoneCraft material-atlas groups.

This module intentionally has no Blender dependency so the safety contract can
be tested without importing ``bpy``.
"""

RENDER_TYPE_ORDER = ("Opaque", "Alpha Clip", "Alpha Blend", "Emissive")


def plan_material_slot_groups(slots):
    """Partition material-slot records by render type.

    Alpha Blend slots are preserved by default because collapsing separate
    transparent materials destroys their draw order. Other groups are enabled
    automatically only when combining them can reduce at least two slots.
    """
    grouped = {render_type: [] for render_type in RENDER_TYPE_ORDER}
    for source in slots:
        if not source.get("has_faces", True):
            continue
        render_type = source["render_type"]
        grouped[render_type].append(
            {
                "object_name": source["object_name"],
                "slot_index": int(source["slot_index"]),
                "render_type": render_type,
            }
        )

    plans = []
    for render_type in RENDER_TYPE_ORDER:

        group_slots = grouped.get(render_type) or []
        if not group_slots:
            continue
        preserve = render_type == "Alpha Blend"
        plans.append(
            {
                "render_type": render_type,
                "enabled": len(group_slots) >= 2 and not preserve,
                "preserve_reason": "render_order" if preserve else "",
                "slots": group_slots,
            }
        )
    return plans
