/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2008 Blender Foundation, Joshua Leung
 * All rights reserved.
 *
 * 
 * Contributor(s): Joshua Leung (original author)
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/animation/anim_filter.c
 *  \ingroup edanimation
 */


/* This file contains a system used to provide a layer of abstraction between sources
 * of animation data and tools in Animation Editors. The method used here involves 
 * generating a list of edit structures which enable tools to naively perform the actions 
 * they require without all the boiler-plate associated with loops within loops and checking 
 * for cases to ignore. 
 *
 * While this is primarily used for the Action/Dopesheet Editor (and its accessory modes),
 * the Graph Editor also uses this for its channel list and for determining which curves
 * are being edited. Likewise, the NLA Editor also uses this for its channel list and in
 * its operators.
 *
 * Note: much of the original system this was based on was built before the creation of the RNA
 * system. In future, it would be interesting to replace some parts of this code with RNA queries,
 * however, RNA does not eliminate some of the boiler-plate reduction benefits presented by this 
 * system, so if any such work does occur, it should only be used for the internals used here...
 *
 * -- Joshua Leung, Dec 2008 (Last revision July 2009)
 */

#include <string.h>

#include "DNA_anim_types.h"
#include "DNA_armature_types.h"
#include "DNA_camera_types.h"
#include "DNA_lamp_types.h"
#include "DNA_lattice_types.h"
#include "DNA_key_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meta_types.h"
#include "DNA_node_types.h"
#include "DNA_particle_types.h"
#include "DNA_space_types.h"
#include "DNA_sequence_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_world_types.h"
#include "DNA_gpencil_types.h"
#include "DNA_object_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_utildefines.h"
#include "BLI_ghash.h"

#include "BKE_animsys.h"
#include "BKE_action.h"
#include "BKE_fcurve.h"
#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_group.h"
#include "BKE_key.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_node.h"
#include "BKE_sequencer.h"
#include "BKE_utildefines.h"

#include "ED_anim_api.h"
#include "ED_markers.h"

/* ************************************************************ */
/* Blender Context <-> Animation Context mapping */

/* ----------- Private Stuff - Action Editor ------------- */

/* Get shapekey data being edited (for Action Editor -> ShapeKey mode) */
/* Note: there's a similar function in key.c (ob_get_key) */
static Key *actedit_get_shapekeys (bAnimContext *ac) 
{
	Scene *scene= ac->scene;
	Object *ob;
	Key *key;
	
	ob = OBACT;
	if (ob == NULL) 
		return NULL;
	
	/* XXX pinning is not available in 'ShapeKey' mode... */
	//if (saction->pin) return NULL;
	
	/* shapekey data is stored with geometry data */
	key= ob_get_key(ob);
	
	if (key) {
		if (key->type == KEY_RELATIVE)
			return key;
	}
	
	return NULL;
}

/* Get data being edited in Action Editor (depending on current 'mode') */
static short actedit_get_context (bAnimContext *ac, SpaceAction *saction)
{
	/* sync settings with current view status, then return appropriate data */
	switch (saction->mode) {
		case SACTCONT_ACTION: /* 'Action Editor' */
			/* if not pinned, sync with active object */
			if (/*saction->pin == 0*/1) {
				if (ac->obact && ac->obact->adt)
					saction->action = ac->obact->adt->action;
				else
					saction->action= NULL;
			}
			
			ac->datatype= ANIMCONT_ACTION;
			ac->data= saction->action;
			
			ac->mode= saction->mode;
			return 1;
			
		case SACTCONT_SHAPEKEY: /* 'ShapeKey Editor' */
			ac->datatype= ANIMCONT_SHAPEKEY;
			ac->data= actedit_get_shapekeys(ac);
			
			ac->mode= saction->mode;
			return 1;
			
		case SACTCONT_GPENCIL: /* Grease Pencil */ // XXX review how this mode is handled...
			/* update scene-pointer (no need to check for pinning yet, as not implemented) */
			saction->ads.source= (ID *)ac->scene;
			
			ac->datatype= ANIMCONT_GPENCIL;
			ac->data= &saction->ads;
			
			ac->mode= saction->mode;
			return 1;
			
		case SACTCONT_DOPESHEET: /* DopeSheet */
			/* update scene-pointer (no need to check for pinning yet, as not implemented) */
			saction->ads.source= (ID *)ac->scene;
			
			ac->datatype= ANIMCONT_DOPESHEET;
			ac->data= &saction->ads;
			
			ac->mode= saction->mode;
			return 1;
		
		default: /* unhandled yet */
			ac->datatype= ANIMCONT_NONE;
			ac->data= NULL;
			
			ac->mode= -1;
			return 0;
	}
}

/* ----------- Private Stuff - Graph Editor ------------- */

/* Get data being edited in Graph Editor (depending on current 'mode') */
static short graphedit_get_context (bAnimContext *ac, SpaceIpo *sipo)
{
	/* init dopesheet data if non-existant (i.e. for old files) */
	if (sipo->ads == NULL) {
		sipo->ads= MEM_callocN(sizeof(bDopeSheet), "GraphEdit DopeSheet");
		sipo->ads->source= (ID *)ac->scene;
	}
	
	/* set settings for Graph Editor - "Selected = Editable" */
	if (sipo->flag & SIPO_SELCUVERTSONLY)
		sipo->ads->filterflag |= ADS_FILTER_SELEDIT;
	else
		sipo->ads->filterflag &= ~ADS_FILTER_SELEDIT;
	
	/* sync settings with current view status, then return appropriate data */
	switch (sipo->mode) {
		case SIPO_MODE_ANIMATION:	/* Animation F-Curve Editor */
			/* update scene-pointer (no need to check for pinning yet, as not implemented) */
			sipo->ads->source= (ID *)ac->scene;
			sipo->ads->filterflag &= ~ADS_FILTER_ONLYDRIVERS;
			
			ac->datatype= ANIMCONT_FCURVES;
			ac->data= sipo->ads;
			
			ac->mode= sipo->mode;
			return 1;
		
		case SIPO_MODE_DRIVERS:		/* Driver F-Curve Editor */
			/* update scene-pointer (no need to check for pinning yet, as not implemented) */
			sipo->ads->source= (ID *)ac->scene;
			sipo->ads->filterflag |= ADS_FILTER_ONLYDRIVERS;
			
			ac->datatype= ANIMCONT_DRIVERS;
			ac->data= sipo->ads;
			
			ac->mode= sipo->mode;
			return 1;
		
		default: /* unhandled yet */
			ac->datatype= ANIMCONT_NONE;
			ac->data= NULL;
			
			ac->mode= -1;
			return 0;
	}
}

/* ----------- Private Stuff - NLA Editor ------------- */

/* Get data being edited in Graph Editor (depending on current 'mode') */
static short nlaedit_get_context (bAnimContext *ac, SpaceNla *snla)
{
	/* init dopesheet data if non-existant (i.e. for old files) */
	if (snla->ads == NULL)
		snla->ads= MEM_callocN(sizeof(bDopeSheet), "NlaEdit DopeSheet");
	
	/* sync settings with current view status, then return appropriate data */
	/* update scene-pointer (no need to check for pinning yet, as not implemented) */
	snla->ads->source= (ID *)ac->scene;
	snla->ads->filterflag |= ADS_FILTER_ONLYNLA;
	
	ac->datatype= ANIMCONT_NLA;
	ac->data= snla->ads;
	
	return 1;
}

/* ----------- Public API --------------- */

/* Obtain current anim-data context, given that context info from Blender context has already been set 
 *	- AnimContext to write to is provided as pointer to var on stack so that we don't have
 *	  allocation/freeing costs (which are not that avoidable with channels).
 */
short ANIM_animdata_context_getdata (bAnimContext *ac)
{
	ScrArea *sa= ac->sa;
	short ok= 0;
	
	/* context depends on editor we are currently in */
	if (sa) {
		switch (sa->spacetype) {
			case SPACE_ACTION:
			{
				SpaceAction *saction= (SpaceAction *)sa->spacedata.first;
				ok= actedit_get_context(ac, saction);
			}
				break;
				
			case SPACE_IPO:
			{
				SpaceIpo *sipo= (SpaceIpo *)sa->spacedata.first;
				ok= graphedit_get_context(ac, sipo);
			}
				break;
				
			case SPACE_NLA:
			{
				SpaceNla *snla= (SpaceNla *)sa->spacedata.first;
				ok= nlaedit_get_context(ac, snla);
			}
				break;
		}
	}
	
	/* check if there's any valid data */
	if (ok && ac->data)
		return 1;
	else
		return 0;
}

/* Obtain current anim-data context from Blender Context info 
 *	- AnimContext to write to is provided as pointer to var on stack so that we don't have
 *	  allocation/freeing costs (which are not that avoidable with channels).
 *	- Clears data and sets the information from Blender Context which is useful
 */
short ANIM_animdata_get_context (const bContext *C, bAnimContext *ac)
{
	ScrArea *sa= CTX_wm_area(C);
	ARegion *ar= CTX_wm_region(C);
	Scene *scene= CTX_data_scene(C);
	
	/* clear old context info */
	if (ac == NULL) return 0;
	memset(ac, 0, sizeof(bAnimContext));
	
	/* get useful default context settings from context */
	ac->scene= scene;
	if (scene) {
		ac->markers= ED_context_get_markers(C);		
		ac->obact= (scene->basact)?  scene->basact->object : NULL;
	}
	ac->sa= sa;
	ac->ar= ar;
	ac->spacetype= (sa) ? sa->spacetype : 0;
	ac->regiontype= (ar) ? ar->regiontype : 0;
	
	/* get data context info */
	return ANIM_animdata_context_getdata(ac);
}

/* ************************************************************ */
/* Blender Data <-- Filter --> Channels to be operated on */

/* quick macro to test if AnimData is usable */
#define ANIMDATA_HAS_KEYS(id) ((id)->adt && (id)->adt->action)

/* quick macro to test if AnimData is usable for drivers */
#define ANIMDATA_HAS_DRIVERS(id) ((id)->adt && (id)->adt->drivers.first)

/* quick macro to test if AnimData is usable for NLA */
#define ANIMDATA_HAS_NLA(id) ((id)->adt && (id)->adt->nla_tracks.first)


/* Quick macro to test for all three avove usability tests, performing the appropriate provided 
 * action for each when the AnimData context is appropriate. 
 *
 * Priority order for this goes (most important, to least): AnimData blocks, NLA, Drivers, Keyframes.
 *
 * For this to work correctly, a standard set of data needs to be available within the scope that this
 * gets called in: 
 *	- ListBase anim_data;
 *	- bDopeSheet *ads;
 *	- bAnimListElem *ale;
 * 	- int items;
 *
 * 	- id: ID block which should have an AnimData pointer following it immediately, to use
 *	- adtOk: line or block of code to execute for AnimData-blocks case (usually ANIMDATA_ADD_ANIMDATA)
 *	- nlaOk: line or block of code to execute for NLA tracks+strips case
 *	- driversOk: line or block of code to execute for Drivers case
 *	- keysOk: line or block of code for Keyframes case
 *
 * The checks for the various cases are as follows:
 *	0) top level: checks for animdata and also that all the F-Curves for the block will be visible
 *	1) animdata check: for filtering animdata blocks only
 *	2A) nla tracks: include animdata block's data as there are NLA tracks+strips there
 *	2B) actions to convert to nla: include animdata block's data as there is an action that can be 
 *		converted to a new NLA strip, and the filtering options allow this
 *	3) drivers: include drivers from animdata block (for Drivers mode in Graph Editor)
 *	4) normal keyframes: only when there is an active action
 */
#define ANIMDATA_FILTER_CASES(id, adtOk, nlaOk, driversOk, keysOk) \
	{\
		if ((id)->adt) {\
			if (!(filter_mode & ANIMFILTER_CURVEVISIBLE) || !((id)->adt->flag & ADT_CURVES_NOT_VISIBLE)) {\
				if (filter_mode & ANIMFILTER_ANIMDATA) {\
					adtOk\
				}\
				else if (ads->filterflag & ADS_FILTER_ONLYNLA) {\
					if (ANIMDATA_HAS_NLA(id)) {\
						nlaOk\
					}\
					else if (!(ads->filterflag & ADS_FILTER_NLA_NOACT) && ANIMDATA_HAS_KEYS(id)) {\
						nlaOk\
					}\
				}\
				else if (ads->filterflag & ADS_FILTER_ONLYDRIVERS) {\
					if (ANIMDATA_HAS_DRIVERS(id)) {\
						driversOk\
					}\
				}\
				else {\
					if (ANIMDATA_HAS_KEYS(id)) {\
						keysOk\
					}\
				}\
			}\
		}\
	}


