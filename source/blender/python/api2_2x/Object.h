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
 * Contributor(s): Michel Selten
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
*/

#ifndef EXPP_OBJECT_H
#define EXPP_OBJECT_H

#include <Python.h>
#include <stdio.h>
#include <BDR_editobject.h>
#include <BKE_armature.h>
#include <BKE_curve.h>
#include <BKE_global.h>
#include <BKE_library.h>
#include <BKE_main.h>
#include <BKE_mesh.h>
#include <BKE_object.h>
#include <BKE_scene.h>
#include <BLI_arithb.h>
#include <BLI_blenlib.h>
#include <DNA_armature_types.h>
#include <DNA_ID.h>
#include <DNA_ika_types.h>
#include <DNA_listBase.h>
#include <DNA_scene_types.h>
#include <DNA_userdef_types.h>
#include <DNA_view3d_types.h>

#include "gen_utils.h"
#include "modules.h"

/* The Object PyType Object defined in Object.c */
extern PyTypeObject Object_Type;

#define C_Object_Check(v) \
    ((v)->ob_type == &Object_Type) /* for type checking */

/*****************************************************************************/
/* Python C_Object structure definition.                                     */
/*****************************************************************************/
struct C_Object;

typedef struct {
    PyObject_HEAD
    struct Object   * object;

    /* points to the data. This only is set when there's a valid PyObject */
    /* that points to the linked data. */
    PyObject        * data;

    /* points to the parent object. This is only set when there's a valid */
    /* PyObject (already created at some point). */
    struct C_Object * parent;

    /* points to the object that is tracking this object. This is only set */
    /* when there's a valid PyObject (already created at some point). */
    struct C_Object * track;
} C_Object;

#endif /* EXPP_OBJECT_H */
