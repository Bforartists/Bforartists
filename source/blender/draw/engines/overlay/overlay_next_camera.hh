/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup overlay
 */

#pragma once

#include "BKE_camera.h"

#include "DEG_depsgraph_query.hh"

#include "BKE_tracking.h"

#include "BLI_math_rotation.h"

#include "DNA_camera_types.h"

#include "ED_view3d.hh"

#include "draw_manager_text.hh"
#include "overlay_next_empty.hh"
#include "overlay_next_private.hh"

static float camera_offaxis_shiftx_get(const Scene *scene,
                                       const Object *ob,
                                       float corner_x,
                                       bool right_eye)
{
  const Camera *cam = static_cast<const Camera *>(ob->data);
  if (cam->stereo.convergence_mode == CAM_S3D_OFFAXIS) {
    const char *viewnames[2] = {STEREO_LEFT_NAME, STEREO_RIGHT_NAME};
    const float shiftx = BKE_camera_multiview_shift_x(&scene->r, ob, viewnames[right_eye]);
    const float delta_shiftx = shiftx - cam->shiftx;
    const float width = corner_x * 2.0f;
    return delta_shiftx * width;
  }

  return 0.0;
}

namespace blender::draw::overlay {
struct CameraInstanceData : public ExtraInstanceData {
 public:
  float &volume_start = color_[2];
  float &volume_end = color_[3];
  float &depth = color_[3];
  float &focus = color_[3];
  float4x4 &matrix = object_to_world_;
  float &dist_color_id = matrix[0][3];
  float &corner_x = matrix[0][3];
  float &corner_y = matrix[1][3];
  float &center_x = matrix[2][3];
  float &clip_start = matrix[2][3];
  float &mist_start = matrix[2][3];
  float &center_y = matrix[3][3];
  float &clip_end = matrix[3][3];
  float &mist_end = matrix[3][3];

  CameraInstanceData(const CameraInstanceData &data)
      : CameraInstanceData(data.object_to_world_, data.color_)
  {
  }

  CameraInstanceData(const float4x4 &p_matrix, const float4 &color)
      : ExtraInstanceData(p_matrix, color, 1.0f){};
};

class Cameras {
  using CameraInstanceBuf = ShapeInstanceBuf<ExtraInstanceData>;

 private:
  PassSimple ps_ = {"Cameras"};

  /* Camera background images with "Depth" switched to "Back".
   * Shown in camera view behind all objects. */
  PassMain background_ps_ = {"background_ps_"};
  /* Camera background images with "Depth" switched to "Front".
   * Shown in camera view in front of all objects. */
  PassMain foreground_ps_ = {"foreground_ps_"};

  /* Same as `background_ps_` with "View as Render" checked. */
  PassMain background_scene_ps_ = {"background_scene_ps_"};
  /* Same as `foreground_ps_` with "View as Render" checked. */
  PassMain foreground_scene_ps_ = {"foreground_scene_ps_"};

  View view_reference_images = {"view_reference_images"};
  float view_dist = 0.0f;

  struct CallBuffers {
    const SelectionType selection_type_;
    CameraInstanceBuf distances_buf = {selection_type_, "camera_distances_buf"};
    CameraInstanceBuf frame_buf = {selection_type_, "camera_frame_buf"};
    CameraInstanceBuf tria_buf = {selection_type_, "camera_tria_buf"};
    CameraInstanceBuf tria_wire_buf = {selection_type_, "camera_tria_wire_buf"};
    CameraInstanceBuf volume_buf = {selection_type_, "camera_volume_buf"};
    CameraInstanceBuf volume_wire_buf = {selection_type_, "camera_volume_wire_buf"};
    CameraInstanceBuf sphere_solid_buf = {selection_type_, "camera_sphere_solid_buf"};
    LinePrimitiveBuf stereo_connect_lines = {selection_type_, "camera_dashed_lines_buf"};
    LinePrimitiveBuf tracking_path = {selection_type_, "camera_tracking_path_buf"};
    Empties::CallBuffers empties{selection_type_};
  } call_buffers_;

