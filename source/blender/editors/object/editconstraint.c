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
 * The Original Code is: all of this file.
 *
 * Contributor(s): Joshua Leung, Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdio.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_dynstr.h"

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_constraint_types.h"
#include "DNA_curve_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_text_types.h"
#include "DNA_view3d_types.h"

#include "BKE_action.h"
#include "BKE_armature.h"
#include "BKE_constraint.h"
#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_object.h"
#include "BKE_report.h"
#include "BKE_utildefines.h"

#ifndef DISABLE_PYTHON
#include "BPY_extern.h"
#endif

#include "WM_api.h"
#include "WM_types.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"
#include "RNA_types.h"

#include "ED_object.h"
#include "ED_screen.h"

#include "UI_interface.h"

#include "object_intern.h"

/* XXX */
static void BIF_undo_push() {}
static void error() {}
static int okee() {return 0;}
static int pupmenu() {return 0;}

/* -------------- Get Active Constraint Data ---------------------- */

/* if object in posemode, active bone constraints, else object constraints */
ListBase *get_active_constraints (Object *ob)
{
	if (ob == NULL)
		return NULL;

	if (ob->flag & OB_POSEMODE) {
		bPoseChannel *pchan;
		
		pchan = get_active_posechannel(ob);
		if (pchan)
			return &pchan->constraints;
	}
	else 
		return &ob->constraints;

	return NULL;
}

/* single constraint */
bConstraint *get_active_constraint (Object *ob)
{
	ListBase *lb= get_active_constraints(ob);

	if (lb) {
		bConstraint *con;
		
		for (con= lb->first; con; con=con->next) {
			if (con->flag & CONSTRAINT_ACTIVE)
				return con;
		}
	}
	
	return NULL;
}
/* -------------- Constraint Management (Add New, Remove, Rename) -------------------- */
/* ------------- PyConstraints ------------------ */

/* this callback sets the text-file to be used for selected menu item */
void validate_pyconstraint_cb (void *arg1, void *arg2)
{
	bPythonConstraint *data = arg1;
	Text *text= NULL;
	int index = *((int *)arg2);
	int i;
	
	/* exception for no script */
	if (index) {
		/* innovative use of a for...loop to search */
		for (text=G.main->text.first, i=1; text && index!=i; i++, text=text->id.next);
	}
	data->text = text;
}

#ifndef DISABLE_PYTHON
/* this returns a string for the list of usable pyconstraint script names */
char *buildmenu_pyconstraints (Text *con_text, int *pyconindex)
{
	DynStr *pupds= BLI_dynstr_new();
	Text *text;
	char *str;
	char buf[64];
	int i;
	
	/* add title first */
	sprintf(buf, "Scripts: %%t|[None]%%x0|");
	BLI_dynstr_append(pupds, buf);
	
	/* init active-index first */
	if (con_text == NULL)
		*pyconindex= 0;
	
	/* loop through markers, adding them */
	for (text=G.main->text.first, i=1; text; i++, text=text->id.next) {
		/* this is important to ensure that right script is shown as active */
		if (text == con_text) *pyconindex = i;
		
		/* only include valid pyconstraint scripts */
		if (BPY_is_pyconstraint(text)) {
			BLI_dynstr_append(pupds, text->id.name+2);
			
			sprintf(buf, "%%x%d", i);
			BLI_dynstr_append(pupds, buf);
			
			if (text->id.next)
				BLI_dynstr_append(pupds, "|");
		}
	}
	
	/* convert to normal MEM_malloc'd string */
	str= BLI_dynstr_get_cstring(pupds);
	BLI_dynstr_free(pupds);
	
	return str;
}
#endif /* DISABLE_PYTHON */

/* this callback gets called when the 'refresh' button of a pyconstraint gets pressed */
void update_pyconstraint_cb (void *arg1, void *arg2)
{
	Object *owner= (Object *)arg1;
	bConstraint *con= (bConstraint *)arg2;
#ifndef DISABLE_PYTHON
	if (owner && con)
		BPY_pyconstraint_update(owner, con);
#endif
}

/* Creates a new constraint, initialises its data, and returns it */
bConstraint *add_new_constraint (short type)
{
	bConstraint *con;
	bConstraintTypeInfo *cti;

	con = MEM_callocN(sizeof(bConstraint), "Constraint");
	
	/* Set up a generic constraint datablock */
	con->type = type;
	con->flag |= CONSTRAINT_EXPAND;
	con->enforce = 1.0F;
	strcpy(con->name, "Const");
	
	/* Load the data for it */
	cti = constraint_get_typeinfo(con);
	if (cti) {
		con->data = MEM_callocN(cti->size, cti->structName);
		
		/* only constraints that change any settings need this */
		if (cti->new_data)
			cti->new_data(con->data);
	}
	
	return con;
}

/* Adds the given constraint to the Object-level set of constraints for the given Object */
void add_constraint_to_object (bConstraint *con, Object *ob)
{
	ListBase *list;
	list = &ob->constraints;
	
	if (list) {
		unique_constraint_name(con, list);
		BLI_addtail(list, con);
		
		if (proxylocked_constraints_owner(ob, NULL))
			con->flag |= CONSTRAINT_PROXY_LOCAL;
		
		con->flag |= CONSTRAINT_ACTIVE;
		for (con= con->prev; con; con= con->prev)
			con->flag &= ~CONSTRAINT_ACTIVE;
	}
}

/* helper function for add_constriant - sets the last target for the active constraint */
static void set_constraint_nth_target (bConstraint *con, Object *target, char subtarget[], int index)
{
	bConstraintTypeInfo *cti= constraint_get_typeinfo(con);
	ListBase targets = {NULL, NULL};
	bConstraintTarget *ct;
	int num_targets, i;
	
	if (cti && cti->get_constraint_targets) {
		cti->get_constraint_targets(con, &targets);
		num_targets= BLI_countlist(&targets);
		
		if (index < 0) {
			if (abs(index) < num_targets)
				index= num_targets - abs(index);
			else
				index= num_targets - 1;
		}
		else if (index >= num_targets) {
			index= num_targets - 1;
		}
		
		for (ct=targets.first, i=0; ct; ct= ct->next, i++) {
			if (i == index) {
				ct->tar= target;
				strcpy(ct->subtarget, subtarget);
				break;
			}
		}
		
		if (cti->flush_constraint_targets)
			cti->flush_constraint_targets(con, &targets, 0);
	}
}