/* quick macro to add a pointer to an AnimData block as a channel */
#define ANIMDATA_ADD_ANIMDATA(id) \
	{\
		ale= make_new_animlistelem((id)->adt, ANIMTYPE_ANIMDATA, NULL, ANIMTYPE_NONE, (ID *)id);\
		if (ale) {\
			BLI_addtail(anim_data, ale);\
			items++;\
		}\
	}
	
/* quick macro to test if an anim-channel representing an AnimData block is suitably active */
#define ANIMCHANNEL_ACTIVEOK(ale) \
	( !(filter_mode & ANIMFILTER_ACTIVE) || !(ale->adt) || (ale->adt->flag & ADT_UI_ACTIVE) )

/* quick macro to test if an anim-channel (F-Curve, Group, etc.) is selected in an acceptable way */
#define ANIMCHANNEL_SELOK(test_func) \
		( !(filter_mode & (ANIMFILTER_SEL|ANIMFILTER_UNSEL)) || \
		  ((filter_mode & ANIMFILTER_SEL) && test_func) || \
		  ((filter_mode & ANIMFILTER_UNSEL) && test_func==0) ) 
		  
/* quick macro to test if an anim-channel (F-Curve) is selected ok for editing purposes 
 *	- _SELEDIT means that only selected curves will have visible+editable keyframes
 *
 * checks here work as follows:
 *	1) seledit off - don't need to consider the implications of this option
 *	2) foredit off - we're not considering editing, so channel is ok still
 *	3) test_func (i.e. selection test) - only if selected, this test will pass
 */
#define ANIMCHANNEL_SELEDITOK(test_func) \
		( !(filter_mode & ANIMFILTER_SELEDIT) || \
		  !(filter_mode & ANIMFILTER_FOREDIT) || \
		  (test_func) )

/* ----------- 'Private' Stuff --------------- */

/* this function allocates memory for a new bAnimListElem struct for the 
 * provided animation channel-data. 
 */
static bAnimListElem *make_new_animlistelem (void *data, short datatype, void *owner, short ownertype, ID *owner_id)
{
	bAnimListElem *ale= NULL;
	
	/* only allocate memory if there is data to convert */
	if (data) {
		/* allocate and set generic data */
		ale= MEM_callocN(sizeof(bAnimListElem), "bAnimListElem");
		
		ale->data= data;
		ale->type= datatype;
			// XXX what is the point of the owner data?
			// xxx try and use this to simplify the problem of finding whether parent channels are working...
		ale->owner= owner;
		ale->ownertype= ownertype;
		
		ale->id= owner_id;
		ale->adt= BKE_animdata_from_id(owner_id);
		
		/* do specifics */
		switch (datatype) {
			case ANIMTYPE_SUMMARY:
			{
				/* nothing to include for now... this is just a dummy wrappy around all the other channels 
				 * in the DopeSheet, and gets included at the start of the list
				 */
				ale->key_data= NULL;
				ale->datatype= ALE_ALL;
			}
				break;
			
			case ANIMTYPE_SCENE:
			{
				Scene *sce= (Scene *)data;
				
				ale->flag= sce->flag;
				
				ale->key_data= sce;
				ale->datatype= ALE_SCE;
				
				ale->adt= BKE_animdata_from_id(data);
			}
				break;
			case ANIMTYPE_OBJECT:
			{
				Base *base= (Base *)data;
				Object *ob= base->object;
				
				ale->flag= ob->flag;
				
				ale->key_data= ob;
				ale->datatype= ALE_OB;
				
				ale->adt= BKE_animdata_from_id(&ob->id);
			}
				break;
			case ANIMTYPE_FILLACTD:
			{
				bAction *act= (bAction *)data;
				
				ale->flag= act->flag;
				
				ale->key_data= act;
				ale->datatype= ALE_ACT;
			}
				break;
			case ANIMTYPE_FILLDRIVERS:
			{
				AnimData *adt= (AnimData *)data;
				
				ale->flag= adt->flag;
				
					// XXX... drivers don't show summary for now
				ale->key_data= NULL;
				ale->datatype= ALE_NONE;
			}
				break;
			case ANIMTYPE_FILLMATD:
			{
				Object *ob= (Object *)data;
				
				ale->flag= FILTER_MAT_OBJC(ob);
				
				ale->key_data= NULL;
				ale->datatype= ALE_NONE;
			}
				break;
			case ANIMTYPE_FILLPARTD:
			{
				Object *ob= (Object *)data;
				
				ale->flag= FILTER_PART_OBJC(ob);
				
				ale->key_data= NULL;
				ale->datatype= ALE_NONE;
			}
				break;
			case ANIMTYPE_FILLTEXD:
			{
				ID *id= (ID *)data;
				
				switch (GS(id->name)) {
					case ID_MA:
					{
						Material *ma= (Material *)id;
						ale->flag= FILTER_TEX_MATC(ma);
					}
						break;
					case ID_LA:
					{
						Lamp *la= (Lamp *)id;
						ale->flag= FILTER_TEX_LAMC(la);
					}
						break;
					case ID_WO:
					{
						World *wo= (World *)id;
						ale->flag= FILTER_TEX_WORC(wo);
					}
						break;
				}
				
				ale->key_data= NULL;
				ale->datatype= ALE_NONE;
			}
				break;
			
			case ANIMTYPE_DSMAT:
			{
				Material *ma= (Material *)data;
				AnimData *adt= ma->adt;
				
				ale->flag= FILTER_MAT_OBJD(ma);
				
				ale->key_data= (adt) ? adt->action : NULL;
				ale->datatype= ALE_ACT;
				
				ale->adt= BKE_animdata_from_id(data);
			}
				break;
			case ANIMTYPE_DSLAM:
			{
				Lamp *la= (Lamp *)data;
				AnimData *adt= la->adt;
				
				ale->flag= FILTER_LAM_OBJD(la);
				
				ale->key_data= (adt) ? adt->action : NULL;
				ale->datatype= ALE_ACT;
				
				ale->adt= BKE_animdata_from_id(data);
			}
				break;
			case ANIMTYPE_DSCAM:
			{
				Camera *ca= (Camera *)data;
				AnimData *adt= ca->adt;
				
				ale->flag= FILTER_CAM_OBJD(ca);
				
				ale->key_data= (adt) ? adt->action : NULL;
				ale->datatype= ALE_ACT;
				
				ale->adt= BKE_animdata_from_id(data);
			}
				break;
			case ANIMTYPE_DSCUR:
			{
				Curve *cu= (Curve *)data;
				AnimData *adt= cu->adt;
				
				ale->flag= FILTER_CUR_OBJD(cu);
				
				ale->key_data= (adt) ? adt->action : NULL;
				ale->datatype= ALE_ACT;
				
				ale->adt= BKE_animdata_from_id(data);
			}
				break;
			case ANIMTYPE_DSARM:
			{
				bArmature *arm= (bArmature *)data;
				AnimData *adt= arm->adt;
				
				ale->flag= FILTER_ARM_OBJD(arm);
				
				ale->key_data= (adt) ? adt->action : NULL;
				ale->datatype= ALE_ACT;
				
				ale->adt= BKE_animdata_from_id(data);
			}
				break;
			case ANIMTYPE_DSMESH:
			{
				Mesh *me= (Mesh *)data;
				AnimData *adt= me->adt;
				
				ale->flag= FILTER_MESH_OBJD(me);
				
				ale->key_data= (adt) ? adt->action : NULL;
				ale->datatype= ALE_ACT;
				
				ale->adt= BKE_animdata_from_id(data);
			}
				break;
			case ANIMTYPE_DSLAT:
			{
				Lattice *lt= (Lattice *)data;
				AnimData *adt= lt->adt;
				
				ale->flag= FILTER_LATTICE_OBJD(lt);
				
				ale->key_data= (adt) ? adt->action : NULL;
				ale->datatype= ALE_ACT;
				
				ale->adt= BKE_animdata_from_id(data);
			}	
				break;
			case ANIMTYPE_DSSKEY:
			{
				Key *key= (Key *)data;
				AnimData *adt= key->adt;
				
				ale->flag= FILTER_SKE_OBJD(key); 
				
				ale->key_data= (adt) ? adt->action : NULL;
				ale->datatype= ALE_ACT;
				
				ale->adt= BKE_animdata_from_id(data);
			}
				break;
			case ANIMTYPE_DSWOR:
			{
				World *wo= (World *)data;
				AnimData *adt= wo->adt;
				
				ale->flag= FILTER_WOR_SCED(wo); 
				
				ale->key_data= (adt) ? adt->action : NULL;
				ale->datatype= ALE_ACT;
				
				ale->adt= BKE_animdata_from_id(data);
			}
				break;
			case ANIMTYPE_DSNTREE:
			{
				bNodeTree *ntree= (bNodeTree *)data;
				AnimData *adt= ntree->adt;
				
				ale->flag= FILTER_NTREE_SCED(ntree); 
				
				ale->key_data= (adt) ? adt->action : NULL;
				ale->datatype= ALE_ACT;
				
				ale->adt= BKE_animdata_from_id(data);
			}
				break;
			case ANIMTYPE_DSPART:
			{
				ParticleSettings *part= (ParticleSettings*)ale->data;
				AnimData *adt= part->adt;
				
				ale->flag= FILTER_PART_OBJD(part); 
				
				ale->key_data= (adt) ? adt->action : NULL;
				ale->datatype= ALE_ACT;
				
				ale->adt= BKE_animdata_from_id(data);
			}
				break;
			case ANIMTYPE_DSTEX:
			{
				Tex *tex= (Tex *)data;
				AnimData *adt= tex->adt;
				
				ale->flag= FILTER_TEX_DATA(tex); 
				
				ale->key_data= (adt) ? adt->action : NULL;
				ale->datatype= ALE_ACT;
				
				ale->adt= BKE_animdata_from_id(data);
			}
				break;
				
			case ANIMTYPE_GROUP:
			{
				bActionGroup *agrp= (bActionGroup *)data;
				
				ale->flag= agrp->flag;
				
				ale->key_data= NULL;
				ale->datatype= ALE_GROUP;
			}
				break;
			case ANIMTYPE_FCURVE:
			{
				FCurve *fcu= (FCurve *)data;
				
				ale->flag= fcu->flag;
				
				ale->key_data= fcu;
				ale->datatype= ALE_FCURVE;
			}
				break;
				
			case ANIMTYPE_SHAPEKEY:
			{
				KeyBlock *kb= (KeyBlock *)data;
				Key *key= (Key *)ale->id;
				
				ale->flag= kb->flag;
				
				/* whether we have keyframes depends on whether there is a Key block to find it from */
				if (key) {
					/* index of shapekey is defined by place in key's list */
					ale->index= BLI_findindex(&key->block, kb);
					
					/* the corresponding keyframes are from the animdata */
					if (ale->adt && ale->adt->action) {
						bAction *act= ale->adt->action;
						char *rna_path = key_get_curValue_rnaPath(key, kb);
						
						/* try to find the F-Curve which corresponds to this exactly,
						 * then free the MEM_alloc'd string
						 */
						if (rna_path) {
							ale->key_data= (void *)list_find_fcurve(&act->curves, rna_path, 0);
							MEM_freeN(rna_path);
						}
					}
					ale->datatype= (ale->key_data)? ALE_FCURVE : ALE_NONE;
				}
			}	
				break;
			
			case ANIMTYPE_GPLAYER:
			{
				bGPDlayer *gpl= (bGPDlayer *)data;
				
				ale->flag= gpl->flag;
				
				ale->key_data= NULL;
				ale->datatype= ALE_GPFRAME;
			}
				break;
				
			case ANIMTYPE_NLATRACK:
			{
				NlaTrack *nlt= (NlaTrack *)data;
				
				ale->flag= nlt->flag;
				
				ale->key_data= &nlt->strips;
				ale->datatype= ALE_NLASTRIP;
			}
				break;
			case ANIMTYPE_NLAACTION:
			{
				/* nothing to include for now... nothing editable from NLA-perspective here */
				ale->key_data= NULL;
				ale->datatype= ALE_NONE;
			}
				break;
		}
	}
	
	/* return created datatype */
	return ale;
}
 
/* ----------------------------------------- */

/* 'Only Selected' selected data filtering
 * NOTE: when this function returns true, the F-Curve is to be skipped 
 */
