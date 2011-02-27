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
 *
 * Contributor(s): Joseph Gilbert
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/python/generic/mathutils_Quaternion.c
 *  \ingroup pygen
 */


#include <Python.h>

#include "mathutils.h"

#include "BLI_math.h"
#include "BLI_utildefines.h"

#define QUAT_SIZE 4

static PyObject *quat__apply_to_copy(PyNoArgsFunction quat_func, QuaternionObject *self);
static PyObject *Quaternion_copy(QuaternionObject *self);

//-----------------------------METHODS------------------------------

/* note: BaseMath_ReadCallback must be called beforehand */
static PyObject *Quaternion_to_tuple_ext(QuaternionObject *self, int ndigits)
{
	PyObject *ret;
	int i;

	ret= PyTuple_New(QUAT_SIZE);

	if(ndigits >= 0) {
		for(i= 0; i < QUAT_SIZE; i++) {
			PyTuple_SET_ITEM(ret, i, PyFloat_FromDouble(double_round((double)self->quat[i], ndigits)));
		}
	}
	else {
		for(i= 0; i < QUAT_SIZE; i++) {
			PyTuple_SET_ITEM(ret, i, PyFloat_FromDouble(self->quat[i]));
		}
	}

	return ret;
}

static char Quaternion_to_euler_doc[] =
".. method:: to_euler(order, euler_compat)\n"
"\n"
"   Return Euler representation of the quaternion.\n"
"\n"
"   :arg order: Optional rotation order argument in ['XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'].\n"
"   :type order: string\n"
"   :arg euler_compat: Optional euler argument the new euler will be made compatible with (no axis flipping between them). Useful for converting a series of matrices to animation curves.\n"
"   :type euler_compat: :class:`Euler`\n"
"   :return: Euler representation of the quaternion.\n"
"   :rtype: :class:`Euler`\n"
;
static PyObject *Quaternion_to_euler(QuaternionObject *self, PyObject *args)
{
	float tquat[4];
	float eul[3];
	const char *order_str= NULL;
	short order= EULER_ORDER_XYZ;
	EulerObject *eul_compat = NULL;

	if(!PyArg_ParseTuple(args, "|sO!:to_euler", &order_str, &euler_Type, &eul_compat))
		return NULL;

	if(!BaseMath_ReadCallback(self))
		return NULL;

	if(order_str) {
		order= euler_order_from_string(order_str, "Matrix.to_euler()");

		if(order == -1)
			return NULL;
	}

	normalize_qt_qt(tquat, self->quat);

	if(eul_compat) {
		float mat[3][3];

		if(!BaseMath_ReadCallback(eul_compat))
			return NULL;

		quat_to_mat3(mat, tquat);

		if(order == EULER_ORDER_XYZ)	mat3_to_compatible_eul(eul, eul_compat->eul, mat);
		else							mat3_to_compatible_eulO(eul, eul_compat->eul, order, mat);
	}
	else {
		if(order == EULER_ORDER_XYZ)	quat_to_eul(eul, tquat);
		else							quat_to_eulO(eul, order, tquat);
	}

	return newEulerObject(eul, order, Py_NEW, NULL);
}
//----------------------------Quaternion.toMatrix()------------------
static char Quaternion_to_matrix_doc[] =
".. method:: to_matrix()\n"
"\n"
"   Return a matrix representation of the quaternion.\n"
"\n"
"   :return: A 3x3 rotation matrix representation of the quaternion.\n"
"   :rtype: :class:`Matrix`\n"
;
static PyObject *Quaternion_to_matrix(QuaternionObject *self)
{
	float mat[9]; /* all values are set */

	if(!BaseMath_ReadCallback(self))
		return NULL;

	quat_to_mat3( (float (*)[3]) mat,self->quat);
	return newMatrixObject(mat, 3, 3, Py_NEW, NULL);
}

//----------------------------Quaternion.cross(other)------------------
static char Quaternion_cross_doc[] =
".. method:: cross(other)\n"
"\n"
"   Return the cross product of this quaternion and another.\n"
"\n"
"   :arg other: The other quaternion to perform the cross product with.\n"
"   :type other: :class:`Quaternion`\n"
"   :return: The cross product.\n"
"   :rtype: :class:`Quaternion`\n"
;
static PyObject *Quaternion_cross(QuaternionObject *self, PyObject *value)
{
	float quat[QUAT_SIZE], tquat[QUAT_SIZE];

	if(!BaseMath_ReadCallback(self))
		return NULL;

	if(mathutils_array_parse(tquat, QUAT_SIZE, QUAT_SIZE, value, "quaternion.cross(other), invalid 'other' arg") == -1)
		return NULL;

	mul_qt_qtqt(quat, self->quat, tquat);
	return newQuaternionObject(quat, Py_NEW, Py_TYPE(self));
}

