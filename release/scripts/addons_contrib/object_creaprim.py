# ###### BEGIN GPL LICENSE BLOCK ######
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# If you have Internet access, you can find the license text at
# http://www.gnu.org/licenses/gpl.txt,
# if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# ###### END GPL LICENCE BLOCK ######


"""
CreaPrim does what it says. I takes the active object and turns it into an
Add Mesh addon. When you enable this, your custom object will be added to the
Add->Mesh menu.


Documentation

Go to User Preferences->Addons and enable the CreaPrim addon in the Object
section. The addon will show up in the 3dview properties panel.

First select your object or objects.
The name (in panel) will be set to the active object name.
Select "Apply transform" if you want transforms to be applied to the selected
objects. Modifiers will taken into account. You can always change this.
Just hit the button and the selected objects will be saved in your addons folder
as an Add Mesh addon with the name "add_mesh_XXXX.py" with XXXX being your
object name.  The addon will show up in User Preferences->Addons in the
Add Mesh section. Enable this addon et voila, your new custom primitive will
now show up in the Add Mesh menu.

REMARK - dont need to be admin anymore - saves to user scripts dir

ALSO - dont forget to Apply rotation and scale to have your object
show up correctly
"""

bl_info = {
    "name": "CreaPrim",
    "author": "Gert De Roost",
    "version": (0, 3, 11),
    "blender": (2, 64, 0),
    "location": "View3D > Object Tools",
    "description": "Create primitive addon",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Object"}


import bpy
import bmesh
import os


started = 0
oldname = ""


def test_data(obj):
    me = obj.data
    is_faces = bool(len(me.polygons) > 0)
    return is_faces


class CreaPrim(bpy.types.Operator):
    bl_idname = "object.creaprim"
    bl_label = "CreaPrim"
    bl_description = "Create a primitive add-on"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH' and context.mode == 'OBJECT')

    def invoke(self, context, event):

        global oldname, groupname, message

        scn = bpy.context.scene

        objlist = []
        for selobj in bpy.context.scene.objects:
            if selobj.select_get() and test_data(selobj) is True:
                objlist.append(selobj)

        if len(objlist) == 0:
            self.report({'WARNING'},
                        "Please select Mesh objects containing Polygons. Operation Cancelled")
            return {"CANCELLED"}

        try:
            direc = bpy.utils.script_paths()[1]
            scriptdir = 1
        except:
            direc = bpy.utils.script_paths()[0]
            scriptdir = 0

        if len(objlist) > 1:
            groupname = scn.Creaprim_Name
            groupname = groupname.replace(".", "")
            addondir = direc + os.sep + "addons" + os.sep + "add_mesh_" + groupname + os.sep
            if not os.path.exists(addondir):
                os.makedirs(addondir)
        else:
            groupname = scn.Creaprim_Name
            print(bpy.utils.script_paths())
            addondir = direc + os.sep + "addons" + os.sep
            print(addondir)
            if not os.path.exists(addondir):
                os.makedirs(addondir)

        actobj = bpy.context.active_object
        txtlist = []
        namelist = []
        for selobj in objlist:
            if len(objlist) == 1:
                objname = scn.Creaprim_Name
                objname = objname.replace(" ", "_")
            else:
                objname = selobj.name
                objname = objname.replace(".", "")
                objname = objname.replace(" ", "_")
                namelist.append(objname)
            mesh = selobj.to_mesh(scn, True, "PREVIEW")
            oldname = selobj.name
            scn.objects.active = selobj

            if scn.Creaprim_Apply:
                bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            txt = do_creaprim(self, mesh, objname, addondir)

            if txt == 0:
                return {'CANCELLED'}

            txtlist.append(txt)

        oldname = actobj.name
        scn.objects.active = actobj

        if len(txtlist) > 1:
            makeinit(txtlist, namelist, groupname, addondir)
            bpy.ops.wm.addon_enable(module="add_mesh_" + groupname)
        else:
            bpy.ops.wm.addon_enable(module="add_mesh_" + str.lower(objname))

        if scriptdir == 1:
            message = "Add Mesh addon " + groupname + " saved to user scripts directory."
        else:
            message = "Add Mesh addon " + groupname + " saved to main scripts directory."
        bpy.ops.creaprim.message('INVOKE_DEFAULT')

        return {'FINISHED'}


class MessageOperator(bpy.types.Operator):
    bl_idname = "creaprim.message"
    bl_label = "Saved"

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width=500, height=20)

    def draw(self, context):

        global groupname

        layout = self.layout
        row = layout.row()
        row.label(text='', icon="PLUGIN")
        row.label(message)


