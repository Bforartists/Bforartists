/**
 * $Id:
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
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>

#include "DNA_screen_types.h"
#include "DNA_windowmanager_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"

#include "BKE_blender.h"
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_main.h"

#include "RNA_access.h"
#include "RNA_types.h"

#include "WM_api.h"
#include "WM_types.h"
#include "wm_window.h"
#include "wm_event_system.h"
#include "wm_event_types.h"

/* ***************** generic call, exported **************** */

static void keymap_event_set(wmKeymapItem *kmi, short type, short val, int modifier, short keymodifier)
{
	kmi->type= type;
	kmi->val= val;
	kmi->keymodifier= keymodifier;
	
	if(modifier & KM_SHIFT)
		kmi->shift= 1;
	else if(modifier & KM_SHIFT2)
		kmi->shift= 2;
	if(modifier & KM_CTRL)
		kmi->ctrl= 1;
	else if(modifier & KM_CTRL2)
		kmi->ctrl= 2;
	if(modifier & KM_ALT)
		kmi->alt= 1;
	else if(modifier & KM_ALT2)
		kmi->alt= 2;
	if(modifier & KM_OSKEY)
		kmi->oskey= 1;
	else if(modifier & KM_OSKEY2)
		kmi->oskey= 2;	
}

static void keymap_properties_set(wmKeymapItem *kmi)
{
	wmOperatorType *ot;
	
	if(!kmi->ptr) {
		ot= WM_operatortype_find(kmi->idname);

		if(ot) {
			kmi->ptr= MEM_callocN(sizeof(PointerRNA), "wmKeymapItemPtr");
			RNA_pointer_create(NULL, NULL, ot->srna, &kmi->properties, kmi->ptr);
		}
	}
}

/* if item was added, then bail out */
wmKeymapItem *WM_keymap_verify_item(ListBase *lb, char *idname, short type, short val, int modifier, short keymodifier)
{
	wmKeymapItem *kmi;
	
	for(kmi= lb->first; kmi; kmi= kmi->next)
		if(strncmp(kmi->idname, idname, OP_MAX_TYPENAME)==0)
			break;
	if(kmi==NULL) {
		kmi= MEM_callocN(sizeof(wmKeymapItem), "keymap entry");
		
		BLI_addtail(lb, kmi);
		BLI_strncpy(kmi->idname, idname, OP_MAX_TYPENAME);
		
		keymap_event_set(kmi, type, val, modifier, keymodifier);
		keymap_properties_set(kmi);
	}
	return kmi;
}

/* if item was added, then replace */
wmKeymapItem *WM_keymap_set_item(ListBase *lb, char *idname, short type, short val, int modifier, short keymodifier)
{
	wmKeymapItem *kmi;
	
	for(kmi= lb->first; kmi; kmi= kmi->next)
		if(strncmp(kmi->idname, idname, OP_MAX_TYPENAME)==0)
			break;
	if(kmi==NULL) {
		kmi= MEM_callocN(sizeof(wmKeymapItem), "keymap entry");
	
		BLI_addtail(lb, kmi);
		BLI_strncpy(kmi->idname, idname, OP_MAX_TYPENAME);
	}
	keymap_event_set(kmi, type, val, modifier, keymodifier);
	keymap_properties_set(kmi);
	return kmi;
}

/* always add item */
wmKeymapItem *WM_keymap_add_item(ListBase *lb, char *idname, short type, short val, int modifier, short keymodifier)
{
	wmKeymapItem *kmi= MEM_callocN(sizeof(wmKeymapItem), "keymap entry");
	
	BLI_addtail(lb, kmi);
	BLI_strncpy(kmi->idname, idname, OP_MAX_TYPENAME);

	keymap_event_set(kmi, type, val, modifier, keymodifier);
	keymap_properties_set(kmi);
	return kmi;
}

/* ****************** storage in WM ************ */

/* name id's are for storing general or multiple keymaps, 
   space/region ids are same as DNA_space_types.h */
/* gets free'd in wm.c */

