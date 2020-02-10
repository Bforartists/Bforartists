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
 * along with this program; if not, write to the Free Software  Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2017, Blender Foundation
 * This is a new part of Blender
 */

/** \file
 *  \ingroup modifiers
 */

#include <stdio.h>

#include "MEM_guardedalloc.h"

#include "DNA_scene_types.h"
#include "DNA_object_types.h"
#include "DNA_gpencil_types.h"
#include "DNA_gpencil_modifier_types.h"

#include "BLI_blenlib.h"
#include "BLI_rand.h"
#include "BLI_math.h"
#include "BLI_utildefines.h"
#include "BLI_linklist.h"
#include "BLI_alloca.h"

#include "BKE_gpencil.h"
#include "BKE_gpencil_modifier.h"
#include "BKE_modifier.h"
#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_object.h"
#include "BKE_main.h"
#include "BKE_scene.h"
#include "BKE_layer.h"
#include "BKE_lib_query.h"
#include "BKE_collection.h"
#include "BKE_mesh.h"
#include "BKE_mesh_mapping.h"

#include "bmesh.h"
#include "bmesh_tools.h"

#include "DEG_depsgraph.h"
#include "DEG_depsgraph_build.h"
#include "DEG_depsgraph_query.h"

#include "MOD_gpencil_util.h"
#include "MOD_gpencil_modifiertypes.h"

static void initData(GpencilModifierData *md)
{
  MultiplyGpencilModifierData *mmd = (MultiplyGpencilModifierData *)md;
  mmd->duplications = 3;
  mmd->distance = 0.1f;
  mmd->split_angle = 1.0f;
}

static void copyData(const GpencilModifierData *md, GpencilModifierData *target)
{
  BKE_gpencil_modifier_copyData_generic(md, target);
}

static void splitStroke(bGPDframe *gpf, bGPDstroke *gps, float split_angle)
{
  bGPDspoint *pt = gps->points;
  bGPDstroke *new_gps = gps;
  int i;
  volatile float angle;

  if (split_angle <= FLT_EPSILON) {
    return;
  }

  for (i = 1; i < new_gps->totpoints - 1; i++) {
    angle = angle_v3v3v3(&pt[i - 1].x, &pt[i].x, &pt[i + 1].x);
    if (angle < split_angle) {
      if (BKE_gpencil_split_stroke(gpf, new_gps, i, &new_gps)) {
        pt = new_gps->points;
        i = 0;
        continue; /* then i == 1 again */
      }
    }
  }
}

static void minter_v3_v3v3v3_ref(
    float *result, float *left, float *middle, float *right, float *stroke_normal)
{
  float left_arm[3], right_arm[3], inter1[3], inter2[3];
  float minter[3];
  if (left) {
    sub_v3_v3v3(left_arm, middle, left);
    cross_v3_v3v3(inter1, stroke_normal, left_arm);
  }
  if (right) {
    sub_v3_v3v3(right_arm, right, middle);
    cross_v3_v3v3(inter2, stroke_normal, right_arm);
  }
  if (!left) {
    normalize_v3(inter2);
    copy_v3_v3(result, inter2);
    return;
  }

  if (!right) {
    normalize_v3(inter1);
    copy_v3_v3(result, inter1);
    return;
  }

  interp_v3_v3v3(minter, inter1, inter2, 0.5);
  normalize_v3(minter);
  copy_v3_v3(result, minter);
}

static void duplicateStroke(bGPDstroke *gps,
                            int count,
                            float dist,
                            float offset,
                            ListBase *results,
                            int fading,
                            float fading_center,
                            float fading_thickness,
                            float fading_opacity)
{
  int i;
  bGPDstroke *new_gps;
  float stroke_normal[3];
  float minter[3];
  bGPDspoint *pt;
  float offset_factor;
  float thickness_factor;
  float opacity_factor;

  BKE_gpencil_stroke_normal(gps, stroke_normal);
  if (len_v3(stroke_normal) < FLT_EPSILON) {
    add_v3_fl(stroke_normal, 1);
    normalize_v3(stroke_normal);
  }

  float *t1_array = MEM_callocN(sizeof(float) * 3 * gps->totpoints,
                                "duplicate_temp_result_array_1");
  float *t2_array = MEM_callocN(sizeof(float) * 3 * gps->totpoints,
                                "duplicate_temp_result_array_2");

  pt = gps->points;

  for (int j = 0; j < gps->totpoints; j++) {
    if (j == 0) {
      minter_v3_v3v3v3_ref(minter, NULL, &pt[j].x, &pt[j + 1].x, stroke_normal);
    }
    else if (j == gps->totpoints - 1) {
      minter_v3_v3v3v3_ref(minter, &pt[j - 1].x, &pt[j].x, NULL, stroke_normal);
    }
    else {
      minter_v3_v3v3v3_ref(minter, &pt[j - 1].x, &pt[j].x, &pt[j + 1].x, stroke_normal);
    }
    mul_v3_fl(minter, dist);
    add_v3_v3v3(&t1_array[j * 3], &pt[j].x, minter);
    sub_v3_v3v3(&t2_array[j * 3], &pt[j].x, minter);
  }

  /* This ensures the original stroke is the last one to be processed. */
  for (i = count - 1; i >= 0; i--) {
    if (i != 0) {
      new_gps = BKE_gpencil_stroke_duplicate(gps);
      new_gps->flag |= GP_STROKE_RECALC_GEOMETRY;
      BLI_addtail(results, new_gps);
    }
    else {
      new_gps = gps;
    }

    pt = new_gps->points;

    if (count == 1) {
      offset_factor = 0;
    }
    else {
      offset_factor = (float)i / (float)(count - 1);
    }

    if (fading) {
      thickness_factor = (offset_factor > fading_center) ?
                             (interpf(1 - fading_thickness, 1.0f, offset_factor - fading_center)) :
                             (interpf(
                                 1.0f, 1 - fading_thickness, offset_factor - fading_center + 1));
      opacity_factor = (offset_factor > fading_center) ?
                           (interpf(1 - fading_opacity, 1.0f, offset_factor - fading_center)) :
                           (interpf(1.0f, 1 - fading_opacity, offset_factor - fading_center + 1));
    }

    for (int j = 0; j < new_gps->totpoints; j++) {
      interp_v3_v3v3(&pt[j].x,
                     &t1_array[j * 3],
                     &t2_array[j * 3],
                     interpf(1 + offset, offset, offset_factor));
      if (fading) {
        pt[j].pressure = gps->points[j].pressure * thickness_factor;
        pt[j].strength = gps->points[j].strength * opacity_factor;
      }
    }
  }
  MEM_freeN(t1_array);
  MEM_freeN(t2_array);
}

