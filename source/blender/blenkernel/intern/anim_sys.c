/* Testing code for new animation system in 2.5 
 * Copyright 2009, Joshua Leung
 */

#include <stdio.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_dynstr.h"

#include "BKE_animsys.h"
#include "BKE_action.h"
#include "BKE_fcurve.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_utildefines.h"

#include "RNA_access.h"
#include "RNA_types.h"

#include "DNA_anim_types.h"

/* ***************************************** */
/* AnimData API */

/* Getter/Setter -------------------------------------------- */

/* Internal utility to check if ID can have AnimData */
static short id_has_animdata (ID *id)
{
	/* sanity check */
	if (id == NULL)
		return 0;
		
	/* Only some ID-blocks have this info for now */
	// TODO: finish adding this for the other blocktypes
	switch (GS(id->name)) {
			/* has AnimData */
		case ID_OB:
		case ID_CU:
		case ID_KE:
		case ID_MA: case ID_TE: case ID_NT:
		case ID_LA: case ID_CA: case ID_WO:
		case ID_SCE:
		{
			return 1;
		}
		
			/* no AnimData */
		default:
			return 0;
	}
}


/* Get AnimData from the given ID-block. In order for this to work, we assume that 
 * the AnimData pointer is stored immediately after the given ID-block in the struct,
 * as per IdAdtTemplate.
 */
AnimData *BKE_animdata_from_id (ID *id)
{
	/* only some ID-blocks have this info for now, so we cast the 
	 * types that do to be of type IdAdtTemplate, and extract the
	 * AnimData that way
	 */
	if (id_has_animdata(id)) {
		IdAdtTemplate *iat= (IdAdtTemplate *)id;
		return iat->adt;
	}
	else
		return NULL;
}

/* Add AnimData to the given ID-block. In order for this to work, we assume that 
 * the AnimData pointer is stored immediately after the given ID-block in the struct,
 * as per IdAdtTemplate. Also note that 
 */
AnimData *BKE_id_add_animdata (ID *id)
{
	/* Only some ID-blocks have this info for now, so we cast the 
	 * types that do to be of type IdAdtTemplate, and add the AnimData
	 * to it using the template
	 */
	if (id_has_animdata(id)) {
		IdAdtTemplate *iat= (IdAdtTemplate *)id;
		
		/* check if there's already AnimData, in which case, don't add */
		if (iat->adt == NULL)
			iat->adt= MEM_callocN(sizeof(AnimData), "AnimData");
		
		return iat->adt;
	}
	else 
		return NULL;
}

/* Freeing -------------------------------------------- */

/* Free AnimData used by the nominated ID-block, and clear ID-block's AnimData pointer */
void BKE_free_animdata (ID *id)
{
	/* Only some ID-blocks have this info for now, so we cast the 
	 * types that do to be of type IdAdtTemplate
	 */
	if (id_has_animdata(id)) {
		IdAdtTemplate *iat= (IdAdtTemplate *)id;
		AnimData *adt= iat->adt;
		
		/* check if there's any AnimData to start with */
		if (adt) {
			/* unlink action (don't free, as it's in its own list) */
			if (adt->action)
				adt->action->id.us--;
				
			/* free drivers - stored as a list of F-Curves */
			free_fcurves(&adt->drivers);
			
			/* free overrides */
			// TODO...
			
			/* free animdata now */
			MEM_freeN(adt);
			iat->adt= NULL;
		}
	}
}

/* Freeing -------------------------------------------- */

/* Make a copy of the given AnimData - to be used when copying datablocks */
AnimData *BKE_copy_animdata (AnimData *adt)
{
	AnimData *dadt;
	
	/* sanity check before duplicating struct */
	if (adt == NULL)
		return NULL;
	dadt= MEM_dupallocN(adt);
	
	/* make a copy of action - at worst, user has to delete copies... */
	// XXX review this... it might not be optimal behaviour yet...
	//id_us_plus((ID *)dadt->action);
	dadt->action= copy_action(adt->action);
	
	/* duplicate NLA data */
	// XXX todo...
	
	/* duplicate drivers (F-Curves) */
	copy_fcurves(&dadt->drivers, &adt->drivers);
	
	/* don't copy overrides */
	dadt->overrides.first= dadt->overrides.last= NULL;
	
	/* return */
	return dadt;
}


/* ***************************************** */
/* Evaluation Data-Setting Backend */

/* Retrieve string to act as RNA-path, adjusted using mapping-table if provided 
 * It returns whether the string needs to be freed (i.e. if it was a temp remapped one)
 * // FIXME: maybe it would be faster if we didn't have to alloc/free strings like this all the time, but for now it's safer
 *
 *	- remap: remapping table to use
 *	- path: original path string (as stored in F-Curve data)
 *	- dst: destination string to write data to
 */
