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
 * The Original Code is Copyright (C) 2013 Blender Foundation
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Joshua Leung, Sergej Reich
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file rigidbody_object.c
 *  \ingroup editor_physics
 *  \brief Rigid Body object editing operators
 */

#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_group_types.h"
#include "DNA_object_types.h"
#include "DNA_mesh_types.h"
#include "DNA_rigidbody_types.h"
#include "DNA_scene_types.h"

#include "BLI_blenlib.h"
#include "BLI_math.h"

#include "BLF_translation.h"

#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_global.h"
#include "BKE_group.h"
#include "BKE_object.h"
#include "BKE_report.h"
#include "BKE_rigidbody.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_physics.h"
#include "ED_screen.h"

#include "physics_intern.h"

/* ********************************************** */
/* Helper API's for RigidBody Objects Editing */

static int ED_operator_rigidbody_active_poll(bContext *C)
{
	if (ED_operator_object_active_editable(C)) {
		Object *ob = CTX_data_active_object(C);
		return (ob && ob->rigidbody_object);
	}
	else
		return 0;
}

static int ED_operator_rigidbody_add_poll(bContext *C)
{
	if (ED_operator_object_active_editable(C)) {
		Object *ob = CTX_data_active_object(C);
		return (ob && ob->type == OB_MESH);
	}
	else
		return 0;
}

/* ----------------- */

void ED_rigidbody_ob_add(wmOperator *op, Scene *scene, Object *ob, int type)
{
	RigidBodyWorld *rbw = BKE_rigidbody_get_world(scene);

	if (ob->type != OB_MESH) {
		BKE_report(op->reports, RPT_ERROR, "Can't add Rigid Body to non mesh object");
		return;
	}
	if (((Mesh *)ob->data)->totpoly == 0) {
		BKE_report(op->reports, RPT_ERROR, "Can't create Rigid Body from mesh with no polygons");
		return;
	}

	/* Add rigid body world and group if they don't exist for convenience */
	if (rbw == NULL) {
		rbw = BKE_rigidbody_create_world(scene);
		BKE_rigidbody_validate_sim_world(scene, rbw, false);
		scene->rigidbody_world = rbw;
	}
	if (rbw->group == NULL) {
		rbw->group = BKE_group_add(G.main, "RigidBodyWorld");
	}

	/* make rigidbody object settings */
	if (ob->rigidbody_object == NULL) {
		ob->rigidbody_object = BKE_rigidbody_create_object(scene, ob, type);
	}
	ob->rigidbody_object->type = type;
	ob->rigidbody_object->flag |= RBO_FLAG_NEEDS_VALIDATE;

	/* add object to rigid body group */
	BKE_group_object_add(rbw->group, ob, scene, NULL);

	DAG_id_tag_update(&ob->id, OB_RECALC_OB);
}

void ED_rigidbody_ob_remove(Scene *scene, Object *ob)
{
	RigidBodyWorld *rbw = BKE_rigidbody_get_world(scene);

	BKE_rigidbody_remove_object(scene, ob);
	if (rbw)
		BKE_group_object_unlink(rbw->group, ob, scene, NULL);

	DAG_id_tag_update(&ob->id, OB_RECALC_OB);
}

/* ********************************************** */
/* Active Object Add/Remove Operators */

/* ************ Add Rigid Body ************** */

static int rigidbody_ob_add_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *ob = (scene) ? OBACT : NULL;
	int type = RNA_enum_get(op->ptr, "type");

	/* apply to active object */
	ED_rigidbody_ob_add(op, scene, ob, type);

	/* send updates */
	WM_event_add_notifier(C, NC_OBJECT | ND_TRANSFORM, NULL);

	/* done */
	return OPERATOR_FINISHED;
}

