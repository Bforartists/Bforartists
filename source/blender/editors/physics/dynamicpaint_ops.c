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
 * ***** END GPL LICENSE BLOCK *****
 */

#include <math.h>
#include <stdio.h>
#include <string.h>

#include "BLI_blenlib.h"
#include "BLI_string.h"
#include "BLI_utildefines.h"

#include "DNA_dynamicpaint_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BKE_blender.h"
#include "BKE_context.h"
#include "BKE_deform.h"
#include "BKE_depsgraph.h"
#include "BKE_dynamicpaint.h"
#include "BKE_global.h"
#include "BKE_modifier.h"
#include "BKE_report.h"

#include "ED_mesh.h"
#include "ED_screen.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

/* Platform independend time	*/
#include "PIL_time.h"

#include "WM_types.h"
#include "WM_api.h"

static int surface_slot_add_exec(bContext *C, wmOperator *UNUSED(op))
{
	DynamicPaintModifierData *pmd = 0;
	Object *cObject = CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	DynamicPaintCanvasSettings *canvas;
	DynamicPaintSurface *surface;

	/* Make sure we're dealing with a canvas */
	pmd = (DynamicPaintModifierData *)modifiers_findByType(cObject, eModifierType_DynamicPaint);
	if (!pmd || !pmd->canvas) return OPERATOR_CANCELLED;

	canvas = pmd->canvas;
	surface = dynamicPaint_createNewSurface(canvas, CTX_data_scene(C));

	if (!surface) return OPERATOR_CANCELLED;

	/* set preview for this surface only and set active */
	canvas->active_sur = 0;
	for(surface=surface->prev; surface; surface=surface->prev) {
				surface->flags &= ~MOD_DPAINT_PREVIEW;
				canvas->active_sur++;
	}

	return OPERATOR_FINISHED;
}

/* add surface slot */
void DPAINT_OT_surface_slot_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Surface Slot";
	ot->idname= "DPAINT_OT_surface_slot_add";
	ot->description="Add a new Dynamic Paint surface slot";
	
	/* api callbacks */
	ot->exec= surface_slot_add_exec;
	ot->poll= ED_operator_object_active_editable;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int surface_slot_remove_exec(bContext *C, wmOperator *UNUSED(op))
{
	DynamicPaintModifierData *pmd = 0;
	Object *cObject = CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	DynamicPaintCanvasSettings *canvas;
	DynamicPaintSurface *surface;
	int id=0;

	/* Make sure we're dealing with a canvas */
	pmd = (DynamicPaintModifierData *)modifiers_findByType(cObject, eModifierType_DynamicPaint);
	if (!pmd || !pmd->canvas) return OPERATOR_CANCELLED;

	canvas = pmd->canvas;
	surface = canvas->surfaces.first;

	/* find active surface and remove it */
	for(; surface; surface=surface->next) {
		if(id == canvas->active_sur) {
				canvas->active_sur -= 1;
				dynamicPaint_freeSurface(surface);
				break;
			}
		id++;
	}

	dynamicPaint_resetPreview(canvas);
	DAG_id_tag_update(&cObject->id, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_MODIFIER, cObject);

	return OPERATOR_FINISHED;
}

