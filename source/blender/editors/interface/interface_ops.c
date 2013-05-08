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
 * Contributor(s): Blender Foundation, Joshua Leung
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/interface/interface_ops.c
 *  \ingroup edinterface
 */

#include <stdio.h>
#include <math.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_text_types.h" /* for UI_OT_reports_to_text */

#include "BLI_blenlib.h"
#include "BLI_math_color.h"
#include "BLI_math_vector.h"
#include "BLI_utildefines.h"

#include "BLF_api.h"
#include "BLF_translation.h"

#include "BKE_context.h"
#include "BKE_screen.h"
#include "BKE_global.h"
#include "BKE_text.h" /* for UI_OT_reports_to_text */
#include "BKE_report.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "BIF_gl.h"

#include "UI_interface.h"

#include "IMB_colormanagement.h"

#include "interface_intern.h"

#include "WM_api.h"
#include "WM_types.h"

/* only for UI_OT_editsource */
#include "ED_screen.h"
#include "BKE_main.h"
#include "BLI_ghash.h"

#include "ED_image.h"  /* for HDR color sampling */
#include "ED_node.h"   /* for HDR color sampling */
#include "ED_clip.h"   /* for HDR color sampling */

/* ********************************************************** */

typedef struct Eyedropper {
	struct ColorManagedDisplay *display;

	PointerRNA ptr;
	PropertyRNA *prop;
	int index;

	int   accum_start; /* has mouse been presed */
	float accum_col[3];
	int   accum_tot;
} Eyedropper;

static int eyedropper_init(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Eyedropper *eye;
	
	op->customdata = eye = MEM_callocN(sizeof(Eyedropper), "Eyedropper");
	
	uiContextActiveProperty(C, &eye->ptr, &eye->prop, &eye->index);

	if ((eye->ptr.data == NULL) ||
	    (eye->prop == NULL) ||
	    (RNA_property_editable(&eye->ptr, eye->prop) == FALSE) ||
	    (RNA_property_array_length(&eye->ptr, eye->prop) < 3) ||
	    (RNA_property_type(eye->prop) != PROP_FLOAT))
	{
		return FALSE;
	}

	if (RNA_property_subtype(eye->prop) == PROP_COLOR) {
		const char *display_device;

		display_device = scene->display_settings.display_device;
		eye->display = IMB_colormanagement_display_get_named(display_device);
	}

	return TRUE;
}

static void eyedropper_exit(bContext *C, wmOperator *op)
{
	WM_cursor_restore(CTX_wm_window(C));
	
	if (op->customdata)
		MEM_freeN(op->customdata);
	op->customdata = NULL;
}

static int eyedropper_cancel(bContext *C, wmOperator *op)
{
	eyedropper_exit(C, op);
	return OPERATOR_CANCELLED;
}

/* *** eyedropper_color_ helper functions *** */

/**
 * \brief get the color from the screen.
 *
 * Special check for image or nodes where we MAY have HDR pixels which don't display.
 */
static void eyedropper_color_sample_fl(bContext *C, Eyedropper *UNUSED(eye), int mx, int my, float r_col[3])
{

	/* we could use some clever */
	wmWindow *win = CTX_wm_window(C);
	ScrArea *sa;
	for (sa = win->screen->areabase.first; sa; sa = sa->next) {
		if (BLI_rcti_isect_pt(&sa->totrct, mx, my)) {
			if (sa->spacetype == SPACE_IMAGE) {
				ARegion *ar = BKE_area_find_region_type(sa, RGN_TYPE_WINDOW);
				if (BLI_rcti_isect_pt(&ar->winrct, mx, my)) {
					SpaceImage *sima = sa->spacedata.first;
					int mval[2] = {mx - ar->winrct.xmin,
					               my - ar->winrct.ymin};

					if (ED_space_image_color_sample(sima, ar, mval, r_col)) {
						return;
					}
				}
			}
			else if (sa->spacetype == SPACE_NODE) {
				ARegion *ar = BKE_area_find_region_type(sa, RGN_TYPE_WINDOW);
				if (BLI_rcti_isect_pt(&ar->winrct, mx, my)) {
					SpaceNode *snode = sa->spacedata.first;
					int mval[2] = {mx - ar->winrct.xmin,
					               my - ar->winrct.ymin};

					if (ED_space_node_color_sample(snode, ar, mval, r_col)) {
						return;
					}
				}
			}
			else if (sa->spacetype == SPACE_CLIP) {
				ARegion *ar = BKE_area_find_region_type(sa, RGN_TYPE_WINDOW);
				if (BLI_rcti_isect_pt(&ar->winrct, mx, my)) {
					SpaceClip *sc = sa->spacedata.first;
					int mval[2] = {mx - ar->winrct.xmin,
					               my - ar->winrct.ymin};

					if (ED_space_clip_color_sample(sc, ar, mval, r_col)) {
						return;
					}
				}
			}
		}
	}

	/* fallback to simple opengl picker */
	glReadBuffer(GL_FRONT);
	glReadPixels(mx, my, 1, 1, GL_RGB, GL_FLOAT, r_col);
	glReadBuffer(GL_BACK);
}

