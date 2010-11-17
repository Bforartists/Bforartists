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
 * .blend file reading entry point
 */

#include <stddef.h>
#include "BLI_storage.h" /* _LARGEFILE_SOURCE */

#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "BLI_ghash.h"
#include "BLI_linklist.h"

#include "DNA_genfile.h"
#include "DNA_sdna_types.h"


#include "BKE_main.h"
#include "BKE_library.h" // for free_main
#include "BKE_idcode.h"
#include "BKE_report.h"

#include "BLO_readfile.h"
#include "BLO_undofile.h"

#include "readfile.h"

#include "BLO_readblenfile.h"

#include "BLO_sys_types.h" // needed for intptr_t

#ifdef _WIN32
#include "BLI_winstuff.h"
#endif

/* local prototypes --------------------- */
void BLO_blendhandle_print_sizes(BlendHandle *, void *); 

	/* Access routines used by filesel. */
	 
BlendHandle *BLO_blendhandle_from_file(char *file) 
{
	BlendHandle *bh;

	bh= (BlendHandle*)blo_openblenderfile(file, NULL);

	return bh;
}

BlendHandle *BLO_blendhandle_from_memory(void *mem, int memsize)
{
	BlendHandle *bh;

	bh= (BlendHandle*)blo_openblendermemory(mem, memsize, NULL);

	return bh;
}

void BLO_blendhandle_print_sizes(BlendHandle *bh, void *fp) 
{
	FileData *fd= (FileData*) bh;
	BHead *bhead;

	fprintf(fp, "[\n");
	for (bhead= blo_firstbhead(fd); bhead; bhead= blo_nextbhead(fd, bhead)) {
		if (bhead->code==ENDB)
			break;
		else {
			short *sp= fd->filesdna->structs[bhead->SDNAnr];
			char *name= fd->filesdna->types[ sp[0] ];
			char buf[4];
			
			buf[0]= (bhead->code>>24)&0xFF;
			buf[1]= (bhead->code>>16)&0xFF;
			buf[2]= (bhead->code>>8)&0xFF;
			buf[3]= (bhead->code>>0)&0xFF;
			
			buf[0]= buf[0]?buf[0]:' ';
			buf[1]= buf[1]?buf[1]:' ';
			buf[2]= buf[2]?buf[2]:' ';
			buf[3]= buf[3]?buf[3]:' ';
			
			fprintf(fp, "['%.4s', '%s', %d, %ld ], \n", buf, name, bhead->nr, (long int)bhead->len+sizeof(BHead));
		}
	}
	fprintf(fp, "]\n");
}

LinkNode *BLO_blendhandle_get_datablock_names(BlendHandle *bh, int ofblocktype) 
{
	FileData *fd= (FileData*) bh;
	LinkNode *names= NULL;
	BHead *bhead;

	for (bhead= blo_firstbhead(fd); bhead; bhead= blo_nextbhead(fd, bhead)) {
		if (bhead->code==ofblocktype) {
			char *idname= bhead_id_name(fd, bhead);
			
			BLI_linklist_prepend(&names, strdup(idname+2));
		} else if (bhead->code==ENDB)
			break;
	}
	
	return names;
}

LinkNode *BLO_blendhandle_get_previews(BlendHandle *bh, int ofblocktype) 
{
	FileData *fd= (FileData*) bh;
	LinkNode *previews= NULL;
	BHead *bhead;
	int looking=0;
	int npreviews = 0;
	PreviewImage* prv = NULL;
	PreviewImage* new_prv = NULL;
	
	for (bhead= blo_firstbhead(fd); bhead; bhead= blo_nextbhead(fd, bhead)) {
		if (bhead->code==ofblocktype) {
			ID *id= (ID*) (bhead+1);
			switch(GS(id->name))
			{
				case ID_MA: /* fall through */
				case ID_TE: /* fall through */
				case ID_IM: /* fall through */
				case ID_WO: /* fall through */
				case ID_LA: /* fall through */
					new_prv = MEM_callocN(sizeof(PreviewImage), "newpreview");
					BLI_linklist_prepend(&previews, new_prv);
					looking = 1;
					break;
				default:
					break;
			}
		} else if (bhead->code==DATA) {
			if (looking) {
				if (bhead->SDNAnr == DNA_struct_find_nr(fd->filesdna, "PreviewImage") ) {
					prv = (PreviewImage*) (bhead+1);
					npreviews = 0;				
					memcpy(new_prv, prv, sizeof(PreviewImage));
					if (prv->rect[0]) {
						unsigned int *rect = NULL;
						int rectlen = 0;
						new_prv->rect[0] = MEM_callocN(new_prv->w[0]*new_prv->h[0]*sizeof(unsigned int), "prvrect");
						bhead= blo_nextbhead(fd, bhead);
						rect = (unsigned int*)(bhead+1);
						rectlen = new_prv->w[0]*new_prv->h[0]*sizeof(unsigned int);
						memcpy(new_prv->rect[0], rect, bhead->len);					
					} else {
						new_prv->rect[0] = NULL;
					}
					
					if (prv->rect[1]) {
						unsigned int *rect = NULL;
						int rectlen = 0;
						new_prv->rect[1] = MEM_callocN(new_prv->w[1]*new_prv->h[1]*sizeof(unsigned int), "prvrect");
						bhead= blo_nextbhead(fd, bhead);
						rect = (unsigned int*)(bhead+1);
						rectlen = new_prv->w[1]*new_prv->h[1]*sizeof(unsigned int);					
						memcpy(new_prv->rect[1], rect, bhead->len);							
					} else {
						new_prv->rect[1] = NULL;
					}
				}
			}
		} else if (bhead->code==ENDB) {
			break;
		} else if (bhead->code==DATA) {
			/* DATA blocks between IDBlock and Preview */
		} else {
			looking = 0;
			new_prv = NULL;
			prv = NULL;
		}
		
	}
	
	return previews;
}

