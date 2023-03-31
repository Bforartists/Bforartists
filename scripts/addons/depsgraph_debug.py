# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import (
        Operator,
        Panel,
        )
from bpy.props import (StringProperty, )

bl_info = {
    "name": "Dependency Graph Debug",
    "author": "Sergey Sharybin",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "description": "Various dependency graph debugging tools",
    "location": "Properties > View Layer > Dependency Graph",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Development",
}


def _get_depsgraph(context):
    scene = context.scene
    if bpy.app.version < (2, 80, 0,):
        return scene.depsgraph
    else:
        view_layer = context.view_layer
        return view_layer.depsgraph


###############################################################################
# Save data from depsgraph to a specified file.

class SCENE_OT_depsgraph_save_common:
    filepath: StringProperty(
        name="File Path",
        description="Filepath used for saving the file",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    def _getExtension(self, context):
        return ""

    @classmethod
    def poll(cls, context):
        depsgraph = _get_depsgraph(context)
        return depsgraph is not None

    def invoke(self, context, event):
        import os
        if not self.filepath:
            blend_filepath = context.blend_data.filepath
            if not blend_filepath:
                blend_filepath = "deg"
            else:
                blend_filepath = os.path.splitext(blend_filepath)[0]

            self.filepath = blend_filepath + self._getExtension(context)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        depsgraph = _get_depsgraph(context)
        if not self.performSave(context, depsgraph):
            return {'CANCELLED'}
        return {'FINISHED'}

    def performSave(self, context, depsgraph):
        pass


class SCENE_OT_depsgraph_relations_graphviz(
        Operator,
        SCENE_OT_depsgraph_save_common,
):
    bl_idname = "scene.depsgraph_relations_graphviz"
    bl_label = "Save Depsgraph"
    bl_description = "Save current scene's dependency graph to a graphviz file"

    def _getExtension(self, context):
        return ".dot"

    def performSave(self, context, depsgraph):
        import os
        basename, extension = os.path.splitext(self.filepath)
        depsgraph.debug_relations_graphviz(os.path.join(self.filepath, basename + ".dot"))
        return True


class SCENE_OT_depsgraph_stats_gnuplot(
        Operator,
        SCENE_OT_depsgraph_save_common,
):
    bl_idname = "scene.depsgraph_stats_gnuplot"
    bl_label = "Save Depsgraph Stats"
    bl_description = "Save current scene's evaluaiton stats to gnuplot file"

    def _getExtension(self, context):
        return ".plot"

    def performSave(self, context, depsgraph):
        depsgraph.debug_stats_gnuplot(self.filepath, "")
        return True


###############################################################################
# Visualize some depsgraph information as an image opening in image editor.

class SCENE_OT_depsgraph_image_common:
    def _getOrCreateImageForAbsPath(self, filepath):
        for image in bpy.data.images:
            if image.filepath == filepath:
                image.reload()
                return image
        return bpy.data.images.load(filepath, check_existing=True)

    def _findBestImageEditor(self, context, image):
        first_none_editor = None
        for area in context.screen.areas:
            if area.type != 'IMAGE_EDITOR':
                continue
            for space in area.spaces:
                if space.type != 'IMAGE_EDITOR':
                    continue
                if not space.image:
                    first_none_editor = space
                else:
                    if space.image == image:
                        return space
        return first_none_editor

    def _createTempFile(self, suffix):
        import os
        import tempfile
        fd, filepath = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        return filepath

    def _openImageInEditor(self, context, image_filepath):
        image = self._getOrCreateImageForAbsPath(image_filepath)
        editor = self._findBestImageEditor(context, image)
        if editor:
            editor.image = image

    def execute(self, context):
        depsgraph = _get_depsgraph(context)
        if not self.performSave(context, depsgraph):
            return {'CANCELLED'}
        return {'FINISHED'}

    def performSave(self, context, depsgraph):
        pass


class SCENE_OT_depsgraph_relations_image(Operator,
                                         SCENE_OT_depsgraph_image_common):
    bl_idname = "scene.depsgraph_relations_image"
    bl_label = "Depsgraph as Image"
    bl_description = "Create new image datablock from the dependency graph"

    def performSave(self, context, depsgraph):
        import os
        import subprocess
        # Create temporary file.
        dot_filepath = self._createTempFile(suffix=".dot")
        # Save dependency graph to graphviz file.
        depsgraph.debug_relations_graphviz(dot_filepath)
        # Convert graphviz to PNG image.
        png_filepath = os.path.join(bpy.app.tempdir, "depsgraph.png")
        command = ("dot", "-Tpng", dot_filepath, "-o", png_filepath)
        try:
            subprocess.run(command)
            self._openImageInEditor(context, png_filepath)
        except:
            self.report({'ERROR'}, "Error invoking dot command")
            return False
        finally:
            # Remove graphviz file.
            os.remove(dot_filepath)
        return True


class SCENE_OT_depsgraph_stats_image(Operator,
                                     SCENE_OT_depsgraph_image_common):
    bl_idname = "scene.depsgraph_stats_image"
    bl_label = "Depsgraph Stats as Image"
    bl_description = "Create new image datablock from the dependency graph " + \
                     "execution statistics"

    def performSave(self, context, depsgraph):
        import os
        import subprocess
        # Create temporary file.
        plot_filepath = self._createTempFile(suffix=".plot")
        png_filepath = os.path.join(bpy.app.tempdir, "depsgraph_stats.png")
        # Save dependency graph stats to gnuplot file.
        depsgraph.debug_stats_gnuplot(plot_filepath, png_filepath)
        # Convert graphviz to PNG image.
        command = ("gnuplot", plot_filepath)
        try:
            subprocess.run(command)
            self._openImageInEditor(context, png_filepath)
        except:
            self.report({'ERROR'}, "Error invoking gnuplot command")
            return False
        finally:
            # Remove graphviz file.
            os.remove(plot_filepath)
        return True


class SCENE_OT_depsgraph_relations_svg(Operator,
                                       SCENE_OT_depsgraph_image_common):
    bl_idname = "scene.depsgraph_relations_svg"
    bl_label = "Depsgraph as SVG in Browser"
    bl_description = "Create an SVG image from the dependency graph and open it in the web browser"

    def performSave(self, context, depsgraph):
        import os
        import subprocess
        import webbrowser
        # Create temporary file.
        dot_filepath = self._createTempFile(suffix=".dot")
        # Save dependency graph to graphviz file.
        depsgraph.debug_relations_graphviz(dot_filepath)
        # Convert graphviz to SVG image.
        svg_filepath = os.path.join(bpy.app.tempdir, "depsgraph.svg")
        command = ("dot", "-Tsvg", dot_filepath, "-o", svg_filepath)
        try:
            subprocess.run(command)
            webbrowser.open_new_tab("file://" + os.path.abspath(svg_filepath))
        except:
            self.report({'ERROR'}, "Error invoking dot command")
            return False
        finally:
            # Remove graphviz file.
            os.remove(dot_filepath)
        return True


###############################################################################
# Interface.


class SCENE_PT_depsgraph_common:
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        # Everything related on relations and graph topology.
        col.label(text="Relations:")
        row = col.row()
        row.operator("scene.depsgraph_relations_graphviz")
        row.operator("scene.depsgraph_relations_image")
        col.operator("scene.depsgraph_relations_svg")
        # Everything related on evaluaiton statistics.
        col.label(text="Statistics:")
        row = col.row()
        row.operator("scene.depsgraph_stats_gnuplot")
        row.operator("scene.depsgraph_stats_image")


class SCENE_PT_depsgraph(bpy.types.Panel, SCENE_PT_depsgraph_common):
    bl_label = "Dependency Graph"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (2, 80, 0,):
            return False
        depsgraph = _get_depsgraph(context)
        return depsgraph is not None


class RENDERLAYER_PT_depsgraph(bpy.types.Panel, SCENE_PT_depsgraph_common):
    bl_label = "Dependency Graph"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "view_layer"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if bpy.app.version < (2, 80, 0,):
            return False
        depsgraph = _get_depsgraph(context)
        return depsgraph is not None


def register():
    bpy.utils.register_class(SCENE_OT_depsgraph_relations_graphviz)
    bpy.utils.register_class(SCENE_OT_depsgraph_relations_image)
    bpy.utils.register_class(SCENE_OT_depsgraph_relations_svg)
    bpy.utils.register_class(SCENE_OT_depsgraph_stats_gnuplot)
    bpy.utils.register_class(SCENE_OT_depsgraph_stats_image)
    bpy.utils.register_class(SCENE_PT_depsgraph)
    bpy.utils.register_class(RENDERLAYER_PT_depsgraph)


def unregister():
    bpy.utils.unregister_class(SCENE_OT_depsgraph_relations_graphviz)
    bpy.utils.unregister_class(SCENE_OT_depsgraph_relations_image)
    bpy.utils.unregister_class(SCENE_OT_depsgraph_relations_svg)
    bpy.utils.unregister_class(SCENE_OT_depsgraph_stats_gnuplot)
    bpy.utils.unregister_class(SCENE_OT_depsgraph_stats_image)
    bpy.utils.unregister_class(SCENE_PT_depsgraph)
    bpy.utils.unregister_class(RENDERLAYER_PT_depsgraph)


if __name__ == "__main__":
    register()