/* sets the sample color RGB, maintaining A */
static void eyedropper_color_set(bContext *C, Eyedropper *eye, const float col[3])
{
	float col_conv[4];

	/* to maintain alpha */
	RNA_property_float_get_array(&eye->ptr, eye->prop, col_conv);

	/* convert from display space to linear rgb space */
	if (eye->display) {
		copy_v3_v3(col_conv, col);
		IMB_colormanagement_display_to_scene_linear_v3(col_conv, eye->display);
	}
	else {
		copy_v3_v3(col_conv, col);
	}

	RNA_property_float_set_array(&eye->ptr, eye->prop, col_conv);

	RNA_property_update(C, &eye->ptr, eye->prop);
}

/* set sample from accumulated values */
static void eyedropper_color_set_accum(bContext *C, Eyedropper *eye)
{
	float col[3];
	mul_v3_v3fl(col, eye->accum_col, 1.0f / (float)eye->accum_tot);
	eyedropper_color_set(C, eye, col);
}

/* single point sample & set */
static void eyedropper_color_sample(bContext *C, Eyedropper *eye, int mx, int my)
{
	float col[3];
	eyedropper_color_sample_fl(C, eye, mx, my, col);
	eyedropper_color_set(C, eye, col);
}

static void eyedropper_color_sample_accum(bContext *C, Eyedropper *eye, int mx, int my)
{
	float col[3];
	eyedropper_color_sample_fl(C, eye, mx, my, col);
	/* delay linear conversion */
	add_v3_v3(eye->accum_col, col);
	eye->accum_tot++;
}

/* main modal status check */
static int eyedropper_modal(bContext *C, wmOperator *op, const wmEvent *event)
{
	Eyedropper *eye = (Eyedropper *)op->customdata;
	
	switch (event->type) {
		case ESCKEY:
		case RIGHTMOUSE:
			return eyedropper_cancel(C, op);
		case LEFTMOUSE:
			if (event->val == KM_RELEASE) {
				if (eye->accum_tot == 0) {
					eyedropper_color_sample(C, eye, event->x, event->y);
				}
				else {
					eyedropper_color_set_accum(C, eye);
				}
				eyedropper_exit(C, op);
				return OPERATOR_FINISHED;
			}
			else if (event->val == KM_PRESS) {
				/* enable accum and make first sample */
				eye->accum_start = TRUE;
				eyedropper_color_sample_accum(C, eye, event->x, event->y);
			}
			break;
		case MOUSEMOVE:
			if (eye->accum_start) {
				/* button is pressed so keep sampling */
				eyedropper_color_sample_accum(C, eye, event->x, event->y);
				eyedropper_color_set_accum(C, eye);
			}
			break;
		case SPACEKEY:
			if (event->val == KM_RELEASE) {
				eye->accum_tot = 0;
				zero_v3(eye->accum_col);
				eyedropper_color_sample_accum(C, eye, event->x, event->y);
				eyedropper_color_set_accum(C, eye);
			}
			break;
	}
	
	return OPERATOR_RUNNING_MODAL;
}

/* Modal Operator init */
static int eyedropper_invoke(bContext *C, wmOperator *op, const wmEvent *UNUSED(event))
{
	/* init */
	if (eyedropper_init(C, op)) {
		WM_cursor_modal(CTX_wm_window(C), BC_EYEDROPPER_CURSOR);

		/* add temp handler */
		WM_event_add_modal_handler(C, op);
		
		return OPERATOR_RUNNING_MODAL;
	}
	else {
		eyedropper_exit(C, op);
		return OPERATOR_CANCELLED;
	}
}

