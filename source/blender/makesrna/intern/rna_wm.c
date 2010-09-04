/**
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
 * Contributor(s): Blender Foundation (2008).
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "rna_internal.h"

#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_userdef_types.h"
#include "DNA_windowmanager_types.h"

#include "WM_types.h"

EnumPropertyItem event_keymouse_value_items[] = {
	{KM_ANY, "ANY", 0, "Any", ""},
	{KM_PRESS, "PRESS", 0, "Press", ""},
	{KM_RELEASE, "RELEASE", 0, "Release", ""},
	{KM_CLICK, "CLICK", 0, "Click", ""},
	{KM_DBL_CLICK, "DOUBLE_CLICK", 0, "Double Click", ""},
	{0, NULL, 0, NULL, NULL}};

EnumPropertyItem event_tweak_value_items[]= {
	{KM_ANY, "ANY", 0, "Any", ""},
	{EVT_GESTURE_N, "NORTH", 0, "North", ""},
	{EVT_GESTURE_NE, "NORTH_EAST", 0, "North-East", ""},
	{EVT_GESTURE_E, "EAST", 0, "East", ""},
	{EVT_GESTURE_SE, "SOUTH_EAST", 0, "South-East", ""},
	{EVT_GESTURE_S, "SOUTH", 0, "South", ""},
	{EVT_GESTURE_SW, "SOUTH_WEST", 0, "South-West", ""},
	{EVT_GESTURE_W, "WEST", 0, "West", ""},
	{EVT_GESTURE_NW, "NORTH_WEST", 0, "North-West", ""},
	{0, NULL, 0, NULL, NULL}};

EnumPropertyItem event_value_items[] = {
	{KM_ANY, "ANY", 0, "Any", ""},
	{KM_NOTHING, "NOTHING", 0, "Nothing", ""},
	{KM_PRESS, "PRESS", 0, "Press", ""},
	{KM_RELEASE, "RELEASE", 0, "Release", ""},
	{KM_CLICK, "CLICK", 0, "Click", ""},
	{KM_DBL_CLICK, "DOUBLE_CLICK", 0, "Double Click", ""},
	{0, NULL, 0, NULL, NULL}};

EnumPropertyItem event_tweak_type_items[]= {
	{EVT_TWEAK_L, "EVT_TWEAK_L", 0, "Left", ""},
	{EVT_TWEAK_M, "EVT_TWEAK_M", 0, "Middle", ""},
	{EVT_TWEAK_R, "EVT_TWEAK_R", 0, "Right", ""},
	{EVT_TWEAK_A, "EVT_TWEAK_A", 0, "Action", ""},
	{EVT_TWEAK_S, "EVT_TWEAK_S", 0, "Select", ""},
	{0, NULL, 0, NULL, NULL}};

EnumPropertyItem event_mouse_type_items[]= {
	{LEFTMOUSE, "LEFTMOUSE", 0, "Left", ""},
	{MIDDLEMOUSE, "MIDDLEMOUSE", 0, "Middle", ""},
	{RIGHTMOUSE, "RIGHTMOUSE", 0, "Right", ""},
	{BUTTON4MOUSE, "BUTTON4MOUSE", 0, "Button4", ""},
	{BUTTON5MOUSE, "BUTTON5MOUSE", 0, "Button5", ""},
	{ACTIONMOUSE, "ACTIONMOUSE", 0, "Action", ""},
	{SELECTMOUSE, "SELECTMOUSE", 0, "Select", ""},
	{0, "", 0, NULL, NULL},
	{MOUSEMOVE, "MOUSEMOVE", 0, "Move", ""},
	{MOUSEPAN, "TRACKPADPAN", 0, "Mouse/Trackpad Pan", ""},
	{MOUSEZOOM, "TRACKPADZOOM", 0, "Mouse/Trackpad Zoom", ""},
	{MOUSEROTATE, "MOUSEROTATE", 0, "Mouse/Trackpad Rotate", ""},
	{0, "", 0, NULL, NULL},
	{WHEELUPMOUSE, "WHEELUPMOUSE", 0, "Wheel Up", ""},
	{WHEELDOWNMOUSE, "WHEELDOWNMOUSE", 0, "Wheel Down", ""},
	{WHEELINMOUSE, "WHEELINMOUSE", 0, "Wheel In", ""},
	{WHEELOUTMOUSE, "WHEELOUTMOUSE", 0, "Wheel Out", ""},
	{0, NULL, 0, NULL, NULL}};

EnumPropertyItem event_timer_type_items[]= {
	{TIMER, "TIMER", 0, "Timer", ""},
	{TIMER0, "TIMER0", 0, "Timer 0", ""},
	{TIMER1, "TIMER1", 0, "Timer 1", ""},
	{TIMER2, "TIMER2", 0, "Timer 2", ""},
	{0, NULL, 0, NULL, NULL}};

/* not returned: CAPSLOCKKEY, UNKNOWNKEY, GRLESSKEY */
EnumPropertyItem event_type_items[] = {

	{0, "NONE", 0, "", ""},
	{LEFTMOUSE, "LEFTMOUSE", 0, "Left Mouse", ""},
	{MIDDLEMOUSE, "MIDDLEMOUSE", 0, "Middle Mouse", ""},
	{RIGHTMOUSE, "RIGHTMOUSE", 0, "Right Mouse", ""},
	{BUTTON4MOUSE, "BUTTON4MOUSE", 0, "Button4 Mouse", ""},
	{BUTTON5MOUSE, "BUTTON5MOUSE", 0, "Button5 Mouse", ""},
	{ACTIONMOUSE, "ACTIONMOUSE", 0, "Action Mouse", ""},
	{SELECTMOUSE, "SELECTMOUSE", 0, "Select Mouse", ""},
	{0, "", 0, NULL, NULL},
	{MOUSEMOVE, "MOUSEMOVE", 0, "Mouse Move", ""},
	{INBETWEEN_MOUSEMOVE, "INBETWEEN_MOUSEMOVE", 0, "Inbetween Move", ""},
	{MOUSEPAN, "TRACKPADPAN", 0, "Mouse/Trackpad Pan", ""},
	{MOUSEZOOM, "TRACKPADZOOM", 0, "Mouse/Trackpad Zoom", ""},
	{MOUSEROTATE, "MOUSEROTATE", 0, "Mouse/Trackpad Rotate", ""},
	{0, "", 0, NULL, NULL},
	{WHEELUPMOUSE, "WHEELUPMOUSE", 0, "Wheel Up", ""},
	{WHEELDOWNMOUSE, "WHEELDOWNMOUSE", 0, "Wheel Down", ""},
	{WHEELINMOUSE, "WHEELINMOUSE", 0, "Wheel In", ""},
	{WHEELOUTMOUSE, "WHEELOUTMOUSE", 0, "Wheel Out", ""},
	{0, "", 0, NULL, NULL},
	{EVT_TWEAK_L, "EVT_TWEAK_L", 0, "Tweak Left", ""},
	{EVT_TWEAK_M, "EVT_TWEAK_M", 0, "Tweak Middle", ""},
	{EVT_TWEAK_R, "EVT_TWEAK_R", 0, "Tweak Right", ""},
	{EVT_TWEAK_A, "EVT_TWEAK_A", 0, "Tweak Action", ""},
	{EVT_TWEAK_S, "EVT_TWEAK_S", 0, "Tweak Select", ""},
	{0, "", 0, NULL, NULL},
	{AKEY, "A", 0, "A", ""},
	{BKEY, "B", 0, "B", ""},
	{CKEY, "C", 0, "C", ""},
	{DKEY, "D", 0, "D", ""},
	{EKEY, "E", 0, "E", ""},
	{FKEY, "F", 0, "F", ""},
	{GKEY, "G", 0, "G", ""},
	{HKEY, "H", 0, "H", ""},
	{IKEY, "I", 0, "I", ""},
	{JKEY, "J", 0, "J", ""},
	{KKEY, "K", 0, "K", ""},
	{LKEY, "L", 0, "L", ""},
	{MKEY, "M", 0, "M", ""},
	{NKEY, "N", 0, "N", ""},
	{OKEY, "O", 0, "O", ""},
	{PKEY, "P", 0, "P", ""},
	{QKEY, "Q", 0, "Q", ""},
	{RKEY, "R", 0, "R", ""},
	{SKEY, "S", 0, "S", ""},
	{TKEY, "T", 0, "T", ""},
	{UKEY, "U", 0, "U", ""},
	{VKEY, "V", 0, "V", ""},
	{WKEY, "W", 0, "W", ""},
	{XKEY, "X", 0, "X", ""},
	{YKEY, "Y", 0, "Y", ""},
	{ZKEY, "Z", 0, "Z", ""},
	{0, "", 0, NULL, NULL},
	{ZEROKEY, "ZERO",	0, "0", ""},
	{ONEKEY, "ONE",		0, "1", ""},
	{TWOKEY, "TWO",		0, "2", ""},
	{THREEKEY, "THREE",	0, "3", ""},
	{FOURKEY, "FOUR",	0, "4", ""},
	{FIVEKEY, "FIVE",	0, "5", ""},
	{SIXKEY, "SIX",		0, "6", ""},
	{SEVENKEY, "SEVEN",	0, "7", ""},
	{EIGHTKEY, "EIGHT",	0, "8", ""},
	{NINEKEY, "NINE",	0, "9", ""},
	{0, "", 0, NULL, NULL},
	{LEFTCTRLKEY,	"LEFT_CTRL",	0, "Left Ctrl", ""},
	{LEFTALTKEY,	"LEFT_ALT",		0, "Left Alt", ""},
	{LEFTSHIFTKEY,	"LEFT_SHIFT",	0, "Left Shift", ""},
	{RIGHTALTKEY,	"RIGHT_ALT",	0, "Right Alt", ""},
	{RIGHTCTRLKEY,	"RIGHT_CTRL",	0, "Right Ctrl", ""},
	{RIGHTSHIFTKEY,	"RIGHT_SHIFT",	0, "Right Shift", ""},
	{0, "", 0, NULL, NULL},
	{COMMANDKEY,	"COMMAND",	0, "Command", ""},
	{0, "", 0, NULL, NULL},
	{ESCKEY, "ESC", 0, "Esc", ""},
	{TABKEY, "TAB", 0, "Tab", ""},
	{RETKEY, "RET", 0, "Return", ""},
	{SPACEKEY, "SPACE", 0, "Spacebar", ""},
	{LINEFEEDKEY, "LINE_FEED", 0, "Line Feed", ""},
	{BACKSPACEKEY, "BACK_SPACE", 0, "Back Space", ""},
	{DELKEY, "DEL", 0, "Delete", ""},
	{SEMICOLONKEY, "SEMI_COLON", 0, ";", ""},
	{PERIODKEY, "PERIOD", 0, ".", ""},
	{COMMAKEY, "COMMA", 0, ",", ""},
	{QUOTEKEY, "QUOTE", 0, "\"", ""},
	{ACCENTGRAVEKEY, "ACCENT_GRAVE", 0, "`", ""},
	{MINUSKEY, "MINUS", 0, "-", ""},
	{SLASHKEY, "SLASH", 0, "/", ""},
	{BACKSLASHKEY, "BACK_SLASH", 0, "\\", ""},
	{EQUALKEY, "EQUAL", 0, "=", ""},
	{LEFTBRACKETKEY, "LEFT_BRACKET", 0, "[", ""},
	{RIGHTBRACKETKEY, "RIGHT_BRACKET", 0, "]", ""},
	{LEFTARROWKEY, "LEFT_ARROW", 0, "Left Arrow", ""},
	{DOWNARROWKEY, "DOWN_ARROW", 0, "Down Arrow", ""},
	{RIGHTARROWKEY, "RIGHT_ARROW", 0, "Right Arrow", ""},
	{UPARROWKEY, "UP_ARROW", 0, "Up Arrow", ""},
	{PAD2, "NUMPAD_2", 0, "Numpad 2", ""},
	{PAD4, "NUMPAD_4", 0, "Numpad 4", ""},
	{PAD6, "NUMPAD_6", 0, "Numpad 6", ""},
	{PAD8, "NUMPAD_8", 0, "Numpad 8", ""},
	{PAD1, "NUMPAD_1", 0, "Numpad 1", ""},
	{PAD3, "NUMPAD_3", 0, "Numpad 3", ""},
	{PAD5, "NUMPAD_5", 0, "Numpad 5", ""},
	{PAD7, "NUMPAD_7", 0, "Numpad 7", ""},
	{PAD9, "NUMPAD_9", 0, "Numpad 9", ""},
	{PADPERIOD, "NUMPAD_PERIOD", 0, "Numpad .", ""},
	{PADSLASHKEY, "NUMPAD_SLASH", 0, "Numpad /", ""},
	{PADASTERKEY, "NUMPAD_ASTERIX", 0, "Numpad *", ""},
	{PAD0, "NUMPAD_0", 0, "Numpad 0", ""},
	{PADMINUS, "NUMPAD_MINUS", 0, "Numpad -", ""},
	{PADENTER, "NUMPAD_ENTER", 0, "Numpad Enter", ""},
	{PADPLUSKEY, "NUMPAD_PLUS", 0, "Numpad +", ""},
	{F1KEY, "F1", 0, "F1", ""},
	{F2KEY, "F2", 0, "F2", ""},
	{F3KEY, "F3", 0, "F3", ""},
	{F4KEY, "F4", 0, "F4", ""},
	{F5KEY, "F5", 0, "F5", ""},
	{F6KEY, "F6", 0, "F6", ""},
	{F7KEY, "F7", 0, "F7", ""},
	{F8KEY, "F8", 0, "F8", ""},
	{F9KEY, "F9", 0, "F9", ""},
	{F10KEY, "F10", 0, "F10", ""},
	{F11KEY, "F11", 0, "F11", ""},
	{F12KEY, "F12", 0, "F12", ""},
	{F13KEY, "F13", 0, "F13", ""},
	{F14KEY, "F14", 0, "F14", ""},
	{F15KEY, "F15", 0, "F15", ""},
	{F16KEY, "F16", 0, "F16", ""},
	{F17KEY, "F17", 0, "F17", ""},
	{F18KEY, "F18", 0, "F18", ""},
	{F19KEY, "F19", 0, "F19", ""},
	{PAUSEKEY, "PAUSE", 0, "Pause", ""},
	{INSERTKEY, "INSERT", 0, "Insert", ""},
	{HOMEKEY, "HOME", 0, "Home", ""},
	{PAGEUPKEY, "PAGE_UP", 0, "Page Up", ""},
	{PAGEDOWNKEY, "PAGE_DOWN", 0, "Page Down", ""},
	{ENDKEY, "END", 0, "End", ""},
	{0, "", 0, NULL, NULL},
	{WINDEACTIVATE, "WINDOW_DEACTIVATE", 0, "Window Deactivate", ""},
	{TIMER, "TIMER", 0, "Timer", ""},
	{TIMER0, "TIMER0", 0, "Timer 0", ""},
	{TIMER1, "TIMER1", 0, "Timer 1", ""},
	{TIMER2, "TIMER2", 0, "Timer 2", ""},
	{0, NULL, 0, NULL, NULL}};	