short animsys_remap_path (AnimMapper *remap, char *path, char **dst)
{
	/* is there a valid remapping table to use? */
	if (remap) {
		/* find a matching entry... to use to remap */
		// ...TODO...
	}
	
	/* nothing suitable found, so just set dst to look at path (i.e. no alloc/free needed) */
	*dst= path;
	return 0;
}


/* Write the given value to a setting using RNA, and return success */
static short animsys_write_rna_setting (PointerRNA *ptr, char *path, int array_index, float value)
{
	PropertyRNA *prop;
	PointerRNA new_ptr;
	
	/* get property to write to */
	if (RNA_path_resolve(ptr, path, &new_ptr, &prop)) 
	{
		/* set value - only for animatable numerical values */
		if (RNA_property_animateable(&new_ptr, prop)) 
		{
			switch (RNA_property_type(&new_ptr, prop)) 
			{
				case PROP_BOOLEAN:
					if (RNA_property_array_length(&new_ptr, prop))
						RNA_property_boolean_set_array(&new_ptr, prop, array_index, (int)value);
					else
						RNA_property_boolean_set(&new_ptr, prop, (int)value);
					break;
				case PROP_INT:
					if (RNA_property_array_length(&new_ptr, prop))
						RNA_property_int_set_array(&new_ptr, prop, array_index, (int)value);
					else
						RNA_property_int_set(&new_ptr, prop, (int)value);
					break;
				case PROP_FLOAT:
					if (RNA_property_array_length(&new_ptr, prop))
						RNA_property_float_set_array(&new_ptr, prop, array_index, value);
					else
						RNA_property_float_set(&new_ptr, prop, value);
					break;
				case PROP_ENUM:
					RNA_property_enum_set(&new_ptr, prop, (int)value);
					break;
				default:
					break;
			}
		}
		
		/* successful */
		// XXX should the unhandled case also be successful?
		return 1;
	}
	else {
		/* failed to get path */
		// XXX don't tag as failed yet though, as there are some legit situations (Action Constraint) 
		// where some channels will not exist, but shouldn't lock up Action
		if (G.f & G_DEBUG) {
			printf("Animato: Invalid path. ID = '%s',  '%s [%d]' \n", 
				(ptr && ptr->id.data) ? (((ID *)ptr->id.data)->name+2) : "<No ID>", 
				path, array_index);
		}
		return 0;
	}
}

/* Simple replacement based data-setting of the FCurve using RNA */
static void animsys_execute_fcurve (PointerRNA *ptr, AnimMapper *remap, FCurve *fcu)
{
	char *path = NULL;
	short free_path=0;
	
	/* get path, remapped as appropriate to work in its new environment */
	free_path= animsys_remap_path(remap, fcu->rna_path, &path);
	
	/* write value to setting */
	if (path)
		animsys_write_rna_setting(ptr, path, fcu->array_index, fcu->curval);
	
	/* free temp path-info */
	if (free_path)
		MEM_freeN(path);
}

/* Evaluate all the F-Curves in the given list 
 * This performs a set of standard checks. If extra checks are required, separate code should be used
 */
static void animsys_evaluate_fcurves (PointerRNA *ptr, ListBase *list, AnimMapper *remap, float ctime)
{
	FCurve *fcu;
	
	/* calculate then execute each curve */
	for (fcu= list->first; fcu; fcu= fcu->next) 
	{
		/* check if this curve should be skipped */
		if ((fcu->flag & (FCURVE_MUTED|FCURVE_DISABLED)) == 0) 
		{
			calculate_fcurve(fcu, ctime);
			animsys_execute_fcurve(ptr, remap, fcu); 
		}
	}
}

/* ***************************************** */
/* Driver Evaluation */

/* Evaluate Drivers */
static void animsys_evaluate_drivers (PointerRNA *ptr, AnimData *adt, float ctime)
{
	FCurve *fcu;
	
	/* drivers are stored as F-Curves, but we cannot use the standard code, as we need to check if
	 * the depsgraph requested that this driver be evaluated...
	 */
	for (fcu= adt->drivers.first; fcu; fcu= fcu->next) 
	{
		ChannelDriver *driver= fcu->driver;
		
		/* check if this driver's curve should be skipped */
		// FIXME: maybe we shouldn't check for muted, though that would make things more confusing, as there's already too many ways to disable?
		if ((fcu->flag & (FCURVE_MUTED|FCURVE_DISABLED)) == 0) 
		{
			/* check if driver itself is tagged for recalculation */
			if ((driver) /*&& (driver->flag & DRIVER_FLAG_RECALC)*/) {	// XXX driver recalc flag is not set yet by depsgraph!
				/* evaluate this using values set already in other places */
				// NOTE: for 'layering' option later on, we should check if we should remove old value before adding new to only be done when drivers only changed
				calculate_fcurve(fcu, ctime);
				animsys_execute_fcurve(ptr, NULL, fcu);
				
				/* clear recalc flag */
				driver->flag &= ~DRIVER_FLAG_RECALC;
			}
		}
	}
}

