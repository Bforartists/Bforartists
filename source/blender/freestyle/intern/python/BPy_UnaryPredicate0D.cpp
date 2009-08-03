#include "BPy_UnaryPredicate0D.h"

#include "BPy_Convert.h"
#include "Iterator/BPy_Interface0DIterator.h"
#include "UnaryPredicate0D/BPy_FalseUP0D.h"
#include "UnaryPredicate0D/BPy_TrueUP0D.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

/*---------------  Python API function prototypes for UnaryPredicate0D instance  -----------*/
static int UnaryPredicate0D___init__(BPy_UnaryPredicate0D *self, PyObject *args, PyObject *kwds);
static void UnaryPredicate0D___dealloc__(BPy_UnaryPredicate0D *self);
static PyObject * UnaryPredicate0D___repr__(BPy_UnaryPredicate0D *self);

static PyObject * UnaryPredicate0D_getName( BPy_UnaryPredicate0D *self );
static PyObject * UnaryPredicate0D___call__( BPy_UnaryPredicate0D *self, PyObject *args, PyObject *kwds);

/*----------------------UnaryPredicate0D instance definitions ----------------------------*/
static PyMethodDef BPy_UnaryPredicate0D_methods[] = {
	{"getName", ( PyCFunction ) UnaryPredicate0D_getName, METH_NOARGS, "Returns the string of the name of the UnaryPredicate0D."},
	{NULL, NULL, 0, NULL}
};

/*-----------------------BPy_UnaryPredicate0D type definition ------------------------------*/

PyTypeObject UnaryPredicate0D_Type = {
	PyObject_HEAD_INIT( NULL ) 
	0,							/* ob_size */
	"UnaryPredicate0D",				/* tp_name */
	sizeof( BPy_UnaryPredicate0D ),	/* tp_basicsize */
	0,							/* tp_itemsize */
	
	/* methods */
	(destructor)UnaryPredicate0D___dealloc__,	/* tp_dealloc */
	NULL,                       				/* printfunc tp_print; */
	NULL,                       				/* getattrfunc tp_getattr; */
	NULL,                       				/* setattrfunc tp_setattr; */
	NULL,										/* tp_compare */
	(reprfunc)UnaryPredicate0D___repr__,					/* tp_repr */

	/* Method suites for standard classes */

	NULL,                       /* PyNumberMethods *tp_as_number; */
	NULL,                       /* PySequenceMethods *tp_as_sequence; */
	NULL,                       /* PyMappingMethods *tp_as_mapping; */

	/* More standard operations (here for binary compatibility) */

	NULL,						/* hashfunc tp_hash; */
	(ternaryfunc)UnaryPredicate0D___call__,                       /* ternaryfunc tp_call; */
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
	BPy_UnaryPredicate0D_methods,	/* struct PyMethodDef *tp_methods; */
	NULL,                       	/* struct PyMemberDef *tp_members; */
	NULL,         					/* struct PyGetSetDef *tp_getset; */
	NULL,							/* struct _typeobject *tp_base; */
	NULL,							/* PyObject *tp_dict; */
	NULL,							/* descrgetfunc tp_descr_get; */
	NULL,							/* descrsetfunc tp_descr_set; */
	0,                          	/* long tp_dictoffset; */
	(initproc)UnaryPredicate0D___init__, /* initproc tp_init; */
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
PyMODINIT_FUNC UnaryPredicate0D_Init( PyObject *module )
{
	if( module == NULL )
		return;

	if( PyType_Ready( &UnaryPredicate0D_Type ) < 0 )
		return;
	Py_INCREF( &UnaryPredicate0D_Type );
	PyModule_AddObject(module, "UnaryPredicate0D", (PyObject *)&UnaryPredicate0D_Type);
	
	if( PyType_Ready( &FalseUP0D_Type ) < 0 )
		return;
	Py_INCREF( &FalseUP0D_Type );
	PyModule_AddObject(module, "FalseUP0D", (PyObject *)&FalseUP0D_Type);
	
	if( PyType_Ready( &TrueUP0D_Type ) < 0 )
		return;
	Py_INCREF( &TrueUP0D_Type );
	PyModule_AddObject(module, "TrueUP0D", (PyObject *)&TrueUP0D_Type);
	
}

//------------------------INSTANCE METHODS ----------------------------------

int UnaryPredicate0D___init__(BPy_UnaryPredicate0D *self, PyObject *args, PyObject *kwds)
{
    if ( !PyArg_ParseTuple(args, "") )
        return -1;
	self->up0D = new UnaryPredicate0D();
	self->up0D->py_up0D = (PyObject *) self;
	return 0;
}

void UnaryPredicate0D___dealloc__(BPy_UnaryPredicate0D* self)
{
	if (self->up0D)
		delete self->up0D;
    self->ob_type->tp_free((PyObject*)self);
}


PyObject * UnaryPredicate0D___repr__(BPy_UnaryPredicate0D* self)
{
    return PyString_FromFormat("type: %s - address: %p", self->up0D->getName().c_str(), self->up0D );
}


PyObject * UnaryPredicate0D_getName( BPy_UnaryPredicate0D *self )
{
	return PyString_FromString( self->up0D->getName().c_str() );
}

PyObject * UnaryPredicate0D___call__( BPy_UnaryPredicate0D *self, PyObject *args, PyObject *kwds)
{
	PyObject *py_if0D_it;

	if( kwds != NULL ) {
		PyErr_SetString(PyExc_TypeError, "keyword argument(s) not supported");
		return NULL;
	}
	if( !PyArg_ParseTuple(args, "O!", &Interface0DIterator_Type, &py_if0D_it) )
		return NULL;

	Interface0DIterator *if0D_it = ((BPy_Interface0DIterator *) py_if0D_it)->if0D_it;

	if( !if0D_it ) {
		string msg(self->up0D->getName() + " has no Interface0DIterator");
		PyErr_SetString(PyExc_RuntimeError, msg.c_str());
		return NULL;
	}
	if( typeid(*(self->up0D)) == typeid(UnaryPredicate0D) ) {
		PyErr_SetString(PyExc_TypeError, "__call__ method not properly overridden");
		return NULL;
	}
	if (self->up0D->operator()(*if0D_it) < 0) {
		if (!PyErr_Occurred()) {
			string msg(self->up0D->getName() + " __call__ method failed");
			PyErr_SetString(PyExc_RuntimeError, msg.c_str());
		}
		return NULL;
	}
	return PyBool_from_bool( self->up0D->result );
}


///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif



