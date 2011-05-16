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
* along with this program; if not, write to the Free Software  Foundation,
* Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
*
* The Original Code is Copyright (C) 2005 by the Blender Foundation.
* All rights reserved.
*
* Contributor(s): Daniel Dunbar
*                 Ton Roosendaal,
*                 Ben Batt,
*                 Brecht Van Lommel,
*                 Campbell Barton
*
* ***** END GPL LICENSE BLOCK *****
*
* Modifier stack implementation.
*
* BKE_modifier.h contains the function prototypes for this file.
*
*/

/** \file blender/blenkernel/intern/modifier.c
 *  \ingroup bke
 */


#include <stddef.h>
#include <string.h>
#include <stdarg.h>
#include <math.h>
#include <float.h>

#include "MEM_guardedalloc.h"

#include "DNA_armature_types.h"
#include "DNA_object_types.h"
#include "DNA_meshdata_types.h"

#include "BLI_utildefines.h"

#include "BKE_bmesh.h"
#include "BKE_cloth.h"
#include "BKE_key.h"
#include "BKE_multires.h"

#include "MOD_modifiertypes.h"

ModifierTypeInfo *modifierType_getInfo(ModifierType type)
{
	static ModifierTypeInfo *types[NUM_MODIFIER_TYPES]= {NULL};
	static int types_init = 1;

	if (types_init) {
		modifier_type_init(types); /* MOD_utils.c */
		types_init= 0;
	}

	/* type unsigned, no need to chech < 0 */
	if(type < NUM_MODIFIER_TYPES && types[type]->name[0] != '\0') {
		return types[type];
	}
	else {
		return NULL;
	}
}

/***/

ModifierData *modifier_new(int type)
{
	ModifierTypeInfo *mti = modifierType_getInfo(type);
	ModifierData *md = MEM_callocN(mti->structSize, mti->structName);
	
	// FIXME: we need to make the name always be unique somehow...
	strcpy(md->name, mti->name);

	md->type = type;
	md->mode = eModifierMode_Realtime
			| eModifierMode_Render | eModifierMode_Expanded;

	if (mti->flags & eModifierTypeFlag_EnableInEditmode)
		md->mode |= eModifierMode_Editmode;

	if (mti->initData) mti->initData(md);

	return md;
}

void modifier_free(ModifierData *md) 
{
	ModifierTypeInfo *mti = modifierType_getInfo(md->type);

	if (mti->freeData) mti->freeData(md);
	if (md->error) MEM_freeN(md->error);

	MEM_freeN(md);
}

void modifier_unique_name(ListBase *modifiers, ModifierData *md)
{
	if (modifiers && md) {
		ModifierTypeInfo *mti = modifierType_getInfo(md->type);
		
		BLI_uniquename(modifiers, md, mti->name, '.', offsetof(ModifierData, name), sizeof(md->name));
	}
}

int modifier_dependsOnTime(ModifierData *md) 
{
	ModifierTypeInfo *mti = modifierType_getInfo(md->type);

	return mti->dependsOnTime && mti->dependsOnTime(md);
}

int modifier_supportsMapping(ModifierData *md)
{
	ModifierTypeInfo *mti = modifierType_getInfo(md->type);

	return (mti->type==eModifierTypeType_OnlyDeform ||
			(mti->flags & eModifierTypeFlag_SupportsMapping));
}

ModifierData *modifiers_findByType(Object *ob, ModifierType type)
{
	ModifierData *md = ob->modifiers.first;

	for (; md; md=md->next)
		if (md->type==type)
			break;

	return md;
}

ModifierData *modifiers_findByName(Object *ob, const char *name)
{
	return BLI_findstring(&(ob->modifiers), name, offsetof(ModifierData, name));
}

void modifiers_clearErrors(Object *ob)
{
	ModifierData *md = ob->modifiers.first;
	/* int qRedraw = 0; */

	for (; md; md=md->next) {
		if (md->error) {
			MEM_freeN(md->error);
			md->error = NULL;

			/* qRedraw = 1; */
		}
	}
}

void modifiers_foreachObjectLink(Object *ob, ObjectWalkFunc walk,
				 void *userData)
{
	ModifierData *md = ob->modifiers.first;

	for (; md; md=md->next) {
		ModifierTypeInfo *mti = modifierType_getInfo(md->type);

		if (mti->foreachObjectLink)
			mti->foreachObjectLink(md, ob, walk, userData);
	}
}

