"""BoneCraft Mannequin Generator — primitive mesh from armature bones.

v3.8.1: bug fix and cleanup pass.

The mannequin is a primitive mesh produced procedurally from an
armature's bones, intended for previewing rig deformation before a
real character mesh exists, or as a sculpting base for stylized work.
This is preview geometry, not a finished asset.

Three generation modes layer on top of one another:

* Universal — walks every bone, producing one capsule per bone.
  Works on any armature (Rigify, custom, imported FBX) but produces
  visible junk on Rigify *control* rigs because every controller bone
  also gets a capsule.

* Filtered — adds a deform-aware predicate. Skips bones where
  ``use_deform=False``, skips bones whose names match common controller
  prefixes (CTRL/MCH/ORG/IK/_) or end-suffixes (_target/_pole/_pivot),
  skips bones in collections named like Controllers/MCH/ORG, and
  filters out tiny utility bones below a length threshold. Falls back
  to Universal behaviour if the filter rejects every bone.

* Anatomical — replaces capsules with smarter primitives for bones
  whose names match a humanoid pattern library: head -> sphere,
  hand -> paddle, foot -> wedge, finger/thumb -> tapered cylinder,
  tail -> long taper, wing -> aerofoil. Falls back to Filtered
  behaviour for any bone the pattern library does not recognise. If
  no anatomy patterns match at all, the whole generator falls back to
  Filtered with a status report so the user is never left without
  output.

Optional v2.0 features stack on top of Anatomical mode:
* Unified volumes — walks parent/child chains and produces single
  tapered volumes across spine and limb chains rather than stacked
  per-bone primitives. Smoother silhouette without joint seams.

Output options:
* Per-bone separate objects — one mesh object per bone primitive.
* Joined single object — one non-manifold combined mesh.
* Joined + voxel remesh — single closed manifold surface,
  sculpting-ready for stylized work.

Body-type presets bundle proportion multipliers into one click.
Per-region scales (Torso / Limbs / Extremities) override the preset
for fine-tuning. The display style toggle sets a viewport shading
treatment that visually marks the output as preview geometry.

The unanimous renaming addition from the brainstorm council applies
throughout: every user-visible label and tooltip uses
*Universal / Filtered / Anatomical*, never *Tier 1 / 2 / 3*.
"""

from __future__ import annotations

import logging
import math
import re
from typing import Optional

import bpy
import bmesh
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
)
from bpy.types import Operator, Panel
from mathutils import Matrix, Vector

from boneforge.i18n import T

logger = logging.getLogger(__name__)


# ── Module-level constants ──────────────────────────────────────

MANNEQUIN_COLLECTION_NAME = "BoneCraft Mannequins"

# Custom property markers so we can find/replace existing mannequins
# without resorting to name-string matching.
PROP_IS_MANNEQUIN = "boneforge_is_mannequin"
PROP_SOURCE_ARMATURE = "boneforge_mannequin_source_armature"
PROP_LAST_PARAMS_PREFIX = "boneforge_mannequin_last_params"
PROP_DOWNGRADE_FLAG = "boneforge_mannequin_downgraded"

# Mode identifiers — these strings are also the EnumProperty values.
MODE_UNIVERSAL = "UNIVERSAL"
MODE_FILTERED = "FILTERED"
MODE_ANATOMICAL = "ANATOMICAL"

MODE_ITEMS = (
    (MODE_UNIVERSAL, "Universal",
     "Capsule per bone. Works on any armature. Produces extra geometry "
     "around controller bones on Rigify control rigs."),
    (MODE_FILTERED, "Filtered",
     "Skips controllers and non-deform bones. Best for Rigify control "
     "rigs and any armature that flags deform bones correctly."),
    (MODE_ANATOMICAL, "Anatomical",
     "Smart primitives for humanoid heads, hands, feet, and fingers. "
     "Falls back to Filtered for unrecognised bones."),
)

# Density presets drive ring/length segment counts on capsules and
# resolution on spheres. Cost framing in the tooltip is intentional.
DENSITY_LOW = "LOW"
DENSITY_MEDIUM = "MEDIUM"
DENSITY_HIGH = "HIGH"

DENSITY_ITEMS = (
    (DENSITY_LOW, "Low",
     "6 ring segments. Fastest to generate, blocky silhouette. "
     "Use for animation blocking or quick previews."),
    (DENSITY_MEDIUM, "Medium",
     "10 ring segments. Balanced speed and smoothness. Default."),
    (DENSITY_HIGH, "High",
     "16 ring segments. Slower to generate, smoother silhouette. "
     "Use when the mannequin will be sculpted on or rendered."),
)

DENSITY_TO_RING_SEGMENTS = {
    DENSITY_LOW: 6,
    DENSITY_MEDIUM: 10,
    DENSITY_HIGH: 16,
}

DENSITY_TO_LENGTH_SEGMENTS = {
    DENSITY_LOW: 1,
    DENSITY_MEDIUM: 2,
    DENSITY_HIGH: 3,
}

# Output modes. Each has a real cost vs. benefit difference.
OUTPUT_PER_BONE = "PER_BONE"
OUTPUT_JOINED = "JOINED"
OUTPUT_JOINED_REMESH = "JOINED_REMESH"

OUTPUT_ITEMS = (
    (OUTPUT_PER_BONE, "Per-bone objects",
     "One mesh object per bone primitive. Easy to delete or hide "
     "individual parts. Heavier on Outliner clutter."),
    (OUTPUT_JOINED, "Joined (non-manifold)",
     "All primitives joined into a single mesh. Faster to manage. "
     "Geometry is non-manifold at joints — fine for previewing, "
     "not suitable for sculpting or remeshing."),
    (OUTPUT_JOINED_REMESH, "Joined + Remesh (manifold)",
     "Joined and run through voxel remesh to produce a single closed "
     "surface. Slower to generate, but the result is sculpting-ready "
     "for stylized work."),
)

# Display styles set a viewport treatment that marks the output as
# preview geometry so users do not mistake it for a final asset.
DISPLAY_XRAY = "XRAY"
DISPLAY_FLAT = "FLAT"
DISPLAY_WIREFRAME = "WIREFRAME"

DISPLAY_ITEMS = (
    (DISPLAY_XRAY, "X-ray",
     "Show in front of other geometry. Lets you see the rig through "
     "the mannequin while posing."),
    (DISPLAY_FLAT, "Flat colour",
     "Solid magenta shade. Loud and obviously a placeholder."),
    (DISPLAY_WIREFRAME, "Wireframe",
     "Wireframe display. Minimal visual obstruction."),
)

FLAT_DISPLAY_MATERIAL_NAME = "BoneForge_Mannequin_Flat"
FLAT_DISPLAY_MATERIAL_COLOR = (1.0, 0.1, 0.7, 1.0)

# Body-type presets bundle per-region scale multipliers into one click.
# Each entry: (torso, limbs, extremities, head_size).
BODY_NEUTRAL = "NEUTRAL"
BODY_MASCULINE = "MASCULINE"
BODY_FEMININE = "FEMININE"
BODY_CHILD = "CHILD"
BODY_HEAVYSET = "HEAVYSET"
BODY_SLENDER = "SLENDER"
BODY_STYLIZED = "STYLIZED"

BODY_ITEMS = (
    (BODY_NEUTRAL, "Neutral",
     "Balanced proportions. Use as a starting point."),
    (BODY_MASCULINE, "Masculine",
     "Wider torso, thicker limbs. Higher shoulder-to-hip ratio."),
    (BODY_FEMININE, "Feminine",
     "Narrower waist, softer limbs. Lower shoulder-to-hip ratio."),
    (BODY_CHILD, "Child",
     "Larger head relative to body, shorter limbs."),
    (BODY_HEAVYSET, "Heavyset",
     "Thicker torso and limbs throughout."),
    (BODY_SLENDER, "Slender",
     "Thinner torso and limbs throughout."),
    (BODY_STYLIZED, "Stylized",
     "Exaggerated head, hands, and feet. Cartoon proportions."),
)

# (torso_scale, limbs_scale, extremities_scale, head_size_scale)
BODY_PRESETS = {
    BODY_NEUTRAL:   (1.00, 1.00, 1.00, 1.00),
    BODY_MASCULINE: (1.20, 1.10, 1.00, 1.00),
    BODY_FEMININE:  (0.95, 0.92, 0.95, 1.00),
    BODY_CHILD:     (0.90, 0.80, 0.85, 1.40),
    BODY_HEAVYSET:  (1.40, 1.30, 1.10, 1.00),
    BODY_SLENDER:   (0.80, 0.75, 0.85, 1.00),
    BODY_STYLIZED:  (1.10, 1.00, 1.30, 1.50),
}


