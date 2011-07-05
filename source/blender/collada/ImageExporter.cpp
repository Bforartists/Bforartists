/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * Contributor(s): Chingiz Dyussenov, Arystanbek Dyussenov, Jan Diederich, Tod Liverseed,
 *                 Nathan Letwory
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/collada/ImageExporter.cpp
 *  \ingroup collada
 */


#include "COLLADABUURI.h"
#include "COLLADASWImage.h"

#include "ImageExporter.h"
#include "MaterialExporter.h"

#include "DNA_texture_types.h"

#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_utildefines.h"
#include "BLI_fileops.h"
#include "BLI_path_util.h"
#include "BLI_string.h"

ImagesExporter::ImagesExporter(COLLADASW::StreamWriter *sw, const char* filename) : COLLADASW::LibraryImages(sw), mfilename(filename)
{}

bool ImagesExporter::hasImages(Scene *sce)
{
	Base *base = (Base *)sce->base.first;
	
	while(base) {
		Object *ob= base->object;
		int a;
		for(a = 0; a < ob->totcol; a++)
		{
			Material *ma = give_current_material(ob, a+1);

			// no material, but check all of the slots
			if (!ma) continue;
			int b;
			for (b = 0; b < MAX_MTEX; b++) {
				MTex *mtex = ma->mtex[b];
				if (mtex && mtex->tex && mtex->tex->ima) return true;
			}

		}
		base= base->next;
	}
	return false;
}

void ImagesExporter::exportImages(Scene *sce, bool export_selected)
{
	if(hasImages(sce)) {
		openLibrary();
		MaterialFunctor mf;
		mf.forEachMaterialInScene<ImagesExporter>(sce, *this, export_selected);

		closeLibrary();
	}
}

void ImagesExporter::operator()(Material *ma, Object *ob)
{
	int a;
	for (a = 0; a < MAX_MTEX; a++) {
		MTex *mtex = ma->mtex[a];
		if (mtex && mtex->tex && mtex->tex->ima) {

			Image *image = mtex->tex->ima;
			std::string name(id_name(image));
			name = translate_id(name);
			char rel[FILE_MAX];
			char abs[FILE_MAX];
			char src[FILE_MAX];
			char dir[FILE_MAX];
			
			BLI_split_dirfile(mfilename, dir, NULL);

			BKE_rebase_path(abs, sizeof(abs), rel, sizeof(rel), G.main->name, image->name, dir);

			if (abs[0] != '\0') {

				// make absolute source path
				BLI_strncpy(src, image->name, sizeof(src));
				BLI_path_abs(src, G.main->name);

				// make dest directory if it doesn't exist
				BLI_make_existing_file(abs);
			
				if (BLI_copy_fileops(src, abs) != 0) {
					fprintf(stderr, "Cannot copy image to file's directory. \n");
				}
			} 
			
			if (find(mImages.begin(), mImages.end(), name) == mImages.end()) {
				COLLADASW::Image img(COLLADABU::URI(COLLADABU::URI::nativePathToUri(rel)), name, name); /* set name also to mNameNC. This helps other viewers import files exported from Blender better */
				img.add(mSW);

				mImages.push_back(name);
			}
		}
	}
}
