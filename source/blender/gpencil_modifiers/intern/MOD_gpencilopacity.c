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
 * \ingroup modifiers
 */

#include <stdio.h>

#include "BLI_utildefines.h"

#include "BLI_blenlib.h"
#include "BLI_ghash.h"
#include "BLI_math_vector.h"

#include "DNA_meshdata_types.h"
#include "DNA_scene_types.h"
#include "DNA_object_types.h"
#include "DNA_gpencil_types.h"
#include "DNA_gpencil_modifier_types.h"

#include "BKE_deform.h"
#include "BKE_material.h"
#include "BKE_gpencil.h"
#include "BKE_gpencil_modifier.h"
#include "BKE_main.h"

#include "DEG_depsgraph.h"

#include "MOD_gpencil_util.h"
#include "MOD_gpencil_modifiertypes.h"

static void initData(GpencilModifierData *md)
{
  OpacityGpencilModifierData *gpmd = (OpacityGpencilModifierData *)md;
  gpmd->pass_index = 0;
  gpmd->factor = 1.0f;
  gpmd->layername[0] = '\0';
  gpmd->materialname[0] = '\0';
  gpmd->vgname[0] = '\0';
  gpmd->flag |= GP_OPACITY_CREATE_COLORS;
  gpmd->modify_color = GP_MODIFY_COLOR_BOTH;
}

static void copyData(const GpencilModifierData *md, GpencilModifierData *target)
{
  BKE_gpencil_modifier_copyData_generic(md, target);
}

/* opacity strokes */
static void deformStroke(GpencilModifierData *md,
                         Depsgraph *UNUSED(depsgraph),
                         Object *ob,
                         bGPDlayer *gpl,
                         bGPDframe *UNUSED(gpf),
                         bGPDstroke *gps)
{
  OpacityGpencilModifierData *mmd = (OpacityGpencilModifierData *)md;
  const int def_nr = defgroup_name_index(ob, mmd->vgname);

  if (!is_stroke_affected_by_modifier(ob,
                                      mmd->layername,
                                      mmd->materialname,
                                      mmd->pass_index,
                                      mmd->layer_pass,
                                      1,
                                      gpl,
                                      gps,
                                      mmd->flag & GP_OPACITY_INVERT_LAYER,
                                      mmd->flag & GP_OPACITY_INVERT_PASS,
                                      mmd->flag & GP_OPACITY_INVERT_LAYERPASS,
                                      mmd->flag & GP_OPACITY_INVERT_MATERIAL)) {
    return;
  }

  if (mmd->opacity_mode == GP_OPACITY_MODE_MATERIAL) {
    if (mmd->modify_color != GP_MODIFY_COLOR_FILL) {
      gps->runtime.tmp_stroke_rgba[3] *= mmd->factor;
      /* if factor is > 1, then force opacity */
      if (mmd->factor > 1.0f) {
        gps->runtime.tmp_stroke_rgba[3] += mmd->factor - 1.0f;
      }
      CLAMP(gps->runtime.tmp_stroke_rgba[3], 0.0f, 1.0f);
    }

    if (mmd->modify_color != GP_MODIFY_COLOR_STROKE) {
      gps->runtime.tmp_fill_rgba[3] *= mmd->factor;
      /* if factor is > 1, then force opacity */
      if (mmd->factor > 1.0f && gps->runtime.tmp_fill_rgba[3] > 1e-5) {
        gps->runtime.tmp_fill_rgba[3] += mmd->factor - 1.0f;
      }
      CLAMP(gps->runtime.tmp_fill_rgba[3], 0.0f, 1.0f);
    }

    /* if opacity > 1.0, affect the strength of the stroke */
    if (mmd->factor > 1.0f) {
      for (int i = 0; i < gps->totpoints; i++) {
        bGPDspoint *pt = &gps->points[i];
        pt->strength += mmd->factor - 1.0f;
        CLAMP(pt->strength, 0.0f, 1.0f);
      }
    }
  }
  /* Apply opacity by strength */
  else {
    for (int i = 0; i < gps->totpoints; i++) {
      bGPDspoint *pt = &gps->points[i];
      MDeformVert *dvert = gps->dvert != NULL ? &gps->dvert[i] : NULL;

      /* verify vertex group */
      float weight = get_modifier_point_weight(
          dvert, (mmd->flag & GP_OPACITY_INVERT_VGROUP) != 0, def_nr);
      if (weight < 0.0f) {
        continue;
      }
      if (def_nr < 0) {
        pt->strength += mmd->factor - 1.0f;
      }
      else {
        /* High factor values, change weight too. */
        if ((mmd->factor > 1.0f) && (weight < 1.0f)) {
          weight += mmd->factor - 1.0f;
          CLAMP(weight, 0.0f, 1.0f);
        }
        pt->strength += (mmd->factor - 1) * weight;
      }
      CLAMP(pt->strength, 0.0f, 1.0f);
    }
  }
}

static void bakeModifier(Main *bmain, Depsgraph *depsgraph, GpencilModifierData *md, Object *ob)
{
  OpacityGpencilModifierData *mmd = (OpacityGpencilModifierData *)md;
  bGPdata *gpd = ob->data;

  GHash *gh_color = BLI_ghash_str_new("GP_Opacity modifier");
  for (bGPDlayer *gpl = gpd->layers.first; gpl; gpl = gpl->next) {
    for (bGPDframe *gpf = gpl->frames.first; gpf; gpf = gpf->next) {
      for (bGPDstroke *gps = gpf->strokes.first; gps; gps = gps->next) {

        Material *mat = BKE_material_gpencil_get(ob, gps->mat_nr + 1);
        if (mat == NULL) {
          continue;
        }
        MaterialGPencilStyle *gp_style = mat->gp_style;
        /* skip stroke if it doesn't have color info */
        if (ELEM(NULL, gp_style)) {
          continue;
        }

        copy_v4_v4(gps->runtime.tmp_stroke_rgba, gp_style->stroke_rgba);
        copy_v4_v4(gps->runtime.tmp_fill_rgba, gp_style->fill_rgba);

        deformStroke(md, depsgraph, ob, gpl, gpf, gps);

        if (mmd->opacity_mode == GP_OPACITY_MODE_MATERIAL) {
          gpencil_apply_modifier_material(
              bmain, ob, mat, gh_color, gps, (bool)(mmd->flag & GP_OPACITY_CREATE_COLORS));
        }
      }
    }
  }
  /* free hash buffers */
  if (gh_color) {
    BLI_ghash_free(gh_color, NULL, NULL);
    gh_color = NULL;
  }
}

GpencilModifierTypeInfo modifierType_Gpencil_Opacity = {
    /* name */ "Opacity",
    /* structName */ "OpacityGpencilModifierData",
    /* structSize */ sizeof(OpacityGpencilModifierData),
    /* type */ eGpencilModifierTypeType_Gpencil,
    /* flags */ eGpencilModifierTypeFlag_SupportsEditmode,

    /* copyData */ copyData,

    /* deformStroke */ deformStroke,
    /* generateStrokes */ NULL,
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
