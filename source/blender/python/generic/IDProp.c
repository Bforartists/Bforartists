/**
 * $Id: IDProp.c
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
 *
 * Contributor(s): Joseph Eagar, Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "DNA_ID.h"

#include "BKE_idprop.h"

#include "IDProp.h"
// #include "gen_utils.h"

#include "MEM_guardedalloc.h"

#define BSTR_EQ(a, b)	(*(a) == *(b) && !strcmp(a, b))

/*** Function to wrap ID properties ***/
PyObject *BPy_Wrap_IDProperty(ID *id, IDProperty *prop, IDProperty *parent);

extern PyTypeObject IDArray_Type;
extern PyTypeObject IDGroup_Iter_Type;

/*********************** ID Property Main Wrapper Stuff ***************/

PyObject *IDGroup_repr( BPy_IDProperty *self )
{
	return PyUnicode_FromFormat( "<bpy ID property from \"%s\">", self->id->name);
}

extern PyTypeObject IDGroup_Type;

PyObject *BPy_IDGroup_WrapData( ID *id, IDProperty *prop )
{
	switch ( prop->type ) {
		case IDP_STRING:
			return PyUnicode_FromString( prop->data.pointer );
		case IDP_INT:
			return PyLong_FromLong( (long)prop->data.val );
		case IDP_FLOAT:
			return PyFloat_FromDouble( (double)(*(float*)(&prop->data.val)) );
		case IDP_DOUBLE:
			return PyFloat_FromDouble( (*(double*)(&prop->data.val)) );
		case IDP_GROUP:
			/*blegh*/
			{
				BPy_IDProperty *group = PyObject_New(BPy_IDProperty, &IDGroup_Type);
				if (!group) {
					PyErr_SetString( PyExc_RuntimeError, "PyObject_New() failed" );
					return NULL;
				}

				group->id = id;
				group->prop = prop;
				return (PyObject*) group;
			}
		case IDP_ARRAY:
			{
				BPy_IDProperty *array = PyObject_New(BPy_IDProperty, &IDArray_Type);
				if (!array) {
					PyErr_SetString( PyExc_RuntimeError, "PyObject_New() failed" );
					return NULL;
				}
				array->id = id;
				array->prop = prop;
				return (PyObject*) array;
			}
	}
	Py_RETURN_NONE;
}

int BPy_IDGroup_SetData(BPy_IDProperty *self, IDProperty *prop, PyObject *value)
{
	switch (prop->type) {
		case IDP_STRING:
		{
			char *st;
			if (!PyUnicode_Check(value)) {
				PyErr_SetString(PyExc_TypeError, "expected a string!");
				return -1;
			}

			st = _PyUnicode_AsString(value);
			IDP_ResizeArray(prop, strlen(st)+1);
			strcpy(prop->data.pointer, st);
			return 0;
		}

		case IDP_INT:
		{
			int ivalue= PyLong_AsSsize_t(value);
			if (ivalue==-1 && PyErr_Occurred()) {
				PyErr_SetString(PyExc_TypeError, "expected an int type");
				return -1;
			}
			prop->data.val = ivalue;
			break;
		}
		case IDP_FLOAT:
		{
			float fvalue= (float)PyFloat_AsDouble(value);
			if (fvalue==-1 && PyErr_Occurred()) {
				PyErr_SetString(PyExc_TypeError, "expected a float");
				return -1;
			}
			*(float*)&self->prop->data.val = fvalue;
			break;
		}
		case IDP_DOUBLE:
		{
			double dvalue= PyFloat_AsDouble(value);
			if (dvalue==-1 && PyErr_Occurred()) {
				PyErr_SetString(PyExc_TypeError, "expected a float");
				return -1;
			}
			*(double*)&self->prop->data.val = dvalue;
			break;
		}
		default:
			PyErr_SetString(PyExc_AttributeError, "attempt to set read-only attribute!");
			return -1;
	}
	return 0;
}

PyObject *BPy_IDGroup_GetName(BPy_IDProperty *self, void *bleh)
{
	return PyUnicode_FromString(self->prop->name);
}

