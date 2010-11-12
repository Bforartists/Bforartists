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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Joshua Leung, Arystanbek Dyussenov
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <stdio.h>

#include "RNA_define.h"

#include "DNA_anim_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "BKE_utildefines.h"

#ifdef RNA_RUNTIME

#include "BKE_animsys.h"
#include "BKE_depsgraph.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_scene.h"
#include "BKE_writeavi.h"



static void rna_Scene_frame_set(Scene *scene, int frame, float subframe)
{
	scene->r.cfra= frame;
	scene->r.subframe= subframe;
	
	CLAMP(scene->r.cfra, MINAFRAME, MAXFRAME);
	scene_update_for_newframe(G.main, scene, (1<<20) - 1);

	WM_main_add_notifier(NC_SCENE|ND_FRAME, scene);
}

static void rna_Scene_update_tagged(Scene *scene)
{
	scene_update_tagged(G.main, scene);
}

static void rna_SceneRender_get_frame_path(RenderData *rd, int frame, char *name)
{
	if(BKE_imtype_is_movie(rd->imtype))
		BKE_makeanimstring(name, rd);
	else
		BKE_makepicstring(name, rd->pic, (frame==INT_MIN) ? rd->cfra : frame, rd->imtype, rd->scemode & R_EXTENSION);
}

#ifdef WITH_COLLADA

#include "../../collada/collada.h"

static void rna_Scene_collada_export(Scene *scene, char *filepath)
{
	collada_export(scene, filepath);
}

#endif

#else

void RNA_api_scene(StructRNA *srna)
{
	FunctionRNA *func;
	PropertyRNA *parm;

	func= RNA_def_function(srna, "frame_set", "rna_Scene_frame_set");
	RNA_def_function_ui_description(func, "Set scene frame updating all objects immediately.");
	parm= RNA_def_int(func, "frame", 0, MINAFRAME, MAXFRAME, "", "Frame number to set.", MINAFRAME, MAXFRAME);
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_float(func, "subframe", 0.0, 0.0, 1.0, "", "Sub-frame time, between 0.0 and 1.0", 0.0, 1.0);

	func= RNA_def_function(srna, "update", "rna_Scene_update_tagged");
	RNA_def_function_ui_description(func, "Update data tagged to be updated from previous access to data or operators.");

#ifdef WITH_COLLADA
	func= RNA_def_function(srna, "collada_export", "rna_Scene_collada_export");
	parm= RNA_def_string(func, "filepath", "", FILE_MAX, "File Path", "File path to write Collada file.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	RNA_def_property_subtype(parm, PROP_FILEPATH); /* allow non utf8 */
	RNA_def_function_ui_description(func, "Export to collada file.");
#endif
}

void RNA_api_scene_render(StructRNA *srna)
{
	FunctionRNA *func;
	PropertyRNA *parm;

	func= RNA_def_function(srna, "frame_path", "rna_SceneRender_get_frame_path");
	RNA_def_function_ui_description(func, "Return the absolute path to the filename to be written for a given frame.");
	parm= RNA_def_int(func, "frame", INT_MIN, INT_MIN, INT_MAX, "", "Frame number to use, if unset the current frame will be used.", MINAFRAME, MAXFRAME);
	parm= RNA_def_string(func, "filepath", "", FILE_MAX, "File Path", "the resulting filepath from the scenes render settings.");
	RNA_def_property_flag(parm, PROP_THICK_WRAP); /* needed for string return value */
	RNA_def_property_subtype(parm, PROP_FILEPATH); /* allow non utf8 */
	RNA_def_function_output(func, parm);
}

#endif

