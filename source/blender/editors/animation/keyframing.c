/* Testing code for 2.5 animation system 
 * Copyright 2009, Joshua Leung
 */
 
#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include <math.h>
#include <float.h>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_dynstr.h"

#include "DNA_anim_types.h"
#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_constraint_types.h"
#include "DNA_key_types.h"
#include "DNA_object_types.h"
#include "DNA_material_types.h"
#include "DNA_scene_types.h"
#include "DNA_userdef_types.h"
#include "DNA_windowmanager_types.h"

#include "BKE_animsys.h"
#include "BKE_action.h"
#include "BKE_constraint.h"
#include "BKE_fcurve.h"
#include "BKE_utildefines.h"
#include "BKE_context.h"
#include "BKE_report.h"
#include "BKE_key.h"
#include "BKE_material.h"

#include "ED_anim_api.h"
#include "ED_keyframing.h"
#include "ED_keyframes_edit.h"
#include "ED_screen.h"
#include "ED_util.h"

#include "UI_interface.h"

#include "WM_api.h"
#include "WM_types.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_types.h"

#include "anim_intern.h"

/* ******************************************* */
/* Animation Data Validation */

/* Get (or add relevant data to be able to do so) F-Curve from the Active Action, 
 * for the given Animation Data block. This assumes that all the destinations are valid.
 */
FCurve *verify_fcurve (ID *id, const char group[], const char rna_path[], const int array_index, short add)
{
	AnimData *adt;
	bAction *act;
	bActionGroup *grp;
	FCurve *fcu;
	
	/* sanity checks */
	if ELEM(NULL, id, rna_path)
		return NULL;
	
	/* init animdata if none available yet */
	adt= BKE_animdata_from_id(id);
	if ((adt == NULL) && (add))
		adt= BKE_id_add_animdata(id);
	if (adt == NULL) { 
		/* if still none (as not allowed to add, or ID doesn't have animdata for some reason) */
		return NULL;
	}
		
	/* init action if none available yet */
	// TODO: need some wizardry to handle NLA stuff correct
	if ((adt->action == NULL) && (add))
		adt->action= add_empty_action("Action");
	act= adt->action;
		
	/* try to find f-curve matching for this setting 
	 *	- add if not found and allowed to add one
	 *		TODO: add auto-grouping support? how this works will need to be resolved
	 */
	if (act)
		fcu= list_find_fcurve(&act->curves, rna_path, array_index);
	else
		fcu= NULL;
	
	if ((fcu == NULL) && (add)) {
		/* use default settings to make a F-Curve */
		fcu= MEM_callocN(sizeof(FCurve), "FCurve");
		
		fcu->flag = (FCURVE_VISIBLE|FCURVE_AUTO_HANDLES|FCURVE_SELECTED);
		if (act->curves.first==NULL) 
			fcu->flag |= FCURVE_ACTIVE;	/* first one added active */
			
		/* store path - make copy, and store that */
		fcu->rna_path= BLI_strdupn(rna_path, strlen(rna_path));
		fcu->array_index= array_index;
		
		/* if a group name has been provided, try to add or find a group, then add F-Curve to it */
		if (group) {
			/* try to find group */
			grp= action_groups_find_named(act, group);
			
			/* no matching groups, so add one */
			if (grp == NULL) {
				/* Add a new group, and make it active */
				grp= MEM_callocN(sizeof(bActionGroup), "bActionGroup");
				
				grp->flag = AGRP_SELECTED;
				BLI_snprintf(grp->name, 64, group);
				
				BLI_addtail(&act->groups, grp);
				BLI_uniquename(&act->groups, grp, "Group", offsetof(bActionGroup, name), 64);
			}
			
			/* add F-Curve to group */
			action_groups_add_channel(act, grp, fcu);
		}
		else {
			/* just add F-Curve to end of Action's list */
			BLI_addtail(&act->curves, fcu);
		}
	}
	
	/* return the F-Curve */
	return fcu;
}

/* ************************************************** */
/* KEYFRAME INSERTION */

/* -------------- BezTriple Insertion -------------------- */

/* threshold for inserting keyframes - threshold here should be good enough for now, but should become userpref */
#define BEZT_INSERT_THRESH 	0.00001f

/* Binary search algorithm for finding where to insert BezTriple. (for use by insert_bezt_icu)
 * Returns the index to insert at (data already at that index will be offset if replace is 0)
 */
static int binarysearch_bezt_index (BezTriple array[], float frame, int arraylen, short *replace)
{
	int start=0, end=arraylen;
	int loopbreaker= 0, maxloop= arraylen * 2;
	
	/* initialise replace-flag first */
	*replace= 0;
	
	/* sneaky optimisations (don't go through searching process if...):
	 *	- keyframe to be added is to be added out of current bounds
	 *	- keyframe to be added would replace one of the existing ones on bounds
	 */
	if ((arraylen <= 0) || (array == NULL)) {
		printf("Warning: binarysearch_bezt_index() encountered invalid array \n");
		return 0;
	}
	else {
		/* check whether to add before/after/on */
		float framenum;
		
		/* 'First' Keyframe (when only one keyframe, this case is used) */
		framenum= array[0].vec[1][0];
		if (IS_EQT(frame, framenum, BEZT_INSERT_THRESH)) {
			*replace = 1;
			return 0;
		}
		else if (frame < framenum)
			return 0;
			
		/* 'Last' Keyframe */
		framenum= array[(arraylen-1)].vec[1][0];
		if (IS_EQT(frame, framenum, BEZT_INSERT_THRESH)) {
			*replace= 1;
			return (arraylen - 1);
		}
		else if (frame > framenum)
			return arraylen;
	}
	
	
	/* most of the time, this loop is just to find where to put it
	 * 'loopbreaker' is just here to prevent infinite loops 
	 */
	for (loopbreaker=0; (start <= end) && (loopbreaker < maxloop); loopbreaker++) {
		/* compute and get midpoint */
		int mid = start + ((end - start) / 2);	/* we calculate the midpoint this way to avoid int overflows... */
		float midfra= array[mid].vec[1][0];
		
		/* check if exactly equal to midpoint */
		if (IS_EQT(frame, midfra, BEZT_INSERT_THRESH)) {
			*replace = 1;
			return mid;
		}
		
		/* repeat in upper/lower half */
		if (frame > midfra)
			start= mid + 1;
		else if (frame < midfra)
			end= mid - 1;
	}
	
	/* print error if loop-limit exceeded */
	if (loopbreaker == (maxloop-1)) {
		printf("Error: binarysearch_bezt_index() was taking too long \n");
		
		// include debug info 
		printf("\tround = %d: start = %d, end = %d, arraylen = %d \n", loopbreaker, start, end, arraylen);
	}
	
	/* not found, so return where to place it */
	return start;
}

