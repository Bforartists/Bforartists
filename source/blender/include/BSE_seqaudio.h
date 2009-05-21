/**
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
 * The Original Code is Copyright (C) 2003 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 * 
 */

#ifndef BSE_SEQAUDIO_H
#define BSE_SEQAUDIO_H

#ifndef DISABLE_SDL
#include "SDL.h"
#endif

/* muha, we don't init (no SDL_main)! */
#ifdef main
#	undef main
#endif

#include "DNA_sound_types.h"
#include "BLO_sys_types.h"

void audio_mixdown();
void audio_makestream(bSound *sound);
void audiostream_play(int startframe, uint32_t duration, int mixdown);
void audiostream_fill(uint8_t* mixdown, int len);
void audiostream_start(int frame);
void audiostream_scrub(int frame);
void audiostream_stop(void);
int audiostream_pos(void);

#endif

