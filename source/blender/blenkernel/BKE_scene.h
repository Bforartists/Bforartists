/**
 * blenlib/BKE_scene.h (mar-2001 nzc)
 *	
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
#ifndef BKE_SCENE_H
#define BKE_SCENE_H

struct Scene;
struct Object;
struct Base;
struct AviCodecData;
struct QuicktimeCodecData;

/* sequence related defines */
#define WHILE_SEQ(base)	{											\
	int totseq_, seq_; Sequence **seqar;	\
		build_seqar( base,  &seqar, &totseq_);	\
			for(seq_ = 0; seq_ < totseq_; seq_++) {	\
				seq= seqar[seq_];
				
				
#define END_SEQ					}						\
				if(seqar) MEM_freeN(seqar);		\
}


#define SETLOOPER(s, b) sce= s, b= sce->base.first; b; b= (b->next?b->next:sce->set?(sce=sce->set)->base.first:NULL)


void free_avicodecdata(struct AviCodecData *acd);
void free_qtcodecdata(struct QuicktimeCodecData *acd);

void free_scene(struct Scene *me);
struct Scene *add_scene(char *name);
struct Base *object_in_scene(struct Object *ob, struct Scene *sce);

void set_scene_bg(struct Scene *sce);
void set_scene_name(char *name);

int next_object(int val, struct Base **base, struct Object **ob);
struct Object *scene_find_camera(struct Scene *sc);

struct Base *scene_add_base(struct Scene *sce, struct Object *ob);
void scene_deselect_all(struct Scene *sce);
void scene_select_base(struct Scene *sce, struct Base *selbase);

void scene_update_for_newframe(struct Scene *sce, unsigned int lay);

void scene_add_render_layer(struct Scene *sce);

#endif

