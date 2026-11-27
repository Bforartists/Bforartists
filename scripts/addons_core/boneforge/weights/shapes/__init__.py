"""BoneCraft Control Shape Library — Procedurally generated control shapes for pose bones."""
import math
import bpy
from bpy.types import Panel, Operator, UIList, PropertyGroup
from bpy.props import StringProperty, CollectionProperty

from boneforge.i18n import T

# ============================================================================
# Shape Generator Functions
# ============================================================================

def generate_circle(radius=1.0, segments=16):
    """Generate circle vertices and edges."""
    verts = []
    for i in range(segments):
        angle = (i / segments) * 2 * math.pi
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        verts.append((x, y, 0))
    edges = [(i, (i + 1) % segments) for i in range(segments)]
    return verts, edges

def generate_circle_small():
    """Small circle (0.01 radius, 16 segments)."""
    return generate_circle(radius=0.01, segments=16)

def generate_circle_medium():
    """Medium circle (0.02 radius, 16 segments)."""
    return generate_circle(radius=0.02, segments=16)

def generate_circle_large():
    """Large circle (0.1 radius, 24 segments)."""
    return generate_circle(radius=0.1, segments=24)

def generate_square(size=0.05, segments_per_side=4):
    """Generate square vertices and edges."""
    half = size / 2
    verts = []
    # Top edge
    for i in range(segments_per_side):
        t = i / (segments_per_side - 1) if segments_per_side > 1 else 0
        verts.append((-half + t * size, half, 0))
    # Right edge
    for i in range(1, segments_per_side):
        t = i / (segments_per_side - 1)
        verts.append((half, half - t * size, 0))
    # Bottom edge
    for i in range(1, segments_per_side):
        t = i / (segments_per_side - 1)
        verts.append((half - t * size, -half, 0))
    # Left edge
    for i in range(1, segments_per_side - 1):
        t = i / (segments_per_side - 1)
        verts.append((-half, -half + t * size, 0))
    edges = [(i, (i + 1) % len(verts)) for i in range(len(verts))]
    return verts, edges

def generate_diamond(size=0.015):
    """Generate diamond shape (rotated square)."""
    verts = [
        (size, 0, 0),      # right
        (0, size, 0),      # top
        (-size, 0, 0),     # left
        (0, -size, 0),     # bottom
    ]
    edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    return verts, edges

def generate_arrow_single(length=0.1, width=0.03):
    """Generate single-head arrow."""
    verts = [
        (0, 0, 0),                                    # base
        (-width, -width, 0),                          # left back
        (0, -width, 0),                               # back
        (width, -width, 0),                           # right back
        (width, 0, 0),                                # right base
        (width * 0.5, 0, 0),                          # right mid
        (width * 0.5, length, 0),                     # right arrowhead
        (0, length * 1.2, 0),                         # tip
        (-width * 0.5, length, 0),                    # left arrowhead
        (-width * 0.5, 0, 0),                         # left mid
    ]
    edges = [(i, (i + 1) % len(verts)) for i in range(len(verts))]
    return verts, edges

def generate_arrow_double(length=0.1, width=0.03):
    """Generate double-head arrow."""
    half_len = length / 2
    verts = [
        (-width * 0.5, -length, 0),                   # left arrow top
        (0, -length * 1.2, 0),                        # tip top
        (width * 0.5, -length, 0),                    # right arrow top
        (width, -length, 0),                          # right mid top
        (width, -width, 0),                           # right back
        (0, 0, 0),                                    # center
        (-width, -width, 0),                          # left back
        (-width, -length, 0),                         # left mid top
        (width, length, 0),                           # right mid bottom
        (width * 0.5, length, 0),                     # right arrow bottom
        (0, length * 1.2, 0),                         # tip bottom
        (-width * 0.5, length, 0),                    # left arrow bottom
        (-width, length, 0),                          # left mid bottom
    ]
    edges = [(i, (i + 1) % len(verts)) for i in range(len(verts))]
    return verts, edges

def generate_arrow_curved(length=0.1, width=0.03, curve=0.02):
    """Generate curved arrow."""
    verts = []
    segments = 16
    for i in range(segments):
        t = i / (segments - 1)
        x = -width / 2 + t * width
        y = -length / 2 + t * length
        z = math.sin(t * math.pi) * curve
        verts.append((x, y, z))
    # Arrowhead
    verts.append((width * 0.3, length * 0.5, 0))
    verts.append((0, length * 0.6, 0))
    verts.append((-width * 0.3, length * 0.5, 0))
    edges = [(i, (i + 1) % len(verts)) for i in range(len(verts))]
    return verts, edges

