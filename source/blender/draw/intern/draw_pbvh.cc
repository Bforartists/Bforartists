/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 *
 * bke::pbvh::Tree drawing.
 * Embeds GPU meshes inside of bke::pbvh::Tree nodes, used by mesh sculpt mode.
 */

#include "BLI_map.hh"
#include "BLI_math_vector_types.hh"
#include "BLI_utildefines.h"
#include "BLI_vector.hh"

#include "DNA_object_types.h"

#include "BKE_attribute.hh"
#include "BKE_attribute_math.hh"
#include "BKE_customdata.hh"
#include "BKE_mesh.hh"
#include "BKE_paint.hh"
#include "BKE_pbvh_api.hh"
#include "BKE_subdiv_ccg.hh"

#include "DEG_depsgraph_query.hh"

#include "GPU_batch.hh"

#include "DRW_engine.hh"
#include "DRW_pbvh.hh"

#include "attribute_convert.hh"
#include "bmesh.hh"

namespace blender {

template<> struct DefaultHash<draw::pbvh::AttributeRequest> {
  uint64_t operator()(const draw::pbvh::AttributeRequest &value) const
  {
    using namespace draw::pbvh;
    if (const CustomRequest *request_type = std::get_if<CustomRequest>(&value)) {
      return get_default_hash(*request_type);
    }
    const GenericRequest &attr = std::get<GenericRequest>(value);
    return get_default_hash(attr.name);
  }
};

}  // namespace blender

namespace blender::draw::pbvh {

uint64_t ViewportRequest::hash() const
{
  return get_default_hash(attributes, use_coarse_grids);
}

/**
 * Because many sculpt mode operations skip tagging dependency graph for reevaluation for
 * performance reasons, the relevant data must be retrieved directly from the original mesh rather
 * than the evaluated copy.
 */
struct OrigMeshData {
  StringRef active_color;
  StringRef default_color;
  StringRef active_uv_map;
  StringRef default_uv_map;
  int face_set_default;
  int face_set_seed;
  bke::AttributeAccessor attributes;
  OrigMeshData(const Mesh &mesh)
      : active_color(mesh.active_color_attribute),
        default_color(mesh.default_color_attribute),
        active_uv_map(CustomData_get_active_layer_name(&mesh.corner_data, CD_PROP_FLOAT2)),
        default_uv_map(CustomData_get_render_layer_name(&mesh.corner_data, CD_PROP_FLOAT2)),
        face_set_default(mesh.face_sets_color_default),
        face_set_seed(mesh.face_sets_color_seed),
        attributes(mesh.attributes())
  {
  }
};

/**
 * Stores the data necessary to draw the PBVH geometry. A separate `*Impl` class is used to hide
 * implementation details from the public header.
 */
class DrawCacheImpl : public DrawCache {
  struct AttributeData {
    /** A vertex buffer for each BVH node. If null, the draw data for the node must be created. */
    Vector<gpu::VertBuf *> vbos;
    /**
     * A separate "dirty" bit per node. We track the dirty value separately from deleting the VBO
     * for a node in order to avoid recreating batches with new VBOs. It's also a necessary
     * addition to the flags stored in the PBVH which are cleared after it's used for drawing
     * (those aren't sufficient when multiple viewports are drawing with the same PBVH but request
     * different sets of attributes).
     */
    BitVector<> dirty_nodes;
    /**
     * Mark attribute values dirty for specific nodes. The next time the attribute is requested,
     * the values will be extracted again.
     */
    void tag_dirty(const IndexMask &node_mask);
  };

  /** Used to determine whether to use indexed VBO layouts for multires grids. */
  BitVector<> use_flat_layout_;
  /** The material index for each node. */
  Array<int> material_indices_;

  /** Index buffers for wireframe geometry for each node. */
  Vector<gpu::IndexBuf *> lines_ibos_;
  /** Index buffers for coarse "fast navigate" wireframe geometry for each node. */
  Vector<gpu::IndexBuf *> lines_ibos_coarse_;
  /** Index buffers for triangles for each node, only used for grids. */
  Vector<gpu::IndexBuf *> tris_ibos_;
  /** Index buffers for coarse "fast navigate" triangles for each node, only used for grids. */
  Vector<gpu::IndexBuf *> tris_ibos_coarse_;
  /**
   * GPU data and per-node dirty status for all requested attributes.
   * \note Currently we do not remove "stale" attributes that haven't been requested in a while.
   */
  Map<AttributeRequest, AttributeData> attribute_vbos_;

  /** Batches for drawing wireframe geometry. */
  Vector<gpu::Batch *> lines_batches_;
  /** Batches for drawing coarse "fast navigate" wireframe geometry. */
  Vector<gpu::Batch *> lines_batches_coarse_;
  /**
   * Batches for drawing triangles, stored separately for each combination of attributes and
   * coarse-ness. Different viewports might request different sets of attributes, and we don't want
   * to recreate the batches on every redraw.
   */
  Map<ViewportRequest, Vector<gpu::Batch *>> tris_batches_;

 public:
  virtual ~DrawCacheImpl() override;

  void tag_all_attributes_dirty(const IndexMask &node_mask) override;

  Span<gpu::Batch *> ensure_tris_batches(const Object &object,
                                         const ViewportRequest &request,
                                         const IndexMask &nodes_to_update) override;

  Span<gpu::Batch *> ensure_lines_batches(const Object &object,
                                          const ViewportRequest &request,
                                          const IndexMask &nodes_to_update) override;

  Span<int> ensure_material_indices(const Object &object) override;

 private:
  /**
   * Free all GPU data for nodes with a changed visible triangle count. The next time the data is
   * requested it will be rebuilt.
   */
  void free_nodes_with_changed_topology(const Object &object, const IndexMask &node_mask);

  BitSpan ensure_use_flat_layout(const Object &object, const OrigMeshData &orig_mesh_data);

  Span<gpu::VertBuf *> ensure_attribute_data(const Object &object,
                                             const OrigMeshData &orig_mesh_data,
                                             const AttributeRequest &attr,
                                             const IndexMask &node_mask);

  Span<gpu::IndexBuf *> ensure_tri_indices(const Object &object,
                                           const OrigMeshData &orig_mesh_data,
                                           const IndexMask &node_mask,
                                           bool coarse);