  static void view3d_reconstruction(const select::ID select_id,
                                    const Scene *scene,
                                    const View3D *v3d,
                                    const float4 &color,
                                    const ObjectRef &ob_ref,
                                    const bool is_select,
                                    Resources &res,
                                    CallBuffers &call_buffers)
  {
    const DRWContextState *draw_ctx = DRW_context_state_get();
    Object *ob = ob_ref.object;

    MovieClip *clip = BKE_object_movieclip_get((Scene *)scene, ob, false);
    if (clip == nullptr) {
      return;
    }

    const bool is_solid_bundle = (v3d->bundle_drawtype == OB_EMPTY_SPHERE) &&
                                 ((v3d->shading.type != OB_SOLID) || !XRAY_FLAG_ENABLED(v3d));

    MovieTracking *tracking = &clip->tracking;
    /* Index must start in 1, to mimic BKE_tracking_track_get_for_selection_index. */
    int track_index = 1;

    float4 bundle_color_custom;
    float *bundle_color_solid = G_draw.block.color_bundle_solid;
    float *bundle_color_unselected = G_draw.block.color_wire;
    uchar4 text_color_selected, text_color_unselected;
    /* Color Management: Exception here as texts are drawn in sRGB space directly. */
    UI_GetThemeColor4ubv(TH_SELECT, text_color_selected);
    UI_GetThemeColor4ubv(TH_TEXT, text_color_unselected);

    float4x4 camera_mat;
    BKE_tracking_get_camera_object_matrix(ob, camera_mat.ptr());

    const float4x4 object_to_world{ob->object_to_world().ptr()};

    for (MovieTrackingObject *tracking_object :
         ListBaseWrapper<MovieTrackingObject>(&tracking->objects))
    {
      float4x4 tracking_object_mat;

      if (tracking_object->flag & TRACKING_OBJECT_CAMERA) {
        tracking_object_mat = camera_mat;
      }
      else {
        const int framenr = BKE_movieclip_remap_scene_to_clip_frame(
            clip, DEG_get_ctime(draw_ctx->depsgraph));

        float4x4 object_mat;
        BKE_tracking_camera_get_reconstructed_interpolate(
            tracking, tracking_object, framenr, object_mat.ptr());

        tracking_object_mat = object_to_world * math::invert(object_mat);
      }

      for (MovieTrackingTrack *track :
           ListBaseWrapper<MovieTrackingTrack>(&tracking_object->tracks))
      {
        if ((track->flag & TRACK_HAS_BUNDLE) == 0) {
          continue;
        }
        bool is_selected = TRACK_SELECTED(track);

        float4x4 bundle_mat = math::translate(tracking_object_mat, float3(track->bundle_pos));

        const float *bundle_color;
        if (track->flag & TRACK_CUSTOMCOLOR) {
          /* Meh, hardcoded srgb transform here. */
          /* TODO: change the actual DNA color to be linear. */
          srgb_to_linearrgb_v3_v3(bundle_color_custom, track->color);
          bundle_color_custom[3] = 1.0;

          bundle_color = bundle_color_custom;
        }
        else if (is_solid_bundle) {
          bundle_color = bundle_color_solid;
        }
        else if (is_selected) {
          bundle_color = color;
        }
        else {
          bundle_color = bundle_color_unselected;
        }

        const select::ID track_select_id = is_select ? res.select_id(ob_ref, track_index++ << 16) :
                                                       select_id;
        if (is_solid_bundle) {
          if (is_selected) {
            Empties::object_sync(track_select_id,
                                 bundle_mat,
                                 v3d->bundle_size,
                                 v3d->bundle_drawtype,
                                 color,
                                 call_buffers.empties);
          }

          call_buffers.sphere_solid_buf.append(
              ExtraInstanceData{bundle_mat, float4(float3(bundle_color), 1.0f), v3d->bundle_size},
              track_select_id);
        }
        else {
          Empties::object_sync(track_select_id,
                               bundle_mat,
                               v3d->bundle_size,
                               v3d->bundle_drawtype,
                               bundle_color,
                               call_buffers.empties);
        }

        if ((v3d->flag2 & V3D_SHOW_BUNDLENAME) && !is_select) {
          DRWTextStore *dt = DRW_text_cache_ensure();

          DRW_text_cache_add(dt,
                             bundle_mat[3],
                             track->name,
                             strlen(track->name),
                             10,
                             0,
                             DRW_TEXT_CACHE_GLOBALSPACE | DRW_TEXT_CACHE_STRING_PTR,
                             is_selected ? text_color_selected : text_color_unselected);
        }
      }

      if ((v3d->flag2 & V3D_SHOW_CAMERAPATH) && (tracking_object->flag & TRACKING_OBJECT_CAMERA) &&
          !is_select)
      {
        const MovieTrackingReconstruction *reconstruction = &tracking_object->reconstruction;

        if (reconstruction->camnr) {
          const MovieReconstructedCamera *camera = reconstruction->cameras;
          float3 v0, v1 = float3(0.0f);
          for (int a = 0; a < reconstruction->camnr; a++, camera++) {
            v0 = v1;
            v1 = math::transform_point(camera_mat, float3(camera->mat[3]));
            if (a > 0) {
              /* This one is suboptimal (gl_lines instead of gl_line_strip)
               * but we keep this for simplicity */
              call_buffers.tracking_path.append(v0, v1, TH_CAMERA_PATH);
            }
          }
        }
      }
    }
  }

