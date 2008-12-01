#include "BPy_Stroke.h"

#include "../BPy_Convert.h"
#include "../BPy_Id.h"
#include "../Interface0D/BPy_SVertex.h"
#include "../Interface0D/CurvePoint/BPy_StrokeVertex.h"
#include "../Iterator/BPy_StrokeVertexIterator.h"
#include "../BPy_MediumType.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

/*---------------  Python API function prototypes for Stroke instance  -----------*/
static int Stroke___init__(BPy_Stroke *self, PyObject *args, PyObject *kwds);
static PyObject * Stroke___iter__(PyObject *self);

static Py_ssize_t Stroke_length( BPy_Stroke *self );
static PyObject * Stroke_item( BPy_Stroke *self, Py_ssize_t i );
static PyObject * Stroke___getitem__( BPy_Stroke *self, PyObject *item );

static PyObject * Stroke_ComputeSampling( BPy_Stroke *self, PyObject *args );
static PyObject * Stroke_Resample( BPy_Stroke *self, PyObject *args );
static PyObject * Stroke_InsertVertex( BPy_Stroke *self, PyObject *args );
static PyObject * Stroke_RemoveVertex( BPy_Stroke *self, PyObject *args );
static PyObject * Stroke_getMediumType( BPy_Stroke *self );
static PyObject * Stroke_getTextureId( BPy_Stroke *self );
static PyObject * Stroke_hasTips( BPy_Stroke *self );
static PyObject * Stroke_setId( BPy_Stroke *self , PyObject *args);
static PyObject * Stroke_setLength( BPy_Stroke *self , PyObject *args);
static PyObject * Stroke_setMediumType( BPy_Stroke *self , PyObject *args);
static PyObject * Stroke_setTextureId( BPy_Stroke *self , PyObject *args);
static PyObject * Stroke_setTips( BPy_Stroke *self , PyObject *args);
static PyObject * Stroke_strokeVerticesBegin( BPy_Stroke *self , PyObject *args);
static PyObject * Stroke_strokeVerticesEnd( BPy_Stroke *self );
static PyObject * Stroke_strokeVerticesSize( BPy_Stroke *self );
static PyObject * Stroke_verticesBegin( BPy_Stroke *self );
static PyObject * Stroke_verticesEnd( BPy_Stroke *self );
static PyObject * Stroke_pointsBegin( BPy_Stroke *self , PyObject *args);
static PyObject * Stroke_pointsEnd( BPy_Stroke *self , PyObject *args);

