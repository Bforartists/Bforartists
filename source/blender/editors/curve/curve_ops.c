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
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view3d_types.h"
#include "DNA_windowmanager_types.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_utildefines.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_screen.h"
#include "ED_object.h"

#include "BIF_transform.h"

#include "UI_interface.h"

#include "curve_intern.h"


/**************************** menus *****************************/

static int specials_menu_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	uiMenuItem *head;

	head= uiPupMenuBegin("Specials", 0);
	uiMenuItemO(head, 0, "CURVE_OT_subdivide");
	uiMenuItemO(head, 0, "CURVE_OT_switch_direction");
	uiMenuItemO(head, 0, "CURVE_OT_set_weight");
	uiMenuItemO(head, 0, "CURVE_OT_set_radius");
	uiMenuItemO(head, 0, "CURVE_OT_smooth");
	uiMenuItemO(head, 0, "CURVE_OT_smooth_radius");
	uiPupMenuEnd(C, head);

	return OPERATOR_CANCELLED;
}

void CURVE_OT_specials_menu(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Specials Menu";
	ot->idname= "CURVE_OT_specials_menu";
	
	/* api clastbacks */
	ot->invoke= specials_menu_invoke;
	ot->poll= ED_operator_editsurfcurve;
}

static int add_menu_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	Object *obedit= CTX_data_edit_object(C);
	uiMenuItem *head;

	head= uiPupMenuBegin("Add", 0);
	if(obedit->type == OB_CURVE)
		uiMenuItemsEnumO(head, "CURVE_OT_add_curve_primitive", "type");
	else
		uiMenuItemsEnumO(head, "CURVE_OT_add_surface_primitive", "type");
	uiPupMenuEnd(C, head);

	return OPERATOR_CANCELLED;
}

void CURVE_OT_add_menu(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Menu";
	ot->idname= "CURVE_OT_add_menu";
	
	/* api clastbacks */
	ot->invoke= add_menu_invoke;
	ot->poll= ED_operator_editsurfcurve;
}

/************************* registration ****************************/

void ED_operatortypes_curve(void)
{
	WM_operatortype_append(FONT_OT_textedit);

	WM_operatortype_append(CURVE_OT_hide);
	WM_operatortype_append(CURVE_OT_reveal);

	WM_operatortype_append(CURVE_OT_separate);
	WM_operatortype_append(CURVE_OT_duplicate);
	WM_operatortype_append(CURVE_OT_delete);

	WM_operatortype_append(CURVE_OT_set_weight);
	WM_operatortype_append(CURVE_OT_set_radius);
	WM_operatortype_append(CURVE_OT_set_spline_type);
	WM_operatortype_append(CURVE_OT_set_handle_type);
	WM_operatortype_append(CURVE_OT_set_smooth);
	WM_operatortype_append(CURVE_OT_clear_tilt);

	WM_operatortype_append(CURVE_OT_smooth);
	WM_operatortype_append(CURVE_OT_smooth_radius);

	WM_operatortype_append(CURVE_OT_de_select_first);
	WM_operatortype_append(CURVE_OT_de_select_last);
	WM_operatortype_append(CURVE_OT_de_select_all);
	WM_operatortype_append(CURVE_OT_select_inverse);
	WM_operatortype_append(CURVE_OT_select_linked);
	WM_operatortype_append(CURVE_OT_select_row);
	WM_operatortype_append(CURVE_OT_select_next);
	WM_operatortype_append(CURVE_OT_select_previous);
	WM_operatortype_append(CURVE_OT_select_more);
	WM_operatortype_append(CURVE_OT_select_less);
	WM_operatortype_append(CURVE_OT_select_random);
	WM_operatortype_append(CURVE_OT_select_every_nth);

	WM_operatortype_append(CURVE_OT_switch_direction);
	WM_operatortype_append(CURVE_OT_subdivide);
	WM_operatortype_append(CURVE_OT_make_segment);
	WM_operatortype_append(CURVE_OT_spin);
	WM_operatortype_append(CURVE_OT_add_vertex);
	WM_operatortype_append(CURVE_OT_extrude);
	WM_operatortype_append(CURVE_OT_toggle_cyclic);

	WM_operatortype_append(CURVE_OT_add_menu);
	WM_operatortype_append(CURVE_OT_specials_menu);

	WM_operatortype_append(CURVE_OT_add_surface_primitive);
	WM_operatortype_append(CURVE_OT_add_curve_primitive);
}

void ED_keymap_curve(wmWindowManager *wm)
{
	ListBase *keymap= WM_keymap_listbase(wm, "Font", 0, 0);
	
	/* only set in editmode font, by space_view3d listener */
	WM_keymap_add_item(keymap, "FONT_OT_textedit", KM_TEXTINPUT, KM_ANY, KM_ANY, 0);

	/* only set in editmode curve, by space_view3d listener */
	keymap= WM_keymap_listbase(wm, "Curve", 0, 0);
	
	WM_keymap_add_item(keymap, "OBJECT_OT_curve_add", AKEY, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_add_item(keymap, "CURVE_OT_add_vertex", ACTIONMOUSE, KM_PRESS, KM_CTRL, 0);

	WM_keymap_add_item(keymap, "CURVE_OT_de_select_all", AKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "CURVE_OT_select_row", RKEY, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_add_item(keymap, "CURVE_OT_select_more", PADPLUSKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "CURVE_OT_select_less", PADMINUS, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "CURVE_OT_select_linked", LKEY, KM_PRESS, 0, 0);
	RNA_boolean_set(WM_keymap_add_item(keymap, "CURVE_OT_select_linked", LKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "deselect", 1);

	WM_keymap_add_item(keymap, "CURVE_OT_separate", PKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "CURVE_OT_extrude", EKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "CURVE_OT_duplicate", DKEY, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_add_item(keymap, "CURVE_OT_make_segment", FKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "CURVE_OT_toggle_cyclic", CKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "CURVE_OT_delete", XKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "CURVE_OT_delete", DELKEY, KM_PRESS, 0, 0);

	WM_keymap_add_item(keymap, "CURVE_OT_clear_tilt", TKEY, KM_PRESS, KM_ALT, 0);
	RNA_enum_set(WM_keymap_add_item(keymap, "TFM_OT_transform", TKEY, KM_PRESS, 0, 0)->ptr, "mode", TFM_TILT);
	RNA_enum_set(WM_keymap_add_item(keymap, "CURVE_OT_set_handle_type", HKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "type", 1);
	RNA_enum_set(WM_keymap_add_item(keymap, "CURVE_OT_set_handle_type", HKEY, KM_PRESS, 0, 0)->ptr, "type", 3);
	RNA_enum_set(WM_keymap_add_item(keymap, "CURVE_OT_set_handle_type", VKEY, KM_PRESS, 0, 0)->ptr, "type", 2);

	WM_keymap_add_item(keymap, "CURVE_OT_reveal", HKEY, KM_PRESS, KM_ALT, 0);
	WM_keymap_add_item(keymap, "CURVE_OT_hide", HKEY, KM_PRESS, KM_ALT|KM_CTRL, 0);
	RNA_enum_set(WM_keymap_add_item(keymap, "CURVE_OT_hide", HKEY, KM_PRESS, KM_ALT|KM_SHIFT, 0)->ptr, "deselected", 1);

	WM_keymap_add_item(keymap, "CURVE_OT_specials_menu", WKEY, KM_PRESS, 0, 0);
}

