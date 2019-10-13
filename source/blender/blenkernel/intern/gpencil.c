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

/** \file
 * \ingroup bke
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stddef.h>
#include <math.h>

#include "CLG_log.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_utildefines.h"
#include "BLI_math_vector.h"
#include "BLI_string_utils.h"

#include "BLT_translation.h"

#include "DNA_anim_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_material_types.h"
#include "DNA_gpencil_types.h"
#include "DNA_userdef_types.h"
#include "DNA_scene_types.h"
#include "DNA_object_types.h"

#include "BKE_action.h"
#include "BKE_animsys.h"
#include "BKE_curve.h"
#include "BKE_collection.h"
#include "BKE_colortools.h"
#include "BKE_deform.h"
#include "BKE_gpencil.h"
#include "BKE_icons.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_object.h"

#include "BLI_math_color.h"

#include "DEG_depsgraph.h"

static CLG_LogRef LOG = {"bke.gpencil"};

/* ************************************************** */
/* Draw Engine */

void (*BKE_gpencil_batch_cache_dirty_tag_cb)(bGPdata *gpd) = NULL;
void (*BKE_gpencil_batch_cache_free_cb)(bGPdata *gpd) = NULL;

void BKE_gpencil_batch_cache_dirty_tag(bGPdata *gpd)
{
  if (gpd) {
    DEG_id_tag_update(&gpd->id, ID_RECALC_GEOMETRY);
    BKE_gpencil_batch_cache_dirty_tag_cb(gpd);
  }
}

void BKE_gpencil_batch_cache_free(bGPdata *gpd)
{
  if (gpd) {
    BKE_gpencil_batch_cache_free_cb(gpd);
  }
}

/* ************************************************** */
/* Memory Management */

/* clean vertex groups weights */
void BKE_gpencil_free_point_weights(MDeformVert *dvert)
{
  if (dvert == NULL) {
    return;
  }
  MEM_SAFE_FREE(dvert->dw);
}

void BKE_gpencil_free_stroke_weights(bGPDstroke *gps)
{
  if (gps == NULL) {
    return;
  }

  if (gps->dvert == NULL) {
    return;
  }

  for (int i = 0; i < gps->totpoints; i++) {
    MDeformVert *dvert = &gps->dvert[i];
    BKE_gpencil_free_point_weights(dvert);
  }
}

/* free stroke, doesn't unlink from any listbase */
void BKE_gpencil_free_stroke(bGPDstroke *gps)
{
  if (gps == NULL) {
    return;
  }
  /* free stroke memory arrays, then stroke itself */
  if (gps->points) {
    MEM_freeN(gps->points);
  }
  if (gps->dvert) {
    BKE_gpencil_free_stroke_weights(gps);
    MEM_freeN(gps->dvert);
  }
  if (gps->triangles) {
    MEM_freeN(gps->triangles);
  }

  MEM_freeN(gps);
}

/* Free strokes belonging to a gp-frame */
bool BKE_gpencil_free_strokes(bGPDframe *gpf)
{
  bGPDstroke *gps_next;
  bool changed = (BLI_listbase_is_empty(&gpf->strokes) == false);

  /* free strokes */
  for (bGPDstroke *gps = gpf->strokes.first; gps; gps = gps_next) {
    gps_next = gps->next;
    BKE_gpencil_free_stroke(gps);
  }
  BLI_listbase_clear(&gpf->strokes);

  return changed;
}

/* Free strokes and colors belonging to a gp-frame */
bool BKE_gpencil_free_frame_runtime_data(bGPDframe *gpf_eval)
{
  bGPDstroke *gps_next;
  if (!gpf_eval) {
    return false;
  }

  /* free strokes */
  for (bGPDstroke *gps = gpf_eval->strokes.first; gps; gps = gps_next) {
    gps_next = gps->next;
    BKE_gpencil_free_stroke(gps);
  }
  BLI_listbase_clear(&gpf_eval->strokes);

  return true;
}

/* Free all of a gp-layer's frames */
void BKE_gpencil_free_frames(bGPDlayer *gpl)
{
  bGPDframe *gpf_next;

  /* error checking */
  if (gpl == NULL) {
    return;
  }

  /* free frames */
  for (bGPDframe *gpf = gpl->frames.first; gpf; gpf = gpf_next) {
    gpf_next = gpf->next;

    /* free strokes and their associated memory */
    BKE_gpencil_free_strokes(gpf);
    BLI_freelinkN(&gpl->frames, gpf);
  }
  gpl->actframe = NULL;
}

/* Free all of the gp-layers for a viewport (list should be &gpd->layers or so) */
void BKE_gpencil_free_layers(ListBase *list)
{
  bGPDlayer *gpl_next;

  /* error checking */
  if (list == NULL) {
    return;
  }

  /* delete layers */
  for (bGPDlayer *gpl = list->first; gpl; gpl = gpl_next) {
    gpl_next = gpl->next;

    /* free layers and their data */
    BKE_gpencil_free_frames(gpl);
    BLI_freelinkN(list, gpl);
  }
}

/** Free (or release) any data used by this grease pencil (does not free the gpencil itself). */
void BKE_gpencil_free(bGPdata *gpd, bool free_all)
{
  /* clear animation data */
  BKE_animdata_free(&gpd->id, false);

  /* free layers */
  BKE_gpencil_free_layers(&gpd->layers);

  /* materials */
  MEM_SAFE_FREE(gpd->mat);

  /* free all data */
  if (free_all) {
    /* clear cache */
    BKE_gpencil_batch_cache_free(gpd);
  }
}

/* ************************************************** */
/* Container Creation */

/* add a new gp-frame to the given layer */
bGPDframe *BKE_gpencil_frame_addnew(bGPDlayer *gpl, int cframe)
{
  bGPDframe *gpf = NULL, *gf = NULL;
  short state = 0;

  /* error checking */
  if (gpl == NULL) {
    return NULL;
  }

  /* allocate memory for this frame */
  gpf = MEM_callocN(sizeof(bGPDframe), "bGPDframe");
  gpf->framenum = cframe;

  /* find appropriate place to add frame */
  if (gpl->frames.first) {
    for (gf = gpl->frames.first; gf; gf = gf->next) {
      /* check if frame matches one that is supposed to be added */
      if (gf->framenum == cframe) {
        state = -1;
        break;
      }

      /* if current frame has already exceeded the frame to add, add before */
      if (gf->framenum > cframe) {
        BLI_insertlinkbefore(&gpl->frames, gf, gpf);
        state = 1;
        break;
      }
    }
  }

  /* check whether frame was added successfully */
  if (state == -1) {
    CLOG_ERROR(
        &LOG, "Frame (%d) existed already for this layer_active. Using existing frame", cframe);

    /* free the newly created one, and use the old one instead */
    MEM_freeN(gpf);

    /* return existing frame instead... */
    BLI_assert(gf != NULL);
    gpf = gf;
  }
  else if (state == 0) {
    /* add to end then! */
    BLI_addtail(&gpl->frames, gpf);
  }

  /* return frame */
  return gpf;
}

/* add a copy of the active gp-frame to the given layer */
bGPDframe *BKE_gpencil_frame_addcopy(bGPDlayer *gpl, int cframe)
{
  bGPDframe *new_frame;
  bool found = false;

  /* Error checking/handling */
  if (gpl == NULL) {
    /* no layer */
    return NULL;
  }
  else if (gpl->actframe == NULL) {
    /* no active frame, so just create a new one from scratch */
    return BKE_gpencil_frame_addnew(gpl, cframe);
  }

  /* Create a copy of the frame */
  new_frame = BKE_gpencil_frame_duplicate(gpl->actframe);

  /* Find frame to insert it before */
  for (bGPDframe *gpf = gpl->frames.first; gpf; gpf = gpf->next) {
    if (gpf->framenum > cframe) {
      /* Add it here */
      BLI_insertlinkbefore(&gpl->frames, gpf, new_frame);

      found = true;
      break;
    }
    else if (gpf->framenum == cframe) {
      /* This only happens when we're editing with framelock on...
       * - Delete the new frame and don't do anything else here...
       */
      BKE_gpencil_free_strokes(new_frame);
      MEM_freeN(new_frame);
      new_frame = NULL;

      found = true;
      break;
    }
  }

  if (found == false) {
    /* Add new frame to the end */
    BLI_addtail(&gpl->frames, new_frame);
  }

  /* Ensure that frame is set up correctly, and return it */
  if (new_frame) {
    new_frame->framenum = cframe;
    gpl->actframe = new_frame;
  }

  return new_frame;
}

/* add a new gp-layer and make it the active layer */
bGPDlayer *BKE_gpencil_layer_addnew(bGPdata *gpd, const char *name, bool setactive)
{
  bGPDlayer *gpl = NULL;
  bGPDlayer *gpl_active = NULL;

  /* check that list is ok */
  if (gpd == NULL) {
    return NULL;
  }

  /* allocate memory for frame and add to end of list */
  gpl = MEM_callocN(sizeof(bGPDlayer), "bGPDlayer");

  gpl_active = BKE_gpencil_layer_getactive(gpd);

  /* add to datablock */
  if (gpl_active == NULL) {
    BLI_addtail(&gpd->layers, gpl);
  }
  else {
    /* if active layer, add after that layer */
    BLI_insertlinkafter(&gpd->layers, gpl_active, gpl);
  }

  /* annotation vs GP Object behavior is slightly different */
  if (gpd->flag & GP_DATA_ANNOTATIONS) {
    /* set default color of new strokes for this layer */
    copy_v4_v4(gpl->color, U.gpencil_new_layer_col);
    gpl->opacity = 1.0f;

    /* set default thickness of new strokes for this layer */
    gpl->thickness = 3;

    /* Onion colors */
    ARRAY_SET_ITEMS(gpl->gcolor_prev, 0.302f, 0.851f, 0.302f);
    ARRAY_SET_ITEMS(gpl->gcolor_next, 0.250f, 0.1f, 1.0f);
  }
  else {
    /* thickness parameter represents "thickness change", not absolute thickness */
    gpl->thickness = 0;
    gpl->opacity = 1.0f;
    /* default channel color */
    ARRAY_SET_ITEMS(gpl->color, 0.2f, 0.2f, 0.2f);
  }

  /* auto-name */
  BLI_strncpy(gpl->info, name, sizeof(gpl->info));
  BLI_uniquename(&gpd->layers,
                 gpl,
                 (gpd->flag & GP_DATA_ANNOTATIONS) ? DATA_("Note") : DATA_("GP_Layer"),
                 '.',
                 offsetof(bGPDlayer, info),
                 sizeof(gpl->info));

  /* make this one the active one */
  if (setactive) {
    BKE_gpencil_layer_setactive(gpd, gpl);
  }

  /* return layer */
  return gpl;
}

/* add a new gp-datablock */
bGPdata *BKE_gpencil_data_addnew(Main *bmain, const char name[])
{
  bGPdata *gpd;

  /* allocate memory for a new block */
  gpd = BKE_libblock_alloc(bmain, ID_GD, name, 0);

  /* initial settings */
  gpd->flag = (GP_DATA_DISPINFO | GP_DATA_EXPAND);

  /* general flags */
  gpd->flag |= GP_DATA_VIEWALIGN;
  gpd->flag |= GP_DATA_STROKE_FORCE_RECALC;
  /* always enable object onion skin switch */
  gpd->flag |= GP_DATA_SHOW_ONIONSKINS;
  /* GP object specific settings */
  ARRAY_SET_ITEMS(gpd->line_color, 0.6f, 0.6f, 0.6f, 0.5f);

  gpd->pixfactor = GP_DEFAULT_PIX_FACTOR;

  /* grid settings */
  ARRAY_SET_ITEMS(gpd->grid.color, 0.5f, 0.5f, 0.5f); /* Color */
  ARRAY_SET_ITEMS(gpd->grid.scale, 1.0f, 1.0f);       /* Scale */
  gpd->grid.lines = GP_DEFAULT_GRID_LINES;            /* Number of lines */

  /* onion-skinning settings (datablock level) */
  gpd->onion_flag |= (GP_ONION_GHOST_PREVCOL | GP_ONION_GHOST_NEXTCOL);
  gpd->onion_flag |= GP_ONION_FADE;
  gpd->onion_mode = GP_ONION_MODE_RELATIVE;
  gpd->onion_factor = 0.5f;
  ARRAY_SET_ITEMS(gpd->gcolor_prev, 0.145098f, 0.419608f, 0.137255f); /* green */
  ARRAY_SET_ITEMS(gpd->gcolor_next, 0.125490f, 0.082353f, 0.529412f); /* blue */
  gpd->gstep = 1;
  gpd->gstep_next = 1;

  return gpd;
}

