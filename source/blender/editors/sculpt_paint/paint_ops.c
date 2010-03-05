/**
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
 * ***** END GPL LICENSE BLOCK *****
 */

#include "DNA_brush_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BKE_brush.h"
#include "BKE_context.h"
#include "BKE_paint.h"

#include "ED_sculpt.h"
#include "ED_screen.h"
#include "UI_resources.h"

#include "WM_api.h"
#include "WM_types.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "paint_intern.h"
#include "sculpt_intern.h"

#include <string.h>

/* Brush operators */
static int brush_add_exec(bContext *C, wmOperator *op)
{
	/*int type = RNA_enum_get(op->ptr, "type");*/
	Brush *br = NULL;

	br = add_brush("Brush");

	if(br)
		paint_brush_set(paint_get_active(CTX_data_scene(C)), br);

	return OPERATOR_FINISHED;
}

static EnumPropertyItem brush_type_items[] = {
	{OB_MODE_SCULPT, "SCULPT", ICON_SCULPTMODE_HLT, "Sculpt", ""},
	{OB_MODE_VERTEX_PAINT, "VERTEX_PAINT", ICON_VPAINT_HLT, "Vertex Paint", ""},
	{OB_MODE_WEIGHT_PAINT, "WEIGHT_PAINT", ICON_WPAINT_HLT, "Weight Paint", ""},
	{OB_MODE_TEXTURE_PAINT, "TEXTURE_PAINT", ICON_TPAINT_HLT, "Texture Paint", ""},
	{0, NULL, 0, NULL, NULL}};

void BRUSH_OT_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Brush";
    ot->description= "Add brush by mode type";
	ot->idname= "BRUSH_OT_add";
	
	/* api callbacks */
	ot->exec= brush_add_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	RNA_def_enum(ot->srna, "type", brush_type_items, OB_MODE_VERTEX_PAINT, "Type", "Which paint mode to create the brush for.");
}

static int vertex_color_set_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *obact = CTX_data_active_object(C);
	unsigned int paintcol = vpaint_get_current_col(scene->toolsettings->vpaint);
	vpaint_fill(obact, paintcol);
	
	ED_region_tag_redraw(CTX_wm_region(C)); // XXX - should redraw all 3D views
	return OPERATOR_FINISHED;
}

