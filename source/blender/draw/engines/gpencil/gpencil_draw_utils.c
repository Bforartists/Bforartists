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

#include "BLI_polyfill_2d.h"

#include "DRW_render.h"

#include "BKE_gpencil.h"
#include "BKE_gpencil_modifier.h"
#include "BKE_image.h"
#include "BKE_material.h"
#include "BKE_paint.h"

#include "BLI_hash.h"

#include "ED_gpencil.h"

#include "DNA_gpencil_types.h"
#include "DNA_material_types.h"
#include "DNA_view3d_types.h"

/* If builtin shaders are needed */
#include "GPU_shader.h"
#include "GPU_texture.h"

/* For EvaluationContext... */
#include "DEG_depsgraph.h"
#include "DEG_depsgraph_query.h"

#include "IMB_imbuf_types.h"

#include "gpencil_engine.h"

#include "UI_resources.h"

/* fill type to communicate to shader */
#define SOLID 0
#define GRADIENT 1
#define RADIAL 2
#define CHECKER 3
#define TEXTURE 4
#define PATTERN 5

/* Verify if must fade object or not. */
static bool gpencil_fade_object_check(GPENCIL_StorageList *stl, Object *ob)
{
  const DRWContextState *draw_ctx = DRW_context_state_get();
  View3D *v3d = draw_ctx->v3d;
  const bool is_overlay = (bool)((v3d) && ((v3d->flag2 & V3D_HIDE_OVERLAYS) == 0) &&
                                 (v3d->gp_flag & V3D_GP_SHOW_PAPER));

  if ((!is_overlay) || (ob == draw_ctx->obact) ||
      ((v3d->gp_flag & V3D_GP_FADE_NOACTIVE_GPENCIL) == 0) ||
      (v3d->overlay.gpencil_paper_opacity == 1.0f)) {
    return false;
  }

  const bool playing = stl->storage->is_playing;
  const bool is_render = (bool)stl->storage->is_render;
  const bool is_mat_preview = (bool)stl->storage->is_mat_preview;
  const bool is_select = (bool)(DRW_state_is_select() || DRW_state_is_depth());

  return (bool)((!is_render) && (!playing) && (!is_mat_preview) && (!is_select));
}

/* Define Fade layer uniforms. */
static void gpencil_set_fade_layer_uniforms(
    GPENCIL_StorageList *stl, DRWShadingGroup *grp, Object *ob, bGPDlayer *gpl, const bool skip)
{
  const DRWContextState *draw_ctx = DRW_context_state_get();
  View3D *v3d = draw_ctx->v3d;
  const bool overlay = v3d != NULL ? (bool)((v3d->flag2 & V3D_HIDE_OVERLAYS) == 0) : true;
  const bool is_fade = (v3d) && (v3d->gp_flag & V3D_GP_FADE_NOACTIVE_LAYERS) &&
                       (draw_ctx->obact) && (draw_ctx->obact == ob) &&
                       ((gpl->flag & GP_LAYER_ACTIVE) == 0);

  const bool playing = stl->storage->is_playing;
  const bool is_render = (bool)stl->storage->is_render;
  const bool is_mat_preview = (bool)stl->storage->is_mat_preview;
  const bool is_select = (bool)(DRW_state_is_select() || DRW_state_is_depth());

  /* If drawing or not fading layer, skip. */
  if ((!overlay) || (skip) || (!is_fade) || (is_render) || (playing) || (is_mat_preview) ||
      (is_select)) {
    DRW_shgroup_uniform_int_copy(grp, "fade_layer", 0);
    return;
  }

  /* If layer is above active, use alpha (2) if below use mix with background (1). */
  if (stl->storage->is_ontop) {
    DRW_shgroup_uniform_int_copy(grp, "fade_layer", 2);
  }
  else {
    DRW_shgroup_uniform_int_copy(grp, "fade_layer", 1);
  }
  if (v3d) {
    DRW_shgroup_uniform_vec3(grp, "fade_color", v3d->shading.background_color, 1);
    DRW_shgroup_uniform_float(grp, "fade_layer_factor", &v3d->overlay.gpencil_fade_layer, 1);
  }
}

/* Define Fade object uniforms. */
static void gpencil_set_fade_ob_uniforms(View3D *v3d, DRWShadingGroup *grp, bool status)
{
  DRW_shgroup_uniform_bool_copy(grp, "fade_ob", status);
  if (v3d) {
    DRW_shgroup_uniform_vec3(grp, "fade_color", v3d->shading.background_color, 1);
    DRW_shgroup_uniform_float(grp, "fade_ob_factor", &v3d->overlay.gpencil_paper_opacity, 1);
  }
}

/* Get number of vertex for using in GPU VBOs */
static void gpencil_calc_vertex(GPENCIL_StorageList *stl,
                                tGPencilObjectCache *cache_ob,
                                GpencilBatchCache *cache,
                                bGPdata *gpd)
{
  if ((!cache->is_dirty) || (gpd == NULL)) {
    return;
  }

  Object *ob = cache_ob->ob;
  const DRWContextState *draw_ctx = DRW_context_state_get();
  const bool main_onion = draw_ctx->v3d != NULL ?
                              (draw_ctx->v3d->gp_flag & V3D_GP_SHOW_ONION_SKIN) :
                              true;
  const bool playing = stl->storage->is_playing;
  const bool overlay = draw_ctx->v3d != NULL ?
                           (bool)((draw_ctx->v3d->flag2 & V3D_HIDE_OVERLAYS) == 0) :
                           true;
  const bool do_onion = (bool)((gpd->flag & GP_DATA_STROKE_WEIGHTMODE) == 0) && overlay &&
                        main_onion && !playing && gpencil_onion_active(gpd);

  const bool is_multiedit = (bool)GPENCIL_MULTIEDIT_SESSIONS_ON(gpd);

  /* Onion skinning. */
  const int step = gpd->gstep;
  const int mode = gpd->onion_mode;
  const short onion_keytype = gpd->onion_keytype;

  cache_ob->tot_vertex = 0;
  cache_ob->tot_triangles = 0;
  int idx_eval = 0;

  for (bGPDlayer *gpl = gpd->layers.first; gpl; gpl = gpl->next) {
    bGPDframe *init_gpf = NULL;
    const bool is_onion = ((do_onion) && (gpl->onion_flag & GP_LAYER_ONIONSKIN));
    if (gpl->flag & GP_LAYER_HIDE) {
      idx_eval++;
      continue;
    }

    /* Relative onion mode needs to find the frame range before. */
    int frame_from = -9999;
    int frame_to = 9999;
    if ((is_onion) && (mode == GP_ONION_MODE_RELATIVE)) {
      /* 1) Found first Frame. */
      int idx = 0;
      if (gpl->actframe) {
        for (bGPDframe *gf = gpl->actframe->prev; gf; gf = gf->prev) {
          idx++;
          frame_from = gf->framenum;
          if (idx >= step) {
            break;
          }
        }
        /* 2) Found last Frame. */
        idx = 0;
        for (bGPDframe *gf = gpl->actframe->next; gf; gf = gf->next) {
          idx++;
          frame_to = gf->framenum;
          if (idx >= gpd->gstep_next) {
            break;
          }
        }
      }
    }

    /* If multiedit or onion skin need to count all frames of the layer. */
    if ((is_multiedit) || (is_onion)) {
      init_gpf = gpl->frames.first;
    }
    else {
      init_gpf = &ob->runtime.gpencil_evaluated_frames[idx_eval];
    }

    if (init_gpf == NULL) {
      continue;
    }

    for (bGPDframe *gpf = init_gpf; gpf; gpf = gpf->next) {
      for (bGPDstroke *gps = gpf->strokes.first; gps; gps = gps->next) {
        if (!is_onion) {
          if ((!is_multiedit) ||
              ((is_multiedit) && ((gpf == gpl->actframe) || (gpf->flag & GP_FRAME_SELECT)))) {
            cache_ob->tot_vertex += gps->totpoints + 3;
            cache_ob->tot_triangles += gps->totpoints - 1;
          }
        }
        else {
          bool select = ((is_multiedit) &&
                         ((gpf == gpl->actframe) || (gpf->flag & GP_FRAME_SELECT)));

          if (!select) {
            /* Only selected frames. */
            if ((mode == GP_ONION_MODE_SELECTED) && ((gpf->flag & GP_FRAME_SELECT) == 0)) {
              continue;
            }
            /* Verify keyframe type. */
            if ((onion_keytype > -1) && (gpf->key_type != onion_keytype)) {
              continue;
            }
            /* Absolute range. */
            if (mode == GP_ONION_MODE_ABSOLUTE) {
              if ((gpl->actframe) && (abs(gpl->actframe->framenum - gpf->framenum) > step)) {
                continue;
              }
            }
            /* Relative range. */
            if (mode == GP_ONION_MODE_RELATIVE) {
              if ((gpf->framenum < frame_from) || (gpf->framenum > frame_to)) {
                continue;
              }
            }
          }

          cache_ob->tot_vertex += gps->totpoints + 3;
          cache_ob->tot_triangles += gps->totpoints - 1;
        }
      }

      /* If not multiframe nor Onion skin, don't need follow counting. */
      if ((!is_multiedit) && (!is_onion)) {
        break;
      }
    }
    idx_eval++;
  }

  cache->b_fill.tot_vertex = cache_ob->tot_triangles * 3;
  cache->b_stroke.tot_vertex = cache_ob->tot_vertex;
  cache->b_point.tot_vertex = cache_ob->tot_vertex;
  cache->b_edit.tot_vertex = cache_ob->tot_vertex;
  cache->b_edlin.tot_vertex = cache_ob->tot_vertex;
}

/* Helper for doing all the checks on whether a stroke can be drawn */
static bool gpencil_can_draw_stroke(struct MaterialGPencilStyle *gp_style,
                                    const bGPDstroke *gps,
                                    const bool onion,
                                    const bool is_mat_preview)
{
  /* skip stroke if it doesn't have any valid data */
  if ((gps->points == NULL) || (gps->totpoints < 1) || (gp_style == NULL)) {
    return false;
  }

  /* if mat preview render always visible */
  if (is_mat_preview) {
    return true;
  }

  /* check if the color is visible */
  if ((gp_style == NULL) || (gp_style->flag & GP_STYLE_COLOR_HIDE) ||
      (onion && (gp_style->flag & GP_STYLE_COLOR_ONIONSKIN))) {
    return false;
  }

  /* stroke can be drawn */
  return true;
}

/* calc bounding box in 2d using flat projection data */
static void gpencil_calc_2d_bounding_box(const float (*points2d)[2],
                                         int totpoints,
                                         float minv[2],
                                         float maxv[2])
{
  minv[0] = points2d[0][0];
  minv[1] = points2d[0][1];
  maxv[0] = points2d[0][0];
  maxv[1] = points2d[0][1];

  for (int i = 1; i < totpoints; i++) {
    /* min */
    if (points2d[i][0] < minv[0]) {
      minv[0] = points2d[i][0];
    }
    if (points2d[i][1] < minv[1]) {
      minv[1] = points2d[i][1];
    }
    /* max */
    if (points2d[i][0] > maxv[0]) {
      maxv[0] = points2d[i][0];
    }
    if (points2d[i][1] > maxv[1]) {
      maxv[1] = points2d[i][1];
    }
  }
  /* use a perfect square */
  if (maxv[0] > maxv[1]) {
    maxv[1] = maxv[0];
  }
  else {
    maxv[0] = maxv[1];
  }
}

/* calc texture coordinates using flat projected points */
static void gpencil_calc_stroke_fill_uv(const float (*points2d)[2],
                                        int totpoints,
                                        const float minv[2],
                                        float maxv[2],
                                        float (*r_uv)[2])
{
  float d[2];
  d[0] = maxv[0] - minv[0];
  d[1] = maxv[1] - minv[1];
  for (int i = 0; i < totpoints; i++) {
    r_uv[i][0] = (points2d[i][0] - minv[0]) / d[0];
    r_uv[i][1] = (points2d[i][1] - minv[1]) / d[1];
  }
}

