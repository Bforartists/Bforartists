"""
mesh_ghosts.py — Full mesh onion skinning for Ghost Tool.

Creates semi-transparent duplicate meshes at ghost frame positions,
giving animators an onion-skin style preview of how the
character mesh looks at in-between frames.

Lifecycle:
    1. generate_mesh_ghosts() — called after point ghosts are generated.
       For each unique frame in the ghost set it:
         a. Moves the scene to that frame
         b. Evaluates the depsgraph to get the deformed mesh
         c. Creates a lightweight mesh duplicate with a transparent material
         d. Parents it to a collector empty named "GhostMeshes"
    2. clear_mesh_ghosts()  — removes all duplicates and the collector.
    3. update_mesh_ghost_visibility() — shows / hides based on settings.

Materials:
    Two colour ramps: PAST frames tint blue, FUTURE frames tint orange.
    The alpha fades out the further the ghost is from the current frame.
    Flat shading, no shadows, so the silhouettes read clearly against
    the viewport even in solid / material preview mode.
"""

from __future__ import annotations

import math
from typing import Optional

import bpy
from mathutils import Vector

from .utils import sampling_operation, is_sampling, log, warn, debug, tag_viewport_redraw

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GHOST_MESH_COLLECTION = "GhostTool_MeshGhosts"
"""Name of the collection that holds all mesh ghost objects."""

GHOST_MESH_PREFIX = "GhostMesh_"
"""Prefix for mesh ghost object names (e.g. GhostMesh_f24.0)."""

# Custom property keys used to mark and identify ghost mesh objects
GHOST_TOOL_MESH_GHOST_KEY = "ghost_tool_mesh_ghost"  # Boolean: marks an object as a ghost mesh
GHOST_TOOL_FRAME_KEY = "ghost_tool_frame"            # Float: the frame at which this ghost was evaluated
GHOST_TOOL_IS_PAST_KEY = "ghost_tool_is_past"        # Boolean: whether the ghost is in the past
GHOST_TOOL_BASE_ALPHA_KEY = "ghost_tool_base_alpha"  # Float: base transparency (before opacity_scale)

GHOST_SOURCE_TYPES = frozenset({'MESH', 'CURVE', 'SURFACE', 'FONT'})
"""Object types whose evaluated geometry can be onion-skinned through to_mesh()."""

PAST_COLOR = (0.25, 0.55, 1.0)       # Cool blue
FUTURE_COLOR = (1.0, 0.55, 0.15)     # Warm orange
CURRENT_COLOR = (0.2, 1.0, 0.4)      # Bright green (for the current frame)

MAX_MESH_GHOSTS = 32
"""Safety cap to avoid memory explosions on dense timelines."""

MIN_ALPHA = 0.05
MAX_ALPHA = 0.40
"""Transparency range — closest ghosts are MAX_ALPHA, farthest are MIN_ALPHA."""

WIREFRAME_ALPHA = 0.6
"""Alpha for wireframe overlay variant."""

COORDS_PER_VERTEX = 3
"""Number of coordinates (x, y, z) per vertex position."""


# ---------------------------------------------------------------------------
# Material factory
# ---------------------------------------------------------------------------

def _get_or_create_ghost_material(
    name: str,
    color: tuple[float, float, float],
    alpha: float,
    wireframe: bool = False,
) -> bpy.types.Material:
    """Get an existing ghost material or create a new one.

    Uses Blender's node-based materials with a Principled BSDF set to
    transparent.  The material renders in both Solid and Material Preview
    modes.

    Args:
        name:  Unique material name.
        color: RGB base colour (0-1 per channel).
        alpha: Transparency value (0 = invisible, 1 = opaque).
        wireframe: If True, use wireframe display instead of solid.

    Returns:
        The Blender Material object.
    """
    mat = bpy.data.materials.get(name)
    if mat is not None:
        # Material already exists — update its color and alpha in case settings changed
        mat.diffuse_color = (*color, alpha)
        if mat.use_nodes and mat.node_tree:
            # Update the Principled BSDF shader node
            for node in mat.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    node.inputs['Base Color'].default_value = (*color, 1.0)
                    node.inputs['Alpha'].default_value = alpha
                    break
        return mat

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    # Eevee transparency — attribute names vary by Blender version
    # Blender < 4.0: blend_method / shadow_method
    # Blender 4.x+: may use surface_render_method or just node-based alpha
    for attr, val in [('blend_method', 'BLEND'), ('shadow_method', 'NONE')]:
        if hasattr(mat, attr):
            try:
                setattr(mat, attr, val)
            except (AttributeError, TypeError) as exc:
                debug(f"Could not configure ghost material node: {exc}")

    mat.use_backface_culling = False
    mat.diffuse_color = (*color, alpha)

    # Configure the Principled BSDF for flat transparent shading
    tree = mat.node_tree
    tree.nodes.clear()

    output = tree.nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)

    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Alpha'].default_value = alpha
    # Flat look — minimal specular / roughness adjustments
    bsdf.inputs['Roughness'].default_value = 1.0
    _set_shader_input(bsdf, ['Specular IOR Level', 'Specular'], 0.0)

    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def _set_shader_input(bsdf_node, input_names: list[str], value) -> bool:
    """Try setting a BSDF input by name, trying each name in order.

    Handles version-dependent BSDF input names (e.g., "Specular IOR Level"
    vs "Specular" in older Blender versions).

    Args:
        bsdf_node: The Principled BSDF shader node.
        input_names: List of input names to try, in priority order.
        value: The value to set on the first matching input.

    Returns:
        bool: True if an input was successfully set, False if no matching input found.
    """
    for name in input_names:
        try:
            bsdf_node.inputs[name].default_value = value
            return True
        except (KeyError, IndexError):
            continue
    return False


def _apply_mesh_falloff(normalized_distance: float, curve_type: str) -> float:
    """Apply a falloff curve to a normalised distance for mesh ghosts.

    Mirrors the viewport_draw falloff but avoids a cross-module import.

    Args:
        normalized_distance: Normalised distance (0 = at cursor, 1 = farthest).
        curve_type: Falloff curve type - one of "LINEAR", "SMOOTH", "EXPONENTIAL", "CONSTANT".

    Returns:
        float: Adjusted distance factor (0–1).
    """
    normalized_distance = max(0.0, min(normalized_distance, 1.0))
    if curve_type == "CONSTANT":
        return 0.0
    elif curve_type == "SMOOTH":
        return normalized_distance * normalized_distance * (3.0 - 2.0 * normalized_distance)
    elif curve_type == "EXPONENTIAL":
        return 1.0 - pow(1.0 - normalized_distance, 3.0)
    return normalized_distance  # LINEAR


