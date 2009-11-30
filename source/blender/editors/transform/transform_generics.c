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
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "BLO_sys_types.h" // for intptr_t support

#include "DNA_anim_types.h"
#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_constraint_types.h"
#include "DNA_curve_types.h"
#include "DNA_lattice_types.h"
#include "DNA_mesh_types.h"
#include "DNA_modifier_types.h"
#include "DNA_nla_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_object_force.h"
#include "DNA_particle_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view3d_types.h"
#include "DNA_windowmanager_types.h"

#include "RNA_access.h"

//#include "BIF_screen.h"
//#include "BIF_mywindow.h"
#include "BIF_gl.h"
#include "BIF_glutil.h"
//#include "BIF_editmesh.h"
//#include "BIF_editsima.h"
//#include "BIF_editparticle.h"
//#include "BIF_meshtools.h"

#include "BKE_animsys.h"
#include "BKE_action.h"
#include "BKE_anim.h"
#include "BKE_armature.h"
#include "BKE_cloth.h"
#include "BKE_curve.h"
#include "BKE_depsgraph.h"
#include "BKE_displist.h"
#include "BKE_depsgraph.h"
#include "BKE_fcurve.h"
#include "BKE_global.h"
#include "BKE_group.h"
#include "BKE_lattice.h"
#include "BKE_key.h"
#include "BKE_mesh.h"
#include "BKE_modifier.h"
#include "BKE_nla.h"
#include "BKE_object.h"
#include "BKE_utildefines.h"
#include "BKE_context.h"

#include "ED_anim_api.h"
#include "ED_armature.h"
#include "ED_image.h"
#include "ED_keyframing.h"
#include "ED_markers.h"
#include "ED_mesh.h"
#include "ED_particle.h"
#include "ED_screen_types.h"
#include "ED_space_api.h"
#include "ED_uvedit.h"
#include "ED_view3d.h"

//#include "BDR_unwrapper.h"

#include "BLI_math.h"
#include "BLI_blenlib.h"
#include "BLI_editVert.h"
#include "BLI_rand.h"

#include "RNA_access.h"

#include "WM_types.h"

#include "UI_resources.h"

//#include "blendef.h"
//
//#include "mydevice.h"

#include "transform.h"

extern ListBase editelems;

/* ************************** Functions *************************** */

void getViewVector(TransInfo *t, float coord[3], float vec[3])
{
	if (t->persp != RV3D_ORTHO)
	{
		float p1[4], p2[4];
		
		VECCOPY(p1, coord);
		p1[3] = 1.0f;
		VECCOPY(p2, p1);
		p2[3] = 1.0f;
		mul_m4_v4(t->viewmat, p2);
		
		p2[0] = 2.0f * p2[0];
		p2[1] = 2.0f * p2[1];
		p2[2] = 2.0f * p2[2];
		
		mul_m4_v4(t->viewinv, p2);
		
		sub_v3_v3v3(vec, p1, p2);
	}
	else {
		VECCOPY(vec, t->viewinv[2]);
	}
	normalize_v3(vec);
}

/* ************************** GENERICS **************************** */

static void clipMirrorModifier(TransInfo *t, Object *ob)
{
	ModifierData *md= ob->modifiers.first;
	float tolerance[3] = {0.0f, 0.0f, 0.0f};
	int axis = 0;
	
	for (; md; md=md->next) {
		if (md->type==eModifierType_Mirror) {
			MirrorModifierData *mmd = (MirrorModifierData*) md;
			
			if(mmd->flag & MOD_MIR_CLIPPING) {
				axis = 0;
				if(mmd->flag & MOD_MIR_AXIS_X) {
					axis |= 1;
					tolerance[0] = mmd->tolerance;
				}
				if(mmd->flag & MOD_MIR_AXIS_Y) {
					axis |= 2;
					tolerance[1] = mmd->tolerance;
				}
				if(mmd->flag & MOD_MIR_AXIS_Z) {
					axis |= 4;
					tolerance[2] = mmd->tolerance;
				}
				if (axis) {
					float mtx[4][4], imtx[4][4];
					int i;
					TransData *td = t->data;
					
					if (mmd->mirror_ob) {
						float obinv[4][4];
						
						invert_m4_m4(obinv, mmd->mirror_ob->obmat);
						mul_m4_m4m4(mtx, ob->obmat, obinv);
						invert_m4_m4(imtx, mtx);
					}
					
					for(i = 0 ; i < t->total; i++, td++) {
						int clip;
						float loc[3], iloc[3];
						
						if (td->flag & TD_NOACTION)
							break;
						if (td->loc==NULL)
							break;
						
						if (td->flag & TD_SKIP)
							continue;
						
						copy_v3_v3(loc,  td->loc);
						copy_v3_v3(iloc, td->iloc);
						
						if (mmd->mirror_ob) {
							mul_v3_m4v3(loc, mtx, loc);
							mul_v3_m4v3(iloc, mtx, iloc);
						}
						
						clip = 0;
						if(axis & 1) {
							if(fabs(iloc[0])<=tolerance[0] ||
							   loc[0]*iloc[0]<0.0f) {
								loc[0]= 0.0f;
								clip = 1;
							}
						}
						
						if(axis & 2) {
							if(fabs(iloc[1])<=tolerance[1] ||
							   loc[1]*iloc[1]<0.0f) {
								loc[1]= 0.0f;
								clip = 1;
							}
						}
						if(axis & 4) {
							if(fabs(iloc[2])<=tolerance[2] ||
							   loc[2]*iloc[2]<0.0f) {
								loc[2]= 0.0f;
								clip = 1;
							}
						}
						if (clip) {
							if (mmd->mirror_ob) {
								mul_v3_m4v3(loc, imtx, loc);
							}
							copy_v3_v3(td->loc, loc);
						}
					}
				}
				
			}
		}
	}
}

/* assumes obedit set to mesh object */
static void editmesh_apply_to_mirror(TransInfo *t)
{
	TransData *td = t->data;
	EditVert *eve;
	int i;
	
	for(i = 0 ; i < t->total; i++, td++) {
		if (td->flag & TD_NOACTION)
			break;
		if (td->loc==NULL)
			break;
		if (td->flag & TD_SKIP)
			continue;
		
		eve = td->extra;
		if (eve) {
			eve->co[0]= -td->loc[0];
			eve->co[1]= td->loc[1];
			eve->co[2]= td->loc[2];
		}
		
		if (td->flag & TD_MIRROR_EDGE)
		{
			td->loc[0] = 0;
		}
	}
}

