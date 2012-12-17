/*
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
 * The Original Code is Copyright (C) 2009 by Blender Foundation
 * All rights reserved.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_sequencer/sequencer_buttons.c
 *  \ingroup spseq
 */

#include <string.h>
#include <stdio.h>


#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_utildefines.h"

#include "BLF_translation.h"

#include "BKE_context.h"
#include "BKE_screen.h"

#include "ED_screen.h"
#include "ED_gpencil.h"
#include "ED_sequencer.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_interface.h"

#include "sequencer_intern.h"

/* **************************** buttons ********************************* */

static int sequencer_grease_pencil_panel_poll(const bContext *C, PanelType *UNUSED(pt))
{
	SpaceSeq *sseq = CTX_wm_space_seq(C);

	/* don't show the gpencil if we are not showing the image */
	return ED_space_sequencer_check_show_imbuf(sseq);
}

void sequencer_buttons_register(ARegionType *art)
{
	PanelType *pt;
	
	pt = MEM_callocN(sizeof(PanelType), "spacetype sequencer panel gpencil");
	strcpy(pt->idname, "SEQUENCER_PT_gpencil");
	strcpy(pt->label, N_("Grease Pencil"));
	pt->draw_header = gpencil_panel_standard_header;
	pt->draw = gpencil_panel_standard;
	pt->poll = sequencer_grease_pencil_panel_poll;
	BLI_addtail(&art->paneltypes, pt);
}

/* **************** operator to open/close properties view ************* */

static int sequencer_properties(bContext *C, wmOperator *UNUSED(op))
{
	ScrArea *sa = CTX_wm_area(C);
	ARegion *ar = sequencer_has_buttons_region(sa);
	
	if (ar)
		ED_region_toggle_hidden(C, ar);

	return OPERATOR_FINISHED;
}

void SEQUENCER_OT_properties(wmOperatorType *ot)
{
	ot->name = "Properties";
	ot->idname = "SEQUENCER_OT_properties";
	ot->description = "Open sequencer properties panel";
	
	ot->exec = sequencer_properties;
	ot->poll = ED_operator_sequencer_active;
	
	/* flags */
	ot->flag = 0;
}

