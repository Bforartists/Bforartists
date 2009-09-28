/**
 * $Id$
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation, 2002-2008 full recode
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>

#include "MEM_guardedalloc.h"

#include "DNA_action_types.h"
#include "DNA_curve_types.h"
#include "DNA_group_types.h"
#include "DNA_lamp_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meta_types.h"
#include "DNA_object_fluidsim.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view3d_types.h"
#include "DNA_vfont_types.h"

#include "BLI_arithb.h"
#include "BLI_listbase.h"

#include "BKE_anim.h"
#include "BKE_armature.h"
#include "BKE_constraint.h"
#include "BKE_context.h"
#include "BKE_curve.h"
#include "BKE_customdata.h"
#include "BKE_depsgraph.h"
#include "BKE_DerivedMesh.h"
#include "BKE_displist.h"
#include "BKE_global.h"
#include "BKE_group.h"
#include "BKE_lattice.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_mball.h"
#include "BKE_mesh.h"
#include "BKE_modifier.h"
#include "BKE_object.h"
#include "BKE_particle.h"
#include "BKE_report.h"
#include "BKE_sca.h"
#include "BKE_scene.h"
#include "BKE_texture.h"
#include "BKE_utildefines.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_anim_api.h"
#include "ED_armature.h"
#include "ED_curve.h"
#include "ED_mball.h"
#include "ED_mesh.h"
#include "ED_object.h"
#include "ED_screen.h"
#include "ED_transform.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "object_intern.h"

/************************** Exported *****************************/

void ED_object_base_init_from_view(bContext *C, Base *base)
{
	View3D *v3d= CTX_wm_view3d(C);
	Scene *scene= CTX_data_scene(C);
	Object *ob= base->object;
	
	if (scene==NULL)
		return;
	
	if (v3d==NULL) {
		base->lay = scene->lay;
		VECCOPY(ob->loc, scene->cursor);
	} 
	else {
		if (v3d->localvd) {
			base->lay= ob->lay= v3d->layact | v3d->lay;
			VECCOPY(ob->loc, v3d->cursor);
		} 
		else {
			base->lay= ob->lay= v3d->layact;
			VECCOPY(ob->loc, scene->cursor);
		}
		
		if (U.flag & USER_ADD_VIEWALIGNED) {
			ARegion *ar= CTX_wm_region(C);
			if(ar) {
				RegionView3D *rv3d= ar->regiondata;
				
				rv3d->viewquat[0]= -rv3d->viewquat[0];
				QuatToEul(rv3d->viewquat, ob->rot);
				rv3d->viewquat[0]= -rv3d->viewquat[0];
			}
		}
	}
	where_is_object(scene, ob);
}

/********************* Add Object Operator ********************/

void add_object_draw(Scene *scene, View3D *v3d, int type)	/* for toolbox or menus, only non-editmode stuff */
{
	/* keep here to get things compile, remove later */
}

/* for object add primitive operators */
static Object *object_add_type(bContext *C, int type)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob;
	
	/* for as long scene has editmode... */
	if (CTX_data_edit_object(C)) 
		ED_object_exit_editmode(C, EM_FREEDATA|EM_FREEUNDO|EM_WAITCURSOR); /* freedata, and undo */
	
	/* deselects all, sets scene->basact */
	ob= add_object(scene, type);
	/* editor level activate, notifiers */
	ED_base_object_activate(C, BASACT);

	/* more editor stuff */
	ED_object_base_init_from_view(C, BASACT);

	DAG_scene_sort(scene);

	return ob;
}

/* for object add operator */
static int object_add_exec(bContext *C, wmOperator *op)
{
	object_add_type(C, RNA_enum_get(op->ptr, "type"));
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Object";
	ot->description = "Add an object to the scene.";
	ot->idname= "OBJECT_OT_add";
	
	/* api callbacks */
	ot->invoke= WM_menu_invoke;
	ot->exec= object_add_exec;
	
	ot->poll= ED_operator_scene_editable;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	RNA_def_enum(ot->srna, "type", object_type_items, 0, "Type", "");
}

/* ***************** add primitives *************** */
/* ******  work both in and outside editmode ****** */

static EnumPropertyItem prop_mesh_types[] = {
	{0, "PLANE", ICON_MESH_PLANE, "Plane", ""},
	{1, "CUBE", ICON_MESH_CUBE, "Cube", ""},
	{2, "CIRCLE", ICON_MESH_CIRCLE, "Circle", ""},
	{3, "UVSPHERE", ICON_MESH_UVSPHERE, "UVsphere", ""},
	{4, "ICOSPHERE", ICON_MESH_ICOSPHERE, "Icosphere", ""},
	{5, "CYLINDER", ICON_MESH_TUBE, "Cylinder", ""},
	{6, "CONE", ICON_MESH_CONE, "Cone", ""},
	{0, "", 0, NULL, NULL},
	{7, "GRID", ICON_MESH_GRID, "Grid", ""},
	{8, "MONKEY", ICON_MESH_MONKEY, "Monkey", ""},
	{0, NULL, 0, NULL, NULL}
};