/* This function adds a given BezTriple to an F-Curve. It will allocate 
 * memory for the array if needed, and will insert the BezTriple into a
 * suitable place in chronological order.
 * 
 * NOTE: any recalculate of the F-Curve that needs to be done will need to 
 * 		be done by the caller.
 */
int insert_bezt_fcurve (FCurve *fcu, BezTriple *bezt)
{
	BezTriple *newb;
	int i= 0;
	
	if (fcu->bezt) {
		short replace = -1;
		i = binarysearch_bezt_index(fcu->bezt, bezt->vec[1][0], fcu->totvert, &replace);
		
		if (replace) {			
			/* sanity check: 'i' may in rare cases exceed arraylen */
			// FIXME: do not overwrite handletype if just replacing...?
			if ((i >= 0) && (i < fcu->totvert))
				*(fcu->bezt + i) = *bezt;
		}
		else {
			/* add new */
			newb= MEM_callocN((fcu->totvert+1)*sizeof(BezTriple), "beztriple");
			
			/* add the beztriples that should occur before the beztriple to be pasted (originally in ei->icu) */
			if (i > 0)
				memcpy(newb, fcu->bezt, i*sizeof(BezTriple));
			
			/* add beztriple to paste at index i */
			*(newb + i)= *bezt;
			
			/* add the beztriples that occur after the beztriple to be pasted (originally in icu) */
			if (i < fcu->totvert) 
				memcpy(newb+i+1, fcu->bezt+i, (fcu->totvert-i)*sizeof(BezTriple));
			
			/* replace (+ free) old with new */
			MEM_freeN(fcu->bezt);
			fcu->bezt= newb;
			
			fcu->totvert++;
		}
	}
	else {
		// TODO: need to check for old sample-data now...
		fcu->bezt= MEM_callocN(sizeof(BezTriple), "beztriple");
		*(fcu->bezt)= *bezt;
		fcu->totvert= 1;
	}
	
	
	/* we need to return the index, so that some tools which do post-processing can 
	 * detect where we added the BezTriple in the array
	 */
	return i;
}

/* This function is a wrapper for insert_bezt_icu, and should be used when
 * adding a new keyframe to a curve, when the keyframe doesn't exist anywhere
 * else yet. 
 * 
 * 'fast' - is only for the python API where importing BVH's would take an extreamly long time.
 */
void insert_vert_fcurve (FCurve *fcu, float x, float y, short fast)
{
	BezTriple beztr;
	int a;
	
	/* set all three points, for nicer start position */
	memset(&beztr, 0, sizeof(BezTriple));
	beztr.vec[0][0]= x; 
	beztr.vec[0][1]= y;
	beztr.vec[1][0]= x;
	beztr.vec[1][1]= y;
	beztr.vec[2][0]= x;
	beztr.vec[2][1]= y;
	beztr.ipo= U.ipo_new; /* use default interpolation mode here... */
	beztr.f1= beztr.f2= beztr.f3= SELECT;
	beztr.h1= beztr.h2= HD_AUTO; // XXX what about when we replace an old one?
	
	/* add temp beztriple to keyframes */
	a= insert_bezt_fcurve(fcu, &beztr);
	
	/* what if 'a' is a negative index? 
	 * for now, just exit to prevent any segfaults
	 */
	if (a < 0) return;
	
	/* don't recalculate handles if fast is set
	 *	- this is a hack to make importers faster
	 *	- we may calculate twice (see editipo_changed(), due to autohandle needing two calculations)
	 */
	if (!fast) calchandles_fcurve(fcu);
	
	/* set handletype and interpolation */
	if (fcu->totvert > 2) {
		BezTriple *bezt= (fcu->bezt + a);
		char h1, h2;
		
		/* set handles (autohandles by default) */
		h1= h2= HD_AUTO;
		
		if (a > 0) h1= (bezt-1)->h2;
		if (a < fcu->totvert-1) h2= (bezt+1)->h1;
		
		bezt->h1= h1;
		bezt->h2= h2;
		
		/* set interpolation from previous (if available) */
		if (a > 0) bezt->ipo= (bezt-1)->ipo;
		else if (a < fcu->totvert-1) bezt->ipo= (bezt+1)->ipo;
			
		/* don't recalculate handles if fast is set
		 *	- this is a hack to make importers faster
		 *	- we may calculate twice (see editipo_changed(), due to autohandle needing two calculations)
		 */
		if (!fast) calchandles_fcurve(fcu);
	}
}

/* -------------- 'Smarter' Keyframing Functions -------------------- */
/* return codes for new_key_needed */
enum {
	KEYNEEDED_DONTADD = 0,
	KEYNEEDED_JUSTADD,
	KEYNEEDED_DELPREV,
	KEYNEEDED_DELNEXT
} eKeyNeededStatus;

/* This helper function determines whether a new keyframe is needed */
/* Cases where keyframes should not be added:
 *	1. Keyframe to be added bewteen two keyframes with similar values
 *	2. Keyframe to be added on frame where two keyframes are already situated
 *	3. Keyframe lies at point that intersects the linear line between two keyframes
 */
