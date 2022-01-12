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
 */

#include "BLI_listbase.h"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"

#include "BKE_attribute_access.hh"
#include "BKE_attribute_math.hh"
#include "BKE_deform.h"
#include "BKE_geometry_set.hh"
#include "BKE_lib_id.h"
#include "BKE_mesh.h"

#include "attribute_access_intern.hh"

extern "C" MDeformVert *BKE_object_defgroup_data_create(ID *id);

/* -------------------------------------------------------------------- */
/** \name Geometry Component Implementation
 * \{ */

MeshComponent::MeshComponent() : GeometryComponent(GEO_COMPONENT_TYPE_MESH)
{
}

MeshComponent::~MeshComponent()
{
  this->clear();
}

GeometryComponent *MeshComponent::copy() const
{
  MeshComponent *new_component = new MeshComponent();
  if (mesh_ != nullptr) {
    new_component->mesh_ = BKE_mesh_copy_for_eval(mesh_, false);
    new_component->ownership_ = GeometryOwnershipType::Owned;
  }
  return new_component;
}

void MeshComponent::clear()
{
  BLI_assert(this->is_mutable());
  if (mesh_ != nullptr) {
    if (ownership_ == GeometryOwnershipType::Owned) {
      BKE_id_free(nullptr, mesh_);
    }
    mesh_ = nullptr;
  }
}

bool MeshComponent::has_mesh() const
{
  return mesh_ != nullptr;
}

void MeshComponent::replace(Mesh *mesh, GeometryOwnershipType ownership)
{
  BLI_assert(this->is_mutable());
  this->clear();
  mesh_ = mesh;
  ownership_ = ownership;
}

Mesh *MeshComponent::release()
{
  BLI_assert(this->is_mutable());
  Mesh *mesh = mesh_;
  mesh_ = nullptr;
  return mesh;
}

const Mesh *MeshComponent::get_for_read() const
{
  return mesh_;
}

Mesh *MeshComponent::get_for_write()
{
  BLI_assert(this->is_mutable());
  if (ownership_ == GeometryOwnershipType::ReadOnly) {
    mesh_ = BKE_mesh_copy_for_eval(mesh_, false);
    ownership_ = GeometryOwnershipType::Owned;
  }
  return mesh_;
}

bool MeshComponent::is_empty() const
{
  return mesh_ == nullptr;
}

bool MeshComponent::owns_direct_data() const
{
  return ownership_ == GeometryOwnershipType::Owned;
}

