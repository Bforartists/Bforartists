#include "BPy_ReadMapPixelF0D.h"

#include "../../../stroke/AdvancedFunctions0D.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------INSTANCE METHODS ----------------------------------

static char ReadMapPixelF0D___doc__[] =
".. method:: __init__(iMapName, level)\n"
"\n"
"   Builds a ReadMapPixelF0D object.\n"
"\n"
"   :arg iMapName: The name of the map to be read.\n"
"   :type iMapName: str\n"
"   :arg level: The level of the pyramid from which the pixel must be\n"
"      read.\n"
"   :type level: int\n"
"\n"
".. method:: __call__(it)\n"
"\n"
"   Reads a pixel in a map.\n"
"\n"
"   :arg it: An Interface0DIterator object.\n"
"   :type it: :class:`Interface0DIterator`\n"
"   :return: A pixel in a map.\n"
"   :rtype: float\n";

static int ReadMapPixelF0D___init__( BPy_ReadMapPixelF0D* self, PyObject *args)
{
	const char *s;
	int i;

	if( !PyArg_ParseTuple(args, "si", &s, &i) )
		return -1;
	self->py_uf0D_float.uf0D_float = new Functions0D::ReadMapPixelF0D(s,i);
	self->py_uf0D_float.uf0D_float->py_uf0D = (PyObject *)self;
	return 0;
}

/*-----------------------BPy_ReadMapPixelF0D type definition ------------------------------*/

PyTypeObject ReadMapPixelF0D_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"ReadMapPixelF0D",              /* tp_name */
	sizeof(BPy_ReadMapPixelF0D),    /* tp_basicsize */
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
	ReadMapPixelF0D___doc__,        /* tp_doc */
	0,                              /* tp_traverse */
	0,                              /* tp_clear */
	0,                              /* tp_richcompare */
	0,                              /* tp_weaklistoffset */
	0,                              /* tp_iter */
	0,                              /* tp_iternext */
	0,                              /* tp_methods */
	0,                              /* tp_members */
	0,                              /* tp_getset */
	&UnaryFunction0DFloat_Type,     /* tp_base */
	0,                              /* tp_dict */
	0,                              /* tp_descr_get */
	0,                              /* tp_descr_set */
	0,                              /* tp_dictoffset */
	(initproc)ReadMapPixelF0D___init__, /* tp_init */
	0,                              /* tp_alloc */
	0,                              /* tp_new */
};

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