def _compute_ghost_color_alpha(
    ghost_frame: float,
    current_frame: float,
    frame_range_width: float,
    settings=None,
) -> tuple[tuple[float, float, float], float]:
    """Compute the colour and alpha for a mesh ghost based on its time distance.

    Past frames are blue, future frames are orange.  Alpha fades with distance.
    When *settings* is provided, uses user-configurable colors, min alpha,
    and falloff curve from the scene's GhostToolSceneSettings.

    Args:
        ghost_frame:      Frame number of the ghost.
        current_frame:    The scene's current frame.
        frame_range_width: Total frame span being ghosted (for normalizing).
        settings:         Optional GhostToolSceneSettings for user overrides.

    Returns:
        Tuple of (r, g, b) colour and alpha float.
    """
    frame_offset = ghost_frame - current_frame
    if frame_range_width <= 0:
        frame_range_width = 1.0

    # Normalised distance from current frame (0 = at current, 1 = farthest)
    raw_normalized_distance = min(abs(frame_offset) / frame_range_width, 1.0)

    # Apply falloff curve
    falloff_curve = getattr(settings, 'mesh_ghost_falloff', 'LINEAR') if settings else 'LINEAR'
    falloff_adjusted_distance = _apply_mesh_falloff(raw_normalized_distance, falloff_curve)

    # Colour: mesh-specific overrides take priority, fall back to point ghost colors
    if settings:
        past_rgb = tuple(settings.mesh_ghost_past_color)
        future_rgb = tuple(settings.mesh_ghost_future_color)
    else:
        past_rgb = PAST_COLOR
        future_rgb = FUTURE_COLOR

    color = past_rgb if frame_offset < 0 else future_rgb

    max_alpha = getattr(settings, 'mesh_ghost_opacity', MAX_ALPHA) if settings else MAX_ALPHA
    user_min_alpha = settings.ghost_min_alpha if settings else MIN_ALPHA
    effective_min_alpha = min(max(MIN_ALPHA, user_min_alpha), max_alpha)

    # Alpha: lerp from max_alpha at distance=0 to effective_min_alpha at distance=1
    alpha = max_alpha + (effective_min_alpha - max_alpha) * falloff_adjusted_distance

    return color, alpha


# ---------------------------------------------------------------------------
# Collection management
# ---------------------------------------------------------------------------

def _get_mesh_collection(scene):
    for collection in scene.collection.children_recursive:
        if collection.get('ghost_tool_collection') or collection.name == GHOST_MESH_COLLECTION:
            return collection
    return None


def _private_mesh_collection(scene):
    """Detach a shared ghost collection before scene-local mutation."""
    collection = _get_mesh_collection(scene)
    if collection is None:
        return None
    shared = any(other != scene and collection in tuple(other.collection.children_recursive)
                 for other in bpy.data.scenes)
    if not shared:
        return collection
    def find_path(parent):
        for child in parent.children:
            if child == collection:
                return [parent, child]
            path = find_path(child)
            if path:
                return [parent] + path
        return None
    path = find_path(scene.collection)
    duplicate = bpy.data.collections.new(GHOST_MESH_COLLECTION)
    duplicate['ghost_tool_collection'] = True
    duplicate.hide_viewport = not scene.ghost_tool.show_cached_skin
    for obj in collection.objects:
        if not obj.get(GHOST_TOOL_MESH_GHOST_KEY):
            duplicate.objects.link(obj)
            continue
        copied = obj.copy()
        if obj.data is not None:
            copied.data = obj.data.copy()
            if hasattr(copied.data, 'materials'):
                for i, material in enumerate(copied.data.materials):
                    if material is not None:
                        copied.data.materials[i] = material.copy()
        duplicate.objects.link(copied)
    replacement = duplicate
    old_child = collection
    for parent in reversed(path[1:-1]):
        private_parent = parent.copy()
        private_parent.children.unlink(old_child)
        private_parent.children.link(replacement)
        replacement, old_child = private_parent, parent
    scene.collection.children.unlink(old_child)
    scene.collection.children.link(replacement)
    return duplicate


def _get_or_create_collection(scene: bpy.types.Scene) -> bpy.types.Collection:
    """Get or create the GhostTool mesh ghost collection.

    The collection is linked to the scene's master collection and has
    viewport display set to wireframe or bounds for performance.

    Args:
        scene: The Blender scene.

    Returns:
        The mesh ghost collection.
    """
    coll = _private_mesh_collection(scene)
    if coll is None:
        coll = bpy.data.collections.new(GHOST_MESH_COLLECTION)
        coll["ghost_tool_collection"] = True
        scene.collection.children.link(coll)

    coll.hide_viewport = not scene.ghost_tool.show_cached_skin

    # Mark collection as non-selectable / non-renderable by default
    # (user can override in the outliner if needed)
    try:
        layer_coll = _find_layer_collection(
            bpy.context.view_layer.layer_collection, coll.name
        )
        if layer_coll:
            layer_coll.exclude = False
    except Exception as exc:
        warn(f"Could not configure ghost collection layer: {exc}")

    return coll


def set_cached_skin_visibility(scene: bpy.types.Scene, visible: bool) -> None:
    """Change display on this scene's existing collection without rebuilding skins."""
    coll = _private_mesh_collection(scene)
    if coll is not None:
        coll.hide_viewport = not visible


def _find_layer_collection(root: bpy.types.LayerCollection, name: str) -> Optional[bpy.types.LayerCollection]:
    """Recursively find a LayerCollection by name.

    Args:
        root: The root LayerCollection to search.
        name: Collection name to find.

    Returns:
        LayerCollection matching the given name, or None if not found.
    """
    if root.name == name:
        return root
    for child in root.children:
        found = _find_layer_collection(child, name)
        if found:
            return found
    return None


# ---------------------------------------------------------------------------
# Core mesh ghost generation
# ---------------------------------------------------------------------------

