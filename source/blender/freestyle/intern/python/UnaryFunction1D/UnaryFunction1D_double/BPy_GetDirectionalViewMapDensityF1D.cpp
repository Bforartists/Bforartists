#include "BPy_GetDirectionalViewMapDensityF1D.h"

#include "../../../stroke/AdvancedFunctions1D.h"
#include "../../BPy_Convert.h"
#include "../../BPy_IntegrationType.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------INSTANCE METHODS ----------------------------------

static char GetDirectionalViewMapDensityF1D___doc__[] =
"Class hierarchy: :class:`UnaryFunction1D` > :class:`UnaryFunction1DDouble` > :class:`GetDirectionalViewMapDensityF1D`\n"
"\n"
".. method:: __init__(iOrientation, level, iType=IntegrationType.MEAN, sampling=2.0)\n"
"\n"
"   Builds a GetDirectionalViewMapDensityF1D object.\n"
"\n"
"   :arg iOrientation: The number of the directional map we must work\n"
"      with.\n"
"   :type iOrientation: int\n"
"   :arg level: The level of the pyramid from which the pixel must be\n"
"      read.\n"
"   :type level: int\n"
"   :arg iType: The integration method used to compute a single value\n"
"      from a set of values.\n"
"   :type iType: :class:`IntegrationType`\n"
"   :arg sampling: The resolution used to sample the chain: the\n"
"      corresponding 0D function is evaluated at each sample point and\n"
"      the result is obtained by combining the resulting values into a\n"
"      single one, following the method specified by iType.\n"
"   :type sampling: float\n"
"\n"
".. method:: __call__(inter)\n"
"\n"
"   Returns the density evaluated for an Interface1D in of the\n"
"   steerable viewmaps image.  The direction telling which Directional\n"
"   map to choose is explicitely specified by the user.  The density is\n"
"   evaluated for a set of points along the Interface1D (using the\n"
"   :class:`ReadSteerableViewMapPixelF0D` functor) and then integrated\n"
"   into a single value using a user-defined integration method.\n"
"\n"
"   :arg inter: An Interface1D object.\n"
"   :type inter: :class:`Interface1D`\n"
"   :return: the density evaluated for an Interface1D in of the\n"
"      steerable viewmaps image.\n"
"   :rtype: float\n";

static int GetDirectionalViewMapDensityF1D___init__( BPy_GetDirectionalViewMapDensityF1D* self, PyObject *args)
{
	PyObject *obj = 0;
	unsigned int u1, u2;
	float f = 2.0;

	if( !PyArg_ParseTuple(args, "II|O!f", &u1, &u2, &IntegrationType_Type, &obj, &f) )
		return -1;
	
	IntegrationType t = ( obj ) ? IntegrationType_from_BPy_IntegrationType(obj) : MEAN;
	self->py_uf1D_double.uf1D_double = new Functions1D::GetDirectionalViewMapDensityF1D(u1, u2, t, f);
	return 0;

}

/*-----------------------BPy_GetDirectionalViewMapDensityF1D type definition ------------------------------*/

PyTypeObject GetDirectionalViewMapDensityF1D_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"GetDirectionalViewMapDensityF1D", /* tp_name */
	sizeof(BPy_GetDirectionalViewMapDensityF1D), /* tp_basicsize */
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
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /* tp_flags */
	GetDirectionalViewMapDensityF1D___doc__, /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	0,                              /* tp_methods */
	0,                              /* tp_members */
	0,                              /* tp_getset */
	&UnaryFunction1DDouble_Type,    /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)GetDirectionalViewMapDensityF1D___init__, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
