/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edmesh
 */

#include "BLI_generic_pointer.hh"

#include "BKE_attribute.h"
#include "BKE_attribute_math.hh"
#include "BKE_context.h"
#include "BKE_report.h"
#include "BKE_type_conversions.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "ED_curves.hh"
#include "ED_geometry.hh"
#include "ED_object.hh"
#include "ED_screen.hh"
#include "ED_transform.hh"
#include "ED_view3d.hh"

#include "RNA_access.hh"

#include "BLT_translation.h"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "DNA_object_types.h"

#include "DEG_depsgraph.hh"
#include "DEG_depsgraph_query.hh"

/* -------------------------------------------------------------------- */
/** \name Delete Operator
 * \{ */

namespace blender::ed::curves {

static bool active_attribute_poll(bContext *C)
{
  if (!editable_curves_in_edit_mode_poll(C)) {
    return false;
  }
  Object *object = CTX_data_active_object(C);
  Curves &curves_id = *static_cast<Curves *>(object->data);
  const CustomDataLayer *layer = BKE_id_attributes_active_get(&const_cast<ID &>(curves_id.id));
  if (!layer) {
    CTX_wm_operator_poll_msg_set(C, "No active attribute");
    return false;
  }
  if (layer->type == CD_PROP_STRING) {
    CTX_wm_operator_poll_msg_set(C, "Active string attribute not supported");
    return false;
  }
  return true;
}

static IndexMask retrieve_selected_elements(const Curves &curves_id,
                                            const eAttrDomain domain,
                                            IndexMaskMemory &memory)
{
  switch (domain) {
    case ATTR_DOMAIN_POINT:
      return retrieve_selected_points(curves_id, memory);
    case ATTR_DOMAIN_CURVE:
      return retrieve_selected_curves(curves_id, memory);
    default:
      BLI_assert_unreachable();
      return {};
  }
}

static void validate_value(const bke::AttributeAccessor attributes,
                           const StringRef name,
                           const CPPType &type,
                           void *buffer)
{
  const bke::AttributeValidator validator = attributes.lookup_validator(name);
  if (!validator) {
    return;
  }
  BUFFER_FOR_CPP_TYPE_VALUE(type, validated_buffer);
  BLI_SCOPED_DEFER([&]() { type.destruct(validated_buffer); });

  const IndexMask single_mask(1);
  mf::ParamsBuilder params(*validator.function, &single_mask);
  params.add_readonly_single_input(GPointer(type, buffer));
  params.add_uninitialized_single_output({type, validated_buffer, 1});
  mf::ContextBuilder context;
  validator.function->call(single_mask, params, context);

  type.copy_assign(validated_buffer, buffer);
}

static int set_attribute_exec(bContext *C, wmOperator *op)
{
  Object *active_object = CTX_data_active_object(C);
  Curves &active_curves_id = *static_cast<Curves *>(active_object->data);

  CustomDataLayer *active_attribute = BKE_id_attributes_active_get(&active_curves_id.id);
  const eCustomDataType active_type = eCustomDataType(active_attribute->type);
  const CPPType &type = *bke::custom_data_type_to_cpp_type(active_type);

  BUFFER_FOR_CPP_TYPE_VALUE(type, buffer);
  BLI_SCOPED_DEFER([&]() { type.destruct(buffer); });
  const GPointer value = geometry::rna_property_for_attribute_type_retrieve_value(
      *op->ptr, active_type, buffer);

  const bke::DataTypeConversions &conversions = bke::get_implicit_type_conversions();

  for (Curves *curves_id : get_unique_editable_curves(*C)) {
    bke::CurvesGeometry &curves = curves_id->geometry.wrap();
    CustomDataLayer *layer = BKE_id_attributes_active_get(&curves_id->id);
    if (!layer) {
      continue;
    }
    bke::MutableAttributeAccessor attributes = curves.attributes_for_write();
    bke::GSpanAttributeWriter attribute = attributes.lookup_for_write_span(layer->name);

    /* Use implicit conversions to try to handle the case where the active attribute has a
     * different type on multiple objects. */
    const CPPType &dst_type = attribute.span.type();
    if (&type != &dst_type && !conversions.is_convertible(type, dst_type)) {
      continue;
    }
    BUFFER_FOR_CPP_TYPE_VALUE(dst_type, dst_buffer);
    BLI_SCOPED_DEFER([&]() { dst_type.destruct(dst_buffer); });
    conversions.convert_to_uninitialized(type, dst_type, value.get(), dst_buffer);

    validate_value(attributes, layer->name, dst_type, dst_buffer);
    const GPointer dst_value(type, dst_buffer);

    IndexMaskMemory memory;
    const IndexMask selection = retrieve_selected_elements(*curves_id, attribute.domain, memory);
    if (selection.is_empty()) {
      attribute.finish();
      continue;
    }
    dst_type.fill_assign_indices(dst_value.get(), attribute.span.data(), selection);
    attribute.finish();

    DEG_id_tag_update(&curves_id->id, ID_RECALC_GEOMETRY);
    WM_event_add_notifier(C, NC_GEOM | ND_DATA, curves_id);
  }

  return OPERATOR_FINISHED;
}

static int set_attribute_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
  Object *active_object = CTX_data_active_object(C);
  Curves &active_curves_id = *static_cast<Curves *>(active_object->data);

