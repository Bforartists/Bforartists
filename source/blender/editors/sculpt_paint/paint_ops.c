/*
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

/** \file blender/editors/sculpt_paint/paint_ops.c
 *  \ingroup edsculpt
 */


#include "BLI_utildefines.h"

#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_brush_types.h"

#include "BKE_brush.h"
#include "BKE_context.h"
#include "BKE_paint.h"
#include "BKE_main.h"

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
//#include <stdio.h>
#include <stddef.h>

/* Brush operators */
static int brush_add_exec(bContext *C, wmOperator *UNUSED(op))
{
	/*int type = RNA_enum_get(op->ptr, "type");*/
	Paint *paint = paint_get_active(CTX_data_scene(C));
	struct Brush *br = paint_brush(paint);

	if (br)
		br = copy_brush(br);
	else
		br = add_brush("Brush");

	paint_brush_set(paint_get_active(CTX_data_scene(C)), br);

	return OPERATOR_FINISHED;
}

static void BRUSH_OT_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Brush";
	ot->description= "Add brush by mode type";
	ot->idname= "BRUSH_OT_add";
	
	/* api callbacks */
	ot->exec= brush_add_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}


static int brush_scale_size_exec(bContext *C, wmOperator *op)
{
	Paint  *paint=  paint_get_active(CTX_data_scene(C));
	struct Brush  *brush=  paint_brush(paint);
	// Object *ob=     CTX_data_active_object(C);
	float   scalar= RNA_float_get(op->ptr, "scalar");

	if (brush) {
		// pixel radius
		{
			const int old_size= brush_size(brush);
			int size= (int)(scalar*old_size);

			if (old_size == size) {
				if (scalar > 1) {
					size++;
				}
				else if (scalar < 1) {
					size--;
				}
			}
			CLAMP(size, 1, 2000); // XXX magic number

			brush_set_size(brush, size);
		}

		// unprojected radius
		{
			float unprojected_radius= scalar*brush_unprojected_radius(brush);

			if (unprojected_radius < 0.001f) // XXX magic number
				unprojected_radius= 0.001f;

			brush_set_unprojected_radius(brush, unprojected_radius);
		}
	}

	return OPERATOR_FINISHED;
}

static void BRUSH_OT_scale_size(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Scale Sculpt/Paint Brush Size";
	ot->description= "Change brush size by a scalar";
	ot->idname= "BRUSH_OT_scale_size";
	
	/* api callbacks */
	ot->exec= brush_scale_size_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	RNA_def_float(ot->srna, "scalar", 1, 0, 2, "Scalar", "Factor to scale brush size by", 0, 2);
}

static int vertex_color_set_exec(bContext *C, wmOperator *UNUSED(op))
{
	Scene *scene = CTX_data_scene(C);
	Object *obact = CTX_data_active_object(C);
	unsigned int paintcol = vpaint_get_current_col(scene->toolsettings->vpaint);
	vpaint_fill(obact, paintcol);
	
	ED_region_tag_redraw(CTX_wm_region(C)); // XXX - should redraw all 3D views
	return OPERATOR_FINISHED;
}

static void PAINT_OT_vertex_color_set(wmOperatorType *ot)
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

static int brush_reset_exec(bContext *C, wmOperator *UNUSED(op))
{
	Paint *paint = paint_get_active(CTX_data_scene(C));
	struct Brush *brush = paint_brush(paint);
	Object *ob = CTX_data_active_object(C);

	if(!ob) return OPERATOR_CANCELLED;

	if(ob->mode & OB_MODE_SCULPT)
		brush_reset_sculpt(brush);
	/* TODO: other modes */

	return OPERATOR_FINISHED;
}