static short new_key_needed (FCurve *fcu, float cFrame, float nValue) 
{
	BezTriple *bezt=NULL, *prev=NULL;
	int totCount, i;
	float valA = 0.0f, valB = 0.0f;
	
	/* safety checking */
	if (fcu == NULL) return KEYNEEDED_JUSTADD;
	totCount= fcu->totvert;
	if (totCount == 0) return KEYNEEDED_JUSTADD;
	
	/* loop through checking if any are the same */
	bezt= fcu->bezt;
	for (i=0; i<totCount; i++) {
		float prevPosi=0.0f, prevVal=0.0f;
		float beztPosi=0.0f, beztVal=0.0f;
			
		/* get current time+value */	
		beztPosi= bezt->vec[1][0];
		beztVal= bezt->vec[1][1];
			
		if (prev) {
			/* there is a keyframe before the one currently being examined */		
			
			/* get previous time+value */
			prevPosi= prev->vec[1][0];
			prevVal= prev->vec[1][1];
			
			/* keyframe to be added at point where there are already two similar points? */
			if (IS_EQ(prevPosi, cFrame) && IS_EQ(beztPosi, cFrame) && IS_EQ(beztPosi, prevPosi)) {
				return KEYNEEDED_DONTADD;
			}
			
			/* keyframe between prev+current points ? */
			if ((prevPosi <= cFrame) && (cFrame <= beztPosi)) {
				/* is the value of keyframe to be added the same as keyframes on either side ? */
				if (IS_EQ(prevVal, nValue) && IS_EQ(beztVal, nValue) && IS_EQ(prevVal, beztVal)) {
					return KEYNEEDED_DONTADD;
				}
				else {
					float realVal;
					
					/* get real value of curve at that point */
					realVal= evaluate_fcurve(fcu, cFrame);
					
					/* compare whether it's the same as proposed */
					if (IS_EQ(realVal, nValue)) 
						return KEYNEEDED_DONTADD;
					else 
						return KEYNEEDED_JUSTADD;
				}
			}
			
			/* new keyframe before prev beztriple? */
			if (cFrame < prevPosi) {
				/* A new keyframe will be added. However, whether the previous beztriple
				 * stays around or not depends on whether the values of previous/current
				 * beztriples and new keyframe are the same.
				 */
				if (IS_EQ(prevVal, nValue) && IS_EQ(beztVal, nValue) && IS_EQ(prevVal, beztVal))
					return KEYNEEDED_DELNEXT;
				else 
					return KEYNEEDED_JUSTADD;
			}
		}
		else {
			/* just add a keyframe if there's only one keyframe 
			 * and the new one occurs before the exisiting one does.
			 */
			if ((cFrame < beztPosi) && (totCount==1))
				return KEYNEEDED_JUSTADD;
		}
		
		/* continue. frame to do not yet passed (or other conditions not met) */
		if (i < (totCount-1)) {
			prev= bezt;
			bezt++;
		}
		else
			break;
	}
	
	/* Frame in which to add a new-keyframe occurs after all other keys
	 * -> If there are at least two existing keyframes, then if the values of the
	 *	 last two keyframes and the new-keyframe match, the last existing keyframe
	 *	 gets deleted as it is no longer required.
	 * -> Otherwise, a keyframe is just added. 1.0 is added so that fake-2nd-to-last
	 *	 keyframe is not equal to last keyframe.
	 */
	bezt= (fcu->bezt + (fcu->totvert - 1));
	valA= bezt->vec[1][1];
	
	if (prev)
		valB= prev->vec[1][1];
	else 
		valB= bezt->vec[1][1] + 1.0f; 
		
	if (IS_EQ(valA, nValue) && IS_EQ(valA, valB)) 
		return KEYNEEDED_DELPREV;
	else 
		return KEYNEEDED_JUSTADD;
}

/* ------------------ RNA Data-Access Functions ------------------ */

/* Try to read value using RNA-properties obtained already */
static float setting_get_rna_value (PointerRNA *ptr, PropertyRNA *prop, int index)
{
	float value= 0.0f;
	
	switch (RNA_property_type(ptr, prop)) {
		case PROP_BOOLEAN:
			if (RNA_property_array_length(ptr, prop))
				value= (float)RNA_property_boolean_get_index(ptr, prop, index);
			else
				value= (float)RNA_property_boolean_get(ptr, prop);
			break;
		case PROP_INT:
			if (RNA_property_array_length(ptr, prop))
				value= (float)RNA_property_int_get_index(ptr, prop, index);
			else
				value= (float)RNA_property_int_get(ptr, prop);
			break;
		case PROP_FLOAT:
			if (RNA_property_array_length(ptr, prop))
				value= RNA_property_float_get_index(ptr, prop, index);
			else
				value= RNA_property_float_get(ptr, prop);
			break;
		case PROP_ENUM:
			value= (float)RNA_property_enum_get(ptr, prop);
			break;
		default:
			break;
	}
	
	return value;
}

/* ------------------ 'Visual' Keyframing Functions ------------------ */

/* internal status codes for visualkey_can_use */
enum {
	VISUALKEY_NONE = 0,
	VISUALKEY_LOC,
	VISUALKEY_ROT,
};

/* This helper function determines if visual-keyframing should be used when  
 * inserting keyframes for the given channel. As visual-keyframing only works
 * on Object and Pose-Channel blocks, this should only get called for those 
 * blocktypes, when using "standard" keying but 'Visual Keying' option in Auto-Keying 
 * settings is on.
 */