def panel_func(self, context):

    global started

    scn = bpy.context.scene

    self.layout.label(text="CreaPrim:")
    self.layout.operator("object.creaprim", text="Create primitive", icon='PLUGIN')
    self.layout.prop(scn, "Creaprim_Name")
    self.layout.prop(scn, "Creaprim_Apply")


classes = (
    CreaPrim,
    MessageOperator)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    #bpy.utils.register_module(__name__)
    bpy.types.Scene.Creaprim_Name = bpy.props.StringProperty(
            name="Name",
            description="Name for the primitive",
            maxlen=1024
            )
    bpy.types.Scene.Creaprim_Apply = bpy.props.BoolProperty(
            name="Apply transform",
            description="Apply transform to selected objects",
            default=False
            )
    #bpy.types.VIEW3D_PT_tools_object.append(panel_func)
    bpy.types.OBJECT_PT_context_object.append(panel_func)
    #bpy.app.handlers.scene_update_post.append(setname)
    bpy.app.handlers.depsgraph_update_post.append(setname)


def unregister():
    #bpy.utils.unregister_module(__name__)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    #bpy.types.VIEW3D_PT_tools_object.remove(panel_func)
    bpy.types.OBJECT_PT_context_object.remove(panel_func)
    #bpy.app.handlers.scene_update_post.remove(setname)
    bpy.app.handlers.depsgraph_update_post.remove(setname)
    del bpy.types.Scene.Creaprim_Name
    del bpy.types.Scene.Creaprim_Apply


if __name__ == "__main__":
    register()