/*----------------------Stroke instance definitions ----------------------------*/
static PyMethodDef BPy_Stroke_methods[] = {	
	{"__getitem__", ( PyCFunction ) Stroke___getitem__, METH_O, "(int i) Returns the i-th StrokeVertex constituting the Stroke."},
	{"ComputeSampling", ( PyCFunction ) Stroke_ComputeSampling, METH_VARARGS, "(int nVertices) Compute the sampling needed to get nVertices vertices. If the specified number of vertices is less than the actual number of vertices, the actual sampling value is returned."},
		{"Resample", ( PyCFunction ) Stroke_Resample, METH_VARARGS, "(float f | int n) Resampling method. If the argument is a float, Resamples the curve with a given sampling; if this sampling is < to the actual sampling value, no resampling is done. If the argument is an integer, Resamples the curve so that it eventually has n. That means it is going to add n-vertices_size, if vertices_size is the number of points we already have. Is vertices_size >= n, no resampling is done."},
	{"RemoveVertex", ( PyCFunction ) Stroke_RemoveVertex, METH_VARARGS, "(StrokeVertex sv) Removes the stroke vertex sv from the stroke. The length and curvilinear abscissa are updated consequently."},
	{"InsertVertex", ( PyCFunction ) Stroke_InsertVertex, METH_VARARGS, "(StrokeVertex sv, StrokeVertexIterator next) Inserts the stroke vertex iVertex in the stroke before next. The length, curvilinear abscissa are updated consequently."},
	{"getMediumType", ( PyCFunction ) Stroke_getMediumType, METH_NOARGS, "() Returns the MediumType used for this Stroke."},
	{"getTextureId", ( PyCFunction ) Stroke_getTextureId, METH_NOARGS, "() Returns the id of the texture used to simulate th marks system for this Stroke."},
	{"hasTips", ( PyCFunction ) Stroke_hasTips, METH_NOARGS, "() Returns true if this Stroke uses a texture with tips, false otherwise."},
	{"setId", ( PyCFunction ) Stroke_setId, METH_VARARGS, "(Id id) Sets the Id of the Stroke."},
	{"setLength", ( PyCFunction ) Stroke_setLength, METH_VARARGS, "(float l) Sets the 2D length of the Stroke."},
	{"setMediumType", ( PyCFunction ) Stroke_setMediumType, METH_VARARGS, "(MediumType mt) Sets the medium type that must be used for this Stroke."},
	{"setTextureId", ( PyCFunction ) Stroke_setTextureId, METH_VARARGS, "(unsigned int id) Sets the texture id to be used to simulate the marks system for this Stroke."},
	{"setTips", ( PyCFunction ) Stroke_setTips, METH_VARARGS, "(bool b) Sets the flag telling whether this stroke is using a texture with tips or not."},
	{"strokeVerticesBegin", ( PyCFunction ) Stroke_strokeVerticesBegin, METH_VARARGS, "(float t=0.f) Returns a StrokeVertexIterator pointing on the first StrokeVertex of the Stroke. One can specifly a sampling value t to resample the Stroke on the fly if needed. "},
	{"strokeVerticesEnd", ( PyCFunction ) Stroke_strokeVerticesEnd, METH_NOARGS, "() Returns a StrokeVertexIterator pointing after the last StrokeVertex of the Stroke."},
	{"strokeVerticesSize", ( PyCFunction ) Stroke_strokeVerticesSize, METH_NOARGS, "() Returns the number of StrokeVertex constituing the Stroke."},
	{"verticesBegin", ( PyCFunction ) Stroke_verticesBegin, METH_NOARGS, "() Returns an Interface0DIterator pointing on the first StrokeVertex of the Stroke. "},
	{"verticesEnd", ( PyCFunction ) Stroke_verticesEnd, METH_NOARGS, "() Returns an Interface0DIterator pointing after the last StrokeVertex of the Stroke. "},
	{"pointsBegin", ( PyCFunction ) Stroke_pointsBegin, METH_VARARGS, "(float t=0.f) Returns an iterator over the Interface1D points, pointing to the first point. The difference with verticesBegin() is that here we can iterate over points of the 1D element at a any given sampling t. Indeed, for each iteration, a virtual point is created. "},
	{"pointsEnd", ( PyCFunction ) Stroke_pointsEnd, METH_VARARGS, "(float t=0.f) Returns an iterator over the Interface1D points, pointing after the last point. The difference with verticesEnd() is that here we can iterate over points of the 1D element at a any given sampling t. Indeed, for each iteration, a virtual point is created. "},

	{NULL, NULL, 0, NULL}
};

/*-----------------------BPy_Stroke type definition ------------------------------*/

static PySequenceMethods Stroke_as_sequence = {
	(lenfunc)Stroke_length,		/* sq_length */
	NULL,						/* sq_concat */
	NULL,						/* sq_repeat */
	(ssizeargfunc)Stroke_item,	/* sq_item */
	NULL,						/* sq_slice */
	NULL,						/* sq_ass_item */
	NULL,						/* sq_ass_slice */
	NULL,						/* sq_contains */
	NULL,						/* sq_inplace_concat */
	NULL,						/* sq_inplace_repeat */
};

