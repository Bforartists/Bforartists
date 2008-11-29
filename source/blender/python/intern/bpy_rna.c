/**
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
 * Contributor(s): Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "bpy_rna.h"
#include "bpy_compat.h"

#include "MEM_guardedalloc.h"
#include "BKE_global.h" /* evil G.* */


static int pyrna_struct_compare( BPy_StructRNA * a, BPy_StructRNA * b )
{ 
	return (a->ptr.data==b->ptr.data) ? 0 : -1;
}

static int pyrna_prop_compare( BPy_PropertyRNA * a, BPy_PropertyRNA * b )
{
	return (a->prop==b->prop && a->ptr.data==b->ptr.data ) ? 0 : -1;
}

/*----------------------repr--------------------------------------------*/
static PyObject *pyrna_struct_repr( BPy_StructRNA * self )
{
	return PyUnicode_FromFormat( "[BPy_StructRNA \"%s\"]", RNA_struct_identifier(&self->ptr));
}

static PyObject *pyrna_prop_repr( BPy_PropertyRNA * self )
{
	return PyUnicode_FromFormat( "[BPy_PropertyRNA \"%s\" -> \"%s\" ]", RNA_struct_identifier(&self->ptr), RNA_property_identifier(&self->ptr, self->prop) );
}

static PyObject * pyrna_prop_to_py(PointerRNA *ptr, PropertyRNA *prop)
{
	PyObject *ret;
	int type = RNA_property_type(ptr, prop);
	int len = RNA_property_array_length(ptr, prop);
	/* resolve path */
	
	if (len > 0) {
		/* resolve the array from a new pytype */
		return pyrna_prop_CreatePyObject(ptr, prop);
	}
	
	/* see if we can coorce into a python type - PropertyType */
	switch (type) {
	case PROP_BOOLEAN:
		ret = PyBool_FromLong( RNA_property_boolean_get(ptr, prop) );
		break;
	case PROP_INT:
		ret = PyLong_FromSize_t( (size_t)RNA_property_int_get(ptr, prop) );
		break;
	case PROP_FLOAT:
		ret = PyFloat_FromDouble( RNA_property_float_get(ptr, prop) );
		break;
	case PROP_STRING:
	{
		char *buf;
		buf = RNA_property_string_get_alloc(ptr, prop, NULL, -1);
		ret = PyUnicode_FromString( buf );
		MEM_freeN(buf);
		break;
	}
	case PROP_ENUM:
	{		
		const EnumPropertyItem *item;
		int totitem;
		
		RNA_property_enum_items(ptr, prop, &item, &totitem);
		ret = PyUnicode_FromString( item->identifier );
		
		if (ret==NULL) {
			PyErr_SetString(PyExc_AttributeError, "enum not found");
		}
		
		break;
	}
	case PROP_POINTER:
	{
		PointerRNA newptr;
		RNA_property_pointer_get(ptr, prop, &newptr);
		if (newptr.data) {
			ret = pyrna_struct_CreatePyObject(&newptr);
		} else {
			ret = Py_None;
			Py_INCREF(ret);
		}
		break;
	}
	case PROP_COLLECTION:
		ret = pyrna_prop_CreatePyObject(ptr, prop);
		break;
	default:
		printf("Warning, unsupported type %d\n", type);
		ret = NULL;
		break;
	}
	
	return ret;
}

static PyObject * pyrna_prop_to_py_index(PointerRNA *ptr, PropertyRNA *prop, int index)
{
	PyObject *ret;
	int type = RNA_property_type(ptr, prop);
	
	/* resolve path */
	
	/* see if we can coorce into a python type - PropertyType */
	switch (type) {
	case PROP_BOOLEAN:
		ret = PyBool_FromLong( RNA_property_boolean_get_array(ptr, prop, index) );
		break;
	case PROP_INT:
		ret = PyLong_FromSize_t( (size_t)RNA_property_int_get_array(ptr, prop, index) );
		break;
	case PROP_FLOAT:
		ret = PyFloat_FromDouble( RNA_property_float_get_array(ptr, prop, index) );
		break;
	default:
		PyErr_SetString(PyExc_AttributeError, "not an array type");
		ret = NULL;
		break;
	}
	
	return ret;
}


