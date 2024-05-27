# SPDX-FileCopyrightText: 2018-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.7"
__date__ = "9 Sep 2022"

import random
from math import fabs

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty
import bmesh

from .. import common
from ..utils.bl_class_registry import BlClassRegistry
from ..utils.property_class_registry import PropertyClassRegistry
from ..utils import compatibility as compat

import gpu
from gpu_extras.batch import batch_for_shader


def _is_valid_context(context):
    # 'IMAGE_EDITOR' and 'VIEW_3D' space is allowed to execute.
    # If 'View_3D' space is not allowed, you can't find option in Tool-Shelf
    # after the execution
    if not common.is_valid_space(context, ['IMAGE_EDITOR', 'VIEW_3D']):
        return False

    objs = common.get_uv_editable_objects(context)
    if not objs:
        return False

    # only edit mode is allowed to execute
    if context.object.mode != 'EDIT':
        return False

    return True


def _update_uvinsp_info(context):
    sc = context.scene
    props = sc.muv_props.uv_inspection
    objs = common.get_uv_editable_objects(context)

    bm_to_obj = {}      # { Object: BMesh }
    bm_list = []
    uv_layer_list = []
    faces_list = []
    for obj in objs:
        bm = bmesh.from_edit_mesh(obj.data)
        if common.check_version(2, 73, 0) >= 0:
            bm.faces.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.verify()

        if context.tool_settings.use_uv_select_sync:
            sel_faces = [f for f in bm.faces]
        else:
            sel_faces = [f for f in bm.faces if f.select]
        bm_to_obj[bm] = obj
        bm_list.append(bm)
        uv_layer_list.append(uv_layer)
        faces_list.append(sel_faces)

    props.overlapped_info = common.get_overlapped_uv_info(
        bm_list, faces_list, uv_layer_list, sc.muv_uv_inspection_show_mode,
        sc.muv_uv_inspection_same_polygon_threshold)
    props.flipped_info = common.get_flipped_uv_info(
        bm_list, faces_list, uv_layer_list)

    if sc.muv_uv_inspection_display_in_v3d:
        props.overlapped_info_for_v3d = {}
        for info in props.overlapped_info:
            bm = info["subject_bmesh"]
            face = info["subject_face"]
            obj = bm_to_obj[bm]
            if obj not in props.overlapped_info_for_v3d:
                props.overlapped_info_for_v3d[obj] = []
            props.overlapped_info_for_v3d[obj].append(face.index)

        props.filpped_info_for_v3d = {}
        for info in props.flipped_info:
            bm = info["bmesh"]
            face = info["face"]
            obj = bm_to_obj[bm]
            if obj not in props.filpped_info_for_v3d:
                props.filpped_info_for_v3d[obj] = []
            props.filpped_info_for_v3d[obj].append(face.index)


@PropertyClassRegistry()
class _Properties:
    idname = "uv_inspection"

    @classmethod
    def init_props(cls, scene):
        class Props():
            overlapped_info = []
            flipped_info = []
            overlapped_info_for_v3d = {}    # { Object: [face_indices] }
            filpped_info_for_v3d = {}       # { Object: [face_indices] }

        scene.muv_props.uv_inspection = Props()

        def get_func(_):
            return MUV_OT_UVInspection_Render.is_running(bpy.context)

        def set_func(_, __):
            pass

        def update_func(_, __):
            bpy.ops.uv.muv_uv_inspection_render('INVOKE_REGION_WIN')

        scene.muv_uv_inspection_enabled = BoolProperty(
            name="UV Inspection Enabled",
            description="UV Inspection is enabled",
            default=False
        )
        scene.muv_uv_inspection_show = BoolProperty(
            name="UV Inspection Showed",
            description="UV Inspection is showed",
            default=False,
            get=get_func,
            set=set_func,
            update=update_func
        )
        scene.muv_uv_inspection_show_overlapped = BoolProperty(
            name="Overlapped",
            description="Show overlapped UVs",
            default=False
        )
        scene.muv_uv_inspection_show_flipped = BoolProperty(
            name="Flipped",
            description="Show flipped UVs",
            default=False
        )
        scene.muv_uv_inspection_display_in_v3d = BoolProperty(
            name="Display View3D",
            description="Display overlapped/flipped faces on View3D",
            default=True
        )
        scene.muv_uv_inspection_show_mode = EnumProperty(
            name="Mode",
            description="Show mode",
            items=[
                ('PART', "Part", "Show only overlapped/flipped part"),
                ('FACE', "Face", "Show overlapped/flipped face")
            ],
            default='PART'
        )
        scene.muv_uv_inspection_same_polygon_threshold = FloatProperty(
            name="Same Polygon Threshold",
            description="Threshold to distinguish same polygons",
            default=0.00001,
            min=0.00001,
            max=0.01,
            step=0.00001
        )

    @classmethod
    def del_props(cls, scene):
        del scene.muv_props.uv_inspection
        del scene.muv_uv_inspection_enabled
        del scene.muv_uv_inspection_show
        del scene.muv_uv_inspection_show_overlapped
        del scene.muv_uv_inspection_show_flipped
        del scene.muv_uv_inspection_display_in_v3d
        del scene.muv_uv_inspection_show_mode
        del scene.muv_uv_inspection_same_polygon_threshold


