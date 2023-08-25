/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup editors
 */

#pragma once

#include "BLI_sys_types.h"

/* ******************* Registration Function ********************** */

struct ARegion;
struct bContext;
struct Scene;
struct ReportList;
struct TransformOrientation;
struct Object;
struct RegionView3D;
struct View3D;
struct ViewLayer;
struct wmGizmoGroupType;
struct wmKeyConfig;
struct wmOperatorType;

void ED_keymap_transform(wmKeyConfig *keyconf);
void transform_operatortypes();

/* ******************** Macros & Prototypes *********************** */

/* MODE AND NUMINPUT FLAGS */
enum eTfmMode {
  TFM_INIT = -1,
  TFM_DUMMY,
  TFM_TRANSLATION,
  TFM_ROTATION,
  TFM_RESIZE,
  TFM_SKIN_RESIZE,
  TFM_TOSPHERE,
  TFM_SHEAR,
  TFM_BEND,
  TFM_SHRINKFATTEN,
  TFM_TILT,
  TFM_TRACKBALL,
  TFM_PUSHPULL,
  TFM_EDGE_CREASE,
  TFM_VERT_CREASE,
  TFM_MIRROR,
  TFM_BONESIZE,
  TFM_BONE_ENVELOPE,
  TFM_CURVE_SHRINKFATTEN,
  TFM_MASK_SHRINKFATTEN,
  TFM_GPENCIL_SHRINKFATTEN,
  TFM_BONE_ROLL,
  TFM_TIME_TRANSLATE,
  TFM_TIME_SLIDE,
  TFM_TIME_SCALE,
  TFM_TIME_EXTEND,
  /* TFM_TIME_DUPLICATE (deprecated). */
  TFM_BAKE_TIME = 26,
  TFM_DEPRECATED, /* was BEVEL */
  TFM_BWEIGHT,
  TFM_ALIGN,
  TFM_EDGE_SLIDE,
  TFM_VERT_SLIDE,
  TFM_SEQ_SLIDE,
  TFM_BONE_ENVELOPE_DIST,
  TFM_NORMAL_ROTATION,
  TFM_GPENCIL_OPACITY,
};

/* Standalone call to get the transformation center corresponding to the current situation
 * returns 1 if successful, 0 otherwise (usually means there's no selection)
 * (if false is returns, `cent3d` is unmodified). */
bool calculateTransformCenter(bContext *C, int centerMode, float cent3d[3], float cent2d[2]);

/* UNUSED */
// int BIF_snappingSupported(Object *obedit);

void BIF_clearTransformOrientation(bContext *C);
void BIF_removeTransformOrientation(bContext *C, TransformOrientation *target);
void BIF_removeTransformOrientationIndex(bContext *C, int index);
bool BIF_createTransformOrientation(bContext *C,
                                    ReportList *reports,
                                    const char *name,
                                    bool use_view,
                                    bool activate,
                                    bool overwrite);
void BIF_selectTransformOrientation(bContext *C, TransformOrientation *target);

void ED_getTransformOrientationMatrix(const Scene *scene,
                                      ViewLayer *view_layer,
                                      const View3D *v3d,
                                      Object *ob,
                                      Object *obedit,
                                      short around,
                                      float r_orientation_mat[3][3]);

int BIF_countTransformOrientation(const bContext *C);

/* to be able to add operator properties to other operators */

#define P_MIRROR (1 << 0)
#define P_MIRROR_DUMMY (P_MIRROR | (1 << 1))
#define P_PROPORTIONAL (1 << 2)
#define P_ORIENT_AXIS (1 << 3)
#define P_ORIENT_AXIS_ORTHO (1 << 4)
#define P_ORIENT_MATRIX (1 << 5)
#define P_SNAP (1 << 6)
#define P_GEO_SNAP (P_SNAP | (1 << 7))
#define P_ALIGN_SNAP (P_GEO_SNAP | (1 << 8))
#define P_CONSTRAINT (1 << 9)
#define P_OPTIONS (1 << 10)
#define P_CORRECT_UV (1 << 11)
#define P_NO_DEFAULTS (1 << 12)
#define P_NO_TEXSPACE (1 << 13)
#define P_CENTER (1 << 14)
#define P_GPENCIL_EDIT (1 << 15)
#define P_CURSOR_EDIT (1 << 16)
#define P_CLNOR_INVALIDATE (1 << 17)
#define P_VIEW2D_EDGE_PAN (1 << 18)
#define P_VIEW3D_ALT_NAVIGATION (1 << 19)
/* For properties performed when confirming the transformation. */
#define P_POST_TRANSFORM (1 << 20)

