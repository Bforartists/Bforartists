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
 * Contributor(s): Blender Foundation (2008)
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <limits.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "BKE_cloth.h"
#include "DNA_cloth_types.h"

#ifdef RNA_RUNTIME

static void rna_ClothSettings_max_bend_set(struct PointerRNA *ptr, float value)
{
	ClothSimSettings *settings = (ClothSimSettings*)ptr->data;
	
	/* check for clipping */
	if(value < settings->bending)
		value = settings->bending;
	
	settings->max_bend = value;
}

static void rna_ClothSettings_max_struct_set(struct PointerRNA *ptr, float value)
{
	ClothSimSettings *settings = (ClothSimSettings*)ptr->data;
	
	/* check for clipping */
	if(value < settings->structural)
		value = settings->structural;
	
	settings->max_struct = value;
}

static void rna_ClothSettings_mass_vgroup_get(PointerRNA *ptr, char *value)
{
	ClothSimSettings *sim= (ClothSimSettings*)ptr->data;
	rna_object_vgroup_name_index_get(ptr, value, sim->vgroup_mass);
}

static int rna_ClothSettings_mass_vgroup_length(PointerRNA *ptr)
{
	ClothSimSettings *sim= (ClothSimSettings*)ptr->data;
	return rna_object_vgroup_name_index_length(ptr, sim->vgroup_mass);
}

static void rna_ClothSettings_mass_vgroup_set(PointerRNA *ptr, const char *value)
{
	ClothSimSettings *sim= (ClothSimSettings*)ptr->data;
	rna_object_vgroup_name_index_set(ptr, value, &sim->vgroup_mass);
}

static void rna_ClothSettings_struct_vgroup_get(PointerRNA *ptr, char *value)
{
	ClothSimSettings *sim= (ClothSimSettings*)ptr->data;
	rna_object_vgroup_name_index_get(ptr, value, sim->vgroup_struct);
}

static int rna_ClothSettings_struct_vgroup_length(PointerRNA *ptr)
{
	ClothSimSettings *sim= (ClothSimSettings*)ptr->data;
	return rna_object_vgroup_name_index_length(ptr, sim->vgroup_struct);
}

static void rna_ClothSettings_struct_vgroup_set(PointerRNA *ptr, const char *value)
{
	ClothSimSettings *sim= (ClothSimSettings*)ptr->data;
	rna_object_vgroup_name_index_set(ptr, value, &sim->vgroup_struct);
}

static void rna_ClothSettings_bend_vgroup_get(PointerRNA *ptr, char *value)
{
	ClothSimSettings *sim= (ClothSimSettings*)ptr->data;
	rna_object_vgroup_name_index_get(ptr, value, sim->vgroup_bend);
}

static int rna_ClothSettings_bend_vgroup_length(PointerRNA *ptr)
{
	ClothSimSettings *sim= (ClothSimSettings*)ptr->data;
	return rna_object_vgroup_name_index_length(ptr, sim->vgroup_bend);
}

static void rna_ClothSettings_bend_vgroup_set(PointerRNA *ptr, const char *value)
{
	ClothSimSettings *sim= (ClothSimSettings*)ptr->data;
	rna_object_vgroup_name_index_set(ptr, value, &sim->vgroup_bend);
}

static void rna_ClothSettings_gravity_get(PointerRNA *ptr, float *values)
{
	ClothSimSettings *sim= (ClothSimSettings*)ptr->data;

	values[0]= sim->gravity[0];
	values[1]= sim->gravity[1];
	values[2]= sim->gravity[2];
}

static void rna_ClothSettings_gravity_set(PointerRNA *ptr, const float *values)
{
	ClothSimSettings *sim= (ClothSimSettings*)ptr->data;

	sim->gravity[0]= values[0];
	sim->gravity[1]= values[1];
	sim->gravity[2]= values[2];
}

#else

