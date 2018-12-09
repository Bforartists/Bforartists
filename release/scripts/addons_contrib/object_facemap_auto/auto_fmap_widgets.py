# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

'''
Face map manipulator:

- Automatic face-map to bone/shape mapping, so tweaking a face-map edits the underlying bone or shape
  by matching names.
- Bones will: Translates, Rotates, Scales (in that order based on locks)
- Face-map selection can be used.
- Transforming multiple face maps at once works (with selection).
- Alt-G/R/S can be used to clear face-map transformation.
- Dot-key can be used for view selected face-maps.
- Face-map names can store key-values, formatted:
  "some_name;foo=bar;baz=spam".
  Currently this is used to set the face-map action if it cant be usefully guessed from locks.
  eg "Bone;action=scale".
- Shapes simply change their influence.
- Face-map colors from bone groups are used when available.
- Supports precision (Shift) and increment snap (Ctrl).
- Keyframes after each edit, regardless of auto-key setting (unless its canceled).
  Note: I did this because there is no easy way to manually key - if you don't want the keyframe you can undo :)
'''

import bpy

from bpy.types import (
    GizmoGroup,
    Gizmo,

    PoseBone,
    ShapeKey,
)


# USE_VERBOSE = True
from . import (
    USE_VERBOSE,
    USE_RELOAD,
)


# -----------------------------------------------------------------------------
# Utility functions

def object_armatures(ob):
    for mod in ob.modifiers:
        if mod.type == 'ARMATURE':
            if mod.show_viewport:
                ob_arm = mod.object
                if ob_arm is not None:
                    yield ob_arm


def face_map_find_target(ob, fmap_name):
    """
    Returns pose-bone or shape-key.
    """
    # first pose-bone
    for ob_arm in object_armatures(ob):
        pbone = ob_arm.pose.bones.get(fmap_name)
        if pbone is not None:
            return pbone

    # second shape-keys
    if ob.type == 'MESH':
        ob_data = ob.data
        shape_keys = ob_data.shape_keys
        if shape_keys is not None:
            shape_key = ob_data.shape_keys.key_blocks.get(fmap_name)
            if shape_key is not None:
                return shape_key

    # can't find target
    return None


def pose_bone_get_color(pose_bone):
    bone_group = pose_bone.bone_group
    if bone_group is not None:
        return bone_group.colors.active
    else:
        return None


# -----------------------------------------------------------------------------
# Face-map gizmos