static int BPy_IDGroup_SetName(BPy_IDProperty *self, PyObject *value, void *bleh)
{
	char *st;
	if (!PyUnicode_Check(value)) {
		PyErr_SetString(PyExc_TypeError, "expected a string!");
		return -1;
	}

	st = _PyUnicode_AsString(value);
	if (strlen(st) >= MAX_IDPROP_NAME) {
		PyErr_SetString(PyExc_TypeError, "string length cannot exceed 31 characters!");
		return -1;
	}

	strcpy(self->prop->name, st);
	return 0;
}

#if 0
static PyObject *BPy_IDGroup_GetType(BPy_IDProperty *self)
{
	return PyLong_FromSsize_t(self->prop->type);
}
#endif

static PyGetSetDef BPy_IDGroup_getseters[] = {
	{"name",
	 (getter)BPy_IDGroup_GetName, (setter)BPy_IDGroup_SetName,
	 "The name of this Group.",
	 NULL},
	 {NULL, NULL, NULL, NULL, NULL}
};

static Py_ssize_t BPy_IDGroup_Map_Len(BPy_IDProperty *self)
{
	if (self->prop->type != IDP_GROUP) {
		PyErr_SetString( PyExc_TypeError, "len() of unsized object");
		return -1;
	}

	return self->prop->len;
}

static PyObject *BPy_IDGroup_Map_GetItem(BPy_IDProperty *self, PyObject *item)
{
	IDProperty *idprop;
	char *name;

	if (self->prop->type  != IDP_GROUP) {
		PyErr_SetString( PyExc_TypeError, "unsubscriptable object");
		return NULL;
	}

	name= _PyUnicode_AsString(item);

	if (name == NULL) {
		PyErr_SetString( PyExc_TypeError, "only strings are allowed as keys of ID properties");
		return NULL;
	}

	idprop= IDP_GetPropertyFromGroup(self->prop, name);

	if(idprop==NULL) {
		PyErr_SetString( PyExc_KeyError, "key not in subgroup dict");
		return NULL;
	}

	return BPy_IDGroup_WrapData(self->id, idprop);

}

/*returns NULL on success, error string on failure*/
char *BPy_IDProperty_Map_ValidateAndCreate(char *name, IDProperty *group, PyObject *ob)
{
	IDProperty *prop = NULL;
	IDPropertyTemplate val = {0};

	if(strlen(name) >= sizeof(group->name))
		return "the length of IDProperty names is limited to 31 characters";

	if (PyFloat_Check(ob)) {
		val.d = PyFloat_AsDouble(ob);
		prop = IDP_New(IDP_DOUBLE, val, name);
	} else if (PyLong_Check(ob)) {
		val.i = (int) PyLong_AsSsize_t(ob);
		prop = IDP_New(IDP_INT, val, name);
	} else if (PyUnicode_Check(ob)) {
		val.str = _PyUnicode_AsString(ob);
		prop = IDP_New(IDP_STRING, val, name);
	} else if (PySequence_Check(ob)) {
		PyObject *item;
		int i;

		/*validate sequence and derive type.
		we assume IDP_INT unless we hit a float
		number; then we assume it's */
		val.array.type = IDP_INT;
		val.array.len = PySequence_Length(ob);
		for (i=0; i<val.array.len; i++) {
			item = PySequence_GetItem(ob, i);
			if (PyFloat_Check(item)) val.array.type = IDP_DOUBLE;
			else if (!PyLong_Check(item)) {
				Py_XDECREF(item);
				return "only floats and ints are allowed in ID property arrays";
			}
			Py_XDECREF(item);
		}

		prop = IDP_New(IDP_ARRAY, val, name);
		for (i=0; i<val.array.len; i++) {
			item = PySequence_GetItem(ob, i);
			if (val.array.type == IDP_INT) {
				((int*)prop->data.pointer)[i] = (int)PyLong_AsSsize_t(item);
			} else {
				((double*)prop->data.pointer)[i] = (float)PyFloat_AsDouble(item);
			}
		}
	} else if (PyMapping_Check(ob)) {
		PyObject *keys, *vals, *key, *pval;
		int i, len;
		/*yay! we get into recursive stuff now!*/
		keys = PyMapping_Keys(ob);
		vals = PyMapping_Values(ob);

		/*we allocate the group first; if we hit any invalid data,
		  we can delete it easily enough.*/
		prop = IDP_New(IDP_GROUP, val, name);
		len = PyMapping_Length(ob);
		for (i=0; i<len; i++) {
			key = PySequence_GetItem(keys, i);
			pval = PySequence_GetItem(vals, i);
			if (!PyUnicode_Check(key)) {
				IDP_FreeProperty(prop);
				MEM_freeN(prop);
				Py_XDECREF(keys);
				Py_XDECREF(vals);
				Py_XDECREF(key);
				Py_XDECREF(pval);
				return "invalid element in subgroup dict template!";
			}
			if (BPy_IDProperty_Map_ValidateAndCreate(_PyUnicode_AsString(key), prop, pval)) {
				IDP_FreeProperty(prop);
				MEM_freeN(prop);
				Py_XDECREF(keys);
				Py_XDECREF(vals);
				Py_XDECREF(key);
				Py_XDECREF(pval);
				return "invalid element in subgroup dict template!";
			}
			Py_XDECREF(key);
			Py_XDECREF(pval);
		}
		Py_XDECREF(keys);
		Py_XDECREF(vals);
	} else return "invalid property value";

	IDP_ReplaceInGroup(group, prop);
	return NULL;
}

