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

#include <string.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "PIL_time.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_curve_types.h"
#include "DNA_ipo_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_userdef_types.h"
#include "DNA_constraint_types.h"
#include "DNA_key_types.h"
#include "DNA_mesh_types.h"
#include "DNA_nla_types.h"
#include "DNA_lattice_types.h"

#include "BKE_action.h"
#include "BKE_armature.h"
#include "BKE_constraint.h"
#include "BKE_curve.h"
#include "BKE_depsgraph.h"
#include "BKE_global.h"
#include "BKE_ipo.h"
#include "BKE_key.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_utildefines.h"
#include "BKE_object.h" /* for where_is_object in obanim -> action baking */

#include "BIF_butspace.h"
#include "BIF_editaction.h"
#include "BIF_editarmature.h"
#include "BIF_editnla.h"
#include "BIF_editview.h"
#include "BIF_gl.h"
#include "BIF_interface.h"
#include "BIF_mywindow.h"
#include "BIF_poseobject.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_toolbox.h"

#include "BSE_edit.h"
#include "BSE_drawipo.h"
#include "BSE_headerbuttons.h"
#include "BSE_editipo.h"
#include "BSE_trans_types.h"

#include "BDR_editobject.h"

#include "mydevice.h"
#include "blendef.h"
#include "nla.h"

extern int count_action_levels (bAction *act);
void top_sel_action();
void up_sel_action();
void bottom_sel_action();
void down_sel_action();

#define BEZSELECTED(bezt)   (((bezt)->f1 & 1) || ((bezt)->f2 & 1) || ((bezt)->f3 & 1))

/* Local Function prototypes, are forward needed */
static void hilight_channel (bAction *act, bActionChannel *chan, short hilight);

/* Implementation */

short showsliders = 0;
short ACTWIDTH = NAMEWIDTH;

/* messy call... */
static void select_poseelement_by_name (char *name, int select)
{
	/* Syncs selection of channels with selection of object elements in posemode */
	Object *ob= OBACT;
	bPoseChannel *pchan;
	
	if (!ob || ob->type!=OB_ARMATURE)
		return;
	
	if(select==2) {
		for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next)
			pchan->bone->flag &= ~(BONE_ACTIVE);
	}
	
	pchan= get_pose_channel(ob->pose, name);
	if(pchan) {
		if(select)
			pchan->bone->flag |= (BONE_SELECTED);
		else 
			pchan->bone->flag &= ~(BONE_SELECTED);
		if(select==2)
			pchan->bone->flag |= (BONE_ACTIVE);
	}
}

bAction* bake_action_with_client (bAction *act, Object *armob, float tolerance)
{
	bArmature		*arm;
	bAction			*result=NULL;
	bActionChannel *achan;
	bAction			*temp;
	bPoseChannel	*pchan;
	ID				*id;
	float			actstart, actend;
	int				oldframe;
	int				curframe;
	char			newname[64];

	if (!act)
		return NULL;
	
	arm = get_armature(armob);

	if (G.obedit){
		error ("Actions can't be baked in Edit Mode");
		return NULL;
	}

	if (!arm || armob->pose==NULL){
		error ("Select an armature before baking");
		return NULL;
	}
	
	/* Get a new action */
	result = add_empty_action(ID_PO);
	id= (ID *)armob;

	/* Assign the new action a unique name */
	sprintf (newname, "%s.BAKED", act->id.name+2);
	rename_id(&result->id, newname);

	calc_action_range(act, &actstart, &actend, 1);

	oldframe = G.scene->r.cfra;

	temp = armob->action;
	armob->action = result;
	
	for (curframe=1; curframe<ceil(actend+1.0f); curframe++){

		/* Apply the old action */
		
		G.scene->r.cfra = curframe;

		/* Apply the object ipo */
		extract_pose_from_action(armob->pose, act, curframe);

		where_is_pose(armob);
		
		/* For each channel: set quats and locs if channel is a bone */
		for (pchan=armob->pose->chanbase.first; pchan; pchan=pchan->next){

			/* Apply to keys */
			insertkey(id, ID_PO, pchan->name, NULL, AC_LOC_X);
			insertkey(id, ID_PO, pchan->name, NULL, AC_LOC_Y);
			insertkey(id, ID_PO, pchan->name, NULL, AC_LOC_Z);
			insertkey(id, ID_PO, pchan->name, NULL, AC_QUAT_X);
			insertkey(id, ID_PO, pchan->name, NULL, AC_QUAT_Y);
			insertkey(id, ID_PO, pchan->name, NULL, AC_QUAT_Z);
			insertkey(id, ID_PO, pchan->name, NULL, AC_QUAT_W);
			insertkey(id, ID_PO, pchan->name, NULL, AC_SIZE_X);
			insertkey(id, ID_PO, pchan->name, NULL, AC_SIZE_Y);
			insertkey(id, ID_PO, pchan->name, NULL, AC_SIZE_Z);
		}
	}


	/* Make another pass to ensure all keyframes are set to linear interpolation mode */
	for (achan = result->chanbase.first; achan; achan=achan->next){
		IpoCurve* icu;
		if(achan->ipo) {
			for (icu = achan->ipo->curve.first; icu; icu=icu->next){
				icu->ipo= IPO_LIN;
			}
		}
	}

	notice ("Made a new action named \"%s\"", newname);
	G.scene->r.cfra = oldframe;
	armob->action = temp;
		
	/* restore */
	extract_pose_from_action(armob->pose, act, G.scene->r.cfra);
	where_is_pose(armob);
	
	allqueue(REDRAWACTION, 1);
	
	return result;
}

/* apparently within active object context */
/* called extern, like on bone selection */
void select_actionchannel_by_name (bAction *act, char *name, int select)
{
	bActionChannel *chan;

	if (!act)
		return;

	for (chan = act->chanbase.first; chan; chan=chan->next){
		if (!strcmp (chan->name, name)){
			if (select){
				chan->flag |= ACHAN_SELECTED;
				hilight_channel (act, chan, 1);
			}
			else{
				chan->flag &= ~ACHAN_SELECTED;
				hilight_channel (act, chan, 0);
			}
			return;
		}
	}
}

/* called on changing action ipos or keys */
void remake_action_ipos(bAction *act)
{
	bActionChannel *chan;
	bConstraintChannel *conchan;
	IpoCurve		*icu;

	for (chan= act->chanbase.first; chan; chan=chan->next){
		if (chan->ipo){
			for (icu = chan->ipo->curve.first; icu; icu=icu->next){
				sort_time_ipocurve(icu);
				testhandles_ipocurve(icu);
			}
		}
		for (conchan=chan->constraintChannels.first; conchan; conchan=conchan->next){
			if (conchan->ipo){
				for (icu = conchan->ipo->curve.first; icu; icu=icu->next){
					sort_time_ipocurve(icu);
					testhandles_ipocurve(icu);
				}
			}
		}
	}
	
	synchronize_action_strips();
}

static void remake_meshaction_ipos(Ipo *ipo)
{
	/* this puts the bezier triples in proper
	 * order and makes sure the bezier handles
	 * aren't too strange.
	 */
	IpoCurve *icu;

	for (icu = ipo->curve.first; icu; icu=icu->next){
		sort_time_ipocurve(icu);
		testhandles_ipocurve(icu);
	}
}

static void meshkey_do_redraw(Key *key)
{
	if(key->ipo)
		remake_meshaction_ipos(key->ipo);

	DAG_object_flush_update(G.scene, OBACT, OB_RECALC_DATA);
	
	allspace(REMAKEIPO, 0);
	allqueue(REDRAWACTION, 0);
	allqueue(REDRAWIPO, 0);
	allqueue(REDRAWNLA, 0);

}

void duplicate_meshchannel_keys(Key *key)
{
	duplicate_ipo_keys(key->ipo);
	transform_meshchannel_keys ('g', key);
}


void duplicate_actionchannel_keys(void)
{
	bAction *act;
	bActionChannel *chan;
	bConstraintChannel *conchan;

	act=G.saction->action;
	if (!act)
		return;

	/* Find selected items */
	for (chan = act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			duplicate_ipo_keys(chan->ipo);
			for (conchan=chan->constraintChannels.first; conchan; conchan=conchan->next)
				duplicate_ipo_keys(conchan->ipo);
		}
	}

	transform_actionchannel_keys ('g', 0);
}

static bActionChannel *get_nearest_actionchannel_key (float *index, short *sel, bConstraintChannel **rchan)
{
	bAction *act;
	bActionChannel *chan;
	IpoCurve *icu;
	bActionChannel *firstchan=NULL;
	bConstraintChannel *conchan, *firstconchan=NULL;
	rctf	rectf;
	float firstvert=-1, foundx=-1;
	float ymin, ymax, xmin, xmax;
	int i;
	int	foundsel=0;
	short mval[2];
	
	*index=0;

	*rchan=NULL;
	act= G.saction->action; /* We presume that we are only called during a valid action */
	
	getmouseco_areawin (mval);

	mval[0]-=7;
	areamouseco_to_ipoco(G.v2d, mval, &rectf.xmin, &rectf.ymin);
	mval[0]+=14;
	areamouseco_to_ipoco(G.v2d, mval, &rectf.xmax, &rectf.ymax);

	ymax = count_action_levels(act) * (CHANNELHEIGHT + CHANNELSKIP);
	ymax += CHANNELHEIGHT/2;
	
	/* if action is mapped in NLA, it returns a correction */
	if(G.saction->pin==0 && OBACT) {
		xmin= get_action_frame(OBACT, rectf.xmin);
		xmax= get_action_frame(OBACT, rectf.xmax);
	}
	else {
		xmin= rectf.xmin;
		xmax= rectf.xmax;
	}
	
	*sel=0;

	for (chan=act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {

			/* Check action channel */
			ymin= ymax-(CHANNELHEIGHT+CHANNELSKIP);
			if (!((ymax < rectf.ymin) || (ymin > rectf.ymax)) && chan->ipo){
				for (icu=chan->ipo->curve.first; icu; icu=icu->next){
					for (i=0; i<icu->totvert; i++){
						if (icu->bezt[i].vec[1][0] > xmin && icu->bezt[i].vec[1][0] <= xmax ){
							if (!firstchan){
								firstchan=chan;
								firstvert=icu->bezt[i].vec[1][0];
								*sel = icu->bezt[i].f2 & 1;	
							}
							
							if (icu->bezt[i].f2 & 1){ 
								if (!foundsel){
									foundsel=1;
									foundx = icu->bezt[i].vec[1][0];
								}
							}
							else if (foundsel && icu->bezt[i].vec[1][0] != foundx){
								*index=icu->bezt[i].vec[1][0];
								*sel = 0;
								return chan;
							}
						}
					}
				}
			}
			ymax=ymin;
			
			/* Check constraint channels */
			for (conchan=chan->constraintChannels.first; conchan; conchan=conchan->next){
				ymin=ymax-(CHANNELHEIGHT+CHANNELSKIP);
				if (!((ymax < rectf.ymin) || (ymin > rectf.ymax)) && conchan->ipo) {
					for (icu=conchan->ipo->curve.first; icu; icu=icu->next){
						for (i=0; i<icu->totvert; i++){
							if (icu->bezt[i].vec[1][0] > xmin && icu->bezt[i].vec[1][0] <= xmax ){
								if (!firstchan){
									firstchan=chan;
									firstconchan=conchan;
									firstvert=icu->bezt[i].vec[1][0];
									*sel = icu->bezt[i].f2 & 1;	
								}
								
								if (icu->bezt[i].f2 & 1){ 
									if (!foundsel){
										foundsel=1;
										foundx = icu->bezt[i].vec[1][0];
									}
								}
								else if (foundsel && icu->bezt[i].vec[1][0] != foundx){
									*index=icu->bezt[i].vec[1][0];
									*sel = 0;
									*rchan = conchan;
									return chan;
								}
							}
						}
					}
				}
				ymax=ymin;
			}
		}
	}	
	
	*rchan = firstconchan;
	*index=firstvert;
	return firstchan;
}