class AutoFaceMapWidget(Gizmo):
    bl_idname = "VIEW3D_WT_auto_facemap"

    __slots__ = (
        # Face-map this widget displays.
        "fmap",
        # Face-Map index is used for drawing.
        "fmap_index",
        # Mesh object the face map is attached to.
        "fmap_mesh_object",
        # Item this widget controls:
        # PoseBone or ShapeKey.
        "fmap_target",
        # list of rules, eg: ["action=rotate", ...]
        "fmap_target_rules",
        # Iterator to use while interacting.
        "_iter",
    )

    def draw(self, context):
        if USE_VERBOSE:
            print("(draw)")
        self.draw_preset_facemap(self.fmap_mesh_object, self.fmap_index)

    def select_refresh(self):
        fmap = getattr(self, "fmap", None)
        if fmap is not None:
            fmap.select = self.select

    def setup(self):
        if USE_VERBOSE:
            print("(setup)", self)

    def draw_select(self, context, select_id):
        if USE_VERBOSE:
            print("(draw_select)", self, context, select_id >> 8)
        self.draw_preset_facemap(self.fmap_mesh_object, self.fmap_index, select_id=select_id)

    def invoke(self, context, event):
        if USE_VERBOSE:
            print("(invoke)", self, event)

        # Avoid having to re-register to test logic
        from .auto_fmap_utils import import_reload_or_none
        auto_fmap_widgets_xform = import_reload_or_none(
            __package__ + "." + "auto_fmap_widgets_xform", reload=USE_RELOAD,
        )

        auto_fmap_widgets_xform.USE_VERBOSE = USE_VERBOSE

        # ob = context.object
        # fmap = ob.fmaps[self.fmap_index]
        # fmap_target = fmap_find_target(ob, fmap)

        mpr_list = [self]
        for mpr in self.group.gizmos:
            if mpr is not self:
                if mpr.select:
                    mpr_list.append(mpr)

        self._iter = []

        self.group.is_modal = True

        for mpr in mpr_list:
            ob = mpr.fmap_mesh_object
            fmap_target = mpr.fmap_target
            fmap = mpr.fmap

            if isinstance(fmap_target, PoseBone):
                # try get from rules first
                action = mpr.fmap_target_rules.get("action")
                if action is None:
                    bone = fmap_target.bone
                    if (not (bone.use_connect and bone.parent)) and (not all(fmap_target.lock_location)):
                        action = "translate"
                    elif not all(fmap_target.lock_rotation):
                        action = "rotate"
                    elif not all(fmap_target.lock_scale):
                        action = "scale"
                    del bone

                # guess from pose
                if action == "translate":
                    mpr_iter = iter(auto_fmap_widgets_xform.widget_iter_pose_translate(
                        context, mpr, ob, fmap, fmap_target))
                elif action == "rotate":
                    mpr_iter = iter(auto_fmap_widgets_xform.widget_iter_pose_rotate(
                        context, mpr, ob, fmap, fmap_target))
                elif action == "scale":
                    mpr_iter = iter(auto_fmap_widgets_xform.widget_iter_pose_scale(
                        context, mpr, ob, fmap, fmap_target))
                elif action:
                    print("Warning: action %r not known!" % action)

            elif isinstance(fmap_target, ShapeKey):
                mpr_iter = iter(auto_fmap_widgets_xform.widget_iter_shapekey(
                    context, mpr, ob, fmap, fmap_target))

            if mpr_iter is None:
                mpr_iter = iter(auto_fmap_widgets_xform.widget_iter_template(
                    context, mpr, ob, fmap, fmap_target))

            # initialize
            mpr_iter.send(None)
            # invoke()
            mpr_iter.send(event)

            self._iter.append(mpr_iter)
        return {'RUNNING_MODAL'}

    def exit(self, context, cancel):
        self.group.is_modal = False
        # failed case
        if not self._iter:
            return

        if USE_VERBOSE:
            print("(exit)", self, cancel)

        # last event, StopIteration is expected!
        for mpr_iter in self._iter:
            try:
                mpr_iter.send((cancel, None))
            except StopIteration:
                continue  # expected state
            raise Exception("for some reason the iterator lives on!")
        if not cancel:
            bpy.ops.ed.undo_push(message="Tweak Gizmo")

    def modal(self, context, event, tweak):
        # failed case
        if not self._iter:
            return {'CANCELLED'}

        # iter prints
        for mpr_iter in self._iter:
            try:
                mpr_iter.send((event, tweak))
            except Exception:
                import traceback
                traceback.print_exc()
                # avoid flooding output
                # We might want to remove this from the list!
                # self._iter = None
        return {'RUNNING_MODAL'}


