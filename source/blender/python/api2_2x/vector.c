/*
 * $Id$
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
 * 
 * Contributor(s): Willian P. Germano, Joseph Gilbert, Ken Hughes, Alex Fraser, Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "Mathutils.h"

#include "BLI_blenlib.h"
#include "BKE_utildefines.h"
#include "BLI_arithb.h"

#define MAX_DIMENSIONS 4
/* Swizzle axes get packed into a single value that is used as a closure. Each
   axis uses SWIZZLE_BITS_PER_AXIS bits. The first bit (SWIZZLE_VALID_AXIS) is
   used as a sentinel: if it is unset, the axis is not valid. */
#define SWIZZLE_BITS_PER_AXIS 3
#define SWIZZLE_VALID_AXIS 0x4
#define SWIZZLE_AXIS       0x3


/* An array of getseters, some of which have members on the stack and some on
   the heap.

   Vector_dyn_getseters: The getseter structures. Terminated with a NULL sentinel.
   Vector_dyn_names:     All the names of the getseters that were allocated on the heap.
              Each name is terminated with a null character, but there is
              currently no way to find the length of this array. */
PyGetSetDef*	Vector_dyn_getseters = NULL; 
char*			Vector_dyn_names = NULL;

/*-------------------------DOC STRINGS ---------------------------*/
char Vector_Zero_doc[] = "() - set all values in the vector to 0";
char Vector_Normalize_doc[] = "() - normalize the vector";
char Vector_Negate_doc[] = "() - changes vector to it's additive inverse";
char Vector_Resize2D_doc[] = "() - resize a vector to [x,y]";
char Vector_Resize3D_doc[] = "() - resize a vector to [x,y,z]";
char Vector_Resize4D_doc[] = "() - resize a vector to [x,y,z,w]";
char Vector_ToTrackQuat_doc[] = "(track, up) - extract a quaternion from the vector and the track and up axis";
char Vector_reflect_doc[] = "(mirror) - return a vector reflected on the mirror normal";
char Vector_copy_doc[] = "() - return a copy of the vector";
char Vector_swizzle_doc[] = "Swizzle: Get or set axes in specified order";
/*-----------------------METHOD DEFINITIONS ----------------------*/
struct PyMethodDef Vector_methods[] = {
	{"zero", (PyCFunction) Vector_Zero, METH_NOARGS, Vector_Zero_doc},
	{"normalize", (PyCFunction) Vector_Normalize, METH_NOARGS, Vector_Normalize_doc},
	{"negate", (PyCFunction) Vector_Negate, METH_NOARGS, Vector_Negate_doc},
	{"resize2D", (PyCFunction) Vector_Resize2D, METH_NOARGS, Vector_Resize2D_doc},
	{"resize3D", (PyCFunction) Vector_Resize3D, METH_NOARGS, Vector_Resize2D_doc},
	{"resize4D", (PyCFunction) Vector_Resize4D, METH_NOARGS, Vector_Resize2D_doc},
	{"toTrackQuat", ( PyCFunction ) Vector_ToTrackQuat, METH_VARARGS, Vector_ToTrackQuat_doc},
	{"reflect", ( PyCFunction ) Vector_reflect, METH_O, Vector_reflect_doc},
	{"copy", (PyCFunction) Vector_copy, METH_NOARGS, Vector_copy_doc},
	{"__copy__", (PyCFunction) Vector_copy, METH_NOARGS, Vector_copy_doc},
	{NULL, NULL, 0, NULL}
};

/*-----------------------------METHODS---------------------------- */
/*----------------------------Vector.zero() ----------------------
  set the vector data to 0,0,0 */
PyObject *Vector_Zero(VectorObject * self)
{
	int i;
	for(i = 0; i < self->size; i++) {
		self->vec[i] = 0.0f;
	}
	Py_INCREF(self);
	return (PyObject*)self;
}
/*----------------------------Vector.normalize() -----------------
  normalize the vector data to a unit vector */
PyObject *Vector_Normalize(VectorObject * self)
{
	int i;
	float norm = 0.0f;

	for(i = 0; i < self->size; i++) {
		norm += self->vec[i] * self->vec[i];
	}
	norm = (float) sqrt(norm);
	for(i = 0; i < self->size; i++) {
		self->vec[i] /= norm;
	}
	Py_INCREF(self);
	return (PyObject*)self;
}


/*----------------------------Vector.resize2D() ------------------
  resize the vector to x,y */
PyObject *Vector_Resize2D(VectorObject * self)
{
	if(self->wrapped==Py_WRAP) {
		PyErr_SetString(PyExc_TypeError, "vector.resize2d(): cannot resize wrapped data - only python vectors\n");
		return NULL;
	}
	self->vec = PyMem_Realloc(self->vec, (sizeof(float) * 2));
	if(self->vec == NULL) {
		PyErr_SetString(PyExc_MemoryError, "vector.resize2d(): problem allocating pointer space\n\n");
		return NULL;
	}
	
	self->size = 2;
	Py_INCREF(self);
	return (PyObject*)self;
}
/*----------------------------Vector.resize3D() ------------------
  resize the vector to x,y,z */
PyObject *Vector_Resize3D(VectorObject * self)
{
	if (self->wrapped==Py_WRAP) {
		PyErr_SetString(PyExc_TypeError, "vector.resize3d(): cannot resize wrapped data - only python vectors\n");
		return NULL;
	}
	self->vec = PyMem_Realloc(self->vec, (sizeof(float) * 3));
	if(self->vec == NULL) {
		PyErr_SetString(PyExc_MemoryError, "vector.resize3d(): problem allocating pointer space\n\n");
		return NULL;
	}
	
	if(self->size == 2)
		self->vec[2] = 0.0f;
	
	self->size = 3;
	Py_INCREF(self);
	return (PyObject*)self;
}
/*----------------------------Vector.resize4D() ------------------
  resize the vector to x,y,z,w */
PyObject *Vector_Resize4D(VectorObject * self)
{
	if(self->wrapped==Py_WRAP) {
		PyErr_SetString(PyExc_TypeError, "vector.resize4d(): cannot resize wrapped data - only python vectors");
		return NULL;
	}
	self->vec = PyMem_Realloc(self->vec, (sizeof(float) * 4));
	if(self->vec == NULL) {
		PyErr_SetString(PyExc_MemoryError, "vector.resize4d(): problem allocating pointer space\n\n");
		return NULL;
	}
	if(self->size == 2){
		self->vec[2] = 0.0f;
		self->vec[3] = 1.0f;
	}else if(self->size == 3){
		self->vec[3] = 1.0f;
	}
	self->size = 4;
	Py_INCREF(self);
	return (PyObject*)self;
}
/*----------------------------Vector.toTrackQuat(track, up) ----------------------
  extract a quaternion from the vector and the track and up axis */
