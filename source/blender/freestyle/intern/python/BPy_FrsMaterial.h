#ifndef FREESTYLE_PYTHON_FRSMATERIAL_H
#define FREESTYLE_PYTHON_FRSMATERIAL_H

#include "../scene_graph/FrsMaterial.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

#include <Python.h>

extern PyTypeObject FrsMaterial_Type;

#define BPy_FrsMaterial_Check(v)	(  PyObject_IsInstance( (PyObject *) v, (PyObject *) &FrsMaterial_Type)  )

/*---------------------------Python BPy_FrsMaterial structure definition----------*/
typedef struct {
	PyObject_HEAD
	FrsMaterial *m;
	int borrowed; /* non-zero if *m is a borrowed object */
} BPy_FrsMaterial;

/*---------------------------Python BPy_FrsMaterial visible prototypes-----------*/

PyMODINIT_FUNC FrsMaterial_Init( PyObject *module );


///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif


#endif /* FREESTYLE_PYTHON_FRSMATERIAL_H */
