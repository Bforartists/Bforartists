#  RNA MANUAL REFERENCE
#
# This file maps RNA to online URL's for right mouse context menu documentation access
#
# To make international, we made a script,
# pointing the manuals to the proper language,
# specified in the 'User Preferences Window' by the users
# Some Languages have their manual page, using a prefix or
# being preceded by their respective reference, for example
#
# manual/ --> manual/ru/
#
# The table in the script, contains all of the languages we have in the
# Blender manual website, for those other languages that still
# doesn't have a team of translators, and/or don't have a manual for their languages
# we commented the lines below, you should add them to the language table
# when they have a proper manual in our Blender manual, or added
# to the Blender UI  translation table
# The Blender manual uses a list of ISO_639-1 codes to convert languages to manual prefixes
#
# URL is the: url_manual_prefix + url_manual_mapping[id]

import bpy

url_manual_prefix = "https://docs.blender.org/manual/en/dev/"

language = ""
if bpy.context.user_preferences.system.use_international_fonts:
    language = bpy.context.user_preferences.system.language
    if language == 'DEFAULT':
        import os
        language = os.getenv('LANG', '').split('.')[0]

LANG = {
#   "ar_EG":        "ar",
#   "bg_BG":        "bg",
#   "ca_AD":        "ca",
#   "cs_CZ":        "cz",
    "de_DE":        "de",  # German.
#   "el_GR":        "el",
    "ru_RU":        "ru",  # Russian.
#   "sr_RS":        "sr",
#   "sv_SE":        "sv",
#   "tr_TR":        "th",
#   "uk_UA":        "uk",
    "es":           "es",  # Spanish.
#   "fi_FI":        "fi",
    "fr_FR":        "fr",  # French.
#   "id_ID":        "id",
#   "it_IT":        "it",
#   "ja_JP":        "ja",
#   "nl_NL":        "nl",
#   "pl_PL":        "pl",
    "pt_PT":        "pt",  # Portuguese.
    "pt_BR":        "pt",  # Portuguese - for until we have a pt_BR version.
    "zh_CN":        "zh.cn",  # Chinese - Should be changed to "zh_cn" but there is a bug in sphinx-intl.
    "zh_TW":        "zh.cn",  # Taiwanese Chinese - for until we have a zh_tw version.
}.get(language)

if LANG is not None:
    url_manual_prefix = url_manual_prefix.replace("manual/en", "manual/" + LANG)

# - The first item is a wildcard - typical file system globbing
#   using python module 'fnmatch.fnmatch'
# - Expressions are evaluated top down (include catch-all expressions last).