PyObject *Vector_ToTrackQuat( VectorObject * self, PyObject * args )
{
	float vec[3], quat[4];
	char *strack, *sup;
	short track = 2, up = 1;

	if( !PyArg_ParseTuple ( args, "|ss", &strack, &sup ) ) {
		PyErr_SetString( PyExc_TypeError, "expected optional two strings\n" );
		return NULL;
	}
	if (self->size != 3) {
		PyErr_SetString( PyExc_TypeError, "only for 3D vectors\n" );
		return NULL;
	}

	if (strack) {
		if (strlen(strack) == 2) {
			if (strack[0] == '-') {
				switch(strack[1]) {
					case 'X':
					case 'x':
						track = 3;
						break;
					case 'Y':
					case 'y':
						track = 4;
						break;
					case 'z':
					case 'Z':
						track = 5;
						break;
					default:
						PyErr_SetString( PyExc_ValueError, "only X, -X, Y, -Y, Z or -Z for track axis\n" );
						return NULL;
				}
			}
			else {
				PyErr_SetString( PyExc_ValueError, "only X, -X, Y, -Y, Z or -Z for track axis\n" );
				return NULL;
			}
		}
		else if (strlen(strack) == 1) {
			switch(strack[0]) {
			case '-':
			case 'X':
			case 'x':
				track = 0;
				break;
			case 'Y':
			case 'y':
				track = 1;
				break;
			case 'z':
			case 'Z':
				track = 2;
				break;
			default:
				PyErr_SetString( PyExc_ValueError, "only X, -X, Y, -Y, Z or -Z for track axis\n" );
				return NULL;
			}
		}
		else {
			PyErr_SetString( PyExc_ValueError, "only X, -X, Y, -Y, Z or -Z for track axis\n" );
			return NULL;
		}
	}

	if (sup) {
		if (strlen(sup) == 1) {
			switch(*sup) {
			case 'X':
			case 'x':
				up = 0;
				break;
			case 'Y':
			case 'y':
				up = 1;
				break;
			case 'z':
			case 'Z':
				up = 2;
				break;
			default:
				PyErr_SetString( PyExc_ValueError, "only X, Y or Z for up axis\n" );
				return NULL;
			}
		}
		else {
			PyErr_SetString( PyExc_ValueError, "only X, Y or Z for up axis\n" );
			return NULL;
		}
	}

	if (track == up) {
		PyErr_SetString( PyExc_ValueError, "Can't have the same axis for track and up\n" );
		return NULL;
	}

	/*
		flip vector around, since vectoquat expect a vector from target to tracking object 
		and the python function expects the inverse (a vector to the target).
	*/
	vec[0] = -self->vec[0];
	vec[1] = -self->vec[1];
	vec[2] = -self->vec[2];

	vectoquat(vec, track, up, quat);

	return newQuaternionObject(quat, Py_NEW);
}

/*----------------------------Vector.reflect(mirror) ----------------------
  return a reflected vector on the mirror normal
  ((2 * DotVecs(vec, mirror)) * mirror) - vec
  using arithb.c would be nice here */
PyObject *Vector_reflect( VectorObject * self, PyObject * value )
{
	VectorObject *mirrvec;
	float mirror[3];
	float vec[3];
	float reflect[4] = {0.0f, 0.0f, 0.0f, 0.0f};
	float dot2;
	
	/* for normalizing */
	int i;
	float norm = 0.0f;
	
	if (!VectorObject_Check(value)) {
		PyErr_SetString( PyExc_TypeError, "expected a vector argument" );
		return NULL;
	}
	mirrvec = (VectorObject *)value;
	
	mirror[0] = mirrvec->vec[0];
	mirror[1] = mirrvec->vec[1];
	if (mirrvec->size > 2)	mirror[2] = mirrvec->vec[2];
	else					mirror[2] = 0.0;
	
	/* normalize, whos idea was it not to use arithb.c? :-/ */
	for(i = 0; i < 3; i++) {
		norm += mirror[i] * mirror[i];
	}
	norm = (float) sqrt(norm);
	for(i = 0; i < 3; i++) {
		mirror[i] /= norm;
	}
	/* done */
	
	vec[0] = self->vec[0];
	vec[1] = self->vec[1];
	if (self->size > 2)		vec[2] = self->vec[2];
	else					vec[2] = 0.0;
	
	dot2 = 2 * vec[0]*mirror[0]+vec[1]*mirror[1]+vec[2]*mirror[2];
	
	reflect[0] = (dot2 * mirror[0]) - vec[0];
	reflect[1] = (dot2 * mirror[1]) - vec[1];
	reflect[2] = (dot2 * mirror[2]) - vec[2];
	
	return newVectorObject(reflect, self->size, Py_NEW);
}

/*----------------------------Vector.copy() --------------------------------------
  return a copy of the vector */
PyObject *Vector_copy(VectorObject * self)
{
	return newVectorObject(self->vec, self->size, Py_NEW);
}

/*----------------------------dealloc()(internal) ----------------
  free the py_object */
static void Vector_dealloc(VectorObject * self)
{
	/* only free non wrapped */
	if(self->wrapped != Py_WRAP){
		PyMem_Free(self->vec);
	}
	PyObject_DEL(self);
}

/*----------------------------print object (internal)-------------
  print the object to screen */
static PyObject *Vector_repr(VectorObject * self)
{
	int i;
	char buffer[48], str[1024];

	BLI_strncpy(str,"[",1024);
	for(i = 0; i < self->size; i++){
		if(i < (self->size - 1)){
			sprintf(buffer, "%.6f, ", self->vec[i]);
			strcat(str,buffer);
		}else{
			sprintf(buffer, "%.6f", self->vec[i]);
			strcat(str,buffer);
		}
	}
	strcat(str, "](vector)");

	return PyString_FromString(str);
}
/*---------------------SEQUENCE PROTOCOLS------------------------
  ----------------------------len(object)------------------------
  sequence length*/
static int Vector_len(VectorObject * self)
{
	return self->size;
}
/*----------------------------object[]---------------------------
  sequence accessor (get)*/
static PyObject *Vector_item(VectorObject * self, int i)
{
	if(i < 0 || i >= self->size) {
		PyErr_SetString(PyExc_IndexError,"vector[index]: out of range\n");
		return NULL;
	}

	return PyFloat_FromDouble(self->vec[i]);

}
/*----------------------------object[]-------------------------
  sequence accessor (set)*/
static int Vector_ass_item(VectorObject * self, int i, PyObject * ob)
{
	
	if(!(PyNumber_Check(ob))) { /* parsed item not a number */
		PyErr_SetString(PyExc_TypeError, "vector[index] = x: index argument not a number\n");
		return -1;
	}

	if(i < 0 || i >= self->size){
		PyErr_SetString(PyExc_IndexError, "vector[index] = x: assignment index out of range\n");
		return -1;
	}
	self->vec[i] = (float)PyFloat_AsDouble(ob);
	return 0;
}

/*----------------------------object[z:y]------------------------
  sequence slice (get) */
