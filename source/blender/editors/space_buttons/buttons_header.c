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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_buttons/buttons_header.c
 *  \ingroup spbuttons
 */


#include <string.h>
#include <stdio.h>

#include "BLI_blenlib.h"
#include "BLI_utildefines.h"

#include "BLF_translation.h"

#include "BKE_context.h"
#include "BKE_modifier.h"
#include "BKE_paint.h"
#include "BKE_scene.h"

#include "ED_buttons.h"
#include "ED_screen.h"
#include "ED_types.h"

#include "DNA_brush_types.h"
#include "DNA_object_force.h"
#include "DNA_object_types.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "buttons_intern.h"


#define B_CONTEXT_SWITCH    101
#define B_BUTSPREVIEW       102

static void set_texture_context(const bContext *C, SpaceButs *sbuts)
{
	Scene *scene = CTX_data_scene(C);

	if (BKE_scene_use_new_shading_nodes(scene)) {
		return;  /* No texture context in new shading mode */
	}

	if ((sbuts->mainb == BCONTEXT_WORLD) && ED_texture_context_check_world(C)) {
		sbuts->texture_context = SB_TEXC_WORLD;
	}
	else if ((sbuts->mainb == BCONTEXT_MATERIAL) && ED_texture_context_check_material(C)) {
		sbuts->texture_context = SB_TEXC_MATERIAL;
	}
	else if ((sbuts->mainb == BCONTEXT_DATA) && ED_texture_context_check_lamp(C)) {
		sbuts->texture_context = SB_TEXC_LAMP;
	}
	else if ((sbuts->mainb == BCONTEXT_PARTICLE) && ED_texture_context_check_particles(C)) {
		sbuts->texture_context = SB_TEXC_PARTICLES;
	}
	/* Else, just be sure that current context is valid! */
	else {
		buttons_check_texture_context(C, sbuts);
	}
}

static void do_buttons_buttons(bContext *C, void *UNUSED(arg), int event)
{
	SpaceButs *sbuts = CTX_wm_space_buts(C);

	if (!sbuts) /* editor type switch */
		return;

	switch (event) {
		case B_CONTEXT_SWITCH:
		case B_BUTSPREVIEW:
			ED_area_tag_redraw(CTX_wm_area(C));

			set_texture_context(C, sbuts);

			sbuts->preview = 1;
			break;
	}

	sbuts->mainbuser = sbuts->mainb;
}

#define BUT_UNIT_X (UI_UNIT_X + 2 * U.pixelsize)

void buttons_header_buttons(const bContext *C, ARegion *ar)
{
	SpaceButs *sbuts = CTX_wm_space_buts(C);
	uiBlock *block;
	uiBut *but;
	int headery = ED_area_headersize();
	int xco, yco = 0.5f * (headery - UI_UNIT_Y);

	buttons_context_compute(C, sbuts);
	
	block = uiBeginBlock(C, ar, __func__, UI_EMBOSS);
	uiBlockSetHandleFunc(block, do_buttons_buttons, NULL);
	
	xco = ED_area_header_switchbutton(C, block, yco);
	
	uiBlockSetEmboss(block, UI_EMBOSS);

	xco -= UI_UNIT_X;

	/* Default panels */

	uiBlockBeginAlign(block);

#define BUTTON_HEADER_CTX(_ctx, _icon, _tip) \
	if (sbuts->pathflag & (1 << _ctx)) { \
		but = uiDefIconButS(block, ROW, B_CONTEXT_SWITCH, _icon, xco += BUT_UNIT_X, yco, BUT_UNIT_X, UI_UNIT_Y, \
		                    &(sbuts->mainb), 0.0, (float)_ctx, 0, 0, TIP_(_tip)); \
		uiButClearFlag(but, UI_BUT_UNDO); \
	} (void)0

	BUTTON_HEADER_CTX(BCONTEXT_RENDER, ICON_SCENE, N_("Render"));
	BUTTON_HEADER_CTX(BCONTEXT_RENDER_LAYER, ICON_RENDERLAYERS, N_("Render Layers"));
	BUTTON_HEADER_CTX(BCONTEXT_SCENE, ICON_SCENE_DATA, N_("Scene"));
	BUTTON_HEADER_CTX(BCONTEXT_WORLD, ICON_WORLD, N_("World"));
	BUTTON_HEADER_CTX(BCONTEXT_OBJECT, ICON_OBJECT_DATA, N_("Object"));
	BUTTON_HEADER_CTX(BCONTEXT_CONSTRAINT, ICON_CONSTRAINT, N_("Object Constraints"));
	BUTTON_HEADER_CTX(BCONTEXT_MODIFIER, ICON_MODIFIER, N_("Object Modifiers"));
	BUTTON_HEADER_CTX(BCONTEXT_DATA, sbuts->dataicon, N_("Object Data"));
	BUTTON_HEADER_CTX(BCONTEXT_BONE, ICON_BONE_DATA, N_("Bone"));
	BUTTON_HEADER_CTX(BCONTEXT_BONE_CONSTRAINT, ICON_CONSTRAINT_BONE, N_("Bone Constraints"));
	BUTTON_HEADER_CTX(BCONTEXT_MATERIAL, ICON_MATERIAL, N_("Material"));
	BUTTON_HEADER_CTX(BCONTEXT_TEXTURE, ICON_TEXTURE, N_("Textures"));
	BUTTON_HEADER_CTX(BCONTEXT_PARTICLE, ICON_PARTICLES, N_("Particles"));
	BUTTON_HEADER_CTX(BCONTEXT_PHYSICS, ICON_PHYSICS, N_("Physics"));

#undef BUTTON_HEADER_CTX

	xco += BUT_UNIT_X;
	
	uiBlockEndAlign(block);
	
	/* always as last  */
	UI_view2d_totRect_set(&ar->v2d, xco + (UI_UNIT_X / 2), BLI_rctf_size_y(&ar->v2d.tot));
	
	uiEndBlock(C, block);
	uiDrawBlock(C, block);
}


