/*
 * Copyright 2011, Blender Foundation.
 *
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

#ifndef __UTIL_TYPES_H__
#define __UTIL_TYPES_H__

#ifndef __KERNEL_OPENCL__

#include <stdlib.h>

#endif

/* Qualifiers for kernel code shared by CPU and GPU */

#ifndef __KERNEL_GPU__

#define __device static inline
#define __device_noinline static
#define __global
#define __local
#define __shared
#define __constant

#if defined(_WIN32) && !defined(FREE_WINDOWS)
#define __device_inline static __forceinline
#define __align(...) __declspec(align(__VA_ARGS__))
#define __may_alias
#else
#define __device_inline static inline __attribute__((always_inline))
#ifndef FREE_WINDOWS64
#define __forceinline inline __attribute__((always_inline))
#endif
#define __align(...) __attribute__((aligned(__VA_ARGS__)))
#define __may_alias __attribute__((__may_alias__))
#endif

#endif

/* Bitness */

#if defined(__ppc64__) || defined(__PPC64__) || defined(__x86_64__) || defined(__ia64__) || defined(_M_X64)
#define __KERNEL_64_BIT__
#endif

/* SIMD Types */

#ifndef __KERNEL_GPU__

/* not enabled, globally applying it gives slowdown, only for testing. */
#if 0
#define __KERNEL_SSE__
#ifndef __KERNEL_SSE2__
#define __KERNEL_SSE2__
#endif
#ifndef __KERNEL_SSE3__
#define __KERNEL_SSE3__
#endif
#ifndef __KERNEL_SSSE3__
#define __KERNEL_SSSE3__
#endif
#ifndef __KERNEL_SSE4__
#define __KERNEL_SSE4__
#endif
#endif

/* SSE2 is always available on x86_64 CPUs, so auto enable */
#if defined(__x86_64__) && !defined(__KERNEL_SSE2__)
#define __KERNEL_SSE2__
#endif

/* SSE intrinsics headers */
#ifndef FREE_WINDOWS64

#ifdef __KERNEL_SSE2__
#include <xmmintrin.h> /* SSE 1 */
#include <emmintrin.h> /* SSE 2 */
#endif

#ifdef __KERNEL_SSE3__
#include <pmmintrin.h> /* SSE 3 */
#endif

#ifdef __KERNEL_SSSE3__
#include <tmmintrin.h> /* SSSE 3 */
#endif

#else

/* MinGW64 has conflicting declarations for these SSE headers in <windows.h>.
 * Since we can't avoid including <windows.h>, better only include that */
#include <windows.h>

#endif

/* int8_t, uint16_t, and friends */
#ifndef _WIN32
#include <stdint.h>
#endif

#endif

CCL_NAMESPACE_BEGIN

/* Types
 *
 * Define simpler unsigned type names, and integer with defined number of bits.
 * Also vector types, named to be compatible with OpenCL builtin types, while
 * working for CUDA and C++ too. */

/* Shorter Unsigned Names */

#ifndef __KERNEL_OPENCL__

typedef unsigned char uchar;
typedef unsigned int uint;

#endif

#ifndef __KERNEL_GPU__

/* Fixed Bits Types */

#ifdef _WIN32

typedef signed char int8_t;
typedef unsigned char uint8_t;

typedef signed short int16_t;
typedef unsigned short uint16_t;

typedef signed int int32_t;
typedef unsigned int uint32_t;

typedef long long int64_t;
typedef unsigned long long uint64_t;

#ifdef __KERNEL_64_BIT__
typedef int64_t ssize_t;
#else
typedef int32_t ssize_t;
#endif

#endif

/* Generic Memory Pointer */

typedef uint64_t device_ptr;

/* Vector Types */

struct uchar2 {
	uchar x, y;

	__forceinline uchar operator[](int i) const { return *(&x + i); }
	__forceinline uchar& operator[](int i) { return *(&x + i); }
};

struct uchar3 {
	uchar x, y, z;

	__forceinline uchar operator[](int i) const { return *(&x + i); }
	__forceinline uchar& operator[](int i) { return *(&x + i); }
};

struct uchar4 {
	uchar x, y, z, w;

	__forceinline uchar operator[](int i) const { return *(&x + i); }
	__forceinline uchar& operator[](int i) { return *(&x + i); }
};

struct int2 {
	int x, y;

	__forceinline int operator[](int i) const { return *(&x + i); }
	__forceinline int& operator[](int i) { return *(&x + i); }
};