void RIGIDBODY_OT_object_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->idname = "RIGIDBODY_OT_object_add";
	ot->name = "Add Rigid Body";
	ot->description = "Add active object as Rigid Body";

	/* callbacks */
	ot->exec = rigidbody_ob_add_exec;
	ot->poll = ED_operator_rigidbody_add_poll;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	ot->prop = RNA_def_enum(ot->srna, "type", rigidbody_ob_type_items, RBO_TYPE_ACTIVE, "Rigid Body Type", "");
}

/* ************ Remove Rigid Body ************** */

static int rigidbody_ob_remove_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *ob = (scene) ? OBACT : NULL;

	/* sanity checks */
	if (scene == NULL)
		return OPERATOR_CANCELLED;

	/* apply to active object */
	if (ELEM(NULL, ob, ob->rigidbody_object)) {
		BKE_report(op->reports, RPT_ERROR, "Object has no Rigid Body settings to remove");
		return OPERATOR_CANCELLED;
	}
	else
		ED_rigidbody_ob_remove(scene, ob);

	/* send updates */
	WM_event_add_notifier(C, NC_OBJECT | ND_TRANSFORM, NULL);

	/* done */
	return OPERATOR_FINISHED;
}

void RIGIDBODY_OT_object_remove(wmOperatorType *ot)
{
	/* identifiers */
	ot->idname = "RIGIDBODY_OT_object_remove";
	ot->name = "Remove Rigid Body";
	ot->description = "Remove Rigid Body settings from Object";

	/* callbacks */
	ot->exec = rigidbody_ob_remove_exec;
	ot->poll = ED_operator_rigidbody_active_poll;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* ********************************************** */
/* Selected Object Add/Remove Operators */

/* ************ Add Rigid Bodies ************** */

static int rigidbody_obs_add_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	int type = RNA_enum_get(op->ptr, "type");

	/* sanity check */
	if (scene == NULL) {
		BKE_report(op->reports, RPT_ERROR, "No Scene to add Rigid Bodies to");
		return OPERATOR_CANCELLED;
	}
	/* create rigid body objects and add them to the world's group */
	CTX_DATA_BEGIN(C, Object *, ob, selected_objects) {
		ED_rigidbody_ob_add(op, scene, ob, type);
	}
	CTX_DATA_END;

	/* send updates */
	WM_event_add_notifier(C, NC_OBJECT | ND_TRANSFORM, NULL);
	WM_event_add_notifier(C, NC_OBJECT | ND_POINTCACHE, NULL);

	/* done */
	return OPERATOR_FINISHED;
}

void RIGIDBODY_OT_objects_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->idname = "RIGIDBODY_OT_objects_add";
	ot->name = "Add Rigid Bodies";
	ot->description = "Add selected objects as Rigid Bodies";

	/* callbacks */
	ot->exec = rigidbody_obs_add_exec;
	ot->poll = ED_operator_rigidbody_add_poll;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	ot->prop = RNA_def_enum(ot->srna, "type", rigidbody_ob_type_items, RBO_TYPE_ACTIVE, "Rigid Body Type", "");
}

/* ************ Remove Rigid Bodies ************** */

static int rigidbody_obs_remove_exec(bContext *C, wmOperator *UNUSED(op))
{
	Scene *scene = CTX_data_scene(C);

	/* sanity checks */
	if (scene == NULL)
		return OPERATOR_CANCELLED;

	/* apply this to all selected objects... */
	CTX_DATA_BEGIN(C, Object *, ob, selected_objects)
	{
		if (ob->rigidbody_object) {
			ED_rigidbody_ob_remove(scene, ob);
		}
	}
	CTX_DATA_END;

	/* send updates */
	WM_event_add_notifier(C, NC_OBJECT | ND_POINTCACHE, NULL);

	/* done */
	return OPERATOR_FINISHED;
}

