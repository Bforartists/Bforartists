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
 * 
 * Contributor(s): Joseph Gilbert
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "Mathutils.h"

#include "BLI_arithb.h"
#include "BKE_utildefines.h"
#include "BLI_blenlib.h"


//-------------------------DOC STRINGS ---------------------------
char Euler_Zero_doc[] = "() - set all values in the euler to 0";
char Euler_Unique_doc[] ="() - sets the euler rotation a unique shortest arc rotation - tests for gimbal lock";
char Euler_ToMatrix_doc[] =	"() - returns a rotation matrix representing the euler rotation";
char Euler_ToQuat_doc[] = "() - returns a quaternion representing the euler rotation";
char Euler_Rotate_doc[] = "() - rotate a euler by certain amount around an axis of rotation";
char Euler_copy_doc[] = "() - returns a copy of the euler.";
char Euler_MakeCompatible_doc[] = "(euler) - Make this user compatible with another (no axis flipping).";
//-----------------------METHOD DEFINITIONS ----------------------
struct PyMethodDef Euler_methods[] = {
	{"zero", (PyCFunction) Euler_Zero, METH_NOARGS, Euler_Zero_doc},
	{"unique", (PyCFunction) Euler_Unique, METH_NOARGS, Euler_Unique_doc},
	{"toMatrix", (PyCFunction) Euler_ToMatrix, METH_NOARGS, Euler_ToMatrix_doc},
	{"toQuat", (PyCFunction) Euler_ToQuat, METH_NOARGS, Euler_ToQuat_doc},
	{"rotate", (PyCFunction) Euler_Rotate, METH_VARARGS, Euler_Rotate_doc},
	{"makeCompatible", (PyCFunction) Euler_MakeCompatible, METH_O, Euler_MakeCompatible_doc},
	{"__copy__", (PyCFunction) Euler_copy, METH_VARARGS, Euler_copy_doc},
	{"copy", (PyCFunction) Euler_copy, METH_VARARGS, Euler_copy_doc},
	{NULL, NULL, 0, NULL}
};
//-----------------------------METHODS----------------------------
//----------------------------Euler.toQuat()----------------------
//return a quaternion representation of the euler
PyObject *Euler_ToQuat(EulerObject * self)
{
	float eul[3], quat[4];
	int x;

	for(x = 0; x < 3; x++) {
		eul[x] = self->eul[x] * ((float)Py_PI / 180);
	}
	EulToQuat(eul, quat);
	return newQuaternionObject(quat, Py_NEW);
}
//----------------------------Euler.toMatrix()---------------------
//return a matrix representation of the euler
PyObject *Euler_ToMatrix(EulerObject * self)
{
	float eul[3];
	float mat[9] = {0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
	int x;

	for(x = 0; x < 3; x++) {
		eul[x] = self->eul[x] * ((float)Py_PI / 180);
	}
	EulToMat3(eul, (float (*)[3]) mat);
	return newMatrixObject(mat, 3, 3 , Py_NEW);
}
//----------------------------Euler.unique()-----------------------
//sets the x,y,z values to a unique euler rotation
PyObject *Euler_Unique(EulerObject * self)
{
	double heading, pitch, bank;
	double pi2 =  Py_PI * 2.0f;
	double piO2 = Py_PI / 2.0f;
	double Opi2 = 1.0f / pi2;

	//radians
	heading = self->eul[0] * (float)Py_PI / 180;
	pitch = self->eul[1] * (float)Py_PI / 180;
	bank = self->eul[2] * (float)Py_PI / 180;

	//wrap heading in +180 / -180
	pitch += Py_PI;
	pitch -= floor(pitch * Opi2) * pi2;
	pitch -= Py_PI;


	if(pitch < -piO2) {
		pitch = -Py_PI - pitch;
		heading += Py_PI;
		bank += Py_PI;
	} else if(pitch > piO2) {
		pitch = Py_PI - pitch;
		heading += Py_PI;
		bank += Py_PI;
	}
	//gimbal lock test
	if(fabs(pitch) > piO2 - 1e-4) {
		heading += bank;
		bank = 0.0f;
	} else {
		bank += Py_PI;
		bank -= (floor(bank * Opi2)) * pi2;
		bank -= Py_PI;
	}

	heading += Py_PI;
	heading -= (floor(heading * Opi2)) * pi2;
	heading -= Py_PI;

	//back to degrees
	self->eul[0] = (float)(heading * 180 / (float)Py_PI);
	self->eul[1] = (float)(pitch * 180 / (float)Py_PI);
	self->eul[2] = (float)(bank * 180 / (float)Py_PI);

	Py_INCREF(self);
	return (PyObject *)self;
}
//----------------------------Euler.zero()-------------------------
//sets the euler to 0,0,0
PyObject *Euler_Zero(EulerObject * self)
{
	self->eul[0] = 0.0;
	self->eul[1] = 0.0;
	self->eul[2] = 0.0;

	Py_INCREF(self);
	return (PyObject *)self;
}
//----------------------------Euler.rotate()-----------------------
//rotates a euler a certain amount and returns the result
//should return a unique euler rotation (i.e. no 720 degree pitches :)
PyObject *Euler_Rotate(EulerObject * self, PyObject *args)
{
	float angle = 0.0f;
	char *axis;
	int x;

	if(!PyArg_ParseTuple(args, "fs", &angle, &axis)){
		PyErr_SetString(PyExc_TypeError, "euler.rotate():expected angle (float) and axis (x,y,z)");
		return NULL;
	}
	if(!STREQ3(axis,"x","y","z")){
		PyErr_SetString(PyExc_TypeError, "euler.rotate(): expected axis to be 'x', 'y' or 'z'");
		return NULL;
	}

	//covert to radians
	angle *= ((float)Py_PI / 180);
	for(x = 0; x < 3; x++) {
		self->eul[x] *= ((float)Py_PI / 180);
	}
	euler_rot(self->eul, angle, *axis);
	//convert back from radians
	for(x = 0; x < 3; x++) {
		self->eul[x] *= (180 / (float)Py_PI);
	}

	Py_INCREF(self);
	return (PyObject *)self;
}

PyObject *Euler_MakeCompatible(EulerObject * self, EulerObject *value)
{
	float eul_from_rad[3];
	int x;
	
	if(!EulerObject_Check(value)) {
		PyErr_SetString(PyExc_TypeError, "euler.makeCompatible(euler):expected a single euler argument.");
		return NULL;
	}
	
	//covert to radians
	for(x = 0; x < 3; x++) {
		self->eul[x] = self->eul[x] * ((float)Py_PI / 180);
		eul_from_rad[x] = value->eul[x] * ((float)Py_PI / 180);
	}
	compatible_eul(self->eul, eul_from_rad);
	//convert back from radians
	for(x = 0; x < 3; x++) {
		self->eul[x] *= (180 / (float)Py_PI);
	}
	
	Py_INCREF(self);
	return (PyObject *)self;
}

//----------------------------Euler.rotate()-----------------------
// return a copy of the euler
PyObject *Euler_copy(EulerObject * self, PyObject *args)
{
	return newEulerObject(self->eul, Py_NEW);
}


//----------------------------dealloc()(internal) ------------------
//free the py_object
static void Euler_dealloc(EulerObject * self)
{
	//only free py_data
	if(self->data.py_data){
		PyMem_Free(self->data.py_data);
	}
	PyObject_DEL(self);
}

//----------------------------print object (internal)--------------
//print the object to screen
static PyObject *Euler_repr(EulerObject * self)
{
	char str[64];
	sprintf(str, "[%.6f, %.6f, %.6f](euler)", self->eul[0], self->eul[1], self->eul[2]);
	return PyString_FromString(str);
}
//------------------------tp_richcmpr
//returns -1 execption, 0 false, 1 true
static PyObject* Euler_richcmpr(PyObject *objectA, PyObject *objectB, int comparison_type)
{
	EulerObject *eulA = NULL, *eulB = NULL;
	int result = 0;

	if (!EulerObject_Check(objectA) || !EulerObject_Check(objectB)){
		if (comparison_type == Py_NE){
			Py_RETURN_TRUE;
		}else{
			Py_RETURN_FALSE;
		}
	}
	eulA = (EulerObject*)objectA;
	eulB = (EulerObject*)objectB;

	switch (comparison_type){
		case Py_EQ:
			result = EXPP_VectorsAreEqual(eulA->eul, eulB->eul, 3, 1);
			break;
		case Py_NE:
			result = EXPP_VectorsAreEqual(eulA->eul, eulB->eul, 3, 1);
			if (result == 0){
				result = 1;
			}else{
				result = 0;
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
//------------------------tp_doc
static char EulerObject_doc[] = "This is a wrapper for euler objects.";
//---------------------SEQUENCE PROTOCOLS------------------------
//----------------------------len(object)------------------------
//sequence length
static int Euler_len(EulerObject * self)
{
	return 3;
}
//----------------------------object[]---------------------------
//sequence accessor (get)
static PyObject *Euler_item(EulerObject * self, int i)
{
	if(i<0)
		i= 3-i;
	
	if(i < 0 || i >= 3) {
		PyErr_SetString(PyExc_IndexError, "euler[attribute]: array index out of range");
		return NULL;
	}
	return PyFloat_FromDouble(self->eul[i]);

}
//----------------------------object[]-------------------------
//sequence accessor (set)
static int Euler_ass_item(EulerObject * self, int i, PyObject * value)
{
	float f = PyFloat_AsDouble(value);

	if(f == -1 && PyErr_Occurred()) { // parsed item not a number
		PyErr_SetString(PyExc_TypeError, "euler[attribute] = x: argument not a number");
		return -1;
	}

	if(i<0)
		i= 3-i;
	
	if(i < 0 || i >= 3){
		PyErr_SetString(PyExc_IndexError, "euler[attribute] = x: array assignment index out of range\n");
		return -1;
	}
	
	self->eul[i] = f;
	return 0;
}
//----------------------------object[z:y]------------------------
//sequence slice (get)
static PyObject *Euler_slice(EulerObject * self, int begin, int end)
{
	PyObject *list = NULL;
	int count;

	CLAMP(begin, 0, 3);
	if (end<0) end= 4+end;
	CLAMP(end, 0, 3);
	begin = MIN2(begin,end);

	list = PyList_New(end - begin);
	for(count = begin; count < end; count++) {
		PyList_SetItem(list, count - begin,
				PyFloat_FromDouble(self->eul[count]));
	}

	return list;
}
//----------------------------object[z:y]------------------------
//sequence slice (set)
static int Euler_ass_slice(EulerObject * self, int begin, int end,
			     PyObject * seq)
{
	int i, y, size = 0;
	float eul[3];
	PyObject *e, *f;

	CLAMP(begin, 0, 3);
	if (end<0) end= 4+end;
	CLAMP(end, 0, 3);
	begin = MIN2(begin,end);

	size = PySequence_Length(seq);
	if(size != (end - begin)){
		PyErr_SetString(PyExc_TypeError, "euler[begin:end] = []: size mismatch in slice assignment");
		return -1;
	}

	for (i = 0; i < size; i++) {
		e = PySequence_GetItem(seq, i);
		if (e == NULL) { // Failed to read sequence
			PyErr_SetString(PyExc_RuntimeError, "euler[begin:end] = []: unable to read sequence");
			return -1;
		}

		f = PyNumber_Float(e);
		if(f == NULL) { // parsed item not a number
			Py_DECREF(e);
			PyErr_SetString(PyExc_TypeError, "euler[begin:end] = []: sequence argument not a number");
			return -1;
		}

		eul[i] = (float)PyFloat_AS_DOUBLE(f);
		Py_DECREF(f);
		Py_DECREF(e);
	}
	//parsed well - now set in vector
	for(y = 0; y < 3; y++){
		self->eul[begin + y] = eul[y];
	}
	return 0;
}
//-----------------PROTCOL DECLARATIONS--------------------------
static PySequenceMethods Euler_SeqMethods = {
	(inquiry) Euler_len,						/* sq_length */
	(binaryfunc) 0,								/* sq_concat */
	(intargfunc) 0,								/* sq_repeat */
	(intargfunc) Euler_item,					/* sq_item */
	(intintargfunc) Euler_slice,				/* sq_slice */
	(intobjargproc) Euler_ass_item,				/* sq_ass_item */
	(intintobjargproc) Euler_ass_slice,			/* sq_ass_slice */
};



/*
 * vector axis, vector.x/y/z/w
 */
	
static PyObject *Euler_getAxis( EulerObject * self, void *type )
{
	switch( (long)type ) {
    case 'X':	/* these are backwards, but that how it works */
		return PyFloat_FromDouble(self->eul[0]);
    case 'Y':
		return PyFloat_FromDouble(self->eul[1]);
    case 'Z':
		return PyFloat_FromDouble(self->eul[2]);
	}
	
	PyErr_SetString(PyExc_SystemError, "corrupt euler, cannot get axis");
	return NULL;
}

static int Euler_setAxis( EulerObject * self, PyObject * value, void * type )
{
	float param= (float)PyFloat_AsDouble( value );
	
	if (param==-1 && PyErr_Occurred()) {
		PyErr_SetString(PyExc_TypeError, "expected a number for the vector axis");
		return -1;
	}
	
	switch( (long)type ) {
    case 'X':	/* these are backwards, but that how it works */
		self->eul[0]= param;
		break;
    case 'Y':
		self->eul[1]= param;
		break;
    case 'Z':
		self->eul[2]= param;
		break;
	}

	return 0;
}

static PyObject *Euler_getWrapped( VectorObject * self, void *type )
{
	if (self->wrapped == Py_WRAP)
		Py_RETURN_TRUE;
	else
		Py_RETURN_FALSE;
}


/*****************************************************************************/
/* Python attributes get/set structure:                                      */
/*****************************************************************************/
static PyGetSetDef Euler_getseters[] = {
	{"x",
	 (getter)Euler_getAxis, (setter)Euler_setAxis,
	 "Euler X axis",
	 (void *)'X'},
	{"y",
	 (getter)Euler_getAxis, (setter)Euler_setAxis,
	 "Euler Y axis",
	 (void *)'Y'},
	{"z",
	 (getter)Euler_getAxis, (setter)Euler_setAxis,
	 "Euler Z axis",
	 (void *)'Z'},
	{"wrapped",
	 (getter)Euler_getWrapped, (setter)NULL,
	 "True when this wraps blenders internal data",
	 NULL},
	{NULL,NULL,NULL,NULL,NULL}  /* Sentinel */
};

//------------------PY_OBECT DEFINITION--------------------------
PyTypeObject euler_Type = {
#if (PY_VERSION_HEX >= 0x02060000)
	PyVarObject_HEAD_INIT(NULL, 0)
#else
	/* python 2.5 and below */
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
#endif
	"euler",						//tp_name
	sizeof(EulerObject),			//tp_basicsize
	0,								//tp_itemsize
	(destructor)Euler_dealloc,		//tp_dealloc
	0,								//tp_print
	0,								//tp_getattr
	0,								//tp_setattr
	0,								//tp_compare
	(reprfunc) Euler_repr,			//tp_repr
	0,				//tp_as_number
	&Euler_SeqMethods,				//tp_as_sequence
	0,								//tp_as_mapping
	0,								//tp_hash
	0,								//tp_call
	0,								//tp_str
	0,								//tp_getattro
	0,								//tp_setattro
	0,								//tp_as_buffer
	Py_TPFLAGS_DEFAULT,				//tp_flags
	EulerObject_doc,				//tp_doc
	0,								//tp_traverse
	0,								//tp_clear
	(richcmpfunc)Euler_richcmpr,	//tp_richcompare
	0,								//tp_weaklistoffset
	0,								//tp_iter
	0,								//tp_iternext
	Euler_methods,					//tp_methods
	0,								//tp_members
	Euler_getseters,				//tp_getset
	0,								//tp_base
	0,								//tp_dict
	0,								//tp_descr_get
	0,								//tp_descr_set
	0,								//tp_dictoffset
	0,								//tp_init
	0,								//tp_alloc
	0,								//tp_new
	0,								//tp_free
	0,								//tp_is_gc
	0,								//tp_bases
	0,								//tp_mro
	0,								//tp_cache
	0,								//tp_subclasses
	0,								//tp_weaklist
	0								//tp_del
};
//------------------------newEulerObject (internal)-------------
//creates a new euler object
/*pass Py_WRAP - if vector is a WRAPPER for data allocated by BLENDER
 (i.e. it was allocated elsewhere by MEM_mallocN())
  pass Py_NEW - if vector is not a WRAPPER and managed by PYTHON
 (i.e. it must be created here with PyMEM_malloc())*/
PyObject *newEulerObject(float *eul, int type)
{
	EulerObject *self;
	int x;

	self = PyObject_NEW(EulerObject, &euler_Type);
	self->data.blend_data = NULL;
	self->data.py_data = NULL;

	if(type == Py_WRAP){
		self->data.blend_data = eul;
		self->eul = self->data.blend_data;
		self->wrapped = Py_WRAP;
	}else if (type == Py_NEW){
		self->data.py_data = PyMem_Malloc(3 * sizeof(float));
		self->eul = self->data.py_data;
		if(!eul) { //new empty
			for(x = 0; x < 3; x++) {
				self->eul[x] = 0.0f;
			}
		}else{
			for(x = 0; x < 3; x++){
				self->eul[x] = eul[x];
			}
		}
		self->wrapped = Py_NEW;
	}else{ //bad type
		return NULL;
	}
	return (PyObject *)self;
}