  Span<gpu::IndexBuf *> ensure_lines_indices(const Object &object,
                                             const OrigMeshData &orig_mesh_data,
                                             const IndexMask &node_mask,
                                             bool coarse);
};

void DrawCacheImpl::AttributeData::tag_dirty(const IndexMask &node_mask)
{
  const int mask_size = node_mask.min_array_size();
  if (this->dirty_nodes.size() < mask_size) {
    this->dirty_nodes.resize(mask_size);
  }
  /* TODO: Somehow use IndexMask::from_bits with the `reset_all` at the beginning disabled. */
  node_mask.foreach_index_optimized<int>(GrainSize(4096),
                                         [&](const int i) { this->dirty_nodes[i].set(); });
}

void DrawCacheImpl::tag_all_attributes_dirty(const IndexMask &node_mask)
{
  for (DrawCacheImpl::AttributeData &data : attribute_vbos_.values()) {
    data.tag_dirty(node_mask);
  }
}

DrawCache &ensure_draw_data(std::unique_ptr<bke::pbvh::DrawCache> &ptr)
{
  if (!ptr) {
    ptr = std::make_unique<DrawCacheImpl>();
  }
  return dynamic_cast<DrawCache &>(*ptr);
}

BLI_NOINLINE static void free_ibos(const MutableSpan<gpu::IndexBuf *> ibos,
                                   const IndexMask &node_mask)
{
  IndexMaskMemory memory;
  const IndexMask mask = IndexMask::from_intersection(node_mask, ibos.index_range(), memory);
  mask.foreach_index([&](const int i) { GPU_INDEXBUF_DISCARD_SAFE(ibos[i]); });
}

BLI_NOINLINE static void free_vbos(const MutableSpan<gpu::VertBuf *> vbos,
                                   const IndexMask &node_mask)
{
  IndexMaskMemory memory;
  const IndexMask mask = IndexMask::from_intersection(node_mask, vbos.index_range(), memory);
  mask.foreach_index([&](const int i) { GPU_VERTBUF_DISCARD_SAFE(vbos[i]); });
}

BLI_NOINLINE static void free_batches(const MutableSpan<gpu::Batch *> batches,
                                      const IndexMask &node_mask)
{
  IndexMaskMemory memory;
  const IndexMask mask = IndexMask::from_intersection(node_mask, batches.index_range(), memory);
  mask.foreach_index([&](const int i) { GPU_BATCH_DISCARD_SAFE(batches[i]); });
}

static const GPUVertFormat &position_format()
{
  static GPUVertFormat format{};
  if (format.attr_len == 0) {
    GPU_vertformat_attr_add(&format, "pos", GPU_COMP_F32, 3, GPU_FETCH_FLOAT);
  }
  return format;
}

static const GPUVertFormat &normal_format()
{
  static GPUVertFormat format{};
  if (format.attr_len == 0) {
    GPU_vertformat_attr_add(&format, "nor", GPU_COMP_I16, 3, GPU_FETCH_INT_TO_FLOAT_UNIT);
  }
  return format;
}

static const GPUVertFormat &mask_format()
{
  static GPUVertFormat format{};
  if (format.attr_len == 0) {
    GPU_vertformat_attr_add(&format, "msk", GPU_COMP_F32, 1, GPU_FETCH_FLOAT);
  }
  return format;
}

static const GPUVertFormat &face_set_format()
{
  static GPUVertFormat format{};
  if (format.attr_len == 0) {
    GPU_vertformat_attr_add(&format, "fset", GPU_COMP_U8, 3, GPU_FETCH_INT_TO_FLOAT_UNIT);
  }
  return format;
}

static GPUVertFormat attribute_format(const OrigMeshData &orig_mesh_data,
                                      const StringRefNull name,
                                      const eCustomDataType data_type)
{
  GPUVertFormat format = draw::init_format_for_attribute(data_type, "data");

  bool is_render, is_active;
  const char *prefix = "a";

  if (CD_TYPE_AS_MASK(data_type) & CD_MASK_COLOR_ALL) {
    prefix = "c";
    is_active = orig_mesh_data.active_color == name;
    is_render = orig_mesh_data.default_color == name;
  }
  if (data_type == CD_PROP_FLOAT2) {
    prefix = "u";
    is_active = orig_mesh_data.active_uv_map == name;
    is_render = orig_mesh_data.default_uv_map == name;
  }

  DRW_cdlayer_attr_aliases_add(&format, prefix, data_type, name.c_str(), is_render, is_active);
  return format;
}

static GPUVertFormat format_for_request(const OrigMeshData &orig_mesh_data,
                                        const AttributeRequest &request)
{
  if (const CustomRequest *request_type = std::get_if<CustomRequest>(&request)) {
    switch (*request_type) {
      case CustomRequest::Position:
        return position_format();
      case CustomRequest::Normal:
        return normal_format();
      case CustomRequest::Mask:
        return mask_format();
      case CustomRequest::FaceSet:
        return face_set_format();
    }
  }
  else {
    const GenericRequest &attr = std::get<GenericRequest>(request);
    return attribute_format(orig_mesh_data, attr.name, attr.type);
  }
  BLI_assert_unreachable();
  return {};
}

static bool pbvh_attr_supported(const AttributeRequest &request)
{
  if (std::holds_alternative<CustomRequest>(request)) {
    return true;
  }
  const GenericRequest &attr = std::get<GenericRequest>(request);
  if (!ELEM(attr.domain, bke::AttrDomain::Point, bke::AttrDomain::Face, bke::AttrDomain::Corner)) {
    /* blender::bke::pbvh::Tree drawing does not support edge domain attributes. */
    return false;
  }
  bool type_supported = false;
  bke::attribute_math::convert_to_static_type(attr.type, [&](auto dummy) {
    using T = decltype(dummy);
    using Converter = AttributeConverter<T>;
    using VBOType = typename Converter::VBOType;
    if constexpr (!std::is_void_v<VBOType>) {
      type_supported = true;
    }
  });
  return type_supported;
}

inline short4 normal_float_to_short(const float3 &value)
{
  short3 result;
  normal_float_to_short_v3(result, value);
  return short4(result.x, result.y, result.z, 0);
}

template<typename T>
void extract_data_vert_mesh(const OffsetIndices<int> faces,
                            const Span<int> corner_verts,
                            const Span<T> attribute,
                            const Span<int> face_indices,
                            gpu::VertBuf &vbo)
{
  using Converter = AttributeConverter<T>;
  using VBOType = typename Converter::VBOType;
  VBOType *data = vbo.data<VBOType>().data();
  for (const int face : face_indices) {
    for (const int vert : corner_verts.slice(faces[face])) {
      *data = Converter::convert(attribute[vert]);
      data++;
    }
  }
}

template<typename T>
void extract_data_face_mesh(const OffsetIndices<int> faces,
                            const Span<T> attribute,
                            const Span<int> face_indices,
                            gpu::VertBuf &vbo)
{
  using Converter = AttributeConverter<T>;
  using VBOType = typename Converter::VBOType;

  VBOType *data = vbo.data<VBOType>().data();
  for (const int face : face_indices) {
    const int face_size = faces[face].size();
    std::fill_n(data, face_size, Converter::convert(attribute[face]));
    data += face_size;
  }
}

template<typename T>
void extract_data_corner_mesh(const OffsetIndices<int> faces,
                              const Span<T> attribute,
                              const Span<int> face_indices,
                              gpu::VertBuf &vbo)
{
  using Converter = AttributeConverter<T>;
  using VBOType = typename Converter::VBOType;

  VBOType *data = vbo.data<VBOType>().data();
  for (const int face : face_indices) {
    for (const int corner : faces[face]) {
      *data = Converter::convert(attribute[corner]);
      data++;
    }
  }
}

template<typename T> const T &bmesh_cd_vert_get(const BMVert &vert, const int offset)
{
  return *static_cast<const T *>(POINTER_OFFSET(vert.head.data, offset));
}

template<typename T> const T &bmesh_cd_loop_get(const BMLoop &loop, const int offset)
{
  return *static_cast<const T *>(POINTER_OFFSET(loop.head.data, offset));
}

template<typename T> const T &bmesh_cd_face_get(const BMFace &face, const int offset)
{
  return *static_cast<const T *>(POINTER_OFFSET(face.head.data, offset));
}

template<typename T>
void extract_data_vert_bmesh(const Set<BMFace *, 0> &faces, const int cd_offset, gpu::VertBuf &vbo)
{
  using Converter = AttributeConverter<T>;
  using VBOType = typename Converter::VBOType;
  VBOType *data = vbo.data<VBOType>().data();

  for (const BMFace *face : faces) {
    if (BM_elem_flag_test(face, BM_ELEM_HIDDEN)) {
      continue;
    }
    const BMLoop *l = face->l_first;
    *data = Converter::convert(bmesh_cd_vert_get<T>(*l->prev->v, cd_offset));
    data++;
    *data = Converter::convert(bmesh_cd_vert_get<T>(*l->v, cd_offset));
    data++;
    *data = Converter::convert(bmesh_cd_vert_get<T>(*l->next->v, cd_offset));
    data++;
  }
}

template<typename T>
void extract_data_face_bmesh(const Set<BMFace *, 0> &faces, const int cd_offset, gpu::VertBuf &vbo)
{
  using Converter = AttributeConverter<T>;
  using VBOType = typename Converter::VBOType;
  VBOType *data = vbo.data<VBOType>().data();

  for (const BMFace *face : faces) {
    if (BM_elem_flag_test(face, BM_ELEM_HIDDEN)) {
      continue;
    }
    std::fill_n(data, 3, Converter::convert(bmesh_cd_face_get<T>(*face, cd_offset)));
    data += 3;
  }
}

template<typename T>
void extract_data_corner_bmesh(const Set<BMFace *, 0> &faces,
                               const int cd_offset,
                               gpu::VertBuf &vbo)
{
  using Converter = AttributeConverter<T>;
  using VBOType = typename Converter::VBOType;
  VBOType *data = vbo.data<VBOType>().data();

  for (const BMFace *face : faces) {
    if (BM_elem_flag_test(face, BM_ELEM_HIDDEN)) {
      continue;
    }
    const BMLoop *l = face->l_first;
    *data = Converter::convert(bmesh_cd_loop_get<T>(*l->prev, cd_offset));
    data++;
    *data = Converter::convert(bmesh_cd_loop_get<T>(*l, cd_offset));
    data++;
    *data = Converter::convert(bmesh_cd_loop_get<T>(*l->next, cd_offset));
    data++;
  }
}

static const CustomData *get_cdata(const BMesh &bm, const bke::AttrDomain domain)
{
  switch (domain) {
    case bke::AttrDomain::Point:
      return &bm.vdata;
    case bke::AttrDomain::Corner:
      return &bm.ldata;
    case bke::AttrDomain::Face:
      return &bm.pdata;
    default:
      return nullptr;
  }
}

template<typename T> T fallback_value_for_fill()
{
  return T();
}

template<> ColorGeometry4f fallback_value_for_fill()
{
  return ColorGeometry4f(1.0f, 1.0f, 1.0f, 1.0f);
}

template<> ColorGeometry4b fallback_value_for_fill()
{
  return fallback_value_for_fill<ColorGeometry4f>().encode();
}

static int count_visible_tris_mesh(const OffsetIndices<int> faces,
                                   const Span<int> face_indices,
                                   const Span<bool> hide_poly)
{
  int tris_count = 0;
  for (const int face : face_indices) {
    if (!hide_poly.is_empty() && hide_poly[face]) {
      continue;
    }
    tris_count += bke::mesh::face_triangles_num(faces[face].size());
  }
  return tris_count;
}

static int count_visible_tris_bmesh(const Set<BMFace *, 0> &faces)
{
  return std::count_if(faces.begin(), faces.end(), [&](const BMFace *face) {
    return !BM_elem_flag_test_bool(face, BM_ELEM_HIDDEN);
  });
}

/**
 * Find nodes which (might) have a different number of visible faces.
 *
 * \note Theoretically the #PBVH_RebuildDrawBuffers flag is redundant with checking for a different
 * number of visible triangles in the PBVH node on every redraw. We could do that too, but it's
 * simpler overall to just tag the node whenever there is such a topology change, and for now there
 * is no real downside.
 */
static IndexMask calc_topology_changed_nodes(const Object &object,
                                             const IndexMask &node_mask,
                                             IndexMaskMemory &memory)
{
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  switch (pbvh.type()) {
    case bke::pbvh::Type::Mesh: {
      const Span<bke::pbvh::MeshNode> nodes = pbvh.nodes<bke::pbvh::MeshNode>();
      return IndexMask::from_predicate(node_mask, GrainSize(1024), memory, [&](const int i) {
        return nodes[i].flag_ & PBVH_RebuildDrawBuffers;
      });
    }
    case bke::pbvh::Type::Grids: {
      const Span<bke::pbvh::GridsNode> nodes = pbvh.nodes<bke::pbvh::GridsNode>();
      return IndexMask::from_predicate(node_mask, GrainSize(1024), memory, [&](const int i) {
        return nodes[i].flag_ & PBVH_RebuildDrawBuffers;
      });
    }
    case bke::pbvh::Type::BMesh: {
      const Span<bke::pbvh::BMeshNode> nodes = pbvh.nodes<bke::pbvh::BMeshNode>();
      return IndexMask::from_predicate(node_mask, GrainSize(1024), memory, [&](const int i) {
        return nodes[i].flag_ & PBVH_RebuildDrawBuffers;
      });
    }
  }
  BLI_assert_unreachable();
  return {};
}

DrawCacheImpl::~DrawCacheImpl()
{
  /* This destructor should support inconsistent vector lengths between attributes and index
   * buffers. That's why the implementation isn't shared with #free_nodes_with_changed_topology.
   * Also the gpu buffers and batches should just use RAII anyway. */
  free_ibos(lines_ibos_, lines_ibos_.index_range());
  free_ibos(lines_ibos_coarse_, lines_ibos_coarse_.index_range());
  free_ibos(tris_ibos_, tris_ibos_.index_range());
  free_ibos(tris_ibos_coarse_, tris_ibos_coarse_.index_range());
  for (DrawCacheImpl::AttributeData &data : attribute_vbos_.values()) {
    free_vbos(data.vbos, data.vbos.index_range());
  }

  free_batches(lines_batches_, lines_batches_.index_range());
  free_batches(lines_batches_coarse_, lines_batches_coarse_.index_range());
  for (MutableSpan<gpu::Batch *> batches : tris_batches_.values()) {
    free_batches(batches, batches.index_range());
  }
}

void DrawCacheImpl::free_nodes_with_changed_topology(const Object &object,
                                                     const IndexMask &node_mask)
{
  /* NOTE: Theoretically we shouldn't need to free batches with a changed triangle count, but
   * currently it's the simplest way to reallocate all the GPU data while keeping everything in a
   * consistent state. */
  IndexMaskMemory memory;
  const IndexMask nodes_to_free = calc_topology_changed_nodes(object, node_mask, memory);

  free_ibos(lines_ibos_, nodes_to_free);
  free_ibos(lines_ibos_coarse_, nodes_to_free);
  free_ibos(tris_ibos_, nodes_to_free);
  free_ibos(tris_ibos_coarse_, nodes_to_free);
  /* TODO: No need to free VBOs visibility changes because of indexing (except for BMesh). */
  for (AttributeData &data : attribute_vbos_.values()) {
    free_vbos(data.vbos, nodes_to_free);
  }

  free_batches(lines_batches_, nodes_to_free);
  free_batches(lines_batches_coarse_, nodes_to_free);
  for (MutableSpan<gpu::Batch *> batches : tris_batches_.values()) {
    free_batches(batches, nodes_to_free);
  }
}

static void fill_vbo_normal_mesh(const OffsetIndices<int> faces,
                                 const Span<int> corner_verts,
                                 const Span<bool> sharp_faces,
                                 const Span<float3> vert_normals,
                                 const Span<float3> face_normals,
                                 const Span<int> face_indices,
                                 gpu::VertBuf &vert_buf)
{
  short4 *data = vert_buf.data<short4>().data();

  for (const int face : face_indices) {
    if (!sharp_faces.is_empty() && sharp_faces[face]) {
      const int face_size = faces[face].size();
      std::fill_n(data, face_size, normal_float_to_short(face_normals[face]));
      data += face_size;
    }
    else {
      for (const int vert : corner_verts.slice(faces[face])) {
        *data = normal_float_to_short(vert_normals[vert]);
        data++;
      }
    }
  }
}

static void fill_vbo_mask_mesh(const OffsetIndices<int> faces,
                               const Span<int> corner_verts,
                               const Span<float> mask,
                               const Span<int> face_indices,
                               gpu::VertBuf &vbo)
{
  float *data = vbo.data<float>().data();
  for (const int face : face_indices) {
    for (const int vert : corner_verts.slice(faces[face])) {
      *data = mask[vert];
      data++;
    }
  }
}

static void fill_vbo_face_set_mesh(const OffsetIndices<int> faces,
                                   const Span<int> face_sets,
                                   const int color_default,
                                   const int color_seed,
                                   const Span<int> face_indices,
                                   gpu::VertBuf &vert_buf)
{
  uchar4 *data = vert_buf.data<uchar4>().data();
  for (const int face : face_indices) {
    const int id = face_sets[face];

    uchar4 fset_color(UCHAR_MAX);
    if (id != color_default) {
      BKE_paint_face_set_overlay_color_get(id, color_seed, fset_color);
    }
    else {
      /* Skip for the default color face set to render it white. */
      fset_color[0] = fset_color[1] = fset_color[2] = UCHAR_MAX;
    }

    const int face_size = faces[face].size();
    std::fill_n(data, face_size, fset_color);
    data += face_size;
  }
}

static void fill_vbo_attribute_mesh(const OffsetIndices<int> faces,
                                    const Span<int> corner_verts,
                                    const GSpan attribute,
                                    const bke::AttrDomain domain,
                                    const Span<int> face_indices,
                                    gpu::VertBuf &vert_buf)
{
  bke::attribute_math::convert_to_static_type(attribute.type(), [&](auto dummy) {
    using T = decltype(dummy);
    if constexpr (!std::is_void_v<typename AttributeConverter<T>::VBOType>) {
      const Span<T> src = attribute.typed<T>();
      switch (domain) {
        case bke::AttrDomain::Point:
          extract_data_vert_mesh<T>(faces, corner_verts, src, face_indices, vert_buf);
          break;
        case bke::AttrDomain::Face:
          extract_data_face_mesh<T>(faces, src, face_indices, vert_buf);
          break;
        case bke::AttrDomain::Corner:
          extract_data_corner_mesh<T>(faces, src, face_indices, vert_buf);
          break;
        default:
          BLI_assert_unreachable();
      }
    }
  });
}

static void fill_vbo_position_grids(const CCGKey &key,
                                    const Span<CCGElem *> grids,
                                    const bool use_flat_layout,
                                    const Span<int> grid_indices,
                                    gpu::VertBuf &vert_buf)
{
  float3 *data = vert_buf.data<float3>().data();
  if (use_flat_layout) {
    const int grid_size_1 = key.grid_size - 1;
    for (const int i : grid_indices.index_range()) {
      CCGElem *grid = grids[grid_indices[i]];
      for (int y = 0; y < grid_size_1; y++) {
        for (int x = 0; x < grid_size_1; x++) {
          *data = CCG_grid_elem_co(key, grid, x, y);
          data++;
          *data = CCG_grid_elem_co(key, grid, x + 1, y);
          data++;
          *data = CCG_grid_elem_co(key, grid, x + 1, y + 1);
          data++;
          *data = CCG_grid_elem_co(key, grid, x, y + 1);
          data++;
        }
      }
    }
  }
  else {
    for (const int i : grid_indices.index_range()) {
      CCGElem *grid = grids[grid_indices[i]];
      for (const int offset : IndexRange(key.grid_area)) {
        *data = CCG_elem_offset_co(key, grid, offset);
        data++;
      }
    }
  }
}

static void fill_vbo_normal_grids(const CCGKey &key,
                                  const Span<CCGElem *> grids,
                                  const Span<int> grid_to_face_map,
                                  const Span<bool> sharp_faces,
                                  const bool use_flat_layout,
                                  const Span<int> grid_indices,
                                  gpu::VertBuf &vert_buf)
{
  short4 *data = vert_buf.data<short4>().data();

  if (use_flat_layout) {
    const int grid_size_1 = key.grid_size - 1;
    for (const int i : grid_indices.index_range()) {
      const int grid_index = grid_indices[i];
      CCGElem *grid = grids[grid_index];
      if (!sharp_faces.is_empty() && sharp_faces[grid_to_face_map[grid_index]]) {
        for (int y = 0; y < grid_size_1; y++) {
          for (int x = 0; x < grid_size_1; x++) {
            float3 no;
            normal_quad_v3(no,
                           CCG_grid_elem_co(key, grid, x, y + 1),
                           CCG_grid_elem_co(key, grid, x + 1, y + 1),
                           CCG_grid_elem_co(key, grid, x + 1, y),
                           CCG_grid_elem_co(key, grid, x, y));
            std::fill_n(data, 4, normal_float_to_short(no));
            data += 4;
          }
        }
      }
      else {
        for (int y = 0; y < grid_size_1; y++) {
          for (int x = 0; x < grid_size_1; x++) {
            std::fill_n(data, 4, normal_float_to_short(CCG_grid_elem_no(key, grid, x, y)));
            data += 4;
          }
        }
      }
    }
  }
  else {
    /* The non-flat VBO layout does not support sharp faces. */
    for (const int i : grid_indices.index_range()) {
      CCGElem *grid = grids[grid_indices[i]];
      for (const int offset : IndexRange(key.grid_area)) {
        *data = normal_float_to_short(CCG_elem_offset_no(key, grid, offset));
        data++;
      }
    }
  }
}

static void fill_vbo_mask_grids(const CCGKey &key,
                                const Span<CCGElem *> grids,
                                const bool use_flat_layout,
                                const Span<int> grid_indices,
                                gpu::VertBuf &vert_buf)
{
  if (key.has_mask) {
    float *data = vert_buf.data<float>().data();
    if (use_flat_layout) {
      const int grid_size_1 = key.grid_size - 1;
      for (const int i : grid_indices.index_range()) {
        CCGElem *grid = grids[grid_indices[i]];
        for (int y = 0; y < grid_size_1; y++) {
          for (int x = 0; x < grid_size_1; x++) {
            *data = CCG_grid_elem_mask(key, grid, x, y);
            data++;
            *data = CCG_grid_elem_mask(key, grid, x + 1, y);
            data++;
            *data = CCG_grid_elem_mask(key, grid, x + 1, y + 1);
            data++;
            *data = CCG_grid_elem_mask(key, grid, x, y + 1);
            data++;
          }
        }
      }
    }
    else {
      for (const int i : grid_indices.index_range()) {
        CCGElem *grid = grids[grid_indices[i]];
        for (const int offset : IndexRange(key.grid_area)) {
          *data = CCG_elem_offset_mask(key, grid, offset);
          data++;
        }
      }
    }
  }
  else {
    vert_buf.data<float>().fill(0.0f);
  }
}

static void fill_vbo_face_set_grids(const CCGKey &key,
                                    const Span<int> grid_to_face_map,
                                    const Span<int> face_sets,
                                    const int color_default,
                                    const int color_seed,
                                    const bool use_flat_layout,
                                    const Span<int> grid_indices,
                                    gpu::VertBuf &vert_buf)
{
  const int verts_per_grid = use_flat_layout ? square_i(key.grid_size - 1) * 4 :
                                               square_i(key.grid_size);
  uchar4 *data = vert_buf.data<uchar4>().data();
  for (const int i : grid_indices.index_range()) {
    uchar4 color{UCHAR_MAX};
    const int fset = face_sets[grid_to_face_map[grid_indices[i]]];
    if (fset != color_default) {
      BKE_paint_face_set_overlay_color_get(fset, color_seed, color);
    }

    std::fill_n(data, verts_per_grid, color);
    data += verts_per_grid;
  }
}

static void fill_vbos_grids(const Object &object,
                            const OrigMeshData &orig_mesh_data,
                            const BitSpan use_flat_layout,
                            const IndexMask &node_mask,
                            const AttributeRequest &request,
                            const MutableSpan<gpu::VertBuf *> vbos)
{
  const SculptSession &ss = *object.sculpt;
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  const Span<bke::pbvh::GridsNode> nodes = pbvh.nodes<bke::pbvh::GridsNode>();
  const SubdivCCG &subdiv_ccg = *ss.subdiv_ccg;
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);
  const Span<CCGElem *> grids = subdiv_ccg.grids;