static int object_add_mesh_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	int newob= 0;
	
	if(obedit==NULL || obedit->type!=OB_MESH) {
		object_add_type(C, OB_MESH);
		ED_object_enter_editmode(C, EM_DO_UNDO);
		newob = 1;
	}
	else DAG_id_flush_update(&obedit->id, OB_RECALC_DATA);

	switch(RNA_enum_get(op->ptr, "type")) {
		case 0:
			WM_operator_name_call(C, "MESH_OT_primitive_plane_add", WM_OP_INVOKE_REGION_WIN, NULL);
			break;
		case 1:
			WM_operator_name_call(C, "MESH_OT_primitive_cube_add", WM_OP_INVOKE_REGION_WIN, NULL);
			break;
		case 2:
			WM_operator_name_call(C, "MESH_OT_primitive_circle_add", WM_OP_INVOKE_REGION_WIN, NULL);
			break;
		case 3:
			WM_operator_name_call(C, "MESH_OT_primitive_uv_sphere_add", WM_OP_INVOKE_REGION_WIN, NULL);
			break;
		case 4:
			WM_operator_name_call(C, "MESH_OT_primitive_ico_sphere_add", WM_OP_INVOKE_REGION_WIN, NULL);
			break;
		case 5:
			WM_operator_name_call(C, "MESH_OT_primitive_cylinder_add", WM_OP_INVOKE_REGION_WIN, NULL);
			break;
		case 6:
			WM_operator_name_call(C, "MESH_OT_primitive_cone_add", WM_OP_INVOKE_REGION_WIN, NULL);
			break;
		case 7:
			WM_operator_name_call(C, "MESH_OT_primitive_grid_add", WM_OP_INVOKE_REGION_WIN, NULL);
			break;
		case 8:
			WM_operator_name_call(C, "MESH_OT_primitive_monkey_add", WM_OP_INVOKE_REGION_WIN, NULL);
			break;
	}
	/* userdef */
	if (newob && (U.flag & USER_ADD_EDITMODE)==0) {
		ED_object_exit_editmode(C, EM_FREEDATA);
	}
	
	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, obedit);
	
	return OPERATOR_FINISHED;
}


void OBJECT_OT_mesh_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Mesh";
	ot->description = "Add a mesh object to the scene.";
	ot->idname= "OBJECT_OT_mesh_add";
	
	/* api callbacks */
	ot->invoke= WM_menu_invoke;
	ot->exec= object_add_mesh_exec;
	
	ot->poll= ED_operator_scene_editable;
	
	/* flags: no register or undo, this operator calls operators */
	ot->flag= 0; //OPTYPE_REGISTER|OPTYPE_UNDO;
	
	RNA_def_enum(ot->srna, "type", prop_mesh_types, 0, "Primitive", "");
}

static EnumPropertyItem prop_curve_types[] = {
	{CU_BEZIER|CU_PRIM_CURVE, "BEZIER_CURVE", ICON_CURVE_BEZCURVE, "Bezier Curve", ""},
	{CU_BEZIER|CU_PRIM_CIRCLE, "BEZIER_CIRCLE", ICON_CURVE_BEZCIRCLE, "Bezier Circle", ""},
	{CU_NURBS|CU_PRIM_CURVE, "NURBS_CURVE", ICON_CURVE_NCURVE, "NURBS Curve", ""},
	{CU_NURBS|CU_PRIM_CIRCLE, "NURBS_CIRCLE", ICON_CURVE_NCIRCLE, "NURBS Circle", ""},
	{CU_NURBS|CU_PRIM_PATH, "PATH", ICON_CURVE_PATH, "Path", ""},
	{0, NULL, 0, NULL, NULL}
};

static int object_add_curve_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	ListBase *editnurb;
	Nurb *nu;
	int newob= 0;
	
	if(obedit==NULL || obedit->type!=OB_CURVE) {
		object_add_type(C, OB_CURVE);
		ED_object_enter_editmode(C, 0);
		newob = 1;
	}
	else DAG_id_flush_update(&obedit->id, OB_RECALC_DATA);
	
	obedit= CTX_data_edit_object(C);
	nu= add_nurbs_primitive(C, RNA_enum_get(op->ptr, "type"), newob);
	editnurb= curve_get_editcurve(obedit);
	BLI_addtail(editnurb, nu);
	
	/* userdef */
	if (newob && (U.flag & USER_ADD_EDITMODE)==0) {
		ED_object_exit_editmode(C, EM_FREEDATA);
	}
	
	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, obedit);
	
	return OPERATOR_FINISHED;
}

static int object_add_curve_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	Object *obedit= CTX_data_edit_object(C);
	uiPopupMenu *pup;
	uiLayout *layout;

	pup= uiPupMenuBegin(C, op->type->name, 0);
	layout= uiPupMenuLayout(pup);
	if(!obedit || obedit->type == OB_CURVE)
		uiItemsEnumO(layout, op->type->idname, "type");
	else
		uiItemsEnumO(layout, "OBJECT_OT_surface_add", "type");
	uiPupMenuEnd(C, pup);

	return OPERATOR_CANCELLED;
}

void OBJECT_OT_curve_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Curve";
	ot->description = "Add a curve object to the scene.";
	ot->idname= "OBJECT_OT_curve_add";
	
	/* api callbacks */
	ot->invoke= object_add_curve_invoke;
	ot->exec= object_add_curve_exec;
	
	ot->poll= ED_operator_scene_editable;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	RNA_def_enum(ot->srna, "type", prop_curve_types, 0, "Primitive", "");
}

static EnumPropertyItem prop_surface_types[]= {
	{CU_PRIM_CURVE|CU_NURBS, "NURBS_CURVE", ICON_SURFACE_NCURVE, "NURBS Curve", ""},
	{CU_PRIM_CIRCLE|CU_NURBS, "NURBS_CIRCLE", ICON_SURFACE_NCIRCLE, "NURBS Circle", ""},
	{CU_PRIM_PATCH|CU_NURBS, "NURBS_SURFACE", ICON_SURFACE_NSURFACE, "NURBS Surface", ""},
	{CU_PRIM_TUBE|CU_NURBS, "NURBS_TUBE", ICON_SURFACE_NTUBE, "NURBS Tube", ""},
	{CU_PRIM_SPHERE|CU_NURBS, "NURBS_SPHERE", ICON_SURFACE_NSPHERE, "NURBS Sphere", ""},
	{CU_PRIM_DONUT|CU_NURBS, "NURBS_DONUT", ICON_SURFACE_NDONUT, "NURBS Donut", ""},
	{0, NULL, 0, NULL, NULL}
};

