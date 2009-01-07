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
* The Original Code is Copyright (C) 2006-2007 Blender Foundation.
* All rights reserved.
* 
* The Original Code is: all of this file.
* 
* Contributor(s): none yet.
* 
* ***** END GPL LICENSE BLOCK *****
*
*/

#include <math.h>
#include <stdlib.h>
#include <string.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "MEM_guardedalloc.h"

#include "DNA_ID.h"
#include "DNA_image_types.h"
#include "DNA_lamp_types.h"
#include "DNA_material_types.h"
#include "DNA_texture_types.h"
#include "DNA_world_types.h"

#include "BLI_ghash.h"

#include "BKE_icons.h"
#include "BKE_utildefines.h"

#include "BLO_sys_types.h" // for intptr_t support

#define GS(a)	(*((short *)(a)))

/* GLOBALS */

static GHash* gIcons = NULL;

static int gNextIconId = 1;

static int gFirstIconId = 1;


static void icon_free(void *val)
{
	Icon* icon = val;

	if (icon)
	{
		if (icon->drawinfo_free) {		
			icon->drawinfo_free(icon->drawinfo);
		}
		else if (icon->drawinfo) {
			MEM_freeN(icon->drawinfo);
		}
		MEM_freeN(icon);
	}
}

/* create an id for a new icon and make sure that ids from deleted icons get reused
   after the integer number range is used up */
static int get_next_free_id()
{
	int startId = gFirstIconId;

	/* if we haven't used up the int number range, we just return the next int */
	if (gNextIconId>=gFirstIconId)
		return gNextIconId++;
	
	/* now we try to find the smallest icon id not stored in the gIcons hash */
	while (BLI_ghash_lookup(gIcons, SET_INT_IN_POINTER(startId)) && startId>=gFirstIconId) 
		startId++;

	/* if we found a suitable one that isnt used yet, return it */
	if (startId>=gFirstIconId)
		return startId;

	/* fail */
	return 0;
}

void BKE_icons_init(int first_dyn_id)
{
	gNextIconId = first_dyn_id;
	gFirstIconId = first_dyn_id;

	if (!gIcons)
		gIcons = BLI_ghash_new(BLI_ghashutil_inthash, BLI_ghashutil_intcmp);
}

void BKE_icons_free()
{
	if(gIcons)
		BLI_ghash_free(gIcons, 0, icon_free);
	gIcons = NULL;
}

struct PreviewImage* BKE_previewimg_create() 
{
	PreviewImage* prv_img = NULL;
	int i;

	prv_img = MEM_callocN(sizeof(PreviewImage), "img_prv");

	for (i=0; i<PREVIEW_MIPMAPS; ++i) {
		prv_img->changed[i] = 1;
	}
	return prv_img;
}

void BKE_previewimg_free(PreviewImage **prv)
{
	if(prv && (*prv)) {
		int i;
		
		for (i=0; i<PREVIEW_MIPMAPS;++i) {
			if ((*prv)->rect[i]) {
				MEM_freeN((*prv)->rect[i]);
				(*prv)->rect[i] = NULL;
			}
		}
		MEM_freeN((*prv));
		*prv = NULL;
	}
}

struct PreviewImage* BKE_previewimg_copy(PreviewImage *prv) 
{
	PreviewImage* prv_img = NULL;
	int i;

	if (prv) {
		prv_img = MEM_dupallocN(prv);
		for (i=0; i < PREVIEW_MIPMAPS; ++i) {
			if (prv->rect[i]) {
				prv_img->rect[i] = MEM_dupallocN(prv->rect[i]);
			} else {
				prv_img->rect[i] = NULL;
			}
		}
	}
	return prv_img;
}