static IpoCurve *get_nearest_meshchannel_key (float *index, short *sel)
{
	/* This function tries to find the RVK key that is
	 * closest to the user's mouse click
	 */
    Key      *key;
    IpoCurve *icu; 
    IpoCurve *firsticu=NULL;
    int	     foundsel=0;
    float    firstvert=-1, foundx=-1;
	int      i;
    short    mval[2];
    float    ymin, ymax, ybase;
    rctf     rectf;

    *index=0;

    key = get_action_mesh_key();
	
    /* lets get the mouse position and process it so 
     * we can start testing selections
     */
    getmouseco_areawin (mval);
    mval[0]-=7;
    areamouseco_to_ipoco(G.v2d, mval, &rectf.xmin, &rectf.ymin);
    mval[0]+=14;
    areamouseco_to_ipoco(G.v2d, mval, &rectf.xmax, &rectf.ymax);

    ybase = key->totkey * (CHANNELHEIGHT + CHANNELSKIP);
	ybase += CHANNELHEIGHT/2;
    *sel=0;

    /* lets loop through the IpoCurves trying to find the closest
     * bezier
     */
	if (!key->ipo) return NULL;
    for (icu = key->ipo->curve.first; icu ; icu = icu->next) {
        /* lets not deal with the "speed" Ipo
         */
        if (!icu->adrcode) continue;

        ymax = ybase	- (CHANNELHEIGHT+CHANNELSKIP)*(icu->adrcode-1);
        ymin=ymax-(CHANNELHEIGHT+CHANNELSKIP);

        /* Does this curve coorespond to the right
         * strip?
         */
        if (!((ymax < rectf.ymin) || (ymin > rectf.ymax))){
			
            /* loop through the beziers in the curve
             */
            for (i=0; i<icu->totvert; i++){

                /* Is this bezier in the right area?
                 */
                if (icu->bezt[i].vec[1][0] > rectf.xmin && 
                    icu->bezt[i].vec[1][0] <= rectf.xmax ){

                    /* if no other curves have been picked ...
                     */
                    if (!firsticu){
                        /* mark this curve/bezier as the first
                         * selected
                         */
                        firsticu=icu;
                        firstvert=icu->bezt[i].vec[1][0];

                        /* sel = (is the bezier is already selected) ? 1 : 0;
                         */
                        *sel = icu->bezt[i].f2 & 1;	
                    }

                    /* if the bezier is selected ...
                     */
                    if (icu->bezt[i].f2 & 1){ 
                        /* if we haven't found a selected one yet ...
                         */
                        if (!foundsel){
                            /* record the found x value
                             */
                            foundsel=1;
                            foundx = icu->bezt[i].vec[1][0];
                        }
                    }

                    /* if the bezier is unselected and not at the x
                     * position of a previous found selected bezier ...
                     */
                    else if (foundsel && icu->bezt[i].vec[1][0] != foundx){
                        /* lets return this found curve/bezier
                         */
                        *index=icu->bezt[i].vec[1][0];
                        *sel = 0;
                        return icu;
                    }
                }
            }
        }
	}
	
    /* return what we've found
     */
    *index=firstvert;
    return firsticu;
}

/* This function makes a list of the selected keyframes
 * in the ipo curves it has been passed
 */
static void make_sel_cfra_list(Ipo *ipo, ListBase *elems)
{
	IpoCurve *icu;
	BezTriple *bezt;
	int a;
	
	for(icu= ipo->curve.first; icu; icu= icu->next) {

		bezt= icu->bezt;
		if(bezt) {
			a= icu->totvert;
			while(a--) {
				if(bezt->f2 & 1) {
					add_to_cfra_elem(elems, bezt);
				}
				bezt++;
			}
		}
	}
}

/* This function selects all key frames in the same column(s) as a already selected key(s)
 * this version only works for Shape Keys, Key should be not NULL
 */
static void column_select_shapekeys(Key *key)
{

	if(key->ipo) {
		IpoCurve *icu;
		ListBase elems= {NULL, NULL};
		CfraElem *ce;
		
		/* create a list of all selected keys */
		make_sel_cfra_list(key->ipo, &elems);
		
		/* loop through all of the keys and select additional keyframes
			* based on the keys found to be selected above
			*/
		for(ce= elems.first; ce; ce= ce->next) {
			for (icu = key->ipo->curve.first; icu ; icu = icu->next) {
				BezTriple *bezt= icu->bezt;
				if(bezt) {
					int verts = icu->totvert;
					while(verts--) {
						if( ((int)ce->cfra) == ((int)bezt->vec[1][0]) ) {
							bezt->f2 |= 1;
						}
						bezt++;
					}
				}
			}
		}

		BLI_freelistN(&elems);
	}
}

/* This function selects all key frames in the same column(s) as a already selected key(s)
 * this version only works for on Action. *act should be not NULL
 */
static void column_select_actionkeys(bAction *act)
{
	IpoCurve *icu;
	BezTriple *bezt;
	ListBase elems= {NULL, NULL};
	CfraElem *ce;
	bActionChannel *chan;
	bConstraintChannel *conchan;

	/* create a list of all selected keys */
	for (chan=act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			if (chan->ipo)
				make_sel_cfra_list(chan->ipo, &elems);
			for (conchan=chan->constraintChannels.first; conchan; conchan=conchan->next) {
				if (conchan->ipo)
					make_sel_cfra_list(conchan->ipo, &elems);
			}
		}
	}

	/* loop through all of the keys and select additional keyframes
	 * based on the keys found to be selected above
	 */
	for (chan=act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			if (chan->ipo) {
				for(ce= elems.first; ce; ce= ce->next) {
					for (icu = chan->ipo->curve.first; icu; icu = icu->next){
						bezt= icu->bezt;
						if(bezt) {
							int verts = icu->totvert;
							while(verts--) {
						
								if( ((int)ce->cfra) == ((int)bezt->vec[1][0]) ) {
									bezt->f2 |= 1;
								}
								bezt++;
							}
						}
					}
				}
			}

			for (conchan=chan->constraintChannels.first; conchan; conchan=conchan->next) {
				if (conchan->ipo) {
					for(ce= elems.first; ce; ce= ce->next) {
						for (icu = conchan->ipo->curve.first; icu; icu = icu->next){
							bezt= icu->bezt;
							if(bezt) {
								int verts = icu->totvert;
								while(verts--) {
							
									if( ((int)ce->cfra) == ((int)bezt->vec[1][0]) ) {
										bezt->f2 |= 1;
									}
									bezt++;
								}
							}
						}
					}
				}
			}			
		}
	}
	BLI_freelistN(&elems);
}

/* apparently within active object context */
static void mouse_action(int selectmode)
{
	bAction	*act;
	short sel;
	float	selx;
	bActionChannel *chan;
	bConstraintChannel *conchan;
	short	mval[2];

	act=G.saction->action;
	if (!act)
		return;

	getmouseco_areawin (mval);

	chan=get_nearest_actionchannel_key(&selx, &sel, &conchan);

	if (chan){
		if (selectmode == SELECT_REPLACE) {
			selectmode = SELECT_ADD;
			
			deselect_actionchannel_keys(act, 0);
			deselect_actionchannels(act, 0);
			
			chan->flag |= ACHAN_SELECTED;
			hilight_channel (act, chan, 1);
			select_poseelement_by_name(chan->name, 2);	/* 2 is activate */
		}
		
		if (conchan)
			select_ipo_key(conchan->ipo, selx, selectmode);
		else
			select_ipo_key(chan->ipo, selx, selectmode);

		
		std_rmouse_transform(transform_actionchannel_keys);
		
		allqueue(REDRAWIPO, 0);
		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWACTION, 0);
		allqueue(REDRAWNLA, 0);
		allqueue(REDRAWOOPS, 0);
		allqueue(REDRAWBUTSALL, 0);
	}
}

static void mouse_mesh_action(int selectmode, Key *key)
{
	/* Handle a right mouse click selection in an
	 * action window displaying RVK data
	 */

    IpoCurve *icu;
    short  sel;
    float  selx;
    short  mval[2];

    /* going to assume that the only reason 
     * we got here is because it has been 
     * determined that we are a mesh with
     * the right properties (i.e., have key
     * data, etc)
     */

	/* get the click location, and the cooresponding
	 * ipo curve and selection time value
	 */
    getmouseco_areawin (mval);
    icu = get_nearest_meshchannel_key(&selx, &sel);

    if (icu){
        if (selectmode == SELECT_REPLACE) {
			/* if we had planned to replace the
			 * selection, then we will first deselect
			 * all of the keys, and if the clicked on
			 * key had been unselected, we will select 
			 * it, otherwise, we are done.
			 */
            deselect_meshchannel_keys(key, 0);

            if (sel == 0)
                selectmode = SELECT_ADD;
            else
				/* the key is selected so we should
				 * deselect -- but everything is now deselected
				 * so we are done.
				 */
				return;
        }
		
		/* select the key using the given mode
		 * and redraw as mush stuff as needed.
		 */
		select_icu_key(icu, selx, selectmode);

		BIF_undo_push("Select Action key");
        allqueue(REDRAWIPO, 0);
        allqueue(REDRAWVIEW3D, 0);
        allqueue(REDRAWACTION, 0);
        allqueue(REDRAWNLA, 0);

    }
}

void borderselect_action(void)
{ 
	rcti rect;
	rctf rectf;
	int val, selectmode;		
	short	mval[2];
	bActionChannel *chan;
	bConstraintChannel *conchan;
	bAction	*act;
	float	ymin, ymax;

	act=G.saction->action;

	if (!act)
		return;

	if ( (val = get_border(&rect, 3)) ){
		if (val == LEFTMOUSE)
			selectmode = SELECT_ADD;
		else
			selectmode = SELECT_SUBTRACT;

		mval[0]= rect.xmin;
		mval[1]= rect.ymin+2;
		areamouseco_to_ipoco(G.v2d, mval, &rectf.xmin, &rectf.ymin);
		mval[0]= rect.xmax;
		mval[1]= rect.ymax-2;
		areamouseco_to_ipoco(G.v2d, mval, &rectf.xmax, &rectf.ymax);
		
		/* if action is mapped in NLA, it returns a correction */
		if(G.saction->pin==0 && OBACT) {
			rectf.xmin= get_action_frame(OBACT, rectf.xmin);
			rectf.xmax= get_action_frame(OBACT, rectf.xmax);
		}
		
		ymax= count_action_levels(act) * (CHANNELHEIGHT+CHANNELSKIP);
		ymax += CHANNELHEIGHT/2;
		
		for (chan=act->chanbase.first; chan; chan=chan->next){
			if((chan->flag & ACHAN_HIDDEN)==0) {
				
				/* Check action */
				ymin=ymax-(CHANNELHEIGHT+CHANNELSKIP);
				if (!((ymax < rectf.ymin) || (ymin > rectf.ymax)))
					borderselect_ipo_key(chan->ipo, rectf.xmin, rectf.xmax,
								   selectmode);

				ymax=ymin;

				/* Check constraints */
				for (conchan=chan->constraintChannels.first; conchan; conchan=conchan->next){
					ymin=ymax-(CHANNELHEIGHT+CHANNELSKIP);
					if (!((ymax < rectf.ymin) || (ymin > rectf.ymax)))
						borderselect_ipo_key(conchan->ipo, rectf.xmin, rectf.xmax,
								   selectmode);
					
					ymax=ymin;
				}
			}
		}	
		BIF_undo_push("Border Select Action");
		allqueue(REDRAWNLA, 0);
		allqueue(REDRAWACTION, 0);
		allqueue(REDRAWIPO, 0);
	}
}

