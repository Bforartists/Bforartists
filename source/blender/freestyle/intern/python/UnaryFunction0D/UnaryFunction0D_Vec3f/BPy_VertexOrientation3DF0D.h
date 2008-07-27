#ifndef FREESTYLE_PYTHON_VERTEXORIENTATION3DF0D_H
#define FREESTYLE_PYTHON_VERTEXORIENTATION3DF0D_H

#include "../BPy_UnaryFunction0DVec3f.h"

#ifdef __cplusplus
extern "C" {
#endif

///////////////////////////////////////////////////////////////////////////////////////////

#include <Python.h>

extern PyTypeObject VertexOrientation3DF0D_Type;

#define BPy_VertexOrientation3DF0D_Check(v)	(( (PyObject *) v)->ob_type == &VertexOrientation3DF0D_Type)

/*---------------------------Python BPy_VertexOrientation3DF0D structure definition----------*/
typedef struct {
	BPy_UnaryFunction0DVec3f py_uf0D_vec3f;
} BPy_VertexOrientation3DF0D;


///////////////////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif

#endif /* FREESTYLE_PYTHON_VERTEXORIENTATION3DF0D_H */
