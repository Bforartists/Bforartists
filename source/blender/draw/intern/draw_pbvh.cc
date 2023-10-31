/* SPDX-FileCopyrightText: 2005 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 *
 * PBVH drawing.
 * Embeds GPU meshes inside of PBVH nodes, used by mesh sculpt mode.
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
#include "DNA_meshdata_types.h"

#include "BKE_DerivedMesh.h"
#include "BKE_attribute.hh"
#include "BKE_attribute_math.hh"
#include "BKE_ccg.h"
#include "BKE_customdata.h"
#include "BKE_mesh.hh"
#include "BKE_paint.hh"
#include "BKE_pbvh_api.hh"
#include "BKE_subdiv_ccg.hh"

#include "GPU_batch.h"

#include "DRW_engine.h"
#include "DRW_pbvh.hh"

#include "bmesh.h"
#include "draw_pbvh.h"
#include "gpu_private.h"

#define MAX_PBVH_BATCH_KEY 512
#define MAX_PBVH_VBOS 16

using blender::char3;
using blender::float2;
using blender::float3;
using blender::float4;
using blender::FunctionRef;
using blender::IndexRange;
using blender::Map;
using blender::MutableSpan;
using blender::short3;
using blender::short4;
using blender::Span;
using blender::StringRef;
using blender::StringRefNull;
using blender::uchar3;
using blender::uchar4;
using blender::ushort3;
using blender::ushort4;
using blender::Vector;

/**
 * Component length of 3 is used for scalars because implicit conversion is done by OpenGL from a
 * scalar `s` will produce `vec4(s, 0, 0, 1)`. However, following the Blender convention, it should
 * be `vec4(s, s, s, 1)`.
 */
constexpr int COMPONENT_LEN_SCALAR = 3;

namespace blender::draw {

/** Similar to #AttributeTypeConverter. */
template<typename T> struct AttributeConverter {
  using VBOT = void;
};

template<> struct AttributeConverter<bool> {
  using VBOT = VecBase<int, COMPONENT_LEN_SCALAR>;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_I32;
  static constexpr int gpu_component_len = COMPONENT_LEN_SCALAR;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_INT_TO_FLOAT;
  static VBOT convert(const bool &value)
  {
    return VBOT(value);
  }
};
template<> struct AttributeConverter<int8_t> {
  using VBOT = VecBase<int, COMPONENT_LEN_SCALAR>;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_I32;
  static constexpr int gpu_component_len = COMPONENT_LEN_SCALAR;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_INT_TO_FLOAT;
  static VBOT convert(const int8_t &value)
  {
    return VecBase<int, COMPONENT_LEN_SCALAR>(value);
  }
};
template<> struct AttributeConverter<int> {
  using VBOT = VecBase<int, COMPONENT_LEN_SCALAR>;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_I32;
  static constexpr int gpu_component_len = COMPONENT_LEN_SCALAR;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_INT_TO_FLOAT;
  static VBOT convert(const int &value)
  {
    return int3(value);
  }
};
template<> struct AttributeConverter<int2> {
  using VBOT = int2;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_I32;
  static constexpr int gpu_component_len = 2;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_INT_TO_FLOAT;
  static VBOT convert(const int2 &value)
  {
    return int2(value.x, value.y);
  }
};
template<> struct AttributeConverter<float> {
  using VBOT = VecBase<float, COMPONENT_LEN_SCALAR>;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_F32;
  static constexpr int gpu_component_len = COMPONENT_LEN_SCALAR;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_FLOAT;
  static VBOT convert(const float &value)
  {
    return VBOT(value);
  }
};
template<> struct AttributeConverter<float2> {
  using VBOT = float2;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_F32;
  static constexpr int gpu_component_len = 2;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_FLOAT;
  static VBOT convert(const float2 &value)
  {
    return value;
  }
};
template<> struct AttributeConverter<float3> {
  using VBOT = float3;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_F32;
  static constexpr int gpu_component_len = 3;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_FLOAT;
  static VBOT convert(const float3 &value)
  {
    return value;
  }
};
template<> struct AttributeConverter<ColorGeometry4b> {
  /* 16 bits are required to store the color in linear space without precision loss. */
  using VBOT = ushort4;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_U16;
  static constexpr int gpu_component_len = 4;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_INT_TO_FLOAT_UNIT;
  static VBOT convert(const ColorGeometry4b &value)
  {
    return {unit_float_to_ushort_clamp(BLI_color_from_srgb_table[value.r]),
            unit_float_to_ushort_clamp(BLI_color_from_srgb_table[value.g]),
            unit_float_to_ushort_clamp(BLI_color_from_srgb_table[value.b]),
            ushort(value.a * 257)};
  }
};
template<> struct AttributeConverter<ColorGeometry4f> {
  using VBOT = ColorGeometry4f;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_F32;
  static constexpr int gpu_component_len = 4;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_FLOAT;
  static VBOT convert(const ColorGeometry4f &value)
  {
    return value;
  }
};
template<> struct AttributeConverter<blender::math::Quaternion> {
  using VBOT = float4;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_F32;
  static constexpr int gpu_component_len = 4;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_FLOAT;
  static VBOT convert(const blender::math::Quaternion &value)
  {
    return float4(value.w, value.x, value.y, value.z);
  }
};

}  // namespace blender::draw

static bool pbvh_attr_supported(int type, const eAttrDomain domain)
{
  using namespace blender;
  if (!ELEM(domain, ATTR_DOMAIN_POINT, ATTR_DOMAIN_FACE, ATTR_DOMAIN_CORNER)) {
    /* PBVH drawing does not support edge domain attributes. */
    return false;
  }
  if (ELEM(type, CD_PBVH_CO_TYPE, CD_PBVH_NO_TYPE, CD_PBVH_FSET_TYPE, CD_PBVH_MASK_TYPE)) {
    return true;
  }
  bool type_supported = false;
  bke::attribute_math::convert_to_static_type(eCustomDataType(type), [&](auto dummy) {
    using T = decltype(dummy);
    using Converter = draw::AttributeConverter<T>;
    using VBOT = typename Converter::VBOT;
    if constexpr (!std::is_void_v<VBOT>) {
      type_supported = true;
    }
  });
  return type_supported;
}

struct PBVHVbo {
  uint64_t type;
  eAttrDomain domain;
  std::string name;
  GPUVertBuf *vert_buf = nullptr;
  std::string key;

  PBVHVbo(eAttrDomain domain, uint64_t type, std::string name)
      : type(type), domain(domain), name(std::move(name))
  {
  }