/* recalc the internal geometry caches for fill and uvs */
static void gpencil_recalc_geometry_caches(Object *ob,
                                           bGPDlayer *gpl,
                                           MaterialGPencilStyle *gp_style,
                                           bGPDstroke *gps)
{
  if (gps->flag & GP_STROKE_RECALC_GEOMETRY) {
    /* Calculate triangles cache for filling area (must be done only after changes) */
    if ((gps->tot_triangles == 0) || (gps->triangles == NULL)) {
      if ((gps->totpoints > 2) && (gp_style->flag & GP_STYLE_FILL_SHOW) &&
          ((gp_style->fill_rgba[3] > GPENCIL_ALPHA_OPACITY_THRESH) || (gp_style->fill_style > 0) ||
           (gpl->blend_mode != eGplBlendMode_Regular))) {
        gpencil_triangulate_stroke_fill(ob, gps);
      }
    }

    /* calc uv data along the stroke */
    ED_gpencil_calc_stroke_uv(ob, gps);

    /* clear flag */
    gps->flag &= ~GP_STROKE_RECALC_GEOMETRY;
  }
}

static void set_wireframe_color(Object *ob,
                                bGPDlayer *gpl,
                                View3D *v3d,
                                GPENCIL_StorageList *stl,
                                MaterialGPencilStyle *gp_style,
                                int id,
                                const bool is_fill)
{
  const DRWContextState *draw_ctx = DRW_context_state_get();
  World *world = draw_ctx->scene->world;

  float color[4];
  if (((gp_style->stroke_rgba[3] < GPENCIL_ALPHA_OPACITY_THRESH) ||
       (((gp_style->flag & GP_STYLE_STROKE_SHOW) == 0))) &&
      (gp_style->fill_rgba[3] >= GPENCIL_ALPHA_OPACITY_THRESH)) {
    copy_v4_v4(color, gp_style->fill_rgba);
  }
  else {
    copy_v4_v4(color, gp_style->stroke_rgba);
  }

  /* wire color */
  if ((v3d) && (id > -1)) {
    const char type = ((stl->shgroups[id].shading_type[0] == OB_WIRE) ?
                           v3d->shading.wire_color_type :
                           v3d->shading.color_type);
    /* if fill and wire, use background color */
    if ((is_fill) && (stl->shgroups[id].shading_type[0] == OB_WIRE)) {
      if (v3d->shading.background_type == V3D_SHADING_BACKGROUND_THEME) {
        UI_GetThemeColor4fv(TH_BACK, stl->shgroups[id].wire_color);
        stl->shgroups[id].wire_color[3] = 1.0f;
      }
      else if (v3d->shading.background_type == V3D_SHADING_BACKGROUND_WORLD) {
        color[0] = world->horr;
        color[1] = world->horg;
        color[2] = world->horb;
        color[3] = 1.0f;
        linearrgb_to_srgb_v4(stl->shgroups[id].wire_color, color);
      }
      else {
        copy_v3_v3(color, v3d->shading.background_color);
        color[3] = 1.0f;
        linearrgb_to_srgb_v4(stl->shgroups[id].wire_color, color);
      }
      return;
    }

    /* strokes */
    switch (type) {
      case V3D_SHADING_SINGLE_COLOR: {
        if (stl->shgroups[id].shading_type[0] == OB_WIRE) {
          UI_GetThemeColor4fv(TH_WIRE, color);
        }
        else {
          copy_v3_v3(color, v3d->shading.single_color);
        }
        color[3] = 1.0f;
        linearrgb_to_srgb_v4(stl->shgroups[id].wire_color, color);
        break;
      }
      case V3D_SHADING_OBJECT_COLOR: {
        copy_v4_v4(color, ob->color);
        color[3] = 1.0f;
        linearrgb_to_srgb_v4(stl->shgroups[id].wire_color, color);
        break;
      }
      case V3D_SHADING_RANDOM_COLOR: {
        uint gpl_hash = 1;
        uint ob_hash = BLI_ghashutil_strhash_p_murmur(ob->id.name);
        if (gpl) {
          gpl_hash = BLI_ghashutil_strhash_p_murmur(gpl->info);
        }

        float hue = BLI_hash_int_01(ob_hash * gpl_hash);
        float hsv[3] = {hue, 0.40f, 0.8f};
        float wire_col[3];
        hsv_to_rgb_v(hsv, &wire_col[0]);

        copy_v3_v3(stl->shgroups[id].wire_color, wire_col);
        stl->shgroups[id].wire_color[3] = 1.0f;
        break;
      }
      default: {
        copy_v4_v4(stl->shgroups[id].wire_color, color);
        break;
      }
    }
  }
  else {
    copy_v4_v4(stl->shgroups[id].wire_color, color);
  }

  /* if solid, the alpha must be set to alpha */
  if (stl->shgroups[id].shading_type[0] == OB_SOLID) {
    stl->shgroups[id].wire_color[3] = 1.0f;
  }
}

/* create shading group for filling */
static DRWShadingGroup *gpencil_shgroup_fill_create(GPENCIL_e_data *e_data,
                                                    GPENCIL_Data *vedata,
                                                    DRWPass *pass,
                                                    GPUShader *shader,
                                                    Object *ob,
                                                    float (*obmat)[4],
                                                    bGPdata *gpd,
                                                    bGPDlayer *gpl,
                                                    MaterialGPencilStyle *gp_style,
                                                    int id,
                                                    const int shading_type[2])
{
  GPENCIL_StorageList *stl = ((GPENCIL_Data *)vedata)->stl;
  const DRWContextState *draw_ctx = DRW_context_state_get();
  View3D *v3d = draw_ctx->v3d;

  /* e_data.gpencil_fill_sh */
  DRWShadingGroup *grp = DRW_shgroup_create(shader, pass);

  DRW_shgroup_uniform_mat4(grp, "gpModelMatrix", obmat);

  DRW_shgroup_uniform_vec4(grp, "color2", gp_style->mix_rgba, 1);

  /* set style type */
  switch (gp_style->fill_style) {
    case GP_STYLE_FILL_STYLE_SOLID:
      stl->shgroups[id].fill_style = SOLID;
      break;
    case GP_STYLE_FILL_STYLE_GRADIENT:
      if (gp_style->gradient_type == GP_STYLE_GRADIENT_LINEAR) {
        stl->shgroups[id].fill_style = GRADIENT;
      }
      else {
        stl->shgroups[id].fill_style = RADIAL;
      }
      break;
    case GP_STYLE_FILL_STYLE_CHECKER:
      stl->shgroups[id].fill_style = CHECKER;
      break;
    case GP_STYLE_FILL_STYLE_TEXTURE:
      if (gp_style->flag & GP_STYLE_FILL_PATTERN) {
        stl->shgroups[id].fill_style = PATTERN;
      }
      else {
        stl->shgroups[id].fill_style = TEXTURE;
      }
      break;
    default:
      stl->shgroups[id].fill_style = GP_STYLE_FILL_STYLE_SOLID;
      break;
  }
  DRW_shgroup_uniform_int(grp, "fill_type", &stl->shgroups[id].fill_style, 1);

  DRW_shgroup_uniform_float(grp, "mix_factor", &gp_style->mix_factor, 1);

  DRW_shgroup_uniform_float(grp, "gradient_angle", &gp_style->gradient_angle, 1);
  DRW_shgroup_uniform_float(grp, "gradient_radius", &gp_style->gradient_radius, 1);
  DRW_shgroup_uniform_float(grp, "pattern_gridsize", &gp_style->pattern_gridsize, 1);
  DRW_shgroup_uniform_vec2(grp, "gradient_scale", gp_style->gradient_scale, 1);
  DRW_shgroup_uniform_vec2(grp, "gradient_shift", gp_style->gradient_shift, 1);

  DRW_shgroup_uniform_float(grp, "texture_angle", &gp_style->texture_angle, 1);
  DRW_shgroup_uniform_vec2(grp, "texture_scale", gp_style->texture_scale, 1);
  DRW_shgroup_uniform_vec2(grp, "texture_offset", gp_style->texture_offset, 1);
  DRW_shgroup_uniform_float(grp, "texture_opacity", &gp_style->texture_opacity, 1);
  DRW_shgroup_uniform_float(grp, "layer_opacity", &gpl->opacity, 1);

  stl->shgroups[id].texture_mix = gp_style->flag & GP_STYLE_FILL_TEX_MIX ? 1 : 0;
  DRW_shgroup_uniform_int(grp, "texture_mix", &stl->shgroups[id].texture_mix, 1);

  stl->shgroups[id].texture_flip = gp_style->flag & GP_STYLE_COLOR_FLIP_FILL ? 1 : 0;
  DRW_shgroup_uniform_int(grp, "texture_flip", &stl->shgroups[id].texture_flip, 1);

  stl->shgroups[id].xray_mode = (ob->dtx & OB_DRAWXRAY) ? GP_XRAY_FRONT : GP_XRAY_3DSPACE;
  DRW_shgroup_uniform_int(grp, "xraymode", &stl->shgroups[id].xray_mode, 1);
  DRW_shgroup_uniform_int(grp, "drawmode", (const int *)&gpd->draw_mode, 1);

  /* viewport x-ray */
  stl->shgroups[id].is_xray = (ob->dt == OB_WIRE) ? 1 : stl->storage->is_xray;
  DRW_shgroup_uniform_int(grp, "viewport_xray", (const int *)&stl->shgroups[id].is_xray, 1);

  /* shading type */
  stl->shgroups[id].shading_type[0] = GPENCIL_USE_SOLID(stl) ? (int)OB_RENDER : shading_type[0];
  if (v3d) {
    stl->shgroups[id].shading_type[1] = ((stl->shgroups[id].shading_type[0] == OB_WIRE) ?
                                             v3d->shading.wire_color_type :
                                             v3d->shading.color_type);
  }

  DRW_shgroup_uniform_int(grp, "shading_type", &stl->shgroups[id].shading_type[0], 2);

  /* Fade layer uniforms. */
  gpencil_set_fade_layer_uniforms(stl, grp, ob, gpl, false);

  /* Fade object uniforms. */
  gpencil_set_fade_ob_uniforms(v3d, grp, gpencil_fade_object_check(stl, ob));

  /* wire color */
  set_wireframe_color(ob, gpl, v3d, stl, gp_style, id, true);
  DRW_shgroup_uniform_vec4(grp, "wire_color", stl->shgroups[id].wire_color, 1);

  /* image texture */
  if ((gp_style->flag & GP_STYLE_FILL_TEX_MIX) ||
      (gp_style->fill_style & GP_STYLE_FILL_STYLE_TEXTURE)) {
    ImBuf *ibuf;
    Image *image = gp_style->ima;
    ImageUser iuser = {NULL};
    void *lock;

    iuser.ok = true;

    ibuf = BKE_image_acquire_ibuf(image, &iuser, &lock);

    if (ibuf == NULL || ibuf->rect == NULL) {
      BKE_image_release_ibuf(image, ibuf, NULL);
    }
    else {
      GPUTexture *texture = GPU_texture_from_blender(gp_style->ima, &iuser, GL_TEXTURE_2D);
      DRW_shgroup_uniform_texture(grp, "myTexture", texture);
      DRW_shgroup_uniform_bool_copy(
          grp, "myTexturePremultiplied", (image->alpha_mode == IMA_ALPHA_PREMUL));

      stl->shgroups[id].texture_clamp = gp_style->flag & GP_STYLE_COLOR_TEX_CLAMP ? 1 : 0;
      DRW_shgroup_uniform_int(grp, "texture_clamp", &stl->shgroups[id].texture_clamp, 1);

      BKE_image_release_ibuf(image, ibuf, NULL);
    }
  }
  else {
    /* if no texture defined, need a blank texture to avoid errors in draw manager */
    DRW_shgroup_uniform_texture(grp, "myTexture", e_data->gpencil_blank_texture);
    stl->shgroups[id].texture_clamp = 0;
    DRW_shgroup_uniform_int(grp, "texture_clamp", &stl->shgroups[id].texture_clamp, 1);
  }

  return grp;
}

