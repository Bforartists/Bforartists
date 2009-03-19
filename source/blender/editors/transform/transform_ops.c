/**
 * $Id: transform_ops.c 17542 2008-11-23 15:27:53Z theeth $
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
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "MEM_guardedalloc.h"

#include "DNA_scene_types.h"
#include "DNA_space_types.h"
#include "DNA_windowmanager_types.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "BLI_arithb.h"

#include "BKE_utildefines.h"
#include "BKE_context.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_interface.h"

#include "ED_screen.h"

#include "transform.h"

typedef struct TransformModeItem
{
	char *idname;
	int		mode;
} TransformModeItem;

static float VecOne[3] = {1, 1, 1};

/* need constants for this */
EnumPropertyItem proportional_mode_types[] = {
		{0, "OFF", "Off", ""},
		{1, "ON", "On", ""},
		{2, "CONNECTED", "Connected", ""},
		{0, NULL, NULL, NULL}
};

EnumPropertyItem proportional_falloff_types[] = {
		{PROP_SMOOTH, "SMOOTH", "Smooth", ""},
		{PROP_SPHERE, "SPHERE", "Sphere", ""},
		{PROP_ROOT, "ROOT", "Root", ""},
		{PROP_SHARP, "SHARP", "Sharp", ""},
		{PROP_LIN, "LINEAR", "Linear", ""},
		{PROP_CONST, "CONSTANT", "Constant", ""},
		{PROP_RANDOM, "RANDOM", "Random", ""},
		{0, NULL, NULL, NULL}
};

char OP_TRANSLATION[] = "TFM_OT_translation";
char OP_ROTATION[] = "TFM_OT_rotation";
char OP_TOSPHERE[] = "TFM_OT_tosphere";
char OP_RESIZE[] = "TFM_OT_resize";
char OP_SHEAR[] = "TFM_OT_shear";
char OP_WARP[] = "TFM_OT_warp";
char OP_SHRINK_FATTEN[] = "TFM_OT_shrink_fatten";
char OP_TILT[] = "TFM_OT_tilt";


TransformModeItem transform_modes[] =
{
	{OP_TRANSLATION, TFM_TRANSLATION},
	{OP_ROTATION, TFM_ROTATION},
	{OP_TOSPHERE, TFM_TOSPHERE},
	{OP_RESIZE, TFM_RESIZE},
	{OP_SHEAR, TFM_SHEAR},
	{OP_WARP, TFM_WARP},
	{OP_SHRINK_FATTEN, TFM_SHRINKFATTEN},
	{OP_TILT, TFM_TILT},
	{NULL, 0}
};

static int select_orientation_exec(bContext *C, wmOperator *op)
{
	int orientation = RNA_enum_get(op->ptr, "orientation");
	int custom_index= RNA_int_get(op->ptr, "custom_index");;

	if(orientation == V3D_MANIP_CUSTOM)
		orientation += custom_index;
	
	BIF_selectTransformOrientationValue(C, orientation);

	return OPERATOR_FINISHED;
}

static int select_orientation_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	uiMenuItem *head;
	
	head= uiPupMenuBegin("Orientation", 0);
	BIF_menuTransformOrientation(C, head, NULL);
	uiPupMenuEnd(C, head);
	
	return OPERATOR_CANCELLED;
}
	
void TFM_OT_select_orientation(struct wmOperatorType *ot)
{
	static EnumPropertyItem orientation_items[]= {
		{V3D_MANIP_GLOBAL, "GLOBAL", "Global", ""},
		{V3D_MANIP_NORMAL, "NORMAL", "Normal", ""},
		{V3D_MANIP_LOCAL, "LOCAL", "Local", ""},
		{V3D_MANIP_VIEW, "VIEW", "View", ""},
		{V3D_MANIP_CUSTOM, "CUSTOM", "Custom", ""},
		{0, NULL, NULL, NULL}};

	/* identifiers */
	ot->name   = "Select Orientation";
	ot->idname = "TFM_OT_select_orientation";

	/* api callbacks */
	ot->invoke = select_orientation_invoke;
	ot->exec   = select_orientation_exec;
	ot->poll   = ED_operator_areaactive;

	RNA_def_enum(ot->srna, "orientation", orientation_items, V3D_MANIP_CUSTOM, "Orientation", "DOC_BROKEN");
	RNA_def_int(ot->srna, "custom_index", 0, 0, INT_MAX, "Custom Index", "", 0, INT_MAX);
}

