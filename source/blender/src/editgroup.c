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
 */

#include <string.h>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "DNA_group_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_view3d_types.h"

#include "BKE_depsgraph.h"
#include "BKE_group.h"
#include "BKE_global.h"
#include "BKE_main.h"

#include "BIF_interface.h"
#include "BIF_editgroup.h"
#include "BIF_space.h"
#include "BIF_toolbox.h"

#include "blendef.h"
#include "mydevice.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

void add_selected_to_group(Group *group)
{
	Base *base;
	
	for(base=FIRSTBASE; base; base= base->next) {
		if TESTBASE(base) {
			add_to_group(group, base->object);
			base->object->flag |= OB_FROMGROUP;
			base->flag |= OB_FROMGROUP;
		}
	}
	
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
	DAG_scene_sort(G.scene);
	BIF_undo_push("Add to Group");
}

void rem_selected_from_group(void)
{
	Base *base;
	Group *group;
	
	for(base=FIRSTBASE; base; base= base->next) {
		if TESTBASE(base) {

			while( (group = find_group(base->object)) ) {
				rem_from_group(group, base->object);
			}
			base->object->flag &= ~OB_FROMGROUP;
			base->flag &= ~OB_FROMGROUP;
		}
	}
	
	DAG_scene_sort(G.scene);
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
	BIF_undo_push("Remove from Group");
}

void group_operation_with_menu(void)
{
	Base *base;
	Group *group= NULL;
	int mode;
	
	for(base=FIRSTBASE; base; base= base->next) {
		if TESTBASE(base) {
			group= find_group(base->object);
			if(group) break;
		}
	}
	
	if(group && group->id.lib) {
		error("Cannot edit library data");
		return;
	}
	
	if(base)
		mode= pupmenu("Groups %t|Add to current Group %x3|Add to New Group %x1|Remove from all Groups %x2");
	else
		mode= pupmenu("Groups %t|Add to New Group %x1|Remove from all Groups %x2");
	
	if(mode>0) {
		if(group==NULL || mode==1) group= add_group();
		
		if(mode==1 || mode==3) add_selected_to_group(group);
		else if(mode==2) rem_selected_from_group();
	}
}