static int skip_fcurve_selected_data (bDopeSheet *ads, FCurve *fcu, ID *owner_id, int filter_mode)
{
	if (GS(owner_id->name) == ID_OB) {
		Object *ob= (Object *)owner_id;
		
		/* only consider if F-Curve involves pose.bones */
		if ((fcu->rna_path) && strstr(fcu->rna_path, "pose.bones")) {
			bPoseChannel *pchan;
			char *bone_name;
			
			/* get bone-name, and check if this bone is selected */
			bone_name= BLI_getQuotedStr(fcu->rna_path, "pose.bones[");
			pchan= get_pose_channel(ob->pose, bone_name);
			if (bone_name) MEM_freeN(bone_name);
			
			/* check whether to continue or skip */
			if ((pchan) && (pchan->bone)) {
				/* if only visible channels, skip if bone not visible unless user wants channels from hidden data too */
				if ((filter_mode & ANIMFILTER_VISIBLE) && !(ads->filterflag & ADS_FILTER_INCL_HIDDEN)) {
					bArmature *arm= (bArmature *)ob->data;
					
					if ((arm->layer & pchan->bone->layer) == 0)
						return 1;
				}
				
				/* can only add this F-Curve if it is selected */
				if ((pchan->bone->flag & BONE_SELECTED) == 0)
					return 1;
			}
		}
	}
	else if (GS(owner_id->name) == ID_SCE) {
		Scene *scene = (Scene *)owner_id;
		
		/* only consider if F-Curve involves sequence_editor.sequences */
		if ((fcu->rna_path) && strstr(fcu->rna_path, "sequences_all")) {
			Editing *ed= seq_give_editing(scene, FALSE);
			Sequence *seq;
			char *seq_name;
			
			/* get strip name, and check if this strip is selected */
			seq_name= BLI_getQuotedStr(fcu->rna_path, "sequences_all[");
			seq = get_seq_by_name(ed->seqbasep, seq_name, FALSE);
			if (seq_name) MEM_freeN(seq_name);
			
			/* can only add this F-Curve if it is selected */
			if (seq==NULL || (seq->flag & SELECT)==0)
				return 1;
		}
	}
	else if (GS(owner_id->name) == ID_NT) {
		bNodeTree *ntree = (bNodeTree *)owner_id;
		
		/* check for selected  nodes */
		if ((fcu->rna_path) && strstr(fcu->rna_path, "nodes")) {
			bNode *node;
			char *node_name;
			
			/* get strip name, and check if this strip is selected */
			node_name= BLI_getQuotedStr(fcu->rna_path, "nodes[");
			node = nodeFindNodebyName(ntree, node_name);
			if (node_name) MEM_freeN(node_name);
			
			/* can only add this F-Curve if it is selected */
			if ((node) && (node->flag & NODE_SELECT)==0)
				return 1;
		}
	}
	return 0;
}

/* (Display-)Name-based F-Curve filtering
 * NOTE: when this function returns true, the F-Curve is to be skipped 
 */
static short skip_fcurve_with_name (bDopeSheet *ads, FCurve *fcu, ID *owner_id)
{
	bAnimListElem ale_dummy = {0};
	bAnimChannelType *acf;
	
	/* create a dummy wrapper for the F-Curve */
	ale_dummy.type = ANIMTYPE_FCURVE;
	ale_dummy.id = owner_id;
	ale_dummy.data = fcu;
	
	/* get type info for channel */
	acf = ANIM_channel_get_typeinfo(&ale_dummy);
	if (acf && acf->name) {
		char name[256]; /* hopefully this will be enough! */
		
		/* get name */
		acf->name(&ale_dummy, name);
		
		/* check for partial match with the match string, assuming case insensitive filtering 
		 * if match, this channel shouldn't be ignored!
		 */
		return BLI_strcasestr(name, ads->searchstr) == NULL;
	}
	
	/* just let this go... */
	return 1;
}

/* find the next F-Curve that is usable for inclusion */
static FCurve *animdata_filter_fcurve_next (bDopeSheet *ads, FCurve *first, bActionGroup *grp, int filter_mode, ID *owner_id)
{
	FCurve *fcu = NULL;
	
	/* loop over F-Curves - assume that the caller of this has already checked that these should be included 
	 * NOTE: we need to check if the F-Curves belong to the same group, as this gets called for groups too...
	 */
	for (fcu= first; ((fcu) && (fcu->grp==grp)); fcu= fcu->next) {
		/* special exception for Pose-Channel/Sequence-Strip/Node Based F-Curves:
		 *	- the 'Only Selected' data filter should be applied to Pose-Channel data too, but those are
		 *	  represented as F-Curves. The way the filter for objects worked was to be the first check
		 *	  after 'normal' visibility, so this is done first here too...
		 *	- we currently use an 'approximate' method for getting these F-Curves that doesn't require
		 *	  carefully checking the entire path
		 *	- this will also affect things like Drivers, and also works for Bone Constraints
		 */
		if ( ((ads) && (ads->filterflag & ADS_FILTER_ONLYSEL)) && (owner_id) ) {
			if (skip_fcurve_selected_data(ads, fcu, owner_id, filter_mode))
				continue;
		}
		
		/* only include if visible (Graph Editor check, not channels check) */
		if (!(filter_mode & ANIMFILTER_CURVEVISIBLE) || (fcu->flag & FCURVE_VISIBLE)) {
			/* only work with this channel and its subchannels if it is editable */
			if (!(filter_mode & ANIMFILTER_FOREDIT) || EDITABLE_FCU(fcu)) {
				/* only include this curve if selected in a way consistent with the filtering requirements */
				if ( ANIMCHANNEL_SELOK(SEL_FCU(fcu)) && ANIMCHANNEL_SELEDITOK(SEL_FCU(fcu)) ) {
					/* only include if this curve is active */
					if (!(filter_mode & ANIMFILTER_ACTIVE) || (fcu->flag & FCURVE_ACTIVE)) {
						/* name based filtering... */
						if ( ((ads) && (ads->filterflag & ADS_FILTER_BY_FCU_NAME)) && (owner_id) ) {
							if (skip_fcurve_with_name(ads, fcu, owner_id))
								continue;
						}
						
						/* this F-Curve can be used, so return it */
						return fcu;
					}
				}
			}
		}
	}
	
	/* no (more) F-Curves from the list are suitable... */
	return NULL;
}

static int animdata_filter_fcurves (ListBase *anim_data, bDopeSheet *ads, FCurve *first, bActionGroup *grp, void *owner, short ownertype, int filter_mode, ID *owner_id)
{
	FCurve *fcu;
	int items = 0;
	
	/* loop over every F-Curve able to be included 
	 *	- this for-loop works like this: 
	 *		1) the starting F-Curve is assigned to the fcu pointer so that we have a starting point to search from
	 *		2) the first valid F-Curve to start from (which may include the one given as 'first') in the remaining 
	 *		   list of F-Curves is found, and verified to be non-null
	 *		3) the F-Curve referenced by fcu pointer is added to the list
	 *		4) the fcu pointer is set to the F-Curve after the one we just added, so that we can keep going through 
	 *		   the rest of the F-Curve list without an eternal loop. Back to step 2 :)
	 */
	for (fcu=first; ( (fcu = animdata_filter_fcurve_next(ads, fcu, grp, filter_mode, owner_id)) ); fcu=fcu->next)
	{
		bAnimListElem *ale = make_new_animlistelem(fcu, ANIMTYPE_FCURVE, owner, ownertype, owner_id);
		
		if (ale) {
			BLI_addtail(anim_data, ale);
			items++;
		}
	}
	
	/* return the number of items added to the list */
	return items;
}

static int animdata_filter_action (bAnimContext *ac, ListBase *anim_data, bDopeSheet *ads, bAction *act, int filter_mode, void *owner, short ownertype, ID *owner_id)
{
	bAnimListElem *ale=NULL;
	bActionGroup *agrp;
	FCurve *lastchan=NULL;
	int items = 0;
	
	/* don't include anything from this action if it is linked in from another file,
	 * and we're getting stuff for editing...
	 */
	// TODO: need a way of tagging other channels that may also be affected...
	if ((filter_mode & ANIMFILTER_FOREDIT) && (act->id.lib))
		return 0;
	
	/* loop over groups */
	// TODO: in future, should we expect to need nested groups?
	for (agrp= act->groups.first; agrp; agrp= agrp->next) {
		FCurve *first_fcu;
		int filter_gmode;
		
		/* store reference to last channel of group */
		if (agrp->channels.last) 
			lastchan= agrp->channels.last;
		
		
		/* make a copy of filtering flags for use by the sub-channels of this group */
		filter_gmode= filter_mode;
		
		/* if we care about the selection status of the channels, 
		 * but the group isn't expanded...
		 */
		if ( (filter_mode & (ANIMFILTER_SEL|ANIMFILTER_UNSEL)) &&	/* care about selection status */
			 (EXPANDED_AGRP(agrp)==0) )								/* group isn't expanded */
		{
			/* if the group itself isn't selected appropriately, we shouldn't consider it's children either */
			if (ANIMCHANNEL_SELOK(SEL_AGRP(agrp)) == 0)
				continue;
			
			/* if we're still here, then the selection status of the curves within this group should not matter,
			 * since this creates too much overhead for animators (i.e. making a slow workflow)
			 *
			 * Tools affected by this at time of coding (2010 Feb 09):
			 *	- inserting keyframes on selected channels only
			 *	- pasting keyframes
			 *	- creating ghost curves in Graph Editor
			 */
			filter_gmode &= ~(ANIMFILTER_SEL|ANIMFILTER_UNSEL);
		}
		
		
		/* get the first F-Curve in this group we can start to use, and if there isn't any F-Curve to start from,  
		 * then don't use this group at all...
		 *
		 * NOTE: use filter_gmode here not filter_mode, since there may be some flags we shouldn't consider under certain circumstances
		 */
		first_fcu = animdata_filter_fcurve_next(ads, agrp->channels.first, agrp, filter_gmode, owner_id);
		
		/* Bug note: 
		 * 	Selecting open group to toggle visbility of the group, where the F-Curves of the group are not suitable 
		 *	for inclusion due to their selection status (vs visibility status of bones/etc., as is usually the case),
		 *	will not work, since the group gets skipped. However, fixing this can easily reintroduce the bugs whereby
		 * 	hidden groups (due to visibility status of bones/etc.) that were selected before becoming invisible, can
		 *	easily get deleted accidentally as they'd be included in the list filtered for that purpose.
		 *
		 * 	So, for now, best solution is to just leave this note here, and hope to find a solution at a later date.
		 *	-- Joshua Leung, 2010 Feb 10
		 */
		if (first_fcu) {
			/* add this group as a channel first */
			if ((filter_mode & ANIMFILTER_CHANNELS) || !(filter_mode & ANIMFILTER_CURVESONLY)) {
				/* filter selection of channel specially here again, since may be open and not subject to previous test */
				if ( ANIMCHANNEL_SELOK(SEL_AGRP(agrp)) ) {
					ale= make_new_animlistelem(agrp, ANIMTYPE_GROUP, NULL, ANIMTYPE_NONE, owner_id);
					if (ale) {
						BLI_addtail(anim_data, ale);
						items++;
					}
				}
			}
			
			/* there are some situations, where only the channels of the action group should get considered */
			if (!(filter_mode & ANIMFILTER_ACTGROUPED) || (agrp->flag & AGRP_ACTIVE)) {
				/* filters here are a bit convoulted...
				 *	- groups show a "summary" of keyframes beside their name which must accessable for tools which handle keyframes
				 *	- groups can be collapsed (and those tools which are only interested in channels rely on knowing that group is closed)
				 *
				 * cases when we should include F-Curves inside group:
				 *	- we don't care about visibility
				 *	- group is expanded
				 *	- we just need the F-Curves present
				 */
				if ( (!(filter_mode & ANIMFILTER_VISIBLE) || EXPANDED_AGRP(agrp)) || (filter_mode & ANIMFILTER_CURVESONLY) ) 
				{
					/* for the Graph Editor, curves may be set to not be visible in the view to lessen clutter,
					 * but to do this, we need to check that the group doesn't have it's not-visible flag set preventing 
					 * all its sub-curves to be shown
					 */
					if ( !(filter_mode & ANIMFILTER_CURVEVISIBLE) || !(agrp->flag & AGRP_NOTVISIBLE) )
					{
						if (!(filter_mode & ANIMFILTER_FOREDIT) || EDITABLE_AGRP(agrp)) {
							/* NOTE: filter_gmode is used here, not standard filter_mode, since there may be some flags that shouldn't apply */
							items += animdata_filter_fcurves(anim_data, ads, first_fcu, agrp, owner, ownertype, filter_gmode, owner_id);
						}
					}
				}
			}
		}
	}
	
	/* loop over un-grouped F-Curves (only if we're not only considering those channels in the animive group) */
	if (!(filter_mode & ANIMFILTER_ACTGROUPED))  {
		// XXX the 'owner' info here needs review...
		items += animdata_filter_fcurves(anim_data, ads, (lastchan)?(lastchan->next):(act->curves.first), NULL, owner, ownertype, filter_mode, owner_id);
	}
	
	/* return the number of items added to the list */
	return items;
}

