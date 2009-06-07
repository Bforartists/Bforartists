/**
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
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <math.h>
#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_action_types.h"
#include "DNA_color_types.h"
#include "DNA_listBase.h"
#include "DNA_material_types.h"
#include "DNA_object_types.h"
#include "DNA_screen_types.h"
#include "DNA_texture_types.h"
#include "DNA_windowmanager_types.h"

#include "BKE_colortools.h"
#include "BKE_context.h"
#include "BKE_idprop.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_texture.h"
#include "BKE_utildefines.h"

#include "RNA_access.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "ED_screen.h"
#include "ED_util.h"

#include "WM_api.h"
#include "WM_types.h"

#include "interface_intern.h"

#define DEF_BUT_WIDTH 		150
#define DEF_ICON_BUT_WIDTH	20
#define DEF_BUT_HEIGHT		20

/*************************** RNA Utilities ******************************/

uiBut *uiDefAutoButR(uiBlock *block, PointerRNA *ptr, PropertyRNA *prop, int index, char *name, int icon, int x1, int y1, int x2, int y2)
{
	uiBut *but=NULL;
	const char *propname= RNA_property_identifier(prop);
	int arraylen= RNA_property_array_length(prop);

	switch(RNA_property_type(prop)) {
		case PROP_BOOLEAN: {
			int value, length;

			if(arraylen && index == -1)
				return NULL;

			length= RNA_property_array_length(prop);

			if(length)
				value= RNA_property_boolean_get_index(ptr, prop, index);
			else
				value= RNA_property_boolean_get(ptr, prop);

			if(icon && name && strcmp(name, "") == 0)
				but= uiDefIconButR(block, ICONTOG, 0, icon, x1, y1, x2, y2, ptr, propname, index, 0, 0, -1, -1, NULL);
			else if(icon)
				but= uiDefIconTextButR(block, ICONTOG, 0, icon, name, x1, y1, x2, y2, ptr, propname, index, 0, 0, -1, -1, NULL);
			else
				but= uiDefButR(block, OPTION, 0, name, x1, y1, x2, y2, ptr, propname, index, 0, 0, -1, -1, NULL);
			break;
		}
		case PROP_INT:
		case PROP_FLOAT:
			if(arraylen && index == -1) {
				if(RNA_property_subtype(prop) == PROP_COLOR)
					but= uiDefButR(block, COL, 0, name, x1, y1, x2, y2, ptr, propname, 0, 0, 0, -1, -1, NULL);
			}
			else if(RNA_property_subtype(prop) == PROP_PERCENTAGE)
				but= uiDefButR(block, NUMSLI, 0, name, x1, y1, x2, y2, ptr, propname, index, 0, 0, -1, -1, NULL);
			else
				but= uiDefButR(block, NUM, 0, name, x1, y1, x2, y2, ptr, propname, index, 0, 0, -1, -1, NULL);
			break;
		case PROP_ENUM:
			but= uiDefButR(block, MENU, 0, NULL, x1, y1, x2, y2, ptr, propname, index, 0, 0, -1, -1, NULL);
			break;
		case PROP_STRING:
			but= uiDefButR(block, TEX, 0, name, x1, y1, x2, y2, ptr, propname, index, 0, 0, -1, -1, NULL);
			break;
		case PROP_POINTER: {
			PointerRNA pptr;
			int icon;

			pptr= RNA_property_pointer_get(ptr, prop);
			if(!pptr.type)
				pptr.type= RNA_property_pointer_type(ptr, prop);
			icon= RNA_struct_ui_icon(pptr.type);

			but= uiDefIconTextButR(block, IDPOIN, 0, icon, name, x1, y1, x2, y2, ptr, propname, index, 0, 0, -1, -1, NULL);
			break;
		}
		case PROP_COLLECTION: {
			char text[256];
			sprintf(text, "%d items", RNA_property_collection_length(ptr, prop));
			but= uiDefBut(block, LABEL, 0, text, x1, y1, x2, y2, NULL, 0, 0, 0, 0, NULL);
			uiButSetFlag(but, UI_BUT_DISABLED);
			break;
		}
		default:
			but= NULL;
			break;
	}

	return but;
}

void uiDefAutoButsRNA(const bContext *C, uiLayout *layout, PointerRNA *ptr)
{
	CollectionPropertyIterator iter;
	PropertyRNA *iterprop, *prop;
	uiLayout *split;
	char *name;

	uiItemL(layout, (char*)RNA_struct_ui_name(ptr->type), 0);

	iterprop= RNA_struct_iterator_property(ptr->type);
	RNA_property_collection_begin(ptr, iterprop, &iter);

	for(; iter.valid; RNA_property_collection_next(&iter)) {
		prop= iter.ptr.data;

		if(strcmp(RNA_property_identifier(prop), "rna_type") == 0)
			continue;

		split = uiLayoutSplit(layout);

		name= (char*)RNA_property_ui_name(prop);

		uiItemL(uiLayoutColumn(split, 0), name, 0);
		uiItemFullR(uiLayoutColumn(split, 0), "", 0, ptr, prop, -1, 0, 0, 0, 0);
	}

	RNA_property_collection_end(&iter);
}