  if (const CustomRequest *request_type = std::get_if<CustomRequest>(&request)) {
    switch (*request_type) {
      case CustomRequest::Position: {
        node_mask.foreach_index(GrainSize(1), [&](const int i) {
          fill_vbo_position_grids(key, grids, use_flat_layout[i], nodes[i].grids(), *vbos[i]);
        });
        break;
      }
      case CustomRequest::Normal: {
        const Span<int> grid_to_face_map = subdiv_ccg.grid_to_face_map;
        const bke::AttributeAccessor attributes = orig_mesh_data.attributes;
        const VArraySpan sharp_faces = *attributes.lookup<bool>("sharp_face",
                                                                bke::AttrDomain::Face);
        node_mask.foreach_index(GrainSize(1), [&](const int i) {
          fill_vbo_normal_grids(key,
                                grids,
                                grid_to_face_map,
                                sharp_faces,
                                use_flat_layout[i],
                                nodes[i].grids(),
                                *vbos[i]);
        });

        break;
      }
      case CustomRequest::Mask: {
        node_mask.foreach_index(GrainSize(1), [&](const int i) {
          fill_vbo_mask_grids(key, grids, use_flat_layout[i], nodes[i].grids(), *vbos[i]);
        });
        break;
      }
      case CustomRequest::FaceSet: {
        const int face_set_default = orig_mesh_data.face_set_default;
        const int face_set_seed = orig_mesh_data.face_set_seed;
        const Span<int> grid_to_face_map = subdiv_ccg.grid_to_face_map;
        const bke::AttributeAccessor attributes = orig_mesh_data.attributes;
        if (const VArray<int> face_sets = *attributes.lookup<int>(".sculpt_face_set",
                                                                  bke::AttrDomain::Face))
        {
          const VArraySpan<int> face_sets_span(face_sets);
          node_mask.foreach_index(GrainSize(1), [&](const int i) {
            fill_vbo_face_set_grids(key,
                                    grid_to_face_map,
                                    face_sets_span,
                                    face_set_default,
                                    face_set_seed,
                                    use_flat_layout[i],
                                    nodes[i].grids(),
                                    *vbos[i]);
          });
        }
        else {
          node_mask.foreach_index(
              GrainSize(1), [&](const int i) { vbos[i]->data<uchar4>().fill(uchar4{UCHAR_MAX}); });
        }
        break;
      }
    }
  }
  else {
    const eCustomDataType type = std::get<GenericRequest>(request).type;
    node_mask.foreach_index(GrainSize(1), [&](const int i) {
      bke::attribute_math::convert_to_static_type(type, [&](auto dummy) {
        using T = decltype(dummy);
        using Converter = AttributeConverter<T>;
        using VBOType = typename Converter::VBOType;
        if constexpr (!std::is_void_v<VBOType>) {
          vbos[i]->data<VBOType>().fill(Converter::convert(fallback_value_for_fill<T>()));
        }
      });
    });
  }
}

