import bpy
import math
import os
from mathutils import Vector, Matrix

from ...functions.mesh import (
    ensure_attribute,
    shade_smooth_by_angle,
)
from ...functions.modifier import (
    add_modifier_asset,
    update_modifier_input,
)


#### ------------------------------ CLASSES ------------------------------ ####

class Selection:
    """Storage of viable cannvas objects and their Boolean modifiers."""

    def __init__(self, selected, active):
        self.selected: list = selected
        self.active = active
        self.modifiers = {}


class Mouse:
    """Mouse positions throughout different phases of the modal operator."""

    def __init__(self):
        self.initial = Vector()
        self.current = Vector()
        self.extrude = Vector()
        self.cached = Vector() # Used for custom modifier keys.

        self.current_3d = Vector()
        self.cached_3d = Vector()

    @classmethod
    def from_event(self, event):
        self.initial = Vector((event.mouse_region_x, event.mouse_region_y))
        self.current = Vector((event.mouse_region_x, event.mouse_region_y))

        self.current_3d = None
        return self


class Workplane:
    """Local 3D coordinate system used as the drawing plane for creating shapes."""

    def __init__(self, matrix, location, normal):
        self.matrix: Matrix = matrix       # full 4x4 transform matrix.
        self.location: Vector = location   # origin point of the plane in world space.
        self.normal: Vector = normal       # perpendicular direction of the plane.


class Cutter:
    """Object created for cutting, as well as it's `bmesh`, and other properties."""

    def __init__(self, obj, mesh, bm, faces, verts):
        self.obj = obj
        self.mesh = mesh
        self.bm = bm
        self.faces: list = faces
        self.verts: list = verts
        self.center = Vector() # Center of the geometry.