/* temp call, single collumn, test for toolbar only */
void uiDefAutoButsRNA_single(const bContext *C, uiLayout *layout, PointerRNA *ptr)
{
	CollectionPropertyIterator iter;
	PropertyRNA *iterprop, *prop;
	uiLayout *col;
	char *name;
	
	uiItemL(layout, (char*)RNA_struct_ui_name(ptr->type), 0);
	
	iterprop= RNA_struct_iterator_property(ptr->type);
	RNA_property_collection_begin(ptr, iterprop, &iter);
	
	for(; iter.valid; RNA_property_collection_next(&iter)) {
		prop= iter.ptr.data;
		
		if(strcmp(RNA_property_identifier(prop), "rna_type") == 0)
			continue;
		
		name= (char*)RNA_property_ui_name(prop);
		col= uiLayoutColumn(layout, 1);
		uiItemL(col, name, 0);
		
		/* temp hack to show normal button for spin/screw */
		if(strcmp(name, "Axis")==0) {
			uiDefButR(uiLayoutGetBlock(layout), BUT_NORMAL, 0, name, 0, 0, 100, 100, ptr, "axis", -1, 0, 0, -1, -1, NULL);
		}
		else uiItemFullR(col, "", 0, ptr, prop, -1, 0, 0, 0, 0);
	}
	
	RNA_property_collection_end(&iter);
}

/***************************** ID Utilities *******************************/

typedef struct uiIDPoinParams {
	uiIDPoinFunc func;
	ID *id;
	short id_code;
	short browsenr;
} uiIDPoinParams;

static void idpoin_cb(bContext *C, void *arg_params, void *arg_event)
{
	Main *bmain;
	ListBase *lb;
	uiIDPoinParams *params= (uiIDPoinParams*)arg_params;
	uiIDPoinFunc func= params->func;
	ID *id= params->id, *idtest;
	int nr, event= GET_INT_FROM_POINTER(arg_event);

	bmain= CTX_data_main(C);
	lb= wich_libbase(bmain, params->id_code);
	
	if(event == UI_ID_BROWSE && params->browsenr == 32767)
		event= UI_ID_ADD_NEW;
	else if(event == UI_ID_BROWSE && params->browsenr == 32766)
		event= UI_ID_OPEN;

	switch(event) {
		case UI_ID_RENAME:
			if(id) test_idbutton(id->name+2);
			else return;
			break;
		case UI_ID_BROWSE: {
			/* ID can be NULL, if nothing was assigned yet */
			if(lb->first==NULL) return;

			if(params->browsenr== -2) {
				/* XXX implement or find a replacement (ID can be NULL!)
				 * activate_databrowse((ID *)G.buts->lockpoin, GS(id->name), 0, B_MESHBROWSE, &params->browsenr, do_global_buttons); */
				return;
			}
			if(params->browsenr < 0)
				return;

			for(idtest=lb->first, nr=1; idtest; idtest=idtest->next, nr++) {
				if(nr==params->browsenr) {
					if(id == idtest)
						return;

					id= idtest;

					break;
				}
			}
			break;
		}
		case UI_ID_DELETE:
			id= NULL;
			break;
		case UI_ID_FAKE_USER:
			if(id) {
				if(id->flag & LIB_FAKEUSER) id->us++;
				else id->us--;
			}
			else return;
			break;
		case UI_ID_PIN:
			break;
		case UI_ID_ADD_NEW:
			break;
		case UI_ID_OPEN:
			break;
		case UI_ID_ALONE:
			if(!id || id->us < 1)
				return;
			break;
		case UI_ID_LOCAL:
			if(!id || id->us < 1)
				return;
			break;
		case UI_ID_AUTO_NAME:
			break;
	}

	if(func)
		func(C, id, event);
}