void borderselect_mesh(Key *key)
{ 
	rcti     rect;
	int      val, adrcodemax, adrcodemin;
	short	 mval[2];
	float	 xmin, xmax;
	int      (*select_function)(BezTriple *);
	IpoCurve *icu;

	if ( (val = get_border(&rect, 3)) ){
		/* set the selection function based on what
		 * mouse button had been used in the border
		 * select
		 */
		if (val == LEFTMOUSE)
			select_function = select_bezier_add;
		else
			select_function = select_bezier_subtract;

		/* get the minimum and maximum adrcode numbers
		 * for the IpoCurves (this is the number that
		 * relates an IpoCurve to the keyblock it
		 * controls).
		 */
		mval[0]= rect.xmin;
		mval[1]= rect.ymin+2;
		adrcodemax = get_nearest_key_num(key, mval, &xmin);
		adrcodemax = (adrcodemax >= key->totkey) ? key->totkey : adrcodemax;

		mval[0]= rect.xmax;
		mval[1]= rect.ymax-2;
		adrcodemin = get_nearest_key_num(key, mval, &xmax);
		adrcodemin = (adrcodemin < 1) ? 1 : adrcodemin;

		/* Lets loop throug the IpoCurves and do borderselect
		 * on the curves with adrcodes in our selected range.
		 */
		if(key->ipo) {
			for (icu = key->ipo->curve.first; icu ; icu = icu->next) {
				/* lets not deal with the "speed" Ipo
				 */
				if (!icu->adrcode) continue;
				if ( (icu->adrcode >= adrcodemin) && 
					 (icu->adrcode <= adrcodemax) ) {
					borderselect_icu_key(icu, xmin, xmax, select_function);
				}
			}
		}
		/* redraw stuff */
		BIF_undo_push("Border select Action Key");
		allqueue(REDRAWNLA, 0);
		allqueue(REDRAWACTION, 0);
		allqueue(REDRAWIPO, 0);
	}
}

/* ******************** action API ***************** */

/* generic get current action call, for action window context */
bAction *ob_get_action(Object *ob)
{
	bActionStrip *strip;
	
	if(ob->action)
		return ob->action;
	
	for (strip=ob->nlastrips.first; strip; strip=strip->next){
		if (strip->flag & ACTSTRIP_SELECT)
			return strip->act;
	}
	return NULL;
}

/* used by ipo, outliner, buttons to find the active channel */
bActionChannel* get_hilighted_action_channel(bAction* action)
{
	bActionChannel *chan;

	if (!action)
		return NULL;

	for (chan=action->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0)
			if (chan->flag & ACHAN_SELECTED && chan->flag & ACHAN_HILIGHTED)
				return chan;
	}

	return NULL;

}

void set_exprap_action(int mode)
{
	if(G.saction->action && G.saction->action->id.lib) return;

	error ("Not yet implemented!");
}

bAction *add_empty_action(int blocktype)
{
	bAction *act;
	char *str= "Action";
	
	if(blocktype==ID_OB)
		str= "ObAction";
	else if(blocktype==ID_KE)
		str= "ShapeAction";
	
	act= alloc_libblock(&G.main->action, ID_AC, str);
	act->id.flag |= LIB_FAKEUSER;
	act->id.us++;
	return act;
}

void transform_actionchannel_keys(int mode, int dummy)
{
	bAction	*act;
	TransVert *tv;
	Object *ob= OBACT;
	bConstraintChannel *conchan;
	bActionChannel	*chan;
	float	deltax, startx;
	float	minx, maxx, cenf[2];
	float	sval[2], cval[2], lastcval[2]={0,0};
	float	fac=0.0f;
	int		loop=1;
	int		tvtot=0;
	int		invert=0, firsttime=1;
	int		i;
	short	cancel=0;
	short	mvals[2], mvalc[2], cent[2];
	char	str[256];

	act=G.saction->action;
	if(act==NULL) return;
	
	/* Ensure that partial selections result in beztriple selections */
	for (chan=act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			tvtot+=fullselect_ipo_keys(chan->ipo);

			for (conchan=chan->constraintChannels.first; conchan; conchan=conchan->next)
				tvtot+=fullselect_ipo_keys(conchan->ipo);
		}
	}
	
	/* If nothing is selected, bail out */
	if (!tvtot)
		return;
	
	
	/* Build the transvert structure */
	tv = MEM_callocN (sizeof(TransVert) * tvtot, "transVert");
	
	tvtot=0;
	for (chan=act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			/* Add the actionchannel */
			tvtot = add_trans_ipo_keys(chan->ipo, tv, tvtot);
			for (conchan=chan->constraintChannels.first; conchan; conchan=conchan->next)
				tvtot = add_trans_ipo_keys(conchan->ipo, tv, tvtot);
		}
	}
	
	/* min max, only every other three */
	minx= maxx= tv[1].loc[0];
	for (i=1; i<tvtot; i+=3){
		if(minx>tv[i].loc[0]) minx= tv[i].loc[0];
		if(maxx<tv[i].loc[0]) maxx= tv[i].loc[0];
	}
	
	/* Do the event loop */
	cent[0] = curarea->winx + (G.saction->v2d.hor.xmax)/2;
	cent[1] = curarea->winy + (G.saction->v2d.hor.ymax)/2;
	areamouseco_to_ipoco(G.v2d, cent, &cenf[0], &cenf[1]);

	getmouseco_areawin (mvals);
	areamouseco_to_ipoco(G.v2d, mvals, &sval[0], &sval[1]);

	if(G.saction->pin==0 && OBACT)
		sval[0]= get_action_frame(OBACT, sval[0]);
	
	/* used for drawing */
	if(mode=='t') {
		G.saction->flag |= SACTION_MOVING;
		G.saction->timeslide= sval[0];
	}
	
	startx=sval[0];
	while (loop) {
		
		if(mode=='t' && minx==maxx)
			break;
		
		/*		Get the input */
		/*		If we're cancelling, reset transformations */
		/*			Else calc new transformation */
		/*		Perform the transformations */
		while (qtest()) {
			short val;
			unsigned short event= extern_qread(&val);

			if (val) {
				switch (event) {
				case LEFTMOUSE:
				case SPACEKEY:
				case RETKEY:
					loop=0;
					break;
				case XKEY:
					break;
				case ESCKEY:
				case RIGHTMOUSE:
					cancel=1;
					loop=0;
					break;
				default:
					arrows_move_cursor(event);
					break;
				};
			}
		}

		if (cancel) {
			for (i=0; i<tvtot; i++) {
				tv[i].loc[0]=tv[i].oldloc[0];
				tv[i].loc[1]=tv[i].oldloc[1];
			}
		} else {
			getmouseco_areawin (mvalc);
			areamouseco_to_ipoco(G.v2d, mvalc, &cval[0], &cval[1]);
			
			if(G.saction->pin==0 && OBACT)
				cval[0]= get_action_frame(OBACT, cval[0]);

			if(mode=='t')
				G.saction->timeslide= cval[0];
			
			if (!firsttime && lastcval[0]==cval[0] && lastcval[1]==cval[1]) {
				PIL_sleep_ms(1);
			} else {
				
				for (i=0; i<tvtot; i++){
					tv[i].loc[0]=tv[i].oldloc[0];

					switch (mode){
					case 't':
						if( sval[0] > minx && sval[0] < maxx) {
							float timefac, cvalc= CLAMPIS(cval[0], minx, maxx);
							
							/* left half */
							if(tv[i].oldloc[0] < sval[0]) {
								timefac= ( sval[0] - tv[i].oldloc[0])/(sval[0] - minx);
								tv[i].loc[0]= cvalc - timefac*( cvalc - minx);
							}
							else {
								timefac= (tv[i].oldloc[0] - sval[0])/(maxx - sval[0]);
								tv[i].loc[0]= cvalc + timefac*(maxx- cvalc);
							}
						}
						break;
					case 'g':
						deltax = cval[0]-sval[0];
						fac= deltax;
						
						apply_keyb_grid(&fac, 0.0, 1.0, 0.1, U.flag & USER_AUTOGRABGRID);

						tv[i].loc[0]+=fac;
						break;
					case 's':
						startx=mvals[0]-(ACTWIDTH/2+(curarea->winrct.xmax-curarea->winrct.xmin)/2);
						deltax=mvalc[0]-(ACTWIDTH/2+(curarea->winrct.xmax-curarea->winrct.xmin)/2);
						fac= fabs(deltax/startx);
						
						apply_keyb_grid(&fac, 0.0, 0.2, 0.1, U.flag & USER_AUTOSIZEGRID);
		
						if (invert){
							if (i % 03 == 0){
								memcpy (tv[i].loc, tv[i].oldloc, sizeof(tv[i+2].oldloc));
							}
							if (i % 03 == 2){
								memcpy (tv[i].loc, tv[i].oldloc, sizeof(tv[i-2].oldloc));
							}
	
							fac*=-1;
						}
						startx= (G.scene->r.cfra);
						if(G.saction->pin==0 && OBACT)
							startx= get_action_frame(OBACT, startx);
							
						tv[i].loc[0]-= startx;
						tv[i].loc[0]*=fac;
						tv[i].loc[0]+= startx;
		
						break;
					}
				}
	
				if (mode=='s'){
					sprintf(str, "scaleX: %.3f", fac);
					headerprint(str);
				}
				else if (mode=='g'){
					sprintf(str, "deltaX: %.3f", fac);
					headerprint(str);
				}
				else if (mode=='t') {
					float fac= 2.0*(cval[0]-sval[0])/(maxx-minx);
					CLAMP(fac, -1.0f, 1.0f);
					sprintf(str, "TimeSlide: %.3f", fac);
					headerprint(str);
				}
		
				if (G.saction->lock) {
					if(ob) {
						ob->ctime= -1234567.0f;
						if(ob->pose || ob_get_key(ob))
							DAG_object_flush_update(G.scene, ob, OB_RECALC);
						else
							DAG_object_flush_update(G.scene, ob, OB_RECALC_OB);
					}
					force_draw_plus(SPACE_VIEW3D, 0);
				}
				else {
					force_draw(0);
				}
			}
		}
		
		lastcval[0]= cval[0];
		lastcval[1]= cval[1];
		firsttime= 0;
	}
	
	/*		Update the curve */
	/*		Depending on the lock status, draw necessary views */

	if(ob) {
		ob->ctime= -1234567.0f;

		if(ob->pose || ob_get_key(ob))
			DAG_object_flush_update(G.scene, ob, OB_RECALC);
		else
			DAG_object_flush_update(G.scene, ob, OB_RECALC_OB);
	}
	
	remake_action_ipos(act);

	G.saction->flag &= ~SACTION_MOVING;
	
	if(cancel==0) BIF_undo_push("Transform Action");
	allqueue (REDRAWVIEW3D, 0);
	allqueue (REDRAWACTION, 0);
	allqueue(REDRAWNLA, 0);
	allqueue (REDRAWIPO, 0);
	allqueue(REDRAWTIME, 0);
	MEM_freeN (tv);
}

