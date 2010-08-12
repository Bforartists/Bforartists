#include "BPy_ViewMapGradientNormBP1D.h"

#include "../BPy_Convert.h"
#include "../BPy_IntegrationType.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------INSTANCE METHODS ----------------------------------

//ViewMapGradientNormBP1D(int level, IntegrationType iType=MEAN, float sampling=2.0) 

static char ViewMapGradientNormBP1D___doc__[] =
"Class hierarchy: :class:`BinaryPredicate1D` > :class:`ViewMapGradientNormBP1D`\n"
"\n"
".. method:: __call__(inter1, inter2)\n"
"\n"
"   Returns true if the evaluation of the Gradient norm Function is\n"
"   higher for inter1 than for inter2.\n"
"\n"
"   :arg inter1: The first Interface1D object.\n"
"   :type inter1: :class:`Interface1D`\n"
"   :arg inter2: The second Interface1D object.\n"
"   :type inter2: :class:`Interface1D`\n"
"   :return: True or false.\n"
"   :rtype: bool\n";

static int ViewMapGradientNormBP1D___init__( BPy_ViewMapGradientNormBP1D* self, PyObject *args )
{
	int i;
	PyObject *obj;
	float f = 2.0;

	if(!( PyArg_ParseTuple(args, "i|O!f", &i, &IntegrationType_Type, &obj, &f) ))
		return -1;
	
	IntegrationType t = ( obj ) ? IntegrationType_from_BPy_IntegrationType(obj) : MEAN;
	self->py_bp1D.bp1D = new Predicates1D::ViewMapGradientNormBP1D(i,t,f);
	return 0;
}

/*-----------------------BPy_ViewMapGradientNormBP1D type definition ------------------------------*/

PyTypeObject ViewMapGradientNormBP1D_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"ViewMapGradientNormBP1D",      /* tp_name */
	sizeof(BPy_ViewMapGradientNormBP1D), /* tp_basicsize */
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
	ViewMapGradientNormBP1D___doc__, /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	0,                              /* tp_methods */
	0,                              /* tp_members */
	0,                              /* tp_getset */
	&BinaryPredicate1D_Type,        /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)ViewMapGradientNormBP1D___init__, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