//---------------sequence-------------------------------------------
static Py_ssize_t pyrna_prop_len( BPy_PropertyRNA * self )
{
	Py_ssize_t len;
	
	if (RNA_property_type(&self->ptr, self->prop) == PROP_COLLECTION) {
		len = RNA_property_collection_length(&self->ptr, self->prop);
	} else {
		len = RNA_property_array_length(&self->ptr, self->prop);
		
		if (len==0) { /* not an array*/
			PyErr_SetString(PyExc_AttributeError, "len() only available for collection RNA types");
			return -1;
		}
	}
	
	return len;
}

static PyObject *pyrna_prop_subscript( BPy_PropertyRNA * self, PyObject *key )
{
	PyObject *ret;
	PointerRNA newptr;
	int keynum;
	char *keyname = NULL;
	
	if (PyUnicode_Check(key)) {
		keyname = _PyUnicode_AsString(key);
	} else if (PyLong_Check(key)) {
		keynum = PyLong_AsSsize_t(key);
	} else {
		PyErr_SetString(PyExc_AttributeError, "invalid key, key must be a string or an int");
		return NULL;
	}
	
	if (RNA_property_type(&self->ptr, self->prop) == PROP_COLLECTION) {
		int ok;
		if (keyname)	ok = RNA_property_collection_lookup_string(&self->ptr, self->prop, keyname, &newptr);
		else			ok = RNA_property_collection_lookup_int(&self->ptr, self->prop, keynum, &newptr);
		
		if (ok) {
			ret = pyrna_struct_CreatePyObject(&newptr);
		} else {
			PyErr_SetString(PyExc_AttributeError, "out of range");
			ret = NULL;
		}
		
	} else if (keyname) {
		PyErr_SetString(PyExc_AttributeError, "string keys are only supported for collections");
		ret = NULL;
	} else {
		int len = RNA_property_array_length(&self->ptr, self->prop);
		
		if (len==0) { /* not an array*/
			PyErr_Format(PyExc_AttributeError, "not an array or collection %d", keynum);
			ret = NULL;
		}
		
		if (keynum >= len){
			PyErr_SetString(PyExc_AttributeError, "index out of range");
			ret = NULL;
		} else { /* not an array*/
			ret = pyrna_prop_to_py_index(&self->ptr, self->prop, keynum);
		}
	}
	
	return ret;
}

static PyMappingMethods pyrna_prop_as_mapping = {
	( inquiry ) pyrna_prop_len,	/* mp_length */
	( binaryfunc ) pyrna_prop_subscript,	/* mp_subscript */
	( objobjargproc ) 0,	/* mp_ass_subscript */
};

//---------------getattr--------------------------------------------
static PyObject *pyrna_struct_getattr( BPy_StructRNA * self, char *name )
{
	PyObject *ret;
	PropertyRNA *prop;
	
	
	
	if( strcmp( name, "__members__" ) == 0 ) {
		PyObject *item;
		
		PropertyRNA *iterprop;
		CollectionPropertyIterator iter;
		
		ret = PyList_New(0);
	
		iterprop= RNA_struct_iterator_property(&self->ptr);
		RNA_property_collection_begin(&self->ptr, iterprop, &iter);
		
		
		for(; iter.valid; RNA_property_collection_next(&iter)) {
			item = PyUnicode_FromString( RNA_property_identifier(&iter.ptr, iter.ptr.data) ); /* iter.ptr.data is just a prop */
			PyList_Append(ret, item);
			Py_DECREF(item);
		}

		RNA_property_collection_end(&iter);
	} else {
		prop = RNA_struct_find_property(&self->ptr, name);
		
		if (prop==NULL) {
			PyErr_Format( PyExc_AttributeError, "Attribute \"%s\" not found", name);
			ret = NULL;
		} else {
			ret = pyrna_prop_to_py(&self->ptr, prop);
			
			if (ret==NULL) {
				PyErr_Format( PyExc_AttributeError, "Attribute \"%s\" could not be converted to a python type", name);
			}
		}
	}
	

	
	return ret;
}

PyObject *pyrna_prop_keys(BPy_PropertyRNA *self)
{
	PyObject *ret;
	if (RNA_property_type(&self->ptr, self->prop) != PROP_COLLECTION) {
		PyErr_SetString( PyExc_TypeError, "keys() is only valid for collection types" );
		ret = NULL;
	} else {
		PyObject *item;
		CollectionPropertyIterator iter;
		PropertyRNA *nameprop;
		char name[256], *nameptr;

		ret = PyList_New(0);
		
		RNA_property_collection_begin(&self->ptr, self->prop, &iter);
		for(; iter.valid; RNA_property_collection_next(&iter)) {
			nameprop= RNA_struct_name_property(&iter.ptr);
			if(iter.ptr.data && nameprop) {
				nameptr= RNA_property_string_get_alloc(&iter.ptr, nameprop, name, sizeof(name));				
				
				/* add to python list */
				item = PyUnicode_FromString( nameptr );
				PyList_Append(ret, item);
				Py_DECREF(item);
				/* done */
				
				if (name != nameptr)
					MEM_freeN(nameptr);
			}
		}
		RNA_property_collection_end(&iter);
	}
	
	return ret;
}

