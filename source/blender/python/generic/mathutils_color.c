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
 * Contributor(s): Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "mathutils.h"

#include "BLI_math.h"
#include "BLI_utildefines.h"



#define COLOR_SIZE 3

//----------------------------------mathutils.Color() -------------------
//makes a new color for you to play with
static PyObject *Color_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
	float col[3]= {0.0f, 0.0f, 0.0f};

	if(kwds && PyDict_Size(kwds)) {
		PyErr_SetString(PyExc_TypeError, "mathutils.Color(): takes no keyword args");
		return NULL;
	}

	switch(PyTuple_GET_SIZE(args)) {
	case 0:
		break;
	case 1:
		if((mathutils_array_parse(col, COLOR_SIZE, COLOR_SIZE, PyTuple_GET_ITEM(args, 0), "mathutils.Color()")) == -1)
			return NULL;
		break;
	default:
		PyErr_SetString(PyExc_TypeError, "mathutils.Color(): more then a single arg given");
		return NULL;
	}
	return newColorObject(col, Py_NEW, type);
}

//-----------------------------METHODS----------------------------

/* note: BaseMath_ReadCallback must be called beforehand */
static PyObject *Color_ToTupleExt(ColorObject *self, int ndigits)
{
	PyObject *ret;
	int i;

	ret= PyTuple_New(COLOR_SIZE);

	if(ndigits >= 0) {
		for(i= 0; i < COLOR_SIZE; i++) {
			PyTuple_SET_ITEM(ret, i, PyFloat_FromDouble(double_round((double)self->col[i], ndigits)));
		}
	}
	else {
		for(i= 0; i < COLOR_SIZE; i++) {
			PyTuple_SET_ITEM(ret, i, PyFloat_FromDouble(self->col[i]));
		}
	}

	return ret;
}

static char Color_copy_doc[] =
".. function:: copy()\n"
"\n"
"   Returns a copy of this color.\n"
"\n"
"   :return: A copy of the color.\n"
"   :rtype: :class:`Color`\n"
"\n"
"   .. note:: use this to get a copy of a wrapped color with no reference to the original data.\n";

static PyObject *Color_copy(ColorObject *self)
{
	if(!BaseMath_ReadCallback(self))
		return NULL;

	return newColorObject(self->col, Py_NEW, Py_TYPE(self));
}

//----------------------------print object (internal)--------------
//print the object to screen

static PyObject *Color_repr(ColorObject * self)
{
	PyObject *ret, *tuple;
	
	if(!BaseMath_ReadCallback(self))
		return NULL;

	tuple= Color_ToTupleExt(self, -1);

	ret= PyUnicode_FromFormat("Color(%R)", tuple);

	Py_DECREF(tuple);
	return ret;
}

