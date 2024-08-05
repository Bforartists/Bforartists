/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup overlay
 */

#pragma once

#include "DNA_lightprobe_types.h"

#include "overlay_next_private.hh"

namespace blender::draw::overlay {

class LightProbes {
  using LightProbeInstanceBuf = ShapeInstanceBuf<ExtraInstanceData>;
  using GroundLineInstanceBuf = ShapeInstanceBuf<float4>;
  using DotsInstanceBuf = ShapeInstanceBuf<float4x4>;

 private:
  const SelectionType selection_type_;

  PassSimple ps_ = {"LightProbes"};
  PassMain ps_dots_ = {"LightProbesDots"};

  struct CallBuffers {
    const SelectionType selection_type_;

    GroundLineInstanceBuf ground_line_buf = {selection_type_, "ground_line_buf"};
    LightProbeInstanceBuf probe_cube_buf = {selection_type_, "probe_cube_buf"};
    LightProbeInstanceBuf probe_planar_buf = {selection_type_, "probe_planar_buf"};
    LightProbeInstanceBuf probe_grid_buf = {selection_type_, "probe_grid_buf"};
    LightProbeInstanceBuf quad_solid_buf = {selection_type_, "quad_solid_buf"};
    LightProbeInstanceBuf cube_buf = {selection_type_, "cube_buf"};
    LightProbeInstanceBuf sphere_buf = {selection_type_, "sphere_buf"};
    LightProbeInstanceBuf single_arrow_buf = {selection_type_, "single_arrow_buf"};

  } call_buffers_{selection_type_};

 public:
  LightProbes(const SelectionType selection_type) : selection_type_(selection_type){};

  void begin_sync(Resources &res, const State &state)
  {
    call_buffers_.ground_line_buf.clear();
    call_buffers_.probe_cube_buf.clear();
    call_buffers_.probe_planar_buf.clear();
    call_buffers_.probe_grid_buf.clear();
    call_buffers_.quad_solid_buf.clear();
    call_buffers_.cube_buf.clear();
    call_buffers_.sphere_buf.clear();
    call_buffers_.single_arrow_buf.clear();

    ps_dots_.init();
    ps_dots_.state_set(DRW_STATE_WRITE_COLOR | state.clipping_state);
    ps_dots_.shader_set(res.shaders.extra_grid.get());
    ps_dots_.bind_ubo("globalsBlock", &res.globals_buf);
    ps_dots_.bind_texture("depthBuffer", &res.depth_tx);
    ps_dots_.push_constant("isTransform", (G.moving & G_TRANSFORM_OBJ) != 0);
    res.select_bind(ps_dots_);
  }

