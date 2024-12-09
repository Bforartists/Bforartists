/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup modifiers
 */

#include "MEM_guardedalloc.h"

#include "BLI_array_utils.hh"
#include "BLI_math_matrix.hh"

#include "DNA_defaults.h"
#include "DNA_material_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_modifier_types.h"
#include "DNA_scene_types.h"

#include "BKE_armature.hh"
#include "BKE_colorband.hh"
#include "BKE_curves.hh"
#include "BKE_geometry_set.hh"
#include "BKE_grease_pencil.hh"
#include "BKE_lib_query.hh"
#include "BKE_material.h"
#include "BKE_modifier.hh"
#include "BKE_screen.hh"

#include "BLO_read_write.hh"

#include "DEG_depsgraph_query.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "BLT_translation.hh"

#include "WM_types.hh"

#include "RNA_access.hh"
#include "RNA_enum_types.hh"
#include "RNA_prototypes.hh"

#include "MOD_grease_pencil_util.hh"
#include "MOD_modifiertypes.hh"
#include "MOD_ui_common.hh"

namespace blender {

using bke::greasepencil::Drawing;

static void init_data(ModifierData *md)
{
  auto *amd = reinterpret_cast<GreasePencilArmatureModifierData *>(md);

  BLI_assert(MEMCMP_STRUCT_AFTER_IS_ZERO(amd, modifier));

  MEMCPY_STRUCT_AFTER(amd, DNA_struct_default_get(GreasePencilArmatureModifierData), modifier);
  modifier::greasepencil::init_influence_data(&amd->influence, false);
}

static void copy_data(const ModifierData *md, ModifierData *target, const int flag)
{
  const auto *amd = reinterpret_cast<const GreasePencilArmatureModifierData *>(md);
  auto *tamd = reinterpret_cast<GreasePencilArmatureModifierData *>(target);

  modifier::greasepencil::free_influence_data(&tamd->influence);

  BKE_modifier_copydata_generic(md, target, flag);
  modifier::greasepencil::copy_influence_data(&amd->influence, &tamd->influence, flag);
}

static void free_data(ModifierData *md)
{
  auto *amd = reinterpret_cast<GreasePencilArmatureModifierData *>(md);
  modifier::greasepencil::free_influence_data(&amd->influence);
}

static void foreach_ID_link(ModifierData *md, Object *ob, IDWalkFunc walk, void *user_data)
{
  auto *amd = reinterpret_cast<GreasePencilArmatureModifierData *>(md);
  modifier::greasepencil::foreach_influence_ID_link(&amd->influence, ob, walk, user_data);
  walk(user_data, ob, (ID **)&amd->object, IDWALK_CB_NOP);
}

static bool is_disabled(const Scene * /*scene*/, ModifierData *md, bool /*use_render_params*/)
{
  auto *amd = reinterpret_cast<GreasePencilArmatureModifierData *>(md);

  /* The object type check is only needed here in case we have a placeholder
   * object assigned (because the library containing the armature is missing).
   *
   * In other cases it should be impossible to have a type mismatch. */
  return !amd->object || amd->object->type != OB_ARMATURE;
}

static void update_depsgraph(ModifierData *md, const ModifierUpdateDepsgraphContext *ctx)
{
  auto *amd = reinterpret_cast<GreasePencilArmatureModifierData *>(md);
  if (amd->object != nullptr) {
    DEG_add_object_relation(ctx->node, amd->object, DEG_OB_COMP_EVAL_POSE, "Armature Modifier");
    DEG_add_object_relation(ctx->node, amd->object, DEG_OB_COMP_TRANSFORM, "Armature Modifier");
  }
  DEG_add_object_relation(ctx->node, ctx->object, DEG_OB_COMP_TRANSFORM, "Armature Modifier");
}

static ImplicitSharingPtrAndData save_shared_attribute(const bke::GAttributeReader &attribute)
{
  if (attribute.sharing_info && attribute.varray.is_span()) {
    const void *data = attribute.varray.get_internal_span().data();
    attribute.sharing_info->add_user();
    return {ImplicitSharingPtr(attribute.sharing_info), data};
  }
  auto *data = new ImplicitSharedValue<GArray<>>(attribute.varray.type(), attribute.varray.size());
  attribute.varray.materialize(data->data.data());
  return {ImplicitSharingPtr<>(data), data->data.data()};
}

static void modify_curves(ModifierData &md,
                          const ModifierEvalContext &ctx,
                          Drawing &drawing,
                          bke::GreasePencilDrawingEditHints *edit_hints)
{
  auto &amd = reinterpret_cast<GreasePencilArmatureModifierData &>(md);
  modifier::greasepencil::ensure_no_bezier_curves(drawing);
  bke::CurvesGeometry &curves = drawing.strokes_for_write();

  /* The influence flag is where the "invert" flag is stored,
   * but armature functions expect `deformflag` to have the flag set as well.
   * Copy to `deformflag` here to keep old functions happy. */
  const int deformflag = amd.deformflag |
                         (amd.influence.flag & GREASE_PENCIL_INFLUENCE_INVERT_VERTEX_GROUP ?
                              ARM_DEF_INVERT_VGROUP :
                              0);

  IndexMaskMemory mask_memory;
  const IndexMask curves_mask = modifier::greasepencil::get_filtered_stroke_mask(
      ctx.object, curves, amd.influence, mask_memory);

  const OffsetIndices<int> points_by_curve = curves.points_by_curve();
  const MutableSpan<float3> positions = curves.positions_for_write();
  const Span<MDeformVert> dverts = curves.deform_verts();

  if (dverts.is_empty()) {
    return;
  }

  ImplicitSharingPtrAndData old_positions_data = save_shared_attribute(
      curves.attributes().lookup("position", CD_PROP_FLOAT3));
  Span<float3> old_positions = {static_cast<const float3 *>(old_positions_data.data),
                                curves.points_num()};

  std::optional<MutableSpan<float3x3>> deform_mats;
  if (edit_hints) {
    if (!edit_hints->deform_mats.has_value()) {
      edit_hints->deform_mats.emplace(drawing.strokes().points_num(), float3x3::identity());
    }
    deform_mats = edit_hints->deform_mats->as_mutable_span();
  }

  curves_mask.foreach_index(blender::GrainSize(128), [&](const int curve_i) {
    const IndexRange points = points_by_curve[curve_i];

    std::optional<Span<float3>> old_positions_for_curve;
    std::optional<MutableSpan<float3x3>> deform_mats_for_curve;
    if (deform_mats) {
      old_positions_for_curve = old_positions.slice(points);
      deform_mats_for_curve = deform_mats->slice(points);
    }

    BKE_armature_deform_coords_with_curves(*amd.object,
                                           *ctx.object,
                                           &curves.vertex_group_names,
                                           positions.slice(points),
                                           old_positions_for_curve,
                                           deform_mats_for_curve,
                                           dverts.slice(points),
                                           deformflag,
                                           amd.influence.vertex_group_name);
  });

  drawing.tag_positions_changed();
}

static void modify_geometry_set(ModifierData *md,
                                const ModifierEvalContext *ctx,
                                bke::GeometrySet *geometry_set)
{
  using namespace modifier::greasepencil;

  const auto *amd = reinterpret_cast<GreasePencilArmatureModifierData *>(md);

  if (!geometry_set->has_grease_pencil()) {
    return;
  }
  GreasePencil &grease_pencil = *geometry_set->get_grease_pencil_for_write();
  const GreasePencil &grease_pencil_orig = *reinterpret_cast<GreasePencil *>(
      DEG_get_original_id(&grease_pencil.id));
  const int frame = grease_pencil.runtime->eval_frame;

  MutableSpan<bke::GreasePencilDrawingEditHints> edit_hints = {};
  if (geometry_set->has_component<bke::GeometryComponentEditData>()) {
    bke::GeometryComponentEditData &edit_component =
        geometry_set->get_component_for_write<bke::GeometryComponentEditData>();
    if (edit_component.grease_pencil_edit_hints_) {
      if (!edit_component.grease_pencil_edit_hints_->drawing_hints) {
        edit_component.grease_pencil_edit_hints_->drawing_hints.emplace(
            grease_pencil_orig.layers().size());
      }
      edit_hints = *edit_component.grease_pencil_edit_hints_->drawing_hints;
    }
  }

  IndexMaskMemory mask_memory;
  const IndexMask layer_mask = get_filtered_layer_mask(grease_pencil, amd->influence, mask_memory);
  const Vector<LayerDrawingInfo> drawings = get_drawing_infos_by_layer(
      grease_pencil, layer_mask, frame);
  threading::parallel_for_each(drawings, [&](const LayerDrawingInfo &info) {
    if (edit_hints.is_empty()) {
      modify_curves(*md, *ctx, *info.drawing, nullptr);
    }
    else {
      modify_curves(*md, *ctx, *info.drawing, &edit_hints[info.layer_index]);
    }
  });
}

static void panel_draw(const bContext *C, Panel *panel)
{
  uiLayout *layout = panel->layout;

  PointerRNA ob_ptr;
  PointerRNA *ptr = modifier_panel_get_property_pointers(panel, &ob_ptr);

  uiLayoutSetPropSep(layout, true);

  uiItemR(layout, ptr, "object", UI_ITEM_NONE, std::nullopt, ICON_NONE);
  modifier::greasepencil::draw_vertex_group_settings(C, layout, ptr);

  uiLayout *col = uiLayoutColumnWithHeading(layout, true, IFACE_("Bind To"));
  uiItemR(col, ptr, "use_vertex_groups", UI_ITEM_NONE, IFACE_("Vertex Groups"), ICON_NONE);
  uiItemR(col, ptr, "use_bone_envelopes", UI_ITEM_NONE, IFACE_("Bone Envelopes"), ICON_NONE);

  modifier_panel_end(layout, ptr);
}

static void panel_register(ARegionType *region_type)
{
  modifier_panel_register(region_type, eModifierType_GreasePencilArmature, panel_draw);
}

static void blend_write(BlendWriter *writer, const ID * /*id_owner*/, const ModifierData *md)
{
  const auto *amd = reinterpret_cast<const GreasePencilArmatureModifierData *>(md);

  BLO_write_struct(writer, GreasePencilArmatureModifierData, amd);
  modifier::greasepencil::write_influence_data(writer, &amd->influence);
}

static void blend_read(BlendDataReader *reader, ModifierData *md)
{
  auto *amd = reinterpret_cast<GreasePencilArmatureModifierData *>(md);

  modifier::greasepencil::read_influence_data(reader, &amd->influence);
}

}  // namespace blender

ModifierTypeInfo modifierType_GreasePencilArmature = {
    /*idname*/ "GreasePencilArmature",
    /*name*/ N_("Armature"),
    /*struct_name*/ "GreasePencilArmatureModifierData",
    /*struct_size*/ sizeof(GreasePencilArmatureModifierData),
    /*srna*/ &RNA_GreasePencilArmatureModifier,
    /*type*/ ModifierTypeType::OnlyDeform,
    /*flags*/ eModifierTypeFlag_AcceptsGreasePencil | eModifierTypeFlag_SupportsEditmode |
        eModifierTypeFlag_EnableInEditmode | eModifierTypeFlag_SupportsMapping,
    /*icon*/ ICON_MOD_ARMATURE,

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
    /*is_disabled*/ blender::is_disabled,
    /*update_depsgraph*/ blender::update_depsgraph,
    /*depends_on_time*/ nullptr,
    /*depends_on_normals*/ nullptr,
    /*foreach_ID_link*/ blender::foreach_ID_link,
    /*foreach_tex_link*/ nullptr,
    /*free_runtime_data*/ nullptr,
    /*panel_register*/ blender::panel_register,
    /*blend_write*/ blender::blend_write,
    /*blend_read*/ blender::blend_read,
};
