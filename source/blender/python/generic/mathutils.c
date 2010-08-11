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
 * Contributor(s): Joseph Gilbert, Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/* Note: Changes to Mathutils since 2.4x
 * use radians rather then degrees
 * - Mathutils.Vector/Euler/Quaternion(), now only take single sequence arguments.
 * - Mathutils.MidpointVecs --> vector.lerp(other, fac)
 * - Mathutils.AngleBetweenVecs --> vector.angle(other)
 * - Mathutils.ProjectVecs --> vector.project(other)
 * - Mathutils.DifferenceQuats --> quat.difference(other)
 * - Mathutils.Slerp --> quat.slerp(other, fac)
 * - Mathutils.Rand: removed, use pythons random module
 * - Mathutils.RotationMatrix(angle, size, axis_flag, axis) --> Mathutils.RotationMatrix(angle, size, axis); merge axis & axis_flag args
 * - Matrix.scalePart --> Matrix.scale_part
 * - Matrix.translationPart --> Matrix.translation_part
 * - Matrix.rotationPart --> Matrix.rotation_part
 * - toMatrix --> to_matrix
 * - toEuler --> to_euler
 * - toQuat --> to_quat
 * - Vector.toTrackQuat --> Vector.to_track_quat
 * - Quaternion * Quaternion --> cross product (not dot product)
 *
 * moved into class functions.
 * - Mathutils.RotationMatrix -> mathutils.Matrix.Rotation
 * - Mathutils.ScaleMatrix -> mathutils.Matrix.Scale
 * - Mathutils.ShearMatrix -> mathutils.Matrix.Shear
 * - Mathutils.TranslationMatrix -> mathutils.Matrix.Translation
 * - Mathutils.OrthoProjectionMatrix -> mathutils.Matrix.OrthoProjection
 *
 * Moved to Geometry module: Intersect, TriangleArea, TriangleNormal, QuadNormal, LineIntersect
 */

#include "mathutils.h"

#include "BLI_math.h"

//-------------------------DOC STRINGS ---------------------------
static char M_Mathutils_doc[] =
"This module provides access to matrices, eulers, quaternions and vectors.";

/* helper functionm returns length of the 'value', -1 on error */
int mathutils_array_parse(float *array, int array_min, int array_max, PyObject *value, const char *error_prefix)
{
	PyObject *value_fast= NULL;

	int i, size;

	/* non list/tuple cases */
	if(!(value_fast=PySequence_Fast(value, error_prefix))) {
		/* PySequence_Fast sets the error */
		return -1;
	}

	size= PySequence_Fast_GET_SIZE(value_fast);

	if(size > array_max || size < array_min) {
		if (array_max == array_min)	PyErr_Format(PyExc_ValueError, "%.200s: sequence size is %d, expected %d", error_prefix, size, array_max);
		else						PyErr_Format(PyExc_ValueError, "%.200s: sequence size is %d, expected [%d - %d]", error_prefix, size, array_min, array_max);
		Py_DECREF(value_fast);
		return -1;
	}

	i= size;
	do {
		i--;
		if(((array[i]= PyFloat_AsDouble(PySequence_Fast_GET_ITEM(value_fast, i))) == -1.0) && PyErr_Occurred()) {
			PyErr_Format(PyExc_ValueError, "%.200s: sequence index %d is not a float", error_prefix, i);
			Py_DECREF(value_fast);
			return -1;
		}
	} while(i);

	Py_XDECREF(value_fast);
	return size;
}

//----------------------------------MATRIX FUNCTIONS--------------------


/* Utility functions */

// LomontRRDCompare4, Ever Faster Float Comparisons by Randy Dillon
#define SIGNMASK(i) (-(int)(((unsigned int)(i))>>31))

int EXPP_FloatsAreEqual(float af, float bf, int maxDiff)
{	// solid, fast routine across all platforms
	// with constant time behavior
	int ai = *(int *)(&af);
	int bi = *(int *)(&bf);
	int test = SIGNMASK(ai^bi);
	int diff, v1, v2;

	assert((0 == test) || (0xFFFFFFFF == test));
	diff = (ai ^ (test & 0x7fffffff)) - bi;
	v1 = maxDiff + diff;
	v2 = maxDiff - diff;
	return (v1|v2) >= 0;
}

/*---------------------- EXPP_VectorsAreEqual -------------------------
  Builds on EXPP_FloatsAreEqual to test vectors */
int EXPP_VectorsAreEqual(float *vecA, float *vecB, int size, int floatSteps)
{
	int x;
	for (x=0; x< size; x++){
		if (EXPP_FloatsAreEqual(vecA[x], vecB[x], floatSteps) == 0)
			return 0;
	}
	return 1;
}


/* Mathutils Callbacks */

/* for mathutils internal use only, eventually should re-alloc but to start with we only have a few users */
Mathutils_Callback *mathutils_callbacks[8] = {NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL};

