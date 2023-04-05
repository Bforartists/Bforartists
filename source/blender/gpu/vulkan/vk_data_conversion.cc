/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2023 Blender Foundation. */

/** \file
 * \ingroup gpu
 */

#include "vk_data_conversion.hh"

#include "Imath/half.h"

namespace blender::gpu {

/* -------------------------------------------------------------------- */
/** \name Conversion types
 * \{ */

enum class ConversionType {
  /** No conversion needed, result can be directly read back to host memory. */
  PASS_THROUGH,

  FLOAT_TO_UNORM8,
  UNORM8_TO_FLOAT,

  FLOAT_TO_SNORM8,
  SNORM8_TO_FLOAT,

  FLOAT_TO_UNORM16,
  UNORM16_TO_FLOAT,

  FLOAT_TO_SNORM16,
  SNORM16_TO_FLOAT,

  UI32_TO_UI16,
  UI16_TO_UI32,

  UI32_TO_UI8,
  UI8_TO_UI32,

  I32_TO_I16,
  I16_TO_I32,

  I32_TO_I8,
  I8_TO_I32,

  /** Convert device 16F to floats. */
  HALF_TO_FLOAT,
  FLOAT_TO_HALF,

  /**
   * The requested conversion isn't supported.
   */
  UNSUPPORTED,
};

static ConversionType type_of_conversion_float(eGPUTextureFormat device_format)
{
  switch (device_format) {
    case GPU_RGBA32F:
    case GPU_RG32F:
    case GPU_R32F:
    case GPU_DEPTH_COMPONENT32F:
      return ConversionType::PASS_THROUGH;

    case GPU_RGBA16F:
    case GPU_RG16F:
    case GPU_R16F:
    case GPU_RGB16F:
      return ConversionType::FLOAT_TO_HALF;

    case GPU_RGBA8:
    case GPU_RG8:
    case GPU_R8:
      return ConversionType::FLOAT_TO_UNORM8;

    case GPU_RGBA8_SNORM:
    case GPU_RGB8_SNORM:
    case GPU_RG8_SNORM:
    case GPU_R8_SNORM:
      return ConversionType::FLOAT_TO_SNORM8;

    case GPU_RGBA16:
    case GPU_RG16:
    case GPU_R16:
      return ConversionType::FLOAT_TO_UNORM16;

    case GPU_RGBA16_SNORM:
    case GPU_RGB16_SNORM:
    case GPU_RG16_SNORM:
    case GPU_R16_SNORM:
      return ConversionType::FLOAT_TO_SNORM16;

    case GPU_RGB32F: /* GPU_RGB32F Not supported by vendors. */
    case GPU_RGBA8UI:
    case GPU_RGBA8I:
    case GPU_RGBA16UI:
    case GPU_RGBA16I:
    case GPU_RGBA32UI:
    case GPU_RGBA32I:
    case GPU_RG8UI:
    case GPU_RG8I:
    case GPU_RG16UI:
    case GPU_RG16I:
    case GPU_RG32UI:
    case GPU_RG32I:
    case GPU_R8UI:
    case GPU_R8I:
    case GPU_R16UI:
    case GPU_R16I:
    case GPU_R32UI:
    case GPU_R32I:
    case GPU_RGB10_A2:
    case GPU_RGB10_A2UI:
    case GPU_R11F_G11F_B10F:
    case GPU_DEPTH32F_STENCIL8:
    case GPU_DEPTH24_STENCIL8:
    case GPU_SRGB8_A8:
    case GPU_RGB8UI:
    case GPU_RGB8I:
    case GPU_RGB8:
    case GPU_RGB16UI:
    case GPU_RGB16I:
    case GPU_RGB16:
    case GPU_RGB32UI:
    case GPU_RGB32I:
    case GPU_SRGB8_A8_DXT1:
    case GPU_SRGB8_A8_DXT3:
    case GPU_SRGB8_A8_DXT5:
    case GPU_RGBA8_DXT1:
    case GPU_RGBA8_DXT3:
    case GPU_RGBA8_DXT5:
    case GPU_SRGB8:
    case GPU_RGB9_E5:
    case GPU_DEPTH_COMPONENT24:
    case GPU_DEPTH_COMPONENT16:
      return ConversionType::UNSUPPORTED;
  }
  return ConversionType::UNSUPPORTED;
}

static ConversionType type_of_conversion_int(eGPUTextureFormat device_format)
{
  switch (device_format) {
    case GPU_RGBA32I:
    case GPU_RG32I:
    case GPU_R32I:
      return ConversionType::PASS_THROUGH;

    case GPU_RGBA16I:
    case GPU_RG16I:
    case GPU_R16I:
      return ConversionType::I32_TO_I16;

    case GPU_RGBA8I:
    case GPU_RG8I:
    case GPU_R8I:
      return ConversionType::I32_TO_I8;

    case GPU_RGBA8UI:
    case GPU_RGBA8:
    case GPU_RGBA16UI:
    case GPU_RGBA16F:
    case GPU_RGBA16:
    case GPU_RGBA32UI:
    case GPU_RGBA32F:
    case GPU_RG8UI:
    case GPU_RG8:
    case GPU_RG16UI:
    case GPU_RG16F:
    case GPU_RG32UI:
    case GPU_RG32F:
    case GPU_RG16:
    case GPU_R8UI:
    case GPU_R8:
    case GPU_R16UI:
    case GPU_R16F:
    case GPU_R16:
    case GPU_R32UI:
    case GPU_R32F:
    case GPU_RGB10_A2:
    case GPU_RGB10_A2UI:
    case GPU_R11F_G11F_B10F:
    case GPU_DEPTH32F_STENCIL8:
    case GPU_DEPTH24_STENCIL8:
    case GPU_SRGB8_A8:
    case GPU_RGBA8_SNORM:
    case GPU_RGBA16_SNORM:
    case GPU_RGB8UI:
    case GPU_RGB8I:
    case GPU_RGB8:
    case GPU_RGB8_SNORM:
    case GPU_RGB16UI:
    case GPU_RGB16I:
    case GPU_RGB16F:
    case GPU_RGB16:
    case GPU_RGB16_SNORM:
    case GPU_RGB32UI:
    case GPU_RGB32I:
    case GPU_RGB32F:
    case GPU_RG8_SNORM:
    case GPU_RG16_SNORM:
    case GPU_R8_SNORM:
    case GPU_R16_SNORM:
    case GPU_SRGB8_A8_DXT1:
    case GPU_SRGB8_A8_DXT3:
    case GPU_SRGB8_A8_DXT5:
    case GPU_RGBA8_DXT1:
    case GPU_RGBA8_DXT3:
    case GPU_RGBA8_DXT5:
    case GPU_SRGB8:
    case GPU_RGB9_E5:
    case GPU_DEPTH_COMPONENT32F:
    case GPU_DEPTH_COMPONENT24:
    case GPU_DEPTH_COMPONENT16:
      return ConversionType::UNSUPPORTED;
  }
  return ConversionType::UNSUPPORTED;
}

static ConversionType type_of_conversion_uint(eGPUTextureFormat device_format)
{
  switch (device_format) {
    case GPU_RGBA32UI:
    case GPU_RG32UI:
    case GPU_R32UI:
      return ConversionType::PASS_THROUGH;

    case GPU_RGBA16UI:
    case GPU_RG16UI:
    case GPU_R16UI:
    case GPU_RGB16UI:
      return ConversionType::UI32_TO_UI16;

    case GPU_RGBA8UI:
    case GPU_RG8UI:
    case GPU_R8UI:
      return ConversionType::UI32_TO_UI8;

    case GPU_RGBA8I:
    case GPU_RGBA8:
    case GPU_RGBA16I:
    case GPU_RGBA16F:
    case GPU_RGBA16:
    case GPU_RGBA32I:
    case GPU_RGBA32F:
    case GPU_RG8I:
    case GPU_RG8:
    case GPU_RG16I:
    case GPU_RG16F:
    case GPU_RG16:
    case GPU_RG32I:
    case GPU_RG32F:
    case GPU_R8I:
    case GPU_R8:
    case GPU_R16I:
    case GPU_R16F:
    case GPU_R16:
    case GPU_R32I:
    case GPU_R32F:
    case GPU_RGB10_A2:
    case GPU_RGB10_A2UI:
    case GPU_R11F_G11F_B10F:
    case GPU_DEPTH32F_STENCIL8:
    case GPU_DEPTH24_STENCIL8:
    case GPU_SRGB8_A8:
    case GPU_RGBA8_SNORM:
    case GPU_RGBA16_SNORM:
    case GPU_RGB8UI:
    case GPU_RGB8I:
    case GPU_RGB8:
    case GPU_RGB8_SNORM:
    case GPU_RGB16I:
    case GPU_RGB16F:
    case GPU_RGB16:
    case GPU_RGB16_SNORM:
    case GPU_RGB32UI:
    case GPU_RGB32I:
    case GPU_RGB32F:
    case GPU_RG8_SNORM:
    case GPU_RG16_SNORM:
    case GPU_R8_SNORM:
    case GPU_R16_SNORM:
    case GPU_SRGB8_A8_DXT1:
    case GPU_SRGB8_A8_DXT3:
    case GPU_SRGB8_A8_DXT5:
    case GPU_RGBA8_DXT1:
    case GPU_RGBA8_DXT3:
    case GPU_RGBA8_DXT5:
    case GPU_SRGB8:
    case GPU_RGB9_E5:
    case GPU_DEPTH_COMPONENT32F:
    case GPU_DEPTH_COMPONENT24:
    case GPU_DEPTH_COMPONENT16:
      return ConversionType::UNSUPPORTED;
  }
  return ConversionType::UNSUPPORTED;
}

static ConversionType type_of_conversion_half(eGPUTextureFormat device_format)
{
  switch (device_format) {
    case GPU_RGBA16F:
    case GPU_RG16F:
    case GPU_R16F:
      return ConversionType::PASS_THROUGH;

    case GPU_RGBA8UI:
    case GPU_RGBA8I:
    case GPU_RGBA8:
    case GPU_RGBA16UI:
    case GPU_RGBA16I:
    case GPU_RGBA16:
    case GPU_RGBA32UI:
    case GPU_RGBA32I:
    case GPU_RGBA32F:
    case GPU_RG8UI:
    case GPU_RG8I:
    case GPU_RG8:
    case GPU_RG16UI:
    case GPU_RG16I:
    case GPU_RG16:
    case GPU_RG32UI:
    case GPU_RG32I:
    case GPU_RG32F:
    case GPU_R8UI:
    case GPU_R8I:
    case GPU_R8:
    case GPU_R16UI:
    case GPU_R16I:
    case GPU_R16:
    case GPU_R32UI:
    case GPU_R32I:
    case GPU_R32F:
    case GPU_RGB10_A2:
    case GPU_RGB10_A2UI:
    case GPU_R11F_G11F_B10F:
    case GPU_DEPTH32F_STENCIL8:
    case GPU_DEPTH24_STENCIL8:
    case GPU_SRGB8_A8:
    case GPU_RGBA8_SNORM:
    case GPU_RGBA16_SNORM:
    case GPU_RGB8UI:
    case GPU_RGB8I:
    case GPU_RGB8:
    case GPU_RGB8_SNORM:
    case GPU_RGB16UI:
    case GPU_RGB16I:
    case GPU_RGB16F:
    case GPU_RGB16:
    case GPU_RGB16_SNORM:
    case GPU_RGB32UI:
    case GPU_RGB32I:
    case GPU_RGB32F:
    case GPU_RG8_SNORM:
    case GPU_RG16_SNORM:
    case GPU_R8_SNORM:
    case GPU_R16_SNORM:
    case GPU_SRGB8_A8_DXT1:
    case GPU_SRGB8_A8_DXT3:
    case GPU_SRGB8_A8_DXT5:
    case GPU_RGBA8_DXT1:
    case GPU_RGBA8_DXT3:
    case GPU_RGBA8_DXT5:
    case GPU_SRGB8:
    case GPU_RGB9_E5:
    case GPU_DEPTH_COMPONENT32F:
    case GPU_DEPTH_COMPONENT24:
    case GPU_DEPTH_COMPONENT16:
      return ConversionType::UNSUPPORTED;
  }
  return ConversionType::UNSUPPORTED;
}

static ConversionType type_of_conversion_ubyte(eGPUTextureFormat device_format)
{
  switch (device_format) {
    case GPU_RGBA8UI:
    case GPU_RGBA8:
    case GPU_RG8UI:
    case GPU_RG8:
    case GPU_R8UI:
    case GPU_R8:
      return ConversionType::PASS_THROUGH;

    case GPU_RGBA8I:
    case GPU_RGBA16UI:
    case GPU_RGBA16I:
    case GPU_RGBA16F:
    case GPU_RGBA16:
    case GPU_RGBA32UI:
    case GPU_RGBA32I:
    case GPU_RGBA32F:
    case GPU_RG8I:
    case GPU_RG16UI:
    case GPU_RG16I:
    case GPU_RG16F:
    case GPU_RG16:
    case GPU_RG32UI:
    case GPU_RG32I:
    case GPU_RG32F:
    case GPU_R8I:
    case GPU_R16UI:
    case GPU_R16I:
    case GPU_R16F:
    case GPU_R16:
    case GPU_R32UI:
    case GPU_R32I:
    case GPU_R32F:
    case GPU_RGB10_A2:
    case GPU_RGB10_A2UI:
    case GPU_R11F_G11F_B10F:
    case GPU_DEPTH32F_STENCIL8:
    case GPU_DEPTH24_STENCIL8:
    case GPU_SRGB8_A8:
    case GPU_RGBA8_SNORM:
    case GPU_RGBA16_SNORM:
    case GPU_RGB8UI:
    case GPU_RGB8I:
    case GPU_RGB8:
    case GPU_RGB8_SNORM:
    case GPU_RGB16UI:
    case GPU_RGB16I:
    case GPU_RGB16F:
    case GPU_RGB16:
    case GPU_RGB16_SNORM:
    case GPU_RGB32UI:
    case GPU_RGB32I:
    case GPU_RGB32F:
    case GPU_RG8_SNORM:
    case GPU_RG16_SNORM:
    case GPU_R8_SNORM:
    case GPU_R16_SNORM:
    case GPU_SRGB8_A8_DXT1:
    case GPU_SRGB8_A8_DXT3:
    case GPU_SRGB8_A8_DXT5:
    case GPU_RGBA8_DXT1:
    case GPU_RGBA8_DXT3:
    case GPU_RGBA8_DXT5:
    case GPU_SRGB8:
    case GPU_RGB9_E5:
    case GPU_DEPTH_COMPONENT32F:
    case GPU_DEPTH_COMPONENT24:
    case GPU_DEPTH_COMPONENT16:
      return ConversionType::UNSUPPORTED;
  }
  return ConversionType::UNSUPPORTED;
}

static ConversionType type_of_conversion_r11g11b10(eGPUTextureFormat device_format)
{
  if (device_format == GPU_R11F_G11F_B10F) {
    return ConversionType::PASS_THROUGH;
  }
  return ConversionType::UNSUPPORTED;
}

static ConversionType type_of_conversion_r10g10b10a2(eGPUTextureFormat device_format)
{
  if (ELEM(device_format, GPU_RGB10_A2, GPU_RGB10_A2UI)) {
    return ConversionType::PASS_THROUGH;
  }
  return ConversionType::UNSUPPORTED;
}

static ConversionType host_to_device(eGPUDataFormat host_format, eGPUTextureFormat device_format)
{
  BLI_assert(validate_data_format(device_format, host_format));

  switch (host_format) {
    case GPU_DATA_FLOAT:
      return type_of_conversion_float(device_format);
    case GPU_DATA_UINT:
      return type_of_conversion_uint(device_format);
    case GPU_DATA_INT:
      return type_of_conversion_int(device_format);
    case GPU_DATA_HALF_FLOAT:
      return type_of_conversion_half(device_format);
    case GPU_DATA_UBYTE:
      return type_of_conversion_ubyte(device_format);
    case GPU_DATA_10_11_11_REV:
      return type_of_conversion_r11g11b10(device_format);
    case GPU_DATA_2_10_10_10_REV:
      return type_of_conversion_r10g10b10a2(device_format);

    case GPU_DATA_UINT_24_8:
      return ConversionType::UNSUPPORTED;
  }

  return ConversionType::UNSUPPORTED;
}

static ConversionType reversed(ConversionType type)
{
#define CASE_SINGLE(a, b) \
  case ConversionType::a##_TO_##b: \
    return ConversionType::b##_TO_##a;

#define CASE_PAIR(a, b) \
  CASE_SINGLE(a, b) \
  CASE_SINGLE(b, a)

  switch (type) {
    case ConversionType::PASS_THROUGH:
      return ConversionType::PASS_THROUGH;

      CASE_PAIR(FLOAT, UNORM8)
      CASE_PAIR(FLOAT, SNORM8)
      CASE_PAIR(FLOAT, UNORM16)
      CASE_PAIR(FLOAT, SNORM16)
      CASE_PAIR(UI32, UI16)
      CASE_PAIR(I32, I16)
      CASE_PAIR(UI32, UI8)
      CASE_PAIR(I32, I8)
      CASE_PAIR(FLOAT, HALF)

    case ConversionType::UNSUPPORTED:
      return ConversionType::UNSUPPORTED;
  }

#undef CASE_PAIR
#undef CASE_SINGLE

  return ConversionType::UNSUPPORTED;
}

/* \} */

/* -------------------------------------------------------------------- */
/** \name Data Conversion
 * \{ */

template<typename InnerType> struct SignedNormalized {
  static_assert(std::is_same<InnerType, uint8_t>() || std::is_same<InnerType, uint16_t>());
  InnerType value;

  static constexpr int32_t scalar()
  {
    return (1 << (sizeof(InnerType) * 8 - 1));
  }

  static constexpr int32_t delta()
  {
    return (1 << (sizeof(InnerType) * 8 - 1)) - 1;
  }

  static constexpr int32_t max()
  {
    return ((1 << (sizeof(InnerType) * 8)) - 1);
  }
};

template<typename InnerType> struct UnsignedNormalized {
  static_assert(std::is_same<InnerType, uint8_t>() || std::is_same<InnerType, uint16_t>());
  InnerType value;

  static constexpr int32_t scalar()
  {
    return (1 << (sizeof(InnerType) * 8)) - 1;
  }

  static constexpr int32_t max()
  {
    return ((1 << (sizeof(InnerType) * 8)) - 1);
  }
};

template<typename InnerType> struct ComponentValue {
  InnerType value;
};

using UI8 = ComponentValue<uint8_t>;
using UI16 = ComponentValue<uint16_t>;
using UI32 = ComponentValue<uint32_t>;
using I8 = ComponentValue<int8_t>;
using I16 = ComponentValue<int16_t>;
using I32 = ComponentValue<int32_t>;
using F32 = ComponentValue<float>;
using F16 = ComponentValue<uint16_t>;

template<typename StorageType>
void convert_component(SignedNormalized<StorageType> &dst, const F32 &src)
{
  static constexpr int32_t scalar = SignedNormalized<StorageType>::scalar();
  static constexpr int32_t delta = SignedNormalized<StorageType>::delta();
  static constexpr int32_t max = SignedNormalized<StorageType>::max();
  dst.value = (clamp_i((src.value * scalar + delta), 0, max));
}

template<typename StorageType>
void convert_component(F32 &dst, const SignedNormalized<StorageType> &src)
{
  static constexpr int32_t scalar = SignedNormalized<StorageType>::scalar();
  static constexpr int32_t delta = SignedNormalized<StorageType>::delta();
  dst.value = float(int32_t(src.value) - delta) / scalar;
}

template<typename StorageType>
void convert_component(UnsignedNormalized<StorageType> &dst, const F32 &src)
{
  static constexpr int32_t scalar = UnsignedNormalized<StorageType>::scalar();
  static constexpr int32_t max = scalar;
  dst.value = (clamp_i((src.value * scalar), 0, max));
}

template<typename StorageType>
void convert_component(F32 &dst, const UnsignedNormalized<StorageType> &src)
{
  static constexpr int32_t scalar = UnsignedNormalized<StorageType>::scalar();
  dst.value = float(src.value) / scalar;
}

/* Copy the contents of src to dst with out performing any actual conversion. */
template<typename DestinationType, typename SourceType>
void convert_component(DestinationType &dst, const SourceType &src)
{
  static_assert(std::is_same<DestinationType, UI8>() || std::is_same<DestinationType, UI16>() ||
                std::is_same<DestinationType, UI32>() || std::is_same<DestinationType, I8>() ||
                std::is_same<DestinationType, I16>() || std::is_same<DestinationType, I32>());
  static_assert(std::is_same<SourceType, UI8>() || std::is_same<SourceType, UI16>() ||
                std::is_same<SourceType, UI32>() || std::is_same<SourceType, I8>() ||
                std::is_same<SourceType, I16>() || std::is_same<SourceType, I32>());
  static_assert(!std::is_same<DestinationType, SourceType>());
  dst.value = src.value;
}

static void convert_component(F16 &dst, const F32 &src)
{
  dst.value = imath_float_to_half(src.value);
}

static void convert_component(F32 &dst, const F16 &src)
{
  dst.value = imath_half_to_float(src.value);
}

/* \} */

template<typename DestinationType, typename SourceType>
void convert_per_component(MutableSpan<DestinationType> dst, Span<SourceType> src)
{
  BLI_assert(src.size() == dst.size());
  for (int64_t index : IndexRange(src.size())) {
    convert_component(dst[index], src[index]);
  }
}

template<typename DestinationType, typename SourceType>
void convert_per_component(void *dst_memory,
                           const void *src_memory,
                           size_t buffer_size,
                           eGPUTextureFormat device_format)
{
  size_t total_components = to_component_len(device_format) * buffer_size;
  Span<SourceType> src = Span<SourceType>(static_cast<const SourceType *>(src_memory),
                                          total_components);
  MutableSpan<DestinationType> dst = MutableSpan<DestinationType>(
      static_cast<DestinationType *>(dst_memory), total_components);
  convert_per_component<DestinationType, SourceType>(dst, src);
}

static void convert_buffer(void *dst_memory,
                           const void *src_memory,
                           size_t buffer_size,
                           eGPUTextureFormat device_format,
                           ConversionType type)
{
  switch (type) {
    case ConversionType::UNSUPPORTED:
      return;

    case ConversionType::PASS_THROUGH:
      memcpy(dst_memory, src_memory, buffer_size * to_bytesize(device_format));
      return;

    case ConversionType::UI32_TO_UI16:
      convert_per_component<UI16, UI32>(dst_memory, src_memory, buffer_size, device_format);
      break;

    case ConversionType::UI16_TO_UI32:
      convert_per_component<UI32, UI16>(dst_memory, src_memory, buffer_size, device_format);
      break;

    case ConversionType::UI32_TO_UI8:
      convert_per_component<UI8, UI32>(dst_memory, src_memory, buffer_size, device_format);
      break;

    case ConversionType::UI8_TO_UI32:
      convert_per_component<UI32, UI8>(dst_memory, src_memory, buffer_size, device_format);
      break;

    case ConversionType::I32_TO_I16:
      convert_per_component<I16, I32>(dst_memory, src_memory, buffer_size, device_format);
      break;

    case ConversionType::I16_TO_I32:
      convert_per_component<I32, I16>(dst_memory, src_memory, buffer_size, device_format);
      break;

    case ConversionType::I32_TO_I8:
      convert_per_component<I8, I32>(dst_memory, src_memory, buffer_size, device_format);
      break;

    case ConversionType::I8_TO_I32:
      convert_per_component<I32, I8>(dst_memory, src_memory, buffer_size, device_format);
      break;

    case ConversionType::FLOAT_TO_SNORM8:
      convert_per_component<SignedNormalized<uint8_t>, F32>(
          dst_memory, src_memory, buffer_size, device_format);
      break;
    case ConversionType::SNORM8_TO_FLOAT:
      convert_per_component<F32, SignedNormalized<uint8_t>>(
          dst_memory, src_memory, buffer_size, device_format);
      break;

    case ConversionType::FLOAT_TO_SNORM16:
      convert_per_component<SignedNormalized<uint16_t>, F32>(
          dst_memory, src_memory, buffer_size, device_format);
      break;
    case ConversionType::SNORM16_TO_FLOAT:
      convert_per_component<F32, SignedNormalized<uint16_t>>(
          dst_memory, src_memory, buffer_size, device_format);
      break;

    case ConversionType::FLOAT_TO_UNORM8:
      convert_per_component<UnsignedNormalized<uint8_t>, F32>(
          dst_memory, src_memory, buffer_size, device_format);
      break;
    case ConversionType::UNORM8_TO_FLOAT:
      convert_per_component<F32, UnsignedNormalized<uint8_t>>(
          dst_memory, src_memory, buffer_size, device_format);
      break;

    case ConversionType::FLOAT_TO_UNORM16:
      convert_per_component<UnsignedNormalized<uint16_t>, F32>(
          dst_memory, src_memory, buffer_size, device_format);
      break;
    case ConversionType::UNORM16_TO_FLOAT:
      convert_per_component<F32, UnsignedNormalized<uint16_t>>(
          dst_memory, src_memory, buffer_size, device_format);
      break;

    case ConversionType::FLOAT_TO_HALF:
      convert_per_component<F16, F32>(dst_memory, src_memory, buffer_size, device_format);
      break;
    case ConversionType::HALF_TO_FLOAT:
      convert_per_component<F32, F16>(dst_memory, src_memory, buffer_size, device_format);
      break;
  }
}

/* -------------------------------------------------------------------- */
/** \name API
 * \{ */

void convert_host_to_device(void *dst_buffer,
                            const void *src_buffer,
                            size_t buffer_size,
                            eGPUDataFormat host_format,
                            eGPUTextureFormat device_format)
{
  ConversionType conversion_type = host_to_device(host_format, device_format);
  BLI_assert(conversion_type != ConversionType::UNSUPPORTED);
  convert_buffer(dst_buffer, src_buffer, buffer_size, device_format, conversion_type);
}

void convert_device_to_host(void *dst_buffer,
                            const void *src_buffer,
                            size_t buffer_size,
                            eGPUDataFormat host_format,
                            eGPUTextureFormat device_format)
{
  ConversionType conversion_type = reversed(host_to_device(host_format, device_format));
  BLI_assert(conversion_type != ConversionType::UNSUPPORTED);
  convert_buffer(dst_buffer, src_buffer, buffer_size, device_format, conversion_type);
}

/* \} */

}  // namespace blender::gpu