static void rna_def_cloth_sim_settings(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna = RNA_def_struct(brna, "ClothSettings", NULL);
	RNA_def_struct_ui_text(srna, "Cloth Settings", "Cloth simulation settings for an object.");
	RNA_def_struct_sdna(srna, "ClothSimSettings");
	
	/* goal */
	
	prop= RNA_def_property(srna, "goal_min", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "mingoal");
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Goal Minimum", "Goal minimum, vertex group weights are scaled to match this range.");

	prop= RNA_def_property(srna, "goal_max", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "maxgoal");
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Goal Maximum", "Goal maximum, vertex group weights are scaled to match this range.");

	prop= RNA_def_property(srna, "goal_default", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "defgoal");
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Goal Default", "Default Goal (vertex target position) value, when no Vertex Group used.");
	
	prop= RNA_def_property(srna, "goal_spring", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "goalspring");
	RNA_def_property_range(prop, 0.0f, 0.999f);
	RNA_def_property_ui_text(prop, "Goal Stiffness", "Goal (vertex target position) spring stiffness.");
	
	prop= RNA_def_property(srna, "goal_friction", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "goalfrict");
	RNA_def_property_range(prop, 0.0f, 50.0f);
	RNA_def_property_ui_text(prop, "Goal Damping", "Goal (vertex target position) friction.");

	/* mass */

	prop= RNA_def_property(srna, "mass", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.0f, 10.0f);
	RNA_def_property_ui_text(prop, "Mass", "Mass of cloth material.");

	prop= RNA_def_property(srna, "mass_vertex_group", PROP_STRING, PROP_NONE);
	RNA_def_property_string_funcs(prop, "rna_ClothSettings_mass_vgroup_get", "rna_ClothSettings_mass_vgroup_length", "rna_ClothSettings_mass_vgroup_set");
	RNA_def_property_ui_text(prop, "Mass Vertex Group", "Vertex group for fine control over mass distribution.");
	
	prop= RNA_def_property(srna, "gravity", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_range(prop, -100.0, 100.0);
	RNA_def_property_float_funcs(prop, "rna_ClothSettings_gravity_get", "rna_ClothSettings_gravity_set", NULL);
	RNA_def_property_ui_text(prop, "Gravity", "Gravity or external force vector.");

	/* various */

	prop= RNA_def_property(srna, "air_damping", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "Cvi");
	RNA_def_property_range(prop, 0.0f, 10.0f);
	RNA_def_property_ui_text(prop, "Air Damping", "Air has normally some thickness which slows falling things down.");

	prop= RNA_def_property(srna, "pin_cloth", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", CLOTH_SIMSETTINGS_FLAG_GOAL);
	RNA_def_property_ui_text(prop, "Pin Cloth", "Define forces for vertices to stick to animated position.");

	prop= RNA_def_property(srna, "pin_stiffness", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "goalspring");
	RNA_def_property_range(prop, 0.0f, 0.50);
	RNA_def_property_ui_text(prop, "Pin Stiffness", "Pin (vertex target position) spring stiffness.");

	prop= RNA_def_property(srna, "quality", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "stepsPerFrame");
	RNA_def_property_range(prop, 4, 80);
	RNA_def_property_ui_text(prop, "Quality", "Quality of the simulation in steps per frame (higher is better quality but slower).");

	/* springs */

	prop= RNA_def_property(srna, "stiffness_scaling", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", CLOTH_SIMSETTINGS_FLAG_SCALING);
	RNA_def_property_ui_text(prop, "Stiffness Scaling", "If enabled, stiffness can be scaled along a weight painted vertex group.");
	
	prop= RNA_def_property(srna, "spring_damping", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "Cdis");
	RNA_def_property_range(prop, 0.0f, 50.0f);
	RNA_def_property_ui_text(prop, "Spring Damping", "Damping of cloth velocity (higher = more smooth, less jiggling)");
	
	prop= RNA_def_property(srna, "structural_stiffness", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "structural");
	RNA_def_property_range(prop, 1.0f, 10000.0f);
	RNA_def_property_ui_text(prop, "Structural Stiffness", "Overall stiffness of structure.");

	prop= RNA_def_property(srna, "structural_stiffness_max", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "max_struct");
	RNA_def_property_range(prop, 0.0f, 10000.0f);
	RNA_def_property_float_funcs(prop, NULL, "rna_ClothSettings_max_struct_set", NULL);
	RNA_def_property_ui_text(prop, "Structural Stiffness Maximum", "Maximum structural stiffness value.");

	prop= RNA_def_property(srna, "structural_stiffness_vertex_group", PROP_STRING, PROP_NONE);
	RNA_def_property_string_funcs(prop, "rna_ClothSettings_struct_vgroup_get", "rna_ClothSettings_struct_vgroup_length", "rna_ClothSettings_struct_vgroup_set");
	RNA_def_property_ui_text(prop, "Structural Stiffness Vertex Group", "Vertex group for fine control over structural stiffness.");

	prop= RNA_def_property(srna, "bending_stiffness", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "bending");
	RNA_def_property_range(prop, 0.0f, 10000.0f);
	RNA_def_property_ui_text(prop, "Bending Stiffness", "Wrinkle coefficient (higher = less smaller but more big wrinkles).");

	prop= RNA_def_property(srna, "bending_stiffness_max", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "max_bend");
	RNA_def_property_range(prop, 0.0f, 10000.0f);
	RNA_def_property_float_funcs(prop, NULL, "rna_ClothSettings_max_bend_set", NULL);
	RNA_def_property_ui_text(prop, "Bending Stiffness Maximum", "Maximum bending stiffness value.");

	prop= RNA_def_property(srna, "bending_vertex_group", PROP_STRING, PROP_NONE);
	RNA_def_property_string_funcs(prop, "rna_ClothSettings_bend_vgroup_get", "rna_ClothSettings_bend_vgroup_length", "rna_ClothSettings_bend_vgroup_set");
	RNA_def_property_ui_text(prop, "Bending Stiffness Vertex Group", "Vertex group for fine control over bending stiffness.");

	/* unused */

	/* unused still
	prop= RNA_def_property(srna, "shear_stiffness", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "shear");
	RNA_def_property_range(prop, 0.0f, 1000.0f);
	RNA_def_property_ui_text(prop, "Shear Stiffness", "Shear spring stiffness."); */

	/* unused still
	prop= RNA_def_property(srna, "shear_stiffness_max", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "max_shear");
	RNA_def_property_range(prop, 0.0f, upperLimitf);
	RNA_def_property_ui_text(prop, "Shear Stiffness Maximum", "Maximum shear scaling value."); */
	
	/* unused still
	prop= RNA_def_property(srna, "effector_force_scale", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "eff_force_scale");
	RNA_def_property_range(prop, 0.0f, 100.0f);
	RNA_def_property_ui_text(prop, "Effector Force Scale", ""); */

	/* unused still
	prop= RNA_def_property(srna, "effector_wind_scale", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "eff_wind_scale");
	RNA_def_property_range(prop, 0.0f, 100.0f);
	RNA_def_property_ui_text(prop, "Effector Wind Scale", ""); */
	
	/* unused still
	prop= RNA_def_property(srna, "pre_roll", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "preroll");
	RNA_def_property_range(prop, 10, 80;
	RNA_def_property_ui_text(prop, "Pre Roll", "Simulation starts on this frame."); */

	/* unused still
	prop= RNA_def_property(srna, "tearing", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", CLOTH_SIMSETTINGS_FLAG_TEARING);
	RNA_def_property_ui_text(prop, "Tearing", "");*/
	
	/* unused still
	prop= RNA_def_property(srna, "max_spring_extensions", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "maxspringlen");
	RNA_def_property_range(prop, 1.0, 1000.0);
	RNA_def_property_ui_text(prop, "Maximum Spring Extension", "Maximum extension before spring gets cut."); */
}

static void rna_def_cloth_collision_settings(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	srna = RNA_def_struct(brna, "ClothCollisionSettings", NULL);
	RNA_def_struct_ui_text(srna, "Cloth Collision Settings", "Cloth simulation settings for self collision and collision with other objects.");
	RNA_def_struct_sdna(srna, "ClothCollSettings");

	/* general collision */

	prop= RNA_def_property(srna, "enable_collision", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", CLOTH_COLLSETTINGS_FLAG_ENABLED);
	RNA_def_property_ui_text(prop, "Enable Collision", "Enable collisions with other objects.");
	
	prop= RNA_def_property(srna, "min_distance", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "epsilon");
	RNA_def_property_range(prop, 0.001f, 1.0f);
	RNA_def_property_ui_text(prop, "Minimum Distance", "Minimum distance between collision objects before collision response takes in, can be changed for each frame.");

	prop= RNA_def_property(srna, "friction", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.0f, 80.0f);
	RNA_def_property_ui_text(prop, "Friction", "Friction force if a collision happened (0=movement not changed, 100=no movement left)");

	prop= RNA_def_property(srna, "collision_quality", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "loop_count");
	RNA_def_property_range(prop, 1, 20);
	RNA_def_property_ui_text(prop, "Collision Quality", "How many collision iterations should be done. (higher is better quality but slower)");

	/* self collision */

	prop= RNA_def_property(srna, "enable_self_collision", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", CLOTH_COLLSETTINGS_FLAG_SELF);
	RNA_def_property_ui_text(prop, "Enable Self Collision", "Enable self collisions.");
	
	prop= RNA_def_property(srna, "self_min_distance", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "selfepsilon");
	RNA_def_property_range(prop, 0.5f, 1.0f);
	RNA_def_property_ui_text(prop, "Self Minimum Distance", "0.5 means no distance at all, 1.0 is maximum distance");
	
	prop= RNA_def_property(srna, "self_friction", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.0f, 80.0f);
	RNA_def_property_ui_text(prop, "Self Friction", "Friction/damping with self contact.");

	prop= RNA_def_property(srna, "self_collision_quality", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "self_loop_count");
	RNA_def_property_range(prop, 1, 10);
	RNA_def_property_ui_text(prop, "Self Collision Quality", "How many self collision iterations should be done. (higher is better quality but slower), can be changed for each frame.");
}

void RNA_def_cloth(BlenderRNA *brna)
{
	rna_def_cloth_sim_settings(brna);
	rna_def_cloth_collision_settings(brna);
}

#endif

