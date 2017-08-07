/*
 * Copyright 2011-2013 Intel Corporation
 * Modifications Copyright 2014, Blender Foundation.
 *
 * Licensed under the Apache License, Version 2.0(the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef __UTIL_SIMD_TYPES_H__
#define __UTIL_SIMD_TYPES_H__

#ifndef __KERNEL_GPU__

#include <limits>

#include "util/util_debug.h"
#include "util/util_defines.h"

/* SSE Intrinsics includes
 *
 * We assume __KERNEL_SSEX__ flags to have been defined at this point */

/* SSE intrinsics headers */
#ifndef FREE_WINDOWS64

#ifdef _MSC_VER
#  include <intrin.h>
#elif (defined(__x86_64__) || defined(__i386__))
#  include <x86intrin.h>
#endif

#else

/* MinGW64 has conflicting declarations for these SSE headers in <windows.h>.
 * Since we can't avoid including <windows.h>, better only include that */
#include "util/util_windows.h"

#endif

CCL_NAMESPACE_BEGIN

#ifdef __KERNEL_SSE2__

extern const __m128 _mm_lookupmask_ps[16];

/* Special Types */

static struct TrueTy {
__forceinline operator bool( ) const { return true; }
} True ccl_maybe_unused;

static struct FalseTy {
__forceinline operator bool( ) const { return false; }
} False ccl_maybe_unused;

static struct NegInfTy
{
__forceinline operator          float    ( ) const { return -std::numeric_limits<float>::infinity(); }
__forceinline operator          int      ( ) const { return std::numeric_limits<int>::min(); }
} neg_inf ccl_maybe_unused;

static struct PosInfTy
{
__forceinline operator          float    ( ) const { return std::numeric_limits<float>::infinity(); }
__forceinline operator          int      ( ) const { return std::numeric_limits<int>::max(); }
} inf ccl_maybe_unused, pos_inf ccl_maybe_unused;

/* Intrinsics Functions */

#if defined(__BMI__) && defined(__GNUC__)
#  ifndef _tzcnt_u32
#    define _tzcnt_u32 __tzcnt_u32
#  endif
#  ifndef _tzcnt_u64
#    define _tzcnt_u64 __tzcnt_u64
#  endif
#endif

#if defined(__LZCNT__)
#define _lzcnt_u32 __lzcnt32
#define _lzcnt_u64 __lzcnt64
#endif

#if defined(_WIN32) && !defined(__MINGW32__) && !defined(__clang__)

__forceinline int __popcnt(int in) {
  return _mm_popcnt_u32(in);
}

#if !defined(_MSC_VER)
__forceinline unsigned int __popcnt(unsigned int in) {
  return _mm_popcnt_u32(in);
}
#endif

#if defined(__KERNEL_64_BIT__)
__forceinline long long __popcnt(long long in) {
  return _mm_popcnt_u64(in);
}
__forceinline size_t __popcnt(size_t in) {
  return _mm_popcnt_u64(in);
}
#endif

__forceinline int __bsf(int v) {
#if defined(__KERNEL_AVX2__) 
  return _tzcnt_u32(v);
#else
  unsigned long r = 0; _BitScanForward(&r,v); return r;
#endif
}

__forceinline unsigned int __bsf(unsigned int v) {
#if defined(__KERNEL_AVX2__) 
  return _tzcnt_u32(v);
#else
  unsigned long r = 0; _BitScanForward(&r,v); return r;
#endif
}

__forceinline int __bsr(int v) {
  unsigned long r = 0; _BitScanReverse(&r,v); return r;
}

__forceinline int __btc(int v, int i) {
  long r = v; _bittestandcomplement(&r,i); return r;
}

__forceinline int __bts(int v, int i) {
  long r = v; _bittestandset(&r,i); return r;
}

__forceinline int __btr(int v, int i) {
  long r = v; _bittestandreset(&r,i); return r;
}

__forceinline int bitscan(int v) {
#if defined(__KERNEL_AVX2__) 
  return _tzcnt_u32(v);
#else
  return __bsf(v);
#endif
}

__forceinline int clz(const int x)
{
#if defined(__KERNEL_AVX2__)
  return _lzcnt_u32(x);
#else
  if(UNLIKELY(x == 0)) return 32;
  return 31 - __bsr(x);    
#endif
}

__forceinline int __bscf(int& v) 
{
  int i = __bsf(v);
  v &= v-1;
  return i;
}

__forceinline unsigned int __bscf(unsigned int& v) 
{
  unsigned int i = __bsf(v);
  v &= v-1;
  return i;
}

#if defined(__KERNEL_64_BIT__)

__forceinline size_t __bsf(size_t v) {
#if defined(__KERNEL_AVX2__) 
  return _tzcnt_u64(v);
#else
  unsigned long r = 0; _BitScanForward64(&r,v); return r;
#endif
}

__forceinline size_t __bsr(size_t v) {
  unsigned long r = 0; _BitScanReverse64(&r,v); return r;
}

__forceinline size_t __btc(size_t v, size_t i) {
  size_t r = v; _bittestandcomplement64((__int64*)&r,i); return r;
}