  CustomDataLayer *active_attribute = BKE_id_attributes_active_get(&active_curves_id.id);
  const bke::CurvesGeometry &curves = active_curves_id.geometry.wrap();
  const bke::AttributeAccessor attributes = curves.attributes();
  const bke::GAttributeReader attribute = attributes.lookup(active_attribute->name);
  const eAttrDomain domain = attribute.domain;

  IndexMaskMemory memory;
  const IndexMask selection = retrieve_selected_elements(active_curves_id, domain, memory);

  const CPPType &type = attribute.varray.type();

  PropertyRNA *prop = geometry::rna_property_for_type(*op->ptr,
                                                      bke::cpp_type_to_custom_data_type(type));
  if (RNA_property_is_set(op->ptr, prop)) {
    return WM_operator_props_popup(C, op, event);
  }

  BUFFER_FOR_CPP_TYPE_VALUE(type, buffer);
  BLI_SCOPED_DEFER([&]() { type.destruct(buffer); });

  bke::attribute_math::convert_to_static_type(type, [&](auto dummy) {
    using T = decltype(dummy);
    const VArray<T> values_typed = attribute.varray.typed<T>();
    bke::attribute_math::DefaultMixer<T> mixer{MutableSpan(static_cast<T *>(buffer), 1)};
    selection.foreach_index([&](const int i) { mixer.mix_in(0, values_typed[i]); });
    mixer.finalize();
  });

  geometry::rna_property_for_attribute_type_set_value(*op->ptr, *prop, GPointer(type, buffer));

  return WM_operator_props_popup(C, op, event);
}

static void set_attribute_ui(bContext *C, wmOperator *op)
{
  uiLayout *layout = uiLayoutColumn(op->layout, true);
  uiLayoutSetPropSep(layout, true);
  uiLayoutSetPropDecorate(layout, false);

  Object *object = CTX_data_active_object(C);
  Curves &curves_id = *static_cast<Curves *>(object->data);

  CustomDataLayer *active_attribute = BKE_id_attributes_active_get(&curves_id.id);
  const eCustomDataType active_type = eCustomDataType(active_attribute->type);
  const StringRefNull prop_name = geometry::rna_property_name_for_type(active_type);
  const char *name = active_attribute->name;
  uiItemR(layout, op->ptr, prop_name.c_str(), UI_ITEM_NONE, name, ICON_NONE);
}

void CURVES_OT_attribute_set(wmOperatorType *ot)
{
  using namespace blender::ed;
  using namespace blender::ed::curves;
  ot->name = "Set Attribute";
  ot->description = "Set values of the active attribute for selected elements";
  ot->idname = "CURVES_OT_attribute_set";

  ot->exec = set_attribute_exec;
  ot->invoke = set_attribute_invoke;
  ot->poll = active_attribute_poll;
  ot->ui = set_attribute_ui;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  geometry::register_rna_properties_for_attribute_types(*ot->srna);
}

}  // namespace blender::ed::curves

/** \} */
