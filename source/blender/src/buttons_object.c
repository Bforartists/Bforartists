/**
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#include <time.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "MEM_guardedalloc.h"

#include "DNA_ID.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"

#include "BKE_action.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_library.h"
#include "BKE_softbody.h"
#include "BKE_utildefines.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "BSE_filesel.h"
#include "BSE_headerbuttons.h"

#include "BIF_butspace.h"
#include "BIF_editaction.h"
#include "BIF_gl.h"
#include "BIF_glutil.h"
#include "BIF_graphics.h"
#include "BIF_interface.h"
#include "BIF_keyval.h"
#include "BIF_mainqueue.h"
#include "BIF_mywindow.h"
#include "BIF_poseobject.h"
#include "BIF_resources.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_toolbox.h"

#include "BDR_drawobject.h"
#include "BDR_editcurve.h"

#include "mydevice.h"
#include "blendef.h"

/* -----includes for this file specific----- */


#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_camera_types.h"
#include "DNA_constraint_types.h"
#include "DNA_curve_types.h"
#include "DNA_effect_types.h"
#include "DNA_group_types.h"
#include "DNA_image_types.h"
#include "DNA_key_types.h"
#include "DNA_lamp_types.h"
#include "DNA_lattice_types.h"
#include "DNA_material_types.h"
#include "DNA_meta_types.h"
#include "DNA_mesh_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_object_force.h"
#include "DNA_object_fluidsim.h"
#include "DNA_radio_types.h"
#include "DNA_screen_types.h"
#include "DNA_sound_types.h"
#include "DNA_texture_types.h"
#include "DNA_userdef_types.h"
#include "DNA_vfont_types.h"
#include "DNA_view3d_types.h"
#include "DNA_world_types.h"

#include "BKE_anim.h"
#include "BKE_armature.h"
#include "BKE_constraint.h"
#include "BKE_curve.h"
#include "BKE_deform.h"
#include "BKE_depsgraph.h"
#include "BKE_displist.h"
#include "BKE_effect.h"
#include "BKE_font.h"
#include "BKE_group.h"
#include "BKE_image.h"
#include "BKE_ipo.h"
#include "BKE_lattice.h"
#include "BKE_material.h"
#include "BKE_mball.h"
#include "BKE_mesh.h"
#include "BKE_modifier.h"
#include "BKE_object.h"
#include "BKE_sound.h"
#include "BKE_texture.h"
#include "BKE_utildefines.h"
#include "BKE_DerivedMesh.h"

#include "LBM_fluidsim.h"
#include "elbeem.h"

#include "BIF_editconstraint.h"
#include "BIF_editdeform.h"

#include "BSE_editipo.h"
#include "BSE_edit.h"

#include "BDR_editobject.h"

#include "butspace.h" // own module

static float prspeed=0.0;
float prlen=0.0;


/* ********************* CONSTRAINT ***************************** */

static void constraint_active_func(void *ob_v, void *con_v)
{
	Object *ob= ob_v;
	bConstraint *con;
	ListBase *lb;
	
	/* lets be nice and escape if its active already */
	if(con_v) {
		con= con_v;
		if(con->flag & CONSTRAINT_ACTIVE) return;
	}
	
	lb= get_active_constraints(ob);
	
	for(con= lb->first; con; con= con->next) {
		if(con==con_v) con->flag |= CONSTRAINT_ACTIVE;
		else con->flag &= ~CONSTRAINT_ACTIVE;
	}

	/* make sure ipowin and buttons shows it */
	if(ob->ipowin==ID_CO) {
		allqueue(REDRAWIPO, ID_CO);
		allspace(REMAKEIPO, 0);
		allqueue(REDRAWNLA, 0);
	}
	allqueue(REDRAWBUTSOBJECT, 0);
}

static void add_constraint_to_active(Object *ob, bConstraint *con)
{
	ListBase *list;
	
	list = get_active_constraints(ob);
	if (list) {
		unique_constraint_name(con, list);
		BLI_addtail(list, con);
		
		con->flag |= CONSTRAINT_ACTIVE;
		for(con= con->prev; con; con= con->prev)
			con->flag &= ~CONSTRAINT_ACTIVE;
	}
}

/* returns base ID for Ipo, sets actname to channel if appropriate */
/* should not make action... */
void get_constraint_ipo_context(void *ob_v, char *actname)
{
	Object *ob= ob_v;
	
	/* todo; check object if it has ob-level action ipo */
	
	if (ob->flag & OB_POSEMODE) {
		bPoseChannel *pchan;
		
		pchan = get_active_posechannel(ob);
		if (pchan) {
			BLI_strncpy(actname, pchan->name, 32);
		}
	}
	else if(ob->ipoflag & OB_ACTION_OB)
		strcpy(actname, "Object");
}	

/* initialize UI to show Ipo window and make sure channels etc exist */
static void enable_constraint_ipo_func (void *ob_v, void *con_v)
{
	Object *ob= ob_v;
	bConstraint *con = con_v;
	char actname[32]="";
	
	/* verifies if active constraint is set and shown in UI */
	constraint_active_func(ob_v, con_v);
	
	/* the context */
	get_constraint_ipo_context(ob, actname);
	
	/* adds ipo & channels & curve if needed */
	verify_ipo((ID *)ob, ID_CO, actname, con->name);
	
	/* make sure ipowin shows it */
	ob->ipowin= ID_CO;
	allqueue(REDRAWIPO, ID_CO);
	allspace(REMAKEIPO, 0);
	allqueue(REDRAWNLA, 0);
}


static void add_influence_key_to_constraint_func (void *ob_v, void *con_v)
{
	Object *ob= ob_v;
	bConstraint *con = con_v;
	IpoCurve *icu;
	char actname[32]="";
	
	/* verifies if active constraint is set and shown in UI */
	constraint_active_func(ob_v, con_v);
	
	/* the context */
	get_constraint_ipo_context(ob, actname);

	/* adds ipo & channels & curve if needed */
	icu= verify_ipocurve((ID *)ob, ID_CO, actname, con->name, CO_ENFORCE);

	if(ob->action)
		insert_vert_ipo(icu, get_action_frame(ob, (float)CFRA), con->enforce);
	else
		insert_vert_ipo(icu, CFRA, con->enforce);
	
	/* make sure ipowin shows it */
	ob->ipowin= ID_CO;
	allqueue(REDRAWIPO, ID_CO);
	allspace(REMAKEIPO, 0);
	allqueue(REDRAWNLA, 0);
	
	BIF_undo_push("Insert Influence Key");
}

void del_constr_func (void *ob_v, void *con_v)
{
	bConstraint *con= con_v;
	bConstraintChannel *chan;
	ListBase *lb;
	
	/* remove ipo channel */
	lb= get_active_constraint_channels(ob_v, 0);
	if(lb) {
		chan = get_constraint_channel(lb, con->name);
		if(chan) {
			if(chan->ipo) chan->ipo->id.us--;
			BLI_freelinkN(lb, chan);
		}
	}
	/* remove constraint itself */
	lb= get_active_constraints(ob_v);
	free_constraint_data (con);
	BLI_freelinkN(lb, con);
	
	constraint_active_func(ob_v, NULL);
}

static void del_constraint_func (void *ob_v, void *con_v)
{
	del_constr_func (ob_v, con_v);
	BIF_undo_push("Delete constraint");
	allqueue(REDRAWBUTSOBJECT, 0);
	allqueue(REDRAWIPO, 0); 
}

static void verify_constraint_name_func (void *ob_v, void *con_v)
{
	ListBase *conlist;
	bConstraint *con= con_v;
	
	if (!con)
		return;
	
	conlist = get_active_constraints(ob_v);
	unique_constraint_name (con, conlist);
	constraint_active_func(ob_v, con);

}

void get_constraint_typestring (char *str, void *con_v)
{
	bConstraint *con= con_v;

	switch (con->type){
	case CONSTRAINT_TYPE_CHILDOF:
		strcpy (str, "Child Of");
		return;
	case CONSTRAINT_TYPE_NULL:
		strcpy (str, "Null");
		return;
	case CONSTRAINT_TYPE_TRACKTO:
		strcpy (str, "Track To");
		return;
	case CONSTRAINT_TYPE_MINMAX:
		strcpy (str, "Floor");
		return;
	case CONSTRAINT_TYPE_KINEMATIC:
		strcpy (str, "IK Solver");
		return;
	case CONSTRAINT_TYPE_ROTLIKE:
		strcpy (str, "Copy Rotation");
		return;
	case CONSTRAINT_TYPE_LOCLIKE:
		strcpy (str, "Copy Location");
		return;
	case CONSTRAINT_TYPE_SIZELIKE:
		strcpy (str, "Copy Scale");
		return;
	case CONSTRAINT_TYPE_ACTION:
		strcpy (str, "Action");
		return;
	case CONSTRAINT_TYPE_LOCKTRACK:
		strcpy (str, "Locked Track");
		return;
	case CONSTRAINT_TYPE_FOLLOWPATH:
		strcpy (str, "Follow Path");
		return;
	case CONSTRAINT_TYPE_STRETCHTO:
		strcpy (str, "Stretch To");
		return;
	case CONSTRAINT_TYPE_LOCLIMIT:
		strcpy (str, "Limit Location");
		return;
	case CONSTRAINT_TYPE_ROTLIMIT:
		strcpy (str, "Limit Rotation");
		return;
	case CONSTRAINT_TYPE_SIZELIMIT:
		strcpy (str, "Limit Scale");
		return;
	default:
		strcpy (str, "Unknown");
		return;
	}
}

static int get_constraint_col(bConstraint *con)
{
	switch (con->type) {
	case CONSTRAINT_TYPE_NULL:
		return TH_BUT_NEUTRAL;
	case CONSTRAINT_TYPE_KINEMATIC:
		return TH_BUT_SETTING2;
	case CONSTRAINT_TYPE_TRACKTO:
		return TH_BUT_SETTING;
	case CONSTRAINT_TYPE_ROTLIKE:
		return TH_BUT_SETTING1;
	case CONSTRAINT_TYPE_LOCLIKE:
		return TH_BUT_POPUP;
	case CONSTRAINT_TYPE_MINMAX:
		return TH_BUT_POPUP;
	case CONSTRAINT_TYPE_SIZELIKE:
		return TH_BUT_POPUP;
	case CONSTRAINT_TYPE_ACTION:
		return TH_BUT_ACTION;
	case CONSTRAINT_TYPE_LOCKTRACK:
		return TH_BUT_SETTING;
	case CONSTRAINT_TYPE_FOLLOWPATH:
		return TH_BUT_SETTING2;
	case CONSTRAINT_TYPE_STRETCHTO:
		return TH_BUT_SETTING;
	case CONSTRAINT_TYPE_LOCLIMIT:
		return TH_BUT_POPUP;
	case CONSTRAINT_TYPE_ROTLIMIT:
		return TH_BUT_POPUP;
	case CONSTRAINT_TYPE_SIZELIMIT:
		return TH_BUT_POPUP;
	default:
		return TH_REDALERT;
	}
}

void const_moveUp(void *ob_v, void *con_v)
{
	bConstraint *con, *constr= con_v;
	ListBase *conlist;
	
	if(constr->prev) {
		conlist = get_active_constraints(ob_v);
		for(con= conlist->first; con; con= con->next) {
			if(con==constr) {
				BLI_remlink(conlist, con);
				BLI_insertlink(conlist, con->prev->prev, con);
				break;
			}
		}
	}
}

static void constraint_moveUp(void *ob_v, void *con_v)
{
	const_moveUp(ob_v, con_v);
	BIF_undo_push("Move constraint");
}

void const_moveDown(void *ob_v, void *con_v)
{
	bConstraint *con, *constr= con_v;
	ListBase *conlist;
	
	if(constr->next) {
		conlist = get_active_constraints(ob_v);
		for(con= conlist->first; con; con= con->next) {
			if(con==constr) {
				BLI_remlink(conlist, con);
				BLI_insertlink(conlist, con->next, con);
				break;
			}
		}
	}
}

static void constraint_moveDown(void *ob_v, void *con_v)
{
	const_moveDown(ob_v, con_v);
	BIF_undo_push("Move constraint");
}

/* autocomplete callback for  buttons */
void autocomplete_bone(char *str, void *arg_v)
{
	Object *ob= (Object *)arg_v;
	char truncate[40]= {0};
	
	if(ob==NULL || ob->pose==NULL) return;
	
	/* search if str matches the beginning of name */
	if(str[0]) {
		bPoseChannel *pchan;
		
		for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
			int a;
			
			for(a=0; a<31; a++) {
				if(str[a]==0 || str[a]!=pchan->name[a])
					break;
			}
			/* found a match */
			if(str[a]==0) {
				/* first match */
				if(truncate[0]==0)
					BLI_strncpy(truncate, pchan->name, 32);
				else {
					/* remove from truncate what is not in bone->name */
					for(a=0; a<31; a++) {
						if(truncate[a]!=pchan->name[a])
							truncate[a]= 0;
					}
				}
			}
		}
		if(truncate[0])
			BLI_strncpy(str, truncate, 32);
	}
}

/* autocomplete callback for buttons */
void autocomplete_vgroup(char *str, void *arg_v)
{
	Object *ob= (Object *)arg_v;
	char truncate[40]= {0};
	
	if(ob==NULL) return;
	
	/* search if str matches the beginning of a name */
	if(str[0]) {
		bDeformGroup *dg;
		
		for(dg= ob->defbase.first; dg; dg= dg->next) {
			int a;
			if(dg->name==str) continue;
			
			for(a=0; a<31; a++) {
				if(str[a]==0 || str[a]!=dg->name[a])
					break;
			}
			/* found a match */
			if(str[a]==0) {
				/* first match */
				if(truncate[0]==0)
					BLI_strncpy(truncate, dg->name, 32);
				else {
					/* remove from truncate what is not in bone->name */
					for(a=0; a<31; a++) {
						if(truncate[a]!=dg->name[a])
							truncate[a]= 0;
					}
				}
			}
		}
		if(truncate[0])
			BLI_strncpy(str, truncate, 32);
	}
}