  void object_sync(const ObjectRef &ob_ref, Resources &res, const State &state)
  {
    const Object *ob = ob_ref.object;
    const LightProbe *prb = static_cast<LightProbe *>(ob_ref.object->data);
    const bool show_clipping = (prb->flag & LIGHTPROBE_FLAG_SHOW_CLIP_DIST) != 0;
    const bool show_parallax = (prb->flag & LIGHTPROBE_FLAG_SHOW_PARALLAX) != 0;
    const bool show_influence = (prb->flag & LIGHTPROBE_FLAG_SHOW_INFLUENCE) != 0;
    const bool is_select = selection_type_ == SelectionType::ENABLED;
    const bool show_data = (ob_ref.object->base_flag & BASE_SELECTED) || is_select;

    const select::ID select_id = res.select_id(ob_ref);
    const float4 color = res.object_wire_color(ob_ref, state);
    ExtraInstanceData data(ob->object_to_world(), color, 1.0f);
    float4x4 &matrix = data.object_to_world_;
    float &clip_start = matrix[2].w;
    float &clip_end = matrix[3].w;
    float &draw_size = matrix[3].w;

    switch (prb->type) {
      case LIGHTPROBE_TYPE_SPHERE:
        clip_start = show_clipping ? prb->clipsta : -1.0;
        clip_end = show_clipping ? prb->clipend : -1.0;
        call_buffers_.probe_cube_buf.append(data, select_id);

        call_buffers_.ground_line_buf.append(float4(matrix.location()), select_id);

        if (show_influence) {
          LightProbeInstanceBuf &attenuation = (prb->attenuation_type == LIGHTPROBE_SHAPE_BOX) ?
                                                   call_buffers_.cube_buf :
                                                   call_buffers_.sphere_buf;
          const float f = 1.0f - prb->falloff;
          ExtraInstanceData data(ob->object_to_world(), color, prb->distinf);
          attenuation.append(data, select_id);
          data.object_to_world_[3].w = prb->distinf * f;
          attenuation.append(data, select_id);
        }

        if (show_parallax) {
          LightProbeInstanceBuf &parallax = (prb->parallax_type == LIGHTPROBE_SHAPE_BOX) ?
                                                call_buffers_.cube_buf :
                                                call_buffers_.sphere_buf;
          const float dist = ((prb->flag & LIGHTPROBE_FLAG_CUSTOM_PARALLAX) != 0) ? prb->distpar :
                                                                                    prb->distinf;
          parallax.append(ExtraInstanceData(ob->object_to_world(), color, dist), select_id);
        }
        break;
      case LIGHTPROBE_TYPE_VOLUME: {
        clip_start = show_clipping ? 0.0f : -1.0f;
        clip_end = show_clipping ? prb->clipend : -1.0f;
        call_buffers_.probe_grid_buf.append(data, select_id);
        {
          /* Display surfel density as a cube. */
          float3 axes_len = math::to_scale(ob->object_to_world());
          float max_axis_len = math::reduce_max(axes_len);
          float3 local_surfel_size = (0.5f / prb->grid_surfel_density) * (max_axis_len / axes_len);

          float4x4 surfel_density_mat = math::from_loc_rot_scale<float4x4>(
              float3(-1.0f + local_surfel_size),
              math::Quaternion::identity(),
              float3(local_surfel_size));
          surfel_density_mat = ob->object_to_world() * surfel_density_mat;
          call_buffers_.cube_buf.append(ExtraInstanceData(surfel_density_mat, color, 1.0f),
                                        select_id);
        }

        if (show_influence) {
          call_buffers_.cube_buf.append(ExtraInstanceData(ob->object_to_world(), color, 1.0f),
                                        select_id);
        }

        /* Data dots */
        if (show_data) {
          matrix[0].w = prb->grid_resolution_x;
          matrix[1].w = prb->grid_resolution_y;
          matrix[2].w = prb->grid_resolution_z;
          /* Put theme id in matrix. */
          matrix[3].w = res.object_wire_theme_id(ob_ref, state) == TH_ACTIVE ? 1.0f : 2.0f;

          const uint cell_count = prb->grid_resolution_x * prb->grid_resolution_y *
                                  prb->grid_resolution_z;
          ps_dots_.push_constant("gridModelMatrix", matrix);
          ps_dots_.draw_procedural(GPU_PRIM_POINTS, 1, cell_count, 0, {0}, select_id.get());
        }
        break;
      }
      case LIGHTPROBE_TYPE_PLANE:
        call_buffers_.probe_planar_buf.append(data, select_id);

        if (is_select && (prb->flag & LIGHTPROBE_FLAG_SHOW_DATA)) {
          call_buffers_.quad_solid_buf.append(data, select_id);
        }

        if (show_influence) {
          matrix.z_axis() = math::normalize(matrix.z_axis()) * prb->distinf;
          call_buffers_.cube_buf.append(data, select_id);
          matrix.z_axis() *= 1.0f - prb->falloff;
          call_buffers_.cube_buf.append(data, select_id);
        }

        matrix.z_axis() = float3(0);
        call_buffers_.cube_buf.append(data, select_id);

        matrix.view<3, 3>() = math::normalize(float4x4(ob->object_to_world().ptr()).view<3, 3>());
        draw_size = ob->empty_drawsize;
        call_buffers_.single_arrow_buf.append(data, select_id);
        break;
    }
  }

  void end_sync(Resources &res, ShapeCache &shapes, const State &state)
  {
    ps_.init();
    res.select_bind(ps_);

    DRWState pass_state = DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH |
                          DRW_STATE_DEPTH_LESS_EQUAL | state.clipping_state;
    {
      PassSimple::Sub &sub_pass = ps_.sub("empties");
      sub_pass.state_set(pass_state);
      sub_pass.shader_set(res.shaders.extra_shape.get());
      sub_pass.bind_ubo("globalsBlock", &res.globals_buf);
      call_buffers_.probe_cube_buf.end_sync(sub_pass, shapes.lightprobe_cube.get());
      call_buffers_.probe_planar_buf.end_sync(sub_pass, shapes.lightprobe_planar.get());
      call_buffers_.probe_grid_buf.end_sync(sub_pass, shapes.lightprobe_grid.get());
      call_buffers_.quad_solid_buf.end_sync(sub_pass, shapes.quad_solid.get());
      call_buffers_.cube_buf.end_sync(sub_pass, shapes.cube.get());
      call_buffers_.sphere_buf.end_sync(sub_pass, shapes.empty_sphere.get());
      call_buffers_.single_arrow_buf.end_sync(sub_pass, shapes.single_arrow.get());
    }
    {
      PassSimple::Sub &sub_pass = ps_.sub("ground_line");
      sub_pass.state_set(pass_state | DRW_STATE_BLEND_ALPHA);
      sub_pass.shader_set(res.shaders.extra_ground_line.get());
      sub_pass.bind_ubo("globalsBlock", &res.globals_buf);
      call_buffers_.ground_line_buf.end_sync(sub_pass, shapes.ground_line.get());
    }
  }

  void draw(Framebuffer &framebuffer, Manager &manager, View &view)
  {
    GPU_framebuffer_bind(framebuffer);
    manager.submit(ps_, view);
    manager.submit(ps_dots_, view);
  }
};

}  // namespace blender::draw::overlay