  /**
   * Draw the stereo 3d support elements (cameras, plane, volume).
   * They are only visible when not looking through the camera:
   */
  static void stereoscopy_extra(const CameraInstanceData &instdata,
                                const select::ID select_id,
                                const Scene *scene,
                                const View3D *v3d,
                                const bool is_select,
                                Resources &res,
                                Object *ob,
                                CallBuffers &call_buffers)
  {
    CameraInstanceData stereodata = instdata;

    const Camera *cam = static_cast<const Camera *>(ob->data);
    const char *viewnames[2] = {STEREO_LEFT_NAME, STEREO_RIGHT_NAME};

    const bool is_stereo3d_cameras = (v3d->stereo3d_flag & V3D_S3D_DISPCAMERAS) != 0;
    const bool is_stereo3d_plane = (v3d->stereo3d_flag & V3D_S3D_DISPPLANE) != 0;
    const bool is_stereo3d_volume = (v3d->stereo3d_flag & V3D_S3D_DISPVOLUME) != 0;

    if (!is_stereo3d_cameras) {
      /* Draw single camera. */
      call_buffers.frame_buf.append(instdata, select_id);
    }

    for (const int eye : IndexRange(2)) {
      ob = BKE_camera_multiview_render(scene, ob, viewnames[eye]);
      BKE_camera_multiview_model_matrix(&scene->r, ob, viewnames[eye], stereodata.matrix.ptr());

      stereodata.corner_x = instdata.corner_x;
      stereodata.corner_y = instdata.corner_y;
      stereodata.center_x = instdata.center_x +
                            camera_offaxis_shiftx_get(scene, ob, instdata.corner_x, eye);
      stereodata.center_y = instdata.center_y;
      stereodata.depth = instdata.depth;

      if (is_stereo3d_cameras) {
        call_buffers.frame_buf.append(stereodata, select_id);

        /* Connecting line between cameras. */
        call_buffers.stereo_connect_lines.append(stereodata.matrix.location(),
                                                 instdata.object_to_world_.location(),
                                                 res.theme_settings.color_wire,
                                                 select_id);
      }

      if (is_stereo3d_volume && !is_select) {
        float r = (eye == 1) ? 2.0f : 1.0f;

        stereodata.volume_start = -cam->clip_start;
        stereodata.volume_end = -cam->clip_end;
        /* Encode eye + intensity and alpha (see shader) */
        copy_v2_fl2(stereodata.color_, r + 0.15f, 1.0f);
        call_buffers.volume_wire_buf.append(stereodata, select_id);

        if (v3d->stereo3d_volume_alpha > 0.0f) {
          /* Encode eye + intensity and alpha (see shader) */
          copy_v2_fl2(stereodata.color_, r + 0.999f, v3d->stereo3d_volume_alpha);
          call_buffers.volume_buf.append(stereodata, select_id);
        }
        /* restore */
        copy_v3_v3(stereodata.color_, instdata.color_);
      }
    }

    if (is_stereo3d_plane && !is_select) {
      if (cam->stereo.convergence_mode == CAM_S3D_TOE) {
        /* There is no real convergence plane but we highlight the center
         * point where the views are pointing at. */
        // zero_v3(stereodata.mat[0]); /* We reconstruct from Z and Y */
        // zero_v3(stereodata.mat[1]); /* Y doesn't change */
        stereodata.matrix.z_axis() = float3(0.0f);
        stereodata.matrix.location() = float3(0.0f);
        for (int i : IndexRange(2)) {
          float4x4 mat;
          /* Need normalized version here. */
          BKE_camera_multiview_model_matrix(&scene->r, ob, viewnames[i], mat.ptr());
          stereodata.matrix.z_axis() += mat.z_axis();
          stereodata.matrix.location() += mat.location() * 0.5f;
        }
        stereodata.matrix.z_axis() = math::normalize(stereodata.matrix.z_axis());
        stereodata.matrix.x_axis() = math::cross(stereodata.matrix.y_axis(),
                                                 stereodata.matrix.z_axis());
      }
      else if (cam->stereo.convergence_mode == CAM_S3D_PARALLEL) {
        /* Show plane at the given distance between the views even if it makes no sense. */
        stereodata.matrix.location() = float3(0.0f);
        for (int i : IndexRange(2)) {
          float4x4 mat;
          BKE_camera_multiview_model_matrix_scaled(&scene->r, ob, viewnames[i], mat.ptr());
          stereodata.matrix.location() += mat.location() * 0.5f;
        }
      }
      else if (cam->stereo.convergence_mode == CAM_S3D_OFFAXIS) {
        /* Nothing to do. Everything is already setup. */
      }
      stereodata.volume_start = -cam->stereo.convergence_distance;
      stereodata.volume_end = -cam->stereo.convergence_distance;
      /* Encode eye + intensity and alpha (see shader) */
      copy_v2_fl2(stereodata.color_, 0.1f, 1.0f);
      call_buffers.volume_wire_buf.append(stereodata, select_id);

      if (v3d->stereo3d_convergence_alpha > 0.0f) {
        /* Encode eye + intensity and alpha (see shader) */
        copy_v2_fl2(stereodata.color_, 0.0f, v3d->stereo3d_convergence_alpha);
        call_buffers.volume_buf.append(stereodata, select_id);
      }
    }
  }