PyTypeObject Stroke_Type = {
	PyObject_HEAD_INIT( NULL ) 
	0,							/* ob_size */
	"Stroke",				/* tp_name */
	sizeof( BPy_Stroke ),	/* tp_basicsize */
	0,							/* tp_itemsize */
	
	/* methods */
	NULL,	/* tp_dealloc */
	NULL,                       				/* printfunc tp_print; */
	NULL,                       				/* getattrfunc tp_getattr; */
	NULL,                       				/* setattrfunc tp_setattr; */
	NULL,										/* tp_compare */
	NULL,					/* tp_repr */

	/* Method suites for standard classes */

	NULL,                       /* PyNumberMethods *tp_as_number; */
	&Stroke_as_sequence,        /* PySequenceMethods *tp_as_sequence; */
	NULL,                       /* PyMappingMethods *tp_as_mapping; */

	/* More standard operations (here for binary compatibility) */

	NULL,						/* hashfunc tp_hash; */
	NULL,                       /* ternaryfunc tp_call; */
	NULL,                       /* reprfunc tp_str; */
	NULL,                       /* getattrofunc tp_getattro; */
	NULL,                       /* setattrofunc tp_setattro; */

	/* Functions to access object as input/output buffer */
	NULL,                       /* PyBufferProcs *tp_as_buffer; */

  /*** Flags to define presence of optional/expanded features ***/
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, 		/* long tp_flags; */

	NULL,                       /*  char *tp_doc;  Documentation string */
  /*** Assigned meaning in release 2.0 ***/
	/* call function for all accessible objects */
	NULL,                       /* traverseproc tp_traverse; */

	/* delete references to contained objects */
	NULL,                       /* inquiry tp_clear; */

  /***  Assigned meaning in release 2.1 ***/
  /*** rich comparisons ***/
	NULL,                       /* richcmpfunc tp_richcompare; */

  /***  weak reference enabler ***/
	0,                          /* long tp_weaklistoffset; */

  /*** Added in release 2.2 ***/
	/*   Iterators */
	Stroke___iter__,            /* getiterfunc tp_iter; */
	NULL,                       /* iternextfunc tp_iternext; */

  /*** Attribute descriptor and subclassing stuff ***/
	BPy_Stroke_methods,	/* struct PyMethodDef *tp_methods; */
	NULL,                       	/* struct PyMemberDef *tp_members; */
	NULL,         					/* struct PyGetSetDef *tp_getset; */
	&Interface1D_Type,				/* struct _typeobject *tp_base; */
	NULL,							/* PyObject *tp_dict; */
	NULL,							/* descrgetfunc tp_descr_get; */
	NULL,							/* descrsetfunc tp_descr_set; */
	0,                          	/* long tp_dictoffset; */
	(initproc)Stroke___init__,                       	/* initproc tp_init; */
	NULL,							/* allocfunc tp_alloc; */
	NULL,		/* newfunc tp_new; */
	
	/*  Low-level free-memory routine */
	NULL,                       /* freefunc tp_free;  */
	
	/* For PyObject_IS_GC */
	NULL,                       /* inquiry tp_is_gc;  */
	NULL,                       /* PyObject *tp_bases; */
	
	/* method resolution order */
	NULL,                       /* PyObject *tp_mro;  */
	NULL,                       /* PyObject *tp_cache; */
	NULL,                       /* PyObject *tp_subclasses; */
	NULL,                       /* PyObject *tp_weaklist; */
	NULL
};

//-------------------MODULE INITIALIZATION--------------------------------


//------------------------INSTANCE METHODS ----------------------------------

// Stroke ()
// template<class InputVertexIterator> Stroke (InputVertexIterator iBegin, InputVertexIterator iEnd)
//
// pb: - need to be able to switch representation: InputVertexIterator <=> position
//     - is it even used ? not even in SWIG version

int Stroke___init__(BPy_Stroke *self, PyObject *args, PyObject *kwds)
{
	PyObject *obj1 = NULL, *obj2 = NULL;

	if (! PyArg_ParseTuple(args, "|OO", &obj1, &obj2) )
        return -1;

	if( !obj1 && !obj2 ){
		self->s = new Stroke();
	} else if ( obj1 && !obj2 ) {
		if (! BPy_Stroke_Check(obj1) ) {
			PyErr_SetString(PyExc_TypeError, "not a Stroke object");
			return -1;
		}
		self->s = new Stroke(*( ((BPy_Stroke *)obj1)->s ));
	} else {
		PyErr_SetString(PyExc_NotImplementedError,
			"Stroke(InputVertexIterator iBegin, InputVertexIterator iEnd) not implemented");
		return -1;
	}

	self->py_if1D.if1D = self->s;

	return 0;
}

PyObject * Stroke___iter__( PyObject *self ) {
	StrokeInternal::StrokeVertexIterator sv_it( ((BPy_Stroke *)self)->s->strokeVerticesBegin() );
	return BPy_StrokeVertexIterator_from_StrokeVertexIterator( sv_it, 0 );
}