/* ************************************************** */
/* Primitive Creation */
/* Utilities for easier bulk-creation of geometry */

/**
 * Populate stroke with point data from data buffers
 *
 * \param array: Flat array of point data values. Each entry has GP_PRIM_DATABUF_SIZE values
 * \param mat: 4x4 transform matrix to transform points into the right coordinate space
 */
void BKE_gpencil_stroke_add_points(bGPDstroke *gps,
                                   const float *array,
                                   const int totpoints,
                                   const float mat[4][4])
{
  for (int i = 0; i < totpoints; i++) {
    bGPDspoint *pt = &gps->points[i];
    const int x = GP_PRIM_DATABUF_SIZE * i;

    pt->x = array[x];
    pt->y = array[x + 1];
    pt->z = array[x + 2];
    mul_m4_v3(mat, &pt->x);

    pt->pressure = array[x + 3];
    pt->strength = array[x + 4];
  }
}

/* Create a new stroke, with pre-allocated data buffers */
bGPDstroke *BKE_gpencil_add_stroke(bGPDframe *gpf, int mat_idx, int totpoints, short thickness)
{
  /* allocate memory for a new stroke */
  bGPDstroke *gps = MEM_callocN(sizeof(bGPDstroke), "gp_stroke");

  gps->thickness = thickness;
  gps->gradient_f = 1.0f;
  gps->gradient_s[0] = 1.0f;
  gps->gradient_s[1] = 1.0f;

  gps->inittime = 0;

  /* enable recalculation flag by default */
  gps->flag = GP_STROKE_RECALC_GEOMETRY | GP_STROKE_3DSPACE;

  gps->totpoints = totpoints;
  gps->points = MEM_callocN(sizeof(bGPDspoint) * gps->totpoints, "gp_stroke_points");

  /* initialize triangle memory to dummy data */
  gps->triangles = MEM_callocN(sizeof(bGPDtriangle), "GP Stroke triangulation");
  gps->flag |= GP_STROKE_RECALC_GEOMETRY;
  gps->tot_triangles = 0;

  gps->mat_nr = mat_idx;

  /* add to frame */
  BLI_addtail(&gpf->strokes, gps);

  return gps;
}

/* ************************************************** */
/* Data Duplication */

/* make a copy of a given gpencil weights */
void BKE_gpencil_stroke_weights_duplicate(bGPDstroke *gps_src, bGPDstroke *gps_dst)
{
  if (gps_src == NULL) {
    return;
  }
  BLI_assert(gps_src->totpoints == gps_dst->totpoints);

  BKE_defvert_array_copy(gps_dst->dvert, gps_src->dvert, gps_src->totpoints);
}

/* make a copy of a given gpencil stroke */
bGPDstroke *BKE_gpencil_stroke_duplicate(bGPDstroke *gps_src)
{
  bGPDstroke *gps_dst = NULL;

  gps_dst = MEM_dupallocN(gps_src);
  gps_dst->prev = gps_dst->next = NULL;

  gps_dst->points = MEM_dupallocN(gps_src->points);

  if (gps_src->dvert != NULL) {
    gps_dst->dvert = MEM_dupallocN(gps_src->dvert);
    BKE_gpencil_stroke_weights_duplicate(gps_src, gps_dst);
  }
  else {
    gps_dst->dvert = NULL;
  }

  /* Don't clear triangles, so that modifier evaluation can just use
   * this without extra work first. Most places that need to force
   * this data to get recalculated will destroy the data anyway though.
   */
  gps_dst->triangles = MEM_dupallocN(gps_dst->triangles);
  /* gps_dst->flag |= GP_STROKE_RECALC_GEOMETRY; */

  /* return new stroke */
  return gps_dst;
}

/* make a copy of a given gpencil frame */
bGPDframe *BKE_gpencil_frame_duplicate(const bGPDframe *gpf_src)
{
  bGPDstroke *gps_dst = NULL;
  bGPDframe *gpf_dst;

  /* error checking */
  if (gpf_src == NULL) {
    return NULL;
  }

  /* make a copy of the source frame */
  gpf_dst = MEM_dupallocN(gpf_src);
  gpf_dst->prev = gpf_dst->next = NULL;

  /* copy strokes */
  BLI_listbase_clear(&gpf_dst->strokes);
  for (bGPDstroke *gps_src = gpf_src->strokes.first; gps_src; gps_src = gps_src->next) {
    /* make copy of source stroke */
    gps_dst = BKE_gpencil_stroke_duplicate(gps_src);
    BLI_addtail(&gpf_dst->strokes, gps_dst);
  }

  /* return new frame */
  return gpf_dst;
}

/* make a copy of strokes between gpencil frames */
void BKE_gpencil_frame_copy_strokes(bGPDframe *gpf_src, struct bGPDframe *gpf_dst)
{
  bGPDstroke *gps_dst = NULL;
  /* error checking */
  if ((gpf_src == NULL) || (gpf_dst == NULL)) {
    return;
  }

  /* copy strokes */
  BLI_listbase_clear(&gpf_dst->strokes);
  for (bGPDstroke *gps_src = gpf_src->strokes.first; gps_src; gps_src = gps_src->next) {
    /* make copy of source stroke */
    gps_dst = BKE_gpencil_stroke_duplicate(gps_src);
    BLI_addtail(&gpf_dst->strokes, gps_dst);
  }
}

/* make a copy of a given gpencil layer */
bGPDlayer *BKE_gpencil_layer_duplicate(const bGPDlayer *gpl_src)
{
  const bGPDframe *gpf_src;
  bGPDframe *gpf_dst;
  bGPDlayer *gpl_dst;

  /* error checking */
  if (gpl_src == NULL) {
    return NULL;
  }

  /* make a copy of source layer */
  gpl_dst = MEM_dupallocN(gpl_src);
  gpl_dst->prev = gpl_dst->next = NULL;

  /* copy frames */
  BLI_listbase_clear(&gpl_dst->frames);
  for (gpf_src = gpl_src->frames.first; gpf_src; gpf_src = gpf_src->next) {
    /* make a copy of source frame */
    gpf_dst = BKE_gpencil_frame_duplicate(gpf_src);
    BLI_addtail(&gpl_dst->frames, gpf_dst);

    /* if source frame was the current layer's 'active' frame, reassign that too */
    if (gpf_src == gpl_dst->actframe) {
      gpl_dst->actframe = gpf_dst;
    }
  }

  /* return new layer */
  return gpl_dst;
}

/**
 * Only copy internal data of GreasePencil ID from source
 * to already allocated/initialized destination.
 * You probably never want to use that directly,
 * use #BKE_id_copy or #BKE_id_copy_ex for typical needs.
 *
 * WARNING! This function will not handle ID user count!
 *
 * \param flag: Copying options (see BKE_library.h's LIB_ID_COPY_... flags for more).
 */
void BKE_gpencil_copy_data(bGPdata *gpd_dst, const bGPdata *gpd_src, const int UNUSED(flag))
{
  /* duplicate material array */
  if (gpd_src->mat) {
    gpd_dst->mat = MEM_dupallocN(gpd_src->mat);
  }

  /* copy layers */
  BLI_listbase_clear(&gpd_dst->layers);
  for (const bGPDlayer *gpl_src = gpd_src->layers.first; gpl_src; gpl_src = gpl_src->next) {
    /* make a copy of source layer and its data */

    /* TODO here too could add unused flags... */
    bGPDlayer *gpl_dst = BKE_gpencil_layer_duplicate(gpl_src);

    BLI_addtail(&gpd_dst->layers, gpl_dst);
  }
}

/* Standard API to make a copy of GP datablock, separate from copying its data */
bGPdata *BKE_gpencil_copy(Main *bmain, const bGPdata *gpd)
{
  bGPdata *gpd_copy;
  BKE_id_copy(bmain, &gpd->id, (ID **)&gpd_copy);
  return gpd_copy;
}

/* make a copy of a given gpencil datablock */
/* XXX: Should this be deprecated? */
bGPdata *BKE_gpencil_data_duplicate(Main *bmain, const bGPdata *gpd_src, bool internal_copy)
{
  bGPdata *gpd_dst;

  /* Yuck and super-uber-hyper yuck!!!
   * Should be replaceable with a no-main copy (LIB_ID_COPY_NO_MAIN etc.), but not sure about it,
   * so for now keep old code for that one. */

  /* error checking */
  if (gpd_src == NULL) {
    return NULL;
  }

  if (internal_copy) {
    /* make a straight copy for undo buffers used during stroke drawing */
    gpd_dst = MEM_dupallocN(gpd_src);
  }
  else {
    BLI_assert(bmain != NULL);
    BKE_id_copy(bmain, &gpd_src->id, (ID **)&gpd_dst);
  }

  /* Copy internal data (layers, etc.) */
  BKE_gpencil_copy_data(gpd_dst, gpd_src, 0);

  /* return new */
  return gpd_dst;
}

void BKE_gpencil_make_local(Main *bmain, bGPdata *gpd, const bool lib_local)
{
  BKE_id_make_local_generic(bmain, &gpd->id, true, lib_local);
}

/* ************************************************** */
/* GP Stroke API */

/* ensure selection status of stroke is in sync with its points */
void BKE_gpencil_stroke_sync_selection(bGPDstroke *gps)
{
  bGPDspoint *pt;
  int i;

  /* error checking */
  if (gps == NULL) {
    return;
  }

  /* we'll stop when we find the first selected point,
   * so initially, we must deselect
   */
  gps->flag &= ~GP_STROKE_SELECT;

  for (i = 0, pt = gps->points; i < gps->totpoints; i++, pt++) {
    if (pt->flag & GP_SPOINT_SELECT) {
      gps->flag |= GP_STROKE_SELECT;
      break;
    }
  }
}

/* ************************************************** */
/* GP Frame API */

/* delete the last stroke of the given frame */
void BKE_gpencil_frame_delete_laststroke(bGPDlayer *gpl, bGPDframe *gpf)
{
  bGPDstroke *gps = (gpf) ? gpf->strokes.last : NULL;
  int cfra = (gpf) ? gpf->framenum : 0; /* assume that the current frame was not locked */

  /* error checking */
  if (ELEM(NULL, gpf, gps)) {
    return;
  }

  /* free the stroke and its data */
  if (gps->points) {
    MEM_freeN(gps->points);
  }
  if (gps->dvert) {
    BKE_gpencil_free_stroke_weights(gps);
    MEM_freeN(gps->dvert);
  }
  MEM_freeN(gps->triangles);
  BLI_freelinkN(&gpf->strokes, gps);

  /* if frame has no strokes after this, delete it */
  if (BLI_listbase_is_empty(&gpf->strokes)) {
    BKE_gpencil_layer_delframe(gpl, gpf);
    BKE_gpencil_layer_getframe(gpl, cfra, GP_GETFRAME_USE_PREV);
  }
}

/* ************************************************** */
/* GP Layer API */

/* Check if the given layer is able to be edited or not */
bool gpencil_layer_is_editable(const bGPDlayer *gpl)
{
  /* Sanity check */
  if (gpl == NULL) {
    return false;
  }

  /* Layer must be: Visible + Editable */
  if ((gpl->flag & (GP_LAYER_HIDE | GP_LAYER_LOCKED)) == 0) {
    /* Opacity must be sufficiently high that it is still "visible"
     * Otherwise, it's not really "visible" to the user, so no point editing...
     */
    if (gpl->opacity > GPENCIL_ALPHA_OPACITY_THRESH) {
      return true;
    }
  }

  /* Something failed */
  return false;
}

