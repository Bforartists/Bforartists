#ifndef FREESTYLE_PYTHON_UNARYPREDICATE0D_H
#define FREESTYLE_PYTHON_UNARYPREDICATE0D_H

#include "../stroke/Predicates0D.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

#include <Python.h>

extern PyTypeObject UnaryPredicate0D_Type;

#define BPy_UnaryPredicate0D_Check(v)	(  PyObject_IsInstance( (PyObject *) v, (PyObject *) &UnaryPredicate0D_Type)  )

/*---------------------------Python BPy_UnaryPredicate0D structure definition----------*/
typedef struct {
	PyObject_HEAD
	UnaryPredicate0D *up0D;
} BPy_UnaryPredicate0D;

/*---------------------------Python BPy_UnaryPredicate0D visible prototypes-----------*/

int UnaryPredicate0D_Init( PyObject *module );

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

#endif /* FREESTYLE_PYTHON_UNARYPREDICATE0D_H */
