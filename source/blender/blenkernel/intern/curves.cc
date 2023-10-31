/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bke
 */

#include <cmath>
#include <cstring>

#include "MEM_guardedalloc.h"

#include "DNA_curves_types.h"
#include "DNA_defaults.h"
#include "DNA_material_types.h"
#include "DNA_object_types.h"

#include "BLI_index_range.hh"
#include "BLI_listbase.h"
#include "BLI_math_base.h"
#include "BLI_math_matrix.hh"
#include "BLI_rand.hh"
#include "BLI_span.hh"
#include "BLI_string.h"
#include "BLI_utildefines.h"
#include "BLI_vector.hh"

#include "BKE_anim_data.h"
#include "BKE_curves.hh"
#include "BKE_customdata.h"
#include "BKE_geometry_fields.hh"
#include "BKE_geometry_set.hh"
#include "BKE_global.h"
#include "BKE_idtype.h"
#include "BKE_lib_id.h"
#include "BKE_lib_query.h"
#include "BKE_lib_remap.h"
#include "BKE_main.h"
#include "BKE_modifier.h"
#include "BKE_object.hh"

#include "BLT_translation.h"

#include "DEG_depsgraph_query.hh"

#include "BLO_read_write.hh"

using blender::float3;
using blender::IndexRange;
using blender::MutableSpan;
using blender::RandomNumberGenerator;
using blender::Span;
using blender::Vector;

static const char *ATTR_POSITION = "position";

static void curves_init_data(ID *id)
{
  Curves *curves = (Curves *)id;
  BLI_assert(MEMCMP_STRUCT_AFTER_IS_ZERO(curves, id));

  MEMCPY_STRUCT_AFTER(curves, DNA_struct_default_get(Curves), id);

  new (&curves->geometry) blender::bke::CurvesGeometry();
}

static void curves_copy_data(Main * /*bmain*/, ID *id_dst, const ID *id_src, const int /*flag*/)
{
  Curves *curves_dst = (Curves *)id_dst;
  const Curves *curves_src = (const Curves *)id_src;
  curves_dst->mat = static_cast<Material **>(MEM_dupallocN(curves_src->mat));

  new (&curves_dst->geometry) blender::bke::CurvesGeometry(curves_src->geometry.wrap());

  if (curves_src->surface_uv_map != nullptr) {
    curves_dst->surface_uv_map = BLI_strdup(curves_src->surface_uv_map);
  }

  curves_dst->batch_cache = nullptr;
}

static void curves_free_data(ID *id)
{
  Curves *curves = (Curves *)id;
  BKE_animdata_free(&curves->id, false);

  curves->geometry.wrap().~CurvesGeometry();

  BKE_curves_batch_cache_free(curves);

  MEM_SAFE_FREE(curves->mat);
  MEM_SAFE_FREE(curves->surface_uv_map);
}

static void curves_foreach_id(ID *id, LibraryForeachIDData *data)
{
  Curves *curves = (Curves *)id;
  for (int i = 0; i < curves->totcol; i++) {
    BKE_LIB_FOREACHID_PROCESS_IDSUPER(data, curves->mat[i], IDWALK_CB_USER);
  }
  BKE_LIB_FOREACHID_PROCESS_IDSUPER(data, curves->surface, IDWALK_CB_NOP);
}

static void curves_blend_write(BlendWriter *writer, ID *id, const void *id_address)
{
  Curves *curves = (Curves *)id;

  blender::bke::CurvesGeometry::BlendWriteData write_data =
      curves->geometry.wrap().blend_write_prepare();

  /* Write LibData */
  BLO_write_id_struct(writer, Curves, id_address, &curves->id);
  BKE_id_blend_write(writer, &curves->id);

  /* Direct data */
  curves->geometry.wrap().blend_write(*writer, curves->id, write_data);

  BLO_write_string(writer, curves->surface_uv_map);

  BLO_write_pointer_array(writer, curves->totcol, curves->mat);
}

static void curves_blend_read_data(BlendDataReader *reader, ID *id)
{
  Curves *curves = (Curves *)id;

  /* Geometry */
  curves->geometry.wrap().blend_read(*reader);

  BLO_read_data_address(reader, &curves->surface_uv_map);

  /* Materials */
  BLO_read_pointer_array(reader, (void **)&curves->mat);
}

