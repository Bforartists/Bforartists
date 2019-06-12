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
 * The Original Code is Copyright (C) 2008, Blender Foundation
 * This is a new part of Blender
 */

#ifndef __BKE_GPENCIL_H__
#define __BKE_GPENCIL_H__

/** \file
 * \ingroup bke
 */

struct ArrayGpencilModifierData;
struct BoundBox;
struct Brush;
struct CurveMapping;
struct Depsgraph;
struct GpencilModifierData;
struct LatticeGpencilModifierData;
struct ListBase;
struct Main;
struct Material;
struct Object;
struct SimplifyGpencilModifierData;
struct ToolSettings;
struct bDeformGroup;
struct bGPDframe;
struct bGPDlayer;
struct bGPDpalette;
struct bGPDpalettecolor;
struct bGPDspoint;
struct bGPDstroke;
struct bGPdata;

struct MDeformVert;
struct MDeformWeight;

/* ------------ Grease-Pencil API ------------------ */

void BKE_gpencil_free_point_weights(struct MDeformVert *dvert);
void BKE_gpencil_free_stroke_weights(struct bGPDstroke *gps);
void BKE_gpencil_free_stroke(struct bGPDstroke *gps);
bool BKE_gpencil_free_strokes(struct bGPDframe *gpf);
void BKE_gpencil_free_frames(struct bGPDlayer *gpl);
void BKE_gpencil_free_layers(struct ListBase *list);
bool BKE_gpencil_free_frame_runtime_data(struct bGPDframe *derived_gpf);
void BKE_gpencil_free(struct bGPdata *gpd, bool free_all);

void BKE_gpencil_batch_cache_dirty_tag(struct bGPdata *gpd);
void BKE_gpencil_batch_cache_free(struct bGPdata *gpd);

void BKE_gpencil_stroke_sync_selection(struct bGPDstroke *gps);

struct bGPDframe *BKE_gpencil_frame_addnew(struct bGPDlayer *gpl, int cframe);
struct bGPDframe *BKE_gpencil_frame_addcopy(struct bGPDlayer *gpl, int cframe);
struct bGPDlayer *BKE_gpencil_layer_addnew(struct bGPdata *gpd, const char *name, bool setactive);
struct bGPdata *BKE_gpencil_data_addnew(struct Main *bmain, const char name[]);

struct bGPDframe *BKE_gpencil_frame_duplicate(const struct bGPDframe *gpf_src);
struct bGPDlayer *BKE_gpencil_layer_duplicate(const struct bGPDlayer *gpl_src);
void BKE_gpencil_frame_copy_strokes(struct bGPDframe *gpf_src, struct bGPDframe *gpf_dst);
struct bGPDstroke *BKE_gpencil_stroke_duplicate(struct bGPDstroke *gps_src);

void BKE_gpencil_copy_data(struct bGPdata *gpd_dst, const struct bGPdata *gpd_src, const int flag);
struct bGPdata *BKE_gpencil_copy(struct Main *bmain, const struct bGPdata *gpd);
struct bGPdata *BKE_gpencil_data_duplicate(struct Main *bmain,
                                           const struct bGPdata *gpd,
                                           bool internal_copy);

void BKE_gpencil_make_local(struct Main *bmain, struct bGPdata *gpd, const bool lib_local);

void BKE_gpencil_frame_delete_laststroke(struct bGPDlayer *gpl, struct bGPDframe *gpf);

/* materials */
void BKE_gpencil_material_index_reassign(struct bGPdata *gpd, int totcol, int index);
void BKE_gpencil_material_remap(struct bGPdata *gpd,
                                const unsigned int *remap,
                                unsigned int remap_len);

/* statistics functions */
void BKE_gpencil_stats_update(struct bGPdata *gpd);

/* Utilities for creating and populating GP strokes */
/* - Number of values defining each point in the built-in data
 *   buffers for primitives (e.g. 2D Monkey)
 */
#define GP_PRIM_DATABUF_SIZE 5

void BKE_gpencil_stroke_add_points(struct bGPDstroke *gps,
                                   const float *array,
                                   const int totpoints,
                                   const float mat[4][4]);

struct bGPDstroke *BKE_gpencil_add_stroke(struct bGPDframe *gpf,
                                          int mat_idx,
                                          int totpoints,
                                          short thickness);

/* Stroke and Fill - Alpha Visibility Threshold */
#define GPENCIL_ALPHA_OPACITY_THRESH 0.001f
#define GPENCIL_STRENGTH_MIN 0.003f

bool gpencil_layer_is_editable(const struct bGPDlayer *gpl);

/* How gpencil_layer_getframe() should behave when there
 * is no existing GP-Frame on the frame requested.
 */
typedef enum eGP_GetFrame_Mode {
  /* Use the preceding gp-frame (i.e. don't add anything) */
  GP_GETFRAME_USE_PREV = 0,

  /* Add a new empty/blank frame */
  GP_GETFRAME_ADD_NEW = 1,
  /* Make a copy of the active frame */
  GP_GETFRAME_ADD_COPY = 2,
} eGP_GetFrame_Mode;

struct bGPDframe *BKE_gpencil_layer_getframe(struct bGPDlayer *gpl,
                                             int cframe,
                                             eGP_GetFrame_Mode addnew);