static int object_add_surface_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	ListBase *editnurb;
	Nurb *nu;
	int newob= 0;
	
	if(obedit==NULL || obedit->type!=OB_SURF) {
		object_add_type(C, OB_SURF);
		ED_object_enter_editmode(C, 0);
		newob = 1;
	}
	else DAG_id_flush_update(&obedit->id, OB_RECALC_DATA);
	
	obedit= CTX_data_edit_object(C);
	nu= add_nurbs_primitive(C, RNA_enum_get(op->ptr, "type"), newob);
	editnurb= curve_get_editcurve(obedit);
	BLI_addtail(editnurb, nu);
	
	/* userdef */
	if (newob && (U.flag & USER_ADD_EDITMODE)==0) {
		ED_object_exit_editmode(C, EM_FREEDATA);
	}
	
	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, obedit);
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_surface_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Surface";
	ot->description = "Add a surface object to the scene.";
	ot->idname= "OBJECT_OT_surface_add";
	
	/* api callbacks */
	ot->invoke= WM_menu_invoke;
	ot->exec= object_add_surface_exec;
	
	ot->poll= ED_operator_scene_editable;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	RNA_def_enum(ot->srna, "type", prop_surface_types, 0, "Primitive", "");
}

static EnumPropertyItem prop_metaball_types[]= {
	{MB_BALL, "MBALL_BALL", ICON_META_BALL, "Meta Ball", ""},
	{MB_TUBE, "MBALL_TUBE", ICON_META_TUBE, "Meta Tube", ""},
	{MB_PLANE, "MBALL_PLANE", ICON_META_PLANE, "Meta Plane", ""},
	{MB_CUBE, "MBALL_CUBE", ICON_META_CUBE, "Meta Cube", ""},
	{MB_ELIPSOID, "MBALL_ELLIPSOID", ICON_META_ELLIPSOID, "Meta Ellipsoid", ""},
	{0, NULL, 0, NULL, NULL}
};

static int object_metaball_add_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	MetaBall *mball;
	MetaElem *elem;
	int newob= 0;
	
	if(obedit==NULL || obedit->type!=OB_MBALL) {
		object_add_type(C, OB_MBALL);
		ED_object_enter_editmode(C, 0);
		newob = 1;
	}
	else DAG_id_flush_update(&obedit->id, OB_RECALC_DATA);
	
	obedit= CTX_data_edit_object(C);
	elem= (MetaElem*)add_metaball_primitive(C, RNA_enum_get(op->ptr, "type"), newob);
	mball= (MetaBall*)obedit->data;
	BLI_addtail(mball->editelems, elem);
	
	/* userdef */
	if (newob && (U.flag & USER_ADD_EDITMODE)==0) {
		ED_object_exit_editmode(C, EM_FREEDATA);
	}
	
	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, obedit);
	
	return OPERATOR_FINISHED;
}

static int object_metaball_add_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	Object *obedit= CTX_data_edit_object(C);
	uiPopupMenu *pup;
	uiLayout *layout;

	pup= uiPupMenuBegin(C, op->type->name, 0);
	layout= uiPupMenuLayout(pup);
	if(!obedit || obedit->type == OB_MBALL)
		uiItemsEnumO(layout, op->type->idname, "type");
	else
		uiItemsEnumO(layout, "OBJECT_OT_metaball_add", "type");
	uiPupMenuEnd(C, pup);

	return OPERATOR_CANCELLED;
}