IDTypeInfo IDType_ID_CV = {
    /*id_code*/ ID_CV,
    /*id_filter*/ FILTER_ID_CV,
    /*main_listbase_index*/ INDEX_ID_CV,
    /*struct_size*/ sizeof(Curves),
    /*name*/ "Curves",
    /*name_plural*/ N_("hair_curves"),
    /*translation_context*/ BLT_I18NCONTEXT_ID_CURVES,
    /*flags*/ IDTYPE_FLAGS_APPEND_IS_REUSABLE,
    /*asset_type_info*/ nullptr,

    /*init_data*/ curves_init_data,
    /*copy_data*/ curves_copy_data,
    /*free_data*/ curves_free_data,
    /*make_local*/ nullptr,
    /*foreach_id*/ curves_foreach_id,
    /*foreach_cache*/ nullptr,
    /*foreach_path*/ nullptr,
    /*owner_pointer_get*/ nullptr,

    /*blend_write*/ curves_blend_write,
    /*blend_read_data*/ curves_blend_read_data,
    /*blend_read_after_liblink*/ nullptr,

    /*blend_read_undo_preserve*/ nullptr,

    /*lib_override_apply_post*/ nullptr,
};

void *BKE_curves_add(Main *bmain, const char *name)
{
  Curves *curves = static_cast<Curves *>(BKE_id_new(bmain, ID_CV, name));

  return curves;
}

BoundBox BKE_curves_boundbox_get(Object *ob)
{
  using namespace blender;
  BLI_assert(ob->type == OB_CURVES);
  const Curves *curves_id = static_cast<const Curves *>(ob->data);
  const bke::CurvesGeometry &curves = curves_id->geometry.wrap();

  BoundBox bb;
  if (const std::optional<Bounds<float3>> bounds = curves.bounds_min_max()) {
    BKE_boundbox_init_from_minmax(&bb, bounds->min, bounds->max);
  }
  else {
    BKE_boundbox_init_from_minmax(&bb, float3(-1), float3(1));
  }
  return bb;
}

bool BKE_curves_attribute_required(const Curves * /*curves*/, const char *name)
{
  return STREQ(name, ATTR_POSITION);
}

Curves *BKE_curves_copy_for_eval(const Curves *curves_src)
{
  return reinterpret_cast<Curves *>(
      BKE_id_copy_ex(nullptr, &curves_src->id, nullptr, LIB_ID_COPY_LOCALIZE));
}

static void curves_evaluate_modifiers(Depsgraph *depsgraph,
                                      Scene *scene,
                                      Object *object,
                                      blender::bke::GeometrySet &geometry_set)
{
  /* Modifier evaluation modes. */
  const bool use_render = (DEG_get_mode(depsgraph) == DAG_EVAL_RENDER);
  int required_mode = use_render ? eModifierMode_Render : eModifierMode_Realtime;
  if (BKE_object_is_in_editmode(object)) {
    required_mode = (ModifierMode)(int(required_mode) | eModifierMode_Editmode);
  }
  ModifierApplyFlag apply_flag = use_render ? MOD_APPLY_RENDER : MOD_APPLY_USECACHE;
  const ModifierEvalContext mectx = {depsgraph, object, apply_flag};

  BKE_modifiers_clear_errors(object);

  /* Get effective list of modifiers to execute. Some effects like shape keys
   * are added as virtual modifiers before the user created modifiers. */
  VirtualModifierData virtual_modifier_data;
  ModifierData *md = BKE_modifiers_get_virtual_modifierlist(object, &virtual_modifier_data);

  /* Evaluate modifiers. */
  for (; md; md = md->next) {
    const ModifierTypeInfo *mti = BKE_modifier_get_info(static_cast<ModifierType>(md->type));

    if (!BKE_modifier_is_enabled(scene, md, required_mode)) {
      continue;
    }

    blender::bke::ScopedModifierTimer modifier_timer{*md};

    if (mti->modify_geometry_set != nullptr) {
      mti->modify_geometry_set(md, &mectx, &geometry_set);
    }
  }
}

void BKE_curves_data_update(Depsgraph *depsgraph, Scene *scene, Object *object)
{
  using namespace blender;
  using namespace blender::bke;
  /* Free any evaluated data and restore original data. */
  BKE_object_free_derived_caches(object);

  /* Evaluate modifiers. */
  Curves *curves = static_cast<Curves *>(object->data);
  GeometrySet geometry_set = GeometrySet::from_curves(curves, GeometryOwnershipType::ReadOnly);
  if (object->mode == OB_MODE_SCULPT_CURVES) {
    /* Try to propagate deformation data through modifier evaluation, so that sculpt mode can work
     * on evaluated curves. */
    GeometryComponentEditData &edit_component =
        geometry_set.get_component_for_write<GeometryComponentEditData>();
    edit_component.curves_edit_hints_ = std::make_unique<CurvesEditHints>(
        *static_cast<const Curves *>(DEG_get_original_object(object)->data));
  }
  curves_evaluate_modifiers(depsgraph, scene, object, geometry_set);

  /* Assign evaluated object. */
  Curves *curves_eval = const_cast<Curves *>(geometry_set.get_curves());
  if (curves_eval == nullptr) {
    curves_eval = curves_new_nomain(0, 0);
    BKE_object_eval_assign_data(object, &curves_eval->id, true);
  }
  else {
    BKE_object_eval_assign_data(object, &curves_eval->id, false);
  }
  object->runtime.geometry_set_eval = new GeometrySet(std::move(geometry_set));
}