Py_ssize_t Stroke_length( BPy_Stroke *self ) {
	return self->s->strokeVerticesSize();
}

PyObject * Stroke_item( BPy_Stroke *self, Py_ssize_t i ) {
	if (i < 0 || i >= (Py_ssize_t)self->s->strokeVerticesSize()) {
		PyErr_SetString(PyExc_IndexError, "subscript index out of range");
		return NULL;
	}
	return BPy_StrokeVertex_from_StrokeVertex_ptr( self->s->strokeVerticeAt(i) );
}

PyObject * Stroke___getitem__( BPy_Stroke *self, PyObject *item ) {
	long i;

	if (PyInt_Check(item)) {
		i = PyInt_AS_LONG(item);
	} else if (PyLong_Check(item)) {
		i = PyLong_AsLong(item);
		if (i == -1 && PyErr_Occurred())
			return NULL;
	} else {
		PyErr_SetString(PyExc_TypeError, "subscript indices must be integers");
		return NULL;
	}
	if (i < 0) {
		i += self->s->strokeVerticesSize();
	}
	return Stroke_item(self, i);
}

PyObject * Stroke_ComputeSampling( BPy_Stroke *self, PyObject *args ) {	
	int i;

	if(!( PyArg_ParseTuple(args, "i", &i)  )) {
		cout << "ERROR: Stroke_ComputeSampling" << endl;
		Py_RETURN_NONE;
	}

	return PyFloat_FromDouble( self->s->ComputeSampling( i ) );
}

PyObject * Stroke_Resample( BPy_Stroke *self, PyObject *args ) {	
	PyObject *obj;

	if(!( PyArg_ParseTuple(args, "O", &obj) )) {
		cout << "ERROR: Stroke_Resample" << endl;
		Py_RETURN_NONE;
	}

	if( PyInt_Check(obj) )
		self->s->Resample( (int) PyInt_AsLong(obj) );
	else if( PyFloat_Check(obj) )
		self->s->Resample( (float) PyFloat_AsDouble(obj) );
		
	Py_RETURN_NONE;
}

PyObject * Stroke_InsertVertex( BPy_Stroke *self, PyObject *args ) {
	PyObject *py_sv = 0, *py_sv_it = 0;

	if(!( PyArg_ParseTuple(args, "OO", &py_sv, &py_sv_it) &&
			BPy_StrokeVertex_Check(py_sv) && BPy_StrokeVertexIterator_Check(py_sv_it) )) {
		cout << "ERROR: Stroke_InsertVertex" << endl;
		Py_RETURN_NONE;
	}

	StrokeVertex *sv = ((BPy_StrokeVertex *) py_sv)->sv;
	StrokeInternal::StrokeVertexIterator sv_it(*( ((BPy_StrokeVertexIterator *) py_sv_it)->sv_it ));
	self->s->InsertVertex( sv, sv_it );

	Py_RETURN_NONE;
}

PyObject * Stroke_RemoveVertex( BPy_Stroke *self, PyObject *args ) {	
	PyObject *py_sv;

	if(!( PyArg_ParseTuple(args, "O", &py_sv) )) {
		cout << "ERROR: Stroke_RemoveVertex" << endl;
		Py_RETURN_NONE;
	}

	if( BPy_StrokeVertex_Check(py_sv) && ((BPy_StrokeVertex *) py_sv)->sv )
		self->s->RemoveVertex( ((BPy_StrokeVertex *) py_sv)->sv );
		
	Py_RETURN_NONE;
}

PyObject * Stroke_getMediumType( BPy_Stroke *self ) {	
	return BPy_MediumType_from_MediumType( self->s->getMediumType() );
}

PyObject * Stroke_getTextureId( BPy_Stroke *self ) {	
	return PyInt_FromLong( self->s->getTextureId() );
}

PyObject * Stroke_hasTips( BPy_Stroke *self ) {	
	return PyBool_from_bool( self->s->hasTips() );
}


PyObject *Stroke_setId( BPy_Stroke *self , PyObject *args) {
	PyObject *py_id;

	if(!( PyArg_ParseTuple(args, "O", &py_id) && BPy_Id_Check(py_id)  )) {
		cout << "ERROR: Stroke_setId" << endl;
		Py_RETURN_NONE;
	}

	if( ((BPy_Id *) py_id)->id )
		self->s->setId(*( ((BPy_Id *) py_id)->id ));

	Py_RETURN_NONE;
}

