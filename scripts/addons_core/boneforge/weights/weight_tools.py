"""BoneCraft Phase 2B — automatic weight repair and flood fill tools.

Quick weight assignment operators: flood to zero, flood to one
(with proportional reduction), and flood to custom value.
Category: Weight Tools.
"""

import bpy
from bpy.props import FloatProperty, BoolProperty, EnumProperty, IntProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup
import logging
from boneforge.i18n import T

logger = logging.getLogger(__name__)


def _weight_mesh_poll(_self, obj):
    return obj.type == 'MESH'


def _weight_armature_poll(_self, obj):
    return obj.type == 'ARMATURE'


class BF_WeightRecalculationSettings(PropertyGroup):
    target_mesh: PointerProperty(name="Mesh to Reweight", type=bpy.types.Object, poll=_weight_mesh_poll)
    armature: PointerProperty(name="Existing Armature", type=bpy.types.Object, poll=_weight_armature_poll)
    mode: EnumProperty(
        name="Mesh Type",
        items=(('BODY', "Body", "Calculate bone heat weights from the existing armature"),
               ('CLOTHING', "Clothing", "Copy weights from the nearest vertices of a weighted body")),
        default='BODY',
    )
    source_mesh: PointerProperty(name="Weighted Body", type=bpy.types.Object, poll=_weight_mesh_poll)
    body_method: EnumProperty(
        name="Body Method",
        items=(('AUTO', "Bone Heat", "Blender's automatic weights, which account for mesh topology"),
               ('DISTANCE', "Nearest Bones", "Weight by distance to deform bone segments; useful when bone heat fails")),
        default='AUTO',
    )
    transfer_method: EnumProperty(
        name="Clothing Sampling",
        items=(('SURFACE', "Nearest Surface", "Interpolate weights across the nearest body triangle"),
               ('VERTEX', "Nearest Vertex", "Copy weights from the nearest body vertex")),
        default='SURFACE',
    )
    max_transfer_distance: FloatProperty(
        name="Max Transfer Distance",
        description="Cancel clothing transfer if any vertex is farther from the body than this distance; zero disables the limit",
        min=0.0, default=0.0, precision=3,
    )
    blend: FloatProperty(
        name="New Weight Strength",
        description="Blend calculated weights with the mesh's existing deform weights",
        min=0.0, max=1.0, default=1.0, subtype='FACTOR',
    )
    smooth_iterations: IntProperty(
        name="Smooth Passes",
        description="Average new weights across connected vertices; zero keeps boundaries sharp",
        min=0, max=10, default=0,
    )
    smooth_strength: FloatProperty(
        name="Smooth Strength",
        min=0.0, max=1.0, default=0.5, subtype='FACTOR',
    )
    max_influences: IntProperty(
        name="Max Bones per Vertex",
        description="Keep only the strongest bone influences; zero leaves the count unlimited",
        min=0, max=16, default=0,
    )
    minimum_weight: FloatProperty(
        name="Minimum Weight",
        description="Discard weaker influences, keeping at least the strongest bone per vertex",
        min=0.0, max=0.25, default=0.001, precision=4,
    )
    keep_backup: BoolProperty(
        name="Keep Weight Backup",
        description="Keep a hidden duplicate of the mesh and its original weights",
        default=True,
    )


def draw_automatic_weight_recalculation(layout, context):
    """The same controls appear in Skin and CATS; both call one operator."""
    if not hasattr(context.scene, "boneforge_weight_recalculation"):
        layout.label(text=T("Enable Weight & Deform Tools to use weight recalculation"), icon='INFO')
        return
    settings = context.scene.boneforge_weight_recalculation
    box = layout.box()
    box.label(text=T("Automatic Bone Weight Recalculation"))
    box.prop(settings, "target_mesh")
    box.prop(settings, "armature")
    box.prop(settings, "mode", expand=True)
    if settings.mode == 'CLOTHING':
        box.prop(settings, "source_mesh")
        box.prop(settings, "transfer_method")
        box.prop(settings, "max_transfer_distance")
        box.label(text=T("Use a correctly weighted body as the source"), icon='INFO')
    else:
        box.prop(settings, "body_method")
        box.label(text=T("Uses the existing rig; mesh topology stays unchanged"), icon='INFO')
    box.prop(settings, "blend")
    box.prop(settings, "smooth_iterations")
    if settings.smooth_iterations:
        box.prop(settings, "smooth_strength")
    box.prop(settings, "max_influences")
    box.prop(settings, "minimum_weight")
    box.prop(settings, "keep_backup")
    box.operator("boneforge.automatic_bone_weight_recalculation",
                 text=T("Automatic Bone Weight Recalculation"), icon='MOD_VERTEX_WEIGHT')