/* Draw Cache */

void (*BKE_curves_batch_cache_dirty_tag_cb)(Curves *curves, int mode) = nullptr;
void (*BKE_curves_batch_cache_free_cb)(Curves *curves) = nullptr;

void BKE_curves_batch_cache_dirty_tag(Curves *curves, int mode)
{
  if (curves->batch_cache) {
    BKE_curves_batch_cache_dirty_tag_cb(curves, mode);
  }
}

void BKE_curves_batch_cache_free(Curves *curves)
{
  if (curves->batch_cache) {
    BKE_curves_batch_cache_free_cb(curves);
  }
}

namespace blender::bke {

Curves *curves_new_nomain(const int points_num, const int curves_num)
{
  BLI_assert(points_num >= 0);
  BLI_assert(curves_num >= 0);
  Curves *curves_id = static_cast<Curves *>(BKE_id_new_nomain(ID_CV, nullptr));
  CurvesGeometry &curves = curves_id->geometry.wrap();
  curves.resize(points_num, curves_num);
  return curves_id;
}

Curves *curves_new_nomain_single(const int points_num, const CurveType type)
{
  Curves *curves_id = curves_new_nomain(points_num, 1);
  CurvesGeometry &curves = curves_id->geometry.wrap();
  curves.offsets_for_write().last() = points_num;
  curves.fill_curve_types(type);
  return curves_id;
}

Curves *curves_new_nomain(CurvesGeometry curves)
{
  Curves *curves_id = static_cast<Curves *>(BKE_id_new_nomain(ID_CV, nullptr));
  curves_id->geometry.wrap() = std::move(curves);
  return curves_id;
}

void curves_copy_parameters(const Curves &src, Curves &dst)
{
  dst.flag = src.flag;
  dst.attributes_active_index = src.attributes_active_index;
  MEM_SAFE_FREE(dst.mat);
  dst.mat = static_cast<Material **>(MEM_malloc_arrayN(src.totcol, sizeof(Material *), __func__));
  dst.totcol = src.totcol;
  MutableSpan(dst.mat, dst.totcol).copy_from(Span(src.mat, src.totcol));
  dst.symmetry = src.symmetry;
  dst.selection_domain = src.selection_domain;
  dst.surface = src.surface;
  MEM_SAFE_FREE(dst.surface_uv_map);
  if (src.surface_uv_map != nullptr) {
    dst.surface_uv_map = BLI_strdup(src.surface_uv_map);
  }
}

CurvesSurfaceTransforms::CurvesSurfaceTransforms(const Object &curves_ob, const Object *surface_ob)
{
  this->curves_to_world = float4x4_view(curves_ob.object_to_world);
  this->world_to_curves = math::invert(this->curves_to_world);

  if (surface_ob != nullptr) {
    this->surface_to_world = float4x4_view(surface_ob->object_to_world);
    this->world_to_surface = math::invert(this->surface_to_world);
    this->surface_to_curves = this->world_to_curves * this->surface_to_world;
    this->curves_to_surface = this->world_to_surface * this->curves_to_world;
    this->surface_to_curves_normal = math::transpose(math::invert(this->surface_to_curves));
  }
}

bool CurvesEditHints::is_valid() const
{
  const int point_num = this->curves_id_orig.geometry.point_num;
  if (this->positions.has_value()) {
    if (this->positions->size() != point_num) {
      return false;
    }
  }
  if (this->deform_mats.has_value()) {
    if (this->deform_mats->size() != point_num) {
      return false;
    }
  }
  return true;
}

void curves_normals_point_domain_calc(const CurvesGeometry &curves, MutableSpan<float3> normals)
{
  const bke::CurvesFieldContext context(curves, ATTR_DOMAIN_POINT);
  fn::FieldEvaluator evaluator(context, curves.points_num());
  fn::Field<float3> field(std::make_shared<bke::NormalFieldInput>());
  evaluator.add_with_destination(std::move(field), normals);
  evaluator.evaluate();
}

}  // namespace blender::bke