/* Repeat operator */
static int eyedropper_exec(bContext *C, wmOperator *op)
{
	/* init */
	if (eyedropper_init(C, op)) {
		
		/* do something */
		
		/* cleanup */
		eyedropper_exit(C, op);
		
		return OPERATOR_FINISHED;
	}
	else {
		return OPERATOR_CANCELLED;
	}
}

static int eyedropper_poll(bContext *C)
{
	if (!CTX_wm_window(C)) return 0;
	else return 1;
}

static void UI_OT_eyedropper(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Eyedropper";
	ot->idname = "UI_OT_eyedropper";
	ot->description = "Sample a color from the Blender Window to store in a property";
	
	/* api callbacks */
	ot->invoke = eyedropper_invoke;
	ot->modal = eyedropper_modal;
	ot->cancel = eyedropper_cancel;
	ot->exec = eyedropper_exec;
	ot->poll = eyedropper_poll;
	
	/* flags */
	ot->flag = OPTYPE_BLOCKING;
	
	/* properties */
}

/* Reset Default Theme ------------------------ */

static int reset_default_theme_exec(bContext *C, wmOperator *UNUSED(op))
{
	ui_theme_init_default();
	WM_event_add_notifier(C, NC_WINDOW, NULL);
	
	return OPERATOR_FINISHED;
}

static void UI_OT_reset_default_theme(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Reset to Default Theme";
	ot->idname = "UI_OT_reset_default_theme";
	ot->description = "Reset to the default theme colors";
	
	/* callbacks */
	ot->exec = reset_default_theme_exec;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER;
}

/* Copy Data Path Operator ------------------------ */

static int copy_data_path_button_poll(bContext *C)
{
	PointerRNA ptr;
	PropertyRNA *prop;
	char *path;
	int index;

	uiContextActiveProperty(C, &ptr, &prop, &index);

	if (ptr.id.data && ptr.data && prop) {
		path = RNA_path_from_ID_to_property(&ptr, prop);
		
		if (path) {
			MEM_freeN(path);
			return 1;
		}
	}

	return 0;
}

static int copy_data_path_button_exec(bContext *C, wmOperator *UNUSED(op))
{
	PointerRNA ptr;
	PropertyRNA *prop;
	char *path;
	int index;

	/* try to create driver using property retrieved from UI */
	uiContextActiveProperty(C, &ptr, &prop, &index);

	if (ptr.id.data && ptr.data && prop) {
		path = RNA_path_from_ID_to_property(&ptr, prop);
		
		if (path) {
			WM_clipboard_text_set(path, FALSE);
			MEM_freeN(path);
			return OPERATOR_FINISHED;
		}
	}

	return OPERATOR_CANCELLED;
}

static void UI_OT_copy_data_path_button(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Copy Data Path";
	ot->idname = "UI_OT_copy_data_path_button";
	ot->description = "Copy the RNA data path for this property to the clipboard";

	/* callbacks */
	ot->exec = copy_data_path_button_exec;
	ot->poll = copy_data_path_button_poll;

	/* flags */
	ot->flag = OPTYPE_REGISTER;
}

/* Reset to Default Values Button Operator ------------------------ */

static int reset_default_button_poll(bContext *C)
{
	PointerRNA ptr;
	PropertyRNA *prop;
	int index;

	uiContextActiveProperty(C, &ptr, &prop, &index);
	
	return (ptr.data && prop && RNA_property_editable(&ptr, prop));
}

