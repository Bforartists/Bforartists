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
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef __BKE_BLENDER_H__
#define __BKE_BLENDER_H__

/** \file BKE_blender.h
 *  \ingroup bke
 *  \since March 2001
 *  \author nzc
 *  \brief Blender util stuff
 */

#ifdef __cplusplus
extern "C" {
#endif

void BKE_blender_free(void);

void BKE_blender_globals_init(void);
void BKE_blender_globals_clear(void);

void BKE_blender_userdef_free(void);
void BKE_blender_userdef_refresh(void);
	
/* set this callback when a UI is running */
void BKE_blender_callback_test_break_set(void (*func)(void));
int  BKE_blender_test_break(void);

#ifdef __cplusplus
}
#endif

#endif  /* __BKE_BLENDER_H__ */