void transform_meshchannel_keys(char mode, Key *key)
{
	/* this is the function that determines what happens
	 * to those little blocky rvk key things you have selected 
	 * after you press a 'g' or an 's'. I'd love to say that
	 * I have an intimate knowledge of all of what this function
	 * is doing, but instead I'm just going to pretend.
	 */
    TransVert *tv;
    int /*sel=0,*/  i;
    short	mvals[2], mvalc[2], cent[2];
    float	sval[2], cval[2], lastcval[2]={0,0};
    short	cancel=0;
    float	fac=0.0F;
    int		loop=1;
    int		tvtot=0;
    float	deltax, startx;
    float	cenf[2];
    int		invert=0, firsttime=1;
    char	str[256];

	/* count all of the selected beziers, and
	 * set all 3 control handles to selected
	 */
    tvtot=fullselect_ipo_keys(key->ipo);
    
    /* If nothing is selected, bail out 
	 */
    if (!tvtot)
        return;
	
	
    /* Build the transvert structure 
	 */
    tv = MEM_callocN (sizeof(TransVert) * tvtot, "transVert");
    tvtot=0;

    tvtot = add_trans_ipo_keys(key->ipo, tv, tvtot);

    /* Do the event loop 
	 */
    cent[0] = curarea->winx + (G.saction->v2d.hor.xmax)/2;
    cent[1] = curarea->winy + (G.saction->v2d.hor.ymax)/2;
    areamouseco_to_ipoco(G.v2d, cent, &cenf[0], &cenf[1]);

    getmouseco_areawin (mvals);
    areamouseco_to_ipoco(G.v2d, mvals, &sval[0], &sval[1]);

    startx=sval[0];
    while (loop) {
        /* Get the input
		 * If we're cancelling, reset transformations
		 * Else calc new transformation
		 * Perform the transformations 
		 */
        while (qtest()) {
            short val;
            unsigned short event= extern_qread(&val);

            if (val) {
                switch (event) {
                case LEFTMOUSE:
                case SPACEKEY:
                case RETKEY:
                    loop=0;
                    break;
                case XKEY:
                    break;
                case ESCKEY:
                case RIGHTMOUSE:
                    cancel=1;
                    loop=0;
                    break;
                default:
                    arrows_move_cursor(event);
                    break;
                };
            }
        }
        
        if (cancel) {
            for (i=0; i<tvtot; i++) {
                tv[i].loc[0]=tv[i].oldloc[0];
                tv[i].loc[1]=tv[i].oldloc[1];
            }
        } 
		else {
            getmouseco_areawin (mvalc);
            areamouseco_to_ipoco(G.v2d, mvalc, &cval[0], &cval[1]);
			
            if (!firsttime && lastcval[0]==cval[0] && lastcval[1]==cval[1]) {
                PIL_sleep_ms(1);
            } else {
                for (i=0; i<tvtot; i++){
                    tv[i].loc[0]=tv[i].oldloc[0];

                    switch (mode){
                    case 'g':
                        deltax = cval[0]-sval[0];
                        fac= deltax;
						
                        apply_keyb_grid(&fac, 0.0, 1.0, 0.1, 
                                        U.flag & USER_AUTOGRABGRID);

                        tv[i].loc[0]+=fac;
                        break;
                    case 's':
                        startx=mvals[0]-(ACTWIDTH/2+(curarea->winrct.xmax
                                                     -curarea->winrct.xmin)/2);
                        deltax=mvalc[0]-(ACTWIDTH/2+(curarea->winrct.xmax
                                                     -curarea->winrct.xmin)/2);
                        fac= fabs(deltax/startx);
						
                        apply_keyb_grid(&fac, 0.0, 0.2, 0.1, 
                                        U.flag & USER_AUTOSIZEGRID);
		
                        if (invert){
                            if (i % 03 == 0){
                                memcpy (tv[i].loc, tv[i].oldloc, 
                                        sizeof(tv[i+2].oldloc));
                            }
                            if (i % 03 == 2){
                                memcpy (tv[i].loc, tv[i].oldloc, 
                                        sizeof(tv[i-2].oldloc));
                            }
							
                            fac*=-1;
                        }
                        startx= (G.scene->r.cfra);
                        
                        tv[i].loc[0]-= startx;
                        tv[i].loc[0]*=fac;
                        tv[i].loc[0]+= startx;
		
                        break;
                    }
                }
            }
			/* Display a message showing the magnitude of
			 * the grab/scale we are performing
			 */
            if (mode=='s'){
                sprintf(str, "scaleX: %.3f", fac);
                headerprint(str);
            }
            else if (mode=='g'){
                sprintf(str, "deltaX: %.3f", fac);
                headerprint(str);
            }
	
            if (G.saction->lock){
				/* doubt any of this code ever gets
				 * executed, but it might in the
				 * future
				 */
				 
				DAG_object_flush_update(G.scene, OBACT, OB_RECALC_OB|OB_RECALC_DATA);
                allqueue (REDRAWVIEW3D, 0);
                allqueue (REDRAWACTION, 0);
                allqueue (REDRAWIPO, 0);
                allqueue(REDRAWNLA, 0);
				allqueue(REDRAWTIME, 0);
                force_draw_all(0);
            }
            else {
                addqueue (curarea->win, REDRAWALL, 0);
                force_draw(0);
            }
        }
		
        lastcval[0]= cval[0];
        lastcval[1]= cval[1];
        firsttime= 0;
    }
	
	/* fix up the Ipocurves and redraw stuff
	 */
    meshkey_do_redraw(key);
	BIF_undo_push("Transform Action Keys");

    MEM_freeN (tv);

	/* did you understand all of that? I pretty much understand
	 * what it does, but the specifics seem a little weird and crufty.
	 */
}

void deselect_actionchannel_keys (bAction *act, int test)
{
	bActionChannel	*chan;
	bConstraintChannel *conchan;
	int		sel=1;;

	if (!act)
		return;

	/* Determine if this is selection or deselection */
	
	if (test){
		for (chan=act->chanbase.first; chan; chan=chan->next){
			if((chan->flag & ACHAN_HIDDEN)==0) {
				/* Test the channel ipos */
				if (is_ipo_key_selected(chan->ipo)){
					sel = 0;
					break;
				}

				/* Test the constraint ipos */
				for (conchan=chan->constraintChannels.first; conchan; conchan=conchan->next){
					if (is_ipo_key_selected(conchan->ipo)){
						sel = 0;
						break;
					}
				}

				if (sel == 0)
					break;
			}
		}
	}
	else
		sel=0;
	
	/* Set the flags */
	for (chan=act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			set_ipo_key_selection(chan->ipo, sel);
			for (conchan=chan->constraintChannels.first; conchan; conchan=conchan->next)
				set_ipo_key_selection(conchan->ipo, sel);
		}
	}
}

void deselect_meshchannel_keys (Key *key, int test)
{
	/* should deselect the rvk keys
	 */
    int		sel=1;

    /* Determine if this is selection or deselection */
    if (test){
        if (is_ipo_key_selected(key->ipo)){
            sel = 0;
        }
    }
    else {
        sel=0;
    }
	
    /* Set the flags */
    set_ipo_key_selection(key->ipo, sel);
}

/* apparently within active object context */
void deselect_actionchannels (bAction *act, int test)
{
	bActionChannel *chan;
	bConstraintChannel *conchan;
	int			sel=1;	

	if (!act)
		return;

	/* See if we should be selecting or deselecting */
	if (test){
		for (chan=act->chanbase.first; chan; chan=chan->next){
			if((chan->flag & ACHAN_HIDDEN)==0) {
				if (!sel)
					break;

				if (chan->flag & ACHAN_SELECTED){
					sel=0;
					break;
				}
				if (sel){
					for (conchan=chan->constraintChannels.first; conchan; conchan=conchan->next){
						if (conchan->flag & CONSTRAINT_CHANNEL_SELECT){
							sel=0;
							break;
						}
					}
				}
			}
		}
	}
	else
		sel=0;

	/* Now set the flags */
	for (chan=act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			select_poseelement_by_name(chan->name, sel);

			if (sel)
				chan->flag |= ACHAN_SELECTED;
			else
				chan->flag &= ~ACHAN_SELECTED;

			for (conchan=chan->constraintChannels.first; conchan; conchan=conchan->next){
				if (sel)
					conchan->flag |= CONSTRAINT_CHANNEL_SELECT;
				else
					conchan->flag &= ~CONSTRAINT_CHANNEL_SELECT;
			}
		}
	}

}

static void hilight_channel (bAction *act, bActionChannel *chan, short select)
{
	bActionChannel *curchan;

	if (!act)
		return;

	for (curchan=act->chanbase.first; curchan; curchan=curchan->next){
		if (curchan==chan && select)
			curchan->flag |= ACHAN_HILIGHTED;
		else
			curchan->flag &= ~ACHAN_HILIGHTED;
	}
}

/* select_mode = SELECT_REPLACE
 *             = SELECT_ADD
 *             = SELECT_SUBTRACT
 *             = SELECT_INVERT
 */

/* exported for outliner (ton) */
/* apparently within active object context */
int select_channel(bAction *act, bActionChannel *chan,
                          int selectmode) 
{
	/* Select the channel based on the selection mode
	 */
	int flag;

	switch (selectmode) {
	case SELECT_ADD:
		chan->flag |= ACHAN_SELECTED;
		break;
	case SELECT_SUBTRACT:
		chan->flag &= ~ACHAN_SELECTED;
		break;
	case SELECT_INVERT:
		chan->flag ^= ACHAN_SELECTED;
		break;
	}
	flag = (chan->flag & ACHAN_SELECTED) ? 1 : 0;

	hilight_channel(act, chan, flag);
	select_poseelement_by_name(chan->name, flag);

	return flag;
}

static int select_constraint_channel(bAction *act, 
                                     bConstraintChannel *conchan, 
                                     int selectmode) {
	/* Select the constraint channel based on the selection mode
	 */
	int flag;

	switch (selectmode) {
	case SELECT_ADD:
		conchan->flag |= CONSTRAINT_CHANNEL_SELECT;
		break;
	case SELECT_SUBTRACT:
		conchan->flag &= ~CONSTRAINT_CHANNEL_SELECT;
		break;
	case SELECT_INVERT:
		conchan->flag ^= CONSTRAINT_CHANNEL_SELECT;
		break;
	}
	flag = (conchan->flag & CONSTRAINT_CHANNEL_SELECT) ? 1 : 0;

	return flag;
}

