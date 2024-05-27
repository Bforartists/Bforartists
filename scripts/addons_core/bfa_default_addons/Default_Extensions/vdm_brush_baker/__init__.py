# SPDX-FileCopyrightText: 2023 Robin Hohnsbeen
#
# SPDX-License-Identifier: GPL-3.0-or-later

from mathutils import Vector
from datetime import datetime
from pathlib import Path
import os
import bpy
from . import bakematerial
import importlib
importlib.reload(bakematerial)

bl_info = {
    'name': 'VDM Brush Baker',
    'author': 'Robin Hohnsbeen',
    'description': 'Bake vector displacement brushes easily from a plane',
    'blender': (3, 5, 0),
    'version': (1, 0, 3),
    'location': 'Sculpt Mode: View3D > Sidebar > Tool Tab',
    'warning': '',
    'category': 'Baking',
    'doc_url': '{BLENDER_MANUAL_URL}/addons/baking/vdm_brush_baker.html'
}


class vdm_brush_baker_addon_data(bpy.types.PropertyGroup):
    draft_brush_name: bpy.props.StringProperty(
        name='Name',
        default='NewVDMBrush',
        description='The name that will be used for the brush and texture')
    render_resolution: bpy.props.EnumProperty(items={
        ('128', '128 px', 'Render with 128 x 128 pixels', 1),
        ('256', '256 px', 'Render with 256 x 256 pixels', 2),
        ('512', '512 px', 'Render with 512 x 512 pixels', 3),
        ('1024', '1024 px', 'Render with 1024 x 1024 pixels', 4),
        ('2048', '2048 px', 'Render with 2048 x 2048 pixels', 5),
    },
        default='512', name='Map Resolution')
    compression: bpy.props.EnumProperty(items={
        ('none', 'None', '', 1),
        ('zip', 'ZIP (lossless)', '', 2),
    },
        default='zip', name='Compression')
    color_depth: bpy.props.EnumProperty(items={
        ('16', '16', '', 1),
        ('32', '32', '', 2),
    },
        default='16',
        name='Color Depth',
        description='A color depth of 32 can give better results but leads to far bigger file sizes. 16 should be good if the sculpt doesn\'t extend "too far" from the original plane')
    render_samples: bpy.props.IntProperty(name='Render Samples',
                                          default=64,
                                          min=2,
                                          max=4096)


def get_addon_data() -> vdm_brush_baker_addon_data:
    return bpy.context.scene.VDMBrushBakerAddonData


def get_output_path(filename):
    save_path = bpy.path.abspath('/tmp')
    if bpy.data.is_saved:
        save_path = os.path.dirname(bpy.data.filepath)
    save_path = os.path.join(save_path, 'output_vdm', filename)

    if bpy.data.is_saved:
        return bpy.path.relpath(save_path)
    else:
        return save_path


class PT_VDMBaker(bpy.types.Panel):
    """
    The main panel of the add-on which contains a button to create a sculpting plane and a button to bake the vector displacement map.
    It also has settings for name (image, texture and brush at once), resolution, compression and color depth.
    """
    bl_label = 'VDM Brush Baker'
    bl_idname = 'VDM_PT_bake_tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        addon_data = get_addon_data()

        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.operator(create_sculpt_plane.bl_idname, icon='ADD')

        layout.separator()

        is_occupied, brush_name = get_new_brush_name()
        button_text = 'Overwrite VDM Brush' if is_occupied else 'Render and Create VDM Brush'

        createvdmlayout = layout.row()
        createvdmlayout.enabled = context.active_object is not None and context.active_object.type == 'MESH'
        createvdmlayout.operator(
            create_vdm_brush.bl_idname, text=button_text, icon='BRUSH_DATA')

        if is_occupied:
            layout.label(
                text='Name Taken: Brush will be overwritten.', icon='INFO')

        col = layout.column()
        col.alert = is_occupied
        col.prop(addon_data, 'draft_brush_name')

        settings_layout = layout.column(align=True)
        settings_layout.label(text='Settings')
        layout_box = settings_layout.box()

        col = layout_box.column()
        col.prop(addon_data, 'render_resolution')

        col = layout_box.column()
        col.prop(addon_data, 'compression')

        col = layout_box.column()
        col.prop(addon_data, 'color_depth')

        col = layout_box.column()
        col.prop(addon_data, 'render_samples')

        layout.separator()


