/*
 * $Id$
 *
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
 * The Original Code is: all of this file.
 *
 * Contributor(s): Willian P. Germano & Joseph Gilbert
 *
 * ***** END GPL LICENSE BLOCK *****
 *
 */

/** \file blender/python/generic/mathutils_Vector.h
 *  \ingroup pygen
 */


#ifndef MATHUTILS_VECTOR_H
#define MATHUTILS_VECTOR_H

extern PyTypeObject vector_Type;
#define VectorObject_Check(_v) PyObject_TypeCheck((_v), &vector_Type)

typedef struct {
	BASE_MATH_MEMBERS(vec)

	unsigned char size;			/* vec size 2,3 or 4 */
} VectorObject;

/*prototypes*/
PyObject *newVectorObject(float *vec, const int size, const int type, PyTypeObject *base_type);
PyObject *newVectorObject_cb(PyObject *user, int size, int callback_type, int subtype);

#endif				/* MATHUTILS_VECTOR_H */
