#include "BPy_IntegrationType.h"

#include "BPy_Convert.h"
#include "UnaryFunction0D/BPy_UnaryFunction0DDouble.h"
#include "UnaryFunction0D/BPy_UnaryFunction0DFloat.h"
#include "UnaryFunction0D/BPy_UnaryFunction0DUnsigned.h"
#include "Iterator/BPy_Interface0DIterator.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------ MODULE FUNCTIONS ----------------------------------

static char Integrator_integrate___doc__[] =
".. function:: integrate(fun, it, it_end, integration_type)\n"
"\n"
"   Returns a single value from a set of values evaluated at each 0D\n"
"   element of this 1D element.\n"
"\n"
"   :arg fun: The UnaryFunction0D used to compute a value at each\n"
"      Interface0D.\n"
"   :type fun: :class:`UnaryFunction0D`\n"
"   :arg it: The Interface0DIterator used to iterate over the 0D\n"
"      elements of this 1D element. The integration will occur over\n"
"      the 0D elements starting from the one pointed by it.\n"
"   :type it: :class:`Interface0DIterator`\n"
"   :arg it_end: The Interface0DIterator pointing the end of the 0D\n"
"      elements of the 1D element.\n"
"   :type it_end: :class:`Interface0DIterator`\n"
"   :arg integration_type: The integration method used to compute a\n"
"      single value from a set of values.\n"
"   :type integration_type: :class:`IntegrationType`\n"
"   :return: The single value obtained for the 1D element.  The return\n"
"      value type is float if fun is of the :class:`UnaryFunction0DDouble`\n"
"      or :class:`UnaryFunction0DFloat` type, and int if fun is of the\n"
"      :class:`UnaryFunction0DUnsigned` type.\n"
"   :rtype: int or float\n";

static PyObject * Integrator_integrate( PyObject *self, PyObject *args )
{
	PyObject *obj1, *obj4 = 0;
	BPy_Interface0DIterator *obj2, *obj3;

#if 1
	if(!( PyArg_ParseTuple(args, "O!O!O!|O!", &UnaryFunction0D_Type, &obj1,
		&Interface0DIterator_Type, &obj2, &Interface0DIterator_Type, &obj3,
		&IntegrationType_Type, &obj4) ))
		return NULL;
#else
	if(!( PyArg_ParseTuple(args, "OOO|O", &obj1, &obj2, &obj3, &obj4) ))
		return NULL;
	if(!BPy_UnaryFunction0D_Check(obj1)) {
		PyErr_SetString(PyExc_TypeError, "argument 1 must be a UnaryFunction0D object");
		return NULL;
	}
	if(!BPy_Interface0DIterator_Check(obj2)) {
		PyErr_SetString(PyExc_TypeError, "argument 2 must be a Interface0DIterator object");
		return NULL;
	}
	if(!BPy_Interface0DIterator_Check(obj3)) {
		PyErr_SetString(PyExc_TypeError, "argument 3 must be a Interface0DIterator object");
		return NULL;
	}
	if(obj4 && !BPy_IntegrationType_Check(obj4)) {
		PyErr_SetString(PyExc_TypeError, "argument 4 must be a IntegrationType object");
		return NULL;
	}
#endif

	Interface0DIterator it(*(obj2->if0D_it)), it_end(*(obj3->if0D_it));
	IntegrationType t = ( obj4 ) ? IntegrationType_from_BPy_IntegrationType( obj4 ) : MEAN;

	if( BPy_UnaryFunction0DDouble_Check(obj1) ) {
		UnaryFunction0D<double> *fun = ((BPy_UnaryFunction0DDouble *)obj1)->uf0D_double;
		double res = integrate( *fun, it, it_end, t );
		return PyFloat_FromDouble( res );

	} else if( BPy_UnaryFunction0DFloat_Check(obj1) ) {
		UnaryFunction0D<float> *fun = ((BPy_UnaryFunction0DFloat *)obj1)->uf0D_float;
		float res = integrate( *fun, it, it_end, t );
		return PyFloat_FromDouble( res );

	} else if( BPy_UnaryFunction0DUnsigned_Check(obj1) ) {
		UnaryFunction0D<unsigned int> *fun = ((BPy_UnaryFunction0DUnsigned *)obj1)->uf0D_unsigned;
		unsigned int res = integrate( *fun, it, it_end, t );
		return PyLong_FromLong( res );

	} else {
		string msg("unsupported function type: " + string(obj1->ob_type->tp_name));
		PyErr_SetString(PyExc_TypeError, msg.c_str());
		return NULL;
	}
}

/*-----------------------Integrator module docstring---------------------------------------*/

static char module_docstring[] = "The Blender Freestyle.Integrator submodule\n\n";

/*-----------------------Integrator module functions definitions---------------------------*/

static PyMethodDef module_functions[] = {
  {"integrate", (PyCFunction) Integrator_integrate, METH_VARARGS, Integrator_integrate___doc__},
  {NULL, NULL, 0, NULL}
};

/*-----------------------Integrator module definition--------------------------------------*/