/* lefthand side */
static void mouse_actionchannels(bAction *act, short *mval,
                                 short *mvalo, int selectmode) {
	/* Select action channels, based on mouse values.
	 * If mvalo is NULL we assume it is a one click
	 * action, other wise we treat it like it is a
	 * border select with mval[0],mval[1] and
	 * mvalo[0], mvalo[1] forming the corners of
	 * a rectangle.
	 */
	bActionChannel *chan;
	float	click, x,y;
	int   clickmin, clickmax;
	int		wsize, sel;
	bConstraintChannel *conchan;

	if (!act)
		return;
  
	if (selectmode == SELECT_REPLACE) {
		deselect_actionchannels (act, 0);
		selectmode = SELECT_ADD;
	}

	/* wsize is the greatest possible height (in pixels) that would be
	 * needed to draw all of the action channels and constraint
	 * channels.
	 */
	wsize =  count_action_levels(act)*(CHANNELHEIGHT+CHANNELSKIP);
	wsize += CHANNELHEIGHT/2;

    areamouseco_to_ipoco(G.v2d, mval, &x, &y);
    clickmin = (int) ((wsize - y) / (CHANNELHEIGHT+CHANNELSKIP));
	
	/* Only one click */
	if (mvalo == NULL) {
		clickmax = clickmin;
	}
	/* Two click values (i.e., border select */
	else {
		areamouseco_to_ipoco(G.v2d, mvalo, &x, &y);
		click = ((wsize - y) / (CHANNELHEIGHT+CHANNELSKIP));

		if ( ((int) click) < clickmin) {
			clickmax = clickmin;
			clickmin = (int) click;
		}
		else {
			clickmax = (int) click;
		}
	}

	if (clickmax < 0) {
		return;
	}

	/* clickmin and clickmax now coorespond to indices into
	 * the collection of channels and constraint channels.
	 * What we need to do is apply the selection mode on all
	 * channels and constraint channels between these indices.
	 * This is done by traversing the channels and constraint
	 * channels, for each item decrementing clickmin and clickmax.
	 * When clickmin is less than zero we start selecting stuff,
	 * until clickmax is less than zero or we run out of channels
	 * and constraint channels.
	 */

	for (chan = act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			if (clickmax < 0) break;

			if ( clickmin <= 0) {
				/* Select the channel with the given mode. If the
				 * channel is freshly selected then set it to the
				 * active channel for the action
				 */
				sel = (chan->flag & ACHAN_SELECTED);
				select_channel(act, chan, selectmode);
				/* messy... */
				select_poseelement_by_name(chan->name, 2);
				
			}
			--clickmin;
			--clickmax;

			/* Check for click in a constraint */
			for (conchan=chan->constraintChannels.first; 
				 conchan; conchan=conchan->next){
				if (clickmax < 0) break;
				if ( clickmin <= 0) {
					select_constraint_channel(act, conchan, selectmode);
				}
				--clickmin;
				--clickmax;
			}
		}
	}

	allqueue (REDRAWIPO, 0);
	allqueue (REDRAWVIEW3D, 0);
	allqueue (REDRAWACTION, 0);
	allqueue (REDRAWNLA, 0);
	allqueue (REDRAWOOPS, 0);
	allqueue (REDRAWBUTSALL, 0);
}

void delete_meshchannel_keys(Key *key)
{
	if (!okee("Erase selected keys"))
		return;

	BIF_undo_push("Delete Action keys");
	delete_ipo_keys(key->ipo);

	meshkey_do_redraw(key);
}

void delete_actionchannel_keys(void)
{
	bAction *act;
	bActionChannel *chan;
	bConstraintChannel *conchan;

	act = G.saction->action;
	if (!act)
		return;

	if (!okee("Erase selected keys"))
		return;

	for (chan = act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {

			/* Check action channel keys*/
			delete_ipo_keys(chan->ipo);

			/* Delete constraint channel keys */
			for (conchan=chan->constraintChannels.first; conchan; conchan=conchan->next)
				delete_ipo_keys(conchan->ipo);
		}
	}

	remake_action_ipos (act);
	BIF_undo_push("Delete Action keys");
	allspace(REMAKEIPO, 0);
	allqueue(REDRAWACTION, 0);
	allqueue(REDRAWIPO, 0);
	allqueue(REDRAWNLA, 0);

}

static void delete_actionchannels (void)
{
	bConstraintChannel *conchan=NULL, *nextconchan;
	bActionChannel *chan, *next;
	bAction	*act;
	int freechan;

	act=G.saction->action;

	if (!act)
		return;

	for (chan=act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			if (chan->flag & ACHAN_SELECTED)
				break;
			for (conchan=chan->constraintChannels.first; conchan; conchan=conchan->next)
			{
				if (conchan->flag & CONSTRAINT_CHANNEL_SELECT){
					chan=act->chanbase.last;
					break;
				}
			}
		}
	}

	if (!chan && !conchan)
		return;

	if (!okee("Erase selected channels"))
		return;

	for (chan=act->chanbase.first; chan; chan=next){
		freechan = 0;
		next=chan->next;
		if((chan->flag & ACHAN_HIDDEN)==0) {
			
			/* Remove action channels */
			if (chan->flag & ACHAN_SELECTED){
				if (chan->ipo)
					chan->ipo->id.us--;	/* Release the ipo */
				freechan = 1;
			}
			
			/* Remove constraint channels */
			for (conchan=chan->constraintChannels.first; conchan; conchan=nextconchan){
				nextconchan=conchan->next;
				if (freechan || conchan->flag & CONSTRAINT_CHANNEL_SELECT){
					if (conchan->ipo)
						conchan->ipo->id.us--;
					BLI_freelinkN(&chan->constraintChannels, conchan);
				}
			}
			
			if (freechan)
				BLI_freelinkN (&act->chanbase, chan);
		}
	}

	BIF_undo_push("Delete Action channels");
	allqueue (REDRAWACTION, 0);
	allqueue(REDRAWNLA, 0);

}

void sethandles_meshchannel_keys(int code, Key *key)
{
	
    sethandles_ipo_keys(key->ipo, code);

	BIF_undo_push("Set handles Action keys");
	meshkey_do_redraw(key);
}

void sethandles_actionchannel_keys(int code)
{
	bAction *act;
	bActionChannel *chan;

	/* Get the selected action, exit if none are selected 
	 */
	act = G.saction->action;
	if (!act)
		return;

	/* Loop through the channels and set the beziers
	 * of the selected keys based on the integer code
	 */
	for (chan = act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0)
			sethandles_ipo_keys(chan->ipo, code);
	}

	/* Clean up and redraw stuff
	 */
	remake_action_ipos (act);
	BIF_undo_push("Set handles Action channel");
	allspace(REMAKEIPO, 0);
	allqueue(REDRAWACTION, 0);
	allqueue(REDRAWIPO, 0);
	allqueue(REDRAWNLA, 0);
}

void set_ipotype_actionchannels(int ipotype) 
{

	bAction *act; 
	bActionChannel *chan;
	bConstraintChannel *conchan;
	short event;

	/* Get the selected action, exit if none are selected 
	 */
	act = G.saction->action;
	if (!act)
		return;

	if (ipotype == SET_IPO_POPUP) {
		/* Present a popup menu asking the user what type
		 * of IPO curve he/she/GreenBTH wants. ;)
		 */
		event
			=  pupmenu("Channel Ipo Type %t|"
					   "Constant %x1|"
					   "Linear %x2|"
					   "Bezier %x3");
		if(event < 1) return;
		ipotype = event;
	}
	
	/* Loop through the channels and for the selected ones set
	 * the type for each Ipo curve in the channel Ipo (based on
	 * the value from the popup).
	 */
	for (chan = act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			if (chan->flag & ACHAN_SELECTED){
				if (chan->ipo)
					setipotype_ipo(chan->ipo, ipotype);
			}
			/* constraint channels */
			for (conchan=chan->constraintChannels.first; conchan; conchan= conchan->next) {
				if (conchan->flag & CONSTRAINT_CHANNEL_SELECT) {
					if (conchan->ipo)
						setipotype_ipo(conchan->ipo, ipotype);
				}
			}
			
		}
	}

	/* Clean up and redraw stuff
	 */
	remake_action_ipos (act);
	BIF_undo_push("Set Ipo type Action channel");
	allspace(REMAKEIPO, 0);
	allqueue(REDRAWACTION, 0);
	allqueue(REDRAWIPO, 0);
	allqueue(REDRAWNLA, 0);
}

void set_extendtype_actionchannels(int extendtype)
{
	bAction *act; 
	bActionChannel *chan;
	bConstraintChannel *conchan;
	short event;

	/* Get the selected action, exit if none are selected 
	 */
	act = G.saction->action;
	if (!act)
		return;

	if (extendtype == SET_EXTEND_POPUP) {
		/* Present a popup menu asking the user what type
		 * of IPO curve he/she/GreenBTH wants. ;)
		 */
		event
			=  pupmenu("Channel Extending Type %t|"
					   "Constant %x1|"
					   "Extrapolation %x2|"
					   "Cyclic %x3|"
					   "Cyclic extrapolation %x4");
		if(event < 1) return;
		extendtype = event;
	}
	
	/* Loop through the channels and for the selected ones set
	 * the type for each Ipo curve in the channel Ipo (based on
	 * the value from the popup).
	 */
	for (chan = act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			if (chan->flag & ACHAN_SELECTED) {
				if (chan->ipo) {
					switch (extendtype) {
					case SET_EXTEND_CONSTANT:
						setexprap_ipoloop(chan->ipo, IPO_HORIZ);
						break;
					case SET_EXTEND_EXTRAPOLATION:
						setexprap_ipoloop(chan->ipo, IPO_DIR);
						break;
					case SET_EXTEND_CYCLIC:
						setexprap_ipoloop(chan->ipo, IPO_CYCL);
						break;
					case SET_EXTEND_CYCLICEXTRAPOLATION:
						setexprap_ipoloop(chan->ipo, IPO_CYCLX);
						break;
					}
				}
			}
			/* constraint channels */
			for (conchan=chan->constraintChannels.first; conchan; conchan= conchan->next) {
				if (conchan->flag & CONSTRAINT_CHANNEL_SELECT) {
					if (conchan->ipo) {
						switch (extendtype) {
							case SET_EXTEND_CONSTANT:
								setexprap_ipoloop(conchan->ipo, IPO_HORIZ);
								break;
							case SET_EXTEND_EXTRAPOLATION:
								setexprap_ipoloop(conchan->ipo, IPO_DIR);
								break;
							case SET_EXTEND_CYCLIC:
								setexprap_ipoloop(conchan->ipo, IPO_CYCL);
								break;
							case SET_EXTEND_CYCLICEXTRAPOLATION:
								setexprap_ipoloop(conchan->ipo, IPO_CYCLX);
								break;
						}
					}
				}
			}
		}
	}

	/* Clean up and redraw stuff
	 */
	remake_action_ipos (act);
	BIF_undo_push("Set Ipo type Action channel");
	allspace(REMAKEIPO, 0);
	allqueue(REDRAWACTION, 0);
	allqueue(REDRAWIPO, 0);
	allqueue(REDRAWNLA, 0);
}