/* Look up the gp-frame on the requested frame number, but don't add a new one */
bGPDframe *BKE_gpencil_layer_find_frame(bGPDlayer *gpl, int cframe)
{
  bGPDframe *gpf;

  /* Search in reverse order, since this is often used for playback/adding,
   * where it's less likely that we're interested in the earlier frames
   */
  for (gpf = gpl->frames.last; gpf; gpf = gpf->prev) {
    if (gpf->framenum == cframe) {
      return gpf;
    }
  }

  return NULL;
}

/* get the appropriate gp-frame from a given layer
 * - this sets the layer's actframe var (if allowed to)
 * - extension beyond range (if first gp-frame is after all frame in interest and cannot add)
 */
bGPDframe *BKE_gpencil_layer_getframe(bGPDlayer *gpl, int cframe, eGP_GetFrame_Mode addnew)
{
  bGPDframe *gpf = NULL;
  bool found = false;

  /* error checking */
  if (gpl == NULL) {
    return NULL;
  }

  /* check if there is already an active frame */
  if (gpl->actframe) {
    gpf = gpl->actframe;

    /* do not allow any changes to layer's active frame if layer is locked from changes
     * or if the layer has been set to stay on the current frame
     */
    if (gpl->flag & GP_LAYER_FRAMELOCK) {
      return gpf;
    }
    /* do not allow any changes to actframe if frame has painting tag attached to it */
    if (gpf->flag & GP_FRAME_PAINT) {
      return gpf;
    }

    /* try to find matching frame */
    if (gpf->framenum < cframe) {
      for (; gpf; gpf = gpf->next) {
        if (gpf->framenum == cframe) {
          found = true;
          break;
        }
        else if ((gpf->next) && (gpf->next->framenum > cframe)) {
          found = true;
          break;
        }
      }

      /* set the appropriate frame */
      if (addnew) {
        if ((found) && (gpf->framenum == cframe)) {
          gpl->actframe = gpf;
        }
        else if (addnew == GP_GETFRAME_ADD_COPY) {
          gpl->actframe = BKE_gpencil_frame_addcopy(gpl, cframe);
        }
        else {
          gpl->actframe = BKE_gpencil_frame_addnew(gpl, cframe);
        }
      }
      else if (found) {
        gpl->actframe = gpf;
      }
      else {
        gpl->actframe = gpl->frames.last;
      }
    }
    else {
      for (; gpf; gpf = gpf->prev) {
        if (gpf->framenum <= cframe) {
          found = true;
          break;
        }
      }

      /* set the appropriate frame */
      if (addnew) {
        if ((found) && (gpf->framenum == cframe)) {
          gpl->actframe = gpf;
        }
        else if (addnew == GP_GETFRAME_ADD_COPY) {
          gpl->actframe = BKE_gpencil_frame_addcopy(gpl, cframe);
        }
        else {
          gpl->actframe = BKE_gpencil_frame_addnew(gpl, cframe);
        }
      }
      else if (found) {
        gpl->actframe = gpf;
      }
      else {
        gpl->actframe = gpl->frames.first;
      }
    }
  }
  else if (gpl->frames.first) {
    /* check which of the ends to start checking from */
    const int first = ((bGPDframe *)(gpl->frames.first))->framenum;
    const int last = ((bGPDframe *)(gpl->frames.last))->framenum;

    if (abs(cframe - first) > abs(cframe - last)) {
      /* find gp-frame which is less than or equal to cframe */
      for (gpf = gpl->frames.last; gpf; gpf = gpf->prev) {
        if (gpf->framenum <= cframe) {
          found = true;
          break;
        }
      }
    }
    else {
      /* find gp-frame which is less than or equal to cframe */
      for (gpf = gpl->frames.first; gpf; gpf = gpf->next) {
        if (gpf->framenum <= cframe) {
          found = true;
          break;
        }
      }
    }

    /* set the appropriate frame */
    if (addnew) {
      if ((found) && (gpf->framenum == cframe)) {
        gpl->actframe = gpf;
      }
      else {
        gpl->actframe = BKE_gpencil_frame_addnew(gpl, cframe);
      }
    }
    else if (found) {
      gpl->actframe = gpf;
    }
    else {
      /* unresolved errogenous situation! */
      CLOG_STR_ERROR(&LOG, "cannot find appropriate gp-frame");
      /* gpl->actframe should still be NULL */
    }
  }
  else {
    /* currently no frames (add if allowed to) */
    if (addnew) {
      gpl->actframe = BKE_gpencil_frame_addnew(gpl, cframe);
    }
    else {
      /* don't do anything... this may be when no frames yet! */
      /* gpl->actframe should still be NULL */
    }
  }

  /* return */
  return gpl->actframe;
}

/* delete the given frame from a layer */
bool BKE_gpencil_layer_delframe(bGPDlayer *gpl, bGPDframe *gpf)
{
  bool changed = false;

  /* error checking */
  if (ELEM(NULL, gpl, gpf)) {
    return false;
  }

  /* if this frame was active, make the previous frame active instead
   * since it's tricky to set active frame otherwise
   */
  if (gpl->actframe == gpf) {
    gpl->actframe = gpf->prev;
  }

  /* free the frame and its data */
  changed = BKE_gpencil_free_strokes(gpf);
  BLI_freelinkN(&gpl->frames, gpf);

  return changed;
}

/* get the active gp-layer for editing */
bGPDlayer *BKE_gpencil_layer_getactive(bGPdata *gpd)
{
  bGPDlayer *gpl;

  /* error checking */
  if (ELEM(NULL, gpd, gpd->layers.first)) {
    return NULL;
  }

  /* loop over layers until found (assume only one active) */
  for (gpl = gpd->layers.first; gpl; gpl = gpl->next) {
    if (gpl->flag & GP_LAYER_ACTIVE) {
      return gpl;
    }
  }

  /* no active layer found */
  return NULL;
}

/* set the active gp-layer */
void BKE_gpencil_layer_setactive(bGPdata *gpd, bGPDlayer *active)
{
  bGPDlayer *gpl;

  /* error checking */
  if (ELEM(NULL, gpd, gpd->layers.first, active)) {
    return;
  }

  /* loop over layers deactivating all */
  for (gpl = gpd->layers.first; gpl; gpl = gpl->next) {
    gpl->flag &= ~GP_LAYER_ACTIVE;
    if (gpd->flag & GP_DATA_AUTOLOCK_LAYERS) {
      gpl->flag |= GP_LAYER_LOCKED;
    }
  }

  /* set as active one */
  active->flag |= GP_LAYER_ACTIVE;
  if (gpd->flag & GP_DATA_AUTOLOCK_LAYERS) {
    active->flag &= ~GP_LAYER_LOCKED;
  }
}

/* Set locked layers for autolock mode. */
void BKE_gpencil_layer_autolock_set(bGPdata *gpd, const bool unlock)
{
  BLI_assert(gpd != NULL);

  bGPDlayer *gpl;

  if (gpd->flag & GP_DATA_AUTOLOCK_LAYERS) {
    bGPDlayer *layer_active = BKE_gpencil_layer_getactive(gpd);

    /* Lock all other layers */
    for (gpl = gpd->layers.first; gpl; gpl = gpl->next) {
      /* unlock active layer */
      if (gpl == layer_active) {
        gpl->flag &= ~GP_LAYER_LOCKED;
      }
      else {
        gpl->flag |= GP_LAYER_LOCKED;
      }
    }
  }
  else {
    /* If disable is better unlock all layers by default or it looks there is
     * a problem in the UI because the user expects all layers will be unlocked
     */
    if (unlock) {
      for (gpl = gpd->layers.first; gpl; gpl = gpl->next) {
        gpl->flag &= ~GP_LAYER_LOCKED;
      }
    }
  }
}

/* delete the active gp-layer */
void BKE_gpencil_layer_delete(bGPdata *gpd, bGPDlayer *gpl)
{
  /* error checking */
  if (ELEM(NULL, gpd, gpl)) {
    return;
  }

  /* free layer */
  BKE_gpencil_free_frames(gpl);

  /* free icon providing preview of icon color */
  BKE_icon_delete(gpl->runtime.icon_id);

  BLI_freelinkN(&gpd->layers, gpl);
}

Material *BKE_gpencil_brush_material_get(Brush *brush)
{
  Material *ma = NULL;

  if ((brush != NULL) && (brush->gpencil_settings != NULL) &&
      (brush->gpencil_settings->material != NULL)) {
    ma = brush->gpencil_settings->material;
  }

  return ma;
}

void BKE_gpencil_brush_material_set(Brush *brush, Material *ma)
{
  BLI_assert(brush);
  BLI_assert(brush->gpencil_settings);
  if (brush->gpencil_settings->material != ma) {
    if (brush->gpencil_settings->material) {
      id_us_min(&brush->gpencil_settings->material->id);
    }
    if (ma) {
      id_us_plus(&ma->id);
    }
    brush->gpencil_settings->material = ma;
  }
}

/* Adds the pinned material to the object if necessary. */
Material *BKE_gpencil_object_material_ensure_from_brush(Main *bmain, Object *ob, Brush *brush)
{
  if (brush->gpencil_settings->flag & GP_BRUSH_MATERIAL_PINNED) {
    Material *ma = BKE_gpencil_brush_material_get(brush);

    /* check if the material is already on object material slots and add it if missing */
    if (ma && BKE_gpencil_object_material_get_index(ob, ma) < 0) {
      BKE_object_material_slot_add(bmain, ob);
      assign_material(bmain, ob, ma, ob->totcol, BKE_MAT_ASSIGN_USERPREF);
    }

    return ma;
  }
  else {
    /* using active material instead */
    return give_current_material(ob, ob->actcol);
  }
}

/* Assigns the material to object (if not already present) and returns its index (mat_nr). */
int BKE_gpencil_object_material_ensure(Main *bmain, Object *ob, Material *material)
{
  if (!material) {
    return -1;
  }
  int index = BKE_gpencil_object_material_get_index(ob, material);
  if (index < 0) {
    BKE_object_material_slot_add(bmain, ob);
    assign_material(bmain, ob, material, ob->totcol, BKE_MAT_ASSIGN_USERPREF);
    return ob->totcol - 1;
  }
  return index;
}

/** Creates a new gpencil material and assigns it to object.
 *
 * \param *r_index: value is set to zero based index of the new material if r_index is not NULL
 */
Material *BKE_gpencil_object_material_new(Main *bmain, Object *ob, const char *name, int *r_index)
{
  Material *ma = BKE_material_add_gpencil(bmain, name);
  id_us_min(&ma->id); /* no users yet */

  BKE_object_material_slot_add(bmain, ob);
  assign_material(bmain, ob, ma, ob->totcol, BKE_MAT_ASSIGN_USERPREF);

  if (r_index) {
    *r_index = ob->actcol - 1;
  }
  return ma;
}

/* Returns the material for a brush with respect to its pinned state. */
Material *BKE_gpencil_object_material_get_from_brush(Object *ob, Brush *brush)
{
  if ((brush) && (brush->gpencil_settings) &&
      (brush->gpencil_settings->flag & GP_BRUSH_MATERIAL_PINNED)) {
    Material *ma = BKE_gpencil_brush_material_get(brush);
    return ma;
  }
  else {
    return give_current_material(ob, ob->actcol);
  }
}

/* Returns the material index for a brush with respect to its pinned state. */
int BKE_gpencil_object_material_get_index_from_brush(Object *ob, Brush *brush)
{
  if ((brush) && (brush->gpencil_settings->flag & GP_BRUSH_MATERIAL_PINNED)) {
    return BKE_gpencil_object_material_get_index(ob, brush->gpencil_settings->material);
  }
  else {
    return ob->actcol - 1;
  }
}

/* Guaranteed to return a material assigned to object. Returns never NULL. */
Material *BKE_gpencil_object_material_ensure_from_active_input_toolsettings(Main *bmain,
                                                                            Object *ob,
                                                                            ToolSettings *ts)
{
  if (ts && ts->gp_paint && ts->gp_paint->paint.brush) {
    return BKE_gpencil_object_material_ensure_from_active_input_brush(
        bmain, ob, ts->gp_paint->paint.brush);
  }
  else {
    return BKE_gpencil_object_material_ensure_from_active_input_brush(bmain, ob, NULL);
  }
}

