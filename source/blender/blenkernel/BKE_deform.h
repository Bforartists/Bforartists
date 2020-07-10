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
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 */

#ifndef __BKE_DEFORM_H__
#define __BKE_DEFORM_H__

#ifdef __cplusplus
extern "C" {
#endif

/** \file
 * \ingroup bke
 * \brief support for deformation groups and hooks.
 */

struct ListBase;
struct MDeformVert;
struct MEdge;
struct MLoop;
struct MPoly;
struct Object;
struct bDeformGroup;

struct bDeformGroup *BKE_object_defgroup_new(struct Object *ob, const char *name);
void BKE_defgroup_copy_list(struct ListBase *lb1, const struct ListBase *lb2);
struct bDeformGroup *BKE_defgroup_duplicate(const struct bDeformGroup *ingroup);
struct bDeformGroup *BKE_object_defgroup_find_name(const struct Object *ob, const char *name);
int *BKE_object_defgroup_flip_map(const struct Object *ob,
                                  int *flip_map_len,
                                  const bool use_default);
int *BKE_object_defgroup_flip_map_single(const struct Object *ob,
                                         int *flip_map_len,
                                         const bool use_default,
                                         int defgroup);
int BKE_object_defgroup_flip_index(const struct Object *ob, int index, const bool use_default);
int BKE_object_defgroup_name_index(const struct Object *ob, const char *name);
void BKE_object_defgroup_unique_name(struct bDeformGroup *dg, struct Object *ob);

struct MDeformWeight *BKE_defvert_find_index(const struct MDeformVert *dv, const int defgroup);
struct MDeformWeight *BKE_defvert_ensure_index(struct MDeformVert *dv, const int defgroup);
void BKE_defvert_add_index_notest(struct MDeformVert *dv, int defgroup, const float weight);
void BKE_defvert_remove_group(struct MDeformVert *dvert, struct MDeformWeight *dw);
void BKE_defvert_clear(struct MDeformVert *dvert);
int BKE_defvert_find_shared(const struct MDeformVert *dvert_a, const struct MDeformVert *dvert_b);
bool BKE_defvert_is_weight_zero(const struct MDeformVert *dvert, const int defgroup_tot);

void BKE_defvert_array_free_elems(struct MDeformVert *dvert, int totvert);
void BKE_defvert_array_free(struct MDeformVert *dvert, int totvert);
void BKE_defvert_array_copy(struct MDeformVert *dst, const struct MDeformVert *src, int totvert);

float BKE_defvert_find_weight(const struct MDeformVert *dvert, const int defgroup);
float BKE_defvert_array_find_weight_safe(const struct MDeformVert *dvert,
                                         const int index,
                                         const int defgroup);

float BKE_defvert_total_selected_weight(const struct MDeformVert *dv,
                                        int defbase_tot,
                                        const bool *defbase_sel);

float BKE_defvert_multipaint_collective_weight(const struct MDeformVert *dv,
                                               int defbase_tot,
                                               const bool *defbase_sel,
                                               int defbase_tot_sel,
                                               bool is_normalized);

float BKE_defvert_calc_lock_relative_weight(float weight,
                                            float locked_weight,
                                            float unlocked_weight);
float BKE_defvert_lock_relative_weight(float weight,
                                       const struct MDeformVert *dv,
                                       int defbase_tot,
                                       const bool *defbase_locked,
                                       const bool *defbase_unlocked);

void BKE_defvert_copy(struct MDeformVert *dvert_dst, const struct MDeformVert *dvert_src);
void BKE_defvert_copy_subset(struct MDeformVert *dvert_dst,
                             const struct MDeformVert *dvert_src,
                             const bool *vgroup_subset,
                             const int vgroup_tot);
void BKE_defvert_mirror_subset(struct MDeformVert *dvert_dst,
                               const struct MDeformVert *dvert_src,
                               const bool *vgroup_subset,
                               const int vgroup_tot,
                               const int *flip_map,
                               const int flip_map_len);
void BKE_defvert_copy_index(struct MDeformVert *dvert_dst,
                            const int defgroup_dst,
                            const struct MDeformVert *dvert_src,
                            const int defgroup_src);
void BKE_defvert_sync(struct MDeformVert *dvert_dst,
                      const struct MDeformVert *dvert_src,
                      const bool use_ensure);
void BKE_defvert_sync_mapped(struct MDeformVert *dvert_dst,
                             const struct MDeformVert *dvert_src,
                             const int *flip_map,
                             const int flip_map_len,
                             const bool use_ensure);
void BKE_defvert_remap(struct MDeformVert *dvert, int *map, const int map_len);
void BKE_defvert_flip(struct MDeformVert *dvert, const int *flip_map, const int flip_map_len);
void BKE_defvert_flip_merged(struct MDeformVert *dvert,
                             const int *flip_map,
                             const int flip_map_len);
void BKE_defvert_normalize(struct MDeformVert *dvert);
void BKE_defvert_normalize_subset(struct MDeformVert *dvert,
                                  const bool *vgroup_subset,
                                  const int vgroup_tot);
void BKE_defvert_normalize_lock_single(struct MDeformVert *dvert,
                                       const bool *vgroup_subset,
                                       const int vgroup_tot,
                                       const uint def_nr_lock);
void BKE_defvert_normalize_lock_map(struct MDeformVert *dvert,
                                    const bool *vgroup_subset,
                                    const int vgroup_tot,
                                    const bool *lock_flags,
                                    const int defbase_tot);

/* Utilities to 'extract' a given vgroup into a simple float array,
 * for verts, but also edges/polys/loops. */
void BKE_defvert_extract_vgroup_to_vertweights(struct MDeformVert *dvert,
                                               const int defgroup,
                                               const int num_verts,
                                               float *r_weights,
                                               const bool invert_vgroup);
void BKE_defvert_extract_vgroup_to_edgeweights(struct MDeformVert *dvert,
                                               const int defgroup,
                                               const int num_verts,
                                               struct MEdge *edges,
                                               const int num_edges,
                                               float *r_weights,
                                               const bool invert_vgroup);
void BKE_defvert_extract_vgroup_to_loopweights(struct MDeformVert *dvert,
                                               const int defgroup,
                                               const int num_verts,
                                               struct MLoop *loops,
                                               const int num_loops,
                                               float *r_weights,
                                               const bool invert_vgroup);
void BKE_defvert_extract_vgroup_to_polyweights(struct MDeformVert *dvert,
                                               const int defgroup,
                                               const int num_verts,
                                               struct MLoop *loops,
                                               const int num_loops,
                                               struct MPoly *polys,
                                               const int num_polys,
                                               float *r_weights,
                                               const bool invert_vgroup);

void BKE_defvert_weight_to_rgb(float r_rgb[3], const float weight);

#ifdef __cplusplus
}
#endif

#endif /* __BKE_DEFORM_H__ */