//----------------------------Quaternion.dot(other)------------------
static char Quaternion_dot_doc[] =
".. method:: dot(other)\n"
"\n"
"   Return the dot product of this quaternion and another.\n"
"\n"
"   :arg other: The other quaternion to perform the dot product with.\n"
"   :type other: :class:`Quaternion`\n"
"   :return: The dot product.\n"
"   :rtype: :class:`Quaternion`\n"
;
static PyObject *Quaternion_dot(QuaternionObject *self, PyObject *value)
{
	float tquat[QUAT_SIZE];

	if(!BaseMath_ReadCallback(self))
		return NULL;

	if(mathutils_array_parse(tquat, QUAT_SIZE, QUAT_SIZE, value, "quaternion.dot(other), invalid 'other' arg") == -1)
		return NULL;

	return PyFloat_FromDouble(dot_qtqt(self->quat, tquat));
}

static char Quaternion_difference_doc[] =
".. function:: difference(other)\n"
"\n"
"   Returns a quaternion representing the rotational difference.\n"
"\n"
"   :arg other: second quaternion.\n"
"   :type other: :class:`Quaternion`\n"
"   :return: the rotational difference between the two quat rotations.\n"
"   :rtype: :class:`Quaternion`\n"
;
static PyObject *Quaternion_difference(QuaternionObject *self, PyObject *value)
{
	float tquat[QUAT_SIZE], quat[QUAT_SIZE];

	if(!BaseMath_ReadCallback(self))
		return NULL;

	if(mathutils_array_parse(tquat, QUAT_SIZE, QUAT_SIZE, value, "quaternion.difference(other), invalid 'other' arg") == -1)
		return NULL;

	rotation_between_quats_to_quat(quat, self->quat, tquat);

	return newQuaternionObject(quat, Py_NEW, Py_TYPE(self));
}

static char Quaternion_slerp_doc[] =
".. function:: slerp(other, factor)\n"
"\n"
"   Returns the interpolation of two quaternions.\n"
"\n"
"   :arg other: value to interpolate with.\n"
"   :type other: :class:`Quaternion`\n"
"   :arg factor: The interpolation value in [0.0, 1.0].\n"
"   :type factor: float\n"
"   :return: The interpolated rotation.\n"
"   :rtype: :class:`Quaternion`\n"
;
static PyObject *Quaternion_slerp(QuaternionObject *self, PyObject *args)
{
	PyObject *value;
	float tquat[QUAT_SIZE], quat[QUAT_SIZE], fac;

	if(!PyArg_ParseTuple(args, "Of:slerp", &value, &fac)) {
		PyErr_SetString(PyExc_TypeError, "quat.slerp(): expected Quaternion types and float");
		return NULL;
	}

	if(!BaseMath_ReadCallback(self))
		return NULL;

	if(mathutils_array_parse(tquat, QUAT_SIZE, QUAT_SIZE, value, "quaternion.slerp(other), invalid 'other' arg") == -1)
		return NULL;

	if(fac > 1.0f || fac < 0.0f) {
		PyErr_SetString(PyExc_AttributeError, "quat.slerp(): interpolation factor must be between 0.0 and 1.0");
		return NULL;
	}

	interp_qt_qtqt(quat, self->quat, tquat, fac);

	return newQuaternionObject(quat, Py_NEW, Py_TYPE(self));
}

static char Quaternion_rotate_doc[] =
".. method:: rotate(other)\n"
"\n"
"   Rotates the quaternion a by another mathutils value.\n"
"\n"
"   :arg other: rotation component of mathutils value\n"
"   :type other: :class:`Euler`, :class:`Quaternion` or :class:`Matrix`\n"
;
static PyObject *Quaternion_rotate(QuaternionObject *self, PyObject *value)
{
	float self_rmat[3][3], other_rmat[3][3], rmat[3][3];
	float tquat[4], length;

	if(!BaseMath_ReadCallback(self))
		return NULL;

	if(mathutils_any_to_rotmat(other_rmat, value, "quaternion.rotate(value)") == -1)
		return NULL;

	length= normalize_qt_qt(tquat, self->quat);
	quat_to_mat3(self_rmat, tquat);
	mul_m3_m3m3(rmat, self_rmat, other_rmat);

	mat3_to_quat(self->quat, rmat);
	mul_qt_fl(self->quat, length); /* maintain length after rotating */

	(void)BaseMath_WriteCallback(self);
	Py_RETURN_NONE;
}

//----------------------------Quaternion.normalize()----------------
//normalize the axis of rotation of [theta,vector]
static char Quaternion_normalize_doc[] =
".. function:: normalize()\n"
"\n"
"   Normalize the quaternion.\n"
;
static PyObject *Quaternion_normalize(QuaternionObject *self)
{
	if(!BaseMath_ReadCallback(self))
		return NULL;

	normalize_qt(self->quat);

	(void)BaseMath_WriteCallback(self);
	Py_RETURN_NONE;
}
static char Quaternion_normalized_doc[] =
".. function:: normalized()\n"
"\n"
"   Return a new normalized quaternion.\n"
"\n"
"   :return: a normalized copy.\n"
"   :rtype: :class:`Quaternion`\n"
;
static PyObject *Quaternion_normalized(QuaternionObject *self)
{
	return quat__apply_to_copy((PyNoArgsFunction)Quaternion_normalize, self);
}

