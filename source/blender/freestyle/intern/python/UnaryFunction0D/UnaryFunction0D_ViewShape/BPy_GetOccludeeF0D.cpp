#include "BPy_GetOccludeeF0D.h"

#include "../../../view_map/Functions0D.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------INSTANCE METHODS ----------------------------------

static char GetOccludeeF0D___doc__[] =
"Class hierarchy: :class:`UnaryFunction0D` > :class:`UnaryFunction0DViewShape` > :class:`GetOccludeeF0D`\n"
"\n"
".. method:: __init__()\n"
"\n"
"   Builds a GetOccludeeF0D object.\n"
"\n"
".. method:: __call__(it)\n"
"\n"
"   Returns the :class:`ViewShape` that the Interface0D pointed by the\n"
"   Interface0DIterator occludes.\n"
"\n"
"   :arg it: An Interface0DIterator object.\n"
"   :type it: :class:`Interface0DIterator`\n"
"   :return: The ViewShape occluded by the pointed Interface0D.\n"
"   :rtype: :class:`ViewShape`\n";

static int GetOccludeeF0D___init__( BPy_GetOccludeeF0D* self, PyObject *args )
{
	if( !PyArg_ParseTuple(args, "") )
		return -1;
	self->py_uf0D_viewshape.uf0D_viewshape = new Functions0D::GetOccludeeF0D();
	self->py_uf0D_viewshape.uf0D_viewshape->py_uf0D = (PyObject *)self;
	return 0;
}

/*-----------------------BPy_GetOccludeeF0D type definition ------------------------------*/

PyTypeObject GetOccludeeF0D_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"GetOccludeeF0D",               /* tp_name */
	sizeof(BPy_GetOccludeeF0D),     /* tp_basicsize */
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
	GetOccludeeF0D___doc__,         /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	0,                              /* tp_methods */
	0,                              /* tp_members */
	0,                              /* tp_getset */
	&UnaryFunction0DViewShape_Type, /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)GetOccludeeF0D___init__, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
