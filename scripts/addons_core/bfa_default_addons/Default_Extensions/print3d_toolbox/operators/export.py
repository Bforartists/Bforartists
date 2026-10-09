# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2013-2023 Campbell Barton
# SPDX-FileCopyrightText: 2016-2026 Mikhail Rachinskiy

# Export wrappers and integration with external tools.

from pathlib import Path

import bpy
from bpy.app.translations import pgettext_data as data_
from bpy.app.translations import pgettext_tip as tip_
from bpy.props import StringProperty
from bpy.types import Image, Material, Object, Operator


class EXPORT_SCENE_OT_export(Operator):
    bl_idname = "export_scene.print3d_export"
    bl_label = "Export"
    bl_description = "Export selected objects using settings below"
    bl_options = {"INTERNAL"}

    filepath: StringProperty(
        subtype="FILE_PATH",
        options={"SKIP_SAVE", "HIDDEN"},
    )

    def execute(self, context):
        from bpy.utils import units as unit_utils

        unit = context.scene.unit_settings
        props = context.scene.print3d_toolbox

        export_scale = unit_utils.to_value(unit_utils.systems.METRIC, unit_utils.categories.LENGTH, "1", str_ref_unit=props.export_unit_scale)
        scale_factor = unit.scale_length / export_scale

        global_scale = scale_factor if (unit.system != "NONE" and props.export_unit_scale != "m") else 1.0
        path_mode = "COPY" if props.use_copy_textures else "AUTO"
        filepath = bpy.path.ensure_ext(self.filepath, f".{props.export_format.lower()}")
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        options = {
            "filepath": filepath,
            "global_scale": global_scale,
            "apply_modifiers": True,
            "export_selected_objects": True,
        }

        if props.export_format == "STL":
            options["ascii_format"] = props.use_ascii_format
            if bpy.app.version >= (5, 2, 0):  # VER
                options["evaluation_mode"] = "DAG_EVAL_VIEWPORT"
            ret = bpy.ops.wm.stl_export(**options)
        elif props.export_format == "PLY":
            options |= {
                "ascii_format": props.use_ascii_format,
                "export_uv": props.use_uv,
                "export_normals": props.use_normals,
                "export_colors": "SRGB" if props.use_colors else "NONE",
                "export_attributes": False,
            }
            ret = bpy.ops.wm.ply_export(**options)
        elif props.export_format == "OBJ":
            options |= {
                "export_uv": props.use_uv,
                "export_normals": props.use_normals,
                "export_colors": props.use_colors,
                "export_materials": props.use_copy_textures,
                "path_mode": path_mode,
                "export_eval_mode": "DAG_EVAL_VIEWPORT",
            }
            ret = bpy.ops.wm.obj_export(**options)
        else:
            assert 0

        # for formats that don't support images
        if path_mode == "COPY" and props.export_format in {"STL", "PLY"}:
            _image_copy_guess(filepath, context.selected_objects)

        if "FINISHED" in ret:
            self.report({"INFO"}, tip_("Exported: {!r}").format(filepath))
            return {"FINISHED"}

        self.report({"ERROR"}, "Export failed")
        return {"CANCELLED"}

    def invoke(self, context, event):
        import re
        from pathlib import Path

        if not context.selected_objects:
            return {"CANCELLED"}

        props = context.scene.print3d_toolbox

        if context.object:
            ob = context.object
        else:
            ob = context.selected_objects[0]

        ob_name = re.sub(r'[\\/:*?"<>|]', "", ob.name)

        if bpy.data.is_saved:
            blend_name = Path(bpy.data.filepath).stem
        else:
            blend_name = data_("Untitled")

        filename = f"{blend_name}-{ob_name}.{props.export_format.lower()}"

        if bpy.data.is_saved or (props.export_path and not props.export_path.startswith("//")):
            self.filepath = str(Path(bpy.path.abspath(props.export_path)) / filename)
        else:
            self.filepath = str(Path.home() / filename)

            wm = context.window_manager
            wm.fileselect_add(self)

            return {"RUNNING_MODAL"}

        return self.execute(context)


def _image_get(mat: Material) -> Image | None:
    from bpy_extras import node_shader_utils

    if mat.use_nodes:
        mat_wrap = node_shader_utils.PrincipledBSDFWrapper(mat)
        base_color_tex = mat_wrap.base_color_texture
        if base_color_tex and base_color_tex.image:
            return base_color_tex.image


def _image_copy_guess(filepath: str, objects: list[Object]) -> None:
    image = None
    mats = set()

    for obj in objects:
        for slot in obj.material_slots:
            if slot.material:
                mats.add(slot.material)

    for mat in mats:
        image = _image_get(mat)
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
            shutil.copy(imagepath, imagepath_dst)