url_manual_mapping = (

    # *** User Prefs ***
    ("bpy.types.UserPreferences.*",                "preferences"),
    ("bpy.types.UserPreferencesView.*",            "preferences/interface.html"),
    ("bpy.types.UserPreferencesEdit.*",            "preferences/editing.html"),
    ("bpy.types.UserPreferencesInput.*",           "preferences/input.html"),
    ("bpy.types.Theme.*",                          "preferences/themes.html"),
    ("bpy.types.UserPreferencesFilePaths.*",       "preferences/file.html"),
    ("bpy.types.UserPreferencesSystem.*",          "preferences/system.html"),
    ("bpy.types.UserSolidLight.*",                 "preferences/system.html"),
    # --- Theme ---
    ("bpy.types.Theme*",                           "preferences/themes.html"),
    # --- Other ---
    ("bpy.types.Addon*",                           "preferences/addons.html"),
    ("bpy.types.AddonPreferences.*",               "preferences/addons.html#add-on-preferences"),

    # *** User Interface ***
    ("bpy.types.Area.*",                    "interface/window_system/areas.html"),
    ("bpy.types.AreaSpaces.*",              "interface/window_system/areas.html"),
    ("bpy.types.ConsoleLine.*",             "advanced/command_line"),
    ("bpy.types.Header.*",                  "interface/window_system/regions.html#header"),
    ("bpy.types.Panel.*",                   "interface/window_system/tabs_panels.html#panels"),
    ("bpy.types.Region.*",                  "interface/window_system/regions.html"),
    # ("bpy.types.UILayout.*",              ""),  # Todo
    # ("bpy.types.UIList.*",                ""),  # Todo
    ("bpy.types.Menu.*",                    "interface/controls/buttons/operators_menus.html#menu-buttons"),
    ("bpy.types.UIPieMenu.*",               "interface/controls/buttons/operators_menus.html#pie-menus"),
    ("bpy.types.UIPopupMenu.*",             "interface/controls/buttons/operators_menus.html#pop-up-menus"),
    ("bpy.types.Window.*",                  "interface/index.html#window-system"),
    ("bpy.types.WindowManager.*",           "interface/index.html#window-system"),
    # --- Spaces ---
    ("bpy.types.SpaceConsole.*",            "editors/python_console.html"),
    ("bpy.types.SpaceDopeSheetEditor.*",    "editors/dope_sheet"),
    ("bpy.types.SpaceFileBrowser.*",        "editors/file_browser/introduction.html"),
    ("bpy.types.SpaceGraphEditor.*",        "editors/graph_editor"),
    ("bpy.types.SpaceImageEditor.*",        "editors/uv_image"),
    ("bpy.types.SpaceInfo.*",               "editors/info"),
    ("bpy.types.SpaceLogicEditor.*",        "editors/logic_editor.html"),
    ("bpy.types.SpaceNLA.*",                "editors/nla.html"),
    ("bpy.types.SpaceNodeEditor.*",         "editors/node_editor"),
    ("bpy.types.SpaceOutliner.*",           "editors/outliner.html"),
    ("bpy.types.SpaceProperties.*",         "editors/properties_editor.html"),
    ("bpy.types.SpaceSequenceEditor.*",     "editors/sequencer"),
    ("bpy.types.SpaceTextEditor.*",         "editors/text_editor.html"),
    ("bpy.types.SpaceTimeline.*",           "editors/timeline.html"),
    ("bpy.types.SpaceUVEditor.*",           "editors/uv_image"),
    ("bpy.types.SpaceUserPreferences.*",    "preferences"),
    ("bpy.types.SpaceView3D.show_background_images", "editors/3dview/display/background_images.html"),
    ("bpy.types.SpaceView3D.*",             "editors/3dview"), # Catchall
    ("bpy.types.Space.*",                   "editors"),  # Catchall

    # *** Modifiers ***
    # --- Intro ---
    ("bpy.types.Modifier.show_*", "modeling/modifiers/introduction.html#the-modifier-stack"),
    ("bpy.types.Modifier.*", "modeling/modifiers"),  # Catchall for various generic options
    # --- Modify Modifiers ---
    ("bpy.types.DataTransferModifier.*",           "modeling/modifiers/modify/data_transfer.html"),
    ("bpy.types.MeshCacheModifier.*",              "modeling/modifiers/modify/mesh_cache.html"),
    ("bpy.types.NormalEditModifier.*",             "modeling/modifiers/modify/normal_edit.html"),
    ("bpy.types.UVProjectModifier.*",              "modeling/modifiers/modify/uv_project.html"),
    ("bpy.types.UVWarpModifier.*",                 "modeling/modifiers/modify/uv_warp.html"),
    ("bpy.types.VertexWeightMixModifier.*",        "modeling/modifiers/modify/weight_mix.html"),
    ("bpy.types.VertexWeightEditModifier.*",       "modeling/modifiers/modify/weight_edit.html"),
    ("bpy.types.VertexWeightProximityModifier.*",  "modeling/modifiers/modify/weight_proximity.html"),
    # --- Generate Modifiers ---
    ("bpy.types.ArrayModifier.*",            "modeling/modifiers/generate/array.html"),
    ("bpy.types.BevelModifier.*",            "modeling/modifiers/generate/bevel.html"),
    ("bpy.types.BooleanModifier.*",          "modeling/modifiers/generate/booleans.html"),
    ("bpy.types.BuildModifier.*",            "modeling/modifiers/generate/build.html"),
    ("bpy.types.DecimateModifier.*",         "modeling/modifiers/generate/decimate.html"),
    ("bpy.types.EdgeSplitModifier.*",        "modeling/modifiers/generate/edge_split.html"),
    ("bpy.types.MaskModifier.*",             "modeling/modifiers/generate/mask.html"),
    ("bpy.types.MirrorModifier.*",           "modeling/modifiers/generate/mirror.html"),
    ("bpy.types.MultiresModifier.*",         "modeling/modifiers/generate/multiresolution.html"),
    ("bpy.types.RemeshModifier.*",           "modeling/modifiers/generate/remesh.html"),
    ("bpy.types.ScrewModifier.*",            "modeling/modifiers/generate/screw.html"),
    ("bpy.types.SkinModifier.*",             "modeling/modifiers/generate/skin.html"),
    ("bpy.types.SolidifyModifier.*",         "modeling/modifiers/generate/solidify.html"),
    ("bpy.types.SubsurfModifier.*",          "modeling/modifiers/generate/subsurf.html"),
    ("bpy.types.TriangulateModifier.*",      "modeling/modifiers/generate/triangulate.html"),
    ("bpy.types.WireframeModifier.*",        "modeling/modifiers/generate/wireframe.html"),
    # --- Deform Modifiers ---
    ("bpy.types.ArmatureModifier.*",         "modeling/modifiers/deform/armature.html"),
    ("bpy.types.CastModifier.*",             "modeling/modifiers/deform/cast.html"),
    ("bpy.types.CorrectiveSmoothModifier.*", "modeling/modifiers/deform/corrective_smooth.html"),
    ("bpy.types.CurveModifier.*",            "modeling/modifiers/deform/curve.html"),
    ("bpy.types.DisplaceModifier.*",         "modeling/modifiers/deform/displace.html"),
    ("bpy.types.HookModifier.*",             "modeling/modifiers/deform/hooks.html"),
    ("bpy.types.LaplacianSmoothModifier.*",  "modeling/modifiers/deform/laplacian_smooth.html"),
    ("bpy.types.LaplacianDeformModifier.*",  "modeling/modifiers/deform/laplacian_deform.html"),
    ("bpy.types.LatticeModifier.*",          "modeling/modifiers/deform/lattice.html"),
    ("bpy.types.MeshDeformModifier.*",       "modeling/modifiers/deform/mesh_deform.html"),
    ("bpy.types.ShrinkwrapModifier.*",       "modeling/modifiers/deform/shrinkwrap.html"),
    ("bpy.types.SimpleDeformModifier.*",     "modeling/modifiers/deform/simple_deform.html"),
    ("bpy.types.SmoothModifier.*",           "modeling/modifiers/deform/smooth.html"),
    # ("bpy.types.SurfaceModifier.*",        "modeling/modifiers/deform/"),  # USERS NEVER SEE THIS
    ("bpy.types.WarpModifier.*",             "modeling/modifiers/deform/warp.html"),
    ("bpy.types.WaveModifier.*",             "modeling/modifiers/deform/wave.html"),
    # --- Simulate Modifiers ---
    ("bpy.types.ClothModifier.*",             "physics/cloth"),
    ("bpy.types.CollisionModifier.*",         "physics/collision.html"),
    ("bpy.types.DynamicPaintModifier.*",      "physics/dynamic_paint"),
    ("bpy.types.ExplodeModifier.*",           "modeling/modifiers/simulate/explode.html"),
    ("bpy.types.FluidSimulationModifier.*",   "physics/fluid"),
    ("bpy.types.OceanModifier.*",             "modeling/modifiers/simulate/ocean.html"),
    ("bpy.types.ParticleInstanceModifier.*",  "modeling/modifiers/simulate/particle_instance.html"),
    ("bpy.types.ParticleSystemModifier.*",    "physics/particles"),
    ("bpy.types.SmokeModifier.*",             "physics/smoke"),
    ("bpy.types.SoftBodyModifier.*",          "physics/soft_body"),

    # *** Constraints ***
    ("bpy.types.Constraint.influence",        "rigging/constraints/interface/influence.html"),
    ("bpy.types.Constraint.mute",             "rigging/constraints/interface/the_stack.html"),  # others could be added here?
    ("bpy.types.Constraint.*",                "rigging/constraints"),
    # --- Motion Tracking Constraints ---
    ("bpy.types.FollowTrackConstraint.*",     "rigging/constraints/motion_tracking/follow_track.html"),
    ("bpy.types.ObjectSolverConstraint.*",    "rigging/constraints/motion_tracking/object_solver.html"),
    ("bpy.types.CameraSolverConstraint.*",    "rigging/constraints/motion_tracking/camera_solver.html"),
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
    ("bpy.types.ClampToConstraint.*",         "rigging/constraints/tracking/clamp_to.html"),
    ("bpy.types.DampedTrackConstraint.*",     "rigging/constraints/tracking/damped_track.html"),
    ("bpy.types.KinematicConstraint.*",       "rigging/constraints/tracking/ik_solver.html"),
    ("bpy.types.LockedTrackConstraint.*",     "rigging/constraints/tracking/locked_track.html"),
    ("bpy.types.SplineIKConstraint.*",        "rigging/constraints/tracking/spline_ik.html"),
    ("bpy.types.StretchToConstraint.*",       "rigging/constraints/tracking/stretch_to.html"),
    ("bpy.types.TrackToConstraint.*",         "rigging/constraints/tracking/track_to.html"),
    # --- Relationship Constraints ---
    ("bpy.types.ActionConstraint.*",          "rigging/constraints/relationship/action.html"),
    ("bpy.types.ChildOfConstraint.*",         "rigging/constraints/relationship/action.html"),
    ("bpy.types.FloorConstraint.*",           "rigging/constraints/relationship/child_of.html"),
    ("bpy.types.FollowPathConstraint.*",      "rigging/constraints/relationship/follow_path.html"),
    ("bpy.types.PivotConstraint.*",           "rigging/constraints/relationship/pivot.html"),
    ("bpy.types.RigidBodyJointConstraint.*",  "rigging/constraints/relationship/rigid_body_joint.html"),
    ("bpy.types.ShrinkwrapConstraint.*",      "rigging/constraints/relationship/shrinkwrap.html"),

    # *** Render Settings ***
    ("bpy.types.ImageFormatSettings.*",        "data_system/files/media/image_formats.html"),
    ("bpy.types.RenderSettings.engine",        "render/introduction.html#render-engines"),
    ("bpy.types.RenderSettings.simplify_subdivision*", "data_system/scenes/properties.html#simplify"),
    ("bpy.types.RenderSettings.filepath",      "render/output/output.html#output-panel"),
    ("bpy.types.RenderSettings.display_mode",  "render/output/render_panel.html#display"),
    ("bpy.types.RenderSettings.*",             "render"),  # Catchall, todo - refine
    ("bpy.types.RenderEngine.*",               "render/introduction.html#render-engines"),
    ("bpy.types.RenderLayer*",                 "render/post_process/layers.html"),
    ("bpy.types.RenderPass.*",                 "render/blender_render/settings/passes.html"),
    ("bpy.types.RenderResult.*",               "editors/uv_image/image/introduction.html"),  # TODO-Refine
    ("bpy.types.RenderSlot*",                  "editors/uv_image/image/introduction.html"),  # TODO-Refine
    ("bpy.types.RenderView*",                  "render/workflows/multiview/usage.html#views-setup"),
    ("bpy.types.FFmpegSettings.audio_channels", "data_system/scenes/properties.html#audio"),
    ("bpy.types.FFmpegSettings.audio_mixrate",  "data_system/scenes/properties.html#audio"),
    ("bpy.types.FFmpegSettings.*",             "render/output/video.html#encoding-panel"),
    # --- Baking ---
    ("bpy.types.BakePixel.*",                  "render/blender_render/bake.html"),
    ("bpy.types.BakeSettings.*",               "render/blender_render/bake.html#options"),

    # Painting/Sculpting
    ("bpy.types.Sculpt.*",                     "sculpt_paint/sculpting"),
    ("bpy.types.SculptToolCapabilities.*",     "sculpt_paint/sculpting"),
    ("bpy.types.VertexColors.*",               "sculpt_paint/painting/vertex_paint"),
    ("bpy.types.VertexPaint.*",                "sculpt_paint/painting/vertex_paint/introduction.html"),

    # *** FreeStyle ***
    ("bpy.types.LineStyleAlphaModifier_AlongStroke.*",            "render/freestyle/parameter_editor/line_style/alpha.html#along-stroke"),
    ("bpy.types.LineStyleAlphaModifier_CreaseAngle.*",            "render/freestyle/parameter_editor/line_style/alpha.html#crease-angle"),
    ("bpy.types.LineStyleAlphaModifier_Curvature_3D.*",           "render/freestyle/parameter_editor/line_style/alpha.html#d-curvature"),
    ("bpy.types.LineStyleAlphaModifier_DistanceFromCamera.*",     "render/freestyle/parameter_editor/line_style/alpha.html#distance-from-camera"),
    ("bpy.types.LineStyleAlphaModifier_DistanceFromObject.*",     "render/freestyle/parameter_editor/line_style/alpha.html#distance-from-object"),
    ("bpy.types.LineStyleAlphaModifier_Material.*",               "render/freestyle/parameter_editor/line_style/alpha.html#material"),
    ("bpy.types.LineStyleAlphaModifier_Noise.*",                  "render/freestyle/parameter_editor/line_style/alpha.html#noise"),
    ("bpy.types.LineStyleAlphaModifier_Tangent.*",                "render/freestyle/parameter_editor/line_style/alpha.html#tangent"),
    ("bpy.types.LineStyleColorModifier_AlongStroke.*",            "render/freestyle/parameter_editor/line_style/color.html#along-stroke"),
    ("bpy.types.LineStyleColorModifier_CreaseAngle.*",            "render/freestyle/parameter_editor/line_style/color.html#crease-angle"),
    ("bpy.types.LineStyleColorModifier_Curvature_3D.*",           "render/freestyle/parameter_editor/line_style/color.html#d-curvature"),
    ("bpy.types.LineStyleColorModifier_DistanceFromCamera.*",     "render/freestyle/parameter_editor/line_style/color.html#distance-from-camera"),
    ("bpy.types.LineStyleColorModifier_DistanceFromObject.*",     "render/freestyle/parameter_editor/line_style/color.html#distance-from-object"),
    ("bpy.types.LineStyleColorModifier_Material.*",               "render/freestyle/parameter_editor/line_style/color.html#material"),
    ("bpy.types.LineStyleColorModifier_Noise.*",                  "render/freestyle/parameter_editor/line_style/color.html#noise"),
    ("bpy.types.LineStyleColorModifier_Tangent.*",                "render/freestyle/parameter_editor/line_style/color.html#tangent"),
    ("bpy.types.LineStyleGeometryModifier_2DOffset.*",            "render/freestyle/parameter_editor/line_style/geometry.html#d-offset"),
    ("bpy.types.LineStyleGeometryModifier_2DTransform.*",         "render/freestyle/parameter_editor/line_style/geometry.html#d-transform"),
    ("bpy.types.LineStyleGeometryModifier_BackboneStretcher.*",   "render/freestyle/parameter_editor/line_style/geometry.html#backbone-stretcher"),
    ("bpy.types.LineStyleGeometryModifier_BezierCurve.*",         "render/freestyle/parameter_editor/line_style/geometry.html#bezier-curve"),
    ("bpy.types.LineStyleGeometryModifier_Blueprint.*",           "render/freestyle/parameter_editor/line_style/geometry.html#blueprint"),
    ("bpy.types.LineStyleGeometryModifier_GuidingLines.*",        "render/freestyle/parameter_editor/line_style/geometry.html#guiding-lines"),
    ("bpy.types.LineStyleGeometryModifier_PerlinNoise1D.*",       "render/freestyle/parameter_editor/line_style/geometry.html#perlin-noise-1d"),
    ("bpy.types.LineStyleGeometryModifier_PerlinNoise2D.*",       "render/freestyle/parameter_editor/line_style/geometry.html#perlin-noise-2d"),
    ("bpy.types.LineStyleGeometryModifier_Polygonalization.*",    "render/freestyle/parameter_editor/line_style/geometry.html#polygonization"),
    ("bpy.types.LineStyleGeometryModifier_Sampling.*",            "render/freestyle/parameter_editor/line_style/geometry.html#sampling"),
    ("bpy.types.LineStyleGeometryModifier_Simplification.*",      "render/freestyle/parameter_editor/line_style/geometry.html#simplification"),
    ("bpy.types.LineStyleGeometryModifier_SinusDisplacement.*",   "render/freestyle/parameter_editor/line_style/geometry.html#sinus-displacement"),
    ("bpy.types.LineStyleGeometryModifier_SpatialNoise.*",        "render/freestyle/parameter_editor/line_style/geometry.html#spatial-noise"),
    ("bpy.types.LineStyleGeometryModifier_TipRemover.*",          "render/freestyle/parameter_editor/line_style/geometry.html#tip-remover"),
    # ("bpy.types.LineStyleTextureSlot.*",                        ""), Todo
    ("bpy.types.LineStyleThicknessModifier_AlongStroke.*",        "render/freestyle/parameter_editor/line_style/thickness.html#along-stroke"),
    ("bpy.types.LineStyleThicknessModifier_Calligraphy.*",        "render/freestyle/parameter_editor/line_style/thickness.html#calligraphy"),
    ("bpy.types.LineStyleThicknessModifier_CreaseAngle.*",        "render/freestyle/parameter_editor/line_style/thickness.html#crease-angle"),
    ("bpy.types.LineStyleThicknessModifier_Curvature_3D.*",       "render/freestyle/parameter_editor/line_style/thickness.html#d-curvature"),
    ("bpy.types.LineStyleThicknessModifier_DistanceFromCamera.*", "render/freestyle/parameter_editor/line_style/thickness.html#distance-from-camera"),
    ("bpy.types.LineStyleThicknessModifier_DistanceFromObject.*", "render/freestyle/parameter_editor/line_style/thickness.html#distance-from-object"),
    ("bpy.types.LineStyleThicknessModifier_Material.*",           "render/freestyle/parameter_editor/line_style/thickness.html#material"),
    ("bpy.types.LineStyleThicknessModifier_Noise.*",              "render/freestyle/parameter_editor/line_style/thickness.html#noise"),
    ("bpy.types.LineStyleThicknessModifier_Tangent.*",            "render/freestyle/parameter_editor/line_style/thickness.html#tangent"),
    ("bpy.types.FreestyleLineSet.*",                              "render/freestyle/parameter_editor/line_set.html"),
    ("bpy.types.FreestyleLineStyle.*",                            "render/freestyle/parameter_editor/line_style"),
    # ("bpy.types.FreestyleModuleSettings.*",                     ""), Todo
    # ("bpy.types.FreestyleSettings.*",                           ""), Todo
    ("bpy.types.Linesets.*",                                      "render/freestyle/parameter_editor/line_set.html"),

    # *** Materials (blender internal) ***
    ("bpy.types.Material.diffuse*",               "render/blender_render/materials/properties/diffuse_shaders.html"),
    ("bpy.types.Material.specular*",              "render/blender_render/materials/properties/specular_shaders.html"),
    ("bpy.types.Material.ambient*",               "render/blender_render/materials/properties/shading.html"),
    ("bpy.types.Material.preview_render_type",    "render/blender_render/materials/properties/preview.html"),
    ("bpy.types.Material.*",                      "render/blender_render/materials"),  # Catchall
    # ("bpy.types.MaterialSlot.link",             "render/blender_render/materials/options.html#material-naming_and_linking"),  # TODO, T42839
    ("bpy.types.MaterialVolume.*",                "render/blender_render/materials/special_effects/volume.html"),
    ("bpy.types.MaterialHalo.*",                  "render/blender_render/materials/special_effects/halo.html"),
    ("bpy.types.MaterialStrand.*",                "render/blender_render/materials/properties/strands.html"),
    ("bpy.types.MaterialSubsurfaceScattering.*",  "render/blender_render/materials/properties/subsurface_scattering.html"),
    ("bpy.types.MaterialRaytraceMirror.*",        "render/blender_render/materials/properties/mirror.html"),
    ("bpy.types.MaterialRaytraceTransparency.*",  "render/blender_render/materials/properties/transparency.html#raytraced-transparency"),
    # --- Textures ---
    ("bpy.types.BlendTexture.*",              "render/blender_render/textures/types/procedural/blend.html"),
    ("bpy.types.CloudsTexture.*",             "render/blender_render/textures/types/procedural/clouds.html"),
    ("bpy.types.DistortedNoiseTexture.*",     "render/blender_render/textures/types/procedural/distorted_noise.html"),
    ("bpy.types.EnvironmentMapTexture.*",     "render/blender_render/textures/types/environment.html"),
    ("bpy.types.ImageTexture.*",              "render/blender_render/textures/types/image"),
    ("bpy.types.MagicTexture.*",              "render/blender_render/textures/types/procedural/magic.html"),
    ("bpy.types.MarbleTexture.*",             "render/blender_render/textures/types/procedural/marble.html"),
    ("bpy.types.MusgraveTexture.*",           "render/blender_render/textures/types/procedural/musgrave.html"),
    ("bpy.types.OceanTexture.*",              "render/blender_render/textures/types/procedural/ocean.html"),
    ("bpy.types.PointDensityTexture.*",       "render/blender_render/textures/types/volume/point_density.html"),
    ("bpy.types.StucciTexture.*",             "render/blender_render/textures/types/procedural/stucci.html"),
    ("bpy.types.VoronoiTexture.*",            "render/blender_render/textures/types/procedural/voronoi.html"),
    ("bpy.types.VoxelDataTexture.*",          "render/blender_render/textures/types/volume/voxel_data.html"),
    ("bpy.types.WoodTexture.*",               "render/blender_render/textures/types/procedural/wood.html"),
    # Nodes
    ("bpy.types.TextureNodeBricks.*",        "render/blender_render/textures/nodes/types/patterns/bricks.html"),
    ("bpy.types.TextureNodeCurveRGB.*",      "render/blender_render/textures/nodes/types/color/rgb_curves.html"),
    ("bpy.types.TextureNodeCurveTime.*",     "render/blender_render/textures/nodes/types/input/time.html"),
    ("bpy.types.TextureNodeGroup.*",         "editors/node_editor/nodes/groups.html"),
    ("bpy.types.TextureNodeImage.*",         "render/blender_render/textures/nodes/types/input/image.html"),
    ("bpy.types.TextureNodeMath.*",          "render/blender_render/textures/nodes/types/converter/math.html"),
    ("bpy.types.TextureNodeMixRGB.*",        "render/blender_render/textures/nodes/types/color/mix_rgb.html"),
    ("bpy.types.TextureNodeOutput.*",        "render/blender_render/textures/nodes/types/output/output.html"),
    ("bpy.types.TextureNodeTexture.*",       "render/blender_render/textures/nodes/types/input/texture.html"),
    ("bpy.types.TextureNodeValToRGB.*",      "render/blender_render/textures/nodes/types/converter/rgb_to_bw.html"),
    # ... todo, many more options

    # *** Movie Clip ***
    ("bpy.types.MovieTrackingCamera.*",        "editors/movie_clip_editor/tracking/clip/properties.html#camera-data-panel"),
    ("bpy.types.MovieTrackingStabilization.*", "editors/movie_clip_editor/tracking/clip/properties.html#d-stabilization-panel"),
    ("bpy.types.MovieTrackingTrack*",          "editors/movie_clip_editor/tracking/clip/properties.html#track-panel"),
    ("bpy.types.MovieTracking*",               "editors/movie_clip_editor/tracking"),
    ("bpy.types.SpaceClipEditor.*",            "editors/movie_clip_editor/introduction.html"),
    ("bpy.types.MovieClipProxy.*",             "editors/movie_clip_editor/properties/proxy.html"),
    ("bpy.types.MovieClip.*",                  "editors/movie_clip_editor"), # Catchall

    ("bpy.types.ColorManagedSequencer*",       "render/post_process/color_management.html#sequencer"),
    ("bpy.types.ColorManagedViewSettings*",    "render/post_process/color_management.html#render"),
    ("bpy.types.ColorManagedDisplaySettings*", "render/post_process/color_management.html#display"),
    ("bpy.types.ColorManaged*",                "render/post_process/color_management.html"),
    # ("bpy.types.NodeTree.*",                 ""), # dont document
    ("bpy.types.Scene.camera",                 "data_system/scenes/properties.html#scene"),
    ("bpy.types.Scene.background_set",         "data_system/scenes/properties.html#scene"),
    ("bpy.types.Scene.active_clip",            "data_system/scenes/properties.html#scene"),
    ("bpy.types.Scene.audio_volume*",          "data_system/scenes/properties.html#audio"),
    ("bpy.types.Scene.gravity",                "physics/introduction.html#gravity"),
    ("bpy.types.Scene.*",                      "data_system/scenes"),
    ("bpy.types.UnitSettings.*",               "data_system/scenes/properties.html#units"),
    ("bpy.types.Screen.*",                     "interface/window_system/screens.html"),
    ("bpy.types.Sound.*",                      "render/audio/speaker.html"),
    ("bpy.types.Speaker.*",                    "render/audio/speaker.html"),
    ("bpy.types.Text.*",                       "editors/text_editor.html"),
    ("bpy.types.Texture.*",                    "render/blender_render/textures"),
    ("bpy.types.VectorFont.*",                 "modeling/texts"),
    ("bpy.types.World.*",                      "render/blender_render/world"),
    ("bpy.types.WorldLighting.ao*",            "render/blender_render/world/ambient_occlusion.html"),
    # only other WorldLighting props are in Gather panel
    ("bpy.types.WorldLighting.*",              "render/blender_render/world/ambient_occlusion.html#gather"),
    ("bpy.types.LatticePoint.*",               "rigging/lattice.html"),  # TODO refine
    ("bpy.types.DisplaySafeAreas.*",           "render/blender_render/camera/object_data.html#safe-areas"),
    ("bpy.types.TextCharacterFormat.*",        "modeling/texts/introduction.html"),  # TODO refine
    ("bpy.types.TextLine.*",                   "modeling/texts/introduction.html"),  # TODO refine

    # *** 3D View ***
    ("bpy.types.GPUDOFSettings.*",             "editors/3dview/display/shading.html#shading-panel"),
    ("bpy.types.GPUFXSettings.*",              "editors/3dview/display/shading.html#shading-panel"),
    ("bpy.types.GPUSSAOSettings.*",            "editors/3dview/display/shading.html#shading-panel"),
    ("bpy.types.BackgroundImage.*",            "editors/3dview/display/background_images.html"),
    ("bpy.types.WalkNavigation.*",             "editors/3dview/navigate/3d_view.html#walk-mode"),
    ("bpy.types.SpaceView3D.cursor_location",  "editors/3dview/3d_cursor.html#numeric-input"),
    ("bpy.types.Object.location",              "editors/3dview/object/properties/transforms.html"),
    ("bpy.types.Object.lock_location",         "editors/3dview/object/properties/transforms.html#transform-properties-locking"),
    ("bpy.types.Object.rotation_euler",        "editors/3dview/object/properties/transforms.html"),
    ("bpy.types.Object.rotation_quaternion",   "editors/3dview/object/properties/transforms.html"),
    ("bpy.types.Object.rotation_axis_angle",   "editors/3dview/object/properties/transforms.html"),
    ("bpy.types.Object.rotation_mode",         "editors/3dview/object/properties/transforms.html"),
    ("bpy.types.Object.lock_rotations_4d",     "editors/3dview/object/properties/transforms.html#transform-properties-locking"),  # Todo
    ("bpy.types.Object.lock_rotation",         "editors/3dview/object/properties/transforms.html#transform-properties-locking"),
    ("bpy.types.Object.scale",                 "editors/3dview/object/properties/transforms.html"),
    ("bpy.types.Object.lock_scale",            "editors/3dview/object/properties/transforms.html#transform-properties-locking"),
    ("bpy.types.Object.dimensions",            "editors/3dview/object/properties/transforms.html"),
    ("bpy.types.Object.delta*",                "editors/3dview/object/properties/transforms.html#delta-transforms"),
    ("bpy.types.Object.layers",                "editors/3dview/object/properties/relations/layers.html"),
    ("bpy.types.Object.dupli_type",            "editors/3dview/object/properties/duplication"),
    ("bpy.types.Object.dupli_frames*",         "editors/3dview/object/properties/duplication/dupliframes.html"),
    ("bpy.types.Object.use_dupli_vertices*",   "editors/3dview/object/properties/duplication/dupliverts.html"),
    ("bpy.types.Object.use_dupli_faces*",      "editors/3dview/object/properties/duplication/duplifaces.html"),
    ("bpy.types.Object.dupli_group",           "editors/3dview/object/properties/duplication/dupligroup.html"),
    ("bpy.types.Object.parent",                "editors/3dview/object/properties/relations/parents.html"),
    ("bpy.types.Object.use_slow_parent*",      "editors/3dview/object/properties/relations/extras.html"),
    ("bpy.types.Object.slow_parent_offset",    "editors/3dview/object/properties/relations/extras.html"),
    ("bpy.types.Object.track_axis",            "editors/3dview/object/properties/relations/extras.html"),
    ("bpy.types.Object.up_axis",               "editors/3dview/object/properties/relations/extras.html"),
    ("bpy.types.Object.use_extra*",            "editors/3dview/object/properties/relations/extras.html"),
    ("bpy.types.Object.show*",                 "editors/3dview/object/properties/display.html"),
    ("bpy.types.Object.draw_type",             "editors/3dview/object/properties/display.html"),
    ("bpy.types.Object.color",                 "editors/3dview/object/properties/display.html"),
    ("bpy.types.Object.*",                     "editors/3dview/object"),  # Catchall
    ("bpy.types.TransformOrientation.*",       "editors/3dview/object/transform/transform_control/transform_orientations.html"),

    # === Tool Settings ===
    ("bpy.types.MeshStatVis.*",                "modeling/meshes/mesh_analysis.html"),

    # *** Cycles ***
    ("bpy.types.CyclesRenderSettings.use_camera_cull",            "data_system/scenes/properties.html#simplify"),
    ("bpy.types.CyclesRenderSettings.camera_cull_margin",         "data_system/scenes/properties.html#simplify"),
    ("bpy.types.CyclesRenderSettings.dicing_rate",                "render/cycles/settings/integrator.html#subdivision-rate"),
    ("bpy.types.CyclesRenderSettings.preview_dicing_rate",        "render/cycles/settings/integrator.html#subdivision-rate"),
    ("bpy.types.CyclesRenderSettings.max_subdivisions",           "render/cycles/settings/integrator.html#subdivision-rate"),
    ("bpy.types.CyclesRenderSettings.*",                          "render/cycles/settings/integrator.html"),  # Catchall
    ("bpy.types.CyclesVisibilitySettings.*",                      "render/cycles/settings/light_paths.html#ray-visibility"),
    ("bpy.types.CyclesWorldSettings.*",                           "render/cycles/world.html"),
    ("bpy.types.SceneRenderLayer.*",                              "render/post_process/layers.html"),
    ("bpy.types.CyclesMaterialSettings.displacement_method",      "render/cycles/materials/settings.html#displacement"),
    ("bpy.types.CyclesMaterialSettings.*",                        "render/cycles/materials/settings.html"),  # Catchall
    ("bpy.types.CyclesObjectSettings.use_adaptive_subdivision",   "render/cycles/materials/displacement.html#true-displacement"),
    ("bpy.types.CyclesObjectSettings.dicing_rate",                "render/cycles/materials/displacement.html#true-displacement"),
    ("bpy.types.Cycles*",                                         "render/cycles"),  # Catchall

    # Currently all manual links on all sockets and values (such as Fac, Roughness, Color...) are NodeSocket* type.
    # It'd be much better if the name of the socket could be used for the manual reference
    ("bpy.types.NodeSocket*", "editors/node_editor/nodes/parts.html"),  # no generic socket type page exists, but composite types are the same

    # *** Cycles Material Nodes ***
    # Input
    ("bpy.types.ShaderNodeTexCoord.*",        "render/cycles/nodes/types/input/texture_coordinate.html"),
    ("bpy.types.ShaderNodeAttribute.*",       "render/cycles/nodes/types/input/attribute.html"),
    ("bpy.types.ShaderNodeLightPath.*",       "render/cycles/nodes/types/input/light_path.html"),
    ("bpy.types.ShaderNodeFresnel.*",         "render/cycles/nodes/types/input/fresnel.html"),
    ("bpy.types.ShaderNodeLayerWeight.*",     "render/cycles/nodes/types/input/layer_weight.html"),
    ("bpy.types.ShaderNodeRGB.*",             "render/cycles/nodes/types/input/rgb.html"),
    ("bpy.types.ShaderNodeValue.*",           "render/cycles/nodes/types/input/value.html"),
    ("bpy.types.ShaderNodeTangent.*",         "render/cycles/nodes/types/input/tangent.html"),
    ("bpy.types.ShaderNodeGeometry.*",        "render/cycles/nodes/types/input/geometry.html"),
    ("bpy.types.ShaderNodeWireframe.*",       "render/cycles/nodes/types/input/wireframe.html"),
    ("bpy.types.ShaderNodeObjectInfo.*",      "render/cycles/nodes/types/input/object_info.html"),
    ("bpy.types.ShaderNodeHairInfo.*",        "render/cycles/nodes/types/input/hair_info.html"),
    ("bpy.types.ShaderNodeParticleInfo.*",    "render/cycles/nodes/types/input/particle_info.html"),
    ("bpy.types.ShaderNodeCameraData.*",      "render/cycles/nodes/types/input/camera_data.html"),
    ("bpy.types.ShaderNodeUVMap",             "render/cycles/nodes/types/input/uv_map.html"),
    # Outputs
    ("bpy.types.ShaderNodeOutputLamp.*",           "render/cycles/nodes/types/output/lamp.html"),
    ("bpy.types.ShaderNodeOutputMaterial.*",       "render/cycles/nodes/types/output/material.html"),
    ("bpy.types.ShaderNodeOutputWorld.*",          "render/cycles/nodes/types/output/world.html"),
    # Shaders
    ("bpy.types.ShaderNodeAddShader.*",            "render/cycles/nodes/types/shaders/add.html"),
    ("bpy.types.ShaderNodeAmbientOcclusion.*",     "render/cycles/nodes/types/shaders/ao.html"),
    ("bpy.types.ShaderNodeBackground.*",           "render/cycles/nodes/types/shaders/background.html"),
    ("bpy.types.ShaderNodeBsdfAnisotropic.*",      "render/cycles/nodes/types/shaders/anisotropic.html"),
    ("bpy.types.ShaderNodeBsdfDiffuse.*",          "render/cycles/nodes/types/shaders/diffuse.html"),
    ("bpy.types.ShaderNodeBsdfGlass.*",            "render/cycles/nodes/types/shaders/glass.html"),
    ("bpy.types.ShaderNodeBsdfGlossy.*",           "render/cycles/nodes/types/shaders/glossy.html"),
    ("bpy.types.ShaderNodeBsdfHair.*",             "render/cycles/nodes/types/shaders/hair.html"),
    ("bpy.types.ShaderNodeBsdfRefraction.*",       "render/cycles/nodes/types/shaders/refraction.html"),
    ("bpy.types.ShaderNodeBsdfToon.*",             "render/cycles/nodes/types/shaders/toon.html"),
    ("bpy.types.ShaderNodeBsdfTranslucent.*",      "render/cycles/nodes/types/shaders/translucent.html"),
    ("bpy.types.ShaderNodeBsdfTransparent.*",      "render/cycles/nodes/types/shaders/transparent.html"),
    ("bpy.types.ShaderNodeBsdfVelvet.*",           "render/cycles/nodes/types/shaders/velvet.html"),
    ("bpy.types.ShaderNodeEmission.*",             "render/cycles/nodes/types/shaders/emission.html"),
    ("bpy.types.ShaderNodeHoldout.*",              "render/cycles/nodes/types/shaders/holdout.html"),
    ("bpy.types.ShaderNodeMixShader.*",            "render/cycles/nodes/types/shaders/mix.html"),
    ("bpy.types.ShaderNodeSubsurfaceScattering.*", "render/cycles/nodes/types/shaders/sss.html"),
    ("bpy.types.ShaderNodeVolumeAbsorption.*",     "render/cycles/nodes/types/shaders/volume_absorption.html"),
    ("bpy.types.ShaderNodeVolumeScatter.*",        "render/cycles/nodes/types/shaders/volume_scatter.html"),
    # Textures
    ("bpy.types.ShaderNodeTexBrick.*",        "render/cycles/nodes/types/textures/brick.html"),
    ("bpy.types.ShaderNodeTexChecker.*",      "render/cycles/nodes/types/textures/checker.html"),
    ("bpy.types.ShaderNodeTexEnvironment.*",  "render/cycles/nodes/types/textures/environment.html"),
    ("bpy.types.ShaderNodeTexGradient.*",     "render/cycles/nodes/types/textures/gradient.html"),
    ("bpy.types.ShaderNodeTexImage.*",        "render/cycles/nodes/types/textures/image.html"),
    ("bpy.types.ShaderNodeTexMagic.*",        "render/cycles/nodes/types/textures/magic.html"),
    ("bpy.types.ShaderNodeTexMusgrave.*",     "render/cycles/nodes/types/textures/musgrave.html"),
    ("bpy.types.ShaderNodeTexNoise.*",        "render/cycles/nodes/types/textures/noise.html"),
    ("bpy.types.ShaderNodeTexSky.*",          "render/cycles/nodes/types/textures/sky.html"),
    ("bpy.types.ShaderNodeTexVoronoi.*",      "render/cycles/nodes/types/textures/voronoi.html"),
    ("bpy.types.ShaderNodeTexWave.*",         "render/cycles/nodes/types/textures/wave.html"),
    # Color
    ("bpy.types.ShaderNodeMixRGB.*",          "render/cycles/nodes/types/color/mix.html"),
    ("bpy.types.ShaderNodeRGBCurve.*",        "render/cycles/nodes/types/color/rgb_curves.html"),
    ("bpy.types.ShaderNodeInvert.*",          "render/cycles/nodes/types/color/invert.html"),
    ("bpy.types.ShaderNodeLightFalloff.*",    "render/cycles/nodes/types/color/light_falloff.html"),
    ("bpy.types.ShaderNodeHueSaturation.*",   "render/cycles/nodes/types/color/hue_saturation.html"),
    ("bpy.types.ShaderNodeGamma.*",           "render/cycles/nodes/types/color/gamma.html"),
    ("bpy.types.ShaderNodeBrightContrast.*",  "render/cycles/nodes/types/color/bright_contrast.html"),
    # Vector
    ("bpy.types.ShaderNodeMapping.*",         "render/cycles/nodes/types/vector/mapping.html"),
    ("bpy.types.ShaderNodeBump.*",            "render/cycles/nodes/types/vector/bump.html"),
    ("bpy.types.ShaderNodeNormalMap.*",       "render/cycles/nodes/types/vector/normal_map.html"),
    ("bpy.types.ShaderNodeNormal",            "render/cycles/nodes/types/vector/normal.html"),
    ("bpy.types.ShaderNodeVectorCurve.*",     "render/cycles/nodes/types/vector/curves.html"),
    ("bpy.types.ShaderNodeVectorTransform.*", "render/cycles/nodes/types/vector/transform.html"),
    # Converter
    ("bpy.types.ShaderNodeMath.*",            "render/cycles/nodes/types/converter/math.html"),
    ("bpy.types.ShaderNodeRGBToBW.*",         "render/cycles/nodes/types/converter/rgb_to_bw.html"),
    ("bpy.types.ShaderNodeVectorMath.*",      "render/cycles/nodes/types/converter/vector_math.html"),
    ("bpy.types.ShaderNodeCombineHSV.*",      "render/cycles/nodes/types/converter/combine_separate.html"),
    ("bpy.types.ShaderNodeSeparateHSV.*",     "render/cycles/nodes/types/converter/combine_separate.html"),
    ("bpy.types.ShaderNodeCombineRGB.*",      "render/cycles/nodes/types/converter/combine_separate.html"),
    ("bpy.types.ShaderNodeSeparateRGB.*",     "render/cycles/nodes/types/converter/combine_separate.html"),
    ("bpy.types.ShaderNodeCombineXYZ",        "render/cycles/nodes/types/converter/combine_separate.html"),
    ("bpy.types.ShaderNodeSeparateXYZ",       "render/cycles/nodes/types/converter/combine_separate.html"),
    ("bpy.types.ShaderNodeWavelength.*",      "render/cycles/nodes/types/converter/wavelength.html"),
    ("bpy.types.ShaderNodeBlackbody.*",       "render/cycles/nodes/types/converter/blackbody.html"),
    # Other
    ("bpy.types.ShaderNodeGroup.*",           "editors/node_editor/nodes/groups.html"),
    ("bpy.types.ShaderNodeScript.*",          "render/cycles/nodes/osl.html"),
    ("bpy.types.ShaderNode*",                 "render/cycles/nodes"),  # Catch all

    # *** Compositing Nodes ***
    # Input
    ("bpy.types.CompositorNodeBokehImage.*",  "compositing/types/input/bokeh_image.html"),
    ("bpy.types.CompositorNodeImage.*",       "compositing/types/input/image.html"),
    ("bpy.types.CompositorNodeMask.*",        "compositing/types/input/mask.html"),
    ("bpy.types.CompositorNodeMovieClip.*",   "compositing/types/input/movie_clip.html"),
    ("bpy.types.CompositorNodeRGB.*",         "compositing/types/input/rgb.html"),
    ("bpy.types.CompositorNodeRLayers.*",     "compositing/types/input/render_layers.html"),
    ("bpy.types.CompositorNodeTexture.*",     "compositing/types/input/texture.html"),
    ("bpy.types.CompositorNodeTime.*",        "compositing/types/input/time.html"),
    ("bpy.types.CompositorNodeTrackPos.*",    "compositing/types/input/track_position.html"),
    ("bpy.types.CompositorNodeValue.*",       "compositing/types/input/value.html"),
    # Output
    ("bpy.types.CompositorNodeComposite.*",   "compositing/types/output/composite.html"),
    ("bpy.types.CompositorNodeLevels.*",      "compositing/types/output/levels.html"),
    ("bpy.types.CompositorNodeOutputFile*",   "compositing/types/output/file.html"),
    ("bpy.types.CompositorNodeSplitViewer.*", "compositing/types/output/split_viewer.html"),
    ("bpy.types.CompositorNodeViewer.*",      "compositing/types/output/viewer.html"),
    # Color
    ("bpy.types.CompositorNodeAlphaOver.*",       "compositing/types/color/alpha_over.html"),
    ("bpy.types.CompositorNodeBrightContrast.*",  "compositing/types/color/bright_contrast.html"),
    ("bpy.types.CompositorNodeColorBalance.*",    "compositing/types/color/bright_contrast.html"),
    ("bpy.types.CompositorNodeColorCorrection.*", "compositing/types/color/color_correction.html"),
    ("bpy.types.CompositorNodeCurveRGB.*",        "compositing/types/color/rgb_curves.html"),
    ("bpy.types.CompositorNodeGamma.*",           "compositing/types/color/gamma.html"),
    ("bpy.types.CompositorNodeHueCorrect.*",      "compositing/types/color/hue_correct.html"),
    ("bpy.types.CompositorNodeHueSat.*",          "compositing/types/color/hue_saturation.html"),
    ("bpy.types.CompositorNodeInvert.*",          "compositing/types/color/invert.html"),
    ("bpy.types.CompositorNodeMixRGB.*",          "compositing/types/color/mix.html"),
    ("bpy.types.CompositorNodeTonemap.*",         "compositing/types/color/tone_map.html"),
    ("bpy.types.CompositorNodeZcombine.*",        "compositing/types/color/z_combine.html"),
    # Converter
    ("bpy.types.CompositorNodeSep*",         "compositing/types/converter/combine_separate.html"),
    ("bpy.types.CompositorNodeComb*",        "compositing/types/converter/combine_separate.html"),
    ("bpy.types.CompositorNodeIDMask.*",     "compositing/types/converter/id_mask.html"),
    ("bpy.types.CompositorNodeMath.*",       "compositing/types/converter/math.html"),
    ("bpy.types.CompositorNodePremulKey.*",  "compositing/types/converter/alpha_convert.html"),
    ("bpy.types.CompositorNodeRGBToBW.*",    "compositing/types/converter/rgb_to_bw.html"),
    ("bpy.types.CompositorNodeSetAlpha.*",   "compositing/types/converter/set_alpha.html"),
    # Filter
    ("bpy.types.CompositorNodeBilateralblur.*", "compositing/types/filter/bilateral_blur.html"),
    ("bpy.types.CompositorNodeBlur.*",          "compositing/types/filter/blur_node.html"),
    ("bpy.types.CompositorNodeBokehBlur.*",     "compositing/types/filter/bokeh_blur.html"),
    ("bpy.types.CompositorNodeDBlur.*",         "compositing/types/filter/directional_blur.html"),
    ("bpy.types.CompositorNodeDefocus.*",       "compositing/types/filter/defocus.html"),
    ("bpy.types.CompositorNodeDespeckle.*",     "compositing/types/filter/despeckle.html"),
    ("bpy.types.CompositorNodeDilateErode.*",   "compositing/types/filter/dilate_erode.html"),
    ("bpy.types.CompositorNodeFilter.*",        "compositing/types/filter/filter_node.html"),
    ("bpy.types.CompositorNodeGlare.*",         "compositing/types/filter/glare.html"),
    ("bpy.types.CompositorNodeInpaint.*",       "compositing/types/filter/inpaint.html"),
    ("bpy.types.CompositorNodePixelate.*",      "compositing/types/filter/pixelate.html"),
    ("bpy.types.CompositorNodeSunBeams.*",      "compositing/types/filter/sun_beams.html"),
    ("bpy.types.CompositorNodeVecBlur.*",       "compositing/types/filter/vector_blur.html"),
    # Vector
    ("bpy.types.CompositorNodeCurveVec.*",   "compositing/types/vector/vector_curves.html"),
    ("bpy.types.CompositorNodeMapRange.*",   "compositing/types/vector/map_range.html"),
    ("bpy.types.CompositorNodeMapValue.*",   "compositing/types/vector/map_value.html"),
    ("bpy.types.CompositorNodeNormal.*",     "compositing/types/vector/normal.html"),
    ("bpy.types.CompositorNodeNormalize.*",  "compositing/types/vector/normalize.html"),
    # Matte
    ("bpy.types.CompositorNodeBoxMask.*",        "compositing/types/matte/box_mask.html"),
    ("bpy.types.CompositorNodeChannelMatte.*",   "compositing/types/matte/channel_key.html"),
    ("bpy.types.CompositorNodeChromaMatte.*",    "compositing/types/matte/chroma_key.html"),
    ("bpy.types.CompositorNodeColorMatte.*",     "compositing/types/matte/color_key.html"),
    ("bpy.types.CompositorNodeColorSpill.*",     "compositing/types/matte/color_spill_key.html"),
    ("bpy.types.CompositorNodeDiffMatte.*",      "compositing/types/matte/difference_key.html"),
    ("bpy.types.CompositorNodeDistanceMatte.*",  "compositing/types/matte/difference_key.html"),
    ("bpy.types.CompositorNodeDoubleEdgeMask.*", "compositing/types/matte/double_edge_mask.html"),
    ("bpy.types.CompositorNodeEllipseMask.*",    "compositing/types/matte/ellipse_mask.html"),
    ("bpy.types.CompositorNodeKeying.*",         "compositing/types/matte/keying.html"),
    ("bpy.types.CompositorNodeKeyingScreen.*",   "compositing/types/matte/keying_screen.html"),
    ("bpy.types.CompositorNodeLumaMatte.*",      "compositing/types/matte/luminance_key.html"),
    # Distort
    ("bpy.types.CompositorNodeCrop.*",             "compositing/types/distort/crop.html"),
    ("bpy.types.CompositorNodeDisplace.*",         "compositing/types/distort/displace.html"),
    ("bpy.types.CompositorNodeFlip.*",             "compositing/types/distort/flip.html"),
    ("bpy.types.CompositorNodeLensdist.*",         "compositing/types/distort/lens.html"),
    ("bpy.types.CompositorNodeMapUV.*",            "compositing/types/distort/map_uv.html"),
    ("bpy.types.CompositorNodeMovieDistortion.*",  "compositing/types/distort/movie_distortion.html"),
    ("bpy.types.CompositorNodePlaneTrackDeform.*", "compositing/types/distort/plane_track_deform.html"),
    ("bpy.types.CompositorNodeRotate.*",           "compositing/types/distort/rotate.html"),
    ("bpy.types.CompositorNodeScale.*",            "compositing/types/distort/scale.html"),
    ("bpy.types.CompositorNodeStabilize.*",        "compositing/types/distort/stabilize_2d.html"),
    ("bpy.types.CompositorNodeTransform.*",        "compositing/types/distort/transform.html"),
    ("bpy.types.CompositorNodeTranslate.*",        "compositing/types/distort/translate.html"),
    # Other
    ("bpy.types.CompositorNodeGroup.*",            "editors/node_editor/nodes/groups.html"),
    ("bpy.types.CompositorNode*",                  "compositing/types"),  # catch anything else

    ("bpy.types.ColorRamp*",                       "interface/controls/templates/color_ramp.html"),

    # *** Node ***
    ("bpy.types.Node.*",                           "editors/node_editor/nodes"),
    ("bpy.types.NodeCustomGroup.*",                "editors/node_editor/nodes/groups.html"),
    ("bpy.types.NodeFrame.*",                      "compositing/types/layout/frame.html"),  # TODO refine
    ("bpy.types.NodeGroup.*",                      "editors/node_editor/nodes/groups.html"),
    ("bpy.types.NodeGroupInput.*",                 "editors/node_editor/nodes/groups.html"),
    ("bpy.types.NodeGroupOutput.*",                "editors/node_editor/nodes/groups.html"),
    # ("bpy.types.NodeInternalSocketTemplate.*",   ""), # TODO
    ("bpy.types.NodeLink.*",                       "editors/node_editor/nodes/parts.html#sockets"),
    # ("bpy.types.NodeOutputFileSlotFile.*",       ""), # TODO
    # ("bpy.types.NodeOutputFileSlotLayer.*",      ""), # TODO
    ("bpy.types.NodeSetting.*",                    "editors/node_editor/nodes/parts.html#settings"),
    ("bpy.types.NodeTree.*",                       "editors/node_editor/nodes/parts.html"),
    ("bpy.types.NodeTreePath.*",                   "editors/node_editor/nodes/parts.html"),

    # *** Sequencer ***
    ("bpy.types.AddSequence.*",            "editors/sequencer/strips/types/effects/add.html"),
    ("bpy.types.AdjustmentSequence.*",     "editors/sequencer/strips/types/effects/adjustment.html"),
    ("bpy.types.AlphaOverSequence.*",      "editors/sequencer/strips/types/effects/alpha_over_under_overdrop.html"),
    ("bpy.types.AlphaUnderSequence.*",     "editors/sequencer/strips/types/effects/alpha_over_under_overdrop.html"),
    ("bpy.types.ColorSequence.*",          "editors/sequencer/strips/types/effects/color.html"),
    ("bpy.types.CrossSequence.*",          "editors/sequencer/strips/types/effects/cross.html"),
    ("bpy.types.EffectSequence.*",         "editors/sequencer/strips/types/effects"),
    ("bpy.types.GammaCrossSequence.*",     "editors/sequencer/strips/types/effects/cross.html"),
    ("bpy.types.GaussianBlurSequence.*",   "editors/sequencer/strips/types/effects/blur.html"),
    ("bpy.types.GlowSequence.*",           "editors/sequencer/strips/types/effects/glow.html"),
    ("bpy.types.ImageSequence.*",          "editors/sequencer/strips/types/image_movie.html"),
    ("bpy.types.MaskSequence.*",           "editors/sequencer/strips/types/mask.html"),
    ("bpy.types.MetaSequence.*",           "editors/sequencer/strips/meta.html"),
    ("bpy.types.MovieSequence.*",          "editors/sequencer/strips/types/image_movie.html"),
    ("bpy.types.MovieClipSequence.*",      "editors/sequencer/strips/types/image_movie.html"),  # Refine
    ("bpy.types.MulticamSequence.*",       "editors/sequencer/strips/types/effects/multicam.html"),
    ("bpy.types.MultiplySequence.*",       "editors/sequencer/strips/types/effects/multiply.html"),
    ("bpy.types.OverDropSequence.*",       "editors/sequencer/strips/types/effects/alpha_over_under_overdrop.html"),
    ("bpy.types.SceneSequence.*",          "editors/sequencer/strips/types/scene.html"),
    ("bpy.types.SoundSequence.*",          "editors/sequencer/strips/types/audio.html"),
    ("bpy.types.SpeedControlSequence.*",   "editors/sequencer/strips/types/effects/speed_control.html"),
    ("bpy.types.SubtractSequence.*",       "editors/sequencer/strips/types/effects/subtract.html"),
    ("bpy.types.TextSequence.*",           "editors/sequencer/strips/types/effects/text.html"),
    ("bpy.types.TransformSequence.*",      "editors/sequencer/strips/types/effects/transform.html"),
    ("bpy.types.WipeSequence.*",           "editors/sequencer/strips/types/effects/wipe.html"),
    # --- Modifiers ---
    ("bpy.types.BrightContrastModifier.*", "editors/sequencer/strips/properties/modifiers.html"),
    ("bpy.types.ColorBalanceModifier.*",   "editors/sequencer/strips/properties/modifiers.html"),
    ("bpy.types.CurvesModifier.*",         "editors/sequencer/strips/properties/modifiers.html"),
    ("bpy.types.HueCorrectModifier.*",     "editors/sequencer/strips/properties/modifiers.html"),
    ("bpy.types.WhiteBalanceModifier.*",   "editors/sequencer/strips/properties/modifiers.html"),
    # ("bpy.types.SequenceColorBalanceData.*", ""),
    # ("py.types.SequenceCrop.*",              ""),
    # ("bpy.types.SequenceEditor.*",           ""),
    # ("bpy.types.SequenceElement.*",          ""),
    ("bpy.types.SequenceModifier.*",           "editors/sequencer/strips/properties/modifiers.html"),
    ("bpy.types.SequenceProxy.*",              "editors/sequencer/strips/properties/proxy_timecode.html"),
    # ("bpy.types.SequenceTransform.*",        ""),
    ("bpy.types.Sequence.*",                   "editors/sequencer"),  # catch anything else

    # *** Physics ***
    # --- Force Field ---
    ("bpy.types.FieldSettings.*",              "physics/force_fields"),
    # --- Colision ---
    ("bpy.types.CollisionSettings.*",          "physics/collision.html"),
    # --- Cloth ---
    ("bpy.types.ClothCollisionSettings.*",     "physics/cloth/settings/collisions.html"),
    ("bpy.types.ClothSettings.*",              "physics/cloth/settings"),
    # ("bpy.types.ClothSolverResult.*",        ""), TODO
    # --- Dynamic Paint ---
    ("bpy.types.DynamicPaintBrushSettings.*",         "physics/dynamic_paint/brush.html"),
    ("bpy.types.DynamicPaintCanvasSettings.*",        "physics/dynamic_paint/canvas.html"),
    # ("bpy.types.DynamicPaintSurface.*",             ""),  # TODO
    # ("bpy.types.DynamicPaintSurfaces.*",            ""),  # TODO
    # --- Soft Body ---
    ("bpy.types.SoftBodySettings.*",           "physics/soft_body/settings.html"),
    # --- Fluid ---
    ("bpy.types.FluidFluidSettings.*",         "physics/fluid/types/fluid_object.html"),
    ("bpy.types.FluidMeshVertex.*",            "physics/fluid"),  # TODO - refine
    ("bpy.types.FluidSettings.*",              "physics/fluid"),  # TODO - refine
    ("bpy.types.ControlFluidSettings.*",       "physics/fluid/types/control.html"),
    ("bpy.types.DomainFluidSettings.*",        "physics/fluid/types/domain.html"),
    ("bpy.types.InflowFluidSettings.*",        "physics/fluid/types/flow.html#inflow"),
    ("bpy.types.ObstacleFluidSettings.*",      "physics/fluid/types/obstacle.html"),
    ("bpy.types.OutflowFluidSettings.*",       "physics/fluid/types/flow.html#outflow"),
    ("bpy.types.SPHFluidSettings.*",           "physics/fluid"),  # TODO - refine
    # --- Smoke ---
    ("bpy.types.SmokeCollSettings.*",          "physics/smoke/types/collisions.html"),
    ("bpy.types.SmokeDomainSettings.*",        "physics/smoke/types/domain.html"),
    ("bpy.types.SmokeFlowSettings.*",          "physics/smoke/types/flow_object.html"),
    # --- Rigid Body ---
    ("bpy.types.RigidBodyConstraint.*",        "physics/rigid_body/constraints"),
    ("bpy.types.RigidBodyObject.*",            "physics/rigid_body"),
    ("bpy.types.RigidBodyWorld.*",             "physics/rigid_body/world.html"),
    # --- Particles ---
    ("bpy.types.Particle.*",                      "physics/particles"),
    ("bpy.types.ParticleBrush.*",                 "physics/particles/mode.html"),  # TODO - refine
    ("bpy.types.ParticleDupliWeight.*",           "physics/particles/properties/vertexgroups.html"),
    ("bpy.types.ParticleEdit.*",                  "physics/particles/mode.html"),
    ("bpy.types.ParticleFluidSettings.*",         "physics/particles/properties/physics/fluid.html"),
    ("bpy.types.ParticleHairKey.*",               "physics/particles/properties/physics/keyed.html"),
    ("bpy.types.ParticleKey.*",                   "physics/particles/properties/physics/keyed.html"),
    ("bpy.types.ParticleSettings.*",              "physics/particles"),
    # ("bpy.types.ParticleSettingsTextureSlot.*", ""),  # TODO - manual has no place for this! XXX
    ("bpy.types.ParticleSystem.*",                "physics/particles"),  # TODO
    ("bpy.types.ParticleSystems.*",               "physics/particles"),  # TODO
    ("bpy.types.ParticleTarget.*",                "physics/particles"),  # TODO

    ("bpy.types.PointCache*",                 "physics/baking.html"),
    ("bpy.types.Boid*",                       "physics/particles/properties/physics/boids.html"),

    # *** ID Subclasses ***
    ("bpy.types.Action.*",        "animation/actions.html"),
    ("bpy.types.Curve.*",         "modeling/curves"),
    ("bpy.types.GreasePencil.*",  "interface/grease_pencil"),
    ("bpy.types.Group.*",         "editors/3dview/object/properties/relations/groups.html"),
    ("bpy.types.Image.*",         "render/blender_render/textures/types/image"),
    ("bpy.types.ShapeKey.*",      "animation/shape_keys.html"),  # not an id but include because of key
    ("bpy.types.Key.*",           "animation/shape_keys.html"),
    ("bpy.types.Lattice.*",       "rigging/lattice.html"),
    ("bpy.types.Library.*",       "data_system/linked_libraries.html"),
    ("bpy.types.Mask.*",          "editors/movie_clip_editor/masking.html"),
    ("bpy.types.Brush.*",         "sculpt_paint/introduction.html#brush"),
    ("bpy.types.Mesh.*",          "modeling/meshes"),    # Catchall, todo - refine
    ("bpy.types.MetaBall.*",      "modeling/metas"),     # Catchall, todo - refine
    ("bpy.types.Nodes.*",         "editors/node_editor/nodes"),
    ("bpy.types.TextCurve.*",     "modeling/texts"),     # Catchall, todo - refine
    ("bpy.types.TextBox.*",       "modeling/texts/editing.html#text-boxes"),
    ("bpy.types.Armature.*",      "rigging/armatures"),  # Catchall, todo - refine
    ("bpy.types.Camera.*",        "render/blender_render/camera"),          # Catchall, todo - refine
    ("bpy.types.PointLamp.*",     "render/blender_render/lighting/lamps/point.html"),  # Catchall, todo - refine
    ("bpy.types.AreaLamp.*",      "render/blender_render/lighting/lamps/area"),   # Catchall, todo - refine
    ("bpy.types.SpotLamp.*",      "render/blender_render/lighting/lamps/spot"),   # Catchall, todo - refine
    ("bpy.types.SunLamp.*",       "render/blender_render/lighting/lamps/sun"),    # Catchall, todo - refine
    ("bpy.types.HemiLamp.*",      "render/blender_render/lighting/lamps/hemi.html"),  # Catchall, todo - refine
    ("bpy.types.Lamp.*",          "render/blender_render/lighting"),              # Catchall, todo - refine

    # *** Blend Data ***
    ("bpy.types.ID.*",                          "data_system/data_blocks.html"),
    ("bpy.types.BlendData*",                    "data_system/data_blocks.html#data-block-types"),

    ("bpy.types.bpy_struct*",                  "data_system/custom_properties.html"),

    # *** Animation ***
    ("bpy.types.Keyframe.*",                       "animation/actions.html"),
    ("bpy.types.FCurve.*",                         "editors/graph_editor/fcurves"),
    ("bpy.types.FCurveModifiers.*",                "editors/graph_editor/fcurves/fmodifiers.html"),
    # ("bpy.types.FCurveSample.*",                 ""), Todo
    ("bpy.types.FModifier.*",                      "editors/graph_editor/fcurves/fmodifiers.html"),
    ("bpy.types.FModifierCycles.*",                "editors/graph_editor/fcurves/fmodifiers.html#cycles"),
    ("bpy.types.FModifierEnvelope.*",              "editors/graph_editor/fcurves/fmodifiers.html#envelope"),
    ("bpy.types.FModifierEnvelopeControlPoint.*",  "editors/graph_editor/fcurves/fmodifiers.html#envelope"),
    ("bpy.types.FModifierFunctionGenerator.*",     "editors/graph_editor/fcurves/fmodifiers.html#generator"),
    ("bpy.types.FModifierGenerator.*",             "editors/graph_editor/fcurves/fmodifiers.html#generator"),
    # ("bpy.types.FModifierLimits.*",              ""), Todo
    ("bpy.types.FModifierNoise.*",                 "editors/graph_editor/fcurves/fmodifiers.html#noise"),
    ("bpy.types.FModifierStepped.*",               "editors/graph_editor/fcurves/fmodifiers.html#stepped"),
    ("bpy.types.TimelineMarker.*",                 "animation/markers.html"),
    ("bpy.types.AnimViz.*",                        "animation/keyframes/visualization.html"),
    ("bpy.types.AnimVizMotionPaths.*",             "animation/keyframes/visualization.html#motion-paths"),
    ("bpy.types.AnimVizOnionSkinning.*",           "animation/keyframes/visualization.html"),
    ("bpy.types.NlaStrip.*",                       "editors/nla.html#strips"),
    ("bpy.types.NlaTrack.*",                       "editors/nla.html#tracks"),
    ("bpy.types.NlaTracks.*",                      "editors/nla.html#tracks"),
    ("bpy.types.DopeSheet.*",                      "editors/dope_sheet"),
    ("bpy.types.Driver.*",                         "animation/drivers.html"),
    ("bpy.types.DriverTarget.*",                   "animation/drivers.html"),
    ("bpy.types.DriverVariable.*",                 "animation/drivers.html"),

    # --- Rigging ---
    ("bpy.types.Bone.*",                "rigging/armatures/bones"),
    ("bpy.types.EditBone.*",            "rigging/armatures/editing"),
    ("bpy.types.PoseBone.*",            "rigging/posing"),
    ("bpy.types.ArmatureBones.*",       "rigging/armatures/bones"),
    ("bpy.types.ArmatureEditBones.*",   "rigging/armatures/editing"),
    ("bpy.types.Pose.*",                "rigging/posing"),
    ("bpy.types.PoseBoneConstraints.*", "rigging/posing/constraints.html"),

    # --- World ---
    ("bpy.types.World.*",               "render/blender_render/world"),
    ("bpy.types.WorldMistSettings.*",   "render/blender_render/world/mist.html"),
    ("bpy.types.WorldTextureSlot.*",    "render/blender_render/world/world_panel.html#textures"),

    ("bpy.types.Texture.*",             "render/blender_render/textures"),

    # *** Game Engine ***
    ("bpy.types.LodLevel.*",                "game_engine/performance/level_of_detail.html"),
    # --- Logic ---
    # Sensors
    ("bpy.types.ActuatorSensor.*",          "game_engine/logic/sensors/types/actuator.html"),
    # ("bpy.types.ArmatureSensor.*",        ""), Not in Blender
    ("bpy.types.NearSensor.*",              "game_engine/logic/sensors/types/near.html"),
    ("bpy.types.RaySensor.*",               "game_engine/logic/sensors/types/ray.html"),
    ("bpy.types.Sensor.*",                  "game_engine/logic/sensors"),
    # ("bpy.types.ArmatureSensor.*",        ""), Not in Blender
    ("bpy.types.CollisionSensor.*",         "game_engine/logic/sensors/types/collision.html"),
    ("bpy.types.DelaySensor.*",             "game_engine/logic/sensors/types/delay.html"),
    ("bpy.types.JoystickSensor.*",          "game_engine/logic/sensors/types/joystick.html"),
    ("bpy.types.KeyboardSensor.*",          "game_engine/logic/sensors/types/keyboard.html"),
    ("bpy.types.MessageSensor.*",           "game_engine/logic/sensors/types/message.html"),
    ("bpy.types.MouseSensor.*",             "game_engine/logic/sensors/types/mouse.html"),
    ("bpy.types.PropertySensor.*",          "game_engine/logic/sensors/types/property.html"),
    ("bpy.types.RadarSensor.*",             "game_engine/logic/sensors/types/radar.html"),
    ("bpy.types.RandomSensor.*",            "game_engine/logic/sensors/types/random.html"),
    # Actuators
    ("bpy.types.ActionActuator.*",         "game_engine/logic/actuators/types/action.html"),
    ("bpy.types.Actuator.*",               "game_engine/logic/actuators"),
    # ("bpy.types.ArmatureActuator.*",     ""), Not in Blender
    ("bpy.types.CameraActuator.*",         "game_engine/logic/actuators/types/camera.html"),
    ("bpy.types.ConstraintActuator.*",     "game_engine/logic/actuators/types/constraint.html"),
    ("bpy.types.EditObjectActuator.*",     "game_engine/logic/actuators/types/edit_object.html"),
    ("bpy.types.Filter2DActuator.*",       "game_engine/logic/actuators/types/2d_filters.html"),
    ("bpy.types.GameActuator.*",           "game_engine/logic/actuators/types/game.html"),
    ("bpy.types.MessageActuator.*",        "game_engine/logic/actuators/types/message.html"),
    ("bpy.types.MouseActuator.*",          "game_engine/logic/actuators/types/mouse.html"),
    # ("bpy.types.ObjectActuator.*",       ""), Not in Blender
    ("bpy.types.ParentActuator.*",         "game_engine/logic/actuators/types/property.html"),
    ("bpy.types.PropertyActuator.*",       "game_engine/logic/actuators/types/property.html"),
    ("bpy.types.RandomActuator.*",         "game_engine/logic/actuators/types/random.html"),
    ("bpy.types.SceneActuator.*",          "game_engine/logic/actuators/types/scene.html"),
    ("bpy.types.SoundActuator.*",          "game_engine/logic/actuators/types/sound.html"),
    ("bpy.types.StateActuator.*",          "game_engine/logic/actuators/types/state.html"),
    ("bpy.types.SteeringActuator.*",       "game_engine/logic/actuators/types/steering.html"),
    ("bpy.types.VisibilityActuator.*",     "game_engine/logic/actuators/types/visibility.html"),
    # Controllers
    ("bpy.types.Controller.*",             "game_engine/logic/controllers"),
    ("bpy.types.ExpressionController.*",   "game_engine/logic/controllers/types/expression.html"),
    ("bpy.types.PythonController.*",       "game_engine/logic/controllers/types/python.html"),

    ("bpy.types.*",                        "contents.html"),  # Catchall

    # === Operators ===
    # Catch all only for now!
    # *** Window/Screen ***

    ("bpy.ops.action.*",                  "animation/actions.html"),
    ("bpy.ops.anim.*",                    "animation"),
    ("bpy.ops.armature.*",                "rigging/armatures"),
    ("bpy.ops.boid.*",                    "physics/particles/properties/physics/boids.html"),
    ("bpy.ops.brush.*",                   "sculpt_paint/introduction.html#brush"),  # TODO doc
    ("bpy.ops.buttons.*",                 "interface/controls/buttons"),
    ("bpy.ops.camera.*",                  "erender/blender_render/camera"),
    ("bpy.ops.clip.*",                    "editors/movie_clip_editor/index.html#movie-clip-editor"),
    ("bpy.ops.cloth.*",                   "physics/cloth"),
    ("bpy.ops.console.*",                 "editors/python_console.html"),
    ("bpy.ops.constraint.*",              "rigging/constraints"),
    ("bpy.ops.curve.*",                   "modeling/curves"),
    ("bpy.ops.cycles.*",                  "render/cycles"),
    ("bpy.ops.dpaint.*",                  "physics/dynamic_paint"),
    ("bpy.ops.ed.undo",                   "interface/undo_and_redo.html#undo"),
    ("bpy.ops.ed.redo",                   "interface/undo_and_redo.html#redo"),
    ("bpy.ops.ed.undo_history",           "interface/undo_and_redo.html#undo-history"),
    ("bpy.ops.ed.*",                      "interface/undo_and_redo.html"), # Catchall
    ("bpy.ops.screen.repeat_last",        "interface/undo_and_redo.html#repeat-last"),
    ("bpy.ops.screen.repeat_history",     "interface/undo_and_redo.html#repeat-history"),
    ("bpy.ops.export_anim.*",             "data_system/files/import_export.html"),
    ("bpy.ops.export_mesh.*",             "data_system/files/import_export.html"),
    ("bpy.ops.export_scene.*",            "data_system/files/import_export.html"),
    ("bpy.ops.file.*",                    "editors/file_browser/introduction.html"),
    ("bpy.ops.fluid.*",                   "physics/fluid"),
    ("bpy.ops.font.*",                    "modeling/texts"),
    ("bpy.ops.gpencil.*",                 "interface/grease_pencil"),
    ("bpy.ops.graph.*",                   "editors/graph_editor/fcurves"),
    ("bpy.ops.group.*",                   "editors/3dview/object/properties/relations/groups.html"),
    ("bpy.ops.image.*",                   "render/blender_render/textures/types/image"),
    ("bpy.ops.import*",                   "data_system/files/import_export.html"),
    # ("bpy.ops.info.*",                  ""),  # TODO
    ("bpy.ops.lamp.*",                    "render/blender_render/lighting"),  # TODO
    ("bpy.ops.lattice.*",                 "rigging/lattice.html"),
    ("bpy.ops.logic.*",                   "game_engine/logic"),
    ("bpy.ops.marker.*",                  "animation/markers.html"),
    ("bpy.ops.mask.*",                    "editors/movie_clip_editor/masking.html"),
    ("bpy.ops.material.new",              "render/blender_render/materials/assigning_a_material.html#creating-a-new-material"),
    ("bpy.ops.material.*",                "render/blender_render"),
    ("bpy.ops.mesh.vertices_smooth",      "modeling/meshes/editing/deforming/smooth.html"),
    ("bpy.ops.view3d.ruler*",             "interface/ruler_and_protractor.html"),
    ("bpy.ops.view3d.edit_mesh_extrude*", "modeling/meshes/editing/duplicating/extrude.html"),
    ("bpy.ops.mesh.subdivide",            "modeling/meshes/editing/subdividing/subdivide.html"),
    ("bpy.ops.mesh.loopcut_slide",        "modeling/meshes/editing/subdividing/loop_subdivide.html"),
    ("bpy.ops.mesh.bridge-edge-loops",    "modeling/meshes/editing/edges.html#bridge-edge-loops"),
    ("bpy.ops.mesh.duplicate_move",       "modeling/meshes/editing/duplicating/duplicate.html"),
    ("bpy.ops.mesh.spin",                 "modeling/meshes/editing/duplicating/spin.html"),
    ("bpy.ops.mesh.screw",                "modeling/meshes/editing/duplicating/screw.html"),
    ("bpy.ops.mesh.knife*",               "modeling/meshes/editing/subdividing/knife_subdivide.html"),
    ("bpy.ops.mesh.bisect",               "modeling/meshes/editing/subdividing/bisect.html"),
    ("bpy.ops.mball.*",                   "modeling/metas"),
    ("bpy.ops.mesh.*",                    "modeling/meshes"),
    ("bpy.ops.nla.*",                     "editors/nla.html"),
    ("bpy.ops.node.*",                    "editors/node_editor/nodes"),
    ("bpy.ops.object.*shape_key*",        "animation/shape_keys.html"),
    ("bpy.ops.object.join_shapes",        "animation/shape_keys.html"),
    ("bpy.ops.outliner.*",                "editors/outliner.html"),
    # ("bpy.ops.paint.*",                 ""),  # TODO
    ("bpy.ops.particle.*",                "physics/particles"),
    ("bpy.ops.pose.*",                    "rigging/posing"),
    ("bpy.ops.poselib.*",                 "rigging/posing/pose_library.html"),
    ("bpy.ops.ptcache.*",                 "physics/baking.html"),

    ("bpy.ops.render.play-rendered-anim", "render/output/animation_player.html"),
    ("bpy.ops.render.*",                  "render"),  # Catchall
    ("bpy.ops.rigidbody.world*",          "physics/rigid_body/world.html"),
    ("bpy.ops.rigidbody.*",               "physics/rigid_body"),
    ("bpy.ops.safe_areas.*",              "render/blender_render/camera/object_data.html#safe-areas"),
    ("bpy.ops.scene.*",                   "data_system/scenes"),
    ("bpy.ops.screen.*",                  "interface/window_system/screens.html"),
    ("bpy.ops.script.*",                  "advanced/scripting"),
    ("bpy.ops.sculpt.*",                  "sculpt_paint/sculpting"),
    ("bpy.ops.sequencer.*",               "editors/sequencer"),
    # ("bpy.ops.sketch.*",                ""),  # TODO
    ("bpy.ops.sound.bake_animation",      "data_system/scenes/properties.html#audio"),
    ("bpy.ops.sound.*",                   "render/audio/speaker.html"),
    ("bpy.ops.surface.*",                 "modeling/surfaces"),
    ("bpy.ops.text.*",                    "editors/text_editor.html"),
    ("bpy.ops.texture.*",                 "render/blender_render/textures"),
    ("bpy.ops.time.*",                    "editors/timeline.html"),
    ("bpy.ops.transform.edge_slide",      "modeling/meshes/editing/edges.html#edge-slide"),
    ("bpy.ops.transform.vert_slide",      "modeling/meshes/editing/vertices.html#vertex-slide"),
    ("bpy.ops.transform.shrink_fatten",   "modeling/meshes/editing/deforming/shrink-fatten.html"),
    ("bpy.ops.transform.push_pull",       "modeling/meshes/editing/deforming/push_pull.html"),
    ("bpy.ops.transform.translate",       "editors/3dview/object/transform/basics/grab.html"),
    ("bpy.ops.transform.rotate",          "editors/3dview/object/transform/basics/rotate.html"),
    ("bpy.ops.transform.resize",          "editors/3dview/object/transform/basics/scale.html"),
    ("bpy.ops.transform.mirror",          "editors/3dview/object/transform/mirror.html"),
    ("bpy.ops.transform.*",               "editors/3dview/object/transform"),  # Catchall
    ("bpy.ops.object.duplicate_move",     "editors/3dview/object/transform/duplication.html"),
    ("bpy.ops.object.duplicate_move_linked",   "editors/3dview/object/transform/duplication.html#linked-duplicates"),
    ("bpy.ops.object.delete",             "modeling/meshes/editing/basics/deleting.html#delete"),
    ("bpy.ops.object.join",               "modeling/meshes/editing/misc.html#join"),
    ("bpy.ops.object.origin_set",         "editors/3dview/object/transform/origns.html#moving-object-centers"),
    ("bpy.ops.object.shade_smooth",       "modeling/meshes/editing/smoothing.html#smooth-shading"),
    ("bpy.ops.object.shade_flat",         "modeling/meshes/editing/smoothing.html#mesh-shading"),
    ("bpy.ops.object.data_transfer",      "modeling/meshes/editing/data_transfer.html#data"),
    ("bpy.ops.object.datalayout_transfer", "modeling/meshes/editing/data_transfer.html#data-layout"),
    ("bpy.ops.object.group*",             "editors/3dview/object/properties/relations/groups.html"),
    ("bpy.ops.object.*",                  "editors/3dview/object/transform"), # Catchall
    ("bpy.ops.ui.*",                      "interface"),
    ("bpy.ops.uv.*",                      "editors/uv_image"),
    # ("bpy.ops.view2d.*",  ""),          #  TODO
    ("bpy.ops.view3d.*",                  "editors/3dview"),  # Catchall
    ("bpy.ops.view3d.background_image_add", "editors/3dview/display/background_images.html"),
    ("bpy.ops.wm.properties*",            "data_system/custom_properties.html"),
    ("bpy.ops.wm.addon_*",                "preferences/addons.html"),
    ("bpy.ops.wm.*",                      "interface/index.html#window-system"),
    ("bpy.ops.world.*",                   "render/blender_render/world"),
    ("bpy.ops.*",                         "contents.html"),  # CATCHALL!

)

# may have 'url_reference_mapping'... etc later