  bool enabled_ = false;

 public:
  Cameras(const SelectionType selection_type) : call_buffers_{selection_type} {};

  void begin_sync(Resources &res, State &state, View &view)
  {
    enabled_ = state.space_type == SPACE_VIEW3D;

    if (!enabled_) {
      return;
    }

    view_dist = state.view_dist_get(view.winmat());

    call_buffers_.distances_buf.clear();
    call_buffers_.frame_buf.clear();
    call_buffers_.tria_buf.clear();
    call_buffers_.tria_wire_buf.clear();
    call_buffers_.volume_buf.clear();
    call_buffers_.volume_wire_buf.clear();
    call_buffers_.sphere_solid_buf.clear();
    call_buffers_.stereo_connect_lines.clear();
    call_buffers_.tracking_path.clear();
    Empties::begin_sync(call_buffers_.empties);

    /* Init image passes. */
    auto init_pass = [&](PassMain &pass, DRWState draw_state) {
      pass.init();
      pass.state_set(draw_state, state.clipping_plane_count);
      pass.shader_set(res.shaders.image_plane.get());
      pass.bind_ubo("globalsBlock", &res.globals_buf);
      res.select_bind(pass);
    };

    DRWState draw_state;
    draw_state = DRW_STATE_WRITE_COLOR | DRW_STATE_DEPTH_GREATER | DRW_STATE_BLEND_ALPHA_PREMUL;
    init_pass(background_ps_, draw_state);

    draw_state = DRW_STATE_WRITE_COLOR | DRW_STATE_BLEND_ALPHA_UNDER_PREMUL;
    init_pass(background_scene_ps_, draw_state);

    draw_state = DRW_STATE_WRITE_COLOR | DRW_STATE_BLEND_ALPHA_PREMUL;
    init_pass(foreground_ps_, draw_state);
    init_pass(foreground_scene_ps_, draw_state);
  }

