#ifndef FREESTYLE_PYTHON_SVERTEX_H
#define FREESTYLE_PYTHON_SVERTEX_H

#include "../../view_map/Silhouette.h"
#include "../BPy_Interface0D.h"


#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

#include <Python.h>

extern PyTypeObject SVertex_Type;

#define BPy_SVertex_Check(v)	(  PyObject_IsInstance( (PyObject *) v, (PyObject *) &SVertex_Type)  )

/*---------------------------Python BPy_SVertex structure definition----------*/
typedef struct {
	BPy_Interface0D py_if0D;
	SVertex *sv;
} BPy_SVertex;

/*---------------------------Python BPy_SVertex visible prototypes-----------*/

void SVertex_mathutils_register_callback();

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

#endif /* FREESTYLE_PYTHON_SVERTEX_H */