__forceinline size_t __bts(size_t v, size_t i) {
  __int64 r = v; _bittestandset64(&r,i); return r;
}

__forceinline size_t __btr(size_t v, size_t i) {
  __int64 r = v; _bittestandreset64(&r,i); return r;
}

__forceinline size_t bitscan(size_t v) {
#if defined(__KERNEL_AVX2__)
#if defined(__KERNEL_64_BIT__)
  return _tzcnt_u64(v);
#else
  return _tzcnt_u32(v);
#endif
#else
  return __bsf(v);
#endif
}

__forceinline size_t __bscf(size_t& v) 
{
  size_t i = __bsf(v);
  v &= v-1;
  return i;
}

#endif /* __KERNEL_64_BIT__ */

#else /* _WIN32 */

__forceinline unsigned int __popcnt(unsigned int in) {
  int r = 0; asm ("popcnt %1,%0" : "=r"(r) : "r"(in)); return r;
}

__forceinline int __bsf(int v) {
  int r = 0; asm ("bsf %1,%0" : "=r"(r) : "r"(v)); return r;
}

__forceinline int __bsr(int v) {
  int r = 0; asm ("bsr %1,%0" : "=r"(r) : "r"(v)); return r;
}

__forceinline int __btc(int v, int i) {
  int r = 0; asm ("btc %1,%0" : "=r"(r) : "r"(i), "0"(v) : "flags" ); return r;
}

__forceinline int __bts(int v, int i) {
  int r = 0; asm ("bts %1,%0" : "=r"(r) : "r"(i), "0"(v) : "flags"); return r;
}

__forceinline int __btr(int v, int i) {
  int r = 0; asm ("btr %1,%0" : "=r"(r) : "r"(i), "0"(v) : "flags"); return r;
}

#if (defined(__KERNEL_64_BIT__) || defined(__APPLE__)) && !(defined(__ILP32__) && defined(__x86_64__))
__forceinline size_t __bsf(size_t v) {
  size_t r = 0; asm ("bsf %1,%0" : "=r"(r) : "r"(v)); return r;
}
#endif

__forceinline unsigned int __bsf(unsigned int v) {
  unsigned int r = 0; asm ("bsf %1,%0" : "=r"(r) : "r"(v)); return r;
}

__forceinline size_t __bsr(size_t v) {
  size_t r = 0; asm ("bsr %1,%0" : "=r"(r) : "r"(v)); return r;
}

__forceinline size_t __btc(size_t v, size_t i) {
  size_t r = 0; asm ("btc %1,%0" : "=r"(r) : "r"(i), "0"(v) : "flags" ); return r;
}

__forceinline size_t __bts(size_t v, size_t i) {
  size_t r = 0; asm ("bts %1,%0" : "=r"(r) : "r"(i), "0"(v) : "flags"); return r;
}

__forceinline size_t __btr(size_t v, size_t i) {
  size_t r = 0; asm ("btr %1,%0" : "=r"(r) : "r"(i), "0"(v) : "flags"); return r;
}

__forceinline int bitscan(int v) {
#if defined(__KERNEL_AVX2__) 
  return _tzcnt_u32(v);
#else
  return __bsf(v);
#endif
}

__forceinline unsigned int bitscan(unsigned int v) {
#if defined(__KERNEL_AVX2__) 
  return _tzcnt_u32(v);
#else
  return __bsf(v);
#endif
}

#if (defined(__KERNEL_64_BIT__) || defined(__APPLE__)) && !(defined(__ILP32__) && defined(__x86_64__))
__forceinline size_t bitscan(size_t v) {
#if defined(__KERNEL_AVX2__)
#if defined(__KERNEL_64_BIT__)
  return _tzcnt_u64(v);
#else
  return _tzcnt_u32(v);
#endif
#else
  return __bsf(v);
#endif
}
#endif

__forceinline int clz(const int x)
{
#if defined(__KERNEL_AVX2__)
  return _lzcnt_u32(x);
#else
  if(UNLIKELY(x == 0)) return 32;
  return 31 - __bsr(x);    
#endif
}

__forceinline int __bscf(int& v) 
{
  int i = bitscan(v);
#if defined(__KERNEL_AVX2__)
  v &= v-1;
#else
  v = __btc(v,i);
#endif
  return i;
}

__forceinline unsigned int __bscf(unsigned int& v) 
{
  unsigned int i = bitscan(v);
  v &= v-1;
  return i;
}

#if (defined(__KERNEL_64_BIT__) || defined(__APPLE__)) && !(defined(__ILP32__) && defined(__x86_64__))
__forceinline size_t __bscf(size_t& v) 
{
  size_t i = bitscan(v);
#if defined(__KERNEL_AVX2__)
  v &= v-1;
#else
  v = __btc(v,i);
#endif
  return i;
}
#endif

#endif /* _WIN32 */

#if !(defined(__SSE4_1__) || defined(__SSE4_2__))

/* Emulation of SSE4 functions with SSE2 */