//------------------------tp_richcmpr
//returns -1 execption, 0 false, 1 true
static PyObject* Color_richcmpr(PyObject *objectA, PyObject *objectB, int comparison_type)
{
	ColorObject *colA = NULL, *colB = NULL;
	int result = 0;

	if(ColorObject_Check(objectA)) {
		colA = (ColorObject*)objectA;
		if(!BaseMath_ReadCallback(colA))
			return NULL;
	}
	if(ColorObject_Check(objectB)) {
		colB = (ColorObject*)objectB;
		if(!BaseMath_ReadCallback(colB))
			return NULL;
	}

	if (!colA || !colB){
		if (comparison_type == Py_NE){
			Py_RETURN_TRUE;
		}else{
			Py_RETURN_FALSE;
		}
	}
	colA = (ColorObject*)objectA;
	colB = (ColorObject*)objectB;

	switch (comparison_type){
		case Py_EQ:
			result = EXPP_VectorsAreEqual(colA->col, colB->col, COLOR_SIZE, 1);
			break;
		case Py_NE:
			result = !EXPP_VectorsAreEqual(colA->col, colB->col, COLOR_SIZE, 1);
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

//---------------------SEQUENCE PROTOCOLS------------------------
//----------------------------len(object)------------------------
//sequence length
static int Color_len(ColorObject *UNUSED(self))
{
	return COLOR_SIZE;
}
//----------------------------object[]---------------------------
//sequence accessor (get)
static PyObject *Color_item(ColorObject * self, int i)
{
	if(i<0) i= COLOR_SIZE-i;

	if(i < 0 || i >= COLOR_SIZE) {
		PyErr_SetString(PyExc_IndexError, "color[attribute]: array index out of range");
		return NULL;
	}

	if(!BaseMath_ReadIndexCallback(self, i))
		return NULL;

	return PyFloat_FromDouble(self->col[i]);

}
//----------------------------object[]-------------------------
//sequence accessor (set)
static int Color_ass_item(ColorObject * self, int i, PyObject * value)
{
	float f = PyFloat_AsDouble(value);

	if(f == -1 && PyErr_Occurred()) { // parsed item not a number
		PyErr_SetString(PyExc_TypeError, "color[attribute] = x: argument not a number");
		return -1;
	}

	if(i<0) i= COLOR_SIZE-i;

	if(i < 0 || i >= COLOR_SIZE){
		PyErr_SetString(PyExc_IndexError, "color[attribute] = x: array assignment index out of range");
		return -1;
	}

	self->col[i] = f;

	if(!BaseMath_WriteIndexCallback(self, i))
		return -1;

	return 0;
}
//----------------------------object[z:y]------------------------
//sequence slice (get)
static PyObject *Color_slice(ColorObject * self, int begin, int end)
{
	PyObject *tuple;
	int count;

	if(!BaseMath_ReadCallback(self))
		return NULL;

	CLAMP(begin, 0, COLOR_SIZE);
	if (end<0) end= (COLOR_SIZE + 1) + end;
	CLAMP(end, 0, COLOR_SIZE);
	begin= MIN2(begin, end);

	tuple= PyTuple_New(end - begin);
	for(count= begin; count < end; count++) {
		PyTuple_SET_ITEM(tuple, count - begin, PyFloat_FromDouble(self->col[count]));
	}

	return tuple;
}
//----------------------------object[z:y]------------------------
//sequence slice (set)
static int Color_ass_slice(ColorObject * self, int begin, int end, PyObject * seq)
{
	int i, size;
	float col[COLOR_SIZE];

	if(!BaseMath_ReadCallback(self))
		return -1;

	CLAMP(begin, 0, COLOR_SIZE);
	if (end<0) end= (COLOR_SIZE + 1) + end;
	CLAMP(end, 0, COLOR_SIZE);
	begin = MIN2(begin,end);

	if((size=mathutils_array_parse(col, 0, COLOR_SIZE, seq, "mathutils.Color[begin:end] = []")) == -1)
		return -1;

	if(size != (end - begin)){
		PyErr_SetString(PyExc_TypeError, "color[begin:end] = []: size mismatch in slice assignment");
		return -1;
	}

	for(i= 0; i < COLOR_SIZE; i++)
		self->col[begin + i] = col[i];

	(void)BaseMath_WriteCallback(self);
	return 0;
}

static PyObject *Color_subscript(ColorObject *self, PyObject *item)
{
	if (PyIndex_Check(item)) {
		Py_ssize_t i;
		i = PyNumber_AsSsize_t(item, PyExc_IndexError);
		if (i == -1 && PyErr_Occurred())
			return NULL;
		if (i < 0)
			i += COLOR_SIZE;
		return Color_item(self, i);
	} else if (PySlice_Check(item)) {
		Py_ssize_t start, stop, step, slicelength;

		if (PySlice_GetIndicesEx((PySliceObject*)item, COLOR_SIZE, &start, &stop, &step, &slicelength) < 0)
			return NULL;

		if (slicelength <= 0) {
			return PyList_New(0);
		}
		else if (step == 1) {
			return Color_slice(self, start, stop);
		}
		else {
			PyErr_SetString(PyExc_TypeError, "slice steps not supported with color");
			return NULL;
		}
	}
	else {
		PyErr_Format(PyExc_TypeError, "color indices must be integers, not %.200s", Py_TYPE(item)->tp_name);
		return NULL;
	}
}

static int Color_ass_subscript(ColorObject *self, PyObject *item, PyObject *value)
{
	if (PyIndex_Check(item)) {
		Py_ssize_t i = PyNumber_AsSsize_t(item, PyExc_IndexError);
		if (i == -1 && PyErr_Occurred())
			return -1;
		if (i < 0)
			i += COLOR_SIZE;
		return Color_ass_item(self, i, value);
	}
	else if (PySlice_Check(item)) {
		Py_ssize_t start, stop, step, slicelength;

		if (PySlice_GetIndicesEx((PySliceObject*)item, COLOR_SIZE, &start, &stop, &step, &slicelength) < 0)
			return -1;

		if (step == 1)
			return Color_ass_slice(self, start, stop, value);
		else {
			PyErr_SetString(PyExc_TypeError, "slice steps not supported with color");
			return -1;
		}
	}
	else {
		PyErr_Format(PyExc_TypeError, "color indices must be integers, not %.200s", Py_TYPE(item)->tp_name);
		return -1;
	}
}

//-----------------PROTCOL DECLARATIONS--------------------------
static PySequenceMethods Color_SeqMethods = {
	(lenfunc) Color_len,					/* sq_length */
	(binaryfunc) NULL,						/* sq_concat */
	(ssizeargfunc) NULL,					/* sq_repeat */
	(ssizeargfunc) Color_item,				/* sq_item */
	NULL,									/* sq_slice, deprecated */
	(ssizeobjargproc) Color_ass_item,		/* sq_ass_item */
	NULL,									/* sq_ass_slice, deprecated */
	(objobjproc) NULL,						/* sq_contains */
	(binaryfunc) NULL,						/* sq_inplace_concat */
	(ssizeargfunc) NULL,					/* sq_inplace_repeat */
};

static PyMappingMethods Color_AsMapping = {
	(lenfunc)Color_len,
	(binaryfunc)Color_subscript,
	(objobjargproc)Color_ass_subscript
};

/* color channel, vector.r/g/b */
static PyObject *Color_getChannel( ColorObject * self, void *type )
{
	return Color_item(self, GET_INT_FROM_POINTER(type));
}

static int Color_setChannel(ColorObject * self, PyObject * value, void * type)
{
	return Color_ass_item(self, GET_INT_FROM_POINTER(type), value);
}

/* color channel (HSV), color.h/s/v */
static PyObject *Color_getChannelHSV( ColorObject * self, void *type )
{
	float hsv[3];
	int i= GET_INT_FROM_POINTER(type);

	if(!BaseMath_ReadCallback(self))
		return NULL;

	rgb_to_hsv(self->col[0], self->col[1], self->col[2], &(hsv[0]), &(hsv[1]), &(hsv[2]));

	return PyFloat_FromDouble(hsv[i]);
}

static int Color_setChannelHSV(ColorObject * self, PyObject * value, void * type)
{
	float hsv[3];
	int i= GET_INT_FROM_POINTER(type);
	float f = PyFloat_AsDouble(value);

	if(f == -1 && PyErr_Occurred()) {
		PyErr_SetString(PyExc_TypeError, "color.h/s/v = value: argument not a number");
		return -1;
	}

	if(!BaseMath_ReadCallback(self))
		return -1;

	rgb_to_hsv(self->col[0], self->col[1], self->col[2], &(hsv[0]), &(hsv[1]), &(hsv[2]));
	CLAMP(f, 0.0f, 1.0f);
	hsv[i] = f;
	hsv_to_rgb(hsv[0], hsv[1], hsv[2], &(self->col[0]), &(self->col[1]), &(self->col[2]));

	if(!BaseMath_WriteCallback(self))
		return -1;

	return 0;
}

/* color channel (HSV), color.h/s/v */
static PyObject *Color_getHSV(ColorObject * self, void *UNUSED(closure))
{
	float hsv[3];
	PyObject *ret;

	if(!BaseMath_ReadCallback(self))
		return NULL;

	rgb_to_hsv(self->col[0], self->col[1], self->col[2], &(hsv[0]), &(hsv[1]), &(hsv[2]));

	ret= PyTuple_New(3);
	PyTuple_SET_ITEM(ret, 0, PyFloat_FromDouble(hsv[0]));
	PyTuple_SET_ITEM(ret, 1, PyFloat_FromDouble(hsv[1]));
	PyTuple_SET_ITEM(ret, 2, PyFloat_FromDouble(hsv[2]));
	return ret;
}

static int Color_setHSV(ColorObject * self, PyObject * value, void *UNUSED(closure))
{
	float hsv[3];

	if(mathutils_array_parse(hsv, 3, 3, value, "mathutils.Color.hsv = value") == -1)
		return -1;

	CLAMP(hsv[0], 0.0f, 1.0f);
	CLAMP(hsv[1], 0.0f, 1.0f);
	CLAMP(hsv[2], 0.0f, 1.0f);

	hsv_to_rgb(hsv[0], hsv[1], hsv[2], &(self->col[0]), &(self->col[1]), &(self->col[2]));

	if(!BaseMath_WriteCallback(self))
		return -1;

	return 0;
}

/*****************************************************************************/
/* Python attributes get/set structure:                                      */
/*****************************************************************************/
static PyGetSetDef Color_getseters[] = {
	{(char *)"r", (getter)Color_getChannel, (setter)Color_setChannel, (char *)"Red color channel.\n\n:type: float", (void *)0},
	{(char *)"g", (getter)Color_getChannel, (setter)Color_setChannel, (char *)"Green color channel.\n\n:type: float", (void *)1},
	{(char *)"b", (getter)Color_getChannel, (setter)Color_setChannel, (char *)"Blue color channel.\n\n:type: float", (void *)2},

	{(char *)"h", (getter)Color_getChannelHSV, (setter)Color_setChannelHSV, (char *)"HSV Hue component in [0, 1].\n\n:type: float", (void *)0},
	{(char *)"s", (getter)Color_getChannelHSV, (setter)Color_setChannelHSV, (char *)"HSV Saturation component in [0, 1].\n\n:type: float", (void *)1},
	{(char *)"v", (getter)Color_getChannelHSV, (setter)Color_setChannelHSV, (char *)"HSV Value component in [0, 1].\n\n:type: float", (void *)2},

	{(char *)"hsv", (getter)Color_getHSV, (setter)Color_setHSV, (char *)"HSV Values in [0, 1].\n\n:type: float triplet", (void *)0},

	{(char *)"is_wrapped", (getter)BaseMathObject_getWrapped, (setter)NULL, BaseMathObject_Wrapped_doc, NULL},
	{(char *)"owner", (getter)BaseMathObject_getOwner, (setter)NULL, BaseMathObject_Owner_doc, NULL},
	{NULL,NULL,NULL,NULL,NULL}  /* Sentinel */
};


//-----------------------METHOD DEFINITIONS ----------------------
static struct PyMethodDef Color_methods[] = {
	{"__copy__", (PyCFunction) Color_copy, METH_NOARGS, Color_copy_doc},
	{"copy", (PyCFunction) Color_copy, METH_NOARGS, Color_copy_doc},
	{NULL, NULL, 0, NULL}
};

//------------------PY_OBECT DEFINITION--------------------------
static char color_doc[] =
"This object gives access to Colors in Blender.";

PyTypeObject color_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"mathutils.Color",						//tp_name
	sizeof(ColorObject),			//tp_basicsize
	0,								//tp_itemsize
	(destructor)BaseMathObject_dealloc,		//tp_dealloc
	0,								//tp_print
	0,								//tp_getattr
	0,								//tp_setattr
	0,								//tp_compare
	(reprfunc) Color_repr,			//tp_repr
	0,				//tp_as_number
	&Color_SeqMethods,				//tp_as_sequence
	&Color_AsMapping,				//tp_as_mapping
	0,								//tp_hash
	0,								//tp_call
	0,								//tp_str
	0,								//tp_getattro
	0,								//tp_setattro
	0,								//tp_as_buffer
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, //tp_flags
	color_doc, //tp_doc
	0,								//tp_traverse
	0,								//tp_clear
	(richcmpfunc)Color_richcmpr,	//tp_richcompare
	0,								//tp_weaklistoffset
	0,								//tp_iter
	0,								//tp_iternext
	Color_methods,					//tp_methods
	0,								//tp_members
	Color_getseters,				//tp_getset
	0,								//tp_base
	0,								//tp_dict
	0,								//tp_descr_get
	0,								//tp_descr_set
	0,								//tp_dictoffset
	0,								//tp_init
	0,								//tp_alloc
	Color_new,						//tp_new
	0,								//tp_free
	0,								//tp_is_gc
	0,								//tp_bases
	0,								//tp_mro
	0,								//tp_cache
	0,								//tp_subclasses
	0,								//tp_weaklist
	0								//tp_del
};
//------------------------newColorObject (internal)-------------
//creates a new color object
/*pass Py_WRAP - if vector is a WRAPPER for data allocated by BLENDER
 (i.e. it was allocated elsewhere by MEM_mallocN())
  pass Py_NEW - if vector is not a WRAPPER and managed by PYTHON
 (i.e. it must be created here with PyMEM_malloc())*/
PyObject *newColorObject(float *col, int type, PyTypeObject *base_type)
{
	ColorObject *self;

	if(base_type)	self = (ColorObject *)base_type->tp_alloc(base_type, 0);
	else			self = PyObject_NEW(ColorObject, &color_Type);

	/* init callbacks as NULL */
	self->cb_user= NULL;
	self->cb_type= self->cb_subtype= 0;

	if(type == Py_WRAP){
		self->col = col;
		self->wrapped = Py_WRAP;
	}
	else if (type == Py_NEW){
		self->col = PyMem_Malloc(COLOR_SIZE * sizeof(float));
		if(col)
			copy_v3_v3(self->col, col);
		else
			zero_v3(self->col);

		self->wrapped = Py_NEW;
	}
	else {
		return NULL;
	}

	return (PyObject *)self;
}

PyObject *newColorObject_cb(PyObject *cb_user, int cb_type, int cb_subtype)
{
	ColorObject *self= (ColorObject *)newColorObject(NULL, Py_NEW, NULL);
	if(self) {
		Py_INCREF(cb_user);
		self->cb_user=			cb_user;
		self->cb_type=			(unsigned char)cb_type;
		self->cb_subtype=		(unsigned char)cb_subtype;
	}

	return (PyObject *)self;
}