static short visualkey_can_use (PointerRNA *ptr, PropertyRNA *prop)
{
	bConstraint *con= NULL;
	short searchtype= VISUALKEY_NONE;
	char *identifier= NULL;
	
	/* validate data */
	// TODO: this check is probably not needed, but it won't hurt
	if (ELEM3(NULL, ptr, ptr->data, prop))
		return 0;
		
	/* get first constraint and determine type of keyframe constraints to check for 
	 * 	- constraints can be on either Objects or PoseChannels, so we only check if the
	 *	  ptr->type is RNA_Object or RNA_PoseChannel, which are the RNA wrapping-info for
	 *  	  those structs, allowing us to identify the owner of the data 
	 */
	if (ptr->type == &RNA_Object) {
		/* Object */
		Object *ob= (Object *)ptr->data;
		
		con= ob->constraints.first;
		identifier= (char *)RNA_property_identifier(ptr, prop);
	}
	else if (ptr->type == &RNA_PoseChannel) {
		/* Pose Channel */
		bPoseChannel *pchan= (bPoseChannel *)ptr->data;
		
		con= pchan->constraints.first;
		identifier= (char *)RNA_property_identifier(ptr, prop);
	}
	
	/* check if any data to search using */
	if (ELEM(NULL, con, identifier))
		return 0;
		
	/* location or rotation identifiers only... */
	if (strstr(identifier, "location"))
		searchtype= VISUALKEY_LOC;
	else if (strstr(identifier, "rotation"))
		searchtype= VISUALKEY_ROT;
	else {
		printf("visualkey_can_use() failed: identifier - '%s' \n", identifier);
		return 0;
	}
	
	
	/* only search if a searchtype and initial constraint are available */
	if (searchtype && con) {
		for (; con; con= con->next) {
			/* only consider constraint if it is not disabled, and has influence */
			if (con->flag & CONSTRAINT_DISABLE) continue;
			if (con->enforce == 0.0f) continue;
			
			/* some constraints may alter these transforms */
			switch (con->type) {
				/* multi-transform constraints */
				case CONSTRAINT_TYPE_CHILDOF:
					return 1;
				case CONSTRAINT_TYPE_TRANSFORM:
					return 1;
				case CONSTRAINT_TYPE_FOLLOWPATH:
					return 1;
				case CONSTRAINT_TYPE_KINEMATIC:
					return 1;
					
				/* single-transform constraits  */
				case CONSTRAINT_TYPE_TRACKTO:
					if (searchtype==VISUALKEY_ROT) return 1;
					break;
				case CONSTRAINT_TYPE_ROTLIMIT:
					if (searchtype==VISUALKEY_ROT) return 1;
					break;
				case CONSTRAINT_TYPE_LOCLIMIT:
					if (searchtype==VISUALKEY_LOC) return 1;
					break;
				case CONSTRAINT_TYPE_ROTLIKE:
					if (searchtype==VISUALKEY_ROT) return 1;
					break;
				case CONSTRAINT_TYPE_DISTLIMIT:
					if (searchtype==VISUALKEY_LOC) return 1;
					break;
				case CONSTRAINT_TYPE_LOCLIKE:
					if (searchtype==VISUALKEY_LOC) return 1;
					break;
				case CONSTRAINT_TYPE_LOCKTRACK:
					if (searchtype==VISUALKEY_ROT) return 1;
					break;
				case CONSTRAINT_TYPE_MINMAX:
					if (searchtype==VISUALKEY_LOC) return 1;
					break;
				
				default:
					break;
			}
		}
	}
	
	/* when some condition is met, this function returns, so here it can be 0 */
	return 0;
}

/* This helper function extracts the value to use for visual-keyframing 
 * In the event that it is not possible to perform visual keying, try to fall-back
 * to using the default method. Assumes that all data it has been passed is valid.
 */
static float visualkey_get_value (PointerRNA *ptr, PropertyRNA *prop, int array_index)
{
	char *identifier= (char *)RNA_property_identifier(ptr, prop);
	
	/* handle for Objects or PoseChannels only 
	 * 	- constraints can be on either Objects or PoseChannels, so we only check if the
	 *	  ptr->type is RNA_Object or RNA_PoseChannel, which are the RNA wrapping-info for
	 *  	  those structs, allowing us to identify the owner of the data 
	 *	- assume that array_index will be sane
	 */
	if (ptr->type == &RNA_Object) {
		Object *ob= (Object *)ptr->data;
		
		/* parented objects are not supported, as the effects of the parent
		 * are included in the matrix, which kindof beats the point
		 */
		if (ob->parent == NULL) {
			/* only Location or Rotation keyframes are supported now */
			if (strstr(identifier, "location")) {
				return ob->obmat[3][array_index];
			}
			else if (strstr(identifier, "rotation")) {
				float eul[3];
				
				Mat4ToEul(ob->obmat, eul);
				return eul[array_index];
			}
		}
	}
	else if (ptr->type == &RNA_PoseChannel) {
		Object *ob= (Object *)ptr->id.data; /* we assume that this is always set, and is an object */
		bPoseChannel *pchan= (bPoseChannel *)ptr->data;
		float tmat[4][4];
		
		/* Although it is not strictly required for this particular space conversion, 
		 * arg1 must not be null, as there is a null check for the other conversions to
		 * be safe. Therefore, the active object is passed here, and in many cases, this
		 * will be what owns the pose-channel that is getting this anyway.
		 */
		Mat4CpyMat4(tmat, pchan->pose_mat);
		constraint_mat_convertspace(ob, pchan, tmat, CONSTRAINT_SPACE_POSE, CONSTRAINT_SPACE_LOCAL);
		
		/* Loc, Rot/Quat keyframes are supported... */
		if (strstr(identifier, "location")) {
			/* only use for non-connected bones */
			if ((pchan->bone->parent) && !(pchan->bone->flag & BONE_CONNECTED))
				return tmat[3][array_index];
			else if (pchan->bone->parent == NULL)
				return tmat[3][array_index];
		}
		else if (strstr(identifier, "euler_rotation")) {
			float eul[3];
			
			/* euler-rotation test before standard rotation, as standard rotation does quats */
			Mat4ToEul(tmat, eul);
			return eul[array_index];
		}
		else if (strstr(identifier, "rotation")) {
			float trimat[3][3], quat[4];
			
			Mat3CpyMat4(trimat, tmat);
			Mat3ToQuat_is_ok(trimat, quat);
			
			return quat[array_index];
		}
	}
	
	/* as the function hasn't returned yet, read value from system in the default way */
	return setting_get_rna_value(ptr, prop, array_index);
}

/* ------------------------- Insert Key API ------------------------- */