/* tags the given ID block for refreshes (if applicable) due to 
 * Animation Editor editing
 */
static void animedit_refresh_id_tags (Scene *scene, ID *id)
{
	if (id) {
		AnimData *adt= BKE_animdata_from_id(id);
		
		/* tag AnimData for refresh so that other views will update in realtime with these changes */
		if (adt)
			adt->recalc |= ADT_RECALC_ANIM;
			
		/* set recalc flags */
		DAG_id_flush_update(id, OB_RECALC); // XXX or do we want something more restrictive?
	}
}

/* for the realtime animation recording feature, handle overlapping data */
static void animrecord_check_state (Scene *scene, ID *id, wmTimer *animtimer)
{
	ScreenAnimData *sad= (animtimer) ? animtimer->customdata : NULL;
	
	/* sanity checks */
	if ELEM3(NULL, scene, id, sad)
		return;
	
	/* check if we need a new strip if:
	 * 	- if animtimer is running 
	 *	- we're not only keying for available channels
	 *	- the option to add new actions for each round is not enabled
	 */
	if (IS_AUTOKEY_FLAG(INSERTAVAIL)==0 && (scene->toolsettings->autokey_flag & ANIMRECORD_FLAG_WITHNLA)) {
		/* if playback has just looped around, we need to add a new NLA track+strip to allow a clean pass to occur */
		if ((sad) && (sad->flag & ANIMPLAY_FLAG_JUMPED)) {
			AnimData *adt= BKE_animdata_from_id(id);
			
			/* perform push-down manually with some differences 
			 * NOTE: BKE_nla_action_pushdown() sync warning...
			 */
			if ((adt->action) && !(adt->flag & ADT_NLA_EDIT_ON)) {
				float astart, aend;
				
				/* only push down if action is more than 1-2 frames long */
				calc_action_range(adt->action, &astart, &aend, 1);
				if (aend > astart+2.0f) {
					NlaStrip *strip= add_nlastrip_to_stack(adt, adt->action);
					
					/* clear reference to action now that we've pushed it onto the stack */
					adt->action->id.us--;
					adt->action= NULL;
					
					/* adjust blending + extend so that they will behave correctly */
					strip->extendmode= NLASTRIP_EXTEND_NOTHING;
					strip->flag &= ~(NLASTRIP_FLAG_AUTO_BLENDS|NLASTRIP_FLAG_SELECT|NLASTRIP_FLAG_ACTIVE);
					
					/* also, adjust the AnimData's action extend mode to be on 
					 * 'nothing' so that previous result still play 
					 */
					adt->act_extendmode= NLASTRIP_EXTEND_NOTHING;
				}
			}
		}
	}
}

