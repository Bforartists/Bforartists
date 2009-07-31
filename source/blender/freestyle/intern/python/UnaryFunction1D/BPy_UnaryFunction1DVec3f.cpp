#include "BPy_UnaryFunction1DVec3f.h"

#include "../BPy_Convert.h"
#include "../BPy_Interface1D.h"
#include "../BPy_IntegrationType.h"

#include "UnaryFunction1D_Vec3f/BPy_Orientation3DF1D.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

/*---------------  Python API function prototypes for UnaryFunction1DVec3f instance  -----------*/
static int UnaryFunction1DVec3f___init__(BPy_UnaryFunction1DVec3f* self, PyObject *args);
static void UnaryFunction1DVec3f___dealloc__(BPy_UnaryFunction1DVec3f* self);
static PyObject * UnaryFunction1DVec3f___repr__(BPy_UnaryFunction1DVec3f* self);

static PyObject * UnaryFunction1DVec3f_getName( BPy_UnaryFunction1DVec3f *self);
static PyObject * UnaryFunction1DVec3f___call__( BPy_UnaryFunction1DVec3f *self, PyObject *args, PyObject *kwds);
static PyObject * UnaryFunction1DVec3f_setIntegrationType(BPy_UnaryFunction1DVec3f* self, PyObject *args);
static PyObject * UnaryFunction1DVec3f_getIntegrationType(BPy_UnaryFunction1DVec3f* self);

/*----------------------UnaryFunction1DVec3f instance definitions ----------------------------*/
static PyMethodDef BPy_UnaryFunction1DVec3f_methods[] = {
	{"getName", ( PyCFunction ) UnaryFunction1DVec3f_getName, METH_NOARGS, "（ ）Returns the string of the name of the unary 1D function."},
	{"setIntegrationType", ( PyCFunction ) UnaryFunction1DVec3f_setIntegrationType, METH_VARARGS, "（IntegrationType i ）Sets the integration method" },
	{"getIntegrationType", ( PyCFunction ) UnaryFunction1DVec3f_getIntegrationType, METH_NOARGS, "() Returns the integration method." },
	{NULL, NULL, 0, NULL}
};

/*-----------------------BPy_UnaryFunction1DVec3f type definition ------------------------------*/

