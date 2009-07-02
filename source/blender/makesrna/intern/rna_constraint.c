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
 * Contributor(s): Blender Foundation (2008), Joshua Leung, Roland Hess
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "DNA_action_types.h"
#include "DNA_constraint_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "WM_types.h"

EnumPropertyItem constraint_type_items[] ={
	{CONSTRAINT_TYPE_CHILDOF, "CHILD_OF", 0, "Child Of", ""},
	{CONSTRAINT_TYPE_TRANSFORM, "TRANSFORM", 0, "Transformation", ""},
	
	{CONSTRAINT_TYPE_LOCLIKE, "COPY_LOCATION", 0, "Copy Location", ""},
	{CONSTRAINT_TYPE_ROTLIKE, "COPY_ROTATION", 0, "Copy Rotation", ""},
	{CONSTRAINT_TYPE_SIZELIKE, "COPY_SCALE", 0, "Copy Scale", ""},
	
	{CONSTRAINT_TYPE_LOCLIMIT, "LIMIT_LOCATION", 0, "Limit Location", ""},
	{CONSTRAINT_TYPE_ROTLIMIT, "LIMIT_ROTATION", 0, "Limit Rotation", ""},
	{CONSTRAINT_TYPE_SIZELIMIT, "LIMIT_SCALE", 0, "Limit Scale", ""},
	{CONSTRAINT_TYPE_DISTLIMIT, "LIMIT_DISTANCE", 0, "Limit Distance", ""},
	
	{CONSTRAINT_TYPE_TRACKTO, "TRACK_TO", 0, "Track To", ""},
	{CONSTRAINT_TYPE_LOCKTRACK, "LOCKED_TRACK", 0, "Locked Track", ""},
	
	{CONSTRAINT_TYPE_MINMAX, "FLOOR", 0, "Floor", ""},
	{CONSTRAINT_TYPE_SHRINKWRAP, "SHRINKWRAP", 0, "Shrinkwrap", ""},
	{CONSTRAINT_TYPE_FOLLOWPATH, "FOLLOW_PATH", 0, "Follow Path", ""},
	
	{CONSTRAINT_TYPE_CLAMPTO, "CLAMP_TO", 0, "Clamp To", ""},
	{CONSTRAINT_TYPE_STRETCHTO, "STRETCH_TO", 0, "Stretch To", ""},
	
	{CONSTRAINT_TYPE_KINEMATIC, "IK", 0, "IK", ""},
	{CONSTRAINT_TYPE_RIGIDBODYJOINT, "RIGID_BODY_JOINT", 0, "Rigid Body Joint", ""},
	
	{CONSTRAINT_TYPE_ACTION, "ACTION", 0, "Action", ""},
	
	{CONSTRAINT_TYPE_PYTHON, "SCRIPT", 0, "Script", ""},
	
	{CONSTRAINT_TYPE_NULL, "NULL", 0, "Null", ""},
	{0, NULL, 0, NULL, NULL}};


#ifdef RNA_RUNTIME

#include "BKE_action.h"
#include "BKE_constraint.h"
#include "BKE_context.h"
#include "BKE_depsgraph.h"

#include "ED_object.h"

StructRNA *rna_ConstraintType_refine(struct PointerRNA *ptr)
{
	bConstraint *con= (bConstraint*)ptr->data;

	switch(con->type) {
		case CONSTRAINT_TYPE_CHILDOF:
			return &RNA_ChildOfConstraint;
		case CONSTRAINT_TYPE_TRACKTO:
			return &RNA_TrackToConstraint;
		case CONSTRAINT_TYPE_KINEMATIC:
			return &RNA_KinematicConstraint;
		case CONSTRAINT_TYPE_FOLLOWPATH:
			return &RNA_FollowPathConstraint;
		case CONSTRAINT_TYPE_ROTLIKE:
			return &RNA_CopyRotationConstraint;
		case CONSTRAINT_TYPE_LOCLIKE:
			return &RNA_CopyLocationConstraint;
		case CONSTRAINT_TYPE_SIZELIKE:
			return &RNA_CopyScaleConstraint;
		case CONSTRAINT_TYPE_PYTHON:
			return &RNA_PythonConstraint;
		case CONSTRAINT_TYPE_ACTION:
			return &RNA_ActionConstraint;
		case CONSTRAINT_TYPE_LOCKTRACK:
			return &RNA_LockedTrackConstraint;
		case CONSTRAINT_TYPE_STRETCHTO:
			return &RNA_StretchToConstraint;
		case CONSTRAINT_TYPE_MINMAX:
			return &RNA_FloorConstraint;
		case CONSTRAINT_TYPE_RIGIDBODYJOINT:
			return &RNA_RigidBodyJointConstraint;
		case CONSTRAINT_TYPE_CLAMPTO:
			return &RNA_ClampToConstraint;			
		case CONSTRAINT_TYPE_TRANSFORM:
			return &RNA_TransformConstraint;
		case CONSTRAINT_TYPE_ROTLIMIT:
			return &RNA_LimitRotationConstraint;
		case CONSTRAINT_TYPE_LOCLIMIT:
			return &RNA_LimitLocationConstraint;
		case CONSTRAINT_TYPE_SIZELIMIT:
			return &RNA_LimitScaleConstraint;
		case CONSTRAINT_TYPE_DISTLIMIT:
			return &RNA_LimitDistanceConstraint;
		case CONSTRAINT_TYPE_SHRINKWRAP:
			return &RNA_ShrinkwrapConstraint;
		default:
			return &RNA_UnknownType;
	}
}

static char *rna_Constraint_path(PointerRNA *ptr)
{
	return BLI_sprintfN("constraints[%s]", ((bConstraint*)ptr->data)->name);
}

static void rna_Constraint_update(bContext *C, PointerRNA *ptr)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob= ptr->id.data;

	if(ob->pose) update_pose_constraint_flags(ob->pose);

	object_test_constraints(ob);

	if(ob->type==OB_ARMATURE) DAG_object_flush_update(scene, ob, OB_RECALC_DATA|OB_RECALC_OB);
	else DAG_object_flush_update(scene, ob, OB_RECALC_OB);
}