//----------------------------Quaternion.invert()------------------
static char Quaternion_invert_doc[] =
".. function:: invert()\n"
"\n"
"   Set the quaternion to its inverse.\n"
;
static PyObject *Quaternion_invert(QuaternionObject *self)
{
	if(!BaseMath_ReadCallback(self))
		return NULL;

	invert_qt(self->quat);

	(void)BaseMath_WriteCallback(self);
	Py_RETURN_NONE;
}
static char Quaternion_inverted_doc[] =
".. function:: inverted()\n"
"\n"
"   Return a new, inverted quaternion.\n"
"\n"
"   :return: the inverted value.\n"
"   :rtype: :class:`Quaternion`\n"
;
static PyObject *Quaternion_inverted(QuaternionObject *self)
{
	return quat__apply_to_copy((PyNoArgsFunction)Quaternion_invert, self);
}

//----------------------------Quaternion.identity()-----------------
static char Quaternion_identity_doc[] =
".. function:: identity()\n"
"\n"
"   Set the quaternion to an identity quaternion.\n"
"\n"
"   :return: an instance of itself.\n"
"   :rtype: :class:`Quaternion`\n"
;
static PyObject *Quaternion_identity(QuaternionObject *self)
{
	if(!BaseMath_ReadCallback(self))
		return NULL;

	unit_qt(self->quat);

	(void)BaseMath_WriteCallback(self);
	Py_RETURN_NONE;
}
//----------------------------Quaternion.negate()-------------------
static char Quaternion_negate_doc[] =
".. function:: negate()\n"
"\n"
"   Set the quaternion to its negative.\n"
"\n"
"   :return: an instance of itself.\n"
"   :rtype: :class:`Quaternion`\n"
;
static PyObject *Quaternion_negate(QuaternionObject *self)
{
	if(!BaseMath_ReadCallback(self))
		return NULL;

	mul_qt_fl(self->quat, -1.0f);

	(void)BaseMath_WriteCallback(self);
	Py_RETURN_NONE;
}
//----------------------------Quaternion.conjugate()----------------
static char Quaternion_conjugate_doc[] =
".. function:: conjugate()\n"
"\n"
"   Set the quaternion to its conjugate (negate x, y, z).\n"
;
static PyObject *Quaternion_conjugate(QuaternionObject *self)
{
	if(!BaseMath_ReadCallback(self))
		return NULL;

	conjugate_qt(self->quat);

	(void)BaseMath_WriteCallback(self);
	Py_RETURN_NONE;
}
static char Quaternion_conjugated_doc[] =
".. function:: conjugated()\n"
"\n"
"   Return a new conjugated quaternion.\n"
"\n"
"   :return: a new quaternion.\n"
"   :rtype: :class:`Quaternion`\n"
;
static PyObject *Quaternion_conjugated(QuaternionObject *self)
{
	return quat__apply_to_copy((PyNoArgsFunction)Quaternion_conjugate, self);
}

//----------------------------Quaternion.copy()----------------
static char Quaternion_copy_doc[] =
".. function:: copy()\n"
"\n"
"   Returns a copy of this quaternion.\n"
"\n"
"   :return: A copy of the quaternion.\n"
"   :rtype: :class:`Quaternion`\n"
"\n"
"   .. note:: use this to get a copy of a wrapped quaternion with no reference to the original data.\n"
;
static PyObject *Quaternion_copy(QuaternionObject *self)
{
	if(!BaseMath_ReadCallback(self))
		return NULL;

	return newQuaternionObject(self->quat, Py_NEW, Py_TYPE(self));
}

//----------------------------print object (internal)--------------
//print the object to screen
static PyObject *Quaternion_repr(QuaternionObject *self)
{
	PyObject *ret, *tuple;

	if(!BaseMath_ReadCallback(self))
		return NULL;

	tuple= Quaternion_to_tuple_ext(self, -1);

	ret= PyUnicode_FromFormat("Quaternion(%R)", tuple);

	Py_DECREF(tuple);
	return ret;
}

static PyObject* Quaternion_richcmpr(PyObject *a, PyObject *b, int op)
{
	PyObject *res;
	int ok= -1; /* zero is true */

	if (QuaternionObject_Check(a) && QuaternionObject_Check(b)) {
		QuaternionObject *quatA= (QuaternionObject *)a;
		QuaternionObject *quatB= (QuaternionObject *)b;

		if(!BaseMath_ReadCallback(quatA) || !BaseMath_ReadCallback(quatB))
			return NULL;

		ok= (EXPP_VectorsAreEqual(quatA->quat, quatB->quat, QUAT_SIZE, 1)) ? 0 : -1;
	}

	switch (op) {
	case Py_NE:
		ok = !ok; /* pass through */
	case Py_EQ:
		res = ok ? Py_False : Py_True;
		break;

	case Py_LT:
	case Py_LE:
	case Py_GT:
	case Py_GE:
		res = Py_NotImplemented;
		break;
	default:
		PyErr_BadArgument();
		return NULL;
	}

	return Py_INCREF(res), res;
}