/* context: active object in posemode, active channel, optional selected channel */
void add_constraint (Scene *scene, View3D *v3d, short only_IK)
{
	Object *ob= OBACT, *obsel=NULL;
	bPoseChannel *pchanact=NULL, *pchansel=NULL;
	bConstraint *con=NULL;
	Base *base;
	short nr;
	
	/* paranoia checks */
	if ((ob==NULL) || (ob==scene->obedit)) 
		return;

	if ((ob->pose) && (ob->flag & OB_POSEMODE)) {
		bArmature *arm= ob->data;
		
		/* find active channel */
		pchanact= get_active_posechannel(ob);
		if (pchanact==NULL) 
			return;
		
		/* find selected bone */
		for (pchansel=ob->pose->chanbase.first; pchansel; pchansel=pchansel->next) {
			if (pchansel != pchanact) {
				if (pchansel->bone->flag & BONE_SELECTED)  {
					if (pchansel->bone->layer & arm->layer)
						break;
				}
			}
		}
	}
	
	/* find selected object */
	for (base= FIRSTBASE; base; base= base->next) {
		if ((TESTBASE(v3d, base)) && (base->object!=ob)) 
			obsel= base->object;
	}
	
	/* the only_IK caller has checked for posemode! */
	if (only_IK) {
		for (con= pchanact->constraints.first; con; con= con->next) {
			if (con->type==CONSTRAINT_TYPE_KINEMATIC) break;
		}
		if (con) {
			error("Pose Channel already has IK");
			return;
		}
		
		if (pchansel)
			nr= pupmenu("Add IK Constraint%t|To Active Bone%x10");
		else if (obsel)
			nr= pupmenu("Add IK Constraint%t|To Active Object%x10");
		else 
			nr= pupmenu("Add IK Constraint%t|To New Empty Object%x10|Without Target%x11");
	}
	else {
		if (pchanact) {
			if (pchansel)
				nr= pupmenu("Add Constraint to Active Bone%t|Child Of%x19|Transformation%x20|%l|Copy Location%x1|Copy Rotation%x2|Copy Scale%x8|%l|Limit Location%x13|Limit Rotation%x14|Limit Scale%x15|Limit Distance%x21|%l|Track To%x3|Floor%x4|Locked Track%x5|Stretch To%x7|%l|Action%x16|Script%x18");
			else if ((obsel) && (obsel->type==OB_CURVE))
				nr= pupmenu("Add Constraint to Active Object%t|Child Of%x19|Transformation%x20|%l|Copy Location%x1|Copy Rotation%x2|Copy Scale%x8|%l|Limit Location%x13|Limit Rotation%x14|Limit Scale%x15|Limit Distance%x21|%l|Track To%x3|Floor%x4|Locked Track%x5|Follow Path%x6|Clamp To%x17|Stretch To%x7|%l|Action%x16|Script%x18");
			else if ((obsel) && (obsel->type==OB_MESH))
				nr= pupmenu("Add Constraint to Active Object%t|Child Of%x19|Transformation%x20|%l|Copy Location%x1|Copy Rotation%x2|Copy Scale%x8|%l|Limit Location%x13|Limit Rotation%x14|Limit Scale%x15|Limit Distance%x21|%l|Track To%x3|Floor%x4|Locked Track%x5|Shrinkwrap%x22|Stretch To%x7|%l|Action%x16|Script%x18");
			else if (obsel)
				nr= pupmenu("Add Constraint to Active Object%t|Child Of%x19|Transformation%x20|%l|Copy Location%x1|Copy Rotation%x2|Copy Scale%x8|%l|Limit Location%x13|Limit Rotation%x14|Limit Scale%x15|Limit Distance%x21|%l|Track To%x3|Floor%x4|Locked Track%x5|Stretch To%x7|%l|Action%x16|Script%x18");
			else
				nr= pupmenu("Add Constraint to New Empty Object%t|Child Of%x19|Transformation%x20|%l|Copy Location%x1|Copy Rotation%x2|Copy Scale%x8|%l|Limit Location%x13|Limit Rotation%x14|Limit Scale%x15|Limit Distance%x21|%l|Track To%x3|Floor%x4|Locked Track%x5|Stretch To%x7|%l|Action%x16|Script%x18");
		}
		else {
			if ((obsel) && (obsel->type==OB_CURVE))
				nr= pupmenu("Add Constraint to Active Object%t|Child Of%x19|Transformation%x20|%l|Copy Location%x1|Copy Rotation%x2|Copy Scale%x8|%l|Limit Location%x13|Limit Rotation%x14|Limit Scale%x15|Limit Distance%x21|%l|Track To%x3|Floor%x4|Locked Track%x5|Follow Path%x6|Clamp To%x17|%l|Action%x16|Script%x18");
			else if ((obsel) && (obsel->type==OB_MESH))
				nr= pupmenu("Add Constraint to Active Object%t|Child Of%x19|Transformation%x20|%l|Copy Location%x1|Copy Rotation%x2|Copy Scale%x8|%l|Limit Location%x13|Limit Rotation%x14|Limit Scale%x15|Limit Distance%x21|%l|Track To%x3|Floor%x4|Locked Track%x5|Shrinkwrap%x22|%l|Action%x16|Script%x18");
			else if (obsel)
				nr= pupmenu("Add Constraint to Active Object%t|Child Of%x19|Transformation%x20|%l|Copy Location%x1|Copy Rotation%x2|Copy Scale%x8|%l|Limit Location%x13|Limit Rotation%x14|Limit Scale%x15|Limit Distance%x21|%l|Track To%x3|Floor%x4|Locked Track%x5|%l|Action%x16|Script%x18");
			else
				nr= pupmenu("Add Constraint to New Empty Object%t|Child Of%x19|Transformation%x20|%l|Copy Location%x1|Copy Rotation%x2|Copy Scale%x8|%l|Limit Location%x13|Limit Rotation%x14|Limit Scale%x15|Limit Distance%x21|%l|Track To%x3|Floor%x4|Locked Track%x5|%l|Action%x16|Script%x18");
		}
	}
	
	if (nr < 1) return;
	
	/* handle IK separate */
	if (nr==10 || nr==11) {
		/* ik - prevent weird chains... */
		if (pchansel) {
			bPoseChannel *pchan= pchanact;
			while (pchan) {
				if (pchan==pchansel) break;
				pchan= pchan->parent;
			}
			if (pchan) {
				error("IK root cannot be linked to IK tip");
				return;
			}
			
			pchan= pchansel;
			while (pchan) {
				if (pchan==pchanact) break;
				pchan= pchan->parent;
			}
			if (pchan) {
				error("IK tip cannot be linked to IK root");
				return;
			}		
		}
		
		con = add_new_constraint(CONSTRAINT_TYPE_KINEMATIC);
		BLI_addtail(&pchanact->constraints, con);
		unique_constraint_name(con, &pchanact->constraints);
		pchanact->constflag |= PCHAN_HAS_IK;	/* for draw, but also for detecting while pose solving */
		if (nr==11) 
			pchanact->constflag |= PCHAN_HAS_TARGET;
		if (proxylocked_constraints_owner(ob, pchanact))
			con->flag |= CONSTRAINT_PROXY_LOCAL;
	}
	else {
		/* normal constraints - add data */
		if (nr==1) con = add_new_constraint(CONSTRAINT_TYPE_LOCLIKE);
		else if (nr==2) con = add_new_constraint(CONSTRAINT_TYPE_ROTLIKE);
		else if (nr==3) con = add_new_constraint(CONSTRAINT_TYPE_TRACKTO);
		else if (nr==4) con = add_new_constraint(CONSTRAINT_TYPE_MINMAX);
		else if (nr==5) con = add_new_constraint(CONSTRAINT_TYPE_LOCKTRACK);
		else if (nr==6) {
			Curve *cu= obsel->data;
			cu->flag |= CU_PATH;
			con = add_new_constraint(CONSTRAINT_TYPE_FOLLOWPATH);
		}
		else if (nr==7) con = add_new_constraint(CONSTRAINT_TYPE_STRETCHTO);
		else if (nr==8) con = add_new_constraint(CONSTRAINT_TYPE_SIZELIKE);
		else if (nr==13) con = add_new_constraint(CONSTRAINT_TYPE_LOCLIMIT);
		else if (nr==14) con = add_new_constraint(CONSTRAINT_TYPE_ROTLIMIT);
		else if (nr==15) con = add_new_constraint(CONSTRAINT_TYPE_SIZELIMIT);
		else if (nr==16) {
			/* TODO: add a popup-menu to display list of available actions to use (like for pyconstraints) */
			con = add_new_constraint(CONSTRAINT_TYPE_ACTION);
		}
		else if (nr==17) {
			Curve *cu= obsel->data;
			cu->flag |= CU_PATH;
			con = add_new_constraint(CONSTRAINT_TYPE_CLAMPTO);
		}
		else if (nr==18) {	
			char *menustr;
			int scriptint= 0;
#ifndef DISABLE_PYTHON
			/* popup a list of usable scripts */
			menustr = buildmenu_pyconstraints(NULL, &scriptint);
			scriptint = pupmenu(menustr);
			MEM_freeN(menustr);
			
			/* only add constraint if a script was chosen */
			if (scriptint) {
				/* add constraint */
				con = add_new_constraint(CONSTRAINT_TYPE_PYTHON);
				validate_pyconstraint_cb(con->data, &scriptint);
				
				/* make sure target allowance is set correctly */
				BPY_pyconstraint_update(ob, con);
			}
#endif
		}
		else if (nr==19) {
			con = add_new_constraint(CONSTRAINT_TYPE_CHILDOF);
		
			/* if this constraint is being added to a posechannel, make sure
			 * the constraint gets evaluated in pose-space
			 */
			if (pchanact) {
				con->ownspace = CONSTRAINT_SPACE_POSE;
				con->flag |= CONSTRAINT_SPACEONCE;
			}
		}
		else if (nr==20) con = add_new_constraint(CONSTRAINT_TYPE_TRANSFORM);
		else if (nr==21) con = add_new_constraint(CONSTRAINT_TYPE_DISTLIMIT);
		else if (nr==22) con = add_new_constraint(CONSTRAINT_TYPE_SHRINKWRAP);
		
		if (con==NULL) return;	/* paranoia */
		
		if (pchanact) {
			BLI_addtail(&pchanact->constraints, con);
			unique_constraint_name(con, &pchanact->constraints);
			pchanact->constflag |= PCHAN_HAS_CONST;	/* for draw */
			if (proxylocked_constraints_owner(ob, pchanact))
				con->flag |= CONSTRAINT_PROXY_LOCAL;
		}
		else {
			BLI_addtail(&ob->constraints, con);
			unique_constraint_name(con, &ob->constraints);
			if (proxylocked_constraints_owner(ob, NULL))
				con->flag |= CONSTRAINT_PROXY_LOCAL;
		}
	}
	
	/* set the target */
	if (pchansel) {
		set_constraint_nth_target(con, ob, pchansel->name, 0);
	}
	else if (obsel) {
		set_constraint_nth_target(con, obsel, "", 0);
	}
	else if (ELEM4(nr, 11, 13, 14, 15)==0) {	/* add new empty as target */
		Base *base= BASACT, *newbase;
		Object *obt;
		
		obt= add_object(scene, OB_EMPTY);
		/* set layers OK */
		newbase= BASACT;
		newbase->lay= base->lay;
		obt->lay= newbase->lay;
		
		/* transform cent to global coords for loc */
		if (pchanact) {
			if (only_IK)
				VecMat4MulVecfl(obt->loc, ob->obmat, pchanact->pose_tail);
			else
				VecMat4MulVecfl(obt->loc, ob->obmat, pchanact->pose_head);
		}
		else
			VECCOPY(obt->loc, ob->obmat[3]);
		
		set_constraint_nth_target(con, obt, "", 0);
		
		/* restore, add_object sets active */
		BASACT= base;
		base->flag |= SELECT;
	}
	
	/* active flag */
	con->flag |= CONSTRAINT_ACTIVE;
	for (con= con->prev; con; con= con->prev)
		con->flag &= ~CONSTRAINT_ACTIVE;

	DAG_scene_sort(scene);		// sort order of objects
	
	if (pchanact) {
		ob->pose->flag |= POSE_RECALC;	// sort pose channels
		DAG_object_flush_update(scene, ob, OB_RECALC_DATA);	// and all its relations
	}
	else
		DAG_object_flush_update(scene, ob, OB_RECALC_OB);	// and all its relations

	if (only_IK)
		BIF_undo_push("Add IK Constraint");
	else
		BIF_undo_push("Add Constraint");

}

