/* 
 * $Id$
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
 * This is a new part of Blender.
 *
 * Contributor(s): Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
*/

#ifndef EXPP_BPY_CONFIG_H
#define EXPP_BPY_CONFIG_H

#include <Python.h>

/* The Main PyType Object defined in Main.c */
extern PyTypeObject Config_Type;

#define BPy_Config_Check(v) \
    ((v)->ob_type == &Config_Type)

/* Main sequence, iterate on the libdatas listbase*/
typedef struct {
	PyObject_VAR_HEAD /* required python macro   */
} BPy_Config;

PyObject *Config_CreatePyObject();


#endif				/* EXPP_BPY_CONFIG_H */