EnumPropertyItem keymap_propvalue_items[] = {
		{0, "NONE", 0, "", ""},
		{0, NULL, 0, NULL, NULL}};

EnumPropertyItem keymap_modifiers_items[] = {
		{KM_ANY, "ANY", 0, "Any", ""},
		{0, "NONE", 0, "None", ""},
		{1, "FIRST", 0, "First", ""},
		{2, "SECOND", 0, "Second", ""},
		{0, NULL, 0, NULL, NULL}};

EnumPropertyItem operator_flag_items[] = {
		{OPTYPE_REGISTER, "REGISTER", 0, "Register", ""},
		{OPTYPE_UNDO, "UNDO", 0, "Undo", ""},
		{OPTYPE_BLOCKING, "BLOCKING", 0, "Finished", ""},
		{OPTYPE_MACRO, "MACRO", 0, "Macro", ""},
		{OPTYPE_GRAB_POINTER, "GRAB_POINTER", 0, "Grab Pointer", ""},
		{0, NULL, 0, NULL, NULL}};

EnumPropertyItem operator_return_items[] = {
		{OPERATOR_RUNNING_MODAL, "RUNNING_MODAL", 0, "Running Modal", ""},
		{OPERATOR_CANCELLED, "CANCELLED", 0, "Cancelled", ""},
		{OPERATOR_FINISHED, "FINISHED", 0, "Finished", ""},
		{OPERATOR_PASS_THROUGH, "PASS_THROUGH", 0, "Pass Through", ""}, // used as a flag
		{0, NULL, 0, NULL, NULL}};

