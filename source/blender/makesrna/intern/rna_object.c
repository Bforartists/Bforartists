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

#include <stdlib.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "DNA_customdata_types.h"
#include "DNA_mesh_types.h"
#include "DNA_object_types.h"
#include "DNA_property_types.h"
#include "DNA_scene_types.h"

#include "WM_types.h"

#ifdef RNA_RUNTIME

#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_material.h"

static void rna_Object_update(bContext *C, PointerRNA *ptr)
{
	DAG_object_flush_update(CTX_data_scene(C), ptr->id.data, OB_RECALC_OB);
}

static int rna_VertexGroup_index_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;

	return BLI_findindex(&ob->defbase, ptr->data);
}

static PointerRNA rna_Object_active_vertex_group_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;
	return rna_pointer_inherit_refine(ptr, &RNA_VertexGroup, BLI_findlink(&ob->defbase, ob->actdef));
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

static void rna_Object_active_material_index_range(PointerRNA *ptr, int *min, int *max)
{
	Object *ob= (Object*)ptr->id.data;
	*min= 0;
	*max= ob->totcol-1;
}

static PointerRNA rna_Object_active_material_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;
	return rna_pointer_inherit_refine(ptr, &RNA_Material, give_current_material(ob, ob->actcol));
}

#if 0
static void rna_Object_active_material_set(PointerRNA *ptr, PointerRNA value)
{
	Object *ob= (Object*)ptr->id.data;

	assign_material(ob, value.data, ob->actcol);
}
#endif

static int rna_Object_active_material_link_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;
	return (ob->colbits & 1<<(ob->actcol)) != 0;
}