int uiDefIDPoinButs(uiBlock *block, Main *bmain, ID *parid, ID *id, int id_code, short *pin_p, int x, int y, uiIDPoinFunc func, int events)
{
	ListBase *lb;
	uiBut *but;
	uiIDPoinParams *params, *dup_params;
	char *str=NULL, str1[10];
	int len, add_addbutton=0;

	/* setup struct that we will pass on with the buttons */
	params= MEM_callocN(sizeof(uiIDPoinParams), "uiIDPoinParams");
	params->id= id;
	params->id_code= id_code;
	params->func= func;

	lb= wich_libbase(bmain, id_code);

	/* create buttons */
	uiBlockBeginAlign(block);

	/* XXX solve?
	if(id && id->us>1)
		uiBlockSetCol(block, TH_BUT_SETTING1);

	if((events & UI_ID_PIN) && *pin_p)
		uiBlockSetCol(block, TH_BUT_SETTING2);
	*/
	
	/* pin button */
	if(id && (events & UI_ID_PIN)) {
		but= uiDefIconButS(block, ICONTOG, (events & UI_ID_PIN), ICON_KEY_DEHLT, x, y ,DEF_ICON_BUT_WIDTH,DEF_BUT_HEIGHT, pin_p, 0, 0, 0, 0, "Keeps this view displaying the current data regardless of what object is selected");
		uiButSetNFunc(but, idpoin_cb, MEM_dupallocN(params), SET_INT_IN_POINTER(UI_ID_PIN));
		x+= DEF_ICON_BUT_WIDTH;
	}

	/* browse menu */
	if(events & UI_ID_BROWSE) {
		char *extrastr= NULL;
		
		if(ELEM4(id_code, ID_MA, ID_TE, ID_BR, ID_PA))
			add_addbutton= 1;
		
		if(ELEM8(id_code, ID_SCE, ID_SCR, ID_MA, ID_TE, ID_WO, ID_IP, ID_AC, ID_BR) || id_code == ID_PA)
			extrastr= "ADD NEW %x 32767";
		else if(id_code==ID_TXT)
			extrastr= "OPEN NEW %x 32766 |ADD NEW %x 32767";
		else if(id_code==ID_SO)
			extrastr= "OPEN NEW %x 32766";

		/* XXX should be moved out of this function
		uiBlockSetButLock(block, G.scene->id.lib!=0, "Can't edit external libdata");
		if( id_code==ID_SCE || id_code==ID_SCR ) uiBlockClearButLock(block); */
		
		/* XXX should be moved out of this function
		if(curarea->spacetype==SPACE_BUTS)
			uiBlockSetButLock(block, id_code!=ID_SCR && G.obedit!=0 && G.buts->mainb==CONTEXT_EDITING, "Cannot perform in EditMode"); */
		
		if(parid)
			uiBlockSetButLock(block, parid->lib!=0, "Can't edit external libdata");

		if(lb) {
			if(id_code!=ID_IM || (events & UI_ID_BROWSE_RENDER))
				IDnames_to_pupstring(&str, NULL, extrastr, lb, id, &params->browsenr);
			else
				IMAnames_to_pupstring(&str, NULL, extrastr, lb, id, &params->browsenr);
		}

		dup_params= MEM_dupallocN(params);
		but= uiDefButS(block, MENU, 0, str, x, y, DEF_ICON_BUT_WIDTH, DEF_BUT_HEIGHT, &dup_params->browsenr, 0, 0, 0, 0, "Browse existing choices, or add new");
		uiButSetNFunc(but, idpoin_cb, dup_params, SET_INT_IN_POINTER(UI_ID_BROWSE));
		x+= DEF_ICON_BUT_WIDTH;
		
		uiBlockClearButLock(block);
	
		MEM_freeN(str);
	}

	/* text button with name */
	if(id) {
		/* XXX solve?
		if(id->us > 1)
			uiBlockSetCol(block, TH_BUT_SETTING1);
		*/
		/* pinned data? 
		if((events & UI_ID_PIN) && *pin_p)
			uiBlockSetCol(block, TH_BUT_SETTING2);
		*/
		/* redalert overrides pin color 
		if(id->us<=0)
			uiBlockSetCol(block, TH_REDALERT);
		*/
		uiBlockSetButLock(block, id->lib!=0, "Can't edit external libdata");
		
		/* name button */
		text_idbutton(id, str1);
		
		if(GS(id->name)==ID_IP) len= 110;
		else if((y) && (GS(id->name)==ID_AC)) len= 100; // comes from button panel (poselib)
		else if(y) len= 140;	// comes from button panel
		else len= 120;
		
		but= uiDefBut(block, TEX, 0, str1,x, y, (short)len, DEF_BUT_HEIGHT, id->name+2, 0.0, 21.0, 0, 0, "Displays current Datablock name. Click to change.");
		uiButSetNFunc(but, idpoin_cb, MEM_dupallocN(params), SET_INT_IN_POINTER(UI_ID_RENAME));

		x+= len;

		uiBlockClearButLock(block);
		
		/* lib make local button */
		if(id->lib) {
			if(id->flag & LIB_INDIRECT) uiDefIconBut(block, BUT, 0, 0 /* XXX ICON_DATALIB */,x,y,DEF_ICON_BUT_WIDTH,DEF_BUT_HEIGHT, 0, 0, 0, 0, 0, "Indirect Library Datablock. Cannot change.");
			else {
				but= uiDefIconBut(block, BUT, 0, 0 /* XXX ICON_PARLIB */, x,y,DEF_ICON_BUT_WIDTH,DEF_BUT_HEIGHT, 0, 0, 0, 0, 0, 
							  (events & UI_ID_LOCAL)? "Direct linked Library Datablock. Click to make local.": "Direct linked Library Datablock, cannot make local.");
				uiButSetNFunc(but, idpoin_cb, MEM_dupallocN(params), SET_INT_IN_POINTER(UI_ID_ALONE));
			}
			
			x+= DEF_ICON_BUT_WIDTH;
		}
		
		/* number of users / make local button */
		if((events & UI_ID_ALONE) && id->us>1) {
			int butwidth;

			uiBlockSetButLock(block, (events & UI_ID_PIN) && *pin_p, "Can't make pinned data single-user");
			
			sprintf(str1, "%d", id->us);
			butwidth= (id->us<10)? DEF_ICON_BUT_WIDTH: DEF_ICON_BUT_WIDTH+10;

			but= uiDefBut(block, BUT, 0, str1, x, y, butwidth, DEF_BUT_HEIGHT, 0, 0, 0, 0, 0, "Displays number of users of this data. Click to make a single-user copy.");
			uiButSetNFunc(but, idpoin_cb, MEM_dupallocN(params), SET_INT_IN_POINTER(UI_ID_ALONE));
			x+= butwidth;
			
			uiBlockClearButLock(block);
		}
		
		/* delete button */
		if(events & UI_ID_DELETE) {
			uiBlockSetButLock(block, (events & UI_ID_PIN) && *pin_p, "Can't unlink pinned data");
			if(parid && parid->lib);
			else {
				but= uiDefIconBut(block, BUT, 0, ICON_X, x,y,DEF_ICON_BUT_WIDTH,DEF_BUT_HEIGHT, 0, 0, 0, 0, 0, "Deletes link to this Datablock");
				uiButSetNFunc(but, idpoin_cb, MEM_dupallocN(params), SET_INT_IN_POINTER(UI_ID_DELETE));
				x+= DEF_ICON_BUT_WIDTH;
			}
			
			uiBlockClearButLock(block);
		}

		/* auto name button */
		if(events & UI_ID_AUTO_NAME) {
			if(parid && parid->lib);
			else {
				but= uiDefIconBut(block, BUT, 0, ICON_AUTO,x,y,DEF_ICON_BUT_WIDTH,DEF_BUT_HEIGHT, 0, 0, 0, 0, 0, "Generates an automatic name");
				uiButSetNFunc(but, idpoin_cb, MEM_dupallocN(params), SET_INT_IN_POINTER(UI_ID_AUTO_NAME));
				x+= DEF_ICON_BUT_WIDTH;
			}
		}

		/* fake user button */
		if(events & UI_ID_FAKE_USER) {
			but= uiDefButBitS(block, TOG, LIB_FAKEUSER, 0, "F", x,y,DEF_ICON_BUT_WIDTH,DEF_BUT_HEIGHT, &id->flag, 0, 0, 0, 0, "Saves this datablock even if it has no users");
			uiButSetNFunc(but, idpoin_cb, MEM_dupallocN(params), SET_INT_IN_POINTER(UI_ID_FAKE_USER));
			x+= DEF_ICON_BUT_WIDTH;
		}
	}
	/* add new button */
	else if(add_addbutton) {
		if(parid) uiBlockSetButLock(block, parid->lib!=0, "Can't edit external libdata");
		dup_params= MEM_dupallocN(params);
		but= uiDefButS(block, TOG, 0, "Add New", x, y, 110, DEF_BUT_HEIGHT, &dup_params->browsenr, params->browsenr, 32767.0, 0, 0, "Add new data block");
		uiButSetNFunc(but, idpoin_cb, dup_params, SET_INT_IN_POINTER(UI_ID_ADD_NEW));
		x+= 110;
	}
	
	uiBlockEndAlign(block);

	MEM_freeN(params);

	return x;
}

/* ****************************** default button callbacks ******************* */
/* ************ LEGACY WARNING, only to get things work with 2.48 code! ****** */

void test_idbutton_cb(struct bContext *C, void *namev, void *arg2)
{
	char *name= namev;
	
	test_idbutton(name+2);
}


void test_scriptpoin_but(struct bContext *C, char *name, ID **idpp)
{
	ID *id;
	
	id= CTX_data_main(C)->text.first;
	while(id) {
		if( strcmp(name, id->name+2)==0 ) {
			*idpp= id;
			return;
		}
		id= id->next;
	}
	*idpp= NULL;
}

void test_actionpoin_but(struct bContext *C, char *name, ID **idpp)
{
	ID *id;
	
	id= CTX_data_main(C)->action.first;
	while(id) {
		if( strcmp(name, id->name+2)==0 ) {
			id_us_plus(id);
			*idpp= id;
			return;
		}
		id= id->next;
	}
	*idpp= NULL;
}


void test_obpoin_but(struct bContext *C, char *name, ID **idpp)
{
	ID *id;
	
// XXX	if(idpp == (ID **)&(emptytex.object)) {
//		error("You must add a texture first");
//		*idpp= 0;
//		return;
//	}
	
	id= CTX_data_main(C)->object.first;
	while(id) {
		if( strcmp(name, id->name+2)==0 ) {
			*idpp= id;
			id_lib_extern(id);	/* checks lib data, sets correct flag for saving then */
			return;
		}
		id= id->next;
	}
	*idpp= NULL;
}

/* tests for an object of type OB_MESH */
void test_meshobpoin_but(struct bContext *C, char *name, ID **idpp)
{
	ID *id;

	id = CTX_data_main(C)->object.first;
	while(id) {
		Object *ob = (Object *)id;
		if(ob->type == OB_MESH && strcmp(name, id->name + 2) == 0) {
			*idpp = id;
			/* checks lib data, sets correct flag for saving then */
			id_lib_extern(id);
			return;
		}
		id = id->next;
	}
	*idpp = NULL;
}

void test_meshpoin_but(struct bContext *C, char *name, ID **idpp)
{
	ID *id;

	if( *idpp ) (*idpp)->us--;
	
	id= CTX_data_main(C)->mesh.first;
	while(id) {
		if( strcmp(name, id->name+2)==0 ) {
			*idpp= id;
			id_us_plus(id);
			return;
		}
		id= id->next;
	}
	*idpp= NULL;
}