LinkNode *BLO_blendhandle_get_linkable_groups(BlendHandle *bh) 
{
	FileData *fd= (FileData*) bh;
	GHash *gathered= BLI_ghash_new(BLI_ghashutil_ptrhash, BLI_ghashutil_ptrcmp, "linkable_groups gh");
	LinkNode *names= NULL;
	BHead *bhead;
	
	for (bhead= blo_firstbhead(fd); bhead; bhead= blo_nextbhead(fd, bhead)) {
		if (bhead->code==ENDB) {
			break;
		} else if (BKE_idcode_is_valid(bhead->code)) {
			if (BKE_idcode_is_linkable(bhead->code)) {
				const char *str= BKE_idcode_to_name(bhead->code);
				
				if (!BLI_ghash_haskey(gathered, (void *)str)) {
					BLI_linklist_prepend(&names, strdup(str));
					BLI_ghash_insert(gathered, (void *)str, NULL);
				}
			}
		}
	}
	
	BLI_ghash_free(gathered, NULL, NULL);
	
	return names;
}		

void BLO_blendhandle_close(BlendHandle *bh) {
	FileData *fd= (FileData*) bh;
	
	blo_freefiledata(fd);
}

	/**********/

BlendFileData *BLO_read_from_file(const char *file, ReportList *reports)
{
	BlendFileData *bfd = NULL;
	FileData *fd;
		
	fd = blo_openblenderfile(file, reports);
	if (fd) {
		fd->reports= reports;
		bfd= blo_read_file_internal(fd, file);
		blo_freefiledata(fd);			
	}

	return bfd;	
}

BlendFileData *BLO_read_from_memory(void *mem, int memsize, ReportList *reports)
{
	BlendFileData *bfd = NULL;
	FileData *fd;
		
	fd = blo_openblendermemory(mem, memsize,  reports);
	if (fd) {
		fd->reports= reports;
		bfd= blo_read_file_internal(fd, "");
		blo_freefiledata(fd);			
	}

	return bfd;	
}

BlendFileData *BLO_read_from_memfile(Main *oldmain, const char *filename, MemFile *memfile, ReportList *reports)
{
	BlendFileData *bfd = NULL;
	FileData *fd;
	ListBase mainlist;
	
	fd = blo_openblendermemfile(memfile, reports);
	if (fd) {
		fd->reports= reports;
		strcpy(fd->relabase, filename);
		
		/* clear ob->proxy_from pointers in old main */
		blo_clear_proxy_pointers_from_lib(oldmain);

		/* separate libraries from old main */
		blo_split_main(&mainlist, oldmain);
		/* add the library pointers in oldmap lookup */
		blo_add_library_pointer_map(&mainlist, fd);
		
		/* makes lookup of existing images in old main */
		blo_make_image_pointer_map(fd, oldmain);
		
		bfd= blo_read_file_internal(fd, filename);
		
		/* ensures relinked images are not freed */
		blo_end_image_pointer_map(fd, oldmain);
		
		/* move libraries from old main to new main */
		if(bfd && mainlist.first!=mainlist.last) {
			
			/* Library structs themselves */
			bfd->main->library= oldmain->library;
			oldmain->library.first= oldmain->library.last= NULL;
			
			/* add the Library mainlist to the new main */
			BLI_remlink(&mainlist, oldmain);
			BLI_addhead(&mainlist, bfd->main);
		}
		blo_join_main(&mainlist);
		
		blo_freefiledata(fd);			
	}

	return bfd;	
}

void BLO_blendfiledata_free(BlendFileData *bfd)
{
	if (bfd->main) {
		free_main(bfd->main);
	}
	
	if (bfd->user) {
		MEM_freeN(bfd->user);
	}

	MEM_freeN(bfd);
}