/* check if some onion is enabled */
bool gpencil_onion_active(bGPdata *gpd)
{
  for (bGPDlayer *gpl = gpd->layers.first; gpl; gpl = gpl->next) {
    if (gpl->onion_flag & GP_LAYER_ONIONSKIN) {
      return true;
    }
  }
  return false;
}

/* create shading group for strokes */
DRWShadingGroup *gpencil_shgroup_stroke_create(GPENCIL_e_data *e_data,
                                               GPENCIL_Data *vedata,
                                               DRWPass *pass,
                                               GPUShader *shader,
                                               Object *ob,
                                               float (*obmat)[4],
                                               bGPdata *gpd,
                                               bGPDlayer *gpl,
                                               bGPDstroke *gps,
                                               MaterialGPencilStyle *gp_style,
                                               int id,
                                               bool onion,
                                               const float scale,
                                               const int shading_type[2])
{
  GPENCIL_StorageList *stl = ((GPENCIL_Data *)vedata)->stl;
  const float *viewport_size = DRW_viewport_size_get();
  const DRWContextState *draw_ctx = DRW_context_state_get();
  View3D *v3d = draw_ctx->v3d;

  /* e_data.gpencil_stroke_sh */
  DRWShadingGroup *grp = DRW_shgroup_create(shader, pass);

  DRW_shgroup_uniform_vec2(grp, "Viewport", viewport_size, 1);

  DRW_shgroup_uniform_float(grp, "pixsize", stl->storage->pixsize, 1);

  DRW_shgroup_uniform_mat4(grp, "gpModelMatrix", obmat);

  /* avoid wrong values */
  if ((gpd) && (gpd->pixfactor == 0.0f)) {
    gpd->pixfactor = GP_DEFAULT_PIX_FACTOR;
  }

  /* object scale and depth */
  if ((ob) && (id > -1)) {
    stl->shgroups[id].obj_scale = scale;
    DRW_shgroup_uniform_float(grp, "objscale", &stl->shgroups[id].obj_scale, 1);
    stl->shgroups[id].keep_size = (int)((gpd) && (gpd->flag & GP_DATA_STROKE_KEEPTHICKNESS));
    DRW_shgroup_uniform_int(grp, "keep_size", &stl->shgroups[id].keep_size, 1);

    stl->shgroups[id].stroke_style = gp_style->stroke_style;
    stl->shgroups[id].color_type = GPENCIL_COLOR_SOLID;
    if ((gp_style->stroke_style == GP_STYLE_STROKE_STYLE_TEXTURE) && (!onion)) {
      stl->shgroups[id].color_type = GPENCIL_COLOR_TEXTURE;
      if (gp_style->flag & GP_STYLE_STROKE_PATTERN) {
        stl->shgroups[id].color_type = GPENCIL_COLOR_PATTERN;
      }
    }
    DRW_shgroup_uniform_int(grp, "color_type", &stl->shgroups[id].color_type, 1);
    DRW_shgroup_uniform_float(grp, "pixfactor", &gpd->pixfactor, 1);

    stl->shgroups[id].caps_mode[0] = gps->caps[0];
    stl->shgroups[id].caps_mode[1] = gps->caps[1];
    DRW_shgroup_uniform_int(grp, "caps_mode", &stl->shgroups[id].caps_mode[0], 2);

    stl->shgroups[id].gradient_f = gps->gradient_f;
    copy_v2_v2(stl->shgroups[id].gradient_s, gps->gradient_s);
    DRW_shgroup_uniform_float(grp, "gradient_f", &stl->shgroups[id].gradient_f, 1);

    /* viewport x-ray */
    stl->shgroups[id].is_xray = (ob->dt == OB_WIRE) ? 1 : stl->storage->is_xray;
    DRW_shgroup_uniform_int(grp, "viewport_xray", (const int *)&stl->shgroups[id].is_xray, 1);

    stl->shgroups[id].shading_type[0] = (GPENCIL_USE_SOLID(stl) || onion) ? (int)OB_RENDER :
                                                                            shading_type[0];
    if (v3d) {
      stl->shgroups[id].shading_type[1] = ((stl->shgroups[id].shading_type[0] == OB_WIRE) ?
                                               v3d->shading.wire_color_type :
                                               v3d->shading.color_type);
    }
    DRW_shgroup_uniform_int(grp, "shading_type", &stl->shgroups[id].shading_type[0], 2);

    /* Fade layer uniforms. */
    gpencil_set_fade_layer_uniforms(stl, grp, ob, gpl, false);

    /* Fade object uniforms. */
    gpencil_set_fade_ob_uniforms(v3d, grp, gpencil_fade_object_check(stl, ob));

    /* wire color */
    set_wireframe_color(ob, gpl, v3d, stl, gp_style, id, false);
    DRW_shgroup_uniform_vec4(grp, "wire_color", stl->shgroups[id].wire_color, 1);

    /* mix stroke factor */
    stl->shgroups[id].mix_stroke_factor = (gp_style->flag & GP_STYLE_STROKE_TEX_MIX) ?
                                              gp_style->mix_stroke_factor :
                                              0.0f;
    DRW_shgroup_uniform_float(grp, "mix_stroke_factor", &stl->shgroups[id].mix_stroke_factor, 1);
  }
  else {
    stl->storage->obj_scale = 1.0f;
    stl->storage->keep_size = 0;
    stl->storage->pixfactor = GP_DEFAULT_PIX_FACTOR;
    DRW_shgroup_uniform_float(grp, "objscale", &stl->storage->obj_scale, 1);
    DRW_shgroup_uniform_int(grp, "keep_size", &stl->storage->keep_size, 1);
    DRW_shgroup_uniform_int(grp, "color_type", &stl->storage->color_type, 1);
    if (gpd) {
      DRW_shgroup_uniform_float(grp, "pixfactor", &gpd->pixfactor, 1);
    }
    else {
      DRW_shgroup_uniform_float(grp, "pixfactor", &stl->storage->pixfactor, 1);
    }
    const int zero[2] = {0, 0};
    DRW_shgroup_uniform_int(grp, "caps_mode", &zero[0], 2);

    DRW_shgroup_uniform_float(grp, "gradient_f", &stl->storage->gradient_f, 1);

    /* viewport x-ray */
    DRW_shgroup_uniform_int(grp, "viewport_xray", &stl->storage->is_xray, 1);
    DRW_shgroup_uniform_int(grp, "shading_type", (const int *)&stl->storage->shade_render, 2);

    /* mix stroke factor */
    stl->storage->mix_stroke_factor = (gp_style->flag & GP_STYLE_STROKE_TEX_MIX) ?
                                          gp_style->mix_stroke_factor :
                                          0.0f;
    DRW_shgroup_uniform_float(grp, "mix_stroke_factor", &stl->storage->mix_stroke_factor, 1);
  }

  DRW_shgroup_uniform_vec4(grp, "colormix", gp_style->stroke_rgba, 1);

  if ((gpd) && (id > -1)) {
    stl->shgroups[id].xray_mode = (ob->dtx & OB_DRAWXRAY) ? GP_XRAY_FRONT : GP_XRAY_3DSPACE;
    DRW_shgroup_uniform_int(grp, "xraymode", &stl->shgroups[id].xray_mode, 1);
  }
  else {
    /* for drawing always on predefined z-depth */
    DRW_shgroup_uniform_int(grp, "xraymode", &stl->storage->xray, 1);
  }

  /* Fade layer uniforms. */
  gpencil_set_fade_layer_uniforms(stl, grp, ob, gpl, true);

  /* Fade object uniforms. */
  gpencil_set_fade_ob_uniforms(v3d, grp, false);

  /* image texture for pattern */
  if ((gp_style) && (gp_style->stroke_style == GP_STYLE_STROKE_STYLE_TEXTURE) && (!onion)) {
    ImBuf *ibuf;
    Image *image = gp_style->sima;
    ImageUser iuser = {NULL};
    void *lock;

    iuser.ok = true;

    ibuf = BKE_image_acquire_ibuf(image, &iuser, &lock);

    if (ibuf == NULL || ibuf->rect == NULL) {
      BKE_image_release_ibuf(image, ibuf, NULL);
    }
    else {
      GPUTexture *texture = GPU_texture_from_blender(gp_style->sima, &iuser, GL_TEXTURE_2D);
      DRW_shgroup_uniform_texture(grp, "myTexture", texture);
      DRW_shgroup_uniform_bool_copy(
          grp, "myTexturePremultiplied", (image->alpha_mode == IMA_ALPHA_PREMUL));

      BKE_image_release_ibuf(image, ibuf, NULL);
    }
  }
  else {
    /* if no texture defined, need a blank texture to avoid errors in draw manager */
    DRW_shgroup_uniform_texture(grp, "myTexture", e_data->gpencil_blank_texture);
  }

  return grp;
}

