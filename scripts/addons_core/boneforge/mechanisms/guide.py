# bonecraft/boneforge/mechanisms/guide.py
"""Guided build: click parts in the viewport, then preview the mechanism working (spec §7.3).

GuideSession holds the logic and needs no window; BC_OT_mech_guide turns events
into session calls and draws outlines and numbered labels over the viewport.
"""
from types import SimpleNamespace

import blf
import bpy
import gpu
from bpy.props import BoolProperty, EnumProperty
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from boneforge.core.helpers import helpers_on
from boneforge.mechanisms import build, guide_steps, model, ops, planner, records, test_sweep

_OP_DEFAULTS = {"parts": "", "source": "", "target": "", "axis": "X", "gear_kind": "GEAR", "curve": False}
ACTIVE = []                                              # running guided builds, newest last (the panel's mode line reads it)
_BOX = ((0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7))


def _box(lo, hi):
    """Eight corners in Blender's bound_box order, so _BOX's edges join them."""
    return [Vector((x, y, z)) for x, y, z in ((lo.x, lo.y, lo.z), (lo.x, lo.y, hi.z), (lo.x, hi.y, hi.z), (lo.x, hi.y, lo.z),
                                               (hi.x, lo.y, lo.z), (hi.x, lo.y, hi.z), (hi.x, hi.y, hi.z), (hi.x, hi.y, lo.z))]


def part_corners(arm, pid):
    """World-space box corners of a part: its object's bounds, or its loose piece's vertices."""
    p = records.find(arm.data, pid)
    ob = records.part_object(p) if p is not None else None
    if ob is None:
        return []
    if p.kind == "OBJECT":
        pts = [Vector(c) for c in ob.bound_box]
    else:
        group = ob.vertex_groups.get(p.vertex_group)
        pts = [v.co for v in ob.data.vertices
               if group is not None and any(g.group == group.index and g.weight > 0.5 for g in v.groups)]
    if not pts:
        return []
    lo = Vector(tuple(min(q[i] for q in pts) for i in range(3)))
    hi = Vector(tuple(max(q[i] for q in pts) for i in range(3)))
    return [ob.matrix_world @ c for c in _box(lo, hi)]


def part_at(arm, obj, face_index):
    """The part id for a clicked object (and face, for loose pieces), or None."""
    if obj is None:
        return None
    rec = arm.data.bonecraft_mech
    for p in rec.parts:
        if p.kind == "OBJECT" and records.part_object(p) == obj:
            return p.id
    groups = {obj.vertex_groups[p.vertex_group].index: p.id for p in rec.parts
              if p.kind == "LOOSE" and obj.vertex_groups.get(p.vertex_group) and records.part_object(p) == obj}
    if not groups or face_index is None or face_index >= len(obj.data.polygons):
        return None
    best, weight = None, 0.0
    for vi in obj.data.polygons[face_index].vertices:
        for g in obj.data.vertices[vi].groups:
            if g.group in groups and g.weight > weight:
                best, weight = groups[g.group], g.weight
    return best


