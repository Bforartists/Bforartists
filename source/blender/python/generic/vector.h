/* $Id$
 *
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Willian P. Germano & Joseph Gilbert
 *
 * ***** END GPL LICENSE BLOCK *****
 *
 */

#ifndef EXPP_vector_h
#define EXPP_vector_h

#include <Python.h>
#include "../intern/bpy_compat.h"

extern PyTypeObject vector_Type;

#define VectorObject_Check(v) (((PyObject *)v)->ob_type == &vector_Type)

typedef struct {
	PyObject_VAR_HEAD 
	float *vec;					/*1D array of data (alias), wrapped status depends on wrapped status */
	PyObject *user;					/* if this vector references another object, otherwise NULL, *Note* this owns its reference */
	unsigned char size;			/* vec size 2,3 or 4 */
	unsigned char wrapped;		/* wrapped data type? */
	unsigned char callback_type;	/* which user funcs do we adhere to, RNA, GameObject, etc */
	unsigned char subtype;		/* subtype: location, rotation... to avoid defining many new functions for every attribute of the same type */
	
} VectorObject;

/*prototypes*/
PyObject *newVectorObject(float *vec, int size, int type);
PyObject *newVectorObject_cb(PyObject *user, int size, int callback_type, int subtype);

#endif				/* EXPP_vector_h */
