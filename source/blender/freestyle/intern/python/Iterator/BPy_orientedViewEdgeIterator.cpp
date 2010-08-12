#include "BPy_orientedViewEdgeIterator.h"

#include "../BPy_Convert.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------INSTANCE METHODS ----------------------------------

static char orientedViewEdgeIterator___doc__[] =
"Class hierarchy: :class:`Iterator` > :class:`orientedViewEdgeIterator`\n"
"\n"
"Class representing an iterator over oriented ViewEdges around a\n"
":class:`ViewVertex`.  This iterator allows a CCW iteration (in the image\n"
"plane).  An instance of an orientedViewEdgeIterator can only be\n"
"obtained from a ViewVertex by calling edgesBegin() or edgesEnd().\n"
"\n"
".. method:: __init__()\n"
"\n"
"   Default constructor.\n"
"\n"
".. method:: __init__(iBrother)\n"
"\n"
"   Copy constructor.\n"
"\n"
"   :arg iBrother: An orientedViewEdgeIterator object.\n"
"   :type iBrother: :class:`orientedViewEdgeIterator`\n";

static int orientedViewEdgeIterator___init__(BPy_orientedViewEdgeIterator *self, PyObject *args )
{	
	PyObject *obj = 0;

	if (!( PyArg_ParseTuple(args, "|O", &obj) ))
	    return -1;

	if( !obj )
		self->ove_it = new ViewVertexInternal::orientedViewEdgeIterator();
	else if( BPy_orientedViewEdgeIterator_Check(obj) )
		self->ove_it = new ViewVertexInternal::orientedViewEdgeIterator(*( ((BPy_orientedViewEdgeIterator *) obj)->ove_it ));
	else {
		PyErr_SetString(PyExc_TypeError, "invalid argument");
		return -1;
	}
	
	self->py_it.it = self->ove_it;
	self->reversed = 0;
	
	return 0;
}

static PyObject * orientedViewEdgeIterator_iternext( BPy_orientedViewEdgeIterator *self ) {
	ViewVertex::directedViewEdge *dve;
	if (self->reversed) {
		if (self->ove_it->isBegin()) {
			PyErr_SetNone(PyExc_StopIteration);
			return NULL;
		}
		self->ove_it->decrement();
		dve = self->ove_it->operator->();
	} else {
		if (self->ove_it->isEnd()) {
			PyErr_SetNone(PyExc_StopIteration);
			return NULL;
		}
		dve = self->ove_it->operator->();
		self->ove_it->increment();
	}
	return BPy_directedViewEdge_from_directedViewEdge( *dve );
}

static char orientedViewEdgeIterator_getObject___doc__[] =
".. method:: getObject()\n"
"\n"
"   Returns the pointed oriented ViewEdge.\n"
"\n"
"   :return: A tuple of the pointed ViewEdge and a boolean value.  If\n"
"      the boolean value is true, the ViewEdge is incoming.\n"
"   :rtype: (:class:`directedViewEdge`, bool)\n";

static PyObject * orientedViewEdgeIterator_getObject( BPy_orientedViewEdgeIterator *self) {
	return BPy_directedViewEdge_from_directedViewEdge( self->ove_it->operator*() );
}

/*----------------------orientedViewEdgeIterator instance definitions ----------------------------*/
static PyMethodDef BPy_orientedViewEdgeIterator_methods[] = {
	{"getObject", ( PyCFunction ) orientedViewEdgeIterator_getObject, METH_NOARGS, orientedViewEdgeIterator_getObject___doc__},
	{NULL, NULL, 0, NULL}
};

/*-----------------------BPy_orientedViewEdgeIterator type definition ------------------------------*/

PyTypeObject orientedViewEdgeIterator_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"orientedViewEdgeIterator",     /* tp_name */
	sizeof(BPy_orientedViewEdgeIterator), /* tp_basicsize */
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
	orientedViewEdgeIterator___doc__, /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	PyObject_SelfIter,              /* tp_iter */
	(iternextfunc)orientedViewEdgeIterator_iternext, /* tp_iternext */
	BPy_orientedViewEdgeIterator_methods, /* tp_methods */
	0,                              /* tp_members */
	0,                              /* tp_getset */
	&Iterator_Type,                 /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)orientedViewEdgeIterator___init__, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
