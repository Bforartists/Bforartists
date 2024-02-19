/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup modifiers
 */

#include "DNA_defaults.h"
#include "DNA_modifier_types.h"
#include "DNA_scene_types.h"

#include "BKE_colortools.hh"
#include "BKE_curves.hh"
#include "BKE_geometry_set.hh"
#include "BKE_grease_pencil.hh"
#include "BKE_modifier.hh"
#include "BKE_screen.hh"

#include "BLO_read_write.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "BLT_translation.h"

#include "WM_types.hh"

#include "RNA_access.hh"
#include "RNA_enum_types.hh"
#include "RNA_prototypes.h"

#include "MOD_grease_pencil_util.hh"
#include "MOD_modifiertypes.hh"
#include "MOD_ui_common.hh"

namespace blender {

using bke::greasepencil::Drawing;
using bke::greasepencil::FramesMapKey;
using bke::greasepencil::Layer;

static void init_data(ModifierData *md)
{
  auto *omd = reinterpret_cast<GreasePencilOpacityModifierData *>(md);

  BLI_assert(MEMCMP_STRUCT_AFTER_IS_ZERO(omd, modifier));

  MEMCPY_STRUCT_AFTER(omd, DNA_struct_default_get(GreasePencilOpacityModifierData), modifier);
  modifier::greasepencil::init_influence_data(&omd->influence, true);
}

static void copy_data(const ModifierData *md, ModifierData *target, const int flag)
{
  const auto *omd = reinterpret_cast<const GreasePencilOpacityModifierData *>(md);
  auto *tomd = reinterpret_cast<GreasePencilOpacityModifierData *>(target);

  modifier::greasepencil::free_influence_data(&tomd->influence);

  BKE_modifier_copydata_generic(md, target, flag);
  modifier::greasepencil::copy_influence_data(&omd->influence, &tomd->influence, flag);
}

static void free_data(ModifierData *md)
{
  auto *omd = reinterpret_cast<GreasePencilOpacityModifierData *>(md);
  modifier::greasepencil::free_influence_data(&omd->influence);
}

static void foreach_ID_link(ModifierData *md, Object *ob, IDWalkFunc walk, void *user_data)
{
  auto *omd = reinterpret_cast<GreasePencilOpacityModifierData *>(md);
  modifier::greasepencil::foreach_influence_ID_link(&omd->influence, ob, walk, user_data);
}

static void modify_stroke_color(const GreasePencilOpacityModifierData &omd,
                                bke::CurvesGeometry &curves,
                                const IndexMask &curves_mask)
{
  const bool use_uniform_opacity = (omd.flag & MOD_GREASE_PENCIL_OPACITY_USE_UNIFORM_OPACITY);
  const bool use_weight_as_factor = (omd.flag & MOD_GREASE_PENCIL_OPACITY_USE_WEIGHT_AS_FACTOR);
  const bool invert_vertex_group = (omd.influence.flag &
                                    GREASE_PENCIL_INFLUENCE_INVERT_VERTEX_GROUP);
  const bool use_curve = (omd.influence.flag & GREASE_PENCIL_INFLUENCE_USE_CUSTOM_CURVE);
  const OffsetIndices<int> points_by_curve = curves.points_by_curve();

  bke::MutableAttributeAccessor attributes = curves.attributes_for_write();
  bke::SpanAttributeWriter<float> opacities = attributes.lookup_or_add_for_write_span<float>(
      "opacity", bke::AttrDomain::Point);
  const VArray<float> vgroup_weights = modifier::greasepencil::get_influence_vertex_weights(
      curves, omd.influence);

  curves_mask.foreach_index(GrainSize(512), [&](const int64_t curve_i) {
    const IndexRange points = points_by_curve[curve_i];
    for (const int64_t point_i : points) {
      const float curve_input = points.size() >= 2 ?
                                    (float(point_i - points.first()) / float(points.size() - 1)) :
                                    0.0f;
      const float curve_factor = use_curve ? BKE_curvemapping_evaluateF(
                                                 omd.influence.custom_curve, 0, curve_input) :
                                             1.0f;

      if (use_uniform_opacity) {
        opacities.span[point_i] = std::clamp(omd.color_factor * curve_factor, 0.0f, 1.0f);
      }
      else if (use_weight_as_factor) {
        /* Use vertex group weights as opacity factors. */
        opacities.span[point_i] = std::clamp(
            omd.color_factor * curve_factor * vgroup_weights[point_i], 0.0f, 1.0f);
      }
      else {
        /* Use vertex group weights as influence factors. */
        const float vgroup_weight = vgroup_weights[point_i];
        const float vgroup_influence = invert_vertex_group ? 1.0f - vgroup_weight : vgroup_weight;
        opacities.span[point_i] = std::clamp(
            opacities.span[point_i] + (omd.color_factor * curve_factor - 1.0f) * vgroup_influence,
            0.0f,
            1.0f);
      }
    }
  });

  opacities.finish();
}

static void modify_fill_color(const GreasePencilOpacityModifierData &omd,
                              bke::CurvesGeometry &curves,
                              const IndexMask &curves_mask)
{
  const bool use_vgroup_opacity = (omd.flag & MOD_GREASE_PENCIL_OPACITY_USE_WEIGHT_AS_FACTOR);
  const bool invert_vertex_group = (omd.influence.flag &
                                    GREASE_PENCIL_INFLUENCE_INVERT_VERTEX_GROUP);
  const OffsetIndices<int> points_by_curve = curves.points_by_curve();

  bke::MutableAttributeAccessor attributes = curves.attributes_for_write();
  /* Fill color opacity per stroke. */
  bke::SpanAttributeWriter<float> fill_opacities = attributes.lookup_or_add_for_write_span<float>(
      "fill_opacity", bke::AttrDomain::Curve);
  const VArray<float> vgroup_weights = modifier::greasepencil::get_influence_vertex_weights(
      curves, omd.influence);

  curves_mask.foreach_index(GrainSize(512), [&](int64_t curve_i) {
    if (use_vgroup_opacity) {
      /* Use the first stroke point as vertex weight. */
      const IndexRange points = points_by_curve[curve_i];
      const float stroke_weight = points.is_empty() ? 1.0f : vgroup_weights[points.first()];
      const float stroke_influence = invert_vertex_group ? 1.0f - stroke_weight : stroke_weight;

      fill_opacities.span[curve_i] = std::clamp(stroke_influence, 0.0f, 1.0f);
    }
    else {
      fill_opacities.span[curve_i] = std::clamp(omd.color_factor, 0.0f, 1.0f);
    }
  });

  fill_opacities.finish();
}

static void modify_hardness(const GreasePencilOpacityModifierData &omd,
                            bke::CurvesGeometry &curves,
                            const IndexMask &curves_mask)
{
  bke::MutableAttributeAccessor attributes = curves.attributes_for_write();
  bke::SpanAttributeWriter<float> hardnesses = attributes.lookup_for_write_span<float>("hardness");
  if (!hardnesses) {
    return;
  }

  curves_mask.foreach_index(GrainSize(512), [&](int64_t curve_i) {
    hardnesses.span[curve_i] = std::clamp(
        hardnesses.span[curve_i] * omd.hardness_factor, 0.0f, 1.0f);
  });

  hardnesses.finish();
}

static void modify_curves(ModifierData *md,
                          const ModifierEvalContext *ctx,
                          bke::CurvesGeometry &curves)
{
  const auto *omd = reinterpret_cast<GreasePencilOpacityModifierData *>(md);

  IndexMaskMemory mask_memory;
  const IndexMask curves_mask = modifier::greasepencil::get_filtered_stroke_mask(
      ctx->object, curves, omd->influence, mask_memory);

  switch (omd->color_mode) {
    case MOD_GREASE_PENCIL_COLOR_STROKE:
      modify_stroke_color(*omd, curves, curves_mask);
      break;
    case MOD_GREASE_PENCIL_COLOR_FILL:
      modify_fill_color(*omd, curves, curves_mask);
      break;
    case MOD_GREASE_PENCIL_COLOR_BOTH:
      modify_stroke_color(*omd, curves, curves_mask);
      modify_fill_color(*omd, curves, curves_mask);
      break;
    case MOD_GREASE_PENCIL_COLOR_HARDNESS:
      modify_hardness(*omd, curves, curves_mask);
      break;
  }
}

static void modify_geometry_set(ModifierData *md,
                                const ModifierEvalContext *ctx,
                                bke::GeometrySet *geometry_set)
{
  const auto *omd = reinterpret_cast<GreasePencilOpacityModifierData *>(md);

  GreasePencil *grease_pencil = geometry_set->get_grease_pencil_for_write();
  if (grease_pencil == nullptr) {
    return;
  }

  IndexMaskMemory mask_memory;
  const IndexMask layer_mask = modifier::greasepencil::get_filtered_layer_mask(
      *grease_pencil, omd->influence, mask_memory);
  const int frame = grease_pencil->runtime->eval_frame;
  const Vector<Drawing *> drawings = modifier::greasepencil::get_drawings_for_write(
      *grease_pencil, layer_mask, frame);
  threading::parallel_for_each(
      drawings, [&](Drawing *drawing) { modify_curves(md, ctx, drawing->strokes_for_write()); });
}

static void panel_draw(const bContext *C, Panel *panel)
{
  uiLayout *layout = panel->layout;

  PointerRNA ob_ptr;
  PointerRNA *ptr = modifier_panel_get_property_pointers(panel, &ob_ptr);

  uiLayoutSetPropSep(layout, true);

  const GreasePencilModifierColorMode color_mode = GreasePencilModifierColorMode(
      RNA_enum_get(ptr, "color_mode"));

  uiItemR(layout, ptr, "color_mode", UI_ITEM_NONE, nullptr, ICON_NONE);

  if (color_mode == MOD_GREASE_PENCIL_COLOR_HARDNESS) {
    uiItemR(layout, ptr, "hardness_factor", UI_ITEM_NONE, nullptr, ICON_NONE);
  }
  else {
    const bool use_uniform_opacity = RNA_boolean_get(ptr, "use_uniform_opacity");
    const bool use_weight_as_factor = RNA_boolean_get(ptr, "use_weight_as_factor");

    uiItemR(layout, ptr, "use_uniform_opacity", UI_ITEM_NONE, nullptr, ICON_NONE);
    const char *text = (use_uniform_opacity) ? IFACE_("Opacity") : IFACE_("Opacity Factor");

    uiLayout *row = uiLayoutRow(layout, true);
    uiLayoutSetActive(row, !use_weight_as_factor || use_uniform_opacity);
    uiItemR(row, ptr, "color_factor", UI_ITEM_NONE, text, ICON_NONE);
    if (!use_uniform_opacity) {
      uiLayout *sub = uiLayoutRow(row, true);
      uiLayoutSetActive(sub, true);
      uiItemR(row, ptr, "use_weight_as_factor", UI_ITEM_NONE, "", ICON_MOD_VERTEX_WEIGHT);
    }
  }

  if (uiLayout *influence_panel = uiLayoutPanelProp(
          C, layout, ptr, "open_influence_panel", "Influence"))
  {
    modifier::greasepencil::draw_layer_filter_settings(C, influence_panel, ptr);
    modifier::greasepencil::draw_material_filter_settings(C, influence_panel, ptr);
    modifier::greasepencil::draw_vertex_group_settings(C, influence_panel, ptr);
    modifier::greasepencil::draw_custom_curve_settings(C, influence_panel, ptr);
  }

  modifier_panel_end(layout, ptr);
}

static void panel_register(ARegionType *region_type)
{
  modifier_panel_register(region_type, eModifierType_GreasePencilOpacity, panel_draw);
}

static void blend_write(BlendWriter *writer, const ID * /*id_owner*/, const ModifierData *md)
{
  const auto *omd = reinterpret_cast<const GreasePencilOpacityModifierData *>(md);

  BLO_write_struct(writer, GreasePencilOpacityModifierData, omd);
  modifier::greasepencil::write_influence_data(writer, &omd->influence);
}

static void blend_read(BlendDataReader *reader, ModifierData *md)
{
  auto *omd = reinterpret_cast<GreasePencilOpacityModifierData *>(md);

  modifier::greasepencil::read_influence_data(reader, &omd->influence);
}

}  // namespace blender