/* ------------- Constraint Sanity Testing ------------------- */

/* checks validity of object pointers, and NULLs,
 * if Bone doesnt exist it sets the CONSTRAINT_DISABLE flag 
 */
static void test_constraints (Object *owner, const char substring[])
{
	bConstraint *curcon;
	ListBase *conlist= NULL;
	int type;
	
	if (owner==NULL) return;
	
	/* Check parents */
	if (strlen(substring)) {
		switch (owner->type) {
			case OB_ARMATURE:
				type = CONSTRAINT_OBTYPE_BONE;
				break;
			default:
				type = CONSTRAINT_OBTYPE_OBJECT;
				break;
		}
	}
	else
		type = CONSTRAINT_OBTYPE_OBJECT;
	
	/* Get the constraint list for this object */
	switch (type) {
		case CONSTRAINT_OBTYPE_OBJECT:
			conlist = &owner->constraints;
			break;
		case CONSTRAINT_OBTYPE_BONE:
			{
				Bone *bone;
				bPoseChannel *chan;
				
				bone = get_named_bone( ((bArmature *)owner->data), substring );
				chan = get_pose_channel(owner->pose, substring);
				if (bone && chan) {
					conlist = &chan->constraints;
				}
			}
			break;
	}
	
	/* Check all constraints - is constraint valid? */
	if (conlist) {
		for (curcon = conlist->first; curcon; curcon=curcon->next) {
			bConstraintTypeInfo *cti= constraint_get_typeinfo(curcon);
			ListBase targets = {NULL, NULL};
			bConstraintTarget *ct;
			
			/* clear disabled-flag first */
			curcon->flag &= ~CONSTRAINT_DISABLE;

			if (curcon->type == CONSTRAINT_TYPE_KINEMATIC) {
				bKinematicConstraint *data = curcon->data;
				
				/* bad: we need a separate set of checks here as poletarget is 
				 *		optional... otherwise poletarget must exist too or else
				 *		the constraint is deemed invalid
				 */
				if (exist_object(data->tar) == 0) {
					data->tar = NULL;
					curcon->flag |= CONSTRAINT_DISABLE;
				}
				else if (data->tar == owner) {
					if (!get_named_bone(get_armature(owner), data->subtarget)) {
						curcon->flag |= CONSTRAINT_DISABLE;
					}
				}
				
				if (data->poletar) {
					if (exist_object(data->poletar) == 0) {
						data->poletar = NULL;
						curcon->flag |= CONSTRAINT_DISABLE;
					}
					else if (data->poletar == owner) {
						if (!get_named_bone(get_armature(owner), data->polesubtarget)) {
							curcon->flag |= CONSTRAINT_DISABLE;
						}
					}
				}
				
				/* targets have already been checked for this */
				continue;
			}
			else if (curcon->type == CONSTRAINT_TYPE_ACTION) {
				bActionConstraint *data = curcon->data;
				
				/* validate action */
				if (data->act == NULL) 
					curcon->flag |= CONSTRAINT_DISABLE;
			}
			else if (curcon->type == CONSTRAINT_TYPE_FOLLOWPATH) {
				bFollowPathConstraint *data = curcon->data;
				
				/* don't allow track/up axes to be the same */
				if (data->upflag==data->trackflag)
					curcon->flag |= CONSTRAINT_DISABLE;
				if (data->upflag+3==data->trackflag)
					curcon->flag |= CONSTRAINT_DISABLE;
			}
			else if (curcon->type == CONSTRAINT_TYPE_TRACKTO) {
				bTrackToConstraint *data = curcon->data;
				
				/* don't allow track/up axes to be the same */
				if (data->reserved2==data->reserved1)
					curcon->flag |= CONSTRAINT_DISABLE;
				if (data->reserved2+3==data->reserved1)
					curcon->flag |= CONSTRAINT_DISABLE;
			}
			else if (curcon->type == CONSTRAINT_TYPE_LOCKTRACK) {
				bLockTrackConstraint *data = curcon->data;
				
				if (data->lockflag==data->trackflag)
					curcon->flag |= CONSTRAINT_DISABLE;
				if (data->lockflag+3==data->trackflag)
					curcon->flag |= CONSTRAINT_DISABLE;
			}
			
			/* Check targets for constraints */
			if (cti && cti->get_constraint_targets) {
				cti->get_constraint_targets(curcon, &targets);
				
				/* disable and clear constraints targets that are incorrect */
				for (ct= targets.first; ct; ct= ct->next) {
					/* general validity checks (for those constraints that need this) */
					if (exist_object(ct->tar) == 0) {
						ct->tar = NULL;
						curcon->flag |= CONSTRAINT_DISABLE;
					}
					else if (ct->tar == owner) {
						if (!get_named_bone(get_armature(owner), ct->subtarget)) {
							curcon->flag |= CONSTRAINT_DISABLE;
						}
					}
					
					/* target checks for specific constraints */
					if (ELEM(curcon->type, CONSTRAINT_TYPE_FOLLOWPATH, CONSTRAINT_TYPE_CLAMPTO)) {
						if (ct->tar) {
							if (ct->tar->type != OB_CURVE) {
								ct->tar= NULL;
								curcon->flag |= CONSTRAINT_DISABLE;
							}
							else {
								Curve *cu= ct->tar->data;
								
								/* auto-set 'Path' setting on curve so this works  */
								cu->flag |= CU_PATH;
							}
						}						
					}
				}	
				
				/* free any temporary targets */
				if (cti->flush_constraint_targets)
					cti->flush_constraint_targets(curcon, &targets, 0);
			}
		}
	}
}

