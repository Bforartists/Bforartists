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
 *
 */

#include <stdio.h>
#include "GEN_messaging.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

	int
BLO_readblenfilememory(
	char *fromBuffer, int fromBufferSize)
{
#ifndef NDEBUG
	fprintf(GEN_errorstream,
			"Error BLO_readblenfilename is a stub\n");
#endif
	return(1);
}

	int
BLO_readblenfilename(
	char *fileName)
{
#ifndef NDEBUG
	fprintf(GEN_errorstream,
			"Error BLO_readblenfilename is a stub\n");
#endif
	return(1);
}

	int
BLO_readblenfilehandle(
	int fileHandle)
{
#ifndef NDEBUG
	fprintf(GEN_errorstream,
			"Error BLO_readblenfilehandle is a stub\n");
#endif
	return(1);
}

	int
BLO_is_a_runtime(
	char *file)
{
#ifndef NDEBUG
	fprintf(GEN_errorstream,
			"Error BLO_is_a_runtime is a stub\n");
#endif
	return 0;
}

	int
BLO_read_runtime(
	char *file) 
{
#ifndef NDEBUG
	fprintf(GEN_errorstream,
			"Error BLO_read_runtime is a stub\n");
#endif
	return 0;
}