/* Main Keyframing API call:
 *	Use this when validation of necessary animation data isn't necessary as it
 *	already exists. It will insert a keyframe using the current value being keyframed.
 *	
 *	The flag argument is used for special settings that alter the behaviour of
 *	the keyframe insertion. These include the 'visual' keyframing modes, quick refresh,
 *	and extra keyframe filtering.
 */
short insertkey (ID *id, const char group[], const char rna_path[], int array_index, float cfra, short flag)
{	
	PointerRNA id_ptr, ptr;
	PropertyRNA *prop;
	FCurve *fcu;
	
	/* validate pointer first - exit if failure */
	RNA_id_pointer_create(id, &id_ptr);
	if ((RNA_path_resolve(&id_ptr, rna_path, &ptr, &prop) == 0) || (prop == NULL)) {
		printf("Insert Key: Could not insert keyframe, as RNA Path is invalid for the given ID (ID = %s, Path = %s)\n", id->name, rna_path);
		return 0;
	}
	
	/* get F-Curve */
	fcu= verify_fcurve(id, group, rna_path, array_index, 1);
	
	/* only continue if we have an F-Curve to add keyframe to */
	if (fcu) {
		float curval= 0.0f;
		
		/* set additional flags for the F-Curve (i.e. only integer values) */
		if (RNA_property_type(&ptr, prop) != PROP_FLOAT)
			fcu->flag |= FCURVE_INT_VALUES;
		
		/* apply special time tweaking */
			// XXX check on this stuff...
		if (GS(id->name) == ID_OB) {
			//Object *ob= (Object *)id;
			
			/* apply NLA-scaling (if applicable) */
			//cfra= get_action_frame(ob, cfra);
			
			/* ancient time-offset cruft */
			//if ( (ob->ipoflag & OB_OFFS_OB) && (give_timeoffset(ob)) ) {
			//	/* actually frametofloat calc again! */
			//	cfra-= give_timeoffset(ob)*scene->r.framelen;
			//}
		}
		
		/* obtain value to give keyframe */
		if ( (flag & INSERTKEY_MATRIX) && 
			 (visualkey_can_use(&ptr, prop)) ) 
		{
			/* visual-keying is only available for object and pchan datablocks, as 
			 * it works by keyframing using a value extracted from the final matrix 
			 * instead of using the kt system to extract a value.
			 */
			curval= visualkey_get_value(&ptr, prop, array_index);
		}
		else {
			/* read value from system */
			curval= setting_get_rna_value(&ptr, prop, array_index);
		}
		
		/* only insert keyframes where they are needed */
		if (flag & INSERTKEY_NEEDED) {
			short insert_mode;
			
			/* check whether this curve really needs a new keyframe */
			insert_mode= new_key_needed(fcu, cfra, curval);
			
			/* insert new keyframe at current frame */
			if (insert_mode)
				insert_vert_fcurve(fcu, cfra, curval, (flag & INSERTKEY_FAST));
			
			/* delete keyframe immediately before/after newly added */
			switch (insert_mode) {
				case KEYNEEDED_DELPREV:
					delete_fcurve_key(fcu, fcu->totvert-2, 1);
					break;
				case KEYNEEDED_DELNEXT:
					delete_fcurve_key(fcu, 1, 1);
					break;
			}
			
			/* only return success if keyframe added */
			if (insert_mode)
				return 1;
		}
		else {
			/* just insert keyframe */
			insert_vert_fcurve(fcu, cfra, curval, (flag & INSERTKEY_FAST));
			
			/* return success */
			return 1;
		}
	}
	
	/* return failure */
	return 0;
}

/* ************************************************** */
/* KEYFRAME DELETION */

/* Main Keyframing API call:
 *	Use this when validation of necessary animation data isn't necessary as it
 *	already exists. It will delete a keyframe at the current frame.
 *	
 *	The flag argument is used for special settings that alter the behaviour of
 *	the keyframe deletion. These include the quick refresh options.
 */
short deletekey (ID *id, const char group[], const char rna_path[], int array_index, float cfra, short flag)
{
	AnimData *adt;
	FCurve *fcu;
	
	/* get F-Curve
	 * Note: here is one of the places where we don't want new Action + F-Curve added!
	 * 		so 'add' var must be 0
	 */
	/* we don't check the validity of the path here yet, but it should be ok... */
	fcu= verify_fcurve(id, group, rna_path, array_index, 0);
	adt= BKE_animdata_from_id(id);
	
	/* only continue if we have an F-Curve to remove keyframes from */
	if (adt && adt->action && fcu) {
		bAction *act= adt->action;
		short found = -1;
		int i;
		
		/* apply special time tweaking */
		if (GS(id->name) == ID_OB) {
			//Object *ob= (Object *)id;
			
			/* apply NLA-scaling (if applicable) */
			//	cfra= get_action_frame(ob, cfra);
			
			/* ancient time-offset cruft */
			//if ( (ob->ipoflag & OB_OFFS_OB) && (give_timeoffset(ob)) ) {
			//	/* actually frametofloat calc again! */
			//	cfra-= give_timeoffset(ob)*scene->r.framelen;
			//}
		}
		
		/* try to find index of beztriple to get rid of */
		i = binarysearch_bezt_index(fcu->bezt, cfra, fcu->totvert, &found);
		if (found) {			
			/* delete the key at the index (will sanity check + do recalc afterwards) */
			delete_fcurve_key(fcu, i, 1);
			
			/* Only delete curve too if there are no points (we don't need to check for drivers, as they're kept separate) */
			if (fcu->totvert == 0) {
				BLI_remlink(&act->curves, fcu);
				free_fcurve(fcu);
			}
			
			/* return success */
			return 1;
		}
	}
	
	/* return failure */
	return 0;
}

/* ******************************************* */
/* KEYFRAME MODIFICATION */

/* mode for commonkey_modifykey */
enum {
	COMMONKEY_MODE_INSERT = 0,
	COMMONKEY_MODE_DELETE,
} eCommonModifyKey_Modes;

/* Polling callback for use with ANIM_*_keyframe() operators
 * This is based on the standard ED_operator_areaactive callback,
 * except that it does special checks for a few spacetypes too...
 */