# ── Anatomy classification patterns ─────────────────────────────
# All patterns are case-insensitive substring matches against the
# bone name. The classification function tests in declaration order
# and picks the first match, so more specific patterns must come
# before more general ones (eye/jaw/teeth before head; thumb/index
# before finger; toe before foot).

CATEGORY_HEAD = "head"
CATEGORY_NECK = "neck"
CATEGORY_HAND = "hand"
CATEGORY_FOOT = "foot"
CATEGORY_FINGER = "finger"
CATEGORY_TAIL = "tail"
CATEGORY_WING = "wing"
CATEGORY_CAPSULE = "capsule"  # default fallback

# (regex pattern, category). First match wins.
ANATOMY_PATTERNS: tuple[tuple[re.Pattern, str], ...] = (
    # Specific facial bones first so they don't get swept into HEAD.
    (re.compile(r"(?i)(?:^|[._-])eye(?:$|[._-])"),     CATEGORY_CAPSULE),
    (re.compile(r"(?i)(?:^|[._-])jaw(?:$|[._-])"),     CATEGORY_CAPSULE),
    (re.compile(r"(?i)(?:^|[._-])teeth(?:$|[._-])"),   CATEGORY_CAPSULE),
    (re.compile(r"(?i)(?:^|[._-])tongue(?:$|[._-])"),  CATEGORY_CAPSULE),
    (re.compile(r"(?i)(?:^|[._-])(?:ear|brow|lid|lip)(?:$|[._-])"),
                                                       CATEGORY_CAPSULE),
    # Head detection — match 'head' or 'skull' anywhere as a token.
    (re.compile(r"(?i)(?:^|[._-])(?:head|skull)(?:$|[._-])"), CATEGORY_HEAD),
    (re.compile(r"(?i)(?:^|[._-])neck(?:$|[._\-\d])"), CATEGORY_NECK),
    # Finger/thumb/digit before hand so the parent hand bone still
    # detects as HAND while individual digit bones are FINGER.
    (re.compile(r"(?i)(?:^|[._-])(?:thumb|index|middle|ring|pinky|"
                r"finger|digit|f_index|f_middle|f_ring|f_pinky)"
                r"(?:$|[._\-\d])"), CATEGORY_FINGER),
    # Hand / palm.
    (re.compile(r"(?i)(?:^|[._-])(?:hand|palm)(?:$|[._-])"), CATEGORY_HAND),
    # Toe before foot.
    (re.compile(r"(?i)(?:^|[._-])(?:toe|toes)(?:$|[._-])"),  CATEGORY_FINGER),
    (re.compile(r"(?i)(?:^|[._-])(?:foot|feet|ankle)(?:$|[._-])"),
                                                       CATEGORY_FOOT),
    # Tail.
    (re.compile(r"(?i)(?:^|[._-])tail(?:$|[._\-\d])"), CATEGORY_TAIL),
    # Wing (Rigify bird metarig).
    (re.compile(r"(?i)(?:^|[._-])(?:wing|feather)(?:$|[._\-\d])"),
                                                       CATEGORY_WING),
)

# Spine chain detection — any bone whose name contains spine/chest/hips
# is a candidate for the unified torso volume in v2.0 mode.
SPINE_PATTERN = re.compile(
    r"(?i)(?:^|[._-])(?:spine|chest|hips|hip|torso|back|abdomen|neck)(?:$|[._\-\d])"
)

# Limb chain detection — upper/lower/forearm/thigh/shin etc.
LIMB_PATTERN = re.compile(
    r"(?i)(?:^|[._-])(?:upper_?arm|forearm|lower_?arm|thigh|shin|"
    r"upper_?leg|lower_?leg|calf)(?:$|[._\-\d])"
)

# Filtered mode — controller name patterns to skip.
CONTROLLER_PREFIXES = ("CTRL", "MCH", "ORG", "WGT", "DEF-WGT", "_")
CONTROLLER_SUFFIXES = (
    "_target", "_pole", "_pivot", "_parent", "_master", "_socket",
)
CONTROLLER_COLLECTION_NAMES = {
    "controllers", "ctrl", "mch", "mech", "org", "widgets", "ik_targets",
}
# Filter out bones shorter than this fraction of the armature's
# longest bone. Removes tiny utility bones that exist only as
# constraint anchors.
MIN_BONE_LENGTH_FRACTION = 0.02

# Tunables for primitive proportions — extracted as named constants
# so the magic numbers don't sit inline with logic.
DEFAULT_RADIUS_AS_FRACTION_OF_BONE_LENGTH = 0.12
MIN_PRIMITIVE_RADIUS = 0.02
HEAD_RADIUS_MULTIPLIER = 1.6
HAND_PADDLE_WIDTH_MULTIPLIER = 2.5
HAND_PADDLE_THICKNESS_MULTIPLIER = 0.6
FOOT_WEDGE_WIDTH_MULTIPLIER = 1.8
FOOT_WEDGE_HEIGHT_MULTIPLIER = 1.4
FINGER_ROOT_RADIUS_MULTIPLIER = 0.6
FINGER_TIP_RADIUS_MULTIPLIER = 0.4
TAIL_TIP_RADIUS_MULTIPLIER = 0.2
WING_CHORD_MULTIPLIER = 4.0
WING_THICKNESS_MULTIPLIER = 0.4
JOINT_SMOOTHING_MERGE_DISTANCE = 0.005
VOXEL_REMESH_FRACTION_OF_BBOX = 0.015


# ── Geometry primitives ─────────────────────────────────────────

def bone_axis_matrix(head_position: Vector,
                     tail_position: Vector) -> Matrix:
    """Return a transform that maps +Z to the head->tail direction.

    Used to orient a primitive built along +Z so it lies along the
    bone. Falls back to identity when head==tail (zero-length bone).
    """
    direction = tail_position - head_position
    length = direction.length
    if length < 1e-9:
        return Matrix.Identity(4)

    direction = direction / length
    z_axis = Vector((0.0, 0.0, 1.0))

    if direction.dot(z_axis) > 0.9999:
        return Matrix.Translation(head_position)
    if direction.dot(z_axis) < -0.9999:
        flip_rotation = Matrix.Rotation(math.pi, 4, Vector((1.0, 0.0, 0.0)))
        return Matrix.Translation(head_position) @ flip_rotation

    rotation_axis = z_axis.cross(direction).normalized()
    angle_radians = math.acos(max(-1.0, min(1.0, z_axis.dot(direction))))
    rotation = Matrix.Rotation(angle_radians, 4, rotation_axis)
    return Matrix.Translation(head_position) @ rotation


def assign_vert_to_group(vert, deform_layer, vertex_group_index: int,
                         weight: float = 1.0) -> None:
    """Assign *vert* to *vertex_group_index* with *weight*.

    BMesh deform layer slots hold a BMDeformVert (dict-like). The
    correct API is ``vert[deform_layer][group_index] = weight``;
    assigning a Python dict to ``vert[deform_layer]`` raises
    ``TypeError: expected BMDeformVert, not a dict`` on Blender 4.x.
    """
    vert[deform_layer][vertex_group_index] = weight


def make_ring_verts(bm, transform: Matrix, height_along_axis: float,
                    ring_radius: float, ring_segments: int) -> list:
    """Create a ring of bmesh verts at the given local height."""
    verts = []
    for segment_index in range(ring_segments):
        theta = 2.0 * math.pi * segment_index / ring_segments
        local_position = Vector((
            math.cos(theta) * ring_radius,
            math.sin(theta) * ring_radius,
            height_along_axis,
        ))
        world_position = transform @ local_position
        verts.append(bm.verts.new(world_position))
    return verts


