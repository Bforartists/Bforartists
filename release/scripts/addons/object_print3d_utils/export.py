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

# <pep8-80 compliant>

# Export wrappers and integration with external tools.


import bpy


def image_get(mat):
    from bpy_extras import node_shader_utils

    if mat.use_nodes:
        mat_wrap = node_shader_utils.PrincipledBSDFWrapper(mat)
        base_color_tex = mat_wrap.base_color_texture
        if base_color_tex and base_color_tex.image:
            return base_color_tex.image


def image_copy_guess(filepath, objects):
    # 'filepath' is the path we are writing to.
    image = None
    mats = set()

    for obj in objects:
        for slot in obj.material_slots:
            if slot.material:
                mats.add(slot.material)

    for mat in mats:
        image = image_get(mat)
        if image is not None:
            break

    if image is not None:
        import os
        import shutil

        imagepath = bpy.path.abspath(image.filepath, library=image.library)
        if os.path.exists(imagepath):
            filepath_noext = os.path.splitext(filepath)[0]
            ext = os.path.splitext(imagepath)[1]

            imagepath_dst = filepath_noext + ext
            print(f"copying texture: {imagepath!r} -> {imagepath_dst!r}")

            try:
                shutil.copy(imagepath, imagepath_dst)
            except:
                import traceback
                traceback.print_exc()


def write_mesh(context, report_cb):
    import os

    scene = context.scene
    layer = context.view_layer
    unit = scene.unit_settings
    print_3d = scene.print_3d

    export_format = print_3d.export_format
    global_scale = unit.scale_length if (unit.system != 'NONE' and print_3d.use_apply_scale) else 1.0
    path_mode = 'COPY' if print_3d.use_export_texture else 'AUTO'
    export_path = bpy.path.abspath(print_3d.export_path)
    obj = layer.objects.active

    # Create name 'export_path/blendname-objname'
    # add the filename component
    if bpy.data.is_saved:
        name = os.path.basename(bpy.data.filepath)
        name = os.path.splitext(name)[0]
    else:
        name = "untitled"

    # add object name
    name += f"-{bpy.path.clean_name(obj.name)}"

    # first ensure the path is created
    if export_path:
        # this can fail with strange errors,
        # if the dir cant be made then we get an error later.
        try:
            os.makedirs(export_path, exist_ok=True)
        except:
            import traceback
            traceback.print_exc()

    filepath = os.path.join(export_path, name)

    # ensure addon is enabled
    import addon_utils

    def addon_ensure(addon_id):
        # Enable the addon, dont change preferences.
        _default_state, loaded_state = addon_utils.check(addon_id)
        if not loaded_state:
            addon_utils.enable(addon_id, default_set=False)

    if export_format == 'STL':
        addon_ensure("io_mesh_stl")
        filepath = bpy.path.ensure_ext(filepath, ".stl")
        ret = bpy.ops.export_mesh.stl(
            filepath=filepath,
            ascii=False,
            use_mesh_modifiers=True,
            use_selection=True,
            global_scale=global_scale,
        )
    elif export_format == 'PLY':
        addon_ensure("io_mesh_ply")
        filepath = bpy.path.ensure_ext(filepath, ".ply")
        ret = bpy.ops.export_mesh.ply(
            filepath=filepath,
            use_mesh_modifiers=True,
            use_selection=True,
            global_scale=global_scale,
        )
    elif export_format == 'X3D':
        addon_ensure("io_scene_x3d")
        filepath = bpy.path.ensure_ext(filepath, ".x3d")
        ret = bpy.ops.export_scene.x3d(
            filepath=filepath,
            use_mesh_modifiers=True,
            use_selection=True,
            path_mode=path_mode,
            global_scale=global_scale,
        )
    elif export_format == 'OBJ':
        addon_ensure("io_scene_obj")
        filepath = bpy.path.ensure_ext(filepath, ".obj")
        ret = bpy.ops.export_scene.obj(
            filepath=filepath,
            use_mesh_modifiers=True,
            use_selection=True,
            path_mode=path_mode,
            global_scale=global_scale,
        )
    else:
        assert 0

    # for formats that don't support images
    if export_format in {'STL', 'PLY'}:
        if path_mode == 'COPY':
            image_copy_guess(filepath, context.selected_objects)

    if 'FINISHED' in ret:
        if report_cb is not None:
            report_cb({'INFO'}, f"Exported: {filepath!r}")

        return True

    if report_cb is not None:
        report_cb({'ERROR'}, "Export failed")

    return False