void test_matpoin_but(struct bContext *C, char *name, ID **idpp)
{
	ID *id;

	if( *idpp ) (*idpp)->us--;
	
	id= CTX_data_main(C)->mat.first;
	while(id) {
		if( strcmp(name, id->name+2)==0 ) {
			*idpp= id;
			id_us_plus(id);
			return;
		}
		id= id->next;
	}
	*idpp= NULL;
}

void test_scenepoin_but(struct bContext *C, char *name, ID **idpp)
{
	ID *id;
	
	if( *idpp ) (*idpp)->us--;
	
	id= CTX_data_main(C)->scene.first;
	while(id) {
		if( strcmp(name, id->name+2)==0 ) {
			*idpp= id;
			id_us_plus(id);
			return;
		}
		id= id->next;
	}
	*idpp= NULL;
}

void test_grouppoin_but(struct bContext *C, char *name, ID **idpp)
{
	ID *id;
	
	if( *idpp ) (*idpp)->us--;
	
	id= CTX_data_main(C)->group.first;
	while(id) {
		if( strcmp(name, id->name+2)==0 ) {
			*idpp= id;
			id_us_plus(id);
			return;
		}
		id= id->next;
	}
	*idpp= NULL;
}

void test_texpoin_but(struct bContext *C, char *name, ID **idpp)
{
	ID *id;
	
	if( *idpp ) (*idpp)->us--;
	
	id= CTX_data_main(C)->tex.first;
	while(id) {
		if( strcmp(name, id->name+2)==0 ) {
			*idpp= id;
			id_us_plus(id);
			return;
		}
		id= id->next;
	}
	*idpp= NULL;
}

void test_imapoin_but(struct bContext *C, char *name, ID **idpp)
{
	ID *id;
	
	if( *idpp ) (*idpp)->us--;
	
	id= CTX_data_main(C)->image.first;
	while(id) {
		if( strcmp(name, id->name+2)==0 ) {
			*idpp= id;
			id_us_plus(id);
			return;
		}
		id= id->next;
	}
	*idpp= NULL;
}

/* autocomplete callback for  buttons */
void autocomplete_bone(struct bContext *C, char *str, void *arg_v)
{
	Object *ob= (Object *)arg_v;
	
	if(ob==NULL || ob->pose==NULL) return;
	
	/* search if str matches the beginning of name */
	if(str[0]) {
		AutoComplete *autocpl= autocomplete_begin(str, 32);
		bPoseChannel *pchan;
		
		for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next)
			autocomplete_do_name(autocpl, pchan->name);
		
		autocomplete_end(autocpl, str);
	}
}

/* autocomplete callback for buttons */
void autocomplete_vgroup(struct bContext *C, char *str, void *arg_v)
{
	Object *ob= (Object *)arg_v;
	
	if(ob==NULL) return;
	
	/* search if str matches the beginning of a name */
	if(str[0]) {
		AutoComplete *autocpl= autocomplete_begin(str, 32);
		bDeformGroup *dg;
		
		for(dg= ob->defbase.first; dg; dg= dg->next)
			if(dg->name!=str)
				autocomplete_do_name(autocpl, dg->name);
		
		autocomplete_end(autocpl, str);
	}
}


/* ----------- custom button group ---------------------- */

static void curvemap_buttons_zoom_in(bContext *C, void *cumap_v, void *unused)
{
	CurveMapping *cumap = cumap_v;
	float d;
	
	/* we allow 20 times zoom */
	if( (cumap->curr.xmax - cumap->curr.xmin) > 0.04f*(cumap->clipr.xmax - cumap->clipr.xmin) ) {
		d= 0.1154f*(cumap->curr.xmax - cumap->curr.xmin);
		cumap->curr.xmin+= d;
		cumap->curr.xmax-= d;
		d= 0.1154f*(cumap->curr.ymax - cumap->curr.ymin);
		cumap->curr.ymin+= d;
		cumap->curr.ymax-= d;
	}
}

static void curvemap_buttons_zoom_out(bContext *C, void *cumap_v, void *unused)
{
	CurveMapping *cumap = cumap_v;
	float d, d1;
	
	/* we allow 20 times zoom, but dont view outside clip */
	if( (cumap->curr.xmax - cumap->curr.xmin) < 20.0f*(cumap->clipr.xmax - cumap->clipr.xmin) ) {
		d= d1= 0.15f*(cumap->curr.xmax - cumap->curr.xmin);
		
		if(cumap->flag & CUMA_DO_CLIP) 
			if(cumap->curr.xmin-d < cumap->clipr.xmin)
				d1= cumap->curr.xmin - cumap->clipr.xmin;
		cumap->curr.xmin-= d1;
		
		d1= d;
		if(cumap->flag & CUMA_DO_CLIP) 
			if(cumap->curr.xmax+d > cumap->clipr.xmax)
				d1= -cumap->curr.xmax + cumap->clipr.xmax;
		cumap->curr.xmax+= d1;
		
		d= d1= 0.15f*(cumap->curr.ymax - cumap->curr.ymin);
		
		if(cumap->flag & CUMA_DO_CLIP) 
			if(cumap->curr.ymin-d < cumap->clipr.ymin)
				d1= cumap->curr.ymin - cumap->clipr.ymin;
		cumap->curr.ymin-= d1;
		
		d1= d;
		if(cumap->flag & CUMA_DO_CLIP) 
			if(cumap->curr.ymax+d > cumap->clipr.ymax)
				d1= -cumap->curr.ymax + cumap->clipr.ymax;
		cumap->curr.ymax+= d1;
	}
}