static int BPy_IDGroup_Map_SetItem(BPy_IDProperty *self, PyObject *key, PyObject *val)
{
	char *err;

	if (self->prop->type  != IDP_GROUP) {
		PyErr_SetString( PyExc_TypeError, "unsubscriptable object");
		return -1;
	}

	if (!PyUnicode_Check(key)) {
		PyErr_SetString( PyExc_TypeError, "only strings are allowed as subgroup keys" );
		return -1;
	}

	if (val == NULL) {
		IDProperty *pkey = IDP_GetPropertyFromGroup(self->prop, _PyUnicode_AsString(key));
		if (pkey) {
			IDP_RemFromGroup(self->prop, pkey);
			IDP_FreeProperty(pkey);
			MEM_freeN(pkey);
			return 0;
		} else {
			PyErr_SetString( PyExc_RuntimeError, "property not found in group" );
			return -1;
		}
	}

	err = BPy_IDProperty_Map_ValidateAndCreate(_PyUnicode_AsString(key), self->prop, val);
	if (err) {
		PyErr_SetString( PyExc_RuntimeError, err );
		return -1;
	}

	return 0;
}

static PyObject *BPy_IDGroup_SpawnIterator(BPy_IDProperty *self)
{
	BPy_IDGroup_Iter *iter = PyObject_New(BPy_IDGroup_Iter, &IDGroup_Iter_Type);

	if (!iter) {
		PyErr_SetString( PyExc_RuntimeError, "PyObject_New() failed" );
		return NULL;
	}
	iter->group = self;
	iter->mode = IDPROP_ITER_KEYS;
	iter->cur = self->prop->data.group.first;
	Py_XINCREF(iter);
	return (PyObject*) iter;
}