/* flag/enum */
EnumPropertyItem wm_report_items[] = {
		{RPT_DEBUG, "DEBUG", 0, "Debug", ""},
		{RPT_INFO, "INFO", 0, "Info", ""},
		{RPT_OPERATOR, "OPERATOR", 0, "Operator", ""},
		{RPT_WARNING, "WARNING", 0, "Warning", ""},
		{RPT_ERROR, "ERROR", 0, "Error", ""},
		{RPT_ERROR_INVALID_INPUT, "ERROR_INVALID_INPUT", 0, "Invalid Input", ""},\
		{RPT_ERROR_INVALID_CONTEXT, "ERROR_INVALID_CONTEXT", 0, "Invalid Context", ""},
		{RPT_ERROR_OUT_OF_MEMORY, "ERROR_OUT_OF_MEMORY", 0, "Out of Memory", ""},
		{0, NULL, 0, NULL, NULL}};

#define KMI_TYPE_KEYBOARD	0
#define KMI_TYPE_MOUSE		1
#define KMI_TYPE_TWEAK		2
#define KMI_TYPE_TEXTINPUT	3
#define KMI_TYPE_TIMER		4

#ifdef RNA_RUNTIME

#include "WM_api.h"

#include "BKE_idprop.h"

#include "MEM_guardedalloc.h"

static wmOperator *rna_OperatorProperties_find_operator(PointerRNA *ptr)
{
	wmWindowManager *wm= ptr->id.data;
	IDProperty *properties= (IDProperty*)ptr->data;
	wmOperator *op;

	if(wm)
		for(op=wm->operators.first; op; op=op->next)
			if(op->properties == properties)
				return op;
	
	return NULL;
}

static StructRNA *rna_OperatorProperties_refine(PointerRNA *ptr)
{
	wmOperator *op= rna_OperatorProperties_find_operator(ptr);

	if(op)
		return op->type->srna;
	else
		return ptr->type;
}

static IDProperty *rna_OperatorProperties_idprops(PointerRNA *ptr, int create)
{
	if(create && !ptr->data) {
		IDPropertyTemplate val = {0};
		ptr->data= IDP_New(IDP_GROUP, val, "RNA_OperatorProperties group");
	}

	return ptr->data;
}

static void rna_Operator_name_get(PointerRNA *ptr, char *value)
{
	wmOperator *op= (wmOperator*)ptr->data;
	strcpy(value, op->type->name);
}

static int rna_Operator_name_length(PointerRNA *ptr)
{
	wmOperator *op= (wmOperator*)ptr->data;
	return strlen(op->type->name);
}

static int rna_Operator_has_reports_get(PointerRNA *ptr)
{
	wmOperator *op= (wmOperator*)ptr->data;
	return (op->reports && op->reports->list.first);
}

static PointerRNA rna_Operator_properties_get(PointerRNA *ptr)
{
	wmOperator *op= (wmOperator*)ptr->data;
	return rna_pointer_inherit_refine(ptr, op->type->srna, op->properties);
}

static PointerRNA rna_OperatorTypeMacro_properties_get(PointerRNA *ptr)
{
	wmOperatorTypeMacro *otmacro= (wmOperatorTypeMacro*)ptr->data;
	wmOperatorType *ot = WM_operatortype_find(otmacro->idname, TRUE);
	return rna_pointer_inherit_refine(ptr, ot->srna, otmacro->properties);
}

static void rna_Event_ascii_get(PointerRNA *ptr, char *value)
{
	wmEvent *event= (wmEvent*)ptr->id.data;
	value[0]= event->ascii;
	value[1]= '\0';
}

static int rna_Event_ascii_length(PointerRNA *ptr)
{
	wmEvent *event= (wmEvent*)ptr->id.data;
	return (event->ascii)? 1 : 0;
}

static void rna_Window_screen_set(PointerRNA *ptr, PointerRNA value)
{
	wmWindow *win= (wmWindow*)ptr->data;

	if(value.data == NULL)
		return;

	/* exception: can't set screens inside of area/region handers */
	win->newscreen= value.data;
}

static void rna_Window_screen_update(bContext *C, PointerRNA *ptr)
{
	wmWindow *win= (wmWindow*)ptr->data;

	/* exception: can't set screens inside of area/region handers */
	if(win->newscreen) {
		WM_event_add_notifier(C, NC_SCREEN|ND_SCREENBROWSE, win->newscreen);
		win->newscreen= NULL;
	}
}

static PointerRNA rna_KeyMapItem_properties_get(PointerRNA *ptr)
{
	wmKeyMapItem *kmi= ptr->data;

	if(kmi->ptr)
		return *(kmi->ptr);
	
	//return rna_pointer_inherit_refine(ptr, &RNA_OperatorProperties, op->properties);
	return PointerRNA_NULL;
}

static int rna_wmKeyMapItem_map_type_get(PointerRNA *ptr)
{
	wmKeyMapItem *kmi= ptr->data;

	if(ISTIMER(kmi->type)) return KMI_TYPE_TIMER;
	if(ISKEYBOARD(kmi->type)) return KMI_TYPE_KEYBOARD;
	if(ISTWEAK(kmi->type)) return KMI_TYPE_TWEAK;
	if(ISMOUSE(kmi->type)) return KMI_TYPE_MOUSE;
	if(kmi->type == KM_TEXTINPUT) return KMI_TYPE_TEXTINPUT;
	return KMI_TYPE_KEYBOARD;
}

static void rna_wmKeyMapItem_map_type_set(PointerRNA *ptr, int value)
{
	wmKeyMapItem *kmi= ptr->data;
	int map_type= rna_wmKeyMapItem_map_type_get(ptr);

	if(value != map_type) {
		switch(value) {
		case KMI_TYPE_KEYBOARD:
			kmi->type= AKEY;
			kmi->val= KM_PRESS;
			break;
		case KMI_TYPE_TWEAK:
			kmi->type= EVT_TWEAK_L;
			kmi->val= KM_ANY;
			break;
		case KMI_TYPE_MOUSE:
			kmi->type= LEFTMOUSE;
			kmi->val= KM_PRESS;
			break;
		case KMI_TYPE_TEXTINPUT:
			kmi->type= KM_TEXTINPUT;
			kmi->val= KM_NOTHING;
			break;
		case KMI_TYPE_TIMER:
			kmi->type= TIMER;
			kmi->val= KM_NOTHING;
			break;
		}
	}
}

static EnumPropertyItem *rna_KeyMapItem_type_itemf(bContext *C, PointerRNA *ptr, int *free)
{
	int map_type= rna_wmKeyMapItem_map_type_get(ptr);

	if(map_type == KMI_TYPE_MOUSE) return event_mouse_type_items;
	if(map_type == KMI_TYPE_TWEAK) return event_tweak_type_items;
	if(map_type == KMI_TYPE_TIMER) return event_timer_type_items;
	else return event_type_items;
}

