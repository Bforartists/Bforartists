"""Show, don't hide (owner, 2026-10-10).

A section or sub-panel whose tools need a certain object stays visible when that object is not the
active one. Instead of vanishing, which reads as "the tool is gone", it draws one line saying what
to select, and a Select button when exactly one suitable object is in the scene.

``draw(layout, context, note, kinds)`` draws that line. ``kinds`` lists the object kinds that would
satisfy the panel, in preference order: "ARMATURE", "MESH", or "MECH_RIG" (an armature carrying
Mechanisms). The first kind with exactly one candidate gets the button.

The sub-panels of a waiting section stay visible too, as folds whose body says what to select
(``keep_children_visible``), so a section never hides what it holds.
"""
import bpy
from bpy.props import StringProperty
from bpy.types import Operator

from boneforge.i18n import T

# Every note a panel can draw (English keys); tests use it to tell a note from a tool's own text.
NOTES = {
    "Overview needs an avatar: select its armature or one of its meshes.",
    "Skin needs an armature or a mesh selected.",
    "Review needs an armature selected.",
    "Retarget needs an armature selected.",
    "Rigify Tools needs an armature selected.",
    "Correctives needs an armature selected.",
    "Delta Mush needs a mesh selected, in Object Mode.",
    "Proximity Wrap needs a mesh selected, in Object Mode.",
    "Game Export needs an armature selected.",
    "Viseme Library needs an armature selected.",
    "Select a mesh to start, or an armature with mechanisms.",     # Mechanisms' own start hint
    # what a waiting section's sub-panels say (see GATES)
    "Select an avatar to use this.",
    "Select an armature or a mesh to use this.",
    "Select an armature to use this.",
    "Select a mesh or a mechanism rig to use this.",
    "Add parts above to use this.",
    # the CATS tab's sections (owner, 2026-10-10: nothing vanishes when the rig is gone)
    "Avatar Tools needs an armature or a mesh selected.",
    "VRChat Tools needs an armature or a mesh selected.",
}


def _candidates(context, kind):
    """Selectable scene objects of ``kind``."""
    scene = getattr(context, "scene", None)
    if scene is None:
        return []
    out = []
    for ob in scene.objects:
        try:
            if not ob.visible_get() or ob.hide_select:
                continue                                  # hidden or unselectable: a button would do nothing
        except Exception:                                 # noqa: BLE001 - an object outside the view layer
            continue
        if kind == "MECH_RIG":
            data = ob.data if ob.type == 'ARMATURE' else None
            rec = getattr(data, "bonecraft_mech", None) if data is not None else None
            if rec is not None and (len(rec.parts) or len(rec.mechanisms) or len(rec.sequences)):
                out.append(ob)
        elif ob.type == kind:
            out.append(ob)
    return out


def draw(layout, context, note, kinds):
    """The 'needs X' line and a Select button when one candidate stands out. Returns None."""
    assert note in NOTES, note
    from boneforge.core.helpers import draw_wrapped
    col = layout.column(align=True)
    draw_wrapped(col, context, T(note), icon='INFO')
    select_button(col, context, kinds)


def select_button(layout, context, kinds):
    """A Select button for the first kind with exactly one candidate; nothing when it would be a guess."""
    col = layout
    for kind in kinds:
        found = _candidates(context, kind)
        if len(found) == 1:
            op = col.operator("boneforge.select_object", text=found[0].name,     # the name alone fits the shelf
                              icon='RESTRICT_SELECT_OFF', translate=False)
            op.name = found[0].name
            return                                        # several of a kind: never a guess; try the next kind


class BF_OT_select_object(Operator):
    bl_idname = "boneforge.select_object"
    bl_label = "Select Object"
    bl_description = "Make this object the only selected, active object so its tools appear"
    bl_options = {'REGISTER', 'UNDO'}
    name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        ob = context.scene.objects.get(self.name)
        if ob is None:
            self.report({'ERROR'}, f"'{self.name}' is not in this scene.")
            return {'CANCELLED'}
        if context.mode != 'OBJECT' and context.active_object is not None:
            bpy.ops.object.mode_set(mode='OBJECT')
        for other in context.selected_objects:
            other.select_set(False)
        ob.select_set(True)
        context.view_layer.objects.active = ob
        return {'FINISHED'}