static int reset_default_button_exec(bContext *C, wmOperator *op)
{
	PointerRNA ptr;
	PropertyRNA *prop;
	int success = 0;
	int index, all = RNA_boolean_get(op->ptr, "all");

	/* try to reset the nominated setting to its default value */
	uiContextActiveProperty(C, &ptr, &prop, &index);
	
	/* if there is a valid property that is editable... */
	if (ptr.data && prop && RNA_property_editable(&ptr, prop)) {
		if (RNA_property_reset(&ptr, prop, (all) ? -1 : index)) {
			/* perform updates required for this property */
			RNA_property_update(C, &ptr, prop);

			/* as if we pressed the button */
			uiContextActivePropertyHandle(C);

			success = 1;
		}
	}

	/* Since we don't want to undo _all_ edits to settings, eg window
	 * edits on the screen or on operator settings.
	 * it might be better to move undo's inline - campbell */
	if (success) {
		ID *id = ptr.id.data;
		if (id && ID_CHECK_UNDO(id)) {
			/* do nothing, go ahead with undo */
		}
		else {
			return OPERATOR_CANCELLED;
		}
	}
	/* end hack */

	return (success) ? OPERATOR_FINISHED : OPERATOR_CANCELLED;
}

static void UI_OT_reset_default_button(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Reset to Default Value";
	ot->idname = "UI_OT_reset_default_button";
	ot->description = "Reset this property's value to its default value";

	/* callbacks */
	ot->poll = reset_default_button_poll;
	ot->exec = reset_default_button_exec;

	/* flags */
	ot->flag = OPTYPE_UNDO;
	
	/* properties */
	RNA_def_boolean(ot->srna, "all", 1, "All", "Reset to default values all elements of the array");
}

/* Copy To Selected Operator ------------------------ */

static int copy_to_selected_list(bContext *C, PointerRNA *ptr, ListBase *lb, int *use_path)
{
	*use_path = FALSE;

	if (RNA_struct_is_a(ptr->type, &RNA_EditBone))
		*lb = CTX_data_collection_get(C, "selected_editable_bones");
	else if (RNA_struct_is_a(ptr->type, &RNA_PoseBone))
		*lb = CTX_data_collection_get(C, "selected_pose_bones");
	else if (RNA_struct_is_a(ptr->type, &RNA_Sequence))
		*lb = CTX_data_collection_get(C, "selected_editable_sequences");
	else {
		ID *id = ptr->id.data;

		if (id && GS(id->name) == ID_OB) {
			*lb = CTX_data_collection_get(C, "selected_editable_objects");
			*use_path = TRUE;
		}
		else
			return 0;
	}
	
	return 1;
}

static int copy_to_selected_button_poll(bContext *C)
{
	PointerRNA ptr, lptr, idptr;
	PropertyRNA *prop, *lprop;
	int index, success = 0;

	uiContextActiveProperty(C, &ptr, &prop, &index);

	if (ptr.data && prop) {
		char *path = NULL;
		int use_path;
		CollectionPointerLink *link;
		ListBase lb;

		if (!copy_to_selected_list(C, &ptr, &lb, &use_path))
			return success;

		if (!use_path || (path = RNA_path_from_ID_to_property(&ptr, prop))) {
			for (link = lb.first; link; link = link->next) {
				if (link->ptr.data != ptr.data) {
					if (use_path) {
						lprop = NULL;
						RNA_id_pointer_create(link->ptr.id.data, &idptr);
						RNA_path_resolve_property(&idptr, path, &lptr, &lprop);
					}
					else {
						lptr = link->ptr;
						lprop = prop;
					}

					if (lprop == prop) {
						if (RNA_property_editable(&lptr, prop))
							success = 1;
					}
				}
			}

			if (path)
				MEM_freeN(path);
		}

		BLI_freelistN(&lb);
	}

	return success;
}

static int copy_to_selected_button_exec(bContext *C, wmOperator *op)
{
	PointerRNA ptr, lptr, idptr;
	PropertyRNA *prop, *lprop;
	int success = 0;
	int index, all = RNA_boolean_get(op->ptr, "all");

	/* try to reset the nominated setting to its default value */
	uiContextActiveProperty(C, &ptr, &prop, &index);
	
	/* if there is a valid property that is editable... */
	if (ptr.data && prop) {
		char *path = NULL;
		int use_path;
		CollectionPointerLink *link;
		ListBase lb;

		if (!copy_to_selected_list(C, &ptr, &lb, &use_path))
			return success;

		if (!use_path || (path = RNA_path_from_ID_to_property(&ptr, prop))) {
			for (link = lb.first; link; link = link->next) {
				if (link->ptr.data != ptr.data) {
					if (use_path) {
						lprop = NULL;
						RNA_id_pointer_create(link->ptr.id.data, &idptr);
						RNA_path_resolve_property(&idptr, path, &lptr, &lprop);
					}
					else {
						lptr = link->ptr;
						lprop = prop;
					}

					if (lprop == prop) {
						if (RNA_property_editable(&lptr, lprop)) {
							if (RNA_property_copy(&lptr, &ptr, prop, (all) ? -1 : index)) {
								RNA_property_update(C, &lptr, prop);
								success = 1;
							}
						}
					}
				}
			}

			if (path)
				MEM_freeN(path);
		}

		BLI_freelistN(&lb);
	}
	
	return (success) ? OPERATOR_FINISHED : OPERATOR_CANCELLED;
}