def generate_locator_cross(size=0.05):
    """Generate cross/crosshair locator."""
    verts = [
        (0, 0, 0),                 # center
        (size, 0, 0),              # right
        (-size, 0, 0),             # left
        (0, size, 0),              # top
        (0, -size, 0),             # bottom
        (0, 0, size),              # front
        (0, 0, -size),             # back
    ]
    edges = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6)]
    return verts, edges

def generate_locator_box(size=0.05):
    """Generate box locator."""
    verts = [
        (-size, -size, -size), (size, -size, -size),   # 0-1
        (size, size, -size), (-size, size, -size),     # 2-3
        (-size, -size, size), (size, -size, size),     # 4-5
        (size, size, size), (-size, size, size),       # 6-7
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),  # back face
        (4, 5), (5, 6), (6, 7), (7, 4),  # front face
        (0, 4), (1, 5), (2, 6), (3, 7),  # vertical edges
    ]
    return verts, edges

def generate_sphere_wire(radius=0.05, rings=6, segments=8):
    """Generate wireframe sphere."""
    verts = []
    edges = []
    vert_idx = 0

    # Pole vertices
    verts.append((0, 0, radius))  # north pole
    north_pole_idx = vert_idx
    vert_idx += 1

    # Rings
    ring_starts = []
    for ring in range(1, rings):
        angle = (ring / rings) * math.pi
        y = radius * math.cos(angle)
        r = radius * math.sin(angle)
        ring_start = vert_idx
        ring_starts.append((ring_start, r, y))
        for seg in range(segments):
            theta = (seg / segments) * 2 * math.pi
            x = r * math.cos(theta)
            z = r * math.sin(theta)
            verts.append((x, y, z))
            vert_idx += 1

    verts.append((0, -radius, 0))  # south pole
    south_pole_idx = vert_idx

    # Connect north pole
    for seg in range(segments):
        edges.append((north_pole_idx, ring_starts[0][0] + seg))
        edges.append((north_pole_idx, ring_starts[0][0] + (seg + 1) % segments))

    # Connect rings
    for ring_idx, (ring_start, _, _) in enumerate(ring_starts[:-1]):
        next_ring_start = ring_starts[ring_idx + 1][0]
        for seg in range(segments):
            curr_v = ring_start + seg
            next_v = ring_start + (seg + 1) % segments
            curr_next_v = next_ring_start + seg
            next_next_v = next_ring_start + (seg + 1) % segments
            edges.append((curr_v, next_v))
            edges.append((curr_v, curr_next_v))

    # Connect south pole
    last_ring_start = ring_starts[-1][0]
    for seg in range(segments):
        edges.append((south_pole_idx, last_ring_start + seg))

    return verts, edges

def generate_cube_wire(size=0.05):
    """Generate wireframe cube."""
    verts = [
        (-size, -size, -size), (size, -size, -size),
        (size, size, -size), (-size, size, -size),
        (-size, -size, size), (size, -size, size),
        (size, size, size), (-size, size, size),
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]
    return verts, edges

def generate_pyramid(size=0.05, height=0.1):
    """Generate pyramid shape."""
    verts = [
        (-size, 0, -size), (size, 0, -size),
        (size, 0, size), (-size, 0, size),
        (0, height, 0),
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (0, 4), (1, 4), (2, 4), (3, 4),
    ]
    return verts, edges

def generate_cylinder_wire(radius=0.05, height=0.1, segments=16):
    """Generate wireframe cylinder."""
    verts = []
    edges = []
    half_h = height / 2

    # Bottom circle
    bottom_start = 0
    for i in range(segments):
        angle = (i / segments) * 2 * math.pi
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        verts.append((x, -half_h, z))

    # Top circle
    top_start = segments
    for i in range(segments):
        angle = (i / segments) * 2 * math.pi
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        verts.append((x, half_h, z))

    # Bottom edges
    for i in range(segments):
        edges.append((bottom_start + i, bottom_start + (i + 1) % segments))

    # Top edges
    for i in range(segments):
        edges.append((top_start + i, top_start + (i + 1) % segments))

    # Vertical edges
    for i in range(0, segments, 4):
        edges.append((bottom_start + i, top_start + i))

    return verts, edges

