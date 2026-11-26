/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bke
 */

#pragma once

#include <cstdint>
#include <memory>

#include "BLI_enum_flags.hh"
#include "BLI_utility_mixins.hh"

namespace blender {
struct Depsgraph;
struct RegionView3D;
struct SmoothView3DStore;
struct ViewRender;
struct wmTimer;
enum eRegionView3D_ViewLock : char;

namespace nodes::eval_log {
class NodesEvalLog;
}  // namespace nodes::eval_log
}  // namespace blender

namespace blender::bke {

enum eRegionView3DTags : uint8_t {
  RV3D_TAG_NAVIGATING = 1 << 0,
  RV3D_TAG_GPULIGHT_UPDATE = 1 << 1,
  RV3D_TAG_PAINTING = 1 << 2,
};
ENUM_OPERATORS(eRegionView3DTags)

class RegionView3DRuntime : NonCopyable, NonMovable {
 public:
  RegionView3DRuntime();
  ~RegionView3DRuntime();

  /* A nodes log of the last viewport compositor evaluation. */
  std::unique_ptr<nodes::eval_log::NodesEvalLog> nodes_evaluation_log;

  /** Offset/scale for camera GLSL texture-coordinates. */
  float viewcamtexcofac[4] = {};

  /** viewmat/persmat multiplied with object matrix, while drawing and selection. */
  float viewmatob[4][4] = {};
  float persmatob[4][4] = {};

  /**
   * Clip in object space,
   * means we can test for clipping in edit-mode without first going into world-space.
   */
  float clip_local[6][4] = {};

  /** Transform gizmo matrix. */
  float twmat[4][4] = {};
  /** min/max dot product on `twmat` XYZ axis. */
  float tw_axis_min[3] = {}, tw_axis_max[3] = {};
  float tw_axis_matrix[3][3] = {};

  /** XXX can easily get rid of this (Julian). */
  short twdrawflag = 0;

  /* Should usually be accessed with bke::region_view3d_lock_flags_get()! */
  eRegionView3D_ViewLock viewlock = {};

  /** Active rotation from NDOF (run-time only). */
  float ndof_rot_angle = 0;
  float ndof_rot_axis[3] = {};

  ViewRender *view_render = nullptr;

  /** Animated smooth view. */
  SmoothView3DStore *sms = nullptr;
  wmTimer *smooth_timer = nullptr;

  eRegionView3DTags tags = {};

  /**
   * BFA - Auto Clipping: clipping range computed for this region before each redraw while
   * #V3D_AUTO_CLIP (or #CAM_AUTO_CLIP when looking through a camera) applies, see
   * `view3d_auto_clip.cc`. In the format of #View3D::clip_start and #View3D::clip_end, or of
   * the clipping of the camera in camera view. It is used instead of the range of the 3D view or
   * of the camera, which are never modified. Each region of a quad view has its own range.
   */
  float auto_clip_start = 0.0f;
  float auto_clip_end = 0.0f;
  bool auto_clip_valid = false;
  /**
   * The range is the one of the camera looked through (a valid range of the camera view), the
   * one the button of the camera can copy to its clipping. Always false when not valid.
   */
  bool auto_clip_camera_view = false;

  /**
   * BFA - Auto Clipping: world space bounds of the selected objects. They only change with a
   * depsgraph evaluation (selection, transform, edit...) or with what the 3D view shows, so they
   * are computed again only then: navigating reuses them.
   */
  struct AutoClipSelection {
    const Depsgraph *depsgraph = nullptr;
    uint64_t update_count = 0;
    /** What decides which objects are visible in the 3D view (local view, object types...). */
    uint32_t visibility_key[3] = {};
    bool cached = false;
    /** False when no visible object is selected. */
    bool has_bounds = false;
    float min[3] = {};
    float max[3] = {};
  } auto_clip_selection;

  /**
   * BFA - Auto Clipping, looking through a camera: depth range (distance along the view axis)
   * of what the camera sees. It depends on the camera, on its frustum and on the scene, so it is
   * computed again only when one of them changes. Heavy scenes are rate limited, see
   * `view3d_auto_clip.cc`.
   */
  struct AutoClipCamera {
    const Depsgraph *depsgraph = nullptr;
    uint64_t update_count = 0;
    uint32_t visibility_key[3] = {};
    /** Camera matrix (16) and frustum (8) the range was computed for. */
    float view_key[24] = {};
    /** Time (`BLI_time_now_seconds`) before which it is not computed again. */
    double next_update_time = 0.0;
    bool cached = false;
    /** False when no visible object is in the frustum. */
    bool has_range = false;
    /** Nearest and furthest depth, zero for the nearest when the camera is inside an object. */
    float near_depth = 0.0f;
    float far_depth = 0.0f;
  } auto_clip_camera;
};

/**
 * Get both the lock flags of the region view 3D and its runtime.
 */
eRegionView3D_ViewLock region_view3d_lock_flags_get(const RegionView3D *rv3d);

}  // namespace blender::bke
