#  RNA WIKI REFERENCE
#
# This file maps RNA to online URL's for right mouse context menu documentation access
#
# To make international, we made a script,
# pointing the manuals to the proper language,
# specified in the 'User Preferences Window' by the users
# Some Languages have their manual page, using a prefix or
# being preceeded by their respective reference, for example
#
# Doc:2.6 --> Doc:FR/2.6
#
# The table in the script, contains all of the languages we have in the
# Blender manual website, for those other languages that still
# doesn't have a team of translators, and/or don't have a manual for their languages
# we commented the lines below, you should add them to the language table
# when they have a proper manual in our Blender manual, or added
# to the Blender UI  translation table
# The Blender manual uses a list of ISO_639-1 codes to convert languages to manual prefixes
#
# "DANISH":        "DK",     - Present in the manual, but not present in Blender UI translations table
# "FARSI":         "FA",     - Present in the manual, but not present in Blender UI translations table
# "KOREAN":        "KO",     - Present in the manual, but not present in Blender UI translations table
# "LITHUANIAN":    "LT",     - Present in the manual, but not present in Blender UI translations table
# "MACEDONIAN":    "MK",     - Present in the manual, but not present in Blender UI translations table
# "MONGOLIAN":     "MN",     - Present in the manual, but not present in Blender UI translations table
# "ROMANIAN":      "RO",     - Present in the manual, but not present in Blender UI translations table
#
# "ESTONIAN":      "ET",     - Present in the manual, as an empty page, not present in UI translations table
#
# "CROATIAN":      "HR",     - Present in Blender UI translations table, but without manual
# "KYRGYZ":        "KY",     - Present in Blender UI translations table, but without manual
# "NEPALI":        "NE",     - Present in Blender UI translations table, but without manual
# "PERSIAN":       "FA",     - Present in Blender UI translations table, but without manual
# "HEBREW":        "HE",     - Present in Blender UI translations table, but without manual
# "HUNGARIAN":     "HU",     - Present in Blender UI translations table, but without manual
# "SERBIAN_LATIN": "SR",     - Present in Blender UI translations table, but without manual
#
# NOTES:
#
#  CHINESE                   - Present in the manual as simplified chinese, for both the traditional and simplified
#  PORTUGUESE                - Present in the manual for both Portuguese and Brazilian Portuguese
#  THAILANDESE               - It's the same being used for Turkish in the manual
#
# URL prefix is the: url_manual_prefix + url_manual_mapping[id]

url_manual_prefix = "https://www.blender.org/manual/"

# TODO
"""
LANG = {
    "ARABIC":       "AR",
    "BULGARIAN":    "BG",
    "CATALAN":      "CA",
    "CZECH":        "CZ",
    "GERMAN":       "DE",
    "GREEK":        "EL",
    "RUSSIAN":      "RU",
    "SERBIAN":      "SR",
    "SWEDISH":      "SV",
    "TURKISH":      "TH",
    "UKRAINIAN":    "UK",
    "SPANISH":      "ES",
    "FINNISH":      "FI",
    "FRENCH":       "FR",
    "INDONESIAN":   "ID",
    "ITALIAN":      "IT",
    "JAPANESE":     "JA",
    "DUTCH":        "NL",
    "POLISH":       "PL",
    "PORTUGUESE":   "PT",
    "BRAZILIANPORTUGUESE":  "PT",
    "SIMPLIFIED_CHINESE":   "ZH",
    "TRADITIONAL_CHINESE":  "ZH",
}.get(__import__("bpy").context.user_preferences.system.language)

url_manual_prefix = url_manual_prefix \
    if LANG is None \
    else url_manual_prefix.replace("Doc:2.6", "Doc:" + LANG + "/" + "2.6")
"""

# - The first item is a wildcard - typical file system globbing
#   using python module 'fnmatch.fnmatch'
# - Expressions are evaluated top down (include catch-all expressions last).