def do_creaprim(self, mesh, objname, addondir):

    global message

    objname = objname.replace(".", "")
    objname = objname.replace(" ", "_")
    bm = bmesh.new()
    bm.from_mesh(mesh)

    try:
        txt = bpy.data.texts[str.lower("add_mesh_" + objname) + ".py"]
        txt.clear()
    except:
        txt = bpy.data.texts.new("add_mesh_" + str.lower(objname) + ".py")

    strlist = []
    strlist.append("# Script autogenerated by object_creaprim.py")
    strlist.append("\n")
    strlist.append("bl_info = {\n")
    strlist.append("    \"name\": \"" + objname + "\",\n")
    strlist.append("    \"author\": \"Gert De Roost\",\n")
    strlist.append("    \"version\": (1, 0, 0),\n")
    strlist.append("    \"blender\": (2, 65, 0),\n")
    strlist.append("    \"location\": \"Add > Mesh\",\n")
    strlist.append("    \"description\": \"Create " + objname + " primitive\",\n")
    strlist.append("    \"warning\": \"\",\n")
    strlist.append("    \"wiki_url\": \"\",\n")
    strlist.append("    \"tracker_url\": \"\",\n")
    strlist.append("    \"category\": \"Add Mesh\"}\n")
    strlist.append("\n")
    strlist.append("\n")
    strlist.append("import bpy\n")
    strlist.append("import bmesh\n")
    strlist.append("import math\n")
    strlist.append("from mathutils import *\n")
    strlist.append("\n")
    strlist.append("\n")
    strlist.append("class " + objname + "(bpy.types.Operator):\n")
    strlist.append("    bl_idname = \"mesh." + str.lower(objname) + "\"\n")
    strlist.append("    bl_label = \"" + objname + "\"\n")
    strlist.append("    bl_options = {\'REGISTER\', \'UNDO\'}\n")
    strlist.append("    bl_description = \"add " + objname + " primitive\"\n")
    strlist.append("\n")
    strlist.append("    def invoke(self, context, event):\n")
    strlist.append("\n")
    strlist.append("        mesh = bpy.data.meshes.new(name=\"" + objname + "\")\n")
    strlist.append("        obj = bpy.data.objects.new(name=\"" + objname + "\", object_data=mesh)\n")
    strlist.append("        collection = bpy.context.collection\n")
    strlist.append("        scene = bpy.context.scene\n")
    strlist.append("        collection.objects.link(obj)\n")
    strlist.append("        obj.location = scene.cursor_location\n")
    strlist.append("        bm = bmesh.new()\n")
    strlist.append("        bm.from_mesh(mesh)\n")
    strlist.append("\n")
    strlist.append("        idxlist = []\n")
    posn = 0
    strlist.append("        vertlist = [")
    for v in bm.verts:
        if posn > 0:
            strlist.append(", ")
        posn += 1
        strlist.append(str(v.co[:]))
    strlist.append("]\n")
    strlist.append("        for co in vertlist:\n")
    strlist.append("            v = bm.verts.new(co)\n")
    strlist.append("            bm.verts.index_update()\n")
    strlist.append("            idxlist.append(v.index)\n")
    posn = 0
    strlist.append("        edgelist = [")
    for e in bm.edges:
        if posn > 0:
            strlist.append(", ")
        posn += 1
        strlist.append("[" + str(e.verts[0].index) + ", " + str(e.verts[1].index) + "]")
    strlist.append("]\n")
    strlist.append("        for verts in edgelist:\n")
    strlist.append("            try:\n")
    strlist.append("                bm.edges.new((bm.verts[verts[0]], bm.verts[verts[1]]))\n")
    strlist.append("            except:\n")
    strlist.append("                pass\n")
    posn1 = 0
    strlist.append("        facelist = [(")
    for f in bm.faces:
        if posn1 > 0:
            strlist.append(", (")
        posn1 += 1
        posn2 = 0
        for v in f.verts:
            if posn2 > 0:
                strlist.append(", ")
            strlist.append(str(v.index))
            posn2 += 1
        strlist.append(")")
    strlist.append("]\n")
    strlist.append("        bm.verts.ensure_lookup_table()\n")
    strlist.append("        for verts in facelist:\n")
    strlist.append("            vlist = []\n")
    strlist.append("            for idx in verts:\n")
    strlist.append("                vlist.append(bm.verts[idxlist[idx]])\n")
    strlist.append("            try:\n")
    strlist.append("                bm.faces.new(vlist)\n")
    strlist.append("            except:\n")
    strlist.append("                pass\n")
    strlist.append("\n")
    strlist.append("        bm.to_mesh(mesh)\n")
    strlist.append("        mesh.update()\n")
    strlist.append("        bm.free()\n")
    strlist.append("        obj.rotation_quaternion = (Matrix.Rotation(math.radians(90), 3, \'X\').to_quaternion())\n")
    strlist.append("\n")
    strlist.append("        return {\'FINISHED\'}\n")

    strlist.append("\n")
    strlist.append("\n")
    strlist.append("def menu_item(self, context):\n")
    strlist.append("    self.layout.operator(" + objname + ".bl_idname, text=\"" + objname + "\", icon=\"PLUGIN\")\n")
    strlist.append("\n")
    strlist.append("\n")
    strlist.append("def register():\n")
    strlist.append("    bpy.utils.register_module(__name__)\n")
    strlist.append("    bpy.types.VIEW3D_MT_mesh_add.append(menu_item)\n")
    strlist.append("\n")
    strlist.append("\n")
    strlist.append("def unregister():\n")
    strlist.append("    bpy.utils.unregister_module(__name__)\n")
    strlist.append("    bpy.types.VIEW3D_MT_mesh_add.remove(menu_item)\n")
    strlist.append("\n")
    strlist.append("\n")
    strlist.append("if __name__ == \"__main__\":\n")
    strlist.append("    register()\n")
    endstring = ''.join(strlist)
    txt.write(endstring)

    try:
        fileobj = open(addondir + "add_mesh_" + str.lower(objname) + ".py", "w")
    except:
        message = "Permission problem - cant write file - run Blender as Administrator!"
        bpy.ops.creaprim.message('INVOKE_DEFAULT')
        return 0

    fileobj.write(endstring)
    fileobj.close()

    bm.free()

    return txt


