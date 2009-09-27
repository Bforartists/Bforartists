#include "BPy_UnaryFunction0DEdgeNature.h"

#include "../BPy_Convert.h"
#include "../Iterator/BPy_Interface0DIterator.h"

#include "UnaryFunction0D_Nature_EdgeNature/BPy_CurveNatureF0D.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

/*---------------  Python API function prototypes for UnaryFunction0DEdgeNature instance  -----------*/
static int UnaryFunction0DEdgeNature___init__(BPy_UnaryFunction0DEdgeNature* self, PyObject *args, PyObject *kwds);
static void UnaryFunction0DEdgeNature___dealloc__(BPy_UnaryFunction0DEdgeNature* self);
static PyObject * UnaryFunction0DEdgeNature___repr__(BPy_UnaryFunction0DEdgeNature* self);

static PyObject * UnaryFunction0DEdgeNature_getName( BPy_UnaryFunction0DEdgeNature *self);
static PyObject * UnaryFunction0DEdgeNature___call__( BPy_UnaryFunction0DEdgeNature *self, PyObject *args, PyObject *kwds);

/*----------------------UnaryFunction0DEdgeNature instance definitions ----------------------------*/
static PyMethodDef BPy_UnaryFunction0DEdgeNature_methods[] = {
	{"getName", ( PyCFunction ) UnaryFunction0DEdgeNature_getName, METH_NOARGS, "() Returns the string of the name of the unary 0D function."},
	{NULL, NULL, 0, NULL}
};

/*-----------------------BPy_UnaryFunction0DEdgeNature type definition ------------------------------*/

PyTypeObject UnaryFunction0DEdgeNature_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"UnaryFunction0DEdgeNature",    /* tp_name */
	sizeof(BPy_UnaryFunction0DEdgeNature), /* tp_basicsize */
	0,                              /* tp_itemsize */
	(destructor)UnaryFunction0DEdgeNature___dealloc__, /* tp_dealloc */
	0,                              /* tp_print */
	0,                              /* tp_getattr */
	0,                              /* tp_setattr */
	0,                              /* tp_reserved */
	(reprfunc)UnaryFunction0DEdgeNature___repr__, /* tp_repr */
	0,                              /* tp_as_number */
	0,                              /* tp_as_sequence */
	0,                              /* tp_as_mapping */
	0,                              /* tp_hash  */
	(ternaryfunc)UnaryFunction0DEdgeNature___call__, /* tp_call */
	0,                              /* tp_str */
	0,                              /* tp_getattro */
	0,                              /* tp_setattro */
	0,                              /* tp_as_buffer */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
	"UnaryFunction0DEdgeNature objects", /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	BPy_UnaryFunction0DEdgeNature_methods, /* tp_methods */
	0,                              /* tp_members */
	0,                              /* tp_getset */
	&UnaryFunction0D_Type,          /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)UnaryFunction0DEdgeNature___init__, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

//-------------------MODULE INITIALIZATION--------------------------------

int UnaryFunction0DEdgeNature_Init( PyObject *module ) {

	if( module == NULL )
		return -1;

	if( PyType_Ready( &UnaryFunction0DEdgeNature_Type ) < 0 )
		return -1;
	Py_INCREF( &UnaryFunction0DEdgeNature_Type );
	PyModule_AddObject(module, "UnaryFunction0DEdgeNature", (PyObject *)&UnaryFunction0DEdgeNature_Type);
	
	if( PyType_Ready( &CurveNatureF0D_Type ) < 0 )
		return -1;
	Py_INCREF( &CurveNatureF0D_Type );
	PyModule_AddObject(module, "CurveNatureF0D", (PyObject *)&CurveNatureF0D_Type);

	return 0;
}

//------------------------INSTANCE METHODS ----------------------------------

int UnaryFunction0DEdgeNature___init__(BPy_UnaryFunction0DEdgeNature* self, PyObject *args, PyObject *kwds)
{
    if ( !PyArg_ParseTuple(args, "") )
        return -1;
	self->uf0D_edgenature = new UnaryFunction0D<Nature::EdgeNature>();
	self->uf0D_edgenature->py_uf0D = (PyObject *)self;
	return 0;
}

void UnaryFunction0DEdgeNature___dealloc__(BPy_UnaryFunction0DEdgeNature* self)
{
	if (self->uf0D_edgenature)
		delete self->uf0D_edgenature;
	UnaryFunction0D_Type.tp_dealloc((PyObject*)self);
}


PyObject * UnaryFunction0DEdgeNature___repr__(BPy_UnaryFunction0DEdgeNature* self)
{
	return PyUnicode_FromFormat("type: %s - address: %p", self->uf0D_edgenature->getName().c_str(), self->uf0D_edgenature );
}

PyObject * UnaryFunction0DEdgeNature_getName( BPy_UnaryFunction0DEdgeNature *self )
{
	return PyUnicode_FromFormat( self->uf0D_edgenature->getName().c_str() );
}

PyObject * UnaryFunction0DEdgeNature___call__( BPy_UnaryFunction0DEdgeNature *self, PyObject *args, PyObject *kwds)
{
	PyObject *obj;

	if( kwds != NULL ) {
		PyErr_SetString(PyExc_TypeError, "keyword argument(s) not supported");
		return NULL;
	}
	if(!PyArg_ParseTuple(args, "O!", &Interface0DIterator_Type, &obj))
		return NULL;
	
	if( typeid(*(self->uf0D_edgenature)) == typeid(UnaryFunction0D<Nature::EdgeNature>) ) {
		PyErr_SetString(PyExc_TypeError, "__call__ method not properly overridden");
		return NULL;
	}
	if (self->uf0D_edgenature->operator()(*( ((BPy_Interface0DIterator *) obj)->if0D_it )) < 0) {
		if (!PyErr_Occurred()) {
			string msg(self->uf0D_edgenature->getName() + " __call__ method failed");
			PyErr_SetString(PyExc_RuntimeError, msg.c_str());
		}
		return NULL;
	}
	return BPy_Nature_from_Nature( self->uf0D_edgenature->result );

}

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
