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
 * Copyright 2017, Blender Foundation.
 */

/** \file
 * \ingroup draw
 */

#ifndef __GPENCIL_ENGINE_H__
#define __GPENCIL_ENGINE_H__

#include "GPU_batch.h"

struct GPENCIL_Data;
struct GPENCIL_StorageList;
struct MaterialGPencilStyle;
struct Object;
struct RenderEngine;
struct RenderLayer;
struct bGPDstroke;

struct GPUBatch;
struct GPUVertBuf;
struct GPUVertFormat;

#define GPENCIL_CACHE_BLOCK_SIZE 8
#define GPENCIL_MAX_SHGROUPS 65536
#define GPENCIL_GROUPS_BLOCK_SIZE 1024

/* used to expand VBOs. Size has a big impact in the speed */
#define GPENCIL_VBO_BLOCK_SIZE 128

#define GPENCIL_COLOR_SOLID 0
#define GPENCIL_COLOR_TEXTURE 1
#define GPENCIL_COLOR_PATTERN 2

#define GP_IS_CAMERAVIEW ((rv3d != NULL) && (rv3d->persp == RV3D_CAMOB && v3d->camera))

/* *********** OBJECTS CACHE *********** */
typedef struct tGPencilObjectCache_shgrp {
  /** type of blend (regular, add, mult, etc...) */
  int mode;
  /** flag to enable the layer clamping */
  bool mask_layer;
  /** factor to define the opacity of the layer */
  float blend_opacity;
  DRWShadingGroup *init_shgrp;
  DRWShadingGroup *end_shgrp;
} tGPencilObjectCache_shgrp;

/* used to save gpencil object data for drawing */
typedef struct tGPencilObjectCache {
  struct Object *ob;
  struct bGPdata *gpd;
  int idx; /*original index, can change after sort */
  char *name;

  /* effects */
  bool has_fx;
  ListBase shader_fx;
  float pixfactor;
  DRWShadingGroup *fx_wave_sh;
  DRWShadingGroup *fx_blur_sh;
  DRWShadingGroup *fx_colorize_sh;
  DRWShadingGroup *fx_pixel_sh;
  DRWShadingGroup *fx_rim_sh;
  DRWShadingGroup *fx_shadow_sh;
  DRWShadingGroup *fx_glow_sh;
  DRWShadingGroup *fx_swirl_sh;
  DRWShadingGroup *fx_flip_sh;
  DRWShadingGroup *fx_light_sh;

  float loc[3];
  float obmat[4][4];
  float zdepth;   /* z-depth value to sort gp object */
  bool is_dup_ob; /* flag to tag duplicate objects */
  float scale;

  /* shading type */
  int shading_type[2];

  /* GPU data size */
  int tot_vertex;
  int tot_triangles;

  /* Save shader groups by layer */
  int tot_layers;
  tGPencilObjectCache_shgrp *shgrp_array;

} tGPencilObjectCache;

/* *********** LISTS *********** */
typedef struct GPENCIL_shgroup {
  int s_clamp;
  int stroke_style;
  int color_type;
  int mode;
  int texture_mix;
  int texture_flip;
  int texture_clamp;
  int fill_style;
  int keep_size;
  int caps_mode[2];
  float obj_scale;
  int xray_mode;
  int alignment_mode;

  float gradient_f;
  float gradient_s[2];

  float mix_stroke_factor;

  /* color of the wireframe */
  float wire_color[4];
  /* shading type and mode */
  int shading_type[2];
  int is_xray;
} GPENCIL_shgroup;

typedef struct GPENCIL_Storage {
  int shgroup_id; /* total elements */
  int stroke_style;
  int color_type;
  int mode;
  int xray;
  int keep_size;
  float obj_scale;
  float pixfactor;
  bool is_playing;
  bool is_render;
  bool is_mat_preview;
  bool background_ready;
  int is_xray;
  bool is_ontop;
  bool reset_cache;
  const float *pixsize;
  float render_pixsize;
  int tonemapping;
  int do_select_outline;
  float select_color[4];
  short multisamples;
  float grid_matrix[4][4];

  short framebuffer_flag; /* flag what framebuffer need to create */

  int blend_mode;
  int mask_layer;

  /* simplify settings*/
  bool simplify_fill;
  bool simplify_modif;
  bool simplify_fx;
  bool simplify_blend;

  float gradient_f;
  float gradient_s[2];
  int alignment_mode;

  float mix_stroke_factor;

  /* Render Matrices and data */
  float view_vecs[2][4]; /* vec4[2] */

  int shade_render[2];

  Object *camera; /* camera pointer for render mode */
} GPENCIL_Storage;

typedef enum eGpencilFramebuffer_Flag {
  GP_FRAMEBUFFER_MULTISAMPLE = (1 << 0),
  GP_FRAMEBUFFER_BASIC = (1 << 1),
  GP_FRAMEBUFFER_DRAW = (1 << 2),
} eGpencilFramebuffer_Flag;

