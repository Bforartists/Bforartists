/* SPDX-FileCopyrightText: 2017 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup modifiers
 */

#include <cstdio>

#include "BLI_utildefines.h"

#include "BLI_listbase.h"
#include "BLI_math_matrix.h"
#include "BLI_math_vector.h"

#include "BLT_translation.h"

#include "DNA_defaults.h"
#include "DNA_gpencil_legacy_types.h"
#include "DNA_gpencil_modifier_types.h"
#include "DNA_material_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"

#include "BKE_colorband.h"
#include "BKE_colortools.h"
#include "BKE_context.h"
#include "BKE_deform.h"
#include "BKE_gpencil_modifier_legacy.h"
#include "BKE_lib_query.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_modifier.h"
#include "BKE_scene.h"
#include "BKE_screen.hh"

#include "MEM_guardedalloc.h"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "RNA_access.hh"

#include "MOD_gpencil_legacy_modifiertypes.h"
#include "MOD_gpencil_legacy_ui_common.h"
#include "MOD_gpencil_legacy_util.h"

#include "DEG_depsgraph.hh"
#include "DEG_depsgraph_build.hh"

static void init_data(GpencilModifierData *md)
{
  TintGpencilModifierData *gpmd = (TintGpencilModifierData *)md;

  BLI_assert(MEMCMP_STRUCT_AFTER_IS_ZERO(gpmd, modifier));

  MEMCPY_STRUCT_AFTER(gpmd, DNA_struct_default_get(TintGpencilModifierData), modifier);

  /* Add default color ramp. */
  gpmd->colorband = BKE_colorband_add(false);
  if (gpmd->colorband) {
    BKE_colorband_init(gpmd->colorband, true);
    CBData *ramp = gpmd->colorband->data;
    ramp[0].r = ramp[0].g = ramp[0].b = ramp[0].a = 1.0f;
    ramp[0].pos = 0.0f;
    ramp[1].r = ramp[1].g = ramp[1].b = 0.0f;
    ramp[1].a = 1.0f;
    ramp[1].pos = 1.0f;

    gpmd->colorband->tot = 2;
  }

  gpmd->curve_intensity = BKE_curvemapping_add(1, 0.0f, 0.0f, 1.0f, 1.0f);
  BKE_curvemapping_init(gpmd->curve_intensity);
}

static void copy_data(const GpencilModifierData *md, GpencilModifierData *target)
{
  TintGpencilModifierData *gmd = (TintGpencilModifierData *)md;
  TintGpencilModifierData *tgmd = (TintGpencilModifierData *)target;

  MEM_SAFE_FREE(tgmd->colorband);

  if (tgmd->curve_intensity != nullptr) {
    BKE_curvemapping_free(tgmd->curve_intensity);
    tgmd->curve_intensity = nullptr;
  }

  BKE_gpencil_modifier_copydata_generic(md, target);

  if (gmd->colorband) {
    tgmd->colorband = static_cast<ColorBand *>(MEM_dupallocN(gmd->colorband));
  }

  tgmd->curve_intensity = BKE_curvemapping_copy(gmd->curve_intensity);
}

