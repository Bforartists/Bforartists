/* SPDX-FileCopyrightText: 2019 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup draw_engine
 */

#include "DRW_render.h"

#include "BKE_global.h"
#include "BKE_gpencil_legacy.h"

#include "BKE_object.hh"

#include "DNA_gpencil_legacy_types.h"

#include "UI_resources.hh"

#include "overlay_private.hh"

/* Returns the normal plane in NDC space. */
static void gpencil_depth_plane(Object *ob, float r_plane[4])
{
  /* TODO: put that into private data. */
  float viewinv[4][4];
  DRW_view_viewmat_get(nullptr, viewinv, true);
  float *camera_z_axis = viewinv[2];
  float *camera_pos = viewinv[3];

  /* Find the normal most likely to represent the grease pencil object. */
  /* TODO: This does not work quite well if you use
   * strokes not aligned with the object axes. Maybe we could try to
   * compute the minimum axis of all strokes. But this would be more
   * computationally heavy and should go into the GPData evaluation. */
  const BoundBox bbox = *BKE_object_boundbox_get(ob);
  /* Convert bbox to matrix */
  float mat[4][4], size[3], center[3];
  BKE_boundbox_calc_size_aabb(&bbox, size);
  BKE_boundbox_calc_center_aabb(&bbox, center);
  unit_m4(mat);
  copy_v3_v3(mat[3], center);
  /* Avoid division by 0.0 later. */
  add_v3_fl(size, 1e-8f);
  rescale_m4(mat, size);
  /* BBox space to World. */
  mul_m4_m4m4(mat, ob->object_to_world, mat);
  /* BBox center in world space. */
  copy_v3_v3(center, mat[3]);
  /* View Vector. */
  if (DRW_view_is_persp_get(nullptr)) {
    /* BBox center to camera vector. */
    sub_v3_v3v3(r_plane, camera_pos, mat[3]);
  }
  else {
    copy_v3_v3(r_plane, camera_z_axis);
  }
  /* World to BBox space. */
  invert_m4(mat);
  /* Normalize the vector in BBox space. */
  mul_mat3_m4_v3(mat, r_plane);
  normalize_v3(r_plane);

  transpose_m4(mat);
  /* mat is now a "normal" matrix which will transform
   * BBox space normal to world space. */
  mul_mat3_m4_v3(mat, r_plane);
  normalize_v3(r_plane);

  plane_from_point_normal_v3(r_plane, center, r_plane);
}

void OVERLAY_outline_init(OVERLAY_Data *vedata)
{
  OVERLAY_FramebufferList *fbl = vedata->fbl;
  OVERLAY_TextureList *txl = vedata->txl;
  OVERLAY_PrivateData *pd = vedata->stl->pd;
  DefaultTextureList *dtxl = DRW_viewport_texture_list_get();

  if (DRW_state_is_fbo()) {
    /* TODO: only alloc if needed. */
    DRW_texture_ensure_fullscreen_2d(&txl->temp_depth_tx, GPU_DEPTH24_STENCIL8, DRWTextureFlag(0));
    DRW_texture_ensure_fullscreen_2d(&txl->outlines_id_tx, GPU_R16UI, DRWTextureFlag(0));

    GPU_framebuffer_ensure_config(
        &fbl->outlines_prepass_fb,
        {GPU_ATTACHMENT_TEXTURE(txl->temp_depth_tx), GPU_ATTACHMENT_TEXTURE(txl->outlines_id_tx)});

    if (pd->antialiasing.enabled) {
      GPU_framebuffer_ensure_config(&fbl->outlines_resolve_fb,
                                    {
                                        GPU_ATTACHMENT_NONE,
                                        GPU_ATTACHMENT_TEXTURE(txl->overlay_color_tx),
                                        GPU_ATTACHMENT_TEXTURE(txl->overlay_line_tx),
                                    });
    }
    else {
      GPU_framebuffer_ensure_config(&fbl->outlines_resolve_fb,
                                    {
                                        GPU_ATTACHMENT_NONE,
                                        GPU_ATTACHMENT_TEXTURE(dtxl->color_overlay),
                                    });
    }
  }
}