void RIGIDBODY_OT_objects_remove(wmOperatorType *ot)
{
	/* identifiers */
	ot->idname = "RIGIDBODY_OT_objects_remove";
	ot->name = "Remove Rigid Bodies";
	ot->description = "Remove selected objects from Rigid Body simulation";

	/* callbacks */
	ot->exec = rigidbody_obs_remove_exec;
	ot->poll = ED_operator_rigidbody_active_poll;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* ********************************************** */
/* Utility Operators */

/* ************ Change Collision Shapes ************** */

static int rigidbody_obs_shape_change_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	int shape = RNA_enum_get(op->ptr, "type");

	/* sanity checks */
	if (scene == NULL)
		return OPERATOR_CANCELLED;

	/* apply this to all selected objects... */
	CTX_DATA_BEGIN(C, Object *, ob, selected_objects)
	{
		if (ob->rigidbody_object) {
			PointerRNA ptr;

			/* use RNA-system to change the property and perform all necessary changes */
			RNA_pointer_create(&ob->id, &RNA_RigidBodyObject, ob->rigidbody_object, &ptr);
			RNA_enum_set(&ptr, "collision_shape", shape);

			DAG_id_tag_update(&ob->id, OB_RECALC_OB);
		}
	}
	CTX_DATA_END;

	/* send updates */
	WM_event_add_notifier(C, NC_OBJECT | ND_POINTCACHE, NULL);

	/* done */
	return OPERATOR_FINISHED;
}

void RIGIDBODY_OT_shape_change(wmOperatorType *ot)
{
	/* identifiers */
	ot->idname = "RIGIDBODY_OT_shape_change";
	ot->name = "Change Collision Shape";
	ot->description = "Change collision shapes for selected Rigid Body Objects";

	/* callbacks */
	ot->invoke = WM_menu_invoke;
	ot->exec = rigidbody_obs_shape_change_exec;
	ot->poll = ED_operator_rigidbody_active_poll;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	ot->prop = RNA_def_enum(ot->srna, "type", rigidbody_ob_shape_items, RB_SHAPE_TRIMESH, "Rigid Body Shape", "");
}

/* ************ Calculate Mass ************** */

/* Entry in material density table */
typedef struct rbMaterialDensityItem {
	const char *name;   /* Name of material */
	float density;      /* Density (kg/m^3) */
} rbMaterialDensityItem;

/* Preset density values for materials (kg/m^3)
 * Selected values obtained from:
 * 1) http://www.jaredzone.info/2010/09/densities.html
 * 2) http://www.avlandesign.com/density_construction.htm
 * 3) http://www.avlandesign.com/density_metal.htm
 */
static rbMaterialDensityItem RB_MATERIAL_DENSITY_TABLE[] = {
	{N_("Air"), 1.0f}, /* not quite; adapted from 1.43 for oxygen for use as default */
	{N_("Acrylic"), 1400.0f},
	{N_("Asphalt (Crushed)"), 721.0f},
	{N_("Bark"), 240.0f},
	{N_("Beans (Cocoa)"), 593.0f},
	{N_("Beans (Soy)"), 721.0f},
	{N_("Brick (Pressed)"), 2400.0f},
	{N_("Brick (Common)"), 2000.0f},
	{N_("Brick (Soft)"), 1600.0f},
	{N_("Brass"), 8216.0f},
	{N_("Bronze"), 8860.0f},
	{N_("Carbon (Solid)"), 2146.0f},
	{N_("Cardboard"), 689.0f},
	{N_("Cast Iron"), 7150.0f},
	/* {N_("Cement"), 1442.0f}, */
	{N_("Chalk (Solid)"), 2499.0f},
	/* {N_("Coffee (Fresh/Roast)"), ~500}, */
	{N_("Concrete"), 2320.0f},
	{N_("Charcoal"), 208.0f},
	{N_("Cork"), 240.0f},
	{N_("Copper"), 8933.0f},
	{N_("Garbage"), 481.0f},
	{N_("Glass (Broken)"), 1940.0f},
	{N_("Glass (Solid)"), 2190.0f},
	{N_("Gold"), 19282.0f},
	{N_("Granite (Broken)"), 1650.0f},
	{N_("Granite (Solid)"), 2691.0f},
	{N_("Gravel"), 2780.0f},
	{N_("Ice (Crushed)"), 593.0f},
	{N_("Ice (Solid)"), 919.0f},
	{N_("Iron"), 7874.0f},
	{N_("Lead"), 11342.0f},
	{N_("Limestone (Broken)"), 1554.0f},
	{N_("Limestone (Solid)"), 2611.0f},
	{N_("Marble (Broken)"), 1570.0f},
	{N_("Marble (Solid)"), 2563.0f},
	{N_("Paper"), 1201.0f},
	{N_("Peanuts (Shelled)"), 641.0f},
	{N_("Peanuts (Not Shelled)"), 272.0f},
	{N_("Plaster"), 849.0f},
	{N_("Plastic"), 1200.0f},
	{N_("Polystyrene"), 1050.0f},
	{N_("Rubber"), 1522.0f},
	{N_("Silver"), 10501.0f},
	{N_("Steel"), 7860.0f},
	{N_("Stone"), 2515.0f},
	{N_("Stone (Crushed)"), 1602.0f},
	{N_("Timber"), 610.0f}
};
static const int NUM_RB_MATERIAL_PRESETS = sizeof(RB_MATERIAL_DENSITY_TABLE) / sizeof(rbMaterialDensityItem);


