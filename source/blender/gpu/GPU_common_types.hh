/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 */

#pragma once

#include "BLI_string_ref.hh"

/**
 * Describes the load operation of a frame-buffer attachment at the start of a render pass.
 */
enum eGPULoadOp {
  /**
   * Clear the frame-buffer attachment using the clear value.
   */
  GPU_LOADACTION_CLEAR = 0,
  /**
   * Load the value from the attached texture.
   * Cannot be used with memoryless attachments.
   * Slower than `GPU_LOADACTION_CLEAR` or `GPU_LOADACTION_DONT_CARE`.
   */
  GPU_LOADACTION_LOAD,
  /**
   * Do not care about the content of the attachment when the render pass starts.
   * Useful if only the values being written are important.
   * Faster than `GPU_LOADACTION_CLEAR`.
   */
  GPU_LOADACTION_DONT_CARE,
};

/**
 * Describes the store operation of a frame-buffer attachment at the end of a render pass.
 */
enum eGPUStoreOp {
  /**
   * Do not care about the content of the attachment when the render pass ends.
   * Useful if only the values being written are important.
   * Cannot be used with memoryless attachments.
   */
  GPU_STOREACTION_STORE = 0,
  /**
   * The result of the rendering for this attachment will be discarded.
   * No writes to the texture memory will be done which makes it faster than
   * `GPU_STOREACTION_STORE`.
   * IMPORTANT: The actual values of the attachment is to be considered undefined.
   * Only to be used on transient attachment that are only used within the boundaries of
   * a render pass (ex.: Unneeded depth buffer result).
   */
  GPU_STOREACTION_DONT_CARE,
};

/**
 * Describes the state of a frame-buffer attachment during a sub-pass.
 *
 * NOTE: Until this is correctly implemented in all backend, reading and writing from the
 * same attachment will not work. Although there is no case where it would currently be useful.
 */
enum GPUAttachmentState {
  /** Attachment will not be written during rendering. */
  GPU_ATTACHMENT_IGNORE = 0,
  /** Attachment will be written during render sub-pass. This also works with blending. */
  GPU_ATTACHMENT_WRITE,
  /** Attachment is used as input in the fragment shader. Incompatible with depth on Metal. */
  GPU_ATTACHMENT_READ,
};

enum eGPUFrontFace {
  GPU_CLOCKWISE,
  GPU_COUNTERCLOCKWISE,
};

namespace blender::gpu::shader {

enum class Type {
  /* Types supported natively across all GPU back-ends. */
  float_t = 0,
  float2_t,
  float3_t,
  float4_t,
  float3x3_t,
  float4x4_t,
  uint_t,
  uint2_t,
  uint3_t,
  uint4_t,
  int_t,
  int2_t,
  int3_t,
  int4_t,
  bool_t,
  /* Additionally supported types to enable data optimization and native
   * support in some GPU back-ends.
   * NOTE: These types must be representable in all APIs. E.g. `VEC3_101010I2` is aliased as vec3
   * in the GL back-end, as implicit type conversions from packed normal attribute data to vec3 is
   * supported. UCHAR/CHAR types are natively supported in Metal and can be used to avoid
   * additional data conversions for `GPU_COMP_U8` vertex attributes. */
  float3_10_10_10_2_t,
  uchar_t,
  uchar2_t,
  uchar3_t,
  uchar4_t,
  char_t,
  char2_t,
  char3_t,
  char4_t,
  ushort_t,
  ushort2_t,
  ushort3_t,
  ushort4_t,
  short_t,
  short2_t,
  short3_t,
  short4_t
};

BLI_INLINE int to_component_count(const Type &type)
{
  switch (type) {
    case Type::float_t:
    case Type::uint_t:
    case Type::int_t:
    case Type::bool_t:
      return 1;
    case Type::float2_t:
    case Type::uint2_t:
    case Type::int2_t:
      return 2;
    case Type::float3_t:
    case Type::uint3_t:
    case Type::int3_t:
      return 3;
    case Type::float4_t:
    case Type::uint4_t:
    case Type::int4_t:
      return 4;
    case Type::float3x3_t:
      return 9;
    case Type::float4x4_t:
      return 16;
    /* Alias special types. */
    case Type::uchar_t:
    case Type::ushort_t:
    case Type::char_t:
    case Type::short_t:
      return 1;
    case Type::uchar2_t:
    case Type::ushort2_t:
    case Type::char2_t:
    case Type::short2_t:
      return 2;
    case Type::uchar3_t:
    case Type::ushort3_t:
    case Type::char3_t:
    case Type::short3_t:
      return 3;
    case Type::uchar4_t:
    case Type::ushort4_t:
    case Type::char4_t:
    case Type::short4_t:
      return 4;
    case Type::float3_10_10_10_2_t:
      return 3;
  }
  BLI_assert_unreachable();
  return -1;
}

struct SpecializationConstant {
  struct Value {
    union {
      uint32_t u;
      int32_t i;
      float f;
    };

    bool operator==(const Value &other) const
    {
      return u == other.u;
    }
  };

  Type type;
  StringRefNull name;
  Value value;

  SpecializationConstant() = default;

  SpecializationConstant(const char *name, uint32_t value) : type(Type::uint_t), name(name)
  {
    this->value.u = value;
  }

  SpecializationConstant(const char *name, int value) : type(Type::int_t), name(name)
  {
    this->value.i = value;
  }

  SpecializationConstant(const char *name, float value) : type(Type::float_t), name(name)
  {
    this->value.f = value;
  }

  SpecializationConstant(const char *name, bool value) : type(Type::bool_t), name(name)
  {
    this->value.u = value ? 1 : 0;
  }

  bool operator==(const SpecializationConstant &b) const
  {
    return this->type == b.type && this->name == b.name && this->value == b.value;
  }
};

}  // namespace blender::gpu::shader