static EnumPropertyItem *rna_KeyMapItem_value_itemf(bContext *C, PointerRNA *ptr, int *free)
{
	int map_type= rna_wmKeyMapItem_map_type_get(ptr);

	if(map_type == KMI_TYPE_MOUSE || map_type == KMI_TYPE_KEYBOARD) return event_keymouse_value_items;
	if(map_type == KMI_TYPE_TWEAK) return event_tweak_value_items;
	else return event_value_items;
}

static EnumPropertyItem *rna_KeyMapItem_propvalue_itemf(bContext *C, PointerRNA *ptr, int *free)
{
	wmWindowManager *wm = CTX_wm_manager(C);
	wmKeyConfig *kc;
	wmKeyMap *km;

	/* check user keymaps */
	for(km=U.keymaps.first; km; km=km->next) {
		wmKeyMapItem *kmi;
		for (kmi=km->items.first; kmi; kmi=kmi->next) {
			if (kmi == ptr->data) {
				if (!km->modal_items) {
					if (!WM_keymap_user_init(wm, km)) {
						return keymap_propvalue_items; /* ERROR */
					}
				}

				return km->modal_items;
			}
		}
	}

	for(kc=wm->keyconfigs.first; kc; kc=kc->next) {
		for(km=kc->keymaps.first; km; km=km->next) {
			/* only check if it's a modal keymap */
			if (km->modal_items) {
				wmKeyMapItem *kmi;
				for (kmi=km->items.first; kmi; kmi=kmi->next) {
					if (kmi == ptr->data) {
						return km->modal_items;
					}
				}
			}
		}
	}


	return keymap_propvalue_items; /* ERROR */
}

static int rna_KeyMapItem_any_getf(PointerRNA *ptr)
{
	wmKeyMapItem *kmi = (wmKeyMapItem*)ptr->data;

	if (kmi->shift == KM_ANY &&
		kmi->ctrl == KM_ANY &&
		kmi->alt == KM_ANY &&
		kmi->oskey == KM_ANY)

		return 1;
	else
		return 0;
}

static void rna_KeyMapItem_any_setf(PointerRNA *ptr, int value)
{
	wmKeyMapItem *kmi = (wmKeyMapItem*)ptr->data;

	if(value) {
		kmi->shift= kmi->ctrl= kmi->alt= kmi->oskey= KM_ANY;
	}
	else {
		kmi->shift= kmi->ctrl= kmi->alt= kmi->oskey= 0;
	}
}


static PointerRNA rna_WindowManager_active_keyconfig_get(PointerRNA *ptr)
{
	wmWindowManager *wm= ptr->data;
	wmKeyConfig *kc;

	for(kc=wm->keyconfigs.first; kc; kc=kc->next)
		if(strcmp(kc->idname, U.keyconfigstr) == 0)
			break;
	
	if(!kc)
		kc= wm->defaultconf;
	
	return rna_pointer_inherit_refine(ptr, &RNA_KeyConfig, kc);
}

static void rna_WindowManager_active_keyconfig_set(PointerRNA *ptr, PointerRNA value)
{
	wmKeyConfig *kc= value.data;

	if(kc)
		BLI_strncpy(U.keyconfigstr, kc->idname, sizeof(U.keyconfigstr));
}

static void rna_wmKeyMapItem_idname_get(PointerRNA *ptr, char *value)
{
	wmKeyMapItem *kmi= ptr->data;
	WM_operator_py_idname(value, kmi->idname);
}

static int rna_wmKeyMapItem_idname_length(PointerRNA *ptr)
{
	wmKeyMapItem *kmi= ptr->data;
	char pyname[OP_MAX_TYPENAME];

	WM_operator_py_idname(pyname, kmi->idname);
	return strlen(pyname);
}

static void rna_wmKeyMapItem_idname_set(PointerRNA *ptr, const char *value)
{
	wmKeyMapItem *kmi= ptr->data;
	char idname[OP_MAX_TYPENAME];

	WM_operator_bl_idname(idname, value);

	if(strcmp(idname, kmi->idname) != 0) {
		BLI_strncpy(kmi->idname, idname, sizeof(kmi->idname));

		WM_keymap_properties_reset(kmi);
	}
}

static void rna_wmKeyMapItem_name_get(PointerRNA *ptr, char *value)
{
	wmKeyMapItem *kmi= ptr->data;
	wmOperatorType *ot= WM_operatortype_find(kmi->idname, 1);
	
	if (ot)
		strcpy(value, ot->name);
}

static int rna_wmKeyMapItem_name_length(PointerRNA *ptr)
{
	wmKeyMapItem *kmi= ptr->data;
	wmOperatorType *ot= WM_operatortype_find(kmi->idname, 1);
	
	if (ot)
		return strlen(ot->name);
	else
		return 0;
}

#ifndef DISABLE_PYTHON
static void rna_Operator_unregister(const bContext *C, StructRNA *type)
{
	char *idname;
	wmOperatorType *ot= RNA_struct_blender_type_get(type);

	if(!ot)
		return;

	/* update while blender is running */
	if(C) {
		WM_operator_stack_clear((bContext*)C);
		WM_main_add_notifier(NC_SCREEN|NA_EDITED, NULL);
	}

	RNA_struct_free_extension(type, &ot->ext);

	idname= ot->idname;
	WM_operatortype_remove(ot->idname);
	MEM_freeN(idname);

	/* not to be confused with the RNA_struct_free that WM_operatortype_remove calls, they are 2 different srna's */
	RNA_struct_free(&BLENDER_RNA, type);
}

static int operator_poll(bContext *C, wmOperatorType *ot)
{
	PointerRNA ptr;
	ParameterList list;
	FunctionRNA *func;
	void *ret;
	int visible;

	RNA_pointer_create(NULL, ot->ext.srna, NULL, &ptr); /* dummy */
	func= RNA_struct_find_function(&ptr, "poll");

	RNA_parameter_list_create(&list, &ptr, func);
	RNA_parameter_set_lookup(&list, "context", &C);
	ot->ext.call(&ptr, func, &list);

	RNA_parameter_get_lookup(&list, "visible", &ret);
	visible= *(int*)ret;

	RNA_parameter_list_free(&list);

	return visible;
}

static int operator_exec(bContext *C, wmOperator *op)
{
	PointerRNA opr;
	ParameterList list;
	FunctionRNA *func;
	void *ret;
	int result;

	RNA_pointer_create(&CTX_wm_screen(C)->id, op->type->ext.srna, op, &opr);
	func= RNA_struct_find_function(&opr, "execute");

	RNA_parameter_list_create(&list, &opr, func);
	RNA_parameter_set_lookup(&list, "context", &C);
	op->type->ext.call(&opr, func, &list);

	RNA_parameter_get_lookup(&list, "result", &ret);
	result= *(int*)ret;

	RNA_parameter_list_free(&list);

	return result;
}

static int operator_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	PointerRNA opr;
	ParameterList list;
	FunctionRNA *func;
	void *ret;
	int result;

	RNA_pointer_create(&CTX_wm_screen(C)->id, op->type->ext.srna, op, &opr);
	func= RNA_struct_find_function(&opr, "invoke");

	RNA_parameter_list_create(&list, &opr, func);
	RNA_parameter_set_lookup(&list, "context", &C);
	RNA_parameter_set_lookup(&list, "event", &event);
	op->type->ext.call(&opr, func, &list);

	RNA_parameter_get_lookup(&list, "result", &ret);
	result= *(int*)ret;

	RNA_parameter_list_free(&list);

	return result;
}

/* same as invoke */
static int operator_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	PointerRNA opr;
	ParameterList list;
	FunctionRNA *func;
	void *ret;
	int result;

	RNA_pointer_create(&CTX_wm_screen(C)->id, op->type->ext.srna, op, &opr);
	func= RNA_struct_find_function(&opr, "modal");

	RNA_parameter_list_create(&list, &opr, func);
	RNA_parameter_set_lookup(&list, "context", &C);
	RNA_parameter_set_lookup(&list, "event", &event);
	op->type->ext.call(&opr, func, &list);

	RNA_parameter_get_lookup(&list, "result", &ret);
	result= *(int*)ret;

	RNA_parameter_list_free(&list);

	return result;
}

