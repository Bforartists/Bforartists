#include "BPy_IncreasingThicknessShader.h"

#include "../../stroke/BasicStrokeShaders.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------INSTANCE METHODS ----------------------------------

static char IncreasingThicknessShader___doc__[] =
"Class hierarchy: :class:`StrokeShader` > :class:`IncreasingThicknessShader`\n"
"\n"
"[Thickness shader]\n"
"\n"
".. method:: __init__(iThicknessA, iThicknessB)\n"
"\n"
"   Builds an IncreasingThicknessShader object.\n"
"\n"
"   :arg iThicknessA: The first thickness value.\n"
"   :type iThicknessA: float\n"
"   :arg iThicknessB: The second thickness value.\n"
"   :type iThicknessB: float\n"
"\n"
".. method:: shade(s)\n"
"\n"
"   Assigns thicknesses values such as the thickness increases from a\n"
"   thickness value A to a thickness value B between the first vertex\n"
"   to the midpoint vertex and then decreases from B to a A between\n"
"   this midpoint vertex and the last vertex.  The thickness is\n"
"   linearly interpolated from A to B.\n"
"\n"
"   :arg s: A Stroke object.\n"
"   :type s: :class:`Stroke`\n";

static int IncreasingThicknessShader___init__( BPy_IncreasingThicknessShader* self, PyObject *args)
{
	float f1, f2;

	if(!( PyArg_ParseTuple(args, "ff", &f1, &f2) ))
		return -1;

	self->py_ss.ss = new StrokeShaders::IncreasingThicknessShader(f1, f2);
	return 0;
}

/*-----------------------BPy_IncreasingThicknessShader type definition ------------------------------*/

PyTypeObject IncreasingThicknessShader_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"IncreasingThicknessShader",    /* tp_name */
	sizeof(BPy_IncreasingThicknessShader), /* tp_basicsize */
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
	IncreasingThicknessShader___doc__, /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	0,                              /* tp_methods */
	0,                              /* tp_members */
	0,                              /* tp_getset */
	&StrokeShader_Type,             /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)IncreasingThicknessShader___init__, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
