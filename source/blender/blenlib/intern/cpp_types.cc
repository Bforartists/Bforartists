/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bli
 */

#include "BLI_color_types.hh"
#include "BLI_cpp_type_make.hh"
#include "BLI_math_matrix_types.hh"
#include "BLI_math_quaternion_types.hh"
#include "BLI_math_vector_types.hh"

namespace blender {

BLI_CPP_TYPE_MAKE(bool, CPPTypeFlags::BasicType)

BLI_CPP_TYPE_MAKE(float, CPPTypeFlags::BasicType)
BLI_CPP_TYPE_MAKE(float2, CPPTypeFlags::BasicType)
BLI_CPP_TYPE_MAKE(float3, CPPTypeFlags::BasicType)
BLI_CPP_TYPE_MAKE(float4, CPPTypeFlags::BasicType)
BLI_CPP_TYPE_MAKE(float4x4, CPPTypeFlags::BasicType)

BLI_CPP_TYPE_MAKE(int8_t, CPPTypeFlags::BasicType)
BLI_CPP_TYPE_MAKE(int16_t, CPPTypeFlags::BasicType)
BLI_CPP_TYPE_MAKE(int32_t, CPPTypeFlags::BasicType)
BLI_CPP_TYPE_MAKE(short2, CPPTypeFlags::BasicType)
BLI_CPP_TYPE_MAKE(int2, CPPTypeFlags::BasicType)
BLI_CPP_TYPE_MAKE(int3, CPPTypeFlags::BasicType)
BLI_CPP_TYPE_MAKE(int4, CPPTypeFlags::BasicType)
BLI_CPP_TYPE_MAKE(int64_t, CPPTypeFlags::BasicType)

BLI_CPP_TYPE_MAKE(uint8_t, CPPTypeFlags::BasicType)
BLI_CPP_TYPE_MAKE(uint16_t, CPPTypeFlags::BasicType)
BLI_CPP_TYPE_MAKE(uint32_t, CPPTypeFlags::BasicType)
BLI_CPP_TYPE_MAKE(uint64_t, CPPTypeFlags::BasicType)

BLI_CPP_TYPE_MAKE(ColorGeometry4f, CPPTypeFlags::BasicType)
BLI_CPP_TYPE_MAKE(ColorGeometry4b, CPPTypeFlags::BasicType)

BLI_CPP_TYPE_MAKE(math::Quaternion, CPPTypeFlags::BasicType | CPPTypeFlags::IdentityDefaultValue)

BLI_CPP_TYPE_MAKE(std::string, CPPTypeFlags::BasicType)

void register_cpp_types()
{
  BLI_CPP_TYPE_REGISTER(bool);

  BLI_CPP_TYPE_REGISTER(float);
  BLI_CPP_TYPE_REGISTER(float2);
  BLI_CPP_TYPE_REGISTER(float3);
  BLI_CPP_TYPE_REGISTER(float4x4);

  BLI_CPP_TYPE_REGISTER(int8_t);
  BLI_CPP_TYPE_REGISTER(int16_t);
  BLI_CPP_TYPE_REGISTER(int32_t);
  BLI_CPP_TYPE_REGISTER(int2);
  BLI_CPP_TYPE_REGISTER(int3);
  BLI_CPP_TYPE_REGISTER(int4);
  BLI_CPP_TYPE_REGISTER(int64_t);

  BLI_CPP_TYPE_REGISTER(uint8_t);
  BLI_CPP_TYPE_REGISTER(uint16_t);
  BLI_CPP_TYPE_REGISTER(uint32_t);
  BLI_CPP_TYPE_REGISTER(uint64_t);

  BLI_CPP_TYPE_REGISTER(ColorGeometry4f);
  BLI_CPP_TYPE_REGISTER(ColorGeometry4b);

  BLI_CPP_TYPE_REGISTER(math::Quaternion);

  BLI_CPP_TYPE_REGISTER(std::string);
}

}  // namespace blender