static void set_snap_actionchannels(bAction *act, short snaptype) 
{
	/* snapping function for action channels*/
	bActionChannel *chan;
	bConstraintChannel *conchan;
	
	/* Loop through the channels */
	for (chan = act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			if (chan->ipo) {
				snap_ipo_keys(chan->ipo, snaptype);
			}
			/* constraint channels */
			for (conchan=chan->constraintChannels.first; conchan; conchan= conchan->next) {
				if (conchan->ipo) {
					snap_ipo_keys(conchan->ipo, snaptype);
				}
			}						
		}
	}
}

static void set_snap_meshchannels(Key *key, short snaptype) 
{
	/* snapping function for mesh channels */
	if(key->ipo) {
		snap_ipo_keys(key->ipo, snaptype);
	}
}


void snap_keys_to_frame() 
{
	/* This function is the generic entry-point for snapping keyframes
	 * to a frame(s). It passes the work off to sub-functions for the 
	 * different types in the action editor.
	 */
	 
	SpaceAction *saction;
	bAction *act;
	Key *key;
	short event;

	/* get data */
	saction= curarea->spacedata.first;
	if (!saction) return;
	act = saction->action;
	key = get_action_mesh_key();
	
	/* find the type of snapping to do */
	event = pupmenu("Snap Frames To%t|Nearest Frame%x1|Current Frame%x2");
	
	/* handle events */
	switch (event) {
		case 1: /* snap to nearest frame */
			if (act) 
				set_snap_actionchannels(act, event);
			else
				set_snap_meshchannels(key, event);
			
			/* Clean up and redraw stuff */
			remake_action_ipos (act);
			BIF_undo_push("Snap To Nearest Frame");
			allspace(REMAKEIPO, 0);
			allqueue(REDRAWACTION, 0);
			allqueue(REDRAWIPO, 0);
			allqueue(REDRAWNLA, 0);
			
			break;
		case 2: /* snap to current frame */
			if (act) 
				set_snap_actionchannels(act, event);
			else
				set_snap_meshchannels(key, event);
			
			/* Clean up and redraw stuff */
			remake_action_ipos (act);
			BIF_undo_push("Snap To Current Frame");
			allspace(REMAKEIPO, 0);
			allqueue(REDRAWACTION, 0);
			allqueue(REDRAWIPO, 0);
			allqueue(REDRAWNLA, 0);
			
			break;
	}
}


static void select_all_keys_frames(bAction *act, short *mval, 
							short *mvalo, int selectmode) {
	
	/* This function tries to select all action keys in
	 * every channel for a given range of keyframes that
	 * are within the mouse values mval and mvalo (usually
	 * the result of a border select). If mvalo is passed as
	 * NULL then the selection is treated as a one-click and
	 * the function tries to select all keys within half a
	 * frame of the click point.
	 */
	
	rcti rect;
	rctf rectf;
	bActionChannel *chan;
	bConstraintChannel *conchan;

	if (!act)
		return;

	if (selectmode == SELECT_REPLACE) {
		deselect_actionchannel_keys(act, 0);
		selectmode = SELECT_ADD;
	}

	if (mvalo == NULL) {
		rect.xmin = rect.xmax = mval[0];
		rect.ymin = rect.ymax = mval[1];
	}
	else {
		if (mval[0] < mvalo[0] ) {
			rect.xmin = mval[0];
			rect.xmax = mvalo[0];
		}
		else {
			rect.xmin = mvalo[0];
			rect.xmax = mval[0];
		}
		if (mval[1] < mvalo[1] ) {
			rect.ymin = mval[1];
			rect.ymax = mvalo[1];
		}
		else {
			rect.ymin = mvalo[1];
			rect.ymax = mval[1];
		}
	}

	mval[0]= rect.xmin;
	mval[1]= rect.ymin+2;
	areamouseco_to_ipoco(G.v2d, mval, &rectf.xmin, &rectf.ymin);
	mval[0]= rect.xmax;
	mval[1]= rect.ymax-2;
	areamouseco_to_ipoco(G.v2d, mval, &rectf.xmax, &rectf.ymax);

	if (mvalo == NULL) {
		rectf.xmin = rectf.xmin - 0.5;
		rectf.xmax = rectf.xmax + 0.5;
	}
    
	for (chan=act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			borderselect_ipo_key(chan->ipo, rectf.xmin, rectf.xmax,
								 selectmode);
			for (conchan=chan->constraintChannels.first; conchan; 
				 conchan=conchan->next){
				borderselect_ipo_key(conchan->ipo, rectf.xmin, rectf.xmax,
									 selectmode);
			}
		}
	}	

	allqueue(REDRAWNLA, 0);
	allqueue(REDRAWACTION, 0);
	allqueue(REDRAWIPO, 0);
}


static void select_all_keys_channels(bAction *act, short *mval, 
                              short *mvalo, int selectmode) {
	bActionChannel    *chan;
	float              click, x,y;
	int                clickmin, clickmax;
	int                wsize;
	bConstraintChannel *conchan;

	/* This function selects all the action keys that
	 * are in the mouse selection range defined by
	 * the ordered pairs mval and mvalo (usually
	 * these 2 are obtained from a border select).
	 * If mvalo is NULL, then the selection is
	 * treated like a one-click action, and at most
	 * one channel is selected.
	 */

	/* If the action is null then abort
	 */
	if (!act)
		return;

	if (selectmode == SELECT_REPLACE) {
		deselect_actionchannel_keys(act, 0);
		selectmode = SELECT_ADD;
	}

	/* wsize is the greatest possible height (in pixels) that would be
	 * needed to draw all of the action channels and constraint
	 * channels.
	 */

	wsize =  count_action_levels(act)*(CHANNELHEIGHT+CHANNELSKIP);
	wsize += CHANNELHEIGHT/2;
	
    areamouseco_to_ipoco(G.v2d, mval, &x, &y);
    clickmin = (int) ((wsize - y) / (CHANNELHEIGHT+CHANNELSKIP));
	
	/* Only one click */
	if (mvalo == NULL) {
		clickmax = clickmin;
	}
	/* Two click values (i.e., border select) */
	else {

		areamouseco_to_ipoco(G.v2d, mvalo, &x, &y);
		click = ((wsize - y) / (CHANNELHEIGHT+CHANNELSKIP));
		
		if ( ((int) click) < clickmin) {
			clickmax = clickmin;
			clickmin = (int) click;
		}
		else {
			clickmax = (int) click;
		}
	}

	if (clickmax < 0) {
		return;
	}

	for (chan = act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			if (clickmax < 0) break;

			if ( clickmin <= 0) {
				/* Select the channel with the given mode. If the
				 * channel is freshly selected then set it to the
				 * active channel for the action
				 */
				select_ipo_bezier_keys(chan->ipo, selectmode);
			}
			--clickmin;
			--clickmax;

			/* Check for click in a constraint */
			for (conchan=chan->constraintChannels.first; 
				 conchan; conchan=conchan->next){
				if (clickmax < 0) break;
				if ( clickmin <= 0) {
					select_ipo_bezier_keys(chan->ipo, selectmode);
				}
				--clickmin;
				--clickmax;
			}
		}
	}
  
	allqueue (REDRAWIPO, 0);
	allqueue (REDRAWVIEW3D, 0);
	allqueue (REDRAWACTION, 0);
	allqueue (REDRAWNLA, 0);
  
}

static void borderselect_function(void (*select_func)(bAction *act, 
                                                     short *mval, 
                                                     short *mvalo, 
                                                     int selectmode)) {
	/* This function executes an arbitrary selection
	 * function as part of a border select. This
	 * way the same function that is used for
	 * right click selection points can generally
	 * be used as the argument to this function
	 */
	rcti rect;
	short	mval[2], mvalo[2];
	bAction	*act;
	int val;		

	/* Get the selected action, exit if none are selected 
	 */
	act=G.saction->action;
	if (!act)
		return;

	/* Let the user draw a border (or abort)
	 */
	if ( (val=get_border (&rect, 3)) ) {
		mval[0]= rect.xmin;
		mval[1]= rect.ymin+2;
		mvalo[0]= rect.xmax;
		mvalo[1]= rect.ymax-2;

		/* if the left mouse was used, do an additive
		 * selection with the user defined selection
		 * function.
		 */
		if (val == LEFTMOUSE)
			select_func(act, mval, mvalo, SELECT_ADD);
		
		/* if the right mouse was used, do a subtractive
		 * selection with the user defined selection
		 * function.
		 */
		else if (val == RIGHTMOUSE)
			select_func(act, mval, mvalo, SELECT_SUBTRACT);
	}
	BIF_undo_push("Border select Action");
	
}

static void clever_keyblock_names(Key *key, short* mval){
    int        but=0, i, keynum;
    char       str[64];
	float      x;
	KeyBlock   *kb;
	/* get the keynum cooresponding to the y value
	 * of the mouse pointer, return if this is
	 * an invalid key number (and we don't deal
	 * with the speed ipo).
	 */

    keynum = get_nearest_key_num(key, mval, &x);
    if ( (keynum < 1) || (keynum >= key->totkey) )
        return;

	kb= key->block.first;
	for (i=0; i<keynum; ++i) kb = kb->next; 

	if (kb->name[0] == '\0') {
		sprintf(str, "Key %d", keynum);
	}
	else {
		strcpy(str, kb->name);
	}

	if ( (kb->slidermin >= kb->slidermax) ) {
		kb->slidermin = 0.0;
		kb->slidermax = 1.0;
	}

    add_numbut(but++, TEX, "KB: ", 0, 24, str, 
               "Does this really need a tool tip?");
	add_numbut(but++, NUM|FLO, "Slider Min:", 
			   -10000, kb->slidermax, &kb->slidermin, 0);
	add_numbut(but++, NUM|FLO, "Slider Max:", 
			   kb->slidermin, 10000, &kb->slidermax, 0);

    if (do_clever_numbuts(str, but, REDRAW)) {
		strcpy(kb->name, str);
        allqueue (REDRAWACTION, 0);
		allspace(REMAKEIPO, 0);
        allqueue (REDRAWIPO, 0);
	}

	
}

static void numbuts_action(void)
{
	/* now called from action window event loop, plus reacts on mouseclick */
	/* removed Hos grunts for that reason! :) (ton) */
    Key *key;
    short mval[2];

    if ( (key = get_action_mesh_key()) ) {
        getmouseco_areawin (mval);
		if (mval[0]<NAMEWIDTH) {
			clever_keyblock_names(key, mval);
		}
    }
}