def _compute_desired_mesh_frames(
    ghost_frames: list[float],
    current_frame: float,
    past_count: int,
    future_count: int,
    step: int,
) -> list[float]:
    """Compute the final list of frames to generate mesh ghosts at.

    Filters the input frames into past/future groups, applies step filtering,
    respects past/future count limits, and enforces the global MAX_MESH_GHOSTS
    cap by keeping the closest ghosts from each side.

    Args:
        ghost_frames: Raw list of frame numbers.
        current_frame: The scene's current frame.
        past_count: Maximum number of past-frame ghosts.
        future_count: Maximum number of future-frame ghosts.
        step: Frame step filter (1 = every frame, 2 = every other frame, etc.).

    Returns:
        list[float]: Sorted list of frames to generate ghosts at.
    """
    # Separate past and future frames
    past_frames = sorted(
        [f for f in ghost_frames if f < current_frame],
        reverse=True,  # closest first
    )
    future_frames = sorted(
        [f for f in ghost_frames if f > current_frame],
    )

    # Apply step filter
    if step > 1:
        past_frames = past_frames[::step]
        future_frames = future_frames[::step]

    # Apply count limits
    past_frames = past_frames[:past_count]
    future_frames = future_frames[:future_count]

    # Combined, but also enforce global cap
    all_frames = sorted(set(past_frames + future_frames))
    if len(all_frames) > MAX_MESH_GHOSTS:
        # Keep closest ghosts from each side
        half = MAX_MESH_GHOSTS // 2
        all_frames = sorted(set(past_frames[:half] + future_frames[:half]))

    return all_frames


def _evaluate_and_create_ghost_mesh(
    context: bpy.types.Context,
    mesh_obj: bpy.types.Object,
    frame: float,
    current_frame: float,
    coll: bpy.types.Collection,
    use_wire: bool,
    frame_range_width: float,
    scene_settings,
    set_frame: bool = True,
) -> Optional[bpy.types.Object]:
    """Evaluate the mesh at a specific frame and create a ghost duplicate.

    Temporarily moves the scene to the frame, evaluates the deformed mesh
    geometry, creates a new static mesh object with appropriate transparency
    and material, and sets up custom properties. Returns the created ghost
    object or None if evaluation failed.

    Args:
        context: Current Blender context.
        mesh_obj: The source mesh object to evaluate.
        frame: Frame number to evaluate at.
        current_frame: Scene's current frame (for color/alpha calculation).
        coll: Collection to link the ghost object into.
        use_wire: Whether to use wireframe display mode.
        frame_range_width: Total frame span for alpha falloff calculation.
        scene_settings: GhostToolSceneSettings or None.

    Returns:
        bpy.types.Object: The created ghost object, or None if creation failed.
    """
    scene = context.scene

    # Move to frame and evaluate (generate_mesh_ghosts sets it once per frame)
    if set_frame:
        scene.frame_set(math.floor(frame), subframe=frame - math.floor(frame))
    depsgraph = context.evaluated_depsgraph_get()

    # Get the evaluated (deformed) mesh
    eval_obj = mesh_obj.evaluated_get(depsgraph)
    if eval_obj is None:
        return None

    try:
        eval_mesh = eval_obj.to_mesh()
    except RuntimeError as exc:
        warn(f"Could not evaluate mesh at frame {frame}: {exc}")
        return None

    ghost_mesh = None
    try:
        if eval_mesh is None:
            return None

        # Create a new mesh data block from the evaluated mesh
        ghost_mesh = bpy.data.meshes.new(f"{GHOST_MESH_PREFIX}data_{frame:.0f}")
        ghost_mesh.from_pydata(
            [v.co.copy() for v in eval_mesh.vertices],
            [tuple(e.vertices) for e in eval_mesh.edges],
            [list(p.vertices) for p in eval_mesh.polygons],
        )
        ghost_mesh.update()

        # Copy normals for better shading
        if hasattr(eval_mesh, 'calc_normals'):
            ghost_mesh.calc_normals()

        # Copy vertex normals for smooth shading
        try:
            ghost_mesh.normals_split_custom_set_from_vertices(
                [v.normal.copy() for v in eval_mesh.vertices]
            )
        except Exception as exc:
            warn(f"Could not set custom normals at frame {frame}: {exc}")

    except Exception:
        if ghost_mesh is not None and ghost_mesh.users == 0:
            bpy.data.meshes.remove(ghost_mesh)
        raise
    finally:
        eval_obj.to_mesh_clear()

    # Create the ghost object
    ghost_name = f"{GHOST_MESH_PREFIX}{mesh_obj.name}_f{frame:.0f}"
    ghost_obj = bpy.data.objects.new(ghost_name, ghost_mesh)

    # Custom properties to identify and track this ghost mesh
    # Set early, right after object creation
    ghost_obj[GHOST_TOOL_MESH_GHOST_KEY] = True
    ghost_obj[GHOST_TOOL_FRAME_KEY] = frame
    ghost_obj["ghost_tool_source"] = mesh_obj.name
    ghost_obj[GHOST_TOOL_IS_PAST_KEY] = (frame < current_frame)

    # Position: copy world matrix from the evaluated source
    ghost_obj.matrix_world = mesh_obj.matrix_world.copy()

    # Material — pass scene settings for user-configurable colors/falloff
    color, alpha = _compute_ghost_color_alpha(
        frame, current_frame, frame_range_width, settings=scene_settings,
    )
    mat_name = f"GhostMat_{ghost_obj.name}"

    if use_wire:
        # Use the computed falloff alpha instead of the fixed WIREFRAME_ALPHA,
        # but cap it so wireframes remain slightly transparent (visual hint).
        wire_alpha = min(alpha, WIREFRAME_ALPHA)
        mat = _get_or_create_ghost_material(mat_name, color, wire_alpha, wireframe=True)
    else:
        mat = _get_or_create_ghost_material(mat_name, color, alpha)

    ghost_obj.data.materials.append(mat)
    ghost_obj[GHOST_TOOL_BASE_ALPHA_KEY] = min(alpha, WIREFRAME_ALPHA) if use_wire else alpha
    if scene_settings:
        ghost_obj.hide_viewport = not (scene_settings.show_mesh_past if frame < current_frame
                                       else scene_settings.show_mesh_future)

    # Display settings
    if use_wire:
        ghost_obj.display_type = 'WIRE'
    else:
        ghost_obj.display_type = 'SOLID'

    # Make non-selectable and non-renderable
    ghost_obj.hide_select = True
    ghost_obj.hide_render = True
    ghost_obj.show_in_front = bool(getattr(scene_settings, 'mesh_ghost_xray', False))

    # Enable smooth shading for solid mode
    if not use_wire:
        for poly in ghost_obj.data.polygons:
            poly.use_smooth = True

    # Apply outline via Solidify modifier if enabled
    if scene_settings and scene_settings.ghost_outline_enabled:
        _apply_outline_modifier(ghost_obj, scene_settings, frame, current_frame)

    # Link to the ghost collection
    coll.objects.link(ghost_obj)

    return ghost_obj


