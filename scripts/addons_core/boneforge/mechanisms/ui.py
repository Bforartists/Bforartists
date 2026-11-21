# bonecraft/boneforge/mechanisms/ui.py
"""Mechanisms section of the BoneCraft sidebar tab (order 30), with four subsections (spec §5.1).

core/scene_tab_mirror.py copies it into Properties > Scene tab after Rig Builder;
core/properties_mirror.py leaves it out of Armature data. All drawing lives in
module functions, because the copies share only draw, draw_header and poll.
"""
import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import Menu, Operator, Panel, UIList

from boneforge.core.helpers import draw_helper, helpers_on
from boneforge.i18n import T
from boneforge.mechanisms import build, model, parts, records

_SPACE, _REGION, _CAT = 'VIEW_3D', 'UI', 'BoneCraft'
ICONS = {"HINGE": 'CON_ROTLIKE', "SLIDE": 'CON_LOCLIKE', "TELESCOPE": 'CON_SIZELIKE',
         "PISTON": 'CON_TRACKTO', "GEAR": 'PREFERENCES', "FOLLOW": 'CON_TRANSLIKE'}
WHAT = {
    "HINGE": "Turns a part around one axis, like a lid or a trigger.",
    "SLIDE": "Moves a part along one axis, like a bolt or a drawer.",
    "TELESCOPE": "Extends nested segments with one handle, like an antenna.",
    "PISTON": "Keeps a cylinder and a rod aimed at each other as their parts move.",
    "GEAR": "Turns one joint when another turns: gears, belts, rack and pinion.",
    "FOLLOW": "Moves one joint through a range while another moves through its range.",
}
ROLE_TEXT = {
    "copy": "adds the handle's value", "limit": "stops the joint at Min and Max",
    "handle_limit": "stops the handle (and its gizmo) at Min and Max",
    "def": "copies the moving bone; the mesh and engines use this bone",
    "gear": "turns this joint with the source joint", "follow": "maps the source range onto this joint",
    "aim_a": "points the cylinder at the rod", "aim_b": "points the rod at the cylinder",
    "stretch_b": "stretches the rod to reach the cylinder",
    "follow_a": "moves the cylinder with its aim bone", "follow_b": "moves the rod with its aim bone",
}
START_HINT = "Select a mesh to start, or an armature with mechanisms."
WM_FLAGS = ("bonecraft_mech_show_parts", "bonecraft_mech_show_links", "bonecraft_mech_show_seqs")


def _count(n, one, many=None):
    return f"{n} {one if n == 1 else (many or one + 's')}"


def _fold(layout, context, rec, flag, summary, foldable=True):
    """Sections 1-3 fold to one line once mechanisms exist. True = folded (the summary line was drawn).

    The flags live on the WindowManager, so nothing is saved into the file; a fresh session starts folded."""
    wm = context.window_manager
    if not len(rec.mechanisms) or not foldable or not hasattr(wm, flag):
        return False
    if getattr(wm, flag):
        layout.prop(wm, flag, text=summary, icon='TRIA_DOWN', emboss=False)
        return False
    layout.prop(wm, flag, text=summary, icon='TRIA_RIGHT', emboss=False)
    return True


def _role_text(role):
    if role in ROLE_TEXT:
        return ROLE_TEXT[role]
    if role.startswith("seg"):
        return "extends this segment by its share"
    if role.startswith("limit"):
        return "stops this segment at its share"
    if role[:1] == "s" and role[1:].isdigit():
        return f"plays step {int(role[1:]) + 1} of the Sequence"
    return role


def _side_tab_on(context):
    try:
        return bool(context.preferences.addons["boneforge"].preferences.show_tab_boneforge)
    except (AttributeError, KeyError):
        return True


def _rig(context):
    arm = records.active_rig(context)
    return arm, (arm.data.bonecraft_mech if arm is not None else None)


