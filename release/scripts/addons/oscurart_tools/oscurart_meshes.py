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

import bpy
from mathutils import Vector
from bpy.types import Operator
from bpy.props import (
        IntProperty,
        BoolProperty,
        FloatProperty,
        EnumProperty,
        )
import os
import bmesh
import time
import blf
from bpy_extras.view3d_utils import location_3d_to_region_2d
from random import uniform

C = bpy.context
D = bpy.data


# -----------------------------RECONST---------------------------

def defReconst(self, OFFSET):
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    bpy.context.tool_settings.mesh_select_mode = (True, True, True)
    ob = bpy.context.active_object
    bm = bmesh.from_edit_mesh(ob.data)
    bm.select_flush(False)
    for vertice in bm.verts[:]:
        if abs(vertice.co[0]) < OFFSET:
            vertice.co[0] = 0
    for vertice in bm.verts[:]:
        if vertice.co[0] < 0:
            bm.verts.remove(vertice)
            bmesh.update_edit_mesh(ob.data)
    mod = ob.modifiers.new("Mirror", "MIRROR")
    uv = ob.data.uv_textures.new(name="SYMMETRICAL")
    for v in bm.faces:
        v.select = 1
    bmesh.update_edit_mesh(ob.data)
    ob.data.uv_textures.active = ob.data.uv_textures['SYMMETRICAL']
    bpy.ops.uv.unwrap(
        method='ANGLE_BASED',
        fill_holes=True,
        correct_aspect=False,
        use_subsurf_data=0)
    bpy.ops.object.mode_set(mode="OBJECT", toggle=False)
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Mirror")
    bpy.ops.object.mode_set(mode="EDIT", toggle=False)
    bm = bmesh.from_edit_mesh(ob.data)
    bm.select_flush(0)
    uv = ob.data.uv_textures.new(name="ASYMMETRICAL")
    ob.data.uv_textures.active = ob.data.uv_textures['ASYMMETRICAL']
    bpy.ops.uv.unwrap(
        method='ANGLE_BASED',
        fill_holes=True,
        correct_aspect=False,
        use_subsurf_data=0)


class reConst(Operator):
    """Erase vertices below cero X position value and rebuilds the symmetry. """
    """It also creates two uv channels, one symmetrical and one asymmetrical"""
    bl_idname = "mesh.reconst_osc"
    bl_label = "ReConst Mesh"
    bl_options = {"REGISTER", "UNDO"}

    OFFSET = FloatProperty(
            name="Offset",
            default=0.001,
            min=-0,
            max=0.1
            )

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')

    def execute(self, context):
        defReconst(self, self.OFFSET)
        return {'FINISHED'}


# -----------------------------------SELECT LEFT---------------------

def side(self, nombre, offset):

    bpy.ops.object.mode_set(mode="EDIT", toggle=0)
    OBJECT = bpy.context.active_object
    ODATA = bmesh.from_edit_mesh(OBJECT.data)
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)
    for VERTICE in ODATA.verts[:]:
        VERTICE.select = False
    if nombre is False:
        for VERTICES in ODATA.verts[:]:
            if VERTICES.co[0] < (offset):
                VERTICES.select = 1
    else:
        for VERTICES in ODATA.verts[:]:
            if VERTICES.co[0] > (offset):
                VERTICES.select = 1
    ODATA.select_flush(False)
    bpy.ops.object.mode_set(mode="EDIT", toggle=0)


class SelectMenor(Operator):
    """Selects the vertex with an N position value on the X axis"""
    bl_idname = "mesh.select_side_osc"
    bl_label = "Select Side"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')

    side = BoolProperty(
            name="Greater than zero",
            default=False
            )
    offset = FloatProperty(
            name="Offset",
            default=0
            )

    def execute(self, context):

        side(self, self.side, self.offset)

        return {'FINISHED'}


# -------------------------RESYM VG----------------------------------