ListBase *WM_keymap_listbase(wmWindowManager *wm, const char *nameid, int spaceid, int regionid)
{
	wmKeyMap *km;
	
	for(km= wm->keymaps.first; km; km= km->next)
		if(km->spaceid==spaceid && km->regionid==regionid)
			if(0==strncmp(nameid, km->nameid, KMAP_MAX_NAME))
				break;

	if(km==NULL) {
		km= MEM_callocN(sizeof(struct wmKeyMap), "keymap list");
		BLI_strncpy(km->nameid, nameid, KMAP_MAX_NAME);
		km->spaceid= spaceid;
		km->regionid= regionid;
		printf("added keymap %s %d %d\n", nameid, spaceid, regionid);
		BLI_addtail(&wm->keymaps, km);
	}
	
	return &km->keymap;
}

/* ***************** get string from key events **************** */

char *WM_key_event_string(short type)
{
	/* not returned: CAPSLOCKKEY, UNKNOWNKEY, COMMANDKEY, GRLESSKEY */

	switch(type) {
	case AKEY:
		return "A";
		break;
	case BKEY:
		return "B";
		break;
	case CKEY:
		return "C";
		break;
	case DKEY:
		return "D";
		break;
	case EKEY:
		return "E";
		break;
	case FKEY:
		return "F";
		break;
	case GKEY:
		return "G";
		break;
	case HKEY:
		return "H";
		break;
	case IKEY:
		return "I";
		break;
	case JKEY:
		return "J";
		break;
	case KKEY:
		return "K";
		break;
	case LKEY:
		return "L";
		break;
	case MKEY:
		return "M";
		break;
	case NKEY:
		return "N";
		break;
	case OKEY:
		return "O";
		break;
	case PKEY:
		return "P";
		break;
	case QKEY:
		return "Q";
		break;
	case RKEY:
		return "R";
		break;
	case SKEY:
		return "S";
		break;
	case TKEY:
		return "T";
		break;
	case UKEY:
		return "U";
		break;
	case VKEY:
		return "V";
		break;
	case WKEY:
		return "W";
		break;
	case XKEY:
		return "X";
		break;
	case YKEY:
		return "Y";
		break;
	case ZKEY:
		return "Z";
		break;

	case ZEROKEY:
		return "Zero";
		break;
	case ONEKEY:
		return "One";
		break;
	case TWOKEY:
		return "Two";
		break;
	case THREEKEY:
		return "Three";
		break;
	case FOURKEY:
		return "Four";
		break;
	case FIVEKEY:
		return "Five";
		break;
	case SIXKEY:
		return "Six";
		break;
	case SEVENKEY:
		return "Seven";
		break;
	case EIGHTKEY:
		return "Eight";
		break;
	case NINEKEY:
		return "Nine";
		break;

	case LEFTCTRLKEY:
		return "Leftctrl";
		break;
	case LEFTALTKEY:
		return "Leftalt";
		break;
	case RIGHTALTKEY:
		return "Rightalt";
		break;
	case RIGHTCTRLKEY:
		return "Rightctrl";
		break;
	case RIGHTSHIFTKEY:
		return "Rightshift";
		break;
	case LEFTSHIFTKEY:
		return "Leftshift";
		break;

	case ESCKEY:
		return "Esc";
		break;
	case TABKEY:
		return "Tab";
		break;
	case RETKEY:
		return "Ret";
		break;
	case SPACEKEY:
		return "Space";
		break;
	case LINEFEEDKEY:
		return "Linefeed";
		break;
	case BACKSPACEKEY:
		return "Backspace";
		break;
	case DELKEY:
		return "Del";
		break;
	case SEMICOLONKEY:
		return "Semicolon";
		break;
	case PERIODKEY:
		return "Period";
		break;
	case COMMAKEY:
		return "Comma";
		break;
	case QUOTEKEY:
		return "Quote";
		break;
	case ACCENTGRAVEKEY:
		return "Accentgrave";
		break;
	case MINUSKEY:
		return "Minus";
		break;
	case SLASHKEY:
		return "Slash";
		break;
	case BACKSLASHKEY:
		return "Backslash";
		break;
	case EQUALKEY:
		return "Equal";
		break;
	case LEFTBRACKETKEY:
		return "Leftbracket";
		break;
	case RIGHTBRACKETKEY:
		return "Rightbracket";
		break;

	case LEFTARROWKEY:
		return "Leftarrow";
		break;
	case DOWNARROWKEY:
		return "Downarrow";
		break;
	case RIGHTARROWKEY:
		return "Rightarrow";
		break;
	case UPARROWKEY:
		return "Uparrow";
		break;

	case PAD2:
		return "Pad2";
		break;
	case PAD4:
		return "Pad4";
		break;
	case PAD6:
		return "Pad6";
		break;
	case PAD8:
		return "Pad8";
		break;
	case PAD1:
		return "Pad1";
		break;
	case PAD3:
		return "Pad3";
		break;
	case PAD5:
		return "Pad5";
		break;
	case PAD7:
		return "Pad7";
		break;
	case PAD9:
		return "Pad9";
		break;

	case PADPERIOD:
		return "Padperiod";
		break;
	case PADSLASHKEY:
		return "Padslash";
		break;
	case PADASTERKEY:
		return "Padaster";
		break;

	case PAD0:
		return "Pad0";
		break;
	case PADMINUS:
		return "Padminus";
		break;
	case PADENTER:
		return "Padenter";
		break;
	case PADPLUSKEY:
		return "Padplus";
		break;

	case F1KEY:
		return "F1";
		break;
	case F2KEY:
		return "F2";
		break;
	case F3KEY:
		return "F3";
		break;
	case F4KEY:
		return "F4";
		break;
	case F5KEY:
		return "F5";
		break;
	case F6KEY:
		return "F6";
		break;
	case F7KEY:
		return "F7";
		break;
	case F8KEY:
		return "F8";
		break;
	case F9KEY:
		return "F9";
		break;
	case F10KEY:
		return "F10";
		break;
	case F11KEY:
		return "F11";
		break;
	case F12KEY:
		return "F12";
		break;

	case PAUSEKEY:
		return "Pause";
		break;
	case INSERTKEY:
		return "Insert";
		break;
	case HOMEKEY:
		return "Home";
		break;
	case PAGEUPKEY:
		return "Pageup";
		break;
	case PAGEDOWNKEY:
		return "Pagedown";
		break;
	case ENDKEY:
		return "End";
		break;
	}
	
	return "";
}

