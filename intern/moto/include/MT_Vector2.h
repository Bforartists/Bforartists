/**
 * $Id$
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

/*

 * Copyright (c) 2000 Gino van den Bergen <gino@acm.org>
 *
 * Permission to use, copy, modify, distribute and sell this software
 * and its documentation for any purpose is hereby granted without fee,
 * provided that the above copyright notice appear in all copies and
 * that both that copyright notice and this permission notice appear
 * in supporting documentation.  Gino van den Bergen makes no
 * representations about the suitability of this software for any
 * purpose.  It is provided "as is" without express or implied warranty.
 *
 */

#ifndef MT_VECTOR2_H
#define MT_VECTOR2_H

#include <MT_assert.h>
#include "MT_Tuple2.h"

class MT_Vector2 : public MT_Tuple2 {
public:
    MT_Vector2() {}
    MT_Vector2(const float *v) : MT_Tuple2(v) {}
    MT_Vector2(const double *v) : MT_Tuple2(v) {}
    MT_Vector2(MT_Scalar xx, MT_Scalar yy) : MT_Tuple2(xx, yy) {}
  
    MT_Vector2& operator+=(const MT_Vector2& v);
    MT_Vector2& operator-=(const MT_Vector2& v);
    MT_Vector2& operator*=(MT_Scalar s);
    MT_Vector2& operator/=(MT_Scalar s);
  
    MT_Scalar   dot(const MT_Vector2& v) const; 

    MT_Scalar   length2() const;
    MT_Scalar   length() const;

    MT_Vector2  absolute() const;

    void        normalize();
    MT_Vector2  normalized() const;

    void        scale(MT_Scalar x, MT_Scalar y); 
    MT_Vector2  scaled(MT_Scalar x, MT_Scalar y) const; 
    
    bool        fuzzyZero() const; 

    MT_Scalar   angle(const MT_Vector2& v) const;
    MT_Vector2  cross(const MT_Vector2& v) const;
    MT_Scalar   triple(const MT_Vector2& v1, const MT_Vector2& v2) const;

    int         closestAxis() const;

    static MT_Vector2 random();
};

MT_Vector2 operator+(const MT_Vector2& v1, const MT_Vector2& v2);
MT_Vector2 operator-(const MT_Vector2& v1, const MT_Vector2& v2);
MT_Vector2 operator-(const MT_Vector2& v);
MT_Vector2 operator*(const MT_Vector2& v, MT_Scalar s);
MT_Vector2 operator*(MT_Scalar s, const MT_Vector2& v);
MT_Vector2 operator/(const MT_Vector2& v, MT_Scalar s);

MT_Scalar  MT_dot(const MT_Vector2& v1, const MT_Vector2& v2);

MT_Scalar  MT_length2(const MT_Vector2& v);
MT_Scalar  MT_length(const MT_Vector2& v);

bool       MT_fuzzyZero(const MT_Vector2& v);
bool       MT_fuzzyEqual(const MT_Vector2& v1, const MT_Vector2& v2);

MT_Scalar  MT_angle(const MT_Vector2& v1, const MT_Vector2& v2);
MT_Vector2 MT_cross(const MT_Vector2& v1, const MT_Vector2& v2);
MT_Scalar  MT_triple(const MT_Vector2& v1, const MT_Vector2& v2, 
                     const MT_Vector2& v3);

#ifdef GEN_INLINED
#include "MT_Vector2.inl"
#endif

#endif

