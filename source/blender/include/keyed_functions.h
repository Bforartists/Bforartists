/* $Id$ 
/*
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


#define KEY_GETPTR(x) (g_ptrtab ? g_ptrtab[x] : 0)

/* these are the defines for the keyed functions:

	 #define key_func<n>  <function name to be behind key>

   This function must be of type "int func(void*)"

   To prevent symbol table dumpers from retrieving certain key
   functions too easily, some of those functions have nonsense names.
*/

#define key_func1 make_beautiful_animation
#define key_func2 key_return_true
#define key_func3 calc_memleak
/* add the corresponding function pointer defines here.
   Example:

	   #define key_func4 my_protected_function_name
	   #define MY_PROTECTED_FUNCTION_PTR  KEY_GETPTR(KEY_FUNC3)

   KEY_GETPTR(KEY_FUNC3) corresponds to the function pointer to function
   key_func3 after the python key code unscrambled the function pointer tables.
   Also add pointer initializations to these functions in 
   license_key.c:init_ftable() if necessary.
*/

#define KEY_WRITE_RUNTIME		KEY_GETPTR(KEY_FUNC1)
#define KEY_RETURN_TRUE			KEY_GETPTR(KEY_FUNC2)
#define KEY_NLA_EVENT			KEY_GETPTR(KEY_FUNC3)

/* PROTOS */
int make_beautiful_animation(void *vp);
int calc_memleak (void* ptr);


