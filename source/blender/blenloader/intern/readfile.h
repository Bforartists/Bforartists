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
 * blenloader readfile private function prototypes
 */

/** \file
 * \ingroup blenloader
 */

#ifndef __READFILE_H__
#define __READFILE_H__

#include "DNA_sdna_types.h"
#include "DNA_space_types.h"
#include "DNA_windowmanager_types.h" /* for ReportType */
#include "zlib.h"

struct GSet;
struct IDNameLib_Map;
struct Key;
struct MemFile;
struct Object;
struct OldNewMap;
struct PartEff;
struct ReportList;
struct View3D;

typedef struct IDNameLib_Map IDNameLib_Map;

enum eFileDataFlag {
  FD_FLAGS_SWITCH_ENDIAN = 1 << 0,
  FD_FLAGS_FILE_POINTSIZE_IS_4 = 1 << 1,
  FD_FLAGS_POINTSIZE_DIFFERS = 1 << 2,
  FD_FLAGS_FILE_OK = 1 << 3,
  FD_FLAGS_NOT_MY_BUFFER = 1 << 4,
  /* XXX Unused in practice (checked once but never set). */
  FD_FLAGS_NOT_MY_LIBMAP = 1 << 5,
};

/* Disallow since it's 32bit on ms-windows. */
#ifdef __GNUC__
#  pragma GCC poison off_t
#endif

#if defined(_MSC_VER) || defined(__APPLE__) || defined(__HAIKU__) || defined(__NetBSD__)
typedef int64_t off64_t;
#endif

typedef int(FileDataReadFn)(struct FileData *filedata,
                            void *buffer,
                            unsigned int size,
                            bool *r_is_memchunk_identical);
typedef off64_t(FileDataSeekFn)(struct FileData *filedata, off64_t offset, int whence);

typedef struct FileData {
  /** Linked list of BHeadN's. */
  ListBase bhead_list;
  enum eFileDataFlag flags;
  bool is_eof;
  int buffersize;
  int64_t file_offset;

  FileDataReadFn *read;
  FileDataSeekFn *seek;

  /** Regular file reading. */
  int filedes;

  /** Variables needed for reading from memory / stream. */
  const char *buffer;
  /** Variables needed for reading from memfile (undo). */
  struct MemFile *memfile;
  /** Whether we are undoing (< 0) or redoing (> 0), used to choose which 'unchanged' flag to use
   * to detect unchanged data from memfile. */
  short undo_direction;

  /** Variables needed for reading from file. */
  gzFile gzfiledes;
  /** Gzip stream for memory decompression. */
  z_stream strm;

  /** Now only in use for library appending. */
  char relabase[FILE_MAX];

  /** General reading variables. */
  struct SDNA *filesdna;
  const struct SDNA *memsdna;
  /** Array of #eSDNA_StructCompare. */
  const char *compflags;

  int fileversion;
  /** Used to retrieve ID names from (bhead+1). */
  int id_name_offs;
  /** For do_versions patching. */
  int globalf, fileflags;

  /** Optionally skip some data-blocks when they're not needed. */
  eBLOReadSkip skip_flags;

  struct OldNewMap *datamap;
  struct OldNewMap *globmap;
  struct OldNewMap *libmap;
  struct OldNewMap *imamap;
  struct OldNewMap *movieclipmap;
  struct OldNewMap *scenemap;
  struct OldNewMap *soundmap;
  struct OldNewMap *volumemap;
  struct OldNewMap *packedmap;

  struct BHeadSort *bheadmap;
  int tot_bheadmap;

  /** See: #USE_GHASH_BHEAD. */
  struct GHash *bhead_idname_hash;

  ListBase *mainlist;
  /** Used for undo. */
  ListBase *old_mainlist;
  struct IDNameLib_Map *old_idmap;

  struct ReportList *reports;
} FileData;

#define SIZEOFBLENDERHEADER 12

/***/
struct Main;
void blo_join_main(ListBase *mainlist);
void blo_split_main(ListBase *mainlist, struct Main *main);