/* called for updating while transform acts, once per redraw */
void recalcData(TransInfo *t)
{
	Scene *scene = t->scene;
	Base *base = scene->basact;

	if (t->spacetype==SPACE_NODE) {
		flushTransNodes(t);
	}
	else if (t->spacetype==SPACE_SEQ) {
		flushTransSeq(t);
	}
	else if (t->spacetype == SPACE_ACTION) {
		Scene *scene= t->scene;
		
		bAnimContext ac;
		ListBase anim_data = {NULL, NULL};
		bAnimListElem *ale;
		int filter;
		
		/* initialise relevant anim-context 'context' data from TransInfo data */
			/* NOTE: sync this with the code in ANIM_animdata_get_context() */
		memset(&ac, 0, sizeof(bAnimContext));
		
		ac.scene= t->scene;
		ac.obact= OBACT;
		ac.sa= t->sa;
		ac.ar= t->ar;
		ac.spacetype= (t->sa)? t->sa->spacetype : 0;
		ac.regiontype= (t->ar)? t->ar->regiontype : 0;
		
		ANIM_animdata_context_getdata(&ac);
		
		/* get animdata blocks visible in editor, assuming that these will be the ones where things changed */
		filter= (ANIMFILTER_VISIBLE | ANIMFILTER_ANIMDATA);
		ANIM_animdata_filter(&ac, &anim_data, filter, ac.data, ac.datatype);
		
		/* just tag these animdata-blocks to recalc, assuming that some data there changed */
		for (ale= anim_data.first; ale; ale= ale->next) {
			/* set refresh tags for objects using this animation */
			animedit_refresh_id_tags(t->scene, ale->id);
		}
		
		/* now free temp channels */
		BLI_freelistN(&anim_data);
	}
	else if (t->spacetype == SPACE_IPO) {
		Scene *scene;
		
		ListBase anim_data = {NULL, NULL};
		bAnimContext ac;
		int filter;
		
		bAnimListElem *ale;
		int dosort = 0;
		
		
		/* initialise relevant anim-context 'context' data from TransInfo data */
			/* NOTE: sync this with the code in ANIM_animdata_get_context() */
		memset(&ac, 0, sizeof(bAnimContext));
		
		scene= ac.scene= t->scene;
		ac.obact= OBACT;
		ac.sa= t->sa;
		ac.ar= t->ar;
		ac.spacetype= (t->sa)? t->sa->spacetype : 0;
		ac.regiontype= (t->ar)? t->ar->regiontype : 0;
		
		ANIM_animdata_context_getdata(&ac);
		
		/* do the flush first */
		flushTransGraphData(t);
		
		/* get curves to check if a re-sort is needed */
		filter= (ANIMFILTER_VISIBLE | ANIMFILTER_FOREDIT | ANIMFILTER_CURVESONLY | ANIMFILTER_CURVEVISIBLE);
		ANIM_animdata_filter(&ac, &anim_data, filter, ac.data, ac.datatype);
		
		/* now test if there is a need to re-sort */
		for (ale= anim_data.first; ale; ale= ale->next) {
			FCurve *fcu= (FCurve *)ale->key_data;
			
			/* watch it: if the time is wrong: do not correct handles yet */
			if (test_time_fcurve(fcu))
				dosort++;
			else
				calchandles_fcurve(fcu);
				
			/* set refresh tags for objects using this animation */
			animedit_refresh_id_tags(t->scene, ale->id);
		}
		
		/* do resort and other updates? */
		if (dosort) remake_graph_transdata(t, &anim_data);
		
		/* now free temp channels */
		BLI_freelistN(&anim_data);
	}
	else if (t->spacetype == SPACE_NLA) {
		TransDataNla *tdn= (TransDataNla *)t->customData;
		SpaceNla *snla= (SpaceNla *)t->sa->spacedata.first;
		Scene *scene= t->scene;
		double secf= FPS;
		int i;
		
		/* for each strip we've got, perform some additional validation of the values that got set before
		 * using RNA to set the value (which does some special operations when setting these values to make
		 * sure that everything works ok)
		 */
		for (i = 0; i < t->total; i++, tdn++) {
			NlaStrip *strip= tdn->strip;
			PointerRNA strip_ptr;
			short pExceeded, nExceeded, iter;
			int delta_y1, delta_y2;
			
			/* if this tdn has no handles, that means it is just a dummy that should be skipped */
			if (tdn->handle == 0)
				continue;
			
			/* set refresh tags for objects using this animation */
			animedit_refresh_id_tags(t->scene, tdn->id);
			
			/* if cancelling transform, just write the values without validating, then move on */
			if (t->state == TRANS_CANCEL) {
				/* clear the values by directly overwriting the originals, but also need to restore
				 * endpoints of neighboring transition-strips
				 */
				
				/* start */
				strip->start= tdn->h1[0];
				
				if ((strip->prev) && (strip->prev->type == NLASTRIP_TYPE_TRANSITION))
					strip->prev->end= tdn->h1[0];
				
				/* end */
				strip->end= tdn->h2[0];
				
				if ((strip->next) && (strip->next->type == NLASTRIP_TYPE_TRANSITION))
					strip->next->start= tdn->h2[0];
				
				/* flush transforms to child strips (since this should be a meta) */
				BKE_nlameta_flush_transforms(strip);
				
				/* restore to original track (if needed) */
				if (tdn->oldTrack != tdn->nlt) {
					/* just append to end of list for now, since strips get sorted in special_aftertrans_update() */
					BLI_remlink(&tdn->nlt->strips, strip);
					BLI_addtail(&tdn->oldTrack->strips, strip);
				}
				
				continue;
			}
			
			/* firstly, check if the proposed transform locations would overlap with any neighbouring strips
			 * (barring transitions) which are absolute barriers since they are not being moved
			 *
			 * this is done as a iterative procedure (done 5 times max for now)
			 */
			for (iter=0; iter < 5; iter++) {
				pExceeded= ((strip->prev) && (strip->prev->type != NLASTRIP_TYPE_TRANSITION) && (tdn->h1[0] < strip->prev->end));
				nExceeded= ((strip->next) && (strip->next->type != NLASTRIP_TYPE_TRANSITION) && (tdn->h2[0] > strip->next->start));
				
				if ((pExceeded && nExceeded) || (iter == 4) ) {
					/* both endpoints exceeded (or iteration ping-pong'd meaning that we need a compromise)
					 *	- simply crop strip to fit within the bounds of the strips bounding it
					 *	- if there were no neighbours, clear the transforms (make it default to the strip's current values)
					 */
					if (strip->prev && strip->next) {
						tdn->h1[0]= strip->prev->end;
						tdn->h2[0]= strip->next->start;
					}
					else {
						tdn->h1[0]= strip->start;
						tdn->h2[0]= strip->end;
					}
				}
				else if (nExceeded) {
					/* move backwards */
					float offset= tdn->h2[0] - strip->next->start;
					
					tdn->h1[0] -= offset;
					tdn->h2[0] -= offset;
				}
				else if (pExceeded) {
					/* more forwards */
					float offset= strip->prev->end - tdn->h1[0];
					
					tdn->h1[0] += offset;
					tdn->h2[0] += offset;
				}
				else /* all is fine and well */
					break;
			}
			
			/* handle auto-snapping */
			switch (snla->autosnap) {
				case SACTSNAP_FRAME: /* snap to nearest frame/time  */
					if (snla->flag & SNLA_DRAWTIME) {
						tdn->h1[0]= (float)( floor((tdn->h1[0]/secf) + 0.5f) * secf );
						tdn->h2[0]= (float)( floor((tdn->h2[0]/secf) + 0.5f) * secf );
					}
					else {
						tdn->h1[0]= (float)( floor(tdn->h1[0]+0.5f) );
						tdn->h2[0]= (float)( floor(tdn->h2[0]+0.5f) );
					}
					break;
				
				case SACTSNAP_MARKER: /* snap to nearest marker */
					tdn->h1[0]= (float)ED_markers_find_nearest_marker_time(&t->scene->markers, tdn->h1[0]);
					tdn->h2[0]= (float)ED_markers_find_nearest_marker_time(&t->scene->markers, tdn->h2[0]);
					break;
			}
			
			/* use RNA to write the values... */
			// TODO: do we need to write in 2 passes to make sure that no truncation goes on?
			RNA_pointer_create(NULL, &RNA_NlaStrip, strip, &strip_ptr);
			
			RNA_float_set(&strip_ptr, "start_frame", tdn->h1[0]);
			RNA_float_set(&strip_ptr, "end_frame", tdn->h2[0]);
			
			/* flush transforms to child strips (since this should be a meta) */
			BKE_nlameta_flush_transforms(strip);
			
			
			/* now, check if we need to try and move track
			 *	- we need to calculate both, as only one may have been altered by transform if only 1 handle moved
			 */
			delta_y1= ((int)tdn->h1[1] / NLACHANNEL_STEP - tdn->trackIndex);
			delta_y2= ((int)tdn->h2[1] / NLACHANNEL_STEP - tdn->trackIndex);
			
			if (delta_y1 || delta_y2) {
				NlaTrack *track;
				int delta = (delta_y2) ? delta_y2 : delta_y1;
				int n;
				
				/* move in the requested direction, checking at each layer if there's space for strip to pass through,
				 * stopping on the last track available or that we're able to fit in
				 */
				if (delta > 0) {
					for (track=tdn->nlt->next, n=0; (track) && (n < delta); track=track->next, n++) {
						/* check if space in this track for the strip */
						if (BKE_nlatrack_has_space(track, strip->start, strip->end)) {
							/* move strip to this track */
							BLI_remlink(&tdn->nlt->strips, strip);
							BKE_nlatrack_add_strip(track, strip);
							
							tdn->nlt= track;
							tdn->trackIndex += (n + 1); /* + 1, since n==0 would mean that we didn't change track */
						}
						else /* can't move any further */
							break;
					}
				}
				else {
					/* make delta 'positive' before using it, since we now know to go backwards */
					delta= -delta;
					
					for (track=tdn->nlt->prev, n=0; (track) && (n < delta); track=track->prev, n++) {
						/* check if space in this track for the strip */
						if (BKE_nlatrack_has_space(track, strip->start, strip->end)) {
							/* move strip to this track */
							BLI_remlink(&tdn->nlt->strips, strip);
							BKE_nlatrack_add_strip(track, strip);
							
							tdn->nlt= track;
							tdn->trackIndex -= (n - 1); /* - 1, since n==0 would mean that we didn't change track */
						}
						else /* can't move any further */
							break;
					}
				}
			}
		}
	}
	else if (t->spacetype == SPACE_IMAGE) {
		if (t->obedit && t->obedit->type == OB_MESH) {
			SpaceImage *sima= t->sa->spacedata.first;
			
			flushTransUVs(t);
			if(sima->flag & SI_LIVE_UNWRAP)
				ED_uvedit_live_unwrap_re_solve();
			
			DAG_id_flush_update(t->obedit->data, OB_RECALC_DATA);
		}
	}
	else if (t->spacetype == SPACE_VIEW3D) {
		
		/* project */
		if(t->state != TRANS_CANCEL) {
			applyProject(t);
		}
		
		if (t->obedit) {
			if ELEM(t->obedit->type, OB_CURVE, OB_SURF) {
				Curve *cu= t->obedit->data;
				Nurb *nu= cu->editnurb->first;
				
				DAG_id_flush_update(t->obedit->data, OB_RECALC_DATA);  /* sets recalc flags */
				
				if (t->state == TRANS_CANCEL) {
					while(nu) {
						calchandlesNurb(nu); /* Cant do testhandlesNurb here, it messes up the h1 and h2 flags */
						nu= nu->next;
					}
				} else {
					/* Normal updating */
					while(nu) {
						test2DNurb(nu);
						calchandlesNurb(nu);
						nu= nu->next;
					}
				}
			}
			else if(t->obedit->type==OB_LATTICE) {
				Lattice *la= t->obedit->data;
				DAG_id_flush_update(t->obedit->data, OB_RECALC_DATA);  /* sets recalc flags */
	
				if(la->editlatt->flag & LT_OUTSIDE) outside_lattice(la->editlatt);
			}
			else if (t->obedit->type == OB_MESH) {
				EditMesh *em = ((Mesh*)t->obedit->data)->edit_mesh;
				/* mirror modifier clipping? */
				if(t->state != TRANS_CANCEL) {
					clipMirrorModifier(t, t->obedit);
				}
				if((t->options & CTX_NO_MIRROR) == 0 && (t->flag & T_MIRROR))
					editmesh_apply_to_mirror(t);
					
				DAG_id_flush_update(t->obedit->data, OB_RECALC_DATA);  /* sets recalc flags */
				
				recalc_editnormals(em);
			}
			else if(t->obedit->type==OB_ARMATURE) { /* no recalc flag, does pose */
				bArmature *arm= t->obedit->data;
				ListBase *edbo = arm->edbo;
				EditBone *ebo;
				TransData *td = t->data;
				int i;
				
				/* Ensure all bones are correctly adjusted */
				for (ebo = edbo->first; ebo; ebo = ebo->next){
					
					if ((ebo->flag & BONE_CONNECTED) && ebo->parent){
						/* If this bone has a parent tip that has been moved */
						if (ebo->parent->flag & BONE_TIPSEL){
							VECCOPY (ebo->head, ebo->parent->tail);
							if(t->mode==TFM_BONE_ENVELOPE) ebo->rad_head= ebo->parent->rad_tail;
						}
						/* If this bone has a parent tip that has NOT been moved */
						else{
							VECCOPY (ebo->parent->tail, ebo->head);
							if(t->mode==TFM_BONE_ENVELOPE) ebo->parent->rad_tail= ebo->rad_head;
						}
					}
					
					/* on extrude bones, oldlength==0.0f, so we scale radius of points */
					ebo->length= len_v3v3(ebo->head, ebo->tail);
					if(ebo->oldlength==0.0f) {
						ebo->rad_head= 0.25f*ebo->length;
						ebo->rad_tail= 0.10f*ebo->length;
						ebo->dist= 0.25f*ebo->length;
						if(ebo->parent) {
							if(ebo->rad_head > ebo->parent->rad_tail)
								ebo->rad_head= ebo->parent->rad_tail;
						}
					}
					else if(t->mode!=TFM_BONE_ENVELOPE) {
						/* if bones change length, lets do that for the deform distance as well */
						ebo->dist*= ebo->length/ebo->oldlength;
						ebo->rad_head*= ebo->length/ebo->oldlength;
						ebo->rad_tail*= ebo->length/ebo->oldlength;
						ebo->oldlength= ebo->length;
					}
				}
				
				
				if (t->mode != TFM_BONE_ROLL)
				{
					/* fix roll */
					for(i = 0; i < t->total; i++, td++)
					{
						if (td->extra)
						{
							float vec[3], up_axis[3];
							float qrot[4];
							
							ebo = td->extra;
							VECCOPY(up_axis, td->axismtx[2]);
							
							if (t->mode != TFM_ROTATION)
							{
								sub_v3_v3v3(vec, ebo->tail, ebo->head);
								normalize_v3(vec);
								rotation_between_vecs_to_quat(qrot, td->axismtx[1], vec);
								mul_qt_v3(qrot, up_axis);
							}
							else
							{
								mul_m3_v3(t->mat, up_axis);
							}
							
							ebo->roll = ED_rollBoneToVector(ebo, up_axis);
						}
					}
				}
				
				if(arm->flag & ARM_MIRROR_EDIT)
					transform_armature_mirror_update(t->obedit);
				
			}
			else
				DAG_id_flush_update(t->obedit->data, OB_RECALC_DATA);  /* sets recalc flags */
		}
		else if( (t->flag & T_POSE) && t->poseobj) {
			Object *ob= t->poseobj;
			bArmature *arm= ob->data;
			
			/* if animtimer is running, and the object already has animation data,
			 * check if the auto-record feature means that we should record 'samples'
			 * (i.e. uneditable animation values)
			 */
			// TODO: autokeyframe calls need some setting to specify to add samples (FPoints) instead of keyframes?
			if ((t->animtimer) && IS_AUTOKEY_ON(t->scene)) {
				int targetless_ik= (t->flag & T_AUTOIK); // XXX this currently doesn't work, since flags aren't set yet!
				
				animrecord_check_state(t->scene, &ob->id, t->animtimer);
				autokeyframe_pose_cb_func(t->scene, (View3D *)t->view, ob, t->mode, targetless_ik);
			}
			
			/* old optimize trick... this enforces to bypass the depgraph */
			if (!(arm->flag & ARM_DELAYDEFORM)) {
				DAG_id_flush_update(&ob->id, OB_RECALC_DATA);  /* sets recalc flags */
			}
			else
				where_is_pose(scene, ob);
		}
		else if(base && (base->object->mode & OB_MODE_PARTICLE_EDIT) && PE_get_current(scene, base->object)) {
			flushTransParticles(t);
		}
		else {
			int i;
			
			for(base= FIRSTBASE; base; base= base->next) {
				Object *ob= base->object;
				
				/* this flag is from depgraph, was stored in initialize phase, handled in drawview.c */
				if(base->flag & BA_HAS_RECALC_OB)
					ob->recalc |= OB_RECALC_OB;
				if(base->flag & BA_HAS_RECALC_DATA)
					ob->recalc |= OB_RECALC_DATA;
			}
			
			for (i = 0; i < t->total; i++) {
				TransData *td = t->data + i;
				Object *ob = td->ob;
				
				if (td->flag & TD_NOACTION)
					break;
				
				if (td->flag & TD_SKIP)
					continue;
				
				/* if animtimer is running, and the object already has animation data,
				 * check if the auto-record feature means that we should record 'samples'
				 * (i.e. uneditable animation values)
				 */
				// TODO: autokeyframe calls need some setting to specify to add samples (FPoints) instead of keyframes?
				if ((t->animtimer) && IS_AUTOKEY_ON(t->scene)) {
					animrecord_check_state(t->scene, &ob->id, t->animtimer);
					autokeyframe_ob_cb_func(t->scene, (View3D *)t->view, ob, t->mode);
				}
				
				/* proxy exception */
				if(ob->proxy)
					ob->proxy->recalc |= ob->recalc;
				if(ob->proxy_group)
					group_tag_recalc(ob->proxy_group->dup_group);
			}
		}
		
		if(((View3D*)t->view)->drawtype == OB_SHADED)
			reshadeall_displist(t->scene);
	}
}

