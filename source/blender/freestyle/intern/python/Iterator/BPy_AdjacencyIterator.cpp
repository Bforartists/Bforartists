/*
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2010 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file source/blender/freestyle/intern/python/Iterator/BPy_AdjacencyIterator.cpp
 *  \ingroup freestyle
 */

#include "BPy_AdjacencyIterator.h"

#include "../BPy_Convert.h"
#include "../Interface0D/BPy_ViewVertex.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------INSTANCE METHODS ----------------------------------

PyDoc_STRVAR(AdjacencyIterator_doc,
"Class hierarchy: :class:`Iterator` > :class:`AdjacencyIterator`\n"
"\n"
"Class for representing adjacency iterators used in the chaining\n"
"process.  An AdjacencyIterator is created in the increment() and\n"
"decrement() methods of a :class:`ChainingIterator` and passed to the\n"
"traverse() method of the ChainingIterator.\n"
"\n"
".. method:: __init__()\n"
"\n"
"   Default constructor.\n"
"\n"
".. method:: __init__(brother)\n"
"\n"
"   Copy constructor.\n"
"\n"
"   :arg brother: An AdjacencyIterator object.\n"
"   :type brother: :class:`AdjacencyIterator`\n"
"\n"
".. method:: __init__(vertex, restrict_to_selection=True, restrict_to_unvisited=True)\n"
"\n"
"   Builds a AdjacencyIterator object.\n"
"\n"
"   :arg vertex: The vertex which is the next crossing.\n"
"   :type vertex: :class:`ViewVertex`\n"
"   :arg restrict_to_selection: Indicates whether to force the chaining\n"
"      to stay within the set of selected ViewEdges or not.\n"
"   :type restrict_to_selection: bool\n"
"   :arg restrict_to_unvisited: Indicates whether a ViewEdge that has\n"
"      already been chained must be ignored ot not.\n"
"   :type restrict_to_unvisited: bool");

static int AdjacencyIterator_init(BPy_AdjacencyIterator *self, PyObject *args, PyObject *kwds)
{
	static const char *kwlist_1[] = {"brother", NULL};
	static const char *kwlist_2[] = {"vertex", "restrict_to_selection", "restrict_to_unvisited", NULL};
	PyObject *obj1 = 0, *obj2 = 0, *obj3 = 0;

	if (PyArg_ParseTupleAndKeywords(args, kwds, "|O!", (char **)kwlist_1, &AdjacencyIterator_Type, &obj1)) {
		if (!obj1)
			self->a_it = new AdjacencyIterator();
		else 
			self->a_it = new AdjacencyIterator(*(((BPy_AdjacencyIterator *)obj1)->a_it));
	}
	else if (PyErr_Clear(), (obj2 = obj3 = 0),
	         PyArg_ParseTupleAndKeywords(args, kwds, "O!|O!O!", (char **)kwlist_2,
	                                     &ViewVertex_Type, &obj1, &PyBool_Type, &obj2, &PyBool_Type, &obj3))
	{
		bool restrictToSelection = (!obj2) ? true : bool_from_PyBool(obj2);
		bool restrictToUnvisited = (!obj3) ? true : bool_from_PyBool(obj3);
		self->a_it = new AdjacencyIterator(((BPy_ViewVertex *)obj1)->vv, restrictToSelection, restrictToUnvisited);
	}
	else {
		PyErr_SetString(PyExc_TypeError, "invalid argument(s)");
		return -1;
	}
	self->py_it.it = self->a_it;
	return 0;
}

static PyObject * AdjacencyIterator_iternext(BPy_AdjacencyIterator *self)
{
	if (self->a_it->isEnd()) {
		PyErr_SetNone(PyExc_StopIteration);
		return NULL;
	}
	ViewEdge *ve = self->a_it->operator*();
	self->a_it->increment();
	return BPy_ViewEdge_from_ViewEdge(*ve);
}

static PyMethodDef BPy_AdjacencyIterator_methods[] = {
	{NULL, NULL, 0, NULL}
};

/*----------------------AdjacencyIterator get/setters ----------------------------*/

PyDoc_STRVAR(AdjacencyIterator_object_doc,
"The ViewEdge object currently pointed by this iterator.\n"
"\n"
":type: :class:`ViewEdge`");

static PyObject *AdjacencyIterator_object_get(BPy_AdjacencyIterator *self, void *UNUSED(closure))
{
	ViewEdge *ve = self->a_it->operator*();
	if (ve)
		return BPy_ViewEdge_from_ViewEdge(*ve);

	Py_RETURN_NONE;
}

PyDoc_STRVAR(AdjacencyIterator_is_incoming_doc,
"True if the current ViewEdge is coming towards the iteration vertex, and\n"
"False otherwise.\n"
"\n"
":type: bool");

static PyObject *AdjacencyIterator_is_incoming_get(BPy_AdjacencyIterator *self, void *UNUSED(closure))
{
	return PyBool_from_bool(self->a_it->isIncoming());
}

static PyGetSetDef BPy_AdjacencyIterator_getseters[] = {
	{(char *)"is_incoming", (getter)AdjacencyIterator_is_incoming_get, (setter)NULL, (char *)AdjacencyIterator_is_incoming_doc, NULL},
	{(char *)"object", (getter)AdjacencyIterator_object_get, (setter)NULL, (char *)AdjacencyIterator_object_doc, NULL},
	{NULL, NULL, NULL, NULL, NULL}  /* Sentinel */
};

/*-----------------------BPy_AdjacencyIterator type definition ------------------------------*/

PyTypeObject AdjacencyIterator_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"AdjacencyIterator",            /* tp_name */
	sizeof(BPy_AdjacencyIterator),  /* tp_basicsize */
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
	AdjacencyIterator_doc,          /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	PyObject_SelfIter,              /* tp_iter */
	(iternextfunc)AdjacencyIterator_iternext, /* tp_iternext */
	BPy_AdjacencyIterator_methods,  /* tp_methods */
	0,                              /* tp_members */
	BPy_AdjacencyIterator_getseters, /* tp_getset */
	&Iterator_Type,                 /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)AdjacencyIterator_init, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
