/* SPDX-FileCopyrightText: 2005 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 *
 * bke::pbvh::Tree drawing.
 * Embeds GPU meshes inside of bke::pbvh::Tree nodes, used by mesh sculpt mode.
 */

#include <algorithm>
#include <climits>
#include <cstddef>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include "MEM_guardedalloc.h"

#include "BLI_bitmap.h"
#include "BLI_function_ref.hh"
#include "BLI_ghash.h"
#include "BLI_index_range.hh"
#include "BLI_map.hh"
#include "BLI_math_color.h"
#include "BLI_math_vector_types.hh"
#include "BLI_string.h"
#include "BLI_string_ref.hh"
#include "BLI_timeit.hh"
#include "BLI_utildefines.h"
#include "BLI_vector.hh"

#include "DNA_mesh_types.h"

#include "BKE_attribute.hh"
#include "BKE_attribute_math.hh"
#include "BKE_ccg.hh"
#include "BKE_customdata.hh"
#include "BKE_mesh.hh"
#include "BKE_paint.hh"
#include "BKE_pbvh_api.hh"
#include "BKE_subdiv_ccg.hh"

#include "GPU_batch.hh"

#include "DRW_engine.hh"
#include "DRW_pbvh.hh"

#include "attribute_convert.hh"
#include "bmesh.hh"
#include "draw_pbvh.hh"
#include "gpu_private.hh"

#define MAX_PBVH_BATCH_KEY 512
#define MAX_PBVH_VBOS 16

namespace blender::draw::pbvh {

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

static GPUVertFormat attribute_format(const PBVH_GPU_Args &args,
                                      const StringRefNull name,
                                      const eCustomDataType data_type)
{
  GPUVertFormat format = draw::init_format_for_attribute(data_type, "data");

  bool is_render, is_active;
  const char *prefix = "a";

  if (CD_TYPE_AS_MASK(data_type) & CD_MASK_COLOR_ALL) {
    prefix = "c";
    is_active = args.active_color == name;
    is_render = args.render_color == name;
  }
  if (data_type == CD_PROP_FLOAT2) {
    prefix = "u";
    is_active = StringRef(CustomData_get_active_layer_name(args.corner_data, data_type)) == name;
    is_render = StringRef(CustomData_get_render_layer_name(args.corner_data, data_type)) == name;
  }

  DRW_cdlayer_attr_aliases_add(&format, prefix, data_type, name.c_str(), is_render, is_active);
  return format;
}

static GPUVertFormat format_for_request(const PBVH_GPU_Args &args, const AttributeRequest &request)
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
    return attribute_format(args, attr.name, attr.type);
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

static std::string calc_request_key(const AttributeRequest &request)
{
  char buf[512];
  if (const CustomRequest *request_type = std::get_if<CustomRequest>(&request)) {
    SNPRINTF(buf, "%d:%d:", int(*request_type) + CD_NUMTYPES, 0);
  }
  else {
    const GenericRequest &attr = std::get<GenericRequest>(request);
    const StringRefNull name = attr.name;
    const bke::AttrDomain domain = attr.domain;
    const eCustomDataType data_type = attr.type;
    SNPRINTF(buf, "%d:%d:%s", int(data_type), int(domain), name.c_str());
  }
  return buf;
}

struct PBVHVbo {
  AttributeRequest request;
  gpu::VertBuf *vert_buf = nullptr;
  std::string key;

  PBVHVbo(const AttributeRequest &request) : request(request)
  {
    key = calc_request_key(request);
  }

