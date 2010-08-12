#include "BPy_GetOccludersF1D.h"

#include "../../../view_map/Functions1D.h"
#include "../../BPy_Convert.h"
#include "../../BPy_IntegrationType.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------INSTANCE METHODS ----------------------------------

static char GetOccludersF1D___doc__[] =
"Class hierarchy: :class:`UnaryFunction1D` > :class:`UnaryFunction1DVectorViewShape` > :class:`GetOccludersF1D`\n"
"\n"
".. method:: __init__()\n"
"\n"
"   Builds a GetOccludersF1D object.\n"
"\n"
".. method:: __call__(inter)\n"
"\n"
"   Returns a list of occluding shapes that cover this Interface1D.\n"
"\n"
"   :arg inter: An Interface1D object.\n"
"   :type inter: :class:`Interface1D`\n"
"   :return: A list of occluding shapes that cover the Interface1D.\n"
"   :rtype: list of :class:`ViewShape` objects\n";

static int GetOccludersF1D___init__( BPy_GetOccludersF1D* self, PyObject *args )
{
	if( !PyArg_ParseTuple(args, "") )
		return -1;
	self->py_uf1D_vectorviewshape.uf1D_vectorviewshape = new Functions1D::GetOccludersF1D();
	return 0;
}

/*-----------------------BPy_GetOccludersF1D type definition ------------------------------*/

PyTypeObject GetOccludersF1D_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"GetOccludersF1D",              /* tp_name */
	sizeof(BPy_GetOccludersF1D),    /* tp_basicsize */
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
	GetOccludersF1D___doc__,        /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	0,                              /* tp_methods */
	0,                              /* tp_members */
	0,                              /* tp_getset */
	&UnaryFunction1DVectorViewShape_Type, /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)GetOccludersF1D___init__, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
