/**
 * $Id: idprop.c
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
 
#include "DNA_listBase.h"
#include "DNA_ID.h"

#include "BKE_idprop.h"
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_utildefines.h"

#include "BLI_blenlib.h"

#include "MEM_guardedalloc.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BSTR_EQ(a, b)	(*(a) == *(b) && !strcmp(a, b))

/* IDPropertyTemplate is a union in DNA_ID.h */
static char idp_size_table[] = {
	0, /*strings don't have fixed sizes :)*/
	sizeof(int),
	sizeof(float),
	sizeof(float)*3, /*Vector type*/
	sizeof(float)*16, /*Matrix type, we allocate max 4x4 even if in 3x3 mode*/
	0, /*arrays don't have a fixed size either :)*/
	sizeof(ListBase), /*Group type*/
	sizeof(void*)
};


/* ----------- Array Type ----------- */

/*this function works for strings too!*/
void IDP_ResizeArray(IDProperty *prop, int newlen)
{
	void *newarr;
	int newsize=newlen;

	/*first check if the array buffer size has room*/
	/*if newlen is 200 chars less then totallen, reallocate anyway*/
	if (newlen <= prop->totallen && prop->totallen - newlen < 200) {
		prop->len = newlen;
		return;
	}

	/* - Note: This code comes from python, here's the corrusponding comment. - */
	/* This over-allocates proportional to the list size, making room
	 * for additional growth.  The over-allocation is mild, but is
	 * enough to give linear-time amortized behavior over a long
	 * sequence of appends() in the presence of a poorly-performing
	 * system realloc().
	 * The growth pattern is:  0, 4, 8, 16, 25, 35, 46, 58, 72, 88, ...
	 */
	newsize = (newsize >> 3) + (newsize < 9 ? 3 : 6) + newsize;

	newarr = MEM_callocN(idp_size_table[prop->type]*newsize, "idproperty array resized");
	/*newlen is bigger*/
	if (newlen >= prop->len) memcpy(newarr, prop->data.pointer, prop->len*idp_size_table[prop->type]);
	/*newlen is smaller*/
	else memcpy(newarr, prop->data.pointer, newlen*prop->len*idp_size_table[prop->type]);

	MEM_freeN(prop->data.pointer);
	prop->data.pointer = newarr;
	prop->len = newlen;
	prop->totallen = newsize;
}

 void IDP_FreeArray(IDProperty *prop)
{
	if (prop->data.pointer)
		MEM_freeN(prop->data.pointer);
}

/*taken from readfile.c*/
#define SWITCH_LONGINT(a) { \
    char s_i, *p_i; \
    p_i= (char *)&(a);  \
    s_i=p_i[0]; p_i[0]=p_i[7]; p_i[7]=s_i; \
    s_i=p_i[1]; p_i[1]=p_i[6]; p_i[6]=s_i; \
    s_i=p_i[2]; p_i[2]=p_i[5]; p_i[5]=s_i; \
    s_i=p_i[3]; p_i[3]=p_i[4]; p_i[4]=s_i; }



/* ---------- String Type ------------ */
void IDP_AssignString(IDProperty *prop, char *st)
{
	int stlen;

	stlen = strlen(st);

	IDP_ResizeArray(prop, stlen+1); /*make room for null byte :) */
	strcpy(prop->data.pointer, st);
}

void IDP_ConcatStringC(IDProperty *prop, char *st)
{
	int newlen;

	newlen = prop->len + strlen(st);
	/*we have to remember that prop->len includes the null byte for strings.
	 so there's no need to add +1 to the resize function.*/
	IDP_ResizeArray(prop, newlen);
	strcat(prop->data.pointer, st);
}

void IDP_ConcatString(IDProperty *str1, IDProperty *append)
{
	int newlen;

	/*since ->len for strings includes the NULL byte, we have to subtract one or
	 we'll get an extra null byte after each concatination operation.*/
	newlen = str1->len + append->len - 1;
	IDP_ResizeArray(str1, newlen);
	strcat(str1->data.pointer, append->data.pointer);
}

void IDP_FreeString(IDProperty *prop)
{
	MEM_freeN(prop->data.pointer);
}


/*-------- ID Type -------*/

void IDP_LinkID(IDProperty *prop, ID *id)
{
	if (prop->data.pointer) ((ID*)prop->data.pointer)->us--;
	prop->data.pointer = id;
	id_us_plus(id);
}

void IDP_UnlinkID(IDProperty *prop)
{
	((ID*)prop->data.pointer)->us--;
}

/*-------- Group Functions -------*/
/*returns 0 if an id property with the same name exists and it failed,
  or 1 if it succeeded in adding to the group.*/
int IDP_AddToGroup(IDProperty *group, IDProperty *prop)
{
	IDProperty *loop;
	for (loop=group->data.group.first; loop; loop=loop->next) {
		if (BSTR_EQ(loop->name, prop->name)) return 0;
	}

	group->len++;
	BLI_addtail(&group->data.group, prop);

	return 1;
}

void IDP_RemFromGroup(IDProperty *group, IDProperty *prop)
{
	group->len--;
	BLI_remlink(&group->data.group, prop);
}

IDProperty *IDP_GetPropertyFromGroup(IDProperty *prop, char *name)
{
	IDProperty *loop;
	for (loop=prop->data.group.first; loop; loop=loop->next) {
		if (strcmp(loop->name, name)==0) return loop;
	}
	return NULL;
}

typedef struct IDPIter {
	void *next;
	IDProperty *parent;
} IDPIter;