static void bakeModifier(Main *UNUSED(bmain),
                         Depsgraph *UNUSED(depsgraph),
                         GpencilModifierData *md,
                         Object *ob)
{

  bGPdata *gpd = ob->data;

  for (bGPDlayer *gpl = gpd->layers.first; gpl; gpl = gpl->next) {
    for (bGPDframe *gpf = gpl->frames.first; gpf; gpf = gpf->next) {
      ListBase duplicates = {0};
      MultiplyGpencilModifierData *mmd = (MultiplyGpencilModifierData *)md;
      bGPDstroke *gps;
      for (gps = gpf->strokes.first; gps; gps = gps->next) {
        if (!is_stroke_affected_by_modifier(ob,
                                            mmd->layername,
                                            mmd->materialname,
                                            mmd->pass_index,
                                            mmd->layer_pass,
                                            1,
                                            gpl,
                                            gps,
                                            mmd->flag & GP_MIRROR_INVERT_LAYER,
                                            mmd->flag & GP_MIRROR_INVERT_PASS,
                                            mmd->flag & GP_MIRROR_INVERT_LAYERPASS,
                                            mmd->flag & GP_MIRROR_INVERT_MATERIAL)) {
          continue;
        }
        if (mmd->flags & GP_MULTIPLY_ENABLE_ANGLE_SPLITTING) {
          splitStroke(gpf, gps, mmd->split_angle);
        }
        if (mmd->duplications > 0) {
          duplicateStroke(gps,
                          mmd->duplications,
                          mmd->distance,
                          mmd->offset,
                          &duplicates,
                          mmd->flags & GP_MULTIPLY_ENABLE_FADING,
                          mmd->fading_center,
                          mmd->fading_thickness,
                          mmd->fading_opacity);
        }
      }
      if (duplicates.first) {
        ((bGPDstroke *)gpf->strokes.last)->next = duplicates.first;
        ((bGPDstroke *)duplicates.first)->prev = gpf->strokes.last;
        gpf->strokes.last = duplicates.first;
      }
    }
  }
}

/* -------------------------------- */

/* Generic "generateStrokes" callback */
static void generateStrokes(GpencilModifierData *md,
                            Depsgraph *UNUSED(depsgraph),
                            Object *ob,
                            bGPDlayer *gpl,
                            bGPDframe *gpf)
{
  MultiplyGpencilModifierData *mmd = (MultiplyGpencilModifierData *)md;
  bGPDstroke *gps;
  ListBase duplicates = {0};
  for (gps = gpf->strokes.first; gps; gps = gps->next) {
    if (!is_stroke_affected_by_modifier(ob,
                                        mmd->layername,
                                        mmd->materialname,
                                        mmd->pass_index,
                                        mmd->layer_pass,
                                        1,
                                        gpl,
                                        gps,
                                        mmd->flag & GP_MIRROR_INVERT_LAYER,
                                        mmd->flag & GP_MIRROR_INVERT_PASS,
                                        mmd->flag & GP_MIRROR_INVERT_LAYERPASS,
                                        mmd->flag & GP_MIRROR_INVERT_MATERIAL)) {
      continue;
    }
    if (mmd->flags & GP_MULTIPLY_ENABLE_ANGLE_SPLITTING) {
      splitStroke(gpf, gps, mmd->split_angle);
    }
    if (mmd->duplications > 0) {
      duplicateStroke(gps,
                      mmd->duplications,
                      mmd->distance,
                      mmd->offset,
                      &duplicates,
                      mmd->flags & GP_MULTIPLY_ENABLE_FADING,
                      mmd->fading_center,
                      mmd->fading_thickness,
                      mmd->fading_opacity);
    }
  }
  if (duplicates.first) {
    ((bGPDstroke *)gpf->strokes.last)->next = duplicates.first;
    ((bGPDstroke *)duplicates.first)->prev = gpf->strokes.last;
    gpf->strokes.last = duplicates.first;
  }
}

GpencilModifierTypeInfo modifierType_Gpencil_Multiply = {
    /* name */ "Multiple Strokes",
    /* structName */ "MultiplyGpencilModifierData",
    /* structSize */ sizeof(MultiplyGpencilModifierData),
    /* type */ eGpencilModifierTypeType_Gpencil,
    /* flags */ 0,

    /* copyData */ copyData,

    /* deformStroke */ NULL,
    /* generateStrokes */ generateStrokes,
    /* bakeModifier */ bakeModifier,
    /* remapTime */ NULL,

    /* initData */ initData,
    /* freeData */ NULL,
    /* isDisabled */ NULL,
    /* updateDepsgraph */ NULL,
    /* dependsOnTime */ NULL,
    /* foreachObjectLink */ NULL,
    /* foreachIDLink */ NULL,
    /* foreachTexLink */ NULL,
};