static void operator_draw(bContext *C, wmOperator *op)
{
	PointerRNA opr;
	ParameterList list;
	FunctionRNA *func;

	RNA_pointer_create(&CTX_wm_screen(C)->id, op->type->ext.srna, op, &opr);
	func= RNA_struct_find_function(&opr, "draw");

	RNA_parameter_list_create(&list, &opr, func);
	RNA_parameter_set_lookup(&list, "context", &C);
	op->type->ext.call(&opr, func, &list);

	RNA_parameter_list_free(&list);
}

void operator_wrapper(wmOperatorType *ot, void *userdata);
void macro_wrapper(wmOperatorType *ot, void *userdata);

static char _operator_idname[OP_MAX_TYPENAME];
static char _operator_name[OP_MAX_TYPENAME];
static char _operator_descr[1024];
static StructRNA *rna_Operator_register(const bContext *C, ReportList *reports, void *data, const char *identifier, StructValidateFunc validate, StructCallbackFunc call, StructFreeFunc free)
{
	wmOperatorType dummyot = {0};
	wmOperator dummyop= {0};
	PointerRNA dummyotr;
	int have_function[5];

	/* setup dummy operator & operator type to store static properties in */
	dummyop.type= &dummyot;
	dummyot.idname= _operator_idname; /* only assigne the pointer, string is NULL'd */
	dummyot.name= _operator_name; /* only assigne the pointer, string is NULL'd */
	dummyot.description= _operator_descr; /* only assigne the pointer, string is NULL'd */
	RNA_pointer_create(NULL, &RNA_Operator, &dummyop, &dummyotr);

	/* validate the python class */
	if(validate(&dummyotr, data, have_function) != 0)
		return NULL;

	{	/* convert foo.bar to FOO_OT_bar
		 * allocate the description and the idname in 1 go */
		int idlen = strlen(_operator_idname) + 4;
		int namelen = strlen(_operator_name) + 1;
		int desclen = strlen(_operator_descr) + 1;
		char *ch, *ch_arr;
		ch_arr= ch= MEM_callocN(sizeof(char) * (idlen + namelen + desclen), "_operator_idname"); /* 2 terminators and 3 to convert a.b -> A_OT_b */
		WM_operator_bl_idname(ch, _operator_idname); /* convert the idname from python */
		dummyot.idname= ch;
		ch += idlen;
		strcpy(ch, _operator_name);
		dummyot.name = ch;
		ch += namelen;
		strcpy(ch, _operator_descr);
		dummyot.description = ch;
	}

	if(strlen(identifier) >= sizeof(dummyop.idname)) {
		BKE_reportf(reports, RPT_ERROR, "registering operator class: '%s' is too long, maximum length is %d.", identifier, sizeof(dummyop.idname));
		return NULL;
	}

	/* check if we have registered this operator type before, and remove it */
	{
		wmOperatorType *ot= WM_operatortype_find(dummyot.idname, TRUE);
		if(ot && ot->ext.srna)
			rna_Operator_unregister(C, ot->ext.srna);
	}

	/* create a new menu type */
	dummyot.ext.srna= RNA_def_struct(&BLENDER_RNA, dummyot.idname, "Operator");
	dummyot.ext.data= data;
	dummyot.ext.call= call;
	dummyot.ext.free= free;

	dummyot.pyop_poll=	(have_function[0])? operator_poll: NULL;
	dummyot.exec=		(have_function[1])? operator_exec: NULL;
	dummyot.invoke=		(have_function[2])? operator_invoke: NULL;
	dummyot.modal=		(have_function[3])? operator_modal: NULL;
	dummyot.ui=			(have_function[4])? operator_draw: NULL;

	WM_operatortype_append_ptr(operator_wrapper, (void *)&dummyot);

	/* update while blender is running */
	if(C)
		WM_main_add_notifier(NC_SCREEN|NA_EDITED, NULL);

	return dummyot.ext.srna;
}


static StructRNA *rna_MacroOperator_register(const bContext *C, ReportList *reports, void *data, const char *identifier, StructValidateFunc validate, StructCallbackFunc call, StructFreeFunc free)
{
	wmOperatorType dummyot = {0};
	wmOperator dummyop= {0};
	PointerRNA dummyotr;
	int have_function[4];

	/* setup dummy operator & operator type to store static properties in */
	dummyop.type= &dummyot;
	dummyot.idname= _operator_idname; /* only assigne the pointer, string is NULL'd */
	dummyot.name= _operator_name; /* only assigne the pointer, string is NULL'd */
	dummyot.description= _operator_descr; /* only assigne the pointer, string is NULL'd */
	RNA_pointer_create(NULL, &RNA_Macro, &dummyop, &dummyotr);

	/* validate the python class */
	if(validate(&dummyotr, data, have_function) != 0)
		return NULL;

	{	/* convert foo.bar to FOO_OT_bar
		 * allocate the description and the idname in 1 go */
		int idlen = strlen(_operator_idname) + 4;
		int namelen = strlen(_operator_name) + 1;
		int desclen = strlen(_operator_descr) + 1;
		char *ch, *ch_arr;
		ch_arr= ch= MEM_callocN(sizeof(char) * (idlen + namelen + desclen), "_operator_idname"); /* 2 terminators and 3 to convert a.b -> A_OT_b */
		WM_operator_bl_idname(ch, _operator_idname); /* convert the idname from python */
		dummyot.idname= ch;
		ch += idlen;
		strcpy(ch, _operator_name);
		dummyot.name = ch;
		ch += namelen;
		strcpy(ch, _operator_descr);
		dummyot.description = ch;
	}

	if(strlen(identifier) >= sizeof(dummyop.idname)) {
		BKE_reportf(reports, RPT_ERROR, "registering operator class: '%s' is too long, maximum length is %d.", identifier, sizeof(dummyop.idname));
		return NULL;
	}

	/* check if we have registered this operator type before, and remove it */
	{
		wmOperatorType *ot= WM_operatortype_find(dummyot.idname, TRUE);
		if(ot && ot->ext.srna)
			rna_Operator_unregister(C, ot->ext.srna);
	}

	/* create a new menu type */
	dummyot.ext.srna= RNA_def_struct(&BLENDER_RNA, dummyot.idname, "Operator");
	dummyot.ext.data= data;
	dummyot.ext.call= call;
	dummyot.ext.free= free;

	dummyot.pyop_poll=	(have_function[0])? operator_poll: NULL;
	dummyot.ui=			(have_function[3])? operator_draw: NULL;

	WM_operatortype_append_macro_ptr(macro_wrapper, (void *)&dummyot);

	/* update while blender is running */
	if(C)
		WM_main_add_notifier(NC_SCREEN|NA_EDITED, NULL);

	return dummyot.ext.srna;
}
#endif /* DISABLE_PYTHON */

static StructRNA* rna_Operator_refine(PointerRNA *opr)
{
	wmOperator *op= (wmOperator*)opr->data;
	return (op->type && op->type->ext.srna)? op->type->ext.srna: &RNA_Operator;
}

static StructRNA* rna_MacroOperator_refine(PointerRNA *opr)
{
	wmOperator *op= (wmOperator*)opr->data;
	return (op->type && op->type->ext.srna)? op->type->ext.srna: &RNA_Macro;
}

static wmKeyMapItem *rna_KeyMap_add_item(wmKeyMap *km, ReportList *reports, char *idname, int type, int value, int any, int shift, int ctrl, int alt, int oskey, int keymodifier)
{
//	wmWindowManager *wm = CTX_wm_manager(C);
	int modifier= 0;

	/* only on non-modal maps */
	if (km->flag & KEYMAP_MODAL) {
		BKE_report(reports, RPT_ERROR, "Not a non-modal keymap.");
		return NULL;
	}

	if(shift) modifier |= KM_SHIFT;
	if(ctrl) modifier |= KM_CTRL;
	if(alt) modifier |= KM_ALT;
	if(oskey) modifier |= KM_OSKEY;

	if(any) modifier = KM_ANY;

	return WM_keymap_add_item(km, idname, type, value, modifier, keymodifier);
}