  void clear_data()
  {
    GPU_vertbuf_clear(vert_buf);
  }

  void build_key()
  {
    char buf[512];

    SNPRINTF(buf, "%d:%d:%s", int(type), int(domain), name.c_str());

    key = std::string(buf);
  }
};

inline short4 normal_float_to_short(const float3 &value)
{
  short3 result;
  normal_float_to_short_v3(result, value);
  return short4(result.x, result.y, result.z, 0);
}

template<typename T>
void extract_data_vert_faces(const PBVH_GPU_Args &args, const Span<T> attribute, GPUVertBuf &vbo)
{
  using Converter = blender::draw::AttributeConverter<T>;
  using VBOT = typename Converter::VBOT;
  const Span<int> corner_verts = args.corner_verts;
  const Span<MLoopTri> looptris = args.mlooptri;
  const Span<int> looptri_faces = args.looptri_faces;
  const bool *hide_poly = args.hide_poly;

  VBOT *data = static_cast<VBOT *>(GPU_vertbuf_get_data(&vbo));
  for (const int looptri_i : args.prim_indices) {
    if (hide_poly && hide_poly[looptri_faces[looptri_i]]) {
      continue;
    }
    for (int i : IndexRange(3)) {
      const int vert = corner_verts[looptris[looptri_i].tri[i]];
      *data = Converter::convert(attribute[vert]);
      data++;
    }
  }
}

template<typename T>
void extract_data_face_faces(const PBVH_GPU_Args &args, const Span<T> attribute, GPUVertBuf &vbo)
{
  using Converter = blender::draw::AttributeConverter<T>;
  using VBOT = typename Converter::VBOT;

  const Span<int> looptri_faces = args.looptri_faces;
  const bool *hide_poly = args.hide_poly;

  VBOT *data = static_cast<VBOT *>(GPU_vertbuf_get_data(&vbo));
  for (const int looptri_i : args.prim_indices) {
    const int face = looptri_faces[looptri_i];
    if (hide_poly && hide_poly[face]) {
      continue;
    }
    std::fill_n(data, 3, Converter::convert(attribute[face]));
    data += 3;
  }
}

