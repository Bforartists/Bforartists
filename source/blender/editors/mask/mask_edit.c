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
 * The Original Code is Copyright (C) 2012 Blender Foundation.
 * All rights reserved.
 *
 *
 * Contributor(s): Blender Foundation,
 *                 Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/mask/mask_ops.c
 *  \ingroup edmask
 */


#include "BLI_math.h"

#include "BKE_context.h"
#include "BKE_mask.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_screen.h"
#include "ED_mask.h"  /* own include */
#include "ED_object.h" /* ED_keymap_proportional_maskmode only */
#include "ED_clip.h"
#include "ED_transform.h"

#include "RNA_access.h"

#include "mask_intern.h"  /* own include */

/********************** generic poll functions *********************/

int ED_maskedit_poll(bContext *C)
{
	SpaceClip *sc = CTX_wm_space_clip(C);

	if (sc) {
		return ED_space_clip_maskedit_poll(C);
	}

	return FALSE;
}

int ED_maskedit_mask_poll(bContext *C)
{
	SpaceClip *sc = CTX_wm_space_clip(C);

	if (sc) {
		return ED_space_clip_maskedit_mask_poll(C);
	}

	return FALSE;
}

/********************** registration *********************/

void ED_mask_mouse_pos(bContext *C, wmEvent *event, float co[2])
{
	SpaceClip *sc = CTX_wm_space_clip(C);

	if (sc) {
		ED_clip_mouse_pos(C, event, co);
		BKE_mask_coord_from_movieclip(sc->clip, &sc->user, co, co);
	}
	else {
		/* possible other spaces from which mask editing is available */
		zero_v2(co);
	}
}

/* input:  x/y   - mval space
 * output: xr/yr - mask point space */
void ED_mask_point_pos(bContext *C, float x, float y, float *xr, float *yr)
{
	SpaceClip *sc = CTX_wm_space_clip(C);
	float co[2];

	if (sc) {
		ED_clip_point_stable_pos(C, x, y, &co[0], &co[1]);
		BKE_mask_coord_from_movieclip(sc->clip, &sc->user, co, co);
	}
	else {
		/* possible other spaces from which mask editing is available */
		zero_v2(co);
	}

	*xr = co[0];
	*yr = co[1];
}

void ED_mask_point_pos__reverse(bContext *C, float x, float y, float *xr, float *yr)
{
	SpaceClip *sc = CTX_wm_space_clip(C);
	ARegion *ar = CTX_wm_region(C);

	float co[2];

	if (sc && ar) {
		co[0] = x;
		co[1] = y;
		BKE_mask_coord_to_movieclip(sc->clip, &sc->user, co, co);
		ED_clip_point_stable_pos__reverse(sc, ar, co, co);
	}
	else {
		/* possible other spaces from which mask editing is available */
		zero_v2(co);
	}

	*xr = co[0];
	*yr = co[1];
}

void ED_mask_size(bContext *C, int *width, int *height)
{
	SpaceClip *sc = CTX_wm_space_clip(C);

	if (sc) {
		ED_space_clip_mask_size(sc, width, height);
	}
	else {
		/* possible other spaces from which mask editing is available */
		*width = 0;
		*height = 0;
	}
}

void ED_mask_aspect(bContext *C, float *aspx, float *aspy)
{
	SpaceClip *sc = CTX_wm_space_clip(C);

	if (sc) {
		ED_space_clip_mask_aspect(sc, aspx, aspy);
	}
	else {
		/* possible other spaces from which mask editing is available */
		*aspx = 1.0f;
		*aspy = 1.0f;
	}
}

void ED_mask_pixelspace_factor(bContext *C, float *scalex, float *scaley)
{
	SpaceClip *sc = CTX_wm_space_clip(C);

	if (sc) {
		ARegion *ar = CTX_wm_region(C);
		int width, height;
		float zoomx, zoomy, aspx, aspy;

		ED_space_clip_size(sc, &width, &height);
		ED_space_clip_zoom(sc, ar, &zoomx, &zoomy);
		ED_space_clip_aspect(sc, &aspx, &aspy);

		*scalex = ((float)width * aspx) * zoomx;
		*scaley = ((float)height * aspy) * zoomy;
	}
	else {
		/* possible other spaces from which mask editing is available */
		*scalex = 1.0f;
		*scaley = 1.0f;
	}
}

