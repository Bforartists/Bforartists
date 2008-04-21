/**
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
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 * 
 */

#ifndef BLO_READBLENFILE_H
#define BLO_READBLENFILE_H

#ifdef __cplusplus
extern "C" {
#endif

	BlendFileData *
BLO_readblenfilename(
	char *fileName, 
	BlendReadError *error_r);

	BlendFileData *
BLO_readblenfilehandle(
	int fileHandle, 
	BlendReadError *error_r);

	BlendFileData *
BLO_readblenfilememory(
	char *fromBuffer,
	int fromBufferSize, 
	BlendReadError *error_r);


	void
BLO_setcurrentversionnumber(
	char array[4]);

	void
BLO_setversionnumber(
	char array[4],
	int version);

	int
blo_is_a_runtime(
	char *file);

	BlendFileData *
blo_read_runtime(
	char *file, 
	BlendReadError *error_r);

#define BLO_RESERVEDSIZE 12
extern char *headerMagic;

#ifdef __cplusplus
}
#endif

#endif /* BLO_READBLENFILE_H */