static void BRUSH_OT_reset(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Reset Brush";
	ot->description= "Return brush to defaults based on current tool";
	ot->idname= "BRUSH_OT_reset";
	
	/* api callbacks */
	ot->exec= brush_reset_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/* generic functions for setting the active brush based on the tool */
static Brush *brush_tool_cycle(Main *bmain, Brush *brush_orig, const int tool, const size_t tool_offset, const int ob_mode)
{
	struct Brush *brush;

	if(!brush_orig && !(brush_orig= bmain->brush.first)) {
		return NULL;
	}

	/* get the next brush with the active tool */
	for(	brush= brush_orig->id.next ? brush_orig->id.next : bmain->brush.first;
			brush != brush_orig;
			brush= brush->id.next ? brush->id.next : bmain->brush.first)
	{
		if(	(brush->ob_mode & ob_mode) &&
			(*(((char *)brush) + tool_offset) == tool)
		) {
			return brush;
		}
	}

	return NULL;

}

static int brush_generic_tool_set(Main *bmain, Paint *paint, const int tool, const size_t tool_offset, const int ob_mode)
{
	struct Brush *brush, *brush_orig= paint_brush(paint);

	brush= brush_tool_cycle(bmain, brush_orig, tool, tool_offset, ob_mode);

	if(brush) {
		paint_brush_set(paint, brush);
		WM_main_add_notifier(NC_BRUSH|NA_EDITED, brush);
		return OPERATOR_FINISHED;
	}
	else {
		return OPERATOR_CANCELLED;
	}
}

static int brush_sculpt_tool_set_exec(bContext *C, wmOperator *op)
{
	Main *bmain= CTX_data_main(C);
	Scene *scene= CTX_data_scene(C);

	return brush_generic_tool_set(bmain, &scene->toolsettings->sculpt->paint, RNA_enum_get(op->ptr, "tool"), offsetof(Brush, sculpt_tool), OB_MODE_SCULPT);
}

static void BRUSH_OT_sculpt_tool_set(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Sculpt Tool Set";
	ot->description= "Set the sculpt tool";
	ot->idname= "BRUSH_OT_sculpt_tool_set";

	/* api callbacks */
	ot->exec= brush_sculpt_tool_set_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* props */
	ot->prop= RNA_def_enum(ot->srna, "tool", brush_sculpt_tool_items, 0, "Tool", "");
}

static int brush_vertex_tool_set_exec(bContext *C, wmOperator *op)
{
	Main *bmain= CTX_data_main(C);
	Scene *scene= CTX_data_scene(C);

	return brush_generic_tool_set(bmain, &scene->toolsettings->vpaint->paint, RNA_enum_get(op->ptr, "tool"), offsetof(Brush, vertexpaint_tool), OB_MODE_VERTEX_PAINT);
}

static void BRUSH_OT_vertex_tool_set(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Vertex Paint Tool Set";
	ot->description= "Set the vertex paint tool";
	ot->idname= "BRUSH_OT_vertex_tool_set";

	/* api callbacks */
	ot->exec= brush_vertex_tool_set_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* props */
	ot->prop= RNA_def_enum(ot->srna, "tool", brush_vertex_tool_items, 0, "Tool", "");
}

static int brush_weight_tool_set_exec(bContext *C, wmOperator *op)
{
	Main *bmain= CTX_data_main(C);
	Scene *scene= CTX_data_scene(C);
	/* vertexpaint_tool is used for weight paint mode */
	return brush_generic_tool_set(bmain, &scene->toolsettings->wpaint->paint, RNA_enum_get(op->ptr, "tool"), offsetof(Brush, vertexpaint_tool), OB_MODE_WEIGHT_PAINT);
}

static void BRUSH_OT_weight_tool_set(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Weight Paint Tool Set";
	ot->description= "Set the weight paint tool";
	ot->idname= "BRUSH_OT_weight_tool_set";

	/* api callbacks */
	ot->exec= brush_weight_tool_set_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* props */
	ot->prop= RNA_def_enum(ot->srna, "tool", brush_vertex_tool_items, 0, "Tool", "");
}

static int brush_image_tool_set_exec(bContext *C, wmOperator *op)
{
	Main *bmain= CTX_data_main(C);
	Scene *scene= CTX_data_scene(C);

	return brush_generic_tool_set(bmain, &scene->toolsettings->imapaint.paint, RNA_enum_get(op->ptr, "tool"), offsetof(Brush, imagepaint_tool), OB_MODE_TEXTURE_PAINT);
}

static void BRUSH_OT_image_tool_set(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Image Paint Tool Set";
	ot->description= "Set the image tool";
	ot->idname= "BRUSH_OT_image_tool_set";

	/* api callbacks */
	ot->exec= brush_image_tool_set_exec;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* props */
	ot->prop= RNA_def_enum(ot->srna, "tool", brush_image_tool_items, 0, "Tool", "");
}


/**************************** registration **********************************/

void ED_operatortypes_paint(void)
{
	/* brush */
	WM_operatortype_append(BRUSH_OT_add);
	WM_operatortype_append(BRUSH_OT_scale_size);
	WM_operatortype_append(BRUSH_OT_curve_preset);
	WM_operatortype_append(BRUSH_OT_reset);

	/* note, particle uses a different system, can be added with existing operators in wm.py */
	WM_operatortype_append(BRUSH_OT_sculpt_tool_set);
	WM_operatortype_append(BRUSH_OT_vertex_tool_set);
	WM_operatortype_append(BRUSH_OT_weight_tool_set);
	WM_operatortype_append(BRUSH_OT_image_tool_set);

	/* image */
	WM_operatortype_append(PAINT_OT_texture_paint_toggle);
	WM_operatortype_append(PAINT_OT_texture_paint_radial_control);
	WM_operatortype_append(PAINT_OT_image_paint);
	WM_operatortype_append(PAINT_OT_image_paint_radial_control);
	WM_operatortype_append(PAINT_OT_sample_color);
	WM_operatortype_append(PAINT_OT_grab_clone);
	WM_operatortype_append(PAINT_OT_clone_cursor_set);
	WM_operatortype_append(PAINT_OT_project_image);
	WM_operatortype_append(PAINT_OT_image_from_view);

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
	WM_operatortype_append(PAINT_OT_face_select_inverse);
	WM_operatortype_append(PAINT_OT_face_select_hide);
	WM_operatortype_append(PAINT_OT_face_select_reveal);
}


static void ed_keymap_paint_brush_switch(wmKeyMap *keymap, const char *mode)
{
	wmKeyMapItem *kmi;

	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", ONEKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 0);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", TWOKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 1);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", THREEKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 2);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", FOURKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 3);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", FIVEKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 4);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", SIXKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 5);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", SEVENKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 6);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", EIGHTKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 7);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", NINEKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 8);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", ZEROKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 9);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", ONEKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 10);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", TWOKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 11);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", THREEKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 12);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", FOURKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 13);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", FIVEKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 14);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", SIXKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 15);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", SEVENKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 16);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", EIGHTKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 17);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", NINEKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 18);
	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_active_index_set", ZEROKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "mode", mode);
	RNA_int_set(kmi->ptr, "index", 19);
}