def add_capsule_to_bmesh(bm, head_position: Vector, tail_position: Vector,
                         radius: float, ring_segments: int,
                         length_segments: int,
                         deform_layer, vertex_group_index: int) -> None:
    """Add a capsule (cylinder + hemisphere caps) along the bone axis."""
    bone_length = (tail_position - head_position).length
    if bone_length < 1e-9:
        return

    transform = bone_axis_matrix(head_position, tail_position)
    cylinder_length = max(0.0, bone_length - 2.0 * radius)
    bottom_cap_height = radius

    new_verts = []
    new_verts.extend(
        build_hemisphere(bm, transform, bottom_cap_height,
                         radius, ring_segments, going_up=False)
    )
    if cylinder_length > 0.0:
        new_verts.extend(
            build_cylinder_body(
                bm, transform,
                height_start=bottom_cap_height,
                height_end=bottom_cap_height + cylinder_length,
                radius=radius,
                ring_segments=ring_segments,
                length_segments=length_segments,
            )
        )
    top_cap_height = bottom_cap_height + cylinder_length
    new_verts.extend(
        build_hemisphere(bm, transform, top_cap_height,
                         radius, ring_segments, going_up=True)
    )

    for vert in new_verts:
        assign_vert_to_group(vert, deform_layer, vertex_group_index)