class GuideSession:
    """One guided build, independent of the window so it can be tested headless."""

    def __init__(self, context, arm, mech_type):
        self.context, self.arm = context, arm
        self.guide = guide_steps.Guide(mech_type)
        self.built = None
        self.sweep = None
        self.message = ""
        self.outlines = {}                               # part id -> (DEF bone, corners in that bone's space)
        self._parents = {}

    def _joint_type(self, pid):
        joint = planner.joint_for_part(records.to_model(self.arm), pid)
        return joint.type if joint is not None else None

    def pick(self, obj, face_index=None):
        pid = part_at(self.arm, obj, face_index)
        if pid is None:
            self.message = "That is not a part of this rig."
            return False
        self.message = self.guide.pick(pid, self._joint_type(pid))
        if not self.message:
            self._remember_outline(pid)
            self._build_when_done()
        return not self.message

    def _remember_outline(self, pid):
        """Keep the part's box in its DEF bone's space, so the outline follows the part when it moves."""
        bone = build.bone_tags(self.arm).get((pid, "DEF"))
        corners = part_corners(self.arm, pid)
        if bone is None or not corners:
            return
        p = records.find(self.arm.data, pid)
        if p.kind == "OBJECT":                           # the object's matrix already includes the pose
            frame = self.arm.matrix_world @ self.arm.pose.bones[bone].matrix
        else:                                            # vertex coordinates are the undeformed rest shape
            frame = self.arm.matrix_world @ self.arm.data.bones[bone].matrix_local
        inv = frame.inverted()
        self.outlines[pid] = (bone, [inv @ c for c in corners])

    def outline_now(self, pid):
        """The part's box corners in world space, through its DEF bone's current pose."""
        bone, local = self.outlines.get(pid, (None, []))
        pb = self.arm.pose.bones.get(bone) if bone else None
        if pb is None:
            return []
        frame = self.arm.matrix_world @ pb.matrix
        return [frame @ c for c in local]

    def key(self, name):
        """X / Y / Z / A choose the axis; ENTER ends a list, or answers "confirm" once built."""
        if name == "ENTER":
            if self.guide.done:
                return "confirm"
            self.message = self.guide.finish_list()
        elif name in ("X", "Y", "Z", "A"):
            self.message = self.guide.choose_axis("SELECTION" if name == "A" else name)
        if not self.message:
            self._build_when_done()
        return ""

    def _build_when_done(self):
        if not self.guide.done or self.built is not None:
            return
        cls_name, args = self.guide.op_args()
        self._parents = {p.id: p.parent for p in self.arm.data.bonecraft_mech.parts}
        before = records.taken_ids(self.arm.data)
        try:
            getattr(ops, cls_name).run(SimpleNamespace(**{**_OP_DEFAULTS, **args}), self.context, self.arm)
        except (build.BuildError, planner.PlanError) as exc:
            self.message = str(exc)
            self.guide.back()
            return
        self.built = next(iter(records.taken_ids(self.arm.data) - before))
        self._preview()

    def _preview(self):
        try:
            self.sweep = test_sweep.Sweep(self.arm, records.to_model(self.arm), self.built)
        except build.BuildError as exc:
            self.sweep, self.message = None, str(exc)    # e.g. a Piston nothing moves yet: no preview

    def tick(self):
        if self.sweep is not None and not self.sweep.step():
            self._preview()                              # loop the preview until Enter or Esc

    def _stop(self):
        if self.sweep is not None:
            self.sweep.stop()
            self.sweep = None

    def confirm(self):
        self._stop()
        return self.built

    def cancel(self):
        """Remove the built mechanism and put back the parents it changed; never raises. The first error is kept in message."""
        self.message = ""
        errors = []
        try:
            self._stop()
        except Exception as exc:                         # noqa: BLE001 - cancelling must always get to the cleanup below
            errors.append(str(exc))
        if self.built is not None:
            try:
                build.delete(self.arm, self.built)
            except Exception as exc:                     # noqa: BLE001 - build.delete can re-raise; keep restoring the parents
                errors.append(str(exc))
            try:
                changed = []
                with records.quiet():
                    for p in self.arm.data.bonecraft_mech.parts:
                        if p.id in self._parents and p.parent != self._parents[p.id]:
                            p.parent = self._parents[p.id]
                            changed.append(p.id)
                if changed:
                    build.rebuild(self.arm, set(changed))
            except Exception as exc:                     # noqa: BLE001
                errors.append(str(exc))
        self.message = errors[0] if errors else ""


def inside_region(region_width, region_height, x, y):
    """True when a region-relative point lies within the region (edges count as inside)."""
    return 0 <= x <= region_width and 0 <= y <= region_height


def target_area(context):
    """The 3D Viewport a guided build works in: the current area if it is one, else the screen's largest, or None."""
    area = context.area
    if area is not None and area.type == 'VIEW_3D':
        return area
    screen = context.screen
    views = [a for a in (screen.areas if screen is not None else ()) if a.type == 'VIEW_3D']
    return max(views, key=lambda a: a.width * a.height, default=None)


def window_region(area):
    """The area's WINDOW region (where the 3D view is drawn), or None."""
    return next((r for r in area.regions if r.type == 'WINDOW'), None) if area is not None else None


