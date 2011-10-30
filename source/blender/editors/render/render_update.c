/*
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. 
 *
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
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/render/render_update.c
 *  \ingroup edrend
 */

#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_lamp_types.h"
#include "DNA_material_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_view3d_types.h"
#include "DNA_world_types.h"

#include "BLI_utildefines.h"

#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_icons.h"
#include "BKE_image.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_node.h"
#include "BKE_scene.h"
#include "BKE_texture.h"
#include "BKE_world.h"

#include "GPU_material.h"

#include "ED_node.h"
#include "ED_render.h"

#include "render_intern.h"	// own include

/***************************** Updates ***********************************
 * ED_render_id_flush_update gets called from DAG_id_tag_update, to do *
 * editor level updates when the ID changes. when these ID blocks are in *
 * the dependency graph, we can get rid of the manual dependency checks  */

static int mtex_use_tex(MTex **mtex, int tot, Tex *tex)
{
	int a;

	if(!mtex)
		return 0;

	for(a=0; a<tot; a++)
		if(mtex[a] && mtex[a]->tex == tex)
			return 1;
	
	return 0;
}

static int nodes_use_tex(bNodeTree *ntree, Tex *tex)
{
	bNode *node;

	for(node=ntree->nodes.first; node; node= node->next) {
		if(node->id) {
			if(node->id == (ID*)tex) {
				return 1;
			}
			else if(node->type==NODE_GROUP) {
				if(nodes_use_tex((bNodeTree *)node->id, tex))
					return 1;
			}
		}
	}

	return 0;
}

static void material_changed(Main *UNUSED(bmain), Material *ma)
{
	/* icons */
	BKE_icon_changed(BKE_icon_getid(&ma->id));

	/* glsl */
	if(ma->gpumaterial.first)
		GPU_material_free(ma);
}

static void texture_changed(Main *bmain, Tex *tex)
{
	Material *ma;
	Lamp *la;
	World *wo;
	Scene *scene;
	bNode *node;

	/* icons */
	BKE_icon_changed(BKE_icon_getid(&tex->id));

	/* find materials */
	for(ma=bmain->mat.first; ma; ma=ma->id.next) {
		if(mtex_use_tex(ma->mtex, MAX_MTEX, tex));
		else if(ma->use_nodes && ma->nodetree && nodes_use_tex(ma->nodetree, tex));
		else continue;

		BKE_icon_changed(BKE_icon_getid(&ma->id));

		if(ma->gpumaterial.first)
			GPU_material_free(ma);
	}

	/* find lamps */
	for(la=bmain->lamp.first; la; la=la->id.next) {
		if(mtex_use_tex(la->mtex, MAX_MTEX, tex));
		else continue;

		BKE_icon_changed(BKE_icon_getid(&la->id));
	}

	/* find worlds */
	for(wo=bmain->world.first; wo; wo=wo->id.next) {
		if(mtex_use_tex(wo->mtex, MAX_MTEX, tex));
		else continue;

		BKE_icon_changed(BKE_icon_getid(&wo->id));
	}

	/* find compositing nodes */
	for(scene=bmain->scene.first; scene; scene=scene->id.next) {
		if(scene->use_nodes && scene->nodetree) {
			for(node=scene->nodetree->nodes.first; node; node=node->next) {
				if(node->id == &tex->id)
					ED_node_changed_update(&scene->id, node);
			}
		}
	}
}

static void lamp_changed(Main *bmain, Lamp *la)
{
	Object *ob;
	Material *ma;

	/* icons */
	BKE_icon_changed(BKE_icon_getid(&la->id));

	/* glsl */
	for(ob=bmain->object.first; ob; ob=ob->id.next)
		if(ob->data == la && ob->gpulamp.first)
			GPU_lamp_free(ob);

	for(ma=bmain->mat.first; ma; ma=ma->id.next)
		if(ma->gpumaterial.first)
			GPU_material_free(ma);
}

static void world_changed(Main *bmain, World *wo)
{
	Material *ma;

	/* icons */
	BKE_icon_changed(BKE_icon_getid(&wo->id));

	/* glsl */
	for(ma=bmain->mat.first; ma; ma=ma->id.next)
		if(ma->gpumaterial.first)
			GPU_material_free(ma);
}

static void image_changed(Main *bmain, Image *ima)
{
	Tex *tex;

	/* icons */
	BKE_icon_changed(BKE_icon_getid(&ima->id));

	/* textures */
	for(tex=bmain->tex.first; tex; tex=tex->id.next)
		if(tex->ima == ima)
			texture_changed(bmain, tex);
}

static void scene_changed(Main *bmain, Scene *UNUSED(scene))
{
	Object *ob;
	Material *ma;

	/* glsl */
	for(ob=bmain->object.first; ob; ob=ob->id.next)
		if(ob->gpulamp.first)
			GPU_lamp_free(ob);

	for(ma=bmain->mat.first; ma; ma=ma->id.next)
		if(ma->gpumaterial.first)
			GPU_material_free(ma);
}

void ED_render_id_flush_update(Main *bmain, ID *id)
{
	if(!id)
		return;

	switch(GS(id->name)) {
		case ID_MA:
			material_changed(bmain, (Material*)id);
			break;
		case ID_TE:
			texture_changed(bmain, (Tex*)id);
			break;
		case ID_WO:
			world_changed(bmain, (World*)id);
			break;
		case ID_LA:
			lamp_changed(bmain, (Lamp*)id);
			break;
		case ID_IM:
			image_changed(bmain, (Image*)id);
			break;
		case ID_SCE:
			scene_changed(bmain, (Scene*)id);
			break;
		default:
			break;
	}
}

