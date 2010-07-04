/**
 * blenlib/BLI_storage_types.h
 *
 * Some types for dealing with directories
 *
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
 */
#ifndef BLI_UTIL_H
#define BLI_UTIL_H

#ifdef __cplusplus
extern "C" {
#endif

struct ListBase;
struct direntry;

char *BLI_gethome(void);
char *BLI_gethome_folder(char *folder_name, int flag);

/* BLI_gethome_folder flag */
#define BLI_GETHOME_LOCAL		1<<1 /* relative location for portable binaries */
#define BLI_GETHOME_SYSTEM		1<<2 /* system location, or set from the BLENDERPATH env variable (UNIX only) */
#define BLI_GETHOME_USER		1<<3 /* home folder ~/.blender */
#define BLI_GETHOME_ALL			(BLI_GETHOME_SYSTEM|BLI_GETHOME_LOCAL|BLI_GETHOME_USER)


#ifdef __APPLE__
typedef enum {
	BasePath_Temporary = 1,
	BasePath_BlenderShared,
	BasePath_BlenderUser,
	BasePath_ApplicationBundle
} basePathesTypes;

/**
 * Gets the base path. The path may not exist.
 * Note that return string must be copied as its persistence is not guaranteed
 *
 * @return base path of pathType
 */
const char* BLI_osx_getBasePath(basePathesTypes pathType);
#endif

char *BLI_get_folder(int folder_id, char *subfolder);
char *BLI_get_folder_create(int folder_id, char *subfolder);

/* folder_id */

/* general, will find baserd on user/local/system priority */
#define BLENDER_CONFIG				1
#define BLENDER_DATAFILES			2
#define BLENDER_SCRIPTS				3
#define BLENDER_PLUGINS				4
#define BLENDER_PYTHON				5

/* user-specific */
#define BLENDER_USER_CONFIG			31
#define BLENDER_USER_DATAFILES		32
#define BLENDER_USER_SCRIPTS		33
#define BLENDER_USER_PLUGINS		34

/* system */
#define BLENDER_SYSTEM_CONFIG		51	/* optional */
#define BLENDER_SYSTEM_DATAFILES	52
#define BLENDER_SYSTEM_SCRIPTS		53
#define BLENDER_SYSTEM_PLUGINS		54
#define BLENDER_SYSTEM_PYTHON		54

#define BLENDER_TEMP				80

#define BLENDER_USERFOLDER(id) (id >= BLENDER_USER_CONFIG && id <= BLENDER_USER_PLUGINS)

#define BLENDER_STARTUP_FILE	"startup.blend"
#define BLENDER_BOOKMARK_FILE	"bookmarks.txt"
#define BLENDER_HISTORY_FILE	"recent-files.txt"


void BLI_setenv(const char *env, const char *val);
void BLI_setenv_if_new(const char *env, const char* val);

void BLI_make_file_string(const char *relabase, char *string,  const char *dir, const char *file);
void BLI_make_exist(char *dir);
void BLI_make_existing_file(char *name);
void BLI_split_dirfile(const char *string, char *dir, char *file);
void BLI_join_dirfile(char *string, const char *dir, const char *file);
char *BLI_path_basename(char *path);
int BKE_rebase_path(char *abs, int abs_size, char *rel, int rel_size, const char *base_dir, const char *src_dir, const char *dest_dir);
void BLI_getlastdir(const char* dir, char *last, int maxlen);
int BLI_testextensie(const char *str, const char *ext);
int BLI_replace_extension(char *path, int maxlen, const char *ext);
void BLI_uniquename(struct ListBase *list, void *vlink, const char defname[], char delim, short name_offs, short len);
void BLI_newname(char * name, int add);
int BLI_stringdec(const char *string, char *head, char *start, unsigned short *numlen);
void BLI_stringenc(char *string, const char *head, const char *tail, unsigned short numlen, int pic);
void BLI_splitdirstring(char *di,char *fi);

/* make sure path separators conform to system one */
void BLI_clean(char *path);

/**
	 * dir can be any input, like from buttons, and this function
	 * converts it to a regular full path.
	 * Also removes garbage from directory paths, like /../ or double slashes etc 
	 */
void BLI_cleanup_file(const char *relabase, char *dir);
void BLI_cleanup_dir(const char *relabase, char *dir); /* same as above but adds a trailing slash */

/* go back one directory */
int BLI_parent_dir(char *path);

/* return whether directory is root and thus has no parent dir */
int BLI_has_parent(char *path);

	/**
	 * Blender's path code replacement function.
	 * Bases @a path strings leading with "//" by the
	 * directory @a basepath, and replaces instances of
	 * '#' with the @a framenum. Results are written
	 * back into @a path.
	 * 
	 * @a path The path to convert
	 * @a basepath The directory to base relative paths with.
	 * @a framenum The framenumber to replace the frame code with.
	 * @retval Returns true if the path was relative (started with "//").
	 */
int BLI_path_abs(char *path, const char *basepath);
int BLI_path_frame(char *path, int frame, int digits);
int BLI_path_frame_range(char *path, int sta, int end, int digits);
int BLI_path_cwd(char *path);

void BLI_path_rel(char *file, const char *relfile);

	/**
	 * Change every @a from in @a string into @a to. The
	 * result will be in @a string
	 *
	 * @a string The string to work on
	 * @a from The character to replace
	 * @a to The character to replace with
	 */
void BLI_char_switch(char *string, char from, char to);

/**
	 * Checks if name is a fully qualified filename to an executable.
	 * If not it searches $PATH for the file. On Windows it also
	 * adds the correct extension (.com .exe etc) from
	 * $PATHEXT if necessary. Also on Windows it translates
	 * the name to its 8.3 version to prevent problems with
	 * spaces and stuff. Final result is returned in fullname.
	 *
	 * @param fullname The full path and full name of the executable
	 * @param name The name of the executable (usually argv[0]) to be checked
	 */
void BLI_where_am_i(char *fullname, const char *name);

char *get_install_dir(void);
	/**
	 * Gets the temp directory when blender first runs.
	 * If the default path is not found, use try $TEMP
	 * 
	 * Also make sure the temp dir has a trailing slash
	 *
	 * @param fullname The full path to the temp directory
	 */
void BLI_where_is_temp(char *fullname, int usertemp);


#ifdef WITH_ICONV
void BLI_string_to_utf8(char *original, char *utf_8, const char *code);
#endif

#ifdef __cplusplus
}
#endif

#endif