static void rna_Constraint_dependency_update(bContext *C, PointerRNA *ptr)
{
	Object *ob= ptr->id.data;

	rna_Constraint_update(C, ptr);

	if(ob->pose) ob->pose->flag |= POSE_RECALC;	// checks & sorts pose channels
    DAG_scene_sort(CTX_data_scene(C));
}

static void rna_Constraint_influence_update(bContext *C, PointerRNA *ptr)
{
	Object *ob= ptr->id.data;

	if(ob->pose)
		ob->pose->flag |= (POSE_LOCKED|POSE_DO_UNLOCK);
	
	rna_Constraint_update(C, ptr);
}

static EnumPropertyItem space_pchan_items[] = {
	{0, "WORLD", 0, "World Space", ""},
	{2, "POSE", 0, "Pose Space", ""},
	{3, "LOCAL_WITH_PARENT", 0, "Local With Parent", ""},
	{1, "LOCAL", 0, "Local Space", ""},
	{0, NULL, 0, NULL, NULL}};

static EnumPropertyItem space_object_items[] = {
	{0, "WORLD", 0, "World Space", ""},
	{1, "LOCAL", 0, "Local (Without Parent) Space", ""},
	{0, NULL, 0, NULL, NULL}};

static EnumPropertyItem *rna_Constraint_owner_space_itemf(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;
	bConstraint *con= (bConstraint*)ptr->data;

	if(BLI_findindex(&ob->constraints, con) == -1)
		return space_pchan_items;
	else /* object */
		return space_object_items;
}

static EnumPropertyItem *rna_Constraint_target_space_itemf(PointerRNA *ptr)
{
	bConstraint *con= (bConstraint*)ptr->data;
	bConstraintTypeInfo *cti= constraint_get_typeinfo(con);
	ListBase targets = {NULL, NULL};
	bConstraintTarget *ct;
	
	if(cti && cti->get_constraint_targets) {
		cti->get_constraint_targets(con, &targets);
		
		for(ct=targets.first; ct; ct= ct->next)
			if(ct->tar && ct->tar->type == OB_ARMATURE)
				break;
		
		if(cti->flush_constraint_targets)
			cti->flush_constraint_targets(con, &targets, 1);

		if(ct)
			return space_pchan_items;
	}

	return space_object_items;
}

#else

