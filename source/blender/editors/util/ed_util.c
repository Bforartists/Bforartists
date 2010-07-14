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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BLI_blenlib.h"
#include "BLI_editVert.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_main.h"

#include "ED_armature.h"
#include "ED_mesh.h"
#include "ED_object.h"
#include "ED_sculpt.h"
#include "ED_util.h"

#include "UI_interface.h"

/* ********* general editor util funcs, not BKE stuff please! ********* */

void ED_editors_init(bContext *C)
{
	Main *bmain= CTX_data_main(C);
	Scene *sce= CTX_data_scene(C);
	Object *ob, *obact= (sce && sce->basact)? sce->basact->object: NULL;
	ID *data;

	/* toggle on modes for objects that were saved with these enabled. for
	   e.g. linked objects we have to ensure that they are actually the
	   active object in this scene. */
	for(ob=bmain->object.first; ob; ob=ob->id.next) {
		int mode= ob->mode;

		if(mode && (mode != OB_MODE_POSE)) {
			ob->mode= 0;
			data= ob->data;

			if(ob == obact && !ob->id.lib && !(data && data->lib))
				ED_object_toggle_modes(C, mode);
		}
	}
}

/* frees all editmode stuff */
void ED_editors_exit(bContext *C)
{
	Scene *sce;
	
	/* frees all editmode undos */
	undo_editmode_clear();
	ED_undo_paint_free();
	
	for(sce=G.main->scene.first; sce; sce= sce->id.next) {
		if(sce->obedit) {
			Object *ob= sce->obedit;
		
			/* global in meshtools... */
			mesh_octree_table(NULL, NULL, NULL, 'e');
			mesh_mirrtopo_table(NULL, 'e');
			
			if(ob) {
				if(ob->type==OB_MESH) {
					Mesh *me= ob->data;
					if(me->edit_mesh) {
						free_editMesh(me->edit_mesh);
						MEM_freeN(me->edit_mesh);
						me->edit_mesh= NULL;
					}
				}
				else if(ob->type==OB_ARMATURE) {
					ED_armature_edit_free(ob);
				}
				else if(ob->type==OB_FONT) {
					//			free_editText();
				}
				//		else if(ob->type==OB_MBALL) 
				//			BLI_freelistN(&editelems);
				//	free_editLatt();
				//	free_posebuf();		// XXX this is still a global...
			}
		}
		else if(sce->basact && sce->basact->object) {
			Object *ob= sce->basact->object;
			
			/* if weight-painting is on, free mesh octree data */
			if(ob->mode & OB_MODE_WEIGHT_PAINT) {
				mesh_octree_table(NULL, NULL, NULL, 'e');
				mesh_mirrtopo_table(NULL, 'e');
			}
		}
	}
	
}


/* ***** XXX: functions are using old blender names, cleanup later ***** */


/* now only used in 2d spaces, like time, ipo, nla, sima... */
/* XXX shift/ctrl not configurable */
void apply_keyb_grid(int shift, int ctrl, float *val, float fac1, float fac2, float fac3, int invert)
{
	/* fac1 is for 'nothing', fac2 for CTRL, fac3 for SHIFT */
	if(invert)
		ctrl= !ctrl;
	
	if(ctrl && shift) {
		if(fac3!= 0.0) *val= fac3*floor(*val/fac3 +.5);
	}
	else if(ctrl) {
		if(fac2!= 0.0) *val= fac2*floor(*val/fac2 +.5);
	}
	else {
		if(fac1!= 0.0) *val= fac1*floor(*val/fac1 +.5);
	}
}


int GetButStringLength(char *str) 
{
	int rt;
	
	rt= UI_GetStringWidth(str);
	
	return rt + 15;
}