/* deform stroke */
static void deform_stroke(GpencilModifierData *md,
                          Depsgraph * /*depsgraph*/,
                          Object *ob,
                          bGPDlayer *gpl,
                          bGPDframe * /*gpf*/,
                          bGPDstroke *gps)
{
  TintGpencilModifierData *mmd = (TintGpencilModifierData *)md;
  if ((mmd->type == GP_TINT_GRADIENT) && (!mmd->object)) {
    return;
  }

  const int def_nr = BKE_object_defgroup_name_index(ob, mmd->vgname);
  const bool use_curve = (mmd->flag & GP_TINT_CUSTOM_CURVE) != 0 && mmd->curve_intensity;
  bool is_inverted = ((mmd->flag & GP_TINT_WEIGHT_FACTOR) == 0) &&
                     ((mmd->flag & GP_TINT_INVERT_VGROUP) != 0);

  if (!is_stroke_affected_by_modifier(ob,
                                      mmd->layername,
                                      mmd->material,
                                      mmd->pass_index,
                                      mmd->layer_pass,
                                      1,
                                      gpl,
                                      gps,
                                      mmd->flag & GP_TINT_INVERT_LAYER,
                                      mmd->flag & GP_TINT_INVERT_PASS,
                                      mmd->flag & GP_TINT_INVERT_LAYERPASS,
                                      mmd->flag & GP_TINT_INVERT_MATERIAL))
  {
    return;
  }
  MaterialGPencilStyle *gp_style = BKE_gpencil_material_settings(ob, gps->mat_nr + 1);
  const bool is_gradient = (mmd->type == GP_TINT_GRADIENT);

  /* If factor > 1.0, affect the strength of the stroke. */
  if (mmd->factor > 1.0f) {
    for (int i = 0; i < gps->totpoints; i++) {
      bGPDspoint *pt = &gps->points[i];
      pt->strength += mmd->factor - 1.0f;
      CLAMP(pt->strength, 0.0f, 1.0f);
    }
  }

  float coba_res[4];
  float matrix[4][4];
  if (is_gradient) {
    mul_m4_m4m4(matrix, mmd->object->world_to_object, ob->object_to_world);
  }

  /* loop points and apply color. */
  bool fill_done = false;
  for (int i = 0; i < gps->totpoints; i++) {
    bGPDspoint *pt = &gps->points[i];
    MDeformVert *dvert = gps->dvert != nullptr ? &gps->dvert[i] : nullptr;

    if (!fill_done) {
      /* Apply to fill. */
      if (mmd->mode != GPPAINT_MODE_STROKE) {
        float fill_factor = mmd->factor;

        /* Use weighted factor. */
        if (mmd->flag & GP_TINT_WEIGHT_FACTOR) {
          /* Use first point for weight. */
          MDeformVert *dvert_fill = (gps->dvert != nullptr) ? &gps->dvert[0] : nullptr;
          float weight = get_modifier_point_weight(dvert_fill, is_inverted, def_nr);
          if (weight >= 0.0f) {
            fill_factor = ((mmd->flag & GP_TINT_INVERT_VGROUP) ? 1.0f - weight : weight);
          }
        }

        /* If not using Vertex Color, use the material color. */
        if ((gp_style != nullptr) && (gps->vert_color_fill[3] == 0.0f) &&
            (gp_style->fill_rgba[3] > 0.0f)) {
          copy_v4_v4(gps->vert_color_fill, gp_style->fill_rgba);
          gps->vert_color_fill[3] = 1.0f;
        }

        if (is_gradient) {
          float center[3];
          add_v3_v3v3(center, gps->boundbox_min, gps->boundbox_max);
          mul_v3_fl(center, 0.5f);
          float pt_loc[3];
          mul_v3_m4v3(pt_loc, matrix, &pt->x);
          float dist = len_v3(pt_loc);
          float mix_factor = clamp_f(dist / mmd->radius, 0.0f, 1.0f);

          BKE_colorband_evaluate(mmd->colorband, mix_factor, coba_res);
          interp_v3_v3v3(gps->vert_color_fill, gps->vert_color_fill, coba_res, mmd->factor);
          gps->vert_color_fill[3] = clamp_f(fill_factor, 0.0f, 1.0f);
        }
        else {
          interp_v3_v3v3(gps->vert_color_fill,
                         gps->vert_color_fill,
                         mmd->rgb,
                         clamp_f(fill_factor, 0.0f, 1.0f));
        }
        /* If no stroke, cancel loop. */
        if (mmd->mode != GPPAINT_MODE_BOTH) {
          break;
        }
      }

      fill_done = true;
    }

    /* Verify vertex group. */
    if (mmd->mode != GPPAINT_MODE_FILL) {
      float weight = get_modifier_point_weight(dvert, is_inverted, def_nr);
      if (weight < 0.0f) {
        continue;
      }

      float factor = mmd->factor;

      /* Custom curve to modulate value. */
      if (use_curve) {
        float value = float(i) / (gps->totpoints - 1);
        weight *= BKE_curvemapping_evaluateF(mmd->curve_intensity, 0, value);
      }

      /* If not using Vertex Color, use the material color. */
      if ((gp_style != nullptr) && (pt->vert_color[3] == 0.0f) &&
          (gp_style->stroke_rgba[3] > 0.0f)) {
        copy_v4_v4(pt->vert_color, gp_style->stroke_rgba);
        pt->vert_color[3] = 1.0f;
      }

      /* Apply weight directly. */
      if (mmd->flag & GP_TINT_WEIGHT_FACTOR) {
        factor = ((mmd->flag & GP_TINT_INVERT_VGROUP) ? 1.0f - weight : weight);
        weight = 1.0f;
      }

      if (is_gradient) {
        /* Calc world position of point. */
        float pt_loc[3];
        mul_v3_m4v3(pt_loc, matrix, &pt->x);
        float dist = len_v3(pt_loc);

        /* Calc the factor using the distance and get mix color. */
        float mix_factor = clamp_f(dist / mmd->radius, 0.0f, 1.0f);
        BKE_colorband_evaluate(mmd->colorband, mix_factor, coba_res);

        interp_v3_v3v3(pt->vert_color,
                       pt->vert_color,
                       coba_res,
                       clamp_f(factor, 0.0f, 1.0f) * weight * coba_res[3]);
      }
      else {
        interp_v3_v3v3(
            pt->vert_color, pt->vert_color, mmd->rgb, clamp_f(factor * weight, 0.0, 1.0f));
      }
    }
  }
}

