/* SPDX-FileCopyrightText: 2008 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup eduv
 */

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

struct BMFace;
struct BMLoop;
struct Object;
struct Scene;
struct SpaceImage;
struct wmOperatorType;

/* find nearest */

typedef struct UvNearestHit {
  /** Only for `*_multi(..)` versions of functions. */
  struct Object *ob;
  /** Always set if we have a hit. */
  struct BMFace *efa;
  struct BMLoop *l;
  /**
   * Needs to be set before calling nearest functions.
   *
   * \note When #uv_nearest_hit_init_dist_px or #uv_nearest_hit_init_max are used,
   * this value is pixels squared.
   */
  float dist_sq;

  /** Scale the UVs to account for aspect ratio from the image view. */
  float scale[2];
} UvNearestHit;

UvNearestHit uv_nearest_hit_init_dist_px(const struct View2D *v2d, const float dist_px);
UvNearestHit uv_nearest_hit_init_max(const struct View2D *v2d);

bool uv_find_nearest_vert(struct Scene *scene,
                          struct Object *obedit,
                          const float co[2],
                          float penalty_dist,
                          struct UvNearestHit *hit);
bool uv_find_nearest_vert_multi(struct Scene *scene,
                                struct Object **objects,
                                uint objects_len,
                                const float co[2],
                                float penalty_dist,
                                struct UvNearestHit *hit);

bool uv_find_nearest_edge(struct Scene *scene,
                          struct Object *obedit,
                          const float co[2],
                          float penalty,
                          struct UvNearestHit *hit);
bool uv_find_nearest_edge_multi(struct Scene *scene,
                                struct Object **objects,
                                uint objects_len,
                                const float co[2],
                                float penalty,
                                struct UvNearestHit *hit);

/**
 * \param only_in_face: when true, only hit faces which `co` is inside.
 * This gives users a result they might expect, especially when zoomed in.
 *
 * \note Concave faces can cause odd behavior, although in practice this isn't often an issue.
 * The center can be outside the face, in this case the distance to the center
 * could cause the face to be considered too far away.
 * If this becomes an issue we could track the distance to the faces closest edge.
 */
bool uv_find_nearest_face_ex(struct Scene *scene,
                             struct Object *obedit,
                             const float co[2],
                             struct UvNearestHit *hit,
                             bool only_in_face);
bool uv_find_nearest_face(struct Scene *scene,
                          struct Object *obedit,
                          const float co[2],
                          struct UvNearestHit *hit);
bool uv_find_nearest_face_multi_ex(struct Scene *scene,
                                   struct Object **objects,
                                   uint objects_len,
                                   const float co[2],
                                   struct UvNearestHit *hit,
                                   bool only_in_face);
bool uv_find_nearest_face_multi(struct Scene *scene,
                                struct Object **objects,
                                uint objects_len,
                                const float co[2],
                                struct UvNearestHit *hit);

BMLoop *uv_find_nearest_loop_from_vert(struct Scene *scene,
                                       struct Object *obedit,
                                       struct BMVert *v,
                                       const float co[2]);
BMLoop *uv_find_nearest_loop_from_edge(struct Scene *scene,
                                       struct Object *obedit,
                                       struct BMEdge *e,
                                       const float co[2]);

bool uvedit_vert_is_edge_select_any_other(const struct Scene *scene,
                                          struct BMLoop *l,
                                          BMUVOffsets offsets);
bool uvedit_vert_is_face_select_any_other(const struct Scene *scene,
                                          struct BMLoop *l,
                                          BMUVOffsets offsets);
bool uvedit_vert_is_all_other_faces_selected(const struct Scene *scene,
                                             struct BMLoop *l,
                                             BMUVOffsets offsets);

/* utility tool functions */

void uvedit_live_unwrap_update(struct SpaceImage *sima,
                               struct Scene *scene,
                               struct Object *obedit);

/* operators */

void UV_OT_average_islands_scale(struct wmOperatorType *ot);
void UV_OT_cube_project(struct wmOperatorType *ot);
void UV_OT_cylinder_project(struct wmOperatorType *ot);
void UV_OT_project_from_view(struct wmOperatorType *ot);
void UV_OT_minimize_stretch(struct wmOperatorType *ot);
void UV_OT_pack_islands(struct wmOperatorType *ot);
void UV_OT_reset(struct wmOperatorType *ot);
void UV_OT_sphere_project(struct wmOperatorType *ot);
void UV_OT_unwrap(struct wmOperatorType *ot);
void UV_OT_rip(struct wmOperatorType *ot);
void UV_OT_stitch(struct wmOperatorType *ot);
void UV_OT_smart_project(struct wmOperatorType *ot);

/* uvedit_copy_paste.cc */
void UV_OT_copy(wmOperatorType *ot);
void UV_OT_paste(wmOperatorType *ot);

/* `uvedit_path.cc` */

void UV_OT_shortest_path_pick(struct wmOperatorType *ot);
void UV_OT_shortest_path_select(struct wmOperatorType *ot);

/* `uvedit_select.cc` */

bool uvedit_select_is_any_selected(const struct Scene *scene, struct Object *obedit);
bool uvedit_select_is_any_selected_multi(const struct Scene *scene,
                                         struct Object **objects,
                                         uint objects_len);
/**
 * \warning This returns first selected UV,
 * not ideal in many cases since there could be multiple.
 */
const float *uvedit_first_selected_uv_from_vertex(struct Scene *scene,
                                                  struct BMVert *eve,
                                                  BMUVOffsets offsets);

void UV_OT_select_all(struct wmOperatorType *ot);
void UV_OT_select(struct wmOperatorType *ot);
void UV_OT_select_loop(struct wmOperatorType *ot);
void UV_OT_select_edge_ring(struct wmOperatorType *ot);
void UV_OT_select_linked(struct wmOperatorType *ot);
void UV_OT_select_linked_pick(struct wmOperatorType *ot);
void UV_OT_select_split(struct wmOperatorType *ot);
void UV_OT_select_pinned(struct wmOperatorType *ot);
void UV_OT_select_box(struct wmOperatorType *ot);
void UV_OT_select_lasso(struct wmOperatorType *ot);
void UV_OT_select_circle(struct wmOperatorType *ot);
void UV_OT_select_more(struct wmOperatorType *ot);
void UV_OT_select_less(struct wmOperatorType *ot);
void UV_OT_select_overlap(struct wmOperatorType *ot);
void UV_OT_select_similar(struct wmOperatorType *ot);
/* Used only when UV sync select is disabled. */
void UV_OT_select_mode(struct wmOperatorType *ot);

#ifdef __cplusplus
}
#endif