static void fill_vbos_mesh(const Object &object,
                           const OrigMeshData &orig_mesh_data,
                           const IndexMask &node_mask,
                           const AttributeRequest &request,
                           const MutableSpan<gpu::VertBuf *> vbos)
{
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  const Span<bke::pbvh::MeshNode> nodes = pbvh.nodes<bke::pbvh::MeshNode>();
  const Mesh &mesh = *static_cast<const Mesh *>(object.data);
  const OffsetIndices<int> faces = mesh.faces();
  const Span<int> corner_verts = mesh.corner_verts();

  if (const CustomRequest *request_type = std::get_if<CustomRequest>(&request)) {
    switch (*request_type) {
      case CustomRequest::Position: {
        const Span<float3> vert_positions = bke::pbvh::vert_positions_eval_from_eval(object);
        node_mask.foreach_index(GrainSize(1), [&](const int i) {
          extract_data_vert_mesh<float3>(
              faces, corner_verts, vert_positions, nodes[i].faces(), *vbos[i]);
        });
        break;
      }
      case CustomRequest::Normal: {
        const Span<float3> vert_normals = bke::pbvh::vert_normals_eval_from_eval(object);
        const Span<float3> face_normals = bke::pbvh::face_normals_eval_from_eval(object);
        const bke::AttributeAccessor attributes = mesh.attributes();
        const VArraySpan sharp_faces = *attributes.lookup<bool>("sharp_face",
                                                                bke::AttrDomain::Face);
        node_mask.foreach_index(GrainSize(1), [&](const int i) {
          fill_vbo_normal_mesh(faces,
                               corner_verts,
                               sharp_faces,
                               vert_normals,
                               face_normals,
                               nodes[i].faces(),
                               *vbos[i]);
        });
        break;
      }
      case CustomRequest::Mask: {
        const VArraySpan mask = *orig_mesh_data.attributes.lookup<float>(".sculpt_mask",
                                                                         bke::AttrDomain::Point);
        if (!mask.is_empty()) {
          node_mask.foreach_index(GrainSize(1), [&](const int i) {
            fill_vbo_mask_mesh(faces, corner_verts, mask, nodes[i].faces(), *vbos[i]);
          });
        }
        else {
          node_mask.foreach_index(GrainSize(64),
                                  [&](const int i) { vbos[i]->data<float>().fill(0.0f); });
        }
        break;
      }
      case CustomRequest::FaceSet: {
        const int face_set_default = orig_mesh_data.face_set_default;
        const int face_set_seed = orig_mesh_data.face_set_seed;
        const VArraySpan face_sets = *orig_mesh_data.attributes.lookup<int>(".sculpt_face_set",
                                                                            bke::AttrDomain::Face);
        if (!face_sets.is_empty()) {
          node_mask.foreach_index(GrainSize(1), [&](const int i) {
            fill_vbo_face_set_mesh(
                faces, face_sets, face_set_default, face_set_seed, nodes[i].faces(), *vbos[i]);
          });
        }
        else {
          node_mask.foreach_index(GrainSize(64),
                                  [&](const int i) { vbos[i]->data<uchar4>().fill(uchar4(255)); });
        }
        break;
      }
    }
  }
  else {
    const GenericRequest &attr = std::get<GenericRequest>(request);
    const StringRef name = attr.name;
    const bke::AttrDomain domain = attr.domain;
    const eCustomDataType data_type = attr.type;
    const bke::AttributeAccessor attributes = orig_mesh_data.attributes;
    const GVArraySpan attribute = *attributes.lookup_or_default(name, domain, data_type);
    node_mask.foreach_index(GrainSize(1), [&](const int i) {
      fill_vbo_attribute_mesh(faces, corner_verts, attribute, domain, nodes[i].faces(), *vbos[i]);
    });
  }
}

static void fill_vbo_position_bmesh(const Set<BMFace *, 0> &faces, gpu::VertBuf &vbo)
{
  float3 *data = vbo.data<float3>().data();
  for (const BMFace *face : faces) {
    if (BM_elem_flag_test(face, BM_ELEM_HIDDEN)) {
      continue;
    }
    const BMLoop *l = face->l_first;
    *data = l->prev->v->co;
    data++;
    *data = l->v->co;
    data++;
    *data = l->next->v->co;
    data++;
  }
}

