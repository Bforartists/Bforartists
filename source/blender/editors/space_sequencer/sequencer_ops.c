
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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
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

#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_userdef_types.h"
#include "DNA_windowmanager_types.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"

#include "BIF_transform.h" /* transform keymap */

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_utildefines.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_screen.h"

#include "sequencer_intern.h"


/* ************************** registration **********************************/


void sequencer_operatortypes(void)
{
	/* sequencer_edit.c */
	WM_operatortype_append(SEQUENCER_OT_cut);
	WM_operatortype_append(SEQUENCER_OT_mute);
	WM_operatortype_append(SEQUENCER_OT_unmute);
	WM_operatortype_append(SEQUENCER_OT_lock);
	WM_operatortype_append(SEQUENCER_OT_unlock);
	WM_operatortype_append(SEQUENCER_OT_reload);
	WM_operatortype_append(SEQUENCER_OT_refresh_all);
	WM_operatortype_append(SEQUENCER_OT_add_duplicate);
	WM_operatortype_append(SEQUENCER_OT_delete);
	WM_operatortype_append(SEQUENCER_OT_separate_images);
	WM_operatortype_append(SEQUENCER_OT_meta_toggle);
	WM_operatortype_append(SEQUENCER_OT_meta_make);
	WM_operatortype_append(SEQUENCER_OT_meta_separate);

	WM_operatortype_append(SEQUENCER_OT_view_all);
	WM_operatortype_append(SEQUENCER_OT_view_selected);
	
	/* sequencer_select.c */
	WM_operatortype_append(SEQUENCER_OT_deselect_all);
	WM_operatortype_append(SEQUENCER_OT_select_invert);
	WM_operatortype_append(SEQUENCER_OT_select);
	WM_operatortype_append(SEQUENCER_OT_select_more);
	WM_operatortype_append(SEQUENCER_OT_select_less);
	WM_operatortype_append(SEQUENCER_OT_select_pick_linked);
	WM_operatortype_append(SEQUENCER_OT_select_linked);
	WM_operatortype_append(SEQUENCER_OT_select_handles);
	WM_operatortype_append(SEQUENCER_OT_select_active_side);
	WM_operatortype_append(SEQUENCER_OT_borderselect);
	
	/* sequencer_add.c */
	WM_operatortype_append(SEQUENCER_OT_add_scene_strip);
	WM_operatortype_append(SEQUENCER_OT_add_movie_strip);
	WM_operatortype_append(SEQUENCER_OT_add_sound_strip);
	WM_operatortype_append(SEQUENCER_OT_add_image_strip);
	WM_operatortype_append(SEQUENCER_OT_add_effect_strip);
}