static void test_bonelist_constraints (Object *owner, ListBase *list)
{
	Bone *bone;

	for (bone = list->first; bone; bone = bone->next) {
		test_constraints(owner, bone->name);
		test_bonelist_constraints(owner, &bone->childbase);
	}
}

void object_test_constraints (Object *owner)
{
	test_constraints(owner, "");

	if (owner->type==OB_ARMATURE) {
		bArmature *arm= get_armature(owner);
		
		if (arm)
			test_bonelist_constraints(owner, &arm->bonebase);
	}
}

/* ********************** CONSTRAINT-SPECIFIC STUFF ********************* */

/* ------------- Child-Of Constraint ------------------ */

/* ChildOf Constraint - set inverse callback */
static int childof_set_inverse_exec (bContext *C, wmOperator *op)
{
	PointerRNA ptr= CTX_data_pointer_get_type(C, "constraint", &RNA_ChildOfConstraint);
	Scene *scene= CTX_data_scene(C);
	Object *ob= ptr.id.data;
	bConstraint *con= ptr.data;
	bChildOfConstraint *data= (bChildOfConstraint *)con->data;
	bPoseChannel *pchan= NULL;

	/* try to find a pose channel */
	// TODO: get from context instead?
	if (ob && ob->pose)
		pchan= get_active_posechannel(ob);
	
	/* calculate/set inverse matrix */
	if (pchan) {
		float pmat[4][4], cinf;
		float imat[4][4], tmat[4][4];
		
		/* make copy of pchan's original pose-mat (for use later) */
		Mat4CpyMat4(pmat, pchan->pose_mat);
		
		/* disable constraint for pose to be solved without it */
		cinf= con->enforce;
		con->enforce= 0.0f;
		
		/* solve pose without constraint */
		where_is_pose(scene, ob);
		
		/* determine effect of constraint by removing the newly calculated 
		 * pchan->pose_mat from the original pchan->pose_mat, thus determining 
		 * the effect of the constraint
		 */
		Mat4Invert(imat, pchan->pose_mat);
		Mat4MulMat4(tmat, imat, pmat);
		Mat4Invert(data->invmat, tmat);
		
		/* recalculate pose with new inv-mat */
		con->enforce= cinf;
		where_is_pose(scene, ob);
	}
	else if (ob) {
		Object workob;
		/* use what_does_parent to find inverse - just like for normal parenting.
		 * NOTE: what_does_parent uses a static workob defined in object.c 
		 */
		what_does_parent(scene, ob, &workob);
		Mat4Invert(data->invmat, workob.obmat);
	}
	else
		Mat4One(data->invmat);
		
	WM_event_add_notifier(C, NC_OBJECT|ND_CONSTRAINT, ob);
		
	return OPERATOR_FINISHED;
}