# Effects
class Effects:

    def __init__(self):
        self.array = None
        self.bevel = None
        self.smooth = None
        self.weld = None

    def from_invoke(self, cls, context):
        """Add modifiers to the cutter object during invoke, if they're enabled on tool level."""

        # Smooth by Angle
        if cls.auto_smooth:
            self.add_auto_smooth_modifier(cls, context)

        # Array
        if cls.rows > 1 or cls.columns > 1:
            self.add_array_modifier(cls)
        else:
            self.array = None

        # Bevel
        if hasattr(cls, "use_bevel") and cls.use_bevel:
            self.add_bevel_modifier(cls, affect='VERTICES')
        else:
            self.bevel = None

        return self

    def update(self, cls, effect):
        """Update cutter modifiers during modal."""

        # Update array count.
        if effect == "ARRAY_COUNT":
            if self.array is None:
                self.add_array_modifier(cls)

            else:
                if cls.columns > 1 or cls.rows > 1:
                    update_modifier_input(self.array, "Socket_2", cls.columns)
                    update_modifier_input(self.array, "Socket_3", cls.rows)

                # Remove modifier if it's no longer needed.
                if cls.columns == 1 and cls.rows == 1:
                    cls.cutter.obj.modifiers.remove(self.array)
                    self.array = None

        # Update array gap.
        if effect == "ARRAY_GAP":
            if cls.columns > 1 or cls.rows > 1:
                if self.array is not None:
                    update_modifier_input(self.array, "Socket_4", cls.gap)

                    # NOTE: Force the modifier to update in viewport when key is pressed.
                    self.array.show_viewport = False
                    self.array.show_viewport = True

        # Update bevel width & segments
        if effect == 'BEVEL':
            self.bevel.segments = cls.bevel_segments
            self.bevel.width = cls.bevel_width


    # Array
    def add_array_modifier(self, cls):
        """Adds an array modifier(s) on the cutter object."""

        cutter = cls.cutter.obj

        # Load geometry nodes modifier asset.
        if self.array is None:
            root = os.path.abspath(os.path.join(__file__, "..", "..", ".."))
            assets_path = os.path.join(root, "assets.blend")
            mod = add_modifier_asset(cutter, path=assets_path, asset="cutter_array")

        if not mod:
            cls.report({'WARNING'}, "Array modifier cannot be loaded for cutter")
            return

        # Columns
        if cls.columns > 1:
            update_modifier_input(mod, "Socket_2", cls.columns)

        # Rows
        if cls.rows > 1:
            update_modifier_input(mod, "Socket_3", cls.rows)

        # Gap
        update_modifier_input(mod, "Socket_4", cls.gap)

        mod.use_pin_to_last = True
        self.array = mod


    # Bevel
    def add_bevel_modifier(self, cls, affect='EDGES'):
        """Adds a bevel modifier on the cutter object."""

        cutter = cls.cutter.obj
        bm = cls.cutter.bm
        faces = cls.cutter.faces

        mod = cutter.modifiers.new("cutter_bevel", 'BEVEL')
        mod.limit_method = 'WEIGHT'
        mod.segments = cls.bevel_segments
        mod.width = cls.bevel_width
        mod.profile = cls.bevel_profile

        """NOTE:
        In order to allow beveling during the shape creation phase,
        when we only have one face, we need to bevel vertices instead of edges,
        and then change it to edges when cutter is manifold (and transfer weights).
        """
        mod.affect = affect
        if affect == 'EDGES':
            attr = ensure_attribute(bm, "bevel_weight_edge", 'EDGE')

            # Mark all edges except ones belonging to original and extruded face.
            for edge in bm.edges:
                if edge in faces[0].edges:
                    continue
                if edge in faces[-1].edges:
                    continue
                edge[attr] = 1.0

        elif affect == 'VERTICES':
            attr = ensure_attribute(bm, "bevel_weight_vert", 'VERTEX')
            face = cls.cutter.faces[0]

            # Mark vertices of the original face.
            verts = [vert for vert in face.verts]
            for v in verts:
                v[attr] = 1.0

        # Add Weld modifier (necessary for merging overlapping vertices).
        # Otherwise live cut produces corrupted booleans because of non-manifold geometry.
        self.add_weld_modifier(cls)

        self.bevel = mod


    def transfer_bevel_weights(self, cls):
        """Transfer bevel weights from vertices to edges."""

        if not cls.use_bevel:
            return

        bm = cls.cutter.bm
        faces = cls.cutter.faces

        # Ensure default edge weights attribute.
        edge_attr = ensure_attribute(bm, "bevel_weight_edge", 'EDGE')

        for edge in bm.edges:
            if edge in faces[0].edges:
                continue
            if edge in faces[-1].edges:
                continue
            edge[edge_attr] = 1.0

        self.bevel.affect = 'EDGES'


    # Smooth by Angle
    def add_auto_smooth_modifier(self, cls, context):
        """Adds a 'Smooth by Angle' modifier on the cutter object (a.k.a. Auto Smooth)."""

        obj = cls.cutter.obj
        mesh = cls.cutter.mesh
        bm = cls.cutter.bm

        modifier_asset_path = "nodes\\geometry_nodes_essentials.blend\\NodeTree\\Smooth by Angle"
        modifier_asset_file = modifier_asset_path[:modifier_asset_path.find(".blend") + 6]
        modifier_asset_name = modifier_asset_path.rsplit("\\", 1)[1]

        # Try adding modifier with `bpy.ops` operator(s) first.
        context_override = {
            "object": obj,
            "active_object": obj,
            "selected_objects": [obj],
            "selected_editable_objects": [obj],
        }
        with context.temp_override(**context_override):
            try:
                # Try adding the modifier with `shade_auto_smooth` operator.
                bpy.ops.object.shade_auto_smooth()
            except:
                # Try adding the modifier with path to Essentials library.
                bpy.ops.object.modifier_add_node_group(asset_library_type="ESSENTIALS",
                                                       asset_library_identifier="",
                                                       relative_asset_identifier=modifier_asset_path)

        mod = obj.modifiers.active

        # Try loading the node group manually if `bpy.ops` operators failed.
        if mod is None:
            dir = os.path.join(os.path.dirname(bpy.app.binary_path), "5.0", "datafiles", "assets")
            assets_path = os.path.join(dir, modifier_asset_file)
            mod = add_modifier_asset(obj, path=assets_path, asset=modifier_asset_name)

        # Resort to destructive editing if everything fails.
        if mod is None:
            print("Smooth by Angle modifier couldn't be added.")
            print("Destructively marking sharp edges and smooth faces in the mesh")
            shade_smooth_by_angle(bm, mesh, angle=math.degrees(cls.sharp_angle))
        else:
            # Set smoothing angle (necessary for all methods except `shade_auto_smooth()`).
            for face in bm.faces:
                face.smooth = True
            bm.to_mesh(mesh)

            mod.use_pin_to_last = True
            update_modifier_input(mod, "Input_1", cls.sharp_angle)

            self.smooth = mod


    # Weld
    def add_weld_modifier(self, cls):
        if self.weld is None:
            self.weld = cls.cutter.obj.modifiers.new("cutter_weld", 'WELD')
        return self.weld