void PAINT_OT_vertex_color_set(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Set Vertex Colors";
	ot->idname= "PAINT_OT_vertex_color_set";
	
	/* api callbacks */
	ot->exec= vertex_color_set_exec;
	ot->poll= vertex_paint_mode_poll;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/**************************** registration **********************************/

void ED_operatortypes_paint(void)
{
	/* brush */
	WM_operatortype_append(BRUSH_OT_add);
	WM_operatortype_append(BRUSH_OT_curve_preset);

	/* image */
	WM_operatortype_append(PAINT_OT_texture_paint_toggle);
	WM_operatortype_append(PAINT_OT_texture_paint_radial_control);
	WM_operatortype_append(PAINT_OT_image_paint);
	WM_operatortype_append(PAINT_OT_image_paint_radial_control);
	WM_operatortype_append(PAINT_OT_sample_color);
	WM_operatortype_append(PAINT_OT_grab_clone);
	WM_operatortype_append(PAINT_OT_clone_cursor_set);
	WM_operatortype_append(PAINT_OT_camera_project);

	/* weight */
	WM_operatortype_append(PAINT_OT_weight_paint_toggle);
	WM_operatortype_append(PAINT_OT_weight_paint_radial_control);
	WM_operatortype_append(PAINT_OT_weight_paint);
	WM_operatortype_append(PAINT_OT_weight_set);
	WM_operatortype_append(PAINT_OT_weight_from_bones);

	/* vertex */
	WM_operatortype_append(PAINT_OT_vertex_paint_radial_control);
	WM_operatortype_append(PAINT_OT_vertex_paint_toggle);
	WM_operatortype_append(PAINT_OT_vertex_paint);
	WM_operatortype_append(PAINT_OT_vertex_color_set);

	/* face-select */
	WM_operatortype_append(PAINT_OT_face_select_linked);
	WM_operatortype_append(PAINT_OT_face_select_linked_pick);
	WM_operatortype_append(PAINT_OT_face_select_all);
}

static void ed_keymap_paint_brush_switch(wmKeyMap *keymap, const char *path)
{
	wmKeyMapItem *kmi;

	kmi= WM_keymap_add_item(keymap, "WM_OT_context_set_int", ONEKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", path);
	RNA_int_set(kmi->ptr, "value", 0);
	kmi= WM_keymap_add_item(keymap, "WM_OT_context_set_int", TWOKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", path);
	RNA_int_set(kmi->ptr, "value", 1);
	kmi= WM_keymap_add_item(keymap, "WM_OT_context_set_int", THREEKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", path);
	RNA_int_set(kmi->ptr, "value", 2);
	kmi= WM_keymap_add_item(keymap, "WM_OT_context_set_int", FOURKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", path);
	RNA_int_set(kmi->ptr, "value", 3);
	kmi= WM_keymap_add_item(keymap, "WM_OT_context_set_int", FIVEKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", path);
	RNA_int_set(kmi->ptr, "value", 4);
	kmi= WM_keymap_add_item(keymap, "WM_OT_context_set_int", SIXKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", path);
	RNA_int_set(kmi->ptr, "value", 5);
	kmi= WM_keymap_add_item(keymap, "WM_OT_context_set_int", SEVENKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", path);
	RNA_int_set(kmi->ptr, "value", 6);
	kmi= WM_keymap_add_item(keymap, "WM_OT_context_set_int", EIGHTKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", path);
	RNA_int_set(kmi->ptr, "value", 7);
	kmi= WM_keymap_add_item(keymap, "WM_OT_context_set_int", NINEKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", path);
	RNA_int_set(kmi->ptr, "value", 8);
	kmi= WM_keymap_add_item(keymap, "WM_OT_context_set_int", ZEROKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", path);
	RNA_int_set(kmi->ptr, "value", 9);
}

static void ed_keymap_paint_brush_size(wmKeyMap *keymap, const char *path)
{
	wmKeyMapItem *kmi;
	
	kmi= WM_keymap_add_item(keymap, "WM_OT_context_set_int", LEFTBRACKETKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", path);
	RNA_int_set(kmi->ptr, "value", -20);
	RNA_boolean_set(kmi->ptr, "relative", 1);
	
	kmi= WM_keymap_add_item(keymap, "WM_OT_context_set_int", RIGHTBRACKETKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", path);
	RNA_int_set(kmi->ptr, "value", 20);
	RNA_boolean_set(kmi->ptr, "relative", 1);
}	

void ED_keymap_paint(wmKeyConfig *keyconf)
{
	wmKeyMap *keymap;
	wmKeyMapItem *kmi;
	int i;
	
	/* Sculpt mode */
	keymap= WM_keymap_find(keyconf, "Sculpt", 0, 0);
	keymap->poll= sculpt_poll;

	RNA_enum_set(WM_keymap_add_item(keymap, "SCULPT_OT_radial_control", FKEY, KM_PRESS, 0, 0)->ptr, "mode", WM_RADIALCONTROL_SIZE);
	RNA_enum_set(WM_keymap_add_item(keymap, "SCULPT_OT_radial_control", FKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "mode", WM_RADIALCONTROL_STRENGTH);
	RNA_enum_set(WM_keymap_add_item(keymap, "SCULPT_OT_radial_control", FKEY, KM_PRESS, KM_CTRL, 0)->ptr, "mode", WM_RADIALCONTROL_ANGLE);

	WM_keymap_add_item(keymap, "SCULPT_OT_brush_stroke", LEFTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "SCULPT_OT_brush_stroke", LEFTMOUSE, KM_PRESS, KM_SHIFT, 0);

	for(i=0; i<=5; i++)
		RNA_int_set(WM_keymap_add_item(keymap, "OBJECT_OT_subdivision_set", ZEROKEY+i, KM_PRESS, KM_CTRL, 0)->ptr, "level", i);

	/* multires switch */
	kmi= WM_keymap_add_item(keymap, "OBJECT_OT_subdivision_set", PAGEUPKEY, KM_PRESS, 0, 0);
	RNA_int_set(kmi->ptr, "level", 1);
	RNA_boolean_set(kmi->ptr, "relative", 1);

	kmi= WM_keymap_add_item(keymap, "OBJECT_OT_subdivision_set", PAGEDOWNKEY, KM_PRESS, 0, 0);
	RNA_int_set(kmi->ptr, "level", -1);
	RNA_boolean_set(kmi->ptr, "relative", 1);

	ed_keymap_paint_brush_switch(keymap, "tool_settings.sculpt.active_brush_index");
	ed_keymap_paint_brush_size(keymap, "tool_settings.sculpt.brush.size");
	
	kmi = WM_keymap_add_item(keymap, "WM_OT_context_toggle", AKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", "tool_settings.sculpt.brush.use_anchor");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_toggle", SKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "path", "tool_settings.sculpt.brush.use_smooth_stroke");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_toggle", RKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", "tool_settings.sculpt.brush.use_rake");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_toggle", AKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "path", "tool_settings.sculpt.brush.use_airbrush");

	/* brush switching */
	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", DKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", "tool_settings.sculpt.active_brush_name");
	RNA_string_set(kmi->ptr, "value", "Draw");
	
	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", SKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", "tool_settings.sculpt.active_brush_name");
	RNA_string_set(kmi->ptr, "value", "Smooth");
	
	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", PKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", "tool_settings.sculpt.active_brush_name");
	RNA_string_set(kmi->ptr, "value", "Pinch");
	
	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", GKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", "tool_settings.sculpt.active_brush_name");
	RNA_string_set(kmi->ptr, "value", "Grab");
	
	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", LKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "path", "tool_settings.sculpt.active_brush_name");
	RNA_string_set(kmi->ptr, "value", "Layer");
	
	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", TKEY, KM_PRESS, KM_SHIFT, 0); // was just T in 2.4x
	RNA_string_set(kmi->ptr, "path", "tool_settings.sculpt.active_brush_name");
	RNA_string_set(kmi->ptr, "value", "Flatten");
	

	/* Vertex Paint mode */
	keymap= WM_keymap_find(keyconf, "Vertex Paint", 0, 0);
	keymap->poll= vertex_paint_mode_poll;

	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_vertex_paint_radial_control", FKEY, KM_PRESS, 0, 0)->ptr, "mode", WM_RADIALCONTROL_SIZE);
	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_vertex_paint_radial_control", FKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "mode", WM_RADIALCONTROL_STRENGTH);
	WM_keymap_verify_item(keymap, "PAINT_OT_vertex_paint", LEFTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "PAINT_OT_sample_color", RIGHTMOUSE, KM_PRESS, 0, 0);

	WM_keymap_add_item(keymap,
			"PAINT_OT_vertex_color_set",KKEY, KM_PRESS, KM_SHIFT, 0);

	ed_keymap_paint_brush_switch(keymap, "tool_settings.vertex_paint.active_brush_index");
	ed_keymap_paint_brush_size(keymap, "tool_settings.vertex_paint.brush.size");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_toggle", MKEY, KM_PRESS, 0, 0); /* mask toggle */
	RNA_string_set(kmi->ptr, "path", "vertex_paint_object.data.use_paint_mask");

	/* Weight Paint mode */
	keymap= WM_keymap_find(keyconf, "Weight Paint", 0, 0);
	keymap->poll= weight_paint_mode_poll;

	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_weight_paint_radial_control", FKEY, KM_PRESS, 0, 0)->ptr, "mode", WM_RADIALCONTROL_SIZE);
	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_weight_paint_radial_control", FKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "mode", WM_RADIALCONTROL_STRENGTH);

	WM_keymap_verify_item(keymap, "PAINT_OT_weight_paint", LEFTMOUSE, KM_PRESS, 0, 0);

	WM_keymap_add_item(keymap,
			"PAINT_OT_weight_set", KKEY, KM_PRESS, KM_SHIFT, 0);

	ed_keymap_paint_brush_switch(keymap, "tool_settings.weight_paint.active_brush_index");
	ed_keymap_paint_brush_size(keymap, "tool_settings.weight_paint.brush.size");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_toggle", MKEY, KM_PRESS, 0, 0); /* mask toggle */
	RNA_string_set(kmi->ptr, "path", "weight_paint_object.data.use_paint_mask");

	WM_keymap_verify_item(keymap, "PAINT_OT_weight_from_bones", WKEY, KM_PRESS, 0, 0);

	/* Image/Texture Paint mode */
	keymap= WM_keymap_find(keyconf, "Image Paint", 0, 0);
	keymap->poll= image_texture_paint_poll;

	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_texture_paint_radial_control", FKEY, KM_PRESS, 0, 0)->ptr, "mode", WM_RADIALCONTROL_SIZE);
	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_texture_paint_radial_control", FKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "mode", WM_RADIALCONTROL_STRENGTH);

	WM_keymap_add_item(keymap, "PAINT_OT_image_paint", LEFTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "PAINT_OT_grab_clone", RIGHTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "PAINT_OT_sample_color", RIGHTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "PAINT_OT_clone_cursor_set", LEFTMOUSE, KM_PRESS, KM_CTRL, 0);

	ed_keymap_paint_brush_switch(keymap, "tool_settings.image_paint.active_brush_index");
	ed_keymap_paint_brush_size(keymap, "tool_settings.image_paint.brush.size");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_toggle", MKEY, KM_PRESS, 0, 0); /* mask toggle */
	RNA_string_set(kmi->ptr, "path", "texture_paint_object.data.use_paint_mask");

	/* face-mask mode */
	keymap= WM_keymap_find(keyconf, "Face Mask", 0, 0);
	keymap->poll= facemask_paint_poll;

	WM_keymap_add_item(keymap, "PAINT_OT_face_select_all", AKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "PAINT_OT_face_select_linked", LKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "PAINT_OT_face_select_linked_pick", LKEY, KM_PRESS, 0, 0);

}