/* Guaranteed to return a material assigned to object. Returns never NULL. */
Material *BKE_gpencil_object_material_ensure_from_active_input_brush(Main *bmain,
                                                                     Object *ob,
                                                                     Brush *brush)
{
  if (brush) {
    Material *ma = BKE_gpencil_object_material_ensure_from_brush(bmain, ob, brush);
    if (ma) {
      return ma;
    }
    else if (brush->gpencil_settings->flag & GP_BRUSH_MATERIAL_PINNED) {
      /* it is easier to just unpin a NULL material, instead of setting a new one */
      brush->gpencil_settings->flag &= ~GP_BRUSH_MATERIAL_PINNED;
    }
  }
  return BKE_gpencil_object_material_ensure_from_active_input_material(ob);
}

/**
 * Guaranteed to return a material assigned to object. Returns never NULL.
 * Only use this for materials unrelated to user input.
 */
Material *BKE_gpencil_object_material_ensure_from_active_input_material(Object *ob)
{
  Material *ma = give_current_material(ob, ob->actcol);
  if (ma) {
    return ma;
  }

  return &defgpencil_material;
}

/* Get active color, and add all default settings if we don't find anything */
Material *BKE_gpencil_object_material_ensure_active(Object *ob)
{
  Material *ma = NULL;

  /* sanity checks */
  if (ob == NULL) {
    return NULL;
  }

  ma = BKE_gpencil_object_material_ensure_from_active_input_material(ob);
  if (ma->gp_style == NULL) {
    BKE_material_init_gpencil_settings(ma);
  }

  return ma;
}

/* ************************************************** */
/* GP Object - Boundbox Support */

/**
 * Get min/max coordinate bounds for single stroke
 * \return Returns whether we found any selected points
 */
bool BKE_gpencil_stroke_minmax(const bGPDstroke *gps,
                               const bool use_select,
                               float r_min[3],
                               float r_max[3])
{
  const bGPDspoint *pt;
  int i;
  bool changed = false;

  if (ELEM(NULL, gps, r_min, r_max)) {
    return false;
  }

  for (i = 0, pt = gps->points; i < gps->totpoints; i++, pt++) {
    if ((use_select == false) || (pt->flag & GP_SPOINT_SELECT)) {
      minmax_v3v3_v3(r_min, r_max, &pt->x);
      changed = true;
    }
  }
  return changed;
}

/* get min/max bounds of all strokes in GP datablock */
bool BKE_gpencil_data_minmax(const bGPdata *gpd, float r_min[3], float r_max[3])
{
  bool changed = false;

  INIT_MINMAX(r_min, r_max);

  if (gpd == NULL) {
    return changed;
  }

  for (bGPDlayer *gpl = gpd->layers.first; gpl; gpl = gpl->next) {
    bGPDframe *gpf = gpl->actframe;

    if (gpf != NULL) {
      for (bGPDstroke *gps = gpf->strokes.first; gps; gps = gps->next) {
        changed = BKE_gpencil_stroke_minmax(gps, false, r_min, r_max);
      }
    }
  }

  return changed;
}

bool BKE_gpencil_stroke_select_check(const bGPDstroke *gps)
{
  const bGPDspoint *pt;
  int i;
  for (i = 0, pt = gps->points; i < gps->totpoints; i++, pt++) {
    if (pt->flag & GP_SPOINT_SELECT) {
      return true;
    }
  }
  return false;
}

/* compute center of bounding box */
void BKE_gpencil_centroid_3d(bGPdata *gpd, float r_centroid[3])
{
  float min[3], max[3], tot[3];

  BKE_gpencil_data_minmax(gpd, min, max);

  add_v3_v3v3(tot, min, max);
  mul_v3_v3fl(r_centroid, tot, 0.5f);
}

/* create bounding box values */
static void boundbox_gpencil(Object *ob)
{
  BoundBox *bb;
  bGPdata *gpd;
  float min[3], max[3];

  if (ob->runtime.bb == NULL) {
    ob->runtime.bb = MEM_callocN(sizeof(BoundBox), "GPencil boundbox");
  }

  bb = ob->runtime.bb;
  gpd = ob->data;

  if (!BKE_gpencil_data_minmax(gpd, min, max)) {
    min[0] = min[1] = min[2] = -1.0f;
    max[0] = max[1] = max[2] = 1.0f;
  }

  BKE_boundbox_init_from_minmax(bb, min, max);

  bb->flag &= ~BOUNDBOX_DIRTY;
}

/* get bounding box */
BoundBox *BKE_gpencil_boundbox_get(Object *ob)
{
  if (ELEM(NULL, ob, ob->data)) {
    return NULL;
  }

  bGPdata *gpd = (bGPdata *)ob->data;
  if ((ob->runtime.bb) && ((gpd->flag & GP_DATA_CACHE_IS_DIRTY) == 0)) {
    return ob->runtime.bb;
  }

  boundbox_gpencil(ob);

  return ob->runtime.bb;
}

/* ************************************************** */
/* Apply Transforms */

void BKE_gpencil_transform(bGPdata *gpd, float mat[4][4])
{
  if (gpd == NULL) {
    return;
  }

  const float scalef = mat4_to_scale(mat);
  for (bGPDlayer *gpl = gpd->layers.first; gpl; gpl = gpl->next) {
    /* FIXME: For now, we just skip parented layers.
     * Otherwise, we have to update each frame to find
     * the current parent position/effects.
     */
    if (gpl->parent) {
      continue;
    }

    for (bGPDframe *gpf = gpl->frames.first; gpf; gpf = gpf->next) {
      for (bGPDstroke *gps = gpf->strokes.first; gps; gps = gps->next) {
        bGPDspoint *pt;
        int i;

        for (pt = gps->points, i = 0; i < gps->totpoints; pt++, i++) {
          mul_m4_v3(mat, &pt->x);
          pt->pressure *= scalef;
        }

        /* TODO: Do we need to do this? distortion may mean we need to re-triangulate */
        gps->flag |= GP_STROKE_RECALC_GEOMETRY;
        gps->tot_triangles = 0;
      }
    }
  }
}

/* ************************************************** */
/* GP Object - Vertex Groups */