def generate_hinge(size=0.05):
    """Generate hinge shape."""
    verts = [
        (-size, -size, -size), (size, -size, -size),
        (size, size, -size), (-size, size, -size),
        (-size, -size, size * 0.5), (size, -size, size * 0.5),
        (size, size, size * 0.5), (-size, size, size * 0.5),
        (0, -size, size), (0, size, size),
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
        (4, 8), (5, 8), (6, 9), (7, 9),
        (8, 9),
    ]
    return verts, edges

def generate_gear(inner_radius=0.03, outer_radius=0.08, teeth=8):
    """Generate gear shape."""
    verts = []
    edges = []
    tooth_height = outer_radius - inner_radius

    for tooth in range(teeth * 2):
        angle = (tooth / (teeth * 2)) * 2 * math.pi
        if tooth % 2 == 0:
            r = outer_radius
        else:
            r = inner_radius + tooth_height * 0.7
        x = r * math.cos(angle)
        z = r * math.sin(angle)
        verts.append((x, 0, z))
        edges.append((tooth, (tooth + 1) % (teeth * 2)))

    # Inner circle
    inner_segments = 8
    inner_start = len(verts)
    for i in range(inner_segments):
        angle = (i / inner_segments) * 2 * math.pi
        x = inner_radius * 0.5 * math.cos(angle)
        z = inner_radius * 0.5 * math.sin(angle)
        verts.append((x, 0, z))
        edges.append((inner_start + i, inner_start + (i + 1) % inner_segments))

    return verts, edges

def generate_foot(size=0.05):
    """Generate foot shape."""
    verts = [
        (-size * 0.8, 0, -size * 1.2),
        (size * 0.8, 0, -size * 1.2),
        (size, 0, -size),
        (size, 0, size * 0.5),
        (size * 0.5, 0, size),
        (-size * 0.5, 0, size),
        (-size, 0, size * 0.5),
        (-size, 0, -size),
    ]
    edges = [(i, (i + 1) % len(verts)) for i in range(len(verts))]
    return verts, edges

def generate_hand_flat(size=0.03):
    """Generate flat hand shape."""
    verts = [
        (0, 0, 0),
        (size * 2, size, 0),
        (size * 3, size * 2, 0),
        (size * 2.5, size * 3, 0),
        (size, size * 3, 0),
        (-size, size * 2.5, 0),
        (-size * 1.5, size, 0),
        (-size, 0, 0),
    ]
    edges = [(i, (i + 1) % len(verts)) for i in range(len(verts))]
    return verts, edges

def generate_hand_grip(size=0.04):
    """Generate hand grip shape."""
    verts = []
    # Palm base
    verts.extend([
        (-size, -size, 0),
        (size, -size, 0),
        (size, size, 0),
        (-size, size, 0),
    ])
    # Fingers
    for finger in range(4):
        x_offset = -size + (size * 0.5 * finger)
        verts.extend([
            (x_offset, size, 0),
            (x_offset, size * 2, 0),
        ])
    edges = [(i, (i + 1) % len(verts)) for i in range(len(verts))]
    return verts, edges

def generate_hip(size=0.08):
    """Generate hip control shape."""
    verts = []
    segments = 12
    for i in range(segments):
        angle = (i / segments) * 2 * math.pi
        x = size * math.cos(angle)
        z = size * math.sin(angle) * 0.7
        verts.append((x, 0, z))
    edges = [(i, (i + 1) % segments) for i in range(segments)]
    return verts, edges

def generate_chest(size=0.1):
    """Generate chest control shape."""
    verts = [
        (-size, 0, -size * 0.5),
        (-size, 0, size * 0.5),
        (0, 0, size),
        (size, 0, size * 0.5),
        (size, 0, -size * 0.5),
        (0, 0, -size * 0.8),
    ]
    edges = [(i, (i + 1) % len(verts)) for i in range(len(verts))]
    return verts, edges

def generate_spine_shape(size=0.06):
    """Generate spine segment shape."""
    verts = []
    for i in range(4):
        angle = (i / 4) * 2 * math.pi
        x = size * math.cos(angle) * (1.0 - i * 0.1)
        z = size * math.sin(angle) * (1.0 - i * 0.1)
        verts.append((x, i * size * 0.5, z))
    verts.extend([
        (0, size * 2, 0),
        (0, size * 2.5, 0),
    ])
    edges = [(i, (i + 1) % len(verts)) for i in range(len(verts))]
    return verts, edges