def _bound_armature(mesh):
    for modifier in mesh.modifiers:
        if modifier.type == 'ARMATURE' and modifier.object is not None:
            return modifier.object
    return mesh.parent if mesh.parent and mesh.parent.type == 'ARMATURE' else None


def _read_deform_weights(mesh, deform_names):
    """Return one sparse name-to-weight map per vertex."""
    names = {group.index: group.name for group in mesh.vertex_groups
             if group.name in deform_names}
    return [
        {names[item.group]: item.weight for item in vertex.groups
         if item.group in names and item.weight > 0.0}
        for vertex in mesh.data.vertices
    ]


def _nearest_bone_weights(target, armature):
    """Weight each vertex against the two nearest deform bone segments."""
    segments = [(bone.name, armature.matrix_world @ bone.head_local,
                 armature.matrix_world @ bone.tail_local)
                for bone in armature.data.bones if bone.use_deform]
    weights = []
    for vertex in target.data.vertices:
        position = target.matrix_world @ vertex.co
        first = (float('inf'), None)
        second = (float('inf'), None)
        for name, head, tail in segments:
            axis = tail - head
            factor = max(0.0, min(1.0, (position - head).dot(axis) / axis.length_squared)) \
                if axis.length_squared > 1e-12 else 0.0
            candidate = ((position - (head + factor * axis)).length_squared, name)
            if candidate[0] < first[0]:
                second = first
                first = candidate
            elif candidate[0] < second[0]:
                second = candidate
        first_squared, first_name = first
        if second[1] is None:
            weights.append({first_name: 1.0})
            continue
        first_distance = first_squared ** 0.5
        second_distance, second_name = second[0] ** 0.5, second[1]
        total = first_distance + second_distance + 1e-8
        weights.append({first_name: (second_distance + 1e-8) / total,
                        second_name: first_distance / total})
    return weights


def _body_weights(context, target, armature, deform_names, method):
    """Use bone heat or nearest bones without changing the original binding."""
    if method == 'DISTANCE':
        return _nearest_bone_weights(target, armature)
    temporary = target.copy()
    temporary.data = target.data.copy()
    temporary.name = "BF_WEIGHT_CALC_TEMP"
    (target.users_collection[0] if target.users_collection else context.scene.collection).objects.link(temporary)
    temporary_data = temporary.data
    world_matrix = target.matrix_world.copy()
    try:
        temporary.parent = None
        temporary.matrix_world = world_matrix
        for modifier in list(temporary.modifiers):
            temporary.modifiers.remove(modifier)
        for group in list(temporary.vertex_groups):
            temporary.vertex_groups.remove(group)
        bpy.ops.object.select_all(action='DESELECT')
        temporary.select_set(True)
        armature.select_set(True)
        context.view_layer.objects.active = armature
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        weights = _read_deform_weights(temporary, deform_names)
        if not weights or any(not vertex_weights for vertex_weights in weights):
            raise RuntimeError("Automatic weights left vertices unweighted; original weights were kept")
        return weights
    finally:
        bpy.data.objects.remove(temporary, do_unlink=True)
        if temporary_data.users == 0:
            bpy.data.meshes.remove(temporary_data)


def _triangle_factors(point, a, b, c):
    """Barycentric factors for a point on a body triangle."""
    ab, ac, ap = b - a, c - a, point - a
    d00, d01, d11 = ab.dot(ab), ab.dot(ac), ac.dot(ac)
    d20, d21 = ap.dot(ab), ap.dot(ac)
    denominator = d00 * d11 - d01 * d01
    if abs(denominator) < 1e-12:
        return (1.0, 0.0, 0.0)
    b_factor = (d11 * d20 - d01 * d21) / denominator
    c_factor = (d00 * d21 - d01 * d20) / denominator
    factors = (max(0.0, 1.0 - b_factor - c_factor),
               max(0.0, b_factor), max(0.0, c_factor))
    total = sum(factors)
    return tuple(value / total for value in factors)


