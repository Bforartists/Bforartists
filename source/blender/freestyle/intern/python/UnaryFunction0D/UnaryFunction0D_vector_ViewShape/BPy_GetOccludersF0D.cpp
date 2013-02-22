#include "BPy_GetOccludersF0D.h"

#include "../../../view_map/Functions0D.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------INSTANCE METHODS ----------------------------------

static char GetOccludersF0D___doc__[] =
"Class hierarchy: :class:`UnaryFunction0D` > :class:`UnaryFunction0DVectorViewShape` > :class:`GetOccludersF0D`\n"
"\n"
".. method:: __init__()\n"
"\n"
"   Builds a GetOccludersF0D object.\n"
"\n"
".. method:: __call__(it)\n"
"\n"
"   Returns a list of :class:`ViewShape` objects occluding the\n"
"   :class:`Interface0D` pointed by the Interface0DIterator.\n"
"\n"
"   :arg it: An Interface0DIterator object.\n"
"   :type it: :class:`Interface0DIterator`\n"
"   :return: A list of ViewShape objects occluding the pointed\n"
"      Interface0D.\n"
"   :rtype: list of :class:`ViewShape` objects\n";

static int GetOccludersF0D___init__(BPy_GetOccludersF0D* self, PyObject *args, PyObject *kwds)
{
	static const char *kwlist[] = {NULL};

	if (!PyArg_ParseTupleAndKeywords(args, kwds, "", (char **)kwlist))
		return -1;
	self->py_uf0D_vectorviewshape.uf0D_vectorviewshape = new Functions0D::GetOccludersF0D();
	self->py_uf0D_vectorviewshape.uf0D_vectorviewshape->py_uf0D = (PyObject *)self;
	return 0;
}

/*-----------------------BPy_GetOccludersF0D type definition ------------------------------*/

PyTypeObject GetOccludersF0D_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"GetOccludersF0D",              /* tp_name */
	sizeof(BPy_GetOccludersF0D),    /* tp_basicsize */
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
	GetOccludersF0D___doc__,        /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	0,                              /* tp_methods */
	0,                              /* tp_members */
	0,                              /* tp_getset */
	&UnaryFunction0DVectorViewShape_Type, /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)GetOccludersF0D___init__, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
