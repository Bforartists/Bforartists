/* SPDX-FileCopyrightText: 2005 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup modifiers
 */

#include "BLI_index_mask.hh"

#include "BLT_translation.hh"

#include "BLO_read_write.hh"

#include "DNA_defaults.h"
#include "DNA_modifier_types.h"
#include "DNA_screen_types.h"

#include "RNA_access.hh"

#include "BKE_curves.hh"
#include "BKE_geometry_set.hh"
#include "BKE_grease_pencil.hh"
#include "BKE_modifier.hh"

#include "UI_interface_layout.hh"
#include "UI_resources.hh"

#include "GEO_smooth_curves.hh"

#include "MOD_grease_pencil_util.hh"
#include "MOD_ui_common.hh"

#include "RNA_prototypes.hh"

namespace blender {

static void init_data(ModifierData *md)
{
  GreasePencilSmoothModifierData *gpmd = reinterpret_cast<GreasePencilSmoothModifierData *>(md);

  BLI_assert(MEMCMP_STRUCT_AFTER_IS_ZERO(gpmd, modifier));

  MEMCPY_STRUCT_AFTER(gpmd, DNA_struct_default_get(GreasePencilSmoothModifierData), modifier);
  modifier::greasepencil::init_influence_data(&gpmd->influence, false);
}

static void copy_data(const ModifierData *md, ModifierData *target, const int flag)
{
  const GreasePencilSmoothModifierData *gmd =
      reinterpret_cast<const GreasePencilSmoothModifierData *>(md);
  GreasePencilSmoothModifierData *tgmd = reinterpret_cast<GreasePencilSmoothModifierData *>(
      target);

  BKE_modifier_copydata_generic(md, target, flag);
  modifier::greasepencil::copy_influence_data(&gmd->influence, &tgmd->influence, flag);
}

static void free_data(ModifierData *md)
{
  GreasePencilSmoothModifierData *mmd = reinterpret_cast<GreasePencilSmoothModifierData *>(md);

  modifier::greasepencil::free_influence_data(&mmd->influence);
}

static void foreach_ID_link(ModifierData *md, Object *ob, IDWalkFunc walk, void *user_data)
{
  GreasePencilSmoothModifierData *mmd = reinterpret_cast<GreasePencilSmoothModifierData *>(md);

  modifier::greasepencil::foreach_influence_ID_link(&mmd->influence, ob, walk, user_data);
}

static void blend_write(BlendWriter *writer, const ID * /*id_owner*/, const ModifierData *md)
{
  const GreasePencilSmoothModifierData *mmd =
      reinterpret_cast<const GreasePencilSmoothModifierData *>(md);

  BLO_write_struct(writer, GreasePencilSmoothModifierData, mmd);
  modifier::greasepencil::write_influence_data(writer, &mmd->influence);
}

static void blend_read(BlendDataReader *reader, ModifierData *md)
{
  GreasePencilSmoothModifierData *mmd = reinterpret_cast<GreasePencilSmoothModifierData *>(md);
  modifier::greasepencil::read_influence_data(reader, &mmd->influence);
}

static void deform_drawing(const ModifierData &md,
                           const Object &ob,
                           bke::greasepencil::Drawing &drawing)
{
  const auto &mmd = reinterpret_cast<const GreasePencilSmoothModifierData &>(md);

  const int iterations = mmd.step;
  const float influence = mmd.factor;
  const bool keep_shape = (mmd.flag & MOD_GREASE_PENCIL_SMOOTH_KEEP_SHAPE);
  const bool smooth_ends = (mmd.flag & MOD_GREASE_PENCIL_SMOOTH_SMOOTH_ENDS);

  const bool smooth_position = (mmd.flag & MOD_GREASE_PENCIL_SMOOTH_MOD_LOCATION);
  const bool smooth_radius = (mmd.flag & MOD_GREASE_PENCIL_SMOOTH_MOD_THICKNESS);
  const bool smooth_opacity = (mmd.flag & MOD_GREASE_PENCIL_SMOOTH_MOD_STRENGTH);
  const bool smooth_uv = (mmd.flag & MOD_GREASE_PENCIL_SMOOTH_MOD_UV);

  if (iterations <= 0 || influence <= 0.0f) {
    return;
  }

  if (!(smooth_position || smooth_radius || smooth_opacity || smooth_uv)) {
    return;
  }

  modifier::greasepencil::ensure_no_bezier_curves(drawing);
  bke::CurvesGeometry &curves = drawing.strokes_for_write();
  if (curves.is_empty()) {
    return;
  }

  IndexMaskMemory memory;
  const IndexMask strokes = modifier::greasepencil::get_filtered_stroke_mask(
      &ob, curves, mmd.influence, memory);

  if (strokes.is_empty()) {
    return;
  }

  bke::MutableAttributeAccessor attributes = curves.attributes_for_write();
  const OffsetIndices points_by_curve = curves.points_by_curve();
  const VArray<bool> cyclic = curves.cyclic();
  const VArray<bool> point_selection = VArray<bool>::from_single(true, curves.points_num());

  VArray<float> influences;
  const bool use_influence_vertex_group = mmd.influence.vertex_group_name[0] != '\0';
  if (use_influence_vertex_group) {
    const VArray<float> vgroup_weights = modifier::greasepencil::get_influence_vertex_weights(
        curves, mmd.influence);
    Array<float> vgroup_weights_factored(vgroup_weights.size());
    threading::parallel_for(
        vgroup_weights_factored.index_range(), 4096, [&](const IndexRange range) {
          for (const int i : range) {
            vgroup_weights_factored[i] = vgroup_weights[i] * influence;
          }
        });
    influences = VArray<float>::from_container(vgroup_weights_factored);
  }
  else {
    influences = VArray<float>::from_single(influence, curves.points_num());
  }

  if (smooth_position) {
    bke::GSpanAttributeWriter positions = attributes.lookup_for_write_span("position");
    geometry::smooth_curve_attribute(strokes,
                                     points_by_curve,
                                     point_selection,
                                     cyclic,
                                     iterations,
                                     influences,
                                     smooth_ends,
                                     keep_shape,
                                     positions.span);
    positions.finish();
    drawing.tag_positions_changed();
  }
  if (smooth_opacity && drawing.opacities().is_span()) {
    bke::GSpanAttributeWriter opacities = attributes.lookup_for_write_span("opacity");
    geometry::smooth_curve_attribute(strokes,
                                     points_by_curve,
                                     point_selection,
                                     cyclic,
                                     iterations,
                                     influences,
                                     smooth_ends,
                                     false,
                                     opacities.span);
    opacities.finish();
  }
  if (smooth_radius && drawing.radii().is_span()) {
    bke::GSpanAttributeWriter radii = attributes.lookup_for_write_span("radius");
    geometry::smooth_curve_attribute(strokes,
                                     points_by_curve,
                                     point_selection,
                                     cyclic,
                                     iterations,
                                     influences,
                                     smooth_ends,
                                     false,
                                     radii.span);
    radii.finish();
  }
  if (smooth_uv) {
    bke::SpanAttributeWriter<float> rotation = attributes.lookup_for_write_span<float>("rotation");
    if (rotation) {
      geometry::smooth_curve_attribute(strokes,
                                       points_by_curve,
                                       point_selection,
                                       cyclic,
                                       iterations,
                                       influences,
                                       smooth_ends,
                                       false,
                                       rotation.span);
    }
    rotation.finish();
  }
}

static void modify_geometry_set(ModifierData *md,
                                const ModifierEvalContext *ctx,
                                bke::GeometrySet *geometry_set)
{
  GreasePencilSmoothModifierData *mmd = reinterpret_cast<GreasePencilSmoothModifierData *>(md);

  if (!geometry_set->has_grease_pencil()) {
    return;
  }
  GreasePencil &grease_pencil = *geometry_set->get_grease_pencil_for_write();
  const int current_frame = grease_pencil.runtime->eval_frame;

  IndexMaskMemory mask_memory;
  const IndexMask layer_mask = modifier::greasepencil::get_filtered_layer_mask(
      grease_pencil, mmd->influence, mask_memory);
  const Vector<bke::greasepencil::Drawing *> drawings =
      modifier::greasepencil::get_drawings_for_write(grease_pencil, layer_mask, current_frame);

  threading::parallel_for_each(drawings, [&](bke::greasepencil::Drawing *drawing) {
    deform_drawing(*md, *ctx->object, *drawing);
  });
}

static void panel_draw(const bContext *C, Panel *panel)
{
  uiLayout *row, *col;
  uiLayout *layout = panel->layout;

  PointerRNA *ptr = modifier_panel_get_property_pointers(panel, nullptr);

  row = &layout->row(true);
  row->prop(ptr, "use_edit_position", UI_ITEM_R_TOGGLE, IFACE_("Position"), ICON_NONE);
  row->prop(ptr,
            "use_edit_strength",
            UI_ITEM_R_TOGGLE,
            CTX_IFACE_(BLT_I18NCONTEXT_ID_GPENCIL, "Strength"),
            ICON_NONE);
  row->prop(ptr, "use_edit_thickness", UI_ITEM_R_TOGGLE, IFACE_("Thickness"), ICON_NONE);

  row->prop(ptr, "use_edit_uv", UI_ITEM_R_TOGGLE, IFACE_("UV"), ICON_NONE);

  layout->use_property_split_set(true);

  layout->prop(ptr, "factor", UI_ITEM_NONE, std::nullopt, ICON_NONE);
  layout->prop(ptr, "step", UI_ITEM_NONE, IFACE_("Repeat"), ICON_NONE);

  col = &layout->column(false);
  col->active_set(RNA_boolean_get(ptr, "use_edit_position"));
  row = &col->row(true); /* bfa - our layout */
  row->use_property_split_set(false); /* bfa - use_property_split = False */
  row->separator(); /*bfa - indent*/
  row->prop(ptr, "use_keep_shape", UI_ITEM_NONE, std::nullopt, ICON_NONE);
  row->decorator(ptr, "use_keep_shape", 0); /*bfa - decorator*/

  row = &col->row(true); /* bfa - our layout */
  row->use_property_split_set(false); /* bfa - use_property_split = False */
  row->separator(); /*bfa - indent*/
  row->prop(ptr, "use_smooth_ends", UI_ITEM_NONE, std::nullopt, ICON_NONE);
  row->decorator(ptr, "use_smooth_ends", 0); /*bfa - decorator*/

  if (uiLayout *influence_panel = layout->panel_prop(
          C, ptr, "open_influence_panel", IFACE_("Influence")))
  {
    modifier::greasepencil::draw_layer_filter_settings(C, influence_panel, ptr);
    modifier::greasepencil::draw_material_filter_settings(C, influence_panel, ptr);
    modifier::greasepencil::draw_vertex_group_settings(C, influence_panel, ptr);
  }

  modifier_error_message_draw(layout, ptr);
}

static void panel_register(ARegionType *region_type)
{
  modifier_panel_register(region_type, eModifierType_GreasePencilSmooth, panel_draw);
}

}  // namespace blender

ModifierTypeInfo modifierType_GreasePencilSmooth = {
    /*idname*/ "GreasePencilSmoothModifier",
    /*name*/ N_("Smooth"),
    /*struct_name*/ "GreasePencilSmoothModifierData",
    /*struct_size*/ sizeof(GreasePencilSmoothModifierData),
    /*srna*/ &RNA_GreasePencilSmoothModifier,
    /*type*/ ModifierTypeType::OnlyDeform,
    /*flags*/
    eModifierTypeFlag_AcceptsGreasePencil | eModifierTypeFlag_SupportsEditmode |
        eModifierTypeFlag_EnableInEditmode | eModifierTypeFlag_SupportsMapping,
    /*icon*/ ICON_SMOOTHCURVE,

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
};