/* Include NLA-Data for NLA-Editor:
 *	- when ANIMFILTER_CHANNELS is used, that means we should be filtering the list for display
 *	  Although the evaluation order is from the first track to the last and then apply the Action on top,
 *	  we present this in the UI as the Active Action followed by the last track to the first so that we 
 *	  get the evaluation order presented as per a stack.
 *	- for normal filtering (i.e. for editing), we only need the NLA-tracks but they can be in 'normal' evaluation
 *	  order, i.e. first to last. Otherwise, some tools may get screwed up.
 */
static int animdata_filter_nla (bAnimContext *UNUSED(ac), ListBase *anim_data, bDopeSheet *UNUSED(ads), AnimData *adt, int filter_mode, void *owner, short ownertype, ID *owner_id)
{
	bAnimListElem *ale;
	NlaTrack *nlt;
	NlaTrack *first=NULL, *next=NULL;
	int items = 0;
	
	/* if showing channels, include active action */
	if (filter_mode & ANIMFILTER_CHANNELS) {
		/* there isn't really anything editable here, so skip if need editable */
		// TODO: currently, selection isn't checked since it doesn't matter
		if ((filter_mode & ANIMFILTER_FOREDIT) == 0) { 
			/* just add the action track now (this MUST appear for drawing)
			 *	- as AnimData may not have an action, we pass a dummy pointer just to get the list elem created, then
			 *	  overwrite this with the real value - REVIEW THIS...
			 */
			ale= make_new_animlistelem((void *)(&adt->action), ANIMTYPE_NLAACTION, owner, ownertype, owner_id);
			ale->data= (adt->action) ? adt->action : NULL;
				
			if (ale) {
				BLI_addtail(anim_data, ale);
				items++;
			}
		}
		
		/* first track to include will be the last one if we're filtering by channels */
		first= adt->nla_tracks.last;
	}
	else {
		/* first track to include will the the first one (as per normal) */
		first= adt->nla_tracks.first;
	}
	
	/* loop over NLA Tracks - assume that the caller of this has already checked that these should be included */
	for (nlt= first; nlt; nlt= next) {
		/* 'next' NLA-Track to use depends on whether we're filtering for drawing or not */
		if (filter_mode & ANIMFILTER_CHANNELS) 
			next= nlt->prev;
		else
			next= nlt->next;
		
		/* if we're in NLA-tweakmode, don't show this track if it was disabled (due to tweaking) for now 
		 *	- active track should still get shown though (even though it has disabled flag set)
		 */
		// FIXME: the channels after should still get drawn, just 'differently', and after an active-action channel
		if ((adt->flag & ADT_NLA_EDIT_ON) && (nlt->flag & NLATRACK_DISABLED) && !(nlt->flag & NLATRACK_ACTIVE))
			continue;
		
		/* only work with this channel and its subchannels if it is editable */
		if (!(filter_mode & ANIMFILTER_FOREDIT) || EDITABLE_NLT(nlt)) {
			/* only include this track if selected in a way consistent with the filtering requirements */
			if ( ANIMCHANNEL_SELOK(SEL_NLT(nlt)) ) {
				/* only include if this track is active */
				if (!(filter_mode & ANIMFILTER_ACTIVE) || (nlt->flag & NLATRACK_ACTIVE)) {
					ale= make_new_animlistelem(nlt, ANIMTYPE_NLATRACK, owner, ownertype, owner_id);
						
					if (ale) {
						BLI_addtail(anim_data, ale);
						items++;
					}
				}
			}
		}
	}
	
	/* return the number of items added to the list */
	return items;
}

/* Include ShapeKey Data for ShapeKey Editor */
static int animdata_filter_shapekey (bAnimContext *ac, ListBase *anim_data, Key *key, int filter_mode)
{
	bAnimListElem *ale;
	int items = 0;
	
	/* check if channels or only F-Curves */
	if ((filter_mode & ANIMFILTER_CURVESONLY) == 0) {
		KeyBlock *kb;
		
		/* loop through the channels adding ShapeKeys as appropriate */
		for (kb= key->block.first; kb; kb= kb->next) {
			/* skip the first one, since that's the non-animateable basis */
			// XXX maybe in future this may become handy?
			if (kb == key->block.first) continue;
			
			/* only work with this channel and its subchannels if it is editable */
			if (!(filter_mode & ANIMFILTER_FOREDIT) || EDITABLE_SHAPEKEY(kb)) {
				/* only include this track if selected in a way consistent with the filtering requirements */
				if ( ANIMCHANNEL_SELOK(SEL_SHAPEKEY(kb)) ) {
					// TODO: consider 'active' too?
					
					/* owner-id here must be key so that the F-Curve can be resolved... */
					ale= make_new_animlistelem(kb, ANIMTYPE_SHAPEKEY, NULL, ANIMTYPE_NONE, (ID *)key);
					
					if (ale) {
						BLI_addtail(anim_data, ale);
						items++;
					}
				}
			}
		}
	}
	else {
		/* just use the action associated with the shapekey */
		// FIXME: is owner-id and having no owner/dopesheet really fine?
		if (key->adt) {
			if (filter_mode & ANIMFILTER_ANIMDATA)
				ANIMDATA_ADD_ANIMDATA(key)
			else if (key->adt->action)
				items= animdata_filter_action(ac, anim_data, NULL, key->adt->action, filter_mode, NULL, ANIMTYPE_NONE, (ID *)key);
		}
	}
	
	/* return the number of items added to the list */
	return items;
}

/* Grab all Grase Pencil datablocks in file */
// TODO: should this be amalgamated with the dopesheet filtering code?
static int animdata_filter_gpencil (ListBase *anim_data, void *UNUSED(data), int filter_mode)
{
	bAnimListElem *ale;
	bGPdata *gpd;
	bGPDlayer *gpl;
	int items = 0;
	
	/* check if filtering types are appropriate */
	if (!(filter_mode & (ANIMFILTER_ACTGROUPED|ANIMFILTER_CURVESONLY)))
	{
		/* for now, grab grease pencil datablocks directly from main*/
		for (gpd = G.main->gpencil.first; gpd; gpd = gpd->id.next) {
			/* only show if gpd is used by something... */
			if (ID_REAL_USERS(gpd) < 1)
				continue;
			
			/* add gpd as channel too (if for drawing, and it has layers) */
			if ((filter_mode & ANIMFILTER_CHANNELS) && (gpd->layers.first)) {
				/* add to list */
				ale= make_new_animlistelem(gpd, ANIMTYPE_GPDATABLOCK, NULL, ANIMTYPE_NONE, NULL);
				if (ale) {
					BLI_addtail(anim_data, ale);
					items++;
				}
			}
			
			/* only add layers if they will be visible (if drawing channels) */
			if ( !(filter_mode & ANIMFILTER_VISIBLE) || (EXPANDED_GPD(gpd)) ) {
				/* loop over layers as the conditions are acceptable */
				for (gpl= gpd->layers.first; gpl; gpl= gpl->next) {
					/* only if selected */
					if ( ANIMCHANNEL_SELOK(SEL_GPL(gpl)) ) {
						/* only if editable */
						if (!(filter_mode & ANIMFILTER_FOREDIT) || EDITABLE_GPL(gpl)) {
							/* add to list */
							ale= make_new_animlistelem(gpl, ANIMTYPE_GPLAYER, gpd, ANIMTYPE_GPDATABLOCK, (ID*)gpd);
							if (ale) {
								BLI_addtail(anim_data, ale);
								items++;
							}
						}
					}
				}
			}
		}
	}
	
	/* return the number of items added to the list */
	return items;
}

/* NOTE: owner_id is either material, lamp, or world block, which is the direct owner of the texture stack in question */
static int animdata_filter_dopesheet_texs (bAnimContext *ac, ListBase *anim_data, bDopeSheet *ads, ID *owner_id, int filter_mode)
{
	ListBase texs = {NULL, NULL};
	LinkData *ld;
	MTex **mtex = NULL;
	short expanded=0;
	int ownertype = ANIMTYPE_NONE;
	
	bAnimListElem *ale=NULL;
	int items=0, a=0;
	
	/* get datatype specific data first */
	if (owner_id == NULL)
		return 0;
	
	switch (GS(owner_id->name)) {
		case ID_MA:
		{
			Material *ma= (Material *)owner_id;
			
			mtex= (MTex**)(&ma->mtex);
			expanded= FILTER_TEX_MATC(ma);
			ownertype= ANIMTYPE_DSMAT;
		}
			break;
		case ID_LA:
		{
			Lamp *la= (Lamp *)owner_id;
			
			mtex= (MTex**)(&la->mtex);
			expanded= FILTER_TEX_LAMC(la);
			ownertype= ANIMTYPE_DSLAM;
		}
			break;
		case ID_WO:
		{
			World *wo= (World *)owner_id;
			
			mtex= (MTex**)(&wo->mtex);
			expanded= FILTER_TEX_WORC(wo);
			ownertype= ANIMTYPE_DSWOR;
		}
			break;
		default: 
		{
			/* invalid/unsupported option */
			if (G.f & G_DEBUG)
				printf("ERROR: unsupported owner_id (i.e. texture stack) for filter textures - %s \n", owner_id->name);
			return 0;
		}
	}
	
	/* firstly check that we actuallly have some textures, by gathering all textures in a temp list */
	for (a=0; a < MAX_MTEX; a++) {
		Tex *tex= (mtex[a]) ? mtex[a]->tex : NULL;
		short ok = 0;
		
		/* for now, if no texture returned, skip (this shouldn't confuse the user I hope) */
		if (ELEM(NULL, tex, tex->adt)) 
			continue;
		
		/* check if ok */
		ANIMDATA_FILTER_CASES(tex, 
			{ /* AnimData blocks - do nothing... */ },
			ok=1;, 
			ok=1;, 
			ok=1;)
		if (ok == 0) continue;
		
		/* make a temp list elem for this */
		ld= MEM_callocN(sizeof(LinkData), "DopeSheet-TextureCache");
		ld->data= tex;
		BLI_addtail(&texs, ld);
	}
	
	/* if there were no channels found, no need to carry on */
	if (texs.first == NULL)
		return 0;
	
	/* include textures-expand widget? */
	if ((filter_mode & ANIMFILTER_CHANNELS) && !(filter_mode & ANIMFILTER_CURVESONLY)) {
		ale= make_new_animlistelem(owner_id, ANIMTYPE_FILLTEXD, owner_id, ownertype, owner_id);
		if (ale) {
			BLI_addtail(anim_data, ale);
			items++;
		}
	}
	
	/* add textures */
	if ((expanded) || (filter_mode & ANIMFILTER_CURVESONLY)) {
		/* for each texture in cache, add channels  */
		for (ld= texs.first; ld; ld= ld->next) {
			Tex *tex= (Tex *)ld->data;
			
			/* include texture-expand widget? */
			if (filter_mode & ANIMFILTER_CHANNELS) {
				/* check if filtering by active status */
				if ANIMCHANNEL_ACTIVEOK(tex) {
					ale= make_new_animlistelem(tex, ANIMTYPE_DSTEX, owner_id, ownertype, owner_id);
					if (ale) {
						BLI_addtail(anim_data, ale);
						items++;
					}
				}
			}
			
			/* add texture's animation data
			 * NOTE: for these, we make the owner/ownertype the material/lamp/etc. not the texture, otherwise the
			 * drawing code cannot resolve the indention easily
			 */
			if (!(filter_mode & ANIMFILTER_VISIBLE) || FILTER_TEX_DATA(tex) || (filter_mode & ANIMFILTER_CURVESONLY)) {
				ANIMDATA_FILTER_CASES(tex, 
					{ /* AnimData blocks - do nothing... */ },
					items += animdata_filter_nla(ac, anim_data, ads, tex->adt, filter_mode, owner_id, ownertype, (ID *)tex);, 
					items += animdata_filter_fcurves(anim_data, ads, tex->adt->drivers.first, NULL, owner_id, ownertype, filter_mode, (ID *)tex);, 
					items += animdata_filter_action(ac, anim_data, ads, tex->adt->action, filter_mode, owner_id, ownertype, (ID *)tex);)
			}
		}
	}
	
	/* free cache */
	BLI_freelistN(&texs);
	
	/* return the number of items added to the list */
	return items;
}