def region_coords(region, event):
    """The event's position relative to ``region``; window coordinates work from whichever region invoked us."""
    return event.mouse_x - region.x, event.mouse_y - region.y


def _click_in_viewport(area, region, event):
    """True when the click is inside the viewport's WINDOW region and not over one of the area's overlapping regions."""
    if region is None or not inside_region(region.width, region.height, *region_coords(region, event)):
        return False
    for other in (area.regions if area is not None else ()):
        if other.type != 'WINDOW' and other.width > 1 and other.height > 1                 and inside_region(other.width, other.height, event.mouse_x - other.x, event.mouse_y - other.y):
            return False                                 # the sidebar or toolbar can overlap the WINDOW region
    return True


def _ray(context, region, rv3d, event):
    co = region_coords(region, event)
    origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, co)
    direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, co)
    hit, _loc, _normal, index, obj, _mw = context.scene.ray_cast(context.evaluated_depsgraph_get(), origin, direction)
    return (obj.original, index) if hit else (None, None)


def _drawing_ours(op, area):
    """True when ``area`` (the one being drawn) is the viewport this guided build works in; others stay clean."""
    try:
        return area == op._area
    except ReferenceError:                               # the area was closed
        return False


def _draw_outlines(op, context):
    if not _drawing_ours(op, bpy.context.area):          # bpy.context: the handler's own context is the invoking editor's
        return
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    shader.uniform_float("color", (1.0, 0.6, 0.1, 1.0))
    for pid in op.session.guide.picked:                  # object parts and loose pieces alike
        corners = op.session.outline_now(pid)            # follows the part during the preview
        if len(corners) == 8:
            batch_for_shader(shader, 'LINES', {"pos": [corners[i] for edge in _BOX for i in edge]}).draw(shader)


def _draw_labels(op, context):
    if not _drawing_ours(op, bpy.context.area):          # bpy.context: the handler's own context is the invoking editor's
        return
    arm = op.session.arm
    for n, pid in enumerate(op.session.guide.picked, 1):
        p = records.find(arm.data, pid)
        if p is None:
            continue
        co = view3d_utils.location_3d_to_region_2d(op._region, op._rv3d, arm.matrix_world @ Vector(p.pivot))
        if co is not None:
            blf.size(0, 14)
            blf.position(0, co.x + 8, co.y + 8, 0)
            blf.draw(0, f"{n}. {p.name}")