static int modify_key_op_poll(bContext *C)
{
	ScrArea *sa= CTX_wm_area(C);
	Scene *scene= CTX_data_scene(C);
	
	/* if no area or active scene */
	if (ELEM(NULL, sa, scene)) 
		return 0;
	
	/* if Outliner, only allow in DataBlocks view */
	if (sa->spacetype == SPACE_OUTLINER) {
		SpaceOops *so= (SpaceOops *)CTX_wm_space_data(C);
		
		if ((so->outlinevis != SO_DATABLOCKS))
			return 0;
	}
	
	/* TODO: checks for other space types can be added here */
	
	/* should be fine */
	return 1;
}

/* Insert Key Operator ------------------------ */

static int insert_key_exec (bContext *C, wmOperator *op)
{
	ListBase dsources = {NULL, NULL};
	Scene *scene= CTX_data_scene(C);
	KeyingSet *ks= NULL;
	int type= RNA_int_get(op->ptr, "type");
	float cfra= (float)CFRA; // XXX for now, don't bother about all the yucky offset crap
	short success;
	
	/* type is the Keying Set the user specified to use when calling the operator:
	 *	- type == 0: use scene's active Keying Set
	 *	- type > 0: use a user-defined Keying Set from the active scene
	 *	- type < 0: use a builtin Keying Set
	 */
	if (type == 0) 
		type= scene->active_keyingset;
	if (type > 0)
		ks= BLI_findlink(&scene->keyingsets, scene->active_keyingset-1);
	else
		ks= BLI_findlink(&builtin_keyingsets, -type-1);
		
	/* report failures */
	if (ks == NULL) {
		BKE_report(op->reports, RPT_ERROR, "No active Keying Set");
		return OPERATOR_CANCELLED;
	}
	
	/* get context info for relative Keying Sets */
	if ((ks->flag & KEYINGSET_ABSOLUTE) == 0) {
		/* exit if no suitable data obtained */
		if (modifykey_get_context_data(C, &dsources, ks) == 0) {
			BKE_report(op->reports, RPT_ERROR, "No suitable context info for active Keying Set");
			return OPERATOR_CANCELLED;
		}
	}
	
	/* try to insert keyframes for the channels specified by KeyingSet */
	success= modify_keyframes(C, &dsources, ks, MODIFYKEY_MODE_INSERT, cfra);
	printf("KeyingSet '%s' - Successfully added %d Keyframes \n", ks->name, success);
	
	/* report failure? */
	if (success == 0)
		BKE_report(op->reports, RPT_WARNING, "Keying Set failed to insert any keyframes");
	
	/* free temp context-data if available */
	if (dsources.first) {
		/* we assume that there is no extra data that needs to be freed from here... */
		BLI_freelistN(&dsources);
	}
	
	/* send updates */
	ED_anim_dag_flush_update(C);	
	
	/* for now, only send ND_KEYS for KeyingSets */
	WM_event_add_notifier(C, ND_KEYS, NULL);
	
	return OPERATOR_FINISHED;
}

void ANIM_OT_insert_keyframe (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Insert Keyframe";
	ot->idname= "ANIM_OT_insert_keyframe";
	
	/* callbacks */
	ot->exec= insert_key_exec; 
	ot->poll= modify_key_op_poll;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* settings */
	RNA_def_int(ot->srna, "type", 0, INT_MIN, INT_MAX, "Keying Set Number", "Index (determined internally) of the Keying Set to use", 0, 1);
}

/* Insert Key Operator (With Menu) ------------------------ */

/* XXX 
 * This operator pops up a menu which sets gets the index of the keyingset to use,
 * setting the global settings, and calling the insert-keyframe operator using these
 * settings
 */

static int insert_key_menu_invoke (bContext *C, wmOperator *op, wmEvent *event)
{
	Scene *scene= CTX_data_scene(C);
	KeyingSet *ks;
	uiMenuItem *head;
	int i = 0;
	
	head= uiPupMenuBegin("Insert Keyframe", 0);
	
	/* active Keying Set */
	uiMenuItemIntO(head, "Active Keying Set", 0, "ANIM_OT_insert_keyframe_menu", "type", i++);
	uiMenuSeparator(head);
	
	/* user-defined Keying Sets 
	 *	- these are listed in the order in which they were defined for the active scene
	 */
	if (scene->keyingsets.first) {
		for (ks= scene->keyingsets.first; ks; ks= ks->next)
			uiMenuItemIntO(head, ks->name, 0, "ANIM_OT_insert_keyframe_menu", "type", i++);
		uiMenuSeparator(head);
	}
	
	/* builtin Keying Sets */
	// XXX polling the entire list may lag
	i= -1;
	for (ks= builtin_keyingsets.first; ks; ks= ks->next) {
		/* only show KeyingSet if context is suitable */
		if (keyingset_context_ok_poll(C, ks)) {
			uiMenuItemIntO(head, ks->name, 0, "ANIM_OT_insert_keyframe_menu", "type", i--);
		}
	}
	
	uiPupMenuEnd(C, head);
	
	return OPERATOR_CANCELLED;
}
 
void ANIM_OT_insert_keyframe_menu (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Insert Keyframe";
	ot->idname= "ANIM_OT_insert_keyframe_menu";
	
	/* callbacks */
	ot->invoke= insert_key_menu_invoke;
	ot->exec= insert_key_exec; 
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* properties
	 *	- NOTE: here the type is int not enum, since many of the indicies here are determined dynamically
	 */
	RNA_def_int(ot->srna, "type", 0, INT_MIN, INT_MAX, "Keying Set Number", "Index (determined internally) of the Keying Set to use", 0, 1);
}

/* Delete Key Operator ------------------------ */

