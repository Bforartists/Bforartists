#include "BPy_ThicknessVariationPatternShader.h"

#include "../../stroke/BasicStrokeShaders.h"
#include "../BPy_Convert.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------INSTANCE METHODS ----------------------------------

static char ThicknessVariationPatternShader___doc__[] =
"[Thickness shader]\n"
"\n"
".. method:: __init__(pattern_name, iMinThickness, iMaxThickness, stretch)\n"
"\n"
"   Builds a ThicknessVariationPatternShader object.\n"
"\n"
"   :arg pattern_name: The texture file name.\n"
"   :type pattern_name: string\n"
"   :arg iMinThickness: The minimum thickness we don't want to exceed.\n"
"   :type iMinThickness: float\n"
"   :arg iMaxThickness: The maximum thickness we don't want to exceed.\n"
"   :type iMaxThickness: float\n"
"   :arg stretch: Tells whether the pattern texture must be stretched\n"
"      or repeted to fit the stroke.\n"
"   :type stretch: bool\n"
"\n"
".. method:: shade(s)\n"
"\n"
"   Applies a pattern (texture) to vary thickness. The new thicknesses\n"
"   are the result of the multiplication of the pattern and the\n"
"   original thickness.\n"
"\n"
"   :arg s: A Stroke object.\n"
"   :type s: :class:`Stroke`\n";

static int ThicknessVariationPatternShader___init__( BPy_ThicknessVariationPatternShader* self, PyObject *args)
{
	const char *s1;
	float f2 = 1.0, f3 = 5.0;
	PyObject *obj4 = 0;

	if(!( PyArg_ParseTuple(args, "s|ffO", &s1, &f2, &f3, &obj4) ))
		return -1;

	bool b = (obj4) ? bool_from_PyBool(obj4) : true;
	self->py_ss.ss = new StrokeShaders::ThicknessVariationPatternShader(s1, f2, f3, b);
	return 0;
}

/*-----------------------BPy_ThicknessVariationPatternShader type definition ------------------------------*/

PyTypeObject ThicknessVariationPatternShader_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"ThicknessVariationPatternShader", /* tp_name */
	sizeof(BPy_ThicknessVariationPatternShader), /* tp_basicsize */
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
	ThicknessVariationPatternShader___doc__, /* tp_doc */
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
	(initproc)ThicknessVariationPatternShader___init__, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
