/* SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bke
 */

#include <mutex>
#include <utility>

#include "MEM_guardedalloc.h"

#include "BLI_bounds.hh"
#include "BLI_index_mask_ops.hh"
#include "BLI_length_parameterize.hh"
#include "BLI_math_rotation.hh"

#include "DNA_curves_types.h"

#include "BKE_attribute_math.hh"
#include "BKE_curves.hh"

namespace blender::bke {

static const std::string ATTR_POSITION = "position";
static const std::string ATTR_RADIUS = "radius";
static const std::string ATTR_TILT = "tilt";
static const std::string ATTR_CURVE_TYPE = "curve_type";
static const std::string ATTR_CYCLIC = "cyclic";
static const std::string ATTR_RESOLUTION = "resolution";
static const std::string ATTR_NORMAL_MODE = "normal_mode";
static const std::string ATTR_HANDLE_TYPE_LEFT = "handle_type_left";
static const std::string ATTR_HANDLE_TYPE_RIGHT = "handle_type_right";
static const std::string ATTR_HANDLE_POSITION_LEFT = "handle_left";
static const std::string ATTR_HANDLE_POSITION_RIGHT = "handle_right";
static const std::string ATTR_NURBS_ORDER = "nurbs_order";
static const std::string ATTR_NURBS_WEIGHT = "nurbs_weight";
static const std::string ATTR_NURBS_KNOTS_MODE = "knots_mode";
static const std::string ATTR_SURFACE_TRIANGLE_INDEX = "surface_triangle_index";
static const std::string ATTR_SURFACE_TRIANGLE_COORDINATE = "surface_triangle_coordinate";

/* -------------------------------------------------------------------- */
/** \name Constructors/Destructor
 * \{ */

CurvesGeometry::CurvesGeometry() : CurvesGeometry(0, 0)
{
}

CurvesGeometry::CurvesGeometry(const int point_size, const int curve_size)
{
  this->point_size = point_size;
  this->curve_size = curve_size;
  CustomData_reset(&this->point_data);
  CustomData_reset(&this->curve_data);

  CustomData_add_layer_named(&this->point_data,
                             CD_PROP_FLOAT3,
                             CD_DEFAULT,
                             nullptr,
                             this->point_size,
                             ATTR_POSITION.c_str());

  this->curve_offsets = (int *)MEM_calloc_arrayN(this->curve_size + 1, sizeof(int), __func__);

  this->update_customdata_pointers();

  this->runtime = MEM_new<CurvesGeometryRuntime>(__func__);
  /* Fill the type counts with the default so they're in a valid state. */
  this->runtime->type_counts[CURVE_TYPE_CATMULL_ROM] = curve_size;
}

/**
 * \note Expects `dst` to be initialized, since the original attributes must be freed.
 */
static void copy_curves_geometry(CurvesGeometry &dst, const CurvesGeometry &src)
{
  CustomData_free(&dst.point_data, dst.point_size);
  CustomData_free(&dst.curve_data, dst.curve_size);
  dst.point_size = src.point_size;
  dst.curve_size = src.curve_size;
  CustomData_copy(&src.point_data, &dst.point_data, CD_MASK_ALL, CD_DUPLICATE, dst.point_size);
  CustomData_copy(&src.curve_data, &dst.curve_data, CD_MASK_ALL, CD_DUPLICATE, dst.curve_size);

  MEM_SAFE_FREE(dst.curve_offsets);
  dst.curve_offsets = (int *)MEM_calloc_arrayN(dst.point_size + 1, sizeof(int), __func__);
  dst.offsets_for_write().copy_from(src.offsets());

  dst.tag_topology_changed();

  /* Though type counts are a cache, they must be copied because they are calculated eagerly. */
  dst.runtime->type_counts = src.runtime->type_counts;

  dst.update_customdata_pointers();
}

CurvesGeometry::CurvesGeometry(const CurvesGeometry &other)
    : CurvesGeometry(other.point_size, other.curve_size)
{
  copy_curves_geometry(*this, other);
}

CurvesGeometry &CurvesGeometry::operator=(const CurvesGeometry &other)
{
  if (this != &other) {
    copy_curves_geometry(*this, other);
  }
  return *this;
}

/* The source should be empty, but in a valid state so that using it further will work. */
static void move_curves_geometry(CurvesGeometry &dst, CurvesGeometry &src)
{
  dst.point_size = src.point_size;
  std::swap(dst.point_data, src.point_data);
  CustomData_free(&src.point_data, src.point_size);
  src.point_size = 0;

  dst.curve_size = src.curve_size;
  std::swap(dst.curve_data, src.curve_data);
  CustomData_free(&src.curve_data, src.curve_size);
  src.curve_size = 0;

  std::swap(dst.curve_offsets, src.curve_offsets);
  MEM_SAFE_FREE(src.curve_offsets);

  std::swap(dst.runtime, src.runtime);

  src.update_customdata_pointers();
  dst.update_customdata_pointers();
}

CurvesGeometry::CurvesGeometry(CurvesGeometry &&other)
    : CurvesGeometry(other.point_size, other.curve_size)
{
  move_curves_geometry(*this, other);
}

CurvesGeometry &CurvesGeometry::operator=(CurvesGeometry &&other)
{
  if (this != &other) {
    move_curves_geometry(*this, other);
  }
  return *this;
}

CurvesGeometry::~CurvesGeometry()
{
  CustomData_free(&this->point_data, this->point_size);
  CustomData_free(&this->curve_data, this->curve_size);
  MEM_SAFE_FREE(this->curve_offsets);
  MEM_delete(this->runtime);
  this->runtime = nullptr;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Accessors
 * \{ */

static int domain_size(const CurvesGeometry &curves, const AttributeDomain domain)
{
  return domain == ATTR_DOMAIN_POINT ? curves.points_num() : curves.curves_num();
}

static CustomData &domain_custom_data(CurvesGeometry &curves, const AttributeDomain domain)
{
  return domain == ATTR_DOMAIN_POINT ? curves.point_data : curves.curve_data;
}

static const CustomData &domain_custom_data(const CurvesGeometry &curves,
                                            const AttributeDomain domain)
{
  return domain == ATTR_DOMAIN_POINT ? curves.point_data : curves.curve_data;
}

template<typename T>
static VArray<T> get_varray_attribute(const CurvesGeometry &curves,
                                      const AttributeDomain domain,
                                      const StringRefNull name,
                                      const T default_value)
{
  const int size = domain_size(curves, domain);
  const CustomDataType type = cpp_type_to_custom_data_type(CPPType::get<T>());
  const CustomData &custom_data = domain_custom_data(curves, domain);

  const T *data = (const T *)CustomData_get_layer_named(&custom_data, type, name.c_str());
  if (data != nullptr) {
    return VArray<T>::ForSpan(Span<T>(data, size));
  }
  return VArray<T>::ForSingle(default_value, size);
}

template<typename T>
static Span<T> get_span_attribute(const CurvesGeometry &curves,
                                  const AttributeDomain domain,
                                  const StringRefNull name)
{
  const int size = domain_size(curves, domain);
  const CustomData &custom_data = domain_custom_data(curves, domain);
  const CustomDataType type = cpp_type_to_custom_data_type(CPPType::get<T>());

  T *data = (T *)CustomData_get_layer_named(&custom_data, type, name.c_str());
  if (data == nullptr) {
    return {};
  }
  return {data, size};
}

template<typename T>
static MutableSpan<T> get_mutable_attribute(CurvesGeometry &curves,
                                            const AttributeDomain domain,
                                            const StringRefNull name,
                                            const T default_value = T())
{
  const int size = domain_size(curves, domain);
  const CustomDataType type = cpp_type_to_custom_data_type(CPPType::get<T>());
  CustomData &custom_data = domain_custom_data(curves, domain);

  T *data = (T *)CustomData_duplicate_referenced_layer_named(
      &custom_data, type, name.c_str(), size);
  if (data != nullptr) {
    return {data, size};
  }
  data = (T *)CustomData_add_layer_named(
      &custom_data, type, CD_CALLOC, nullptr, size, name.c_str());
  MutableSpan<T> span = {data, size};
  if (size > 0 && span.first() != default_value) {
    span.fill(default_value);
  }
  return span;
}

VArray<int8_t> CurvesGeometry::curve_types() const
{
  return get_varray_attribute<int8_t>(
      *this, ATTR_DOMAIN_CURVE, ATTR_CURVE_TYPE, CURVE_TYPE_CATMULL_ROM);
}

MutableSpan<int8_t> CurvesGeometry::curve_types_for_write()
{
  return get_mutable_attribute<int8_t>(*this, ATTR_DOMAIN_CURVE, ATTR_CURVE_TYPE);
}

void CurvesGeometry::fill_curve_types(const CurveType type)
{
  this->curve_types_for_write().fill(type);
  this->runtime->type_counts.fill(0);
  this->runtime->type_counts[type] = this->curves_num();
  this->tag_topology_changed();
}

void CurvesGeometry::fill_curve_types(const IndexMask selection, const CurveType type)
{
  if (selection.size() == this->curves_num()) {
    this->fill_curve_types(type);
    return;
  }
  /* A potential performance optimization is only counting the changed indices. */
  this->curve_types_for_write().fill_indices(selection, type);
  this->update_curve_types();
  this->tag_topology_changed();
}

std::array<int, CURVE_TYPES_NUM> calculate_type_counts(const VArray<int8_t> &types)
{
  using CountsType = std::array<int, CURVE_TYPES_NUM>;
  CountsType counts;
  counts.fill(0);

  if (types.is_single()) {
    counts[types.get_internal_single()] = types.size();
    return counts;
  }

  Span<int8_t> types_span = types.get_internal_span();
  return threading::parallel_reduce(
      types.index_range(),
      2048,
      counts,
      [&](const IndexRange curves_range, const CountsType &init) {
        CountsType result = init;
        for (const int curve_index : curves_range) {
          result[types_span[curve_index]]++;
        }
        return result;
      },
      [](const CountsType &a, const CountsType &b) {
        CountsType result = a;
        for (const int i : IndexRange(CURVE_TYPES_NUM)) {
          result[i] += b[i];
        }
        return result;
      });
}

void CurvesGeometry::update_curve_types()
{
  this->runtime->type_counts = calculate_type_counts(this->curve_types());
}

Span<float3> CurvesGeometry::positions() const
{
  return {(const float3 *)this->position, this->point_size};
}
MutableSpan<float3> CurvesGeometry::positions_for_write()
{
  this->position = (float(*)[3])CustomData_duplicate_referenced_layer_named(
      &this->point_data, CD_PROP_FLOAT3, ATTR_POSITION.c_str(), this->point_size);
  return {(float3 *)this->position, this->point_size};
}

Span<int> CurvesGeometry::offsets() const
{
  return {this->curve_offsets, this->curve_size + 1};
}
MutableSpan<int> CurvesGeometry::offsets_for_write()
{
  return {this->curve_offsets, this->curve_size + 1};
}

VArray<bool> CurvesGeometry::cyclic() const
{
  return get_varray_attribute<bool>(*this, ATTR_DOMAIN_CURVE, ATTR_CYCLIC, false);
}
MutableSpan<bool> CurvesGeometry::cyclic_for_write()
{
  return get_mutable_attribute<bool>(*this, ATTR_DOMAIN_CURVE, ATTR_CYCLIC, false);
}

VArray<int> CurvesGeometry::resolution() const
{
  return get_varray_attribute<int>(*this, ATTR_DOMAIN_CURVE, ATTR_RESOLUTION, 12);
}
MutableSpan<int> CurvesGeometry::resolution_for_write()
{
  return get_mutable_attribute<int>(*this, ATTR_DOMAIN_CURVE, ATTR_RESOLUTION, 12);
}

VArray<int8_t> CurvesGeometry::normal_mode() const
{
  return get_varray_attribute<int8_t>(*this, ATTR_DOMAIN_CURVE, ATTR_NORMAL_MODE, 0);
}
MutableSpan<int8_t> CurvesGeometry::normal_mode_for_write()
{
  return get_mutable_attribute<int8_t>(*this, ATTR_DOMAIN_CURVE, ATTR_NORMAL_MODE);
}

VArray<float> CurvesGeometry::tilt() const
{
  return get_varray_attribute<float>(*this, ATTR_DOMAIN_POINT, ATTR_TILT, 0.0f);
}
MutableSpan<float> CurvesGeometry::tilt_for_write()
{
  return get_mutable_attribute<float>(*this, ATTR_DOMAIN_POINT, ATTR_TILT);
}

VArray<int8_t> CurvesGeometry::handle_types_left() const
{
  return get_varray_attribute<int8_t>(*this, ATTR_DOMAIN_POINT, ATTR_HANDLE_TYPE_LEFT, 0);
}
MutableSpan<int8_t> CurvesGeometry::handle_types_left_for_write()
{
  return get_mutable_attribute<int8_t>(*this, ATTR_DOMAIN_POINT, ATTR_HANDLE_TYPE_LEFT, 0);
}

VArray<int8_t> CurvesGeometry::handle_types_right() const
{
  return get_varray_attribute<int8_t>(*this, ATTR_DOMAIN_POINT, ATTR_HANDLE_TYPE_RIGHT, 0);
}
MutableSpan<int8_t> CurvesGeometry::handle_types_right_for_write()
{
  return get_mutable_attribute<int8_t>(*this, ATTR_DOMAIN_POINT, ATTR_HANDLE_TYPE_RIGHT, 0);
}

Span<float3> CurvesGeometry::handle_positions_left() const
{
  return get_span_attribute<float3>(*this, ATTR_DOMAIN_POINT, ATTR_HANDLE_POSITION_LEFT);
}
MutableSpan<float3> CurvesGeometry::handle_positions_left_for_write()
{
  return get_mutable_attribute<float3>(*this, ATTR_DOMAIN_POINT, ATTR_HANDLE_POSITION_LEFT);
}

Span<float3> CurvesGeometry::handle_positions_right() const
{
  return get_span_attribute<float3>(*this, ATTR_DOMAIN_POINT, ATTR_HANDLE_POSITION_RIGHT);
}
MutableSpan<float3> CurvesGeometry::handle_positions_right_for_write()
{
  return get_mutable_attribute<float3>(*this, ATTR_DOMAIN_POINT, ATTR_HANDLE_POSITION_RIGHT);
}

VArray<int8_t> CurvesGeometry::nurbs_orders() const
{
  return get_varray_attribute<int8_t>(*this, ATTR_DOMAIN_CURVE, ATTR_NURBS_ORDER, 4);
}
MutableSpan<int8_t> CurvesGeometry::nurbs_orders_for_write()
{
  return get_mutable_attribute<int8_t>(*this, ATTR_DOMAIN_CURVE, ATTR_NURBS_ORDER, 4);
}

Span<float> CurvesGeometry::nurbs_weights() const
{
  return get_span_attribute<float>(*this, ATTR_DOMAIN_POINT, ATTR_NURBS_WEIGHT);
}
MutableSpan<float> CurvesGeometry::nurbs_weights_for_write()
{
  return get_mutable_attribute<float>(*this, ATTR_DOMAIN_POINT, ATTR_NURBS_WEIGHT);
}

VArray<int8_t> CurvesGeometry::nurbs_knots_modes() const
{
  return get_varray_attribute<int8_t>(*this, ATTR_DOMAIN_CURVE, ATTR_NURBS_KNOTS_MODE, 0);
}
MutableSpan<int8_t> CurvesGeometry::nurbs_knots_modes_for_write()
{
  return get_mutable_attribute<int8_t>(*this, ATTR_DOMAIN_CURVE, ATTR_NURBS_KNOTS_MODE, 0);
}

VArray<int> CurvesGeometry::surface_triangle_indices() const
{
  return get_varray_attribute<int>(*this, ATTR_DOMAIN_CURVE, ATTR_SURFACE_TRIANGLE_INDEX, -1);
}

MutableSpan<int> CurvesGeometry::surface_triangle_indices_for_write()
{
  return get_mutable_attribute<int>(*this, ATTR_DOMAIN_CURVE, ATTR_SURFACE_TRIANGLE_INDEX, -1);
}

Span<float2> CurvesGeometry::surface_triangle_coords() const
{
  return get_span_attribute<float2>(*this, ATTR_DOMAIN_CURVE, ATTR_SURFACE_TRIANGLE_COORDINATE);
}

MutableSpan<float2> CurvesGeometry::surface_triangle_coords_for_write()
{
  return get_mutable_attribute<float2>(*this, ATTR_DOMAIN_CURVE, ATTR_SURFACE_TRIANGLE_COORDINATE);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Evaluation
 * \{ */

template<typename SizeFn> void build_offsets(MutableSpan<int> offsets, const SizeFn &size_fn)
{
  int offset = 0;
  for (const int i : offsets.drop_back(1).index_range()) {
    offsets[i] = offset;
    offset += size_fn(i);
  }
  offsets.last() = offset;
}

static void calculate_evaluated_offsets(const CurvesGeometry &curves,
                                        MutableSpan<int> offsets,
                                        MutableSpan<int> bezier_evaluated_offsets)
{
  VArray<int8_t> types = curves.curve_types();
  VArray<int> resolution = curves.resolution();
  VArray<bool> cyclic = curves.cyclic();

  VArray_Span<int8_t> handle_types_left{curves.handle_types_left()};
  VArray_Span<int8_t> handle_types_right{curves.handle_types_right()};

  VArray<int8_t> nurbs_orders = curves.nurbs_orders();
  VArray<int8_t> nurbs_knots_modes = curves.nurbs_knots_modes();

  build_offsets(offsets, [&](const int curve_index) -> int {
    const IndexRange points = curves.points_for_curve(curve_index);
    switch (types[curve_index]) {
      case CURVE_TYPE_CATMULL_ROM:
        return curves::catmull_rom::calculate_evaluated_size(
            points.size(), cyclic[curve_index], resolution[curve_index]);
      case CURVE_TYPE_POLY:
        return points.size();
      case CURVE_TYPE_BEZIER:
        curves::bezier::calculate_evaluated_offsets(handle_types_left.slice(points),
                                                    handle_types_right.slice(points),
                                                    cyclic[curve_index],
                                                    resolution[curve_index],
                                                    bezier_evaluated_offsets.slice(points));
        return bezier_evaluated_offsets[points.last()];
      case CURVE_TYPE_NURBS:
        return curves::nurbs::calculate_evaluated_size(points.size(),
                                                       nurbs_orders[curve_index],
                                                       cyclic[curve_index],
                                                       resolution[curve_index],
                                                       KnotsMode(nurbs_knots_modes[curve_index]));
    }
    BLI_assert_unreachable();
    return 0;
  });
}

void CurvesGeometry::ensure_evaluated_offsets() const
{
  if (!this->runtime->offsets_cache_dirty) {
    return;
  }

  /* A double checked lock. */
  std::scoped_lock lock{this->runtime->offsets_cache_mutex};
  if (!this->runtime->offsets_cache_dirty) {
    return;
  }

  threading::isolate_task([&]() {
    this->runtime->evaluated_offsets_cache.resize(this->curves_num() + 1);

    if (this->has_curve_with_type(CURVE_TYPE_BEZIER)) {
      this->runtime->bezier_evaluated_offsets.resize(this->points_num());
    }
    else {
      this->runtime->bezier_evaluated_offsets.clear_and_make_inline();
    }

    calculate_evaluated_offsets(
        *this, this->runtime->evaluated_offsets_cache, this->runtime->bezier_evaluated_offsets);
  });

  this->runtime->offsets_cache_dirty = false;
}

Span<int> CurvesGeometry::evaluated_offsets() const
{
  this->ensure_evaluated_offsets();
  return this->runtime->evaluated_offsets_cache;
}

IndexMask CurvesGeometry::indices_for_curve_type(const CurveType type,
                                                 Vector<int64_t> &r_indices) const
{
  return this->indices_for_curve_type(type, this->curves_range(), r_indices);
}

IndexMask CurvesGeometry::indices_for_curve_type(const CurveType type,
                                                 const IndexMask selection,
                                                 Vector<int64_t> &r_indices) const
{
  if (this->curve_type_counts()[type] == this->curves_num()) {
    return selection;
  }
  const VArray<int8_t> types = this->curve_types();
  if (types.is_single()) {
    return types.get_internal_single() == type ? IndexMask(this->curves_num()) : IndexMask(0);
  }
  Span<int8_t> types_span = types.get_internal_span();
  return index_mask_ops::find_indices_based_on_predicate(
      selection, 1024, r_indices, [&](const int index) { return types_span[index] == type; });
}

void CurvesGeometry::ensure_nurbs_basis_cache() const
{
  if (!this->runtime->nurbs_basis_cache_dirty) {
    return;
  }

  /* A double checked lock. */
  std::scoped_lock lock{this->runtime->nurbs_basis_cache_mutex};
  if (!this->runtime->nurbs_basis_cache_dirty) {
    return;
  }

  threading::isolate_task([&]() {
    Vector<int64_t> nurbs_indices;
    const IndexMask nurbs_mask = this->indices_for_curve_type(CURVE_TYPE_NURBS, nurbs_indices);
    if (nurbs_mask.is_empty()) {
      return;
    }

    this->runtime->nurbs_basis_cache.resize(this->curves_num());
    MutableSpan<curves::nurbs::BasisCache> basis_caches(this->runtime->nurbs_basis_cache);

    VArray<bool> cyclic = this->cyclic();
    VArray<int8_t> orders = this->nurbs_orders();
    VArray<int8_t> knots_modes = this->nurbs_knots_modes();

    threading::parallel_for(nurbs_mask.index_range(), 64, [&](const IndexRange range) {
      for (const int curve_index : nurbs_mask.slice(range)) {
        const IndexRange points = this->points_for_curve(curve_index);
        const IndexRange evaluated_points = this->evaluated_points_for_curve(curve_index);

        const int8_t order = orders[curve_index];
        const bool is_cyclic = cyclic[curve_index];
        const KnotsMode mode = KnotsMode(knots_modes[curve_index]);

        if (!curves::nurbs::check_valid_size_and_order(points.size(), order, is_cyclic, mode)) {
          basis_caches[curve_index].invalid = true;
          continue;
        }

        const int knots_size = curves::nurbs::knots_size(points.size(), order, is_cyclic);
        Array<float> knots(knots_size);
        curves::nurbs::calculate_knots(points.size(), mode, order, is_cyclic, knots);
        curves::nurbs::calculate_basis_cache(points.size(),
                                             evaluated_points.size(),
                                             order,
                                             is_cyclic,
                                             knots,
                                             basis_caches[curve_index]);
      }
    });
  });

  this->runtime->nurbs_basis_cache_dirty = false;
}

Span<float3> CurvesGeometry::evaluated_positions() const
{
  if (!this->runtime->position_cache_dirty) {
    return this->runtime->evaluated_positions_span;
  }

  /* A double checked lock. */
  std::scoped_lock lock{this->runtime->position_cache_mutex};
  if (!this->runtime->position_cache_dirty) {
    return this->runtime->evaluated_positions_span;
  }

  threading::isolate_task([&]() {
    if (this->is_single_type(CURVE_TYPE_POLY)) {
      this->runtime->evaluated_positions_span = this->positions();
      this->runtime->evaluated_position_cache.clear_and_make_inline();
      return;
    }

    this->runtime->evaluated_position_cache.resize(this->evaluated_points_num());
    MutableSpan<float3> evaluated_positions = this->runtime->evaluated_position_cache;
    this->runtime->evaluated_positions_span = evaluated_positions;

    VArray<int8_t> types = this->curve_types();
    VArray<bool> cyclic = this->cyclic();
    VArray<int> resolution = this->resolution();
    Span<float3> positions = this->positions();

    Span<float3> handle_positions_left = this->handle_positions_left();
    Span<float3> handle_positions_right = this->handle_positions_right();
    Span<int> bezier_evaluated_offsets = this->runtime->bezier_evaluated_offsets;

    VArray<int8_t> nurbs_orders = this->nurbs_orders();
    Span<float> nurbs_weights = this->nurbs_weights();

    this->ensure_nurbs_basis_cache();

    threading::parallel_for(this->curves_range(), 128, [&](IndexRange curves_range) {
      for (const int curve_index : curves_range) {
        const IndexRange points = this->points_for_curve(curve_index);
        const IndexRange evaluated_points = this->evaluated_points_for_curve(curve_index);

        switch (types[curve_index]) {
          case CURVE_TYPE_CATMULL_ROM:
            curves::catmull_rom::interpolate_to_evaluated(
                positions.slice(points),
                cyclic[curve_index],
                resolution[curve_index],
                evaluated_positions.slice(evaluated_points));
            break;
          case CURVE_TYPE_POLY:
            evaluated_positions.slice(evaluated_points).copy_from(positions.slice(points));
            break;
          case CURVE_TYPE_BEZIER:
            curves::bezier::calculate_evaluated_positions(
                positions.slice(points),
                handle_positions_left.slice(points),
                handle_positions_right.slice(points),
                bezier_evaluated_offsets.slice(points),
                evaluated_positions.slice(evaluated_points));
            break;
          case CURVE_TYPE_NURBS: {
            curves::nurbs::interpolate_to_evaluated(this->runtime->nurbs_basis_cache[curve_index],
                                                    nurbs_orders[curve_index],
                                                    nurbs_weights.slice(points),
                                                    positions.slice(points),
                                                    evaluated_positions.slice(evaluated_points));
            break;
          }
          default:
            BLI_assert_unreachable();
            break;
        }
      }
    });
  });

  this->runtime->position_cache_dirty = false;
  return this->runtime->evaluated_positions_span;
}

Span<float3> CurvesGeometry::evaluated_tangents() const
{
  if (!this->runtime->tangent_cache_dirty) {
    return this->runtime->evaluated_tangent_cache;
  }

  /* A double checked lock. */
  std::scoped_lock lock{this->runtime->tangent_cache_mutex};
  if (!this->runtime->tangent_cache_dirty) {
    return this->runtime->evaluated_tangent_cache;
  }

  threading::isolate_task([&]() {
    const Span<float3> evaluated_positions = this->evaluated_positions();
    const VArray<bool> cyclic = this->cyclic();

    this->runtime->evaluated_tangent_cache.resize(this->evaluated_points_num());
    MutableSpan<float3> tangents = this->runtime->evaluated_tangent_cache;

    threading::parallel_for(this->curves_range(), 128, [&](IndexRange curves_range) {
      for (const int curve_index : curves_range) {
        const IndexRange evaluated_points = this->evaluated_points_for_curve(curve_index);
        curves::poly::calculate_tangents(evaluated_positions.slice(evaluated_points),
                                         cyclic[curve_index],
                                         tangents.slice(evaluated_points));
      }
    });

    /* Correct the first and last tangents of Bezier curves so that they align with the inner
     * handles. This is a separate loop to avoid the cost when Bezier type curves are not used. */
    Vector<int64_t> bezier_indices;
    const IndexMask bezier_mask = this->indices_for_curve_type(CURVE_TYPE_BEZIER, bezier_indices);
    if (!bezier_mask.is_empty()) {
      const Span<float3> positions = this->positions();
      const Span<float3> handles_left = this->handle_positions_left();
      const Span<float3> handles_right = this->handle_positions_right();

      threading::parallel_for(bezier_mask.index_range(), 1024, [&](IndexRange range) {
        for (const int curve_index : bezier_mask.slice(range)) {
          const IndexRange points = this->points_for_curve(curve_index);
          const IndexRange evaluated_points = this->evaluated_points_for_curve(curve_index);

          if (handles_right[points.first()] != positions[points.first()]) {
            tangents[evaluated_points.first()] = math::normalize(handles_right[points.first()] -
                                                                 positions[points.first()]);
          }
          if (handles_left[points.last()] != positions[points.last()]) {
            tangents[evaluated_points.last()] = math::normalize(positions[points.last()] -
                                                                handles_left[points.last()]);
          }
        }
      });
    }
  });

  this->runtime->tangent_cache_dirty = false;
  return this->runtime->evaluated_tangent_cache;
}

static void rotate_directions_around_axes(MutableSpan<float3> directions,
                                          const Span<float3> axes,
                                          const Span<float> angles)
{
  for (const int i : directions.index_range()) {
    directions[i] = math::rotate_direction_around_axis(directions[i], axes[i], angles[i]);
  }
}

Span<float3> CurvesGeometry::evaluated_normals() const
{
  if (!this->runtime->normal_cache_dirty) {
    return this->runtime->evaluated_normal_cache;
  }

  /* A double checked lock. */
  std::scoped_lock lock{this->runtime->normal_cache_mutex};
  if (!this->runtime->normal_cache_dirty) {
    return this->runtime->evaluated_normal_cache;
  }

  threading::isolate_task([&]() {
    const Span<float3> evaluated_tangents = this->evaluated_tangents();
    const VArray<bool> cyclic = this->cyclic();
    const VArray<int8_t> normal_mode = this->normal_mode();
    const VArray<int8_t> types = this->curve_types();
    const VArray<float> tilt = this->tilt();

    this->runtime->evaluated_normal_cache.resize(this->evaluated_points_num());
    MutableSpan<float3> evaluated_normals = this->runtime->evaluated_normal_cache;

    threading::parallel_for(this->curves_range(), 128, [&](IndexRange curves_range) {
      /* Reuse a buffer for the evaluated tilts. */
      Vector<float> evaluated_tilts;

      for (const int curve_index : curves_range) {
        const IndexRange evaluated_points = this->evaluated_points_for_curve(curve_index);
        switch (normal_mode[curve_index]) {
          case NORMAL_MODE_Z_UP:
            curves::poly::calculate_normals_z_up(evaluated_tangents.slice(evaluated_points),
                                                 evaluated_normals.slice(evaluated_points));
            break;
          case NORMAL_MODE_MINIMUM_TWIST:
            curves::poly::calculate_normals_minimum(evaluated_tangents.slice(evaluated_points),
                                                    cyclic[curve_index],
                                                    evaluated_normals.slice(evaluated_points));
            break;
        }

        /* If the "tilt" attribute exists, rotate the normals around the tangents by the
         * evaluated angles. We can avoid copying the tilts to evaluate them for poly curves. */
        if (!(tilt.is_single() && tilt.get_internal_single() == 0.0f)) {
          const IndexRange points = this->points_for_curve(curve_index);
          Span<float> curve_tilt = tilt.get_internal_span().slice(points);
          if (types[curve_index] == CURVE_TYPE_POLY) {
            rotate_directions_around_axes(evaluated_normals.slice(evaluated_points),
                                          evaluated_tangents.slice(evaluated_points),
                                          curve_tilt);
          }
          else {
            evaluated_tilts.clear();
            evaluated_tilts.resize(evaluated_points.size());
            this->interpolate_to_evaluated(
                curve_index, curve_tilt, evaluated_tilts.as_mutable_span());
            rotate_directions_around_axes(evaluated_normals.slice(evaluated_points),
                                          evaluated_tangents.slice(evaluated_points),
                                          evaluated_tilts.as_span());
          }
        }
      }
    });
  });

  this->runtime->normal_cache_dirty = false;
  return this->runtime->evaluated_normal_cache;
}

void CurvesGeometry::interpolate_to_evaluated(const int curve_index,
                                              const GSpan src,
                                              GMutableSpan dst) const
{
  BLI_assert(!this->runtime->offsets_cache_dirty);
  BLI_assert(!this->runtime->nurbs_basis_cache_dirty);
  const IndexRange points = this->points_for_curve(curve_index);
  BLI_assert(src.size() == points.size());
  BLI_assert(dst.size() == this->evaluated_points_for_curve(curve_index).size());
  switch (this->curve_types()[curve_index]) {
    case CURVE_TYPE_CATMULL_ROM:
      curves::catmull_rom::interpolate_to_evaluated(
          src, this->cyclic()[curve_index], this->resolution()[curve_index], dst);
      return;
    case CURVE_TYPE_POLY:
      dst.type().copy_assign_n(src.data(), dst.data(), src.size());
      return;
    case CURVE_TYPE_BEZIER:
      curves::bezier::interpolate_to_evaluated(
          src, this->runtime->bezier_evaluated_offsets.as_span().slice(points), dst);
      return;
    case CURVE_TYPE_NURBS:
      curves::nurbs::interpolate_to_evaluated(this->runtime->nurbs_basis_cache[curve_index],
                                              this->nurbs_orders()[curve_index],
                                              this->nurbs_weights().slice(points),
                                              src,
                                              dst);
      return;
  }
  BLI_assert_unreachable();
}

void CurvesGeometry::interpolate_to_evaluated(const GSpan src, GMutableSpan dst) const
{
  BLI_assert(!this->runtime->offsets_cache_dirty);
  BLI_assert(!this->runtime->nurbs_basis_cache_dirty);
  const VArray<int8_t> types = this->curve_types();
  const VArray<int> resolution = this->resolution();
  const VArray<bool> cyclic = this->cyclic();
  const VArray<int8_t> nurbs_orders = this->nurbs_orders();
  const Span<float> nurbs_weights = this->nurbs_weights();

  threading::parallel_for(this->curves_range(), 512, [&](IndexRange curves_range) {
    for (const int curve_index : curves_range) {
      const IndexRange points = this->points_for_curve(curve_index);
      const IndexRange evaluated_points = this->evaluated_points_for_curve(curve_index);
      switch (types[curve_index]) {
        case CURVE_TYPE_CATMULL_ROM:
          curves::catmull_rom::interpolate_to_evaluated(src.slice(points),
                                                        cyclic[curve_index],
                                                        resolution[curve_index],
                                                        dst.slice(evaluated_points));
          continue;
        case CURVE_TYPE_POLY:
          dst.slice(evaluated_points).copy_from(src.slice(points));
          continue;
        case CURVE_TYPE_BEZIER:
          curves::bezier::interpolate_to_evaluated(
              src.slice(points),
              this->runtime->bezier_evaluated_offsets.as_span().slice(points),
              dst.slice(evaluated_points));
          continue;
        case CURVE_TYPE_NURBS:
          curves::nurbs::interpolate_to_evaluated(this->runtime->nurbs_basis_cache[curve_index],
                                                  nurbs_orders[curve_index],
                                                  nurbs_weights.slice(points),
                                                  src.slice(points),
                                                  dst.slice(evaluated_points));
          continue;
      }
    }
  });
}

void CurvesGeometry::ensure_evaluated_lengths() const
{
  if (!this->runtime->length_cache_dirty) {
    return;
  }

  /* A double checked lock. */
  std::scoped_lock lock{this->runtime->length_cache_mutex};
  if (!this->runtime->length_cache_dirty) {
    return;
  }

  threading::isolate_task([&]() {
    /* Use an extra length value for the final cyclic segment for a consistent size
     * (see comment on #evaluated_length_cache). */
    const int total_size = this->evaluated_points_num() + this->curves_num();
    this->runtime->evaluated_length_cache.resize(total_size);
    MutableSpan<float> evaluated_lengths = this->runtime->evaluated_length_cache;

    Span<float3> evaluated_positions = this->evaluated_positions();
    VArray<bool> curves_cyclic = this->cyclic();

    threading::parallel_for(this->curves_range(), 128, [&](IndexRange curves_range) {
      for (const int curve_index : curves_range) {
        const bool cyclic = curves_cyclic[curve_index];
        const IndexRange evaluated_points = this->evaluated_points_for_curve(curve_index);
        const IndexRange lengths_range = this->lengths_range_for_curve(curve_index, cyclic);
        length_parameterize::accumulate_lengths(evaluated_positions.slice(evaluated_points),
                                                cyclic,
                                                evaluated_lengths.slice(lengths_range));
      }
    });
  });

  this->runtime->length_cache_dirty = false;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Operations
 * \{ */

void CurvesGeometry::resize(const int points_num, const int curves_num)
{
  if (points_num != this->point_size) {
    CustomData_realloc(&this->point_data, points_num);
    this->point_size = points_num;
  }
  if (curves_num != this->curve_size) {
    CustomData_realloc(&this->curve_data, curves_num);
    this->curve_size = curves_num;
    this->curve_offsets = (int *)MEM_reallocN(this->curve_offsets, sizeof(int) * (curves_num + 1));
  }
  this->tag_topology_changed();
  this->update_customdata_pointers();
}

void CurvesGeometry::tag_positions_changed()
{
  this->runtime->position_cache_dirty = true;
  this->runtime->tangent_cache_dirty = true;
  this->runtime->normal_cache_dirty = true;
  this->runtime->length_cache_dirty = true;
}
void CurvesGeometry::tag_topology_changed()
{
  this->runtime->position_cache_dirty = true;
  this->runtime->tangent_cache_dirty = true;
  this->runtime->normal_cache_dirty = true;
  this->runtime->offsets_cache_dirty = true;
  this->runtime->nurbs_basis_cache_dirty = true;
  this->runtime->length_cache_dirty = true;
}
void CurvesGeometry::tag_normals_changed()
{
  this->runtime->normal_cache_dirty = true;
}

static void translate_positions(MutableSpan<float3> positions, const float3 &translation)
{
  threading::parallel_for(positions.index_range(), 2048, [&](const IndexRange range) {
    for (float3 &position : positions.slice(range)) {
      position += translation;
    }
  });
}

static void transform_positions(MutableSpan<float3> positions, const float4x4 &matrix)
{
  threading::parallel_for(positions.index_range(), 1024, [&](const IndexRange range) {
    for (float3 &position : positions.slice(range)) {
      position = matrix * position;
    }
  });
}

void CurvesGeometry::calculate_bezier_auto_handles()
{
  const VArray<int8_t> types = this->curve_types();
  if (types.is_single() && types.get_internal_single() != CURVE_TYPE_BEZIER) {
    return;
  }
  if (this->handle_positions_left().is_empty() || this->handle_positions_right().is_empty()) {
    return;
  }
  const VArray<bool> cyclic = this->cyclic();
  const VArray_Span<int8_t> types_left{this->handle_types_left()};
  const VArray_Span<int8_t> types_right{this->handle_types_right()};
  const Span<float3> positions = this->positions();
  MutableSpan<float3> positions_left = this->handle_positions_left_for_write();
  MutableSpan<float3> positions_right = this->handle_positions_right_for_write();

  threading::parallel_for(this->curves_range(), 128, [&](IndexRange range) {
    for (const int i_curve : range) {
      if (types[i_curve] == CURVE_TYPE_BEZIER) {
        const IndexRange points = this->points_for_curve(i_curve);
        curves::bezier::calculate_auto_handles(cyclic[i_curve],
                                               types_left.slice(points),
                                               types_right.slice(points),
                                               positions.slice(points),
                                               positions_left.slice(points),
                                               positions_right.slice(points));
      }
    }
  });
}

void CurvesGeometry::translate(const float3 &translation)
{
  translate_positions(this->positions_for_write(), translation);
  if (!this->handle_positions_left().is_empty()) {
    translate_positions(this->handle_positions_left_for_write(), translation);
  }
  if (!this->handle_positions_right().is_empty()) {
    translate_positions(this->handle_positions_right_for_write(), translation);
  }
  this->tag_positions_changed();
}

void CurvesGeometry::transform(const float4x4 &matrix)
{
  transform_positions(this->positions_for_write(), matrix);
  if (!this->handle_positions_left().is_empty()) {
    transform_positions(this->handle_positions_left_for_write(), matrix);
  }
  if (!this->handle_positions_right().is_empty()) {
    transform_positions(this->handle_positions_right_for_write(), matrix);
  }
  this->tag_positions_changed();
}

static std::optional<bounds::MinMaxResult<float3>> curves_bounds(const CurvesGeometry &curves)
{
  Span<float3> positions = curves.positions();
  if (curves.radius) {
    Span<float> radii{curves.radius, curves.points_num()};
    return bounds::min_max_with_radii(positions, radii);
  }
  return bounds::min_max(positions);
}

bool CurvesGeometry::bounds_min_max(float3 &min, float3 &max) const
{
  const std::optional<bounds::MinMaxResult<float3>> bounds = curves_bounds(*this);
  if (!bounds) {
    return false;
  }
  min = math::min(bounds->min, min);
  max = math::max(bounds->max, max);
  return true;
}

void CurvesGeometry::update_customdata_pointers()
{
  this->position = (float(*)[3])CustomData_get_layer_named(
      &this->point_data, CD_PROP_FLOAT3, ATTR_POSITION.c_str());
  this->radius = (float *)CustomData_get_layer_named(
      &this->point_data, CD_PROP_FLOAT, ATTR_RADIUS.c_str());
  this->curve_type = (int8_t *)CustomData_get_layer_named(
      &this->point_data, CD_PROP_INT8, ATTR_CURVE_TYPE.c_str());
}

static void *ensure_customdata_layer(CustomData &custom_data,
                                     const StringRefNull name,
                                     const CustomDataType data_type,
                                     const int tot_elements)
{
  for (const int other_layer_i : IndexRange(custom_data.totlayer)) {
    CustomDataLayer &new_layer = custom_data.layers[other_layer_i];
    if (name == StringRef(new_layer.name)) {
      return new_layer.data;
    }
  }
  return CustomData_add_layer_named(
      &custom_data, data_type, CD_DEFAULT, nullptr, tot_elements, name.c_str());
}

static CurvesGeometry copy_with_removed_curves(const CurvesGeometry &curves,
                                               const IndexMask curves_to_delete)
{
  const Span<int> old_offsets = curves.offsets();
  const Vector<IndexRange> old_curve_ranges = curves_to_delete.extract_ranges_invert(
      curves.curves_range(), nullptr);
  Vector<IndexRange> new_curve_ranges;
  Vector<IndexRange> old_point_ranges;
  Vector<IndexRange> new_point_ranges;
  int new_tot_points = 0;
  int new_tot_curves = 0;
  for (const IndexRange &curve_range : old_curve_ranges) {
    new_curve_ranges.append(IndexRange(new_tot_curves, curve_range.size()));
    new_tot_curves += curve_range.size();

    const IndexRange old_point_range = curves.points_for_curves(curve_range);
    old_point_ranges.append(old_point_range);
    new_point_ranges.append(IndexRange(new_tot_points, old_point_range.size()));
    new_tot_points += old_point_range.size();
  }

  CurvesGeometry new_curves{new_tot_points, new_tot_curves};

  threading::parallel_invoke(
      /* Initialize curve offsets. */
      [&]() {
        MutableSpan<int> new_offsets = new_curves.offsets_for_write();
        new_offsets.last() = new_tot_points;
        threading::parallel_for(
            old_curve_ranges.index_range(), 128, [&](const IndexRange ranges_range) {
              for (const int range_i : ranges_range) {
                const IndexRange old_curve_range = old_curve_ranges[range_i];
                const IndexRange new_curve_range = new_curve_ranges[range_i];
                const IndexRange old_point_range = old_point_ranges[range_i];
                const IndexRange new_point_range = new_point_ranges[range_i];
                const int offset_shift = new_point_range.start() - old_point_range.start();
                const int curves_in_range = old_curve_range.size();
                threading::parallel_for(
                    IndexRange(curves_in_range), 512, [&](const IndexRange range) {
                      for (const int i : range) {
                        const int old_curve_i = old_curve_range[i];
                        const int new_curve_i = new_curve_range[i];
                        const int old_offset = old_offsets[old_curve_i];
                        const int new_offset = old_offset + offset_shift;
                        new_offsets[new_curve_i] = new_offset;
                      }
                    });
              }
            });
      },
      /* Copy over point attributes. */
      [&]() {
        const CustomData &old_point_data = curves.point_data;
        CustomData &new_point_data = new_curves.point_data;
        for (const int layer_i : IndexRange(old_point_data.totlayer)) {
          const CustomDataLayer &old_layer = old_point_data.layers[layer_i];
          const CustomDataType data_type = static_cast<CustomDataType>(old_layer.type);
          const CPPType &type = *bke::custom_data_type_to_cpp_type(data_type);

          const void *src_buffer = old_layer.data;
          void *dst_buffer = ensure_customdata_layer(
              new_point_data, old_layer.name, data_type, new_tot_points);

          threading::parallel_for(
              old_curve_ranges.index_range(), 128, [&](const IndexRange ranges_range) {
                for (const int range_i : ranges_range) {
                  const IndexRange old_point_range = old_point_ranges[range_i];
                  const IndexRange new_point_range = new_point_ranges[range_i];

                  type.copy_construct_n(
                      POINTER_OFFSET(src_buffer, type.size() * old_point_range.start()),
                      POINTER_OFFSET(dst_buffer, type.size() * new_point_range.start()),
                      old_point_range.size());
                }
              });
        }
      },
      /* Copy over curve attributes. */
      [&]() {
        const CustomData &old_curve_data = curves.curve_data;
        CustomData &new_curve_data = new_curves.curve_data;
        for (const int layer_i : IndexRange(old_curve_data.totlayer)) {
          const CustomDataLayer &old_layer = old_curve_data.layers[layer_i];
          const CustomDataType data_type = static_cast<CustomDataType>(old_layer.type);
          const CPPType &type = *bke::custom_data_type_to_cpp_type(data_type);

          const void *src_buffer = old_layer.data;
          void *dst_buffer = ensure_customdata_layer(
              new_curve_data, old_layer.name, data_type, new_tot_points);

          threading::parallel_for(
              old_curve_ranges.index_range(), 128, [&](const IndexRange ranges_range) {
                for (const int range_i : ranges_range) {
                  const IndexRange old_curve_range = old_curve_ranges[range_i];
                  const IndexRange new_curve_range = new_curve_ranges[range_i];

                  type.copy_construct_n(
                      POINTER_OFFSET(src_buffer, type.size() * old_curve_range.start()),
                      POINTER_OFFSET(dst_buffer, type.size() * new_curve_range.start()),
                      old_curve_range.size());
                }
              });
        }
      });

  new_curves.update_curve_types();

  return new_curves;
}

void CurvesGeometry::remove_curves(const IndexMask curves_to_delete)
{
  *this = copy_with_removed_curves(*this, curves_to_delete);
}

template<typename T>
static void reverse_curve_point_data(const CurvesGeometry &curves,
                                     const IndexMask curve_selection,
                                     MutableSpan<T> data)
{
  threading::parallel_for(curve_selection.index_range(), 256, [&](IndexRange range) {
    for (const int curve_i : curve_selection.slice(range)) {
      data.slice(curves.points_for_curve(curve_i)).reverse();
    }
  });
}

template<typename T>
static void reverse_swap_curve_point_data(const CurvesGeometry &curves,
                                          const IndexMask curve_selection,
                                          MutableSpan<T> data_a,
                                          MutableSpan<T> data_b)
{
  threading::parallel_for(curve_selection.index_range(), 256, [&](IndexRange range) {
    for (const int curve_i : curve_selection.slice(range)) {
      const IndexRange points = curves.points_for_curve(curve_i);
      MutableSpan<T> a = data_a.slice(points);
      MutableSpan<T> b = data_b.slice(points);
      for (const int i : IndexRange(points.size() / 2)) {
        const int end_index = points.size() - 1 - i;
        std::swap(a[end_index], b[i]);
        std::swap(b[end_index], a[i]);
      }
    }
  });
}

static bool layer_matches_name_and_type(const CustomDataLayer &layer,
                                        const StringRef name,
                                        const CustomDataType type)
{
  if (layer.type != type) {
    return false;
  }
  return layer.name == name;
}

void CurvesGeometry::reverse_curves(const IndexMask curves_to_reverse)
{
  CustomData_duplicate_referenced_layers(&this->point_data, this->points_num());

  /* Collect the Bezier handle attributes while iterating through the point custom data layers;
   * they need special treatment later. */
  MutableSpan<float3> positions_left;
  MutableSpan<float3> positions_right;
  MutableSpan<int8_t> types_left;
  MutableSpan<int8_t> types_right;

  for (const int layer_i : IndexRange(this->point_data.totlayer)) {
    CustomDataLayer &layer = this->point_data.layers[layer_i];

    if (positions_left.is_empty() &&
        layer_matches_name_and_type(layer, ATTR_HANDLE_POSITION_LEFT, CD_PROP_FLOAT3)) {
      positions_left = {static_cast<float3 *>(layer.data), this->points_num()};
      continue;
    }
    if (positions_right.is_empty() &&
        layer_matches_name_and_type(layer, ATTR_HANDLE_POSITION_RIGHT, CD_PROP_FLOAT3)) {
      positions_right = {static_cast<float3 *>(layer.data), this->points_num()};
      continue;
    }
    if (types_left.is_empty() &&
        layer_matches_name_and_type(layer, ATTR_HANDLE_TYPE_LEFT, CD_PROP_INT8)) {
      types_left = {static_cast<int8_t *>(layer.data), this->points_num()};
      continue;
    }
    if (types_right.is_empty() &&
        layer_matches_name_and_type(layer, ATTR_HANDLE_TYPE_RIGHT, CD_PROP_INT8)) {
      types_right = {static_cast<int8_t *>(layer.data), this->points_num()};
      continue;
    }

    const CustomDataType data_type = static_cast<CustomDataType>(layer.type);
    attribute_math::convert_to_static_type(data_type, [&](auto dummy) {
      using T = decltype(dummy);
      reverse_curve_point_data<T>(
          *this, curves_to_reverse, {static_cast<T *>(layer.data), this->points_num()});
    });
  }

  /* In order to maintain the shape of Bezier curves, handle attributes must reverse, but also the
   * values for the left and right must swap. Use a utility to swap and reverse at the same time,
   * to avoid loading the attribute twice. Generally we can expect the right layer to exist when
   * the left does, but there's no need to count on it, so check for both attributes. */

  if (!positions_left.is_empty() && !positions_right.is_empty()) {
    reverse_swap_curve_point_data(*this, curves_to_reverse, positions_left, positions_right);
  }
  if (!types_left.is_empty() && !types_right.is_empty()) {
    reverse_swap_curve_point_data(*this, curves_to_reverse, types_left, types_right);
  }

  this->tag_topology_changed();
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Domain Interpolation
 * \{ */

/**
 * Mix together all of a curve's control point values.
 *
 * \note Theoretically this interpolation does not need to compute all values at once.
 * However, doing that makes the implementation simpler, and this can be optimized in the future if
 * only some values are required.
 */
template<typename T>
static void adapt_curve_domain_point_to_curve_impl(const CurvesGeometry &curves,
                                                   const VArray<T> &old_values,
                                                   MutableSpan<T> r_values)
{
  attribute_math::DefaultMixer<T> mixer(r_values);
  for (const int i_curve : IndexRange(curves.curves_num())) {
    for (const int i_point : curves.points_for_curve(i_curve)) {
      mixer.mix_in(i_curve, old_values[i_point]);
    }
  }
  mixer.finalize();
}

/**
 * A curve is selected if all of its control points were selected.
 *
 * \note Theoretically this interpolation does not need to compute all values at once.
 * However, doing that makes the implementation simpler, and this can be optimized in the future if
 * only some values are required.
 */
template<>
void adapt_curve_domain_point_to_curve_impl(const CurvesGeometry &curves,
                                            const VArray<bool> &old_values,
                                            MutableSpan<bool> r_values)
{
  r_values.fill(true);
  for (const int i_curve : IndexRange(curves.curves_num())) {
    for (const int i_point : curves.points_for_curve(i_curve)) {
      if (!old_values[i_point]) {
        r_values[i_curve] = false;
        break;
      }
    }
  }
}

static GVArray adapt_curve_domain_point_to_curve(const CurvesGeometry &curves,
                                                 const GVArray &varray)
{
  GVArray new_varray;
  attribute_math::convert_to_static_type(varray.type(), [&](auto dummy) {
    using T = decltype(dummy);
    if constexpr (!std::is_void_v<attribute_math::DefaultMixer<T>>) {
      Array<T> values(curves.curves_num());
      adapt_curve_domain_point_to_curve_impl<T>(curves, varray.typed<T>(), values);
      new_varray = VArray<T>::ForContainer(std::move(values));
    }
  });
  return new_varray;
}

/**
 * Copy the value from a curve to all of its points.
 *
 * \note Theoretically this interpolation does not need to compute all values at once.
 * However, doing that makes the implementation simpler, and this can be optimized in the future if
 * only some values are required.
 */
template<typename T>
static void adapt_curve_domain_curve_to_point_impl(const CurvesGeometry &curves,
                                                   const VArray<T> &old_values,
                                                   MutableSpan<T> r_values)
{
  for (const int i_curve : IndexRange(curves.curves_num())) {
    r_values.slice(curves.points_for_curve(i_curve)).fill(old_values[i_curve]);
  }
}

static GVArray adapt_curve_domain_curve_to_point(const CurvesGeometry &curves,
                                                 const GVArray &varray)
{
  GVArray new_varray;
  attribute_math::convert_to_static_type(varray.type(), [&](auto dummy) {
    using T = decltype(dummy);
    Array<T> values(curves.points_num());
    adapt_curve_domain_curve_to_point_impl<T>(curves, varray.typed<T>(), values);
    new_varray = VArray<T>::ForContainer(std::move(values));
  });
  return new_varray;
}

GVArray CurvesGeometry::adapt_domain(const GVArray &varray,
                                     const AttributeDomain from,
                                     const AttributeDomain to) const
{
  if (!varray) {
    return {};
  }
  if (varray.is_empty()) {
    return {};
  }
  if (from == to) {
    return varray;
  }

  if (from == ATTR_DOMAIN_POINT && to == ATTR_DOMAIN_CURVE) {
    return adapt_curve_domain_point_to_curve(*this, varray);
  }
  if (from == ATTR_DOMAIN_CURVE && to == ATTR_DOMAIN_POINT) {
    return adapt_curve_domain_curve_to_point(*this, varray);
  }

  BLI_assert_unreachable();
  return {};
}

/** \} */

}  // namespace blender::bke