  void object_sync(
      const ObjectRef &ob_ref, ShapeCache &shapes, Manager &manager, Resources &res, State &state)
  {
    if (!enabled_) {
      return;
    }

    Object *ob = ob_ref.object;
    const select::ID select_id = res.select_id(ob_ref);
    CameraInstanceData data(ob->object_to_world(), res.object_wire_color(ob_ref, state));

    const View3D *v3d = state.v3d;
    const Scene *scene = state.scene;
    const RegionView3D *rv3d = state.rv3d;

    const Camera *cam = static_cast<Camera *>(ob->data);
    const Object *camera_object = DEG_get_evaluated_object(state.depsgraph, v3d->camera);
    const bool is_select = call_buffers_.selection_type_ == SelectionType::ENABLED;
    const bool is_active = (ob == camera_object);
    const bool is_camera_view = (is_active && (rv3d->persp == RV3D_CAMOB));

    const bool is_multiview = (scene->r.scemode & R_MULTIVIEW) != 0;
    const bool is_stereo3d_view = (scene->r.views_format == SCE_VIEWS_FORMAT_STEREO_3D);
    const bool is_stereo3d_display_extra = is_active && is_multiview && (!is_camera_view) &&
                                           ((v3d->stereo3d_flag) != 0);
    const bool is_selection_camera_stereo = is_select && is_camera_view && is_multiview &&
                                            is_stereo3d_view;

    float3 scale = math::to_scale(data.matrix);
    /* BKE_camera_multiview_model_matrix already accounts for scale, don't do it here. */
    if (is_selection_camera_stereo) {
      scale = float3(1.0f);
    }
    else if (ELEM(0.0f, scale.x, scale.y, scale.z)) {
      /* Avoid division by 0. */
      return;
    }
    float4x3 vecs;
    float2 aspect_ratio;
    float2 shift;
    float drawsize;

    BKE_camera_view_frame_ex(scene,
                             cam,
                             cam->drawsize,
                             is_camera_view,
                             1.0f / scale,
                             aspect_ratio,
                             shift,
                             &drawsize,
                             vecs.ptr());

    /* Apply scale to simplify the rest of the drawing. */
    for (int i = 0; i < 4; i++) {
      vecs[i] *= scale;
      /* Project to z=-1 plane. Makes positioning / scaling easier. (see shader) */
      mul_v2_fl(vecs[i], 1.0f / std::abs(vecs[i].z));
    }

    /* Frame coords */
    const float2 center = (vecs[0].xy() + vecs[2].xy()) * 0.5f;
    const float2 corner = vecs[0].xy() - center.xy();
    data.corner_x = corner.x;
    data.corner_y = corner.y;
    data.center_x = center.x;
    data.center_y = center.y;
    data.depth = vecs[0].z;

    if (is_camera_view) {
      /* TODO(Miguel Pozo) */
      if (!DRW_state_is_image_render()) {
        /* Only draw the frame. */
        if (is_multiview) {
          float4x4 mat;
          const bool is_right = v3d->multiview_eye == STEREO_RIGHT_ID;
          const char *view_name = is_right ? STEREO_RIGHT_NAME : STEREO_LEFT_NAME;
          BKE_camera_multiview_model_matrix(&scene->r, ob, view_name, mat.ptr());
          data.center_x += camera_offaxis_shiftx_get(scene, ob, data.corner_x, is_right);
          for (int i : IndexRange(4)) {
            /* Partial copy to avoid overriding packed data. */
            copy_v3_v3(data.matrix[i], mat[i].xyz());
          }
        }
        data.depth *= -1.0f; /* Hides the back of the camera wires (see shader). */
        call_buffers_.frame_buf.append(data, select_id);
      }
    }
    else {
      /* Stereo cameras, volumes, plane drawing. */
      if (is_stereo3d_display_extra) {
        stereoscopy_extra(data, select_id, scene, v3d, is_select, res, ob, call_buffers_);
      }
      else {
        call_buffers_.frame_buf.append(data, select_id);
      }
    }

    if (!is_camera_view) {
      /* Triangle. */
      float tria_size = 0.7f * drawsize / fabsf(data.depth);
      float tria_margin = 0.1f * drawsize / fabsf(data.depth);
      data.center_x = center.x;
      data.center_y = center.y + data.corner_y + tria_margin + tria_size;
      data.corner_x = data.corner_y = -tria_size;
      (is_active ? call_buffers_.tria_buf : call_buffers_.tria_wire_buf).append(data, select_id);
    }

    if (cam->flag & CAM_SHOWLIMITS) {
      /* Scale focus point. */
      data.matrix.x_axis() *= cam->drawsize;
      data.matrix.y_axis() *= cam->drawsize;

      data.dist_color_id = (is_active) ? 3 : 2;
      data.focus = -BKE_camera_object_dof_distance(ob);
      data.clip_start = cam->clip_start;
      data.clip_end = cam->clip_end;
      call_buffers_.distances_buf.append(data, select_id);
    }

    if (cam->flag & CAM_SHOWMIST) {
      World *world = scene->world;
      if (world) {
        data.dist_color_id = (is_active) ? 1 : 0;
        data.focus = 1.0f; /* Disable */
        data.mist_start = world->miststa;
        data.mist_end = world->miststa + world->mistdist;
        call_buffers_.distances_buf.append(data, select_id);
      }
    }

    /* Motion Tracking. */
    if ((v3d->flag2 & V3D_SHOW_RECONSTRUCTION) != 0) {
      view3d_reconstruction(select_id,
                            scene,
                            v3d,
                            res.object_wire_color(ob_ref, state),
                            ob_ref,
                            is_select,
                            res,
                            call_buffers_);
    }

    if (is_camera_view && (cam->flag & CAM_SHOW_BG_IMAGE) &&
        !BLI_listbase_is_empty(&cam->bg_images))
    {
      sync_camera_images(
          ob_ref, select_id, shapes, manager, state, res, call_buffers_.selection_type_);
    }
  }