void modifiers_foreachIDLink(Object *ob, IDWalkFunc walk, void *userData)
{
	ModifierData *md = ob->modifiers.first;

	for (; md; md=md->next) {
		ModifierTypeInfo *mti = modifierType_getInfo(md->type);

		if(mti->foreachIDLink) mti->foreachIDLink(md, ob, walk, userData);
		else if(mti->foreachObjectLink) {
			/* each Object can masquerade as an ID, so this should be OK */
			ObjectWalkFunc fp = (ObjectWalkFunc)walk;
			mti->foreachObjectLink(md, ob, fp, userData);
		}
	}
}

void modifier_copyData(ModifierData *md, ModifierData *target)
{
	ModifierTypeInfo *mti = modifierType_getInfo(md->type);

	target->mode = md->mode;

	if (mti->copyData)
		mti->copyData(md, target);
}

int modifier_couldBeCage(struct Scene *scene, ModifierData *md)
{
	ModifierTypeInfo *mti = modifierType_getInfo(md->type);

	md->scene= scene;

	return (	(md->mode & eModifierMode_Realtime) &&
			(md->mode & eModifierMode_Editmode) &&
			(!mti->isDisabled || !mti->isDisabled(md, 0)) &&
			modifier_supportsMapping(md));	
}

int modifier_sameTopology(ModifierData *md)
{
	ModifierTypeInfo *mti = modifierType_getInfo(md->type);
	return ( mti->type == eModifierTypeType_OnlyDeform || mti->type == eModifierTypeType_Nonconstructive);
}

void modifier_setError(ModifierData *md, const char *format, ...)
{
	char buffer[512];
	va_list ap;

	va_start(ap, format);
	vsnprintf(buffer, sizeof(buffer), format, ap);
	va_end(ap);
	buffer[sizeof(buffer) - 1]= '\0';

	if (md->error)
		MEM_freeN(md->error);

	md->error = BLI_strdup(buffer);

}

/* used for buttons, to find out if the 'draw deformed in editmode' option is
 * there
 * 
 * also used in transform_conversion.c, to detect CrazySpace [tm] (2nd arg
 * then is NULL) 
 * also used for some mesh tools to give warnings
 */
int modifiers_getCageIndex(struct Scene *scene, Object *ob, int *lastPossibleCageIndex_r, int virtual_)
{
	ModifierData *md = (virtual_)? modifiers_getVirtualModifierList(ob): ob->modifiers.first;
	int i, cageIndex = -1;

	if(lastPossibleCageIndex_r) {
		/* ensure the value is initialized */
		*lastPossibleCageIndex_r= -1;
	}

	/* Find the last modifier acting on the cage. */
	for (i=0; md; i++,md=md->next) {
		ModifierTypeInfo *mti = modifierType_getInfo(md->type);

		md->scene= scene;

		if (!(md->mode & eModifierMode_Realtime)) continue;
		if (!(md->mode & eModifierMode_Editmode)) continue;
		if (mti->isDisabled && mti->isDisabled(md, 0)) continue;
		if (!(mti->flags & eModifierTypeFlag_SupportsEditmode)) continue;
		if (md->mode & eModifierMode_DisableTemporary) continue;

		if (!modifier_supportsMapping(md))
			break;

		if (lastPossibleCageIndex_r) *lastPossibleCageIndex_r = i;
		if (md->mode & eModifierMode_OnCage)
			cageIndex = i;
	}

	return cageIndex;
}


int modifiers_isSoftbodyEnabled(Object *ob)
{
	ModifierData *md = modifiers_findByType(ob, eModifierType_Softbody);

	return (md && md->mode & (eModifierMode_Realtime | eModifierMode_Render));
}

int modifiers_isClothEnabled(Object *ob)
{
	ModifierData *md = modifiers_findByType(ob, eModifierType_Cloth);

	return (md && md->mode & (eModifierMode_Realtime | eModifierMode_Render));
}

int modifiers_isParticleEnabled(Object *ob)
{
	ModifierData *md = modifiers_findByType(ob, eModifierType_ParticleSystem);

	return (md && md->mode & (eModifierMode_Realtime | eModifierMode_Render));
}