void CONSTRAINT_OT_childof_set_inverse (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Set Inverse";
	ot->idname= "CONSTRAINT_OT_childof_set_inverse";
	ot->description= "Set inverse correction for ChildOf constraint.";
	
	ot->exec= childof_set_inverse_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}


/* ChildOf Constraint - clear inverse callback */
static int childof_clear_inverse_exec (bContext *C, wmOperator *op)
{
	PointerRNA ptr= CTX_data_pointer_get_type(C, "constraint", &RNA_ChildOfConstraint);
	Object *ob= ptr.id.data;
	bConstraint *con= ptr.data;
	bChildOfConstraint *data= (bChildOfConstraint *)con->data;
	
	/* simply clear the matrix */
	Mat4One(data->invmat);
	
	WM_event_add_notifier(C, NC_OBJECT|ND_CONSTRAINT, ob);
	
	return OPERATOR_FINISHED;
}

void CONSTRAINT_OT_childof_clear_inverse (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Clear Inverse";
	ot->idname= "CONSTRAINT_OT_childof_clear_inverse";
	ot->description= "Clear inverse correction for ChildOf constraint.";
	
	ot->exec= childof_clear_inverse_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/***************************** BUTTONS ****************************/

/* Rename the given constraint, con already has the new name */
void ED_object_constraint_rename(Object *ob, bConstraint *con, char *oldname)
{
	bConstraint *tcon;
	ListBase *conlist= NULL;
	int from_object= 0;
	
	/* get context by searching for con (primitive...) */
	for (tcon= ob->constraints.first; tcon; tcon= tcon->next) {
		if (tcon==con)
			break;
	}
	
	if (tcon) {
		conlist= &ob->constraints;
		from_object= 1;
	}
	else if (ob->pose) {
		bPoseChannel *pchan;
		
		for (pchan=ob->pose->chanbase.first; pchan; pchan=pchan->next) {
			for (tcon= pchan->constraints.first; tcon; tcon= tcon->next) {
				if (tcon==con)
					break;
			}
			if (tcon) 
				break;
		}
		
		if (tcon) {
			conlist= &pchan->constraints;
		}
	}
	
	if (conlist==NULL) {
		printf("rename constraint failed\n");	/* should not happen in UI */
		return;
	}
	
	/* first make sure it's a unique name within context */
	unique_constraint_name(con, conlist);
}




void ED_object_constraint_set_active(Object *ob, bConstraint *con)
{
	ListBase *lb;
	bConstraint *origcon= con;
	
	/* lets be nice and escape if its active already */
	if(con && (con->flag & CONSTRAINT_ACTIVE))
		return ;
	
	lb= get_active_constraints(ob);
	if(lb == NULL)
		return;
	
	for(con= lb->first; con; con= con->next) {
		if(con==origcon) con->flag |= CONSTRAINT_ACTIVE;
		else con->flag &= ~CONSTRAINT_ACTIVE;
	}
}

static int constraint_delete_exec (bContext *C, wmOperator *op)
{
	PointerRNA ptr= CTX_data_pointer_get_type(C, "constraint", &RNA_Constraint);
	Object *ob= ptr.id.data;
	bConstraint *con= ptr.data;
	ListBase *lb;
	
	/* remove constraint itself */
	lb= get_active_constraints(ob);
	free_constraint_data(con);
	BLI_freelinkN(lb, con);
	
	ED_object_constraint_set_active(ob, NULL);
	WM_event_add_notifier(C, NC_OBJECT|ND_CONSTRAINT, ob);

	return OPERATOR_FINISHED;
}

void CONSTRAINT_OT_delete (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Delete Constraint";
	ot->idname= "CONSTRAINT_OT_delete";
	ot->description= "Remove constraitn from constraint stack.";
	
	/* callbacks */
	ot->exec= constraint_delete_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO; 
}

static int constraint_move_down_exec (bContext *C, wmOperator *op)
{
	PointerRNA ptr= CTX_data_pointer_get_type(C, "constraint", &RNA_Constraint);
	Object *ob= ptr.id.data;
	bConstraint *con= ptr.data;
	
	if (con->next) {
		ListBase *conlist= get_active_constraints(ob);
		bConstraint *nextCon= con->next;
		
		/* insert the nominated constraint after the one that used to be after it */
		BLI_remlink(conlist, con);
		BLI_insertlinkafter(conlist, nextCon, con);
		
		WM_event_add_notifier(C, NC_OBJECT|ND_CONSTRAINT, ob);
		
		return OPERATOR_FINISHED;
	}
	
	return OPERATOR_CANCELLED;
}

void CONSTRAINT_OT_move_down (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Move Constraint Down";
	ot->idname= "CONSTRAINT_OT_move_down";
	ot->description= "Move constraint down constraint stack.";
	
	/* callbacks */
	ot->exec= constraint_move_down_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO; 
}


static int constraint_move_up_exec (bContext *C, wmOperator *op)
{
	PointerRNA ptr= CTX_data_pointer_get_type(C, "constraint", &RNA_Constraint);
	Object *ob= ptr.id.data;
	bConstraint *con= ptr.data;
	
	if (con->prev) {
		ListBase *conlist= get_active_constraints(ob);
		bConstraint *prevCon= con->prev;
		
		/* insert the nominated constraint before the one that used to be before it */
		BLI_remlink(conlist, con);
		BLI_insertlinkbefore(conlist, prevCon, con);
		
		WM_event_add_notifier(C, NC_OBJECT|ND_CONSTRAINT, ob);
		
		return OPERATOR_FINISHED;
	}
	
	return OPERATOR_CANCELLED;
}

void CONSTRAINT_OT_move_up (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Move Constraint Up";
	ot->idname= "CONSTRAINT_OT_move_up";
	ot->description= "Move constraint up constraint stack.";
	
	/* callbacks */
	ot->exec= constraint_move_up_exec;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO; 
}

/***************************** OPERATORS ****************************/

/************************ remove constraint operators *********************/

static int pose_constraints_clear_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_active_object(C);
	
	/* free constraints for all selected bones */
	CTX_DATA_BEGIN(C, bPoseChannel*, pchan, selected_pchans)
	{
		free_constraints(&pchan->constraints);
	}
	CTX_DATA_END;
	
	/* do updates */
	DAG_object_flush_update(scene, ob, OB_RECALC_OB);
	WM_event_add_notifier(C, NC_OBJECT|ND_POSE|ND_CONSTRAINT|NA_REMOVED, ob);
	
	return OPERATOR_FINISHED;
}

