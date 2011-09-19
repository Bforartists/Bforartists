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
 * This is a new part of Blender.
 *
 * Contributor(s): Joseph Gilbert
 *
 * ***** END GPL LICENSE BLOCK *****
*/

/** \file blender/python/generic/mathutils.h
 *  \ingroup pygen
 */

//Include this file for access to vector, quat, matrix, euler, etc...

#ifndef MATHUTILS_H
#define MATHUTILS_H

/* Can cast different mathutils types to this, use for generic funcs */

extern char BaseMathObject_Wrapped_doc[];
extern char BaseMathObject_Owner_doc[];

#define BASE_MATH_MEMBERS(_data) \
	PyObject_VAR_HEAD \
	float *_data;				/* array of data (alias), wrapped status depends on wrapped status */ \
	PyObject *cb_user;			/* if this vector references another object, otherwise NULL, *Note* this owns its reference */ \
	unsigned char cb_type;		/* which user funcs do we adhere to, RNA, GameObject, etc */ \
	unsigned char cb_subtype;	/* subtype: location, rotation... to avoid defining many new functions for every attribute of the same type */ \
	unsigned char wrapped;		/* wrapped data type? */ \

typedef struct {
	BASE_MATH_MEMBERS(data)
} BaseMathObject;

#include "mathutils_Vector.h"
#include "mathutils_Matrix.h"
#include "mathutils_Quaternion.h"
#include "mathutils_Euler.h"
#include "mathutils_Color.h"
#include "mathutils_geometry.h"

PyObject *BaseMathObject_getOwner( BaseMathObject * self, void * );
PyObject *BaseMathObject_getWrapped( BaseMathObject *self, void * );

int BaseMathObject_traverse(BaseMathObject *self, visitproc visit, void *arg);
int BaseMathObject_clear(BaseMathObject *self);
void BaseMathObject_dealloc(BaseMathObject * self);

PyMODINIT_FUNC PyInit_mathutils(void);

int EXPP_FloatsAreEqual(float A, float B, int floatSteps);
int EXPP_VectorsAreEqual(float *vecA, float *vecB, int size, int floatSteps);

#define Py_NEW  1
#define Py_WRAP 2

typedef struct Mathutils_Callback Mathutils_Callback;

typedef int (*BaseMathCheckFunc)(BaseMathObject *);							/* checks the user is still valid */
typedef int (*BaseMathGetFunc)(BaseMathObject *, int);				/* gets the vector from the user */
typedef int (*BaseMathSetFunc)(BaseMathObject *, int);				/* sets the users vector values once the vector is modified */
typedef int (*BaseMathGetIndexFunc)(BaseMathObject *, int, int);	/* same as above but only for an index */
typedef int (*BaseMathSetIndexFunc)(BaseMathObject *, int, int);	/* same as above but only for an index */

struct Mathutils_Callback {
	BaseMathCheckFunc		check;
	BaseMathGetFunc			get;
	BaseMathSetFunc			set;
	BaseMathGetIndexFunc	get_index;
	BaseMathSetIndexFunc	set_index;
};

int Mathutils_RegisterCallback(Mathutils_Callback *cb);

int _BaseMathObject_ReadCallback(BaseMathObject *self);
int _BaseMathObject_WriteCallback(BaseMathObject *self);
int _BaseMathObject_ReadIndexCallback(BaseMathObject *self, int index);
int _BaseMathObject_WriteIndexCallback(BaseMathObject *self, int index);

/* since this is called so often avoid where possible */
#define BaseMath_ReadCallback(_self) (((_self)->cb_user ?	_BaseMathObject_ReadCallback((BaseMathObject *)_self):0))
#define BaseMath_WriteCallback(_self) (((_self)->cb_user ?_BaseMathObject_WriteCallback((BaseMathObject *)_self):0))
#define BaseMath_ReadIndexCallback(_self, _index) (((_self)->cb_user ?	_BaseMathObject_ReadIndexCallback((BaseMathObject *)_self, _index):0))
#define BaseMath_WriteIndexCallback(_self, _index) (((_self)->cb_user ?	_BaseMathObject_WriteIndexCallback((BaseMathObject *)_self, _index):0))

/* utility func */
int mathutils_array_parse(float *array, int array_min, int array_max, PyObject *value, const char *error_prefix);
int mathutils_any_to_rotmat(float rmat[3][3], PyObject *value, const char *error_prefix);

int column_vector_multiplication(float rvec[4], VectorObject *vec, MatrixObject *mat);

#endif /* MATHUTILS_H */
