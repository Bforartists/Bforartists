#ifndef FREESTYLE_PYTHON_VIEWMAP_H
#define FREESTYLE_PYTHON_VIEWMAP_H

#include <Python.h>

#include "../view_map/ViewMap.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

extern PyTypeObject ViewMap_Type;

#define BPy_ViewMap_Check(v)	(  PyObject_IsInstance( (PyObject *) v, (PyObject *) &ViewMap_Type)  )

/*---------------------------Python BPy_ViewMap structure definition----------*/
typedef struct {
	PyObject_HEAD
	ViewMap *vm;
} BPy_ViewMap;

/*---------------------------Python BPy_ViewMap visible prototypes-----------*/

int ViewMap_Init( PyObject *module );

///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

#endif /* FREESTYLE_PYTHON_VIEWMAP_H */
