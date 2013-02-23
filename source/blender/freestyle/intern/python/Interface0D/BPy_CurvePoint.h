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
 * The Original Code is Copyright (C) 2010 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file source/blender/freestyle/intern/python/Interface0D/BPy_CurvePoint.h
 *  \ingroup freestyle
 */

#ifndef __FREESTYLE_PYTHON_CURVEPOINT_H__
#define __FREESTYLE_PYTHON_CURVEPOINT_H__

#include "../BPy_Interface0D.h"
#include "../../stroke/Curve.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

#include <Python.h>

extern PyTypeObject CurvePoint_Type;

#define BPy_CurvePoint_Check(v) (PyObject_IsInstance((PyObject *)v, (PyObject *)&CurvePoint_Type))

/*---------------------------Python BPy_CurvePoint structure definition----------*/
typedef struct {
	BPy_Interface0D py_if0D;
	CurvePoint *cp;
} BPy_CurvePoint;

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

#endif /* __FREESTYLE_PYTHON_CURVEPOINT_H__ */
