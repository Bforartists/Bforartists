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
 *
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 *
 */

/** \file blender/blenloader/intern/readfile.c
 *  \ingroup blenloader
 */


#include "zlib.h"

#include <limits.h>
#include <stdio.h> // for printf fopen fwrite fclose sprintf FILE
#include <stdlib.h> // for getenv atoi
#include <stddef.h> // for offsetof
#include <fcntl.h> // for open
#include <string.h> // for strrchr strncmp strstr
#include <math.h> // for fabs
#include <stdarg.h> /* for va_start/end */

#include "BLI_utildefines.h"
#ifndef WIN32
#  include <unistd.h> // for read close
#else
#  include <io.h> // for open close read
#  include "winsock2.h"
#  include "BLI_winstuff.h"
#endif

/* allow readfile to use deprecated functionality */
#define DNA_DEPRECATED_ALLOW

#include "DNA_anim_types.h"
#include "DNA_armature_types.h"
#include "DNA_actuator_types.h"
#include "DNA_brush_types.h"
#include "DNA_camera_types.h"
#include "DNA_cloth_types.h"
#include "DNA_controller_types.h"
#include "DNA_constraint_types.h"
#include "DNA_dynamicpaint_types.h"
#include "DNA_effect_types.h"
#include "DNA_fileglobal_types.h"
#include "DNA_genfile.h"
#include "DNA_group_types.h"
#include "DNA_gpencil_types.h"
#include "DNA_ipo_types.h"
#include "DNA_key_types.h"
#include "DNA_lattice_types.h"
#include "DNA_lamp_types.h"
#include "DNA_linestyle_types.h"
#include "DNA_meta_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_nla_types.h"
#include "DNA_node_types.h"
#include "DNA_object_fluidsim.h" // NT
#include "DNA_object_types.h"
#include "DNA_packedFile_types.h"
#include "DNA_particle_types.h"
#include "DNA_property_types.h"
#include "DNA_rigidbody_types.h"
#include "DNA_text_types.h"
#include "DNA_view3d_types.h"
#include "DNA_screen_types.h"
#include "DNA_sensor_types.h"
#include "DNA_sdna_types.h"
#include "DNA_scene_types.h"
#include "DNA_sequence_types.h"
#include "DNA_smoke_types.h"
#include "DNA_speaker_types.h"
#include "DNA_sound_types.h"
#include "DNA_space_types.h"
#include "DNA_vfont_types.h"
#include "DNA_world_types.h"
#include "DNA_movieclip_types.h"
#include "DNA_mask_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"
#include "BLI_endian_switch.h"
#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BLI_edgehash.h"
#include "BLI_threads.h"

#include "BLF_translation.h"

#include "BKE_anim.h"
#include "BKE_action.h"
#include "BKE_armature.h"
#include "BKE_brush.h"
#include "BKE_colortools.h"
#include "BKE_constraint.h"
#include "BKE_context.h"
#include "BKE_curve.h"
#include "BKE_deform.h"
#include "BKE_depsgraph.h"
#include "BKE_effect.h"
#include "BKE_fcurve.h"
#include "BKE_global.h" // for G
#include "BKE_group.h"
#include "BKE_image.h"
#include "BKE_lattice.h"
#include "BKE_library.h" // for which_libbase
#include "BKE_idcode.h"
#include "BKE_idprop.h"
#include "BKE_material.h"
#include "BKE_main.h" // for Main
#include "BKE_mesh.h" // for ME_ defines (patching)
#include "BKE_modifier.h"
#include "BKE_multires.h"
#include "BKE_node.h" // for tree type defines
#include "BKE_ocean.h"
#include "BKE_object.h"
#include "BKE_paint.h"
#include "BKE_particle.h"
#include "BKE_pointcache.h"
#include "BKE_property.h" // for BKE_bproperty_object_get
#include "BKE_report.h"
#include "BKE_sca.h" // for init_actuator
#include "BKE_scene.h"
#include "BKE_screen.h"
#include "BKE_sequencer.h"
#include "BKE_text.h" // for txt_extended_ascii_as_utf8
#include "BKE_texture.h"
#include "BKE_tracking.h"
#include "BKE_sound.h"

#include "IMB_imbuf.h"  // for proxy / timecode versioning stuff

#include "NOD_common.h"
#include "NOD_socket.h"
#include "NOD_composite.h"
#include "NOD_shader.h"
#include "NOD_texture.h"

#include "BLO_readfile.h"
#include "BLO_undofile.h"
#include "BLO_blend_defs.h"

#include "RE_engine.h"

#include "readfile.h"

#include "PIL_time.h"

#include <errno.h>

/*
 * Remark: still a weak point is the newaddress() function, that doesnt solve reading from
 * multiple files at the same time
 *
 * (added remark: oh, i thought that was solved? will look at that... (ton)
 *
 * READ
 * - Existing Library (Main) push or free
 * - allocate new Main
 * - load file
 * - read SDNA
 * - for each LibBlock
 *     - read LibBlock
 *     - if a Library
 *         - make a new Main
 *         - attach ID's to it
 *     - else
 *         - read associated 'direct data'
 *         - link direct data (internal and to LibBlock)
 * - read FileGlobal
 * - read USER data, only when indicated (file is ~/X.XX/startup.blend)
 * - free file
 * - per Library (per Main)
 *     - read file
 *     - read SDNA
 *     - find LibBlocks and attach IDs to Main
 *         - if external LibBlock
 *             - search all Main's
 *                 - or it's already read,
 *                 - or not read yet
 *                 - or make new Main
 *     - per LibBlock
 *         - read recursive
 *         - read associated direct data
 *         - link direct data (internal and to LibBlock)
 *     - free file
 * - per Library with unread LibBlocks
 *     - read file
 *     - read SDNA
 *     - per LibBlock
 *                - read recursive
 *                - read associated direct data
 *                - link direct data (internal and to LibBlock)
 *         - free file
 * - join all Mains
 * - link all LibBlocks and indirect pointers to libblocks
 * - initialize FileGlobal and copy pointers to Global
 */

/***/

typedef struct OldNew {
	void *old, *newp;
	int nr;
} OldNew;

typedef struct OldNewMap {
	OldNew *entries;
	int nentries, entriessize;
	int sorted;
	int lasthit;
} OldNewMap;


/* local prototypes */
static void *read_struct(FileData *fd, BHead *bh, const char *blockname);
static void direct_link_modifiers(FileData *fd, ListBase *lb);
static void convert_tface_mt(FileData *fd, Main *main);

/* this function ensures that reports are printed,
 * in the case of libraray linking errors this is important!
 *
 * bit kludge but better then doubling up on prints,
 * we could alternatively have a versions of a report function which forces printing - campbell
 */

static void BKE_reportf_wrap(ReportList *reports, ReportType type, const char *format, ...)
#ifdef __GNUC__
__attribute__ ((format(printf, 3, 4)))
#endif
;
static void BKE_reportf_wrap(ReportList *reports, ReportType type, const char *format, ...)
{
	char fixed_buf[1024]; /* should be long enough */
	
	va_list args;
	
	va_start(args, format);
	vsnprintf(fixed_buf, sizeof(fixed_buf), format, args);
	va_end(args);
	
	fixed_buf[sizeof(fixed_buf) - 1] = '\0';
	
	BKE_report(reports, type, fixed_buf);
	
	if (G.background == 0) {
		printf("%s\n", fixed_buf);
	}
}

static OldNewMap *oldnewmap_new(void) 
{
	OldNewMap *onm= MEM_callocN(sizeof(*onm), "OldNewMap");
	
	onm->entriessize = 1024;
	onm->entries = MEM_mallocN(sizeof(*onm->entries)*onm->entriessize, "OldNewMap.entries");
	
	return onm;
}

static int verg_oldnewmap(const void *v1, const void *v2)
{
	const struct OldNew *x1=v1, *x2=v2;
	
	if (x1->old > x2->old) return 1;
	else if (x1->old < x2->old) return -1;
	return 0;
}


static void oldnewmap_sort(FileData *fd) 
{
	qsort(fd->libmap->entries, fd->libmap->nentries, sizeof(OldNew), verg_oldnewmap);
	fd->libmap->sorted = 1;
}

/* nr is zero for data, and ID code for libdata */
static void oldnewmap_insert(OldNewMap *onm, void *oldaddr, void *newaddr, int nr) 
{
	OldNew *entry;
	
	if (oldaddr==NULL || newaddr==NULL) return;
	
	if (onm->nentries == onm->entriessize) {
		int osize = onm->entriessize;
		OldNew *oentries = onm->entries;
		
		onm->entriessize *= 2;
		onm->entries = MEM_mallocN(sizeof(*onm->entries)*onm->entriessize, "OldNewMap.entries");
		
		memcpy(onm->entries, oentries, sizeof(*oentries)*osize);
		MEM_freeN(oentries);
	}

	entry = &onm->entries[onm->nentries++];
	entry->old = oldaddr;
	entry->newp = newaddr;
	entry->nr = nr;
}

void blo_do_versions_oldnewmap_insert(OldNewMap *onm, void *oldaddr, void *newaddr, int nr)
{
	oldnewmap_insert(onm, oldaddr, newaddr, nr);
}

static void *oldnewmap_lookup_and_inc(OldNewMap *onm, void *addr) 
{
	int i;
	
	if (addr == NULL) return NULL;
	
	if (onm->lasthit < onm->nentries-1) {
		OldNew *entry = &onm->entries[++onm->lasthit];
		
		if (entry->old == addr) {
			entry->nr++;
			return entry->newp;
		}
	}
	
	for (i = 0; i < onm->nentries; i++) {
		OldNew *entry = &onm->entries[i];
		
		if (entry->old == addr) {
			onm->lasthit = i;
			
			entry->nr++;
			return entry->newp;
		}
	}
	
	return NULL;
}

/* for libdata, nr has ID code, no increment */
static void *oldnewmap_liblookup(OldNewMap *onm, void *addr, void *lib)
{
	if (addr == NULL) {
		return NULL;
	}

	/* lasthit works fine for non-libdata, linking there is done in same sequence as writing */
	if (onm->sorted) {
		OldNew entry_s, *entry;

		entry_s.old = addr;

		entry = bsearch(&entry_s, onm->entries, onm->nentries, sizeof(OldNew), verg_oldnewmap);
		if (entry) {
			ID *id = entry->newp;

			if (id && (!lib || id->lib)) {
				return id;
			}
		}
	}
	else {
		/* note, this can be a bottle neck when loading some files */
		unsigned int nentries = (unsigned int)onm->nentries;
		unsigned int i;
		OldNew *entry;

		for (i = 0, entry = onm->entries; i < nentries; i++, entry++) {
			if (entry->old == addr) {
				ID *id = entry->newp;
				if (id && (!lib || id->lib)) {
					return id;
				}
			}
		}
	}

	return NULL;
}

static void oldnewmap_free_unused(OldNewMap *onm) 
{
	int i;

	for (i = 0; i < onm->nentries; i++) {
		OldNew *entry = &onm->entries[i];
		if (entry->nr == 0) {
			MEM_freeN(entry->newp);
			entry->newp = NULL;
		}
	}
}

static void oldnewmap_clear(OldNewMap *onm) 
{
	onm->nentries = 0;
	onm->lasthit = 0;
}

static void oldnewmap_free(OldNewMap *onm) 
{
	MEM_freeN(onm->entries);
	MEM_freeN(onm);
}

/***/

static void read_libraries(FileData *basefd, ListBase *mainlist);

/* ************ help functions ***************** */

static void add_main_to_main(Main *mainvar, Main *from)
{
	ListBase *lbarray[MAX_LIBARRAY], *fromarray[MAX_LIBARRAY];
	int a;
	
	set_listbasepointers(mainvar, lbarray);
	a = set_listbasepointers(from, fromarray);
	while (a--) {
		BLI_movelisttolist(lbarray[a], fromarray[a]);
	}
}

void blo_join_main(ListBase *mainlist)
{
	Main *tojoin, *mainl;
	
	mainl = mainlist->first;
	while ((tojoin = mainl->next)) {
		add_main_to_main(mainl, tojoin);
		BLI_remlink(mainlist, tojoin);
		MEM_freeN(tojoin);
	}
}

static void split_libdata(ListBase *lb, Main *first)
{
	ListBase *lbn;
	ID *id, *idnext;
	Main *mainvar;
	
	id = lb->first;
	while (id) {
		idnext = id->next;
		if (id->lib) {
			mainvar = first;
			while (mainvar) {
				if (mainvar->curlib == id->lib) {
					lbn= which_libbase(mainvar, GS(id->name));
					BLI_remlink(lb, id);
					BLI_addtail(lbn, id);
					break;
				}
				mainvar = mainvar->next;
			}
			if (mainvar == NULL) printf("error split_libdata\n");
		}
		id = idnext;
	}
}

void blo_split_main(ListBase *mainlist, Main *main)
{
	ListBase *lbarray[MAX_LIBARRAY];
	Library *lib;
	int i;
	
	mainlist->first = mainlist->last = main;
	main->next = NULL;
	
	if (main->library.first == NULL)
		return;
	
	for (lib = main->library.first; lib; lib = lib->id.next) {
		Main *libmain = MEM_callocN(sizeof(Main), "libmain");
		libmain->curlib = lib;
		BLI_addtail(mainlist, libmain);
	}
	
	i = set_listbasepointers(main, lbarray);
	while (i--)
		split_libdata(lbarray[i], main->next);
}

static void read_file_version(FileData *fd, Main *main)
{
	BHead *bhead;
	
	for (bhead= blo_firstbhead(fd); bhead; bhead= blo_nextbhead(fd, bhead)) {
		if (bhead->code == GLOB) {
			FileGlobal *fg= read_struct(fd, bhead, "Global");
			if (fg) {
				main->subversionfile= fg->subversion;
				main->minversionfile= fg->minversion;
				main->minsubversionfile= fg->minsubversion;
				MEM_freeN(fg);
			}
			else if (bhead->code == ENDB)
				break;
		}
	}
}


static Main *blo_find_main(FileData *fd, const char *filepath, const char *relabase)
{
	ListBase *mainlist = fd->mainlist;
	Main *m;
	Library *lib;
	char name1[FILE_MAX];
	
	BLI_strncpy(name1, filepath, sizeof(name1));
	BLI_cleanup_path(relabase, name1);
	
//	printf("blo_find_main: relabase  %s\n", relabase);
//	printf("blo_find_main: original in  %s\n", filepath);
//	printf("blo_find_main: converted to %s\n", name1);
	
	for (m = mainlist->first; m; m = m->next) {
		char *libname = (m->curlib) ? m->curlib->filepath : m->name;
		
		if (BLI_path_cmp(name1, libname) == 0) {
			if (G.debug & G_DEBUG) printf("blo_find_main: found library %s\n", libname);
			return m;
		}
	}
	
	m = MEM_callocN(sizeof(Main), "find_main");
	BLI_addtail(mainlist, m);
	
	lib = BKE_libblock_alloc(&m->library, ID_LI, "lib");
	BLI_strncpy(lib->name, filepath, sizeof(lib->name));
	BLI_strncpy(lib->filepath, name1, sizeof(lib->filepath));
	
	m->curlib = lib;
	
	read_file_version(fd, m);
	
	if (G.debug & G_DEBUG) printf("blo_find_main: added new lib %s\n", filepath);
	return m;
}


/* ************ FILE PARSING ****************** */

static void switch_endian_bh4(BHead4 *bhead)
{
	/* the ID_.. codes */
	if ((bhead->code & 0xFFFF)==0) bhead->code >>= 16;
	
	if (bhead->code != ENDB) {
		BLI_endian_switch_int32(&bhead->len);
		BLI_endian_switch_int32(&bhead->SDNAnr);
		BLI_endian_switch_int32(&bhead->nr);
	}
}

static void switch_endian_bh8(BHead8 *bhead)
{
	/* the ID_.. codes */
	if ((bhead->code & 0xFFFF)==0) bhead->code >>= 16;
	
	if (bhead->code != ENDB) {
		BLI_endian_switch_int32(&bhead->len);
		BLI_endian_switch_int32(&bhead->SDNAnr);
		BLI_endian_switch_int32(&bhead->nr);
	}
}

static void bh4_from_bh8(BHead *bhead, BHead8 *bhead8, int do_endian_swap)
{
	BHead4 *bhead4 = (BHead4 *) bhead;
	int64_t old;

	bhead4->code = bhead8->code;
	bhead4->len = bhead8->len;

	if (bhead4->code != ENDB) {
		/* perform a endian swap on 64bit pointers, otherwise the pointer might map to zero
		 * 0x0000000000000000000012345678 would become 0x12345678000000000000000000000000
		 */
		if (do_endian_swap) {
			BLI_endian_switch_int64(&bhead8->old);
		}
		
		/* this patch is to avoid a long long being read from not-eight aligned positions
		 * is necessary on any modern 64bit architecture) */
		memcpy(&old, &bhead8->old, 8);
		bhead4->old = (int) (old >> 3);
		
		bhead4->SDNAnr = bhead8->SDNAnr;
		bhead4->nr = bhead8->nr;
	}
}

static void bh8_from_bh4(BHead *bhead, BHead4 *bhead4)
{
	BHead8 *bhead8 = (BHead8 *) bhead;
	
	bhead8->code = bhead4->code;
	bhead8->len = bhead4->len;
	
	if (bhead8->code != ENDB) {
		bhead8->old = bhead4->old;
		bhead8->SDNAnr = bhead4->SDNAnr;
		bhead8->nr= bhead4->nr;
	}
}

static BHeadN *get_bhead(FileData *fd)
{
	BHeadN *new_bhead = NULL;
	int readsize;
	
	if (fd) {
		if (!fd->eof) {
			/* initializing to zero isn't strictly needed but shuts valgrind up
			 * since uninitialized memory gets compared */
			BHead8 bhead8 = {0};
			BHead4 bhead4 = {0};
			BHead  bhead = {0};
			
			/* First read the bhead structure.
			 * Depending on the platform the file was written on this can
			 * be a big or little endian BHead4 or BHead8 structure.
			 *
			 * As usual 'ENDB' (the last *partial* bhead of the file)
			 * needs some special handling. We don't want to EOF just yet.
			 */
			if (fd->flags & FD_FLAGS_FILE_POINTSIZE_IS_4) {
				bhead4.code = DATA;
				readsize = fd->read(fd, &bhead4, sizeof(bhead4));
				
				if (readsize == sizeof(bhead4) || bhead4.code == ENDB) {
					if (fd->flags & FD_FLAGS_SWITCH_ENDIAN) {
						switch_endian_bh4(&bhead4);
					}
					
					if (fd->flags & FD_FLAGS_POINTSIZE_DIFFERS) {
						bh8_from_bh4(&bhead, &bhead4);
					}
					else {
						memcpy(&bhead, &bhead4, sizeof(bhead));
					}
				}
				else {
					fd->eof = 1;
					bhead.len= 0;
				}
			}
			else {
				bhead8.code = DATA;
				readsize = fd->read(fd, &bhead8, sizeof(bhead8));
				
				if (readsize == sizeof(bhead8) || bhead8.code == ENDB) {
					if (fd->flags & FD_FLAGS_SWITCH_ENDIAN) {
						switch_endian_bh8(&bhead8);
					}
					
					if (fd->flags & FD_FLAGS_POINTSIZE_DIFFERS) {
						bh4_from_bh8(&bhead, &bhead8, (fd->flags & FD_FLAGS_SWITCH_ENDIAN));
					}
					else {
						memcpy(&bhead, &bhead8, sizeof(bhead));
					}
				}
				else {
					fd->eof = 1;
					bhead.len= 0;
				}
			}
			
			/* make sure people are not trying to pass bad blend files */
			if (bhead.len < 0) fd->eof = 1;
			
			/* bhead now contains the (converted) bhead structure. Now read
			 * the associated data and put everything in a BHeadN (creative naming !)
			 */
			if (!fd->eof) {
				new_bhead = MEM_mallocN(sizeof(BHeadN) + bhead.len, "new_bhead");
				if (new_bhead) {
					new_bhead->next = new_bhead->prev = NULL;
					new_bhead->bhead = bhead;
					
					readsize = fd->read(fd, new_bhead + 1, bhead.len);
					
					if (readsize != bhead.len) {
						fd->eof = 1;
						MEM_freeN(new_bhead);
						new_bhead = NULL;
					}
				}
				else {
					fd->eof = 1;
				}
			}
		}
	}

	/* We've read a new block. Now add it to the list
	 * of blocks.
	 */
	if (new_bhead) {
		BLI_addtail(&fd->listbase, new_bhead);
	}
	
	return(new_bhead);
}

BHead *blo_firstbhead(FileData *fd)
{
	BHeadN *new_bhead;
	BHead *bhead = NULL;
	
	/* Rewind the file
	 * Read in a new block if necessary
	 */
	new_bhead = fd->listbase.first;
	if (new_bhead == NULL) {
		new_bhead = get_bhead(fd);
	}
	
	if (new_bhead) {
		bhead = &new_bhead->bhead;
	}
	
	return(bhead);
}

BHead *blo_prevbhead(FileData *UNUSED(fd), BHead *thisblock)
{
	BHeadN *bheadn = (BHeadN *) (((char *) thisblock) - offsetof(BHeadN, bhead));
	BHeadN *prev = bheadn->prev;
	
	return (prev) ? &prev->bhead : NULL;
}

BHead *blo_nextbhead(FileData *fd, BHead *thisblock)
{
	BHeadN *new_bhead = NULL;
	BHead *bhead = NULL;
	
	if (thisblock) {
		/* bhead is actually a sub part of BHeadN
		 * We calculate the BHeadN pointer from the BHead pointer below */
		new_bhead = (BHeadN *) (((char *) thisblock) - offsetof(BHeadN, bhead));
		
		/* get the next BHeadN. If it doesn't exist we read in the next one */
		new_bhead = new_bhead->next;
		if (new_bhead == NULL) {
			new_bhead = get_bhead(fd);
		}
	}
	
	if (new_bhead) {
		/* here we do the reverse:
		 * go from the BHeadN pointer to the BHead pointer */
		bhead = &new_bhead->bhead;
	}
	
	return(bhead);
}

static void decode_blender_header(FileData *fd)
{
	char header[SIZEOFBLENDERHEADER], num[4];
	int readsize;
	
	/* read in the header data */
	readsize = fd->read(fd, header, sizeof(header));
	
	if (readsize == sizeof(header)) {
		if (strncmp(header, "BLENDER", 7) == 0) {
			int remove_this_endian_test = 1;
			
			fd->flags |= FD_FLAGS_FILE_OK;
			
			/* what size are pointers in the file ? */
			if (header[7]=='_') {
				fd->flags |= FD_FLAGS_FILE_POINTSIZE_IS_4;
				if (sizeof(void *) != 4) {
					fd->flags |= FD_FLAGS_POINTSIZE_DIFFERS;
				}
			}
			else {
				if (sizeof(void *) != 8) {
					fd->flags |= FD_FLAGS_POINTSIZE_DIFFERS;
				}
			}
			
			/* is the file saved in a different endian
			 * than we need ?
			 */
			if (((((char *)&remove_this_endian_test)[0] == 1) ? L_ENDIAN : B_ENDIAN) != ((header[8] == 'v') ? L_ENDIAN : B_ENDIAN)) {
				fd->flags |= FD_FLAGS_SWITCH_ENDIAN;
			}
			
			/* get the version number */
			memcpy(num, header + 9, 3);
			num[3] = 0;
			fd->fileversion = atoi(num);
		}
	}
}

static int read_file_dna(FileData *fd)
{
	BHead *bhead;
	
	for (bhead = blo_firstbhead(fd); bhead; bhead = blo_nextbhead(fd, bhead)) {
		if (bhead->code == DNA1) {
			const bool do_endian_swap = (fd->flags & FD_FLAGS_SWITCH_ENDIAN) != 0;
			
			fd->filesdna = DNA_sdna_from_data(&bhead[1], bhead->len, do_endian_swap);
			if (fd->filesdna) {
				fd->compflags = DNA_struct_get_compareflags(fd->filesdna, fd->memsdna);
				/* used to retrieve ID names from (bhead+1) */
				fd->id_name_offs = DNA_elem_offset(fd->filesdna, "ID", "char", "name[]");
			}
			
			return 1;
		}
		else if (bhead->code == ENDB)
			break;
	}
	
	return 0;
}

static int fd_read_from_file(FileData *filedata, void *buffer, unsigned int size)
{
	int readsize = read(filedata->filedes, buffer, size);
	
	if (readsize < 0) {
		readsize = EOF;
	}
	else {
		filedata->seek += readsize;
	}
	
	return readsize;
}

static int fd_read_gzip_from_file(FileData *filedata, void *buffer, unsigned int size)
{
	int readsize = gzread(filedata->gzfiledes, buffer, size);
	
	if (readsize < 0) {
		readsize = EOF;
	}
	else {
		filedata->seek += readsize;
	}
	
	return (readsize);
}

static int fd_read_from_memory(FileData *filedata, void *buffer, unsigned int size)
{
	/* don't read more bytes then there are available in the buffer */
	int readsize = (int)MIN2(size, (unsigned int)(filedata->buffersize - filedata->seek));
	
	memcpy(buffer, filedata->buffer + filedata->seek, readsize);
	filedata->seek += readsize;
	
	return (readsize);
}

static int fd_read_from_memfile(FileData *filedata, void *buffer, unsigned int size)
{
	static unsigned int seek = (1<<30);	/* the current position */
	static unsigned int offset = 0;		/* size of previous chunks */
	static MemFileChunk *chunk = NULL;
	unsigned int chunkoffset, readsize, totread;
	
	if (size == 0) return 0;
	
	if (seek != (unsigned int)filedata->seek) {
		chunk = filedata->memfile->chunks.first;
		seek = 0;
		
		while (chunk) {
			if (seek + chunk->size > (unsigned) filedata->seek) break;
			seek += chunk->size;
			chunk = chunk->next;
		}
		offset = seek;
		seek = filedata->seek;
	}
	
	if (chunk) {
		totread = 0;
		
		do {
			/* first check if it's on the end if current chunk */
			if (seek-offset == chunk->size) {
				offset += chunk->size;
				chunk = chunk->next;
			}
			
			/* debug, should never happen */
			if (chunk == NULL) {
				printf("illegal read, chunk zero\n");
				return 0;
			}
			
			chunkoffset = seek-offset;
			readsize = size-totread;
			
			/* data can be spread over multiple chunks, so clamp size
			 * to within this chunk, and then it will read further in
			 * the next chunk */
			if (chunkoffset+readsize > chunk->size)
				readsize= chunk->size-chunkoffset;
			
			memcpy((char *)buffer + totread, chunk->buf + chunkoffset, readsize);
			totread += readsize;
			filedata->seek += readsize;
			seek += readsize;
		} while (totread < size);
		
		return totread;
	}
	
	return 0;
}

static FileData *filedata_new(void)
{
	FileData *fd = MEM_callocN(sizeof(FileData), "FileData");
	
	fd->filedes = -1;
	fd->gzfiledes = NULL;
	
	/* XXX, this doesn't need to be done all the time,
	 * but it keeps us re-entrant,  remove once we have
	 * a lib that provides a nice lock. - zr
	 */
	fd->memsdna = DNA_sdna_from_data(DNAstr, DNAlen, false);
	
	fd->datamap = oldnewmap_new();
	fd->globmap = oldnewmap_new();
	fd->libmap = oldnewmap_new();
	
	return fd;
}

static FileData *blo_decode_and_check(FileData *fd, ReportList *reports)
{
	decode_blender_header(fd);
	
	if (fd->flags & FD_FLAGS_FILE_OK) {
		if (!read_file_dna(fd)) {
			BKE_reportf(reports, RPT_ERROR, "Failed to read blend file '%s', incomplete", fd->relabase);
			blo_freefiledata(fd);
			fd = NULL;
		}
	}
	else {
		BKE_reportf(reports, RPT_ERROR, "Failed to read blend file '%s', not a blend file", fd->relabase);
		blo_freefiledata(fd);
		fd = NULL;
	}
	
	return fd;
}

/* cannot be called with relative paths anymore! */
/* on each new library added, it now checks for the current FileData and expands relativeness */
FileData *blo_openblenderfile(const char *filepath, ReportList *reports)
{
	gzFile gzfile;
	errno = 0;
	gzfile = BLI_gzopen(filepath, "rb");
	
	if (gzfile == (gzFile)Z_NULL) {
		BKE_reportf(reports, RPT_WARNING, "Unable to open '%s': %s",
		            filepath, errno ? strerror(errno) : TIP_("unknown error reading file"));
		return NULL;
	}
	else {
		FileData *fd = filedata_new();
		fd->gzfiledes = gzfile;
		fd->read = fd_read_gzip_from_file;
		
		/* needed for library_append and read_libraries */
		BLI_strncpy(fd->relabase, filepath, sizeof(fd->relabase));
		
		return blo_decode_and_check(fd, reports);
	}
}

static int fd_read_gzip_from_memory(FileData *filedata, void *buffer, unsigned int size)
{
	int err;

	filedata->strm.next_out = (Bytef *) buffer;
	filedata->strm.avail_out = size;

	// Inflate another chunk.
	err = inflate (&filedata->strm, Z_SYNC_FLUSH);

	if (err == Z_STREAM_END) {
		return 0;
	}
	else if (err != Z_OK) {
		printf("fd_read_gzip_from_memory: zlib error\n");
		return 0;
	}

	filedata->seek += size;

	return (size);
}

static int fd_read_gzip_from_memory_init(FileData *fd)
{

	fd->strm.next_in = (Bytef *) fd->buffer;
	fd->strm.avail_in = fd->buffersize;
	fd->strm.total_out = 0;
	fd->strm.zalloc = Z_NULL;
	fd->strm.zfree = Z_NULL;
	
	if (inflateInit2(&fd->strm, (16+MAX_WBITS)) != Z_OK)
		return 0;

	fd->read = fd_read_gzip_from_memory;
	
	return 1;
}

FileData *blo_openblendermemory(const void *mem, int memsize, ReportList *reports)
{
	if (!mem || memsize<SIZEOFBLENDERHEADER) {
		BKE_report(reports, RPT_WARNING, (mem) ? TIP_("Unable to read"): TIP_("Unable to open"));
		return NULL;
	}
	else {
		FileData *fd = filedata_new();
		const char *cp = mem;
		
		fd->buffer = mem;
		fd->buffersize = memsize;
		
		/* test if gzip */
		if (cp[0] == 0x1f && cp[1] == 0x8b) {
			if (0 == fd_read_gzip_from_memory_init(fd)) {
				blo_freefiledata(fd);
				return NULL;
			}
		}
		else
			fd->read = fd_read_from_memory;
			
		fd->flags |= FD_FLAGS_NOT_MY_BUFFER;

		return blo_decode_and_check(fd, reports);
	}
}

FileData *blo_openblendermemfile(MemFile *memfile, ReportList *reports)
{
	if (!memfile) {
		BKE_report(reports, RPT_WARNING, "Unable to open blend <memory>");
		return NULL;
	}
	else {
		FileData *fd = filedata_new();
		fd->memfile = memfile;
		
		fd->read = fd_read_from_memfile;
		fd->flags |= FD_FLAGS_NOT_MY_BUFFER;
		
		return blo_decode_and_check(fd, reports);
	}
}


void blo_freefiledata(FileData *fd)
{
	if (fd) {
		if (fd->filedes != -1) {
			close(fd->filedes);
		}
		
		if (fd->gzfiledes != NULL) {
			gzclose(fd->gzfiledes);
		}
		
		if (fd->strm.next_in) {
			if (inflateEnd (&fd->strm) != Z_OK) {
				printf("close gzip stream error\n");
			}
		}
		
		if (fd->buffer && !(fd->flags & FD_FLAGS_NOT_MY_BUFFER)) {
			MEM_freeN((void *)fd->buffer);
			fd->buffer = NULL;
		}
		
		// Free all BHeadN data blocks
		BLI_freelistN(&fd->listbase);
		
		if (fd->memsdna)
			DNA_sdna_free(fd->memsdna);
		if (fd->filesdna)
			DNA_sdna_free(fd->filesdna);
		if (fd->compflags)
			MEM_freeN(fd->compflags);
		
		if (fd->datamap)
			oldnewmap_free(fd->datamap);
		if (fd->globmap)
			oldnewmap_free(fd->globmap);
		if (fd->imamap)
			oldnewmap_free(fd->imamap);
		if (fd->movieclipmap)
			oldnewmap_free(fd->movieclipmap);
		if (fd->packedmap)
			oldnewmap_free(fd->packedmap);
		if (fd->libmap && !(fd->flags & FD_FLAGS_NOT_MY_LIBMAP))
			oldnewmap_free(fd->libmap);
		if (fd->bheadmap)
			MEM_freeN(fd->bheadmap);
		
		MEM_freeN(fd);
	}
}

/* ************ DIV ****************** */

int BLO_has_bfile_extension(const char *str)
{
	return (BLI_testextensie(str, ".ble") || 
	        BLI_testextensie(str, ".blend") || 
	        BLI_testextensie(str, ".blend.gz"));
}

int BLO_is_a_library(const char *path, char *dir, char *group)
{
	/* return ok when a blenderfile, in dir is the filename,
	 * in group the type of libdata
	 */
	int len;
	char *fd;
	
	strcpy(dir, path);
	len = strlen(dir);
	if (len < 7) return 0;
	if ((dir[len - 1] != '/') && (dir[len - 1] != '\\')) return 0;
	
	group[0] = '\0';
	dir[len - 1] = '\0';

	/* Find the last slash */
	fd = (char *)BLI_last_slash(dir);

	if (fd == NULL) return 0;
	*fd = 0;
	if (BLO_has_bfile_extension(fd+1)) {
		/* the last part of the dir is a .blend file, no group follows */
		*fd = '/'; /* put back the removed slash separating the dir and the .blend file name */
	}
	else {
		const char * const gp = fd + 1; // in case we have a .blend file, gp points to the group
		
		/* Find the last slash */
		fd = (char *)BLI_last_slash(dir);
		if (!fd || !BLO_has_bfile_extension(fd+1)) return 0;
		
		/* now we know that we are in a blend file and it is safe to 
		 * assume that gp actually points to a group */
		if (strcmp("Screen", gp) != 0)
			BLI_strncpy(group, gp, GROUP_MAX);
	}
	return 1;
}

/* ************** OLD POINTERS ******************* */

static void *newdataadr(FileData *fd, void *adr)		/* only direct databocks */
{
	return oldnewmap_lookup_and_inc(fd->datamap, adr);
}

static void *newglobadr(FileData *fd, void *adr)	    /* direct datablocks with global linking */
{
	return oldnewmap_lookup_and_inc(fd->globmap, adr);
}

static void *newimaadr(FileData *fd, void *adr)		    /* used to restore image data after undo */
{
	if (fd->imamap && adr)
		return oldnewmap_lookup_and_inc(fd->imamap, adr);
	return NULL;
}

static void *newmclipadr(FileData *fd, void *adr)      /* used to restore movie clip data after undo */
{
	if (fd->movieclipmap && adr)
		return oldnewmap_lookup_and_inc(fd->movieclipmap, adr);
	return NULL;
}

static void *newpackedadr(FileData *fd, void *adr)      /* used to restore packed data after undo */
{
	if (fd->packedmap && adr)
		return oldnewmap_lookup_and_inc(fd->packedmap, adr);
	
	return oldnewmap_lookup_and_inc(fd->datamap, adr);
}


static void *newlibadr(FileData *fd, void *lib, void *adr)		/* only lib data */
{
	return oldnewmap_liblookup(fd->libmap, adr, lib);
}

void *blo_do_versions_newlibadr(FileData *fd, void *lib, void *adr)		/* only lib data */
{
	return newlibadr(fd, lib, adr);
}

static void *newlibadr_us(FileData *fd, void *lib, void *adr)	/* increases user number */
{
	ID *id = newlibadr(fd, lib, adr);
	
	if (id)
		id->us++;
	
	return id;
}

void *blo_do_versions_newlibadr_us(FileData *fd, void *lib, void *adr)	/* increases user number */
{
	return newlibadr_us(fd, lib, adr);
}

static void change_idid_adr_fd(FileData *fd, void *old, void *new)
{
	int i;
	
	for (i = 0; i < fd->libmap->nentries; i++) {
		OldNew *entry = &fd->libmap->entries[i];
		
		if (old==entry->newp && entry->nr==ID_ID) {
			entry->newp = new;
			if (new) entry->nr = GS( ((ID *)new)->name );
		}
	}
}

static void change_idid_adr(ListBase *mainlist, FileData *basefd, void *old, void *new)
{
	Main *mainptr;
	
	for (mainptr = mainlist->first; mainptr; mainptr = mainptr->next) {
		FileData *fd;
		
		if (mainptr->curlib)
			fd = mainptr->curlib->filedata;
		else
			fd = basefd;
		
		if (fd) {
			change_idid_adr_fd(fd, old, new);
		}
	}
}

/* lib linked proxy objects point to our local data, we need
 * to clear that pointer before reading the undo memfile since
 * the object might be removed, it is set again in reading
 * if the local object still exists */
void blo_clear_proxy_pointers_from_lib(Main *oldmain)
{
	Object *ob = oldmain->object.first;
	
	for (; ob; ob= ob->id.next) {
		if (ob->id.lib)
			ob->proxy_from = NULL;
	}
}

void blo_make_image_pointer_map(FileData *fd, Main *oldmain)
{
	Image *ima = oldmain->image.first;
	Scene *sce = oldmain->scene.first;
	int a;
	
	fd->imamap = oldnewmap_new();
	
	for (; ima; ima = ima->id.next) {
		Link *ibuf = ima->ibufs.first;
		for (; ibuf; ibuf = ibuf->next)
			oldnewmap_insert(fd->imamap, ibuf, ibuf, 0);
		if (ima->gputexture)
			oldnewmap_insert(fd->imamap, ima->gputexture, ima->gputexture, 0);
		if (ima->rr)
			oldnewmap_insert(fd->imamap, ima->rr, ima->rr, 0);
		for (a=0; a < IMA_MAX_RENDER_SLOT; a++)
			if (ima->renders[a])
				oldnewmap_insert(fd->imamap, ima->renders[a], ima->renders[a], 0);
	}
	for (; sce; sce = sce->id.next) {
		if (sce->nodetree && sce->nodetree->previews) {
			bNodeInstanceHashIterator iter;
			NODE_INSTANCE_HASH_ITER(iter, sce->nodetree->previews) {
				bNodePreview *preview = BKE_node_instance_hash_iterator_get_value(&iter);
				oldnewmap_insert(fd->imamap, preview, preview, 0);
			}
		}
	}
}

/* set old main image ibufs to zero if it has been restored */
/* this works because freeing old main only happens after this call */
void blo_end_image_pointer_map(FileData *fd, Main *oldmain)
{
	OldNew *entry = fd->imamap->entries;
	Image *ima = oldmain->image.first;
	Scene *sce = oldmain->scene.first;
	int i;
	
	/* used entries were restored, so we put them to zero */
	for (i = 0; i < fd->imamap->nentries; i++, entry++) {
		if (entry->nr > 0)
			entry->newp = NULL;
	}
	
	for (; ima; ima = ima->id.next) {
		Link *ibuf, *next;
		
		/* this mirrors direct_link_image */
		for (ibuf = ima->ibufs.first; ibuf; ibuf = next) {
			next = ibuf->next;
			if (NULL == newimaadr(fd, ibuf)) {	/* so was restored */
				BLI_remlink(&ima->ibufs, ibuf);
				ima->bindcode = 0;
				ima->tpageflag &= ~IMA_GLBIND_IS_DATA;
				ima->gputexture = NULL;
				ima->rr = NULL;
			}
		}
		for (i = 0; i < IMA_MAX_RENDER_SLOT; i++)
			ima->renders[i] = newimaadr(fd, ima->renders[i]);
		
		ima->gputexture = newimaadr(fd, ima->gputexture);
		ima->rr = newimaadr(fd, ima->rr);
	}
	for (; sce; sce = sce->id.next) {
		if (sce->nodetree && sce->nodetree->previews) {
			bNodeInstanceHash *new_previews = BKE_node_instance_hash_new("node previews");
			bNodeInstanceHashIterator iter;
			
			/* reconstruct the preview hash, only using remaining pointers */
			NODE_INSTANCE_HASH_ITER(iter, sce->nodetree->previews) {
				bNodePreview *preview = BKE_node_instance_hash_iterator_get_value(&iter);
				if (preview) {
					bNodePreview *new_preview = newimaadr(fd, preview);
					if (new_preview) {
						bNodeInstanceKey key = BKE_node_instance_hash_iterator_get_key(&iter);
						BKE_node_instance_hash_insert(new_previews, key, new_preview);
					}
				}
			}
			BKE_node_instance_hash_free(sce->nodetree->previews, NULL);
			sce->nodetree->previews = new_previews;
		}
	}
}

void blo_make_movieclip_pointer_map(FileData *fd, Main *oldmain)
{
	MovieClip *clip = oldmain->movieclip.first;
	Scene *sce = oldmain->scene.first;
	
	fd->movieclipmap = oldnewmap_new();
	
	for (; clip; clip = clip->id.next) {
		if (clip->cache)
			oldnewmap_insert(fd->movieclipmap, clip->cache, clip->cache, 0);
		
		if (clip->tracking.camera.intrinsics)
			oldnewmap_insert(fd->movieclipmap, clip->tracking.camera.intrinsics, clip->tracking.camera.intrinsics, 0);
	}
	
	for (; sce; sce = sce->id.next) {
		if (sce->nodetree) {
			bNode *node;
			for (node = sce->nodetree->nodes.first; node; node = node->next)
				if (node->type == CMP_NODE_MOVIEDISTORTION)
					oldnewmap_insert(fd->movieclipmap, node->storage, node->storage, 0);
		}
	}
}

/* set old main movie clips caches to zero if it has been restored */
/* this works because freeing old main only happens after this call */
void blo_end_movieclip_pointer_map(FileData *fd, Main *oldmain)
{
	OldNew *entry = fd->movieclipmap->entries;
	MovieClip *clip = oldmain->movieclip.first;
	Scene *sce = oldmain->scene.first;
	int i;
	
	/* used entries were restored, so we put them to zero */
	for (i=0; i < fd->movieclipmap->nentries; i++, entry++) {
		if (entry->nr > 0)
			entry->newp = NULL;
	}
	
	for (; clip; clip = clip->id.next) {
		clip->cache = newmclipadr(fd, clip->cache);
		clip->tracking.camera.intrinsics = newmclipadr(fd, clip->tracking.camera.intrinsics);
	}
	
	for (; sce; sce = sce->id.next) {
		if (sce->nodetree) {
			bNode *node;
			for (node = sce->nodetree->nodes.first; node; node = node->next)
				if (node->type == CMP_NODE_MOVIEDISTORTION)
					node->storage = newmclipadr(fd, node->storage);
		}
	}
}

/* XXX disabled this feature - packed files also belong in temp saves and quit.blend, to make restore work */

static void insert_packedmap(FileData *fd, PackedFile *pf)
{
	oldnewmap_insert(fd->packedmap, pf, pf, 0);
	oldnewmap_insert(fd->packedmap, pf->data, pf->data, 0);
}

void blo_make_packed_pointer_map(FileData *fd, Main *oldmain)
{
	Image *ima;
	VFont *vfont;
	bSound *sound;
	Library *lib;
	
	fd->packedmap = oldnewmap_new();
	
	for (ima = oldmain->image.first; ima; ima = ima->id.next)
		if (ima->packedfile)
			insert_packedmap(fd, ima->packedfile);
			
	for (vfont = oldmain->vfont.first; vfont; vfont = vfont->id.next)
		if (vfont->packedfile)
			insert_packedmap(fd, vfont->packedfile);
	
	for (sound = oldmain->sound.first; sound; sound = sound->id.next)
		if (sound->packedfile)
			insert_packedmap(fd, sound->packedfile);
	
	for (lib = oldmain->library.first; lib; lib = lib->id.next)
		if (lib->packedfile)
			insert_packedmap(fd, lib->packedfile);

}

/* set old main packed data to zero if it has been restored */
/* this works because freeing old main only happens after this call */
void blo_end_packed_pointer_map(FileData *fd, Main *oldmain)
{
	Image *ima;
	VFont *vfont;
	bSound *sound;
	Library *lib;
	OldNew *entry = fd->packedmap->entries;
	int i;
	
	/* used entries were restored, so we put them to zero */
	for (i=0; i < fd->packedmap->nentries; i++, entry++) {
		if (entry->nr > 0)
			entry->newp = NULL;
	}
	
	for (ima = oldmain->image.first; ima; ima = ima->id.next)
		ima->packedfile = newpackedadr(fd, ima->packedfile);
	
	for (vfont = oldmain->vfont.first; vfont; vfont = vfont->id.next)
		vfont->packedfile = newpackedadr(fd, vfont->packedfile);

	for (sound = oldmain->sound.first; sound; sound = sound->id.next)
		sound->packedfile = newpackedadr(fd, sound->packedfile);
		
	for (lib = oldmain->library.first; lib; lib = lib->id.next)
		lib->packedfile = newpackedadr(fd, lib->packedfile);
}


/* undo file support: add all library pointers in lookup */
void blo_add_library_pointer_map(ListBase *mainlist, FileData *fd)
{
	Main *ptr = mainlist->first;
	ListBase *lbarray[MAX_LIBARRAY];
	
	for (ptr = ptr->next; ptr; ptr = ptr->next) {
		int i = set_listbasepointers(ptr, lbarray);
		while (i--) {
			ID *id;
			for (id = lbarray[i]->first; id; id = id->next)
				oldnewmap_insert(fd->libmap, id, id, GS(id->name));
		}
	}
}


/* ********** END OLD POINTERS ****************** */
/* ********** READ FILE ****************** */

static void switch_endian_structs(struct SDNA *filesdna, BHead *bhead)
{
	int blocksize, nblocks;
	char *data;
	
	data = (char *)(bhead+1);
	blocksize = filesdna->typelens[ filesdna->structs[bhead->SDNAnr][0] ];
	
	nblocks = bhead->nr;
	while (nblocks--) {
		DNA_struct_switch_endian(filesdna, bhead->SDNAnr, data);
		
		data += blocksize;
	}
}

static void *read_struct(FileData *fd, BHead *bh, const char *blockname)
{
	void *temp = NULL;
	
	if (bh->len) {
		/* switch is based on file dna */
		if (bh->SDNAnr && (fd->flags & FD_FLAGS_SWITCH_ENDIAN))
			switch_endian_structs(fd->filesdna, bh);
		
		if (fd->compflags[bh->SDNAnr]) {	/* flag==0: doesn't exist anymore */
			if (fd->compflags[bh->SDNAnr] == 2) {
				temp = DNA_struct_reconstruct(fd->memsdna, fd->filesdna, fd->compflags, bh->SDNAnr, bh->nr, (bh+1));
			}
			else {
				temp = MEM_mallocN(bh->len, blockname);
				memcpy(temp, (bh+1), bh->len);
			}
		}
	}

	return temp;
}

static void link_list(FileData *fd, ListBase *lb)		/* only direct data */
{
	Link *ln, *prev;
	
	if (lb->first == NULL) return;
	
	lb->first = newdataadr(fd, lb->first);
	ln = lb->first;
	prev = NULL;
	while (ln) {
		ln->next = newdataadr(fd, ln->next);
		ln->prev = prev;
		prev = ln;
		ln = ln->next;
	}
	lb->last = prev;
}

static void link_glob_list(FileData *fd, ListBase *lb)		/* for glob data */
{
	Link *ln, *prev;
	void *poin;

	if (lb->first == NULL) return;
	poin = newdataadr(fd, lb->first);
	if (lb->first) {
		oldnewmap_insert(fd->globmap, lb->first, poin, 0);
	}
	lb->first = poin;
	
	ln = lb->first;
	prev = NULL;
	while (ln) {
		poin = newdataadr(fd, ln->next);
		if (ln->next) {
			oldnewmap_insert(fd->globmap, ln->next, poin, 0);
		}
		ln->next = poin;
		ln->prev = prev;
		prev = ln;
		ln = ln->next;
	}
	lb->last = prev;
}

static void test_pointer_array(FileData *fd, void **mat)
{
	int64_t *lpoin, *lmat;
	int *ipoin, *imat;
	size_t len;

		/* manually convert the pointer array in
		 * the old dna format to a pointer array in
		 * the new dna format.
		 */
	if (*mat) {
		len = MEM_allocN_len(*mat)/fd->filesdna->pointerlen;
			
		if (fd->filesdna->pointerlen==8 && fd->memsdna->pointerlen==4) {
			ipoin=imat= MEM_mallocN(len * 4, "newmatar");
			lpoin= *mat;
			
			while (len-- > 0) {
				if ((fd->flags & FD_FLAGS_SWITCH_ENDIAN))
					BLI_endian_switch_int64(lpoin);
				*ipoin = (int)((*lpoin) >> 3);
				ipoin++;
				lpoin++;
			}
			MEM_freeN(*mat);
			*mat = imat;
		}
		
		if (fd->filesdna->pointerlen==4 && fd->memsdna->pointerlen==8) {
			lpoin = lmat = MEM_mallocN(len * 8, "newmatar");
			ipoin = *mat;
			
			while (len-- > 0) {
				*lpoin = *ipoin;
				ipoin++;
				lpoin++;
			}
			MEM_freeN(*mat);
			*mat= lmat;
		}
	}
}

/* ************ READ ID Properties *************** */

static void IDP_DirectLinkProperty(IDProperty *prop, int switch_endian, FileData *fd);
static void IDP_LibLinkProperty(IDProperty *prop, int switch_endian, FileData *fd);

static void IDP_DirectLinkIDPArray(IDProperty *prop, int switch_endian, FileData *fd)
{
	IDProperty *array;
	int i;
	
	/* since we didn't save the extra buffer, set totallen to len */
	prop->totallen = prop->len;
	prop->data.pointer = newdataadr(fd, prop->data.pointer);

	array = (IDProperty *)prop->data.pointer;
	
	/* note!, idp-arrays didn't exist in 2.4x, so the pointer will be cleared
	 * theres not really anything we can do to correct this, at least don't crash */
	if (array == NULL) {
		prop->len = 0;
		prop->totallen = 0;
	}
	
	
	for (i = 0; i < prop->len; i++)
		IDP_DirectLinkProperty(&array[i], switch_endian, fd);
}

static void IDP_DirectLinkArray(IDProperty *prop, int switch_endian, FileData *fd)
{
	IDProperty **array;
	int i;
	
	/* since we didn't save the extra buffer, set totallen to len */
	prop->totallen = prop->len;
	prop->data.pointer = newdataadr(fd, prop->data.pointer);
	
	if (prop->subtype == IDP_GROUP) {
		test_pointer_array(fd, prop->data.pointer);
		array = prop->data.pointer;
		
		for (i = 0; i < prop->len; i++)
			IDP_DirectLinkProperty(array[i], switch_endian, fd);
	}
	else if (prop->subtype == IDP_DOUBLE) {
		if (switch_endian) {
			BLI_endian_switch_double_array(prop->data.pointer, prop->len);
		}
	}
	else {
		if (switch_endian) {
			/* also used for floats */
			BLI_endian_switch_int32_array(prop->data.pointer, prop->len);
		}
	}
}

static void IDP_DirectLinkString(IDProperty *prop, FileData *fd)
{
	/*since we didn't save the extra string buffer, set totallen to len.*/
	prop->totallen = prop->len;
	prop->data.pointer = newdataadr(fd, prop->data.pointer);
}

static void IDP_DirectLinkGroup(IDProperty *prop, int switch_endian, FileData *fd)
{
	ListBase *lb = &prop->data.group;
	IDProperty *loop;
	
	link_list(fd, lb);
	
	/*Link child id properties now*/
	for (loop=prop->data.group.first; loop; loop=loop->next) {
		IDP_DirectLinkProperty(loop, switch_endian, fd);
	}
}

static void IDP_DirectLinkProperty(IDProperty *prop, int switch_endian, FileData *fd)
{
	switch (prop->type) {
		case IDP_GROUP:
			IDP_DirectLinkGroup(prop, switch_endian, fd);
			break;
		case IDP_STRING:
			IDP_DirectLinkString(prop, fd);
			break;
		case IDP_ARRAY:
			IDP_DirectLinkArray(prop, switch_endian, fd);
			break;
		case IDP_IDPARRAY:
			IDP_DirectLinkIDPArray(prop, switch_endian, fd);
			break;
		case IDP_DOUBLE:
			/* erg, stupid doubles.  since I'm storing them
			 * in the same field as int val; val2 in the
			 * IDPropertyData struct, they have to deal with
			 * endianness specifically
			 *
			 * in theory, val and val2 would've already been swapped
			 * if switch_endian is true, so we have to first unswap
			 * them then reswap them as a single 64-bit entity.
			 */
			
			if (switch_endian) {
				BLI_endian_switch_int32(&prop->data.val);
				BLI_endian_switch_int32(&prop->data.val2);
				BLI_endian_switch_int64((int64_t *)&prop->data.val);
			}
			
			break;
	}
}

/* stub function */
static void IDP_LibLinkProperty(IDProperty *UNUSED(prop), int UNUSED(switch_endian), FileData *UNUSED(fd))
{
}

/* ************ READ ID *************** */

static void direct_link_id(FileData *fd, ID *id)
{
	/*link direct data of ID properties*/
	if (id->properties) {
		id->properties = newdataadr(fd, id->properties);
		if (id->properties) { /* this case means the data was written incorrectly, it should not happen */
			IDP_DirectLinkProperty(id->properties, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
		}
	}
}

/* ************ READ CurveMapping *************** */

/* cuma itself has been read! */
static void direct_link_curvemapping(FileData *fd, CurveMapping *cumap)
{
	int a;
	
	/* flag seems to be able to hang? Maybe old files... not bad to clear anyway */
	cumap->flag &= ~CUMA_PREMULLED;
	
	for (a = 0; a < CM_TOT; a++) {
		cumap->cm[a].curve = newdataadr(fd, cumap->cm[a].curve);
		cumap->cm[a].table = NULL;
		cumap->cm[a].premultable = NULL;
	}
}

/* ************ READ Brush *************** */
/* library brush linking after fileread */
static void lib_link_brush(FileData *fd, Main *main)
{
	Brush *brush;
	
	/* only link ID pointers */
	for (brush = main->brush.first; brush; brush = brush->id.next) {
		if (brush->id.flag & LIB_NEED_LINK) {
			brush->id.flag -= LIB_NEED_LINK;
			
			brush->mtex.tex = newlibadr_us(fd, brush->id.lib, brush->mtex.tex);
			brush->mask_mtex.tex = newlibadr_us(fd, brush->id.lib, brush->mask_mtex.tex);
			brush->clone.image = newlibadr_us(fd, brush->id.lib, brush->clone.image);
		}
	}
}

static void direct_link_brush(FileData *fd, Brush *brush)
{
	/* brush itself has been read */

	/* fallof curve */
	brush->curve = newdataadr(fd, brush->curve);
	if (brush->curve)
		direct_link_curvemapping(fd, brush->curve);
	else
		BKE_brush_curve_preset(brush, CURVE_PRESET_SHARP);

	brush->preview = NULL;
	brush->icon_imbuf = NULL;
}

static void direct_link_script(FileData *UNUSED(fd), Script *script)
{
	script->id.us = 1;
	SCRIPT_SET_NULL(script);
}


/* ************ READ PACKEDFILE *************** */

static PackedFile *direct_link_packedfile(FileData *fd, PackedFile *oldpf)
{
	PackedFile *pf = newpackedadr(fd, oldpf);
	
	if (pf) {
		pf->data = newpackedadr(fd, pf->data);
	}
	
	return pf;
}

/* ************ READ IMAGE PREVIEW *************** */

static PreviewImage *direct_link_preview_image(FileData *fd, PreviewImage *old_prv)
{
	PreviewImage *prv = newdataadr(fd, old_prv);
	
	if (prv) {
		int i;
		for (i = 0; i < NUM_ICON_SIZES; ++i) {
			if (prv->rect[i]) {
				prv->rect[i] = newdataadr(fd, prv->rect[i]);
			}
			prv->gputexture[i] = NULL;
		}
	}
	
	return prv;
}

/* ************ READ ANIMATION STUFF ***************** */

/* Legacy Data Support (for Version Patching) ----------------------------- */

// XXX deprecated - old animation system
static void lib_link_ipo(FileData *fd, Main *main)
{
	Ipo *ipo;
	
	for (ipo = main->ipo.first; ipo; ipo = ipo->id.next) {
		if (ipo->id.flag & LIB_NEED_LINK) {
			IpoCurve *icu;
			for (icu = ipo->curve.first; icu; icu = icu->next) {
				if (icu->driver)
					icu->driver->ob = newlibadr(fd, ipo->id.lib, icu->driver->ob);
			}
			ipo->id.flag -= LIB_NEED_LINK;
		}
	}
}

// XXX deprecated - old animation system
static void direct_link_ipo(FileData *fd, Ipo *ipo)
{
	IpoCurve *icu;

	link_list(fd, &(ipo->curve));
	
	for (icu = ipo->curve.first; icu; icu = icu->next) {
		icu->bezt = newdataadr(fd, icu->bezt);
		icu->bp = newdataadr(fd, icu->bp);
		icu->driver = newdataadr(fd, icu->driver);
	}
}

// XXX deprecated - old animation system
static void lib_link_nlastrips(FileData *fd, ID *id, ListBase *striplist)
{
	bActionStrip *strip;
	bActionModifier *amod;
	
	for (strip=striplist->first; strip; strip=strip->next) {
		strip->object = newlibadr(fd, id->lib, strip->object);
		strip->act = newlibadr_us(fd, id->lib, strip->act);
		strip->ipo = newlibadr(fd, id->lib, strip->ipo);
		for (amod = strip->modifiers.first; amod; amod = amod->next)
			amod->ob = newlibadr(fd, id->lib, amod->ob);
	}
}

// XXX deprecated - old animation system
static void direct_link_nlastrips(FileData *fd, ListBase *strips)
{
	bActionStrip *strip;
	
	link_list(fd, strips);
	
	for (strip = strips->first; strip; strip = strip->next)
		link_list(fd, &strip->modifiers);
}

// XXX deprecated - old animation system
static void lib_link_constraint_channels(FileData *fd, ID *id, ListBase *chanbase)
{
	bConstraintChannel *chan;

	for (chan=chanbase->first; chan; chan=chan->next) {
		chan->ipo = newlibadr_us(fd, id->lib, chan->ipo);
	}
}

/* Data Linking ----------------------------- */

static void lib_link_fmodifiers(FileData *fd, ID *id, ListBase *list)
{
	FModifier *fcm;
	
	for (fcm = list->first; fcm; fcm = fcm->next) {
		/* data for specific modifiers */
		switch (fcm->type) {
			case FMODIFIER_TYPE_PYTHON:
			{
				FMod_Python *data = (FMod_Python *)fcm->data;
				data->script = newlibadr(fd, id->lib, data->script);
			}
				break;
		}
	}
}

static void lib_link_fcurves(FileData *fd, ID *id, ListBase *list) 
{
	FCurve *fcu;
	
	if (list == NULL)
		return;
	
	/* relink ID-block references... */
	for (fcu = list->first; fcu; fcu = fcu->next) {
		/* driver data */
		if (fcu->driver) {
			ChannelDriver *driver = fcu->driver;
			DriverVar *dvar;
			
			for (dvar= driver->variables.first; dvar; dvar= dvar->next) {
				DRIVER_TARGETS_LOOPER(dvar)
				{
					/* only relink if still used */
					if (tarIndex < dvar->num_targets)
						dtar->id = newlibadr(fd, id->lib, dtar->id); 
					else
						dtar->id = NULL;
				}
				DRIVER_TARGETS_LOOPER_END
			}
		}
		
		/* modifiers */
		lib_link_fmodifiers(fd, id, &fcu->modifiers);
	}
}


/* NOTE: this assumes that link_list has already been called on the list */
static void direct_link_fmodifiers(FileData *fd, ListBase *list)
{
	FModifier *fcm;
	
	for (fcm = list->first; fcm; fcm = fcm->next) {
		/* relink general data */
		fcm->data  = newdataadr(fd, fcm->data);
		fcm->edata = NULL;
		
		/* do relinking of data for specific types */
		switch (fcm->type) {
			case FMODIFIER_TYPE_GENERATOR:
			{
				FMod_Generator *data = (FMod_Generator *)fcm->data;
				
				data->coefficients = newdataadr(fd, data->coefficients);
				
				if (fd->flags & FD_FLAGS_SWITCH_ENDIAN) {
					BLI_endian_switch_float_array(data->coefficients, data->arraysize);
				}
			}
				break;
			case FMODIFIER_TYPE_ENVELOPE:
			{
				FMod_Envelope *data=  (FMod_Envelope *)fcm->data;
				
				data->data= newdataadr(fd, data->data);
			}
				break;
			case FMODIFIER_TYPE_PYTHON:
			{
				FMod_Python *data = (FMod_Python *)fcm->data;
				
				data->prop = newdataadr(fd, data->prop);
				IDP_DirectLinkProperty(data->prop, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
			}
				break;
		}
	}
}

/* NOTE: this assumes that link_list has already been called on the list */
static void direct_link_fcurves(FileData *fd, ListBase *list)
{
	FCurve *fcu;
	
	/* link F-Curve data to F-Curve again (non ID-libs) */
	for (fcu = list->first; fcu; fcu = fcu->next) {
		/* curve data */
		fcu->bezt = newdataadr(fd, fcu->bezt);
		fcu->fpt = newdataadr(fd, fcu->fpt);
		
		/* rna path */
		fcu->rna_path = newdataadr(fd, fcu->rna_path);
		
		/* group */
		fcu->grp = newdataadr(fd, fcu->grp);
		
		/* clear disabled flag - allows disabled drivers to be tried again ([#32155]),
		 * but also means that another method for "reviving disabled F-Curves" exists
		 */
		fcu->flag &= ~FCURVE_DISABLED;
		
		/* driver */
		fcu->driver= newdataadr(fd, fcu->driver);
		if (fcu->driver) {
			ChannelDriver *driver= fcu->driver;
			DriverVar *dvar;
			
			/* compiled expression data will need to be regenerated (old pointer may still be set here) */
			driver->expr_comp = NULL;
			
			/* give the driver a fresh chance - the operating environment may be different now 
			 * (addons, etc. may be different) so the driver namespace may be sane now [#32155]
			 */
			driver->flag &= ~DRIVER_FLAG_INVALID;
			
			/* relink variables, targets and their paths */
			link_list(fd, &driver->variables);
			for (dvar= driver->variables.first; dvar; dvar= dvar->next) {
				DRIVER_TARGETS_LOOPER(dvar)
				{
					/* only relink the targets being used */
					if (tarIndex < dvar->num_targets)
						dtar->rna_path = newdataadr(fd, dtar->rna_path);
					else
						dtar->rna_path = NULL;
				}
				DRIVER_TARGETS_LOOPER_END
			}
		}
		
		/* modifiers */
		link_list(fd, &fcu->modifiers);
		direct_link_fmodifiers(fd, &fcu->modifiers);
	}
}


static void lib_link_action(FileData *fd, Main *main)
{
	bAction *act;
	bActionChannel *chan;

	for (act = main->action.first; act; act = act->id.next) {
		if (act->id.flag & LIB_NEED_LINK) {
			act->id.flag -= LIB_NEED_LINK;
			
// XXX deprecated - old animation system <<<
			for (chan=act->chanbase.first; chan; chan=chan->next) {
				chan->ipo = newlibadr_us(fd, act->id.lib, chan->ipo);
				lib_link_constraint_channels(fd, &act->id, &chan->constraintChannels);
			}
// >>> XXX deprecated - old animation system
			
			lib_link_fcurves(fd, &act->id, &act->curves);
		}
	}
}

static void direct_link_action(FileData *fd, bAction *act)
{
	bActionChannel *achan; // XXX deprecated - old animation system
	bActionGroup *agrp;

	link_list(fd, &act->curves);
	link_list(fd, &act->chanbase); // XXX deprecated - old animation system
	link_list(fd, &act->groups);
	link_list(fd, &act->markers);

// XXX deprecated - old animation system <<<
	for (achan = act->chanbase.first; achan; achan=achan->next) {
		achan->grp = newdataadr(fd, achan->grp);
		
		link_list(fd, &achan->constraintChannels);
	}
// >>> XXX deprecated - old animation system

	direct_link_fcurves(fd, &act->curves);
	
	for (agrp = act->groups.first; agrp; agrp= agrp->next) {
		agrp->channels.first= newdataadr(fd, agrp->channels.first);
		agrp->channels.last= newdataadr(fd, agrp->channels.last);
	}
}

static void lib_link_nladata_strips(FileData *fd, ID *id, ListBase *list)
{
	NlaStrip *strip;
	
	for (strip = list->first; strip; strip = strip->next) {
		/* check strip's children */
		lib_link_nladata_strips(fd, id, &strip->strips);
		
		/* check strip's F-Curves */
		lib_link_fcurves(fd, id, &strip->fcurves);
		
		/* reassign the counted-reference to action */
		strip->act = newlibadr_us(fd, id->lib, strip->act);
		
		/* fix action id-root (i.e. if it comes from a pre 2.57 .blend file) */
		if ((strip->act) && (strip->act->idroot == 0))
			strip->act->idroot = GS(id->name);
	}
}

static void lib_link_nladata(FileData *fd, ID *id, ListBase *list)
{
	NlaTrack *nlt;
	
	/* we only care about the NLA strips inside the tracks */
	for (nlt = list->first; nlt; nlt = nlt->next) {
		lib_link_nladata_strips(fd, id, &nlt->strips);
	}
}

/* This handles Animato NLA-Strips linking 
 * NOTE: this assumes that link_list has already been called on the list 
 */
static void direct_link_nladata_strips(FileData *fd, ListBase *list)
{
	NlaStrip *strip;
	
	for (strip = list->first; strip; strip = strip->next) {
		/* strip's child strips */
		link_list(fd, &strip->strips);
		direct_link_nladata_strips(fd, &strip->strips);
		
		/* strip's F-Curves */
		link_list(fd, &strip->fcurves);
		direct_link_fcurves(fd, &strip->fcurves);
		
		/* strip's F-Modifiers */
		link_list(fd, &strip->modifiers);
		direct_link_fmodifiers(fd, &strip->modifiers);
	}
}

/* NOTE: this assumes that link_list has already been called on the list */
static void direct_link_nladata(FileData *fd, ListBase *list)
{
	NlaTrack *nlt;
	
	for (nlt = list->first; nlt; nlt = nlt->next) {
		/* relink list of strips */
		link_list(fd, &nlt->strips);
		
		/* relink strip data */
		direct_link_nladata_strips(fd, &nlt->strips);
	}
}

/* ------- */

static void lib_link_keyingsets(FileData *fd, ID *id, ListBase *list)
{
	KeyingSet *ks;
	KS_Path *ksp;
	
	/* here, we're only interested in the ID pointer stored in some of the paths */
	for (ks = list->first; ks; ks = ks->next) {
		for (ksp = ks->paths.first; ksp; ksp = ksp->next) {
			ksp->id= newlibadr(fd, id->lib, ksp->id); 
		}
	}
}

/* NOTE: this assumes that link_list has already been called on the list */
static void direct_link_keyingsets(FileData *fd, ListBase *list)
{
	KeyingSet *ks;
	KS_Path *ksp;
	
	/* link KeyingSet data to KeyingSet again (non ID-libs) */
	for (ks = list->first; ks; ks = ks->next) {
		/* paths */
		link_list(fd, &ks->paths);
		
		for (ksp = ks->paths.first; ksp; ksp = ksp->next) {
			/* rna path */
			ksp->rna_path= newdataadr(fd, ksp->rna_path);
		}
	}
}

/* ------- */

static void lib_link_animdata(FileData *fd, ID *id, AnimData *adt)
{
	if (adt == NULL)
		return;
	
	/* link action data */
	adt->action= newlibadr_us(fd, id->lib, adt->action);
	adt->tmpact= newlibadr_us(fd, id->lib, adt->tmpact);
	
	/* fix action id-roots (i.e. if they come from a pre 2.57 .blend file) */
	if ((adt->action) && (adt->action->idroot == 0))
		adt->action->idroot = GS(id->name);
	if ((adt->tmpact) && (adt->tmpact->idroot == 0))
		adt->tmpact->idroot = GS(id->name);
	
	/* link drivers */
	lib_link_fcurves(fd, id, &adt->drivers);
	
	/* overrides don't have lib-link for now, so no need to do anything */
	
	/* link NLA-data */
	lib_link_nladata(fd, id, &adt->nla_tracks);
}

static void direct_link_animdata(FileData *fd, AnimData *adt)
{
	/* NOTE: must have called newdataadr already before doing this... */
	if (adt == NULL)
		return;
	
	/* link drivers */
	link_list(fd, &adt->drivers);
	direct_link_fcurves(fd, &adt->drivers);
	
	/* link overrides */
	// TODO...
	
	/* link NLA-data */
	link_list(fd, &adt->nla_tracks);
	direct_link_nladata(fd, &adt->nla_tracks);
	
	/* relink active strip - even though strictly speaking this should only be used
	 * if we're in 'tweaking mode', we need to be able to have this loaded back for
	 * undo, but also since users may not exit tweakmode before saving (#24535)
	 */
	// TODO: it's not really nice that anyone should be able to save the file in this
	//		state, but it's going to be too hard to enforce this single case...
	adt->actstrip = newdataadr(fd, adt->actstrip);
}	

/* ************ READ MOTION PATHS *************** */

/* direct data for cache */
static void direct_link_motionpath(FileData *fd, bMotionPath *mpath)
{
	/* sanity check */
	if (mpath == NULL)
		return;
	
	/* relink points cache */
	mpath->points = newdataadr(fd, mpath->points);
}

/* ************ READ NODE TREE *************** */

static void lib_link_node_socket(FileData *fd, ID *UNUSED(id), bNodeSocket *sock)
{
	/* Link ID Properties -- and copy this comment EXACTLY for easy finding
	 * of library blocks that implement this.*/
	if (sock->prop)
		IDP_LibLinkProperty(sock->prop, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
}

/* singe node tree (also used for material/scene trees), ntree is not NULL */
static void lib_link_ntree(FileData *fd, ID *id, bNodeTree *ntree)
{
	bNode *node;
	bNodeSocket *sock;
	
	if (ntree->adt) lib_link_animdata(fd, &ntree->id, ntree->adt);
	
	ntree->gpd = newlibadr_us(fd, id->lib, ntree->gpd);
	
	for (node = ntree->nodes.first; node; node = node->next) {
		/* Link ID Properties -- and copy this comment EXACTLY for easy finding
		 * of library blocks that implement this.*/
		if (node->prop)
			IDP_LibLinkProperty(node->prop, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
		
		node->id= newlibadr_us(fd, id->lib, node->id);

		for (sock = node->inputs.first; sock; sock = sock->next)
			lib_link_node_socket(fd, id, sock);
		for (sock = node->outputs.first; sock; sock = sock->next)
			lib_link_node_socket(fd, id, sock);
	}
	
	for (sock = ntree->inputs.first; sock; sock = sock->next)
		lib_link_node_socket(fd, id, sock);
	for (sock = ntree->outputs.first; sock; sock = sock->next)
		lib_link_node_socket(fd, id, sock);
}

/* library ntree linking after fileread */
static void lib_link_nodetree(FileData *fd, Main *main)
{
	bNodeTree *ntree;
	
	/* only link ID pointers */
	for (ntree = main->nodetree.first; ntree; ntree = ntree->id.next) {
		if (ntree->id.flag & LIB_NEED_LINK) {
			ntree->id.flag -= LIB_NEED_LINK;
			lib_link_ntree(fd, &ntree->id, ntree);
		}
	}
}

/* get node tree stored locally in other IDs */
static bNodeTree *nodetree_from_id(ID *id)
{
	if (!id)
		return NULL;
	switch (GS(id->name)) {
		case ID_SCE: return ((Scene *)id)->nodetree;
		case ID_MA: return ((Material *)id)->nodetree;
		case ID_WO: return ((World *)id)->nodetree;
		case ID_LA: return ((Lamp *)id)->nodetree;
		case ID_TE: return ((Tex *)id)->nodetree;
	}
	return NULL;
}

/* updates group node socket identifier so that
 * external links to/from the group node are preserved.
 */
static void lib_node_do_versions_group_indices(bNode *gnode)
{
	bNodeTree *ngroup = (bNodeTree*)gnode->id;
	bNodeSocket *sock;
	bNodeLink *link;
	
	for (sock=gnode->outputs.first; sock; sock = sock->next) {
		int old_index = sock->to_index;
		
		for (link = ngroup->links.first; link; link = link->next) {
			if (link->tonode == NULL && link->fromsock->own_index == old_index) {
				strcpy(sock->identifier, link->fromsock->identifier);
				/* deprecated */
				sock->own_index = link->fromsock->own_index;
				sock->to_index = 0;
				sock->groupsock = NULL;
			}
		}
	}
	for (sock=gnode->inputs.first; sock; sock = sock->next) {
		int old_index = sock->to_index;
		
		for (link = ngroup->links.first; link; link = link->next) {
			if (link->fromnode == NULL && link->tosock->own_index == old_index) {
				strcpy(sock->identifier, link->tosock->identifier);
				/* deprecated */
				sock->own_index = link->tosock->own_index;
				sock->to_index = 0;
				sock->groupsock = NULL;
			}
		}
	}
}

/* verify types for nodes and groups, all data has to be read */
/* open = 0: appending/linking, open = 1: open new file (need to clean out dynamic
 * typedefs */
static void lib_verify_nodetree(Main *main, int UNUSED(open))
{
	bNodeTree *ntree;
	
	/* this crashes blender on undo/redo */
#if 0
		if (open == 1) {
			reinit_nodesystem();
		}
#endif
	
	/* set node->typeinfo pointers */
	FOREACH_NODETREE(main, ntree, id) {
		ntreeSetTypes(NULL, ntree);
	} FOREACH_NODETREE_END
	
	/* verify static socket templates */
	FOREACH_NODETREE(main, ntree, id) {
		bNode *node;
		for (node=ntree->nodes.first; node; node=node->next)
			node_verify_socket_templates(ntree, node);
	} FOREACH_NODETREE_END
	
	{
		int has_old_groups = 0;
		/* XXX this should actually be part of do_versions, but since we need
		 * finished library linking, it is not possible there. Instead in do_versions
		 * we have set the NTREE_DO_VERSIONS_GROUP_EXPOSE_2_56_2 flag, so at this point we can do the
		 * actual group node updates.
		 */
		for (ntree = main->nodetree.first; ntree; ntree = ntree->id.next) {
			if (ntree->flag & NTREE_DO_VERSIONS_GROUP_EXPOSE_2_56_2)
				has_old_groups = 1;
		}
		
		if (has_old_groups) {
			FOREACH_NODETREE(main, ntree, id) {
				/* updates external links for all group nodes in a tree */
				bNode *node;
				for (node = ntree->nodes.first; node; node = node->next) {
					if (node->type == NODE_GROUP) {
						bNodeTree *ngroup = (bNodeTree*)node->id;
						if (ngroup && (ngroup->flag & NTREE_DO_VERSIONS_GROUP_EXPOSE_2_56_2))
							lib_node_do_versions_group_indices(node);
					}
				}
			} FOREACH_NODETREE_END
		}
		
		for (ntree = main->nodetree.first; ntree; ntree = ntree->id.next)
			ntree->flag &= ~NTREE_DO_VERSIONS_GROUP_EXPOSE_2_56_2;
	}
	
	{
		/* Convert the previously used ntree->inputs/ntree->outputs lists to interface nodes.
		 * Pre 2.56.2 node trees automatically have all unlinked sockets exposed already
		 * (see NTREE_DO_VERSIONS_GROUP_EXPOSE_2_56_2).
		 *
		 * XXX this should actually be part of do_versions,
		 * but needs valid typeinfo pointers to create interface nodes.
		 *
		 * Note: theoretically only needed in node groups (main->nodetree),
		 * but due to a temporary bug such links could have been added in all trees,
		 * so have to clean up all of them ...
		 */
		
		FOREACH_NODETREE(main, ntree, id) {
			if (ntree->flag & NTREE_DO_VERSIONS_CUSTOMNODES_GROUP) {
				bNode *input_node = NULL, *output_node = NULL;
				int num_inputs = 0, num_outputs = 0;
				bNodeLink *link, *next_link;
				/* Only create new interface nodes for actual older files.
				 * New file versions already have input/output nodes with duplicate links,
				 * in that case just remove the invalid links.
				 */
				int create_io_nodes = (ntree->flag & NTREE_DO_VERSIONS_CUSTOMNODES_GROUP_CREATE_INTERFACE);
				
				float input_locx = 1000000.0f, input_locy = 0.0f;
				float output_locx = -1000000.0f, output_locy = 0.0f;
				/* rough guess, not nice but we don't have access to UI constants here ... */
				static const float offsetx = 42 + 3*20 + 20;
				/*static const float offsety = 0.0f;*/
				
				if (create_io_nodes) {
					if (ntree->inputs.first)
						input_node = nodeAddStaticNode(NULL, ntree, NODE_GROUP_INPUT);
					
					if (ntree->outputs.first)
						output_node = nodeAddStaticNode(NULL, ntree, NODE_GROUP_OUTPUT);
				}
				
				/* Redirect links from/to the node tree interface to input/output node.
				 * If the fromnode/tonode pointers are NULL, this means a link from/to
				 * the ntree interface sockets, which need to be redirected to new interface nodes.
				 */
				for (link = ntree->links.first; link; link = next_link) {
					int free_link = FALSE;
					next_link = link->next;
					
					if (link->fromnode == NULL) {
						if (input_node) {
							link->fromnode = input_node;
							link->fromsock = node_group_input_find_socket(input_node, link->fromsock->identifier);
							++num_inputs;
							
							if (link->tonode) {
								if (input_locx > link->tonode->locx - offsetx)
									input_locx = link->tonode->locx - offsetx;
								input_locy += link->tonode->locy;
							}
						}
						else
							free_link = TRUE;
					}
					
					if (link->tonode == NULL) {
						if (output_node) {
							link->tonode = output_node;
							link->tosock = node_group_output_find_socket(output_node, link->tosock->identifier);
							++num_outputs;
							
							if (link->fromnode) {
								if (output_locx < link->fromnode->locx + offsetx)
									output_locx = link->fromnode->locx + offsetx;
								output_locy += link->fromnode->locy;
							}
						}
						else
							free_link = TRUE;
					}
					
					if (free_link)
						nodeRemLink(ntree, link);
				}
				
				if (num_inputs > 0) {
					input_locy /= num_inputs;
					input_node->locx = input_locx;
					input_node->locy = input_locy;
				}
				if (num_outputs > 0) {
					output_locy /= num_outputs;
					output_node->locx = output_locx;
					output_node->locy = output_locy;
				}
				
				/* clear do_versions flags */
				ntree->flag &= ~(NTREE_DO_VERSIONS_CUSTOMNODES_GROUP | NTREE_DO_VERSIONS_CUSTOMNODES_GROUP_CREATE_INTERFACE);
			}
		}
		FOREACH_NODETREE_END
	}
	
	/* verify all group user nodes */
	for (ntree = main->nodetree.first; ntree; ntree = ntree->id.next) {
		ntreeVerifyNodes(main, &ntree->id);
	}
	
	/* make update calls where necessary */
	{
		FOREACH_NODETREE(main, ntree, id) {
			/* make an update call for the tree */
			ntreeUpdateTree(main, ntree);
		} FOREACH_NODETREE_END
	}
}

static void direct_link_node_socket(FileData *fd, bNodeSocket *sock)
{
	sock->prop = newdataadr(fd, sock->prop);
	if (sock->prop)
		IDP_DirectLinkProperty(sock->prop, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
	
	sock->link = newdataadr(fd, sock->link);
	sock->typeinfo = NULL;
	sock->storage = newdataadr(fd, sock->storage);
	sock->default_value = newdataadr(fd, sock->default_value);
	sock->cache = NULL;
}

/* ntree itself has been read! */
static void direct_link_nodetree(FileData *fd, bNodeTree *ntree)
{
	/* note: writing and reading goes in sync, for speed */
	bNode *node;
	bNodeSocket *sock;
	bNodeLink *link;
	
	ntree->init = 0;		/* to set callbacks and force setting types */
	ntree->is_updating = FALSE;
	ntree->typeinfo= NULL;
	ntree->interface_type = NULL;
	
	ntree->progress = NULL;
	ntree->execdata = NULL;
	
	ntree->adt = newdataadr(fd, ntree->adt);
	direct_link_animdata(fd, ntree->adt);
	
	ntree->id.flag &= ~(LIB_ID_RECALC|LIB_ID_RECALC_DATA);

	link_list(fd, &ntree->nodes);
	for (node = ntree->nodes.first; node; node = node->next) {
		node->typeinfo = NULL;
		
		link_list(fd, &node->inputs);
		link_list(fd, &node->outputs);
		
		node->prop = newdataadr(fd, node->prop);
		if (node->prop)
			IDP_DirectLinkProperty(node->prop, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
		
		link_list(fd, &node->internal_links);
		for (link = node->internal_links.first; link; link = link->next) {
			link->fromnode = newdataadr(fd, link->fromnode);
			link->fromsock = newdataadr(fd, link->fromsock);
			link->tonode = newdataadr(fd, link->tonode);
			link->tosock = newdataadr(fd, link->tosock);
		}
		
		if (node->type == CMP_NODE_MOVIEDISTORTION) {
			node->storage = newmclipadr(fd, node->storage);
		}
		else {
			node->storage = newdataadr(fd, node->storage);
		}
		
		if (node->storage) {
			/* could be handlerized at some point */
			if (ntree->type==NTREE_SHADER) {
				if (node->type==SH_NODE_CURVE_VEC || node->type==SH_NODE_CURVE_RGB) {
					direct_link_curvemapping(fd, node->storage);
				}
				else if (node->type==SH_NODE_SCRIPT) {
					NodeShaderScript *nss = (NodeShaderScript *) node->storage;
					nss->bytecode = newdataadr(fd, nss->bytecode);
				}
			}
			else if (ntree->type==NTREE_COMPOSIT) {
				if (ELEM4(node->type, CMP_NODE_TIME, CMP_NODE_CURVE_VEC, CMP_NODE_CURVE_RGB, CMP_NODE_HUECORRECT))
					direct_link_curvemapping(fd, node->storage);
				else if (ELEM3(node->type, CMP_NODE_IMAGE, CMP_NODE_VIEWER, CMP_NODE_SPLITVIEWER))
					((ImageUser *)node->storage)->ok = 1;
			}
			else if ( ntree->type==NTREE_TEXTURE) {
				if (node->type==TEX_NODE_CURVE_RGB || node->type==TEX_NODE_CURVE_TIME)
					direct_link_curvemapping(fd, node->storage);
				else if (node->type==TEX_NODE_IMAGE)
					((ImageUser *)node->storage)->ok = 1;
			}
		}
	}
	link_list(fd, &ntree->links);
	
	/* and we connect the rest */
	for (node = ntree->nodes.first; node; node = node->next) {
		node->parent = newdataadr(fd, node->parent);
		node->lasty = 0;
		
		for (sock = node->inputs.first; sock; sock = sock->next)
			direct_link_node_socket(fd, sock);
		for (sock = node->outputs.first; sock; sock = sock->next)
			direct_link_node_socket(fd, sock);
	}
	
	/* interface socket lists */
	link_list(fd, &ntree->inputs);
	link_list(fd, &ntree->outputs);
	for (sock = ntree->inputs.first; sock; sock = sock->next)
		direct_link_node_socket(fd, sock);
	for (sock = ntree->outputs.first; sock; sock = sock->next)
		direct_link_node_socket(fd, sock);
	
	for (link = ntree->links.first; link; link= link->next) {
		link->fromnode = newdataadr(fd, link->fromnode);
		link->tonode = newdataadr(fd, link->tonode);
		link->fromsock = newdataadr(fd, link->fromsock);
		link->tosock = newdataadr(fd, link->tosock);
	}
	
#if 0
	if (ntree->previews) {
		bNodeInstanceHash *new_previews = BKE_node_instance_hash_new("node previews");
		bNodeInstanceHashIterator iter;
		
		NODE_INSTANCE_HASH_ITER(iter, ntree->previews) {
			bNodePreview *preview = BKE_node_instance_hash_iterator_get_value(&iter);
			if (preview) {
				bNodePreview *new_preview = newimaadr(fd, preview);
				if (new_preview) {
					bNodeInstanceKey key = BKE_node_instance_hash_iterator_get_key(&iter);
					BKE_node_instance_hash_insert(new_previews, key, new_preview);
				}
			}
		}
		BKE_node_instance_hash_free(ntree->previews, NULL);
		ntree->previews = new_previews;
	}
#else
	/* XXX TODO */
	ntree->previews = NULL;
#endif
	
	/* type verification is in lib-link */
}

/* ************ READ ARMATURE ***************** */

/* temp struct used to transport needed info to lib_link_constraint_cb() */
typedef struct tConstraintLinkData {
	FileData *fd;
	ID *id;
} tConstraintLinkData;
/* callback function used to relink constraint ID-links */
static void lib_link_constraint_cb(bConstraint *UNUSED(con), ID **idpoin, short isReference, void *userdata)
{
	tConstraintLinkData *cld= (tConstraintLinkData *)userdata;
	
	/* for reference types, we need to increment the usercounts on load... */
	if (isReference) {
		/* reference type - with usercount */
		*idpoin = newlibadr_us(cld->fd, cld->id->lib, *idpoin);
	}
	else {
		/* target type - no usercount needed */
		*idpoin = newlibadr(cld->fd, cld->id->lib, *idpoin);
	}
}

static void lib_link_constraints(FileData *fd, ID *id, ListBase *conlist)
{
	tConstraintLinkData cld;
	bConstraint *con;
	
	/* legacy fixes */
	for (con = conlist->first; con; con=con->next) {
		/* patch for error introduced by changing constraints (dunno how) */
		/* if con->data type changes, dna cannot resolve the pointer! (ton) */
		if (con->data == NULL) {
			con->type = CONSTRAINT_TYPE_NULL;
		}
		/* own ipo, all constraints have it */
		con->ipo = newlibadr_us(fd, id->lib, con->ipo); // XXX deprecated - old animation system
	}
	
	/* relink all ID-blocks used by the constraints */
	cld.fd = fd;
	cld.id = id;
	
	BKE_id_loop_constraints(conlist, lib_link_constraint_cb, &cld);
}

static void direct_link_constraints(FileData *fd, ListBase *lb)
{
	bConstraint *con;
	
	link_list(fd, lb);
	for (con=lb->first; con; con=con->next) {
		con->data = newdataadr(fd, con->data);
		
		switch (con->type) {
			case CONSTRAINT_TYPE_PYTHON:
			{
				bPythonConstraint *data= con->data;
				
				link_list(fd, &data->targets);
				
				data->prop = newdataadr(fd, data->prop);
				if (data->prop)
					IDP_DirectLinkProperty(data->prop, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
				break;
			}
			case CONSTRAINT_TYPE_SPLINEIK:
			{
				bSplineIKConstraint *data= con->data;

				data->points= newdataadr(fd, data->points);
				break;
			}
			case CONSTRAINT_TYPE_KINEMATIC:
			{
				bKinematicConstraint *data = con->data;

				con->lin_error = 0.f;
				con->rot_error = 0.f;

				/* version patch for runtime flag, was not cleared in some case */
				data->flag &= ~CONSTRAINT_IK_AUTO;
				break;
			}
			case CONSTRAINT_TYPE_CHILDOF:
			{
				/* XXX version patch, in older code this flag wasn't always set, and is inherent to type */
				if (con->ownspace == CONSTRAINT_SPACE_POSE)
					con->flag |= CONSTRAINT_SPACEONCE;
				break;
			}
		}
	}
}

static void lib_link_pose(FileData *fd, Main *bmain, Object *ob, bPose *pose)
{
	bPoseChannel *pchan;
	bArmature *arm = ob->data;
	int rebuild = 0;
	
	if (!pose || !arm)
		return;
	
	/* always rebuild to match proxy or lib changes, but on Undo */
	if (fd->memfile == NULL)
		if (ob->proxy || (ob->id.lib==NULL && arm->id.lib))
			rebuild = 1;
	
	if (ob->proxy) {
		/* sync proxy layer */
		if (pose->proxy_layer)
			arm->layer = pose->proxy_layer;
		
		/* sync proxy active bone */
		if (pose->proxy_act_bone[0]) {
			Bone *bone = BKE_armature_find_bone_name(arm, pose->proxy_act_bone);
			if (bone)
				arm->act_bone = bone;
		}
	}
	
	for (pchan = pose->chanbase.first; pchan; pchan=pchan->next) {
		lib_link_constraints(fd, (ID *)ob, &pchan->constraints);
		
		/* hurms... loop in a loop, but yah... later... (ton) */
		pchan->bone = BKE_armature_find_bone_name(arm, pchan->name);
		
		pchan->custom = newlibadr_us(fd, arm->id.lib, pchan->custom);
		if (pchan->bone == NULL)
			rebuild= 1;
		else if (ob->id.lib==NULL && arm->id.lib) {
			/* local pose selection copied to armature, bit hackish */
			pchan->bone->flag &= ~BONE_SELECTED;
			pchan->bone->flag |= pchan->selectflag;
		}
	}
	
	if (rebuild) {
		DAG_id_tag_update_ex(bmain, &ob->id, OB_RECALC_OB | OB_RECALC_DATA | OB_RECALC_TIME);
		pose->flag |= POSE_RECALC;
	}
}

static void lib_link_armature(FileData *fd, Main *main)
{
	bArmature *arm;
	
	for (arm = main->armature.first; arm; arm = arm->id.next) {
		if (arm->id.flag & LIB_NEED_LINK) {
			if (arm->adt) lib_link_animdata(fd, &arm->id, arm->adt);
			arm->id.flag -= LIB_NEED_LINK;
		}
	}
}

static void direct_link_bones(FileData *fd, Bone *bone)
{
	Bone *child;
	
	bone->parent = newdataadr(fd, bone->parent);
	bone->prop = newdataadr(fd, bone->prop);
	if (bone->prop)
		IDP_DirectLinkProperty(bone->prop, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
		
	bone->flag &= ~BONE_DRAW_ACTIVE;
	
	link_list(fd, &bone->childbase);
	
	for (child=bone->childbase.first; child; child=child->next)
		direct_link_bones(fd, child);
}

static void direct_link_armature(FileData *fd, bArmature *arm)
{
	Bone *bone;
	
	link_list(fd, &arm->bonebase);
	arm->edbo = NULL;
	arm->sketch = NULL;
	
	arm->adt = newdataadr(fd, arm->adt);
	direct_link_animdata(fd, arm->adt);
	
	for (bone = arm->bonebase.first; bone; bone = bone->next) {
		direct_link_bones(fd, bone);
	}
	
	arm->act_bone = newdataadr(fd, arm->act_bone);
	arm->act_edbone = NULL;
}

/* ************ READ CAMERA ***************** */

static void lib_link_camera(FileData *fd, Main *main)
{
	Camera *ca;
	
	for (ca = main->camera.first; ca; ca = ca->id.next) {
		if (ca->id.flag & LIB_NEED_LINK) {
			if (ca->adt) lib_link_animdata(fd, &ca->id, ca->adt);
			
			ca->ipo = newlibadr_us(fd, ca->id.lib, ca->ipo); // XXX deprecated - old animation system
			
			ca->dof_ob = newlibadr_us(fd, ca->id.lib, ca->dof_ob);
			
			ca->id.flag -= LIB_NEED_LINK;
		}
	}
}

static void direct_link_camera(FileData *fd, Camera *ca)
{
	ca->adt = newdataadr(fd, ca->adt);
	direct_link_animdata(fd, ca->adt);
}


/* ************ READ LAMP ***************** */

static void lib_link_lamp(FileData *fd, Main *main)
{
	Lamp *la;
	MTex *mtex;
	int a;
	
	for (la = main->lamp.first; la; la = la->id.next) {
		if (la->id.flag & LIB_NEED_LINK) {
			if (la->adt) lib_link_animdata(fd, &la->id, la->adt);
			
			for (a = 0; a < MAX_MTEX; a++) {
				mtex = la->mtex[a];
				if (mtex) {
					mtex->tex = newlibadr_us(fd, la->id.lib, mtex->tex);
					mtex->object = newlibadr(fd, la->id.lib, mtex->object);
				}
			}
			
			la->ipo = newlibadr_us(fd, la->id.lib, la->ipo); // XXX deprecated - old animation system
			
			if (la->nodetree) {
				lib_link_ntree(fd, &la->id, la->nodetree);
				la->nodetree->id.lib = la->id.lib;
			}
			
			la->id.flag -= LIB_NEED_LINK;
		}
	}
}

static void direct_link_lamp(FileData *fd, Lamp *la)
{
	int a;
	
	la->adt = newdataadr(fd, la->adt);
	direct_link_animdata(fd, la->adt);
	
	for (a=0; a<MAX_MTEX; a++) {
		la->mtex[a] = newdataadr(fd, la->mtex[a]);
	}
	
	la->curfalloff = newdataadr(fd, la->curfalloff);
	if (la->curfalloff)
		direct_link_curvemapping(fd, la->curfalloff);

	la->nodetree= newdataadr(fd, la->nodetree);
	if (la->nodetree) {
		direct_link_id(fd, &la->nodetree->id);
		direct_link_nodetree(fd, la->nodetree);
	}
	
	la->preview = direct_link_preview_image(fd, la->preview);
}

/* ************ READ keys ***************** */

static void do_versions_key_uidgen(Key *key)
{
	KeyBlock *block;

	key->uidgen = 1;
	for (block = key->block.first; block; block = block->next) {
		block->uid = key->uidgen++;
	}
}

static void lib_link_key(FileData *fd, Main *main)
{
	Key *key;
	
	for (key = main->key.first; key; key = key->id.next) {
		/*check if we need to generate unique ids for the shapekeys*/
		if (!key->uidgen) {
			do_versions_key_uidgen(key);
		}
		
		if (key->id.flag & LIB_NEED_LINK) {
			if (key->adt) lib_link_animdata(fd, &key->id, key->adt);
			
			key->ipo = newlibadr_us(fd, key->id.lib, key->ipo); // XXX deprecated - old animation system
			key->from = newlibadr(fd, key->id.lib, key->from);
			
			key->id.flag -= LIB_NEED_LINK;
		}
	}
}

static void switch_endian_keyblock(Key *key, KeyBlock *kb)
{
	int elemsize, a, b;
	char *data, *poin, *cp;
	
	elemsize = key->elemsize;
	data = kb->data;
	
	for (a = 0; a < kb->totelem; a++) {
		cp = key->elemstr;
		poin = data;
		
		while (cp[0]) {  /* cp[0] == amount */
			switch (cp[1]) {  /* cp[1] = type */
				case IPO_FLOAT:
				case IPO_BPOINT:
				case IPO_BEZTRIPLE:
					b = cp[0];
					BLI_endian_switch_float_array((float *)poin, b);
					poin += sizeof(float) * b;
					break;
			}
			
			cp += 2;
		}
		data += elemsize;
	}
}

static void direct_link_key(FileData *fd, Key *key)
{
	KeyBlock *kb;
	
	link_list(fd, &(key->block));
	
	key->adt = newdataadr(fd, key->adt);
	direct_link_animdata(fd, key->adt);
		
	key->refkey= newdataadr(fd, key->refkey);
	
	for (kb = key->block.first; kb; kb = kb->next) {
		kb->data = newdataadr(fd, kb->data);
		
		if (fd->flags & FD_FLAGS_SWITCH_ENDIAN)
			switch_endian_keyblock(key, kb);
	}
}

/* ************ READ mball ***************** */

static void lib_link_mball(FileData *fd, Main *main)
{
	MetaBall *mb;
	int a;
	
	for (mb = main->mball.first; mb; mb = mb->id.next) {
		if (mb->id.flag & LIB_NEED_LINK) {
			if (mb->adt) lib_link_animdata(fd, &mb->id, mb->adt);
			
			for (a = 0; a < mb->totcol; a++) 
				mb->mat[a] = newlibadr_us(fd, mb->id.lib, mb->mat[a]);
			
			mb->ipo = newlibadr_us(fd, mb->id.lib, mb->ipo); // XXX deprecated - old animation system
			
			mb->id.flag -= LIB_NEED_LINK;
		}
	}
}

static void direct_link_mball(FileData *fd, MetaBall *mb)
{
	mb->adt = newdataadr(fd, mb->adt);
	direct_link_animdata(fd, mb->adt);
	
	mb->mat = newdataadr(fd, mb->mat);
	test_pointer_array(fd, (void **)&mb->mat);
	
	link_list(fd, &(mb->elems));
	
	mb->disp.first = mb->disp.last = NULL;
	mb->editelems = NULL;
	mb->bb = NULL;
/*	mb->edit_elems.first= mb->edit_elems.last= NULL;*/
	mb->lastelem = NULL;
}

/* ************ READ WORLD ***************** */

static void lib_link_world(FileData *fd, Main *main)
{
	World *wrld;
	MTex *mtex;
	int a;
	
	for (wrld = main->world.first; wrld; wrld = wrld->id.next) {
		if (wrld->id.flag & LIB_NEED_LINK) {
			if (wrld->adt) lib_link_animdata(fd, &wrld->id, wrld->adt);
			
			wrld->ipo = newlibadr_us(fd, wrld->id.lib, wrld->ipo); // XXX deprecated - old animation system
			
			for (a=0; a < MAX_MTEX; a++) {
				mtex = wrld->mtex[a];
				if (mtex) {
					mtex->tex = newlibadr_us(fd, wrld->id.lib, mtex->tex);
					mtex->object = newlibadr(fd, wrld->id.lib, mtex->object);
				}
			}
			
			if (wrld->nodetree) {
				lib_link_ntree(fd, &wrld->id, wrld->nodetree);
				wrld->nodetree->id.lib = wrld->id.lib;
			}
			
			wrld->id.flag -= LIB_NEED_LINK;
		}
	}
}

static void direct_link_world(FileData *fd, World *wrld)
{
	int a;
	
	wrld->adt = newdataadr(fd, wrld->adt);
	direct_link_animdata(fd, wrld->adt);
	
	for (a = 0; a < MAX_MTEX; a++) {
		wrld->mtex[a] = newdataadr(fd, wrld->mtex[a]);
	}
	
	wrld->nodetree = newdataadr(fd, wrld->nodetree);
	if (wrld->nodetree) {
		direct_link_id(fd, &wrld->nodetree->id);
		direct_link_nodetree(fd, wrld->nodetree);
	}
	
	wrld->preview = direct_link_preview_image(fd, wrld->preview);
}


/* ************ READ VFONT ***************** */

static void lib_link_vfont(FileData *UNUSED(fd), Main *main)
{
	VFont *vf;
	
	for (vf = main->vfont.first; vf; vf = vf->id.next) {
		if (vf->id.flag & LIB_NEED_LINK) {
			vf->id.flag -= LIB_NEED_LINK;
		}
	}
}

static void direct_link_vfont(FileData *fd, VFont *vf)
{
	vf->data = NULL;
	vf->temp_pf = NULL;
	vf->packedfile = direct_link_packedfile(fd, vf->packedfile);
}

/* ************ READ TEXT ****************** */

static void lib_link_text(FileData *UNUSED(fd), Main *main)
{
	Text *text;
	
	for (text = main->text.first; text; text = text->id.next) {
		if (text->id.flag & LIB_NEED_LINK) {
			text->id.flag -= LIB_NEED_LINK;
		}
	}
}

static void direct_link_text(FileData *fd, Text *text)
{
	TextLine *ln;
	
	text->name = newdataadr(fd, text->name);
	
	text->undo_pos = -1;
	text->undo_len = TXT_INIT_UNDO;
	text->undo_buf = MEM_mallocN(text->undo_len, "undo buf");
	
	text->compiled = NULL;
	
#if 0
	if (text->flags & TXT_ISEXT) {
		BKE_text_reload(text);
		}
		/* else { */
#endif
	
	link_list(fd, &text->lines);
	
	text->curl = newdataadr(fd, text->curl);
	text->sell = newdataadr(fd, text->sell);
	
	for (ln = text->lines.first; ln; ln = ln->next) {
		ln->line = newdataadr(fd, ln->line);
		ln->format = NULL;
		
		if (ln->len != (int) strlen(ln->line)) {
			printf("Error loading text, line lengths differ\n");
			ln->len = strlen(ln->line);
		}
	}
	
	text->flags = (text->flags) & ~TXT_ISEXT;
	
	text->id.us = 1;
}

/* ************ READ IMAGE ***************** */

static void lib_link_image(FileData *fd, Main *main)
{
	Image *ima;
	
	for (ima = main->image.first; ima; ima = ima->id.next) {
		if (ima->id.flag & LIB_NEED_LINK) {
			if (ima->id.properties) IDP_LibLinkProperty(ima->id.properties, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
			
			ima->id.flag -= LIB_NEED_LINK;
		}
	}
}

static void link_ibuf_list(FileData *fd, ListBase *lb)
{
	Link *ln, *prev;
	
	if (lb->first == NULL) return;
	
	lb->first = newimaadr(fd, lb->first);
	ln = lb->first;
	prev = NULL;
	while (ln) {
		ln->next = newimaadr(fd, ln->next);
		ln->prev = prev;
		prev = ln;
		ln = ln->next;
	}
	lb->last = prev;
}

static void direct_link_image(FileData *fd, Image *ima)
{
	/* for undo system, pointers could be restored */
	if (fd->imamap)
		link_ibuf_list(fd, &ima->ibufs);
	else
		ima->ibufs.first = ima->ibufs.last = NULL;

	/* if not restored, we keep the binded opengl index */
	if (ima->ibufs.first == NULL) {
		ima->bindcode = 0;
		ima->tpageflag &= ~IMA_GLBIND_IS_DATA;
		ima->gputexture = NULL;
		ima->rr = NULL;
	}
	
	ima->anim = NULL;
	ima->repbind = NULL;
	
	/* undo system, try to restore render buffers */
	if (fd->imamap) {
		int a;
		
		for (a = 0; a < IMA_MAX_RENDER_SLOT; a++)
			ima->renders[a] = newimaadr(fd, ima->renders[a]);
	}
	else {
		memset(ima->renders, 0, sizeof(ima->renders));
		ima->last_render_slot = ima->render_slot;
	}
	
	ima->packedfile = direct_link_packedfile(fd, ima->packedfile);
	ima->preview = direct_link_preview_image(fd, ima->preview);
	ima->ok = 1;
}


/* ************ READ CURVE ***************** */

static void lib_link_curve(FileData *fd, Main *main)
{
	Curve *cu;
	int a;
	
	for (cu = main->curve.first; cu; cu = cu->id.next) {
		if (cu->id.flag & LIB_NEED_LINK) {
			if (cu->adt) lib_link_animdata(fd, &cu->id, cu->adt);
			
			for (a = 0; a < cu->totcol; a++) 
				cu->mat[a] = newlibadr_us(fd, cu->id.lib, cu->mat[a]);
			
			cu->bevobj = newlibadr(fd, cu->id.lib, cu->bevobj);
			cu->taperobj = newlibadr(fd, cu->id.lib, cu->taperobj);
			cu->textoncurve = newlibadr(fd, cu->id.lib, cu->textoncurve);
			cu->vfont = newlibadr_us(fd, cu->id.lib, cu->vfont);
			cu->vfontb = newlibadr_us(fd, cu->id.lib, cu->vfontb);
			cu->vfonti = newlibadr_us(fd, cu->id.lib, cu->vfonti);
			cu->vfontbi = newlibadr_us(fd, cu->id.lib, cu->vfontbi);
			
			cu->ipo = newlibadr_us(fd, cu->id.lib, cu->ipo); // XXX deprecated - old animation system
			cu->key = newlibadr_us(fd, cu->id.lib, cu->key);
			
			cu->id.flag -= LIB_NEED_LINK;
		}
	}
}


static void switch_endian_knots(Nurb *nu)
{
	if (nu->knotsu) {
		BLI_endian_switch_float_array(nu->knotsu, KNOTSU(nu));
	}
	if (nu->knotsv) {
		BLI_endian_switch_float_array(nu->knotsv, KNOTSV(nu));
	}
}

static void direct_link_curve(FileData *fd, Curve *cu)
{
	Nurb *nu;
	TextBox *tb;
	
	cu->adt= newdataadr(fd, cu->adt);
	direct_link_animdata(fd, cu->adt);
	
	cu->mat = newdataadr(fd, cu->mat);
	test_pointer_array(fd, (void **)&cu->mat);
	cu->str = newdataadr(fd, cu->str);
	cu->strinfo= newdataadr(fd, cu->strinfo);
	cu->tb = newdataadr(fd, cu->tb);

	if (cu->vfont == NULL) {
		link_list(fd, &(cu->nurb));
	}
	else {
		cu->nurb.first=cu->nurb.last= NULL;
		
		tb = MEM_callocN(MAXTEXTBOX*sizeof(TextBox), "TextBoxread");
		if (cu->tb) {
			memcpy(tb, cu->tb, cu->totbox*sizeof(TextBox));
			MEM_freeN(cu->tb);
			cu->tb = tb;
		}
		else {
			cu->totbox = 1;
			cu->actbox = 1;
			cu->tb = tb;
			cu->tb[0].w = cu->linewidth;
		}
		if (cu->wordspace == 0.0f) cu->wordspace = 1.0f;
	}

	cu->bev.first = cu->bev.last = NULL;
	cu->editnurb = NULL;
	cu->lastsel = NULL;
	cu->path = NULL;
	cu->editfont = NULL;
	
	for (nu = cu->nurb.first; nu; nu = nu->next) {
		nu->bezt = newdataadr(fd, nu->bezt);
		nu->bp = newdataadr(fd, nu->bp);
		nu->knotsu = newdataadr(fd, nu->knotsu);
		nu->knotsv = newdataadr(fd, nu->knotsv);
		if (cu->vfont == NULL) nu->charidx= nu->mat_nr;
		
		if (fd->flags & FD_FLAGS_SWITCH_ENDIAN) {
			switch_endian_knots(nu);
		}
	}
	cu->bb = NULL;
}

/* ************ READ TEX ***************** */

static void lib_link_texture(FileData *fd, Main *main)
{
	Tex *tex;
	
	for (tex = main->tex.first; tex; tex = tex->id.next) {
		if (tex->id.flag & LIB_NEED_LINK) {
			if (tex->adt) lib_link_animdata(fd, &tex->id, tex->adt);
			
			tex->ima = newlibadr_us(fd, tex->id.lib, tex->ima);
			tex->ipo = newlibadr_us(fd, tex->id.lib, tex->ipo);
			if (tex->env)
				tex->env->object = newlibadr(fd, tex->id.lib, tex->env->object);
			if (tex->pd)
				tex->pd->object = newlibadr(fd, tex->id.lib, tex->pd->object);
			if (tex->vd)
				tex->vd->object = newlibadr(fd, tex->id.lib, tex->vd->object);
			if (tex->ot)
				tex->ot->object = newlibadr(fd, tex->id.lib, tex->ot->object);
			
			if (tex->nodetree) {
				lib_link_ntree(fd, &tex->id, tex->nodetree);
				tex->nodetree->id.lib = tex->id.lib;
			}
			
			tex->id.flag -= LIB_NEED_LINK;
		}
	}
}

static void direct_link_texture(FileData *fd, Tex *tex)
{
	tex->adt = newdataadr(fd, tex->adt);
	direct_link_animdata(fd, tex->adt);

	tex->coba = newdataadr(fd, tex->coba);
	tex->env = newdataadr(fd, tex->env);
	if (tex->env) {
		tex->env->ima = NULL;
		memset(tex->env->cube, 0, 6 * sizeof(void *));
		tex->env->ok= 0;
	}
	tex->pd = newdataadr(fd, tex->pd);
	if (tex->pd) {
		tex->pd->point_tree = NULL;
		tex->pd->coba = newdataadr(fd, tex->pd->coba);
		tex->pd->falloff_curve = newdataadr(fd, tex->pd->falloff_curve);
		if (tex->pd->falloff_curve) {
			direct_link_curvemapping(fd, tex->pd->falloff_curve);
		}
	}
	
	tex->vd = newdataadr(fd, tex->vd);
	if (tex->vd) {
		tex->vd->dataset = NULL;
		tex->vd->ok = 0;
	}
	else {
		if (tex->type == TEX_VOXELDATA)
			tex->vd = MEM_callocN(sizeof(VoxelData), "direct_link_texture VoxelData");
	}
	
	tex->ot = newdataadr(fd, tex->ot);
	
	tex->nodetree = newdataadr(fd, tex->nodetree);
	if (tex->nodetree) {
		direct_link_id(fd, &tex->nodetree->id);
		direct_link_nodetree(fd, tex->nodetree);
	}
	
	tex->preview = direct_link_preview_image(fd, tex->preview);
	
	tex->iuser.ok = 1;
}



/* ************ READ MATERIAL ***************** */

static void lib_link_material(FileData *fd, Main *main)
{
	Material *ma;
	MTex *mtex;
	int a;
	
	for (ma = main->mat.first; ma; ma = ma->id.next) {
		if (ma->id.flag & LIB_NEED_LINK) {
			if (ma->adt) lib_link_animdata(fd, &ma->id, ma->adt);
			
			/* Link ID Properties -- and copy this comment EXACTLY for easy finding
			 * of library blocks that implement this.*/
			if (ma->id.properties) IDP_LibLinkProperty(ma->id.properties, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
			
			ma->ipo = newlibadr_us(fd, ma->id.lib, ma->ipo);
			ma->group = newlibadr_us(fd, ma->id.lib, ma->group);
			
			for (a = 0; a < MAX_MTEX; a++) {
				mtex = ma->mtex[a];
				if (mtex) {
					mtex->tex = newlibadr_us(fd, ma->id.lib, mtex->tex);
					mtex->object = newlibadr(fd, ma->id.lib, mtex->object);
				}
			}
			
			if (ma->nodetree) {
				lib_link_ntree(fd, &ma->id, ma->nodetree);
				ma->nodetree->id.lib = ma->id.lib;
			}
			
			ma->id.flag -= LIB_NEED_LINK;
		}
	}
}

static void direct_link_material(FileData *fd, Material *ma)
{
	int a;
	
	ma->adt = newdataadr(fd, ma->adt);
	direct_link_animdata(fd, ma->adt);
	
	for (a = 0; a < MAX_MTEX; a++) {
		ma->mtex[a] = newdataadr(fd, ma->mtex[a]);
	}
	
	ma->ramp_col = newdataadr(fd, ma->ramp_col);
	ma->ramp_spec = newdataadr(fd, ma->ramp_spec);
	
	ma->nodetree = newdataadr(fd, ma->nodetree);
	if (ma->nodetree) {
		direct_link_id(fd, &ma->nodetree->id);
		direct_link_nodetree(fd, ma->nodetree);
	}
	
	ma->preview = direct_link_preview_image(fd, ma->preview);
	ma->gpumaterial.first = ma->gpumaterial.last = NULL;
}

/* ************ READ PARTICLE SETTINGS ***************** */
/* update this also to writefile.c */
static const char *ptcache_data_struct[] = {
	"", // BPHYS_DATA_INDEX
	"", // BPHYS_DATA_LOCATION
	"", // BPHYS_DATA_VELOCITY
	"", // BPHYS_DATA_ROTATION
	"", // BPHYS_DATA_AVELOCITY / BPHYS_DATA_XCONST */
	"", // BPHYS_DATA_SIZE:
	"", // BPHYS_DATA_TIMES:
	"BoidData" // case BPHYS_DATA_BOIDS:
};
static void direct_link_pointcache(FileData *fd, PointCache *cache)
{
	if ((cache->flag & PTCACHE_DISK_CACHE)==0) {
		PTCacheMem *pm;
		PTCacheExtra *extra;
		int i;
		
		link_list(fd, &cache->mem_cache);
		
		pm = cache->mem_cache.first;
		
		for (; pm; pm=pm->next) {
			for (i=0; i<BPHYS_TOT_DATA; i++) {
				pm->data[i] = newdataadr(fd, pm->data[i]);
				
				/* the cache saves non-struct data without DNA */
				if (pm->data[i] && ptcache_data_struct[i][0]=='\0' && (fd->flags & FD_FLAGS_SWITCH_ENDIAN)) {
					int tot = (BKE_ptcache_data_size (i) * pm->totpoint) / sizeof(int); /* data_size returns bytes */
					int *poin = pm->data[i];
					
					BLI_endian_switch_int32_array(poin, tot);
				}
			}
			
			link_list(fd, &pm->extradata);
			
			for (extra=pm->extradata.first; extra; extra=extra->next)
				extra->data = newdataadr(fd, extra->data);
		}
	}
	else
		cache->mem_cache.first = cache->mem_cache.last = NULL;
	
	cache->flag &= ~PTCACHE_SIMULATION_VALID;
	cache->simframe = 0;
	cache->edit = NULL;
	cache->free_edit = NULL;
	cache->cached_frames = NULL;
}

static void direct_link_pointcache_list(FileData *fd, ListBase *ptcaches, PointCache **ocache, int force_disk)
{
	if (ptcaches->first) {
		PointCache *cache= NULL;
		link_list(fd, ptcaches);
		for (cache=ptcaches->first; cache; cache=cache->next) {
			direct_link_pointcache(fd, cache);
			if (force_disk) {
				cache->flag |= PTCACHE_DISK_CACHE;
				cache->step = 1;
			}
		}
		
		*ocache = newdataadr(fd, *ocache);
	}
	else if (*ocache) {
		/* old "single" caches need to be linked too */
		*ocache = newdataadr(fd, *ocache);
		direct_link_pointcache(fd, *ocache);
		if (force_disk) {
			(*ocache)->flag |= PTCACHE_DISK_CACHE;
			(*ocache)->step = 1;
		}
		
		ptcaches->first = ptcaches->last = *ocache;
	}
}

static void lib_link_partdeflect(FileData *fd, ID *id, PartDeflect *pd)
{
	if (pd && pd->tex)
		pd->tex = newlibadr_us(fd, id->lib, pd->tex);
	if (pd && pd->f_source)
		pd->f_source = newlibadr_us(fd, id->lib, pd->f_source);
}

static void lib_link_particlesettings(FileData *fd, Main *main)
{
	ParticleSettings *part;
	ParticleDupliWeight *dw;
	MTex *mtex;
	int a;
	
	for (part = main->particle.first; part; part = part->id.next) {
		if (part->id.flag & LIB_NEED_LINK) {
			if (part->adt) lib_link_animdata(fd, &part->id, part->adt);
			part->ipo = newlibadr_us(fd, part->id.lib, part->ipo); // XXX deprecated - old animation system
			
			part->dup_ob = newlibadr(fd, part->id.lib, part->dup_ob);
			part->dup_group = newlibadr(fd, part->id.lib, part->dup_group);
			part->eff_group = newlibadr(fd, part->id.lib, part->eff_group);
			part->bb_ob = newlibadr(fd, part->id.lib, part->bb_ob);
			
			lib_link_partdeflect(fd, &part->id, part->pd);
			lib_link_partdeflect(fd, &part->id, part->pd2);
			
			if (part->effector_weights)
				part->effector_weights->group = newlibadr(fd, part->id.lib, part->effector_weights->group);
			
			if (part->dupliweights.first && part->dup_group) {
				int index_ok = 0;
				/* check for old files without indices (all indexes 0) */
				if (part->dupliweights.first == part->dupliweights.last) {
					/* special case for only one object in the group */
					index_ok = 1;
				}
				else {
					for (dw = part->dupliweights.first; dw; dw = dw->next) {
						if (dw->index > 0) {
							index_ok = 1;
							break;
						}
					}
				}

				if (index_ok) {
					/* if we have indexes, let's use them */
					for (dw = part->dupliweights.first; dw; dw = dw->next) {
						GroupObject *go = (GroupObject *)BLI_findlink(&part->dup_group->gobject, dw->index);
						dw->ob = go ? newlibadr(fd, part->id.lib, dw->ob) : NULL;
					}
				}
				else {
					/* otherwise try to get objects from own library (won't work on library linked groups) */
					for (dw = part->dupliweights.first; dw; dw = dw->next) {
						dw->ob = newlibadr(fd, part->id.lib, dw->ob);
					}
				}
			}
			else {
				part->dupliweights.first = part->dupliweights.last = NULL;
			}
			
			if (part->boids) {
				BoidState *state = part->boids->states.first;
				BoidRule *rule;
				for (; state; state=state->next) {
					rule = state->rules.first;
				for (; rule; rule=rule->next)
					switch (rule->type) {
						case eBoidRuleType_Goal:
						case eBoidRuleType_Avoid:
						{
							BoidRuleGoalAvoid *brga = (BoidRuleGoalAvoid*)rule;
							brga->ob = newlibadr(fd, part->id.lib, brga->ob);
							break;
						}
						case eBoidRuleType_FollowLeader:
						{
							BoidRuleFollowLeader *brfl = (BoidRuleFollowLeader*)rule;
							brfl->ob = newlibadr(fd, part->id.lib, brfl->ob);
							break;
						}
					}
				}
			}
			
			for (a = 0; a < MAX_MTEX; a++) {
				mtex= part->mtex[a];
				if (mtex) {
					mtex->tex = newlibadr_us(fd, part->id.lib, mtex->tex);
					mtex->object = newlibadr(fd, part->id.lib, mtex->object);
				}
			}
			
			part->id.flag -= LIB_NEED_LINK;
		}
	}
}

static void direct_link_partdeflect(PartDeflect *pd)
{
	if (pd) pd->rng = NULL;
}

static void direct_link_particlesettings(FileData *fd, ParticleSettings *part)
{
	int a;
	
	part->adt = newdataadr(fd, part->adt);
	part->pd = newdataadr(fd, part->pd);
	part->pd2 = newdataadr(fd, part->pd2);

	direct_link_animdata(fd, part->adt);
	direct_link_partdeflect(part->pd);
	direct_link_partdeflect(part->pd2);

	part->effector_weights = newdataadr(fd, part->effector_weights);
	if (!part->effector_weights)
		part->effector_weights = BKE_add_effector_weights(part->eff_group);

	link_list(fd, &part->dupliweights);

	part->boids = newdataadr(fd, part->boids);
	part->fluid = newdataadr(fd, part->fluid);

	if (part->boids) {
		BoidState *state;
		link_list(fd, &part->boids->states);
		
		for (state=part->boids->states.first; state; state=state->next) {
			link_list(fd, &state->rules);
			link_list(fd, &state->conditions);
			link_list(fd, &state->actions);
		}
	}
	for (a = 0; a < MAX_MTEX; a++) {
		part->mtex[a] = newdataadr(fd, part->mtex[a]);
	}
}

static void lib_link_particlesystems(FileData *fd, Object *ob, ID *id, ListBase *particles)
{
	ParticleSystem *psys, *psysnext;

	for (psys=particles->first; psys; psys=psysnext) {
		psysnext = psys->next;
		
		psys->part = newlibadr_us(fd, id->lib, psys->part);
		if (psys->part) {
			ParticleTarget *pt = psys->targets.first;
			
			for (; pt; pt=pt->next)
				pt->ob=newlibadr(fd, id->lib, pt->ob);
			
			psys->parent = newlibadr_us(fd, id->lib, psys->parent);
			psys->target_ob = newlibadr(fd, id->lib, psys->target_ob);
			
			if (psys->clmd) {
				/* XXX - from reading existing code this seems correct but intended usage of
				 * pointcache should /w cloth should be added in 'ParticleSystem' - campbell */
				psys->clmd->point_cache = psys->pointcache;
				psys->clmd->ptcaches.first = psys->clmd->ptcaches.last= NULL;
				psys->clmd->coll_parms->group = newlibadr(fd, id->lib, psys->clmd->coll_parms->group);
			}
		}
		else {
			/* particle modifier must be removed before particle system */
			ParticleSystemModifierData *psmd = psys_get_modifier(ob, psys);
			BLI_remlink(&ob->modifiers, psmd);
			modifier_free((ModifierData *)psmd);
			
			BLI_remlink(particles, psys);
			MEM_freeN(psys);
		}
	}
}
static void direct_link_particlesystems(FileData *fd, ListBase *particles)
{
	ParticleSystem *psys;
	ParticleData *pa;
	int a;
	
	for (psys=particles->first; psys; psys=psys->next) {
		psys->particles=newdataadr(fd, psys->particles);
		
		if (psys->particles && psys->particles->hair) {
			for (a=0, pa=psys->particles; a<psys->totpart; a++, pa++)
				pa->hair=newdataadr(fd, pa->hair);
		}
		
		if (psys->particles && psys->particles->keys) {
			for (a=0, pa=psys->particles; a<psys->totpart; a++, pa++) {
				pa->keys= NULL;
				pa->totkey= 0;
			}
			
			psys->flag &= ~PSYS_KEYED;
		}
		
		if (psys->particles && psys->particles->boid) {
			pa = psys->particles;
			pa->boid = newdataadr(fd, pa->boid);
			for (a=1, pa++; a<psys->totpart; a++, pa++)
				pa->boid = (pa-1)->boid + 1;
		}
		else if (psys->particles) {
			for (a=0, pa=psys->particles; a<psys->totpart; a++, pa++)
				pa->boid = NULL;
		}
		
		psys->fluid_springs = newdataadr(fd, psys->fluid_springs);
		
		psys->child = newdataadr(fd, psys->child);
		psys->effectors = NULL;
		
		link_list(fd, &psys->targets);
		
		psys->edit = NULL;
		psys->free_edit = NULL;
		psys->pathcache = NULL;
		psys->childcache = NULL;
		psys->pathcachebufs.first = psys->pathcachebufs.last = NULL;
		psys->childcachebufs.first = psys->childcachebufs.last = NULL;
		psys->frand = NULL;
		psys->pdd = NULL;
		psys->renderdata = NULL;
		
		direct_link_pointcache_list(fd, &psys->ptcaches, &psys->pointcache, 0);
		
		if (psys->clmd) {
			psys->clmd = newdataadr(fd, psys->clmd);
			psys->clmd->clothObject = NULL;
			
			psys->clmd->sim_parms= newdataadr(fd, psys->clmd->sim_parms);
			psys->clmd->coll_parms= newdataadr(fd, psys->clmd->coll_parms);
			
			if (psys->clmd->sim_parms) {
				psys->clmd->sim_parms->effector_weights = NULL;
				if (psys->clmd->sim_parms->presets > 10)
					psys->clmd->sim_parms->presets = 0;
			}
			
			psys->hair_in_dm = psys->hair_out_dm = NULL;
			
			psys->clmd->point_cache = psys->pointcache;
		}
		
		psys->tree = NULL;
		psys->bvhtree = NULL;
	}
	return;
}

/* ************ READ MESH ***************** */

static void lib_link_mtface(FileData *fd, Mesh *me, MTFace *mtface, int totface)
{
	MTFace *tf= mtface;
	int i;
	
	/* Add pseudo-references (not fake users!) to images used by texface. A
	 * little bogus; it would be better if each mesh consistently added one ref
	 * to each image it used. - z0r */
	for (i = 0; i < totface; i++, tf++) {
		tf->tpage= newlibadr(fd, me->id.lib, tf->tpage);
		if (tf->tpage && tf->tpage->id.us==0)
			tf->tpage->id.us= 1;
	}
}

static void lib_link_customdata_mtface(FileData *fd, Mesh *me, CustomData *fdata, int totface)
{
	int i;
	for (i = 0; i < fdata->totlayer; i++) {
		CustomDataLayer *layer = &fdata->layers[i];
		
		if (layer->type == CD_MTFACE)
			lib_link_mtface(fd, me, layer->data, totface);
	}

}

static void lib_link_customdata_mtpoly(FileData *fd, Mesh *me, CustomData *pdata, int totface)
{
	int i;

	for (i=0; i < pdata->totlayer; i++) {
		CustomDataLayer *layer = &pdata->layers[i];
		
		if (layer->type == CD_MTEXPOLY) {
			MTexPoly *tf= layer->data;
			int j;
			
			for (j = 0; j < totface; j++, tf++) {
				tf->tpage = newlibadr(fd, me->id.lib, tf->tpage);
				if (tf->tpage && tf->tpage->id.us == 0) {
					tf->tpage->id.us = 1;
				}
			}
		}
	}
}

static void lib_link_mesh(FileData *fd, Main *main)
{
	Mesh *me;
	
	for (me = main->mesh.first; me; me = me->id.next) {
		if (me->id.flag & LIB_NEED_LINK) {
			int i;
			
			/* Link ID Properties -- and copy this comment EXACTLY for easy finding
			 * of library blocks that implement this.*/
			if (me->id.properties) IDP_LibLinkProperty(me->id.properties, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
			if (me->adt) lib_link_animdata(fd, &me->id, me->adt);
			
			/* this check added for python created meshes */
			if (me->mat) {
				for (i = 0; i < me->totcol; i++) {
					me->mat[i] = newlibadr_us(fd, me->id.lib, me->mat[i]);
				}
			}
			else {
				me->totcol = 0;
			}

			me->ipo = newlibadr_us(fd, me->id.lib, me->ipo); // XXX: deprecated: old anim sys
			me->key = newlibadr_us(fd, me->id.lib, me->key);
			me->texcomesh = newlibadr_us(fd, me->id.lib, me->texcomesh);
			
			lib_link_customdata_mtface(fd, me, &me->fdata, me->totface);
			lib_link_customdata_mtpoly(fd, me, &me->pdata, me->totpoly);
			if (me->mr && me->mr->levels.first)
				lib_link_customdata_mtface(fd, me, &me->mr->fdata,
							   ((MultiresLevel*)me->mr->levels.first)->totface);
		}
	}

	/* convert texface options to material */
	convert_tface_mt(fd, main);

	for (me = main->mesh.first; me; me = me->id.next) {
		if (me->id.flag & LIB_NEED_LINK) {
			/*check if we need to convert mfaces to mpolys*/
			if (me->totface && !me->totpoly) {
				/* temporarily switch main so that reading from
				 * external CustomData works */
				Main *gmain = G.main;
				G.main = main;
				
				BKE_mesh_do_versions_convert_mfaces_to_mpolys(me);
				
				G.main = gmain;
			}

			/*
			 * Re-tessellate, even if the polys were just created from tessfaces, this
			 * is important because it:
			 *  - fill the CD_ORIGINDEX layer
			 *  - gives consistency of tessface between loading from a file and
			 *    converting an edited BMesh back into a mesh (i.e. it replaces
			 *    quad tessfaces in a loaded mesh immediately, instead of lazily
			 *    waiting until edit mode has been entered/exited, making it easier
			 *    to recognize problems that would otherwise only show up after edits).
			 */
#ifdef USE_TESSFACE_DEFAULT
			BKE_mesh_tessface_calc(me);
#else
			BKE_mesh_tessface_clear(me);
#endif

			me->id.flag -= LIB_NEED_LINK;
		}
	}
}

static void direct_link_dverts(FileData *fd, int count, MDeformVert *mdverts)
{
	int i;
	
	if (mdverts == NULL) {
		return;
	}
	
	for (i = count; i > 0; i--, mdverts++) {
		/*convert to vgroup allocation system*/
		MDeformWeight *dw;
		if (mdverts->dw && (dw = newdataadr(fd, mdverts->dw))) {
			const ssize_t dw_len = mdverts->totweight * sizeof(MDeformWeight);
			void *dw_tmp = MEM_mallocN(dw_len, "direct_link_dverts");
			memcpy(dw_tmp, dw, dw_len);
			mdverts->dw = dw_tmp;
			MEM_freeN(dw);
		}
		else {
			mdverts->dw = NULL;
			mdverts->totweight = 0;
		}
	}
}

static void direct_link_mdisps(FileData *fd, int count, MDisps *mdisps, int external)
{
	if (mdisps) {
		int i;
		
		for (i = 0; i < count; ++i) {
			mdisps[i].disps = newdataadr(fd, mdisps[i].disps);
			mdisps[i].hidden = newdataadr(fd, mdisps[i].hidden);
			
			if (mdisps[i].totdisp && !mdisps[i].level) {
				/* this calculation is only correct for loop mdisps;
				 * if loading pre-BMesh face mdisps this will be
				 * overwritten with the correct value in
				 * bm_corners_to_loops() */
				float gridsize = sqrtf(mdisps[i].totdisp);
				mdisps[i].level = (int)(logf(gridsize - 1.0f) / (float)M_LN2) + 1;
			}
			
			if ((fd->flags & FD_FLAGS_SWITCH_ENDIAN) && (mdisps[i].disps)) {
				/* DNA_struct_switch_endian doesn't do endian swap for (*disps)[] */
				/* this does swap for data written at write_mdisps() - readfile.c */
				BLI_endian_switch_float_array(*mdisps[i].disps, mdisps[i].totdisp * 3);
			}
			if (!external && !mdisps[i].disps)
				mdisps[i].totdisp = 0;
		}
	}
}

static void direct_link_grid_paint_mask(FileData *fd, int count, GridPaintMask *grid_paint_mask)
{
	if (grid_paint_mask) {
		int i;
		
		for (i = 0; i < count; ++i) {
			GridPaintMask *gpm = &grid_paint_mask[i];
			if (gpm->data)
				gpm->data = newdataadr(fd, gpm->data);
		}
	}
}

/*this isn't really a public api function, so prototyped here*/
static void direct_link_customdata(FileData *fd, CustomData *data, int count)
{
	int i = 0;
	
	data->layers = newdataadr(fd, data->layers);
	
	/* annoying workaround for bug [#31079] loading legacy files with
	 * no polygons _but_ have stale customdata */
	if (UNLIKELY(count == 0 && data->layers == NULL && data->totlayer != 0)) {
		CustomData_reset(data);
		return;
	}
	
	data->external = newdataadr(fd, data->external);
	
	while (i < data->totlayer) {
		CustomDataLayer *layer = &data->layers[i];
		
		if (layer->flag & CD_FLAG_EXTERNAL)
			layer->flag &= ~CD_FLAG_IN_MEMORY;
		
		if (CustomData_verify_versions(data, i)) {
			layer->data = newdataadr(fd, layer->data);
			if (layer->type == CD_MDISPS)
				direct_link_mdisps(fd, count, layer->data, layer->flag & CD_FLAG_EXTERNAL);
			else if (layer->type == CD_GRID_PAINT_MASK)
				direct_link_grid_paint_mask(fd, count, layer->data);
			i++;
		}
	}
	
	CustomData_update_typemap(data);
}

static void direct_link_mesh(FileData *fd, Mesh *mesh)
{
	mesh->mat= newdataadr(fd, mesh->mat);
	test_pointer_array(fd, (void **)&mesh->mat);
	
	mesh->mvert = newdataadr(fd, mesh->mvert);
	mesh->medge = newdataadr(fd, mesh->medge);
	mesh->mface = newdataadr(fd, mesh->mface);
	mesh->mloop = newdataadr(fd, mesh->mloop);
	mesh->mpoly = newdataadr(fd, mesh->mpoly);
	mesh->tface = newdataadr(fd, mesh->tface);
	mesh->mtface = newdataadr(fd, mesh->mtface);
	mesh->mcol = newdataadr(fd, mesh->mcol);
	mesh->dvert = newdataadr(fd, mesh->dvert);
	mesh->mloopcol = newdataadr(fd, mesh->mloopcol);
	mesh->mloopuv = newdataadr(fd, mesh->mloopuv);
	mesh->mtpoly = newdataadr(fd, mesh->mtpoly);
	mesh->mselect = newdataadr(fd, mesh->mselect);
	
	/* animdata */
	mesh->adt = newdataadr(fd, mesh->adt);
	direct_link_animdata(fd, mesh->adt);
	
	/* normally direct_link_dverts should be called in direct_link_customdata,
	 * but for backwards compat in do_versions to work we do it here */
	direct_link_dverts(fd, mesh->totvert, mesh->dvert);
	
	direct_link_customdata(fd, &mesh->vdata, mesh->totvert);
	direct_link_customdata(fd, &mesh->edata, mesh->totedge);
	direct_link_customdata(fd, &mesh->fdata, mesh->totface);
	direct_link_customdata(fd, &mesh->ldata, mesh->totloop);
	direct_link_customdata(fd, &mesh->pdata, mesh->totpoly);
	
	mesh->bb = NULL;
	mesh->edit_btmesh = NULL;
	
	/* happens with old files */
	if (mesh->mselect == NULL) {
		mesh->totselect = 0;
	}

	/* Multires data */
	mesh->mr= newdataadr(fd, mesh->mr);
	if (mesh->mr) {
		MultiresLevel *lvl;
		
		link_list(fd, &mesh->mr->levels);
		lvl = mesh->mr->levels.first;
		
		direct_link_customdata(fd, &mesh->mr->vdata, lvl->totvert);
		direct_link_dverts(fd, lvl->totvert, CustomData_get(&mesh->mr->vdata, 0, CD_MDEFORMVERT));
		direct_link_customdata(fd, &mesh->mr->fdata, lvl->totface);
		
		mesh->mr->edge_flags = newdataadr(fd, mesh->mr->edge_flags);
		mesh->mr->edge_creases = newdataadr(fd, mesh->mr->edge_creases);
		
		mesh->mr->verts = newdataadr(fd, mesh->mr->verts);
		
		/* If mesh has the same number of vertices as the
		 * highest multires level, load the current mesh verts
		 * into multires and discard the old data. Needed
		 * because some saved files either do not have a verts
		 * array, or the verts array contains out-of-date
		 * data. */
		if (mesh->totvert == ((MultiresLevel*)mesh->mr->levels.last)->totvert) {
			if (mesh->mr->verts)
				MEM_freeN(mesh->mr->verts);
			mesh->mr->verts = MEM_dupallocN(mesh->mvert);
		}
			
		for (; lvl; lvl = lvl->next) {
			lvl->verts = newdataadr(fd, lvl->verts);
			lvl->faces = newdataadr(fd, lvl->faces);
			lvl->edges = newdataadr(fd, lvl->edges);
			lvl->colfaces = newdataadr(fd, lvl->colfaces);
		}
	}

	/* if multires is present but has no valid vertex data,
	 * there's no way to recover it; silently remove multires */
	if (mesh->mr && !mesh->mr->verts) {
		multires_free(mesh->mr);
		mesh->mr = NULL;
	}
	
	if ((fd->flags & FD_FLAGS_SWITCH_ENDIAN) && mesh->tface) {
		TFace *tf = mesh->tface;
		int i;
		
		for (i = 0; i < mesh->totface; i++, tf++) {
			BLI_endian_switch_uint32_array(tf->col, 4);
		}
	}
}

/* ************ READ LATTICE ***************** */

static void lib_link_latt(FileData *fd, Main *main)
{
	Lattice *lt;
	
	for (lt = main->latt.first; lt; lt = lt->id.next) {
		if (lt->id.flag & LIB_NEED_LINK) {
			if (lt->adt) lib_link_animdata(fd, &lt->id, lt->adt);
			
			lt->ipo = newlibadr_us(fd, lt->id.lib, lt->ipo); // XXX deprecated - old animation system
			lt->key = newlibadr_us(fd, lt->id.lib, lt->key);
			
			lt->id.flag -= LIB_NEED_LINK;
		}
	}
}

static void direct_link_latt(FileData *fd, Lattice *lt)
{
	lt->def = newdataadr(fd, lt->def);
	
	lt->dvert = newdataadr(fd, lt->dvert);
	direct_link_dverts(fd, lt->pntsu*lt->pntsv*lt->pntsw, lt->dvert);
	
	lt->editlatt = NULL;
	
	lt->adt = newdataadr(fd, lt->adt);
	direct_link_animdata(fd, lt->adt);
}


/* ************ READ OBJECT ***************** */

static void lib_link_modifiers__linkModifiers(void *userData, Object *ob,
                                              ID **idpoin)
{
	FileData *fd = userData;

	*idpoin = newlibadr(fd, ob->id.lib, *idpoin);
	/* hardcoded bad exception; non-object modifier data gets user count (texture, displace) */
	if (*idpoin && GS((*idpoin)->name)!=ID_OB)
		(*idpoin)->us++;
}
static void lib_link_modifiers(FileData *fd, Object *ob)
{
	modifiers_foreachIDLink(ob, lib_link_modifiers__linkModifiers, fd);
}

static void lib_link_object(FileData *fd, Main *main)
{
	Object *ob;
	PartEff *paf;
	bSensor *sens;
	bController *cont;
	bActuator *act;
	void *poin;
	int warn=0, a;
	
	for (ob = main->object.first; ob; ob = ob->id.next) {
		if (ob->id.flag & LIB_NEED_LINK) {
			if (ob->id.properties) IDP_LibLinkProperty(ob->id.properties, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
			if (ob->adt) lib_link_animdata(fd, &ob->id, ob->adt);
			
// XXX deprecated - old animation system <<<
			ob->ipo = newlibadr_us(fd, ob->id.lib, ob->ipo);
			ob->action = newlibadr_us(fd, ob->id.lib, ob->action);
// >>> XXX deprecated - old animation system

			ob->parent = newlibadr(fd, ob->id.lib, ob->parent);
			ob->track = newlibadr(fd, ob->id.lib, ob->track);
			ob->poselib = newlibadr_us(fd, ob->id.lib, ob->poselib);
			ob->dup_group = newlibadr_us(fd, ob->id.lib, ob->dup_group);
			
			ob->proxy = newlibadr_us(fd, ob->id.lib, ob->proxy);
			if (ob->proxy) {
				/* paranoia check, actually a proxy_from pointer should never be written... */
				if (ob->proxy->id.lib == NULL) {
					ob->proxy->proxy_from = NULL;
					ob->proxy = NULL;
					
					if (ob->id.lib)
						printf("Proxy lost from  object %s lib %s\n", ob->id.name + 2, ob->id.lib->name);
					else
						printf("Proxy lost from  object %s lib <NONE>\n", ob->id.name + 2);
				}
				else {
					/* this triggers object_update to always use a copy */
					ob->proxy->proxy_from = ob;
				}
			}
			ob->proxy_group = newlibadr(fd, ob->id.lib, ob->proxy_group);
			
			poin = ob->data;
			ob->data = newlibadr_us(fd, ob->id.lib, ob->data);
			
			if (ob->data==NULL && poin!=NULL) {
				if (ob->id.lib)
					printf("Can't find obdata of %s lib %s\n", ob->id.name + 2, ob->id.lib->name);
				else
					printf("Object %s lost data.\n", ob->id.name + 2);
				
				ob->type = OB_EMPTY;
				warn = 1;
				
				if (ob->pose) {
					/* we can't call #BKE_pose_free() here because of library linking
					 * freeing will recurse down into every pose constraints ID pointers
					 * which are not always valid, so for now free directly and suffer
					 * some leaked memory rather then crashing immediately
					 * while bad this _is_ an exceptional case - campbell */
#if 0
					BKE_pose_free(ob->pose);
#else
					MEM_freeN(ob->pose);
#endif
					ob->pose= NULL;
					ob->mode &= ~OB_MODE_POSE;
				}
			}
			for (a=0; a < ob->totcol; a++) 
				ob->mat[a] = newlibadr_us(fd, ob->id.lib, ob->mat[a]);
			
			/* When the object is local and the data is library its possible
			 * the material list size gets out of sync. [#22663] */
			if (ob->data && ob->id.lib != ((ID *)ob->data)->lib) {
				short *totcol_data = give_totcolp(ob);
				/* Only expand so as not to loose any object materials that might be set. */
				if (totcol_data && (*totcol_data > ob->totcol)) {
					/* printf("'%s' %d -> %d\n", ob->id.name, ob->totcol, *totcol_data); */
					resize_object_material(ob, *totcol_data);
				}
			}
			
			ob->gpd = newlibadr_us(fd, ob->id.lib, ob->gpd);
			ob->duplilist = NULL;
			
			ob->id.flag -= LIB_NEED_LINK;
			/* if id.us==0 a new base will be created later on */
			
			/* WARNING! Also check expand_object(), should reflect the stuff below. */
			lib_link_pose(fd, main, ob, ob->pose);
			lib_link_constraints(fd, &ob->id, &ob->constraints);
			
// XXX deprecated - old animation system <<<
			lib_link_constraint_channels(fd, &ob->id, &ob->constraintChannels);
			lib_link_nlastrips(fd, &ob->id, &ob->nlastrips);
// >>> XXX deprecated - old animation system
			
			for (paf = ob->effect.first; paf; paf = paf->next) {
				if (paf->type == EFF_PARTICLE) {
					paf->group = newlibadr_us(fd, ob->id.lib, paf->group);
				}
			}
			
			for (sens = ob->sensors.first; sens; sens = sens->next) {
				for (a = 0; a < sens->totlinks; a++)
					sens->links[a] = newglobadr(fd, sens->links[a]);
				
				if (sens->type == SENS_TOUCH) {
					bTouchSensor *ts = sens->data;
					ts->ma = newlibadr(fd, ob->id.lib, ts->ma);
				}
				else if (sens->type == SENS_MESSAGE) {
					bMessageSensor *ms = sens->data;
					ms->fromObject =
						newlibadr(fd, ob->id.lib, ms->fromObject);
				}
			}
			
			for (cont = ob->controllers.first; cont; cont = cont->next) {
				for (a=0; a < cont->totlinks; a++)
					cont->links[a] = newglobadr(fd, cont->links[a]);
				
				if (cont->type == CONT_PYTHON) {
					bPythonCont *pc = cont->data;
					pc->text = newlibadr(fd, ob->id.lib, pc->text);
				}
				cont->slinks = NULL;
				cont->totslinks = 0;
			}
			
			for (act = ob->actuators.first; act; act = act->next) {
				if (act->type == ACT_SOUND) {
					bSoundActuator *sa = act->data;
					sa->sound= newlibadr_us(fd, ob->id.lib, sa->sound);
				}
				else if (act->type == ACT_GAME) {
					/* bGameActuator *ga= act->data; */
				}
				else if (act->type == ACT_CAMERA) {
					bCameraActuator *ca = act->data;
					ca->ob= newlibadr(fd, ob->id.lib, ca->ob);
				}
					/* leave this one, it's obsolete but necessary to read for conversion */
				else if (act->type == ACT_ADD_OBJECT) {
					bAddObjectActuator *eoa = act->data;
					if (eoa) eoa->ob= newlibadr(fd, ob->id.lib, eoa->ob);
				}
				else if (act->type == ACT_OBJECT) {
					bObjectActuator *oa = act->data;
					if (oa == NULL) {
						init_actuator(act);
					}
					else {
						oa->reference = newlibadr(fd, ob->id.lib, oa->reference);
					}
				}
				else if (act->type == ACT_EDIT_OBJECT) {
					bEditObjectActuator *eoa = act->data;
					if (eoa == NULL) {
						init_actuator(act);
					}
					else {
						eoa->ob= newlibadr(fd, ob->id.lib, eoa->ob);
						eoa->me= newlibadr(fd, ob->id.lib, eoa->me);
					}
				}
				else if (act->type == ACT_SCENE) {
					bSceneActuator *sa = act->data;
					sa->camera= newlibadr(fd, ob->id.lib, sa->camera);
					sa->scene= newlibadr(fd, ob->id.lib, sa->scene);
				}
				else if (act->type == ACT_ACTION) {
					bActionActuator *aa = act->data;
					aa->act= newlibadr(fd, ob->id.lib, aa->act);
				}
				else if (act->type == ACT_SHAPEACTION) {
					bActionActuator *aa = act->data;
					aa->act= newlibadr(fd, ob->id.lib, aa->act);
				}
				else if (act->type == ACT_PROPERTY) {
					bPropertyActuator *pa = act->data;
					pa->ob= newlibadr(fd, ob->id.lib, pa->ob);
				}
				else if (act->type == ACT_MESSAGE) {
					bMessageActuator *ma = act->data;
					ma->toObject= newlibadr(fd, ob->id.lib, ma->toObject);
				}
				else if (act->type == ACT_2DFILTER) {
					bTwoDFilterActuator *_2dfa = act->data; 
					_2dfa->text= newlibadr(fd, ob->id.lib, _2dfa->text);
				}
				else if (act->type == ACT_PARENT) {
					bParentActuator *parenta = act->data; 
					parenta->ob = newlibadr(fd, ob->id.lib, parenta->ob);
				}
				else if (act->type == ACT_STATE) {
					/* bStateActuator *statea = act->data; */
				}
				else if (act->type == ACT_ARMATURE) {
					bArmatureActuator *arma= act->data;
					arma->target= newlibadr(fd, ob->id.lib, arma->target);
					arma->subtarget= newlibadr(fd, ob->id.lib, arma->subtarget);
				}
				else if (act->type == ACT_STEERING) {
					bSteeringActuator *steeringa = act->data; 
					steeringa->target = newlibadr(fd, ob->id.lib, steeringa->target);
					steeringa->navmesh = newlibadr(fd, ob->id.lib, steeringa->navmesh);
				}
			}
			
			{
				FluidsimModifierData *fluidmd = (FluidsimModifierData *)modifiers_findByType(ob, eModifierType_Fluidsim);
				
				if (fluidmd && fluidmd->fss)
					fluidmd->fss->ipo = newlibadr_us(fd, ob->id.lib, fluidmd->fss->ipo);
			}
			
			{
				SmokeModifierData *smd = (SmokeModifierData *)modifiers_findByType(ob, eModifierType_Smoke);
				
				if (smd && (smd->type == MOD_SMOKE_TYPE_DOMAIN) && smd->domain) {
					smd->domain->flags |= MOD_SMOKE_FILE_LOAD; /* flag for refreshing the simulation after loading */
				}
			}
			
			/* texture field */
			if (ob->pd)
				lib_link_partdeflect(fd, &ob->id, ob->pd);
			
			if (ob->soft)
				ob->soft->effector_weights->group = newlibadr(fd, ob->id.lib, ob->soft->effector_weights->group);
			
			lib_link_particlesystems(fd, ob, &ob->id, &ob->particlesystem);
			lib_link_modifiers(fd, ob);

			if (ob->rigidbody_constraint) {
				ob->rigidbody_constraint->ob1 = newlibadr(fd, ob->id.lib, ob->rigidbody_constraint->ob1);
				ob->rigidbody_constraint->ob2 = newlibadr(fd, ob->id.lib, ob->rigidbody_constraint->ob2);
			}
		}
	}
	
	if (warn) {
		BKE_report(fd->reports, RPT_WARNING, "Warning in console");
	}
}


static void direct_link_pose(FileData *fd, bPose *pose)
{
	bPoseChannel *pchan;

	if (!pose)
		return;

	link_list(fd, &pose->chanbase);
	link_list(fd, &pose->agroups);

	pose->chanhash = NULL;

	for (pchan = pose->chanbase.first; pchan; pchan=pchan->next) {
		pchan->bone = NULL;
		pchan->parent = newdataadr(fd, pchan->parent);
		pchan->child = newdataadr(fd, pchan->child);
		pchan->custom_tx = newdataadr(fd, pchan->custom_tx);
		
		direct_link_constraints(fd, &pchan->constraints);
		
		pchan->prop = newdataadr(fd, pchan->prop);
		if (pchan->prop)
			IDP_DirectLinkProperty(pchan->prop, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
		
		pchan->mpath = newdataadr(fd, pchan->mpath);
		if (pchan->mpath)
			direct_link_motionpath(fd, pchan->mpath);
		
		pchan->iktree.first = pchan->iktree.last = NULL;
		pchan->siktree.first = pchan->siktree.last = NULL;
		
		/* in case this value changes in future, clamp else we get undefined behavior */
		CLAMP(pchan->rotmode, ROT_MODE_MIN, ROT_MODE_MAX);
	}
	pose->ikdata = NULL;
	if (pose->ikparam != NULL) {
		pose->ikparam = newdataadr(fd, pose->ikparam);
	}
}

static void direct_link_modifiers(FileData *fd, ListBase *lb)
{
	ModifierData *md;
	
	link_list(fd, lb);
	
	for (md=lb->first; md; md=md->next) {
		md->error = NULL;
		md->scene = NULL;
		
		/* if modifiers disappear, or for upward compatibility */
		if (NULL == modifierType_getInfo(md->type))
			md->type = eModifierType_None;
			
		if (md->type == eModifierType_Subsurf) {
			SubsurfModifierData *smd = (SubsurfModifierData *)md;
			
			smd->emCache = smd->mCache = NULL;
		}
		else if (md->type == eModifierType_Armature) {
			ArmatureModifierData *amd = (ArmatureModifierData *)md;
			
			amd->prevCos = NULL;
		}
		else if (md->type == eModifierType_Cloth) {
			ClothModifierData *clmd = (ClothModifierData *)md;
			
			clmd->clothObject = NULL;
			
			clmd->sim_parms= newdataadr(fd, clmd->sim_parms);
			clmd->coll_parms= newdataadr(fd, clmd->coll_parms);
			
			direct_link_pointcache_list(fd, &clmd->ptcaches, &clmd->point_cache, 0);
			
			if (clmd->sim_parms) {
				if (clmd->sim_parms->presets > 10)
					clmd->sim_parms->presets = 0;
				
				clmd->sim_parms->reset = 0;
				
				clmd->sim_parms->effector_weights = newdataadr(fd, clmd->sim_parms->effector_weights);
				
				if (!clmd->sim_parms->effector_weights) {
					clmd->sim_parms->effector_weights = BKE_add_effector_weights(NULL);
				}
			}
		}
		else if (md->type == eModifierType_Fluidsim) {
			FluidsimModifierData *fluidmd = (FluidsimModifierData *)md;
			
			fluidmd->fss = newdataadr(fd, fluidmd->fss);
			if (fluidmd->fss) {
				fluidmd->fss->fmd = fluidmd;
				fluidmd->fss->meshVelocities = NULL;
			}
		}
		else if (md->type == eModifierType_Smoke) {
			SmokeModifierData *smd = (SmokeModifierData *)md;
			
			if (smd->type == MOD_SMOKE_TYPE_DOMAIN) {
				smd->flow = NULL;
				smd->coll = NULL;
				smd->domain = newdataadr(fd, smd->domain);
				smd->domain->smd = smd;
				
				smd->domain->fluid = NULL;
				smd->domain->fluid_mutex = BLI_rw_mutex_alloc();
				smd->domain->wt = NULL;
				smd->domain->shadow = NULL;
				smd->domain->tex = NULL;
				smd->domain->tex_shadow = NULL;
				smd->domain->tex_wt = NULL;
				
				smd->domain->effector_weights = newdataadr(fd, smd->domain->effector_weights);
				if (!smd->domain->effector_weights)
					smd->domain->effector_weights = BKE_add_effector_weights(NULL);
				
				direct_link_pointcache_list(fd, &(smd->domain->ptcaches[0]), &(smd->domain->point_cache[0]), 1);
				
				/* Smoke uses only one cache from now on, so store pointer convert */
				if (smd->domain->ptcaches[1].first || smd->domain->point_cache[1]) {
					if (smd->domain->point_cache[1]) {
						PointCache *cache = newdataadr(fd, smd->domain->point_cache[1]);
						if (cache->flag & PTCACHE_FAKE_SMOKE) {
							/* Smoke was already saved in "new format" and this cache is a fake one. */
						}
						else {
							printf("High resolution smoke cache not available due to pointcache update. Please reset the simulation.\n");
						}
						BKE_ptcache_free(cache);
					}
					smd->domain->ptcaches[1].first = NULL;
					smd->domain->ptcaches[1].last = NULL;
					smd->domain->point_cache[1] = NULL;
				}
			}
			else if (smd->type == MOD_SMOKE_TYPE_FLOW) {
				smd->domain = NULL;
				smd->coll = NULL;
				smd->flow = newdataadr(fd, smd->flow);
				smd->flow->smd = smd;
				smd->flow->dm = NULL;
				smd->flow->verts_old = NULL;
				smd->flow->numverts = 0;
				smd->flow->psys = newdataadr(fd, smd->flow->psys);
			}
			else if (smd->type == MOD_SMOKE_TYPE_COLL) {
				smd->flow = NULL;
				smd->domain = NULL;
				smd->coll = newdataadr(fd, smd->coll);
				if (smd->coll) {
					smd->coll->smd = smd;
					smd->coll->verts_old = NULL;
					smd->coll->numverts = 0;
					smd->coll->dm = NULL;
				}
				else {
					smd->type = 0;
					smd->flow = NULL;
					smd->domain = NULL;
					smd->coll = NULL;
				}
			}
		}
		else if (md->type == eModifierType_DynamicPaint) {
			DynamicPaintModifierData *pmd = (DynamicPaintModifierData *)md;
			
			if (pmd->canvas) {
				pmd->canvas = newdataadr(fd, pmd->canvas);
				pmd->canvas->pmd = pmd;
				pmd->canvas->dm = NULL;
				pmd->canvas->flags &= ~MOD_DPAINT_BAKING; /* just in case */
				
				if (pmd->canvas->surfaces.first) {
					DynamicPaintSurface *surface;
					link_list(fd, &pmd->canvas->surfaces);
					
					for (surface=pmd->canvas->surfaces.first; surface; surface=surface->next) {
						surface->canvas = pmd->canvas;
						surface->data = NULL;
						direct_link_pointcache_list(fd, &(surface->ptcaches), &(surface->pointcache), 1);
						
						if (!(surface->effector_weights = newdataadr(fd, surface->effector_weights)))
							surface->effector_weights = BKE_add_effector_weights(NULL);
					}
				}
			}
			if (pmd->brush) {
				pmd->brush = newdataadr(fd, pmd->brush);
				pmd->brush->pmd = pmd;
				pmd->brush->psys = newdataadr(fd, pmd->brush->psys);
				pmd->brush->paint_ramp = newdataadr(fd, pmd->brush->paint_ramp);
				pmd->brush->vel_ramp = newdataadr(fd, pmd->brush->vel_ramp);
				pmd->brush->dm = NULL;
			}
		}
		else if (md->type == eModifierType_Collision) {
			CollisionModifierData *collmd = (CollisionModifierData *)md;
#if 0
			// TODO: CollisionModifier should use pointcache 
			// + have proper reset events before enabling this
			collmd->x = newdataadr(fd, collmd->x);
			collmd->xnew = newdataadr(fd, collmd->xnew);
			collmd->mfaces = newdataadr(fd, collmd->mfaces);
			
			collmd->current_x = MEM_callocN(sizeof(MVert)*collmd->numverts, "current_x");
			collmd->current_xnew = MEM_callocN(sizeof(MVert)*collmd->numverts, "current_xnew");
			collmd->current_v = MEM_callocN(sizeof(MVert)*collmd->numverts, "current_v");
#endif
			
			collmd->x = NULL;
			collmd->xnew = NULL;
			collmd->current_x = NULL;
			collmd->current_xnew = NULL;
			collmd->current_v = NULL;
			collmd->time_x = collmd->time_xnew = -1000;
			collmd->numverts = 0;
			collmd->bvhtree = NULL;
			collmd->mfaces = NULL;
			
		}
		else if (md->type == eModifierType_Surface) {
			SurfaceModifierData *surmd = (SurfaceModifierData *)md;
			
			surmd->dm = NULL;
			surmd->bvhtree = NULL;
			surmd->x = NULL;
			surmd->v = NULL;
			surmd->numverts = 0;
		}
		else if (md->type == eModifierType_Hook) {
			HookModifierData *hmd = (HookModifierData *)md;
			
			hmd->indexar = newdataadr(fd, hmd->indexar);
			if (fd->flags & FD_FLAGS_SWITCH_ENDIAN) {
				BLI_endian_switch_int32_array(hmd->indexar, hmd->totindex);
			}
		}
		else if (md->type == eModifierType_ParticleSystem) {
			ParticleSystemModifierData *psmd = (ParticleSystemModifierData *)md;
			
			psmd->dm= NULL;
			psmd->psys= newdataadr(fd, psmd->psys);
			psmd->flag &= ~eParticleSystemFlag_psys_updated;
			psmd->flag |= eParticleSystemFlag_file_loaded;
		}
		else if (md->type == eModifierType_Explode) {
			ExplodeModifierData *psmd = (ExplodeModifierData *)md;
			
			psmd->facepa = NULL;
		}
		else if (md->type == eModifierType_MeshDeform) {
			MeshDeformModifierData *mmd = (MeshDeformModifierData *)md;
			
			mmd->bindinfluences = newdataadr(fd, mmd->bindinfluences);
			mmd->bindoffsets = newdataadr(fd, mmd->bindoffsets);
			mmd->bindcagecos = newdataadr(fd, mmd->bindcagecos);
			mmd->dyngrid = newdataadr(fd, mmd->dyngrid);
			mmd->dyninfluences = newdataadr(fd, mmd->dyninfluences);
			mmd->dynverts = newdataadr(fd, mmd->dynverts);
			
			mmd->bindweights = newdataadr(fd, mmd->bindweights);
			mmd->bindcos = newdataadr(fd, mmd->bindcos);
			
			if (fd->flags & FD_FLAGS_SWITCH_ENDIAN) {
				if (mmd->bindoffsets)  BLI_endian_switch_int32_array(mmd->bindoffsets, mmd->totvert + 1);
				if (mmd->bindcagecos)  BLI_endian_switch_float_array(mmd->bindcagecos, mmd->totcagevert * 3);
				if (mmd->dynverts)     BLI_endian_switch_int32_array(mmd->dynverts, mmd->totvert);
				if (mmd->bindweights)  BLI_endian_switch_float_array(mmd->bindweights, mmd->totvert);
				if (mmd->bindcos)      BLI_endian_switch_float_array(mmd->bindcos, mmd->totcagevert * 3);
			}
		}
		else if (md->type == eModifierType_Ocean) {
			OceanModifierData *omd = (OceanModifierData *)md;
			omd->oceancache = NULL;
			omd->ocean = NULL;
			omd->refresh = (MOD_OCEAN_REFRESH_ADD|MOD_OCEAN_REFRESH_RESET|MOD_OCEAN_REFRESH_SIM);
		}
		else if (md->type == eModifierType_Warp) {
			WarpModifierData *tmd = (WarpModifierData *)md;
			
			tmd->curfalloff= newdataadr(fd, tmd->curfalloff);
			if (tmd->curfalloff)
				direct_link_curvemapping(fd, tmd->curfalloff);
		}
		else if (md->type == eModifierType_WeightVGEdit) {
			WeightVGEditModifierData *wmd = (WeightVGEditModifierData *)md;
			
			wmd->cmap_curve = newdataadr(fd, wmd->cmap_curve);
			if (wmd->cmap_curve)
				direct_link_curvemapping(fd, wmd->cmap_curve);
		}
	}
}

static void direct_link_object(FileData *fd, Object *ob)
{
	PartEff *paf;
	bProperty *prop;
	bSensor *sens;
	bController *cont;
	bActuator *act;
	
	/* weak weak... this was only meant as draw flag, now is used in give_base_to_objects too */
	ob->flag &= ~OB_FROMGROUP;

	/* loading saved files with editmode enabled works, but for undo we like
	 * to stay in object mode during undo presses so keep editmode disabled.
	 *
	 * Also when linking in a file don't allow editmode: [#34776] */
	if (fd->memfile || (ob->id.flag & (LIB_EXTERN | LIB_INDIRECT))) {
		ob->mode &= ~(OB_MODE_EDIT | OB_MODE_PARTICLE_EDIT);
	}
	
	ob->disp.first = ob->disp.last = NULL;
	
	ob->adt = newdataadr(fd, ob->adt);
	direct_link_animdata(fd, ob->adt);
	
	ob->pose = newdataadr(fd, ob->pose);
	direct_link_pose(fd, ob->pose);
	
	ob->mpath = newdataadr(fd, ob->mpath);
	if (ob->mpath)
		direct_link_motionpath(fd, ob->mpath);
	
	link_list(fd, &ob->defbase);
// XXX deprecated - old animation system <<<
	direct_link_nlastrips(fd, &ob->nlastrips);
	link_list(fd, &ob->constraintChannels);
// >>> XXX deprecated - old animation system
	
	ob->mat= newdataadr(fd, ob->mat);
	test_pointer_array(fd, (void **)&ob->mat);
	ob->matbits= newdataadr(fd, ob->matbits);
	
	/* do it here, below old data gets converted */
	direct_link_modifiers(fd, &ob->modifiers);
	
	link_list(fd, &ob->effect);
	paf= ob->effect.first;
	while (paf) {
		if (paf->type == EFF_PARTICLE) {
			paf->keys = NULL;
		}
		if (paf->type == EFF_WAVE) {
			WaveEff *wav = (WaveEff*) paf;
			PartEff *next = paf->next;
			WaveModifierData *wmd = (WaveModifierData*) modifier_new(eModifierType_Wave);
			
			wmd->damp = wav->damp;
			wmd->flag = wav->flag;
			wmd->height = wav->height;
			wmd->lifetime = wav->lifetime;
			wmd->narrow = wav->narrow;
			wmd->speed = wav->speed;
			wmd->startx = wav->startx;
			wmd->starty = wav->startx;
			wmd->timeoffs = wav->timeoffs;
			wmd->width = wav->width;
			
			BLI_addtail(&ob->modifiers, wmd);
			
			BLI_remlink(&ob->effect, paf);
			MEM_freeN(paf);
			
			paf = next;
			continue;
		}
		if (paf->type == EFF_BUILD) {
			BuildEff *baf = (BuildEff*) paf;
			PartEff *next = paf->next;
			BuildModifierData *bmd = (BuildModifierData*) modifier_new(eModifierType_Build);
			
			bmd->start = baf->sfra;
			bmd->length = baf->len;
			bmd->randomize = 0;
			bmd->seed = 1;
			
			BLI_addtail(&ob->modifiers, bmd);
			
			BLI_remlink(&ob->effect, paf);
			MEM_freeN(paf);
			
			paf = next;
			continue;
		}
		paf = paf->next;
	}
	
	ob->pd= newdataadr(fd, ob->pd);
	direct_link_partdeflect(ob->pd);
	ob->soft= newdataadr(fd, ob->soft);
	if (ob->soft) {
		SoftBody *sb = ob->soft;
		
		sb->bpoint = NULL;	// init pointers so it gets rebuilt nicely
		sb->bspring = NULL;
		sb->scratch = NULL;
		/* although not used anymore */
		/* still have to be loaded to be compatible with old files */
		sb->keys = newdataadr(fd, sb->keys);
		test_pointer_array(fd, (void **)&sb->keys);
		if (sb->keys) {
			int a;
			for (a = 0; a < sb->totkey; a++) {
				sb->keys[a] = newdataadr(fd, sb->keys[a]);
			}
		}
		
		sb->effector_weights = newdataadr(fd, sb->effector_weights);
		if (!sb->effector_weights)
			sb->effector_weights = BKE_add_effector_weights(NULL);
		
		direct_link_pointcache_list(fd, &sb->ptcaches, &sb->pointcache, 0);
	}
	ob->bsoft = newdataadr(fd, ob->bsoft);
	ob->fluidsimSettings= newdataadr(fd, ob->fluidsimSettings); /* NT */
	
	ob->rigidbody_object = newdataadr(fd, ob->rigidbody_object);
	if (ob->rigidbody_object) {
		RigidBodyOb *rbo = ob->rigidbody_object;
		
		/* must nullify the references to physics sim objects, since they no-longer exist 
		 * (and will need to be recalculated) 
		 */
		rbo->physics_object = NULL;
		rbo->physics_shape = NULL;
	}
	ob->rigidbody_constraint = newdataadr(fd, ob->rigidbody_constraint);
	if (ob->rigidbody_constraint)
		ob->rigidbody_constraint->physics_constraint = NULL;

	link_list(fd, &ob->particlesystem);
	direct_link_particlesystems(fd, &ob->particlesystem);
	
	link_list(fd, &ob->prop);
	for (prop = ob->prop.first; prop; prop = prop->next) {
		prop->poin = newdataadr(fd, prop->poin);
		if (prop->poin == NULL) 
			prop->poin = &prop->data;
	}

	link_list(fd, &ob->sensors);
	for (sens = ob->sensors.first; sens; sens = sens->next) {
		sens->data = newdataadr(fd, sens->data);
		sens->links = newdataadr(fd, sens->links);
		test_pointer_array(fd, (void **)&sens->links);
	}

	direct_link_constraints(fd, &ob->constraints);

	link_glob_list(fd, &ob->controllers);
	if (ob->init_state) {
		/* if a known first state is specified, set it so that the game will start ok */
		ob->state = ob->init_state;
	}
	else if (!ob->state) {
		ob->state = 1;
	}
	for (cont = ob->controllers.first; cont; cont = cont->next) {
		cont->data = newdataadr(fd, cont->data);
		cont->links = newdataadr(fd, cont->links);
		test_pointer_array(fd, (void **)&cont->links);
		if (cont->state_mask == 0)
			cont->state_mask = 1;
	}

	link_glob_list(fd, &ob->actuators);
	for (act = ob->actuators.first; act; act = act->next) {
		act->data = newdataadr(fd, act->data);
	}

	link_list(fd, &ob->hooks);
	while (ob->hooks.first) {
		ObHook *hook = ob->hooks.first;
		HookModifierData *hmd = (HookModifierData *)modifier_new(eModifierType_Hook);
		
		hook->indexar= newdataadr(fd, hook->indexar);
		if (fd->flags & FD_FLAGS_SWITCH_ENDIAN) {
			BLI_endian_switch_int32_array(hook->indexar, hook->totindex);
		}
		
		/* Do conversion here because if we have loaded
		 * a hook we need to make sure it gets converted
		 * and freed, regardless of version.
		 */
		copy_v3_v3(hmd->cent, hook->cent);
		hmd->falloff = hook->falloff;
		hmd->force = hook->force;
		hmd->indexar = hook->indexar;
		hmd->object = hook->parent;
		memcpy(hmd->parentinv, hook->parentinv, sizeof(hmd->parentinv));
		hmd->totindex = hook->totindex;
		
		BLI_addhead(&ob->modifiers, hmd);
		BLI_remlink(&ob->hooks, hook);
		
		modifier_unique_name(&ob->modifiers, (ModifierData*)hmd);
		
		MEM_freeN(hook);
	}
	
	ob->customdata_mask = 0;
	ob->bb = NULL;
	ob->derivedDeform = NULL;
	ob->derivedFinal = NULL;
	ob->gpulamp.first= ob->gpulamp.last = NULL;
	link_list(fd, &ob->pc_ids);

	/* in case this value changes in future, clamp else we get undefined behavior */
	CLAMP(ob->rotmode, ROT_MODE_MIN, ROT_MODE_MAX);

	if (ob->sculpt) {
		ob->sculpt = MEM_callocN(sizeof(SculptSession), "reload sculpt session");
	}
}

/* ************ READ SCENE ***************** */

/* patch for missing scene IDs, can't be in do-versions */
static void composite_patch(bNodeTree *ntree, Scene *scene)
{
	bNode *node;
	
	for (node = ntree->nodes.first; node; node = node->next) {
		if (node->id==NULL && ELEM4(node->type, CMP_NODE_R_LAYERS, CMP_NODE_COMPOSITE, CMP_NODE_DEFOCUS, CMP_NODE_OUTPUT_FILE))
			node->id = &scene->id;
	}
}

static void link_paint(FileData *fd, Scene *sce, Paint *p)
{
	if (p) {
		p->brush = newlibadr_us(fd, sce->id.lib, p->brush);
		p->paint_cursor = NULL;
	}
}

static void lib_link_sequence_modifiers(FileData *fd, Scene *scene, ListBase *lb)
{
	SequenceModifierData *smd;

	for (smd = lb->first; smd; smd = smd->next) {
		if (smd->mask_id)
			smd->mask_id = newlibadr_us(fd, scene->id.lib, smd->mask_id);
	}
}

static void lib_link_scene(FileData *fd, Main *main)
{
	Scene *sce;
	Base *base, *next;
	Sequence *seq;
	SceneRenderLayer *srl;
	TimeMarker *marker;
	FreestyleModuleConfig *fmc;
	FreestyleLineSet *fls;
	
	for (sce = main->scene.first; sce; sce = sce->id.next) {
		if (sce->id.flag & LIB_NEED_LINK) {
			/* Link ID Properties -- and copy this comment EXACTLY for easy finding
			 * of library blocks that implement this.*/
			if (sce->id.properties) IDP_LibLinkProperty(sce->id.properties, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
			if (sce->adt) lib_link_animdata(fd, &sce->id, sce->adt);
			
			lib_link_keyingsets(fd, &sce->id, &sce->keyingsets);
			
			sce->camera = newlibadr(fd, sce->id.lib, sce->camera);
			sce->world = newlibadr_us(fd, sce->id.lib, sce->world);
			sce->set = newlibadr(fd, sce->id.lib, sce->set);
			sce->gpd = newlibadr_us(fd, sce->id.lib, sce->gpd);
			
			link_paint(fd, sce, &sce->toolsettings->sculpt->paint);
			link_paint(fd, sce, &sce->toolsettings->vpaint->paint);
			link_paint(fd, sce, &sce->toolsettings->wpaint->paint);
			link_paint(fd, sce, &sce->toolsettings->imapaint.paint);
			link_paint(fd, sce, &sce->toolsettings->uvsculpt->paint);
			sce->toolsettings->skgen_template = newlibadr(fd, sce->id.lib, sce->toolsettings->skgen_template);
			
			for (base = sce->base.first; base; base = next) {
				next = base->next;
				
				/* base->object= newlibadr_us(fd, sce->id.lib, base->object); */
				base->object = newlibadr_us(fd, sce->id.lib, base->object);
				
				if (base->object == NULL) {
					BKE_reportf_wrap(fd->reports, RPT_WARNING, TIP_("LIB ERROR: object lost from scene: '%s'"),
					                 sce->id.name + 2);
					BLI_remlink(&sce->base, base);
					if (base == sce->basact) sce->basact = NULL;
					MEM_freeN(base);
				}
			}
			
			SEQ_BEGIN (sce->ed, seq)
			{
				if (seq->ipo) seq->ipo = newlibadr_us(fd, sce->id.lib, seq->ipo);
				seq->scene_sound = NULL;
				if (seq->scene) {
					seq->scene = newlibadr(fd, sce->id.lib, seq->scene);
					if (seq->scene) {
						seq->scene_sound = sound_scene_add_scene_sound_defaults(sce, seq);
					}
				}
				if (seq->clip) {
					seq->clip = newlibadr(fd, sce->id.lib, seq->clip);
					if (seq->clip) {
						seq->clip->id.us++;
					}
				}
				if (seq->mask) {
					seq->mask = newlibadr(fd, sce->id.lib, seq->mask);
					if (seq->mask) {
						seq->mask->id.us++;
					}
				}
				if (seq->scene_camera) {
					seq->scene_camera = newlibadr(fd, sce->id.lib, seq->scene_camera);
				}
				if (seq->sound) {
					seq->scene_sound = NULL;
					if (seq->type == SEQ_TYPE_SOUND_HD) {
						seq->type = SEQ_TYPE_SOUND_RAM;
					}
					else {
						seq->sound = newlibadr(fd, sce->id.lib, seq->sound);
					}
					if (seq->sound) {
						seq->sound->id.us++;
						seq->scene_sound = sound_add_scene_sound_defaults(sce, seq);
					}
				}
				seq->anim = NULL;

				lib_link_sequence_modifiers(fd, sce, &seq->modifiers);
			}
			SEQ_END

#ifdef DURIAN_CAMERA_SWITCH
			for (marker = sce->markers.first; marker; marker = marker->next) {
				if (marker->camera) {
					marker->camera = newlibadr(fd, sce->id.lib, marker->camera);
				}
			}
#else
			(void)marker;
#endif
			
			BKE_sequencer_update_muting(sce->ed);
			BKE_sequencer_update_sound_bounds_all(sce);
			
			
			/* rigidbody world relies on it's linked groups */
			if (sce->rigidbody_world) {
				RigidBodyWorld *rbw = sce->rigidbody_world;
				if (rbw->group)
					rbw->group = newlibadr(fd, sce->id.lib, rbw->group);
				if (rbw->constraints)
					rbw->constraints = newlibadr(fd, sce->id.lib, rbw->constraints);
				if (rbw->effector_weights)
					rbw->effector_weights->group = newlibadr(fd, sce->id.lib, rbw->effector_weights->group);
			}
			
			if (sce->nodetree) {
				lib_link_ntree(fd, &sce->id, sce->nodetree);
				sce->nodetree->id.lib = sce->id.lib;
				composite_patch(sce->nodetree, sce);
			}
			
			for (srl = sce->r.layers.first; srl; srl = srl->next) {
				srl->mat_override = newlibadr_us(fd, sce->id.lib, srl->mat_override);
				srl->light_override = newlibadr_us(fd, sce->id.lib, srl->light_override);
				for (fmc = srl->freestyleConfig.modules.first; fmc; fmc = fmc->next) {
					fmc->script = newlibadr(fd, sce->id.lib, fmc->script);
				}
				for (fls = srl->freestyleConfig.linesets.first; fls; fls = fls->next) {
					fls->linestyle = newlibadr_us(fd, sce->id.lib, fls->linestyle);
					fls->group = newlibadr_us(fd, sce->id.lib, fls->group);
				}
			}
			/*Game Settings: Dome Warp Text*/
			sce->gm.dome.warptext = newlibadr(fd, sce->id.lib, sce->gm.dome.warptext);
			
			/* Motion Tracking */
			sce->clip = newlibadr_us(fd, sce->id.lib, sce->clip);
			
			sce->id.flag -= LIB_NEED_LINK;
		}
	}
}

static void link_recurs_seq(FileData *fd, ListBase *lb)
{
	Sequence *seq;
	
	link_list(fd, lb);
	
	for (seq = lb->first; seq; seq = seq->next) {
		if (seq->seqbase.first)
			link_recurs_seq(fd, &seq->seqbase);
	}
}

static void direct_link_paint(FileData *fd, Paint **paint)
{
	/* TODO. is this needed */
	(*paint) = newdataadr(fd, (*paint));
	if (*paint && (*paint)->num_input_samples < 1)
		(*paint)->num_input_samples = 1;
}

static void direct_link_sequence_modifiers(FileData *fd, ListBase *lb)
{
	SequenceModifierData *smd;

	link_list(fd, lb);

	for (smd = lb->first; smd; smd = smd->next) {
		if (smd->mask_sequence)
			smd->mask_sequence = newdataadr(fd, smd->mask_sequence);

		if (smd->type == seqModifierType_Curves) {
			CurvesModifierData *cmd = (CurvesModifierData *) smd;

			direct_link_curvemapping(fd, &cmd->curve_mapping);
		}
		else if (smd->type == seqModifierType_HueCorrect) {
			HueCorrectModifierData *hcmd = (HueCorrectModifierData *) smd;

			direct_link_curvemapping(fd, &hcmd->curve_mapping);
		}
	}
}

static void direct_link_view_settings(FileData *fd, ColorManagedViewSettings *view_settings)
{
	view_settings->curve_mapping = newdataadr(fd, view_settings->curve_mapping);

	if (view_settings->curve_mapping)
		direct_link_curvemapping(fd, view_settings->curve_mapping);
}

static void direct_link_scene(FileData *fd, Scene *sce)
{
	Editing *ed;
	Sequence *seq;
	MetaStack *ms;
	RigidBodyWorld *rbw;
	SceneRenderLayer *srl;
	
	sce->theDag = NULL;
	sce->obedit = NULL;
	sce->stats = NULL;
	sce->fps_info = NULL;
	sce->customdata_mask_modal = 0;
	sce->lay_updated = 0;
	
	sound_create_scene(sce);
	
	/* set users to one by default, not in lib-link, this will increase it for compo nodes */
	sce->id.us = 1;
	
	link_list(fd, &(sce->base));
	
	sce->adt = newdataadr(fd, sce->adt);
	direct_link_animdata(fd, sce->adt);
	
	link_list(fd, &sce->keyingsets);
	direct_link_keyingsets(fd, &sce->keyingsets);
	
	sce->basact = newdataadr(fd, sce->basact);
	
	sce->toolsettings= newdataadr(fd, sce->toolsettings);
	if (sce->toolsettings) {
		direct_link_paint(fd, (Paint**)&sce->toolsettings->sculpt);
		direct_link_paint(fd, (Paint**)&sce->toolsettings->vpaint);
		direct_link_paint(fd, (Paint**)&sce->toolsettings->wpaint);
		direct_link_paint(fd, (Paint**)&sce->toolsettings->uvsculpt);
		
		sce->toolsettings->imapaint.paintcursor = NULL;
		sce->toolsettings->particle.paintcursor = NULL;

		/* in rare cases this is needed, see [#33806] */
		if (sce->toolsettings->vpaint) {
			sce->toolsettings->vpaint->vpaint_prev = NULL;
			sce->toolsettings->vpaint->tot = 0;
		}
		if (sce->toolsettings->wpaint) {
			sce->toolsettings->wpaint->wpaint_prev = NULL;
			sce->toolsettings->wpaint->tot = 0;
		}
	}

	if (sce->ed) {
		ListBase *old_seqbasep = &((Editing *)sce->ed)->seqbase;
		
		ed = sce->ed = newdataadr(fd, sce->ed);
		
		ed->act_seq = newdataadr(fd, ed->act_seq);
		
		/* recursive link sequences, lb will be correctly initialized */
		link_recurs_seq(fd, &ed->seqbase);
		
		SEQ_BEGIN (ed, seq)
		{
			seq->seq1= newdataadr(fd, seq->seq1);
			seq->seq2= newdataadr(fd, seq->seq2);
			seq->seq3= newdataadr(fd, seq->seq3);
			/* a patch: after introduction of effects with 3 input strips */
			if (seq->seq3 == NULL) seq->seq3 = seq->seq2;
			
			seq->effectdata = newdataadr(fd, seq->effectdata);
			
			if (seq->type & SEQ_TYPE_EFFECT)
				seq->flag |= SEQ_EFFECT_NOT_LOADED;
			
			if (seq->type == SEQ_TYPE_SPEED) {
				SpeedControlVars *s = seq->effectdata;
				s->frameMap = NULL;
			}
			
			seq->strip = newdataadr(fd, seq->strip);
			if (seq->strip && seq->strip->done==0) {
				seq->strip->done = TRUE;
				
				if (ELEM4(seq->type, SEQ_TYPE_IMAGE, SEQ_TYPE_MOVIE, SEQ_TYPE_SOUND_RAM, SEQ_TYPE_SOUND_HD)) {
					seq->strip->stripdata = newdataadr(fd, seq->strip->stripdata);
				}
				else {
					seq->strip->stripdata = NULL;
				}
				if (seq->flag & SEQ_USE_CROP) {
					seq->strip->crop = newdataadr(
						fd, seq->strip->crop);
				}
				else {
					seq->strip->crop = NULL;
				}
				if (seq->flag & SEQ_USE_TRANSFORM) {
					seq->strip->transform = newdataadr(
						fd, seq->strip->transform);
				}
				else {
					seq->strip->transform = NULL;
				}
				if (seq->flag & SEQ_USE_PROXY) {
					seq->strip->proxy = newdataadr(
						fd, seq->strip->proxy);
					seq->strip->proxy->anim = NULL;
				}
				else {
					seq->strip->proxy = NULL;
				}

				/* need to load color balance to it could be converted to modifier */
				seq->strip->color_balance = newdataadr(fd, seq->strip->color_balance);
			}

			direct_link_sequence_modifiers(fd, &seq->modifiers);
		}
		SEQ_END
		
		/* link metastack, slight abuse of structs here, have to restore pointer to internal part in struct */
		{
			Sequence temp;
			char *poin;
			intptr_t offset;
			
			offset = ((intptr_t)&(temp.seqbase)) - ((intptr_t)&temp);
			
			/* root pointer */
			if (ed->seqbasep == old_seqbasep) {
				ed->seqbasep = &ed->seqbase;
			}
			else {
				poin = (char *)ed->seqbasep;
				poin -= offset;
				
				poin = newdataadr(fd, poin);
				if (poin)
					ed->seqbasep = (ListBase *)(poin+offset);
				else
					ed->seqbasep = &ed->seqbase;
			}
			/* stack */
			link_list(fd, &(ed->metastack));
			
			for (ms = ed->metastack.first; ms; ms= ms->next) {
				ms->parseq = newdataadr(fd, ms->parseq);
				
				if (ms->oldbasep == old_seqbasep)
					ms->oldbasep= &ed->seqbase;
				else {
					poin = (char *)ms->oldbasep;
					poin -= offset;
					poin = newdataadr(fd, poin);
					if (poin) 
						ms->oldbasep = (ListBase *)(poin+offset);
					else 
						ms->oldbasep = &ed->seqbase;
				}
			}
		}
	}
	
	sce->r.avicodecdata = newdataadr(fd, sce->r.avicodecdata);
	if (sce->r.avicodecdata) {
		sce->r.avicodecdata->lpFormat = newdataadr(fd, sce->r.avicodecdata->lpFormat);
		sce->r.avicodecdata->lpParms = newdataadr(fd, sce->r.avicodecdata->lpParms);
	}
	
	sce->r.qtcodecdata = newdataadr(fd, sce->r.qtcodecdata);
	if (sce->r.qtcodecdata) {
		sce->r.qtcodecdata->cdParms = newdataadr(fd, sce->r.qtcodecdata->cdParms);
	}
	if (sce->r.ffcodecdata.properties) {
		sce->r.ffcodecdata.properties = newdataadr(fd, sce->r.ffcodecdata.properties);
		if (sce->r.ffcodecdata.properties) {
			IDP_DirectLinkProperty(sce->r.ffcodecdata.properties, 
				(fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
		}
	}
	
	link_list(fd, &(sce->markers));
	link_list(fd, &(sce->transform_spaces));
	link_list(fd, &(sce->r.layers));

	for(srl = sce->r.layers.first; srl; srl = srl->next) {
		link_list(fd, &(srl->freestyleConfig.modules));
	}
	for(srl = sce->r.layers.first; srl; srl = srl->next) {
		link_list(fd, &(srl->freestyleConfig.linesets));
	}
	
	sce->nodetree = newdataadr(fd, sce->nodetree);
	if (sce->nodetree) {
		direct_link_id(fd, &sce->nodetree->id);
		direct_link_nodetree(fd, sce->nodetree);
	}

	direct_link_view_settings(fd, &sce->view_settings);
	
	sce->rigidbody_world = newdataadr(fd, sce->rigidbody_world);
	rbw = sce->rigidbody_world;
	if (rbw) {
		/* must nullify the reference to physics sim object, since it no-longer exist 
		 * (and will need to be recalculated) 
		 */
		rbw->physics_world = NULL;
		rbw->objects = NULL;
		rbw->numbodies = 0;

		/* set effector weights */
		rbw->effector_weights = newdataadr(fd, rbw->effector_weights);
		if (!rbw->effector_weights)
			rbw->effector_weights = BKE_add_effector_weights(NULL);

		/* link cache */
		direct_link_pointcache_list(fd, &rbw->ptcaches, &rbw->pointcache, FALSE);
		/* make sure simulation starts from the beginning after loading file */
		if (rbw->pointcache) {
			rbw->ltime = (float)rbw->pointcache->startframe;
		}
	}
}

/* ************ READ WM ***************** */

static void direct_link_windowmanager(FileData *fd, wmWindowManager *wm)
{
	wmWindow *win;
	
	wm->id.us = 1;
	link_list(fd, &wm->windows);
	
	for (win = wm->windows.first; win; win = win->next) {
		win->ghostwin = NULL;
		win->eventstate = NULL;
		win->curswin = NULL;
		win->tweak = NULL;
		
		win->queue.first = win->queue.last = NULL;
		win->handlers.first = win->handlers.last = NULL;
		win->modalhandlers.first = win->modalhandlers.last = NULL;
		win->subwindows.first = win->subwindows.last = NULL;
		win->gesture.first = win->gesture.last = NULL;
		
		win->drawdata = NULL;
		win->drawmethod = -1;
		win->drawfail = 0;
		win->active = 0;
	}
	
	wm->timers.first = wm->timers.last = NULL;
	wm->operators.first = wm->operators.last = NULL;
	wm->paintcursors.first = wm->paintcursors.last = NULL;
	wm->queue.first = wm->queue.last = NULL;
	BKE_reports_init(&wm->reports, RPT_STORE);
	
	wm->keyconfigs.first = wm->keyconfigs.last = NULL;
	wm->defaultconf = NULL;
	wm->addonconf = NULL;
	wm->userconf = NULL;
	
	wm->jobs.first = wm->jobs.last = NULL;
	wm->drags.first = wm->drags.last = NULL;
	
	wm->windrawable = NULL;
	wm->winactive = NULL;
	wm->initialized = 0;
	wm->op_undo_depth = 0;
	wm->is_interface_locked = 0;
}

static void lib_link_windowmanager(FileData *fd, Main *main)
{
	wmWindowManager *wm;
	wmWindow *win;
	
	for (wm = main->wm.first; wm; wm = wm->id.next) {
		if (wm->id.flag & LIB_NEED_LINK) {
			for (win = wm->windows.first; win; win = win->next)
				win->screen = newlibadr(fd, NULL, win->screen);
			
			wm->id.flag -= LIB_NEED_LINK;
		}
	}
}

/* ****************** READ GREASE PENCIL ***************** */

/* relinks grease-pencil data - used for direct_link and old file linkage */
static void direct_link_gpencil(FileData *fd, bGPdata *gpd)
{
	bGPDlayer *gpl;
	bGPDframe *gpf;
	bGPDstroke *gps;
	
	/* we must firstly have some grease-pencil data to link! */
	if (gpd == NULL)
		return;
	
	/* relink layers */
	link_list(fd, &gpd->layers);
	
	for (gpl = gpd->layers.first; gpl; gpl = gpl->next) {
		/* relink frames */
		link_list(fd, &gpl->frames);
		gpl->actframe = newdataadr(fd, gpl->actframe);
		
		for (gpf = gpl->frames.first; gpf; gpf = gpf->next) {
			/* relink strokes (and their points) */
			link_list(fd, &gpf->strokes);
			
			for (gps = gpf->strokes.first; gps; gps = gps->next) {
				gps->points = newdataadr(fd, gps->points);
			}
		}
	}
}

/* ****************** READ SCREEN ***************** */

/* note: file read without screens option G_FILE_NO_UI; 
 * check lib pointers in call below */
static void lib_link_screen(FileData *fd, Main *main)
{
	bScreen *sc;
	ScrArea *sa;
	
	for (sc = main->screen.first; sc; sc = sc->id.next) {
		if (sc->id.flag & LIB_NEED_LINK) {
			sc->id.us = 1;
			sc->scene = newlibadr(fd, sc->id.lib, sc->scene);
			sc->animtimer = NULL; /* saved in rare cases */
			
			for (sa = sc->areabase.first; sa; sa = sa->next) {
				SpaceLink *sl;
				
				sa->full = newlibadr(fd, sc->id.lib, sa->full);
				
				for (sl = sa->spacedata.first; sl; sl= sl->next) {
					if (sl->spacetype == SPACE_VIEW3D) {
						View3D *v3d = (View3D*) sl;
						BGpic *bgpic = NULL;
						
						v3d->camera= newlibadr(fd, sc->id.lib, v3d->camera);
						v3d->ob_centre= newlibadr(fd, sc->id.lib, v3d->ob_centre);
						
						/* should be do_versions but not easy adding into the listbase */
						if (v3d->bgpic) {
							v3d->bgpic = newlibadr(fd, sc->id.lib, v3d->bgpic);
							BLI_addtail(&v3d->bgpicbase, bgpic);
							v3d->bgpic = NULL;
						}
						
						for (bgpic = v3d->bgpicbase.first; bgpic; bgpic = bgpic->next) {
							bgpic->ima = newlibadr_us(fd, sc->id.lib, bgpic->ima);
							bgpic->clip = newlibadr_us(fd, sc->id.lib, bgpic->clip);
						}
						if (v3d->localvd) {
							v3d->localvd->camera = newlibadr(fd, sc->id.lib, v3d->localvd->camera);
						}
					}
					else if (sl->spacetype == SPACE_IPO) {
						SpaceIpo *sipo = (SpaceIpo *)sl;
						bDopeSheet *ads = sipo->ads;
						
						if (ads) {
							ads->source = newlibadr(fd, sc->id.lib, ads->source);
							ads->filter_grp = newlibadr(fd, sc->id.lib, ads->filter_grp);
						}
					}
					else if (sl->spacetype == SPACE_BUTS) {
						SpaceButs *sbuts = (SpaceButs *)sl;
						sbuts->pinid = newlibadr(fd, sc->id.lib, sbuts->pinid);
					}
					else if (sl->spacetype == SPACE_FILE) {
						;
					}
					else if (sl->spacetype == SPACE_ACTION) {
						SpaceAction *saction = (SpaceAction *)sl;
						bDopeSheet *ads = &saction->ads;
						
						if (ads) {
							ads->source = newlibadr(fd, sc->id.lib, ads->source);
							ads->filter_grp = newlibadr(fd, sc->id.lib, ads->filter_grp);
						}
						
						saction->action = newlibadr(fd, sc->id.lib, saction->action);
					}
					else if (sl->spacetype == SPACE_IMAGE) {
						SpaceImage *sima = (SpaceImage *)sl;
						
						sima->image = newlibadr_us(fd, sc->id.lib, sima->image);
						sima->mask_info.mask = newlibadr_us(fd, sc->id.lib, sima->mask_info.mask);

						/* NOTE: pre-2.5, this was local data not lib data, but now we need this as lib data
						 * so fingers crossed this works fine!
						 */
						sima->gpd = newlibadr_us(fd, sc->id.lib, sima->gpd);
					}
					else if (sl->spacetype == SPACE_SEQ) {
						SpaceSeq *sseq = (SpaceSeq *)sl;
						
						/* NOTE: pre-2.5, this was local data not lib data, but now we need this as lib data
						 * so fingers crossed this works fine!
						 */
						sseq->gpd = newlibadr_us(fd, sc->id.lib, sseq->gpd);

					}
					else if (sl->spacetype == SPACE_NLA) {
						SpaceNla *snla= (SpaceNla *)sl;
						bDopeSheet *ads= snla->ads;
						
						if (ads) {
							ads->source = newlibadr(fd, sc->id.lib, ads->source);
							ads->filter_grp = newlibadr(fd, sc->id.lib, ads->filter_grp);
						}
					}
					else if (sl->spacetype == SPACE_TEXT) {
						SpaceText *st= (SpaceText *)sl;
						
						st->text= newlibadr(fd, sc->id.lib, st->text);
					}
					else if (sl->spacetype == SPACE_SCRIPT) {
						SpaceScript *scpt = (SpaceScript *)sl;
						/*scpt->script = NULL; - 2.45 set to null, better re-run the script */
						if (scpt->script) {
							scpt->script = newlibadr(fd, sc->id.lib, scpt->script);
							if (scpt->script) {
								SCRIPT_SET_NULL(scpt->script);
							}
						}
					}
					else if (sl->spacetype == SPACE_OUTLINER) {
						SpaceOops *so= (SpaceOops *)sl;
						TreeStoreElem *tselem;
						int a;
						
						so->search_tse.id = newlibadr(fd, NULL, so->search_tse.id);
						
						if (so->treestore) {
							tselem = so->treestore->data;
							for (a=0; a < so->treestore->usedelem; a++, tselem++) {
								tselem->id = newlibadr(fd, NULL, tselem->id);
							}
						}
					}
					else if (sl->spacetype == SPACE_NODE) {
						SpaceNode *snode = (SpaceNode *)sl;
						bNodeTreePath *path, *path_next;
						bNodeTree *ntree;
						
						/* node tree can be stored locally in id too, link this first */
						snode->id = newlibadr(fd, sc->id.lib, snode->id);
						snode->from = newlibadr(fd, sc->id.lib, snode->from);
						
						ntree = nodetree_from_id(snode->id);
						if (ntree)
							snode->nodetree = ntree;
						else
							snode->nodetree = newlibadr(fd, sc->id.lib, snode->nodetree);
						
						for (path = snode->treepath.first; path; path = path->next) {
							if (path == snode->treepath.first) {
								/* first nodetree in path is same as snode->nodetree */
								path->nodetree = snode->nodetree;
							}
							else
								path->nodetree = newlibadr(fd, sc->id.lib, path->nodetree);
							
							if (!path->nodetree)
								break;
						}
						
						/* remaining path entries are invalid, remove */
						for (; path; path = path_next) {
							path_next = path->next;
							
							BLI_remlink(&snode->treepath, path);
							MEM_freeN(path);
						}
						
						/* edittree is just the last in the path,
						 * set this directly since the path may have been shortened above */
						if (snode->treepath.last) {
							path = snode->treepath.last;
							snode->edittree = path->nodetree;
						}
						else
							snode->edittree = NULL;
					}
					else if (sl->spacetype == SPACE_CLIP) {
						SpaceClip *sclip = (SpaceClip *)sl;
						
						sclip->clip = newlibadr_us(fd, sc->id.lib, sclip->clip);
						sclip->mask_info.mask = newlibadr_us(fd, sc->id.lib, sclip->mask_info.mask);
					}
					else if (sl->spacetype == SPACE_LOGIC) {
						SpaceLogic *slogic = (SpaceLogic *)sl;
						
						slogic->gpd = newlibadr_us(fd, sc->id.lib, slogic->gpd);
					}
				}
			}
			sc->id.flag -= LIB_NEED_LINK;
		}
	}
}

static bool restore_pointer(ID *id, ID *newid, int user)
{
	if (strcmp(newid->name + 2, id->name + 2) == 0) {
		if (newid->lib == id->lib) {
			if (user == 1) {
				if (newid->us == 0) {
					newid->us++;
				}
			}
			else if (user == 2) {
				id_us_ensure_real(newid);
			}
			return true;
		}
	}
	return false;
}

/**
 * Only for undo files, or to restore a screen after reading without UI...
 *
 * user
 * - 0: no usercount change
 * - 1: ensure a user
 * - 2: ensure a real user (even if a fake one is set)
 */
static void *restore_pointer_by_name(Main *mainp, ID *id, int user)
{
	if (id) {
		ListBase *lb = which_libbase(mainp, GS(id->name));
		if (lb) {	// there's still risk of checking corrupt mem (freed Ids in oops)
			ID *idn = lb->first;
			
			for (; idn; idn = idn->next) {
				if (restore_pointer(id, idn, user))
					break;
			}
			
			return idn;
		}
	}
	return NULL;
}

static int lib_link_seq_clipboard_cb(Sequence *seq, void *arg_pt)
{
	Main *newmain = (Main *)arg_pt;
	
	if (seq->sound) {
		seq->sound = restore_pointer_by_name(newmain, (ID *)seq->sound, 0);
		seq->sound->id.us++;
	}
	
	if (seq->scene)
		seq->scene = restore_pointer_by_name(newmain, (ID *)seq->scene, 1);
	
	if (seq->scene_camera)
		seq->scene_camera = restore_pointer_by_name(newmain, (ID *)seq->scene_camera, 1);
	
	return 1;
}

static void lib_link_clipboard_restore(Main *newmain)
{
	/* update IDs stored in sequencer clipboard */
	BKE_sequencer_base_recursive_apply(&seqbase_clipboard, lib_link_seq_clipboard_cb, newmain);
}

/* called from kernel/blender.c */
/* used to link a file (without UI) to the current UI */
/* note that it assumes the old pointers in UI are still valid, so old Main is not freed */
void blo_lib_link_screen_restore(Main *newmain, bScreen *curscreen, Scene *curscene)
{
	wmWindow *win;
	wmWindowManager *wm;
	bScreen *sc;
	ScrArea *sa;
	
	/* first windowmanager */
	for (wm = newmain->wm.first; wm; wm = wm->id.next) {
		for (win= wm->windows.first; win; win= win->next) {
			win->screen = restore_pointer_by_name(newmain, (ID *)win->screen, 1);
			
			if (win->screen == NULL)
				win->screen = curscreen;
			
			win->screen->winid = win->winid;
		}
	}
	
	
	for (sc = newmain->screen.first; sc; sc = sc->id.next) {
		Scene *oldscene = sc->scene;
		
		sc->scene= restore_pointer_by_name(newmain, (ID *)sc->scene, 1);
		if (sc->scene == NULL)
			sc->scene = curscene;
		
		/* keep cursor location through undo */
		copy_v3_v3(sc->scene->cursor, oldscene->cursor);
		
		for (sa = sc->areabase.first; sa; sa = sa->next) {
			SpaceLink *sl;
			
			for (sl = sa->spacedata.first; sl; sl = sl->next) {
				if (sl->spacetype == SPACE_VIEW3D) {
					View3D *v3d = (View3D *)sl;
					BGpic *bgpic;
					ARegion *ar;
					
					if (v3d->scenelock)
						v3d->camera = NULL; /* always get from scene */
					else
						v3d->camera = restore_pointer_by_name(newmain, (ID *)v3d->camera, 1);
					if (v3d->camera == NULL)
						v3d->camera = sc->scene->camera;
					v3d->ob_centre = restore_pointer_by_name(newmain, (ID *)v3d->ob_centre, 1);
					
					for (bgpic= v3d->bgpicbase.first; bgpic; bgpic= bgpic->next) {
						bgpic->ima = restore_pointer_by_name(newmain, (ID *)bgpic->ima, 1);
						bgpic->clip = restore_pointer_by_name(newmain, (ID *)bgpic->clip, 1);
					}
					if (v3d->localvd) {
						/*Base *base;*/
						
						v3d->localvd->camera = sc->scene->camera;
						
						/* localview can become invalid during undo/redo steps, so we exit it when no could be found */
#if 0					/* XXX  regionlocalview ? */
						for (base= sc->scene->base.first; base; base= base->next) {
							if (base->lay & v3d->lay) break;
						}
						if (base==NULL) {
							v3d->lay= v3d->localvd->lay;
							v3d->layact= v3d->localvd->layact;
							MEM_freeN(v3d->localvd); 
							v3d->localvd= NULL;
						}
#endif
					}
					else if (v3d->scenelock) {
						v3d->lay = sc->scene->lay;
					}
					
					/* not very nice, but could help */
					if ((v3d->layact & v3d->lay) == 0) v3d->layact = v3d->lay;
					
					/* free render engines for now */
					for (ar = sa->regionbase.first; ar; ar = ar->next) {
						RegionView3D *rv3d= ar->regiondata;
						
						if (rv3d && rv3d->render_engine) {
							RE_engine_free(rv3d->render_engine);
							rv3d->render_engine = NULL;
						}
					}
				}
				else if (sl->spacetype == SPACE_IPO) {
					SpaceIpo *sipo = (SpaceIpo *)sl;
					bDopeSheet *ads = sipo->ads;
					
					if (ads) {
						ads->source = restore_pointer_by_name(newmain, (ID *)ads->source, 1);
						
						if (ads->filter_grp)
							ads->filter_grp = restore_pointer_by_name(newmain, (ID *)ads->filter_grp, 0);
					}
					
					/* force recalc of list of channels (i.e. includes calculating F-Curve colors)
					 * thus preventing the "black curves" problem post-undo
					 */
					sipo->flag |= SIPO_TEMP_NEEDCHANSYNC;
				}
				else if (sl->spacetype == SPACE_BUTS) {
					SpaceButs *sbuts = (SpaceButs *)sl;
					sbuts->pinid = restore_pointer_by_name(newmain, sbuts->pinid, 0);
					//XXX if (sbuts->ri) sbuts->ri->curtile = 0;
				}
				else if (sl->spacetype == SPACE_FILE) {
					SpaceFile *sfile = (SpaceFile *)sl;
					sfile->op = NULL;
				}
				else if (sl->spacetype == SPACE_ACTION) {
					SpaceAction *saction = (SpaceAction *)sl;
					
					saction->action = restore_pointer_by_name(newmain, (ID *)saction->action, 1);
					saction->ads.source = restore_pointer_by_name(newmain, (ID *)saction->ads.source, 1);
					
					if (saction->ads.filter_grp)
						saction->ads.filter_grp = restore_pointer_by_name(newmain, (ID *)saction->ads.filter_grp, 0);
						
					
					/* force recalc of list of channels, potentially updating the active action 
					 * while we're at it (as it can only be updated that way) [#28962] 
					 */
					saction->flag |= SACTION_TEMP_NEEDCHANSYNC;
				}
				else if (sl->spacetype == SPACE_IMAGE) {
					SpaceImage *sima = (SpaceImage *)sl;
					
					sima->image = restore_pointer_by_name(newmain, (ID *)sima->image, 2);
					
					/* this will be freed, not worth attempting to find same scene,
					 * since it gets initialized later */
					sima->iuser.scene = NULL;
					
					sima->scopes.waveform_1 = NULL;
					sima->scopes.waveform_2 = NULL;
					sima->scopes.waveform_3 = NULL;
					sima->scopes.vecscope = NULL;
					sima->scopes.ok = 0;
					
					/* NOTE: pre-2.5, this was local data not lib data, but now we need this as lib data
					 * so assume that here we're doing for undo only...
					 */
					sima->gpd = restore_pointer_by_name(newmain, (ID *)sima->gpd, 1);
					sima->mask_info.mask = restore_pointer_by_name(newmain, (ID *)sima->mask_info.mask, 2);
				}
				else if (sl->spacetype == SPACE_SEQ) {
					SpaceSeq *sseq = (SpaceSeq *)sl;
					
					/* NOTE: pre-2.5, this was local data not lib data, but now we need this as lib data
					 * so assume that here we're doing for undo only...
					 */
					sseq->gpd = restore_pointer_by_name(newmain, (ID *)sseq->gpd, 1);
				}
				else if (sl->spacetype == SPACE_NLA) {
					SpaceNla *snla = (SpaceNla *)sl;
					bDopeSheet *ads = snla->ads;
					
					if (ads) {
						ads->source = restore_pointer_by_name(newmain, (ID *)ads->source, 1);
						
						if (ads->filter_grp)
							ads->filter_grp = restore_pointer_by_name(newmain, (ID *)ads->filter_grp, 0);
					}
				}
				else if (sl->spacetype == SPACE_TEXT) {
					SpaceText *st = (SpaceText *)sl;
					
					st->text = restore_pointer_by_name(newmain, (ID *)st->text, 1);
					if (st->text == NULL) st->text = newmain->text.first;
				}
				else if (sl->spacetype == SPACE_SCRIPT) {
					SpaceScript *scpt = (SpaceScript *)sl;
					
					scpt->script = restore_pointer_by_name(newmain, (ID *)scpt->script, 1);
					
					/*sc->script = NULL; - 2.45 set to null, better re-run the script */
					if (scpt->script) {
						SCRIPT_SET_NULL(scpt->script);
					}
				}
				else if (sl->spacetype == SPACE_OUTLINER) {
					SpaceOops *so= (SpaceOops *)sl;
					int a;
					
					so->search_tse.id = restore_pointer_by_name(newmain, so->search_tse.id, 0);
					
					if (so->treestore) {
						TreeStore *ts = so->treestore;
						TreeStoreElem *tselem = ts->data;
						for (a = 0; a < ts->usedelem; a++, tselem++) {
							tselem->id = restore_pointer_by_name(newmain, tselem->id, 0);
						}
					}
				}
				else if (sl->spacetype == SPACE_NODE) {
					SpaceNode *snode= (SpaceNode *)sl;
					bNodeTreePath *path, *path_next;
					bNodeTree *ntree;
					
					/* node tree can be stored locally in id too, link this first */
					snode->id = restore_pointer_by_name(newmain, snode->id, 1);
					snode->from = restore_pointer_by_name(newmain, snode->from, 0);
					
					ntree = nodetree_from_id(snode->id);
					if (ntree)
						snode->nodetree = ntree;
					else
						snode->nodetree = restore_pointer_by_name(newmain, (ID*)snode->nodetree, 0);
					
					for (path = snode->treepath.first; path; path = path->next) {
						if (path == snode->treepath.first) {
							/* first nodetree in path is same as snode->nodetree */
							path->nodetree = snode->nodetree;
						}
						else
							path->nodetree= restore_pointer_by_name(newmain, (ID*)path->nodetree, 0);
						
						if (!path->nodetree)
							break;
					}
					
					/* remaining path entries are invalid, remove */
					for (; path; path = path_next) {
						path_next = path->next;
						
						BLI_remlink(&snode->treepath, path);
						MEM_freeN(path);
					}
					
					/* edittree is just the last in the path,
					 * set this directly since the path may have been shortened above */
					if (snode->treepath.last) {
						path = snode->treepath.last;
						snode->edittree = path->nodetree;
					}
					else
						snode->edittree = NULL;
				}
				else if (sl->spacetype == SPACE_CLIP) {
					SpaceClip *sclip = (SpaceClip *)sl;
					
					sclip->clip = restore_pointer_by_name(newmain, (ID *)sclip->clip, 2);
					sclip->mask_info.mask = restore_pointer_by_name(newmain, (ID *)sclip->mask_info.mask, 2);
					
					sclip->scopes.ok = 0;
				}
				else if (sl->spacetype == SPACE_LOGIC) {
					SpaceLogic *slogic = (SpaceLogic *)sl;
					
					slogic->gpd = restore_pointer_by_name(newmain, (ID *)slogic->gpd, 1);
				}
			}
		}
	}

	/* update IDs stored in all possible clipboards */
	lib_link_clipboard_restore(newmain);
}

static void direct_link_region(FileData *fd, ARegion *ar, int spacetype)
{
	Panel *pa;
	uiList *ui_list;

	link_list(fd, &ar->panels);

	for (pa = ar->panels.first; pa; pa = pa->next) {
		pa->paneltab = newdataadr(fd, pa->paneltab);
		pa->runtime_flag = 0;
		pa->activedata = NULL;
		pa->type = NULL;
	}

	link_list(fd, &ar->ui_lists);

	for (ui_list = ar->ui_lists.first; ui_list; ui_list = ui_list->next) {
		ui_list->type = NULL;
	}

	ar->regiondata = newdataadr(fd, ar->regiondata);
	if (ar->regiondata) {
		if (spacetype == SPACE_VIEW3D) {
			RegionView3D *rv3d = ar->regiondata;
			
			rv3d->localvd = newdataadr(fd, rv3d->localvd);
			rv3d->clipbb = newdataadr(fd, rv3d->clipbb);
			
			rv3d->depths = NULL;
			rv3d->gpuoffscreen = NULL;
			rv3d->ri = NULL;
			rv3d->render_engine = NULL;
			rv3d->sms = NULL;
			rv3d->smooth_timer = NULL;
		}
	}
	
	ar->v2d.tab_offset = NULL;
	ar->v2d.tab_num = 0;
	ar->v2d.tab_cur = 0;
	ar->v2d.sms = NULL;
	ar->handlers.first = ar->handlers.last = NULL;
	ar->uiblocks.first = ar->uiblocks.last = NULL;
	ar->headerstr = NULL;
	ar->swinid = 0;
	ar->type = NULL;
	ar->swap = 0;
	ar->do_draw = FALSE;
	ar->regiontimer = NULL;
	memset(&ar->drawrct, 0, sizeof(ar->drawrct));
}

/* for the saved 2.50 files without regiondata */
/* and as patch for 2.48 and older */
void blo_do_versions_view3d_split_250(View3D *v3d, ListBase *regions)
{
	ARegion *ar;
	
	for (ar = regions->first; ar; ar = ar->next) {
		if (ar->regiontype==RGN_TYPE_WINDOW && ar->regiondata==NULL) {
			RegionView3D *rv3d;
			
			rv3d = ar->regiondata = MEM_callocN(sizeof(RegionView3D), "region v3d patch");
			rv3d->persp = (char)v3d->persp;
			rv3d->view = (char)v3d->view;
			rv3d->dist = v3d->dist;
			copy_v3_v3(rv3d->ofs, v3d->ofs);
			copy_qt_qt(rv3d->viewquat, v3d->viewquat);
		}
	}
	
	/* this was not initialized correct always */
	if (v3d->twtype == 0)
		v3d->twtype = V3D_MANIP_TRANSLATE;
}

static bool direct_link_screen(FileData *fd, bScreen *sc)
{
	ScrArea *sa;
	ScrVert *sv;
	ScrEdge *se;
	bool wrong_id = false;
	
	link_list(fd, &(sc->vertbase));
	link_list(fd, &(sc->edgebase));
	link_list(fd, &(sc->areabase));
	sc->regionbase.first = sc->regionbase.last= NULL;
	sc->context = NULL;
	
	sc->mainwin = sc->subwinactive= 0;	/* indices */
	sc->swap = 0;

	/* edges */
	for (se = sc->edgebase.first; se; se = se->next) {
		se->v1 = newdataadr(fd, se->v1);
		se->v2 = newdataadr(fd, se->v2);
		if ((intptr_t)se->v1 > (intptr_t)se->v2) {
			sv = se->v1;
			se->v1 = se->v2;
			se->v2 = sv;
		}
		
		if (se->v1 == NULL) {
			printf("Error reading Screen %s... removing it.\n", sc->id.name+2);
			BLI_remlink(&sc->edgebase, se);
			wrong_id = true;
		}
	}
	
	/* areas */
	for (sa = sc->areabase.first; sa; sa = sa->next) {
		SpaceLink *sl;
		ARegion *ar;
		
		link_list(fd, &(sa->spacedata));
		link_list(fd, &(sa->regionbase));
		
		sa->handlers.first = sa->handlers.last = NULL;
		sa->type = NULL;	/* spacetype callbacks */
		sa->region_active_win = -1;
		
		for (ar = sa->regionbase.first; ar; ar = ar->next)
			direct_link_region(fd, ar, sa->spacetype);
		
		/* accident can happen when read/save new file with older version */
		/* 2.50: we now always add spacedata for info */
		if (sa->spacedata.first==NULL) {
			SpaceInfo *sinfo= MEM_callocN(sizeof(SpaceInfo), "spaceinfo");
			sa->spacetype= sinfo->spacetype= SPACE_INFO;
			BLI_addtail(&sa->spacedata, sinfo);
		}
		/* add local view3d too */
		else if (sa->spacetype == SPACE_VIEW3D)
			blo_do_versions_view3d_split_250(sa->spacedata.first, &sa->regionbase);
		
		for (sl = sa->spacedata.first; sl; sl = sl->next) {
			link_list(fd, &(sl->regionbase));
			
			for (ar = sl->regionbase.first; ar; ar = ar->next)
				direct_link_region(fd, ar, sl->spacetype);
			
			if (sl->spacetype == SPACE_VIEW3D) {
				View3D *v3d= (View3D*) sl;
				BGpic *bgpic;
				
				v3d->flag |= V3D_INVALID_BACKBUF;
				
				link_list(fd, &v3d->bgpicbase);
				
				/* should be do_versions except this doesnt fit well there */
				if (v3d->bgpic) {
					bgpic = newdataadr(fd, v3d->bgpic);
					BLI_addtail(&v3d->bgpicbase, bgpic);
					v3d->bgpic = NULL;
				}
			
				for (bgpic = v3d->bgpicbase.first; bgpic; bgpic = bgpic->next)
					bgpic->iuser.ok = 1;
				
				if (v3d->gpd) {
					v3d->gpd = newdataadr(fd, v3d->gpd);
					direct_link_gpencil(fd, v3d->gpd);
				}
				v3d->localvd = newdataadr(fd, v3d->localvd);
				v3d->afterdraw_transp.first = v3d->afterdraw_transp.last = NULL;
				v3d->afterdraw_xray.first = v3d->afterdraw_xray.last = NULL;
				v3d->afterdraw_xraytransp.first = v3d->afterdraw_xraytransp.last = NULL;
				v3d->properties_storage = NULL;
				v3d->defmaterial = NULL;
				
				/* render can be quite heavy, set to solid on load */
				if (v3d->drawtype == OB_RENDER)
					v3d->drawtype = OB_SOLID;
				
				blo_do_versions_view3d_split_250(v3d, &sl->regionbase);
			}
			else if (sl->spacetype == SPACE_IPO) {
				SpaceIpo *sipo = (SpaceIpo *)sl;
				
				sipo->ads = newdataadr(fd, sipo->ads);
				sipo->ghostCurves.first = sipo->ghostCurves.last = NULL;
			}
			else if (sl->spacetype == SPACE_NLA) {
				SpaceNla *snla = (SpaceNla *)sl;
				
				snla->ads = newdataadr(fd, snla->ads);
			}
			else if (sl->spacetype == SPACE_OUTLINER) {
				SpaceOops *soops = (SpaceOops *) sl;
				
				soops->treestore = newdataadr(fd, soops->treestore);
				if (soops->treestore) {
					soops->treestore->data = newdataadr(fd, soops->treestore->data);
					/* we only saved what was used */
					soops->treestore->totelem = soops->treestore->usedelem;
					soops->storeflag |= SO_TREESTORE_CLEANUP;	// at first draw
				}
				soops->tree.first = soops->tree.last= NULL;
			}
			else if (sl->spacetype == SPACE_IMAGE) {
				SpaceImage *sima = (SpaceImage *)sl;
				
				sima->cumap = newdataadr(fd, sima->cumap);
				if (sima->cumap)
					direct_link_curvemapping(fd, sima->cumap);
				
				sima->iuser.scene = NULL;
				sima->iuser.ok = 1;
				sima->scopes.waveform_1 = NULL;
				sima->scopes.waveform_2 = NULL;
				sima->scopes.waveform_3 = NULL;
				sima->scopes.vecscope = NULL;
				sima->scopes.ok = 0;
				
				/* WARNING: gpencil data is no longer stored directly in sima after 2.5 
				 * so sacrifice a few old files for now to avoid crashes with new files!
				 * committed: r28002 */
#if 0
				sima->gpd = newdataadr(fd, sima->gpd);
				if (sima->gpd)
					direct_link_gpencil(fd, sima->gpd);
#endif
			}
			else if (sl->spacetype == SPACE_NODE) {
				SpaceNode *snode = (SpaceNode *)sl;
				
				if (snode->gpd) {
					snode->gpd = newdataadr(fd, snode->gpd);
					direct_link_gpencil(fd, snode->gpd);
				}
				
				link_list(fd, &snode->treepath);
				snode->edittree = NULL;
				snode->linkdrag.first = snode->linkdrag.last = NULL;
			}
			else if (sl->spacetype == SPACE_TEXT) {
				SpaceText *st= (SpaceText *)sl;
				
				st->drawcache= NULL;
			}
			else if (sl->spacetype == SPACE_TIME) {
				SpaceTime *stime = (SpaceTime *)sl;
				stime->caches.first = stime->caches.last = NULL;
			}
			else if (sl->spacetype == SPACE_LOGIC) {
				SpaceLogic *slogic = (SpaceLogic *)sl;
				
				/* XXX: this is new stuff, which shouldn't be directly linking to gpd... */
				if (slogic->gpd) {
					slogic->gpd = newdataadr(fd, slogic->gpd);
					direct_link_gpencil(fd, slogic->gpd);
				}
			}
			else if (sl->spacetype == SPACE_SEQ) {
				SpaceSeq *sseq = (SpaceSeq *)sl;
				
				/* grease pencil data is not a direct data and can't be linked from direct_link*
				 * functions, it should be linked from lib_link* functions instead
				 *
				 * otherwise it'll lead to lost grease data on open because it'll likely be
				 * read from file after all other users of grease pencil and newdataadr would
				 * simple return NULL here (sergey)
				 */
#if 0
				if (sseq->gpd) {
					sseq->gpd = newdataadr(fd, sseq->gpd);
					direct_link_gpencil(fd, sseq->gpd);
				}
#endif
				sseq->scopes.reference_ibuf = NULL;
				sseq->scopes.zebra_ibuf = NULL;
				sseq->scopes.waveform_ibuf = NULL;
				sseq->scopes.sep_waveform_ibuf = NULL;
				sseq->scopes.vector_ibuf = NULL;
				sseq->scopes.histogram_ibuf = NULL;

			}
			else if (sl->spacetype == SPACE_BUTS) {
				SpaceButs *sbuts = (SpaceButs *)sl;
				
				sbuts->path= NULL;
				sbuts->texuser= NULL;
				sbuts->mainbo = sbuts->mainb;
				sbuts->mainbuser = sbuts->mainb;
			}
			else if (sl->spacetype == SPACE_CONSOLE) {
				SpaceConsole *sconsole = (SpaceConsole *)sl;
				ConsoleLine *cl, *cl_next;
				
				link_list(fd, &sconsole->scrollback);
				link_list(fd, &sconsole->history);
				
				//for (cl= sconsole->scrollback.first; cl; cl= cl->next)
				//	cl->line= newdataadr(fd, cl->line);
				
				/* comma expressions, (e.g. expr1, expr2, expr3) evaluate each expression,
				 * from left to right.  the right-most expression sets the result of the comma
				 * expression as a whole*/
				for (cl = sconsole->history.first; cl; cl = cl_next) {
					cl_next = cl->next;
					cl->line = newdataadr(fd, cl->line);
					if (cl->line) {
						/* the allocted length is not written, so reset here */
						cl->len_alloc = cl->len + 1;
					}
					else {
						BLI_remlink(&sconsole->history, cl);
						MEM_freeN(cl);
					}
				}
			}
			else if (sl->spacetype == SPACE_FILE) {
				SpaceFile *sfile = (SpaceFile *)sl;
				
				/* this sort of info is probably irrelevant for reloading...
				 * plus, it isn't saved to files yet!
				 */
				sfile->folders_prev = sfile->folders_next = NULL;
				sfile->files = NULL;
				sfile->layout = NULL;
				sfile->op = NULL;
				sfile->params = newdataadr(fd, sfile->params);
			}
			else if (sl->spacetype == SPACE_CLIP) {
				SpaceClip *sclip = (SpaceClip *)sl;
				
				sclip->scopes.track_search = NULL;
				sclip->scopes.track_preview = NULL;
				sclip->scopes.ok = 0;
			}
		}
		
		sa->actionzones.first = sa->actionzones.last = NULL;
		
		sa->v1 = newdataadr(fd, sa->v1);
		sa->v2 = newdataadr(fd, sa->v2);
		sa->v3 = newdataadr(fd, sa->v3);
		sa->v4 = newdataadr(fd, sa->v4);
	}
	
	return wrong_id;
}

/* ********** READ LIBRARY *************** */


static void direct_link_library(FileData *fd, Library *lib, Main *main)
{
	Main *newmain;
	
	/* check if the library was already read */
	for (newmain = fd->mainlist->first; newmain; newmain = newmain->next) {
		if (newmain->curlib) {
			if (BLI_path_cmp(newmain->curlib->filepath, lib->filepath) == 0) {
				BKE_reportf_wrap(fd->reports, RPT_WARNING,
				                 TIP_("Library '%s', '%s' had multiple instances, save and reload!"),
				                 lib->name, lib->filepath);
				
				change_idid_adr(fd->mainlist, fd, lib, newmain->curlib);
/*				change_idid_adr_fd(fd, lib, newmain->curlib); */
				
				BLI_remlink(&main->library, lib);
				MEM_freeN(lib);
				
				
				return;
			}
		}
	}
	/* make sure we have full path in lib->filepath */
	BLI_strncpy(lib->filepath, lib->name, sizeof(lib->name));
	BLI_cleanup_path(fd->relabase, lib->filepath);
	
//	printf("direct_link_library: name %s\n", lib->name);
//	printf("direct_link_library: filepath %s\n", lib->filepath);
	
	lib->packedfile = direct_link_packedfile(fd, lib->packedfile);
	
	/* new main */
	newmain= MEM_callocN(sizeof(Main), "directlink");
	BLI_addtail(fd->mainlist, newmain);
	newmain->curlib = lib;
	
	lib->parent = NULL;
}

static void lib_link_library(FileData *UNUSED(fd), Main *main)
{
	Library *lib;
	for (lib = main->library.first; lib; lib = lib->id.next) {
		lib->id.us = 1;
	}
}

/* Always call this once you have loaded new library data to set the relative paths correctly in relation to the blend file */
static void fix_relpaths_library(const char *basepath, Main *main)
{
	Library *lib;
	/* BLO_read_from_memory uses a blank filename */
	if (basepath == NULL || basepath[0] == '\0') {
		for (lib = main->library.first; lib; lib= lib->id.next) {
			/* when loading a linked lib into a file which has not been saved,
			 * there is nothing we can be relative to, so instead we need to make
			 * it absolute. This can happen when appending an object with a relative
			 * link into an unsaved blend file. See [#27405].
			 * The remap relative option will make it relative again on save - campbell */
			if (BLI_path_is_rel(lib->name)) {
				BLI_strncpy(lib->name, lib->filepath, sizeof(lib->name));
			}
		}
	}
	else {
		for (lib = main->library.first; lib; lib = lib->id.next) {
			/* Libraries store both relative and abs paths, recreate relative paths,
			 * relative to the blend file since indirectly linked libs will be relative to their direct linked library */
			if (BLI_path_is_rel(lib->name)) {  /* if this is relative to begin with? */
				BLI_strncpy(lib->name, lib->filepath, sizeof(lib->name));
				BLI_path_rel(lib->name, basepath);
			}
		}
	}
}

/* ************ READ SPEAKER ***************** */

static void lib_link_speaker(FileData *fd, Main *main)
{
	Speaker *spk;
	
	for (spk = main->speaker.first; spk; spk = spk->id.next) {
		if (spk->id.flag & LIB_NEED_LINK) {
			if (spk->adt) lib_link_animdata(fd, &spk->id, spk->adt);
			
			spk->sound= newlibadr(fd, spk->id.lib, spk->sound);
			if (spk->sound) {
				spk->sound->id.us++;
			}
			
			spk->id.flag -= LIB_NEED_LINK;
		}
	}
}

static void direct_link_speaker(FileData *fd, Speaker *spk)
{
	spk->adt = newdataadr(fd, spk->adt);
	direct_link_animdata(fd, spk->adt);

#if 0
	spk->sound = newdataadr(fd, spk->sound);
	direct_link_sound(fd, spk->sound);
#endif
}

/* ************** READ SOUND ******************* */

static void direct_link_sound(FileData *fd, bSound *sound)
{
	sound->handle = NULL;
	sound->playback_handle = NULL;
	sound->waveform = NULL;

	// versioning stuff, if there was a cache, then we enable caching:
	if (sound->cache) {
		sound->flags |= SOUND_FLAGS_CACHING;
		sound->cache = NULL;
	}

	sound->packedfile = direct_link_packedfile(fd, sound->packedfile);
	sound->newpackedfile = direct_link_packedfile(fd, sound->newpackedfile);
}

static void lib_link_sound(FileData *fd, Main *main)
{
	bSound *sound;
	
	for (sound = main->sound.first; sound; sound = sound->id.next) {
		if (sound->id.flag & LIB_NEED_LINK) {
			sound->id.flag -= LIB_NEED_LINK;
			sound->ipo = newlibadr_us(fd, sound->id.lib, sound->ipo); // XXX deprecated - old animation system
			
			sound_load(main, sound);
		}
	}
}
/* ***************** READ GROUP *************** */

static void direct_link_group(FileData *fd, Group *group)
{
	link_list(fd, &group->gobject);
}

static void lib_link_group(FileData *fd, Main *main)
{
	Group *group;
	GroupObject *go;
	int add_us;
	
	for (group = main->group.first; group; group = group->id.next) {
		if (group->id.flag & LIB_NEED_LINK) {
			group->id.flag -= LIB_NEED_LINK;
			
			add_us = 0;
			
			for (go = group->gobject.first; go; go = go->next) {
				go->ob= newlibadr(fd, group->id.lib, go->ob);
				if (go->ob) {
					go->ob->flag |= OB_FROMGROUP;
					/* if group has an object, it increments user... */
					add_us = 1;
					if (go->ob->id.us == 0)
						go->ob->id.us = 1;
				}
			}
			if (add_us) group->id.us++;
			BKE_group_object_unlink(group, NULL, NULL, NULL);	/* removes NULL entries */
		}
	}
}

/* ***************** READ MOVIECLIP *************** */

static void direct_link_movieReconstruction(FileData *fd, MovieTrackingReconstruction *reconstruction)
{
	reconstruction->cameras = newdataadr(fd, reconstruction->cameras);
}

static void direct_link_movieTracks(FileData *fd, ListBase *tracksbase)
{
	MovieTrackingTrack *track;
	
	link_list(fd, tracksbase);
	
	for (track = tracksbase->first; track; track = track->next) {
		track->markers = newdataadr(fd, track->markers);
	}
}

static void direct_link_movieclip(FileData *fd, MovieClip *clip)
{
	MovieTracking *tracking = &clip->tracking;
	MovieTrackingObject *object;

	clip->adt= newdataadr(fd, clip->adt);

	if (fd->movieclipmap) clip->cache = newmclipadr(fd, clip->cache);
	else clip->cache = NULL;

	if (fd->movieclipmap) clip->tracking.camera.intrinsics = newmclipadr(fd, clip->tracking.camera.intrinsics);
	else clip->tracking.camera.intrinsics = NULL;

	direct_link_movieTracks(fd, &tracking->tracks);
	direct_link_movieReconstruction(fd, &tracking->reconstruction);

	clip->tracking.act_track = newdataadr(fd, clip->tracking.act_track);

	clip->anim = NULL;
	clip->tracking_context = NULL;
	clip->tracking.stats = NULL;

	clip->tracking.stabilization.ok = 0;
	clip->tracking.stabilization.rot_track = newdataadr(fd, clip->tracking.stabilization.rot_track);

	clip->tracking.dopesheet.ok = 0;
	clip->tracking.dopesheet.channels.first = clip->tracking.dopesheet.channels.last = NULL;
	clip->tracking.dopesheet.coverage_segments.first = clip->tracking.dopesheet.coverage_segments.last = NULL;

	link_list(fd, &tracking->objects);
	
	for (object = tracking->objects.first; object; object = object->next) {
		direct_link_movieTracks(fd, &object->tracks);
		direct_link_movieReconstruction(fd, &object->reconstruction);
	}
}

static void lib_link_movieTracks(FileData *fd, MovieClip *clip, ListBase *tracksbase)
{
	MovieTrackingTrack *track;

	for (track = tracksbase->first; track; track = track->next) {
		track->gpd = newlibadr_us(fd, clip->id.lib, track->gpd);
	}
}

static void lib_link_movieclip(FileData *fd, Main *main)
{
	MovieClip *clip;
	
	for (clip = main->movieclip.first; clip; clip = clip->id.next) {
		if (clip->id.flag & LIB_NEED_LINK) {
			MovieTracking *tracking = &clip->tracking;
			MovieTrackingObject *object;

			if (clip->adt)
				lib_link_animdata(fd, &clip->id, clip->adt);
			
			clip->gpd = newlibadr_us(fd, clip->id.lib, clip->gpd);
			
			lib_link_movieTracks(fd, clip, &tracking->tracks);

			for (object = tracking->objects.first; object; object = object->next) {
				lib_link_movieTracks(fd, clip, &object->tracks);
			}

			clip->id.flag -= LIB_NEED_LINK;
		}
	}
}

/* ***************** READ MOVIECLIP *************** */

static void direct_link_mask(FileData *fd, Mask *mask)
{
	MaskLayer *masklay;

	mask->adt = newdataadr(fd, mask->adt);

	link_list(fd, &mask->masklayers);

	for (masklay = mask->masklayers.first; masklay; masklay = masklay->next) {
		MaskSpline *spline;
		MaskLayerShape *masklay_shape;

		link_list(fd, &masklay->splines);

		for (spline = masklay->splines.first; spline; spline = spline->next) {
			int i;

			spline->points = newdataadr(fd, spline->points);

			for (i = 0; i < spline->tot_point; i++) {
				MaskSplinePoint *point = &spline->points[i];

				if (point->tot_uw)
					point->uw = newdataadr(fd, point->uw);
			}
		}

		link_list(fd, &masklay->splines_shapes);

		for (masklay_shape = masklay->splines_shapes.first; masklay_shape; masklay_shape = masklay_shape->next) {
			masklay_shape->data = newdataadr(fd, masklay_shape->data);

			if (masklay_shape->tot_vert) {
				if (fd->flags & FD_FLAGS_SWITCH_ENDIAN) {
					BLI_endian_switch_float_array(masklay_shape->data,
					                              masklay_shape->tot_vert * sizeof(float) * MASK_OBJECT_SHAPE_ELEM_SIZE);

				}
			}
		}

		masklay->act_spline = newdataadr(fd, masklay->act_spline);
		masklay->act_point = newdataadr(fd, masklay->act_point);
	}
}

static void lib_link_mask_parent(FileData *fd, Mask *mask, MaskParent *parent)
{
	parent->id = newlibadr_us(fd, mask->id.lib, parent->id);
}

static void lib_link_mask(FileData *fd, Main *main)
{
	Mask *mask;

	mask = main->mask.first;
	while (mask) {
		if (mask->id.flag & LIB_NEED_LINK) {
			MaskLayer *masklay;

			if (mask->adt)
				lib_link_animdata(fd, &mask->id, mask->adt);

			for (masklay = mask->masklayers.first; masklay; masklay = masklay->next) {
				MaskSpline *spline;

				spline = masklay->splines.first;
				while (spline) {
					int i;

					for (i = 0; i < spline->tot_point; i++) {
						MaskSplinePoint *point = &spline->points[i];

						lib_link_mask_parent(fd, mask, &point->parent);
					}

					lib_link_mask_parent(fd, mask, &spline->parent);

					spline = spline->next;
				}
			}

			mask->id.flag -= LIB_NEED_LINK;
		}
		mask = mask->id.next;
	}
}

/* ************ READ LINE STYLE ***************** */

static void lib_link_linestyle(FileData *fd, Main *main)
{
	FreestyleLineStyle *linestyle;
	LineStyleModifier *m;

	linestyle = main->linestyle.first;
	while (linestyle) {
		if (linestyle->id.flag & LIB_NEED_LINK) {
			linestyle->id.flag -= LIB_NEED_LINK;

			if (linestyle->id.properties)
				IDP_LibLinkProperty(linestyle->id.properties, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
			if (linestyle->adt)
				lib_link_animdata(fd, &linestyle->id, linestyle->adt);
			for (m = linestyle->color_modifiers.first; m; m = m->next) {
				switch (m->type) {
				case LS_MODIFIER_DISTANCE_FROM_OBJECT:
					{
						LineStyleColorModifier_DistanceFromObject *cm = (LineStyleColorModifier_DistanceFromObject *)m;
						cm->target = newlibadr(fd, linestyle->id.lib, cm->target);
					}
					break;
				}
			}
			for (m = linestyle->alpha_modifiers.first; m; m = m->next) {
				switch (m->type) {
				case LS_MODIFIER_DISTANCE_FROM_OBJECT:
					{
						LineStyleAlphaModifier_DistanceFromObject *am = (LineStyleAlphaModifier_DistanceFromObject *)m;
						am->target = newlibadr(fd, linestyle->id.lib, am->target);
					}
					break;
				}
			}
			for (m = linestyle->thickness_modifiers.first; m; m = m->next) {
				switch (m->type) {
				case LS_MODIFIER_DISTANCE_FROM_OBJECT:
					{
						LineStyleThicknessModifier_DistanceFromObject *tm = (LineStyleThicknessModifier_DistanceFromObject *)m;
						tm->target = newlibadr(fd, linestyle->id.lib, tm->target);
					}
					break;
				}
			}
		}
		linestyle = linestyle->id.next;
	}
}

static void direct_link_linestyle_color_modifier(FileData *fd, LineStyleModifier *modifier)
{
	switch (modifier->type) {
	case LS_MODIFIER_ALONG_STROKE:
		{
			LineStyleColorModifier_AlongStroke *m = (LineStyleColorModifier_AlongStroke *)modifier;
			m->color_ramp = newdataadr(fd, m->color_ramp);
		}
		break;
	case LS_MODIFIER_DISTANCE_FROM_CAMERA:
		{
			LineStyleColorModifier_DistanceFromCamera *m = (LineStyleColorModifier_DistanceFromCamera *)modifier;
			m->color_ramp = newdataadr(fd, m->color_ramp);
		}
		break;
	case LS_MODIFIER_DISTANCE_FROM_OBJECT:
		{
			LineStyleColorModifier_DistanceFromObject *m = (LineStyleColorModifier_DistanceFromObject *)modifier;
			m->color_ramp = newdataadr(fd, m->color_ramp);
		}
		break;
	case LS_MODIFIER_MATERIAL:
		{
			LineStyleColorModifier_Material *m = (LineStyleColorModifier_Material *)modifier;
			m->color_ramp = newdataadr(fd, m->color_ramp);
		}
		break;
	}
}

static void direct_link_linestyle_alpha_modifier(FileData *fd, LineStyleModifier *modifier)
{
	switch (modifier->type) {
	case LS_MODIFIER_ALONG_STROKE:
		{
			LineStyleAlphaModifier_AlongStroke *m = (LineStyleAlphaModifier_AlongStroke *)modifier;
			m->curve = newdataadr(fd, m->curve);
			direct_link_curvemapping(fd, m->curve);
		}
		break;
	case LS_MODIFIER_DISTANCE_FROM_CAMERA:
		{
			LineStyleAlphaModifier_DistanceFromCamera *m = (LineStyleAlphaModifier_DistanceFromCamera *)modifier;
			m->curve = newdataadr(fd, m->curve);
			direct_link_curvemapping(fd, m->curve);
		}
		break;
	case LS_MODIFIER_DISTANCE_FROM_OBJECT:
		{
			LineStyleAlphaModifier_DistanceFromObject *m = (LineStyleAlphaModifier_DistanceFromObject *)modifier;
			m->curve = newdataadr(fd, m->curve);
			direct_link_curvemapping(fd, m->curve);
		}
		break;
	case LS_MODIFIER_MATERIAL:
		{
			LineStyleAlphaModifier_Material *m = (LineStyleAlphaModifier_Material *)modifier;
			m->curve = newdataadr(fd, m->curve);
			direct_link_curvemapping(fd, m->curve);
		}
		break;
	}
}

static void direct_link_linestyle_thickness_modifier(FileData *fd, LineStyleModifier *modifier)
{
	switch (modifier->type) {
	case LS_MODIFIER_ALONG_STROKE:
		{
			LineStyleThicknessModifier_AlongStroke *m = (LineStyleThicknessModifier_AlongStroke *)modifier;
			m->curve = newdataadr(fd, m->curve);
			direct_link_curvemapping(fd, m->curve);
		}
		break;
	case LS_MODIFIER_DISTANCE_FROM_CAMERA:
		{
			LineStyleThicknessModifier_DistanceFromCamera *m = (LineStyleThicknessModifier_DistanceFromCamera *)modifier;
			m->curve = newdataadr(fd, m->curve);
			direct_link_curvemapping(fd, m->curve);
		}
		break;
	case LS_MODIFIER_DISTANCE_FROM_OBJECT:
		{
			LineStyleThicknessModifier_DistanceFromObject *m = (LineStyleThicknessModifier_DistanceFromObject *)modifier;
			m->curve = newdataadr(fd, m->curve);
			direct_link_curvemapping(fd, m->curve);
		}
		break;
	case LS_MODIFIER_MATERIAL:
		{
			LineStyleThicknessModifier_Material *m = (LineStyleThicknessModifier_Material *)modifier;
			m->curve = newdataadr(fd, m->curve);
			direct_link_curvemapping(fd, m->curve);
		}
		break;
	}
}

static void direct_link_linestyle_geometry_modifier(FileData *UNUSED(fd), LineStyleModifier *UNUSED(modifier))
{
}

static void direct_link_linestyle(FileData *fd, FreestyleLineStyle *linestyle)
{
	LineStyleModifier *modifier;

	linestyle->adt= newdataadr(fd, linestyle->adt);
	direct_link_animdata(fd, linestyle->adt);
	link_list(fd, &linestyle->color_modifiers);
	for(modifier = linestyle->color_modifiers.first; modifier; modifier = modifier->next)
		direct_link_linestyle_color_modifier(fd, modifier);
	link_list(fd, &linestyle->alpha_modifiers);
	for(modifier = linestyle->alpha_modifiers.first; modifier; modifier = modifier->next)
		direct_link_linestyle_alpha_modifier(fd, modifier);
	link_list(fd, &linestyle->thickness_modifiers);
	for(modifier = linestyle->thickness_modifiers.first; modifier; modifier = modifier->next)
		direct_link_linestyle_thickness_modifier(fd, modifier);
	link_list(fd, &linestyle->geometry_modifiers);
	for(modifier = linestyle->geometry_modifiers.first; modifier; modifier = modifier->next)
		direct_link_linestyle_geometry_modifier(fd, modifier);
}

/* ************** GENERAL & MAIN ******************** */


static const char *dataname(short id_code)
{
	switch (id_code) {
		case ID_OB: return "Data from OB";
		case ID_ME: return "Data from ME";
		case ID_IP: return "Data from IP";
		case ID_SCE: return "Data from SCE";
		case ID_MA: return "Data from MA";
		case ID_TE: return "Data from TE";
		case ID_CU: return "Data from CU";
		case ID_GR: return "Data from GR";
		case ID_AR: return "Data from AR";
		case ID_AC: return "Data from AC";
		case ID_LI: return "Data from LI";
		case ID_MB: return "Data from MB";
		case ID_IM: return "Data from IM";
		case ID_LT: return "Data from LT";
		case ID_LA: return "Data from LA";
		case ID_CA: return "Data from CA";
		case ID_KE: return "Data from KE";
		case ID_WO: return "Data from WO";
		case ID_SCR: return "Data from SCR";
		case ID_VF: return "Data from VF";
		case ID_TXT	: return "Data from TXT";
		case ID_SPK: return "Data from SPK";
		case ID_SO: return "Data from SO";
		case ID_NT: return "Data from NT";
		case ID_BR: return "Data from BR";
		case ID_PA: return "Data from PA";
		case ID_GD: return "Data from GD";
		case ID_MC: return "Data from MC";
		case ID_LS: return "Data from LS";
	}
	return "Data from Lib Block";
	
}

static BHead *read_data_into_oldnewmap(FileData *fd, BHead *bhead, const char *allocname)
{
	bhead = blo_nextbhead(fd, bhead);
	
	while (bhead && bhead->code==DATA) {
		void *data;
#if 0
		/* XXX DUMB DEBUGGING OPTION TO GIVE NAMES for guarded malloc errors */
		short *sp = fd->filesdna->structs[bhead->SDNAnr];
		char *tmp = malloc(100);
		allocname = fd->filesdna->types[ sp[0] ];
		strcpy(tmp, allocname);
		data = read_struct(fd, bhead, tmp);
#else
		data = read_struct(fd, bhead, allocname);
#endif
		
		if (data) {
			oldnewmap_insert(fd->datamap, bhead->old, data, 0);
		}
		
		bhead = blo_nextbhead(fd, bhead);
	}
	
	return bhead;
}

static BHead *read_libblock(FileData *fd, Main *main, BHead *bhead, int flag, ID **id_r)
{
	/* this routine reads a libblock and its direct data. Use link functions
	 * to connect it all
	 */
	ID *id;
	ListBase *lb;
	const char *allocname;
	bool wrong_id = false;
	
	/* read libblock */
	id = read_struct(fd, bhead, "lib block");
	if (id_r)
		*id_r = id;
	if (!id)
		return blo_nextbhead(fd, bhead);
	
	oldnewmap_insert(fd->libmap, bhead->old, id, bhead->code);	/* for ID_ID check */
	
	/* do after read_struct, for dna reconstruct */
	if (bhead->code == ID_ID) {
		lb = which_libbase(main, GS(id->name));
	}
	else {
		lb = which_libbase(main, bhead->code);
	}
	
	BLI_addtail(lb, id);
	
	/* clear first 8 bits */
	id->flag = (id->flag & 0xFF00) | flag | LIB_NEED_LINK;
	id->lib = main->curlib;
	if (id->flag & LIB_FAKEUSER) id->us= 1;
	else id->us = 0;
	id->icon_id = 0;
	id->flag &= ~(LIB_ID_RECALC|LIB_ID_RECALC_DATA);
	
	/* this case cannot be direct_linked: it's just the ID part */
	if (bhead->code == ID_ID) {
		return blo_nextbhead(fd, bhead);
	}
	
	/* need a name for the mallocN, just for debugging and sane prints on leaks */
	allocname = dataname(GS(id->name));
	
	/* read all data into fd->datamap */
	bhead = read_data_into_oldnewmap(fd, bhead, allocname);
	
	/* init pointers direct data */
	direct_link_id(fd, id);
	
	switch (GS(id->name)) {
		case ID_WM:
			direct_link_windowmanager(fd, (wmWindowManager *)id);
			break;
		case ID_SCR:
			wrong_id = direct_link_screen(fd, (bScreen *)id);
			break;
		case ID_SCE:
			direct_link_scene(fd, (Scene *)id);
			break;
		case ID_OB:
			direct_link_object(fd, (Object *)id);
			break;
		case ID_ME:
			direct_link_mesh(fd, (Mesh *)id);
			break;
		case ID_CU:
			direct_link_curve(fd, (Curve *)id);
			break;
		case ID_MB:
			direct_link_mball(fd, (MetaBall *)id);
			break;
		case ID_MA:
			direct_link_material(fd, (Material *)id);
			break;
		case ID_TE:
			direct_link_texture(fd, (Tex *)id);
			break;
		case ID_IM:
			direct_link_image(fd, (Image *)id);
			break;
		case ID_LA:
			direct_link_lamp(fd, (Lamp *)id);
			break;
		case ID_VF:
			direct_link_vfont(fd, (VFont *)id);
			break;
		case ID_TXT:
			direct_link_text(fd, (Text *)id);
			break;
		case ID_IP:
			direct_link_ipo(fd, (Ipo *)id);
			break;
		case ID_KE:
			direct_link_key(fd, (Key *)id);
			break;
		case ID_LT:
			direct_link_latt(fd, (Lattice *)id);
			break;
		case ID_WO:
			direct_link_world(fd, (World *)id);
			break;
		case ID_LI:
			direct_link_library(fd, (Library *)id, main);
			break;
		case ID_CA:
			direct_link_camera(fd, (Camera *)id);
			break;
		case ID_SPK:
			direct_link_speaker(fd, (Speaker *)id);
			break;
		case ID_SO:
			direct_link_sound(fd, (bSound *)id);
			break;
		case ID_GR:
			direct_link_group(fd, (Group *)id);
			break;
		case ID_AR:
			direct_link_armature(fd, (bArmature*)id);
			break;
		case ID_AC:
			direct_link_action(fd, (bAction*)id);
			break;
		case ID_NT:
			direct_link_nodetree(fd, (bNodeTree*)id);
			break;
		case ID_BR:
			direct_link_brush(fd, (Brush*)id);
			break;
		case ID_PA:
			direct_link_particlesettings(fd, (ParticleSettings*)id);
			break;
		case ID_SCRIPT:
			direct_link_script(fd, (Script*)id);
			break;
		case ID_GD:
			direct_link_gpencil(fd, (bGPdata *)id);
			break;
		case ID_MC:
			direct_link_movieclip(fd, (MovieClip *)id);
			break;
		case ID_MSK:
			direct_link_mask(fd, (Mask *)id);
			break;
		case ID_LS:
			direct_link_linestyle(fd, (FreestyleLineStyle *)id);
			break;
	}
	
	oldnewmap_free_unused(fd->datamap);
	oldnewmap_clear(fd->datamap);
	
	if (wrong_id) {
		BKE_libblock_free(lb, id);
	}
	
	return (bhead);
}

/* note, this has to be kept for reading older files... */
/* also version info is written here */
static BHead *read_global(BlendFileData *bfd, FileData *fd, BHead *bhead)
{
	FileGlobal *fg = read_struct(fd, bhead, "Global");
	
	/* copy to bfd handle */
	bfd->main->subversionfile = fg->subversion;
	bfd->main->minversionfile = fg->minversion;
	bfd->main->minsubversionfile = fg->minsubversion;
	bfd->main->revision = fg->revision;
	
	bfd->winpos = fg->winpos;
	bfd->fileflags = fg->fileflags;
	bfd->displaymode = fg->displaymode;
	bfd->globalf = fg->globalf;
	BLI_strncpy(bfd->filename, fg->filename, sizeof(bfd->filename));
	
	/* error in 2.65 and older: main->name was not set if you save from startup (not after loading file) */
	if (bfd->filename[0] == 0) {
		if (fd->fileversion < 265 || (fd->fileversion == 265 && fg->subversion < 1))
			if ((G.fileflags & G_FILE_RECOVER)==0)
				BLI_strncpy(bfd->filename, bfd->main->name, sizeof(bfd->filename));
		
		/* early 2.50 version patch - filename not in FileGlobal struct at all */
		if (fd->fileversion <= 250)
			BLI_strncpy(bfd->filename, bfd->main->name, sizeof(bfd->filename));
	}
	
	if (G.fileflags & G_FILE_RECOVER)
		BLI_strncpy(fd->relabase, fg->filename, sizeof(fd->relabase));
	
	bfd->curscreen = fg->curscreen;
	bfd->curscene = fg->curscene;
	
	MEM_freeN(fg);
	
	fd->globalf = bfd->globalf;
	fd->fileflags = bfd->fileflags;
	
	return blo_nextbhead(fd, bhead);
}

/* note, this has to be kept for reading older files... */
static void link_global(FileData *fd, BlendFileData *bfd)
{
	bfd->curscreen = newlibadr(fd, NULL, bfd->curscreen);
	bfd->curscene = newlibadr(fd, NULL, bfd->curscene);
	// this happens in files older than 2.35
	if (bfd->curscene == NULL) {
		if (bfd->curscreen) bfd->curscene = bfd->curscreen->scene;
	}
}

void convert_tface_mt(FileData *fd, Main *main)
{
	Main *gmain;
	
	/* this is a delayed do_version (so it can create new materials) */
	if (main->versionfile < 259 || (main->versionfile == 259 && main->subversionfile < 3)) {
		//XXX hack, material.c uses G.main all over the place, instead of main
		// temporarily set G.main to the current main
		gmain = G.main;
		G.main = main;
		
		if (!(do_version_tface(main, 1))) {
			BKE_report(fd->reports, RPT_WARNING, "Texface conversion problem (see error in console)");
		}
		
		//XXX hack, material.c uses G.main allover the place, instead of main
		G.main = gmain;
	}
}

static void do_versions_nodetree_image_default_alpha_output(bNodeTree *ntree)
{
	bNode *node;
	bNodeSocket *sock;
	
	for (node = ntree->nodes.first; node; node = node->next) {
		if (ELEM(node->type, CMP_NODE_IMAGE, CMP_NODE_R_LAYERS)) {
			/* default Image output value should have 0 alpha */
			sock = node->outputs.first;
			((bNodeSocketValueRGBA *)(sock->default_value))->value[3] = 0.0f;
		}
	}
}

static void do_versions_nodetree_convert_angle(bNodeTree *ntree)
{
	bNode *node;
	for (node=ntree->nodes.first; node; node=node->next) {
		if (node->type == CMP_NODE_ROTATE) {
			/* Convert degrees to radians. */
			bNodeSocket *sock = ((bNodeSocket*)node->inputs.first)->next;
			((bNodeSocketValueFloat*)sock->default_value)->value = DEG2RADF(((bNodeSocketValueFloat*)sock->default_value)->value);
		}
		else if (node->type == CMP_NODE_DBLUR) {
			/* Convert degrees to radians. */
			NodeDBlurData *ndbd= node->storage;
			ndbd->angle = DEG2RADF(ndbd->angle);
			ndbd->spin = DEG2RADF(ndbd->spin);
		}
		else if (node->type == CMP_NODE_DEFOCUS) {
			/* Convert degrees to radians. */
			NodeDefocus *nqd = node->storage;
			/* XXX DNA char to float conversion seems to map the char value into the [0.0f, 1.0f] range... */
			nqd->rotation = DEG2RADF(nqd->rotation * 255.0f);
		}
		else if (node->type == CMP_NODE_CHROMA_MATTE) {
			/* Convert degrees to radians. */
			NodeChroma *ndc = node->storage;
			ndc->t1 = DEG2RADF(ndc->t1);
			ndc->t2 = DEG2RADF(ndc->t2);
		}
		else if (node->type == CMP_NODE_GLARE) {
			/* Convert degrees to radians. */
			NodeGlare *ndg = node->storage;
			/* XXX DNA char to float conversion seems to map the char value into the [0.0f, 1.0f] range... */
			ndg->angle_ofs = DEG2RADF(ndg->angle_ofs * 255.0f);
		}
		/* XXX TexMapping struct is used by other nodes too (at least node_composite_mapValue),
		 *     but not the rot part...
		 */
		else if (node->type == SH_NODE_MAPPING) {
			/* Convert degrees to radians. */
			TexMapping *tmap = node->storage;
			tmap->rot[0] = DEG2RADF(tmap->rot[0]);
			tmap->rot[1] = DEG2RADF(tmap->rot[1]);
			tmap->rot[2] = DEG2RADF(tmap->rot[2]);
		}
	}
}

static void do_versions_image_settings_2_60(Scene *sce)
{
	/* note: rd->subimtype is moved into individual settings now and no longer
	 * exists */
	RenderData *rd = &sce->r;
	ImageFormatData *imf = &sce->r.im_format;

	/* we know no data loss happens here, the old values were in char range */
	imf->imtype =   (char)rd->imtype;
	imf->planes =   (char)rd->planes;
	imf->compress = (char)rd->quality;
	imf->quality =  (char)rd->quality;

	/* default, was stored in multiple places, may override later */
	imf->depth = R_IMF_CHAN_DEPTH_8;

	/* openexr */
	imf->exr_codec = rd->quality & 7; /* strange but true! 0-4 are valid values, OPENEXR_COMPRESS */

	switch (imf->imtype) {
	case R_IMF_IMTYPE_OPENEXR:
		imf->depth =  (rd->subimtype & R_OPENEXR_HALF) ? R_IMF_CHAN_DEPTH_16 : R_IMF_CHAN_DEPTH_32;
		if (rd->subimtype & R_PREVIEW_JPG) {
			imf->flag |= R_IMF_FLAG_PREVIEW_JPG;
		}
		if (rd->subimtype & R_OPENEXR_ZBUF) {
			imf->flag |= R_IMF_FLAG_ZBUF;
		}
		break;
	case R_IMF_IMTYPE_TIFF:
		if (rd->subimtype & R_TIFF_16BIT) {
			imf->depth= R_IMF_CHAN_DEPTH_16;
		}
		break;
	case R_IMF_IMTYPE_JP2:
		if (rd->subimtype & R_JPEG2K_16BIT) {
			imf->depth= R_IMF_CHAN_DEPTH_16;
		}
		else if (rd->subimtype & R_JPEG2K_12BIT) {
			imf->depth= R_IMF_CHAN_DEPTH_12;
		}

		if (rd->subimtype & R_JPEG2K_YCC) {
			imf->jp2_flag |= R_IMF_JP2_FLAG_YCC;
		}
		if (rd->subimtype & R_JPEG2K_CINE_PRESET) {
			imf->jp2_flag |= R_IMF_JP2_FLAG_CINE_PRESET;
		}
		if (rd->subimtype & R_JPEG2K_CINE_48FPS) {
			imf->jp2_flag |= R_IMF_JP2_FLAG_CINE_48;
		}
		break;
	case R_IMF_IMTYPE_CINEON:
	case R_IMF_IMTYPE_DPX:
		if (rd->subimtype & R_CINEON_LOG) {
			imf->cineon_flag |= R_IMF_CINEON_FLAG_LOG;
		}
		break;
	}

}

/* socket use flags were only temporary before */
static void do_versions_nodetree_socket_use_flags_2_62(bNodeTree *ntree)
{
	bNode *node;
	bNodeSocket *sock;
	bNodeLink *link;
	
	for (node = ntree->nodes.first; node; node = node->next) {
		for (sock = node->inputs.first; sock; sock = sock->next)
			sock->flag &= ~SOCK_IN_USE;
		for (sock = node->outputs.first; sock; sock = sock->next)
			sock->flag &= ~SOCK_IN_USE;
	}
	for (sock = ntree->inputs.first; sock; sock = sock->next)
		sock->flag &= ~SOCK_IN_USE;
	for (sock = ntree->outputs.first; sock; sock = sock->next)
		sock->flag &= ~SOCK_IN_USE;
	
	for (link = ntree->links.first; link; link = link->next) {
		link->fromsock->flag |= SOCK_IN_USE;
		link->tosock->flag |= SOCK_IN_USE;
	}
}

static void do_versions_nodetree_multi_file_output_format_2_62_1(Scene *sce, bNodeTree *ntree)
{
	bNode *node;
	
	for (node = ntree->nodes.first; node; node = node->next) {
		if (node->type == CMP_NODE_OUTPUT_FILE) {
			/* previous CMP_NODE_OUTPUT_FILE nodes get converted to multi-file outputs */
			NodeImageFile *old_data = node->storage;
			NodeImageMultiFile *nimf= MEM_callocN(sizeof(NodeImageMultiFile), "node image multi file");
			bNodeSocket *old_image = BLI_findlink(&node->inputs, 0);
			bNodeSocket *old_z = BLI_findlink(&node->inputs, 1);
			bNodeSocket *sock;
			char filename[FILE_MAXFILE];
			
			/* ugly, need to remove the old inputs list to avoid bad pointer checks when adding new sockets.
			 * sock->storage is expected to contain path info in ntreeCompositOutputFileAddSocket.
			 */
			node->inputs.first = node->inputs.last = NULL;
			
			node->storage = nimf;
			
			/* looks like storage data can be messed up somehow, stupid check here */
			if (old_data) {
				char basepath[FILE_MAXDIR];

				/* split off filename from the old path, to be used as socket sub-path */
				BLI_split_dirfile(old_data->name, basepath, filename, sizeof(basepath), sizeof(filename));
				
				BLI_strncpy(nimf->base_path, basepath, sizeof(nimf->base_path));
				nimf->format = old_data->im_format;
			}
			else {
				BLI_strncpy(filename, old_image->name, sizeof(filename));
			}
			
			/* if z buffer is saved, change the image type to multilayer exr.
			 * XXX this is slightly messy, Z buffer was ignored before for anything but EXR and IRIS ...
			 * i'm just assuming here that IRIZ means IRIS with z buffer ...
			 */
			if (old_data && ELEM(old_data->im_format.imtype, R_IMF_IMTYPE_IRIZ, R_IMF_IMTYPE_OPENEXR)) {
				char sockpath[FILE_MAX];
				
				nimf->format.imtype = R_IMF_IMTYPE_MULTILAYER;
				
				BLI_snprintf(sockpath, sizeof(sockpath), "%s_Image", filename);
				sock = ntreeCompositOutputFileAddSocket(ntree, node, sockpath, &nimf->format);
				/* XXX later do_versions copies path from socket name, need to set this explicitely */
				BLI_strncpy(sock->name, sockpath, sizeof(sock->name));
				if (old_image->link) {
					old_image->link->tosock = sock;
					sock->link = old_image->link;
				}
				
				BLI_snprintf(sockpath, sizeof(sockpath), "%s_Z", filename);
				sock = ntreeCompositOutputFileAddSocket(ntree, node, sockpath, &nimf->format);
				/* XXX later do_versions copies path from socket name, need to set this explicitely */
				BLI_strncpy(sock->name, sockpath, sizeof(sock->name));
				if (old_z->link) {
					old_z->link->tosock = sock;
					sock->link = old_z->link;
				}
			}
			else {
				sock = ntreeCompositOutputFileAddSocket(ntree, node, filename, &nimf->format);
				/* XXX later do_versions copies path from socket name, need to set this explicitely */
				BLI_strncpy(sock->name, filename, sizeof(sock->name));
				if (old_image->link) {
					old_image->link->tosock = sock;
					sock->link = old_image->link;
				}
			}
			
			nodeRemoveSocket(ntree, node, old_image);
			nodeRemoveSocket(ntree, node, old_z);
			if (old_data)
				MEM_freeN(old_data);
		}
		else if (node->type==CMP_NODE_OUTPUT_MULTI_FILE__DEPRECATED) {
			NodeImageMultiFile *nimf = node->storage;
			bNodeSocket *sock;
			
			/* CMP_NODE_OUTPUT_MULTI_FILE has been redeclared as CMP_NODE_OUTPUT_FILE */
			node->type = CMP_NODE_OUTPUT_FILE;
			
			/* initialize the node-wide image format from render data, if available */
			if (sce)
				nimf->format = sce->r.im_format;
			
			/* transfer render format toggle to node format toggle */
			for (sock = node->inputs.first; sock; sock = sock->next) {
				NodeImageMultiFileSocket *simf = sock->storage;
				simf->use_node_format = simf->use_render_format;
			}
			
			/* we do have preview now */
			node->flag |= NODE_PREVIEW;
		}
	}
}

/* blue and red are swapped pre 2.62.1, be sane (red == red) now! */
static void do_versions_mesh_mloopcol_swap_2_62_1(Mesh *me)
{
	CustomDataLayer *layer;
	MLoopCol *mloopcol;
	int a;
	int i;
	
	for (a = 0; a < me->ldata.totlayer; a++) {
		layer = &me->ldata.layers[a];
		
		if (layer->type == CD_MLOOPCOL) {
			mloopcol = (MLoopCol *)layer->data;
			for (i = 0; i < me->totloop; i++, mloopcol++) {
				SWAP(char, mloopcol->r, mloopcol->b);
			}
		}
	}
}

static void do_versions_nodetree_multi_file_output_path_2_63_1(bNodeTree *ntree)
{
	bNode *node;
	
	for (node=ntree->nodes.first; node; node=node->next) {
		if (node->type == CMP_NODE_OUTPUT_FILE) {
			bNodeSocket *sock;
			for (sock = node->inputs.first; sock; sock = sock->next) {
				NodeImageMultiFileSocket *input = sock->storage;
				/* input file path is stored in dedicated struct now instead socket name */
				BLI_strncpy(input->path, sock->name, sizeof(input->path));
			}
		}
	}
}

static void do_versions_nodetree_file_output_layers_2_64_5(bNodeTree *ntree)
{
	bNode *node;
	
	for (node=ntree->nodes.first; node; node=node->next) {
		if (node->type == CMP_NODE_OUTPUT_FILE) {
			bNodeSocket *sock;
			for (sock = node->inputs.first; sock; sock = sock->next) {
				NodeImageMultiFileSocket *input = sock->storage;
				
				/* multilayer names are stored as separate strings now,
				 * used the path string before, so copy it over.
				 */
				BLI_strncpy(input->layer, input->path, sizeof(input->layer));
				
				/* paths/layer names also have to be unique now, initial check */
				ntreeCompositOutputFileUniquePath(&node->inputs, sock, input->path, '_');
				ntreeCompositOutputFileUniqueLayer(&node->inputs, sock, input->layer, '_');
			}
		}
	}
}

static void do_versions_nodetree_image_layer_2_64_5(bNodeTree *ntree)
{
	bNode *node;
	
	for (node = ntree->nodes.first; node; node = node->next) {
		if (node->type == CMP_NODE_IMAGE) {
			bNodeSocket *sock;
			for (sock = node->outputs.first; sock; sock = sock->next) {
				NodeImageLayer *output = MEM_callocN(sizeof(NodeImageLayer), "node image layer");
				
				/* take pass index both from current storage ptr (actually an int) */
				output->pass_index = GET_INT_FROM_POINTER(sock->storage);
				
				/* replace socket data pointer */
				sock->storage = output;
			}
		}
	}
}

static void do_versions_nodetree_frame_2_64_6(bNodeTree *ntree)
{
	bNode *node;
	
	for (node=ntree->nodes.first; node; node=node->next) {
		if (node->type==NODE_FRAME) {
			/* initialize frame node storage data */
			if (node->storage == NULL) {
				NodeFrame *data = (NodeFrame *)MEM_callocN(sizeof(NodeFrame), "frame node storage");
				node->storage = data;
				
				/* copy current flags */
				data->flag = node->custom1;
				
				data->label_size = 20;
			}
		}
		
		/* initialize custom node color */
		node->color[0] = node->color[1] = node->color[2] = 0.608f;	/* default theme color */
	}
}

static void do_version_logic_264(ListBase *regionbase)
{
	ARegion *ar;
	
	/* view settings for logic changed */
	for (ar = regionbase->first; ar; ar = ar->next) {
		if (ar->regiontype == RGN_TYPE_WINDOW) {
			if (ar->v2d.keeptot == 0) {
				ar->v2d.maxzoom = 1.5f;
				
				ar->v2d.keepzoom = V2D_KEEPZOOM | V2D_LIMITZOOM | V2D_KEEPASPECT;
				ar->v2d.keeptot = V2D_KEEPTOT_BOUNDS;
				ar->v2d.align = V2D_ALIGN_NO_POS_Y | V2D_ALIGN_NO_NEG_X;
				ar->v2d.keepofs = V2D_KEEPOFS_Y;
			}
		}
	}
	

}

static void do_versions_affine_tracker_track(MovieTrackingTrack *track)
{
	int i;

	for (i = 0; i < track->markersnr; i++) {
		MovieTrackingMarker *marker = &track->markers[i];

		if (is_zero_v2(marker->pattern_corners[0]) && is_zero_v2(marker->pattern_corners[1]) &&
		    is_zero_v2(marker->pattern_corners[2]) && is_zero_v2(marker->pattern_corners[3]))
			{
				marker->pattern_corners[0][0] = track->pat_min[0];
				marker->pattern_corners[0][1] = track->pat_min[1];

				marker->pattern_corners[1][0] = track->pat_max[0];
				marker->pattern_corners[1][1] = track->pat_min[1];

				marker->pattern_corners[2][0] = track->pat_max[0];
				marker->pattern_corners[2][1] = track->pat_max[1];

				marker->pattern_corners[3][0] = track->pat_min[0];
				marker->pattern_corners[3][1] = track->pat_max[1];
			}

		if (is_zero_v2(marker->search_min) && is_zero_v2(marker->search_max)) {
			copy_v2_v2(marker->search_min, track->search_min);
			copy_v2_v2(marker->search_max, track->search_max);
		}
	}
}


static const char *node_get_static_idname(int type, int treetype)
{
	/* use static type info header to map static int type to identifier string */
	#define DefNode(Category, ID, DefFunc, EnumName, StructName, UIName, UIDesc) \
		case ID: return #Category #StructName;
	
	/* XXX hack, group types share a single static integer identifier, but are registered as separate types */
	if (type == NODE_GROUP) {
		switch (treetype) {
		case NTREE_COMPOSIT: return "CompositorNodeGroup";
		case NTREE_SHADER: return "ShaderNodeGroup";
		case NTREE_TEXTURE: return "TextureNodeGroup";
		}
	}
	else {
		switch (type) {
		#include "NOD_static_types.h"
		}
	}
	return "";
}

static const char *node_socket_get_static_idname(bNodeSocket *sock)
{
	switch (sock->type) {
	case SOCK_FLOAT: {
		bNodeSocketValueFloat *dval = sock->default_value;
		return nodeStaticSocketType(SOCK_FLOAT, dval->subtype);
	}
	case SOCK_INT: {
		bNodeSocketValueInt *dval = sock->default_value;
		return nodeStaticSocketType(SOCK_INT, dval->subtype);
	}
	case SOCK_BOOLEAN: {
		return nodeStaticSocketType(SOCK_BOOLEAN, PROP_NONE);
	}
	case SOCK_VECTOR: {
		bNodeSocketValueVector *dval = sock->default_value;
		return nodeStaticSocketType(SOCK_VECTOR, dval->subtype);
	}
	case SOCK_RGBA: {
		return nodeStaticSocketType(SOCK_RGBA, PROP_NONE);
	}
	case SOCK_STRING: {
		bNodeSocketValueString *dval = sock->default_value;
		return nodeStaticSocketType(SOCK_STRING, dval->subtype);
	}
	case SOCK_SHADER: {
		return nodeStaticSocketType(SOCK_SHADER, PROP_NONE);
	}
	}
	return "";
}

static void do_versions_nodetree_customnodes(bNodeTree *ntree, int UNUSED(is_group))
{
	/* initialize node tree type idname */
	{
		bNode *node;
		bNodeSocket *sock;
		
		ntree->typeinfo = NULL;
		
		/* tree type idname */
		switch (ntree->type) {
		case NTREE_COMPOSIT:
			strcpy(ntree->idname, "CompositorNodeTree");
			break;
		case NTREE_SHADER:
			strcpy(ntree->idname, "ShaderNodeTree");
			break;
		case NTREE_TEXTURE:
			strcpy(ntree->idname, "TextureNodeTree");
			break;
		}
		
		/* node type idname */
		for (node=ntree->nodes.first; node; node=node->next) {
			BLI_strncpy(node->idname, node_get_static_idname(node->type, ntree->type), sizeof(node->idname));
			
			/* existing old nodes have been initialized already */
			node->flag |= NODE_INIT;
			
			/* sockets idname */
			for (sock = node->inputs.first; sock; sock = sock->next)
				BLI_strncpy(sock->idname, node_socket_get_static_idname(sock), sizeof(sock->idname));
			for (sock = node->outputs.first; sock; sock = sock->next)
				BLI_strncpy(sock->idname, node_socket_get_static_idname(sock), sizeof(sock->idname));
		}
		/* tree sockets idname */
		for (sock = ntree->inputs.first; sock; sock = sock->next)
			BLI_strncpy(sock->idname, node_socket_get_static_idname(sock), sizeof(sock->idname));
		for (sock = ntree->outputs.first; sock; sock = sock->next)
			BLI_strncpy(sock->idname, node_socket_get_static_idname(sock), sizeof(sock->idname));
	}
	
	/* initialize socket in_out values */
	{
		bNode *node;
		bNodeSocket *sock;
		
		for (node=ntree->nodes.first; node; node=node->next) {
			for (sock = node->inputs.first; sock; sock = sock->next)
				sock->in_out = SOCK_IN;
			for (sock = node->outputs.first; sock; sock = sock->next)
				sock->in_out = SOCK_OUT;
		}
		for (sock = ntree->inputs.first; sock; sock = sock->next)
			sock->in_out = SOCK_IN;
		for (sock = ntree->outputs.first; sock; sock = sock->next)
			sock->in_out = SOCK_OUT;
	}
	
	/* initialize socket identifier strings */
	{
		bNode *node;
		bNodeSocket *sock;
		
		for (node=ntree->nodes.first; node; node=node->next) {
			for (sock = node->inputs.first; sock; sock = sock->next) {
				BLI_strncpy(sock->identifier, sock->name, sizeof(sock->identifier));
				BLI_uniquename(&node->inputs, sock, "socket", '.', offsetof(bNodeSocket, identifier), sizeof(sock->identifier));
			}
			for (sock = node->outputs.first; sock; sock = sock->next) {
				BLI_strncpy(sock->identifier, sock->name, sizeof(sock->identifier));
				BLI_uniquename(&node->outputs, sock, "socket", '.', offsetof(bNodeSocket, identifier), sizeof(sock->identifier));
			}
		}
		for (sock = ntree->inputs.first; sock; sock = sock->next) {
			BLI_strncpy(sock->identifier, sock->name, sizeof(sock->identifier));
			BLI_uniquename(&ntree->inputs, sock, "socket", '.', offsetof(bNodeSocket, identifier), sizeof(sock->identifier));
		}
		for (sock = ntree->outputs.first; sock; sock = sock->next) {
			BLI_strncpy(sock->identifier, sock->name, sizeof(sock->identifier));
			BLI_uniquename(&ntree->outputs, sock, "socket", '.', offsetof(bNodeSocket, identifier), sizeof(sock->identifier));
		}
	}
}

/* initialize userdef with non-UI dependency stuff */
/* other initializers (such as theme color defaults) go to resources.c */
static void do_versions_userdef(FileData *UNUSED(fd), BlendFileData *bfd)
{
	Main *bmain = bfd->main;
	UserDef *user = bfd->user;
	
	if (user == NULL) return;
	
	if (MAIN_VERSION_OLDER(bmain, 266, 4)) {
		bTheme *btheme;
		
		/* themes for Node and Sequence editor were not using grid color, but back. we copy this over then */
		for (btheme = user->themes.first; btheme; btheme = btheme->next) {
			copy_v4_v4_char(btheme->tnode.grid, btheme->tnode.back);
			copy_v4_v4_char(btheme->tseq.grid, btheme->tseq.back);
		}
	}
}

static void do_versions(FileData *fd, Library *lib, Main *main)
{
	/* WATCH IT!!!: pointers from libdata have not been converted */
	
	if (G.debug & G_DEBUG)
		printf("read file %s\n  Version %d sub %d svn r%d\n", fd->relabase, main->versionfile, main->subversionfile, main->revision);
	
	blo_do_versions_pre250(fd, lib, main);
	blo_do_versions_250(fd, lib, main);
	
	if (main->versionfile < 260) {
		{
			/* set default alpha value of Image outputs in image and render layer nodes to 0 */
			Scene *sce;
			bNodeTree *ntree;
			
			for (sce = main->scene.first; sce; sce = sce->id.next) {
				/* there are files with invalid audio_channels value, the real cause
				 * is unknown, but we fix it here anyway to avoid crashes */
				if (sce->r.ffcodecdata.audio_channels == 0)
					sce->r.ffcodecdata.audio_channels = 2;
				
				if (sce->nodetree)
					do_versions_nodetree_image_default_alpha_output(sce->nodetree);
			}

			for (ntree = main->nodetree.first; ntree; ntree = ntree->id.next)
				do_versions_nodetree_image_default_alpha_output(ntree);
		}
		
		{
			/* support old particle dupliobject rotation settings */
			ParticleSettings *part;
			
			for (part=main->particle.first; part; part=part->id.next) {
				if (ELEM(part->ren_as, PART_DRAW_OB, PART_DRAW_GR)) {
					part->draw |= PART_DRAW_ROTATE_OB;
					
					if (part->rotmode == 0)
						part->rotmode = PART_ROT_VEL;
				}
			}
		}
	}
	
	if (main->versionfile < 260 || (main->versionfile == 260 && main->subversionfile < 1)) {
		Object *ob;
		
		for (ob = main->object.first; ob; ob = ob->id.next) {
			ob->collision_boundtype= ob->boundtype;
		}
		
		{
			Camera *cam;
			for (cam = main->camera.first; cam; cam = cam->id.next) {
				if (cam->sensor_x < 0.01f)
					cam->sensor_x = DEFAULT_SENSOR_WIDTH;
				
				if (cam->sensor_y < 0.01f)
					cam->sensor_y = DEFAULT_SENSOR_HEIGHT;
			}
		}
	}
	
	if (main->versionfile < 260 || (main->versionfile == 260 && main->subversionfile < 2)) {
		FOREACH_NODETREE(main, ntree, id) {
			if (ntree->type == NTREE_SHADER) {
				bNode *node;
				for (node = ntree->nodes.first; node; node = node->next) {
					if (node->type == SH_NODE_MAPPING) {
						TexMapping *tex_mapping;
						
						tex_mapping= node->storage;
						tex_mapping->projx= PROJ_X;
						tex_mapping->projy= PROJ_Y;
						tex_mapping->projz= PROJ_Z;
					}
				}
			}
		} FOREACH_NODETREE_END
	}

	if (main->versionfile < 260 || (main->versionfile == 260 && main->subversionfile < 4)) {
		{
			/* Convert node angles to radians! */
			Scene *sce;
			Material *mat;
			bNodeTree *ntree;
			
			for (sce = main->scene.first; sce; sce = sce->id.next) {
				if (sce->nodetree)
					do_versions_nodetree_convert_angle(sce->nodetree);
			}
			
			for (mat = main->mat.first; mat; mat = mat->id.next) {
				if (mat->nodetree)
					do_versions_nodetree_convert_angle(mat->nodetree);
			}
			
			for (ntree = main->nodetree.first; ntree; ntree = ntree->id.next)
				do_versions_nodetree_convert_angle(ntree);
		}
		
		{
			/* Tomato compatibility code. */
			bScreen *sc;
			MovieClip *clip;
			
			for (sc = main->screen.first; sc; sc = sc->id.next) {
				ScrArea *sa;
				for (sa = sc->areabase.first; sa; sa = sa->next) {
					SpaceLink *sl;
					for (sl = sa->spacedata.first; sl; sl = sl->next) {
						if (sl->spacetype == SPACE_VIEW3D) {
							View3D *v3d= (View3D *)sl;
							if (v3d->bundle_size == 0.0f) {
								v3d->bundle_size = 0.2f;
								v3d->flag2 |= V3D_SHOW_RECONSTRUCTION;
							}
							
							if (v3d->bundle_drawtype == 0)
								v3d->bundle_drawtype = OB_PLAINAXES;
						}
						else if (sl->spacetype == SPACE_CLIP) {
							SpaceClip *sclip = (SpaceClip *)sl;
							if (sclip->scopes.track_preview_height == 0)
								sclip->scopes.track_preview_height = 120;
						}
					}
				}
			}
			
			for (clip = main->movieclip.first; clip; clip = clip->id.next) {
				MovieTrackingTrack *track;
				
				if (clip->aspx < 1.0f) {
					clip->aspx = 1.0f;
					clip->aspy = 1.0f;
				}
				
				clip->proxy.build_tc_flag = IMB_TC_RECORD_RUN |
				                            IMB_TC_FREE_RUN |
				                            IMB_TC_INTERPOLATED_REC_DATE_FREE_RUN;
				
				if (clip->proxy.build_size_flag == 0)
					clip->proxy.build_size_flag = IMB_PROXY_25;
				
				if (clip->proxy.quality == 0)
					clip->proxy.quality = 90;
				
				if (clip->tracking.camera.pixel_aspect < 0.01f)
					clip->tracking.camera.pixel_aspect = 1.0f;
					
				track = clip->tracking.tracks.first;
				while (track) {
					if (track->minimum_correlation == 0.0f)
						track->minimum_correlation = 0.75f;

					track = track->next;
				}
			}
		}
	}
	
	if (main->versionfile < 260 || (main->versionfile == 260 && main->subversionfile < 6)) {
		Scene *sce;
		MovieClip *clip;
		bScreen *sc;
		
		for (sce = main->scene.first; sce; sce = sce->id.next) {
			do_versions_image_settings_2_60(sce);
		}
		
		for (clip= main->movieclip.first; clip; clip= clip->id.next) {
			MovieTrackingSettings *settings= &clip->tracking.settings;

			if (settings->default_pattern_size == 0.0f) {
				settings->default_motion_model = TRACK_MOTION_MODEL_TRANSLATION;
				settings->default_minimum_correlation = 0.75;
				settings->default_pattern_size = 11;
				settings->default_search_size = 51;
			}
		}
		
		for (sc = main->screen.first; sc; sc = sc->id.next) {
			ScrArea *sa;
			for (sa = sc->areabase.first; sa; sa = sa->next) {
				SpaceLink *sl;
				for (sl = sa->spacedata.first; sl; sl = sl->next) {
					if (sl->spacetype == SPACE_VIEW3D) {
						View3D *v3d = (View3D *)sl;
						v3d->flag2 &= ~V3D_RENDER_SHADOW;
					}
				}
			}
		}
		
		{
			Object *ob;
			for (ob = main->object.first; ob; ob = ob->id.next) {
				/* convert delta addition into delta scale */
				int i;
				for (i= 0; i < 3; i++) {
					if ( (ob->dsize[i] == 0.0f) || /* simple case, user never touched dsize */
					     (ob->size[i]  == 0.0f))   /* cant scale the dsize to give a non zero result, so fallback to 1.0f */
					{
						ob->dscale[i] = 1.0f;
					}
					else {
						ob->dscale[i] = (ob->size[i] + ob->dsize[i]) / ob->size[i];
					}
				}
			}
		}
	}
	/* sigh, this dscale vs dsize version patching was not done right, fix for fix,
	 * this intentionally checks an exact subversion, also note this was never in a release,
	 * at some point this could be removed. */
	else if (main->versionfile == 260 && main->subversionfile == 6) {
		Object *ob;
		for (ob = main->object.first; ob; ob = ob->id.next) {
			if (is_zero_v3(ob->dscale)) {
				fill_vn_fl(ob->dscale, 3, 1.0f);
			}
		}
	}
	
	if (main->versionfile < 260 || (main->versionfile == 260 && main->subversionfile < 8)) {
		Brush *brush;
		
		for (brush = main->brush.first; brush; brush = brush->id.next) {
			if (brush->sculpt_tool == SCULPT_TOOL_ROTATE)
				brush->alpha= 1.0f;
		}
	}

	if (main->versionfile < 261 || (main->versionfile == 261 && main->subversionfile < 1)) {
		{
			/* update use flags for node sockets (was only temporary before) */
			Scene *sce;
			Material *mat;
			Tex *tex;
			Lamp *lamp;
			World *world;
			bNodeTree *ntree;
			
			for (sce = main->scene.first; sce; sce = sce->id.next) {
				if (sce->nodetree)
					do_versions_nodetree_socket_use_flags_2_62(sce->nodetree);
			}
			
			for (mat = main->mat.first; mat; mat = mat->id.next) {
				if (mat->nodetree)
					do_versions_nodetree_socket_use_flags_2_62(mat->nodetree);
			}
			
			for (tex = main->tex.first; tex; tex = tex->id.next) {
				if (tex->nodetree)
					do_versions_nodetree_socket_use_flags_2_62(tex->nodetree);
			}
			
			for (lamp = main->lamp.first; lamp; lamp = lamp->id.next) {
				if (lamp->nodetree)
					do_versions_nodetree_socket_use_flags_2_62(lamp->nodetree);
			}
			
			for (world = main->world.first; world; world = world->id.next) {
				if (world->nodetree)
					do_versions_nodetree_socket_use_flags_2_62(world->nodetree);
			}
			
			for (ntree = main->nodetree.first; ntree; ntree = ntree->id.next) {
				do_versions_nodetree_socket_use_flags_2_62(ntree);
			}
		}
		{
			/* Initialize BGE exit key to esc key */
			Scene *scene;
			for (scene = main->scene.first; scene; scene = scene->id.next) {
				if (!scene->gm.exitkey)
					scene->gm.exitkey = 218; // Blender key code for ESC
			}
		}
		{
			MovieClip *clip;
			Object *ob;
			
			for (clip = main->movieclip.first; clip; clip = clip->id.next) {
				MovieTracking *tracking = &clip->tracking;
				MovieTrackingObject *tracking_object = tracking->objects.first;
				
				clip->proxy.build_tc_flag |= IMB_TC_RECORD_RUN_NO_GAPS;
				
				if (!tracking->settings.object_distance)
					tracking->settings.object_distance = 1.0f;
				
				if (tracking->objects.first == NULL)
					BKE_tracking_object_add(tracking, "Camera");
				
				while (tracking_object) {
					if (!tracking_object->scale)
						tracking_object->scale = 1.0f;
					
					tracking_object = tracking_object->next;
				}
			}
			
			for (ob = main->object.first; ob; ob = ob->id.next) {
				bConstraint *con;
				for (con = ob->constraints.first; con; con = con->next) {
					bConstraintTypeInfo *cti = BKE_constraint_get_typeinfo(con);
					
					if (!cti)
						continue;
					
					if (cti->type == CONSTRAINT_TYPE_OBJECTSOLVER) {
						bObjectSolverConstraint *data = (bObjectSolverConstraint *)con->data;
						
						if (data->invmat[3][3] == 0.0f)
							unit_m4(data->invmat);
					}
				}
			}
		}
		{
		/* Warn the user if he is using ["Text"] properties for Font objects */
			Object *ob;
			bProperty *prop;
			
			for (ob= main->object.first; ob; ob= ob->id.next) {
				if (ob->type == OB_FONT) {
					prop = BKE_bproperty_object_get(ob, "Text");
					if (prop) {
						BKE_reportf_wrap(fd->reports, RPT_WARNING,
						                 TIP_("Game property name conflict in object '%s': text objects reserve the "
						                      "['Text'] game property to change their content through logic bricks"),
						                 ob->id.name + 2);
					}
				}
			}
		}
	}
	
	if (main->versionfile < 261 || (main->versionfile == 261 && main->subversionfile < 2)) {
		{
			/* convert Camera Actuator values to defines */
			Object *ob;
			bActuator *act;
			for (ob = main->object.first; ob; ob= ob->id.next) {
				for (act= ob->actuators.first; act; act= act->next) {
					if (act->type == ACT_CAMERA) {
						bCameraActuator *ba= act->data;
					
						if (ba->axis==(float) 'x') ba->axis=OB_POSX;
						else if (ba->axis==(float)'y') ba->axis=OB_POSY;
						/* don't do an if/else to avoid imediate subversion bump*/
//						ba->axis=((ba->axis == (float)'x') ? OB_POSX_X : OB_POSY);
					}
				}
			}
		}
		
		{
			/* convert deprecated sculpt_paint_unified_* fields to
			 * UnifiedPaintSettings */
			Scene *scene;
			for (scene= main->scene.first; scene; scene= scene->id.next) {
				ToolSettings *ts= scene->toolsettings;
				UnifiedPaintSettings *ups= &ts->unified_paint_settings;
				ups->size= ts->sculpt_paint_unified_size;
				ups->unprojected_radius= ts->sculpt_paint_unified_unprojected_radius;
				ups->alpha= ts->sculpt_paint_unified_alpha;
				ups->flag= ts->sculpt_paint_settings;
			}
		}
	}

	if (main->versionfile < 261 || (main->versionfile == 261 && main->subversionfile < 3)) {
		{
			/* convert extended ascii to utf-8 for text editor */
			Text *text;
			for (text= main->text.first; text; text= text->id.next)
				if (!(text->flags & TXT_ISEXT)) {
					TextLine *tl;
					
					for (tl= text->lines.first; tl; tl= tl->next) {
						int added= txt_extended_ascii_as_utf8(&tl->line);
						tl->len+= added;
						
						/* reset cursor position if line was changed */
						if (added && tl == text->curl)
							text->curc = 0;
					}
				}
		}
		{
			/* set new dynamic paint values */
			Object *ob;
			for (ob = main->object.first; ob; ob = ob->id.next) {
				ModifierData *md;
				for (md= ob->modifiers.first; md; md= md->next) {
					if (md->type == eModifierType_DynamicPaint) {
						DynamicPaintModifierData *pmd = (DynamicPaintModifierData *)md;
						if (pmd->canvas) {
							DynamicPaintSurface *surface = pmd->canvas->surfaces.first;
							for (; surface; surface=surface->next) {
								surface->color_dry_threshold = 1.0f;
								surface->influence_scale = 1.0f;
								surface->radius_scale = 1.0f;
								surface->flags |= MOD_DPAINT_USE_DRYING;
							}
						}
					}
				}
			}
		}
	}
	
	if (main->versionfile < 262) {
		Object *ob;
		for (ob=main->object.first; ob; ob= ob->id.next) {
			ModifierData *md;
			
			for (md=ob->modifiers.first; md; md=md->next) {
				if (md->type==eModifierType_Cloth) {
					ClothModifierData *clmd = (ClothModifierData*) md;
					if (clmd->sim_parms)
						clmd->sim_parms->vel_damping = 1.0f;
				}
			}
		}
	}

	if (main->versionfile < 263) {
		/* set fluidsim rate. the version patch for this in 2.62 was wrong, so
		 * try to correct it, if rate is 0.0 that's likely not intentional */
		Object *ob;

		for (ob = main->object.first; ob; ob = ob->id.next) {
			ModifierData *md;
			for (md = ob->modifiers.first; md; md = md->next) {
				if (md->type == eModifierType_Fluidsim) {
					FluidsimModifierData *fmd = (FluidsimModifierData *)md;
					if (fmd->fss->animRate == 0.0f)
						fmd->fss->animRate = 1.0f;
				}
			}
		}
	}

	if (main->versionfile < 262 || (main->versionfile == 262 && main->subversionfile < 1)) {
		/* update use flags for node sockets (was only temporary before) */
		Scene *sce;
		bNodeTree *ntree;
		
		for (sce=main->scene.first; sce; sce=sce->id.next) {
			if (sce->nodetree)
				do_versions_nodetree_multi_file_output_format_2_62_1(sce, sce->nodetree);
		}
		
		/* XXX can't associate with scene for group nodes, image format will stay uninitialized */
		for (ntree=main->nodetree.first; ntree; ntree=ntree->id.next)
			do_versions_nodetree_multi_file_output_format_2_62_1(NULL, ntree);
	}

	/* only swap for pre-release bmesh merge which had MLoopCol red/blue swap */
	if (main->versionfile == 262 && main->subversionfile == 1) {
		{
			Mesh *me;
			for (me = main->mesh.first; me; me = me->id.next) {
				do_versions_mesh_mloopcol_swap_2_62_1(me);
			}
		}
	}

	if (main->versionfile < 262 || (main->versionfile == 262 && main->subversionfile < 2)) {
		/* Set new idname of keyingsets from their now "label-only" name. */
		Scene *scene;
		for (scene = main->scene.first; scene; scene = scene->id.next) {
			KeyingSet *ks;
			for (ks = scene->keyingsets.first; ks; ks = ks->next) {
				if (!ks->idname[0])
					BLI_strncpy(ks->idname, ks->name, sizeof(ks->idname));
			}
		}
	}
	
	if (main->versionfile < 262 || (main->versionfile == 262 && main->subversionfile < 3)) {
		Object *ob;
		ModifierData *md;
		
		for (ob = main->object.first; ob; ob = ob->id.next) {
			for (md = ob->modifiers.first; md; md = md->next) {
				if (md->type == eModifierType_Lattice) {
					LatticeModifierData *lmd = (LatticeModifierData *)md;
					lmd->strength = 1.0f;
				}
			}
		}
	}

	if (main->versionfile < 262 || (main->versionfile == 262 && main->subversionfile < 4)) {
		/* Read Viscosity presets from older files */
		Object *ob;

		for (ob = main->object.first; ob; ob = ob->id.next) {
			ModifierData *md;
			for (md = ob->modifiers.first; md; md = md->next) {
				if (md->type == eModifierType_Fluidsim) {
					FluidsimModifierData *fmd = (FluidsimModifierData *)md;
					if (fmd->fss->viscosityMode == 3) {
						fmd->fss->viscosityValue = 5.0;
						fmd->fss->viscosityExponent = 5;
					}
					else if (fmd->fss->viscosityMode == 4) {
						fmd->fss->viscosityValue = 2.0;
						fmd->fss->viscosityExponent = 3;
					}
				}
			}
		}
	}



	if (main->versionfile < 263) {
		/* Default for old files is to save particle rotations to pointcache */
		ParticleSettings *part;
		for (part = main->particle.first; part; part = part->id.next) {
			part->flag |= PART_ROTATIONS;
		}
	}

	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 1)) {
		/* file output node paths are now stored in the file info struct instead socket name */
		Scene *sce;
		bNodeTree *ntree;
		
		for (sce = main->scene.first; sce; sce=sce->id.next)
			if (sce->nodetree)
				do_versions_nodetree_multi_file_output_path_2_63_1(sce->nodetree);
		for (ntree = main->nodetree.first; ntree; ntree=ntree->id.next)
			do_versions_nodetree_multi_file_output_path_2_63_1(ntree);
	}

	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 3)) {
		Scene *scene;
		Brush *brush;
		
		/* For weight paint, each brush now gets its own weight;
		 * unified paint settings also have weight. Update unified
		 * paint settings and brushes with a default weight value. */
		
		for (scene = main->scene.first; scene; scene = scene->id.next) {
			ToolSettings *ts = scene->toolsettings;
			if (ts) {
				ts->unified_paint_settings.weight = ts->vgroup_weight;
				ts->unified_paint_settings.flag |= UNIFIED_PAINT_WEIGHT;
			}
		}
		
		for (brush = main->brush.first; brush; brush = brush->id.next) {
			brush->weight = 0.5;
		}
	}
	
	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 2)) {
		bScreen *sc;
		
		for (sc = main->screen.first; sc; sc = sc->id.next) {
			ScrArea *sa;
			for (sa = sc->areabase.first; sa; sa = sa->next) {
				SpaceLink *sl;
				
				for (sl = sa->spacedata.first; sl; sl = sl->next) {
					if (sl->spacetype == SPACE_CLIP) {
						SpaceClip *sclip = (SpaceClip *)sl;
						ARegion *ar;
						int hide = FALSE;
						
						for (ar = sa->regionbase.first; ar; ar = ar->next) {
							if (ar->regiontype == RGN_TYPE_PREVIEW) {
								if (ar->alignment != RGN_ALIGN_NONE) {
									ar->flag |= RGN_FLAG_HIDDEN;
									ar->v2d.flag &= ~V2D_IS_INITIALISED;
									ar->alignment = RGN_ALIGN_NONE;
									
									hide = TRUE;
								}
							}
						}
						
						if (hide) {
							sclip->view = SC_VIEW_CLIP;
						}
					}
				}
			}
		}
	}
	
	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 4))
	{
		Lamp *la;
		Camera *cam;
		Curve *cu;
		
		for (la = main->lamp.first; la; la = la->id.next) {
			if (la->shadow_frustum_size == 0.0f)
				la->shadow_frustum_size= 10.0f;
		}
		
		for (cam = main->camera.first; cam; cam = cam->id.next) {
			if (cam->flag & CAM_PANORAMA) {
				cam->type = CAM_PANO;
				cam->flag &= ~CAM_PANORAMA;
			}
		}
		
		for (cu = main->curve.first; cu; cu = cu->id.next) {
			if (cu->bevfac2 == 0.0f) {
				cu->bevfac1 = 0.0f;
				cu->bevfac2 = 1.0f;
			}
		}
	}
	
	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 5))
	{
		{
			/* file output node paths are now stored in the file info struct instead socket name */
			Scene *sce;
			bNodeTree *ntree;
			
			for (sce = main->scene.first; sce; sce=sce->id.next) {
				if (sce->nodetree) {
					do_versions_nodetree_file_output_layers_2_64_5(sce->nodetree);
					do_versions_nodetree_image_layer_2_64_5(sce->nodetree);
				}
			}
			for (ntree = main->nodetree.first; ntree; ntree=ntree->id.next) {
				do_versions_nodetree_file_output_layers_2_64_5(ntree);
				do_versions_nodetree_image_layer_2_64_5(ntree);
			}
		}
	}

	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 6))
	{
		/* update use flags for node sockets (was only temporary before) */
		Scene *sce;
		Material *mat;
		Tex *tex;
		Lamp *lamp;
		World *world;
		bNodeTree *ntree;
		
		for (sce=main->scene.first; sce; sce=sce->id.next)
			if (sce->nodetree)
				do_versions_nodetree_frame_2_64_6(sce->nodetree);
		
		for (mat=main->mat.first; mat; mat=mat->id.next)
			if (mat->nodetree)
				do_versions_nodetree_frame_2_64_6(mat->nodetree);
		
		for (tex=main->tex.first; tex; tex=tex->id.next)
			if (tex->nodetree)
				do_versions_nodetree_frame_2_64_6(tex->nodetree);
		
		for (lamp=main->lamp.first; lamp; lamp=lamp->id.next)
			if (lamp->nodetree)
				do_versions_nodetree_frame_2_64_6(lamp->nodetree);
		
		for (world=main->world.first; world; world=world->id.next)
			if (world->nodetree)
				do_versions_nodetree_frame_2_64_6(world->nodetree);
		
		for (ntree=main->nodetree.first; ntree; ntree=ntree->id.next)
			do_versions_nodetree_frame_2_64_6(ntree);
	}

	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 7))
	{
		Object *ob;

		for (ob = main->object.first; ob; ob = ob->id.next) {
			ModifierData *md;
			for (md = ob->modifiers.first; md; md = md->next) {
				if (md->type == eModifierType_Smoke) {
					SmokeModifierData *smd = (SmokeModifierData *)md;
					if ((smd->type & MOD_SMOKE_TYPE_DOMAIN) && smd->domain) {
						int maxres = max_iii(smd->domain->res[0], smd->domain->res[1], smd->domain->res[2]);
						smd->domain->scale = smd->domain->dx * maxres;
						smd->domain->dx = 1.0f / smd->domain->scale;
					}
				}
			}
		}
	}


	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 8))
	{
		/* set new deactivation values for game settings */
		Scene *sce;

		for (sce = main->scene.first; sce; sce = sce->id.next) {
			/* Game Settings */
			sce->gm.lineardeactthreshold = 0.8f;
			sce->gm.angulardeactthreshold = 1.0f;
			sce->gm.deactivationtime = 2.0f;
		}
	}

	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 9)) {
		FOREACH_NODETREE(main, ntree, id) {
			if (ntree->type == NTREE_SHADER) {
				bNode *node;
				for (node = ntree->nodes.first; node; node = node->next) {
					if (ELEM(node->type, SH_NODE_TEX_IMAGE, SH_NODE_TEX_ENVIRONMENT)) {
						NodeTexImage *tex = node->storage;
						
						tex->iuser.frames= 1;
						tex->iuser.sfra= 1;
						tex->iuser.fie_ima= 2;
						tex->iuser.ok= 1;
					}
				}
			}
		} FOREACH_NODETREE_END
	}

	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 10)) {
		{
			Scene *scene;
			// composite redesign
			for (scene=main->scene.first; scene; scene=scene->id.next) {
				if (scene->nodetree) {
					if (scene->nodetree->chunksize == 0) {
						scene->nodetree->chunksize = 256;
					}
				}
			}
			
			FOREACH_NODETREE(main, ntree, id) {
				if (ntree->type == NTREE_COMPOSIT) {
					bNode *node;
					for (node = ntree->nodes.first; node; node = node->next) {
						if (node->type == CMP_NODE_DEFOCUS) {
							NodeDefocus *data = node->storage;
							if (data->maxblur == 0.0f) {
								data->maxblur = 16.0f;
							}
						}
					}
				}
			} FOREACH_NODETREE_END
		}

		{
			bScreen *sc;

			for (sc = main->screen.first; sc; sc = sc->id.next) {
				ScrArea *sa;

				for (sa = sc->areabase.first; sa; sa = sa->next) {
					SpaceLink *sl;

					for (sl = sa->spacedata.first; sl; sl = sl->next) {
						if (sl->spacetype == SPACE_CLIP) {
							SpaceClip *sclip = (SpaceClip *)sl;

							if (sclip->around == 0) {
								sclip->around = V3D_CENTROID;
							}
						}
					}
				}
			}
		}

		{
			MovieClip *clip;

			for (clip = main->movieclip.first; clip; clip = clip->id.next) {
				clip->start_frame = 1;
			}
		}
	}

	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 11)) {
		MovieClip *clip;

		for (clip = main->movieclip.first; clip; clip = clip->id.next) {
			MovieTrackingTrack *track;

			track = clip->tracking.tracks.first;
			while (track) {
				do_versions_affine_tracker_track(track);

				track = track->next;
			}
		}
	}

	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 12)) {
		Material *ma;

		for (ma = main->mat.first; ma; ma = ma->id.next)
			if (ma->strand_widthfade == 2.0f)
				ma->strand_widthfade = 0.0f;
	}

	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 13)) {
		FOREACH_NODETREE(main, ntree, id) {
			if (ntree->type == NTREE_COMPOSIT) {
				bNode *node;
				for (node = ntree->nodes.first; node; node = node->next) {
					if (node->type == CMP_NODE_DILATEERODE) {
						if (node->storage == NULL) {
							NodeDilateErode *data = MEM_callocN(sizeof(NodeDilateErode), __func__);
							data->falloff = PROP_SMOOTH;
							node->storage = data;
						}
					}
				}
			}
		} FOREACH_NODETREE_END
	}

	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 14)) {
		ParticleSettings *part;
		
		FOREACH_NODETREE(main, ntree, id) {
			if (ntree->type == NTREE_COMPOSIT) {
				bNode *node;
				for (node = ntree->nodes.first; node; node = node->next) {
					if (node->type == CMP_NODE_KEYING) {
						NodeKeyingData *data = node->storage;
						
						if (data->despill_balance == 0.0f) {
							data->despill_balance = 0.5f;
						}
					}
				}
			}
		} FOREACH_NODETREE_END
		
		/* keep compatibility for dupliobject particle size */
		for (part=main->particle.first; part; part=part->id.next)
			if (ELEM(part->ren_as, PART_DRAW_OB, PART_DRAW_GR))
				if ((part->draw & PART_DRAW_ROTATE_OB) == 0)
					part->draw |= PART_DRAW_NO_SCALE_OB;
	}

	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 17)) {
		FOREACH_NODETREE(main, ntree, id) {
			if (ntree->type == NTREE_COMPOSIT) {
				bNode *node;
				for (node = ntree->nodes.first; node; node = node->next) {
					if (node->type == CMP_NODE_MASK) {
						if (node->storage == NULL) {
							NodeMask *data = MEM_callocN(sizeof(NodeMask), __func__);
							/* move settings into own struct */
							data->size_x = (int)node->custom3;
							data->size_y = (int)node->custom4;
							node->custom3 = 0.5f; /* default shutter */
							node->storage = data;
						}
					}
				}
			}
		} FOREACH_NODETREE_END
	}
	
	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 18)) {
		Scene *scene;

		for (scene = main->scene.first; scene; scene = scene->id.next) {
			if (scene->ed) {
				Sequence *seq;

				SEQ_BEGIN (scene->ed, seq)
				{
					Strip *strip = seq->strip;

					if (strip && strip->color_balance) {
						SequenceModifierData *smd;
						ColorBalanceModifierData *cbmd;

						smd = BKE_sequence_modifier_new(seq, NULL, seqModifierType_ColorBalance);
						cbmd = (ColorBalanceModifierData *) smd;

						cbmd->color_balance = *strip->color_balance;

						/* multiplication with color balance used is handled differently,
						 * so we need to move multiplication to modifier so files would be
						 * compatible
						 */
						cbmd->color_multiply = seq->mul;
						seq->mul = 1.0f;

						MEM_freeN(strip->color_balance);
						strip->color_balance = NULL;
					}
				}
				SEQ_END
			}
		}
	}

	/* color management pipeline changes compatibility code */
	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 19)) {
		Scene *scene;
		Image *ima;
		int colormanagement_disabled = FALSE;

		/* make scenes which are not using color management have got None as display device,
		 * so they wouldn't perform linear-to-sRGB conversion on display
		 */
		for (scene = main->scene.first; scene; scene = scene->id.next) {
			if ((scene->r.color_mgt_flag & R_COLOR_MANAGEMENT) == 0) {
				ColorManagedDisplaySettings *display_settings = &scene->display_settings;

				if (display_settings->display_device[0] == 0) {
					BKE_scene_disable_color_management(scene);

				}

				colormanagement_disabled = TRUE;
			}
		}

		for (ima = main->image.first; ima; ima = ima->id.next) {
			if (ima->source == IMA_SRC_VIEWER) {
				ima->flag |= IMA_VIEW_AS_RENDER;
			}
			else if (colormanagement_disabled) {
				/* if colormanagement not used, set image's color space to raw, so no sRGB->linear conversion
				 * would happen on display and render
				 * there's no clear way to check whether color management is enabled or not in render engine
				 * so set all images to raw if there's at least one scene with color management disabled
				 * this would still behave incorrect in cases when color management was used for only some
				 * of scenes, but such a setup is crazy anyway and think it's fair enough to break compatibility
				 * in that cases
				 */

				BLI_strncpy(ima->colorspace_settings.name, "Raw", sizeof(ima->colorspace_settings.name));
			}
		}
	}

	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 20)) {
		Key *key;
		for (key = main->key.first; key; key = key->id.next) {
			do_versions_key_uidgen(key);
		}
	}

	/* remove texco */
	if (main->versionfile < 263 || (main->versionfile == 263 && main->subversionfile < 21)) {
		Material *ma;
		for (ma = main->mat.first; ma; ma = ma->id.next) {
			int a;
			for (a = 0; a < MAX_MTEX; a++) {
				if (ma->mtex[a]) {
					if (ma->mtex[a]->texco == TEXCO_STICKY_) {
						ma->mtex[a]->texco = TEXCO_UV;
					}
				}
			}
		}

		{
			Mesh *me;
			for (me = main->mesh.first; me; me = me->id.next) {
				CustomData_update_typemap(&me->vdata);
				CustomData_free_layers(&me->vdata, CD_MSTICKY, me->totvert);
			}
		}
	}

	/* correction for files saved in blender version when BKE_pose_copy_data
	 * didn't copy animation visualization, which lead to deadlocks on motion
	 * path calculation for proxied armatures, see [#32742]
	 */
	if (main->versionfile < 264) {
		Object *ob;

		for (ob = main->object.first; ob; ob = ob->id.next) {
			if (ob->pose) {
				if (ob->pose->avs.path_step == 0) {
					animviz_settings_init(&ob->pose->avs);
				}
			}
		}
	}

	if (main->versionfile < 264 || (main->versionfile == 264 && main->subversionfile < 1)) {
		FOREACH_NODETREE(main, ntree, id) {
			if (ntree->type == NTREE_SHADER) {
				bNode *node;
				for (node = ntree->nodes.first; node; node = node->next)
					if (node->type == SH_NODE_TEX_COORD)
						node->flag |= NODE_OPTIONS;
			}
		} FOREACH_NODETREE_END
	}

	if (main->versionfile < 264 || (main->versionfile == 264 && main->subversionfile < 2)) {
		MovieClip *clip;

		for (clip = main->movieclip.first; clip; clip = clip->id.next) {
			MovieTracking *tracking = &clip->tracking;
			MovieTrackingObject *tracking_object;

			for (tracking_object = tracking->objects.first;
			     tracking_object;
			     tracking_object = tracking_object->next)
			{
				if (tracking_object->keyframe1 == 0 && tracking_object->keyframe2 == 0) {
					tracking_object->keyframe1 = tracking->settings.keyframe1;
					tracking_object->keyframe2 = tracking->settings.keyframe2;
				}
			}
		}
	}

	if (main->versionfile < 264 || (main->versionfile == 264 && main->subversionfile < 3)) {
		/* smoke branch */
		{
			Object *ob;

			for (ob = main->object.first; ob; ob = ob->id.next) {
				ModifierData *md;
				for (md = ob->modifiers.first; md; md = md->next) {
					if (md->type == eModifierType_Smoke) {
						SmokeModifierData *smd = (SmokeModifierData *)md;
						if ((smd->type & MOD_SMOKE_TYPE_DOMAIN) && smd->domain) {
							/* keep branch saves if possible */
							if (!smd->domain->flame_max_temp) {
								smd->domain->burning_rate = 0.75f;
								smd->domain->flame_smoke = 1.0f;
								smd->domain->flame_vorticity = 0.5f;
								smd->domain->flame_ignition = 1.25f;
								smd->domain->flame_max_temp = 1.75f;
								smd->domain->adapt_threshold = 0.02f;
								smd->domain->adapt_margin = 4;
								smd->domain->flame_smoke_color[0] = 0.7f;
								smd->domain->flame_smoke_color[1] = 0.7f;
								smd->domain->flame_smoke_color[2] = 0.7f;
							}
						}
						else if ((smd->type & MOD_SMOKE_TYPE_FLOW) && smd->flow) {
							if (!smd->flow->texture_size) {
								smd->flow->fuel_amount = 1.0;
								smd->flow->surface_distance = 1.5;
								smd->flow->color[0] = 0.7f;
								smd->flow->color[1] = 0.7f;
								smd->flow->color[2] = 0.7f;
								smd->flow->texture_size = 1.0f;
							}
						}
					}
				}
			}
		}

		/* render border for viewport */
		{
			bScreen *sc;

			for (sc = main->screen.first; sc; sc = sc->id.next) {
				ScrArea *sa;
				for (sa = sc->areabase.first; sa; sa = sa->next) {
					SpaceLink *sl;
					for (sl = sa->spacedata.first; sl; sl = sl->next) {
						if (sl->spacetype == SPACE_VIEW3D) {
							View3D *v3d = (View3D *)sl;
							if (v3d->render_border.xmin == 0.0f && v3d->render_border.ymin == 0.0f &&
							    v3d->render_border.xmax == 0.0f && v3d->render_border.ymax == 0.0f)
							{
								v3d->render_border.xmax = 1.0f;
								v3d->render_border.ymax = 1.0f;
							}
						}
					}
				}
			}
		}
	}

	if (main->versionfile < 264 || (main->versionfile == 264 && main->subversionfile < 5)) {
		/* set a unwrapping margin and ABF by default */
		Scene *scene;

		for (scene=main->scene.first; scene; scene=scene->id.next) {
			if (scene->toolsettings->uvcalc_margin == 0.0f) {
				scene->toolsettings->uvcalc_margin = 0.001f;
				scene->toolsettings->unwrapper = 0;
			}
		}
	}

	if (main->versionfile < 264 || (main->versionfile == 264 && main->subversionfile < 6)) {
		/* Fix for bug #32982, internal_links list could get corrupted from r51630 onward.
		 * Simply remove bad internal_links lists to avoid NULL pointers.
		 */
		FOREACH_NODETREE(main, ntree, id) {
			bNode *node;
			bNodeLink *link, *nextlink;
			
			for (node = ntree->nodes.first; node; node = node->next) {
				for (link = node->internal_links.first; link; link = nextlink) {
					nextlink = link->next;
					if (!link->fromnode || !link->fromsock || !link->tonode || !link->tosock) {
						BLI_remlink(&node->internal_links, link);
					}
				}
			}
		} FOREACH_NODETREE_END
	}
	
	if (main->versionfile < 264 || (main->versionfile == 264 && main->subversionfile < 6)) {
		bScreen *sc;
		
		for (sc = main->screen.first; sc; sc = sc->id.next) {
			ScrArea *sa;
			for (sa = sc->areabase.first; sa; sa = sa->next) {
				SpaceLink *sl;
				if ( sa->spacetype == SPACE_LOGIC)
					do_version_logic_264(&sa->regionbase);
				
				for (sl = sa->spacedata.first; sl; sl = sl->next) {
					if (sl->spacetype == SPACE_LOGIC)
						do_version_logic_264(&sl->regionbase);
				}
			}
		}
	}

	if (main->versionfile < 264 || (main->versionfile == 264 && main->subversionfile < 7)) {
		/* convert tiles size from resolution and number of tiles */
		{
			Scene *scene;

			for (scene = main->scene.first; scene; scene = scene->id.next) {
				if (scene->r.tilex == 0 || scene->r.tiley == 1) {
					if (scene->r.xparts && scene->r.yparts) {
						/* scene could be set for panoramic rendering, so clamp with the
						 * lowest possible tile size value
						 */
						scene->r.tilex = max_ii(scene->r.xsch * scene->r.size / scene->r.xparts / 100, 8);
						scene->r.tiley = max_ii(scene->r.ysch * scene->r.size / scene->r.yparts / 100, 8);
					}
					else {
						/* happens when mixing using current trunk and previous release */
						scene->r.tilex = scene->r.tiley = 64;
					}
				}
			}
		}

		/* collision masks */
		{
			Object *ob;
			for (ob = main->object.first; ob; ob = ob->id.next) {
				if (ob->col_group == 0) {
					ob->col_group = 0x01;
					ob->col_mask = 0xff;
				}
			}
		}

		/* fallbck resection method settings */
		{
			MovieClip *clip;

			for (clip = main->movieclip.first; clip; clip = clip->id.next) {
				if (clip->tracking.settings.reconstruction_success_threshold == 0.0f) {
					clip->tracking.settings.reconstruction_success_threshold = 1e-3f;
				}
			}
		}
	}

	if (main->versionfile < 264 || (main->versionfile == 264 && main->subversionfile < 7)) {
		MovieClip *clip;

		for (clip = main->movieclip.first; clip; clip = clip->id.next) {
			MovieTrackingTrack *track;
			MovieTrackingObject *object;

			for (track = clip->tracking.tracks.first; track; track = track->next) {
				do_versions_affine_tracker_track(track);
			}

			for (object = clip->tracking.objects.first; object; object = object->next) {
				for (track = object->tracks.first; track; track = track->next) {
					do_versions_affine_tracker_track(track);
				}
			}
		}
	}

	if (main->versionfile < 265) {
		Object *ob;
		for (ob = main->object.first; ob; ob = ob->id.next) {
			if (ob->step_height == 0.0f) {
				ob->step_height = 0.15f;
				ob->jump_speed = 10.0f;
				ob->fall_speed = 55.0f;
			}
		}
	}

	if (main->versionfile < 265 || (main->versionfile == 265 && main->subversionfile < 3)) {
		bScreen *sc;
		for (sc = main->screen.first; sc; sc = sc->id.next) {
			ScrArea *sa;
			for (sa = sc->areabase.first; sa; sa = sa->next) {
				SpaceLink *sl;
				for (sl = sa->spacedata.first; sl; sl = sl->next) {
					switch (sl->spacetype) {
						case SPACE_VIEW3D:
						{
							View3D *v3d = (View3D *)sl;
							v3d->flag2 |= V3D_SHOW_GPENCIL;
							break;
						}
						case SPACE_SEQ:
						{
							SpaceSeq *sseq = (SpaceSeq *)sl;
							sseq->flag |= SEQ_SHOW_GPENCIL;
							break;
						}
						case SPACE_IMAGE:
						{
							SpaceImage *sima = (SpaceImage *)sl;
							sima->flag |= SI_SHOW_GPENCIL;
							break;
						}
						case SPACE_NODE:
						{
							SpaceNode *snode = (SpaceNode *)sl;
							snode->flag |= SNODE_SHOW_GPENCIL;
							break;
						}
						case SPACE_CLIP:
						{
							SpaceClip *sclip = (SpaceClip *)sl;
							sclip->flag |= SC_SHOW_GPENCIL;
							break;
						}
					}
				}
			}
		}
	}

	if (main->versionfile < 265 || (main->versionfile == 265 && main->subversionfile < 5)) {
		Scene *scene;
		Image *image;
		Tex *tex;

		for (scene = main->scene.first; scene; scene = scene->id.next) {
			Sequence *seq;
			bool set_premul = false;

			SEQ_BEGIN (scene->ed, seq)
			{
				if (seq->flag & SEQ_MAKE_PREMUL) {
					seq->alpha_mode = SEQ_ALPHA_STRAIGHT;
				}
				else {
					BKE_sequence_alpha_mode_from_extension(seq);
				}
			}
			SEQ_END

			if (scene->r.bake_samples == 0)
			scene->r.bake_samples = 256;

			if (scene->world) {
				World *world = blo_do_versions_newlibadr(fd, scene->id.lib, scene->world);

				if (world && is_zero_v3(&world->horr)) {
					if ((world->skytype & WO_SKYBLEND) == 0 || is_zero_v3(&world->zenr)) {
						set_premul = true;
					}
				}
			}
			else
				set_premul = true;

			if (set_premul) {
				printf("2.66 versioning fix: replacing black sky with premultiplied alpha for scene %s\n", scene->id.name + 2);
				scene->r.alphamode = R_ALPHAPREMUL;
			}
		}

		for (image = main->image.first; image; image = image->id.next) {
			if (image->flag & IMA_DO_PREMUL) {
				image->alpha_mode = IMA_ALPHA_STRAIGHT;
			}
			else {
				BKE_image_alpha_mode_from_extension(image);
			}
		}

		for (tex = main->tex.first; tex; tex = tex->id.next) {
			if (tex->type == TEX_IMAGE && (tex->imaflag & TEX_USEALPHA) == 0) {
				image = blo_do_versions_newlibadr(fd, tex->id.lib, tex->ima);

				if (image && (image->flag & IMA_DO_PREMUL) == 0)
					image->flag |= IMA_IGNORE_ALPHA;
			}
		}

		FOREACH_NODETREE(main, ntree, id) {
			if (ntree->type == NTREE_COMPOSIT) {
				bNode *node;
				for (node = ntree->nodes.first; node; node = node->next) {
					if (node->type == CMP_NODE_IMAGE) {
						Image *image = blo_do_versions_newlibadr(fd, ntree->id.lib, node->id);

						if (image) {
							if ((image->flag & IMA_DO_PREMUL) == 0 && image->alpha_mode == IMA_ALPHA_STRAIGHT)
								node->custom1 |= CMP_NODE_IMAGE_USE_STRAIGHT_OUTPUT;
						}
					}
				}
			}
		} FOREACH_NODETREE_END
	}
	else if (main->versionfile < 266 || (main->versionfile == 266 && main->subversionfile < 1)) {
		/* texture use alpha was removed for 2.66 but added back again for 2.66a,
		 * for compatibility all textures assumed it to be enabled */
		Tex *tex;

		for (tex = main->tex.first; tex; tex = tex->id.next)
			if (tex->type == TEX_IMAGE)
				tex->imaflag |= TEX_USEALPHA;
	}

	if (main->versionfile < 265 || (main->versionfile == 265 && main->subversionfile < 7)) {
		Curve *cu;

		for (cu = main->curve.first; cu; cu = cu->id.next) {
			if (cu->flag & (CU_FRONT | CU_BACK)) {
				if ( cu->ext1 != 0.0f || cu->ext2 != 0.0f) {
					Nurb *nu;

					for (nu = cu->nurb.first; nu; nu = nu->next) {
						int a;

						if (nu->bezt) {
							BezTriple *bezt = nu->bezt;
							a = nu->pntsu;

							while (a--) {
								bezt->radius = 1.0f;
								bezt++;
							}
						}
						else if (nu->bp) {
							BPoint *bp = nu->bp;
							a = nu->pntsu * nu->pntsv;

							while (a--) {
								bp->radius = 1.0f;
								bp++;
							}
						}
					}
				}
			}
		}
	}

	if (MAIN_VERSION_OLDER(main, 265, 9)) {
		Mesh *me;
		for (me = main->mesh.first; me; me = me->id.next) {
			BKE_mesh_do_versions_cd_flag_init(me);
		}
	}

	if (MAIN_VERSION_OLDER(main, 265, 10)) {
		Brush *br;
		for (br = main->brush.first; br; br = br->id.next) {
			if (br->ob_mode & OB_MODE_TEXTURE_PAINT) {
				br->mtex.brush_map_mode = MTEX_MAP_MODE_TILED;
			}
		}
	}

	// add storage for compositor translate nodes when not existing
	if (MAIN_VERSION_OLDER(main, 265, 11)) {
		FOREACH_NODETREE(main, ntree, id) {
			if (ntree->type == NTREE_COMPOSIT) {
				bNode *node;
				for (node = ntree->nodes.first; node; node = node->next) {
					if (node->type == CMP_NODE_TRANSLATE && node->storage == NULL) {
						node->storage = MEM_callocN(sizeof(NodeTranslateData), "node translate data");
					}
				}
			}
		} FOREACH_NODETREE_END
	}

	if (MAIN_VERSION_OLDER(main, 266, 2)) {
		FOREACH_NODETREE(main, ntree, id) {
			do_versions_nodetree_customnodes(ntree, ((ID *)ntree == id));
		} FOREACH_NODETREE_END
	}

	if (MAIN_VERSION_OLDER(main, 266, 2)) {
		bScreen *sc;
		for (sc= main->screen.first; sc; sc= sc->id.next) {
			ScrArea *sa;
			for (sa= sc->areabase.first; sa; sa= sa->next) {
				SpaceLink *sl;
				for (sl= sa->spacedata.first; sl; sl= sl->next) {
					if (sl->spacetype==SPACE_NODE) {
						SpaceNode *snode = (SpaceNode *)sl;
						
						/* reset pointers to force tree path update from context */
						snode->nodetree = NULL;
						snode->edittree = NULL;
						snode->id = NULL;
						snode->from = NULL;
						
						/* convert deprecated treetype setting to tree_idname */
						switch (snode->treetype) {
							case NTREE_COMPOSIT:
								strcpy(snode->tree_idname, "CompositorNodeTree");
								break;
							case NTREE_SHADER:
								strcpy(snode->tree_idname, "ShaderNodeTree");
								break;
							case NTREE_TEXTURE:
								strcpy(snode->tree_idname, "TextureNodeTree");
								break;
						}
					}
				}
			}
		}
	}
	
	/* Set flag for delayed do_versions in lib_verify_nodetree. It needs valid typeinfo pointers ... */
	{
		FOREACH_NODETREE(main, ntree, id) {
			/* XXX This should be kept without version check for now!
			 * As long as USE_NODE_COMPAT_CUSTOMNODES is active, files will write links
			 * to tree interface sockets for forward compatibility. These links need to be removed again
			 * on file load in new versions.
			 * Once forward compatibility is not required any longer, make a subversion bump
			 * and only execute this for older versions.
			 */
			ntree->flag |= NTREE_DO_VERSIONS_CUSTOMNODES_GROUP;
			
			/* Only add interface nodes once.
			 * In old Blender versions they will be removed automatically due to undefined type */
			if (MAIN_VERSION_OLDER(main, 266, 2))
				ntree->flag |= NTREE_DO_VERSIONS_CUSTOMNODES_GROUP_CREATE_INTERFACE;
		}
		FOREACH_NODETREE_END
	}

	if (MAIN_VERSION_OLDER(main, 266, 3)) {
		{
			/* Fix for a very old issue:
			 * Node names were nominally made unique in r24478 (2.50.8), but the do_versions check
			 * to update existing node names only applied to main->nodetree (i.e. group nodes).
			 * Uniqueness is now required for proper preview mapping,
			 * so do this now to ensure old files don't break.
			 */
			bNode *node;
			FOREACH_NODETREE(main, ntree, id) {
				if (id == &ntree->id)
					continue;	/* already fixed for node groups */
				
				for (node = ntree->nodes.first; node; node = node->next)
					nodeUniqueName(ntree, node);
			}
			FOREACH_NODETREE_END
		}
	}

	if (!MAIN_VERSION_ATLEAST(main, 266, 4)) {
		Brush *brush;
		for (brush = main->brush.first; brush; brush = brush->id.next) {
			default_mtex(&brush->mask_mtex);

			if (brush->ob_mode & OB_MODE_TEXTURE_PAINT) {
				brush->spacing /= 2;
			}
		}
	}

	if (!MAIN_VERSION_ATLEAST(main, 266, 6)) {
		Brush *brush;
		#define BRUSH_TEXTURE_OVERLAY (1 << 21)

		for (brush = main->brush.first; brush; brush = brush->id.next) {
			brush->overlay_flags = 0;
			if (brush->flag & BRUSH_TEXTURE_OVERLAY)
				brush->overlay_flags |= (BRUSH_OVERLAY_PRIMARY | BRUSH_OVERLAY_CURSOR);
		}
		#undef BRUSH_TEXTURE_OVERLAY
	}

	if (main->versionfile < 267) {
		//if (!DNA_struct_elem_find(fd->filesdna, "Brush", "int", "stencil_pos")) {
		Brush *brush;

		for (brush = main->brush.first; brush; brush = brush->id.next) {
			if (brush->stencil_dimension[0] == 0) {
				brush->stencil_dimension[0] = 256;
				brush->stencil_dimension[1] = 256;
				brush->stencil_pos[0] = 256;
				brush->stencil_pos[1] = 256;
			}
			if (brush->mask_stencil_dimension[0] == 0) {
				brush->mask_stencil_dimension[0] = 256;
				brush->mask_stencil_dimension[1] = 256;
				brush->mask_stencil_pos[0] = 256;
				brush->mask_stencil_pos[1] = 256;
			}
		}

		/* TIP: to initialize new variables added, use the new function
		 * DNA_struct_elem_find(fd->filesdna, "structname", "typename", "varname")
		 * example:
		 * if (!DNA_struct_elem_find(fd->filesdna, "UserDef", "short", "image_gpubuffer_limit"))
		 *     user->image_gpubuffer_limit = 10;
		 */
		
	}
	
	/* default values in Freestyle settings */
	if (main->versionfile < 267) {
		Scene *sce;
		SceneRenderLayer *srl;
		FreestyleLineStyle *linestyle;

		for(sce = main->scene.first; sce; sce = sce->id.next) {
			if (sce->r.line_thickness_mode == 0) {
				sce->r.line_thickness_mode = R_LINE_THICKNESS_ABSOLUTE;
				sce->r.unit_line_thickness = 1.0f;
			}
			for(srl = sce->r.layers.first; srl; srl = srl->next) {
				if (srl->freestyleConfig.mode == 0)
					srl->freestyleConfig.mode = FREESTYLE_CONTROL_EDITOR_MODE;
				if (srl->freestyleConfig.raycasting_algorithm == FREESTYLE_ALGO_CULLED_ADAPTIVE_CUMULATIVE ||
				    srl->freestyleConfig.raycasting_algorithm == FREESTYLE_ALGO_CULLED_ADAPTIVE_TRADITIONAL) {
					srl->freestyleConfig.raycasting_algorithm = 0; /* deprecated */
					srl->freestyleConfig.flags |= FREESTYLE_CULLING;
				}
			}

			/* not freestyle */
			{
				MeshStatVis *statvis = &sce->toolsettings->statvis;
				if (statvis->thickness_samples == 0) {
					statvis->overhang_axis = OB_NEGZ;
					statvis->overhang_min = 0;
					statvis->overhang_max = DEG2RADF(45.0f);

					statvis->thickness_max = 0.1f;
					statvis->thickness_samples = 1;

					statvis->distort_min = DEG2RADF(5.0f);
					statvis->distort_max = DEG2RADF(45.0f);

					statvis->sharp_min = DEG2RADF(90.0f);
					statvis->sharp_max = DEG2RADF(180.0f);
				}
			}

		}
		for(linestyle = main->linestyle.first; linestyle; linestyle = linestyle->id.next) {
#if 1
			/* disable the Misc panel for now */
			if (linestyle->panel == LS_PANEL_MISC) {
				linestyle->panel = LS_PANEL_STROKES;
			}
#endif
			if (linestyle->thickness_position == 0) {
				linestyle->thickness_position = LS_THICKNESS_CENTER;
				linestyle->thickness_ratio = 0.5f;
			}
			if (linestyle->chaining == 0)
				linestyle->chaining = LS_CHAINING_PLAIN;
			if (linestyle->rounds == 0)
				linestyle->rounds = 3;
		}
	}

	if (main->versionfile < 267) {
		/* Initialize the active_viewer_key for compositing */
		bScreen *screen;
		Scene *scene;
		bNodeInstanceKey active_viewer_key = {0};
		/* simply pick the first node space and use that for the active viewer key */
		for (screen = main->screen.first; screen; screen = screen->id.next) {
			ScrArea *sa;
			for (sa = screen->areabase.first; sa; sa = sa->next) {
				SpaceLink *sl;
				for (sl = sa->spacedata.first; sl; sl= sl->next) {
					if (sl->spacetype == SPACE_NODE) {
						SpaceNode *snode = (SpaceNode *)sl;
						bNodeTreePath *path = snode->treepath.last;
						if (!path)
							continue;
						
						active_viewer_key = path->parent_key;
						break;
					}
				}
				if (active_viewer_key.value != 0)
					break;
			}
			if (active_viewer_key.value != 0)
				break;
		}
		
		for (scene = main->scene.first; scene; scene = scene->id.next) {
			/* NB: scene->nodetree is a local ID block, has been direct_link'ed */
			if (scene->nodetree)
				scene->nodetree->active_viewer_key = active_viewer_key;
		}
	}

	if (MAIN_VERSION_OLDER(main, 267, 1))
	{
		Object *ob;

		for (ob = main->object.first; ob; ob = ob->id.next) {
			ModifierData *md;
			for (md = ob->modifiers.first; md; md = md->next) {
				if (md->type == eModifierType_Smoke) {
					SmokeModifierData *smd = (SmokeModifierData *)md;
					if ((smd->type & MOD_SMOKE_TYPE_DOMAIN) && smd->domain) {
						if (smd->domain->flags & MOD_SMOKE_HIGH_SMOOTH) {
							smd->domain->highres_sampling = SM_HRES_LINEAR;
						}
						else {
							smd->domain->highres_sampling = SM_HRES_NEAREST;
						}
					}
				}
			}
		}
	}


	{
		bScreen *sc;
		Object *ob;

		for (ob = main->object.first; ob; ob = ob->id.next) {
			ModifierData *md;
			for (md = ob->modifiers.first; md; md = md->next) {
				if (md->type == eModifierType_Smoke) {
					SmokeModifierData *smd = (SmokeModifierData *)md;
					if ((smd->type & MOD_SMOKE_TYPE_FLOW) && smd->flow) {
						if (!smd->flow->particle_size) {
							smd->flow->particle_size = 1.0f;
						}
					}
				}
			}
		}

		/*
		 * FIX some files have a zoom level of 0, and was checked during the drawing of the node space
		 *
		 * We moved this check to the do versions to be sure the value makes any sense.
		 */
		for (sc = main->screen.first; sc; sc = sc->id.next) {
			ScrArea *sa;
			for (sa = sc->areabase.first; sa; sa = sa->next) {
				SpaceLink *sl;
				for (sl = sa->spacedata.first; sl; sl = sl->next) {
					if (sl->spacetype == SPACE_NODE) {
						SpaceNode *snode = (SpaceNode *)sl;
						if (snode->zoom < 0.02f) {
							snode->zoom = 1.0;
						}
					}
				}
			}
		}
	}

	/* WATCH IT!!!: pointers from libdata have not been converted yet here! */
	/* WATCH IT 2!: Userdef struct init see do_versions_userdef() above! */

	/* don't forget to set version number in blender.c! */
}

#if 0 // XXX: disabled for now... we still don't have this in the right place in the loading code for it to work
static void do_versions_after_linking(FileData *fd, Library *lib, Main *main)
{
	/* old Animation System (using IPO's) needs to be converted to the new Animato system */
	if (main->versionfile < 250)
		do_versions_ipos_to_animato(main);
}
#endif

static void lib_link_all(FileData *fd, Main *main)
{
	oldnewmap_sort(fd);
	
	/* No load UI for undo memfiles */
	if (fd->memfile == NULL) {
		lib_link_windowmanager(fd, main);
		lib_link_screen(fd, main);
	}
	lib_link_scene(fd, main);
	lib_link_object(fd, main);
	lib_link_curve(fd, main);
	lib_link_mball(fd, main);
	lib_link_material(fd, main);
	lib_link_texture(fd, main);
	lib_link_image(fd, main);
	lib_link_ipo(fd, main);		// XXX deprecated... still needs to be maintained for version patches still
	lib_link_key(fd, main);
	lib_link_world(fd, main);
	lib_link_lamp(fd, main);
	lib_link_latt(fd, main);
	lib_link_text(fd, main);
	lib_link_camera(fd, main);
	lib_link_speaker(fd, main);
	lib_link_sound(fd, main);
	lib_link_group(fd, main);
	lib_link_armature(fd, main);
	lib_link_action(fd, main);
	lib_link_vfont(fd, main);
	lib_link_nodetree(fd, main);	/* has to be done after scene/materials, this will verify group nodes */
	lib_link_brush(fd, main);
	lib_link_particlesettings(fd, main);
	lib_link_movieclip(fd, main);
	lib_link_mask(fd, main);
	lib_link_linestyle(fd, main);

	lib_link_mesh(fd, main);		/* as last: tpage images with users at zero */
	
	lib_link_library(fd, main);		/* only init users */
}

static void direct_link_keymapitem(FileData *fd, wmKeyMapItem *kmi)
{
	kmi->properties = newdataadr(fd, kmi->properties);
	if (kmi->properties)
		IDP_DirectLinkProperty(kmi->properties, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
	kmi->ptr = NULL;
	kmi->flag &= ~KMI_UPDATE;
}

static BHead *read_userdef(BlendFileData *bfd, FileData *fd, BHead *bhead)
{
	UserDef *user;
	wmKeyMap *keymap;
	wmKeyMapItem *kmi;
	wmKeyMapDiffItem *kmdi;
	bAddon *addon;
	
	bfd->user = user= read_struct(fd, bhead, "user def");
	
	/* User struct has separate do-version handling */
	user->versionfile = bfd->main->versionfile;
	user->subversionfile = bfd->main->subversionfile;
	
	/* read all data into fd->datamap */
	bhead = read_data_into_oldnewmap(fd, bhead, "user def");
	
	if (user->keymaps.first) {
		/* backwards compatibility */
		user->user_keymaps= user->keymaps;
		user->keymaps.first= user->keymaps.last= NULL;
	}
	
	link_list(fd, &user->themes);
	link_list(fd, &user->user_keymaps);
	link_list(fd, &user->addons);
	link_list(fd, &user->autoexec_paths);
	
	for (keymap=user->user_keymaps.first; keymap; keymap=keymap->next) {
		keymap->modal_items= NULL;
		keymap->poll = NULL;
		keymap->flag &= ~KEYMAP_UPDATE;
		
		link_list(fd, &keymap->diff_items);
		link_list(fd, &keymap->items);
		
		for (kmdi=keymap->diff_items.first; kmdi; kmdi=kmdi->next) {
			kmdi->remove_item= newdataadr(fd, kmdi->remove_item);
			kmdi->add_item= newdataadr(fd, kmdi->add_item);
			
			if (kmdi->remove_item)
				direct_link_keymapitem(fd, kmdi->remove_item);
			if (kmdi->add_item)
				direct_link_keymapitem(fd, kmdi->add_item);
		}
		
		for (kmi=keymap->items.first; kmi; kmi=kmi->next)
			direct_link_keymapitem(fd, kmi);
	}

	for (addon = user->addons.first; addon; addon = addon->next) {
		addon->prop = newdataadr(fd, addon->prop);
		if (addon->prop) {
			IDP_DirectLinkProperty(addon->prop, (fd->flags & FD_FLAGS_SWITCH_ENDIAN), fd);
		}
	}

	// XXX
	user->uifonts.first = user->uifonts.last= NULL;
	
	link_list(fd, &user->uistyles);
	
	/* free fd->datamap again */
	oldnewmap_free_unused(fd->datamap);
	oldnewmap_clear(fd->datamap);
	
	return bhead;
}

BlendFileData *blo_read_file_internal(FileData *fd, const char *filepath)
{
	BHead *bhead = blo_firstbhead(fd);
	BlendFileData *bfd;
	ListBase mainlist = {NULL, NULL};
	
	bfd = MEM_callocN(sizeof(BlendFileData), "blendfiledata");
	bfd->main = MEM_callocN(sizeof(Main), "readfile_Main");
	BLI_addtail(&mainlist, bfd->main);
	fd->mainlist = &mainlist;
	
	bfd->main->versionfile = fd->fileversion;
	
	bfd->type = BLENFILETYPE_BLEND;
	BLI_strncpy(bfd->main->name, filepath, sizeof(bfd->main->name));

	while (bhead) {
		switch (bhead->code) {
		case DATA:
		case DNA1:
		case TEST: /* used as preview since 2.5x */
		case REND:
			bhead = blo_nextbhead(fd, bhead);
			break;
		case GLOB:
			bhead = read_global(bfd, fd, bhead);
			break;
		case USER:
			bhead = read_userdef(bfd, fd, bhead);
			break;
		case ENDB:
			bhead = NULL;
			break;
		
		case ID_LI:
			/* skip library datablocks in undo, this works together with
			 * BLO_read_from_memfile, where the old main->library is restored
			 * overwriting  the libraries from the memory file. previously
			 * it did not save ID_LI/ID_ID blocks in this case, but they are
			 * needed to make quit.blend recover them correctly. */
			if (fd->memfile)
				bhead = blo_nextbhead(fd, bhead);
			else
				bhead = read_libblock(fd, bfd->main, bhead, LIB_LOCAL, NULL);
			break;
		case ID_ID:
			/* same as above */
			if (fd->memfile)
				bhead = blo_nextbhead(fd, bhead);
			else
				/* always adds to the most recently loaded
				 * ID_LI block, see direct_link_library.
				 * this is part of the file format definition. */
				bhead = read_libblock(fd, mainlist.last, bhead, LIB_READ+LIB_EXTERN, NULL);
			break;
			
			/* in 2.50+ files, the file identifier for screens is patched, forward compatibility */
		case ID_SCRN:
			bhead->code = ID_SCR;
			/* deliberate pass on to default */
		default:
			bhead = read_libblock(fd, bfd->main, bhead, LIB_LOCAL, NULL);
		}
	}
	
	/* do before read_libraries, but skip undo case */
	if (fd->memfile==NULL)
		do_versions(fd, NULL, bfd->main);
	
	do_versions_userdef(fd, bfd);
	
	read_libraries(fd, &mainlist);
	
	blo_join_main(&mainlist);
	
	lib_link_all(fd, bfd->main);
	//do_versions_after_linking(fd, NULL, bfd->main); // XXX: not here (or even in this function at all)! this causes crashes on many files - Aligorith (July 04, 2010)
	lib_verify_nodetree(bfd->main, TRUE);
	fix_relpaths_library(fd->relabase, bfd->main); /* make all relative paths, relative to the open blend file */
	
	link_global(fd, bfd);	/* as last */
	
	return bfd;
}

/* ************* APPEND LIBRARY ************** */

struct BHeadSort {
	BHead *bhead;
	void *old;
};

static int verg_bheadsort(const void *v1, const void *v2)
{
	const struct BHeadSort *x1=v1, *x2=v2;
	
	if (x1->old > x2->old) return 1;
	else if (x1->old < x2->old) return -1;
	return 0;
}

static void sort_bhead_old_map(FileData *fd)
{
	BHead *bhead;
	struct BHeadSort *bhs;
	int tot = 0;
	
	for (bhead = blo_firstbhead(fd); bhead; bhead = blo_nextbhead(fd, bhead))
		tot++;
	
	fd->tot_bheadmap = tot;
	if (tot == 0) return;
	
	bhs = fd->bheadmap = MEM_mallocN(tot * sizeof(struct BHeadSort), "BHeadSort");
	
	for (bhead = blo_firstbhead(fd); bhead; bhead = blo_nextbhead(fd, bhead), bhs++) {
		bhs->bhead = bhead;
		bhs->old = bhead->old;
	}
	
	qsort(fd->bheadmap, tot, sizeof(struct BHeadSort), verg_bheadsort);
}

static BHead *find_previous_lib(FileData *fd, BHead *bhead)
{
	/* skip library datablocks in undo, see comment in read_libblock */
	if (fd->memfile)
		return NULL;

	for (; bhead; bhead = blo_prevbhead(fd, bhead)) {
		if (bhead->code == ID_LI)
			break;
	}

	return bhead;
}

static BHead *find_bhead(FileData *fd, void *old)
{
#if 0
	BHead *bhead;
#endif
	struct BHeadSort *bhs, bhs_s;
	
	if (!old)
		return NULL;

	if (fd->bheadmap == NULL)
		sort_bhead_old_map(fd);
	
	bhs_s.old = old;
	bhs = bsearch(&bhs_s, fd->bheadmap, fd->tot_bheadmap, sizeof(struct BHeadSort), verg_bheadsort);

	if (bhs)
		return bhs->bhead;
	
#if 0
	for (bhead = blo_firstbhead(fd); bhead; bhead= blo_nextbhead(fd, bhead)) {
		if (bhead->old == old)
			return bhead;
	}
#endif

	return NULL;
}

char *bhead_id_name(FileData *fd, BHead *bhead)
{
	return ((char *)(bhead+1)) + fd->id_name_offs;
}

static ID *is_yet_read(FileData *fd, Main *mainvar, BHead *bhead)
{
	const char *idname= bhead_id_name(fd, bhead);
	/* which_libbase can be NULL, intentionally not using idname+2 */
	return BLI_findstring(which_libbase(mainvar, GS(idname)), idname, offsetof(ID, name));
}

static void expand_doit_library(void *fdhandle, Main *mainvar, void *old)
{
	BHead *bhead;
	FileData *fd = fdhandle;
	ID *id;
	
	bhead = find_bhead(fd, old);
	if (bhead) {
		/* from another library? */
		if (bhead->code == ID_ID) {
			BHead *bheadlib= find_previous_lib(fd, bhead);
			
			if (bheadlib) {
				Library *lib = read_struct(fd, bheadlib, "Library");
				Main *ptr = blo_find_main(fd, lib->name, fd->relabase);
				
				if (ptr->curlib == NULL) {
					const char *idname= bhead_id_name(fd, bhead);
					
					BKE_reportf_wrap(fd->reports, RPT_WARNING, TIP_("LIB ERROR: Data refers to main .blend file: '%s' from %s"),
					                 idname, mainvar->curlib->filepath);
					return;
				}
				else
					id = is_yet_read(fd, ptr, bhead);
				
				if (id == NULL) {
					read_libblock(fd, ptr, bhead, LIB_READ+LIB_INDIRECT, NULL);
					// commented because this can print way too much
					// if (G.debug & G_DEBUG) printf("expand_doit: other lib %s\n", lib->name);
					
					/* for outliner dependency only */
					ptr->curlib->parent = mainvar->curlib;
				}
				else {
					/* The line below was commented by Ton (I assume), when Hos did the merge from the orange branch. rev 6568
					 * This line is NEEDED, the case is that you have 3 blend files...
					 * user.blend, lib.blend and lib_indirect.blend - if user.blend already references a "tree" from
					 * lib_indirect.blend but lib.blend does too, linking in a Scene or Group from lib.blend can result in an
					 * empty without the dupli group referenced. Once you save and reload the group would appear. - Campbell */
					/* This crashes files, must look further into it */
					
					/* Update: the issue is that in file reading, the oldnewmap is OK, but for existing data, it has to be
					 * inserted in the map to be found! */
					
					/* Update: previously it was checking for id->flag & LIB_PRE_EXISTING, however that does not affect file
					 * reading. For file reading we may need to insert it into the libmap as well, because you might have
					 * two files indirectly linking the same datablock, and in that case we need this in the libmap for the
					 * fd of both those files.
					 *
					 * The crash that this check avoided earlier was because bhead->code wasn't properly passed in, making
					 * change_idid_adr not detect the mapping was for an ID_ID datablock. */
					oldnewmap_insert(fd->libmap, bhead->old, id, bhead->code);
					change_idid_adr_fd(fd, bhead->old, id);
					
					// commented because this can print way too much
					// if (G.debug & G_DEBUG) printf("expand_doit: already linked: %s lib: %s\n", id->name, lib->name);
				}
				
				MEM_freeN(lib);
			}
		}
		else {
			id = is_yet_read(fd, mainvar, bhead);
			if (id == NULL) {
				read_libblock(fd, mainvar, bhead, LIB_TESTIND, NULL);
			}
			else {
				/* this is actually only needed on UI call? when ID was already read before, and another append
				 * happens which invokes same ID... in that case the lookup table needs this entry */
				oldnewmap_insert(fd->libmap, bhead->old, id, bhead->code);
				// commented because this can print way too much
				// if (G.debug & G_DEBUG) printf("expand: already read %s\n", id->name);
			}
		}
	}
}

static void (*expand_doit)(void *, Main *, void *);

// XXX deprecated - old animation system
static void expand_ipo(FileData *fd, Main *mainvar, Ipo *ipo)
{
	IpoCurve *icu;
	for (icu = ipo->curve.first; icu; icu = icu->next) {
		if (icu->driver)
			expand_doit(fd, mainvar, icu->driver->ob);
	}
}

// XXX deprecated - old animation system
static void expand_constraint_channels(FileData *fd, Main *mainvar, ListBase *chanbase)
{
	bConstraintChannel *chan;
	for (chan = chanbase->first; chan; chan = chan->next) {
		expand_doit(fd, mainvar, chan->ipo);
	}
}

static void expand_fmodifiers(FileData *fd, Main *mainvar, ListBase *list)
{
	FModifier *fcm;
	
	for (fcm = list->first; fcm; fcm = fcm->next) {
		/* library data for specific F-Modifier types */
		switch (fcm->type) {
			case FMODIFIER_TYPE_PYTHON:
			{
				FMod_Python *data = (FMod_Python *)fcm->data;
				
				expand_doit(fd, mainvar, data->script);
			}
				break;
		}
	}
}

static void expand_fcurves(FileData *fd, Main *mainvar, ListBase *list)
{
	FCurve *fcu;
	
	for (fcu = list->first; fcu; fcu = fcu->next) {
		/* Driver targets if there is a driver */
		if (fcu->driver) {
			ChannelDriver *driver = fcu->driver;
			DriverVar *dvar;
			
			for (dvar = driver->variables.first; dvar; dvar = dvar->next) {
				DRIVER_TARGETS_LOOPER(dvar) 
				{
					// TODO: only expand those that are going to get used?
					expand_doit(fd, mainvar, dtar->id);
				}
				DRIVER_TARGETS_LOOPER_END
			}
		}
		
		/* F-Curve Modifiers */
		expand_fmodifiers(fd, mainvar, &fcu->modifiers);
	}
}

static void expand_action(FileData *fd, Main *mainvar, bAction *act)
{
	bActionChannel *chan;
	
	// XXX deprecated - old animation system --------------
	for (chan=act->chanbase.first; chan; chan=chan->next) {
		expand_doit(fd, mainvar, chan->ipo);
		expand_constraint_channels(fd, mainvar, &chan->constraintChannels);
	}
	// ---------------------------------------------------
	
	/* F-Curves in Action */
	expand_fcurves(fd, mainvar, &act->curves);
}

static void expand_keyingsets(FileData *fd, Main *mainvar, ListBase *list)
{
	KeyingSet *ks;
	KS_Path *ksp;
	
	/* expand the ID-pointers in KeyingSets's paths */
	for (ks = list->first; ks; ks = ks->next) {
		for (ksp = ks->paths.first; ksp; ksp = ksp->next) {
			expand_doit(fd, mainvar, ksp->id);
		}
	}
}

static void expand_animdata_nlastrips(FileData *fd, Main *mainvar, ListBase *list)
{
	NlaStrip *strip;
	
	for (strip= list->first; strip; strip= strip->next) {
		/* check child strips */
		expand_animdata_nlastrips(fd, mainvar, &strip->strips);
		
		/* check F-Curves */
		expand_fcurves(fd, mainvar, &strip->fcurves);
		
		/* check F-Modifiers */
		expand_fmodifiers(fd, mainvar, &strip->modifiers);
		
		/* relink referenced action */
		expand_doit(fd, mainvar, strip->act);
	}
}

static void expand_animdata(FileData *fd, Main *mainvar, AnimData *adt)
{
	NlaTrack *nlt;
	
	/* own action */
	expand_doit(fd, mainvar, adt->action);
	expand_doit(fd, mainvar, adt->tmpact);
	
	/* drivers - assume that these F-Curves have driver data to be in this list... */
	expand_fcurves(fd, mainvar, &adt->drivers);
	
	/* nla-data - referenced actions */
	for (nlt = adt->nla_tracks.first; nlt; nlt = nlt->next) 
		expand_animdata_nlastrips(fd, mainvar, &nlt->strips);
}	

static void expand_particlesettings(FileData *fd, Main *mainvar, ParticleSettings *part)
{
	int a;
	
	expand_doit(fd, mainvar, part->dup_ob);
	expand_doit(fd, mainvar, part->dup_group);
	expand_doit(fd, mainvar, part->eff_group);
	expand_doit(fd, mainvar, part->bb_ob);
	
	if (part->adt)
		expand_animdata(fd, mainvar, part->adt);
	
	for (a = 0; a < MAX_MTEX; a++) {
		if (part->mtex[a]) {
			expand_doit(fd, mainvar, part->mtex[a]->tex);
			expand_doit(fd, mainvar, part->mtex[a]->object);
		}
	}
}

static void expand_group(FileData *fd, Main *mainvar, Group *group)
{
	GroupObject *go;
	
	for (go = group->gobject.first; go; go = go->next) {
		expand_doit(fd, mainvar, go->ob);
	}
}

static void expand_key(FileData *fd, Main *mainvar, Key *key)
{
	expand_doit(fd, mainvar, key->ipo); // XXX deprecated - old animation system
	
	if (key->adt)
		expand_animdata(fd, mainvar, key->adt);
}

static void expand_nodetree(FileData *fd, Main *mainvar, bNodeTree *ntree)
{
	bNode *node;
	
	if (ntree->adt)
		expand_animdata(fd, mainvar, ntree->adt);
		
	if (ntree->gpd)
		expand_doit(fd, mainvar, ntree->gpd);
	
	for (node = ntree->nodes.first; node; node = node->next) {
		if (node->id && node->type != CMP_NODE_R_LAYERS)
			expand_doit(fd, mainvar, node->id);
	}

}

static void expand_texture(FileData *fd, Main *mainvar, Tex *tex)
{
	expand_doit(fd, mainvar, tex->ima);
	expand_doit(fd, mainvar, tex->ipo); // XXX deprecated - old animation system
	
	if (tex->adt)
		expand_animdata(fd, mainvar, tex->adt);
	
	if (tex->nodetree)
		expand_nodetree(fd, mainvar, tex->nodetree);
}

static void expand_brush(FileData *fd, Main *mainvar, Brush *brush)
{
	expand_doit(fd, mainvar, brush->mtex.tex);
	expand_doit(fd, mainvar, brush->clone.image);
}

static void expand_material(FileData *fd, Main *mainvar, Material *ma)
{
	int a;
	
	for (a = 0; a < MAX_MTEX; a++) {
		if (ma->mtex[a]) {
			expand_doit(fd, mainvar, ma->mtex[a]->tex);
			expand_doit(fd, mainvar, ma->mtex[a]->object);
		}
	}
	
	expand_doit(fd, mainvar, ma->ipo); // XXX deprecated - old animation system
	
	if (ma->adt)
		expand_animdata(fd, mainvar, ma->adt);
	
	if (ma->nodetree)
		expand_nodetree(fd, mainvar, ma->nodetree);
	
	if (ma->group)
		expand_doit(fd, mainvar, ma->group);
}

static void expand_lamp(FileData *fd, Main *mainvar, Lamp *la)
{
	int a;
	
	for (a = 0; a < MAX_MTEX; a++) {
		if (la->mtex[a]) {
			expand_doit(fd, mainvar, la->mtex[a]->tex);
			expand_doit(fd, mainvar, la->mtex[a]->object);
		}
	}
	
	expand_doit(fd, mainvar, la->ipo); // XXX deprecated - old animation system
	
	if (la->adt)
		expand_animdata(fd, mainvar, la->adt);
	
	if (la->nodetree)
		expand_nodetree(fd, mainvar, la->nodetree);
}

static void expand_lattice(FileData *fd, Main *mainvar, Lattice *lt)
{
	expand_doit(fd, mainvar, lt->ipo); // XXX deprecated - old animation system
	expand_doit(fd, mainvar, lt->key);
	
	if (lt->adt)
		expand_animdata(fd, mainvar, lt->adt);
}


static void expand_world(FileData *fd, Main *mainvar, World *wrld)
{
	int a;
	
	for (a = 0; a < MAX_MTEX; a++) {
		if (wrld->mtex[a]) {
			expand_doit(fd, mainvar, wrld->mtex[a]->tex);
			expand_doit(fd, mainvar, wrld->mtex[a]->object);
		}
	}
	
	expand_doit(fd, mainvar, wrld->ipo); // XXX deprecated - old animation system
	
	if (wrld->adt)
		expand_animdata(fd, mainvar, wrld->adt);
	
	if (wrld->nodetree)
		expand_nodetree(fd, mainvar, wrld->nodetree);
}


static void expand_mball(FileData *fd, Main *mainvar, MetaBall *mb)
{
	int a;
	
	for (a = 0; a < mb->totcol; a++) {
		expand_doit(fd, mainvar, mb->mat[a]);
	}
	
	if (mb->adt)
		expand_animdata(fd, mainvar, mb->adt);
}

static void expand_curve(FileData *fd, Main *mainvar, Curve *cu)
{
	int a;
	
	for (a = 0; a < cu->totcol; a++) {
		expand_doit(fd, mainvar, cu->mat[a]);
	}
	
	expand_doit(fd, mainvar, cu->vfont);
	expand_doit(fd, mainvar, cu->vfontb);
	expand_doit(fd, mainvar, cu->vfonti);
	expand_doit(fd, mainvar, cu->vfontbi);
	expand_doit(fd, mainvar, cu->key);
	expand_doit(fd, mainvar, cu->ipo); // XXX deprecated - old animation system
	expand_doit(fd, mainvar, cu->bevobj);
	expand_doit(fd, mainvar, cu->taperobj);
	expand_doit(fd, mainvar, cu->textoncurve);
	
	if (cu->adt)
		expand_animdata(fd, mainvar, cu->adt);
}

static void expand_mesh(FileData *fd, Main *mainvar, Mesh *me)
{
	CustomDataLayer *layer;
	TFace *tf;
	int a, i;
	
	if (me->adt)
		expand_animdata(fd, mainvar, me->adt);
		
	for (a = 0; a < me->totcol; a++) {
		expand_doit(fd, mainvar, me->mat[a]);
	}
	
	expand_doit(fd, mainvar, me->key);
	expand_doit(fd, mainvar, me->texcomesh);
	
	if (me->tface) {
		tf = me->tface;
		for (i=0; i<me->totface; i++, tf++) {
			if (tf->tpage)
				expand_doit(fd, mainvar, tf->tpage);
		}
	}

	if (me->mface && !me->mpoly) {
		MTFace *mtf;

		for (a = 0; a < me->fdata.totlayer; a++) {
			layer = &me->fdata.layers[a];

			if (layer->type == CD_MTFACE) {
				mtf = (MTFace *) layer->data;
				for (i = 0; i < me->totface; i++, mtf++) {
					if (mtf->tpage)
						expand_doit(fd, mainvar, mtf->tpage);
				}
			}
		}
	}
	else {
		MTexPoly *mtp;

		for (a = 0; a < me->pdata.totlayer; a++) {
			layer = &me->pdata.layers[a];

			if (layer->type == CD_MTEXPOLY) {
				mtp = (MTexPoly *) layer->data;

				for (i = 0; i < me->totpoly; i++, mtp++) {
					if (mtp->tpage)
						expand_doit(fd, mainvar, mtp->tpage);
				}
			}
		}
	}
}

/* temp struct used to transport needed info to expand_constraint_cb() */
typedef struct tConstraintExpandData {
	FileData *fd;
	Main *mainvar;
} tConstraintExpandData;
/* callback function used to expand constraint ID-links */
static void expand_constraint_cb(bConstraint *UNUSED(con), ID **idpoin, short UNUSED(isReference), void *userdata)
{
	tConstraintExpandData *ced = (tConstraintExpandData *)userdata;
	expand_doit(ced->fd, ced->mainvar, *idpoin);
}

static void expand_constraints(FileData *fd, Main *mainvar, ListBase *lb)
{
	tConstraintExpandData ced;
	bConstraint *curcon;
	
	/* relink all ID-blocks used by the constraints */
	ced.fd = fd;
	ced.mainvar = mainvar;
	
	BKE_id_loop_constraints(lb, expand_constraint_cb, &ced);
	
	/* deprecated manual expansion stuff */
	for (curcon = lb->first; curcon; curcon = curcon->next) {
		if (curcon->ipo)
			expand_doit(fd, mainvar, curcon->ipo); // XXX deprecated - old animation system
	}
}

#if 0 /* Disabled as it doesn't actually do anything except recurse... */
static void expand_bones(FileData *fd, Main *mainvar, Bone *bone)
{
	Bone *curBone;
	
	for (curBone = bone->childbase.first; curBone; curBone=curBone->next) {
		expand_bones(fd, mainvar, curBone);
	}
}
#endif

static void expand_pose(FileData *fd, Main *mainvar, bPose *pose)
{
	bPoseChannel *chan;
	
	if (!pose)
		return;
	
	for (chan = pose->chanbase.first; chan; chan = chan->next) {
		expand_constraints(fd, mainvar, &chan->constraints);
		expand_doit(fd, mainvar, chan->custom);
	}
}

static void expand_armature(FileData *fd, Main *mainvar, bArmature *arm)
{	
	if (arm->adt)
		expand_animdata(fd, mainvar, arm->adt);
	
#if 0 /* Disabled as this currently only recurses down the chain doing nothing */
	{
		Bone *curBone;
		
		for (curBone = arm->bonebase.first; curBone; curBone=curBone->next) {
			expand_bones(fd, mainvar, curBone);
		}
	}
#endif
}

static void expand_object_expandModifiers(void *userData, Object *UNUSED(ob),
                                          ID **idpoin)
{
	struct { FileData *fd; Main *mainvar; } *data= userData;
	
	FileData *fd = data->fd;
	Main *mainvar = data->mainvar;
	
	expand_doit(fd, mainvar, *idpoin);
}

static void expand_object(FileData *fd, Main *mainvar, Object *ob)
{
	ParticleSystem *psys;
	bSensor *sens;
	bController *cont;
	bActuator *act;
	bActionStrip *strip;
	PartEff *paf;
	int a;
	
	expand_doit(fd, mainvar, ob->data);
	
	/* expand_object_expandModifier() */
	if (ob->modifiers.first) {
		struct { FileData *fd; Main *mainvar; } data;
		data.fd = fd;
		data.mainvar = mainvar;
		
		modifiers_foreachIDLink(ob, expand_object_expandModifiers, (void *)&data);
	}
	
	expand_pose(fd, mainvar, ob->pose);
	expand_doit(fd, mainvar, ob->poselib);
	expand_constraints(fd, mainvar, &ob->constraints);
	
	expand_doit(fd, mainvar, ob->gpd);
	
// XXX deprecated - old animation system (for version patching only)
	expand_doit(fd, mainvar, ob->ipo);
	expand_doit(fd, mainvar, ob->action);
	
	expand_constraint_channels(fd, mainvar, &ob->constraintChannels);
	
	for (strip=ob->nlastrips.first; strip; strip=strip->next) {
		expand_doit(fd, mainvar, strip->object);
		expand_doit(fd, mainvar, strip->act);
		expand_doit(fd, mainvar, strip->ipo);
	}
// XXX deprecated - old animation system (for version patching only)
	
	if (ob->adt)
		expand_animdata(fd, mainvar, ob->adt);
	
	for (a = 0; a < ob->totcol; a++) {
		expand_doit(fd, mainvar, ob->mat[a]);
	}
	
	paf = blo_do_version_give_parteff_245(ob);
	if (paf && paf->group) 
		expand_doit(fd, mainvar, paf->group);
	
	if (ob->dup_group)
		expand_doit(fd, mainvar, ob->dup_group);
	
	if (ob->proxy)
		expand_doit(fd, mainvar, ob->proxy);
	if (ob->proxy_group)
		expand_doit(fd, mainvar, ob->proxy_group);
	
	for (psys = ob->particlesystem.first; psys; psys = psys->next)
		expand_doit(fd, mainvar, psys->part);
	
	for (sens = ob->sensors.first; sens; sens = sens->next) {
		if (sens->type == SENS_TOUCH) {
			bTouchSensor *ts = sens->data;
			expand_doit(fd, mainvar, ts->ma);
		}
		else if (sens->type == SENS_MESSAGE) {
			bMessageSensor *ms = sens->data;
			expand_doit(fd, mainvar, ms->fromObject);
		}
	}
	
	for (cont = ob->controllers.first; cont; cont = cont->next) {
		if (cont->type == CONT_PYTHON) {
			bPythonCont *pc = cont->data;
			expand_doit(fd, mainvar, pc->text);
		}
	}
	
	for (act = ob->actuators.first; act; act = act->next) {
		if (act->type == ACT_SOUND) {
			bSoundActuator *sa = act->data;
			expand_doit(fd, mainvar, sa->sound);
		}
		else if (act->type == ACT_CAMERA) {
			bCameraActuator *ca = act->data;
			expand_doit(fd, mainvar, ca->ob);
		}
		else if (act->type == ACT_EDIT_OBJECT) {
			bEditObjectActuator *eoa = act->data;
			if (eoa) {
				expand_doit(fd, mainvar, eoa->ob);
				expand_doit(fd, mainvar, eoa->me);
			}
		}
		else if (act->type == ACT_OBJECT) {
			bObjectActuator *oa = act->data;
			expand_doit(fd, mainvar, oa->reference);
		}
		else if (act->type == ACT_ADD_OBJECT) {
			bAddObjectActuator *aoa = act->data;
			expand_doit(fd, mainvar, aoa->ob);
		}
		else if (act->type == ACT_SCENE) {
			bSceneActuator *sa = act->data;
			expand_doit(fd, mainvar, sa->camera);
			expand_doit(fd, mainvar, sa->scene);
		}
		else if (act->type == ACT_2DFILTER) {
			bTwoDFilterActuator *tdfa = act->data;
			expand_doit(fd, mainvar, tdfa->text);
		}
		else if (act->type == ACT_ACTION) {
			bActionActuator *aa = act->data;
			expand_doit(fd, mainvar, aa->act);
		}
		else if (act->type == ACT_SHAPEACTION) {
			bActionActuator *aa = act->data;
			expand_doit(fd, mainvar, aa->act);
		}
		else if (act->type == ACT_PROPERTY) {
			bPropertyActuator *pa = act->data;
			expand_doit(fd, mainvar, pa->ob);
		}
		else if (act->type == ACT_MESSAGE) {
			bMessageActuator *ma = act->data;
			expand_doit(fd, mainvar, ma->toObject);
		}
		else if (act->type==ACT_PARENT) {
			bParentActuator *pa = act->data;
			expand_doit(fd, mainvar, pa->ob);
		}
		else if (act->type == ACT_ARMATURE) {
			bArmatureActuator *arma = act->data;
			expand_doit(fd, mainvar, arma->target);
		}
		else if (act->type == ACT_STEERING) {
			bSteeringActuator *sta = act->data;
			expand_doit(fd, mainvar, sta->target);
			expand_doit(fd, mainvar, sta->navmesh);
		}
	}
	
	if (ob->pd && ob->pd->tex)
		expand_doit(fd, mainvar, ob->pd->tex);

	if (ob->rigidbody_constraint) {
		expand_doit(fd, mainvar, ob->rigidbody_constraint->ob1);
		expand_doit(fd, mainvar, ob->rigidbody_constraint->ob2);
	}

}

static void expand_scene(FileData *fd, Main *mainvar, Scene *sce)
{
	Base *base;
	SceneRenderLayer *srl;
	FreestyleModuleConfig *module;
	FreestyleLineSet *lineset;
	
	for (base = sce->base.first; base; base = base->next) {
		expand_doit(fd, mainvar, base->object);
	}
	expand_doit(fd, mainvar, sce->camera);
	expand_doit(fd, mainvar, sce->world);
	
	if (sce->adt)
		expand_animdata(fd, mainvar, sce->adt);
	expand_keyingsets(fd, mainvar, &sce->keyingsets);
	
	if (sce->set)
		expand_doit(fd, mainvar, sce->set);
	
	if (sce->nodetree)
		expand_nodetree(fd, mainvar, sce->nodetree);
	
	for (srl = sce->r.layers.first; srl; srl = srl->next) {
		expand_doit(fd, mainvar, srl->mat_override);
		expand_doit(fd, mainvar, srl->light_override);
		for (module = srl->freestyleConfig.modules.first; module; module = module->next) {
			if (module->script)
				expand_doit(fd, mainvar, module->script);
		}
		for (lineset = srl->freestyleConfig.linesets.first; lineset; lineset = lineset->next) {
			if (lineset->group)
				expand_doit(fd, mainvar, lineset->group);
			expand_doit(fd, mainvar, lineset->linestyle);
		}
	}
	
	if (sce->r.dometext)
		expand_doit(fd, mainvar, sce->gm.dome.warptext);
	
	if (sce->gpd)
		expand_doit(fd, mainvar, sce->gpd);
		
	if (sce->ed) {
		Sequence *seq;
		
		SEQ_BEGIN (sce->ed, seq)
		{
			if (seq->scene) expand_doit(fd, mainvar, seq->scene);
			if (seq->scene_camera) expand_doit(fd, mainvar, seq->scene_camera);
			if (seq->sound) expand_doit(fd, mainvar, seq->sound);
		}
		SEQ_END
	}
	
	if (sce->rigidbody_world) {
		expand_doit(fd, mainvar, sce->rigidbody_world->group);
		expand_doit(fd, mainvar, sce->rigidbody_world->constraints);
	}

#ifdef DURIAN_CAMERA_SWITCH
	{
		TimeMarker *marker;
		
		for (marker = sce->markers.first; marker; marker = marker->next) {
			if (marker->camera) {
				expand_doit(fd, mainvar, marker->camera);
			}
		}
	}
#endif

	expand_doit(fd, mainvar, sce->clip);
}

static void expand_camera(FileData *fd, Main *mainvar, Camera *ca)
{
	expand_doit(fd, mainvar, ca->ipo); // XXX deprecated - old animation system
	
	if (ca->adt)
		expand_animdata(fd, mainvar, ca->adt);
}

static void expand_speaker(FileData *fd, Main *mainvar, Speaker *spk)
{
	expand_doit(fd, mainvar, spk->sound);

	if (spk->adt)
		expand_animdata(fd, mainvar, spk->adt);
}

static void expand_sound(FileData *fd, Main *mainvar, bSound *snd)
{
	expand_doit(fd, mainvar, snd->ipo); // XXX deprecated - old animation system
}

static void expand_movieclip(FileData *fd, Main *mainvar, MovieClip *clip)
{
	if (clip->adt)
		expand_animdata(fd, mainvar, clip->adt);
}

static void expand_mask_parent(FileData *fd, Main *mainvar, MaskParent *parent)
{
	if (parent->id) {
		expand_doit(fd, mainvar, parent->id);
	}
}

static void expand_mask(FileData *fd, Main *mainvar, Mask *mask)
{
	MaskLayer *mask_layer;

	if (mask->adt)
		expand_animdata(fd, mainvar, mask->adt);

	for (mask_layer = mask->masklayers.first; mask_layer; mask_layer = mask_layer->next) {
		MaskSpline *spline;

		for (spline = mask_layer->splines.first; spline; spline = spline->next) {
			int i;

			for (i = 0; i < spline->tot_point; i++) {
				MaskSplinePoint *point = &spline->points[i];

				expand_mask_parent(fd, mainvar, &point->parent);
			}

			expand_mask_parent(fd, mainvar, &spline->parent);
		}
	}
}

static void expand_linestyle(FileData *fd, Main *mainvar, FreestyleLineStyle *linestyle)
{
	LineStyleModifier *m;

	if (linestyle->adt)
		expand_animdata(fd, mainvar, linestyle->adt);
	for (m = linestyle->color_modifiers.first; m; m = m->next) {
		if (m->type == LS_MODIFIER_DISTANCE_FROM_OBJECT)
			expand_doit(fd, mainvar, ((LineStyleColorModifier_DistanceFromObject *)m)->target);
	}
	for (m = linestyle->alpha_modifiers.first; m; m = m->next) {
		if (m->type == LS_MODIFIER_DISTANCE_FROM_OBJECT)
			expand_doit(fd, mainvar, ((LineStyleAlphaModifier_DistanceFromObject *)m)->target);
	}
	for (m = linestyle->thickness_modifiers.first; m; m = m->next) {
		if (m->type == LS_MODIFIER_DISTANCE_FROM_OBJECT)
			expand_doit(fd, mainvar, ((LineStyleThicknessModifier_DistanceFromObject *)m)->target);
	}
}

void BLO_main_expander(void (*expand_doit_func)(void *, Main *, void *))
{
	expand_doit = expand_doit_func;
}

void BLO_expand_main(void *fdhandle, Main *mainvar)
{
	ListBase *lbarray[MAX_LIBARRAY];
	FileData *fd = fdhandle;
	ID *id;
	int a, do_it = TRUE;
	
	while (do_it) {
		do_it = FALSE;
		
		a = set_listbasepointers(mainvar, lbarray);
		while (a--) {
			id = lbarray[a]->first;
			while (id) {
				if (id->flag & LIB_NEED_EXPAND) {
					switch (GS(id->name)) {
					case ID_OB:
						expand_object(fd, mainvar, (Object *)id);
						break;
					case ID_ME:
						expand_mesh(fd, mainvar, (Mesh *)id);
						break;
					case ID_CU:
						expand_curve(fd, mainvar, (Curve *)id);
						break;
					case ID_MB:
						expand_mball(fd, mainvar, (MetaBall *)id);
						break;
					case ID_SCE:
						expand_scene(fd, mainvar, (Scene *)id);
						break;
					case ID_MA:
						expand_material(fd, mainvar, (Material *)id);
						break;
					case ID_TE:
						expand_texture(fd, mainvar, (Tex *)id);
						break;
					case ID_WO:
						expand_world(fd, mainvar, (World *)id);
						break;
					case ID_LT:
						expand_lattice(fd, mainvar, (Lattice *)id);
						break;
					case ID_LA:
						expand_lamp(fd, mainvar, (Lamp *)id);
						break;
					case ID_KE:
						expand_key(fd, mainvar, (Key *)id);
						break;
					case ID_CA:
						expand_camera(fd, mainvar, (Camera *)id);
						break;
					case ID_SPK:
						expand_speaker(fd, mainvar, (Speaker *)id);
						break;
					case ID_SO:
						expand_sound(fd, mainvar, (bSound *)id);
						break;
					case ID_AR:
						expand_armature(fd, mainvar, (bArmature *)id);
						break;
					case ID_AC:
						expand_action(fd, mainvar, (bAction *)id); // XXX deprecated - old animation system
						break;
					case ID_GR:
						expand_group(fd, mainvar, (Group *)id);
						break;
					case ID_NT:
						expand_nodetree(fd, mainvar, (bNodeTree *)id);
						break;
					case ID_BR:
						expand_brush(fd, mainvar, (Brush *)id);
						break;
					case ID_IP:
						expand_ipo(fd, mainvar, (Ipo *)id); // XXX deprecated - old animation system
						break;
					case ID_PA:
						expand_particlesettings(fd, mainvar, (ParticleSettings *)id);
						break;
					case ID_MC:
						expand_movieclip(fd, mainvar, (MovieClip *)id);
						break;
					case ID_MSK:
						expand_mask(fd, mainvar, (Mask *)id);
						break;
					case ID_LS:
						expand_linestyle(fd, mainvar, (FreestyleLineStyle *)id);
						break;
					}
					
					do_it = TRUE;
					id->flag -= LIB_NEED_EXPAND;
					
				}
				id = id->next;
			}
		}
	}
}


/* ***************************** */
	
static int object_in_any_scene(Main *mainvar, Object *ob)
{
	Scene *sce;
	
	for (sce= mainvar->scene.first; sce; sce= sce->id.next) {
		if (BKE_scene_base_find(sce, ob))
			return 1;
	}
	
	return 0;
}

static void give_base_to_objects(Main *mainvar, Scene *sce, Library *lib, const short idcode, const short is_link, const short active_lay)
{
	Object *ob;
	Base *base;
	const short is_group_append = (is_link==FALSE && idcode==ID_GR);

	/* give all objects which are LIB_INDIRECT a base, or for a group when *lib has been set */
	for (ob = mainvar->object.first; ob; ob = ob->id.next) {
		if (ob->id.flag & LIB_INDIRECT) {
			/* IF below is quite confusing!
			 * if we are appending, but this object wasnt just added along with a group,
			 * then this is already used indirectly in the scene somewhere else and we didnt just append it.
			 *
			 * (ob->id.flag & LIB_PRE_EXISTING)==0 means that this is a newly appended object - Campbell */
			if (is_group_append==0 || (ob->id.flag & LIB_PRE_EXISTING)==0) {
				int do_it = FALSE;
				
				if (ob->id.us == 0) {
					do_it = TRUE;
				}
				else if (idcode==ID_GR) {
					if (ob->id.us==1 && is_link==FALSE && ob->id.lib==lib) {
						if ((ob->flag & OB_FROMGROUP) && object_in_any_scene(mainvar, ob)==0) {
							do_it = TRUE;
						}
					}
				}
				else {
					/* when appending, make sure any indirectly loaded objects
					 * get a base else they cant be accessed at all [#27437] */
					if (ob->id.us==1 && is_link==FALSE && ob->id.lib==lib) {
						/* we may be appending from a scene where we already
						 *  have a linked object which is not in any scene [#27616] */
						if ((ob->id.flag & LIB_PRE_EXISTING)==0) {
							if (object_in_any_scene(mainvar, ob)==0) {
								do_it = TRUE;
							}
						}
					}
				}
				
				if (do_it) {
					base = MEM_callocN(sizeof(Base), "add_ext_base");
					BLI_addtail(&sce->base, base);
					
					if (active_lay) ob->lay = sce->lay;
					
					base->lay = ob->lay;
					base->object = ob;
					base->flag = ob->flag;
					ob->id.us = 1;
					
					ob->id.flag -= LIB_INDIRECT;
					ob->id.flag |= LIB_EXTERN;
				}
			}
		}
	}
}

static void give_base_to_groups(Main *mainvar, Scene *scene)
{
	Group *group;
	
	/* give all objects which are LIB_INDIRECT a base, or for a group when *lib has been set */
	for (group = mainvar->group.first; group; group = group->id.next) {
		if (((group->id.flag & LIB_INDIRECT)==0 && (group->id.flag & LIB_PRE_EXISTING)==0)) {
			Base *base;
			
			/* BKE_object_add(...) messes with the selection */
			Object *ob = BKE_object_add_only_object(mainvar, OB_EMPTY, group->id.name + 2);
			ob->type = OB_EMPTY;
			ob->lay = scene->lay;
			
			/* assign the base */
			base = BKE_scene_base_add(scene, ob);
			base->flag |= SELECT;
			base->object->flag= base->flag;
			DAG_id_tag_update(&ob->id, OB_RECALC_OB | OB_RECALC_DATA | OB_RECALC_TIME);
			scene->basact = base;
			
			/* assign the group */
			ob->dup_group = group;
			ob->transflag |= OB_DUPLIGROUP;
			rename_id(&ob->id, group->id.name + 2);
			copy_v3_v3(ob->loc, scene->cursor);
		}
	}
}

/* returns true if the item was found
 * but it may already have already been appended/linked */
static ID *append_named_part(Main *mainl, FileData *fd, const char *idname, const short idcode)
{
	BHead *bhead;
	ID *id = NULL;
	int found = 0;

	for (bhead = blo_firstbhead(fd); bhead; bhead = blo_nextbhead(fd, bhead)) {
		if (bhead->code == idcode) {
			const char *idname_test= bhead_id_name(fd, bhead);
			
			if (strcmp(idname_test + 2, idname) == 0) {
				found = 1;
				id = is_yet_read(fd, mainl, bhead);
				if (id == NULL) {
					/* not read yet */
					read_libblock(fd, mainl, bhead, LIB_TESTEXT, &id);
					
					if (id) {
						/* sort by name in list */
						ListBase *lb = which_libbase(mainl, idcode);
						id_sort_by_name(lb, id);
					}
				}
				else {
					/* already linked */
					if (G.debug)
						printf("append: already linked\n");
					oldnewmap_insert(fd->libmap, bhead->old, id, bhead->code);
					if (id->flag & LIB_INDIRECT) {
						id->flag -= LIB_INDIRECT;
						id->flag |= LIB_EXTERN;
					}
				}
				
				break;
			}
		}
		else if (bhead->code == ENDB) {
			break;
		}
	}
	
	/* if we found the id but the id is NULL, this is really bad */
	BLI_assert((found != 0) == (id != NULL));
	
	return (found) ? id : NULL;
}

/* simple reader for copy/paste buffers */
void BLO_library_append_all(Main *mainl, BlendHandle *bh)
{
	FileData *fd = (FileData *)(bh);
	BHead *bhead;
	ID *id = NULL;
	
	for (bhead = blo_firstbhead(fd); bhead; bhead = blo_nextbhead(fd, bhead)) {
		if (bhead->code == ENDB)
			break;
		if (bhead->code == ID_OB)
			read_libblock(fd, mainl, bhead, LIB_TESTIND, &id);
			
		if (id) {
			/* sort by name in list */
			ListBase *lb = which_libbase(mainl, GS(id->name));
			id_sort_by_name(lb, id);
		}
	}
}


static ID *append_named_part_ex(const bContext *C, Main *mainl, FileData *fd, const char *idname, const int idcode, const int flag)
{
	ID *id= append_named_part(mainl, fd, idname, idcode);

	if (id && (GS(id->name) == ID_OB)) {	/* loose object: give a base */
		Scene *scene = CTX_data_scene(C); /* can be NULL */
		if (scene) {
			Base *base;
			Object *ob;
			
			base= MEM_callocN(sizeof(Base), "app_nam_part");
			BLI_addtail(&scene->base, base);
			
			ob = (Object *)id;
			
			/* link at active layer (view3d->lay if in context, else scene->lay */
			if ((flag & FILE_ACTIVELAY)) {
				View3D *v3d = CTX_wm_view3d(C);
				ob->lay = v3d ? v3d->layact : scene->lay;
			}
			
			ob->mode = 0;
			base->lay = ob->lay;
			base->object = ob;
			ob->id.us++;
			
			if (flag & FILE_AUTOSELECT) {
				base->flag |= SELECT;
				base->object->flag = base->flag;
				/* do NOT make base active here! screws up GUI stuff, if you want it do it on src/ level */
			}
		}
	}
	
	return id;
}

ID *BLO_library_append_named_part(Main *mainl, BlendHandle **bh, const char *idname, const int idcode)
{
	FileData *fd = (FileData*)(*bh);
	return append_named_part(mainl, fd, idname, idcode);
}

ID *BLO_library_append_named_part_ex(const bContext *C, Main *mainl, BlendHandle **bh, const char *idname, const int idcode, const short flag)
{
	FileData *fd = (FileData*)(*bh);
	return append_named_part_ex(C, mainl, fd, idname, idcode, flag);
}

static void append_id_part(FileData *fd, Main *mainvar, ID *id, ID **id_r)
{
	BHead *bhead;
	
	for (bhead = blo_firstbhead(fd); bhead; bhead = blo_nextbhead(fd, bhead)) {
		if (bhead->code == GS(id->name)) {
			
			if (strcmp(id->name, bhead_id_name(fd, bhead))==0) {
				id->flag &= ~LIB_READ;
				id->flag |= LIB_NEED_EXPAND;
//				printf("read lib block %s\n", id->name);
				read_libblock(fd, mainvar, bhead, id->flag, id_r);
				
				break;
			}
		}
		else if (bhead->code==ENDB)
			break;
	}
}

/* common routine to append/link something from a library */

static Main *library_append_begin(Main *mainvar, FileData **fd, const char *filepath)
{
	Main *mainl;

	(*fd)->mainlist = MEM_callocN(sizeof(ListBase), "FileData.mainlist");
	
	/* make mains */
	blo_split_main((*fd)->mainlist, mainvar);
	
	/* which one do we need? */
	mainl = blo_find_main(*fd, filepath, G.main->name);
	
	/* needed for do_version */
	mainl->versionfile = (*fd)->fileversion;
	read_file_version(*fd, mainl);
	
	return mainl;
}

Main *BLO_library_append_begin(Main *mainvar, BlendHandle **bh, const char *filepath)
{
	FileData *fd = (FileData*)(*bh);
	return library_append_begin(mainvar, &fd, filepath);
}


/* Context == NULL signifies not to do any scene manipulation */
static void library_append_end(const bContext *C, Main *mainl, FileData **fd, int idcode, short flag)
{
	Main *mainvar;
	Library *curlib;
	
	/* expander now is callback function */
	BLO_main_expander(expand_doit_library);
	
	/* make main consistent */
	BLO_expand_main(*fd, mainl);
	
	/* do this when expand found other libs */
	read_libraries(*fd, (*fd)->mainlist);
	
	curlib = mainl->curlib;
	
	/* make the lib path relative if required */
	if (flag & FILE_RELPATH) {
		/* use the full path, this could have been read by other library even */
		BLI_strncpy(curlib->name, curlib->filepath, sizeof(curlib->name));
		
		/* uses current .blend file as reference */
		BLI_path_rel(curlib->name, G.main->name);
	}
	
	blo_join_main((*fd)->mainlist);
	mainvar = (*fd)->mainlist->first;
	MEM_freeN((*fd)->mainlist);
	mainl = NULL; /* blo_join_main free's mainl, cant use anymore */
	
	lib_link_all(*fd, mainvar);
	lib_verify_nodetree(mainvar, FALSE);
	fix_relpaths_library(G.main->name, mainvar); /* make all relative paths, relative to the open blend file */
	
	if (C) {
		Scene *scene = CTX_data_scene(C);
		
		/* give a base to loose objects. If group append, do it for objects too */
		if (scene) {
			const short is_link = (flag & FILE_LINK) != 0;
			if (idcode == ID_SCE) {
				/* don't instance anything when linking in scenes, assume the scene its self instances the data */
			}
			else {
				give_base_to_objects(mainvar, scene, curlib, idcode, is_link, flag & FILE_ACTIVELAY);
				
				if (flag & FILE_GROUP_INSTANCE) {
					give_base_to_groups(mainvar, scene);
				}
			}
		}
		else {
			printf("library_append_end, scene is NULL (objects wont get bases)\n");
		}
	}
	/* has been removed... erm, why? s..ton) */
	/* 20040907: looks like they are give base already in append_named_part(); -Nathan L */
	/* 20041208: put back. It only linked direct, not indirect objects (ton) */
	
	/* patch to prevent switch_endian happens twice */
	if ((*fd)->flags & FD_FLAGS_SWITCH_ENDIAN) {
		blo_freefiledata(*fd);
		*fd = NULL;
	}
}

void BLO_library_append_end(const bContext *C, struct Main *mainl, BlendHandle **bh, int idcode, short flag)
{
	FileData *fd = (FileData*)(*bh);
	library_append_end(C, mainl, &fd, idcode, flag);
	*bh = (BlendHandle*)fd;
}

void *BLO_library_read_struct(FileData *fd, BHead *bh, const char *blockname)
{
	return read_struct(fd, bh, blockname);
}

/* ************* READ LIBRARY ************** */

static int mainvar_count_libread_blocks(Main *mainvar)
{
	ListBase *lbarray[MAX_LIBARRAY];
	int a, tot = 0;
	
	a = set_listbasepointers(mainvar, lbarray);
	while (a--) {
		ID *id;
		
		for (id = lbarray[a]->first; id; id = id->next) {
			if (id->flag & LIB_READ)
				tot++;
		}
	}
	return tot;
}

static void read_libraries(FileData *basefd, ListBase *mainlist)
{
	Main *mainl = mainlist->first;
	Main *mainptr;
	ListBase *lbarray[MAX_LIBARRAY];
	int a, do_it = TRUE;
	
	/* expander now is callback function */
	BLO_main_expander(expand_doit_library);
	
	while (do_it) {
		do_it = FALSE;
		
		/* test 1: read libdata */
		mainptr= mainl->next;
		while (mainptr) {
			int tot = mainvar_count_libread_blocks(mainptr);
			
			// printf("found LIB_READ %s\n", mainptr->curlib->name);
			if (tot) {
				FileData *fd = mainptr->curlib->filedata;
				
				if (fd == NULL) {
					
					/* printf and reports for now... its important users know this */
					
					/* if packed file... */
					if (mainptr->curlib->packedfile) {
						PackedFile *pf = mainptr->curlib->packedfile;
						
						BKE_reportf_wrap(basefd->reports, RPT_INFO, TIP_("Read packed library:  '%s'"),
						                 mainptr->curlib->name);
						fd = blo_openblendermemory(pf->data, pf->size, basefd->reports);
						
						
						/* needed for library_append and read_libraries */
						BLI_strncpy(fd->relabase, mainptr->curlib->filepath, sizeof(fd->relabase));
					}
					else {
						BKE_reportf_wrap(basefd->reports, RPT_INFO, TIP_("Read library:  '%s', '%s'"),
						                 mainptr->curlib->filepath, mainptr->curlib->name);
						fd = blo_openblenderfile(mainptr->curlib->filepath, basefd->reports);
					}
					/* allow typing in a new lib path */
					if (G.debug_value == -666) {
						while (fd == NULL) {
							char newlib_path[FILE_MAX] = {0};
							printf("Missing library...'\n");
							printf("	current file: %s\n", G.main->name);
							printf("	absolute lib: %s\n", mainptr->curlib->filepath);
							printf("	relative lib: %s\n", mainptr->curlib->name);
							printf("  enter a new path:\n");
							
							if (scanf("%s", newlib_path) > 0) {
								BLI_strncpy(mainptr->curlib->name, newlib_path, sizeof(mainptr->curlib->name));
								BLI_strncpy(mainptr->curlib->filepath, newlib_path, sizeof(mainptr->curlib->filepath));
								BLI_cleanup_path(G.main->name, mainptr->curlib->filepath);
								
								fd = blo_openblenderfile(mainptr->curlib->filepath, basefd->reports);

								if (fd) {
									fd->mainlist = mainlist;
									printf("found: '%s', party on macuno!\n", mainptr->curlib->filepath);
								}
							}
						}
					}
					
					if (fd) {
						/* share the mainlist, so all libraries are added immediately in a
						 * single list. it used to be that all FileData's had their own list,
						 * but with indirectly linking this meant we didn't catch duplicate
						 * libraries properly */
						fd->mainlist = mainlist;

						fd->reports = basefd->reports;
						
						if (fd->libmap)
							oldnewmap_free(fd->libmap);
						
						fd->libmap = oldnewmap_new();
						
						mainptr->curlib->filedata = fd;
						mainptr->versionfile=  fd->fileversion;
						
						/* subversion */
						read_file_version(fd, mainptr);
					}
					else {
						mainptr->curlib->filedata = NULL;
					}
					
					if (fd == NULL) {
						BKE_reportf_wrap(basefd->reports, RPT_WARNING, TIP_("Cannot find lib '%s'"),
						                 mainptr->curlib->filepath);
					}
				}
				if (fd) {
					do_it = TRUE;
					a = set_listbasepointers(mainptr, lbarray);
					while (a--) {
						ID *id = lbarray[a]->first;
						
						while (id) {
							ID *idn = id->next;
							if (id->flag & LIB_READ) {
								ID *realid = NULL;
								BLI_remlink(lbarray[a], id);
								
								append_id_part(fd, mainptr, id, &realid);
								if (!realid) {
									BKE_reportf_wrap(fd->reports, RPT_WARNING,
									                 TIP_("LIB ERROR: %s: '%s' missing from '%s'"),
									                 BKE_idcode_to_name(GS(id->name)),
									                 id->name + 2, mainptr->curlib->filepath);
								}
								
								change_idid_adr(mainlist, basefd, id, realid);
								
								MEM_freeN(id);
							}
							id = idn;
						}
					}
					
					BLO_expand_main(fd, mainptr);
				}
			}
			
			mainptr = mainptr->next;
		}
	}
	
	/* test if there are unread libblocks */
	for (mainptr = mainl->next; mainptr; mainptr = mainptr->next) {
		a = set_listbasepointers(mainptr, lbarray);
		while (a--) {
			ID *id, *idn = NULL;
			
			for (id = lbarray[a]->first; id; id = idn) {
				idn = id->next;
				if (id->flag & LIB_READ) {
					BLI_remlink(lbarray[a], id);
					BKE_reportf_wrap(basefd->reports, RPT_WARNING,
					                 TIP_("LIB ERROR: %s: '%s' unread lib block missing from '%s'"),
					                 BKE_idcode_to_name(GS(id->name)), id->name + 2, mainptr->curlib->filepath);
					change_idid_adr(mainlist, basefd, id, NULL);
					
					MEM_freeN(id);
				}
			}
		}
	}
	
	/* do versions, link, and free */
	for (mainptr = mainl->next; mainptr; mainptr = mainptr->next) {
		/* some mains still have to be read, then
		 * versionfile is still zero! */
		if (mainptr->versionfile) {
			if (mainptr->curlib->filedata) // can be zero... with shift+f1 append
				do_versions(mainptr->curlib->filedata, mainptr->curlib, mainptr);
			else
				do_versions(basefd, NULL, mainptr);
		}
		
		if (mainptr->curlib->filedata)
			lib_link_all(mainptr->curlib->filedata, mainptr);
		
		if (mainptr->curlib->filedata) blo_freefiledata(mainptr->curlib->filedata);
		mainptr->curlib->filedata = NULL;
	}
}


/* reading runtime */

BlendFileData *blo_read_blendafterruntime(int file, const char *name, int actualsize, ReportList *reports)
{
	BlendFileData *bfd = NULL;
	FileData *fd = filedata_new();
	fd->filedes = file;
	fd->buffersize = actualsize;
	fd->read = fd_read_from_file;
	
	/* needed for library_append and read_libraries */
	BLI_strncpy(fd->relabase, name, sizeof(fd->relabase));
	
	fd = blo_decode_and_check(fd, reports);
	if (!fd)
		return NULL;
	
	fd->reports = reports;
	bfd = blo_read_file_internal(fd, "");
	blo_freefiledata(fd);
	
	return bfd;
}