static void rna_def_constrainttarget(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "ConstraintTarget", NULL);
	RNA_def_struct_ui_text(srna, "Constraint Target", "Target object for multi-target constraints.");
	RNA_def_struct_sdna(srna, "bConstraintTarget");

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tar");
	RNA_def_property_ui_text(prop, "Target", "Target Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "subtarget", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "subtarget");
	RNA_def_property_ui_text(prop, "Sub-Target", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	// space, flag and type still to do 
}

static void rna_def_constraint_childof(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "ChildOfConstraint", "Constraint"); 
	RNA_def_struct_ui_text(srna, "Child Of Constraint", "Creates constraint-based parent-child relationship."); 
	RNA_def_struct_sdna_from(srna, "bChildOfConstraint", "data"); 

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tar");
	RNA_def_property_ui_text(prop, "Target", "Target Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "subtarget", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "subtarget");
	RNA_def_property_ui_text(prop, "Sub-Target", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "locationx", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CHILDOF_LOCX);
	RNA_def_property_ui_text(prop, "Location X", "Use X Location of Parent.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "locationy", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CHILDOF_LOCY);
	RNA_def_property_ui_text(prop, "Location Y", "Use Y Location of Parent.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "locationz", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CHILDOF_LOCZ);
	RNA_def_property_ui_text(prop, "Location Z", "Use Z Location of Parent.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "rotationx", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CHILDOF_ROTX);
	RNA_def_property_ui_text(prop, "Rotation X", "Use X Rotation of Parent.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "rotationy", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CHILDOF_ROTY);
	RNA_def_property_ui_text(prop, "Rotation Y", "Use Y Rotation of Parent.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "rotationz", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CHILDOF_ROTZ);
	RNA_def_property_ui_text(prop, "Rotation Z", "Use Z Rotation of Parent.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "sizex", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CHILDOF_SIZEX);
	RNA_def_property_ui_text(prop, "Size X", "Use X Scale of Parent.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "sizey", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CHILDOF_SIZEY);
	RNA_def_property_ui_text(prop, "Size Y", "Use Y Scale of Parent.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "sizez", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CHILDOF_SIZEZ);
	RNA_def_property_ui_text(prop, "Size Z", "Use Z Scale of Parent.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_python(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "PythonConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Python Constraint", "Uses Python script for constraint evaluation.");
	RNA_def_struct_sdna_from(srna, "bPythonConstraint", "data");

	prop= RNA_def_property(srna, "targets", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "targets", NULL);
	RNA_def_property_struct_type(prop, "ConstraintTarget");
	RNA_def_property_ui_text(prop, "Targets", "Target Objects.");

	prop= RNA_def_property(srna, "number_of_targets", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "tarnum");
	RNA_def_property_ui_text(prop, "Number of Targets", "Usually only 1-3 are needed.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "text", PROP_POINTER, PROP_NONE);
	RNA_def_property_ui_text(prop, "Script", "The text object that contains the Python script.");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "use_targets", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PYCON_USETARGETS);
	RNA_def_property_ui_text(prop, "Use Targets", "Use the targets indicated in the constraint panel.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "script_error", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", PYCON_SCRIPTERROR);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Script Error", "The linked Python script has thrown an error.");
}

static void rna_def_constraint_kinematic(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "KinematicConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Kinematic Constraint", "Inverse Kinematics.");
	RNA_def_struct_sdna_from(srna, "bKinematicConstraint", "data");

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tar");
	RNA_def_property_ui_text(prop, "Target", "Target Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "subtarget", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "subtarget");
	RNA_def_property_ui_text(prop, "Sub-Target", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "iterations", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, 1, 10000);
	RNA_def_property_ui_text(prop, "Iterations", "Maximum number of solving iterations.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "pole_target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "poletar");
	RNA_def_property_ui_text(prop, "Pole Target", "Object for pole rotation.");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "pole_subtarget", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "polesubtarget");
	RNA_def_property_ui_text(prop, "Pole Sub-Target", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "pole_angle", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "poleangle");
	RNA_def_property_range(prop, 0.0, 180.f);
	RNA_def_property_ui_text(prop, "Pole Angle", "Pole rotation offset.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "weight", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.01, 1.f);
	RNA_def_property_ui_text(prop, "Weight", "For Tree-IK: Weight of position control for this target.");

	prop= RNA_def_property(srna, "orient_weight", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "orientweight");
	RNA_def_property_range(prop, 0.01, 1.f);
	RNA_def_property_ui_text(prop, "Orientation Weight", "For Tree-IK: Weight of orientation control for this target.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "chain_length", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "rootbone");
	RNA_def_property_range(prop, 0, 255);
	RNA_def_property_ui_text(prop, "Chain Length", "How many bones are included in the IK effect - 0 uses all bones.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "tail", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CONSTRAINT_IK_TIP);
	RNA_def_property_ui_text(prop, "Use Tail", "Include bone's tail as last element in chain.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "rotation", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CONSTRAINT_IK_ROT);
	RNA_def_property_ui_text(prop, "Rotation", "Chain follows rotation of target.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "targetless", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CONSTRAINT_IK_AUTO);
	RNA_def_property_ui_text(prop, "Targetless", "Use targetless IK.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "stretch", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CONSTRAINT_IK_STRETCH);
	RNA_def_property_ui_text(prop, "Stretch", "Enable IK Stretching.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_track_to(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem track_items[] = {
		{TRACK_X, "TRACK_X", 0, "X", ""},
		{TRACK_Y, "TRACK_Y", 0, "Y", ""},
		{TRACK_Z, "TRACK_Z", 0, "Z", ""},
		{TRACK_nX, "TRACK_NEGATIVE_X", 0, "-X", ""},
		{TRACK_nY, "TRACK_NEGATIVE_Y", 0, "-Y", ""},
		{TRACK_nZ, "TRACK_NEGATIVE_Z", 0, "-Z", ""},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem up_items[] = {
		{TRACK_X, "UP_X", 0, "X", ""},
		{TRACK_Y, "UP_Y", 0, "Y", ""},
		{TRACK_Z, "UP_Z", 0, "Z", ""},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "TrackToConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Track To Constraint", "Aims the constrained object toward the target.");
	RNA_def_struct_sdna_from(srna, "bTrackToConstraint", "data");

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tar");
	RNA_def_property_ui_text(prop, "Target", "Target Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "subtarget", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "subtarget");
	RNA_def_property_ui_text(prop, "Sub-Target", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "track", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "reserved1");
	RNA_def_property_enum_items(prop, track_items);
	RNA_def_property_ui_text(prop, "Track Axis", "Axis that points to the target object.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "up", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "reserved2");
	RNA_def_property_enum_items(prop, up_items);
	RNA_def_property_ui_text(prop, "Up Axis", "Axis that points upward.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "target_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", TARGET_Z_UP);
	RNA_def_property_ui_text(prop, "Target Z", "Target's Z axis, not World Z axis, will constraint the Up direction.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_rotate_like(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "CopyRotationConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Copy Rotation Constraint", "Copies the rotation of the target.");
	RNA_def_struct_sdna_from(srna, "bRotateLikeConstraint", "data");

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tar");
	RNA_def_property_ui_text(prop, "Target", "Target Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "subtarget", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "subtarget");
	RNA_def_property_ui_text(prop, "Sub-Target", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "rotate_like_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ROTLIKE_X);
	RNA_def_property_ui_text(prop, "Like X", "Copy the target's X rotation.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "rotate_like_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ROTLIKE_Y);
	RNA_def_property_ui_text(prop, "Like Y", "Copy the target's Y rotation.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "rotate_like_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ROTLIKE_Z);
	RNA_def_property_ui_text(prop, "Like Z", "Copy the target's Z rotation.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "invert_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ROTLIKE_X_INVERT);
	RNA_def_property_ui_text(prop, "Invert X", "Invert the X rotation.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "invert_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ROTLIKE_Y_INVERT);
	RNA_def_property_ui_text(prop, "Invert Y", "Invert the Y rotation.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "invert_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ROTLIKE_Z_INVERT);
	RNA_def_property_ui_text(prop, "Invert Z", "Invert the Z rotation.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "offset", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", ROTLIKE_OFFSET);
	RNA_def_property_ui_text(prop, "Offset", "Add original rotation into copied rotation.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_locate_like(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "CopyLocationConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Copy Location Constraint", "Copies the location of the target.");

	prop= RNA_def_property(srna, "head_tail", PROP_FLOAT, PROP_PERCENTAGE);
	RNA_def_property_float_sdna(prop, "bConstraint", "headtail");
	RNA_def_property_ui_text(prop, "Head/Tail", "Target along length of bone: Head=0, Tail=1.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	RNA_def_struct_sdna_from(srna, "bLocateLikeConstraint", "data");

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tar");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Target", "Target Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "subtarget", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "subtarget");
	RNA_def_property_ui_text(prop, "Sub-Target", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "locate_like_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LOCLIKE_X);
	RNA_def_property_ui_text(prop, "Like X", "Copy the target's X location.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "locate_like_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LOCLIKE_Y);
	RNA_def_property_ui_text(prop, "Like Y", "Copy the target's Y location.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "locate_like_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LOCLIKE_Z);
	RNA_def_property_ui_text(prop, "Like Z", "Copy the target's Z location.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "invert_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LOCLIKE_X_INVERT);
	RNA_def_property_ui_text(prop, "Invert X", "Invert the X location.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "invert_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LOCLIKE_Y_INVERT);
	RNA_def_property_ui_text(prop, "Invert Y", "Invert the Y location.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "invert_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LOCLIKE_Z_INVERT);
	RNA_def_property_ui_text(prop, "Invert Z", "Invert the Z location.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "offset", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LOCLIKE_OFFSET);
	RNA_def_property_ui_text(prop, "Offset", "Add original location into copied location.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_minmax(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem minmax_items[] = {
		{LOCLIKE_X, "FLOOR_X", 0, "X", ""},
		{LOCLIKE_Y, "FLOOR_Y", 0, "Y", ""},
		{LOCLIKE_Z, "FLOOR_Z", 0, "Z", ""},
		{LOCLIKE_X_INVERT, "FLOOR_NEGATIVE_X", 0, "-X", ""},
		{LOCLIKE_Y_INVERT, "FLOOR_NEGATIVE_Y", 0, "-Y", ""},
		{LOCLIKE_Z_INVERT, "FLOOR_NEGATIVE_Z", 0, "-Z", ""},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "FloorConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Floor Constraint", "Uses the target object for location limitation.");
	RNA_def_struct_sdna_from(srna, "bMinMaxConstraint","data");

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tar");
	RNA_def_property_ui_text(prop, "Target", "Target Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "subtarget", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "subtarget");
	RNA_def_property_ui_text(prop, "Sub-Target", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "floor_location", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "minmaxflag");
	RNA_def_property_enum_items(prop, minmax_items);
	RNA_def_property_ui_text(prop, "Floor Location", "Location of target that object will not pass through.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "sticky", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MINMAX_STICKY);
	RNA_def_property_ui_text(prop, "Sticky", "Immobilize object while constrained.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "use_rotation", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", MINMAX_USEROT);
	RNA_def_property_ui_text(prop, "Use Rotation", "Use the target's rotation to determine floor.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "offset", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.0, 100.f);
	RNA_def_property_ui_text(prop, "Offset", "Offset of floor from object center.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_size_like(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "CopyScaleConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Copy Scale Constraint", "Copies the scale of the target.");
	RNA_def_struct_sdna_from(srna, "bSizeLikeConstraint", "data");

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tar");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Target", "Target Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "subtarget", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "subtarget");
	RNA_def_property_ui_text(prop, "Sub-Target", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "size_like_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SIZELIKE_X);
	RNA_def_property_ui_text(prop, "Like X", "Copy the target's X scale.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "size_like_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SIZELIKE_Y);
	RNA_def_property_ui_text(prop, "Like Y", "Copy the target's Y scale.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "size_like_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SIZELIKE_Z);
	RNA_def_property_ui_text(prop, "Like Z", "Copy the target's Z scale.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "offset", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", SIZELIKE_OFFSET);
	RNA_def_property_ui_text(prop, "Offset", "Add original scale into copied scale.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_action(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem transform_channel_items[] = {
		{00, "ROTATION_X", 0, "Rotation X", ""},
		{01, "ROTATION_Y", 0, "Rotation Y", ""},
		{02, "ROTATION_Z", 0, "Rotation Z", ""},
		{10, "SIZE_X", 0, "Scale X", ""},
		{11, "SIZE_Y", 0, "Scale Y", ""},
		{12, "SIZE_Z", 0, "Scale Z", ""},
		{20, "LOCATION_X", 0, "Location X", ""},
		{21, "LOCATION_Y", 0, "Location Y", ""},
		{22, "LOCATION_Z", 0, "Location Z", ""},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "ActionConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Action Constraint", "Map an action to the transform axes of a bone.");
	RNA_def_struct_sdna_from(srna, "bActionConstraint", "data");

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tar");
	RNA_def_property_ui_text(prop, "Target", "Target Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "subtarget", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "subtarget");
	RNA_def_property_ui_text(prop, "Sub-Target", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "transform_channel", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "type");
	RNA_def_property_enum_items(prop, transform_channel_items);
	RNA_def_property_ui_text(prop, "Transform Channel", "Transformation channel from the target that is used to key the Action.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "action", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "act");
	RNA_def_property_ui_text(prop, "Action", "");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "start_frame", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "start");
	RNA_def_property_range(prop, MINFRAME, MAXFRAME);
	RNA_def_property_ui_text(prop, "Start Frame", "First frame of the Action to use.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "end_frame", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "end");
	RNA_def_property_range(prop, MINFRAME, MAXFRAME);
	RNA_def_property_ui_text(prop, "End Frame", "Last frame of the Action to use.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "maximum", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "max");
	RNA_def_property_range(prop, 0.0, 1000.f);
	RNA_def_property_ui_text(prop, "Maximum", "Maximum value for target channel range.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "minimum", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "min");
	RNA_def_property_range(prop, 0.0, 1000.f);
	RNA_def_property_ui_text(prop, "Minimum", "Minimum value for target channel range.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_locked_track(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem locktrack_items[] = {
		{TRACK_X, "TRACK_X", 0, "X", ""},
		{TRACK_Y, "TRACK_Y", 0, "Y", ""},
		{TRACK_Z, "TRACK_Z", 0, "Z", ""},
		{TRACK_nX, "TRACK_NEGATIVE_X", 0, "-X", ""},
		{TRACK_nY, "TRACK_NEGATIVE_Y", 0, "-Y", ""},
		{TRACK_nZ, "TRACK_NEGATIVE_Z", 0, "-Z", ""},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem lock_items[] = {
		{TRACK_X, "LOCK_X", 0, "X", ""},
		{TRACK_Y, "LOCK_Y", 0, "Y", ""},
		{TRACK_Z, "LOCK_Z", 0, "Z", ""},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "LockedTrackConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Locked Track Constraint", "Points toward the target along the track axis, while locking the other axis.");
	RNA_def_struct_sdna_from(srna, "bLockTrackConstraint", "data");

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tar");
	RNA_def_property_ui_text(prop, "Target", "Target Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "subtarget", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "subtarget");
	RNA_def_property_ui_text(prop, "Sub-Target", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "track", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "trackflag");
	RNA_def_property_enum_items(prop, locktrack_items);
	RNA_def_property_ui_text(prop, "Track Axis", "Axis that points to the target object.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "locked", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "lockflag");
	RNA_def_property_enum_items(prop, lock_items);
	RNA_def_property_ui_text(prop, "Locked Axis", "Axis that points upward.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_follow_path(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem forwardpath_items[] = {
		{TRACK_X, "FORWARD_X", 0, "X", ""},
		{TRACK_Y, "FORWARD_Y", 0, "Y", ""},
		{TRACK_Z, "FORWARD_Z", 0, "Z", ""},
		{TRACK_nX, "TRACK_NEGATIVE_X", 0, "-X", ""},
		{TRACK_nY, "TRACK_NEGATIVE_Y", 0, "-Y", ""},
		{TRACK_nZ, "TRACK_NEGATIVE_Z", 0, "-Z", ""},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem pathup_items[] = {
		{TRACK_X, "UP_X", 0, "X", ""},
		{TRACK_Y, "UP_Y", 0, "Y", ""},
		{TRACK_Z, "UP_Z", 0, "Z", ""},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "FollowPathConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Follow Path Constraint", "Locks motion to the target path.");
	RNA_def_struct_sdna_from(srna, "bFollowPathConstraint", "data");

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tar");
	RNA_def_property_ui_text(prop, "Target", "Target Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "offset", PROP_INT, PROP_NONE);
	RNA_def_property_range(prop, -300000.0, 300000.f);
	RNA_def_property_ui_text(prop, "Offset", "Offset from the position corresponding to the time frame.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "forward", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "trackflag");
	RNA_def_property_enum_items(prop, forwardpath_items);
	RNA_def_property_ui_text(prop, "Forward Axis", "Axis that points forward along the path.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "up", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "upflag");
	RNA_def_property_enum_items(prop, pathup_items);
	RNA_def_property_ui_text(prop, "Up Axis", "Axis that points upward.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "curve_follow", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "followflag", 1);
	RNA_def_property_ui_text(prop, "Follow Curve", "Object will follow the heading and banking of the curve.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_stretch_to(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem volume_items[] = {
		{VOLUME_XZ, "VOLUME_XZX", 0, "XZ", ""},
		{VOLUME_X, "VOLUME_X", 0, "Y", ""},
		{VOLUME_Z, "VOLUME_Z", 0, "Z", ""},
		{NO_VOLUME, "NO_VOLUME", 0, "None", ""},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem plane_items[] = {
		{PLANE_X, "PLANE_X", 0, "X", "Keep X Axis"},
		{PLANE_Z, "PLANE_Z", 0, "Z", "Keep Z Axis"},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "StretchToConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Stretch To Constraint", "Stretches to meet the target object.");
	RNA_def_struct_sdna_from(srna, "bStretchToConstraint", "data");

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tar");
	RNA_def_property_ui_text(prop, "Target", "Target Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "volume", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "volmode");
	RNA_def_property_enum_items(prop, volume_items);
	RNA_def_property_ui_text(prop, "Maintain Volume", "Maintain the object's volume as it stretches.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "keep_axis", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "plane");
	RNA_def_property_enum_items(prop, plane_items);
	RNA_def_property_ui_text(prop, "Keep Axis", "Axis to maintain during stretch.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "original_length", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "orglength");
	RNA_def_property_range(prop, 0.0, 100.f);
	RNA_def_property_ui_text(prop, "Original Length", "Length at rest position.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "bulge", PROP_FLOAT, PROP_NONE);
	RNA_def_property_range(prop, 0.0, 100.f);
	RNA_def_property_ui_text(prop, "Volume Variation", "Factor between volume variation and stretching.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_rigid_body_joint(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem pivot_items[] = {
		{CONSTRAINT_RB_BALL, "BALL", 0, "Ball", ""},
		{CONSTRAINT_RB_HINGE, "HINGE", 0, "Hinge", ""},
		{CONSTRAINT_RB_CONETWIST, "CONE_TWIST", 0, "Cone Twist", ""},
		{CONSTRAINT_RB_GENERIC6DOF, "GENERIC_6_DOF", 0, "Generic 6 DoF", ""},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "RigidBodyJointConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Rigid Body Joint Constraint", "For use with the Game Engine.");
	RNA_def_struct_sdna_from(srna, "bRigidBodyJointConstraint", "data");

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tar");
	RNA_def_property_ui_text(prop, "Target", "Target Object.");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "child", PROP_POINTER, PROP_NONE);
	RNA_def_property_ui_text(prop, "Child Object", "Child object.");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "pivot_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "type");
	RNA_def_property_enum_items(prop, pivot_items);
	RNA_def_property_ui_text(prop, "Pivot Type", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "pivot_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "pivX");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Pivot X", "Offset pivot on X.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "pivot_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "pivY");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Pivot Y", "Offset pivot on Y.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "pivot_z", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "pivZ");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Pivot Z", "Offset pivot on Z.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "axis_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "axX");
	RNA_def_property_range(prop, -360.0, 360.f);
	RNA_def_property_ui_text(prop, "Axis X", "Rotate pivot on X axis in degrees.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "axis_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "axY");
	RNA_def_property_range(prop, -360.0, 360.f);
	RNA_def_property_ui_text(prop, "Axis Y", "Rotate pivot on Y axis in degrees.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "axis_z", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "axZ");
	RNA_def_property_range(prop, -360.0, 360.f);
	RNA_def_property_ui_text(prop, "Axis Z", "Rotate pivot on Z axis in degrees.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
	
	/* XXX not sure how to wrap the two 6 element arrays for the generic joint */
	//float       minLimit[6];
	//float       maxLimit[6];
	
	prop= RNA_def_property(srna, "disable_linked_collision", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CONSTRAINT_DISABLE_LINKED_COLLISION);
	RNA_def_property_ui_text(prop, "Disable Linked Collision", "Disable collision between linked bodies.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "draw_pivot", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CONSTRAINT_DRAW_PIVOT);
	RNA_def_property_ui_text(prop, "Draw Pivot", "Display the pivot point and rotation in 3D view.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_clamp_to(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem clamp_items[] = {
		{CLAMPTO_AUTO, "CLAMPTO_AUTO", 0, "Auto", ""},
		{CLAMPTO_X, "CLAMPTO_X", 0, "X", ""},
		{CLAMPTO_Y, "CLAMPTO_Y", 0, "Y", ""},
		{CLAMPTO_Z, "CLAMPTO_Z", 0, "Z", ""},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "ClampToConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Clamp To Constraint", "Constrains an object's location to the nearest point along the target path.");
	RNA_def_struct_sdna_from(srna, "bClampToConstraint", "data");

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tar");
	RNA_def_property_ui_text(prop, "Target", "Target Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "main_axis", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "flag");
	RNA_def_property_enum_items(prop, clamp_items);
	RNA_def_property_ui_text(prop, "Main Axis", "Main axis of movement.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "cyclic", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag2", CLAMPTO_CYCLIC);
	RNA_def_property_ui_text(prop, "Cyclic", "Treat curve as cyclic curve (no clamping to curve bounding box.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_transform(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem transform_items[] = {
		{0, "LOCATION", 0, "Loc", ""},
		{1, "ROTATION", 0, "Rot", ""},
		{2, "SCALE", 0, "Scale", ""},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem axis_map_items[] = {
		{0, "X", 0, "X", ""},
		{1, "Y", 0, "Y", ""},
		{2, "Z", 0, "Z", ""},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "TransformConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Transformation Constraint", "Maps transformations of the target to the object.");
	RNA_def_struct_sdna_from(srna, "bTransformConstraint", "data");

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tar");
	RNA_def_property_ui_text(prop, "Target", "Target Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "subtarget", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "subtarget");
	RNA_def_property_ui_text(prop, "Sub-Target", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "map_from", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "from");
	RNA_def_property_enum_items(prop, transform_items);
	RNA_def_property_ui_text(prop, "Map From", "The transformation type to use from the target.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "map_to", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "to");
	RNA_def_property_enum_items(prop, transform_items);
	RNA_def_property_ui_text(prop, "Map To", "The transformation type to affect of the constrained object.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "map_to_x_from", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "map[0]");
	RNA_def_property_enum_items(prop, axis_map_items);
	RNA_def_property_ui_text(prop, "Map To X From", "The source axis constrained object's X axis uses.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "map_to_y_from", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "map[1]");
	RNA_def_property_enum_items(prop, axis_map_items);
	RNA_def_property_ui_text(prop, "Map To Y From", "The source axis constrained object's Y axis uses.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "map_to_z_from", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "map[2]");
	RNA_def_property_enum_items(prop, axis_map_items);
	RNA_def_property_ui_text(prop, "Map To Z From", "The source axis constrained object's Z axis uses.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "extrapolate_motion", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "expo", CLAMPTO_CYCLIC);
	RNA_def_property_ui_text(prop, "Extrapolate Motion", "Extrapolate ranges.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "from_min_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "from_min[0]");
	RNA_def_property_range(prop, 0.0, 1000.f);
	RNA_def_property_ui_text(prop, "From Minimum X", "Bottom range of X axis source motion.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "from_min_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "from_min[1]");
	RNA_def_property_range(prop, 0.0, 1000.f);
	RNA_def_property_ui_text(prop, "From Minimum Y", "Bottom range of Y axis source motion.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "from_min_z", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "from_min[2]");
	RNA_def_property_range(prop, 0.0, 1000.f);
	RNA_def_property_ui_text(prop, "From Minimum Z", "Bottom range of Z axis source motion.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "from_max_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "from_max[0]");
	RNA_def_property_range(prop, 0.0, 1000.f);
	RNA_def_property_ui_text(prop, "From Maximum X", "Top range of X axis source motion.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "from_max_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "from_max[1]");
	RNA_def_property_range(prop, 0.0, 1000.f);
	RNA_def_property_ui_text(prop, "From Maximum Y", "Top range of Y axis source motion.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "from_max_z", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "from_max[2]");
	RNA_def_property_range(prop, 0.0, 1000.f);
	RNA_def_property_ui_text(prop, "From Maximum Z", "Top range of Z axis source motion.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "to_min_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "to_min[0]");
	RNA_def_property_range(prop, 0.0, 1000.f);
	RNA_def_property_ui_text(prop, "To Minimum X", "Bottom range of X axis destination motion.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "to_min_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "to_min[1]");
	RNA_def_property_range(prop, 0.0, 1000.f);
	RNA_def_property_ui_text(prop, "To Minimum Y", "Bottom range of Y axis destination motion.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "to_min_z", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "to_min[2]");
	RNA_def_property_range(prop, 0.0, 1000.f);
	RNA_def_property_ui_text(prop, "To Minimum Z", "Bottom range of Z axis destination motion.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "to_max_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "to_max[0]");
	RNA_def_property_range(prop, 0.0, 1000.f);
	RNA_def_property_ui_text(prop, "To Maximum X", "Top range of X axis destination motion.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "to_max_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "to_max[1]");
	RNA_def_property_range(prop, 0.0, 1000.f);
	RNA_def_property_ui_text(prop, "To Maximum Y", "Top range of Y axis destination motion.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "to_max_z", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "to_max[2]");
	RNA_def_property_range(prop, 0.0, 1000.f);
	RNA_def_property_ui_text(prop, "To Maximum Z", "Top range of Z axis destination motion.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_location_limit(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "LimitLocationConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Limit Location Constraint", "Limits the location of the constrained object.");
	RNA_def_struct_sdna_from(srna, "bLocLimitConstraint", "data");

	prop= RNA_def_property(srna, "use_minimum_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LIMIT_XMIN);
	RNA_def_property_ui_text(prop, "Minimum X", "Use the minimum X value.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "use_minimum_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LIMIT_YMIN);
	RNA_def_property_ui_text(prop, "Minimum Y", "Use the minimum Y value.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "use_minimum_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LIMIT_ZMIN);
	RNA_def_property_ui_text(prop, "Minimum Z", "Use the minimum Z value.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "use_maximum_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LIMIT_XMAX);
	RNA_def_property_ui_text(prop, "Maximum X", "Use the maximum X value.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "use_maximum_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LIMIT_YMAX);
	RNA_def_property_ui_text(prop, "Maximum Y", "Use the maximum Y value.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "use_maximum_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LIMIT_ZMAX);
	RNA_def_property_ui_text(prop, "Maximum Z", "Use the maximum Z value.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "minimum_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "xmin");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Minimum X", "Lowest X value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "minimum_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ymin");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Minimum Y", "Lowest Y value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "minimum_z", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "zmin");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Minimum Z", "Lowest Z value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "maximum_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "xmax");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Maximum X", "Highest X value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "maximum_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ymax");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Maximum Y", "Highest Y value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "maximum_z", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "zmax");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Maximum Z", "Highest Z value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "limit_transform", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag2", LIMIT_TRANSFORM);
	RNA_def_property_ui_text(prop, "For Transform", "Transforms are affected by this constraint as well.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_rotation_limit(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "LimitRotationConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Limit Rotation Constraint", "Limits the rotation of the constrained object.");
	RNA_def_struct_sdna_from(srna, "bRotLimitConstraint", "data");

	prop= RNA_def_property(srna, "use_limit_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LIMIT_XROT);
	RNA_def_property_ui_text(prop, "Limit X", "Use the minimum X value.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "use_limit_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LIMIT_YROT);
	RNA_def_property_ui_text(prop, "Limit Y", "Use the minimum Y value.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "use_limit_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LIMIT_ZROT);
	RNA_def_property_ui_text(prop, "Limit Z", "Use the minimum Z value.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "minimum_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "xmin");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Minimum X", "Lowest X value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "minimum_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ymin");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Minimum Y", "Lowest Y value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "minimum_z", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "zmin");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Minimum Z", "Lowest Z value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "maximum_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "xmax");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Maximum X", "Highest X value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "maximum_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ymax");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Maximum Y", "Highest Y value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "maximum_z", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "zmax");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Maximum Z", "Highest Z value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "limit_transform", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag2", LIMIT_TRANSFORM);
	RNA_def_property_ui_text(prop, "For Transform", "Transforms are affected by this constraint as well.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_size_limit(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "LimitScaleConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Limit Size Constraint", "Limits the scaling of the constrained object.");
	RNA_def_struct_sdna_from(srna, "bSizeLimitConstraint", "data");

	prop= RNA_def_property(srna, "use_minimum_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LIMIT_XMIN);
	RNA_def_property_ui_text(prop, "Minimum X", "Use the minimum X value.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "use_minimum_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LIMIT_YMIN);
	RNA_def_property_ui_text(prop, "Minimum Y", "Use the minimum Y value.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "use_minimum_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LIMIT_ZMIN);
	RNA_def_property_ui_text(prop, "Minimum Z", "Use the minimum Z value.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "use_maximum_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LIMIT_XMAX);
	RNA_def_property_ui_text(prop, "Maximum X", "Use the maximum X value.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "use_maximum_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LIMIT_YMAX);
	RNA_def_property_ui_text(prop, "Maximum Y", "Use the maximum Y value.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "use_maximum_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", LIMIT_ZMAX);
	RNA_def_property_ui_text(prop, "Maximum Z", "Use the maximum Z value.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "minimum_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "xmin");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Minimum X", "Lowest X value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "minimum_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ymin");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Minimum Y", "Lowest Y value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "minimum_z", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "zmin");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Minimum Z", "Lowest Z value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "maximum_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "xmax");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Maximum X", "Highest X value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "maximum_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ymax");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Maximum Y", "Highest Y value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "maximum_z", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "zmax");
	RNA_def_property_range(prop, -1000.0, 1000.f);
	RNA_def_property_ui_text(prop, "Maximum Z", "Highest Z value to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "limit_transform", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag2", LIMIT_TRANSFORM);
	RNA_def_property_ui_text(prop, "For Transform", "Transforms are affected by this constraint as well.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_distance_limit(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem distance_items[] = {
		{LIMITDIST_INSIDE, "LIMITDIST_INSIDE", 0, "Inside", ""},
		{LIMITDIST_OUTSIDE, "LIMITDIST_OUTSIDE", 0, "Outside", ""},
		{LIMITDIST_ONSURFACE, "LIMITDIST_ONSURFACE", 0, "On Surface", ""},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "LimitDistanceConstraint", "Constraint");
	RNA_def_struct_ui_text(srna, "Limit Distance Constraint", "Limits the distance from target object.");
	RNA_def_struct_sdna_from(srna, "bDistLimitConstraint", "data");

	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "tar");
	RNA_def_property_ui_text(prop, "Target", "Target Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "subtarget", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "subtarget");
	RNA_def_property_ui_text(prop, "Sub-Target", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");

	prop= RNA_def_property(srna, "distance", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "dist");
	RNA_def_property_range(prop, 0.0, 100.f);
	RNA_def_property_ui_text(prop, "Distance", "Radius of limiting sphere.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");

	prop= RNA_def_property(srna, "limit_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "mode");
	RNA_def_property_enum_items(prop, distance_items);
	RNA_def_property_ui_text(prop, "Limit Mode", "Distances in relation to sphere of influence to allow.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

static void rna_def_constraint_shrinkwrap(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	static EnumPropertyItem type_items[] = {
		{MOD_SHRINKWRAP_NEAREST_SURFACE, "NEAREST_SURFACE", 0, "Nearest Surface Point", ""},
		{MOD_SHRINKWRAP_PROJECT, "PROJECT", 0, "Project", ""},
		{MOD_SHRINKWRAP_NEAREST_VERTEX, "NEAREST_VERTEX", 0, "Nearest Vertex", ""},
		{0, NULL, 0, NULL, NULL}};
	
	srna= RNA_def_struct(brna, "ShrinkwrapConstraint", "Constraint"); 
	RNA_def_struct_ui_text(srna, "Shrinkwrap Constraint", "Creates constraint-based shrinkwrap relationship."); 
	RNA_def_struct_sdna_from(srna, "bShrinkwrapConstraint", "data");
	
	prop= RNA_def_property(srna, "target", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "target");
	RNA_def_property_ui_text(prop, "Target", "Target Object");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_dependency_update");
	
	prop= RNA_def_property(srna, "shrinkwrap_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "shrinkType");
	RNA_def_property_enum_items(prop, type_items);
	RNA_def_property_ui_text(prop, "Shrinkwrap Type", "Selects type of shrinkwrap algorithm for target position");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
	
	prop= RNA_def_property(srna, "distance", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "dist");
	RNA_def_property_range(prop, 0.0, 100.f);
	RNA_def_property_ui_text(prop, "Distance", "Distance to Target.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
	
	prop= RNA_def_property(srna, "axis_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "projAxis", MOD_SHRINKWRAP_PROJECT_OVER_X_AXIS);
	RNA_def_property_ui_text(prop, "Axis X", "Projection over X Axis");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
	
	prop= RNA_def_property(srna, "axis_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "projAxis", MOD_SHRINKWRAP_PROJECT_OVER_Y_AXIS);
	RNA_def_property_ui_text(prop, "Axis Y", "Projection over Y Axis");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
	
	prop= RNA_def_property(srna, "axis_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "projAxis", MOD_SHRINKWRAP_PROJECT_OVER_Z_AXIS);
	RNA_def_property_ui_text(prop, "Axis Z", "Projection over Z Axis");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_update");
}

/* base struct for constraints */
void RNA_def_constraint(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	/* data */
	srna= RNA_def_struct(brna, "Constraint", NULL );
	RNA_def_struct_ui_text(srna, "Constraint", "Constraint modifying the transformation of objects and bones.");
	RNA_def_struct_refine_func(srna, "rna_ConstraintType_refine");
	RNA_def_struct_path_func(srna, "rna_Constraint_path");
	RNA_def_struct_sdna(srna, "bConstraint");
	
	/* strings */
	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_ui_text(prop, "Name", "");
	RNA_def_struct_name_property(srna, prop);
	
	/* enums */
	prop= RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_enum_sdna(prop, NULL, "type");
	RNA_def_property_enum_items(prop, constraint_type_items);
	RNA_def_property_ui_text(prop, "Type", "");

	prop= RNA_def_property(srna, "owner_space", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "ownspace");
	RNA_def_property_enum_funcs(prop, NULL, NULL, "rna_Constraint_owner_space_itemf");
	RNA_def_property_ui_text(prop, "Owner Space", "Space that owner is evaluated in.");

	prop= RNA_def_property(srna, "target_space", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "tarspace");
	RNA_def_property_enum_funcs(prop, NULL, NULL, "rna_Constraint_target_space_itemf");
	RNA_def_property_ui_text(prop, "Target Space", "Space that target is evaluated in.");

	/* flags */
		// XXX do we want to wrap this?
	prop= RNA_def_property(srna, "expanded", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CONSTRAINT_EXPAND);
	RNA_def_property_ui_text(prop, "Expanded", "Constraint's panel is expanded in UI.");
	
		// XXX this is really an internal flag, but it may be useful for some tools to be able to access this...
	prop= RNA_def_property(srna, "disabled", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CONSTRAINT_DISABLE);
	RNA_def_property_ui_text(prop, "Disabled", "Constraint has invalid settings and will not be evaluated.");
	
		// TODO: setting this to true must ensure that all others in stack are turned off too...
	prop= RNA_def_property(srna, "active", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CONSTRAINT_ACTIVE);
	RNA_def_property_ui_text(prop, "Active", "Constraint is the one being edited ");
	
	prop= RNA_def_property(srna, "proxy_local", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", CONSTRAINT_PROXY_LOCAL);
	RNA_def_property_ui_text(prop, "Proxy Local", "Constraint was added in this proxy instance (i.e. did not belong to source Armature).");
	
	/* values */
	prop= RNA_def_property(srna, "influence", PROP_FLOAT, PROP_PERCENTAGE);
	RNA_def_property_float_sdna(prop, NULL, "enforce");
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Influence", "Amount of influence constraint will have on the final solution.");
	RNA_def_property_update(prop, NC_OBJECT|ND_CONSTRAINT, "rna_Constraint_influence_update");
	
	/* pointers */
	rna_def_constrainttarget(brna);

	rna_def_constraint_childof(brna);
	rna_def_constraint_python(brna);
	rna_def_constraint_stretch_to(brna);
	rna_def_constraint_follow_path(brna);
	rna_def_constraint_locked_track(brna);
	rna_def_constraint_action(brna);
	rna_def_constraint_size_like(brna);
	rna_def_constraint_locate_like(brna);
	rna_def_constraint_rotate_like(brna);
	rna_def_constraint_minmax(brna);
	rna_def_constraint_track_to(brna);
	rna_def_constraint_kinematic(brna);
	rna_def_constraint_rigid_body_joint(brna);
	rna_def_constraint_clamp_to(brna);
	rna_def_constraint_distance_limit(brna);
	rna_def_constraint_size_limit(brna);
	rna_def_constraint_rotation_limit(brna);
	rna_def_constraint_location_limit(brna);
	rna_def_constraint_transform(brna);
	rna_def_constraint_shrinkwrap(brna);
}

#endif

