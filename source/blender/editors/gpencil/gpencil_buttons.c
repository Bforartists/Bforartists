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
 * The Original Code is Copyright (C) 2008, Blender Foundation, Joshua Leung
 * This is a new part of Blender
 *
 * Contributor(s): Joshua Leung
 *
 * ***** END GPL LICENSE BLOCK *****
 */
 
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stddef.h>

#include "MEM_guardedalloc.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"

#include "DNA_gpencil_types.h"
#include "DNA_listBase.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_userdef_types.h"
#include "DNA_windowmanager_types.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_gpencil.h"
#include "BKE_utildefines.h"

#include "WM_api.h"
#include "WM_types.h"

#include "RNA_access.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "ED_gpencil.h"
#include "ED_sequencer.h"
#include "ED_util.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "gpencil_intern.h"

/* ************************************************** */
/* GREASE PENCIL PANEL-UI DRAWING */

/* Every space which implements Grease-Pencil functionality should have a panel
 * for the settings. All of the space-dependent parts should be coded in the panel
 * code for that space, but the rest is all handled by generic panel here.
 */

/* ------- Callbacks ----------- */
/* These are just 'dummy wrappers' around gpencil api calls */


/* make layer active one after being clicked on */
void gp_ui_activelayer_cb (bContext *C, void *gpd, void *gpl)
{
	gpencil_layer_setactive(gpd, gpl);
	
	WM_event_add_notifier(C, NC_SCREEN|ND_GPENCIL|NA_EDITED, NULL); // XXX please work!
}

/* delete 'active' layer */
void gp_ui_dellayer_cb (bContext *C, void *gpd, void *gpl)
{
	/* make sure the layer we want to remove is the active one */
	gpencil_layer_setactive(gpd, gpl); 
	gpencil_layer_delactive(gpd);
	
	WM_event_add_notifier(C, NC_SCREEN|ND_GPENCIL|NA_EDITED, NULL); // XXX please work!
}

/* ------- Drawing Code ------- */

/* draw the controls for a given layer */
static void gp_drawui_layer (uiLayout *layout, bGPdata *gpd, bGPDlayer *gpl)
{
	uiLayout *box=NULL, *split=NULL;
	uiLayout *col=NULL, *subcol=NULL;
	uiLayout *row=NULL, *subrow=NULL;
	uiBlock *block;
	uiBut *but;
	PointerRNA ptr;
	
	/* make pointer to layer data */
	RNA_pointer_create((ID *)gpd, &RNA_GPencilLayer, gpl, &ptr);
	
	/* unless button has own callback, it adds this callback to button */
	block= uiLayoutGetBlock(layout);
	uiBlockSetFunc(block, gp_ui_activelayer_cb, gpd, gpl);
	
	/* draw header ---------------------------------- */
	/* get layout-row + UI-block for header */
	box= uiLayoutBox(layout);
	
	row= uiLayoutRow(box, 0);
	block= uiLayoutGetBlock(row); // err...
	
	uiBlockSetEmboss(block, UI_EMBOSSN);
	
	/* left-align ............................... */
	subrow= uiLayoutRow(row, 1);
	uiLayoutSetAlignment(subrow, UI_LAYOUT_ALIGN_LEFT);
	
	/* active */
	uiItemR(subrow, "", ICON_RADIOBUT_OFF, &ptr, "active", UI_ITEM_R_TOGGLE); // XXX we need to set it to toggle to get icon
	
	/* locked */
	uiItemR(subrow, "", ICON_UNLOCKED, &ptr, "locked", UI_ITEM_R_TOGGLE); // XXX we need to set it to toggle to get icon
	
	/* when layer is locked or hidden, only draw header */
	if (gpl->flag & (GP_LAYER_LOCKED|GP_LAYER_HIDE)) {
		char name[256]; /* gpl->info is 128, but we need space for 'locked/hidden' as well */
		
		/* visibility button (only if hidden but not locked!) */
		if ((gpl->flag & GP_LAYER_HIDE) && !(gpl->flag & GP_LAYER_LOCKED))
			uiItemR(subrow, "", ICON_RESTRICT_VIEW_OFF, &ptr, "hide", UI_ITEM_R_TOGGLE); // XXX we need to set it to toggle to get icon
		
		/* name */
		if (gpl->flag & GP_LAYER_HIDE)
			sprintf(name, "%s (Hidden)", gpl->info);
		else
			sprintf(name, "%s (Locked)", gpl->info);
		uiItemL(subrow, name, 0);
			
		/* delete button (only if hidden but not locked!) */
		if ((gpl->flag & GP_LAYER_HIDE) & !(gpl->flag & GP_LAYER_LOCKED)) {
			/* right-align ............................... */
			subrow= uiLayoutRow(row, 1);
			uiLayoutSetAlignment(subrow, UI_LAYOUT_ALIGN_RIGHT);
			block= uiLayoutGetBlock(subrow); // XXX... err...
			
			but= uiDefIconBut(block, BUT, 0, ICON_X, 0, 0, UI_UNIT_X, UI_UNIT_Y, NULL, 0.0, 0.0, 0.0, 0.0, "Delete layer");
			uiButSetFunc(but, gp_ui_dellayer_cb, gpd, gpl);
		}	
		uiBlockSetEmboss(block, UI_EMBOSS);
	}
	else {
		/* draw rest of header -------------------------------- */
		/* visibility button */
		uiItemR(subrow, "", ICON_RESTRICT_VIEW_OFF, &ptr, "hide", UI_ITEM_R_TOGGLE); // XXX we need to set it to toggle to get icon
		
		uiBlockSetEmboss(block, UI_EMBOSS);
		
		/* name */
		uiItemR(subrow, "", 0, &ptr, "info", 0);
		
		/* delete 'button' */
		uiBlockSetEmboss(block, UI_EMBOSSN);
			/* right-align ............................... */
			subrow= uiLayoutRow(row, 1);
			uiLayoutSetAlignment(subrow, UI_LAYOUT_ALIGN_RIGHT);
			block= uiLayoutGetBlock(subrow); // XXX... err...
			
			but= uiDefIconBut(block, BUT, 0, ICON_X, 0, 0, UI_UNIT_X, UI_UNIT_Y, NULL, 0.0, 0.0, 0.0, 0.0, "Delete layer");
			uiButSetFunc(but, gp_ui_dellayer_cb, gpd, gpl);
		uiBlockSetEmboss(block, UI_EMBOSS);
		
		
		/* new backdrop ----------------------------------- */
		box= uiLayoutBox(layout);
		split= uiLayoutSplit(box, 0.5f);
		
		
		/* draw settings ---------------------------------- */
		/* left column ..................... */
		col= uiLayoutColumn(split, 0);
		
		/* color */
		subcol= uiLayoutColumn(col, 1);
			uiItemR(subcol, "", 0, &ptr, "color", 0);
			uiItemR(subcol, NULL, 0, &ptr, "opacity", UI_ITEM_R_SLIDER);
			
		/* stroke thickness */
		subcol= uiLayoutColumn(col, 1);
			uiItemR(subcol, NULL, 0, &ptr, "line_thickness", UI_ITEM_R_SLIDER);
		
		/* debugging options */
		if (G.f & G_DEBUG) {
			// XXX this option hasn't been wrapped yet... since it's just debug
			//subcol= uiLayoutColumn(col, 1);
			//	uiItemR(subrow, NULL, 0, &ptr, "show_points", 0);
		}
		
		/* right column ................... */
		col= uiLayoutColumn(split, 0);
		
		/* onion-skinning */
		subcol= uiLayoutColumn(col, 1);
			uiItemR(subcol, "Onion Skinning", 0, &ptr, "use_onion_skinning", 0);
			uiItemR(subcol, "GStep", 0, &ptr, "max_ghost_range", 0); // XXX shorter name here? (i.e. GStep)
		
		/* additional options... */
		// None at the moment...
	}
} 