static void UI_OT_copy_to_selected_button(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Copy To Selected";
	ot->idname = "UI_OT_copy_to_selected_button";
	ot->description = "Copy property from this object to selected objects or bones";

	/* callbacks */
	ot->poll = copy_to_selected_button_poll;
	ot->exec = copy_to_selected_button_exec;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	RNA_def_boolean(ot->srna, "all", 1, "All", "Reset to default values all elements of the array");
}

/* Reports to Textblock Operator ------------------------ */

/* FIXME: this is just a temporary operator so that we can see all the reports somewhere 
 * when there are too many to display...
 */

static int reports_to_text_poll(bContext *C)
{
	return CTX_wm_reports(C) != NULL;
}

static int reports_to_text_exec(bContext *C, wmOperator *UNUSED(op))
{
	ReportList *reports = CTX_wm_reports(C);
	Main *bmain = CTX_data_main(C);
	Text *txt;
	char *str;
	
	/* create new text-block to write to */
	txt = BKE_text_add(bmain, "Recent Reports");
	
	/* convert entire list to a display string, and add this to the text-block
	 *	- if commandline debug option enabled, show debug reports too
	 *	- otherwise, up to info (which is what users normally see)
	 */
	str = BKE_reports_string(reports, (G.debug & G_DEBUG) ? RPT_DEBUG : RPT_INFO);

	if (str) {
		BKE_text_write(txt, str);
		MEM_freeN(str);

		return OPERATOR_FINISHED;
	}
	else {
		return OPERATOR_CANCELLED;
	}
}

static void UI_OT_reports_to_textblock(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Reports to Text Block";
	ot->idname = "UI_OT_reports_to_textblock";
	ot->description = "Write the reports ";
	
	/* callbacks */
	ot->poll = reports_to_text_poll;
	ot->exec = reports_to_text_exec;
}

#ifdef WITH_PYTHON

/* ------------------------------------------------------------------------- */
/* EditSource Utility funcs and operator,
 * note, this includes utility functions and button matching checks */

struct uiEditSourceStore {
	uiBut but_orig;
	GHash *hash;
} uiEditSourceStore;

struct uiEditSourceButStore {
	char py_dbg_fn[FILE_MAX];
	int py_dbg_ln;
} uiEditSourceButStore;

/* should only ever be set while the edit source operator is running */
static struct uiEditSourceStore *ui_editsource_info = NULL;

bool UI_editsource_enable_check(void)
{
	return (ui_editsource_info != NULL);
}

static void ui_editsource_active_but_set(uiBut *but)
{
	BLI_assert(ui_editsource_info == NULL);

	ui_editsource_info = MEM_callocN(sizeof(uiEditSourceStore), __func__);
	memcpy(&ui_editsource_info->but_orig, but, sizeof(uiBut));

	ui_editsource_info->hash = BLI_ghash_ptr_new(__func__);
}

static void ui_editsource_active_but_clear(void)
{
	BLI_ghash_free(ui_editsource_info->hash, NULL, (GHashValFreeFP)MEM_freeN);
	MEM_freeN(ui_editsource_info);
	ui_editsource_info = NULL;
}

