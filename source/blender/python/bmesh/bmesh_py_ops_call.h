/* SPDX-FileCopyrightText: 2012 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup pybmesh
 */

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
  PyObject_HEAD /* Required Python macro. */
  const char *opname;
} BPy_BMeshOpFunc;

/**
 * This is the `__call__` for `bmesh.ops.xxx()`.
 */
PyObject *BPy_BMO_call(BPy_BMeshOpFunc *self, PyObject *args, PyObject *kw);

#ifdef __cplusplus
}
#endif
