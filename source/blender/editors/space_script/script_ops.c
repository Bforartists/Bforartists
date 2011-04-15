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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 *
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_script/script_ops.c
 *  \ingroup spscript
 */


#include <stdlib.h>
#include <math.h>


#include "DNA_screen_types.h"
#include "DNA_space_types.h"

#include "BLI_math.h"
#include "BLI_blenlib.h"

#include "BKE_context.h"

#include "RNA_access.h"

#include "WM_api.h"
#include "WM_types.h"


#include "script_intern.h"


/* ************************** registration **********************************/

void script_operatortypes(void)
{
	WM_operatortype_append(SCRIPT_OT_python_file_run);
	WM_operatortype_append(SCRIPT_OT_reload);
}

void script_keymap(wmKeyConfig *keyconf)
{
	wmKeyMap *keymap= WM_keymap_find(keyconf, "Script", SPACE_SCRIPT, 0);

	/* TODO - this is just while we have no way to load a text datablock */
	RNA_string_set(WM_keymap_add_item(keymap, "SCRIPT_OT_python_file_run", PKEY, KM_PRESS, KM_CTRL|KM_SHIFT|KM_ALT, 0)->ptr, "filepath", "test.py");
}