void drawLine(TransInfo *t, float *center, float *dir, char axis, short options)
{
	float v1[3], v2[3], v3[3];
	char col[3], col2[3];

	if (t->spacetype == SPACE_VIEW3D)
	{
		View3D *v3d = t->view;
		
		glPushMatrix();
		
		//if(t->obedit) glLoadMatrixf(t->obedit->obmat);	// sets opengl viewing
		
		
		copy_v3_v3(v3, dir);
		mul_v3_fl(v3, v3d->far);
		
		sub_v3_v3v3(v2, center, v3);
		add_v3_v3v3(v1, center, v3);
		
		if (options & DRAWLIGHT) {
			col[0] = col[1] = col[2] = 220;
		}
		else {
			UI_GetThemeColor3ubv(TH_GRID, col);
		}
		UI_make_axis_color(col, col2, axis);
		glColor3ubv((GLubyte *)col2);
		
		setlinestyle(0);
		glBegin(GL_LINE_STRIP);
			glVertex3fv(v1);
			glVertex3fv(v2);
		glEnd();
		
		glPopMatrix();
	}
}

void resetTransRestrictions(TransInfo *t)
{
	t->flag &= ~T_ALL_RESTRICTIONS;
}

int initTransInfo (bContext *C, TransInfo *t, wmOperator *op, wmEvent *event)
{
	Scene *sce = CTX_data_scene(C);
	ToolSettings *ts = CTX_data_tool_settings(C);
	ARegion *ar = CTX_wm_region(C);
	ScrArea *sa = CTX_wm_area(C);
	Object *obedit = CTX_data_edit_object(C);
	
	/* moving: is shown in drawobject() (transform color) */
//  TRANSFORM_FIX_ME
//	if(obedit || (t->flag & T_POSE) ) G.moving= G_TRANSFORM_EDIT;
//	else if(G.f & G_PARTICLEEDIT) G.moving= G_TRANSFORM_PARTICLE;
//	else G.moving= G_TRANSFORM_OBJ;
	
	t->scene = sce;
	t->sa = sa;
	t->ar = ar;
	t->obedit = obedit;
	t->settings = ts;
	
	t->data = NULL;
	t->ext = NULL;
	
	t->helpline = HLP_NONE;
	
	t->flag = 0;
	
	t->redraw = 1; /* redraw first time */
	
	if (event)
	{
		t->imval[0] = event->x - t->ar->winrct.xmin;
		t->imval[1] = event->y - t->ar->winrct.ymin;
		
		t->event_type = event->type;
	}
	else
	{
		t->imval[0] = 0;
		t->imval[1] = 0;
	}
	
	t->con.imval[0] = t->imval[0];
	t->con.imval[1] = t->imval[1];
	
	t->mval[0] = t->imval[0];
	t->mval[1] = t->imval[1];
	
	t->transform		= NULL;
	t->handleEvent		= NULL;
	
	t->total			= 0;
	
	t->val = 0.0f;
	
	t->vec[0]			=
		t->vec[1]		=
		t->vec[2]		= 0.0f;
	
	t->center[0]		=
		t->center[1]	=
		t->center[2]	= 0.0f;
	
	unit_m3(t->mat);
	
	/* if there's an event, we're modal */
	if (event) {
		t->flag |= T_MODAL;
	}

	t->spacetype = sa->spacetype;
	if(t->spacetype == SPACE_VIEW3D)
	{
		View3D *v3d = sa->spacedata.first;
		
		t->view = v3d;
		t->animtimer= CTX_wm_screen(C)->animtimer;
		
		if(v3d->flag & V3D_ALIGN) t->flag |= T_V3D_ALIGN;
		t->around = v3d->around;
		
		if (op && RNA_struct_find_property(op->ptr, "constraint_orientation") && RNA_property_is_set(op->ptr, "constraint_orientation"))
		{
			t->current_orientation = RNA_enum_get(op->ptr, "constraint_orientation");
			
			if (t->current_orientation >= V3D_MANIP_CUSTOM + BIF_countTransformOrientation(C) - 1)
			{
				t->current_orientation = V3D_MANIP_GLOBAL;
			}
		}
		else
		{
			t->current_orientation = v3d->twmode;
		}
	}
	else if(t->spacetype==SPACE_IMAGE || t->spacetype==SPACE_NODE)
	{
		SpaceImage *sima = sa->spacedata.first;
		// XXX for now, get View2D  from the active region
		t->view = &ar->v2d;
		t->around = sima->around;
	}
	else if(t->spacetype==SPACE_IPO) 
	{
		SpaceIpo *sipo= sa->spacedata.first;
		t->view = &ar->v2d;
		t->around = sipo->around;
	}
	else
	{
		// XXX for now, get View2D  from the active region
		t->view = &ar->v2d;
		// XXX for now, the center point is the midpoint of the data
		t->around = V3D_CENTER;
	}
	
	if (op && RNA_struct_find_property(op->ptr, "mirror") && RNA_property_is_set(op->ptr, "mirror"))
	{
		if (RNA_boolean_get(op->ptr, "mirror"))
		{
			t->flag |= T_MIRROR;
			t->mirror = 1;
		}
	}
	// Need stuff to take it from edit mesh or whatnot here
	else
	{
		if (t->obedit && t->obedit->type == OB_MESH && (((Mesh *)t->obedit->data)->editflag & ME_EDIT_MIRROR_X))
		{
			t->flag |= T_MIRROR;
			t->mirror = 1;
		}
	}
	
	/* setting PET flag only if property exist in operator. Otherwise, assume it's not supported */
	if (op && RNA_struct_find_property(op->ptr, "proportional"))
	{
		if (RNA_property_is_set(op->ptr, "proportional"))
		{
			switch(RNA_enum_get(op->ptr, "proportional"))
			{
			case 2: /* XXX connected constant */
				t->flag |= T_PROP_CONNECTED;
			case 1: /* XXX prop on constant */
				t->flag |= T_PROP_EDIT;
				break;
			}
		}
		else
		{
			/* use settings from scene only if modal */
			if (t->flag & T_MODAL)
			{
				if ((t->options & CTX_NO_PET) == 0 && (ts->proportional != PROP_EDIT_OFF)) {
					t->flag |= T_PROP_EDIT;

					if(ts->proportional == PROP_EDIT_CONNECTED)
						t->flag |= T_PROP_CONNECTED;
				}
			}
		}
		
		if (op && RNA_struct_find_property(op->ptr, "proportional_size") && RNA_property_is_set(op->ptr, "proportional_size"))
		{
			t->prop_size = RNA_float_get(op->ptr, "proportional_size");
		}
		else
		{
			t->prop_size = ts->proportional_size;
		}
		
		
		/* TRANSFORM_FIX_ME rna restrictions */
		if (t->prop_size <= 0)
		{
			t->prop_size = 1.0f;
		}
		
		if (op && RNA_struct_find_property(op->ptr, "proportional_editing_falloff") && RNA_property_is_set(op->ptr, "proportional_editing_falloff"))
		{
			t->prop_mode = RNA_enum_get(op->ptr, "proportional_editing_falloff");
		}
		else
		{
			t->prop_mode = ts->prop_mode;
		}
	}
	else /* add not pet option to context when not available */
	{
		t->options |= CTX_NO_PET;
	}
	
	setTransformViewMatrices(t);
	initNumInput(&t->num);
	initNDofInput(&t->ndof);
	
	return 1;
}

