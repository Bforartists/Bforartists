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

/** \file blender/blenkernel/intern/packedFile.c
 *  \ingroup bke
 */


#include <stdio.h>
#include <fcntl.h>
#include <sys/stat.h>

#ifndef WIN32 
#include <unistd.h>
#else
#include <io.h>
#endif
#include <string.h>
#include "MEM_guardedalloc.h"

#include "DNA_image_types.h"
#include "DNA_sound_types.h"
#include "DNA_vfont_types.h"
#include "DNA_packedFile_types.h"

#include "BLI_blenlib.h"
#include "BLI_utildefines.h"

#include "BKE_font.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_main.h"
#include "BKE_packedFile.h"
#include "BKE_report.h"
#include "BKE_sound.h"

#ifdef _WIN32
#define open _open
#define close _close
#define read _read
#define write _write
#endif


int seekPackedFile(PackedFile *pf, int offset, int whence)
{
	int oldseek = -1, seek = 0;

	if (pf) {
		oldseek = pf->seek;
		switch (whence) {
			case SEEK_CUR:
				seek = oldseek + offset;
				break;
			case SEEK_END:
				seek = pf->size + offset;
				break;
			case SEEK_SET:
				seek = offset;
				break;
			default:
				oldseek = -1;
		}
		if (seek < 0) {
			seek = 0;
		}
		else if (seek > pf->size) {
			seek = pf->size;
		}
		pf->seek = seek;
	}

	return(oldseek);
}
	
void rewindPackedFile(PackedFile *pf)
{
	seekPackedFile(pf, 0, SEEK_SET);
}

int readPackedFile(PackedFile *pf, void *data, int size)
{ 
	if ((pf != NULL) && (size >= 0) && (data != NULL)) {
		if (size + pf->seek > pf->size) {
			size = pf->size - pf->seek;
		}

		if (size > 0) {
			memcpy(data, ((char *) pf->data) + pf->seek, size);
		}
		else {
			size = 0;
		}

		pf->seek += size;
	}
	else {
		size = -1;
	}

	return(size);
}

int countPackedFiles(Main *bmain)
{
	Image *ima;
	VFont *vf;
	bSound *sound;
	int count = 0;
	
	/* let's check if there are packed files... */
	for (ima = bmain->image.first; ima; ima = ima->id.next)
		if (ima->packedfile)
			count++;

	for (vf = bmain->vfont.first; vf; vf = vf->id.next)
		if (vf->packedfile)
			count++;

	for (sound = bmain->sound.first; sound; sound = sound->id.next)
		if (sound->packedfile)
			count++;

	return count;
}

void freePackedFile(PackedFile *pf)
{
	if (pf) {
		MEM_freeN(pf->data);
		MEM_freeN(pf);
	}
	else
		printf("freePackedFile: Trying to free a NULL pointer\n");
}

PackedFile *dupPackedFile(const PackedFile *pf_src)
{
	PackedFile *pf_dst;

	pf_dst       = MEM_dupallocN(pf_src);
	pf_dst->data = MEM_dupallocN(pf_src->data);

	return pf_dst;
}

PackedFile *newPackedFileMemory(void *mem, int memlen)
{
	PackedFile *pf = MEM_callocN(sizeof(*pf), "PackedFile");
	pf->data = mem;
	pf->size = memlen;
	
	return pf;
}

PackedFile *newPackedFile(ReportList *reports, const char *filename, const char *basepath)
{
	PackedFile *pf = NULL;
	int file, filelen;
	char name[FILE_MAX];
	void *data;
	
	/* render result has no filename and can be ignored
	 * any other files with no name can be ignored too */
	if (filename[0] == '\0')
		return NULL;

	//XXX waitcursor(1);
	
	/* convert relative filenames to absolute filenames */

	BLI_strncpy(name, filename, sizeof(name));
	BLI_path_abs(name, basepath);

	/* open the file
	 * and create a PackedFile structure */

	file = BLI_open(name, O_BINARY | O_RDONLY, 0);
	if (file <= 0) {
		BKE_reportf(reports, RPT_ERROR, "Unable to pack file, source path '%s' not found", name);
	}
	else {
		filelen = BLI_file_descriptor_size(file);

		if (filelen == 0) {
			/* MEM_mallocN complains about MEM_mallocN(0, "bla");
			 * we don't care.... */
			data = MEM_mallocN(1, "packFile");
		}
		else {
			data = MEM_mallocN(filelen, "packFile");
		}
		if (read(file, data, filelen) == filelen) {
			pf = newPackedFileMemory(data, filelen);
		}

		close(file);
	}

	//XXX waitcursor(0);
		
	return (pf);
}

