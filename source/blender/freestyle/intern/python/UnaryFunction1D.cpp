#include "UnaryFunction1D.h"

#include "Convert.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

/*---------------  Python API function prototypes for UnaryFunction1D instance  -----------*/
static int UnaryFunction1D___init__(BPy_UnaryFunction1D *self, PyObject *args, PyObject *kwds);
static void UnaryFunction1D___dealloc__(BPy_UnaryFunction1D *self);
static PyObject * UnaryFunction1D___repr__(BPy_UnaryFunction1D *self);

static PyObject * UnaryFunction1D_getName( BPy_UnaryFunction1D *self, PyObject *args);
static PyObject * UnaryFunction1D___call__( BPy_UnaryFunction1D *self, PyObject *args);

/*----------------------UnaryFunction1D instance definitions ----------------------------*/
static PyMethodDef BPy_UnaryFunction1D_methods[] = {
	{"getName", ( PyCFunction ) UnaryFunction1D_getName, METH_NOARGS, ""},
	{"__call__", ( PyCFunction ) UnaryFunction1D___call__, METH_VARARGS, "" },
	{NULL, NULL, 0, NULL}
};

/*-----------------------BPy_UnaryFunction1D type definition ------------------------------*/

PyTypeObject UnaryFunction1D_Type = {
	PyObject_HEAD_INIT( NULL ) 
	0,							/* ob_size */
	"UnaryFunction1D",				/* tp_name */
	sizeof( BPy_UnaryFunction1D ),	/* tp_basicsize */
	0,							/* tp_itemsize */
	
	/* methods */
	(destructor)UnaryFunction1D___dealloc__,	/* tp_dealloc */
	NULL,                       				/* printfunc tp_print; */
	NULL,                       				/* getattrfunc tp_getattr; */
	NULL,                       				/* setattrfunc tp_setattr; */
	NULL,										/* tp_compare */
	(reprfunc)UnaryFunction1D___repr__,					/* tp_repr */

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
	NULL,                          /* long tp_weaklistoffset; */

  /*** Added in release 2.2 ***/
	/*   Iterators */
	NULL,                       /* getiterfunc tp_iter; */
	NULL,                       /* iternextfunc tp_iternext; */

  /*** Attribute descriptor and subclassing stuff ***/
	BPy_UnaryFunction1D_methods,	/* struct PyMethodDef *tp_methods; */
	NULL,                       	/* struct PyMemberDef *tp_members; */
	NULL,         					/* struct PyGetSetDef *tp_getset; */
	NULL,							/* struct _typeobject *tp_base; */
	NULL,							/* PyObject *tp_dict; */
	NULL,							/* descrgetfunc tp_descr_get; */
	NULL,							/* descrsetfunc tp_descr_set; */
	NULL,                          	/* long tp_dictoffset; */
	(initproc)UnaryFunction1D___init__, /* initproc tp_init; */
	NULL,							/* allocfunc tp_alloc; */
	PyType_GenericNew,		/* newfunc tp_new; */
	
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
PyMODINIT_FUNC UnaryFunction1D_Init( PyObject *module )
{
	if( module == NULL )
		return;

	if( PyType_Ready( &UnaryFunction1D_Type ) < 0 )
		return;
	Py_INCREF( &UnaryFunction1D_Type );
	PyModule_AddObject(module, "UnaryFunction1D", (PyObject *)&UnaryFunction1D_Type);
}

//------------------------INSTANCE METHODS ----------------------------------

int UnaryFunction1D___init__(BPy_UnaryFunction1D *self, PyObject *args, PyObject *kwds)
{
	return 0;
}

void UnaryFunction1D___dealloc__(BPy_UnaryFunction1D* self)
{
	//delete self->uf1D;
    self->ob_type->tp_free((PyObject*)self);
}


PyObject * UnaryFunction1D___repr__(BPy_UnaryFunction1D* self)
{
    return PyString_FromFormat("type: %s - address: %p", ((UnaryFunction1D<void> *) self->uf1D)->getName().c_str(), self->uf1D );
}


PyObject * UnaryFunction1D_getName( BPy_UnaryFunction1D *self, PyObject *args)
{
	return PyString_FromString( ((UnaryFunction1D<void> *) self->uf1D)->getName().c_str() );
}

PyObject * UnaryFunction1D___call__( BPy_UnaryFunction1D *self, PyObject *args)
{
	PyObject *l;

	if( !PyArg_ParseTuple(args, "O", &l) ) {
		cout << "ERROR: UnaryFunction1D___call__ " << endl;		
		return NULL;
	}
	
	// pb: operator() is called on Interface0DIterator while we have a list
	// solutions:
	// 1)reconvert back to iterator ?
	// 2) adapt interface0d to have t(), u() functions
	
	// b = self->bp0D->operator()( *(obj1->uf0D) );
	// return PyBool_from_bool( b );
	
	Py_RETURN_NONE;
}

// void 	setIntegrationType (IntegrationType integration)
// IntegrationType 	getIntegrationType () const

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
