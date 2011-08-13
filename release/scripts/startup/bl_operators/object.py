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

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty


class SelectPattern(Operator):
    '''Select object matching a naming pattern'''
    bl_idname = "object.select_pattern"
    bl_label = "Select Pattern"
    bl_options = {'REGISTER', 'UNDO'}

    pattern = StringProperty(
            name="Pattern",
            description="Name filter using '*' and '?' wildcard chars",
            maxlen=32,
            default="*",
            )
    case_sensitive = BoolProperty(
            name="Case Sensitive",
            description="Do a case sensitive compare",
            default=False,
            )
    extend = BoolProperty(
            name="Extend",
            description="Extend the existing selection",
            default=True,
            )

    def execute(self, context):

        import fnmatch

        if self.case_sensitive:
            pattern_match = fnmatch.fnmatchcase
        else:
            pattern_match = (lambda a, b:
                                 fnmatch.fnmatchcase(a.upper(), b.upper()))
        is_ebone = False
        obj = context.object
        if obj and obj.mode == 'POSE':
            items = obj.data.bones
            if not self.extend:
                bpy.ops.pose.select_all(action='DESELECT')
        elif obj and obj.type == 'ARMATURE' and obj.mode == 'EDIT':
            items = obj.data.edit_bones
            if not self.extend:
                bpy.ops.armature.select_all(action='DESELECT')
            is_ebone = True
        else:
            items = context.visible_objects
            if not self.extend:
                bpy.ops.object.select_all(action='DESELECT')

        # Can be pose bones or objects
        for item in items:
            if pattern_match(item.name, self.pattern):
                item.select = True

                # hrmf, perhaps there should be a utility function for this.
                if is_ebone:
                    item.select_head = True
                    item.select_tail = True
                    if item.use_connect:
                        item_parent = item.parent
                        if item_parent is not None:
                            item_parent.select_tail = True

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_popup(self, event)

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "pattern")
        row = layout.row()
        row.prop(self, "case_sensitive")
        row.prop(self, "extend")


class SelectCamera(Operator):
    '''Select object matching a naming pattern'''
    bl_idname = "object.select_camera"
    bl_label = "Select Camera"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera is not None

    def execute(self, context):
        scene = context.scene
        camera = scene.camera
        if camera.name not in scene.objects:
            self.report({'WARNING'}, "Active camera is not in this scene")

        context.scene.objects.active = camera
        camera.select = True
        return {'FINISHED'}


class SelectHierarchy(Operator):
    '''Select object relative to the active objects position''' \
    '''in the hierarchy'''
    bl_idname = "object.select_hierarchy"
    bl_label = "Select Hierarchy"
    bl_options = {'REGISTER', 'UNDO'}

    direction = EnumProperty(
            items=(('PARENT', "Parent", ""),
                   ('CHILD', "Child", ""),
                   ),
            name="Direction",
            description="Direction to select in the hierarchy",
            default='PARENT')

    extend = BoolProperty(
            name="Extend",
            description="Extend the existing selection",
            default=False,
            )

    @classmethod
    def poll(cls, context):
        return context.object

    def execute(self, context):
        select_new = []
        act_new = None

        selected_objects = context.selected_objects
        obj_act = context.object

        if context.object not in selected_objects:
            selected_objects.append(context.object)

        if self.direction == 'PARENT':
            for obj in selected_objects:
                parent = obj.parent

                if parent:
                    if obj_act == obj:
                        act_new = parent

                    select_new.append(parent)

        else:
            for obj in selected_objects:
                select_new.extend(obj.children)

            if select_new:
                select_new.sort(key=lambda obj_iter: obj_iter.name)
                act_new = select_new[0]

        # dont edit any object settings above this
        if select_new:
            if not self.extend:
                bpy.ops.object.select_all(action='DESELECT')

            for obj in select_new:
                obj.select = True

            context.scene.objects.active = act_new
            return {'FINISHED'}

        return {'CANCELLED'}