static PyObject *BPy_IDGroup_MapDataToPy(IDProperty *prop)
{
	switch (prop->type) {
		case IDP_STRING:
			return PyUnicode_FromString(prop->data.pointer);
			break;
		case IDP_FLOAT:
			return PyFloat_FromDouble(*((float*)&prop->data.val));
			break;
		case IDP_DOUBLE:
			return PyFloat_FromDouble(*((double*)&prop->data.val));
			break;
		case IDP_INT:
			return PyLong_FromSsize_t( prop->data.val );
			break;
		case IDP_ARRAY:
		{
			PyObject *seq = PyList_New(prop->len);
			int i;

			if (!seq) {
				PyErr_SetString( PyExc_RuntimeError, "PyList_New() failed" );
				return NULL;
			}

			for (i=0; i<prop->len; i++) {
				if (prop->subtype == IDP_FLOAT) {
						PyList_SetItem(seq, i,
						PyFloat_FromDouble(((float*)prop->data.pointer)[i]));
				} else if (prop->subtype == IDP_DOUBLE) {
						PyList_SetItem(seq, i,
						PyFloat_FromDouble(((double*)prop->data.pointer)[i]));
				} else 	{ PyList_SetItem(seq, i,
						  PyLong_FromLong(((int*)prop->data.pointer)[i]));
				}
			}
			return seq;
		}
		case IDP_GROUP:
		{
			PyObject *dict = PyDict_New(), *wrap;
			IDProperty *loop;

			if (!dict) {
				PyErr_SetString( PyExc_RuntimeError, "PyDict_New() failed" );
				return NULL;
			}

			for (loop=prop->data.group.first; loop; loop=loop->next) {
				wrap = BPy_IDGroup_MapDataToPy(loop);
				if (!wrap) {
					PyErr_SetString( PyExc_RuntimeError, "BPy_IDGroup_MapDataToPy() failed" );
					return NULL;
				}

				PyDict_SetItemString(dict, loop->name, wrap);
			}
			return dict;
		}
	}

	PyErr_SetString( PyExc_RuntimeError, "eek!! a property exists with a bad type code!!!" );
	return NULL;
}

static PyObject *BPy_IDGroup_Pop(BPy_IDProperty *self, PyObject *value)
{
	IDProperty *idprop;
	PyObject *pyform;
	char *name = _PyUnicode_AsString(value);

	if (!name) {
		PyErr_SetString( PyExc_TypeError, "pop expected at least 1 argument, got 0" );
		return NULL;
	}

	idprop= IDP_GetPropertyFromGroup(self->prop, name);

	if(idprop) {
		pyform = BPy_IDGroup_MapDataToPy(idprop);

		if (!pyform) {
			/*ok something bad happened with the pyobject,
			  so don't remove the prop from the group.  if pyform is
			  NULL, then it already should have raised an exception.*/
			  return NULL;
		}

		IDP_RemFromGroup(self->prop, idprop);
		return pyform;
	}

	PyErr_SetString( PyExc_KeyError, "item not in group" );
	return NULL;
}

static PyObject *BPy_IDGroup_IterItems(BPy_IDProperty *self)
{
	BPy_IDGroup_Iter *iter = PyObject_New(BPy_IDGroup_Iter, &IDGroup_Iter_Type);

	if (!iter) {
		PyErr_SetString( PyExc_RuntimeError, "PyObject_New() failed" );
		return NULL;
	}

	iter->group = self;
	iter->mode = IDPROP_ITER_ITEMS;
	iter->cur = self->prop->data.group.first;
	Py_XINCREF(iter);
	return (PyObject*) iter;
}

static PyObject *BPy_IDGroup_GetKeys(BPy_IDProperty *self)
{
	PyObject *seq = PyList_New(self->prop->len);
	IDProperty *loop;
	int i, j;

	if (!seq) {
		PyErr_SetString( PyExc_RuntimeError, "PyList_New() failed" );
		return NULL;
	}

	for (i=0, loop=self->prop->data.group.first; loop; loop=loop->next, i++)
		PyList_SetItem(seq, i, PyUnicode_FromString(loop->name));

	if (i != self->prop->len) {
		printf("ID Property Error found and corrected in BPy_IDGroup_GetKeys!\n");

		/*fill rest of list with valid references to None*/
		for (j=i; j<self->prop->len; j++) {
			Py_INCREF(Py_None);
			PyList_SetItem(seq, j, Py_None);
		}

		/*set correct group length*/
		self->prop->len = i;

		/*free the list*/
		Py_DECREF(seq);

		/*call self again*/
		return BPy_IDGroup_GetKeys(self);
	}

	return seq;
}