PyTypeObject UnaryFunction1DVec3f_Type = {
	PyObject_HEAD_INIT( NULL ) 
	0,							/* ob_size */
	"UnaryFunction1DVec3f",				/* tp_name */
	sizeof( BPy_UnaryFunction1DVec3f ),	/* tp_basicsize */
	0,							/* tp_itemsize */
	
	/* methods */
	(destructor)UnaryFunction1DVec3f___dealloc__,	/* tp_dealloc */
	NULL,                       				/* printfunc tp_print; */
	NULL,                       				/* getattrfunc tp_getattr; */
	NULL,                       				/* setattrfunc tp_setattr; */
	NULL,										/* tp_compare */
	(reprfunc)UnaryFunction1DVec3f___repr__,					/* tp_repr */

	/* Method suites for standard classes */

	NULL,                       /* PyNumberMethods *tp_as_number; */
	NULL,                       /* PySequenceMethods *tp_as_sequence; */
	NULL,                       /* PyMappingMethods *tp_as_mapping; */

	/* More standard operations (here for binary compatibility) */

	NULL,						/* hashfunc tp_hash; */
	(ternaryfunc)UnaryFunction1DVec3f___call__,                       /* ternaryfunc tp_call; */
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
	BPy_UnaryFunction1DVec3f_methods,	/* struct PyMethodDef *tp_methods; */
	NULL,                       	/* struct PyMemberDef *tp_members; */
	NULL,         					/* struct PyGetSetDef *tp_getset; */
	&UnaryFunction1D_Type,							/* struct _typeobject *tp_base; */
	NULL,							/* PyObject *tp_dict; */
	NULL,							/* descrgetfunc tp_descr_get; */
	NULL,							/* descrsetfunc tp_descr_set; */
	0,                          	/* long tp_dictoffset; */
	(initproc)UnaryFunction1DVec3f___init__, /* initproc tp_init; */
	NULL,							/* allocfunc tp_alloc; */
	NULL,		/* newfunc tp_new; */
	
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

PyMODINIT_FUNC UnaryFunction1DVec3f_Init( PyObject *module ) {

	if( module == NULL )
		return;

	if( PyType_Ready( &UnaryFunction1DVec3f_Type ) < 0 )
		return;
	Py_INCREF( &UnaryFunction1DVec3f_Type );
	PyModule_AddObject(module, "UnaryFunction1DVec3f", (PyObject *)&UnaryFunction1DVec3f_Type);
	
	if( PyType_Ready( &Orientation3DF1D_Type ) < 0 )
		return;
	Py_INCREF( &Orientation3DF1D_Type );
	PyModule_AddObject(module, "Orientation3DF1D", (PyObject *)&Orientation3DF1D_Type);
		
}

//------------------------INSTANCE METHODS ----------------------------------

int UnaryFunction1DVec3f___init__(BPy_UnaryFunction1DVec3f* self, PyObject *args)
{
	PyObject *obj;

	if( !PyArg_ParseTuple(args, "|O!", &IntegrationType_Type, &obj) ) {
		cout << "ERROR: UnaryFunction1DVec3f___init__ " << endl;		
		return -1;
	}
	
	if( !obj )
		self->uf1D_vec3f = new UnaryFunction1D<Vec3f>();
	else {
		self->uf1D_vec3f = new UnaryFunction1D<Vec3f>( IntegrationType_from_BPy_IntegrationType(obj) );
	}
	
	self->uf1D_vec3f->py_uf1D = (PyObject *)self;
	
	return 0;
}
void UnaryFunction1DVec3f___dealloc__(BPy_UnaryFunction1DVec3f* self)
{
	if (self->uf1D_vec3f)
		delete self->uf1D_vec3f;
	UnaryFunction1D_Type.tp_dealloc((PyObject*)self);
}


PyObject * UnaryFunction1DVec3f___repr__(BPy_UnaryFunction1DVec3f* self)
{
	return PyString_FromFormat("type: %s - address: %p", self->uf1D_vec3f->getName().c_str(), self->uf1D_vec3f );
}

PyObject * UnaryFunction1DVec3f_getName( BPy_UnaryFunction1DVec3f *self )
{
	return PyString_FromString( self->uf1D_vec3f->getName().c_str() );
}

PyObject * UnaryFunction1DVec3f___call__( BPy_UnaryFunction1DVec3f *self, PyObject *args, PyObject *kwds)
{
	PyObject *obj;

	if( kwds != NULL ) {
		PyErr_SetString(PyExc_TypeError, "keyword argument(s) not supported");
		return NULL;
	}
	if( !PyArg_ParseTuple(args, "O!", &Interface1D_Type, &obj) )
		return NULL;
	
	if( typeid(*(self->uf1D_vec3f)) == typeid(UnaryFunction1D<Vec3f>) ) {
		PyErr_SetString(PyExc_TypeError, "__call__ method not properly overridden");
		return NULL;
	}
	if (self->uf1D_vec3f->operator()(*( ((BPy_Interface1D *) obj)->if1D )) < 0) {
		if (!PyErr_Occurred()) {
			string msg(self->uf1D_vec3f->getName() + " __call__ method failed");
			PyErr_SetString(PyExc_RuntimeError, msg.c_str());
		}
		return NULL;
	}
	return Vector_from_Vec3f( self->uf1D_vec3f->result );

}

PyObject * UnaryFunction1DVec3f_setIntegrationType(BPy_UnaryFunction1DVec3f* self, PyObject *args)
{
	PyObject *obj;

	if( !PyArg_ParseTuple(args, "O!", &IntegrationType_Type, &obj) )
		return NULL;
	
	self->uf1D_vec3f->setIntegrationType( IntegrationType_from_BPy_IntegrationType(obj) );
	Py_RETURN_NONE;
}

PyObject * UnaryFunction1DVec3f_getIntegrationType(BPy_UnaryFunction1DVec3f* self) {
	return BPy_IntegrationType_from_IntegrationType( self->uf1D_vec3f->getIntegrationType() );
}

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