//---------------------SEQUENCE PROTOCOLS------------------------
//----------------------------len(object)------------------------
//sequence length
static int Quaternion_len(QuaternionObject *UNUSED(self))
{
	return QUAT_SIZE;
}
//----------------------------object[]---------------------------
//sequence accessor (get)
static PyObject *Quaternion_item(QuaternionObject *self, int i)
{
	if(i<0)	i= QUAT_SIZE-i;

	if(i < 0 || i >= QUAT_SIZE) {
		PyErr_SetString(PyExc_IndexError, "quaternion[attribute]: array index out of range");
		return NULL;
	}

	if(!BaseMath_ReadIndexCallback(self, i))
		return NULL;

	return PyFloat_FromDouble(self->quat[i]);

}
//----------------------------object[]-------------------------
//sequence accessor (set)
static int Quaternion_ass_item(QuaternionObject *self, int i, PyObject *ob)
{
	float scalar= (float)PyFloat_AsDouble(ob);
	if(scalar==-1.0f && PyErr_Occurred()) { /* parsed item not a number */
		PyErr_SetString(PyExc_TypeError, "quaternion[index] = x: index argument not a number");
		return -1;
	}

	if(i<0)	i= QUAT_SIZE-i;

	if(i < 0 || i >= QUAT_SIZE){
		PyErr_SetString(PyExc_IndexError, "quaternion[attribute] = x: array assignment index out of range");
		return -1;
	}
	self->quat[i] = scalar;

	if(!BaseMath_WriteIndexCallback(self, i))
		return -1;

	return 0;
}
//----------------------------object[z:y]------------------------
//sequence slice (get)
static PyObject *Quaternion_slice(QuaternionObject *self, int begin, int end)
{
	PyObject *tuple;
	int count;

	if(!BaseMath_ReadCallback(self))
		return NULL;

	CLAMP(begin, 0, QUAT_SIZE);
	if (end<0) end= (QUAT_SIZE + 1) + end;
	CLAMP(end, 0, QUAT_SIZE);
	begin= MIN2(begin, end);

	tuple= PyTuple_New(end - begin);
	for(count= begin; count < end; count++) {
		PyTuple_SET_ITEM(tuple, count - begin, PyFloat_FromDouble(self->quat[count]));
	}

	return tuple;
}
//----------------------------object[z:y]------------------------
//sequence slice (set)
static int Quaternion_ass_slice(QuaternionObject *self, int begin, int end, PyObject *seq)
{
	int i, size;
	float quat[QUAT_SIZE];

	if(!BaseMath_ReadCallback(self))
		return -1;

	CLAMP(begin, 0, QUAT_SIZE);
	if (end<0) end= (QUAT_SIZE + 1) + end;
	CLAMP(end, 0, QUAT_SIZE);
	begin = MIN2(begin,end);

	if((size=mathutils_array_parse(quat, 0, QUAT_SIZE, seq, "mathutils.Quaternion[begin:end] = []")) == -1)
		return -1;

	if(size != (end - begin)){
		PyErr_SetString(PyExc_TypeError, "quaternion[begin:end] = []: size mismatch in slice assignment");
		return -1;
	}

	/* parsed well - now set in vector */
	for(i= 0; i < size; i++)
		self->quat[begin + i] = quat[i];

	(void)BaseMath_WriteCallback(self);
	return 0;
}


static PyObject *Quaternion_subscript(QuaternionObject *self, PyObject *item)
{
	if (PyIndex_Check(item)) {
		Py_ssize_t i;
		i = PyNumber_AsSsize_t(item, PyExc_IndexError);
		if (i == -1 && PyErr_Occurred())
			return NULL;
		if (i < 0)
			i += QUAT_SIZE;
		return Quaternion_item(self, i);
	} else if (PySlice_Check(item)) {
		Py_ssize_t start, stop, step, slicelength;

		if (PySlice_GetIndicesEx((void *)item, QUAT_SIZE, &start, &stop, &step, &slicelength) < 0)
			return NULL;

		if (slicelength <= 0) {
			return PyTuple_New(0);
		}
		else if (step == 1) {
			return Quaternion_slice(self, start, stop);
		}
		else {
			PyErr_SetString(PyExc_TypeError, "slice steps not supported with quaternions");
			return NULL;
		}
	}
	else {
		PyErr_Format(PyExc_TypeError, "quaternion indices must be integers, not %.200s", Py_TYPE(item)->tp_name);
		return NULL;
	}
}


static int Quaternion_ass_subscript(QuaternionObject *self, PyObject *item, PyObject *value)
{
	if (PyIndex_Check(item)) {
		Py_ssize_t i = PyNumber_AsSsize_t(item, PyExc_IndexError);
		if (i == -1 && PyErr_Occurred())
			return -1;
		if (i < 0)
			i += QUAT_SIZE;
		return Quaternion_ass_item(self, i, value);
	}
	else if (PySlice_Check(item)) {
		Py_ssize_t start, stop, step, slicelength;

		if (PySlice_GetIndicesEx((void *)item, QUAT_SIZE, &start, &stop, &step, &slicelength) < 0)
			return -1;

		if (step == 1)
			return Quaternion_ass_slice(self, start, stop, value);
		else {
			PyErr_SetString(PyExc_TypeError, "slice steps not supported with quaternion");
			return -1;
		}
	}
	else {
		PyErr_Format(PyExc_TypeError, "quaternion indices must be integers, not %.200s", Py_TYPE(item)->tp_name);
		return -1;
	}
}

