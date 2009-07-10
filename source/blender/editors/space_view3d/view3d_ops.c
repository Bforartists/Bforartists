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
#include "ED_transform.h"

#include "view3d_intern.h"


/* ************************** registration **********************************/

void view3d_operatortypes(void)
{
	WM_operatortype_append(VIEW3D_OT_viewrotate);
	WM_operatortype_append(VIEW3D_OT_viewmove);
	WM_operatortype_append(VIEW3D_OT_zoom);
	WM_operatortype_append(VIEW3D_OT_view_all);
	WM_operatortype_append(VIEW3D_OT_viewnumpad);
	WM_operatortype_append(VIEW3D_OT_view_orbit);
	WM_operatortype_append(VIEW3D_OT_view_pan);
	WM_operatortype_append(VIEW3D_OT_view_persportho);
	WM_operatortype_append(VIEW3D_OT_view_center);
	WM_operatortype_append(VIEW3D_OT_select);
	WM_operatortype_append(VIEW3D_OT_select_border);
	WM_operatortype_append(VIEW3D_OT_clip_border);
	WM_operatortype_append(VIEW3D_OT_select_circle);
	WM_operatortype_append(VIEW3D_OT_smoothview);
	WM_operatortype_append(VIEW3D_OT_render_border);
	WM_operatortype_append(VIEW3D_OT_zoom_border);
	WM_operatortype_append(VIEW3D_OT_manipulator);
	WM_operatortype_append(VIEW3D_OT_cursor3d);
	WM_operatortype_append(VIEW3D_OT_select_lasso);
	WM_operatortype_append(VIEW3D_OT_setcameratoview);
	WM_operatortype_append(VIEW3D_OT_drawtype);
	WM_operatortype_append(VIEW3D_OT_localview);
	WM_operatortype_append(VIEW3D_OT_game_start);
	WM_operatortype_append(VIEW3D_OT_layers);
	
	WM_operatortype_append(VIEW3D_OT_properties);
	WM_operatortype_append(VIEW3D_OT_toolbar);
	
	WM_operatortype_append(VIEW3D_OT_snap_selected_to_grid);
	WM_operatortype_append(VIEW3D_OT_snap_selected_to_cursor);
	WM_operatortype_append(VIEW3D_OT_snap_selected_to_center);
	WM_operatortype_append(VIEW3D_OT_snap_cursor_to_grid);
	WM_operatortype_append(VIEW3D_OT_snap_cursor_to_selected);
	WM_operatortype_append(VIEW3D_OT_snap_cursor_to_active);
	WM_operatortype_append(VIEW3D_OT_snap_menu);
		
	transform_operatortypes();
}