#ifdef __KERNEL_SSE__
struct __align(16) int3 {
	union {
		__m128i m128;
		struct { int x, y, z, w; };
	};

	__forceinline int3() {}
	__forceinline int3(const __m128i a) : m128(a) {}
	__forceinline operator const __m128i&(void) const { return m128; }
	__forceinline operator __m128i&(void) { return m128; }
#else
struct int3 {
	int x, y, z, w;
#endif

	__forceinline int operator[](int i) const { return *(&x + i); }
	__forceinline int& operator[](int i) { return *(&x + i); }
};

#ifdef __KERNEL_SSE__
struct __align(16) int4 {
	union {
		__m128i m128;
		struct { int x, y, z, w; };
	};

	__forceinline int4() {}
	__forceinline int4(const __m128i a) : m128(a) {}
	__forceinline operator const __m128i&(void) const { return m128; }
	__forceinline operator __m128i&(void) { return m128; }
#else
struct int4 {
	int x, y, z, w;
#endif

	__forceinline int operator[](int i) const { return *(&x + i); }
	__forceinline int& operator[](int i) { return *(&x + i); }
};

struct uint2 {
	uint x, y;

	__forceinline uint operator[](uint i) const { return *(&x + i); }
	__forceinline uint& operator[](uint i) { return *(&x + i); }
};

struct uint3 {
	uint x, y, z;

	__forceinline uint operator[](uint i) const { return *(&x + i); }
	__forceinline uint& operator[](uint i) { return *(&x + i); }
};

struct uint4 {
	uint x, y, z, w;

	__forceinline uint operator[](uint i) const { return *(&x + i); }
	__forceinline uint& operator[](uint i) { return *(&x + i); }
};

struct float2 {
	float x, y;

	__forceinline float operator[](int i) const { return *(&x + i); }
	__forceinline float& operator[](int i) { return *(&x + i); }
};

#ifdef __KERNEL_SSE__
struct __align(16) float3 {
	union {
		__m128 m128;
		struct { float x, y, z, w; };
	};

	__forceinline float3() {}
	__forceinline float3(const __m128 a) : m128(a) {}
	__forceinline operator const __m128&(void) const { return m128; }
	__forceinline operator __m128&(void) { return m128; }
#else
struct float3 {
	float x, y, z, w;
#endif

	__forceinline float operator[](int i) const { return *(&x + i); }
	__forceinline float& operator[](int i) { return *(&x + i); }
};

#ifdef __KERNEL_SSE__
struct __align(16) float4 {
	union {
		__m128 m128;
		struct { float x, y, z, w; };
	};

	__forceinline float4() {}
	__forceinline float4(const __m128 a) : m128(a) {}
	__forceinline operator const __m128&(void) const { return m128; }
	__forceinline operator __m128&(void) { return m128; }
#else
struct float4 {
	float x, y, z, w;
#endif

