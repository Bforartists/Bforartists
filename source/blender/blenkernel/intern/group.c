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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdio.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_action_types.h"
#include "DNA_effect_types.h"
#include "DNA_group_types.h"
#include "DNA_ID.h"
#include "DNA_ipo_types.h"
#include "DNA_material_types.h"
#include "DNA_object_types.h"
#include "DNA_nla_types.h"
#include "DNA_scene_types.h"

#include "BLI_blenlib.h"

#include "BKE_global.h"
#include "BKE_group.h"
#include "BKE_ipo.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_object.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

void free_group_object(GroupObject *go)
{
	MEM_freeN(go);
}


void free_group(Group *group)
{
	/* don't free group itself */
	GroupObject *go;
	
	while(group->gobject.first) {
		go= group->gobject.first;
		BLI_remlink(&group->gobject, go);
		free_group_object(go);
	}
}

void unlink_group(Group *group)
{
	Material *ma;
	Object *ob;
	
	for(ma= G.main->mat.first; ma; ma= ma->id.next) {
		if(ma->group==group)
			ma->group= NULL;
	}
	for(ob= G.main->object.first; ob; ob= ob->id.next) {
		bActionStrip *strip;
		PartEff *paf;
		
		if(ob->dup_group==group) {
			ob->dup_group= NULL;
		
			/* duplicator strips use a group object, we remove it */
			for(strip= ob->nlastrips.first; strip; strip= strip->next) {
				if(strip->object)
					strip->object= NULL;
			}
		}
		for(paf= ob->effect.first; paf; paf= paf->next) {
			if(paf->type==EFF_PARTICLE) {
				if(paf->group)
					paf->group= NULL;
			}
		}
	}
	group->id.us= 0;
}

Group *add_group()
{
	Group *group;
	
	group = alloc_libblock(&G.main->group, ID_GR, "Group");
	return group;
}

/* external */
void add_to_group(Group *group, Object *ob)
{
	GroupObject *go;
	
	if(group==NULL || ob==NULL) return;
	
	/* check if the object has been added already */
	for(go= group->gobject.first; go; go= go->next) {
		if(go->ob==ob) return;
	}
	
	go= MEM_callocN(sizeof(GroupObject), "groupobject");
	BLI_addtail( &group->gobject, go);
	
	go->ob= ob;
	
}

/* also used for ob==NULL */
void rem_from_group(Group *group, Object *ob)
{
	GroupObject *go, *gon;
	
	if(group==NULL) return;
	
	go= group->gobject.first;
	while(go) {
		gon= go->next;
		if(go->ob==ob) {
			BLI_remlink(&group->gobject, go);
			free_group_object(go);
		}
		go= gon;
	}
}

int object_in_group(Object *ob, Group *group)
{
	GroupObject *go;
	
	if(group==NULL || ob==NULL) return 0;
	
	for(go= group->gobject.first; go; go= go->next) {
		if(go->ob==ob) 
			return 1;
	}
	return 0;
}

Group *find_group(Object *ob)
{
	Group *group= G.main->group.first;
	
	while(group) {
		if(object_in_group(ob, group))
			return group;
		group= group->id.next;
	}
	return NULL;
}

void group_tag_recalc(Group *group)
{
	GroupObject *go;
	
	if(group==NULL) return;
	
	for(go= group->gobject.first; go; go= go->next) {
		if(go->ob) 
			go->ob->recalc= go->recalc;
	}
}

/* only replaces object strips or action when parent nla instructs it */
/* keep checking nla.c though, in case internal structure of strip changes */
static void group_replaces_nla(Object *parent, Object *target, char mode)
{
	static ListBase nlastrips={NULL, NULL};
	static bAction *action= NULL;
	static int done= 0;
	bActionStrip *strip, *nstrip;
	
	if(mode=='s') {
		
		for(strip= parent->nlastrips.first; strip; strip= strip->next) {
			if(strip->object==target) {
				if(done==0) {
					/* clear nla & action from object */
					nlastrips= target->nlastrips;
					target->nlastrips.first= target->nlastrips.last= NULL;
					action= target->action;
					target->action= NULL;
					target->nlaflag |= OB_NLA_OVERRIDE;
					done= 1;
				}
				nstrip= MEM_dupallocN(strip);
				BLI_addtail(&target->nlastrips, nstrip);
			}
		}
	}
	else if(mode=='e') {
		if(done) {
			BLI_freelistN(&target->nlastrips);
			target->nlastrips= nlastrips;
			target->action= action;
			
			nlastrips.first= nlastrips.last= NULL;	/* not needed, but yah... :) */
			action= NULL;
			done= 0;
		}
	}
}


/* puts all group members in local timing system, after this call
you can draw everything, leaves tags in objects to signal it needs further updating */
void group_handle_recalc_and_update(Object *parent, Group *group)
{
	GroupObject *go;
	
	/* if animated group... */
	if(parent->sf != 0.0f || parent->nlastrips.first) {
		int cfrao;
		
		/* switch to local time */
		cfrao= G.scene->r.cfra;
		G.scene->r.cfra -= (int)parent->sf;
		
		/* we need a DAG per group... */
		for(go= group->gobject.first; go; go= go->next) {
			if(go->ob && go->recalc) {
				go->ob->recalc= go->recalc;
				
				group_replaces_nla(parent, go->ob, 's');
				object_handle_update(go->ob);
				group_replaces_nla(parent, go->ob, 'e');
				
				/* leave recalc tags in case group members are in normal scene */
				go->ob->recalc= go->recalc;
			}
		}
		
		/* restore */
		G.scene->r.cfra= cfrao;
	}
	else {
		/* only do existing tags, as set by regular depsgraph */
		for(go= group->gobject.first; go; go= go->next) {
			if(go->ob) {
				if(go->ob->recalc) {
					object_handle_update(go->ob);
				}
			}
		}
	}
}

Object *group_get_member_with_action(Group *group, bAction *act)
{
	GroupObject *go;
	
	if(group==NULL || act==NULL) return NULL;
	
	for(go= group->gobject.first; go; go= go->next) {
		if(go->ob) {
			if(go->ob->action==act)
				return go->ob;
			if(go->ob->nlastrips.first) {
				bActionStrip *strip;
				
				for(strip= go->ob->nlastrips.first; strip; strip= strip->next) {
					if(strip->act==act)
						return go->ob;
				}
			}
		}
	}
	return NULL;
}

/* if group has NLA, we try to map the used objects in NLA to group members */
/* this assuming that object has received a new group link */
void group_relink_nla_objects(Object *ob)
{
	Group *group;
	GroupObject *go;
	bActionStrip *strip;
	
	if(ob==NULL || ob->dup_group==NULL) return;
	group= ob->dup_group;
	
	for(strip= ob->nlastrips.first; strip; strip= strip->next) {
		if(strip->object) {
			for(go= group->gobject.first; go; go= go->next) {
				if(go->ob) {
					if(strcmp(go->ob->id.name, strip->object->id.name)==0)
						break;
				}
			}
			if(go)
				strip->object= go->ob;
			else
				strip->object= NULL;
		}
			
	}
}