def generate_head_shape(size=0.1):
    """Generate head control shape."""
    verts = []
    segments = 16
    for i in range(segments):
        angle = (i / segments) * 2 * math.pi
        x = size * math.cos(angle)
        z = size * math.sin(angle) * 0.8
        verts.append((x, size * 0.5, z))
    edges = [(i, (i + 1) % segments) for i in range(segments)]
    return verts, edges

def generate_eye(size=0.02):
    """Generate eye control shape."""
    verts, edges = generate_circle(radius=size, segments=8)
    return verts, edges

def generate_lip(size=0.03):
    """Generate lip control shape."""
    verts = [
        (-size * 1.5, 0, 0),
        (-size * 0.5, size, 0),
        (size * 0.5, size, 0),
        (size * 1.5, 0, 0),
        (size * 0.5, -size * 0.5, 0),
        (-size * 0.5, -size * 0.5, 0),
    ]
    edges = [(i, (i + 1) % len(verts)) for i in range(len(verts))]
    return verts, edges

def generate_root(size=0.1):
    """Generate root/master control shape."""
    verts, edges = generate_circle(radius=size, segments=24)
    return verts, edges

# Shape registry
SHAPES = {
    'circle': generate_circle,
    'circle_small': generate_circle_small,
    'circle_medium': generate_circle_medium,
    'circle_large': generate_circle_large,
    'square': generate_square,
    'diamond': generate_diamond,
    'arrow_single': generate_arrow_single,
    'arrow_double': generate_arrow_double,
    'arrow_curved': generate_arrow_curved,
    'locator_cross': generate_locator_cross,
    'locator_box': generate_locator_box,
    'sphere_wire': generate_sphere_wire,
    'cube_wire': generate_cube_wire,
    'pyramid': generate_pyramid,
    'cylinder_wire': generate_cylinder_wire,
    'hinge': generate_hinge,
    'gear': generate_gear,
    'foot': generate_foot,
    'hand_flat': generate_hand_flat,
    'hand_grip': generate_hand_grip,
    'hip': generate_hip,
    'chest': generate_chest,
    'spine_shape': generate_spine_shape,
    'head_shape': generate_head_shape,
    'eye': generate_eye,
    'lip': generate_lip,
    'root': generate_root,
}

# ============================================================================
# Public API
# ============================================================================

def get_or_create_shape(name, armature=None):
    """Get or create a shape object. Returns shape vertices and edges."""
    if name not in SHAPES:
        return None, None
    return SHAPES[name]()

def create_shape_object(name, verts, edges, location=(0, 0, 0)):
    """Create a Blender mesh object from shape data."""
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, edges, [])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    bpy.context.collection.objects.link(obj)
    return obj

# ============================================================================
# Property Groups
# ============================================================================

class BONEFORGE_ShapeItem(PropertyGroup):
    """Shape library item."""
    name: StringProperty(name="Name")
    display_name: StringProperty(name="Display", default="")

# ============================================================================
# Operators
# ============================================================================

class BF_OT_ApplyShape(Operator):
    """Apply selected shape to active pose bone."""
    bl_idname = "boneforge.apply_shape"
    bl_label = "Apply Shape"
    bl_options = {'REGISTER', 'UNDO'}

    shape_name: StringProperty(options={'HIDDEN', 'SKIP_SAVE'}, name="Shape", default="circle")

    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' and
                context.active_pose_bone is not None and
                context.active_object and
                context.active_object.type == 'ARMATURE')

    def execute(self, context):
        bone = context.active_pose_bone
        verts, edges = get_or_create_shape(self.shape_name)
        if verts is None:
            self.report({'ERROR'}, f"Shape {self.shape_name} not found")
            return {'CANCELLED'}

        # Get bone length for auto-scaling
        bone_length = (bone.tail - bone.head).length

        # Create shape object
        shape_obj = create_shape_object(
            f"{bone.name}_{self.shape_name}",
            verts, edges,
            location=bone.head
        )

        # Auto-scale to bone length
        if bone_length > 0:
            scale_factor = bone_length / 0.1
            shape_obj.scale = (scale_factor, scale_factor, scale_factor)

        # Store reference to shape on bone
        bone['boneforge_shape_object'] = shape_obj.name

        self.report({'INFO'}, f"Applied {self.shape_name} to {bone.name}")
        return {'FINISHED'}