static PyModuleDef module_definition = {
    PyModuleDef_HEAD_INIT,
    "Freestyle.Integrator",
    module_docstring,
    -1,
    module_functions
};

/*-----------------------BPy_IntegrationType type definition ------------------------------*/

static char IntegrationType___doc__[] =
"Class hierarchy: int > :class:`IntegrationType`\n"
"\n"
"Different integration methods that can be invoked to integrate into a\n"
"single value the set of values obtained from each 0D element of an 1D\n"
"element:\n"
"\n"
"* IntegrationType.MEAN: The value computed for the 1D element is the\n"
"  mean of the values obtained for the 0D elements.\n"
"* IntegrationType.MIN: The value computed for the 1D element is the\n"
"  minimum of the values obtained for the 0D elements.\n"
"* IntegrationType.MAX: The value computed for the 1D element is the\n"
"  maximum of the values obtained for the 0D elements.\n"
"* IntegrationType.FIRST: The value computed for the 1D element is the\n"
"  first of the values obtained for the 0D elements.\n"
"* IntegrationType.LAST: The value computed for the 1D element is the\n"
"  last of the values obtained for the 0D elements.\n";

PyTypeObject IntegrationType_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"IntegrationType",              /* tp_name */
	sizeof(PyLongObject),           /* tp_basicsize */
	0,                              /* tp_itemsize */
	0,                              /* tp_dealloc */
	0,                              /* tp_print */
	0,                              /* tp_getattr */
	0,                              /* tp_setattr */
	0,                              /* tp_reserved */
	0,                              /* tp_repr */
	0,                              /* tp_as_number */
	0,                              /* tp_as_sequence */
	0,                              /* tp_as_mapping */
	0,                              /* tp_hash  */
	0,                              /* tp_call */
	0,                              /* tp_str */
	0,                              /* tp_getattro */
	0,                              /* tp_setattro */
	0,                              /* tp_as_buffer */
	Py_TPFLAGS_DEFAULT,             /* tp_flags */
	IntegrationType___doc__,        /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	0,                              /* tp_methods */
	0,                              /* tp_members */
	0,                              /* tp_getset */
	&PyLong_Type,                   /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	0,                              /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

/*-----------------------BPy_IntegrationType instance definitions -------------------------*/

static PyLongObject _IntegrationType_MEAN = {
	PyVarObject_HEAD_INIT(&IntegrationType_Type, 1)
	{ MEAN }
};
static PyLongObject _IntegrationType_MIN = {
	PyVarObject_HEAD_INIT(&IntegrationType_Type, 1)
	{ MIN }
};
static PyLongObject _IntegrationType_MAX = {
	PyVarObject_HEAD_INIT(&IntegrationType_Type, 1)
	{ MAX }
};
static PyLongObject _IntegrationType_FIRST = {
	PyVarObject_HEAD_INIT(&IntegrationType_Type, 1)
	{ FIRST }
};
static PyLongObject _IntegrationType_LAST = {
	PyVarObject_HEAD_INIT(&IntegrationType_Type, 1)
	{ LAST }
};

#define BPy_IntegrationType_MEAN  ((PyObject *)&_IntegrationType_MEAN)
#define BPy_IntegrationType_MIN   ((PyObject *)&_IntegrationType_MIN)
#define BPy_IntegrationType_MAX   ((PyObject *)&_IntegrationType_MAX)
#define BPy_IntegrationType_FIRST ((PyObject *)&_IntegrationType_FIRST)
#define BPy_IntegrationType_LAST  ((PyObject *)&_IntegrationType_LAST)

//-------------------MODULE INITIALIZATION--------------------------------
int IntegrationType_Init( PyObject *module )
{	
	PyObject *m, *d, *f;
	
	if( module == NULL )
		return -1;

	if( PyType_Ready( &IntegrationType_Type ) < 0 )
		return -1;
	Py_INCREF( &IntegrationType_Type );
	PyModule_AddObject(module, "IntegrationType", (PyObject *)&IntegrationType_Type);

	PyDict_SetItemString( IntegrationType_Type.tp_dict, "MEAN", BPy_IntegrationType_MEAN);
	PyDict_SetItemString( IntegrationType_Type.tp_dict, "MIN", BPy_IntegrationType_MIN);
	PyDict_SetItemString( IntegrationType_Type.tp_dict, "MAX", BPy_IntegrationType_MAX);
	PyDict_SetItemString( IntegrationType_Type.tp_dict, "FIRST", BPy_IntegrationType_FIRST);
	PyDict_SetItemString( IntegrationType_Type.tp_dict, "LAST", BPy_IntegrationType_LAST);
	
    m = PyModule_Create(&module_definition);
    if (m == NULL)
        return -1;
	Py_INCREF(m);
	PyModule_AddObject(module, "Integrator", m);

	// from Integrator import *
	d = PyModule_GetDict(m);
	for (PyMethodDef *p = module_functions; p->ml_name; p++) {
		f = PyDict_GetItemString(d, p->ml_name);
		Py_INCREF(f);
		PyModule_AddObject(module, p->ml_name, f);
	}

	return 0;
}

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