/* create shading group for points */
static DRWShadingGroup *gpencil_shgroup_point_create(GPENCIL_e_data *e_data,
                                                     GPENCIL_Data *vedata,
                                                     DRWPass *pass,
                                                     GPUShader *shader,
                                                     Object *ob,
                                                     float (*obmat)[4],
                                                     bGPdata *gpd,
                                                     bGPDlayer *gpl,
                                                     bGPDstroke *gps,
                                                     MaterialGPencilStyle *gp_style,
                                                     int id,
                                                     bool onion,
                                                     const float scale,
                                                     const int shading_type[2])
{
  GPENCIL_StorageList *stl = ((GPENCIL_Data *)vedata)->stl;
  const float *viewport_size = DRW_viewport_size_get();
  const DRWContextState *draw_ctx = DRW_context_state_get();
  View3D *v3d = draw_ctx->v3d;

  /* e_data.gpencil_stroke_sh */
  DRWShadingGroup *grp = DRW_shgroup_create(shader, pass);

  DRW_shgroup_uniform_vec2(grp, "Viewport", viewport_size, 1);
  DRW_shgroup_uniform_float(grp, "pixsize", stl->storage->pixsize, 1);

  DRW_shgroup_uniform_mat4(grp, "gpModelMatrix", obmat);

  /* avoid wrong values */
  if ((gpd) && (gpd->pixfactor == 0.0f)) {
    gpd->pixfactor = GP_DEFAULT_PIX_FACTOR;
  }

  /* object scale and depth */
  if ((ob) && (id > -1)) {
    stl->shgroups[id].obj_scale = scale;
    DRW_shgroup_uniform_float(grp, "objscale", &stl->shgroups[id].obj_scale, 1);
    stl->shgroups[id].keep_size = (int)((gpd) && (gpd->flag & GP_DATA_STROKE_KEEPTHICKNESS));
    DRW_shgroup_uniform_int(grp, "keep_size", &stl->shgroups[id].keep_size, 1);

    stl->shgroups[id].mode = gp_style->mode;
    stl->shgroups[id].stroke_style = gp_style->stroke_style;
    stl->shgroups[id].color_type = GPENCIL_COLOR_SOLID;
    if ((gp_style->stroke_style == GP_STYLE_STROKE_STYLE_TEXTURE) && (!onion)) {
      stl->shgroups[id].color_type = GPENCIL_COLOR_TEXTURE;
      if (gp_style->flag & GP_STYLE_STROKE_PATTERN) {
        stl->shgroups[id].color_type = GPENCIL_COLOR_PATTERN;
      }
    }
    DRW_shgroup_uniform_int(grp, "color_type", &stl->shgroups[id].color_type, 1);
    DRW_shgroup_uniform_int(grp, "mode", &stl->shgroups[id].mode, 1);
    DRW_shgroup_uniform_float(grp, "pixfactor", &gpd->pixfactor, 1);

    stl->shgroups[id].gradient_f = gps->gradient_f;
    copy_v2_v2(stl->shgroups[id].gradient_s, gps->gradient_s);
    DRW_shgroup_uniform_float(grp, "gradient_f", &stl->shgroups[id].gradient_f, 1);
    DRW_shgroup_uniform_vec2(grp, "gradient_s", stl->shgroups[id].gradient_s, 1);

    /* viewport x-ray */
    stl->shgroups[id].is_xray = (ob->dt == OB_WIRE) ? 1 : stl->storage->is_xray;
    DRW_shgroup_uniform_int(grp, "viewport_xray", (const int *)&stl->shgroups[id].is_xray, 1);

    stl->shgroups[id].shading_type[0] = (GPENCIL_USE_SOLID(stl) || onion) ? (int)OB_RENDER :
                                                                            shading_type[0];
    if (v3d) {
      stl->shgroups[id].shading_type[1] = ((stl->shgroups[id].shading_type[0] == OB_WIRE) ?
                                               v3d->shading.wire_color_type :
                                               v3d->shading.color_type);
    }
    DRW_shgroup_uniform_int(grp, "shading_type", &stl->shgroups[id].shading_type[0], 2);

    /* Fade layer uniforms. */
    gpencil_set_fade_layer_uniforms(stl, grp, ob, gpl, false);

    /* Fade object uniforms. */
    gpencil_set_fade_ob_uniforms(v3d, grp, gpencil_fade_object_check(stl, ob));

    /* wire color */
    set_wireframe_color(ob, gpl, v3d, stl, gp_style, id, false);
    DRW_shgroup_uniform_vec4(grp, "wire_color", stl->shgroups[id].wire_color, 1);

    /* mix stroke factor */
    stl->shgroups[id].mix_stroke_factor = (gp_style->flag & GP_STYLE_STROKE_TEX_MIX) ?
                                              gp_style->mix_stroke_factor :
                                              0.0f;
    DRW_shgroup_uniform_float(grp, "mix_stroke_factor", &stl->shgroups[id].mix_stroke_factor, 1);

    /* lock rotation of dots and boxes */
    stl->shgroups[id].alignment_mode = gp_style->alignment_mode;
    DRW_shgroup_uniform_int(grp, "alignment_mode", &stl->shgroups[id].alignment_mode, 1);
  }
  else {
    stl->storage->obj_scale = 1.0f;
    stl->storage->keep_size = 0;
    stl->storage->pixfactor = GP_DEFAULT_PIX_FACTOR;
    stl->storage->mode = gp_style->mode;
    DRW_shgroup_uniform_float(grp, "objscale", &stl->storage->obj_scale, 1);
    DRW_shgroup_uniform_int(grp, "keep_size", &stl->storage->keep_size, 1);
    DRW_shgroup_uniform_int(grp, "color_type", &stl->storage->color_type, 1);
    DRW_shgroup_uniform_int(grp, "mode", &stl->storage->mode, 1);
    if (gpd) {
      DRW_shgroup_uniform_float(grp, "pixfactor", &gpd->pixfactor, 1);
    }
    else {
      DRW_shgroup_uniform_float(grp, "pixfactor", &stl->storage->pixfactor, 1);
    }

    DRW_shgroup_uniform_float(grp, "gradient_f", &stl->storage->gradient_f, 1);
    DRW_shgroup_uniform_vec2(grp, "gradient_s", stl->storage->gradient_s, 1);

    /* viewport x-ray */
    DRW_shgroup_uniform_int(grp, "viewport_xray", &stl->storage->is_xray, 1);
    DRW_shgroup_uniform_int(grp, "shading_type", (const int *)&stl->storage->shade_render, 2);

    /* mix stroke factor */
    stl->storage->mix_stroke_factor = (gp_style->flag & GP_STYLE_STROKE_TEX_MIX) ?
                                          gp_style->mix_stroke_factor :
                                          0.0f;
    DRW_shgroup_uniform_float(grp, "mix_stroke_factor", &stl->storage->mix_stroke_factor, 1);

    /* lock rotation of dots and boxes */
    DRW_shgroup_uniform_int(grp, "alignment_mode", &stl->storage->alignment_mode, 1);
  }

  DRW_shgroup_uniform_vec4(grp, "colormix", gp_style->stroke_rgba, 1);

  if ((gpd) && (id > -1)) {
    stl->shgroups[id].xray_mode = (ob->dtx & OB_DRAWXRAY) ? GP_XRAY_FRONT : GP_XRAY_3DSPACE;
    DRW_shgroup_uniform_int(grp, "xraymode", (const int *)&stl->shgroups[id].xray_mode, 1);
  }
  else {
    /* for drawing always on predefined z-depth */
    DRW_shgroup_uniform_int(grp, "xraymode", &stl->storage->xray, 1);
  }

  /* Fade layer uniforms. */
  gpencil_set_fade_layer_uniforms(stl, grp, ob, gpl, true);

  /* Fade object uniforms. */
  gpencil_set_fade_ob_uniforms(v3d, grp, false);

  /* image texture */
  if ((gp_style) && (gp_style->stroke_style == GP_STYLE_STROKE_STYLE_TEXTURE) && (!onion)) {
    ImBuf *ibuf;
    Image *image = gp_style->sima;
    ImageUser iuser = {NULL};
    void *lock;

    iuser.ok = true;

    ibuf = BKE_image_acquire_ibuf(image, &iuser, &lock);

    if (ibuf == NULL || ibuf->rect == NULL) {
      BKE_image_release_ibuf(image, ibuf, NULL);
    }
    else {
      GPUTexture *texture = GPU_texture_from_blender(gp_style->sima, &iuser, GL_TEXTURE_2D);
      DRW_shgroup_uniform_texture(grp, "myTexture", texture);
      DRW_shgroup_uniform_bool_copy(
          grp, "myTexturePremultiplied", (image->alpha_mode == IMA_ALPHA_PREMUL));

      BKE_image_release_ibuf(image, ibuf, NULL);
    }
  }
  else {
    /* if no texture defined, need a blank texture to avoid errors in draw manager */
    DRW_shgroup_uniform_texture(grp, "myTexture", e_data->gpencil_blank_texture);
  }

  return grp;
}

/* add fill vertex info  */
static void gpencil_add_fill_vertexdata(GpencilBatchCache *cache,
                                        Object *ob,
                                        bGPDlayer *gpl,
                                        bGPDframe *gpf,
                                        bGPDstroke *gps,
                                        float opacity,
                                        const float tintcolor[4],
                                        const bool onion,
                                        const bool custonion)
{
  MaterialGPencilStyle *gp_style = BKE_material_gpencil_settings_get(ob, gps->mat_nr + 1);
  if (gps->totpoints >= 3) {
    float tfill[4];
    /* set color using material, tint color and opacity */
    interp_v3_v3v3(tfill, gps->runtime.tmp_fill_rgba, tintcolor, tintcolor[3]);
    tfill[3] = gps->runtime.tmp_fill_rgba[3] * opacity;
    if ((tfill[3] > GPENCIL_ALPHA_OPACITY_THRESH) || (gp_style->fill_style > 0) ||
        (gpl->blend_mode != eGplBlendMode_Regular)) {
      if (cache->is_dirty) {
        const float *color;
        if (!onion) {
          color = tfill;
        }
        else {
          if (custonion) {
            color = tintcolor;
          }
          else {
            ARRAY_SET_ITEMS(tfill, UNPACK3(gps->runtime.tmp_fill_rgba), tintcolor[3]);
            color = tfill;
          }
        }
        /* create vertex data */
        const int old_len = cache->b_fill.vbo_len;
        gpencil_get_fill_geom(&cache->b_fill, ob, gps, color);

        /* add to list of groups */
        if (old_len < cache->b_fill.vbo_len) {
          cache->grp_cache = gpencil_group_cache_add(cache->grp_cache,
                                                     gpl,
                                                     gpf,
                                                     gps,
                                                     eGpencilBatchGroupType_Fill,
                                                     onion,
                                                     cache->b_fill.vbo_len,
                                                     &cache->grp_size,
                                                     &cache->grp_used);
        }
      }
    }
  }
}

/* add stroke vertex info */
static void gpencil_add_stroke_vertexdata(GpencilBatchCache *cache,
                                          Object *ob,
                                          bGPDlayer *gpl,
                                          bGPDframe *gpf,
                                          bGPDstroke *gps,
                                          const float opacity,
                                          const float tintcolor[4],
                                          const bool onion,
                                          const bool custonion)
{
  float tcolor[4];
  float ink[4];
  short sthickness;
  MaterialGPencilStyle *gp_style = BKE_material_gpencil_settings_get(ob, gps->mat_nr + 1);
  const int alignment_mode = (gp_style) ? gp_style->alignment_mode : GP_STYLE_FOLLOW_PATH;

  /* set color using base color, tint color and opacity */
  if (cache->is_dirty) {
    if (!onion) {
      /* if special stroke, use fill color as stroke color */
      if (gps->flag & GP_STROKE_NOFILL) {
        interp_v3_v3v3(tcolor, gps->runtime.tmp_fill_rgba, tintcolor, tintcolor[3]);
        tcolor[3] = gps->runtime.tmp_fill_rgba[3] * opacity;
      }
      else {
        interp_v3_v3v3(tcolor, gps->runtime.tmp_stroke_rgba, tintcolor, tintcolor[3]);
        tcolor[3] = gps->runtime.tmp_stroke_rgba[3] * opacity;
      }
      copy_v4_v4(ink, tcolor);
    }
    else {
      if (custonion) {
        copy_v4_v4(ink, tintcolor);
      }
      else {
        ARRAY_SET_ITEMS(tcolor, UNPACK3(gps->runtime.tmp_stroke_rgba), opacity);
        copy_v4_v4(ink, tcolor);
      }
    }

    sthickness = gps->thickness + gpl->line_change;
    CLAMP_MIN(sthickness, 1);

    if ((gps->totpoints > 1) && (gp_style->mode == GP_STYLE_MODE_LINE)) {
      /* create vertex data */
      const int old_len = cache->b_stroke.vbo_len;
      gpencil_get_stroke_geom(&cache->b_stroke, gps, sthickness, ink);

      /* add to list of groups */
      if (old_len < cache->b_stroke.vbo_len) {
        cache->grp_cache = gpencil_group_cache_add(cache->grp_cache,
                                                   gpl,
                                                   gpf,
                                                   gps,
                                                   eGpencilBatchGroupType_Stroke,
                                                   onion,
                                                   cache->b_stroke.vbo_len,
                                                   &cache->grp_size,
                                                   &cache->grp_used);
      }
    }
    else {
      /* create vertex data */
      const int old_len = cache->b_point.vbo_len;
      gpencil_get_point_geom(&cache->b_point, gps, sthickness, ink, alignment_mode);

      /* add to list of groups */
      if (old_len < cache->b_point.vbo_len) {
        cache->grp_cache = gpencil_group_cache_add(cache->grp_cache,
                                                   gpl,
                                                   gpf,
                                                   gps,
                                                   eGpencilBatchGroupType_Point,
                                                   onion,
                                                   cache->b_point.vbo_len,
                                                   &cache->grp_size,
                                                   &cache->grp_used);
      }
    }
  }
}