@sampling_operation
def generate_mesh_ghosts(
    context: bpy.types.Context,
    source_obj: bpy.types.Object,
    ghost_frames: list[float],
    mode: str = "SOLID",
    past_count: int = 5,
    future_count: int = 5,
    step: int = 1,
) -> int:
    """Generate mesh ghost duplicates at specified frames.

    For each frame, the scene is temporarily moved to that frame,
    the depsgraph is evaluated, and a snapshot of the deformed mesh
    is created as a static mesh object with a transparent material.

    Args:
        context:      Current Blender context.
        source_obj:   A mesh or armature, or a list of them. An armature
                      contributes every mesh it deforms.
        ghost_frames: List of frame numbers to create ghosts at.
        mode:         Display mode — "SOLID" for shaded, "WIRE" for wireframe.
        past_count:   Max number of past-frame ghosts.
        future_count: Max number of future-frame ghosts.
        step:         Frame step between ghosts (1 = every frame).

    Returns:
        int: Number of mesh ghosts created.
    """
    scene = context.scene
    current_frame = scene.frame_current

    # Every mesh the sources deform: a character's body, clothes, hair and
    # eyes, for each selected character.
    mesh_objs = resolve_mesh_objects(source_obj)
    if not mesh_objs:
        warn("No mesh object found for mesh ghost generation.")
        return 0

    # Compute the final list of frames to generate ghosts at
    all_frames = _compute_desired_mesh_frames(
        ghost_frames, current_frame, past_count, future_count, step
    )

    if not all_frames:
        clear_mesh_ghosts(context)
        warn("No valid frames for mesh ghost generation.")
        return 0

    # Compute frame range for alpha falloff
    min_frame = min(all_frames)
    max_frame = max(all_frames)
    frame_range_width = max(max_frame - min_frame, 1.0)

    clear_mesh_ghosts(context)
    coll = _get_or_create_collection(scene)

    created = 0
    failed = 0
    use_wire = (mode == "WIRE")
    mesh_settings = getattr(scene, 'ghost_tool', None)

    for frame in all_frames:
        scene.frame_set(math.floor(frame), subframe=frame - math.floor(frame))
        for mesh_obj in mesh_objs:
            ghost_obj = _evaluate_and_create_ghost_mesh(
                context,
                mesh_obj,
                frame,
                current_frame,
                coll,
                use_wire,
                frame_range_width,
                mesh_settings,
                set_frame=False,
            )
            if ghost_obj is not None:
                created += 1
            else:
                failed += 1

    if failed > 0:
        log(f"Created {created} of {created + failed} mesh ghosts ({failed} failed to evaluate)")
    else:
        log(f"Created {created} mesh ghosts")

    return created


def _apply_outline_modifier(
    ghost_obj: bpy.types.Object,
    settings,
    ghost_frame: float,
    current_frame: float,
) -> None:
    """Add a Solidify modifier to a mesh ghost for outline rendering.

    Creates a dark inverted-hull outline around the ghost mesh. The Solidify
    modifier with flipped normals duplicates the mesh shell with reversed
    geometry, and a separate dark material is assigned to this shell layer.
    This technique produces a crisp silhouette effect even in solid shading
    mode, making the ghost mesh edges stand out distinctly from the background.

    Args:
        ghost_obj:     The mesh ghost object.
        settings:      GhostToolSceneSettings with outline params.
        ghost_frame:   Frame of this ghost (for unique material naming).
        current_frame: Scene's current frame.
    """
    width = settings.ghost_outline_width
    outline_rgb = tuple(settings.ghost_outline_color)

    # Create the outline material (opaque dark)
    outline_mat_name = f"GhostOutline_{ghost_obj.name}"
    outline_mat = bpy.data.materials.get(outline_mat_name)
    if outline_mat is None:
        outline_mat = bpy.data.materials.new(name=outline_mat_name)
        outline_mat.use_nodes = True
        outline_mat.diffuse_color = (*outline_rgb, 1.0)

        tree = outline_mat.node_tree
        tree.nodes.clear()
        output = tree.nodes.new('ShaderNodeOutputMaterial')
        output.location = (300, 0)
        bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
        bsdf.inputs['Base Color'].default_value = (*outline_rgb, 1.0)
        bsdf.inputs['Roughness'].default_value = 1.0
        _set_shader_input(bsdf, ['Specular IOR Level', 'Specular'], 0.0)
        tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    # Add the outline material as the second slot on the ghost object
    ghost_obj.data.materials.append(outline_mat)
    outline_mat_idx = len(ghost_obj.data.materials) - 1

    # Add Solidify modifier configured as inverted-hull outline
    mod = ghost_obj.modifiers.new(name="GhostOutline", type='SOLIDIFY')
    mod.thickness = -width  # Negative = grow inward → flip renders outward
    mod.offset = -1.0
    mod.use_flip_normals = True
    mod.use_rim = False
    mod.material_offset = outline_mat_idx  # Assign outline mat to shell


def resolve_mesh_objects(sources) -> list[bpy.types.Object]:
    """Every visible object to onion-skin for one object or a list of objects.

    A mesh, curve, surface or text object contributes itself. An armature
    contributes every visible such object parented under it or deformed by it
    through an Armature modifier, so a character split into body, clothes,
    hair and eyes is ghosted whole.
    """
    if sources is None:
        return []
    if isinstance(sources, bpy.types.Object):
        sources = [sources]
    meshes: list[bpy.types.Object] = []
    for obj in sources:
        if obj is None:
            continue
        if obj.type in GHOST_SOURCE_TYPES:
            candidates = [obj]
        elif obj.type == 'ARMATURE':
            candidates = [child for child in obj.children_recursive if child.type in GHOST_SOURCE_TYPES]
            candidates += [
                other for other in bpy.data.objects
                if other.type in GHOST_SOURCE_TYPES and any(
                    mod.type == 'ARMATURE' and mod.object == obj for mod in other.modifiers)
            ]
        else:
            continue
        for mesh in candidates:
            if mesh.get(GHOST_TOOL_MESH_GHOST_KEY) or mesh in meshes:
                continue
            if mesh is obj or mesh.visible_get():
                meshes.append(mesh)
    return meshes