static void curvemap_buttons_setclip(bContext *C, void *cumap_v, void *unused)
{
	CurveMapping *cumap = cumap_v;
	
	curvemapping_changed(cumap, 0);
}	

static void curvemap_buttons_delete(bContext *C, void *cumap_v, void *unused)
{
	CurveMapping *cumap = cumap_v;
	
	curvemap_remove(cumap->cm+cumap->cur, SELECT);
	curvemapping_changed(cumap, 0);
}

/* NOTE: this is a block-menu, needs 0 events, otherwise the menu closes */
static uiBlock *curvemap_clipping_func(struct bContext *C, struct ARegion *ar, void *cumap_v)
{
	CurveMapping *cumap = cumap_v;
	uiBlock *block;
	uiBut *bt;
	
	block= uiBeginBlock(C, ar, "curvemap_clipping_func", UI_EMBOSS);
	
	/* use this for a fake extra empy space around the buttons */
	uiDefBut(block, LABEL, 0, "",			-4, 16, 128, 106, NULL, 0, 0, 0, 0, "");
	
	bt= uiDefButBitI(block, TOG, CUMA_DO_CLIP, 1, "Use Clipping",	 
										0,100,120,18, &cumap->flag, 0.0, 0.0, 10, 0, "");
	uiButSetFunc(bt, curvemap_buttons_setclip, cumap, NULL);

	uiBlockBeginAlign(block);
	uiDefButF(block, NUM, 0, "Min X ",	 0,74,120,18, &cumap->clipr.xmin, -100.0, cumap->clipr.xmax, 10, 0, "");
	uiDefButF(block, NUM, 0, "Min Y ",	 0,56,120,18, &cumap->clipr.ymin, -100.0, cumap->clipr.ymax, 10, 0, "");
	uiDefButF(block, NUM, 0, "Max X ",	 0,38,120,18, &cumap->clipr.xmax, cumap->clipr.xmin, 100.0, 10, 0, "");
	uiDefButF(block, NUM, 0, "Max Y ",	 0,20,120,18, &cumap->clipr.ymax, cumap->clipr.ymin, 100.0, 10, 0, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	
	uiEndBlock(C, block);
	return block;
}


static void curvemap_tools_dofunc(bContext *C, void *cumap_v, int event)
{
	CurveMapping *cumap = cumap_v;
	CurveMap *cuma= cumap->cm+cumap->cur;
	
	switch(event) {
		case 0:
			curvemap_reset(cuma, &cumap->clipr);
			curvemapping_changed(cumap, 0);
			break;
		case 1:
			cumap->curr= cumap->clipr;
			break;
		case 2:	/* set vector */
			curvemap_sethandle(cuma, 1);
			curvemapping_changed(cumap, 0);
			break;
		case 3: /* set auto */
			curvemap_sethandle(cuma, 0);
			curvemapping_changed(cumap, 0);
			break;
		case 4: /* extend horiz */
			cuma->flag &= ~CUMA_EXTEND_EXTRAPOLATE;
			curvemapping_changed(cumap, 0);
			break;
		case 5: /* extend extrapolate */
			cuma->flag |= CUMA_EXTEND_EXTRAPOLATE;
			curvemapping_changed(cumap, 0);
			break;
	}
	ED_region_tag_redraw(CTX_wm_region(C));
}

static uiBlock *curvemap_tools_func(struct bContext *C, struct ARegion *ar, void *cumap_v)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, ar, "curvemap_tools_func", UI_EMBOSS);
	uiBlockSetButmFunc(block, curvemap_tools_dofunc, cumap_v);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Reset View",				0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Vector Handle",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Auto Handle",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Extend Horizontal",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Extend Extrapolated",	0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Reset Curve",			0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 50);
	
	uiEndBlock(C, block);
	return block;
}