void OVERLAY_outline_cache_init(OVERLAY_Data *vedata)
{
  OVERLAY_PassList *psl = vedata->psl;
  OVERLAY_TextureList *txl = vedata->txl;
  OVERLAY_PrivateData *pd = vedata->stl->pd;
  DefaultTextureList *dtxl = DRW_viewport_texture_list_get();
  DRWShadingGroup *grp = nullptr;

  const float outline_width = UI_GetThemeValuef(TH_OUTLINE_WIDTH);
  const bool do_expand = (U.pixelsize > 1.0) || (outline_width > 2.0f);

  {
    DRWState state = DRW_STATE_WRITE_COLOR | DRW_STATE_WRITE_DEPTH | DRW_STATE_DEPTH_LESS_EQUAL;
    DRW_PASS_CREATE(psl->outlines_prepass_ps, state | pd->clipping_state);

    GPUShader *sh_geom = OVERLAY_shader_outline_prepass(pd->xray_enabled_and_not_wire);

    pd->outlines_grp = grp = DRW_shgroup_create(sh_geom, psl->outlines_prepass_ps);
    DRW_shgroup_uniform_bool_copy(grp, "isTransform", (G.moving & G_TRANSFORM_OBJ) != 0);
    DRW_shgroup_uniform_block(grp, "globalsBlock", G_draw.block_ubo);

    GPUShader *sh_geom_ptcloud = OVERLAY_shader_outline_prepass_pointcloud();

    pd->outlines_ptcloud_grp = grp = DRW_shgroup_create(sh_geom_ptcloud, psl->outlines_prepass_ps);
    DRW_shgroup_uniform_bool_copy(grp, "isTransform", (G.moving & G_TRANSFORM_OBJ) != 0);
    DRW_shgroup_uniform_block(grp, "globalsBlock", G_draw.block_ubo);

    GPUShader *sh_gpencil = OVERLAY_shader_outline_prepass_gpencil();

    pd->outlines_gpencil_grp = grp = DRW_shgroup_create(sh_gpencil, psl->outlines_prepass_ps);
    DRW_shgroup_uniform_bool_copy(grp, "isTransform", (G.moving & G_TRANSFORM_OBJ) != 0);
    DRW_shgroup_uniform_float_copy(grp, "gpStrokeIndexOffset", 0.0);
    DRW_shgroup_uniform_block(grp, "globalsBlock", G_draw.block_ubo);

    GPUShader *sh_curves = OVERLAY_shader_outline_prepass_curves();

    pd->outlines_curves_grp = grp = DRW_shgroup_create(sh_curves, psl->outlines_prepass_ps);
    DRW_shgroup_uniform_bool_copy(grp, "isTransform", (G.moving & G_TRANSFORM_OBJ) != 0);
    DRW_shgroup_uniform_block(grp, "globalsBlock", G_draw.block_ubo);
  }

  /* outlines_prepass_ps is still needed for selection of probes. */
  if (!(pd->v3d_flag & V3D_SELECT_OUTLINE)) {
    return;
  }

  {
    /* We can only do alpha blending with lineOutput just after clearing the buffer. */
    DRWState state = DRW_STATE_WRITE_COLOR | DRW_STATE_BLEND_ALPHA_PREMUL;
    DRW_PASS_CREATE(psl->outlines_detect_ps, state);

    GPUShader *sh = OVERLAY_shader_outline_detect();

    grp = DRW_shgroup_create(sh, psl->outlines_detect_ps);
    /* Don't occlude the "outline" detection pass if in xray mode (too much flickering). */
    DRW_shgroup_uniform_float_copy(grp, "alphaOcclu", (pd->xray_enabled) ? 1.0f : 0.35f);
    DRW_shgroup_uniform_bool_copy(grp, "doThickOutlines", do_expand);
    DRW_shgroup_uniform_bool_copy(grp, "doAntiAliasing", pd->antialiasing.enabled);
    DRW_shgroup_uniform_bool_copy(grp, "isXrayWires", pd->xray_enabled_and_not_wire);
    DRW_shgroup_uniform_texture_ref(grp, "outlineId", &txl->outlines_id_tx);
    DRW_shgroup_uniform_texture_ref(grp, "sceneDepth", &dtxl->depth);
    DRW_shgroup_uniform_texture_ref(grp, "outlineDepth", &txl->temp_depth_tx);
    DRW_shgroup_uniform_block(grp, "globalsBlock", G_draw.block_ubo);
    DRW_shgroup_call_procedural_triangles(grp, nullptr, 1);
  }
}

struct iterData {
  Object *ob;
  DRWShadingGroup *stroke_grp;
  int cfra;
  float plane[4];
};