static PyObject *BPy_IDGroup_GetValues(BPy_IDProperty *self)
{
	PyObject *seq = PyList_New(self->prop->len);
	IDProperty *loop;
	int i, j;

	if (!seq) {
		PyErr_SetString( PyExc_RuntimeError, "PyList_New() failed" );
		return NULL;
	}

	for (i=0, loop=self->prop->data.group.first; loop; loop=loop->next, i++) {
		PyList_SetItem(seq, i, BPy_IDGroup_WrapData(self->id, loop));
	}

	if (i != self->prop->len) {
		printf("ID Property Error found and corrected in BPy_IDGroup_GetValues!\n");

		/*fill rest of list with valid references to None*/
		for (j=i; j<self->prop->len; j++) {
			Py_INCREF(Py_None);
			PyList_SetItem(seq, j, Py_None);
		}

		/*set correct group length*/
		self->prop->len = i;

		/*free the old list*/
		Py_DECREF(seq);

		/*call self again*/
		return BPy_IDGroup_GetValues(self);
	}

	return seq;
}

static int BPy_IDGroup_Contains(BPy_IDProperty *self, PyObject *value)
{
	char *name = _PyUnicode_AsString(value);

	if (!name) {
		PyErr_SetString( PyExc_TypeError, "expected a string");
		return -1;
	}

	return IDP_GetPropertyFromGroup(self->prop, name) ? 1:0;
}

static PyObject *BPy_IDGroup_Update(BPy_IDProperty *self, PyObject *value)
{
	PyObject *pkey, *pval;
	Py_ssize_t i=0;

	if (!PyDict_Check(value)) {
		PyErr_SetString( PyExc_TypeError, "expected an object derived from dict.");
		return NULL;
	}

	while (PyDict_Next(value, &i, &pkey, &pval)) {
		BPy_IDGroup_Map_SetItem(self, pkey, pval);
		if (PyErr_Occurred()) return NULL;
	}

	Py_RETURN_NONE;
}

static PyObject *BPy_IDGroup_ConvertToPy(BPy_IDProperty *self)
{
	return BPy_IDGroup_MapDataToPy(self->prop);
}

static struct PyMethodDef BPy_IDGroup_methods[] = {
	{"pop", (PyCFunction)BPy_IDGroup_Pop, METH_O,
		"pop an item from the group; raises KeyError if the item doesn't exist."},
	{"iteritems", (PyCFunction)BPy_IDGroup_IterItems, METH_NOARGS,
		"iterate through the items in the dict; behaves like dictionary method iteritems."},
	{"keys", (PyCFunction)BPy_IDGroup_GetKeys, METH_NOARGS,
		"get the keys associated with this group as a list of strings."},
	{"values", (PyCFunction)BPy_IDGroup_GetValues, METH_NOARGS,
		"get the values associated with this group."},
	{"update", (PyCFunction)BPy_IDGroup_Update, METH_O,
		"updates the values in the group with the values of another or a dict."},
	{"convert_to_pyobject", (PyCFunction)BPy_IDGroup_ConvertToPy, METH_NOARGS,
		"return a purely python version of the group."},
	{0, NULL, 0, NULL}
};

static PySequenceMethods BPy_IDGroup_Seq = {
	(lenfunc) BPy_IDGroup_Map_Len,			/* lenfunc sq_length */
	0,									/* binaryfunc sq_concat */
	0,									/* ssizeargfunc sq_repeat */
	0,									/* ssizeargfunc sq_item */ /* TODO - setting this will allow PySequence_Check to return True */
	0,									/* intintargfunc ***was_sq_slice*** */
	0,									/* intobjargproc sq_ass_item */
	0,									/* ssizeobjargproc ***was_sq_ass_slice*** */
	(objobjproc) BPy_IDGroup_Contains,	/* objobjproc sq_contains */
	0,									/* binaryfunc sq_inplace_concat */
	0,									/* ssizeargfunc sq_inplace_repeat */
};

PyMappingMethods BPy_IDGroup_Mapping = {
	(lenfunc)BPy_IDGroup_Map_Len, 			/*inquiry mp_length */
	(binaryfunc)BPy_IDGroup_Map_GetItem,		/*binaryfunc mp_subscript */
	(objobjargproc)BPy_IDGroup_Map_SetItem,	/*objobjargproc mp_ass_subscript */
};

