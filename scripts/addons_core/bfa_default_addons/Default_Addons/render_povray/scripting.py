# SPDX-FileCopyrightText: 2021-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Support POV Scene Description Language snippets or full includes: import,

load, create or edit"""

import bpy
from bpy.props import StringProperty, BoolProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper
from bpy.utils import register_class, unregister_class

from mathutils import Vector
from math import pi, sqrt


def export_custom_code(file):
    """write all POV user defined custom code to exported file"""
    # Write CurrentAnimation Frame for use in Custom POV Code
    file.write("#declare CURFRAMENUM = %d;\n" % bpy.context.scene.frame_current)
    # Change path and uncomment to add an animated include file by hand:
    file.write('//#include "/home/user/directory/animation_include_file.inc"\n')
    for txt in bpy.data.texts:
        if txt.pov.custom_code == "both":
            # Why are the newlines needed?
            file.write("\n")
            file.write(txt.as_string())
            file.write("\n")


# ----------------------------------- IMPORT


class SCENE_OT_POV_Import(bpy.types.Operator, ImportHelper):
    """Load Povray files"""

    bl_idname = "import_scene.pov"
    bl_label = "POV-Ray files (.pov/.inc)"
    bl_options = {"PRESET", "UNDO"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    # -----------
    # File props.
    files: CollectionProperty(
        type=bpy.types.OperatorFileListElement, options={"HIDDEN", "SKIP_SAVE"}
    )
    directory: StringProperty(maxlen=1024, subtype="FILE_PATH", options={"HIDDEN", "SKIP_SAVE"})

    filename_ext = {".pov", ".inc"}
    filter_glob: StringProperty(default="*.pov;*.inc", options={"HIDDEN"})

    import_at_cur: BoolProperty(
        name="Import at Cursor Location", description="Ignore Object Matrix", default=False
    )

    def execute(self, context):
        from mathutils import Matrix

        verts = []
        faces = []
        materials = []
        blend_mats = []  # XXX
        pov_mats = []  # XXX
        colors = []
        mat_names = []
        lenverts = None
        lenfaces = None
        suffix = -1
        name = "Mesh2_%s" % suffix
        name_search = False
        verts_search = False
        faces_search = False
        plane_search = False
        box_search = False
        cylinder_search = False
        sphere_search = False
        cone_search = False
        tex_search = False  # XXX
        cache = []
        matrixes = {}
        write_matrix = False
        index = None
        value = None
        # file_pov = bpy.path.abspath(self.filepath) # was used for single files

        def mat_search(cache):
            r = g = b = 0.5
            f = t = 0
            color = None
            for item, value in enumerate(cache):
                # if value == 'texture': # add more later
                if value == "pigment":
                    # Todo: create function for all color models.
                    # instead of current pass statements
                    # distinguish srgb from rgb into blend option
                    if cache[item + 2] in {"rgb", "srgb"}:
                        pass
                    elif cache[item + 2] in {"rgbf", "srgbf"}:
                        pass
                    elif cache[item + 2] in {"rgbt", "srgbt"}:
                        try:
                            r, g, b, t = (
                                float(cache[item + 3]),
                                float(cache[item + 4]),
                                float(cache[item + 5]),
                                float(cache[item + 6]),
                            )
                        except BaseException as e:
                            print(e.__doc__)
                            print("An exception occurred: {}".format(e))
                            r = g = b = t = float(cache[item + 2])
                        color = (r, g, b, t)

                    elif cache[item + 2] in {"rgbft", "srgbft"}:
                        pass

                    else:
                        pass

            if colors == [] or color not in colors:
                colors.append(color)
                name = ob.name + "_mat"
                mat_names.append(name)
                mat = bpy.data.materials.new(name)
                mat.diffuse_color = (r, g, b)
                mat.pov.alpha = 1 - t
                if mat.pov.alpha != 1:
                    mat.pov.use_transparency = True
                ob.data.materials.append(mat)

            else:
                for i, value in enumerate(colors):
                    if color == value:
                        ob.data.materials.append(bpy.data.materials[mat_names[i]])

        for file in self.files:
            print("Importing file: " + file.name)
            file_pov = self.directory + file.name
            # Ignore any non unicode character
            with open(file_pov, 'r', encoding='utf-8', errors="ignore") as infile:
                for line in infile:
                    string = line.replace("{", " ")
                    string = string.replace("}", " ")
                    string = string.replace("<", " ")
                    string = string.replace(">", " ")
                    string = string.replace(",", " ")
                    lw = string.split()
                    # lenwords = len(lw) # Not used... why written?
                    if lw:
                        if lw[0] == "object":
                            write_matrix = True
                        if write_matrix:
                            if lw[0] not in {"object", "matrix"}:
                                index = lw[0]
                            if lw[0] in {"matrix"}:
                                value = [
                                    float(lw[1]),
                                    float(lw[2]),
                                    float(lw[3]),
                                    float(lw[4]),
                                    float(lw[5]),
                                    float(lw[6]),
                                    float(lw[7]),
                                    float(lw[8]),
                                    float(lw[9]),
                                    float(lw[10]),
                                    float(lw[11]),
                                    float(lw[12]),
                                ]
                                matrixes[index] = value
                                write_matrix = False
            with open(file_pov, 'r', encoding='utf-8', errors="ignore") as infile:
                for line in infile:
                    S = line.replace("{", " { ")
                    S = S.replace("}", " } ")
                    S = S.replace(",", " ")
                    S = S.replace("<", "")
                    S = S.replace(">", " ")
                    S = S.replace("=", " = ")
                    S = S.replace(";", " ; ")
                    S = S.split()
                    # lenS = len(S) # Not used... why written?
                    for word in S:
                        # -------- Primitives Import -------- #
                        if word == "cone":
                            cone_search = True
                            name_search = False
                        if cone_search:
                            cache.append(word)
                            if cache[-1] == "}":
                                try:
                                    x0 = float(cache[2])
                                    y0 = float(cache[3])
                                    z0 = float(cache[4])
                                    r0 = float(cache[5])
                                    x1 = float(cache[6])
                                    y1 = float(cache[7])
                                    z1 = float(cache[8])
                                    r1 = float(cache[9])
                                    # Y is height in most pov files, not z
                                    bpy.ops.pov.addcone(base=r0, cap=r1, height=(y1 - y0))
                                    ob = context.object
                                    ob.location = (x0, y0, z0)
                                    # ob.scale = (r,r,r)
                                    mat_search(cache)
                                except ValueError:
                                    pass
                                cache = []
                                cone_search = False
                        if word == "plane":
                            plane_search = True
                            name_search = False
                        if plane_search:
                            cache.append(word)
                            if cache[-1] == "}":
                                try:
                                    bpy.ops.pov.addplane()
                                    ob = context.object
                                    mat_search(cache)
                                except ValueError:
                                    pass
                                cache = []
                                plane_search = False
                        if word == "box":
                            box_search = True
                            name_search = False
                        if box_search:
                            cache.append(word)
                            if cache[-1] == "}":
                                try:
                                    x0 = float(cache[2])
                                    y0 = float(cache[3])
                                    z0 = float(cache[4])
                                    x1 = float(cache[5])
                                    y1 = float(cache[6])
                                    z1 = float(cache[7])
                                    # imported_corner_1=(x0, y0, z0)
                                    # imported_corner_2 =(x1, y1, z1)
                                    center = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
                                    bpy.ops.pov.addbox()
                                    ob = context.object
                                    ob.location = center
                                    mat_search(cache)

                                except ValueError:
                                    pass
                                cache = []
                                box_search = False
                        if word == "cylinder":
                            cylinder_search = True
                            name_search = False
                        if cylinder_search:
                            cache.append(word)
                            if cache[-1] == "}":
                                try:
                                    x0 = float(cache[2])
                                    y0 = float(cache[3])
                                    z0 = float(cache[4])
                                    x1 = float(cache[5])
                                    y1 = float(cache[6])
                                    z1 = float(cache[7])
                                    imported_cyl_loc = (x0, y0, z0)
                                    imported_cyl_loc_cap = (x1, y1, z1)

                                    r = float(cache[8])

                                    vec = Vector(imported_cyl_loc_cap) - Vector(imported_cyl_loc)
                                    depth = vec.length
                                    rot = Vector((0, 0, 1)).rotation_difference(
                                        vec
                                    )  # Rotation from Z axis.
                                    trans = rot @ Vector(  # XXX Not used, why written?
                                        (0, 0, depth / 2)
                                    )  # Such that origin is at center of the base of the cylinder.
                                    # center = ((x0 + x1)/2,(y0 + y1)/2,(z0 + z1)/2)
                                    scale_z = sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2 + (z1 - z0) ** 2) / 2
                                    bpy.ops.pov.addcylinder(
                                        R=r,
                                        imported_cyl_loc=imported_cyl_loc,
                                        imported_cyl_loc_cap=imported_cyl_loc_cap,
                                    )
                                    ob = context.object
                                    ob.location = (x0, y0, z0)
                                    # todo: test and search where to add the below currently commented
                                    # since Blender defers the evaluation until the results are needed.
                                    # bpy.context.view_layer.update()
                                    # as explained here: https://docs.blender.org/api/current/info_gotcha.html?highlight=gotcha#no-updates-after-setting-values
                                    ob.rotation_euler = rot.to_euler()
                                    ob.scale = (1, 1, scale_z)

                                    # scale data rather than obj?
                                    # bpy.ops.object.mode_set(mode='EDIT')
                                    # bpy.ops.mesh.reveal()
                                    # bpy.ops.mesh.select_all(action='SELECT')
                                    # bpy.ops.transform.resize(value=(1,1,scale_z), orient_type='LOCAL')
                                    # bpy.ops.mesh.hide(unselected=False)
                                    # bpy.ops.object.mode_set(mode='OBJECT')

                                    mat_search(cache)

                                except ValueError:
                                    pass
                                cache = []
                                cylinder_search = False
                        if word == "sphere":
                            sphere_search = True
                            name_search = False
                        if sphere_search:
                            cache.append(word)
                            if cache[-1] == "}":
                                x = y = z = r = 0
                                try:
                                    x = float(cache[2])
                                    y = float(cache[3])
                                    z = float(cache[4])
                                    r = float(cache[5])

                                except ValueError:
                                    pass
                                except BaseException as e:
                                    print(e.__doc__)
                                    print("An exception occurred: {}".format(e))
                                    x = y = z = float(cache[2])
                                    r = float(cache[3])
                                bpy.ops.pov.addsphere(R=r, imported_loc=(x, y, z))
                                ob = context.object
                                ob.location = (x, y, z)
                                ob.scale = (r, r, r)
                                mat_search(cache)
                                cache = []
                                sphere_search = False
                        # -------- End Primitives Import -------- #
                        if word == "#declare":
                            name_search = True
                        if name_search:
                            cache.append(word)
                            if word == "mesh2":
                                name_search = False
                                if cache[-2] == "=":
                                    name = cache[-3]
                                else:
                                    suffix += 1
                                cache = []
                            if word in {"texture", ";"}:
                                name_search = False
                                cache = []
                        if word == "vertex_vectors":
                            verts_search = True
                        if verts_search:
                            cache.append(word)
                            if word == "}":
                                verts_search = False
                                lenverts = cache[2]
                                cache.pop()
                                cache.pop(0)
                                cache.pop(0)
                                cache.pop(0)
                                for j in range(int(lenverts)):
                                    x = j * 3
                                    y = (j * 3) + 1
                                    z = (j * 3) + 2
                                    verts.append((float(cache[x]), float(cache[y]), float(cache[z])))
                                cache = []
                        # if word == 'face_indices':
                        # faces_search = True
                        if word == "texture_list":  # XXX
                            tex_search = True  # XXX
                        if tex_search:  # XXX
                            if (
                                word not in {"texture_list", "texture", "{", "}", "face_indices"}
                                and not word.isdigit()
                            ):  # XXX
                                pov_mats.append(word)  # XXX
                        if word == "face_indices":
                            tex_search = False  # XXX
                            faces_search = True
                        if faces_search:
                            cache.append(word)
                            if word == "}":
                                faces_search = False
                                lenfaces = cache[2]
                                cache.pop()
                                cache.pop(0)
                                cache.pop(0)
                                cache.pop(0)
                                lf = int(lenfaces)
                                var = int(len(cache) / lf)
                                for k in range(lf):
                                    if var == 3:
                                        v0 = k * 3
                                        v1 = k * 3 + 1
                                        v2 = k * 3 + 2
                                        faces.append((int(cache[v0]), int(cache[v1]), int(cache[v2])))
                                    if var == 4:
                                        v0 = k * 4
                                        v1 = k * 4 + 1
                                        v2 = k * 4 + 2
                                        m = k * 4 + 3
                                        materials.append((int(cache[m])))
                                        faces.append((int(cache[v0]), int(cache[v1]), int(cache[v2])))
                                    if var == 6:
                                        v0 = k * 6
                                        v1 = k * 6 + 1
                                        v2 = k * 6 + 2
                                        m0 = k * 6 + 3
                                        m1 = k * 6 + 4
                                        m2 = k * 6 + 5
                                        materials.append(
                                            (int(cache[m0]), int(cache[m1]), int(cache[m2]))
                                        )
                                        faces.append((int(cache[v0]), int(cache[v1]), int(cache[v2])))
                                # mesh = pov_define_mesh(None, verts, [], faces, name, hide_geometry=False)
                                # ob = object_utils.object_data_add(context, mesh, operator=None)

                                me = bpy.data.meshes.new(name)  # XXX
                                ob = bpy.data.objects.new(name, me)  # XXX
                                bpy.context.collection.objects.link(ob)  # XXX
                                me.from_pydata(verts, [], faces)  # XXX

                                for mat in bpy.data.materials:  # XXX
                                    blend_mats.append(mat.name)  # XXX
                                for m_name in pov_mats:  # XXX
                                    if m_name not in blend_mats:  # XXX
                                        bpy.data.materials.new(m_name)  # XXX
                                        mat_search(cache)
                                    ob.data.materials.append(bpy.data.materials[m_name])  # XXX
                                if materials:  # XXX
                                    for idx, val in enumerate(materials):  # XXX
                                        try:  # XXX
                                            ob.data.polygons[idx].material_index = val  # XXX
                                        except TypeError:  # XXX
                                            ob.data.polygons[idx].material_index = int(val[0])  # XXX

                                blend_mats = []  # XXX
                                pov_mats = []  # XXX
                                materials = []  # XXX
                                cache = []
                                name_search = True
                                if name in matrixes and not self.import_at_cur:
                                    global_matrix = Matrix.Rotation(pi / 2.0, 4, "X")
                                    ob = bpy.context.object
                                    matrix = ob.matrix_world
                                    v = matrixes[name]
                                    matrix[0][0] = v[0]
                                    matrix[1][0] = v[1]
                                    matrix[2][0] = v[2]
                                    matrix[0][1] = v[3]
                                    matrix[1][1] = v[4]
                                    matrix[2][1] = v[5]
                                    matrix[0][2] = v[6]
                                    matrix[1][2] = v[7]
                                    matrix[2][2] = v[8]
                                    matrix[0][3] = v[9]
                                    matrix[1][3] = v[10]
                                    matrix[2][3] = v[11]
                                    matrix = global_matrix * ob.matrix_world
                                    ob.matrix_world = matrix
                                verts = []
                                faces = []

                        # if word == 'pigment':
                        # try:
                        # #all indices have been incremented once to fit a bad test file
                        # r,g,b,t = float(S[2]),float(S[3]),float(S[4]),float(S[5])
                        # color = (r,g,b,t)

                        # except IndexError:
                        # #all indices have been incremented once to fit alternate test file
                        # r,g,b,t = float(S[3]),float(S[4]),float(S[5]),float(S[6])
                        # color = (r,g,b,t)
                        # except UnboundLocalError:
                        # # In case no transmit is specified ? put it to 0
                        # r,g,b,t = float(S[2]),float(S[3]),float(S[4],0)
                        # color = (r,g,b,t)

                        # except ValueError:
                        # color = (0.8,0.8,0.8,0)
                        # pass

                        # if colors == [] or (colors != [] and color not in colors):
                        # colors.append(color)
                        # name = ob.name+"_mat"
                        # mat_names.append(name)
                        # mat = bpy.data.materials.new(name)
                        # mat.diffuse_color = (r,g,b)
                        # mat.pov.alpha = 1-t
                        # if mat.pov.alpha != 1:
                        # mat.pov.use_transparency=True
                        # ob.data.materials.append(mat)
                        # print (colors)
                        # else:
                        # for m in range(len(colors)):
                        # if color == colors[m]:
                        # ob.data.materials.append(bpy.data.materials[mat_names[m]])

        # To keep Avogadro Camera angle:
        # for obj in bpy.context.view_layer.objects:
        # if obj.type == "CAMERA":
        # track = obj.constraints.new(type = "TRACK_TO")
        # track.target = ob
        # track.track_axis ="TRACK_NEGATIVE_Z"
        # track.up_axis = "UP_Y"
        # obj.location = (0,0,0)
        return {"FINISHED"}


classes = (SCENE_OT_POV_Import,)


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