class rvg(Operator):
    bl_idname = "mesh.resym_vertex_weights_osc"
    bl_label = "Resym Vertex Weights"
    bl_description = ("Copies the symmetrical weight value of the vertices on the X axys\n"
                      "(It needs the XML map and the Active Object is not in Edit mode)")
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.mode != "EDIT"

    def execute(self, context):
        ob = bpy.context.object
        actgr = ob.vertex_groups.active if ob else None
        if not actgr:
            self.report({'WARNING'},
                        "Object doesn't have active Vertex groups. Operation Cancelled")
            return {"CANCELLED"}

        with open("%s_%s_SYM_TEMPLATE.xml" % (os.path.join(os.path.dirname(bpy.data.filepath),
                                              bpy.context.scene.name), bpy.context.object.name)) as file:
            actind = ob.vertex_groups.active_index
            ls = eval(file.read())
            wdict = {left: actgr.weight(right) for left, right in ls.items()
                     for group in ob.data.vertices[right].groups if group.group == actind}
            actgr.remove(
                [vert.index for vert in ob.data.vertices if vert.co[0] <= 0])
            for ind, weight in wdict.items():
                actgr.add([ind], weight, 'REPLACE')
            bpy.context.object.data.update()

        return {'FINISHED'}


# --------------------------- RESYM MESH-------------------------


def reSymSave(self, quality):

    bpy.ops.object.mode_set(mode='OBJECT')

    object = bpy.context.object

    rdqual = quality
    rd = lambda x: round(x, rdqual)
    absol = lambda x: (abs(x[0]), x[1], x[2])

    inddict = {
            tuple(map(rd, vert.co[:])): vert.index for vert in object.data.vertices[:]
            }
    reldict = {inddict[vert]: inddict.get(absol(vert), inddict[vert])
               for vert in inddict if vert[0] <= 0}

    ENTFILEPATH = "%s_%s_SYM_TEMPLATE.xml" % (
        os.path.join(os.path.dirname(bpy.data.filepath),
                     bpy.context.scene.name),
        bpy.context.object.name)

    with open(ENTFILEPATH, mode="w") as file:
        file.writelines(str(reldict))
        reldict.clear()


def reSymMesh(self, SELECTED, SIDE):
    bpy.ops.object.mode_set(mode='EDIT')
    ENTFILEPATH = "%s_%s_SYM_TEMPLATE.xml" % (
        os.path.join(os.path.dirname(bpy.data.filepath),
                     bpy.context.scene.name),
        bpy.context.object.name)
    with open(ENTFILEPATH, mode="r") as file:
        SYMAP = eval(file.readlines()[0])
        bm = bmesh.from_edit_mesh(bpy.context.object.data)
        object = bpy.context.object

        def MAME(SYMAP):
            bm.verts.ensure_lookup_table()
            if SELECTED:
                for vert in SYMAP:
                    if bm.verts[SYMAP[vert]].select:
                        bm.verts[vert].co = (-1 * bm.verts[SYMAP[vert]].co[0],
                                             bm.verts[SYMAP[vert]].co[1],
                                             bm.verts[SYMAP[vert]].co[2])
            else:
                for vert in SYMAP:
                    bm.verts[vert].co = (-1 * bm.verts[SYMAP[vert]].co[0],
                                         bm.verts[SYMAP[vert]].co[1],
                                         bm.verts[SYMAP[vert]].co[2])
            bmesh.update_edit_mesh(object.data)

        def MEMA(SYMAP):
            bm.verts.ensure_lookup_table()
            if SELECTED:
                for vert in SYMAP:
                    if bm.verts[vert].select:
                        bm.verts[SYMAP[vert]].co = (-1 * bm.verts[vert].co[0],
                                                    bm.verts[vert].co[1],
                                                    bm.verts[vert].co[2])
            else:
                for vert in SYMAP:
                    bm.verts[SYMAP[vert]].co = (-1 * bm.verts[vert].co[0],
                                                bm.verts[vert].co[1],
                                                bm.verts[vert].co[2])
            bmesh.update_edit_mesh(object.data)

        if SIDE == "+-":
            MAME(SYMAP)
        else:
            MEMA(SYMAP)


class OscResymSave(Operator):
    """Creates a file on disk that saves the info of every vertex but in simmetry, """ \
    """this info its going to be later used by “Resym Mesh” and “Resym Vertex Weights”"""
    bl_idname = "mesh.resym_save_map"
    bl_label = "Resym save XML Map"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')

    quality = IntProperty(
            default=4,
            name="Quality"
            )

    def execute(self, context):
        reSymSave(self, self.quality)
        return {'FINISHED'}


class OscResymMesh(Operator):
    """Copies the symmetrical position of the vertices on the X axys. It needs the XML map"""
    bl_idname = "mesh.resym_mesh"
    bl_label = "Resym save Apply XML"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    selected = BoolProperty(
            default=False,
            name="Only Selected"
            )
    side = EnumProperty(
            name="Side:",
            description="Select Side",
            items=(('+-', "+X to -X", "+X to -X"),
                   ('-+', "-X to +X", "-X to +X")),
            default='+-',
            )

    def execute(self, context):
        reSymMesh(self, self.selected, self.side)
        return {'FINISHED'}