static void gpencil_layer_cache_populate(bGPDlayer *gpl,
                                         bGPDframe * /*gpf*/,
                                         bGPDstroke * /*gps*/,
                                         void *thunk)
{
  iterData *iter = (iterData *)thunk;
  bGPdata *gpd = (bGPdata *)iter->ob->data;

  const bool is_screenspace = (gpd->flag & GP_DATA_STROKE_KEEPTHICKNESS) != 0;
  const bool is_stroke_order_3d = (gpd->draw_mode == GP_DRAWMODE_3D);

  float object_scale = mat4_to_scale(iter->ob->object_to_world);
  /* Negate thickness sign to tag that strokes are in screen space.
   * Convert to world units (by default, 1 meter = 2000 pixels). */
  float thickness_scale = (is_screenspace) ? -1.0f : (gpd->pixfactor / 2000.0f);

  GPUVertBuf *position_tx = DRW_cache_gpencil_position_buffer_get(iter->ob, iter->cfra);
  GPUVertBuf *color_tx = DRW_cache_gpencil_color_buffer_get(iter->ob, iter->cfra);

  DRWShadingGroup *grp = iter->stroke_grp = DRW_shgroup_create_sub(iter->stroke_grp);
  DRW_shgroup_uniform_bool_copy(grp, "gpStrokeOrder3d", is_stroke_order_3d);
  DRW_shgroup_uniform_float_copy(grp, "gpThicknessScale", object_scale);
  DRW_shgroup_uniform_float_copy(grp, "gpThicknessOffset", float(gpl->line_change));
  DRW_shgroup_uniform_float_copy(grp, "gpThicknessWorldScale", thickness_scale);
  DRW_shgroup_uniform_vec4_copy(grp, "gpDepthPlane", iter->plane);
  DRW_shgroup_buffer_texture(grp, "gp_pos_tx", position_tx);
  DRW_shgroup_buffer_texture(grp, "gp_col_tx", color_tx);
}

static void gpencil_stroke_cache_populate(bGPDlayer * /*gpl*/,
                                          bGPDframe * /*gpf*/,
                                          bGPDstroke *gps,
                                          void *thunk)
{
  iterData *iter = (iterData *)thunk;

  MaterialGPencilStyle *gp_style = BKE_gpencil_material_settings(iter->ob, gps->mat_nr + 1);

  bool hide_material = (gp_style->flag & GP_MATERIAL_HIDE) != 0;
  bool show_stroke = (gp_style->flag & GP_MATERIAL_STROKE_SHOW) != 0;
  /* TODO: What about simplify Fill? */
  bool show_fill = (gps->tot_triangles > 0) && (gp_style->flag & GP_MATERIAL_FILL_SHOW) != 0;

  if (hide_material) {
    return;
  }

  GPUBatch *geom = DRW_cache_gpencil_get(iter->ob, iter->cfra);

  if (show_fill) {
    int vfirst = gps->runtime.fill_start * 3;
    int vcount = gps->tot_triangles * 3;
    DRW_shgroup_call_range(iter->stroke_grp, iter->ob, geom, vfirst, vcount);
  }

  if (show_stroke) {
    int vfirst = gps->runtime.stroke_start * 3;
    bool is_cyclic = ((gps->flag & GP_STROKE_CYCLIC) != 0) && (gps->totpoints > 2);
    int vcount = (gps->totpoints + int(is_cyclic)) * 2 * 3;
    DRW_shgroup_call_range(iter->stroke_grp, iter->ob, geom, vfirst, vcount);
  }
}

static void OVERLAY_outline_gpencil(OVERLAY_PrivateData *pd, Object *ob)
{
  /* No outlines in edit mode. */
  bGPdata *gpd = (bGPdata *)ob->data;
  if (gpd && GPENCIL_ANY_MODE(gpd)) {
    return;
  }

  iterData iter{};
  iter.ob = ob;
  iter.stroke_grp = pd->outlines_gpencil_grp;
  iter.cfra = pd->cfra;

  if (gpd->draw_mode == GP_DRAWMODE_2D) {
    gpencil_depth_plane(ob, iter.plane);
  }

  BKE_gpencil_visible_stroke_advanced_iter(nullptr,
                                           ob,
                                           gpencil_layer_cache_populate,
                                           gpencil_stroke_cache_populate,
                                           &iter,
                                           false,
                                           pd->cfra);
}