static wmKeyMapItem *rna_KeyMap_add_modal_item(wmKeyMap *km, bContext *C, ReportList *reports, char* propvalue_str, int type, int value, int any, int shift, int ctrl, int alt, int oskey, int keymodifier)
{
	wmWindowManager *wm = CTX_wm_manager(C);
	int modifier= 0;
	int propvalue = 0;

	/* only modal maps */
	if ((km->flag & KEYMAP_MODAL) == 0) {
		BKE_report(reports, RPT_ERROR, "Not a modal keymap.");
		return NULL;
	}

	if (!km->modal_items) {
		if(!WM_keymap_user_init(wm, km)) {
			BKE_report(reports, RPT_ERROR, "User defined keymap doesn't correspond to a system keymap.");
			return NULL;
		}
	}

	if (!km->modal_items) {
		BKE_report(reports, RPT_ERROR, "No property values defined.");
		return NULL;
	}


	if(RNA_enum_value_from_id(km->modal_items, propvalue_str, &propvalue)==0) {
		BKE_report(reports, RPT_WARNING, "Property value not in enumeration.");
	}

	if(shift) modifier |= KM_SHIFT;
	if(ctrl) modifier |= KM_CTRL;
	if(alt) modifier |= KM_ALT;
	if(oskey) modifier |= KM_OSKEY;

	if(any) modifier = KM_ANY;

	return WM_modalkeymap_add_item(km, type, value, modifier, keymodifier, propvalue);
}

#else /* RNA_RUNTIME */

static void rna_def_operator(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "Operator", NULL);
	RNA_def_struct_ui_text(srna, "Operator", "Storage of an operator being executed, or registered after execution");
	RNA_def_struct_sdna(srna, "wmOperator");
	RNA_def_struct_refine_func(srna, "rna_Operator_refine");
#ifndef DISABLE_PYTHON
	RNA_def_struct_register_funcs(srna, "rna_Operator_register", "rna_Operator_unregister");
#endif

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_string_funcs(prop, "rna_Operator_name_get", "rna_Operator_name_length", NULL);
	RNA_def_property_ui_text(prop, "Name", "");

	prop= RNA_def_property(srna, "properties", PROP_POINTER, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "OperatorProperties");
	RNA_def_property_ui_text(prop, "Properties", "");
	RNA_def_property_pointer_funcs(prop, "rna_Operator_properties_get", NULL, NULL, NULL);
	
	prop= RNA_def_property(srna, "has_reports", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE); /* this is 'virtual' property */
	RNA_def_property_boolean_funcs(prop, "rna_Operator_has_reports_get", NULL);
	RNA_def_property_ui_text(prop, "Has Reports", "Operator has a set of reports (warnings and errors) from last execution");
	
	prop= RNA_def_property(srna, "layout", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "UILayout");

	/* Registration */
	prop= RNA_def_property(srna, "bl_idname", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "type->idname");
	RNA_def_property_string_maxlength(prop, OP_MAX_TYPENAME); /* else it uses the pointer size! */
	RNA_def_property_flag(prop, PROP_REGISTER);
	RNA_def_struct_name_property(srna, prop);

	prop= RNA_def_property(srna, "bl_label", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "type->name");
	RNA_def_property_string_maxlength(prop, 1024); /* else it uses the pointer size! */
	RNA_def_property_flag(prop, PROP_REGISTER);

	prop= RNA_def_property(srna, "bl_description", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "type->description");
	RNA_def_property_string_maxlength(prop, 1024); /* else it uses the pointer size! */
	RNA_def_property_flag(prop, PROP_REGISTER);

	prop= RNA_def_property(srna, "bl_options", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "type->flag");
	RNA_def_property_enum_items(prop, operator_flag_items);
	RNA_def_property_flag(prop, PROP_REGISTER_OPTIONAL|PROP_ENUM_FLAG);
	RNA_def_property_ui_text(prop, "Options",  "Options for this operator type");

	RNA_api_operator(srna);

	srna= RNA_def_struct(brna, "OperatorProperties", NULL);
	RNA_def_struct_ui_text(srna, "Operator Properties", "Input properties of an Operator");
	RNA_def_struct_refine_func(srna, "rna_OperatorProperties_refine");
	RNA_def_struct_idprops_func(srna, "rna_OperatorProperties_idprops");
}

static void rna_def_macro_operator(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "Macro", NULL);
	RNA_def_struct_ui_text(srna, "Macro Operator", "Storage of a macro operator being executed, or registered after execution");
	RNA_def_struct_sdna(srna, "wmOperator");
	RNA_def_struct_refine_func(srna, "rna_MacroOperator_refine");
#ifndef DISABLE_PYTHON
	RNA_def_struct_register_funcs(srna, "rna_MacroOperator_register", "rna_Operator_unregister");
#endif
    
	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_string_funcs(prop, "rna_Operator_name_get", "rna_Operator_name_length", NULL);
	RNA_def_property_ui_text(prop, "Name", "");

	prop= RNA_def_property(srna, "properties", PROP_POINTER, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "OperatorProperties");
	RNA_def_property_ui_text(prop, "Properties", "");
	RNA_def_property_pointer_funcs(prop, "rna_Operator_properties_get", NULL, NULL, NULL);

	/* Registration */
	prop= RNA_def_property(srna, "bl_idname", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "type->idname");
	RNA_def_property_string_maxlength(prop, OP_MAX_TYPENAME); /* else it uses the pointer size! */
	RNA_def_property_flag(prop, PROP_REGISTER);
	RNA_def_struct_name_property(srna, prop);

	prop= RNA_def_property(srna, "bl_label", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "type->name");
	RNA_def_property_string_maxlength(prop, 1024); /* else it uses the pointer size! */
	RNA_def_property_flag(prop, PROP_REGISTER);

	prop= RNA_def_property(srna, "bl_description", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "type->description");
	RNA_def_property_string_maxlength(prop, 1024); /* else it uses the pointer size! */
	RNA_def_property_flag(prop, PROP_REGISTER);

	prop= RNA_def_property(srna, "bl_options", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "type->flag");
	RNA_def_property_enum_items(prop, operator_flag_items);
	RNA_def_property_flag(prop, PROP_REGISTER_OPTIONAL|PROP_ENUM_FLAG);
	RNA_def_property_ui_text(prop, "Options",  "Options for this operator type");

	RNA_api_macro(srna);
}

static void rna_def_operator_type_macro(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "OperatorTypeMacro", NULL);
	RNA_def_struct_ui_text(srna, "OperatorTypeMacro", "Storage of a sub operator in a macro after it has been added");
	RNA_def_struct_sdna(srna, "wmOperatorTypeMacro");

//	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
//	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
//	RNA_def_property_string_sdna(prop, NULL, "idname");
//	RNA_def_property_ui_text(prop, "Name", "Name of the sub operator");
//	RNA_def_struct_name_property(srna, prop);

	prop= RNA_def_property(srna, "properties", PROP_POINTER, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "OperatorProperties");
	RNA_def_property_ui_text(prop, "Properties", "");
	RNA_def_property_pointer_funcs(prop, "rna_OperatorTypeMacro_properties_get", NULL, NULL, NULL);
}

static void rna_def_operator_utils(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "OperatorMousePath", "IDPropertyGroup");
	RNA_def_struct_ui_text(srna, "Operator Mouse Path", "Mouse path values for operators that record such paths");

	prop= RNA_def_property(srna, "loc", PROP_FLOAT, PROP_XYZ);
	RNA_def_property_flag(prop, PROP_IDPROPERTY);
	RNA_def_property_array(prop, 2);
	RNA_def_property_ui_text(prop, "Location", "Mouse location");

	prop= RNA_def_property(srna, "time", PROP_FLOAT, PROP_NONE);
	RNA_def_property_flag(prop, PROP_IDPROPERTY);
	RNA_def_property_ui_text(prop, "Time", "Time of mouse location");
}