def _clothing_weights(target, source, deform_names, method, max_distance):
    """Sample a weighted body in world space for each clothing vertex."""
    from mathutils import kdtree
    if not source.data.vertices:
        raise ValueError("The weighted body has no vertices")
    source_weights = _read_deform_weights(source, deform_names)
    if not any(source_weights):
        raise ValueError("The weighted body has no weights for this armature")
    world_vertices = [source.matrix_world @ vertex.co for vertex in source.data.vertices]
    if method == 'SURFACE':
        from mathutils.bvhtree import BVHTree
        source.data.calc_loop_triangles()
        triangles = [tuple(triangle.vertices) for triangle in source.data.loop_triangles]
        if not triangles:
            raise ValueError("The weighted body needs faces for nearest-surface transfer")
        tree = BVHTree.FromPolygons(world_vertices, triangles, all_triangles=True)
    else:
        tree = kdtree.KDTree(len(world_vertices))
        for index, point in enumerate(world_vertices):
            tree.insert(point, index)
        tree.balance()
    weights = []
    for vertex in target.data.vertices:
        position = target.matrix_world @ vertex.co
        if method == 'SURFACE':
            nearest, _normal, index, distance = tree.find_nearest(position)
            if index is None:
                raise ValueError("Could not find a body surface near the clothing")
            triangle = triangles[index]
            factors = _triangle_factors(nearest, *(world_vertices[i] for i in triangle))
            values = {}
            for source_index, factor in zip(triangle, factors):
                for name, weight in source_weights[source_index].items():
                    values[name] = values.get(name, 0.0) + factor * weight
        else:
            _point, index, distance = tree.find(position)
            values = source_weights[index]
        if max_distance and distance > max_distance:
            raise ValueError(
                f"Clothing is {distance:.3f} units from the body; increase Max Transfer Distance"
            )
        if not values:
            raise ValueError("The nearest body area has no deform weights; original weights were kept")
        total = sum(values.values())
        weights.append({name: value / total for name, value in values.items()})
    return weights


def _finish_recalculated_weights(target, deform_names, weights, blend,
                                 smooth_iterations, smooth_strength,
                                 max_influences, minimum_weight):
    """Blend, optionally smooth, then prune and normalize deform weights."""
    if blend < 1.0:
        previous = _read_deform_weights(target, deform_names)
        for index, values in enumerate(weights):
            if not previous[index]:
                continue
            names = set(values) | set(previous[index])
            weights[index] = {
                name: blend * values.get(name, 0.0)
                      + (1.0 - blend) * previous[index].get(name, 0.0)
                for name in names
            }

    if smooth_iterations and smooth_strength:
        neighbors = [set() for _ in target.data.vertices]
        for edge in target.data.edges:
            a, b = edge.vertices
            neighbors[a].add(b)
            neighbors[b].add(a)
        for _iteration in range(smooth_iterations):
            smoothed = []
            for index, values in enumerate(weights):
                if not neighbors[index]:
                    smoothed.append(values)
                    continue
                names = set(values)
                for neighbor in neighbors[index]:
                    names.update(weights[neighbor])
                smoothed.append({
                    name: (1.0 - smooth_strength) * values.get(name, 0.0)
                          + smooth_strength * sum(
                              weights[neighbor].get(name, 0.0)
                              for neighbor in neighbors[index]
                          ) / len(neighbors[index])
                    for name in names
                })
            weights = smoothed

    finished = []
    for values in weights:
        ranked = sorted(((name, weight) for name, weight in values.items()
                         if weight > 0.0), key=lambda item: item[1], reverse=True)
        if not ranked:
            raise ValueError("Recalculation left vertices without bone weights")
        kept = [ranked[0]] + [item for item in ranked[1:]
                              if item[1] >= minimum_weight]
        if max_influences:
            kept = kept[:max_influences]
        total = sum(weight for _name, weight in kept)
        finished.append({name: weight / total for name, weight in kept})
    return finished


def _write_deform_weights(target, deform_names, weights):
    for group in list(target.vertex_groups):
        if group.name in deform_names:
            target.vertex_groups.remove(group)
    used_names = set().union(*(values.keys() for values in weights))
    groups = {name: target.vertex_groups.new(name=name)
              for name in sorted(used_names)}
    for index, values in enumerate(weights):
        for name, value in values.items():
            groups[name].add([index], value, 'REPLACE')