PyObject *pyrna_prop_items(BPy_PropertyRNA *self)
{
	PyObject *ret;
	if (RNA_property_type(&self->ptr, self->prop) != PROP_COLLECTION) {
		PyErr_SetString( PyExc_TypeError, "keys() is only valid for collection types" );
		ret = NULL;
	} else {
		PyObject *item;
		CollectionPropertyIterator iter;
		PropertyRNA *nameprop;
		char name[256], *nameptr;

		ret = PyList_New(0);
		
		RNA_property_collection_begin(&self->ptr, self->prop, &iter);
		for(; iter.valid; RNA_property_collection_next(&iter)) {
			nameprop= RNA_struct_name_property(&iter.ptr);
			if(iter.ptr.data && nameprop) {
				nameptr= RNA_property_string_get_alloc(&iter.ptr, nameprop, name, sizeof(name));
				
				/* add to python list */
				item = Py_BuildValue("(NN)", PyUnicode_FromString( nameptr ), pyrna_struct_CreatePyObject(&iter.ptr));
				PyList_Append(ret, item);
				Py_DECREF(item);
				/* done */
				
				if (name != nameptr)
					MEM_freeN(nameptr);
			}
		}
		RNA_property_collection_end(&iter);
	}
	
	return ret;
}


PyObject *pyrna_prop_values(BPy_PropertyRNA *self)
{
	PyObject *ret;
	if (RNA_property_type(&self->ptr, self->prop) != PROP_COLLECTION) {
		PyErr_SetString( PyExc_TypeError, "keys() is only valid for collection types" );
		ret = NULL;
	} else {
		PyObject *item;
		CollectionPropertyIterator iter;
		PropertyRNA *nameprop;
		
		ret = PyList_New(0);
		
		RNA_property_collection_begin(&self->ptr, self->prop, &iter);
		for(; iter.valid; RNA_property_collection_next(&iter)) {
			nameprop= RNA_struct_name_property(&iter.ptr);
			if(iter.ptr.data && nameprop) {
				
				/* add to python list */
				item = pyrna_struct_CreatePyObject(&iter.ptr);
				PyList_Append(ret, item);
				Py_DECREF(item);
				/* done */
				
			}
		}
		RNA_property_collection_end(&iter);
	}
	
	return ret;
}


static struct PyMethodDef pyrna_prop_methods[] = {
	{"keys", (PyCFunction)pyrna_prop_keys, METH_NOARGS, ""},
	{"items", (PyCFunction)pyrna_prop_items, METH_NOARGS, ""},
	{"values", (PyCFunction)pyrna_prop_values, METH_NOARGS, ""},
	{NULL, NULL, 0, NULL}
};

