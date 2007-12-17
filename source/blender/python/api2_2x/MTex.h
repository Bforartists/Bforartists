/* 
 * $Id: MTex.h 10269 2007-03-15 01:09:14Z campbellbarton $
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
 * Contributor(s): Alex Mole
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
*/

#ifndef EXPP_MTEX_H
#define EXPP_MTEX_H

#include <Python.h>
#include "DNA_texture_types.h"


/*****************************************************************************/
/* Python BPy_MTex structure definition                                      */
/*****************************************************************************/

typedef struct {
	PyObject_HEAD
	MTex * mtex;
} BPy_MTex;

extern PyTypeObject MTex_Type;

#define BPy_MTex_Check(v)  ((v)->ob_type == &MTex_Type)


/*****************************************************************************/
/* Module Blender.Texture.MTex - public functions                            */
/*****************************************************************************/

PyObject *MTex_Init( void );
PyObject *MTex_CreatePyObject( struct MTex *obj );
MTex *MTex_FromPyObject( PyObject * py_obj );


#endif				/* EXPP_MTEX_H */