int Mathutils_RegisterCallback(Mathutils_Callback *cb)
{
	int i;
	
	/* find the first free slot */
	for(i= 0; mathutils_callbacks[i]; i++) {
		if(mathutils_callbacks[i]==cb) /* already registered? */
			return i;
	}
	
	mathutils_callbacks[i] = cb;
	return i;
}

/* use macros to check for NULL */
int _BaseMathObject_ReadCallback(BaseMathObject *self)
{
	Mathutils_Callback *cb= mathutils_callbacks[self->cb_type];
	if(cb->get(self, self->cb_subtype))
		return 1;

	if(!PyErr_Occurred())
		PyErr_Format(PyExc_SystemError, "%s user has become invalid", Py_TYPE(self)->tp_name);
	return 0;
}

int _BaseMathObject_WriteCallback(BaseMathObject *self)
{
	Mathutils_Callback *cb= mathutils_callbacks[self->cb_type];
	if(cb->set(self, self->cb_subtype))
		return 1;

	if(!PyErr_Occurred())
		PyErr_Format(PyExc_SystemError, "%s user has become invalid", Py_TYPE(self)->tp_name);
	return 0;
}

int _BaseMathObject_ReadIndexCallback(BaseMathObject *self, int index)
{
	Mathutils_Callback *cb= mathutils_callbacks[self->cb_type];
	if(cb->get_index(self, self->cb_subtype, index))
		return 1;

	if(!PyErr_Occurred())
		PyErr_Format(PyExc_SystemError, "%s user has become invalid", Py_TYPE(self)->tp_name);
	return 0;
}

int _BaseMathObject_WriteIndexCallback(BaseMathObject *self, int index)
{
	Mathutils_Callback *cb= mathutils_callbacks[self->cb_type];
	if(cb->set_index(self, self->cb_subtype, index))
		return 1;

	if(!PyErr_Occurred())
		PyErr_Format(PyExc_SystemError, "%s user has become invalid", Py_TYPE(self)->tp_name);
	return 0;
}

/* BaseMathObject generic functions for all mathutils types */
char BaseMathObject_Owner_doc[] = "The item this is wrapping or None  (readonly).";
PyObject *BaseMathObject_getOwner( BaseMathObject * self, void *type )
{
	PyObject *ret= self->cb_user ? self->cb_user : Py_None;
	Py_INCREF(ret);
	return ret;
}

char BaseMathObject_Wrapped_doc[] = "True when this object wraps external data (readonly).\n\n:type: boolean";
PyObject *BaseMathObject_getWrapped( BaseMathObject *self, void *type )
{
	return PyBool_FromLong((self->wrapped == Py_WRAP) ? 1:0);
}

void BaseMathObject_dealloc(BaseMathObject * self)
{
	/* only free non wrapped */
	if(self->wrapped != Py_WRAP)
		PyMem_Free(self->data);

	Py_XDECREF(self->cb_user);
	Py_TYPE(self)->tp_free(self); // PyObject_DEL(self); // breaks subtypes
}

/*----------------------------MODULE INIT-------------------------*/
struct PyMethodDef M_Mathutils_methods[] = {
	{NULL, NULL, 0, NULL}
};

static struct PyModuleDef M_Mathutils_module_def = {
	PyModuleDef_HEAD_INIT,
	"mathutils",  /* m_name */
	M_Mathutils_doc,  /* m_doc */
	0,  /* m_size */
	M_Mathutils_methods,  /* m_methods */
	0,  /* m_reload */
	0,  /* m_traverse */
	0,  /* m_clear */
	0,  /* m_free */
};

PyObject *Mathutils_Init(void)
{
	PyObject *submodule;
	
	if( PyType_Ready( &vector_Type ) < 0 )
		return NULL;
	if( PyType_Ready( &matrix_Type ) < 0 )
		return NULL;	
	if( PyType_Ready( &euler_Type ) < 0 )
		return NULL;
	if( PyType_Ready( &quaternion_Type ) < 0 )
		return NULL;
	if( PyType_Ready( &color_Type ) < 0 )
		return NULL;

	submodule = PyModule_Create(&M_Mathutils_module_def);
	PyDict_SetItemString(PySys_GetObject("modules"), M_Mathutils_module_def.m_name, submodule);
	
	/* each type has its own new() function */
	PyModule_AddObject( submodule, "Vector",		(PyObject *)&vector_Type );
	PyModule_AddObject( submodule, "Matrix",		(PyObject *)&matrix_Type );
	PyModule_AddObject( submodule, "Euler",			(PyObject *)&euler_Type );
	PyModule_AddObject( submodule, "Quaternion",	(PyObject *)&quaternion_Type );
	PyModule_AddObject( submodule, "Color",			(PyObject *)&color_Type );
	
	mathutils_matrix_vector_cb_index= Mathutils_RegisterCallback(&mathutils_matrix_vector_cb);

	return (submodule);
}
