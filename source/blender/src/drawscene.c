/**
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 * drawing graphics and editing
 */
	
#include <math.h>

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "DNA_scene_types.h"
#include "DNA_space_types.h"
#include "DNA_screen_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view3d_types.h"

#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_scene.h"

#include "BDR_editobject.h"

#include "BIF_space.h"
#include "BIF_drawscene.h"
#include "BIF_poseobject.h"

#include "BSE_view.h"

#include "blendef.h" /* old */
#include "mydevice.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

void set_scene(Scene *sce)		/* also see scene.c: set_scene_bg() */
{
	bScreen *sc;
	
	if( G.obedit) exit_editmode(2);
	if(G.obpose) exit_posemode(1);

	G.scene= sce;

	sc= G.main->screen.first;
	while(sc) {
		if((U.flag & USER_SCENEGLOBAL) || sc==G.curscreen) {
		
			if(sce != sc->scene) {
				/* all areas endlocalview */
				ScrArea *sa= sc->areabase.first;
				while(sa) {
					endlocalview(sa);
					sa= sa->next;
				}		
				sc->scene= sce;
			}
			
		}
		sc= sc->id.next;
	}
	
	copy_view3d_lock(0);	/* space.c */

	/* are there cameras in the views that are not in the scene? */
	sc= G.main->screen.first;
	while(sc) {
		if( (U.flag & USER_SCENEGLOBAL) || sc==G.curscreen) {
			ScrArea *sa= sc->areabase.first;
			while(sa) {
				SpaceLink *sl= sa->spacedata.first;
				while(sl) {
					if(sl->spacetype==SPACE_VIEW3D) {
						View3D *v3d= (View3D*) sl;
						if (!v3d->camera || !object_in_scene(v3d->camera, sce)) {
							v3d->camera= scene_find_camera(sc->scene);
							if (sc==G.curscreen) handle_view3d_lock();
							if (!v3d->camera && v3d->persp>1) v3d->persp= 1;
						}
					}
					sl= sl->next;
				}
				sa= sa->next;
			}
		}
		sc= sc->id.next;
	}

	set_scene_bg(G.scene);	
	
	/* complete redraw */
	allqueue(REDRAWALL, 0);
	allqueue(REDRAWDATASELECT, 0);	/* does a remake */
}