/* remove surface slot */
void DPAINT_OT_surface_slot_remove(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Remove Surface Slot";
	ot->idname= "DPAINT_OT_surface_slot_remove";
	ot->description="Remove the selected surface slot";
	
	/* api callbacks */
	ot->exec= surface_slot_remove_exec;
	ot->poll= ED_operator_object_active_editable;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int type_toggle_exec(bContext *C, wmOperator *op)
{

	Object *cObject = CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	Scene *scene = CTX_data_scene(C);
	DynamicPaintModifierData *pmd = (DynamicPaintModifierData *)modifiers_findByType(cObject, eModifierType_DynamicPaint);
	int type= RNA_enum_get(op->ptr, "type");

	if (!pmd) return OPERATOR_CANCELLED;

	/* if type is already enabled, toggle it off */
	if (type == MOD_DYNAMICPAINT_TYPE_CANVAS && pmd->canvas) {
			dynamicPaint_freeCanvas(pmd);
	}
	else if (type == MOD_DYNAMICPAINT_TYPE_BRUSH && pmd->brush) {
			dynamicPaint_freeBrush(pmd);
	}
	/* else create a new type */
	else {
		if (!dynamicPaint_createType(pmd, type, scene))
			return OPERATOR_CANCELLED;
	}
	
	/* update dependancy */
	DAG_id_tag_update(&cObject->id, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_MODIFIER, cObject);
	DAG_scene_sort(CTX_data_main(C), scene);

	return OPERATOR_FINISHED;
}

void DPAINT_OT_type_toggle(wmOperatorType *ot)
{
	PropertyRNA *prop;

	/* identifiers */
	ot->name= "Toggle Type Active";
	ot->idname= "DPAINT_OT_type_toggle";
	ot->description = "Toggles whether given type is active or not";
	
	/* api callbacks */
	ot->exec= type_toggle_exec;
	ot->poll= ED_operator_object_active_editable;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* properties */
	prop= RNA_def_enum(ot->srna, "type", prop_dynamicpaint_type_items, MOD_DYNAMICPAINT_TYPE_CANVAS, "Type", "");
	ot->prop= prop;
}

static int output_toggle_exec(bContext *C, wmOperator *op)
{
	Object *ob = CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	Scene *scene = CTX_data_scene(C);
	DynamicPaintSurface *surface;
	DynamicPaintModifierData *pmd = (DynamicPaintModifierData *)modifiers_findByType(ob, eModifierType_DynamicPaint);
	int output= RNA_enum_get(op->ptr, "output"); /* currently only 1/0 */

	if (!pmd || !pmd->canvas) return OPERATOR_CANCELLED;
	surface = get_activeSurface(pmd->canvas);

	/* if type is already enabled, toggle it off */
	if (surface->format == MOD_DPAINT_SURFACE_F_VERTEX) {
		int exists = dynamicPaint_outputLayerExists(surface, ob, output);
		const char *name;
		
		if (output == 0)
			name = surface->output_name;
		else
			name = surface->output_name2;

		/* Vertex Color Layer */
		if (surface->type == MOD_DPAINT_SURFACE_T_PAINT) {
			if (!exists)
				ED_mesh_color_add(C, scene, ob, ob->data, name, 1);
			else 
				ED_mesh_color_remove_named(C, ob, ob->data, name);
		}
		/* Vertex Weight Layer */
		else if (surface->type == MOD_DPAINT_SURFACE_T_WEIGHT) {
			if (!exists) {
				ED_vgroup_add_name(ob, name);
			}
			else {
				bDeformGroup *defgroup = defgroup_find_name(ob, name);
				if (defgroup) ED_vgroup_delete(ob, defgroup);
			}
		}
	}

	return OPERATOR_FINISHED;
}

void DPAINT_OT_output_toggle(wmOperatorType *ot)
{
	static EnumPropertyItem prop_output_toggle_types[] = {
		{0, "A", 0, "Output A", ""},
		{1, "B", 0, "Output B", ""},
		{0, NULL, 0, NULL, NULL}
	};

	/* identifiers */
	ot->name= "Toggle Output Layer";
	ot->idname= "DPAINT_OT_output_toggle";
	ot->description = "Adds or removes Dynamic Paint output data layer";
	
	/* api callbacks */
	ot->exec= output_toggle_exec;
	ot->poll= ED_operator_object_active_editable;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* properties */
	ot->prop= RNA_def_enum(ot->srna, "output", prop_output_toggle_types, 0, "Output Toggle", "");
}


/***************************** Image Sequence Baking ******************************/

/*
*	Do actual bake operation. Loop through to-be-baked frames.
*	Returns 0 on failture.
*/
static int dynamicPaint_bakeImageSequence(bContext *C, DynamicPaintSurface *surface, Object *cObject)
{
	DynamicPaintCanvasSettings *canvas = surface->canvas;
	Scene *scene= CTX_data_scene(C);
	wmWindow *win = CTX_wm_window(C);
	int frame = 1;
	int frames;

	frames = surface->end_frame - surface->start_frame + 1;
	if (frames <= 0) {BLI_strncpy(canvas->error, "No frames to bake.", sizeof(canvas->error)); return 0;}

	/* Set frame to start point (also inits modifier data) */
	frame = surface->start_frame;
	scene->r.cfra = (int)frame;
	ED_update_for_newframe(CTX_data_main(C), scene, win->screen, 1);

	/* Init surface	*/
	if (!dynamicPaint_createUVSurface(surface)) return 0;

	/* Loop through selected frames */
	for (frame=surface->start_frame; frame<=surface->end_frame; frame++)
	{
		float progress = (frame - surface->start_frame) / (float)frames * 100;
		surface->current_frame = frame;

		/* If user requested stop (esc), quit baking	*/
		if (blender_test_break()) return 0;

		/* Update progress bar cursor */
		WM_timecursor(win, (int)progress);

		/* calculate a frame */
		scene->r.cfra = (int)frame;
		ED_update_for_newframe(CTX_data_main(C), scene, win->screen, 1);
		if (!dynamicPaint_calculateFrame(surface, scene, cObject, frame)) return 0;

		/*
		*	Save output images
		*/
		{
			char filename[FILE_MAX];
			/* make sure output path has ending slash */
			BLI_add_slash(surface->image_output_path);

			/* primary output layer */
			if (surface->flags & MOD_DPAINT_OUT1) {
				/* set filepath */
				BLI_snprintf(filename, sizeof(filename), "%s%s", surface->image_output_path, surface->output_name);
				BLI_path_frame(filename, frame, 4);
				/* save image */
				dynamicPaint_outputSurfaceImage(surface, filename, 0);
			}
			/* secondary output */
			if (surface->flags & MOD_DPAINT_OUT2 && surface->type == MOD_DPAINT_SURFACE_T_PAINT) {
				/* set filepath */
				BLI_snprintf(filename, sizeof(filename), "%s%s", surface->image_output_path, surface->output_name2);
				BLI_path_frame(filename, frame, 4);
				/* save image */
				dynamicPaint_outputSurfaceImage(surface, filename, 1);
			}
		}
	}
	return 1;
}


/*
*	Bake Dynamic Paint image sequence surface
*/
int dynamicPaint_initBake(struct bContext *C, struct wmOperator *op)
{
	DynamicPaintModifierData *pmd = NULL;
	DynamicPaintCanvasSettings *canvas;
	Object *ob = CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	int status = 0;
	double timer = PIL_check_seconds_timer();
	char result_str[80];
	DynamicPaintSurface *surface;

	/*
	*	Get modifier data
	*/
	pmd = (DynamicPaintModifierData *)modifiers_findByType(ob, eModifierType_DynamicPaint);
	if (!pmd) {
		BKE_report(op->reports, RPT_ERROR, "Bake Failed: No Dynamic Paint modifier found.");
		return 0;
	}

	/* Make sure we're dealing with a canvas */
	canvas = pmd->canvas;
	if (!canvas) {
		BKE_report(op->reports, RPT_ERROR, "Bake Failed: Invalid Canvas.");
		return 0;
	}
	surface = get_activeSurface(canvas);

	/* Set state to baking and init surface */
	canvas->error[0] = '\0';
	canvas->flags |= MOD_DPAINT_BAKING;
	G.afbreek= 0;	/* reset blender_test_break*/

	/*  Bake Dynamic Paint	*/
	status = dynamicPaint_bakeImageSequence(C, surface, ob);
	/* Clear bake */
	canvas->flags &= ~MOD_DPAINT_BAKING;
	WM_cursor_restore(CTX_wm_window(C));
	dynamicPaint_freeSurfaceData(surface);

	/* Bake was successful:
	*  Report for ended bake and how long it took */
	if (status) {
		/* Format time string	*/
		char time_str[30];
		double time = PIL_check_seconds_timer() - timer;
		BLI_timestr(time, time_str);

		/* Show bake info */
		BLI_snprintf(result_str, sizeof(result_str), "Bake Complete! (%s)", time_str);
		BKE_report(op->reports, RPT_INFO, result_str);
	}
	else {
		if (strlen(canvas->error)) { /* If an error occured */
			BLI_snprintf(result_str, sizeof(result_str), "Bake Failed: %s", canvas->error);
			BKE_report(op->reports, RPT_ERROR, result_str);
		}
		else {	/* User cancelled the bake */
			BLI_strncpy(result_str, "Baking Cancelled!", sizeof(result_str));
			BKE_report(op->reports, RPT_WARNING, result_str);
		}
	}

	return status;
}

static int dynamicpaint_bake_exec(bContext *C, wmOperator *op)
{
	/* Bake dynamic paint */
	if(!dynamicPaint_initBake(C, op)) {
		return OPERATOR_CANCELLED;}

	return OPERATOR_FINISHED;
}

void DPAINT_OT_bake(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Dynamic Paint Bake";
	ot->description= "Bake dynamic paint image sequence surface";
	ot->idname= "DPAINT_OT_bake";
	
	/* api callbacks */
	ot->exec= dynamicpaint_bake_exec;
	ot->poll= ED_operator_object_active_editable;
}