static void rna_def_operator_filelist_element(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "OperatorFileListElement", "IDPropertyGroup");
	RNA_def_struct_ui_text(srna, "Operator File List Element", "");
	
	
	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_flag(prop, PROP_IDPROPERTY);
	RNA_def_property_ui_text(prop, "Name", "the name of a file or directory within a file list");
}
	
static void rna_def_event(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna= RNA_def_struct(brna, "Event", NULL);
	RNA_def_struct_ui_text(srna, "Event", "Window Manager Event");
	RNA_def_struct_sdna(srna, "wmEvent");

	RNA_define_verify_sdna(0); // not in sdna

	/* strings */
	prop= RNA_def_property(srna, "ascii", PROP_STRING, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_string_funcs(prop, "rna_Event_ascii_get", "rna_Event_ascii_length", NULL);
	RNA_def_property_ui_text(prop, "ASCII", "Single ASCII character for this event");


	/* enums */
	prop= RNA_def_property(srna, "value", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "val");
	RNA_def_property_enum_items(prop, event_value_items);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Value",  "The type of event, only applies to some");
	
	prop= RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "type");
	RNA_def_property_enum_items(prop, event_type_items);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Type",  "");


	/* mouse */
	prop= RNA_def_property(srna, "mouse_x", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "x");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Mouse X Position", "The window relative vertical location of the mouse");
	
	prop= RNA_def_property(srna, "mouse_y", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "y");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Mouse Y Position", "The window relative horizontal location of the mouse");

	prop= RNA_def_property(srna, "mouse_region_x", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "mval[0]");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Mouse X Position", "The region relative vertical location of the mouse");

	prop= RNA_def_property(srna, "mouse_region_y", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "mval[1]");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Mouse Y Position", "The region relative horizontal location of the mouse");
	
	prop= RNA_def_property(srna, "mouse_prev_x", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "prevx");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Mouse Previous X Position", "The window relative vertical location of the mouse");
	
	prop= RNA_def_property(srna, "mouse_prev_y", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "prevy");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Mouse Previous Y Position", "The window relative horizontal location of the mouse");	


	/* modifiers */
	prop= RNA_def_property(srna, "shift", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "shift", 1);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Shift", "True when the Shift key is held");
	
	prop= RNA_def_property(srna, "ctrl", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ctrl", 1);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Ctrl", "True when the Ctrl key is held");
	
	prop= RNA_def_property(srna, "alt", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "alt", 1);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Alt", "True when the Alt/Option key is held");
	
	prop= RNA_def_property(srna, "oskey", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "oskey", 1);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "OS Key", "True when the Cmd key is held");

	RNA_define_verify_sdna(1); // not in sdna
}

static void rna_def_window(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "Window", NULL);
	RNA_def_struct_ui_text(srna, "Window", "Open window");
	RNA_def_struct_sdna(srna, "wmWindow");

	prop= RNA_def_property(srna, "screen", PROP_POINTER, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "Screen");
	RNA_def_property_ui_text(prop, "Screen", "Active screen showing in the window");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_pointer_funcs(prop, NULL, "rna_Window_screen_set", NULL, NULL);
	RNA_def_property_flag(prop, PROP_CONTEXT_UPDATE);
	RNA_def_property_update(prop, 0, "rna_Window_screen_update");
}

static void rna_def_windowmanager(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "WindowManager", "ID");
	RNA_def_struct_ui_text(srna, "Window Manager", "Window manager datablock defining open windows and other user interface data");
	RNA_def_struct_clear_flag(srna, STRUCT_ID_REFCOUNT);
	RNA_def_struct_sdna(srna, "wmWindowManager");

	prop= RNA_def_property(srna, "operators", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "Operator");
	RNA_def_property_ui_text(prop, "Operators", "Operator registry");

	prop= RNA_def_property(srna, "windows", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "Window");
	RNA_def_property_ui_text(prop, "Windows", "Open windows");

	prop= RNA_def_property(srna, "keyconfigs", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "KeyConfig");
	RNA_def_property_ui_text(prop, "Key Configurations", "Registered key configurations");

	prop= RNA_def_property(srna, "active_keyconfig", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "KeyConfig");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_pointer_funcs(prop, "rna_WindowManager_active_keyconfig_get", "rna_WindowManager_active_keyconfig_set", 0, NULL);
	RNA_def_property_ui_text(prop, "Active Key Configuration", "");

	prop= RNA_def_property(srna, "default_keyconfig", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "defaultconf");
	RNA_def_property_struct_type(prop, "KeyConfig");
	RNA_def_property_ui_text(prop, "Default Key Configuration", "");

	RNA_api_wm(srna);
}