class BC_OT_mech_guide(bpy.types.Operator):
    bl_idname = "boneforge.mech_guide"
    bl_label = "Add"
    bl_description = "Build a joint or link by clicking its parts in the viewport"
    bl_options = {'REGISTER', 'UNDO'}
    type: EnumProperty(description='Kind of joint or link to build', items=[(t, model.TYPE_LABEL[t], "") for t in model.TYPES])
    # set by the Build Mechanism tool: the click that starts the build is its first pick
    from_tool: BoolProperty(default=False, options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        if target_area(context) is None:                 # the sidebar, the Scene tab: any screen with a 3D Viewport
            cls.poll_message_set("Open a 3D Viewport first.")
            return False
        if records.active_rig(context) is None:
            cls.poll_message_set("Add parts first (Add Parts from Selection).")
            return False
        return True

    def invoke(self, context, event):
        area = target_area(context)
        region = window_region(area)
        if region is None or region.data is None:
            self.report({'ERROR'}, "Open a 3D Viewport first.")
            return {'CANCELLED'}
        first = None
        if self.from_tool:                               # a tool click: start only on a part, and pick it
            if not _click_in_viewport(area, region, event):
                return {'PASS_THROUGH'}
            first = _ray(context, region, region.data, event)
            if part_at(records.active_rig(context), *first) is None:
                return {'PASS_THROUGH'}                  # empty space or a non-part: the click is the viewport's
        self._area, self._region, self._rv3d = area, region, region.data     # clicks and labels use these, not context
        self.session = GuideSession(context, records.active_rig(context), self.type)
        self._handles = (
            bpy.types.SpaceView3D.draw_handler_add(_draw_outlines, (self, context), 'WINDOW', 'POST_VIEW'),
            bpy.types.SpaceView3D.draw_handler_add(_draw_labels, (self, context), 'WINDOW', 'POST_PIXEL'),
        )
        self._timer = context.window_manager.event_timer_add(1.0 / 24.0, window=context.window)
        context.window_manager.modal_handler_add(self)
        self._hover = ""
        ACTIVE.append(self)
        if first is not None:
            self.session.pick(*first)
        if hasattr(context.window_manager, "bonecraft_mech_show_links"):
            context.window_manager.bonecraft_mech_show_links = True
        self._text(context)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        try:
            return self._handle(context, event)
        except Exception as exc:                         # noqa: BLE001 - never leave handlers, timer or header text behind
            self.session.cancel()
            self.report({'ERROR'}, f"Guided build stopped: {exc}")
            return self._end(context, {'CANCELLED'})

    def cancel(self, context):
        """Blender ends the modal (window closed, file loaded): remove the preview and everything this run added."""
        try:
            self.session.cancel()
        except Exception:                                # noqa: BLE001 - always get to the teardown
            pass
        self._end(context, {'CANCELLED'})

    def _handle(self, context, event):
        self._area.tag_redraw()
        if event.type == 'TIMER':
            self.session.tick()
            return {'RUNNING_MODAL'}
        if event.type == 'MOUSEMOVE':
            self._update_hover(context, event)
            return {'PASS_THROUGH'}
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} or event.type.startswith('NDOF')                 or event.type == 'INBETWEEN_MOUSEMOVE':
            return {'PASS_THROUGH'}
        if event.value != 'PRESS':
            return {'RUNNING_MODAL'}
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            self.session.cancel()
            return self._end(context, {'CANCELLED'})
        if event.type == 'LEFTMOUSE':
            if not _click_in_viewport(self._area, self._region, event):
                return {'PASS_THROUGH'}                  # a click in the sidebar, header or another editor is not a pick
            self.session.pick(*_ray(context, self._region, self._rv3d, event))
        elif event.type in {'X', 'Y', 'Z', 'A'}:
            self.session.key(event.type)
        elif event.type in {'RET', 'NUMPAD_ENTER'} and self.session.key("ENTER") == "confirm":
            self.session.confirm()
            return self._end(context, {'FINISHED'})
        self._text(context)
        return {'RUNNING_MODAL'}

    def _update_hover(self, context, event):
        """X2: name the part under the cursor before the click, while a click would pick a part."""
        g = self.session.guide
        ask = g.steps[g.i].kind if not g.done else ""
        hover = ""
        if ask in ("part", "parts") and _click_in_viewport(self._area, self._region, event):
            pid = part_at(self.session.arm, *_ray(context, self._region, self._rv3d, event))
            p = records.find(self.session.arm.data, pid) if pid is not None else None
            hover = p.name if p is not None else ""
        if hover != self._hover:
            self._hover = hover
            self._text(context)

    def _text(self, context):
        s = self.session
        g = s.guide
        ask = g.steps[g.i].kind if not g.done else ""
        names = {p.id: p.name for p in s.arm.data.bonecraft_mech.parts}
        picked = names.get(g.picked[-1], "") if g.picked and ask == "axis" else ""
        text = guide_steps.header_text(g.prompt(helpers_on(context)),
                                       hover=self._hover if ask in ("part", "parts") else "",
                                       picked=picked, message=s.message)
        self._area.header_text_set(text)
        context.workspace.status_text_set(text)

    def _end(self, context, result):
        if self in ACTIVE:
            ACTIVE.remove(self)
        for h in self._handles:
            try:
                bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
            except Exception:                            # noqa: BLE001 - keep tearing down
                pass
        try:
            context.window_manager.event_timer_remove(self._timer)
        except Exception:                                # noqa: BLE001
            pass
        try:
            self._area.header_text_set(None)
            self._area.tag_redraw()
        except Exception:                                # noqa: BLE001 - the area may have been closed
            pass
        if context.workspace is not None:
            context.workspace.status_text_set(None)
        return result


def register():
    bpy.utils.register_class(BC_OT_mech_guide)


def unregister():
    try:
        bpy.utils.unregister_class(BC_OT_mech_guide)
    except RuntimeError:
        pass