static int ui_editsource_uibut_match(uiBut *but_a, uiBut *but_b)
{
#if 0
	printf("matching buttons: '%s' == '%s'\n",
	       but_a->drawstr, but_b->drawstr);
#endif

	/* this just needs to be a 'good-enough' comparison so we can know beyond
	 * reasonable doubt that these buttons are the same between redraws.
	 * if this fails it only means edit-source fails - campbell */
	if (BLI_rctf_compare(&but_a->rect, &but_b->rect, FLT_EPSILON) &&
	    (but_a->type == but_b->type) &&
	    (but_a->rnaprop == but_b->rnaprop) &&
	    (but_a->optype == but_b->optype) &&
	    (but_a->unit_type == but_b->unit_type) &&
	    (strncmp(but_a->drawstr, but_b->drawstr, UI_MAX_DRAW_STR) == 0))
	{
		return TRUE;
	}
	else {
		return FALSE;
	}
}

void UI_editsource_active_but_test(uiBut *but)
{
	extern void PyC_FileAndNum_Safe(const char **filename, int *lineno);

	struct uiEditSourceButStore *but_store = MEM_callocN(sizeof(uiEditSourceButStore), __func__);

	const char *fn;
	int lineno = -1;

#if 0
	printf("comparing buttons: '%s' == '%s'\n",
	       but->drawstr, ui_editsource_info->but_orig.drawstr);
#endif

	PyC_FileAndNum_Safe(&fn, &lineno);

	if (lineno != -1) {
		BLI_strncpy(but_store->py_dbg_fn, fn,
		            sizeof(but_store->py_dbg_fn));
		but_store->py_dbg_ln = lineno;
	}
	else {
		but_store->py_dbg_fn[0] = '\0';
		but_store->py_dbg_ln = -1;
	}

	BLI_ghash_insert(ui_editsource_info->hash, but, but_store);
}

static int editsource_text_edit(bContext *C, wmOperator *op,
                                char filepath[FILE_MAX], int line)
{
	struct Main *bmain = CTX_data_main(C);
	Text *text;

	for (text = bmain->text.first; text; text = text->id.next) {
		if (text->name && BLI_path_cmp(text->name, filepath) == 0) {
			break;
		}
	}

	if (text == NULL) {
		text = BKE_text_load(bmain, filepath, bmain->name);
	}

	if (text == NULL) {
		BKE_reportf(op->reports, RPT_WARNING, "File '%s' cannot be opened", filepath);
		return OPERATOR_CANCELLED;
	}
	else {
		/* naughty!, find text area to set, not good behavior
		 * but since this is a dev tool lets allow it - campbell */
		ScrArea *sa = BKE_screen_find_big_area(CTX_wm_screen(C), SPACE_TEXT, 0);
		if (sa) {
			SpaceText *st = sa->spacedata.first;
			st->text = text;
		}
		else {
			BKE_reportf(op->reports, RPT_INFO, "See '%s' in the text editor", text->id.name + 2);
		}

		txt_move_toline(text, line - 1, FALSE);
		WM_event_add_notifier(C, NC_TEXT | ND_CURSOR, text);
	}

	return OPERATOR_FINISHED;
}

static int editsource_exec(bContext *C, wmOperator *op)
{
	uiBut *but = uiContextActiveButton(C);

	if (but) {
		GHashIterator ghi;
		struct uiEditSourceButStore *but_store = NULL;

		ARegion *ar = CTX_wm_region(C);
		int ret;

		/* needed else the active button does not get tested */
		uiFreeActiveButtons(C, CTX_wm_screen(C));

		// printf("%s: begin\n", __func__);

		/* take care not to return before calling ui_editsource_active_but_clear */
		ui_editsource_active_but_set(but);

		/* redraw and get active button python info */
		ED_region_do_draw(C, ar);

		for (BLI_ghashIterator_init(&ghi, ui_editsource_info->hash);
		     BLI_ghashIterator_done(&ghi) == false;
		     BLI_ghashIterator_step(&ghi))
		{
			uiBut *but_key = BLI_ghashIterator_getKey(&ghi);
			if (but_key && ui_editsource_uibut_match(&ui_editsource_info->but_orig, but_key)) {
				but_store = BLI_ghashIterator_getValue(&ghi);
				break;
			}

		}

		if (but_store) {
			if (but_store->py_dbg_ln != -1) {
				ret = editsource_text_edit(C, op,
				                           but_store->py_dbg_fn,
				                           but_store->py_dbg_ln);
			}
			else {
				BKE_report(op->reports, RPT_ERROR, "Active button is not from a script, cannot edit source");
				ret = OPERATOR_CANCELLED;
			}
		}
		else {
			BKE_report(op->reports, RPT_ERROR, "Active button match cannot be found");
			ret = OPERATOR_CANCELLED;
		}


		ui_editsource_active_but_clear();

		// printf("%s: end\n", __func__);

		return ret;
	}
	else {
		BKE_report(op->reports, RPT_ERROR, "Active button not found");
		return OPERATOR_CANCELLED;
	}
}