static int animdata_filter_dopesheet_mats (bAnimContext *ac, ListBase *anim_data, bDopeSheet *ads, Base *base, int filter_mode)
{
	ListBase mats = {NULL, NULL};
	LinkData *ld;
	
	bAnimListElem *ale=NULL;
	Object *ob= base->object;
	int items=0, a=0;
	
	/* firstly check that we actuallly have some materials, by gathering all materials in a temp list */
	for (a=1; a <= ob->totcol; a++) {
		Material *ma= give_current_material(ob, a);
		short ok = 0;
		
		/* for now, if no material returned, skip (this shouldn't confuse the user I hope) */
		if (ma == NULL) continue;

		/* check if ok */
		ANIMDATA_FILTER_CASES(ma, 
			{ /* AnimData blocks - do nothing... */ },
			ok=1;, 
			ok=1;, 
			ok=1;)

		/* need to check textures */
		if (ok == 0 && !(ads->filterflag & ADS_FILTER_NOTEX)) {
			int mtInd;

			for (mtInd=0; mtInd < MAX_MTEX; mtInd++) {
				MTex *mtex = ma->mtex[mtInd];

				if(mtex && mtex->tex) {
					ANIMDATA_FILTER_CASES(mtex->tex,
					{ /* AnimData blocks - do nothing... */ },
					ok=1;, 
					ok=1;, 
					ok=1;)
				}

				if(ok)
					break;
			}
		}
		
		if (ok == 0) continue;
		
		/* make a temp list elem for this */
		ld= MEM_callocN(sizeof(LinkData), "DopeSheet-MaterialCache");
		ld->data= ma;
		BLI_addtail(&mats, ld);
	}
	
	/* if there were no channels found, no need to carry on */
	if (mats.first == NULL)
		return 0;
	
	/* include materials-expand widget? */
	if ((filter_mode & ANIMFILTER_CHANNELS) && !(filter_mode & ANIMFILTER_CURVESONLY)) {
		ale= make_new_animlistelem(ob, ANIMTYPE_FILLMATD, base, ANIMTYPE_OBJECT, (ID *)ob);
		if (ale) {
			BLI_addtail(anim_data, ale);
			items++;
		}
	}
	
	/* add materials? */
	if (FILTER_MAT_OBJC(ob) || (filter_mode & ANIMFILTER_CURVESONLY)) {
		/* for each material in cache, add channels  */
		for (ld= mats.first; ld; ld= ld->next) {
			Material *ma= (Material *)ld->data;
			
			/* include material-expand widget? */
			// hmm... do we need to store the index of this material in the array anywhere?
			if (filter_mode & ANIMFILTER_CHANNELS) {
				/* check if filtering by active status */
				if ANIMCHANNEL_ACTIVEOK(ma) {
					ale= make_new_animlistelem(ma, ANIMTYPE_DSMAT, base, ANIMTYPE_OBJECT, (ID *)ma);
					if (ale) {
						BLI_addtail(anim_data, ale);
						items++;
					}
				}
			}
			
			/* add material's animation data */
			if (!(filter_mode & ANIMFILTER_VISIBLE) || FILTER_MAT_OBJD(ma) || (filter_mode & ANIMFILTER_CURVESONLY)) {
				/* material's animation data */
				ANIMDATA_FILTER_CASES(ma, 
					{ /* AnimData blocks - do nothing... */ },
					items += animdata_filter_nla(ac, anim_data, ads, ma->adt, filter_mode, ma, ANIMTYPE_DSMAT, (ID *)ma);, 
					items += animdata_filter_fcurves(anim_data, ads, ma->adt->drivers.first, NULL, ma, ANIMTYPE_DSMAT, filter_mode, (ID *)ma);, 
					items += animdata_filter_action(ac, anim_data, ads, ma->adt->action, filter_mode, ma, ANIMTYPE_DSMAT, (ID *)ma);)
					
				/* textures */
				if (!(ads->filterflag & ADS_FILTER_NOTEX))
					items += animdata_filter_dopesheet_texs(ac, anim_data, ads, (ID *)ma, filter_mode);
			}
		}
	}
	
	/* free cache */
	BLI_freelistN(&mats);
	
	/* return the number of items added to the list */
	return items;
}

static int animdata_filter_dopesheet_particles (bAnimContext *ac, ListBase *anim_data, bDopeSheet *ads, Base *base, int filter_mode)
{
	bAnimListElem *ale=NULL;
	Object *ob= base->object;
	ParticleSystem *psys = ob->particlesystem.first;
	int items= 0, first = 1;

	for(; psys; psys=psys->next) {
		short ok = 0;

		if(ELEM(NULL, psys->part, psys->part->adt))
			continue;

		ANIMDATA_FILTER_CASES(psys->part,
			{ /* AnimData blocks - do nothing... */ },
			ok=1;, 
			ok=1;, 
			ok=1;)
		if (ok == 0) continue;

		/* include particles-expand widget? */
		if (first && (filter_mode & ANIMFILTER_CHANNELS) && !(filter_mode & ANIMFILTER_CURVESONLY)) {
			ale= make_new_animlistelem(ob, ANIMTYPE_FILLPARTD, base, ANIMTYPE_OBJECT, (ID *)ob);
			if (ale) {
				BLI_addtail(anim_data, ale);
				items++;
			}
			first = 0;
		}
		
		/* add particle settings? */
		if (FILTER_PART_OBJC(ob) || (filter_mode & ANIMFILTER_CURVESONLY)) {
			if ((filter_mode & ANIMFILTER_CHANNELS)) {
				/* check if filtering by active status */
				if ANIMCHANNEL_ACTIVEOK(psys->part) {
					ale = make_new_animlistelem(psys->part, ANIMTYPE_DSPART, base, ANIMTYPE_OBJECT, (ID *)psys->part);
					if (ale) {
						BLI_addtail(anim_data, ale);
						items++;
					}
				}
			}
			
			if (!(filter_mode & ANIMFILTER_VISIBLE) || FILTER_PART_OBJD(psys->part) || (filter_mode & ANIMFILTER_CURVESONLY)) {
				ANIMDATA_FILTER_CASES(psys->part,
					{ /* AnimData blocks - do nothing... */ },
					items += animdata_filter_nla(ac, anim_data, ads, psys->part->adt, filter_mode, psys->part, ANIMTYPE_DSPART, (ID *)psys->part);, 
					items += animdata_filter_fcurves(anim_data, ads, psys->part->adt->drivers.first, NULL, psys->part, ANIMTYPE_DSPART, filter_mode, (ID *)psys->part);, 
					items += animdata_filter_action(ac, anim_data, ads, psys->part->adt->action, filter_mode, psys->part, ANIMTYPE_DSPART, (ID *)psys->part);)
			}
		}
	}
	
	/* return the number of items added to the list */
	return items;
}

static int animdata_filter_dopesheet_obdata (bAnimContext *ac, ListBase *anim_data, bDopeSheet *ads, Base *base, int filter_mode)
{
	bAnimListElem *ale=NULL;
	Object *ob= base->object;
	IdAdtTemplate *iat= ob->data;
	AnimData *adt= iat->adt;
	short type=0, expanded=0;
	int items= 0;
	
	/* get settings based on data type */
	switch (ob->type) {
		case OB_CAMERA: /* ------- Camera ------------ */
		{
			Camera *ca= (Camera *)ob->data;
			
			type= ANIMTYPE_DSCAM;
			expanded= FILTER_CAM_OBJD(ca);
		}
			break;
		case OB_LAMP: /* ---------- Lamp ----------- */
		{
			Lamp *la= (Lamp *)ob->data;
			
			type= ANIMTYPE_DSLAM;
			expanded= FILTER_LAM_OBJD(la);
		}
			break;
		case OB_CURVE: /* ------- Curve ---------- */
		case OB_SURF: /* ------- Nurbs Surface ---------- */
		case OB_FONT: /* ------- Text Curve ---------- */
		{
			Curve *cu= (Curve *)ob->data;
			
			type= ANIMTYPE_DSCUR;
			expanded= FILTER_CUR_OBJD(cu);
		}
			break;
		case OB_MBALL: /* ------- MetaBall ---------- */
		{
			MetaBall *mb= (MetaBall *)ob->data;
			
			type= ANIMTYPE_DSMBALL;
			expanded= FILTER_MBALL_OBJD(mb);
		}
			break;
		case OB_ARMATURE: /* ------- Armature ---------- */
		{
			bArmature *arm= (bArmature *)ob->data;
			
			type= ANIMTYPE_DSARM;
			expanded= FILTER_ARM_OBJD(arm);
		}
			break;
		case OB_MESH: /* ------- Mesh ---------- */
		{
			Mesh *me= (Mesh *)ob->data;
			
			type= ANIMTYPE_DSMESH;
			expanded= FILTER_MESH_OBJD(me);
		}
			break;
		case OB_LATTICE: /* ---- Lattice ---- */
		{
			Lattice *lt = (Lattice *)ob->data;
			
			type= ANIMTYPE_DSLAT;
			expanded= FILTER_LATTICE_OBJD(lt);
		}
			break;
	}
	
	/* special exception for drivers instead of action */
	if (ads->filterflag & ADS_FILTER_ONLYDRIVERS)
		expanded= EXPANDED_DRVD(adt);
	
	/* include data-expand widget? */
	if ((filter_mode & ANIMFILTER_CURVESONLY) == 0) {	
		/* check if filtering by active status */
		if ANIMCHANNEL_ACTIVEOK(iat) {
			ale= make_new_animlistelem(iat, type, base, ANIMTYPE_OBJECT, (ID *)iat);
			if (ale) BLI_addtail(anim_data, ale);
		}
	}
	
	/* add object-data animation channels? */
	if (!(filter_mode & ANIMFILTER_VISIBLE) || (expanded) || (filter_mode & ANIMFILTER_CURVESONLY)) {
		/* filtering for channels - nla, drivers, keyframes */
		ANIMDATA_FILTER_CASES(iat, 
			{ /* AnimData blocks - do nothing... */ },
			items+= animdata_filter_nla(ac, anim_data, ads, iat->adt, filter_mode, iat, type, (ID *)iat);,
			items+= animdata_filter_fcurves(anim_data, ads, adt->drivers.first, NULL, iat, type, filter_mode, (ID *)iat);, 
			items+= animdata_filter_action(ac, anim_data, ads, iat->adt->action, filter_mode, iat, type, (ID *)iat);)
			
		/* sub-data filtering... */
		switch (ob->type) {
			case OB_LAMP:	/* lamp - textures */
			{
				/* textures */
				if (!(ads->filterflag & ADS_FILTER_NOTEX))
					items += animdata_filter_dopesheet_texs(ac, anim_data, ads, ob->data, filter_mode);
			}
				break;
		}
	}
	
	/* return the number of items added to the list */
	return items;
}