void winqreadactionspace(ScrArea *sa, void *spacedata, BWinEvent *evt)
{
	extern void do_actionbuts(unsigned short event); // drawaction.c
	SpaceAction *saction;
	bAction	*act;
	Key *key;
	float dx,dy;
	int doredraw= 0;
	int	cfra;
	short	mval[2];
	unsigned short event= evt->event;
	short val= evt->val;
	short mousebut = L_MOUSE;

	if(curarea->win==0) return;

	saction= curarea->spacedata.first;
	if (!saction)
		return;

	act=saction->action;
	if(val) {
		
		if( uiDoBlocks(&curarea->uiblocks, event)!=UI_NOTHING ) event= 0;
		
		/* swap mouse buttons based on user preference */
		if (U.flag & USER_LMOUSESELECT) {
			if (event == LEFTMOUSE) {
				event = RIGHTMOUSE;
				mousebut = L_MOUSE;
			} else if (event == RIGHTMOUSE) {
				event = LEFTMOUSE;
				mousebut = R_MOUSE;
			}
		}
		
		getmouseco_areawin(mval);

		key = get_action_mesh_key();

		switch(event) {
		case UI_BUT_EVENT:
			do_actionbuts(val); 	// window itself
			break;
		
		case HOMEKEY:
			do_action_buttons(B_ACTHOME);	// header
			break;

		case AKEY:
			if (key) {
				if (mval[0]<ACTWIDTH){
					/* to do ??? */
				}
				else{
					deselect_meshchannel_keys(key, 1);
					allqueue (REDRAWACTION, 0);
					allqueue(REDRAWNLA, 0);
					allqueue (REDRAWIPO, 0);
				}
			}
			else {
				if (mval[0]<NAMEWIDTH){
					deselect_actionchannels (act, 1);
					allqueue (REDRAWVIEW3D, 0);
					allqueue (REDRAWACTION, 0);
					allqueue(REDRAWNLA, 0);
					allqueue (REDRAWIPO, 0);
				}
				else if (mval[0]>ACTWIDTH){
					deselect_actionchannel_keys (act, 1);
					allqueue (REDRAWACTION, 0);
					allqueue(REDRAWNLA, 0);
					allqueue (REDRAWIPO, 0);
				}
			}
			break;

		case BKEY:
			if (key) {
				if (mval[0]<ACTWIDTH){
					/* to do?? */
				}
				else {
					borderselect_mesh(key);
				}
			}
			else {

				/* If the border select is initiated in the
				 * part of the action window where the channel
				 * names reside, then select the channels
				 */
				if (mval[0]<NAMEWIDTH){
					borderselect_function(mouse_actionchannels);
					BIF_undo_push("Select Action");
				}
				else if (mval[0]>ACTWIDTH){

					/* If the border select is initiated in the
					 * vertical scrollbar, then (de)select all keys
					 * for the channels in the selection region
					 */
					if (IN_2D_VERT_SCROLL(mval)) {
						borderselect_function(select_all_keys_channels);
					}

					/* If the border select is initiated in the
					 * horizontal scrollbar, then (de)select all keys
					 * for the keyframes in the selection region
					 */
					else if (IN_2D_HORIZ_SCROLL(mval)) {
						borderselect_function(select_all_keys_frames);
					}

					/* Other wise, select the action keys
					 */
					else {
						borderselect_action();
					}
				}
			}
			break;

		case CKEY:
			/* scroll the window so the current
			 * frame is in the center.
			 */
			center_currframe();
			break;

		case DKEY:
			if (key) {
				if (G.qual & LR_SHIFTKEY && mval[0]>ACTWIDTH) {
					duplicate_meshchannel_keys(key);
				}
			}
			else if (act) {
				if (G.qual & LR_SHIFTKEY && mval[0]>ACTWIDTH){
					duplicate_actionchannel_keys();
					remake_action_ipos(act);
				}
			}
			break;

		case GKEY:
			if (mval[0]>=ACTWIDTH) {
				if (key) {
					transform_meshchannel_keys('g', key);
				}
				else if (act) {
					transform_actionchannel_keys ('g', 0);
				}
			}
			break;

		case HKEY:
			if(G.qual & LR_SHIFTKEY) {
				if(okee("Set Keys to Auto Handle")) {
					if (key)
						sethandles_meshchannel_keys(HD_AUTO, key);
					else
						sethandles_actionchannel_keys(HD_AUTO);
				}
			}
			else {
				if(okee("Toggle Keys Aligned Handle")) {
					if (key)
						sethandles_meshchannel_keys(HD_ALIGN, key);
					else
						sethandles_actionchannel_keys(HD_ALIGN);
				}
			}
			break;
			
		case KKEY:
			if(key)
				column_select_shapekeys(key);
			else if(act)
				column_select_actionkeys(act);
			
			allqueue(REDRAWIPO, 0);
			allqueue(REDRAWVIEW3D, 0);
			allqueue(REDRAWACTION, 0);
			allqueue(REDRAWNLA, 0);
			break;
			
		case NKEY:
			if(G.qual==0) {
				numbuts_action();
				
				/* no panel (yet). current numbuts are not easy to put in panel... */
				//add_blockhandler(curarea, ACTION_HANDLER_PROPERTIES, UI_PNL_TO_MOUSE);
				//scrarea_queue_winredraw(curarea);
			}
			break;
			
		case SKEY: 
			if (mval[0]>=ACTWIDTH) {
				if(G.qual & LR_SHIFTKEY) {
					snap_keys_to_frame();
				}
				else {
					if (key)
						transform_meshchannel_keys('s', key);
					else if (act)
						transform_actionchannel_keys ('s', 0);
				}
			}
			break;

			/*** set the Ipo type  ***/
		case TKEY:
			if (key) {
				/* to do */
			}
			else {
				if(G.qual & LR_SHIFTKEY)
					set_ipotype_actionchannels(SET_IPO_POPUP);
				else
					transform_actionchannel_keys ('t', 0);
			}
			break;

		case VKEY:
			if(okee("Set Keys to Vector Handle")) {
				if (key)
					sethandles_meshchannel_keys(HD_VECT, key);
				else
					sethandles_actionchannel_keys(HD_VECT);
			}
			break;

		case PAGEUPKEY:
			if (key) {
				/* to do */
			}
			else {
				if(G.qual & LR_SHIFTKEY) {
					top_sel_action();
				}
				else
				{
					up_sel_action();
				}
				
			}
			break;
		case PAGEDOWNKEY:
			if (key) {
				/* to do */
			}
			else {
				if(G.qual & LR_SHIFTKEY) {
					bottom_sel_action();
				}
				else
				down_sel_action();
				
			}
			break;
		case DELKEY:
		case XKEY:
			if (key) {
				delete_meshchannel_keys(key);
			}
			else {
				if (mval[0]<NAMEWIDTH)
					delete_actionchannels ();
				else
					delete_actionchannel_keys ();
			}
			break;
		/* LEFTMOUSE and RIGHTMOUSE event codes can be swapped above,
		 * based on user preference USER_LMOUSESELECT
		 */
		case LEFTMOUSE:
			if(view2dmove(LEFTMOUSE)) // only checks for sliders
				break;
			else if (mval[0]>ACTWIDTH){
				do {
					getmouseco_areawin(mval);
					
					areamouseco_to_ipoco(G.v2d, mval, &dx, &dy);
					
					cfra= (int)dx;
					if(cfra< 1) cfra= 1;
					
					if( cfra!=CFRA ) {
						CFRA= cfra;
						update_for_newframe();
						force_draw_all(0);					}
					else PIL_sleep_ms(30);
					
				} while(get_mbut() & mousebut);
				break;
			}
			/* passed on as selection */
		case RIGHTMOUSE:
			/* Clicking in the channel area selects the
			 * channel or constraint channel
			 */
			if (mval[0]<NAMEWIDTH) {
				if(act) {
					if(G.qual & LR_SHIFTKEY)
						mouse_actionchannels(act, mval, NULL,  SELECT_INVERT);
					else
						mouse_actionchannels(act, mval, NULL,  SELECT_REPLACE);
					
					BIF_undo_push("Select Action");
				}
				else numbuts_action();
			}
			else if (mval[0]>ACTWIDTH) {
		
				/* Clicking in the vertical scrollbar selects
				 * all of the keys for that channel at that height
				 */
				if (IN_2D_VERT_SCROLL(mval)) {
					if(G.qual & LR_SHIFTKEY)
						select_all_keys_channels(act, mval, NULL, 
												 SELECT_INVERT);
					else
						select_all_keys_channels(act, mval, NULL, 
												 SELECT_REPLACE);
				}
		
				/* Clicking in the horizontal scrollbar selects
				 * all of the keys within 0.5 of the nearest integer
				 * frame
				 */
				else if (IN_2D_HORIZ_SCROLL(mval)) {
					if(G.qual & LR_SHIFTKEY)
						select_all_keys_frames(act, mval, NULL, 
											   SELECT_INVERT);
					else
						select_all_keys_frames(act, mval, NULL, 
											   SELECT_REPLACE);
					BIF_undo_push("Select all Action");
				}
				
				/* Clicking in the main area of the action window
				 * selects keys
				 */
				else {
					if (key) {
						if(G.qual & LR_SHIFTKEY)
							mouse_mesh_action(SELECT_INVERT, key);
						else
							mouse_mesh_action(SELECT_REPLACE, key);
					}
					else {
						if(G.qual & LR_SHIFTKEY)
							mouse_action(SELECT_INVERT);
						else
							mouse_action(SELECT_REPLACE);
					}
				}
			}
			break;
		case PADPLUSKEY:
			view2d_zoom(G.v2d, 0.1154, sa->winx, sa->winy);
			test_view2d(G.v2d, sa->winx, sa->winy);
			view2d_do_locks(curarea, V2D_LOCK_COPY);

			doredraw= 1;
			break;
		case PADMINUS:
			view2d_zoom(G.v2d, -0.15, sa->winx, sa->winy);
			test_view2d(G.v2d, sa->winx, sa->winy);
			view2d_do_locks(curarea, V2D_LOCK_COPY);
			
			doredraw= 1;
			break;
		case MIDDLEMOUSE:
		case WHEELUPMOUSE:
		case WHEELDOWNMOUSE:
			view2dmove(event);	/* in drawipo.c */
			break;
		}
	}

	if(doredraw) addqueue(curarea->win, REDRAW, 1);
	
}

Key *get_action_mesh_key(void) 
{
	/* gets the key data from the currently selected
	 * mesh/lattice. If a mesh is not selected, or does not have
	 * key data, then we return NULL (currently only
	 * returns key data for RVK type meshes). If there
	 * is an action that is pinned, return null
	 */
    Object *ob;
    Key    *key;

    ob = OBACT;
    if (!ob) return NULL;

	if (G.saction->pin) return NULL;

    if (ob->type==OB_MESH ) {
		key = ((Mesh *)ob->data)->key;
    }
	else if (ob->type==OB_LATTICE ) {
		key = ((Lattice *)ob->data)->key;
	}
	else return NULL;

	if (key) {
		if (key->type == KEY_RELATIVE)
			return key;
	}

    return NULL;
}

int get_nearest_key_num(Key *key, short *mval, float *x) {
	/* returns the key num that cooresponds to the
	 * y value of the mouse click. Does not check
	 * if this is a valid keynum. Also gives the Ipo
	 * x coordinate.
	 */
    int num;
    float ybase, y;

    areamouseco_to_ipoco(G.v2d, mval, x, &y);

    ybase = key->totkey * (CHANNELHEIGHT + CHANNELSKIP);
    num = (int) ((ybase - y + CHANNELHEIGHT/2) / (CHANNELHEIGHT+CHANNELSKIP));

    return (num + 1);
}