/* ***************************************** */
/* Actions Evaluation */

/* Evaluate Action (F-Curve Bag) */
static void animsys_evaluate_action (PointerRNA *ptr, bAction *act, AnimMapper *remap, float ctime)
{
	/* check if mapper is appropriate for use here (we set to NULL if it's inappropriate) */
	if (act == NULL) return;
	if ((remap) && (remap->target != act)) remap= NULL;
	
	/* calculate then execute each curve */
	animsys_evaluate_fcurves(ptr, &act->curves, remap, ctime);
}

/* ***************************************** */
/* NLA System - Evaluation */

/* used for list of strips to accumulate at current time */
typedef struct NlaEvalStrip {
	struct NlaEvalStrip *next, *prev;
	
	NlaTrack *track;			/* track that this strip belongs to */
	NlaStrip *strip;		/* strip that's being used */
	NlaStrip *sblend;		/* strip that's being blended towards (if applicable) */
	
	short track_index;			/* the index of the track within the list */
	short strip_mode;			/* which end of the strip are we looking at */
} NlaEvalStrip;

/* bNlaEvalStrip->strip_mode */
enum {
	NES_TIME_BEFORE = -1,
	NES_TIME_WITHIN,
	NES_TIME_AFTER,
	NES_TIME_AFTER_BLEND
} eNlaEvalStrip_StripMode;


/* temp channel for accumulating data from NLA (avoids needing to clear all values first) */
// TODO: maybe this will be used as the 'cache' stuff needed for editable values too?
typedef struct NlaEvalChannel {
	struct NlaEvalChannel *next, *prev;
	
	char *path;				/* ready-to-use path (i.e. remapped already) */
	int array_index;		/* if applicable... */
	
	float value;			/* value of this channel */
} NlaEvalChannel;


/* ---------------------- */

/* evaluate the F-Curves controlling settings for the NLA-strips (currently, not relinkable) */
static void nlastrip_evaluate_fcurves (NlaStrip *strip, float ctime)
{
	//PointerRNA actstrip_ptr;
	//FCurve *fcu;
	
	/* create RNA-pointer needed to set values */
	//RNA_pointer_create(NULL, &RNA_NlaStrip, strip, &actstrip_ptr);
	
	/* execute these settings as per normal */
	//animsys_evaluate_fcurves(&actstrip_ptr, &strip->fcurves, NULL, ctime);
}


/* gets the strip active at the current time for a track */
static void nlatrack_ctime_get_strip (ListBase *list, NlaTrack *nlt, short index, float ctime)
{
	NlaStrip *strip, *astrip=NULL, *bstrip=NULL;
	NlaEvalStrip *nes;
	short side= 0;
	
	/* skip if track is muted */
	if (nlt->flag & NLATRACK_MUTED) 
		return;
	
	/* loop over strips, checking if they fall within the range */
	for (strip= nlt->strips.first; strip; strip= strip->next) {
		/* only consider if:
		 *	- current time occurs within strip's extents
		 *	- current time occurs before strip (if it is the first)
		 *	- current time occurs after strip (if hold is on)
		 *	- current time occurs between strips (1st of those isn't holding) - blend!
		 */
		if (IN_RANGE(ctime, strip->start, strip->end)) {
			astrip= strip;
			side= NES_TIME_WITHIN;
			break;
		}
		else if (ctime < strip->start) {
			if (strip == nlt->strips.first) {
				astrip= strip;
				side= NES_TIME_BEFORE;
				break;
			}
			else {
				astrip= strip->prev;
				
				if (astrip->flag & NLASTRIP_HOLDLASTFRAME) {
					side= NES_TIME_AFTER;
					break;
				}
				else {
					bstrip= strip;
					side= NES_TIME_AFTER_BLEND;
					break;
				}
			}
		}
	}
	
	/* check if strip has been found (and whether it has data worth considering) */
	if (ELEM(NULL, astrip, astrip->act)) 
		return;
	if (astrip->flag & NLASTRIP_MUTE) 
		return;
	
	/* check if blending between strips */
	if (side == NES_TIME_AFTER_BLEND) {
		/* blending between strips... so calculate influence+act_time of both */
		nlastrip_evaluate_fcurves(astrip, ctime);
		nlastrip_evaluate_fcurves(bstrip, ctime);
		
		if ((astrip->influence <= 0.0f) && (bstrip->influence <= 0.0f))
			return;
	}
	else {
		/* calculate/set the influence+act_time of this strip - don't consider if 0 influence */
		nlastrip_evaluate_fcurves(astrip, ctime);
		
		if (astrip->influence <= 0.0f) 
			return;
	}
	
	
	/* allocate new eval-strip for this strip + add to stack */
	nes= MEM_callocN(sizeof(NlaEvalStrip), "NlaEvalStrip");
	
	nes->track= nlt;
	nes->strip= astrip;
	nes->sblend= bstrip;
	nes->track_index= index;
	nes->strip_mode= side;
	
	BLI_addtail(list, nes);
}