/* dynamically generate list of items
 * - Although there is a runtime cost, this has a lower maintenance cost
 *   in the long run than other two-list solutions...
 */
static EnumPropertyItem *rigidbody_materials_itemf(bContext *UNUSED(C), PointerRNA *UNUSED(ptr), PropertyRNA *UNUSED(prop), int *free)
{
	EnumPropertyItem item_tmp = {0};
	EnumPropertyItem *item = NULL;
	int totitem = 0;
	int i = 0;

	/* add each preset to the list */
	for (i = 0; i < NUM_RB_MATERIAL_PRESETS; i++) {
		rbMaterialDensityItem *preset = &RB_MATERIAL_DENSITY_TABLE[i];

		item_tmp.identifier = preset->name;
		item_tmp.name = IFACE_(preset->name);
		item_tmp.value = i;
		RNA_enum_item_add(&item, &totitem, &item_tmp);
	}

	/* add special "custom" entry to the end of the list */
	{
		item_tmp.identifier = "Custom";
		item_tmp.name = IFACE_("Custom");
		item_tmp.value = -1;
		RNA_enum_item_add(&item, &totitem, &item_tmp);
	}

	RNA_enum_item_end(&item, &totitem);
	*free = 1;

	return item;
}

/* ------------------------------------------ */

/* helper function to calculate volume of rigidbody object */
// TODO: allow a parameter to specify method used to calculate this?
static float calc_rigidbody_ob_volume(Object *ob)
{
	RigidBodyOb *rbo = ob->rigidbody_object;

	float size[3]  = {1.0f, 1.0f, 1.0f};
	float radius = 1.0f;
	float height = 1.0f;

	float volume = 0.0f;

	/* if automatically determining dimensions, use the Object's boundbox
	 *	- assume that all quadrics are standing upright on local z-axis
	 *	- assume even distribution of mass around the Object's pivot
	 *	  (i.e. Object pivot is centralised in boundbox)
	 *	- boundbox gives full width
	 */
	// XXX: all dimensions are auto-determined now... later can add stored settings for this
	BKE_object_dimensions_get(ob, size);

	if (ELEM3(rbo->shape, RB_SHAPE_CAPSULE, RB_SHAPE_CYLINDER, RB_SHAPE_CONE)) {
		/* take radius as largest x/y dimension, and height as z-dimension */
		radius = MAX2(size[0], size[1]) * 0.5f;
		height = size[2];
	}
	else if (rbo->shape == RB_SHAPE_SPHERE) {
		/* take radius to the the largest dimension to try and encompass everything */
		radius = max_fff(size[0], size[1], size[2]) * 0.5f;
	}

	/* calculate volume as appropriate  */
	switch (rbo->shape) {
		case RB_SHAPE_BOX:
			volume = size[0] * size[1] * size[2];
			break;

		case RB_SHAPE_SPHERE:
			volume = 4.0f / 3.0f * (float)M_PI * radius * radius * radius;
			break;

		/* for now, assume that capsule is close enough to a cylinder... */
		case RB_SHAPE_CAPSULE:
		case RB_SHAPE_CYLINDER:
			volume = (float)M_PI * radius * radius * height;
			break;

		case RB_SHAPE_CONE:
			volume = (float)M_PI / 3.0f * radius * radius * height;
			break;

		/* for now, all mesh shapes are just treated as boxes...
		 * NOTE: this may overestimate the volume, but other methods are overkill
		 */
		case RB_SHAPE_CONVEXH:
		case RB_SHAPE_TRIMESH:
			volume = size[0] * size[1] * size[2];
			break;

#if 0 // XXX: not defined yet
		case RB_SHAPE_COMPOUND:
			volume = 0.0f;
			break;
#endif
	}

	/* return the volume calculated */
	return volume;
}

