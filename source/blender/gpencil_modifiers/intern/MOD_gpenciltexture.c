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
 * The Original Code is Copyright (C) 2017, Blender Foundation
 * This is a new part of Blender
 */

/** \file
 * \ingroup modifiers
 */

#include <stdio.h>

#include "BLI_listbase.h"
#include "BLI_math.h"
#include "BLI_utildefines.h"

#include "DNA_gpencil_modifier_types.h"
#include "DNA_gpencil_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BKE_colortools.h"
#include "BKE_deform.h"
#include "BKE_gpencil.h"
#include "BKE_gpencil_geom.h"
#include "BKE_gpencil_modifier.h"

#include "DEG_depsgraph.h"

#include "MOD_gpencil_modifiertypes.h"
#include "MOD_gpencil_util.h"

static void initData(GpencilModifierData *md)
{
  TextureGpencilModifierData *gpmd = (TextureGpencilModifierData *)md;
  gpmd->fit_method = GP_TEX_CONSTANT_LENGTH;
  gpmd->fill_rotation = 0.0f;
  gpmd->fill_scale = 1.0f;
  gpmd->fill_offset[0] = 0.0f;
  gpmd->fill_offset[1] = 0.0f;
  gpmd->uv_offset = 0.0f;
  gpmd->uv_scale = 1.0f;
  gpmd->pass_index = 0;
  gpmd->layername[0] = '\0';
  gpmd->materialname[0] = '\0';
  gpmd->vgname[0] = '\0';
}

static void copyData(const GpencilModifierData *md, GpencilModifierData *target)
{
  BKE_gpencil_modifier_copydata_generic(md, target);
}

/* change stroke uv texture values */
static void deformStroke(GpencilModifierData *md,
                         Depsgraph *UNUSED(depsgraph),
                         Object *ob,
                         bGPDlayer *gpl,
                         bGPDframe *UNUSED(gpf),
                         bGPDstroke *gps)
{
  TextureGpencilModifierData *mmd = (TextureGpencilModifierData *)md;
  const int def_nr = BKE_object_defgroup_name_index(ob, mmd->vgname);

  if (!is_stroke_affected_by_modifier(ob,
                                      mmd->layername,
                                      mmd->materialname,
                                      mmd->pass_index,
                                      mmd->layer_pass,
                                      1,
                                      gpl,
                                      gps,
                                      mmd->flag & GP_TEX_INVERT_LAYER,
                                      mmd->flag & GP_TEX_INVERT_PASS,
                                      mmd->flag & GP_TEX_INVERT_LAYERPASS,
                                      mmd->flag & GP_TEX_INVERT_MATERIAL)) {
    return;
  }
  if ((mmd->mode == FILL) || (mmd->mode == STROKE_AND_FILL)) {
    gps->uv_rotation += mmd->fill_rotation;
    gps->uv_translation[0] += mmd->fill_offset[0];
    gps->uv_translation[1] += mmd->fill_offset[1];
    gps->uv_scale *= mmd->fill_scale;
    BKE_gpencil_stroke_geometry_update(gps);
  }

  if ((mmd->mode == STROKE) || (mmd->mode == STROKE_AND_FILL)) {
    float totlen = 1.0f;
    if (mmd->fit_method == GP_TEX_FIT_STROKE) {
      totlen = 0.0f;
      for (int i = 1; i < gps->totpoints; i++) {
        totlen += len_v3v3(&gps->points[i - 1].x, &gps->points[i].x);
      }
    }

    for (int i = 0; i < gps->totpoints; i++) {
      bGPDspoint *pt = &gps->points[i];
      MDeformVert *dvert = gps->dvert != NULL ? &gps->dvert[i] : NULL;
      /* Verify point is part of vertex group. */
      float weight = get_modifier_point_weight(
          dvert, (mmd->flag & GP_TEX_INVERT_VGROUP) != 0, def_nr);
      if (weight < 0.0f) {
        continue;
      }

      pt->uv_fac /= totlen;
      pt->uv_fac *= mmd->uv_scale;
      pt->uv_fac += mmd->uv_offset;
    }
  }
}

static void bakeModifier(struct Main *UNUSED(bmain),
                         Depsgraph *depsgraph,
                         GpencilModifierData *md,
                         Object *ob)
{
  bGPdata *gpd = ob->data;

  LISTBASE_FOREACH (bGPDlayer *, gpl, &gpd->layers) {
    LISTBASE_FOREACH (bGPDframe *, gpf, &gpl->frames) {
      LISTBASE_FOREACH (bGPDstroke *, gps, &gpf->strokes) {
        deformStroke(md, depsgraph, ob, gpl, gpf, gps);
      }
    }
  }
}

GpencilModifierTypeInfo modifierType_Gpencil_Texture = {
    /* name */ "Texture Mapping",
    /* structName */ "TextureGpencilModifierData",
    /* structSize */ sizeof(TextureGpencilModifierData),
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