void sequencer_keymap(wmWindowManager *wm)
{
	ListBase *keymap= WM_keymap_listbase(wm, "Sequencer", SPACE_SEQ, 0);
	wmKeymapItem *kmi;
	
	WM_keymap_add_item(keymap, "SEQUENCER_OT_deselect_all", AKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "SEQUENCER_OT_select_invert", IKEY, KM_PRESS, KM_CTRL, 0);
	
	RNA_enum_set(WM_keymap_add_item(keymap, "SEQUENCER_OT_cut", KKEY, KM_PRESS, 0, 0)->ptr, "type", SEQ_CUT_SOFT);
	RNA_enum_set(WM_keymap_add_item(keymap, "SEQUENCER_OT_cut", KKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "type", SEQ_CUT_HARD);
	
	RNA_enum_set(WM_keymap_add_item(keymap, "SEQUENCER_OT_mute", HKEY, KM_PRESS, 0, 0)->ptr, "type", SEQ_SELECTED);
	RNA_enum_set(WM_keymap_add_item(keymap, "SEQUENCER_OT_mute", HKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "type", SEQ_UNSELECTED);
	
	RNA_enum_set(WM_keymap_add_item(keymap, "SEQUENCER_OT_unmute", HKEY, KM_PRESS, KM_ALT, 0)->ptr, "type", SEQ_SELECTED);
	RNA_enum_set(WM_keymap_add_item(keymap, "SEQUENCER_OT_unmute", HKEY, KM_PRESS, KM_ALT|KM_SHIFT, 0)->ptr, "type", SEQ_UNSELECTED);

	WM_keymap_add_item(keymap, "SEQUENCER_OT_lock", LKEY, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_add_item(keymap, "SEQUENCER_OT_unlock", HKEY, KM_PRESS, KM_SHIFT|KM_ALT, 0);

	WM_keymap_add_item(keymap, "SEQUENCER_OT_reload", RKEY, KM_PRESS, KM_ALT, 0);

	WM_keymap_add_item(keymap, "SEQUENCER_OT_add_duplicate", DKEY, KM_PRESS, KM_SHIFT, 0);

	WM_keymap_add_item(keymap, "SEQUENCER_OT_delete", XKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "SEQUENCER_OT_delete", DELKEY, KM_PRESS, 0, 0);
	
	WM_keymap_add_item(keymap, "SEQUENCER_OT_separate_images", YKEY, KM_PRESS, 0, 0);

	WM_keymap_add_item(keymap, "SEQUENCER_OT_meta_toggle", TABKEY, KM_PRESS, 0, 0);

	WM_keymap_add_item(keymap, "SEQUENCER_OT_meta_make", MKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "SEQUENCER_OT_meta_separate", MKEY, KM_PRESS, KM_ALT, 0);

	WM_keymap_add_item(keymap, "SEQUENCER_OT_view_all", HOMEKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "SEQUENCER_OT_view_selected", PADPERIOD, KM_PRESS, 0, 0);


	/* Mouse selection, a bit verbose :/ */
	WM_keymap_add_item(keymap, "SEQUENCER_OT_select", SELECTMOUSE, KM_PRESS, 0, 0);
	RNA_boolean_set(WM_keymap_add_item(keymap, "SEQUENCER_OT_select", SELECTMOUSE, KM_PRESS, KM_SHIFT, 0)->ptr, "extend", 1);
	RNA_boolean_set(WM_keymap_add_item(keymap, "SEQUENCER_OT_select", SELECTMOUSE, KM_PRESS, KM_CTRL, 0)->ptr, "linked_left", 1);
	RNA_boolean_set(WM_keymap_add_item(keymap, "SEQUENCER_OT_select", SELECTMOUSE, KM_PRESS, KM_ALT, 0)->ptr, "linked_right", 1);
	
	kmi= WM_keymap_add_item(keymap, "SEQUENCER_OT_select", SELECTMOUSE, KM_PRESS, KM_CTRL|KM_ALT, 0);
	RNA_boolean_set(kmi->ptr, "linked_left", 1);
	RNA_boolean_set(kmi->ptr, "linked_right", 1);

	kmi= WM_keymap_add_item(keymap, "SEQUENCER_OT_select", SELECTMOUSE, KM_PRESS, KM_SHIFT|KM_CTRL|KM_ALT, 0);
	RNA_boolean_set(kmi->ptr, "extend", 1);
	RNA_boolean_set(kmi->ptr, "linked_left", 1);
	RNA_boolean_set(kmi->ptr, "linked_right", 1);

	kmi= WM_keymap_add_item(keymap, "SEQUENCER_OT_select", SELECTMOUSE, KM_PRESS, KM_SHIFT|KM_CTRL, 0);
	RNA_boolean_set(kmi->ptr, "extend", 1);
	RNA_boolean_set(kmi->ptr, "linked_left", 1);

	kmi= WM_keymap_add_item(keymap, "SEQUENCER_OT_select", SELECTMOUSE, KM_PRESS, KM_SHIFT|KM_ALT, 0);
	RNA_boolean_set(kmi->ptr, "extend", 1);
	RNA_boolean_set(kmi->ptr, "linked_right", 1);

	

	WM_keymap_add_item(keymap, "SEQUENCER_OT_select_more", PADPLUSKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "SEQUENCER_OT_select_less", PADMINUS, KM_PRESS, KM_CTRL, 0);
	
	WM_keymap_add_item(keymap, "SEQUENCER_OT_select_pick_linked", LKEY, KM_PRESS, 0, 0);
	RNA_boolean_set(WM_keymap_add_item(keymap, "SEQUENCER_OT_select_pick_linked", LKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "extend", 1);
	
	WM_keymap_add_item(keymap, "SEQUENCER_OT_select_linked", LKEY, KM_PRESS, KM_CTRL, 0);
	
	WM_keymap_add_item(keymap, "SEQUENCER_OT_borderselect", BKEY, KM_PRESS, 0, 0);
	
	WM_keymap_verify_item(keymap, "ANIM_OT_change_frame", LEFTMOUSE, KM_PRESS, 0, 0);

	transform_keymap_for_space(wm, keymap, SPACE_SEQ);
}