static void transformops_exit(bContext *C, wmOperator *op)
{
	saveTransform(C, op->customdata, op);
	MEM_freeN(op->customdata);
	op->customdata = NULL;
}

static void transformops_data(bContext *C, wmOperator *op, wmEvent *event)
{
	if (op->customdata == NULL)
	{
		TransInfo *t = MEM_callocN(sizeof(TransInfo), "TransInfo data");
		TransformModeItem *tmode;
		int mode = -1;

		for (tmode = transform_modes; tmode->idname; tmode++)
		{
			if (op->type->idname == tmode->idname)
			{
				mode = tmode->mode;
			}
		}

		if (mode == -1)
		{
			mode = RNA_int_get(op->ptr, "mode");
		}

		initTransform(C, t, op, event, mode);
	
		/* store data */
		op->customdata = t;
	}
}

static int transform_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	int exit_code;
	
	TransInfo *t = op->customdata;
	
	transformEvent(t, event);
	
	transformApply(C, t);
	
	
	exit_code = transformEnd(C, t);
	
	if (exit_code != OPERATOR_RUNNING_MODAL)
	{
		transformops_exit(C, op);
	}

	return exit_code;
}

static int transform_cancel(bContext *C, wmOperator *op)
{
	TransInfo *t = op->customdata;
	
	t->state = TRANS_CANCEL;
	transformEnd(C, t);
	transformops_exit(C, op);
	
	return OPERATOR_CANCELLED;
}

static int transform_exec(bContext *C, wmOperator *op)
{
	TransInfo *t;

	transformops_data(C, op, NULL);

	t = op->customdata;

	t->options |= CTX_AUTOCONFIRM;

	transformApply(C, t);
	
	transformEnd(C, t);

	transformops_exit(C, op);
	
	return OPERATOR_FINISHED;
}

static int transform_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	transformops_data(C, op, event);

	if(RNA_property_is_set(op->ptr, "value")) {
		return transform_exec(C, op);
	}
	else {
		TransInfo *t = op->customdata;

		/* add temp handler */
		WM_event_add_modal_handler(C, &CTX_wm_window(C)->handlers, op);

		t->flag |= T_MODAL; // XXX meh maybe somewhere else

		return OPERATOR_RUNNING_MODAL;
	}
}

void Properties_Proportional(struct wmOperatorType *ot)
{
	RNA_def_enum(ot->srna, "proportional", proportional_mode_types, 0, "Proportional Edition", "");
	RNA_def_enum(ot->srna, "proportional_editing_falloff", prop_mode_items, 0, "Proportional Editing Falloff", "Falloff type for proportional editing mode.");
	RNA_def_float(ot->srna, "proportional_size", 1, 0, FLT_MAX, "Proportional Size", "", 0, 100);

}

void Properties_Constraints(struct wmOperatorType *ot)
{
	RNA_def_boolean_vector(ot->srna, "constraint_axis", 3, NULL, "Constraint Axis", "");
	RNA_def_int(ot->srna, "constraint_orientation", 0, 0, INT_MAX, "Constraint Orientation", "", 0, INT_MAX);
}

void TFM_OT_translation(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name   = "Translation";
	ot->idname = OP_TRANSLATION;
	ot->flag = OPTYPE_REGISTER|OPTYPE_UNDO;

	/* api callbacks */
	ot->invoke = transform_invoke;
	ot->exec   = transform_exec;
	ot->modal  = transform_modal;
	ot->cancel  = transform_cancel;
	ot->poll   = ED_operator_areaactive;

	RNA_def_float_vector(ot->srna, "value", 3, NULL, -FLT_MAX, FLT_MAX, "Vector", "", -FLT_MAX, FLT_MAX);

	Properties_Proportional(ot);

	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Edition", "");

	Properties_Constraints(ot);
}

void TFM_OT_resize(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name   = "Resize";
	ot->idname = OP_RESIZE;
	ot->flag = OPTYPE_REGISTER|OPTYPE_UNDO;

	/* api callbacks */
	ot->invoke = transform_invoke;
	ot->exec   = transform_exec;
	ot->modal  = transform_modal;
	ot->cancel  = transform_cancel;
	ot->poll   = ED_operator_areaactive;

	RNA_def_float_vector(ot->srna, "value", 3, VecOne, -FLT_MAX, FLT_MAX, "Vector", "", -FLT_MAX, FLT_MAX);

	Properties_Proportional(ot);

	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Edition", "");

	Properties_Constraints(ot);
}

