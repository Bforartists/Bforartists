#ifndef FREESTYLE_PYTHON_UNARYFUNCTION0D_H
#define FREESTYLE_PYTHON_UNARYFUNCTION0D_H

#include <Python.h>

#include "../view_map/Functions0D.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

extern PyTypeObject UnaryFunction0D_Type;

#define BPy_UnaryFunction0D_Check(v)	(  PyObject_IsInstance( (PyObject *) v, (PyObject *) &UnaryFunction0D_Type)  )

/*---------------------------Python BPy_UnaryFunction0D structure definition----------*/
typedef struct {
	PyObject_HEAD
	PyObject *py_uf0D;
} BPy_UnaryFunction0D;

/*---------------------------Python BPy_UnaryFunction0D visible prototypes-----------*/

int UnaryFunction0D_Init( PyObject *module );

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

#endif /* FREESTYLE_PYTHON_UNARYFUNCTION0D_H */
