/**
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
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "DNA_object_types.h"

#ifdef RNA_RUNTIME

#include "BKE_utildefines.h"
#include "BKE_image.h"

#include "MEM_guardedalloc.h"

/*
  User should check if returned path exists before copying a file there.

  TODO: it would be better to return a (abs, rel) tuple.
*/
static char *rna_Image_get_export_path(Image *image, char *dest_dir, int rel)
{
	int length = FILE_MAX;
	char *path= MEM_callocN(length, "image file path");

	if (!BKE_get_image_export_path(image, dest_dir, rel ? NULL : path, length, rel ? path : NULL, length )) {
		MEM_freeN(path);
		return NULL;
	}

	return path;
}

#else

void RNA_api_image(StructRNA *srna)
{
	FunctionRNA *func;
	PropertyRNA *parm;

	func= RNA_def_function(srna, "get_export_path", "rna_Image_get_export_path");
	RNA_def_function_ui_description(func, "Produce image export path.");
	parm= RNA_def_string(func, "dest_dir", "", 0, "", "Destination directory.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_boolean(func, "get_rel_path", 1, "", "Return relative path if True.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_string(func, "path", "", 0, "", "Absolute export path.");
	RNA_def_function_return(func, parm);
}

#endif

