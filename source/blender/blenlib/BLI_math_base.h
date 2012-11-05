/*
 * ***** BEGIN GPL LICENSE BLOCK *****
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
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: some of this file.
 *
 * ***** END GPL LICENSE BLOCK *****
 * */

#ifndef __BLI_MATH_BASE_H__
#define __BLI_MATH_BASE_H__

/** \file BLI_math_base.h
 *  \ingroup bli
 */

#ifdef _MSC_VER
#  define _USE_MATH_DEFINES
#endif

#include <math.h>
#include "BLI_math_inline.h"

#ifdef __sun__
#include <ieeefp.h> /* for finite() */
#endif

#ifndef M_PI
#define M_PI        3.14159265358979323846
#endif
#ifndef M_PI_2
#define M_PI_2      1.57079632679489661923
#endif
#ifndef M_SQRT2
#define M_SQRT2     1.41421356237309504880
#endif
#ifndef M_SQRT1_2
#define M_SQRT1_2   0.70710678118654752440
#endif
#ifndef M_SQRT3
#define M_SQRT3   1.7320508075688772
#endif
#ifndef M_1_PI
#define M_1_PI      0.318309886183790671538
#endif
#ifndef M_E
#define M_E             2.7182818284590452354
#endif
#ifndef M_LOG2E
#define M_LOG2E         1.4426950408889634074
#endif
#ifndef M_LOG10E
#define M_LOG10E        0.43429448190325182765
#endif
#ifndef M_LN2
#define M_LN2           0.69314718055994530942
#endif
#ifndef M_LN10
#define M_LN10          2.30258509299404568402
#endif

/* non-standard defines, used in some places */
#ifndef MAXFLOAT
#define MAXFLOAT  ((float)3.40282347e+38)
#endif

#ifndef sqrtf
#define sqrtf(a) ((float)sqrt(a))
#endif
#ifndef powf
#define powf(a, b) ((float)pow(a, b))
#endif
#ifndef cosf
#define cosf(a) ((float)cos(a))
#endif
#ifndef sinf
#define sinf(a) ((float)sin(a))
#endif
#ifndef acosf
#define acosf(a) ((float)acos(a))
#endif
#ifndef asinf
#define asinf(a) ((float)asin(a))
#endif
#ifndef atan2f
#define atan2f(a, b) ((float)atan2(a, b))
#endif
#ifndef tanf
#define tanf(a) ((float)tan(a))
#endif
#ifndef atanf
#define atanf(a) ((float)atan(a))
#endif
#ifndef floorf
#define floorf(a) ((float)floor(a))
#endif
#ifndef ceilf
#define ceilf(a) ((float)ceil(a))
#endif
#ifndef fabsf
#define fabsf(a) ((float)fabs(a))
#endif
#ifndef logf
#define logf(a) ((float)log(a))
#endif
#ifndef expf
#define expf(a) ((float)exp(a))
#endif
#ifndef fmodf
#define fmodf(a, b) ((float)fmod(a, b))
#endif
#ifndef hypotf
#define hypotf(a, b) ((float)hypot(a, b))
#endif

#ifdef WIN32
#  ifndef FREE_WINDOWS
#    define isnan(n) _isnan(n)
#    define finite _finite
#    define hypot _hypot
#  endif
#endif

/* Causes warning:
 * incompatible types when assigning to type 'Foo' from type 'Bar'
 * ... the compiler optimizes away the temp var */
#ifndef CHECK_TYPE
#ifdef __GNUC__
#define CHECK_TYPE(var, type)  {  \
	__typeof(var) *__tmp;         \
	__tmp = (type *)NULL;         \
	(void)__tmp;                  \
} (void)0
#else
#define CHECK_TYPE(var, type)
#endif
#endif

#ifndef SWAP
#  define SWAP(type, a, b)  {  \
	type sw_ap;                \
	CHECK_TYPE(a, type);       \
	CHECK_TYPE(b, type);       \
	sw_ap = (a);               \
	(a) = (b);                 \
	(b) = sw_ap;               \
} (void)0
#endif

#ifndef CLAMP
#  define CLAMP(a, b, c)  {         \
	if ((a) < (b)) (a) = (b);       \
	else if ((a) > (c)) (a) = (c);  \
} (void)0
#endif

#ifdef __BLI_MATH_INLINE_H__
#include "intern/math_base_inline.c"
#endif

/******************************* Float ******************************/

MINLINE float sqrt3f(float f);
MINLINE double sqrt3d(double d);

MINLINE float saacosf(float f);
MINLINE float saasinf(float f);
MINLINE float sasqrtf(float f);
MINLINE float saacos(float fac);
MINLINE float saasin(float fac);
MINLINE float sasqrt(float fac);

MINLINE float interpf(float a, float b, float t);

MINLINE float min_ff(float a, float b);
MINLINE float max_ff(float a, float b);

MINLINE int min_ii(int a, int b);
MINLINE int max_ii(int a, int b);

MINLINE float signf(float f);

MINLINE float power_of_2(float f);

/* these don't really fit anywhere but were being copied about a lot */
MINLINE int is_power_of_2_i(int n);
MINLINE int power_of_2_max_i(int n);
MINLINE int power_of_2_min_i(int n);

MINLINE float shell_angle_to_dist(float angle);

#if (defined(WIN32) || defined(WIN64)) && !defined(FREE_WINDOWS)
extern double copysign(double x, double y);
extern double round(double x);
#endif

double double_round(double x, int ndigits);

#endif /* __BLI_MATH_BASE_H__ */

