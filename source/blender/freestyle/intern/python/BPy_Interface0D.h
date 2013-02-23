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

/** \file source/blender/freestyle/intern/python/BPy_Interface0D.h
 *  \ingroup freestyle
 */

#ifndef FREESTYLE_PYTHON_INTERFACE0D_H
#define FREESTYLE_PYTHON_INTERFACE0D_H

#include <Python.h>

#include "../view_map/Interface0D.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

extern PyTypeObject Interface0D_Type;

#define BPy_Interface0D_Check(v)	(  PyObject_IsInstance( (PyObject *) v, (PyObject *) &Interface0D_Type)  )

/*---------------------------Python BPy_Interface0D structure definition----------*/
typedef struct {
	PyObject_HEAD
	Interface0D *if0D;
	int borrowed; /* non-zero if *if0D is a borrowed object */
} BPy_Interface0D;

/*---------------------------Python BPy_Interface0D visible prototypes-----------*/

int Interface0D_Init( PyObject *module );

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

#endif /* FREESTYLE_PYTHON_INTERFACE0D_H */