PyTypeObject IDGroup_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	/*  For printing, in format "<module>.<name>" */
	"Blender IDProperty",           /* char *tp_name; */
	sizeof( BPy_IDProperty ),       /* int tp_basicsize; */
	0,                          /* tp_itemsize;  For allocation */

	/* Methods to implement standard operations */

	NULL,						/* destructor tp_dealloc; */
	NULL,                       /* printfunc tp_print; */
	NULL,     /* getattrfunc tp_getattr; */
	NULL,     /* setattrfunc tp_setattr; */
	NULL,                       /* cmpfunc tp_compare; */
	( reprfunc ) IDGroup_repr,     /* reprfunc tp_repr; */

	/* Method suites for standard classes */

	NULL,                       /* PyNumberMethods *tp_as_number; */
	&BPy_IDGroup_Seq,			/* PySequenceMethods *tp_as_sequence; */
	&BPy_IDGroup_Mapping,		/* PyMappingMethods *tp_as_mapping; */

	/* More standard operations (here for binary compatibility) */

	NULL,                       /* hashfunc tp_hash; */
	NULL,                       /* ternaryfunc tp_call; */
	NULL,                       /* reprfunc tp_str; */
	NULL,                       /* getattrofunc tp_getattro; */
	NULL,                       /* setattrofunc tp_setattro; */

	/* Functions to access object as input/output buffer */
	NULL,                       /* PyBufferProcs *tp_as_buffer; */

  /*** Flags to define presence of optional/expanded features ***/
	Py_TPFLAGS_DEFAULT,         /* long tp_flags; */

	NULL,                       /*  char *tp_doc;  Documentation string */
  /*** Assigned meaning in release 2.0 ***/
	/* call function for all accessible objects */
	NULL,                       /* traverseproc tp_traverse; */

	/* delete references to contained objects */
	NULL,                       /* inquiry tp_clear; */

  /***  Assigned meaning in release 2.1 ***/
  /*** rich comparisons ***/
	NULL,                       /* richcmpfunc tp_richcompare; */

  /***  weak reference enabler ***/
	0,                          /* long tp_weaklistoffset; */

  /*** Added in release 2.2 ***/
	/*   Iterators */
	(getiterfunc)BPy_IDGroup_SpawnIterator, /* getiterfunc tp_iter; */
	NULL,                       /* iternextfunc tp_iternext; */
  /*** Attribute descriptor and subclassing stuff ***/
	BPy_IDGroup_methods,        /* struct PyMethodDef *tp_methods; */
	NULL,                       /* struct PyMemberDef *tp_members; */
	BPy_IDGroup_getseters,       /* struct PyGetSetDef *tp_getset; */
};

/*********** Main external wrapping function *******/
PyObject *BPy_Wrap_IDProperty(ID *id, IDProperty *prop, IDProperty *parent)
{
	BPy_IDProperty *wrap = PyObject_New(BPy_IDProperty, &IDGroup_Type);

	if (!wrap) {
		PyErr_SetString( PyExc_RuntimeError, "PyObject_New() failed" );
		return NULL;
	}

	wrap->prop = prop;
	wrap->parent = parent;
	wrap->id = id;
	//wrap->destroy = 0;
	return (PyObject*) wrap;
}


/********Array Wrapper********/

static PyObject *IDArray_repr(BPy_IDArray *self)
{
	return PyUnicode_FromString("(ID Array)");
}


static PyObject *BPy_IDArray_GetType(BPy_IDArray *self)
{
	return PyLong_FromSsize_t( self->prop->subtype );
}

static PyObject *BPy_IDArray_GetLen(BPy_IDArray *self)
{
	return PyLong_FromSsize_t( self->prop->len );
}

static PyGetSetDef BPy_IDArray_getseters[] = {
	{"len",
	 (getter)BPy_IDArray_GetLen, (setter)NULL,
	 "The length of the array, can also be gotten with len(array).",
	 NULL},
	{"type",
	 (getter)BPy_IDArray_GetType, (setter)NULL,
	 "The type of the data in the array, is an ant.",
	 NULL},
	{NULL, NULL, NULL, NULL, NULL},
};

