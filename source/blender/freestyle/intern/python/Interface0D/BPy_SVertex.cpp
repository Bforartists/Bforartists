#include "BPy_SVertex.h"

#include "../BPy_Convert.h"
#include "../BPy_Id.h"
#include "../Interface1D/BPy_FEdge.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

/*---------------  Python API function prototypes for SVertex instance  -----------*/
static int SVertex___init__(BPy_SVertex *self, PyObject *args, PyObject *kwds);
static PyObject * SVertex___copy__( BPy_SVertex *self );
static PyObject * SVertex_normals( BPy_SVertex *self );
static PyObject * SVertex_normalsSize( BPy_SVertex *self );
static PyObject * SVertex_viewvertex( BPy_SVertex *self );
static PyObject * SVertex_setPoint3D( BPy_SVertex *self , PyObject *args);
static PyObject * SVertex_setPoint2D( BPy_SVertex *self , PyObject *args);
static PyObject * SVertex_AddNormal( BPy_SVertex *self , PyObject *args);
static PyObject * SVertex_setId( BPy_SVertex *self , PyObject *args);
static PyObject *SVertex_AddFEdge( BPy_SVertex *self , PyObject *args);

/*----------------------SVertex instance definitions ----------------------------*/
static PyMethodDef BPy_SVertex_methods[] = {
	{"__copy__", ( PyCFunction ) SVertex___copy__, METH_NOARGS, "（ ）Cloning method."},
	{"normals", ( PyCFunction ) SVertex_normals, METH_NOARGS, "Returns the normals for this Vertex as a list. In a smooth surface, a vertex has exactly one normal. In a sharp surface, a vertex can have any number of normals."},
	{"normalsSize", ( PyCFunction ) SVertex_normalsSize, METH_NOARGS, "Returns the number of different normals for this vertex." },
	{"viewvertex", ( PyCFunction ) SVertex_viewvertex, METH_NOARGS, "If this SVertex is also a ViewVertex, this method returns a pointer onto this ViewVertex. 0 is returned otherwise." },	
	{"setPoint3D", ( PyCFunction ) SVertex_setPoint3D, METH_VARARGS, "Sets the 3D coordinates of the SVertex." },
	{"setPoint2D", ( PyCFunction ) SVertex_setPoint2D, METH_VARARGS, "Sets the 3D projected coordinates of the SVertex." },
	{"AddNormal", ( PyCFunction ) SVertex_AddNormal, METH_VARARGS, "Adds a normal to the Svertex's set of normals. If the same normal is already in the set, nothing changes." },
	{"setId", ( PyCFunction ) SVertex_setId, METH_VARARGS, "Sets the Id." },
	{"AddFEdge", ( PyCFunction ) SVertex_AddFEdge, METH_VARARGS, "Add an FEdge to the list of edges emanating from this SVertex." },	
	{NULL, NULL, 0, NULL}
};

/*-----------------------BPy_SVertex type definition ------------------------------*/

