#include "BPy_DensityF0D.h"

#include "../../../stroke/AdvancedFunctions0D.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------INSTANCE METHODS ----------------------------------

static char DensityF0D___doc__[] =
"Class hierarchy: :class:`UnaryFunction0D` > :class:`UnaryFunction0DDouble` > :class:`DensityF0D`\n"
"\n"
".. method:: __init__(sigma=2.0)\n"
"\n"
"   Builds a DensityF0D object.\n"
"\n"
"   :arg sigma: The gaussian sigma value indicating the X value for\n"
"      which the gaussian function is 0.5.  It leads to the window size\n"
"      value (the larger, the smoother).\n"
"   :type sigma: float\n"
"\n"
".. method:: __call__(it)\n"
"\n"
"   Returns the density of the (result) image evaluated at the\n"
"   :class:`Interface0D` pointed by the Interface0DIterator.  This\n"
"   density is evaluated using a pixels square window around the\n"
"   evaluation point and integrating these values using a gaussian.\n"
"\n"
"   :arg it: An Interface0DIterator object.\n"
"   :type it: :class:`Interface0DIterator`\n"
"   :return: The density of the image evaluated at the pointed\n"
"      Interface0D.\n"
"   :rtype: float\n";

static int DensityF0D___init__(BPy_DensityF0D* self, PyObject *args, PyObject *kwds)
{
	static const char *kwlist[] = {"sigma", NULL};
	double d = 2;

	if (!PyArg_ParseTupleAndKeywords(args, kwds, "|d", (char **)kwlist, &d))
		return -1;
	self->py_uf0D_double.uf0D_double = new Functions0D::DensityF0D(d);
	self->py_uf0D_double.uf0D_double->py_uf0D = (PyObject *)self;
	return 0;
}

/*-----------------------BPy_DensityF0D type definition ------------------------------*/

PyTypeObject DensityF0D_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"DensityF0D",                   /* tp_name */
	sizeof(BPy_DensityF0D),         /* tp_basicsize */
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
	DensityF0D___doc__,             /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	0,                              /* tp_methods */
	0,                              /* tp_members */
	0,                              /* tp_getset */
	&UnaryFunction0DDouble_Type,    /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)DensityF0D___init__,  /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
