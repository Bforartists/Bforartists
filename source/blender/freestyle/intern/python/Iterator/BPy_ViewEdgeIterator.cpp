#include "BPy_ViewEdgeIterator.h"

#include "../BPy_Convert.h"
#include "../Interface1D/BPy_ViewEdge.h"


#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------INSTANCE METHODS ----------------------------------

PyDoc_STRVAR(ViewEdgeIterator_doc,
"Class hierarchy: :class:`Iterator` > :class:`ViewEdgeIterator`\n"
"\n"
"Base class for iterators over ViewEdges of the :class:`ViewMap` Graph.\n"
"Basically the increment() operator of this class should be able to\n"
"take the decision of \"where\" (on which ViewEdge) to go when pointing\n"
"on a given ViewEdge.\n"
"\n"
".. method:: __init__(begin=None, orientation=True)\n"
"\n"
"   Builds a ViewEdgeIterator from a starting ViewEdge and its\n"
"   orientation.\n"
"\n"
"   :arg begin: The ViewEdge from where to start the iteration.\n"
"   :type begin: :class:`ViewEdge` or None\n"
"   :arg orientation: If true, we'll look for the next ViewEdge among\n"
"      the ViewEdges that surround the ending ViewVertex of begin.  If\n"
"      false, we'll search over the ViewEdges surrounding the ending\n"
"      ViewVertex of begin.\n"
"   :type orientation: bool\n"
"\n"
".. method:: __init__(it)\n"
"\n"
"   Copy constructor.\n"
"\n"
"   :arg it: A ViewEdgeIterator object.\n"
"   :type it: :class:`ViewEdgeIterator`");

static int ViewEdgeIterator_init(BPy_ViewEdgeIterator *self, PyObject *args)
{
	PyObject *obj1 = 0, *obj2 = 0;

	if (!PyArg_ParseTuple(args, "O|O", &obj1, &obj2))
		return -1;

	if (BPy_ViewEdgeIterator_Check(obj1)) {
		self->ve_it = new ViewEdgeInternal::ViewEdgeIterator(*(((BPy_ViewEdgeIterator *)obj1)->ve_it));

	} else {
		ViewEdge *begin;
		if (obj1 == Py_None)
			begin = NULL;
		else if (BPy_ViewEdge_Check(obj1))
			begin = ((BPy_ViewEdge *)obj1)->ve;
		else {
			PyErr_SetString(PyExc_TypeError, "1st argument must be either a ViewEdge object or None");
			return -1;
		}
		bool orientation = (obj2) ? bool_from_PyBool(obj2) : true;

		self->ve_it = new ViewEdgeInternal::ViewEdgeIterator(begin, orientation);
	}

	self->py_it.it = self->ve_it;

	return 0;
}

PyDoc_STRVAR(ViewEdgeIterator_change_orientation_doc,
".. method:: change_orientation()\n"
"\n"
"   Changes the current orientation.");

static PyObject *ViewEdgeIterator_change_orientation(BPy_ViewEdgeIterator *self)
{
	self->ve_it->changeOrientation();
	
	Py_RETURN_NONE;
}

static PyMethodDef BPy_ViewEdgeIterator_methods[] = {
	{"change_orientation", (PyCFunction) ViewEdgeIterator_change_orientation, METH_NOARGS, ViewEdgeIterator_change_orientation_doc},
	{NULL, NULL, 0, NULL}
};

/*----------------------ViewEdgeIterator get/setters ----------------------------*/

PyDoc_STRVAR(ViewEdgeIterator_object_doc,
"The ViewEdge object currently pointed by this iterator.\n"
"\n"
":type: :class:`ViewEdge`");

static PyObject *ViewEdgeIterator_object_get(BPy_ViewEdgeIterator *self, void *UNUSED(closure))
{
	ViewEdge *ve = self->ve_it->operator*();
	if (ve)
		return BPy_ViewEdge_from_ViewEdge(*ve);

	Py_RETURN_NONE;
}

PyDoc_STRVAR(ViewEdgeIterator_current_edge_doc,
"The ViewEdge object currently pointed by this iterator.\n"
"\n"
":type: :class:`ViewEdge`");