  void end_sync(Resources &res, ShapeCache &shapes, const State &state)
  {
    if (!enabled_) {
      return;
    }

    ps_.init();
    res.select_bind(ps_);

    {
      PassSimple::Sub &sub_pass = ps_.sub("volume");
      sub_pass.state_set(DRW_STATE_WRITE_COLOR | DRW_STATE_BLEND_ALPHA |
                             DRW_STATE_DEPTH_LESS_EQUAL | DRW_STATE_CULL_BACK,
                         state.clipping_plane_count);
      sub_pass.shader_set(res.shaders.extra_shape.get());
      sub_pass.bind_ubo("globalsBlock", &res.globals_buf);
      call_buffers_.volume_buf.end_sync(sub_pass, shapes.camera_volume.get());
    }
    {
      PassSimple::Sub &sub_pass = ps_.sub("volume_wire");
      sub_pass.state_set(DRW_STATE_WRITE_COLOR | DRW_STATE_BLEND_ALPHA |
                             DRW_STATE_DEPTH_LESS_EQUAL | DRW_STATE_CULL_BACK,
                         state.clipping_plane_count);
      sub_pass.shader_set(res.shaders.extra_shape.get());
      sub_pass.bind_ubo("globalsBlock", &res.globals_buf);
      call_buffers_.volume_wire_buf.end_sync(sub_pass, shapes.camera_volume_wire.get());
    }

    {
      PassSimple::Sub &sub_pass = ps_.sub("camera_shapes");
      sub_pass.state_set(DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH |
                             DRW_STATE_DEPTH_LESS_EQUAL,
                         state.clipping_plane_count);
      sub_pass.shader_set(res.shaders.extra_shape.get());
      sub_pass.bind_ubo("globalsBlock", &res.globals_buf);
      call_buffers_.distances_buf.end_sync(sub_pass, shapes.camera_distances.get());
      call_buffers_.frame_buf.end_sync(sub_pass, shapes.camera_frame.get());
      call_buffers_.tria_buf.end_sync(sub_pass, shapes.camera_tria.get());
      call_buffers_.tria_wire_buf.end_sync(sub_pass, shapes.camera_tria_wire.get());
      call_buffers_.sphere_solid_buf.end_sync(sub_pass, shapes.sphere_low_detail.get());
    }
    {
      PassSimple::Sub &sub_pass = ps_.sub("camera_extra_wire");
      sub_pass.state_set(DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH |
                             DRW_STATE_DEPTH_LESS_EQUAL,
                         state.clipping_plane_count);
      sub_pass.shader_set(res.shaders.extra_wire.get());
      sub_pass.bind_ubo("globalsBlock", &res.globals_buf);
      call_buffers_.stereo_connect_lines.end_sync(sub_pass);
      call_buffers_.tracking_path.end_sync(sub_pass);
    }
    {
      PassSimple::Sub &sub_pass = ps_.sub("empties");
      Empties::end_sync(res, shapes, state, sub_pass, call_buffers_.empties);
    }
  }

  void draw(Framebuffer &framebuffer, Manager &manager, View &view)
  {
    if (!enabled_) {
      return;
    }

    GPU_framebuffer_bind(framebuffer);
    manager.submit(ps_, view);
  }

  void draw_scene_background_images(Framebuffer &framebuffer, Manager &manager, View &view)
  {
    if (!enabled_) {
      return;
    }

    GPU_framebuffer_bind(framebuffer);
    manager.submit(background_scene_ps_, view);
    manager.submit(foreground_scene_ps_, view);
  }

  void draw_background_images(Framebuffer &framebuffer, Manager &manager, View &view)
  {
    if (!enabled_) {
      return;
    }

    GPU_framebuffer_bind(framebuffer);
    manager.submit(background_ps_, view);
  }