void OBJECT_OT_metaball_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Metaball";
	ot->description= "Add an metaball object to the scene.";
	ot->idname= "OBJECT_OT_metaball_add";

	/* api callbacks */
	ot->invoke= object_metaball_add_invoke;
	ot->exec= object_metaball_add_exec;
	ot->poll= ED_operator_scene_editable;

	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	RNA_def_enum(ot->srna, "type", prop_metaball_types, 0, "Primitive", "");
}
static int object_add_text_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	
	if(obedit && obedit->type==OB_FONT)
		return OPERATOR_CANCELLED;

	object_add_type(C, OB_FONT);
	obedit= CTX_data_active_object(C);

	if(U.flag & USER_ADD_EDITMODE)
		ED_object_enter_editmode(C, 0);
	
	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, obedit);
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_text_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Text";
	ot->description = "Add a text object to the scene";
	ot->idname= "OBJECT_OT_text_add";
	
	/* api callbacks */
	ot->exec= object_add_text_exec;
	ot->poll= ED_operator_scene_editable;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int object_armature_add_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	View3D *v3d= CTX_wm_view3d(C);
	RegionView3D *rv3d= NULL;
	int newob= 0;
	
	if ((obedit==NULL) || (obedit->type != OB_ARMATURE)) {
		object_add_type(C, OB_ARMATURE);
		ED_object_enter_editmode(C, 0);
		newob = 1;
	}
	else DAG_id_flush_update(&obedit->id, OB_RECALC_DATA);
	
	if(v3d) 
		rv3d= CTX_wm_region(C)->regiondata;
	
	/* v3d and rv3d are allowed to be NULL */
	add_primitive_bone(CTX_data_scene(C), v3d, rv3d);

	/* userdef */
	if (newob && (U.flag & USER_ADD_EDITMODE)==0) {
		ED_object_exit_editmode(C, EM_FREEDATA);
	}
	
	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, obedit);
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_armature_add(wmOperatorType *ot)
{	
	/* identifiers */
	ot->name= "Add Armature";
	ot->description = "Add an armature object to the scene.";
	ot->idname= "OBJECT_OT_armature_add";
	
	/* api callbacks */
	ot->exec= object_armature_add_exec;
	ot->poll= ED_operator_scene_editable;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int object_lamp_add_exec(bContext *C, wmOperator *op)
{
	Object *ob;
	int type= RNA_enum_get(op->ptr, "type");

	ob= object_add_type(C, OB_LAMP);
	if(ob && ob->data)
		((Lamp*)ob->data)->type= type;
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_lamp_add(wmOperatorType *ot)
{	
	static EnumPropertyItem lamp_type_items[] = {
		{LA_LOCAL, "POINT", ICON_LAMP_POINT, "Point", "Omnidirectional point light source."},
		{LA_SUN, "SUN", ICON_LAMP_SUN, "Sun", "Constant direction parallel ray light source."},
		{LA_SPOT, "SPOT", ICON_LAMP_SPOT, "Spot", "Directional cone light source."},
		{LA_HEMI, "HEMI", ICON_LAMP_HEMI, "Hemi", "180 degree constant light source."},
		{LA_AREA, "AREA", ICON_LAMP_AREA, "Area", "Directional area light source."},
		{0, NULL, 0, NULL, NULL}};

	/* identifiers */
	ot->name= "Add Lamp";
	ot->description = "Add a lamp object to the scene.";
	ot->idname= "OBJECT_OT_lamp_add";
	
	/* api callbacks */
	ot->invoke= WM_menu_invoke;
	ot->exec= object_lamp_add_exec;
	ot->poll= ED_operator_scene_editable;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* properties */
	RNA_def_enum(ot->srna, "type", lamp_type_items, 0, "Type", "");
}

static int object_primitive_add_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	uiPopupMenu *pup= uiPupMenuBegin(C, "Add Object", 0);
	uiLayout *layout= uiPupMenuLayout(pup);
	
	uiItemMenuEnumO(layout, "Mesh", ICON_OUTLINER_OB_MESH, "OBJECT_OT_mesh_add", "type");
	uiItemMenuEnumO(layout, "Curve", ICON_OUTLINER_OB_CURVE, "OBJECT_OT_curve_add", "type");
	uiItemMenuEnumO(layout, "Surface", ICON_OUTLINER_OB_SURFACE, "OBJECT_OT_surface_add", "type");
	uiItemMenuEnumO(layout, "Metaball", ICON_OUTLINER_OB_META, "OBJECT_OT_metaball_add", "type");
	uiItemO(layout, "Text", ICON_OUTLINER_OB_FONT, "OBJECT_OT_text_add");
	uiItemS(layout);
	uiItemO(layout, "Armature", ICON_OUTLINER_OB_ARMATURE, "OBJECT_OT_armature_add");
	uiItemEnumO(layout, NULL, ICON_OUTLINER_OB_LATTICE, "OBJECT_OT_add", "type", OB_LATTICE);
	uiItemEnumO(layout, NULL, ICON_OUTLINER_OB_EMPTY, "OBJECT_OT_add", "type", OB_EMPTY);
	uiItemS(layout);
	uiItemEnumO(layout, NULL, ICON_OUTLINER_OB_CAMERA, "OBJECT_OT_add", "type", OB_CAMERA);
	uiItemMenuEnumO(layout, "Lamp", ICON_OUTLINER_OB_LAMP, "OBJECT_OT_lamp_add", "type");
	
	uiPupMenuEnd(C, pup);
	
	/* this operator is only for a menu, not used further */
	return OPERATOR_CANCELLED;
}

/* only used as menu */
void OBJECT_OT_primitive_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Primitive";
	ot->description = "Add a primitive object.";
	ot->idname= "OBJECT_OT_primitive_add";
	
	/* api callbacks */
	ot->invoke= object_primitive_add_invoke;
	
	ot->poll= ED_operator_scene_editable;
	
	/* flags */
	ot->flag= 0;
}

/**************************** Delete Object *************************/

/* remove base from a specific scene */
/* note: now unlinks constraints as well */
void ED_base_object_free_and_unlink(Scene *scene, Base *base)
{
	BLI_remlink(&scene->base, base);
	free_libblock_us(&G.main->object, base->object);
	if(scene->basact==base) scene->basact= NULL;
	MEM_freeN(base);
}