static void fill_vbo_normal_bmesh(const Set<BMFace *, 0> &faces, gpu::VertBuf &vbo)
{
  short4 *data = vbo.data<short4>().data();
  for (const BMFace *face : faces) {
    if (BM_elem_flag_test(face, BM_ELEM_HIDDEN)) {
      continue;
    }
    if (BM_elem_flag_test(face, BM_ELEM_SMOOTH)) {
      const BMLoop *l = face->l_first;
      *data = normal_float_to_short(l->prev->v->no);
      data++;
      *data = normal_float_to_short(l->v->no);
      data++;
      *data = normal_float_to_short(l->next->v->no);
      data++;
    }
    else {
      std::fill_n(data, 3, normal_float_to_short(face->no));
      data += 3;
    }
  }
}

static void fill_vbo_mask_bmesh(const Set<BMFace *, 0> &faces,
                                const int cd_offset,
                                gpu::VertBuf &vbo)
{
  float *data = vbo.data<float>().data();
  for (const BMFace *face : faces) {
    if (BM_elem_flag_test(face, BM_ELEM_HIDDEN)) {
      continue;
    }
    const BMLoop *l = face->l_first;
    *data = bmesh_cd_vert_get<float>(*l->prev->v, cd_offset);
    data++;
    *data = bmesh_cd_vert_get<float>(*l->v, cd_offset);
    data++;
    *data = bmesh_cd_vert_get<float>(*l->next->v, cd_offset);
    data++;
  }
}

static void fill_vbo_face_set_bmesh(const Set<BMFace *, 0> &faces,
                                    const int color_default,
                                    const int color_seed,
                                    const int offset,
                                    gpu::VertBuf &vbo)
{
  uchar4 *data = vbo.data<uchar4>().data();
  for (const BMFace *face : faces) {
    if (BM_elem_flag_test(face, BM_ELEM_HIDDEN)) {
      continue;
    }
    uchar4 color{UCHAR_MAX};
    const int fset = bmesh_cd_face_get<int>(*face, offset);
    if (fset != color_default) {
      BKE_paint_face_set_overlay_color_get(fset, color_seed, color);
    }
    std::fill_n(data, 3, color);
    data += 3;
  }
}

static void fill_vbo_attribute_bmesh(const Set<BMFace *, 0> &faces,
                                     const eCustomDataType data_type,
                                     const bke::AttrDomain domain,
                                     const int offset,
                                     gpu::VertBuf &vbo)
{
  bke::attribute_math::convert_to_static_type(data_type, [&](auto dummy) {
    using T = decltype(dummy);
    if constexpr (!std::is_void_v<typename AttributeConverter<T>::VBOType>) {
      switch (domain) {
        case bke::AttrDomain::Point:
          extract_data_vert_bmesh<T>(faces, offset, vbo);
          break;
        case bke::AttrDomain::Face:
          extract_data_face_bmesh<T>(faces, offset, vbo);
          break;
        case bke::AttrDomain::Corner:
          extract_data_corner_bmesh<T>(faces, offset, vbo);
          break;
        default:
          BLI_assert_unreachable();
      }
    }
  });
}

static void fill_vbos_bmesh(const Object &object,
                            const OrigMeshData &orig_mesh_data,
                            const IndexMask &node_mask,
                            const AttributeRequest &request,
                            const MutableSpan<gpu::VertBuf *> vbos)
{
  const SculptSession &ss = *object.sculpt;
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  const Span<bke::pbvh::BMeshNode> nodes = pbvh.nodes<bke::pbvh::BMeshNode>();
  const BMesh &bm = *ss.bm;
  if (const CustomRequest *request_type = std::get_if<CustomRequest>(&request)) {
    switch (*request_type) {
      case CustomRequest::Position: {
        node_mask.foreach_index(GrainSize(1), [&](const int i) {
          fill_vbo_position_bmesh(
              BKE_pbvh_bmesh_node_faces(&const_cast<bke::pbvh::BMeshNode &>(nodes[i])), *vbos[i]);
        });
        break;
      }
      case CustomRequest::Normal: {
        node_mask.foreach_index(GrainSize(1), [&](const int i) {
          fill_vbo_normal_bmesh(
              BKE_pbvh_bmesh_node_faces(&const_cast<bke::pbvh::BMeshNode &>(nodes[i])), *vbos[i]);
        });
        break;
      }
      case CustomRequest::Mask: {
        const int cd_offset = CustomData_get_offset_named(
            &bm.vdata, CD_PROP_FLOAT, ".sculpt_mask");
        if (cd_offset != -1) {
          node_mask.foreach_index(GrainSize(1), [&](const int i) {
            fill_vbo_mask_bmesh(
                BKE_pbvh_bmesh_node_faces(&const_cast<bke::pbvh::BMeshNode &>(nodes[i])),
                cd_offset,
                *vbos[i]);
          });
        }
        else {
          node_mask.foreach_index(GrainSize(64),
                                  [&](const int i) { vbos[i]->data<float>().fill(0.0f); });
        }
        break;
      }
      case CustomRequest::FaceSet: {
        const int face_set_default = orig_mesh_data.face_set_default;
        const int face_set_seed = orig_mesh_data.face_set_seed;
        const int cd_offset = CustomData_get_offset_named(
            &bm.pdata, CD_PROP_INT32, ".sculpt_face_set");
        if (cd_offset != -1) {
          node_mask.foreach_index(GrainSize(1), [&](const int i) {
            fill_vbo_face_set_bmesh(
                BKE_pbvh_bmesh_node_faces(&const_cast<bke::pbvh::BMeshNode &>(nodes[i])),
                face_set_default,
                face_set_seed,
                cd_offset,
                *vbos[i]);
          });
        }
        else {
          node_mask.foreach_index(GrainSize(64),
                                  [&](const int i) { vbos[i]->data<uchar4>().fill(uchar4(255)); });
        }
        break;
      }
    }
  }
  else {
    const GenericRequest &attr = std::get<GenericRequest>(request);
    const bke::AttrDomain domain = attr.domain;
    const eCustomDataType data_type = attr.type;
    const CustomData &custom_data = *get_cdata(bm, domain);
    const int offset = CustomData_get_offset_named(&custom_data, data_type, attr.name);
    node_mask.foreach_index(GrainSize(1), [&](const int i) {
      fill_vbo_attribute_bmesh(
          BKE_pbvh_bmesh_node_faces(&const_cast<bke::pbvh::BMeshNode &>(nodes[i])),
          data_type,
          domain,
          offset,
          *vbos[i]);
    });
  }
}

static gpu::IndexBuf *create_index_faces(const OffsetIndices<int> faces,
                                         const Span<bool> hide_poly,
                                         const Span<int> face_indices)
{
  int corners_count = 0;
  for (const int face : face_indices) {
    if (!hide_poly.is_empty() && hide_poly[face]) {
      continue;
    }
    corners_count += faces[face].size();
  }

  GPUIndexBufBuilder builder;
  GPU_indexbuf_init(&builder, GPU_PRIM_LINES, corners_count, INT_MAX);
  MutableSpan<uint2> data = GPU_indexbuf_get_data(&builder).cast<uint2>();

  int node_corner_offset = 0;
  int line_index = 0;
  for (const int face_index : face_indices) {
    const int face_size = faces[face_index].size();
    if (!hide_poly.is_empty() && hide_poly[face_index]) {
      node_corner_offset += face_size;
      continue;
    }
    for (const int i : IndexRange(face_size)) {
      const int next = (i == face_size - 1) ? 0 : i + 1;
      data[line_index] = uint2(i, next) + node_corner_offset;
      line_index++;
    }

    node_corner_offset += face_size;
  }

  gpu::IndexBuf *ibo = GPU_indexbuf_calloc();
  GPU_indexbuf_build_in_place_ex(&builder, 0, node_corner_offset, false, ibo);
  return ibo;
}

static gpu::IndexBuf *create_index_bmesh(const Set<BMFace *, 0> &faces,
                                         const int visible_faces_num)
{
  GPUIndexBufBuilder elb_lines;
  GPU_indexbuf_init(&elb_lines, GPU_PRIM_LINES, visible_faces_num * 3, INT_MAX);

  int v_index = 0;

  for (const BMFace *face : faces) {
    if (BM_elem_flag_test(face, BM_ELEM_HIDDEN)) {
      continue;
    }

    GPU_indexbuf_add_line_verts(&elb_lines, v_index, v_index + 1);
    GPU_indexbuf_add_line_verts(&elb_lines, v_index + 1, v_index + 2);
    GPU_indexbuf_add_line_verts(&elb_lines, v_index + 2, v_index);

    v_index += 3;
  }

  return GPU_indexbuf_build(&elb_lines);
}

static void create_tri_index_grids(const Span<int> grid_indices,
                                   const BitGroupVector<> &grid_hidden,
                                   const int gridsize,
                                   const int skip,
                                   const int totgrid,
                                   GPUIndexBufBuilder &elb)
{
  uint offset = 0;
  const uint grid_vert_len = gridsize * gridsize;
  for (int i = 0; i < totgrid; i++, offset += grid_vert_len) {
    uint v0, v1, v2, v3;

    const BoundedBitSpan gh = grid_hidden.is_empty() ? BoundedBitSpan() :
                                                       grid_hidden[grid_indices[i]];

    for (int y = 0; y < gridsize - skip; y += skip) {
      for (int x = 0; x < gridsize - skip; x += skip) {
        /* Skip hidden grid face */
        if (!gh.is_empty() && paint_is_grid_face_hidden(gh, gridsize, x, y)) {
          continue;
        }
        /* Indices in a Clockwise QUAD disposition. */
        v0 = offset + CCG_grid_xy_to_index(gridsize, x, y);
        v1 = offset + CCG_grid_xy_to_index(gridsize, x + skip, y);
        v2 = offset + CCG_grid_xy_to_index(gridsize, x + skip, y + skip);
        v3 = offset + CCG_grid_xy_to_index(gridsize, x, y + skip);

        GPU_indexbuf_add_tri_verts(&elb, v0, v2, v1);
        GPU_indexbuf_add_tri_verts(&elb, v0, v3, v2);
      }
    }
  }
}