class BF_OT_AutomaticBoneWeightRecalculation(bpy.types.Operator):
    """Recalculate body weights or transfer body weights to clothing."""
    bl_idname = "boneforge.automatic_bone_weight_recalculation"
    bl_label = "Smart Automatic Weights"
    bl_options = {'REGISTER', 'UNDO'}

    smart: BoolProperty(default=False, options={'HIDDEN', 'SKIP_SAVE'})      # set by the Smart button
    smart_target_name: StringProperty(description='The mesh to give new weights', name="Mesh to Reweight")
    smart_armature_name: StringProperty(description='The armature the mesh is weighted to', name="Existing Armature")
    smart_mode: EnumProperty(description='Body: calculate weights from the bones. Clothing: copy them from a weighted body',
        name="Mesh Type",
        items=(('BODY', "Body", "Calculate automatic weights for the body"),
               ('CLOTHING', "Clothing", "Copy weights from a weighted body")),
        default='BODY',
    )
    smart_source_name: StringProperty(description='The weighted body to copy clothing weights from', name="Weighted Body")

    def invoke(self, context, _event):
        if not self.smart:
            return self.execute(context)
        active = context.active_object
        target = active if active and active.type == 'MESH' else next(
            (obj for obj in context.selected_objects if obj.type == 'MESH'), None)
        if target:
            self.smart_target_name = target.name
            bound = _bound_armature(target)
            if bound:
                self.smart_armature_name = bound.name
        settings = context.scene.boneforge_weight_recalculation
        if not self.smart_armature_name and settings.armature:
            self.smart_armature_name = settings.armature.name
        if settings.source_mesh:
            self.smart_source_name = settings.source_mesh.name
        return context.window_manager.invoke_props_dialog(self, width=380)

    def draw(self, _context):
        if not self.smart:
            return
        layout = self.layout
        layout.prop_search(self, "smart_target_name", _context.scene, "objects")
        layout.prop_search(self, "smart_armature_name", _context.scene, "objects")
        layout.prop(self, "smart_mode", expand=True)
        if self.smart_mode == 'CLOTHING':
            layout.prop_search(self, "smart_source_name", _context.scene, "objects")
        layout.label(text="Smart defaults; a hidden backup is kept", icon='INFO')

    def execute(self, context):
        settings = context.scene.boneforge_weight_recalculation
        target = (context.scene.objects.get(self.smart_target_name)
                  if self.smart else settings.target_mesh) or context.active_object
        if target is None or target.type != 'MESH' or target.name not in context.scene.objects:
            self.report({'ERROR'}, "Choose a mesh to reweight")
            return {'CANCELLED'}
        if target.library or target.data.library:
            self.report({'ERROR'}, "Make the mesh local before recalculating its weights")
            return {'CANCELLED'}
        armature = (context.scene.objects.get(self.smart_armature_name)
                    if self.smart else settings.armature) or _bound_armature(target)
        if armature is None or armature.type != 'ARMATURE' or armature.name not in context.scene.objects:
            self.report({'ERROR'}, "Choose the existing armature for this mesh")
            return {'CANCELLED'}
        if _bound_armature(target) not in (None, armature):
            self.report({'ERROR'}, "Mesh is bound to a different armature")
            return {'CANCELLED'}
        deform_names = {bone.name for bone in armature.data.bones if bone.use_deform}
        if not deform_names or not target.data.vertices:
            self.report({'ERROR'}, "The armature needs deform bones and the mesh needs vertices")
            return {'CANCELLED'}
        source = (context.scene.objects.get(self.smart_source_name)
                  if self.smart else settings.source_mesh)
        mode = self.smart_mode if self.smart else settings.mode
        if mode == 'CLOTHING':
            if source is None or source == target or source.name not in context.scene.objects:
                self.report({'ERROR'}, "Choose a separate, weighted body mesh")
                return {'CANCELLED'}
            if _bound_armature(source) != armature:
                self.report({'ERROR'}, "The weighted body must use the same armature")
                return {'CANCELLED'}
        original_active = context.view_layer.objects.active
        original_selection = tuple(context.selected_objects)
        original_mode = context.mode
        try:
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            body_method = 'AUTO' if self.smart else settings.body_method
            transfer_method = 'SURFACE' if self.smart else settings.transfer_method
            max_distance = 0.0 if self.smart else settings.max_transfer_distance
            weights = (_body_weights(context, target, armature, deform_names, body_method)
                       if mode == 'BODY' else
                       _clothing_weights(target, source, deform_names,
                                         transfer_method, max_distance))
            weights = _finish_recalculated_weights(
                target, deform_names, weights,
                1.0 if self.smart else settings.blend,
                0 if self.smart else settings.smooth_iterations,
                0.0 if self.smart else settings.smooth_strength,
                0 if self.smart else settings.max_influences,
                0.001 if self.smart else settings.minimum_weight,
            )
            backup_name = None
            if self.smart or settings.keep_backup:
                backup = target.copy()
                backup.data = target.data.copy()
                backup.name = f"WEIGHTS_BACKUP_{target.name}"
                (target.users_collection[0] if target.users_collection else context.scene.collection).objects.link(backup)
                backup.hide_set(True)
                backup.hide_render = True
                backup_name = backup.name
            if target.data.users > 1:
                target.data = target.data.copy()
            _write_deform_weights(target, deform_names, weights)
            if not any(mod.type == 'ARMATURE' and mod.object == armature
                       for mod in target.modifiers):
                modifier = target.modifiers.new("Armature", 'ARMATURE')
                modifier.object = armature
            message = f"Recalculated bone weights on {target.name}"
            if backup_name:
                message += f"; original saved as {backup_name}"
            self.report({'INFO'}, message)
            return {'FINISHED'}
        except (RuntimeError, ValueError) as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        finally:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in original_selection:
                if obj.name in context.view_layer.objects:
                    obj.select_set(True)
            if original_active and original_active.name in context.view_layer.objects:
                context.view_layer.objects.active = original_active
            restore_mode = {
                'PAINT_WEIGHT': 'WEIGHT_PAINT',
                'EDIT_MESH': 'EDIT',
                'EDIT_ARMATURE': 'EDIT',
                'POSE': 'POSE',
            }.get(original_mode)
            if restore_mode and bpy.ops.object.mode_set.poll():
                bpy.ops.object.mode_set(mode=restore_mode)