def _shown_part(context):
    """(arm, rec, part pg, from marker): the pivot marker's part while one is selected, else the list's part."""
    arm, rec = _rig(context)
    if rec is None:
        return arm, rec, None, False
    marker = context.active_object
    pid = marker.get(parts.PIVOT_PROP) if marker is not None else None
    if pid is not None:
        return arm, rec, records.find(arm.data, pid), True
    if 0 <= rec.active_part < len(rec.parts):
        return arm, rec, rec.parts[rec.active_part], False
    return arm, rec, None, False


def explain(arm, rid):
    """[(text, bone name)]: each constraint (and gear driver) BoneCraft built for ``rid``, and what it does."""
    out = []
    for pb in arm.pose.bones:
        for con in pb.constraints:
            if build.tag_of(con.name) == rid:
                role = con.name.split("·", 2)[2]
                kind = con.type.replace("_", " ").title()
                out.append((f"{pb.name} · {con.name} ({kind}): {_role_text(role)}", pb.name))
    m = records.find(arm.data, rid)
    if m is not None and getattr(m, "type", "") == "GEAR" and arm.animation_data is not None:
        target = records.find(arm.data, m.target)
        mch = build.bone_tags(arm).get((target.parts.split(",")[0], "MCH")) if target is not None else None
        for fc in arm.animation_data.drivers:
            if mch and fc.data_path.startswith(f'pose.bones["{mch}"]'):
                out.append((f"{mch} · driver, no Python: {fc.driver.expression}", mch))
    return out


# -- drawing ----------------------------------------------------------------

def draw_root(layout, context):
    arm, rec = _rig(context)
    if arm is None:
        ob = context.active_object
        if ob is not None and ob.type == 'MESH':
            draw_helper(layout, context, T("Turn hard-surface parts into a moving rig."),
                        T("Select the parts, then add them."))
            layout.operator("boneforge.mech_add_parts", icon='ADD')
        else:
            from boneforge.core.helpers import draw_wrapped
            draw_wrapped(layout, context, T(START_HINT), icon='INFO' if helpers_on(context) else 'NONE')
            from boneforge.core import needs              # show, don't hide: offer the one rig or mesh
            needs.select_button(layout, context, ("MECH_RIG", "MESH"))
        return
    if rec.last_error:
        layout.label(text=rec.last_error, icon='ERROR')
    draw_mode_line(layout, context, arm, rec)


def draw_mode_line(layout, context, arm, rec):
    """X1: one line names the single active mode, what it waits for, and its way out. Modes never stack."""
    from boneforge.mechanisms import guide
    if guide.ACTIVE:
        s = guide.ACTIVE[-1].session
        layout.label(text=T("Guided build: ") + s.guide.prompt(False) + ". " + T("Esc cancels."), icon='INFO')
        return True
    markers = parts.pivot_markers(arm)
    if markers:
        pg = records.find(arm.data, markers[0].get(parts.PIVOT_PROP))
        row = layout.row(align=True)
        row.label(text=T("Editing pivot: ") + (pg.name if pg is not None else "?"), icon='INFO')
        row.operator("boneforge.mech_apply_pivot", text=T("Apply")).marker = markers[0].name
        row.operator("boneforge.mech_cancel_pivot", text=T("Cancel"))
        return True
    if 0 <= rec.active_seq < len(rec.sequences):
        s = rec.sequences[rec.active_seq]
        if _at_end(arm, s.id):
            row = layout.row(align=True)
            row.label(text=T("Capture armed: pose the handles, then click Record Step ") + f"{len(s.steps) + 1}.", icon='REC')
            row.operator("boneforge.mech_cancel_capture", text=T("Cancel")).target = s.id
            return True
    return False


def _at_end(arm, sid):
    """True when the Sequence slider sits at its end (the armed half of Capture Step)."""
    try:
        return abs(build.get_value(arm, records.to_model(arm), sid) - 1.0) <= 1e-4
    except Exception:                                     # noqa: BLE001 - a half-built rig is never armed
        return False


