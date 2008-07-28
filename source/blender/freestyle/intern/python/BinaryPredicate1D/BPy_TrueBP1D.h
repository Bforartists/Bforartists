#ifndef FREESTYLE_PYTHON_TRUEBP1D_H
#define FREESTYLE_PYTHON_TRUEBP1D_H

#include "../BPy_BinaryPredicate1D.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

#include <Python.h>

extern PyTypeObject TrueBP1D_Type;

#define BPy_TrueBP1D_Check(v)	(( (PyObject *) v)->ob_type == &TrueBP1D_Type)

/*---------------------------Python BPy_TrueBP1D structure definition----------*/
typedef struct {
	BPy_BinaryPredicate1D py_bp1D;
} BPy_TrueBP1D;

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

#endif /* FREESTYLE_PYTHON_TRUEBP1D_H */
