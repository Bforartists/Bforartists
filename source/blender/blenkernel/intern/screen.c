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
#include <stdio.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_screen_types.h"
#include "DNA_space_types.h"

#include "BLI_blenlib.h"

#include "BKE_screen.h"

#ifndef DISABLE_PYTHON
#include "BPY_extern.h"
#endif

/* ************ Spacetype/regiontype handling ************** */

/* keep global; this has to be accessible outside of windowmanager */
static ListBase spacetypes= {NULL, NULL};

/* not SpaceType itself */
static void spacetype_free(SpaceType *st)
{
	BLI_freelistN(&st->regiontypes);
}

void BKE_spacetypes_free(void)
{
	SpaceType *st, *stn;
	
	for(st= spacetypes.first; st; st= stn) {
		stn= st->next;
		spacetype_free(st);
	}
	
	BLI_freelistN(&spacetypes);
}

SpaceType *BKE_spacetype_from_id(int spaceid)
{
	SpaceType *st;
	
	for(st= spacetypes.first; st; st= st->next) {
		if(st->spaceid==spaceid)
			return st;
	}
	return NULL;
}

const ListBase *BKE_spacetypes_list()
{
	return &spacetypes;
}

void BKE_spacetype_register(SpaceType *st)
{
	SpaceType *stype;
	
	/* sanity check */
	stype= BKE_spacetype_from_id(st->spaceid);
	if(stype) {
		printf("error: redefinition of spacetype %s\n", stype->name);
		spacetype_free(stype);
		MEM_freeN(stype);
	}
	
	BLI_addtail(&spacetypes, st);
}

/* ***************** Space handling ********************** */

void BKE_spacedata_freelist(ListBase *lb)
{
	SpaceLink *sl, *sln;
	ARegion *ar, *arn;
	
	for (sl= lb->first; sl; sl= sln) {
		SpaceType *st= BKE_spacetype_from_id(sl->spacetype);
		sln= sl->next;
		
		/* regions for pushed spaces */
		for(ar=sl->regionbase.first; ar; ar=arn) {
			arn= ar->next;
			BKE_area_region_free(ar);
		}
		BLI_freelistN(&sl->regionbase);
		
		if(st && st->free) 
			st->free(sl);
	}
	
	BLI_freelistN(lb);
}

/* lb1 should be empty */
void BKE_spacedata_copylist(ListBase *lb1, ListBase *lb2)
{
	SpaceLink *sl;
	
	lb1->first= lb2->last= NULL;	/* to be sure */
	
	for (sl= lb2->first; sl; sl= sl->next) {
		SpaceType *st= BKE_spacetype_from_id(sl->spacetype);
		
		if(st && st->duplicate)
			BLI_addtail(lb1, st->duplicate(sl));
	}
}

/* not region itself */
void BKE_area_region_free(ARegion *ar)
{
	if(ar && ar->type && ar->type->free)
		ar->type->free(ar);
}

/* not area itself */
void BKE_screen_area_free(ScrArea *sa)
{
	ARegion *ar, *arn;
	
	for(ar=sa->regionbase.first; ar; ar=arn) {
		arn= ar->next;
		BKE_area_region_free(ar);
	}

	BKE_spacedata_freelist(&sa->spacedata);
	
	BLI_freelistN(&sa->regionbase);
	BLI_freelistN(&sa->actionzones);
	
	BLI_freelistN(&sa->panels);
	//	uiFreeBlocks(&sa->uiblocks);
	//	uiFreePanels(&sa->panels);
	
#ifndef DISABLE_PYTHON
	BPY_free_scriptlink(&sa->scriptlink);
#endif
}

/* don't free screen itself */
void free_screen(bScreen *sc)
{
	ScrArea *sa, *san;
	ARegion *ar, *arn;
	
	for(ar=sc->regionbase.first; ar; ar=arn) {
		arn= ar->next;
		BKE_area_region_free(ar);
	}
	BLI_freelistN(&sc->regionbase);
	
	for(sa= sc->areabase.first; sa; sa= san) {
		san= sa->next;
		BKE_screen_area_free(sa);
	}
	
	BLI_freelistN(&sc->vertbase);
	BLI_freelistN(&sc->edgebase);
	BLI_freelistN(&sc->areabase);
}


