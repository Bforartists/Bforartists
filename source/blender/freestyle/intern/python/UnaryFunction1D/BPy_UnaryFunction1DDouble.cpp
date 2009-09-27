#include "BPy_UnaryFunction1DDouble.h"

#include "../BPy_Convert.h"
#include "../BPy_Interface1D.h"
#include "../BPy_IntegrationType.h"

#include "UnaryFunction1D_double/BPy_Curvature2DAngleF1D.h"
#include "UnaryFunction1D_double/BPy_DensityF1D.h"
#include "UnaryFunction1D_double/BPy_GetCompleteViewMapDensityF1D.h"
#include "UnaryFunction1D_double/BPy_GetDirectionalViewMapDensityF1D.h"
#include "UnaryFunction1D_double/BPy_GetProjectedXF1D.h"
#include "UnaryFunction1D_double/BPy_GetProjectedYF1D.h"
#include "UnaryFunction1D_double/BPy_GetProjectedZF1D.h"
#include "UnaryFunction1D_double/BPy_GetSteerableViewMapDensityF1D.h"
#include "UnaryFunction1D_double/BPy_GetViewMapGradientNormF1D.h"
#include "UnaryFunction1D_double/BPy_GetXF1D.h"
#include "UnaryFunction1D_double/BPy_GetYF1D.h"
#include "UnaryFunction1D_double/BPy_GetZF1D.h"
#include "UnaryFunction1D_double/BPy_LocalAverageDepthF1D.h"
#include "UnaryFunction1D_double/BPy_ZDiscontinuityF1D.h"


#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

/*---------------  Python API function prototypes for UnaryFunction1DDouble instance  -----------*/
static int UnaryFunction1DDouble___init__(BPy_UnaryFunction1DDouble* self, PyObject *args);
static void UnaryFunction1DDouble___dealloc__(BPy_UnaryFunction1DDouble* self);
static PyObject * UnaryFunction1DDouble___repr__(BPy_UnaryFunction1DDouble* self);

static PyObject * UnaryFunction1DDouble_getName( BPy_UnaryFunction1DDouble *self);
static PyObject * UnaryFunction1DDouble___call__( BPy_UnaryFunction1DDouble *self, PyObject *args, PyObject *kwds);
static PyObject * UnaryFunction1DDouble_setIntegrationType(BPy_UnaryFunction1DDouble* self, PyObject *args);
static PyObject * UnaryFunction1DDouble_getIntegrationType(BPy_UnaryFunction1DDouble* self);

/*----------------------UnaryFunction1DDouble instance definitions ----------------------------*/
static PyMethodDef BPy_UnaryFunction1DDouble_methods[] = {
	{"getName", ( PyCFunction ) UnaryFunction1DDouble_getName, METH_NOARGS, "() Returns the string of the name of the unary 1D function."},
	{"setIntegrationType", ( PyCFunction ) UnaryFunction1DDouble_setIntegrationType, METH_VARARGS, "(IntegrationType i) Sets the integration method" },
	{"getIntegrationType", ( PyCFunction ) UnaryFunction1DDouble_getIntegrationType, METH_NOARGS, "() Returns the integration method." },
	{NULL, NULL, 0, NULL}
};

/*-----------------------BPy_UnaryFunction1DDouble type definition ------------------------------*/

PyTypeObject UnaryFunction1DDouble_Type = {
	PyObject_HEAD_INIT(NULL)
	"UnaryFunction1DDouble",        /* tp_name */
	sizeof(BPy_UnaryFunction1DDouble), /* tp_basicsize */
	0,                              /* tp_itemsize */
	(destructor)UnaryFunction1DDouble___dealloc__, /* tp_dealloc */
	0,                              /* tp_print */
	0,                              /* tp_getattr */
	0,                              /* tp_setattr */
	0,                              /* tp_reserved */
	(reprfunc)UnaryFunction1DDouble___repr__, /* tp_repr */
	0,                              /* tp_as_number */
	0,                              /* tp_as_sequence */
	0,                              /* tp_as_mapping */
	0,                              /* tp_hash  */
	(ternaryfunc)UnaryFunction1DDouble___call__, /* tp_call */
	0,                              /* tp_str */
	0,                              /* tp_getattro */
	0,                              /* tp_setattro */
	0,                              /* tp_as_buffer */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
	"UnaryFunction1DDouble objects", /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	BPy_UnaryFunction1DDouble_methods, /* tp_methods */
	0,                              /* tp_members */
	0,                              /* tp_getset */
	&UnaryFunction1D_Type,          /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)UnaryFunction1DDouble___init__, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