def build_hemisphere(bm, transform: Matrix, center_height: float,
                     radius: float, ring_segments: int,
                     going_up: bool) -> list:
    """Build a hemisphere cap; return all created verts.

    going_up=True caps the top (verts climb from equator up to pole).
    going_up=False caps the bottom (verts descend from equator).
    """
    rings = max(2, ring_segments // 4)
    all_verts = []
    rings_of_verts = []

    for ring_index in range(rings + 1):
        phi = (math.pi / 2.0) * ring_index / rings
        if going_up:
            ring_height = center_height + math.sin(phi) * radius
        else:
            ring_height = center_height - math.sin(phi) * radius
        ring_radius = math.cos(phi) * radius

        if ring_radius < 1e-6:
            pole_position = transform @ Vector((0.0, 0.0, ring_height))
            pole_vert = bm.verts.new(pole_position)
            rings_of_verts.append([pole_vert])
            all_verts.append(pole_vert)
            continue

        ring = make_ring_verts(bm, transform, ring_height, ring_radius,
                               ring_segments)
        rings_of_verts.append(ring)
        all_verts.extend(ring)

    stitch_rings(bm, rings_of_verts)
    return all_verts


def build_cylinder_body(bm, transform: Matrix, height_start: float,
                        height_end: float, radius: float,
                        ring_segments: int, length_segments: int) -> list:
    """Build a tube between two heights; return all created verts."""
    rings_of_verts = []
    for segment_index in range(length_segments + 1):
        progress = segment_index / length_segments
        height = height_start + (height_end - height_start) * progress
        rings_of_verts.append(make_ring_verts(
            bm, transform, height, radius, ring_segments,
        ))

    all_verts = [vert for ring in rings_of_verts for vert in ring]

    for ring_index in range(length_segments):
        bottom_ring = rings_of_verts[ring_index]
        top_ring = rings_of_verts[ring_index + 1]
        for segment_index in range(ring_segments):
            next_index = (segment_index + 1) % ring_segments
            try:
                bm.faces.new((
                    bottom_ring[segment_index],
                    bottom_ring[next_index],
                    top_ring[next_index],
                    top_ring[segment_index],
                ))
            except ValueError:
                # Face already exists or has duplicate verts —
                # safe to skip; topology continues.
                pass
    return all_verts


def stitch_rings(bm, rings_of_verts: list) -> None:
    """Stitch faces between consecutive rings of verts.

    Handles both ring-to-ring quad strips and ring-to-pole triangle
    fans (when one of the rings is a single pole vertex).
    """
    for ring_index in range(len(rings_of_verts) - 1):
        bottom = rings_of_verts[ring_index]
        top = rings_of_verts[ring_index + 1]

        if len(bottom) == 1 or len(top) == 1:
            stitch_pole_fan(bm, bottom, top)
            continue

        for segment_index in range(len(bottom)):
            next_index = (segment_index + 1) % len(bottom)
            try:
                bm.faces.new((
                    bottom[segment_index],
                    bottom[next_index],
                    top[next_index],
                    top[segment_index],
                ))
            except ValueError:
                pass


def stitch_pole_fan(bm, bottom: list, top: list) -> None:
    """Triangulate a fan around a pole vertex."""
    pole_vertex = bottom[0] if len(bottom) == 1 else top[0]
    ring = top if len(bottom) == 1 else bottom

    for segment_index in range(len(ring)):
        next_index = (segment_index + 1) % len(ring)
        try:
            if pole_vertex is bottom[0]:
                bm.faces.new((
                    pole_vertex,
                    ring[next_index],
                    ring[segment_index],
                ))
            else:
                bm.faces.new((
                    pole_vertex,
                    ring[segment_index],
                    ring[next_index],
                ))
        except ValueError:
            pass


def add_sphere_to_bmesh(bm, center: Vector, radius: float,
                        ring_segments: int,
                        deform_layer, vertex_group_index: int) -> None:
    """Add a UV sphere at *center*; tag verts to the given group."""
    rings = max(4, ring_segments // 2)
    all_verts = []
    rings_of_verts = []

    for ring_index in range(rings + 1):
        phi = math.pi * ring_index / rings - math.pi / 2.0
        ring_height = center.z + math.sin(phi) * radius
        ring_radius = math.cos(phi) * radius

        if ring_radius < 1e-6:
            pole_vert = bm.verts.new(Vector((center.x, center.y, ring_height)))
            rings_of_verts.append([pole_vert])
            all_verts.append(pole_vert)
            continue

        ring = []
        for segment_index in range(ring_segments):
            theta = 2.0 * math.pi * segment_index / ring_segments
            ring_vert = bm.verts.new(Vector((
                center.x + math.cos(theta) * ring_radius,
                center.y + math.sin(theta) * ring_radius,
                ring_height,
            )))
            ring.append(ring_vert)
        rings_of_verts.append(ring)
        all_verts.extend(ring)

    stitch_rings(bm, rings_of_verts)

    for vert in all_verts:
        assign_vert_to_group(vert, deform_layer, vertex_group_index)


def add_paddle_to_bmesh(bm, head_position: Vector, tail_position: Vector,
                        width: float, thickness: float,
                        deform_layer, vertex_group_index: int) -> None:
    """Add a flat paddle (hand-shape) along the bone axis."""
    transform = bone_axis_matrix(head_position, tail_position)
    bone_length = (tail_position - head_position).length
    half_width = width / 2.0
    half_thickness = thickness / 2.0

    corner_offsets = (
        Vector((-half_width, -half_thickness, 0.0)),
        Vector((half_width, -half_thickness, 0.0)),
        Vector((half_width, half_thickness, 0.0)),
        Vector((-half_width, half_thickness, 0.0)),
        Vector((-half_width * 0.7, -half_thickness, bone_length)),
        Vector((half_width * 0.7, -half_thickness, bone_length)),
        Vector((half_width * 0.7, half_thickness, bone_length)),
        Vector((-half_width * 0.7, half_thickness, bone_length)),
    )
    corner_verts = [bm.verts.new(transform @ offset)
                    for offset in corner_offsets]

    box_face_indices = (
        (0, 1, 2, 3),  # base
        (4, 7, 6, 5),  # tip
        (0, 4, 5, 1),  # bottom long
        (2, 6, 7, 3),  # top long
        (1, 5, 6, 2),  # right side
        (0, 3, 7, 4),  # left side
    )
    for face_indices in box_face_indices:
        try:
            bm.faces.new([corner_verts[i] for i in face_indices])
        except ValueError:
            pass

    for vert in corner_verts:
        assign_vert_to_group(vert, deform_layer, vertex_group_index)


def add_wedge_to_bmesh(bm, head_position: Vector, tail_position: Vector,
                       width: float, height: float,
                       deform_layer, vertex_group_index: int) -> None:
    """Add a wedge (foot-shape) along the bone axis.

    Heel (back of the wedge) is slightly taller than the toe (front).
    """
    transform = bone_axis_matrix(head_position, tail_position)
    bone_length = (tail_position - head_position).length
    half_width = width / 2.0

    corner_offsets = (
        Vector((-half_width, -height * 0.4, 0.0)),
        Vector((half_width, -height * 0.4, 0.0)),
        Vector((half_width, height * 0.6, 0.0)),
        Vector((-half_width, height * 0.6, 0.0)),
        Vector((-half_width * 0.8, -height * 0.2, bone_length)),
        Vector((half_width * 0.8, -height * 0.2, bone_length)),
        Vector((half_width * 0.8, height * 0.2, bone_length)),
        Vector((-half_width * 0.8, height * 0.2, bone_length)),
    )
    corner_verts = [bm.verts.new(transform @ offset)
                    for offset in corner_offsets]

    box_face_indices = (
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (2, 6, 7, 3),
        (1, 5, 6, 2),
        (0, 3, 7, 4),
    )
    for face_indices in box_face_indices:
        try:
            bm.faces.new([corner_verts[i] for i in face_indices])
        except ValueError:
            pass

    for vert in corner_verts:
        assign_vert_to_group(vert, deform_layer, vertex_group_index)


def add_tapered_cylinder_to_bmesh(bm, head_position: Vector,
                                  tail_position: Vector,
                                  root_radius: float, tip_radius: float,
                                  ring_segments: int,
                                  length_segments: int,
                                  deform_layer,
                                  vertex_group_index: int) -> None:
    """Add a tapered cylinder (finger/tail shape) along the bone axis."""
    bone_length = (tail_position - head_position).length
    if bone_length < 1e-9:
        return

    transform = bone_axis_matrix(head_position, tail_position)
    rings_of_verts = []
    for segment_index in range(length_segments + 1):
        progress = segment_index / length_segments
        height = bone_length * progress
        radius_at_height = (root_radius * (1.0 - progress)
                            + tip_radius * progress)
        rings_of_verts.append(make_ring_verts(
            bm, transform, height, radius_at_height, ring_segments,
        ))

    all_verts = [vert for ring in rings_of_verts for vert in ring]

    # Cap the root.
    try:
        bm.faces.new(rings_of_verts[0])
    except ValueError:
        pass

    # Tip — pointed cone if the tip is much narrower than the root,
    # otherwise a flat cap.
    if tip_radius < root_radius * 0.2:
        tip_position = transform @ Vector((0.0, 0.0, bone_length + tip_radius))
        tip_vert = bm.verts.new(tip_position)
        all_verts.append(tip_vert)
        last_ring = rings_of_verts[-1]
        for segment_index in range(ring_segments):
            next_index = (segment_index + 1) % ring_segments
            try:
                bm.faces.new((
                    last_ring[segment_index],
                    last_ring[next_index],
                    tip_vert,
                ))
            except ValueError:
                pass
    else:
        try:
            bm.faces.new(list(reversed(rings_of_verts[-1])))
        except ValueError:
            pass

    # Body sides.
    for ring_index in range(length_segments):
        bottom_ring = rings_of_verts[ring_index]
        top_ring = rings_of_verts[ring_index + 1]
        for segment_index in range(ring_segments):
            next_index = (segment_index + 1) % ring_segments
            try:
                bm.faces.new((
                    bottom_ring[segment_index],
                    bottom_ring[next_index],
                    top_ring[next_index],
                    top_ring[segment_index],
                ))
            except ValueError:
                pass

    for vert in all_verts:
        assign_vert_to_group(vert, deform_layer, vertex_group_index)


def add_aerofoil_to_bmesh(bm, head_position: Vector, tail_position: Vector,
                          chord: float, thickness: float,
                          deform_layer, vertex_group_index: int) -> None:
    """Add a flat aerofoil-ish paddle for wings."""
    add_paddle_to_bmesh(
        bm, head_position, tail_position,
        width=chord, thickness=thickness,
        deform_layer=deform_layer,
        vertex_group_index=vertex_group_index,
    )


# ── Bone classification + filtering ─────────────────────────────

def classify_bone(bone) -> str:
    """Return the anatomy category for a bone name. CAPSULE is fallback."""
    name = bone.name
    for pattern, category in ANATOMY_PATTERNS:
        if pattern.search(name):
            return category
    return CATEGORY_CAPSULE


def looks_like_controller_bone(bone) -> bool:
    """Heuristic: does *bone* look like a controller, not a deform bone?"""
    name = bone.name

    for prefix in CONTROLLER_PREFIXES:
        if name.startswith(prefix):
            return True
    for suffix in CONTROLLER_SUFFIXES:
        if name.endswith(suffix):
            return True

    # Membership in controller-named bone collections (Blender 4.0+).
    for collection in getattr(bone, "collections", ()):
        collection_name = getattr(collection, "name", "") or ""
        if collection_name.lower() in CONTROLLER_COLLECTION_NAMES:
            return True
    return False


def collect_bones(armature_object, mode: str) -> list:
    """Return the bones to generate primitives for, per *mode*.

    Universal: every bone with non-zero length.
    Filtered: skip non-deform, controllers, tiny utility bones.
    Anatomical: same filter as Filtered (anatomy applies per-bone).
    Falls back to the universal walk if Filtered rejects every bone.
    """
    armature_data = armature_object.data
    all_bones = list(armature_data.bones)
    if not all_bones:
        return []

    if mode == MODE_UNIVERSAL:
        return [bone for bone in all_bones if bone.length > 1e-6]

    longest_bone_length = max((bone.length for bone in all_bones), default=1.0)
    minimum_bone_length = longest_bone_length * MIN_BONE_LENGTH_FRACTION

    kept_bones = []
    for bone in all_bones:
        if bone.length < minimum_bone_length:
            continue
        if not getattr(bone, "use_deform", True):
            continue
        if looks_like_controller_bone(bone):
            continue
        kept_bones.append(bone)

    if not kept_bones:
        logger.info(
            "[BoneCraft] Mannequin filter rejected every bone; "
            "falling back to Universal walk."
        )
        return [bone for bone in all_bones if bone.length > 1e-6]
    return kept_bones


# ── Settings dictionary ─────────────────────────────────────────

SETTINGS_KEYS = (
    "mode",
    "density",
    "radius_scale",
    "body_type",
    "torso_scale",
    "limbs_scale",
    "extremities_scale",
    "output_mode",
    "display_style",
    "joint_smoothing",
    "unified_volumes",
)


def settings_from_scene(scene) -> dict:
    """Snapshot scene properties into a plain dict for the generator."""
    return {
        "mode":              scene.boneforge_mannequin_mode,
        "density":           scene.boneforge_mannequin_density,
        "radius_scale":      scene.boneforge_mannequin_radius_scale,
        "body_type":         scene.boneforge_mannequin_body_type,
        "torso_scale":       scene.boneforge_mannequin_torso_scale,
        "limbs_scale":       scene.boneforge_mannequin_limbs_scale,
        "extremities_scale": scene.boneforge_mannequin_extremities_scale,
        "output_mode":       scene.boneforge_mannequin_output_mode,
        "display_style":     scene.boneforge_mannequin_display_style,
        "joint_smoothing":   scene.boneforge_mannequin_joint_smoothing,
        "unified_volumes":   scene.boneforge_mannequin_unified_volumes,
    }


def quick_mannequin_settings() -> dict:
    """Return the Quick Mannequin one-click defaults."""
    return {
        "mode":              MODE_FILTERED,
        "density":           DENSITY_MEDIUM,
        "radius_scale":      1.0,
        "body_type":         BODY_NEUTRAL,
        "torso_scale":       1.0,
        "limbs_scale":       1.0,
        "extremities_scale": 1.0,
        "output_mode":       OUTPUT_JOINED,
        "display_style":     DISPLAY_XRAY,
        "joint_smoothing":   True,
        "unified_volumes":   False,
    }


# ── Generation pipeline ─────────────────────────────────────────

def compute_radius_for_bone(bone, settings: dict, category: str) -> float:
    """Compute the primitive radius for *bone* given mode and scaling."""
    base_radius = max(
        MIN_PRIMITIVE_RADIUS,
        bone.length * DEFAULT_RADIUS_AS_FRACTION_OF_BONE_LENGTH,
    )
    base_radius *= settings["radius_scale"]

    body_torso, body_limbs, body_extremities, _ = BODY_PRESETS.get(
        settings["body_type"], BODY_PRESETS[BODY_NEUTRAL],
    )
    body_torso *= settings["torso_scale"]
    body_limbs *= settings["limbs_scale"]
    body_extremities *= settings["extremities_scale"]

    if category in (CATEGORY_HEAD, CATEGORY_HAND, CATEGORY_FOOT,
                    CATEGORY_FINGER, CATEGORY_WING):
        base_radius *= body_extremities
    elif category == CATEGORY_NECK:
        base_radius *= body_torso * 0.75
    elif SPINE_PATTERN.search(bone.name):
        base_radius *= body_torso
    elif LIMB_PATTERN.search(bone.name):
        base_radius *= body_limbs
    return base_radius


def ensure_vertex_group(mesh_object, vertex_group_name: str) -> int:
    """Return the index of the vertex group named *vertex_group_name*.

    Creates the group if it does not already exist.
    """
    vertex_group = mesh_object.vertex_groups.get(vertex_group_name)
    if vertex_group is None:
        vertex_group = mesh_object.vertex_groups.new(name=vertex_group_name)
    return vertex_group.index


def get_or_create_collection(scene,
                             collection_name: str) -> bpy.types.Collection:
    """Return the named collection, creating it under the scene root."""
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        collection = bpy.data.collections.new(collection_name)
        scene.collection.children.link(collection)
        return collection

    children_recursive = scene.collection.children_recursive
    if collection.name not in {child.name for child in children_recursive}:
        try:
            scene.collection.children.link(collection)
        except RuntimeError:
            # Already linked elsewhere — fine.
            pass
    return collection


def generate_one_primitive(bm, bone, category: str, settings: dict,
                           deform_layer, vertex_group_index: int) -> None:
    """Dispatch to the correct primitive generator for *bone*."""
    head_position = Vector(bone.head_local)
    tail_position = Vector(bone.tail_local)
    primitive_radius = compute_radius_for_bone(bone, settings, category)
    ring_segments = DENSITY_TO_RING_SEGMENTS[settings["density"]]
    length_segments = DENSITY_TO_LENGTH_SEGMENTS[settings["density"]]

    if category == CATEGORY_HEAD:
        center = head_position + (tail_position - head_position) * 0.5
        head_radius = max(
            primitive_radius * HEAD_RADIUS_MULTIPLIER,
            bone.length * 0.45,
        )
        body_extras = BODY_PRESETS.get(
            settings["body_type"], BODY_PRESETS[BODY_NEUTRAL],
        )
        head_radius *= body_extras[3]
        add_sphere_to_bmesh(
            bm, center, head_radius, ring_segments,
            deform_layer, vertex_group_index,
        )
        return

    if category == CATEGORY_HAND:
        add_paddle_to_bmesh(
            bm, head_position, tail_position,
            width=primitive_radius * HAND_PADDLE_WIDTH_MULTIPLIER,
            thickness=primitive_radius * HAND_PADDLE_THICKNESS_MULTIPLIER,
            deform_layer=deform_layer,
            vertex_group_index=vertex_group_index,
        )
        return

    if category == CATEGORY_NECK:
        add_tapered_cylinder_to_bmesh(
            bm, head_position, tail_position,
            root_radius=primitive_radius * 1.05,
            tip_radius=primitive_radius * 0.85,
            ring_segments=ring_segments,
            length_segments=max(1, length_segments),
            deform_layer=deform_layer,
            vertex_group_index=vertex_group_index,
        )
        return

    if category == CATEGORY_FOOT:
        add_wedge_to_bmesh(
            bm, head_position, tail_position,
            width=primitive_radius * FOOT_WEDGE_WIDTH_MULTIPLIER,
            height=primitive_radius * FOOT_WEDGE_HEIGHT_MULTIPLIER,
            deform_layer=deform_layer,
            vertex_group_index=vertex_group_index,
        )
        return

    if category == CATEGORY_FINGER:
        add_tapered_cylinder_to_bmesh(
            bm, head_position, tail_position,
            root_radius=primitive_radius * FINGER_ROOT_RADIUS_MULTIPLIER,
            tip_radius=primitive_radius * FINGER_TIP_RADIUS_MULTIPLIER,
            ring_segments=max(4, ring_segments // 2),
            length_segments=max(1, length_segments),
            deform_layer=deform_layer,
            vertex_group_index=vertex_group_index,
        )
        return

    if category == CATEGORY_TAIL:
        add_tapered_cylinder_to_bmesh(
            bm, head_position, tail_position,
            root_radius=primitive_radius,
            tip_radius=primitive_radius * TAIL_TIP_RADIUS_MULTIPLIER,
            ring_segments=ring_segments,
            length_segments=max(2, length_segments * 2),
            deform_layer=deform_layer,
            vertex_group_index=vertex_group_index,
        )
        return

    if category == CATEGORY_WING:
        add_aerofoil_to_bmesh(
            bm, head_position, tail_position,
            chord=primitive_radius * WING_CHORD_MULTIPLIER,
            thickness=primitive_radius * WING_THICKNESS_MULTIPLIER,
            deform_layer=deform_layer,
            vertex_group_index=vertex_group_index,
        )
        return

    add_capsule_to_bmesh(
        bm, head_position, tail_position,
        primitive_radius, ring_segments, length_segments,
        deform_layer, vertex_group_index,
    )


def detect_chains(bones: list) -> tuple[list[list], list[list]]:
    """Detect spine and limb chains for v2.0 unified volumes.

    Returns (spine_chains, limb_chains). Each chain is a list of bones
    in head-to-tail order.
    """
    spine_bones = [bone for bone in bones if SPINE_PATTERN.search(bone.name)]
    spine_chains: list = []
    if spine_bones:
        spine_chains.append(
            sorted(spine_bones, key=lambda bone: bone.head_local.z)
        )

    limb_chains: list[list] = []
    limb_bones = [bone for bone in bones if LIMB_PATTERN.search(bone.name)]
    consumed_bone_names = set()

    for bone in limb_bones:
        if bone.name in consumed_bone_names:
            continue
        chain = [bone]
        consumed_bone_names.add(bone.name)
        current_bone = bone
        while True:
            next_in_chain = next(
                (child for child in current_bone.children
                 if child.name not in consumed_bone_names
                 and LIMB_PATTERN.search(child.name)),
                None,
            )
            if next_in_chain is None:
                break
            chain.append(next_in_chain)
            consumed_bone_names.add(next_in_chain.name)
            current_bone = next_in_chain
        if len(chain) >= 2:
            limb_chains.append(chain)
    return spine_chains, limb_chains


def build_unified_chain(bm, chain: list, settings: dict, mannequin_object,
                        deform_layer) -> None:
    """Build a single tapered volume across *chain* in head-to-tail order.

    Used in v2.0 unified-volumes mode. Each bone in the chain still
    gets its own vertex group so the deform follows the rig naturally.
    """
    if len(chain) < 2:
        return

    ring_segments = DENSITY_TO_RING_SEGMENTS[settings["density"]]
    rings_data = []
    for bone in chain:
        head_position = Vector(bone.head_local)
        radius_at_bone = compute_radius_for_bone(
            bone, settings, CATEGORY_CAPSULE,
        )
        vertex_group_index = ensure_vertex_group(mannequin_object, bone.name)
        rings_data.append((head_position, radius_at_bone, vertex_group_index))

    # Final ring at the tail of the last bone, slightly narrower.
    last_bone = chain[-1]
    tail_radius = compute_radius_for_bone(
        last_bone, settings, CATEGORY_CAPSULE,
    ) * 0.8
    tail_vertex_group_index = ensure_vertex_group(
        mannequin_object, last_bone.name,
    )
    rings_data.append((Vector(last_bone.tail_local),
                       tail_radius, tail_vertex_group_index))

    rings_of_verts = []
    for ring_center, ring_radius, vertex_group_index in rings_data:
        ring = []
        for segment_index in range(ring_segments):
            theta = 2.0 * math.pi * segment_index / ring_segments
            local_offset = Vector((
                math.cos(theta) * ring_radius,
                math.sin(theta) * ring_radius,
                0.0,
            ))
            world_position = ring_center + local_offset
            new_vert = bm.verts.new(world_position)
            assign_vert_to_group(new_vert, deform_layer, vertex_group_index)
            ring.append(new_vert)
        rings_of_verts.append(ring)

    for ring_index in range(len(rings_of_verts) - 1):
        bottom = rings_of_verts[ring_index]
        top = rings_of_verts[ring_index + 1]
        for segment_index in range(ring_segments):
            next_index = (segment_index + 1) % ring_segments
            try:
                bm.faces.new((
                    bottom[segment_index],
                    bottom[next_index],
                    top[next_index],
                    top[segment_index],
                ))
            except ValueError:
                pass


def apply_display_style(mesh_object, style: str) -> None:
    """Apply a viewport treatment that visually marks preview geometry."""
    mesh_object.show_in_front = (style == DISPLAY_XRAY)
    mesh_object.display_type = ("WIRE" if style == DISPLAY_WIREFRAME
                                else "TEXTURED")

    if style != DISPLAY_FLAT:
        return

    material = bpy.data.materials.get(FLAT_DISPLAY_MATERIAL_NAME)
    if material is None:
        material = bpy.data.materials.new(FLAT_DISPLAY_MATERIAL_NAME)
        material.use_nodes = False
        material.diffuse_color = FLAT_DISPLAY_MATERIAL_COLOR

    if not mesh_object.data.materials:
        mesh_object.data.materials.append(material)
    else:
        mesh_object.data.materials[0] = material


def try_voxel_remesh(mesh_object, voxel_size: float) -> None:
    """Best-effort voxel remesh; skip with a warning on older Blender."""
    try:
        remesh_modifier = mesh_object.modifiers.new(
            name="MannequinRemesh", type="REMESH",
        )
        remesh_modifier.mode = "VOXEL"
        remesh_modifier.voxel_size = voxel_size
        bpy.ops.object.select_all(action="DESELECT")
        mesh_object.select_set(True)
        bpy.context.view_layer.objects.active = mesh_object
        bpy.ops.object.modifier_apply(modifier="MannequinRemesh")
    except (RuntimeError, AttributeError, TypeError) as exc:
        logger.warning("[BoneCraft] Mannequin remesh skipped: %s", exc)


def find_mannequin_for(armature_object) -> Optional[bpy.types.Object]:
    """Return the existing mannequin tagged for *armature_object* if any."""
    for candidate in bpy.data.objects:
        if not candidate.get(PROP_IS_MANNEQUIN):
            continue
        if candidate.get(PROP_SOURCE_ARMATURE) == armature_object.name:
            return candidate
    return None


def store_last_params(mannequin_object, settings: dict) -> None:
    """Stash the params used so Regenerate can replay them."""
    for key in SETTINGS_KEYS:
        if key not in settings:
            continue
        try:
            mannequin_object[f"{PROP_LAST_PARAMS_PREFIX}_{key}"] = (
                settings[key]
            )
        except (TypeError, ValueError) as exc:
            logger.debug(
                "[BoneCraft] could not store mannequin param %s=%r: %s",
                key, settings[key], exc,
            )


def restore_last_params(mannequin_object) -> Optional[dict]:
    """Reconstruct settings dict from the stored custom properties."""
    restored = {}
    for key in SETTINGS_KEYS:
        property_name = f"{PROP_LAST_PARAMS_PREFIX}_{key}"
        if property_name not in mannequin_object.keys():
            return None
        restored[key] = mannequin_object[property_name]
    return restored


def generate_mannequin(context, armature_object,
                       settings: dict) -> bpy.types.Object:
    """Generate a mannequin mesh for *armature_object*; return the new object.

    Parents the mannequin to the armature with an Armature modifier and
    pre-binds vertex groups 1:1 to deform bones. Tags the object with
    custom properties so Regenerate / Remove can find it later.
    """
    mode = settings["mode"]
    bones_to_generate = collect_bones(armature_object, mode)
    if not bones_to_generate:
        raise RuntimeError(
            "Active armature has no bones to build a mannequin from."
        )

    mesh_data = bpy.data.meshes.new(
        f"{armature_object.name}_Mannequin_mesh",
    )
    mannequin_object = bpy.data.objects.new(
        name=f"{armature_object.name}_Mannequin",
        object_data=mesh_data,
    )

    # Anatomical-mode pre-pass — count anatomy hits. If none, degrade
    # to Filtered with a logger note (the operator surfaces this).
    downgraded_from_anatomical = False
    if mode == MODE_ANATOMICAL:
        anatomy_match_count = sum(
            1 for bone in bones_to_generate
            if classify_bone(bone) != CATEGORY_CAPSULE
        )
        if anatomy_match_count == 0:
            logger.info(
                "[BoneCraft] Anatomical mode found no humanoid bones; "
                "falling back to Filtered."
            )
            mode = MODE_FILTERED
            settings = dict(settings, mode=MODE_FILTERED)
            downgraded_from_anatomical = True

    mesh_buffer = bmesh.new()
    try:
        deform_layer = mesh_buffer.verts.layers.deform.verify()

        # v2.0 unified-chain pre-pass — bones consumed by a chain do
        # not also receive an individual primitive.
        consumed_bone_names: set[str] = set()
        if settings.get("unified_volumes") and mode == MODE_ANATOMICAL:
            spine_chains, limb_chains = detect_chains(bones_to_generate)
            for chain in spine_chains + limb_chains:
                build_unified_chain(
                    mesh_buffer, chain, settings,
                    mannequin_object, deform_layer,
                )
                for bone in chain:
                    consumed_bone_names.add(bone.name)

        for bone in bones_to_generate:
            if bone.name in consumed_bone_names:
                continue
            category = (classify_bone(bone) if mode == MODE_ANATOMICAL
                        else CATEGORY_CAPSULE)
            vertex_group_index = ensure_vertex_group(
                mannequin_object, bone.name,
            )
            generate_one_primitive(
                mesh_buffer, bone, category, settings,
                deform_layer, vertex_group_index,
            )

        if settings.get("joint_smoothing"):
            bmesh.ops.remove_doubles(
                mesh_buffer,
                verts=mesh_buffer.verts,
                dist=JOINT_SMOOTHING_MERGE_DISTANCE,
            )

        mesh_buffer.normal_update()
        mesh_buffer.to_mesh(mesh_data)
    finally:
        # Always free the bmesh, even on exception.
        mesh_buffer.free()

    mesh_data.update()

    target_collection = get_or_create_collection(
        context.scene, MANNEQUIN_COLLECTION_NAME,
    )
    target_collection.objects.link(mannequin_object)
    mannequin_object.matrix_world = armature_object.matrix_world.copy()
    mannequin_object.parent = armature_object
    mannequin_object.matrix_parent_inverse = (
        armature_object.matrix_world.inverted()
    )

    armature_modifier = mannequin_object.modifiers.new(
        name="Armature", type="ARMATURE",
    )
    armature_modifier.object = armature_object
    armature_modifier.use_vertex_groups = True

    if settings["output_mode"] == OUTPUT_JOINED_REMESH:
        bbox_diagonal_length = mannequin_object.dimensions.length or 1.0
        voxel_size = bbox_diagonal_length * VOXEL_REMESH_FRACTION_OF_BBOX
        bpy.context.view_layer.objects.active = mannequin_object
        try_voxel_remesh(mannequin_object, voxel_size)

    apply_display_style(mannequin_object, settings["display_style"])

    mannequin_object[PROP_IS_MANNEQUIN] = 1
    mannequin_object[PROP_SOURCE_ARMATURE] = armature_object.name
    store_last_params(mannequin_object, settings)

    if downgraded_from_anatomical:
        mannequin_object[PROP_DOWNGRADE_FLAG] = 1

    return mannequin_object


def safe_remove_object(mesh_object) -> None:
    """Remove *mesh_object* and its mesh data; silent on error."""
    try:
        owned_mesh = mesh_object.data
        for collection in list(mesh_object.users_collection):
            try:
                collection.objects.unlink(mesh_object)
            except RuntimeError:
                pass
        bpy.data.objects.remove(mesh_object, do_unlink=True)
        if owned_mesh and owned_mesh.users == 0:
            bpy.data.meshes.remove(owned_mesh)
    except (ReferenceError, RuntimeError):
        logger.exception("[BoneCraft] mannequin removal failed")


# ── Operators ───────────────────────────────────────────────────

def resolve_active_armature(context) -> Optional[bpy.types.Object]:
    """Return the active armature, walking parent if active is a child mesh."""
    active = context.active_object
    if active is None:
        return None
    if active.type == "ARMATURE":
        return active
    if active.parent is not None and active.parent.type == "ARMATURE":
        return active.parent
    return None


class BF_OT_AddMannequin(Operator):
    """Generate a mannequin mesh fitted to the active armature.

    Preview geometry only — replace with your own mesh before final use.
    """
    bl_idname = "boneforge.add_mannequin"
    bl_label = "Add Mannequin"
    bl_description = (
        "Generate a primitive mesh skinned to the active armature for "
        "previewing rig deformation. Choose a mode based on your rig: "
        "Universal (any rig), Filtered (Rigify control rigs), "
        "Anatomical (humanoid). Preview only — replace with your own "
        "mesh before final use"
    )
    bl_options = {"REGISTER", "UNDO"}

    replace_existing: BoolProperty(
        name="Replace Existing",
        description=(
            "If a mannequin already exists for this armature, replace "
            "it instead of adding a second one"
        ),
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return resolve_active_armature(context) is not None

    # no dialog when one exists: it acts at once (undoable); Replace Existing is tuned after the click
    # in Adjust Last Operation, which draws the note below

    def draw(self, context):
        armature = resolve_active_armature(context)
        if armature is None:
            return
        existing = find_mannequin_for(armature)
        if existing is None:
            return
        self.layout.label(
            text=f"A mannequin already exists for {armature.name}.",
            icon='INFO',
        )
        self.layout.prop(self, "replace_existing")

    def execute(self, context):
        armature = resolve_active_armature(context)
        if armature is None:
            self.report({"ERROR"}, "No active armature.")
            return {"CANCELLED"}

        if self.replace_existing:
            existing = find_mannequin_for(armature)
            if existing is not None:
                safe_remove_object(existing)

        try:
            settings = settings_from_scene(context.scene)
            mannequin = generate_mannequin(context, armature, settings)
        except RuntimeError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        except (TypeError, ValueError, AttributeError) as exc:
            logger.exception("[BoneCraft] Mannequin generation failed")
            self.report({"ERROR"}, f"Mannequin generation failed: {exc}")
            return {"CANCELLED"}

        if mannequin.get(PROP_DOWNGRADE_FLAG):
            self.report(
                {"INFO"},
                "Anatomical mode found no humanoid bones — used "
                "Filtered mode instead.",
            )
            return {"FINISHED"}

        mode_label = next(
            (label for key, label, _ in MODE_ITEMS
             if key == settings["mode"]),
            settings["mode"],
        )
        self.report({"INFO"}, f"Mannequin generated ({mode_label} mode).")
        return {"FINISHED"}


class BF_OT_QuickMannequin(Operator):
    """One-click mannequin using safe defaults (Filtered + Neutral + Med).

    Use this when you just want a usable mannequin without configuring
    anything. For finer control, use Add Mannequin instead.
    """
    bl_idname = "boneforge.quick_mannequin"
    bl_label = "Quick Mannequin"
    bl_description = (
        "Generate a mannequin in one click using safe defaults: "
        "Filtered mode, Neutral body type, Medium density. Skips "
        "configuration entirely. Use Add Mannequin if you want to "
        "tweak parameters first"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return resolve_active_armature(context) is not None

    def execute(self, context):
        armature = resolve_active_armature(context)
        if armature is None:
            self.report({"ERROR"}, "No active armature.")
            return {"CANCELLED"}

        existing = find_mannequin_for(armature)
        if existing is not None:
            safe_remove_object(existing)

        try:
            generate_mannequin(context, armature, quick_mannequin_settings())
        except RuntimeError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        except (TypeError, ValueError, AttributeError) as exc:
            logger.exception("[BoneCraft] Quick Mannequin failed")
            self.report({"ERROR"}, f"Quick Mannequin failed: {exc}")
            return {"CANCELLED"}

        self.report({"INFO"}, "Quick Mannequin generated.")
        return {"FINISHED"}


class BF_OT_RegenerateMannequin(Operator):
    """Re-run mannequin generation using the params last applied to this rig.

    Useful after tweaking bone positions, bone radii, or scaling the
    armature — the mannequin no longer fits, regenerate to refit.
    """
    bl_idname = "boneforge.regenerate_mannequin"
    bl_label = "Regenerate Mannequin"
    bl_description = (
        "Re-run mannequin generation with the parameters last used "
        "for this rig. Use after moving bones or changing rig "
        "proportions so the mannequin refits"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        armature = resolve_active_armature(context)
        if armature is None:
            return False
        return find_mannequin_for(armature) is not None

    def execute(self, context):
        armature = resolve_active_armature(context)
        if armature is None:
            self.report({"ERROR"}, "No active armature.")
            return {"CANCELLED"}

        existing = find_mannequin_for(armature)
        if existing is None:
            self.report({"ERROR"}, "No existing mannequin to regenerate.")
            return {"CANCELLED"}

        last_settings = restore_last_params(existing)
        settings = (last_settings if last_settings is not None
                    else settings_from_scene(context.scene))
        safe_remove_object(existing)

        try:
            generate_mannequin(context, armature, settings)
        except RuntimeError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        except (TypeError, ValueError, AttributeError) as exc:
            logger.exception("[BoneCraft] Regenerate failed")
            self.report({"ERROR"}, f"Regenerate failed: {exc}")
            return {"CANCELLED"}

        self.report({"INFO"}, "Mannequin regenerated.")
        return {"FINISHED"}


class BF_OT_RemoveMannequin(Operator):
    """Remove the mannequin associated with the active armature."""
    bl_idname = "boneforge.remove_mannequin"
    bl_label = "Remove Mannequin"
    bl_description = (
        "Delete the mannequin generated for the active armature. "
        "Does not affect the armature or any user-authored meshes"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        armature = resolve_active_armature(context)
        if armature is None:
            return False
        return find_mannequin_for(armature) is not None

    def execute(self, context):
        armature = resolve_active_armature(context)
        existing = find_mannequin_for(armature) if armature else None
        if existing is None:
            self.report({"ERROR"}, "No mannequin to remove.")
            return {"CANCELLED"}
        safe_remove_object(existing)
        self.report({"INFO"}, "Mannequin removed.")
        return {"FINISHED"}


# ── Panel ───────────────────────────────────────────────────────

# ── Panel draw helpers ──────────────────────────────────────────
# These are module-level functions, not @staticmethod on the panel
# class. Reason: the sidebar wrapper BF_PT_rb_mannequin delegates by
# calling BF_PT_MannequinPanel.draw(self, context) with the wrapper's
# `self`. Static methods accessed via `self.X` then fail because the
# attribute lookup hits the wrapper class instead of the panel class.
# Plain module-level functions sidestep the binding issue entirely.

def draw_preview_only_tip(layout) -> None:
    tip_box = layout.box()
    tip_box.scale_y = 0.85
    tip_box.label(
        text=T("Preview only — replace with your own mesh before final use."),
        icon='INFO',
    )


def draw_action_buttons(layout, existing) -> None:
    quick_row = layout.row(align=True)
    quick_row.scale_y = 1.4
    quick_row.operator(
        "boneforge.quick_mannequin",
        text=T("Quick Mannequin"),
        icon='OUTLINER_OB_MESH',
    )

    action_column = layout.column(align=True)
    add_row = action_column.row(align=True)
    add_row.operator(
        "boneforge.add_mannequin",
        text=T("Add Mannequin"),
        icon='OUTLINER_OB_MESH',
    )

    regenerate_remove_row = action_column.row(align=True)
    regenerate_subrow = regenerate_remove_row.row(align=True)
    regenerate_subrow.enabled = existing is not None
    regenerate_subrow.operator(
        "boneforge.regenerate_mannequin",
        text=T("Regenerate"),
        icon='FILE_REFRESH',
    )
    remove_subrow = regenerate_remove_row.row(align=True)
    remove_subrow.enabled = existing is not None
    remove_subrow.operator(
        "boneforge.remove_mannequin",
        text=T("Remove"),
        icon='TRASH',
    )


def draw_core_controls(layout, scene) -> None:
    layout.separator(factor=0.5)
    layout.prop(scene, "boneforge_mannequin_mode", text=T("Mode"))
    layout.prop(scene, "boneforge_mannequin_body_type", text=T("Body Type"))

    density_row = layout.row(align=True)
    density_row.prop(scene, "boneforge_mannequin_density", expand=True)

    layout.prop(
        scene, "boneforge_mannequin_radius_scale",
        text=T("Radius Scale"), slider=True,
    )


def draw_advanced_subsection(layout, scene) -> None:
    advanced_box = layout.box()
    header_row = advanced_box.row(align=True)
    header_row.prop(
        scene, "boneforge_mannequin_show_advanced",
        text="",
        icon=('TRIA_DOWN' if scene.boneforge_mannequin_show_advanced
              else 'TRIA_RIGHT'),
        emboss=False,
    )
    header_row.label(text=T("Advanced"))

    if not scene.boneforge_mannequin_show_advanced:
        return

    advanced_column = advanced_box.column(align=True)
    advanced_column.label(text=T("Per-region scales:"))
    advanced_column.prop(scene, "boneforge_mannequin_torso_scale",
                         text=T("Torso"), slider=True)
    advanced_column.prop(scene, "boneforge_mannequin_limbs_scale",
                         text=T("Limbs"), slider=True)
    advanced_column.prop(scene, "boneforge_mannequin_extremities_scale",
                         text=T("Extremities"), slider=True)
    advanced_column.separator(factor=0.5)
    advanced_column.prop(scene, "boneforge_mannequin_output_mode",
                         text=T("Output"))
    advanced_column.prop(scene, "boneforge_mannequin_display_style",
                         text=T("Display"))
    advanced_column.prop(scene, "boneforge_mannequin_joint_smoothing",
                         text=T("Joint Smoothing"), toggle=True)
    advanced_column.prop(scene, "boneforge_mannequin_unified_volumes",
                         text=T("Unified Volumes (v2 / Anatomical only)"),
                         toggle=True)


def draw_handoff_hint(layout) -> None:
    layout.separator()
    handoff_box = layout.box()
    handoff_box.scale_y = 0.85
    handoff_box.label(
        text=T("Next: switch to the BoneCraft tab for posing, "
             "weight tools, and VRChat optimization."),
        icon='INFO',
    )


class BF_PT_MannequinPanel(Panel):
    """Mannequin subpanel — surfaced inside the Rig Builder tab.

    Layered visibility: top action row + four essential controls
    visible by default, advanced controls hidden behind a disclosure
    triangle. The unanimous council additions are wired in here:
    Quick Mannequin button, Regenerate, existing-mannequin detection,
    cost/benefit tooltips, preview-only header tip, cross-tab handoff.
    """
    bl_idname = "BF_PT_MannequinPanel"
    bl_label = " "
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Rig Builder"
    bl_options = {"HIDE_HEADER"}

    def draw_header(self, context):
        self.layout.label(text=T("Mannequin"))

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        armature = resolve_active_armature(context)

        draw_preview_only_tip(layout)

        if armature is None:
            layout.label(
                text=T("Select an armature to generate a mannequin for it."),
                icon='INFO',
            )
            return

        existing = find_mannequin_for(armature)
        draw_action_buttons(layout, existing)
        # act first, tune later: the shape settings fold below the buttons (owner's UI critique, 2026-10-10)
        from boneforge.core.helpers import options_fold
        options = options_fold(layout, "bc_mannequin_options")
        if options is not None:
            draw_core_controls(options, scene)
            draw_advanced_subsection(options, scene)

        if existing is not None:
            draw_handoff_hint(layout)


# ── Registration ────────────────────────────────────────────────

# v3.8.3: BF_PT_MannequinPanel deliberately omitted from this tuple.
# The panel's draw() is reached only via _delegate_draw from the
# sidebar wrapper BF_PT_rb_mannequin (which is parented under
# BF_PT_rb_setup inside the Rig Builder tab). Registering it as a
# standalone Panel as well caused a duplicate Mannequin section to
# appear at the top of the Rig Builder tab. Keep the class definition
# intact so the delegation and the Properties-editor mirror still
# work, but do not register it as its own panel.
REGISTERED_CLASSES = (
    BF_OT_AddMannequin,
    BF_OT_QuickMannequin,
    BF_OT_RegenerateMannequin,
    BF_OT_RemoveMannequin,
)


def register_scene_properties() -> None:
    """Define every Scene-level mannequin property in one place."""
    bpy.types.Scene.boneforge_mannequin_mode = EnumProperty(
        name="Mannequin Mode",
        description=(
            "Which generation strategy to use. Universal works on any "
            "rig but produces extra geometry on Rigify control rigs. "
            "Filtered skips controllers. Anatomical adds smart "
            "primitives for humanoid heads/hands/feet"
        ),
        items=MODE_ITEMS,
        default=MODE_FILTERED,
    )
    bpy.types.Scene.boneforge_mannequin_density = EnumProperty(
        name="Density",
        description=(
            "Mesh resolution. Low = fast and blocky. Medium = balanced "
            "(default). High = slow but smoother for sculpting"
        ),
        items=DENSITY_ITEMS,
        default=DENSITY_MEDIUM,
    )
    bpy.types.Scene.boneforge_mannequin_radius_scale = FloatProperty(
        name="Radius Scale",
        description=(
            "Global thickness multiplier. Higher = chunkier mannequin, "
            "lower = stick figure"
        ),
        default=1.0,
        min=0.1,
        max=4.0,
        soft_min=0.5,
        soft_max=2.0,
    )
    bpy.types.Scene.boneforge_mannequin_body_type = EnumProperty(
        name="Body Type",
        description=(
            "Preset proportion bundle. Drives torso, limb, and head "
            "scale together. Override with the per-region sliders in "
            "Advanced"
        ),
        items=BODY_ITEMS,
        default=BODY_NEUTRAL,
    )
    bpy.types.Scene.boneforge_mannequin_torso_scale = FloatProperty(
        name="Torso Scale",
        description="Multiplier for spine/chest/hip primitive radius",
        default=1.0, min=0.3, max=3.0,
        soft_min=0.5, soft_max=2.0,
    )
    bpy.types.Scene.boneforge_mannequin_limbs_scale = FloatProperty(
        name="Limbs Scale",
        description="Multiplier for upper arm/forearm/thigh/shin radius",
        default=1.0, min=0.3, max=3.0,
        soft_min=0.5, soft_max=2.0,
    )
    bpy.types.Scene.boneforge_mannequin_extremities_scale = FloatProperty(
        name="Extremities Scale",
        description="Multiplier for head/hand/foot/finger primitive radius",
        default=1.0, min=0.3, max=3.0,
        soft_min=0.5, soft_max=2.0,
    )
    bpy.types.Scene.boneforge_mannequin_output_mode = EnumProperty(
        name="Output Mode",
        description=(
            "How the geometry is delivered. Per-bone keeps each "
            "primitive separate. Joined merges into one mesh "
            "(non-manifold). Joined+Remesh produces a single closed "
            "surface suitable for sculpting"
        ),
        items=OUTPUT_ITEMS,
        default=OUTPUT_JOINED,
    )
    bpy.types.Scene.boneforge_mannequin_display_style = EnumProperty(
        name="Display Style",
        description=(
            "Viewport treatment. X-ray shows through other geometry. "
            "Flat colour gives obvious magenta. Wireframe minimises "
            "obstruction"
        ),
        items=DISPLAY_ITEMS,
        default=DISPLAY_XRAY,
    )
    bpy.types.Scene.boneforge_mannequin_joint_smoothing = BoolProperty(
        name="Joint Smoothing",
        description=(
            "Merge nearby vertices at bone joints to hide capsule "
            "intersections. Cheap and almost always desirable"
        ),
        default=True,
    )
    bpy.types.Scene.boneforge_mannequin_unified_volumes = BoolProperty(
        name="Unified Volumes",
        description=(
            "v2.0: build single tapered volumes across spine and limb "
            "chains instead of stacked per-bone primitives. Smoother "
            "silhouette but only effective on humanoid Anatomical-mode "
            "output"
        ),
        default=False,
    )
    bpy.types.Scene.boneforge_mannequin_show_advanced = BoolProperty(
        name="Show Advanced",
        description="Reveal per-region scales, output mode, display style",
        default=False,
    )


SCENE_PROPERTY_NAMES = (
    "boneforge_mannequin_mode",
    "boneforge_mannequin_density",
    "boneforge_mannequin_radius_scale",
    "boneforge_mannequin_body_type",
    "boneforge_mannequin_torso_scale",
    "boneforge_mannequin_limbs_scale",
    "boneforge_mannequin_extremities_scale",
    "boneforge_mannequin_output_mode",
    "boneforge_mannequin_display_style",
    "boneforge_mannequin_joint_smoothing",
    "boneforge_mannequin_unified_volumes",
    "boneforge_mannequin_show_advanced",
)


def unregister_scene_properties() -> None:
    """Drop every Scene-level mannequin property defined here."""
    for property_name in SCENE_PROPERTY_NAMES:
        if not hasattr(bpy.types.Scene, property_name):
            continue
        try:
            delattr(bpy.types.Scene, property_name)
        except (AttributeError, RuntimeError):
            pass


def register() -> None:
    for cls in REGISTERED_CLASSES:
        bpy.utils.register_class(cls)
    register_scene_properties()


def unregister() -> None:
    unregister_scene_properties()
    for cls in reversed(REGISTERED_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
