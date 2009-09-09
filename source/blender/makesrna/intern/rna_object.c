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
 * Contributor(s): Blender Foundation (2008).
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdio.h>
#include <stdlib.h>

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "DNA_customdata_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_object_force.h"
#include "DNA_object_types.h"
#include "DNA_property_types.h"
#include "DNA_scene_types.h"

#include "WM_api.h"
#include "WM_types.h"

EnumPropertyItem object_mode_items[] = {
	{OB_MODE_OBJECT, "OBJECT", ICON_OBJECT_DATAMODE, "Object", ""},
	{OB_MODE_EDIT, "EDIT", ICON_EDITMODE_HLT, "Edit", ""},
	{OB_MODE_SCULPT, "SCULPT", ICON_SCULPTMODE_HLT, "Sculpt", ""},
	{OB_MODE_VERTEX_PAINT, "VERTEX_PAINT", ICON_VPAINT_HLT, "Vertex Paint", ""},
	{OB_MODE_WEIGHT_PAINT, "WEIGHT_PAINT", ICON_WPAINT_HLT, "Weight Paint", ""},
	{OB_MODE_TEXTURE_PAINT, "TEXTURE_PAINT", ICON_TPAINT_HLT, "Texture Paint", ""},
	{OB_MODE_PARTICLE_EDIT, "PARTICLE_EDIT", ICON_PARTICLEMODE, "Particle Edit", ""},
	{OB_MODE_POSE, "POSE", ICON_POSE_HLT, "Pose", ""},
	{0, NULL, 0, NULL, NULL}};

static EnumPropertyItem parent_type_items[] = {
	{PAROBJECT, "OBJECT", 0, "Object", ""},
	{PARCURVE, "CURVE", 0, "Curve", ""},
	{PARKEY, "KEY", 0, "Key", ""},
	{PARSKEL, "ARMATURE", 0, "Armature", ""},
	{PARSKEL, "LATTICE", 0, "Lattice", ""}, // PARSKEL reuse will give issues
	{PARVERT1, "VERTEX", 0, "Vertex", ""},
	{PARVERT3, "VERTEX_3", 0, "3 Vertices", ""},
	{PARBONE, "BONE", 0, "Bone", ""},
	{0, NULL, 0, NULL, NULL}};

EnumPropertyItem object_type_items[] = {
	{OB_MESH, "MESH", 0, "Mesh", ""},
	{OB_CURVE, "CURVE", 0, "Curve", ""},
	{OB_SURF, "SURFACE", 0, "Surface", ""},
	{OB_MBALL, "META", 0, "Meta", ""},
	{OB_FONT, "TEXT", 0, "Text", ""},
	{0, "", 0, NULL, NULL},
	{OB_ARMATURE, "ARMATURE", 0, "Armature", ""},
	{OB_LATTICE, "LATTICE", 0, "Lattice", ""},
	{OB_EMPTY, "EMPTY", 0, "Empty", ""},
	{0, "", 0, NULL, NULL},
	{OB_CAMERA, "CAMERA", 0, "Camera", ""},
	{OB_LAMP, "LAMP", 0, "Lamp", ""},
	{0, NULL, 0, NULL, NULL}
};

#ifdef RNA_RUNTIME

#include "DNA_key_types.h"

#include "BKE_armature.h"
#include "BKE_bullet.h"
#include "BKE_context.h"
#include "BKE_curve.h"
#include "BKE_depsgraph.h"
#include "BKE_effect.h"
#include "BKE_key.h"
#include "BKE_material.h"
#include "BKE_mesh.h"
#include "BKE_particle.h"
#include "BKE_scene.h"

#include "ED_object.h"

void rna_Object_update(bContext *C, PointerRNA *ptr)
{
	DAG_id_flush_update(ptr->id.data, OB_RECALC_OB);
}

void rna_Object_update_data(bContext *C, PointerRNA *ptr)
{
	DAG_id_flush_update(ptr->id.data, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_DRAW, ptr->id.data);
}

static void rna_Object_dependency_update(bContext *C, PointerRNA *ptr)
{
	DAG_id_flush_update(ptr->id.data, OB_RECALC_OB);
	DAG_scene_sort(CTX_data_scene(C));
}

static void rna_Object_layer_update(bContext *C, PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;
	Scene *scene= CTX_data_scene(C);
	Base *base;

	base= object_in_scene(ob, scene);
	if(!base)
		return;

	/* try to avoid scene sort */
	if((ob->lay & scene->lay) && (base->lay & scene->lay))
 		base->lay= ob->lay;
	else if((ob->lay & scene->lay)==0 && (base->lay & scene->lay)==0)
		base->lay= ob->lay;
	else {
		base->lay= ob->lay;
		DAG_scene_sort(scene);
	}
}

static int rna_Object_data_editable(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->data;

	return (ob->type == OB_EMPTY)? 0: PROP_EDITABLE;
}

static void rna_Object_data_set(PointerRNA *ptr, PointerRNA value)
{
	Object *ob= (Object*)ptr->data;
	ID *id= value.data;

	if(ob->type == OB_EMPTY || id == NULL)
		return;
	
	if(ob->type == OB_MESH) {
		set_mesh(ob, (Mesh*)id);
	}
	else {
		if(ob->data)
			id_us_min((ID*)ob->data);
		if(id)
			id_us_plus(id);

		ob->data= id;
		test_object_materials(id);

		if(GS(id->name)==ID_CU)
			test_curve_type(ob);
		else if(ob->type==OB_ARMATURE)
			armature_rebuild_pose(ob, ob->data);
	}
}

static StructRNA *rna_Object_data_typef(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->data;

	switch(ob->type) {
		case OB_MESH: return &RNA_Mesh;
		case OB_CURVE: return &RNA_Curve;
		case OB_SURF: return &RNA_Curve;
		case OB_FONT: return &RNA_Curve;
		case OB_MBALL: return &RNA_MetaBall;
		case OB_LAMP: return &RNA_Lamp;
		case OB_CAMERA: return &RNA_Camera;
		case OB_LATTICE: return &RNA_Lattice;
		case OB_ARMATURE: return &RNA_Armature;
		default: return &RNA_ID;
	}
}

static void rna_Object_parent_set(PointerRNA *ptr, PointerRNA value)
{
	Object *ob= (Object*)ptr->data;
	Object *par= (Object*)value.data;

	ED_object_parent(ob, par, ob->partype, ob->parsubstr);
}

static void rna_Object_parent_type_set(PointerRNA *ptr, int value)
{
	Object *ob= (Object*)ptr->data;

	ED_object_parent(ob, ob->parent, value, ob->parsubstr);
}

static void rna_Object_track_set(PointerRNA *ptr, PointerRNA value)
{
	Object *ob= (Object*)ptr->data;

	if(ob != value.data)
		ob->track= value.data;
}

static EnumPropertyItem *rna_Object_parent_type_itemf(bContext *C, PointerRNA *ptr, int *free)
{
	Object *ob= (Object*)ptr->data;
	EnumPropertyItem *item= NULL;
	int totitem= 0;

	if(C==NULL) {
		return parent_type_items;
	}
	
	RNA_enum_items_add_value(&item, &totitem, parent_type_items, PAROBJECT);

	if(ob->parent) {
		Object *par= ob->parent;
		
		if(par->type == OB_CURVE)
			RNA_enum_items_add_value(&item, &totitem, parent_type_items, PARCURVE);
		else if(par->type == OB_LATTICE)
			RNA_enum_items_add_value(&item, &totitem, &parent_type_items[4], PARSKEL); // special hack: prevents this overriding others
		else if(par->type == OB_ARMATURE) {
			RNA_enum_items_add_value(&item, &totitem, &parent_type_items[3], PARSKEL); // special hack: prevents this being overrided
			RNA_enum_items_add_value(&item, &totitem, parent_type_items, PARBONE);
		}
		else if(par->type == OB_MESH) {
			RNA_enum_items_add_value(&item, &totitem, parent_type_items, PARVERT1);
			RNA_enum_items_add_value(&item, &totitem, parent_type_items, PARVERT3);
		}
	}

	RNA_enum_item_end(&item, &totitem);

	*free= 1;

	return item;
}