void TFM_OT_rotation(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name   = "Rotation";
	ot->idname = OP_ROTATION;
	ot->flag = OPTYPE_REGISTER|OPTYPE_UNDO;

	/* api callbacks */
	ot->invoke = transform_invoke;
	ot->exec   = transform_exec;
	ot->modal  = transform_modal;
	ot->cancel  = transform_cancel;
	ot->poll   = ED_operator_areaactive;

	RNA_def_float_rotation(ot->srna, "value", 1, NULL, -FLT_MAX, FLT_MAX, "Angle", "", -M_PI*2, M_PI*2);

	Properties_Proportional(ot);

	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Edition", "");

	Properties_Constraints(ot);
}

void TFM_OT_tilt(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name   = "Tilt";
	ot->idname = OP_TILT;
	ot->flag = OPTYPE_REGISTER|OPTYPE_UNDO;

	/* api callbacks */
	ot->invoke = transform_invoke;
	ot->exec   = transform_exec;
	ot->modal  = transform_modal;
	ot->cancel  = transform_cancel;
	ot->poll   = ED_operator_editcurve;

	RNA_def_float_rotation(ot->srna, "value", 1, NULL, -FLT_MAX, FLT_MAX, "Angle", "", -M_PI*2, M_PI*2);

	Properties_Proportional(ot);

	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Edition", "");

	Properties_Constraints(ot);
}

void TFM_OT_warp(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name   = "Warp";
	ot->idname = OP_WARP;
	ot->flag = OPTYPE_REGISTER|OPTYPE_UNDO;

	/* api callbacks */
	ot->invoke = transform_invoke;
	ot->exec   = transform_exec;
	ot->modal  = transform_modal;
	ot->cancel  = transform_cancel;
	ot->poll   = ED_operator_areaactive;

	RNA_def_float_rotation(ot->srna, "value", 1, NULL, -FLT_MAX, FLT_MAX, "Angle", "", 0, 1);

	Properties_Proportional(ot);

	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Edition", "");

	// XXX Shear axis?
//	Properties_Constraints(ot);
}

void TFM_OT_shear(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name   = "Shear";
	ot->idname = OP_SHEAR;
	ot->flag = OPTYPE_REGISTER|OPTYPE_UNDO;

	/* api callbacks */
	ot->invoke = transform_invoke;
	ot->exec   = transform_exec;
	ot->modal  = transform_modal;
	ot->cancel  = transform_cancel;
	ot->poll   = ED_operator_areaactive;

	RNA_def_float(ot->srna, "value", 0, -FLT_MAX, FLT_MAX, "Offset", "", -FLT_MAX, FLT_MAX);

	Properties_Proportional(ot);

	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Edition", "");

	// XXX Shear axis?
//	Properties_Constraints(ot);
}

void TFM_OT_shrink_fatten(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name   = "Shrink/Fatten";
	ot->idname = OP_SHRINK_FATTEN;
	ot->flag = OPTYPE_REGISTER|OPTYPE_UNDO;

	/* api callbacks */
	ot->invoke = transform_invoke;
	ot->exec   = transform_exec;
	ot->modal  = transform_modal;
	ot->cancel  = transform_cancel;
	ot->poll   = ED_operator_editmesh;

	RNA_def_float(ot->srna, "value", 0, -FLT_MAX, FLT_MAX, "Offset", "", -FLT_MAX, FLT_MAX);

	Properties_Proportional(ot);

	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Edition", "");
}

void TFM_OT_tosphere(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name   = "To Sphere";
	ot->idname = OP_TOSPHERE;
	ot->flag = OPTYPE_REGISTER|OPTYPE_UNDO;

	/* api callbacks */
	ot->invoke = transform_invoke;
	ot->exec   = transform_exec;
	ot->modal  = transform_modal;
	ot->cancel  = transform_cancel;
	ot->poll   = ED_operator_areaactive;

	RNA_def_float_percentage(ot->srna, "value", 0, 0, 1, "Percentage", "", 0, 1);

	Properties_Proportional(ot);

	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Edition", "");
}

