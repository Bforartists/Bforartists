#include "BPy_ConstrainedIncreasingThicknessShader.h"

#include "../../stroke/BasicStrokeShaders.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------INSTANCE METHODS ----------------------------------

static char ConstrainedIncreasingThicknessShader___doc__[] =
"[Thickness shader]\n"
"\n"
".. method:: __init__(iThicknessMin, iThicknessMax, iRatio)\n"
"\n"
"   Builds a ConstrainedIncreasingThicknessShader object.\n"
"\n"
"   :arg iThicknessMin: The minimum thickness.\n"
"   :type iThicknessMin: float\n"
"   :arg iThicknessMax: The maximum thickness.\n"
"   :type iThicknessMax: float\n"
"   :arg iRatio: The thickness/length ratio that we don't want to exceed. \n"
"   :type iRatio: float\n"
"\n"
".. method:: shade(s)\n"
"\n"
"   Same as the :class:`IncreasingThicknessShader`, but here we allow\n"
"   the user to control the thickness/length ratio so that we don't get\n"
"   fat short lines.\n"
"\n"
"   :arg s: A Stroke object.\n"
"   :type s: :class:`Stroke`\n";

static int ConstrainedIncreasingThicknessShader___init__( BPy_ConstrainedIncreasingThicknessShader* self, PyObject *args)
{
	float f1, f2, f3;

	if(!( PyArg_ParseTuple(args, "fff", &f1, &f2, &f3) ))
		return -1;

	self->py_ss.ss = new StrokeShaders::ConstrainedIncreasingThicknessShader(f1, f2, f3);
	return 0;
}

/*-----------------------BPy_ConstrainedIncreasingThicknessShader type definition ------------------------------*/

PyTypeObject ConstrainedIncreasingThicknessShader_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"ConstrainedIncreasingThicknessShader", /* tp_name */
	sizeof(BPy_ConstrainedIncreasingThicknessShader), /* tp_basicsize */
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
	ConstrainedIncreasingThicknessShader___doc__, /* tp_doc */
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
	(initproc)ConstrainedIncreasingThicknessShader___init__, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