static void rna_Object_active_material_link_set(PointerRNA *ptr, int value)
{
	Object *ob= (Object*)ptr->id.data;
	
	if(value)
		ob->colbits |= (1<<(ob->actcol));
	else
		ob->colbits &= ~(1<<(ob->actcol));
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

	/* ensure we always have some stateer selected */
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

#else

static void rna_def_vertex_group(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "VertexGroup", NULL);
	RNA_def_struct_sdna(srna, "bDeformGroup");
	RNA_def_struct_ui_text(srna, "Vertex Group", "Group of vertices, used for armature deform and other purposes.");

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_ui_text(prop, "Name", "Vertex group name.");
	RNA_def_struct_name_property(srna, prop);

	prop= RNA_def_property(srna, "index", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_int_funcs(prop, "rna_VertexGroup_index_get", NULL, NULL);
	RNA_def_property_ui_text(prop, "Index", "Index number of the vertex group.");
}

static void rna_def_object_game_settings(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem body_type_items[] = {
		{OB_BODY_TYPE_NO_COLLISION, "NO_COLLISION", "No Collision", ""},
		{OB_BODY_TYPE_STATIC, "STATIC", "Static", ""},
		{OB_BODY_TYPE_DYNAMIC, "DYNAMIC", "Dynamic", ""},
		{OB_BODY_TYPE_RIGID, "RIGID_BODY", "Rigid Body", ""},
		{OB_BODY_TYPE_SOFT, "SOFT_BODY", "Soft Body", ""},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem collision_bounds_items[] = {
		{OB_BOUND_BOX, "BOX", "Box", ""},
		{OB_BOUND_SPHERE, "SPHERE", "Sphere", ""},
		{OB_BOUND_CYLINDER, "CYLINDER", "Cylinder", ""},
		{OB_BOUND_CONE, "CONE", "Cone", ""},
		{OB_BOUND_POLYH, "CONVEX_HULL", "Convex Hull", ""},
		{OB_BOUND_POLYT, "TRIANGLE_MESH", "Triangle Mesh", ""},
		//{OB_DYN_MESH, "DYNAMIC_MESH", "Dynamic Mesh", ""},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "GameObjectSettings", NULL);
	RNA_def_struct_sdna(srna, "Object");
	RNA_def_struct_nested(brna, srna, "Object");
	RNA_def_struct_ui_text(srna, "Game Object Settings", "Game engine related settings for the object.");

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
	RNA_def_property_struct_type(prop, "GameProperty");
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
	RNA_def_property_clear_flag(prop, PROP_EDITABLE); // this controls various gameflags
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

	prop= RNA_def_property(srna, "radius", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "inertia");
	RNA_def_property_range(prop, 0.01, 10.0);
	RNA_def_property_ui_text(prop, "Radius", "Radius for Bounding sphere and Fh/Fh Rot.");
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

	prop= RNA_def_property(srna, "do_fh", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag", OB_DO_FH);
	RNA_def_property_ui_text(prop, "Do Fh", "Use Fh settings in materials.");

	prop= RNA_def_property(srna, "rotation_fh", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag", OB_ROT_FH);
	RNA_def_property_ui_text(prop, "Rotation Fh", "Use face normal to rotate Object");

	prop= RNA_def_property(srna, "form_factor", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "formfactor");
	RNA_def_property_range(prop, 0.0, 1.0);
	RNA_def_property_ui_text(prop, "Form Factor", "Form factor scales the inertia tensor.");

	prop= RNA_def_property(srna, "anisotropic_friction", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "gameflag", OB_ANISOTROPIC_FRICTION);
	RNA_def_property_ui_text(prop, "Anisotropic Friction", "Enable anisotropic friction.");

	prop= RNA_def_property(srna, "friction_coefficients", PROP_FLOAT, PROP_VECTOR);
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

	prop= RNA_def_property(srna, "collision_margin", PROP_FLOAT, PROP_NONE);
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

static StructRNA *rna_def_object(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem parent_type_items[] = {
		{PAROBJECT, "OBJECT", "Object", ""},
		{PARCURVE, "CURVE", "Curve", ""},
		//{PARKEY, "KEY", "Key", ""},
		{PARSKEL, "ARMATURE", "Armature", ""},
		{PARSKEL, "LATTICE", "Lattice", ""}, // PARSKEL reuse will give issues
		{PARVERT1, "VERTEX", "Vertex", ""},
		{PARVERT3, "VERTEX_3", "3 Vertices", ""},
		{PARBONE, "BONE", "Bone", ""},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem empty_drawtype_items[] = {
		{OB_ARROWS, "ARROWS", "Arrows", ""},
		{OB_SINGLE_ARROW, "SINGLE_ARROW", "Single Arrow", ""},
		{OB_PLAINAXES, "PLAIN_AXES", "Plain Axes", ""},
		{OB_CIRCLE, "CIRCLE", "Circle", ""},
		{OB_CUBE, "CUBE", "Cube", ""},
		{OB_EMPTY_SPHERE, "SPHERE", "Sphere", ""},
		{OB_EMPTY_CONE, "CONE", "Cone", ""},
		{0, NULL, NULL, NULL}};
	
	static EnumPropertyItem track_items[] = {
		{OB_POSX, "POSX", "+X", ""},
		{OB_POSY, "POSY", "+Y", ""},
		{OB_POSZ, "POSZ", "+Z", ""},
		{OB_NEGX, "NEGX", "-X", ""},
		{OB_NEGY, "NEGY", "-Y", ""},
		{OB_NEGZ, "NEGZ", "-Z", ""},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem up_items[] = {
		{OB_POSX, "X", "X", ""},
		{OB_POSY, "Y", "Y", ""},
		{OB_POSZ, "Z", "Z", ""},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem drawtype_items[] = {
		{OB_BOUNDBOX, "BOUNDS", "Bounds", ""},
		{OB_WIRE, "WIRE", "Wire", ""},
		{OB_SOLID, "SOLID", "Solid", ""},
		{OB_SHADED, "SHADED", "Shaded", ""},
		{OB_TEXTURE, "TEXTURED", "Textured", ""},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem boundtype_items[] = {
		{OB_BOUND_BOX, "BOX", "Box", ""},
		{OB_BOUND_SPHERE, "SPHERE", "Sphere", ""},
		{OB_BOUND_CYLINDER, "CYLINDER", "Cylinder", ""},
		{OB_BOUND_CONE, "CONE", "Cone", ""},
		{OB_BOUND_POLYH, "POLYHEDER", "Polyheder", ""},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem material_link_items[] = {
		{0, "DATA", "Data", ""},
		{1, "OBJECT", "Object", ""},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "Object", "ID");
	RNA_def_struct_ui_text(srna, "Object", "Object datablock defining an object in a scene..");

	prop= RNA_def_property(srna, "data", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "ID");
	RNA_def_property_ui_text(prop, "Data", "Object data.");

	prop= RNA_def_property(srna, "layers", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "lay", 1);
	RNA_def_property_array(prop, 20);
	RNA_def_property_ui_text(prop, "Layers", "Layers the object is on.");
	RNA_def_property_boolean_funcs(prop, NULL, "rna_Object_layer_set");

	prop= RNA_def_property(srna, "selected", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SELECT);
	RNA_def_property_ui_text(prop, "Selected", "Object selection state.");

	/* parent and track */

	prop= RNA_def_property(srna, "parent", PROP_POINTER, PROP_NONE);
	RNA_def_property_ui_text(prop, "Parent", "Parent Object");

	prop= RNA_def_property(srna, "parent_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "partype");
	RNA_def_property_enum_items(prop, parent_type_items);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Parent Type", "Type of parent relation.");

	prop= RNA_def_property(srna, "parent_vertices", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_int_sdna(prop, NULL, "par1");
	RNA_def_property_array(prop, 3);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Parent Vertices", "Indices of vertices in cases of a vertex parenting relation.");

	prop= RNA_def_property(srna, "parent_bone", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "parsubstr");
	RNA_def_property_ui_text(prop, "Parent Bone", "Name of parent bone in case of a bone parenting relation.");

	prop= RNA_def_property(srna, "track", PROP_POINTER, PROP_NONE);
	RNA_def_property_ui_text(prop, "Track", "Object being tracked to define the rotation (Old Track).");

	prop= RNA_def_property(srna, "track_axis", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "trackflag");
	RNA_def_property_enum_items(prop, track_items);
	RNA_def_property_ui_text(prop, "Track Axis", "Tracking axis pointing to the another object.");

	prop= RNA_def_property(srna, "up_axis", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "upflag");
	RNA_def_property_enum_items(prop, up_items);
	RNA_def_property_ui_text(prop, "Up Axis", "Specify the axis that points up.");

	/* proxy */

	prop= RNA_def_property(srna, "proxy", PROP_POINTER, PROP_NONE);
	RNA_def_property_ui_text(prop, "Proxy", "Library object this proxy object controls.");

	prop= RNA_def_property(srna, "proxy_group", PROP_POINTER, PROP_NONE);
	RNA_def_property_ui_text(prop, "Proxy Group", "Library group duplicator object this proxy object controls.");

	/* materials */

	prop= RNA_def_property(srna, "materials", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "mat", "totcol");
	RNA_def_property_struct_type(prop, "Material");
	RNA_def_property_ui_text(prop, "Materials", "");

	prop= RNA_def_property(srna, "active_material", PROP_POINTER, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_struct_type(prop, "Material");
	RNA_def_property_pointer_funcs(prop, "rna_Object_active_material_get", NULL);
	RNA_def_property_ui_text(prop, "Active Material", "Active material being displayed.");

	prop= RNA_def_property(srna, "active_material_index", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_int_sdna(prop, NULL, "actcol");
	RNA_def_property_int_funcs(prop, NULL, NULL, "rna_Object_active_material_index_range");
	RNA_def_property_ui_text(prop, "Active Material Index", "Index of active material.");

	prop= RNA_def_property(srna, "active_material_link", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, material_link_items);
	RNA_def_property_enum_funcs(prop, "rna_Object_active_material_link_get", "rna_Object_active_material_link_set");
	RNA_def_property_ui_text(prop, "Active Material Link", "Use material from object or data for the active material.");

	/* transform */

	prop= RNA_def_property(srna, "location", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_float_sdna(prop, NULL, "loc");
	RNA_def_property_ui_text(prop, "Location", "Location of the object.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");

	prop= RNA_def_property(srna, "delta_location", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_float_sdna(prop, NULL, "dloc");
	RNA_def_property_ui_text(prop, "Delta Location", "Extra added translation to object location.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");
	
	prop= RNA_def_property(srna, "rotation", PROP_FLOAT, PROP_ROTATION);
	RNA_def_property_float_sdna(prop, NULL, "rot");
	RNA_def_property_ui_text(prop, "Rotation", "Rotation of the object.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");

	prop= RNA_def_property(srna, "delta_rotation", PROP_FLOAT, PROP_ROTATION);
	RNA_def_property_float_sdna(prop, NULL, "drot");
	RNA_def_property_ui_text(prop, "Delta Rotation", "Extra added rotation to the rotation of the object.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");
	
	prop= RNA_def_property(srna, "scale", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_float_sdna(prop, NULL, "size");
	RNA_def_property_ui_text(prop, "Scale", "Scaling of the object.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");

	prop= RNA_def_property(srna, "delta_scale", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_float_sdna(prop, NULL, "dsize");
	RNA_def_property_ui_text(prop, "Delta Scale", "Extra added scaling to the scale of the object.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");

	prop= RNA_def_property(srna, "lock_location", PROP_BOOLEAN, PROP_VECTOR);
	RNA_def_property_boolean_sdna(prop, NULL, "protectflag", OB_LOCK_LOCX);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Lock Location", "Lock editing of location in the interface.");

	prop= RNA_def_property(srna, "lock_rotation", PROP_BOOLEAN, PROP_VECTOR);
	RNA_def_property_boolean_sdna(prop, NULL, "protectflag", OB_LOCK_ROTX);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Lock Rotation", "Lock editing of rotation in the interface.");

	prop= RNA_def_property(srna, "lock_scale", PROP_BOOLEAN, PROP_VECTOR);
	RNA_def_property_boolean_sdna(prop, NULL, "protectflag", OB_LOCK_SCALEX);
	RNA_def_property_array(prop, 3);
	RNA_def_property_ui_text(prop, "Lock Scale", "Lock editing of scale in the interface.");

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
	RNA_def_property_pointer_funcs(prop, "rna_Object_game_settings_get", NULL);
	RNA_def_property_ui_text(prop, "Game Settings", "Game engine related settings for the object.");

	/* vertex groups */

	prop= RNA_def_property(srna, "vertex_groups", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "defbase", NULL);
	RNA_def_property_struct_type(prop, "VertexGroup");
	RNA_def_property_ui_text(prop, "Vertex Groups", "Vertex groups of the object.");

	prop= RNA_def_property(srna, "active_vertex_group", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "VertexGroup");
	RNA_def_property_pointer_funcs(prop, "rna_Object_active_vertex_group_get", NULL);
	RNA_def_property_ui_text(prop, "Active Vertex Group", "Vertex groups of the object.");

	/* empty */

	prop= RNA_def_property(srna, "empty_draw_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "empty_drawtype");
	RNA_def_property_enum_items(prop, empty_drawtype_items);
	RNA_def_property_ui_text(prop, "Empty Draw Type", "Viewport display style for empties.");

	prop= RNA_def_property(srna, "empty_draw_size", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "empty_drawsize");
	RNA_def_property_range(prop, 0.01, 10.0);
	RNA_def_property_ui_text(prop, "Empty Draw Size", "Size of of display for empties in the viewport.");

	/* render */

	prop= RNA_def_property(srna, "pass_index", PROP_INT, PROP_UNSIGNED);
	RNA_def_property_int_sdna(prop, NULL, "index");
	RNA_def_property_ui_text(prop, "Pass Index", "Index # for the IndexOB render pass.");

	prop= RNA_def_property(srna, "color", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_float_sdna(prop, NULL, "col");
	RNA_def_property_ui_text(prop, "Color", "Object color and alpha, used when faces have the ObColor mode enabled.");

	/* physics */

	prop= RNA_def_property(srna, "field", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "pd");
	RNA_def_property_struct_type(prop, "FieldSettings");
	RNA_def_property_ui_text(prop, "Field Settings", "Settings for using the objects as a field in physics simulation.");

	prop= RNA_def_property(srna, "collision", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "pd");
	RNA_def_property_struct_type(prop, "CollisionSettings");
	RNA_def_property_ui_text(prop, "Collision Settings", "Settings for using the objects as a collider in physics simulation.");

	prop= RNA_def_property(srna, "soft_body", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "soft");
	RNA_def_property_ui_text(prop, "Soft Body Settings", "Settings for soft body simulation.");

	prop= RNA_def_property(srna, "particle_systems", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "particlesystem", NULL);
	RNA_def_property_struct_type(prop, "ParticleSystem");
	RNA_def_property_ui_text(prop, "Particle Systems", "Particle systems emitted from the object.");

	/* restrict */

	prop= RNA_def_property(srna, "restrict_view", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "restrictflag", OB_RESTRICT_VIEW);
	RNA_def_property_ui_text(prop, "Restrict View", "Restrict visibility in the viewport.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	prop= RNA_def_property(srna, "restrict_select", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "restrictflag", OB_RESTRICT_SELECT);
	RNA_def_property_ui_text(prop, "Restrict Select", "Restrict selection in the viewport.");

	prop= RNA_def_property(srna, "restrict_render", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "restrictflag", OB_RESTRICT_RENDER);
	RNA_def_property_ui_text(prop, "Restrict Render", "Restrict renderability.");

	/* anim */
	
	rna_def_animdata_common(srna);
	
	prop= RNA_def_property(srna, "draw_keys", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ipoflag", OB_DRAWKEY);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE); // update ipo flag indirect
	RNA_def_property_ui_text(prop, "Draw Keys", "Draw object as key positions.");

	prop= RNA_def_property(srna, "draw_keys_selected", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ipoflag", OB_DRAWKEYSEL);
	RNA_def_property_ui_text(prop, "Draw Keys Selected", "Limit the drawing of object keys to selected.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	prop= RNA_def_property(srna, "track_rotation", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transflag", OB_POWERTRACK);
	RNA_def_property_ui_text(prop, "Track Rotation", "Switch object rotation of in tracking.");

	prop= RNA_def_property(srna, "slow_parent", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "partype", PARSLOW);
	RNA_def_property_ui_text(prop, "Slow Parent", "Create a delay in the parent relationship.");

	prop= RNA_def_property(srna, "dupli_frames", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transflag", OB_DUPLIFRAMES);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE); // clear other flags
	RNA_def_property_ui_text(prop, "Dupli Frames", "Make copy of object for every frame.");

	prop= RNA_def_property(srna, "dupli_verts", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transflag", OB_DUPLIVERTS);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE); // clear other flags
	RNA_def_property_ui_text(prop, "Dupli Verts", "Duplicate child objects on all vertices.");

	prop= RNA_def_property(srna, "dupli_faces", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transflag", OB_DUPLIFACES);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE); // clear other flags
	RNA_def_property_ui_text(prop, "Dupli Faces", "Duplicate child objects on all faces.");

	prop= RNA_def_property(srna, "use_dupli_group", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transflag", OB_DUPLIGROUP);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE); // clear other flags
	RNA_def_property_ui_text(prop, "Use Dupli Group", "Enable group instancing.");

	prop= RNA_def_property(srna, "dupli_frames_no_speed", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transflag", OB_DUPLINOSPEED);
	RNA_def_property_ui_text(prop, "Dupli Frames No Speed", "Set dupliframes to still, regardless of frame.");

	prop= RNA_def_property(srna, "dupli_verts_rotation", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transflag", OB_DUPLIROT);
	RNA_def_property_ui_text(prop, "Dupli Verts Rotation", "Rotate dupli according to vertex normal.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	prop= RNA_def_property(srna, "dupli_faces_inherit_scale", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "transflag", OB_DUPLIROT);
	RNA_def_property_ui_text(prop, "Dupli Faces Inherit Scale", "Scale dupli based on face size.");

	prop= RNA_def_property(srna, "dupli_faces_scale", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "dupfacesca");
	RNA_def_property_range(prop, 0.001f, 10000.0f);
	RNA_def_property_ui_text(prop, "Dupli Faces Scale", "Scale the DupliFace objects.");
	RNA_def_property_update(prop, NC_OBJECT|ND_DRAW, NULL);

	prop= RNA_def_property(srna, "dupli_group", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "dup_group");
	RNA_def_property_ui_text(prop, "Dupli Group", "Instance an existing group.");

	prop= RNA_def_property(srna, "dupli_frames_start", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "dupsta");
	RNA_def_property_range(prop, 1, 32767);
	RNA_def_property_ui_text(prop, "Dupli Frames Start", "Start frame for DupliFrames.");

	prop= RNA_def_property(srna, "dupli_frames_end", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "dupend");
	RNA_def_property_range(prop, 1, 32767);
	RNA_def_property_ui_text(prop, "Dupli Frames End", "End frame for DupliFrames.");

	prop= RNA_def_property(srna, "dupli_frames_on", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "dupon");
	RNA_def_property_range(prop, 1, 1500);
	RNA_def_property_ui_text(prop, "Dupli Frames On", "Number of frames to use between DupOff frames.");

	prop= RNA_def_property(srna, "dupli_frames_off", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "dupoff");
	RNA_def_property_range(prop, 0, 1500);
	RNA_def_property_ui_text(prop, "Dupli Frames Off", "Recurring frames to exclude from the Dupliframes.");

	/* time offset */

	prop= RNA_def_property(srna, "time_offset", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "sf");
	RNA_def_property_range(prop, -MAXFRAMEF, MAXFRAMEF);
	RNA_def_property_ui_text(prop, "Time Offset", "Animation offset in frames for ipo's and dupligroup instances.");
	RNA_def_property_update(prop, NC_OBJECT|ND_TRANSFORM, "rna_Object_update");

	prop= RNA_def_property(srna, "time_offset_edit", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ipoflag", OB_OFFS_OB);
	RNA_def_property_ui_text(prop, "Time Offset Edit", "Use time offset when inserting keys and display time offset for ipo and action views.");

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

	/* script link */

	prop= RNA_def_property(srna, "script_link", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_pointer_sdna(prop, NULL, "scriptlink");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Script Link", "Scripts linked to this object.");

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
	
	/* pose */
	prop= RNA_def_property(srna, "pose_library", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "poselib");
	RNA_def_property_struct_type(prop, "Action");
	RNA_def_property_ui_text(prop, "Pose Library", "Action used as a pose library for armatures.");

	prop= RNA_def_property(srna, "pose", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "pose");
	RNA_def_property_struct_type(prop, "Pose");
	RNA_def_property_ui_text(prop, "Pose", "Current pose for armatures.");

	prop= RNA_def_property(srna, "pose_mode", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", OB_POSEMODE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Pose Mode", "Object with armature data is in pose mode.");

	// XXX this stuff should be moved to AnimData...
/*
	prop= RNA_def_property(srna, "nla_disable_path", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "nlaflag", OB_DISABLE_PATH);
	RNA_def_property_ui_text(prop, "NLA Disable Path", "Disable path temporally, for editing cycles.");

	prop= RNA_def_property(srna, "nla_collapsed", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "nlaflag", OB_NLA_COLLAPSED);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "NLA Collapsed", "");

	prop= RNA_def_property(srna, "nla_override", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "nlaflag", OB_NLA_OVERRIDE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "NLA Override", "");

	prop= RNA_def_property(srna, "nla_strips", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "nlastrips", NULL);
	RNA_def_property_struct_type(prop, "UnknownType");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "NLA Strips", "NLA strips of the object.");
*/
	
	/* shape keys */

	prop= RNA_def_property(srna, "shape_key_lock", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "shapeflag", OB_SHAPE_LOCK);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Shape Key Lock", "Always show the current Shape for this Object.");

	prop= RNA_def_property(srna, "active_shape_key", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "shapenr");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Active Shape Key", "Current shape key index.");
	
	return srna;
}

void RNA_def_object(BlenderRNA *brna)
{
	rna_def_object(brna);
	rna_def_object_game_settings(brna);
	rna_def_vertex_group(brna);
}

#endif