class SubdivisionSet(Operator):
    '''Sets a Subdivision Surface Level (1-5)'''

    bl_idname = "object.subdivision_set"
    bl_label = "Subdivision Set"
    bl_options = {'REGISTER', 'UNDO'}

    level = IntProperty(name="Level",
            default=1, min=-100, max=100, soft_min=-6, soft_max=6)

    relative = BoolProperty(
            name="Relative",
            description=("Apply the subsurf level as an offset "
                         "relative to the current level"),
            default=False,
            )

    @classmethod
    def poll(cls, context):
        obs = context.selected_editable_objects
        return (obs is not None)

    def execute(self, context):
        level = self.level
        relative = self.relative

        if relative and level == 0:
            return {'CANCELLED'}  # nothing to do

        if not relative and level < 0:
            self.level = level = 0

        def set_object_subd(obj):
            for mod in obj.modifiers:
                if mod.type == 'MULTIRES':
                    if not relative:
                        if level <= mod.total_levels:
                            if obj.mode == 'SCULPT':
                                if mod.sculpt_levels != level:
                                    mod.sculpt_levels = level
                            elif obj.mode == 'OBJECT':
                                if mod.levels != level:
                                    mod.levels = level
                        return
                    else:
                        if obj.mode == 'SCULPT':
                            if mod.sculpt_levels + level <= mod.total_levels:
                                mod.sculpt_levels += level
                        elif obj.mode == 'OBJECT':
                            if mod.levels + level <= mod.total_levels:
                                mod.levels += level
                        return

                elif mod.type == 'SUBSURF':
                    if relative:
                        mod.levels += level
                    else:
                        if mod.levels != level:
                            mod.levels = level

                    return

            # add a new modifier
            try:
                mod = obj.modifiers.new("Subsurf", 'SUBSURF')
                mod.levels = level
            except:
                self.report({'WARNING'},
                            "Modifiers cannot be added to object: " + obj.name)

        for obj in context.selected_editable_objects:
            set_object_subd(obj)

        return {'FINISHED'}