def _is_ghost_source(obj) -> bool:
    return obj is not None and not obj.get(GHOST_TOOL_MESH_GHOST_KEY) \
        and (obj.type in GHOST_SOURCE_TYPES or obj.type == 'ARMATURE')


def selected_ghost_sources(context: bpy.types.Context) -> list[bpy.types.Object]:
    """The active object plus any selected mesh, curve, surface, text or armature."""
    sources: list[bpy.types.Object] = []
    active = getattr(context, 'active_object', None)
    for obj in [active, *getattr(context, 'selected_objects', ())]:
        if _is_ghost_source(obj) and obj not in sources:
            sources.append(obj)
    return sources


def pinned_ghost_sources(scene: bpy.types.Scene) -> list[bpy.types.Object]:
    """Objects pinned by Show Onion Skin; deleted or renamed ones drop out."""
    settings = getattr(scene, 'ghost_tool', None)
    names = getattr(settings, 'mesh_ghost_sources', '') if settings is not None else ''
    sources: list[bpy.types.Object] = []
    for name in names.split('\n'):
        obj = bpy.data.objects.get(name) if name else None
        if _is_ghost_source(obj) and obj not in sources:
            sources.append(obj)
    return sources


def pin_ghost_sources(scene: bpy.types.Scene, sources) -> None:
    """Remember which objects the onion skins follow, independent of selection."""
    settings = getattr(scene, 'ghost_tool', None)
    if settings is not None:
        settings["mesh_ghost_sources"] = "\n".join(obj.name for obj in sources)


def ghost_source_objects(context: bpy.types.Context) -> list[bpy.types.Object]:
    """The characters to onion-skin: the pinned ones, else the current selection."""
    return pinned_ghost_sources(context.scene) or selected_ghost_sources(context)


def set_mesh_ghost_xray(scene: bpy.types.Scene, enabled: bool) -> None:
    """Toggle drawing existing onion skins in front of everything."""
    coll = _get_mesh_collection(scene)
    if coll is None:
        return
    for obj in coll.objects:
        if obj.get(GHOST_TOOL_MESH_GHOST_KEY):
            obj.show_in_front = enabled


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def clear_mesh_ghosts(context: bpy.types.Context) -> int:
    """Remove all mesh ghost objects and their data.

    Deletes every object in the GhostTool_MeshGhosts collection,
    cleans up orphaned mesh data and materials, and removes the
    collection itself.

    Args:
        context: Current Blender context.

    Returns:
        int: Number of mesh ghosts removed.
    """
    scene = context.scene
    removed = 0
    owned_materials = set()

    coll = _private_mesh_collection(scene)
    if coll is not None:
        # Collect objects to remove
        objects_to_remove = [obj for obj in coll.objects if obj.get(GHOST_TOOL_MESH_GHOST_KEY)]

        for obj in objects_to_remove:
            # Store mesh data ref before unlinking
            mesh_data = obj.data if obj.type == 'MESH' else None

            if mesh_data:
                owned_materials.update(mat for mat in mesh_data.materials if mat)

            # Unlink from collection
            coll.objects.unlink(obj)

            # Remove the object
            bpy.data.objects.remove(obj, do_unlink=True)

            # Remove orphaned mesh data
            if mesh_data and mesh_data.users == 0:
                bpy.data.meshes.remove(mesh_data)

            removed += 1

        # Remove the collection if empty
        if len(coll.objects) == 0:
            bpy.data.collections.remove(coll)

    # Clean up ghost materials with zero users
    mats_to_remove = [
        mat for mat in owned_materials if mat.users == 0
    ]
    for mat in mats_to_remove:
        bpy.data.materials.remove(mat)

    if removed > 0:
        log(f"Cleared {removed} mesh ghosts")

    return removed


# ---------------------------------------------------------------------------
# Visibility control
# ---------------------------------------------------------------------------

def update_mesh_ghost_visibility(
    scene: bpy.types.Scene,
    show_past: bool = True,
    show_future: bool = True,
    opacity_scale: float = 1.0,
) -> None:
    """Update visibility and opacity of all mesh ghosts in the scene.

    Iterates over all mesh ghosts, showing or hiding them based on whether
    they are in the past or future relative to the current frame, and scales
    their material alpha by the given opacity_scale multiplier.

    Args:
        scene:         The Blender scene.
        show_past:     Whether past-frame ghosts should be visible.
        show_future:   Whether future-frame ghosts should be visible.
        opacity_scale: Multiplier for ghost opacity (0.0–1.0).
    """
    coll = _private_mesh_collection(scene)
    if coll is None:
        return

    current_frame = scene.frame_current

    for obj in coll.objects:
        if not obj.get(GHOST_TOOL_MESH_GHOST_KEY):
            continue

        ghost_frame = obj.get(GHOST_TOOL_FRAME_KEY, 0)
        is_past = ghost_frame < current_frame

        # Visibility
        if is_past:
            obj.hide_viewport = not show_past
        else:
            obj.hide_viewport = not show_future

        # Update material alpha based on opacity_scale
        if obj.data and obj.data.materials:
            mat = obj.data.materials[0]
            if mat and mat.use_nodes and mat.node_tree:
                # Find and update the Principled BSDF shader node
                for node in mat.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        base_alpha = obj.get(GHOST_TOOL_BASE_ALPHA_KEY, MAX_ALPHA)
                        node.inputs['Alpha'].default_value = base_alpha * opacity_scale
                        break


def set_mesh_ghost_display_mode(mode: str = "SOLID", scene=None) -> None:
    """Change display mode for all mesh ghosts.

    Args:
        mode: "SOLID", "WIRE", or "BOUNDS".
    """
    scene = scene or bpy.context.scene
    coll = _private_mesh_collection(scene)
    if coll is None:
        return

    for obj in coll.objects:
        if obj.get(GHOST_TOOL_MESH_GHOST_KEY):
            obj.display_type = mode


# ---------------------------------------------------------------------------
# Frame-change handler — auto-update mesh ghost positions
# ---------------------------------------------------------------------------