def get_new_brush_name():
    addon_data = get_addon_data()

    is_name_occupied = False
    for custom_brush in bpy.data.brushes:
        if custom_brush.name == addon_data.draft_brush_name:
            is_name_occupied = True
            break

    if addon_data.draft_brush_name != '':
        return is_name_occupied, addon_data.draft_brush_name
    else:
        date = datetime.now()
        dateformat = date.strftime('%b-%d-%Y-%H-%M-%S')
        return False, f'vdm-{dateformat}'


class create_sculpt_plane(bpy.types.Operator):
    """
    Creates a grid with 128 vertices per side plus two multires subdivisions.
    It uses 'Preserve corners' so further subdivisions can be made while the corners of the grid stay pointy.
    """
    bl_idname = 'sculptplane.create'
    bl_label = 'Create Sculpting Plane'
    bl_description = 'Creates a plane with a multires modifier to sculpt on'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=128, y_subdivisions=128, size=2,
                                        enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        new_grid = bpy.context.active_object
        multires = new_grid.modifiers.new('MultiresVDM', type='MULTIRES')
        multires.boundary_smooth = 'PRESERVE_CORNERS'
        bpy.ops.object.multires_subdivide(
            modifier='MultiresVDM', mode='CATMULL_CLARK')
        bpy.ops.object.multires_subdivide(
            modifier='MultiresVDM', mode='CATMULL_CLARK')  # 512 vertices per one side

        return {'FINISHED'}