static PyObject *Vector_slice(VectorObject * self, int begin, int end)
{
	PyObject *list = NULL;
	int count;

	CLAMP(begin, 0, self->size);
	if (end<0) end= self->size+end+1;
	CLAMP(end, 0, self->size);
	begin = MIN2(begin,end);

	list = PyList_New(end - begin);
	for(count = begin; count < end; count++) {
		PyList_SetItem(list, count - begin,
				PyFloat_FromDouble(self->vec[count]));
	}

	return list;
}
/*----------------------------object[z:y]------------------------
  sequence slice (set) */
static int Vector_ass_slice(VectorObject * self, int begin, int end,
			     PyObject * seq)
{
	int i, y, size = 0;
	float vec[4];
	PyObject *v;

	CLAMP(begin, 0, self->size);
	if (end<0) end= self->size+end+1;
	CLAMP(end, 0, self->size);
	begin = MIN2(begin,end);

	size = PySequence_Length(seq);
	if(size != (end - begin)){
		PyErr_SetString(PyExc_TypeError, "vector[begin:end] = []: size mismatch in slice assignment\n");
		return -1;
	}

	for (i = 0; i < size; i++) {
		v = PySequence_GetItem(seq, i);
		if (v == NULL) { /* Failed to read sequence */
			PyErr_SetString(PyExc_RuntimeError, "vector[begin:end] = []: unable to read sequence\n");
			return -1;
		}
		
		if(!PyNumber_Check(v)) { /* parsed item not a number */
			Py_DECREF(v);
			PyErr_SetString(PyExc_TypeError, "vector[begin:end] = []: sequence argument not a number\n");
			return -1;
		}

		vec[i] = (float)PyFloat_AsDouble(v);
		Py_DECREF(v);
	}
	/*parsed well - now set in vector*/
	for(y = 0; y < size; y++){
		self->vec[begin + y] = vec[y];
	}
	return 0;
}
/*------------------------NUMERIC PROTOCOLS----------------------
  ------------------------obj + obj------------------------------
  addition*/
static PyObject *Vector_add(PyObject * v1, PyObject * v2)
{
	int i;
	float vec[4];

	VectorObject *vec1 = NULL, *vec2 = NULL;
	
	if VectorObject_Check(v1)
		vec1= (VectorObject *)v1;
	
	if VectorObject_Check(v2)
		vec2= (VectorObject *)v2;
	
	/* make sure v1 is always the vector */
	if (vec1 && vec2 ) {
		/*VECTOR + VECTOR*/
		if(vec1->size != vec2->size) {
			PyErr_SetString(PyExc_AttributeError, "Vector addition: vectors must have the same dimensions for this operation\n");
			return NULL;
		}
		for(i = 0; i < vec1->size; i++) {
			vec[i] = vec1->vec[i] +	vec2->vec[i];
		}
		return newVectorObject(vec, vec1->size, Py_NEW);
	}
	
	PyErr_SetString(PyExc_AttributeError, "Vector addition: arguments not valid for this operation....\n");
	return NULL;
}

/*  ------------------------obj += obj------------------------------
  addition in place */
static PyObject *Vector_iadd(PyObject * v1, PyObject * v2)
{
	int i;

	VectorObject *vec1 = NULL, *vec2 = NULL;
	
	if VectorObject_Check(v1)
		vec1= (VectorObject *)v1;
	
	if VectorObject_Check(v2)
		vec2= (VectorObject *)v2;
	
	/* make sure v1 is always the vector */
	if (vec1 && vec2 ) {
		/*VECTOR + VECTOR*/
		if(vec1->size != vec2->size) {
			PyErr_SetString(PyExc_AttributeError, "Vector addition: vectors must have the same dimensions for this operation\n");
			return NULL;
		}
		for(i = 0; i < vec1->size; i++) {
			vec1->vec[i] +=	vec2->vec[i];
		}
		Py_INCREF( v1 );
		return v1;
	}
	
	PyErr_SetString(PyExc_AttributeError, "Vector addition: arguments not valid for this operation....\n");
	return NULL;
}

/*------------------------obj - obj------------------------------
  subtraction*/
static PyObject *Vector_sub(PyObject * v1, PyObject * v2)
{
	int i;
	float vec[4];
	VectorObject *vec1 = NULL, *vec2 = NULL;

	if (!VectorObject_Check(v1) || !VectorObject_Check(v2)) {
		PyErr_SetString(PyExc_AttributeError, "Vector subtraction: arguments not valid for this operation....\n");
		return NULL;
	}
	vec1 = (VectorObject*)v1;
	vec2 = (VectorObject*)v2;
	
	if(vec1->size != vec2->size) {
		PyErr_SetString(PyExc_AttributeError, "Vector subtraction: vectors must have the same dimensions for this operation\n");
		return NULL;
	}
	for(i = 0; i < vec1->size; i++) {
		vec[i] = vec1->vec[i] -	vec2->vec[i];
	}

	return newVectorObject(vec, vec1->size, Py_NEW);
}

/*------------------------obj -= obj------------------------------
  subtraction*/
static PyObject *Vector_isub(PyObject * v1, PyObject * v2)
{
	int i, size;
	VectorObject *vec1 = NULL, *vec2 = NULL;

	if (!VectorObject_Check(v1) || !VectorObject_Check(v2)) {
		PyErr_SetString(PyExc_AttributeError, "Vector subtraction: arguments not valid for this operation....\n");
		return NULL;
	}
	vec1 = (VectorObject*)v1;
	vec2 = (VectorObject*)v2;
	
	if(vec1->size != vec2->size) {
		PyErr_SetString(PyExc_AttributeError, "Vector subtraction: vectors must have the same dimensions for this operation\n");
		return NULL;
	}

	size = vec1->size;
	for(i = 0; i < vec1->size; i++) {
		vec1->vec[i] = vec1->vec[i] -	vec2->vec[i];
	}

	Py_INCREF( v1 );
	return v1;
}

/*------------------------obj * obj------------------------------
  mulplication*/
