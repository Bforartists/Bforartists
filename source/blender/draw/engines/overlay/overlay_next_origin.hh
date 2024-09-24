/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup overlay
 */

#pragma once

#include "overlay_next_private.hh"

namespace blender::draw::overlay {
class Origins {
 private:
  StorageVectorBuffer<VertexData> point_buf_;

  PassSimple ps_ = {"Origins"};

  bool enabled_ = false;

 public:
  void begin_sync(const State &state)
  {
    const bool is_paint_mode = (state.object_mode &
                                (OB_MODE_ALL_PAINT | OB_MODE_ALL_PAINT_GPENCIL |
                                 OB_MODE_SCULPT_CURVES)) != 0;
    enabled_ = state.v3d && !is_paint_mode &&
               (state.overlay.flag & V3D_OVERLAY_HIDE_OBJECT_ORIGINS) == 0;
    point_buf_.clear();
  }

  void object_sync(const ObjectRef &ob_ref, Resources &res, State &state)
  {
    if (!enabled_) {
      return;
    }
    const Object *ob = ob_ref.object;
    const bool is_library = ID_REAL_USERS(&ob->id) > 1 || ID_IS_LINKED(ob);
    BKE_view_layer_synced_ensure(state.scene, (ViewLayer *)state.view_layer);
    const float4 location = float4(ob->object_to_world().location());

    if (ob == BKE_view_layer_active_object_get(state.view_layer)) {
      point_buf_.append(VertexData{location, res.theme_settings.color_active});
    }
    else if (ob->base_flag & BASE_SELECTED) {
      point_buf_.append(VertexData{location,
                                   is_library ? res.theme_settings.color_library_select :
                                                res.theme_settings.color_select});
    }
    else if (state.v3d_flag & V3D_DRAW_CENTERS) {
      point_buf_.append(VertexData{location,
                                   is_library ? res.theme_settings.color_library :
                                                res.theme_settings.color_deselect});
    }
  }

  void end_sync(Resources &res, const State &state)
  {
    if (!enabled_) {
      return;
    }
    ps_.init();
    ps_.state_set(DRW_STATE_WRITE_COLOR | DRW_STATE_BLEND_ALPHA, state.clipping_plane_count);
    ps_.shader_set(res.shaders.extra_point.get());
    ps_.bind_ubo("globalsBlock", &res.globals_buf);
    point_buf_.push_update();
    ps_.bind_ssbo("data_buf", &point_buf_);
    ps_.draw_procedural(GPU_PRIM_POINTS, 1, point_buf_.size());
  }

  void draw(Framebuffer &framebuffer, Manager &manager, View &view)
  {
    if (!enabled_) {
      return;
    }

    GPU_framebuffer_bind(framebuffer);
    manager.submit(ps_, view);
  }
};
}  // namespace blender::draw::overlay
