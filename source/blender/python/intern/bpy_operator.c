
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

#include "bpy_operator.h"
#include "bpy_opwrapper.h"
#include "bpy_rna.h" /* for setting arg props only - pyrna_py_to_prop() */
#include "bpy_compat.h"

//#include "blendef.h"
#include "BLI_dynstr.h"

#include "WM_api.h"
#include "WM_types.h"

#include "MEM_guardedalloc.h"
#include "BKE_idprop.h"

extern ListBase global_ops; /* evil, temp use */

/* floats bigger then this are displayed as inf in the docstrings */
#define MAXFLOAT_DOC 10000000

#if 0
void PyObSpit(char *name, PyObject *var) {
	fprintf(stderr, "<%s> : ", name);
	if (var==NULL) {
		fprintf(stderr, "<NIL>");
	}
	else {
		PyObject_Print(var, stderr, 0);
	}
	fprintf(stderr, "\n");
}
#endif


static int pyop_func_compare( BPy_OperatorFunc * a, BPy_OperatorFunc * b )
{
	return (strcmp(a->name, b->name)==0) ? 0 : -1;
}

/*----------------------repr--------------------------------------------*/
static PyObject *pyop_base_repr( BPy_OperatorBase * self )
{
	return PyUnicode_FromFormat( "[BPy_OperatorBase]");
}

static PyObject *pyop_func_repr( BPy_OperatorFunc * self )
{
	return PyUnicode_FromFormat( "[BPy_OperatorFunc \"%s\"]", self->name);
}


//---------------getattr--------------------------------------------
static PyObject *pyop_base_getattro( BPy_OperatorBase * self, PyObject *pyname )
{
	char *name = _PyUnicode_AsString(pyname);
	PyObject *ret;
	wmOperatorType *ot;

	if( strcmp( name, "__members__" ) == 0 ) {
		PyObject *item;
		ret = PyList_New(2);
		
		PyList_SET_ITEM(ret, 0, PyUnicode_FromString("add"));
		PyList_SET_ITEM(ret, 1, PyUnicode_FromString("remove"));

		for(ot= WM_operatortype_first(); ot; ot= ot->next) {
			item = PyUnicode_FromString( ot->idname );
			PyList_Append(ret, item);
			Py_DECREF(item);
		}
	}
	else if ( strcmp( name, "add" ) == 0 ) {
		ret= PYOP_wrap_add_func();
	}
	else if ( strcmp( name, "remove" ) == 0 ) {
		ret= PYOP_wrap_remove_func();
	}
	else {
		ot = WM_operatortype_find(name);

		if (ot) {
			ret= pyop_func_CreatePyObject(self->C, name);
		}
		else {
			PyErr_Format( PyExc_AttributeError, "Operator \"%s\" not found", name);
			ret= NULL;
		}
	}
	
	return ret;
}

static PyObject * pyop_func_call(BPy_OperatorFunc * self, PyObject *args, PyObject *kw)
{
	IDProperty *properties = NULL;
	wmOperatorType *ot;

	int error_val = 0;
	int totkw;
	const char *arg_name= NULL;
	PyObject *item;
	
	PointerRNA ptr;
	PropertyRNA *prop, *iterprop;
	CollectionPropertyIterator iter;

	if (PyTuple_Size(args)) {
		PyErr_SetString( PyExc_AttributeError, "All operator args must be keywords");
		return NULL;
	}

	ot= WM_operatortype_find(self->name);
	if (ot == NULL) {
		PyErr_SetString( PyExc_SystemError, "Operator could not be found");
		return NULL;
	}
	
	RNA_pointer_create(NULL, NULL, ot->srna, &properties, &ptr);


	iterprop= RNA_struct_iterator_property(&ptr);
	RNA_property_collection_begin(&ptr, iterprop, &iter);

	totkw = kw ? PyDict_Size(kw):0;

	for(; iter.valid; RNA_property_collection_next(&iter)) {
		prop= iter.ptr.data;

		arg_name= RNA_property_identifier(&iter.ptr, prop);

		if (strcmp(arg_name, "rna_type")==0) continue;

		if (kw==NULL) {
			PyErr_Format( PyExc_AttributeError, "no args, expected \"%s\"", arg_name ? arg_name : "<UNKNOWN>");
			error_val= 1;
			break;
		}
		
		item= PyDict_GetItemString(kw, arg_name);

		if (item == NULL) {
			PyErr_Format( PyExc_AttributeError, "argument \"%s\" missing", arg_name ? arg_name : "<UNKNOWN>");
			error_val = 1; /* pyrna_py_to_prop sets the error */
			break;
		}
		
		if (pyrna_py_to_prop(&ptr, prop, item)) {
			error_val= 1;
			break;
		}

		totkw--;
	}

	RNA_property_collection_end(&iter);

	if (error_val==0 && totkw > 0) { /* some keywords were given that were not used :/ */
		PyObject *key, *value;
		Py_ssize_t pos = 0;

		while (PyDict_Next(kw, &pos, &key, &value)) {
			arg_name= _PyUnicode_AsString(key);
			if (RNA_struct_find_property(&ptr, arg_name) == NULL) break;
			arg_name= NULL;
		}

		PyErr_Format( PyExc_AttributeError, "argument \"%s\" unrecognized", arg_name ? arg_name : "<UNKNOWN>");
		error_val = 1;
	}

	if (error_val==0) {
		WM_operator_name_call(self->C, self->name, WM_OP_EXEC_DEFAULT, properties);
	}

	if (properties) {
		IDP_FreeProperty(properties);
		MEM_freeN(properties);
	}

	if (error_val) {
		return NULL;
	}

	Py_RETURN_NONE;
}