@BlClassRegistry()
class MUV_OT_UVInspection_Render(bpy.types.Operator):
    """
    Operation class: Render UV Inspection
    No operation (only rendering)
    """

    bl_idname = "uv.muv_uv_inspection_render"
    bl_description = "Render overlapped/flipped UVs"
    bl_label = "Overlapped/Flipped UV renderer"

    __handle = None
    __handle_v3d = None

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return False
        return _is_valid_context(context)

    @classmethod
    def is_running(cls, _):
        return 1 if cls.__handle else 0

    @classmethod
    def handle_add(cls, obj, context):
        sie = bpy.types.SpaceImageEditor
        cls.__handle = sie.draw_handler_add(
            MUV_OT_UVInspection_Render.draw, (obj, context),
            'WINDOW', 'POST_PIXEL')

        sv3d = bpy.types.SpaceView3D
        cls.__handle_v3d = sv3d.draw_handler_add(
            MUV_OT_UVInspection_Render.draw_v3d, (obj, context),
            'WINDOW', 'POST_VIEW')

    @classmethod
    def handle_remove(cls):
        if cls.__handle is not None:
            bpy.types.SpaceImageEditor.draw_handler_remove(
                cls.__handle, 'WINDOW')
            cls.__handle = None

        if cls.__handle_v3d is not None:
            bpy.types.SpaceView3D.draw_handler_remove(
                cls.__handle_v3d, 'WINDOW')

    @staticmethod
    def draw_v3d(_, context):
        sc = context.scene
        props = sc.muv_props.uv_inspection
        user_prefs = compat.get_user_preferences(context)
        prefs = user_prefs.addons["magic_uv"].preferences

        if not MUV_OT_UVInspection_Render.is_running(context):
            return

        if not sc.muv_uv_inspection_display_in_v3d:
            return

        # OpenGL configuration.
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('LESS_EQUAL')

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        shader.bind()

        # Render faces whose UV is overlapped.
        if sc.muv_uv_inspection_show_overlapped:
            shader.uniform_float("color", prefs.uv_inspection_overlapped_color_for_v3d)

            for obj, findices in props.overlapped_info_for_v3d.items():
                world_mat = obj.matrix_world
                bm = bmesh.from_edit_mesh(obj.data)

                for fidx in findices:
                    coords = [compat.matmul(world_mat, l.vert.co) for l in bm.faces[fidx].loops]
                    batch = batch_for_shader(shader, 'TRI_FAN', {"pos": coords})
                    batch.draw(shader)

        # Render faces whose UV is flipped.
        if sc.muv_uv_inspection_show_flipped:
            shader.uniform_float("color", prefs.uv_inspection_flipped_color_for_v3d)

            for obj, findices in props.filpped_info_for_v3d.items():
                world_mat = obj.matrix_world
                bm = bmesh.from_edit_mesh(obj.data)

                for fidx in findices:
                    coords = [compat.matmul(world_mat, l.vert.co) for l in bm.faces[fidx].loops]
                    batch = batch_for_shader(shader, 'TRI_FAN', {"pos": coords})
                    batch.draw(shader)

        gpu.state.depth_test_set('NONE')
        gpu.state.blend_set('NONE')

    @staticmethod
    def draw(_, context):
        sc = context.scene
        props = sc.muv_props.uv_inspection
        user_prefs = compat.get_user_preferences(context)
        prefs = user_prefs.addons["magic_uv"].preferences

        if not MUV_OT_UVInspection_Render.is_running(context):
            return

        # OpenGL configuration
        gpu.state.blend_set('ALPHA')

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        shader.bind()

        # render overlapped UV
        if sc.muv_uv_inspection_show_overlapped:
            shader.uniform_float("color", prefs.uv_inspection_overlapped_color)

            for info in props.overlapped_info:
                if sc.muv_uv_inspection_show_mode == 'PART':
                    for poly in info["polygons"]:
                        coords = [context.region.view2d.view_to_region(uv.x, uv.y, clip=False) for uv in poly]
                        batch = batch_for_shader(shader, 'TRI_FAN', {"pos": coords})
                        batch.draw(shader)

                elif sc.muv_uv_inspection_show_mode == 'FACE':
                    coords = [
                        context.region.view2d.view_to_region(
                            uv.x, uv.y, clip=False) for uv in info["subject_uvs"]]
                    batch = batch_for_shader(shader, 'TRI_FAN', {"pos": coords})
                    batch.draw(shader)

        # render flipped UV
        if sc.muv_uv_inspection_show_flipped:
            shader.uniform_float("color", prefs.uv_inspection_flipped_color)

            for info in props.flipped_info:
                if sc.muv_uv_inspection_show_mode == 'PART':
                    for poly in info["polygons"]:
                        coords = [context.region.view2d.view_to_region(uv.x, uv.y, clip=False) for uv in poly]
                        batch = batch_for_shader(shader, 'TRI_FAN', {"pos": coords})
                        batch.draw(shader)

                elif sc.muv_uv_inspection_show_mode == 'FACE':
                    coords = [context.region.view2d.view_to_region(uv.x, uv.y, clip=False) for uv in info["uvs"]]
                    batch = batch_for_shader(shader, 'TRI_FAN', {"pos": coords})
                    batch.draw(shader)

        gpu.state.blend_set('NONE')

    def invoke(self, context, _):
        if not MUV_OT_UVInspection_Render.is_running(context):
            _update_uvinsp_info(context)
            MUV_OT_UVInspection_Render.handle_add(self, context)
        else:
            MUV_OT_UVInspection_Render.handle_remove()

        if context.area:
            context.area.tag_redraw()

        return {'FINISHED'}