static void UI_OT_editsource(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Edit Source";
	ot->idname = "UI_OT_editsource";
	ot->description = "Edit UI source code of the active button";

	/* callbacks */
	ot->exec = editsource_exec;
}

/* ------------------------------------------------------------------------- */
/* EditTranslation utility funcs and operator,
 * Note: this includes utility functions and button matching checks.
 *       this only works in conjunction with a py operator! */

static void edittranslation_find_po_file(const char *root, const char *uilng, char *path, const size_t maxlen)
{
	char tstr[32]; /* Should be more than enough! */

	/* First, full lang code. */
	BLI_snprintf(tstr, sizeof(tstr), "%s.po", uilng);
	BLI_join_dirfile(path, maxlen, root, uilng);
	BLI_join_dirfile(path, maxlen, path, tstr);
	if (BLI_is_file(path))
		return;

	/* Now try without the second iso code part (_ES in es_ES). */
	{
		char *tc = NULL;
		size_t szt = 0;
		tstr[0] = '\0';

		tc = strchr(uilng, '_');
		if (tc) {
			szt = tc - uilng;
			if (szt < sizeof(tstr)) /* Paranoid, should always be true! */
				BLI_strncpy(tstr, uilng, szt + 1); /* +1 for '\0' char! */
		}
		if (tstr[0]) {
			/* Because of some codes like sr_SR@latin... */
			tc = strchr(uilng, '@');
			if (tc)
				BLI_strncpy(tstr + szt, tc, sizeof(tstr) - szt);

			BLI_join_dirfile(path, maxlen, root, tstr);
			strcat(tstr, ".po");
			BLI_join_dirfile(path, maxlen, path, tstr);
			if (BLI_is_file(path))
				return;
		}
	}

	/* Else no po file! */
	path[0] = '\0';
}