struct bGPDframe *BKE_gpencil_layer_find_frame(struct bGPDlayer *gpl, int cframe);
bool BKE_gpencil_layer_delframe(struct bGPDlayer *gpl, struct bGPDframe *gpf);

struct bGPDlayer *BKE_gpencil_layer_getactive(struct bGPdata *gpd);
void BKE_gpencil_layer_setactive(struct bGPdata *gpd, struct bGPDlayer *active);
void BKE_gpencil_layer_delete(struct bGPdata *gpd, struct bGPDlayer *gpl);

/* Brush */
struct Material *BKE_gpencil_brush_material_get(struct Brush *brush);
void BKE_gpencil_brush_material_set(struct Brush *brush, struct Material *material);

/* Object */
struct Material *BKE_gpencil_object_material_ensure_active(struct Main *bmain, struct Object *ob);
struct Material *BKE_gpencil_object_material_ensure_from_brush(struct Main *bmain,
                                                               struct Object *ob,
                                                               struct Brush *brush);
int BKE_gpencil_object_material_ensure(struct Main *bmain,
                                       struct Object *ob,
                                       struct Material *material);

struct Material *BKE_gpencil_object_material_new(struct Main *bmain,
                                                 struct Object *ob,
                                                 const char *name,
                                                 int *r_index);

int BKE_gpencil_object_material_get_index(struct Object *ob, struct Material *ma);

struct Material *BKE_gpencil_object_material_get_from_brush(struct Object *ob,
                                                            struct Brush *brush);
int BKE_gpencil_object_material_get_index_from_brush(struct Object *ob, struct Brush *brush);

struct Material *BKE_gpencil_object_material_ensure_from_active_input_toolsettings(
    struct Main *bmain, struct Object *ob, struct ToolSettings *ts);
struct Material *BKE_gpencil_object_material_ensure_from_active_input_brush(struct Main *bmain,
                                                                            struct Object *ob,
                                                                            struct Brush *brush);
struct Material *BKE_gpencil_object_material_ensure_from_active_input_material(struct Main *bmain,
                                                                               struct Object *ob);

/* object boundbox */
bool BKE_gpencil_data_minmax(const struct bGPdata *gpd, float r_min[3], float r_max[3]);
bool BKE_gpencil_stroke_minmax(const struct bGPDstroke *gps,
                               const bool use_select,
                               float r_min[3],
                               float r_max[3]);
bool BKE_gpencil_stroke_select_check(const struct bGPDstroke *gps);

struct BoundBox *BKE_gpencil_boundbox_get(struct Object *ob);
void BKE_gpencil_centroid_3d(struct bGPdata *gpd, float r_centroid[3]);

/* vertex groups */
void BKE_gpencil_dvert_ensure(struct bGPDstroke *gps);
void BKE_gpencil_vgroup_remove(struct Object *ob, struct bDeformGroup *defgroup);
void BKE_gpencil_stroke_weights_duplicate(struct bGPDstroke *gps_src, struct bGPDstroke *gps_dst);

/* GPencil geometry evaluation */
void BKE_gpencil_eval_geometry(struct Depsgraph *depsgraph, struct bGPdata *gpd);

/* stroke geometry utilities */
void BKE_gpencil_stroke_normal(const struct bGPDstroke *gps, float r_normal[3]);
void BKE_gpencil_simplify_stroke(struct bGPDstroke *gps, float factor);
void BKE_gpencil_simplify_fixed(struct bGPDstroke *gps);
void BKE_gpencil_subdivide(struct bGPDstroke *gps, int level, int flag);
bool BKE_gpencil_trim_stroke(struct bGPDstroke *gps);

void BKE_gpencil_stroke_2d_flat(const struct bGPDspoint *points,
                                int totpoints,
                                float (*points2d)[2],
                                int *r_direction);
void BKE_gpencil_stroke_2d_flat_ref(const struct bGPDspoint *ref_points,
                                    int ref_totpoints,
                                    const struct bGPDspoint *points,
                                    int totpoints,
                                    float (*points2d)[2],
                                    const float scale,
                                    int *r_direction);

void BKE_gpencil_transform(struct bGPdata *gpd, float mat[4][4]);

bool BKE_gpencil_smooth_stroke(struct bGPDstroke *gps, int i, float inf);
bool BKE_gpencil_smooth_stroke_strength(struct bGPDstroke *gps, int point_index, float influence);
bool BKE_gpencil_smooth_stroke_thickness(struct bGPDstroke *gps, int point_index, float influence);
bool BKE_gpencil_smooth_stroke_uv(struct bGPDstroke *gps, int point_index, float influence);

void BKE_gpencil_get_range_selected(struct bGPDlayer *gpl, int *r_initframe, int *r_endframe);
float BKE_gpencil_multiframe_falloff_calc(
    struct bGPDframe *gpf, int actnum, int f_init, int f_end, struct CurveMapping *cur_falloff);

extern void (*BKE_gpencil_batch_cache_dirty_tag_cb)(struct bGPdata *gpd);
extern void (*BKE_gpencil_batch_cache_free_cb)(struct bGPdata *gpd);

#endif /*  __BKE_GPENCIL_H__ */