//-------------------MODULE INITIALIZATION--------------------------------

int UnaryFunction1DDouble_Init( PyObject *module ) {

	if( module == NULL )
		return -1;

	if( PyType_Ready( &UnaryFunction1DDouble_Type ) < 0 )
		return -1;
	Py_INCREF( &UnaryFunction1DDouble_Type );
	PyModule_AddObject(module, "UnaryFunction1DDouble", (PyObject *)&UnaryFunction1DDouble_Type);

	if( PyType_Ready( &DensityF1D_Type ) < 0 )
		return -1;
	Py_INCREF( &DensityF1D_Type );
	PyModule_AddObject(module, "DensityF1D", (PyObject *)&DensityF1D_Type);

	if( PyType_Ready( &Curvature2DAngleF1D_Type ) < 0 )
		return -1;
	Py_INCREF( &Curvature2DAngleF1D_Type );
	PyModule_AddObject(module, "Curvature2DAngleF1D", (PyObject *)&Curvature2DAngleF1D_Type);

	if( PyType_Ready( &GetCompleteViewMapDensityF1D_Type ) < 0 )
		return -1;
	Py_INCREF( &GetCompleteViewMapDensityF1D_Type );
	PyModule_AddObject(module, "GetCompleteViewMapDensityF1D", (PyObject *)&GetCompleteViewMapDensityF1D_Type);

	if( PyType_Ready( &GetDirectionalViewMapDensityF1D_Type ) < 0 )
		return -1;
	Py_INCREF( &GetDirectionalViewMapDensityF1D_Type );
	PyModule_AddObject(module, "GetDirectionalViewMapDensityF1D", (PyObject *)&GetDirectionalViewMapDensityF1D_Type);

	if( PyType_Ready( &GetProjectedXF1D_Type ) < 0 )
		return -1;
	Py_INCREF( &GetProjectedXF1D_Type );
	PyModule_AddObject(module, "GetProjectedXF1D", (PyObject *)&GetProjectedXF1D_Type);

	if( PyType_Ready( &GetProjectedYF1D_Type ) < 0 )
		return -1;
	Py_INCREF( &GetProjectedYF1D_Type );
	PyModule_AddObject(module, "GetProjectedYF1D", (PyObject *)&GetProjectedYF1D_Type);
	
	if( PyType_Ready( &GetProjectedZF1D_Type ) < 0 )
		return -1;
	Py_INCREF( &GetProjectedZF1D_Type );
	PyModule_AddObject(module, "GetProjectedZF1D", (PyObject *)&GetProjectedZF1D_Type);

	if( PyType_Ready( &GetSteerableViewMapDensityF1D_Type ) < 0 )
		return -1;
	Py_INCREF( &GetSteerableViewMapDensityF1D_Type );
	PyModule_AddObject(module, "GetSteerableViewMapDensityF1D", (PyObject *)&GetSteerableViewMapDensityF1D_Type);

	if( PyType_Ready( &GetViewMapGradientNormF1D_Type ) < 0 )
		return -1;
	Py_INCREF( &GetViewMapGradientNormF1D_Type );
	PyModule_AddObject(module, "GetViewMapGradientNormF1D", (PyObject *)&GetViewMapGradientNormF1D_Type);

	if( PyType_Ready( &GetXF1D_Type ) < 0 )
		return -1;
	Py_INCREF( &GetXF1D_Type );
	PyModule_AddObject(module, "GetXF1D", (PyObject *)&GetXF1D_Type);

	if( PyType_Ready( &GetYF1D_Type ) < 0 )
		return -1;
	Py_INCREF( &GetYF1D_Type );
	PyModule_AddObject(module, "GetYF1D", (PyObject *)&GetYF1D_Type);

	if( PyType_Ready( &GetZF1D_Type ) < 0 )
		return -1;
	Py_INCREF( &GetZF1D_Type );
	PyModule_AddObject(module, "GetZF1D", (PyObject *)&GetZF1D_Type);

	if( PyType_Ready( &LocalAverageDepthF1D_Type ) < 0 )
		return -1;
	Py_INCREF( &LocalAverageDepthF1D_Type );
	PyModule_AddObject(module, "LocalAverageDepthF1D", (PyObject *)&LocalAverageDepthF1D_Type);

	if( PyType_Ready( &ZDiscontinuityF1D_Type ) < 0 )
		return -1;
	Py_INCREF( &ZDiscontinuityF1D_Type );
	PyModule_AddObject(module, "ZDiscontinuityF1D", (PyObject *)&ZDiscontinuityF1D_Type);

	return 0;
}