//------------------------NUMERIC PROTOCOLS----------------------
//------------------------obj + obj------------------------------
//addition
static PyObject *Quaternion_add(PyObject *q1, PyObject *q2)
{
	float quat[QUAT_SIZE];
	QuaternionObject *quat1 = NULL, *quat2 = NULL;

	if(!QuaternionObject_Check(q1) || !QuaternionObject_Check(q2)) {
		PyErr_SetString(PyExc_AttributeError, "Quaternion addition: arguments not valid for this operation");
		return NULL;
	}
	quat1 = (QuaternionObject*)q1;
	quat2 = (QuaternionObject*)q2;

	if(!BaseMath_ReadCallback(quat1) || !BaseMath_ReadCallback(quat2))
		return NULL;

	add_qt_qtqt(quat, quat1->quat, quat2->quat, 1.0f);
	return newQuaternionObject(quat, Py_NEW, Py_TYPE(q1));
}
//------------------------obj - obj------------------------------
//subtraction
static PyObject *Quaternion_sub(PyObject *q1, PyObject *q2)
{
	int x;
	float quat[QUAT_SIZE];
	QuaternionObject *quat1 = NULL, *quat2 = NULL;

	if(!QuaternionObject_Check(q1) || !QuaternionObject_Check(q2)) {
		PyErr_SetString(PyExc_AttributeError, "Quaternion addition: arguments not valid for this operation");
		return NULL;
	}

	quat1 = (QuaternionObject*)q1;
	quat2 = (QuaternionObject*)q2;

	if(!BaseMath_ReadCallback(quat1) || !BaseMath_ReadCallback(quat2))
		return NULL;

	for(x = 0; x < QUAT_SIZE; x++) {
		quat[x] = quat1->quat[x] - quat2->quat[x];
	}

	return newQuaternionObject(quat, Py_NEW, Py_TYPE(q1));
}

static PyObject *quat_mul_float(QuaternionObject *quat, const float scalar)
{
	float tquat[4];
	copy_qt_qt(tquat, quat->quat);
	mul_qt_fl(tquat, scalar);
	return newQuaternionObject(tquat, Py_NEW, Py_TYPE(quat));
}

//------------------------obj * obj------------------------------
//mulplication
static PyObject *Quaternion_mul(PyObject *q1, PyObject *q2)
{
	float quat[QUAT_SIZE], scalar;
	QuaternionObject *quat1 = NULL, *quat2 = NULL;

	if(QuaternionObject_Check(q1)) {
		quat1 = (QuaternionObject*)q1;
		if(!BaseMath_ReadCallback(quat1))
			return NULL;
	}
	if(QuaternionObject_Check(q2)) {
		quat2 = (QuaternionObject*)q2;
		if(!BaseMath_ReadCallback(quat2))
			return NULL;
	}

	if(quat1 && quat2) { /* QUAT*QUAT (cross product) */
		mul_qt_qtqt(quat, quat1->quat, quat2->quat);
		return newQuaternionObject(quat, Py_NEW, Py_TYPE(q1));
	}
	/* the only case this can happen (for a supported type is "FLOAT*QUAT" ) */
	else if(quat2) { /* FLOAT*QUAT */
		if(((scalar= PyFloat_AsDouble(q1)) == -1.0 && PyErr_Occurred())==0) {
			return quat_mul_float(quat2, scalar);
		}
	}
	else if (quat1) { /* QUAT*FLOAT */
		if((((scalar= PyFloat_AsDouble(q2)) == -1.0 && PyErr_Occurred())==0)) {
			return quat_mul_float(quat1, scalar);
		}
	}
	else {
		BLI_assert(!"internal error");
	}

	PyErr_Format(PyExc_TypeError, "Quaternion multiplication: not supported between '%.200s' and '%.200s' types", Py_TYPE(q1)->tp_name, Py_TYPE(q2)->tp_name);
	return NULL;
}

/* -obj
  returns the negative of this object*/
static PyObject *Quaternion_neg(QuaternionObject *self)
{
	float tquat[QUAT_SIZE];

	if(!BaseMath_ReadCallback(self))
		return NULL;

	negate_v4_v4(tquat, self->quat);
	return newQuaternionObject(tquat, Py_NEW, Py_TYPE(self));
}


//-----------------PROTOCOL DECLARATIONS--------------------------
static PySequenceMethods Quaternion_SeqMethods = {
	(lenfunc) Quaternion_len,				/* sq_length */
	(binaryfunc) NULL,						/* sq_concat */
	(ssizeargfunc) NULL,					/* sq_repeat */
	(ssizeargfunc) Quaternion_item,			/* sq_item */
	(ssizessizeargfunc) NULL,				/* sq_slice, deprecated */
	(ssizeobjargproc) Quaternion_ass_item,	/* sq_ass_item */
	(ssizessizeobjargproc) NULL,			/* sq_ass_slice, deprecated */
	(objobjproc) NULL,						/* sq_contains */
	(binaryfunc) NULL,						/* sq_inplace_concat */
	(ssizeargfunc) NULL,					/* sq_inplace_repeat */
};