/* still unsure how this call evolves... we use labeltype for defining what curve-channels to show */
void curvemap_buttons(uiBlock *block, CurveMapping *cumap, char labeltype, short event, short redraw, rctf *rect)
{
	uiBut *bt;
	float dx, fy= rect->ymax-18.0f;
	int icon;
	short xco, yco;
	
	yco= (short)(rect->ymax-18.0f);
	
	/* curve choice options + tools/settings, 8 icons + spacer */
	dx= (rect->xmax-rect->xmin)/(9.0f);
	
	uiBlockBeginAlign(block);
	if(labeltype=='v') {	/* vector */
		xco= (short)rect->xmin;
		if(cumap->cm[0].curve)
			uiDefButI(block, ROW, redraw, "X", xco, yco+2, dx, 16, &cumap->cur, 0.0, 0.0, 0.0, 0.0, "");
		xco= (short)(rect->xmin+1.0f*dx);
		if(cumap->cm[1].curve)
			uiDefButI(block, ROW, redraw, "Y", xco, yco+2, dx, 16, &cumap->cur, 0.0, 1.0, 0.0, 0.0, "");
		xco= (short)(rect->xmin+2.0f*dx);
		if(cumap->cm[2].curve)
			uiDefButI(block, ROW, redraw, "Z", xco, yco+2, dx, 16, &cumap->cur, 0.0, 2.0, 0.0, 0.0, "");
	}
	else if(labeltype=='c') { /* color */
		xco= (short)rect->xmin;
		if(cumap->cm[3].curve)
			uiDefButI(block, ROW, redraw, "C", xco, yco+2, dx, 16, &cumap->cur, 0.0, 3.0, 0.0, 0.0, "");
		xco= (short)(rect->xmin+1.0f*dx);
		if(cumap->cm[0].curve)
			uiDefButI(block, ROW, redraw, "R", xco, yco+2, dx, 16, &cumap->cur, 0.0, 0.0, 0.0, 0.0, "");
		xco= (short)(rect->xmin+2.0f*dx);
		if(cumap->cm[1].curve)
			uiDefButI(block, ROW, redraw, "G", xco, yco+2, dx, 16, &cumap->cur, 0.0, 1.0, 0.0, 0.0, "");
		xco= (short)(rect->xmin+3.0f*dx);
		if(cumap->cm[2].curve)
			uiDefButI(block, ROW, redraw, "B", xco, yco+2, dx, 16, &cumap->cur, 0.0, 2.0, 0.0, 0.0, "");
	}
	/* else no channels ! */
	uiBlockEndAlign(block);

	xco= (short)(rect->xmin+4.5f*dx);
	uiBlockSetEmboss(block, UI_EMBOSSN);
	bt= uiDefIconBut(block, BUT, redraw, ICON_ZOOMIN, xco, yco, dx, 14, NULL, 0.0, 0.0, 0.0, 0.0, "Zoom in");
	uiButSetFunc(bt, curvemap_buttons_zoom_in, cumap, NULL);
	
	xco= (short)(rect->xmin+5.25f*dx);
	bt= uiDefIconBut(block, BUT, redraw, ICON_ZOOMOUT, xco, yco, dx, 14, NULL, 0.0, 0.0, 0.0, 0.0, "Zoom out");
	uiButSetFunc(bt, curvemap_buttons_zoom_out, cumap, NULL);
	
	xco= (short)(rect->xmin+6.0f*dx);
	bt= uiDefIconBlockBut(block, curvemap_tools_func, cumap, event, ICON_MODIFIER, xco, yco, dx, 18, "Tools");
	
	xco= (short)(rect->xmin+7.0f*dx);
	if(cumap->flag & CUMA_DO_CLIP) icon= ICON_CLIPUV_HLT; else icon= ICON_CLIPUV_DEHLT;
	bt= uiDefIconBlockBut(block, curvemap_clipping_func, cumap, event, icon, xco, yco, dx, 18, "Clipping Options");
	
	xco= (short)(rect->xmin+8.0f*dx);
	bt= uiDefIconBut(block, BUT, event, ICON_X, xco, yco, dx, 18, NULL, 0.0, 0.0, 0.0, 0.0, "Delete points");
	uiButSetFunc(bt, curvemap_buttons_delete, cumap, NULL);
	
	uiBlockSetEmboss(block, UI_EMBOSS);
	
	uiDefBut(block, BUT_CURVE, event, "", 
			  rect->xmin, rect->ymin, rect->xmax-rect->xmin, fy-rect->ymin, 
			  cumap, 0.0f, 1.0f, 0, 0, "");
}

#define B_BANDCOL 1

static int vergcband(const void *a1, const void *a2)
{
	const CBData *x1=a1, *x2=a2;

	if( x1->pos > x2->pos ) return 1;
	else if( x1->pos < x2->pos) return -1;
	return 0;
}

static void colorband_pos_cb(bContext *C, void *coba_v, void *unused_v)
{
	ColorBand *coba= coba_v;
	int a;
	
	if(coba->tot<2) return;
	
	for(a=0; a<coba->tot; a++) coba->data[a].cur= a;
	qsort(coba->data, coba->tot, sizeof(CBData), vergcband);
	for(a=0; a<coba->tot; a++) {
		if(coba->data[a].cur==coba->cur) {
			// XXX if(coba->cur!=a) addqueue(curarea->win, REDRAW, 0);	/* button cur */
			coba->cur= a;
			break;
		}
	}
}

static void colorband_add_cb(bContext *C, void *coba_v, void *unused_v)
{
	ColorBand *coba= coba_v;
	
	if(coba->tot < MAXCOLORBAND-1) coba->tot++;
	coba->cur= coba->tot-1;
	
	colorband_pos_cb(C, coba, NULL);
	ED_undo_push(C, "Add colorband");
}

static void colorband_del_cb(bContext *C, void *coba_v, void *unused_v)
{
	ColorBand *coba= coba_v;
	int a;
	
	if(coba->tot<2) return;
	
	for(a=coba->cur; a<coba->tot; a++) {
		coba->data[a]= coba->data[a+1];
	}
	if(coba->cur) coba->cur--;
	coba->tot--;
	
	ED_undo_push(C, "Delete colorband");
	// XXX BIF_preview_changed(ID_TE);
}