void *IDP_GetGroupIterator(IDProperty *prop)
{
	IDPIter *iter = MEM_callocN(sizeof(IDPIter), "IDPIter");
	iter->next = prop->data.group.first;
	iter->parent = prop;
	return (void*) iter;
}

void *IDP_GroupIterNext(void *vself)
{
	IDPIter *self = (IDPIter*) vself;
	Link *next = (Link*) self->next;
	if (self->next == NULL) {
		MEM_freeN(self);
		return NULL;
	}

	self->next = next->next;
	return (void*) next;
}

void IDP_FreeIterBeforeEnd(void *vself)
{
	MEM_freeN(vself);
}

/*Ok, the way things work, Groups free the ID Property structs of their children.
  This is because all ID Property freeing functions free only direct data (not the ID Property
  struct itself), but for Groups the child properties *are* considered
  direct data.*/
void IDP_FreeGroup(IDProperty *prop)
{
	IDProperty *loop, *next;
	for (loop=prop->data.group.first; loop; loop=next)
	{
		next = loop->next;
		IDP_FreeProperty(loop);
		MEM_freeN(loop);
	}
}


/*-------- Main Functions --------*/

IDProperty *IDP_GetProperties(ID *id, int create_if_needed)
{
	if (id->properties) return id->properties;
	else {
		if (create_if_needed) {
			id->properties = MEM_callocN(sizeof(IDProperty), "IDProperty");
			id->properties->type = IDP_GROUP;
		}
		return id->properties;
	}
}

IDProperty *IDP_New(int type, IDPropertyTemplate val, char *name)
{
	IDProperty *prop=NULL;

	switch (type) {
		case IDP_INT:
			prop = MEM_callocN(sizeof(IDProperty), "IDProperty int");
			prop->data.val = val.i;
			break;
		case IDP_FLOAT:
			prop = MEM_callocN(sizeof(IDProperty), "IDProperty float");
			*(float*)&prop->data.val = val.f;
			break;
		case IDP_ARRAY:
		{
			/*for now, we only support float and int arrays*/
			if (val.array.type == IDP_FLOAT || val.array.type == IDP_INT) {
				prop = MEM_callocN(sizeof(IDProperty), "IDProperty array");
				prop->len = prop->totallen = val.array.len;
				prop->subtype = val.array.type;
				prop->data.pointer = MEM_callocN(idp_size_table[val.array.type]*val.array.len, "id property array");
				break;
			} else {
				return NULL;
			}
		}
		case IDP_STRING:
		{
			char *st = val.str;
			int stlen;

			prop = MEM_callocN(sizeof(IDProperty), "IDProperty string");
			if (st == NULL) {
				prop->data.pointer = MEM_callocN(DEFAULT_ALLOC_FOR_NULL_STRINGS, "id property string 1");
				prop->totallen = DEFAULT_ALLOC_FOR_NULL_STRINGS;
				prop->len = 1; /*NULL string, has len of 1 to account for null byte.*/
			} else {
				stlen = strlen(st) + 1;
				prop->data.pointer = MEM_callocN(stlen, "id property string 2");
				prop->len = prop->totallen = stlen;
				strcpy(prop->data.pointer, st);
			}
			break;
		}
		case IDP_GROUP:
		{
			prop = MEM_callocN(sizeof(IDProperty), "IDProperty group");
			/* heh I think all needed values are set properly by calloc anyway :) */
			break;
		}
		case IDP_MATRIX:
			prop = MEM_callocN(sizeof(IDProperty), "IDProperty array");
			if (val.matrix_or_vector.matvec_size == IDP_MATRIX4X4)
				prop->data.pointer = MEM_callocN(sizeof(float)*4*4, "matrix 4x4 idproperty");
			else
				prop->data.pointer = MEM_callocN(sizeof(float)*3*3, "matrix 3x3 idproperty");
		case IDP_VECTOR:
			prop = MEM_callocN(sizeof(IDProperty), "IDProperty array");
			switch (val.matrix_or_vector.matvec_size) {
				case IDP_VECTOR4D:
					prop->data.pointer = MEM_callocN(sizeof(float)*4, "vector 4d idproperty");
					break;
				case IDP_VECTOR3D:
					prop->data.pointer = MEM_callocN(sizeof(float)*3, "vector 3d idproperty");
					break;
				case IDP_VECTOR2D:
					prop->data.pointer = MEM_callocN(sizeof(float)*2, "vector 2d idproperty");
					break;

			}
		default:
		{
			prop = MEM_callocN(sizeof(IDProperty), "IDProperty array");
			break;
		}
	}

	prop->type = type;
	strncpy(prop->name, name, MAX_IDPROP_NAME);
	return prop;
}

/*NOTE: this will free all child properties of list arrays and groups!
  Also, note that this does NOT unlink anything!  Plus it doesn't free
  the actual IDProperty struct either.*/
void IDP_FreeProperty(IDProperty *prop)
{
	switch (prop->type) {
		case IDP_ARRAY:
			IDP_FreeArray(prop);
			break;
		case IDP_STRING:
			IDP_FreeString(prop);
			break;
		case IDP_GROUP:
			IDP_FreeGroup(prop);
			break;
		case IDP_VECTOR:
		case IDP_MATRIX:
			MEM_freeN(prop->data.pointer);
			break;
	}
}

/*Unlinks any IDProperty<->ID linkage that might be going on.*/
void IDP_UnlinkProperty(IDProperty *prop)
{
	switch (prop->type) {
		case IDP_ID:
			IDP_UnlinkID(prop);
	}
}