static PyMappingMethods Quaternion_AsMapping = {
	(lenfunc)Quaternion_len,
	(binaryfunc)Quaternion_subscript,
	(objobjargproc)Quaternion_ass_subscript
};

static PyNumberMethods Quaternion_NumMethods = {
	(binaryfunc)	Quaternion_add,	/*nb_add*/
	(binaryfunc)	Quaternion_sub,	/*nb_subtract*/
	(binaryfunc)	Quaternion_mul,	/*nb_multiply*/
	NULL,							/*nb_remainder*/
	NULL,							/*nb_divmod*/
	NULL,							/*nb_power*/
	(unaryfunc) 	Quaternion_neg,	/*nb_negative*/
	(unaryfunc) 	0,	/*tp_positive*/
	(unaryfunc) 	0,	/*tp_absolute*/
	(inquiry)	0,	/*tp_bool*/
	(unaryfunc)	0,	/*nb_invert*/
	NULL,				/*nb_lshift*/
	(binaryfunc)0,	/*nb_rshift*/
	NULL,				/*nb_and*/
	NULL,				/*nb_xor*/
	NULL,				/*nb_or*/
	NULL,				/*nb_int*/
	NULL,				/*nb_reserved*/
	NULL,				/*nb_float*/
	NULL,				/* nb_inplace_add */
	NULL,				/* nb_inplace_subtract */
	NULL,				/* nb_inplace_multiply */
	NULL,				/* nb_inplace_remainder */
	NULL,				/* nb_inplace_power */
	NULL,				/* nb_inplace_lshift */
	NULL,				/* nb_inplace_rshift */
	NULL,				/* nb_inplace_and */
	NULL,				/* nb_inplace_xor */
	NULL,				/* nb_inplace_or */
	NULL,				/* nb_floor_divide */
	NULL,				/* nb_true_divide */
	NULL,				/* nb_inplace_floor_divide */
	NULL,				/* nb_inplace_true_divide */
	NULL,				/* nb_index */
};

static PyObject *Quaternion_getAxis( QuaternionObject *self, void *type )
{
	return Quaternion_item(self, GET_INT_FROM_POINTER(type));
}

static int Quaternion_setAxis( QuaternionObject *self, PyObject *value, void *type )
{
	return Quaternion_ass_item(self, GET_INT_FROM_POINTER(type), value);
}

static PyObject *Quaternion_getMagnitude(QuaternionObject *self, void *UNUSED(closure))
{
	if(!BaseMath_ReadCallback(self))
		return NULL;

	return PyFloat_FromDouble(sqrt(dot_qtqt(self->quat, self->quat)));
}

static PyObject *Quaternion_getAngle(QuaternionObject *self, void *UNUSED(closure))
{
	float tquat[4];

	if(!BaseMath_ReadCallback(self))
		return NULL;

	normalize_qt_qt(tquat, self->quat);
	return PyFloat_FromDouble(2.0 * (saacos(tquat[0])));
}

static int Quaternion_setAngle(QuaternionObject *self, PyObject *value, void *UNUSED(closure))
{
	float tquat[4];
	float len;

	float axis[3], angle_dummy;
	double angle;

	if(!BaseMath_ReadCallback(self))
		return -1;

	len= normalize_qt_qt(tquat, self->quat);
	quat_to_axis_angle(axis, &angle_dummy, tquat);

	angle= PyFloat_AsDouble(value);

	if(angle==-1.0f && PyErr_Occurred()) { /* parsed item not a number */
		PyErr_SetString(PyExc_TypeError, "quaternion.angle = value: float expected");
		return -1;
	}

	angle= fmod(angle + M_PI*2, M_PI*4) - M_PI*2;

	/* If the axis of rotation is 0,0,0 set it to 1,0,0 - for zero-degree rotations */
	if( EXPP_FloatsAreEqual(axis[0], 0.0f, 10) &&
		EXPP_FloatsAreEqual(axis[1], 0.0f, 10) &&
		EXPP_FloatsAreEqual(axis[2], 0.0f, 10)
	) {
		axis[0] = 1.0f;
	}

	axis_angle_to_quat(self->quat, axis, angle);
	mul_qt_fl(self->quat, len);

	if(!BaseMath_WriteCallback(self))
		return -1;

	return 0;
}

static PyObject *Quaternion_getAxisVec(QuaternionObject *self, void *UNUSED(closure))
{
	float tquat[4];

	float axis[3];
	float angle;

	if(!BaseMath_ReadCallback(self))
		return NULL;

	normalize_qt_qt(tquat, self->quat);
	quat_to_axis_angle(axis, &angle, tquat);

	/* If the axis of rotation is 0,0,0 set it to 1,0,0 - for zero-degree rotations */
	if( EXPP_FloatsAreEqual(axis[0], 0.0f, 10) &&
		EXPP_FloatsAreEqual(axis[1], 0.0f, 10) &&
		EXPP_FloatsAreEqual(axis[2], 0.0f, 10)
	) {
		axis[0] = 1.0f;
	}

	return (PyObject *) newVectorObject(axis, 3, Py_NEW, NULL);
}