/* ---------------------- */

/* evaluates the given evaluation strip */
// FIXME: will we need the evaluation cache table set up to blend stuff in?
// TODO: only evaluate here, but flush in one go using the accumulated channels at end...
static void nlastrip_ctime_evaluate (ListBase *channels, NlaEvalStrip *nes, float ctime)
{
	// 1. (in old code) was to extract 'IPO-channels' from actions
	// 2. blend between the 'accumulated' data, and the new data
}

/* write the accumulated settings to */
static void nladata_flush_channels (PointerRNA *ptr, ListBase *channels)
{
	
}

/* ---------------------- */

/* NLA Evaluation function (mostly for use through do_animdata) 
 *	- All channels that will be affected are not cleared anymore. Instead, we just evaluate into 
 *		some temp channels, where values can be accumulated in one go.
 */
static void animsys_evaluate_nla (PointerRNA *ptr, AnimData *adt, float ctime)
{
	NlaTrack *nlt;
	short track_index=0;
	
	ListBase estrips= {NULL, NULL};
	ListBase echannels= {NULL, NULL};
	NlaEvalStrip *nes;
	
	/* 1. get the stack of strips to evaluate at current time (influence calculated here) */
	for (nlt=adt->nla_tracks.first; nlt; nlt=nlt->next, track_index++) 
		nlatrack_ctime_get_strip(&estrips, nlt, track_index, ctime);
	
	/* only continue if there are strips to evaluate */
	if (estrips.first == NULL)
		return;
	
	
	/* 2. for each strip, evaluate then accumulate on top of existing channels, but don't set values yet */
	for (nes= estrips.first; nes; nes= nes->next) 
		nlastrip_ctime_evaluate(&echannels, nes, ctime);
	
	/* 3. flush effects of accumulating channels in NLA to the actual data they affect */
	nladata_flush_channels(ptr, &echannels);
	
	/* 4. free temporary evaluation data */
	BLI_freelistN(&estrips);
	BLI_freelistN(&echannels);
}

/* ***************************************** */ 
/* Overrides System - Public API */

/* Clear all overides */

/* Add or get existing Override for given setting */
AnimOverride *BKE_animsys_validate_override (PointerRNA *ptr, char *path, int array_index)
{
	// FIXME: need to define how to get overrides
	return NULL;
} 

/* -------------------- */

/* Evaluate Overrides */
static void animsys_evaluate_overrides (PointerRNA *ptr, AnimData *adt, float ctime)
{
	AnimOverride *aor;
	
	/* for each override, simply execute... */
	for (aor= adt->overrides.first; aor; aor= aor->next)
		animsys_write_rna_setting(ptr, aor->rna_path, aor->array_index, aor->value);
}

/* ***************************************** */
/* Evaluation System - Public API */

/* Overview of how this system works:
 *	1) Depsgraph sorts data as necessary, so that data is in an order that means 
 *		that all dependences are resolved before dependants.
 *	2) All normal animation is evaluated, so that drivers have some basis values to
 *		work with
 *		a.	NLA stacks are done first, as the Active Actions act as 'tweaking' tracks
 *			which modify the effects of the NLA-stacks
 *		b.	Active Action is evaluated as per normal, on top of the results of the NLA tracks
 *
 * --------------< often in a separate phase... >------------------ 
 *
 *	3) Drivers/expressions are evaluated on top of this, in an order where dependences are
 *		resolved nicely. 
 *	   Note: it may be necessary to have some tools to handle the cases where some higher-level
 *		drivers are added and cause some problematic dependencies that didn't exist in the local levels...
 *
 * --------------< always executed >------------------ 
 *
 * Maintainance of editability of settings (XXX):
 *	In order to ensure that settings that are animated can still be manipulated in the UI without requiring
 *	that keyframes are added to prevent these values from being overwritten, we use 'overrides'. 
 *
 * Unresolved things:
 *	- Handling of multi-user settings (i.e. time-offset, group-instancing) -> big cache grids or nodal system? but stored where?
 *	- Multiple-block dependencies (i.e. drivers for settings are in both local and higher levels) -> split into separate lists?  
 */