class BF_OT_CopyShapeFrom(Operator):
    """Copy shape from scene object and apply to active bone."""
    bl_idname = "boneforge.copy_shape_from"
    bl_label = "Copy Shape From Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'POSE' and
                context.active_pose_bone is not None and
                context.active_object and
                context.active_object.type == 'ARMATURE')

    def execute(self, context):
        bone = context.active_pose_bone

        # Find selected non-armature object
        source_obj = None
        for obj in context.selected_objects:
            if obj.type == 'MESH' and obj != context.active_object:
                source_obj = obj
                break

        if source_obj is None:
            self.report({'ERROR'}, "Select a mesh object as source")
            return {'CANCELLED'}

        if source_obj.data.vertices.__len__() == 0:
            self.report({'ERROR'}, "Source object has no vertices")
            return {'CANCELLED'}

        # Copy shape data
        verts = [tuple(v.co) for v in source_obj.data.vertices]
        edges = [tuple(e.vertices) for e in source_obj.data.edges]

        # Create new shape object
        shape_name = f"{bone.name}_custom_shape"
        shape_obj = create_shape_object(shape_name, verts, edges, bone.head)

        bone['boneforge_shape_object'] = shape_obj.name
        self.report({'INFO'}, f"Copied shape to {bone.name}")
        return {'FINISHED'}

class BF_OT_SaveShapeToLibrary(Operator):
    """Save current shape to library."""
    bl_idname = "boneforge.save_shape_to_library"
    bl_label = "Save Shape to Library"
    bl_options = {'REGISTER', 'UNDO'}

    shape_name: StringProperty(description='Name to save the shape under', name="Shape Name", default="new_shape")

    def execute(self, context):
        import os
        import json

        # Get active pose bone shape
        bone = context.active_pose_bone
        if not bone or 'boneforge_shape_object' not in bone:
            self.report({'ERROR'}, "No shape object on active bone")
            return {'CANCELLED'}

        shape_obj_name = bone['boneforge_shape_object']
        shape_obj = bpy.data.objects.get(shape_obj_name)
        if not shape_obj or shape_obj.type != 'MESH':
            self.report({'ERROR'}, "Shape object not found or not a mesh")
            return {'CANCELLED'}

        # Use fallback library path
        lib_dir = os.path.join(bpy.app.tempdir, 'boneforge_shapes')
        try:
            os.makedirs(lib_dir, exist_ok=True)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create library directory: {str(e)}")
            return {'CANCELLED'}

        # Serialize shape data
        verts = [tuple(v.co) for v in shape_obj.data.vertices]
        edges = [tuple(e.vertices) for e in shape_obj.data.edges]
        shape_data = {
            'name': self.shape_name,
            'vertices': verts,
            'edges': edges
        }

        # Write to file
        file_path = os.path.join(lib_dir, f"{self.shape_name}.json")
        try:
            with open(file_path, 'w') as f:
                json.dump(shape_data, f, indent=2)
            self.report({'INFO'}, f"Shape '{self.shape_name}' saved to {file_path}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save shape: {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}

# ============================================================================
# UI List
# ============================================================================

class BONEFORGE_UL_ShapeLibrary(UIList):
    """Shape library list."""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name, icon='MESH_DATA')

# ============================================================================
# Panels
# ============================================================================

class BONEFORGE_PT_p2b_shape_library(Panel):
    """Shape library panel in pose mode."""
    bl_label = " "
    bl_idname = "BONEFORGE_PT_p2b_shape_library"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BoneCraft"

    def draw_header(self, context):
        self.layout.label(text=T("Shape Library"))

    @classmethod
    def poll(cls, context):
        return False  # Orphan standalone — no sidebar delegate; suppressed to avoid blank header

    def draw(self, context):
        layout = self.layout
        layout.label(text=T("Control Shapes:"))

        col = layout.column(align=True)
        shape_names = list(SHAPES.keys())

        # Grid layout for shapes
        for i, shape_name in enumerate(shape_names):
            if i % 3 == 0:
                row = layout.row(align=True)

            row.operator(
                "boneforge.apply_shape",
                text=shape_name[:6],
                icon='SHAPEKEY_DATA'
            ).shape_name = shape_name

        layout.separator()
        layout.operator("boneforge.copy_shape_from", icon='COPYDOWN')
        layout.operator("boneforge.save_shape_to_library", icon='FILE_TICK')

# ============================================================================
# Registration
# ============================================================================

_classes = [
    BONEFORGE_ShapeItem,
    BF_OT_ApplyShape,
    BF_OT_CopyShapeFrom,
    BF_OT_SaveShapeToLibrary,
    BONEFORGE_UL_ShapeLibrary,
    BONEFORGE_PT_p2b_shape_library,
]

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
