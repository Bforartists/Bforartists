/**
 * $Id$
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
 */

#include <stdio.h>

#ifdef _WIN32
#include <windows.h>
#endif

#include "MT_assert.h"

#ifdef _MSC_VER
#define _snprintf snprintf
#endif

// Query the user if they want to break/abort the program, ignore the assert, or ignore all future
// occurance of the assert.
int MT_QueryAssert(char *file, int line, char *predicate, int *do_assert)
{
#ifdef _WIN32
	if (*do_assert)
	{
		char buffer[1024];
		snprintf(buffer, 1024, "ASSERT %s:%d: %s failed.\nWould you like to debug? (Cancel = ignore)", file, line, predicate);
		int result = MessageBox(NULL, buffer, "ASSERT failed.", MB_YESNOCANCEL|MB_ICONERROR);
		if (result == IDCANCEL)
		{
			*do_assert = 0;
			return 0;
		}
		
		return result == IDYES;
	}
#endif
	printf("ASSERT %s:%d: %s failed.\n", file, line, predicate);
	return *do_assert;
}