void TFM_OT_transform(struct wmOperatorType *ot)
{
	static EnumPropertyItem transform_mode_types[] = {
			{TFM_INIT, "INIT", "Init", ""},
			{TFM_DUMMY, "DUMMY", "Dummy", ""},
			{TFM_TRANSLATION, "TRANSLATION", "Translation", ""},
			{TFM_ROTATION, "ROTATION", "Rotation", ""},
			{TFM_RESIZE, "RESIZE", "Resize", ""},
			{TFM_TOSPHERE, "TOSPHERE", "Tosphere", ""},
			{TFM_SHEAR, "SHEAR", "Shear", ""},
			{TFM_WARP, "WARP", "Warp", ""},
			{TFM_SHRINKFATTEN, "SHRINKFATTEN", "Shrinkfatten", ""},
			{TFM_TILT, "TILT", "Tilt", ""},
			{TFM_TRACKBALL, "TRACKBALL", "Trackball", ""},
			{TFM_PUSHPULL, "PUSHPULL", "Pushpull", ""},
			{TFM_CREASE, "CREASE", "Crease", ""},
			{TFM_MIRROR, "MIRROR", "Mirror", ""},
			{TFM_BONESIZE, "BONESIZE", "Bonesize", ""},
			{TFM_BONE_ENVELOPE, "BONE_ENVELOPE", "Bone_Envelope", ""},
			{TFM_CURVE_SHRINKFATTEN, "CURVE_SHRINKFATTEN", "Curve_Shrinkfatten", ""},
			{TFM_BONE_ROLL, "BONE_ROLL", "Bone_Roll", ""},
			{TFM_TIME_TRANSLATE, "TIME_TRANSLATE", "Time_Translate", ""},
			{TFM_TIME_SLIDE, "TIME_SLIDE", "Time_Slide", ""},
			{TFM_TIME_SCALE, "TIME_SCALE", "Time_Scale", ""},
			{TFM_TIME_EXTEND, "TIME_EXTEND", "Time_Extend", ""},
			{TFM_BAKE_TIME, "BAKE_TIME", "Bake_Time", ""},
			{TFM_BEVEL, "BEVEL", "Bevel", ""},
			{TFM_BWEIGHT, "BWEIGHT", "Bweight", ""},
			{TFM_ALIGN, "ALIGN", "Align", ""},
			{0, NULL, NULL, NULL}
	};

	/* identifiers */
	ot->name   = "Transform";
	ot->idname = "TFM_OT_transform";
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* api callbacks */
	ot->invoke = transform_invoke;
	ot->exec   = transform_exec;
	ot->modal  = transform_modal;
	ot->cancel  = transform_cancel;
	ot->poll   = ED_operator_areaactive;

	RNA_def_enum(ot->srna, "mode", transform_mode_types, 0, "Mode", "");

	RNA_def_float_vector(ot->srna, "value", 4, NULL, -FLT_MAX, FLT_MAX, "Values", "", -FLT_MAX, FLT_MAX);

	Properties_Proportional(ot);
	RNA_def_boolean(ot->srna, "mirror", 0, "Mirror Edition", "");

	RNA_def_boolean_vector(ot->srna, "constraint_axis", 3, NULL, "Constraint Axis", "");
	RNA_def_int(ot->srna, "constraint_orientation", 0, 0, INT_MAX, "Constraint Orientation", "", 0, INT_MAX);
}

void transform_operatortypes(void)
{
	WM_operatortype_append(TFM_OT_transform);
	WM_operatortype_append(TFM_OT_translation);
	WM_operatortype_append(TFM_OT_rotation);
	WM_operatortype_append(TFM_OT_tosphere);
	WM_operatortype_append(TFM_OT_resize);
	WM_operatortype_append(TFM_OT_shear);
	WM_operatortype_append(TFM_OT_warp);
	WM_operatortype_append(TFM_OT_shrink_fatten);
	WM_operatortype_append(TFM_OT_tilt);

	WM_operatortype_append(TFM_OT_select_orientation);
}
 