@BlClassRegistry()
class MUV_OT_UVInspection_Update(bpy.types.Operator):
    """
    Operation class: Update
    """

    bl_idname = "uv.muv_uv_inspection_update"
    bl_label = "Update UV Inspection"
    bl_description = "Update UV Inspection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        if not MUV_OT_UVInspection_Render.is_running(context):
            return False
        return _is_valid_context(context)

    def execute(self, context):
        _update_uvinsp_info(context)

        if context.area:
            context.area.tag_redraw()

        return {'FINISHED'}


@BlClassRegistry()
class MUV_OT_UVInspection_PaintUVIsland(bpy.types.Operator):
    """
    Operation class: Paint UV island with random color.
    """

    bl_idname = "uv.muv_uv_inspection_paint_uv_island"
    bl_label = "Paint UV Island"
    bl_description = "Paint UV island with random color"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # we can not get area/space/region from console
        if common.is_console_mode():
            return True
        return _is_valid_context(context)

    def _get_or_new_image(self, name, width, height):
        if name in bpy.data.images.keys():
            return bpy.data.images[name]
        return bpy.data.images.new(name, width, height)

    def _get_or_new_material(self, name):
        if name in bpy.data.materials.keys():
            return bpy.data.materials[name]
        return bpy.data.materials.new(name)

    def _get_or_new_texture(self, name):
        if name in bpy.data.textures.keys():
            return bpy.data.textures[name]
        return bpy.data.textures.new(name, 'IMAGE')

    def _get_override_context(self, context):
        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            return {'window': window, 'screen': screen,
                                    'area': area, 'region': region}
        return None

    def _create_unique_color(self, exist_colors, allowable=0.1):
        retry = 0
        while retry < 20:
            r = random.random()
            g = random.random()
            b = random.random()
            new_color = [r, g, b]
            for color in exist_colors:
                if ((fabs(new_color[0] - color[0]) < allowable) and
                        (fabs(new_color[1] - color[1]) < allowable) and
                        (fabs(new_color[2] - color[2]) < allowable)):
                    break
            else:
                return new_color
        return None

    def execute(self, context):
        selected_objs_orig = [o for o in bpy.data.objects
                              if compat.get_object_select(o)]
        active_obj_orig = compat.get_active_object(context)

        objs = common.get_uv_editable_objects(context)
        mode_orig = context.object.mode
        context_override = self._get_override_context(context)
        if context_override is None:
            self.report({'WARNING'}, "More than one 'VIEW_3D' area must exist")
            return {'CANCELLED'}

        for i, obj in enumerate(objs):
            # Select/Active only one object to paint.
            for o in objs:
                compat.set_object_select(o, False)
            compat.set_object_select(obj, True)
            compat.set_active_object(obj)

            # Setup material of drawing target.
            target_image = self._get_or_new_image(
                "MagicUV_PaintUVIsland_{}".format(i), 4096, 4096)
            target_mtrl = self._get_or_new_material(
                "MagicUV_PaintUVMaterial_{}".format(i))
            if compat.check_version(2, 80, 0) >= 0:
                target_mtrl.use_nodes = True
                output_node = next(n for n in target_mtrl.node_tree.nodes
                                   if n.type == "OUTPUT_MATERIAL")
                nodes_to_remove = [n for n in target_mtrl.node_tree.nodes
                                   if n != output_node]
                for n in nodes_to_remove:
                    target_mtrl.node_tree.nodes.remove(n)
                texture_node = \
                    target_mtrl.node_tree.nodes.new("ShaderNodeTexImage")
                texture_node.image = target_image
                target_mtrl.node_tree.links.new(output_node.inputs["Surface"],
                                                texture_node.outputs["Color"])
                obj.data.use_paint_mask = True

                # Apply material to object (all faces).
                found = False
                for mtrl_idx, mtrl_slot in enumerate(obj.material_slots):
                    if mtrl_slot.material == target_mtrl:
                        found = True
                        break
                if not found:
                    bpy.ops.object.material_slot_add()
                    mtrl_idx = len(obj.material_slots) - 1
                    obj.material_slots[mtrl_idx].material = target_mtrl
                bpy.ops.object.mode_set(mode='EDIT')
                bm = bmesh.from_edit_mesh(obj.data)
                bm.faces.ensure_lookup_table()
                for f in bm.faces:
                    f.select = True
                bmesh.update_edit_mesh(obj.data)
                obj.active_material_index = mtrl_idx
                obj.active_material = target_mtrl
                bpy.ops.object.material_slot_assign()
            else:
                target_tex_slot = target_mtrl.texture_slots.add()
                target_tex = self._get_or_new_texture(
                    "MagicUV_PaintUVTexture_{}".format(i))
                target_tex_slot.texture = target_tex
                obj.data.use_paint_mask = True

                # Apply material to object (all faces).
                found = False
                for mtrl_idx, mtrl_slot in enumerate(obj.material_slots):
                    if mtrl_slot.material == target_mtrl:
                        found = True
                        break
                if not found:
                    bpy.ops.object.material_slot_add()
                    mtrl_idx = len(obj.material_slots) - 1
                    obj.material_slots[mtrl_idx].material = target_mtrl
                bpy.ops.object.mode_set(mode='EDIT')
                bm = bmesh.from_edit_mesh(obj.data)
                bm.faces.ensure_lookup_table()
                for f in bm.faces:
                    f.select = True
                bmesh.update_edit_mesh(obj.data)
                obj.active_material_index = mtrl_idx
                obj.active_material = target_mtrl
                bpy.ops.object.material_slot_assign()

            # Update active image in Image Editor.
            _, _, space = common.get_space(
                'IMAGE_EDITOR', 'WINDOW', 'IMAGE_EDITOR')
            if space is None:
                return {'CANCELLED'}
            space.image = target_image

            # Analyze island to make map between face and paint color.
            islands = common.get_island_info_from_bmesh(bm)
            color_to_faces = []
            for isl in islands:
                color = self._create_unique_color(
                    [c[0] for c in color_to_faces])
                if color is None:
                    self.report({'WARNING'},
                                "Failed to create color. Please try again")
                    return {'CANCELLED'}
                indices = [f["face"].index for f in isl["faces"]]
                color_to_faces.append((color, indices))

            for cf in color_to_faces:
                # Update selection information.
                bpy.ops.object.mode_set(mode='EDIT')
                bm = bmesh.from_edit_mesh(obj.data)
                bm.faces.ensure_lookup_table()
                for f in bm.faces:
                    f.select = False
                for fidx in cf[1]:
                    bm.faces[fidx].select = True
                bmesh.update_edit_mesh(obj.data)
                bpy.ops.object.mode_set(mode='OBJECT')

                # Update brush color.
                bpy.data.brushes["Fill"].color = cf[0]

                # Paint.
                bpy.ops.object.mode_set(mode='TEXTURE_PAINT')
                if compat.check_version(2, 80, 0) >= 0:
                    with context.temp_override(**context_override):
                        bpy.ops.paint.brush_select(image_tool='FILL')
                else:
                    paint_settings = \
                        bpy.data.scenes['Scene'].tool_settings.image_paint
                    paint_mode_orig = paint_settings.mode
                    paint_canvas_orig = paint_settings.canvas
                    paint_settings.mode = 'IMAGE'
                    paint_settings.canvas = target_image
                    with context.temp_override(**context_override):
                        bpy.ops.paint.brush_select(texture_paint_tool='FILL')

                with context.temp_override(**context_override):
                    bpy.ops.paint.image_paint(stroke=[{
                        "name": "",
                        "location": (0, 0, 0),
                        "mouse": (0, 0),
                        "mouse_event":  (0.0, 0.0),
                        "size": 0,
                        "pressure": 0,
                        "pen_flip": False,
                        "time": 0,
                        "is_start": False,
                        "x_tilt": 0.0,
                        "y_tilt": 0.0,
                    }])

                if compat.check_version(2, 80, 0) < 0:
                    paint_settings.mode = paint_mode_orig
                    paint_settings.canvas = paint_canvas_orig

        for obj in selected_objs_orig:
            compat.set_object_select(obj, True)
        compat.set_active_object(active_obj_orig)

        bpy.ops.object.mode_set(mode=mode_orig)

        return {'FINISHED'}