def draw_parts(layout, context):
    arm, rec = _rig(context)
    if rec is None:                                   # copies can be drawn without their poll (Review Focus 5)
        return
    if _fold(layout, context, rec, "bonecraft_mech_show_parts", _count(len(rec.parts), T("part"))):
        return
    draw_helper(layout, context, T("A part moves as one solid block."), T("Parts ride on their parent part."))
    layout.operator("boneforge.mech_add_parts", icon='ADD')
    layout.template_list("BC_UL_mech_parts", "", rec, "parts", rec, "active_part", rows=3)
    _arm, _rec, p, from_marker = _shown_part(context)       # every control below acts on this part
    if p is None:
        return
    if from_marker:
        layout.label(text=T("Pivot marker for: ") + p.name, icon='INFO')
    if p.state == "MISSING_PART":
        box = layout.box()
        box.label(text=p.message or T("This part's mesh is missing."), icon='ERROR')
        row = box.row(align=True)
        row.operator("boneforge.mech_reassign", text=T("Reassign")).target = p.id
        row.operator("boneforge.mech_delete", text=T("Delete")).target = p.id
        return
    ob = records.part_object(p)
    if ob is not None and p.kind == "OBJECT" and parts.needs_apply(ob):
        box = layout.box()
        box.label(text=T("Unapplied rotation or scale tilts the axes."), icon='ERROR')
        box.operator("boneforge.mech_apply_transforms").target = p.id
    col = layout.column(align=True)
    col.prop(p, "name")
    parent = records.find(arm.data, p.parent)
    col.menu("BC_MT_mech_parent", text=T("Rides on: ") + (parent.name if parent is not None else T("the rig")))
    col.prop(p, "size")
    row = layout.row(align=True)
    if from_marker:
        row.operator("boneforge.mech_apply_pivot", icon='PIVOT_CURSOR')
        row.operator("boneforge.mech_cancel_pivot", text=T("Cancel"))
    else:
        row.operator("boneforge.mech_edit_pivot", icon='PIVOT_CURSOR').target = p.id
    layout.separator()
    layout.operator("boneforge.mech_delete", text=T("Delete Part"), icon='X').target = p.id


def draw_links(layout, context):
    arm, rec = _rig(context)
    if rec is None:                                   # copies can be drawn without their poll (Review Focus 5)
        return
    if _fold(layout, context, rec, "bonecraft_mech_show_links", _count(len(rec.mechanisms), T("joint & link"), T("joints & links"))):
        return
    draw_helper(layout, context, T("A joint says how a part may move; a link moves a part automatically."))
    row = layout.row(align=True)
    row.menu("BC_MT_mech_add_joint", text=T("Add Joint"), icon='ADD')
    row.menu("BC_MT_mech_add_link", text=T("Add Link"), icon='ADD')
    layout.template_list("BC_UL_mechs", "", rec, "mechanisms", rec, "active_mech", rows=4)
    if 0 <= rec.active_mech < len(rec.mechanisms):
        draw_settings(layout, context, arm, rec.mechanisms[rec.active_mech])


