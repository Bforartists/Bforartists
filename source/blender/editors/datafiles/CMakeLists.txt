# SPDX-FileCopyrightText: 2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# BFA - this document is heavily modified, so best compare Blender new with Blender old (a week back or so)
# BFA - then when you see any changes, splice them in. Bforartists icon list is completely different. 

set(INC
  PUBLIC ${CMAKE_CURRENT_BINARY_DIR}
  ../include
)

set(INC_SYS

)

# Part of the `blender` binary (sources for data-files are appended).
set(SRC

)

set(LIB
  PRIVATE bf::blenlib
)

# This section is maintained by the updating script, keep BEGIN/END comments.
# See: `make icons_geom` and the script `./release/datafiles/blender_icons_geom_update.py`.
set_property(GLOBAL PROPERTY ICON_GEOM_NAMES
  # BEGIN ICON_GEOM_NAMES
  brush.gpencil_draw.erase
  brush.gpencil_draw.fill
  brush.particle.add
  brush.particle.comb
  brush.particle.cut
  brush.particle.length
  brush.particle.puff
  brush.particle.smooth
  brush.particle.weight
  brush.sculpt.paint
  brush.uv_sculpt.grab
  brush.uv_sculpt.pinch
  brush.uv_sculpt.relax
  none
  ops.armature.bone.roll
  ops.armature.extrude_cursor
  ops.armature.extrude_move
  ops.curve.draw
  ops.curve.extrude_cursor
  ops.curve.extrude_move
  ops.curve.pen
  ops.curve.radius
  ops.curve.vertex_random
  ops.generic.cursor
  ops.generic.select
  ops.generic.select_box
  ops.generic.select_circle
  ops.generic.select_lasso
  ops.generic.select_paint
  ops.gpencil.draw
  ops.gpencil.draw.eraser
  ops.gpencil.draw.line
  ops.gpencil.draw.poly
  ops.gpencil.edit_bend
  ops.gpencil.edit_mirror
  ops.gpencil.edit_shear
  ops.gpencil.edit_to_sphere
  ops.gpencil.extrude_move
  ops.gpencil.primitive_arc
  ops.gpencil.primitive_box
  ops.gpencil.primitive_circle
  ops.gpencil.primitive_curve
  ops.gpencil.primitive_line
  ops.gpencil.primitive_polyline
  ops.gpencil.radius
  ops.gpencil.stroke_cutter
  ops.gpencil.transform_fill
  ops.mesh.bevel
  ops.mesh.bisect
  ops.mesh.dupli_extrude_cursor
  ops.mesh.extrude_faces_move
  ops.mesh.extrude_manifold
  ops.mesh.extrude_region_move
  ops.mesh.extrude_region_shrink_fatten
  ops.mesh.inset
  ops.mesh.knife_tool
  ops.mesh.loopcut_slide
  ops.mesh.offset_edge_loops_slide
  ops.mesh.polybuild_hover
  ops.mesh.primitive_cone_add_gizmo
  ops.mesh.primitive_cube_add_gizmo
  ops.mesh.primitive_cylinder_add_gizmo
  ops.mesh.primitive_grid_add_gizmo
  ops.mesh.primitive_sphere_add_gizmo
  ops.mesh.primitive_torus_add_gizmo
  ops.mesh.rip
  ops.mesh.rip_edge
  ops.mesh.spin
  ops.mesh.spin.duplicate
  ops.mesh.vertices_smooth
  ops.node.links_cut
  ops.paint.eyedropper_add
  ops.paint.vertex_color_fill
  ops.paint.weight_fill
  ops.paint.weight_gradient
  ops.paint.weight_sample
  ops.paint.weight_sample_group
  ops.pose.breakdowner
  ops.pose.push
  ops.pose.relax
  ops.sculpt.border_face_set
  ops.sculpt.border_hide
  ops.sculpt.border_mask
  ops.sculpt.box_trim
  ops.sculpt.cloth_filter
  ops.sculpt.color_filter
  ops.sculpt.face_set_edit
  ops.sculpt.lasso_face_set
  ops.sculpt.lasso_hide
  ops.sculpt.lasso_mask
  ops.sculpt.lasso_trim
  ops.sculpt.line_face_set
  ops.sculpt.line_hide
  ops.sculpt.line_mask
  ops.sculpt.line_project
  ops.sculpt.line_trim
  ops.sculpt.mask_by_color
  ops.sculpt.mesh_filter
  ops.sculpt.polyline_face_set
  ops.sculpt.polyline_hide
  ops.sculpt.polyline_mask
  ops.sculpt.polyline_trim
  ops.sequencer.blade
  ops.sequencer.retime
  ops.transform.bone_envelope
  ops.transform.bone_size
  ops.transform.edge_slide
  ops.transform.push_pull
  ops.transform.resize.cage
  ops.transform.resize
  ops.transform.rotate
  ops.transform.shear
  ops.transform.shrink_fatten
  ops.transform.tilt
  ops.transform.tosphere
  ops.transform.transform
  ops.transform.translate
  ops.transform.vert_slide
  ops.transform.vertex_random
  ops.view3d.ruler
  # END ICON_GEOM_NAMES
)

data_to_c_simple(../../../../release/datafiles/bfont.pfb SRC)