void view3d_keymap(wmWindowManager *wm)
{
	ListBase *keymap= WM_keymap_listbase(wm, "View3D Generic", SPACE_VIEW3D, 0);
	wmKeymapItem *km;
	
	WM_keymap_add_item(keymap, "PAINT_OT_vertex_paint_toggle", VKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "PAINT_OT_weight_paint_toggle", TABKEY, KM_PRESS, KM_CTRL, 0);
	
	WM_keymap_add_item(keymap, "VIEW3D_OT_properties", NKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "VIEW3D_OT_toolbar", TKEY, KM_PRESS, 0, 0);
	
	/* only for region 3D window */
	keymap= WM_keymap_listbase(wm, "View3D", SPACE_VIEW3D, 0);
	
	/* paint poll checks mode */
	WM_keymap_verify_item(keymap, "PAINT_OT_vertex_paint", LEFTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "PAINT_OT_weight_paint", LEFTMOUSE, KM_PRESS, 0, 0);

	WM_keymap_add_item(keymap, "PAINT_OT_image_paint", LEFTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "PAINT_OT_sample_color", RIGHTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "PAINT_OT_clone_cursor_set", LEFTMOUSE, KM_PRESS, KM_CTRL, 0);

	WM_keymap_add_item(keymap, "SCULPT_OT_brush_stroke", LEFTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "SCULPT_OT_brush_stroke", LEFTMOUSE, KM_PRESS, KM_SHIFT, 0);

	/* sketch poll checks mode */	
	WM_keymap_add_item(keymap, "SKETCH_OT_gesture", ACTIONMOUSE, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_add_item(keymap, "SKETCH_OT_draw_stroke", ACTIONMOUSE, KM_PRESS, 0, 0);
	km = WM_keymap_add_item(keymap, "SKETCH_OT_draw_stroke", ACTIONMOUSE, KM_PRESS, KM_CTRL, 0);
	RNA_boolean_set(km->ptr, "snap", 1);
	WM_keymap_add_item(keymap, "SKETCH_OT_draw_preview", MOUSEMOVE, KM_ANY, 0, 0);
	km = WM_keymap_add_item(keymap, "SKETCH_OT_draw_preview", MOUSEMOVE, KM_ANY, KM_CTRL, 0);
	RNA_boolean_set(km->ptr, "snap", 1);

	WM_keymap_verify_item(keymap, "VIEW3D_OT_manipulator", ACTIONMOUSE, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "VIEW3D_OT_cursor3d", ACTIONMOUSE, KM_PRESS, 0, 0);
	
	WM_keymap_verify_item(keymap, "VIEW3D_OT_viewrotate", MIDDLEMOUSE, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "VIEW3D_OT_viewmove", MIDDLEMOUSE, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_verify_item(keymap, "VIEW3D_OT_zoom", MIDDLEMOUSE, KM_PRESS, KM_CTRL, 0);
	WM_keymap_verify_item(keymap, "VIEW3D_OT_view_center", PADPERIOD, KM_PRESS, 0, 0);
	
	WM_keymap_verify_item(keymap, "VIEW3D_OT_smoothview", TIMER1, KM_ANY, KM_ANY, 0);
	
	RNA_int_set(WM_keymap_add_item(keymap, "VIEW3D_OT_zoom", PADPLUSKEY, KM_PRESS, 0, 0)->ptr, "delta", 1);
	RNA_int_set(WM_keymap_add_item(keymap, "VIEW3D_OT_zoom", PADMINUS, KM_PRESS, 0, 0)->ptr, "delta", -1);
	RNA_int_set(WM_keymap_add_item(keymap, "VIEW3D_OT_zoom", WHEELINMOUSE, KM_PRESS, 0, 0)->ptr, "delta", 1);
	RNA_int_set(WM_keymap_add_item(keymap, "VIEW3D_OT_zoom", WHEELOUTMOUSE, KM_PRESS, 0, 0)->ptr, "delta", -1);

	RNA_boolean_set(WM_keymap_add_item(keymap, "VIEW3D_OT_view_all", HOMEKEY, KM_PRESS, 0, 0)->ptr, "center", 0);
	RNA_boolean_set(WM_keymap_add_item(keymap, "VIEW3D_OT_view_all", CKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "center", 1);

	/* numpad view hotkeys*/
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_viewnumpad", PAD0, KM_PRESS, 0, 0)->ptr, "type", V3D_VIEW_CAMERA);
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_viewnumpad", PAD1, KM_PRESS, 0, 0)->ptr, "type", V3D_VIEW_FRONT);
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_view_orbit", PAD2, KM_PRESS, 0, 0)->ptr, "type", V3D_VIEW_STEPDOWN);
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_viewnumpad", PAD3, KM_PRESS, 0, 0)->ptr, "type", V3D_VIEW_RIGHT);
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_view_orbit", PAD4, KM_PRESS, 0, 0)->ptr, "type", V3D_VIEW_STEPLEFT);
	WM_keymap_add_item(keymap, "VIEW3D_OT_view_persportho", PAD5, KM_PRESS, 0, 0);
	
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_view_orbit", PAD6, KM_PRESS, 0, 0)->ptr, "type", V3D_VIEW_STEPRIGHT);
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_viewnumpad", PAD7, KM_PRESS, 0, 0)->ptr, "type", V3D_VIEW_TOP);
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_view_orbit", PAD8, KM_PRESS, 0, 0)->ptr, "type", V3D_VIEW_STEPUP);
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_viewnumpad", PAD1, KM_PRESS, KM_CTRL, 0)->ptr, "type", V3D_VIEW_BACK);
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_viewnumpad", PAD3, KM_PRESS, KM_CTRL, 0)->ptr, "type", V3D_VIEW_LEFT);
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_viewnumpad", PAD7, KM_PRESS, KM_CTRL, 0)->ptr, "type", V3D_VIEW_BOTTOM);
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_view_pan", PAD2, KM_PRESS, KM_CTRL, 0)->ptr, "type", V3D_VIEW_PANDOWN);
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_view_pan", PAD4, KM_PRESS, KM_CTRL, 0)->ptr, "type", V3D_VIEW_PANLEFT);
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_view_pan", PAD6, KM_PRESS, KM_CTRL, 0)->ptr, "type", V3D_VIEW_PANRIGHT);
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_view_pan", PAD8, KM_PRESS, KM_CTRL, 0)->ptr, "type", V3D_VIEW_PANUP);

	WM_keymap_add_item(keymap, "VIEW3D_OT_localview", PADSLASHKEY, KM_PRESS, 0, 0);
	
	WM_keymap_add_item(keymap, "VIEW3D_OT_game_start", PKEY, KM_PRESS, 0, 0);
	
	/* layers, shift + alt are properties set in invoke() */
	RNA_int_set(WM_keymap_add_item(keymap, "VIEW3D_OT_layers", ONEKEY, KM_PRESS, KM_ANY, 0)->ptr, "nr", 1);
	RNA_int_set(WM_keymap_add_item(keymap, "VIEW3D_OT_layers", TWOKEY, KM_PRESS, KM_ANY, 0)->ptr, "nr", 2);
	RNA_int_set(WM_keymap_add_item(keymap, "VIEW3D_OT_layers", THREEKEY, KM_PRESS, KM_ANY, 0)->ptr, "nr", 3);
	RNA_int_set(WM_keymap_add_item(keymap, "VIEW3D_OT_layers", FOURKEY, KM_PRESS, KM_ANY, 0)->ptr, "nr", 4);
	RNA_int_set(WM_keymap_add_item(keymap, "VIEW3D_OT_layers", FIVEKEY, KM_PRESS, KM_ANY, 0)->ptr, "nr", 5);
	RNA_int_set(WM_keymap_add_item(keymap, "VIEW3D_OT_layers", SIXKEY, KM_PRESS, KM_ANY, 0)->ptr, "nr", 6);
	RNA_int_set(WM_keymap_add_item(keymap, "VIEW3D_OT_layers", SEVENKEY, KM_PRESS, KM_ANY, 0)->ptr, "nr", 7);
	RNA_int_set(WM_keymap_add_item(keymap, "VIEW3D_OT_layers", EIGHTKEY, KM_PRESS, KM_ANY, 0)->ptr, "nr", 8);
	RNA_int_set(WM_keymap_add_item(keymap, "VIEW3D_OT_layers", NINEKEY, KM_PRESS, KM_ANY, 0)->ptr, "nr", 9);
	RNA_int_set(WM_keymap_add_item(keymap, "VIEW3D_OT_layers", ZEROKEY, KM_PRESS, KM_ANY, 0)->ptr, "nr", 10);
	
	/* drawtype */
	km = WM_keymap_add_item(keymap, "VIEW3D_OT_drawtype", ZKEY, KM_PRESS, 0, 0);
	RNA_int_set(km->ptr, "draw_type", OB_SOLID);
	RNA_int_set(km->ptr, "draw_type_alternate", OB_WIRE);

	km = WM_keymap_add_item(keymap, "VIEW3D_OT_drawtype", ZKEY, KM_PRESS, KM_ALT, 0);
	RNA_int_set(km->ptr, "draw_type", OB_TEXTURE);
	RNA_int_set(km->ptr, "draw_type_alternate", OB_SOLID);

	km = WM_keymap_add_item(keymap, "VIEW3D_OT_drawtype", ZKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_int_set(km->ptr, "draw_type", OB_SHADED);
	RNA_int_set(km->ptr, "draw_type_alternate", OB_WIRE);

	/* selection*/
	WM_keymap_add_item(keymap, "VIEW3D_OT_select", SELECTMOUSE, KM_PRESS, 0, 0);
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_select", SELECTMOUSE, KM_PRESS, KM_SHIFT, 0)->ptr, "type", 1);
	WM_keymap_add_item(keymap, "VIEW3D_OT_select_border", BKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "VIEW3D_OT_select_lasso", EVT_TWEAK_A, KM_ANY, KM_CTRL, 0);
	RNA_enum_set(WM_keymap_add_item(keymap, "VIEW3D_OT_select_lasso", EVT_TWEAK_A, KM_ANY, KM_SHIFT|KM_CTRL, 0)->ptr, "type", 1);
	WM_keymap_add_item(keymap, "VIEW3D_OT_select_circle", CKEY, KM_PRESS, 0, 0);
	
	WM_keymap_add_item(keymap, "VIEW3D_OT_clip_border", BKEY, KM_PRESS, KM_ALT, 0);
	WM_keymap_add_item(keymap, "VIEW3D_OT_zoom_border", BKEY, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_add_item(keymap, "VIEW3D_OT_render_border", BKEY, KM_PRESS, KM_SHIFT, 0);
	
	WM_keymap_add_item(keymap, "VIEW3D_OT_camera_to_view", PAD0, KM_PRESS, KM_ALT|KM_CTRL, 0);
	
	WM_keymap_add_item(keymap, "VIEW3D_OT_snap_menu", SKEY, KM_PRESS, KM_SHIFT, 0);
	
	/* radial control */
	RNA_enum_set(WM_keymap_add_item(keymap, "SCULPT_OT_radial_control", FKEY, KM_PRESS, 0, 0)->ptr, "mode", WM_RADIALCONTROL_SIZE);
	RNA_enum_set(WM_keymap_add_item(keymap, "SCULPT_OT_radial_control", FKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "mode", WM_RADIALCONTROL_STRENGTH);
	RNA_enum_set(WM_keymap_add_item(keymap, "SCULPT_OT_radial_control", FKEY, KM_PRESS, KM_CTRL, 0)->ptr, "mode", WM_RADIALCONTROL_ANGLE);

	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_vertex_paint_radial_control", FKEY, KM_PRESS, 0, 0)->ptr, "mode", WM_RADIALCONTROL_SIZE);
	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_weight_paint_radial_control", FKEY, KM_PRESS, 0, 0)->ptr, "mode", WM_RADIALCONTROL_SIZE);
	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_texture_paint_radial_control", FKEY, KM_PRESS, 0, 0)->ptr, "mode", WM_RADIALCONTROL_SIZE);
	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_vertex_paint_radial_control", FKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "mode", WM_RADIALCONTROL_STRENGTH);
	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_weight_paint_radial_control", FKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "mode", WM_RADIALCONTROL_STRENGTH);
	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_texture_paint_radial_control", FKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "mode", WM_RADIALCONTROL_STRENGTH);

	transform_keymap_for_space(wm, keymap, SPACE_VIEW3D);

}