static int object_delete_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	int islamp= 0;
	
	if(CTX_data_edit_object(C)) 
		return OPERATOR_CANCELLED;
	
	CTX_DATA_BEGIN(C, Base*, base, selected_editable_bases) {

		if(base->object->type==OB_LAMP) islamp= 1;
		
		/* remove from current scene only */
		ED_base_object_free_and_unlink(scene, base);
	}
	CTX_DATA_END;

	if(islamp) reshadeall_displist(scene);	/* only frees displist */
	
	DAG_scene_sort(scene);
	ED_anim_dag_flush_update(C);
	
	WM_event_add_notifier(C, NC_SCENE|ND_OB_ACTIVE, CTX_data_scene(C));
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_delete(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Delete";
	ot->description = "Delete selected objects.";
	ot->idname= "OBJECT_OT_delete";
	
	/* api callbacks */
	ot->invoke= WM_operator_confirm;
	ot->exec= object_delete_exec;
	ot->poll= ED_operator_scene_editable;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/**************************** Copy Utilities ******************************/

static void copy_object__forwardModifierLinks(void *userData, Object *ob,
                                              ID **idpoin)
{
	/* this is copied from ID_NEW; it might be better to have a macro */
	if(*idpoin && (*idpoin)->newid) *idpoin = (*idpoin)->newid;
}

/* after copying objects, copied data should get new pointers */
static void copy_object_set_idnew(bContext *C, int dupflag)
{
	Object *ob;
	Material *ma, *mao;
	ID *id;
#if 0 // XXX old animation system
	Ipo *ipo;
	bActionStrip *strip;
#endif // XXX old animation system
	int a;
	
	/* XXX check object pointers */
	CTX_DATA_BEGIN(C, Base*, base, selected_editable_bases) {
		ob= base->object;
		relink_constraints(&ob->constraints);
		if (ob->pose){
			bPoseChannel *chan;
			for (chan = ob->pose->chanbase.first; chan; chan=chan->next){
				relink_constraints(&chan->constraints);
			}
		}
		modifiers_foreachIDLink(ob, copy_object__forwardModifierLinks, NULL);
		ID_NEW(ob->parent);
		ID_NEW(ob->track);
		ID_NEW(ob->proxy);
		ID_NEW(ob->proxy_group);
		
#if 0 // XXX old animation system
		for(strip= ob->nlastrips.first; strip; strip= strip->next) {
			bActionModifier *amod;
			for(amod= strip->modifiers.first; amod; amod= amod->next)
				ID_NEW(amod->ob);
		}
#endif // XXX old animation system
	}
	CTX_DATA_END;
	
	/* materials */
	if( dupflag & USER_DUP_MAT) {
		mao= G.main->mat.first;
		while(mao) {
			if(mao->id.newid) {
				
				ma= (Material *)mao->id.newid;
				
				if(dupflag & USER_DUP_TEX) {
					for(a=0; a<MAX_MTEX; a++) {
						if(ma->mtex[a]) {
							id= (ID *)ma->mtex[a]->tex;
							if(id) {
								ID_NEW_US(ma->mtex[a]->tex)
								else ma->mtex[a]->tex= copy_texture(ma->mtex[a]->tex);
								id->us--;
							}
						}
					}
				}
#if 0 // XXX old animation system
				id= (ID *)ma->ipo;
				if(id) {
					ID_NEW_US(ma->ipo)
					else ma->ipo= copy_ipo(ma->ipo);
					id->us--;
				}
#endif // XXX old animation system
			}
			mao= mao->id.next;
		}
	}
	
#if 0 // XXX old animation system
	/* lamps */
	if( dupflag & USER_DUP_IPO) {
		Lamp *la= G.main->lamp.first;
		while(la) {
			if(la->id.newid) {
				Lamp *lan= (Lamp *)la->id.newid;
				id= (ID *)lan->ipo;
				if(id) {
					ID_NEW_US(lan->ipo)
					else lan->ipo= copy_ipo(lan->ipo);
					id->us--;
				}
			}
			la= la->id.next;
		}
	}
	
	/* ipos */
	ipo= G.main->ipo.first;
	while(ipo) {
		if(ipo->id.lib==NULL && ipo->id.newid) {
			Ipo *ipon= (Ipo *)ipo->id.newid;
			IpoCurve *icu;
			for(icu= ipon->curve.first; icu; icu= icu->next) {
				if(icu->driver) {
					ID_NEW(icu->driver->ob);
				}
			}
		}
		ipo= ipo->id.next;
	}
#endif // XXX old animation system
	
	set_sca_new_poins();
	
	clear_id_newpoins();
}

/********************* Make Duplicates Real ************************/

static void make_object_duplilist_real(bContext *C, Scene *scene, Base *base)
{
	Base *basen;
	Object *ob;
	ListBase *lb;
	DupliObject *dob;
	
	if(!base && !(base = BASACT))
		return;
	
	if(!(base->object->transflag & OB_DUPLI))
		return;
	
	lb= object_duplilist(scene, base->object);
	
	for(dob= lb->first; dob; dob= dob->next) {
		ob= copy_object(dob->ob);
		/* font duplis can have a totcol without material, we get them from parent
		* should be implemented better...
		*/
		if(ob->mat==NULL) ob->totcol= 0;
		
		basen= MEM_dupallocN(base);
		basen->flag &= ~OB_FROMDUPLI;
		BLI_addhead(&scene->base, basen);	/* addhead: othwise eternal loop */
		basen->object= ob;
		ob->ipo= NULL;		/* make sure apply works */
		ob->parent= ob->track= NULL;
		ob->disp.first= ob->disp.last= NULL;
		ob->transflag &= ~OB_DUPLI;	
		
		Mat4CpyMat4(ob->obmat, dob->mat);
		ED_object_apply_obmat(ob);
	}
	
	copy_object_set_idnew(C, 0);
	
	free_object_duplilist(lb);
	
	base->object->transflag &= ~OB_DUPLI;	
}

static int object_duplicates_make_real_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	
	clear_id_newpoins();
		
	CTX_DATA_BEGIN(C, Base*, base, selected_editable_bases) {
		make_object_duplilist_real(C, scene, base);
	}
	CTX_DATA_END;

	DAG_scene_sort(scene);
	ED_anim_dag_flush_update(C);	
	WM_event_add_notifier(C, NC_SCENE, scene);
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_duplicates_make_real(wmOperatorType *ot)
{
	
	/* identifiers */
	ot->name= "Make Duplicates Real";
	ot->description = "Make dupli objects attached to this object real.";
	ot->idname= "OBJECT_OT_duplicates_make_real";
	
	/* api callbacks */
	ot->invoke= WM_operator_confirm;
	ot->exec= object_duplicates_make_real_exec;
	
	ot->poll= ED_operator_scene_editable;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/**************************** Convert **************************/

static EnumPropertyItem convert_target_items[]= {
	{OB_CURVE, "CURVE", 0, "Curve", ""},
	{OB_MESH, "MESH", 0, "Mesh", ""},
	{0, NULL, 0, NULL, NULL}};

static void curvetomesh(Scene *scene, Object *ob) 
{
	Curve *cu= ob->data;
	
	if(cu->disp.first==0)
		makeDispListCurveTypes(scene, ob, 0); /* force creation */

	nurbs_to_mesh(ob); /* also does users */

	if(ob->type == OB_MESH)
		object_free_modifiers(ob);
}

static int convert_poll(bContext *C)
{
	Object *obact= CTX_data_active_object(C);
	Scene *scene= CTX_data_scene(C);

	return (!scene->id.lib && obact && scene->obedit != obact && (obact->flag & SELECT));
}

static int convert_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	Base *basen=NULL, *basact=NULL, *basedel=NULL;
	Object *ob, *ob1, *obact= CTX_data_active_object(C);
	DerivedMesh *dm;
	Curve *cu;
	Nurb *nu;
	MetaBall *mb;
	Mesh *me;
	int target= RNA_enum_get(op->ptr, "target");
	int keep_original= RNA_boolean_get(op->ptr, "keep_original");
	int a;
	
	/* don't forget multiple users! */

	/* reset flags */
	CTX_DATA_BEGIN(C, Base*, base, selected_editable_bases) {
		ob= base->object;
		ob->flag &= ~OB_DONE;
	}
	CTX_DATA_END;

	CTX_DATA_BEGIN(C, Base*, base, selected_editable_bases) {
		ob= base->object;
		
		if(ob->flag & OB_DONE)
			continue;
		else if(ob->type==OB_MESH && ob->modifiers.first) { /* converting a mesh with no modifiers causes a segfault */
			ob->flag |= OB_DONE;
			basedel = base;

			ob1= copy_object(ob);
			ob1->recalc |= OB_RECALC;

			basen= MEM_mallocN(sizeof(Base), "duplibase");
			*basen= *base;
			BLI_addhead(&scene->base, basen);	/* addhead: otherwise eternal loop */
			basen->object= ob1;
			basen->flag |= SELECT;
			base->flag &= ~SELECT;
			ob->flag &= ~SELECT;

			/* decrement original mesh's usage count  */
			me= ob1->data;
			me->id.us--;

			/* make a new copy of the mesh */
			ob1->data= copy_mesh(me);

			/* make new mesh data from the original copy */
			dm= mesh_get_derived_final(scene, ob1, CD_MASK_MESH);
			/* dm= mesh_create_derived_no_deform(ob1, NULL);	this was called original (instead of get_derived). man o man why! (ton) */
			
			DM_to_mesh(dm, ob1->data);

			dm->release(dm);
			object_free_modifiers(ob1);	/* after derivedmesh calls! */
		}
		else if(ob->type==OB_FONT) {
			ob->flag |= OB_DONE;

			ob->type= OB_CURVE;
			cu= ob->data;

			if(cu->vfont) {
				cu->vfont->id.us--;
				cu->vfont= 0;
			}
			if(cu->vfontb) {
				cu->vfontb->id.us--;
				cu->vfontb= 0;
			}
			if(cu->vfonti) {
				cu->vfonti->id.us--;
				cu->vfonti= 0;
			}
			if(cu->vfontbi) {
				cu->vfontbi->id.us--;
				cu->vfontbi= 0;
			}					
			/* other users */
			if(cu->id.us>1) {
				for(ob1= G.main->object.first; ob1; ob1=ob1->id.next) {
					if(ob1->data==cu) {
						ob1->type= OB_CURVE;
						ob1->recalc |= OB_RECALC;
					}
				}
			}

			for(nu=cu->nurb.first; nu; nu=nu->next)
				nu->charidx= 0;

			if(target == OB_MESH)
				curvetomesh(scene, ob);
		}
		else if(ELEM(ob->type, OB_CURVE, OB_SURF)) {
			ob->flag |= OB_DONE;

			if(target == OB_MESH)
				curvetomesh(scene, ob);
		}
		else if(ob->type==OB_MBALL) {
			ob= find_basis_mball(scene, ob);
			
			if(ob->disp.first && !(ob->flag & OB_DONE)) {
				ob->flag |= OB_DONE;
				basedel = base;

				ob1= copy_object(ob);
				ob1->recalc |= OB_RECALC;

				basen= MEM_mallocN(sizeof(Base), "duplibase");
				*basen= *base;
				BLI_addhead(&scene->base, basen);	/* addhead: otherwise eternal loop */
				basen->object= ob1;
				basen->flag |= SELECT;
				basedel->flag &= ~SELECT;
				ob->flag &= ~SELECT;
				
				mb= ob1->data;
				mb->id.us--;
				
				ob1->data= add_mesh("Mesh");
				ob1->type= OB_MESH;
				
				me= ob1->data;
				me->totcol= mb->totcol;
				if(ob1->totcol) {
					me->mat= MEM_dupallocN(mb->mat);
					for(a=0; a<ob1->totcol; a++) id_us_plus((ID *)me->mat[a]);
				}
				
				mball_to_mesh(&ob->disp, ob1->data);
				
				/* So we can see the wireframe */
				BASACT= basen; // XXX hm
			}
			else
				continue;
		}
		else
			continue;

		/* If the original object is active then make this object active */
		if(basen) {
			if(ob == obact) {
				ED_base_object_activate(C, basen);
				basact = basen;
			}

			basen= NULL;
		}

		/* delete original if needed */
		if(basedel) {
			if(!keep_original)
				ED_base_object_free_and_unlink(scene, basedel);	

			basedel = NULL;
		}
	}
	CTX_DATA_END;
	
	/* delete object should renew depsgraph */
	if(!keep_original)
		DAG_scene_sort(scene);

	/* texspace and normals */
	if(!basen) BASACT= NULL; // XXX base;

// XXX	ED_object_enter_editmode(C, 0);
// XXX	exit_editmode(C, EM_FREEDATA|EM_WAITCURSOR); /* freedata, but no undo */
	BASACT= basact;

	DAG_scene_sort(scene);
	WM_event_add_notifier(C, NC_SCENE, scene);

	return OPERATOR_FINISHED;
}

static int convert_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	Object *obact= CTX_data_active_object(C);
	uiPopupMenu *pup;
	uiLayout *layout;
	char *title;

	if(obact->type==OB_FONT) {
		pup= uiPupMenuBegin(C, "Convert Font to", 0);
		layout= uiPupMenuLayout(pup);

		uiItemEnumO(layout, "Curve", 0, op->type->idname, "target", OB_CURVE);
	}
	else {
		if(obact->type == OB_MBALL)
			title= "Convert Metaball to";
		else if(obact->type == OB_CURVE)
			title= "Convert Curve to";
		else if(obact->type == OB_SURF)
			title= "Convert Nurbs Surface to";
		else if(obact->type == OB_MESH)
			title= "Convert Modifiers to";
		else
			return OPERATOR_CANCELLED;

		pup= uiPupMenuBegin(C, title, 0);
		layout= uiPupMenuLayout(pup);
	}

	uiItemBooleanO(layout, "Mesh (keep original)", 0, op->type->idname, "keep_original", 1);
	uiItemBooleanO(layout, "Mesh (delete original)", 0, op->type->idname, "keep_original", 0);

	uiPupMenuEnd(C, pup);

	return OPERATOR_CANCELLED;
}