/********************** registration *********************/

void ED_operatortypes_mask(void)
{
	WM_operatortype_append(MASK_OT_new);

	/* mask layers */
	WM_operatortype_append(MASK_OT_layer_new);
	WM_operatortype_append(MASK_OT_layer_remove);

	/* add */
	WM_operatortype_append(MASK_OT_add_vertex);
	WM_operatortype_append(MASK_OT_add_feather_vertex);

	/* geometry */
	WM_operatortype_append(MASK_OT_switch_direction);
	WM_operatortype_append(MASK_OT_delete);

	/* select */
	WM_operatortype_append(MASK_OT_select);
	WM_operatortype_append(MASK_OT_select_all);
	WM_operatortype_append(MASK_OT_select_border);
	WM_operatortype_append(MASK_OT_select_lasso);
	WM_operatortype_append(MASK_OT_select_circle);
	WM_operatortype_append(MASK_OT_select_linked_pick);
	WM_operatortype_append(MASK_OT_select_linked);

	/* hide/reveal */
	WM_operatortype_append(MASK_OT_hide_view_clear);
	WM_operatortype_append(MASK_OT_hide_view_set);

	/* feather */
	WM_operatortype_append(MASK_OT_feather_weight_clear);

	/* shape */
	WM_operatortype_append(MASK_OT_slide_point);
	WM_operatortype_append(MASK_OT_cyclic_toggle);
	WM_operatortype_append(MASK_OT_handle_type_set);

	/* relationships */
	WM_operatortype_append(MASK_OT_parent_set);
	WM_operatortype_append(MASK_OT_parent_clear);

	/* shapekeys */
	WM_operatortype_append(MASK_OT_shape_key_insert);
	WM_operatortype_append(MASK_OT_shape_key_clear);
}