void MeshComponent::ensure_owns_direct_data()
{
  BLI_assert(this->is_mutable());
  if (ownership_ != GeometryOwnershipType::Owned) {
    mesh_ = BKE_mesh_copy_for_eval(mesh_, false);
    ownership_ = GeometryOwnershipType::Owned;
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Mesh Normals Field Input
 * \{ */

namespace blender::bke {

static VArray<float3> mesh_face_normals(const Mesh &mesh,
                                        const Span<MVert> verts,
                                        const Span<MPoly> polys,
                                        const Span<MLoop> loops,
                                        const IndexMask mask)
{
  /* Use existing normals to avoid unnecessarily recalculating them, if possible. */
  if (!(mesh.runtime.cd_dirty_poly & CD_MASK_NORMAL) &&
      CustomData_has_layer(&mesh.pdata, CD_NORMAL)) {
    const void *data = CustomData_get_layer(&mesh.pdata, CD_NORMAL);

    return VArray<float3>::ForSpan({(const float3 *)data, polys.size()});
  }

  auto normal_fn = [verts, polys, loops](const int i) -> float3 {
    float3 normal;
    const MPoly &poly = polys[i];
    BKE_mesh_calc_poly_normal(&poly, &loops[poly.loopstart], verts.data(), normal);
    return normal;
  };

  return VArray<float3>::ForFunc(mask.min_array_size(), normal_fn);
}

static VArray<float3> mesh_vertex_normals(const Mesh &mesh,
                                          const Span<MVert> verts,
                                          const Span<MPoly> polys,
                                          const Span<MLoop> loops,
                                          const IndexMask mask)
{
  /* Use existing normals to avoid unnecessarily recalculating them, if possible. */
  if (!(mesh.runtime.cd_dirty_vert & CD_MASK_NORMAL) &&
      CustomData_has_layer(&mesh.vdata, CD_NORMAL)) {
    const void *data = CustomData_get_layer(&mesh.pdata, CD_NORMAL);

    return VArray<float3>::ForSpan({(const float3 *)data, mesh.totvert});
  }

  /* If the normals are dirty, they must be recalculated for the output of this node's field
   * source. Ideally vertex normals could be calculated lazily on a const mesh, but that's not
   * possible at the moment, so we take ownership of the results. Sadly we must also create a copy
   * of MVert to use the mesh normals API. This can be improved by adding mutex-protected lazy
   * calculation of normals on meshes.
   *
   * Use mask.min_array_size() to avoid calculating a final chunk of data if possible. */
  Array<MVert> temp_verts(verts);
  Array<float3> normals(verts.size()); /* Use full size for accumulation from faces. */
  BKE_mesh_calc_normals_poly_and_vertex(temp_verts.data(),
                                        mask.min_array_size(),
                                        loops.data(),
                                        loops.size(),
                                        polys.data(),
                                        polys.size(),
                                        nullptr,
                                        (float(*)[3])normals.data());

  return VArray<float3>::ForContainer(std::move(normals));
}

VArray<float3> mesh_normals_varray(const MeshComponent &mesh_component,
                                   const Mesh &mesh,
                                   const IndexMask mask,
                                   const AttributeDomain domain)
{
  Span<MVert> verts{mesh.mvert, mesh.totvert};
  Span<MEdge> edges{mesh.medge, mesh.totedge};
  Span<MPoly> polys{mesh.mpoly, mesh.totpoly};
  Span<MLoop> loops{mesh.mloop, mesh.totloop};

  switch (domain) {
    case ATTR_DOMAIN_FACE: {
      return mesh_face_normals(mesh, verts, polys, loops, mask);
    }
    case ATTR_DOMAIN_POINT: {
      return mesh_vertex_normals(mesh, verts, polys, loops, mask);
    }
    case ATTR_DOMAIN_EDGE: {
      /* In this case, start with vertex normals and convert to the edge domain, since the
       * conversion from edges to vertices is very simple. Use the full mask since the edges
       * might use the vertex normal from any index. */
      GVArray vert_normals = mesh_vertex_normals(
          mesh, verts, polys, loops, IndexRange(verts.size()));
      Span<float3> vert_normals_span = vert_normals.get_internal_span().typed<float3>();
      Array<float3> edge_normals(mask.min_array_size());

      /* Use "manual" domain interpolation instead of the GeometryComponent API to avoid
       * calculating unnecessary values and to allow normalizing the result much more simply. */
      for (const int i : mask) {
        const MEdge &edge = edges[i];
        edge_normals[i] = float3::interpolate(
                              vert_normals_span[edge.v1], vert_normals_span[edge.v2], 0.5f)
                              .normalized();
      }

      return VArray<float3>::ForContainer(std::move(edge_normals));
    }
    case ATTR_DOMAIN_CORNER: {
      /* The normals on corners are just the mesh's face normals, so start with the face normal
       * array and copy the face normal for each of its corners. */
      VArray<float3> face_normals = mesh_face_normals(
          mesh, verts, polys, loops, IndexRange(polys.size()));

      /* In this case using the mesh component's generic domain interpolation is fine, the data
       * will still be normalized, since the face normal is just copied to every corner. */
      return mesh_component.attribute_try_adapt_domain<float3>(
          std::move(face_normals), ATTR_DOMAIN_FACE, ATTR_DOMAIN_CORNER);
    }
    default:
      return {};
  }
}

}  // namespace blender::bke

/** \} */

/* -------------------------------------------------------------------- */
/** \name Attribute Access
 * \{ */

int MeshComponent::attribute_domain_size(const AttributeDomain domain) const
{
  if (mesh_ == nullptr) {
    return 0;
  }
  switch (domain) {
    case ATTR_DOMAIN_CORNER:
      return mesh_->totloop;
    case ATTR_DOMAIN_POINT:
      return mesh_->totvert;
    case ATTR_DOMAIN_EDGE:
      return mesh_->totedge;
    case ATTR_DOMAIN_FACE:
      return mesh_->totpoly;
    default:
      break;
  }
  return 0;
}

namespace blender::bke {

template<typename T>
static void adapt_mesh_domain_corner_to_point_impl(const Mesh &mesh,
                                                   const VArray<T> &old_values,
                                                   MutableSpan<T> r_values)
{
  BLI_assert(r_values.size() == mesh.totvert);
  attribute_math::DefaultMixer<T> mixer(r_values);

  for (const int loop_index : IndexRange(mesh.totloop)) {
    const T value = old_values[loop_index];
    const MLoop &loop = mesh.mloop[loop_index];
    const int point_index = loop.v;
    mixer.mix_in(point_index, value);
  }
  mixer.finalize();
}

/* A vertex is selected if all connected face corners were selected and it is not loose. */
template<>
void adapt_mesh_domain_corner_to_point_impl(const Mesh &mesh,
                                            const VArray<bool> &old_values,
                                            MutableSpan<bool> r_values)
{
  BLI_assert(r_values.size() == mesh.totvert);
  Array<bool> loose_verts(mesh.totvert, true);

  r_values.fill(true);
  for (const int loop_index : IndexRange(mesh.totloop)) {
    const MLoop &loop = mesh.mloop[loop_index];
    const int point_index = loop.v;

    loose_verts[point_index] = false;
    if (!old_values[loop_index]) {
      r_values[point_index] = false;
    }
  }

  /* Deselect loose vertices without corners that are still selected from the 'true' default. */
  for (const int vert_index : IndexRange(mesh.totvert)) {
    if (loose_verts[vert_index]) {
      r_values[vert_index] = false;
    }
  }
}

static GVArray adapt_mesh_domain_corner_to_point(const Mesh &mesh, const GVArray &varray)
{
  GVArray new_varray;
  attribute_math::convert_to_static_type(varray.type(), [&](auto dummy) {
    using T = decltype(dummy);
    if constexpr (!std::is_void_v<attribute_math::DefaultMixer<T>>) {
      /* We compute all interpolated values at once, because for this interpolation, one has to
       * iterate over all loops anyway. */
      Array<T> values(mesh.totvert);
      adapt_mesh_domain_corner_to_point_impl<T>(mesh, varray.typed<T>(), values);
      new_varray = VArray<T>::ForContainer(std::move(values));
    }
  });
  return new_varray;
}

/**
 * Each corner's value is simply a copy of the value at its vertex.
 *
 * \note Theoretically this interpolation does not need to compute all values at once.
 * However, doing that makes the implementation simpler, and this can be optimized in the future if
 * only some values are required.
 */
template<typename T>
static void adapt_mesh_domain_point_to_corner_impl(const Mesh &mesh,
                                                   const VArray<T> &old_values,
                                                   MutableSpan<T> r_values)
{
  BLI_assert(r_values.size() == mesh.totloop);

  for (const int loop_index : IndexRange(mesh.totloop)) {
    const int vertex_index = mesh.mloop[loop_index].v;
    r_values[loop_index] = old_values[vertex_index];
  }
}

static GVArray adapt_mesh_domain_point_to_corner(const Mesh &mesh, const GVArray &varray)
{
  GVArray new_varray;
  attribute_math::convert_to_static_type(varray.type(), [&](auto dummy) {
    using T = decltype(dummy);
    Array<T> values(mesh.totloop);
    adapt_mesh_domain_point_to_corner_impl<T>(mesh, varray.typed<T>(), values);
    new_varray = VArray<T>::ForContainer(std::move(values));
  });
  return new_varray;
}

/**
 * \note Theoretically this interpolation does not need to compute all values at once.
 * However, doing that makes the implementation simpler, and this can be optimized in the future if
 * only some values are required.
 */
template<typename T>
static void adapt_mesh_domain_corner_to_face_impl(const Mesh &mesh,
                                                  const VArray<T> &old_values,
                                                  MutableSpan<T> r_values)
{
  BLI_assert(r_values.size() == mesh.totpoly);
  attribute_math::DefaultMixer<T> mixer(r_values);

  for (const int poly_index : IndexRange(mesh.totpoly)) {
    const MPoly &poly = mesh.mpoly[poly_index];
    for (const int loop_index : IndexRange(poly.loopstart, poly.totloop)) {
      const T value = old_values[loop_index];
      mixer.mix_in(poly_index, value);
    }
  }

  mixer.finalize();
}

/* A face is selected if all of its corners were selected. */
template<>
void adapt_mesh_domain_corner_to_face_impl(const Mesh &mesh,
                                           const VArray<bool> &old_values,
                                           MutableSpan<bool> r_values)
{
  BLI_assert(r_values.size() == mesh.totpoly);

  r_values.fill(true);
  for (const int poly_index : IndexRange(mesh.totpoly)) {
    const MPoly &poly = mesh.mpoly[poly_index];
    for (const int loop_index : IndexRange(poly.loopstart, poly.totloop)) {
      if (!old_values[loop_index]) {
        r_values[poly_index] = false;
        break;
      }
    }
  }
}

static GVArray adapt_mesh_domain_corner_to_face(const Mesh &mesh, const GVArray &varray)
{
  GVArray new_varray;
  attribute_math::convert_to_static_type(varray.type(), [&](auto dummy) {
    using T = decltype(dummy);
    if constexpr (!std::is_void_v<attribute_math::DefaultMixer<T>>) {
      Array<T> values(mesh.totpoly);
      adapt_mesh_domain_corner_to_face_impl<T>(mesh, varray.typed<T>(), values);
      new_varray = VArray<T>::ForContainer(std::move(values));
    }
  });
  return new_varray;
}

template<typename T>
static void adapt_mesh_domain_corner_to_edge_impl(const Mesh &mesh,
                                                  const VArray<T> &old_values,
                                                  MutableSpan<T> r_values)
{
  BLI_assert(r_values.size() == mesh.totedge);
  attribute_math::DefaultMixer<T> mixer(r_values);

  for (const int poly_index : IndexRange(mesh.totpoly)) {
    const MPoly &poly = mesh.mpoly[poly_index];

    /* For every edge, mix values from the two adjacent corners (the current and next corner). */
    for (const int loop_index : IndexRange(poly.loopstart, poly.totloop)) {
      const int loop_index_next = (loop_index + 1) % poly.totloop;
      const MLoop &loop = mesh.mloop[loop_index];
      const int edge_index = loop.e;
      mixer.mix_in(edge_index, old_values[loop_index]);
      mixer.mix_in(edge_index, old_values[loop_index_next]);
    }
  }

  mixer.finalize();
}

/* An edge is selected if all corners on adjacent faces were selected. */
template<>
void adapt_mesh_domain_corner_to_edge_impl(const Mesh &mesh,
                                           const VArray<bool> &old_values,
                                           MutableSpan<bool> r_values)
{
  BLI_assert(r_values.size() == mesh.totedge);

  /* It may be possible to rely on the #ME_LOOSEEDGE flag, but that seems error-prone. */
  Array<bool> loose_edges(mesh.totedge, true);

  r_values.fill(true);
  for (const int poly_index : IndexRange(mesh.totpoly)) {
    const MPoly &poly = mesh.mpoly[poly_index];

    for (const int loop_index : IndexRange(poly.loopstart, poly.totloop)) {
      const int loop_index_next = (loop_index == poly.totloop) ? poly.loopstart : (loop_index + 1);
      const MLoop &loop = mesh.mloop[loop_index];
      const int edge_index = loop.e;
      loose_edges[edge_index] = false;

      if (!old_values[loop_index] || !old_values[loop_index_next]) {
        r_values[edge_index] = false;
      }
    }
  }

  /* Deselect loose edges without corners that are still selected from the 'true' default. */
  for (const int edge_index : IndexRange(mesh.totedge)) {
    if (loose_edges[edge_index]) {
      r_values[edge_index] = false;
    }
  }
}

static GVArray adapt_mesh_domain_corner_to_edge(const Mesh &mesh, const GVArray &varray)
{
  GVArray new_varray;
  attribute_math::convert_to_static_type(varray.type(), [&](auto dummy) {
    using T = decltype(dummy);
    if constexpr (!std::is_void_v<attribute_math::DefaultMixer<T>>) {
      Array<T> values(mesh.totedge);
      adapt_mesh_domain_corner_to_edge_impl<T>(mesh, varray.typed<T>(), values);
      new_varray = VArray<T>::ForContainer(std::move(values));
    }
  });
  return new_varray;
}

template<typename T>
void adapt_mesh_domain_face_to_point_impl(const Mesh &mesh,
                                          const VArray<T> &old_values,
                                          MutableSpan<T> r_values)
{
  BLI_assert(r_values.size() == mesh.totvert);
  attribute_math::DefaultMixer<T> mixer(r_values);

  for (const int poly_index : IndexRange(mesh.totpoly)) {
    const MPoly &poly = mesh.mpoly[poly_index];
    const T value = old_values[poly_index];
    for (const int loop_index : IndexRange(poly.loopstart, poly.totloop)) {
      const MLoop &loop = mesh.mloop[loop_index];
      const int point_index = loop.v;
      mixer.mix_in(point_index, value);
    }
  }

  mixer.finalize();
}

/* A vertex is selected if any of the connected faces were selected. */
template<>
void adapt_mesh_domain_face_to_point_impl(const Mesh &mesh,
                                          const VArray<bool> &old_values,
                                          MutableSpan<bool> r_values)
{
  BLI_assert(r_values.size() == mesh.totvert);

  r_values.fill(false);
  for (const int poly_index : IndexRange(mesh.totpoly)) {
    const MPoly &poly = mesh.mpoly[poly_index];
    if (old_values[poly_index]) {
      for (const int loop_index : IndexRange(poly.loopstart, poly.totloop)) {
        const MLoop &loop = mesh.mloop[loop_index];
        const int vert_index = loop.v;
        r_values[vert_index] = true;
      }
    }
  }
}

static GVArray adapt_mesh_domain_face_to_point(const Mesh &mesh, const GVArray &varray)
{
  GVArray new_varray;
  attribute_math::convert_to_static_type(varray.type(), [&](auto dummy) {
    using T = decltype(dummy);
    if constexpr (!std::is_void_v<attribute_math::DefaultMixer<T>>) {
      Array<T> values(mesh.totvert);
      adapt_mesh_domain_face_to_point_impl<T>(mesh, varray.typed<T>(), values);
      new_varray = VArray<T>::ForContainer(std::move(values));
    }
  });
  return new_varray;
}

/* Each corner's value is simply a copy of the value at its face. */
template<typename T>
void adapt_mesh_domain_face_to_corner_impl(const Mesh &mesh,
                                           const VArray<T> &old_values,
                                           MutableSpan<T> r_values)
{
  BLI_assert(r_values.size() == mesh.totloop);

  for (const int poly_index : IndexRange(mesh.totpoly)) {
    const MPoly &poly = mesh.mpoly[poly_index];
    MutableSpan<T> poly_corner_values = r_values.slice(poly.loopstart, poly.totloop);
    poly_corner_values.fill(old_values[poly_index]);
  }
}

static GVArray adapt_mesh_domain_face_to_corner(const Mesh &mesh, const GVArray &varray)
{
  GVArray new_varray;
  attribute_math::convert_to_static_type(varray.type(), [&](auto dummy) {
    using T = decltype(dummy);
    if constexpr (!std::is_void_v<attribute_math::DefaultMixer<T>>) {
      Array<T> values(mesh.totloop);
      adapt_mesh_domain_face_to_corner_impl<T>(mesh, varray.typed<T>(), values);
      new_varray = VArray<T>::ForContainer(std::move(values));
    }
  });
  return new_varray;
}

template<typename T>
void adapt_mesh_domain_face_to_edge_impl(const Mesh &mesh,
                                         const VArray<T> &old_values,
                                         MutableSpan<T> r_values)
{
  BLI_assert(r_values.size() == mesh.totedge);
  attribute_math::DefaultMixer<T> mixer(r_values);

  for (const int poly_index : IndexRange(mesh.totpoly)) {
    const MPoly &poly = mesh.mpoly[poly_index];
    const T value = old_values[poly_index];
    for (const int loop_index : IndexRange(poly.loopstart, poly.totloop)) {
      const MLoop &loop = mesh.mloop[loop_index];
      mixer.mix_in(loop.e, value);
    }
  }
  mixer.finalize();
}

/* An edge is selected if any connected face was selected. */
template<>
void adapt_mesh_domain_face_to_edge_impl(const Mesh &mesh,
                                         const VArray<bool> &old_values,
                                         MutableSpan<bool> r_values)
{
  BLI_assert(r_values.size() == mesh.totedge);

  r_values.fill(false);
  for (const int poly_index : IndexRange(mesh.totpoly)) {
    const MPoly &poly = mesh.mpoly[poly_index];
    if (old_values[poly_index]) {
      for (const int loop_index : IndexRange(poly.loopstart, poly.totloop)) {
        const MLoop &loop = mesh.mloop[loop_index];
        const int edge_index = loop.e;
        r_values[edge_index] = true;
      }
    }
  }
}

static GVArray adapt_mesh_domain_face_to_edge(const Mesh &mesh, const GVArray &varray)
{
  GVArray new_varray;
  attribute_math::convert_to_static_type(varray.type(), [&](auto dummy) {
    using T = decltype(dummy);
    if constexpr (!std::is_void_v<attribute_math::DefaultMixer<T>>) {
      Array<T> values(mesh.totedge);
      adapt_mesh_domain_face_to_edge_impl<T>(mesh, varray.typed<T>(), values);
      new_varray = VArray<T>::ForContainer(std::move(values));
    }
  });
  return new_varray;
}

/**
 * \note Theoretically this interpolation does not need to compute all values at once.
 * However, doing that makes the implementation simpler, and this can be optimized in the future if
 * only some values are required.
 */
template<typename T>
static void adapt_mesh_domain_point_to_face_impl(const Mesh &mesh,
                                                 const VArray<T> &old_values,
                                                 MutableSpan<T> r_values)
{
  BLI_assert(r_values.size() == mesh.totpoly);
  attribute_math::DefaultMixer<T> mixer(r_values);

  for (const int poly_index : IndexRange(mesh.totpoly)) {
    const MPoly &poly = mesh.mpoly[poly_index];
    for (const int loop_index : IndexRange(poly.loopstart, poly.totloop)) {
      MLoop &loop = mesh.mloop[loop_index];
      const int point_index = loop.v;
      mixer.mix_in(poly_index, old_values[point_index]);
    }
  }
  mixer.finalize();
}

/* A face is selected if all of its vertices were selected too. */
template<>
void adapt_mesh_domain_point_to_face_impl(const Mesh &mesh,
                                          const VArray<bool> &old_values,
                                          MutableSpan<bool> r_values)
{
  BLI_assert(r_values.size() == mesh.totpoly);

  r_values.fill(true);
  for (const int poly_index : IndexRange(mesh.totpoly)) {
    const MPoly &poly = mesh.mpoly[poly_index];
    for (const int loop_index : IndexRange(poly.loopstart, poly.totloop)) {
      MLoop &loop = mesh.mloop[loop_index];
      const int vert_index = loop.v;
      if (!old_values[vert_index]) {
        r_values[poly_index] = false;
        break;
      }
    }
  }
}

static GVArray adapt_mesh_domain_point_to_face(const Mesh &mesh, const GVArray &varray)
{
  GVArray new_varray;
  attribute_math::convert_to_static_type(varray.type(), [&](auto dummy) {
    using T = decltype(dummy);
    if constexpr (!std::is_void_v<attribute_math::DefaultMixer<T>>) {
      Array<T> values(mesh.totpoly);
      adapt_mesh_domain_point_to_face_impl<T>(mesh, varray.typed<T>(), values);
      new_varray = VArray<T>::ForContainer(std::move(values));
    }
  });
  return new_varray;
}

/**
 * \note Theoretically this interpolation does not need to compute all values at once.
 * However, doing that makes the implementation simpler, and this can be optimized in the future if
 * only some values are required.
 */
template<typename T>
static void adapt_mesh_domain_point_to_edge_impl(const Mesh &mesh,
                                                 const VArray<T> &old_values,
                                                 MutableSpan<T> r_values)
{
  BLI_assert(r_values.size() == mesh.totedge);
  attribute_math::DefaultMixer<T> mixer(r_values);

  for (const int edge_index : IndexRange(mesh.totedge)) {
    const MEdge &edge = mesh.medge[edge_index];
    mixer.mix_in(edge_index, old_values[edge.v1]);
    mixer.mix_in(edge_index, old_values[edge.v2]);
  }

  mixer.finalize();
}

/* An edge is selected if both of its vertices were selected. */
template<>
void adapt_mesh_domain_point_to_edge_impl(const Mesh &mesh,
                                          const VArray<bool> &old_values,
                                          MutableSpan<bool> r_values)
{
  BLI_assert(r_values.size() == mesh.totedge);

  for (const int edge_index : IndexRange(mesh.totedge)) {
    const MEdge &edge = mesh.medge[edge_index];
    r_values[edge_index] = old_values[edge.v1] && old_values[edge.v2];
  }
}

static GVArray adapt_mesh_domain_point_to_edge(const Mesh &mesh, const GVArray &varray)
{
  GVArray new_varray;
  attribute_math::convert_to_static_type(varray.type(), [&](auto dummy) {
    using T = decltype(dummy);
    if constexpr (!std::is_void_v<attribute_math::DefaultMixer<T>>) {
      Array<T> values(mesh.totedge);
      adapt_mesh_domain_point_to_edge_impl<T>(mesh, varray.typed<T>(), values);
      new_varray = VArray<T>::ForContainer(std::move(values));
    }
  });
  return new_varray;
}

template<typename T>
void adapt_mesh_domain_edge_to_corner_impl(const Mesh &mesh,
                                           const VArray<T> &old_values,
                                           MutableSpan<T> r_values)
{
  BLI_assert(r_values.size() == mesh.totloop);
  attribute_math::DefaultMixer<T> mixer(r_values);

  for (const int poly_index : IndexRange(mesh.totpoly)) {
    const MPoly &poly = mesh.mpoly[poly_index];

    /* For every corner, mix the values from the adjacent edges on the face. */
    for (const int loop_index : IndexRange(poly.loopstart, poly.totloop)) {
      const int loop_index_prev = loop_index - 1 + (loop_index == poly.loopstart) * poly.totloop;
      const MLoop &loop = mesh.mloop[loop_index];
      const MLoop &loop_prev = mesh.mloop[loop_index_prev];
      mixer.mix_in(loop_index, old_values[loop.e]);
      mixer.mix_in(loop_index, old_values[loop_prev.e]);
    }
  }

  mixer.finalize();
}

/* A corner is selected if its two adjacent edges were selected. */
template<>
void adapt_mesh_domain_edge_to_corner_impl(const Mesh &mesh,
                                           const VArray<bool> &old_values,
                                           MutableSpan<bool> r_values)
{
  BLI_assert(r_values.size() == mesh.totloop);

  r_values.fill(false);

  for (const int poly_index : IndexRange(mesh.totpoly)) {
    const MPoly &poly = mesh.mpoly[poly_index];
    for (const int loop_index : IndexRange(poly.loopstart, poly.totloop)) {
      const int loop_index_prev = loop_index - 1 + (loop_index == poly.loopstart) * poly.totloop;
      const MLoop &loop = mesh.mloop[loop_index];
      const MLoop &loop_prev = mesh.mloop[loop_index_prev];
      if (old_values[loop.e] && old_values[loop_prev.e]) {
        r_values[loop_index] = true;
      }
    }
  }
}

static GVArray adapt_mesh_domain_edge_to_corner(const Mesh &mesh, const GVArray &varray)
{
  GVArray new_varray;
  attribute_math::convert_to_static_type(varray.type(), [&](auto dummy) {
    using T = decltype(dummy);
    if constexpr (!std::is_void_v<attribute_math::DefaultMixer<T>>) {
      Array<T> values(mesh.totloop);
      adapt_mesh_domain_edge_to_corner_impl<T>(mesh, varray.typed<T>(), values);
      new_varray = VArray<T>::ForContainer(std::move(values));
    }
  });
  return new_varray;
}

template<typename T>
static void adapt_mesh_domain_edge_to_point_impl(const Mesh &mesh,
                                                 const VArray<T> &old_values,
                                                 MutableSpan<T> r_values)
{
  BLI_assert(r_values.size() == mesh.totvert);
  attribute_math::DefaultMixer<T> mixer(r_values);

  for (const int edge_index : IndexRange(mesh.totedge)) {
    const MEdge &edge = mesh.medge[edge_index];
    const T value = old_values[edge_index];
    mixer.mix_in(edge.v1, value);
    mixer.mix_in(edge.v2, value);
  }

  mixer.finalize();
}

/* A vertex is selected if any connected edge was selected. */
template<>
void adapt_mesh_domain_edge_to_point_impl(const Mesh &mesh,
                                          const VArray<bool> &old_values,
                                          MutableSpan<bool> r_values)
{
  BLI_assert(r_values.size() == mesh.totvert);

  r_values.fill(false);
  for (const int edge_index : IndexRange(mesh.totedge)) {
    const MEdge &edge = mesh.medge[edge_index];
    if (old_values[edge_index]) {
      r_values[edge.v1] = true;
      r_values[edge.v2] = true;
    }
  }
}

static GVArray adapt_mesh_domain_edge_to_point(const Mesh &mesh, const GVArray &varray)
{
  GVArray new_varray;
  attribute_math::convert_to_static_type(varray.type(), [&](auto dummy) {
    using T = decltype(dummy);
    if constexpr (!std::is_void_v<attribute_math::DefaultMixer<T>>) {
      Array<T> values(mesh.totvert);
      adapt_mesh_domain_edge_to_point_impl<T>(mesh, varray.typed<T>(), values);
      new_varray = VArray<T>::ForContainer(std::move(values));
    }
  });
  return new_varray;
}

/**
 * \note Theoretically this interpolation does not need to compute all values at once.
 * However, doing that makes the implementation simpler, and this can be optimized in the future if
 * only some values are required.
 */
template<typename T>
static void adapt_mesh_domain_edge_to_face_impl(const Mesh &mesh,
                                                const VArray<T> &old_values,
                                                MutableSpan<T> r_values)
{
  BLI_assert(r_values.size() == mesh.totpoly);
  attribute_math::DefaultMixer<T> mixer(r_values);

  for (const int poly_index : IndexRange(mesh.totpoly)) {
    const MPoly &poly = mesh.mpoly[poly_index];
    for (const int loop_index : IndexRange(poly.loopstart, poly.totloop)) {
      const MLoop &loop = mesh.mloop[loop_index];
      mixer.mix_in(poly_index, old_values[loop.e]);
    }
  }

  mixer.finalize();
}

/* A face is selected if all of its edges are selected. */
template<>
void adapt_mesh_domain_edge_to_face_impl(const Mesh &mesh,
                                         const VArray<bool> &old_values,
                                         MutableSpan<bool> r_values)
{
  BLI_assert(r_values.size() == mesh.totpoly);

  r_values.fill(true);
  for (const int poly_index : IndexRange(mesh.totpoly)) {
    const MPoly &poly = mesh.mpoly[poly_index];
    for (const int loop_index : IndexRange(poly.loopstart, poly.totloop)) {
      const MLoop &loop = mesh.mloop[loop_index];
      const int edge_index = loop.e;
      if (!old_values[edge_index]) {
        r_values[poly_index] = false;
        break;
      }
    }
  }
}

static GVArray adapt_mesh_domain_edge_to_face(const Mesh &mesh, const GVArray &varray)
{
  GVArray new_varray;
  attribute_math::convert_to_static_type(varray.type(), [&](auto dummy) {
    using T = decltype(dummy);
    if constexpr (!std::is_void_v<attribute_math::DefaultMixer<T>>) {
      Array<T> values(mesh.totpoly);
      adapt_mesh_domain_edge_to_face_impl<T>(mesh, varray.typed<T>(), values);
      new_varray = VArray<T>::ForContainer(std::move(values));
    }
  });
  return new_varray;
}

}  // namespace blender::bke

blender::fn::GVArray MeshComponent::attribute_try_adapt_domain_impl(
    const blender::fn::GVArray &varray,
    const AttributeDomain from_domain,
    const AttributeDomain to_domain) const
{
  if (!varray) {
    return {};
  }
  if (varray.size() == 0) {
    return {};
  }
  if (from_domain == to_domain) {
    return varray;
  }

  switch (from_domain) {
    case ATTR_DOMAIN_CORNER: {
      switch (to_domain) {
        case ATTR_DOMAIN_POINT:
          return blender::bke::adapt_mesh_domain_corner_to_point(*mesh_, varray);
        case ATTR_DOMAIN_FACE:
          return blender::bke::adapt_mesh_domain_corner_to_face(*mesh_, varray);
        case ATTR_DOMAIN_EDGE:
          return blender::bke::adapt_mesh_domain_corner_to_edge(*mesh_, varray);
        default:
          break;
      }
      break;
    }
    case ATTR_DOMAIN_POINT: {
      switch (to_domain) {
        case ATTR_DOMAIN_CORNER:
          return blender::bke::adapt_mesh_domain_point_to_corner(*mesh_, varray);
        case ATTR_DOMAIN_FACE:
          return blender::bke::adapt_mesh_domain_point_to_face(*mesh_, varray);
        case ATTR_DOMAIN_EDGE:
          return blender::bke::adapt_mesh_domain_point_to_edge(*mesh_, varray);
        default:
          break;
      }
      break;
    }
    case ATTR_DOMAIN_FACE: {
      switch (to_domain) {
        case ATTR_DOMAIN_POINT:
          return blender::bke::adapt_mesh_domain_face_to_point(*mesh_, varray);
        case ATTR_DOMAIN_CORNER:
          return blender::bke::adapt_mesh_domain_face_to_corner(*mesh_, varray);
        case ATTR_DOMAIN_EDGE:
          return blender::bke::adapt_mesh_domain_face_to_edge(*mesh_, varray);
        default:
          break;
      }
      break;
    }
    case ATTR_DOMAIN_EDGE: {
      switch (to_domain) {
        case ATTR_DOMAIN_CORNER:
          return blender::bke::adapt_mesh_domain_edge_to_corner(*mesh_, varray);
        case ATTR_DOMAIN_POINT:
          return blender::bke::adapt_mesh_domain_edge_to_point(*mesh_, varray);
        case ATTR_DOMAIN_FACE:
          return blender::bke::adapt_mesh_domain_edge_to_face(*mesh_, varray);
        default:
          break;
      }
      break;
    }
    default:
      break;
  }

  return {};
}

static Mesh *get_mesh_from_component_for_write(GeometryComponent &component)
{
  BLI_assert(component.type() == GEO_COMPONENT_TYPE_MESH);
  MeshComponent &mesh_component = static_cast<MeshComponent &>(component);
  return mesh_component.get_for_write();
}

static const Mesh *get_mesh_from_component_for_read(const GeometryComponent &component)
{
  BLI_assert(component.type() == GEO_COMPONENT_TYPE_MESH);
  const MeshComponent &mesh_component = static_cast<const MeshComponent &>(component);
  return mesh_component.get_for_read();
}

namespace blender::bke {

template<typename StructT, typename ElemT, ElemT (*GetFunc)(const StructT &)>
static GVArray make_derived_read_attribute(const void *data, const int domain_size)
{
  return VArray<ElemT>::template ForDerivedSpan<StructT, GetFunc>(
      Span<StructT>((const StructT *)data, domain_size));
}

template<typename StructT,
         typename ElemT,
         ElemT (*GetFunc)(const StructT &),
         void (*SetFunc)(StructT &, ElemT)>
static GVMutableArray make_derived_write_attribute(void *data, const int domain_size)
{
  return VMutableArray<ElemT>::template ForDerivedSpan<StructT, GetFunc, SetFunc>(
      MutableSpan<StructT>((StructT *)data, domain_size));
}

template<typename T>
static GVArray make_array_read_attribute(const void *data, const int domain_size)
{
  return VArray<T>::ForSpan(Span<T>((const T *)data, domain_size));
}

template<typename T>
static GVMutableArray make_array_write_attribute(void *data, const int domain_size)
{
  return VMutableArray<T>::ForSpan(MutableSpan<T>((T *)data, domain_size));
}

static float3 get_vertex_position(const MVert &vert)
{
  return float3(vert.co);
}

static void set_vertex_position(MVert &vert, float3 position)
{
  copy_v3_v3(vert.co, position);
}

static void tag_normals_dirty_when_writing_position(GeometryComponent &component)
{
  Mesh *mesh = get_mesh_from_component_for_write(component);
  if (mesh != nullptr) {
    BKE_mesh_normals_tag_dirty(mesh);
  }
}

static int get_material_index(const MPoly &mpoly)
{
  return static_cast<int>(mpoly.mat_nr);
}

static void set_material_index(MPoly &mpoly, int index)
{
  mpoly.mat_nr = static_cast<short>(std::clamp(index, 0, SHRT_MAX));
}

static bool get_shade_smooth(const MPoly &mpoly)
{
  return mpoly.flag & ME_SMOOTH;
}

static void set_shade_smooth(MPoly &mpoly, bool value)
{
  SET_FLAG_FROM_TEST(mpoly.flag, value, ME_SMOOTH);
}

static float2 get_loop_uv(const MLoopUV &uv)
{
  return float2(uv.uv);
}

static void set_loop_uv(MLoopUV &uv, float2 co)
{
  copy_v2_v2(uv.uv, co);
}

static ColorGeometry4f get_loop_color(const MLoopCol &col)
{
  ColorGeometry4b encoded_color = ColorGeometry4b(col.r, col.g, col.b, col.a);
  ColorGeometry4f linear_color = encoded_color.decode();
  return linear_color;
}

static void set_loop_color(MLoopCol &col, ColorGeometry4f linear_color)
{
  ColorGeometry4b encoded_color = linear_color.encode();
  col.r = encoded_color.r;
  col.g = encoded_color.g;
  col.b = encoded_color.b;
  col.a = encoded_color.a;
}

static float get_crease(const MEdge &edge)
{
  return edge.crease / 255.0f;
}

static void set_crease(MEdge &edge, float value)
{
  edge.crease = round_fl_to_uchar_clamp(value * 255.0f);
}

class VArrayImpl_For_VertexWeights final : public VMutableArrayImpl<float> {
 private:
  MDeformVert *dverts_;
  const int dvert_index_;

 public:
  VArrayImpl_For_VertexWeights(MDeformVert *dverts, const int totvert, const int dvert_index)
      : VMutableArrayImpl<float>(totvert), dverts_(dverts), dvert_index_(dvert_index)
  {
  }

  float get(const int64_t index) const override
  {
    if (dverts_ == nullptr) {
      return 0.0f;
    }
    const MDeformVert &dvert = dverts_[index];
    for (const MDeformWeight &weight : Span(dvert.dw, dvert.totweight)) {
      if (weight.def_nr == dvert_index_) {
        return weight.weight;
      }
    }
    return 0.0f;
    ;
  }

  void set(const int64_t index, const float value) override
  {
    MDeformWeight *weight = BKE_defvert_ensure_index(&dverts_[index], dvert_index_);
    weight->weight = value;
  }
};

/**
 * This provider makes vertex groups available as float attributes.
 */
class VertexGroupsAttributeProvider final : public DynamicAttributesProvider {
 public:
  ReadAttributeLookup try_get_for_read(const GeometryComponent &component,
                                       const AttributeIDRef &attribute_id) const final
  {
    BLI_assert(component.type() == GEO_COMPONENT_TYPE_MESH);
    if (!attribute_id.is_named()) {
      return {};
    }
    const MeshComponent &mesh_component = static_cast<const MeshComponent &>(component);
    const Mesh *mesh = mesh_component.get_for_read();
    if (mesh == nullptr) {
      return {};
    }
    const std::string name = attribute_id.name();
    const int vertex_group_index = BLI_findstringindex(
        &mesh->vertex_group_names, name.c_str(), offsetof(bDeformGroup, name));
    if (vertex_group_index < 0) {
      return {};
    }
    if (mesh->dvert == nullptr) {
      static const float default_value = 0.0f;
      return {VArray<float>::ForSingle(default_value, mesh->totvert), ATTR_DOMAIN_POINT};
    }
    return {VArray<float>::For<VArrayImpl_For_VertexWeights>(
                mesh->dvert, mesh->totvert, vertex_group_index),
            ATTR_DOMAIN_POINT};
  }

  WriteAttributeLookup try_get_for_write(GeometryComponent &component,
                                         const AttributeIDRef &attribute_id) const final
  {
    BLI_assert(component.type() == GEO_COMPONENT_TYPE_MESH);
    if (!attribute_id.is_named()) {
      return {};
    }
    MeshComponent &mesh_component = static_cast<MeshComponent &>(component);
    Mesh *mesh = mesh_component.get_for_write();
    if (mesh == nullptr) {
      return {};
    }

    const std::string name = attribute_id.name();
    const int vertex_group_index = BLI_findstringindex(
        &mesh->vertex_group_names, name.c_str(), offsetof(bDeformGroup, name));
    if (vertex_group_index < 0) {
      return {};
    }
    if (mesh->dvert == nullptr) {
      BKE_object_defgroup_data_create(&mesh->id);
    }
    else {
      /* Copy the data layer if it is shared with some other mesh. */
      mesh->dvert = (MDeformVert *)CustomData_duplicate_referenced_layer(
          &mesh->vdata, CD_MDEFORMVERT, mesh->totvert);
    }
    return {VMutableArray<float>::For<VArrayImpl_For_VertexWeights>(
                mesh->dvert, mesh->totvert, vertex_group_index),
            ATTR_DOMAIN_POINT};
  }

  bool try_delete(GeometryComponent &component, const AttributeIDRef &attribute_id) const final
  {
    BLI_assert(component.type() == GEO_COMPONENT_TYPE_MESH);
    if (!attribute_id.is_named()) {
      return false;
    }
    MeshComponent &mesh_component = static_cast<MeshComponent &>(component);
    Mesh *mesh = mesh_component.get_for_write();
    if (mesh == nullptr) {
      return true;
    }

    const std::string name = attribute_id.name();

    int index;
    bDeformGroup *group;
    if (!BKE_id_defgroup_name_find(&mesh->id, name.c_str(), &index, &group)) {
      return false;
    }
    BLI_remlink(&mesh->vertex_group_names, group);
    MEM_freeN(group);
    if (mesh->dvert == nullptr) {
      return true;
    }
    for (MDeformVert &dvert : MutableSpan(mesh->dvert, mesh->totvert)) {
      MDeformWeight *weight = BKE_defvert_find_index(&dvert, index);
      BKE_defvert_remove_group(&dvert, weight);
    }
    return true;
  }

  bool foreach_attribute(const GeometryComponent &component,
                         const AttributeForeachCallback callback) const final
  {
    BLI_assert(component.type() == GEO_COMPONENT_TYPE_MESH);
    const MeshComponent &mesh_component = static_cast<const MeshComponent &>(component);
    const Mesh *mesh = mesh_component.get_for_read();
    if (mesh == nullptr) {
      return true;
    }

    LISTBASE_FOREACH (const bDeformGroup *, group, &mesh->vertex_group_names) {
      if (!callback(group->name, {ATTR_DOMAIN_POINT, CD_PROP_FLOAT})) {
        return false;
      }
    }
    return true;
  }

  void foreach_domain(const FunctionRef<void(AttributeDomain)> callback) const final
  {
    callback(ATTR_DOMAIN_POINT);
  }
};

/**
 * This provider makes face normals available as a read-only float3 attribute.
 */
class NormalAttributeProvider final : public BuiltinAttributeProvider {
 public:
  NormalAttributeProvider()
      : BuiltinAttributeProvider(
            "normal", ATTR_DOMAIN_FACE, CD_PROP_FLOAT3, NonCreatable, Readonly, NonDeletable)
  {
  }

  GVArray try_get_for_read(const GeometryComponent &component) const final
  {
    const MeshComponent &mesh_component = static_cast<const MeshComponent &>(component);
    const Mesh *mesh = mesh_component.get_for_read();
    if (mesh == nullptr) {
      return {};
    }

    /* Use existing normals if possible. */
    if (!(mesh->runtime.cd_dirty_poly & CD_MASK_NORMAL) &&
        CustomData_has_layer(&mesh->pdata, CD_NORMAL)) {
      const void *data = CustomData_get_layer(&mesh->pdata, CD_NORMAL);

      return VArray<float3>::ForSpan(Span<float3>((const float3 *)data, mesh->totpoly));
    }

    Array<float3> normals(mesh->totpoly);
    for (const int i : IndexRange(mesh->totpoly)) {
      const MPoly *poly = &mesh->mpoly[i];
      BKE_mesh_calc_poly_normal(poly, &mesh->mloop[poly->loopstart], mesh->mvert, normals[i]);
    }

    return VArray<float3>::ForContainer(std::move(normals));
  }

  WriteAttributeLookup try_get_for_write(GeometryComponent &UNUSED(component)) const final
  {
    return {};
  }

  bool try_delete(GeometryComponent &UNUSED(component)) const final
  {
    return false;
  }

  bool try_create(GeometryComponent &UNUSED(component),
                  const AttributeInit &UNUSED(initializer)) const final
  {
    return false;
  }

  bool exists(const GeometryComponent &component) const final
  {
    return component.attribute_domain_size(ATTR_DOMAIN_FACE) != 0;
  }
};

/**
 * In this function all the attribute providers for a mesh component are created. Most data in this
 * function is statically allocated, because it does not change over time.
 */
static ComponentAttributeProviders create_attribute_providers_for_mesh()
{
  static auto update_custom_data_pointers = [](GeometryComponent &component) {
    Mesh *mesh = get_mesh_from_component_for_write(component);
    if (mesh != nullptr) {
      BKE_mesh_update_customdata_pointers(mesh, false);
    }
  };

#define MAKE_MUTABLE_CUSTOM_DATA_GETTER(NAME) \
  [](GeometryComponent &component) -> CustomData * { \
    Mesh *mesh = get_mesh_from_component_for_write(component); \
    return mesh ? &mesh->NAME : nullptr; \
  }
#define MAKE_CONST_CUSTOM_DATA_GETTER(NAME) \
  [](const GeometryComponent &component) -> const CustomData * { \
    const Mesh *mesh = get_mesh_from_component_for_read(component); \
    return mesh ? &mesh->NAME : nullptr; \
  }

  static CustomDataAccessInfo corner_access = {MAKE_MUTABLE_CUSTOM_DATA_GETTER(ldata),
                                               MAKE_CONST_CUSTOM_DATA_GETTER(ldata),
                                               update_custom_data_pointers};
  static CustomDataAccessInfo point_access = {MAKE_MUTABLE_CUSTOM_DATA_GETTER(vdata),
                                              MAKE_CONST_CUSTOM_DATA_GETTER(vdata),
                                              update_custom_data_pointers};
  static CustomDataAccessInfo edge_access = {MAKE_MUTABLE_CUSTOM_DATA_GETTER(edata),
                                             MAKE_CONST_CUSTOM_DATA_GETTER(edata),
                                             update_custom_data_pointers};
  static CustomDataAccessInfo face_access = {MAKE_MUTABLE_CUSTOM_DATA_GETTER(pdata),
                                             MAKE_CONST_CUSTOM_DATA_GETTER(pdata),
                                             update_custom_data_pointers};

#undef MAKE_CONST_CUSTOM_DATA_GETTER
#undef MAKE_MUTABLE_CUSTOM_DATA_GETTER

  static BuiltinCustomDataLayerProvider position(
      "position",
      ATTR_DOMAIN_POINT,
      CD_PROP_FLOAT3,
      CD_MVERT,
      BuiltinAttributeProvider::NonCreatable,
      BuiltinAttributeProvider::Writable,
      BuiltinAttributeProvider::NonDeletable,
      point_access,
      make_derived_read_attribute<MVert, float3, get_vertex_position>,
      make_derived_write_attribute<MVert, float3, get_vertex_position, set_vertex_position>,
      tag_normals_dirty_when_writing_position);

  static NormalAttributeProvider normal;

  static BuiltinCustomDataLayerProvider id("id",
                                           ATTR_DOMAIN_POINT,
                                           CD_PROP_INT32,
                                           CD_PROP_INT32,
                                           BuiltinAttributeProvider::Creatable,
                                           BuiltinAttributeProvider::Writable,
                                           BuiltinAttributeProvider::Deletable,
                                           point_access,
                                           make_array_read_attribute<int>,
                                           make_array_write_attribute<int>,
                                           nullptr);

  static BuiltinCustomDataLayerProvider material_index(
      "material_index",
      ATTR_DOMAIN_FACE,
      CD_PROP_INT32,
      CD_MPOLY,
      BuiltinAttributeProvider::NonCreatable,
      BuiltinAttributeProvider::Writable,
      BuiltinAttributeProvider::NonDeletable,
      face_access,
      make_derived_read_attribute<MPoly, int, get_material_index>,
      make_derived_write_attribute<MPoly, int, get_material_index, set_material_index>,
      nullptr);

  static BuiltinCustomDataLayerProvider shade_smooth(
      "shade_smooth",
      ATTR_DOMAIN_FACE,
      CD_PROP_BOOL,
      CD_MPOLY,
      BuiltinAttributeProvider::NonCreatable,
      BuiltinAttributeProvider::Writable,
      BuiltinAttributeProvider::NonDeletable,
      face_access,
      make_derived_read_attribute<MPoly, bool, get_shade_smooth>,
      make_derived_write_attribute<MPoly, bool, get_shade_smooth, set_shade_smooth>,
      nullptr);

  static BuiltinCustomDataLayerProvider crease(
      "crease",
      ATTR_DOMAIN_EDGE,
      CD_PROP_FLOAT,
      CD_MEDGE,
      BuiltinAttributeProvider::NonCreatable,
      BuiltinAttributeProvider::Writable,
      BuiltinAttributeProvider::NonDeletable,
      edge_access,
      make_derived_read_attribute<MEdge, float, get_crease>,
      make_derived_write_attribute<MEdge, float, get_crease, set_crease>,
      nullptr);

  static NamedLegacyCustomDataProvider uvs(
      ATTR_DOMAIN_CORNER,
      CD_PROP_FLOAT2,
      CD_MLOOPUV,
      corner_access,
      make_derived_read_attribute<MLoopUV, float2, get_loop_uv>,
      make_derived_write_attribute<MLoopUV, float2, get_loop_uv, set_loop_uv>);

  static NamedLegacyCustomDataProvider vertex_colors(
      ATTR_DOMAIN_CORNER,
      CD_PROP_COLOR,
      CD_MLOOPCOL,
      corner_access,
      make_derived_read_attribute<MLoopCol, ColorGeometry4f, get_loop_color>,
      make_derived_write_attribute<MLoopCol, ColorGeometry4f, get_loop_color, set_loop_color>);

  static VertexGroupsAttributeProvider vertex_groups;
  static CustomDataAttributeProvider corner_custom_data(ATTR_DOMAIN_CORNER, corner_access);
  static CustomDataAttributeProvider point_custom_data(ATTR_DOMAIN_POINT, point_access);
  static CustomDataAttributeProvider edge_custom_data(ATTR_DOMAIN_EDGE, edge_access);
  static CustomDataAttributeProvider face_custom_data(ATTR_DOMAIN_FACE, face_access);

  return ComponentAttributeProviders(
      {&position, &id, &material_index, &shade_smooth, &normal, &crease},
      {&uvs,
       &vertex_colors,
       &corner_custom_data,
       &vertex_groups,
       &point_custom_data,
       &edge_custom_data,
       &face_custom_data});
}

}  // namespace blender::bke

const blender::bke::ComponentAttributeProviders *MeshComponent::get_attribute_providers() const
{
  static blender::bke::ComponentAttributeProviders providers =
      blender::bke::create_attribute_providers_for_mesh();
  return &providers;
}

/** \} */