/* remove a vertex group */
void BKE_gpencil_vgroup_remove(Object *ob, bDeformGroup *defgroup)
{
  bGPdata *gpd = ob->data;
  MDeformVert *dvert = NULL;
  const int def_nr = BLI_findindex(&ob->defbase, defgroup);
  const int totgrp = BLI_listbase_count(&ob->defbase);

  /* Remove points data */
  if (gpd) {
    for (bGPDlayer *gpl = gpd->layers.first; gpl; gpl = gpl->next) {
      for (bGPDframe *gpf = gpl->frames.first; gpf; gpf = gpf->next) {
        for (bGPDstroke *gps = gpf->strokes.first; gps; gps = gps->next) {
          if (gps->dvert != NULL) {
            for (int i = 0; i < gps->totpoints; i++) {
              dvert = &gps->dvert[i];
              MDeformWeight *dw = defvert_find_index(dvert, def_nr);
              if (dw != NULL) {
                defvert_remove_group(dvert, dw);
              }
              else {
                /* Reorganize weights for other groups after deleted one. */
                for (int g = 0; g < totgrp; g++) {
                  dw = defvert_find_index(dvert, g);
                  if ((dw != NULL) && (dw->def_nr > def_nr)) {
                    dw->def_nr--;
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  /* Remove the group */
  BLI_freelinkN(&ob->defbase, defgroup);
  DEG_id_tag_update(&gpd->id, ID_RECALC_TRANSFORM | ID_RECALC_GEOMETRY);
}

void BKE_gpencil_dvert_ensure(bGPDstroke *gps)
{
  if (gps->dvert == NULL) {
    gps->dvert = MEM_callocN(sizeof(MDeformVert) * gps->totpoints, "gp_stroke_weights");
  }
}

/* ************************************************** */

static void stroke_defvert_create_nr_list(MDeformVert *dv_list,
                                          int count,
                                          ListBase *result,
                                          int *totweight)
{
  LinkData *ld;
  MDeformVert *dv;
  MDeformWeight *dw;
  int i, j;
  int tw = 0;
  for (i = 0; i < count; i++) {
    dv = &dv_list[i];

    /* find def_nr in list, if not exist, then create one */
    for (j = 0; j < dv->totweight; j++) {
      bool found = false;
      dw = &dv->dw[j];
      for (ld = result->first; ld; ld = ld->next) {
        if (ld->data == POINTER_FROM_INT(dw->def_nr)) {
          found = true;
          break;
        }
      }
      if (!found) {
        ld = MEM_callocN(sizeof(LinkData), "def_nr_item");
        ld->data = POINTER_FROM_INT(dw->def_nr);
        BLI_addtail(result, ld);
        tw++;
      }
    }
  }

  *totweight = tw;
}

static MDeformVert *stroke_defvert_new_count(int count, int totweight, ListBase *def_nr_list)
{
  int i, j;
  LinkData *ld;
  MDeformVert *dst = MEM_mallocN(count * sizeof(MDeformVert), "new_deformVert");

  for (i = 0; i < count; i++) {
    dst[i].dw = MEM_mallocN(sizeof(MDeformWeight) * totweight, "new_deformWeight");
    dst[i].totweight = totweight;
    j = 0;
    /* re-assign deform groups */
    for (ld = def_nr_list->first; ld; ld = ld->next) {
      dst[i].dw[j].def_nr = POINTER_AS_INT(ld->data);
      j++;
    }
  }

  return dst;
}

static void stroke_interpolate_deform_weights(
    bGPDstroke *gps, int index_from, int index_to, float ratio, MDeformVert *vert)
{
  const MDeformVert *vl = &gps->dvert[index_from];
  const MDeformVert *vr = &gps->dvert[index_to];
  int i;

  for (i = 0; i < vert->totweight; i++) {
    float wl = defvert_find_weight(vl, vert->dw[i].def_nr);
    float wr = defvert_find_weight(vr, vert->dw[i].def_nr);
    vert->dw[i].weight = interpf(wr, wl, ratio);
  }
}

static int stroke_march_next_point(const bGPDstroke *gps,
                                   const int index_next_pt,
                                   const float *current,
                                   const float dist,
                                   float *result,
                                   float *pressure,
                                   float *strength,
                                   float *ratio_result,
                                   int *index_from,
                                   int *index_to)
{
  float remaining_till_next = 0.0f;
  float remaining_march = dist;
  float step_start[3];
  float point[3];
  int next_point_index = index_next_pt;
  bGPDspoint *pt = NULL;

  if (!(next_point_index < gps->totpoints)) {
    return -1;
  }

  copy_v3_v3(step_start, current);
  pt = &gps->points[next_point_index];
  copy_v3_v3(point, &pt->x);
  remaining_till_next = len_v3v3(point, step_start);

  while (remaining_till_next < remaining_march) {
    remaining_march -= remaining_till_next;
    pt = &gps->points[next_point_index];
    copy_v3_v3(point, &pt->x);
    copy_v3_v3(step_start, point);
    next_point_index++;
    if (!(next_point_index < gps->totpoints)) {
      next_point_index = gps->totpoints - 1;
      break;
    }
    pt = &gps->points[next_point_index];
    copy_v3_v3(point, &pt->x);
    remaining_till_next = len_v3v3(point, step_start);
  }
  if (remaining_till_next < remaining_march) {
    pt = &gps->points[next_point_index];
    copy_v3_v3(result, &pt->x);
    *pressure = gps->points[next_point_index].pressure;
    *strength = gps->points[next_point_index].strength;

    *index_from = next_point_index - 1;
    *index_to = next_point_index;
    *ratio_result = 1.0f;

    return 0;
  }
  else {
    float ratio = remaining_march / remaining_till_next;
    interp_v3_v3v3(result, step_start, point, ratio);
    *pressure = interpf(
        gps->points[next_point_index].pressure, gps->points[next_point_index - 1].pressure, ratio);
    *strength = interpf(
        gps->points[next_point_index].strength, gps->points[next_point_index - 1].strength, ratio);

    *index_from = next_point_index - 1;
    *index_to = next_point_index;
    *ratio_result = ratio;

    return next_point_index;
  }
}

static int stroke_march_next_point_no_interp(const bGPDstroke *gps,
                                             const int index_next_pt,
                                             const float *current,
                                             const float dist,
                                             float *result)
{
  float remaining_till_next = 0.0f;
  float remaining_march = dist;
  float step_start[3];
  float point[3];
  int next_point_index = index_next_pt;
  bGPDspoint *pt = NULL;

  if (!(next_point_index < gps->totpoints)) {
    return -1;
  }

  copy_v3_v3(step_start, current);
  pt = &gps->points[next_point_index];
  copy_v3_v3(point, &pt->x);
  remaining_till_next = len_v3v3(point, step_start);

  while (remaining_till_next < remaining_march) {
    remaining_march -= remaining_till_next;
    pt = &gps->points[next_point_index];
    copy_v3_v3(point, &pt->x);
    copy_v3_v3(step_start, point);
    next_point_index++;
    if (!(next_point_index < gps->totpoints)) {
      next_point_index = gps->totpoints - 1;
      break;
    }
    pt = &gps->points[next_point_index];
    copy_v3_v3(point, &pt->x);
    remaining_till_next = len_v3v3(point, step_start);
  }
  if (remaining_till_next < remaining_march) {
    pt = &gps->points[next_point_index];
    copy_v3_v3(result, &pt->x);
    return 0;
  }
  else {
    float ratio = remaining_march / remaining_till_next;
    interp_v3_v3v3(result, step_start, point, ratio);
    return next_point_index;
  }
}

static int stroke_march_count(const bGPDstroke *gps, const float dist)
{
  int point_count = 0;
  float point[3];
  int next_point_index = 1;
  bGPDspoint *pt = NULL;

  pt = &gps->points[0];
  copy_v3_v3(point, &pt->x);
  point_count++;

  while ((next_point_index = stroke_march_next_point_no_interp(
              gps, next_point_index, point, dist, point)) > -1) {
    point_count++;
    if (next_point_index == 0) {
      break; /* last point finished */
    }
  }
  return point_count;
}

/**
 * Resample a stroke
 * \param gps: Stroke to sample
 * \param dist: Distance of one segment
 */
bool BKE_gpencil_sample_stroke(bGPDstroke *gps, const float dist, const bool select)
{
  bGPDspoint *pt = gps->points;
  bGPDspoint *pt1 = NULL;
  bGPDspoint *pt2 = NULL;
  int i;
  LinkData *ld;
  ListBase def_nr_list = {0};

  if (gps->totpoints < 2 || dist < FLT_EPSILON) {
    return false;
  }
  /* TODO: Implement feature point preservation. */
  int count = stroke_march_count(gps, dist);

  bGPDspoint *new_pt = MEM_callocN(sizeof(bGPDspoint) * count, "gp_stroke_points_sampled");
  MDeformVert *new_dv = NULL;

  int result_totweight;

  if (gps->dvert != NULL) {
    stroke_defvert_create_nr_list(gps->dvert, gps->totpoints, &def_nr_list, &result_totweight);
    new_dv = stroke_defvert_new_count(count, result_totweight, &def_nr_list);
  }

  int next_point_index = 1;
  i = 0;
  float pressure, strength, ratio_result;
  int index_from, index_to;
  float last_coord[3];

  /*  1st point is always at the start */
  pt1 = &gps->points[0];
  copy_v3_v3(last_coord, &pt1->x);
  pt2 = &new_pt[i];
  copy_v3_v3(&pt2->x, last_coord);
  new_pt[i].pressure = pt[0].pressure;
  new_pt[i].strength = pt[0].strength;
  if (select) {
    new_pt[i].flag |= GP_SPOINT_SELECT;
  }
  i++;

  if (new_dv) {
    stroke_interpolate_deform_weights(gps, 0, 0, 0, &new_dv[0]);
  }

  /*  the rest */
  while ((next_point_index = stroke_march_next_point(gps,
                                                     next_point_index,
                                                     last_coord,
                                                     dist,
                                                     last_coord,
                                                     &pressure,
                                                     &strength,
                                                     &ratio_result,
                                                     &index_from,
                                                     &index_to)) > -1) {
    pt2 = &new_pt[i];
    copy_v3_v3(&pt2->x, last_coord);
    new_pt[i].pressure = pressure;
    new_pt[i].strength = strength;
    if (select) {
      new_pt[i].flag |= GP_SPOINT_SELECT;
    }

    if (new_dv) {
      stroke_interpolate_deform_weights(gps, index_from, index_to, ratio_result, &new_dv[i]);
    }

    i++;
    if (next_point_index == 0) {
      break; /* last point finished */
    }
  }

  gps->points = new_pt;
  /* Free original vertex list. */
  MEM_freeN(pt);

  if (new_dv) {
    /* Free original weight data. */
    BKE_gpencil_free_stroke_weights(gps);
    MEM_freeN(gps->dvert);
    while ((ld = BLI_pophead(&def_nr_list))) {
      MEM_freeN(ld);
    }

    gps->dvert = new_dv;
  }

  gps->totpoints = i;

  gps->flag |= GP_STROKE_RECALC_GEOMETRY;
  gps->tot_triangles = 0;

  return true;
}

/**
 * Apply smooth to stroke point
 * \param gps: Stroke to smooth
 * \param i: Point index
 * \param inf: Amount of smoothing to apply
 */
bool BKE_gpencil_smooth_stroke(bGPDstroke *gps, int i, float inf)
{
  bGPDspoint *pt = &gps->points[i];
  float sco[3] = {0.0f};

  /* Do nothing if not enough points to smooth out */
  if (gps->totpoints <= 2) {
    return false;
  }

  /* Only affect endpoints by a fraction of the normal strength,
   * to prevent the stroke from shrinking too much
   */
  if ((i == 0) || (i == gps->totpoints - 1)) {
    inf *= 0.1f;
  }

  /* Compute smoothed coordinate by taking the ones nearby */
  /* XXX: This is potentially slow,
   *      and suffers from accumulation error as earlier points are handled before later ones. */
  {
    /* XXX: this is hardcoded to look at 2 points on either side of the current one
     * (i.e. 5 items total). */
    const int steps = 2;
    const float average_fac = 1.0f / (float)(steps * 2 + 1);
    int step;

    /* add the point itself */
    madd_v3_v3fl(sco, &pt->x, average_fac);

    /* n-steps before/after current point */
    /* XXX: review how the endpoints are treated by this algorithm. */
    /* XXX: falloff measures should also introduce some weighting variations,
     *      so that further-out points get less weight. */
    for (step = 1; step <= steps; step++) {
      bGPDspoint *pt1, *pt2;
      int before = i - step;
      int after = i + step;

      CLAMP_MIN(before, 0);
      CLAMP_MAX(after, gps->totpoints - 1);

      pt1 = &gps->points[before];
      pt2 = &gps->points[after];

      /* add both these points to the average-sum (s += p[i]/n) */
      madd_v3_v3fl(sco, &pt1->x, average_fac);
      madd_v3_v3fl(sco, &pt2->x, average_fac);
    }
  }

  /* Based on influence factor, blend between original and optimal smoothed coordinate */
  interp_v3_v3v3(&pt->x, &pt->x, sco, inf);

  return true;
}

/**
 * Apply smooth for strength to stroke point */
bool BKE_gpencil_smooth_stroke_strength(bGPDstroke *gps, int point_index, float influence)
{
  bGPDspoint *ptb = &gps->points[point_index];

  /* Do nothing if not enough points */
  if ((gps->totpoints <= 2) || (point_index < 1)) {
    return false;
  }
  /* Only affect endpoints by a fraction of the normal influence */
  float inf = influence;
  if ((point_index == 0) || (point_index == gps->totpoints - 1)) {
    inf *= 0.01f;
  }
  /* Limit max influence to reduce pop effect. */
  CLAMP_MAX(inf, 0.98f);

  float total = 0.0f;
  float max_strength = 0.0f;
  const int steps = 4;
  const float average_fac = 1.0f / (float)(steps * 2 + 1);
  int step;

  /* add the point itself */
  total += ptb->strength * average_fac;
  max_strength = ptb->strength;

  /* n-steps before/after current point */
  for (step = 1; step <= steps; step++) {
    bGPDspoint *pt1, *pt2;
    int before = point_index - step;
    int after = point_index + step;

    CLAMP_MIN(before, 0);
    CLAMP_MAX(after, gps->totpoints - 1);

    pt1 = &gps->points[before];
    pt2 = &gps->points[after];

    /* add both these points to the average-sum (s += p[i]/n) */
    total += pt1->strength * average_fac;
    total += pt2->strength * average_fac;
    /* Save max value. */
    if (max_strength < pt1->strength) {
      max_strength = pt1->strength;
    }
    if (max_strength < pt2->strength) {
      max_strength = pt2->strength;
    }
  }

  /* Based on influence factor, blend between original and optimal smoothed value. */
  ptb->strength = interpf(ptb->strength, total, inf);
  /* Clamp to maximum stroke strength to avoid weird results. */
  CLAMP_MAX(ptb->strength, max_strength);

  return true;
}

/**
 * Apply smooth for thickness to stroke point (use pressure) */
bool BKE_gpencil_smooth_stroke_thickness(bGPDstroke *gps, int point_index, float influence)
{
  bGPDspoint *ptb = &gps->points[point_index];

  /* Do nothing if not enough points */
  if ((gps->totpoints <= 2) || (point_index < 1)) {
    return false;
  }
  /* Only affect endpoints by a fraction of the normal influence */
  float inf = influence;
  if ((point_index == 0) || (point_index == gps->totpoints - 1)) {
    inf *= 0.01f;
  }
  /* Limit max influence to reduce pop effect. */
  CLAMP_MAX(inf, 0.98f);

  float total = 0.0f;
  float max_pressure = 0.0f;
  const int steps = 4;
  const float average_fac = 1.0f / (float)(steps * 2 + 1);
  int step;

  /* add the point itself */
  total += ptb->pressure * average_fac;
  max_pressure = ptb->pressure;

  /* n-steps before/after current point */
  for (step = 1; step <= steps; step++) {
    bGPDspoint *pt1, *pt2;
    int before = point_index - step;
    int after = point_index + step;

    CLAMP_MIN(before, 0);
    CLAMP_MAX(after, gps->totpoints - 1);

    pt1 = &gps->points[before];
    pt2 = &gps->points[after];

    /* add both these points to the average-sum (s += p[i]/n) */
    total += pt1->pressure * average_fac;
    total += pt2->pressure * average_fac;
    /* Save max value. */
    if (max_pressure < pt1->pressure) {
      max_pressure = pt1->pressure;
    }
    if (max_pressure < pt2->pressure) {
      max_pressure = pt2->pressure;
    }
  }

  /* Based on influence factor, blend between original and optimal smoothed value. */
  ptb->pressure = interpf(ptb->pressure, total, inf);
  /* Clamp to maximum stroke thickness to avoid weird results. */
  CLAMP_MAX(ptb->pressure, max_pressure);
  return true;
}

/**
 * Apply smooth for UV rotation to stroke point (use pressure).
 */
bool BKE_gpencil_smooth_stroke_uv(bGPDstroke *gps, int point_index, float influence)
{
  bGPDspoint *ptb = &gps->points[point_index];

  /* Do nothing if not enough points */
  if (gps->totpoints <= 2) {
    return false;
  }

  /* Compute theoretical optimal value */
  bGPDspoint *pta, *ptc;
  int before = point_index - 1;
  int after = point_index + 1;

  CLAMP_MIN(before, 0);
  CLAMP_MAX(after, gps->totpoints - 1);

  pta = &gps->points[before];
  ptc = &gps->points[after];

  /* the optimal value is the corresponding to the interpolation of the pressure
   * at the distance of point b
   */
  float fac = line_point_factor_v3(&ptb->x, &pta->x, &ptc->x);
  /* sometimes the factor can be wrong due stroke geometry, so use middle point */
  if ((fac < 0.0f) || (fac > 1.0f)) {
    fac = 0.5f;
  }
  float optimal = interpf(ptc->uv_rot, pta->uv_rot, fac);

  /* Based on influence factor, blend between original and optimal */
  ptb->uv_rot = interpf(optimal, ptb->uv_rot, influence);
  CLAMP(ptb->uv_rot, -M_PI_2, M_PI_2);

  return true;
}

/**
 * Get range of selected frames in layer.
 * Always the active frame is considered as selected, so if no more selected the range
 * will be equal to the current active frame.
 * \param gpl: Layer
 * \param r_initframe: Number of first selected frame
 * \param r_endframe: Number of last selected frame
 */
void BKE_gpencil_get_range_selected(bGPDlayer *gpl, int *r_initframe, int *r_endframe)
{
  *r_initframe = gpl->actframe->framenum;
  *r_endframe = gpl->actframe->framenum;

  for (bGPDframe *gpf = gpl->frames.first; gpf; gpf = gpf->next) {
    if (gpf->flag & GP_FRAME_SELECT) {
      if (gpf->framenum < *r_initframe) {
        *r_initframe = gpf->framenum;
      }
      if (gpf->framenum > *r_endframe) {
        *r_endframe = gpf->framenum;
      }
    }
  }
}

/**
 * Get Falloff factor base on frame range
 * \param gpf: Frame
 * \param actnum: Number of active frame in layer
 * \param f_init: Number of first selected frame
 * \param f_end: Number of last selected frame
 * \param cur_falloff: Curve with falloff factors
 */
float BKE_gpencil_multiframe_falloff_calc(
    bGPDframe *gpf, int actnum, int f_init, int f_end, CurveMapping *cur_falloff)
{
  float fnum = 0.5f; /* default mid curve */
  float value;

  /* check curve is available */
  if (cur_falloff == NULL) {
    return 1.0f;
  }

  /* frames to the right of the active frame */
  if (gpf->framenum < actnum) {
    fnum = (float)(gpf->framenum - f_init) / (actnum - f_init);
    fnum *= 0.5f;
    value = BKE_curvemapping_evaluateF(cur_falloff, 0, fnum);
  }
  /* frames to the left of the active frame */
  else if (gpf->framenum > actnum) {
    fnum = (float)(gpf->framenum - actnum) / (f_end - actnum);
    fnum *= 0.5f;
    value = BKE_curvemapping_evaluateF(cur_falloff, 0, fnum + 0.5f);
  }
  else {
    value = 1.0f;
  }

  return value;
}

/* reassign strokes using a material */
void BKE_gpencil_material_index_reassign(bGPdata *gpd, int totcol, int index)
{
  for (bGPDlayer *gpl = gpd->layers.first; gpl; gpl = gpl->next) {
    for (bGPDframe *gpf = gpl->frames.first; gpf; gpf = gpf->next) {
      for (bGPDstroke *gps = gpf->strokes.first; gps; gps = gps->next) {
        /* reassign strokes */
        if ((gps->mat_nr > index) || (gps->mat_nr > totcol - 1)) {
          gps->mat_nr--;
          CLAMP_MIN(gps->mat_nr, 0);
        }
      }
    }
  }
}

/* remove strokes using a material */
bool BKE_gpencil_material_index_used(bGPdata *gpd, int index)
{
  for (bGPDlayer *gpl = gpd->layers.first; gpl; gpl = gpl->next) {
    for (bGPDframe *gpf = gpl->frames.first; gpf; gpf = gpf->next) {
      for (bGPDstroke *gps = gpf->strokes.first; gps; gps = gps->next) {
        if (gps->mat_nr == index) {
          return true;
        }
      }
    }
  }

  return false;
}

void BKE_gpencil_material_remap(struct bGPdata *gpd,
                                const unsigned int *remap,
                                unsigned int remap_len)
{
  const short remap_len_short = (short)remap_len;

#define MAT_NR_REMAP(n) \
  if (n < remap_len_short) { \
    BLI_assert(n >= 0 && remap[n] < remap_len_short); \
    n = remap[n]; \
  } \
  ((void)0)

  for (bGPDlayer *gpl = gpd->layers.first; gpl; gpl = gpl->next) {
    for (bGPDframe *gpf = gpl->frames.first; gpf; gpf = gpf->next) {
      for (bGPDstroke *gps = gpf->strokes.first; gps; gps = gps->next) {
        /* reassign strokes */
        MAT_NR_REMAP(gps->mat_nr);
      }
    }
  }

#undef MAT_NR_REMAP
}

/* statistics functions */
void BKE_gpencil_stats_update(bGPdata *gpd)
{
  gpd->totlayer = 0;
  gpd->totframe = 0;
  gpd->totstroke = 0;
  gpd->totpoint = 0;

  for (bGPDlayer *gpl = gpd->layers.first; gpl; gpl = gpl->next) {
    gpd->totlayer++;
    for (bGPDframe *gpf = gpl->frames.first; gpf; gpf = gpf->next) {
      gpd->totframe++;
      for (bGPDstroke *gps = gpf->strokes.first; gps; gps = gps->next) {
        gpd->totstroke++;
        gpd->totpoint += gps->totpoints;
      }
    }
  }
}

/* get material index (0-based like mat_nr not actcol) */
int BKE_gpencil_object_material_get_index(Object *ob, Material *ma)
{
  short *totcol = give_totcolp(ob);
  Material *read_ma = NULL;
  for (short i = 0; i < *totcol; i++) {
    read_ma = give_current_material(ob, i + 1);
    if (ma == read_ma) {
      return i;
    }
  }

  return -1;
}

/* Get points of stroke always flat to view not affected by camera view or view position */
void BKE_gpencil_stroke_2d_flat(const bGPDspoint *points,
                                int totpoints,
                                float (*points2d)[2],
                                int *r_direction)
{
  BLI_assert(totpoints >= 2);

  const bGPDspoint *pt0 = &points[0];
  const bGPDspoint *pt1 = &points[1];
  const bGPDspoint *pt3 = &points[(int)(totpoints * 0.75)];

  float locx[3];
  float locy[3];
  float loc3[3];
  float normal[3];

  /* local X axis (p0 -> p1) */
  sub_v3_v3v3(locx, &pt1->x, &pt0->x);

  /* point vector at 3/4 */
  float v3[3];
  if (totpoints == 2) {
    mul_v3_v3fl(v3, &pt3->x, 0.001f);
  }
  else {
    copy_v3_v3(v3, &pt3->x);
  }

  sub_v3_v3v3(loc3, v3, &pt0->x);

  /* vector orthogonal to polygon plane */
  cross_v3_v3v3(normal, locx, loc3);

  /* local Y axis (cross to normal/x axis) */
  cross_v3_v3v3(locy, normal, locx);

  /* Normalize vectors */
  normalize_v3(locx);
  normalize_v3(locy);

  /* Get all points in local space */
  for (int i = 0; i < totpoints; i++) {
    const bGPDspoint *pt = &points[i];
    float loc[3];

    /* Get local space using first point as origin */
    sub_v3_v3v3(loc, &pt->x, &pt0->x);

    points2d[i][0] = dot_v3v3(loc, locx);
    points2d[i][1] = dot_v3v3(loc, locy);
  }

  /* Concave (-1), Convex (1), or Autodetect (0)? */
  *r_direction = (int)locy[2];
}

/* Get points of stroke always flat to view not affected by camera view or view position
 * using another stroke as reference
 */
void BKE_gpencil_stroke_2d_flat_ref(const bGPDspoint *ref_points,
                                    int ref_totpoints,
                                    const bGPDspoint *points,
                                    int totpoints,
                                    float (*points2d)[2],
                                    const float scale,
                                    int *r_direction)
{
  BLI_assert(totpoints >= 2);

  const bGPDspoint *pt0 = &ref_points[0];
  const bGPDspoint *pt1 = &ref_points[1];
  const bGPDspoint *pt3 = &ref_points[(int)(ref_totpoints * 0.75)];

  float locx[3];
  float locy[3];
  float loc3[3];
  float normal[3];

  /* local X axis (p0 -> p1) */
  sub_v3_v3v3(locx, &pt1->x, &pt0->x);

  /* point vector at 3/4 */
  float v3[3];
  if (totpoints == 2) {
    mul_v3_v3fl(v3, &pt3->x, 0.001f);
  }
  else {
    copy_v3_v3(v3, &pt3->x);
  }

  sub_v3_v3v3(loc3, v3, &pt0->x);

  /* vector orthogonal to polygon plane */
  cross_v3_v3v3(normal, locx, loc3);

  /* local Y axis (cross to normal/x axis) */
  cross_v3_v3v3(locy, normal, locx);

  /* Normalize vectors */
  normalize_v3(locx);
  normalize_v3(locy);

  /* Get all points in local space */
  for (int i = 0; i < totpoints; i++) {
    const bGPDspoint *pt = &points[i];
    float loc[3];
    float v1[3];
    float vn[3] = {0.0f, 0.0f, 0.0f};

    /* apply scale to extremes of the stroke to get better collision detection
     * the scale is divided to get more control in the UI parameter
     */
    /* first point */
    if (i == 0) {
      const bGPDspoint *pt_next = &points[i + 1];
      sub_v3_v3v3(vn, &pt->x, &pt_next->x);
      normalize_v3(vn);
      mul_v3_fl(vn, scale / 10.0f);
      add_v3_v3v3(v1, &pt->x, vn);
    }
    /* last point */
    else if (i == totpoints - 1) {
      const bGPDspoint *pt_prev = &points[i - 1];
      sub_v3_v3v3(vn, &pt->x, &pt_prev->x);
      normalize_v3(vn);
      mul_v3_fl(vn, scale / 10.0f);
      add_v3_v3v3(v1, &pt->x, vn);
    }
    else {
      copy_v3_v3(v1, &pt->x);
    }

    /* Get local space using first point as origin (ref stroke) */
    sub_v3_v3v3(loc, v1, &pt0->x);

    points2d[i][0] = dot_v3v3(loc, locx);
    points2d[i][1] = dot_v3v3(loc, locy);
  }

  /* Concave (-1), Convex (1), or Autodetect (0)? */
  *r_direction = (int)locy[2];
}

/**
 * Trim stroke to the first intersection or loop
 * \param gps: Stroke data
 */
bool BKE_gpencil_trim_stroke(bGPDstroke *gps)
{
  if (gps->totpoints < 4) {
    return false;
  }
  bool intersect = false;
  int start, end;
  float point[3];
  /* loop segments from start until we have an intersection */
  for (int i = 0; i < gps->totpoints - 2; i++) {
    start = i;
    bGPDspoint *a = &gps->points[start];
    bGPDspoint *b = &gps->points[start + 1];
    for (int j = start + 2; j < gps->totpoints - 1; j++) {
      end = j + 1;
      bGPDspoint *c = &gps->points[j];
      bGPDspoint *d = &gps->points[end];
      float pointb[3];
      /* get intersection */
      if (isect_line_line_v3(&a->x, &b->x, &c->x, &d->x, point, pointb)) {
        if (len_v3(point) > 0.0f) {
          float closest[3];
          /* check intersection is on both lines */
          float lambda = closest_to_line_v3(closest, point, &a->x, &b->x);
          if ((lambda <= 0.0f) || (lambda >= 1.0f)) {
            continue;
          }
          lambda = closest_to_line_v3(closest, point, &c->x, &d->x);
          if ((lambda <= 0.0f) || (lambda >= 1.0f)) {
            continue;
          }
          else {
            intersect = true;
            break;
          }
        }
      }
    }
    if (intersect) {
      break;
    }
  }

  /* trim unwanted points */
  if (intersect) {

    /* save points */
    bGPDspoint *old_points = MEM_dupallocN(gps->points);
    MDeformVert *old_dvert = NULL;
    MDeformVert *dvert_src = NULL;

    if (gps->dvert != NULL) {
      old_dvert = MEM_dupallocN(gps->dvert);
    }

    /* resize gps */
    int newtot = end - start + 1;

    gps->points = MEM_recallocN(gps->points, sizeof(*gps->points) * newtot);
    if (gps->dvert != NULL) {
      gps->dvert = MEM_recallocN(gps->dvert, sizeof(*gps->dvert) * newtot);
    }

    for (int i = 0; i < newtot; i++) {
      int idx = start + i;
      bGPDspoint *pt_src = &old_points[idx];
      bGPDspoint *pt_new = &gps->points[i];
      memcpy(pt_new, pt_src, sizeof(bGPDspoint));
      if (gps->dvert != NULL) {
        dvert_src = &old_dvert[idx];
        MDeformVert *dvert = &gps->dvert[i];
        memcpy(dvert, dvert_src, sizeof(MDeformVert));
        if (dvert_src->dw) {
          memcpy(dvert->dw, dvert_src->dw, sizeof(MDeformWeight));
        }
      }
      if (idx == start || idx == end) {
        copy_v3_v3(&pt_new->x, point);
      }
    }

    gps->flag |= GP_STROKE_RECALC_GEOMETRY;
    gps->tot_triangles = 0;
    gps->totpoints = newtot;

    MEM_SAFE_FREE(old_points);
    MEM_SAFE_FREE(old_dvert);
  }
  return intersect;
}

/**
 * Close stroke
 * \param gps: Stroke to close
 */
bool BKE_gpencil_close_stroke(bGPDstroke *gps)
{
  bGPDspoint *pt1 = NULL;
  bGPDspoint *pt2 = NULL;

  /* Only can close a stroke with 3 points or more. */
  if (gps->totpoints < 3) {
    return false;
  }

  /* Calc average distance between points to get same level of sampling. */
  float dist_tot = 0.0f;
  for (int i = 0; i < gps->totpoints - 1; i++) {
    pt1 = &gps->points[i];
    pt2 = &gps->points[i + 1];
    dist_tot += len_v3v3(&pt1->x, &pt2->x);
  }
  /* Calc the average distance. */
  float dist_avg = dist_tot / (gps->totpoints - 1);

  /* Calc distance between last and first point. */
  pt1 = &gps->points[gps->totpoints - 1];
  pt2 = &gps->points[0];
  float dist_close = len_v3v3(&pt1->x, &pt2->x);

  /* if the distance to close is very small, don't need add points and just enable cyclic. */
  if (dist_close <= dist_avg) {
    gps->flag |= GP_STROKE_CYCLIC;
    return true;
  }

  /* Calc number of points required using the average distance. */
  int tot_newpoints = MAX2(dist_close / dist_avg, 1);

  /* Resize stroke array. */
  int old_tot = gps->totpoints;
  gps->totpoints += tot_newpoints;
  gps->points = MEM_recallocN(gps->points, sizeof(*gps->points) * gps->totpoints);
  if (gps->dvert != NULL) {
    gps->dvert = MEM_recallocN(gps->dvert, sizeof(*gps->dvert) * gps->totpoints);
  }

  /* Generate new points */
  pt1 = &gps->points[old_tot - 1];
  pt2 = &gps->points[0];
  bGPDspoint *pt = &gps->points[old_tot];
  for (int i = 1; i < tot_newpoints + 1; i++, pt++) {
    float step = (tot_newpoints > 1) ? ((float)i / (float)tot_newpoints) : 0.99f;
    /* Clamp last point to be near, but not on top of first point. */
    if ((tot_newpoints > 1) && (i == tot_newpoints)) {
      step *= 0.99f;
    }

    /* Average point. */
    interp_v3_v3v3(&pt->x, &pt1->x, &pt2->x, step);
    pt->pressure = interpf(pt2->pressure, pt1->pressure, step);
    pt->strength = interpf(pt2->strength, pt1->strength, step);
    pt->flag = 0;

    /* Set weights. */
    if (gps->dvert != NULL) {
      MDeformVert *dvert1 = &gps->dvert[old_tot - 1];
      MDeformWeight *dw1 = defvert_verify_index(dvert1, 0);
      float weight_1 = dw1 ? dw1->weight : 0.0f;

      MDeformVert *dvert2 = &gps->dvert[0];
      MDeformWeight *dw2 = defvert_verify_index(dvert2, 0);
      float weight_2 = dw2 ? dw2->weight : 0.0f;

      MDeformVert *dvert_final = &gps->dvert[old_tot + i - 1];
      dvert_final->totweight = 0;
      MDeformWeight *dw = defvert_verify_index(dvert_final, 0);
      if (dvert_final->dw) {
        dw->weight = interpf(weight_2, weight_1, step);
      }
    }
  }

  /* Enable cyclic flag. */
  gps->flag |= GP_STROKE_CYCLIC;

  return true;
}
/* Dissolve points in stroke */
void BKE_gpencil_dissolve_points(bGPDframe *gpf, bGPDstroke *gps, const short tag)
{
  bGPDspoint *pt;
  MDeformVert *dvert = NULL;
  int i;

  int tot = gps->totpoints; /* number of points in new buffer */
  /* first pass: count points to remove */
  /* Count how many points are selected (i.e. how many to remove) */
  for (i = 0, pt = gps->points; i < gps->totpoints; i++, pt++) {
    if (pt->flag & tag) {
      /* selected point - one of the points to remove */
      tot--;
    }
  }

  /* if no points are left, we simply delete the entire stroke */
  if (tot <= 0) {
    /* remove the entire stroke */
    if (gps->points) {
      MEM_freeN(gps->points);
    }
    if (gps->dvert) {
      BKE_gpencil_free_stroke_weights(gps);
      MEM_freeN(gps->dvert);
    }
    if (gps->triangles) {
      MEM_freeN(gps->triangles);
    }
    BLI_freelinkN(&gpf->strokes, gps);
  }
  else {
    /* just copy all points to keep into a smaller buffer */
    bGPDspoint *new_points = MEM_callocN(sizeof(bGPDspoint) * tot, "new gp stroke points copy");
    bGPDspoint *npt = new_points;

    MDeformVert *new_dvert = NULL;
    MDeformVert *ndvert = NULL;

    if (gps->dvert != NULL) {
      new_dvert = MEM_callocN(sizeof(MDeformVert) * tot, "new gp stroke weights copy");
      ndvert = new_dvert;
    }

    (gps->dvert != NULL) ? dvert = gps->dvert : NULL;
    for (i = 0, pt = gps->points; i < gps->totpoints; i++, pt++) {
      if ((pt->flag & tag) == 0) {
        *npt = *pt;
        npt++;

        if (gps->dvert != NULL) {
          *ndvert = *dvert;
          ndvert->dw = MEM_dupallocN(dvert->dw);
          ndvert++;
        }
      }
      if (gps->dvert != NULL) {
        dvert++;
      }
    }

    /* free the old buffer */
    if (gps->points) {
      MEM_freeN(gps->points);
    }
    if (gps->dvert) {
      BKE_gpencil_free_stroke_weights(gps);
      MEM_freeN(gps->dvert);
    }

    /* save the new buffer */
    gps->points = new_points;
    gps->dvert = new_dvert;
    gps->totpoints = tot;

    /* triangles cache needs to be recalculated */
    gps->flag |= GP_STROKE_RECALC_GEOMETRY;
    gps->tot_triangles = 0;
  }
}

/* Merge by distance ------------------------------------- */
/* Reduce a series of points when the distance is below a threshold.
 * Special case for first and last points (both are keeped) for other points,
 * the merge point always is at first point.
 * \param gpf: Grease Pencil frame
 * \param gps: Grease Pencil stroke
 * \param threshold: Distance between points
 * \param use_unselected: Set to true to analyze all stroke and not only selected points
 */
void BKE_gpencil_merge_distance_stroke(bGPDframe *gpf,
                                       bGPDstroke *gps,
                                       const float threshold,
                                       const bool use_unselected)
{
  bGPDspoint *pt = NULL;
  bGPDspoint *pt_next = NULL;
  float tagged = false;
  /* Use square distance to speed up loop */
  const float th_square = threshold * threshold;
  /* Need to have something to merge. */
  if (gps->totpoints < 2) {
    return;
  }
  int i = 0;
  int step = 1;
  while ((i < gps->totpoints - 1) && (i + step < gps->totpoints)) {
    pt = &gps->points[i];
    if (pt->flag & GP_SPOINT_TAG) {
      i++;
      step = 1;
      continue;
    }
    pt_next = &gps->points[i + step];
    /* Do not recalc tagged points. */
    if (pt_next->flag & GP_SPOINT_TAG) {
      step++;
      continue;
    }
    /* Check if contiguous points are selected. */
    if (!use_unselected) {
      if (((pt->flag & GP_SPOINT_SELECT) == 0) || ((pt_next->flag & GP_SPOINT_SELECT) == 0)) {
        i++;
        step = 1;
        continue;
      }
    }
    float len_square = len_squared_v3v3(&pt->x, &pt_next->x);
    if (len_square <= th_square) {
      tagged = true;
      if (i != gps->totpoints - 1) {
        /* Tag second point for delete. */
        pt_next->flag |= GP_SPOINT_TAG;
      }
      else {
        pt->flag |= GP_SPOINT_TAG;
      }
      /* Jump to next pair of points, keeping first point segment equals.*/
      step++;
    }
    else {
      /* Analyze next point. */
      i++;
      step = 1;
    }
  }

  /* Always untag extremes. */
  pt = &gps->points[0];
  pt->flag &= ~GP_SPOINT_TAG;
  pt = &gps->points[gps->totpoints - 1];
  pt->flag &= ~GP_SPOINT_TAG;

  /* Dissolve tagged points */
  if (tagged) {
    BKE_gpencil_dissolve_points(gpf, gps, GP_SPOINT_TAG);
  }
}

/* Helper: Check materials with same color. */
static int gpencil_check_same_material_color(Object *ob_gp, float color[4], Material **r_mat)
{
  Material *ma = NULL;
  float color_cu[4];
  linearrgb_to_srgb_v3_v3(color_cu, color);
  float hsv1[4];
  rgb_to_hsv_v(color_cu, hsv1);
  hsv1[3] = color[3];

  for (int i = 1; i <= ob_gp->totcol; i++) {
    ma = give_current_material(ob_gp, i);
    MaterialGPencilStyle *gp_style = ma->gp_style;
    /* Check color with small tolerance (better in HSV). */
    float hsv2[4];
    rgb_to_hsv_v(gp_style->fill_rgba, hsv2);
    hsv2[3] = gp_style->fill_rgba[3];
    if ((gp_style->fill_style == GP_STYLE_FILL_STYLE_SOLID) && (compare_v4v4(hsv1, hsv2, 0.01f))) {
      *r_mat = ma;
      return i - 1;
    }
  }

  *r_mat = NULL;
  return -1;
}

/* Helper: Add gpencil material using curve material as base. */
static Material *gpencil_add_from_curve_material(Main *bmain,
                                                 Object *ob_gp,
                                                 const float cu_color[4],
                                                 const bool gpencil_lines,
                                                 const bool fill,
                                                 int *r_idx)
{
  Material *mat_gp = BKE_gpencil_object_material_new(
      bmain, ob_gp, (fill) ? "Material" : "Unassigned", r_idx);
  MaterialGPencilStyle *gp_style = mat_gp->gp_style;

  /* Stroke color. */
  if (gpencil_lines) {
    ARRAY_SET_ITEMS(gp_style->stroke_rgba, 0.0f, 0.0f, 0.0f, 1.0f);
    gp_style->flag |= GP_STYLE_STROKE_SHOW;
  }
  else {
    linearrgb_to_srgb_v4(gp_style->stroke_rgba, cu_color);
    gp_style->flag &= ~GP_STYLE_STROKE_SHOW;
  }

  /* Fill color. */
  linearrgb_to_srgb_v4(gp_style->fill_rgba, cu_color);
  /* Fill is false if the original curve hasn't material assigned, so enable it. */
  if (fill) {
    gp_style->flag |= GP_STYLE_FILL_SHOW;
  }

  /* Check at least one is enabled. */
  if (((gp_style->flag & GP_STYLE_STROKE_SHOW) == 0) &&
      ((gp_style->flag & GP_STYLE_FILL_SHOW) == 0)) {
    gp_style->flag |= GP_STYLE_STROKE_SHOW;
  }

  return mat_gp;
}

/* Helper: Create new stroke section. */
static void gpencil_add_new_points(bGPDstroke *gps,
                                   float *coord_array,
                                   float pressure,
                                   int init,
                                   int totpoints,
                                   const float init_co[3],
                                   bool last)
{
  for (int i = 0; i < totpoints; i++) {
    bGPDspoint *pt = &gps->points[i + init];
    copy_v3_v3(&pt->x, &coord_array[3 * i]);
    /* Be sure the last point is not on top of the first point of the curve or
     * the close of the stroke will produce glitches. */
    if ((last) && (i > 0) && (i == totpoints - 1)) {
      float dist = len_v3v3(init_co, &pt->x);
      if (dist < 0.1f) {
        /* Interpolate between previous point and current to back slightly. */
        bGPDspoint *pt_prev = &gps->points[i + init - 1];
        interp_v3_v3v3(&pt->x, &pt_prev->x, &pt->x, 0.95f);
      }
    }

    pt->pressure = pressure;
    pt->strength = 1.0f;
  }
}

/* Helper: Get the first collection that includes the object. */
static Collection *gpencil_get_parent_collection(Scene *scene, Object *ob)
{
  Collection *mycol = NULL;
  FOREACH_SCENE_COLLECTION_BEGIN (scene, collection) {
    for (CollectionObject *cob = collection->gobject.first; cob; cob = cob->next) {
      if ((mycol == NULL) && (cob->ob == ob)) {
        mycol = collection;
      }
    }
  }
  FOREACH_SCENE_COLLECTION_END;

  return mycol;
}

/* Helper: Convert one spline to grease pencil stroke. */
static void gpencil_convert_spline(Main *bmain,
                                   Object *ob_gp,
                                   Object *ob_cu,
                                   const bool gpencil_lines,
                                   const bool only_stroke,
                                   bGPDframe *gpf,
                                   Nurb *nu)
{
  Curve *cu = (Curve *)ob_cu->data;
  bool cyclic = true;

  /* Create Stroke. */
  bGPDstroke *gps = MEM_callocN(sizeof(bGPDstroke), "bGPDstroke");
  gps->thickness = 1.0f;
  gps->gradient_f = 1.0f;
  ARRAY_SET_ITEMS(gps->gradient_s, 1.0f, 1.0f);
  ARRAY_SET_ITEMS(gps->caps, GP_STROKE_CAP_ROUND, GP_STROKE_CAP_ROUND);
  gps->inittime = 0.0f;

  /* Enable recalculation flag by default. */
  gps->flag |= GP_STROKE_RECALC_GEOMETRY;
  gps->flag &= ~GP_STROKE_SELECT;
  gps->flag |= GP_STROKE_3DSPACE;

  gps->mat_nr = 0;
  /* Count total points
   * The total of points must consider that last point of each segment is equal to the first
   * point of next segment.
   */
  int totpoints = 0;
  int segments = 0;
  int resolu = nu->resolu + 1;
  segments = nu->pntsu;
  if (((nu->flagu & CU_NURB_CYCLIC) == 0) || (nu->pntsu == 2)) {
    segments--;
    cyclic = false;
  }
  totpoints = (resolu * segments) - (segments - 1);

  /* Initialize triangle memory to dummy data. */
  gps->tot_triangles = 0;
  gps->triangles = NULL;

  /* Materials
   * Notice: The color of the material is the color of viewport and not the final shader color.
   */
  Material *mat_gp = NULL;
  bool fill = true;
  /* Check if grease pencil has a material with same color.*/
  float color[4];
  if ((cu->mat) && (*cu->mat)) {
    Material *mat_cu = *cu->mat;
    copy_v4_v4(color, &mat_cu->r);
  }
  else {
    /* Gray (unassigned from SVG add-on) */
    zero_v4(color);
    add_v3_fl(color, 0.6f);
    color[3] = 1.0f;
    fill = false;
  }

  /* Special case: If the color was created by the SVG add-on and the name contains '_stroke' and
   * there is only one color, the stroke must not be closed, fill to false and use for
   * stroke the fill color.
   */
  bool do_stroke = false;
  if (ob_cu->totcol == 1) {
    Material *ma_stroke = give_current_material(ob_cu, 1);
    if ((ma_stroke) && (strstr(ma_stroke->id.name, "_stroke") != NULL)) {
      do_stroke = true;
    }
  }

  int r_idx = gpencil_check_same_material_color(ob_gp, color, &mat_gp);
  if ((ob_cu->totcol > 0) && (r_idx < 0)) {
    Material *mat_curve = give_current_material(ob_cu, 1);
    mat_gp = gpencil_add_from_curve_material(bmain, ob_gp, color, gpencil_lines, fill, &r_idx);

    if ((mat_curve) && (mat_curve->gp_style != NULL)) {
      MaterialGPencilStyle *gp_style_cur = mat_curve->gp_style;
      MaterialGPencilStyle *gp_style_gp = mat_gp->gp_style;

      copy_v4_v4(gp_style_gp->mix_rgba, gp_style_cur->mix_rgba);
      gp_style_gp->fill_style = gp_style_cur->fill_style;
      gp_style_gp->mix_factor = gp_style_cur->mix_factor;
      gp_style_gp->gradient_angle = gp_style_cur->gradient_angle;
    }

    /* If object has more than 1 material, use second material for stroke color. */
    if ((!only_stroke) && (ob_cu->totcol > 1) && (give_current_material(ob_cu, 2))) {
      mat_curve = give_current_material(ob_cu, 2);
      if (mat_curve) {
        linearrgb_to_srgb_v3_v3(mat_gp->gp_style->stroke_rgba, &mat_curve->r);
        mat_gp->gp_style->stroke_rgba[3] = mat_curve->a;
      }
    }
    else if ((only_stroke) || (do_stroke)) {
      /* Also use the first color if the fill is none for stroke color. */
      if (ob_cu->totcol > 0) {
        mat_curve = give_current_material(ob_cu, 1);
        if (mat_curve) {
          linearrgb_to_srgb_v3_v3(mat_gp->gp_style->stroke_rgba, &mat_curve->r);
          mat_gp->gp_style->stroke_rgba[3] = mat_curve->a;
          /* Set fill and stroke depending of curve type (3D or 2D). */
          if ((cu->flag & CU_3D) || ((cu->flag & (CU_FRONT | CU_BACK)) == 0)) {
            mat_gp->gp_style->flag |= GP_STYLE_STROKE_SHOW;
            mat_gp->gp_style->flag &= ~GP_STYLE_FILL_SHOW;
          }
          else {
            mat_gp->gp_style->flag &= ~GP_STYLE_STROKE_SHOW;
            mat_gp->gp_style->flag |= GP_STYLE_FILL_SHOW;
          }
        }
      }
    }
  }
  CLAMP_MIN(r_idx, 0);

  /* Assign material index to stroke. */
  gps->mat_nr = r_idx;

  /* Add stroke to frame.*/
  BLI_addtail(&gpf->strokes, gps);

  float *coord_array = NULL;
  float init_co[3];

  switch (nu->type) {
    case CU_POLY: {
      /* Allocate memory for storage points. */
      gps->totpoints = nu->pntsu;
      gps->points = MEM_callocN(sizeof(bGPDspoint) * gps->totpoints, "gp_stroke_points");
      /* Increase thickness for this type. */
      gps->thickness = 10.0f;

      /* Get all curve points */
      for (int s = 0; s < gps->totpoints; s++) {
        BPoint *bp = &nu->bp[s];
        bGPDspoint *pt = &gps->points[s];
        copy_v3_v3(&pt->x, bp->vec);
        pt->pressure = bp->radius;
        pt->strength = 1.0f;
      }
      break;
    }
    case CU_BEZIER: {
      /* Allocate memory for storage points. */
      gps->totpoints = totpoints;
      gps->points = MEM_callocN(sizeof(bGPDspoint) * gps->totpoints, "gp_stroke_points");

      int init = 0;
      resolu = nu->resolu + 1;
      segments = nu->pntsu;
      if (((nu->flagu & CU_NURB_CYCLIC) == 0) || (nu->pntsu == 2)) {
        segments--;
      }
      /* Get all interpolated curve points of Beziert */
      for (int s = 0; s < segments; s++) {
        int inext = (s + 1) % nu->pntsu;
        BezTriple *prevbezt = &nu->bezt[s];
        BezTriple *bezt = &nu->bezt[inext];
        bool last = (bool)(s == segments - 1);

        coord_array = MEM_callocN((size_t)3 * resolu * sizeof(float), __func__);

        for (int j = 0; j < 3; j++) {
          BKE_curve_forward_diff_bezier(prevbezt->vec[1][j],
                                        prevbezt->vec[2][j],
                                        bezt->vec[0][j],
                                        bezt->vec[1][j],
                                        coord_array + j,
                                        resolu - 1,
                                        3 * sizeof(float));
        }
        /* Save first point coordinates. */
        if (s == 0) {
          copy_v3_v3(init_co, &coord_array[0]);
        }
        /* Add points to the stroke */
        gpencil_add_new_points(gps, coord_array, bezt->radius, init, resolu, init_co, last);
        /* Free memory. */
        MEM_SAFE_FREE(coord_array);

        /* As the last point of segment is the first point of next segment, back one array
         * element to avoid duplicated points on the same location.
         */
        init += resolu - 1;
      }
      break;
    }
    case CU_NURBS: {
      if (nu->pntsv == 1) {

        int nurb_points;
        if (nu->flagu & CU_NURB_CYCLIC) {
          resolu++;
          nurb_points = nu->pntsu * resolu;
        }
        else {
          nurb_points = (nu->pntsu - 1) * resolu;
        }
        /* Get all curve points. */
        coord_array = MEM_callocN(sizeof(float[3]) * nurb_points, __func__);
        BKE_nurb_makeCurve(nu, coord_array, NULL, NULL, NULL, resolu, sizeof(float[3]));

        /* Allocate memory for storage points. */
        gps->totpoints = nurb_points - 1;
        gps->points = MEM_callocN(sizeof(bGPDspoint) * gps->totpoints, "gp_stroke_points");

        /* Add points. */
        gpencil_add_new_points(gps, coord_array, 1.0f, 0, gps->totpoints, init_co, false);

        MEM_SAFE_FREE(coord_array);
      }
      break;
    }
    default: {
      break;
    }
  }
  /* Cyclic curve, close stroke. */
  if ((cyclic) && (!do_stroke)) {
    BKE_gpencil_close_stroke(gps);
  }
}

/* Convert a curve object to grease pencil stroke.
 *
 * \param bmain: Main thread pointer
 * \param scene: Original scene.
 * \param ob_gp: Grease pencil object to add strokes.
 * \param ob_cu: Curve to convert.
 * \param gpencil_lines: Use lines for strokes.
 * \param use_collections: Create layers using collection names.
 * \param only_stroke: The material must be only stroke without fill.
 */
void BKE_gpencil_convert_curve(Main *bmain,
                               Scene *scene,
                               Object *ob_gp,
                               Object *ob_cu,
                               const bool gpencil_lines,
                               const bool use_collections,
                               const bool only_stroke)
{
  if (ELEM(NULL, ob_gp, ob_cu) || (ob_gp->type != OB_GPENCIL) || (ob_gp->data == NULL)) {
    return;
  }

  Curve *cu = (Curve *)ob_cu->data;
  bGPdata *gpd = (bGPdata *)ob_gp->data;
  bGPDlayer *gpl = NULL;

  /* If the curve is empty, cancel. */
  if (cu->nurb.first == NULL) {
    return;
  }

  /* Check if there is an active layer. */
  if (use_collections) {
    Collection *collection = gpencil_get_parent_collection(scene, ob_cu);
    if (collection != NULL) {
      gpl = BLI_findstring(&gpd->layers, collection->id.name + 2, offsetof(bGPDlayer, info));
      if (gpl == NULL) {
        gpl = BKE_gpencil_layer_addnew(gpd, collection->id.name + 2, true);
      }
    }
  }

  if (gpl == NULL) {
    gpl = BKE_gpencil_layer_getactive(gpd);
    if (gpl == NULL) {
      gpl = BKE_gpencil_layer_addnew(gpd, DATA_("GP_Layer"), true);
    }
  }

  /* Check if there is an active frame and add if needed. */
  bGPDframe *gpf = BKE_gpencil_layer_getframe(gpl, CFRA, GP_GETFRAME_ADD_COPY);

  /* Read all splines of the curve and create a stroke for each. */
  for (Nurb *nu = cu->nurb.first; nu; nu = nu->next) {
    gpencil_convert_spline(bmain, ob_gp, ob_cu, gpencil_lines, only_stroke, gpf, nu);
  }

  /* Tag for recalculation */
  DEG_id_tag_update(&gpd->id, ID_RECALC_GEOMETRY | ID_RECALC_COPY_ON_WRITE);
}