/* Evaluation loop for evaluation animation data 
 *
 * This assumes that the animation-data provided belongs to the ID block in question,
 * and that the flags for which parts of the anim-data settings need to be recalculated 
 * have been set already by the depsgraph. Now, we use the recalc 
 */
void BKE_animsys_evaluate_animdata (ID *id, AnimData *adt, float ctime, short recalc)
{
	PointerRNA id_ptr;
	
	/* sanity checks */
	if ELEM(NULL, id, adt)
		return;
	
	/* get pointer to ID-block for RNA to use */
	RNA_id_pointer_create(id, &id_ptr);
	
	/* recalculate keyframe data:
	 *	- NLA before Active Action, as Active Action behaves as 'tweaking track'
	 *	  that overrides 'rough' work in NLA
	 */
	if ((recalc & ADT_RECALC_ANIM) /*|| (adt->recalc & ADT_RECALC_ANIM)*/) // XXX for now,don't check yet, as depsgraph doesn't know this yet
 	{
		/* evaluate NLA data */
		if ((adt->nla_tracks.first) && !(adt->flag & ADT_NLA_EVAL_OFF))
		{
			animsys_evaluate_nla(&id_ptr, adt, ctime);
		}
		
		/* evaluate Action data */
		// FIXME: what if the solo track was not tweaking one, then nla-solo should be checked too?
		if (adt->action) 
			animsys_evaluate_action(&id_ptr, adt->action, adt->remap, ctime);
	}
	
	/* recalculate drivers 
	 *	- Drivers need to be evaluated afterwards, as they can either override 
	 *	  or be layered on top of existing animation data.
	 *	- Drivers should be in the appropriate order to be evaluated without problems...
	 */
	if ((recalc & ADT_RECALC_DRIVERS) /*&& (adt->recalc & ADT_RECALC_DRIVERS)*/) // XXX for now, don't check yet, as depsgraph hasn't been updated
	{
		animsys_evaluate_drivers(&id_ptr, adt, ctime);
	}
	
	/* always execute 'overrides' 
	 *	- Overrides allow editing, by overwriting the value(s) set from animation-data, with the
	 *	  value last set by the user (and not keyframed yet). 
	 *	- Overrides are cleared upon frame change and/or keyframing
	 *	- It is best that we execute this everytime, so that no errors are likely to occur.
	 */
	animsys_evaluate_overrides(&id_ptr, adt, ctime);
	
	/* clear recalc flag now */
	adt->recalc= 0;
}

/* Evaluation of all ID-blocks with Animation Data blocks - Animation Data Only
 *
 * This will evaluate only the animation info available in the animation data-blocks
 * encountered. In order to enforce the system by which some settings controlled by a
 * 'local' (i.e. belonging in the nearest ID-block that setting is related to, not a
 * standard 'root') block are overridden by a larger 'user'
 */
// TODO: we currently go over entire 'main' database...
void BKE_animsys_evaluate_all_animation (Main *main, float ctime)
{
	ID *id;
	
	if (G.f & G_DEBUG)
		printf("Evaluate all animation - %f \n", ctime);

	/* macro for less typing */
#define EVAL_ANIM_IDS(first) \
	for (id= first; id; id= id->next) { \
		AnimData *adt= BKE_animdata_from_id(id); \
		BKE_animsys_evaluate_animdata(id, adt, ctime, ADT_RECALC_ANIM); \
	}
	
	/* nodes */
	// TODO...
	
	/* textures */
	EVAL_ANIM_IDS(main->tex.first);
	
	/* lamps */
	EVAL_ANIM_IDS(main->lamp.first);
	
	/* materials */
	EVAL_ANIM_IDS(main->mat.first);
	
	/* cameras */
	EVAL_ANIM_IDS(main->camera.first);
	
	/* shapekeys */
	EVAL_ANIM_IDS(main->key.first);
	
	/* curves */
	// TODO...
	
	/* meshes */
	// TODO...
	
	/* objects */
	EVAL_ANIM_IDS(main->object.first);
	
	/* worlds */
	EVAL_ANIM_IDS(main->world.first);
	
	/* scenes */
	EVAL_ANIM_IDS(main->scene.first);
}

/* ***************************************** */ 