void ED_keymap_mask(wmKeyConfig *keyconf)
{
	wmKeyMap *keymap;
	wmKeyMapItem *kmi;

	keymap = WM_keymap_find(keyconf, "Mask Editing", 0, 0);
	keymap->poll = ED_maskedit_poll;

	WM_keymap_add_item(keymap, "MASK_OT_new", NKEY, KM_PRESS, KM_ALT, 0);

	/* mask mode supports PET now */
	ED_keymap_proportional_cycle(keyconf, keymap);
	ED_keymap_proportional_maskmode(keyconf, keymap);

	/* geometry */
	WM_keymap_add_item(keymap, "MASK_OT_add_vertex_slide", LEFTMOUSE, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "MASK_OT_add_feather_vertex_slide", LEFTMOUSE, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_add_item(keymap, "MASK_OT_delete", XKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "MASK_OT_delete", DELKEY, KM_PRESS, 0, 0);

	/* selection */
	kmi = WM_keymap_add_item(keymap, "MASK_OT_select", SELECTMOUSE, KM_PRESS, 0, 0);
	RNA_boolean_set(kmi->ptr, "extend", FALSE);
	RNA_boolean_set(kmi->ptr, "deselect", FALSE);
	RNA_boolean_set(kmi->ptr, "toggle", FALSE);
	kmi = WM_keymap_add_item(keymap, "MASK_OT_select", SELECTMOUSE, KM_PRESS, KM_SHIFT, 0);
	RNA_boolean_set(kmi->ptr, "extend", FALSE);
	RNA_boolean_set(kmi->ptr, "deselect", FALSE);
	RNA_boolean_set(kmi->ptr, "toggle", TRUE);

	kmi = WM_keymap_add_item(keymap, "MASK_OT_select_all", AKEY, KM_PRESS, 0, 0);
	RNA_enum_set(kmi->ptr, "action", SEL_TOGGLE);
	kmi = WM_keymap_add_item(keymap, "MASK_OT_select_all", IKEY, KM_PRESS, KM_CTRL, 0);
	RNA_enum_set(kmi->ptr, "action", SEL_INVERT);

	WM_keymap_add_item(keymap, "MASK_OT_select_linked", LKEY, KM_PRESS, KM_CTRL, 0);
	kmi = WM_keymap_add_item(keymap, "MASK_OT_select_linked_pick", LKEY, KM_PRESS, 0, 0);
	RNA_boolean_set(kmi->ptr, "deselect", FALSE);
	kmi = WM_keymap_add_item(keymap, "MASK_OT_select_linked_pick", LKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_boolean_set(kmi->ptr, "deselect", TRUE);

	WM_keymap_add_item(keymap, "MASK_OT_select_border", BKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "MASK_OT_select_circle", CKEY, KM_PRESS, 0, 0);

	kmi = WM_keymap_add_item(keymap, "MASK_OT_select_lasso", EVT_TWEAK_A, KM_ANY, KM_CTRL | KM_ALT, 0);
	RNA_boolean_set(kmi->ptr, "deselect", FALSE);
	kmi = WM_keymap_add_item(keymap, "MASK_OT_select_lasso", EVT_TWEAK_A, KM_ANY, KM_CTRL | KM_SHIFT | KM_ALT, 0);
	RNA_boolean_set(kmi->ptr, "deselect", TRUE);

	/* hide/reveal */
	WM_keymap_add_item(keymap, "MASK_OT_hide_view_clear", HKEY, KM_PRESS, KM_ALT, 0);
	kmi = WM_keymap_add_item(keymap, "MASK_OT_hide_view_set", HKEY, KM_PRESS, 0, 0);
	RNA_boolean_set(kmi->ptr, "unselected", FALSE);

	kmi = WM_keymap_add_item(keymap, "MASK_OT_hide_view_set", HKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_boolean_set(kmi->ptr, "unselected", TRUE);

	/* select clip while in maker view,
	 * this matches View3D functionality where you can select an
	 * object while in editmode to allow vertex parenting */
	kmi = WM_keymap_add_item(keymap, "CLIP_OT_select", SELECTMOUSE, KM_PRESS, KM_CTRL, 0);
	RNA_boolean_set(kmi->ptr, "extend", FALSE);

	/* shape */
	WM_keymap_add_item(keymap, "MASK_OT_cyclic_toggle", CKEY, KM_PRESS, KM_ALT, 0);
	WM_keymap_add_item(keymap, "MASK_OT_slide_point", LEFTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "MASK_OT_handle_type_set", VKEY, KM_PRESS, 0, 0);
	// WM_keymap_add_item(keymap, "MASK_OT_feather_weight_clear", SKEY, KM_PRESS, KM_ALT, 0);
	/* ... matches curve editmode */
	RNA_enum_set(WM_keymap_add_item(keymap, "TRANSFORM_OT_transform", SKEY, KM_PRESS, KM_ALT, 0)->ptr, "mode", TFM_MASK_SHRINKFATTEN);

	/* relationships */
	WM_keymap_add_item(keymap, "MASK_OT_parent_set", PKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "MASK_OT_parent_clear", PKEY, KM_PRESS, KM_ALT, 0);

	WM_keymap_add_item(keymap, "MASK_OT_shape_key_insert", IKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "MASK_OT_shape_key_clear", IKEY, KM_PRESS, KM_ALT, 0);


	transform_keymap_for_space(keyconf, keymap, SPACE_CLIP);
}

void ED_operatormacros_mask(void)
{
	/* XXX: just for sample */
	wmOperatorType *ot;
	wmOperatorTypeMacro *otmacro;

	ot = WM_operatortype_append_macro("MASK_OT_add_vertex_slide", "Add Vertex and Slide", "Add new vertex and slide it", OPTYPE_UNDO | OPTYPE_REGISTER);
	ot->description = "Add new vertex and slide it";
	WM_operatortype_macro_define(ot, "MASK_OT_add_vertex");
	otmacro = WM_operatortype_macro_define(ot, "TRANSFORM_OT_translate");
	RNA_boolean_set(otmacro->ptr, "release_confirm", TRUE);

	ot = WM_operatortype_append_macro("MASK_OT_add_feather_vertex_slide", "Add Feather Vertex and Slide", "Add new vertex to feater and slide it", OPTYPE_UNDO | OPTYPE_REGISTER);
	ot->description = "Add new feather vertex and slide it";
	WM_operatortype_macro_define(ot, "MASK_OT_add_feather_vertex");
	otmacro = WM_operatortype_macro_define(ot, "MASK_OT_slide_point");
	RNA_boolean_set(otmacro->ptr, "slide_feather", TRUE);
}
