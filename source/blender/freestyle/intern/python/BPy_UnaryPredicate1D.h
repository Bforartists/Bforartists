#ifndef FREESTYLE_PYTHON_UNARYPREDICATE1D_H
#define FREESTYLE_PYTHON_UNARYPREDICATE1D_H

#include <Python.h>

#include "../stroke/Predicates1D.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

extern PyTypeObject UnaryPredicate1D_Type;

#define BPy_UnaryPredicate1D_Check(v)	(  PyObject_IsInstance( (PyObject *) v, (PyObject *) &UnaryPredicate1D_Type)  )

/*---------------------------Python BPy_UnaryPredicate1D structure definition----------*/
typedef struct {
	PyObject_HEAD
	UnaryPredicate1D *up1D;
} BPy_UnaryPredicate1D;

/*---------------------------Python BPy_UnaryPredicate1D visible prototypes-----------*/

int UnaryPredicate1D_Init( PyObject *module );

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

#endif /* FREESTYLE_PYTHON_UNARYPREDICATE1D_H */