typedef struct GPENCIL_StorageList {
  struct GPENCIL_Storage *storage;
  struct g_data *g_data;
  struct GPENCIL_shgroup *shgroups;
} GPENCIL_StorageList;

typedef struct GPENCIL_PassList {
  struct DRWPass *stroke_pass_2d;
  struct DRWPass *stroke_pass_3d;
  struct DRWPass *edit_pass;
  struct DRWPass *drawing_pass;
  struct DRWPass *mix_pass;
  struct DRWPass *mix_pass_noblend;
  struct DRWPass *background_pass;
  struct DRWPass *paper_pass;
  struct DRWPass *grid_pass;
  struct DRWPass *blend_pass;

  /* effects */
  struct DRWPass *fx_shader_pass;
  struct DRWPass *fx_shader_pass_blend;

} GPENCIL_PassList;

typedef struct GPENCIL_FramebufferList {
  struct GPUFrameBuffer *main;
  struct GPUFrameBuffer *temp_fb_a;
  struct GPUFrameBuffer *temp_fb_b;
  struct GPUFrameBuffer *temp_fb_fx;
  struct GPUFrameBuffer *background_fb;

  struct GPUFrameBuffer *multisample_fb;
} GPENCIL_FramebufferList;

typedef struct GPENCIL_TextureList {
  struct GPUTexture *texture;

  /* multisample textures */
  struct GPUTexture *multisample_color;
  struct GPUTexture *multisample_depth;

  /* Background textures for speed-up drawing. */
  struct GPUTexture *background_depth_tx;
  struct GPUTexture *background_color_tx;

} GPENCIL_TextureList;

typedef struct GPENCIL_Data {
  void *engine_type; /* Required */
  struct GPENCIL_FramebufferList *fbl;
  struct GPENCIL_TextureList *txl;
  struct GPENCIL_PassList *psl;
  struct GPENCIL_StorageList *stl;

  /* render textures */
  struct GPUTexture *render_depth_tx;
  struct GPUTexture *render_color_tx;

} GPENCIL_Data;

/* *********** STATIC *********** */
typedef struct g_data {
  struct DRWShadingGroup *shgrps_edit_point;
  struct DRWShadingGroup *shgrps_edit_line;
  struct DRWShadingGroup *shgrps_drawing_stroke;
  struct DRWShadingGroup *shgrps_drawing_fill;
  struct DRWShadingGroup *shgrps_grid;

  int gp_cache_used; /* total objects in cache */
  int gp_cache_size; /* size of the cache */
  struct tGPencilObjectCache *gp_object_cache;

  /* for buffer only one batch is nedeed because the drawing is only of one stroke */
  GPUBatch *batch_buffer_stroke;
  GPUBatch *batch_buffer_fill;
  GPUBatch *batch_buffer_ctrlpoint;

  /* grid geometry */
  GPUBatch *batch_grid;

  /* runtime pointers texture */
  struct GPUTexture *input_depth_tx;
  struct GPUTexture *input_color_tx;

  /* working textures */
  struct GPUTexture *temp_color_tx_a;
  struct GPUTexture *temp_depth_tx_a;

  struct GPUTexture *temp_color_tx_b;
  struct GPUTexture *temp_depth_tx_b;

  struct GPUTexture *temp_color_tx_fx;
  struct GPUTexture *temp_depth_tx_fx;

  int session_flag;
  bool do_instances;

} g_data; /* Transient data */

/* flags for fast drawing support */
typedef enum eGPsession_Flag {
  GP_DRW_PAINT_HOLD = (1 << 0),
  GP_DRW_PAINT_IDLE = (1 << 1),
  GP_DRW_PAINT_FILLING = (1 << 2),
  GP_DRW_PAINT_READY = (1 << 3),
  GP_DRW_PAINT_PAINTING = (1 << 4),
} eGPsession_Flag;

