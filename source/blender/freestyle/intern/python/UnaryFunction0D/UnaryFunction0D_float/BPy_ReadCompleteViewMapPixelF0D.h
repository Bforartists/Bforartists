#ifndef FREESTYLE_PYTHON_READCOMPLETEVIEWMAPPIXELF0D_H
#define FREESTYLE_PYTHON_READCOMPLETEVIEWMAPPIXELF0D_H

#include "../BPy_UnaryFunction0DFloat.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

#include <Python.h>

extern PyTypeObject ReadCompleteViewMapPixelF0D_Type;

#define BPy_ReadCompleteViewMapPixelF0D_Check(v)	(  PyObject_IsInstance( (PyObject *) v, (PyObject *) &ReadCompleteViewMapPixelF0D_Type)  )

/*---------------------------Python BPy_ReadCompleteViewMapPixelF0D structure definition----------*/
typedef struct {
	BPy_UnaryFunction0DFloat py_uf0D_float;
} BPy_ReadCompleteViewMapPixelF0D;


///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

#endif /* FREESTYLE_PYTHON_READCOMPLETEVIEWMAPPIXELF0D_H */
