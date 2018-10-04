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
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 *
 */

/** \file blender/blenloader/intern/versioning_defaults.c
 *  \ingroup blenloader
 */

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"
#include "BLI_listbase.h"
#include "BLI_math.h"
#include "BLI_string.h"

#include "DNA_gpencil_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_userdef_types.h"
#include "DNA_object_types.h"
#include "DNA_workspace_types.h"

#include "BKE_colortools.h"
#include "BKE_layer.h"
#include "BKE_main.h"
#include "BKE_node.h"
#include "BKE_screen.h"
#include "BKE_workspace.h"

#include "BLO_readfile.h"

/**
 * Override values in in-memory startup.blend, avoids resaving for small changes.
 */
void BLO_update_defaults_userpref_blend(void)
{
	/* default so DPI is detected automatically */
	U.dpi = 0;
	U.ui_scale = 1.0f;

#ifdef WITH_PYTHON_SECURITY
	/* use alternative setting for security nuts
	 * otherwise we'd need to patch the binary blob - startup.blend.c */
	U.flag |= USER_SCRIPT_AUTOEXEC_DISABLE;
#else
	U.flag &= ~USER_SCRIPT_AUTOEXEC_DISABLE;
#endif

	/* Ignore the theme saved in the blend file,
	 * instead use the theme from 'userdef_default_theme.c' */
	{
		bTheme *theme = U.themes.first;
		memcpy(theme, &U_theme_default, sizeof(bTheme));
	}
}

/**
 * Update defaults in startup.blend, without having to save and embed the file.
 * This function can be emptied each time the startup.blend is updated. */
void BLO_update_defaults_startup_blend(Main *bmain, const char *app_template)
{
	/* For all startup.blend files. */
	for (bScreen *screen = bmain->screen.first; screen; screen = screen->id.next) {
		for (ScrArea *area = screen->areabase.first; area; area = area->next) {
			for (ARegion *ar = area->regionbase.first; ar; ar = ar->next) {
				/* Remove all stored panels, we want to use defaults (order, open/closed) as defined by UI code here! */
				BKE_area_region_panels_free(&ar->panels);

				/* some toolbars have been saved as initialized,
				 * we don't want them to have odd zoom-level or scrolling set, see: T47047 */
				if (ELEM(ar->regiontype, RGN_TYPE_UI, RGN_TYPE_TOOLS, RGN_TYPE_TOOL_PROPS)) {
					ar->v2d.flag &= ~V2D_IS_INITIALISED;
				}
			}
		}
	}

	if (app_template == NULL) {
		/* Clear all tools to use default options instead, ignore the tool saved in the file. */
		for (WorkSpace *workspace = bmain->workspaces.first; workspace; workspace = workspace->id.next) {
			while (!BLI_listbase_is_empty(&workspace->tools)) {
				BKE_workspace_tool_remove(workspace, workspace->tools.first);
			}
		}
	}

	/* For 2D animation template. */
	if (app_template && STREQ(app_template, "2D_Animation")) {
		for (WorkSpace *workspace = bmain->workspaces.first; workspace; workspace = workspace->id.next) {
			const char *name = workspace->id.name + 2;

			if (STREQ(name, "Drawing")) {
				workspace->object_mode = OB_MODE_GPENCIL_PAINT;
			}
		}
		/* set object in drawing mode */
		for (Object *object = bmain->object.first; object; object = object->id.next) {
			if (object->type == OB_GPENCIL) {
				bGPdata *gpd = (bGPdata *)object->data;
				object->mode = OB_MODE_GPENCIL_PAINT;
				gpd->flag |= GP_DATA_STROKE_PAINTMODE;
				break;
			}
		}

		/* Be sure curfalloff is initializated */
		for (Scene *scene = bmain->scene.first; scene; scene = scene->id.next) {
			ToolSettings *ts = scene->toolsettings;
			if (ts->gp_sculpt.cur_falloff == NULL) {
				ts->gp_sculpt.cur_falloff = curvemapping_add(1, 0.0f, 0.0f, 1.0f, 1.0f);
				CurveMapping *gp_falloff_curve = ts->gp_sculpt.cur_falloff;
				curvemapping_initialize(gp_falloff_curve);
				curvemap_reset(gp_falloff_curve->cm,
					&gp_falloff_curve->clipr,
					CURVE_PRESET_GAUSS,
					CURVEMAP_SLOPE_POSITIVE);
			}
		}
	}

	/* For all builtin templates shipped with Blender. */
	bool builtin_template = !app_template ||
	                        STREQ(app_template, "2D_Animation") ||
	                        STREQ(app_template, "Sculpting") ||
	                        STREQ(app_template, "VFX") ||
	                        STREQ(app_template, "Video_Editing");

	if (builtin_template) {
		for (bScreen *screen = bmain->screen.first; screen; screen = screen->id.next) {
			/* Hide channels in timelines. */
			for (ScrArea *sa = screen->areabase.first; sa; sa = sa->next) {
				SpaceAction *saction = (sa->spacetype == SPACE_ACTION) ? sa->spacedata.first : NULL;

				if (saction && saction->mode == SACTCONT_TIMELINE) {
					for (ARegion *ar = sa->regionbase.first; ar; ar = ar->next) {
						if (ar->regiontype == RGN_TYPE_CHANNELS) {
							ar->flag |= RGN_FLAG_HIDDEN;
						}
					}
				}
			}
		}

		for (Scene *scene = bmain->scene.first; scene; scene = scene->id.next) {
			BLI_strncpy(scene->r.engine, RE_engine_id_BLENDER_EEVEE, sizeof(scene->r.engine));

			scene->r.cfra = 1.0f;
			scene->r.displaymode = R_OUTPUT_WINDOW;

			/* Don't enable compositing nodes. */
			if (scene->nodetree) {
				ntreeFreeTree(scene->nodetree);
				MEM_freeN(scene->nodetree);
				scene->nodetree = NULL;
				scene->use_nodes = false;
			}

			/* Rename render layers. */
			BKE_view_layer_rename(bmain, scene, scene->view_layers.first, "View Layer");
		}
	}
}