  void draw_in_front(Framebuffer &framebuffer, Manager &manager, View &view)
  {
    if (!enabled_) {
      return;
    }

    view_reference_images.sync(view.viewmat(),
                               winmat_polygon_offset(view.winmat(), view_dist, -1.0f));
    GPU_framebuffer_bind(framebuffer);
    manager.submit(foreground_ps_, view_reference_images);
  }

 private:
  void sync_camera_images(const ObjectRef &ob_ref,
                          select::ID select_id,
                          ShapeCache &shapes,
                          Manager &manager,
                          const State &state,
                          Resources &res,
                          const SelectionType selection_type)
  {
    Object *ob = ob_ref.object;
    const Camera *cam = static_cast<Camera *>(ob->data);

    const bool show_frame = BKE_object_empty_image_frame_is_visible_in_view3d(ob, state.rv3d);

    if (!show_frame || selection_type != SelectionType::DISABLED) {
      return;
    }

    const bool stereo_eye = Images::images_stereo_eye(state.scene, state.v3d) == STEREO_LEFT_ID;
    const char *viewname = (stereo_eye == STEREO_LEFT_ID) ? STEREO_RIGHT_NAME : STEREO_LEFT_NAME;
    float4x4 modelmat;
    BKE_camera_multiview_model_matrix(&state.scene->r, ob, viewname, modelmat.ptr());

    for (const CameraBGImage *bgpic : ConstListBaseWrapper<CameraBGImage>(&cam->bg_images)) {
      if (bgpic->flag & CAM_BGIMG_FLAG_DISABLED) {
        continue;
      }

      float aspect = 1.0;
      bool use_alpha_premult;
      bool use_view_transform = false;
      float4x4 mat;

      /* retrieve the image we want to show, continue to next when no image could be found */
      GPUTexture *tex = image_camera_background_texture_get(
          bgpic, state, res, aspect, use_alpha_premult, use_view_transform);

      if (tex) {
        image_camera_background_matrix_get(cam, bgpic, state, aspect, mat);

        const bool is_foreground = (bgpic->flag & CAM_BGIMG_FLAG_FOREGROUND) != 0;
        /* Alpha is clamped just below 1.0 to fix background images to interfere with foreground
         * images. Without this a background image with 1.0 will be rendered on top of a
         * transparent foreground image due to the different blending modes they use. */
        const float4 color_premult_alpha{1.0f, 1.0f, 1.0f, std::min(bgpic->alpha, 0.999999f)};

        PassMain &pass = is_foreground ?
                             (use_view_transform ? foreground_scene_ps_ : foreground_ps_) :
                             (use_view_transform ? background_scene_ps_ : background_ps_);
        pass.bind_texture("imgTexture", tex);
        pass.push_constant("imgPremultiplied", use_alpha_premult);
        pass.push_constant("imgAlphaBlend", true);
        pass.push_constant("isCameraBackground", true);
        pass.push_constant("depthSet", true);
        pass.push_constant("ucolor", color_premult_alpha);
        ResourceHandle res_handle = manager.resource_handle(mat);
        pass.draw(shapes.quad_solid.get(), res_handle, select_id.get());
      }
    }
  }

