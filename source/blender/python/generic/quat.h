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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Joseph Gilbert
 *
 * ***** END GPL LICENSE BLOCK *****
 *
 */

#ifndef EXPP_quat_h
#define EXPP_quat_h

#include <Python.h>
#include "../intern/bpy_compat.h"

extern PyTypeObject quaternion_Type;

#define QuaternionObject_Check(v) (Py_TYPE(v) == &quaternion_Type)

typedef struct { /* keep aligned with BaseMathObject in Mathutils.h */
	PyObject_VAR_HEAD 
	float *quat;				/* 1D array of data (alias) */
	PyObject *cb_user;			/* if this vector references another object, otherwise NULL, *Note* this owns its reference */
	unsigned char cb_type;		/* which user funcs do we adhere to, RNA, GameObject, etc */
	unsigned char cb_subtype;	/* subtype: location, rotation... to avoid defining many new functions for every attribute of the same type */
	unsigned char wrapped;		/* wrapped data type? */
	/* end BaseMathObject */

} QuaternionObject;

/*struct data contains a pointer to the actual data that the
object uses. It can use either PyMem allocated data (which will
be stored in py_data) or be a wrapper for data allocated through
blender (stored in blend_data). This is an either/or struct not both*/

//prototypes
PyObject *newQuaternionObject( float *quat, int type );
PyObject *newQuaternionObject_cb(PyObject *cb_user, int cb_type, int cb_subtype);

#endif				/* EXPP_quat_h */