# -------------------------- OBJECT TO MESH ------------------------------

def DefOscObjectToMesh():
    ACTOBJ = bpy.context.object
    MESH = ACTOBJ.to_mesh(
        scene=bpy.context.scene,
        apply_modifiers=True,
        settings="RENDER")
    OBJECT = bpy.data.objects.new(("%s_Freeze") % (ACTOBJ.name), MESH)
    bpy.context.scene.objects.link(OBJECT)


class OscObjectToMesh(Operator):
    """It creates a copy of the final state of the object as it being see in the viewport"""
    bl_idname = "mesh.object_to_mesh_osc"
    bl_label = "Object To Mesh"

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type in
                {'MESH', 'META', 'CURVE', 'SURFACE'})

    def execute(self, context):
        print("Active type object is", context.object.type)
        DefOscObjectToMesh()

        return {'FINISHED'}


# ----------------------------- OVERLAP UV -------------------------------


def DefOscOverlapUv(self,offset,rotate):
    me = bpy.context.object.data
    bm = bmesh.from_edit_mesh(me)
    bm.faces.ensure_lookup_table()
    faces = [face for face in bm.faces if face.select]
    uv_layer = bm.loops.layers.uv[bpy.context.object.data.uv_layers.active.name]

    faceDict = {}
    faceReverse = []
    bm.select_mode = {'FACE'}
    for face in faces:
        bpy.ops.mesh.select_all(action="DESELECT")
        face.select = True
        bpy.ops.mesh.select_mirror()
        faceDict[face.index] = [mirrorface for mirrorface in bm.faces if mirrorface.select][0].index
        faceReverse.append([mirrorface for mirrorface in bm.faces if mirrorface.select][0])



    for selFace,mirrorFace in faceDict.items():
        for loop,mirrorLoop in zip(bm.faces[selFace].loops,bm.faces[mirrorFace].loops):
            mirrorLoop.copy_from(loop)
        if offset:
            for loop,mirrorLoop in zip(bm.faces[selFace].loops,bm.faces[mirrorFace].loops):
                mirrorLoop[uv_layer].uv += Vector((1,0))


    #invierto direcciones
    bmesh.ops.reverse_uvs(bm, faces=[f for f in faceReverse])
    bmesh.ops.rotate_uvs(bm, faces=[f for f in faceReverse])
    if rotate:
        bmesh.ops.rotate_uvs(bm, faces=[f for f in faceReverse])

    bmesh.update_edit_mesh(me)


class OscOverlapUv(Operator):
    """Overlaps the uvs on one side of the model symmetry plane. """ \
    """Useful to get more detail on fixed resolution bitmaps"""
    bl_idname = "mesh.overlap_uv_faces"
    bl_label = "Overlap Uvs"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')


    offset = BoolProperty(
            default=True,
            name="Offset"
            )
    rotate = BoolProperty(
            default=False,
            name="Rotate"
            )

    def execute(self, context):
        DefOscOverlapUv(self,self.offset,self.rotate)
        return {'FINISHED'}


# ------------------ PRINT VERTICES ----------------------

def dibuja_callback(self, context):
    font_id = 0
    bm = bmesh.from_edit_mesh(bpy.context.object.data)
    for v in bm.verts:
        cord = location_3d_to_region_2d(
            context.region,
            context.space_data.region_3d,
            self.matr * v.co)
        blf.position(font_id, cord[0], cord[1], 0)
        blf.size(font_id, self.tsize, 72)
        blf.draw(font_id, str(v.index))