/* offset aligns from bottom, standard width 300, height 115 */
static void colorband_buttons_large(uiBlock *block, ColorBand *coba, int xoffs, int yoffs, int redraw)
{
	CBData *cbd;
	uiBut *bt;
	
	if(coba==NULL) return;
	
	bt= uiDefBut(block, BUT, redraw,	"Add",		80+xoffs,95+yoffs,37,20, 0, 0, 0, 0, 0, "Adds a new color position to the colorband");
	uiButSetFunc(bt, colorband_add_cb, coba, NULL);
	uiDefButS(block, NUM, redraw,		"Cur:",		117+xoffs,95+yoffs,81,20, &coba->cur, 0.0, (float)(coba->tot-1), 0, 0, "Displays the active color from the colorband");
	bt= uiDefBut(block, BUT, redraw,		"Del",		199+xoffs,95+yoffs,37,20, 0, 0, 0, 0, 0, "Deletes the active position");
	uiButSetFunc(bt, colorband_del_cb, coba, NULL);
	
	uiDefButS(block, MENU, redraw,		"Interpolation %t|Ease %x1|Cardinal %x3|Linear %x0|B-Spline %x2|Constant %x4",
		236+xoffs, 95+yoffs, 64, 20,		&coba->ipotype, 0.0, 0.0, 0, 0, "Sets interpolation type");

	uiDefBut(block, BUT_COLORBAND, redraw, "", 	xoffs,65+yoffs,300,30, coba, 0, 0, 0, 0, "");
	
	cbd= coba->data + coba->cur;
	
	uiBlockBeginAlign(block);
	bt= uiDefButF(block, NUM, redraw, "Pos",		xoffs,40+yoffs,110,20, &cbd->pos, 0.0, 1.0, 10, 0, "Sets the position of the active color");
	uiButSetFunc(bt, colorband_pos_cb, coba, NULL);
	uiDefButF(block, COL, redraw,		"",		xoffs,20+yoffs,110,20, &(cbd->r), 0, 0, 0, B_BANDCOL, "");
	uiDefButF(block, NUMSLI, redraw,	"A ",	xoffs,yoffs,110,20, &cbd->a, 0.0, 1.0, 10, 0, "Sets the alpha value for this position");

	uiBlockBeginAlign(block);
	uiDefButF(block, NUMSLI, redraw,	"R ",	115+xoffs,40+yoffs,185,20, &cbd->r, 0.0, 1.0, B_BANDCOL, 0, "Sets the red value for the active color");
	uiDefButF(block, NUMSLI, redraw,	"G ",	115+xoffs,20+yoffs,185,20, &cbd->g, 0.0, 1.0, B_BANDCOL, 0, "Sets the green value for the active color");
	uiDefButF(block, NUMSLI, redraw,	"B ",	115+xoffs,yoffs,185,20, &cbd->b, 0.0, 1.0, B_BANDCOL, 0, "Sets the blue value for the active color");
	uiBlockEndAlign(block);
}

static void colorband_buttons_small(uiBlock *block, ColorBand *coba, rctf *butr, int event)
{
	CBData *cbd;
	uiBut *bt;
	float unit= (butr->xmax-butr->xmin)/14.0f;
	float xs= butr->xmin;
	
	cbd= coba->data + coba->cur;
	
	uiBlockBeginAlign(block);
	uiDefButF(block, COL, event,		"",			xs,butr->ymin+20.0f,2.0f*unit,20,				&(cbd->r), 0, 0, 0, B_BANDCOL, "");
	uiDefButF(block, NUM, event,		"A:",		xs+2.0f*unit,butr->ymin+20.0f,4.0f*unit,20,	&(cbd->a), 0.0f, 1.0f, 10, 2, "");
	bt= uiDefBut(block, BUT, event,	"Add",		xs+6.0f*unit,butr->ymin+20.0f,2.0f*unit,20,	NULL, 0, 0, 0, 0, "Adds a new color position to the colorband");
	uiButSetFunc(bt, colorband_add_cb, coba, NULL);
	bt= uiDefBut(block, BUT, event,	"Del",		xs+8.0f*unit,butr->ymin+20.0f,2.0f*unit,20,	NULL, 0, 0, 0, 0, "Deletes the active position");
	uiButSetFunc(bt, colorband_del_cb, coba, NULL);

	uiDefButS(block, MENU, event,		"Interpolation %t|Ease %x1|Cardinal %x3|Linear %x0|B-Spline %x2|Constant %x4",
		xs+10.0f*unit, butr->ymin+20.0f, unit*4, 20,		&coba->ipotype, 0.0, 0.0, 0, 0, "Sets interpolation type");

	uiDefBut(block, BUT_COLORBAND, event, "",		xs,butr->ymin,butr->xmax-butr->xmin,20.0f, coba, 0, 0, 0, 0, "");
	uiBlockEndAlign(block);
	
}

void colorband_buttons(uiBlock *block, ColorBand *coba, rctf *butr, int small)
{
	if(small)
		colorband_buttons_small(block, coba, butr, 0);
	else
		colorband_buttons_large(block, coba, 0, 0, 0);
}