/*-----------------------BPy_StructRNA method def------------------------------*/
PyTypeObject pyrna_struct_Type = {
#if (PY_VERSION_HEX >= 0x02060000)
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
#else
	/* python 2.5 and below */
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
#endif
	"StructRNA",			/* tp_name */
	sizeof( BPy_StructRNA ),	/* tp_basicsize */
	0,			/* tp_itemsize */
	/* methods */
	NULL,						/* tp_dealloc */
	NULL,                       /* printfunc tp_print; */
	( getattrfunc ) pyrna_struct_getattr,			/* getattrfunc tp_getattr; */
	NULL,                       /* setattrfunc tp_setattr; */
	( cmpfunc ) pyrna_struct_compare,	/* tp_compare */
	( reprfunc ) pyrna_struct_repr,	/* tp_repr */

	/* Method suites for standard classes */

	NULL,                       /* PyNumberMethods *tp_as_number; */
	NULL,						/* PySequenceMethods *tp_as_sequence; */
	NULL,						/* PyMappingMethods *tp_as_mapping; */

	/* More standard operations (here for binary compatibility) */

	NULL,						/* hashfunc tp_hash; */
	NULL,                       /* ternaryfunc tp_call; */
	NULL,                       /* reprfunc tp_str; */
	NULL,                       /* getattrofunc tp_getattro; */
	NULL,                       /* setattrofunc tp_setattro; */

	/* Functions to access object as input/output buffer */
	NULL,                       /* PyBufferProcs *tp_as_buffer; */

  /*** Flags to define presence of optional/expanded features ***/
	Py_TPFLAGS_DEFAULT,         /* long tp_flags; */

	NULL,						/*  char *tp_doc;  Documentation string */
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
	NULL,						/* struct PyMethodDef *tp_methods; */
	NULL,                       /* struct PyMemberDef *tp_members; */
	NULL,      					/* struct PyGetSetDef *tp_getset; */
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

/*-----------------------BPy_PropertyRNA method def------------------------------*/
PyTypeObject pyrna_prop_Type = {
#if (PY_VERSION_HEX >= 0x02060000)
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
#else
	/* python 2.5 and below */
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
#endif
	
	"PropertyRNA",		/* tp_name */
	sizeof( BPy_PropertyRNA ),			/* tp_basicsize */
	0,			/* tp_itemsize */
	/* methods */
	NULL,						/* tp_dealloc */
	NULL,                       /* printfunc tp_print; */
	NULL,						/* getattrfunc tp_getattr; */ /* NOTE - adding getattr here will override  pyrna_prop_methods*/
	NULL,                       /* setattrfunc tp_setattr; */
	( cmpfunc ) pyrna_prop_compare,	/* tp_compare */
	( reprfunc ) pyrna_prop_repr,	/* tp_repr */

	/* Method suites for standard classes */

	NULL,                       /* PyNumberMethods *tp_as_number; */
	NULL,						/* PySequenceMethods *tp_as_sequence; */
	&pyrna_prop_as_mapping,		/* PyMappingMethods *tp_as_mapping; */

	/* More standard operations (here for binary compatibility) */

	NULL,						/* hashfunc tp_hash; */
	NULL,                       /* ternaryfunc tp_call; */
	NULL,                       /* reprfunc tp_str; */
	NULL,                       /* getattrofunc tp_getattro; */
	NULL,                       /* setattrofunc tp_setattro; */

	/* Functions to access object as input/output buffer */
	NULL,                       /* PyBufferProcs *tp_as_buffer; */

  /*** Flags to define presence of optional/expanded features ***/
	Py_TPFLAGS_DEFAULT,         /* long tp_flags; */

	NULL,						/*  char *tp_doc;  Documentation string */
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
	pyrna_prop_methods,			/* struct PyMethodDef *tp_methods; */
	NULL,                       /* struct PyMemberDef *tp_members; */
	NULL,      					/* struct PyGetSetDef *tp_getset; */
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

/*-----------------------CreatePyObject---------------------------------*/
PyObject *pyrna_struct_CreatePyObject( PointerRNA *ptr )
{
	BPy_StructRNA *pyrna;

	pyrna = ( BPy_StructRNA * ) PyObject_NEW( BPy_StructRNA, &pyrna_struct_Type );

	if( !pyrna ) {
		PyErr_SetString( PyExc_MemoryError, "couldn't create BPy_StructRNA object" );
		return NULL;
	}
	
	pyrna->ptr = *ptr;
	
	return ( PyObject * ) pyrna;
}

PyObject *pyrna_prop_CreatePyObject( PointerRNA *ptr, PropertyRNA *prop )
{
	BPy_PropertyRNA *pyrna;

	pyrna = ( BPy_PropertyRNA * ) PyObject_NEW( BPy_PropertyRNA, &pyrna_prop_Type );

	if( !pyrna ) {
		PyErr_SetString( PyExc_MemoryError, "couldn't create BPy_rna object" );
		return NULL;
	}
	
	pyrna->ptr = *ptr;
	pyrna->prop = prop;
	
	/* TODO - iterator? */
		
	return ( PyObject * ) pyrna;
}


PyObject *BPY_rna_module( void )
{
	PointerRNA ptr;
	
	if( PyType_Ready( &pyrna_struct_Type ) < 0 )
		return NULL;
	
	if( PyType_Ready( &pyrna_prop_Type ) < 0 )
		return NULL;
	
	/* for now, return the base RNA type rather then a real module */
	RNA_main_pointer_create(G.main, &ptr);
	
	//submodule = Py_InitModule3( "rna", M_rna_methods, "rna module" );
	return pyrna_struct_CreatePyObject(&ptr);
}