static void create_tri_index_grids_flat_layout(const Span<int> grid_indices,
                                               const BitGroupVector<> &grid_hidden,
                                               const int gridsize,
                                               const int skip,
                                               const int totgrid,
                                               GPUIndexBufBuilder &elb)
{
  uint offset = 0;
  const uint grid_vert_len = square_uint(gridsize - 1) * 4;

  for (int i = 0; i < totgrid; i++, offset += grid_vert_len) {
    const BoundedBitSpan gh = grid_hidden.is_empty() ? BoundedBitSpan() :
                                                       grid_hidden[grid_indices[i]];

    uint v0, v1, v2, v3;
    for (int y = 0; y < gridsize - skip; y += skip) {
      for (int x = 0; x < gridsize - skip; x += skip) {
        /* Skip hidden grid face */
        if (!gh.is_empty() && paint_is_grid_face_hidden(gh, gridsize, x, y)) {
          continue;
        }

        v0 = (y * (gridsize - 1) + x) * 4;

        if (skip > 1) {
          v1 = (y * (gridsize - 1) + x + skip - 1) * 4;
          v2 = ((y + skip - 1) * (gridsize - 1) + x + skip - 1) * 4;
          v3 = ((y + skip - 1) * (gridsize - 1) + x) * 4;
        }
        else {
          v1 = v2 = v3 = v0;
        }

        /* VBO data are in a Clockwise QUAD disposition.  Note
         * that vertices might be in different quads if we're
         * building a coarse index buffer.
         */
        v0 += offset;
        v1 += offset + 1;
        v2 += offset + 2;
        v3 += offset + 3;

        GPU_indexbuf_add_tri_verts(&elb, v0, v2, v1);
        GPU_indexbuf_add_tri_verts(&elb, v0, v3, v2);
      }
    }
  }
}

static void create_lines_index_grids(const Span<int> grid_indices,
                                     int display_gridsize,
                                     const BitGroupVector<> &grid_hidden,
                                     const int gridsize,
                                     const int skip,
                                     const int totgrid,
                                     GPUIndexBufBuilder &elb_lines)
{
  uint offset = 0;
  const uint grid_vert_len = gridsize * gridsize;
  for (int i = 0; i < totgrid; i++, offset += grid_vert_len) {
    uint v0, v1, v2, v3;
    bool grid_visible = false;

    const BoundedBitSpan gh = grid_hidden.is_empty() ? BoundedBitSpan() :
                                                       grid_hidden[grid_indices[i]];

    for (int y = 0; y < gridsize - skip; y += skip) {
      for (int x = 0; x < gridsize - skip; x += skip) {
        /* Skip hidden grid face */
        if (!gh.is_empty() && paint_is_grid_face_hidden(gh, gridsize, x, y)) {
          continue;
        }
        /* Indices in a Clockwise QUAD disposition. */
        v0 = offset + CCG_grid_xy_to_index(gridsize, x, y);
        v1 = offset + CCG_grid_xy_to_index(gridsize, x + skip, y);
        v2 = offset + CCG_grid_xy_to_index(gridsize, x + skip, y + skip);
        v3 = offset + CCG_grid_xy_to_index(gridsize, x, y + skip);

        GPU_indexbuf_add_line_verts(&elb_lines, v0, v1);
        GPU_indexbuf_add_line_verts(&elb_lines, v0, v3);

        if (y / skip + 2 == display_gridsize) {
          GPU_indexbuf_add_line_verts(&elb_lines, v2, v3);
        }
        grid_visible = true;
      }

      if (grid_visible) {
        GPU_indexbuf_add_line_verts(&elb_lines, v1, v2);
      }
    }
  }
}

static void create_lines_index_grids_flat_layout(const Span<int> grid_indices,
                                                 int display_gridsize,
                                                 const BitGroupVector<> &grid_hidden,
                                                 const int gridsize,
                                                 const int skip,
                                                 const int totgrid,
                                                 GPUIndexBufBuilder &elb_lines)
{
  uint offset = 0;
  const uint grid_vert_len = square_uint(gridsize - 1) * 4;

  for (int i = 0; i < totgrid; i++, offset += grid_vert_len) {
    bool grid_visible = false;
    const BoundedBitSpan gh = grid_hidden.is_empty() ? BoundedBitSpan() :
                                                       grid_hidden[grid_indices[i]];

    uint v0, v1, v2, v3;
    for (int y = 0; y < gridsize - skip; y += skip) {
      for (int x = 0; x < gridsize - skip; x += skip) {
        /* Skip hidden grid face */
        if (!gh.is_empty() && paint_is_grid_face_hidden(gh, gridsize, x, y)) {
          continue;
        }

        v0 = (y * (gridsize - 1) + x) * 4;

        if (skip > 1) {
          v1 = (y * (gridsize - 1) + x + skip - 1) * 4;
          v2 = ((y + skip - 1) * (gridsize - 1) + x + skip - 1) * 4;
          v3 = ((y + skip - 1) * (gridsize - 1) + x) * 4;
        }
        else {
          v1 = v2 = v3 = v0;
        }

        /* VBO data are in a Clockwise QUAD disposition.  Note
         * that vertices might be in different quads if we're
         * building a coarse index buffer.
         */
        v0 += offset;
        v1 += offset + 1;
        v2 += offset + 2;
        v3 += offset + 3;

        GPU_indexbuf_add_line_verts(&elb_lines, v0, v1);
        GPU_indexbuf_add_line_verts(&elb_lines, v0, v3);

        if (y / skip + 2 == display_gridsize) {
          GPU_indexbuf_add_line_verts(&elb_lines, v2, v3);
        }
        grid_visible = true;
      }

      if (grid_visible) {
        GPU_indexbuf_add_line_verts(&elb_lines, v1, v2);
      }
    }
  }
}

static Array<int> calc_material_indices(const Object &object)
{
  const SculptSession &ss = *object.sculpt;
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  switch (pbvh.type()) {
    case bke::pbvh::Type::Mesh: {
      const Span<bke::pbvh::MeshNode> nodes = pbvh.nodes<bke::pbvh::MeshNode>();
      const Mesh &mesh = *static_cast<const Mesh *>(object.data);
      const bke::AttributeAccessor attributes = mesh.attributes();
      const VArray material_indices = *attributes.lookup<int>("material_index",
                                                              bke::AttrDomain::Face);
      if (!material_indices) {
        return {};
      }
      Array<int> node_materials(nodes.size());
      threading::parallel_for(nodes.index_range(), 64, [&](const IndexRange range) {
        for (const int i : range) {
          const Span<int> face_indices = nodes[i].faces();
          if (face_indices.is_empty()) {
            continue;
          }
          node_materials[i] = material_indices[face_indices.first()];
        }
      });
      return node_materials;
    }
    case bke::pbvh::Type::Grids: {
      const Span<bke::pbvh::GridsNode> nodes = pbvh.nodes<bke::pbvh::GridsNode>();
      const Mesh &mesh = *static_cast<const Mesh *>(object.data);
      const bke::AttributeAccessor attributes = mesh.attributes();
      const VArray material_indices = *attributes.lookup<int>("material_index",
                                                              bke::AttrDomain::Face);
      if (!material_indices) {
        return {};
      }
      Array<int> node_materials(nodes.size());
      const SubdivCCG &subdiv_ccg = *ss.subdiv_ccg;
      const Span<int> grid_faces = subdiv_ccg.grid_to_face_map;
      threading::parallel_for(nodes.index_range(), 64, [&](const IndexRange range) {
        for (const int i : range) {
          const Span<int> grids = nodes[i].grids();
          if (grids.is_empty()) {
            continue;
          }
          node_materials[i] = material_indices[grid_faces[grids.first()]];
        }
      });
      return node_materials;
    }
    case bke::pbvh::Type::BMesh:
      return {};
  }
  BLI_assert_unreachable();
  return {};
}

static BitVector<> calc_use_flat_layout(const Object &object, const OrigMeshData &orig_mesh_data)
{
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  switch (pbvh.type()) {
    case bke::pbvh::Type::Mesh:
      /* NOTE: Theoretically it would be possible to used vertex indexed buffers if there are no
       * face corner attributes, sharp faces, or face sets. */
      return {};
    case bke::pbvh::Type::Grids: {
      const Span<bke::pbvh::GridsNode> nodes = pbvh.nodes<bke::pbvh::GridsNode>();
      const bke::AttributeAccessor attributes = orig_mesh_data.attributes;
      const VArraySpan sharp_faces = *attributes.lookup<bool>("sharp_face", bke::AttrDomain::Face);
      if (sharp_faces.is_empty()) {
        return BitVector<>(nodes.size(), false);
      }

      const SubdivCCG &subdiv_ccg = *object.sculpt->subdiv_ccg;
      const Span<int> grid_to_face_map = subdiv_ccg.grid_to_face_map;

      /* Use boolean array instead of #BitVector for parallelized writing. */
      Array<bool> use_flat_layout(nodes.size());
      threading::parallel_for(nodes.index_range(), 4, [&](const IndexRange range) {
        for (const int i : range) {
          const Span<int> grids = nodes[i].grids();
          if (grids.is_empty()) {
            continue;
          }
          use_flat_layout[i] = std::any_of(grids.begin(), grids.end(), [&](const int grid) {
            return sharp_faces[grid_to_face_map[grid]];
          });
        }
      });
      return BitVector<>(use_flat_layout);
    }
    case bke::pbvh::Type::BMesh:
      return {};
  }
  BLI_assert_unreachable();
  return {};
}