static int animdata_filter_dopesheet_ob (bAnimContext *ac, ListBase *anim_data, bDopeSheet *ads, Base *base, int filter_mode)
{
	bAnimListElem *ale=NULL;
	AnimData *adt = NULL;
	Object *ob= base->object;
	Key *key= ob_get_key(ob);
	short obdata_ok = 0;
	int items = 0;
	
	/* add this object as a channel first */
	if ((filter_mode & (ANIMFILTER_CURVESONLY|ANIMFILTER_NLATRACKS)) == 0) {
		/* check if filtering by selection */
		if ANIMCHANNEL_SELOK((base->flag & SELECT)) {
			/* check if filtering by active status */
			if ANIMCHANNEL_ACTIVEOK(ob) {
				ale= make_new_animlistelem(base, ANIMTYPE_OBJECT, NULL, ANIMTYPE_NONE, (ID *)ob);
				if (ale) {
					BLI_addtail(anim_data, ale);
					items++;
				}
			}
		}
	}
	
	/* if collapsed, don't go any further (unless adding keyframes only) */
	if ( ((filter_mode & ANIMFILTER_VISIBLE) && EXPANDED_OBJC(ob) == 0) &&
		 !(filter_mode & (ANIMFILTER_CURVESONLY|ANIMFILTER_NLATRACKS)) )
		return items;
	
	/* Action, Drivers, or NLA */
	if (ob->adt && !(ads->filterflag & ADS_FILTER_NOOBJ)) {
		adt= ob->adt;
		ANIMDATA_FILTER_CASES(ob,
			{ /* AnimData blocks - do nothing... */ },
			{ /* nla */
				/* add NLA tracks */
				items += animdata_filter_nla(ac, anim_data, ads, adt, filter_mode, ob, ANIMTYPE_OBJECT, (ID *)ob);
			},
			{ /* drivers */
				/* include drivers-expand widget? */
				if ((filter_mode & ANIMFILTER_CHANNELS) && !(filter_mode & ANIMFILTER_CURVESONLY)) {
					ale= make_new_animlistelem(adt->action, ANIMTYPE_FILLDRIVERS, base, ANIMTYPE_OBJECT, (ID *)ob);
					if (ale) {
						BLI_addtail(anim_data, ale);
						items++;
					}
				}
				
				/* add F-Curve channels (drivers are F-Curves) */
				if (!(filter_mode & ANIMFILTER_VISIBLE) || EXPANDED_DRVD(adt) || !(filter_mode & ANIMFILTER_CHANNELS)) {
					// need to make the ownertype normal object here... (maybe type should be a separate one for clarity?)
					items += animdata_filter_fcurves(anim_data, ads, adt->drivers.first, NULL, ob, ANIMTYPE_OBJECT, filter_mode, (ID *)ob);
				}
			},
			{ /* action (keyframes) */
				/* include action-expand widget? */
				if ((filter_mode & ANIMFILTER_CHANNELS) && !(filter_mode & ANIMFILTER_CURVESONLY)) {
					ale= make_new_animlistelem(adt->action, ANIMTYPE_FILLACTD, base, ANIMTYPE_OBJECT, (ID *)ob);
					if (ale) {
						BLI_addtail(anim_data, ale);
						items++;
					}
				}
				
				/* add F-Curve channels? */
				if (!(filter_mode & ANIMFILTER_VISIBLE) || EXPANDED_ACTC(adt->action) || !(filter_mode & ANIMFILTER_CHANNELS)) {
					// need to make the ownertype normal object here... (maybe type should be a separate one for clarity?)
					items += animdata_filter_action(ac, anim_data, ads, adt->action, filter_mode, ob, ANIMTYPE_OBJECT, (ID *)ob); 
				}
			}
		);
	}
	
	
	/* ShapeKeys? */
	if ((key) && !(ads->filterflag & ADS_FILTER_NOSHAPEKEYS)) {
		adt= key->adt;
		ANIMDATA_FILTER_CASES(key,
			{ /* AnimData blocks - do nothing... */ },
			{ /* nla */
				/* include shapekey-expand widget? */
				if ((filter_mode & ANIMFILTER_CHANNELS) && !(filter_mode & ANIMFILTER_CURVESONLY)) {
					/* check if filtering by active status */
					if ANIMCHANNEL_ACTIVEOK(key) {
						ale= make_new_animlistelem(key, ANIMTYPE_DSSKEY, base, ANIMTYPE_OBJECT, (ID *)ob);
						if (ale) {
							BLI_addtail(anim_data, ale);
							items++;
						}
					}
				}
				
				/* add NLA tracks - only if expanded or so */
				if (!(filter_mode & ANIMFILTER_VISIBLE) || FILTER_SKE_OBJD(key) || (filter_mode & ANIMFILTER_CURVESONLY))
					items += animdata_filter_nla(ac, anim_data, ads, adt, filter_mode, ob, ANIMTYPE_OBJECT, (ID *)key);
			},
			{ /* drivers */
				/* include shapekey-expand widget? */
				if ((filter_mode & ANIMFILTER_CHANNELS) && !(filter_mode & ANIMFILTER_CURVESONLY)) {
					ale= make_new_animlistelem(key, ANIMTYPE_DSSKEY, base, ANIMTYPE_OBJECT, (ID *)ob);
					if (ale) {
						BLI_addtail(anim_data, ale);
						items++;
					}
				}
				
				/* add channels */
				if (!(filter_mode & ANIMFILTER_VISIBLE) || FILTER_SKE_OBJD(key) || (filter_mode & ANIMFILTER_CURVESONLY)) {
					items += animdata_filter_fcurves(anim_data, ads, adt->drivers.first, NULL, key, ANIMTYPE_DSSKEY, filter_mode, (ID *)key);
				}
			},
			{ /* action (keyframes) */
				/* include shapekey-expand widget? */
				if ((filter_mode & ANIMFILTER_CHANNELS) && !(filter_mode & ANIMFILTER_CURVESONLY)) {
					/* check if filtering by active status */
					if ANIMCHANNEL_ACTIVEOK(key) {
						ale= make_new_animlistelem(key, ANIMTYPE_DSSKEY, base, ANIMTYPE_OBJECT, (ID *)ob);
						if (ale) {
							BLI_addtail(anim_data, ale);
							items++;
						}
					}
				}
				
				/* add channels */
				if (!(filter_mode & ANIMFILTER_VISIBLE) || FILTER_SKE_OBJD(key) || (filter_mode & ANIMFILTER_CURVESONLY)) {
					items += animdata_filter_action(ac, anim_data, ads, adt->action, filter_mode, key, ANIMTYPE_DSSKEY, (ID *)key); 
				}
			}
		);
	}

	/* Materials? */
	if ((ob->totcol) && !(ads->filterflag & ADS_FILTER_NOMAT))
		items += animdata_filter_dopesheet_mats(ac, anim_data, ads, base, filter_mode);
	
	/* Object Data */
	switch (ob->type) {
		case OB_CAMERA: /* ------- Camera ------------ */
		{
			Camera *ca= (Camera *)ob->data;
			
			if ((ads->filterflag & ADS_FILTER_NOCAM) == 0) {
				ANIMDATA_FILTER_CASES(ca,
					{ /* AnimData blocks - do nothing... */ },
					obdata_ok= 1;,
					obdata_ok= 1;,
					obdata_ok= 1;)
			}
		}
			break;
		case OB_LAMP: /* ---------- Lamp ----------- */
		{
			Lamp *la= (Lamp *)ob->data;
			
			if ((ads->filterflag & ADS_FILTER_NOLAM) == 0) {
				ANIMDATA_FILTER_CASES(la,
					{ /* AnimData blocks - do nothing... */ },
					obdata_ok= 1;,
					obdata_ok= 1;,
					obdata_ok= 1;)
			}
		}
			break;
		case OB_CURVE: /* ------- Curve ---------- */
		case OB_SURF: /* ------- Nurbs Surface ---------- */
		case OB_FONT: /* ------- Text Curve ---------- */
		{
			Curve *cu= (Curve *)ob->data;
			
			if ((ads->filterflag & ADS_FILTER_NOCUR) == 0) {
				ANIMDATA_FILTER_CASES(cu,
					{ /* AnimData blocks - do nothing... */ },
					obdata_ok= 1;,
					obdata_ok= 1;,
					obdata_ok= 1;)
			}
		}
			break;
		case OB_MBALL: /* ------- MetaBall ---------- */
		{
			MetaBall *mb= (MetaBall *)ob->data;
			
			if ((ads->filterflag & ADS_FILTER_NOMBA) == 0) {
				ANIMDATA_FILTER_CASES(mb,
					{ /* AnimData blocks - do nothing... */ },
					obdata_ok= 1;,
					obdata_ok= 1;,
					obdata_ok= 1;)
			}
		}
			break;
		case OB_ARMATURE: /* ------- Armature ---------- */
		{
			bArmature *arm= (bArmature *)ob->data;
			
			if ((ads->filterflag & ADS_FILTER_NOARM) == 0) {
				ANIMDATA_FILTER_CASES(arm,
					{ /* AnimData blocks - do nothing... */ },
					obdata_ok= 1;,
					obdata_ok= 1;,
					obdata_ok= 1;)
			}
		}
			break;
		case OB_MESH: /* ------- Mesh ---------- */
		{
			Mesh *me= (Mesh *)ob->data;
			
			if ((ads->filterflag & ADS_FILTER_NOMESH) == 0) {
				ANIMDATA_FILTER_CASES(me,
					{ /* AnimData blocks - do nothing... */ },
					obdata_ok= 1;,
					obdata_ok= 1;,
					obdata_ok= 1;)
			}
		}
			break;
		case OB_LATTICE: /* ------- Lattice ---------- */
		{
			Lattice *lt= (Lattice *)ob->data;
			
			if ((ads->filterflag & ADS_FILTER_NOLAT) == 0) {
				ANIMDATA_FILTER_CASES(lt,
					{ /* AnimData blocks - do nothing... */ },
					obdata_ok= 1;,
					obdata_ok= 1;,
					obdata_ok= 1;)
			}
		}
			break;
	}
	if (obdata_ok) 
		items += animdata_filter_dopesheet_obdata(ac, anim_data, ads, base, filter_mode);

	/* particles */
	if (ob->particlesystem.first && !(ads->filterflag & ADS_FILTER_NOPART))
		items += animdata_filter_dopesheet_particles(ac, anim_data, ads, base, filter_mode);
	
	/* return the number of items added to the list */
	return items;
}	

static int animdata_filter_dopesheet_scene (bAnimContext *ac, ListBase *anim_data, bDopeSheet *ads, Scene *sce, int filter_mode)
{
	World *wo= sce->world;
	bNodeTree *ntree= sce->nodetree;
	AnimData *adt= NULL;
	bAnimListElem *ale;
	int items = 0;
	
	/* add scene as a channel first (even if we aren't showing scenes we still need to show the scene's sub-data */
	if ((filter_mode & (ANIMFILTER_CURVESONLY|ANIMFILTER_NLATRACKS)) == 0) {
		/* check if filtering by selection */
		if (ANIMCHANNEL_SELOK( (sce->flag & SCE_DS_SELECTED) )) {
			ale= make_new_animlistelem(sce, ANIMTYPE_SCENE, NULL, ANIMTYPE_NONE, NULL);
			if (ale) {
				BLI_addtail(anim_data, ale);
				items++;
			}
		}
	}
	
	/* if collapsed, don't go any further (unless adding keyframes only) */
	if ( (EXPANDED_SCEC(sce) == 0) && !(filter_mode & (ANIMFILTER_CURVESONLY|ANIMFILTER_NLATRACKS)) )
		return items;
		
	/* Action, Drivers, or NLA for Scene */
	if ((ads->filterflag & ADS_FILTER_NOSCE) == 0) {
		adt= sce->adt;
		ANIMDATA_FILTER_CASES(sce,
			{ /* AnimData blocks - do nothing... */ },
			{ /* nla */
				/* add NLA tracks */
				items += animdata_filter_nla(ac, anim_data, ads, adt, filter_mode, sce, ANIMTYPE_SCENE, (ID *)sce);
			},
			{ /* drivers */
				/* include drivers-expand widget? */
				if ((filter_mode & ANIMFILTER_CHANNELS) && !(filter_mode & ANIMFILTER_CURVESONLY)) {
					ale= make_new_animlistelem(adt->action, ANIMTYPE_FILLDRIVERS, sce, ANIMTYPE_SCENE, (ID *)sce);
					if (ale) {
						BLI_addtail(anim_data, ale);
						items++;
					}
				}
				
				/* add F-Curve channels (drivers are F-Curves) */
				if (EXPANDED_DRVD(adt) || !(filter_mode & ANIMFILTER_CHANNELS)) {
					items += animdata_filter_fcurves(anim_data, ads, adt->drivers.first, NULL, sce, ANIMTYPE_SCENE, filter_mode, (ID *)sce);
				}
			},
			{ /* action */
				/* include action-expand widget? */
				if ((filter_mode & ANIMFILTER_CHANNELS) && !(filter_mode & ANIMFILTER_CURVESONLY)) {
					ale= make_new_animlistelem(adt->action, ANIMTYPE_FILLACTD, sce, ANIMTYPE_SCENE, (ID *)sce);
					if (ale) {
						BLI_addtail(anim_data, ale);
						items++;
					}
				}
				
				/* add F-Curve channels? */
				if (EXPANDED_ACTC(adt->action) || !(filter_mode & ANIMFILTER_CHANNELS)) {
					items += animdata_filter_action(ac, anim_data, ads, adt->action, filter_mode, sce, ANIMTYPE_SCENE, (ID *)sce); 
				}
			}
		)
	}
	
	/* world */
	if ((wo && wo->adt) && !(ads->filterflag & ADS_FILTER_NOWOR)) {
		/* Action, Drivers, or NLA for World */
		adt= wo->adt;
		ANIMDATA_FILTER_CASES(wo,
			{ /* AnimData blocks - do nothing... */ },
			{ /* nla */
				/* add NLA tracks */
				items += animdata_filter_nla(ac, anim_data, ads, adt, filter_mode, wo, ANIMTYPE_DSWOR, (ID *)wo);
			},
			{ /* drivers */
				/* include world-expand widget? */
				if ((filter_mode & ANIMFILTER_CHANNELS) && !(filter_mode & ANIMFILTER_CURVESONLY)) {
					ale= make_new_animlistelem(wo, ANIMTYPE_DSWOR, sce, ANIMTYPE_SCENE, (ID *)wo);
					if (ale) {
						BLI_addtail(anim_data, ale);
						items++;
					}
				}
				
				/* add F-Curve channels (drivers are F-Curves) */
				if (FILTER_WOR_SCED(wo)/*EXPANDED_DRVD(adt)*/ || !(filter_mode & ANIMFILTER_CHANNELS)) {
					// XXX owner info is messed up now...
					items += animdata_filter_fcurves(anim_data, ads, adt->drivers.first, NULL, wo, ANIMTYPE_DSWOR, filter_mode, (ID *)wo);
				}
			},
			{ /* action */
				/* include world-expand widget? */
				if ((filter_mode & ANIMFILTER_CHANNELS) && !(filter_mode & ANIMFILTER_CURVESONLY)) {
					ale= make_new_animlistelem(wo, ANIMTYPE_DSWOR, sce, ANIMTYPE_SCENE, (ID *)sce);
					if (ale) {
						BLI_addtail(anim_data, ale);
						items++;
					}
				}
				
				/* add channels */
				if (FILTER_WOR_SCED(wo) || (filter_mode & ANIMFILTER_CURVESONLY)) {
					items += animdata_filter_action(ac, anim_data, ads, adt->action, filter_mode, wo, ANIMTYPE_DSWOR, (ID *)wo); 
				}
			}
		)
		
		/* if expanded, check world textures too */
		if (FILTER_WOR_SCED(wo) || (filter_mode & ANIMFILTER_CURVESONLY)) {
			/* textures for world */
			if (!(ads->filterflag & ADS_FILTER_NOTEX))
				items += animdata_filter_dopesheet_texs(ac, anim_data, ads, (ID *)wo, filter_mode);
		}
	}
	/* nodetree */
	if ((ntree && ntree->adt) && !(ads->filterflag & ADS_FILTER_NONTREE)) {
		/* Action, Drivers, or NLA for Nodetree */
		adt= ntree->adt;
		ANIMDATA_FILTER_CASES(ntree,
			{ /* AnimData blocks - do nothing... */ },
			{ /* nla */
				/* add NLA tracks */
				items += animdata_filter_nla(ac, anim_data, ads, adt, filter_mode, ntree, ANIMTYPE_DSNTREE, (ID *)ntree);
			},
			{ /* drivers */
				/* include nodetree-expand widget? */
				if ((filter_mode & ANIMFILTER_CHANNELS) && !(filter_mode & ANIMFILTER_CURVESONLY)) {
					ale= make_new_animlistelem(ntree, ANIMTYPE_DSNTREE, sce, ANIMTYPE_SCENE, (ID *)ntree);
					if (ale) {
						BLI_addtail(anim_data, ale);
						items++;
					}
				}
				
				/* add F-Curve channels (drivers are F-Curves) */
				if (FILTER_NTREE_SCED(ntree)/*EXPANDED_DRVD(adt)*/ || !(filter_mode & ANIMFILTER_CHANNELS)) {
					// XXX owner info is messed up now...
					items += animdata_filter_fcurves(anim_data, ads, adt->drivers.first, NULL, ntree, ANIMTYPE_DSNTREE, filter_mode, (ID *)ntree);
				}
			},
			{ /* action */
				/* include nodetree-expand widget? */
				if ((filter_mode & ANIMFILTER_CHANNELS) && !(filter_mode & ANIMFILTER_CURVESONLY)) {
					ale= make_new_animlistelem(ntree, ANIMTYPE_DSNTREE, sce, ANIMTYPE_SCENE, (ID *)sce);
					if (ale) {
						BLI_addtail(anim_data, ale);
						items++;
					}
				}
				
				/* add channels */
				if (FILTER_NTREE_SCED(ntree) || (filter_mode & ANIMFILTER_CURVESONLY)) {
					items += animdata_filter_action(ac, anim_data, ads, adt->action, filter_mode, ntree, ANIMTYPE_DSNTREE, (ID *)ntree); 
				}
			}
		)
	}

	
	// TODO: scene compositing nodes (these aren't standard node-trees)
	
	/* return the number of items added to the list */
	return items;
}