void transform_keymap_for_space(struct wmWindowManager *wm, struct ListBase *keymap, int spaceid)
{
	wmKeymapItem *km;
	switch(spaceid)
	{
		case SPACE_VIEW3D:
			km = WM_keymap_add_item(keymap, "TFM_OT_translation", GKEY, KM_PRESS, 0, 0);
			
			km= WM_keymap_add_item(keymap, "TFM_OT_translation", EVT_TWEAK_S, KM_ANY, 0, 0);
			
			km = WM_keymap_add_item(keymap, "TFM_OT_rotation", RKEY, KM_PRESS, 0, 0);

			km = WM_keymap_add_item(keymap, "TFM_OT_resize", SKEY, KM_PRESS, 0, 0);

			km = WM_keymap_add_item(keymap, "TFM_OT_warp", WKEY, KM_PRESS, KM_SHIFT, 0);

			km = WM_keymap_add_item(keymap, "TFM_OT_tosphere", SKEY, KM_PRESS, KM_CTRL|KM_SHIFT, 0);
			
			km = WM_keymap_add_item(keymap, "TFM_OT_shear", SKEY, KM_PRESS, KM_ALT|KM_CTRL|KM_SHIFT, 0);
			
			km = WM_keymap_add_item(keymap, "TFM_OT_shrink_fatten", SKEY, KM_PRESS, KM_ALT, 0);

			km = WM_keymap_add_item(keymap, "TFM_OT_tilt", TKEY, KM_PRESS, 0, 0);

			km = WM_keymap_add_item(keymap, "TFM_OT_select_orientation", SPACEKEY, KM_PRESS, KM_ALT, 0);

			break;
		case SPACE_ACTION:
			km= WM_keymap_add_item(keymap, "TFM_OT_transform", GKEY, KM_PRESS, 0, 0);
			RNA_int_set(km->ptr, "mode", TFM_TIME_TRANSLATE);
			
			km= WM_keymap_add_item(keymap, "TFM_OT_transform", EVT_TWEAK_S, KM_ANY, 0, 0);
			RNA_int_set(km->ptr, "mode", TFM_TIME_TRANSLATE);
			
			km= WM_keymap_add_item(keymap, "TFM_OT_transform", EKEY, KM_PRESS, 0, 0);
			RNA_int_set(km->ptr, "mode", TFM_TIME_EXTEND);
			
			km= WM_keymap_add_item(keymap, "TFM_OT_transform", SKEY, KM_PRESS, 0, 0);
			RNA_int_set(km->ptr, "mode", TFM_TIME_SCALE);
			
			km= WM_keymap_add_item(keymap, "TFM_OT_transform", TKEY, KM_PRESS, 0, 0);
			RNA_int_set(km->ptr, "mode", TFM_TIME_SLIDE);
			break;
		case SPACE_IPO:
			km= WM_keymap_add_item(keymap, "TFM_OT_translation", GKEY, KM_PRESS, 0, 0);
			
			km= WM_keymap_add_item(keymap, "TFM_OT_translation", EVT_TWEAK_S, KM_ANY, 0, 0);
			
				// XXX the 'mode' identifier here is not quite right
			km= WM_keymap_add_item(keymap, "TFM_OT_transform", EKEY, KM_PRESS, 0, 0);
			RNA_int_set(km->ptr, "mode", TFM_TIME_EXTEND);
			
			km = WM_keymap_add_item(keymap, "TFM_OT_rotation", RKEY, KM_PRESS, 0, 0);
			
			km = WM_keymap_add_item(keymap, "TFM_OT_resize", SKEY, KM_PRESS, 0, 0);
			break;
		case SPACE_NODE:
			km= WM_keymap_add_item(keymap, "TFM_OT_translation", GKEY, KM_PRESS, 0, 0);
			
			km= WM_keymap_add_item(keymap, "TFM_OT_translation", EVT_TWEAK_A, KM_ANY, 0, 0);
			km= WM_keymap_add_item(keymap, "TFM_OT_translation", EVT_TWEAK_S, KM_ANY, 0, 0);
			
			km = WM_keymap_add_item(keymap, "TFM_OT_rotation", RKEY, KM_PRESS, 0, 0);
			
			km = WM_keymap_add_item(keymap, "TFM_OT_resize", SKEY, KM_PRESS, 0, 0);
			break;
		case SPACE_SEQ:
			km= WM_keymap_add_item(keymap, "TFM_OT_translation", GKEY, KM_PRESS, 0, 0);
			
			km= WM_keymap_add_item(keymap, "TFM_OT_translation", EVT_TWEAK_S, KM_ANY, 0, 0);
			
			km= WM_keymap_add_item(keymap, "TFM_OT_transform", EKEY, KM_PRESS, 0, 0);
			RNA_int_set(km->ptr, "mode", TFM_TIME_EXTEND);
			break;
		case SPACE_IMAGE:
			km = WM_keymap_add_item(keymap, "TFM_OT_translation", GKEY, KM_PRESS, 0, 0);
			
			km= WM_keymap_add_item(keymap, "TFM_OT_translation", EVT_TWEAK_S, KM_ANY, 0, 0);
			
			km = WM_keymap_add_item(keymap, "TFM_OT_rotation", RKEY, KM_PRESS, 0, 0);

			km = WM_keymap_add_item(keymap, "TFM_OT_resize", SKEY, KM_PRESS, 0, 0);

			km = WM_keymap_add_item(keymap, "TFM_OT_transform", MKEY, KM_PRESS, 0, 0);
			RNA_int_set(km->ptr, "mode", TFM_MIRROR);
			break;
		default:
			break;
	}
}