@bpy.app.handlers.persistent
def _on_frame_change(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph) -> None:
    """Handler called on frame change to update mesh ghost appearance.

    Re-colours ghosts based on their relation to the new current frame
    (past ghosts go blue, future ghosts go orange, alpha adjusts).

    Registered/unregistered via register()/unregister() below.

    Args:
        scene:     The Blender scene.
        depsgraph: The evaluated dependency graph.
    """
    if is_sampling():
        return
    if not hasattr(scene, 'ghost_tool'):
        return

    settings = scene.ghost_tool
    if not settings.is_active or not settings.show_mesh_ghosts:
        return

    coll = _private_mesh_collection(scene)
    if coll is None or len(coll.objects) == 0:
        return

    current_frame = scene.frame_current

    # Find frame range from existing ghosts
    frames = [
        obj.get(GHOST_TOOL_FRAME_KEY, 0) for obj in coll.objects
        if obj.get(GHOST_TOOL_MESH_GHOST_KEY)
    ]
    if not frames:
        return

    frame_range_width = max(max(frames) - min(frames), 1.0)

    for obj in coll.objects:
        if not obj.get(GHOST_TOOL_MESH_GHOST_KEY):
            continue

        ghost_frame = obj.get(GHOST_TOOL_FRAME_KEY, 0)
        is_past = ghost_frame < current_frame
        obj[GHOST_TOOL_IS_PAST_KEY] = is_past

        color, alpha = _compute_ghost_color_alpha(
            ghost_frame, current_frame, frame_range_width, settings
        )
        obj[GHOST_TOOL_BASE_ALPHA_KEY] = alpha

        # Update material colour and alpha
        if obj.data and obj.data.materials:
            mat = obj.data.materials[0]
            if mat:
                mat.diffuse_color = (*color, alpha)
                if mat.use_nodes and mat.node_tree:
                    for node in mat.node_tree.nodes:
                        if node.type == 'BSDF_PRINCIPLED':
                            node.inputs['Base Color'].default_value = (*color, 1.0)
                            node.inputs['Alpha'].default_value = alpha
                            break

        # Show/hide based on settings
        show_past = settings.show_mesh_past
        show_future = settings.show_mesh_future
        if is_past:
            obj.hide_viewport = not show_past
        else:
            obj.hide_viewport = not show_future


# ---------------------------------------------------------------------------
# Incremental mesh ghost update (live mode)
# ---------------------------------------------------------------------------

def _same_mesh_topology(source, target):
    """Vertex counts alone miss animated connectivity/face changes."""
    if (len(source.vertices), len(source.edges), len(source.polygons), len(source.loops)) != (
            len(target.vertices), len(target.edges), len(target.polygons), len(target.loops)):
        return False
    import numpy as np

    def _array(collection, attr, count, width=1):
        data = np.empty(count * width, dtype=np.int32)
        if count:
            collection.foreach_get(attr, data)
        return data.reshape(count, width) if width > 1 else data

    # Faces/loops retain source order through from_pydata.
    loop_count = len(source.loops)
    if not np.array_equal(_array(source.loops, 'vertex_index', loop_count),
                          _array(target.loops, 'vertex_index', loop_count)):
        return False
    poly_count = len(source.polygons)
    if not np.array_equal(_array(source.polygons, 'loop_start', poly_count),
                          _array(target.polygons, 'loop_start', poly_count)):
        return False
    # from_pydata may reorder edges: compare as sorted vertex pairs.
    edge_count = len(source.edges)
    a = np.sort(_array(source.edges, 'vertices', edge_count, 2), axis=1)
    b = np.sort(_array(target.edges, 'vertices', edge_count, 2), axis=1)
    a = a[np.lexsort((a[:, 1], a[:, 0]))] if edge_count else a
    b = b[np.lexsort((b[:, 1], b[:, 0]))] if edge_count else b
    return bool(np.array_equal(a, b))


