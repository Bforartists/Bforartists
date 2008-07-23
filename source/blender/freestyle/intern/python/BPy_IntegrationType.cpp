#include "BPy_IntegrationType.h"

#include "BPy_Convert.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

/*---------------  Python API function prototypes for IntegrationType instance  -----------*/
static int IntegrationType___init__(BPy_IntegrationType *self, PyObject *args, PyObject *kwds);

/*----------------------IntegrationType instance definitions ----------------------------*/
static PyMethodDef BPy_IntegrationType_methods[] = {
	{NULL, NULL, 0, NULL}
};

/*-----------------------BPy_IntegrationType type definition ------------------------------*/

PyTypeObject IntegrationType_Type = {
	PyObject_HEAD_INIT( NULL ) 
	0,							/* ob_size */
	"IntegrationType",				/* tp_name */
	sizeof( BPy_IntegrationType ),	/* tp_basicsize */
	0,							/* tp_itemsize */
	
	/* methods */
	NULL,	/* tp_dealloc */
	NULL,                       				/* printfunc tp_print; */
	NULL,                       				/* getattrfunc tp_getattr; */
	NULL,                       				/* setattrfunc tp_setattr; */
	NULL,										/* tp_compare */
	NULL,					/* tp_repr */

	/* Method suites for standard classes */

	NULL,                       /* PyNumberMethods *tp_as_number; */
	NULL,                       /* PySequenceMethods *tp_as_sequence; */
	NULL,                       /* PyMappingMethods *tp_as_mapping; */

	/* More standard operations (here for binary compatibility) */

	NULL,						/* hashfunc tp_hash; */
	NULL,                       /* ternaryfunc tp_call; */
	NULL,                       /* reprfunc tp_str; */
	NULL,                       /* getattrofunc tp_getattro; */
	NULL,                       /* setattrofunc tp_setattro; */

	/* Functions to access object as input/output buffer */
	NULL,                       /* PyBufferProcs *tp_as_buffer; */

  /*** Flags to define presence of optional/expanded features ***/
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, 		/* long tp_flags; */

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
	BPy_IntegrationType_methods,	/* struct PyMethodDef *tp_methods; */
	NULL,                       	/* struct PyMemberDef *tp_members; */
	NULL,         					/* struct PyGetSetDef *tp_getset; */
	&PyInt_Type,							/* struct _typeobject *tp_base; */
	NULL,							/* PyObject *tp_dict; */
	NULL,							/* descrgetfunc tp_descr_get; */
	NULL,							/* descrsetfunc tp_descr_set; */
	0,                          	/* long tp_dictoffset; */
	(initproc)IntegrationType___init__,                       	/* initproc tp_init; */
	NULL,							/* allocfunc tp_alloc; */
	PyType_GenericNew,			/* newfunc tp_new; */
	
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

//-------------------MODULE INITIALIZATION--------------------------------
PyMODINIT_FUNC IntegrationType_Init( PyObject *module )
{	
	PyObject *tmp;
	
	if( module == NULL )
		return;

	if( PyType_Ready( &IntegrationType_Type ) < 0 )
		return;
	Py_INCREF( &IntegrationType_Type );
	PyModule_AddObject(module, "IntegrationType", (PyObject *)&IntegrationType_Type);

	tmp = PyInt_FromLong( MEAN );
	PyDict_SetItemString( IntegrationType_Type.tp_dict, "MEAN", tmp);
	Py_DECREF(tmp);
	
	tmp = PyInt_FromLong( MIN );
	PyDict_SetItemString( IntegrationType_Type.tp_dict, "MIN", tmp);
	Py_DECREF(tmp);
	
	tmp = PyInt_FromLong( MAX );
	PyDict_SetItemString( IntegrationType_Type.tp_dict, "MAX", tmp);
	Py_DECREF(tmp);
	
	tmp = PyInt_FromLong( FIRST );
	PyDict_SetItemString( IntegrationType_Type.tp_dict, "FIRST", tmp);
	Py_DECREF(tmp);
	
	tmp = PyInt_FromLong( LAST );
	PyDict_SetItemString( IntegrationType_Type.tp_dict, "LAST", tmp);
	Py_DECREF(tmp);
	
	
}

int IntegrationType___init__(BPy_IntegrationType *self, PyObject *args, PyObject *kwds)
{
    if (PyInt_Type.tp_init((PyObject *)self, args, kwds) < 0)
        return -1;
	
	return 0;
}

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