static PyObject *Vector_mul(PyObject * v1, PyObject * v2)
{
	VectorObject *vec1 = NULL, *vec2 = NULL;
	
	if VectorObject_Check(v1)
		vec1= (VectorObject *)v1;
	
	if VectorObject_Check(v2)
		vec2= (VectorObject *)v2;
	
	/* make sure v1 is always the vector */
	if (vec1 && vec2 ) {
		int i;
		double dot = 0.0f;
		
		if(vec1->size != vec2->size) {
			PyErr_SetString(PyExc_AttributeError, "Vector multiplication: vectors must have the same dimensions for this operation\n");
			return NULL;
		}
		
		/*dot product*/
		for(i = 0; i < vec1->size; i++) {
			dot += vec1->vec[i] * vec2->vec[i];
		}
		return PyFloat_FromDouble(dot);
	}
	
	/*swap so vec1 is always the vector */
	if (vec2) {
		vec1= vec2;
		v2= v1;
	}
	
	if (PyNumber_Check(v2)) {
		/* VEC * NUM */
		int i;
		float vec[4];
		float scalar = (float)PyFloat_AsDouble( v2 );
		
		for(i = 0; i < vec1->size; i++) {
			vec[i] = vec1->vec[i] *	scalar;
		}
		return newVectorObject(vec, vec1->size, Py_NEW);
		
	} else if (MatrixObject_Check(v2)) {
		/* VEC * MATRIX */
		if (v1==v2) /* mat*vec, we have swapped the order */
			return column_vector_multiplication((MatrixObject*)v2, vec1);
		else /* vec*mat */
			return row_vector_multiplication(vec1, (MatrixObject*)v2);
	} else if (QuaternionObject_Check(v2)) {
		QuaternionObject *quat = (QuaternionObject*)v2;
		if(vec1->size != 3) {
			PyErr_SetString(PyExc_TypeError, "Vector multiplication: only 3D vector rotations (with quats) currently supported\n");
			return NULL;
		}
		return quat_rotation((PyObject*)vec1, (PyObject*)quat);
	}
	
	PyErr_SetString(PyExc_TypeError, "Vector multiplication: arguments not acceptable for this operation\n");
	return NULL;
}

/*------------------------obj *= obj------------------------------
  in place mulplication */
static PyObject *Vector_imul(PyObject * v1, PyObject * v2)
{
	VectorObject *vec = (VectorObject *)v1;
	int i;
	
	/* only support vec*=float and vec*=mat
	   vec*=vec result is a float so that wont work */
	if (PyNumber_Check(v2)) {
		/* VEC * NUM */
		float scalar = (float)PyFloat_AsDouble( v2 );
		
		for(i = 0; i < vec->size; i++) {
			vec->vec[i] *=	scalar;
		}
		
		Py_INCREF( v1 );
		return v1;
		
	} else if (MatrixObject_Check(v2)) {
		float vecCopy[4];
		int x,y, size = vec->size;
		MatrixObject *mat= (MatrixObject*)v2;
		
		if(mat->colSize != size){
			if(mat->rowSize == 4 && vec->size != 3){
				PyErr_SetString(PyExc_AttributeError, "vector * matrix: matrix column size and the vector size must be the same");
				return NULL;
			} else {
				vecCopy[3] = 1.0f;
			}
		}
		
		for(i = 0; i < size; i++){
			vecCopy[i] = vec->vec[i];
		}
		
		size = MIN2(size, mat->colSize);
		
		/*muliplication*/
		for(x = 0, i = 0; x < size; x++, i++) {
			double dot = 0.0f;
			for(y = 0; y < mat->rowSize; y++) {
				dot += mat->matrix[y][x] * vecCopy[y];
			}
			vec->vec[i] = (float)dot;
		}
		Py_INCREF( v1 );
		return v1;
	}
	PyErr_SetString(PyExc_TypeError, "Vector multiplication: arguments not acceptable for this operation\n");
	return NULL;
}

/*------------------------obj / obj------------------------------
  divide*/
static PyObject *Vector_div(PyObject * v1, PyObject * v2)
{
	int i, size;
	float vec[4], scalar;
	VectorObject *vec1 = NULL;
	
	if(!VectorObject_Check(v1)) { /* not a vector */
		PyErr_SetString(PyExc_TypeError, "Vector division: Vector must be divided by a float\n");
		return NULL;
	}
	vec1 = (VectorObject*)v1; /* vector */
	
	if(!PyNumber_Check(v2)) { /* parsed item not a number */
		PyErr_SetString(PyExc_TypeError, "Vector division: Vector must be divided by a float\n");
		return NULL;
	}
	scalar = (float)PyFloat_AsDouble(v2);
	
	if(scalar==0.0) { /* not a vector */
		PyErr_SetString(PyExc_ZeroDivisionError, "Vector division: divide by zero error.\n");
		return NULL;
	}
	size = vec1->size;
	for(i = 0; i < size; i++) {
		vec[i] = vec1->vec[i] /	scalar;
	}
	return newVectorObject(vec, size, Py_NEW);
}

/*------------------------obj / obj------------------------------
  divide*/
static PyObject *Vector_idiv(PyObject * v1, PyObject * v2)
{
	int i, size;
	float scalar;
	VectorObject *vec1 = NULL;
	
	/*if(!VectorObject_Check(v1)) {
		PyErr_SetString(PyExc_TypeError, "Vector division: Vector must be divided by a float\n");
		return -1;
	}*/
	
	vec1 = (VectorObject*)v1; /* vector */
	
	if(!PyNumber_Check(v2)) { /* parsed item not a number */
		PyErr_SetString(PyExc_TypeError, "Vector division: Vector must be divided by a float\n");
		return NULL;
	}

	scalar = (float)PyFloat_AsDouble(v2);
	
	if(scalar==0.0) { /* not a vector */
		PyErr_SetString(PyExc_ZeroDivisionError, "Vector division: divide by zero error.\n");
		return NULL;
	}
	size = vec1->size;
	for(i = 0; i < size; i++) {
		vec1->vec[i] /=	scalar;
	}
	Py_INCREF( v1 );
	return v1;
}

/*-------------------------- -obj -------------------------------
  returns the negative of this object*/
static PyObject *Vector_neg(VectorObject *self)
{
	int i;
	float vec[4];
	for(i = 0; i < self->size; i++){
		vec[i] = -self->vec[i];
	}

	return newVectorObject(vec, self->size, Py_NEW);
}
/*------------------------coerce(obj, obj)-----------------------
  coercion of unknown types to type VectorObject for numeric protocols
  Coercion() is called whenever a math operation has 2 operands that
 it doesn't understand how to evaluate. 2+Matrix for example. We want to 
 evaluate some of these operations like: (vector * 2), however, for math
 to proceed, the unknown operand must be cast to a type that python math will
 understand. (e.g. in the case above case, 2 must be cast to a vector and 
 then call vector.multiply(vector, scalar_cast_as_vector)*/


static int Vector_coerce(PyObject ** v1, PyObject ** v2)
{
	/* Just incref, each functon must raise errors for bad types */
	Py_INCREF (*v1);
	Py_INCREF (*v2);
	return 0;
}


/*------------------------tp_doc*/
static char VectorObject_doc[] = "This is a wrapper for vector objects.";
/*------------------------vec_magnitude_nosqrt (internal) - for comparing only */
static double vec_magnitude_nosqrt(float *data, int size)
{
	double dot = 0.0f;
	int i;

	for(i=0; i<size; i++){
		dot += data[i];
	}
	/*return (double)sqrt(dot);*/
	/* warning, line above removed because we are not using the length,
	   rather the comparing the sizes and for this we do not need the sqrt
	   for the actual length, the dot must be sqrt'd */
	return (double)dot;
}


/*------------------------tp_richcmpr
  returns -1 execption, 0 false, 1 true */