static PyObject *ViewEdgeIterator_current_edge_get(BPy_ViewEdgeIterator *self, void *UNUSED(closure))
{
	ViewEdge *ve = self->ve_it->getCurrentEdge();
	if (ve)
		return BPy_ViewEdge_from_ViewEdge(*ve);

	Py_RETURN_NONE;}

static int ViewEdgeIterator_current_edge_set(BPy_ViewEdgeIterator *self, PyObject *value, void *UNUSED(closure))
{
	if (!BPy_ViewEdge_Check(value)) {
		PyErr_SetString(PyExc_TypeError, "value must be a ViewEdge");
		return -1;
	}
	self->ve_it->setCurrentEdge(((BPy_ViewEdge *)value)->ve);
	return 0;
}

PyDoc_STRVAR(ViewEdgeIterator_orientation_doc,
"The orientation of the pointed ViewEdge in the iteration.\n"
"If true, the iterator looks for the next ViewEdge among those ViewEdges\n"
"that surround the ending ViewVertex of the \"begin\" ViewEdge.  If false,\n"
"the iterator searches over the ViewEdges surrounding the ending ViewVertex\n"
"of the \"begin\" ViewEdge.\n"
"\n"
":type: bool");

static PyObject *ViewEdgeIterator_orientation_get(BPy_ViewEdgeIterator *self, void *UNUSED(closure))
{
	return PyBool_from_bool(self->ve_it->getOrientation());
}

static int ViewEdgeIterator_orientation_set(BPy_ViewEdgeIterator *self, PyObject *value, void *UNUSED(closure))
{
	if (!PyBool_Check(value)) {
		PyErr_SetString(PyExc_TypeError, "value must be a boolean");
		return -1;
	}
	self->ve_it->setOrientation(bool_from_PyBool(value));
	return 0;
}

PyDoc_STRVAR(ViewEdgeIterator_begin_doc,
"The first ViewEdge used for the iteration.\n"
"\n"
":type: :class:`ViewEdge`");

static PyObject *ViewEdgeIterator_begin_get(BPy_ViewEdgeIterator *self, void *UNUSED(closure))
{
	ViewEdge *ve = self->ve_it->getBegin();
	if (ve)
		return BPy_ViewEdge_from_ViewEdge(*ve);

	Py_RETURN_NONE;
}

static int ViewEdgeIterator_begin_set(BPy_ViewEdgeIterator *self, PyObject *value, void *UNUSED(closure))
{
	if(!BPy_ViewEdge_Check(value)) {
		PyErr_SetString(PyExc_TypeError, "value must be a ViewEdge");
		return -1;
	}
	self->ve_it->setBegin(((BPy_ViewEdge *)value)->ve);
	return 0;
}

static PyGetSetDef BPy_ViewEdgeIterator_getseters[] = {
	{(char *)"object", (getter)ViewEdgeIterator_object_get, (setter)NULL, (char *)ViewEdgeIterator_object_doc, NULL},
	{(char *)"current_edge", (getter)ViewEdgeIterator_current_edge_get, (setter)ViewEdgeIterator_current_edge_set, (char *)ViewEdgeIterator_current_edge_doc, NULL},
	{(char *)"orientation", (getter)ViewEdgeIterator_orientation_get, (setter)ViewEdgeIterator_orientation_set, (char *)ViewEdgeIterator_orientation_doc, NULL},
	{(char *)"begin", (getter)ViewEdgeIterator_begin_get, (setter)ViewEdgeIterator_begin_set, (char *)ViewEdgeIterator_begin_doc, NULL},
	{NULL, NULL, NULL, NULL, NULL}  /* Sentinel */
};

/*-----------------------BPy_ViewEdgeIterator type definition ------------------------------*/

PyTypeObject ViewEdgeIterator_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"ViewEdgeIterator",             /* tp_name */
	sizeof(BPy_ViewEdgeIterator),   /* tp_basicsize */
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
	ViewEdgeIterator_doc,           /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	BPy_ViewEdgeIterator_methods,   /* tp_methods */
	0,                              /* tp_members */
	BPy_ViewEdgeIterator_getseters, /* tp_getset */
	&Iterator_Type,                 /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)ViewEdgeIterator_init, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
