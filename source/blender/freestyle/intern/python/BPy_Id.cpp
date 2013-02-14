#include "BPy_Id.h"

#include "BPy_Convert.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//-------------------MODULE INITIALIZATION--------------------------------
int Id_Init( PyObject *module )
{
	if( module == NULL )
		return -1;

	if( PyType_Ready( &Id_Type ) < 0 )
		return -1;

	Py_INCREF( &Id_Type );
	PyModule_AddObject(module, "Id", (PyObject *)&Id_Type);
	return 0;
}

//------------------------INSTANCE METHODS ----------------------------------

static char Id___doc__[] =
".. method:: __init__()\n"
"\n"
"   Default constructor.\n"
"\n"
".. method:: __init__(iBrother)\n"
"\n"
"   Copy constructor.\n"
"\n"
"   :arg iBrother: An Id object.\n"
"   :type iBrother: :class:`Id`\n"
"\n"
".. method:: __init__(iFirst)\n"
"\n"
"   Builds an Id from an integer. The second number is set to 0.\n"
"\n"
"   :arg iFirst: The first Id number.\n"
"   :type iFirst: int\n"
"\n"
".. method:: __init__(iFirst, iSecond)\n"
"\n"
"   Builds the Id from the two numbers.\n"
"\n"
"   :arg iFirst: The first Id number.\n"
"   :type iFirst: int\n"
"   :arg iSecond: The second Id number.\n"
"   :type iSecond: int\n";

static int Id___init__(BPy_Id *self, PyObject *args, PyObject *kwds)
{
    int first = 0, second = 0;
    static const char *kwlist[] = {"first", "second", NULL};

    if (! PyArg_ParseTupleAndKeywords(args, kwds, "|ii", (char**)kwlist, &first, &second) )
        return -1;

	self->id = new Id( first, second );

    return 0;
}

static void Id___dealloc__(BPy_Id* self)
{
	delete self->id;
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject * Id___repr__(BPy_Id* self)
{
    return PyUnicode_FromFormat("[ first: %i, second: %i ](BPy_Id)", self->id->getFirst(), self->id->getSecond() );
}

static PyObject * Id_RichCompare(BPy_Id *o1, BPy_Id *o2, int opid) {
	switch(opid){
		case Py_LT:
			return PyBool_from_bool( o1->id->operator<(*(o2->id)) );
			break;
		case Py_LE:
			return PyBool_from_bool( o1->id->operator<(*(o2->id)) || o1->id->operator<(*(o2->id)) );
			break;
		case Py_EQ:
			return PyBool_from_bool( o1->id->operator==(*(o2->id)) );
			break;
		case Py_NE:
			return PyBool_from_bool( o1->id->operator!=(*(o2->id)) );
			break;
		case Py_GT:
			return PyBool_from_bool(!( o1->id->operator<(*(o2->id)) || o1->id->operator<(*(o2->id)) ));
			break;
		case Py_GE:
			return PyBool_from_bool(!( o1->id->operator<(*(o2->id)) ));
			break;
	}
	
	Py_RETURN_NONE;
}

/*----------------------Id instance definitions ----------------------------*/
static PyMethodDef BPy_Id_methods[] = {
	{NULL, NULL, 0, NULL}
};

/*----------------------Id get/setters ----------------------------*/

PyDoc_STRVAR(Id_first_doc,
"The first number constituting the Id.\n"
"\n"
":type: int"
);

static PyObject *Id_first_get(BPy_Id *self, void *UNUSED(closure))
{
	return PyLong_FromLong(self->id->getFirst());
}

static int Id_first_set(BPy_Id *self, PyObject *value, void *UNUSED(closure))
{
	int scalar;
	if ((scalar = PyLong_AsLong(value)) == -1 && PyErr_Occurred()) {
		PyErr_SetString(PyExc_TypeError, "value must be an integer");
		return -1;
	}
	self->id->setFirst(scalar);
	return 0;
}

PyDoc_STRVAR(Id_second_doc,
"The second number constituting the Id.\n"
"\n"
":type: int"
);

static PyObject *Id_second_get(BPy_Id *self, void *UNUSED(closure))
{
	return PyLong_FromLong(self->id->getSecond());
}

static int Id_second_set(BPy_Id *self, PyObject *value, void *UNUSED(closure))
{
	int scalar;
	if ((scalar = PyLong_AsLong(value)) == -1 && PyErr_Occurred()) {
		PyErr_SetString(PyExc_TypeError, "value must be an integer");
		return -1;
	}
	self->id->setSecond(scalar);
	return 0;
}

static PyGetSetDef BPy_Id_getseters[] = {
	{(char *)"first", (getter)Id_first_get, (setter)Id_first_set, (char *)Id_first_doc, NULL},
	{(char *)"second", (getter)Id_second_get, (setter)Id_second_set, (char *)Id_second_doc, NULL},
	{NULL, NULL, NULL, NULL, NULL}  /* Sentinel */
};

/*-----------------------BPy_Id type definition ------------------------------*/

PyTypeObject Id_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"Id",                           /* tp_name */
	sizeof(BPy_Id),                 /* tp_basicsize */
	0,                              /* tp_itemsize */
	(destructor)Id___dealloc__,     /* tp_dealloc */
	0,                              /* tp_print */
	0,                              /* tp_getattr */
	0,                              /* tp_setattr */
	0,                              /* tp_reserved */
	(reprfunc)Id___repr__,          /* tp_repr */
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
	Id___doc__,                     /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	(richcmpfunc)Id_RichCompare,    /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	BPy_Id_methods,                 /* tp_methods */
	0,                              /* tp_members */
	BPy_Id_getseters,               /* tp_getset */
	0,                              /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)Id___init__,          /* tp_init */
	0,                              /* tp_alloc */
	PyType_GenericNew,              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
