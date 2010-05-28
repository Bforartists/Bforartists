#include "BPy_UnaryFunction0DVec3f.h"

#include "../BPy_Convert.h"
#include "../Iterator/BPy_Interface0DIterator.h"

#include "UnaryFunction0D_Vec3f/BPy_VertexOrientation3DF0D.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//-------------------MODULE INITIALIZATION--------------------------------

int UnaryFunction0DVec3f_Init( PyObject *module ) {

	if( module == NULL )
		return -1;

	if( PyType_Ready( &UnaryFunction0DVec3f_Type ) < 0 )
		return -1;
	Py_INCREF( &UnaryFunction0DVec3f_Type );
	PyModule_AddObject(module, "UnaryFunction0DVec3f", (PyObject *)&UnaryFunction0DVec3f_Type);
	
	if( PyType_Ready( &VertexOrientation3DF0D_Type ) < 0 )
		return -1;
	Py_INCREF( &VertexOrientation3DF0D_Type );
	PyModule_AddObject(module, "VertexOrientation3DF0D", (PyObject *)&VertexOrientation3DF0D_Type);

	return 0;
}

//------------------------INSTANCE METHODS ----------------------------------

static char UnaryFunction0DVec3f___doc__[] =
"Base class for unary functions (functors) that work on\n"
":class:`Interface0DIterator` and return a 3D vector.\n"
"\n"
".. method:: __init__()\n"
"\n"
"   Default constructor.\n";

static int UnaryFunction0DVec3f___init__(BPy_UnaryFunction0DVec3f* self, PyObject *args, PyObject *kwds)
{
    if ( !PyArg_ParseTuple(args, "") )
        return -1;
	self->uf0D_vec3f = new UnaryFunction0D<Vec3f>();
	self->uf0D_vec3f->py_uf0D = (PyObject *)self;
	return 0;
}

static void UnaryFunction0DVec3f___dealloc__(BPy_UnaryFunction0DVec3f* self)
{
	if (self->uf0D_vec3f)
		delete self->uf0D_vec3f;
	UnaryFunction0D_Type.tp_dealloc((PyObject*)self);
}

static PyObject * UnaryFunction0DVec3f___repr__(BPy_UnaryFunction0DVec3f* self)
{
	return PyUnicode_FromFormat("type: %s - address: %p", self->uf0D_vec3f->getName().c_str(), self->uf0D_vec3f );
}

static char UnaryFunction0DVec3f_getName___doc__[] =
".. method:: getName()\n"
"\n"
"   Returns the name of the unary 0D predicate.\n"
"\n"
"   :return: The name of the unary 0D predicate.\n"
"   :rtype: str\n";

static PyObject * UnaryFunction0DVec3f_getName( BPy_UnaryFunction0DVec3f *self )
{
	return PyUnicode_FromString( self->uf0D_vec3f->getName().c_str() );
}

static PyObject * UnaryFunction0DVec3f___call__( BPy_UnaryFunction0DVec3f *self, PyObject *args, PyObject *kwds)
{
	PyObject *obj;

	if( kwds != NULL ) {
		PyErr_SetString(PyExc_TypeError, "keyword argument(s) not supported");
		return NULL;
	}
	if(!PyArg_ParseTuple(args, "O!", &Interface0DIterator_Type, &obj))
		return NULL;
	
	if( typeid(*(self->uf0D_vec3f)) == typeid(UnaryFunction0D<Vec3f>) ) {
		PyErr_SetString(PyExc_TypeError, "__call__ method not properly overridden");
		return NULL;
	}
	if (self->uf0D_vec3f->operator()(*( ((BPy_Interface0DIterator *) obj)->if0D_it )) < 0) {
		if (!PyErr_Occurred()) {
			string msg(self->uf0D_vec3f->getName() + " __call__ method failed");
			PyErr_SetString(PyExc_RuntimeError, msg.c_str());
		}
		return NULL;
	}
	return Vector_from_Vec3f( self->uf0D_vec3f->result );

}

/*----------------------UnaryFunction0DVec3f instance definitions ----------------------------*/
static PyMethodDef BPy_UnaryFunction0DVec3f_methods[] = {
	{"getName", ( PyCFunction ) UnaryFunction0DVec3f_getName, METH_NOARGS, UnaryFunction0DVec3f_getName___doc__},
	{NULL, NULL, 0, NULL}
};

/*-----------------------BPy_UnaryFunction0DVec3f type definition ------------------------------*/

PyTypeObject UnaryFunction0DVec3f_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"UnaryFunction0DVec3f",         /* tp_name */
	sizeof(BPy_UnaryFunction0DVec3f), /* tp_basicsize */
	0,                              /* tp_itemsize */
	(destructor)UnaryFunction0DVec3f___dealloc__, /* tp_dealloc */
	0,                              /* tp_print */
	0,                              /* tp_getattr */
	0,                              /* tp_setattr */
	0,                              /* tp_reserved */
	(reprfunc)UnaryFunction0DVec3f___repr__, /* tp_repr */
	0,                              /* tp_as_number */
	0,                              /* tp_as_sequence */
	0,                              /* tp_as_mapping */
	0,                              /* tp_hash  */
	(ternaryfunc)UnaryFunction0DVec3f___call__, /* tp_call */
	0,                              /* tp_str */
	0,                              /* tp_getattro */
	0,                              /* tp_setattro */
	0,                              /* tp_as_buffer */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
	UnaryFunction0DVec3f___doc__,   /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	BPy_UnaryFunction0DVec3f_methods, /* tp_methods */
	0,                              /* tp_members */
	0,                              /* tp_getset */
	&UnaryFunction0D_Type,          /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)UnaryFunction0DVec3f___init__, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