static int BPy_IDArray_Len(BPy_IDArray *self)
{
	return self->prop->len;
}

static PyObject *BPy_IDArray_GetItem(BPy_IDArray *self, int index)
{
	if (index < 0 || index >= self->prop->len) {
		PyErr_SetString( PyExc_IndexError, "index out of range!");
		return NULL;
	}

	switch (self->prop->subtype) {
		case IDP_FLOAT:
			return PyFloat_FromDouble( (double)(((float*)self->prop->data.pointer)[index]));
			break;
		case IDP_DOUBLE:
			return PyFloat_FromDouble( (((double*)self->prop->data.pointer)[index]));
			break;
		case IDP_INT:
			return PyLong_FromLong( (long)((int*)self->prop->data.pointer)[index] );
			break;
	}

	PyErr_SetString( PyExc_RuntimeError, "invalid/corrupt array type!");
	return NULL;
}

static int BPy_IDArray_SetItem(BPy_IDArray *self, int index, PyObject *value)
{
	int i;
	float f;
	double d;

	if (index < 0 || index >= self->prop->len) {
		PyErr_SetString( PyExc_RuntimeError, "index out of range!");
		return -1;
	}

	switch (self->prop->subtype) {
		case IDP_FLOAT:
			f= (float)PyFloat_AsDouble(value);
			if (f==-1 && PyErr_Occurred()) {
				PyErr_SetString(PyExc_TypeError, "expected a float");
				return -1;
			}
			((float*)self->prop->data.pointer)[index] = f;
			break;
		case IDP_DOUBLE:
			d= PyFloat_AsDouble(value);
			if (d==-1 && PyErr_Occurred()) {
				PyErr_SetString(PyExc_TypeError, "expected a float");
				return -1;
			}
			((double*)self->prop->data.pointer)[index] = d;
			break;
		case IDP_INT:
			i= PyLong_AsSsize_t(value);
			if (i==-1 && PyErr_Occurred()) {
				PyErr_SetString(PyExc_TypeError, "expected an int type");
				return -1;
			}

			((int*)self->prop->data.pointer)[index] = i;
			break;
	}
	return 0;
}

static PySequenceMethods BPy_IDArray_Seq = {
	(lenfunc) BPy_IDArray_Len,			/* inquiry sq_length */
	0,									/* binaryfunc sq_concat */
	0,									/* intargfunc sq_repeat */
	(ssizeargfunc)BPy_IDArray_GetItem,	/* intargfunc sq_item */
	0,									/* intintargfunc sq_slice */
	(ssizeobjargproc)BPy_IDArray_SetItem,	/* intobjargproc sq_ass_item */
	0,									/* intintobjargproc sq_ass_slice */
	0,									/* objobjproc sq_contains */
				/* Added in release 2.0 */
	0,									/* binaryfunc sq_inplace_concat */
	0,									/* intargfunc sq_inplace_repeat */
};

