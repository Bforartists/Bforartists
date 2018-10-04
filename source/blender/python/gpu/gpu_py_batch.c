/*
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * Copyright 2015, Blender Foundation.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/python/gpu/gpu_py_batch.c
 *  \ingroup bpygpu
 *
 * This file defines the offscreen functionalities of the 'gpu' module
 * used for off-screen OpenGL rendering.
 *
 * - Use ``bpygpu_`` for local API.
 * - Use ``BPyGPU`` for public API.
 */

#include <Python.h>

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"

#include "BKE_global.h"
#include "BKE_library.h"

#include "GPU_batch.h"

#include "../mathutils/mathutils.h"

#include "../generic/py_capi_utils.h"

#include "gpu_py_primitive.h"
#include "gpu_py_shader.h"
#include "gpu_py_vertex_buffer.h"
#include "gpu_py_element.h"
#include "gpu_py_batch.h" /* own include */


/* -------------------------------------------------------------------- */

/** \name VertBatch Type
 * \{ */

static PyObject *bpygpu_Batch_new(PyTypeObject *UNUSED(type), PyObject *args, PyObject *kwds)
{
	const char *exc_str_missing_arg = "GPUBatch.__new__() missing required argument '%s' (pos %d)";

	struct {
		GPUPrimType type_id;
		BPyGPUVertBuf *py_vertbuf;
		BPyGPUIndexBuf *py_indexbuf;
	} params = {GPU_PRIM_NONE, NULL, NULL};

	static const char *_keywords[] = {"type", "buf", "elem", NULL};
	static _PyArg_Parser _parser = {"|$O&O!O!:GPUBatch.__new__", _keywords, 0};
	if (!_PyArg_ParseTupleAndKeywordsFast(
	        args, kwds, &_parser,
	        bpygpu_ParsePrimType, &params.type_id,
	        &BPyGPUVertBuf_Type, &params.py_vertbuf,
	        &BPyGPUIndexBuf_Type, &params.py_indexbuf))
	{
		return NULL;
	}

	if (params.type_id == GPU_PRIM_NONE) {
		PyErr_Format(PyExc_TypeError,
		             exc_str_missing_arg, _keywords[0], 1);
		return NULL;
	}

	if (params.py_vertbuf == NULL) {
		PyErr_Format(PyExc_TypeError,
		             exc_str_missing_arg, _keywords[1], 2);
		return NULL;
	}

	GPUBatch *batch = GPU_batch_create(
	        params.type_id,
	        params.py_vertbuf->buf,
	        params.py_indexbuf ? params.py_indexbuf->elem : NULL);

	BPyGPUBatch *ret = (BPyGPUBatch *)BPyGPUBatch_CreatePyObject(batch);

#ifdef USE_GPU_PY_REFERENCES
	ret->references = PyList_New(params.py_indexbuf ? 2 : 1);
	PyList_SET_ITEM(ret->references, 0, (PyObject *)params.py_vertbuf);
	Py_INCREF(params.py_vertbuf);

	if (params.py_indexbuf != NULL) {
		PyList_SET_ITEM(ret->references, 1, (PyObject *)params.py_indexbuf);
		Py_INCREF(params.py_indexbuf);
	}

	PyObject_GC_Track(ret);
#endif

	return (PyObject *)ret;
}

PyDoc_STRVAR(bpygpu_VertBatch_vertbuf_add_doc,
"TODO"
);
static PyObject *bpygpu_VertBatch_vertbuf_add(BPyGPUBatch *self, BPyGPUVertBuf *py_buf)
{
	if (!BPyGPUVertBuf_Check(py_buf)) {
		PyErr_Format(PyExc_TypeError,
		             "Expected a GPUVertBuf, got %s",
		             Py_TYPE(py_buf)->tp_name);
		return NULL;
	}

	if (self->batch->verts[0]->vertex_len != py_buf->buf->vertex_len) {
		PyErr_Format(PyExc_TypeError,
		             "Expected %d length, got %d",
		             self->batch->verts[0]->vertex_len, py_buf->buf->vertex_len);
		return NULL;
	}

#ifdef USE_GPU_PY_REFERENCES
	/* Hold user */
	PyList_Append(self->references, (PyObject *)py_buf);
#endif

	GPU_batch_vertbuf_add(self->batch, py_buf->buf);
	Py_RETURN_NONE;
}

PyDoc_STRVAR(bpygpu_VertBatch_program_set_doc,
"TODO"
);
static PyObject *bpygpu_VertBatch_program_set(BPyGPUBatch *self, BPyGPUShader *py_shader)
{
	if (!BPyGPUShader_Check(py_shader)) {
		PyErr_Format(PyExc_TypeError,
		             "Expected a GPUShader, got %s",
		             Py_TYPE(py_shader)->tp_name);
		return NULL;
	}

	GPUShader *shader = py_shader->shader;
	GPU_batch_program_set(self->batch,
	        GPU_shader_get_program(shader),
	        GPU_shader_get_interface(shader));

#ifdef USE_GPU_PY_REFERENCES
	/* Hold user */
	PyList_Append(self->references, (PyObject *)py_shader);
#endif

	Py_RETURN_NONE;
}

