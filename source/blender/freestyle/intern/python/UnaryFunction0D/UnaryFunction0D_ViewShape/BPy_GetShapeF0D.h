#ifndef FREESTYLE_PYTHON_GETSHAPEF0D_H
#define FREESTYLE_PYTHON_GETSHAPEF0D_H

#include "../BPy_UnaryFunction0DViewShape.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

#include <Python.h>

extern PyTypeObject GetShapeF0D_Type;

#define BPy_GetShapeF0D_Check(v)	(  PyObject_IsInstance( (PyObject *) v, (PyObject *) &GetShapeF0D_Type)  )

/*---------------------------Python BPy_GetShapeF0D structure definition----------*/
typedef struct {
	BPy_UnaryFunction0DViewShape py_uf0D_viewshape;
} BPy_GetShapeF0D;


///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

#endif /* FREESTYLE_PYTHON_GETSHAPEF0D_H */