/* Here I would suggest only TransInfo related issues, like free data & reset vars. Not redraws */
void postTrans (TransInfo *t)
{
	TransData *td;
	
	if (t->draw_handle_view)
		ED_region_draw_cb_exit(t->ar->type, t->draw_handle_view);
	if (t->draw_handle_pixel)
		ED_region_draw_cb_exit(t->ar->type, t->draw_handle_pixel);
	

	if (t->customFree) {
		/* Can take over freeing t->data and data2d etc... */
		t->customFree(t);
	}
	else if (t->customData) {
		MEM_freeN(t->customData);
	}

	/* postTrans can be called when nothing is selected, so data is NULL already */
	if (t->data) {
		int a;
		
		/* since ipokeys are optional on objects, we mallocced them per trans-data */
		for(a=0, td= t->data; a<t->total; a++, td++) {
			if (td->flag & TD_BEZTRIPLE) 
				MEM_freeN(td->hdata);
		}
		MEM_freeN(t->data);
	}
	
	if (t->ext) MEM_freeN(t->ext);
	if (t->data2d) {
		MEM_freeN(t->data2d);
		t->data2d= NULL;
	}
	
	if(t->spacetype==SPACE_IMAGE) {
		SpaceImage *sima= t->sa->spacedata.first;
		if(sima->flag & SI_LIVE_UNWRAP)
			ED_uvedit_live_unwrap_end(t->state == TRANS_CANCEL);
	}
	
	if (t->mouse.data)
	{
		MEM_freeN(t->mouse.data);
	}
}