static gpu::IndexBuf *create_tri_index_mesh(const OffsetIndices<int> faces,
                                            const Span<int3> corner_tris,
                                            const Span<bool> hide_poly,
                                            const Span<int> face_indices)
{
  int tris_num = 0;
  for (const int face : face_indices) {
    if (!hide_poly.is_empty() && hide_poly[face]) {
      continue;
    }
    tris_num += bke::mesh::face_triangles_num(faces[face].size());
  }

  GPUIndexBufBuilder builder;
  GPU_indexbuf_init(&builder, GPU_PRIM_TRIS, tris_num, INT_MAX);
  MutableSpan<uint3> data = GPU_indexbuf_get_data(&builder).cast<uint3>();

  int tri_index = 0;
  int node_corner_offset = 0;
  for (const int face_index : face_indices) {
    const IndexRange face = faces[face_index];
    if (!hide_poly.is_empty() && hide_poly[face_index]) {
      node_corner_offset += face.size();
      continue;
    }
    for (const int tri : bke::mesh::face_triangles_range(faces, face_index)) {
      for (int i : IndexRange(3)) {
        const int corner = corner_tris[tri][i];
        const int index_in_face = corner - face.first();
        data[tri_index][i] = node_corner_offset + index_in_face;
      }
      tri_index++;
    }
    node_corner_offset += face.size();
  }

  gpu::IndexBuf *ibo = GPU_indexbuf_calloc();
  GPU_indexbuf_build_in_place_ex(&builder, 0, node_corner_offset, false, ibo);
  return ibo;
}

static gpu::IndexBuf *create_tri_index_grids(const CCGKey &key,
                                             const BitGroupVector<> &grid_hidden,
                                             const bool do_coarse,
                                             const Span<int> grid_indices,
                                             const bool use_flat_layout)
{
  int gridsize = key.grid_size;
  int display_gridsize = gridsize;
  int totgrid = grid_indices.size();
  int skip = 1;

  const int display_level = do_coarse ? 0 : key.level;

  if (display_level < key.level) {
    display_gridsize = (1 << display_level) + 1;
    skip = 1 << (key.level - display_level - 1);
  }

  GPUIndexBufBuilder elb;

  uint visible_quad_len = bke::pbvh::count_grid_quads(
      grid_hidden, grid_indices, key.grid_size, display_gridsize);

  GPU_indexbuf_init(&elb, GPU_PRIM_TRIS, 2 * visible_quad_len, INT_MAX);

  if (use_flat_layout) {
    create_tri_index_grids_flat_layout(grid_indices, grid_hidden, gridsize, skip, totgrid, elb);
  }
  else {
    create_tri_index_grids(grid_indices, grid_hidden, gridsize, skip, totgrid, elb);
  }

  return GPU_indexbuf_build(&elb);
}

static gpu::IndexBuf *create_lines_index_grids(const CCGKey &key,
                                               const BitGroupVector<> &grid_hidden,
                                               const bool do_coarse,
                                               const Span<int> grid_indices,
                                               const bool use_flat_layout)
{
  int gridsize = key.grid_size;
  int display_gridsize = gridsize;
  int totgrid = grid_indices.size();
  int skip = 1;

  const int display_level = do_coarse ? 0 : key.level;

  if (display_level < key.level) {
    display_gridsize = (1 << display_level) + 1;
    skip = 1 << (key.level - display_level - 1);
  }

  GPUIndexBufBuilder elb;
  GPU_indexbuf_init(
      &elb, GPU_PRIM_LINES, 2 * totgrid * display_gridsize * (display_gridsize - 1), INT_MAX);

  if (use_flat_layout) {
    create_lines_index_grids_flat_layout(
        grid_indices, display_gridsize, grid_hidden, gridsize, skip, totgrid, elb);
  }
  else {
    create_lines_index_grids(
        grid_indices, display_gridsize, grid_hidden, gridsize, skip, totgrid, elb);
  }

  return GPU_indexbuf_build(&elb);
}

Span<gpu::IndexBuf *> DrawCacheImpl::ensure_lines_indices(const Object &object,
                                                          const OrigMeshData &orig_mesh_data,
                                                          const IndexMask &node_mask,
                                                          const bool coarse)
{
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  Vector<gpu::IndexBuf *> &ibos = coarse ? lines_ibos_coarse_ : lines_ibos_;
  ibos.resize(pbvh.nodes_num(), nullptr);

  IndexMaskMemory memory;
  const IndexMask nodes_to_calculate = IndexMask::from_predicate(
      node_mask, GrainSize(8196), memory, [&](const int i) { return !ibos[i]; });

  switch (pbvh.type()) {
    case bke::pbvh::Type::Mesh: {
      const Span<bke::pbvh::MeshNode> nodes = pbvh.nodes<bke::pbvh::MeshNode>();
      const Mesh &mesh = *static_cast<const Mesh *>(object.data);
      const OffsetIndices<int> faces = mesh.faces();
      const bke::AttributeAccessor attributes = orig_mesh_data.attributes;
      const VArraySpan hide_poly = *attributes.lookup<bool>(".hide_poly", bke::AttrDomain::Face);
      nodes_to_calculate.foreach_index(GrainSize(1), [&](const int i) {
        ibos[i] = create_index_faces(faces, hide_poly, nodes[i].faces());
      });
      break;
    }
    case bke::pbvh::Type::Grids: {
      const Span<bke::pbvh::GridsNode> nodes = pbvh.nodes<bke::pbvh::GridsNode>();
      nodes_to_calculate.foreach_index(GrainSize(1), [&](const int i) {
        const SubdivCCG &subdiv_ccg = *object.sculpt->subdiv_ccg;
        const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);
        ibos[i] = create_lines_index_grids(
            key, subdiv_ccg.grid_hidden, coarse, nodes[i].grids(), use_flat_layout_[i]);
      });
      break;
    }
    case bke::pbvh::Type::BMesh: {
      const Span<bke::pbvh::BMeshNode> nodes = pbvh.nodes<bke::pbvh::BMeshNode>();
      nodes_to_calculate.foreach_index(GrainSize(1), [&](const int i) {
        const Set<BMFace *, 0> &faces = BKE_pbvh_bmesh_node_faces(
            &const_cast<bke::pbvh::BMeshNode &>(nodes[i]));
        const int visible_faces_num = count_visible_tris_bmesh(faces);
        ibos[i] = create_index_bmesh(faces, visible_faces_num);
      });
      break;
    }
  }

  return ibos;
}

BitSpan DrawCacheImpl::ensure_use_flat_layout(const Object &object,
                                              const OrigMeshData &orig_mesh_data)
{
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  if (use_flat_layout_.size() != pbvh.nodes_num()) {
    use_flat_layout_ = calc_use_flat_layout(object, orig_mesh_data);
  }
  return use_flat_layout_;
}

BLI_NOINLINE static void ensure_vbos_allocated_mesh(const Object &object,
                                                    const OrigMeshData &orig_mesh_data,
                                                    const GPUVertFormat &format,
                                                    const IndexMask &node_mask,
                                                    const MutableSpan<gpu::VertBuf *> vbos)
{
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  const Span<bke::pbvh::MeshNode> nodes = pbvh.nodes<bke::pbvh::MeshNode>();
  const Mesh &mesh = *static_cast<Mesh *>(object.data);
  const OffsetIndices<int> faces = mesh.faces();
  const bke::AttributeAccessor attributes = orig_mesh_data.attributes;
  const VArraySpan hide_poly = *attributes.lookup<bool>(".hide_poly", bke::AttrDomain::Face);
  node_mask.foreach_index(GrainSize(64), [&](const int i) {
    if (!vbos[i]) {
      vbos[i] = GPU_vertbuf_create_with_format(format);
    }
    const Span<int> face_indices = nodes[i].faces();
    const int verts_num = count_visible_tris_mesh(faces, face_indices, hide_poly) * 3;
    GPU_vertbuf_data_alloc(*vbos[i], verts_num);
  });
}

BLI_NOINLINE static void ensure_vbos_allocated_grids(const Object &object,
                                                     const GPUVertFormat &format,
                                                     const BitSpan use_flat_layout,
                                                     const IndexMask &node_mask,
                                                     const MutableSpan<gpu::VertBuf *> vbos)
{
  const SculptSession &ss = *object.sculpt;
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  const Span<bke::pbvh::GridsNode> nodes = pbvh.nodes<bke::pbvh::GridsNode>();
  const SubdivCCG &subdiv_ccg = *ss.subdiv_ccg;
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);
  node_mask.foreach_index(GrainSize(64), [&](const int i) {
    if (!vbos[i]) {
      vbos[i] = GPU_vertbuf_create_with_format(format);
    }
    const int verts_per_grid = use_flat_layout[i] ? square_i(key.grid_size - 1) * 4 :
                                                    square_i(key.grid_size);
    const int verts_num = nodes[i].grids().size() * verts_per_grid;
    GPU_vertbuf_data_alloc(*vbos[i], verts_num);
  });
}

BLI_NOINLINE static void ensure_vbos_allocated_bmesh(const Object &object,
                                                     const GPUVertFormat &format,
                                                     const IndexMask &node_mask,
                                                     const MutableSpan<gpu::VertBuf *> vbos)
{
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  const Span<bke::pbvh::BMeshNode> nodes = pbvh.nodes<bke::pbvh::BMeshNode>();

  node_mask.foreach_index(GrainSize(64), [&](const int i) {
    if (!vbos[i]) {
      vbos[i] = GPU_vertbuf_create_with_format(format);
    }
    const Set<BMFace *, 0> &faces = BKE_pbvh_bmesh_node_faces(
        &const_cast<bke::pbvh::BMeshNode &>(nodes[i]));
    const int verts_num = count_visible_tris_bmesh(faces) * 3;
    GPU_vertbuf_data_alloc(*vbos[i], verts_num);
  });
}