static int Quaternion_setAxisVec(QuaternionObject *self, PyObject *value, void *UNUSED(closure))
{
	float tquat[4];
	float len;

	float axis[3];
	float angle;

	if(!BaseMath_ReadCallback(self))
		return -1;

	len= normalize_qt_qt(tquat, self->quat);
	quat_to_axis_angle(axis, &angle, tquat); /* axis value is unused */

	if (mathutils_array_parse(axis, 3, 3, value, "quat.axis = other") == -1)
		return -1;

	axis_angle_to_quat(self->quat, axis, angle);
	mul_qt_fl(self->quat, len);

	if(!BaseMath_WriteCallback(self))
		return -1;

	return 0;
}

//----------------------------------mathutils.Quaternion() --------------
static PyObject *Quaternion_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	PyObject *seq= NULL;
	double angle = 0.0f;
	float quat[QUAT_SIZE]= {0.0f, 0.0f, 0.0f, 0.0f};

	if(kwds && PyDict_Size(kwds)) {
		PyErr_SetString(PyExc_TypeError, "mathutils.Quaternion(): takes no keyword args");
		return NULL;
	}

	if(!PyArg_ParseTuple(args, "|Od:mathutils.Quaternion", &seq, &angle))
		return NULL;

	switch(PyTuple_GET_SIZE(args)) {
	case 0:
		break;
	case 1:
		if (mathutils_array_parse(quat, QUAT_SIZE, QUAT_SIZE, seq, "mathutils.Quaternion()") == -1)
			return NULL;
		break;
	case 2:
		if (mathutils_array_parse(quat, 3, 3, seq, "mathutils.Quaternion()") == -1)
			return NULL;
		angle= fmod(angle + M_PI*2, M_PI*4) - M_PI*2; /* clamp because of precision issues */
		axis_angle_to_quat(quat, quat, angle);
		break;
	/* PyArg_ParseTuple assures no more then 2 */
	}
	return newQuaternionObject(quat, Py_NEW, type);
}

static PyObject *quat__apply_to_copy(PyNoArgsFunction quat_func, QuaternionObject *self)
{
	PyObject *ret= Quaternion_copy(self);
	PyObject *ret_dummy= quat_func(ret);
	if(ret_dummy) {
		Py_DECREF(ret_dummy);
		return (PyObject *)ret;
	}
	else { /* error */
		Py_DECREF(ret);
		return NULL;
	}
}

//-----------------------METHOD DEFINITIONS ----------------------
static struct PyMethodDef Quaternion_methods[] = {
	/* in place only */
	{"identity", (PyCFunction) Quaternion_identity, METH_NOARGS, Quaternion_identity_doc},
	{"negate", (PyCFunction) Quaternion_negate, METH_NOARGS, Quaternion_negate_doc},

	/* operate on original or copy */
	{"conjugate", (PyCFunction) Quaternion_conjugate, METH_NOARGS, Quaternion_conjugate_doc},
	{"conjugated", (PyCFunction) Quaternion_conjugated, METH_NOARGS, Quaternion_conjugated_doc},

	{"invert", (PyCFunction) Quaternion_invert, METH_NOARGS, Quaternion_invert_doc},
	{"inverted", (PyCFunction) Quaternion_inverted, METH_NOARGS, Quaternion_inverted_doc},

	{"normalize", (PyCFunction) Quaternion_normalize, METH_NOARGS, Quaternion_normalize_doc},
	{"normalized", (PyCFunction) Quaternion_normalized, METH_NOARGS, Quaternion_normalized_doc},

	/* return converted representation */
	{"to_euler", (PyCFunction) Quaternion_to_euler, METH_VARARGS, Quaternion_to_euler_doc},
	{"to_matrix", (PyCFunction) Quaternion_to_matrix, METH_NOARGS, Quaternion_to_matrix_doc},

	/* operation between 2 or more types  */
	{"cross", (PyCFunction) Quaternion_cross, METH_O, Quaternion_cross_doc},
	{"dot", (PyCFunction) Quaternion_dot, METH_O, Quaternion_dot_doc},
	{"difference", (PyCFunction) Quaternion_difference, METH_O, Quaternion_difference_doc},
	{"slerp", (PyCFunction) Quaternion_slerp, METH_VARARGS, Quaternion_slerp_doc},
	{"rotate", (PyCFunction) Quaternion_rotate, METH_O, Quaternion_rotate_doc},

	{"__copy__", (PyCFunction) Quaternion_copy, METH_NOARGS, Quaternion_copy_doc},
	{"copy", (PyCFunction) Quaternion_copy, METH_NOARGS, Quaternion_copy_doc},
	{NULL, NULL, 0, NULL}
};