PyObject* Vector_richcmpr(PyObject *objectA, PyObject *objectB, int comparison_type)
{
	VectorObject *vecA = NULL, *vecB = NULL;
	int result = 0;
	float epsilon = .000001f;
	double lenA,lenB;

	if (!VectorObject_Check(objectA) || !VectorObject_Check(objectB)){
		if (comparison_type == Py_NE){
			Py_RETURN_TRUE;
		}else{
			Py_RETURN_FALSE;
		}
	}
	vecA = (VectorObject*)objectA;
	vecB = (VectorObject*)objectB;

	if (vecA->size != vecB->size){
		if (comparison_type == Py_NE){
			Py_RETURN_TRUE;
		}else{
			Py_RETURN_FALSE;
		}
	}

	switch (comparison_type){
		case Py_LT:
			lenA = vec_magnitude_nosqrt(vecA->vec, vecA->size);
			lenB = vec_magnitude_nosqrt(vecB->vec, vecB->size);
			if( lenA < lenB ){
				result = 1;
			}
			break;
		case Py_LE:
			lenA = vec_magnitude_nosqrt(vecA->vec, vecA->size);
			lenB = vec_magnitude_nosqrt(vecB->vec, vecB->size);
			if( lenA < lenB ){
				result = 1;
			}else{
				result = (((lenA + epsilon) > lenB) && ((lenA - epsilon) < lenB));
			}
			break;
		case Py_EQ:
			result = EXPP_VectorsAreEqual(vecA->vec, vecB->vec, vecA->size, 1);
			break;
		case Py_NE:
			result = EXPP_VectorsAreEqual(vecA->vec, vecB->vec, vecA->size, 1);
			if (result == 0){
				result = 1;
			}else{
				result = 0;
			}
			break;
		case Py_GT:
			lenA = vec_magnitude_nosqrt(vecA->vec, vecA->size);
			lenB = vec_magnitude_nosqrt(vecB->vec, vecB->size);
			if( lenA > lenB ){
				result = 1;
			}
			break;
		case Py_GE:
			lenA = vec_magnitude_nosqrt(vecA->vec, vecA->size);
			lenB = vec_magnitude_nosqrt(vecB->vec, vecB->size);
			if( lenA > lenB ){
				result = 1;
			}else{
				result = (((lenA + epsilon) > lenB) && ((lenA - epsilon) < lenB));
			}
			break;
		default:
			printf("The result of the comparison could not be evaluated");
			break;
	}
	if (result == 1){
		Py_RETURN_TRUE;
	}else{
		Py_RETURN_FALSE;
	}
}
/*-----------------PROTCOL DECLARATIONS--------------------------*/
static PySequenceMethods Vector_SeqMethods = {
	(inquiry) Vector_len,						/* sq_length */
	(binaryfunc) 0,								/* sq_concat */
	(intargfunc) 0,								/* sq_repeat */
	(intargfunc) Vector_item,					/* sq_item */
	(intintargfunc) Vector_slice,				/* sq_slice */
	(intobjargproc) Vector_ass_item,			/* sq_ass_item */
	(intintobjargproc) Vector_ass_slice,		/* sq_ass_slice */
};


/* For numbers without flag bit Py_TPFLAGS_CHECKTYPES set, all
   arguments are guaranteed to be of the object's type (modulo
   coercion hacks -- i.e. if the type's coercion function
   returns other types, then these are allowed as well).  Numbers that
   have the Py_TPFLAGS_CHECKTYPES flag bit set should check *both*
   arguments for proper type and implement the necessary conversions
   in the slot functions themselves. */
 
static PyNumberMethods Vector_NumMethods = {
	(binaryfunc) Vector_add,					/* __add__ */
	(binaryfunc) Vector_sub,					/* __sub__ */
	(binaryfunc) Vector_mul,					/* __mul__ */
	(binaryfunc) Vector_div,					/* __div__ */
	(binaryfunc) NULL,							/* __mod__ */
	(binaryfunc) NULL,							/* __divmod__ */
	(ternaryfunc) NULL,							/* __pow__ */
	(unaryfunc) Vector_neg,						/* __neg__ */
	(unaryfunc) NULL,							/* __pos__ */
	(unaryfunc) NULL,							/* __abs__ */
	(inquiry) NULL,								/* __nonzero__ */
	(unaryfunc) NULL,							/* __invert__ */
	(binaryfunc) NULL,							/* __lshift__ */
	(binaryfunc) NULL,							/* __rshift__ */
	(binaryfunc) NULL,							/* __and__ */
	(binaryfunc) NULL,							/* __xor__ */
	(binaryfunc) NULL,							/* __or__ */
	(coercion)  Vector_coerce,					/* __coerce__ */
	(unaryfunc) NULL,							/* __int__ */
	(unaryfunc) NULL,							/* __long__ */
	(unaryfunc) NULL,							/* __float__ */
	(unaryfunc) NULL,							/* __oct__ */
	(unaryfunc) NULL,							/* __hex__ */
	
	/* Added in release 2.0 */
	(binaryfunc) Vector_iadd,					/*__iadd__*/
	(binaryfunc) Vector_isub,					/*__isub__*/
	(binaryfunc) Vector_imul,					/*__imul__*/
	(binaryfunc) Vector_idiv,					/*__idiv__*/
	(binaryfunc) NULL,							/*__imod__*/
	(ternaryfunc) NULL,							/*__ipow__*/
	(binaryfunc) NULL,							/*__ilshift__*/
	(binaryfunc) NULL,							/*__irshift__*/
	(binaryfunc) NULL,							/*__iand__*/
	(binaryfunc) NULL,							/*__ixor__*/
	(binaryfunc) NULL,							/*__ior__*/
 
	/* Added in release 2.2 */
	/* The following require the Py_TPFLAGS_HAVE_CLASS flag */
	(binaryfunc) NULL,							/*__floordiv__  __rfloordiv__*/
	(binaryfunc) NULL,							/*__truediv__ __rfloordiv__*/
	(binaryfunc) NULL,							/*__ifloordiv__*/
	(binaryfunc) NULL,							/*__itruediv__*/
};
/*------------------PY_OBECT DEFINITION--------------------------*/

/*
 * vector axis, vector.x/y/z/w
 */
	
static PyObject *Vector_getAxis( VectorObject * self, void *type )
{
	switch( (long)type ) {
    case 'X':	/* these are backwards, but that how it works */
		return PyFloat_FromDouble(self->vec[0]);
    case 'Y':
		return PyFloat_FromDouble(self->vec[1]);
    case 'Z':	/* these are backwards, but that how it works */
		if(self->size < 3) {
			PyErr_SetString(PyExc_AttributeError, "vector.z: error, cannot get this axis for a 2D vector\n");
			return NULL;
		}
		else {
			return PyFloat_FromDouble(self->vec[2]);
		}
    case 'W':
		if(self->size < 4) {
			PyErr_SetString(PyExc_AttributeError, "vector.w: error, cannot get this axis for a 3D vector\n");
			return NULL;
		}
	
		return PyFloat_FromDouble(self->vec[3]);
	default:
		{
			PyErr_SetString( PyExc_RuntimeError, "undefined type in Vector_getAxis" );
			return NULL;
		}
	}
}