void OBJECT_OT_convert(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Convert";
	ot->description = "Convert selected objects to another type.";
	ot->idname= "OBJECT_OT_convert";
	
	/* api callbacks */
	ot->invoke= convert_invoke;
	ot->exec= convert_exec;
	ot->poll= convert_poll;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* properties */
	RNA_def_enum(ot->srna, "target", convert_target_items, OB_MESH, "Target", "Type of object to convert to.");
	RNA_def_boolean(ot->srna, "keep_original", 0, "Keep Original", "Keep original objects instead of replacing them.");
}

/**************************** Duplicate ************************/

/* 
	dupflag: a flag made from constants declared in DNA_userdef_types.h
	The flag tells adduplicate() weather to copy data linked to the object, or to reference the existing data.
	U.dupflag for default operations or you can construct a flag as python does
	if the dupflag is 0 then no data will be copied (linked duplicate) */

/* used below, assumes id.new is correct */
/* leaves selection of base/object unaltered */
static Base *object_add_duplicate_internal(Scene *scene, Base *base, int dupflag)
{
	Base *basen= NULL;
	Material ***matarar;
	Object *ob, *obn;
	ID *id;
	int a, didit;

	ob= base->object;
	if(ob->mode & OB_MODE_POSE) {
		; /* nothing? */
	}
	else {
		obn= copy_object(ob);
		obn->recalc |= OB_RECALC;
		
		basen= MEM_mallocN(sizeof(Base), "duplibase");
		*basen= *base;
		BLI_addhead(&scene->base, basen);	/* addhead: prevent eternal loop */
		basen->object= obn;
		
		if(basen->flag & OB_FROMGROUP) {
			Group *group;
			for(group= G.main->group.first; group; group= group->id.next) {
				if(object_in_group(ob, group))
					add_to_group(group, obn);
			}
			obn->flag |= OB_FROMGROUP; /* this flag is unset with copy_object() */
		}
		
		/* duplicates using userflags */
#if 0 // XXX old animation system				
		if(dupflag & USER_DUP_IPO) {
			bConstraintChannel *chan;
			id= (ID *)obn->ipo;
			
			if(id) {
				ID_NEW_US( obn->ipo)
				else obn->ipo= copy_ipo(obn->ipo);
				id->us--;
			}
			/* Handle constraint ipos */
			for (chan=obn->constraintChannels.first; chan; chan=chan->next){
				id= (ID *)chan->ipo;
				if(id) {
					ID_NEW_US( chan->ipo)
					else chan->ipo= copy_ipo(chan->ipo);
					id->us--;
				}
			}
		}
		if(dupflag & USER_DUP_ACT){ /* Not buttons in the UI to modify this, add later? */
			id= (ID *)obn->action;
			if (id){
				ID_NEW_US(obn->action)
				else{
					obn->action= copy_action(obn->action);
				}
				id->us--;
			}
		}
#endif // XXX old animation system
		if(dupflag & USER_DUP_MAT) {
			for(a=0; a<obn->totcol; a++) {
				id= (ID *)obn->mat[a];
				if(id) {
					ID_NEW_US(obn->mat[a])
					else obn->mat[a]= copy_material(obn->mat[a]);
					id->us--;
				}
			}
		}
		if(dupflag & USER_DUP_PSYS) {
			ParticleSystem *psys;
			for(psys=obn->particlesystem.first; psys; psys=psys->next) {
				id= (ID*) psys->part;
				if(id) {
					ID_NEW_US(psys->part)
					else psys->part= psys_copy_settings(psys->part);
					id->us--;
				}
			}
		}
		
		id= obn->data;
		didit= 0;
		
		switch(obn->type) {
			case OB_MESH:
				if(dupflag & USER_DUP_MESH) {
					ID_NEW_US2( obn->data )
					else {
						obn->data= copy_mesh(obn->data);
						
						if(obn->fluidsimSettings) {
							obn->fluidsimSettings->orgMesh = (Mesh *)obn->data;
						}
						
						didit= 1;
					}
					id->us--;
				}
				break;
			case OB_CURVE:
				if(dupflag & USER_DUP_CURVE) {
					ID_NEW_US2(obn->data )
					else {
						obn->data= copy_curve(obn->data);
						didit= 1;
					}
					id->us--;
				}
				break;
			case OB_SURF:
				if(dupflag & USER_DUP_SURF) {
					ID_NEW_US2( obn->data )
					else {
						obn->data= copy_curve(obn->data);
						didit= 1;
					}
					id->us--;
				}
				break;
			case OB_FONT:
				if(dupflag & USER_DUP_FONT) {
					ID_NEW_US2( obn->data )
					else {
						obn->data= copy_curve(obn->data);
						didit= 1;
					}
					id->us--;
				}
				break;
			case OB_MBALL:
				if(dupflag & USER_DUP_MBALL) {
					ID_NEW_US2(obn->data )
					else {
						obn->data= copy_mball(obn->data);
						didit= 1;
					}
					id->us--;
				}
				break;
			case OB_LAMP:
				if(dupflag & USER_DUP_LAMP) {
					ID_NEW_US2(obn->data )
					else obn->data= copy_lamp(obn->data);
					id->us--;
				}
				break;
				
			case OB_ARMATURE:
				obn->recalc |= OB_RECALC_DATA;
				if(obn->pose) obn->pose->flag |= POSE_RECALC;
					
					if(dupflag & USER_DUP_ARM) {
						ID_NEW_US2(obn->data )
						else {
							obn->data= copy_armature(obn->data);
							armature_rebuild_pose(obn, obn->data);
							didit= 1;
						}
						id->us--;
					}
						
						break;
				
			case OB_LATTICE:
				if(dupflag!=0) {
					ID_NEW_US2(obn->data )
					else obn->data= copy_lattice(obn->data);
					id->us--;
				}
				break;
			case OB_CAMERA:
				if(dupflag!=0) {
					ID_NEW_US2(obn->data )
					else obn->data= copy_camera(obn->data);
					id->us--;
				}
				break;
		}
		
		if(dupflag & USER_DUP_MAT) {
			matarar= give_matarar(obn);
			if(didit && matarar) {
				for(a=0; a<obn->totcol; a++) {
					id= (ID *)(*matarar)[a];
					if(id) {
						ID_NEW_US( (*matarar)[a] )
						else (*matarar)[a]= copy_material((*matarar)[a]);
						
						id->us--;
					}
				}
			}
		}
	}
	return basen;
}

