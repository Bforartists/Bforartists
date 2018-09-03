bl_info = {
    "name": "Mesh Cache Tools",
    "author": "Oscurart",
    "version": (1, 0, 1),
    "blender": (2, 70, 0),
    "location": "Tools > Mesh Cache Tools",
    "description": "Tools for Management Mesh Cache Process",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Import-Export"}


import bpy
import os
import struct
from bpy_extras.io_utils import ImportHelper
from bpy.types import (
        Operator,
        Panel,
        PropertyGroup,
        AddonPreferences,
        )
from bpy.props import (
        BoolProperty,
        IntProperty,
        StringProperty,
        PointerProperty,
        CollectionProperty,
        )
from bpy.app.handlers import persistent


class OscurartMeshCacheModifiersSettings(PropertyGroup):
    array = BoolProperty(default=True)
    bevel = BoolProperty(default=True)
    boolean = BoolProperty(default=True)
    build = BoolProperty(default=True)
    decimate = BoolProperty(default=True)
    edge_split = BoolProperty(default=True)
    mask = BoolProperty(default=True)
    mirror = BoolProperty(default=True)
    multires = BoolProperty(default=True)
    remesh = BoolProperty(default=True)
    screw = BoolProperty(default=True)
    skin = BoolProperty(default=True)
    solidify = BoolProperty(default=True)
    subsurf = BoolProperty(default=True)
    triangulate = BoolProperty(default=True)
    wireframe = BoolProperty(default=True)
    cloth = BoolProperty(default=True)


# ----------------- AUTO LOAD PROXY

# bpy.context.scene.pc_auto_load_proxy.remove(0)
class CreaPropiedades(Operator):
    bl_idname = "scene.pc_auto_load_proxy_create"
    bl_label = "Create Auto Load PC Proxy List"

    def execute(self, context):
        for gr in bpy.data.groups:
            if gr.library is not None:
                i = bpy.context.scene.pc_auto_load_proxy.add()
                i.name = gr.name
                i.use_auto_load = False
        return {'FINISHED'}


class RemuevePropiedades(Operator):
    bl_idname = "scene.pc_auto_load_proxy_remove"
    bl_label = "Remove Auto Load PC Proxy List"

    def execute(self, context):
        for i in bpy.context.scene.pc_auto_load_proxy:
            bpy.context.scene.pc_auto_load_proxy.remove(0)
        return {'FINISHED'}


class OscurartMeshCacheSceneAutoLoad(PropertyGroup):
    name = StringProperty(
            name="GroupName",
            default=""
            )
    use_auto_load = BoolProperty(
            name="Bool",
            default=False
            )


@persistent
def CargaAutoLoadPC(dummy):
    for gr in bpy.context.scene.pc_auto_load_proxy:
        if gr.use_auto_load:
            for ob in bpy.data.groups[gr.name].objects:
                for MOD in ob.modifiers:
                    if MOD.type == "MESH_CACHE":
                        MOD.cache_format = "PC2"
                        MOD.forward_axis = "POS_Y"
                        MOD.up_axis = "POS_Z"
                        MOD.flip_axis = set(())
                        MOD.frame_start = bpy.context.scene.pc_pc2_start
                        abspath = os.path.abspath(bpy.path.abspath("//" + bpy.context.scene.pc_pc2_folder))
                        MOD.filepath = "%s/%s.pc2" % (abspath, ob.name)


bpy.app.handlers.load_post.append(CargaAutoLoadPC)


# - PANELS -

class View3DMCPanel():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'


class OscEPc2ExporterPanel(View3DMCPanel, Panel):
    bl_category = "Tools"
    bl_label = "Mesh Cache Tools"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.column(align=1)
        row.prop(scene, "pc_pc2_folder", text="Folder")
        row.operator("buttons.set_meshcache_folder", icon='FILESEL', text="Select Folder Path")
        row = layout.box().column(align=1)
        row.label("EXPORTER:")
        row.operator("group.linked_group_to_local", text="Linked To Local", icon="LINKED")
        row.operator("object.remove_subsurf_modifier", text="Remove Gen Modifiers", icon="MOD_SUBSURF")
        row.prop(scene.mesh_cache_tools_settings, "array", text="Array")
        row.prop(scene.mesh_cache_tools_settings, "bevel", text="Bevel")
        row.prop(scene.mesh_cache_tools_settings, "boolean", text="Boolean")
        row.prop(scene.mesh_cache_tools_settings, "build", text="Build")
        row.prop(scene.mesh_cache_tools_settings, "decimate", text="Decimate")
        row.prop(scene.mesh_cache_tools_settings, "edge_split", text="Edge Split")
        row.prop(scene.mesh_cache_tools_settings, "mask", text="Mask")
        row.prop(scene.mesh_cache_tools_settings, "mirror", text="Mirror")
        row.prop(scene.mesh_cache_tools_settings, "multires", text="Multires")
        row.prop(scene.mesh_cache_tools_settings, "remesh", text="Remesh")
        row.prop(scene.mesh_cache_tools_settings, "screw", text="Screw")
        row.prop(scene.mesh_cache_tools_settings, "skin", text="Skin")
        row.prop(scene.mesh_cache_tools_settings, "solidify", text="Solidify")
        row.prop(scene.mesh_cache_tools_settings, "subsurf", text="Subsurf")
        row.prop(scene.mesh_cache_tools_settings, "triangulate", text="Triangulate")
        row.prop(scene.mesh_cache_tools_settings, "wireframe", text="Wireframe")

        # row = layout.column(align=1)
        row.prop(scene, "pc_pc2_start", text="Frame Start")
        row.prop(scene, "pc_pc2_end", text="Frame End")
        row.prop(scene, "pc_pc2_exclude", text="Exclude Token:")
        row.prop_search(scene, "pc_pc2_group", bpy.data, "groups", text="")
        row.operator("export_shape.pc2_selection", text="Export!", icon="POSE_DATA")
        row.prop(scene, "pc_pc2_world_space", text="World Space")
        row = layout.box().column(align=1)
        row.label("IMPORTER:")
        row.operator("import_shape.pc2_selection", text="Import", icon="POSE_DATA")
        row.operator("object.modifier_mesh_cache_up", text="MC Top", icon="TRIA_UP")
        row = layout.box().column(align=1)
        row.label("PROXY AUTO LOAD:")
        row.operator("scene.pc_auto_load_proxy_create", text="Create List", icon="GROUP")
        row.operator("scene.pc_auto_load_proxy_remove", text="Remove List", icon="X")

        for i in scene.pc_auto_load_proxy:
            if bpy.data.groups[i.name].library is not None:
                row = layout.row()
                row.prop(bpy.data.groups[i.name], "name", text="")
                row.prop(i, "use_auto_load", text="")


def OscSetFolder(self, context, filepath):
    fp = filepath if os.path.isdir(filepath) else os.path.dirname(filepath)
    try:
        os.chdir(os.path.dirname(bpy.data.filepath))
    except Exception as e:
        self.report({'WARNING'}, "Folder could not be set: {}".format(e))
        return {'CANCELLED'}

    rfp = os.path.relpath(fp)
    for sc in bpy.data.scenes:
        sc.pc_pc2_folder = rfp
    return {'FINISHED'}


class OscMeshCacheButtonSet(Operator, ImportHelper):
    bl_idname = "buttons.set_meshcache_folder"
    bl_label = "Set Mesh Cache Folder"
    filename_ext = ".txt"

    def execute(self, context):
        return OscSetFolder(self, context, self.filepath)


def OscFuncExportPc2(self):
    start = bpy.context.scene.pc_pc2_start
    end = bpy.context.scene.pc_pc2_end
    folderpath = bpy.context.scene.pc_pc2_folder
    framerange = end - start

    for ob in bpy.data.groups[bpy.context.scene.pc_pc2_group].objects[:]:
        if any(token not in ob.name for token in bpy.context.scene.pc_pc2_exclude.split(",")):
            bpy.context.window_manager.progress_begin(0, 100)  # progressbar
            if ob.type == "MESH":
                with open("%s/%s.pc2" % (os.path.normpath(folderpath), ob.name), mode="wb") as file:
                    # header
                    headerFormat = '<12siiffi'
                    headerStr = struct.pack(headerFormat,
                             b'POINTCACHE2\0', 1, len(ob.data.vertices[:]), 0, 1.0, (end + 1) - start)
                    file.write(headerStr)
                    # bake
                    obmat = ob.matrix_world
                    for i, frame in enumerate(range(start, end + 1)):
                        print("Percentage of %s bake: %s " % (ob.name, i * 100 / framerange))
                        bpy.context.window_manager.progress_update(i * 100 / framerange)  # progressbarUpdate
                        bpy.context.scene.frame_set(frame)
                        me = bpy.data.meshes.new_from_object(
                                    scene=bpy.context.scene,
                                    object=ob,
                                    apply_modifiers=True,
                                    settings="RENDER",
                                    calc_tessface=True,
                                    calc_undeformed=False
                                    )
                        # rotate
                        if bpy.context.scene.pc_pc2_world_space:
                            me.transform(obmat)
                            me.calc_normals()
                        # create archive
                        for vert in me.vertices[:]:
                            file.write(struct.pack("<3f", *vert.co))
                        # drain mesh
                        bpy.data.meshes.remove(me)

                    print("%s Bake finished!" % (ob.name))

            bpy.context.window_manager.progress_end()  # progressBarClose
    print("Bake Totally Finished!")


class OscPc2ExporterBatch(Operator):
    bl_idname = "export_shape.pc2_selection"
    bl_label = "Export pc2 for selected Objects"
    bl_description = "Export pc2 for selected Objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return(bpy.context.scene.pc_pc2_group != "" and bpy.context.scene.pc_pc2_folder != 'Set me Please!')

    def execute(self, context):
        OscFuncExportPc2(self)
        return {'FINISHED'}


class OscRemoveSubsurf(Operator):
    bl_idname = "object.remove_subsurf_modifier"
    bl_label = "Remove Subdivision Surface Modifier"
    bl_description = "Remove Subdivision Surface Modifier"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return(bpy.context.scene.pc_pc2_group != "")

    def execute(self, context):
        GENERATE = [
                'MULTIRES', 'ARRAY', 'BEVEL', 'BOOLEAN', 'BUILD',
                'DECIMATE', 'MASK', 'MIRROR', 'REMESH', 'SCREW',
                'SKIN', 'SOLIDIFY', 'SUBSURF', 'TRIANGULATE'
                ]
        for OBJ in bpy.data.groups[bpy.context.scene.pc_pc2_group].objects[:]:
            for MOD in OBJ.modifiers[:]:
                if MOD.type in GENERATE:
                    if eval("bpy.context.scene.mesh_cache_tools_settings.%s" % (MOD.type.lower())):
                        OBJ.modifiers.remove(MOD)

        return {'FINISHED'}


class OscPc2iMporterBatch(Operator):
    bl_idname = "import_shape.pc2_selection"
    bl_label = "Import pc2 for selected Objects"
    bl_description = "Import pc2 for selected Objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return(bpy.context.scene.pc_pc2_folder != 'Set me Please!')

    def execute(self, context):
        for OBJ in bpy.context.selected_objects[:]:
            MOD = OBJ.modifiers.new("MeshCache", 'MESH_CACHE')
            MOD.filepath = "//%s%s%s.pc2" % (bpy.context.scene.pc_pc2_folder, os.sep, OBJ.name)
            MOD.cache_format = "PC2"
            MOD.forward_axis = "POS_Y"
            MOD.up_axis = "POS_Z"
            MOD.flip_axis = set(())
            MOD.frame_start = bpy.context.scene.pc_pc2_start

        return {'FINISHED'}


def OscLinkedGroupToLocal():
    try:
        ACTOBJ = bpy.context.active_object

        if not ACTOBJ.id_data.dupli_group:
            return False

        GROBJS = [ob for ob in ACTOBJ.id_data.dupli_group.objects[:] if ob.type == "MESH"]

        for ob in ACTOBJ.id_data.dupli_group.objects[:]:
            bpy.context.scene.objects.link(ob)
        NEWGROUP = bpy.data.groups.new("%s_CLEAN" % (ACTOBJ.name))
        bpy.context.scene.objects.unlink(ACTOBJ)
        NEWOBJ = []
        for ob in GROBJS:
            NEWGROUP.objects.link(ob)
            NEWOBJ.append(ob)
    except:
        return False

    return True


class OscGroupLinkedToLocal(Operator):
    bl_idname = "group.linked_group_to_local"
    bl_label = "Group Linked To Local"
    bl_description = "Group Linked To Local"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        group_check = OscLinkedGroupToLocal()
        if not group_check:
            self.report({'WARNING'},
                        "There is no objects to link or the object already linked. Operation Cancelled")
            return {'CANCELLED'}

        return {'FINISHED'}


class OscMeshCacheUp(Operator):
    bl_idname = "object.modifier_mesh_cache_up"
    bl_label = "Mesh Cache To Top"
    bl_description = "Send Mesh Cache Modifiers top"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type == "MESH")

    def execute(self, context):

        actob = bpy.context.scene.objects.active

        for ob in bpy.context.selected_objects[:]:
            bpy.context.scene.objects.active = ob
            for mod in ob.modifiers[:]:
                if mod.type == "MESH_CACHE":
                    for up in range(ob.modifiers.keys().index(mod.name)):
                        bpy.ops.object.modifier_move_up(modifier=mod.name)

        bpy.context.scene.objects.active = actob

        return {'FINISHED'}