  void clear_data()
  {
    GPU_vertbuf_clear(vert_buf);
  }
};

inline short4 normal_float_to_short(const float3 &value)
{
  short3 result;
  normal_float_to_short_v3(result, value);
  return short4(result.x, result.y, result.z, 0);
}

template<typename T>
void extract_data_vert_mesh(const Span<int> corner_verts,
                            const Span<int3> corner_tris,
                            const Span<int> tri_faces,
                            const Span<bool> hide_poly,
                            const Span<T> attribute,
                            const Span<int> tris,
                            gpu::VertBuf &vbo)
{
  using Converter = AttributeConverter<T>;
  using VBOType = typename Converter::VBOType;
  VBOType *data = vbo.data<VBOType>().data();
  for (const int tri : tris) {
    if (!hide_poly.is_empty() && hide_poly[tri_faces[tri]]) {
      continue;
    }
    for (int i : IndexRange(3)) {
      const int vert = corner_verts[corner_tris[tri][i]];
      *data = Converter::convert(attribute[vert]);
      data++;
    }
  }
}

template<typename T>
void extract_data_face_mesh(const Span<int> tri_faces,
                            const Span<bool> hide_poly,
                            const Span<T> attribute,
                            const Span<int> tris,
                            gpu::VertBuf &vbo)
{
  using Converter = AttributeConverter<T>;
  using VBOType = typename Converter::VBOType;

  VBOType *data = vbo.data<VBOType>().data();
  for (const int tri : tris) {
    const int face = tri_faces[tri];
    if (!hide_poly.is_empty() && hide_poly[face]) {
      continue;
    }
    std::fill_n(data, 3, Converter::convert(attribute[face]));
    data += 3;
  }
}

template<typename T>
void extract_data_corner_mesh(const Span<int3> corner_tris,
                              const Span<int> tri_faces,
                              const Span<bool> hide_poly,
                              const Span<T> attribute,
                              const Span<int> tris,
                              gpu::VertBuf &vbo)
{
  using Converter = AttributeConverter<T>;
  using VBOType = typename Converter::VBOType;

  VBOType *data = vbo.data<VBOType>().data();
  for (const int tri : tris) {
    if (!hide_poly.is_empty() && hide_poly[tri_faces[tri]]) {
      continue;
    }
    for (int i : IndexRange(3)) {
      const int corner = corner_tris[tri][i];
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

struct PBVHBatch {
  Vector<int> vbos;
  gpu::Batch *tris = nullptr, *lines = nullptr;
  /* Coarse multi-resolution, will use full-sized VBOs only index buffer changes. */
  bool is_coarse = false;

  void sort_vbos(Vector<PBVHVbo> &master_vbos)
  {
    struct cmp {
      Vector<PBVHVbo> &master_vbos;

      cmp(Vector<PBVHVbo> &_master_vbos) : master_vbos(_master_vbos) {}

      bool operator()(const int &a, const int &b)
      {
        return master_vbos[a].key < master_vbos[b].key;
      }
    };

    std::sort(vbos.begin(), vbos.end(), cmp(master_vbos));
  }

  std::string build_key(Vector<PBVHVbo> &master_vbos)
  {
    std::string key = "";

    if (is_coarse) {
      key += "c:";
    }

    sort_vbos(master_vbos);

    for (int vbo_i : vbos) {
      key += master_vbos[vbo_i].key + ":";
    }

    return key;
  }
};

static const CustomData *get_cdata(bke::AttrDomain domain, const PBVH_GPU_Args &args)
{
  switch (domain) {
    case bke::AttrDomain::Point:
      return args.vert_data;
    case bke::AttrDomain::Corner:
      return args.corner_data;
    case bke::AttrDomain::Face:
      return args.face_data;
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

struct PBVHBatches {
  Vector<PBVHVbo> vbos;
  Map<std::string, PBVHBatch> batches;
  gpu::IndexBuf *tri_index = nullptr;
  gpu::IndexBuf *lines_index = nullptr;
  int faces_count = 0; /* Used by bke::pbvh::Type::BMesh and bke::pbvh::Type::Grids */
  bool use_flat_layout = false;

  int material_index = 0;

  /* Stuff for displaying coarse multires grids. */
  gpu::IndexBuf *tri_index_coarse = nullptr;
  gpu::IndexBuf *lines_index_coarse = nullptr;
  int coarse_level = 0; /* Coarse multires depth. */

  PBVHBatches(const PBVH_GPU_Args &args);
  ~PBVHBatches();

  void update(const PBVH_GPU_Args &args);
  void update_pre(const PBVH_GPU_Args &args);

  int create_vbo(const AttributeRequest &request, const PBVH_GPU_Args &args);
  int ensure_vbo(const AttributeRequest &request, const PBVH_GPU_Args &args);

  void create_index(const PBVH_GPU_Args &args);
};

static int count_visible_tris_mesh(const Span<int> tris,
                                   const Span<int> tri_faces,
                                   const Span<bool> hide_poly)
{
  if (hide_poly.is_empty()) {
    return tris.size();
  }
  return std::count_if(
      tris.begin(), tris.end(), [&](const int tri) { return !hide_poly[tri_faces[tri]]; });
}

static int count_visible_tris_bmesh(const Set<BMFace *, 0> &faces)
{
  return std::count_if(faces.begin(), faces.end(), [&](const BMFace *face) {
    return !BM_elem_flag_test_bool(face, BM_ELEM_HIDDEN);
  });
}

static int count_faces(const PBVH_GPU_Args &args)
{
  switch (args.pbvh_type) {
    case bke::pbvh::Type::Mesh:
      return count_visible_tris_mesh(args.prim_indices, args.tri_faces, args.hide_poly);
    case bke::pbvh::Type::Grids:
      return bke::pbvh::count_grid_quads(args.subdiv_ccg->grid_hidden,
                                         args.grid_indices,
                                         args.ccg_key.grid_size,
                                         args.ccg_key.grid_size);

    case bke::pbvh::Type::BMesh:
      return count_visible_tris_bmesh(*args.bm_faces);
  }
  BLI_assert_unreachable();
  return 0;
}

PBVHBatches::PBVHBatches(const PBVH_GPU_Args &args)
{
  this->faces_count = count_faces(args);
}

PBVHBatches::~PBVHBatches()
{
  for (PBVHBatch &batch : this->batches.values()) {
    GPU_BATCH_DISCARD_SAFE(batch.tris);
    GPU_BATCH_DISCARD_SAFE(batch.lines);
  }

  for (PBVHVbo &vbo : this->vbos) {
    GPU_vertbuf_discard(vbo.vert_buf);
  }

  GPU_INDEXBUF_DISCARD_SAFE(this->tri_index);
  GPU_INDEXBUF_DISCARD_SAFE(this->lines_index);
  GPU_INDEXBUF_DISCARD_SAFE(this->tri_index_coarse);
  GPU_INDEXBUF_DISCARD_SAFE(this->lines_index_coarse);
}

static std::string build_key(const Span<AttributeRequest> requests, bool do_coarse_grids)
{
  PBVHBatch batch;
  Vector<PBVHVbo> vbos;

  for (const int i : requests.index_range()) {
    const AttributeRequest &request = requests[i];
    if (!pbvh_attr_supported(request)) {
      continue;
    }
    vbos.append_as(request);
    batch.vbos.append(i);
  }

  batch.is_coarse = do_coarse_grids;
  return batch.build_key(vbos);
}

int PBVHBatches::ensure_vbo(const AttributeRequest &request, const PBVH_GPU_Args &args)
{
  for (const int i : this->vbos.index_range()) {
    if (this->vbos[i].request == request) {
      return i;
    }
  }
  return this->create_vbo(request, args);
}

static void fill_vbo_normal_mesh(const Span<int> corner_verts,
                                 const Span<int3> corner_tris,
                                 const Span<int> tri_faces,
                                 const Span<bool> sharp_faces,
                                 const Span<bool> hide_poly,
                                 const Span<float3> vert_normals,
                                 const Span<float3> face_normals,
                                 const Span<int> tris,
                                 gpu::VertBuf &vert_buf)
{
  short4 *data = vert_buf.data<short4>().data();

  short4 face_no;
  int last_face = -1;
  for (const int tri : tris) {
    const int face = tri_faces[tri];
    if (!hide_poly.is_empty() && hide_poly[face]) {
      continue;
    }
    if (!sharp_faces.is_empty() && sharp_faces[face]) {
      if (face != last_face) {
        face_no = normal_float_to_short(face_normals[face]);
        last_face = face;
      }
      std::fill_n(data, 3, face_no);
      data += 3;
    }
    else {
      for (const int i : IndexRange(3)) {
        const int vert = corner_verts[corner_tris[tri][i]];
        *data = normal_float_to_short(vert_normals[vert]);
        data++;
      }
    }
  }
}

static void fill_vbo_mask_mesh(const Span<int> corner_verts,
                               const Span<int3> corner_tris,
                               const Span<int> tri_faces,
                               const Span<bool> hide_poly,
                               const Span<float> mask,
                               const Span<int> tris,
                               gpu::VertBuf &vbo)
{
  float *data = vbo.data<float>().data();
  for (const int tri : tris) {
    if (!hide_poly.is_empty() && hide_poly[tri_faces[tri]]) {
      continue;
    }
    for (int i : IndexRange(3)) {
      const int vert = corner_verts[corner_tris[tri][i]];
      *data = mask[vert];
      data++;
    }
  }
}

static void fill_vbo_face_set_mesh(const Span<int> tri_faces,
                                   const Span<bool> hide_poly,
                                   const Span<int> face_sets,
                                   const int color_default,
                                   const int color_seed,
                                   const Span<int> tris,
                                   gpu::VertBuf &vert_buf)
{
  uchar4 *data = vert_buf.data<uchar4>().data();
  int last_face = -1;
  uchar4 fset_color(UCHAR_MAX);
  for (const int tri : tris) {
    if (!hide_poly.is_empty() && hide_poly[tri_faces[tri]]) {
      continue;
    }
    const int face = tri_faces[tri];
    if (last_face != face) {
      last_face = face;

      const int id = face_sets[face];

      if (id != color_default) {
        BKE_paint_face_set_overlay_color_get(id, color_seed, fset_color);
      }
      else {
        /* Skip for the default color face set to render it white. */
        fset_color[0] = fset_color[1] = fset_color[2] = UCHAR_MAX;
      }
    }
    std::fill_n(data, 3, fset_color);
    data += 3;
  }
}

static void fill_vbo_attribute_mesh(const Span<int> corner_verts,
                                    const Span<int3> corner_tris,
                                    const Span<int> tri_faces,
                                    const Span<bool> hide_poly,
                                    const GSpan attribute,
                                    const bke::AttrDomain domain,
                                    const Span<int> tris,
                                    gpu::VertBuf &vert_buf)
{
  bke::attribute_math::convert_to_static_type(attribute.type(), [&](auto dummy) {
    using T = decltype(dummy);
    if constexpr (!std::is_void_v<typename AttributeConverter<T>::VBOType>) {
      switch (domain) {
        case bke::AttrDomain::Point:
          extract_data_vert_mesh<T>(corner_verts,
                                    corner_tris,
                                    tri_faces,
                                    hide_poly,
                                    attribute.typed<T>(),
                                    tris,
                                    vert_buf);
          break;
        case bke::AttrDomain::Face:
          extract_data_face_mesh<T>(tri_faces, hide_poly, attribute.typed<T>(), tris, vert_buf);
          break;
        case bke::AttrDomain::Corner:
          extract_data_corner_mesh<T>(
              corner_tris, tri_faces, hide_poly, attribute.typed<T>(), tris, vert_buf);
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

static void fill_vbo_grids(PBVHVbo &vbo, const PBVH_GPU_Args &args, const bool use_flat_layout)
{
  const SubdivCCG &subdiv_ccg = *args.subdiv_ccg;
  const Span<int> grid_indices = args.grid_indices;
  const Span<CCGElem *> grids = args.grids;
  const CCGKey key = args.ccg_key;
  const int gridsize = key.grid_size;

  const int verts_per_grid = use_flat_layout ? square_i(gridsize - 1) * 4 : square_i(gridsize);
  const int vert_count = args.grid_indices.size() * verts_per_grid;

  int existing_num = GPU_vertbuf_get_vertex_len(vbo.vert_buf);

  if (vbo.vert_buf->data<uchar>().data() == nullptr || existing_num != vert_count) {
    /* Allocate buffer if not allocated yet or size changed. */
    GPU_vertbuf_data_alloc(*vbo.vert_buf, vert_count);
  }

  if (const CustomRequest *request_type = std::get_if<CustomRequest>(&vbo.request)) {
    switch (*request_type) {
      case CustomRequest::Position: {
        fill_vbo_position_grids(key, grids, use_flat_layout, grid_indices, *vbo.vert_buf);
        break;
      }
      case CustomRequest::Normal: {
        const Mesh &mesh = *args.mesh;
        const Span<int> grid_to_face_map = subdiv_ccg.grid_to_face_map;
        const bke::AttributeAccessor attributes = mesh.attributes();
        const VArraySpan sharp_faces = *attributes.lookup<bool>("sharp_face",
                                                                bke::AttrDomain::Face);
        fill_vbo_normal_grids(key,
                              grids,
                              grid_to_face_map,
                              sharp_faces,
                              use_flat_layout,
                              grid_indices,
                              *vbo.vert_buf);
        break;
      }
      case CustomRequest::Mask: {
        fill_vbo_mask_grids(key, grids, use_flat_layout, grid_indices, *vbo.vert_buf);
        break;
      }
      case CustomRequest::FaceSet: {
        const Mesh &mesh = *args.mesh;
        const int face_set_default = args.face_sets_color_default;
        const int face_set_seed = args.face_sets_color_seed;
        const Span<int> grid_to_face_map = subdiv_ccg.grid_to_face_map;
        const bke::AttributeAccessor attributes = mesh.attributes();
        if (const VArray<int> face_sets = *attributes.lookup<int>(".sculpt_face_set",
                                                                  bke::AttrDomain::Face))
        {
          const VArraySpan<int> face_sets_span(face_sets);
          fill_vbo_face_set_grids(key,
                                  grid_to_face_map,
                                  face_sets_span,
                                  face_set_default,
                                  face_set_seed,
                                  use_flat_layout,
                                  grid_indices,
                                  *vbo.vert_buf);
        }
        else {
          vbo.vert_buf->data<uchar4>().fill(uchar4{UCHAR_MAX});
        }
        break;
      }
    }
  }
  else {
    const eCustomDataType type = std::get<GenericRequest>(vbo.request).type;
    bke::attribute_math::convert_to_static_type(type, [&](auto dummy) {
      using T = decltype(dummy);
      using Converter = AttributeConverter<T>;
      using VBOType = typename Converter::VBOType;
      if constexpr (!std::is_void_v<VBOType>) {
        vbo.vert_buf->data<VBOType>().fill(Converter::convert(fallback_value_for_fill<T>()));
      }
    });
  }
}

static void fill_vbo_faces(PBVHVbo &vbo, const PBVH_GPU_Args &args)
{
  const Mesh &mesh = *args.mesh;
  const Span<int> corner_verts = args.corner_verts;
  const Span<int3> corner_tris = args.corner_tris;
  const Span<int> tri_faces = args.tri_faces;
  const Span<bool> hide_poly = args.hide_poly;

  const int totvert = count_faces(args) * 3;
  int existing_num = GPU_vertbuf_get_vertex_len(vbo.vert_buf);

  if (vbo.vert_buf->data<uchar>().data() == nullptr || existing_num != totvert) {
    /* Allocate buffer if not allocated yet or size changed. */
    GPU_vertbuf_data_alloc(*vbo.vert_buf, totvert);
  }

  gpu::VertBuf &vert_buf = *vbo.vert_buf;

  const bke::AttributeAccessor attributes = mesh.attributes();

  if (const CustomRequest *request_type = std::get_if<CustomRequest>(&vbo.request)) {
    switch (*request_type) {
      case CustomRequest::Position: {
        const Span<float3> vert_positions = args.vert_positions;
        extract_data_vert_mesh<float3>(corner_verts,
                                       corner_tris,
                                       tri_faces,
                                       hide_poly,
                                       vert_positions,
                                       args.prim_indices,
                                       vert_buf);
        break;
      }
      case CustomRequest::Normal: {
        const Span<float3> vert_normals = args.vert_normals;
        const Span<float3> face_normals = args.face_normals;
        const VArraySpan sharp_faces = *attributes.lookup<bool>("sharp_face",
                                                                bke::AttrDomain::Face);
        fill_vbo_normal_mesh(corner_verts,
                             corner_tris,
                             tri_faces,
                             sharp_faces,
                             hide_poly,
                             vert_normals,
                             face_normals,
                             args.prim_indices,
                             vert_buf);
        break;
      }
      case CustomRequest::Mask: {
        const VArraySpan mask = *attributes.lookup<float>(".sculpt_mask", bke::AttrDomain::Point);
        if (!mask.is_empty()) {
          fill_vbo_mask_mesh(
              corner_verts, corner_tris, tri_faces, hide_poly, mask, args.prim_indices, vert_buf);
        }
        else {
          vert_buf.data<float>().fill(0.0f);
        }
        break;
      }
      case CustomRequest::FaceSet: {
        const int face_set_default = args.face_sets_color_default;
        const int face_set_seed = args.face_sets_color_seed;
        const VArraySpan face_sets = *attributes.lookup<int>(".sculpt_face_set",
                                                             bke::AttrDomain::Face);
        if (!face_sets.is_empty()) {
          fill_vbo_face_set_mesh(tri_faces,
                                 hide_poly,
                                 face_sets,
                                 face_set_default,
                                 face_set_seed,
                                 args.prim_indices,
                                 vert_buf);
        }
        else {
          vert_buf.data<uchar4>().fill(uchar4(255));
        }
        break;
      }
    }
  }
  else {
    const GenericRequest &attr = std::get<GenericRequest>(vbo.request);
    const StringRef name = attr.name;
    const bke::AttrDomain domain = attr.domain;
    const eCustomDataType data_type = attr.type;
    const GVArraySpan attribute = *attributes.lookup_or_default(name, domain, data_type);
    fill_vbo_attribute_mesh(corner_verts,
                            corner_tris,
                            tri_faces,
                            hide_poly,
                            attribute,
                            domain,
                            args.prim_indices,
                            vert_buf);
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

static void fill_vbo_bmesh(PBVHVbo &vbo, const PBVH_GPU_Args &args)
{
  const BMesh &bm = *args.bm;
  int existing_num = GPU_vertbuf_get_vertex_len(vbo.vert_buf);

  int vert_count = count_faces(args) * 3;

  if (vbo.vert_buf->data<uchar>().data() == nullptr || existing_num != vert_count) {
    /* Allocate buffer if not allocated yet or size changed. */
    GPU_vertbuf_data_alloc(*vbo.vert_buf, vert_count);
  }

  if (const CustomRequest *request_type = std::get_if<CustomRequest>(&vbo.request)) {
    switch (*request_type) {
      case CustomRequest::Position: {
        fill_vbo_position_bmesh(*args.bm_faces, *vbo.vert_buf);
        break;
      }
      case CustomRequest::Normal: {
        fill_vbo_normal_bmesh(*args.bm_faces, *vbo.vert_buf);
        break;
      }
      case CustomRequest::Mask: {
        const int cd_offset = CustomData_get_offset_named(
            &bm.vdata, CD_PROP_FLOAT, ".sculpt_mask");
        if (cd_offset != -1) {
          fill_vbo_mask_bmesh(*args.bm_faces, cd_offset, *vbo.vert_buf);
        }
        else {
          vbo.vert_buf->data<float>().fill(0.0f);
        }
        break;
      }
      case CustomRequest::FaceSet: {
        const int face_set_default = args.face_sets_color_default;
        const int face_set_seed = args.face_sets_color_seed;
        const int cd_offset = CustomData_get_offset_named(
            &bm.pdata, CD_PROP_INT32, ".sculpt_face_set");
        if (cd_offset != -1) {
          fill_vbo_face_set_bmesh(
              *args.bm_faces, face_set_default, face_set_seed, cd_offset, *vbo.vert_buf);
        }
        else {
          vbo.vert_buf->data<uchar4>().fill(uchar4(255));
        }
        break;
      }
    }
  }
  else {
    const GenericRequest &attr = std::get<GenericRequest>(vbo.request);
    const bke::AttrDomain domain = attr.domain;
    const eCustomDataType data_type = attr.type;
    const CustomData &custom_data = *get_cdata(domain, args);
    const int cd_offset = CustomData_get_offset_named(&custom_data, data_type, attr.name);
    fill_vbo_attribute_bmesh(*args.bm_faces, attr.type, attr.domain, cd_offset, *vbo.vert_buf);
  }
}

void PBVHBatches::update(const PBVH_GPU_Args &args)
{
  if (!this->lines_index) {
    this->create_index(args);
  }
  for (PBVHVbo &vbo : this->vbos) {
    switch (args.pbvh_type) {
      case bke::pbvh::Type::Mesh:
        fill_vbo_faces(vbo, args);
        break;
      case bke::pbvh::Type::Grids:
        fill_vbo_grids(vbo, args, this->use_flat_layout);
        break;
      case bke::pbvh::Type::BMesh:
        fill_vbo_bmesh(vbo, args);
        break;
    }
  }
}

int PBVHBatches::create_vbo(const AttributeRequest &request, const PBVH_GPU_Args &args)
{
  const GPUVertFormat format = format_for_request(args, request);
  this->vbos.append_as(request);
  this->vbos.last().vert_buf = GPU_vertbuf_create_with_format_ex(format, GPU_USAGE_STATIC);
  switch (args.pbvh_type) {
    case bke::pbvh::Type::Mesh:
      fill_vbo_faces(vbos.last(), args);
      break;
    case bke::pbvh::Type::Grids:
      fill_vbo_grids(vbos.last(), args, this->use_flat_layout);
      break;
    case bke::pbvh::Type::BMesh:
      fill_vbo_bmesh(vbos.last(), args);
      break;
  }

  return vbos.index_range().last();
}

void PBVHBatches::update_pre(const PBVH_GPU_Args &args)
{
  if (args.pbvh_type == bke::pbvh::Type::BMesh) {
    int count = count_faces(args);

    if (this->faces_count != count) {
      for (PBVHVbo &vbo : this->vbos) {
        vbo.clear_data();
      }

      GPU_INDEXBUF_DISCARD_SAFE(this->tri_index);
      GPU_INDEXBUF_DISCARD_SAFE(this->lines_index);
      GPU_INDEXBUF_DISCARD_SAFE(this->tri_index_coarse);
      GPU_INDEXBUF_DISCARD_SAFE(this->lines_index_coarse);

      this->faces_count = count;
    }
  }
}

static gpu::IndexBuf *create_index_faces(const Span<int2> edges,
                                         const Span<int> corner_verts,
                                         const Span<int> corner_edges,
                                         const Span<int3> corner_tris,
                                         const Span<int> tri_faces,
                                         const Span<bool> hide_poly,
                                         const Span<int> tri_indices)
{
  /* Calculate number of edges. */
  int edge_count = 0;
  for (const int tri_i : tri_indices) {
    if (!hide_poly.is_empty() && hide_poly[tri_faces[tri_i]]) {
      continue;
    }
    const int3 real_edges = bke::mesh::corner_tri_get_real_edges(
        edges, corner_verts, corner_edges, corner_tris[tri_i]);
    if (real_edges[0] != -1) {
      edge_count++;
    }
    if (real_edges[1] != -1) {
      edge_count++;
    }
    if (real_edges[2] != -1) {
      edge_count++;
    }
  }

  GPUIndexBufBuilder builder;
  GPU_indexbuf_init(&builder, GPU_PRIM_LINES, edge_count, INT_MAX);
  MutableSpan<uint2> data = GPU_indexbuf_get_data(&builder).cast<uint2>();

  int edge_i = 0;
  int vert_i = 0;
  for (const int tri_i : tri_indices) {
    if (!hide_poly.is_empty() && hide_poly[tri_faces[tri_i]]) {
      continue;
    }

    const int3 real_edges = bke::mesh::corner_tri_get_real_edges(
        edges, corner_verts, corner_edges, corner_tris[tri_i]);

    if (real_edges[0] != -1) {
      data[edge_i] = uint2(vert_i, vert_i + 1);
      edge_i++;
    }
    if (real_edges[1] != -1) {
      data[edge_i] = uint2(vert_i + 1, vert_i + 2);
      edge_i++;
    }
    if (real_edges[2] != -1) {
      data[edge_i] = uint2(vert_i + 2, vert_i);
      edge_i++;
    }

    vert_i += 3;
  }

  gpu::IndexBuf *ibo = GPU_indexbuf_calloc();
  GPU_indexbuf_build_in_place_ex(&builder, 0, vert_i, false, ibo);
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

static void create_grids_index(const Span<int> grid_indices,
                               int display_gridsize,
                               GPUIndexBufBuilder &elb,
                               GPUIndexBufBuilder &elb_lines,
                               const BitGroupVector<> &grid_hidden,
                               const int gridsize,
                               const int skip,
                               const int totgrid)
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

        GPU_indexbuf_add_tri_verts(&elb, v0, v2, v1);
        GPU_indexbuf_add_tri_verts(&elb, v0, v3, v2);

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
                                                 GPUIndexBufBuilder &elb,
                                                 GPUIndexBufBuilder &elb_lines,
                                                 const BitGroupVector<> &grid_hidden,
                                                 const int gridsize,
                                                 const int skip,
                                                 const int totgrid)
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

        GPU_indexbuf_add_tri_verts(&elb, v0, v2, v1);
        GPU_indexbuf_add_tri_verts(&elb, v0, v3, v2);

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

static int calc_material_index(const PBVH_GPU_Args &args)
{
  switch (args.pbvh_type) {
    case bke::pbvh::Type::Mesh: {
      const Mesh &mesh = *args.mesh;
      const Span<int> tri_faces = args.tri_faces;
      const bke::AttributeAccessor attributes = mesh.attributes();
      const VArray material_indices = *attributes.lookup_or_default<int>(
          "material_index", bke::AttrDomain::Face, 0);
      const Span<int> tris = args.prim_indices;
      if (tris.is_empty()) {
        return 0;
      }
      return material_indices[tri_faces[tris.first()]];
    }
    case bke::pbvh::Type::Grids: {
      const Mesh &mesh = *args.mesh;
      const bke::AttributeAccessor attributes = mesh.attributes();
      const VArray material_indices = *attributes.lookup_or_default<int>(
          "material_index", bke::AttrDomain::Face, 0);
      const SubdivCCG &subdiv_ccg = *args.subdiv_ccg;
      const Span<int> grid_faces = subdiv_ccg.grid_to_face_map;
      const Span<int> grids = args.grid_indices;
      if (grids.is_empty()) {
        return 0;
      }
      return material_indices[grid_faces[grids.first()]];
    }
    case bke::pbvh::Type::BMesh:
      return 0;
  }
  BLI_assert_unreachable();
  return 0;
}

static bool calc_use_flat_layout(const PBVH_GPU_Args &args)
{
  const Mesh &mesh = *args.mesh;
  const bke::AttributeAccessor attributes = mesh.attributes();
  const VArraySpan sharp_faces = *attributes.lookup<bool>("sharp_face", bke::AttrDomain::Face);
  if (sharp_faces.is_empty()) {
    return false;
  }
  else {
    const SubdivCCG &subdiv_ccg = *args.subdiv_ccg;
    const Span<int> grid_to_face_map = subdiv_ccg.grid_to_face_map;
    const Span<int> grids = args.grid_indices;
    return std::any_of(grids.begin(), grids.end(), [&](const int grid) {
      return sharp_faces[grid_to_face_map[grid]];
    });
  }
}

static void create_index_grids(const CCGKey &key,
                               const SubdivCCG &subdiv_ccg,
                               const bool do_coarse,
                               const Span<int> grid_indices,
                               const bool use_flat_layout,
                               PBVHBatches &batches)
{
  const BitGroupVector<> &grid_hidden = subdiv_ccg.grid_hidden;

  int gridsize = key.grid_size;
  int display_gridsize = gridsize;
  int totgrid = grid_indices.size();
  int skip = 1;

  const int display_level = do_coarse ? batches.coarse_level : key.level;

  if (display_level < key.level) {
    display_gridsize = (1 << display_level) + 1;
    skip = 1 << (key.level - display_level - 1);
  }

  GPUIndexBufBuilder elb, elb_lines;

  uint visible_quad_len = bke::pbvh::count_grid_quads(
      grid_hidden, grid_indices, key.grid_size, display_gridsize);

  GPU_indexbuf_init(&elb, GPU_PRIM_TRIS, 2 * visible_quad_len, INT_MAX);
  GPU_indexbuf_init(&elb_lines,
                    GPU_PRIM_LINES,
                    2 * totgrid * display_gridsize * (display_gridsize - 1),
                    INT_MAX);

  if (use_flat_layout) {
    create_lines_index_grids_flat_layout(
        grid_indices, display_gridsize, elb, elb_lines, grid_hidden, gridsize, skip, totgrid);
  }
  else {
    create_grids_index(
        grid_indices, display_gridsize, elb, elb_lines, grid_hidden, gridsize, skip, totgrid);
  }

  if (do_coarse) {
    batches.tri_index_coarse = GPU_indexbuf_build(&elb);
    batches.lines_index_coarse = GPU_indexbuf_build(&elb_lines);
  }
  else {
    batches.tri_index = GPU_indexbuf_build(&elb);
    batches.lines_index = GPU_indexbuf_build(&elb_lines);
  }
}

void PBVHBatches::create_index(const PBVH_GPU_Args &args)
{
  switch (args.pbvh_type) {
    case bke::pbvh::Type::Mesh: {
      const Mesh &mesh = *args.mesh;
      const Span<int2> edges = mesh.edges();
      const Span<int> corner_verts = args.corner_verts;
      const Span<int> corner_edges = args.corner_edges;
      const Span<int3> corner_tris = args.corner_tris;
      const Span<int> tri_faces = args.tri_faces;
      const Span<bool> hide_poly = args.hide_poly;
      const Span<int> tris = args.prim_indices;
      this->lines_index = create_index_faces(
          edges, corner_verts, corner_edges, corner_tris, tri_faces, hide_poly, tris);
      break;
    }

    case bke::pbvh::Type::Grids: {
      this->use_flat_layout = calc_use_flat_layout(args);
      create_index_grids(
          args.ccg_key, *args.subdiv_ccg, false, args.grid_indices, this->use_flat_layout, *this);
      if (args.ccg_key.level > coarse_level) {
        create_index_grids(
            args.ccg_key, *args.subdiv_ccg, true, args.grid_indices, this->use_flat_layout, *this);
      }
      break;
    }
    case bke::pbvh::Type::BMesh: {
      this->lines_index = create_index_bmesh(*args.bm_faces, faces_count);
      break;
    }
  }

  for (PBVHBatch &batch : batches.values()) {
    if (tri_index) {
      GPU_batch_elembuf_set(batch.tris, tri_index, false);
    }
    else {
      /* Still flag the batch as dirty even if we're using the default index layout. */
      batch.tris->flag |= GPU_BATCH_DIRTY;
    }

    if (this->lines_index) {
      GPU_batch_elembuf_set(batch.lines, this->lines_index, false);
    }
  }
}

static PBVHBatch create_batch(PBVHBatches &batches,
                              const Span<AttributeRequest> requests,
                              const PBVH_GPU_Args &args,
                              bool do_coarse_grids)
{
  batches.material_index = calc_material_index(args);
  if (!batches.lines_index) {
    batches.create_index(args);
  }

  PBVHBatch batch;

  batch.tris = GPU_batch_create(GPU_PRIM_TRIS,
                                nullptr,
                                /* can be nullptr if buffer is empty */
                                do_coarse_grids ? batches.tri_index_coarse : batches.tri_index);
  batch.is_coarse = do_coarse_grids;

  if (batches.lines_index) {
    batch.lines = GPU_batch_create(GPU_PRIM_LINES,
                                   nullptr,
                                   do_coarse_grids ? batches.lines_index_coarse :
                                                     batches.lines_index);
  }

  for (const AttributeRequest &request : requests) {
    if (!pbvh_attr_supported(request)) {
      continue;
    }
    const int i = batches.ensure_vbo(request, args);
    batch.vbos.append(i);
    const PBVHVbo &vbo = batches.vbos[i];

    GPU_batch_vertbuf_add(batch.tris, vbo.vert_buf, false);
    if (batch.lines) {
      GPU_batch_vertbuf_add(batch.lines, vbo.vert_buf, false);
    }
  }

  return batch;
}

static PBVHBatch &ensure_batch(PBVHBatches &batches,
                               const Span<AttributeRequest> requests,
                               const PBVH_GPU_Args &args,
                               const bool do_coarse_grids)
{
  return batches.batches.lookup_or_add_cb(build_key(requests, do_coarse_grids), [&]() {
    return create_batch(batches, requests, args, do_coarse_grids);
  });
}

void node_update(PBVHBatches *batches, const PBVH_GPU_Args &args)
{
  batches->update(args);
}

void node_gpu_flush(PBVHBatches *batches)
{
  for (PBVHVbo &vbo : batches->vbos) {
    if (vbo.vert_buf && vbo.vert_buf->data<char>().data()) {
      GPU_vertbuf_use(vbo.vert_buf);
    }
  }
}

PBVHBatches *node_create(const PBVH_GPU_Args &args)
{
  PBVHBatches *batches = new PBVHBatches(args);
  return batches;
}

void node_free(PBVHBatches *batches)
{
  delete batches;
}

gpu::Batch *tris_get(PBVHBatches *batches,
                     const Span<AttributeRequest> attrs,
                     const PBVH_GPU_Args &args,
                     bool do_coarse_grids)
{
  do_coarse_grids &= args.pbvh_type == bke::pbvh::Type::Grids;
  PBVHBatch &batch = ensure_batch(*batches, attrs, args, do_coarse_grids);
  return batch.tris;
}

gpu::Batch *lines_get(PBVHBatches *batches,
                      const Span<AttributeRequest> attrs,
                      const PBVH_GPU_Args &args,
                      bool do_coarse_grids)
{
  do_coarse_grids &= args.pbvh_type == bke::pbvh::Type::Grids;
  PBVHBatch &batch = ensure_batch(*batches, attrs, args, do_coarse_grids);
  return batch.lines;
}

void update_pre(PBVHBatches *batches, const PBVH_GPU_Args &args)
{
  batches->update_pre(args);
}

int material_index_get(PBVHBatches *batches)
{
  return batches->material_index;
}

}  // namespace blender::draw::pbvh