typedef struct GPENCIL_e_data {
  /* textures */
  struct GPUTexture *gpencil_blank_texture;

  /* general drawing shaders */
  struct GPUShader *gpencil_fill_sh;
  struct GPUShader *gpencil_stroke_sh;
  struct GPUShader *gpencil_point_sh;
  struct GPUShader *gpencil_edit_point_sh;
  struct GPUShader *gpencil_line_sh;
  struct GPUShader *gpencil_drawing_fill_sh;
  struct GPUShader *gpencil_fullscreen_sh;
  struct GPUShader *gpencil_simple_fullscreen_sh;
  struct GPUShader *gpencil_blend_fullscreen_sh;
  struct GPUShader *gpencil_background_sh;
  struct GPUShader *gpencil_paper_sh;

  /* effects */
  struct GPUShader *gpencil_fx_blur_sh;
  struct GPUShader *gpencil_fx_colorize_sh;
  struct GPUShader *gpencil_fx_flip_sh;
  struct GPUShader *gpencil_fx_glow_prepare_sh;
  struct GPUShader *gpencil_fx_glow_resolve_sh;
  struct GPUShader *gpencil_fx_light_sh;
  struct GPUShader *gpencil_fx_pixel_sh;
  struct GPUShader *gpencil_fx_rim_prepare_sh;
  struct GPUShader *gpencil_fx_rim_resolve_sh;
  struct GPUShader *gpencil_fx_shadow_prepare_sh;
  struct GPUShader *gpencil_fx_shadow_resolve_sh;
  struct GPUShader *gpencil_fx_swirl_sh;
  struct GPUShader *gpencil_fx_wave_sh;

} GPENCIL_e_data; /* Engine data */

/* GPUBatch Cache Element */
typedef struct GpencilBatchCacheElem {
  GPUBatch *batch;
  GPUVertBuf *vbo;
  int vbo_len;
  /* attr ids */
  GPUVertFormat *format;
  uint pos_id;
  uint color_id;
  uint thickness_id;
  uint uvdata_id;
  uint prev_pos_id;

  /* size for VBO alloc */
  int tot_vertex;
} GpencilBatchCacheElem;

/* Defines each batch group to define later the shgroup */
typedef struct GpencilBatchGroup {
  struct bGPDlayer *gpl;  /* reference to original layer */
  struct bGPDframe *gpf;  /* reference to original frame */
  struct bGPDstroke *gps; /* reference to original stroke */
  short type;             /* type of element */
  bool onion;             /* the group is part of onion skin */
  int vertex_idx;         /* index of vertex data */
} GpencilBatchGroup;

typedef enum GpencilBatchGroup_Type {
  eGpencilBatchGroupType_Stroke = 1,
  eGpencilBatchGroupType_Point = 2,
  eGpencilBatchGroupType_Fill = 3,
  eGpencilBatchGroupType_Edit = 4,
  eGpencilBatchGroupType_Edlin = 5,
} GpencilBatchGroup_Type;

/* Runtime data for GPU and evaluated frames after applying modifiers */
typedef struct GpencilBatchCache {
  GpencilBatchCacheElem b_stroke;
  GpencilBatchCacheElem b_point;
  GpencilBatchCacheElem b_fill;
  GpencilBatchCacheElem b_edit;
  GpencilBatchCacheElem b_edlin;

  /** Cache is dirty */
  bool is_dirty;
  /** Edit mode flag */
  bool is_editmode;
  /** Last cache frame */
  int cache_frame;

  /** Total groups in arrays */
  int grp_used;
  /** Max size of the array */
  int grp_size;
  /** Array of cache elements */
  struct GpencilBatchGroup *grp_cache;
} GpencilBatchCache;

/* general drawing functions */
struct DRWShadingGroup *gpencil_shgroup_stroke_create(struct GPENCIL_e_data *e_data,
                                                      struct GPENCIL_Data *vedata,
                                                      struct DRWPass *pass,
                                                      struct GPUShader *shader,
                                                      struct Object *ob,
                                                      float (*obmat)[4],
                                                      struct bGPdata *gpd,
                                                      struct bGPDlayer *gpl,
                                                      struct bGPDstroke *gps,
                                                      struct MaterialGPencilStyle *gp_style,
                                                      int id,
                                                      bool onion,
                                                      const float scale,
                                                      const int shading_type[2]);
void gpencil_populate_datablock(struct GPENCIL_e_data *e_data,
                                void *vedata,
                                struct Object *ob,
                                struct tGPencilObjectCache *cache_ob);
void gpencil_populate_buffer_strokes(struct GPENCIL_e_data *e_data,
                                     void *vedata,
                                     struct ToolSettings *ts,
                                     struct Object *ob);
void gpencil_populate_multiedit(struct GPENCIL_e_data *e_data,
                                void *vedata,
                                struct Object *ob,
                                struct tGPencilObjectCache *cache_ob);
void gpencil_triangulate_stroke_fill(struct Object *ob, struct bGPDstroke *gps);
void gpencil_populate_particles(struct GPENCIL_e_data *e_data,
                                struct GHash *gh_objects,
                                void *vedata);

void gpencil_multisample_ensure(struct GPENCIL_Data *vedata, int rect_w, int rect_h);

/* create geometry functions */
void gpencil_get_point_geom(struct GpencilBatchCacheElem *be,
                            struct bGPDstroke *gps,
                            short thickness,
                            const float ink[4],
                            const int follow_mode);
void gpencil_get_stroke_geom(struct GpencilBatchCacheElem *be,
                             struct bGPDstroke *gps,
                             short thickness,
                             const float ink[4]);