class AutoFaceMapWidgetGroup(GizmoGroup):
    bl_idname = "OBJECT_WGT_auto_facemap"
    bl_label = "Auto Face Map"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'DEPTH_3D', 'SELECT', 'PERSISTENT', 'SHOW_MODAL_ALL'}

    __slots__ = (
        # "widgets",
        # need some comparison
        "last_active_object",
        "is_modal",
    )

    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            return False
        ob = context.object
        return (ob and ob.type == 'MESH' and ob.face_maps)

    @staticmethod
    def mesh_objects_from_armature(ob, visible_mesh_objects):
        """
        Take a context and return all mesh objects we can face-map.
        """
        for ob_iter in visible_mesh_objects:
            if ob in object_armatures(ob_iter):
                yield ob_iter

    @staticmethod
    def mesh_objects_from_context(context):
        """
        Take a context and return all mesh objects we can face-map.
        """
        ob = context.object
        if ob is None:
            pass
        ob_type = ob.type
        visible_mesh_objects = [ob_iter for ob_iter in context.visible_objects if ob_iter.type == 'MESH']
        if ob_type == 'ARMATURE':
            yield from AutoFaceMapWidgetGroup.mesh_objects_from_armature(ob, visible_mesh_objects)
        elif ob_type == 'MESH':
            # Unlikely, but possible 2x armatures control the same meshes
            # so double check we dont add the same meshes twice.
            unique_objects = set()
            for ob_iter in object_armatures(ob):
                if ob_iter not in unique_objects:
                    yield from AutoFaceMapWidgetGroup.mesh_objects_from_armature(ob_iter, visible_mesh_objects)
                unique_objects.add(ob_iter)

    def setup_manipulator_from_facemap(self, fmap_mesh_object, fmap, i):
        color_fallback = 0.15, 0.62, 1.0

        # foo;bar;baz --> ("foo", "bar;baz")
        fmap_name = fmap.name
        fmap_name_strip, fmap_rules = fmap_name.partition(";")[::2]
        fmap_target = face_map_find_target(fmap_mesh_object, fmap_name_strip)

        if fmap_target is None:
            return None

        mpr = self.gizmos.new(AutoFaceMapWidget.bl_idname)
        mpr.fmap_index = i
        mpr.fmap = fmap
        mpr.fmap_mesh_object = fmap_mesh_object
        mpr.fmap_target = fmap_target

        # See 'select_refresh' which syncs back in the other direction.
        mpr.select = fmap.select

        # foo;bar=baz;bonzo=bingo --> {"bar": baz", "bonzo": bingo}
        mpr.fmap_target_rules = dict(
            item.partition("=")[::2] for item in fmap_rules
        )

        # XXX, we might want to have some way to extract a 'center' from a face-map
        # for now use the pose-bones location.
        if isinstance(fmap_target, PoseBone):
            mpr.matrix_basis = (fmap_target.id_data.matrix_world @ fmap_target.matrix).normalized()

        mpr.use_draw_hover = True
        mpr.use_draw_modal = True

        if isinstance(fmap_target, PoseBone):
            mpr.color = pose_bone_get_color(fmap_target) or color_fallback
        else:  # We could color shapes, for now not.
            mpr.color = color_fallback

        mpr.alpha = 0.5

        mpr.color_highlight = mpr.color
        mpr.alpha_highlight = 0.5
        return mpr

    def setup(self, context):
        self.is_modal = False

        # we could remove this,
        # for now ensure keymaps are added on setup
        self.evil_keymap_setup(context)

        is_update = hasattr(self, "last_active_object")

        # For weak sanity check - detects undo
        if is_update and (self.last_active_object != context.active_object):
            is_update = False
            self.gizmos.clear()

        self.last_active_object = context.active_object

        if not is_update:
            for fmap_mesh_object in self.mesh_objects_from_context(context):
                for (i, fmap) in enumerate(fmap_mesh_object.face_maps):
                    self.setup_manipulator_from_facemap(fmap_mesh_object, fmap, i)
        else:
            # first attempt simple update
            force_full_update = False
            mpr_iter_old = iter(self.gizmos)
            for fmap_mesh_object in self.mesh_objects_from_context(context):
                for (i, fmap) in enumerate(fmap_mesh_object.face_maps):
                    mpr_old = next(mpr_iter_old, None)
                    if (
                            (mpr_old is None) or
                            (mpr_old.fmap_mesh_object != fmap_mesh_object) or
                            (mpr_old.fmap != fmap)
                    ):
                        force_full_update = True
                        break
                    # else we will want to update the base matrix at least
                    # possibly colors
                    # but its not so important
            del mpr_iter_old

            if force_full_update:
                self.gizmos.clear()
                # same as above
                for fmap_mesh_object in self.mesh_objects_from_context(context):
                    for (i, fmap) in enumerate(fmap_mesh_object.face_maps):
                        self.setup_manipulator_from_facemap(fmap_mesh_object, fmap, i)

    def refresh(self, context):
        if self.is_modal:
            return
        # WEAK!
        self.setup(context)

    @classmethod
    def evil_keymap_setup(cls, context):
        # only once!
        if hasattr(cls, "_keymap_init"):
            return
        cls._keymap_init = True

        # TODO, lookup existing keys and use those.

        # in-place of bpy.ops.object.location_clear and friends.
        km = context.window_manager.keyconfigs.active.keymaps.get(cls.bl_idname)
        if km is None:
            return
        kmi = km.keymap_items.new('my_facemap.transform_clear', 'G', 'PRESS', alt=True)
        kmi.properties.clear_types = {'LOCATION'}
        kmi = km.keymap_items.new('my_facemap.transform_clear', 'R', 'PRESS', alt=True)
        kmi.properties.clear_types = {'ROTATION'}
        kmi = km.keymap_items.new('my_facemap.transform_clear', 'S', 'PRESS', alt=True)
        kmi.properties.clear_types = {'SCALE'}

        # in-place of bpy.ops.view3d.view_selected
        # km.keymap_items.new('my_facemap.view_selected', 'NUMPAD_PERIOD', 'PRESS')

    '''
    @classmethod
    def setup_keymap(cls, keyconfig):
        km = keyconfig.keymaps.new(name=cls.bl_label, space_type='VIEW_3D', region_type='WINDOW')
        # XXX add keymaps
        return km
    '''


classes = (
    AutoFaceMapWidget,
    AutoFaceMapWidgetGroup,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
