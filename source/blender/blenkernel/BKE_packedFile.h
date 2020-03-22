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
#ifndef __BKE_PACKEDFILE_H__
#define __BKE_PACKEDFILE_H__

/** \file
 * \ingroup bke
 */

#ifdef __cplusplus
extern "C" {
#endif

#define RET_OK 0
#define RET_ERROR 1

struct ID;
struct Image;
struct Main;
struct PackedFile;
struct ReportList;
struct VFont;
struct Volume;
struct bSound;

enum ePF_FileCompare {
  PF_CMP_EQUAL = 0,
  PF_CMP_DIFFERS = 1,
  PF_CMP_NOFILE = 2,
};

enum ePF_FileStatus {
  PF_WRITE_ORIGINAL = 3,
  PF_WRITE_LOCAL = 4,
  PF_USE_LOCAL = 5,
  PF_USE_ORIGINAL = 6,
  PF_KEEP = 7,
  PF_REMOVE = 8,

  PF_ASK = 10,
};

/* pack */
struct PackedFile *BKE_packedfile_duplicate(const struct PackedFile *pf_src);
struct PackedFile *BKE_packedfile_new(struct ReportList *reports,
                                      const char *filename,
                                      const char *relabase);
struct PackedFile *BKE_packedfile_new_from_memory(void *mem, int memlen);

void BKE_packedfile_pack_all(struct Main *bmain, struct ReportList *reports, bool verbose);
void BKE_packedfile_pack_all_libraries(struct Main *bmain, struct ReportList *reports);

/* unpack */
char *BKE_packedfile_unpack_to_file(struct ReportList *reports,
                                    const char *ref_file_name,
                                    const char *abs_name,
                                    const char *local_name,
                                    struct PackedFile *pf,
                                    enum ePF_FileStatus how);
int BKE_packedfile_unpack_vfont(struct Main *bmain,
                                struct ReportList *reports,
                                struct VFont *vfont,
                                enum ePF_FileStatus how);
int BKE_packedfile_unpack_sound(struct Main *bmain,
                                struct ReportList *reports,
                                struct bSound *sound,
                                enum ePF_FileStatus how);
int BKE_packedfile_unpack_image(struct Main *bmain,
                                struct ReportList *reports,
                                struct Image *ima,
                                enum ePF_FileStatus how);
int BKE_packedfile_unpack_volume(struct Main *bmain,
                                 struct ReportList *reports,
                                 struct Volume *volume,
                                 enum ePF_FileStatus how);
void BKE_packedfile_unpack_all(struct Main *bmain,
                               struct ReportList *reports,
                               enum ePF_FileStatus how);
int BKE_packedfile_unpack_all_libraries(struct Main *bmain, struct ReportList *reports);

int BKE_packedfile_write_to_file(struct ReportList *reports,
                                 const char *ref_file_name,
                                 const char *filename,
                                 struct PackedFile *pf,
                                 const bool guimode);

/* free */
void BKE_packedfile_free(struct PackedFile *pf);

/* info */
int BKE_packedfile_count_all(struct Main *bmain);
enum ePF_FileCompare BKE_packedfile_compare_to_file(const char *ref_file_name,
                                                    const char *filename,
                                                    struct PackedFile *pf);

/* read */
int BKE_packedfile_seek(struct PackedFile *pf, int offset, int whence);
void BKE_packedfile_rewind(struct PackedFile *pf);
int BKE_packedfile_read(struct PackedFile *pf, void *data, int size);

/* ID should be not NULL, return 1 if there's a packed file */
bool BKE_packedfile_id_check(struct ID *id);
/* ID should be not NULL, throws error when ID is Library */
void BKE_packedfile_id_unpack(struct Main *bmain,
                              struct ID *id,
                              struct ReportList *reports,
                              enum ePF_FileStatus how);

#ifdef __cplusplus
}
#endif

#endif