class BONEFORGE_PT_p2b_flood_fill(bpy.types.Panel):
    """Flood fill weight tools panel."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2b_flood_fill"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BoneCraft"

    def draw_header(self, context):
        self.layout.label(text=T("Flood Fill"))

    @classmethod
    def poll(cls, context):
        return context.mode == "PAINT_WEIGHT"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # act first, tune later: the options are the operators' own, adjusted after the click
        # in Adjust Last Operation (owner's UI critique, 2026-10-10)
        col = layout.column(align=True)
        col.operator("boneforge.flood_to_zero", text=T("Flood to 0.0"))
        col.operator("boneforge.flood_to_one", text=T("Flood to 1.0"))
        col.operator("boneforge.flood_to_custom", text=T("Flood to Custom"))
        from boneforge.core.helpers import draw_helper
        draw_helper(layout, context, T("Flood to Custom: set its value and Normalize after flooding, "
                                       "in the Adjust Last Operation panel."))


class BF_OT_FloodToZero(bpy.types.Operator):
    """Set active vertex group to 0.0 on all/selected vertices."""
    bl_idname = "boneforge.flood_to_zero"
    bl_label = "Flood to Zero"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.mode == "PAINT_WEIGHT" and
                context.active_object and
                context.active_object.type == "MESH" and
                context.active_object.vertex_groups.active)

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        vgroup = obj.vertex_groups.active

        affected_count = 0

        # v3.1.6 (M-1): assigned-only walk; vg.remove is also list-tolerant.
        affected_verts = [
            vert.index for vert in mesh.vertices
            if any(vge.group == vgroup.index and vge.weight > 0.0
                   for vge in vert.groups)
        ]
        for vert_idx in affected_verts:
            vgroup.remove([vert_idx])
            affected_count += 1

        self.report({"INFO"}, f"Zeroed {vgroup.name} on {affected_count} vertices")
        return {"FINISHED"}


class BF_OT_FloodToOne(bpy.types.Operator):
    """Set active vertex group to 1.0 and reduce other weights proportionally."""
    bl_idname = "boneforge.flood_to_one"
    bl_label = "Flood to One"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.mode == "PAINT_WEIGHT" and
                context.active_object and
                context.active_object.type == "MESH" and
                context.active_object.vertex_groups.active)

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        vgroup = obj.vertex_groups.active

        affected_count = 0

        # Apply flood to one with proportional reduction
        for vert in mesh.vertices:
            # Get other group weights
            other_weights = {}
            total_other = 0.0

            # v3.1.6 (M-1): assigned-only weight read.
            for vge in vert.groups:
                if vge.group == vgroup.index or vge.weight <= 0.0:
                    continue
                other_weights[vge.group] = vge.weight
                total_other += vge.weight

            # Set active group to 1.0
            vgroup.add([vert.index], 1.0, "REPLACE")

            # Reduce other weights proportionally
            if total_other > 0.0 and total_other > 1e-6:
                scale_factor = 0.0  # Active bone gets 1.0, so remaining budget is 0

                for vg_idx, weight in other_weights.items():
                    new_weight = weight * scale_factor
                    if new_weight > 0.0:
                        obj.vertex_groups[vg_idx].add([vert.index], new_weight, "REPLACE")
                    else:
                        obj.vertex_groups[vg_idx].remove([vert.index])

            affected_count += 1

        self.report({"INFO"}, f"Flooded {vgroup.name} to 1.0 on {affected_count} vertices")
        return {"FINISHED"}


class BF_OT_FloodToCustom(bpy.types.Operator):
    """Set active vertex group to custom float value."""
    bl_idname = "boneforge.flood_to_custom"
    bl_label = "Flood to Custom"
    bl_options = {"REGISTER", "UNDO"}

    value: bpy.props.FloatProperty(
        name="Value",
        description="Weight to flood the active vertex group with",
        min=0.0, max=1.0, default=0.5,
    )
    normalize: bpy.props.BoolProperty(
        name="Normalize",
        description="Normalize each vertex's weights to a total of 1 after flooding",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return (context.mode == "PAINT_WEIGHT" and
                context.active_object and
                context.active_object.type == "MESH" and
                context.active_object.vertex_groups.active)

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        scene = context.scene
        vgroup = obj.vertex_groups.active

        custom_value = self.value
        normalize = self.normalize

        affected_count = 0

        # Flood to custom value
        for vert in mesh.vertices:
            if custom_value > 0.0:
                vgroup.add([vert.index], custom_value, "REPLACE")
                affected_count += 1

        # Normalize if requested
        if normalize and custom_value > 0.0:
            for vert in mesh.vertices:
                total_weight = 0.0
                weights = {}

                # v3.1.6 (M-1): assigned-only weight read.
                weights = {vge.group: vge.weight
                           for vge in vert.groups if vge.weight > 0.0}
                total_weight = sum(weights.values())

                if total_weight > 0.0 and abs(total_weight - 1.0) > 0.001:
                    inv = 1.0 / total_weight
                    for vg_idx, weight in weights.items():
                        obj.vertex_groups[vg_idx].add(
                            [vert.index], weight * inv, "REPLACE",
                        )

        self.report({"INFO"}, f"Flooded {vgroup.name} to {custom_value} on {affected_count} vertices")
        return {"FINISHED"}


def register():
    """Register flood fill tool classes and properties."""
    bpy.utils.register_class(BF_WeightRecalculationSettings)
    bpy.utils.register_class(BF_OT_AutomaticBoneWeightRecalculation)
    bpy.types.Scene.boneforge_weight_recalculation = PointerProperty(
        type=BF_WeightRecalculationSettings)
    bpy.utils.register_class(BONEFORGE_PT_p2b_flood_fill)
    bpy.utils.register_class(BF_OT_FloodToZero)
    bpy.utils.register_class(BF_OT_FloodToOne)
    bpy.utils.register_class(BF_OT_FloodToCustom)

    # Scene properties
    bpy.types.Scene.boneforge_flood_custom_value = FloatProperty(
        name="Custom Value",
        description="Custom weight value for flood",
        min=0.0,
        max=1.0,
        default=0.5
    )

    bpy.types.Scene.boneforge_flood_normalize = BoolProperty(
        name="Normalize",
        description="Normalize weights after flooding",
        default=False
    )


def unregister():
    """Unregister flood fill tool classes and properties."""
    if hasattr(bpy.types.Scene, "boneforge_weight_recalculation"):
        del bpy.types.Scene.boneforge_weight_recalculation
    bpy.utils.unregister_class(BF_OT_AutomaticBoneWeightRecalculation)
    bpy.utils.unregister_class(BF_WeightRecalculationSettings)
    bpy.utils.unregister_class(BONEFORGE_PT_p2b_flood_fill)
    bpy.utils.unregister_class(BF_OT_FloodToZero)
    bpy.utils.unregister_class(BF_OT_FloodToOne)
    bpy.utils.unregister_class(BF_OT_FloodToCustom)

    # Clean up properties
    if hasattr(bpy.types.Scene, "boneforge_flood_custom_value"):
        del bpy.types.Scene.boneforge_flood_custom_value
    if hasattr(bpy.types.Scene, "boneforge_flood_normalize"):
        del bpy.types.Scene.boneforge_flood_normalize
