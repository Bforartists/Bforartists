#include "BPy_Freestyle.h"

#include "BPy_BBox.h"
#include "BPy_BinaryPredicate0D.h"
#include "BPy_BinaryPredicate1D.h"
#include "BPy_ContextFunctions.h"
#include "BPy_FrsMaterial.h"
#include "BPy_FrsNoise.h"
#include "BPy_Id.h"
#include "BPy_IntegrationType.h"
#include "BPy_Interface0D.h"
#include "BPy_Interface1D.h"
#include "BPy_Iterator.h"
#include "BPy_MediumType.h"
#include "BPy_Nature.h"
#include "BPy_Operators.h"
#include "BPy_SShape.h"
#include "BPy_StrokeAttribute.h"
#include "BPy_StrokeShader.h"
#include "BPy_UnaryFunction0D.h"
#include "BPy_UnaryFunction1D.h"
#include "BPy_UnaryPredicate0D.h"
#include "BPy_UnaryPredicate1D.h"
#include "BPy_ViewMap.h"
#include "BPy_ViewShape.h"


#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

//------------------------ MODULE FUNCTIONS ----------------------------------

#include "FRS_freestyle.h"
#include "bpy_rna.h" /* pyrna_struct_CreatePyObject() */

static char Freestyle_getCurrentScene___doc__[] =
".. function:: getCurrentScene()\n"
"\n"
"   Returns the current scene.\n"
"\n"
"   :return: The current scene.\n"
"   :rtype: :class:`bpy.types.Scene`\n";

static PyObject *Freestyle_getCurrentScene( PyObject *self )
{
	if (!freestyle_scene) {
		PyErr_SetString(PyExc_TypeError, "current scene not available");
		return NULL;
	}
	PointerRNA ptr_scene;
	RNA_pointer_create(NULL, &RNA_Scene, freestyle_scene, &ptr_scene);
	return pyrna_struct_CreatePyObject(&ptr_scene);
}

#include "BKE_texture.h" /* do_colorband() */

static char Freestyle_evaluateColorRamp___doc__[] =
".. function:: evaluateColorRamp(ramp, in)\n"
"\n"
"   Evaluate a color ramp at a point in the interval 0 to 1.\n"
"\n"
"   :arg ramp: Color ramp object.\n"
"   :type ramp: :class:`bpy.types.ColorRamp`\n"
"   :arg in: Value in the interval 0 to 1.\n"
"   :type in: float\n"
"   :return: color in RGBA format.\n"
"   :rtype: Tuple of 4 float values\n";

static PyObject *Freestyle_evaluateColorRamp( PyObject *self, PyObject *args )
{
	BPy_StructRNA *py_srna;
	ColorBand *coba;
	float in, out[4];

	if(!( PyArg_ParseTuple(args, "O!f", &pyrna_struct_Type, &py_srna, &in) ))
		return NULL;
	if(!RNA_struct_is_a(py_srna->ptr.type, &RNA_ColorRamp)) {
		PyErr_SetString(PyExc_TypeError, "1st argument is not a ColorRamp object");
		return NULL;
	}
	coba = (ColorBand *)py_srna->ptr.data;
	if (!do_colorband(coba, in, out)) {
		PyErr_SetString(PyExc_ValueError, "failed to evaluate the color ramp");
		return NULL;
	}
	return Py_BuildValue("(f,f,f,f)", out[0], out[1], out[2], out[3]);
}

#include "BKE_colortools.h" /* curvemapping_evaluateF() */

static char Freestyle_evaluateCurveMappingF___doc__[] =
".. function:: evaluateCurveMappingF(cumap, cur, value)\n"
"\n"
"   Evaluate a curve mapping at a point in the interval 0 to 1.\n"
"\n"
"   :arg cumap: Curve mapping object.\n"
"   :type cumap: :class:`bpy.types.CurveMapping`\n"
"   :arg cur: Index of the curve to be used (0 <= cur <= 3).\n"
"   :type cur: int\n"
"   :arg value: Input value in the interval 0 to 1.\n"
"   :type value: float\n"
"   :return: Mapped output value.\n"
"   :rtype: float\n";

static PyObject *Freestyle_evaluateCurveMappingF( PyObject *self, PyObject *args )
{
	BPy_StructRNA *py_srna;
	CurveMapping *cumap;
	int cur;
	float value;

	if(!( PyArg_ParseTuple(args, "O!if", &pyrna_struct_Type, &py_srna, &cur, &value) ))
		return NULL;
	if(!RNA_struct_is_a(py_srna->ptr.type, &RNA_CurveMapping)) {
		PyErr_SetString(PyExc_TypeError, "1st argument is not a CurveMapping object");
		return NULL;
	}
	if (cur < 0 || cur > 3) {
		PyErr_SetString(PyExc_ValueError, "2nd argument is out of range");
		return NULL;
	}
	cumap = (CurveMapping *)py_srna->ptr.data;
	return PyFloat_FromDouble(curvemapping_evaluateF(cumap, cur, value));
}

/*-----------------------Freestyle module docstring----------------------------*/

static char module_docstring[] = "The Blender Freestyle module\n\n";

/*-----------------------Freestyle module method def---------------------------*/

static PyMethodDef module_functions[] = {
	{"getCurrentScene", ( PyCFunction ) Freestyle_getCurrentScene, METH_NOARGS, Freestyle_getCurrentScene___doc__},
	{"evaluateColorRamp", ( PyCFunction ) Freestyle_evaluateColorRamp, METH_VARARGS, Freestyle_evaluateColorRamp___doc__},
	{"evaluateCurveMappingF", ( PyCFunction ) Freestyle_evaluateCurveMappingF, METH_VARARGS, Freestyle_evaluateCurveMappingF___doc__},
	{NULL, NULL, 0, NULL}
};

/*-----------------------Freestyle module definition---------------------------*/

static PyModuleDef module_definition = {
    PyModuleDef_HEAD_INIT,
    "Freestyle",
    module_docstring,
    -1,
    module_functions
};

//-------------------MODULE INITIALIZATION--------------------------------
PyObject *Freestyle_Init( void )
{
	PyObject *module;
	
	// initialize modules
	module = PyModule_Create(&module_definition);
    if (!module)
		return NULL;
	PyDict_SetItemString(PySys_GetObject("modules"), module_definition.m_name, module);
	
	// attach its classes (adding the object types to the module)
	
	// those classes have to be initialized before the others
	MediumType_Init( module );
	Nature_Init( module );
	
	BBox_Init( module );
	BinaryPredicate0D_Init( module );
	BinaryPredicate1D_Init( module );
	ContextFunctions_Init( module );
	FrsMaterial_Init( module );
	FrsNoise_Init( module );
	Id_Init( module );
	IntegrationType_Init( module );
	Interface0D_Init( module );
	Interface1D_Init( module );
	Iterator_Init( module );
	Operators_Init( module );
	SShape_Init( module );
	StrokeAttribute_Init( module );
	StrokeShader_Init( module );
	UnaryFunction0D_Init( module );
	UnaryFunction1D_Init( module );
	UnaryPredicate0D_Init( module );
	UnaryPredicate1D_Init( module );
	ViewMap_Init( module );
	ViewShape_Init( module );

	return module;
}

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif
