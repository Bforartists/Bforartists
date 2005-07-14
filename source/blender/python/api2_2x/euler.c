/*
 * $Id$
 *
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
 * 
 * Contributor(s): Joseph Gilbert
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#include "BLI_arithb.h"
#include "BKE_utildefines.h"
#include "Mathutils.h"
#include "gen_utils.h"
#include "BLI_blenlib.h"

//-------------------------DOC STRINGS ---------------------------
char Euler_Zero_doc[] = "() - set all values in the euler to 0";
char Euler_Unique_doc[] ="() - sets the euler rotation a unique shortest arc rotation - tests for gimbal lock";
char Euler_ToMatrix_doc[] =	"() - returns a rotation matrix representing the euler rotation";
char Euler_ToQuat_doc[] = "() - returns a quaternion representing the euler rotation";
char Euler_Rotate_doc[] = "() - rotate a euler by certain amount around an axis of rotation";
//-----------------------METHOD DEFINITIONS ----------------------
struct PyMethodDef Euler_methods[] = {
	{"zero", (PyCFunction) Euler_Zero, METH_NOARGS, Euler_Zero_doc},
	{"unique", (PyCFunction) Euler_Unique, METH_NOARGS, Euler_Unique_doc},
	{"toMatrix", (PyCFunction) Euler_ToMatrix, METH_NOARGS, Euler_ToMatrix_doc},
	{"toQuat", (PyCFunction) Euler_ToQuat, METH_NOARGS, Euler_ToQuat_doc},
	{"rotate", (PyCFunction) Euler_Rotate, METH_VARARGS, Euler_Rotate_doc},
	{NULL, NULL, 0, NULL}
};
//-----------------------------METHODS----------------------------
//----------------------------Euler.toQuat()----------------------
//return a quaternion representation of the euler
PyObject *Euler_ToQuat(EulerObject * self)
{
	float eul[3];
	float quat[4];
	int x;

	for(x = 0; x < 3; x++) {
		eul[x] = self->eul[x] * ((float)Py_PI / 180);
	}
	EulToQuat(eul, quat);
	if(self->data.blend_data)
		return (PyObject *) newQuaternionObject(quat, Py_WRAP);
	else
		return (PyObject *) newQuaternionObject(quat, Py_NEW);
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
	if(self->data.blend_data)
		return (PyObject *) newMatrixObject(mat, 3, 3 , Py_WRAP);
	else	
		return (PyObject *) newMatrixObject(mat, 3, 3 , Py_NEW);
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
	self->eul[0] = heading * 180 / (float)Py_PI;
	self->eul[1] = pitch * 180 / (float)Py_PI;
	self->eul[2] = bank * 180 / (float)Py_PI;

	return (PyObject*)self;
}
//----------------------------Euler.zero()-------------------------
//sets the euler to 0,0,0
PyObject *Euler_Zero(EulerObject * self)
{
	self->eul[0] = 0.0;
	self->eul[1] = 0.0;
	self->eul[2] = 0.0;

	return (PyObject*)self;
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
		return EXPP_ReturnPyObjError(PyExc_TypeError,
			"euler.rotate():expected angle (float) and axis (x,y,z)");
	}
	if(!STREQ3(axis,"x","y","z")){
		return EXPP_ReturnPyObjError(PyExc_TypeError,
			"euler.rotate(): expected axis to be 'x', 'y' or 'z'");
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

	return (PyObject*)self;
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
//----------------------------getattr()(internal) ------------------
//object.attribute access (get)
static PyObject *Euler_getattr(EulerObject * self, char *name)
{
	if(STREQ(name,"x")){
		return PyFloat_FromDouble(self->eul[0]);
	}else if(STREQ(name, "y")){
		return PyFloat_FromDouble(self->eul[1]);
	}else if(STREQ(name, "z")){
		return PyFloat_FromDouble(self->eul[2]);
	}

	return Py_FindMethod(Euler_methods, (PyObject *) self, name);
}
//----------------------------setattr()(internal) ------------------
//object.attribute access (set)
static int Euler_setattr(EulerObject * self, char *name, PyObject * e)
{
	PyObject *f = NULL;

	f = PyNumber_Float(e);
	if(f == NULL) { // parsed item not a number
		return EXPP_ReturnIntError(PyExc_TypeError, 
			"euler.attribute = x: argument not a number\n");
	}

	if(STREQ(name,"x")){
		self->eul[0] = PyFloat_AS_DOUBLE(f);
	}else if(STREQ(name, "y")){
		self->eul[1] = PyFloat_AS_DOUBLE(f);
	}else if(STREQ(name, "z")){
		self->eul[2] = PyFloat_AS_DOUBLE(f);
	}else{
		Py_DECREF(f);
		return EXPP_ReturnIntError(PyExc_AttributeError,
				"euler.attribute = x: unknown attribute\n");
	}

	Py_DECREF(f);
	return 0;
}
//----------------------------print object (internal)--------------
//print the object to screen
static PyObject *Euler_repr(EulerObject * self)
{
	int i;
	char buffer[48], str[1024];

	BLI_strncpy(str,"[",1024);
	for(i = 0; i < 3; i++){
		if(i < (2)){
			sprintf(buffer, "%.6f, ", self->eul[i]);
			strcat(str,buffer);
		}else{
			sprintf(buffer, "%.6f", self->eul[i]);
			strcat(str,buffer);
		}
	}
	strcat(str, "](euler)");

	return EXPP_incr_ret(PyString_FromString(str));
}
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
	if(i < 0 || i >= 3)
		return EXPP_ReturnPyObjError(PyExc_IndexError,
		"euler[attribute]: array index out of range\n");

	return Py_BuildValue("f", self->eul[i]);

}
//----------------------------object[]-------------------------
//sequence accessor (set)
static int Euler_ass_item(EulerObject * self, int i, PyObject * ob)
{
	PyObject *f = NULL;

	f = PyNumber_Float(ob);
	if(f == NULL) { // parsed item not a number
		return EXPP_ReturnIntError(PyExc_TypeError, 
			"euler[attribute] = x: argument not a number\n");
	}

	if(i < 0 || i >= 3){
		Py_DECREF(f);
		return EXPP_ReturnIntError(PyExc_IndexError,
			"euler[attribute] = x: array assignment index out of range\n");
	}
	self->eul[i] = PyFloat_AS_DOUBLE(f);
	Py_DECREF(f);
	return 0;
}
//----------------------------object[z:y]------------------------
//sequence slice (get)
static PyObject *Euler_slice(EulerObject * self, int begin, int end)
{
	PyObject *list = NULL;
	int count;

	CLAMP(begin, 0, 3);
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

	CLAMP(begin, 0, 3);
	CLAMP(end, 0, 3);
	begin = MIN2(begin,end);

	size = PySequence_Length(seq);
	if(size != (end - begin)){
		return EXPP_ReturnIntError(PyExc_TypeError,
			"euler[begin:end] = []: size mismatch in slice assignment\n");
	}

	for (i = 0; i < size; i++) {
		PyObject *e, *f;

		e = PySequence_GetItem(seq, i);
		if (e == NULL) { // Failed to read sequence
			return EXPP_ReturnIntError(PyExc_RuntimeError, 
				"euler[begin:end] = []: unable to read sequence\n");
		}
		f = PyNumber_Float(e);
		if(f == NULL) { // parsed item not a number
			Py_DECREF(e);
			return EXPP_ReturnIntError(PyExc_TypeError, 
				"euler[begin:end] = []: sequence argument not a number\n");
		}
		eul[i] = PyFloat_AS_DOUBLE(f);
		EXPP_decr2(f,e);
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
//------------------PY_OBECT DEFINITION--------------------------
PyTypeObject euler_Type = {
	PyObject_HEAD_INIT(NULL) 
	0,											/*ob_size */
	"euler",									/*tp_name */
	sizeof(EulerObject),						/*tp_basicsize */
	0,											/*tp_itemsize */
	(destructor) Euler_dealloc,					/*tp_dealloc */
	(printfunc) 0,								/*tp_print */
	(getattrfunc) Euler_getattr,				/*tp_getattr */
	(setattrfunc) Euler_setattr,				/*tp_setattr */
	0,											/*tp_compare */
	(reprfunc) Euler_repr,						/*tp_repr */
	0,											/*tp_as_number */
	&Euler_SeqMethods,							/*tp_as_sequence */
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

	euler_Type.ob_type = &PyType_Type;
	self = PyObject_NEW(EulerObject, &euler_Type);
	self->data.blend_data = NULL;
	self->data.py_data = NULL;

	if(type == Py_WRAP){
		self->data.blend_data = eul;
		self->eul = self->data.blend_data;
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
	}else{ //bad type
		return NULL;
	}
	return (PyObject *) EXPP_incr_ret((PyObject *)self);
}