@sampling_operation
def update_mesh_ghosts_incremental(
    context: bpy.types.Context,
) -> bool:
    """Update existing mesh ghost vertex positions without recreating objects.

    Instead of the expensive delete-and-recreate cycle, this function:
    1. Checks if mesh ghost objects already exist
    2. For each existing ghost, evaluates the deformed mesh at its frame
    3. Writes the new vertex positions via foreach_set (fast bulk update)
    4. Updates material colors based on new current-frame distance

    This is designed for live mode — called by the pipeline on frame change.

    Args:
        context: Current Blender context.

    Returns:
        bool: True if update succeeded, False if a full rebuild is needed.
    """
    scene = context.scene
    coll = _private_mesh_collection(scene)

    if coll is None or len(coll.objects) == 0:
        return False  # No existing ghosts — need full generate

    settings = scene.ghost_tool
    current_frame = scene.frame_current

    # Gather existing ghost objects with their frame numbers
    ghost_objects = []
    for obj in coll.objects:
        if obj.get(GHOST_TOOL_MESH_GHOST_KEY) and obj.type == 'MESH':
            frame = obj.get(GHOST_TOOL_FRAME_KEY, None)
            if frame is not None:
                ghost_objects.append((frame, obj))

    if not ghost_objects:
        return False

    # Same ghost count per mesh as the playhead now wants: reuse the objects and
    # move them to the new frames. Anything else needs a full rebuild.
    sources = ghost_source_objects(context)
    desired_frames = sorted(_compute_desired_mesh_frames_from_settings(
        settings, current_frame, scene, sources))
    if not desired_frames:
        return False

    mesh_objs = resolve_mesh_objects(sources)
    if not mesh_objs:
        return False
    mesh_by_name = {mesh.name: mesh for mesh in mesh_objs}

    ghosts_by_source: dict[str, list] = {}
    for frame, obj in ghost_objects:
        ghosts_by_source.setdefault(obj.get('ghost_tool_source'), []).append((frame, obj))
    if set(ghosts_by_source) != set(mesh_by_name):
        return False
    if any(len(items) != len(desired_frames) for items in ghosts_by_source.values()):
        return False

    plan: list[tuple[float, bpy.types.Object, bpy.types.Object]] = []
    for source_name, items in ghosts_by_source.items():
        items.sort(key=lambda item: item[0])
        for frame, (_old_frame, obj) in zip(desired_frames, items):
            plan.append((frame, obj, mesh_by_name[source_name]))

    frame_range_width = max(desired_frames[-1] - desired_frames[0], 1.0)

    success = True

    last_frame = None
    for frame, ghost_obj, mesh_obj in sorted(plan, key=lambda item: item[0]):
        ghost_obj[GHOST_TOOL_FRAME_KEY] = frame
        # Move to frame and evaluate (once per frame for all meshes)
        if frame != last_frame:
            scene.frame_set(math.floor(frame), subframe=frame - math.floor(frame))
            last_frame = frame
        depsgraph = context.evaluated_depsgraph_get()

        eval_obj = mesh_obj.evaluated_get(depsgraph)
        if eval_obj is None:
            success = False
            continue

        try:
            eval_mesh = eval_obj.to_mesh()
        except RuntimeError:
            success = False
            continue

        try:
            if eval_mesh is None:
                success = False
                continue

            ghost_mesh = ghost_obj.data

            # Check topology matches — if not, topology changed, need rebuild
            if not _same_mesh_topology(eval_mesh, ghost_mesh):
                success = False
                break  # Topology mismatch — full rebuild required

            # Fast bulk vertex position update via foreach_set
            vertex_count = len(eval_mesh.vertices)
            flattened_vertex_coords = [0.0] * (vertex_count * COORDS_PER_VERTEX)
            eval_mesh.vertices.foreach_get('co', flattened_vertex_coords)
            ghost_mesh.vertices.foreach_set('co', flattened_vertex_coords)

            # Notify Blender that geometry changed
            ghost_mesh.update()

        finally:
            eval_obj.to_mesh_clear()

        # Update world matrix (in case armature moved)
        ghost_obj.matrix_world = mesh_obj.matrix_world.copy()

        # Update color/alpha based on new current frame
        color, alpha = _compute_ghost_color_alpha(
            frame, current_frame, frame_range_width, settings=settings
        )
        ghost_obj[GHOST_TOOL_IS_PAST_KEY] = (frame < current_frame)
        if settings.mesh_ghost_mode == "WIRE":
            alpha = min(alpha, WIREFRAME_ALPHA)
        ghost_obj[GHOST_TOOL_BASE_ALPHA_KEY] = alpha

        if ghost_obj.data.materials:
            mat = ghost_obj.data.materials[0]
            if mat:
                mat.diffuse_color = (*color, alpha)
                if mat.use_nodes and mat.node_tree:
                    for node in mat.node_tree.nodes:
                        if node.type == 'BSDF_PRINCIPLED':
                            node.inputs['Base Color'].default_value = (*color, 1.0)
                            node.inputs['Alpha'].default_value = alpha
                            break

        # Update visibility
        show_past = settings.show_mesh_past
        show_future = settings.show_mesh_future
        is_past = frame < current_frame
        ghost_obj.hide_viewport = (not show_past) if is_past else (not show_future)

    if success:
        renames = []
        for frame, ghost_obj, mesh_obj in plan:
            name = f"{GHOST_MESH_PREFIX}{mesh_obj.name}_f{frame:.0f}"
            if ghost_obj.name != name:
                renames.append((ghost_obj, name))
        for ghost_obj, _name in renames:
            ghost_obj.name = f"{ghost_obj.name}~"  # release every target name first
        for ghost_obj, name in renames:
            ghost_obj.name = name

    return success


def _get_keyframe_frames_for_object(obj: bpy.types.Object) -> list[float]:
    """Collect all unique keyframe frame numbers from an object's animation data.

    Examines the object's action f-curves (using the slotted-action compat
    helper for Blender 4.4+/Bforartists 5.x) and returns a sorted list of
    frame numbers where keyframes exist.

    For armatures, also checks child objects (meshes with shape key actions)
    to catch all keyframes that affect the visual result.

    Args:
        obj: The Blender object to inspect.

    Returns:
        list[float]: Sorted list of keyframe frame numbers.
    """
    from .utils import get_fcurves_from_action, debug

    frames: set[float] = set()

    sources = [obj]
    if obj.type == 'ARMATURE':
        sources.extend(obj.children_recursive)
    for source in sources:
        owners = [source]
        shape_keys = getattr(getattr(source, 'data', None), 'shape_keys', None)
        if shape_keys is not None:
            owners.append(shape_keys)
        for owner in owners:
            animation = owner.animation_data
            if animation and animation.action:
                for curve in get_fcurves_from_action(animation.action, owner):
                    frames.update(float(key.co.x) for key in curve.keyframe_points)

    debug(f"Keyframe scan total: {len(frames)} unique keyframe frames for {obj.name}")
    return sorted(frames)


def _compute_desired_mesh_frames_from_settings(
    settings,
    current_frame: float,
    scene: bpy.types.Scene,
    obj: bpy.types.Object = None,
) -> set[float]:
    """Compute the set of frames that mesh ghosts should exist at.

    Used by incremental update to detect when the frame window has shifted
    and a full rebuild is needed instead. Reads past_count, future_count,
    frame step, and frame mode from the scene settings.

    Args:
        settings: GhostToolSceneSettings.
        current_frame: The scene's current frame.
        scene: The Blender scene with frame_start and frame_end bounds.
        obj: Optional object for keyframe lookup (needed for KEYFRAMES mode).

    Returns:
        set[float]: Desired frame numbers for mesh ghosts.
    """
    past_count = settings.mesh_ghost_past_count
    future_count = settings.mesh_ghost_future_count
    frame_step = settings.mesh_ghost_step
    frame_mode = settings.mesh_ghost_frame_mode

    frame_start_bound = scene.frame_start
    frame_end_bound = scene.frame_end

    if frame_mode == 'KEYFRAMES' and obj is not None:
        # Only generate at keyframe positions (every source's keys)
        sources = obj if isinstance(obj, (list, tuple)) else [obj]
        all_keyframes = sorted({f for source in sources for f in _get_keyframe_frames_for_object(source)})

        # Determine keyframe skip interval (every Nth keyframe)
        kf_skip_enum = settings.mesh_ghost_keyframe_skip
        if kf_skip_enum == 'CUSTOM':
            kf_skip = max(1, settings.mesh_ghost_keyframe_skip_custom)
        else:
            kf_skip = max(1, int(kf_skip_enum))

        # Past keyframes: sorted nearest-first (descending), then take every Nth
        past_all = sorted(
            [f for f in all_keyframes if f < current_frame and frame_start_bound <= f <= frame_end_bound],
            reverse=True,
        )
        # Apply skip: from the nearest keyframe outward, take every Nth
        # Index 0 = nearest past keyframe, so we pick indices 0, N, 2N, 3N...
        past_frames = past_all[::kf_skip][:past_count]

        # Future keyframes: sorted nearest-first (ascending), then take every Nth
        future_all = sorted(
            [f for f in all_keyframes if f > current_frame and frame_start_bound <= f <= frame_end_bound],
        )
        future_frames = future_all[::kf_skip][:future_count]

        return set(past_frames + future_frames)

    # Default STEP mode: regular frame intervals
    frames = set()
    for step_index in range(1, past_count + 1):
        frame_number = current_frame - step_index * frame_step
        if frame_start_bound <= frame_number <= frame_end_bound:
            frames.add(float(frame_number))

    for step_index in range(1, future_count + 1):
        frame_number = current_frame + step_index * frame_step
        if frame_start_bound <= frame_number <= frame_end_bound:
            frames.add(float(frame_number))

    return frames


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

