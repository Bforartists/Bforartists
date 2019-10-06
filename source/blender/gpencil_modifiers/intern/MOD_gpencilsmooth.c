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

#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_gpencil_types.h"
#include "DNA_gpencil_modifier_types.h"

#include "BKE_deform.h"
#include "BKE_gpencil.h"
#include "BKE_gpencil_modifier.h"

#include "DEG_depsgraph.h"

#include "MOD_gpencil_util.h"
#include "MOD_gpencil_modifiertypes.h"

static void initData(GpencilModifierData *md)
{
  SmoothGpencilModifierData *gpmd = (SmoothGpencilModifierData *)md;
  gpmd->pass_index = 0;
  gpmd->flag |= GP_SMOOTH_MOD_LOCATION;
  gpmd->factor = 0.5f;
  gpmd->layername[0] = '\0';
  gpmd->materialname[0] = '\0';
  gpmd->vgname[0] = '\0';
  gpmd->step = 1;
}

static void copyData(const GpencilModifierData *md, GpencilModifierData *target)
{
  BKE_gpencil_modifier_copyData_generic(md, target);
}

/* aply smooth effect based on stroke direction */
static void deformStroke(GpencilModifierData *md,
                         Depsgraph *UNUSED(depsgraph),
                         Object *ob,
                         bGPDlayer *gpl,
                         bGPDframe *UNUSED(gpf),
                         bGPDstroke *gps)
{
  SmoothGpencilModifierData *mmd = (SmoothGpencilModifierData *)md;
  const int def_nr = defgroup_name_index(ob, mmd->vgname);

  if (!is_stroke_affected_by_modifier(ob,
                                      mmd->layername,
                                      mmd->materialname,
                                      mmd->pass_index,
                                      mmd->layer_pass,
                                      3,
                                      gpl,
                                      gps,
                                      mmd->flag & GP_SMOOTH_INVERT_LAYER,
                                      mmd->flag & GP_SMOOTH_INVERT_PASS,
                                      mmd->flag & GP_SMOOTH_INVERT_LAYERPASS,
                                      mmd->flag & GP_SMOOTH_INVERT_MATERIAL)) {
    return;
  }

  /* smooth stroke */
  if (mmd->factor > 0.0f) {
    for (int r = 0; r < mmd->step; r++) {
      for (int i = 0; i < gps->totpoints; i++) {
        MDeformVert *dvert = gps->dvert != NULL ? &gps->dvert[i] : NULL;

        /* verify vertex group */
        const float weight = get_modifier_point_weight(
            dvert, (mmd->flag & GP_SMOOTH_INVERT_VGROUP) != 0, def_nr);
        if (weight < 0.0f) {
          continue;
        }

        const float val = mmd->factor * weight;
        /* perform smoothing */
        if (mmd->flag & GP_SMOOTH_MOD_LOCATION) {
          BKE_gpencil_smooth_stroke(gps, i, val);
        }
        if (mmd->flag & GP_SMOOTH_MOD_STRENGTH) {
          BKE_gpencil_smooth_stroke_strength(gps, i, val);
        }
        if ((mmd->flag & GP_SMOOTH_MOD_THICKNESS) && (val > 0.0f)) {
          /* thickness need to repeat process several times */
          for (int r2 = 0; r2 < r * 10; r2++) {
            BKE_gpencil_smooth_stroke_thickness(gps, i, val);
          }
        }
        if (mmd->flag & GP_SMOOTH_MOD_UV) {
          BKE_gpencil_smooth_stroke_uv(gps, i, val);
        }
      }
    }
  }
}

static void bakeModifier(struct Main *UNUSED(bmain),
                         Depsgraph *depsgraph,
                         GpencilModifierData *md,
                         Object *ob)
{
  bGPdata *gpd = ob->data;

  for (bGPDlayer *gpl = gpd->layers.first; gpl; gpl = gpl->next) {
    for (bGPDframe *gpf = gpl->frames.first; gpf; gpf = gpf->next) {
      for (bGPDstroke *gps = gpf->strokes.first; gps; gps = gps->next) {
        deformStroke(md, depsgraph, ob, gpl, gpf, gps);
      }
    }
  }
}

GpencilModifierTypeInfo modifierType_Gpencil_Smooth = {
    /* name */ "Smooth",
    /* structName */ "SmoothGpencilModifierData",
    /* structSize */ sizeof(SmoothGpencilModifierData),
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