void gpencil_get_fill_geom(struct GpencilBatchCacheElem *be,
                           struct Object *ob,
                           struct bGPDstroke *gps,
                           const float color[4]);
void gpencil_get_edit_geom(struct GpencilBatchCacheElem *be,
                           struct bGPDstroke *gps,
                           float alpha,
                           short dflag);
void gpencil_get_edlin_geom(struct GpencilBatchCacheElem *be,
                            struct bGPDstroke *gps,
                            float alpha,
                            const bool hide_select);

struct GPUBatch *gpencil_get_buffer_stroke_geom(struct bGPdata *gpd, short thickness);
struct GPUBatch *gpencil_get_buffer_fill_geom(struct bGPdata *gpd);
struct GPUBatch *gpencil_get_buffer_point_geom(struct bGPdata *gpd, short thickness);
struct GPUBatch *gpencil_get_buffer_ctrlpoint_geom(struct bGPdata *gpd);
struct GPUBatch *gpencil_get_grid(Object *ob);

/* object cache functions */
struct tGPencilObjectCache *gpencil_object_cache_add(struct tGPencilObjectCache *cache_array,
                                                     struct Object *ob,
                                                     int *gp_cache_size,
                                                     int *gp_cache_used);

bool gpencil_onion_active(struct bGPdata *gpd);

/* shading groups cache functions */
struct GpencilBatchGroup *gpencil_group_cache_add(struct GpencilBatchGroup *cache_array,
                                                  struct bGPDlayer *gpl,
                                                  struct bGPDframe *gpf,
                                                  struct bGPDstroke *gps,
                                                  const short type,
                                                  const bool onion,
                                                  const int vertex_idx,
                                                  int *grp_size,
                                                  int *grp_used);

/* geometry batch cache functions */
struct GpencilBatchCache *gpencil_batch_cache_get(struct Object *ob, int cfra);

/* effects */
void GPENCIL_create_fx_shaders(struct GPENCIL_e_data *e_data);
void GPENCIL_delete_fx_shaders(struct GPENCIL_e_data *e_data);
void GPENCIL_create_fx_passes(struct GPENCIL_PassList *psl);

void gpencil_fx_prepare(struct GPENCIL_e_data *e_data,
                        struct GPENCIL_Data *vedata,
                        struct tGPencilObjectCache *cache_ob);
void gpencil_fx_draw(struct GPENCIL_e_data *e_data,
                     struct GPENCIL_Data *vedata,
                     struct tGPencilObjectCache *cache_ob);

/* main functions */
void GPENCIL_engine_init(void *vedata);
void GPENCIL_cache_init(void *vedata);
void GPENCIL_cache_populate(void *vedata, struct Object *ob);
void GPENCIL_cache_finish(void *vedata);
void GPENCIL_draw_scene(void *vedata);

/* render */
void GPENCIL_render_init(struct GPENCIL_Data *ved,
                         struct RenderEngine *engine,
                         struct Depsgraph *depsgraph);
void GPENCIL_render_to_image(void *vedata,
                             struct RenderEngine *engine,
                             struct RenderLayer *render_layer,
                             const rcti *rect);

/* TODO: GPXX workaround function to call free memory from draw manager while draw manager support
 * scene finish callback. */
void DRW_gpencil_free_runtime_data(void *ved);

/* Use of multisample framebuffers. */
#define MULTISAMPLE_GP_SYNC_ENABLE(lvl, fbl) \
  { \
    if ((lvl > 0) && (fbl->multisample_fb != NULL) && (DRW_state_is_fbo())) { \
      DRW_stats_query_start("GP Multisample Blit"); \
      GPU_framebuffer_bind(fbl->multisample_fb); \
      GPU_framebuffer_clear_color_depth_stencil( \
          fbl->multisample_fb, (const float[4]){0.0f}, 1.0f, 0x0); \
      DRW_stats_query_end(); \
    } \
  } \
  ((void)0)

#define MULTISAMPLE_GP_SYNC_DISABLE(lvl, fbl, fb, txl) \
  { \
    if ((lvl > 0) && (fbl->multisample_fb != NULL) && (DRW_state_is_fbo())) { \
      DRW_stats_query_start("GP Multisample Resolve"); \
      GPU_framebuffer_bind(fb); \
      DRW_multisamples_resolve(txl->multisample_depth, txl->multisample_color, true); \
      DRW_stats_query_end(); \
    } \
  } \
  ((void)0)

#define GPENCIL_3D_DRAWMODE(ob, gpd) \
  ((gpd) && (gpd->draw_mode == GP_DRAWMODE_3D) && ((ob->dtx & OB_DRAWXRAY) == 0))

#define GPENCIL_USE_SOLID(stl) \
  ((stl) && ((stl->storage->is_render) || (stl->storage->is_mat_preview)))

#endif /* __GPENCIL_ENGINE_H__ */
