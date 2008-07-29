#ifndef FREESTYLE_PYTHON_GETPROJECTEDYF0D_H
#define FREESTYLE_PYTHON_GETPROJECTEDYF0D_H

#include "../BPy_UnaryFunction0DDouble.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

#include <Python.h>

extern PyTypeObject GetProjectedYF0D_Type;

#define BPy_GetProjectedYF0D_Check(v)	(  PyObject_IsInstance( (PyObject *) v, (PyObject *) &GetProjectedYF0D_Type)  )

/*---------------------------Python BPy_GetProjectedYF0D structure definition----------*/
typedef struct {
	BPy_UnaryFunction0DDouble py_uf0D_double;
} BPy_GetProjectedYF0D;


///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

#endif /* FREESTYLE_PYTHON_GETPROJECTEDYF0D_H */
