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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Jörg Müller.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/blenkernel/intern/speaker.c
 *  \ingroup bke
 */

#include "DNA_object_types.h"
#include "DNA_sound_types.h"
#include "DNA_speaker_types.h"

#include "BLI_math.h"

#include "BKE_animsys.h"
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_speaker.h"

void *add_speaker(const char *name)
{
	Speaker *spk;

	spk=  alloc_libblock(&G.main->speaker, ID_SPK, name);

	spk->attenuation = 1.0f;
	spk->cone_angle_inner = 360.0f;
	spk->cone_angle_outer = 360.0f;
	spk->cone_volume_outer = 1.0f;
	spk->distance_max = FLT_MAX;
	spk->distance_reference = 1.0f;
	spk->flag = 0;
	spk->pitch = 1.0f;
	spk->sound = NULL;
	spk->volume = 1.0f;
	spk->volume_max = 1.0f;
	spk->volume_min = 0.0f;

	return spk;
}

Speaker *copy_speaker(Speaker *spk)
{
	Speaker *spkn;

	spkn= copy_libblock(spk);
	if(spkn->sound)
		spkn->sound->id.us++;

	return spkn;
}

void make_local_speaker(Speaker *spk)
{
	Main *bmain= G.main;
	Object *ob;
	int local=0, lib=0;

	/* - only lib users: do nothing
		* - only local users: set flag
		* - mixed: make copy
		*/

	if(spk->id.lib==NULL) return;
	if(spk->id.us==1) {
		id_clear_lib_data(&bmain->speaker, (ID *)spk);
		return;
	}

	ob= bmain->object.first;
	while(ob) {
		if(ob->data==spk) {
			if(ob->id.lib) lib= 1;
			else local= 1;
		}
		ob= ob->id.next;
	}

	if(local && lib==0) {
		id_clear_lib_data(&bmain->speaker, (ID *)spk);
	}
	else if(local && lib) {
		Speaker *spkn= copy_speaker(spk);
		spkn->id.us= 0;

		ob= bmain->object.first;
		while(ob) {
			if(ob->data==spk) {

				if(ob->id.lib==NULL) {
					ob->data= spkn;
					spkn->id.us++;
					spk->id.us--;
				}
			}
			ob= ob->id.next;
		}
	}
}

void free_speaker(Speaker *spk)
{
	if(spk->sound)
		spk->sound->id.us--;

	BKE_free_animdata((ID *)spk);
}