/* FIXME: Ideally we be doing this on a copy of the main depsgraph
 * (i.e. one where we don't have to worry about restoring state)
 */
static void bake_modifier(Main * /*bmain*/,
                          Depsgraph *depsgraph,
                          GpencilModifierData *md,
                          Object *ob)
{
  TintGpencilModifierData *mmd = (TintGpencilModifierData *)md;

  if ((mmd->type == GP_TINT_GRADIENT) && (mmd->object == nullptr)) {
    return;
  }

  generic_bake_deform_stroke(depsgraph, md, ob, true, deform_stroke);
}

static void free_data(GpencilModifierData *md)
{
  TintGpencilModifierData *mmd = (TintGpencilModifierData *)md;
  MEM_SAFE_FREE(mmd->colorband);
  if (mmd->curve_intensity) {
    BKE_curvemapping_free(mmd->curve_intensity);
  }
}

static bool is_disabled(GpencilModifierData *md, bool /*use_render_params*/)
{
  TintGpencilModifierData *mmd = (TintGpencilModifierData *)md;
  if (mmd->type == GP_TINT_UNIFORM) {
    return false;
  }

  return !mmd->object;
}

static void update_depsgraph(GpencilModifierData *md,
                             const ModifierUpdateDepsgraphContext *ctx,
                             const int /*mode*/)
{
  TintGpencilModifierData *lmd = (TintGpencilModifierData *)md;
  if (lmd->object != nullptr) {
    DEG_add_object_relation(ctx->node, lmd->object, DEG_OB_COMP_GEOMETRY, "Vertexcolor Modifier");
    DEG_add_object_relation(ctx->node, lmd->object, DEG_OB_COMP_TRANSFORM, "Vertexcolor Modifier");
  }
  DEG_add_object_relation(ctx->node, ctx->object, DEG_OB_COMP_TRANSFORM, "Vertexcolor Modifier");
}