PyTypeObject SVertex_Type = {
	PyObject_HEAD_INIT( NULL ) 
	0,							/* ob_size */
	"SVertex",				/* tp_name */
	sizeof( BPy_SVertex ),	/* tp_basicsize */
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
	NULL,                       /* PySequenceMethods *tp_as_sequence; */
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
	NULL,                       /* getiterfunc tp_iter; */
	NULL,                       /* iternextfunc tp_iternext; */

  /*** Attribute descriptor and subclassing stuff ***/
	BPy_SVertex_methods,	/* struct PyMethodDef *tp_methods; */
	NULL,                       	/* struct PyMemberDef *tp_members; */
	NULL,         					/* struct PyGetSetDef *tp_getset; */
	&Interface0D_Type,				/* struct _typeobject *tp_base; */
	NULL,							/* PyObject *tp_dict; */
	NULL,							/* descrgetfunc tp_descr_get; */
	NULL,							/* descrsetfunc tp_descr_set; */
	0,                          	/* long tp_dictoffset; */
	(initproc)SVertex___init__,                       	/* initproc tp_init; */
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

int SVertex___init__(BPy_SVertex *self, PyObject *args, PyObject *kwds)
{
	PyObject *py_point = 0;
	BPy_Id *py_id = 0;
	

	if (! PyArg_ParseTuple(args, "|OO!", &py_point, &Id_Type, &py_id) )
        return -1;
	
	if( py_point && py_id ) {
		Vec3r *v = Vec3r_ptr_from_PyObject(py_point);
		if( !v ) {
			PyErr_SetString(PyExc_TypeError, "argument 1 must be a 3D vector (either a list of 3 elements or Vector)");
			return -1;
		}
		self->sv = new SVertex( *v, *(py_id->id) );
		delete v;
	} else if( !py_point && !py_id ) {
		self->sv = new SVertex();
	} else {
		PyErr_SetString(PyExc_TypeError, "invalid argument(s)");
		return -1;
	}

	self->py_if0D.if0D = self->sv;
	
	return 0;
}

PyObject * SVertex___copy__( BPy_SVertex *self ) {
	BPy_SVertex *py_svertex;
	
	py_svertex = (BPy_SVertex *) SVertex_Type.tp_new( &SVertex_Type, 0, 0 );
	
	py_svertex->sv = self->sv->duplicate();
	py_svertex->py_if0D.if0D = py_svertex->sv;

	return (PyObject *) py_svertex;
}


PyObject * SVertex_normals( BPy_SVertex *self ) {
	PyObject *py_normals; 
	set< Vec3r > normals;
	
	py_normals  = PyList_New(NULL);
	normals = self->sv->normals();
		
	for( set< Vec3r >::iterator set_iterator = normals.begin(); set_iterator != normals.end(); set_iterator++ ) {
		Vec3r v( *set_iterator );
		PyList_Append( py_normals, Vector_from_Vec3r(v) );
	}
	
	return py_normals;
}

PyObject * SVertex_normalsSize( BPy_SVertex *self ) {
	return PyInt_FromLong( self->sv->normalsSize() );
}

PyObject * SVertex_viewvertex( BPy_SVertex *self ) {
	ViewVertex *vv = self->sv->viewvertex();
	if (!vv)
		Py_RETURN_NONE;
	if (typeid(*vv) == typeid(NonTVertex))
		return BPy_NonTVertex_from_NonTVertex_ptr( dynamic_cast<NonTVertex*>(vv) );
	else
		return BPy_TVertex_from_TVertex_ptr( dynamic_cast<TVertex*>(vv) );
}

PyObject *SVertex_setPoint3D( BPy_SVertex *self , PyObject *args) {
	PyObject *py_point;

	if(!( PyArg_ParseTuple(args, "O", &py_point) ))
		return NULL;
	Vec3r *v = Vec3r_ptr_from_PyObject(py_point);
	if( !v ) {
		PyErr_SetString(PyExc_TypeError, "argument 1 must be a 3D vector (either a list of 3 elements or Vector)");
		return NULL;
	}
	self->sv->setPoint3D( *v );
	delete v;

	Py_RETURN_NONE;
}

PyObject *SVertex_setPoint2D( BPy_SVertex *self , PyObject *args) {
	PyObject *py_point;

	if(!( PyArg_ParseTuple(args, "O", &py_point) ))
		return NULL;
	Vec3r *v = Vec3r_ptr_from_PyObject(py_point);
	if( !v ) {
		PyErr_SetString(PyExc_TypeError, "argument 1 must be a 3D vector (either a list of 3 elements or Vector)");
		return NULL;
	}
	self->sv->setPoint2D( *v );
	delete v;

	Py_RETURN_NONE;
}

PyObject *SVertex_AddNormal( BPy_SVertex *self , PyObject *args) {
	PyObject *py_normal;

	if(!( PyArg_ParseTuple(args, "O", &py_normal) ))
		return NULL;
	Vec3r *n = Vec3r_ptr_from_PyObject(py_normal);
	if( !n ) {
		PyErr_SetString(PyExc_TypeError, "argument 1 must be a 3D vector (either a list of 3 elements or Vector)");
		return NULL;
	}
	self->sv->AddNormal( *n );
	delete n;

	Py_RETURN_NONE;
}

PyObject *SVertex_setId( BPy_SVertex *self , PyObject *args) {
	BPy_Id *py_id;

	if( !PyArg_ParseTuple(args, "O!", &Id_Type, &py_id) )
		return NULL;

	self->sv->setId( *(py_id->id) );

	Py_RETURN_NONE;
}

PyObject *SVertex_AddFEdge( BPy_SVertex *self , PyObject *args) {
	PyObject *py_fe;

	if(!( PyArg_ParseTuple(args, "O!", &FEdge_Type, &py_fe) ))
		return NULL;
	
	self->sv->AddFEdge( ((BPy_FEdge *) py_fe)->fe );

	Py_RETURN_NONE;
}


// virtual bool 	operator== (const SVertex &iBrother)
// ViewVertex * 	viewvertex ()


///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