# Add-ons Preferences Update Panel

# Define Panel classes for updating
panels = (
        OscEPc2ExporterPanel,
        )


def update_panel(self, context):
    message = "Mesh Cache Tools: Updating Panel locations has failed"
    try:
        for panel in panels:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)

        for panel in panels:
            panel.bl_category = context.user_preferences.addons[__name__].preferences.category
            bpy.utils.register_class(panel)

    except Exception as e:
        print("\n[{}]\n{}\n\nError:\n{}".format(__name__, message, e))
        pass


class OscurartMeshCacheToolsAddonPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    category = StringProperty(
            name="Category",
            description="Choose a name for the category of the panel",
            default="Tools",
            update=update_panel,
            )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column()
        col.label(text="Category:")
        col.prop(self, "category", text="")


classes = (
        OscurartMeshCacheModifiersSettings,
        OscGroupLinkedToLocal,
        OscMeshCacheButtonSet,
        OscMeshCacheUp,
        OscPc2ExporterBatch,
        OscPc2iMporterBatch,
        OscRemoveSubsurf,
        OscurartMeshCacheToolsAddonPreferences,
        RemuevePropiedades,
        OscurartMeshCacheSceneAutoLoad,
        CreaPropiedades,
        OscEPc2ExporterPanel,
        )