static int Vector_setAxis( VectorObject * self, PyObject * value, void * type )
{
	float param= (float)PyFloat_AsDouble( value );
	
	if (param==-1 && PyErr_Occurred()) {
		PyErr_SetString( PyExc_TypeError, "expected a number for the vector axis" );
		return -1;
	}
	switch( (long)type ) {
    case 'X':	/* these are backwards, but that how it works */
		self->vec[0]= param;
		break;
    case 'Y':
		self->vec[1]= param;
		break;
    case 'Z':	/* these are backwards, but that how it works */
		if(self->size < 3) {
			PyErr_SetString(PyExc_AttributeError, "vector.z: error, cannot get this axis for a 2D vector\n");
			return -1;
		}
		self->vec[2]= param;
		break;
    case 'W':
		if(self->size < 4) {
			PyErr_SetString(PyExc_AttributeError, "vector.w: error, cannot get this axis for a 3D vector\n");
			return -1;
		}
		self->vec[3]= param;
		break;
	}

	return 0;
}

/* vector.length */
static PyObject *Vector_getLength( VectorObject * self, void *type )
{
	double dot = 0.0f;
	int i;
	
	for(i = 0; i < self->size; i++){
		dot += (self->vec[i] * self->vec[i]);
	}
	return PyFloat_FromDouble(sqrt(dot));
}

static int Vector_setLength( VectorObject * self, PyObject * value )
{
	double dot = 0.0f, param;
	int i;
	
	if (!PyNumber_Check(value)) {
		PyErr_SetString( PyExc_TypeError, "expected a number for the vector axis" );
		return -1;
	}
	param= PyFloat_AsDouble( value );
	
	if (param < 0) {
		PyErr_SetString( PyExc_TypeError, "cannot set a vectors length to a negative value" );
		return -1;
	}
	if (param==0) {
		for(i = 0; i < self->size; i++){
			self->vec[i]= 0;
		}
		return 0;
	}
	
	for(i = 0; i < self->size; i++){
		dot += (self->vec[i] * self->vec[i]);
	}

	if (!dot) /* cant sqrt zero */
		return 0;
	
	dot = sqrt(dot);
	
	if (dot==param)
		return 0;
	
	dot= dot/param;
	
	for(i = 0; i < self->size; i++){
		self->vec[i]= self->vec[i] / (float)dot;
	}
	
	return 0;
}

static PyObject *Vector_getWrapped( VectorObject * self, void *type )
{
	if (self->wrapped == Py_WRAP)
		Py_RETURN_TRUE;
	else
		Py_RETURN_FALSE;
}


/*****************************************************************************/
/* Python attributes get/set structure:                                      */
/*****************************************************************************/
static PyGetSetDef Vector_getseters[] = {
	{"x",
	 (getter)Vector_getAxis, (setter)Vector_setAxis,
	 "Vector X axis",
	 (void *)'X'},
	{"y",
	 (getter)Vector_getAxis, (setter)Vector_setAxis,
	 "Vector Y axis",
	 (void *)'Y'},
	{"z",
	 (getter)Vector_getAxis, (setter)Vector_setAxis,
	 "Vector Z axis",
	 (void *)'Z'},
	{"w",
	 (getter)Vector_getAxis, (setter)Vector_setAxis,
	 "Vector Z axis",
	 (void *)'W'},
	{"length",
	 (getter)Vector_getLength, (setter)Vector_setLength,
	 "Vector Length",
	 NULL},
	{"magnitude",
	 (getter)Vector_getLength, (setter)Vector_setLength,
	 "Vector Length",
	 NULL},
	{"wrapped",
	 (getter)Vector_getWrapped, (setter)NULL,
	 "True when this wraps blenders internal data",
	 NULL},
	{NULL,NULL,NULL,NULL,NULL}  /* Sentinel */
};

/* Get a new Vector according to the provided swizzle. This function has little
   error checking, as we are in control of the inputs: the closure is set by us
   in Vector_createSwizzleGetSeter. */
static PyObject *Vector_getSwizzle(VectorObject * self, void *closure)
{
	size_t axisA;
	size_t axisB;
	float vec[MAX_DIMENSIONS];
	unsigned int swizzleClosure;
	
	/* Unpack the axes from the closure into an array. */
	axisA = 0;
	swizzleClosure = (unsigned int) closure;
	while (swizzleClosure & SWIZZLE_VALID_AXIS)
	{
		axisB = swizzleClosure & SWIZZLE_AXIS;
		vec[axisA] = self->vec[axisB];
		swizzleClosure = swizzleClosure >> SWIZZLE_BITS_PER_AXIS;
		axisA++;
	}
	
	return newVectorObject(vec, axisA, Py_NEW);
}

/* Set the items of this vector using a swizzle.
   - If value is a vector or list this operates like an array copy, except that
     the destination is effectively re-ordered as defined by the swizzle. At
     most min(len(source), len(dest)) values will be copied.
   - If the value is scalar, it is copied to all axes listed in the swizzle.
   - If an axis appears more than once in the swizzle, the final occurrance is
     the one that determines its value.

   Returns 0 on success and -1 on failure. On failure, the vector will be
   unchanged. */
