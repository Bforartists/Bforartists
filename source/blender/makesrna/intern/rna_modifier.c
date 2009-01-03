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
 * Contributor(s): Blender Foundation (2008), Juho Veps�l�inen
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <float.h>
#include <limits.h>
#include <stdlib.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "DNA_armature_types.h"
#include "DNA_modifier_types.h"
#include "DNA_scene_types.h"

#include "BKE_bmesh.h" /* For BevelModifierData */

#ifdef RNA_RUNTIME

static StructRNA* rna_Modifier_refine(struct PointerRNA *ptr)
{
	ModifierData *md= (ModifierData*)ptr->data;

	switch(md->type) {
		case eModifierType_Subsurf:
			return &RNA_SubsurfModifier;
		case eModifierType_Lattice:
			return &RNA_LatticeModifier;
		case eModifierType_Curve:
			return &RNA_CurveModifier;
		case eModifierType_Build:
			return &RNA_BuildModifier;
		case eModifierType_Mirror:
			return &RNA_MirrorModifier;
		case eModifierType_Decimate:
			return &RNA_DecimateModifier;
		case eModifierType_Wave:
			return &RNA_WaveModifier;
		case eModifierType_Armature:
			return &RNA_ArmatureModifier;
		case eModifierType_Hook:
			return &RNA_HookModifier;
		case eModifierType_Softbody:
			return &RNA_SoftbodyModifier;
		case eModifierType_Boolean:
			return &RNA_BooleanModifier;
		case eModifierType_Array:
			return &RNA_ArrayModifier;
		case eModifierType_EdgeSplit:
			return &RNA_EdgeSplitModifier;
		case eModifierType_Displace:
			return &RNA_DisplaceModifier;
		case eModifierType_UVProject:
			return &RNA_UVProjectModifier;
		case eModifierType_Smooth:
			return &RNA_SmoothModifier;
		case eModifierType_Cast:
			return &RNA_CastModifier;
		case eModifierType_MeshDeform:
			return &RNA_MeshDeformModifier;
		case eModifierType_ParticleSystem:
			return &RNA_ParticleSystemModifier;
		case eModifierType_ParticleInstance:
			return &RNA_ParticleInstanceModifier;
		case eModifierType_Explode:
			return &RNA_ExplodeModifier;
		case eModifierType_Cloth:
			return &RNA_ClothModifier;
		case eModifierType_Collision:
			return &RNA_CollisionModifier;
		case eModifierType_Bevel:
			return &RNA_BevelModifier;
		case eModifierType_Shrinkwrap:
			return &RNA_ShrinkwrapModifier;
		case eModifierType_Fluidsim:
			return &RNA_FluidSimulationModifier;
		case eModifierType_Mask:
			return &RNA_MaskModifier;
		case eModifierType_SimpleDeform:
			return &RNA_SimpleDeformModifier;
		default:
			return &RNA_Modifier;
	}
}

#else