void Transform_Properties(wmOperatorType *ot, int flags);

/* `transform_orientations.cc` */
void ED_transform_calc_orientation_from_type(const bContext *C, float r_mat[3][3]);
/**
 * \note The resulting matrix may not be orthogonal,
 * callers that depend on `r_mat` to be orthogonal should use #orthogonalize_m3.
 *
 * A non orthogonal matrix may be returned when:
 * - #V3D_ORIENT_GIMBAL the result won't be orthogonal unless the object has no rotation.
 * - #V3D_ORIENT_LOCAL may contain shear from non-uniform scale in parent/child relationships.
 * - #V3D_ORIENT_CUSTOM may have been created from #V3D_ORIENT_LOCAL.
 */
short ED_transform_calc_orientation_from_type_ex(const Scene *scene,
                                                 ViewLayer *view_layer,
                                                 const View3D *v3d,
                                                 const RegionView3D *rv3d,
                                                 Object *ob,
                                                 Object *obedit,
                                                 short orientation_index,
                                                 int pivot_point,
                                                 float r_mat[3][3]);

bool ED_transform_calc_pivot_pos(const bContext *C, const short pivot_type, float r_pivot_pos[3]);

/* transform gizmos */

void VIEW3D_GGT_xform_gizmo(wmGizmoGroupType *gzgt);
/**
 * Only poll, flag & gzmap_params differ.
 */
void VIEW3D_GGT_xform_gizmo_context(wmGizmoGroupType *gzgt);
void VIEW3D_GGT_xform_cage(wmGizmoGroupType *gzgt);
void VIEW3D_GGT_xform_shear(wmGizmoGroupType *gzgt);

/* `transform_gizmo_extrude_3d.cc` */
void VIEW3D_GGT_xform_extrude(wmGizmoGroupType *gzgt);

/* Generic 2D transform gizmo callback assignment. */
void ED_widgetgroup_gizmo2d_xform_callbacks_set(wmGizmoGroupType *gzgt);
void ED_widgetgroup_gizmo2d_xform_no_cage_callbacks_set(wmGizmoGroupType *gzgt);
void ED_widgetgroup_gizmo2d_resize_callbacks_set(wmGizmoGroupType *gzgt);
void ED_widgetgroup_gizmo2d_rotate_callbacks_set(wmGizmoGroupType *gzgt);

#define SNAP_INCREMENTAL_ANGLE DEG2RAD(5.0)

struct TransformBounds {
  float center[3];      /* Center for transform widget. */
  float min[3], max[3]; /* Bounding-box of selection for transform widget. */

  /* Normalized axis */
  float axis[3][3];
  float axis_min[3], axis_max[3];

  /**
   * When #TransformCalcParams.use_local_axis is used.
   * This is the local space matrix the caller may need to access.
   */
  bool use_matrix_space;
  float matrix_space[4][4];
};

struct TransformCalcParams {
  uint use_only_center : 1;
  uint use_local_axis : 1;
  /* Use 'Scene.orientation_type' when zero, otherwise subtract one and use. */
  ushort orientation_index;
};
/**
 * Centroid, bound-box, of selection.
 *
 * Returns total items selected.
 */
int ED_transform_calc_gizmo_stats(const bContext *C,
                                  const TransformCalcParams *params,
                                  TransformBounds *tbounds,
                                  RegionView3D *rv3d);

/**
 * Iterates over all the strips and finds the closest snapping candidate of either \a frame_1 or \a
 * frame_2. The closest snapping candidate will be the closest start or end frame of an existing
 * strip.
 * \returns True if there was anything to snap to.
 */
bool ED_transform_snap_sequencer_to_closest_strip_calc(Scene *scene,
                                                       ARegion *region,
                                                       int frame_1,
                                                       int frame_2,
                                                       int *r_snap_distance,
                                                       float *r_snap_frame);

void ED_draw_sequencer_snap_point(struct ARegion *region, float snap_point);