void packAll(Main *bmain, ReportList *reports)
{
	Image *ima;
	VFont *vfont;
	bSound *sound;
	
	for (ima = bmain->image.first; ima; ima = ima->id.next) {
		if (ima->packedfile == NULL && ima->id.lib == NULL) {
			if (ima->source == IMA_SRC_FILE) {
				ima->packedfile = newPackedFile(reports, ima->name, ID_BLEND_PATH(bmain, &ima->id));
			}
			else if (ELEM(ima->source, IMA_SRC_SEQUENCE, IMA_SRC_MOVIE)) {
				BKE_reportf(reports, RPT_WARNING, "Image '%s' skipped, movies and image sequences not supported",
				            ima->id.name + 2);
			}
		}
	}

	for (vfont = bmain->vfont.first; vfont; vfont = vfont->id.next)
		if (vfont->packedfile == NULL && vfont->id.lib == NULL && BKE_vfont_is_builtin(vfont) == FALSE)
			vfont->packedfile = newPackedFile(reports, vfont->name, bmain->name);

	for (sound = bmain->sound.first; sound; sound = sound->id.next)
		if (sound->packedfile == NULL && sound->id.lib == NULL)
			sound->packedfile = newPackedFile(reports, sound->name, bmain->name);
}


#if 0

// attempt to create a function that generates an unique filename
// this will work when all funtions in fileops.c understand relative filenames...

static char *find_new_name(char *name)
{
	char tempname[FILE_MAX];
	char *newname;
	size_t len;
	
	if (fop_exists(name)) {
		for (number = 1; number <= 999; number++) {
			BLI_snprintf(tempname, sizeof(tempname), "%s.%03d", name, number);
			if (!fop_exists(tempname)) {
				break;
			}
		}
	}
	len = strlen(tempname) + 1;
	newname = MEM_mallocN(len, "find_new_name");
	memcpy(newname, tempname, len * sizeof(char));
	return newname;
}
#endif

int writePackedFile(ReportList *reports, const char *filename, PackedFile *pf, int guimode)
{
	int file, number, remove_tmp = FALSE;
	int ret_value = RET_OK;
	char name[FILE_MAX];
	char tempname[FILE_MAX];
/*      void *data; */
	
	if (guimode) {} //XXX  waitcursor(1);
	
	BLI_strncpy(name, filename, sizeof(name));
	BLI_path_abs(name, G.main->name);
	
	if (BLI_exists(name)) {
		for (number = 1; number <= 999; number++) {
			BLI_snprintf(tempname, sizeof(tempname), "%s.%03d_", name, number);
			if (!BLI_exists(tempname)) {
				if (BLI_copy(name, tempname) == RET_OK) {
					remove_tmp = TRUE;
				}
				break;
			}
		}
	}
	
	/* make sure the path to the file exists... */
	BLI_make_existing_file(name);
	
	file = BLI_open(name, O_BINARY + O_WRONLY + O_CREAT + O_TRUNC, 0666);
	if (file >= 0) {
		if (write(file, pf->data, pf->size) != pf->size) {
			BKE_reportf(reports, RPT_ERROR, "Error writing file '%s'", name);
			ret_value = RET_ERROR;
		}
		close(file);
	}
	else {
		BKE_reportf(reports, RPT_ERROR, "Error creating file '%s'", name);
		ret_value = RET_ERROR;
	}
	
	if (remove_tmp) {
		if (ret_value == RET_ERROR) {
			if (BLI_rename(tempname, name) != 0) {
				BKE_reportf(reports, RPT_ERROR, "Error restoring temp file (check files '%s' '%s')", tempname, name);
			}
		}
		else {
			if (BLI_delete(tempname, 0, 0) != 0) {
				BKE_reportf(reports, RPT_ERROR, "Error deleting '%s' (ignored)", tempname);
			}
		}
	}
	
	if (guimode) {} //XXX waitcursor(0);

	return (ret_value);
}
	
/*
 * This function compares a packed file to a 'real' file.
 * It returns an integer indicating if:
 *
 * PF_EQUAL		- the packed file and original file are identical
 * PF_DIFFERENT	- the packed file and original file differ
 * PF_NOFILE	- the original file doens't exist
 */

int checkPackedFile(const char *filename, PackedFile *pf)
{
	struct stat st;
	int ret_val, i, len, file;
	char buf[4096];
	char name[FILE_MAX];
	
	BLI_strncpy(name, filename, sizeof(name));
	BLI_path_abs(name, G.main->name);
	
	if (stat(name, &st)) {
		ret_val = PF_NOFILE;
	}
	else if (st.st_size != pf->size) {
		ret_val = PF_DIFFERS;
	}
	else {
		/* we'll have to compare the two... */

		file = BLI_open(name, O_BINARY | O_RDONLY, 0);
		if (file < 0) {
			ret_val = PF_NOFILE;
		}
		else {
			ret_val = PF_EQUAL;

			for (i = 0; i < pf->size; i += sizeof(buf)) {
				len = pf->size - i;
				if (len > sizeof(buf)) {
					len = sizeof(buf);
				}

				if (read(file, buf, len) != len) {
					/* read error ... */
					ret_val = PF_DIFFERS;
					break;
				}
				else {
					if (memcmp(buf, ((char *)pf->data) + i, len)) {
						ret_val = PF_DIFFERS;
						break;
					}
				}
			}
			
			close(file);
		}
	}
	
	return(ret_val);
}