static void rna_def_modifier_subsurf(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_subdivision_type_items[] = {
		{0, "CATMULL_CLARK", "Catmull-Clark", ""},
		{1, "SIMPLE", "Simple", ""},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "SubsurfModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Subsurf Modifier", "Subsurf Modifier.");
	RNA_def_struct_sdna(srna, "SubsurfModifierData");

	prop= RNA_def_property(srna, "subdivision_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "subdivType");
	RNA_def_property_enum_items(prop, prop_subdivision_type_items);
	RNA_def_property_ui_text(prop, "Subdivision Type", "Selects type of subdivision algorithm.");

	prop= RNA_def_property(srna, "levels", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 1, 20);
	RNA_def_property_ui_range(prop, 1, 6, 1, 0);
	RNA_def_property_ui_text(prop, "Levels", "Number of subdivisions to perform.");

	prop= RNA_def_property(srna, "render_levels", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "renderLevels");
	RNA_def_property_range(prop, 1, 20);
	RNA_def_property_ui_range(prop, 1, 6, 1, 0);
	RNA_def_property_ui_text(prop, "Render Levels", "Number of subdivisions to perform when rendering.");

	prop= RNA_def_property(srna, "optimal_draw", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", eSubsurfModifierFlag_ControlEdges);
	RNA_def_property_ui_text(prop, "Optimal Draw", "Skip drawing/rendering of interior subdivided edges");
	
	prop= RNA_def_property(srna, "subsurf_uv", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", eSubsurfModifierFlag_SubsurfUv);
	RNA_def_property_ui_text(prop, "Subsurf UV", "Use subsurf to subdivide UVs.");
}

static void rna_def_modifier_lattice(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "LatticeModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Lattice Modifier", "Lattice Modifier.");
	RNA_def_struct_sdna(srna, "LatticeModifierData");

	prop= RNA_def_property(srna, "lattice", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "object");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Lattice", "Lattice object to deform with.");

	prop= RNA_def_property(srna, "vertex_group", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "name");
	RNA_def_property_ui_text(prop, "Vertex Group", "Vertex group name.");
}

static void rna_def_modifier_curve(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_deform_axis_items[] = {
		{MOD_CURVE_POSX, "POS_X", "X", ""},
		{MOD_CURVE_POSY, "POS_Y", "Y", ""},
		{MOD_CURVE_POSZ, "POS_Z", "Z", ""},
		{MOD_CURVE_NEGX, "NEG_X", "-X", ""},
		{MOD_CURVE_NEGY, "NEG_Y", "-Y", ""},
		{MOD_CURVE_NEGZ, "NEG_Z", "-Z", ""},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "CurveModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Curve Modifier", "Curve Modifier.");
	RNA_def_struct_sdna(srna, "CurveModifierData");

	prop= RNA_def_property(srna, "curve", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "object");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Curve", "Curve object to deform with.");

	prop= RNA_def_property(srna, "vertex_group", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "name");
	RNA_def_property_ui_text(prop, "Vertex Group", "Vertex group name.");

	prop= RNA_def_property(srna, "deform_axis", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "defaxis");
	RNA_def_property_enum_items(prop, prop_deform_axis_items);
	RNA_def_property_ui_text(prop, "Deform Axis", "The axis that the curve deforms along.");
}

static void rna_def_modifier_build(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "BuildModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Build Modifier", "Build Modifier.");
	RNA_def_struct_sdna(srna, "BuildModifierData");

	prop= RNA_def_property(srna, "start", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 1, MAXFRAMEF);
	RNA_def_property_ui_text(prop, "Start", "Specify the start frame of the effect.");

	prop= RNA_def_property(srna, "length", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 1, MAXFRAMEF);
	RNA_def_property_ui_text(prop, "Length", "Specify the total time the build effect requires");

	prop= RNA_def_property(srna, "randomize", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_ui_text(prop, "Randomize", "Randomize the faces or edges during build.");

	prop= RNA_def_property(srna, "seed", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 1, MAXFRAMEF);
	RNA_def_property_ui_text(prop, "Seed", "Specify the seed for random if used.");
}

static void rna_def_modifier_mirror(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "MirrorModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Mirror Modifier", "Mirror Modifier.");
	RNA_def_struct_sdna(srna, "MirrorModifierData");

	prop= RNA_def_property(srna, "x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_MIR_AXIS_X);
	RNA_def_property_ui_text(prop, "X", "Enable X axis mirror.");

	prop= RNA_def_property(srna, "y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_MIR_AXIS_Y);
	RNA_def_property_ui_text(prop, "Y", "Enable Y axis mirror.");

	prop= RNA_def_property(srna, "z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_MIR_AXIS_Z);
	RNA_def_property_ui_text(prop, "Z", "Enable Z axis mirror.");

	prop= RNA_def_property(srna, "clip", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_MIR_CLIPPING);
	RNA_def_property_ui_text(prop, "clip", "Prevents vertices from going through the mirror during transform.");

	prop= RNA_def_property(srna, "mirror_vertex_groups", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_MIR_VGROUP);
	RNA_def_property_ui_text(prop, "Mirror Vertex Groups", "Mirror vertex groups (e.g. .R->.L).");

	prop= RNA_def_property(srna, "mirror_u", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_MIR_MIRROR_U);
	RNA_def_property_ui_text(prop, "Mirror U", "Mirror the U texture coordinate around the 0.5 point.");

	prop= RNA_def_property(srna, "mirror_v", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_MIR_MIRROR_V);
	RNA_def_property_ui_text(prop, "Mirror V", "Mirror the V texture coordinate around the 0.5 point.");

	prop= RNA_def_property(srna, "merge_limit", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "tolerance");
	RNA_def_property_range(prop, 0, FLT_MAX);
	RNA_def_property_ui_range(prop, 0, 1, 10, 3); 
	RNA_def_property_ui_text(prop, "Merge Limit", "Distance from axis within which mirrored vertices are merged.");

	prop= RNA_def_property(srna, "mirror_object", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "mirror_ob");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Mirror Object", "Object to use as mirror.");
}

static void rna_def_modifier_decimate(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "DecimateModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Decimate Modifier", "Decimate Modifier.");
	RNA_def_struct_sdna(srna, "DecimateModifierData");

	prop= RNA_def_property(srna, "ratio", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "percent");
	RNA_def_property_range(prop, 0, 1);
	RNA_def_property_ui_text(prop, "Ratio", "Defines the ratio of triangles to reduce to.");

	prop= RNA_def_property(srna, "face_count", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "faceCount");
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_ui_text(prop, "Face Count", "The current number of faces in the decimated mesh.");
}

static void rna_def_modifier_wave(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_texture_coordinates_items[] = {
		{MOD_WAV_MAP_LOCAL, "MAP_LOCAL", "Local", ""},
		{MOD_WAV_MAP_GLOBAL, "MAP_GLOBAL", "Global", ""},
		{MOD_WAV_MAP_OBJECT, "MAP_OBJECT", "Object", ""},
		{MOD_WAV_MAP_UV, "MAP_UV", "UV", ""},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "WaveModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Wave Modifier", "Wave Modifier.");
	RNA_def_struct_sdna(srna, "WaveModifierData");

	prop= RNA_def_property(srna, "x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_WAVE_X);
	RNA_def_property_ui_text(prop, "X", "X axis motion.");

	prop= RNA_def_property(srna, "y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_WAVE_Y);
	RNA_def_property_ui_text(prop, "Y", "Y axis motion.");

	prop= RNA_def_property(srna, "cyclic", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_WAVE_CYCL);
	RNA_def_property_ui_text(prop, "Cyclic", "Cyclic wave effect.");

	prop= RNA_def_property(srna, "normals", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_WAVE_NORM);
	RNA_def_property_ui_text(prop, "Normals", "Dispace along normals.");

	prop= RNA_def_property(srna, "x_normal", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_WAVE_NORM_X);
	RNA_def_property_ui_text(prop, "X Normal", "Enable displacement along the X normal");

	prop= RNA_def_property(srna, "y_normal", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_WAVE_NORM_Y);
	RNA_def_property_ui_text(prop, "Y Normal", "Enable displacement along the Y normal");

	prop= RNA_def_property(srna, "z_normal", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_WAVE_NORM_Z);
	RNA_def_property_ui_text(prop, "Z Normal", "Enable displacement along the Z normal");

	prop= RNA_def_property(srna, "time_offset", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "timeoffs");
	RNA_def_property_range(prop, -MAXFRAMEF, MAXFRAMEF);
	RNA_def_property_ui_text(prop, "Time Offset", "Either the starting frame (for positive speed) or ending frame (for negative speed.)");

	prop= RNA_def_property(srna, "lifetime", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, -MAXFRAMEF, MAXFRAMEF);
	RNA_def_property_ui_text(prop, "Lifetime",  "");

	prop= RNA_def_property(srna, "damping_time", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "damp");
	RNA_def_property_range(prop, -MAXFRAMEF, MAXFRAMEF);
	RNA_def_property_ui_text(prop, "Damping Time",  "");

	prop= RNA_def_property(srna, "falloff_radius", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "falloff");
	RNA_def_property_range(prop, 0, FLT_MAX);
	RNA_def_property_ui_range(prop, 0, 100, 100, 2);
	RNA_def_property_ui_text(prop, "Falloff Radius",  "");

	prop= RNA_def_property(srna, "start_position_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "startx");
	RNA_def_property_range(prop, FLT_MIN, FLT_MAX);
	RNA_def_property_ui_range(prop, -100, 100, 100, 2);
	RNA_def_property_ui_text(prop, "Start Position X",  "");

	prop= RNA_def_property(srna, "start_position_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "starty");
	RNA_def_property_range(prop, FLT_MIN, FLT_MAX);
	RNA_def_property_ui_range(prop, -100, 100, 100, 2);
	RNA_def_property_ui_text(prop, "Start Position Y",  "");

	prop= RNA_def_property(srna, "start_position_object", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "objectcenter");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Start Position Object", "");

	prop= RNA_def_property(srna, "vertex_group", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "defgrp_name");
	RNA_def_property_ui_text(prop, "Vertex Group", "Vertex group name for modulating the wave.");

	prop= RNA_def_property(srna, "texture", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Texture", "Texture for modulating the wave.");

	prop= RNA_def_property(srna, "texture_coordinates", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "texmapping");
	RNA_def_property_enum_items(prop, prop_texture_coordinates_items);
	RNA_def_property_ui_text(prop, "Texture Coordinates", "Texture coordinates used for modulating input.");

	/* XXX: Not sure how to handle WaveModifierData.uvlayer_tmp. It should be a menu of this object's UV customdata layers. */

	prop= RNA_def_property(srna, "texture_coordinates_object", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "map_object");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Texture Coordinates Object", "");

	prop= RNA_def_property(srna, "speed", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, FLT_MIN, FLT_MAX);
	RNA_def_property_ui_range(prop, -2, 2, 10, 2);
	RNA_def_property_ui_text(prop, "Speed", "");

	prop= RNA_def_property(srna, "height", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, FLT_MIN, FLT_MAX);
	RNA_def_property_ui_range(prop, -2, 2, 10, 2);
	RNA_def_property_ui_text(prop, "Height", "");

	prop= RNA_def_property(srna, "width", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0, FLT_MAX);
	RNA_def_property_ui_range(prop, 0, 5, 10, 2);
	RNA_def_property_ui_text(prop, "Width", "");

	prop= RNA_def_property(srna, "narrowness", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "narrow");
	RNA_def_property_range(prop, 0, FLT_MAX);
	RNA_def_property_ui_range(prop, 0, 10, 10, 2);
	RNA_def_property_ui_text(prop, "Narrowness", "");
}

static void rna_def_modifier_armature(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "ArmatureModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Armature Modifier", "Armature Modifier.");
	RNA_def_struct_sdna(srna, "ArmatureModifierData");

	prop= RNA_def_property(srna, "armature", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "object");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Armature", "Armature object to deform with.");

	prop= RNA_def_property(srna, "vertex_group", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "defgrp_name");
	RNA_def_property_ui_text(prop, "Vertex Group", "Vertex group name.");

	prop= RNA_def_property(srna, "invert", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "deformflag", ARM_DEF_INVERT_VGROUP);
	RNA_def_property_ui_text(prop, "Invert", "Invert vertex group influence.");

	prop= RNA_def_property(srna, "use_vertex_groups", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "deformflag", ARM_DEF_VGROUP);
	RNA_def_property_ui_text(prop, "Use Vertex Groups", "");

	prop= RNA_def_property(srna, "use_bone_envelopes", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "deformflag", ARM_DEF_ENVELOPE);
	RNA_def_property_ui_text(prop, "Use Bone Envelopes", "");

	prop= RNA_def_property(srna, "quaternion", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "deformflag", ARM_DEF_QUATERNION);
	RNA_def_property_ui_text(prop, "Quaternion", "Deform rotation interpolation with quaternions.");

	prop= RNA_def_property(srna, "b_bone_rest", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "deformflag", ARM_DEF_B_BONE_REST);
	RNA_def_property_ui_text(prop, "Quaternion",  "Make B-Bones deform already in rest position");
}

static void rna_def_modifier_hook(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "HookModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Hook Modifier", "Hook Modifier.");
	RNA_def_struct_sdna(srna, "HookModifierData");

	prop= RNA_def_property(srna, "falloff", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0, FLT_MAX);
	RNA_def_property_ui_range(prop, 0, 100, 100, 2);
	RNA_def_property_ui_text(prop, "Falloff",  "If not zero, the distance from the hook where influence ends.");

	prop= RNA_def_property(srna, "force", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0, 1);
	RNA_def_property_ui_text(prop, "Force",  "Relative force of the hook.");

	prop= RNA_def_property(srna, "object", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Object", "Parent Object for hook, also recalculates and clears offset");

	prop= RNA_def_property(srna, "vertex_group", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "name");
	RNA_def_property_ui_text(prop, "Vertex Group", "Vertex group name.");
}

static void rna_def_modifier_softbody(BlenderRNA *brna)
{
	StructRNA *srna;

	srna= RNA_def_struct(brna, "SoftbodyModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Softbody Modifier", "Softbody Modifier.");
	RNA_def_struct_sdna(srna, "SoftbodyModifierData");
}

static void rna_def_modifier_boolean(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_operation_items[] = {
		{eBooleanModifierOp_Intersect, "OPERATION_INTERSECT", "Intersect", ""},
		{eBooleanModifierOp_Union, "OPERATION_UNION", "Union", ""},
		{eBooleanModifierOp_Difference, "OPERATION_DIFFERENCE", "Difference", ""},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "BooleanModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Boolean Modifier", "Boolean Modifier.");
	RNA_def_struct_sdna(srna, "BooleanModifierData");

	prop= RNA_def_property(srna, "object", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Object", "Mesh object to use for boolean operation.");

	prop= RNA_def_property(srna, "operation", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, prop_operation_items);
	RNA_def_property_ui_text(prop, "Operation", "");
}

static void rna_def_modifier_array(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_fit_type_items[] = {
		{MOD_ARR_FIXEDCOUNT, "FIXED_COUNT", "Fixed Count", ""},
		{MOD_ARR_FITLENGTH, "FIT_LENGTH", "Fit Length", ""},
		{MOD_ARR_FITCURVE, "FIT_CURVE", "Fit Curve", ""},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "ArrayModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Array Modifier", "Array Modifier.");
	RNA_def_struct_sdna(srna, "ArrayModifierData");

	/* Length parameters */
	prop= RNA_def_property(srna, "fit_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, prop_fit_type_items);
	RNA_def_property_ui_text(prop, "Fit Type", "Array length calculation method.");

	prop= RNA_def_property(srna, "count", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 1, INT_MAX);
	RNA_def_property_ui_range(prop, 1, 1000, 1, 0);
	RNA_def_property_ui_text(prop, "Count",  "Number of duplicates to make.");

	prop= RNA_def_property(srna, "length", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0, INT_MAX);
	RNA_def_property_ui_range(prop, 0, 10000, 10, 2);
	RNA_def_property_ui_text(prop, "Length", "Length to fit array within.");

	prop= RNA_def_property(srna, "curve", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "curve_ob");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Curve", "Curve object to fit array length to.");

	/* Offset parameters */
	prop= RNA_def_property(srna, "constant_offset", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "offset_type", MOD_ARR_OFF_CONST);
	RNA_def_property_ui_text(prop, "Constant Offset", "");
	
	prop= RNA_def_property(srna, "constant_offset_displacement", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_float_sdna(prop, NULL, "offset");
	RNA_def_property_ui_text(prop, "Constant Offset Displacement", "");

	prop= RNA_def_property(srna, "relative_offset", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "offset_type", MOD_ARR_OFF_RELATIVE);
	RNA_def_property_ui_text(prop, "Relative Offset", "");

	prop= RNA_def_property(srna, "relative_offset_displacement", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_float_sdna(prop, NULL, "scale");
	RNA_def_property_ui_text(prop, "Relative Offset Displacement", "");

	/* Vertex merging parameters */
	prop= RNA_def_property(srna, "merge_adjacent_vertices", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", MOD_ARR_MERGE);
	RNA_def_property_ui_text(prop, "Merge Vertices", "Merge vertices in adjacent duplicates.");

	prop= RNA_def_property(srna, "merge_end_vertices", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", MOD_ARR_MERGEFINAL);
	RNA_def_property_ui_text(prop, "Merge Vertices", "Merge vertices in first and last duplicates.");

	prop= RNA_def_property(srna, "merge_distance", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "merge_dist");
	RNA_def_property_range(prop, 0, FLT_MAX);
	RNA_def_property_ui_range(prop, 0, 1, 1, 4);
	RNA_def_property_ui_text(prop, "Merge Distance", "Limit below which to merge vertices.");

	/* Offset object */
	prop= RNA_def_property(srna, "add_offset_object", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "offset_type", MOD_ARR_OFF_OBJ);
	RNA_def_property_ui_text(prop, "Add Offset Object", "Add an object transformation to the total offset.");

	prop= RNA_def_property(srna, "offset_object", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "offset_ob");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Offset Object", "");
	
	/* Caps */
	prop= RNA_def_property(srna, "start_cap", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Start Cap", "Mesh object to use as a start cap.");

	prop= RNA_def_property(srna, "end_cap", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "End Cap", "Mesh object to use as an end cap.");
}

static void rna_def_modifier_edgesplit(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "EdgeSplitModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "EdgeSplit Modifier", "EdgeSplit Modifier.");
	RNA_def_struct_sdna(srna, "EdgeSplitModifierData");

	prop= RNA_def_property(srna, "split_angle", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0, 180);
	RNA_def_property_ui_range(prop, 0, 180, 100, 2);
	RNA_def_property_ui_text(prop, "Split Angle", "Angle above which to split edges.");

	prop= RNA_def_property(srna, "use_edge_angle", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", MOD_EDGESPLIT_FROMANGLE);
	RNA_def_property_ui_text(prop, "Use Edge Angle", "Split edges with high angle between faces.");

	prop= RNA_def_property(srna, "use_sharp", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", MOD_EDGESPLIT_FROMFLAG);
	RNA_def_property_ui_text(prop, "Use Sharp Edges", "Split edges that are marked as sharp.");
}

static void rna_def_modifier_displace(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_direction_items[] = {
		{MOD_DISP_DIR_X, "DIR_X", "X", ""},
		{MOD_DISP_DIR_Y, "DIR_Y", "Y", ""},
		{MOD_DISP_DIR_Z, "DIR_Z", "Z", ""},
		{MOD_DISP_DIR_NOR, "DIR_NORMAL", "Normal", ""},
		/* XXX: Correct name? */
		{MOD_DISP_DIR_RGB_XYZ, "DIR_RGB_TO_XYZ", "RGB To XYZ", ""},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem prop_texture_coordinates_items[] = {
		{MOD_DISP_MAP_LOCAL, "MAP_LOCAL", "Map", ""},
		{MOD_DISP_MAP_GLOBAL, "MAP_GLOBAL", "Global", ""},
		{MOD_DISP_MAP_OBJECT, "MAP_OBJECT", "Object", ""},
		{MOD_DISP_MAP_UV, "MAP_UV", "UV", ""},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "DisplaceModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Displace Modifier", "Displace Modifier.");
	RNA_def_struct_sdna(srna, "DisplaceModifierData");

	prop= RNA_def_property(srna, "vertex_group", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "defgrp_name");
	RNA_def_property_ui_text(prop, "Vertex Group", "Vertex group name.");

	/* XXX: no texture type in RNA yet */
	prop= RNA_def_property(srna, "texture", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "ID");
	RNA_def_property_ui_text(prop, "Texture", "");

	prop= RNA_def_property(srna, "midlevel", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0, 1);
	RNA_def_property_ui_range(prop, 0, 1, 10, 3);
	RNA_def_property_ui_text(prop, "Midlevel", "Material value that gives no displacement.");

	prop= RNA_def_property(srna, "strength", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, FLT_MIN, FLT_MAX);
	RNA_def_property_ui_range(prop, -100, 100, 10, 2);
	RNA_def_property_ui_text(prop, "Strength", "");

	prop= RNA_def_property(srna, "direction", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, prop_direction_items);
	RNA_def_property_ui_text(prop, "Direction", "");

	prop= RNA_def_property(srna, "texture_coordinates", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "texmapping");
	RNA_def_property_enum_items(prop, prop_texture_coordinates_items);
	RNA_def_property_ui_text(prop, "Texture Coordinates", "");

	/* XXX: not sure how to handle uvlayer_tmp (for setting the UV layer if UV mapping is used.) */

	prop= RNA_def_property(srna, "texture_coordinate_object", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "map_object");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Texture Coordinate Object", "");
}

static void rna_def_modifier_uvproject(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "UVProjectModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "UVProject Modifier", "UVProject Modifier.");
	RNA_def_struct_sdna(srna, "UVProjectModifierData");

	/* XXX: not sure how to handle uvlayer_tmp */

	/* XXX: and how to do UVProjectModifier.projectors, a statically-sized array of Object pointers?
	        (this code crashes when it's expanded in the RNA viewer...) */
	/*prop= RNA_def_property(srna, "projectors", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "projectors", "num_projectors");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Projectors", "");*/

	prop= RNA_def_property(srna, "image", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "Image");
	RNA_def_property_ui_text(prop, "Image", "");

	prop= RNA_def_property(srna, "horizontal_aspect_ratio", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "aspectx");
	RNA_def_property_range(prop, 1, FLT_MAX);
	RNA_def_property_ui_range(prop, 1, 1000, 100, 2);
	RNA_def_property_ui_text(prop, "Horizontal Aspect Ratio", "");

	prop= RNA_def_property(srna, "vertical_aspect_ratio", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "aspecty");
	RNA_def_property_range(prop, 1, FLT_MAX);
	RNA_def_property_ui_range(prop, 1, 1000, 100, 2);
	RNA_def_property_ui_text(prop, "Vertical Aspect Ratio", "");

	prop= RNA_def_property(srna, "override_image", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", MOD_UVPROJECT_OVERRIDEIMAGE);
	RNA_def_property_ui_text(prop, "Override Image", "Override faces' current images with the given image.");
}

static void rna_def_modifier_smooth(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "SmoothModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Smooth Modifier", "Smooth Modifier.");
	RNA_def_struct_sdna(srna, "SmoothModifierData");

	prop= RNA_def_property(srna, "x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_SMOOTH_X);
	RNA_def_property_ui_text(prop, "X", "");

	prop= RNA_def_property(srna, "y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_SMOOTH_Y);
	RNA_def_property_ui_text(prop, "Y", "");

	prop= RNA_def_property(srna, "z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_SMOOTH_Z);
	RNA_def_property_ui_text(prop, "Z", "");

	prop= RNA_def_property(srna, "factor", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "fac");
	RNA_def_property_range(prop, FLT_MIN, FLT_MAX);
	RNA_def_property_ui_range(prop, -10, 10, 0.5, 2);
	RNA_def_property_ui_text(prop, "Factor", "");

	prop= RNA_def_property(srna, "repeat", PROP_INT, PROP_NONE);
	RNA_def_property_ui_range(prop, 0, 30, 1, 0);
	RNA_def_property_ui_text(prop, "Repeat", "");
	
	prop= RNA_def_property(srna, "vertex_group", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "defgrp_name");
	RNA_def_property_ui_text(prop, "Vertex Group", "Vertex group name.");
}

static void rna_def_modifier_cast(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_cast_type_items[] = {
		{MOD_CAST_TYPE_SPHERE, "TYPE_SPHERE", "Sphere", ""},
		{MOD_CAST_TYPE_CYLINDER, "TYPE_CYLINDER", "Cylinder", ""},
		{MOD_CAST_TYPE_CUBOID, "TYPE_CUBOID", "Cuboid", ""},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "CastModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Cast Modifier", "Cast Modifier.");
	RNA_def_struct_sdna(srna, "CastModifierData");

	prop= RNA_def_property(srna, "cast_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "type");
	RNA_def_property_enum_items(prop, prop_cast_type_items);
	RNA_def_property_ui_text(prop, "Cast Type", "");

	prop= RNA_def_property(srna, "x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_CAST_X);
	RNA_def_property_ui_text(prop, "X", "");

	prop= RNA_def_property(srna, "y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_CAST_Y);
	RNA_def_property_ui_text(prop, "Y", "");

	prop= RNA_def_property(srna, "z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_CAST_Z);
	RNA_def_property_ui_text(prop, "Z", "");
	
	prop= RNA_def_property(srna, "factor", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "fac");
	RNA_def_property_range(prop, FLT_MIN, FLT_MAX);
	RNA_def_property_ui_range(prop, -10, 10, 5, 2);
	RNA_def_property_ui_text(prop, "Factor", "");

	prop= RNA_def_property(srna, "radius", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0, FLT_MAX);
	RNA_def_property_ui_range(prop, 0, 100, 10, 2);
	RNA_def_property_ui_text(prop, "Radius", "Only deform vertices within this distance from the center of the effect (leave as 0 for infinite.)");

	prop= RNA_def_property(srna, "size", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0, FLT_MAX);
	RNA_def_property_ui_range(prop, 0, 100, 10, 2);
	RNA_def_property_ui_text(prop, "Size", "Size of projection shape (leave as 0 for auto.)");

	prop= RNA_def_property(srna, "vertex_group", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "defgrp_name");
	RNA_def_property_ui_text(prop, "Vertex Group", "Vertex group name.");
}

static void rna_def_modifier_meshdeform(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "MeshDeformModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "MeshDeform Modifier", "MeshDeform Modifier.");
	RNA_def_struct_sdna(srna, "MeshDeformModifierData");

	prop= RNA_def_property(srna, "mesh", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "object");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Mesh", "");

	prop= RNA_def_property(srna, "invert", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_MDEF_INVERT_VGROUP);
	RNA_def_property_ui_text(prop, "Invert", "Invert vertex group influence.");

	prop= RNA_def_property(srna, "vertex_group", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "defgrp_name");
	RNA_def_property_ui_text(prop, "Vertex Group", "Vertex group name.");

	prop= RNA_def_property(srna, "precision", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "gridsize");
	RNA_def_property_range(prop, 2, 10);
	RNA_def_property_ui_text(prop, "Precision", "The grid size for binding.");

	prop= RNA_def_property(srna, "dynamic", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_MDEF_INVERT_VGROUP);
	RNA_def_property_ui_text(prop, "Dynamic", "Recompute binding dynamically on top of other deformers (slower and more memory consuming.)");

}

static void rna_def_modifier_particlesystem(BlenderRNA *brna)
{
	StructRNA *srna;

	srna= RNA_def_struct(brna, "ParticleSystemModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "ParticleSystem Modifier", "ParticleSystem Modifier.");
	RNA_def_struct_sdna(srna, "ParticleSystemModifierData");
}

static void rna_def_modifier_particleinstance(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "ParticleInstanceModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "ParticleInstance Modifier", "ParticleInstance Modifier.");
	RNA_def_struct_sdna(srna, "ParticleInstanceModifierData");

	prop= RNA_def_property(srna, "object", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "ob");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Object", "Object that has the particle system.");

	prop= RNA_def_property(srna, "particle_system_number", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "psys");
	RNA_def_property_range(prop, 1, 10);
	RNA_def_property_ui_text(prop, "Particle System Number", "");
	
	prop= RNA_def_property(srna, "normal", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", eParticleInstanceFlag_Parents);
	RNA_def_property_ui_text(prop, "Normal", "Create instances from normal particles.");

	prop= RNA_def_property(srna, "children", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", eParticleInstanceFlag_Children);
	RNA_def_property_ui_text(prop, "Children", "Create instances from child particles.");

	prop= RNA_def_property(srna, "path", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", eParticleInstanceFlag_Path);
	RNA_def_property_ui_text(prop, "Path", "Create instances along particle paths.");

	prop= RNA_def_property(srna, "unborn", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", eParticleInstanceFlag_Unborn);
	RNA_def_property_ui_text(prop, "Unborn", "Show instances when particles are unborn.");

	prop= RNA_def_property(srna, "alive", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", eParticleInstanceFlag_Alive);
	RNA_def_property_ui_text(prop, "Alive", "Show instances when particles are alive.");

	prop= RNA_def_property(srna, "dead", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", eParticleInstanceFlag_Dead);
	RNA_def_property_ui_text(prop, "Dead", "Show instances when particles are dead.");
}

static void rna_def_modifier_explode(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "ExplodeModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Explode Modifier", "Explode Modifier.");
	RNA_def_struct_sdna(srna, "ExplodeModifierData");

	/* XXX: vgroup */

	prop= RNA_def_property(srna, "protect", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0, 1);
	RNA_def_property_ui_text(prop, "Protect", "Clean vertex group edges");

	prop= RNA_def_property(srna, "split_edges", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", eExplodeFlag_EdgeSplit);
	RNA_def_property_ui_text(prop, "Split Edges", "Split face edges for nicer shrapnel.");

	prop= RNA_def_property(srna, "unborn", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", eExplodeFlag_Unborn);
	RNA_def_property_ui_text(prop, "Unborn", "Show mesh when particles are unborn.");

	prop= RNA_def_property(srna, "alive", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", eExplodeFlag_Alive);
	RNA_def_property_ui_text(prop, "alive", "Show mesh when particles are alive.");

	prop= RNA_def_property(srna, "dead", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", eExplodeFlag_Dead);
	RNA_def_property_ui_text(prop, "dead", "Show mesh when particles are dead.");
}

static void rna_def_modifier_cloth(BlenderRNA *brna)
{
	StructRNA *srna;

	srna= RNA_def_struct(brna, "ClothModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Cloth Modifier", "Cloth Modifier.");
	RNA_def_struct_sdna(srna, "ClothModifierData");
}

static void rna_def_modifier_collision(BlenderRNA *brna)
{
	StructRNA *srna;

	srna= RNA_def_struct(brna, "CollisionModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Collision Modifier", "Collision Modifier.");
	RNA_def_struct_sdna(srna, "CollisionModifierData");
}

static void rna_def_modifier_bevel(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_limit_method_items[] = {
		{0, "NONE", "None", "Bevel the entire mesh by a constant amount."},
		{BME_BEVEL_ANGLE, "ANGLE", "Angle", "Only bevel edges with sharp enough angles between faces."},
		{BME_BEVEL_WEIGHT, "WEIGHT", "Weight", "Use bevel weights to determine how much bevel is applied; apply them separately in vert/edge select mode."},
		{0, NULL, NULL, NULL}};

	static EnumPropertyItem prop_edge_weight_method_items[] = {
		{0, "AVERAGE", "Average", ""},
		{BME_BEVEL_EMIN, "SHARPEST", "Sharpest", ""},
		{BME_BEVEL_EMAX, "LARGEST", "Largest", ""},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "BevelModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Bevel Modifier", "Bevel Modifier.");
	RNA_def_struct_sdna(srna, "BevelModifierData");

	prop= RNA_def_property(srna, "width", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "value");
	RNA_def_property_range(prop, 0, 0.5);
	RNA_def_property_ui_text(prop, "Width", "Bevel value/amount.");

	prop= RNA_def_property(srna, "only_vertices", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", BME_BEVEL_VERT);
	RNA_def_property_ui_text(prop, "Only Vertices", "Bevel verts/corners, not edges.");

	prop= RNA_def_property(srna, "limit_method", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "lim_flags");
	RNA_def_property_enum_items(prop, prop_limit_method_items);
	RNA_def_property_ui_text(prop, "Limit Method", "");

	prop= RNA_def_property(srna, "edge_weight_method", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "e_flags");
	RNA_def_property_enum_items(prop, prop_edge_weight_method_items);
	RNA_def_property_ui_text(prop, "Edge Weight Method", "What edge weight to use for weighting a vertex.");

	prop= RNA_def_property(srna, "angle", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "bevel_angle");
	RNA_def_property_range(prop, 0, 180);
	RNA_def_property_ui_range(prop, 0, 180, 100, 2);
	RNA_def_property_ui_text(prop, "Angle", "Angle above which to bevel edges.");
}

static void rna_def_modifier_shrinkwrap(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_mode_items[] = {
		{MOD_SHRINKWRAP_NEAREST_SURFACE, "NEAREST_SURFACEPOINT", "Nearest Surface Point", ""},
		{MOD_SHRINKWRAP_PROJECT, "PROJECT", "Project", ""},
		{MOD_SHRINKWRAP_NEAREST_VERTEX, "NEAREST_VERTEX", "Nearest Vertex", ""},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "ShrinkwrapModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Shrinkwrap Modifier", "Shrinkwrap Modifier.");
	RNA_def_struct_sdna(srna, "ShrinkwrapModifierData");

	prop= RNA_def_property(srna, "mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "shrinkType");
	RNA_def_property_enum_items(prop, prop_mode_items);
	RNA_def_property_ui_text(prop, "Mode", "");

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Target", "Mesh target to shrink to.");

	prop= RNA_def_property(srna, "auxiliary_target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "auxTarget");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Auxiliary Target", "Additional mesh target to shrink to.");

	prop= RNA_def_property(srna, "vertex_group", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "vgroup_name");
	RNA_def_property_ui_text(prop, "Vertex Group", "Vertex group name.");
	
	prop= RNA_def_property(srna, "offset", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "keepDist");
	RNA_def_property_range(prop, 0, FLT_MAX);
	RNA_def_property_ui_range(prop, 0, 100, 1, 2);
	RNA_def_property_ui_text(prop, "Offset", "Distance to keep from the target.");

	/* XXX: need to do projaxis */
	
	prop= RNA_def_property(srna, "subsurf_levels", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "subsurfLevels");
	RNA_def_property_range(prop, 0, 20);
	RNA_def_property_ui_range(prop, 0, 6, 1, 0);
	RNA_def_property_ui_text(prop, "Subsurf Levels", "Number of subdivisions that must be performed before extracting vertices' positions and normals.");

	prop= RNA_def_property(srna, "negative", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "shrinkOpts", MOD_SHRINKWRAP_PROJECT_ALLOW_NEG_DIR);
	RNA_def_property_ui_text(prop, "Negative", "Allow vertices to move in the negative direction of axis.");

	prop= RNA_def_property(srna, "positive", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "shrinkOpts", MOD_SHRINKWRAP_PROJECT_ALLOW_POS_DIR);
	RNA_def_property_ui_text(prop, "Positive", "Allow vertices to move in the positive direction of axis.");

	prop= RNA_def_property(srna, "cull_front_faces", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "shrinkOpts", MOD_SHRINKWRAP_CULL_TARGET_FRONTFACE);
	RNA_def_property_ui_text(prop, "Cull Front Faces", "Stop vertices from projecting to a front face on the target.");

	prop= RNA_def_property(srna, "cull_back_faces", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "shrinkOpts", MOD_SHRINKWRAP_CULL_TARGET_BACKFACE);
	RNA_def_property_ui_text(prop, "Cull Back Faces", "Stop vertices from projecting to a back face on the target.");

	prop= RNA_def_property(srna, "keep_above_surface", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "shrinkOpts", MOD_SHRINKWRAP_KEEP_ABOVE_SURFACE);
	RNA_def_property_ui_text(prop, "Keep Above Surface", "");
}

static void rna_def_modifier_fluidsim(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "FluidSimulationModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Fluid Simulation Modifier", "Fluid Simulation Modifier.");
	RNA_def_struct_sdna(srna, "FluidsimModifierData");

	prop= RNA_def_property(srna, "settings", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "fss");
	RNA_def_property_struct_type(prop, "FluidSettings");
	RNA_def_property_ui_text(prop, "Settings", "Settings for how this object is used in the fluid simulation.");
}

static void rna_def_modifier_mask(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_mode_items[] = {
		{MOD_MASK_MODE_VGROUP, "MODE_VERTEXGROUP", "Vertex Group", ""},
		{MOD_MASK_MODE_ARM, "MODE_ARMATURE", "Armature", ""},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "MaskModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "Mask Modifier", "Mask Modifier.");
	RNA_def_struct_sdna(srna, "MaskModifierData");

	prop= RNA_def_property(srna, "mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, prop_mode_items);
	RNA_def_property_ui_text(prop, "Mode", "");

	prop= RNA_def_property(srna, "armature", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "ob_arm");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Armature", "Armature to use as source of bones to mask.");

	prop= RNA_def_property(srna, "vertex_group", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "vgroup");
	RNA_def_property_ui_text(prop, "Vertex Group", "Vertex group name.");

	prop= RNA_def_property(srna, "inverse", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MOD_MASK_INV);
	RNA_def_property_ui_text(prop, "Inverse", "Use vertices that are not part of region defined.");
}

static void rna_def_modifier_simpledeform(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem prop_mode_items[] = {
		{MOD_SIMPLEDEFORM_MODE_TWIST, "MODE_TWIST", "Twist", ""},
		{MOD_SIMPLEDEFORM_MODE_BEND, "MODE_BEND", "Bend", ""},
		{MOD_SIMPLEDEFORM_MODE_TAPER, "MODE_TAPER", "Taper", ""},
		{MOD_SIMPLEDEFORM_MODE_STRETCH, "MODE_STRETCH", "Stretch", ""},
		{0, NULL, NULL, NULL}};

	srna= RNA_def_struct(brna, "SimpleDeformModifier", "Modifier");
	RNA_def_struct_ui_text(srna, "SimpleDeform Modifier", "SimpleDeform Modifier.");
	RNA_def_struct_sdna(srna, "SimpleDeformModifierData");

	prop= RNA_def_property(srna, "mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, prop_mode_items);
	RNA_def_property_ui_text(prop, "Mode", "");

	prop= RNA_def_property(srna, "vertex_group", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "vgroup_name");
	RNA_def_property_ui_text(prop, "Vertex Group", "Vertex group name.");

	prop= RNA_def_property(srna, "Origin", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "origin");
	RNA_def_property_struct_type(prop, "Object");
	RNA_def_property_ui_text(prop, "Origin", "Origin of modifier space coordinates.");

	prop= RNA_def_property(srna, "relative", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "originOpts", MOD_SIMPLEDEFORM_ORIGIN_LOCAL);
	RNA_def_property_ui_text(prop, "Relative", "Sets the origin of deform space to be relative to the object.");

	prop= RNA_def_property(srna, "factor", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, FLT_MIN, FLT_MAX);
	RNA_def_property_ui_range(prop, -10, 10, 0.5, 2);
	RNA_def_property_ui_text(prop, "Factor", "");

	prop= RNA_def_property(srna, "limits", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "limit");
	RNA_def_property_array(prop, 2);
	RNA_def_property_range(prop, 0, 1);
	RNA_def_property_ui_range(prop, 0, 1, 5, 2);
	RNA_def_property_ui_text(prop, "Limits", "Lower/Upper limits for deform.");

	prop= RNA_def_property(srna, "lock_x_axis", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "axis", MOD_SIMPLEDEFORM_LOCK_AXIS_X);
	RNA_def_property_ui_text(prop, "Lock X Axis", "");

	prop= RNA_def_property(srna, "lock_y_axis", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "axis", MOD_SIMPLEDEFORM_LOCK_AXIS_Y);
	RNA_def_property_ui_text(prop, "Lock Y Axis", "");
}

void RNA_def_modifier(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	static EnumPropertyItem type_items[] ={
		{eModifierType_Subsurf, "SUBSURF", "Subsurf", ""},
		{eModifierType_Lattice, "LATTICE", "Lattice", ""},
		{eModifierType_Curve, "CURVE", "Curve", ""},
		{eModifierType_Build, "BUILD", "Build", ""},
		{eModifierType_Mirror, "MIRROR", "Mirror", ""},
		{eModifierType_Decimate, "DECIMATE", "Decimate", ""},
		{eModifierType_Wave, "WAVE", "Wave", ""},
		{eModifierType_Armature, "ARMATURE", "Armature", ""},
		{eModifierType_Hook, "HOOK", "Hook", ""},
		{eModifierType_Softbody, "SOFTBODY", "Softbody", ""},
		{eModifierType_Boolean, "BOOLEAN", "Boolean", ""},
		{eModifierType_Array, "ARRAY", "Array", ""},
		{eModifierType_EdgeSplit, "EDGE_SPLIT", "Edge Split", ""},
		{eModifierType_Displace, "DISPLACE", "Displace", ""},
		{eModifierType_UVProject, "UV_PROJECT", "UV Project", ""},
		{eModifierType_Smooth, "SMOOTH", "Smooth", ""},
		{eModifierType_Cast, "CAST", "Cast", ""},
		{eModifierType_MeshDeform, "MESH_DEFORM", "Mesh Deform", ""},
		{eModifierType_ParticleSystem, "PARTICLE_SYSTEM", "Particle System", ""},
		{eModifierType_ParticleInstance, "PARTICLE_INSTANCE", "Particle Instance", ""},
		{eModifierType_Explode, "EXPLODE", "Explode", ""},
		{eModifierType_Cloth, "CLOTH", "Cloth", ""},
		{eModifierType_Collision, "COLLISION", "Collision", ""},
		{eModifierType_Bevel, "BEVEL", "Bevel", ""},
		{eModifierType_Shrinkwrap, "SHRINKWRAP", "Shrinkwrap", ""},
		{eModifierType_Fluidsim, "FLUID_SIMULATION", "Fluid Simulation", ""},
		{eModifierType_Mask, "MASK", "Mask", ""},
		{eModifierType_SimpleDeform, "SIMPLE_DEFORM", "Simple Deform", ""},
		{0, NULL, NULL, NULL}};
	
	/* data */
	srna= RNA_def_struct(brna, "Modifier", NULL);
	RNA_def_struct_ui_text(srna , "Object Modifier", "DOC_BROKEN");
	RNA_def_struct_refine_func(srna, "rna_Modifier_refine");
	RNA_def_struct_sdna(srna, "ModifierData");
	
	/* strings */
	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_ui_text(prop, "Name", "Modifier name.");
	RNA_def_struct_name_property(srna, prop);
	
	/* enums */
	prop= RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_enum_sdna(prop, NULL, "type");
	RNA_def_property_enum_items(prop, type_items);
	RNA_def_property_ui_text(prop, "Type", "");
	
	/* flags */
	prop= RNA_def_property(srna, "realtime", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", eModifierMode_Realtime);
	RNA_def_property_ui_text(prop, "Realtime", "Realtime display of a modifier.");
	
	prop= RNA_def_property(srna, "render", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", eModifierMode_Render);
	RNA_def_property_ui_text(prop, "Render", "Use modifier during rendering.");
	
	prop= RNA_def_property(srna, "editmode", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", eModifierMode_Editmode);
	RNA_def_property_ui_text(prop, "Editmode", "Use modifier while in the edit mode.");
	
	prop= RNA_def_property(srna, "on_cage", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", eModifierMode_OnCage);
	RNA_def_property_ui_text(prop, "On Cage", "Enable direct editing of modifier control cage.");
	
	prop= RNA_def_property(srna, "expanded", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "mode", eModifierMode_Expanded);
	RNA_def_property_ui_text(prop, "Expanded", "Set modifier expanded in the user interface.");

	/* types */
	rna_def_modifier_subsurf(brna);
	rna_def_modifier_lattice(brna);
	rna_def_modifier_curve(brna);
	rna_def_modifier_build(brna);
	rna_def_modifier_mirror(brna);
	rna_def_modifier_decimate(brna);
	rna_def_modifier_wave(brna);
	rna_def_modifier_armature(brna);
	rna_def_modifier_hook(brna);
	rna_def_modifier_softbody(brna);
	rna_def_modifier_boolean(brna);
	rna_def_modifier_array(brna);
	rna_def_modifier_edgesplit(brna);
	rna_def_modifier_displace(brna);
	rna_def_modifier_uvproject(brna);
	rna_def_modifier_smooth(brna);
	rna_def_modifier_cast(brna);
	rna_def_modifier_meshdeform(brna);
	rna_def_modifier_particlesystem(brna);
	rna_def_modifier_particleinstance(brna);
	rna_def_modifier_explode(brna);
	rna_def_modifier_cloth(brna);
	rna_def_modifier_collision(brna);
	rna_def_modifier_bevel(brna);
	rna_def_modifier_shrinkwrap(brna);
	rna_def_modifier_fluidsim(brna);
	rna_def_modifier_mask(brna);
	rna_def_modifier_simpledeform(brna);
}

#endif
