/* SPDX-FileCopyrightText: 2016 by Mike Erwin. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 *
 * GPU vertex format
 */

#pragma once

#include "BLI_assert.h"
#include "BLI_compiler_compat.h"
#include "BLI_string_ref.hh"
#include "BLI_sys_types.h"

#include "GPU_format.hh"

namespace blender::gpu {

enum class VertAttrType : uint8_t {
  Invalid = 0,

#define DECLARE(a, b, c, blender_enum, d, e, f, g, h) blender_enum = int(DataFormat::blender_enum),

#define GPU_VERTEX_FORMAT_EXPAND(impl) \
  SNORM_8_8_8_8_(impl) \
\
  SNORM_16_16_(impl) \
  SNORM_16_16_16_16_(impl) \
\
  UNORM_8_8_8_8_(impl) \
\
  UNORM_16_16_(impl) \
  UNORM_16_16_16_16_(impl) \
\
  SINT_8_8_8_8_(impl) \
\
  SINT_16_16_(impl) \
  SINT_16_16_16_16_(impl) \
\
  SINT_32_(impl) \
  SINT_32_32_(impl) \
  SINT_32_32_32_(impl) \
  SINT_32_32_32_32_(impl) \
\
  UINT_8_8_8_8_(impl) \
\
  UINT_16_16_(impl) \
  UINT_16_16_16_16_(impl) \
\
  UINT_32_(impl) \
  UINT_32_32_(impl) \
  UINT_32_32_32_(impl) \
  UINT_32_32_32_32_(impl) \
\
  SFLOAT_32_(impl) \
  SFLOAT_32_32_(impl) \
  SFLOAT_32_32_32_(impl) \
  SFLOAT_32_32_32_32_(impl) \
\
  SNORM_10_10_10_2_(impl) \
  UNORM_10_10_10_2_(impl) \
\
  /* Legacy format unsupported by Metal and Vulkan. To be phased out. */ \
  SINT_TO_FLT_32_(impl) \
  SINT_TO_FLT_32_32_(impl) \
  SINT_TO_FLT_32_32_32_(impl) \
  SINT_TO_FLT_32_32_32_32_(impl) \
\
  /* UFLOAT_11_11_10_(impl) Available on Metal (and maybe VK) but not on GL. */ \
  /* UFLOAT_9_9_9_EXP_5_(impl) Available on Metal (and maybe VK) but not on GL. */

  GPU_VERTEX_FORMAT_EXPAND(DECLARE)
#undef DECLARE

#define DECLARE(a, b, c, blender_enum, d, e, f, g, h) \
  blender_enum##_DEPRECATED = int(DataFormat::blender_enum),

/* Deprecated formats. To be removed in 5.0. Needed for python shaders. */
#define GPU_VERTEX_DEPRECATED_FORMAT_EXPAND(impl) \
  SNORM_8_(impl) \
  SNORM_8_8_(impl) \
  SNORM_8_8_8_(impl) \
  SNORM_16_(impl) \
  SNORM_16_16_16_(impl) \
  UNORM_8_(impl) \
  UNORM_8_8_(impl) \
  UNORM_8_8_8_(impl) \
  UNORM_16_(impl) \
  UNORM_16_16_16_(impl) \
  SINT_8_(impl) \
  SINT_8_8_(impl) \
  SINT_8_8_8_(impl) \
  SINT_16_(impl) \
  SINT_16_16_16_(impl) \
  UINT_8_(impl) \
  UINT_8_8_(impl) \
  UINT_8_8_8_(impl) \
  UINT_16_(impl) \
  UINT_16_16_16_(impl)

      GPU_VERTEX_DEPRECATED_FORMAT_EXPAND(DECLARE)

#undef DECLARE
};

inline constexpr DataFormat to_data_format(VertAttrType format)
{
  return DataFormat(int(format));
}

}  // namespace blender::gpu

struct GPUShader;

constexpr static int GPU_VERT_ATTR_MAX_LEN = 16;
constexpr static int GPU_VERT_ATTR_MAX_NAMES = 6;
constexpr static int GPU_VERT_ATTR_NAMES_BUF_LEN = 256;
constexpr static int GPU_VERT_FORMAT_MAX_NAMES = 63; /* More than enough, actual max is ~30. */
/* Computed as GPU_VERT_ATTR_NAMES_BUF_LEN / 30 (actual max format name). */
constexpr static int GPU_MAX_SAFE_ATTR_NAME = 12;

enum GPUVertCompType {
  GPU_COMP_I8 = 0,
  GPU_COMP_U8,
  GPU_COMP_I16,
  GPU_COMP_U16,
  GPU_COMP_I32,
  GPU_COMP_U32,

  GPU_COMP_F32,

  GPU_COMP_I10,
  /* Warning! adjust GPUVertAttr if changing. */

  GPU_COMP_MAX
};

