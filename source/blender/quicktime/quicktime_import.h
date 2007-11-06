/**
 * Quicktime_import.h
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
 * The Original Code is Copyright (C) 2002-2003 by TNCCI Inc.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */


#ifndef __QUICKTIME_IMP_H__
#define __QUICKTIME_IMP_H__

#define __AIFF__

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "../imbuf/IMB_imbuf.h"
#include "../imbuf/IMB_imbuf_types.h"

#ifndef __MOVIES__
#ifdef _WIN32
#include <Movies.h>
#elif defined(__APPLE__)
#define __CARBONSOUND__
#import <Carbon/Carbon.h>
#include <QuickTime/Movies.h>
#endif
#endif

#ifdef _WIN32
#ifndef __FIXMATH__
#include <FixMath.h>
#endif /* __FIXMATH__ */
#endif /* _WIN32 _ */

// quicktime structure definition
// this structure is part of the anim struct

typedef struct _QuicktimeMovie {
	GWorldPtr	offscreenGWorld;
	PixMapHandle	offscreenPixMap;

	Movie		movie;
	short		movieRefNum;
	short		movieResId;
	int			movWidth, movHeight;
	Rect		movieBounds;

	int			framecount;

	TimeValue	*frameIndex;
	ImBuf		*ibuf;

	Media		theMedia;
	Track		theTrack;
	long		trackIndex;
	short		depth;

	int			have_gw;	//ugly
} QuicktimeMovie;

char *get_valid_qtname(char *name);


// quicktime movie import functions

int		anim_is_quicktime (char *name);
int		startquicktime (struct anim *anim);
void	free_anim_quicktime (struct anim *anim);
ImBuf  *qtime_fetchibuf (struct anim *anim, int position);

// quicktime image import functions

int		imb_is_a_quicktime (char *name);
ImBuf  *imb_quicktime_decode(unsigned char *mem, int size, int flags);

#endif  // __QUICKTIME_IMP_H__