class GHOST_OT_generate_mesh_ghosts(bpy.types.Operator):
    """Generate mesh onion skin ghosts for the active object."""

    bl_idname = "ghost_tool.generate_mesh_ghosts"
    bl_label = "Generate Mesh Ghosts"
    bl_description = (
        "Generate and show onion skins at frames around the playhead. "
        "Use Onion Skin options > Show cached skin to hide or show existing skins"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """Require a selected or active mesh, curve, surface, text or armature."""
        if selected_ghost_sources(context):
            return True
        cls.poll_message_set("Select a character (its armature, mesh or curve) first")
        return False

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Generate mesh ghost duplicates.

        Args:
            context: Current Blender context.

        Returns:
            set[str]: {'FINISHED'} on success.
        """
        scene = context.scene
        settings = scene.ghost_tool
        obj = selected_ghost_sources(context)
        current_frame = scene.frame_current
        if not resolve_mesh_objects(obj):
            self.report({'WARNING'}, "No visible geometry on the selected character(s): "
                                     "onion skins need a mesh or curve deformed by the rig")
            return {'CANCELLED'}
        pin_ghost_sources(scene, obj)

        # Build the frame list from settings (respects STEP vs KEYFRAMES mode)
        past_count = settings.mesh_ghost_past_count
        future_count = settings.mesh_ghost_future_count
        mode = settings.mesh_ghost_mode

        ghost_frames = sorted(
            _compute_desired_mesh_frames_from_settings(
                settings, current_frame, scene, obj
            )
        )

        frame_mode = settings.mesh_ghost_frame_mode
        if not ghost_frames and frame_mode == 'KEYFRAMES':
            self.report({'WARNING'}, "No keyframes found on this object — try Frame Step mode")
            return {'CANCELLED'}

        count = generate_mesh_ghosts(
            context=context,
            source_obj=obj,
            ghost_frames=ghost_frames,
            mode=mode,
            past_count=past_count,
            future_count=future_count,
            step=1,  # step already applied above
        )

        # Raw writes: the ghosts were just built, so skip the callbacks that
        # would clear them (Ghost Tools off) or queue a second full build.
        if not settings.is_active:
            settings["is_active"] = True
        settings["show_mesh_ghosts"] = True
        if count > 0:
            settings.show_cached_skin = True
        from .ghost_pipeline import GhostPipeline
        GhostPipeline.get(scene).remember_edit_state(scene)

        mode_label = "at keyframes" if frame_mode == 'KEYFRAMES' else "frame-step"
        meshes = len(resolve_mesh_objects(obj))
        self.report({'INFO'}, f"Created {count} onion skins from {meshes} mesh(es) ({mode_label})")
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


class GHOST_OT_clear_mesh_ghosts(bpy.types.Operator):
    """Remove all mesh onion skin ghost objects."""

    bl_idname = "ghost_tool.clear_mesh_ghosts"
    bl_label = "Clear Mesh Ghosts"
    bl_description = "Remove all transparent mesh ghost duplicates from the scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Clear mesh ghosts.

        Args:
            context: Current Blender context.

        Returns:
            set[str]: {'FINISHED'}.
        """
        count = clear_mesh_ghosts(context)
        pin_ghost_sources(context.scene, [])
        self.report({'INFO'}, f"Removed {count} mesh ghosts")
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


class GHOST_OT_toggle_mesh_visibility(bpy.types.Operator):
    """Show or hide onion skins without changing their shading."""

    bl_idname = "ghost_tool.toggle_mesh_visibility"
    bl_label = "Show Mesh Ghosts"
    bl_description = "Show or hide mesh onion skins, preserving the Solid/Wireframe setting"
    bl_options = {'REGISTER'}

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.ghost_tool
        settings.show_mesh_ghosts = not settings.show_mesh_ghosts
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


class GHOST_OT_toggle_mesh_mode(bpy.types.Operator):
    """Switch Solid/Wireframe without changing onion skin visibility."""

    bl_idname = "ghost_tool.toggle_mesh_mode"
    bl_label = "Wireframe Mesh Ghosts"
    bl_description = "Switch mesh ghosts between Solid and Wireframe, preserving visibility"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """Always available; operates on the ghost collection.

        Args:
            context: Current Blender context.

        Returns:
            bool: True (always available).
        """
        return True

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Toggle shading independently of visibility.

        Args:
            context: Current Blender context.

        Returns:
            set[str]: {'FINISHED'}.
        """
        settings = context.scene.ghost_tool
        # The RNA update callback applies the style to existing ghost objects.
        settings.mesh_ghost_mode = 'WIRE' if settings.mesh_ghost_mode == 'SOLID' else 'SOLID'
        self.report({'INFO'}, f"Mesh ghost shading: {'Wireframe' if settings.mesh_ghost_mode == 'WIRE' else 'Solid'}")
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

_classes = (
    GHOST_OT_generate_mesh_ghosts,
    GHOST_OT_clear_mesh_ghosts,
    GHOST_OT_toggle_mesh_visibility,
    GHOST_OT_toggle_mesh_mode,
)


def register() -> None:
    """Register mesh ghost operators and frame-change handler."""
    for cls in _classes:
        bpy.utils.register_class(cls)

    # Register the frame-change handler
    if _on_frame_change not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(_on_frame_change)

    log("Mesh ghosts module registered.")


def unregister() -> None:
    """Unregister mesh ghost operators and clean up handler."""
    # Remove frame-change handler
    if _on_frame_change in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(_on_frame_change)

    for cls in reversed(_classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as exc:
            debug(f"Could not unregister {cls.__name__}: {exc}")