/*-----------------------BPy_OperatorBase method def------------------------------*/
PyTypeObject pyop_base_Type = {
#if (PY_VERSION_HEX >= 0x02060000)
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
#else
	/* python 2.5 and below */
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
#endif

	"Operator",		/* tp_name */
	sizeof( BPy_OperatorBase ),			/* tp_basicsize */
	0,			/* tp_itemsize */
	/* methods */
	NULL,						/* tp_dealloc */
	NULL,                       /* printfunc tp_print; */
	NULL,						/* getattrfunc tp_getattr; */
	NULL,                       /* setattrfunc tp_setattr; */
	NULL,						/* tp_compare */
	( reprfunc ) pyop_base_repr,	/* tp_repr */

	/* Method suites for standard classes */

	NULL,                       /* PyNumberMethods *tp_as_number; */
	NULL,						/* PySequenceMethods *tp_as_sequence; */
	NULL,						/* PyMappingMethods *tp_as_mapping; */

	/* More standard operations (here for binary compatibility) */

	NULL,						/* hashfunc tp_hash; */
	NULL,                       /* ternaryfunc tp_call; */
	NULL,                       /* reprfunc tp_str; */
	( getattrofunc )pyop_base_getattro, /*PyObject_GenericGetAttr - MINGW Complains, assign later */	/* getattrofunc tp_getattro; */
	NULL, /*PyObject_GenericSetAttr - MINGW Complains, assign later */	/* setattrofunc tp_setattro; */

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
	NULL,						/* getiterfunc tp_iter; */
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
	NULL,						/* newfunc tp_new; */
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

/*-----------------------BPy_OperatorBase method def------------------------------*/
PyTypeObject pyop_func_Type = {
#if (PY_VERSION_HEX >= 0x02060000)
	PyVarObject_HEAD_INIT(&PyType_Type, 0)
#else
	/* python 2.5 and below */
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
#endif

	"OperatorFunc",		/* tp_name */
	sizeof( BPy_OperatorFunc ),			/* tp_basicsize */
	0,			/* tp_itemsize */
	/* methods */
	NULL,						/* tp_dealloc */
	NULL,                       /* printfunc tp_print; */
	NULL,						/* getattrfunc tp_getattr; */
	NULL,                       /* setattrfunc tp_setattr; */
	( cmpfunc ) pyop_func_compare,	/* tp_compare */
	( reprfunc ) pyop_func_repr,	/* tp_repr */

	/* Method suites for standard classes */

	NULL,                       /* PyNumberMethods *tp_as_number; */
	NULL,						/* PySequenceMethods *tp_as_sequence; */
	NULL,						/* PyMappingMethods *tp_as_mapping; */

	/* More standard operations (here for binary compatibility) */

	NULL,						/* hashfunc tp_hash; */
	(ternaryfunc)pyop_func_call,                       /* ternaryfunc tp_call; */
	NULL,                       /* reprfunc tp_str; */
	NULL, /*PyObject_GenericGetAttr - MINGW Complains, assign later */	/* getattrofunc tp_getattro; */
	NULL, /*PyObject_GenericSetAttr - MINGW Complains, assign later */	/* setattrofunc tp_setattro; */

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
	NULL,						/* getiterfunc tp_iter; */
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
	NULL,						/* newfunc tp_new; */
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

PyObject *pyop_base_CreatePyObject( bContext *C )
{
	BPy_OperatorBase *pyop;

	pyop = ( BPy_OperatorBase * ) PyObject_NEW( BPy_OperatorBase, &pyop_base_Type );

	if( !pyop ) {
		PyErr_SetString( PyExc_MemoryError, "couldn't create BPy_OperatorBase object" );
		return NULL;
	}

	pyop->C = C; /* TODO - copy this? */

	return ( PyObject * ) pyop;
}

PyObject *pyop_func_CreatePyObject( bContext *C, char *name )
{
	BPy_OperatorFunc *pyop;

	pyop = ( BPy_OperatorFunc * ) PyObject_NEW( BPy_OperatorFunc, &pyop_func_Type );

	if( !pyop ) {
		PyErr_SetString( PyExc_MemoryError, "couldn't create BPy_OperatorFunc object" );
		return NULL;
	}

	strcpy(pyop->name, name);
	pyop->C= C; /* TODO - how should contexts be dealt with? */

	return ( PyObject * ) pyop;
}

PyObject *BPY_operator_module( bContext *C )
{
	if( PyType_Ready( &pyop_base_Type ) < 0 )
		return NULL;

	if( PyType_Ready( &pyop_func_Type ) < 0 )
		return NULL;

	//submodule = Py_InitModule3( "operator", M_rna_methods, "rna module" );
	return pyop_base_CreatePyObject(C);
}