/* add edit points vertex info */
static void gpencil_add_editpoints_vertexdata(GpencilBatchCache *cache,
                                              Object *ob,
                                              bGPdata *gpd,
                                              bGPDlayer *gpl,
                                              bGPDframe *gpf,
                                              bGPDstroke *gps)
{
  const DRWContextState *draw_ctx = DRW_context_state_get();
  View3D *v3d = draw_ctx->v3d;
  ToolSettings *ts = draw_ctx->scene->toolsettings;
  const bool use_sculpt_mask = (GPENCIL_SCULPT_MODE(gpd) && (ts->gpencil_selectmode_sculpt &
                                                             (GP_SCULPT_MASK_SELECTMODE_POINT |
                                                              GP_SCULPT_MASK_SELECTMODE_STROKE |
                                                              GP_SCULPT_MASK_SELECTMODE_SEGMENT)));

  const bool show_sculpt_points = (GPENCIL_SCULPT_MODE(gpd) &&
                                   (ts->gpencil_selectmode_sculpt &
                                    (GP_SCULPT_MASK_SELECTMODE_POINT |
                                     GP_SCULPT_MASK_SELECTMODE_SEGMENT)));

  MaterialGPencilStyle *gp_style = BKE_material_gpencil_settings_get(ob, gps->mat_nr + 1);

  /* alpha factor for edit points/line to make them more subtle */
  float edit_alpha = v3d->vertex_opacity;

  if (GPENCIL_ANY_EDIT_MODE(gpd)) {
    Object *obact = DRW_context_state_get()->obact;
    if ((!obact) || (obact->type != OB_GPENCIL)) {
      return;
    }
    const bool is_weight_paint = (gpd) && (gpd->flag & GP_DATA_STROKE_WEIGHTMODE);

    /* If Sculpt mode and the mask is disabled, the select must be hidden. */
    const bool hide_select = GPENCIL_SCULPT_MODE(gpd) && !use_sculpt_mask;

    /* Show Edit points if:
     *  Edit mode: Not in Stroke selection mode
     *  Sculpt mode: Not in Stroke mask mode and any other mask mode enabled
     *  Weight mode: Always
     */
    const bool show_points = (show_sculpt_points) || (is_weight_paint) ||
                             (GPENCIL_EDIT_MODE(gpd) &&
                              ((ts->gpencil_selectmode_edit != GP_SELECTMODE_STROKE) ||
                               (gps->totpoints == 1)));

    if (cache->is_dirty) {
      if ((obact == ob) && ((v3d->flag2 & V3D_HIDE_OVERLAYS) == 0) &&
          (v3d->gp_flag & V3D_GP_SHOW_EDIT_LINES) && (gps->totpoints > 1)) {

        /* line of the original stroke */
        gpencil_get_edlin_geom(&cache->b_edlin, gps, edit_alpha, hide_select);

        /* add to list of groups */
        cache->grp_cache = gpencil_group_cache_add(cache->grp_cache,
                                                   gpl,
                                                   gpf,
                                                   gps,
                                                   eGpencilBatchGroupType_Edlin,
                                                   false,
                                                   cache->b_edlin.vbo_len,
                                                   &cache->grp_size,
                                                   &cache->grp_used);
      }

      /* If the points are hidden return. */
      if ((!show_points) || (hide_select)) {
        return;
      }

      /* edit points */
      if ((gps->flag & GP_STROKE_SELECT) || (is_weight_paint)) {
        if ((gpl->flag & GP_LAYER_UNLOCK_COLOR) ||
            ((gp_style->flag & GP_STYLE_COLOR_LOCKED) == 0)) {
          if (obact == ob) {
            gpencil_get_edit_geom(&cache->b_edit, gps, edit_alpha, gpd->flag);

            /* add to list of groups */
            cache->grp_cache = gpencil_group_cache_add(cache->grp_cache,
                                                       gpl,
                                                       gpf,
                                                       gps,
                                                       eGpencilBatchGroupType_Edit,
                                                       false,
                                                       cache->b_edit.vbo_len,
                                                       &cache->grp_size,
                                                       &cache->grp_used);
          }
        }
      }
    }
  }
}

/* main function to draw strokes */
static void gpencil_draw_strokes(GpencilBatchCache *cache,
                                 GPENCIL_e_data *e_data,
                                 void *vedata,
                                 Object *ob,
                                 bGPdata *gpd,
                                 bGPDlayer *gpl,
                                 bGPDframe *gpf,
                                 const float opacity,
                                 const float tintcolor[4],
                                 const bool custonion,
                                 tGPencilObjectCache *cache_ob)
{
  GPENCIL_PassList *psl = ((GPENCIL_Data *)vedata)->psl;
  GPENCIL_StorageList *stl = ((GPENCIL_Data *)vedata)->stl;
  const DRWContextState *draw_ctx = DRW_context_state_get();
  Scene *scene = draw_ctx->scene;
  View3D *v3d = draw_ctx->v3d;
  bGPDstroke *gps;
  const bool is_multiedit = (bool)GPENCIL_MULTIEDIT_SESSIONS_ON(gpd);
  const bool playing = stl->storage->is_playing;
  const bool is_render = (bool)stl->storage->is_render;
  const bool is_mat_preview = (bool)stl->storage->is_mat_preview;
  const bool overlay_multiedit = v3d != NULL ? !(v3d->gp_flag & V3D_GP_SHOW_MULTIEDIT_LINES) :
                                               true;

  /* Get evaluation context */
  /* NOTE: We must check if C is valid, otherwise we get crashes when trying to save files
   * (i.e. the thumbnail offscreen rendering fails)
   */
  Depsgraph *depsgraph = DRW_context_state_get()->depsgraph;

  /* get parent matrix and save as static data */
  if ((cache_ob != NULL) && (cache_ob->is_dup_ob)) {
    copy_m4_m4(gpf->runtime.parent_obmat, cache_ob->obmat);
  }
  else {
    ED_gpencil_parent_location(depsgraph, ob, gpd, gpl, gpf->runtime.parent_obmat);
  }

  for (gps = gpf->strokes.first; gps; gps = gps->next) {
    MaterialGPencilStyle *gp_style = BKE_material_gpencil_settings_get(ob, gps->mat_nr + 1);

    /* check if stroke can be drawn */
    if (gpencil_can_draw_stroke(gp_style, gps, false, is_mat_preview) == false) {
      continue;
    }

    /* Copy color to temp fields. */
    if ((is_multiedit) && (gp_style)) {
      copy_v4_v4(gps->runtime.tmp_stroke_rgba, gp_style->stroke_rgba);
      copy_v4_v4(gps->runtime.tmp_fill_rgba, gp_style->fill_rgba);
    }

    /* be sure recalc all cache in source stroke to avoid recalculation when frame change
     * and improve fps */
    gpencil_recalc_geometry_caches(
        ob, gpl, gp_style, (gps->runtime.gps_orig) ? gps->runtime.gps_orig : gps);

    /* if the fill has any value, it's considered a fill and is not drawn if simplify fill is
     * enabled */
    if ((stl->storage->simplify_fill) &&
        (scene->r.simplify_gpencil & SIMPLIFY_GPENCIL_REMOVE_FILL_LINE)) {
      if ((gp_style->fill_rgba[3] > GPENCIL_ALPHA_OPACITY_THRESH) ||
          (gp_style->fill_style > GP_STYLE_FILL_STYLE_SOLID) ||
          (gpl->blend_mode != eGplBlendMode_Regular)) {

        continue;
      }
    }

    if ((gpl->actframe && (gpl->actframe->framenum == gpf->framenum)) || (!is_multiedit) ||
        (overlay_multiedit)) {
      /* hide any blend layer */
      if ((!stl->storage->simplify_blend) || (gpl->blend_mode == eGplBlendMode_Regular)) {
        /* fill */
        if ((gp_style->flag & GP_STYLE_FILL_SHOW) && (!stl->storage->simplify_fill) &&
            ((gps->flag & GP_STROKE_NOFILL) == 0)) {
          gpencil_add_fill_vertexdata(
              cache, ob, gpl, gpf, gps, opacity, tintcolor, false, custonion);
        }
        /* stroke
         * No fill strokes, must show stroke always or if the total points is lower than 3,
         * because the stroke cannot be filled and it would be invisible. */
        if (((gp_style->flag & GP_STYLE_STROKE_SHOW) || (gps->flag & GP_STROKE_NOFILL) ||
             (gps->totpoints < 3)) &&
            ((gp_style->stroke_rgba[3] > GPENCIL_ALPHA_OPACITY_THRESH) ||
             (gpl->blend_mode == eGplBlendMode_Regular))) {
          /* recalc strokes uv (geometry can be changed by modifiers) */
          if (gps->flag & GP_STROKE_RECALC_GEOMETRY) {
            ED_gpencil_calc_stroke_uv(ob, gps);
          }

          gpencil_add_stroke_vertexdata(
              cache, ob, gpl, gpf, gps, opacity, tintcolor, false, custonion);
        }
      }
    }

    /* edit points (only in edit mode and not play animation not render) */
    if ((draw_ctx->obact == ob) && (!playing) && (!is_render) && (!cache_ob->is_dup_ob)) {
      if ((gpl->flag & GP_LAYER_LOCKED) == 0) {
        if (!stl->g_data->shgrps_edit_line) {
          stl->g_data->shgrps_edit_line = DRW_shgroup_create(e_data->gpencil_line_sh,
                                                             psl->edit_pass);
          DRW_shgroup_uniform_mat4(stl->g_data->shgrps_edit_line, "gpModelMatrix", ob->obmat);
        }
        if (!stl->g_data->shgrps_edit_point) {
          stl->g_data->shgrps_edit_point = DRW_shgroup_create(e_data->gpencil_edit_point_sh,
                                                              psl->edit_pass);
          const float *viewport_size = DRW_viewport_size_get();
          DRW_shgroup_uniform_vec2(stl->g_data->shgrps_edit_point, "Viewport", viewport_size, 1);
          DRW_shgroup_uniform_mat4(stl->g_data->shgrps_edit_point, "gpModelMatrix", ob->obmat);
        }

        gpencil_add_editpoints_vertexdata(cache, ob, gpd, gpl, gpf, gps);
      }
    }
  }
}

/* get alpha factor for onion strokes */
static void gpencil_get_onion_alpha(float color[4], bGPdata *gpd)
{
#define MIN_ALPHA_VALUE 0.01f

  /* if fade is disabled, opacity is equal in all frames */
  if ((gpd->onion_flag & GP_ONION_FADE) == 0) {
    color[3] = gpd->onion_factor;
  }
  else {
    /* add override opacity factor */
    color[3] += gpd->onion_factor - 0.5f;
  }

  CLAMP(color[3], MIN_ALPHA_VALUE, 1.0f);
}

/* function to draw strokes for onion only */
static void gpencil_draw_onion_strokes(GpencilBatchCache *cache,
                                       void *vedata,
                                       Object *ob,
                                       bGPdata *gpd,
                                       bGPDlayer *gpl,
                                       bGPDframe *gpf,
                                       const float opacity,
                                       const float tintcolor[4],
                                       const bool custonion)
{
  GPENCIL_StorageList *stl = ((GPENCIL_Data *)vedata)->stl;
  Depsgraph *depsgraph = DRW_context_state_get()->depsgraph;

  /* get parent matrix and save as static data */
  ED_gpencil_parent_location(depsgraph, ob, gpd, gpl, gpf->runtime.parent_obmat);

  for (bGPDstroke *gps = gpf->strokes.first; gps; gps = gps->next) {
    MaterialGPencilStyle *gp_style = BKE_material_gpencil_settings_get(ob, gps->mat_nr + 1);
    if (gp_style == NULL) {
      continue;
    }
    copy_v4_v4(gps->runtime.tmp_stroke_rgba, gp_style->stroke_rgba);
    copy_v4_v4(gps->runtime.tmp_fill_rgba, gp_style->fill_rgba);

    int id = stl->storage->shgroup_id;
    /* check if stroke can be drawn */
    if (gpencil_can_draw_stroke(gp_style, gps, true, false) == false) {
      continue;
    }
    /* limit the number of shading groups */
    if (id >= GPENCIL_MAX_SHGROUPS) {
      continue;
    }

    /* stroke */
    gpencil_add_stroke_vertexdata(cache, ob, gpl, gpf, gps, opacity, tintcolor, true, custonion);

    stl->storage->shgroup_id++;
  }
}