PyTypeObject IDArray_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	/*  For printing, in format "<module>.<name>" */
	"Blender IDArray",           /* char *tp_name; */
	sizeof( BPy_IDArray ),       /* int tp_basicsize; */
	0,                          /* tp_itemsize;  For allocation */

	/* Methods to implement standard operations */

	NULL,						/* destructor tp_dealloc; */
	NULL,                       /* printfunc tp_print; */
	NULL,     /* getattrfunc tp_getattr; */
	NULL,     /* setattrfunc tp_setattr; */
	NULL,                       /* cmpfunc tp_compare; */
	( reprfunc ) IDArray_repr,     /* reprfunc tp_repr; */

	/* Method suites for standard classes */

	NULL,                       /* PyNumberMethods *tp_as_number; */
	&BPy_IDArray_Seq,   			/* PySequenceMethods *tp_as_sequence; */
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
	Py_TPFLAGS_DEFAULT,         /* long tp_flags; */

	NULL,                       /*  char *tp_doc;  Documentation string */
  /*** Assigned meaning in release 2.0 ***/
	/* call function for all accessible objects */
	NULL,                       /* traverseproc tp_traverse; */

	/* delete references to contained objects */
	NULL,                       /* inquiry tp_clear; */

  /***  Assigned meaning in release 2.1 ***/
  /*** rich comparisons ***/
	NULL,                       /* richcmpfunc tp_richcompare; */

  /***  weak reference enabler ***/
	0,                          /* long tp_weaklistoffset; */

  /*** Added in release 2.2 ***/
	/*   Iterators */
	NULL,                       /* getiterfunc tp_iter; */
	NULL,                       /* iternextfunc tp_iternext; */

  /*** Attribute descriptor and subclassing stuff ***/
	NULL,                       /* struct PyMethodDef *tp_methods; */
	NULL,                       /* struct PyMemberDef *tp_members; */
	BPy_IDArray_getseters,       /* struct PyGetSetDef *tp_getset; */
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

/*********** ID Property Group iterator ********/

static PyObject *IDGroup_Iter_iterself(PyObject *self)
{
	Py_XINCREF(self);
	return self;
}

static PyObject *IDGroup_Iter_repr(BPy_IDGroup_Iter *self)
{
	return PyUnicode_FromString("(ID Property Group)");
}

static PyObject *BPy_Group_Iter_Next(BPy_IDGroup_Iter *self)
{
	IDProperty *cur=NULL;
	PyObject *tmpval;
	PyObject *ret;

	if (self->cur) {
		cur = self->cur;
		self->cur = self->cur->next;
		if (self->mode == IDPROP_ITER_ITEMS) {
			tmpval = BPy_IDGroup_WrapData(self->group->id, cur);
			ret = Py_BuildValue("[s, O]", cur->name, tmpval);
			Py_DECREF(tmpval);
			return ret;
		} else {
			return PyUnicode_FromString(cur->name);
		}
	} else {
		PyErr_SetString( PyExc_StopIteration, "iterator at end" );
		return NULL;
	}
}

PyTypeObject IDGroup_Iter_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	/*  For printing, in format "<module>.<name>" */
	"Blender IDGroup_Iter",           /* char *tp_name; */
	sizeof( BPy_IDGroup_Iter ),       /* int tp_basicsize; */
	0,                          /* tp_itemsize;  For allocation */

	/* Methods to implement standard operations */

	NULL,						/* destructor tp_dealloc; */
	NULL,                       /* printfunc tp_print; */
	NULL,     /* getattrfunc tp_getattr; */
	NULL,     /* setattrfunc tp_setattr; */
	NULL,                       /* cmpfunc tp_compare; */
	( reprfunc ) IDGroup_Iter_repr,     /* reprfunc tp_repr; */

	/* Method suites for standard classes */

	NULL,                       /* PyNumberMethods *tp_as_number; */
	NULL,						/* PySequenceMethods *tp_as_sequence; */
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
	Py_TPFLAGS_DEFAULT,         /* long tp_flags; */

	NULL,                       /*  char *tp_doc;  Documentation string */
  /*** Assigned meaning in release 2.0 ***/
	/* call function for all accessible objects */
	NULL,                       /* traverseproc tp_traverse; */

	/* delete references to contained objects */
	NULL,                       /* inquiry tp_clear; */

  /***  Assigned meaning in release 2.1 ***/
  /*** rich comparisons ***/
	NULL,                       /* richcmpfunc tp_richcompare; */

  /***  weak reference enabler ***/
	0,                          /* long tp_weaklistoffset; */

  /*** Added in release 2.2 ***/
	/*   Iterators */
	IDGroup_Iter_iterself,              /* getiterfunc tp_iter; */
	(iternextfunc) BPy_Group_Iter_Next, /* iternextfunc tp_iternext; */
};

void IDProp_Init_Types(void)
{
	PyType_Ready( &IDGroup_Type );
	PyType_Ready( &IDGroup_Iter_Type );
	PyType_Ready( &IDArray_Type );
}