/* single object duplicate, if dupflag==0, fully linked, else it uses the flags given */
/* leaves selection of base/object unaltered */
Base *ED_object_add_duplicate(Scene *scene, Base *base, int dupflag)
{
	Base *basen;

	clear_id_newpoins();
	clear_sca_new_poins();	/* sensor/contr/act */
	
	basen= object_add_duplicate_internal(scene, base, dupflag);
	
	DAG_scene_sort(scene);
	
	return basen;
}

/* contextual operator dupli */
static int duplicate_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	int linked= RNA_boolean_get(op->ptr, "linked");
	int dupflag= (linked)? 0: U.dupflag;
	
	clear_id_newpoins();
	clear_sca_new_poins();	/* sensor/contr/act */
	
	CTX_DATA_BEGIN(C, Base*, base, selected_editable_bases) {
		Base *basen= object_add_duplicate_internal(scene, base, dupflag);
		
		/* note that this is safe to do with this context iterator,
		   the list is made in advance */
		ED_base_object_select(base, BA_DESELECT);

		/* new object becomes active */
		if(BASACT==base)
			ED_base_object_activate(C, basen);
		
	}
	CTX_DATA_END;

	copy_object_set_idnew(C, dupflag);

	DAG_scene_sort(scene);
	ED_anim_dag_flush_update(C);	

	WM_event_add_notifier(C, NC_SCENE|ND_OB_SELECT, scene);

	return OPERATOR_FINISHED;
}