def draw_settings(layout, context, arm, m):
    """The selected mechanism's settings: only the fields its type uses (no UI bloat)."""
    box = layout.box()
    if m.state != "OK":
        col = box.column(align=True)
        col.label(text=m.message or m.state.replace("_", " ").title(), icon='ERROR')
        row = col.row(align=True)
        if m.state == "CHANGED_BY_HAND":
            row.operator("boneforge.mech_keep_mine").target = m.id
            row.operator("boneforge.mech_restore").target = m.id
        else:
            row.operator("boneforge.mech_delete").target = m.id
    col = box.column(align=True)
    for f in model.FIELDS[m.type]:
        if f == "axis":
            row = col.row(align=True)
            row.label(text=T("Axis"))
            for i, axis_name in enumerate(("X", "Y", "Z")):
                row.prop(m, "axis", index=i, text=axis_name)
        elif f in ("min", "max") and m.type == "HINGE":
            col.prop(m, f, text=T(f.title()) + " (°)")
        elif f == "shares":
            col.prop(m, f, text=T("Shares (empty = even)"))
        else:
            col.prop(m, f)
    if m.type in model.JOINT_TYPES:
        row = box.row(align=True)
        for which in ("MIN", "MAX"):
            op = row.operator("boneforge.mech_set_limit", text=T("Set " + which.title()))
            op.target, op.which = m.id, which
        sub = box.column(align=True)
        sub.label(text=T("Handle"))
        sub.prop(m, "handle_widget_ui")
        sub.prop(m, "handle_size")
        sub.prop(m, "handle_color_ui")
    if helpers_on(context):
        draw_note(box, context, arm, m)


def draw_note(layout, context, arm, m):
    """How this works in Blender: the constraints by name, what each does, and a Select button."""
    layout.prop(m, "show_note", icon='TRIA_DOWN' if m.show_note else 'TRIA_RIGHT', emboss=False)
    if not m.show_note:
        return
    col = layout.column(align=True)
    col.scale_y = 0.8
    for text, bone in explain(arm, m.id):
        row = col.row(align=True)
        row.label(text=text, icon='INFO')
        row.operator("boneforge.mech_select_bone", text="", icon='RESTRICT_SELECT_OFF').bone = bone


def draw_sequences(layout, context):
    arm, rec = _rig(context)
    if rec is None:                                   # copies can be drawn without their poll (Review Focus 5)
        return
    if _fold(layout, context, rec, "bonecraft_mech_show_seqs", _count(len(rec.sequences), T("sequence")),
             foldable=bool(len(rec.sequences))):
        return
    draw_helper(layout, context, T("A Sequence plays a transformation with one slider."),
                T("Pose the handles for each step, then Capture Step."))
    layout.operator("boneforge.mech_add_sequence", icon='ADD')
    if not len(rec.sequences):
        return
    layout.template_list("BC_UL_mech_sequences", "", rec, "sequences", rec, "active_seq", rows=2)
    if not (0 <= rec.active_seq < len(rec.sequences)):
        return
    s = rec.sequences[rec.active_seq]
    if s.state != "OK":                               # a held Sequence: Restore (Keep mine refuses Sequences)
        box = layout.box()
        box.label(text=s.message or s.state.replace("_", " ").title(), icon='ERROR')
        box.operator("boneforge.mech_restore").target = s.id
    armed = _at_end(arm, s.id)                        # Capture Step's two clicks, each named (spec M2)
    row = layout.row(align=True)
    row.operator("boneforge.mech_capture_step", icon='REC',
                 text=T("Record Step ") + str(len(s.steps) + 1) if armed else T("Move Slider to End")).target = s.id
    row.operator("boneforge.mech_test", text=T("Test"), icon='PLAY').target = s.id
    row.operator("boneforge.mech_detach", text="", icon='UNLINKED').target = s.id
    row.operator("boneforge.mech_delete", text="", icon='X').target = s.id
    if armed:
        layout.label(text=T("Pose the handles, then click Record Step ") + f"{len(s.steps) + 1}.", icon='REC')
        spans = [(st.start, st.end) for st in s.steps]
        over = model.overlapping_steps(spans, *model.step_window(spans))
        if over:
            layout.label(text=T("The new step overlaps step ") + ", ".join(str(i + 1) for i in over) + ".", icon='ERROR')
    names = {m.id: m.name for m in rec.mechanisms}
    for i, st in enumerate(s.steps):
        box = layout.box()
        top = box.row(align=True)
        top.label(text=f"{i + 1}. {names.get(st.target, T('missing joint'))}")
        op = top.operator("boneforge.mech_remove_step", text="", icon='X')
        op.target, op.index = s.id, i
        r = box.row(align=True)
        r.prop(st, "value")
        r.prop(st, "ease", text="")
        r = box.row(align=True)
        r.prop(st, "start")
        r.prop(st, "end")