static int delete_key_exec (bContext *C, wmOperator *op)
{
	ListBase dsources = {NULL, NULL};
	Scene *scene= CTX_data_scene(C);
	KeyingSet *ks= NULL;	
	int type= RNA_int_get(op->ptr, "type");
	float cfra= (float)CFRA; // XXX for now, don't bother about all the yucky offset crap
	short success;
	
	/* type is the Keying Set the user specified to use when calling the operator:
	 *	- type == 0: use scene's active Keying Set
	 *	- type > 0: use a user-defined Keying Set from the active scene
	 *	- type < 0: use a builtin Keying Set
	 */
	if (type == 0) 
		type= scene->active_keyingset;
	if (type > 0)
		ks= BLI_findlink(&scene->keyingsets, scene->active_keyingset-1);
	else
		ks= BLI_findlink(&builtin_keyingsets, -type-1);
	
	/* report failure */
	if (ks == NULL) {
		BKE_report(op->reports, RPT_ERROR, "No active Keying Set");
		return OPERATOR_CANCELLED;
	}
	
	/* get context info for relative Keying Sets */
	if ((ks->flag & KEYINGSET_ABSOLUTE) == 0) {
		/* exit if no suitable data obtained */
		if (modifykey_get_context_data(C, &dsources, ks) == 0) {
			BKE_report(op->reports, RPT_ERROR, "No suitable context info for active Keying Set");
			return OPERATOR_CANCELLED;
		}
	}
	
	/* try to insert keyframes for the channels specified by KeyingSet */
	success= modify_keyframes(C, &dsources, ks, MODIFYKEY_MODE_DELETE, cfra);
	printf("KeyingSet '%s' - Successfully removed %d Keyframes \n", ks->name, success);
	
	/* report failure? */
	if (success == 0)
		BKE_report(op->reports, RPT_WARNING, "Keying Set failed to remove any keyframes");
	
	/* free temp context-data if available */
	if (dsources.first) {
		/* we assume that there is no extra data that needs to be freed from here... */
		BLI_freelistN(&dsources);
	}
	
	/* send updates */
	ED_anim_dag_flush_update(C);	
	
	/* for now, only send ND_KEYS for KeyingSets */
	WM_event_add_notifier(C, ND_KEYS, NULL);
	
	return OPERATOR_FINISHED;
}

void ANIM_OT_delete_keyframe (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Delete Keyframe";
	ot->idname= "ANIM_OT_delete_keyframe";
	
	/* callbacks */
	ot->exec= delete_key_exec; 
	ot->poll= modify_key_op_poll;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* properties
	 *	- NOTE: here the type is int not enum, since many of the indicies here are determined dynamically
	 */
	RNA_def_int(ot->srna, "type", 0, INT_MIN, INT_MAX, "Keying Set Number", "Index (determined internally) of the Keying Set to use", 0, 1);
}

/* Delete Key Operator ------------------------ */

/* XXX WARNING:
 * This is currently just a basic operator, which work in 3d-view context on objects only. 
 * Should this be kept? It does have advantages over a version which requires selecting a keyingset to use...
 * -- Joshua Leung, Jan 2009
 */
 
static int delete_key_old_exec (bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	float cfra= (float)CFRA; // XXX for now, don't bother about all the yucky offset crap
	
	// XXX more comprehensive tests will be needed
	CTX_DATA_BEGIN(C, Base*, base, selected_bases) 
	{
		Object *ob= base->object;
		ID *id= (ID *)ob;
		FCurve *fcu, *fcn;
		short success= 0;
		
		/* loop through all curves in animdata and delete keys on this frame */
		if (ob->adt) {
			AnimData *adt= ob->adt;
			bAction *act= adt->action;
			
			for (fcu= act->curves.first; fcu; fcu= fcn) {
				fcn= fcu->next;
				success+= deletekey(id, NULL, fcu->rna_path, fcu->array_index, cfra, 0);
			}
		}
		
		printf("Ob '%s' - Successfully removed %d keyframes \n", id->name+2, success);
		
		ob->recalc |= OB_RECALC_OB;
	}
	CTX_DATA_END;
	
	/* send updates */
	ED_anim_dag_flush_update(C);	
	
	WM_event_add_notifier(C, NC_OBJECT|ND_KEYS, NULL);
	
	return OPERATOR_FINISHED;
}

void ANIM_OT_delete_keyframe_old (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Delete Keyframe";
	ot->idname= "ANIM_OT_delete_keyframe_old";
	
	/* callbacks */
	ot->invoke= WM_operator_confirm;
	ot->exec= delete_key_old_exec; 
	
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}


/* Insert Key Button Operator ------------------------ */

static int insert_key_button_exec (bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	PointerRNA ptr;
	PropertyRNA *prop= NULL;
	char *path;
	float cfra= (float)CFRA; // XXX for now, don't bother about all the yucky offset crap
	short success= 0;
	int a, index, length, all= RNA_boolean_get(op->ptr, "all");
	
	/* try to insert keyframe using property retrieved from UI */
	memset(&ptr, 0, sizeof(PointerRNA));
	uiAnimContextProperty(C, &ptr, &prop, &index);
	
	if(ptr.data && prop && RNA_property_animateable(ptr.data, prop)) {
		path= RNA_path_from_ID_to_property(&ptr, prop);
		
		if(path) {
			if(all) {
				length= RNA_property_array_length(&ptr, prop);
				
				if(length) index= 0;
				else length= 1;
			}
			else
				length= 1;
			
			for(a=0; a<length; a++)
				success+= insertkey(ptr.id.data, NULL, path, index+a, cfra, 0);
			
			MEM_freeN(path);
		}
	}
	
	if(success) {
		/* send updates */
		ED_anim_dag_flush_update(C);	
		
		/* for now, only send ND_KEYS for KeyingSets */
		WM_event_add_notifier(C, ND_KEYS, NULL);
	}
	
	return (success)? OPERATOR_FINISHED: OPERATOR_CANCELLED;
}

void ANIM_OT_insert_keyframe_button (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Insert Keyframe";
	ot->idname= "ANIM_OT_insert_keyframe_button";
	
	/* callbacks */
	ot->exec= insert_key_button_exec; 
	ot->poll= modify_key_op_poll;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* properties */
	RNA_def_boolean(ot->srna, "all", 1, "All", "Insert a keyframe for all element of the array.");
}

/* Delete Key Button Operator ------------------------ */