BlendFileData *blo_read_file_internal(FileData *fd, const char *filepath);

FileData *blo_filedata_from_file(const char *filepath, struct ReportList *reports);
FileData *blo_filedata_from_memory(const void *buffer, int buffersize, struct ReportList *reports);
FileData *blo_filedata_from_memfile(struct MemFile *memfile,
                                    const struct BlendFileReadParams *params,
                                    struct ReportList *reports);

void blo_clear_proxy_pointers_from_lib(struct Main *oldmain);
void blo_make_image_pointer_map(FileData *fd, struct Main *oldmain);
void blo_end_image_pointer_map(FileData *fd, struct Main *oldmain);
void blo_make_scene_pointer_map(FileData *fd, struct Main *oldmain);
void blo_end_scene_pointer_map(FileData *fd, struct Main *oldmain);
void blo_make_movieclip_pointer_map(FileData *fd, struct Main *oldmain);
void blo_end_movieclip_pointer_map(FileData *fd, struct Main *oldmain);
void blo_make_sound_pointer_map(FileData *fd, struct Main *oldmain);
void blo_end_sound_pointer_map(FileData *fd, struct Main *oldmain);
void blo_make_volume_pointer_map(FileData *fd, struct Main *oldmain);
void blo_end_volume_pointer_map(FileData *fd, struct Main *oldmain);
void blo_make_packed_pointer_map(FileData *fd, struct Main *oldmain);
void blo_end_packed_pointer_map(FileData *fd, struct Main *oldmain);
void blo_add_library_pointer_map(ListBase *old_mainlist, FileData *fd);
void blo_make_old_idmap_from_main(FileData *fd, struct Main *bmain);

void blo_filedata_free(FileData *fd);

BHead *blo_bhead_first(FileData *fd);
BHead *blo_bhead_next(FileData *fd, BHead *thisblock);
BHead *blo_bhead_prev(FileData *fd, BHead *thisblock);

const char *blo_bhead_id_name(const FileData *fd, const BHead *bhead);

/* do versions stuff */

void blo_reportf_wrap(struct ReportList *reports, ReportType type, const char *format, ...)
    ATTR_PRINTF_FORMAT(3, 4);

void blo_do_versions_dna(struct SDNA *sdna, const int versionfile, const int subversionfile);

void blo_do_versions_oldnewmap_insert(struct OldNewMap *onm,
                                      const void *oldaddr,
                                      void *newaddr,
                                      int nr);
void *blo_do_versions_newlibadr(struct FileData *fd, const void *lib, const void *adr);
void *blo_do_versions_newlibadr_us(struct FileData *fd, const void *lib, const void *adr);

struct PartEff *blo_do_version_give_parteff_245(struct Object *ob);
void blo_do_version_old_trackto_to_constraints(struct Object *ob);
void blo_do_versions_view3d_split_250(struct View3D *v3d, struct ListBase *regions);
void blo_do_versions_key_uidgen(struct Key *key);

void blo_do_versions_pre250(struct FileData *fd, struct Library *lib, struct Main *bmain);
void blo_do_versions_250(struct FileData *fd, struct Library *lib, struct Main *bmain);
void blo_do_versions_260(struct FileData *fd, struct Library *lib, struct Main *bmain);
void blo_do_versions_270(struct FileData *fd, struct Library *lib, struct Main *bmain);
void blo_do_versions_280(struct FileData *fd, struct Library *lib, struct Main *bmain);
void blo_do_versions_290(struct FileData *fd, struct Library *lib, struct Main *bmain);
void blo_do_versions_cycles(struct FileData *fd, struct Library *lib, struct Main *bmain);

void do_versions_after_linking_250(struct Main *bmain);
void do_versions_after_linking_260(struct Main *bmain);
void do_versions_after_linking_270(struct Main *bmain);
void do_versions_after_linking_280(struct Main *bmain, struct ReportList *reports);
void do_versions_after_linking_290(struct Main *bmain, struct ReportList *reports);
void do_versions_after_linking_cycles(struct Main *bmain);

#endif