class ModalIndexOperator(Operator):
    """Allow to visualize the index number for vertices in the viewport"""
    bl_idname = "view3d.modal_operator"
    bl_label = "Print Vertices"

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH')

    def modal(self, context, event):
        context.area.tag_redraw()
        if event.type == 'MOUSEMOVE':
            self.x = event.mouse_region_x
            self.matr = context.object.matrix_world
        elif event.type == 'LEFTMOUSE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}
        elif event.type == 'PAGE_UP':
            self.tsize += 1
        elif event.type == 'PAGE_DOWN':
            self.tsize -= 1
        elif event.type in {'RIGHTMOUSE', 'ESC', 'TAB'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            context.area.header_text_set(None)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == "VIEW_3D":
            context.area.header_text_set("Esc: exit, PageUP/Down: text size")
            bpy.ops.object.mode_set(mode="EDIT")
            self.tsize = 20
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(
                dibuja_callback, args, "WINDOW", "POST_PIXEL")
            context.window_manager.modal_handler_add(self)
            return{'RUNNING_MODAL'}
        else:
            self.report({"WARNING"}, "Is not a 3D Space")
            return {'CANCELLED'}


# -------------------------- SELECT DOUBLES

def SelDoubles(self, context):
    bm = bmesh.from_edit_mesh(bpy.context.object.data)

    for v in bm.verts:
        v.select = 0

    dictloc = {}

    rd = lambda x: (round(x[0], 4), round(x[1], 4), round(x[2], 4))

    for vert in bm.verts:
        dictloc.setdefault(rd(vert.co), []).append(vert.index)

    for loc, ind in dictloc.items():
        if len(ind) > 1:
            for v in ind:
                bm.verts[v].select = 1

    bpy.context.scene.objects.active = bpy.context.scene.objects.active


class SelectDoubles(Operator):
    """Selects duplicated vertex without merge them"""
    bl_idname = "mesh.select_doubles"
    bl_label = "Select Doubles"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH' and
                context.active_object.mode == "EDIT")

    def execute(self, context):
        SelDoubles(self, context)
        return {'FINISHED'}


# -------------------------- SELECT DOUBLES

def defLatticeMirror(self, context):

    ob = bpy.context.object
    u = ob.data.points_u
    v = ob.data.points_v
    w = ob.data.points_w
    total = u * v * w

    # guardo indices a cada punto
    libIndex = {point: index for point, index in zip(bpy.context.object.data.points, range(0, total))}

    # guardo puntos seleccionados
    selectionPoint = [libIndex[i] for i in ob.data.points if i.select]

    for point in selectionPoint:
        rango = list(range(int(point / u) * u, int(point / u) * u + (u)))
        rango.reverse()
        indPorcion = range(int(point / u) * u, int(point / u) * u + (u)).index(point)
        ob.data.points[rango[indPorcion]].co_deform.x = -ob.data.points[point].co_deform.x
        ob.data.points[rango[indPorcion]].co_deform.y = ob.data.points[point].co_deform.y
        ob.data.points[rango[indPorcion]].co_deform.z = ob.data.points[point].co_deform.z


class LatticeMirror(Operator):
    """Mirror Lattice"""
    bl_idname = "lattice.mirror_selected"
    bl_label = "Mirror Lattice"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'LATTICE' and
                context.active_object.mode == "EDIT")

    def execute(self, context):
        defLatticeMirror(self, context)
        return {'FINISHED'}


# -------------------------- OVERLAP UV ISLANDS

def defCopyUvsIsland(self, context):
    bpy.ops.object.mode_set(mode="OBJECT")
    global obLoop
    global islandFaces
    obLoop = []
    islandFaces = []
    for poly in bpy.context.object.data.polygons:
        if poly.select:
            islandFaces.append(poly.index)
            for li in poly.loop_indices:
                obLoop.append(li)

    bpy.ops.object.mode_set(mode="EDIT")

def defPasteUvsIsland(self, uvOffset, rotateUv,context):
    bpy.ops.object.mode_set(mode="OBJECT")
    selPolys = [poly.index for poly in bpy.context.object.data.polygons if poly.select]

    for island in selPolys:
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.object.data.polygons[island].select = True
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_linked()
        bpy.ops.object.mode_set(mode="OBJECT")
        TobLoop = []
        TislandFaces = []
        for poly in bpy.context.object.data.polygons:
            if poly.select:
                TislandFaces.append(poly.index)
                for li in poly.loop_indices:
                    TobLoop.append(li)

        for source,target in zip(range(min(obLoop),max(obLoop)+1),range(min(TobLoop),max(TobLoop)+1)):
            bpy.context.object.data.uv_layers.active.data[target].uv = bpy.context.object.data.uv_layers.active.data[source].uv + Vector((uvOffset,0))

        bpy.ops.object.mode_set(mode="EDIT")

    if rotateUv:
        bpy.ops.object.mode_set(mode="OBJECT")
        for poly in selPolys:
            bpy.context.object.data.polygons[poly].select = True
        bpy.ops.object.mode_set(mode="EDIT")
        bm = bmesh.from_edit_mesh(bpy.context.object.data)
        bmesh.ops.reverse_uvs(bm, faces=[f for f in bm.faces if f.select])
        bmesh.ops.rotate_uvs(bm, faces=[f for f in bm.faces if f.select])
        #bmesh.update_edit_mesh(bpy.context.object.data, loop_triangles=False, destructive=False)