void top_sel_action()
{
	bAction *act;
	bActionChannel *chan;
	
	/* Get the selected action, exit if none are selected */
	act = G.saction->action;
	if (!act) return;
	
	for (chan=act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			if ((chan->flag & ACHAN_SELECTED) && !(chan->flag & ACHAN_MOVED)){
				/* take it out off the chain keep data */
				BLI_remlink (&act->chanbase, chan);
				/* make it first element */
				BLI_insertlinkbefore(&act->chanbase,act->chanbase.first, chan);
				chan->flag |= ACHAN_MOVED;
				/* restart with rest of list */
				chan=chan->next;
			}
		}
	}
    /* clear temp flags */
	for (chan=act->chanbase.first; chan; chan=chan->next){
		chan->flag = chan->flag & ~ACHAN_MOVED;
	}
	
	/* Clean up and redraw stuff */
	remake_action_ipos (act);
	BIF_undo_push("Top Action channel");
	allspace(REMAKEIPO, 0);
	allqueue(REDRAWACTION, 0);
	allqueue(REDRAWIPO, 0);
	allqueue(REDRAWNLA, 0);
}

void up_sel_action()
{
	bAction *act;
	bActionChannel *chan;
	bActionChannel *prev;
	
	/* Get the selected action, exit if none are selected */
	act = G.saction->action;
	if (!act) return;
	
	for (chan=act->chanbase.first; chan; chan=chan->next){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			if ((chan->flag & ACHAN_SELECTED) && !(chan->flag & ACHAN_MOVED)){
				prev = chan->prev;
				if (prev){
					/* take it out off the chain keep data */
					BLI_remlink (&act->chanbase, chan);
					/* push it up */
					BLI_insertlinkbefore(&act->chanbase,prev, chan);
					chan->flag |= ACHAN_MOVED;
					/* restart with rest of list */
					chan=chan->next;
				}
			}
		}
	}
	/* clear temp flags */
	for (chan=act->chanbase.first; chan; chan=chan->next){
		chan->flag = chan->flag & ~ACHAN_MOVED;
	}
	
	/* Clean up and redraw stuff
	*/
	remake_action_ipos (act);
	BIF_undo_push("Up Action channel");
	allspace(REMAKEIPO, 0);
	allqueue(REDRAWACTION, 0);
	allqueue(REDRAWIPO, 0);
	allqueue(REDRAWNLA, 0);
}

void down_sel_action()
{
	bAction *act;
	bActionChannel *chan;
	bActionChannel *next;
	
	/* Get the selected action, exit if none are selected */
	act = G.saction->action;
	if (!act) return;
	
	for (chan=act->chanbase.last; chan; chan=chan->prev){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			if ((chan->flag & ACHAN_SELECTED) && !(chan->flag & ACHAN_MOVED)){
				next = chan->next;
				if (next) next = next->next;
				if (next){
					/* take it out off the chain keep data */
					BLI_remlink (&act->chanbase, chan);
					/* move it down */
					BLI_insertlinkbefore(&act->chanbase,next, chan);
					chan->flag |= ACHAN_MOVED;
				}
				else {
					/* take it out off the chain keep data */
					BLI_remlink (&act->chanbase, chan);
					/* add at end */
					BLI_addtail(&act->chanbase,chan);
					chan->flag |= ACHAN_MOVED;
				}
			}
		}
	}
	/* clear temp flags */
	for (chan=act->chanbase.first; chan; chan=chan->next){
		chan->flag = chan->flag & ~ACHAN_MOVED;
	}
	
	/* Clean up and redraw stuff
	*/
	remake_action_ipos (act);
	BIF_undo_push("Down Action channel");
	allspace(REMAKEIPO, 0);
	allqueue(REDRAWACTION, 0);
	allqueue(REDRAWIPO, 0);
	allqueue(REDRAWNLA, 0);
}

void bottom_sel_action()
{
	bAction *act;
	bActionChannel *chan;
	
	/* Get the selected action, exit if none are selected */
	act = G.saction->action;
	if (!act) return;
	
	for (chan=act->chanbase.last; chan; chan=chan->prev){
		if((chan->flag & ACHAN_HIDDEN)==0) {
			if ((chan->flag & ACHAN_SELECTED) && !(chan->flag & ACHAN_MOVED)) {
				/* take it out off the chain keep data */
				BLI_remlink (&act->chanbase, chan);
				/* add at end */
				BLI_addtail(&act->chanbase,chan);
				chan->flag |= ACHAN_MOVED;
			}
		}		
	}
	/* clear temp flags */
	for (chan=act->chanbase.first; chan; chan=chan->next){
		chan->flag = chan->flag & ~ACHAN_MOVED;
	}
	
	/* Clean up and redraw stuff
	*/
	remake_action_ipos (act);
	BIF_undo_push("Bottom Action channel");
	allspace(REMAKEIPO, 0);
	allqueue(REDRAWACTION, 0);
	allqueue(REDRAWIPO, 0);
	allqueue(REDRAWNLA, 0);
}

void world2bonespace(float boneSpaceMat[][4], float worldSpace[][4], float restPos[][4], float armPos[][4])
{
	float imatarm[4][4], imatbone[4][4], tmat[4][4], t2mat[4][4];
	
	Mat4Invert(imatarm, armPos);
	Mat4Invert(imatbone, restPos);
	Mat4MulMat4(tmat, imatarm, worldSpace);
	Mat4MulMat4(t2mat, tmat, imatbone);
	Mat4MulMat4(boneSpaceMat, restPos, t2mat);
}


bAction* bake_obIPO_to_action (Object *ob)
{
	bArmature		*arm;
	bAction			*result=NULL;
	bAction			*temp;
	Bone			*bone;
	ID				*id;
	ListBase		elems;
	int		        oldframe,testframe;
	char			newname[64];
	float			quat[4],tmat[4][4],startpos[4][4];
	CfraElem		*firstcfra, *lastcfra;
	
	arm = get_armature(ob);
	
	if (arm) {	
	
		oldframe = CFRA;
		result = add_empty_action(ID_PO);
		id = (ID *)ob;
		
		sprintf (newname, "TESTOBBAKE");
		rename_id(&result->id, newname);
		
		if(ob!=G.obedit) { // make sure object is not in edit mode
			if(ob->ipo) {
				/* convert the ipo to a list of 'current frame elements' */
				
				temp = ob->action;
				ob->action = result;
				
				elems.first= elems.last= NULL;
				make_cfra_list(ob->ipo, &elems);
				/* set the beginning armature location */
				firstcfra=elems.first;
				lastcfra=elems.last;
				CFRA=firstcfra->cfra;
				
				where_is_object(ob);
				Mat4CpyMat4(startpos,ob->obmat);
				
				/* loop from first key to last, sampling every 10 */
				for (testframe = firstcfra->cfra; testframe<=lastcfra->cfra; testframe=testframe+10) { 
					CFRA=testframe;
					where_is_object(ob);

					for (bone = arm->bonebase.first; bone; bone=bone->next) {
						if (!bone->parent) { /* this is a root bone, so give it a key! */
							world2bonespace(tmat,ob->obmat,bone->arm_mat,startpos);
							Mat4ToQuat(tmat,quat);
							printf("Frame: %i %f, %f, %f, %f\n",CFRA,quat[0],quat[1],quat[2],quat[3]);
							insertmatrixkey(id, ID_PO, bone->name, NULL, AC_LOC_X,tmat[3][0]);
							insertmatrixkey(id, ID_PO, bone->name, NULL, AC_LOC_Y,tmat[3][1]);
							insertmatrixkey(id, ID_PO, bone->name, NULL, AC_LOC_Z,tmat[3][2]);
							insertmatrixkey(id, ID_PO, bone->name, NULL, AC_QUAT_X,quat[1]);
							insertmatrixkey(id, ID_PO, bone->name, NULL, AC_QUAT_Y,quat[2]);
							insertmatrixkey(id, ID_PO, bone->name, NULL, AC_QUAT_Z,quat[3]);
							insertmatrixkey(id, ID_PO, bone->name, NULL, AC_QUAT_W,quat[0]);
							//insertmatrixkey(id, ID_PO, bone->name, NULL, AC_SIZE_X,size[0]);
							//insertmatrixkey(id, ID_PO, bone->name, NULL, AC_SIZE_Y,size[1]);
							//insertmatrixkey(id, ID_PO, bone->name, NULL, AC_SIZE_Z,size[2]);
						}
					}
				}
				BLI_freelistN(&elems);  
			}
		}
		CFRA = oldframe;
	}
	return result;	
}

bAction* bake_everything_to_action (Object *ob)
{
	bArmature		*arm;
	bAction			*result=NULL;
	bAction			*temp;
	Bone			*bone;
	ID				*id;
	ListBase		elems;
	int		        oldframe,testframe;
	char			newname[64];
	float			quat[4],tmat[4][4],startpos[4][4];
	CfraElem		*firstcfra, *lastcfra;
	
	arm = get_armature(ob);
	
	if (arm) {	
	
		oldframe = CFRA;
		result = add_empty_action(ID_PO);
		id = (ID *)ob;
		
		sprintf (newname, "TESTOBBAKE");
		rename_id(&result->id, newname);
		
		if(ob!=G.obedit) { // make sure object is not in edit mode
			if(ob->ipo) {
				/* convert the ipo to a list of 'current frame elements' */
				
				temp = ob->action;
				ob->action = result;
				
				elems.first= elems.last= NULL;
				make_cfra_list(ob->ipo, &elems);
				/* set the beginning armature location */
				firstcfra=elems.first;
				lastcfra=elems.last;
				CFRA=firstcfra->cfra;
				
				where_is_object(ob);
				Mat4CpyMat4(startpos,ob->obmat);
				
				/* loop from first key to last, sampling every 10 */
				for (testframe = firstcfra->cfra; testframe<=lastcfra->cfra; testframe=testframe+10) { 
					CFRA=testframe;
					
					do_all_pose_actions(ob);
					where_is_object(ob);
					for (bone = arm->bonebase.first; bone; bone=bone->next) {
						if (!bone->parent) { /* this is a root bone, so give it a key! */
							world2bonespace(tmat,ob->obmat,bone->arm_mat,startpos);
							
							Mat4ToQuat(tmat,quat);
							printf("Frame: %i %f, %f, %f, %f\n",CFRA,quat[0],quat[1],quat[2],quat[3]);
							insertmatrixkey(id, ID_PO, bone->name, NULL, AC_LOC_X,tmat[3][0]);
							insertmatrixkey(id, ID_PO, bone->name, NULL, AC_LOC_Y,tmat[3][1]);
							insertmatrixkey(id, ID_PO, bone->name, NULL, AC_LOC_Z,tmat[3][2]);
							insertmatrixkey(id, ID_PO, bone->name, NULL, AC_QUAT_X,quat[1]);
							insertmatrixkey(id, ID_PO, bone->name, NULL, AC_QUAT_Y,quat[2]);
							insertmatrixkey(id, ID_PO, bone->name, NULL, AC_QUAT_Z,quat[3]);
							insertmatrixkey(id, ID_PO, bone->name, NULL, AC_QUAT_W,quat[0]);
							//insertmatrixkey(id, ID_PO, bone->name, NULL, AC_SIZE_X,size[0]);
							//insertmatrixkey(id, ID_PO, bone->name, NULL, AC_SIZE_Y,size[1]);
							//insertmatrixkey(id, ID_PO, bone->name, NULL, AC_SIZE_Z,size[2]);
						}
					}
				}
				BLI_freelistN(&elems);  
			}
		}
		CFRA = oldframe;
	}
	return result;	
}