static void rna_Object_parent_bone_set(PointerRNA *ptr, const char *value)
{
	Object *ob= (Object*)ptr->data;

	ED_object_parent(ob, ob->parent, ob->partype, value);
}

static int rna_VertexGroup_index_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;

	return BLI_findindex(&ob->defbase, ptr->data);
}

static PointerRNA rna_Object_active_vertex_group_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;
	return rna_pointer_inherit_refine(ptr, &RNA_VertexGroup, BLI_findlink(&ob->defbase, ob->actdef-1));
}

static int rna_Object_active_vertex_group_index_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;
	return MAX2(ob->actdef-1, 0);
}

static void rna_Object_active_vertex_group_index_set(PointerRNA *ptr, int value)
{
	Object *ob= (Object*)ptr->id.data;
	ob->actdef= value+1;
}

static void rna_Object_active_vertex_group_index_range(PointerRNA *ptr, int *min, int *max)
{
	Object *ob= (Object*)ptr->id.data;

	*min= 0;
	*max= BLI_countlist(&ob->defbase)-1;
	*max= MAX2(0, *max);
}

void rna_object_vgroup_name_index_get(PointerRNA *ptr, char *value, int index)
{
	Object *ob= (Object*)ptr->id.data;
	bDeformGroup *dg;

	dg= BLI_findlink(&ob->defbase, index-1);

	if(dg) BLI_strncpy(value, dg->name, sizeof(dg->name));
	else BLI_strncpy(value, "", sizeof(dg->name));
}

int rna_object_vgroup_name_index_length(PointerRNA *ptr, int index)
{
	Object *ob= (Object*)ptr->id.data;
	bDeformGroup *dg;

	dg= BLI_findlink(&ob->defbase, index-1);
	return (dg)? strlen(dg->name): 0;
}

void rna_object_vgroup_name_index_set(PointerRNA *ptr, const char *value, short *index)
{
	Object *ob= (Object*)ptr->id.data;
	bDeformGroup *dg;
	int a;

	for(a=1, dg=ob->defbase.first; dg; dg=dg->next, a++) {
		if(strcmp(dg->name, value) == 0) {
			*index= a;
			return;
		}
	}

	*index= 0;
}

void rna_object_vgroup_name_set(PointerRNA *ptr, const char *value, char *result, int maxlen)
{
	Object *ob= (Object*)ptr->id.data;
	bDeformGroup *dg;

	for(dg=ob->defbase.first; dg; dg=dg->next) {
		if(strcmp(dg->name, value) == 0) {
			BLI_strncpy(result, value, maxlen);
			return;
		}
	}

	BLI_strncpy(result, "", maxlen);
}

void rna_object_uvlayer_name_set(PointerRNA *ptr, const char *value, char *result, int maxlen)
{
	Object *ob= (Object*)ptr->id.data;
	Mesh *me;
	CustomDataLayer *layer;
	int a;

	if(ob->type == OB_MESH && ob->data) {
		me= (Mesh*)ob->data;

		for(a=0; a<me->fdata.totlayer; a++) {
			layer= &me->fdata.layers[a];

			if(layer->type == CD_MTFACE && strcmp(layer->name, value) == 0) {
				BLI_strncpy(result, value, maxlen);
				return;
			}
		}
	}

	BLI_strncpy(result, "", maxlen);
}

void rna_object_vcollayer_name_set(PointerRNA *ptr, const char *value, char *result, int maxlen)
{
	Object *ob= (Object*)ptr->id.data;
	Mesh *me;
	CustomDataLayer *layer;
	int a;

	if(ob->type == OB_MESH && ob->data) {
		me= (Mesh*)ob->data;

		for(a=0; a<me->fdata.totlayer; a++) {
			layer= &me->fdata.layers[a];

			if(layer->type == CD_MCOL && strcmp(layer->name, value) == 0) {
				BLI_strncpy(result, value, maxlen);
				return;
			}
		}
	}

	BLI_strncpy(result, "", maxlen);
}

static int rna_Object_active_material_index_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;
	return MAX2(ob->actcol-1, 0);
}

static void rna_Object_active_material_index_set(PointerRNA *ptr, int value)
{
	Object *ob= (Object*)ptr->id.data;
	ob->actcol= value+1;
}

static void rna_Object_active_material_index_range(PointerRNA *ptr, int *min, int *max)
{
	Object *ob= (Object*)ptr->id.data;
	*min= 0;
	*max= MAX2(ob->totcol-1, 0);
}

static PointerRNA rna_Object_active_material_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;
	Material *ma;

	ma= (ob->totcol)? give_current_material(ob, ob->actcol): NULL;
	return rna_pointer_inherit_refine(ptr, &RNA_Material, ma);
}

static void rna_Object_active_material_set(PointerRNA *ptr, PointerRNA value)
{
	Object *ob= (Object*)ptr->id.data;

	assign_material(ob, value.data, ob->actcol);
}

static void rna_Object_active_particle_system_index_range(PointerRNA *ptr, int *min, int *max)
{
	Object *ob= (Object*)ptr->id.data;
	*min= 0;
	*max= BLI_countlist(&ob->particlesystem)-1;
	*max= MAX2(0, *max);
}

static int rna_Object_active_particle_system_index_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;
	return psys_get_current_num(ob);
}

static void rna_Object_active_particle_system_index_set(struct PointerRNA *ptr, int value)
{
	Object *ob= (Object*)ptr->id.data;
	psys_set_current_num(ob, value);
}

static PointerRNA rna_MaterialSlot_material_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;
	Material *ma;
	int index= (Material**)ptr->data - ob->mat;

	ma= give_current_material(ob, index+1);
	return rna_pointer_inherit_refine(ptr, &RNA_Material, ma);
}

static void rna_MaterialSlot_material_set(PointerRNA *ptr, PointerRNA value)
{
	Object *ob= (Object*)ptr->id.data;
	int index= (Material**)ptr->data - ob->mat;

	assign_material(ob, value.data, index+1);
}

static int rna_MaterialSlot_link_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;
	int index= (Material**)ptr->data - ob->mat;

	return ob->matbits[index] != 0;
}

static void rna_MaterialSlot_link_set(PointerRNA *ptr, int value)
{
	Object *ob= (Object*)ptr->id.data;
	int index= (Material**)ptr->data - ob->mat;
	
	if(value) {
		ob->matbits[index]= 1;
		ob->colbits |= (1<<index);
	}
	else {
		ob->matbits[index]= 0;
		ob->colbits &= ~(1<<index);
	}
}

static int rna_MaterialSlot_name_length(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;
	Material *ma;
	int index= (Material**)ptr->data - ob->mat;

	ma= give_current_material(ob, index+1);

	if(ma)
		return strlen(ma->id.name+2);
	
	return 0;
}

static void rna_MaterialSlot_name_get(PointerRNA *ptr, char *str)
{
	Object *ob= (Object*)ptr->id.data;
	Material *ma;
	int index= (Material**)ptr->data - ob->mat;

	ma= give_current_material(ob, index+1);

	if(ma)
		strcpy(str, ma->id.name+2);
	else
		strcpy(str, "");
}