ModifierTypeInfo modifierType_GreasePencilOpacity = {
    /*idname*/ "GreasePencilOpacity",
    /*name*/ N_("Opacity"),
    /*struct_name*/ "GreasePencilOpacityModifierData",
    /*struct_size*/ sizeof(GreasePencilOpacityModifierData),
    /*srna*/ &RNA_GreasePencilOpacityModifier,
    /*type*/ ModifierTypeType::NonGeometrical,
    /*flags*/ eModifierTypeFlag_AcceptsGreasePencil | eModifierTypeFlag_SupportsEditmode |
        eModifierTypeFlag_EnableInEditmode | eModifierTypeFlag_SupportsMapping,
    /*icon*/ ICON_MOD_OPACITY,

    /*copy_data*/ blender::copy_data,

    /*deform_verts*/ nullptr,
    /*deform_matrices*/ nullptr,
    /*deform_verts_EM*/ nullptr,
    /*deform_matrices_EM*/ nullptr,
    /*modify_mesh*/ nullptr,
    /*modify_geometry_set*/ blender::modify_geometry_set,

    /*init_data*/ blender::init_data,
    /*required_data_mask*/ nullptr,
    /*free_data*/ blender::free_data,
    /*is_disabled*/ nullptr,
    /*update_depsgraph*/ nullptr,
    /*depends_on_time*/ nullptr,
    /*depends_on_normals*/ nullptr,
    /*foreach_ID_link*/ blender::foreach_ID_link,
    /*foreach_tex_link*/ nullptr,
    /*free_runtime_data*/ nullptr,
    /*panel_register*/ blender::panel_register,
    /*blend_write*/ blender::blend_write,
    /*blend_read*/ blender::blend_read,
    /*foreach_cache*/ nullptr,
};