void OBJECT_OT_duplicate(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Duplicate";
	ot->description = "Duplicate selected objects.";
	ot->idname= "OBJECT_OT_duplicate";
	
	/* api callbacks */
	ot->exec= duplicate_exec;
	ot->poll= ED_operator_scene_editable;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* to give to transform */
	RNA_def_boolean(ot->srna, "linked", 0, "Linked", "Duplicate object but not object data, linking to the original data.");
	RNA_def_int(ot->srna, "mode", TFM_TRANSLATION, 0, INT_MAX, "Mode", "", 0, INT_MAX);
}

/**************************** Join *************************/

static int join_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_active_object(C);

	if(scene->obedit) {
		BKE_report(op->reports, RPT_ERROR, "This data does not support joining in editmode.");
		return OPERATOR_CANCELLED;
	}
	else if(!ob) {
		BKE_report(op->reports, RPT_ERROR, "Can't join unless there is an active object.");
		return OPERATOR_CANCELLED;
	}
	else if(object_data_is_libdata(ob)) {
		BKE_report(op->reports, RPT_ERROR, "Can't edit external libdata.");
		return OPERATOR_CANCELLED;
	}

	if(ob->type == OB_MESH)
		return join_mesh_exec(C, op);
	else if(ELEM(ob->type, OB_CURVE, OB_SURF))
		return join_curve_exec(C, op);
	else if(ob->type == OB_ARMATURE)
		return join_armature_exec(C, op);

	BKE_report(op->reports, RPT_ERROR, "This object type doesn't support joining.");

	return OPERATOR_CANCELLED;
}

void OBJECT_OT_join(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Join";
	ot->description = "Join selected objects into active object.";
	ot->idname= "OBJECT_OT_join";
	
	/* api callbacks */
	ot->exec= join_exec;
	ot->poll= ED_operator_scene_editable;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