int modifier_isEnabled(struct Scene *scene, ModifierData *md, int required_mode)
{
	ModifierTypeInfo *mti = modifierType_getInfo(md->type);

	md->scene= scene;

	if((md->mode & required_mode) != required_mode) return 0;
	if(mti->isDisabled && mti->isDisabled(md, required_mode == eModifierMode_Render)) return 0;
	if(md->mode & eModifierMode_DisableTemporary) return 0;
	if(required_mode & eModifierMode_Editmode)
		if(!(mti->flags & eModifierTypeFlag_SupportsEditmode)) return 0;
	
	return 1;
}

LinkNode *modifiers_calcDataMasks(struct Scene *scene, Object *ob, ModifierData *md, CustomDataMask dataMask, int required_mode)
{
	LinkNode *dataMasks = NULL;
	LinkNode *curr, *prev;

	/* build a list of modifier data requirements in reverse order */
	for(; md; md = md->next) {
		ModifierTypeInfo *mti = modifierType_getInfo(md->type);
		CustomDataMask mask = 0;

		if(modifier_isEnabled(scene, md, required_mode))
			if(mti->requiredDataMask)
				mask = mti->requiredDataMask(ob, md);

		BLI_linklist_prepend(&dataMasks, SET_INT_IN_POINTER(mask));
	}

	/* build the list of required data masks - each mask in the list must
	* include all elements of the masks that follow it
	*
	* note the list is currently in reverse order, so "masks that follow it"
	* actually means "masks that precede it" at the moment
	*/
	for(curr = dataMasks, prev = NULL; curr; prev = curr, curr = curr->next) {
		if(prev) {
			CustomDataMask prev_mask = (CustomDataMask)GET_INT_FROM_POINTER(prev->link);
			CustomDataMask curr_mask = (CustomDataMask)GET_INT_FROM_POINTER(curr->link);

			curr->link = SET_INT_IN_POINTER(curr_mask | prev_mask);
		} else {
			CustomDataMask curr_mask = (CustomDataMask)GET_INT_FROM_POINTER(curr->link);

			curr->link = SET_INT_IN_POINTER(curr_mask | dataMask);
		}
	}

	/* reverse the list so it's in the correct order */
	BLI_linklist_reverse(&dataMasks);

	return dataMasks;
}

ModifierData *modifiers_getVirtualModifierList(Object *ob)
{
		/* Kinda hacky, but should be fine since we are never
	* reentrant and avoid free hassles.
		*/
	static ArmatureModifierData amd;
	static CurveModifierData cmd;
	static LatticeModifierData lmd;
	static ShapeKeyModifierData smd;
	static int init = 1;
	ModifierData *md;

	if (init) {
		md = modifier_new(eModifierType_Armature);
		amd = *((ArmatureModifierData*) md);
		modifier_free(md);

		md = modifier_new(eModifierType_Curve);
		cmd = *((CurveModifierData*) md);
		modifier_free(md);

		md = modifier_new(eModifierType_Lattice);
		lmd = *((LatticeModifierData*) md);
		modifier_free(md);

		md = modifier_new(eModifierType_ShapeKey);
		smd = *((ShapeKeyModifierData*) md);
		modifier_free(md);

		amd.modifier.mode |= eModifierMode_Virtual;
		cmd.modifier.mode |= eModifierMode_Virtual;
		lmd.modifier.mode |= eModifierMode_Virtual;
		smd.modifier.mode |= eModifierMode_Virtual;

		init = 0;
	}

	md = ob->modifiers.first;

	if(ob->parent) {
		if(ob->parent->type==OB_ARMATURE && ob->partype==PARSKEL) {
			amd.object = ob->parent;
			amd.modifier.next = md;
			amd.deformflag= ((bArmature *)(ob->parent->data))->deformflag;
			md = &amd.modifier;
		} else if(ob->parent->type==OB_CURVE && ob->partype==PARSKEL) {
			cmd.object = ob->parent;
			cmd.defaxis = ob->trackflag + 1;
			cmd.modifier.next = md;
			md = &cmd.modifier;
		} else if(ob->parent->type==OB_LATTICE && ob->partype==PARSKEL) {
			lmd.object = ob->parent;
			lmd.modifier.next = md;
			md = &lmd.modifier;
		}
	}

	/* shape key modifier, not yet for curves */
	if(ELEM(ob->type, OB_MESH, OB_LATTICE) && ob_get_key(ob)) {
		if(ob->type == OB_MESH && (ob->shapeflag & OB_SHAPE_EDIT_MODE))
			smd.modifier.mode |= eModifierMode_Editmode|eModifierMode_OnCage;
		else
			smd.modifier.mode &= ~eModifierMode_Editmode|eModifierMode_OnCage;

		smd.modifier.next = md;
		md = &smd.modifier;
	}

	return md;
}
/* Takes an object and returns its first selected armature, else just its
 * armature
 * This should work for multiple armatures per object
 */
