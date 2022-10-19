/* SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup eduv
 *
 * Utilities for manipulating UV islands.
 *
 * \note This is similar to `GEO_uv_parametrizer.h`,
 * however the data structures there don't support arbitrary topology
 * such as an edge with 3 or more faces using it.
 * This API uses #BMesh data structures and doesn't have limitations for manifold meshes.
 */

#include "MEM_guardedalloc.h"

#include "DNA_meshdata_types.h"
#include "DNA_scene_types.h"
#include "DNA_space_types.h"

#include "BLI_boxpack_2d.h"
#include "BLI_convexhull_2d.h"
#include "BLI_listbase.h"
#include "BLI_math.h"
#include "BLI_rect.h"

#include "BKE_customdata.h"
#include "BKE_editmesh.h"
#include "BKE_image.h"

#include "DEG_depsgraph.h"

#include "ED_uvedit.h" /* Own include. */

#include "WM_api.h"
#include "WM_types.h"

#include "bmesh.h"

/* -------------------------------------------------------------------- */
/** \name UV Face Utilities
 * \{ */

static void bm_face_uv_translate_and_scale_around_pivot(BMFace *f,
                                                        const float offset[2],
                                                        const float scale[2],
                                                        const float pivot[2],
                                                        const int cd_loop_uv_offset)
{
  BMLoop *l_iter;
  BMLoop *l_first;
  l_iter = l_first = BM_FACE_FIRST_LOOP(f);
  do {
    MLoopUV *luv = static_cast<MLoopUV *>(BM_ELEM_CD_GET_VOID_P(l_iter, cd_loop_uv_offset));
    for (int i = 0; i < 2; i++) {
      luv->uv[i] = offset[i] + (((luv->uv[i] - pivot[i]) * scale[i]) + pivot[i]);
    }
  } while ((l_iter = l_iter->next) != l_first);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name UV Face Array Utilities
 * \{ */

static void bm_face_array_calc_bounds(BMFace **faces,
                                      const int faces_len,
                                      const int cd_loop_uv_offset,
                                      rctf *r_bounds_rect)
{
  BLI_assert(cd_loop_uv_offset >= 0);
  float bounds_min[2], bounds_max[2];
  INIT_MINMAX2(bounds_min, bounds_max);
  for (int i = 0; i < faces_len; i++) {
    BMFace *f = faces[i];
    BM_face_uv_minmax(f, bounds_min, bounds_max, cd_loop_uv_offset);
  }
  r_bounds_rect->xmin = bounds_min[0];
  r_bounds_rect->ymin = bounds_min[1];
  r_bounds_rect->xmax = bounds_max[0];
  r_bounds_rect->ymax = bounds_max[1];
}

/**
 * Return an array of un-ordered UV coordinates,
 * without duplicating coordinates for loops that share a vertex.
 */
static float (*bm_face_array_calc_unique_uv_coords(
    BMFace **faces, int faces_len, const int cd_loop_uv_offset, int *r_coords_len))[2]
{
  BLI_assert(cd_loop_uv_offset >= 0);
  int coords_len_alloc = 0;
  for (int i = 0; i < faces_len; i++) {
    BMFace *f = faces[i];
    BMLoop *l_iter, *l_first;
    l_iter = l_first = BM_FACE_FIRST_LOOP(f);
    do {
      BM_elem_flag_enable(l_iter, BM_ELEM_TAG);
    } while ((l_iter = l_iter->next) != l_first);
    coords_len_alloc += f->len;
  }

  float(*coords)[2] = static_cast<float(*)[2]>(
      MEM_mallocN(sizeof(*coords) * coords_len_alloc, __func__));
  int coords_len = 0;

  for (int i = 0; i < faces_len; i++) {
    BMFace *f = faces[i];
    BMLoop *l_iter, *l_first;
    l_iter = l_first = BM_FACE_FIRST_LOOP(f);
    do {
      if (!BM_elem_flag_test(l_iter, BM_ELEM_TAG)) {
        /* Already walked over, continue. */
        continue;
      }

      BM_elem_flag_disable(l_iter, BM_ELEM_TAG);
      const MLoopUV *luv = static_cast<const MLoopUV *>(
          BM_ELEM_CD_GET_VOID_P(l_iter, cd_loop_uv_offset));
      copy_v2_v2(coords[coords_len++], luv->uv);

      /* Un tag all connected so we don't add them twice.
       * Note that we will tag other loops not part of `faces` but this is harmless,
       * since we're only turning off a tag. */
      BMVert *v_pivot = l_iter->v;
      BMEdge *e_first = v_pivot->e;
      const BMEdge *e = e_first;
      do {
        if (e->l != nullptr) {
          const BMLoop *l_radial = e->l;
          do {
            if (l_radial->v == l_iter->v) {
              if (BM_elem_flag_test(l_radial, BM_ELEM_TAG)) {
                const MLoopUV *luv_radial = static_cast<const MLoopUV *>(
                    BM_ELEM_CD_GET_VOID_P(l_radial, cd_loop_uv_offset));
                if (equals_v2v2(luv->uv, luv_radial->uv)) {
                  /* Don't add this UV when met in another face in `faces`. */
                  BM_elem_flag_disable(l_iter, BM_ELEM_TAG);
                }
              }
            }
          } while ((l_radial = l_radial->radial_next) != e->l);
        }
      } while ((e = BM_DISK_EDGE_NEXT(e, v_pivot)) != e_first);
    } while ((l_iter = l_iter->next) != l_first);
  }
  *r_coords_len = coords_len;
  return coords;
}

static void face_island_uv_rotate_fit_aabb(FaceIsland *island)
{
  BMFace **faces = island->faces;
  const int faces_len = island->faces_len;
  const float aspect_y = island->aspect_y;
  const int cd_loop_uv_offset = island->cd_loop_uv_offset;

  /* Calculate unique coordinates since calculating a convex hull can be an expensive operation. */
  int coords_len;
  float(*coords)[2] = bm_face_array_calc_unique_uv_coords(
      faces, faces_len, cd_loop_uv_offset, &coords_len);

  /* Correct aspect ratio. */
  if (aspect_y != 1.0f) {
    for (int i = 0; i < coords_len; i++) {
      coords[i][1] /= aspect_y;
    }
  }

  float angle = BLI_convexhull_aabb_fit_points_2d(coords, coords_len);

  /* Rotate coords by `angle` before computing bounding box. */
  if (angle != 0.0f) {
    float matrix[2][2];
    angle_to_mat2(matrix, angle);
    matrix[0][1] *= aspect_y;
    matrix[1][1] *= aspect_y;
    for (int i = 0; i < coords_len; i++) {
      mul_m2_v2(matrix, coords[i]);
    }
  }

  /* Compute new AABB. */
  float bounds_min[2], bounds_max[2];
  INIT_MINMAX2(bounds_min, bounds_max);
  for (int i = 0; i < coords_len; i++) {
    minmax_v2v2_v2(bounds_min, bounds_max, coords[i]);
  }

  float size[2];
  sub_v2_v2v2(size, bounds_max, bounds_min);
  if (size[1] < size[0]) {
    angle += DEG2RADF(90.0f);
  }

  MEM_freeN(coords);

  /* Apply rotation back to BMesh. */
  if (angle != 0.0f) {
    float matrix[2][2];
    angle_to_mat2(matrix, angle);
    matrix[1][0] *= 1.0f / aspect_y;
    /* matrix[1][1] *= aspect_y / aspect_y; */
    matrix[0][1] *= aspect_y;
    for (int i = 0; i < faces_len; i++) {
      BM_face_uv_transform(faces[i], matrix, cd_loop_uv_offset);
    }
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name UDIM packing helper functions
 * \{ */

bool uv_coords_isect_udim(const Image *image, const int udim_grid[2], const float coords[2])
{
  const float coords_floor[2] = {floorf(coords[0]), floorf(coords[1])};
  const bool is_tiled_image = image && (image->source == IMA_SRC_TILED);

  if (coords[0] < udim_grid[0] && coords[0] > 0 && coords[1] < udim_grid[1] && coords[1] > 0) {
    return true;
  }
  /* Check if selection lies on a valid UDIM image tile. */
  if (is_tiled_image) {
    LISTBASE_FOREACH (const ImageTile *, tile, &image->tiles) {
      const int tile_index = tile->tile_number - 1001;
      const int target_x = (tile_index % 10);
      const int target_y = (tile_index / 10);
      if (coords_floor[0] == target_x && coords_floor[1] == target_y) {
        return true;
      }
    }
  }
  /* Probably not required since UDIM grid checks for 1001. */
  else if (image && !is_tiled_image) {
    if (is_zero_v2(coords_floor)) {
      return true;
    }
  }

  return false;
}

/**
 * Calculates distance to nearest UDIM image tile in UV space and its UDIM tile number.
 */
static float uv_nearest_image_tile_distance(const Image *image,
                                            const float coords[2],
                                            float nearest_tile_co[2])
{
  BKE_image_find_nearest_tile_with_offset(image, coords, nearest_tile_co);

  /* Add 0.5 to get tile center coordinates. */
  float nearest_tile_center_co[2] = {nearest_tile_co[0], nearest_tile_co[1]};
  add_v2_fl(nearest_tile_center_co, 0.5f);

  return len_squared_v2v2(coords, nearest_tile_center_co);
}

/**
 * Calculates distance to nearest UDIM grid tile in UV space and its UDIM tile number.
 */
static float uv_nearest_grid_tile_distance(const int udim_grid[2],
                                           const float coords[2],
                                           float nearest_tile_co[2])
{
  const float coords_floor[2] = {floorf(coords[0]), floorf(coords[1])};

  if (coords[0] > udim_grid[0]) {
    nearest_tile_co[0] = udim_grid[0] - 1;
  }
  else if (coords[0] < 0) {
    nearest_tile_co[0] = 0;
  }
  else {
    nearest_tile_co[0] = coords_floor[0];
  }

  if (coords[1] > udim_grid[1]) {
    nearest_tile_co[1] = udim_grid[1] - 1;
  }
  else if (coords[1] < 0) {
    nearest_tile_co[1] = 0;
  }
  else {
    nearest_tile_co[1] = coords_floor[1];
  }

  /* Add 0.5 to get tile center coordinates. */
  float nearest_tile_center_co[2] = {nearest_tile_co[0], nearest_tile_co[1]};
  add_v2_fl(nearest_tile_center_co, 0.5f);

  return len_squared_v2v2(coords, nearest_tile_center_co);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Calculate UV Islands
 * \{ */

struct SharedUVLoopData {
  int cd_loop_uv_offset;
  bool use_seams;
};

static bool bm_loop_uv_shared_edge_check(const BMLoop *l_a, const BMLoop *l_b, void *user_data)
{
  const struct SharedUVLoopData *data = static_cast<const struct SharedUVLoopData *>(user_data);

  if (data->use_seams) {
    if (BM_elem_flag_test(l_a->e, BM_ELEM_SEAM)) {
      return false;
    }
  }

  return BM_loop_uv_share_edge_check((BMLoop *)l_a, (BMLoop *)l_b, data->cd_loop_uv_offset);
}

/**
 * Calculate islands and add them to \a island_list returning the number of items added.
 */
int bm_mesh_calc_uv_islands(const Scene *scene,
                            BMesh *bm,
                            ListBase *island_list,
                            const bool only_selected_faces,
                            const bool only_selected_uvs,
                            const bool use_seams,
                            const float aspect_y,
                            const int cd_loop_uv_offset)
{
  BLI_assert(cd_loop_uv_offset >= 0);
  int island_added = 0;
  BM_mesh_elem_table_ensure(bm, BM_FACE);

  int *groups_array = static_cast<int *>(
      MEM_mallocN(sizeof(*groups_array) * size_t(bm->totface), __func__));

  int(*group_index)[2];

  /* Calculate the tag to use. */
  uchar hflag_face_test = 0;
  if (only_selected_faces) {
    if (only_selected_uvs) {
      BMFace *f;
      BMIter iter;
      BM_ITER_MESH (f, &iter, bm, BM_FACES_OF_MESH) {
        bool value = false;
        if (BM_elem_flag_test(f, BM_ELEM_SELECT) &&
            uvedit_face_select_test(scene, f, cd_loop_uv_offset)) {
          value = true;
        }
        BM_elem_flag_set(f, BM_ELEM_TAG, value);
      }
      hflag_face_test = BM_ELEM_TAG;
    }
    else {
      hflag_face_test = BM_ELEM_SELECT;
    }
  }

  struct SharedUVLoopData user_data = {0};
  user_data.cd_loop_uv_offset = cd_loop_uv_offset;
  user_data.use_seams = use_seams;

  const int group_len = BM_mesh_calc_face_groups(bm,
                                                 groups_array,
                                                 &group_index,
                                                 nullptr,
                                                 bm_loop_uv_shared_edge_check,
                                                 &user_data,
                                                 hflag_face_test,
                                                 BM_EDGE);

  for (int i = 0; i < group_len; i++) {
    const int faces_start = group_index[i][0];
    const int faces_len = group_index[i][1];
    BMFace **faces = static_cast<BMFace **>(MEM_mallocN(sizeof(*faces) * faces_len, __func__));

    float bounds_min[2], bounds_max[2];
    INIT_MINMAX2(bounds_min, bounds_max);

    for (int j = 0; j < faces_len; j++) {
      faces[j] = BM_face_at_index(bm, groups_array[faces_start + j]);
    }

    struct FaceIsland *island = static_cast<struct FaceIsland *>(
        MEM_callocN(sizeof(*island), __func__));
    island->faces = faces;
    island->faces_len = faces_len;
    island->cd_loop_uv_offset = cd_loop_uv_offset;
    island->aspect_y = aspect_y;
    BLI_addtail(island_list, island);
    island_added += 1;
  }

  MEM_freeN(groups_array);
  MEM_freeN(group_index);
  return island_added;
}

/** \} */

static float pack_islands_scale_margin(const blender::Vector<FaceIsland *> &island_vector,
                                       BoxPack *box_array,
                                       const float scale,
                                       const float margin)
{
  for (const int index : island_vector.index_range()) {
    FaceIsland *island = island_vector[index];
    BoxPack *box = &box_array[index];
    box->index = index;
    box->w = BLI_rctf_size_x(&island->bounds_rect) * scale + 2 * margin;
    box->h = BLI_rctf_size_y(&island->bounds_rect) * scale + 2 * margin;
  }
  float max_u, max_v;
  BLI_box_pack_2d(box_array, island_vector.size(), &max_u, &max_v);
  return max_ff(max_u, max_v);
}

static float pack_islands_margin_fraction(const blender::Vector<FaceIsland *> &island_vector,
                                          BoxPack *box_array,
                                          const float margin_fraction)
{
  /*
   * Root finding using a combined search / modified-secant method.
   * First, use a robust search procedure to bracket the root within a factor of 10.
   * Then, use a modified-secant method to converge.
   *
   * This is a specialized solver using domain knowledge to accelerate convergence.
   */

  float scale_low = 0.0f;
  float value_low = 0.0f;
  float scale_high = 0.0f;
  float value_high = 0.0f;
  float scale_last = 0.0f;

  /* Scaling smaller than `min_scale_roundoff` is unlikely to fit and
   * will destroy information in existing UVs. */
  float min_scale_roundoff = 1e-5f;

  /* Certain inputs might have poor convergence properties.
   * Use `max_iteration` to prevent an infinite loop. */
  int max_iteration = 25;
  for (int iteration = 0; iteration < max_iteration; iteration++) {
    float scale = 1.0f;

    if (iteration == 0) {
      BLI_assert(iteration == 0);
      BLI_assert(scale == 1.0f);
      BLI_assert(scale_low == 0.0f);
      BLI_assert(scale_high == 0.0f);
    }
    else if (scale_low == 0.0f) {
      BLI_assert(scale_high > 0.0f);
      /* Search mode, shrink layout until we can find a scale that fits. */
      scale = scale_high * 0.1f;
    }
    else if (scale_high == 0.0f) {
      BLI_assert(scale_low > 0.0f);
      /* Search mode, grow layout until we can find a scale that doesn't fit. */
      scale = scale_low * 10.0f;
    }
    else {
      /* Bracket mode, use modified secant method to find root. */
      BLI_assert(scale_low > 0.0f);
      BLI_assert(scale_high > 0.0f);
      BLI_assert(value_low <= 0.0f);
      BLI_assert(value_high >= 0.0f);
      if (scale_high < scale_low * 1.0001f) {
        /* Convergence. */
        break;
      }

      /* Secant method for area. */
      scale = (sqrtf(scale_low) * value_high - sqrtf(scale_high) * value_low) /
              (value_high - value_low);
      scale = scale * scale;

      if (iteration & 1) {
        /* Modified binary-search to improve robustness. */
        scale = sqrtf(scale * sqrtf(scale_low * scale_high));
      }
    }

    scale = max_ff(scale, min_scale_roundoff);

    /* Evaluate our `f`. */
    scale_last = scale;
    float max_uv = pack_islands_scale_margin(
        island_vector, box_array, scale_last, margin_fraction);
    float value = sqrtf(max_uv) - 1.0f;

    if (value <= 0.0f) {
      scale_low = scale;
      value_low = value;
    }
    else {
      scale_high = scale;
      value_high = value;
      if (scale == min_scale_roundoff) {
        /* Unable to pack without damaging UVs. */
        scale_low = scale;
        break;
      }
    }
  }

  const bool flush = true;
  if (flush) {
    /* Write back best pack as a side-effect. First get best pack. */
    if (scale_last != scale_low) {
      scale_last = scale_low;
      float max_uv = pack_islands_scale_margin(
          island_vector, box_array, scale_last, margin_fraction);
      UNUSED_VARS(max_uv);
      /* TODO (?): `if (max_uv < 1.0f) { scale_last /= max_uv; }` */
    }

    /* Then expand FaceIslands by the correct amount. */
    for (const int index : island_vector.index_range()) {
      BoxPack *box = &box_array[index];
      box->x /= scale_last;
      box->y /= scale_last;
      FaceIsland *island = island_vector[index];
      BLI_rctf_pad(
          &island->bounds_rect, margin_fraction / scale_last, margin_fraction / scale_last);
    }
  }
  return scale_last;
}

static float calc_margin_from_aabb_length_sum(const blender::Vector<FaceIsland *> &island_vector,
                                              const struct UVPackIsland_Params &params)
{
  /* Logic matches behavior from #GEO_uv_parametrizer_pack.
   * Attempt to give predictable results
   * not dependent on current UV scale by using
   * `aabb_length_sum` (was "`area`") to multiply
   * the margin by the length (was "area").
   */
  double aabb_length_sum = 0.0f;
  for (FaceIsland *island : island_vector) {
    float w = BLI_rctf_size_x(&island->bounds_rect);
    float h = BLI_rctf_size_y(&island->bounds_rect);
    aabb_length_sum += sqrtf(w * h);
  }
  return params.margin * aabb_length_sum * 0.1f;
}

static BoxPack *pack_islands_params(const blender::Vector<FaceIsland *> &island_vector,
                                    const struct UVPackIsland_Params &params,
                                    float r_scale[2])
{
  BoxPack *box_array = static_cast<BoxPack *>(
      MEM_mallocN(sizeof(*box_array) * island_vector.size(), __func__));

  if (params.margin == 0.0f) {
    /* Special case for zero margin. Margin_method is ignored as all formulas give same result. */
    const float max_uv = pack_islands_scale_margin(island_vector, box_array, 1.0f, 0.0f);
    r_scale[0] = 1.0f / max_uv;
    r_scale[1] = r_scale[0];
    return box_array;
  }

  if (params.margin_method == ED_UVPACK_MARGIN_FRACTION) {
    /* Uses a line search on scale. ~10x slower than other method. */
    const float scale = pack_islands_margin_fraction(island_vector, box_array, params.margin);
    r_scale[0] = scale;
    r_scale[1] = scale;
    /* pack_islands_margin_fraction will pad FaceIslands, return early. */
    return box_array;
  }

  float margin = params.margin;
  switch (params.margin_method) {
    case ED_UVPACK_MARGIN_ADD:    /* Default for Blender 2.8 and earlier. */
      break;                      /* Nothing to do. */
    case ED_UVPACK_MARGIN_SCALED: /* Default for Blender 3.3 and later. */
      margin = calc_margin_from_aabb_length_sum(island_vector, params);
      break;
    case ED_UVPACK_MARGIN_FRACTION: /* Added as an option in Blender 3.4. */
      BLI_assert_unreachable();     /* Handled above. */
      break;
    default:
      BLI_assert_unreachable();
  }

  const float max_uv = pack_islands_scale_margin(island_vector, box_array, 1.0f, margin);
  r_scale[0] = 1.0f / max_uv;
  r_scale[1] = r_scale[0];

  for (int index = 0; index < island_vector.size(); index++) {
    FaceIsland *island = island_vector[index];
    BLI_rctf_pad(&island->bounds_rect, margin, margin);
  }
  return box_array;
}

static bool island_has_pins(FaceIsland *island)
{
  BMLoop *l;
  BMIter iter;
  const int cd_loop_uv_offset = island->cd_loop_uv_offset;
  for (int i = 0; i < island->faces_len; i++) {
    BM_ITER_ELEM (l, &iter, island->faces[i], BM_LOOPS_OF_FACE) {
      MLoopUV *luv = static_cast<MLoopUV *>(BM_ELEM_CD_GET_VOID_P(l, cd_loop_uv_offset));
      if (luv->flag & MLOOPUV_PINNED) {
        return true;
      }
    }
  }
  return false;
}

/* -------------------------------------------------------------------- */
/** \name Public UV Island Packing
 *
 * \note This behavior loosely follows #GEO_uv_parametrizer_pack.
 * \{ */

void ED_uvedit_pack_islands_multi(const Scene *scene,
                                  Object **objects,
                                  const uint objects_len,
                                  BMesh **bmesh_override,
                                  const struct UVMapUDIM_Params *udim_params,
                                  const struct UVPackIsland_Params *params)
{
  blender::Vector<FaceIsland *> island_vector;

  for (uint ob_index = 0; ob_index < objects_len; ob_index++) {
    Object *obedit = objects[ob_index];
    BMesh *bm = nullptr;
    if (bmesh_override) {
      /* Note: obedit is still required for aspect ratio and ID_RECALC_GEOMETRY. */
      bm = bmesh_override[ob_index];
    }
    else {
      BMEditMesh *em = BKE_editmesh_from_object(obedit);
      bm = em->bm;
    }
    BLI_assert(bm);
    const int cd_loop_uv_offset = CustomData_get_offset(&bm->ldata, CD_MLOOPUV);
    if (cd_loop_uv_offset == -1) {
      continue;
    }

    float aspect_y = 1.0f;
    if (params->correct_aspect) {
      float aspx, aspy;
      ED_uvedit_get_aspect(obedit, &aspx, &aspy);
      if (aspx != aspy) {
        aspect_y = aspx / aspy;
      }
    }

    ListBase island_list = {nullptr};
    bm_mesh_calc_uv_islands(scene,
                            bm,
                            &island_list,
                            params->only_selected_faces,
                            params->only_selected_uvs,
                            params->use_seams,
                            aspect_y,
                            cd_loop_uv_offset);

    /* Remove from linked list and append to blender::Vector. */
    LISTBASE_FOREACH_MUTABLE (struct FaceIsland *, island, &island_list) {
      BLI_remlink(&island_list, island);
      if (params->ignore_pinned && island_has_pins(island)) {
        MEM_freeN(island->faces);
        MEM_freeN(island);
        continue;
      }
      island_vector.append(island);
    }
  }

  if (island_vector.size() == 0) {
    return;
  }

  /* Coordinates of bounding box containing all selected UVs. */
  float selection_min_co[2], selection_max_co[2];
  INIT_MINMAX2(selection_min_co, selection_max_co);

  for (int index = 0; index < island_vector.size(); index++) {
    FaceIsland *island = island_vector[index];
    /* Skip calculation if using specified UDIM option. */
    if (udim_params && (udim_params->use_target_udim == false)) {
      float bounds_min[2], bounds_max[2];
      INIT_MINMAX2(bounds_min, bounds_max);
      for (int i = 0; i < island->faces_len; i++) {
        BMFace *f = island->faces[i];
        BM_face_uv_minmax(f, bounds_min, bounds_max, island->cd_loop_uv_offset);
      }

      selection_min_co[0] = MIN2(bounds_min[0], selection_min_co[0]);
      selection_min_co[1] = MIN2(bounds_min[1], selection_min_co[1]);
      selection_max_co[0] = MAX2(bounds_max[0], selection_max_co[0]);
      selection_max_co[1] = MAX2(bounds_max[1], selection_max_co[1]);
    }

    if (params->rotate) {
      face_island_uv_rotate_fit_aabb(island);
    }

    bm_face_array_calc_bounds(
        island->faces, island->faces_len, island->cd_loop_uv_offset, &island->bounds_rect);
  }

  /* Center of bounding box containing all selected UVs. */
  float selection_center[2];
  if (udim_params && (udim_params->use_target_udim == false)) {
    selection_center[0] = (selection_min_co[0] + selection_max_co[0]) / 2.0f;
    selection_center[1] = (selection_min_co[1] + selection_max_co[1]) / 2.0f;
  }

  float scale[2] = {1.0f, 1.0f};
  BoxPack *box_array = pack_islands_params(island_vector, *params, scale);

  /* Tile offset. */
  float base_offset[2] = {0.0f, 0.0f};

  /* CASE: ignore UDIM. */
  if (udim_params == nullptr) {
    /* pass */
  }
  /* CASE: Active/specified(smart uv project) UDIM. */
  else if (udim_params->use_target_udim) {

    /* Calculate offset based on specified_tile_index. */
    base_offset[0] = (udim_params->target_udim - 1001) % 10;
    base_offset[1] = (udim_params->target_udim - 1001) / 10;
  }

  /* CASE: Closest UDIM. */
  else {
    const Image *image = udim_params->image;
    const int *udim_grid = udim_params->grid_shape;
    /* Check if selection lies on a valid UDIM grid tile. */
    bool is_valid_udim = uv_coords_isect_udim(image, udim_grid, selection_center);
    if (is_valid_udim) {
      base_offset[0] = floorf(selection_center[0]);
      base_offset[1] = floorf(selection_center[1]);
    }
    /* If selection doesn't lie on any UDIM then find the closest UDIM grid or image tile. */
    else {
      float nearest_image_tile_co[2] = {FLT_MAX, FLT_MAX};
      float nearest_image_tile_dist = FLT_MAX, nearest_grid_tile_dist = FLT_MAX;
      if (image) {
        nearest_image_tile_dist = uv_nearest_image_tile_distance(
            image, selection_center, nearest_image_tile_co);
      }

      float nearest_grid_tile_co[2] = {0.0f, 0.0f};
      nearest_grid_tile_dist = uv_nearest_grid_tile_distance(
          udim_grid, selection_center, nearest_grid_tile_co);

      base_offset[0] = (nearest_image_tile_dist < nearest_grid_tile_dist) ?
                           nearest_image_tile_co[0] :
                           nearest_grid_tile_co[0];
      base_offset[1] = (nearest_image_tile_dist < nearest_grid_tile_dist) ?
                           nearest_image_tile_co[1] :
                           nearest_grid_tile_co[1];
    }
  }

  for (int i = 0; i < island_vector.size(); i++) {
    FaceIsland *island = island_vector[box_array[i].index];
    const float pivot[2] = {
        island->bounds_rect.xmin,
        island->bounds_rect.ymin,
    };
    const float offset[2] = {
        ((box_array[i].x * scale[0]) - island->bounds_rect.xmin) + base_offset[0],
        ((box_array[i].y * scale[1]) - island->bounds_rect.ymin) + base_offset[1],
    };
    for (int j = 0; j < island->faces_len; j++) {
      BMFace *efa = island->faces[j];
      bm_face_uv_translate_and_scale_around_pivot(
          efa, offset, scale, pivot, island->cd_loop_uv_offset);
    }
  }

  for (uint ob_index = 0; ob_index < objects_len; ob_index++) {
    Object *obedit = objects[ob_index];
    DEG_id_tag_update(static_cast<ID *>(obedit->data), ID_RECALC_GEOMETRY);
    WM_main_add_notifier(NC_GEOM | ND_DATA, obedit->data);
  }

  for (FaceIsland *island : island_vector) {
    MEM_freeN(island->faces);
    MEM_freeN(island);
  }

  MEM_freeN(box_array);
}

/** \} */
