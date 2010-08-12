#include "BPy_CalligraphicShader.h"

#include "../../stroke/AdvancedStrokeShaders.h"
#include "../BPy_Convert.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------INSTANCE METHODS ----------------------------------

static char CalligraphicShader___doc__[] =
"Class hierarchy: :class:`StrokeShader` > :class:`CalligraphicShader`\n"
"\n"
"[Thickness Shader]\n"
"\n"
".. method:: __init__(iMinThickness, iMaxThickness, iOrientation, iClamp)\n"
"\n"
"   Builds a CalligraphicShader object.\n"
"\n"
"   :arg iMinThickness: The minimum thickness in the direction\n"
"      perpandicular to the main direction.\n"
"   :type iMinThickness: float\n"
"   :arg iMaxThickness: The maximum thickness in the main direction.\n"
"   :type iMaxThickness: float\n"
"   :arg iOrientation: The 2D vector giving the main direction.\n"
"   :type iOrientation: :class:`mathutils.Vector`\n"
"   :arg iClamp: If true, the strokes are drawn in black when the stroke\n"
"      direction is between -90 and 90 degrees with respect to the main\n"
"      direction and drawn in white otherwise.  If false, the strokes\n"
"      are always drawn in black.\n"
"   :type iClamp: bool\n"
"\n"
".. method:: shade(s)\n"
"\n"
"   Assigns thicknesses to the stroke vertices so that the stroke looks\n"
"   like made with a calligraphic tool, i.e. the stroke will be the\n"
"   thickest in a main direction, and the thinest in the direction\n"
"   perpendicular to this one, and an interpolation inbetween.\n"
"\n"
"   :arg s: A Stroke object.\n"
"   :type s: :class:`Stroke`\n";

static int CalligraphicShader___init__( BPy_CalligraphicShader* self, PyObject *args)
{
	double d1, d2;
	PyObject *obj3 = 0, *obj4 = 0;
	

	if(!( PyArg_ParseTuple(args, "ddOO", &d1, &d2, &obj3, &obj4) ))
		return -1;
	Vec2f *v = Vec2f_ptr_from_PyObject(obj3);
	if( !v ) {
		PyErr_SetString(PyExc_TypeError, "argument 3 must be a 2D vector (either a list of 2 elements or Vector)");
		return -1;
	}
	self->py_ss.ss = new CalligraphicShader(d1, d2, *v, bool_from_PyBool(obj4) );
	delete v;

	return 0;

}

/*-----------------------BPy_CalligraphicShader type definition ------------------------------*/

PyTypeObject CalligraphicShader_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"CalligraphicShader",           /* tp_name */
	sizeof(BPy_CalligraphicShader), /* tp_basicsize */
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
	CalligraphicShader___doc__,     /* tp_doc */
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
	(initproc)CalligraphicShader___init__, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