class create_vdm_brush(bpy.types.Operator):
    """
    This operator will bake a vector displacement map from the active object and create a texture and brush datablock.
    """
    bl_idname = 'vdmbrush.create'
    bl_label = 'Create vdm brush from plane'
    bl_description = 'Creates a vector displacement map from your sculpture and creates a brush with it'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        if context.active_object is None or context.active_object.type != 'MESH':
            return {'CANCELLED'}

        vdm_plane = context.active_object
        addon_data = get_addon_data()
        new_brush_name = addon_data.draft_brush_name
        reference_brush_name = addon_data.draft_brush_name

        is_occupied, brush_name = get_new_brush_name()
        if len(addon_data.draft_brush_name) == 0 or is_occupied:
            addon_data.draft_brush_name = brush_name

        # Saving user settings
        scene = context.scene
        default_render_engine = scene.render.engine
        default_view_transform = scene.view_settings.view_transform
        default_display_device = scene.display_settings.display_device
        default_file_format = scene.render.image_settings.file_format
        default_color_mode = scene.render.image_settings.color_mode
        default_codec = scene.render.image_settings.exr_codec
        default_denoise = scene.cycles.use_denoising
        default_compute_device = scene.cycles.device
        default_scene_samples = scene.cycles.samples
        default_plane_location = vdm_plane.location.copy()
        default_plane_rotation = vdm_plane.rotation_euler.copy()
        default_mode = bpy.context.object.mode

        bpy.ops.object.mode_set(mode='OBJECT')

        vdm_bake_material = bakematerial.get_vdm_bake_material()
        vdm_texture_image = None
        try:
            # Prepare baking
            scene.render.engine = 'CYCLES'
            scene.cycles.samples = addon_data.render_samples
            scene.cycles.use_denoising = False
            scene.cycles.device = 'GPU'

            old_image_name = f'{reference_brush_name}'
            if old_image_name in bpy.data.images:
                bpy.data.images[old_image_name].name = 'Old VDM texture'

                # Removing the image right away can cause a crash when sculpt mode is exited.
                # bpy.data.images.remove(bpy.data.images[old_image_name])

            vdm_plane.data.materials.clear()
            vdm_plane.data.materials.append(vdm_bake_material)
            vdm_plane.location = Vector([0, 0, 0])
            vdm_plane.rotation_euler = (0, 0, 0)

            vdm_texture_node = vdm_bake_material.node_tree.nodes['VDMTexture']
            render_resolution = int(addon_data.render_resolution)

            bpy.ops.object.select_all(action='DESELECT')
            vdm_plane.select_set(True)
            output_path = get_output_path(f'{new_brush_name}.exr')
            vdm_texture_image = bpy.data.images.new(
                name=new_brush_name, width=render_resolution, height=render_resolution, alpha=False, float_buffer=True)
            vdm_bake_material.node_tree.nodes.active = vdm_texture_node

            vdm_texture_image.filepath_raw = output_path

            scene.render.image_settings.file_format = 'OPEN_EXR'
            scene.render.image_settings.color_mode = 'RGB'
            scene.render.image_settings.exr_codec = 'NONE'
            if addon_data.compression == 'zip':
                scene.render.image_settings.exr_codec = 'ZIP'

            scene.render.image_settings.color_depth = addon_data.color_depth
            vdm_texture_image.use_half_precision = addon_data.color_depth == '16'

            vdm_texture_image.colorspace_settings.is_data = True
            vdm_texture_image.colorspace_settings.name = 'Non-Color'

            vdm_texture_node.image = vdm_texture_image
            vdm_texture_node.select = True

            # Bake
            bpy.ops.object.bake(type='EMIT')
            # save as render so we have more control over compression settings
            vdm_texture_image.save_render(
                filepath=bpy.path.abspath(output_path), scene=scene, quality=0)
            # Removes the dirty flag, so the image doesn't have to be saved again by the user.
            vdm_texture_image.pack()
            vdm_texture_image.unpack(method='REMOVE')

        except BaseException as Err:
            self.report({"ERROR"}, f"{Err}")

        finally:
            scene.render.image_settings.file_format = default_file_format
            scene.render.image_settings.color_mode = default_color_mode
            scene.render.image_settings.exr_codec = default_codec
            scene.cycles.samples = default_scene_samples
            scene.display_settings.display_device = default_display_device
            scene.view_settings.view_transform = default_view_transform
            scene.cycles.use_denoising = default_denoise
            scene.cycles.device = default_compute_device
            scene.render.engine = default_render_engine
            vdm_plane.data.materials.clear()
            vdm_plane.location = default_plane_location
            vdm_plane.rotation_euler = default_plane_rotation

        # Needs to be in sculpt mode to set 'AREA_PLANE' mapping on new brush.
        bpy.ops.object.mode_set(mode='SCULPT')

        # Texture
        vdm_texture: bpy.types.Texture = None
        if bpy.data.textures.find(reference_brush_name) != -1:
            vdm_texture = bpy.data.textures[reference_brush_name]
        else:
            vdm_texture = bpy.data.textures.new(
                name=new_brush_name, type='IMAGE')
        vdm_texture.extension = 'EXTEND'
        vdm_texture.image = vdm_texture_image
        vdm_texture.name = new_brush_name

        # Brush
        new_brush: bpy.types.Brush = None
        if bpy.data.brushes.find(reference_brush_name) != -1:
            new_brush = bpy.data.brushes[reference_brush_name]
            self.report({'INFO'}, f'Changed draw brush \'{new_brush.name}\'')
        else:
            new_brush = bpy.data.brushes.new(
                name=new_brush_name, mode='SCULPT')
            self.report(
                {'INFO'}, f'Created new draw brush \'{new_brush.name}\'')

        new_brush.texture = vdm_texture
        new_brush.texture_slot.map_mode = 'AREA_PLANE'
        new_brush.stroke_method = 'ANCHORED'
        new_brush.name = new_brush_name
        new_brush.use_color_as_displacement = True
        new_brush.strength = 1.0
        new_brush.hardness = 0.9

        bpy.ops.object.mode_set(mode = default_mode)

        if bpy.context.object.mode == 'SCULPT':
            context.tool_settings.sculpt.brush = new_brush

        return {'FINISHED'}


registered_classes = [
    PT_VDMBaker,
    vdm_brush_baker_addon_data,
    create_vdm_brush,
    create_sculpt_plane
]


def register():
    for registered_class in registered_classes:
        bpy.utils.register_class(registered_class)

    bpy.types.Scene.VDMBrushBakerAddonData = bpy.props.PointerProperty(
        type=vdm_brush_baker_addon_data)


def unregister():
    for registered_class in registered_classes:
        bpy.utils.unregister_class(registered_class)

    del bpy.types.Scene.VDMBrushBakerAddonData