def _active(context, *kinds):
    ob = getattr(context, "active_object", None)
    return ob is not None and ob.type in kinds


def _has_avatar(context):
    from boneforge.core import find_avatar_armature
    return find_avatar_armature(context) is not None


def _has_mech_rig(context):
    from boneforge.mechanisms import records
    return records.active_rig(context) is not None


def _has_armature(context):
    from boneforge.core.armature import active_armature
    return active_armature(context) is not None


def _mech_note(context):
    return "Add parts above to use this." if _active(context, 'MESH') else "Select a mesh or a mechanism rig to use this."


# section id -> (its requirement is met, what its sub-panels say while it is not)
GATES = {
    "BF_PT_sb_overview": (_has_avatar, "Select an avatar to use this."),
    "BF_PT_sb_skin": (lambda c: _active(c, 'ARMATURE', 'MESH'), "Select an armature or a mesh to use this."),
    "BF_PT_sb_animate": (lambda c: _active(c, 'ARMATURE'), "Select an armature to use this."),
    "BONEFORGE_PT_p2c_viseme_library": (lambda c: _active(c, 'ARMATURE'), "Select an armature to use this."),
    "BF_PT_mech": (_has_mech_rig, _mech_note),
    "CATS_PT_main": (_has_armature, "Select an armature to use this."),
    "BF_PT_sb_vrchat": (_has_armature, "Select an armature to use this."),   # its sections all need one
}


def _panels():
    out, todo = [], list(bpy.types.Panel.__subclasses__())
    while todo:
        c = todo.pop()
        out.append(c)
        todo.extend(c.__subclasses__())
    return [c for c in out if getattr(c, "is_registered", False)]


# Panels that say what they need themselves (needs.draw, with a Select button): never wrapped.
SELF_GATED = {
    "BF_PT_sb_retarget", "BF_PT_sb_rigify", "BF_PT_sb_correctives", "BONEFORGE_PT_p2b_delta_mush",
    "BONEFORGE_PT_p2b_proximity_wrap", "BONEFORGE_PT_profile_export", "BONEFORGE_PT_p2c_viseme_library",
    "CATS_PT_target_armature",             # the CATS Armature picker: how you choose the rig
}


def _wrap(cls, met, note):
    """While its section waits, ``cls`` shows with the section's note in place of its tools; otherwise as before."""
    orig_poll = getattr(cls, "poll", None) or (lambda context: True)     # bound to cls: survives the swap
    orig_draw = cls.draw

    def poll(_cls, context):
        return bool(orig_poll(context)) if met(context) else True

    def draw(self, context):
        if met(context):
            return orig_draw(self, context)
        from boneforge.core.helpers import draw_wrapped
        draw_wrapped(self.layout, context, T(note(context) if callable(note) else note), icon='INFO')

    cls.poll, cls.draw, cls._bc_needs_wrapped = classmethod(poll), draw, True


def keep_children_visible():
    """Show, don't hide, all the way down: every panel under a GATES section stays visible while it waits.

    Panels in SELF_GATED, and sections with their own gate, keep their own notes. Runs once every
    BoneCraft panel is registered. Patches the classes in place: Blender looks poll and draw up on the
    class at each redraw, and re-registering would move a panel below its siblings. Idempotent."""
    panels = _panels()
    kids = {}
    for k in panels:
        kids.setdefault(getattr(k, "bl_parent_id", ""), []).append(k)
    todo = []                                             # (panel, its section's gate)
    for sid, gate in GATES.items():
        stack = list(kids.get(sid, ()))
        while stack:
            k = stack.pop()
            if k.bl_idname in SELF_GATED or k.bl_idname in GATES:
                continue                                  # it explains itself, and so does its subtree
            todo.append((k, gate))
            stack.extend(kids.get(k.bl_idname, ()))
    for cls, gate in todo:
        if "_bc_needs_wrapped" not in cls.__dict__:
            _wrap(cls, *gate)


classes = (BF_OT_select_object,)