static int Vector_setSwizzle(VectorObject * self, PyObject * value, void *closure)
{
	VectorObject *vecVal;
	PyObject *item;
	size_t listLen;
	float scalarVal;

	size_t axisB;
	size_t axisA;
	unsigned int swizzleClosure;
	
	float vecTemp[MAX_DIMENSIONS];
	
	/* Check that the closure can be used with this vector: even 2D vectors have
	   swizzles defined for axes z and w, but they would be invalid. */
	swizzleClosure = (unsigned int) closure;
	while (swizzleClosure & SWIZZLE_VALID_AXIS)
	{
		axisA = swizzleClosure & SWIZZLE_AXIS;
		if (axisA >= self->size)
		{
			PyErr_SetString(PyExc_AttributeError, "Error: vector does not have specified axis.\n");
			return -1;
		}
		swizzleClosure = swizzleClosure >> SWIZZLE_BITS_PER_AXIS;
	}
	
	if (VectorObject_Check(value))
	{
		/* Copy vector contents onto swizzled axes. */
		vecVal = (VectorObject*) value;
		axisB = 0;
		swizzleClosure = (unsigned int) closure;
		while (swizzleClosure & SWIZZLE_VALID_AXIS && axisB < vecVal->size)
		{
			axisA = swizzleClosure & SWIZZLE_AXIS;
			vecTemp[axisA] = vecVal->vec[axisB];
			
			swizzleClosure = swizzleClosure >> SWIZZLE_BITS_PER_AXIS;
			axisB++;
		}
		memcpy(self->vec, vecTemp, axisB * sizeof(float));
		return 0;
	}
	else if (PyList_Check(value))
	{
		/* Copy list contents onto swizzled axes. */
		listLen = PyList_Size(value);
		swizzleClosure = (unsigned int) closure;
		axisB = 0;
		while (swizzleClosure & SWIZZLE_VALID_AXIS && axisB < listLen)
		{
			item = PyList_GetItem(value, axisB);
			if (!PyNumber_Check(item))
			{
				PyErr_SetString(PyExc_AttributeError, "Error: vector does not have specified axis.\n");
				return -1;
			}
			scalarVal = (float)PyFloat_AsDouble(item);
			
			axisA = swizzleClosure & SWIZZLE_AXIS;
			vecTemp[axisA] = scalarVal;
			
			swizzleClosure = swizzleClosure >> SWIZZLE_BITS_PER_AXIS;
			axisB++;
		}
		memcpy(self->vec, vecTemp, axisB * sizeof(float));
		return 0;
	}
	else if (PyNumber_Check(value))
	{
		/* Assign the same value to each axis. */
		scalarVal = (float)PyFloat_AsDouble(value);
		swizzleClosure = (unsigned int) closure;
		while (swizzleClosure & SWIZZLE_VALID_AXIS)
		{
			axisA = swizzleClosure & SWIZZLE_AXIS;
			self->vec[axisA] = scalarVal;
			
			swizzleClosure = swizzleClosure >> SWIZZLE_BITS_PER_AXIS;
		}
		return 0;
	}
	else
	{
		PyErr_SetString( PyExc_TypeError, "Expected a Vector, list or scalar value." );
		return -1;
	}
}

/* Create a getseter that operates on the axes defined in swizzle.
   Parameters:
   gsd:        An empty PyGetSetDef object. This will be modified.
   swizzle:    An array of axis indices.
   dimensions: The number of axes to swizzle. Must be >= 2 and <=
               MAX_DIMENSIONS.
   name:       A pointer to string that the name will be stored in. This is
               purely to reduce the number of allocations. Before this function
               returns, name will be advanced to the point immediately after
               the name of the new getseter. Therefore, do not attempt to read
               its contents. */
static void Vector_createSwizzleGetSeter
(
	PyGetSetDef *gsd,
	unsigned short *swizzle,
	size_t dimensions,
	char **name
)
{
	const char axes[] = {'x', 'y', 'z', 'w'};
	unsigned int closure;
	int i;
	
	/* Convert the index array into named axes. Store the name in the string
	   that was passed in, and make the getseter structure point to the same
	   address. */
	gsd->name = *name;
	for (i = 0; i < dimensions; i++)
		gsd->name[i] = axes[swizzle[i]];
	gsd->name[i] = '\0';
	/* Advance the name pointer to the next available address. */
	(*name) = (*name) + dimensions + 1;
	
	gsd->get = (getter)Vector_getSwizzle;
	gsd->set = (setter)Vector_setSwizzle;
	
	gsd->doc = Vector_swizzle_doc;
	
	/* Pack the axes into a single value to use as the closure. Pack these in
	   in reverse so they come out in the right order when unpacked. */
	closure = 0;
	for (i = MAX_DIMENSIONS - 1; i >= 0; i--)
	{
		closure = closure << SWIZZLE_BITS_PER_AXIS;
		if (i < dimensions)
			closure = closure | swizzle[i] | SWIZZLE_VALID_AXIS;
	}
	gsd->closure = (void*) closure;
}

/* Create and append all implicit swizzle getseters to an existing array of
   getseters.
   Parameters:
   Vector_getseters:
				 A null-terminated array of getseters that have been manually
                 defined.
   resGds:       The resultant array of getseters. This will be a combination of
                 static and manually-defined getseters. Use Vector_DelGetseters
                 to free this array.

   Returns: 0 on success, -1 on failure. On failure, resGsd will be left
   untouched. */
static int Vector_AppendSwizzleGetseters(void)
{
	int len;
	int len_orig;
	int len_names;
	unsigned int i;
	unsigned short swizzle[MAX_DIMENSIONS];
	char *name;
	
	/* Count the explicit getseters. */
	for (len_orig = 0; Vector_getseters[len_orig].name != NULL; len_orig++);
	
	/* Then there are 4^4 + 4^3 + 4^2 = 336 swizzles. */
	len = len_orig + 336 + 1; /* Plus one sentinel. */
	
	/* That means 4^4 names of length 4 + 1, 4^3 names of length 3 + 1, and 4^2
	   names of length 2 + 1 (including a null character at the end of each)
	   = (4^4) * 5 + (4^3) * 4 + (4^2) * 3
	   = 1584 */
	len_names = 1584;
	
	if(Vector_dyn_getseters) { /* Should never happen */
		PyMem_Del(Vector_dyn_getseters);
		Vector_dyn_getseters= NULL;
	}
	Vector_dyn_getseters = PyMem_New(PyGetSetDef, len * sizeof(PyGetSetDef));
	if (Vector_dyn_getseters == NULL) {
		PyErr_SetString(PyExc_MemoryError, "Could not allocate memory for swizzle getseters.");
		return -1;
	}
	memset(Vector_dyn_getseters, 0, len * sizeof(PyGetSetDef));

	if(Vector_dyn_names) { /* Should never happen */
		PyMem_Del(Vector_dyn_names);
		Vector_dyn_getseters= NULL;
	}
	Vector_dyn_names = PyMem_New(char, len_names * sizeof(char));
	if (Vector_dyn_names == NULL) {
		PyErr_SetString(PyExc_MemoryError, "Could not allocate memory for swizzle getseter names.");
		PyMem_Del(Vector_dyn_getseters);
		return -1;
	}
	memset(Vector_dyn_names, 0, len_names * sizeof(char));
	
	/* Do a shallow copy of the getseters. A deep clone can't be done because
	   we don't know how much memory each closure needs. */
	memcpy(Vector_dyn_getseters, Vector_getseters, len_orig * sizeof(PyGetSetDef));
	
	/* Create the swizzle functions. The pointer for name will be advanced by
	   Vector_createSwizzleGetSeter. */
	name = Vector_dyn_names;
	i = len_orig;
	for (swizzle[0] = 0; swizzle[0] < MAX_DIMENSIONS; swizzle[0]++)
	{
		for (swizzle[1] = 0; swizzle[1] < MAX_DIMENSIONS; swizzle[1]++)
		{
			Vector_createSwizzleGetSeter(&Vector_dyn_getseters[i++], swizzle, 2, &name);
			for (swizzle[2] = 0; swizzle[2] < MAX_DIMENSIONS; swizzle[2]++)
			{
				Vector_createSwizzleGetSeter(&Vector_dyn_getseters[i++], swizzle, 3, &name);
				for (swizzle[3] = 0; swizzle[3] < MAX_DIMENSIONS; swizzle[3]++)
				{
					Vector_createSwizzleGetSeter(&Vector_dyn_getseters[i++], swizzle, 4, &name);
				}
			}
		}
	}
	
	/* No need to add a sentinel - memory was initialised to zero above. */
	vector_Type.tp_getset = Vector_dyn_getseters;
	
	return 0;
}

