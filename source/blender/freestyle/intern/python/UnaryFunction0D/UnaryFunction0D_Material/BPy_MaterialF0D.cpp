#include "BPy_MaterialF0D.h"

#include "../../../view_map/Functions0D.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------INSTANCE METHODS ----------------------------------

static char MaterialF0D___doc__[] =
"Class hierarchy: :class:`UnaryFunction0D` > :class:`UnaryFunction0DMaterial` > :class:`MaterialF0D`\n"
"\n"
".. method:: __init__()\n"
"\n"
"   Builds a MaterialF0D object.\n"
"\n"
".. method:: __call__(it)\n"
"\n"
"   Returns the material of the object evaluated at the\n"
"   :class:`Interface0D` pointed by the Interface0DIterator.  This\n"
"   evaluation can be ambiguous (in the case of a :class:`TVertex` for\n"
"   example.  This functor tries to remove this ambiguity using the\n"
"   context offered by the 1D element to which the Interface0DIterator\n"
"   belongs to and by arbitrary chosing the material of the face that\n"
"   lies on its left when following the 1D element if there are two\n"
"   different materials on each side of the point.  However, there\n"
"   still can be problematic cases, and the user willing to deal with\n"
"   this cases in a specific way should implement its own getMaterial\n"
"   functor.\n"
"\n"
"   :arg it: An Interface0DIterator object.\n"
"   :type it: :class:`Interface0DIterator`\n"
"   :return: The material of the object evaluated at the pointed\n"
"      Interface0D.\n"
"   :rtype: :class:`Material`\n";

static int MaterialF0D___init__(BPy_MaterialF0D* self, PyObject *args, PyObject *kwds)
{
	static const char *kwlist[] = {NULL};

	if (!PyArg_ParseTupleAndKeywords(args, kwds, "", (char **)kwlist))
		return -1;
	self->py_uf0D_material.uf0D_material = new Functions0D::MaterialF0D();
	self->py_uf0D_material.uf0D_material->py_uf0D = (PyObject *)self;
	return 0;
}

/*-----------------------BPy_MaterialF0D type definition ------------------------------*/

PyTypeObject MaterialF0D_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"MaterialF0D",                  /* tp_name */
	sizeof(BPy_MaterialF0D),        /* tp_basicsize */
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
	MaterialF0D___doc__,            /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	0,                              /* tp_methods */
	0,                              /* tp_members */
	0,                              /* tp_getset */
	&UnaryFunction0DMaterial_Type,  /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)MaterialF0D___init__, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