PyDoc_STRVAR(bpygpu_VertBatch_draw_doc,
".. method:: draw(program=None)\n"
"\n"
"   Run the drawing program with the parameters assigned to the batch.\n"
"\n"
"   :param program: program that performs the drawing operations. \n"
"      If ``None`` is passed, the last program setted to this batch will run.\n"
"   :type program: :class:`gpu.types.GPUShader`\n"
);
static PyObject *bpygpu_VertBatch_draw(BPyGPUBatch *self, PyObject *args)
{
	BPyGPUShader *py_program = NULL;

	if (!PyArg_ParseTuple(
	        args, "|O!:GPUShader.__exit__",
	        &BPyGPUShader_Type, &py_program))
	{
		return NULL;
	}

	else if (self->batch->program != GPU_shader_get_program(py_program->shader)) {
		GPU_batch_program_set(self->batch,
		        GPU_shader_get_program(py_program->shader),
		        GPU_shader_get_interface(py_program->shader));
	}

	GPU_batch_draw(self->batch);
	Py_RETURN_NONE;
}

static PyObject *bpygpu_VertBatch_program_use_begin(BPyGPUBatch *self)
{
	if (!glIsProgram(self->batch->program)) {
		PyErr_SetString(PyExc_ValueError,
		                "batch program has not not set");
	}
	GPU_batch_program_use_begin(self->batch);
	Py_RETURN_NONE;
}

static PyObject *bpygpu_VertBatch_program_use_end(BPyGPUBatch *self)
{
	if (!glIsProgram(self->batch->program)) {
		PyErr_SetString(PyExc_ValueError,
		                "batch program has not not set");
	}
	GPU_batch_program_use_end(self->batch);
	Py_RETURN_NONE;
}

static struct PyMethodDef bpygpu_VertBatch_methods[] = {
	{"vertbuf_add", (PyCFunction)bpygpu_VertBatch_vertbuf_add,
	 METH_O, bpygpu_VertBatch_vertbuf_add_doc},
	{"program_set", (PyCFunction)bpygpu_VertBatch_program_set,
	 METH_O, bpygpu_VertBatch_program_set_doc},
	{"draw", (PyCFunction) bpygpu_VertBatch_draw,
	 METH_VARARGS, bpygpu_VertBatch_draw_doc},
	{"__program_use_begin", (PyCFunction)bpygpu_VertBatch_program_use_begin,
	 METH_NOARGS, ""},
	{"__program_use_end", (PyCFunction)bpygpu_VertBatch_program_use_end,
	 METH_NOARGS, ""},
	{NULL, NULL, 0, NULL}
};

#ifdef USE_GPU_PY_REFERENCES

static int bpygpu_Batch_traverse(BPyGPUBatch *self, visitproc visit, void *arg)
{
	Py_VISIT(self->references);
	return 0;
}

static int bpygpu_Batch_clear(BPyGPUBatch *self)
{
	Py_CLEAR(self->references);
	return 0;
}

#endif

static void bpygpu_Batch_dealloc(BPyGPUBatch *self)
{
	GPU_batch_discard(self->batch);

#ifdef USE_GPU_PY_REFERENCES
	if (self->references) {
		PyObject_GC_UnTrack(self);
		bpygpu_Batch_clear(self);
		Py_XDECREF(self->references);
	}
#endif

	Py_TYPE(self)->tp_free(self);
}

PyDoc_STRVAR(py_gpu_batch_doc,
"GPUBatch(type, buf, elem=None)\n"
"\n"
"Contains VAOs + VBOs + Shader representing a drawable entity."
"\n"
"   :param type: One of these primitive types: {\n"
"       'POINTS',\n"
"       'LINES',\n"
"       'TRIS',\n"
"       'LINE_STRIP',\n"
"       'LINE_LOOP',\n"
"       'TRI_STRIP',\n"
"       'TRI_FAN',\n"
"       'LINES_ADJ',\n"
"       'TRIS_ADJ',\n"
"       'LINE_STRIP_ADJ'}\n"
"   :type type: `str`\n"
"   :param buf: Vertex buffer.\n"
"   :type buf: :class: `gpu.types.GPUVertBuf`\n"
"   :param elem: Optional Index buffer.\n"
"   :type elem: :class: `gpu.types.GPUIndexBuf`\n"
);
PyTypeObject BPyGPUBatch_Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	.tp_name = "GPUBatch",
	.tp_basicsize = sizeof(BPyGPUBatch),
	.tp_dealloc = (destructor)bpygpu_Batch_dealloc,
#ifdef USE_GPU_PY_REFERENCES
	.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
	.tp_doc = py_gpu_batch_doc,
	.tp_traverse = (traverseproc)bpygpu_Batch_traverse,
	.tp_clear = (inquiry)bpygpu_Batch_clear,
#else
	.tp_flags = Py_TPFLAGS_DEFAULT,
#endif
	.tp_methods = bpygpu_VertBatch_methods,
	.tp_new = bpygpu_Batch_new,
};

/** \} */


/* -------------------------------------------------------------------- */

/** \name Public API
* \{ */

PyObject *BPyGPUBatch_CreatePyObject(GPUBatch *batch)
{
	BPyGPUBatch *self;

#ifdef USE_GPU_PY_REFERENCES
	self = (BPyGPUBatch *)_PyObject_GC_New(&BPyGPUBatch_Type);
	self->references = NULL;
#else
	self = PyObject_New(BPyGPUBatch, &BPyGPUBatch_Type);
#endif

	self->batch = batch;

	return (PyObject *)self;
}

/** \} */

#undef BPY_GPU_BATCH_CHECK_OBJ