void BKE_previewimg_free_id(ID *id) 
{
	if (GS(id->name) == ID_MA) {
		Material *mat = (Material*)id;	
		BKE_previewimg_free(&mat->preview);
	} else if (GS(id->name) == ID_TE) {
		Tex *tex = (Tex*)id;
		BKE_previewimg_free(&tex->preview);
	} else if (GS(id->name) == ID_WO) {
		World *wo = (World*)id;
		BKE_previewimg_free(&wo->preview);
	} else if (GS(id->name) == ID_LA) {
		Lamp *la  = (Lamp*)id;
		BKE_previewimg_free(&la->preview);
	} else if (GS(id->name) == ID_IM) {
		Image *img  = (Image*)id;
		BKE_previewimg_free(&img->preview);
	}
}

PreviewImage* BKE_previewimg_get(ID *id) 
{
	PreviewImage* prv_img = NULL;

	if (GS(id->name) == ID_MA) {
		Material *mat = (Material*)id;	
		if (!mat->preview) mat->preview = BKE_previewimg_create();
		prv_img = mat->preview;
	} else if (GS(id->name) == ID_TE) {
		Tex *tex = (Tex*)id;
		if (!tex->preview) tex->preview = BKE_previewimg_create();
		prv_img = tex->preview;
	} else if (GS(id->name) == ID_WO) {
		World *wo = (World*)id;
		if (!wo->preview) wo->preview = BKE_previewimg_create();
		prv_img = wo->preview;
	} else if (GS(id->name) == ID_LA) {
		Lamp *la  = (Lamp*)id;
		if (!la->preview) la->preview = BKE_previewimg_create();
		prv_img = la->preview;
	} else if (GS(id->name) == ID_IM) {
		Image *img  = (Image*)id;
		if (!img->preview) img->preview = BKE_previewimg_create();
		prv_img = img->preview;
	} 

	return prv_img;
}

void BKE_icon_changed(int id)
{
	Icon* icon = 0;
	
	if (!id) return;

	icon = BLI_ghash_lookup(gIcons, SET_INT_IN_POINTER(id));
	
	if (icon)
	{
		PreviewImage *prv = BKE_previewimg_get((ID*)icon->obj);

		/* all previews changed */
		if (prv) {
			int i;
			for (i=0; i<PREVIEW_MIPMAPS; ++i) {
				prv->changed[i] = 1;
			}
		}
	}	
}

int BKE_icon_getid(struct ID* id)
{
	Icon* new_icon = 0;

	if (!id)
		return 0;

	if (id->icon_id)
		return id->icon_id;

	id->icon_id = get_next_free_id();

	if (!id->icon_id){
		printf("BKE_icon_getid: Internal error - not enough IDs\n");
		return 0;
	}

	new_icon = MEM_callocN(sizeof(Icon), "texicon");

	new_icon->obj = id;
	new_icon->type = GS(id->name);
	
	/* next two lines make sure image gets created */
	new_icon->drawinfo = 0;
	new_icon->drawinfo_free = 0;

	BLI_ghash_insert(gIcons, SET_INT_IN_POINTER(id->icon_id), new_icon);
	
	return id->icon_id;
}

Icon* BKE_icon_get(int icon_id)
{
	Icon* icon = 0;

	icon = BLI_ghash_lookup(gIcons, SET_INT_IN_POINTER(icon_id));
	
	if (!icon) {
		printf("BKE_icon_get: Internal error, no icon for icon ID: %d\n", icon_id);
		return 0;
	}

	return icon;
}

void BKE_icon_set(int icon_id, struct Icon* icon)
{
	Icon* old_icon = 0;

	old_icon = BLI_ghash_lookup(gIcons, SET_INT_IN_POINTER(icon_id));

	if (old_icon)
	{
		printf("BKE_icon_set: Internal error, icon already set: %d\n", icon_id);
		return;
	}

	BLI_ghash_insert(gIcons, SET_INT_IN_POINTER(icon_id), icon);
}

void BKE_icon_delete(struct ID* id)
{

	if (!id->icon_id) return; /* no icon defined for library object */

	BLI_ghash_remove(gIcons, SET_INT_IN_POINTER(id->icon_id), 0, icon_free);
	id->icon_id = 0;
}
