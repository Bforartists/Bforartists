/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 */

#pragma once

/** \file
 * \ingroup bmesh
 */

#include "bmesh_class.h"

struct BMeshNormalsUpdate_Params {
  /**
   * When calculating tessellation as well as normals, tessellate & calculate face normals
   * for improved performance. See #BMeshCalcTessellation_Params
   */
  bool face_normals;
};

void BM_mesh_normals_update_ex(BMesh *bm, const struct BMeshNormalsUpdate_Params *param);
void BM_mesh_normals_update(BMesh *bm);
void BM_mesh_normals_update_with_partial_ex(BMesh *bm,
                                            const struct BMPartialUpdate *bmpinfo,
                                            const struct BMeshNormalsUpdate_Params *param);
void BM_mesh_normals_update_with_partial(BMesh *bm, const struct BMPartialUpdate *bmpinfo);

void BM_verts_calc_normal_vcos(BMesh *bm,
                               const float (*fnos)[3],
                               const float (*vcos)[3],
                               float (*vnos)[3]);
void BM_loops_calc_normal_vcos(BMesh *bm,
                               const float (*vcos)[3],
                               const float (*vnos)[3],
                               const float (*fnos)[3],
                               const bool use_split_normals,
                               const float split_angle,
                               float (*r_lnos)[3],
                               struct MLoopNorSpaceArray *r_lnors_spacearr,
                               short (*clnors_data)[2],
                               const int cd_loop_clnors_offset,
                               const bool do_rebuild);

bool BM_loop_check_cyclic_smooth_fan(BMLoop *l_curr);
void BM_lnorspacearr_store(BMesh *bm, float (*r_lnors)[3]);
void BM_lnorspace_invalidate(BMesh *bm, const bool do_invalidate_all);
void BM_lnorspace_rebuild(BMesh *bm, bool preserve_clnor);
void BM_lnorspace_update(BMesh *bm);
void BM_normals_loops_edges_tag(BMesh *bm, const bool do_edges);
#ifndef NDEBUG
void BM_lnorspace_err(BMesh *bm);
#endif

/* Loop Generics */
struct BMLoopNorEditDataArray *BM_loop_normal_editdata_array_init(BMesh *bm,
                                                                  const bool do_all_loops_of_vert);
void BM_loop_normal_editdata_array_free(struct BMLoopNorEditDataArray *lnors_ed_arr);

bool BM_custom_loop_normals_to_vector_layer(struct BMesh *bm);
void BM_custom_loop_normals_from_vector_layer(struct BMesh *bm, bool add_sharp_edges);

void BM_edges_sharp_from_angle_set(BMesh *bm, const float split_angle);
