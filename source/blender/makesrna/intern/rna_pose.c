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
 * Contributor(s): Blender Foundation (2008), Roland Hess
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_constraint_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "WM_types.h"

#ifdef RNA_RUNTIME

#include "BLI_arithb.h"

#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_idprop.h"

#include "ED_armature.h"

static void rna_Pose_update(bContext *C, PointerRNA *ptr)
{
	// XXX when to use this? ob->pose->flag |= (POSE_LOCKED|POSE_DO_UNLOCK);

	DAG_object_flush_update(CTX_data_scene(C), ptr->id.data, OB_RECALC_DATA);
}

IDProperty *rna_PoseChannel_idproperties(PointerRNA *ptr, int create)
{
	bPoseChannel *pchan= ptr->data;

	if(create && !pchan->prop) {
		IDPropertyTemplate val = {0};
		pchan->prop= IDP_New(IDP_GROUP, val, "RNA_PoseChannel group");
	}

	return pchan->prop;
}

static void rna_PoseChannel_euler_rotation_get(PointerRNA *ptr, float *value)
{
	bPoseChannel *pchan= ptr->data;

	if(pchan->rotmode == PCHAN_ROT_QUAT)
		QuatToEul(pchan->quat, value);
	else
		VECCOPY(value, pchan->eul);
}

static void rna_PoseChannel_euler_rotation_set(PointerRNA *ptr, const float *value)
{
	bPoseChannel *pchan= ptr->data;

	if(pchan->rotmode == PCHAN_ROT_QUAT)
		EulToQuat((float*)value, pchan->quat);
	else
		VECCOPY(pchan->eul, value);
}

static void rna_PoseChannel_name_set(PointerRNA *ptr, const char *value)
{
	Object *ob= (Object*)ptr->id.data;
	bPoseChannel *pchan= (bPoseChannel*)ptr->data;
	char oldname[32], newname[32];
	
	/* need to be on the stack */
	BLI_strncpy(newname, value, 32);
	BLI_strncpy(oldname, pchan->name, 32);
	
	ED_armature_bone_rename(ob->data, oldname, newname);
}

static int rna_PoseChannel_has_ik_get(PointerRNA *ptr)
{
	Object *ob= (Object*)ptr->id.data;
	bPoseChannel *pchan= (bPoseChannel*)ptr->data;

	return ED_pose_channel_in_IK_chain(ob, pchan);
}

static PointerRNA rna_Pose_active_bone_group_get(PointerRNA *ptr)
{
	bPose *pose= (bPose*)ptr->data;
	return rna_pointer_inherit_refine(ptr, &RNA_BoneGroup, BLI_findlink(&pose->agroups, pose->active_group-1));
}

static int rna_Pose_active_bone_group_index_get(PointerRNA *ptr)
{
	bPose *pose= (bPose*)ptr->data;
	return MAX2(pose->active_group-1, 0);
}

static void rna_Pose_active_bone_group_index_set(PointerRNA *ptr, int value)
{
	bPose *pose= (bPose*)ptr->data;
	pose->active_group= value+1;
}

static void rna_Pose_active_bone_group_index_range(PointerRNA *ptr, int *min, int *max)
{
	bPose *pose= (bPose*)ptr->data;

	*min= 0;
	*max= BLI_countlist(&pose->agroups)-1;
	*max= MAX2(0, *max);
}

void rna_pose_bgroup_name_index_get(PointerRNA *ptr, char *value, int index)
{
	bPose *pose= (bPose*)ptr->data;
	bActionGroup *grp;

	grp= BLI_findlink(&pose->agroups, index-1);

	if(grp) BLI_strncpy(value, grp->name, sizeof(grp->name));
	else BLI_strncpy(value, "", sizeof(grp->name)); // XXX if invalid pointer, won't this crash?
}

int rna_pose_bgroup_name_index_length(PointerRNA *ptr, int index)
{
	bPose *pose= (bPose*)ptr->data;
	bActionGroup *grp;

	grp= BLI_findlink(&pose->agroups, index-1);
	return (grp)? strlen(grp->name): 0;
}

