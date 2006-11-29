/**
 * $Id: BKE_idprop.h
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
 * Contributor(s): Joseph Eagar
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */
 
#ifndef _BKE_IDPROP_H
#define _BKE_IDPROP_H

#include "DNA_ID.h"

/*
these two are included for their (new :P )function
pointers.
*/
#include "BLO_readfile.h"
#include "BLO_writefile.h"

struct WriteData;
struct FileData;

struct IDProperty;
struct ID;

typedef union {
	int i;
	float f;
	char *str;
	struct ID *id;
	struct {
		short type;
		short len;
	} array;
	struct {
		int matvec_size;
		float *example;
	} matrix_or_vector;
} IDPropertyTemplate;

/* ----------- Array Type ----------- */
/*this function works for strings too!*/
void IDP_ResizeArray(struct IDProperty *prop, int newlen);
void IDP_FreeArray(struct IDProperty *prop);
void IDP_UnlinkArray(struct IDProperty *prop);

/* ---------- String Type ------------ */
void IDP_AssignString(struct IDProperty *prop, char *st);
void IDP_ConcatStringC(struct IDProperty *prop, char *st);
void IDP_ConcatString(struct IDProperty *str1, struct IDProperty *append);
void IDP_FreeString(struct IDProperty *prop);

/*-------- ID Type -------*/
void IDP_LinkID(struct IDProperty *prop, ID *id);
void IDP_UnlinkID(struct IDProperty *prop);

/*-------- Group Functions -------*/
/*
This function has a sanity check to make sure ID properties with the same name don't
get added to the group.

The sanity check just means the property is not added to the group if another property
exists with the same name; the client code using ID properties then needs to detect this 
(the function that adds new properties to groups, IDP_AddToGroup, returns 0 if a property can't
be added to the group, and 1 if it can) and free the property.

Currently the code to free ID properties is designesd to leave the actual struct
you pass it un-freed, this is needed for how the system works.  This means
to free an ID property, you first call IDP_FreeProperty then MEM_freeN the
struct.  In the future this will just be IDP_FreeProperty and the code will
be reorganized to work properly.
*/
int IDP_AddToGroup(struct IDProperty *group, struct IDProperty *prop);
void IDP_RemFromGroup(struct IDProperty *group, struct IDProperty *prop);
IDProperty *IDP_GetPropertyFromGroup(struct IDProperty *prop, char *name);

/*Get an iterator to iterate over the members of an id property group.
 Note that this will automatically free the iterator once iteration is complete;
 if you stop the iteration before hitting the end, make sure to call
 IDP_FreeIterBeforeEnd().*/
void *IDP_GetGroupIterator(struct IDProperty *prop);

/*Returns the next item in the iteration.  To use, simple for a loop like the following:
 while (IDP_GroupIterNext(iter) != NULL) {
	. . .
 }*/
void *IDP_GroupIterNext(void *vself);

/*Frees the iterator pointed to at vself, only use this if iteration is stopped early; 
  when the iterator hits the end of the list it'll automatially free itself.*/
void IDP_FreeIterBeforeEnd(void *vself);

/*-------- Main Functions --------*/
/*Get the Group property that contains the id properties for ID id.  Set create_if_needed
  to create the Group property and attach it to id if it doesn't exist; otherwise
  the function will return NULL if there's no Group property attached to the ID.*/
struct IDProperty *IDP_GetProperties(struct ID *id, int create_if_needed);

/*
Allocate a new ID.

This function takes three arguments: the ID property type, a union which defines
it's initial value, and a name.

The union is simple to use; see the top of this header file for its definition. 
An example of using this function:

 IDPropertyTemplate val;
 IDProperty *group, *idgroup, *color;
 group = IDP_New(IDP_GROUP, val, "group1"); //groups don't need a template.

 val.array.len = 4
 val.array.type = IDP_FLOAT;
 color = IDP_New(IDP_ARRAY, val, "color1");

 idgroup = IDP_GetProperties(some_id, 1);
 IDP_AddToGroup(idgroup, color);
 IDP_AddToGroup(idgroup, group);

Note that you MUST either attach the id property to an id property group with 
IDP_AddToGroup or MEM_freeN the property, doing anything else might result in
a memory leak.
*/
struct IDProperty *IDP_New(int type, IDPropertyTemplate val, char *name);
\
/*NOTE: this will free all child properties of list arrays and groups!
  Also, note that this does NOT unlink anything!  Plus it doesn't free
  the actual struct IDProperty struct either.*/
void IDP_FreeProperty(struct IDProperty *prop);

/*Unlinks any struct IDProperty<->ID linkage that might be going on.*/
void IDP_UnlinkProperty(struct IDProperty *prop);

#endif /* _BKE_IDPROP_H */