// TODO: implement pinning... (if and when pinning is done, what we need to do is to provide freeing mechanisms - to protect against data that was deleted)
static int animdata_filter_dopesheet (bAnimContext *ac, ListBase *anim_data, bDopeSheet *ads, int filter_mode)
{
	Scene *sce= (Scene *)ads->source;
	Base *base;
	bAnimListElem *ale;
	int items = 0;
	
	/* check that we do indeed have a scene */
	if ((ads->source == NULL) || (GS(ads->source->name)!=ID_SCE)) {
		printf("DopeSheet Error: Not scene!\n");
		if (G.f & G_DEBUG)
			printf("\tPointer = %p, Name = '%s' \n", (void *)ads->source, (ads->source)?ads->source->name:NULL);
		return 0;
	}
	
	/* augment the filter-flags with settings based on the dopesheet filterflags 
	 * so that some temp settings can get added automagically...
	 */
	if (ads->filterflag & ADS_FILTER_SELEDIT) {
		/* only selected F-Curves should get their keyframes considered for editability */
		filter_mode |= ANIMFILTER_SELEDIT;
	}
	
	/* scene-linked animation */
	// TODO: sequencer, composite nodes - are we to include those here too?
	{
		short sceOk= 0, worOk= 0, nodeOk=0;
		
		/* check filtering-flags if ok */
		ANIMDATA_FILTER_CASES(sce, 
			{
				/* for the special AnimData blocks only case, we only need to add
				 * the block if it is valid... then other cases just get skipped (hence ok=0)
				 */
				ANIMDATA_ADD_ANIMDATA(sce);
				sceOk=0;
			},
			sceOk= !(ads->filterflag & ADS_FILTER_NOSCE);, 
			sceOk= !(ads->filterflag & ADS_FILTER_NOSCE);, 
			sceOk= !(ads->filterflag & ADS_FILTER_NOSCE);)
		if (sce->world) {
			ANIMDATA_FILTER_CASES(sce->world, 
				{
					/* for the special AnimData blocks only case, we only need to add
					 * the block if it is valid... then other cases just get skipped (hence ok=0)
					 */
					ANIMDATA_ADD_ANIMDATA(sce->world);
					worOk=0;
				},
				worOk= !(ads->filterflag & ADS_FILTER_NOWOR);, 
				worOk= !(ads->filterflag & ADS_FILTER_NOWOR);, 
				worOk= !(ads->filterflag & ADS_FILTER_NOWOR);)
		}
		if (sce->nodetree) {
			ANIMDATA_FILTER_CASES(sce->nodetree, 
				{
					/* for the special AnimData blocks only case, we only need to add
					 * the block if it is valid... then other cases just get skipped (hence ok=0)
					 */
					ANIMDATA_ADD_ANIMDATA(sce->nodetree);
					nodeOk=0;
				},
				nodeOk= !(ads->filterflag & ADS_FILTER_NONTREE);, 
				nodeOk= !(ads->filterflag & ADS_FILTER_NONTREE);, 
				nodeOk= !(ads->filterflag & ADS_FILTER_NONTREE);)
		}
		
		/* if only F-Curves with visible flags set can be shown, check that 
		 * datablocks haven't been set to invisible 
		 */
		if (filter_mode & ANIMFILTER_CURVEVISIBLE) {
			if ((sce->adt) && (sce->adt->flag & ADT_CURVES_NOT_VISIBLE))
				sceOk= worOk= nodeOk= 0;
		}
		
		/* check if not all bad (i.e. so there is something to show) */
		if ( !(!sceOk && !worOk && !nodeOk) ) {
			/* add scene data to the list of filtered channels */
			items += animdata_filter_dopesheet_scene(ac, anim_data, ads, sce, filter_mode);
		}
	}
	
	
	/* loop over all bases in the scene */
	for (base= sce->base.first; base; base= base->next) {
		/* check if there's an object (all the relevant checks are done in the ob-function) */
		if (base->object) {
			Object *ob= base->object;
			Key *key= ob_get_key(ob);
			short actOk=1, keyOk=1, dataOk=1, matOk=1, partOk=1;
			
			/* firstly, check if object can be included, by the following factors:
			 *	- if only visible, must check for layer and also viewport visibility
			 *		--> while tools may demand only visible, user setting takes priority
			 *			as user option controls whether sets of channels get included while
			 *			tool-flag takes into account collapsed/open channels too
			 *	- if only selected, must check if object is selected 
			 *	- there must be animation data to edit
			 */
			// TODO: if cache is implemented, just check name here, and then 
			if ((filter_mode & ANIMFILTER_VISIBLE) && !(ads->filterflag & ADS_FILTER_INCL_HIDDEN)) {
				/* layer visibility - we check both object and base, since these may not be in sync yet */
				if ((sce->lay & (ob->lay|base->lay))==0) continue;
				
				/* outliner restrict-flag */
				if (ob->restrictflag & OB_RESTRICT_VIEW) continue;
			}
			
			/* if only F-Curves with visible flags set can be shown, check that 
			 * datablock hasn't been set to invisible 
			 */
			if (filter_mode & ANIMFILTER_CURVEVISIBLE) {
				if ((ob->adt) && (ob->adt->flag & ADT_CURVES_NOT_VISIBLE))
					continue;
			}
			
			/* additionally, dopesheet filtering also affects what objects to consider */
			{
				/* check selection and object type filters */
				if ( (ads->filterflag & ADS_FILTER_ONLYSEL) && !((base->flag & SELECT) /*|| (base == sce->basact)*/) )  {
					/* only selected should be shown */
					continue;
				}
				
				/* check if object belongs to the filtering group if option to filter 
				 * objects by the grouped status is on
				 *	- used to ease the process of doing multiple-character choreographies
				 */
				if (ads->filterflag & ADS_FILTER_ONLYOBGROUP) {
					if (object_in_group(ob, ads->filter_grp) == 0)
						continue;
				}
				
				/* check filters for datatypes */
					/* object */
				actOk= 0;
				if (!(ads->filterflag & ADS_FILTER_NOOBJ)) {
					ANIMDATA_FILTER_CASES(ob, 
						{
							/* for the special AnimData blocks only case, we only need to add
							 * the block if it is valid... then other cases just get skipped (hence ok=0)
							 */
							ANIMDATA_ADD_ANIMDATA(ob);
							actOk=0;
						},
						actOk= 1;, 
						actOk= 1;, 
						actOk= 1;)
				}
				
				keyOk= 0;
				if ((key) && !(ads->filterflag & ADS_FILTER_NOSHAPEKEYS)) {
					/* shapekeys */
					ANIMDATA_FILTER_CASES(key, 
						{
							/* for the special AnimData blocks only case, we only need to add
							 * the block if it is valid... then other cases just get skipped (hence ok=0)
							 */
							ANIMDATA_ADD_ANIMDATA(key);
							keyOk=0;
						},
						keyOk= 1;, 
						keyOk= 1;, 
						keyOk= 1;)
				}
				
				/* materials - only for geometric types */
				matOk= 0; /* by default, not ok... */
				if ( !(ads->filterflag & ADS_FILTER_NOMAT) && (ob->totcol) && 
					 ELEM5(ob->type, OB_MESH, OB_CURVE, OB_SURF, OB_FONT, OB_MBALL) ) 
				{
					int a;
					
					/* firstly check that we actuallly have some materials */
					for (a=1; a <= ob->totcol; a++) {
						Material *ma= give_current_material(ob, a);
						
						if (ma) {
							/* if material has relevant animation data, break */
							ANIMDATA_FILTER_CASES(ma, 
								{
									/* for the special AnimData blocks only case, we only need to add
									 * the block if it is valid... then other cases just get skipped (hence ok=0)
									 */
									ANIMDATA_ADD_ANIMDATA(ma);
									matOk=0;
								},
								matOk= 1;, 
								matOk= 1;, 
								matOk= 1;)
								
							if (matOk) 
								break;
							
							/* textures? */
							// TODO: make this a macro that is used in the other checks too
							// NOTE: this has little use on its own, since the actual filtering still ignores if no anim on the data
							if (!(ads->filterflag & ADS_FILTER_NOTEX)) {
								int mtInd;
								
								for (mtInd= 0; mtInd < MAX_MTEX; mtInd++) {
									MTex *mtex= ma->mtex[mtInd];
									
									if (mtex && mtex->tex) {
										/* if texture has relevant animation data, break */
										ANIMDATA_FILTER_CASES(mtex->tex, 
											{
												/* for the special AnimData blocks only case, we only need to add
												 * the block if it is valid... then other cases just get skipped (hence ok=0)
												 */
												ANIMDATA_ADD_ANIMDATA(mtex->tex);
												matOk=0;
											},
											matOk= 1;, 
											matOk= 1;, 
											matOk= 1;)
											
										if (matOk) 
											break;
									}
								}
							}
							
						}
					}
				}
				
				/* data */
				switch (ob->type) {
					case OB_CAMERA: /* ------- Camera ------------ */
					{
						Camera *ca= (Camera *)ob->data;
						dataOk= 0;
						ANIMDATA_FILTER_CASES(ca, 
							if ((ads->filterflag & ADS_FILTER_NOCAM)==0) {
								/* for the special AnimData blocks only case, we only need to add
								 * the block if it is valid... then other cases just get skipped (hence ok=0)
								 */
								ANIMDATA_ADD_ANIMDATA(ca);
								dataOk=0;
							},
							dataOk= !(ads->filterflag & ADS_FILTER_NOCAM);, 
							dataOk= !(ads->filterflag & ADS_FILTER_NOCAM);, 
							dataOk= !(ads->filterflag & ADS_FILTER_NOCAM);)
					}
						break;
					case OB_LAMP: /* ---------- Lamp ----------- */
					{
						Lamp *la= (Lamp *)ob->data;
						dataOk= 0;
						ANIMDATA_FILTER_CASES(la, 
							if ((ads->filterflag & ADS_FILTER_NOLAM)==0) {
								/* for the special AnimData blocks only case, we only need to add
								 * the block if it is valid... then other cases just get skipped (hence ok=0)
								 */
								ANIMDATA_ADD_ANIMDATA(la);
								dataOk=0;
							},
							dataOk= !(ads->filterflag & ADS_FILTER_NOLAM);, 
							dataOk= !(ads->filterflag & ADS_FILTER_NOLAM);, 
							dataOk= !(ads->filterflag & ADS_FILTER_NOLAM);)
					}
						break;
					case OB_CURVE: /* ------- Curve ---------- */
					case OB_SURF: /* ------- Nurbs Surface ---------- */
					case OB_FONT: /* ------- Text Curve ---------- */
					{
						Curve *cu= (Curve *)ob->data;
						dataOk= 0;
						ANIMDATA_FILTER_CASES(cu, 
							if ((ads->filterflag & ADS_FILTER_NOCUR)==0) {
								/* for the special AnimData blocks only case, we only need to add
								 * the block if it is valid... then other cases just get skipped (hence ok=0)
								 */
								ANIMDATA_ADD_ANIMDATA(cu);
								dataOk=0;
							},
							dataOk= !(ads->filterflag & ADS_FILTER_NOCUR);, 
							dataOk= !(ads->filterflag & ADS_FILTER_NOCUR);, 
							dataOk= !(ads->filterflag & ADS_FILTER_NOCUR);)
					}
						break;
					case OB_MBALL: /* ------- MetaBall ---------- */
					{
						MetaBall *mb= (MetaBall *)ob->data;
						dataOk= 0;
						ANIMDATA_FILTER_CASES(mb, 
							if ((ads->filterflag & ADS_FILTER_NOMBA)==0) {
								/* for the special AnimData blocks only case, we only need to add
								 * the block if it is valid... then other cases just get skipped (hence ok=0)
								 */
								ANIMDATA_ADD_ANIMDATA(mb);
								dataOk=0;
							},
							dataOk= !(ads->filterflag & ADS_FILTER_NOMBA);, 
							dataOk= !(ads->filterflag & ADS_FILTER_NOMBA);, 
							dataOk= !(ads->filterflag & ADS_FILTER_NOMBA);)
					}
						break;
					case OB_ARMATURE: /* ------- Armature ---------- */
					{
						bArmature *arm= (bArmature *)ob->data;
						dataOk= 0;
						ANIMDATA_FILTER_CASES(arm, 
							if ((ads->filterflag & ADS_FILTER_NOARM)==0) {
								/* for the special AnimData blocks only case, we only need to add
								 * the block if it is valid... then other cases just get skipped (hence ok=0)
								 */
								ANIMDATA_ADD_ANIMDATA(arm);
								dataOk=0;
							},
							dataOk= !(ads->filterflag & ADS_FILTER_NOARM);, 
							dataOk= !(ads->filterflag & ADS_FILTER_NOARM);, 
							dataOk= !(ads->filterflag & ADS_FILTER_NOARM);)
					}
						break;
					case OB_MESH: /* ------- Mesh ---------- */
					{
						Mesh *me= (Mesh *)ob->data;
						dataOk= 0;
						ANIMDATA_FILTER_CASES(me, 
							if ((ads->filterflag & ADS_FILTER_NOMESH)==0) {
								/* for the special AnimData blocks only case, we only need to add
								 * the block if it is valid... then other cases just get skipped (hence ok=0)
								 */
								ANIMDATA_ADD_ANIMDATA(me);
								dataOk=0;
							},
							dataOk= !(ads->filterflag & ADS_FILTER_NOMESH);, 
							dataOk= !(ads->filterflag & ADS_FILTER_NOMESH);, 
							dataOk= !(ads->filterflag & ADS_FILTER_NOMESH);)
					}
						break;
					case OB_LATTICE: /* ------- Lattice ---------- */
					{
						Lattice *lt= (Lattice *)ob->data;
						dataOk= 0;
						ANIMDATA_FILTER_CASES(lt, 
							if ((ads->filterflag & ADS_FILTER_NOLAT)==0) {
								/* for the special AnimData blocks only case, we only need to add
								 * the block if it is valid... then other cases just get skipped (hence ok=0)
								 */
								ANIMDATA_ADD_ANIMDATA(lt);
								dataOk=0;
							},
							dataOk= !(ads->filterflag & ADS_FILTER_NOLAT);, 
							dataOk= !(ads->filterflag & ADS_FILTER_NOLAT);, 
							dataOk= !(ads->filterflag & ADS_FILTER_NOLAT);)
					}
						break;
					default: /* --- other --- */
						dataOk= 0;
						break;
				}
				
				/* particles */
				partOk = 0;
				if (!(ads->filterflag & ADS_FILTER_NOPART) && ob->particlesystem.first) {
					ParticleSystem *psys = ob->particlesystem.first;
					for(; psys; psys=psys->next) {
						if (psys->part) {
							/* if particlesettings has relevant animation data, break */
							ANIMDATA_FILTER_CASES(psys->part, 
								{
									/* for the special AnimData blocks only case, we only need to add
									 * the block if it is valid... then other cases just get skipped (hence ok=0)
									 */
									ANIMDATA_ADD_ANIMDATA(psys->part);
									partOk=0;
								},
								partOk= 1;, 
								partOk= 1;, 
								partOk= 1;)
						}
							
						if (partOk) 
							break;
					}
				}
				
				/* check if all bad (i.e. nothing to show) */
				if (!actOk && !keyOk && !dataOk && !matOk && !partOk)
					continue;
			}
			
			/* since we're still here, this object should be usable */
			items += animdata_filter_dopesheet_ob(ac, anim_data, ads, base, filter_mode);
		}
	}
	
	/* return the number of items in the list */
	return items;
}