void rna_pose_bgroup_name_index_set(PointerRNA *ptr, const char *value, short *index)
{
	bPose *pose= (bPose*)ptr->data;
	bActionGroup *grp;
	int a;
	
	for (a=1, grp=pose->agroups.first; grp; grp=grp->next, a++) {
		if (strcmp(grp->name, value) == 0) {
			*index= a;
			return;
		}
	}
	
	*index= 0;
}

void rna_pose_pgroup_name_set(PointerRNA *ptr, const char *value, char *result, int maxlen)
{
	bPose *pose= (bPose*)ptr->data;
	bActionGroup *grp;
	
	for (grp= pose->agroups.first; grp; grp= grp->next) {
		if (strcmp(grp->name, value) == 0) {
			BLI_strncpy(result, value, maxlen);
			return;
		}
	}
	
	BLI_strncpy(result, "", maxlen);
}

#else

static void rna_def_bone_group(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "BoneGroup", NULL);
	RNA_def_struct_sdna(srna, "bActionGroup");
	RNA_def_struct_ui_text(srna, "Bone Group", "Groups of Pose Channels (Bones).");

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_ui_text(prop, "Name", "");
	RNA_def_struct_name_property(srna, prop);
	
	// TODO: add some runtime-collections stuff to access grouped bones 
	
	// FIXME: this needs more work - probably a custom template?
	prop= RNA_def_property(srna, "custom_color", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "customCol");
	RNA_def_property_ui_text(prop, "Custom Color", "Index of custom color set.");
}

