#include "BPy_ExternalContourUP1D.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------INSTANCE METHODS ----------------------------------

static char ExternalContourUP1D___doc__[] =
"Class hierarchy: :class:`UnaryPredicate1D` > :class:`ExternalContourUP1D`\n"
"\n"
".. method:: __call__(inter)\n"
"\n"
"   Returns true if the Interface1D is an external contour.  An\n"
"   Interface1D is an external contour if it is borded by no shape on\n"
"   one of its sides.\n"
"\n"
"   :arg inter: An Interface1D object.\n"
"   :type inter: :class:`Interface1D`\n"
"   :return: True if the Interface1D is an external contour, false\n"
"      otherwise.\n"
"   :rtype: bool\n";

static int ExternalContourUP1D___init__(BPy_ExternalContourUP1D* self, PyObject *args, PyObject *kwds)
{
	static const char *kwlist[] = {NULL};

	if (!PyArg_ParseTupleAndKeywords(args, kwds, "", (char **)kwlist))
		return -1;
	self->py_up1D.up1D = new Predicates1D::ExternalContourUP1D();
	return 0;
}

/*-----------------------BPy_ExternalContourUP1D type definition ------------------------------*/

PyTypeObject ExternalContourUP1D_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"ExternalContourUP1D",          /* tp_name */
	sizeof(BPy_ExternalContourUP1D), /* tp_basicsize */
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
	ExternalContourUP1D___doc__,    /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	0,                              /* tp_methods */
	0,                              /* tp_members */
	0,                              /* tp_getset */
	&UnaryPredicate1D_Type,         /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)ExternalContourUP1D___init__, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