/* unpackFile() looks at the existing files (abs_name, local_name) and a packed file.
 *
 * It returns a char *to the existing file name / new file name or NULL when
 * there was an error or when the user decides to cancel the operation.
 */

char *unpackFile(ReportList *reports, const char *abs_name, const char *local_name, PackedFile *pf, int how)
{
	char *newname = NULL;
	const char *temp = NULL;
	
	// char newabs[FILE_MAX];
	// char newlocal[FILE_MAX];
	
	if (pf != NULL) {
		switch (how) {
			case -1:
			case PF_KEEP:
				break;
			case PF_REMOVE:
				temp = abs_name;
				break;
			case PF_USE_LOCAL:
				/* if file exists use it */
				if (BLI_exists(local_name)) {
					temp = local_name;
					break;
				}
			/* else fall through and create it */
			case PF_WRITE_LOCAL:
				if (writePackedFile(reports, local_name, pf, 1) == RET_OK) {
					temp = local_name;
				}
				break;
			case PF_USE_ORIGINAL:
				/* if file exists use it */
				if (BLI_exists(abs_name)) {
					temp = abs_name;
					break;
				}
			/* else fall through and create it */
			case PF_WRITE_ORIGINAL:
				if (writePackedFile(reports, abs_name, pf, 1) == RET_OK) {
					temp = abs_name;
				}
				break;
			default:
				printf("unpackFile: unknown return_value %d\n", how);
				break;
		}
		
		if (temp) {
			newname = BLI_strdup(temp);
		}
	}
	
	return newname;
}


int unpackVFont(ReportList *reports, VFont *vfont, int how)
{
	char localname[FILE_MAX], fi[FILE_MAXFILE];
	char *newname;
	int ret_value = RET_ERROR;
	
	if (vfont != NULL) {
		BLI_strncpy(localname, vfont->name, sizeof(localname));
		BLI_splitdirstring(localname, fi);
		
		BLI_snprintf(localname, sizeof(localname), "//fonts/%s", fi);
		
		newname = unpackFile(reports, vfont->name, localname, vfont->packedfile, how);
		if (newname != NULL) {
			ret_value = RET_OK;
			freePackedFile(vfont->packedfile);
			vfont->packedfile = NULL;
			BLI_strncpy(vfont->name, newname, sizeof(vfont->name));
			MEM_freeN(newname);
		}
	}
	
	return (ret_value);
}

int unpackSound(Main *bmain, ReportList *reports, bSound *sound, int how)
{
	char localname[FILE_MAXDIR + FILE_MAX], fi[FILE_MAX];
	char *newname;
	int ret_value = RET_ERROR;

	if (sound != NULL) {
		BLI_strncpy(localname, sound->name, sizeof(localname));
		BLI_splitdirstring(localname, fi);
		BLI_snprintf(localname, sizeof(localname), "//sounds/%s", fi);

		newname = unpackFile(reports, sound->name, localname, sound->packedfile, how);
		if (newname != NULL) {
			BLI_strncpy(sound->name, newname, sizeof(sound->name));
			MEM_freeN(newname);

			freePackedFile(sound->packedfile);
			sound->packedfile = NULL;

			sound_load(bmain, sound);

			ret_value = RET_OK;
		}
	}
	
	return(ret_value);
}

int unpackImage(ReportList *reports, Image *ima, int how)
{
	char localname[FILE_MAXDIR + FILE_MAX], fi[FILE_MAX];
	char *newname;
	int ret_value = RET_ERROR;
	
	if (ima != NULL && ima->name[0]) {
		BLI_strncpy(localname, ima->name, sizeof(localname));
		BLI_splitdirstring(localname, fi);
		BLI_snprintf(localname, sizeof(localname), "//textures/%s", fi);

		newname = unpackFile(reports, ima->name, localname, ima->packedfile, how);
		if (newname != NULL) {
			ret_value = RET_OK;
			freePackedFile(ima->packedfile);
			ima->packedfile = NULL;
			BLI_strncpy(ima->name, newname, sizeof(ima->name));
			MEM_freeN(newname);
			BKE_image_signal(ima, NULL, IMA_SIGNAL_RELOAD);
		}
	}
	
	return(ret_value);
}

void unpackAll(Main *bmain, ReportList *reports, int how)
{
	Image *ima;
	VFont *vf;
	bSound *sound;

	for (ima = bmain->image.first; ima; ima = ima->id.next)
		if (ima->packedfile)
			unpackImage(reports, ima, how);

	for (vf = bmain->vfont.first; vf; vf = vf->id.next)
		if (vf->packedfile)
			unpackVFont(reports, vf, how);

	for (sound = bmain->sound.first; sound; sound = sound->id.next)
		if (sound->packedfile)
			unpackSound(bmain, reports, sound, how);
}