static void OVERLAY_outline_volume(OVERLAY_PrivateData *pd, Object *ob)
{
  GPUBatch *geom = DRW_cache_volume_selection_surface_get(ob);
  if (geom == nullptr) {
    return;
  }

  DRWShadingGroup *shgroup = pd->outlines_grp;
  DRW_shgroup_call(shgroup, geom, ob);
}

static void OVERLAY_outline_curves(OVERLAY_PrivateData *pd, Object *ob)
{
  DRWShadingGroup *shgroup = pd->outlines_curves_grp;
  DRW_shgroup_curves_create_sub(ob, shgroup, nullptr);
}

static void OVERLAY_outline_pointcloud(OVERLAY_PrivateData *pd, Object *ob)
{
  if (pd->wireframe_mode) {
    /* Looks bad in this case. Could be relaxed if we draw a
     * wireframe of some sort in the future. */
    return;
  }

  DRWShadingGroup *shgroup = pd->outlines_ptcloud_grp;
  DRW_shgroup_pointcloud_create_sub(ob, shgroup, nullptr);
}

void OVERLAY_outline_cache_populate(OVERLAY_Data *vedata,
                                    Object *ob,
                                    OVERLAY_DupliData *dupli,
                                    bool init_dupli)
{
  OVERLAY_PrivateData *pd = vedata->stl->pd;
  const DRWContextState *draw_ctx = DRW_context_state_get();
  GPUBatch *geom;
  DRWShadingGroup *shgroup = nullptr;
  const bool draw_outline = ob->dt > OB_BOUNDBOX;

  /* Early exit: outlines of bounding boxes are not drawn. */
  if (!draw_outline) {
    return;
  }

  if (ob->type == OB_GPENCIL_LEGACY) {
    OVERLAY_outline_gpencil(pd, ob);
    return;
  }

  if (ob->type == OB_VOLUME) {
    OVERLAY_outline_volume(pd, ob);
    return;
  }

  if (ob->type == OB_CURVES) {
    OVERLAY_outline_curves(pd, ob);
    return;
  }

  if (ob->type == OB_POINTCLOUD) {
    OVERLAY_outline_pointcloud(pd, ob);
    return;
  }

  if (dupli && !init_dupli) {
    geom = dupli->outline_geom;
    shgroup = dupli->outline_shgrp;
  }
  else {
    /* This fixes only the biggest case which is a plane in ortho view. */
    int flat_axis = 0;
    bool is_flat_object_viewed_from_side = ((draw_ctx->rv3d->persp == RV3D_ORTHO) &&
                                            DRW_object_is_flat(ob, &flat_axis) &&
                                            DRW_object_axis_orthogonal_to_view(ob, flat_axis));

    if (pd->xray_enabled_and_not_wire || is_flat_object_viewed_from_side) {
      geom = DRW_cache_object_edge_detection_get(ob, nullptr);
    }
    else {
      geom = DRW_cache_object_surface_get(ob);
    }

    if (geom) {
      shgroup = pd->outlines_grp;
    }
  }

  if (shgroup && geom) {
    DRW_shgroup_call(shgroup, geom, ob);
  }

  if (init_dupli) {
    dupli->outline_shgrp = shgroup;
    dupli->outline_geom = geom;
  }
}

void OVERLAY_outline_draw(OVERLAY_Data *vedata)
{
  OVERLAY_FramebufferList *fbl = vedata->fbl;
  OVERLAY_PassList *psl = vedata->psl;
  const float clearcol[4] = {0.0f, 0.0f, 0.0f, 0.0f};

  bool do_outlines = psl->outlines_prepass_ps != nullptr &&
                     !DRW_pass_is_empty(psl->outlines_prepass_ps);

  if (DRW_state_is_fbo() && do_outlines) {
    DRW_stats_group_start("Outlines");

    /* Render filled polygon on a separate framebuffer */
    GPU_framebuffer_bind(fbl->outlines_prepass_fb);
    GPU_framebuffer_clear_color_depth_stencil(fbl->outlines_prepass_fb, clearcol, 1.0f, 0x00);
    DRW_draw_pass(psl->outlines_prepass_ps);

    /* Search outline pixels */
    GPU_framebuffer_bind(fbl->outlines_resolve_fb);
    DRW_draw_pass(psl->outlines_detect_ps);

    DRW_stats_group_end();
  }
}