static char *wm_keymap_item_to_string(wmKeymapItem *kmi, char *str, int len)
{
	char buf[100];

	buf[0]= 0;

	if(kmi->shift)
		strcat(buf, "Shift ");

	if(kmi->ctrl)
		strcat(buf, "Ctrl ");

	if(kmi->alt)
		strcat(buf, "Alt ");

	if(kmi->oskey)
		strcat(buf, "OS ");

	strcat(buf, WM_key_event_string(kmi->type));
	BLI_strncpy(str, buf, len);

	return str;
}

char *WM_key_event_operator_string(bContext *C, char *opname, int opcontext, char *str, int len)
{
	wmEventHandler *handler;
	wmKeymapItem *kmi;
	ListBase *handlers= NULL;

	/* find right handler list based on specified context */
	if(opcontext == WM_OP_REGION_WIN) {
		if(C->area) {
			ARegion *ar= C->area->regionbase.first;
			for(; ar; ar= ar->next)
				if(ar->regiontype==RGN_TYPE_WINDOW)
					break;

			if(ar)
				handlers= &ar->handlers;
		}
	}
	else if(opcontext == WM_OP_AREA) {
		if(C->area)
			handlers= &C->area->handlers;
	}
	else if(opcontext == WM_OP_SCREEN) {
		if(C->window)
			handlers= &C->window->handlers;
	}
	else {
		if(C->region)
			handlers= &C->region->handlers;
	}

	if(!handlers)
		return NULL;
	
	/* find keymap item in handlers */
	for(handler=handlers->first; handler; handler=handler->next)
		if(handler->keymap)
			for(kmi=handler->keymap->first; kmi; kmi=kmi->next)
				if(strcmp(kmi->idname, opname) == 0 && WM_key_event_string(kmi->type)[0])
					return wm_keymap_item_to_string(kmi, str, len);

	return NULL;
}