if(WITH_BLENDER)
  # Blender only (not Cycles stand-alone).

  if(NOT WITH_HEADLESS)
    # Blender UI only.

    set(SVG_FILENAMES_NOEXT
      # ------------------------- row 1 --------------------------*/

      none

      question
      error
      cancel
      tria_right
      tria_down
      tria_left
      tria_up
      arrow_leftright
      plus

      disclosure_tri_right
      disclosure_tri_down
      radiobut_off
      radiobut_on
      menu_panel
      blender
      grip
      dot
      collapsemenu
      x

      template
      lastoperator
      alternated
      ui
      node
      node_sel
      blend_tex
      cloud_tex
      distorted_noise_tex
      assign

      connected
      prefix
      suffix
      flip
      string
      set_roll
      clear_roll
      roll_x_neg
      roll_x_pos
      roll_x_tang_neg

      marker_to_mesh
      origin
      floor
      wall
      setup
      background
      select_root
      select_tip
      image_aspect
      brushsize

      point_scale
      point_translate
      attribute_proximity
      attribute_texture
      collection_info
      point_to_volume
      volume_to_mesh
      planar
      attribute_combine_xyz
      attribute_separate_xyz

      line_trim
      internet_offline
      polyline_hide
      polyline_show
      frame_preview_range
      frame_scene_range
      named_layer_selection
      tag


      fullscreen
      splitscreen
      rightarrow_thin
      bordermove
      viewzoom
      zoomin
      zoomout
      panel_close
      copy_id
      eyedropper

      link_area
      auto
      checkbox_dehlt
      checkbox_hlt
      unlocked
      locked
      unpinned
      pinned
      screen_back
      rightarrow

      downarrow_hlt
      spot_blend
      lens_scale
      make_internal
      normal_setstrength
      plugin
      magic_tex
      marble_tex
	    musgrave_tex
      view_graph_all
      noise_tex

      roll_x_tang_pos
      roll_y_neg
      roll_y_pos
      roll_z_neg
      roll_z_pos
      roll_z_tang_neg
      roll_z_tang_pos
      clear_constraint
      add_ik
      clear_ik

      floodfill
      optimize
      propagate
      brushstrength
      interpolate
      reproject
      brushangle
      vertcolfromweight
      huecorrect
      particlebrush_none

      groundgrid
      nodetree_active
      node_compositing_active
      texture_active
      spreadsheet
      shader_active
      attribute_remove
      node_vectorrotate
      mask_slice
      mesh_line

      instance_transform_get

      help
      ghost_enabled
      color # see color_red/green/blue */
      linked
      unlinked
      hand
      zoom_all
      zoom_selected
      zoom_previous
      zoom_in

      zoom_out
      render_region
      border_rect
      border_lasso
      freeze
      stylus_pressure
      ghost_disabled
      new
      file_tick
      quit

      url
      recover_last
      duplicate
      fullscreen_enter
      fullscreen_exit
      blank1  # BFA - not actually blank - this is used all over the place
      load_gltf
      save_gltf
      stucci_tex
      voroni_tex

      clear
      reset
      flip_x
      flip_y
      flip_z
      zoom_set
      view_fit
      gp_select_between_strokes
      inversesquarecurve
      prop_projected

      particlebrush_add
      particlebrush_comb
      particlebrush_puff
      particlebrush_smooth
      particlebrush_weight
      particlebrush_length
      mod_mesh_cache
      add
      file_3d
      align_center

      lineart_collection
      lineart_scene
      lineart_object
      exposure
      attribute_convert
      groupinput
      groupoutput
      save_svg
      save_pdf
      load_svg_gpencil

      viewport_transform

      sharpen
      material
      texture
      normal_multiply
      world
      scene
      edit
      game
      radio
      script

      particles
      physics
      speaker
      texture_shaded
      view_front
      view_back
      view_left
      view_right
      view_top
      view_bottom

      view_reset
      view_switchtocam
      view_switchactivecam
      delete
      persp_ortho
      wireframe
      wood_tex
      renderborder_clear
      renderborder
      clippingborder

      edit_external
      save_all
      stitch
      marker_bind
      split_horizontal
      split_vertical
      view_frame
      after_current_frame
      before_current_frame
      between_markers

      align_flush
      align_justify
      align_left
      align_middle
      align_right
      align_bottom
      align_top
      decorate
      decorate_animate
      decorate_driver

      attribute_clamp
      attribute_maprange
      lock_to_camview_on
      action_tweak_solo
      transfer_sculpt
      switch
      attribute_curvemap
      attribute_transfer
      curve_resample
      attribute_vector_rotate

      view3d
      ipo
      oops
      buts
      dissolve_between
      dissolve_unselected
      info
      sequence
      text
      imasel

      sound
      action
      nla
      scriptwin
      time
      nodetree
      geometry_set
      rename
      console
      preferences
      clip

      asset_manager
      toolbar
      circle_select
      inverse
      select_all
      select_none
      apptemplate
      maximize_area
      new_window
      quadview

      column_current_frame
      columns_keys
      columns_markers
      expandmenu
      bake_curve
      bake_sound
      clean_channels
      clean_keys
      discontinue_euler
      jump_to_keyframes

      decorate_keyframe
      orientation_cursor
      decorate_override
      decorate_unlocked
      decorate_locked
      face_maps
      documents
      file_new
      filebrowser
      smooth_laplacian

      node_volumeprincipled
      vector_displace
      lock_rotation
      material_add
      material_replace
      merge_center
      merge_cursor
      split_byvertices
      separate_bymaterial
      separate_loose


      object_datamode
      editmode_hlt
      facesel_hlt
      vpaint_hlt
      tpaint_hlt
      wpaint_hlt
      sculptmode_hlt
      pose_hlt
      particlemode
      knife

      selectless
      selectmore
      bend
      shear
      tosphere
      joincopy
      splitedge
      vertexconnectpath
      vertexconnect
      marksharpedges

      buts_active
      oops_active
      nla_active
      dopesheet_active
      graph_active
      offset_edge_slide
      viewall
      viewall_resetcursor
      view_global_local
      view_selected

      sample_keyframes
      smooth_keyframes
      flatten_handler
      snap_currentframe
      snap_cursorvalue
      snap_nearestframe
      snap_nearestmarker
      snap_nearestsecond
      mirror_cursorvalue
      mirror_marker

      graph
      loop_cut_and_slide
      hide_on
      hide_off
      image
      keyframe_hlt
      keyframe
      library_data_override
      light
      light_area

      shading_edge_sharp
      shading_edge_smooth
      shading_vert_sharp
      shading_vert_smooth
      clearsharpverts
      marksharpverts
      rotateccw
      projectfromview_bounds
      area_dock
      area_join_down
      area_join_left
      area_join_up
      join_areas
      swap_areas

      scene_data
      renderlayers
      file_blank
      object_data
      mesh_data
      curve_data
      meta_data
      lattice_data
      apply_rotscale
      material_data

      outliner_data_camera
      anim_data
      camera_data
      particle_data
      library_data_direct
      group
      armature_data
      pose_data
      bone_data
      constraint

      shapekey_data
      constraint_bone
      camera_stereo
      package
      uglypackage
      solidify
      viewcameracenter
      view_active_back
      view_active_bottom
      view_active_front

      mirror_time
      handle_autoclamped
      move_down
      move_to_bottom
      move_to_top
      move_up
      extrapolation_constant
      extrapolation_cyclic
      extrapolation_cyclic_clear
      extrapolation_linear

      light_data
      light_hemi
      light_point
      light_spot
      light_sun
      lightprobe_sphere
      lightprobe_plane
      lightprobe_volume
      view_remove_local
      shape

      mask_slice_fill
      mask_slice_new
      simplify_sample
      simplify_adaptive
      toggle_close
      separate_gp_strokes
      separate_gp_points
      separate_gp_layer
      bone_layer
      clean_channels_frames

      brush_data
      image_data
      file
      fcurve
      font_data
      render_result
      surface_data
      empty_data
      settings
      render_animation

      render_still
      library_data_broken
      boids
      gizmo
      library_data_indirect
      greasepencil
      line_data
      hide_renderview
      group_bone
      group_vertex

      group_vcol
      group_uvs
      render_still_view
      render_ani_view
      rna
      outliner_data_lightprobe
      view_active_left
      view_active_right
      view_active_top
      centertomouse

      builtin_modifier
      cycles_modifier
      envelope_modifier
      generator_modifier
      limit_modifier
      noise_modifier
      stepped_modifier
      swap
      sync
      transition

      matcloth
      matfluid
      matshaderball
      node_compositing
      node_corner
      node_material
      node_side
      node_top
      normals_face
      normals_vertex

      mod_armature_selected
      node_transform_clear
      propagate_marker
      propagate_next
      propagate_previous
      propagate_selected
      select_by_material
      pose_from_breakdown
      pose_relax_to_breakdown
      raycast

      clearsharpedges
      convexhull
      blendfromshape
      shapepropagate
      bridge_edgeloops
      clear_fs_edge
      mark_fs_edge
      makedupliface
      rotatecw
      split

      subdivedgeloop
      unsubdivide
      subdiv_edgering
      reverse_colors
      rotate_colors
      reverse_uvs
      rotate_uvs
      alignauto
      alignhorizontal
      alignvertical

      straighten
      straighten_x
      straighten_y
      unwrap_abf
      unwrap_lscm
      weld
      dolly
      fly_navigation
      view_navigation
      walk_navigation

      add_strip
      add_track
      add_track_above
      add_metastrip
      remove_metastrip
      seq_multiply
      add_selected
      center
      hierarchy
      hierarchy_down

      normals_vertex_face
      object_origin
      onionskin_off
      onionskin_on
      orientation_gimbal
      orientation_local
      orientation_normal
      orientation_view
      orphan_data
      outliner

      rename_x
      rename_y
      rename_z
      curve_spiral
      curve_star
      curve_startend
      curve_line
      float_to_int
      curve_quadrilateral
      curve_trim

      outliner_ob_empty
      outliner_ob_mesh
      outliner_ob_curve
      outliner_ob_lattice
      outliner_ob_meta
      options
      outliner_ob_camera
      outliner_ob_armature
      outliner_ob_font
      outliner_ob_surface

      outliner_ob_speaker
      empty_arrows
      empty_circle
      empty_cone
      empty_cube
      empty_image
      temp
      empty_sphere
      restrict_color_off
      restrict_color_on

      restrict_view_on
      restrict_view_off
      restrict_select_on
      restrict_select_off
      restrict_render_on
      restrict_render_off
      outliner_ob_force_field
      outliner_ob_group_instance
      zoom_camera
      zoom_border

      hierarchy_up
      cut_links
      detach_links
      toggle_node_mute
      toggle_node_options
      toggle_node_preview
      statusbar
      topbar
      caret_line_begin
      caret_line_end

      outliner_data_greasepencil
      outliner_data_light
      outliner_ob_greasepencil
      outliner_ob_image
      outliner_ob_light
      outliner_ob_lightprobe
      overlay
      pivot_active
      pivot_boundbox
      pivot_cursor

      gp_caps_flat
      gp_caps_round
      fixed_size
      load_usd
      select_handletype
      spline_type
      curve_fill
      posterize
      mod_dash
      search_menu

      outliner_data_empty
      outliner_data_mesh
      outliner_data_curve
      outliner_data_lattice
      outliner_data_meta
      inc_contrast
      dec_contrast
      outliner_data_armature
      outliner_data_font
      outliner_data_surface

      outliner_data_speaker
      outliner_data_pose
      applyall
      applymove
      applyrotate
      applyscale
      clearmove
      clearorigin
      clearrotate
      clearscale

      makeduplireal
      visualtransform
      pokefaces
      splitbyedges
      triangulate
      tristoquads
      pan_down
      pan_left
      pan_right
      pan_up

      caret_next_char
      caret_next_word
      caret_prev_word
      caret_prev_char
      history_cycle_back
      history_cycle_forward
      indent
      unindent
      autocomplete
      goto

      pivot_individual
      pivot_median
      preset
      properties
      remove
      sculpt_dyntopo
      shaderfx
      shading_bbox
      shading_rendered
      shading_solid

      make_screenshot_area
      new_window_main
      blend_to_neighbour
      special
      string_join
      string_length
      string_substring
      string_to_curve
      value_to_string
      attribute_statistic

      # primitives */
      mesh_plane
      mesh_cube
      mesh_circle
      mesh_uvsphere
      mesh_icosphere
      mesh_grid
      mesh_monkey
      mesh_cylinder
      mesh_torus
      mesh_cone

      mesh_capsule
      intersect
      pivot_to_active_vert
      pivot_to_maskborder
      pivot_to_origin
      pivot_to_surface
      pivot_to_unmasked
      markfsface
      clearfsface
      meta_empty

      meta_plane
      meta_cube
      meta_ball
      meta_ellipsoid
      meta_capsule
      boolean_intersect
      orbit_down
      orbit_left
      orbit_right
      orbit_up

      select_line
      comment
      uncomment
      whitespace_spaces
      whitespace_tabs
      debug
      seq_multicam
      make_screenshot
      seq_alpha_over
      prefetch

      shading_texture
      shading_wire
      sort_desc
      sort_asc
      system
      collection_new
      tool_settings
      tracking
      tracking_backwards
      tracking_backwards_single

      attribute_capture
      curve_fillet
      curve_parameter
      curve_sample
      curve_tangent
      spline_length
      set_position
      geometry_proximity
      position
      index


      # primitives */
      surface_ncurve
      surface_ncircle
      surface_nsurface
      surface_ncylinder
      surface_nsphere
      surface_ntorus
      beautify
      fill
      gridfill
      curve_bezcurve

      curve_bezcircle
      curve_ncurve
      curve_ncircle
      curve_path
      averageislandscale
      copymirrored
      minimizestretch
      packisland
      seamsfromisland
      color_red

      color_green
      color_blue
      tria_right_bar
      tria_down_bar
      tria_left_bar
      tria_up_bar
      orbit_opposite
      roll_left
      roll_right
      layer

      node_add_shader
      disc
      node_alphaconvert
      node_ambient_occlusion
      node_anisotopic
      node_at
      node_attribute
      node_backgroundshader
      node_bilateral_blur
      node_blackbody

      tracking_clear_backwards
      tracking_clear_forwards
      tracking_forwards
      tracking_forwards_single
      tracking_refine_backwards
      tracking_refine_forwards
      underline
      user
      view_camera
      view_ortho

      points_to_vertices
      mesh_to_points
      float_curve
      rotate_euler
      align_euler_to_vector
      curve_handle_positions
      curve_tilt
      is_spline_cyclic
      set_curve_handle_positions
      set_curve_radius

      # empty */
      force_force
      force_wind
      force_vortex
      force_magnetic
      force_harmonic
      force_charge
      force_lennardjones
      force_texture
      force_curve
      force_boid

      force_turbulence
      force_drag
      force_fluidflow
      recalc_normals
      recalc_normals_inside
      flip_normals
      mark_seam
      clear_seam
      home
      push_pose

      relax_pose
      breakdowner_pose
      keyframes_clear
      remove_from_all_groups
      remove_selected_from_active_group
      fillbetween
      parent
      child
      child_recursive
      siblings

      memory
      node_blur
      node_bokeh_blur
      node_bokeh_image
      node_boxmask
      node_brick
      overlap
      node_bump

      node_channel
      folder_redirect
      view_pan
      view_perspective
      view_zoom
      vis_sel_11
      vis_sel_10
      vis_sel_01
      vis_sel_00
      outliner_data_gp_layer
      workspace
      xray

      spline_resolution
      set_spline_resolution
      set_curve_tilt
      separate_geometry
      rotate_instance
      scale_instance
      translate_instance
      material_index
      set_material_index
      set_shade_smooth

      snaptopixel_center
      snaptopixel_corner
      snaptopixel_off
      node_insert_on
      node_insert_off
      rigid_add_active
      rigid_add_passive
      rigid_remove
      rigid_change_shape
      rigid_calculate_mass

      rigid_copy_from_active
      rigid_apply_trans
      rigid_bake_to_keyframe
      rigid_constraints_connect
      keyframes_insert
      keyframes_remove
      motionpaths_calculate
      motionpaths_clear
      bake_action
      toggle_cyclic

      switch_direction
      handle_auto
      handle_vector
      handle_aligned
      handle_free
      radius
      type
      pass
      select_faces_by_side
      checker_deselect

      node_checker
      node_chroma
      node_clouds
      handle_align_single
      node_colorbalance
      node_colorcorrection
      node_colorramp
      node_combinehsv
      node_combinergb
      node_combinexyz

      center_only
      holdout_off
      holdout_on
      community
      cone
      cube
      brushes_all
      driver_distance
      driver_rotational_difference
      driver_transform

      subdivide_mesh
      merge_at_first
      merge_at_last
      motionpaths_update
      motionpaths_update_all
      integer
      input_bool
      instances_to_points
      replace_string
      color_tag

      origin_to_volume
      weight_transfer_weights
      join
      geometry_to_origin
      origin_to_geometry
      origin_to_cursor
      origin_to_centerofmass
      shading_smooth
      shading_flat
      transfer_data

      transfer_data_layout
      new_group
      add_to_active
      mod_smoke
      parent_set
      parent_clear
      link_data
      make_single_user
      make_local
      make_proxy

      erase
      extrudesize
      width_size
      file_cache
      ruler
      vertex_parent
      select_nonmanifold
      select_boundary
      select_edgeloop
      select_edgering

      node_combineycbcra
      node_combineyuva
      lock_to_camview
      node_cornerpin
      node_crop
      node_curve_time
      node_defocus
      node_despeckle
      file_volume
      node_diffuseshader

      empty_axis
      empty_single_arrow
      experimental
      fake_user_off
      fake_user_on
      group_bright
      gp_multiframe_editing
      gp_only_selected
      gp_select_points
      gp_select_strokes

      view_stretch
      view_fill
      get_id
      set_id
      add_all
      delete_all
      duplicate_all
      visual_move
      visual_rotate
      visual_scale

      inset_faces
      make_edgeface
      subdivide_edges
      normal_rotate
      normal_average
      normal_smooth
      normal_target
      knife_project
      bisect
      dissolve_verts

      dissolve_edges
      dissolve_faces
      dissolve_limited
      dissolve_selection
      edge_collapse
      remove_doubles
      weight_normalize_all
      weight_normalize
      weight_mirror
      weight_invert

      weight_clean
      weight_quantize
      weight_levels
      weight_smooth
      weight_limit_total
      weight_fix_deforms
      select_interior
      select_loopinner
      select_loose
      select_sharpedges

      node_direcitonalblur
      value_to_selection
      seq_strip_duplicate
      seq_strip_meta
      node_doubleedgemask
      node_editgroup
      node_ellipsemask
      node_emission
      node_environment
      node_erode

      rigid_body
      image_background
      rigid_body_constraint
      image_reference
      indirect_only_off
      indirect_only_on
      white_balance
      mod_hue_saturation
      outliner_collection
      mod_noise

      loc_rot
      loc_rot_scale
      loc_scale
      rot_scale
      visual_loc_rot
      visual_loc_rot_scale
      visual_loc_scale
      visual_rot_scale
      loc_rot_scale_custom
      separate_copy

      modifier
      mod_wave
      mod_build
      mod_decim
      mod_mirror
      mod_soft
      mod_subsurf
      mod_lineart
      hook
      mod_physics
      mod_particles

      mod_boolean
      mod_edgesplit
      mod_array
      mod_uvproject
      mod_displace
      mod_curve
      mod_lattice
      constraint_data
      mod_armature
      mod_shrinkwrap

      mod_cast
      mod_meshdeform
      mod_bevel
      mod_smooth
      mod_simpledeform
      mod_mask
      select_shortestpath
      select_sideofactive
      select_ungrouped_verts
      angle

      mod_mask_off
      node_fileoutput
      snap_midpoint
      snap_perpendicular
      node_frame
      node_fresnel
      node_gamma
      node_geometry
      node_glare
      node_glasshader

      mod_offset
      mod_opacity
      mod_particle_instance
      mod_simplify
      mod_thickness
      mod_time
      mod_tint
      modifier_off
      modifier_on
      orientation_global

      link_replace
      detach_links_move
      hold_split
      dual_mesh
      domain_size
      edge_neighbors
      edge_vertices
      face_neighbors
      geometry_instance
      vertex_neighbors

      # modifiers */
      mod_cloth
      mod_explode
      mod_fluidsim
      mod_multires
      mod_fluid
      mod_solidify
      mod_screw
      mod_vertex_weight
      mod_dynamicpaint
      mod_remesh

      mod_ocean
      mod_warp
      mod_skin
      mod_triangulate
      mod_wireframe
      mod_data_transfer
      mod_normaledit
      decimate
      degenerate_dissolve
      delete_loose

      fill_hole
      make_planar
      split_concave
      split_nonplanar
      merge
      separate
      crease
      faceregions
      perimeter
      polygonsides

      node_glossyshader
      node_gradient
      node_groupinsert
      node_hairinfo
      hue
      node_holdoutshader
      node_huesaturation
      saturation
      node_impaint
      node_invert

      cryptomatte
      output
      increase_kerning
      decrease_kerning
      sphere
      stroke
      rimlight
      uv
      window
      swirl

      accumulate
      edge_angle
      color_space
      object_contents
      field_at_index
      curve_arc
      equalize_handler
      point_info
      paint_add
      paint_average

      rec
      play
      ff
      rew
      pause
      prev_keyframe
      next_keyframe
      play_audio
      play_reverse
      preview_range

      action_tweak
      pmarker_act
      pmarker_sel
      pmarker
      marker_hlt
      marker
      space2
      space3
      keyingset
      key_dehlt

      key_hlt
      mute_ipo_off
      mute_ipo_on
      random_float
      driver_active
      driver
      area
      mirror_vertexgroup
      snap_symmetry
      symmetrize

      node_keyingscreen
      node_layerweight
      node_lensdistort
      boolean_math
      node_lightfalloff
      node_lightpath
      node_linestyle_output
      node_luminance
      float_compare
      node_makegroup

      modifier_data
      tracker
      tracker_data
      uv_data
      cubeproject
      cylinderproject
      followquads
      lightmappack
      projectfromview
      sphereproject

      paint_blur
      paint_darken
      paint_draw
      paint_lighten
      paint_mix
      paint_multiply
      paint_smear
      paint_subtract
      blend_to_default
      apply_parent_inverse

      solo_off
      solo_on
      frame_prev
      frame_next
      nla_pushdown
      ipo_constant
      ipo_linear
      ipo_bezier
      ipo_sine
      ipo_quad

      ipo_cubic
      ipo_quart
      ipo_quint
      ipo_expo
      ipo_circ
      ipo_bounce
      ipo_elastic
      ipo_back
      ipo_ease_in
      ipo_ease_out

      ipo_ease_in_out
      normalize_fcurves
      light_size
      light_strength
      dof
      lens_angle
      x_icon
      y_icon
      z_icon
      extend_vertices

      node_mapping
      node_clamp
      node_denoise
      node_math
      node_mixrgb
      node_mixshader
      node_map_range
      node_vertex_color
      node_moviedistort
      node_volume_info

      mouse_lmb
      mouse_mmb
      mouse_rmb
      mouse_move
      mouse_lmb_drag
      mouse_mmb_drag
      mouse_mmb_scroll # BFA - New
      mouse_lmb_2x # BFA - New
      mouse_rmb_drag
      automerge_off
      automerge_on
      node_white_noise

      delete_duplicate
      attribute_store
      named_attribute
      combine_color
      separate_color
      geometry_nodes
      geometry_nodes_active
      instance_rotate
      instance_scale
      volume_cube

      vertexsel
      edgesel
      facesel
      loopsel
      drawsize
      rotate
      cursor
      rotatecollection
      rotatecenter
      rotactive

      align
      hide_unselected
      smoothcurve
      spherecurve
      rootcurve
      sharpcurve
      lincurve
      nocurve
      rndcurve
      prop_off

      prop_on
      prop_con
      clear_track
      particle_point
      particle_tip
      particle_path
      rip
      rip_fill
      hook_new
      hook_selected

      4l_on
      4l_off
      node_normalize
      node_normalmap
      node_objectinfo
      node_output
      node_particleinfo
      node_pixelated
      node_planetrackdeform
      node_pointcloud

      parent_bone
      parent_curve
      parent_lattice
      parent_object
      togglecaps_both
      togglecaps_default
      togglecaps_end
      togglecaps_start
      snap_step
      snap_step_second

      similar
      snap_face_nearest
      field_domain
      deform_curves
      vertex_crease
      edge_path_to_selection
      edge_paths_to_curves
      mesh_to_volume
      startpoint
      outline

      man_trans
      man_rot
      man_scale
      manipul
      snap_off
      snap_on
      snap_normal
      snap_grid
      snap_vertex
      snap_edge

      snap_face
      snap_volume
      snap_increment
      sticky_uvs_loc
      sticky_uvs_disable
      sticky_uvs_vert
      clipuv_dehlt
      clipuv_hlt
      snap_peel_object
      grid

      undo
      redo
      repeat
      undo_history
      redo_history
      bevel
      hook_bone
      hook_assign
      hook_reset
      hook_recenter

      node_principled
      node_range
      node_refractionshader
      node_rgbtobw
      node_reroute
      node_rgb
      node_rgbcurve
      select_handle_both
      select_handle_left
      select_handle_right

      select_difference
      select_extend
      select_intersect
      select_set
      select_subtract
      fcurve_snapshot
      external_drive
      network_drive
      object_hidden
      desktop

      volume_distribute
      corners_of_face
      corners_of_vertex
      edges_of_corner
      edges_of_vertex
      face_of_corner
      offset_corner_in_face
      vertex_of_corner
      sample_nearest_surface
      sample_uv_surface

      pastedown
      copydown
      pasteflipup
      pasteflipdown
      slide_edge
      slide_vertex
      smooth_vertex
      point_separate
      snap_surface
      outliner_ob_curves

      hair_data
      retopo
      uv_vertexsel
      uv_edgesel
      uv_facesel
      uv_islandsel
      uv_sync_select
      noise
      randomize
      extrude_region

      show_unselected
      dupli_extrude
      dupli_extrude_rotate
      spin
      screw
      make_regular
      hook_remove
      hook_select
      box_mask
      clear_mask

      point_rotate
      node_separate_ycbcra
      node_separate_yuva
      node_separatehsv
      node_separatergb
      node_separatexyz
      node_sky
      node_sss
      node_stabilize2d
      point_instance

      con_camerasolver
      con_followtrack
      con_objectsolver
      con_loclike
      con_rotlike
      con_sizelike
      con_translike
      con_distlimit
      con_loclimit
      con_rotlimit

      point_of_curve
      curve_of_point
      offset_point_in_curve
      curve_normal
      self_object
      sample_index
      sample_nearest
      image_info
      blur_attribute
      node_mix

      checkmark
      file_archive
      snap_face_center
      transform_origins
      point_distribute
      transfer_uv
      ortho
      push_pull
      shrink_fatten

      attribute_randomize
      view
      tilt
      axis_side
      axis_front
      axis_top
      outliner_ob_pointcloud
      pointcloud_data
      outliner_ob_volume
      volume_data

      layer_used
      layer_active
      transform_mirror
      transform_move
      transform_rotate
      transform_scale
      seq_add
      fill_mask
      invert_mask
      lasso_mask

      brightness_contrast
      node_sunbeams
      attribute_mix
      attribute_math
      node_tangent
      node_texcoordinate
      attribute_fill
      attribute_compare
      node_tonemap
      node_toonshader
      node_trackposition

      con_sizelimit
      con_samevol
      con_transform
      con_transform_cache
      con_clampto
      con_kinematic
      con_locktrack
      con_splineik
      con_stretchto
      con_trackto

      winding
      facegroup
      current_file
      box_show
      box_hide
      box_trim
      box_add
      lasso_add
      lasso_trim
      line_project

      load_3ds
      load_bvh
      load_dae
      load_fbx
      load_obj
      load_ply
      load_stl
      load_svg
      load_x3d
      save_3ds

      save_bvh
      save_dae
      save_fbx
      save_obj
      save_ply
      save_stl
      save_x3d
      load_abc
      save_abc
      rotate_minus_90

      rotate_plus_90
      mirror_x
      mirror_y
      mirror_z
      library
      library_object
      dirty_vertex
      huesatval
      levels
      seq_text

      node_transform
      node_translucent
      node_transparent
      node_ungroup
      node_uvalongstroke
      save_usd
      node_value
      node_vector
      node_vector_blur
      node_vector_transform

      con_armature
      con_childof
      con_floor
      con_followpath
      con_pivot
      con_shrinkwrap
      con_action
      follow_leader
      goal
      protect

      surface_smooth
      inflate
      relax_face_sets
      relax_topology
      enhance
      interpolate_curve
      index_of_nearest
      orientation_parent
      kuwahara
      corners_of_edge

      sortalpha
      sortbyext
      sorttime
      sortsize
      longdisplay
      shortdisplay
      ghost
      imgdisplay
      save_as
      save_copy

      bookmarks
      fontpreview
      filter
      newfolder
      open_recent
      file_alias
      file_parent
      file_refresh
      file_folder
      attribute_colorramp
      file_blend

      file_image
      file_movie
      file_script
      file_sound
      file_font
      file_text
      select_first
      select_last
      controlpointrow
      make_curvesegment

      node_vectormath
      node_velvet
      node_viewer
      node_viwersplit
      node_volumeabsorption
      node_volumescatter
      select_tracks
      node_wavelength
      node_waves
      node_wireframe

      anchor_bottom
      anchor_center
      anchor_left
      anchor_right
      anchor_top
      align_rotation_to_vector
      avoid
      fight
      flock
      outliner_data_volume

      gradient
      points_to_curves
      mod_equalizer
      axis_angle_to_rotation
      euler_to_rotation
      invert_rotation
      quaternion_to_rotation
      rotation_to_axis_angle
      rotation_to_euler
      rotation_to_quaternion

      recover_auto
      save_prefs
      link_blend
      append_blend
      import
      export
      external_data
      load_factory
      applymovedelta
      applyrotatedelta

      applyscaledelta
      applyalldelta
      applyanidelta
      loop_back
      loop_forwards
      back
      forward
      aligncamera_active
      aligncamera_view
      centertocursor

      lock_clear
      locktoactive
      locktocenter
      file_hidden
      file_backup
      disk_drive
      smooth_radius
      smooth_tilt
      smooth_weight
      clear_tilt

      outliner_data_pointcloud
      outliner_data_hair
      node_zcombine
      node_keying
      lockview_off
      lockview_on
      node_spill
      remove_active_group
      remove_all_groups
      set_frames

      play_sound
      mod_instance
      image_plane
      restrict_instanced_on
      restrict_instanced_off
      heart
      fund
      decorate_library_override
      decorate_linked
      preset_new

      blend_offset
      blend_to_ease
      split_to_instances
      index_switch
      bake
      line_show
      line_hide
      rotation
      instance_transform
      collection_bone_remove

      matplane
      matsphere
      matcube
      monkey
      curves
      aliased
      antialiased
      mat_sphere_sky
      move_texturespace
      scale_texturespace

      randomize_transform
      align_transform
      wordwrap_off
      wordwrap_on
      syntax_off
      syntax_on
      linenumbers_off
      linenumbers_on
      scriptplugins
      bold

      italic
      underlined
      set_lowercase
      set_uppercase
      small_caps
      set_from_faces
      cut
      pastefile
      circle
      copyright

      yen
      absolutepath
      relativepath
      batch_generate
      batch_generate_clear
      datablock_clear
      detect
      disable
      enable
      planetrack

      seq_swap_left
      seq_swap_right
      texture_data
      attribute_vectormath
      toggle_meta
      seq_snap_strip
      world_data
      node_texture
      anim
      trash

      scale_average
      set_time
      set_selection
      view_graph
      internet
      euro
      export_collection
      axes_to_rotation
      active_element
      collection_bone_add

      seq_sequencer
      seq_preview
      seq_luma_waveform
      seq_chroma_scope
      seq_histogram
      seq_splitview
      nextactive
      previousactive
      brush_reset
      image_rgb

      image_rgb_alpha
      image_alpha
      image_zdepth
      palette
      cursortoactive
      cursortocenter
      cursortogrid
      cursortoselection
      selectiontocursoroffset
      selectiontoactive

      selectiontocursor
      selectiontogrid
      cursor_to_pixels
      snap_to_adjacent
      snap_to_pixels
      pattern
      degree
      double_left
      double_right
      dutch_florin

      german_s
      multiplication
      pound
      promille
      spanish_exclamation
      spanish_question
      super_one
      super_two
      super_three
      trademark

      seq_snap_to_frame
      seq_clear_offset
      rna_add
      strands
      seq_deinterlace
      seq_move_extend
      seq_slip_contents
      seq_remove_gaps
      seq_insert_gaps
      three_dots

      face_maps_active
      select_key
      face_set
      set_face_set
      lasso_show
      lasso_hide
      menu_switch
      unicode
      marksharpangle
      collection_bone_new
	  
	  
      combine_transform
      invert_matrix
      multiply_matrix
      project_point
      separate_transform
      transform_direction
      transform_point
      transpose_matrix
      combine_matrix
      separate_matrix

      mouse_position
      gabor_noise
      geometry_name
      dial_gizmo
      linear_gizmo
      transform_gizmo

      warning
      face_corner
      pointcloud_point

      # ------------------------- large --------------------------
      cancel_large
      warning_large
      question_large
      info_large
      disc_large
      disk_drive_large
      external_drive_large
      file_folder_large
      file_large
      file_parent_large
      network_drive_large
      blender_large
      blender_logo_large


      #  The following are used when creating the Event Icons.
      key_backspace
      key_backspace_filled
      key_command
      key_command_filled
      key_control
      key_control_filled
      key_empty1
      key_empty1_filled
      key_empty2
      key_empty2_filled
      key_empty3
      key_empty3_filled
      key_menu
      key_menu_filled
      key_option
      key_option_filled
      key_return
      key_return_filled
      key_ring
      key_ring_filled
      key_shift
      key_shift_filled
      key_tab
      key_tab_filled
      key_windows
      key_windows_filled

    )
    set(SVG_CONTENTS_H)
    set(SVG_CONTENTS_C)
    foreach(svg ${SVG_FILENAMES_NOEXT})
      data_to_c_simple(../../../../release/datafiles/icons_svg/${svg}.svg SRC)
      string(TOUPPER ${svg} svg_name_upper)
      list(APPEND SVG_CONTENTS_H
        "extern const char datatoc_${svg}_svg[]\;\n"
      )
      list(APPEND SVG_CONTENTS_C
        "case ICON_${svg_name_upper}: return datatoc_${svg}_svg\;\n"
      )
    endforeach()
    unset(svg_name_upper)

    list(JOIN SVG_CONTENTS_C "" SVG_CONTENTS_C)
    list(JOIN SVG_CONTENTS_H "" SVG_CONTENTS_H)

    configure_file(
      "svg_icons.h.in"
      "${CMAKE_CURRENT_BINARY_DIR}/svg_icons.h"
      ESCAPE_QUOTES
      @ONLY
    )
    configure_file(
      "svg_icons.cc.in"
      "${CMAKE_CURRENT_BINARY_DIR}/svg_icons.cc"
      ESCAPE_QUOTES
      @ONLY
    )

    list(APPEND SRC ${CMAKE_CURRENT_BINARY_DIR}/svg_icons.h)
    list(APPEND SRC ${CMAKE_CURRENT_BINARY_DIR}/svg_icons.cc)
    # Blend files.
    data_to_c_simple(../../../../release/datafiles/preview.blend SRC)
    data_to_c_simple(../../../../release/datafiles/preview_grease_pencil.blend SRC)
    data_to_c_simple(../../../../release/datafiles/preview_grease_pencil_legacy.blend SRC)

    # Images.
    data_to_c_simple(../../../../release/datafiles/splash.png SRC)

    unset(SVG_CONTENTS_H)
    unset(SVG_CONTENTS_C)
    unset(SVG_FILENAMES_NOEXT)

  endif()

  data_to_c_simple(../../../../release/datafiles/startup.blend SRC)
endif()

unset(ICON_NAMES)

blender_add_lib(bf_editor_datafiles "${SRC}" "${INC}" "${INC_SYS}" "${LIB}")
add_library(bf::editor::datafiles ALIAS bf_editor_datafiles)
