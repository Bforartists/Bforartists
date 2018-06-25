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
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 *
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/screen/screen_user_menu.c
 *  \ingroup spview3d
 */

#include <string.h>
#include <stdio.h>
#include <math.h>
#include <float.h>

#include "DNA_scene_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"
#include "BLI_listbase.h"
#include "BLI_string.h"

#include "BLT_translation.h"

#include "BKE_blender_user_menu.h"
#include "BKE_context.h"
#include "BKE_screen.h"
#include "BKE_idprop.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_screen.h"

#include "UI_interface.h"
#include "UI_resources.h"

/* -------------------------------------------------------------------- */
/** \name Menu Type
 * \{ */

bUserMenu *ED_screen_user_menu_find(bContext *C)
{
	SpaceLink *sl = CTX_wm_space_data(C);
	const char *context = CTX_data_mode_string(C);
	return BKE_blender_user_menu_find(&U.user_menus, sl->spacetype, context);
}

bUserMenu *ED_screen_user_menu_ensure(bContext *C)
{
	SpaceLink *sl = CTX_wm_space_data(C);
	const char *context = CTX_data_mode_string(C);
	return BKE_blender_user_menu_ensure(&U.user_menus, sl->spacetype, context);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Menu Item
 * \{ */

bUserMenuItem_Op *ED_screen_user_menu_item_find_operator(
        ListBase *lb,
        wmOperatorType *ot, IDProperty *prop, short opcontext)
{
	for (bUserMenuItem *umi = lb->first; umi; umi = umi->next) {
		if (umi->type == USER_MENU_TYPE_OPERATOR) {
			bUserMenuItem_Op *umi_op = (bUserMenuItem_Op *)umi;
			if (STREQ(ot->idname, umi_op->opname) &&
			    (opcontext == umi_op->opcontext) &&
			    (IDP_EqualsProperties(prop, umi_op->prop)))
			{
				return umi_op;
			}
		}
	}
	return NULL;
}

void ED_screen_user_menu_item_add_operator(
        ListBase *lb, const char *ui_name,
        wmOperatorType *ot, IDProperty *prop, short opcontext)
{
	bUserMenuItem_Op *umi_op = (bUserMenuItem_Op *)BKE_blender_user_menu_item_add(lb, USER_MENU_TYPE_OPERATOR);
	umi_op->opcontext = opcontext;
	if (!STREQ(ui_name, ot->name)) {
		BLI_strncpy(umi_op->item.ui_name, ui_name, OP_MAX_TYPENAME);
	}
	BLI_strncpy(umi_op->opname, ot->idname, OP_MAX_TYPENAME);
	umi_op->prop = prop ? IDP_CopyProperty(prop) : NULL;
}

void ED_screen_user_menu_item_remove(ListBase *lb, bUserMenuItem *umi)
{
	BLI_remlink(lb, umi);
	BKE_blender_user_menu_item_free(umi);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Menu Definition
 * \{ */

static void screen_user_menu_draw(const bContext *C, Menu *menu)
{
	SpaceLink *sl = CTX_wm_space_data(C);
	const char *context = CTX_data_mode_string(C);
	bUserMenu *um_array[] = {
		BKE_blender_user_menu_find(&U.user_menus, sl->spacetype, context),
		(sl->spacetype != SPACE_TOPBAR) ? BKE_blender_user_menu_find(&U.user_menus, SPACE_TOPBAR, context) : NULL,
	};
	for (int um_index = 0; um_index < ARRAY_SIZE(um_array); um_index++) {
		bUserMenu *um = um_array[um_index];
		if (um == NULL) {
			continue;
		}
		for (bUserMenuItem *umi = um->items.first; umi; umi = umi->next) {
			if (umi->type == USER_MENU_TYPE_OPERATOR) {
				bUserMenuItem_Op *umi_op = (bUserMenuItem_Op *)umi;
				IDProperty *prop = umi_op->prop ? IDP_CopyProperty(umi_op->prop) : NULL;
				uiItemFullO(
				        menu->layout, umi_op->opname, umi->ui_name[0] ? umi->ui_name : NULL,
				        ICON_NONE, prop, umi_op->opcontext, 0, NULL);
			}
			else if (umi->type == USER_MENU_TYPE_SEP) {
				uiItemS(menu->layout);
			}
		}
	}
}

void ED_screen_user_menu_register(void)
{
	MenuType *mt = MEM_callocN(sizeof(MenuType), __func__);
	strcpy(mt->idname, "SCREEN_MT_user_menu");
	strcpy(mt->label, "Quick Favorites");
	strcpy(mt->translation_context, BLT_I18NCONTEXT_DEFAULT_BPYRNA);
	mt->draw = screen_user_menu_draw;
	WM_menutype_add(mt);
}

/** \} */
