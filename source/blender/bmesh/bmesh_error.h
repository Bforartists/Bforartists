/*
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
 * Contributor(s): Joseph Eagar.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef _BMESH_ERROR_H
#define _BMESH_ERROR_H

/*----------- bmop error system ----------*/

/* pushes an error onto the bmesh error stack.
 * if msg is null, then the default message for the errorcode is used.*/
void BMO_RaiseError(BMesh *bm, BMOperator *owner, int errcode, const char *msg);

/* gets the topmost error from the stack.
 * returns error code or 0 if no error.*/
int BMO_GetError(BMesh *bm, const char **msg, BMOperator **op);
int BMO_HasError(BMesh *bm);

/* same as geterror, only pops the error off the stack as well */
int BMO_PopError(BMesh *bm, const char **msg, BMOperator **op);
void BMO_ClearStack(BMesh *bm);

#if 0
//this is meant for handling errors, like self-intersection test failures.
//it's dangerous to handle errors in general though, so disabled for now.

/* catches an error raised by the op pointed to by catchop.
 * errorcode is either the errorcode, or BMERR_ALL for any
 * error.*/
int BMO_CatchOpError(BMesh *bm, BMOperator *catchop, int errorcode, char **msg);
#endif

#define BM_ELEM_INDEX_VALIDATE(_bm, _msg_a, _msg_b) \
	BM_ElemIndex_Validate(_bm, __FILE__ ":" STRINGIFY(__LINE__), __func__, _msg_a, _msg_b)

/*------ error code defines -------*/

/*error messages*/
#define BMERR_SELF_INTERSECTING			1
#define BMERR_DISSOLVEDISK_FAILED		2
#define BMERR_CONNECTVERT_FAILED		3
#define BMERR_WALKER_FAILED				4
#define BMERR_DISSOLVEFACES_FAILED		5
#define BMERR_DISSOLVEVERTS_FAILED		6
#define BMERR_TESSELATION				7
#define BMERR_NONMANIFOLD				8
#define BMERR_INVALID_SELECTION			9
#define BMERR_MESH_ERROR				10

#endif /* _BMESH_ERROR_H */