def makeinit(txtlist, namelist, groupname, addondir):

    global message

    try:
        txt = bpy.data.texts["__init__.py"]
        txt.clear()
    except:
        txt = bpy.data.texts.new("__init__.py")

    strlist = []
    strlist.append("# Script autogenerated by object_creaprim.py")
    strlist.append("\n")
    strlist.append("bl_info = {\n")
    strlist.append("    \"name\": \"" + groupname + "\",\n")
    strlist.append("    \"author\": \"Gert De Roost\",\n")
    strlist.append("    \"version\": (1, 0, 0),\n")
    strlist.append("    \"blender\": (2, 65, 0),\n")
    strlist.append("    \"location\": \"Add > Mesh\",\n")
    strlist.append("    \"description\": \"Create " + groupname + " primitive group\",\n")
    strlist.append("    \"warning\": \"\",\n")
    strlist.append("    \"wiki_url\": \"\",\n")
    strlist.append("    \"tracker_url\": \"\",\n")
    strlist.append("    \"category\": \"Add Mesh\"}\n")
    strlist.append("\n")
    strlist.append("\n")
    strlist.append("if \"bpy\" in locals():\n")
    strlist.append("    import importlib\n")
    addonlist = []
    for txt in txtlist:
        name = txt.name.replace(".py", "")
        addonlist.append(name)
    for name in addonlist:
        strlist.append("    importlib.reload(" + name + ")\n")
    strlist.append("else:\n")
    for name in addonlist:
        strlist.append("    from . import " + name + "\n")
    strlist.append("\n")
    strlist.append("\n")
    strlist.append("import bpy\n")
    strlist.append("\n")
    strlist.append("\n")
    strlist.append("class VIEW3D_MT_mesh_" + str.lower(groupname) + "_add(bpy.types.Menu):\n")
    strlist.append("    bl_idname = \"VIEW3D_MT_mesh_" + str.lower(groupname) + "_add\"\n")
    strlist.append("    bl_label = \"" + groupname + "\"\n")
    strlist.append("\n")
    strlist.append("    def draw(self, context):\n")
    strlist.append("        layout = self.layout\n")

    for name in namelist:
        strlist.append("        layout.operator(\"mesh." + str.lower(name) + "\", text=\"" + name + "\")\n")
    strlist.append("\n")
    strlist.append("\n")
    strlist.append("def menu_item(self, context):\n")
    strlist.append("    self.layout.menu(\"VIEW3D_MT_mesh_" + str.lower(groupname) + "_add\", icon=\"PLUGIN\")\n")
    strlist.append("\n")
    strlist.append("\n")
    strlist.append("def register():\n")
    strlist.append("    bpy.utils.register_module(__name__)\n")
    strlist.append("    bpy.types.VIEW3D_MT_mesh_add.append(menu_item)\n")
    strlist.append("\n")
    strlist.append("\n")
    strlist.append("def unregister():\n")
    strlist.append("    bpy.utils.unregister_module(__name__)\n")
    strlist.append("    bpy.types.VIEW3D_MT_mesh_add.remove(menu_item)\n")
    strlist.append("\n")
    strlist.append("\n")
    strlist.append("if __name__ == \"__main__\":\n")
    strlist.append("    register()\n")
    endstring = ''.join(strlist)
    txt.write(endstring)

    try:
        fileobj = open(addondir + "__init__.py", "w")
    except:
        message = "Permission problem - cant write file - run Blender as Administrator!"
        bpy.ops.creaprim.message('INVOKE_DEFAULT')
        return 0

    fileobj.write(endstring)
    fileobj.close()


def setname(dummy):

    scn = bpy.context.scene
    oldname = scn.Creaprim_Name

    if bpy.context.active_object and bpy.context.active_object.name != oldname:

        scn.Creaprim_Name = bpy.context.active_object.name
