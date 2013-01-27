#ifndef FREESTYLE_PYTHON_STROKEVERTEX_H
#define FREESTYLE_PYTHON_STROKEVERTEX_H

#include "../BPy_CurvePoint.h"
#include "../../../stroke/Stroke.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

#include <Python.h>

extern PyTypeObject StrokeVertex_Type;

#define BPy_StrokeVertex_Check(v)	(  PyObject_IsInstance( (PyObject *) v, (PyObject *) &StrokeVertex_Type)  )

/*---------------------------Python BPy_StrokeVertex structure definition----------*/
typedef struct {
	BPy_CurvePoint py_cp;
	StrokeVertex *sv;
} BPy_StrokeVertex;

/*---------------------------Python BPy_StrokeVertex visible prototypes-----------*/

void StrokeVertex_mathutils_register_callback();

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

#endif /* FREESTYLE_PYTHON_STROKEVERTEX_H */