class ShapeTransfer(Operator):
    '''Copy another selected objects active shape to this one by ''' \
    '''applying the relative offsets'''

    bl_idname = "object.shape_key_transfer"
    bl_label = "Transfer Shape Key"
    bl_options = {'REGISTER', 'UNDO'}

    mode = EnumProperty(
            items=(('OFFSET',
                    "Offset",
                    "Apply the relative positional offset",
                    ),
                   ('RELATIVE_FACE',
                    "Relative Face",
                    "Calculate relative position (using faces).",
                    ),
                   ('RELATIVE_EDGE',
                   "Relative Edge",
                   "Calculate relative position (using edges).",
                   ),
                   ),
            name="Transformation Mode",
            description="Relative shape positions to the new shape method",
            default='OFFSET',
            )
    use_clamp = BoolProperty(
            name="Clamp Offset",
            description=("Clamp the transformation to the distance each "
                         "vertex moves in the original shape."),
            default=False,
            )

    def _main(self, ob_act, objects, mode='OFFSET', use_clamp=False):

        def me_nos(verts):
            return [v.normal.copy() for v in verts]

        def me_cos(verts):
            return [v.co.copy() for v in verts]

        def ob_add_shape(ob, name):
            me = ob.data
            key = ob.shape_key_add(from_mix=False)
            if len(me.shape_keys.key_blocks) == 1:
                key.name = "Basis"
                key = ob.shape_key_add(from_mix=False)  # we need a rest
            key.name = name
            ob.active_shape_key_index = len(me.shape_keys.key_blocks) - 1
            ob.show_only_shape_key = True

        from mathutils.geometry import barycentric_transform
        from mathutils import Vector

        if use_clamp and mode == 'OFFSET':
            use_clamp = False

        me = ob_act.data
        orig_key_name = ob_act.active_shape_key.name

        orig_shape_coords = me_cos(ob_act.active_shape_key.data)

        orig_normals = me_nos(me.vertices)
        # the actual mverts location isnt as relyable as the base shape :S
        # orig_coords = me_cos(me.vertices)
        orig_coords = me_cos(me.shape_keys.key_blocks[0].data)

        for ob_other in objects:
            me_other = ob_other.data
            if len(me_other.vertices) != len(me.vertices):
                self.report({'WARNING'},
                            ("Skipping '%s', "
                             "vertex count differs") % ob_other.name)
                continue

            target_normals = me_nos(me_other.vertices)
            if me_other.shape_keys:
                target_coords = me_cos(me_other.shape_keys.key_blocks[0].data)
            else:
                target_coords = me_cos(me_other.vertices)

            ob_add_shape(ob_other, orig_key_name)

            # editing the final coords, only list that stores wrapped coords
            target_shape_coords = [v.co for v in
                                   ob_other.active_shape_key.data]

            median_coords = [[] for i in range(len(me.vertices))]

            # Method 1, edge
            if mode == 'OFFSET':
                for i, vert_cos in enumerate(median_coords):
                    vert_cos.append(target_coords[i] +
                                    (orig_shape_coords[i] - orig_coords[i]))

            elif mode == 'RELATIVE_FACE':
                for face in me.faces:
                    i1, i2, i3, i4 = face.vertices_raw
                    if i4 != 0:
                        pt = barycentric_transform(orig_shape_coords[i1],
                                                   orig_coords[i4],
                                                   orig_coords[i1],
                                                   orig_coords[i2],
                                                   target_coords[i4],
                                                   target_coords[i1],
                                                   target_coords[i2],
                                                   )
                        median_coords[i1].append(pt)

                        pt = barycentric_transform(orig_shape_coords[i2],
                                                   orig_coords[i1],
                                                   orig_coords[i2],
                                                   orig_coords[i3],
                                                   target_coords[i1],
                                                   target_coords[i2],
                                                   target_coords[i3],
                                                   )
                        median_coords[i2].append(pt)

                        pt = barycentric_transform(orig_shape_coords[i3],
                                                   orig_coords[i2],
                                                   orig_coords[i3],
                                                   orig_coords[i4],
                                                   target_coords[i2],
                                                   target_coords[i3],
                                                   target_coords[i4],
                                                   )
                        median_coords[i3].append(pt)

                        pt = barycentric_transform(orig_shape_coords[i4],
                                                   orig_coords[i3],
                                                   orig_coords[i4],
                                                   orig_coords[i1],
                                                   target_coords[i3],
                                                   target_coords[i4],
                                                   target_coords[i1],
                                                   )
                        median_coords[i4].append(pt)

                    else:
                        pt = barycentric_transform(orig_shape_coords[i1],
                                                   orig_coords[i3],
                                                   orig_coords[i1],
                                                   orig_coords[i2],
                                                   target_coords[i3],
                                                   target_coords[i1],
                                                   target_coords[i2],
                                                   )
                        median_coords[i1].append(pt)

                        pt = barycentric_transform(orig_shape_coords[i2],
                                                   orig_coords[i1],
                                                   orig_coords[i2],
                                                   orig_coords[i3],
                                                   target_coords[i1],
                                                   target_coords[i2],
                                                   target_coords[i3],
                                                   )
                        median_coords[i2].append(pt)

                        pt = barycentric_transform(orig_shape_coords[i3],
                                                   orig_coords[i2],
                                                   orig_coords[i3],
                                                   orig_coords[i1],
                                                   target_coords[i2],
                                                   target_coords[i3],
                                                   target_coords[i1],
                                                   )
                        median_coords[i3].append(pt)

            elif mode == 'RELATIVE_EDGE':
                for ed in me.edges:
                    i1, i2 = ed.vertices
                    v1, v2 = orig_coords[i1], orig_coords[i2]
                    edge_length = (v1 - v2).length
                    n1loc = v1 + orig_normals[i1] * edge_length
                    n2loc = v2 + orig_normals[i2] * edge_length

                    # now get the target nloc's
                    v1_to, v2_to = target_coords[i1], target_coords[i2]
                    edlen_to = (v1_to - v2_to).length
                    n1loc_to = v1_to + target_normals[i1] * edlen_to
                    n2loc_to = v2_to + target_normals[i2] * edlen_to

                    pt = barycentric_transform(orig_shape_coords[i1],
                        v2, v1, n1loc,
                        v2_to, v1_to, n1loc_to)
                    median_coords[i1].append(pt)

                    pt = barycentric_transform(orig_shape_coords[i2],
                        v1, v2, n2loc,
                        v1_to, v2_to, n2loc_to)
                    median_coords[i2].append(pt)

            # apply the offsets to the new shape
            from functools import reduce
            VectorAdd = Vector.__add__

            for i, vert_cos in enumerate(median_coords):
                if vert_cos:
                    co = reduce(VectorAdd, vert_cos) / len(vert_cos)

                    if use_clamp:
                        # clamp to the same movement as the original
                        # breaks copy between different scaled meshes.
                        len_from = (orig_shape_coords[i] -
                                    orig_coords[i]).length
                        ofs = co - target_coords[i]
                        ofs.length = len_from
                        co = target_coords[i] + ofs

                    target_shape_coords[i][:] = co

        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.mode != 'EDIT')

    def execute(self, context):
        C = bpy.context
        ob_act = C.active_object
        objects = [ob for ob in C.selected_editable_objects if ob != ob_act]

        if 1:  # swap from/to, means we cant copy to many at once.
            if len(objects) != 1:
                self.report({'ERROR'},
                            ("Expected one other selected "
                             "mesh object to copy from"))

                return {'CANCELLED'}
            ob_act, objects = objects[0], [ob_act]

        if ob_act.type != 'MESH':
            self.report({'ERROR'}, "Other object is not a mesh.")
            return {'CANCELLED'}

        if ob_act.active_shape_key is None:
            self.report({'ERROR'}, "Other object has no shape key")
            return {'CANCELLED'}
        return self._main(ob_act, objects, self.mode, self.use_clamp)


class JoinUVs(Operator):
    '''Copy UV Layout to objects with matching geometry'''
    bl_idname = "object.join_uvs"
    bl_label = "Join as UVs"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def _main(self, context):
        import array
        obj = context.active_object
        mesh = obj.data

        is_editmode = (obj.mode == 'EDIT')
        if is_editmode:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        if not mesh.uv_textures:
            self.report({'WARNING'},
                        "Object: %s, Mesh: '%s' has no UVs"
                        % (obj.name, mesh.name))
        else:
            len_faces = len(mesh.faces)

            # seems to be the fastest way to create an array
            uv_array = array.array('f', [0.0] * 8) * len_faces
            mesh.uv_textures.active.data.foreach_get("uv_raw", uv_array)

            objects = context.selected_editable_objects[:]

            for obj_other in objects:
                if obj_other.type == 'MESH':
                    obj_other.data.tag = False

            for obj_other in objects:
                if obj_other != obj and obj_other.type == 'MESH':
                    mesh_other = obj_other.data
                    if mesh_other != mesh:
                        if mesh_other.tag == False:
                            mesh_other.tag = True

                            if len(mesh_other.faces) != len_faces:
                                self.report({'WARNING'}, "Object: %s, Mesh: "
                                            "'%s' has %d faces, expected %d\n"
                                            % (obj_other.name,
                                               mesh_other.name,
                                               len(mesh_other.faces),
                                               len_faces),
                                               )
                            else:
                                uv_other = mesh_other.uv_textures.active
                                if not uv_other:
                                    # should return the texture it adds
                                    uv_other = mesh_other.uv_textures.new()

                                # finally do the copy
                                uv_other.data.foreach_set("uv_raw", uv_array)

        if is_editmode:
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    def execute(self, context):
        self._main(context)
        return {'FINISHED'}


class MakeDupliFace(Operator):
    '''Make linked objects into dupli-faces'''
    bl_idname = "object.make_dupli_face"
    bl_label = "Make Dupli-Face"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def _main(self, context):
        from mathutils import Vector

        SCALE_FAC = 0.01
        offset = 0.5 * SCALE_FAC
        base_tri = (Vector((-offset, -offset, 0.0)),
                    Vector((+offset, -offset, 0.0)),
                    Vector((+offset, +offset, 0.0)),
                    Vector((-offset, +offset, 0.0)),
                    )

        def matrix_to_quat(matrix):
            # scale = matrix.median_scale
            trans = matrix.to_translation()
            rot = matrix.to_3x3()  # also contains scale

            return [(rot * b) + trans for b in base_tri]
        scene = bpy.context.scene
        linked = {}
        for obj in bpy.context.selected_objects:
            data = obj.data
            if data:
                linked.setdefault(data, []).append(obj)

        for data, objects in linked.items():
            face_verts = [axis for obj in objects
                          for v in matrix_to_quat(obj.matrix_world)
                          for axis in v]

            faces = list(range(len(face_verts) // 3))

            mesh = bpy.data.meshes.new(data.name + "_dupli")

            mesh.vertices.add(len(face_verts) // 3)
            mesh.faces.add(len(face_verts) // 12)

            mesh.vertices.foreach_set("co", face_verts)
            mesh.faces.foreach_set("vertices_raw", faces)
            mesh.update()  # generates edge data

            # pick an object to use
            obj = objects[0]

            ob_new = bpy.data.objects.new(mesh.name, mesh)
            base = scene.objects.link(ob_new)
            base.layers[:] = obj.layers

            ob_inst = bpy.data.objects.new(data.name, data)
            base = scene.objects.link(ob_inst)
            base.layers[:] = obj.layers

            for obj in objects:
                scene.objects.unlink(obj)

            ob_new.dupli_type = 'FACES'
            ob_inst.parent = ob_new
            ob_new.use_dupli_faces_scale = True
            ob_new.dupli_faces_scale = 1.0 / SCALE_FAC

    def execute(self, context):
        self._main(context)
        return {'FINISHED'}


class IsolateTypeRender(Operator):
    '''Hide unselected render objects of same type as active ''' \
    '''by setting the hide render flag'''
    bl_idname = "object.isolate_type_render"
    bl_label = "Restrict Render Unselected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        act_type = context.object.type

        for obj in context.visible_objects:

            if obj.select:
                obj.hide_render = False
            else:
                if obj.type == act_type:
                    obj.hide_render = True

        return {'FINISHED'}


class ClearAllRestrictRender(Operator):
    '''Reveal all render objects by setting the hide render flag'''
    bl_idname = "object.hide_render_clear_all"
    bl_label = "Clear All Restrict Render"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for obj in context.scene.objects:
            obj.hide_render = False
        return {'FINISHED'}
