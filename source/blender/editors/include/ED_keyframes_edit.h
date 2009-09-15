/**
 * $Id:
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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Joshua Leung
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef ED_KEYFRAMES_EDIT_H
#define ED_KEYFRAMES_EDIT_H

struct bAnimContext;
struct bAnimListElem;
struct FCurve;
struct BezTriple;
struct Scene;

/* ************************************************ */
/* Common Macros and Defines */

/* --------- BezTriple Selection ------------- */

#define BEZSELECTED(bezt) ((bezt->f2 & SELECT) || (bezt->f1 & SELECT) || (bezt->f3 & SELECT))

#define BEZ_SEL(bezt)		{ (bezt)->f1 |=  SELECT; (bezt)->f2 |=  SELECT; (bezt)->f3 |=  SELECT; }
#define BEZ_DESEL(bezt)		{ (bezt)->f1 &= ~SELECT; (bezt)->f2 &= ~SELECT; (bezt)->f3 &= ~SELECT; }
#define BEZ_INVSEL(bezt)	{ (bezt)->f1 ^=  SELECT; (bezt)->f2 ^=  SELECT; (bezt)->f3 ^=  SELECT; }

/* --------- Tool Flags ------------ */

/* bezt validation */
typedef enum eEditKeyframes_Validate {
	BEZT_OK_FRAME	= 1,
	BEZT_OK_FRAMERANGE,
	BEZT_OK_SELECTED,
	BEZT_OK_VALUE,
	BEZT_OK_VALUERANGE,
	BEZT_OK_REGION,
} eEditKeyframes_Validate;

/* ------------ */

/* select tools */
typedef enum eEditKeyframes_Select {
	SELECT_REPLACE	=	(1<<0),
	SELECT_ADD		= 	(1<<1),
	SELECT_SUBTRACT	= 	(1<<2),
	SELECT_INVERT	= 	(1<<4),
} eEditKeyframes_Select;

/* snapping tools */
typedef enum eEditKeyframes_Snap {
	SNAP_KEYS_CURFRAME = 1,
	SNAP_KEYS_NEARFRAME,
	SNAP_KEYS_NEARSEC,
	SNAP_KEYS_NEARMARKER,
	SNAP_KEYS_HORIZONTAL,
} eEditKeyframes_Snap;

/* mirroring tools */
typedef enum eEditKeyframes_Mirror {
	MIRROR_KEYS_CURFRAME = 1,
	MIRROR_KEYS_YAXIS,
	MIRROR_KEYS_XAXIS,
	MIRROR_KEYS_MARKER,
} eEditKeyframes_Mirror;

/* ************************************************ */
/* Non-Destuctive Editing API (keyframes_edit.c) */

/* --- Generic Properties for Bezier Edit Tools ----- */

typedef struct BeztEditData {
	ListBase list;				/* temp list for storing custom list of data to check */
	struct Scene *scene;		/* pointer to current scene - many tools need access to cfra/etc.  */
	void *data;					/* pointer to custom data - usually 'Object' but also 'rectf', but could be other types too */
	float f1, f2;				/* storage of times/values as 'decimals' */
	int i1, i2;					/* storage of times/values/flags as 'whole' numbers */
} BeztEditData;

/* ------- Function Pointer Typedefs ---------------- */

	/* callback function that refreshes the IPO curve after use */
typedef void (*FcuEditFunc)(struct FCurve *fcu);
	/* callback function that operates on the given BezTriple */
typedef short (*BeztEditFunc)(BeztEditData *bed, struct BezTriple *bezt);

/* ---------------- Looping API --------------------- */

/* functions for looping over keyframes */
	/* function for working with F-Curve data only (i.e. when filters have been chosen to explicitly use this) */
short ANIM_fcurve_keys_bezier_loop(BeztEditData *bed, struct FCurve *fcu, BeztEditFunc bezt_ok, BeztEditFunc bezt_cb, FcuEditFunc fcu_cb);
	/* function for working with any type (i.e. one of the known types) of animation channel 
	 *	- filterflag is bDopeSheet->flag (DOPESHEET_FILTERFLAG)
	 */
short ANIM_animchannel_keys_bezier_loop(BeztEditData *bed, struct bAnimListElem *ale, BeztEditFunc bezt_ok, BeztEditFunc bezt_cb, FcuEditFunc fcu_cb, int filterflag);
	/* same as above, except bAnimListElem wrapper is not needed... 
	 * 	- keytype is eAnim_KeyType
	 */
short ANIM_animchanneldata_keys_bezier_loop(BeztEditData *bed, void *data, int keytype, BeztEditFunc bezt_ok, BeztEditFunc bezt_cb, FcuEditFunc fcu_cb, int filterflag);

/* functions for making sure all keyframes are in good order */
void ANIM_editkeyframes_refresh(struct bAnimContext *ac);

/* ----------- BezTriple Callback Getters ---------- */

/* accessories */
BeztEditFunc ANIM_editkeyframes_ok(short mode);

/* edit */
BeztEditFunc ANIM_editkeyframes_snap(short mode);
BeztEditFunc ANIM_editkeyframes_mirror(short mode);
BeztEditFunc ANIM_editkeyframes_select(short mode);
BeztEditFunc ANIM_editkeyframes_handles(short mode);
BeztEditFunc ANIM_editkeyframes_ipo(short mode);

/* ----------- BezTriple Callback (Assorted Utilities) ---------- */

short bezt_calc_average(BeztEditData *bed, struct BezTriple *bezt);
short bezt_to_cfraelem(BeztEditData *bed, struct BezTriple *bezt);

/* ************************************************ */
/* Destructive Editing API (keyframes_general.c) */

void delete_fcurve_key(struct FCurve *fcu, int index, short do_recalc);
void delete_fcurve_keys(struct FCurve *fcu);
void duplicate_fcurve_keys(struct FCurve *fcu);

void clean_fcurve(struct FCurve *fcu, float thresh);
void smooth_fcurve(struct FCurve *fcu);

/* ----------- */

void free_anim_copybuf(void);
short copy_animedit_keys(struct bAnimContext *ac, ListBase *anim_data);
short paste_animedit_keys(struct bAnimContext *ac, ListBase *anim_data);

/* ************************************************ */

#endif /* ED_KEYFRAMES_EDIT_H */