static int edittranslation_exec(bContext *C, wmOperator *op)
{
	uiBut *but = uiContextActiveButton(C);
	int ret = OPERATOR_CANCELLED;

	if (but) {
		PointerRNA ptr;
		char popath[FILE_MAX];
		const char *root = U.i18ndir;
		const char *uilng = BLF_lang_get();

		uiStringInfo but_label = {BUT_GET_LABEL, NULL};
		uiStringInfo rna_label = {BUT_GET_RNA_LABEL, NULL};
		uiStringInfo enum_label = {BUT_GET_RNAENUM_LABEL, NULL};
		uiStringInfo but_tip = {BUT_GET_TIP, NULL};
		uiStringInfo rna_tip = {BUT_GET_RNA_TIP, NULL};
		uiStringInfo enum_tip = {BUT_GET_RNAENUM_TIP, NULL};
		uiStringInfo rna_struct = {BUT_GET_RNASTRUCT_IDENTIFIER, NULL};
		uiStringInfo rna_prop = {BUT_GET_RNAPROP_IDENTIFIER, NULL};
		uiStringInfo rna_enum = {BUT_GET_RNAENUM_IDENTIFIER, NULL};
		uiStringInfo rna_ctxt = {BUT_GET_RNA_LABEL_CONTEXT, NULL};

		if (!BLI_is_dir(root)) {
			BKE_report(op->reports, RPT_ERROR, "Please set your User Preferences' 'Translation Branches "
			                                   "Directory' path to a valid directory");
			return OPERATOR_CANCELLED;
		}
		if (!WM_operatortype_find(EDTSRC_I18N_OP_NAME, 0)) {
			BKE_reportf(op->reports, RPT_ERROR, "Could not find operator '%s'! Please enable ui_translate addon "
			                                    "in the User Preferences", EDTSRC_I18N_OP_NAME);
			return OPERATOR_CANCELLED;
		}
		/* Try to find a valid po file for current language... */
		edittranslation_find_po_file(root, uilng, popath, FILE_MAX);
/*		printf("po path: %s\n", popath);*/
		if (popath[0] == '\0') {
			BKE_reportf(op->reports, RPT_ERROR, "No valid po found for language '%s' under %s", uilng, root);
			return OPERATOR_CANCELLED;
		}

		uiButGetStrInfo(C, but, &but_label, &rna_label, &enum_label, &but_tip, &rna_tip, &enum_tip,
		                &rna_struct, &rna_prop, &rna_enum, &rna_ctxt, NULL);

		WM_operator_properties_create(&ptr, EDTSRC_I18N_OP_NAME);
		RNA_string_set(&ptr, "lang", uilng);
		RNA_string_set(&ptr, "po_file", popath);
		RNA_string_set(&ptr, "but_label", but_label.strinfo);
		RNA_string_set(&ptr, "rna_label", rna_label.strinfo);
		RNA_string_set(&ptr, "enum_label", enum_label.strinfo);
		RNA_string_set(&ptr, "but_tip", but_tip.strinfo);
		RNA_string_set(&ptr, "rna_tip", rna_tip.strinfo);
		RNA_string_set(&ptr, "enum_tip", enum_tip.strinfo);
		RNA_string_set(&ptr, "rna_struct", rna_struct.strinfo);
		RNA_string_set(&ptr, "rna_prop", rna_prop.strinfo);
		RNA_string_set(&ptr, "rna_enum", rna_enum.strinfo);
		RNA_string_set(&ptr, "rna_ctxt", rna_ctxt.strinfo);
		ret = WM_operator_name_call(C, EDTSRC_I18N_OP_NAME, WM_OP_INVOKE_DEFAULT, &ptr);

		/* Clean up */
		if (but_label.strinfo)
			MEM_freeN(but_label.strinfo);
		if (rna_label.strinfo)
			MEM_freeN(rna_label.strinfo);
		if (enum_label.strinfo)
			MEM_freeN(enum_label.strinfo);
		if (but_tip.strinfo)
			MEM_freeN(but_tip.strinfo);
		if (rna_tip.strinfo)
			MEM_freeN(rna_tip.strinfo);
		if (enum_tip.strinfo)
			MEM_freeN(enum_tip.strinfo);
		if (rna_struct.strinfo)
			MEM_freeN(rna_struct.strinfo);
		if (rna_prop.strinfo)
			MEM_freeN(rna_prop.strinfo);
		if (rna_enum.strinfo)
			MEM_freeN(rna_enum.strinfo);
		if (rna_ctxt.strinfo)
			MEM_freeN(rna_ctxt.strinfo);

		return ret;
	}
	else {
		BKE_report(op->reports, RPT_ERROR, "Active button not found");
		return OPERATOR_CANCELLED;
	}
}

static void UI_OT_edittranslation_init(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Edit Translation";
	ot->idname = "UI_OT_edittranslation_init";
	ot->description = "Edit i18n in current language for the active button";

	/* callbacks */
	ot->exec = edittranslation_exec;
}

#endif /* WITH_PYTHON */

static int reloadtranslation_exec(bContext *UNUSED(C), wmOperator *UNUSED(op))
{
	BLF_lang_init();
	BLF_cache_clear();
	BLF_lang_set(NULL);
	UI_reinit_font();
	return OPERATOR_FINISHED;
}

static void UI_OT_reloadtranslation(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Reload Translation";
	ot->idname = "UI_OT_reloadtranslation";
	ot->description = "Force a full reload of UI translation";

	/* callbacks */
	ot->exec = reloadtranslation_exec;
}

/* ********************************************************* */
/* Registration */

void UI_buttons_operatortypes(void)
{
	WM_operatortype_append(UI_OT_eyedropper);
	WM_operatortype_append(UI_OT_reset_default_theme);
	WM_operatortype_append(UI_OT_copy_data_path_button);
	WM_operatortype_append(UI_OT_reset_default_button);
	WM_operatortype_append(UI_OT_copy_to_selected_button);
	WM_operatortype_append(UI_OT_reports_to_textblock);  /* XXX: temp? */

#ifdef WITH_PYTHON
	WM_operatortype_append(UI_OT_editsource);
	WM_operatortype_append(UI_OT_edittranslation_init);
#endif
	WM_operatortype_append(UI_OT_reloadtranslation);
}