/* keyconfig.items */
static void rna_def_keymap_items(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
//	PropertyRNA *prop;

	FunctionRNA *func;
	PropertyRNA *parm;
	
	RNA_def_property_srna(cprop, "KeyMapItems");
	srna= RNA_def_struct(brna, "KeyMapItems", NULL);
	RNA_def_struct_sdna(srna, "wmKeyMap");
	RNA_def_struct_ui_text(srna, "KeyMap Items", "Collection of keymap items");

	func= RNA_def_function(srna, "add", "rna_KeyMap_add_item");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	parm= RNA_def_string(func, "idname", "", 0, "Operator Identifier", "");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_enum(func, "type", event_type_items, 0, "Type", "");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_enum(func, "value", event_value_items, 0, "Value", "");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	RNA_def_boolean(func, "any", 0, "Any", "");
	RNA_def_boolean(func, "shift", 0, "Shift", "");
	RNA_def_boolean(func, "ctrl", 0, "Ctrl", "");
	RNA_def_boolean(func, "alt", 0, "Alt", "");
	RNA_def_boolean(func, "oskey", 0, "OS Key", "");
	RNA_def_enum(func, "key_modifier", event_type_items, 0, "Key Modifier", "");
	parm= RNA_def_pointer(func, "item", "KeyMapItem", "Item", "Added key map item.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "add_modal", "rna_KeyMap_add_modal_item");
	RNA_def_function_flag(func, FUNC_USE_CONTEXT|FUNC_USE_REPORTS);
	parm= RNA_def_string(func, "propvalue", "", 0, "Property Value", "");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_enum(func, "type", event_type_items, 0, "Type", "");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_enum(func, "value", event_value_items, 0, "Value", "");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	RNA_def_boolean(func, "any", 0, "Any", "");
	RNA_def_boolean(func, "shift", 0, "Shift", "");
	RNA_def_boolean(func, "ctrl", 0, "Ctrl", "");
	RNA_def_boolean(func, "alt", 0, "Alt", "");
	RNA_def_boolean(func, "oskey", 0, "OS Key", "");
	RNA_def_enum(func, "key_modifier", event_type_items, 0, "Key Modifier", "");
	parm= RNA_def_pointer(func, "item", "KeyMapItem", "Item", "Added key map item.");
	RNA_def_function_return(func, parm);
	
}

static void rna_def_keyconfig(BlenderRNA *brna)
{
	StructRNA *srna;
	// FunctionRNA *func;
	// PropertyRNA *parm;
	PropertyRNA *prop;

	static EnumPropertyItem map_type_items[] = {
		{KMI_TYPE_KEYBOARD, "KEYBOARD", 0, "Keyboard", ""},
		{KMI_TYPE_TWEAK, "TWEAK", 0, "Tweak", ""},
		{KMI_TYPE_MOUSE, "MOUSE", 0, "Mouse", ""},
		{KMI_TYPE_TEXTINPUT, "TEXTINPUT", 0, "Text Input", ""},
		{KMI_TYPE_TIMER, "TIMER", 0, "Timer", ""},
		{0, NULL, 0, NULL, NULL}};

	/* KeyConfig */
	srna= RNA_def_struct(brna, "KeyConfig", NULL);
	RNA_def_struct_sdna(srna, "wmKeyConfig");
	RNA_def_struct_ui_text(srna, "Key Configuration", "Input configuration, including keymaps");

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "idname");
	RNA_def_property_ui_text(prop, "Name", "Name of the key configuration");
	RNA_def_struct_name_property(srna, prop);
	
	prop= RNA_def_property(srna, "keymaps", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "KeyMap");
	RNA_def_property_ui_text(prop, "Key Maps", "Key maps configured as part of this configuration");

	prop= RNA_def_property(srna, "is_user_defined", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", KEYCONF_USER);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "User Defined", "Indicates that a keyconfig was defined by the user");

	RNA_api_keyconfig(srna);

	/* KeyMap */
	srna= RNA_def_struct(brna, "KeyMap", NULL);
	RNA_def_struct_sdna(srna, "wmKeyMap");
	RNA_def_struct_ui_text(srna, "Key Map", "Input configuration, including keymaps");

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "idname");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Name", "Name of the key map");
	RNA_def_struct_name_property(srna, prop);

	prop= RNA_def_property(srna, "space_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "spaceid");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_enum_items(prop, space_type_items);
	RNA_def_property_ui_text(prop, "Space Type", "Optional space type keymap is associated with");

	prop= RNA_def_property(srna, "region_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "regionid");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_enum_items(prop, region_type_items);
	RNA_def_property_ui_text(prop, "Region Type", "Optional region type keymap is associated with");

	prop= RNA_def_property(srna, "items", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "KeyMapItem");
	RNA_def_property_ui_text(prop, "Items", "Items in the keymap, linking an operator to an input event");
	rna_def_keymap_items(brna, prop);

	prop= RNA_def_property(srna, "is_user_defined", PROP_BOOLEAN, PROP_NEVER_NULL);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", KEYMAP_USER);
	RNA_def_property_ui_text(prop, "User Defined", "Keymap is defined by the user");

	prop= RNA_def_property(srna, "is_modal", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", KEYMAP_MODAL);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Modal Keymap", "Indicates that a keymap is used for translate modal events for an operator");

	prop= RNA_def_property(srna, "show_expanded_items", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", KEYMAP_EXPANDED);
	RNA_def_property_ui_text(prop, "Items Expanded", "Expanded in the user interface");
	RNA_def_property_ui_icon(prop, ICON_TRIA_RIGHT, 1);
	
	prop= RNA_def_property(srna, "show_expanded_children", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", KEYMAP_CHILDREN_EXPANDED);
	RNA_def_property_ui_text(prop, "Children Expanded", "Children expanded in the user interface");
	RNA_def_property_ui_icon(prop, ICON_TRIA_RIGHT, 1);


	RNA_api_keymap(srna);

	/* KeyMapItem */
	srna= RNA_def_struct(brna, "KeyMapItem", NULL);
	RNA_def_struct_sdna(srna, "wmKeyMapItem");
	RNA_def_struct_ui_text(srna, "Key Map Item", "Item in a Key Map");

	prop= RNA_def_property(srna, "idname", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "idname");
	RNA_def_property_ui_text(prop, "Identifier", "Identifier of operator to call on input event");
	RNA_def_property_string_funcs(prop, "rna_wmKeyMapItem_idname_get", "rna_wmKeyMapItem_idname_length", "rna_wmKeyMapItem_idname_set");
	RNA_def_struct_name_property(srna, prop);
	
	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Name", "Name of operator to call on input event");
	RNA_def_property_string_funcs(prop, "rna_wmKeyMapItem_name_get", "rna_wmKeyMapItem_name_length", NULL);
	
	prop= RNA_def_property(srna, "properties", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "OperatorProperties");
	RNA_def_property_pointer_funcs(prop, "rna_KeyMapItem_properties_get", NULL, NULL, NULL);
	RNA_def_property_ui_text(prop, "Properties", "Properties to set when the operator is called");

	prop= RNA_def_property(srna, "map_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "maptype");
	RNA_def_property_enum_items(prop, map_type_items);
	RNA_def_property_enum_funcs(prop, "rna_wmKeyMapItem_map_type_get", "rna_wmKeyMapItem_map_type_set", NULL);
	RNA_def_property_ui_text(prop, "Map Type", "Type of event mapping");

	prop= RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "type");
	RNA_def_property_enum_items(prop, event_type_items);
	RNA_def_property_enum_funcs(prop, NULL, NULL, "rna_KeyMapItem_type_itemf");
	RNA_def_property_ui_text(prop, "Type", "Type of event");

	prop= RNA_def_property(srna, "value", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "val");
	RNA_def_property_enum_items(prop, event_value_items);
	RNA_def_property_enum_funcs(prop, NULL, NULL, "rna_KeyMapItem_value_itemf");
	RNA_def_property_ui_text(prop, "Value", "");

	prop= RNA_def_property(srna, "id", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "id");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "id", "ID of the item");

	prop= RNA_def_property(srna, "any", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_funcs(prop, "rna_KeyMapItem_any_getf", "rna_KeyMapItem_any_setf");
	RNA_def_property_ui_text(prop, "Any", "Any modifier keys pressed");

	prop= RNA_def_property(srna, "shift", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "shift", 0);
//	RNA_def_property_enum_sdna(prop, NULL, "shift");
//	RNA_def_property_enum_items(prop, keymap_modifiers_items);
	RNA_def_property_ui_text(prop, "Shift", "Shift key pressed");

	prop= RNA_def_property(srna, "ctrl", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ctrl", 0);
//	RNA_def_property_enum_sdna(prop, NULL, "ctrl");
//	RNA_def_property_enum_items(prop, keymap_modifiers_items);
	RNA_def_property_ui_text(prop, "Ctrl", "Control key pressed");

	prop= RNA_def_property(srna, "alt", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "alt", 0);
//	RNA_def_property_enum_sdna(prop, NULL, "alt");
//	RNA_def_property_enum_items(prop, keymap_modifiers_items);
	RNA_def_property_ui_text(prop, "Alt", "Alt key pressed");

	prop= RNA_def_property(srna, "oskey", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "oskey", 0);
//	RNA_def_property_enum_sdna(prop, NULL, "oskey");
//	RNA_def_property_enum_items(prop, keymap_modifiers_items);
	RNA_def_property_ui_text(prop, "OS Key", "Operating system key pressed");

	prop= RNA_def_property(srna, "key_modifier", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "keymodifier");
	RNA_def_property_enum_items(prop, event_type_items);
	RNA_def_property_ui_text(prop, "Key Modifier", "Regular key pressed as a modifier");

	prop= RNA_def_property(srna, "show_expanded", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", KMI_EXPANDED);
	RNA_def_property_ui_text(prop, "Expanded", "Show key map event and property details in the user interface");
	RNA_def_property_ui_icon(prop, ICON_TRIA_RIGHT, 1);

	prop= RNA_def_property(srna, "propvalue", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "propvalue");
	RNA_def_property_enum_items(prop, keymap_propvalue_items);
	RNA_def_property_enum_funcs(prop, NULL, NULL, "rna_KeyMapItem_propvalue_itemf");
	RNA_def_property_ui_text(prop, "Property Value", "The value this event translates to in a modal keymap");

	prop= RNA_def_property(srna, "active", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", KMI_INACTIVE);
	RNA_def_property_ui_text(prop, "Active", "Activate or deactivate item");
	RNA_def_property_ui_icon(prop, ICON_CHECKBOX_DEHLT, 1);

	RNA_api_keymapitem(srna);
}

void RNA_def_wm(BlenderRNA *brna)
{
	rna_def_operator(brna);
	rna_def_operator_utils(brna);
	rna_def_operator_filelist_element(brna);
	rna_def_macro_operator(brna);
	rna_def_operator_type_macro(brna);
	rna_def_event(brna);
	rna_def_window(brna);
	rna_def_windowmanager(brna);
	rna_def_keyconfig(brna);
}

#endif /* RNA_RUNTIME */