static void draw_constraint (uiBlock *block, ListBase *list, bConstraint *con, short *xco, short *yco)
{
	Object *ob= OBACT, *target;
	uiBut *but;
	char typestr[64], *subtarget;
	short height, width = 265, is_armature_target;
	int curCol, rb_col;

	target= get_constraint_target(con, &subtarget);
	is_armature_target= (target && target->type==OB_ARMATURE);
	
	/* unless button has own callback, it adds this callback to button */
	uiBlockSetFunc(block, constraint_active_func, ob, con);
	
	get_constraint_typestring (typestr, con);

	curCol = get_constraint_col(con);

	/* Draw constraint header */
	uiBlockSetEmboss(block, UI_EMBOSSN);
	
	/* rounded header */
	rb_col= (con->flag & CONSTRAINT_ACTIVE)?40:20;
	uiDefBut(block, ROUNDBOX, B_DIFF, "", *xco-10, *yco-1, width+40, 22, NULL, 5.0, 0.0, 
			 (con->flag & CONSTRAINT_EXPAND)?3:15 , rb_col-20, ""); 
	
	/* open/close */
	uiDefIconButBitS(block, ICONTOG, CONSTRAINT_EXPAND, B_CONSTRAINT_TEST, ICON_DISCLOSURE_TRI_RIGHT, *xco-10, *yco, 20, 20, &con->flag, 0.0, 0.0, 0.0, 0.0, "Collapse/Expand Constraint");
	
	/* up down */
	uiBlockSetEmboss(block, UI_EMBOSS);
	but = uiDefIconBut(block, BUT, B_CONSTRAINT_TEST, VICON_MOVE_UP, *xco+width-50, *yco, 16, 18, NULL, 0.0, 0.0, 0.0, 0.0, "Move modifier up in stack");
	uiButSetFunc(but, constraint_moveUp, ob, con);
	
	but = uiDefIconBut(block, BUT, B_CONSTRAINT_TEST, VICON_MOVE_DOWN, *xco+width-50+20, *yco, 16, 18, NULL, 0.0, 0.0, 0.0, 0.0, "Move modifier down in stack");
	uiButSetFunc(but, constraint_moveDown, ob, con);
	
	if (con->flag & CONSTRAINT_EXPAND) {
		
		if (con->flag & CONSTRAINT_DISABLE) {
			BIF_ThemeColor(TH_REDALERT);
			uiBlockSetCol(block, TH_REDALERT);
		}
		else
			BIF_ThemeColor(curCol);

		/*if (type==TARGET_BONE)
			but = uiDefButC(block, MENU, B_CONSTRAINT_TEST, "Bone Constraint%t|Track To%x2|IK Solver%x3|Copy Rotation%x8|Copy Location%x9|Action%x12|Null%x0", *xco+20, *yco, 100, 20, &con->type, 0.0, 0.0, 0.0, 0.0, "Constraint type"); 
		else
			but = uiDefButC(block, MENU, B_CONSTRAINT_TEST, "Object Constraint%t|Track To%x2|Copy Rotation%x8|Copy Location%x9|Null%x0", *xco+20, *yco, 100, 20, &con->type, 0.0, 0.0, 0.0, 0.0, "Constraint type"); 
		*/
		uiBlockSetEmboss(block, UI_EMBOSS);
		
		uiDefBut(block, LABEL, B_CONSTRAINT_TEST, typestr, *xco+10, *yco, 100, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 
		
		but = uiDefBut(block, TEX, B_CONSTRAINT_TEST, "", *xco+120, *yco, 85, 18, con->name, 0.0, 29.0, 0.0, 0.0, "Constraint name"); 
		uiButSetFunc(but, verify_constraint_name_func, ob, con);
	}	
	else{
		uiBlockSetEmboss(block, UI_EMBOSSN);

		if (con->flag & CONSTRAINT_DISABLE) {
			uiBlockSetCol(block, TH_REDALERT);
			BIF_ThemeColor(TH_REDALERT);
		}
		else
			BIF_ThemeColor(curCol);
		
		uiDefBut(block, LABEL, B_CONSTRAINT_TEST, typestr, *xco+10, *yco, 100, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 
		
		uiDefBut(block, LABEL, B_CONSTRAINT_TEST, con->name, *xco+120, *yco-1, 135, 19, NULL, 0.0, 0.0, 0.0, 0.0, ""); 
	}

	uiBlockSetCol(block, TH_AUTO);	
	
	uiBlockSetEmboss(block, UI_EMBOSSN);
	
	but = uiDefIconBut(block, BUT, B_CONSTRAINT_CHANGETARGET, ICON_X, *xco+262, *yco, 19, 19, list, 0.0, 0.0, 0.0, 0.0, "Delete constraint");
	uiButSetFunc(but, del_constraint_func, ob, con);

	uiBlockSetEmboss(block, UI_EMBOSS);


	/* Draw constraint data*/
	if (!(con->flag & CONSTRAINT_EXPAND)) {
		(*yco)-=21;
	}
	else {
		switch (con->type){
		case CONSTRAINT_TYPE_ACTION:
			{
				bActionConstraint *data = con->data;

				height = 88;
				uiDefBut(block, ROUNDBOX, B_DIFF, "", *xco-10, *yco-height, width+40,height-1, NULL, 5.0, 0.0, 12, rb_col, ""); 
				
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Target:", *xco+65, *yco-24, 50, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 

				/* Draw target parameters */
				uiBlockBeginAlign(block);
				uiDefIDPoinBut(block, test_obpoin_but, ID_OB, B_CONSTRAINT_CHANGETARGET, "OB:", *xco+120, *yco-24, 135, 18, &data->tar, "Target Object"); 

				if (is_armature_target){
					but= uiDefBut(block, TEX, B_CONSTRAINT_CHANGETARGET, "BO:", *xco+120, *yco-42,135,18, &data->subtarget, 0, 24, 0, 0, "Subtarget Bone");
					uiButSetCompleteFunc(but, autocomplete_bone, (void *)data->tar);
				}
				else
					strcpy (data->subtarget, "");
				uiBlockEndAlign(block);

				/* Draw action button */
				uiBlockBeginAlign(block);
				uiDefButS(block, TOG, B_CONSTRAINT_TEST, "Local",						*xco+((width/2)-117), *yco-46, 78, 18, &data->local, 0, 0, 0, 0, "Use true local rotation difference");
				uiDefIDPoinBut(block, test_actionpoin_but, ID_AC, B_CONSTRAINT_TEST, "AC:",	*xco+((width/2)-117), *yco-64, 78, 18, &data->act, "Action containing the keyed motion for this bone"); 
				uiDefButS(block, MENU, B_CONSTRAINT_TEST, "Key on%t|X Rot%x0|Y Rot%x1|Z Rot%x2", *xco+((width/2)-117), *yco-84, 78, 18, &data->type, 0, 24, 0, 0, "Specify which transformation channel from the target is used to key the action");

				uiBlockBeginAlign(block);
				uiDefButI(block, NUM, B_CONSTRAINT_TEST, "Start:", *xco+((width/2)-36), *yco-64, 78, 18, &data->start, 1, MAXFRAME, 0.0, 0.0, "Starting frame of the keyed motion"); 
				uiDefButI(block, NUM, B_CONSTRAINT_TEST, "End:", *xco+((width/2)-36), *yco-84, 78, 18, &data->end, 1, MAXFRAME, 0.0, 0.0, "Ending frame of the keyed motion"); 
				
				uiBlockBeginAlign(block);
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "Min:", *xco+((width/2)+45), *yco-64, 78, 18, &data->min, -180, 180, 0, 0, "Minimum value for target channel range");
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "Max:", *xco+((width/2)+45), *yco-84, 78, 18, &data->max, -180, 180, 0, 0, "Maximum value for target channel range");
				uiBlockEndAlign(block);
			}
			break;
		case CONSTRAINT_TYPE_LOCLIKE:
			{
				bLocateLikeConstraint *data = con->data;
				
				height = 66;
				uiDefBut(block, ROUNDBOX, B_DIFF, "", *xco-10, *yco-height, width+40,height-1, NULL, 5.0, 0.0, 12, rb_col, ""); 

				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Target:", *xco+65, *yco-24, 50, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 

				/* Draw target parameters */
				uiBlockBeginAlign(block);
				uiDefIDPoinBut(block, test_obpoin_but, ID_OB, B_CONSTRAINT_CHANGETARGET, "OB:", *xco+120, *yco-24, 135, 18, &data->tar, "Target Object"); 

				if (is_armature_target) {
					but= uiDefBut(block, TEX, B_CONSTRAINT_CHANGETARGET, "BO:", *xco+120, *yco-42,135,18, &data->subtarget, 0, 24, 0, 0, "Subtarget Bone");
					uiButSetCompleteFunc(but, autocomplete_bone, (void *)data->tar);
				}
				else
					strcpy (data->subtarget, "");
				uiBlockEndAlign(block);
				
				/* Draw XYZ toggles */
				uiBlockBeginAlign(block);
				if (is_armature_target)
					uiDefButBitS(block, TOG, CONSTRAINT_LOCAL, B_CONSTRAINT_TEST, "Local", *xco+((width/2)-98), *yco-64, 50, 18, &con->flag, 0, 24, 0, 0, "Work on a Pose's local transform");
				but=uiDefButBitI(block, TOG, LOCLIKE_X, B_CONSTRAINT_TEST, "X", *xco+((width/2)-48), *yco-64, 32, 18, &data->flag, 0, 24, 0, 0, "Copy X component");
				but=uiDefButBitI(block, TOG, LOCLIKE_Y, B_CONSTRAINT_TEST, "Y", *xco+((width/2)-16), *yco-64, 32, 18, &data->flag, 0, 24, 0, 0, "Copy Y component");
				but=uiDefButBitI(block, TOG, LOCLIKE_Z, B_CONSTRAINT_TEST, "Z", *xco+((width/2)+16), *yco-64, 32, 18, &data->flag, 0, 24, 0, 0, "Copy Z component");
				uiBlockEndAlign(block);
			}
			break;
		case CONSTRAINT_TYPE_ROTLIKE:
			{
				bRotateLikeConstraint *data = con->data;
				
				/* also old files stuff... version patch is too much code! */
				if(data->flag==0) data->flag = ROTLIKE_X|ROTLIKE_Y|ROTLIKE_Z;
				
				height = 66;
				uiDefBut(block, ROUNDBOX, B_DIFF, "", *xco-10, *yco-height, width+40,height-1, NULL, 5.0, 0.0, 12, rb_col, ""); 
				
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Target:", *xco+65, *yco-24, 50, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 

				/* Draw target parameters */
				uiBlockBeginAlign(block);
				uiDefIDPoinBut(block, test_obpoin_but, ID_OB, B_CONSTRAINT_CHANGETARGET, "OB:", *xco+120, *yco-24, 135, 18, &data->tar, "Target Object"); 

				if (is_armature_target) {
					but= uiDefBut(block, TEX, B_CONSTRAINT_CHANGETARGET, "BO:", *xco+120, *yco-42,135,18, &data->subtarget, 0, 24, 0, 0, "Subtarget Bone");
					uiButSetCompleteFunc(but, autocomplete_bone, (void *)data->tar);
				}
				else
					strcpy (data->subtarget, "");
				uiBlockEndAlign(block);
				
				/* Draw XYZ toggles */
				uiBlockBeginAlign(block);
				if (is_armature_target)
					uiDefButBitS(block, TOG, CONSTRAINT_LOCAL, B_CONSTRAINT_TEST, "Local", *xco+((width/2)-98), *yco-64, 50, 18, &con->flag, 0, 24, 0, 0, "Work on a Pose's local transform");
				uiDefButBitI(block, TOG, ROTLIKE_X, B_CONSTRAINT_TEST, "X", *xco+((width/2)-48), *yco-64, 32, 18, &data->flag, 0, 24, 0, 0, "Copy X component");
				uiDefButBitI(block, TOG, ROTLIKE_Y, B_CONSTRAINT_TEST, "Y", *xco+((width/2)-16), *yco-64, 32, 18, &data->flag, 0, 24, 0, 0, "Copy Y component");
				uiDefButBitI(block, TOG, ROTLIKE_Z, B_CONSTRAINT_TEST, "Z", *xco+((width/2)+16), *yco-64, 32, 18, &data->flag, 0, 24, 0, 0, "Copy Z component");
				uiBlockEndAlign(block);
			}
			break;
		case CONSTRAINT_TYPE_SIZELIKE:
			{
				bSizeLikeConstraint *data = con->data;
				height = 66;
			
				uiDefBut(block, ROUNDBOX, B_DIFF, "", *xco-10, *yco-height, width+40,height-1, NULL, 5.0, 0.0, 12, rb_col, ""); 

				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Target:", *xco+65, *yco-24, 50, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 

				/* Draw target parameters */
				uiBlockBeginAlign(block);
				uiDefIDPoinBut(block, test_obpoin_but, ID_OB, B_CONSTRAINT_CHANGETARGET, "OB:", *xco+120, *yco-24, 135, 18, &data->tar, "Target Object"); 
				
				if (is_armature_target) {
					but= uiDefBut(block, TEX, B_CONSTRAINT_CHANGETARGET, "BO:", *xco+120, *yco-42,135,18, &data->subtarget, 0, 24, 0, 0, "Subtarget Bone");
					uiButSetCompleteFunc(but, autocomplete_bone, (void *)data->tar);
				}
				else
					strcpy (data->subtarget, "");
				uiBlockEndAlign(block);

				/* Draw XYZ toggles */
				uiBlockBeginAlign(block);
				but=uiDefButI(block, TOG|BIT|0, B_CONSTRAINT_TEST, "X", *xco+((width/2)-48), *yco-64, 32, 18, &data->flag, 0, 24, 0, 0, "Copy X component");
				but=uiDefButI(block, TOG|BIT|1, B_CONSTRAINT_TEST, "Y", *xco+((width/2)-16), *yco-64, 32, 18, &data->flag, 0, 24, 0, 0, "Copy Y component");
				but=uiDefButI(block, TOG|BIT|2, B_CONSTRAINT_TEST, "Z", *xco+((width/2)+16), *yco-64, 32, 18, &data->flag, 0, 24, 0, 0, "Copy Z component");
				uiBlockEndAlign(block);
			}
 			break;
		case CONSTRAINT_TYPE_KINEMATIC:
			{
				bKinematicConstraint *data = con->data;
				
				height = 108;
				uiDefBut(block, ROUNDBOX, B_DIFF, "", *xco-10, *yco-height, width+40,height-1, NULL, 5.0, 0.0, 12, rb_col, ""); 
				
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Target:", *xco+65, *yco-24, 50, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 

				/* Draw target parameters */
				uiDefButBitS(block, TOG, CONSTRAINT_IK_ROT, B_CONSTRAINT_TEST, "Rot", *xco, *yco-24,60,19, &data->flag, 0, 0, 0, 0, "Chain follows rotation of target");
				
				uiBlockBeginAlign(block);
				uiDefIDPoinBut(block, test_obpoin_but, ID_OB, B_CONSTRAINT_CHANGETARGET, "OB:", *xco+120, *yco-24, 135, 19, &data->tar, "Target Object"); 

				if (is_armature_target) {
					but=uiDefBut(block, TEX, B_CONSTRAINT_CHANGETARGET, "BO:", *xco+120, *yco-42,135,19, &data->subtarget, 0, 24, 0, 0, "Subtarget Bone");
					uiButSetCompleteFunc(but, autocomplete_bone, (void *)data->tar);
				}
				else
					strcpy (data->subtarget, "");
	
				uiBlockBeginAlign(block);
				uiDefButBitS(block, TOG, CONSTRAINT_IK_TIP, B_CONSTRAINT_TEST, "Use Tip", *xco, *yco-64, 142, 19, &data->flag, 0, 0, 0, 0, "Include Bone's tip als last element in Chain");
				uiDefButI(block, NUM, B_CONSTRAINT_TEST, "ChainLen:", *xco+142, *yco-64,143,19, &data->rootbone, 0, 255, 0, 0, "If not zero, the amount of bones in this chain");
				
				uiBlockBeginAlign(block);
				uiDefButF(block, NUMSLI, B_CONSTRAINT_TEST, "PosW ", *xco, *yco-86, 142, 19, &data->weight, 0.01, 1.0, 2, 2, "For Tree-IK: weight of position control for this target");
				uiDefButF(block, NUMSLI, B_CONSTRAINT_TEST, "RotW ", *xco+142, *yco-86, 143, 19, &data->orientweight, 0.01, 1.0, 2, 2, "For Tree-IK: Weight of orientation control for this target");
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "Tolerance:", *xco, *yco-106, 142, 19, &data->tolerance, 0.0001f, 1.0, 0, 0, "Maximum distance to target after solving"); 
				uiDefButS(block, NUM, B_CONSTRAINT_TEST, "Iterations:", *xco+142, *yco-106, 143, 19, &data->iterations, 1, 10000, 0, 0, "Maximum number of solving iterations"); 
				
			}
			break;
		case CONSTRAINT_TYPE_TRACKTO:
			{
				bTrackToConstraint *data = con->data;

				height = 66;
				uiDefBut(block, ROUNDBOX, B_DIFF, "", *xco-10, *yco-height, width+40,height-1, NULL, 5.0, 0.0, 12, rb_col, ""); 
				
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Target:", *xco+65, *yco-24, 50, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 

				/* Draw target parameters */
				uiBlockBeginAlign(block);
				uiDefIDPoinBut(block, test_obpoin_but, ID_OB, B_CONSTRAINT_CHANGETARGET, "OB:", *xco+120, *yco-24, 135, 18, &data->tar, "Target Object"); 

				if (is_armature_target) {
					but=uiDefBut(block, TEX, B_CONSTRAINT_CHANGETARGET, "BO:", *xco+120, *yco-42,135,18, &data->subtarget, 0, 24, 0, 0, "Subtarget Bone");
					uiButSetCompleteFunc(but, autocomplete_bone, (void *)data->tar);
				}
				else
					strcpy (data->subtarget, "");
				uiBlockEndAlign(block);

				uiBlockBeginAlign(block);
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "To:", *xco+12, *yco-64, 25, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 
				
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"X",	*xco+39, *yco-64,17,18, &data->reserved1, 12.0, 0.0, 0, 0, "The axis that points to the target object");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"Y",	*xco+56, *yco-64,17,18, &data->reserved1, 12.0, 1.0, 0, 0, "The axis that points to the target object");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"Z",	*xco+73, *yco-64,17,18, &data->reserved1, 12.0, 2.0, 0, 0, "The axis that points to the target object");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"-X",	*xco+90, *yco-64,24,18, &data->reserved1, 12.0, 3.0, 0, 0, "The axis that points to the target object");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"-Y",	*xco+114, *yco-64,24,18, &data->reserved1, 12.0, 4.0, 0, 0, "The axis that points to the target object");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"-Z",	*xco+138, *yco-64,24,18, &data->reserved1, 12.0, 5.0, 0, 0, "The axis that points to the target object");
				uiBlockEndAlign(block);
				
				uiBlockBeginAlign(block);
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Up:", *xco+174, *yco-64, 30, 18, NULL, 0.0, 0.0, 0.0, 0.0, "");
				
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"X",	*xco+204, *yco-64,17,18, &data->reserved2, 13.0, 0.0, 0, 0, "The axis that points upward");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"Y",	*xco+221, *yco-64,17,18, &data->reserved2, 13.0, 1.0, 0, 0, "The axis that points upward");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"Z",	*xco+238, *yco-64,17,18, &data->reserved2, 13.0, 2.0, 0, 0, "The axis that points upward");
				uiBlockEndAlign(block);
			}
			break;
		case CONSTRAINT_TYPE_MINMAX:
			{
				bMinMaxConstraint *data = con->data;

				height = 66;
				uiDefBut(block, ROUNDBOX, B_DIFF, "", *xco-10, *yco-height, width+40,height-1, NULL, 5.0, 0.0, 12, rb_col, ""); 
				
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Target:", *xco+65, *yco-24, 50, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 

				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "Offset:", *xco, *yco-44, 100, 18, &data->offset, -100, 100, 100.0, 0.0, "Offset from the position of the object center"); 

				/* Draw target parameters */
				uiBlockBeginAlign(block);
				uiDefIDPoinBut(block, test_obpoin_but, ID_OB, B_CONSTRAINT_CHANGETARGET, "OB:", *xco+120, *yco-24, 135, 18, &data->tar, "Target Object"); 

				if (is_armature_target) {
					but=uiDefBut(block, TEX, B_CONSTRAINT_CHANGETARGET, "BO:", *xco+120, *yco-42,135,18, &data->subtarget, 0, 24, 0, 0, "Subtarget Bone");
					uiButSetCompleteFunc(but, autocomplete_bone, (void *)data->tar);
				}
				else
					strcpy (data->subtarget, "");
				uiBlockEndAlign(block);

				but=uiDefButBitS(block, TOG, 1, B_CONSTRAINT_TEST, "Sticky", *xco, *yco-24, 54, 18, &data->sticky, 0, 24, 0, 0, "Immobilize object while constrained");
				
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Max/Min:", *xco-8, *yco-64, 54, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 

				uiBlockBeginAlign(block);			
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"X",	*xco+51, *yco-64,17,18, &data->minmaxflag, 12.0, 0.0, 0, 0, "Will not pass below X of target");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"Y",	*xco+67, *yco-64,17,18, &data->minmaxflag, 12.0, 1.0, 0, 0, "Will not pass below Y of target");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"Z",	*xco+85, *yco-64,17,18, &data->minmaxflag, 12.0, 2.0, 0, 0, "Will not pass below Z of target");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"-X",	*xco+102, *yco-64,24,18, &data->minmaxflag, 12.0, 3.0, 0, 0, "Will not pass above X of target");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"-Y",	*xco+126, *yco-64,24,18, &data->minmaxflag, 12.0, 4.0, 0, 0, "Will not pass above Y of target");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"-Z",	*xco+150, *yco-64,24,18, &data->minmaxflag, 12.0, 5.0, 0, 0, "Will not pass above Z of target");
				uiBlockEndAlign(block);
			}
			break;
		case CONSTRAINT_TYPE_LOCKTRACK:
			{
				bLockTrackConstraint *data = con->data;
				height = 66;
				uiDefBut(block, ROUNDBOX, B_DIFF, "", *xco-10, *yco-height, width+40,height-1, NULL, 5.0, 0.0, 12, rb_col, ""); 

				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Target:", *xco+65, *yco-24, 50, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 

				/* Draw target parameters */
				uiBlockBeginAlign(block);
				uiDefIDPoinBut(block, test_obpoin_but, ID_OB, B_CONSTRAINT_CHANGETARGET, "OB:", *xco+120, *yco-24, 135, 18, &data->tar, "Target Object"); 

				if (is_armature_target) {
					but=uiDefBut(block, TEX, B_CONSTRAINT_CHANGETARGET, "BO:", *xco+120, *yco-42,135,18, &data->subtarget, 0, 24, 0, 0, "Subtarget Bone");
					uiButSetCompleteFunc(but, autocomplete_bone, (void *)data->tar);
				}
				else
					strcpy (data->subtarget, "");
				uiBlockEndAlign(block);
				
				uiBlockBeginAlign(block);
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "To:", *xco+12, *yco-64, 25, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 
				
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"X",	*xco+39, *yco-64,17,18, &data->trackflag, 12.0, 0.0, 0, 0, "The axis that points to the target object");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"Y",	*xco+56, *yco-64,17,18, &data->trackflag, 12.0, 1.0, 0, 0, "The axis that points to the target object");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"Z",	*xco+73, *yco-64,17,18, &data->trackflag, 12.0, 2.0, 0, 0, "The axis that points to the target object");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"-X",	*xco+90, *yco-64,24,18, &data->trackflag, 12.0, 3.0, 0, 0, "The axis that points to the target object");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"-Y",	*xco+114, *yco-64,24,18, &data->trackflag, 12.0, 4.0, 0, 0, "The axis that points to the target object");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"-Z",	*xco+138, *yco-64,24,18, &data->trackflag, 12.0, 5.0, 0, 0, "The axis that points to the target object");
				uiBlockEndAlign(block);
				
				uiBlockBeginAlign(block);
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Lock:", *xco+166, *yco-64, 38, 18, NULL, 0.0, 0.0, 0.0, 0.0, "");
				
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"X",	*xco+204, *yco-64,17,18, &data->lockflag, 13.0, 0.0, 0, 0, "The axis that is locked");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"Y",	*xco+221, *yco-64,17,18, &data->lockflag, 13.0, 1.0, 0, 0, "The axis that is locked");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"Z",	*xco+238, *yco-64,17,18, &data->lockflag, 13.0, 2.0, 0, 0, "The axis that is locked");
				uiBlockEndAlign(block);
			}
			break;
		case CONSTRAINT_TYPE_FOLLOWPATH:
			{
				bFollowPathConstraint *data = con->data;

				height = 66;
				uiDefBut(block, ROUNDBOX, B_DIFF, "", *xco-10, *yco-height, width+40,height-1, NULL, 5.0, 0.0, 12, rb_col, ""); 
				
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Target:", *xco+65, *yco-24, 50, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 

				/* Draw target parameters */
				uiDefIDPoinBut(block, test_obpoin_but, ID_OB, B_CONSTRAINT_CHANGETARGET, "OB:", *xco+120, *yco-24, 135, 18, &data->tar, "Target Object"); 
				
				/* Draw Curve Follow toggle */
				but=uiDefButBitI(block, TOG, 1, B_CONSTRAINT_TEST, "CurveFollow", *xco+39, *yco-44, 100, 18, &data->followflag, 0, 24, 0, 0, "Object will follow the heading and banking of the curve");

				/* Draw Offset number button */
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "Offset:", *xco+155, *yco-44, 100, 18, &data->offset, -MAXFRAMEF, MAXFRAMEF, 100.0, 0.0, "Offset from the position corresponding to the time frame"); 

				uiBlockBeginAlign(block);
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Fw:", *xco+12, *yco-64, 27, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 
				
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"X",	*xco+39, *yco-64,17,18, &data->trackflag, 12.0, 0.0, 0, 0, "The axis that points forward along the path");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"Y",	*xco+56, *yco-64,17,18, &data->trackflag, 12.0, 1.0, 0, 0, "The axis that points forward along the path");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"Z",	*xco+73, *yco-64,17,18, &data->trackflag, 12.0, 2.0, 0, 0, "The axis that points forward along the path");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"-X",	*xco+90, *yco-64,24,18, &data->trackflag, 12.0, 3.0, 0, 0, "The axis that points forward along the path");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"-Y",	*xco+114, *yco-64,24,18, &data->trackflag, 12.0, 4.0, 0, 0, "The axis that points forward along the path");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"-Z",	*xco+138, *yco-64,24,18, &data->trackflag, 12.0, 5.0, 0, 0, "The axis that points forward along the path");
				uiBlockEndAlign(block);
				
				uiBlockBeginAlign(block);
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Up:", *xco+174, *yco-64, 30, 18, NULL, 0.0, 0.0, 0.0, 0.0, "");
				
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"X",	*xco+204, *yco-64,17,18, &data->upflag, 13.0, 0.0, 0, 0, "The axis that points upward");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"Y",	*xco+221, *yco-64,17,18, &data->upflag, 13.0, 1.0, 0, 0, "The axis that points upward");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"Z",	*xco+238, *yco-64,17,18, &data->upflag, 13.0, 2.0, 0, 0, "The axis that points upward");
				uiBlockEndAlign(block);
			}
			break;
		case CONSTRAINT_TYPE_STRETCHTO:
			{
				bStretchToConstraint *data = con->data;
				
				height = 105;
				uiDefBut(block, ROUNDBOX, B_DIFF, "", *xco-10, *yco-height, width+40,height-1, NULL, 5.0, 0.0, 12, rb_col, ""); 
				
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Target:", *xco+65, *yco-24, 50, 18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 

				/* Draw target parameters */
				uiBlockBeginAlign(block);
				uiDefIDPoinBut(block, test_obpoin_but, ID_OB, B_CONSTRAINT_CHANGETARGET, "OB:", *xco+120, *yco-24, 135, 18, &data->tar, "Target Object"); 

				if (is_armature_target) {
					but=uiDefBut(block, TEX, B_CONSTRAINT_CHANGETARGET, "BO:", *xco+120, *yco-42,135,18, &data->subtarget, 0, 24, 0, 0, "Subtarget Bone");
					uiButSetCompleteFunc(but, autocomplete_bone, (void *)data->tar);
				}
				else
					strcpy (data->subtarget, "");
				uiBlockEndAlign(block);

				
				uiBlockBeginAlign(block);
				uiDefButF(block,BUTM,B_CONSTRAINT_TEST,"R",*xco, *yco-60,20,18,&(data->orglength),0.0,0,0,0,"Recalculate RLength");
				uiDefButF(block,NUM,B_CONSTRAINT_TEST,"Rest Length:",*xco+18, *yco-60,237,18,&(data->orglength),0.0,100,0.5,0.5,"Length at Rest Position");
				uiBlockEndAlign(block);

				uiDefButF(block,NUM,B_CONSTRAINT_TEST,"Volume Variation:",*xco+18, *yco-82,237,18,&(data->bulge),0.0,100,0.5,0.5,"Factor between volume variation and stretching");

				uiBlockBeginAlign(block);
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST, "Vol:",*xco+14, *yco-104,30,18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"XZ",	 *xco+44, *yco-104,30,18, &data->volmode, 12.0, 0.0, 0, 0, "Keep Volume: Scaling X & Z");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"X",	 *xco+74, *yco-104,20,18, &data->volmode, 12.0, 1.0, 0, 0, "Keep Volume: Scaling X");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"Z",	 *xco+94, *yco-104,20,18, &data->volmode, 12.0, 2.0, 0, 0, "Keep Volume: Scaling Z");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"NONE", *xco+114, *yco-104,50,18, &data->volmode, 12.0, 3.0, 0, 0, "Ignore Volume");
				uiBlockEndAlign(block);

				
				uiBlockBeginAlign(block);
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST,"Plane:",*xco+175, *yco-104,40,18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"X",	  *xco+215, *yco-104,20,18, &data->plane, 12.0, 0.0, 0, 0, "Keep X axis");
				uiDefButI(block, ROW,B_CONSTRAINT_TEST,"Z",	  *xco+235, *yco-104,20,18, &data->plane, 12.0, 2.0, 0, 0, "Keep Z axis");
				uiBlockEndAlign(block);
				}
			break;
		case CONSTRAINT_TYPE_LOCLIMIT:
			{
				bLocLimitConstraint *data = con->data;
				
				int togButWidth = 50;
				int textButWidth = ((width/2)-togButWidth);
				
				height = 118; 
				uiDefBut(block, ROUNDBOX, B_DIFF, "", *xco-10, *yco-height, width+40,height-1, NULL, 5.0, 0.0, 12, rb_col, ""); 
				
				/* Draw Pairs of LimitToggle+LimitValue */
				uiBlockBeginAlign(block); 
				uiDefButBitS(block, TOG, LIMIT_XMIN, B_CONSTRAINT_TEST, "minX", *xco, *yco-28, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use minimum x value"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", *xco+togButWidth, *yco-28, (textButWidth-5), 18, &(data->xmin), -1000, 1000, 0.1,0.5,"Lowest x value to allow"); 
				uiBlockEndAlign(block); 
				
				uiBlockBeginAlign(block); 
				uiDefButBitS(block, TOG, LIMIT_XMAX, B_CONSTRAINT_TEST, "maxX", *xco+(width-(textButWidth-5)-togButWidth), *yco-28, 50, 18, &data->flag, 0, 24, 0, 0, "Use maximum x value"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", *xco+(width-textButWidth-5), *yco-28, (textButWidth-5), 18, &(data->xmax), -1000, 1000, 0.1,0.5,"Highest x value to allow"); 
				uiBlockEndAlign(block); 
				
				uiBlockBeginAlign(block); 
				uiDefButBitS(block, TOG, LIMIT_YMIN, B_CONSTRAINT_TEST, "minY", *xco, *yco-50, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use minimum y value"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", *xco+togButWidth, *yco-50, (textButWidth-5), 18, &(data->ymin), -1000, 1000, 0.1,0.5,"Lowest y value to allow"); 
				uiBlockEndAlign(block);
				
				uiBlockBeginAlign(block); 
				uiDefButBitS(block, TOG, LIMIT_YMAX, B_CONSTRAINT_TEST, "maxY", *xco+(width-(textButWidth-5)-togButWidth), *yco-50, 50, 18, &data->flag, 0, 24, 0, 0, "Use maximum y value"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", *xco+(width-textButWidth-5), *yco-50, (textButWidth-5), 18, &(data->ymax), -1000, 1000, 0.1,0.5,"Highest y value to allow"); 
				uiBlockEndAlign(block); 
				
				uiBlockBeginAlign(block); 
				uiDefButBitS(block, TOG, LIMIT_ZMIN, B_CONSTRAINT_TEST, "minZ", *xco, *yco-72, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use minimum z value"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", *xco+togButWidth, *yco-72, (textButWidth-5), 18, &(data->zmin), -1000, 1000, 0.1,0.5,"Lowest z value to allow"); 
				uiBlockEndAlign(block);
				
				uiBlockBeginAlign(block); 
				uiDefButBitS(block, TOG, LIMIT_ZMAX, B_CONSTRAINT_TEST, "maxZ", *xco+(width-(textButWidth-5)-togButWidth), *yco-72, 50, 18, &data->flag, 0, 24, 0, 0, "Use maximum z value"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", *xco+(width-textButWidth-5), *yco-72, (textButWidth-5), 18, &(data->zmax), -1000, 1000, 0.1,0.5,"Highest z value to allow"); 
				uiBlockEndAlign(block);
				
				uiBlockBeginAlign(block);
				uiDefBut(block, LABEL, B_CONSTRAINT_TEST,"Co-ordinate Space:",*xco, *yco-100,150,18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 
				
				if (ob->type == OB_ARMATURE && (ob->flag & OB_POSEMODE))
					uiDefButBitS(block, TOG, CONSTRAINT_LOCAL, B_CONSTRAINT_TEST, "Local", *xco+160, *yco-100, 60, 18, &con->flag, 0, 24, 0, 0, "Limit locations relative to the bone's rest-position");
				else if (ob->parent != NULL)
					uiDefButBitS(block, TOG, LIMIT_NOPARENT, B_CONSTRAINT_TEST, "Local", *xco+160, *yco-100, 60, 18, &data->flag2, 0, 24, 0, 0, "Limit locations relative to parent, not origin/world");
				else 
					uiDefBut(block, LABEL, B_CONSTRAINT_TEST,"World",*xco+160, *yco-100,60,18, NULL, 0.0, 0.0, 0.0, 0.0, "Limit locations relative to origin/world"); 
				
				uiBlockEndAlign(block);
			}
			break;
		case CONSTRAINT_TYPE_ROTLIMIT:
			{
				bRotLimitConstraint *data = con->data;
				
				int normButWidth = (width/3);
				
				height = 118; 
				uiDefBut(block, ROUNDBOX, B_DIFF, "", *xco-10, *yco-height, width+40,height-1, NULL, 5.0, 0.0, 12, rb_col, ""); 
				
				/* Draw Pairs of LimitToggle+LimitValue */
				uiBlockBeginAlign(block); 
				uiDefButBitS(block, TOG, LIMIT_XROT, B_CONSTRAINT_TEST, "LimitX", *xco, *yco-28, normButWidth, 18, &data->flag, 0, 24, 0, 0, "Limit rotation on x-axis"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "min:", *xco+normButWidth, *yco-28, normButWidth, 18, &(data->xmin), -360, 360, 0.1,0.5,"Lowest x value to allow"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "max:", *xco+(normButWidth * 2), *yco-28, normButWidth, 18, &(data->xmax), -360, 360, 0.1,0.5,"Highest x value to allow"); 
				uiBlockEndAlign(block); 
				
				uiBlockBeginAlign(block); 
				uiDefButBitS(block, TOG, LIMIT_YROT, B_CONSTRAINT_TEST, "LimitY", *xco, *yco-50, normButWidth, 18, &data->flag, 0, 24, 0, 0, "Limit rotation on y-axis"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "min:", *xco+normButWidth, *yco-50, normButWidth, 18, &(data->ymin), -360, 360, 0.1,0.5,"Lowest y value to allow"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "max:", *xco+(normButWidth * 2), *yco-50, normButWidth, 18, &(data->ymax), -360, 360, 0.1,0.5,"Highest y value to allow"); 
				uiBlockEndAlign(block); 
				
				uiBlockBeginAlign(block); 
				uiDefButBitS(block, TOG, LIMIT_ZROT, B_CONSTRAINT_TEST, "LimitZ", *xco, *yco-72, normButWidth, 18, &data->flag, 0, 24, 0, 0, "Limit rotation on z-axis"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "min:", *xco+normButWidth, *yco-72, normButWidth, 18, &(data->zmin), -360, 360, 0.1,0.5,"Lowest z value to allow"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "max:", *xco+(normButWidth * 2), *yco-72, normButWidth, 18, &(data->zmax), -360, 360, 0.1,0.5,"Highest z value to allow"); 
				uiBlockEndAlign(block); 
				
				if (ob->type == OB_ARMATURE && (ob->flag & OB_POSEMODE)) {
					uiBlockBeginAlign(block);
					uiDefBut(block, LABEL, B_CONSTRAINT_TEST,"Co-ordinate Space:",*xco, *yco-100,150,18, NULL, 0.0, 0.0, 0.0, 0.0, ""); 
					uiDefButBitS(block, TOG, CONSTRAINT_LOCAL, B_CONSTRAINT_TEST, "Local", *xco+160, *yco-100, 60, 18, &con->flag, 0, 24, 0, 0, "Work on a Pose's local transform");
					uiBlockEndAlign(block);
				}
			}
			break;
		case CONSTRAINT_TYPE_SIZELIMIT:
			{
				bSizeLimitConstraint *data = con->data;
				
				int togButWidth = 50;
				int textButWidth = ((width/2)-togButWidth);
				
				height = 90; 
				uiDefBut(block, ROUNDBOX, B_DIFF, "", *xco-10, *yco-height, width+40,height-1, NULL, 5.0, 0.0, 12, rb_col, ""); 
				
				/* Draw Pairs of LimitToggle+LimitValue */
				uiBlockBeginAlign(block); 
				uiDefButBitS(block, TOG, LIMIT_XMIN, B_CONSTRAINT_TEST, "minX", *xco, *yco-28, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use minimum x value"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", *xco+togButWidth, *yco-28, (textButWidth-5), 18, &(data->xmin), 0.0001, 1000, 0.1,0.5,"Lowest x value to allow"); 
				uiBlockEndAlign(block); 

				uiBlockBeginAlign(block); 
				uiDefButBitS(block, TOG, LIMIT_XMAX, B_CONSTRAINT_TEST, "maxX", *xco+(width-(textButWidth-5)-togButWidth), *yco-28, 50, 18, &data->flag, 0, 24, 0, 0, "Use maximum x value"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", *xco+(width-textButWidth-5), *yco-28, (textButWidth-5), 18, &(data->xmax), 0.0001, 1000, 0.1,0.5,"Highest x value to allow"); 
				uiBlockEndAlign(block); 


				uiBlockBeginAlign(block); 
				uiDefButBitS(block, TOG, LIMIT_YMIN, B_CONSTRAINT_TEST, "minY", *xco, *yco-50, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use minimum y value"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", *xco+togButWidth, *yco-50, (textButWidth-5), 18, &(data->ymin), 0.0001, 1000, 0.1,0.5,"Lowest y value to allow"); 
				uiBlockEndAlign(block); 

				uiBlockBeginAlign(block); 
				uiDefButBitS(block, TOG, LIMIT_YMAX, B_CONSTRAINT_TEST, "maxY", *xco+(width-(textButWidth-5)-togButWidth), *yco-50, 50, 18, &data->flag, 0, 24, 0, 0, "Use maximum y value"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", *xco+(width-textButWidth-5), *yco-50, (textButWidth-5), 18, &(data->ymax), 0.0001, 1000, 0.1,0.5,"Highest y value to allow"); 
				uiBlockEndAlign(block); 


				uiBlockBeginAlign(block); 
				uiDefButBitS(block, TOG, LIMIT_ZMIN, B_CONSTRAINT_TEST, "minZ", *xco, *yco-72, togButWidth, 18, &data->flag, 0, 24, 0, 0, "Use minimum z value"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", *xco+togButWidth, *yco-72, (textButWidth-5), 18, &(data->zmin), 0.0001, 1000, 0.1,0.5,"Lowest z value to allow"); 
				uiBlockEndAlign(block); 

				uiBlockBeginAlign(block); 
				uiDefButBitS(block, TOG, LIMIT_ZMAX, B_CONSTRAINT_TEST, "maxZ", *xco+(width-(textButWidth-5)-togButWidth), *yco-72, 50, 18, &data->flag, 0, 24, 0, 0, "Use maximum z value"); 
				uiDefButF(block, NUM, B_CONSTRAINT_TEST, "", *xco+(width-textButWidth-5), *yco-72, (textButWidth-5), 18, &(data->zmax), 0.0001, 1000, 0.1,0.5,"Highest z value to allow"); 
				uiBlockEndAlign(block);
			}
			break;
		case CONSTRAINT_TYPE_NULL:
			{
				height = 17;
				uiDefBut(block, ROUNDBOX, B_DIFF, "", *xco-10, *yco-height, width+40,height-1, NULL, 5.0, 0.0, 12, rb_col, ""); 
				
			}
			break;
		default:
			height = 0;
			break;
		}

		(*yco)-=(24+height);
	}

	if (con->type!=CONSTRAINT_TYPE_NULL) {
		uiBlockBeginAlign(block);
		uiDefButF(block, NUMSLI, B_CONSTRAINT_INF, "Influence ", *xco, *yco, 197, 20, &(con->enforce), 0.0, 1.0, 0.0, 0.0, "Amount of influence this constraint will have on the final solution");
		but = uiDefBut(block, BUT, B_CONSTRAINT_TEST, "Show", *xco+200, *yco, 45, 20, 0, 0.0, 1.0, 0.0, 0.0, "Show constraint's ipo in the Ipo window, adds a channel if not there");
		/* If this is on an object or bone, add ipo channel the constraint */
		uiButSetFunc (but, enable_constraint_ipo_func, ob, con);
		but = uiDefBut(block, BUT, B_CONSTRAINT_TEST, "Key", *xco+245, *yco, 40, 20, 0, 0.0, 1.0, 0.0, 0.0, "Add an influence keyframe to the constraint");
		/* Add a keyframe to the influence IPO */
		uiButSetFunc (but, add_influence_key_to_constraint_func, ob, con);
		uiBlockEndAlign(block);
		(*yco)-=24;
	} else {
		(*yco)-=3;
	}
	
}

static uiBlock *add_constraintmenu(void *arg_unused)
{
	Object *ob= OBACT;
	uiBlock *block;
	ListBase *conlist;
	short yco= 0;
	
	conlist = get_active_constraints(ob);
	
	block= uiNewBlock(&curarea->uiblocks, "add_constraintmenu", UI_EMBOSSP, UI_HELV, curarea->win);

	uiDefBut(block, BUTM, B_CONSTRAINT_ADD_LOCLIKE,"Copy Location",		0, yco-=20, 160, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefBut(block, BUTM, B_CONSTRAINT_ADD_ROTLIKE,"Copy Rotation",		0, yco-=20, 160, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefBut(block, BUTM, B_CONSTRAINT_ADD_SIZELIKE,"Copy Scale",		0, yco-=20, 160, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, 120, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefBut(block, BUTM, B_CONSTRAINT_ADD_LOCLIMIT,"Limit Location",		0, yco-=20, 160, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefBut(block, BUTM, B_CONSTRAINT_ADD_ROTLIMIT,"Limit Rotation",		0, yco-=20, 160, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefBut(block, BUTM, B_CONSTRAINT_ADD_SIZELIMIT,"Limit Scale",			0, yco-=20, 160, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, 120, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefBut(block, BUTM, B_CONSTRAINT_ADD_TRACKTO,"Track To",		0, yco-=20, 160, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefBut(block, BUTM, B_CONSTRAINT_ADD_MINMAX,"Floor",		0, yco-=20, 160, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefBut(block, BUTM, B_CONSTRAINT_ADD_LOCKTRACK,"Locked Track",		0, yco-=20, 160, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefBut(block, BUTM, B_CONSTRAINT_ADD_FOLLOWPATH,"Follow Path",		0, yco-=20, 160, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, 120, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefBut(block, BUTM, B_CONSTRAINT_ADD_STRETCHTO,"Stretch To",		0, yco-=20, 160, 19, NULL, 0.0, 0.0, 1, 0, "");

	if (ob->flag & OB_POSEMODE) {
		uiDefBut(block, SEPR, 0, "",					0, yco-=6, 120, 6, NULL, 0.0, 0.0, 0, 0, "");
		
		uiDefBut(block, BUTM, B_CONSTRAINT_ADD_KINEMATIC,"IK Solver",		0, yco-=20, 160, 19, NULL, 0.0, 0.0, 1, 0, "");
		uiDefBut(block, BUTM, B_CONSTRAINT_ADD_ACTION,"Action",		0, yco-=20, 160, 19, NULL, 0.0, 0.0, 1, 0, "");
		
	}
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, 120, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefBut(block, BUTM, B_CONSTRAINT_ADD_NULL,"Null",		0, yco-=20, 160, 19, NULL, 0.0, 0.0, 1, 0, "");
	
	uiTextBoundsBlock(block, 50);
	uiBlockSetDirection(block, UI_DOWN);
		
	return block;
}

void do_constraintbuts(unsigned short event)
{
	Object *ob= OBACT;
	
	switch(event) {
	case B_CONSTRAINT_TEST:
		break;  // no handling
	case B_CONSTRAINT_INF:
		/* influence; do not execute actions for 1 dag_flush */
		if(ob->pose)
			ob->pose->flag |= (POSE_LOCKED|POSE_DO_UNLOCK);

	case B_CONSTRAINT_CHANGETARGET:
		if(ob->pose) ob->pose->flag |= POSE_RECALC;	// checks & sorts pose channels
		DAG_scene_sort(G.scene);
		break;
		
	case B_CONSTRAINT_ADD_NULL:
		{
			bConstraint *con;
			
			con = add_new_constraint(CONSTRAINT_TYPE_NULL);
			add_constraint_to_active(ob, con);

			BIF_undo_push("Add constraint");
		}
		break;
	case B_CONSTRAINT_ADD_KINEMATIC:
		{
			bConstraint *con;
			
			con = add_new_constraint(CONSTRAINT_TYPE_KINEMATIC);
			add_constraint_to_active(ob, con);

			BIF_undo_push("Add constraint");
		}
		break;
	case B_CONSTRAINT_ADD_TRACKTO:
		{
			bConstraint *con;

			con = add_new_constraint(CONSTRAINT_TYPE_TRACKTO);
			add_constraint_to_active(ob, con);

			BIF_undo_push("Add constraint");
		}
		break;
	case B_CONSTRAINT_ADD_MINMAX:
		{
			bConstraint *con;

			con = add_new_constraint(CONSTRAINT_TYPE_MINMAX);
			add_constraint_to_active(ob, con);

			BIF_undo_push("Add constraint");
		}
		break;
	case B_CONSTRAINT_ADD_ROTLIKE:
		{
			bConstraint *con;

			con = add_new_constraint(CONSTRAINT_TYPE_ROTLIKE);
			add_constraint_to_active(ob, con);

			BIF_undo_push("Add constraint");
		}
		break;
	case B_CONSTRAINT_ADD_LOCLIKE:
		{
			bConstraint *con;

			con = add_new_constraint(CONSTRAINT_TYPE_LOCLIKE);
			add_constraint_to_active(ob, con);

			BIF_undo_push("Add constraint");
		}
		break;
 	case B_CONSTRAINT_ADD_SIZELIKE:
 		{
 			bConstraint *con;
 
 			con = add_new_constraint(CONSTRAINT_TYPE_SIZELIKE);
			add_constraint_to_active(ob, con);
  
			BIF_undo_push("Add constraint");
		}
		break;
	case B_CONSTRAINT_ADD_ACTION:
		{
			bConstraint *con;

			con = add_new_constraint(CONSTRAINT_TYPE_ACTION);
			add_constraint_to_active(ob, con);

			BIF_undo_push("Add constraint");
		}
		break;
	case B_CONSTRAINT_ADD_LOCKTRACK:
		{
			bConstraint *con;

			con = add_new_constraint(CONSTRAINT_TYPE_LOCKTRACK);
			add_constraint_to_active(ob, con);

			BIF_undo_push("Add constraint");
		}
		break;
	case B_CONSTRAINT_ADD_FOLLOWPATH:
		{
			bConstraint *con;

			con = add_new_constraint(CONSTRAINT_TYPE_FOLLOWPATH);
			add_constraint_to_active(ob, con);

		}
		break;
	case B_CONSTRAINT_ADD_STRETCHTO:
		{
			bConstraint *con;
			con = add_new_constraint(CONSTRAINT_TYPE_STRETCHTO);
			add_constraint_to_active(ob, con);
				
			BIF_undo_push("Add constraint");
		}
		break;
	case B_CONSTRAINT_ADD_LOCLIMIT:
		{
			bConstraint *con;

			con = add_new_constraint(CONSTRAINT_TYPE_LOCLIMIT);
			add_constraint_to_active(ob, con);

			BIF_undo_push("Add constraint");
		}
		break;
	case B_CONSTRAINT_ADD_ROTLIMIT:
		{
			bConstraint *con;

			con = add_new_constraint(CONSTRAINT_TYPE_ROTLIMIT);
			add_constraint_to_active(ob, con);

			BIF_undo_push("Add constraint");
		}
		break;
	case B_CONSTRAINT_ADD_SIZELIMIT:
		{
			bConstraint *con;

			con = add_new_constraint(CONSTRAINT_TYPE_SIZELIMIT);
			add_constraint_to_active(ob, con);

			BIF_undo_push("Add constraint");
		}
		break;

	default:
		break;
	}

	object_test_constraints(ob);
	
	if(ob->pose) update_pose_constraint_flags(ob->pose);
	
	if(ob->type==OB_ARMATURE) DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA|OB_RECALC_OB);
	else DAG_object_flush_update(G.scene, ob, OB_RECALC_OB);
	
	allqueue (REDRAWVIEW3D, 0);
	allqueue (REDRAWBUTSOBJECT, 0);
}

void softbody_bake(Object *ob)
{
	Base *base;
	SoftBody *sb;
	ScrArea *sa;
	float frameleno= G.scene->r.framelen;
	int cfrao= CFRA, sfra=100000, efra=0;
	unsigned short event=0;
	short val;
	
	G.scene->r.framelen= 1.0;		// baking has to be in uncorrected time
	
	if(ob) {
		sb= ob->soft;
		sfra= MIN2(sfra, sb->sfra);
		efra= MAX2(efra, sb->efra);
		sbObjectToSoftbody(ob);	// put softbody in restposition, free bake
		ob->softflag |= OB_SB_BAKEDO;
	}
	else {
		for(base=G.scene->base.first; base; base= base->next) {
			if(TESTBASE(base)) {
				if(base->object->soft) {
					sb= base->object->soft;
					sfra= MIN2(sfra, sb->sfra);
					efra= MAX2(efra, sb->efra);
					sbObjectToSoftbody(base->object);	// put softbody in restposition, free bake
					base->object->softflag |= OB_SB_BAKEDO;
				}
			}
		}
	}
	
	CFRA= sfra;
	update_for_newframe_muted();	// put everything on this frame
	
	curarea->win_swap= 0;		// clean swapbuffers
	
	for(; CFRA <= efra; CFRA++) {
		set_timecursor(CFRA);
		
		update_for_newframe_muted();
		
		for(sa= G.curscreen->areabase.first; sa; sa= sa->next) {
			if(sa->spacetype == SPACE_VIEW3D) {
				scrarea_do_windraw(sa);
			}
		}
		screen_swapbuffers();
		
		while(qtest()) {
			
			event= extern_qread(&val);
			if(event==ESCKEY) break;
		}
		if(event==ESCKEY) break;
	}
	
	if(event==ESCKEY) {
		if(ob) 
			sbObjectToSoftbody(ob);	// free bake
		else {
			for(base=G.scene->base.first; base; base= base->next) {
				if(TESTBASE(base)) {
					if(base->object->soft) {
						sbObjectToSoftbody(base->object);	// free bake
					}
				}
			}
		}
	}
	
	/* restore */
	waitcursor(0);
	
	if(ob) 
		ob->softflag &= ~OB_SB_BAKEDO;
	else {
		for(base=G.scene->base.first; base; base= base->next)
			if(TESTBASE(base))
				if(base->object->soft)
					base->object->softflag &= ~OB_SB_BAKEDO;
	}
	
	CFRA= cfrao;
	G.scene->r.framelen= frameleno;
	update_for_newframe_muted();
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
}

// store processed path & file prefix for fluidsim bake directory
void fluidsimFilesel(char *selection)
{
	Object *ob = OBACT;
	char srcDir[FILE_MAXDIR+FILE_MAXFILE], srcFile[FILE_MAXFILE];
	char prefix[FILE_MAXFILE];
	char *srch, *srchSub, *srchExt, *lastFound;
	int isElbeemSurf = 0;

	// make prefix
	strcpy(srcDir, selection);
	BLI_splitdirstring(srcDir, srcFile);
	strcpy(prefix, srcFile);
	// check if this is a previously generated surface mesh file
	srch = strstr(prefix, "fluidsurface_");
	// TODO search from back...
	if(srch) {
		srchSub = strstr(prefix,"_preview_");
		if(!srchSub) srchSub = strstr(prefix,"_final_");
		srchExt = strstr(prefix,".gz.bobj");
		if(!srchExt) srchExt = strstr(prefix,".bobj");
		if(srchSub && srchExt) {
			*srch = '\0';
			isElbeemSurf = 1;
		}
	}
	if(!isElbeemSurf) {
		// try to remove suffix
		lastFound = NULL;
		srch = strchr(prefix, '.'); // search last . from extension
		while(srch) {
			lastFound = srch;
			if(srch) {
				srch++;
				srch = strchr(srch, '.');
			}
		}
		if(lastFound) {
			*lastFound = '\0';
		} 
	}

	if(ob->fluidsimSettings) {
		strcpy(ob->fluidsimSettings->surfdataPath, srcDir);
		//not necessary? strcat(ob->fluidsimSettings->surfdataPath, "/");
		strcat(ob->fluidsimSettings->surfdataPath, prefix);

		// redraw view & buttons...
		allqueue(REDRAWBUTSOBJECT, 0);
		allqueue(REDRAWVIEW3D, 0);
		DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA);
	}
}

void do_object_panels(unsigned short event)
{
	Object *ob;
	Effect *eff;
	
	ob= OBACT;

	switch(event) {
	case B_TRACKBUTS:
		ob= OBACT;
		DAG_object_flush_update(G.scene, ob, OB_RECALC_OB);
		allqueue(REDRAWVIEW3D, 0);
		break;
	case B_RECALCPATH:
		DAG_object_flush_update(G.scene, OBACT, OB_RECALC_DATA);
		allqueue(REDRAWVIEW3D, 0);
		break;
	case B_PRINTSPEED:
		ob= OBACT;
		if(ob) {
			float vec[3];
			CFRA++;
			do_ob_ipo(ob);
			where_is_object(ob);
			VECCOPY(vec, ob->obmat[3]);
			CFRA--;
			do_ob_ipo(ob);
			where_is_object(ob);
			VecSubf(vec, vec, ob->obmat[3]);
			prspeed= Normalise(vec);
			scrarea_queue_winredraw(curarea);
		}
		break;
	case B_PRINTLEN:
		ob= OBACT;
		if(ob && ob->type==OB_CURVE) {
			Curve *cu=ob->data;
			
			if(cu->path) prlen= cu->path->totdist; else prlen= -1.0;
			scrarea_queue_winredraw(curarea);
		} 
		break;
	case B_RELKEY:
		allspace(REMAKEIPO, 0);
		allqueue(REDRAWBUTSOBJECT, 0);
		allqueue(REDRAWBUTSEDIT, 0);
		allqueue(REDRAWIPO, 0);
		DAG_object_flush_update(G.scene, OBACT, OB_RECALC_DATA);
		break;
	case B_CURVECHECK:
		DAG_object_flush_update(G.scene, OBACT, OB_RECALC_DATA);
		allqueue(REDRAWVIEW3D, 0);
		break;
	
	case B_SOFTBODY_CHANGE:
		ob= OBACT;
		if(ob) {
			ob->softflag |= OB_SB_REDO;
			allqueue(REDRAWBUTSOBJECT, 0);
			allqueue(REDRAWVIEW3D, 0);
		}
		break;
	case B_SOFTBODY_DEL_VG:
		ob= OBACT;
		if(ob && ob->soft) {
			ob->soft->vertgroup= 0;
			ob->softflag |= OB_SB_REDO;
			allqueue(REDRAWBUTSOBJECT, 0);
			allqueue(REDRAWVIEW3D, 0);
		}
		break;
	case B_SOFTBODY_BAKE:
		ob= OBACT;
		if(ob && ob->soft) softbody_bake(ob);
		break;
	case B_SOFTBODY_BAKE_FREE:
		ob= OBACT;
		if(ob && ob->soft) sbObjectToSoftbody(ob);
		allqueue(REDRAWBUTSOBJECT, 0);
		allqueue(REDRAWVIEW3D, 0);
		break;
	case B_FLUIDSIM_BAKE:
		ob= OBACT;
		/* write config files (currently no simulation) */
		fluidsimBake(ob);
		break;
	case B_FLUIDSIM_MAKEPART:
		ob= OBACT;
		{
			PartEff *paf= NULL;
			/* prepare fluidsim particle display */
			// simplified delete effect, create new - recalc some particles...
			if(ob==NULL || ob->type!=OB_MESH) break;
			ob->fluidsimSettings->type = 0;
			// reset type, and init particle system once normally
			eff= ob->effect.first;
			//if((eff) && (eff->flag & SELECT)) { BLI_remlink(&ob->effect, eff); free_effect(eff); }
			if(!eff){ copy_act_effect(ob); DAG_scene_sort(G.scene); }
			paf = give_parteff(ob);
			paf->totpart = 1000; paf->sta = paf->end = 1.0; // generate some particles...
			build_particle_system(ob);
			
			ob->fluidsimSettings->type = OB_FLUIDSIM_PARTICLE;
		}
		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWBUTSOBJECT, 0);
		break;
	case B_FLUIDSIM_SELDIR: {
			ScrArea *sa = closest_bigger_area();
			ob= OBACT;
			/* choose dir for surface files */
			areawinset(sa->win);
			activate_fileselect(FILE_SPECIAL, "Select Directory", ob->fluidsimSettings->surfdataPath, fluidsimFilesel);
		}
		break;
	case B_FLUIDSIM_FORCEREDRAW:
		/* force redraw */
		allqueue(REDRAWBUTSOBJECT, 0);
		allqueue(REDRAWVIEW3D, 0);
		DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA);
		break;
	case B_GROUP_RELINK:
		group_relink_nla_objects(OBACT);
		allqueue(REDRAWVIEW3D, 0);
		break;
		
	default:
		if(event>=B_SELEFFECT && event<B_SELEFFECT+MAX_EFFECT) {
			ob= OBACT;
			if(ob) {
				int a=B_SELEFFECT;
				
				eff= ob->effect.first;
				while(eff) {
					if(event==a) eff->flag |= SELECT;
					else eff->flag &= ~SELECT;
					
					a++;
					eff= eff->next;
				}
				allqueue(REDRAWBUTSOBJECT, 0);
			}
		}
	}

}

static void do_add_groupmenu(void *arg, int event)
{
	Object *ob= OBACT;
	
	if(ob) {
		
		if(event== -1) {
			Group *group= add_group();
			add_to_group(group, ob);
		}
		else
			add_to_group(BLI_findlink(&G.main->group, event), ob);
			
		ob->flag |= OB_FROMGROUP;
		BASACT->flag |= OB_FROMGROUP;
		allqueue(REDRAWBUTSOBJECT, 0);
		allqueue(REDRAWVIEW3D, 0);
	}		
}

static uiBlock *add_groupmenu(void *arg_unused)
{
	uiBlock *block;
	Group *group;
	short yco= 0;
	char str[32];
	
	block= uiNewBlock(&curarea->uiblocks, "add_constraintmenu", UI_EMBOSSP, UI_HELV, curarea->win);
	uiBlockSetButmFunc(block, do_add_groupmenu, NULL);

	uiDefBut(block, BUTM, B_NOP, "ADD NEW",		0, 20, 160, 19, NULL, 0.0, 0.0, 1, -1, "");
	for(group= G.main->group.first; group; group= group->id.next, yco++) {
		if(group->id.lib) strcpy(str, "L  ");
		else strcpy(str, "   ");
		strcat(str, group->id.name+2);
		uiDefBut(block, BUTM, B_NOP, str,	0, -20*yco, 160, 19, NULL, 0.0, 0.0, 1, yco, "");
	}
	
	uiTextBoundsBlock(block, 50);
	uiBlockSetDirection(block, UI_DOWN);	
	
	return block;
}

static void group_ob_rem(void *gr_v, void *ob_v)
{
	Object *ob= OBACT;
	
	rem_from_group(gr_v, ob);
	if(find_group(ob)==NULL) {
		ob->flag &= ~OB_FROMGROUP;
		BASACT->flag &= ~OB_FROMGROUP;
	}
	allqueue(REDRAWBUTSOBJECT, 0);
	allqueue(REDRAWVIEW3D, 0);

}

static void group_local(void *gr_v, void *unused)
{
	Group *group= gr_v;
	
	group->id.lib= NULL;
	
	allqueue(REDRAWBUTSOBJECT, 0);
	allqueue(REDRAWVIEW3D, 0);
	
}

static void object_panel_object(Object *ob)
{
	uiBlock *block;
	uiBut *but;
	Group *group;
	int a=0, xco;
	
	block= uiNewBlock(&curarea->uiblocks, "object_panel_object", UI_EMBOSS, UI_HELV, curarea->win);
	if(uiNewPanel(curarea, block, "Object and Links", "Object", 0, 0, 318, 204)==0) return;
	
	if(ob->id.lib) uiSetButLock(1, "Can't edit library data");
	
	/* object name */
	uiBlockSetCol(block, TH_BUT_SETTING2);
	xco= std_libbuttons(block, 10, 180, 0, NULL, 0, ID_OB, 0, &ob->id, NULL, &(G.buts->menunr), B_OBALONE, B_OBLOCAL, 0, 0, B_KEEPDATA);
	uiBlockSetCol(block, TH_AUTO);
	
	/* parent */
	uiDefIDPoinBut(block, test_obpoin_but, ID_OB, B_OBJECTPANELPARENT, "Par:", xco+5, 180, 305-xco, 20, &ob->parent, "Parent Object"); 

	uiDefBlockBut(block, add_groupmenu, NULL, "Add to Group", 10,150,150,20, "Add Object to a new Group");

	/* all groups */
	uiBlockBeginAlign(block);
	for(group= G.main->group.first; group; group= group->id.next) {
		if(object_in_group(ob, group)) {
			xco= 160;
			
			but = uiDefBut(block, TEX, B_IDNAME, "GR:",	10, 120-a, 150, 20, group->id.name+2, 0.0, 19.0, 0, 0, "Displays Group name. Click to change.");
			uiButSetFunc(but, test_idbutton_cb, group->id.name, NULL);
			
			if(group->id.lib) {
				but= uiDefIconBut(block, BUT, B_NOP, ICON_PARLIB, 160, 120-a, 20, 20, NULL, 0.0, 0.0, 0.0, 0.0, "Make Group local");
				uiButSetFunc(but, group_local, group, NULL);
				xco= 180;
			}
			but = uiDefIconBut(block, BUT, B_NOP, VICON_X, xco, 120-a, 20, 20, NULL, 0.0, 0.0, 0.0, 0.0, "Remove Group membership");
			uiButSetFunc(but, group_ob_rem, group, ob);
			
			a+= 20;
		}
	}
}

static void object_panel_anim(Object *ob)
{
	uiBlock *block;
	char str[32];
	
	block= uiNewBlock(&curarea->uiblocks, "object_panel_anim", UI_EMBOSS, UI_HELV, curarea->win);
	if(uiNewPanel(curarea, block, "Anim settings", "Object", 320, 0, 318, 204)==0) return;
	
	if(ob->id.lib) uiSetButLock(1, "Can't edit library data");
	
	uiBlockBeginAlign(block);
	uiDefButS(block, ROW,B_TRACKBUTS,"TrackX",	24,180,59,19, &ob->trackflag, 12.0, 0.0, 0, 0, "Specify the axis that points to another object");
	uiDefButS(block, ROW,B_TRACKBUTS,"Y",		85,180,19,19, &ob->trackflag, 12.0, 1.0, 0, 0, "Specify the axis that points to another object");
	uiDefButS(block, ROW,B_TRACKBUTS,"Z",		104,180,19,19, &ob->trackflag, 12.0, 2.0, 0, 0, "Specify the axis that points to another object");
	uiDefButS(block, ROW,B_TRACKBUTS,"-X",		124,180,24,19, &ob->trackflag, 12.0, 3.0, 0, 0, "Specify the axis that points to another object");
	uiDefButS(block, ROW,B_TRACKBUTS,"-Y",		150,180,24,19, &ob->trackflag, 12.0, 4.0, 0, 0, "Specify the axis that points to another object");
	uiDefButS(block, ROW,B_TRACKBUTS,"-Z",		178,180,24,19, &ob->trackflag, 12.0, 5.0, 0, 0, "Specify the axis that points to another object");
	uiBlockBeginAlign(block);
	uiDefButS(block, ROW,REDRAWVIEW3D,"UpX",	226,180,45,19, &ob->upflag, 13.0, 0.0, 0, 0, "Specify the axis that points up");
	uiDefButS(block, ROW,REDRAWVIEW3D,"Y",		274,180,20,19, &ob->upflag, 13.0, 1.0, 0, 0, "Specify the axis that points up");
	uiDefButS(block, ROW,REDRAWVIEW3D,"Z",		298,180,19,19, &ob->upflag, 13.0, 2.0, 0, 0, "Specify the axis that points up");
	
	uiBlockBeginAlign(block);
	uiDefButBitS(block, TOG, OB_DRAWKEY, REDRAWVIEW3D, "Draw Key",		24,155,71,19, &ob->ipoflag, 0, 0, 0, 0, "Draw object as key position");
	uiDefButBitS(block, TOG, OB_DRAWKEYSEL, REDRAWVIEW3D, "Draw Key Sel",	97,155,81,19, &ob->ipoflag, 0, 0, 0, 0, "Limit the drawing of object keys");
	uiDefButBitS(block, TOG, OB_POWERTRACK, REDRAWVIEW3D, "Powertrack",		180,155,78,19, &ob->transflag, 0, 0, 0, 0, "Switch objects rotation off");
	uiDefButBitS(block, TOG, PARSLOW, 0, "SlowPar",					260,155,56,19, &ob->partype, 0, 0, 0, 0, "Create a delay in the parent relationship");
	uiBlockBeginAlign(block);
	
	uiDefButBitS(block, TOG, OB_DUPLIFRAMES, REDRAWVIEW3D, "DupliFrames",	24,130,89,20, &ob->transflag, 0, 0, 0, 0, "Make copy of object for every frame");
	uiDefButBitS(block, TOG, OB_DUPLIVERTS, REDRAWVIEW3D, "DupliVerts",		114,130,82,20, &ob->transflag, 0, 0, 0, 0, "Duplicate child objects on all vertices");
	uiDefButBitS(block, TOG, OB_DUPLIROT, REDRAWVIEW3D, "Rot",				200,130,31,20, &ob->transflag, 0, 0, 0, 0, "Rotate dupli according to vertnormal");
	uiDefButBitS(block, TOG, OB_DUPLINOSPEED, REDRAWVIEW3D, "No Speed",		234,130,82,20, &ob->transflag, 0, 0, 0, 0, "Set dupliframes to still, regardless of frame");
	
	uiDefButBitS(block, TOG, OB_DUPLIGROUP, REDRAWVIEW3D, "DupliGroup",		24,110,150,20, &ob->transflag, 0, 0, 0, 0, "Enable group instancing");
	uiDefIDPoinBut(block, test_grouppoin_but, ID_GR, B_GROUP_RELINK, "GR:",	174,110,142,20, &ob->dup_group, "Instance an existing group");

	uiBlockBeginAlign(block);
	/* DupSta and DupEnd are both shorts, so the maxframe is greater then their range
	just limit the buttons to the max short */
	uiDefButI(block, NUM, REDRAWVIEW3D, "DupSta:",		24,85,141,19, &ob->dupsta, 1.0, 32767, 0, 0, "Specify startframe for Dupliframes");
	uiDefButI(block, NUM, REDRAWVIEW3D, "DupOn:",		170,85,146,19, &ob->dupon, 1.0, 1500.0, 0, 0, "Specify the number of frames to use between DupOff frames");
	uiDefButI(block, NUM, REDRAWVIEW3D, "DupEnd",		24,65,140,19, &ob->dupend, 1.0, 32767, 0, 0, "Specify endframe for Dupliframes");
	uiDefButI(block, NUM, REDRAWVIEW3D, "DupOff",		171,65,145,19, &ob->dupoff, 0.0, 1500.0, 0, 0, "Specify recurring frames to exclude from the Dupliframes");
	uiBlockBeginAlign(block);
	uiDefButBitS(block, TOG, OB_OFFS_OB, REDRAWALL, "Offs Ob",			24,35,56,20, &ob->ipoflag, 0, 0, 0, 0, "Not functional at the moment!");
	uiDefButBitS(block, TOG, OB_OFFS_PARENT, REDRAWALL, "Offs Par",			82,35,56,20 , &ob->ipoflag, 0, 0, 0, 0, "Let the timeoffset work on the parent");
	uiDefButBitS(block, TOG, OB_OFFS_PARTICLE, REDRAWALL, "Offs Particle",		140,35,103,20, &ob->ipoflag, 0, 0, 0, 0, "Let the timeoffset work on the particle effect");
	
	uiBlockBeginAlign(block);
	uiDefButF(block, NUM, REDRAWALL, "TimeOffset:",			24,10,115,20, &ob->sf, -MAXFRAMEF, MAXFRAMEF, 100, 0, "Specify an offset in frames");
	uiDefBut(block, BUT, B_AUTOTIMEOFS, "Automatic Time",	139,10,104,20, 0, 0, 0, 0, 0, "Generate automatic timeoffset values for all selected frames");
	uiDefBut(block, BUT, B_PRINTSPEED,	"PrSpeed",			248,10,67,20, 0, 0, 0, 0, 0, "Print objectspeed");
	uiBlockEndAlign(block);
	
	sprintf(str, "%.4f", prspeed);
	uiDefBut(block, LABEL, 0, str,							247,35,63,31, NULL, 1.0, 0, 0, 0, "");
	
}

static void object_panel_draw(Object *ob)
{
	uiBlock *block;
	int xco, a, dx, dy;
	
	block= uiNewBlock(&curarea->uiblocks, "object_panel_draw", UI_EMBOSS, UI_HELV, curarea->win);
	if(uiNewPanel(curarea, block, "Draw", "Object", 640, 0, 318, 204)==0) return;
	
	if(ob->id.lib) uiSetButLock(1, "Can't edit library data");
	
	/* LAYERS */
	xco= 120;
	dx= 35;
	dy= 30;
	
	uiDefBut(block, LABEL, 0, "Layers",				10,170,100,20, NULL, 0, 0, 0, 0, "");
	
	uiBlockBeginAlign(block);
	for(a=0; a<5; a++)
		uiDefButBitI(block, TOG, 1<<a, B_OBLAY+a, "",	(short)(xco+a*(dx/2)), 180, (short)(dx/2), (short)(dy/2), &(BASACT->lay), 0, 0, 0, 0, "");
	for(a=0; a<5; a++)
		uiDefButBitI(block, TOG, 1<<(a+10), B_OBLAY+a+10, "",	(short)(xco+a*(dx/2)), 165, (short)(dx/2), (short)(dy/2), &(BASACT->lay), 0, 0, 0, 0, "");
	
	xco+= 7;
	uiBlockBeginAlign(block);
	for(a=5; a<10; a++)
		uiDefButBitI(block, TOG, 1<<a, B_OBLAY+a, "",	(short)(xco+a*(dx/2)), 180, (short)(dx/2), (short)(dy/2), &(BASACT->lay), 0, 0, 0, 0, "");
	for(a=5; a<10; a++)
		uiDefButBitI(block, TOG, 1<<(a+10), B_OBLAY+a+10, "",	(short)(xco+a*(dx/2)), 165, (short)(dx/2), (short)(dy/2), &(BASACT->lay), 0, 0, 0, 0, "");
	
	uiBlockEndAlign(block);
	
	uiDefBut(block, LABEL, 0, "Drawtype",						10,120,100,20, NULL, 0, 0, 0, 0, "");
	
	uiBlockBeginAlign(block);
	uiDefButC(block, ROW, REDRAWVIEW3D, "Shaded",	10,100,100, 20, &ob->dt, 0, OB_SHADED, 0, 0, "Draw active object shaded or textured");
	uiDefButC(block, ROW, REDRAWVIEW3D, "Solid",	10,80,100, 20, &ob->dt, 0, OB_SOLID, 0, 0, "Draw active object in solid");
	uiDefButC(block, ROW, REDRAWVIEW3D, "Wire",		10,60, 100, 20, &ob->dt, 0, OB_WIRE, 0, 0, "Draw active object in wireframe");
	uiDefButC(block, ROW, REDRAWVIEW3D, "Bounds",	10,40, 100, 20, &ob->dt, 0, OB_BOUNDBOX, 0, 0, "Only draw object with bounding box");
	uiBlockEndAlign(block);
	
	uiDefBut(block, LABEL, 0, "Draw Extra",							120,120,90,20, NULL, 0, 0, 0, 0, "");
	
	uiBlockBeginAlign(block);
	uiDefButBitC(block, TOG, OB_BOUNDBOX, REDRAWVIEW3D, "Bounds",				120, 100, 90, 20, &ob->dtx, 0, 0, 0, 0, "Displays the active object's bounds");
	uiDefButBitC(block, TOG, OB_DRAWNAME, REDRAWVIEW3D, "Name",		210, 100, 90, 20, &ob->dtx, 0, 0, 0, 0, "Displays the active object's name");
	
	uiDefButS(block, MENU, REDRAWVIEW3D, "Boundary Display%t|Box%x0|Sphere%x1|Cylinder%x2|Cone%x3|Polyheder%x4",
			  120, 80, 90, 20, &ob->boundtype, 0, 0, 0, 0, "Selects the boundary display type");
	uiDefButBitC(block, TOG, OB_AXIS, REDRAWVIEW3D, "Axis",			210, 80, 90, 20, &ob->dtx, 0, 0, 0, 0, "Displays the active object's centre and axis");
	
	uiDefButBitC(block, TOG, OB_TEXSPACE, REDRAWVIEW3D, "TexSpace",	120, 60, 90, 20, &ob->dtx, 0, 0, 0, 0, "Displays the active object's texture space");
	uiDefButBitC(block, TOG, OB_DRAWWIRE, REDRAWVIEW3D, "Wire",		210, 60, 90, 20, &ob->dtx, 0, 0, 0, 0, "Adds the active object's wireframe over solid drawing");
	
	uiDefButBitC(block, TOG, OB_DRAWTRANSP, REDRAWVIEW3D, "Transp",	120, 40, 90, 20, &ob->dtx, 0, 0, 0, 0, "Enables transparent materials for the active object (Mesh only)");
	uiDefButBitC(block, TOG, OB_DRAWXRAY, REDRAWVIEW3D, "X-ray",	210, 40, 90, 20, &ob->dtx, 0, 0, 0, 0, "Makes the active object draw in front of others");
	
}

void object_panel_constraint(char *context)
{
	uiBlock *block;
	Object *ob= OBACT;
	ListBase *conlist;
	bConstraint *curcon;
	short xco, yco;
	char str[64];
	
	block= uiNewBlock(&curarea->uiblocks, "object_panel_constraint", UI_EMBOSS, UI_HELV, curarea->win);
	if(uiNewPanel(curarea, block, "Constraints", context, 960, 0, 318, 204)==0) return;
	
	if(ob->id.lib) uiSetButLock(1, "Can't edit library data");
	
	/* this is a variable height panel, newpanel doesnt force new size on existing panels */
	/* so first we make it default height */
	uiNewPanelHeight(block, 204);
	
	if(G.obedit==OBACT) return;	// ??
	
	conlist = get_active_constraints(OBACT);
	
	if (conlist) {
		
		uiDefBlockBut(block, add_constraintmenu, NULL, "Add Constraint", 0, 190, 130, 20, "Add a new constraint");
		
		/* print active object or bone */
		str[0]= 0;
		if (ob->flag & OB_POSEMODE){
			bPoseChannel *pchan= get_active_posechannel(ob);
			if(pchan) sprintf(str, "To Bone: %s", pchan->name);
		}
		else {
			sprintf(str, "To Object: %s", ob->id.name+2);
		}
		uiDefBut(block, LABEL, 1, str,	150, 190, 150, 20, NULL, 0.0, 0.0, 0, 0, "Displays Active Object or Bone name");
		
		/* Go through the list of constraints and draw them */
		xco = 10;
		yco = 160;
		
		for (curcon = conlist->first; curcon; curcon=curcon->next) {
			/* hrms, the temporal constraint should not draw! */
			if(curcon->type==CONSTRAINT_TYPE_KINEMATIC) {
				bKinematicConstraint *data= curcon->data;
				if(data->flag & CONSTRAINT_IK_TEMP)
					continue;
			}
			/* Draw default constraint header */
			draw_constraint(block, conlist, curcon, &xco, &yco);	
		}
		
		if(yco < 0) uiNewPanelHeight(block, 204-yco);
		
	}
}

void do_effects_panels(unsigned short event)
{
	Object *ob;
	Base *base;
	Effect *eff, *effn;
	PartEff *paf;
	
	ob= OBACT;

	switch(event) {

    case B_AUTOTIMEOFS:
		auto_timeoffs();
		break;
	case B_FRAMEMAP:
		G.scene->r.framelen= G.scene->r.framapto;
		G.scene->r.framelen/= G.scene->r.images;
		allqueue(REDRAWALL, 0);
		break;
	case B_NEWEFFECT:
		if(ob) {
			if (BLI_countlist(&ob->effect)==MAX_EFFECT)
				error("Unable to add: effect limit reached");
			else
				copy_act_effect(ob);
		}
		DAG_scene_sort(G.scene);
		BIF_undo_push("New effect");
		allqueue(REDRAWBUTSOBJECT, 0);
		break;
	case B_DELEFFECT:
		if(ob==NULL || ob->type!=OB_MESH) break;
		eff= ob->effect.first;
		while(eff) {
			effn= eff->next;
			if(eff->flag & SELECT) {
				BLI_remlink(&ob->effect, eff);
				free_effect(eff);
				break;
			}
			eff= effn;
		}
		BIF_undo_push("Delete effect");
		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWBUTSOBJECT, 0);
		break;
	case B_NEXTEFFECT:
		if(ob==0 || ob->type!=OB_MESH) break;
		eff= ob->effect.first;
		while(eff) {
			if(eff->flag & SELECT) {
				if(eff->next) {
					eff->flag &= ~SELECT;
					eff->next->flag |= SELECT;
				}
				break;
			}
			eff= eff->next;
		}
		allqueue(REDRAWBUTSOBJECT, 0);
		break;
	case B_PREVEFFECT:
		if(ob==0 || ob->type!=OB_MESH) break;
		eff= ob->effect.first;
		while(eff) {
			if(eff->flag & SELECT) {
				if(eff->prev) {
					eff->flag &= ~SELECT;
					eff->prev->flag |= SELECT;
				}
				break;
			}
			eff= eff->next;
		}
		allqueue(REDRAWBUTSOBJECT, 0);
		break;
	case B_EFFECT_DEP:
		DAG_scene_sort(G.scene);
		/* no break, pass on */
	case B_CALCEFFECT:
		if(ob==NULL || ob->type!=OB_MESH) break;
		eff= ob->effect.first;
		while(eff) {
			if(eff->flag & SELECT) {
				if(eff->type==EFF_PARTICLE) build_particle_system(ob);
			}
			eff= eff->next;
		}
		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWBUTSOBJECT, 0);
		break;
	case B_PAF_SET_VG:
		
		paf= give_parteff(ob);
		if(paf) {
			bDeformGroup *dg= get_named_vertexgroup(ob, paf->vgroupname);
			if(dg)
				paf->vertgroup= get_defgroup_num(ob, dg)+1;
			else
				paf->vertgroup= 0;
			
			DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA);
			allqueue(REDRAWVIEW3D, 0);
		}
		break;
	case B_PAF_SET_VG1:
		
		paf= give_parteff(ob);
		if(paf) {
			bDeformGroup *dg= get_named_vertexgroup(ob, paf->vgroupname_v);
			if(dg)
				paf->vertgroup_v= get_defgroup_num(ob, dg)+1;
			else
				paf->vertgroup_v= 0;
			
			DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA);
			allqueue(REDRAWVIEW3D, 0);
		}
		break;
	case B_FIELD_DEP:
		/* do this before scene sort, that one checks for CU_PATH */
		if(ob->type==OB_CURVE && ob->pd->forcefield==PFIELD_GUIDE) {
			Curve *cu= ob->data;
			
			cu->flag |= (CU_PATH|CU_3D);
			do_curvebuts(B_CU3D);	/* all curves too */
		}
		DAG_scene_sort(G.scene);

		if(ob->type==OB_CURVE && ob->pd->forcefield==PFIELD_GUIDE)
			DAG_object_flush_update(G.scene, ob, OB_RECALC);
		else
			DAG_object_flush_update(G.scene, ob, OB_RECALC_OB);

		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWBUTSOBJECT, 0);
		break;
	case B_FIELD_CHANGE:
		DAG_object_flush_update(G.scene, ob, OB_RECALC_OB);
		allqueue(REDRAWVIEW3D, 0);
		break;
	case B_RECALCAL:
		if (G.vd==NULL)
			break;
		
		base= FIRSTBASE;
		while(base) {
			if(base->lay & G.vd->lay) {
				ob= base->object;
				eff= ob->effect.first;
				while(eff) {
					if(eff->flag & SELECT) {
						if(eff->type==EFF_PARTICLE) build_particle_system(ob);
					}
					eff= eff->next;
				}
			}
			base= base->next;
		}
		allqueue(REDRAWVIEW3D, 0);
		break;
	default:
		if(event>=B_SELEFFECT && event<B_SELEFFECT+MAX_EFFECT) {
			ob= OBACT;
			if(ob) {
				int a=B_SELEFFECT;
				
				eff= ob->effect.first;
				while(eff) {
					if(event==a) eff->flag |= SELECT;
					else eff->flag &= ~SELECT;
					
					a++;
					eff= eff->next;
				}
				allqueue(REDRAWBUTSOBJECT, 0);
			}
		}
	}

}

/* Panel for particle interaction settings */
static void object_panel_fields(Object *ob)
{
	uiBlock *block;

	block= uiNewBlock(&curarea->uiblocks, "object_panel_fields", UI_EMBOSS, UI_HELV, curarea->win);
	if(uiNewPanel(curarea, block, "Fields and Deflection", "Physics", 0, 0, 318, 204)==0) return;

	if(ob->id.lib) uiSetButLock(1, "Can't edit library data");
	
	/* should become button, option? */
	if(ob->pd==NULL) {
		ob->pd= MEM_callocN(sizeof(PartDeflect), "PartDeflect");
		/* and if needed, init here */
		ob->pd->pdef_sbdamp = 0.1f;
		ob->pd->pdef_sbift  = 0.2f;
		ob->pd->pdef_sboft  = 0.02f;
	}
	
	if(ob->pd) {
		PartDeflect *pd= ob->pd;
		char *menustr= MEM_mallocN(256, "temp string");
		char *tipstr="Choose field type";
		
		uiDefBut(block, LABEL, 0, "Fields",		10,180,140,20, NULL, 0.0, 0, 0, 0, "");
		
		/* setup menu button */
		sprintf(menustr, "Field Type%%t|None %%x0|Spherical %%x%d|Wind %%x%d|Vortex %%x%d|Curve Guide %%x%d", 
				PFIELD_FORCE, PFIELD_WIND, PFIELD_VORTEX, PFIELD_GUIDE);
		
		if(pd->forcefield==PFIELD_FORCE) tipstr= "Object center attracts or repels particles";
		else if(pd->forcefield==PFIELD_WIND) tipstr= "Constant force applied in direction of Object Z axis";
		else if(pd->forcefield==PFIELD_VORTEX) tipstr= "Particles swirl around Z-axis of the Object";
		else if(pd->forcefield==PFIELD_GUIDE) tipstr= "Use a Curve Path to guide particles";
		
		uiDefButS(block, MENU, B_FIELD_DEP, menustr,			10,160,140,20, &pd->forcefield, 0.0, 0.0, 0, 0, tipstr);
		MEM_freeN(menustr);
		
		if(pd->forcefield) {
			uiBlockBeginAlign(block);
			if(pd->forcefield == PFIELD_GUIDE) {
				uiDefButF(block, NUM, B_FIELD_CHANGE, "MinDist: ",	10,120,140,20, &pd->f_strength, 0.0, 1000.0, 10, 0, "The distance from which particles are affected fully.");
				uiDefButF(block, NUM, B_FIELD_CHANGE, "Fall-off: ",	10,100,140,20, &pd->f_power, 0.0, 10.0, 10, 0, "Falloff factor, between mindist and maxdist");
			}
			else {	
				uiDefButF(block, NUM, B_FIELD_CHANGE, "Strength: ",	10,110,140,20, &pd->f_strength, -1000, 1000, 10, 0, "Strength of force field");
				uiDefButF(block, NUM, B_FIELD_CHANGE, "Fall-off: ",	10,90,140,20, &pd->f_power, 0, 10, 10, 0, "Falloff power (real gravitational fallof = 2)");
			}
			
			uiBlockBeginAlign(block);
			uiDefButBitS(block, TOG, PFIELD_USEMAX, B_FIELD_CHANGE, "Use MaxDist",	10,60,140,20, &pd->flag, 0.0, 0, 0, 0, "Use a maximum distance for the field to work");
			uiDefButF(block, NUM, B_FIELD_CHANGE, "MaxDist: ",	10,40,140,20, &pd->maxdist, 0, 1000.0, 10, 0, "Maximum distance for the field to work");
			uiBlockEndAlign(block);
			
			if(pd->forcefield == PFIELD_GUIDE)
				uiDefButBitS(block, TOG, PFIELD_GUIDE_PATH_ADD, B_FIELD_CHANGE, "Additive",	10,10,140,20, &pd->flag, 0.0, 0, 0, 0, "Based on distance/falloff it adds a portion of the entire path");
			
		}
		
		uiDefBut(block, LABEL, 0, "Deflection",	160,180,140,20, NULL, 0.0, 0, 0, 0, "");
			
		/* only meshes collide now */
		if(ob->type==OB_MESH) {
			uiDefButBitS(block, TOG, 1, B_REDR, "Deflection",160,160,150,20, &pd->deflect, 0, 0, 0, 0, "Deflects particles based on collision");
			if(pd->deflect) {
				uiDefBut(block, LABEL, 0, "Particles",			160,140,150,20, NULL, 0.0, 0, 0, 0, "");
				
				uiBlockBeginAlign(block);
				uiDefButF(block, NUM, B_DIFF, "Damping: ",		160,120,150,20, &pd->pdef_damp, 0.0, 1.0, 10, 0, "Amount of damping during particle collision");
				uiDefButF(block, NUM, B_DIFF, "Rnd Damping: ",	160,100,150,20, &pd->pdef_rdamp, 0.0, 1.0, 10, 0, "Random variation of damping");
				uiDefButF(block, NUM, B_DIFF, "Permeability: ",	160,80,150,20, &pd->pdef_perm, 0.0, 1.0, 10, 0, "Chance that the particle will pass through the mesh");
				uiBlockEndAlign(block);
				
				uiDefBut(block, LABEL, 0, "Soft Body",			160,60,150,20, NULL, 0.0, 0, 0, 0, "");

				uiBlockBeginAlign(block);
				uiDefButF(block, NUM, B_DIFF, "Damping:",	160,40,150,20, &pd->pdef_sbdamp, 0.0, 1.0, 10, 0, "Amount of damping during soft body collision");
				uiDefButF(block, NUM, B_DIFF, "Inner:",	160,20,150,20, &pd->pdef_sbift, 0.001, 1.0, 10, 0, "Inner face thickness");
				uiDefButF(block, NUM, B_DIFF, "Outer:",	160, 0,150,20, &pd->pdef_sboft, 0.001, 1.0, 10, 0, "Outer face thickness");
			}
		}		
	}
}


/* Panel for softbodies */
static void object_softbodies__enable(void *ob_v, void *arg2)
{
	Object *ob = ob_v;
	ModifierData *md = modifiers_findByType(ob, eModifierType_Softbody);

	if (modifiers_isSoftbodyEnabled(ob)) {
		if (md) {
			md->mode &= ~(eModifierMode_Render|eModifierMode_Realtime);
		}
	} else {
		if (!md) {
			md = modifier_new(eModifierType_Softbody);
			BLI_addhead(&ob->modifiers, md);
		}

		md->mode |= eModifierMode_Render|eModifierMode_Realtime;

		if (!ob->soft) {
			ob->soft= sbNew();
			ob->softflag |= OB_SB_GOAL|OB_SB_EDGES;
		}
	}

	allqueue(REDRAWBUTSEDIT, 0);
}

static void object_softbodies(Object *ob)
{
	uiBlock *block;
	
	block= uiNewBlock(&curarea->uiblocks, "object_softbodies", UI_EMBOSS, UI_HELV, curarea->win);
	if(uiNewPanel(curarea, block, "Soft Body", "Physics", 640, 0, 318, 204)==0) return;

	if(ob->id.lib) uiSetButLock(1, "Can't edit library data");
	
	/* do not allow to combine with force fields */
	/* if(ob->pd && ob->pd->deflect) { */
	/* no reason for that any more BM */
	if(0) {
		uiDefBut(block, LABEL, 0, "Object has Deflection,",		10,160,300,20, NULL, 0.0, 0, 0, 0, "");
		uiDefBut(block, LABEL, 0, "no Soft Body possible",		10,140,300,20, NULL, 0.0, 0, 0, 0, "");
	} else {
		static int val;
		uiBut *but;

		val = modifiers_isSoftbodyEnabled(ob);
		but = uiDefButI(block, TOG, REDRAWBUTSOBJECT, "Enable Soft Body",	10,200,150,20, &val, 0, 0, 0, 0, "Sets object to become soft body");
		uiButSetFunc(but, object_softbodies__enable, ob, NULL);
		uiDefBut(block, LABEL, 0, "",	160, 200,150,20, NULL, 0.0, 0.0, 0, 0, "");	// alignment reason
	}
	
	if(modifiers_isSoftbodyEnabled(ob)) {
		SoftBody *sb= ob->soft;
		int defCount;
		char *menustr;
		
		if(sb==NULL) {
			sb= ob->soft= sbNew();
			ob->softflag |= OB_SB_GOAL|OB_SB_EDGES;
		}
		
		uiDefButBitS(block, TOG, OB_SB_BAKESET, REDRAWBUTSOBJECT, "Bake settings",	180,200,130,20, &ob->softflag, 0, 0, 0, 0, "To convert simulation into baked (cached) result");
		
		if(sb->keys) uiSetButLock(1, "Soft Body is baked, free it first");
		
		if(ob->softflag & OB_SB_BAKESET) {
			uiBlockBeginAlign(block);
			uiDefButI(block, NUM, B_DIFF, "Start:",			10, 170,100,20, &sb->sfra, 1.0, 10000.0, 10, 0, "Start frame for baking");
			uiDefButI(block, NUM, B_DIFF, "End:",			110, 170,100,20, &sb->efra, 1.0, 10000.0, 10, 0, "End frame for baking");
			uiDefButI(block, NUM, B_DIFF, "Interval:",		210, 170,100,20, &sb->interval, 1.0, 10.0, 10, 0, "Interval in frames between baked keys");
			uiBlockEndAlign(block);
			
			uiDefButS(block, TOG, B_DIFF, "Local",			10, 145,100,20, &sb->local, 0.0, 0.0, 0, 0, "Use local coordinates for baking");
			
			uiClearButLock();
			uiBlockBeginAlign(block);
			
			if(sb->keys) {
				char str[128];
				uiDefIconTextBut(block, BUT, B_SOFTBODY_BAKE_FREE, ICON_X, "FREE BAKE", 10, 120,300,20, NULL, 0.0, 0.0, 0, 0, "Free baked result");
				sprintf(str, "Stored %d vertices %d keys %.3f MB", sb->totpoint, sb->totkey, ((float)16*sb->totpoint*sb->totkey)/(1024.0*1024.0));
				uiDefBut(block, LABEL, 0, str, 10, 100,300,20, NULL, 0.0, 0.0, 00, 0, "");
			}
			else				
				uiDefBut(block, BUT, B_SOFTBODY_BAKE, "BAKE",	10, 120,300,20, NULL, 0.0, 0.0, 10, 0, "Start baking. Press ESC to exit without baking");
		}
		else {
			/* GENERAL STUFF */
			uiBlockBeginAlign(block);
			uiDefButF(block, NUM, B_DIFF, "Friction:",		10, 170,150,20, &sb->mediafrict, 0.0, 10.0, 10, 0, "General media friction for point movements");
			uiDefButF(block, NUM, B_DIFF, "Mass:",			160, 170,150,20, &sb->nodemass , 0.001, 50.0, 10, 0, "Point Mass, the heavier the slower");
			uiDefButF(block, NUM, B_DIFF, "Grav:",			10,150,150,20, &sb->grav , 0.0, 10.0, 10, 0, "Apply gravitation to point movement");
			uiDefButF(block, NUM, B_DIFF, "Speed:",			160,150,150,20, &sb->physics_speed , 0.01, 100.0, 10, 0, "Tweak timing for physics to control frequency and speed");
			uiDefButF(block, NUM, B_DIFF, "Error Limit:",	10,130,150,20, &sb->rklimit , 0.01, 1.0, 10, 0, "The Runge-Kutta ODE solver error limit, low value gives more precision");
			uiBlockEndAlign(block);
			
			/* GOAL STUFF */
			uiBlockBeginAlign(block);
			uiDefButBitS(block, TOG, OB_SB_GOAL, B_SOFTBODY_CHANGE, "Use Goal",	10,100,130,20, &ob->softflag, 0, 0, 0, 0, "Define forces for vertices to stick to animated position");
			
			if(ob->type==OB_MESH) {
				menustr= get_vertexgroup_menustr(ob);
				defCount=BLI_countlist(&ob->defbase);
				if(defCount==0) sb->vertgroup= 0;
				uiDefButS(block, MENU, B_SOFTBODY_CHANGE, menustr,	140,100,20,20, &sb->vertgroup, 0, defCount, 0, 0, "Browses available vertex groups");
				MEM_freeN (menustr);

				if(sb->vertgroup) {
					bDeformGroup *defGroup = BLI_findlink(&ob->defbase, sb->vertgroup-1);
					if(defGroup)
						uiDefBut(block, BUT, B_DIFF, defGroup->name,	160,100,130,20, NULL, 0.0, 0.0, 0, 0, "Name of current vertex group");
					else
						uiDefBut(block, BUT, B_DIFF, "(no group)",	160,100,130,20, NULL, 0.0, 0.0, 0, 0, "Vertex Group doesn't exist anymore");
					uiDefIconBut(block, BUT, B_SOFTBODY_DEL_VG, ICON_X, 290,100,20,20, 0, 0, 0, 0, 0, "Disable use of vertex group");
				}
				else
					uiDefButF(block, NUM, B_SOFTBODY_CHANGE, "Goal:",	160,100,150,20, &sb->defgoal, 0.0, 1.0, 10, 0, "Default Goal (vertex target position) value, when no Vertex Group used");
			}
			else {
				uiDefButS(block, TOG, B_SOFTBODY_CHANGE, "W",			140,100,20,20, &sb->vertgroup, 0, 1, 0, 0, "Use control point weight values");
				uiDefButF(block, NUM, B_SOFTBODY_CHANGE, "Goal:",	160,100,150,20, &sb->defgoal, 0.0, 1.0, 10, 0, "Default Goal (vertex target position) value, when no Vertex Group used");
			}

			uiDefButF(block, NUM, B_DIFF, "G Stiff:",	10,80,150,20, &sb->goalspring, 0.0, 0.999, 10, 0, "Goal (vertex target position) spring stiffness");
			uiDefButF(block, NUM, B_DIFF, "G Damp:",	160,80,150,20, &sb->goalfrict  , 0.0, 10.0, 10, 0, "Goal (vertex target position) friction");
			uiDefButF(block, NUM, B_SOFTBODY_CHANGE, "G Min:",		10,60,150,20, &sb->mingoal, 0.0, 1.0, 10, 0, "Goal minimum, vertex group weights are scaled to match this range");
			uiDefButF(block, NUM, B_SOFTBODY_CHANGE, "G Max:",		160,60,150,20, &sb->maxgoal, 0.0, 1.0, 10, 0, "Goal maximum, vertex group weights are scaled to match this range");
			uiBlockEndAlign(block);
			
			/* EDGE SPRING STUFF */
			if(ob->type!=OB_SURF) {
				uiBlockBeginAlign(block);
				uiDefButBitS(block, TOG, OB_SB_EDGES, B_SOFTBODY_CHANGE, "Use Edges",		10,30,150,20, &ob->softflag, 0, 0, 0, 0, "Use Edges as springs");
				uiDefButBitS(block, TOG, OB_SB_QUADS, B_SOFTBODY_CHANGE, "Stiff Quads",		160,30,150,20, &ob->softflag, 0, 0, 0, 0, "Adds diagonal springs on 4-gons");
				uiDefButF(block, NUM, B_DIFF, "E Stiff:",	10,10,150,20, &sb->inspring, 0.0,  0.999, 10, 0, "Edge spring stiffness");
				uiDefButF(block, NUM, B_DIFF, "E Damp:",	160,10,150,20, &sb->infrict, 0.0,  10.0, 10, 0, "Edge spring friction");
				uiBlockEndAlign(block);
			}
		}
	}
	uiBlockEndAlign(block);

}

static void object_panel_particles_motion(Object *ob)
{
	uiBlock *block;
	uiBut *but;
	PartEff *paf= give_parteff(ob);

	if (paf==NULL) return;
		
	block= uiNewBlock(&curarea->uiblocks, "object_panel_particles_motion", UI_EMBOSS, UI_HELV, curarea->win);
	uiNewPanelTabbed("Particles ", "Physics");
	if(uiNewPanel(curarea, block, "Particle Motion", "Physics", 320, 0, 318, 204)==0) return;
	
	if(ob->id.lib) uiSetButLock(1, "Can't edit library data");
	
	/* top row */
	uiBlockBeginAlign(block);
	uiDefButI(block, NUM, B_CALCEFFECT, "Keys:",	0,180,75,20, &paf->totkey, 1.0, 100.0, 0, 0, "Specify the number of key positions");
	uiDefButBitS(block, TOG, PAF_BSPLINE, B_CALCEFFECT, "Bspline",	75,180,75,20, &paf->flag, 0, 0, 0, 0, "Use B spline formula for particle interpolation");
	uiDefButI(block, NUM, B_CALCEFFECT, "Seed:",	150,180,75,20, &paf->seed, 0.0, 255.0, 0, 0, "Set an offset in the random table");
	uiDefButF(block, NUM, B_CALCEFFECT, "RLife:",	225,180,85,20, &paf->randlife, 0.0, 2.0, 10, 1, "Give the particlelife a random variation");
	uiBlockEndAlign(block);
	
	/* left collumn */
	uiDefBut(block, LABEL, 0, "Velocity:",			0,160,150,20, NULL, 0.0, 0, 0, 0, "");
	uiBlockBeginAlign(block);
	uiBlockSetCol(block, TH_BUT_SETTING2);
	uiDefButF(block, NUM, B_CALCEFFECT, "Normal:",		0,140,150,18, &paf->normfac, -2.0, 2.0, 1, 3, "Let the mesh give the particle a starting speed");
	uiDefButF(block, NUM, B_CALCEFFECT, "Object:",		0,122,150,18, &paf->obfac, -1.0, 1.0, 1, 3, "Let the object give the particle a starting speed");
	uiDefButF(block, NUM, B_CALCEFFECT, "Random:",		0,104,150,18, &paf->randfac, 0.0, 2.0, 1, 3, "Give the startingspeed a random variation");
	uiDefButF(block, NUM, B_CALCEFFECT, "Texture:",		0,86,150,18, &paf->texfac, 0.0, 2.0, 1, 3, "Let the texture give the particle a starting speed");
	uiDefButF(block, NUM, B_CALCEFFECT, "Damping:",		0,68,150,18, &paf->damp, 0.0, 1.0, 1, 3, "Specify the damping factor");
	uiBlockSetCol(block, TH_AUTO);
	but=uiDefBut(block, TEX, B_PAF_SET_VG1, "VGroup:",	0,50,150,18, paf->vgroupname_v, 0, 31, 0, 0, "Name of vertex group to use for speed control");
	uiButSetCompleteFunc(but, autocomplete_vgroup, (void *)OBACT);
	uiBlockEndAlign(block);
	
	uiDefBut(block, LABEL, 0, "Texture Emission",			0,30,150,20, NULL, 0.0, 0, 0, 0, "");
	uiBlockBeginAlign(block);
	uiDefButBitS(block, TOG3, PAF_TEXTIME, B_CALCEFFECT, "TexEmit",		0,10,75,20, &(paf->flag2), 0, 0, 0, 0, "Use a texture to define emission of particles");
	uiDefButS(block, NUM, B_CALCEFFECT, "Tex:",		75,10,75,20, &paf->timetex, 1.0, 10.0, 0, 0, "Specify texture used for the texture emission");
	
	/* right collumn */
	uiDefIDPoinBut(block, test_grouppoin_but, ID_GR, B_CALCEFFECT, "GR:", 160, 155, 150, 20, &paf->group, "Limit Force Fields to this Group"); 

	uiBlockBeginAlign(block);
	uiDefBut(block, LABEL, 0, "Force:",				160,130,75,20, NULL, 0.0, 0, 0, 0, "");
	uiDefButF(block, NUM, B_CALCEFFECT, "X:",		235,130,75,20, paf->force, -1.0, 1.0, 1, 2, "Specify the X axis of a continues force");
	uiDefButF(block, NUM, B_CALCEFFECT, "Y:",		160,110,75,20, paf->force+1,-1.0, 1.0, 1, 2, "Specify the Y axis of a continues force");
	uiDefButF(block, NUM, B_CALCEFFECT, "Z:",		235,110,75,20, paf->force+2, -1.0, 1.0, 1, 2, "Specify the Z axis of a continues force");
	
	uiBlockBeginAlign(block);
	uiDefButS(block, NUM, B_CALCEFFECT, "Tex:",		160,80,75,20, &paf->speedtex, 1.0, 10.0, 0, 2, "Specify the texture used for force");
	uiDefButF(block, NUM, B_CALCEFFECT, "X:",		235,80,75,20, paf->defvec, -1.0, 1.0, 1, 2, "Specify the X axis of a force, determined by the texture");
	uiDefButF(block, NUM, B_CALCEFFECT, "Y:",		160,60,75,20, paf->defvec+1,-1.0, 1.0, 1, 2, "Specify the Y axis of a force, determined by the texture");
	uiDefButF(block, NUM, B_CALCEFFECT, "Z:",		235,60,75,20, paf->defvec+2, -1.0, 1.0, 1, 2, "Specify the Z axis of a force, determined by the texture");
	
	uiBlockBeginAlign(block);
	uiDefButS(block, ROW, B_CALCEFFECT, "Int",		160,30,50,20, &paf->texmap, 14.0, 0.0, 0, 0, "Use texture intensity as a factor for texture force");
	uiDefButS(block, ROW, B_CALCEFFECT, "RGB",		210,30,50,20, &paf->texmap, 14.0, 1.0, 0, 0, "Use RGB values as a factor for particle speed vector");
	uiDefButS(block, ROW, B_CALCEFFECT, "Grad",		260,30,50,20, &paf->texmap, 14.0, 2.0, 0, 0, "Use texture gradient as a factor for particle speed vector");
	
	uiDefButF(block, NUM, B_CALCEFFECT, "Nabla:",	160,10,150,20, &paf->nabla, 0.0001f, 1.0, 1, 0, "Specify the dimension of the area for gradient calculation");
	
}


static void object_panel_particles(Object *ob)
{
	uiBlock *block;
	uiBut *but;
	PartEff *paf= give_parteff(ob);
	
	/* the panelname "Particles " has a space to exclude previous saved panel "Particles" */
	block= uiNewBlock(&curarea->uiblocks, "object_panel_particles", UI_EMBOSS, UI_HELV, curarea->win);
	if(uiNewPanel(curarea, block, "Particles ", "Physics", 320, 0, 318, 204)==0) return;

	if(ob->id.lib) uiSetButLock(1, "Can't edit library data");
	
	if (ob->type == OB_MESH) {
		uiBlockBeginAlign(block);
		if(paf==NULL)
			uiDefBut(block, BUT, B_NEWEFFECT, "NEW",	0,180,75,20, 0, 0, 0, 0, 0, "Create a new Particle effect");
		else
			uiDefBut(block, BUT, B_DELEFFECT, "Delete", 0,180,75,20, 0, 0, 0, 0, 0, "Delete the effect");
	}
	else uiDefBut(block, LABEL, 0, "Only Mesh Objects can generate particles",				10,180,300,20, NULL, 0.0, 0, 0, 0, "");
	
	
	if(paf==NULL) return;
	
	uiDefBut(block, BUT, B_RECALCAL, "RecalcAll",		75,180,75,20, 0, 0, 0, 0, 0, "Update all particle systems");
	uiBlockEndAlign(block);
	
	uiDefBut(block, LABEL, 0, "Emit:",					0,150,75,20, NULL, 0.0, 0, 0, 0, "");
	uiBlockBeginAlign(block);
	uiDefButI(block, NUM, B_CALCEFFECT, "Amount:",		0,130,150,20, &paf->totpart, 1.0, 100000.0, 0, 0, "The total number of particles");
	if(paf->flag & PAF_STATIC) {
		uiDefButS(block, NUM, REDRAWVIEW3D, "Step:",	0,110,150,20, &paf->staticstep, 1.0, 100.0, 10, 0, "For static duplicators, the Step value skips particles");
	}
	else {
		uiDefButF(block, NUM, B_CALCEFFECT, "Sta:",		0,110,75,20, &paf->sta, -250.0, MAXFRAMEF, 100, 1, "Frame # to start emitting particles");
		uiDefButF(block, NUM, B_CALCEFFECT, "End:",		75,110,75,20, &paf->end, 1.0, MAXFRAMEF, 100, 1, "Frame # to stop emitting particles");
	}
	uiDefButF(block, NUM, B_CALCEFFECT, "Life:",		0,90,75,20, &paf->lifetime, 1.0, MAXFRAMEF, 100, 1, "Specify the life span of the particles");
	uiDefButS(block, NUM, B_CALCEFFECT, "Disp:",		75,90,75,20, &paf->disp, 0.0, 100.0, 10, 0, "Percentage of particles to calculate for 3d view");
	uiBlockEndAlign(block);
	
	uiDefBut(block, LABEL, 0, "From:",					0,70,75,20, NULL, 0.0, 0, 0, 0, "");
	uiBlockBeginAlign(block);
	uiDefButBitS(block, TOGN, PAF_OFACE, B_CALCEFFECT, "Verts",	0,50,75,20, &paf->flag, 0, 0, 0, 0, "Emit particles from vertices");
	uiDefButBitS(block, TOG, PAF_FACE, B_CALCEFFECT, "Faces",	75,50,75,20, &paf->flag, 0, 0, 0, 0, "Emit particles from faces");
	if(paf->flag & PAF_FACE) {
		uiDefButBitS(block, TOG, PAF_TRAND, B_CALCEFFECT, "Rand",	0,30,50,20, &paf->flag, 0, 0, 0, 0, "Use true random distribution from faces");
		uiDefButBitS(block, TOG, PAF_EDISTR, B_CALCEFFECT, "Even",	50,30,50,20, &paf->flag, 0, 0, 0, 0, "Use even distribution from faces based on face areas");
		uiDefButS(block, NUM, B_CALCEFFECT, "P/F:",					100,30,50,20, &paf->userjit, 0.0, 200.0, 1, 0, "Jitter table distribution: maximum particles per face (0=uses default)");
	}
	else uiBlockEndAlign(block);	/* vgroup button no align */
	
	but=uiDefBut(block, TEX, B_PAF_SET_VG, "VGroup:",					0,10,150,20, paf->vgroupname, 0, 31, 0, 0, "Name of vertex group to use");
	uiButSetCompleteFunc(but, autocomplete_vgroup, (void *)OBACT);
	uiBlockEndAlign(block);
	
	/* right collumn */
	uiBlockBeginAlign(block);
	uiDefButBitS(block, TOG, PAF_STATIC, B_EFFECT_DEP, "Static",	160,180,75,20, &paf->flag, 0, 0, 0, 0, "Make static particles (deform only works with SubSurf)");
	if(paf->flag & PAF_STATIC) {
		uiDefButBitS(block, TOG, PAF_ANIMATED, B_DIFF, "Animated",	235,180,75,20, &paf->flag, 0, 0, 0, 0, "Static particles are recalculated each rendered frame");
	}
	uiBlockEndAlign(block);

	uiDefBut(block, LABEL, 0, "Display:",				160,150,75,20, NULL, 0.0, 0, 0, 0, "");
	uiBlockBeginAlign(block);
	uiDefButS(block, NUM, B_CALCEFFECT, "Material:",	160,130,150,20, &paf->omat, 1.0, 16.0, 0, 0, "Specify material used for the particles");
	uiDefButS(block, TOG|BIT|7, B_REDR, "Mesh",			160,110,50,20, &paf->flag, 0, 0, 0, 0, "Render emitter Mesh also");
	uiDefButBitS(block, TOG, PAF_UNBORN, B_DIFF, "Unborn",210,110,50,20, &paf->flag, 0, 0, 0, 0, "Make particles appear before they are emitted");
	uiDefButBitS(block, TOG, PAF_DIED, B_DIFF, "Died",	260,110,50,20, &paf->flag, 0, 0, 0, 0, "Make particles appear after they have died");
	uiDefButS(block, TOG, REDRAWVIEW3D, "Vect",			160,90,75,20, &paf->stype, 0, 0, 0, 0, "Give the particles a direction and rotation");
	uiDefButF(block, NUM, B_DIFF,		"Size:",		235,90,75,20, &paf->vectsize, 0.0, 1.0, 10, 1, "The amount the Vect option influences halo size");	
	uiBlockEndAlign(block);

	uiDefBut(block, LABEL, 0, "Children:",				160,70,75,20, NULL, 0.0, 0, 0, 0, "");
	uiBlockBeginAlign(block);
	uiDefButS(block, NUM, B_REDR,		"Generation:",	160,50,150,20, &paf->curmult, 0.0, 3.0, 0, 0, "Current generation of particles");
	uiDefButS(block, NUM, B_CALCEFFECT, "Num:",			160,30,75,20, paf->child+paf->curmult, 1.0, 600.0, 100, 0, "Specify the number of generations of particles that can multiply itself");
	uiDefButF(block, NUM, B_CALCEFFECT, "Prob:",		235,30,75,20, paf->mult+paf->curmult, 0.0, 1.0, 10, 1, "Probability \"dying\" particle spawns a new one.");
	uiDefButF(block, NUM, B_CALCEFFECT, "Life:",		160,10,75,20, paf->life+paf->curmult, 1.0, 600.0, 100, 1, "Specify the lifespan of the next generation particles");
	uiDefButS(block, NUM, B_CALCEFFECT, "Mat:",			235,10,75,20, paf->mat+paf->curmult, 1.0, 8.0, 0, 0, "Specify the material used for the particles");
	uiBlockEndAlign(block);
	
}

/* NT - Panel for fluidsim settings */
static void object_panel_fluidsim(Object *ob)
{
#ifndef DISABLE_ELBEEM
	uiBlock *block;
	int yline = 160;
	const int lineHeight = 20;
	const int separateHeight = 3;
	const int objHeight = 20;
	
	block= uiNewBlock(&curarea->uiblocks, "object_fluidsim", UI_EMBOSS, UI_HELV, curarea->win);
	uiNewPanelTabbed("Soft Body", "Physics");
	if(uiNewPanel(curarea, block, "Fluid Simulation", "Physics", 1060, 0, 318, 204)==0) return;

	if(ob->id.lib) uiSetButLock(1, "Can't edit library data");
	
	if(ob->type==OB_MESH) {
		uiDefButBitS(block, TOG, OB_FLUIDSIM_ENABLE, REDRAWBUTSOBJECT, "Enable",	 0,yline, 75,objHeight, 
				&ob->fluidsimFlag, 0, 0, 0, 0, "Sets object to participate in fluid simulation");

		if(ob->fluidsimFlag & OB_FLUIDSIM_ENABLE) {
			FluidsimSettings *fss= ob->fluidsimSettings;
			
			if(fss==NULL) {
				fss = ob->fluidsimSettings = fluidsimSettingsNew(ob);
			}
			
			uiBlockBeginAlign(block);
			uiDefButS(block, ROW, REDRAWBUTSOBJECT ,"Domain",	    90, yline, 70,objHeight, &fss->type, 15.0, OB_FLUIDSIM_DOMAIN,  20.0, 1.0, "Bounding box of this object represents the computational domain of the fluid simulation.");
			uiDefButS(block, ROW, REDRAWBUTSOBJECT ,"Fluid",	   160, yline, 70,objHeight, &fss->type, 15.0, OB_FLUIDSIM_FLUID,   20.0, 2.0, "Object represents a volume of fluid in the simulation.");
			uiDefButS(block, ROW, REDRAWBUTSOBJECT ,"Obstacle",	 230, yline, 70,objHeight, &fss->type, 15.0, OB_FLUIDSIM_OBSTACLE,20.0, 3.0, "Object is a fixed obstacle.");
			yline -= lineHeight;

			uiDefButS(block, ROW, REDRAWBUTSOBJECT ,"Inflow",	    90, yline, 70,objHeight, &fss->type, 15.0, OB_FLUIDSIM_INFLOW,  20.0, 4.0, "Object adds fluid to the simulation.");
			uiDefButS(block, ROW, REDRAWBUTSOBJECT ,"Outflow",   160, yline, 70,objHeight, &fss->type, 15.0, OB_FLUIDSIM_OUTFLOW, 20.0, 5.0, "Object removes fluid from the simulation.");
			uiDefButS(block, ROW, B_FLUIDSIM_MAKEPART ,"Particle",	 230, yline, 70,objHeight, &fss->type, 15.0, OB_FLUIDSIM_PARTICLE,20.0, 3.0, "Object is made a particle system to display particles generated by a fluidsim domain object.");
			uiBlockEndAlign(block);
			yline -= lineHeight;
			yline -= 2*separateHeight;

			/* display specific settings for each type */
			if(fss->type == OB_FLUIDSIM_DOMAIN) {
				const int maxRes = 512;
				char memString[32];

				// use mesh bounding box and object scaling
				// TODO fix redraw issue
				elbeemEstimateMemreq(fss->resolutionxyz, 
						ob->fluidsimSettings->bbSize[0],ob->fluidsimSettings->bbSize[1],ob->fluidsimSettings->bbSize[2], fss->maxRefine, memString);
				
				uiBlockBeginAlign(block);
				uiDefButS(block, ROW, REDRAWBUTSOBJECT, "Std",	 0,yline, 25,objHeight, &fss->show_advancedoptions, 16.0, 0, 20.0, 0, "Show standard domain options.");
				uiDefButS(block, ROW, REDRAWBUTSOBJECT, "Adv",	25,yline, 25,objHeight, &fss->show_advancedoptions, 16.0, 1, 20.0, 1, "Show advanced domain options.");
				uiDefButS(block, ROW, REDRAWBUTSOBJECT, "Bnd",	50,yline, 25,objHeight, &fss->show_advancedoptions, 16.0, 2, 20.0, 2, "Show domain boundary options.");
				uiBlockEndAlign(block);
				
				uiDefBut(block, BUT, B_FLUIDSIM_BAKE, "BAKE",90, yline,210,objHeight, NULL, 0.0, 0.0, 10, 0, "Perform simulation and output and surface&preview meshes for each frame.");
				yline -= lineHeight;
				yline -= 2*separateHeight;

				if(fss->show_advancedoptions == 0) {
					uiDefBut(block, LABEL,   0, "Req. BAKE Memory:",  0,yline,150,objHeight, NULL, 0.0, 0, 0, 0, "");
					uiDefBut(block, LABEL,   0, memString,  200,yline,100,objHeight, NULL, 0.0, 0, 0, 0, "");
					yline -= lineHeight;

					uiBlockBeginAlign(block);
					uiDefButS(block, NUM, REDRAWBUTSOBJECT, "Resolution:", 0, yline,150,objHeight, &fss->resolutionxyz, 1, maxRes, 10, 0, "Domain resolution in X,Y and Z direction");
					uiDefButS(block, NUM, B_DIFF,           "Preview-Res.:", 150, yline,150,objHeight, &fss->previewresxyz, 1, 100, 10, 0, "Resolution of the preview meshes to generate, also in X,Y and Z direction");
					uiBlockEndAlign(block);
					yline -= lineHeight;
					yline -= 1*separateHeight;

					uiBlockBeginAlign(block);
					uiDefButF(block, NUM, B_DIFF, "Start time:",   0, yline,150,objHeight, &fss->animStart, 0.0, 100.0, 10, 0, "Simulation time of the first blender frame.");
					uiDefButF(block, NUM, B_DIFF, "End time:",   150, yline,150,objHeight, &fss->animEnd  , 0.0, 100.0, 10, 0, "Simulation time of the last blender frame.");
					uiBlockEndAlign(block);
					yline -= lineHeight;
					yline -= 2*separateHeight;

					if((fss->guiDisplayMode<1) || (fss->guiDisplayMode>3)){ fss->guiDisplayMode=2; } // can be changed by particle setting
					uiDefBut(block, LABEL,   0, "Disp.-Qual.:",		 0,yline, 90,objHeight, NULL, 0.0, 0, 0, 0, "");
					uiBlockBeginAlign(block);
					uiDefButS(block, MENU, B_FLUIDSIM_FORCEREDRAW, "GuiDisplayMode%t|Geometry %x1|Preview %x2|Final %x3",	
							 90,yline,105,objHeight, &fss->guiDisplayMode, 0, 0, 0, 0, "How to display the fluid mesh in the blender gui.");
					uiDefButS(block, MENU, B_DIFF, "RenderDisplayMode%t|Geometry %x1|Preview %x2|Final %x3",	
							195,yline,105,objHeight, &fss->renderDisplayMode, 0, 0, 0, 0, "How to display the fluid mesh for rendering.");
					uiBlockEndAlign(block);
					yline -= lineHeight;
					yline -= 1*separateHeight;

					uiBlockBeginAlign(block);
					uiDefIconBut(block, BUT, B_FLUIDSIM_SELDIR, ICON_FILESEL,  0, yline,  20, objHeight,                   0, 0, 0, 0, 0,  "Select Directory (and/or filename prefix) to store baked fluid simulation files in");
					uiDefBut(block, TEX,     B_FLUIDSIM_FORCEREDRAW,"",	      20, yline, 280, objHeight, fss->surfdataPath, 0.0,79.0, 0, 0,  "Enter Directory (and/or filename prefix) to store baked fluid simulation files in");
					uiBlockEndAlign(block);
					// FIXME what is the 79.0 above?
				} else if(fss->show_advancedoptions == 1) {
					// advanced options
					uiDefBut(block, LABEL, 0, "Gravity:",		0, yline,  90,objHeight, NULL, 0.0, 0, 0, 0, "");
					uiBlockBeginAlign(block);
					uiDefButF(block, NUM, B_DIFF, "X:",    90, yline,  70,objHeight, &fss->gravx, -1000.1, 1000.1, 10, 0, "Gravity in X direction");
					uiDefButF(block, NUM, B_DIFF, "Y:",   160, yline,  70,objHeight, &fss->gravy, -1000.1, 1000.1, 10, 0, "Gravity in Y direction");
					uiDefButF(block, NUM, B_DIFF, "Z:",   230, yline,  70,objHeight, &fss->gravz, -1000.1, 1000.1, 10, 0, "Gravity in Z direction");
					uiBlockEndAlign(block);
					yline -= lineHeight;
					yline -= 1*separateHeight;

					/* viscosity */
					if (fss->viscosityMode==1) /*manual*/
						uiBlockBeginAlign(block);
					uiDefButS(block, MENU, REDRAWVIEW3D, "Viscosity%t|Manual %x1|Water %x2|Oil %x3|Honey %x4",	
							0,yline, 90,objHeight, &fss->viscosityMode, 0, 0, 0, 0, "Set viscosity of the fluid to a preset value, or use manual input.");
					if(fss->viscosityMode==1) {
						uiDefButF(block, NUM, B_DIFF, "Value:",     90, yline, 105,objHeight, &fss->viscosityValue,       0.0, 1.0, 10, 0, "Viscosity setting, value that is multiplied by 10 to the power of (exponent*-1).");
						uiDefButS(block, NUM, B_DIFF, "Neg-Exp.:", 195, yline, 105,objHeight, &fss->viscosityExponent, 0,   10,  10, 0, "Negative exponent for the viscosity value (to simplify entering small values e.g. 5*10^-6.");
						uiBlockEndAlign(block);
					} else {
						// display preset values
						uiDefBut(block, LABEL,   0, fluidsimViscosityPresetString[fss->viscosityMode],  90,yline,200,objHeight, NULL, 0.0, 0, 0, 0, "");
					}
					yline -= lineHeight;
					yline -= 1*separateHeight;

					uiDefBut(block, LABEL, 0, "Realworld-size:",		0,yline,150,objHeight, NULL, 0.0, 0, 0, 0, "");
					uiDefButF(block, NUM, B_DIFF, "", 150, yline,150,objHeight, &fss->realsize, 0.001, 10.0, 10, 0, "Size of the simulation domain in meters.");
					yline -= lineHeight;
					yline -= 2*separateHeight;

					uiDefBut(block, LABEL, 0, "Gridlevels:",		0,yline,150,objHeight, NULL, 0.0, 0, 0, 0, "");
					uiDefButI(block, NUM, B_DIFF, "", 150, yline,150,objHeight, &fss->maxRefine, -1, 4, 10, 0, "Number of coarsened Grids to use (set to -1 for automatic selection).");
					yline -= lineHeight;

					uiDefBut(block, LABEL, 0, "Compressibility:",		0,yline,150,objHeight, NULL, 0.0, 0, 0, 0, "");
					uiDefButF(block, NUM, B_DIFF, "", 150, yline,150,objHeight, &fss->gstar, 0.001, 0.10, 10,0, "Allowed compressibility due to gravitational force for standing fluid (directly affects simulation step size).");
					yline -= lineHeight;

				} else if(fss->show_advancedoptions == 2) {
					// copied from obstacle...
					//yline -= lineHeight + 5;
					uiDefBut(block, LABEL, 0, "Domain boundary type settings:",		0,yline,300,objHeight, NULL, 0.0, 0, 0, 0, "");
					yline -= lineHeight;

					uiBlockBeginAlign(block); // domain
					uiDefButS(block, ROW, REDRAWBUTSOBJECT ,"Noslip",    0, yline,100,objHeight, &fss->typeFlags, 15.0, OB_FSBND_NOSLIP,   20.0, 1.0, "Obstacle causes zero normal and tangential velocity (=sticky). Default for all. Only option for moving objects.");
					uiDefButS(block, ROW, REDRAWBUTSOBJECT ,"Part",	   100, yline,100,objHeight, &fss->typeFlags, 15.0, OB_FSBND_PARTSLIP, 20.0, 2.0, "Mix between no-slip and free-slip. Non moving objects only!");
					uiDefButS(block, ROW, REDRAWBUTSOBJECT ,"Free",  	 200, yline,100,objHeight, &fss->typeFlags, 15.0, OB_FSBND_FREESLIP, 20.0, 3.0, "Obstacle only causes zero normal velocity (=not sticky). Non moving objects only!");
					uiBlockEndAlign(block);
					yline -= lineHeight;

					uiDefBut(block, LABEL, 0, "PartSlipValue:",		0,yline,200,objHeight, NULL, 0.0, 0, 0, 0, "");
					if(fss->typeFlags&OB_FSBND_PARTSLIP) {
						uiDefButF(block, NUM, B_DIFF, "", 200, yline,100,objHeight, &fss->partSlipValue, 0.0, 1.0, 10,0, ".");
					} else { uiDefBut(block, LABEL, 0, "-",	200,yline,100,objHeight, NULL, 0.0, 0, 0, 0, ""); }
					yline -= lineHeight;
					// copied from obstacle...

					uiDefBut(block, LABEL, 0, "Tracer Particles:",		0,yline,200,objHeight, NULL, 0.0, 0, 0, 0, "");
					uiDefButI(block, NUM, B_DIFF, "", 200, yline,100,objHeight, &fss->generateTracers, 0.0, 10000.0, 10,0, "Number of tracer particles to generate.");
					yline -= lineHeight;
					uiDefBut(block, LABEL, 0, "Generate Particles:",		0,yline,200,objHeight, NULL, 0.0, 0, 0, 0, "");
					uiDefButF(block, NUM, B_DIFF, "", 200, yline,100,objHeight, &fss->generateParticles, 0.0, 10.0, 10,0, "Amount of particles to generate (0=off, 1=normal, >1=more).");
					yline -= lineHeight;

					uiDefBut(block, LABEL, 0, "Surface Smoothing:",		0,yline,200,objHeight, NULL, 0.0, 0, 0, 0, "");
					uiDefButF(block, NUM, B_DIFF, "", 200, yline,100,objHeight, &fss->surfaceSmoothing, 0.0, 5.0, 10,0, "Amount of surface smoothing (0=off, 1=normal, >1=stronger smoothing).");
					yline -= lineHeight;

					// use new variable...
					uiDefBut(block, LABEL, 0, "Generate&Use SpeedVecs:",		0,yline,200,objHeight, NULL, 0.0, 0, 0, 0, "");
				  uiDefButBitC(block, TOG, 1, REDRAWBUTSOBJECT, "Disable",     200, yline,100,objHeight, &fss->domainNovecgen, 0, 0, 0, 0, "Default is to generate and use fluidsim vertex speed vectors, this option switches calculation off during bake, and disables loading.");
					yline -= lineHeight;
				} // domain 3
			}
			else if(
					(fss->type == OB_FLUIDSIM_FLUID) 
					|| (fss->type == OB_FLUIDSIM_INFLOW) 
					) {
				uiBlockBeginAlign(block); // fluid
				uiDefButC(block, ROW, REDRAWBUTSOBJECT ,"Init Volume",    0, yline,100,objHeight, &fss->volumeInitType, 15.0, 1, 20.0, 1.0, "Type of volume init: use only inner region of mesh.");
				uiDefButC(block, ROW, REDRAWBUTSOBJECT ,"Init Shell",   100, yline,100,objHeight, &fss->volumeInitType, 15.0, 2, 20.0, 2.0, "Type of volume init: use only the hollow shell defines by the faces of the mesh.");
				uiDefButC(block, ROW, REDRAWBUTSOBJECT ,"Init Both",    200, yline,100,objHeight, &fss->volumeInitType, 15.0, 3, 20.0, 3.0, "Type of volume init: use both the inner volume and the outer shell.");
				uiBlockEndAlign(block);
				yline -= lineHeight;

				yline -= lineHeight + 5; // fluid + inflow
				if(fss->type == OB_FLUIDSIM_FLUID)  uiDefBut(block, LABEL, 0, "Initial velocity:",		0,yline,200,objHeight, NULL, 0.0, 0, 0, 0, "");
				if(fss->type == OB_FLUIDSIM_INFLOW) uiDefBut(block, LABEL, 0, "Inflow velocity:",		  0,yline,200,objHeight, NULL, 0.0, 0, 0, 0, "");
				yline -= lineHeight;
				uiBlockBeginAlign(block);
				uiDefButF(block, NUM, B_DIFF, "X:",   0, yline, 100,objHeight, &fss->iniVelx, -1000.1, 1000.1, 10, 0, "Fluid velocity in X direction");
				uiDefButF(block, NUM, B_DIFF, "Y:", 100, yline, 100,objHeight, &fss->iniVely, -1000.1, 1000.1, 10, 0, "Fluid velocity in Y direction");
				uiDefButF(block, NUM, B_DIFF, "Z:", 200, yline, 100,objHeight, &fss->iniVelz, -1000.1, 1000.1, 10, 0, "Fluid velocity in Z direction");
				uiBlockEndAlign(block);
				yline -= lineHeight;

				if(fss->type == OB_FLUIDSIM_INFLOW) { // inflow
					uiDefBut(block, LABEL, 0, "Local Inflow Coords",		0,yline,200,objHeight, NULL, 0.0, 0, 0, 0, "");
				  uiDefButBitS(block, TOG, OB_FSINFLOW_LOCALCOORD, REDRAWBUTSOBJECT, "Enable",     200, yline,100,objHeight, &fss->typeFlags, 0, 0, 0, 0, "Use local coordinates for inflow (e.g. for rotating objects).");
				  yline -= lineHeight;
				} else {
				}
			} // fluid inflow
			else if( (fss->type == OB_FLUIDSIM_OUTFLOW) )	{
				yline -= lineHeight + 5;

				uiBlockBeginAlign(block); // outflow
				uiDefButC(block, ROW, REDRAWBUTSOBJECT ,"Init Volume",    0, yline,100,objHeight, &fss->volumeInitType, 15.0, 1, 20.0, 1.0, "Type of volume init: use only inner region of mesh.");
				uiDefButC(block, ROW, REDRAWBUTSOBJECT ,"Init Shell",   100, yline,100,objHeight, &fss->volumeInitType, 15.0, 2, 20.0, 2.0, "Type of volume init: use only the hollow shell defines by the faces of the mesh.");
				uiDefButC(block, ROW, REDRAWBUTSOBJECT ,"Init Both",    200, yline,100,objHeight, &fss->volumeInitType, 15.0, 3, 20.0, 3.0, "Type of volume init: use both the inner volume and the outer shell.");
				uiBlockEndAlign(block);
				yline -= lineHeight;

				//uiDefBut(block, LABEL, 0, "No additional settings as of now...",		0,yline,300,objHeight, NULL, 0.0, 0, 0, 0, "");
			}
			else if( (fss->type == OB_FLUIDSIM_OBSTACLE) )	{
				yline -= lineHeight + 5; // obstacle

				uiBlockBeginAlign(block); // obstacle
				uiDefButC(block, ROW, REDRAWBUTSOBJECT ,"Init Volume",    0, yline,100,objHeight, &fss->volumeInitType, 15.0, 1, 20.0, 1.0, "Type of volume init: use only inner region of mesh.");
				uiDefButC(block, ROW, REDRAWBUTSOBJECT ,"Init Shell",   100, yline,100,objHeight, &fss->volumeInitType, 15.0, 2, 20.0, 2.0, "Type of volume init: use only the hollow shell defines by the faces of the mesh.");
				uiDefButC(block, ROW, REDRAWBUTSOBJECT ,"Init Both",    200, yline,100,objHeight, &fss->volumeInitType, 15.0, 3, 20.0, 3.0, "Type of volume init: use both the inner volume and the outer shell.");
				uiBlockEndAlign(block);
				yline -= lineHeight;

				uiBlockBeginAlign(block); // obstacle
				uiDefButS(block, ROW, REDRAWBUTSOBJECT ,"Noslip",   00, yline,100,objHeight, &fss->typeFlags, 15.0, OB_FSBND_NOSLIP,   20.0, 1.0, "Obstacle causes zero normal and tangential velocity (=sticky). Default for all. Only option for moving objects.");
				uiDefButS(block, ROW, REDRAWBUTSOBJECT ,"Part",	   100, yline,100,objHeight, &fss->typeFlags, 15.0, OB_FSBND_PARTSLIP, 20.0, 2.0, "Mix between no-slip and free-slip. Non moving objects only!");
				uiDefButS(block, ROW, REDRAWBUTSOBJECT ,"Free",  	 200, yline,100,objHeight, &fss->typeFlags, 15.0, OB_FSBND_FREESLIP, 20.0, 3.0, "Obstacle only causes zero normal velocity (=not sticky). Non moving objects only!");
				uiBlockEndAlign(block);
				yline -= lineHeight;

				// domainNovecgen "misused" here
				uiDefBut(block, LABEL, 0, "Animated Mesh:",		0,yline,200,objHeight, NULL, 0.0, 0, 0, 0, "");
			  uiDefButBitC(block, TOG, 1, REDRAWBUTSOBJECT, "Export",     200, yline,100,objHeight, &fss->domainNovecgen, 0, 0, 0, 0, "Export this mesh as an animated one. Slower, only use if really necessary (e.g. armatures), animated pos/rot/scale IPOs do not require it.");
				yline -= lineHeight;

				uiDefBut(block, LABEL, 0, "PartSlip Amount:",		0,yline,200,objHeight, NULL, 0.0, 0, 0, 0, "");
				if(fss->typeFlags&OB_FSBND_PARTSLIP) {
					uiDefButF(block, NUM, B_DIFF, "", 200, yline,100,objHeight, &fss->partSlipValue, 0.0, 1.0, 10,0, "Amount of mixing between no- and free-slip, 0=stickier, 1=same as free slip.");
				} else { uiDefBut(block, LABEL, 0, "-",	200,yline,100,objHeight, NULL, 0.0, 0, 0, 0, ""); }
				yline -= lineHeight;

				yline -= lineHeight; // obstacle
			}
			else if(fss->type == OB_FLUIDSIM_PARTICLE) {

				// fixed for now
				fss->typeFlags = (1<<5)|(1<<1); 

				uiDefBut(block, LABEL, 0, "Size Influence:",		0,yline,150,objHeight, NULL, 0.0, 0, 0, 0, "");
				uiDefButF(block, NUM, B_DIFF, "", 150, yline,150,objHeight, &fss->particleInfSize, 0.0, 2.0,   10,0, "Amount of particle size scaling: 0=off (all same size), 1=full (range 0.2-2.0), >1=stronger.");
				yline -= lineHeight;
				uiDefBut(block, LABEL, 0, "Alpha Influence:",		0,yline,150,objHeight, NULL, 0.0, 0, 0, 0, "");
				uiDefButF(block, NUM, B_DIFF, "", 150, yline,150,objHeight, &fss->particleInfAlpha, 0.0, 2.0,   10,0, "Amount of particle alpha change, inverse of size influence: 0=off (all same alpha), 1=full (large particles get lower alphas, smaller ones higher values).");
				yline -= lineHeight;

				yline -= 1*separateHeight;

				// FSPARTICLE also select input files
				uiBlockBeginAlign(block);
				uiDefIconBut(block, BUT, B_FLUIDSIM_SELDIR, ICON_FILESEL,  0, yline,  20, objHeight,                   0, 0, 0, 0, 0,  "Select fluid simulation bake directory/prefix to load particles from, same as for domain object.");
				uiDefBut(block, TEX,     B_FLUIDSIM_FORCEREDRAW,"",	      20, yline, 280, objHeight, fss->surfdataPath, 0.0,79.0, 0, 0,  "Enter fluid simulation bake directory/prefix to load particles from, same as for domain object.");
				uiBlockEndAlign(block);
				yline -= lineHeight;


			}
			else {
				yline -= lineHeight + 5;
				/* not yet set */
				uiDefBut(block, LABEL, 0, "Select object type for simulation",		0,yline,300,objHeight, NULL, 0.0, 0, 0, 0, "");
				yline -= lineHeight;
			}

		} else {
			yline -= lineHeight + 5;
			uiDefBut(block, LABEL, 0, "Object not enabled for fluid simulation...", 0,yline,300,objHeight, NULL, 0.0, 0, 0, 0, "");
			yline -= lineHeight;
		}
	} else {
		yline -= lineHeight + 5;
		uiDefBut(block, LABEL, 0, "Only Mesh Objects can participate", 0,yline,300,objHeight, NULL, 0.0, 0, 0, 0, "");
		yline -= lineHeight;
	}
#endif // DISABLE_ELBEEM
}

void object_panels()
{
	Object *ob;

	/* check context here */
	ob= OBACT;
	if(ob) {
		object_panel_object(ob);
		object_panel_anim(ob);
		object_panel_draw(ob);
		object_panel_constraint("Object");

		uiClearButLock();
	}
}

void physics_panels()
{
	Object *ob;
	
	/* check context here */
	ob= OBACT;
	if(ob) {
		object_panel_fields(ob);
		object_panel_particles(ob);
		object_panel_particles_motion(ob);
		object_softbodies(ob);
		object_panel_fluidsim(ob);
	}
}