url_manual_mapping = (

    # *** User Prefs ***
    ("bpy.types.UserPreferences.*",                "preferences"),
    ("bpy.types.UserPreferencesView.*",            "preferences/interface.html"),
    ("bpy.types.UserPreferencesEdit.*",            "preferences/editing.html"),
    ("bpy.types.UserPreferencesInput.*",           "preferences/input.html"),
    ("bpy.ops.wm.addon_*",                         "preferences/add_ons.html"),
    ("bpy.types.Theme.*",                          "preferences/themes.html"),
    ("bpy.types.UserPreferencesFilePaths.*",       "preferences/file.html"),
    ("bpy.types.UserPreferencesSystem.*",          "preferences/system.html"),
    ("bpy.types.UserSolidLight.*",                 "preferences/system.html"),

    # *** Modifiers ***
    # --- Intro ---
    ("bpy.types.Modifier.show_*", "modifiers/the_stack.html"),
    ("bpy.types.Modifier.*", "modifiers"),  # catchall for various generic options
    # --- Modify Modifiers ---
    ("bpy.types.MeshCacheModifier.*",              "modifiers/modify/mesh_cache.html"),
    ("bpy.types.UVProjectModifier.*",              "modifiers/modify/uv_project.html"),
    ("bpy.types.UVWarpModifier.*",                 "modifiers/modify/uv_warp.html"),
    ("bpy.types.VertexWeightMixModifier.*",        "modifiers/modify/vertex_weight.html"),
    ("bpy.types.VertexWeightEditModifier.*",       "modifiers/modify/vertex_weight.html"),
    ("bpy.types.VertexWeightProximityModifier.*",  "modifiers/modify/vertex_weight.html"),
    # --- Generate Modifiers ---
    ("bpy.types.ArrayModifier.*",      "modifiers/generate/array.html"),
    ("bpy.types.BevelModifier.*",      "modifiers/generate/bevel.html"),
    ("bpy.types.BooleanModifier.*",    "modifiers/generate/booleans.html"),
    ("bpy.types.BuildModifier.*",      "modifiers/generate/build.html"),
    ("bpy.types.DecimateModifier.*",   "modifiers/generate/decimate.html"),
    ("bpy.types.EdgeSplitModifier.*",  "modifiers/generate/edge_split.html"),
    ("bpy.types.MaskModifier.*",       "modifiers/generate/mask.html"),
    ("bpy.types.MirrorModifier.*",     "modifiers/generate/mirror.html"),
    ("bpy.types.MultiresModifier.*",   "modifiers/generate/multiresolution.html"),
    ("bpy.types.RemeshModifier.*",     "modifiers/generate/remesh.html"),
    ("bpy.types.ScrewModifier.*",      "modifiers/generate/screw.html"),
    ("bpy.types.SkinModifier.*",       "modifiers/generate/skin.html"),
    ("bpy.types.SolidifyModifier.*",   "modifiers/generate/solidify.html"),
    ("bpy.types.SubsurfModifier.*",    "modifiers/generate/subsurf.html"),
    ("bpy.types.TriangulateModifier.*","modifiers/generate/triangulate.html"),
    # --- Deform Modifiers ---
    ("bpy.types.ArmatureModifier.*",      "modifiers/deform/armature.html"),
    ("bpy.types.CastModifier.*",          "modifiers/deform/cast.html"),
    ("bpy.types.CurveModifier.*",         "modifiers/deform/curve.html"),
    ("bpy.types.DisplaceModifier.*",      "modifiers/deform/displace.html"),
    ("bpy.types.HookModifier.*",          "modifiers/deform/hooks.html"),
    ("bpy.types.LaplacianSmoothModifier.*", "modifiers/deform/laplacian_smooth.html"),
    ("bpy.types.LatticeModifier.*",       "modifiers/deform/lattice.html"),
    ("bpy.types.MeshDeformModifier.*",    "modifiers/deform/mesh_deform.html"),
    ("bpy.types.ShrinkwrapModifier.*",    "modifiers/deform/shrinkwrap.html"),
    ("bpy.types.SimpleDeformModifier.*",  "modifiers/deform/simple_deform.html"),
    ("bpy.types.SmoothModifier.*",        "modifiers/deform/smooth.html"),
    # ("bpy.types.SurfaceModifier.*",     "Modifiers/Deform/"),  # USERS NEVER SEE THIS
    ("bpy.types.WarpModifier.*",          "modifiers/deform/warp.html"),
    ("bpy.types.WaveModifier.*",          "modifiers/deform/wave.html"),
    # --- Simulate Modifiers ---
    ("bpy.types.ClothModifier.*",             "physics/cloth.html"),
    ("bpy.types.CollisionModifier.*",         "physics/collision.html"),
    ("bpy.types.DynamicPaintModifier.*",      "physics/dynamic_paint"),
    ("bpy.types.ExplodeModifier.*",           "modifiers/simulate/explode.html"),
    ("bpy.types.FluidSimulationModifier.*",   "physics/fluid"),
    ("bpy.types.OceanModifier.*",             "modifiers/simulate/ocean.html"),
    ("bpy.types.ParticleInstanceModifier.*",  "modifiers/simulate/particle_instance.html"),
    ("bpy.types.ParticleSystemModifier.*",    "physics/particles"),
    ("bpy.types.SmokeModifier.*",             "physics/smoke"),
    ("bpy.types.SoftBodyModifier.*",          "physics/soft_body"),

    # *** Constraints ***
    ("bpy.types.Constraint.*", "rigging/constraints"),
    ("bpy.types.Constraint.mute", "rigging/constraints/the_stack.html"),  # others could be added here?
    # --- Transform Constraints ---
    ("bpy.types.CopyLocationConstraint.*",    "rigging/constraints/transform/copy_location.html"),
    ("bpy.types.CopyRotationConstraint.*",    "rigging/constraints/transform/copy_rotation.html"),
    ("bpy.types.CopyScaleConstraint.*",       "rigging/constraints/transform/copy_scale.html"),
    ("bpy.types.CopyTransformsConstraint.*",  "rigging/constraints/transform/copy_transforms.html"),
    ("bpy.types.LimitDistanceConstraint.*",   "rigging/constraints/transform/limit_distance.html"),
    ("bpy.types.LimitLocationConstraint.*",   "rigging/constraints/transform/limit_location.html"),
    ("bpy.types.LimitRotationConstraint.*",   "rigging/constraints/transform/limit_rotation.html"),
    ("bpy.types.LimitScaleConstraint.*",      "rigging/constraints/transform/limit_scale.html"),
    ("bpy.types.MaintainVolumeConstraint.*",  "rigging/constraints/transform/maintain_volume.html"),
    ("bpy.types.TransformConstraint.*",       "rigging/constraints/transform/transformation.html"),
    # --- Tracking Constraints ---
    ("bpy.types.ClampToConstraint.*",      "rigging/constraints/tracking/clamp_to.html"),
    ("bpy.types.DampedTrackConstraint.*",  "rigging/constraints/tracking/damped_track.html"),
    ("bpy.types.KinematicConstraint.*",    "rigging/constraints/tracking/ik_solver.html"),
    ("bpy.types.LockedTrackConstraint.*",  "rigging/constraints/tracking/locked_track.html"),
    ("bpy.types.SplineIKConstraint.*",     "rigging/constraints/tracking/spline_ik.html"),
    ("bpy.types.StretchToConstraint.*",    "rigging/constraints/tracking/stretch_to.html"),
    ("bpy.types.TrackToConstraint.*",      "rigging/constraints/tracking/track_to.html"),
    # --- Relationship Constraints ---
    ("bpy.types.ActionConstraint.*",          "rigging/constraints/relationship/action.html"),
    ("bpy.types.CameraSolverConstraint.*",    "editors/movie_clip_editor"),  # not exact match
    ("bpy.types.ChildOfConstraint.*",         "rigging/constraints/relationship/action.html"),
    ("bpy.types.FloorConstraint.*",           "rigging/constraints/relationship/child_of.html"),
    ("bpy.types.FollowPathConstraint.*",      "rigging/constraints/relationship/floor.html"),
    ("bpy.types.FollowTrackConstraint.*",     "rigging/constraints/relationship/follow_path.html"),
    ("bpy.types.ObjectSolverConstraint.*",    "editors/movie_clip_editor"),  # not exact match
    ("bpy.types.PivotConstraint.*",           "rigging/constraints/relationship/pivot.html"),
    ("bpy.types.PythonConstraint.*",          "rigging/constraints/relationship/script.html"),
    ("bpy.types.RigidBodyJointConstraint.*",  "rigging/constraints/relationship/rigid_body_joint.html"),
    ("bpy.types.ShrinkwrapConstraint.*",      "rigging/constraints/relationship/shrinkwrap.html"),

    ("bpy.types.ImageFormatSettings.*",  "render/output.html#file-type"),
    ("bpy.types.RenderSettings.filepath",  "render/output.html#file-locations"),
    ("bpy.types.RenderSettings.display_mode",  "render/display.html#displaying-renders"),
    ("bpy.types.RenderSettings.*",       "render"),  # catchall, todo - refine

    # *** ID Subclasses ***
    ("bpy.types.Action.*", "animation/basics/actions.html"),
    #("bpy.types.Brush.*", ""),  # TODO - manual has no place for this! XXX
    ("bpy.types.Curve.*", "modeling/curves"),
    ("bpy.types.GreasePencil.*", "interface/grease_pencil/index.html"),
    ("bpy.types.Group.*", "modeling/objects/groups_and_parenting.html#grouping-objects"),
    ("bpy.types.Image.*", "render/blender_render/textures/types/image.html"),
    ("bpy.types.ShapeKey.*", "animation/techs/shape/shape_keys.html"), # not an id but include because of key
    ("bpy.types.Key.*", "animation/techs/shape/shape_keys.html"),
    #("bpy.types.Lattice.*", ""), # TODO - manual has no place for this! XXX
    ("bpy.types.Library.*", "data_system/linked_libraries.html"),
    #("bpy.types.Mask.*", ""), # TODO - manual has no place for this! XXX
    # *** Materials (blender internal) ***
    ("bpy.types.Material.diffuse*", "render/blender_render/materials/properties/diffuse_shaders.html"),
    ("bpy.types.Material.specular*", "render/blender_render/materials/properties/specular_shaders.html"),
    ("bpy.types.Material.ambient*", "render/blender_render/materials/properties/shading.html"),
    ("bpy.types.Material.preview_render_type", "render/blender_render/materials/properties/preview.html"),
    ("bpy.types.Material.*", "render/blender_render"),  # catchall, until the section is filled in

    # ("bpy.types.MaterialSlot.link", "render/blender_render/materials/options.html#material-naming_and_linking"),  # TODO, T42839
    ("bpy.types.MaterialVolume.*", "render/blender_render/materials/special_effects/volume.html"),
    ("bpy.types.MaterialHalo.*", "render/blender_render/materials/special_effects/halo.html"),
    ("bpy.types.MaterialStrand.*", "render/blender_render/materials/properties/strands.html"),
    ("bpy.types.MaterialSubsurfaceScattering.*", "render/blender_render/materials/properties/subsurface_scattering.html"),
    ("bpy.types.MaterialRaytraceMirror.*", "render/blender_render/materials/properties/mirror.html"),
    ("bpy.types.MaterialRaytraceTransparency.*", "render/blender_render/materials/properties/transparency.html#raytraced-transparency"),
    # ... todo, many more options
    ("bpy.types.MovieClip.*", "editors/movie_clip_editor/index.html#movie-clip_editor.html"),
    ("bpy.types.MovieTrackingCamera.*", "editors/movie_clip_editor/index.html#camera-data_panel"),
    ("bpy.types.MovieTrackingStabilization.*", "editors/movie_clip_editor/index.html#tools-available-in-reconstruction-mode"),
    ("bpy.types.MovieTrackingTrack*", "editors/movie_clip_editor/index.html#tools-available-in-tracking-mode"),
    ("bpy.types.MovieTracking*", "editors/movie_clip_editor"),
    ("bpy.types.SpaceClipEditor.*", "editors/movie_clip_editor/index.html#movie-clip-editor"),
    ("bpy.types.ColorManaged*", "render/post_process/cm_and_exposure.html"),
    #("bpy.types.NodeTree.*", ""),  # dont document
    ("bpy.types.Object.*",  "modeling/objects"),  # catchall, todo - refine
    ("bpy.types.ParticleSettings.*", "physics/particles"),
    ("bpy.types.Scene.*", "interface/scenes.html"),
    ("bpy.types.Screen.*", "interface/screens.html"),
    #("bpy.types.Sound.*", ""), # TODO - manual has no place for this! XXX
    #("bpy.types.Speaker.*", ""), # TODO - manual has no place for this! XXX
    ("bpy.types.Text.*", "editors/text_editor.html"),
    ("bpy.types.Texture.*", "render/blender_render/textures"),
    ("bpy.types.VectorFont.*", "modeling/texts"),
    ("bpy.types.WindowManager.*", "interface/window_system"),
    ("bpy.types.World.*", "render/blender_render/world"),
    ("bpy.types.WorldLighting.*ao*", "render/blender_render/lighting/ambient_occlusion.html"),
    ("bpy.types.WorldLighting.*ambient*", "render/blender_render/lighting/ambient_occlusion.html"),
    ("bpy.types.WorldLighting.*environment*", "render/blender_render/lighting/ambient_light.html"),
    # only other WorldLighting props are in Gather panel
    ("bpy.types.WorldLighting.*", "render/blender_render/lighting/ambient_occlusion.html#gather"),

    # *** Cycles ***
    ("bpy.types.CyclesRenderSettings.*", "render/cycles/settings/integrator.html"),
    ("bpy.types.CyclesVisibilitySettings.*", "render/cycles/settings/light_paths.html#ray-visibility"),
    ("bpy.types.CyclesWorldSettings.*", "render/cycles/world.html"),
    ("bpy.types.SceneRenderLayer.*pass*", "render/blender_render/passes.html"),
    ("bpy.types.SceneRenderLayer.*", "render/post_process/layers.html"),
    ("bpy.types.Cycles*", "render/cycles"),

    # Currently all manual links on all sockets and values (such as Fac, Roughness, Color...) are NodeSocket* type.
    # It'd be much better if the name of the socket could be used for the manual reference
    ("bpy.types.NodeSocket*", "editors/node_editor/node_controls.html"),  # no generic socket type page exists, but composite types are the same

    # *** Cycles Material Nodes ***
    # Outputs
    ("bpy.types.ShaderNodeOutputLamp.*", "render/cycles/lamps.html"),
    ("bpy.types.ShaderNodeOutputMaterial.*", "render/cycles/materials"),
    ("bpy.types.ShaderNodeOutputWorld.*", "render/cycles/world.html"),
    # Shaders
    ("bpy.types.ShaderNodeAddShader.*", "render/cycles/nodes/shaders.html#mix-and-add"),
    ("bpy.types.ShaderNodeAmbientOcclusion.*", "render/cycles/nodes/shaders.html#ambient-occlusion"),
    ("bpy.types.ShaderNodeBackground.*", "render/cycles/nodes/shaders.html#background"),
    ("bpy.types.ShaderNodeBsdfAnisotropic.*", "render/cycles/nodes/shaders.html#anisotropic"),
    ("bpy.types.ShaderNodeBsdfDiffuse.*", "render/cycles/nodes/shaders.html#diffuse"),
    ("bpy.types.ShaderNodeBsdfGlass.*", "render/cycles/nodes/shaders.html#glass"),
    ("bpy.types.ShaderNodeBsdfGlossy.*", "render/cycles/nodes/shaders.html#glossy"),
    ("bpy.types.ShaderNodeBsdfHair.*", "render/cycles/nodes/shaders.html"),  # todo doc
    ("bpy.types.ShaderNodeBsdfRefraction.*", "render/cycles/nodes/shaders.html#refraction"),
    ("bpy.types.ShaderNodeBsdfToon.*", "render/cycles/nodes/shaders.html#toon"),
    ("bpy.types.ShaderNodeBsdfTranslucent.*", "render/cycles/nodes/shaders.html#translucent"),
    ("bpy.types.ShaderNodeBsdfTransparent.*", "render/cycles/nodes/shaders.html#transparent"),
    ("bpy.types.ShaderNodeBsdfVelvet.*", "render/cycles/nodes/shaders.html#velvet"),
    ("bpy.types.ShaderNodeEmission.*", "render/cycles/nodes/shaders.html#emission"),
    ("bpy.types.ShaderNodeHoldout.*", "render/cycles/nodes/shaders.html#holdout"),
    ("bpy.types.ShaderNodeMixShader.*", "render/cycles/nodes/shaders.html#mix-and-add"),
    ("bpy.types.ShaderNodeSubsurfaceScattering.*", "render/cycles/nodes/shaders.html#subsurface-scattering"),
    ("bpy.types.ShaderNodeVolumeAbsorption.*", "render/cycles/nodes/shaders.html"),  # todo doc
    ("bpy.types.ShaderNodeVolumeScatter.*", "render/cycles/nodes/shaders.html"),  # todo doc
    # Textures
    ("bpy.types.ShaderNodeTexBrick.*", "render/cycles/nodes/textures.html#brick-texture"),
    ("bpy.types.ShaderNodeTexChecker.*", "render/cycles/nodes/textures.html#checker-texture"),
    ("bpy.types.ShaderNodeTexEnvironment.*", "render/cycles/nodes/textures.html#environment-texture"),
    ("bpy.types.ShaderNodeTexGradient.*", "render/cycles/nodes/textures.html#gradient-texture"),
    ("bpy.types.ShaderNodeTexImage.*", "render/cycles/nodes/textures.html#image-texture"),
    ("bpy.types.ShaderNodeTexMagic.*", "render/cycles/nodes/textures.html#magic-texture"),
    ("bpy.types.ShaderNodeTexMusgrave.*", "render/cycles/nodes/textures.html#musgrave-texture"),
    ("bpy.types.ShaderNodeTexNoise.*", "render/cycles/nodes/textures.html#noise-texture"),
    ("bpy.types.ShaderNodeTexSky.*", "render/cycles/nodes/textures.html#sky-texture"),
    ("bpy.types.ShaderNodeTexVoronoi.*", "render/cycles/nodes/textures.html#voronoi-texture"),
    ("bpy.types.ShaderNodeTexWave.*", "render/cycles/nodes/textures.html#wave-texture"),
    # Other
    ("bpy.types.ShaderNodeAttribute.*", "render/cycles/nodes/more.html#attribute"),
    ("bpy.types.ShaderNodeBlackbody.*", "render/cycles/nodes/more.html#blackbody"),
    # ("bpy.types.ShaderNodeBrightContrast.*", ""),
    ("bpy.types.ShaderNodeBump.*", "render/cycles/nodes/more.html#bump"),
    ("bpy.types.ShaderNodeCameraData.*", "render/cycles/nodes/more.html"),  # TODO doc
    # ("bpy.types.ShaderNodeCombineHSV.*", ""),
    # ("bpy.types.ShaderNodeCombineRGB.*", ""),
    ("bpy.types.ShaderNodeFresnel.*", "render/cycles/nodes/more.html#fresnel"),
    # ("bpy.types.ShaderNodeGamma.*", ""),
    ("bpy.types.ShaderNodeGeometry.*", "render/cycles/nodes/more.html#geometry"),
    ("bpy.types.ShaderNodeHairInfo.*", "render/cycles/nodes/more.html#hair-info"),
    # ("bpy.types.ShaderNodeHueSaturation.*", ""),
    # ("bpy.types.ShaderNodeInvert.*", ""),
    ("bpy.types.ShaderNodeLayerWeight.*", "render/cycles/nodes/more.html#layer-weight"),
    ("bpy.types.ShaderNodeLightFalloff.*", "render/cycles/nodes/more.html#light-falloff"),
    ("bpy.types.ShaderNodeLightPath.*", "render/cycles/nodes/more.html#light-path"),
    ("bpy.types.ShaderNodeMapping.*", "render/cycles/nodes/more.html#mapping"),
    # # ("bpy.types.ShaderNodeMath.*", ""),
    # ("bpy.types.ShaderNodeMixRGB.*", ""),
    ("bpy.types.ShaderNodeNormalMap.*", "render/cycles/nodes/more.html#normal-map"),
    ("bpy.types.ShaderNodeObjectInfo.*", "render/cycles/nodes/more.html#object-info"),
    ("bpy.types.ShaderNodeParticleInfo.*", "render/cycles/nodes/more.html#particle-info"),
    ("bpy.types.ShaderNodeRGB.*", "render/cycles/nodes/more.html#rgb"),
    # ("bpy.types.ShaderNodeRGBCurve.*", ""),
    # ("bpy.types.ShaderNodeRGBToBW.*", ""),
    # ("bpy.types.ShaderNodeSeparateHSV.*", ""),
    # ("bpy.types.ShaderNodeSeparateRGB.*", ""),
    ("bpy.types.ShaderNodeTangent.*", "render/cycles/nodes/more.html#tangent"),
    ("bpy.types.ShaderNodeTexCoord.*", "render/cycles/nodes/more.html#texture-coordinates"),
    ("bpy.types.ShaderNodeValue.*", "render/cycles/nodes/more.html#value"),
    # ("bpy.types.ShaderNodeVectorCurve.*", ""),
    ("bpy.types.ShaderNodeVectorMath.*", "render/cycles/nodes/more.html"),  # TODO doc
    ("bpy.types.ShaderNodeVectorTransform.*", "render/cycles/nodes/more.html#vector-transform"),

    ("bpy.types.ShaderNodeWavelength.*", "render/cycles/nodes/more.html#wavelength"),
    ("bpy.types.ShaderNodeWireframe.*", "render/cycles/nodes/more.html#wireframe"),

    ("bpy.types.ShaderNodeGroup.*", "editors/node_editor/node_groups.html"),
    ("bpy.types.ShaderNode*", "render/cycles/nodes"),

    ("bpy.types.ShaderNodeScript.*", "render/cycles/osl.html"),

    # *** Compositing Nodes ***
    # Input
    ("bpy.types.CompositorNodeBokehImage.*", "composite_nodes/types/input/bokeh_image.html"),
    ("bpy.types.CompositorNodeImage.*", "composite_nodes/types/input/image.html"),
    ("bpy.types.CompositorNodeMask.*", "composite_nodes/types/input/mask.html"),
    ("bpy.types.CompositorNodeMovieClip.*", "composite_nodes/types/input/movie_clip.html"),
    ("bpy.types.CompositorNodeRGB.*", "composite_nodes/types/input/rgb.html"),
    ("bpy.types.CompositorNodeRLayers.*", "composite_nodes/types/input/render_layers.html"),
    ("bpy.types.CompositorNodeTexture.*", "composite_nodes/types/input/texture.html"),
    ("bpy.types.CompositorNodeTime.*", "composite_nodes/types/input/time.html"),
    ("bpy.types.CompositorNodeTrackPos.*", "composite_nodes/types/input/track_position.html"),
    ("bpy.types.CompositorNodeValue.*", "composite_nodes/types/input/value.html"),
    # Output
    ("bpy.types.CompositorNodeComposite.*", "composite_nodes/types/output/composite.html"),
    ("bpy.types.CompositorNodeLevels.*", "composite_nodes/types/output/levels.html"),
    ("bpy.types.CompositorNodeOutputFile*", "composite_nodes/types/output/file.html"),
    ("bpy.types.CompositorNodeSplitViewer.*", "composite_nodes/types/output/split_viewer.html"),
    ("bpy.types.CompositorNodeViewer.*", "composite_nodes/types/output/viewer.html"),
    # Color
    ("bpy.types.CompositorNodeAlphaOver.*", "composite_nodes/types/color/alpha_over.html"),
    ("bpy.types.CompositorNodeBrightContrast.*", "composite_nodes/types/color/bright_contrast.html"),
    ("bpy.types.CompositorNodeColorBalance.*", "composite_nodes/types/color/bright_contrast.html"),
    ("bpy.types.CompositorNodeColorCorrection.*", "composite_nodes/types/color/color_correction.html"),
    ("bpy.types.CompositorNodeCurveRGB.*", "composite_nodes/types/color/rgb_curves.html"),
    ("bpy.types.CompositorNodeGamma.*", "composite_nodes/types/color/gamma.html"),
    ("bpy.types.CompositorNodeHueCorrect.*", "composite_nodes/types/color/hue_correct.html"),
    ("bpy.types.CompositorNodeHueSat.*", "composite_nodes/types/color/hue_saturation.html"),
    ("bpy.types.CompositorNodeInvert.*", "composite_nodes/types/color/invert.html"),
    ("bpy.types.CompositorNodeMixRGB.*", "composite_nodes/types/color/mix.html"),
    ("bpy.types.CompositorNodeTonemap.*", "composite_nodes/types/color/tone_map.html"),
    ("bpy.types.CompositorNodeZcombine.*", "composite_nodes/types/color/z-combine.html"),
    # Converter
    ("bpy.types.CompositorNodeSep*", "composite_nodes/types/converter/combine_separate.html"),
    ("bpy.types.CompositorNodeComb*", "composite_nodes/types/converter/combine_separate.html"),
    ("bpy.types.CompositorNodeIDMask.*", "composite_nodes/types/converter/id_mask.html"),
    ("bpy.types.CompositorNodeMath.*", "composite_nodes/types/converter/math.html"),
    ("bpy.types.CompositorNodePremulKey.*", "composite_nodes/types/converter/alpha_convert.html"),
    ("bpy.types.CompositorNodeRGBToBW.*", "composite_nodes/types/converter/rgb_to_bw.html"),
    ("bpy.types.CompositorNodeSetAlpha.*", "composite_nodes/types/converter/set_alpha.html"),
    # Filter
    ("bpy.types.CompositorNodeBilateralblur.*", "composite_nodes/types/filter/bilateral_blur.html"),
    ("bpy.types.CompositorNodeBlur.*", "composite_nodes/types/filter/blur_node.html"),
    ("bpy.types.CompositorNodeBokehBlur.*", "composite_nodes/types/filter/bokeh_blur.html"),
    ("bpy.types.CompositorNodeDBlur.*", "composite_nodes/types/filter/directional_blur.html"),
    ("bpy.types.CompositorNodeDefocus.*", "composite_nodes/types/filter/defocus.html"),
    ("bpy.types.CompositorNodeDespeckle.*", "composite_nodes/types/filter/despeckle.html"),
    ("bpy.types.CompositorNodeDilateErode.*", "composite_nodes/types/filter/dilate_erode.html"),
    ("bpy.types.CompositorNodeFilter.*", "composite_nodes/types/filter/filter_node.html"),
    ("bpy.types.CompositorNodeGlare.*", "composite_nodes/types/filter/glare.html"),
    ("bpy.types.CompositorNodeInpaint.*", "composite_nodes/types/filter/inpaint.html"),
    ("bpy.types.CompositorNodePixelate.*", "composite_nodes/types/filter/pixelate.html"),
    ("bpy.types.CompositorNodeSunBeams.*", "composite_nodes/types/filter/sun_beams.html"),
    ("bpy.types.CompositorNodeVecBlur.*", "composite_nodes/types/filter/vector_blur.html"),
    # Vector
    ("bpy.types.CompositorNodeCurveVec.*", "composite_nodes/types/vector/vector_curves.html"),
    ("bpy.types.CompositorNodeMapRange.*", "composite_nodes/types/vector/map_range.html"),
    ("bpy.types.CompositorNodeMapValue.*", "composite_nodes/types/vector/map_value.html"),
    ("bpy.types.CompositorNodeNormal.*", "composite_nodes/types/vector/normal.html"),
    ("bpy.types.CompositorNodeNormalize.*", "composite_nodes/types/vector/normalize.html"),
    # Matte
    ("bpy.types.CompositorNodeBoxMask.*", "composite_nodes/types/matte/box_mask.html"),
    ("bpy.types.CompositorNodeChannelMatte.*", "composite_nodes/types/matte/channel_key.html"),
    ("bpy.types.CompositorNodeChromaMatte.*", "composite_nodes/types/matte/chroma_key.html"),
    ("bpy.types.CompositorNodeColorMatte.*", "composite_nodes/types/matte/color_key.html"),
    ("bpy.types.CompositorNodeColorSpill.*", "composite_nodes/types/matte/color_spill_key.html"),
    ("bpy.types.CompositorNodeDiffMatte.*", "composite_nodes/types/matte/difference_key.html"),
    ("bpy.types.CompositorNodeDistanceMatte.*", "composite_nodes/types/matte/difference_key.html"),
    ("bpy.types.CompositorNodeDoubleEdgeMask.*", "composite_nodes/types/matte/double_edge_mask.html"),
    ("bpy.types.CompositorNodeEllipseMask.*", "composite_nodes/types/matte/ellipse_mask.html"),
    ("bpy.types.CompositorNodeKeying.*", "composite_nodes/types/matte/keying.html"),
    ("bpy.types.CompositorNodeKeyingScreen.*", "composite_nodes/types/matte/keying_screen.html"),
    ("bpy.types.CompositorNodeLumaMatte.*", "composite_nodes/types/matte/luminance_key.html"),
    # Distort
    ("bpy.types.CompositorNodeCrop.*", "composite_nodes/types/distort/crop.html"),
    ("bpy.types.CompositorNodeDisplace.*", "composite_nodes/types/distort/displace.html"),
    ("bpy.types.CompositorNodeFlip.*", "composite_nodes/types/distort/flip.html"),
    ("bpy.types.CompositorNodeLensdist.*", "composite_nodes/types/distort/lens.html"),
    ("bpy.types.CompositorNodeMapUV.*", "composite_nodes/types/distort/map_uv.html"),
    ("bpy.types.CompositorNodeMovieDistortion.*", "composite_nodes/types/distort/movie_distortion.html"),
    ("bpy.types.CompositorNodePlaneTrackDeform.*", "composite_nodes/types/distort/plane_track_deform.html"),
    ("bpy.types.CompositorNodeRotate.*", "composite_nodes/types/distort/rotate.html"),
    ("bpy.types.CompositorNodeScale.*", "composite_nodes/types/distort/scale.html"),
    ("bpy.types.CompositorNodeStabilize.*", "composite_nodes/types/distort/stabilize_2d.html"),
    ("bpy.types.CompositorNodeTransform.*", "composite_nodes/types/distort/transform.html"),
    ("bpy.types.CompositorNodeTranslate.*", "composite_nodes/types/distort/translate.html"),
    #Other
    ("bpy.types.CompositorNodeGroup.*", "editors/node_editor/node_groups.html"),
    ("bpy.types.CompositorNode*", "composite_nodes/types"),  # catch anything else

    ("bpy.types.ColorRamp*", "render/blender_render/materials/properties/ramps.html"),

    # *** ID Subclasses (cont.) Object Data ***
    ("bpy.types.Mesh.*",  "modeling/meshes"),  # catchall, todo - refine
    ("bpy.types.MetaBall.*",  "modeling/metas"),  # catchall, todo - refine
    ("bpy.types.TextCurve.*",  "modeling/texts"),  # catchall, todo - refine
    ("bpy.types.Armature.*",  "rigging/armatures.html"),  # catchall, todo - refine
    ("bpy.types.Camera.*",  "render/camera"),  # catchall, todo - refine

    ("bpy.types.PointLamp.*",  "render/blender_render/lighting/lamps/point"),  # catchall, todo - refine
    ("bpy.types.AreaLamp.*",   "render/blender_render/lighting/lamps/area"),  # catchall, todo - refine
    ("bpy.types.SpotLamp.*",   "render/blender_render/lighting/lamps/spot"),  # catchall, todo - refine
    ("bpy.types.SunLamp.*",    "render/blender_render/lighting/lamps/sun"),   # catchall, todo - refine
    ("bpy.types.HemiLamp.*",   "render/blender_render/lighting/lamps/hemi.html"),  # catchall, todo - refine
    ("bpy.types.Lamp.*",       "render/blender_render/lighting"),             # catchall, todo - refine

    # --- Animation ---
    ("bpy.types.Keyframe.*", "animation/basics/actions.html"),
    ("bpy.types.FCurve.*", "editors/graph_editor/fcurves.html"),

    # --- Rigging ---
    ("bpy.types.Bone.*",      "rigging/armatures/bones.html"),
    ("bpy.types.EditBone.*",  "rigging/armatures/bones.html"),
    ("bpy.types.PoseBone.*",  "rigging/posing.html"),

    # --- World ---
    ("bpy.types.World.*",  "render/blender_render/world"),

    ("bpy.types.Texture.*",  "render/blender_render/textures"),

    # *** Spaces ***
    ("bpy.types.SpaceView3D.*", "editors/3dview"),

    # === Operators ===
    # Catch all only for now!
    # *** Window/Screen ***

    ("bpy.ops.action.*",  "animation/basics/actions.html"),
    ("bpy.ops.anim.*",  "animation"),
    ("bpy.ops.armature.*",  "rigging/armatures.html"),
    ("bpy.ops.boid.*",  "physics/particles/physics/boids.html"),
    # ("bpy.ops.brush.*",  ""),  # TODO
    ("bpy.ops.buttons.*",  "interface/buttons_and_controls.html"),
    ("bpy.ops.camera.*",  "render/camera"),
    ("bpy.ops.clip.*",  "editors/movie_clip_editor/index.html#movie-clip-editor"),
    ("bpy.ops.cloth.*",  "physics/cloth.html"),
    ("bpy.ops.console.*",  "editors/python_console.html"),
    ("bpy.ops.constraint.*",  "rigging/constraints"),
    ("bpy.ops.curve.*",  "modeling/curves"),
    ("bpy.ops.dpaint.*",  "physics/dynamic_paint"),
    # ("bpy.ops.ed.*",  ""),  # TODO, this is for internal use only?
    # ("bpy.ops.export_anim.*",  ""),  # TODO
    # ("bpy.ops.export_mesh.*",  ""),  # TODO
    # ("bpy.ops.export_scene.*",  ""),  # TODO
    ("bpy.ops.file.*",  ""),
    ("bpy.ops.fluid.*",  "physics/fluid"),
    ("bpy.ops.font.*",  "modeling/texts"),
    ("bpy.ops.gpencil.*",  "interface/grease_pencil/index.html"),
    ("bpy.ops.graph.*",  "editors/graph_editor/fcurves.html"),
    ("bpy.ops.group.*",  "modeling/objects/groups_and_parenting.html#grouping-objects"),
    ("bpy.ops.image.*",  "render/blender_render/textures/types/image.html"),
    # ("bpy.ops.import_anim.*",  ""),  # TODO
    # ("bpy.ops.import_curve.*",  ""),  # TODO
    # ("bpy.ops.import_mesh.*",  ""),  # TODO
    # ("bpy.ops.import_scene.*",  ""),  # TODO
    # ("bpy.ops.info.*",  ""),  # TODO
    ("bpy.ops.lamp.*",  "render/blender_render/lighting"),  # --- todo ... all below ---
    # ("bpy.ops.lattice.*",  ""),  # TODO
    ("bpy.ops.logic.*",  "game_engine/logic"),
    ("bpy.ops.marker.*",  "animation/basics/markers.html"),
    # ("bpy.ops.mask.*",  ""),  # TODO
    ("bpy.ops.material.new",  "render/blender_render/materials/assigning_a_material.html#creating-a-new-material"),
    ("bpy.ops.material.*",  "render/blender_render"),
    ("bpy.ops.mesh.vertices_smooth", "modeling/meshes/editing/deforming/smooth.html"),
    ("bpy.ops.view3d.edit_mesh_extrude*", "modeling/meshes/editing/duplicating/extrude.html"),
    ("bpy.ops.mesh.subdivide", "modeling/meshes/editing/subdividing/subdivide.html"),
    ("bpy.ops.mesh.loopcut_slide", "modeling/meshes/editing/subdividing/loop_subdivide.html"),
    ("bpy.ops.mesh.bridge-edge-loops", "modeling/meshes/editing/edges.html#bridge-edge-loops"),
    ("bpy.ops.mesh.duplicate_move", "modeling/meshes/editing/duplicating/duplicate.html"),
    ("bpy.ops.mesh.spin", "modeling/meshes/editing/duplicating/spin.html"),
    ("bpy.ops.mesh.screw", "modeling/meshes/editing/duplicating/screw.html"),
    ("bpy.ops.mesh.knife*", "modeling/meshes/editing/subdividing/knife_subdivide.html"),
    ("bpy.ops.mesh.bisect", "modeling/meshes/editing/subdividing/bisect.html"),
    ("bpy.ops.mball.*",  "modeling/metas"),
    ("bpy.ops.mesh.*",  "modeling/meshes"),
    ("bpy.ops.nla.*",  "editors/nla.html"),
    # ("bpy.ops.node.*",  ""),  # TODO
    ("bpy.ops.object.*shape_key*", "animation/techs/shape/shape_keys.html"),
    ("bpy.ops.object.join_shapes", "animation/techs/shape/shape_keys.html"),
    ("bpy.ops.object.*",  "modeling/objects"),
    ("bpy.ops.outliner.*",  "editors/outliner.html"),
    # ("bpy.ops.paint.*",  ""),  # TODO
    ("bpy.ops.particle.*",  "physics/particles"),
    ("bpy.ops.pose.*",  "rigging/posing.html"),
    ("bpy.ops.poselib.*",  "rigging/posing/pose_library.html"),
    # ("bpy.ops.ptcache.*",  ""),  # TODO

    ("bpy.ops.render.play-rendered-anim",  "render/display.html#animation-playback"),
    ("bpy.ops.render.*",  "render"),  # catchall

    ("bpy.ops.scene.*",  "interface/scenes.html"),
    ("bpy.ops.screen.*",  "interface/window_system"),
    ("bpy.ops.script.*",  "advanced/scripting"),
    ("bpy.ops.sculpt.*",  "modeling/meshes/editing/sculpt_mode.html"),
    ("bpy.ops.sequencer.*",  "editors/sequencer"),
    # ("bpy.ops.sketch.*",  ""),  # TODO
    # ("bpy.ops.sound.*",  ""),  # TODO
    ("bpy.ops.surface.*",  "modeling/surfaces"),
    ("bpy.ops.text.*",  "editors/text_editor.html"),
    ("bpy.ops.texture.*",  "render/blender_render/textures"),
    ("bpy.ops.time.*",  "editors/timeline.html"),
    ("bpy.ops.transform.edge_slide", "modeling/meshes/editing/edges.html#edge-slide"),
    ("bpy.ops.transform.vert_slide", "modeling/meshes/editing/vertices.html#vertex-slide"),
    ("bpy.ops.transform.shrink_fatten", "modeling/meshes/editing/deforming/shrink-fatten.html"),
    ("bpy.ops.transform.push_pull", "modeling/meshes/editing/deforming/push_pull.html"),
    ("bpy.ops.transform.*",  "editors/3dview/transform/transform_control"),
    ("bpy.ops.ui.*",  "interface"),
    ("bpy.ops.uv.*",  "editors/uv_image/index.html"),
    # ("bpy.ops.view2d.*",  ""),  # TODO
    ("bpy.ops.view3d.*",  "editors/3dview/navigate/3d_view.html"),  # this link is a bit arbitrary
    ("bpy.ops.wm.*",      "interface/window_system"),
    ("bpy.ops.world.*",  "render/blender_render/world"),

    # === Tool Settings ===
    ("bpy.types.MeshStatVis.*",  "modeling/meshes/mesh_analysis.html"),
)

# may have 'url_reference_mapping'... etc later