static void ed_keymap_paint_brush_size(wmKeyMap *keymap, const char *UNUSED(path))
{
	wmKeyMapItem *kmi;

	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_scale_size", LEFTBRACKETKEY, KM_PRESS, 0, 0);
	RNA_float_set(kmi->ptr, "scalar", 0.9);

	kmi= WM_keymap_add_item(keymap, "BRUSH_OT_scale_size", RIGHTBRACKETKEY, KM_PRESS, 0, 0);
	RNA_float_set(kmi->ptr, "scalar", 10.0/9.0); // 1.1111....
}

void ED_keymap_paint(wmKeyConfig *keyconf)
{
	wmKeyMap *keymap;
	wmKeyMapItem *kmi;
	int i;
	
	/* Sculpt mode */
	keymap= WM_keymap_find(keyconf, "Sculpt", 0, 0);
	keymap->poll= sculpt_poll;

	RNA_enum_set(WM_keymap_add_item(keymap, "SCULPT_OT_radial_control", FKEY, KM_PRESS, 0, 0)->ptr,        "mode", WM_RADIALCONTROL_SIZE);
	RNA_enum_set(WM_keymap_add_item(keymap, "SCULPT_OT_radial_control", FKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "mode", WM_RADIALCONTROL_STRENGTH);
	RNA_enum_set(WM_keymap_add_item(keymap, "SCULPT_OT_radial_control", FKEY, KM_PRESS, KM_CTRL, 0)->ptr,  "mode", WM_RADIALCONTROL_ANGLE);

	RNA_enum_set(WM_keymap_add_item(keymap, "SCULPT_OT_brush_stroke", LEFTMOUSE, KM_PRESS, 0,        0)->ptr, "mode", BRUSH_STROKE_NORMAL);
	RNA_enum_set(WM_keymap_add_item(keymap, "SCULPT_OT_brush_stroke", LEFTMOUSE, KM_PRESS, KM_CTRL,  0)->ptr, "mode", BRUSH_STROKE_INVERT);
	RNA_enum_set(WM_keymap_add_item(keymap, "SCULPT_OT_brush_stroke", LEFTMOUSE, KM_PRESS, KM_SHIFT, 0)->ptr, "mode", BRUSH_STROKE_SMOOTH);

	for(i=0; i<=5; i++)
		RNA_int_set(WM_keymap_add_item(keymap, "OBJECT_OT_subdivision_set", ZEROKEY+i, KM_PRESS, KM_CTRL, 0)->ptr, "level", i);

	/* multires switch */
	kmi= WM_keymap_add_item(keymap, "OBJECT_OT_subdivision_set", PAGEUPKEY, KM_PRESS, 0, 0);
	RNA_int_set(kmi->ptr, "level", 1);
	RNA_boolean_set(kmi->ptr, "relative", 1);

	kmi= WM_keymap_add_item(keymap, "OBJECT_OT_subdivision_set", PAGEDOWNKEY, KM_PRESS, 0, 0);
	RNA_int_set(kmi->ptr, "level", -1);
	RNA_boolean_set(kmi->ptr, "relative", 1);

	ed_keymap_paint_brush_switch(keymap, "sculpt");
	ed_keymap_paint_brush_size(keymap, "tool_settings.sculpt.brush.size");

	RNA_enum_set(WM_keymap_add_item(keymap, "BRUSH_OT_sculpt_tool_set", DKEY, KM_PRESS, 0, 0)->ptr, "tool", SCULPT_TOOL_DRAW);
	RNA_enum_set(WM_keymap_add_item(keymap, "BRUSH_OT_sculpt_tool_set", SKEY, KM_PRESS, 0, 0)->ptr, "tool", SCULPT_TOOL_SMOOTH);
	RNA_enum_set(WM_keymap_add_item(keymap, "BRUSH_OT_sculpt_tool_set", PKEY, KM_PRESS, 0, 0)->ptr, "tool", SCULPT_TOOL_PINCH);
	RNA_enum_set(WM_keymap_add_item(keymap, "BRUSH_OT_sculpt_tool_set", IKEY, KM_PRESS, 0, 0)->ptr, "tool", SCULPT_TOOL_INFLATE);
	RNA_enum_set(WM_keymap_add_item(keymap, "BRUSH_OT_sculpt_tool_set", GKEY, KM_PRESS, 0, 0)->ptr, "tool", SCULPT_TOOL_GRAB);
	RNA_enum_set(WM_keymap_add_item(keymap, "BRUSH_OT_sculpt_tool_set", LKEY, KM_PRESS, 0, 0)->ptr, "tool", SCULPT_TOOL_LAYER);
	RNA_enum_set(WM_keymap_add_item(keymap, "BRUSH_OT_sculpt_tool_set", TKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "tool", SCULPT_TOOL_FLATTEN); /* was just TKEY in 2.4x */
	RNA_enum_set(WM_keymap_add_item(keymap, "BRUSH_OT_sculpt_tool_set", CKEY, KM_PRESS, 0, 0)->ptr, "tool", SCULPT_TOOL_CLAY);
	RNA_enum_set(WM_keymap_add_item(keymap, "BRUSH_OT_sculpt_tool_set", CKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "tool", SCULPT_TOOL_CREASE);

	/* */
	kmi = WM_keymap_add_item(keymap, "WM_OT_context_menu_enum", AKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "data_path", "tool_settings.sculpt.brush.stroke_method");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_toggle", SKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "data_path", "tool_settings.sculpt.brush.use_smooth_stroke");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_toggle", RKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "data_path", "tool_settings.sculpt.brush.use_rake");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_toggle", AKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "data_path", "tool_settings.sculpt.brush.use_airbrush");

	/* Vertex Paint mode */
	keymap= WM_keymap_find(keyconf, "Vertex Paint", 0, 0);
	keymap->poll= vertex_paint_mode_poll;

	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_vertex_paint_radial_control", FKEY, KM_PRESS, 0, 0)->ptr, "mode", WM_RADIALCONTROL_SIZE);
	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_vertex_paint_radial_control", FKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "mode", WM_RADIALCONTROL_STRENGTH);
	WM_keymap_verify_item(keymap, "PAINT_OT_vertex_paint", LEFTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "PAINT_OT_sample_color", RIGHTMOUSE, KM_PRESS, 0, 0);

	WM_keymap_add_item(keymap,
			"PAINT_OT_vertex_color_set",KKEY, KM_PRESS, KM_SHIFT, 0);

	ed_keymap_paint_brush_switch(keymap, "vertex_paint");
	ed_keymap_paint_brush_size(keymap, "tool_settings.vertex_paint.brush.size");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_toggle", MKEY, KM_PRESS, 0, 0); /* mask toggle */
	RNA_string_set(kmi->ptr, "data_path", "vertex_paint_object.data.use_paint_mask");

	/* Weight Paint mode */
	keymap= WM_keymap_find(keyconf, "Weight Paint", 0, 0);
	keymap->poll= weight_paint_mode_poll;

	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_weight_paint_radial_control", FKEY, KM_PRESS, 0, 0)->ptr, "mode", WM_RADIALCONTROL_SIZE);
	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_weight_paint_radial_control", FKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "mode", WM_RADIALCONTROL_STRENGTH);

	WM_keymap_verify_item(keymap, "PAINT_OT_weight_paint", LEFTMOUSE, KM_PRESS, 0, 0);

	WM_keymap_add_item(keymap,
			"PAINT_OT_weight_set", KKEY, KM_PRESS, KM_SHIFT, 0);

	ed_keymap_paint_brush_switch(keymap, "weight_paint");
	ed_keymap_paint_brush_size(keymap, "tool_settings.weight_paint.brush.size");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_toggle", MKEY, KM_PRESS, 0, 0); /* mask toggle */
	RNA_string_set(kmi->ptr, "data_path", "weight_paint_object.data.use_paint_mask");

	WM_keymap_verify_item(keymap, "PAINT_OT_weight_from_bones", WKEY, KM_PRESS, 0, 0);

	/* Image/Texture Paint mode */
	keymap= WM_keymap_find(keyconf, "Image Paint", 0, 0);
	keymap->poll= image_texture_paint_poll;

	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_image_paint_radial_control", FKEY, KM_PRESS, 0, 0)->ptr, "mode", WM_RADIALCONTROL_SIZE);
	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_image_paint_radial_control", FKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "mode", WM_RADIALCONTROL_STRENGTH);

	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_texture_paint_radial_control", FKEY, KM_PRESS, 0, 0)->ptr, "mode", WM_RADIALCONTROL_SIZE);
	RNA_enum_set(WM_keymap_add_item(keymap, "PAINT_OT_texture_paint_radial_control", FKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "mode", WM_RADIALCONTROL_STRENGTH);

	WM_keymap_add_item(keymap, "PAINT_OT_image_paint", LEFTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "PAINT_OT_grab_clone", RIGHTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "PAINT_OT_sample_color", RIGHTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "PAINT_OT_clone_cursor_set", LEFTMOUSE, KM_PRESS, KM_CTRL, 0);

	ed_keymap_paint_brush_switch(keymap, "image_paint");
	ed_keymap_paint_brush_size(keymap, "tool_settings.image_paint.brush.size");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_toggle", MKEY, KM_PRESS, 0, 0); /* mask toggle */
	RNA_string_set(kmi->ptr, "data_path", "image_paint_object.data.use_paint_mask");

	/* face-mask mode */
	keymap= WM_keymap_find(keyconf, "Face Mask", 0, 0);
	keymap->poll= facemask_paint_poll;

	WM_keymap_add_item(keymap, "PAINT_OT_face_select_all", AKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "PAINT_OT_face_select_inverse", IKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "PAINT_OT_face_select_hide", HKEY, KM_PRESS, 0, 0);
	RNA_boolean_set(WM_keymap_add_item(keymap, "PAINT_OT_face_select_hide", HKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "unselected", 1);
	WM_keymap_add_item(keymap, "PAINT_OT_face_select_reveal", HKEY, KM_PRESS, KM_ALT, 0);

	WM_keymap_add_item(keymap, "PAINT_OT_face_select_linked", LKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "PAINT_OT_face_select_linked_pick", LKEY, KM_PRESS, 0, 0);
}