BLI_NOINLINE static void flush_vbo_data(const Span<gpu::VertBuf *> vbos,
                                        const IndexMask &node_mask)
{
  node_mask.foreach_index([&](const int i) { GPU_vertbuf_use(vbos[i]); });
}

Span<gpu::VertBuf *> DrawCacheImpl::ensure_attribute_data(const Object &object,
                                                          const OrigMeshData &orig_mesh_data,
                                                          const AttributeRequest &attr,
                                                          const IndexMask &node_mask)
{
  if (!pbvh_attr_supported(attr)) {
    return {};
  }
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  AttributeData &data = attribute_vbos_.lookup_or_add_default(attr);
  Vector<gpu::VertBuf *> &vbos = data.vbos;
  vbos.resize(pbvh.nodes_num(), nullptr);

  /* The nodes we recompute here are a combination of:
   *   1. null VBOs, which correspond to nodes that either haven't been drawn before, or have been
   *      cleared completely by #free_nodes_with_changed_topology.
   *   2. Nodes that have been tagged dirty as their values are changed.
   * We also only process a subset of the nodes referenced by the caller, for example to only
   * recompute visible nodes. */
  IndexMaskMemory memory;
  const IndexMask empty_mask = IndexMask::from_predicate(
      node_mask, GrainSize(8196), memory, [&](const int i) { return !vbos[i]; });
  const IndexMask dirty_mask = IndexMask::from_bits(
      node_mask.slice_content(data.dirty_nodes.index_range()), data.dirty_nodes, memory);
  const IndexMask mask = IndexMask::from_union(empty_mask, dirty_mask, memory);

  const GPUVertFormat format = format_for_request(orig_mesh_data, attr);

  switch (pbvh.type()) {
    case bke::pbvh::Type::Mesh: {
      ensure_vbos_allocated_mesh(object, orig_mesh_data, format, mask, vbos);
      fill_vbos_mesh(object, orig_mesh_data, mask, attr, vbos);
      break;
    }
    case bke::pbvh::Type::Grids: {
      ensure_vbos_allocated_grids(object, format, use_flat_layout_, mask, vbos);
      fill_vbos_grids(object, orig_mesh_data, use_flat_layout_, mask, attr, vbos);
      break;
    }
    case bke::pbvh::Type::BMesh: {
      ensure_vbos_allocated_bmesh(object, format, mask, vbos);
      fill_vbos_bmesh(object, orig_mesh_data, mask, attr, vbos);
      break;
    }
  }

  data.dirty_nodes.clear_and_shrink();

  flush_vbo_data(vbos, mask);

  return vbos;
}

Span<gpu::IndexBuf *> DrawCacheImpl::ensure_tri_indices(const Object &object,
                                                        const OrigMeshData &orig_mesh_data,
                                                        const IndexMask &node_mask,
                                                        const bool coarse)
{
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  switch (pbvh.type()) {
    case bke::pbvh::Type::Mesh: {
      const Span<bke::pbvh::MeshNode> nodes = pbvh.nodes<bke::pbvh::MeshNode>();

      Vector<gpu::IndexBuf *> &ibos = tris_ibos_;
      ibos.resize(nodes.size(), nullptr);

      /* Whenever a node's visible triangle count has changed the index buffers are freed, so we
       * only recalculate null IBOs here. A new mask is recalculated for more even task
       * distribution between threads. */
      IndexMaskMemory memory;
      const IndexMask nodes_to_calculate = IndexMask::from_predicate(
          node_mask, GrainSize(8196), memory, [&](const int i) { return !ibos[i]; });

      const Mesh &mesh = *static_cast<const Mesh *>(object.data);
      const OffsetIndices<int> faces = mesh.faces();
      const Span<int3> corner_tris = mesh.corner_tris();
      const bke::AttributeAccessor attributes = orig_mesh_data.attributes;
      const VArraySpan hide_poly = *attributes.lookup<bool>(".hide_poly", bke::AttrDomain::Face);
      nodes_to_calculate.foreach_index(GrainSize(1), [&](const int i) {
        ibos[i] = create_tri_index_mesh(faces, corner_tris, hide_poly, nodes[i].faces());
      });
      return ibos;
    }
    case bke::pbvh::Type::Grids: {
      /* Unlike the other geometry types, multires grids use indexed vertex buffers because when
       * there are no flat faces, vertices can be shared between neighboring quads. This results in
       * a 4x decrease in the amount of data uploaded. Theoretically it also means freeing VBOs
       * because of visibility changes is unnecessary.
       *
       * TODO: With the "flat layout" and no hidden faces, the index buffers are unnecessary, we
       * should avoid creating them in that case. */
      const Span<bke::pbvh::GridsNode> nodes = pbvh.nodes<bke::pbvh::GridsNode>();

      Vector<gpu::IndexBuf *> &ibos = coarse ? tris_ibos_coarse_ : tris_ibos_;
      ibos.resize(nodes.size(), nullptr);

      /* Whenever a node's visible triangle count has changed the index buffers are freed, so we
       * only recalculate null IBOs here. A new mask is recalculated for more even task
       * distribution between threads. */
      IndexMaskMemory memory;
      const IndexMask nodes_to_calculate = IndexMask::from_predicate(
          node_mask, GrainSize(8196), memory, [&](const int i) { return !ibos[i]; });

      const SubdivCCG &subdiv_ccg = *object.sculpt->subdiv_ccg;
      const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);

      nodes_to_calculate.foreach_index(GrainSize(1), [&](const int i) {
        ibos[i] = create_tri_index_grids(
            key, subdiv_ccg.grid_hidden, coarse, nodes[i].grids(), use_flat_layout_[i]);
      });
      return ibos;
    }
    case bke::pbvh::Type::BMesh:
      return {};
  }
  BLI_assert_unreachable();
  return {};
}

Span<gpu::Batch *> DrawCacheImpl::ensure_tris_batches(const Object &object,
                                                      const ViewportRequest &request,
                                                      const IndexMask &nodes_to_update)
{
  const Object &object_orig = *DEG_get_original_object(&const_cast<Object &>(object));
  const OrigMeshData orig_mesh_data{*static_cast<const Mesh *>(object_orig.data)};

  this->ensure_use_flat_layout(object, orig_mesh_data);
  this->free_nodes_with_changed_topology(object, nodes_to_update);

  const Span<gpu::IndexBuf *> ibos = this->ensure_tri_indices(
      object, orig_mesh_data, nodes_to_update, request.use_coarse_grids);

  for (const AttributeRequest &attr : request.attributes) {
    this->ensure_attribute_data(object, orig_mesh_data, attr, nodes_to_update);
  }

  /* Collect VBO spans in a different loop because #ensure_attribute_data invalidates the allocated
   * arrays when its map is changed. */
  Vector<Span<gpu::VertBuf *>> attr_vbos;
  for (const AttributeRequest &attr : request.attributes) {
    const Span<gpu::VertBuf *> vbos = attribute_vbos_.lookup(attr).vbos;
    if (!vbos.is_empty()) {
      attr_vbos.append(vbos);
    }
  }

  /* Except for the first iteration of the draw loop, we only need to rebuild batches for nodes
   * with changed topology (visible triangle count). */
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  Vector<gpu::Batch *> &batches = tris_batches_.lookup_or_add_default(request);
  batches.resize(pbvh.nodes_num(), nullptr);
  nodes_to_update.foreach_index(GrainSize(64), [&](const int i) {
    if (!batches[i]) {
      batches[i] = GPU_batch_create(GPU_PRIM_TRIS, nullptr, ibos.is_empty() ? nullptr : ibos[i]);
      for (const Span<gpu::VertBuf *> vbos : attr_vbos) {
        GPU_batch_vertbuf_add(batches[i], vbos[i], false);
      }
    }
  });

  return batches;
}

Span<gpu::Batch *> DrawCacheImpl::ensure_lines_batches(const Object &object,
                                                       const ViewportRequest &request,
                                                       const IndexMask &nodes_to_update)
{
  const Object &object_orig = *DEG_get_original_object(&const_cast<Object &>(object));
  const OrigMeshData orig_mesh_data(*static_cast<const Mesh *>(object_orig.data));

  this->ensure_use_flat_layout(object, orig_mesh_data);
  this->free_nodes_with_changed_topology(object, nodes_to_update);

  const Span<gpu::VertBuf *> position = this->ensure_attribute_data(
      object, orig_mesh_data, CustomRequest::Position, nodes_to_update);
  const Span<gpu::IndexBuf *> lines = this->ensure_lines_indices(
      object, orig_mesh_data, nodes_to_update, request.use_coarse_grids);

  /* Except for the first iteration of the draw loop, we only need to rebuild batches for nodes
   * with changed topology (visible triangle count). */
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  Vector<gpu::Batch *> &batches = request.use_coarse_grids ? lines_batches_coarse_ :
                                                             lines_batches_;
  batches.resize(pbvh.nodes_num(), nullptr);
  nodes_to_update.foreach_index(GrainSize(64), [&](const int i) {
    if (!batches[i]) {
      batches[i] = GPU_batch_create(GPU_PRIM_LINES, nullptr, lines[i]);
      GPU_batch_vertbuf_add(batches[i], position[i], false);
    }
  });

  return batches;
}

Span<int> DrawCacheImpl::ensure_material_indices(const Object &object)
{
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  if (material_indices_.size() != pbvh.nodes_num()) {
    material_indices_ = calc_material_indices(object);
  }
  return material_indices_;
}

}  // namespace blender::draw::pbvh