void POSE_OT_constraints_clear(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Clear Constraints";
	ot->idname= "POSE_OT_constraints_clear";
	ot->description= "Clear all the constraints for the selected bones.";
	
	/* callbacks */
	ot->exec= pose_constraints_clear_exec;
	ot->poll= ED_operator_posemode; // XXX - do we want to ensure there are selected bones too?
}


static int object_constraints_clear_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_active_object(C);
	
	/* do freeing */
	// TODO: we should free constraints for all selected objects instead (to be more consistent with bones)
	free_constraints(&ob->constraints);
	
	/* do updates */
	DAG_object_flush_update(scene, ob, OB_RECALC_OB);
	WM_event_add_notifier(C, NC_OBJECT|ND_CONSTRAINT|NA_REMOVED, ob);
	
	return OPERATOR_FINISHED;
}

void OBJECT_OT_constraints_clear(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Clear Constraints";
	ot->idname= "OBJECT_OT_constraints_clear";
	ot->description= "Clear all the constraints for the active Object only.";
	
	/* callbacks */
	ot->exec= object_constraints_clear_exec;
	ot->poll= ED_operator_object_active;
}

/************************ add constraint operators *********************/

/* get the Object and/or PoseChannel to use as target */
static short get_new_constraint_target(bContext *C, int con_type, Object **tar_ob, bPoseChannel **tar_pchan, short add)
{
	Object *obact= CTX_data_active_object(C);
	short only_curve= 0, only_mesh= 0, only_ob= 0;
	short found= 0;
	
	/* clear tar_ob and tar_pchan fields before use 
	 *	- assume for now that both always exist...
	 */
	*tar_ob= NULL;
	*tar_pchan= NULL;
	
	/* check if constraint type doesn't requires a target
	 *	- if so, no need to get any targets 
	 */
	switch (con_type) {
		/* no-target constraints --------------------------- */
			/* null constraint - shouldn't even be added! */
		case CONSTRAINT_TYPE_NULL:
			/* limit constraints - no targets needed */
		case CONSTRAINT_TYPE_LOCLIMIT:
		case CONSTRAINT_TYPE_ROTLIMIT:
		case CONSTRAINT_TYPE_SIZELIMIT:
			return 0;
			
		/* restricted target-type constraints -------------- */
			/* curve-based constraints - set the only_curve and only_ob flags */
		case CONSTRAINT_TYPE_TRACKTO:
		case CONSTRAINT_TYPE_CLAMPTO:
		case CONSTRAINT_TYPE_FOLLOWPATH:
			only_curve= 1;
			only_ob= 1;
			break;
			
			/* mesh only? */
		case CONSTRAINT_TYPE_SHRINKWRAP:
			only_mesh= 1;
			only_ob= 1;
			break;
			
			/* object only */
		case CONSTRAINT_TYPE_RIGIDBODYJOINT:
			only_ob= 1;
			break;
	}
	
	/* if the active Object is Armature, and we can search for bones, do so... */
	if ((obact->type == OB_ARMATURE) && (only_ob == 0)) {
		/* search in list of selected Pose-Channels for target */
		CTX_DATA_BEGIN(C, bPoseChannel*, pchan, selected_pchans) 
		{
			/* just use the first one that we encounter... */
			*tar_ob= obact;
			*tar_pchan= pchan;
			found= 1;
			
			break;
		}
		CTX_DATA_END;
	}
	
	/* if not yet found, try selected Objects... */
	if (found == 0) {
		/* search in selected objects context */
		CTX_DATA_BEGIN(C, Object*, ob, selected_objects) 
		{
			/* just use the first object we encounter (that isn't the active object) 
			 * and which fulfills the criteria for the object-target that we've got 
			 */
			if ( (ob != obact) &&
				 ((!only_curve) || (ob->type == OB_CURVE)) && 
				 ((!only_mesh) || (ob->type == OB_MESH)) )
			{
				/* set target */
				*tar_ob= ob;
				found= 1;
				
				/* perform some special operations on the target */
				if (only_curve) {
					/* Curve-Path option must be enabled for follow-path constraints to be able to work */
					Curve *cu= (Curve *)ob->data;
					cu->flag |= CU_PATH;
				}
				
				break;
			}
		}
		CTX_DATA_END;
	}
	
	/* if still not found, add a new empty to act as a target (if allowed) */
	if ((found == 0) && (add)) {
#if 0 // XXX old code to be fixed
		Base *base= BASACT, *newbase;
		Object *obt;
		
		obt= add_object(scene, OB_EMPTY);
		/* set layers OK */
		newbase= BASACT;
		newbase->lay= base->lay;
		obt->lay= newbase->lay;
		
		/* transform cent to global coords for loc */
		if (pchanact) {
			if (only_IK)
				VecMat4MulVecfl(obt->loc, ob->obmat, pchanact->pose_tail);
			else
				VecMat4MulVecfl(obt->loc, ob->obmat, pchanact->pose_head);
		}
		else
			VECCOPY(obt->loc, ob->obmat[3]);
		
		//set_constraint_nth_target(con, obt, "", 0);
		
		/* restore, add_object sets active */
		BASACT= base;
		base->flag |= SELECT;
#endif // XXX old code to be ported
	}
	
	/* return whether there's any target */
	return found;
}

