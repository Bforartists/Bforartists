/*
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
* along with this program; if not, write to the Free Software  Foundation,
* Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
*
* The Original Code is Copyright (C) 2006 Blender Foundation.
* All rights reserved.
*
* The Original Code is: all of this file.
*
* Contributor(s): Campbell Barton <ideasman42@gmail.com>
*
* ***** END GPL LICENSE BLOCK *****
*/

#ifndef BKE_POINTCACHE_H
#define BKE_POINTCACHE_H

#include "DNA_ID.h"

/* options for clearing pointcache - used for BKE_ptcache_id_clear
 Before and after are non inclusive (they wont remove the cfra) */
#define PTCACHE_CLEAR_ALL		0
#define PTCACHE_CLEAR_FRAME		1
#define PTCACHE_CLEAR_BEFORE	2
#define PTCACHE_CLEAR_AFTER		3

#define PTCACHE_EXT ".bphys"
#define PTCACHE_PATH "//pointcache/"

int	BKE_ptcache_id_filename(struct ID *id, char *filename, int cfra, int stack_index, short do_path, short do_ext);
FILE *	BKE_ptcache_id_fopen(struct ID *id, char mode, int cfra, int stack_index);
void	BKE_ptcache_id_clear(struct ID *id, char mode, int cfra, int stack_index);
int		BKE_ptcache_id_exist(struct ID *id, int cfra, int stack_index);

#endif