#define _MM_FROUND_TO_NEAREST_INT    0x00
#define _MM_FROUND_TO_NEG_INF        0x01
#define _MM_FROUND_TO_POS_INF        0x02
#define _MM_FROUND_TO_ZERO           0x03
#define _MM_FROUND_CUR_DIRECTION     0x04

#undef _mm_blendv_ps
#define _mm_blendv_ps _mm_blendv_ps_emu
__forceinline __m128 _mm_blendv_ps_emu( __m128 value, __m128 input, __m128 mask)
{
    return _mm_or_ps(_mm_and_ps(mask, input), _mm_andnot_ps(mask, value)); 
}

#undef _mm_blend_ps
#define _mm_blend_ps _mm_blend_ps_emu
__forceinline __m128 _mm_blend_ps_emu( __m128 value, __m128 input, const int mask)
{
    assert(mask < 0x10); return _mm_blendv_ps(value, input, _mm_lookupmask_ps[mask]); 
}

#undef _mm_blendv_epi8
#define _mm_blendv_epi8 _mm_blendv_epi8_emu
__forceinline __m128i _mm_blendv_epi8_emu( __m128i value, __m128i input, __m128i mask)
{
    return _mm_or_si128(_mm_and_si128(mask, input), _mm_andnot_si128(mask, value)); 
}

#undef _mm_min_epi32
#define _mm_min_epi32 _mm_min_epi32_emu
__forceinline __m128i _mm_min_epi32_emu( __m128i value, __m128i input)
{
    return _mm_blendv_epi8(input, value, _mm_cmplt_epi32(value, input)); 
}

#undef _mm_max_epi32
#define _mm_max_epi32 _mm_max_epi32_emu
__forceinline __m128i _mm_max_epi32_emu( __m128i value, __m128i input)
{
    return _mm_blendv_epi8(value, input, _mm_cmplt_epi32(value, input)); 
}

#undef _mm_extract_epi32
#define _mm_extract_epi32 _mm_extract_epi32_emu
__forceinline int _mm_extract_epi32_emu( __m128i input, const int index)
{
  switch(index) {
  case 0: return _mm_cvtsi128_si32(input);
  case 1: return _mm_cvtsi128_si32(_mm_shuffle_epi32(input, _MM_SHUFFLE(1, 1, 1, 1)));
  case 2: return _mm_cvtsi128_si32(_mm_shuffle_epi32(input, _MM_SHUFFLE(2, 2, 2, 2)));
  case 3: return _mm_cvtsi128_si32(_mm_shuffle_epi32(input, _MM_SHUFFLE(3, 3, 3, 3)));
  default: assert(false); return 0;
  }
}

#undef _mm_insert_epi32
#define _mm_insert_epi32 _mm_insert_epi32_emu
__forceinline __m128i _mm_insert_epi32_emu( __m128i value, int input, const int index)
{
    assert(index >= 0 && index < 4); ((int*)&value)[index] = input; return value; 
}

#undef _mm_insert_ps
#define _mm_insert_ps _mm_insert_ps_emu
__forceinline __m128 _mm_insert_ps_emu( __m128 value, __m128 input, const int index)
{
	assert(index < 0x100);
	((float*)&value)[(index >> 4)&0x3] = ((float*)&input)[index >> 6];
	return _mm_andnot_ps(_mm_lookupmask_ps[index&0xf], value);
}

#undef _mm_round_ps
#define _mm_round_ps _mm_round_ps_emu
__forceinline __m128 _mm_round_ps_emu( __m128 value, const int flags)
{
  switch(flags)
  {
  case _MM_FROUND_TO_NEAREST_INT: return _mm_cvtepi32_ps(_mm_cvtps_epi32(value));
  case _MM_FROUND_TO_NEG_INF    : return _mm_cvtepi32_ps(_mm_cvtps_epi32(_mm_add_ps(value, _mm_set1_ps(-0.5f))));
  case _MM_FROUND_TO_POS_INF    : return _mm_cvtepi32_ps(_mm_cvtps_epi32(_mm_add_ps(value, _mm_set1_ps( 0.5f))));
  case _MM_FROUND_TO_ZERO       : return _mm_cvtepi32_ps(_mm_cvttps_epi32(value));
  }
  return value;
}

#endif /* !(defined(__SSE4_1__) || defined(__SSE4_2__)) */

#else  /* __KERNEL_SSE2__ */

/* This section is for utility functions which operates on non-register data
 * which might be used from a non-vectorized code.
 */

ccl_device_inline int bitscan(int value)
{
	assert(value != 0);
	int bit = 0;
	while(value >>= 1) {
		++bit;
	}
	return bit;
}


#endif /* __KERNEL_SSE2__ */

/* quiet unused define warnings */
#if defined(__KERNEL_SSE2__)  || \
	defined(__KERNEL_SSE3__)  || \
	defined(__KERNEL_SSSE3__) || \
	defined(__KERNEL_SSE41__) || \
	defined(__KERNEL_AVX__)   || \
	defined(__KERNEL_AVX2__)
	/* do nothing */
#endif

CCL_NAMESPACE_END

#endif /* __KERNEL_GPU__ */

#endif /* __UTIL_SIMD_TYPES_H__ */