Object *modifiers_isDeformedByArmature(Object *ob)
{
	ModifierData *md = modifiers_getVirtualModifierList(ob);
	ArmatureModifierData *amd= NULL;
	
	/* return the first selected armature, this lets us use multiple armatures
	*/
	for (; md; md=md->next) {
		if (md->type==eModifierType_Armature) {
			amd = (ArmatureModifierData*) md;
			if (amd->object && (amd->object->flag & SELECT))
				return amd->object;
		}
	}
	
	if (amd) /* if were still here then return the last armature */
		return amd->object;
	
	return NULL;
}

/* Takes an object and returns its first selected lattice, else just its
* lattice
* This should work for multiple lattics per object
*/
Object *modifiers_isDeformedByLattice(Object *ob)
{
	ModifierData *md = modifiers_getVirtualModifierList(ob);
	LatticeModifierData *lmd= NULL;
	
	/* return the first selected lattice, this lets us use multiple lattices
	*/
	for (; md; md=md->next) {
		if (md->type==eModifierType_Lattice) {
			lmd = (LatticeModifierData*) md;
			if (lmd->object && (lmd->object->flag & SELECT))
				return lmd->object;
		}
	}
	
	if (lmd) /* if were still here then return the last lattice */
		return lmd->object;
	
	return NULL;
}



int modifiers_usesArmature(Object *ob, bArmature *arm)
{
	ModifierData *md = modifiers_getVirtualModifierList(ob);

	for (; md; md=md->next) {
		if (md->type==eModifierType_Armature) {
			ArmatureModifierData *amd = (ArmatureModifierData*) md;
			if (amd->object && amd->object->data==arm) 
				return 1;
		}
	}

	return 0;
}

int modifier_isCorrectableDeformed(ModifierData *md)
{
	if (md->type==eModifierType_Armature)
		return 1;
	if (md->type==eModifierType_ShapeKey)
		return 1;
	
	return 0;
}

int modifiers_isCorrectableDeformed(Object *ob)
{
	ModifierData *md = modifiers_getVirtualModifierList(ob);
	
	for (; md; md=md->next) {
		if(ob->mode==OB_MODE_EDIT && (md->mode & eModifierMode_Editmode)==0);
		else 
			if(modifier_isCorrectableDeformed(md))
				return 1;
	}
	return 0;
}

int modifiers_indexInObject(Object *ob, ModifierData *md_seek)
{
	int i= 0;
	ModifierData *md;
	
	for (md=ob->modifiers.first; (md && md_seek!=md); md=md->next, i++);
	if (!md) return -1; /* modifier isnt in the object */
	return i;
}

void modifier_freeTemporaryData(ModifierData *md)
{
	if(md->type == eModifierType_Armature) {
		ArmatureModifierData *amd= (ArmatureModifierData*)md;

		if(amd->prevCos) {
			MEM_freeN(amd->prevCos);
			amd->prevCos= NULL;
		}
	}
}

/* ensure modifier correctness when changing ob->data */
void test_object_modifiers(Object *ob)
{
	ModifierData *md;

	/* just multires checked for now, since only multires
	   modifies mesh data */

	if(ob->type != OB_MESH) return;

	for(md = ob->modifiers.first; md; md = md->next) {
		if(md->type == eModifierType_Multires) {
			MultiresModifierData *mmd = (MultiresModifierData*)md;

			multiresModifier_set_levels_from_disps(mmd, ob);
		}
	}
}
