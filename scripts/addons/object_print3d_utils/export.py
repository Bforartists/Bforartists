# SPDX-FileCopyrightText: 2013-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Export wrappers and integration with external tools.


import bpy

from bpy.app.translations import (
    pgettext_tip as tip_,
    pgettext_data as data_,
)


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
    export_data_layers = print_3d.use_data_layers

    # Create name 'export_path/blendname-objname'
    # add the filename component
    if bpy.data.is_saved:
        name = os.path.basename(bpy.data.filepath)
        name = os.path.splitext(name)[0]
    else:
        name = data_("untitled")

    # add object name
    import re
    name += "-" + re.sub(r'[\\/:*?"<>|]', "", obj.name)

    # first ensure the path is created
    if export_path:
        # this can fail with strange errors,
        # if the dir can't be made then we get an error later.
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
        filepath = bpy.path.ensure_ext(filepath, ".ply")
        ret = bpy.ops.wm.ply_export(
            filepath=filepath,
            ascii_format=False,
            apply_modifiers=True,
            export_selected_objects=True,
            global_scale=global_scale,
            export_normals=export_data_layers,
            export_uv=export_data_layers,
            export_colors="SRGB" if export_data_layers else "NONE",
        )
    elif export_format == 'X3D':
        addon_ensure("io_scene_x3d")
        filepath = bpy.path.ensure_ext(filepath, ".x3d")
        ret = bpy.ops.export_scene.x3d(
            filepath=filepath,
            use_mesh_modifiers=True,
            use_selection=True,
            global_scale=global_scale,
            path_mode=path_mode,
            use_normals=export_data_layers,
        )
    elif export_format == 'OBJ':
        filepath = bpy.path.ensure_ext(filepath, ".obj")
        ret = bpy.ops.wm.obj_export(
            filepath=filepath,
            apply_modifiers=True,
            export_selected_objects=True,
            global_scale=global_scale,
            path_mode=path_mode,
            export_normals=export_data_layers,
            export_uv=export_data_layers,
            export_materials=export_data_layers,
            export_colors=export_data_layers,
        )
    else:
        assert 0

    # for formats that don't support images
    if path_mode == 'COPY' and export_format in {'STL', 'PLY'}:
        image_copy_guess(filepath, context.selected_objects)

    if 'FINISHED' in ret:
        if report_cb is not None:
            report_cb({'INFO'}, tip_("Exported: {!r}").format(filepath))

        return True

    if report_cb is not None:
        report_cb({'ERROR'}, "Export failed")

    return False
