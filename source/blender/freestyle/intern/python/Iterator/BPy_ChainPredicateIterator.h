#ifndef FREESTYLE_PYTHON_CHAINPREDICATEITERATOR_H
#define FREESTYLE_PYTHON_CHAINPREDICATEITERATOR_H


#include "../../stroke/ChainingIterators.h"

#include "BPy_ChainingIterator.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

#include <Python.h>

extern PyTypeObject ChainPredicateIterator_Type;

#define BPy_ChainPredicateIterator_Check(v)	(  PyObject_IsInstance( (PyObject *) v, (PyObject *) &ChainPredicateIterator_Type)  )

/*---------------------------Python BPy_ChainPredicateIterator structure definition----------*/
typedef struct {
	BPy_ChainingIterator py_c_it;
	ChainPredicateIterator *cp_it;
	PyObject *upred;
	PyObject *bpred;
} BPy_ChainPredicateIterator;

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

#endif /* FREESTYLE_PYTHON_CHAINPREDICATEITERATOR_H */
