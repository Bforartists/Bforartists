/* 
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * This is a new part of Blender.
 *
 * Contributor(s): Willian P. Germano
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
*/

#ifndef EXPP_CAMERA_H
#define EXPP_CAMERA_H

#include <Python.h>

#include <DNA_camera_types.h>

#include "constant.h"
#include "gen_utils.h"

/* The Camera PyType Object defined in Camera.c */
extern PyTypeObject Camera_Type;

#define BPy_Camera_Check(v) \
    ((v)->ob_type == &Camera_Type) /* for type checking */

/*****************************************************************************/
/* Python BPy_Camera structure definition:                                   */
/*****************************************************************************/
typedef struct {
  PyObject_HEAD
  Camera *camera;

} BPy_Camera;

/*****************************************************************************/
/* Python Camera_Type helper functions needed by Blender (the Init function) */
/* and Object modules.                                                       */
/*****************************************************************************/
PyObject *M_Camera_Init (void);
PyObject *Camera_CreatePyObject (Camera *cam);
Camera   *Camera_FromPyObject (PyObject *pyobj);
int       Camera_CheckPyObject (PyObject *pyobj);


#endif /* EXPP_CAMERA_H */
