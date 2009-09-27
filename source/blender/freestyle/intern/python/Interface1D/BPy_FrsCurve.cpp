#include "BPy_FrsCurve.h"

#include "../BPy_Convert.h"
#include "../BPy_Id.h"
#include "../Interface0D/BPy_CurvePoint.h"
#include "../Interface0D/BPy_SVertex.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

/*---------------  Python API function prototypes for FrsCurve instance  -----------*/
static int FrsCurve___init__(BPy_FrsCurve *self, PyObject *args, PyObject *kwds);
static PyObject * FrsCurve_push_vertex_back( BPy_FrsCurve *self, PyObject *args );
static PyObject * FrsCurve_push_vertex_front( BPy_FrsCurve *self, PyObject *args );
static PyObject * FrsCurve_empty( BPy_FrsCurve *self );
static PyObject * FrsCurve_nSegments( BPy_FrsCurve *self );
// point_iterator 	points_begin (float step=0)
static PyObject * FrsCurve_verticesBegin( BPy_FrsCurve *self );
static PyObject * FrsCurve_verticesEnd( BPy_FrsCurve *self );
static PyObject * FrsCurve_pointsBegin( BPy_FrsCurve *self, PyObject *args );
static PyObject * FrsCurve_pointsEnd( BPy_FrsCurve *self, PyObject *args );

/*----------------------FrsCurve instance definitions ----------------------------*/
static PyMethodDef BPy_FrsCurve_methods[] = {	
	{"push_vertex_back", ( PyCFunction ) FrsCurve_push_vertex_back, METH_VARARGS, "(CurvePoint cp | SVertex sv) Adds a single vertex at the front of the Curve."},
	{"push_vertex_front", ( PyCFunction ) FrsCurve_push_vertex_front, METH_VARARGS, "(CurvePoint cp | SVertex sv) Adds a single vertex at the end of the Curve."},
	{"empty", ( PyCFunction ) FrsCurve_empty, METH_NOARGS, "() Returns true is the Curve doesn't have any Vertex yet."},
	{"nSegments", ( PyCFunction ) FrsCurve_nSegments, METH_NOARGS, "() Returns the number of segments in the oplyline constituing the Curve."},
	{"verticesBegin", ( PyCFunction ) FrsCurve_verticesBegin, METH_NOARGS, "() Returns an Interface0DIterator pointing onto the first vertex of the Curve and that can iterate over the vertices of the Curve."},
	{"verticesEnd", ( PyCFunction ) FrsCurve_verticesEnd, METH_NOARGS, "() Returns an Interface0DIterator pointing after the last vertex of the Curve and that can iterate over the vertices of the Curve."},
	{"pointsBegin", ( PyCFunction ) FrsCurve_pointsBegin, METH_VARARGS, "(float t=0) Returns an Interface0DIterator pointing onto the first point of the Curve and that can iterate over the points of the Curve at any resolution t. At each iteration a virtual temporary CurvePoint is created."},
	{"pointsEnd", ( PyCFunction ) FrsCurve_pointsEnd, METH_VARARGS, "(float t=0) Returns an Interface0DIterator pointing after the last point of the Curve and that can iterate over the points of the Curve at any resolution t. At each iteration a virtual temporary CurvePoint is created."},
	{NULL, NULL, 0, NULL}
};

/*-----------------------BPy_FrsCurve type definition ------------------------------*/

PyTypeObject FrsCurve_Type = {
	PyObject_HEAD_INIT(NULL)
	"FrsCurve",                     /* tp_name */
	sizeof(BPy_FrsCurve),           /* tp_basicsize */
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
	"FrsCurve objects",             /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	BPy_FrsCurve_methods,           /* tp_methods */
	0,                              /* tp_members */
	0,                              /* tp_getset */
	&Interface1D_Type,              /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)FrsCurve___init__,    /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

//------------------------INSTANCE METHODS ----------------------------------
	
int FrsCurve___init__(BPy_FrsCurve *self, PyObject *args, PyObject *kwds)
{

	PyObject *obj = 0;

    if (! PyArg_ParseTuple(args, "|O", &obj) )
        return -1;

	if( !obj ){
		self->c = new Curve();
		
	} else if( BPy_FrsCurve_Check(obj) ) {
		self->c = new Curve(*( ((BPy_FrsCurve *) obj)->c ));
		
	} else if( BPy_Id_Check(obj) ) {
		self->c = new Curve(*( ((BPy_Id *) obj)->id ));
			
	} else {
		PyErr_SetString(PyExc_TypeError, "invalid argument");
		return -1;
	}

	self->py_if1D.if1D = self->c;
	self->py_if1D.borrowed = 0;

	return 0;
}


PyObject * FrsCurve_push_vertex_back( BPy_FrsCurve *self, PyObject *args ) {
	PyObject *obj;

	if(!( PyArg_ParseTuple(args, "O", &obj) ))
		return NULL;

	if( BPy_CurvePoint_Check(obj) ) {
		self->c->push_vertex_back( ((BPy_CurvePoint *) obj)->cp );
	} else if( BPy_SVertex_Check(obj) ) {
		self->c->push_vertex_back( ((BPy_SVertex *) obj)->sv );
	} else {
		PyErr_SetString(PyExc_TypeError, "invalid argument");
		return NULL;
	}

	Py_RETURN_NONE;
}

PyObject * FrsCurve_push_vertex_front( BPy_FrsCurve *self, PyObject *args ) {
	PyObject *obj;

	if(!( PyArg_ParseTuple(args, "O", &obj) ))
		return NULL;

	if( BPy_CurvePoint_Check(obj) ) {
		self->c->push_vertex_front( ((BPy_CurvePoint *) obj)->cp );
	} else if( BPy_SVertex_Check(obj) ) {
		self->c->push_vertex_front( ((BPy_SVertex *) obj)->sv );
	} else {
		PyErr_SetString(PyExc_TypeError, "invalid argument");
		return NULL;
	}

	Py_RETURN_NONE;
}

PyObject * FrsCurve_empty( BPy_FrsCurve *self ) {
	return PyBool_from_bool( self->c->empty() );
}

PyObject * FrsCurve_nSegments( BPy_FrsCurve *self ) {
	return PyLong_FromLong( self->c->nSegments() );
}

// point_iterator 	points_begin (float step=0)
// not implemented


PyObject * FrsCurve_verticesBegin( BPy_FrsCurve *self ) {
	Interface0DIterator if0D_it( self->c->verticesBegin() );
	return BPy_Interface0DIterator_from_Interface0DIterator( if0D_it, 0 );
}

PyObject * FrsCurve_verticesEnd( BPy_FrsCurve *self ) {
	Interface0DIterator if0D_it( self->c->verticesEnd() );
	return BPy_Interface0DIterator_from_Interface0DIterator( if0D_it, 1 );
}


PyObject * FrsCurve_pointsBegin( BPy_FrsCurve *self, PyObject *args ) {
	float f = 0;

	if(!( PyArg_ParseTuple(args, "|f", &f)  ))
		return NULL;
	
	Interface0DIterator if0D_it( self->c->pointsBegin(f) );
	return BPy_Interface0DIterator_from_Interface0DIterator( if0D_it, 0 );
}

PyObject * FrsCurve_pointsEnd( BPy_FrsCurve *self, PyObject *args ) {
	float f = 0;

	if(!( PyArg_ParseTuple(args, "|f", &f)  ))
		return NULL;
	
	Interface0DIterator if0D_it( self->c->pointsEnd(f) );
	return BPy_Interface0DIterator_from_Interface0DIterator( if0D_it, 1 );
}



///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