PyObject *Stroke_setLength( BPy_Stroke *self , PyObject *args) {
	float f;

	if(!( PyArg_ParseTuple(args, "f", &f) )) {
		cout << "ERROR: Stroke_setLength" << endl;
		Py_RETURN_NONE;
	}

	self->s->setLength( f );

	Py_RETURN_NONE;
}

PyObject *Stroke_setMediumType( BPy_Stroke *self , PyObject *args) {
	PyObject *py_mt;

	if(!( PyArg_ParseTuple(args, "O", &py_mt) && BPy_MediumType_Check(py_mt)  )) {
		cout << "ERROR: Stroke_setMediumType" << endl;
		Py_RETURN_NONE;
	}

	self->s->setMediumType( static_cast<Stroke::MediumType>(PyInt_AsLong(py_mt)) );

	Py_RETURN_NONE;
}

PyObject *Stroke_setTextureId( BPy_Stroke *self , PyObject *args) {
	unsigned int i;

	if(!( PyArg_ParseTuple(args, "I", &i) )) {
		cout << "ERROR: Stroke_setTextureId" << endl;
		Py_RETURN_NONE;
	}

	self->s->setTextureId( i );

	Py_RETURN_NONE;
}

PyObject *Stroke_setTips( BPy_Stroke *self , PyObject *args) {
	PyObject *py_b;

	if(!( PyArg_ParseTuple(args, "O", &py_b) && PyBool_Check(py_b)  )) {
		cout << "ERROR: Stroke_setTips" << endl;
		Py_RETURN_NONE;
	}

	self->s->setTips( bool_from_PyBool(py_b) );

	Py_RETURN_NONE;
}

PyObject * Stroke_strokeVerticesBegin( BPy_Stroke *self , PyObject *args) {
	float f = 0;

	if(!( PyArg_ParseTuple(args, "|f", &f)  )){
		cout << "ERROR: Stroke_pointsBegin" << endl;
		Py_RETURN_NONE;
	}
	StrokeInternal::StrokeVertexIterator sv_it( self->s->strokeVerticesBegin(f) );
	return BPy_StrokeVertexIterator_from_StrokeVertexIterator( sv_it, 0 );
}

PyObject * Stroke_strokeVerticesEnd( BPy_Stroke *self ) {
	StrokeInternal::StrokeVertexIterator sv_it( self->s->strokeVerticesEnd() );
	return BPy_StrokeVertexIterator_from_StrokeVertexIterator( sv_it, 1 );
}

PyObject * Stroke_strokeVerticesSize( BPy_Stroke *self ) {
	return PyInt_FromLong( self->s->strokeVerticesSize() );
}

PyObject * Stroke_verticesBegin( BPy_Stroke *self ) {
	Interface0DIterator if0D_it( self->s->verticesBegin() );
	return BPy_Interface0DIterator_from_Interface0DIterator( if0D_it );
}

PyObject * Stroke_verticesEnd( BPy_Stroke *self ) {
	Interface0DIterator if0D_it( self->s->verticesEnd() );
	return BPy_Interface0DIterator_from_Interface0DIterator( if0D_it );	
}

PyObject * Stroke_pointsBegin( BPy_Stroke *self , PyObject *args) {
	float f = 0;

	if(!( PyArg_ParseTuple(args, "|f", &f)  )) {
		cout << "ERROR: Stroke_pointsBegin" << endl;
		Py_RETURN_NONE;
	}

	Interface0DIterator if0D_it( self->s->pointsBegin(f) );
	return BPy_Interface0DIterator_from_Interface0DIterator( if0D_it );
}

PyObject * Stroke_pointsEnd( BPy_Stroke *self , PyObject *args) {
	float f = 0;

	if(!( PyArg_ParseTuple(args, "|f", &f)  )) {
		cout << "ERROR: Stroke_pointsEnd" << endl;
		Py_RETURN_NONE;
	}
	
	Interface0DIterator if0D_it( self->s->pointsEnd(f) );
	return BPy_Interface0DIterator_from_Interface0DIterator( if0D_it );
}
	
///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