/* draw onion-skinning for a layer */
static void gpencil_draw_onionskins(GpencilBatchCache *cache,
                                    void *vedata,
                                    Object *ob,
                                    bGPdata *gpd,
                                    bGPDlayer *gpl,
                                    bGPDframe *gpf)
{

  const float default_color[3] = {UNPACK3(U.gpencil_new_layer_col)};
  const float alpha = 1.0f;
  float color[4];
  int idx;
  float fac = 1.0f;
  int step = 0;
  bool colflag = false;
  const int mode = gpd->onion_mode;
  bGPDframe *gpf_loop = ((gpd->onion_flag & GP_ONION_LOOP) && (mode != GP_ONION_MODE_SELECTED)) ?
                            gpl->frames.first :
                            NULL;
  int last = gpf->framenum;

  colflag = (gpd->onion_flag & GP_ONION_GHOST_PREVCOL) != 0;
  const short onion_keytype = gpd->onion_keytype;
  /* -------------------------------
   * 1) Draw Previous Frames First
   * ------------------------------- */
  step = gpd->gstep;

  if (gpd->onion_flag & GP_ONION_GHOST_PREVCOL) {
    copy_v3_v3(color, gpd->gcolor_prev);
  }
  else {
    copy_v3_v3(color, default_color);
  }

  idx = 0;
  for (bGPDframe *gf = gpf->prev; gf; gf = gf->prev) {
    /* only selected frames */
    if ((mode == GP_ONION_MODE_SELECTED) && ((gf->flag & GP_FRAME_SELECT) == 0)) {
      continue;
    }
    /* verify keyframe type */
    if ((onion_keytype > -1) && (gf->key_type != onion_keytype)) {
      continue;
    }
    /* absolute range */
    if (mode == GP_ONION_MODE_ABSOLUTE) {
      if ((gpf->framenum - gf->framenum) > step) {
        break;
      }
    }
    /* relative range */
    if (mode == GP_ONION_MODE_RELATIVE) {
      idx++;
      if (idx > step) {
        break;
      }
    }
    /* alpha decreases with distance from curframe index */
    if (mode != GP_ONION_MODE_SELECTED) {
      if (mode == GP_ONION_MODE_ABSOLUTE) {
        fac = 1.0f - ((float)(gpf->framenum - gf->framenum) / (float)(step + 1));
      }
      else {
        fac = 1.0f - ((float)idx / (float)(step + 1));
      }
      color[3] = alpha * fac * 0.66f;
    }
    else {
      idx++;
      fac = alpha - ((1.1f - (1.0f / (float)idx)) * 0.66f);
      color[3] = fac;
    }

    /* if loop option, save the frame to use later */
    if ((mode == GP_ONION_MODE_SELECTED) && (gpd->onion_flag & GP_ONION_LOOP)) {
      gpf_loop = gf;
    }

    gpencil_get_onion_alpha(color, gpd);
    gpencil_draw_onion_strokes(cache, vedata, ob, gpd, gpl, gf, color[3], color, colflag);
  }
  /* -------------------------------
   * 2) Now draw next frames
   * ------------------------------- */
  step = gpd->gstep_next;

  if (gpd->onion_flag & GP_ONION_GHOST_NEXTCOL) {
    copy_v3_v3(color, gpd->gcolor_next);
  }
  else {
    copy_v3_v3(color, default_color);
  }

  idx = 0;
  for (bGPDframe *gf = gpf->next; gf; gf = gf->next) {
    /* only selected frames */
    if ((mode == GP_ONION_MODE_SELECTED) && ((gf->flag & GP_FRAME_SELECT) == 0)) {
      continue;
    }
    /* verify keyframe type */
    if ((onion_keytype > -1) && (gf->key_type != onion_keytype)) {
      continue;
    }
    /* absolute range */
    if (mode == GP_ONION_MODE_ABSOLUTE) {
      if ((gf->framenum - gpf->framenum) > step) {
        break;
      }
    }
    /* relative range */
    if (mode == GP_ONION_MODE_RELATIVE) {
      idx++;
      if (idx > step) {
        break;
      }
    }
    /* alpha decreases with distance from curframe index */
    if (mode != GP_ONION_MODE_SELECTED) {
      if (mode == GP_ONION_MODE_ABSOLUTE) {
        fac = 1.0f - ((float)(gf->framenum - gpf->framenum) / (float)(step + 1));
      }
      else {
        fac = 1.0f - ((float)idx / (float)(step + 1));
      }
      color[3] = alpha * fac * 0.66f;
    }
    else {
      idx++;
      fac = alpha - ((1.1f - (1.0f / (float)idx)) * 0.66f);
      color[3] = fac;
    }

    gpencil_get_onion_alpha(color, gpd);
    gpencil_draw_onion_strokes(cache, vedata, ob, gpd, gpl, gf, color[3], color, colflag);
    if (last < gf->framenum) {
      last = gf->framenum;
    }
  }

  /* Draw first frame in blue for loop mode */
  if ((gpd->onion_flag & GP_ONION_LOOP) && (gpf_loop != NULL)) {
    if ((last == gpf->framenum) || (gpf->next == NULL)) {
      gpencil_get_onion_alpha(color, gpd);
      gpencil_draw_onion_strokes(cache, vedata, ob, gpd, gpl, gpf_loop, color[3], color, colflag);
    }
  }
}

/* Triangulate stroke for high quality fill (this is done only if cache is null or stroke was
 * modified) */
void gpencil_triangulate_stroke_fill(Object *ob, bGPDstroke *gps)
{
  BLI_assert(gps->totpoints >= 3);

  bGPdata *gpd = (bGPdata *)ob->data;

  /* allocate memory for temporary areas */
  gps->tot_triangles = gps->totpoints - 2;
  uint(*tmp_triangles)[3] = MEM_mallocN(sizeof(*tmp_triangles) * gps->tot_triangles,
                                        "GP Stroke temp triangulation");
  float(*points2d)[2] = MEM_mallocN(sizeof(*points2d) * gps->totpoints,
                                    "GP Stroke temp 2d points");
  float(*uv)[2] = MEM_mallocN(sizeof(*uv) * gps->totpoints, "GP Stroke temp 2d uv data");

  int direction = 0;

  /* convert to 2d and triangulate */
  BKE_gpencil_stroke_2d_flat(gps->points, gps->totpoints, points2d, &direction);
  BLI_polyfill_calc(points2d, (uint)gps->totpoints, direction, tmp_triangles);

  /* calc texture coordinates automatically */
  float minv[2];
  float maxv[2];
  /* first needs bounding box data */
  if (gpd->flag & GP_DATA_UV_ADAPTIVE) {
    gpencil_calc_2d_bounding_box(points2d, gps->totpoints, minv, maxv);
  }
  else {
    ARRAY_SET_ITEMS(minv, -1.0f, -1.0f);
    ARRAY_SET_ITEMS(maxv, 1.0f, 1.0f);
  }

  /* calc uv data */
  gpencil_calc_stroke_fill_uv(points2d, gps->totpoints, minv, maxv, uv);

  /* Number of triangles */
  gps->tot_triangles = gps->totpoints - 2;
  /* save triangulation data in stroke cache */
  if (gps->tot_triangles > 0) {
    if (gps->triangles == NULL) {
      gps->triangles = MEM_callocN(sizeof(*gps->triangles) * gps->tot_triangles,
                                   "GP Stroke triangulation");
    }
    else {
      gps->triangles = MEM_recallocN(gps->triangles, sizeof(*gps->triangles) * gps->tot_triangles);
    }

    for (int i = 0; i < gps->tot_triangles; i++) {
      bGPDtriangle *stroke_triangle = &gps->triangles[i];
      memcpy(gps->triangles[i].verts, tmp_triangles[i], sizeof(uint[3]));
      /* copy texture coordinates */
      copy_v2_v2(stroke_triangle->uv[0], uv[tmp_triangles[i][0]]);
      copy_v2_v2(stroke_triangle->uv[1], uv[tmp_triangles[i][1]]);
      copy_v2_v2(stroke_triangle->uv[2], uv[tmp_triangles[i][2]]);
    }
  }
  else {
    /* No triangles needed - Free anything allocated previously */
    if (gps->triangles) {
      MEM_freeN(gps->triangles);
    }

    gps->triangles = NULL;
  }

  /* disable recalculation flag */
  if (gps->flag & GP_STROKE_RECALC_GEOMETRY) {
    gps->flag &= ~GP_STROKE_RECALC_GEOMETRY;
  }

  /* clear memory */
  MEM_SAFE_FREE(tmp_triangles);
  MEM_SAFE_FREE(points2d);
  MEM_SAFE_FREE(uv);
}

/* Check if stencil is required */
static bool gpencil_is_stencil_required(MaterialGPencilStyle *gp_style)
{
  return (bool)((gp_style->stroke_style == GP_STYLE_STROKE_STYLE_SOLID) &&
                ((gp_style->flag & GP_STYLE_DISABLE_STENCIL) == 0));
}