# Register

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    from bpy.types import Scene
    Scene.mesh_cache_tools_settings = PointerProperty(
                                            type=OscurartMeshCacheModifiersSettings
                                            )
    Scene.pc_auto_load_proxy = CollectionProperty(
                                            type=OscurartMeshCacheSceneAutoLoad
                                            )

    Scene.pc_pc2_rotx = BoolProperty(default=True, name="Rotx = 90")
    Scene.pc_pc2_world_space = BoolProperty(default=True, name="World Space")
    Scene.pc_pc2_modifiers = BoolProperty(default=True, name="Apply Modifiers")
    Scene.pc_pc2_subsurf = BoolProperty(default=True, name="Turn Off SubSurf")
    Scene.pc_pc2_start = IntProperty(default=0, name="Frame Start")
    Scene.pc_pc2_end = IntProperty(default=100, name="Frame End")
    Scene.pc_pc2_group = StringProperty()
    Scene.pc_pc2_folder = StringProperty(default="Set me Please!")
    Scene.pc_pc2_exclude = StringProperty(default="*")

    update_panel(None, bpy.context)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    from bpy.types import Scene
    del Scene.mesh_cache_tools_settings
    del Scene.pc_auto_load_proxy
    del Scene.pc_pc2_rotx
    del Scene.pc_pc2_world_space
    del Scene.pc_pc2_modifiers
    del Scene.pc_pc2_subsurf
    del Scene.pc_pc2_start
    del Scene.pc_pc2_end
    del Scene.pc_pc2_group
    del Scene.pc_pc2_folder
    del Scene.pc_pc2_exclude


if __name__ == "__main__":
    register()