static int delete_key_button_exec (bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	PointerRNA ptr;
	PropertyRNA *prop= NULL;
	char *path;
	float cfra= (float)CFRA; // XXX for now, don't bother about all the yucky offset crap
	short success= 0;
	int a, index, length, all= RNA_boolean_get(op->ptr, "all");
	
	/* try to insert keyframe using property retrieved from UI */
	memset(&ptr, 0, sizeof(PointerRNA));
	uiAnimContextProperty(C, &ptr, &prop, &index);

	if(ptr.data && prop) {
		path= RNA_path_from_ID_to_property(&ptr, prop);
		
		if(path) {
			if(all) {
				length= RNA_property_array_length(&ptr, prop);
				
				if(length) index= 0;
				else length= 1;
			}
			else
				length= 1;
			
			for(a=0; a<length; a++)
				success+= deletekey(ptr.id.data, NULL, path, index+a, cfra, 0);
			
			MEM_freeN(path);
		}
	}
	
	
	if(success) {
		/* send updates */
		ED_anim_dag_flush_update(C);	
		
		/* for now, only send ND_KEYS for KeyingSets */
		WM_event_add_notifier(C, ND_KEYS, NULL);
	}
	
	return (success)? OPERATOR_FINISHED: OPERATOR_CANCELLED;
}

void ANIM_OT_delete_keyframe_button (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Delete Keyframe";
	ot->idname= "ANIM_OT_delete_keyframe_button";
	
	/* callbacks */
	ot->exec= delete_key_button_exec; 
	ot->poll= modify_key_op_poll;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;

	/* properties */
	RNA_def_boolean(ot->srna, "all", 1, "All", "Delete keyfames from all elements of the array.");
}

/* ******************************************* */
/* KEYFRAME DETECTION */

/* --------------- API/Per-Datablock Handling ------------------- */

/* Checks whether an Action has a keyframe for a given frame 
 * Since we're only concerned whether a keyframe exists, we can simply loop until a match is found...
 */
short action_frame_has_keyframe (bAction *act, float frame, short filter)
{
	FCurve *fcu;
	
	/* can only find if there is data */
	if (act == NULL)
		return 0;
		
	/* if only check non-muted, check if muted */
	if ((filter & ANIMFILTER_KEYS_MUTED) || (act->flag & ACT_MUTED))
		return 0;
	
	/* loop over F-Curves, using binary-search to try to find matches 
	 *	- this assumes that keyframes are only beztriples
	 */
	for (fcu= act->curves.first; fcu; fcu= fcu->next) {
		/* only check if there are keyframes (currently only of type BezTriple) */
		if (fcu->bezt && fcu->totvert) {
			/* we either include all regardless of muting, or only non-muted  */
			if ((filter & ANIMFILTER_KEYS_MUTED) || (fcu->flag & FCURVE_MUTED)==0) {
				short replace = -1;
				int i = binarysearch_bezt_index(fcu->bezt, frame, fcu->totvert, &replace);
				
				/* binarysearch_bezt_index will set replace to be 0 or 1
				 * 	- obviously, 1 represents a match
				 */
				if (replace) {			
					/* sanity check: 'i' may in rare cases exceed arraylen */
					if ((i >= 0) && (i < fcu->totvert))
						return 1;
				}
			}
		}
	}
	
	/* nothing found */
	return 0;
}

/* Checks whether an Object has a keyframe for a given frame */
short object_frame_has_keyframe (Object *ob, float frame, short filter)
{
	/* error checking */
	if (ob == NULL)
		return 0;
	
	/* check own animation data - specifically, the action it contains */
	if ((ob->adt) && (ob->adt->action)) {
		if (action_frame_has_keyframe(ob->adt->action, frame, filter))
			return 1;
	}
	
	/* try shapekey keyframes (if available, and allowed by filter) */
	if ( !(filter & ANIMFILTER_KEYS_LOCAL) && !(filter & ANIMFILTER_KEYS_NOSKEY) ) {
		Key *key= ob_get_key(ob);
		
		/* shapekeys can have keyframes ('Relative Shape Keys') 
		 * or depend on time (old 'Absolute Shape Keys') 
		 */
		 
			/* 1. test for relative (with keyframes) */
		if (id_frame_has_keyframe((ID *)key, frame, filter))
			return 1;
			
			/* 2. test for time */
		// TODO... yet to be implemented (this feature may evolve before then anyway)
	}
	
	/* try materials */
	if ( !(filter & ANIMFILTER_KEYS_LOCAL) && !(filter & ANIMFILTER_KEYS_NOMAT) ) {
		/* if only active, then we can skip a lot of looping */
		if (filter & ANIMFILTER_KEYS_ACTIVE) {
			Material *ma= give_current_material(ob, (ob->actcol + 1));
			
			/* we only retrieve the active material... */
			if (id_frame_has_keyframe((ID *)ma, frame, filter))
				return 1;
		}
		else {
			int a;
			
			/* loop over materials */
			for (a=0; a<ob->totcol; a++) {
				Material *ma= give_current_material(ob, a+1);
				
				if (id_frame_has_keyframe((ID *)ma, frame, filter))
					return 1;
			}
		}
	}
	
	/* nothing found */
	return 0;
}

/* --------------- API ------------------- */

/* Checks whether a keyframe exists for the given ID-block one the given frame */
short id_frame_has_keyframe (ID *id, float frame, short filter)
{
	/* sanity checks */
	if (id == NULL)
		return 0;
	
	/* perform special checks for 'macro' types */
	switch (GS(id->name)) {
		case ID_OB: /* object */
			return object_frame_has_keyframe((Object *)id, frame, filter);
			break;
			
		case ID_SCE: /* scene */
		// XXX TODO... for now, just use 'normal' behaviour
		//	break;
		
		default: 	/* 'normal type' */
		{
			AnimData *adt= BKE_animdata_from_id(id);
			
			/* only check keyframes in active action */
			if (adt)
				return action_frame_has_keyframe(adt->action, frame, filter);
		}
			break;
	}
	
	
	/* no keyframe found */
	return 0;
}

/* ************************************************** */