def draw_controls(layout, context):
    arm, rec = _rig(context)
    if rec is None:                                   # copies can be drawn without their poll (Review Focus 5)
        return
    rig = records.to_model(arm)
    draw_helper(layout, context, T("Every joint and Sequence as one slider; the handle in the viewport moves with it."))
    col = layout.column(align=True)
    for cid, label in model.controls(rig):
        m = rig.mech(cid)
        if m is None:                                 # a Sequence: a 0-100% view of its handle, stored nowhere
            seq_pg = records.find(arm.data, cid)
            if seq_pg is not None:
                col.prop(seq_pg, "progress", text=label, translate=False, slider=True)
            continue
        pb = build.handle(arm, cid)
        if pb is None:
            continue
        if m.type == "HINGE":
            col.prop(pb, "rotation_euler", index=0, text=label, translate=False)
        else:
            col.prop(pb, "location", index=1, text=label, translate=False)
    layout.separator()
    layout.operator("boneforge.mech_save_form", icon='ADD').name = model.unique_name("Form", {f.name for f in rec.forms})
    if len(rec.forms):
        layout.template_list("BC_UL_mech_forms", "", rec, "forms", rec, "active_form", rows=2)
    if len(rec.forms) and 0 <= rec.active_form < len(rec.forms):
        f = rec.forms[rec.active_form]
        row = layout.row(align=True)
        row.operator("boneforge.mech_go_to_form", text=T("Go to Form")).name = f.name
        op = row.operator("boneforge.mech_go_to_form", text=T("Go and Key"), icon='KEY_HLT')
        op.name, op.insert_keys = f.name, True
        row.operator("boneforge.mech_remove_form", text="", icon='X').name = f.name
    if sum(1 for x in rec.parts if x.kind == "OBJECT") >= 2:    # export prep belongs after the build (spec M6)
        layout.separator()
        layout.operator("boneforge.mech_merge_vrchat", icon='JOIN')


def _draw_add_menu(layout, context, types):
    on = helpers_on(context)
    for t in types:
        layout.operator("boneforge.mech_guide", text=T(model.TYPE_LABEL[t]), icon=ICONS[t]).type = t
        if on:
            layout.label(text="      " + T(WHAT[t]))


# -- lists, menus, small UI operators ------------------------------------------