static void foreach_ID_link(GpencilModifierData *md, Object *ob, IDWalkFunc walk, void *user_data)
{
  TintGpencilModifierData *mmd = (TintGpencilModifierData *)md;

  walk(user_data, ob, (ID **)&mmd->material, IDWALK_CB_USER);
  walk(user_data, ob, (ID **)&mmd->object, IDWALK_CB_NOP);
}

static void panel_draw(const bContext * /*C*/, Panel *panel)
{
  uiLayout *col;
  uiLayout *layout = panel->layout;

  PointerRNA *ptr = gpencil_modifier_panel_get_property_pointers(panel, nullptr);

  int tint_type = RNA_enum_get(ptr, "tint_type");

  uiLayoutSetPropSep(layout, true);

  uiItemR(layout, ptr, "vertex_mode", UI_ITEM_NONE, nullptr, ICON_NONE);

  const bool is_weighted = !RNA_boolean_get(ptr, "use_weight_factor");
  uiLayout *row = uiLayoutRow(layout, true);
  uiLayoutSetActive(row, is_weighted);
  uiItemR(row, ptr, "factor", UI_ITEM_NONE, nullptr, ICON_NONE);
  uiLayout *sub = uiLayoutRow(row, true);
  uiLayoutSetActive(sub, true);
  uiItemR(row, ptr, "use_weight_factor", UI_ITEM_NONE, "", ICON_MOD_VERTEX_WEIGHT);

  uiItemR(layout, ptr, "tint_type", UI_ITEM_R_EXPAND, nullptr, ICON_NONE);

  if (tint_type == GP_TINT_UNIFORM) {
    uiItemR(layout, ptr, "color", UI_ITEM_NONE, nullptr, ICON_NONE);
  }
  else {
    col = uiLayoutColumn(layout, false);
    uiLayoutSetPropSep(col, false);
    uiTemplateColorRamp(col, ptr, "colors", true);
    uiItemS(layout);
    uiItemR(layout, ptr, "object", UI_ITEM_NONE, nullptr, ICON_NONE);
    uiItemR(layout, ptr, "radius", UI_ITEM_NONE, nullptr, ICON_NONE);
  }

  gpencil_modifier_panel_end(layout, ptr);
}

static void mask_panel_draw(const bContext * /*C*/, Panel *panel)
{
  gpencil_modifier_masking_panel_draw(panel, true, true);
}

static void panel_register(ARegionType *region_type)
{
  PanelType *panel_type = gpencil_modifier_panel_register(
      region_type, eGpencilModifierType_Tint, panel_draw);
  PanelType *mask_panel_type = gpencil_modifier_subpanel_register(
      region_type, "mask", "Influence", nullptr, mask_panel_draw, panel_type);
  gpencil_modifier_subpanel_register(region_type,
                                     "curve",
                                     "",
                                     gpencil_modifier_curve_header_draw,
                                     gpencil_modifier_curve_panel_draw,
                                     mask_panel_type);
}

GpencilModifierTypeInfo modifierType_Gpencil_Tint = {
    /*name*/ N_("Tint"),
    /*struct_name*/ "TintGpencilModifierData",
    /*struct_size*/ sizeof(TintGpencilModifierData),
    /*type*/ eGpencilModifierTypeType_Gpencil,
    /*flags*/ eGpencilModifierTypeFlag_SupportsEditmode,

    /*copy_data*/ copy_data,

    /*deform_stroke*/ deform_stroke,
    /*generate_strokes*/ nullptr,
    /*bake_modifier*/ bake_modifier,
    /*remap_time*/ nullptr,

    /*init_data*/ init_data,
    /*free_data*/ free_data,
    /*is_disabled*/ is_disabled,
    /*update_depsgraph*/ update_depsgraph,
    /*depends_on_time*/ nullptr,
    /*foreach_ID_link*/ foreach_ID_link,
    /*foreach_tex_link*/ nullptr,
    /*panel_register*/ panel_register,
};