void applyTransObjects(TransInfo *t)
{
	TransData *td;
	
	for (td = t->data; td < t->data + t->total; td++) {
		VECCOPY(td->iloc, td->loc);
		if (td->ext->rot) {
			VECCOPY(td->ext->irot, td->ext->rot);
		}
		if (td->ext->size) {
			VECCOPY(td->ext->isize, td->ext->size);
		}
	}
	recalcData(t);
}

static void restoreElement(TransData *td) {
	/* TransData for crease has no loc */
	if (td->loc) {
		VECCOPY(td->loc, td->iloc);
	}
	if (td->val) {
		*td->val = td->ival;
	}
	if (td->ext && (td->flag&TD_NO_EXT)==0) {
		if (td->ext->rot) {
			VECCOPY(td->ext->rot, td->ext->irot);
		}
		if (td->ext->size) {
			VECCOPY(td->ext->size, td->ext->isize);
		}
		if (td->ext->quat) {
			QUATCOPY(td->ext->quat, td->ext->iquat);
		}
	}
	
	if (td->flag & TD_BEZTRIPLE) {
		*(td->hdata->h1) = td->hdata->ih1;
		*(td->hdata->h2) = td->hdata->ih2;
	}
}

void restoreTransObjects(TransInfo *t)
{
	TransData *td;
	
	for (td = t->data; td < t->data + t->total; td++) {
		restoreElement(td);
	}
	
	unit_m3(t->mat);
	
	recalcData(t);
}