class CopyUvIsland(Operator):
    """Copy Uv Island"""
    bl_idname = "mesh.uv_island_copy"
    bl_label = "Copy Uv Island"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH' and
                context.active_object.mode == "EDIT")

    def execute(self, context):
        defCopyUvsIsland(self, context)
        return {'FINISHED'}

class PasteUvIsland(Operator):
    """Paste Uv Island"""
    bl_idname = "mesh.uv_island_paste"
    bl_label = "Paste Uv Island"
    bl_options = {"REGISTER", "UNDO"}

    uvOffset = BoolProperty(
            name="Uv Offset",
            default=False
            )

    rotateUv = BoolProperty(
            name="Rotate Uv Corner",
            default=False
            )
    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and
                context.active_object.type == 'MESH' and
                context.active_object.mode == "EDIT")

    def execute(self, context):
        defPasteUvsIsland(self, self.uvOffset, self.rotateUv, context)
        return {'FINISHED'}



class createEditMultimesh(Operator):
    """Create Edit Multi Mesh"""
    bl_idname = "mesh.create_edit_multimesh"
    bl_label = "Create edit multimesh"
    bl_options = {"REGISTER", "UNDO"}


    # creo el merge para editar
    def execute(self,context):
        global relvert
        global me
        global ob
        temp = [[ob , [vert.co for vert in ob.data.vertices]]for ob in bpy.data.collections[bpy.context.scene.multimeshedit].objects]
        vi = 0
        pi = 0
        relvert = {}
        vertlist = []
        polylist = []
        for ob in temp:
            objectMatrix = ob[0].matrix_world.copy()
            for vert in ob[0].data.vertices:
                vertlist.append(objectMatrix*vert.co)
            for poly in ob[0].data.polygons:
                polylist.append(tuple([vert+vi for vert in poly.vertices[:]]))
            relvert[ob[0]] = {vert.index:vert.index+vi for vert in  ob[0].data.vertices}
            vi += len(ob[0].data.vertices)
            ob[0].hide = 1
        me = bpy.data.meshes.new("editMesh")
        ob = bpy.data.objects.new("editMesh", me)
        bpy.context.scene.objects.link(ob)
        me.from_pydata(vertlist,[],polylist)
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.scene.objects.active = ob
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        return {'FINISHED'}


class ApplyEditMultimesh(Operator):
    """Apply Edit Multi Mesh"""
    bl_idname = "mesh.apply_edit_multimesh"
    bl_label = "Apply edit multimesh"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self,context):
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        for object,rv in relvert.items():
            objectMatrix = object.matrix_world.inverted().copy()
            for source, target in rv.items():
                object.data.vertices[source].co = objectMatrix * me.vertices[target].co
            object.hide = 0
        bpy.context.scene.objects.unlink(ob)
        return {'FINISHED'}

# -------------------------VERTEX COLOR MASK----------------------------------


class resymVertexGroups(Operator):
    bl_idname = "mesh.vertex_color_mask"
    bl_label = "Vertex Color Mask"
    bl_description = ("Create a Vertex Color Mask")
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None

    def execute(self, context):
        obj = bpy.context.active_object
        mesh= obj.data

        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.ops.mesh.select_all(action="DESELECT")

        bm = bmesh.from_edit_mesh(mesh)
        bm.faces.ensure_lookup_table()

        islands = []
        faces = bm.faces

        try:
            color_layer = bm.loops.layers.color["RGBMask"]
        except:
            color_layer = bm.loops.layers.color.new("RGBMask")

        while faces:
            faces[0].select_set(True)
            bpy.ops.mesh.select_linked()
            islands.append([f for f in faces if f.select])
            bpy.ops.mesh.hide(unselected=False)
            faces = [f for f in bm.faces if not f.hide]

        bpy.ops.mesh.reveal()

        for island in islands:
            color = (uniform(0,1),uniform(0,1),uniform(0,1),1)
            for face in island:
                for loop in face.loops:
                    loop[color_layer] = color

        bpy.ops.object.mode_set(mode="VERTEX_PAINT")

        return {'FINISHED'}