/* Delete an array of getseters that was created by
   Vector_AppendSwizzleGetseters. It is safe to call this even if the structure
   members are NULL. */
static void Vector_DelGetseters(void)
{	
	/* Free strings that were allocated on the heap. */
	if (Vector_dyn_names != NULL) {
		PyMem_Del(Vector_dyn_names);
		Vector_dyn_names = NULL;
	}
	
	/* Free the structure arrays themselves. */
	if (Vector_dyn_getseters != NULL) {
		PyMem_Del(Vector_dyn_getseters);
		Vector_dyn_getseters = NULL;
	}
	
	/* for the blenderplayer that will initialize multiple times :| */
	vector_Type.tp_getset = Vector_getseters;
	vector_Type.tp_flags = 0; /* maybe python does this when finalizing? - wont hurt anyway */
}

/* Note
 Py_TPFLAGS_CHECKTYPES allows us to avoid casting all types to Vector when coercing
 but this means for eg that 
 vec*mat and mat*vec both get sent to Vector_mul and it neesd to sort out the order
*/

PyTypeObject vector_Type = {
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
	/*  For printing, in format "<module>.<name>" */
	"Blender Vector",             /* char *tp_name; */
	sizeof( VectorObject ),         /* int tp_basicsize; */
	0,                          /* tp_itemsize;  For allocation */

	/* Methods to implement standard operations */

	( destructor ) Vector_dealloc,/* destructor tp_dealloc; */
	NULL,                       /* printfunc tp_print; */
	NULL,                       /* getattrfunc tp_getattr; */
	NULL,                       /* setattrfunc tp_setattr; */
	NULL,   /* cmpfunc tp_compare; */
	( reprfunc ) Vector_repr,     /* reprfunc tp_repr; */

	/* Method suites for standard classes */

	&Vector_NumMethods,                       /* PyNumberMethods *tp_as_number; */
	&Vector_SeqMethods,                       /* PySequenceMethods *tp_as_sequence; */
	NULL,                       /* PyMappingMethods *tp_as_mapping; */

	/* More standard operations (here for binary compatibility) */

	NULL,                       /* hashfunc tp_hash; */
	NULL,                       /* ternaryfunc tp_call; */
	NULL,                       /* reprfunc tp_str; */
	NULL,                       /* getattrofunc tp_getattro; */
	NULL,                       /* setattrofunc tp_setattro; */

	/* Functions to access object as input/output buffer */
	NULL,                       /* PyBufferProcs *tp_as_buffer; */

  /*** Flags to define presence of optional/expanded features ***/
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_CHECKTYPES,         /* long tp_flags; */

	VectorObject_doc,                       /*  char *tp_doc;  Documentation string */
  /*** Assigned meaning in release 2.0 ***/
	/* call function for all accessible objects */
	NULL,                       /* traverseproc tp_traverse; */

	/* delete references to contained objects */
	NULL,                       /* inquiry tp_clear; */

  /***  Assigned meaning in release 2.1 ***/
  /*** rich comparisons ***/
	(richcmpfunc)Vector_richcmpr,                       /* richcmpfunc tp_richcompare; */

  /***  weak reference enabler ***/
	0,                          /* long tp_weaklistoffset; */

  /*** Added in release 2.2 ***/
	/*   Iterators */
	NULL,                       /* getiterfunc tp_iter; */
	NULL,                       /* iternextfunc tp_iternext; */

  /*** Attribute descriptor and subclassing stuff ***/
	Vector_methods,           /* struct PyMethodDef *tp_methods; */
	NULL,                       /* struct PyMemberDef *tp_members; */
	Vector_getseters,           /* struct PyGetSetDef *tp_getset; */
	NULL,                       /* struct _typeobject *tp_base; */
	NULL,                       /* PyObject *tp_dict; */
	NULL,                       /* descrgetfunc tp_descr_get; */
	NULL,                       /* descrsetfunc tp_descr_set; */
	0,                          /* long tp_dictoffset; */
	NULL,                       /* initproc tp_init; */
	NULL,                       /* allocfunc tp_alloc; */
	NULL,                       /* newfunc tp_new; */
	/*  Low-level free-memory routine */
	NULL,                       /* freefunc tp_free;  */
	/* For PyObject_IS_GC */
	NULL,                       /* inquiry tp_is_gc;  */
	NULL,                       /* PyObject *tp_bases; */
	/* method resolution order */
	NULL,                       /* PyObject *tp_mro;  */
	NULL,                       /* PyObject *tp_cache; */
	NULL,                       /* PyObject *tp_subclasses; */
	NULL,                       /* PyObject *tp_weaklist; */
	NULL
};


/*------------------------newVectorObject (internal)-------------
  creates a new vector object
  pass Py_WRAP - if vector is a WRAPPER for data allocated by BLENDER
 (i.e. it was allocated elsewhere by MEM_mallocN())
  pass Py_NEW - if vector is not a WRAPPER and managed by PYTHON
 (i.e. it must be created here with PyMEM_malloc())*/
PyObject *newVectorObject(float *vec, int size, int type)
{
	int i;
	VectorObject *self = PyObject_NEW(VectorObject, &vector_Type);
	
	if(size > 4 || size < 2)
		return NULL;
	self->size = size;

	if(type == Py_WRAP) {
		self->vec = vec;
		self->wrapped = Py_WRAP;
	} else if (type == Py_NEW) {
		self->vec = PyMem_Malloc(size * sizeof(float));
		if(!vec) { /*new empty*/
			for(i = 0; i < size; i++){
				self->vec[i] = 0.0f;
			}
			if(size == 4)  /* do the homogenous thing */
				self->vec[3] = 1.0f;
		}else{
			for(i = 0; i < size; i++){
				self->vec[i] = vec[i];
			}
		}
		self->wrapped = Py_NEW;
	}else{ /*bad type*/
		return NULL;
	}
	return (PyObject *) self;
}

/*
  #############################DEPRECATED################################
  #######################################################################
  ----------------------------Vector.negate() --------------------
  set the vector to it's negative -x, -y, -z */
PyObject *Vector_Negate(VectorObject * self)
{
	int i;
	for(i = 0; i < self->size; i++) {
		self->vec[i] = -(self->vec[i]);
	}
	/*printf("Vector.negate(): Deprecated: use -vector instead\n");*/
	Py_INCREF(self);
	return (PyObject*)self;
}
/*###################################################################
  ###########################DEPRECATED##############################*/

int Vector_Init(void)
{
	return Vector_AppendSwizzleGetseters();
}

void Vector_Free() {
	Vector_DelGetseters();
}