/* why does this have to be so complicated?, can't all this crap be
 * moved to in BGE conversion function? - Campbell *
 *
 * logic from check_body_type()
 *  */
static int rna_GameObjectSettings_physics_type_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;

	/* determine the body_type setting based on flags */
	if (!(ob->gameflag & OB_COLLISION)) {
		if (ob->gameflag & OB_OCCLUDER) {
			ob->body_type = OB_BODY_TYPE_OCCLUDER;
		} else {
			ob->body_type = OB_BODY_TYPE_NO_COLLISION;
		}
	} else if (ob->gameflag & OB_SENSOR) {
		ob->body_type = OB_BODY_TYPE_SENSOR;
	} else if (!(ob->gameflag & OB_DYNAMIC)) {
		ob->body_type = OB_BODY_TYPE_STATIC;
	} else if (!(ob->gameflag & (OB_RIGID_BODY|OB_SOFT_BODY))) {
		ob->body_type = OB_BODY_TYPE_DYNAMIC;
	} else if (ob->gameflag & OB_RIGID_BODY) {
		ob->body_type = OB_BODY_TYPE_RIGID;
	} else {
		ob->body_type = OB_BODY_TYPE_SOFT;
		/* create the structure here because we display soft body buttons in the main panel */
		if (!ob->bsoft)
			ob->bsoft = bsbNew();
	}

	return ob->body_type;
}

static void rna_GameObjectSettings_physics_type_set(PointerRNA *ptr, int value)
{
	Object *ob= (Object*)ptr->id.data;
	ob->body_type= value;

	switch (ob->body_type) {
	case OB_BODY_TYPE_SENSOR:
		ob->gameflag |= OB_SENSOR|OB_COLLISION|OB_GHOST;
		ob->gameflag &= ~(OB_OCCLUDER|OB_DYNAMIC|OB_RIGID_BODY|OB_SOFT_BODY|OB_ACTOR|OB_ANISOTROPIC_FRICTION|OB_DO_FH|OB_ROT_FH|OB_COLLISION_RESPONSE);
		break;
	case OB_BODY_TYPE_OCCLUDER:
		ob->gameflag |= OB_OCCLUDER;
		ob->gameflag &= ~(OB_SENSOR|OB_COLLISION|OB_DYNAMIC);
		break;
	case OB_BODY_TYPE_NO_COLLISION:
		ob->gameflag &= ~(OB_SENSOR|OB_COLLISION|OB_OCCLUDER|OB_DYNAMIC);
		break;
	case OB_BODY_TYPE_STATIC:
		ob->gameflag |= OB_COLLISION;
		ob->gameflag &= ~(OB_DYNAMIC|OB_RIGID_BODY|OB_SOFT_BODY|OB_OCCLUDER|OB_SENSOR);
		break;
	case OB_BODY_TYPE_DYNAMIC:
		ob->gameflag |= OB_COLLISION|OB_DYNAMIC|OB_ACTOR;
		ob->gameflag &= ~(OB_RIGID_BODY|OB_SOFT_BODY|OB_OCCLUDER|OB_SENSOR);
		break;
	case OB_BODY_TYPE_RIGID:
		ob->gameflag |= OB_COLLISION|OB_DYNAMIC|OB_RIGID_BODY|OB_ACTOR;
		ob->gameflag &= ~(OB_SOFT_BODY|OB_OCCLUDER|OB_SENSOR);
		break;
	default:
	case OB_BODY_TYPE_SOFT:
		ob->gameflag |= OB_COLLISION|OB_DYNAMIC|OB_SOFT_BODY|OB_ACTOR;
		ob->gameflag &= ~(OB_RIGID_BODY|OB_OCCLUDER|OB_SENSOR);

		/* assume triangle mesh, if no bounds chosen for soft body */
		if ((ob->gameflag & OB_BOUNDS) && (ob->boundtype<OB_BOUND_POLYH))
		{
			ob->boundtype=OB_BOUND_POLYH;
		}
		/* create a BulletSoftBody structure if not already existing */
		if (!ob->bsoft)
			ob->bsoft = bsbNew();
		break;
	}
}

static PointerRNA rna_Object_active_particle_system_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;
	ParticleSystem *psys= psys_get_current(ob);
	return rna_pointer_inherit_refine(ptr, &RNA_ParticleSystem, psys);
}

static PointerRNA rna_Object_game_settings_get(PointerRNA *ptr)
{
	return rna_pointer_inherit_refine(ptr, &RNA_GameObjectSettings, ptr->id.data);
}

static void rna_Object_layer_set(PointerRNA *ptr, const int *values)
{
	Object *ob= (Object*)ptr->data;
	int i, tot= 0;

	/* ensure we always have some layer selected */
	for(i=0; i<20; i++)
		if(values[i])
			tot++;
	
	if(tot==0)
		return;

	for(i=0; i<20; i++) {
		if(values[i]) ob->lay |= (1<<i);
		else ob->lay &= ~(1<<i);
	}
}

static void rna_GameObjectSettings_state_set(PointerRNA *ptr, const int *values)
{
	Object *ob= (Object*)ptr->data;
	int i, tot= 0;

	/* ensure we always have some state selected */
	for(i=0; i<20; i++)
		if(values[i])
			tot++;
	
	if(tot==0)
		return;

	for(i=0; i<20; i++) {
		if(values[i]) ob->state |= (1<<i);
		else ob->state &= ~(1<<i);
	}
}

static void rna_Object_active_shape_key_index_range(PointerRNA *ptr, int *min, int *max)
{
	Object *ob= (Object*)ptr->id.data;
	Key *key= ob_get_key(ob);

	*min= 0;
	*max= (key)? BLI_countlist(&key->block)-1: 0;
	*max= MAX2(0, *max);
}

static int rna_Object_active_shape_key_index_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;

	return MAX2(ob->shapenr-1, 0);
}

static void rna_Object_active_shape_key_index_set(PointerRNA *ptr, int value)
{
	Object *ob= (Object*)ptr->id.data;

	ob->shapenr= value+1;
	ob->shapeflag |= OB_SHAPE_TEMPLOCK;
}

static PointerRNA rna_Object_active_shape_key_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;
	Key *key= ob_get_key(ob);
	KeyBlock *kb;
	PointerRNA keyptr;

	if(key==NULL)
		return PointerRNA_NULL;
	
	kb= BLI_findlink(&key->block, ob->shapenr-1);
	RNA_pointer_create(&key->id, &RNA_ShapeKey, kb, &keyptr);
	return keyptr;
}

static void rna_Object_shape_key_lock_set(PointerRNA *ptr, int value)
{
	Object *ob= (Object*)ptr->id.data;

	if(value) ob->shapeflag |= OB_SHAPE_LOCK;
	else ob->shapeflag &= ~OB_SHAPE_LOCK;

	ob->shapeflag &= ~OB_SHAPE_TEMPLOCK;
}

static PointerRNA rna_Object_field_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;

	/* weak */
	if(!ob->pd)
		ob->pd= object_add_collision_fields();
	
	return rna_pointer_inherit_refine(ptr, &RNA_FieldSettings, ob->pd);
}

static PointerRNA rna_Object_collision_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;

	/* weak */
	if(!ob->pd)
		ob->pd= object_add_collision_fields();
	
	return rna_pointer_inherit_refine(ptr, &RNA_CollisionSettings, ob->pd);
}

#else