static void rna_def_pose_channel(BlenderRNA *brna)
{
	static EnumPropertyItem prop_rotmode_items[] = {
		{PCHAN_ROT_QUAT, "QUATERNION", 0, "Quaternion (WXYZ)", "No Gimbal Lock (default)"},
		{PCHAN_ROT_EUL, "EULER", 0, "Euler (XYZ)", "Prone to Gimbal Lock"},
		{0, NULL, 0, NULL, NULL}};
	
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "PoseChannel", NULL);
	RNA_def_struct_sdna(srna, "bPoseChannel");
	RNA_def_struct_ui_text(srna, "Pose Channel", "Channel defining pose data for a bone in a Pose.");
	RNA_def_struct_idproperties_func(srna, "rna_PoseChannel_idproperties");

	prop= RNA_def_property(srna, "constraints", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "Constraint");
	RNA_def_property_ui_text(prop, "Constraints", "Constraints that act on this PoseChannel."); 

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_string_funcs(prop, NULL, NULL, "rna_PoseChannel_name_set");
	RNA_def_property_ui_text(prop, "Name", "");
	RNA_def_struct_name_property(srna, prop);

	prop= RNA_def_property(srna, "has_ik", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_funcs(prop,  "rna_PoseChannel_has_ik_get", NULL);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Has IK", "Is part of an IK chain.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "ik_dof_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "ikflag", BONE_IK_NO_XDOF);
	RNA_def_property_ui_text(prop, "IK X DoF", "Allow movement around the X axis.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "ik_dof_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "ikflag", BONE_IK_NO_YDOF);
	RNA_def_property_ui_text(prop, "IK Y DoF", "Allow movement around the Y axis.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "ik_dof_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "ikflag", BONE_IK_NO_ZDOF);
	RNA_def_property_ui_text(prop, "IK Z DoF", "Allow movement around the Z axis.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "ik_limit_x", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ikflag", BONE_IK_XLIMIT);
	RNA_def_property_ui_text(prop, "IK X Limit", "Limit movement around the X axis.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "ik_limit_y", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ikflag", BONE_IK_YLIMIT);
	RNA_def_property_ui_text(prop, "IK Y Limit", "Limit movement around the Y axis.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "ik_limit_z", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "ikflag", BONE_IK_ZLIMIT);
	RNA_def_property_ui_text(prop, "IK Z Limit", "Limit movement around the Z axis.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");
	
	prop= RNA_def_property(srna, "selected", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "selectflag", BONE_SELECTED);
	RNA_def_property_ui_text(prop, "Selected", "");
	
		/* XXX note: bone groups are stored internally as bActionGroups :) - Aligorith */
	prop= RNA_def_property(srna, "bone_group_index", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "agrp_index");
	RNA_def_property_ui_text(prop, "Bone Group Index", "Bone Group this pose channel belongs to (0=no group).");

	prop= RNA_def_property(srna, "path_start_frame", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "pathsf");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Bone Paths Calculation Start Frame", "Starting frame of range of frames to use for Bone Path calculations.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "path_end_frame", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "pathef");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Bone Paths Calculation End Frame", "End frame of range of frames to use for Bone Path calculations.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "bone", PROP_POINTER, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "Bone");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Bone", "Bone associated with this Pose Channel.");

	prop= RNA_def_property(srna, "parent", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "PoseChannel");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Parent", "Parent of this pose channel.");

	prop= RNA_def_property(srna, "child", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "PoseChannel");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Child", "Child of this pose channel.");

	prop= RNA_def_property(srna, "location", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_float_sdna(prop, NULL, "loc");
	RNA_def_property_ui_text(prop, "Location", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "scale", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_float_sdna(prop, NULL, "size");
	RNA_def_property_ui_text(prop, "Scale", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "rotation", PROP_FLOAT, PROP_ROTATION);
	RNA_def_property_float_sdna(prop, NULL, "quat");
	RNA_def_property_ui_text(prop, "Rotation", "Rotation in Quaternions.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");
	
	prop= RNA_def_property(srna, "euler_rotation", PROP_FLOAT, PROP_ROTATION);
	RNA_def_property_float_sdna(prop, NULL, "eul");
	RNA_def_property_float_funcs(prop, "rna_PoseChannel_euler_rotation_get", "rna_PoseChannel_euler_rotation_set", NULL);
	RNA_def_property_ui_text(prop, "Rotation (Euler)", "Rotation in Eulers.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");
	
	prop= RNA_def_property(srna, "rotation_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "rotmode");
	RNA_def_property_enum_items(prop, prop_rotmode_items);
	RNA_def_property_ui_text(prop, "Rotation Mode", "");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	/* These three matrix properties await an implementation of the PROP_MATRIX subtype, which currently doesn't exist. */
	prop= RNA_def_property(srna, "channel_matrix", PROP_FLOAT, PROP_MATRIX);
	RNA_def_property_float_sdna(prop, NULL, "chan_mat");
	RNA_def_property_array(prop, 16);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Channel Matrix", "4x4 matrix, before constraints.");

	/* kaito says this should be not user-editable; I disagree; power users should be able to force this in python; he's the boss. */
	prop= RNA_def_property(srna, "pose_matrix", PROP_FLOAT, PROP_MATRIX);
	RNA_def_property_float_sdna(prop, NULL, "pose_mat");
	RNA_def_property_array(prop, 16);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE); 
	RNA_def_property_ui_text(prop, "Pose Matrix", "Final 4x4 matrix for this channel.");

	/*
	prop= RNA_def_property(srna, "constraint_inverse_matrix", PROP_FLOAT, PROP_MATRIX);
	RNA_def_property_struct_type(prop, "constinv");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Constraint Inverse Matrix", "4x4 matrix, defines transform from final position to unconstrained position.");
	*/
	
	prop= RNA_def_property(srna, "pose_head", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Pose Head Position", "Location of head of the channel's bone.");

	prop= RNA_def_property(srna, "pose_tail", PROP_FLOAT, PROP_VECTOR);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Pose Tail Position", "Location of tail of the channel's bone.");

	prop= RNA_def_property(srna, "ik_min_x", PROP_FLOAT, PROP_ROTATION);
	RNA_def_property_float_sdna(prop, NULL, "limitmin[0]");
	RNA_def_property_range(prop, -180.0f, 0.0f);
	RNA_def_property_ui_text(prop, "IK X Minimum", "Minimum angles for IK Limit");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "ik_max_x", PROP_FLOAT, PROP_ROTATION);
	RNA_def_property_float_sdna(prop, NULL, "limitmax[0]");
	RNA_def_property_range(prop, 0.0f, 180.0f);
	RNA_def_property_ui_text(prop, "IK X Maximum", "Maximum angles for IK Limit");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "ik_min_y", PROP_FLOAT, PROP_ROTATION);
	RNA_def_property_float_sdna(prop, NULL, "limitmin[1]");
	RNA_def_property_range(prop, -180.0f, 0.0f);
	RNA_def_property_ui_text(prop, "IK Y Minimum", "Minimum angles for IK Limit");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "ik_max_y", PROP_FLOAT, PROP_ROTATION);
	RNA_def_property_float_sdna(prop, NULL, "limitmax[1]");
	RNA_def_property_range(prop, 0.0f, 180.0f);
	RNA_def_property_ui_text(prop, "IK Y Maximum", "Maximum angles for IK Limit");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "ik_min_z", PROP_FLOAT, PROP_ROTATION);
	RNA_def_property_float_sdna(prop, NULL, "limitmin[2]");
	RNA_def_property_range(prop, -180.0f, 0.0f);
	RNA_def_property_ui_text(prop, "IK Z Minimum", "Minimum angles for IK Limit");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "ik_max_z", PROP_FLOAT, PROP_ROTATION);
	RNA_def_property_float_sdna(prop, NULL, "limitmax[2]");
	RNA_def_property_range(prop, 0.0f, 180.0f);
	RNA_def_property_ui_text(prop, "IK Z Maximum", "Maximum angles for IK Limit");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "ik_stiffness_x", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "stiffness[0]");
	RNA_def_property_range(prop, 0.0f, 0.99f);
	RNA_def_property_ui_text(prop, "IK X Stiffness", "IK stiffness around the X axis.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "ik_stiffness_y", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "stiffness[1]");
	RNA_def_property_range(prop, 0.0f, 0.99f);
	RNA_def_property_ui_text(prop, "IK Y Stiffness", "IK stiffness around the Y axis.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "ik_stiffness_z", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "stiffness[2]");
	RNA_def_property_range(prop, 0.0f, 0.99f);
	RNA_def_property_ui_text(prop, "IK Z Stiffness", "IK stiffness around the Z axis.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "ik_stretch", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "ikstretch");
	RNA_def_property_range(prop, 0.0f,1.0f);
	RNA_def_property_ui_text(prop, "IK Stretch", "Allow scaling of the bone for IK.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

	prop= RNA_def_property(srna, "custom", PROP_POINTER, PROP_NONE);
	RNA_def_property_ui_text(prop, "Custom Object", "Object that defines custom draw type for this bone.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE|ND_TRANSFORM, "rna_Pose_update");

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
}

static void rna_def_pose(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	
	/* struct definition */
	srna= RNA_def_struct(brna, "Pose", NULL);
	RNA_def_struct_sdna(srna, "bPose");
	RNA_def_struct_ui_text(srna, "Pose", "A collection of pose channels, including settings for animating bones.");

	/* pose channels */
	prop= RNA_def_property(srna, "pose_channels", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "chanbase", NULL);
	RNA_def_property_struct_type(prop, "PoseChannel");
	RNA_def_property_ui_text(prop, "Pose Channels", "Individual pose channels for the armature.");

	/* bone groups */
	prop= RNA_def_property(srna, "bone_groups", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "agroups", NULL);
	RNA_def_property_struct_type(prop, "BoneGroup");
	RNA_def_property_ui_text(prop, "Bone Groups", "Groups of the bones.");

	prop= RNA_def_property(srna, "active_bone_group", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "BoneGroup");
	RNA_def_property_pointer_funcs(prop, "rna_Pose_active_bone_group_get", "rna_Pose_active_bone_group_set", NULL);
	RNA_def_property_ui_text(prop, "Active Bone Group", "Bone groups of the pose.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE, "rna_Pose_update");

	prop= RNA_def_property(srna, "active_bone_group_index", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "active_group");
	RNA_def_property_int_funcs(prop, "rna_Pose_active_bone_group_index_get", "rna_Pose_active_bone_group_index_set", "rna_Pose_active_bone_group_index_range");
	RNA_def_property_ui_text(prop, "Active Bone Group Index", "Active index in bone groups array.");
	RNA_def_property_update(prop, NC_OBJECT|ND_POSE, "rna_Pose_update");
}

void RNA_def_pose(BlenderRNA *brna)
{
	rna_def_pose(brna);
	rna_def_pose_channel(brna);
	
	rna_def_bone_group(brna);
}

#endif
