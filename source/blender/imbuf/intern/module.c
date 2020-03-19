/*
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
 */

/** \file
 * \ingroup imbuf
 */

#include <stddef.h>

#include "BLI_utildefines.h"

#include "IMB_allocimbuf.h"
#include "IMB_colormanagement_intern.h"
#include "IMB_filetype.h"
#include "IMB_imbuf.h"

void IMB_init(void)
{
  imb_refcounter_lock_init();
  imb_mmap_lock_init();
  imb_filetypes_init();
  imb_tile_cache_init();
  colormanagement_init();
}

void IMB_exit(void)
{
  imb_tile_cache_exit();
  imb_filetypes_exit();
  colormanagement_exit();
  imb_mmap_lock_exit();
  imb_refcounter_lock_exit();
}
