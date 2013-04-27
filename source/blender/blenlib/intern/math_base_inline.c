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

/** \file blender/blenlib/intern/math_base_inline.c
 *  \ingroup bli
 */

#ifndef __MATH_BASE_INLINE_C__
#define __MATH_BASE_INLINE_C__

#include <float.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "BLI_math_base.h"

/* copied from BLI_utildefines.h */
#ifdef __GNUC__
#  define UNLIKELY(x)     __builtin_expect(!!(x), 0)
#else
#  define UNLIKELY(x)     (x)
#endif

/* A few small defines. Keep'em local! */
#define SMALL_NUMBER  1.e-8f

MINLINE float sqrt3f(float f)
{
	if      (UNLIKELY(f == 0.0f)) return 0.0f;
	else if (UNLIKELY(f <  0.0f)) return -(float)(exp(log(-f) / 3.0));
	else                          return  (float)(exp(log( f) / 3.0));
}

MINLINE double sqrt3d(double d)
{
	if      (UNLIKELY(d == 0.0)) return 0.0;
	else if (UNLIKELY(d <  0.0)) return -exp(log(-d) / 3.0);
	else                         return  exp(log( d) / 3.0);
}

MINLINE float saacos(float fac)
{
	if      (UNLIKELY(fac <= -1.0f)) return (float)M_PI;
	else if (UNLIKELY(fac >=  1.0f)) return 0.0f;
	else                             return acosf(fac);
}

MINLINE float saasin(float fac)
{
	if      (UNLIKELY(fac <= -1.0f)) return (float)-M_PI / 2.0f;
	else if (UNLIKELY(fac >=  1.0f)) return (float) M_PI / 2.0f;
	else                             return asinf(fac);
}

MINLINE float sasqrt(float fac)
{
	if (UNLIKELY(fac <= 0.0f)) return 0.0f;
	else                       return sqrtf(fac);
}

MINLINE float saacosf(float fac)
{
	if      (UNLIKELY(fac <= -1.0f)) return (float)M_PI;
	else if (UNLIKELY(fac >=  1.0f)) return 0.0f;
	else                             return acosf(fac);
}

MINLINE float saasinf(float fac)
{
	if      (UNLIKELY(fac <= -1.0f)) return (float)-M_PI / 2.0f;
	else if (UNLIKELY(fac >=  1.0f)) return (float) M_PI / 2.0f;
	else                             return asinf(fac);
}

MINLINE float sasqrtf(float fac)
{
	if (UNLIKELY(fac <= 0.0f)) return 0.0f;
	else                       return sqrtf(fac);
}

MINLINE float interpf(float target, float origin, float fac)
{
	return (fac * target) + (1.0f - fac) * origin;
}

/* useful to calculate an even width shell, by taking the angle between 2 planes.
 * The return value is a scale on the offset.
 * no angle between planes is 1.0, as the angle between the 2 planes approaches 180d
 * the distance gets very high, 180d would be inf, but this case isn't valid */
MINLINE float shell_angle_to_dist(const float angle)
{
	return (UNLIKELY(angle < SMALL_NUMBER)) ? 1.0f : fabsf(1.0f / cosf(angle));
}

/* used for zoom values*/
MINLINE float power_of_2(float val)
{
	return (float)pow(2.0, ceil(log((double)val) / M_LN2));
}

MINLINE int is_power_of_2_i(int n)
{
	return (n & (n - 1)) == 0;
}

MINLINE int power_of_2_max_i(int n)
{
	if (is_power_of_2_i(n))
		return n;

	while (!is_power_of_2_i(n))
		n = n & (n - 1);

	return n * 2;
}

MINLINE int power_of_2_min_i(int n)
{
	while (!is_power_of_2_i(n))
		n = n & (n - 1);

	return n;
}

/* integer division that rounds 0.5 up, particularly useful for color blending
 * with integers, to avoid gradual darkening when rounding down */
MINLINE int divide_round_i(int a, int b)
{
	return (2 * a + b) / (2 * b);
}

MINLINE unsigned int highest_order_bit_i(unsigned int n)
{
	n |= (n >>  1);
	n |= (n >>  2);
	n |= (n >>  4);
	n |= (n >>  8);
	n |= (n >> 16);
	return n - (n >> 1);
}

MINLINE unsigned short highest_order_bit_s(unsigned short n)
{
	n |= (n >>  1);
	n |= (n >>  2);
	n |= (n >>  4);
	n |= (n >>  8);
	return n - (n >> 1);
}

MINLINE float min_ff(float a, float b)
{
	return (a < b) ? a : b;
}
MINLINE float max_ff(float a, float b)
{
	return (a > b) ? a : b;
}

MINLINE int min_ii(int a, int b)
{
	return (a < b) ? a : b;
}
MINLINE int max_ii(int a, int b)
{
	return (b < a) ? a : b;
}

MINLINE float min_fff(float a, float b, float c)
{
	return min_ff(min_ff(a, b), c);
}
MINLINE float max_fff(float a, float b, float c)
{
	return max_ff(max_ff(a, b), c);
}

MINLINE int min_iii(int a, int b, int c)
{
	return min_ii(min_ii(a, b), c);
}
MINLINE int max_iii(int a, int b, int c)
{
	return max_ii(max_ii(a, b), c);
}

MINLINE float min_ffff(float a, float b, float c, float d)
{
	return min_ff(min_fff(a, b, c), d);
}
MINLINE float max_ffff(float a, float b, float c, float d)
{
	return max_ff(max_fff(a, b, c), d);
}

MINLINE int min_iiii(int a, int b, int c, int d)
{
	return min_ii(min_iii(a, b, c), d);
}
MINLINE int max_iiii(int a, int b, int c, int d)
{
	return max_ii(max_iii(a, b, c), d);
}

MINLINE float signf(float f)
{
	return (f < 0.f) ? -1.f : 1.f;
}


#endif /* __MATH_BASE_INLINE_C__ */