enum GPUVertFetchMode {
  GPU_FETCH_FLOAT = 0,
  GPU_FETCH_INT,
  GPU_FETCH_INT_TO_FLOAT_UNIT, /* 127 (ubyte) -> 0.5 (and so on for other int types) */
  /* Warning! adjust GPUVertAttr if changing. */
};

struct GPUVertAttr {
  /* To replace fetch_mode, comp_type, comp_len, size. */
  blender::gpu::VertAttrType format;
#ifndef NO_LEGACY_VERT_TYPE
  /* GPUVertFetchMode */
  uint fetch_mode : 2;
  /* GPUVertCompType */
  uint comp_type : 3;
  /* 1 to 4 or 8 or 12 or 16 */
  uint comp_len : 5;
  /* size in bytes, 1 to 64 */
  uint size : 7;
  /* WORKAROUND: Allow casting inside pyGPU attr_fill. To be removed with 5.0. */
  uint python_int_to_float : 1;
#endif
  /* from beginning of vertex, in bytes */
  uint8_t offset;
  /* up to GPU_VERT_ATTR_MAX_NAMES */
  uint8_t name_len;
  uchar names[GPU_VERT_ATTR_MAX_NAMES];
};

BLI_STATIC_ASSERT(GPU_VERT_ATTR_NAMES_BUF_LEN <= 256,
                  "We use uchar as index inside the name buffer "
                  "so GPU_VERT_ATTR_NAMES_BUF_LEN needs to be "
                  "smaller than GPUVertFormat->name_offset and "
                  "GPUVertAttr->names maximum value");

struct GPUVertFormat {
  /** 0 to 16 (GPU_VERT_ATTR_MAX_LEN). */
  uint attr_len : 5;
  /** Total count of active vertex attribute names. (max GPU_VERT_FORMAT_MAX_NAMES) */
  uint name_len : 6;
  /** Stride in bytes, 1 to 1024. */
  uint stride : 11;
  /** Has the format been packed. */
  uint packed : 1;
  /** Current offset in names[]. */
  uint name_offset : 8;
  /** Store each attribute in one contiguous buffer region. */
  uint deinterleaved : 1;

  GPUVertAttr attrs[GPU_VERT_ATTR_MAX_LEN];
  char names[GPU_VERT_ATTR_NAMES_BUF_LEN];
};

void GPU_vertformat_clear(GPUVertFormat *);
void GPU_vertformat_copy(GPUVertFormat *dest, const GPUVertFormat &src);
void GPU_vertformat_from_shader(GPUVertFormat *format, const GPUShader *shader);

uint GPU_vertformat_attr_add(
    GPUVertFormat *, blender::StringRef name, GPUVertCompType, uint comp_len, GPUVertFetchMode);
void GPU_vertformat_alias_add(GPUVertFormat *, blender::StringRef alias);

/**
 * Return a vertex format from a single attribute description.
 * The attribute ID is ensured to be 0.
 */
GPUVertFormat GPU_vertformat_from_attribute(blender::StringRef name,
                                            const GPUVertCompType comp_type,
                                            const uint comp_len,
                                            const GPUVertFetchMode fetch_mode);

/**
 * Makes vertex attribute from the next vertices to be accessible in the vertex shader.
 * For an attribute named "attr" you can access the next nth vertex using "attr{number}".
 * Use this function after specifying all the attributes in the format.
 *
 * NOTE: This does NOT work when using indexed rendering.
 * NOTE: Only works for first attribute name. (this limitation can be changed if needed)
 *
 * WARNING: this function creates a lot of aliases/attributes, make sure to keep the attribute
 * name short to avoid overflowing the name-buffer.
 */
void GPU_vertformat_multiload_enable(GPUVertFormat *format, int load_count);

/**
 * Make attribute layout non-interleaved.
 * Warning! This does not change data layout!
 * Use direct buffer access to fill the data.
 * This is for advanced usage.
 *
 * De-interleaved data means all attribute data for each attribute
 * is stored continuously like this:
 * 000011112222
 * instead of:
 * 012012012012
 *
 * \note This is per attribute de-interleaving, NOT per component.
 */
void GPU_vertformat_deinterleave(GPUVertFormat *format);

int GPU_vertformat_attr_id_get(const GPUVertFormat *, blender::StringRef name);

BLI_INLINE const char *GPU_vertformat_attr_name_get(const GPUVertFormat *format,
                                                    const GPUVertAttr *attr,
                                                    uint n_idx)
{
  return format->names + attr->names[n_idx];
}

/**
 * \warning Can only rename using a string with same character count.
 * \warning This removes all other aliases of this attribute.
 */
void GPU_vertformat_attr_rename(GPUVertFormat *format, int attr, const char *new_name);

/**
 * \warning Always add a prefix to the result of this function as
 * the generated string can start with a number and not be a valid attribute name.
 */
void GPU_vertformat_safe_attr_name(blender::StringRef attr_name, char *r_safe_name, uint max_len);