/* ------------------------------------------ */

static int rigidbody_obs_calc_mass_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	int material = RNA_enum_get(op->ptr, "material");
	float density;

	/* sanity checks */
	if (scene == NULL)
		return OPERATOR_CANCELLED;

	/* get density (kg/m^3) to apply */
	if (material >= 0) {
		/* get density from table, and store in props for later repeating */
		if (material >= NUM_RB_MATERIAL_PRESETS)
			material = 0;

		density = RB_MATERIAL_DENSITY_TABLE[material].density;
		RNA_float_set(op->ptr, "density", density);
	}
	else {
		/* custom - grab from whatever value is set */
		density = RNA_float_get(op->ptr, "density");
	}

	/* apply this to all selected objects (with rigidbodies)... */
	CTX_DATA_BEGIN(C, Object *, ob, selected_objects)
	{
		if (ob->rigidbody_object) {
			PointerRNA ptr;

			float volume; /* m^3 */
			float mass;   /* kg */

			/* mass is calculated from the approximate volume of the object,
			 * and the density of the material we're simulating
			 */
			volume = calc_rigidbody_ob_volume(ob);
			mass = volume * density;

			/* use RNA-system to change the property and perform all necessary changes */
			RNA_pointer_create(&ob->id, &RNA_RigidBodyObject, ob->rigidbody_object, &ptr);
			RNA_float_set(&ptr, "mass", mass);

			DAG_id_tag_update(&ob->id, OB_RECALC_OB);
		}
	}
	CTX_DATA_END;

	/* send updates */
	WM_event_add_notifier(C, NC_OBJECT | ND_POINTCACHE, NULL);

	/* done */
	return OPERATOR_FINISHED;
}

void RIGIDBODY_OT_mass_calculate(wmOperatorType *ot)
{
	PropertyRNA *prop;

	/* identifiers */
	ot->idname = "RIGIDBODY_OT_mass_calculate";
	ot->name = "Calculate Mass";
	ot->description = "Automatically calculate mass values for Rigid Body Objects based on volume";

	/* callbacks */
	ot->invoke = WM_menu_invoke; // XXX
	ot->exec = rigidbody_obs_calc_mass_exec;
	ot->poll = ED_operator_rigidbody_active_poll;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	ot->prop = prop = RNA_def_enum(ot->srna, "material",
	                               DummyRNA_DEFAULT_items, 0,
	                               "Material Preset",
	                               "Type of material that objects are made of (determines material density)");
	RNA_def_enum_funcs(prop, rigidbody_materials_itemf);

	RNA_def_float(ot->srna, "density", 1.0, FLT_MIN, FLT_MAX,
	              "Density",
	              "Custom density value (kg/m^3) to use instead of material preset",
	              1.0f, 2500.0f);
}

/* ********************************************** */