/* draw stroke in drawing buffer */
void gpencil_populate_buffer_strokes(GPENCIL_e_data *e_data,
                                     void *vedata,
                                     ToolSettings *ts,
                                     Object *ob)
{
  GPENCIL_PassList *psl = ((GPENCIL_Data *)vedata)->psl;
  GPENCIL_StorageList *stl = ((GPENCIL_Data *)vedata)->stl;
  const DRWContextState *draw_ctx = DRW_context_state_get();
  View3D *v3d = draw_ctx->v3d;
  const bool overlay = v3d != NULL ? (bool)((v3d->flag2 & V3D_HIDE_OVERLAYS) == 0) : true;
  Brush *brush = BKE_paint_brush(&ts->gp_paint->paint);
  const bool is_paint_tool = (bool)((brush) && (brush->gpencil_tool == GPAINT_TOOL_DRAW));
  bGPdata *gpd_eval = ob->data;
  /* need the original to avoid cow overhead while drawing */
  bGPdata *gpd = (bGPdata *)DEG_get_original_id(&gpd_eval->id);

  MaterialGPencilStyle *gp_style = NULL;
  float obscale = mat4_to_scale(ob->obmat);

  /* use the brush material */
  Material *ma = BKE_gpencil_object_material_get_from_brush(ob, brush);
  if (ma != NULL) {
    gp_style = ma->gp_style;
  }
  /* this is not common, but avoid any special situations when brush could be without material */
  if (gp_style == NULL) {
    gp_style = BKE_material_gpencil_settings_get(ob, ob->actcol);
  }

  static float unit_mat[4][4] = {
      {1.0, 0.0, 0.0, 0.0}, {0.0, 1.0, 0.0, 0.0}, {0.0, 0.0, 1.0, 0.0}, {0.0, 0.0, 0.0, 1.0}};

  /* drawing strokes */
  /* Check if may need to draw the active stroke cache, only if this layer is the active layer
   * that is being edited. (Stroke buffer is currently stored in gp-data)
   */
  if (gpd->runtime.sbuffer_used > 0) {
    if ((gpd->runtime.sbuffer_sflag & GP_STROKE_ERASER) == 0) {
      /* It should also be noted that sbuffer contains temporary point types
       * i.e. tGPspoints NOT bGPDspoints
       */
      short lthick = brush->size * obscale;

      /* save gradient info */
      stl->storage->gradient_f = brush->gpencil_settings->gradient_f;
      copy_v2_v2(stl->storage->gradient_s, brush->gpencil_settings->gradient_s);
      stl->storage->alignment_mode = (gp_style) ? gp_style->alignment_mode : GP_STYLE_FOLLOW_PATH;

      /* if only one point, don't need to draw buffer because the user has no time to see it */
      if (gpd->runtime.sbuffer_used > 1) {
        if ((gp_style) && (gp_style->mode == GP_STYLE_MODE_LINE)) {
          stl->g_data->shgrps_drawing_stroke = gpencil_shgroup_stroke_create(
              e_data,
              vedata,
              psl->drawing_pass,
              e_data->gpencil_stroke_sh,
              NULL,
              unit_mat,
              gpd,
              NULL,
              NULL,
              gp_style,
              -1,
              false,
              1.0f,
              (const int *)stl->storage->shade_render);

          if (gpencil_is_stencil_required(gp_style)) {
            DRW_shgroup_stencil_mask(stl->g_data->shgrps_drawing_stroke, 0x01);
          }
          else {
            /* Disable stencil for this type */
            DRW_shgroup_state_disable(stl->g_data->shgrps_drawing_stroke,
                                      DRW_STATE_WRITE_STENCIL | DRW_STATE_STENCIL_NEQUAL);
          }
        }
        else {
          stl->g_data->shgrps_drawing_stroke = gpencil_shgroup_point_create(
              e_data,
              vedata,
              psl->drawing_pass,
              e_data->gpencil_point_sh,
              NULL,
              unit_mat,
              gpd,
              NULL,
              NULL,
              gp_style,
              -1,
              false,
              1.0f,
              (const int *)stl->storage->shade_render);
          /* Disable stencil for this type */
          DRW_shgroup_state_disable(stl->g_data->shgrps_drawing_stroke,
                                    DRW_STATE_WRITE_STENCIL | DRW_STATE_STENCIL_NEQUAL);
        }

        /* use unit matrix because the buffer is in screen space and does not need conversion */
        if (gpd->runtime.mode == GP_STYLE_MODE_LINE) {
          stl->g_data->batch_buffer_stroke = gpencil_get_buffer_stroke_geom(gpd, lthick);
        }
        else {
          stl->g_data->batch_buffer_stroke = gpencil_get_buffer_point_geom(gpd, lthick);
        }

        /* buffer strokes, must show stroke always */
        DRW_shgroup_call(
            stl->g_data->shgrps_drawing_stroke, stl->g_data->batch_buffer_stroke, NULL);

        if ((gpd->runtime.sbuffer_used >= 3) &&
            (gpd->runtime.sfill[3] > GPENCIL_ALPHA_OPACITY_THRESH) &&
            ((gpd->runtime.sbuffer_sflag & GP_STROKE_NOFILL) == 0) &&
            ((brush->gpencil_settings->flag & GP_BRUSH_DISSABLE_LASSO) == 0) &&
            (gp_style->flag & GP_STYLE_FILL_SHOW)) {
          /* if not solid, fill is simulated with solid color */
          if (gpd->runtime.bfill_style > 0) {
            gpd->runtime.sfill[3] = 0.5f;
          }
          stl->g_data->shgrps_drawing_fill = DRW_shgroup_create(e_data->gpencil_drawing_fill_sh,
                                                                psl->drawing_pass);
          /* Disable stencil for this type */
          DRW_shgroup_state_disable(stl->g_data->shgrps_drawing_fill,
                                    DRW_STATE_WRITE_STENCIL | DRW_STATE_STENCIL_NEQUAL);

          stl->g_data->batch_buffer_fill = gpencil_get_buffer_fill_geom(gpd);
          DRW_shgroup_call(stl->g_data->shgrps_drawing_fill, stl->g_data->batch_buffer_fill, NULL);
        }
      }
    }
  }

  /* control points for primitives and speed guide */
  const bool is_cppoint = (gpd->runtime.tot_cp_points > 0);
  const bool is_speed_guide = (ts->gp_sculpt.guide.use_guide &&
                               (draw_ctx->object_mode == OB_MODE_PAINT_GPENCIL));
  const bool is_show_gizmo = (((v3d->gizmo_flag & V3D_GIZMO_HIDE) == 0) &&
                              ((v3d->gizmo_flag & V3D_GIZMO_HIDE_TOOL) == 0));

  if ((overlay) && (is_paint_tool) && (is_cppoint || is_speed_guide) && (is_show_gizmo) &&
      ((gpd->runtime.sbuffer_sflag & GP_STROKE_ERASER) == 0)) {
    DRWShadingGroup *shgrp = DRW_shgroup_create(e_data->gpencil_edit_point_sh, psl->drawing_pass);
    const float *viewport_size = DRW_viewport_size_get();
    DRW_shgroup_uniform_vec2(shgrp, "Viewport", viewport_size, 1);
    DRW_shgroup_uniform_mat4(shgrp, "gpModelMatrix", unit_mat);

    /* Disable stencil for this type */
    DRW_shgroup_state_disable(shgrp, DRW_STATE_WRITE_STENCIL | DRW_STATE_STENCIL_NEQUAL);
    stl->g_data->batch_buffer_ctrlpoint = gpencil_get_buffer_ctrlpoint_geom(gpd);

    DRW_shgroup_call(shgrp, stl->g_data->batch_buffer_ctrlpoint, NULL);
  }
}

/* create all missing batches */
static void gpencil_batches_ensure(GpencilBatchCache *cache)
{
  if ((cache->b_point.vbo) && (cache->b_point.batch == NULL)) {
    cache->b_point.batch = GPU_batch_create_ex(
        GPU_PRIM_POINTS, cache->b_point.vbo, NULL, GPU_BATCH_OWNS_VBO);
  }
  if ((cache->b_stroke.vbo) && (cache->b_stroke.batch == NULL)) {
    cache->b_stroke.batch = GPU_batch_create_ex(
        GPU_PRIM_LINE_STRIP_ADJ, cache->b_stroke.vbo, NULL, GPU_BATCH_OWNS_VBO);
  }
  if ((cache->b_fill.vbo) && (cache->b_fill.batch == NULL)) {
    cache->b_fill.batch = GPU_batch_create_ex(
        GPU_PRIM_TRIS, cache->b_fill.vbo, NULL, GPU_BATCH_OWNS_VBO);
  }
  if ((cache->b_edit.vbo) && (cache->b_edit.batch == NULL)) {
    cache->b_edit.batch = GPU_batch_create_ex(
        GPU_PRIM_POINTS, cache->b_edit.vbo, NULL, GPU_BATCH_OWNS_VBO);
  }
  if ((cache->b_edlin.vbo) && (cache->b_edlin.batch == NULL)) {
    cache->b_edlin.batch = GPU_batch_create_ex(
        GPU_PRIM_LINE_STRIP, cache->b_edlin.vbo, NULL, GPU_BATCH_OWNS_VBO);
  }
}

/* create all shading groups */
static void gpencil_shgroups_create(GPENCIL_e_data *e_data,
                                    void *vedata,
                                    Object *ob,
                                    GpencilBatchCache *cache,
                                    tGPencilObjectCache *cache_ob)
{
  GPENCIL_StorageList *stl = ((GPENCIL_Data *)vedata)->stl;
  GPENCIL_PassList *psl = ((GPENCIL_Data *)vedata)->psl;
  bGPdata *gpd = (bGPdata *)ob->data;
  DRWPass *stroke_pass = GPENCIL_3D_DRAWMODE(ob, gpd) ? psl->stroke_pass_3d : psl->stroke_pass_2d;

  GpencilBatchGroup *elm = NULL;
  DRWShadingGroup *shgrp = NULL;
  tGPencilObjectCache_shgrp *array_elm = NULL;

  bGPDlayer *gpl = NULL;
  bGPDlayer *gpl_prev = NULL;
  int idx = 0;
  bool tag_first = false;

  const DRWContextState *draw_ctx = DRW_context_state_get();
  const View3D *v3d = draw_ctx->v3d;

  const bool overlay = draw_ctx->v3d != NULL ?
                           (bool)((draw_ctx->v3d->flag2 & V3D_HIDE_OVERLAYS) == 0) :
                           true;
  const bool main_onion = v3d != NULL ? (v3d->gp_flag & V3D_GP_SHOW_ONION_SKIN) : true;
  const bool do_onion = (bool)((gpd->flag & GP_DATA_STROKE_WEIGHTMODE) == 0) && main_onion &&
                        overlay && gpencil_onion_active(gpd);

  int start_stroke = 0;
  int start_point = 0;
  int start_fill = 0;
  int start_edit = 0;
  int start_edlin = 0;

  uint stencil_id = 1;
  /* Flag to determine if the layer is above active layer. */
  stl->storage->is_ontop = false;
  for (int i = 0; i < cache->grp_used; i++) {
    elm = &cache->grp_cache[i];
    array_elm = &cache_ob->shgrp_array[idx];
    const float scale = cache_ob->scale;

    /* Limit stencil id */
    if (stencil_id > 255) {
      stencil_id = 1;
    }

    /* save last group when change */
    if (gpl_prev == NULL) {
      gpl_prev = elm->gpl;
      tag_first = true;
    }
    else {
      if (elm->gpl != gpl_prev) {
        /* first layer is always blend Normal */
        array_elm->mode = idx == 0 ? eGplBlendMode_Regular : gpl->blend_mode;
        array_elm->end_shgrp = shgrp;
        gpl_prev = elm->gpl;
        tag_first = true;
        idx++;
      }
    }

    gpl = elm->gpl;
    if ((!stl->storage->is_ontop) && (gpl->flag & GP_LAYER_ACTIVE)) {
      stl->storage->is_ontop = true;
    }

    bGPDframe *gpf = elm->gpf;
    bGPDstroke *gps = elm->gps;
    MaterialGPencilStyle *gp_style = BKE_material_gpencil_settings_get(ob, gps->mat_nr + 1);
    /* if the user switch used material from data to object,
     * the material could not be available */
    if (gp_style == NULL) {
      break;
    }

    /* limit the number of shading groups */
    if (i >= GPENCIL_MAX_SHGROUPS) {
      break;
    }

    float(*obmat)[4] = (!cache_ob->is_dup_ob) ? gpf->runtime.parent_obmat : cache_ob->obmat;
    switch (elm->type) {
      case eGpencilBatchGroupType_Stroke: {
        const int len = elm->vertex_idx - start_stroke;

        shgrp = gpencil_shgroup_stroke_create(e_data,
                                              vedata,
                                              stroke_pass,
                                              e_data->gpencil_stroke_sh,
                                              ob,
                                              obmat,
                                              gpd,
                                              gpl,
                                              gps,
                                              gp_style,
                                              stl->storage->shgroup_id,
                                              elm->onion,
                                              scale,
                                              cache_ob->shading_type);

        /* set stencil mask id */
        if (gpencil_is_stencil_required(gp_style)) {
          if (stencil_id == 1) {
            /* Clear previous stencils. */
            DRW_shgroup_clear_framebuffer(shgrp, GPU_STENCIL_BIT, 0, 0, 0, 0, 0.0f, 0x0);
          }
          DRW_shgroup_stencil_mask(shgrp, stencil_id);
          stencil_id++;
        }
        else {
          /* Disable stencil for this type */
          DRW_shgroup_state_disable(shgrp, DRW_STATE_WRITE_STENCIL | DRW_STATE_STENCIL_NEQUAL);
        }

        if ((do_onion) || (elm->onion == false)) {
          DRW_shgroup_call_range(shgrp, cache->b_stroke.batch, start_stroke, len);
        }
        stl->storage->shgroup_id++;
        start_stroke = elm->vertex_idx;
        break;
      }
      case eGpencilBatchGroupType_Point: {
        const int len = elm->vertex_idx - start_point;

        shgrp = gpencil_shgroup_point_create(e_data,
                                             vedata,
                                             stroke_pass,
                                             e_data->gpencil_point_sh,
                                             ob,
                                             obmat,
                                             gpd,
                                             gpl,
                                             gps,
                                             gp_style,
                                             stl->storage->shgroup_id,
                                             elm->onion,
                                             scale,
                                             cache_ob->shading_type);

        /* Disable stencil for this type */
        DRW_shgroup_state_disable(shgrp, DRW_STATE_WRITE_STENCIL | DRW_STATE_STENCIL_NEQUAL);

        if ((do_onion) || (elm->onion == false)) {
          DRW_shgroup_call_range(shgrp, cache->b_point.batch, start_point, len);
        }
        stl->storage->shgroup_id++;
        start_point = elm->vertex_idx;
        break;
      }
      case eGpencilBatchGroupType_Fill: {
        const int len = elm->vertex_idx - start_fill;

        shgrp = gpencil_shgroup_fill_create(e_data,
                                            vedata,
                                            stroke_pass,
                                            e_data->gpencil_fill_sh,
                                            ob,
                                            obmat,
                                            gpd,
                                            gpl,
                                            gp_style,
                                            stl->storage->shgroup_id,
                                            cache_ob->shading_type);

        /* Disable stencil for this type */
        DRW_shgroup_state_disable(shgrp, DRW_STATE_WRITE_STENCIL | DRW_STATE_STENCIL_NEQUAL);

        if ((do_onion) || (elm->onion == false)) {
          DRW_shgroup_call_range(shgrp, cache->b_fill.batch, start_fill, len);
        }
        stl->storage->shgroup_id++;
        start_fill = elm->vertex_idx;
        break;
      }
      case eGpencilBatchGroupType_Edit: {
        if (stl->g_data->shgrps_edit_point) {
          const int len = elm->vertex_idx - start_edit;

          shgrp = DRW_shgroup_create_sub(stl->g_data->shgrps_edit_point);
          DRW_shgroup_uniform_mat4(shgrp, "gpModelMatrix", obmat);
          /* use always the same group */
          DRW_shgroup_call_range(
              stl->g_data->shgrps_edit_point, cache->b_edit.batch, start_edit, len);

          start_edit = elm->vertex_idx;
        }
        break;
      }
      case eGpencilBatchGroupType_Edlin: {
        if (stl->g_data->shgrps_edit_line) {
          const int len = elm->vertex_idx - start_edlin;

          shgrp = DRW_shgroup_create_sub(stl->g_data->shgrps_edit_line);
          DRW_shgroup_uniform_mat4(shgrp, "gpModelMatrix", obmat);
          /* use always the same group */
          DRW_shgroup_call_range(
              stl->g_data->shgrps_edit_line, cache->b_edlin.batch, start_edlin, len);

          start_edlin = elm->vertex_idx;
        }
        break;
      }
      default: {
        break;
      }
    }
    /* save first group */
    if ((shgrp != NULL) && (tag_first)) {
      array_elm = &cache_ob->shgrp_array[idx];
      array_elm->mode = idx == 0 ? eGplBlendMode_Regular : gpl->blend_mode;
      array_elm->mask_layer = gpl->flag & GP_LAYER_USE_MASK;
      array_elm->blend_opacity = gpl->opacity;
      array_elm->init_shgrp = shgrp;
      cache_ob->tot_layers++;

      tag_first = false;
    }
  }

  /* save last group */
  if (shgrp != NULL) {
    array_elm->mode = idx == 0 ? eGplBlendMode_Regular : gpl->blend_mode;
    array_elm->end_shgrp = shgrp;
  }
}
/* populate a datablock for multiedit (no onions, no modifiers) */
void gpencil_populate_multiedit(GPENCIL_e_data *e_data,
                                void *vedata,
                                Object *ob,
                                tGPencilObjectCache *cache_ob)
{
  bGPdata *gpd = (bGPdata *)ob->data;
  bGPDframe *gpf = NULL;

  GPENCIL_StorageList *stl = ((GPENCIL_Data *)vedata)->stl;
  const DRWContextState *draw_ctx = DRW_context_state_get();
  Scene *scene = draw_ctx->scene;
  int cfra_eval = (int)DEG_get_ctime(draw_ctx->depsgraph);
  GpencilBatchCache *cache = gpencil_batch_cache_get(ob, cfra_eval);

  /* check if playing animation */
  const bool playing = stl->storage->is_playing;

  /* calc max size of VBOs */
  gpencil_calc_vertex(stl, cache_ob, cache, gpd);

  /* draw strokes */
  for (bGPDlayer *gpl = gpd->layers.first; gpl; gpl = gpl->next) {
    /* don't draw layer if hidden */
    if (gpl->flag & GP_LAYER_HIDE) {
      continue;
    }
    const float alpha = GPENCIL_SIMPLIFY_TINT(scene, playing) ? 0.0f : gpl->tintcolor[3];
    const float tintcolor[4] = {gpl->tintcolor[0], gpl->tintcolor[1], gpl->tintcolor[2], alpha};

    /* list of frames to draw */
    if (!playing) {
      for (gpf = gpl->frames.first; gpf; gpf = gpf->next) {
        if ((gpf == gpl->actframe) || (gpf->flag & GP_FRAME_SELECT)) {
          gpencil_draw_strokes(
              cache, e_data, vedata, ob, gpd, gpl, gpf, gpl->opacity, tintcolor, false, cache_ob);
        }
      }
    }
    else {
      gpf = BKE_gpencil_layer_getframe(gpl, cfra_eval, GP_GETFRAME_USE_PREV);
      if (gpf) {
        gpencil_draw_strokes(
            cache, e_data, vedata, ob, gpd, gpl, gpf, gpl->opacity, tintcolor, false, cache_ob);
      }
    }
  }

  /* create batchs and shading groups */
  gpencil_batches_ensure(cache);
  gpencil_shgroups_create(e_data, vedata, ob, cache, cache_ob);

  cache->is_dirty = false;
}

