/**
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
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 * dxf/vrml/videoscape external file io function prototypes
 */

#ifndef BKE_EXOTIC_H
#define BKE_EXOTIC_H

struct Mesh;

void mcol_to_rgba(unsigned int col, float *r, float *g, float *b, float *a);
unsigned int *mcol_to_vcol(struct Mesh *me); // used in py_main.c

/**
 * Reads all 3D fileformats other than Blender fileformat
 * @retval 0 The file could not be read.
 * @retval 1 The file was read succesfully.
 * @attention Used in filesel.c
 */
int BKE_read_exotic(char *name);

void write_dxf(char *str);
void write_vrml(char *str);
void write_videoscape(char *str);
void write_stl(char *str);

#endif