static void rna_def_vertex_group(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "VertexGroup", NULL);
	RNA_def_struct_sdna(srna, "bDeformGroup");
	RNA_def_struct_ui_text(srna, "Vertex Group", "Group of vertices, used for armature deform and other purposes.");
	RNA_def_struct_ui_icon(srna, ICON_GROUP_VERTEX);

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_ui_text(prop, "Name", "Vertex group name.");
	RNA_def_struct_name_property(srna, prop);

	prop= RNA_def_property(srna, "index", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_int_funcs(prop, "rna_VertexGroup_index_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Index", "Index number of the vertex group.");
}

static void rna_def_material_slot(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem link_items[] = {
		{1, "OBJECT", 0, "Object", ""},
		{0, "DATA", 0, "Data", ""},
		{0, NULL, 0, NULL, NULL}};
	
	/* NOTE: there is no MaterialSlot equivalent in DNA, so the internal
	 * pointer data points to ob->mat + index, and we manually implement
	 * get/set for the properties. */

	srna= RNA_def_struct(brna, "MaterialSlot", NULL);
	RNA_def_struct_ui_text(srna, "Material Slot", "Material slot in an object.");
	RNA_def_struct_ui_icon(srna, ICON_MATERIAL_DATA);

	prop= RNA_def_property(srna, "material", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "Material");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_pointer_funcs(prop, "rna_MaterialSlot_material_get", "rna_MaterialSlot_material_set", NULL);
	RNA_def_property_ui_text(prop, "Material", "Material datablock used by this material slot.");
	RNA_def_property_update(prop, NC_OBJECT|ND_SHADING, "rna_Object_update");

	prop= RNA_def_property(srna, "link", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, link_items);
	RNA_def_property_enum_funcs(prop, "rna_MaterialSlot_link_get", "rna_MaterialSlot_link_set", NULL);
	RNA_def_property_ui_text(prop, "Link", "Link material to object or the object's data.");
	RNA_def_property_update(prop, NC_OBJECT|ND_SHADING, "rna_Object_update");

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_string_funcs(prop, "rna_MaterialSlot_name_get", "rna_MaterialSlot_name_length", NULL);
	RNA_def_property_ui_text(prop, "Name", "Material slot name.");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_struct_name_property(srna, prop);
}

