/**
 * $Id: rna_image_api.c 23507 2009-09-27 09:19:29Z kazanbas $
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Arystanbek Dyussenov
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#include "RNA_define.h"
#include "RNA_types.h"

#ifdef RNA_RUNTIME

#include "BKE_image.h"
#include "BKE_packedFile.h"
#include "BKE_main.h"
#include "BKE_utildefines.h"

#include "IMB_imbuf.h"

#include "DNA_image_types.h"
#include "DNA_scene_types.h"

#include "MEM_guardedalloc.h"

static void rna_Image_save_render(Image *image, bContext *C, ReportList *reports, char *path, Scene *scene)
{
	ImBuf *ibuf;

	if (scene == NULL) {
		scene = CTX_data_scene(C);
	}

	if (scene) {
		ImageUser iuser;
		void *lock;

		iuser.scene = scene;
		iuser.ok = 1;

		ibuf = BKE_image_acquire_ibuf(image, &iuser, &lock);

		if (ibuf == NULL) {
			BKE_reportf(reports, RPT_ERROR, "Couldn't acquire buffer from image");
		}

		if (!BKE_write_ibuf(NULL, ibuf, path, scene->r.imtype, scene->r.subimtype, scene->r.quality)) {
			BKE_reportf(reports, RPT_ERROR, "Couldn't write image: %s", path);
		}
	} else {
		BKE_reportf(reports, RPT_ERROR, "Scene not in context, couldn't get save parameters");
	}
}

static void rna_Image_save(Image *image, ReportList *reports)
{
	ImBuf *ibuf= BKE_image_get_ibuf(image, NULL);
	if(ibuf) {
		if(image->packedfile) {
			if (writePackedFile(reports, image->name, image->packedfile, 0) != RET_OK) {
				BKE_reportf(reports, RPT_ERROR, "Image \"%s\" could saved packed file to \"%s\"", image->id.name+2, image->name);
			}
		}
		else if (IMB_saveiff(ibuf, image->name, ibuf->flags)) {
			ibuf->userflags &= ~IB_BITMAPDIRTY;
		}
		else {
			BKE_reportf(reports, RPT_ERROR, "Image \"%s\" could not be saved to \"%s\"", image->id.name+2, image->name);
		}
	}
	else {
		BKE_reportf(reports, RPT_ERROR, "Image \"%s\" does not have any image data", image->id.name+2);
	}
}

#else

void RNA_api_image(StructRNA *srna)
{
	FunctionRNA *func;
	PropertyRNA *parm;

	func= RNA_def_function(srna, "save_render", "rna_Image_save_render");
	RNA_def_function_ui_description(func, "Save image to a specific path using a scenes render settings.");
	RNA_def_function_flag(func, FUNC_USE_CONTEXT|FUNC_USE_REPORTS);
	parm= RNA_def_string(func, "path", "", 0, "", "Save path.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_pointer(func, "scene", "Scene", "", "Scene to take image parameters from.");

	func= RNA_def_function(srna, "save", "rna_Image_save");
	RNA_def_function_ui_description(func, "Save image to its source path.");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
}

#endif