//------------------------INSTANCE METHODS ----------------------------------

int UnaryFunction1DDouble___init__(BPy_UnaryFunction1DDouble* self, PyObject *args)
{
	PyObject *obj = 0;

	if( !PyArg_ParseTuple(args, "|O!", &IntegrationType_Type, &obj) ) 	
		return -1;
	
	if( !obj )
		self->uf1D_double = new UnaryFunction1D<double>();
	else {
		self->uf1D_double = new UnaryFunction1D<double>( IntegrationType_from_BPy_IntegrationType(obj) );
	}
	
	self->uf1D_double->py_uf1D = (PyObject *)self;
	
	return 0;
}

void UnaryFunction1DDouble___dealloc__(BPy_UnaryFunction1DDouble* self)
{
	if (self->uf1D_double)
		delete self->uf1D_double;
	UnaryFunction1D_Type.tp_dealloc((PyObject*)self);
}


PyObject * UnaryFunction1DDouble___repr__(BPy_UnaryFunction1DDouble* self)
{
	return PyUnicode_FromFormat("type: %s - address: %p", self->uf1D_double->getName().c_str(), self->uf1D_double );
}

PyObject * UnaryFunction1DDouble_getName( BPy_UnaryFunction1DDouble *self )
{
	return PyUnicode_FromFormat( self->uf1D_double->getName().c_str() );
}

PyObject * UnaryFunction1DDouble___call__( BPy_UnaryFunction1DDouble *self, PyObject *args, PyObject *kwds)
{
	PyObject *obj;

	if( kwds != NULL ) {
		PyErr_SetString(PyExc_TypeError, "keyword argument(s) not supported");
		return NULL;
	}
	if( !PyArg_ParseTuple(args, "O!", &Interface1D_Type, &obj) )
		return NULL;
	
	if( typeid(*(self->uf1D_double)) == typeid(UnaryFunction1D<double>) ) {
		PyErr_SetString(PyExc_TypeError, "__call__ method not properly overridden");
		return NULL;
	}
	if (self->uf1D_double->operator()(*( ((BPy_Interface1D *) obj)->if1D )) < 0) {
		if (!PyErr_Occurred()) {
			string msg(self->uf1D_double->getName() + " __call__ method failed");
			PyErr_SetString(PyExc_RuntimeError, msg.c_str());
		}
		return NULL;
	}
	return PyFloat_FromDouble( self->uf1D_double->result );

}

PyObject * UnaryFunction1DDouble_setIntegrationType(BPy_UnaryFunction1DDouble* self, PyObject *args)
{
	PyObject *obj;

	if( !PyArg_ParseTuple(args, "O!", &IntegrationType_Type, &obj) )
		return NULL;
	
	self->uf1D_double->setIntegrationType( IntegrationType_from_BPy_IntegrationType(obj) );
	Py_RETURN_NONE;
}

PyObject * UnaryFunction1DDouble_getIntegrationType(BPy_UnaryFunction1DDouble* self) {
	return BPy_IntegrationType_from_IntegrationType( self->uf1D_double->getIntegrationType() );
}


///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
