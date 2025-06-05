# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2013-2023 Campbell Barton
# SPDX-FileContributor: Mikhail Rachinskiy

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
    props = scene.print_3d

    global_scale = unit.scale_length if (unit.system != "NONE" and props.use_scene_scale) else 1.0
    path_mode = "COPY" if props.use_copy_textures else "AUTO"
    export_path = bpy.path.abspath(props.export_path)
    obj = layer.objects.active

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

    if props.export_format == "STL":
        filepath = bpy.path.ensure_ext(filepath, ".stl")
        ret = bpy.ops.wm.stl_export(
            filepath=filepath,
            ascii_format=props.use_ascii_format,
            global_scale=global_scale,
            apply_modifiers=True,
            export_selected_objects=True,
        )
    elif props.export_format == "PLY":
        filepath = bpy.path.ensure_ext(filepath, ".ply")
        ret = bpy.ops.wm.ply_export(
            filepath=filepath,
            ascii_format=props.use_ascii_format,
            global_scale=global_scale,
            export_uv=props.use_uv,
            export_normals=props.use_normals,
            export_colors="SRGB" if props.use_colors else "NONE",
            apply_modifiers=True,
            export_selected_objects=True,
            export_attributes=False,
        )
    elif props.export_format == "OBJ":
        filepath = bpy.path.ensure_ext(filepath, ".obj")
        ret = bpy.ops.wm.obj_export(
            filepath=filepath,
            global_scale=global_scale,
            export_uv=props.use_uv,
            export_normals=props.use_normals,
            export_colors=props.use_colors,
            export_materials=props.use_copy_textures,
            path_mode=path_mode,
            apply_modifiers=True,
            export_selected_objects=True,
        )
    else:
        assert 0

    # for formats that don't support images
    if path_mode == "COPY" and props.export_format in {"STL", "PLY"}:
        image_copy_guess(filepath, context.selected_objects)

    if "FINISHED" in ret:
        if report_cb is not None:
            report_cb({"INFO"}, tip_("Exported: {!r}").format(filepath))

        return True

    if report_cb is not None:
        report_cb({"ERROR"}, "Export failed")

    return False