static void rna_def_object_game_settings(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem body_type_items[] = {
		{OB_BODY_TYPE_NO_COLLISION, "NO_COLLISION", 0, "No Collision", "Disable colision for this object"},
		{OB_BODY_TYPE_STATIC, "STATIC", 0, "Static", "Stationary object"},
		{OB_BODY_TYPE_DYNAMIC, "DYNAMIC", 0, "Dynamic", "Linear physics"},
		{OB_BODY_TYPE_RIGID, "RIGID_BODY", 0, "Rigid Body", "Linear and angular physics"},
		{OB_BODY_TYPE_SOFT, "SOFT_BODY", 0, "Soft Body", "Soft body"},
		{OB_BODY_TYPE_OCCLUDER, "OCCLUDE", 0, "Occlude", "Occluder for optimizing scene rendering"},
		{OB_BODY_TYPE_SENSOR, "SENSOR", 0, "Sensor", "Collision Sensor, detects static and dynamic objects but not the other collision sensor objects"},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem collision_bounds_items[] = {
		{OB_BOUND_BOX, "BOX", 0, "Box", ""},
		{OB_BOUND_SPHERE, "SPHERE", 0, "Sphere", ""},
		{OB_BOUND_CYLINDER, "CYLINDER", 0, "Cylinder", ""},
		{OB_BOUND_CONE, "CONE", 0, "Cone", ""},
		{OB_BOUND_POLYT, "CONVEX_HULL", 0, "Convex Hull", ""},
		{OB_BOUND_POLYH, "TRIANGLE_MESH", 0, "Triangle Mesh", ""},
		//{OB_DYN_MESH, "DYNAMIC_MESH", 0, "Dynamic Mesh", ""},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "GameObjectSettings", NULL);
	RNA_def_struct_sdna(srna, "Object");
	RNA_def_struct_nested(brna, srna, "Object");
	RNA_def_struct_ui_text(srna, "Game Object Settings", "Game engine related settings for the object.");
	RNA_def_struct_ui_icon(srna, ICON_GAME);

	/* logic */

	prop= RNA_def_property(srna, "sensors", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "Sensor");
	RNA_def_property_ui_text(prop, "Sensors", "Game engine sensor to detect events.");

	prop= RNA_def_property(srna, "controllers", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "Controller");
	RNA_def_property_ui_text(prop, "Controllers", "Game engine controllers to process events, connecting sensor to actuators.");

	prop= RNA_def_property(srna, "actuators", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "Actuator");
	RNA_def_property_ui_text(prop, "Actuators", "Game engine actuators to act on events.");

	prop= RNA_def_property(srna, "properties", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "prop", NULL);
	RNA_def_property_struct_type(prop, "GameProperty"); /* rna_property.c */
	RNA_def_property_ui_text(prop, "Properties", "Game engine properties.");

	prop= RNA_def_property(srna, "show_sensors", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "scaflag", OB_SHOWSENS);
	RNA_def_property_ui_text(prop, "Show Sensors", "Shows sensors for this object in the user interface.");

	prop= RNA_def_property(srna, "show_controllers", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "scaflag", OB_SHOWCONT);
	RNA_def_property_ui_text(prop, "Show Controllers", "Shows controllers for this object in the user interface.");

	prop= RNA_def_property(srna, "show_actuators", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "scaflag", OB_SHOWACT);
	RNA_def_property_ui_text(prop, "Show Actuators", "Shows actuators for this object in the user interface.");

	/* physics */

	prop= RNA_def_property(srna, "physics_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "body_type");
	RNA_def_property_enum_items(prop, body_type_items);
	RNA_def_property_enum_funcs(prop, "rna_GameObjectSettings_physics_type_get", "rna_GameObjectSettings_physics_type_set", NULL);
	RNA_def_property_ui_text(prop, "Physics Type",  "Selects the type of physical representation.");

	prop= RNA_def_property(srna, "actor", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag", OB_ACTOR);
	RNA_def_property_ui_text(prop, "Actor", "Object is detected by the Near and Radar sensor.");

	prop= RNA_def_property(srna, "ghost", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag", OB_GHOST);
	RNA_def_property_ui_text(prop, "Ghost", "Object does not restitute collisions, like a ghost.");

	prop= RNA_def_property(srna, "mass", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.01, 10000.0);
	RNA_def_property_ui_text(prop, "Mass", "Mass of the object.");

	prop= RNA_def_property(srna, "radius", PROP_FLOAT, PROP_NONE|PROP_UNIT_LENGTH);
	RNA_def_property_float_sdna(prop, NULL, "inertia");
	RNA_def_property_range(prop, 0.01, 10.0);
	RNA_def_property_ui_text(prop, "Radius", "Radius of bounding sphere and material physics");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	prop= RNA_def_property(srna, "no_sleeping", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag", OB_COLLISION_RESPONSE);
	RNA_def_property_ui_text(prop, "No Sleeping", "Disable auto (de)activation in physics simulation.");

	prop= RNA_def_property(srna, "damping", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "damping");
	RNA_def_property_range(prop, 0.0, 1.0);
	RNA_def_property_ui_text(prop, "Damping", "General movement damping.");

	prop= RNA_def_property(srna, "rotation_damping", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "rdamping");
	RNA_def_property_range(prop, 0.0, 1.0);
	RNA_def_property_ui_text(prop, "Rotation Damping", "General rotation damping.");

	prop= RNA_def_property(srna, "minimum_velocity", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "min_vel");
	RNA_def_property_range(prop, 0.0, 1000.0);
	RNA_def_property_ui_text(prop, "Velocity Min", "Clamp velocity to this minimum speed (except when totally still).");

	prop= RNA_def_property(srna, "maximum_velocity", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "max_vel");
	RNA_def_property_range(prop, 0.0, 1000.0);
	RNA_def_property_ui_text(prop, "Velocity Max", "Clamp velocity to this maximum speed.");

	/* lock position */
	prop= RNA_def_property(srna, "lock_x_axis", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag2", OB_LOCK_RIGID_BODY_X_AXIS);
	RNA_def_property_ui_text(prop, "Lock X Axis", "Disable simulation of linear motion along the X axis.");
	
	prop= RNA_def_property(srna, "lock_y_axis", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag2", OB_LOCK_RIGID_BODY_Y_AXIS);
	RNA_def_property_ui_text(prop, "Lock Y Axis", "Disable simulation of linear motion along the Y axis.");
	
	prop= RNA_def_property(srna, "lock_z_axis", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag2", OB_LOCK_RIGID_BODY_Z_AXIS);
	RNA_def_property_ui_text(prop, "Lock Z Axis", "Disable simulation of linear motion along the Z axis.");
	
	
	/* lock rotation */
	prop= RNA_def_property(srna, "lock_x_rot_axis", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag2", OB_LOCK_RIGID_BODY_X_ROT_AXIS);
	RNA_def_property_ui_text(prop, "Lock X Rotation Axis", "Disable simulation of angular  motion along the X axis.");
	
	prop= RNA_def_property(srna, "lock_y_rot_axis", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag2", OB_LOCK_RIGID_BODY_Y_ROT_AXIS);
	RNA_def_property_ui_text(prop, "Lock Y Rotation Axis", "Disable simulation of angular  motion along the Y axis.");
	
	prop= RNA_def_property(srna, "lock_z_rot_axis", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag2", OB_LOCK_RIGID_BODY_Z_ROT_AXIS);
	RNA_def_property_ui_text(prop, "Lock Z Rotation Axis", "Disable simulation of angular  motion along the Z axis.");
	
	/* is this used anywhere ? */
	prop= RNA_def_property(srna, "use_activity_culling", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "gameflag2", OB_NEVER_DO_ACTIVITY_CULLING);
	RNA_def_property_ui_text(prop, "Lock Z Rotation Axis", "Disable simulation of angular  motion along the Z axis.");	
	

	prop= RNA_def_property(srna, "material_physics", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag", OB_DO_FH);
	RNA_def_property_ui_text(prop, "Use Material Physics", "Use physics settings in materials.");

	prop= RNA_def_property(srna, "rotate_from_normal", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag", OB_ROT_FH);
	RNA_def_property_ui_text(prop, "Rotate From Normal", "Use face normal to rotate object, so that it points away from the surface");

	prop= RNA_def_property(srna, "form_factor", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "formfactor");
	RNA_def_property_range(prop, 0.0, 1.0);
	RNA_def_property_ui_text(prop, "Form Factor", "Form factor scales the inertia tensor.");

	prop= RNA_def_property(srna, "anisotropic_friction", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag", OB_ANISOTROPIC_FRICTION);
	RNA_def_property_ui_text(prop, "Anisotropic Friction", "Enable anisotropic friction.");

	prop= RNA_def_property(srna, "friction_coefficients", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "anisotropicFriction");
	RNA_def_property_range(prop, 0.0, 1.0);
	RNA_def_property_ui_text(prop, "Friction Coefficients", "Relative friction coefficient in the in the X, Y and Z directions, when anisotropic friction is enabled.");

	prop= RNA_def_property(srna, "use_collision_bounds", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag", OB_BOUNDS);
	RNA_def_property_ui_text(prop, "Use Collision Bounds", "Specify a collision bounds type other than the default.");

	prop= RNA_def_property(srna, "collision_bounds", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "boundtype");
	RNA_def_property_enum_items(prop, collision_bounds_items);
	RNA_def_property_ui_text(prop, "Collision Bounds",  "Selects the collision type.");

	prop= RNA_def_property(srna, "collision_compound", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag", OB_CHILD);
	RNA_def_property_ui_text(prop, "Collison Compound", "Add children to form a compound collision object.");

	prop= RNA_def_property(srna, "collision_margin", PROP_FLOAT, PROP_NONE|PROP_UNIT_LENGTH);
	RNA_def_property_float_sdna(prop, NULL, "margin");
	RNA_def_property_range(prop, 0.0, 1.0);
	RNA_def_property_ui_text(prop, "Collision Margin", "Extra margin around object for collision detection, small amount required for stability.");

	prop= RNA_def_property(srna, "soft_body", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "bsoft");
	RNA_def_property_ui_text(prop, "Soft Body Settings", "Settings for Bullet soft body simulation.");

	/* state */

	prop= RNA_def_property(srna, "state", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "state", 1);
	RNA_def_property_array(prop, 30);
	RNA_def_property_ui_text(prop, "State", "State determining which controllers are displayed.");
	RNA_def_property_boolean_funcs(prop, NULL, "rna_GameObjectSettings_state_set");

	prop= RNA_def_property(srna, "initial_state", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "init_state", 1);
	RNA_def_property_array(prop, 30);
	RNA_def_property_ui_text(prop, "Initial State", "Initial state when the game starts.");

	prop= RNA_def_property(srna, "debug_state", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "scaflag", OB_DEBUGSTATE);
	RNA_def_property_ui_text(prop, "Debug State", "Print state debug info in the game engine.");
}

static void rna_def_object(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem object_type_items[] = {
		{OB_EMPTY, "EMPTY", 0, "Empty", ""},
		{OB_MESH, "MESH", 0, "Mesh", ""},
		{OB_CURVE, "CURVE", 0, "Curve", ""},
		{OB_SURF, "SURFACE", 0, "Surface", ""},
		{OB_FONT, "TEXT", 0, "Text", ""},
		{OB_MBALL, "META", 0, "Meta", ""},
		{OB_LAMP, "LAMP", 0, "Lamp", ""},
		{OB_CAMERA, "CAMERA", 0, "Camera", ""},
		{OB_WAVE, "WAVE", 0, "Wave", ""},
		{OB_LATTICE, "LATTICE", 0, "Lattice", ""},
		{OB_ARMATURE, "ARMATURE", 0, "Armature", ""},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem empty_drawtype_items[] = {
		{OB_ARROWS, "ARROWS", 0, "Arrows", ""},
		{OB_SINGLE_ARROW, "SINGLE_ARROW", 0, "Single Arrow", ""},
		{OB_PLAINAXES, "PLAIN_AXES", 0, "Plain Axes", ""},
		{OB_CIRCLE, "CIRCLE", 0, "Circle", ""},
		{OB_CUBE, "CUBE", 0, "Cube", ""},
		{OB_EMPTY_SPHERE, "SPHERE", 0, "Sphere", ""},
		{OB_EMPTY_CONE, "CONE", 0, "Cone", ""},
		{0, NULL, 0, NULL, NULL}};
	
	static EnumPropertyItem track_items[] = {
		{OB_POSX, "POSX", 0, "+X", ""},
		{OB_POSY, "POSY", 0, "+Y", ""},
		{OB_POSZ, "POSZ", 0, "+Z", ""},
		{OB_NEGX, "NEGX", 0, "-X", ""},
		{OB_NEGY, "NEGY", 0, "-Y", ""},
		{OB_NEGZ, "NEGZ", 0, "-Z", ""},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem up_items[] = {
		{OB_POSX, "X", 0, "X", ""},
		{OB_POSY, "Y", 0, "Y", ""},
		{OB_POSZ, "Z", 0, "Z", ""},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem drawtype_items[] = {
		{OB_BOUNDBOX, "BOUNDS", 0, "Bounds", ""},
		{OB_WIRE, "WIRE", 0, "Wire", ""},
		{OB_SOLID, "SOLID", 0, "Solid", ""},
		{OB_SHADED, "SHADED", 0, "Shaded", ""},
		{OB_TEXTURE, "TEXTURED", 0, "Textured", ""},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem boundtype_items[] = {
		{OB_BOUND_BOX, "BOX", 0, "Box", ""},
		{OB_BOUND_SPHERE, "SPHERE", 0, "Sphere", ""},
		{OB_BOUND_CYLINDER, "CYLINDER", 0, "Cylinder", ""},
		{OB_BOUND_CONE, "CONE", 0, "Cone", ""},
		{OB_BOUND_POLYH, "POLYHEDER", 0, "Polyheder", ""},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem dupli_items[] = {
		{0, "NONE", 0, "None", ""},
		{OB_DUPLIFRAMES, "FRAMES", 0, "Frames", "Make copy of object for every frame."},
		{OB_DUPLIVERTS, "VERTS", 0, "Verts", "Duplicate child objects on all vertices."},
		{OB_DUPLIFACES, "FACES", 0, "Faces", "Duplicate child objects on all faces."},
		{OB_DUPLIGROUP, "GROUP", 0, "Group", "Enable group instancing."},
		{0, NULL, 0, NULL, NULL}};

	unsigned short matrix_dimsize[]= {4};

	srna= RNA_def_struct(brna, "Object", "ID");
	RNA_def_struct_ui_text(srna, "Object", "Object datablock defining an object in a scene..");
	RNA_def_struct_clear_flag(srna, STRUCT_ID_REFCOUNT);
	RNA_def_struct_ui_icon(srna, ICON_OBJECT_DATA);

	prop= RNA_def_property(srna, "data", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "ID");
	RNA_def_property_pointer_funcs(prop, NULL, "rna_Object_data_set", "rna_Object_data_typef");
	RNA_def_property_editable_func(prop, "rna_Object_data_editable");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Data", "Object data.");
	RNA_def_property_update(prop, 0, "rna_Object_update_data");

	prop= RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "type");
	RNA_def_property_enum_items(prop, object_type_items);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Type", "Type of Object.");

	prop= RNA_def_property(srna, "mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "mode");
	RNA_def_property_enum_items(prop, object_mode_items);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Mode", "Object interaction mode.");

	prop= RNA_def_property(srna, "layers", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "lay", 1);
	RNA_def_property_array(prop, 20);
	RNA_def_property_ui_text(prop, "Layers", "Layers the object is on.");
	RNA_def_property_boolean_funcs(prop, NULL, "rna_Object_layer_set");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_layer_update");

	prop= RNA_def_property(srna, "selected", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SELECT);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Selected", "Object selection state.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	/* parent and track */

	prop= RNA_def_property(srna, "parent", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_funcs(prop, NULL, "rna_Object_parent_set", NULL);
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Parent", "Parent Object");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_dependency_update");
	
	prop= RNA_def_property(srna, "parent_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "partype");
	RNA_def_property_enum_items(prop, parent_type_items);
	RNA_def_property_enum_funcs(prop, NULL, "rna_Object_parent_type_set", "rna_Object_parent_type_itemf");
	RNA_def_property_ui_text(prop, "Parent Type", "Type of parent relation.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_dependency_update");

	prop= RNA_def_property(srna, "parent_vertices", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_int_sdna(prop, NULL, "par1");
	RNA_def_property_array(prop, 3);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Parent Vertices", "Indices of vertices in cases of a vertex parenting relation.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_update");

	prop= RNA_def_property(srna, "parent_bone", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "parsubstr");
	RNA_def_property_string_funcs(prop, NULL, NULL, "rna_Object_parent_bone_set");
	RNA_def_property_ui_text(prop, "Parent Bone", "Name of parent bone in case of a bone parenting relation.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_dependency_update");

	prop= RNA_def_property(srna, "track", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_funcs(prop, NULL, "rna_Object_track_set", NULL);
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Track", "Object being tracked to define the rotation (Old Track).");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_dependency_update");

	prop= RNA_def_property(srna, "track_axis", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "trackflag");
	RNA_def_property_enum_items(prop, track_items);
	RNA_def_property_ui_text(prop, "Track Axis", "Tracking axis pointing to the another object.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_update");

	prop= RNA_def_property(srna, "up_axis", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "upflag");
	RNA_def_property_enum_items(prop, up_items);
	RNA_def_property_ui_text(prop, "Up Axis", "Specify the axis that points up.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_update");

	/* proxy */

	prop= RNA_def_property(srna, "proxy", PROP_POINTER, PROP_NONE);
	RNA_def_property_ui_text(prop, "Proxy", "Library object this proxy object controls.");

	prop= RNA_def_property(srna, "proxy_group", PROP_POINTER, PROP_NONE);
	RNA_def_property_ui_text(prop, "Proxy Group", "Library group duplicator object this proxy object controls.");

	/* materials */
	prop= RNA_def_property(srna, "materials", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "mat", "totcol");
	RNA_def_property_struct_type(prop, "MaterialSlot");
	RNA_def_property_collection_funcs(prop, NULL, NULL, NULL, "rna_iterator_array_get", 0, 0, 0, 0, 0); /* don't dereference pointer! */
	RNA_def_property_ui_text(prop, "Materials", "Material slots in the object.");

	prop= RNA_def_property(srna, "active_material", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "Material");
	RNA_def_property_pointer_funcs(prop, "rna_Object_active_material_get", "rna_Object_active_material_set", NULL);
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Active Material", "Active material being displayed.");
	RNA_def_property_update(prop, NC_OBJECT|ND_SHADING, "rna_Object_update");

	prop= RNA_def_property(srna, "active_material_index", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_int_sdna(prop, NULL, "actcol");
	RNA_def_property_int_funcs(prop, "rna_Object_active_material_index_get", "rna_Object_active_material_index_set", "rna_Object_active_material_index_range");
	RNA_def_property_ui_text(prop, "Active Material Index", "Index of active material slot.");
	RNA_def_property_update(prop, NC_OBJECT|ND_SHADING, NULL);
	
	/* transform */

	prop= RNA_def_property(srna, "location", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_float_sdna(prop, NULL, "loc");
	RNA_def_property_ui_text(prop, "Location", "Location of the object.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");

	prop= RNA_def_property(srna, "delta_location", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_float_sdna(prop, NULL, "dloc");
	RNA_def_property_ui_text(prop, "Delta Location", "Extra added translation to object location.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");
	
	prop= RNA_def_property(srna, "rotation", PROP_FLOAT, PROP_EULER);
	RNA_def_property_float_sdna(prop, NULL, "rot");
	RNA_def_property_ui_text(prop, "Rotation", "Rotation of the object.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");

	prop= RNA_def_property(srna, "delta_rotation", PROP_FLOAT, PROP_EULER);
	RNA_def_property_float_sdna(prop, NULL, "drot");
	RNA_def_property_ui_text(prop, "Delta Rotation", "Extra added rotation to the rotation of the object.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");
	
	prop= RNA_def_property(srna, "scale", PROP_FLOAT, PROP_XYZ);
	RNA_def_property_float_sdna(prop, NULL, "size");
	RNA_def_property_ui_text(prop, "Scale", "Scaling of the object.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");

	prop= RNA_def_property(srna, "delta_scale", PROP_FLOAT, PROP_XYZ);
	RNA_def_property_float_sdna(prop, NULL, "dsize");
	RNA_def_property_ui_text(prop, "Delta Scale", "Extra added scaling to the scale of the object.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");

	prop= RNA_def_property(srna, "lock_location", PROP_BOOLEAN, PROP_XYZ);
	RNA_def_property_boolean_sdna(prop, NULL, "protectflag", OB_LOCK_LOCX);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Lock Location", "Lock editing of location in the interface.");

	prop= RNA_def_property(srna, "lock_rotation", PROP_BOOLEAN, PROP_XYZ);
	RNA_def_property_boolean_sdna(prop, NULL, "protectflag", OB_LOCK_ROTX);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Lock Rotation", "Lock editing of rotation in the interface.");

	prop= RNA_def_property(srna, "lock_scale", PROP_BOOLEAN, PROP_XYZ);
	RNA_def_property_boolean_sdna(prop, NULL, "protectflag", OB_LOCK_SCALEX);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Lock Scale", "Lock editing of scale in the interface.");

	/* matrix */
	prop= RNA_def_property(srna, "matrix", PROP_FLOAT, PROP_MATRIX);
	RNA_def_property_float_sdna(prop, NULL, "obmat");
	RNA_def_property_multidimensional_array(prop, 16, 2, matrix_dimsize);
	RNA_def_property_ui_text(prop, "Matrix", "Transformation matrix.");

	/* collections */
	prop= RNA_def_property(srna, "constraints", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "Constraint");
	RNA_def_property_ui_text(prop, "Constraints", "Constraints of the object.");

	prop= RNA_def_property(srna, "modifiers", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "Modifier");
	RNA_def_property_ui_text(prop, "Modifiers", "Modifiers affecting the geometric data of the Object.");

	/* game engine */

	prop= RNA_def_property(srna, "game", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "GameObjectSettings");
	RNA_def_property_pointer_funcs(prop, "rna_Object_game_settings_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Game Settings", "Game engine related settings for the object.");

	/* vertex groups */

	prop= RNA_def_property(srna, "vertex_groups", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "defbase", NULL);
	RNA_def_property_struct_type(prop, "VertexGroup");
	RNA_def_property_ui_text(prop, "Vertex Groups", "Vertex groups of the object.");

	prop= RNA_def_property(srna, "active_vertex_group", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "VertexGroup");
	RNA_def_property_pointer_funcs(prop, "rna_Object_active_vertex_group_get", "rna_Object_active_vertex_group_set", NULL);
	RNA_def_property_ui_text(prop, "Active Vertex Group", "Vertex groups of the object.");
	RNA_def_property_update(prop, 0, "rna_Object_update_data");

	prop= RNA_def_property(srna, "active_vertex_group_index", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "actdef");
	RNA_def_property_int_funcs(prop, "rna_Object_active_vertex_group_index_get", "rna_Object_active_vertex_group_index_set", "rna_Object_active_vertex_group_index_range");
	RNA_def_property_ui_text(prop, "Active Vertex Group Index", "Active index in vertex group array.");
	RNA_def_property_update(prop, 0, "rna_Object_update_data");

	/* empty */

	prop= RNA_def_property(srna, "empty_draw_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "empty_drawtype");
	RNA_def_property_enum_items(prop, empty_drawtype_items);
	RNA_def_property_ui_text(prop, "Empty Draw Type", "Viewport display style for empties.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	prop= RNA_def_property(srna, "empty_draw_size", PROP_FLOAT, PROP_DISTANCE);
	RNA_def_property_float_sdna(prop, NULL, "empty_drawsize");
	RNA_def_property_range(prop, 0.01, 10.0);
	RNA_def_property_ui_text(prop, "Empty Draw Size", "Size of of display for empties in the viewport.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	/* render */

	prop= RNA_def_property(srna, "pass_index", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_int_sdna(prop, NULL, "index");
	RNA_def_property_ui_text(prop, "Pass Index", "Index # for the IndexOB render pass.");

	prop= RNA_def_property(srna, "color", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "col");
	RNA_def_property_ui_text(prop, "Color", "Object color and alpha, used when faces have the ObColor mode enabled.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	/* physics */

	prop= RNA_def_property(srna, "field", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "pd");
	RNA_def_property_struct_type(prop, "FieldSettings");
	RNA_def_property_pointer_funcs(prop, "rna_Object_field_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Field Settings", "Settings for using the objects as a field in physics simulation.");

	prop= RNA_def_property(srna, "collision", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "pd");
	RNA_def_property_struct_type(prop, "CollisionSettings");
	RNA_def_property_pointer_funcs(prop, "rna_Object_collision_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Collision Settings", "Settings for using the objects as a collider in physics simulation.");

	prop= RNA_def_property(srna, "soft_body", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "soft");
	RNA_def_property_ui_text(prop, "Soft Body Settings", "Settings for soft body simulation.");

	prop= RNA_def_property(srna, "particle_systems", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "particlesystem", NULL);
	RNA_def_property_struct_type(prop, "ParticleSystem");
	RNA_def_property_ui_text(prop, "Particle Systems", "Particle systems emitted from the object.");

	prop= RNA_def_property(srna, "active_particle_system", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "ParticleSystem");
	RNA_def_property_pointer_funcs(prop, "rna_Object_active_particle_system_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Active Particle System", "Active particle system being displayed");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	prop= RNA_def_property(srna, "active_particle_system_index", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_int_funcs(prop, "rna_Object_active_particle_system_index_get", "rna_Object_active_particle_system_index_set", "rna_Object_active_particle_system_index_range");
	RNA_def_property_ui_text(prop, "Active Particle System Index", "Index of active particle system slot.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	/* restrict */

	prop= RNA_def_property(srna, "restrict_view", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "restrictflag", OB_RESTRICT_VIEW);
	RNA_def_property_ui_text(prop, "Restrict View", "Restrict visibility in the viewport.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	prop= RNA_def_property(srna, "restrict_select", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "restrictflag", OB_RESTRICT_SELECT);
	RNA_def_property_ui_text(prop, "Restrict Select", "Restrict selection in the viewport.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	prop= RNA_def_property(srna, "restrict_render", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "restrictflag", OB_RESTRICT_RENDER);
	RNA_def_property_ui_text(prop, "Restrict Render", "Restrict renderability.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	/* anim */
	
	rna_def_animdata_common(srna);
	
	prop= RNA_def_property(srna, "draw_keys", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ipoflag", OB_DRAWKEY);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE); // update ipo flag indirect
	RNA_def_property_ui_text(prop, "Draw Keys", "Draw object as key positions.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_update");

	prop= RNA_def_property(srna, "draw_keys_selected", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ipoflag", OB_DRAWKEYSEL);
	RNA_def_property_ui_text(prop, "Draw Keys Selected", "Limit the drawing of object keys to selected.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	prop= RNA_def_property(srna, "track_override_parent", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transflag", OB_POWERTRACK);
	RNA_def_property_ui_text(prop, "Track Override Parent", "Override rotation from parenting.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_update");

	prop= RNA_def_property(srna, "slow_parent", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "partype", PARSLOW);
	RNA_def_property_ui_text(prop, "Slow Parent", "Create a delay in the parent relationship.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_update");

	prop= RNA_def_property(srna, "dupli_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_bitflag_sdna(prop, NULL, "transflag");
	RNA_def_property_enum_items(prop, dupli_items);
	RNA_def_property_ui_text(prop, "Dupli Type", "If not None, object duplication method to use.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_dependency_update");

	prop= RNA_def_property(srna, "dupli_frames_no_speed", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transflag", OB_DUPLINOSPEED);
	RNA_def_property_ui_text(prop, "Dupli Frames No Speed", "Set dupliframes to still, regardless of frame.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_update");

	prop= RNA_def_property(srna, "dupli_verts_rotation", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transflag", OB_DUPLIROT);
	RNA_def_property_ui_text(prop, "Dupli Verts Rotation", "Rotate dupli according to vertex normal.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	prop= RNA_def_property(srna, "dupli_faces_inherit_scale", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transflag", OB_DUPLIROT);
	RNA_def_property_ui_text(prop, "Dupli Faces Inherit Scale", "Scale dupli based on face size.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_update");

	prop= RNA_def_property(srna, "dupli_faces_scale", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "dupfacesca");
	RNA_def_property_range(prop, 0.001f, 10000.0f);
	RNA_def_property_ui_text(prop, "Dupli Faces Scale", "Scale the DupliFace objects.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	prop= RNA_def_property(srna, "dupli_group", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "dup_group");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Dupli Group", "Instance an existing group.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_dependency_update");

	prop= RNA_def_property(srna, "dupli_frames_start", PROP_INT, PROP_NONE|PROP_UNIT_TIME);
	RNA_def_property_int_sdna(prop, NULL, "dupsta");
	RNA_def_property_range(prop, 1, 32767);
	RNA_def_property_ui_text(prop, "Dupli Frames Start", "Start frame for DupliFrames.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_update");

	prop= RNA_def_property(srna, "dupli_frames_end", PROP_INT, PROP_NONE|PROP_UNIT_TIME);
	RNA_def_property_int_sdna(prop, NULL, "dupend");
	RNA_def_property_range(prop, 1, 32767);
	RNA_def_property_ui_text(prop, "Dupli Frames End", "End frame for DupliFrames.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_update");

	prop= RNA_def_property(srna, "dupli_frames_on", PROP_INT, PROP_NONE|PROP_UNIT_TIME);
	RNA_def_property_int_sdna(prop, NULL, "dupon");
	RNA_def_property_range(prop, 1, 1500);
	RNA_def_property_ui_text(prop, "Dupli Frames On", "Number of frames to use between DupOff frames.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_update");

	prop= RNA_def_property(srna, "dupli_frames_off", PROP_INT, PROP_NONE|PROP_UNIT_TIME);
	RNA_def_property_int_sdna(prop, NULL, "dupoff");
	RNA_def_property_range(prop, 0, 1500);
	RNA_def_property_ui_text(prop, "Dupli Frames Off", "Recurring frames to exclude from the Dupliframes.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, "rna_Object_update");

	/* time offset */

	prop= RNA_def_property(srna, "time_offset", PROP_FLOAT, PROP_NONE|PROP_UNIT_TIME);
	RNA_def_property_float_sdna(prop, NULL, "sf");
	RNA_def_property_range(prop, MINAFRAMEF, MAXFRAMEF);
	RNA_def_property_ui_text(prop, "Time Offset", "Animation offset in frames for IPO's and dupligroup instances.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");

	prop= RNA_def_property(srna, "time_offset_edit", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ipoflag", OB_OFFS_OB);
	RNA_def_property_ui_text(prop, "Time Offset Edit", "Use time offset when inserting keys and display time offset for IPO and action views.");

	prop= RNA_def_property(srna, "time_offset_parent", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ipoflag", OB_OFFS_PARENT);
	RNA_def_property_ui_text(prop, "Time Offset Parent", "Apply the time offset to this objects parent relationship.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");

	prop= RNA_def_property(srna, "time_offset_particle", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ipoflag", OB_OFFS_PARTICLE);
	RNA_def_property_ui_text(prop, "Time Offset Particle", "Let the time offset work on the particle effect.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");

	prop= RNA_def_property(srna, "time_offset_add_parent", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ipoflag", OB_OFFS_PARENTADD);
	RNA_def_property_ui_text(prop, "Time Offset Add Parent", "Add the parents time offset value");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");

	/* drawing */

	prop= RNA_def_property(srna, "max_draw_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "dt");
	RNA_def_property_enum_items(prop, drawtype_items);
	RNA_def_property_ui_text(prop, "Maximum Draw Type",  "Maximum draw type to display object with in viewport.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	prop= RNA_def_property(srna, "draw_bounds", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dtx", OB_BOUNDBOX);
	RNA_def_property_ui_text(prop, "Draw Bounds", "Displays the object's bounds.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	prop= RNA_def_property(srna, "draw_bounds_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "boundtype");
	RNA_def_property_enum_items(prop, boundtype_items);
	RNA_def_property_ui_text(prop, "Draw Bounds Type", "Object boundary display type.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);
	
	prop= RNA_def_property(srna, "draw_name", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dtx", OB_DRAWNAME);
	RNA_def_property_ui_text(prop, "Draw Name", "Displays the object's name.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);
	
	prop= RNA_def_property(srna, "draw_axis", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dtx", OB_AXIS);
	RNA_def_property_ui_text(prop, "Draw Axis", "Displays the object's center and axis");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);
	
	prop= RNA_def_property(srna, "draw_texture_space", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dtx", OB_TEXSPACE);
	RNA_def_property_ui_text(prop, "Draw Texture Space", "Displays the object's texture space.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);
	
	prop= RNA_def_property(srna, "draw_wire", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dtx", OB_DRAWWIRE);
	RNA_def_property_ui_text(prop, "Draw Wire", "Adds the object's wireframe over solid drawing.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);
	
	prop= RNA_def_property(srna, "draw_transparent", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dtx", OB_DRAWTRANSP);
	RNA_def_property_ui_text(prop, "Draw Transparent", "Enables transparent materials for the object (Mesh only).");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);
	
	prop= RNA_def_property(srna, "x_ray", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "dtx", OB_DRAWXRAY);
	RNA_def_property_ui_text(prop, "X-Ray", "Makes the object draw in front of others.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);
	
	/* Grease Pencil */
	prop= RNA_def_property(srna, "grease_pencil", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "gpd");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_struct_type(prop, "GreasePencil");
	RNA_def_property_ui_text(prop, "Grease Pencil Data", "Grease Pencil datablock");
	
	/* pose */
	prop= RNA_def_property(srna, "pose_library", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "poselib");
	RNA_def_property_struct_type(prop, "Action");
	RNA_def_property_ui_text(prop, "Pose Library", "Action used as a pose library for armatures.");

	prop= RNA_def_property(srna, "pose", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "pose");
	RNA_def_property_struct_type(prop, "Pose");
	RNA_def_property_ui_text(prop, "Pose", "Current pose for armatures.");

	/* shape keys */

	prop= RNA_def_property(srna, "shape_key_lock", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "shapeflag", OB_SHAPE_LOCK);
	RNA_def_property_boolean_funcs(prop, NULL, "rna_Object_shape_key_lock_set");
	RNA_def_property_ui_text(prop, "Shape Key Lock", "Always show the current Shape for this Object.");
	RNA_def_property_ui_icon(prop, ICON_UNPINNED, 1);
	RNA_def_property_update(prop, 0, "rna_Object_update_data");

	prop= RNA_def_property(srna, "active_shape_key", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "ShapeKey");
	RNA_def_property_pointer_funcs(prop, "rna_Object_active_shape_key_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Active Shape Key", "Current shape key.");

	prop= RNA_def_property(srna, "active_shape_key_index", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "shapenr");
	RNA_def_property_int_funcs(prop, "rna_Object_active_shape_key_index_get", "rna_Object_active_shape_key_index_set", "rna_Object_active_shape_key_index_range");
	RNA_def_property_ui_text(prop, "Active Shape Key Index", "Current shape key index.");
	RNA_def_property_update(prop, 0, "rna_Object_update_data");

	RNA_api_object(srna);
}

void RNA_def_object(BlenderRNA *brna)
{
	rna_def_object(brna);
	rna_def_object_game_settings(brna);
	rna_def_vertex_group(brna);
	rna_def_material_slot(brna);
}

#endif