	__forceinline float operator[](int i) const { return *(&x + i); }
	__forceinline float& operator[](int i) { return *(&x + i); }
};

#endif

#ifndef __KERNEL_GPU__

/* Vector Type Constructors
 * 
 * OpenCL does not support C++ class, so we use these instead. */

__device_inline uchar2 make_uchar2(uchar x, uchar y)
{
	uchar2 a = {x, y};
	return a;
}

__device_inline uchar3 make_uchar3(uchar x, uchar y, uchar z)
{
	uchar3 a = {x, y, z};
	return a;
}

__device_inline uchar4 make_uchar4(uchar x, uchar y, uchar z, uchar w)
{
	uchar4 a = {x, y, z, w};
	return a;
}

__device_inline int2 make_int2(int x, int y)
{
	int2 a = {x, y};
	return a;
}

__device_inline int3 make_int3(int x, int y, int z)
{
#ifdef __KERNEL_SSE__
	int3 a;
	a.m128 = _mm_set_epi32(0, z, y, x);
#else
	int3 a = {x, y, z, 0};
#endif

	return a;
}

__device_inline int4 make_int4(int x, int y, int z, int w)
{
#ifdef __KERNEL_SSE__
	int4 a;
	a.m128 = _mm_set_epi32(w, z, y, x);
#else
	int4 a = {x, y, z, w};
#endif

	return a;
}

__device_inline uint2 make_uint2(uint x, uint y)
{
	uint2 a = {x, y};
	return a;
}

__device_inline uint3 make_uint3(uint x, uint y, uint z)
{
	uint3 a = {x, y, z};
	return a;
}

__device_inline uint4 make_uint4(uint x, uint y, uint z, uint w)
{
	uint4 a = {x, y, z, w};
	return a;
}

__device_inline float2 make_float2(float x, float y)
{
	float2 a = {x, y};
	return a;
}

__device_inline float3 make_float3(float x, float y, float z)
{
#ifdef __KERNEL_SSE__
	float3 a;
	a.m128 = _mm_set_ps(0.0f, z, y, x);
#else
	float3 a = {x, y, z, 0.0f};
#endif

	return a;
}

__device_inline float4 make_float4(float x, float y, float z, float w)
{
#ifdef __KERNEL_SSE__
	float4 a;
	a.m128 = _mm_set_ps(w, z, y, x);
#else
	float4 a = {x, y, z, w};
#endif

	return a;
}

__device_inline int align_up(int offset, int alignment)
{
	return (offset + alignment - 1) & ~(alignment - 1);
}

__device_inline int3 make_int3(int i)
{
#ifdef __KERNEL_SSE__
	int3 a;
	a.m128 = _mm_set1_epi32(i);
#else
	int3 a = {i, i, i, i};
#endif

	return a;
}

__device_inline int4 make_int4(int i)
{
#ifdef __KERNEL_SSE__
	int4 a;
	a.m128 = _mm_set1_epi32(i);
#else
	int4 a = {i, i, i, i};
#endif

	return a;
}

__device_inline float3 make_float3(float f)
{
#ifdef __KERNEL_SSE__
	float3 a;
	a.m128 = _mm_set1_ps(f);
#else
	float3 a = {f, f, f, f};
#endif

	return a;
}

__device_inline float4 make_float4(float f)
{
#ifdef __KERNEL_SSE__
	float4 a;
	a.m128 = _mm_set1_ps(f);
#else
	float4 a = {f, f, f, f};
#endif

	return a;
}

__device_inline float4 make_float4(const int4& i)
{
#ifdef __KERNEL_SSE__
	float4 a;
	a.m128 = _mm_cvtepi32_ps(i.m128);
#else
	float4 a = {(float)i.x, (float)i.y, (float)i.z, (float)i.w};
#endif

	return a;
}

__device_inline int4 make_int4(const float3& f)
{
#ifdef __KERNEL_SSE__
	int4 a;
	a.m128 = _mm_cvtps_epi32(f.m128);
#else
	int4 a = {(int)f.x, (int)f.y, (int)f.z, (int)f.w};
#endif

	return a;
}

#endif

#ifdef __KERNEL_SSE2__

/* SSE shuffle utility functions */

#ifdef __KERNEL_SSSE3__

/* faster version for SSSE3 */
typedef __m128i shuffle_swap_t;

__device_inline const shuffle_swap_t shuffle_swap_identity(void)
{
	return _mm_set_epi8(15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0);
}

__device_inline const shuffle_swap_t shuffle_swap_swap(void)
{
	return _mm_set_epi8(7, 6, 5, 4, 3, 2, 1, 0, 15, 14, 13, 12, 11, 10, 9, 8);
}

__device_inline const __m128 shuffle_swap(const __m128& a, const shuffle_swap_t& shuf)
{
	return _mm_castsi128_ps(_mm_shuffle_epi8(_mm_castps_si128(a), shuf));
}

#else

/* somewhat slower version for SSE2 */
typedef int shuffle_swap_t;

__device_inline const shuffle_swap_t shuffle_swap_identity(void)
{
	return 0;
}

__device_inline const shuffle_swap_t shuffle_swap_swap(void)
{
	return 1;
}

__device_inline const __m128 shuffle_swap(const __m128& a, shuffle_swap_t shuf)
{
	/* shuffle value must be a constant, so we need to branch */
	if(shuf)
		return _mm_shuffle_ps(a, a, _MM_SHUFFLE(1, 0, 3, 2));
	else
		return _mm_shuffle_ps(a, a, _MM_SHUFFLE(3, 2, 1, 0));
}

#endif

template<size_t i0, size_t i1, size_t i2, size_t i3> __device_inline const __m128 shuffle(const __m128& a, const __m128& b)
{
	return _mm_shuffle_ps(a, b, _MM_SHUFFLE(i3, i2, i1, i0));
}

template<size_t i0, size_t i1, size_t i2, size_t i3> __device_inline const __m128 shuffle(const __m128& b)
{
	return _mm_castsi128_ps(_mm_shuffle_epi32(_mm_castps_si128(b), _MM_SHUFFLE(i3, i2, i1, i0)));
}
#endif

CCL_NAMESPACE_END

#endif /* __UTIL_TYPES_H__ */

