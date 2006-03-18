/* 
 * $Id$
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

#ifndef EXPP_GROUP_H
#define EXPP_GROUP_H

#include <Python.h>
#include "DNA_group_types.h"

/* The Group PyTypeObject defined in Group.c */
extern PyTypeObject Group_Type;
extern PyTypeObject MGroupObSeq_Type;

#define BPy_Group_Check(v)       ((v)->ob_type == &Mesh_Type)
#define BPy_MGroupObSeq_Check(v)      ((v)->ob_type == &MGroupObSeq_Type)

/*****************************************************************************/
/* Python BPy_Group structure definition.                                  */
/*****************************************************************************/
typedef struct {
	PyObject_HEAD /* required python macro   */
	struct Group *group; /* Blender group type, can be NULL when unlinked */
} BPy_Group;


/* Group object sequence, iterate on the groups object listbase*/
typedef struct {
	PyObject_VAR_HEAD /* required python macro   */
	BPy_Group *bpygroup; /* link to the python group so we can know if its been removed */
	GroupObject *iter; /* so we can iterate over the objects */
} BPy_MGroupObSeq;

PyObject *Group_Init( void );
PyObject *Group_CreatePyObject( struct Group *group );
Group *Group_FromPyObject( PyObject * py_obj );
int Group_CheckPyObject( PyObject * py_obj );
Group *GetGroupByName( char *name );

#endif				/* EXPP_GROUP_H */