/* Draw the contents for a grease-pencil panel*/
static void draw_gpencil_panel (bContext *C, uiLayout *layout, bGPdata *gpd, PointerRNA *ctx_ptr)
{
	bGPDlayer *gpl;
	uiLayout *col;
	
	/* draw gpd settings first ------------------------------------- */
	col= uiLayoutColumn(layout, 1);
		/* current Grease Pencil block */
		// TODO: show some info about who owns this?
			// XXX: this template doesn't show up!
		uiTemplateID(col, C, ctx_ptr, "grease_pencil", "GPENCIL_OT_data_new", "GPENCIL_OT_data_unlink");
		
		/* add new layer button */
		uiItemO(col, NULL, 0, "GPENCIL_OT_layer_add");
	
	/* 'view align' button (naming depends on context) */
#if 0 // XXX for now, this is enabled by default anyways
	if (sa->spacetype == SPACE_VIEW3D)
		uiDefButBitI(block, TOG, GP_DATA_VIEWALIGN, B_REDR, "Sketch in 3D", 170, 205, 150, 20, &gpd->flag, 0, 0, 0, 0, "New strokes are added in 3D-space");
	else
		uiDefButBitI(block, TOG, GP_DATA_VIEWALIGN, B_REDR, "Stick to View", 170, 205, 150, 20, &gpd->flag, 0, 0, 0, 0, "New strokes are added on 2d-canvas");
#endif
	
	/* draw each layer --------------------------------------------- */
	for (gpl= gpd->layers.first; gpl; gpl= gpl->next) {
		col= uiLayoutColumn(layout, 1);
			gp_drawui_layer(col, gpd, gpl);
	}
}	


/* Standard panel to be included whereever Grease Pencil is used... */
void gpencil_panel_standard(const bContext *C, Panel *pa)
{
	bGPdata **gpd_ptr = NULL;
	PointerRNA ptr;
	
	//if (v3d->flag2 & V3D_DISPGP)... etc.
	
	/* get pointer to Grease Pencil Data */
	gpd_ptr= gpencil_data_get_pointers((bContext *)C, &ptr);
	
	if (gpd_ptr && *gpd_ptr)
		draw_gpencil_panel((bContext *)C, pa->layout, *gpd_ptr, &ptr);
}

/* ************************************************** */