void calculateCenter2D(TransInfo *t)
{
	if (t->flag & (T_EDIT|T_POSE)) {
		Object *ob= t->obedit?t->obedit:t->poseobj;
		float vec[3];
		
		VECCOPY(vec, t->center);
		mul_m4_v3(ob->obmat, vec);
		projectIntView(t, vec, t->center2d);
	}
	else {
		projectIntView(t, t->center, t->center2d);
	}
}

void calculateCenterCursor(TransInfo *t)
{
	float *cursor;
	
	cursor = give_cursor(t->scene, t->view);
	VECCOPY(t->center, cursor);
	
	/* If edit or pose mode, move cursor in local space */
	if (t->flag & (T_EDIT|T_POSE)) {
		Object *ob = t->obedit?t->obedit:t->poseobj;
		float mat[3][3], imat[3][3];
		
		sub_v3_v3v3(t->center, t->center, ob->obmat[3]);
		copy_m3_m4(mat, ob->obmat);
		invert_m3_m3(imat, mat);
		mul_m3_v3(imat, t->center);
	}
	
	calculateCenter2D(t);
}

void calculateCenterCursor2D(TransInfo *t)
{
	View2D *v2d= t->view;
	float aspx=1.0, aspy=1.0;
	
	if(t->spacetype==SPACE_IMAGE) /* only space supported right now but may change */
		ED_space_image_uv_aspect(t->sa->spacedata.first, &aspx, &aspy);
	
	if (v2d) {
		t->center[0] = v2d->cursor[0] * aspx;
		t->center[1] = v2d->cursor[1] * aspy;
	}
	
	calculateCenter2D(t);
}

void calculateCenterCursorGraph2D(TransInfo *t)
{
	SpaceIpo *sipo= (SpaceIpo *)t->sa->spacedata.first;
	Scene *scene= t->scene;
	
	/* cursor is combination of current frame, and graph-editor cursor value */
	t->center[0]= (float)(scene->r.cfra);
	t->center[1]= sipo->cursorVal;
	
	calculateCenter2D(t);
}

void calculateCenterMedian(TransInfo *t)
{
	float partial[3] = {0.0f, 0.0f, 0.0f};
	int total = 0;
	int i;
	
	for(i = 0; i < t->total; i++) {
		if (t->data[i].flag & TD_SELECTED) {
			if (!(t->data[i].flag & TD_NOCENTER))
			{
				add_v3_v3v3(partial, partial, t->data[i].center);
				total++;
			}
		}
		else {
			/*
			   All the selected elements are at the head of the array
			   which means we can stop when it finds unselected data
			*/
			break;
		}
	}
	if(i)
		mul_v3_fl(partial, 1.0f / total);
	VECCOPY(t->center, partial);
	
	calculateCenter2D(t);
}

void calculateCenterBound(TransInfo *t)
{
	float max[3];
	float min[3];
	int i;
	for(i = 0; i < t->total; i++) {
		if (i) {
			if (t->data[i].flag & TD_SELECTED) {
				if (!(t->data[i].flag & TD_NOCENTER))
					minmax_v3_v3v3(min, max, t->data[i].center);
			}
			else {
				/*
				   All the selected elements are at the head of the array
				   which means we can stop when it finds unselected data
				*/
				break;
			}
		}
		else {
			VECCOPY(max, t->data[i].center);
			VECCOPY(min, t->data[i].center);
		}
	}
	add_v3_v3v3(t->center, min, max);
	mul_v3_fl(t->center, 0.5);
	
	calculateCenter2D(t);
}

