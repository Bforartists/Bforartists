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
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef WM_KEYMAP_H
#define WM_KEYMAP_H

/** \file WM_keymap.h
 *  \ingroup wm
 */

/* dna-savable wmStructs here */
#include "DNA_windowmanager_types.h"

#ifdef __cplusplus
extern "C" {
#endif

struct EnumPropertyItem;

/* Key Configuration */

wmKeyConfig *WM_keyconfig_new	(struct wmWindowManager *wm, const char *idname);
wmKeyConfig *WM_keyconfig_new_user(struct wmWindowManager *wm, const char *idname);
void 		WM_keyconfig_remove	(struct wmWindowManager *wm, struct wmKeyConfig *keyconf);
void 		WM_keyconfig_free	(struct wmKeyConfig *keyconf);

void		WM_keyconfig_set_active(struct wmWindowManager *wm, const char *idname);

void		WM_keyconfig_update(struct wmWindowManager *wm);
void		WM_keyconfig_update_tag(struct wmKeyMap *keymap, struct wmKeyMapItem *kmi);

/* Keymap */

void		WM_keymap_init		(struct bContext *C);
void		WM_keymap_free		(struct wmKeyMap *keymap);

wmKeyMapItem *WM_keymap_verify_item(struct wmKeyMap *keymap, const char *idname, int type, 
								 int val, int modifier, int keymodifier);
wmKeyMapItem *WM_keymap_add_item(struct wmKeyMap *keymap, const char *idname, int type, 
								 int val, int modifier, int keymodifier);
wmKeyMapItem *WM_keymap_add_menu(struct wmKeyMap *keymap, const char *idname, int type,
								 int val, int modifier, int keymodifier);

void		WM_keymap_remove_item(struct wmKeyMap *keymap, struct wmKeyMapItem *kmi);
char		 *WM_keymap_item_to_string(wmKeyMapItem *kmi, char *str, int len);

wmKeyMap	*WM_keymap_list_find(ListBase *lb, const char *idname, int spaceid, int regionid);
wmKeyMap	*WM_keymap_find(struct wmKeyConfig *keyconf, const char *idname, int spaceid, int regionid);
wmKeyMap	*WM_keymap_find_all(const struct bContext *C, const char *idname, int spaceid, int regionid);
wmKeyMap	*WM_keymap_active(struct wmWindowManager *wm, struct wmKeyMap *keymap);
wmKeyMap	*WM_keymap_guess_opname(const struct bContext *C, const char *opname);

wmKeyMapItem *WM_keymap_item_find_id(struct wmKeyMap *keymap, int id);
int			WM_keymap_item_compare(struct wmKeyMapItem *k1, struct wmKeyMapItem *k2);

/* Modal Keymap */

wmKeyMap	*WM_modalkeymap_add(struct wmKeyConfig *keyconf, const char *idname, struct EnumPropertyItem *items);
wmKeyMap	*WM_modalkeymap_get(struct wmKeyConfig *keyconf, const char *idname);
wmKeyMapItem *WM_modalkeymap_add_item(struct wmKeyMap *km, int type, int val, int modifier, int keymodifier, int value);
void		WM_modalkeymap_assign(struct wmKeyMap *km, const char *opname);

/* Keymap Editor */

void		WM_keymap_restore_to_default(struct wmKeyMap *keymap, struct bContext *C);
void		WM_keymap_properties_reset(struct wmKeyMapItem *kmi, struct IDProperty *properties);
void		WM_keymap_restore_item_to_default(struct bContext *C, struct wmKeyMap *keymap, struct wmKeyMapItem *kmi);

/* Key Event */

const char	*WM_key_event_string(short type);
int			WM_key_event_operator_id(const struct bContext *C, const char *opname, int opcontext, struct IDProperty *properties, int hotkey, struct wmKeyMap **keymap_r);
char		*WM_key_event_operator_string(const struct bContext *C, const char *opname, int opcontext, struct IDProperty *properties, char *str, int len);

#ifdef __cplusplus
}
#endif

#endif /* WM_KEYMAP_H */

