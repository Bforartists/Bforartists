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
 * The Original Code is Copyright (C) 2011 Blender Foundation.
 * All rights reserved.
 *
 *
 * Contributor(s): Blender Foundation,
 *                 Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_clip/clip_header.c
 *  \ingroup spclip
 */

#include "DNA_windowmanager_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_utildefines.h"

#include "BKE_context.h"
#include "BKE_screen.h"

#include "ED_screen.h"

#include "WM_types.h"

/* ************************ header area region *********************** */

/************************** properties ******************************/

static ARegion *clip_has_properties_region(ScrArea *sa)
{
	ARegion *ar, *arnew;

	ar= BKE_area_find_region_type(sa, RGN_TYPE_UI);
	if(ar)
		return ar;

	/* add subdiv level; after header */
	ar= BKE_area_find_region_type(sa, RGN_TYPE_HEADER);

	/* is error! */
	if(ar==NULL)
		return NULL;

	arnew= MEM_callocN(sizeof(ARegion), "clip properties region");

	BLI_insertlinkafter(&sa->regionbase, ar, arnew);
	arnew->regiontype= RGN_TYPE_UI;
	arnew->alignment= RGN_ALIGN_RIGHT;

	arnew->flag= RGN_FLAG_HIDDEN;

	return arnew;
}

static int properties_poll(bContext *C)
{
	return (CTX_wm_space_clip(C) != NULL);
}

static int properties_exec(bContext *C, wmOperator *UNUSED(op))
{
	ScrArea *sa= CTX_wm_area(C);
	ARegion *ar= clip_has_properties_region(sa);

	if(ar)
		ED_region_toggle_hidden(C, ar);

	return OPERATOR_FINISHED;
}

void CLIP_OT_properties(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Properties";
	ot->description= "Toggle clip properties panel";
	ot->idname= "CLIP_OT_properties";

	/* api callbacks */
	ot->exec= properties_exec;
	ot->poll= properties_poll;
}

/************************** tools ******************************/

static ARegion *clip_has_tools_region(ScrArea *sa)
{
	ARegion *ar, *arnew;

	ar= BKE_area_find_region_type(sa, RGN_TYPE_TOOLS);
	if(ar)
		return ar;

	/* add subdiv level; after header */
	ar= BKE_area_find_region_type(sa, RGN_TYPE_HEADER);

	/* is error! */
	if(ar==NULL)
		return NULL;

	arnew= MEM_callocN(sizeof(ARegion), "clip tools region");

	BLI_insertlinkafter(&sa->regionbase, ar, arnew);
	arnew->regiontype= RGN_TYPE_TOOLS;
	arnew->alignment= RGN_ALIGN_LEFT;

	arnew->flag= RGN_FLAG_HIDDEN;

	return arnew;
}

static int tools_poll(bContext *C)
{
	return (CTX_wm_space_clip(C) != NULL);
}

static int tools_exec(bContext *C, wmOperator *UNUSED(op))
{
	ScrArea *sa= CTX_wm_area(C);
	ARegion *ar= clip_has_tools_region(sa);

	if(ar)
		ED_region_toggle_hidden(C, ar);

	return OPERATOR_FINISHED;
}

void CLIP_OT_tools(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Tools";
	ot->description= "Toggle clip tools panel";
	ot->idname= "CLIP_OT_tools";

	/* api callbacks */
	ot->exec= tools_exec;
	ot->poll= tools_poll;
}
