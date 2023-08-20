/* SPDX-FileCopyrightText: 2016 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup intern_mantaflow
 */

#ifndef MANTA_PYTHON_API_H
#define MANTA_PYTHON_API_H

#include "Python.h"

#ifdef __cplusplus
extern "C" {
#endif

PyObject *Manta_initPython(void);

#ifdef __cplusplus
}
#endif

#endif