void calculateCenter(TransInfo *t)
{
	switch(t->around) {
	case V3D_CENTER:
		calculateCenterBound(t);
		break;
	case V3D_CENTROID:
		calculateCenterMedian(t);
		break;
	case V3D_CURSOR:
		if(t->spacetype==SPACE_IMAGE)
			calculateCenterCursor2D(t);
		else if(t->spacetype==SPACE_IPO)
			calculateCenterCursorGraph2D(t);
		else
			calculateCenterCursor(t);
		break;
	case V3D_LOCAL:
		/* Individual element center uses median center for helpline and such */
		calculateCenterMedian(t);
		break;
	case V3D_ACTIVE:
		{
		/* set median, and if if if... do object center */
		
		/* EDIT MODE ACTIVE EDITMODE ELEMENT */

		if (t->obedit && t->obedit->type == OB_MESH) {
			EditSelection ese;
			EditMesh *em = BKE_mesh_get_editmesh(t->obedit->data);
			
			if (EM_get_actSelection(em, &ese)) {
				EM_editselection_center(t->center, &ese);
				calculateCenter2D(t);
				break;
			}
		} /* END EDIT MODE ACTIVE ELEMENT */
		
		calculateCenterMedian(t);
		if((t->flag & (T_EDIT|T_POSE))==0)
		{
			Scene *scene = t->scene;
			Object *ob= OBACT;
			if(ob)
			{
				VECCOPY(t->center, ob->obmat[3]);
				projectIntView(t, t->center, t->center2d);
			}
		}
		
		}
	}
	
	/* setting constraint center */
	VECCOPY(t->con.center, t->center);
	if(t->flag & (T_EDIT|T_POSE))
	{
		Object *ob= t->obedit?t->obedit:t->poseobj;
		mul_m4_v3(ob->obmat, t->con.center);
	}
	
	/* for panning from cameraview */
	if(t->flag & T_OBJECT)
	{
		if(t->spacetype==SPACE_VIEW3D && t->ar->regiontype == RGN_TYPE_WINDOW)
		{
			View3D *v3d = t->view;
			Scene *scene = t->scene;
			RegionView3D *rv3d = t->ar->regiondata;
			
			if(v3d->camera == OBACT && rv3d->persp==RV3D_CAMOB)
			{
				float axis[3];
				/* persinv is nasty, use viewinv instead, always right */
				VECCOPY(axis, t->viewinv[2]);
				normalize_v3(axis);
				
				/* 6.0 = 6 grid units */
				axis[0]= t->center[0]- 6.0f*axis[0];
				axis[1]= t->center[1]- 6.0f*axis[1];
				axis[2]= t->center[2]- 6.0f*axis[2];
				
				projectIntView(t, axis, t->center2d);
				
				/* rotate only needs correct 2d center, grab needs initgrabz() value */
				if(t->mode==TFM_TRANSLATION)
				{
					VECCOPY(t->center, axis);
					VECCOPY(t->con.center, t->center);
				}
			}
		}
	}
	
	if(t->spacetype==SPACE_VIEW3D)
	{
		/* initgrabz() defines a factor for perspective depth correction, used in window_to_3d_delta() */
		if(t->flag & (T_EDIT|T_POSE)) {
			Object *ob= t->obedit?t->obedit:t->poseobj;
			float vec[3];
			
			VECCOPY(vec, t->center);
			mul_m4_v3(ob->obmat, vec);
			initgrabz(t->ar->regiondata, vec[0], vec[1], vec[2]);
		}
		else {
			initgrabz(t->ar->regiondata, t->center[0], t->center[1], t->center[2]);
		}
	}
}

void calculatePropRatio(TransInfo *t)
{
	TransData *td = t->data;
	int i;
	float dist;
	short connected = t->flag & T_PROP_CONNECTED;

	if (t->flag & T_PROP_EDIT) {
		for(i = 0 ; i < t->total; i++, td++) {
			if (td->flag & TD_SELECTED) {
				td->factor = 1.0f;
			}
			else if (t->flag & T_MIRROR && td->loc[0] * t->mirror < -0.00001f)
			{
				td->flag |= TD_SKIP;
				td->factor = 0.0f;
				restoreElement(td);
			}
			else if	((connected &&
						(td->flag & TD_NOTCONNECTED || td->dist > t->prop_size))
				||
					(connected == 0 &&
						td->rdist > t->prop_size)) {
				/*
				   The elements are sorted according to their dist member in the array,
				   that means we can stop when it finds one element outside of the propsize.
				*/
				td->flag |= TD_NOACTION;
				td->factor = 0.0f;
				restoreElement(td);
			}
			else {
				/* Use rdist for falloff calculations, it is the real distance */
				td->flag &= ~TD_NOACTION;
				dist= (t->prop_size-td->rdist)/t->prop_size;
				
				/*
				 * Clamp to positive numbers.
				 * Certain corner cases with connectivity and individual centers
				 * can give values of rdist larger than propsize.
				 */
				if (dist < 0.0f)
					dist = 0.0f;
				
				switch(t->prop_mode) {
				case PROP_SHARP:
					td->factor= dist*dist;
					break;
				case PROP_SMOOTH:
					td->factor= 3.0f*dist*dist - 2.0f*dist*dist*dist;
					break;
				case PROP_ROOT:
					td->factor = (float)sqrt(dist);
					break;
				case PROP_LIN:
					td->factor = dist;
					break;
				case PROP_CONST:
					td->factor = 1.0f;
					break;
				case PROP_SPHERE:
					td->factor = (float)sqrt(2*dist - dist * dist);
					break;
				case PROP_RANDOM:
					BLI_srand( BLI_rand() ); /* random seed */
					td->factor = BLI_frand()*dist;
					break;
				default:
					td->factor = 1;
				}
			}
		}
		switch(t->prop_mode) {
		case PROP_SHARP:
			strcpy(t->proptext, "(Sharp)");
			break;
		case PROP_SMOOTH:
			strcpy(t->proptext, "(Smooth)");
			break;
		case PROP_ROOT:
			strcpy(t->proptext, "(Root)");
			break;
		case PROP_LIN:
			strcpy(t->proptext, "(Linear)");
			break;
		case PROP_CONST:
			strcpy(t->proptext, "(Constant)");
			break;
		case PROP_SPHERE:
			strcpy(t->proptext, "(Sphere)");
			break;
		case PROP_RANDOM:
			strcpy(t->proptext, "(Random)");
			break;
		default:
			strcpy(t->proptext, "");
		}
	}
	else {
		for(i = 0 ; i < t->total; i++, td++) {
			td->factor = 1.0;
		}
		strcpy(t->proptext, "");
	}
}

float get_drawsize(ARegion *ar, float *co)
{
	RegionView3D *rv3d= ar->regiondata;
	float size, vec[3], len1, len2;
	
	/* size calculus, depending ortho/persp settings, like initgrabz() */
	size= rv3d->persmat[0][3]*co[0]+ rv3d->persmat[1][3]*co[1]+ rv3d->persmat[2][3]*co[2]+ rv3d->persmat[3][3];
	
	VECCOPY(vec, rv3d->persinv[0]);
	len1= normalize_v3(vec);
	VECCOPY(vec, rv3d->persinv[1]);
	len2= normalize_v3(vec);
	
	size*= 0.01f*(len1>len2?len1:len2);
	
	/* correct for window size to make widgets appear fixed size */
	if(ar->winx > ar->winy) size*= 1000.0f/(float)ar->winx;
	else size*= 1000.0f/(float)ar->winy;
	
	return size;
}