/* helper for populate a complete grease pencil datablock */
void gpencil_populate_datablock(GPENCIL_e_data *e_data,
                                void *vedata,
                                Object *ob,
                                tGPencilObjectCache *cache_ob)
{
  GPENCIL_StorageList *stl = ((GPENCIL_Data *)vedata)->stl;
  const DRWContextState *draw_ctx = DRW_context_state_get();
  const ViewLayer *view_layer = DEG_get_evaluated_view_layer(draw_ctx->depsgraph);
  Scene *scene = draw_ctx->scene;

  /* TODO: Review why is needed this recalc when render cycles + GP object in background.
   * We need these lines to keep running the background render, but asap we get an alternative
   * solution, we must remove it and keep all logic inside gpencil_modifier module. (antoniov)
   */
  if (ob->runtime.gpencil_tot_layers == 0) {
    BKE_gpencil_modifiers_calc(draw_ctx->depsgraph, draw_ctx->scene, ob);
  }

  /* Use original data to shared in edit/transform operators */
  bGPdata *gpd_eval = (bGPdata *)ob->data;
  bGPdata *gpd = (bGPdata *)DEG_get_original_id(&gpd_eval->id);

  const bool main_onion = draw_ctx->v3d != NULL ?
                              (draw_ctx->v3d->gp_flag & V3D_GP_SHOW_ONION_SKIN) :
                              true;
  const bool playing = stl->storage->is_playing;
  const bool overlay = draw_ctx->v3d != NULL ?
                           (bool)((draw_ctx->v3d->flag2 & V3D_HIDE_OVERLAYS) == 0) :
                           true;
  const bool do_onion = (bool)((gpd->flag & GP_DATA_STROKE_WEIGHTMODE) == 0) && overlay &&
                        main_onion && !playing && gpencil_onion_active(gpd);

  View3D *v3d = draw_ctx->v3d;
  int cfra_eval = (int)DEG_get_ctime(draw_ctx->depsgraph);

  bGPDframe *gpf_eval = NULL;
  const bool time_remap = BKE_gpencil_has_time_modifiers(ob);

  float opacity;
  bGPDframe *gpf = NULL;

  GpencilBatchCache *cache = gpencil_batch_cache_get(ob, cfra_eval);

  /* if object is duplicate, only create shading groups */
  if (cache_ob->is_dup_ob) {
    gpencil_shgroups_create(e_data, vedata, ob, cache, cache_ob);
    return;
  }

  /* calc max size of VBOs */
  gpencil_calc_vertex(stl, cache_ob, cache, gpd);

  /* draw normal strokes */
  for (bGPDlayer *gpl = gpd->layers.first; gpl; gpl = gpl->next) {
    /* don't draw layer if hidden */
    if (gpl->flag & GP_LAYER_HIDE) {
      continue;
    }

    const bool is_solomode = GPENCIL_PAINT_MODE(gpd) && (!playing) && (!stl->storage->is_render) &&
                             (gpl->flag & GP_LAYER_SOLO_MODE);

    /* filter view layer to gp layers in the same view layer (for compo) */
    if ((stl->storage->is_render) && (gpl->viewlayername[0] != '\0')) {
      if (!STREQ(view_layer->name, gpl->viewlayername)) {
        continue;
      }
    }

    /* remap time */
    int remap_cfra = cfra_eval;
    if ((time_remap) && (!stl->storage->simplify_modif)) {
      remap_cfra = BKE_gpencil_time_modifier(
          draw_ctx->depsgraph, scene, ob, gpl, cfra_eval, stl->storage->is_render);
    }

    gpf = BKE_gpencil_layer_getframe(gpl, remap_cfra, GP_GETFRAME_USE_PREV);
    if (gpf == NULL) {
      continue;
    }

    /* if solo mode, display only frames with keyframe in the current frame */
    if ((is_solomode) && (gpf->framenum != remap_cfra)) {
      continue;
    }

    opacity = gpl->opacity;
    /* if pose mode, maybe the overlay to fade geometry is enabled */
    if ((draw_ctx->obact) && (draw_ctx->object_mode == OB_MODE_POSE) &&
        (v3d->overlay.flag & V3D_OVERLAY_BONE_SELECT)) {
      opacity = opacity * v3d->overlay.xray_alpha_bone;
    }

    /* Get evaluated frames array data */
    int idx_eval = BLI_findindex(&gpd->layers, gpl);
    gpf_eval = &ob->runtime.gpencil_evaluated_frames[idx_eval];

    /* draw onion skins */
    if (!ID_IS_LINKED(&gpd->id)) {
      if ((do_onion) && (gpl->onion_flag & GP_LAYER_ONIONSKIN) &&
          ((!playing) || (gpd->onion_flag & GP_ONION_GHOST_ALWAYS)) && (!cache_ob->is_dup_ob) &&
          (gpd->id.us <= 1)) {
        if ((!stl->storage->is_render) ||
            ((stl->storage->is_render) && (gpd->onion_flag & GP_ONION_GHOST_ALWAYS))) {
          gpencil_draw_onionskins(cache, vedata, ob, gpd, gpl, gpf);
        }
      }
    }
    /* draw normal strokes */
    const float alpha = GPENCIL_SIMPLIFY_TINT(scene, playing) ? 0.0f : gpl->tintcolor[3];
    const float tintcolor[4] = {gpl->tintcolor[0], gpl->tintcolor[1], gpl->tintcolor[2], alpha};
    gpencil_draw_strokes(
        cache, e_data, vedata, ob, gpd, gpl, gpf_eval, opacity, tintcolor, false, cache_ob);
  }

  /* create batchs and shading groups */
  gpencil_batches_ensure(cache);
  gpencil_shgroups_create(e_data, vedata, ob, cache, cache_ob);

  cache->is_dirty = false;
}

void gpencil_populate_particles(GPENCIL_e_data *e_data, GHash *gh_objects, void *vedata)
{
  GPENCIL_StorageList *stl = ((GPENCIL_Data *)vedata)->stl;

  /* add particles */
  for (int i = 0; i < stl->g_data->gp_cache_used; i++) {
    tGPencilObjectCache *cache_ob = &stl->g_data->gp_object_cache[i];
    if (cache_ob->is_dup_ob) {
      /* Reassign duplicate objects because memory for particles is not available
       * and need to use the original data-block and run-time data. */
      Object *ob = (Object *)BLI_ghash_lookup(gh_objects, cache_ob->name);
      if (ob) {
        cache_ob->ob = ob;
        cache_ob->gpd = (bGPdata *)ob->data;
        GpencilBatchCache *cache = ob->runtime.gpencil_cache;
        if (cache != NULL) {
          gpencil_shgroups_create(e_data, vedata, ob, cache, cache_ob);
        }
      }
    }
  }
}