/*****************************************************************************/
/* Python attributes get/set structure:                                      */
/*****************************************************************************/
static PyGetSetDef Quaternion_getseters[] = {
	{(char *)"w", (getter)Quaternion_getAxis, (setter)Quaternion_setAxis, (char *)"Quaternion W value.\n\n:type: float", (void *)0},
	{(char *)"x", (getter)Quaternion_getAxis, (setter)Quaternion_setAxis, (char *)"Quaternion X axis.\n\n:type: float", (void *)1},
	{(char *)"y", (getter)Quaternion_getAxis, (setter)Quaternion_setAxis, (char *)"Quaternion Y axis.\n\n:type: float", (void *)2},
	{(char *)"z", (getter)Quaternion_getAxis, (setter)Quaternion_setAxis, (char *)"Quaternion Z axis.\n\n:type: float", (void *)3},
	{(char *)"magnitude", (getter)Quaternion_getMagnitude, (setter)NULL, (char *)"Size of the quaternion (readonly).\n\n:type: float", NULL},
	{(char *)"angle", (getter)Quaternion_getAngle, (setter)Quaternion_setAngle, (char *)"angle of the quaternion.\n\n:type: float", NULL},
	{(char *)"axis",(getter)Quaternion_getAxisVec, (setter)Quaternion_setAxisVec, (char *)"quaternion axis as a vector.\n\n:type: :class:`Vector`", NULL},
	{(char *)"is_wrapped", (getter)BaseMathObject_getWrapped, (setter)NULL, (char *)BaseMathObject_Wrapped_doc, NULL},
	{(char *)"owner", (getter)BaseMathObject_getOwner, (setter)NULL, (char *)BaseMathObject_Owner_doc, NULL},
	{NULL,NULL,NULL,NULL,NULL}  /* Sentinel */
};

//------------------PY_OBECT DEFINITION--------------------------
static char quaternion_doc[] =
"This object gives access to Quaternions in Blender."
;
PyTypeObject quaternion_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"mathutils.Quaternion",						//tp_name
	sizeof(QuaternionObject),			//tp_basicsize
	0,								//tp_itemsize
	(destructor)BaseMathObject_dealloc,		//tp_dealloc
	NULL,								//tp_print
	NULL,								//tp_getattr
	NULL,								//tp_setattr
	NULL,								//tp_compare
	(reprfunc) Quaternion_repr,		//tp_repr
	&Quaternion_NumMethods,			//tp_as_number
	&Quaternion_SeqMethods,			//tp_as_sequence
	&Quaternion_AsMapping,			//tp_as_mapping
	NULL,								//tp_hash
	NULL,								//tp_call
	NULL,								//tp_str
	NULL,								//tp_getattro
	NULL,								//tp_setattro
	NULL,								//tp_as_buffer
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC, //tp_flags
	quaternion_doc, //tp_doc
	(traverseproc)BaseMathObject_traverse,	//tp_traverse
	(inquiry)BaseMathObject_clear,	//tp_clear
	(richcmpfunc)Quaternion_richcmpr,	//tp_richcompare
	0,								//tp_weaklistoffset
	NULL,								//tp_iter
	NULL,								//tp_iternext
	Quaternion_methods,				//tp_methods
	NULL,								//tp_members
	Quaternion_getseters,			//tp_getset
	NULL,								//tp_base
	NULL,								//tp_dict
	NULL,								//tp_descr_get
	NULL,								//tp_descr_set
	0,								//tp_dictoffset
	NULL,								//tp_init
	NULL,								//tp_alloc
	Quaternion_new,					//tp_new
	NULL,								//tp_free
	NULL,								//tp_is_gc
	NULL,								//tp_bases
	NULL,								//tp_mro
	NULL,								//tp_cache
	NULL,								//tp_subclasses
	NULL,								//tp_weaklist
	NULL,								//tp_del
};
//------------------------newQuaternionObject (internal)-------------
//creates a new quaternion object
/*pass Py_WRAP - if vector is a WRAPPER for data allocated by BLENDER
 (i.e. it was allocated elsewhere by MEM_mallocN())
  pass Py_NEW - if vector is not a WRAPPER and managed by PYTHON
 (i.e. it must be created here with PyMEM_malloc())*/
PyObject *newQuaternionObject(float *quat, int type, PyTypeObject *base_type)
{
	QuaternionObject *self;

	self= base_type ?	(QuaternionObject *)base_type->tp_alloc(base_type, 0) :
						(QuaternionObject *)PyObject_GC_New(QuaternionObject, &quaternion_Type);

	if(self) {
		/* init callbacks as NULL */
		self->cb_user= NULL;
		self->cb_type= self->cb_subtype= 0;

		if(type == Py_WRAP){
			self->quat = quat;
			self->wrapped = Py_WRAP;
		}
		else if (type == Py_NEW){
			self->quat = PyMem_Malloc(QUAT_SIZE * sizeof(float));
			if(!quat) { //new empty
				unit_qt(self->quat);
			}else{
				QUATCOPY(self->quat, quat);
			}
			self->wrapped = Py_NEW;
		}
		else{
			PyErr_SetString(PyExc_RuntimeError, "Quaternion(): invalid type");
			return NULL;
		}
	}
	return (PyObject *) self;
}

PyObject *newQuaternionObject_cb(PyObject *cb_user, int cb_type, int cb_subtype)
{
	QuaternionObject *self= (QuaternionObject *)newQuaternionObject(NULL, Py_NEW, NULL);
	if(self) {
		Py_INCREF(cb_user);
		self->cb_user=			cb_user;
		self->cb_type=			(unsigned char)cb_type;
		self->cb_subtype=		(unsigned char)cb_subtype;
	}

	return (PyObject *)self;
}

