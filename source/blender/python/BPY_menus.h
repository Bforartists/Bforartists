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
 * Contributor(s): Willian P. Germano
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
*/

#ifndef BPY_MENUS_H
#define BPY_MENUS_H

/* This header exposes BPyMenu related public declarations.  The implementation
 * adds 'dynamic' menus to Blender, letting scripts register themselves in any
 * of a few pre-defined (trivial to upgrade) places in menus.  These places or
 * slots are called groups here (Import, Export, etc).  This is how it works:
 * - scripts at some specific folder (only the user pref U.pythondir, right
 * now) are scanned for registration info.
 * - this data is also saved to a .Bpymenus file at the user's home dir and
 * only re-created when the scripts folder gets modified.
 * - on start-up Blender uses this info to fill a table, which is used to
 * create the menu entries when they are needed (see header_info.c or
 * header_script.c, under source/blender/src/, for examples).
*/

/* These two structs hold py menu/submenu info.
 * BPyMenu holds a script's name (as should appear in the menu) and filename,
 * plus an optional list of submenus.  Each submenu is related to a string
 * (arg) that the script can get from the __script__ pydict, to know which
 * submenu was chosen. */

typedef struct BPySubMenu {
	char *name;
	char *arg;
	struct BPySubMenu *next;
} BPySubMenu;

typedef struct BPyMenu {
	char *name;
	char *filename;
	char *tooltip;
	struct BPySubMenu *submenus;
	struct BPyMenu *next;
} BPyMenu;

/* Scripts can be added to only a few pre-defined places in menus, like
 * File->Import, File->Export, etc. (for speed and better control).
 * To make a new menu 'slot' available for scripts:
 * - add an entry to the enum below, right before PYMENU_TOTAL, of course;
 * - update the bpymenu_group_atoi() and BPyMenu_group_itoa() functions in
 * BPY_menus.c; 
 * - add the necessary code to the header_***.c file in
 * source/blender/src/, like done in header_info.c for import/export;
 * - update the bpython registering function and its documentation to include
 * the new group.
*/ 
typedef enum {
	PYMENU_IMPORT,
	PYMENU_EXPORT,
	PYMENU_MISC,
	PYMENU_TOTAL
} PYMENUHOOKS;

/* BPyMenuTable holds all registered pymenus, as linked lists for each menu
 * where they can appear (see PYMENUHOOKS enum above).
*/
BPyMenu *BPyMenuTable[PYMENU_TOTAL];

/* public functions: */
void BPyMenu_Init(void);
void BPyMenu_RemoveAllEntries(void);
void BPyMenu_PrintAllEntries(void);
char *BPyMenu_CreatePupmenuStr(BPyMenu *pym, short group);
char *BPyMenu_group_itoa (short group);

#endif /* BPY_MENUS_H */
