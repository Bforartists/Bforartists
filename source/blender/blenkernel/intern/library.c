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
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 */

/** \file
 * \ingroup bke
 *
 * Contains code specific to the `Library` ID type.
 */

#include "CLG_log.h"

#include "MEM_guardedalloc.h"

/* all types are needed here, in order to do memory operations */
#include "DNA_ID.h"

#include "BLI_utildefines.h"

#include "BLI_blenlib.h"

#include "BKE_lib_id.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_packedFile.h"

/* Unused currently. */
// static CLG_LogRef LOG = {.identifier = "bke.library"};

void BKE_library_free(Library *lib)
{
  if (lib->packedfile) {
    BKE_packedfile_free(lib->packedfile);
  }
}

void BKE_library_filepath_set(Main *bmain, Library *lib, const char *filepath)
{
  /* in some cases this is used to update the absolute path from the
   * relative */
  if (lib->name != filepath) {
    BLI_strncpy(lib->name, filepath, sizeof(lib->name));
  }

  BLI_strncpy(lib->filepath, filepath, sizeof(lib->filepath));

  /* not essential but set filepath is an absolute copy of value which
   * is more useful if its kept in sync */
  if (BLI_path_is_rel(lib->filepath)) {
    /* note that the file may be unsaved, in this case, setting the
     * filepath on an indirectly linked path is not allowed from the
     * outliner, and its not really supported but allow from here for now
     * since making local could cause this to be directly linked - campbell
     */
    /* Never make paths relative to parent lib - reading code (blenloader) always set *all*
     * lib->name relative to current main, not to their parent for indirectly linked ones. */
    const char *basepath = BKE_main_blendfile_path(bmain);
    BLI_path_abs(lib->filepath, basepath);
  }
}