class BC_UL_mech_parts(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        kind = 'MESH_CUBE' if item.kind == "OBJECT" else 'MESH_DATA'
        layout.label(text=item.name, icon='ERROR' if item.state != "OK" else kind, translate=False)


class BC_UL_mechs(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.label(text=item.name, icon='ERROR' if item.state != "OK" else ICONS.get(item.type, 'DOT'), translate=False)
        row.operator("boneforge.mech_test", text="", icon='PLAY').target = item.id
        row.operator("boneforge.mech_detach", text="", icon='UNLINKED').target = item.id
        row.separator()
        row.operator("boneforge.mech_delete", text="", icon='X').target = item.id


class BC_UL_mech_sequences(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=False, icon='ERROR' if item.state != "OK" else 'NLA')


class BC_UL_mech_forms(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=False, icon='POSE_HLT')


class BC_MT_mech_add_joint(Menu):
    bl_idname = "BC_MT_mech_add_joint"
    bl_label = "Add Joint"

    def draw(self, context):
        _draw_add_menu(self.layout, context, model.JOINT_TYPES)


class BC_MT_mech_add_link(Menu):
    bl_idname = "BC_MT_mech_add_link"
    bl_label = "Add Link"

    def draw(self, context):
        _draw_add_menu(self.layout, context, model.LINK_TYPES)


class BC_MT_mech_parent(Menu):
    """The Rides on choices. A menu, not an enum: part names are the user's and are never translated (X3)."""
    bl_idname = "BC_MT_mech_parent"
    bl_label = "Rides On"

    def draw(self, context):
        arm, rec, shown, _ = _shown_part(context)
        self.layout.operator("boneforge.mech_set_parent", text=T("The rig")).parent = ""
        if shown is None:
            return
        for p in rec.parts:
            if p.id != shown.id:
                self.layout.operator("boneforge.mech_set_parent", text=p.name, translate=False).parent = p.id


class BC_OT_mech_set_parent(Operator):
    bl_idname = "boneforge.mech_set_parent"
    bl_label = "Rides On"
    bl_description = "Choose the part this part rides on"
    bl_options = {'REGISTER', 'UNDO'}
    parent: StringProperty(description="The parent part id; empty rides on the rig")

    @classmethod
    def poll(cls, context):
        return records.active_rig(context) is not None

    def execute(self, context):
        arm, rec, p, _ = _shown_part(context)                 # the part the panel shows
        if p is None:
            return {'CANCELLED'}
        old = p.parent
        p.parent = self.parent                                # edit hook rebuilds
        if rec.last_error:
            error = rec.last_error
            with records.quiet():
                p.parent = old
            build.rebuild(arm, {p.id})
            self.report({'ERROR'}, error)
            return {'CANCELLED'}
        return {'FINISHED'}


# -- panels -----------------------------------------------------------------------

class BF_PT_mech(Panel):
    bl_label = " "
    bl_idname = "BF_PT_mech"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CAT
    bl_order = 30

    def draw_header(self, context):
        self.layout.label(text=T("Mechanisms"))      # no icon: in the 132 px shelf an icon left no room for the title

    @classmethod
    def poll(cls, context):
        # Show, don't hide: with nothing to work on, draw_root says what to select.
        return _side_tab_on(context)

    def draw(self, context):
        draw_root(self.layout, context)


def _sub(idname, label, order, fn):
    def draw_header(self, context):
        self.layout.label(text=T(label))

    def draw(self, context):
        fn(self.layout, context)

    def poll(cls, context):
        return records.active_rig(context) is not None

    return type(idname, (Panel,), {
        "bl_label": " ", "bl_idname": idname, "bl_space_type": _SPACE, "bl_region_type": _REGION,
        "bl_category": _CAT, "bl_parent_id": "BF_PT_mech", "bl_order": order,
        "draw_header": draw_header, "draw": draw, "poll": classmethod(poll)})


BF_PT_mech_parts = _sub("BF_PT_mech_parts", "1. Parts", 1, draw_parts)
BF_PT_mech_links = _sub("BF_PT_mech_links", "2. Joints & Links", 2, draw_links)
BF_PT_mech_sequences = _sub("BF_PT_mech_sequences", "3. Sequences", 3, draw_sequences)
BF_PT_mech_controls = _sub("BF_PT_mech_controls", "4. Controls", 4, draw_controls)

classes = (BC_UL_mech_parts, BC_UL_mechs, BC_UL_mech_sequences, BC_UL_mech_forms,
           BC_MT_mech_add_joint, BC_MT_mech_add_link, BC_MT_mech_parent, BC_OT_mech_set_parent,
           BF_PT_mech, BF_PT_mech_parts, BF_PT_mech_links, BF_PT_mech_sequences, BF_PT_mech_controls)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    for flag in WM_FLAGS:                             # runtime only: never saved, so every session starts folded
        setattr(bpy.types.WindowManager, flag,
                BoolProperty(name="Show Section", default=False, options={'SKIP_SAVE'},
                             description="Show this section full controls"))


def unregister():
    for flag in WM_FLAGS:
        if hasattr(bpy.types.WindowManager, flag):
            delattr(bpy.types.WindowManager, flag)
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