/* used by add constraint operators to add the constraint required */
static int constraint_add_exec(bContext *C, wmOperator *op, ListBase *list)
{
	Scene *scene= CTX_data_scene(C);
    Object *ob = CTX_data_active_object(C);
	bPoseChannel *pchan= get_active_posechannel(ob);
	bConstraint *con;
	int type= RNA_enum_get(op->ptr, "type");
	int setTarget= RNA_boolean_get(op->ptr, "set_targets");
	
	/* create a new constraint of the type requried, and add it to the active/given constraints list */
	con = add_new_constraint(type);
	
	if (list) {
		bConstraint *coniter; 
		
		/* add new constraint to end of list of constraints before ensuring that it has a unique name 
		 * (otherwise unique-naming code will fail, since it assumes element exists in list)
		 */
		BLI_addtail(list, con);
		unique_constraint_name(con, list);
		
		/* if the target list is a list on some PoseChannel belonging to a proxy-protected 
		 * Armature layer, we must tag newly added constraints with a flag which allows them
		 * to persist after proxy syncing has been done
		 */
		if (proxylocked_constraints_owner(ob, pchan))
			con->flag |= CONSTRAINT_PROXY_LOCAL;
		
		/* make this constraint the active one 
		 * 	- since constraint was added at end of stack, we can just go 
		 * 	  through deactivating all previous ones
		 */
		con->flag |= CONSTRAINT_ACTIVE;
		for (coniter= con->prev; coniter; coniter= coniter->prev)
			coniter->flag &= ~CONSTRAINT_ACTIVE;
	}
	
	/* get the first selected object/bone, and make that the target
	 *	- apart from the buttons-window add buttons, we shouldn't add in this way
	 */
	if (setTarget) {
		Object *tar_ob= NULL;
		bPoseChannel *tar_pchan= NULL;
		
		/* get the target objects, adding them as need be */
		if (get_new_constraint_target(C, type, &tar_ob, &tar_pchan, 1)) {
			/* method of setting target depends on the type of target we've got 
			 *	- by default, just set the first target (distinction here is only for multiple-targetted constraints)
			 */
			if (tar_pchan)
				set_constraint_nth_target(con, tar_ob, tar_pchan->name, 0);
			else
				set_constraint_nth_target(con, tar_ob, "", 0);
		}
	}
	
	/* do type-specific tweaking to the constraint settings  */
	switch (type) {
		case CONSTRAINT_TYPE_CHILDOF:
		{
			/* if this constraint is being added to a posechannel, make sure
			 * the constraint gets evaluated in pose-space */
			if (ob->flag & OB_POSEMODE) {
				con->ownspace = CONSTRAINT_SPACE_POSE;
				con->flag |= CONSTRAINT_SPACEONCE;
			}
		}
			break;
			
		case CONSTRAINT_TYPE_PYTHON: // FIXME: this code is not really valid anymore
		{
			char *menustr;
			int scriptint= 0;
#ifndef DISABLE_PYTHON
			/* popup a list of usable scripts */
			menustr = buildmenu_pyconstraints(NULL, &scriptint);
			scriptint = pupmenu(menustr);
			MEM_freeN(menustr);
			
			/* only add constraint if a script was chosen */
			if (scriptint) {
				/* add constraint */
				validate_pyconstraint_cb(con->data, &scriptint);
				
				/* make sure target allowance is set correctly */
				BPY_pyconstraint_update(ob, con);
			}
#endif
		}
		default:
			break;
	}
	
	/* make sure all settings are valid - similar to above checks, but sometimes can be wrong */
	object_test_constraints(ob);
	
	if (ob->pose)
		update_pose_constraint_flags(ob->pose);
	
	
	/* force depsgraph to get recalculated since new relationships added */
	DAG_scene_sort(scene);		/* sort order of objects */
	
	if ((ob->type==OB_ARMATURE) && (pchan)) {
		ob->pose->flag |= POSE_RECALC;	/* sort pose channels */
		DAG_object_flush_update(scene, ob, OB_RECALC_DATA|OB_RECALC_OB);
	}
	else
		DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
	
	/* notifiers for updates */
	WM_event_add_notifier(C, NC_OBJECT|ND_CONSTRAINT|NA_ADDED, ob);
	
	return OPERATOR_FINISHED;
}