/* Summary track for DopeSheet/Action Editor 
 * 	- return code is whether the summary lets the other channels get drawn
 */
static short animdata_filter_dopesheet_summary (bAnimContext *ac, ListBase *anim_data, int filter_mode, int *items)
{
	bDopeSheet *ads = NULL;
	
	/* get the DopeSheet information to use 
	 *	- we should only need to deal with the DopeSheet/Action Editor, 
	 *	  since all the other Animation Editors won't have this concept
	 *	  being applicable.
	 */
	if ((ac && ac->sa) && (ac->sa->spacetype == SPACE_ACTION)) {
		SpaceAction *saction= (SpaceAction *)ac->sa->spacedata.first;
		ads= &saction->ads;
	}
	else {
		/* invalid space type - skip this summary channels */
		return 1;
	}
	
	/* dopesheet summary 
	 *	- only for drawing and/or selecting keyframes in channels, but not for real editing 
	 *	- only useful for DopeSheet/Action/etc. editors where it is actually useful
	 */
	// TODO: we should really check if some other prohibited filters are also active, but that can be for later
	if ((filter_mode & ANIMFILTER_CHANNELS) && (ads->filterflag & ADS_FILTER_SUMMARY)) {
		bAnimListElem *ale= make_new_animlistelem(ac, ANIMTYPE_SUMMARY, NULL, ANIMTYPE_NONE, NULL);
		if (ale) {
			BLI_addtail(anim_data, ale);
			(*items)++;
		}
		
		/* if summary is collapsed, don't show other channels beneath this 
		 *	- this check is put inside the summary check so that it doesn't interfere with normal operation
		 */ 
		if (ads->flag & ADS_FLAG_SUMMARY_COLLAPSED)
			return 0;
	}
	
	/* the other channels beneath this can be shown */
	return 1;
}  

/* ----------- Cleanup API --------------- */

/* Remove entries with invalid types in animation channel list */
static int animdata_filter_remove_invalid (ListBase *anim_data)
{
	bAnimListElem *ale, *next;
	int items = 0;
	
	/* only keep entries with valid types */
	for (ale= anim_data->first; ale; ale= next) {
		next= ale->next;
		
		if (ale->type == ANIMTYPE_NONE)
			BLI_freelinkN(anim_data, ale);
		else
			items++;
	}
	
	return items;
}

/* Remove duplicate entries in animation channel list */
static int animdata_filter_remove_duplis (ListBase *anim_data)
{
	bAnimListElem *ale, *next;
	GHash *gh;
	int items = 0;
	
	/* build new hashtable to efficiently store and retrieve which entries have been 
	 * encountered already while searching
	 */
	gh= BLI_ghash_new(BLI_ghashutil_ptrhash, BLI_ghashutil_ptrcmp, "animdata_filter_duplis_remove gh");
	
	/* loop through items, removing them from the list if a similar item occurs already */
	for (ale = anim_data->first; ale; ale = next) {
		next = ale->next;
		
		/* check if hash has any record of an entry like this 
		 *	- just use ale->data for now, though it would be nicer to involve 
		 *	  ale->type in combination too to capture corner cases (where same data performs differently)
		 */
		if (BLI_ghash_haskey(gh, ale->data) == 0) {
			/* this entry is 'unique' and can be kept */
			BLI_ghash_insert(gh, ale->data, NULL);
			items++;
		}
		else {
			/* this entry isn't needed anymore */
			BLI_freelinkN(anim_data, ale);
		}
	}
	
	/* free the hash... */
	BLI_ghash_free(gh, NULL, NULL);
	
	/* return the number of items still in the list */
	return items;
}

/* ----------- Public API --------------- */

/* This function filters the active data source to leave only animation channels suitable for
 * usage by the caller. It will return the length of the list 
 * 
 * 	*anim_data: is a pointer to a ListBase, to which the filtered animation channels
 *		will be placed for use.
 *	filter_mode: how should the data be filtered - bitmapping accessed flags
 */
int ANIM_animdata_filter (bAnimContext *ac, ListBase *anim_data, int filter_mode, void *data, short datatype)
{
	int items = 0;
	
	/* only filter data if there's somewhere to put it */
	if (data && anim_data) {
		Object *obact= (ac) ? ac->obact : NULL;
		
		/* firstly filter the data */
		switch (datatype) {
			case ANIMCONT_ACTION:	/* 'Action Editor' */
			{
				SpaceAction *saction = (SpaceAction *)ac->sa->spacedata.first;
				bDopeSheet *ads = (saction)? &saction->ads : NULL;
				
				/* the check for the DopeSheet summary is included here since the summary works here too */
				if (animdata_filter_dopesheet_summary(ac, anim_data, filter_mode, &items))
					items += animdata_filter_action(ac, anim_data, ads, data, filter_mode, NULL, ANIMTYPE_NONE, (ID *)obact);
			}
				break;
				
			case ANIMCONT_SHAPEKEY: /* 'ShapeKey Editor' */
			{
				/* the check for the DopeSheet summary is included here since the summary works here too */
				if (animdata_filter_dopesheet_summary(ac, anim_data, filter_mode, &items))
					items= animdata_filter_shapekey(ac, anim_data, data, filter_mode);
			}
				break;
				
			case ANIMCONT_GPENCIL:
			{
				items= animdata_filter_gpencil(anim_data, data, filter_mode);
			}
				break;
				
			case ANIMCONT_DOPESHEET: /* 'DopeSheet Editor' */
			{
				/* the DopeSheet editor is the primary place where the DopeSheet summaries are useful */
				if (animdata_filter_dopesheet_summary(ac, anim_data, filter_mode, &items))
					items += animdata_filter_dopesheet(ac, anim_data, data, filter_mode);
			}
				break;
				
			case ANIMCONT_FCURVES: /* Graph Editor -> FCurves/Animation Editing */
			case ANIMCONT_DRIVERS: /* Graph Editor -> Drivers Editing */
			case ANIMCONT_NLA: /* NLA Editor */
			{
				/* all of these editors use the basic DopeSheet data for filtering options, but don't have all the same features */
				items = animdata_filter_dopesheet(ac, anim_data, data, filter_mode);
			}
				break;
		}
			
		/* remove any 'weedy' entries */
		items = animdata_filter_remove_invalid(anim_data);
		
		/* remove duplicates (if required) */
		if (filter_mode & ANIMFILTER_NODUPLIS)
			items = animdata_filter_remove_duplis(anim_data);
	}
	
	/* return the number of items in the list */
	return items;
}

/* ************************************************************ */