template<typename T>
void extract_data_corner_faces(const PBVH_GPU_Args &args, const Span<T> attribute, GPUVertBuf &vbo)
{
  using Converter = blender::draw::AttributeConverter<T>;
  using VBOT = typename Converter::VBOT;

  const Span<MLoopTri> looptris = args.mlooptri;
  const Span<int> looptri_faces = args.looptri_faces;
  const bool *hide_poly = args.hide_poly;

  VBOT *data = static_cast<VBOT *>(GPU_vertbuf_get_data(&vbo));
  for (const int looptri_i : args.prim_indices) {
    if (hide_poly && hide_poly[looptri_faces[looptri_i]]) {
      continue;
    }
    for (int i : IndexRange(3)) {
      const int corner = looptris[looptri_i].tri[i];
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
void extract_data_vert_bmesh(const PBVH_GPU_Args &args, const int cd_offset, GPUVertBuf &vbo)
{
  using Converter = blender::draw::AttributeConverter<T>;
  using VBOT = typename Converter::VBOT;
  VBOT *data = static_cast<VBOT *>(GPU_vertbuf_get_data(&vbo));

  for (const BMFace *f : *args.bm_faces) {
    if (BM_elem_flag_test(f, BM_ELEM_HIDDEN)) {
      continue;
    }
    const BMLoop *l = f->l_first;
    *data = Converter::convert(bmesh_cd_vert_get<T>(*l->prev->v, cd_offset));
    data++;
    *data = Converter::convert(bmesh_cd_vert_get<T>(*l->v, cd_offset));
    data++;
    *data = Converter::convert(bmesh_cd_vert_get<T>(*l->next->v, cd_offset));
    data++;
  }
}

template<typename T>
void extract_data_face_bmesh(const PBVH_GPU_Args &args, const int cd_offset, GPUVertBuf &vbo)
{
  using Converter = blender::draw::AttributeConverter<T>;
  using VBOT = typename Converter::VBOT;
  VBOT *data = static_cast<VBOT *>(GPU_vertbuf_get_data(&vbo));

  for (const BMFace *f : *args.bm_faces) {
    if (BM_elem_flag_test(f, BM_ELEM_HIDDEN)) {
      continue;
    }
    std::fill_n(data, 3, Converter::convert(bmesh_cd_face_get<T>(*f, cd_offset)));
    data += 3;
  }
}

template<typename T>
void extract_data_corner_bmesh(const PBVH_GPU_Args &args, const int cd_offset, GPUVertBuf &vbo)
{
  using Converter = blender::draw::AttributeConverter<T>;
  using VBOT = typename Converter::VBOT;
  VBOT *data = static_cast<VBOT *>(GPU_vertbuf_get_data(&vbo));

  for (const BMFace *f : *args.bm_faces) {
    if (BM_elem_flag_test(f, BM_ELEM_HIDDEN)) {
      continue;
    }
    const BMLoop *l = f->l_first;
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
  GPUBatch *tris = nullptr, *lines = nullptr;
  int tris_count = 0, lines_count = 0;
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

static const CustomData *get_cdata(eAttrDomain domain, const PBVH_GPU_Args &args)
{
  switch (domain) {
    case ATTR_DOMAIN_POINT:
      return args.vert_data;
    case ATTR_DOMAIN_CORNER:
      return args.loop_data;
    case ATTR_DOMAIN_FACE:
      return args.face_data;
    default:
      return nullptr;
  }
}

struct PBVHBatches {
  Vector<PBVHVbo> vbos;
  Map<std::string, PBVHBatch> batches;
  GPUIndexBuf *tri_index = nullptr;
  GPUIndexBuf *lines_index = nullptr;
  int faces_count = 0; /* Used by PBVH_BMESH and PBVH_GRIDS */
  int tris_count = 0, lines_count = 0;
  bool needs_tri_index = false;

  int material_index = 0;

  /* Stuff for displaying coarse multires grids. */
  GPUIndexBuf *tri_index_coarse = nullptr;
  GPUIndexBuf *lines_index_coarse = nullptr;
  int coarse_level = 0; /* Coarse multires depth. */
  int tris_count_coarse = 0, lines_count_coarse = 0;

  int count_faces(const PBVH_GPU_Args &args)
  {
    int count = 0;

    switch (args.pbvh_type) {
      case PBVH_FACES: {
        if (args.hide_poly) {
          for (const int looptri_i : args.prim_indices) {
            if (!args.hide_poly[args.looptri_faces[looptri_i]]) {
              count++;
            }
          }
        }
        else {
          count = args.prim_indices.size();
        }
        break;
      }
      case PBVH_GRIDS: {
        count = BKE_pbvh_count_grid_quads((BLI_bitmap **)args.grid_hidden,
                                          args.grid_indices.data(),
                                          args.grid_indices.size(),
                                          args.ccg_key.grid_size,
                                          args.ccg_key.grid_size);

        break;
      }
      case PBVH_BMESH: {
        for (const BMFace *f : *args.bm_faces) {
          if (!BM_elem_flag_test(f, BM_ELEM_HIDDEN)) {
            count++;
          }
        }
      }
    }

    return count;
  }

  PBVHBatches(const PBVH_GPU_Args &args)
  {
    faces_count = count_faces(args);

    if (args.pbvh_type == PBVH_BMESH) {
      tris_count = faces_count;
    }
  }

  ~PBVHBatches()
  {
    for (PBVHBatch &batch : batches.values()) {
      GPU_BATCH_DISCARD_SAFE(batch.tris);
      GPU_BATCH_DISCARD_SAFE(batch.lines);
    }

    for (PBVHVbo &vbo : vbos) {
      GPU_vertbuf_discard(vbo.vert_buf);
    }

    GPU_INDEXBUF_DISCARD_SAFE(tri_index);
    GPU_INDEXBUF_DISCARD_SAFE(lines_index);
    GPU_INDEXBUF_DISCARD_SAFE(tri_index_coarse);
    GPU_INDEXBUF_DISCARD_SAFE(lines_index_coarse);
  }

  std::string build_key(PBVHAttrReq *attrs, int attrs_num, bool do_coarse_grids)
  {
    PBVHBatch batch;
    Vector<PBVHVbo> vbos;

    for (int i : IndexRange(attrs_num)) {
      PBVHAttrReq *attr = attrs + i;

      if (!pbvh_attr_supported(attr->type, attr->domain)) {
        continue;
      }

      PBVHVbo vbo(attr->domain, attr->type, std::string(attr->name));
      vbo.build_key();

      vbos.append(vbo);
      batch.vbos.append(i);
    }

    batch.is_coarse = do_coarse_grids;
    return batch.build_key(vbos);
  }

  bool has_vbo(eAttrDomain domain, int type, const StringRef name)
  {
    for (PBVHVbo &vbo : vbos) {
      if (vbo.domain == domain && vbo.type == type && vbo.name == name) {
        return true;
      }
    }

    return false;
  }

  int get_vbo_index(PBVHVbo *vbo)
  {
    for (int i : IndexRange(vbos.size())) {
      if (vbo == &vbos[i]) {
        return i;
      }
    }

    return -1;
  }

  PBVHVbo *get_vbo(eAttrDomain domain, int type, const StringRef name)
  {
    for (PBVHVbo &vbo : vbos) {
      if (vbo.domain == domain && vbo.type == type && vbo.name == name) {
        return &vbo;
      }
    }

    return nullptr;
  }

  bool has_batch(PBVHAttrReq *attrs, int attrs_num, bool do_coarse_grids)
  {
    return batches.contains(build_key(attrs, attrs_num, do_coarse_grids));
  }

  PBVHBatch &ensure_batch(PBVHAttrReq *attrs,
                          int attrs_num,
                          const PBVH_GPU_Args &args,
                          bool do_coarse_grids)
  {
    if (!has_batch(attrs, attrs_num, do_coarse_grids)) {
      create_batch(attrs, attrs_num, args, do_coarse_grids);
    }

    return batches.lookup(build_key(attrs, attrs_num, do_coarse_grids));
  }

  void fill_vbo_normal_faces(const PBVH_GPU_Args &args, GPUVertBuf &vert_buf)
  {
    const bool *sharp_faces = static_cast<const bool *>(
        CustomData_get_layer_named(args.face_data, CD_PROP_BOOL, "sharp_face"));
    short4 *data = static_cast<short4 *>(GPU_vertbuf_get_data(&vert_buf));

    short4 face_no;
    int last_face = -1;
    for (const int looptri_i : args.prim_indices) {
      const int face_i = args.looptri_faces[looptri_i];
      if (args.hide_poly && args.hide_poly[face_i]) {
        continue;
      }
      if (sharp_faces && sharp_faces[face_i]) {
        if (face_i != last_face) {
          face_no = normal_float_to_short(args.face_normals[face_i]);
          last_face = face_i;
        }
        std::fill_n(data, 3, face_no);
        data += 3;
      }
      else {
        for (const int i : IndexRange(3)) {
          const int vert = args.corner_verts[args.mlooptri[looptri_i].tri[i]];
          *data = normal_float_to_short(args.vert_normals[vert]);
          data++;
        }
      }
    }
  }

  void fill_vbo_grids_intern(
      PBVHVbo &vbo,
      const PBVH_GPU_Args &args,
      FunctionRef<void(FunctionRef<void(int x, int y, int grid_index, CCGElem *elems[4], int i)>
                           func)> foreach_grids)
  {
    using namespace blender;
    uint vert_per_grid = square_i(args.ccg_key.grid_size - 1) * 4;
    uint vert_count = args.grid_indices.size() * vert_per_grid;

    int existing_num = GPU_vertbuf_get_vertex_len(vbo.vert_buf);
    void *existing_data = GPU_vertbuf_get_data(vbo.vert_buf);

    if (existing_data == nullptr || existing_num != vert_count) {
      /* Allocate buffer if not allocated yet or size changed. */
      GPU_vertbuf_data_alloc(vbo.vert_buf, vert_count);
    }

    GPUVertBufRaw access;
    GPU_vertbuf_attr_get_raw_data(vbo.vert_buf, 0, &access);

    if (vbo.type == CD_PBVH_CO_TYPE) {
      foreach_grids([&](int /*x*/, int /*y*/, int /*grid_index*/, CCGElem *elems[4], int i) {
        float *co = CCG_elem_co(&args.ccg_key, elems[i]);

        *static_cast<float3 *>(GPU_vertbuf_raw_step(&access)) = co;
      });
    }
    else if (vbo.type == CD_PBVH_NO_TYPE) {
      foreach_grids([&](int /*x*/, int /*y*/, int grid_index, CCGElem *elems[4], int /*i*/) {
        float3 no(0.0f, 0.0f, 0.0f);

        const bool smooth = !args.grid_flag_mats[grid_index].sharp;

        if (smooth) {
          no = CCG_elem_no(&args.ccg_key, elems[0]);
        }
        else {
          normal_quad_v3(no,
                         CCG_elem_co(&args.ccg_key, elems[3]),
                         CCG_elem_co(&args.ccg_key, elems[2]),
                         CCG_elem_co(&args.ccg_key, elems[1]),
                         CCG_elem_co(&args.ccg_key, elems[0]));
        }

        short sno[3];

        normal_float_to_short_v3(sno, no);

        *static_cast<short3 *>(GPU_vertbuf_raw_step(&access)) = sno;
      });
    }
    else if (vbo.type == CD_PBVH_MASK_TYPE) {
      if (args.ccg_key.has_mask) {
        foreach_grids([&](int /*x*/, int /*y*/, int /*grid_index*/, CCGElem *elems[4], int i) {
          float *mask = CCG_elem_mask(&args.ccg_key, elems[i]);

          *static_cast<float *>(GPU_vertbuf_raw_step(&access)) = *mask;
        });
      }
      else {
        foreach_grids(
            [&](int /*x*/, int /*y*/, int /*grid_index*/, CCGElem * /*elems*/[4], int /*i*/) {
              *static_cast<uchar *>(GPU_vertbuf_raw_step(&access)) = 0;
            });
      }
    }
    else if (vbo.type == CD_PBVH_FSET_TYPE) {
      const int *face_sets = args.face_sets;

      if (!face_sets) {
        uchar white[3] = {UCHAR_MAX, UCHAR_MAX, UCHAR_MAX};

        foreach_grids(
            [&](int /*x*/, int /*y*/, int /*grid_index*/, CCGElem * /*elems*/[4], int /*i*/) {
              *static_cast<uchar3 *>(GPU_vertbuf_raw_step(&access)) = white;
            });
      }
      else {
        foreach_grids(
            [&](int /*x*/, int /*y*/, int grid_index, CCGElem * /*elems*/[4], int /*i*/) {
              uchar face_set_color[4] = {UCHAR_MAX, UCHAR_MAX, UCHAR_MAX, UCHAR_MAX};

              if (face_sets) {
                const int face_index = BKE_subdiv_ccg_grid_to_face_index(args.subdiv_ccg,
                                                                         grid_index);
                const int fset = face_sets[face_index];

                /* Skip for the default color Face Set to render it white. */
                if (fset != args.face_sets_color_default) {
                  BKE_paint_face_set_overlay_color_get(
                      fset, args.face_sets_color_seed, face_set_color);
                }
              }

              *static_cast<uchar3 *>(GPU_vertbuf_raw_step(&access)) = face_set_color;
            });
      }
    }
    else {
      bke::attribute_math::convert_to_static_type(eCustomDataType(vbo.type), [&](auto dummy) {
        using T = decltype(dummy);
        using Converter = draw::AttributeConverter<T>;
        using VBOT = typename Converter::VBOT;
        std::fill_n(static_cast<VBOT *>(GPU_vertbuf_get_data(vbo.vert_buf)),
                    GPU_vertbuf_get_vertex_len(vbo.vert_buf),
                    VBOT());
      });
    }
  }

  void fill_vbo_grids(PBVHVbo &vbo, const PBVH_GPU_Args &args)
  {
    int gridsize = args.ccg_key.grid_size;

    uint totgrid = args.grid_indices.size();

    auto foreach_solid =
        [&](FunctionRef<void(int x, int y, int grid_index, CCGElem *elems[4], int i)> func) {
          for (int i = 0; i < totgrid; i++) {
            const int grid_index = args.grid_indices[i];

            CCGElem *grid = args.grids[grid_index];

            for (int y = 0; y < gridsize - 1; y++) {
              for (int x = 0; x < gridsize - 1; x++) {
                CCGElem *elems[4] = {
                    CCG_grid_elem(&args.ccg_key, grid, x, y),
                    CCG_grid_elem(&args.ccg_key, grid, x + 1, y),
                    CCG_grid_elem(&args.ccg_key, grid, x + 1, y + 1),
                    CCG_grid_elem(&args.ccg_key, grid, x, y + 1),
                };

                func(x, y, grid_index, elems, 0);
                func(x + 1, y, grid_index, elems, 1);
                func(x + 1, y + 1, grid_index, elems, 2);
                func(x, y + 1, grid_index, elems, 3);
              }
            }
          }
        };

    auto foreach_indexed =
        [&](FunctionRef<void(int x, int y, int grid_index, CCGElem *elems[4], int i)> func) {
          for (int i = 0; i < totgrid; i++) {
            const int grid_index = args.grid_indices[i];

            CCGElem *grid = args.grids[grid_index];

            for (int y = 0; y < gridsize; y++) {
              for (int x = 0; x < gridsize; x++) {
                CCGElem *elems[4] = {
                    CCG_grid_elem(&args.ccg_key, grid, x, y),
                    CCG_grid_elem(&args.ccg_key, grid, min_ii(x + 1, gridsize - 1), y),
                    CCG_grid_elem(&args.ccg_key,
                                  grid,
                                  min_ii(x + 1, gridsize - 1),
                                  min_ii(y + 1, gridsize - 1)),
                    CCG_grid_elem(&args.ccg_key, grid, x, min_ii(y + 1, gridsize - 1)),
                };

                func(x, y, grid_index, elems, 0);
              }
            }
          }
        };

    if (needs_tri_index) {
      fill_vbo_grids_intern(vbo, args, foreach_indexed);
    }
    else {
      fill_vbo_grids_intern(vbo, args, foreach_solid);
    }
  }

  void fill_vbo_faces(PBVHVbo &vbo, const PBVH_GPU_Args &args)
  {
    using namespace blender;
    const int totvert = this->count_faces(args) * 3;

    int existing_num = GPU_vertbuf_get_vertex_len(vbo.vert_buf);
    void *existing_data = GPU_vertbuf_get_data(vbo.vert_buf);

    if (existing_data == nullptr || existing_num != totvert) {
      /* Allocate buffer if not allocated yet or size changed. */
      GPU_vertbuf_data_alloc(vbo.vert_buf, totvert);
    }

    GPUVertBuf &vert_buf = *vbo.vert_buf;

    if (vbo.type == CD_PBVH_CO_TYPE) {
      extract_data_vert_faces<float3>(args, args.vert_positions, vert_buf);
    }
    else if (vbo.type == CD_PBVH_NO_TYPE) {
      fill_vbo_normal_faces(args, vert_buf);
    }
    else if (vbo.type == CD_PBVH_MASK_TYPE) {
      if (const float *mask = static_cast<const float *>(
              CustomData_get_layer(args.vert_data, CD_PAINT_MASK)))
      {
        const Span<int> corner_verts = args.corner_verts;
        const Span<MLoopTri> looptris = args.mlooptri;
        const Span<int> looptri_faces = args.looptri_faces;
        const bool *hide_poly = args.hide_poly;

        float *data = static_cast<float *>(GPU_vertbuf_get_data(&vert_buf));
        for (const int looptri_i : args.prim_indices) {
          if (hide_poly && hide_poly[looptri_faces[looptri_i]]) {
            continue;
          }
          for (int i : IndexRange(3)) {
            const int vert = corner_verts[looptris[looptri_i].tri[i]];
            *data = mask[vert];
            data++;
          }
        }
      }
      else {
        MutableSpan(static_cast<float *>(GPU_vertbuf_get_data(vbo.vert_buf)), totvert).fill(0);
      }
    }
    else if (vbo.type == CD_PBVH_FSET_TYPE) {
      const int *face_sets = static_cast<const int *>(
          CustomData_get_layer_named(args.face_data, CD_PROP_INT32, ".sculpt_face_set"));
      uchar4 *data = static_cast<uchar4 *>(GPU_vertbuf_get_data(vbo.vert_buf));
      if (face_sets) {
        int last_face = -1;
        uchar4 fset_color(UCHAR_MAX);

        for (const int looptri_i : args.prim_indices) {
          if (args.hide_poly && args.hide_poly[args.looptri_faces[looptri_i]]) {
            continue;
          }
          const int face_i = args.looptri_faces[looptri_i];
          if (last_face != face_i) {
            last_face = face_i;

            const int fset = face_sets[face_i];

            if (fset != args.face_sets_color_default) {
              BKE_paint_face_set_overlay_color_get(fset, args.face_sets_color_seed, fset_color);
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
      else {
        MutableSpan(data, totvert).fill(uchar4(255));
      }
    }
    else {
      const bke::AttributeAccessor attributes = args.me->attributes();
      const eCustomDataType data_type = eCustomDataType(vbo.type);
      const GVArraySpan attribute = *attributes.lookup_or_default(vbo.name, vbo.domain, data_type);
      bke::attribute_math::convert_to_static_type(data_type, [&](auto dummy) {
        using T = decltype(dummy);
        switch (vbo.domain) {
          case ATTR_DOMAIN_POINT:
            extract_data_vert_faces<T>(args, attribute.typed<T>(), vert_buf);
            break;
          case ATTR_DOMAIN_FACE:
            extract_data_face_faces<T>(args, attribute.typed<T>(), vert_buf);
            break;
          case ATTR_DOMAIN_CORNER:
            extract_data_corner_faces<T>(args, attribute.typed<T>(), vert_buf);
            break;
          default:
            BLI_assert_unreachable();
        }
      });
    }
  }

  void gpu_flush()
  {
    for (PBVHVbo &vbo : vbos) {
      if (vbo.vert_buf && GPU_vertbuf_get_data(vbo.vert_buf)) {
        GPU_vertbuf_use(vbo.vert_buf);
      }
    }
  }

  void update(const PBVH_GPU_Args &args)
  {
    check_index_buffers(args);

    for (PBVHVbo &vbo : vbos) {
      fill_vbo(vbo, args);
    }
  }

  void fill_vbo_bmesh(PBVHVbo &vbo, const PBVH_GPU_Args &args)
  {
    using namespace blender;
    faces_count = tris_count = count_faces(args);

    int existing_num = GPU_vertbuf_get_vertex_len(vbo.vert_buf);
    void *existing_data = GPU_vertbuf_get_data(vbo.vert_buf);

    int vert_count = tris_count * 3;

    if (existing_data == nullptr || existing_num != vert_count) {
      /* Allocate buffer if not allocated yet or size changed. */
      GPU_vertbuf_data_alloc(vbo.vert_buf, vert_count);
    }

    GPUVertBufRaw access;
    GPU_vertbuf_attr_get_raw_data(vbo.vert_buf, 0, &access);

#if 0 /* Enable to fuzz GPU data (to check for over-allocation). */
    existing_data = GPU_vertbuf_get_data(vbo.vert_buf);
    uchar *c = static_cast<uchar *>(existing_data);
    for (int i : IndexRange(vert_count * access.stride)) {
      *c++ = i & 255;
    }
#endif

    if (vbo.type == CD_PBVH_CO_TYPE) {
      float3 *data = static_cast<float3 *>(GPU_vertbuf_get_data(vbo.vert_buf));
      for (const BMFace *f : *args.bm_faces) {
        if (BM_elem_flag_test(f, BM_ELEM_HIDDEN)) {
          continue;
        }
        const BMLoop *l = f->l_first;
        *data = l->prev->v->co;
        data++;
        *data = l->v->co;
        data++;
        *data = l->next->v->co;
        data++;
      }
    }
    else if (vbo.type == CD_PBVH_NO_TYPE) {
      short4 *data = static_cast<short4 *>(GPU_vertbuf_get_data(vbo.vert_buf));
      for (const BMFace *f : *args.bm_faces) {
        if (BM_elem_flag_test(f, BM_ELEM_HIDDEN)) {
          continue;
        }
        if (BM_elem_flag_test(f, BM_ELEM_SMOOTH)) {
          const BMLoop *l = f->l_first;
          *data = normal_float_to_short(l->prev->v->no);
          data++;
          *data = normal_float_to_short(l->v->no);
          data++;
          *data = normal_float_to_short(l->next->v->no);
          data++;
        }
        else {
          std::fill_n(data, 3, normal_float_to_short(f->no));
          data += 3;
        }
      }
    }
    else if (vbo.type == CD_PBVH_MASK_TYPE) {
      const int cd_offset = args.cd_mask_layer;
      if (cd_offset != -1) {
        float *data = static_cast<float *>(GPU_vertbuf_get_data(vbo.vert_buf));

        for (const BMFace *f : *args.bm_faces) {
          if (BM_elem_flag_test(f, BM_ELEM_HIDDEN)) {
            continue;
          }
          const BMLoop *l = f->l_first;
          *data = bmesh_cd_vert_get<float>(*l->prev->v, cd_offset);
          data++;
          *data = bmesh_cd_vert_get<float>(*l->v, cd_offset);
          data++;
          *data = bmesh_cd_vert_get<float>(*l->next->v, cd_offset);
          data++;
        }
      }
      else {
        MutableSpan(static_cast<float *>(GPU_vertbuf_get_data(vbo.vert_buf)),
                    GPU_vertbuf_get_vertex_len(vbo.vert_buf))
            .fill(0.0f);
      }
    }
    else if (vbo.type == CD_PBVH_FSET_TYPE) {
      BLI_assert(vbo.domain == ATTR_DOMAIN_FACE);

      const int cd_offset = CustomData_get_offset_named(
          &args.bm->pdata, CD_PROP_INT32, ".sculpt_face_set");

      uchar4 *data = static_cast<uchar4 *>(GPU_vertbuf_get_data(vbo.vert_buf));
      if (cd_offset != -1) {
        for (const BMFace *f : *args.bm_faces) {
          if (BM_elem_flag_test(f, BM_ELEM_HIDDEN)) {
            continue;
          }

          const int fset = bmesh_cd_face_get<int>(*f, cd_offset);

          uchar4 fset_color;
          if (fset != args.face_sets_color_default) {
            BKE_paint_face_set_overlay_color_get(fset, args.face_sets_color_seed, fset_color);
          }
          else {
            /* Skip for the default color face set to render it white. */
            fset_color[0] = fset_color[1] = fset_color[2] = UCHAR_MAX;
          }
          std::fill_n(data, 3, fset_color);
          data += 3;
        }
      }
      else {
        MutableSpan(data, GPU_vertbuf_get_vertex_len(vbo.vert_buf)).fill(uchar4(255));
      }
    }
    else {
      const eCustomDataType type = eCustomDataType(vbo.type);
      const CustomData &custom_data = *get_cdata(vbo.domain, args);
      const int cd_offset = CustomData_get_offset_named(&custom_data, type, vbo.name.c_str());

      bke::attribute_math::convert_to_static_type(eCustomDataType(vbo.type), [&](auto dummy) {
        using T = decltype(dummy);
        switch (vbo.domain) {
          case ATTR_DOMAIN_POINT:
            extract_data_vert_bmesh<T>(args, cd_offset, *vbo.vert_buf);
            break;
          case ATTR_DOMAIN_FACE:
            extract_data_face_bmesh<T>(args, cd_offset, *vbo.vert_buf);
            break;
          case ATTR_DOMAIN_CORNER:
            extract_data_corner_bmesh<T>(args, cd_offset, *vbo.vert_buf);
            break;
          default:
            BLI_assert_unreachable();
        }
      });
    }
  }

  void fill_vbo(PBVHVbo &vbo, const PBVH_GPU_Args &args)
  {
    switch (args.pbvh_type) {
      case PBVH_FACES:
        fill_vbo_faces(vbo, args);
        break;
      case PBVH_GRIDS:
        fill_vbo_grids(vbo, args);
        break;
      case PBVH_BMESH:
        fill_vbo_bmesh(vbo, args);
        break;
    }
  }

  void create_vbo(eAttrDomain domain,
                  const uint32_t type,
                  const StringRefNull name,
                  const PBVH_GPU_Args &args)
  {
    using namespace blender;
    PBVHVbo vbo(domain, type, name);
    GPUVertFormat format;

    bool need_aliases = !ELEM(
        type, CD_PBVH_CO_TYPE, CD_PBVH_NO_TYPE, CD_PBVH_FSET_TYPE, CD_PBVH_MASK_TYPE);

    GPU_vertformat_clear(&format);

    if (type == CD_PBVH_CO_TYPE) {
      GPU_vertformat_attr_add(&format, "pos", GPU_COMP_F32, 3, GPU_FETCH_FLOAT);
    }
    else if (type == CD_PBVH_NO_TYPE) {
      GPU_vertformat_attr_add(&format, "nor", GPU_COMP_I16, 3, GPU_FETCH_INT_TO_FLOAT_UNIT);
    }
    else if (type == CD_PBVH_FSET_TYPE) {
      GPU_vertformat_attr_add(&format, "fset", GPU_COMP_U8, 3, GPU_FETCH_INT_TO_FLOAT_UNIT);
    }
    else if (type == CD_PBVH_MASK_TYPE) {
      GPU_vertformat_attr_add(&format, "msk", GPU_COMP_F32, 1, GPU_FETCH_FLOAT);
    }
    else {
      bke::attribute_math::convert_to_static_type(eCustomDataType(type), [&](auto dummy) {
        using T = decltype(dummy);
        using Converter = draw::AttributeConverter<T>;
        GPU_vertformat_attr_add(&format,
                                "data",
                                Converter::gpu_component_type,
                                Converter::gpu_component_len,
                                Converter::gpu_fetch_mode);
      });
      need_aliases = true;
    }

    if (need_aliases) {
      const CustomData *cdata = get_cdata(domain, args);
      int layer_i = cdata ? CustomData_get_named_layer_index(
                                cdata, eCustomDataType(type), name.c_str()) :
                            -1;
      CustomDataLayer *layer = layer_i != -1 ? cdata->layers + layer_i : nullptr;

      if (layer) {
        bool is_render, is_active;
        const char *prefix = "a";

        if (ELEM(type, CD_PROP_COLOR, CD_PROP_BYTE_COLOR)) {
          prefix = "c";
          is_active = StringRef(args.active_color) == layer->name;
          is_render = StringRef(args.render_color) == layer->name;
        }
        else {
          switch (type) {
            case CD_PROP_FLOAT2:
              prefix = "u";
              break;
            default:
              break;
          }

          const char *active_name = CustomData_get_active_layer_name(cdata, eCustomDataType(type));
          const char *render_name = CustomData_get_render_layer_name(cdata, eCustomDataType(type));

          is_active = active_name && STREQ(layer->name, active_name);
          is_render = render_name && STREQ(layer->name, render_name);
        }

        DRW_cdlayer_attr_aliases_add(&format, prefix, cdata, layer, is_render, is_active);
      }
      else {
        printf("%s: error looking up attribute %s\n", __func__, name.c_str());
      }
    }

    vbo.vert_buf = GPU_vertbuf_create_with_format_ex(&format, GPU_USAGE_STATIC);
    vbo.build_key();
    fill_vbo(vbo, args);

    vbos.append(vbo);
  }

  void update_pre(const PBVH_GPU_Args &args)
  {
    if (args.pbvh_type == PBVH_BMESH) {
      int count = count_faces(args);

      if (faces_count != count) {
        for (PBVHVbo &vbo : vbos) {
          vbo.clear_data();
        }

        GPU_INDEXBUF_DISCARD_SAFE(tri_index);
        GPU_INDEXBUF_DISCARD_SAFE(lines_index);
        GPU_INDEXBUF_DISCARD_SAFE(tri_index_coarse);
        GPU_INDEXBUF_DISCARD_SAFE(lines_index_coarse);

        tri_index = lines_index = tri_index_coarse = lines_index_coarse = nullptr;
        faces_count = tris_count = count;
      }
    }
  }

  void create_index_faces(const PBVH_GPU_Args &args)
  {
    const int *mat_index = static_cast<const int *>(
        CustomData_get_layer_named(args.face_data, CD_PROP_INT32, "material_index"));

    if (mat_index && !args.prim_indices.is_empty()) {
      const int looptri_i = args.prim_indices[0];
      const int face_i = args.looptri_faces[looptri_i];
      material_index = mat_index[face_i];
    }

    const blender::Span<blender::int2> edges = args.me->edges();

    /* Calculate number of edges. */
    int edge_count = 0;
    for (const int looptri_i : args.prim_indices) {
      const int face_i = args.looptri_faces[looptri_i];
      if (args.hide_poly && args.hide_poly[face_i]) {
        continue;
      }

      const MLoopTri *lt = &args.mlooptri[looptri_i];
      int r_edges[3];
      BKE_mesh_looptri_get_real_edges(
          edges.data(), args.corner_verts.data(), args.corner_edges.data(), lt, r_edges);

      if (r_edges[0] != -1) {
        edge_count++;
      }
      if (r_edges[1] != -1) {
        edge_count++;
      }
      if (r_edges[2] != -1) {
        edge_count++;
      }
    }

    GPUIndexBufBuilder elb_lines;
    GPU_indexbuf_init(&elb_lines, GPU_PRIM_LINES, edge_count * 2, INT_MAX);

    int vertex_i = 0;
    for (const int looptri_i : args.prim_indices) {
      const int face_i = args.looptri_faces[looptri_i];
      if (args.hide_poly && args.hide_poly[face_i]) {
        continue;
      }

      const MLoopTri *lt = &args.mlooptri[looptri_i];
      int r_edges[3];
      BKE_mesh_looptri_get_real_edges(
          edges.data(), args.corner_verts.data(), args.corner_edges.data(), lt, r_edges);

      if (r_edges[0] != -1) {
        GPU_indexbuf_add_line_verts(&elb_lines, vertex_i, vertex_i + 1);
      }
      if (r_edges[1] != -1) {
        GPU_indexbuf_add_line_verts(&elb_lines, vertex_i + 1, vertex_i + 2);
      }
      if (r_edges[2] != -1) {
        GPU_indexbuf_add_line_verts(&elb_lines, vertex_i + 2, vertex_i);
      }

      vertex_i += 3;
    }

    lines_index = GPU_indexbuf_build(&elb_lines);
  }

  void create_index_bmesh(const PBVH_GPU_Args &args)
  {
    GPUIndexBufBuilder elb_lines;
    GPU_indexbuf_init(&elb_lines, GPU_PRIM_LINES, tris_count * 3 * 2, INT_MAX);

    int v_index = 0;
    lines_count = 0;

    for (const BMFace *f : *args.bm_faces) {
      if (BM_elem_flag_test(f, BM_ELEM_HIDDEN)) {
        continue;
      }

      GPU_indexbuf_add_line_verts(&elb_lines, v_index, v_index + 1);
      GPU_indexbuf_add_line_verts(&elb_lines, v_index + 1, v_index + 2);
      GPU_indexbuf_add_line_verts(&elb_lines, v_index + 2, v_index);

      lines_count += 3;
      v_index += 3;
    }

    lines_index = GPU_indexbuf_build(&elb_lines);
  }

  void create_index_grids(const PBVH_GPU_Args &args, bool do_coarse)
  {
    const int *mat_index = static_cast<const int *>(
        CustomData_get_layer_named(args.face_data, CD_PROP_INT32, "material_index"));

    if (mat_index && !args.grid_indices.is_empty()) {
      int face_i = BKE_subdiv_ccg_grid_to_face_index(args.subdiv_ccg, args.grid_indices[0]);
      material_index = mat_index[face_i];
    }

    needs_tri_index = true;
    int gridsize = args.ccg_key.grid_size;
    int display_gridsize = gridsize;
    int totgrid = args.grid_indices.size();
    int skip = 1;

    const int display_level = do_coarse ? coarse_level : args.ccg_key.level;

    if (display_level < args.ccg_key.level) {
      display_gridsize = (1 << display_level) + 1;
      skip = 1 << (args.ccg_key.level - display_level - 1);
    }

    for (const int grid_index : args.grid_indices) {
      bool smooth = !args.grid_flag_mats[grid_index].sharp;
      BLI_bitmap *gh = args.grid_hidden[grid_index];

      for (int y = 0; y < gridsize - 1; y += skip) {
        for (int x = 0; x < gridsize - 1; x += skip) {
          if (gh && paint_is_grid_face_hidden(gh, gridsize, x, y)) {
            /* Skip hidden faces by just setting smooth to true. */
            smooth = true;
            goto outer_loop_break;
          }
        }
      }

    outer_loop_break:

      if (!smooth) {
        needs_tri_index = false;
        break;
      }
    }

    GPUIndexBufBuilder elb, elb_lines;

    const CCGKey *key = &args.ccg_key;

    uint visible_quad_len = BKE_pbvh_count_grid_quads((BLI_bitmap **)args.grid_hidden,
                                                      args.grid_indices.data(),
                                                      totgrid,
                                                      key->grid_size,
                                                      display_gridsize);

    GPU_indexbuf_init(&elb, GPU_PRIM_TRIS, 2 * visible_quad_len, INT_MAX);
    GPU_indexbuf_init(&elb_lines,
                      GPU_PRIM_LINES,
                      2 * totgrid * display_gridsize * (display_gridsize - 1),
                      INT_MAX);

    if (needs_tri_index) {
      uint offset = 0;
      const uint grid_vert_len = gridsize * gridsize;
      for (int i = 0; i < totgrid; i++, offset += grid_vert_len) {
        uint v0, v1, v2, v3;
        bool grid_visible = false;

        BLI_bitmap *gh = args.grid_hidden[args.grid_indices[i]];

        for (int j = 0; j < gridsize - skip; j += skip) {
          for (int k = 0; k < gridsize - skip; k += skip) {
            /* Skip hidden grid face */
            if (gh && paint_is_grid_face_hidden(gh, gridsize, k, j)) {
              continue;
            }
            /* Indices in a Clockwise QUAD disposition. */
            v0 = offset + j * gridsize + k;
            v1 = offset + j * gridsize + k + skip;
            v2 = offset + (j + skip) * gridsize + k + skip;
            v3 = offset + (j + skip) * gridsize + k;

            GPU_indexbuf_add_tri_verts(&elb, v0, v2, v1);
            GPU_indexbuf_add_tri_verts(&elb, v0, v3, v2);

            GPU_indexbuf_add_line_verts(&elb_lines, v0, v1);
            GPU_indexbuf_add_line_verts(&elb_lines, v0, v3);

            if (j / skip + 2 == display_gridsize) {
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
    else {
      uint offset = 0;
      const uint grid_vert_len = square_uint(gridsize - 1) * 4;

      for (int i = 0; i < totgrid; i++, offset += grid_vert_len) {
        bool grid_visible = false;
        BLI_bitmap *gh = args.grid_hidden[args.grid_indices[i]];

        uint v0, v1, v2, v3;
        for (int j = 0; j < gridsize - skip; j += skip) {
          for (int k = 0; k < gridsize - skip; k += skip) {
            /* Skip hidden grid face */
            if (gh && paint_is_grid_face_hidden(gh, gridsize, k, j)) {
              continue;
            }

            v0 = (j * (gridsize - 1) + k) * 4;

            if (skip > 1) {
              v1 = (j * (gridsize - 1) + k + skip - 1) * 4;
              v2 = ((j + skip - 1) * (gridsize - 1) + k + skip - 1) * 4;
              v3 = ((j + skip - 1) * (gridsize - 1) + k) * 4;
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

            if ((j / skip) + 2 == display_gridsize) {
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

    if (do_coarse) {
      tri_index_coarse = GPU_indexbuf_build(&elb);
      lines_index_coarse = GPU_indexbuf_build(&elb_lines);
      tris_count_coarse = visible_quad_len;
      lines_count_coarse = totgrid * display_gridsize * (display_gridsize - 1);
    }
    else {
      tri_index = GPU_indexbuf_build(&elb);
      lines_index = GPU_indexbuf_build(&elb_lines);
    }
  }

  void create_index(const PBVH_GPU_Args &args)
  {
    switch (args.pbvh_type) {
      case PBVH_FACES:
        create_index_faces(args);
        break;
      case PBVH_BMESH:
        create_index_bmesh(args);
        break;
      case PBVH_GRIDS:
        create_index_grids(args, false);

        if (args.ccg_key.level > coarse_level) {
          create_index_grids(args, true);
        }

        break;
    }

    for (PBVHBatch &batch : batches.values()) {
      if (tri_index) {
        GPU_batch_elembuf_set(batch.tris, tri_index, false);
      }
      else {
        /* Still flag the batch as dirty even if we're using the default index layout. */
        batch.tris->flag |= GPU_BATCH_DIRTY;
      }

      if (lines_index) {
        GPU_batch_elembuf_set(batch.lines, lines_index, false);
      }
    }
  }

  void check_index_buffers(const PBVH_GPU_Args &args)
  {
    if (!lines_index) {
      create_index(args);
    }
  }

  void create_batch(PBVHAttrReq *attrs,
                    int attrs_num,
                    const PBVH_GPU_Args &args,
                    bool do_coarse_grids)
  {
    check_index_buffers(args);

    PBVHBatch batch;

    batch.tris = GPU_batch_create(GPU_PRIM_TRIS,
                                  nullptr,
                                  /* can be nullptr if buffer is empty */
                                  do_coarse_grids ? tri_index_coarse : tri_index);
    batch.tris_count = do_coarse_grids ? tris_count_coarse : tris_count;
    batch.is_coarse = do_coarse_grids;

    if (lines_index) {
      batch.lines = GPU_batch_create(
          GPU_PRIM_LINES, nullptr, do_coarse_grids ? lines_index_coarse : lines_index);
      batch.lines_count = do_coarse_grids ? lines_count_coarse : lines_count;
    }

    for (int i : IndexRange(attrs_num)) {
      PBVHAttrReq *attr = attrs + i;

      if (!pbvh_attr_supported(attr->type, attr->domain)) {
        continue;
      }

      if (!has_vbo(attr->domain, int(attr->type), attr->name)) {
        create_vbo(attr->domain, uint32_t(attr->type), attr->name, args);
      }

      PBVHVbo *vbo = get_vbo(attr->domain, uint32_t(attr->type), attr->name);
      int vbo_i = get_vbo_index(vbo);

      batch.vbos.append(vbo_i);
      GPU_batch_vertbuf_add(batch.tris, vbo->vert_buf, false);

      if (batch.lines) {
        GPU_batch_vertbuf_add(batch.lines, vbo->vert_buf, false);
      }
    }

    batches.add(batch.build_key(vbos), batch);
  }
};

void DRW_pbvh_node_update(PBVHBatches *batches, const PBVH_GPU_Args &args)
{
  batches->update(args);
}

void DRW_pbvh_node_gpu_flush(PBVHBatches *batches)
{
  batches->gpu_flush();
}

PBVHBatches *DRW_pbvh_node_create(const PBVH_GPU_Args &args)
{
  PBVHBatches *batches = new PBVHBatches(args);
  return batches;
}

void DRW_pbvh_node_free(PBVHBatches *batches)
{
  delete batches;
}

GPUBatch *DRW_pbvh_tris_get(PBVHBatches *batches,
                            PBVHAttrReq *attrs,
                            int attrs_num,
                            const PBVH_GPU_Args &args,
                            int *r_prim_count,
                            bool do_coarse_grids)
{
  do_coarse_grids &= args.pbvh_type == PBVH_GRIDS;

  PBVHBatch &batch = batches->ensure_batch(attrs, attrs_num, args, do_coarse_grids);

  *r_prim_count = batch.tris_count;

  return batch.tris;
}

GPUBatch *DRW_pbvh_lines_get(PBVHBatches *batches,
                             PBVHAttrReq *attrs,
                             int attrs_num,
                             const PBVH_GPU_Args &args,
                             int *r_prim_count,
                             bool do_coarse_grids)
{
  do_coarse_grids &= args.pbvh_type == PBVH_GRIDS;

  PBVHBatch &batch = batches->ensure_batch(attrs, attrs_num, args, do_coarse_grids);

  *r_prim_count = batch.lines_count;

  return batch.lines;
}

void DRW_pbvh_update_pre(PBVHBatches *batches, const PBVH_GPU_Args &args)
{
  batches->update_pre(args);
}

int drw_pbvh_material_index_get(PBVHBatches *batches)
{
  return batches->material_index;
}
