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
#include "BLI_math_color.h"
#include "BLI_math_vector.h"

#include "DNA_scene_types.h"
#include "DNA_object_types.h"
#include "DNA_gpencil_types.h"
#include "DNA_gpencil_modifier_types.h"

#include "BKE_gpencil.h"
#include "BKE_gpencil_modifier.h"
#include "BKE_main.h"
#include "BKE_material.h"

#include "DEG_depsgraph.h"

#include "MOD_gpencil_util.h"
#include "MOD_gpencil_modifiertypes.h"

static void initData(GpencilModifierData *md)
{
  ColorGpencilModifierData *gpmd = (ColorGpencilModifierData *)md;
  gpmd->pass_index = 0;
  ARRAY_SET_ITEMS(gpmd->hsv, 0.5f, 1.0f, 1.0f);
  gpmd->layername[0] = '\0';
  gpmd->flag |= GP_COLOR_CREATE_COLORS;
  gpmd->modify_color = GP_MODIFY_COLOR_BOTH;
}

static void copyData(const GpencilModifierData *md, GpencilModifierData *target)
{
  BKE_gpencil_modifier_copyData_generic(md, target);
}

/* color correction strokes */
static void deformStroke(GpencilModifierData *md,
                         Depsgraph *UNUSED(depsgraph),
                         Object *ob,
                         bGPDlayer *gpl,
                         bGPDstroke *gps)
{

  ColorGpencilModifierData *mmd = (ColorGpencilModifierData *)md;
  float hsv[3], factor[3];

  if (!is_stroke_affected_by_modifier(ob,
                                      mmd->layername,
                                      mmd->pass_index,
                                      mmd->layer_pass,
                                      1,
                                      gpl,
                                      gps,
                                      mmd->flag & GP_COLOR_INVERT_LAYER,
                                      mmd->flag & GP_COLOR_INVERT_PASS,
                                      mmd->flag & GP_COLOR_INVERT_LAYERPASS)) {
    return;
  }

  copy_v3_v3(factor, mmd->hsv);
  /* keep initial values unchanged, subtracting the default values. */
  factor[0] -= 0.5f;
  factor[1] -= 1.0f;
  factor[2] -= 1.0f;

  if (mmd->modify_color != GP_MODIFY_COLOR_FILL) {
    rgb_to_hsv_v(gps->runtime.tmp_stroke_rgba, hsv);
    add_v3_v3(hsv, factor);
    CLAMP3(hsv, 0.0f, 1.0f);
    hsv_to_rgb_v(hsv, gps->runtime.tmp_stroke_rgba);
  }

  if (mmd->modify_color != GP_MODIFY_COLOR_STROKE) {
    rgb_to_hsv_v(gps->runtime.tmp_fill_rgba, hsv);
    add_v3_v3(hsv, factor);
    CLAMP3(hsv, 0.0f, 1.0f);
    hsv_to_rgb_v(hsv, gps->runtime.tmp_fill_rgba);
  }
}

static void bakeModifier(Main *bmain, Depsgraph *depsgraph, GpencilModifierData *md, Object *ob)
{
  ColorGpencilModifierData *mmd = (ColorGpencilModifierData *)md;
  bGPdata *gpd = ob->data;

  GHash *gh_color = BLI_ghash_str_new("GP_Color modifier");
  for (bGPDlayer *gpl = gpd->layers.first; gpl; gpl = gpl->next) {
    for (bGPDframe *gpf = gpl->frames.first; gpf; gpf = gpf->next) {
      for (bGPDstroke *gps = gpf->strokes.first; gps; gps = gps->next) {

        Material *mat = give_current_material(ob, gps->mat_nr + 1);
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

        deformStroke(md, depsgraph, ob, gpl, gps);

        gpencil_apply_modifier_material(
            bmain, ob, mat, gh_color, gps, (bool)(mmd->flag & GP_COLOR_CREATE_COLORS));
      }
    }
  }
  /* free hash buffers */
  if (gh_color) {
    BLI_ghash_free(gh_color, NULL, NULL);
    gh_color = NULL;
  }
}

GpencilModifierTypeInfo modifierType_Gpencil_Color = {
    /* name */ "Hue/Saturation",
    /* structName */ "ColorGpencilModifierData",
    /* structSize */ sizeof(ColorGpencilModifierData),
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
    /* getDuplicationFactor */ NULL,
};