/* ------------------ */

#if 0 // BUGGY
/* for object cosntraints, don't include NULL or IK for now */
static int object_constraint_add_invoke(bContext *C, wmOperator *op, wmEvent *evt)
{
	EnumPropertyItem *item;
	uiPopupMenu *pup;
	uiLayout *layout;
	int i, totitem;
	
	pup= uiPupMenuBegin(C, "Add Constraint", 0);
	layout= uiPupMenuLayout(pup);
	
	/* loop over the constraint-types as defined in the enum 
	 *	- code below is based on the code used for WM_menu_invoke()
	 */
	totitem= sizeof(&constraint_type_items[0]) / sizeof(EnumPropertyItem);
	item= constraint_type_items;
	 
	for (i=0; i < totitem; i++) {
		if (ELEM(item[i].value, CONSTRAINT_TYPE_NULL, CONSTRAINT_TYPE_KINEMATIC) == 0) {
			if (item[i].identifier[0])
				uiItemEnumO(layout, (char*)item[i].name, item[i].icon, "OBJECT_OT_constraint_add", "type", item[i].value);
			else
				uiItemS(layout);
		}
	}
	
	uiPupMenuEnd(C, pup);
}
#endif // BUGGY

/* dummy operator callback */
static int object_constraint_add_exec(bContext *C, wmOperator *op)
{
	ScrArea *sa= CTX_wm_area(C);
	Object *ob;
	
	if (sa->spacetype == SPACE_BUTS)
		ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	else
		ob= CTX_data_active_object(C);
	
	if (!ob)
		return OPERATOR_CANCELLED;

	return constraint_add_exec(C, op, &ob->constraints);
}

#if 0 // BUGGY
/* for bone constraints, don't include NULL for now */
static int pose_constraint_add_invoke(bContext *C, wmOperator *op, wmEvent *evt)
{
	EnumPropertyItem *item;
	uiPopupMenu *pup;
	uiLayout *layout;
	int i, totitem;
	
	pup= uiPupMenuBegin(C, "Add Constraint", 0);
	layout= uiPupMenuLayout(pup);
	
	/* loop over the constraint-types as defined in the enum 
	 *	- code below is based on the code used for WM_menu_invoke()
	 */
	totitem= sizeof(&constraint_type_items[0]) / sizeof(EnumPropertyItem);
	item= constraint_type_items;
	 
	for (i=0; i < totitem; i++) {
		// TODO: can add some other conditions here...
		if (item[i].value != CONSTRAINT_TYPE_NULL) {
			if (item[i].identifier[0])
				uiItemEnumO(layout, (char*)item[i].name, item[i].icon, "POSE_OT_constraint_add", "type", item[i].value);
			else
				uiItemS(layout);
		}
	}
	
	uiPupMenuEnd(C, pup);
}
#endif // BUGGY

/* dummy operator callback */
static int pose_constraint_add_exec(bContext *C, wmOperator *op)
{
	ScrArea *sa= CTX_wm_area(C);
	Object *ob;
	
	if (sa->spacetype == SPACE_BUTS)
		ob= CTX_data_pointer_get_type(C, "object", &RNA_Object).data;
	else
		ob= CTX_data_active_object(C);
	
	if (!ob)
		return OPERATOR_CANCELLED;
	
	return constraint_add_exec(C, op, get_active_constraints(ob));
}

void OBJECT_OT_constraint_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Constraint";
	ot->description = "Add a constraint to the active object.";
	ot->idname= "OBJECT_OT_constraint_add";
	
	/* api callbacks */
	ot->invoke= WM_menu_invoke;//object_constraint_add_invoke;
	ot->exec= object_constraint_add_exec;
	ot->poll= ED_operator_object_active;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* properties */
	RNA_def_enum(ot->srna, "type", constraint_type_items, 0, "Type", "");
	RNA_def_boolean(ot->srna, "set_targets", 0, "Set Targets", "Set target info for new constraints from context.");
}

void POSE_OT_constraint_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Constraint";
	ot->description = "Add a constraint to the active bone.";
	ot->idname= "POSE_OT_constraint_add";
	
	/* api callbacks */
	ot->invoke= WM_menu_invoke; //pose_constraint_add_invoke;
	ot->exec= pose_constraint_add_exec;
	ot->poll= ED_operator_posemode;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* properties */
	RNA_def_enum(ot->srna, "type", constraint_type_items, 0, "Type", "");
	RNA_def_boolean(ot->srna, "set_targets", 0, "Set Targets", "Set target info for new constraints from context.");
}