  static void image_camera_background_matrix_get(const Camera *cam,
                                                 const CameraBGImage *bgpic,
                                                 const State &state,
                                                 const float image_aspect,
                                                 float4x4 &rmat)
  {
    float4x4 rotate, scale = float4x4::identity(), translate = float4x4::identity();

    axis_angle_to_mat4_single(rotate.ptr(), 'Z', -bgpic->rotation);

    /* Normalized Object space camera frame corners. */
    float cam_corners[4][3];
    BKE_camera_view_frame(state.scene, cam, cam_corners);
    float cam_width = fabsf(cam_corners[0][0] - cam_corners[3][0]);
    float cam_height = fabsf(cam_corners[0][1] - cam_corners[1][1]);
    float cam_aspect = cam_width / cam_height;

    if (bgpic->flag & CAM_BGIMG_FLAG_CAMERA_CROP) {
      /* Crop. */
      if (image_aspect > cam_aspect) {
        scale[0][0] *= cam_height * image_aspect;
        scale[1][1] *= cam_height;
      }
      else {
        scale[0][0] *= cam_width;
        scale[1][1] *= cam_width / image_aspect;
      }
    }
    else if (bgpic->flag & CAM_BGIMG_FLAG_CAMERA_ASPECT) {
      /* Fit. */
      if (image_aspect > cam_aspect) {
        scale[0][0] *= cam_width;
        scale[1][1] *= cam_width / image_aspect;
      }
      else {
        scale[0][0] *= cam_height * image_aspect;
        scale[1][1] *= cam_height;
      }
    }
    else {
      /* Stretch. */
      scale[0][0] *= cam_width;
      scale[1][1] *= cam_height;
    }

    translate[3][0] = bgpic->offset[0];
    translate[3][1] = bgpic->offset[1];
    translate[3][2] = cam_corners[0][2];
    if (cam->type == CAM_ORTHO) {
      translate[3].xy() *= cam->ortho_scale;
    }
    /* These lines are for keeping 2.80 behavior and could be removed to keep 2.79 behavior. */
    translate[3][0] *= min_ff(1.0f, cam_aspect);
    translate[3][1] /= max_ff(1.0f, cam_aspect) * (image_aspect / cam_aspect);
    /* quad is -1..1 so divide by 2. */
    scale[0][0] *= 0.5f * bgpic->scale * ((bgpic->flag & CAM_BGIMG_FLAG_FLIP_X) ? -1.0 : 1.0);
    scale[1][1] *= 0.5f * bgpic->scale * ((bgpic->flag & CAM_BGIMG_FLAG_FLIP_Y) ? -1.0 : 1.0);
    /* Camera shift. (middle of cam_corners) */
    translate[3][0] += (cam_corners[0][0] + cam_corners[2][0]) * 0.5f;
    translate[3][1] += (cam_corners[0][1] + cam_corners[2][1]) * 0.5f;

    rmat = translate * rotate * scale;
  }

  GPUTexture *image_camera_background_texture_get(const CameraBGImage *bgpic,
                                                  const State &state,
                                                  Resources &res,
                                                  float &r_aspect,
                                                  bool &r_use_alpha_premult,
                                                  bool &r_use_view_transform)
  {
    ::Image *image = bgpic->ima;
    ImageUser *iuser = (ImageUser *)&bgpic->iuser;
    MovieClip *clip = nullptr;
    GPUTexture *tex = nullptr;
    float aspect_x, aspect_y;
    int width, height;
    int ctime = int(DEG_get_ctime(state.depsgraph));
    r_use_alpha_premult = false;
    r_use_view_transform = false;

    switch (bgpic->source) {
      case CAM_BGIMG_SOURCE_IMAGE: {
        if (image == nullptr) {
          return nullptr;
        }
        r_use_alpha_premult = (image->alpha_mode == IMA_ALPHA_PREMUL);
        r_use_view_transform = (image->flag & IMA_VIEW_AS_RENDER) != 0;

        BKE_image_user_frame_calc(image, iuser, ctime);
        if (image->source == IMA_SRC_SEQUENCE && !(iuser->flag & IMA_USER_FRAME_IN_RANGE)) {
          /* Frame is out of range, don't show. */
          return nullptr;
        }

        Images::stereo_setup(state.scene, state.v3d, image, iuser);

        iuser->scene = (Scene *)state.scene;
        tex = BKE_image_get_gpu_viewer_texture(image, iuser);
        iuser->scene = nullptr;

        if (tex == nullptr) {
          return nullptr;
        }

        width = GPU_texture_original_width(tex);
        height = GPU_texture_original_height(tex);

        aspect_x = bgpic->ima->aspx;
        aspect_y = bgpic->ima->aspy;
        break;
      }

      case CAM_BGIMG_SOURCE_MOVIE: {
        if (bgpic->flag & CAM_BGIMG_FLAG_CAMERACLIP) {
          if (state.scene->camera) {
            clip = BKE_object_movieclip_get((Scene *)state.scene, state.scene->camera, true);
          }
        }
        else {
          clip = bgpic->clip;
        }

        if (clip == nullptr) {
          return nullptr;
        }

        BKE_movieclip_user_set_frame((MovieClipUser *)&bgpic->cuser, ctime);
        tex = BKE_movieclip_get_gpu_texture(clip, (MovieClipUser *)&bgpic->cuser);
        if (tex == nullptr) {
          return nullptr;
        }

        aspect_x = clip->aspx;
        aspect_y = clip->aspy;
        r_use_view_transform = true;

        BKE_movieclip_get_size(clip, &bgpic->cuser, &width, &height);

        /* Save for freeing. */
        res.bg_movie_clips.append(clip);
        break;
      }

      default:
        /* Unsupported type. */
        return nullptr;
    }

    r_aspect = (width * aspect_x) / (height * aspect_y);
    return tex;
  }
};

}  // namespace blender::draw::overlay
