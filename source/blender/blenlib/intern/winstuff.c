/**
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 * Windows-posix compatibility layer, windows-specific functions.
 */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifdef WIN32

#include <stdlib.h>
#include <stdio.h>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_util.h"
#define WIN32_SKIP_HKEY_PROTECTION		// need to use HKEY
#include "BLI_winstuff.h"

#include "BKE_utildefines.h" /* FILE_MAXDIR + FILE_MAXFILE */

int BLI_getInstallationDir( char * str ) {
	char dir[FILE_MAXDIR];
	char file[FILE_MAXFILE];
	int a;
	
	GetModuleFileName(NULL,str,FILE_MAXDIR+FILE_MAXFILE);
	BLI_split_dirfile(str,dir,file); /* shouldn't be relative */
	a = strlen(dir);
	if(dir[a-1] == '\\') dir[a-1]=0;
	
	strcpy(str,dir);
	
	return 1;
}


void RegisterBlendExtension(char * str) {
	LONG lresult;
	HKEY hkey = 0;
	DWORD dwd = 0;
	char buffer[128];
	
	lresult = RegCreateKeyEx(HKEY_CLASSES_ROOT, "blendfile\\shell\\open\\command", 0,
		"", REG_OPTION_NON_VOLATILE, KEY_ALL_ACCESS, NULL, &hkey, &dwd);

	if (lresult == ERROR_SUCCESS) {
		sprintf(buffer, "\"%s\" \"%%1\"", str);
		lresult = RegSetValueEx(hkey, NULL, 0, REG_SZ, buffer, strlen(buffer) + 1);
		RegCloseKey(hkey);
	}

	lresult = RegCreateKeyEx(HKEY_CLASSES_ROOT, "blendfile\\DefaultIcon", 0,
		"", REG_OPTION_NON_VOLATILE, KEY_ALL_ACCESS, NULL, &hkey, &dwd);

	if (lresult == ERROR_SUCCESS) {
		sprintf(buffer, "\"%s\",1", str);
		lresult = RegSetValueEx(hkey, NULL, 0, REG_SZ, buffer, strlen(buffer) + 1);
		RegCloseKey(hkey);
	}

	lresult = RegCreateKeyEx(HKEY_CLASSES_ROOT, ".blend", 0,
		"", REG_OPTION_NON_VOLATILE, KEY_ALL_ACCESS, NULL, &hkey, &dwd);

	if (lresult == ERROR_SUCCESS) {
		sprintf(buffer, "%s", "blendfile");
		lresult = RegSetValueEx(hkey, NULL, 0, REG_SZ, buffer, strlen(buffer) + 1);
		RegCloseKey(hkey);
	}
}

DIR *opendir (const char *path) {
	if (GetFileAttributes(path) & FILE_ATTRIBUTE_DIRECTORY) {
		DIR *newd= MEM_mallocN(sizeof(DIR), "opendir");

		newd->handle = INVALID_HANDLE_VALUE;
		sprintf(newd->path, "%s\\*",path);
		
		newd->direntry.d_ino= 0;
		newd->direntry.d_off= 0;
		newd->direntry.d_reclen= 0;
		newd->direntry.d_name= NULL;
		
		return newd;
	} else {
		return NULL;
	}
}

struct dirent *readdir(DIR *dp) {
	if (dp->direntry.d_name) {
		MEM_freeN(dp->direntry.d_name);
		dp->direntry.d_name= NULL;
	}
		
	if (dp->handle==INVALID_HANDLE_VALUE) {
		dp->handle= FindFirstFile(dp->path, &(dp->data));
		if (dp->handle==INVALID_HANDLE_VALUE)
			return NULL;
			
		dp->direntry.d_name= BLI_strdup(dp->data.cFileName);

		return &dp->direntry;
	} else if (FindNextFile (dp->handle, &(dp->data))) {
		dp->direntry.d_name= BLI_strdup(dp->data.cFileName);

		return &dp->direntry;
	} else {
		return NULL;
	}
}

int closedir (DIR *dp) {
	if (dp->direntry.d_name) MEM_freeN(dp->direntry.d_name);
	if (dp->handle!=INVALID_HANDLE_VALUE) FindClose(dp->handle);

	MEM_freeN(dp);
	
	return 0;
}

void get_default_root(char* root) {
	DWORD tmp;
	int i;

	tmp= GetLogicalDrives();

	for (i=2; i < 26; i++) {
		if ((tmp>>i) & 1) {
			root[0] = 'a'+i;
			root[1] = ':';
			root[2] = '\\';
			root[3] = '\0';
			if (GetFileAttributes(root) != 0xFFFFFFFF)
				return;			
		}
	}

	printf("ERROR in 'get_default_root': can't find a valid drive!");
	root[0] = 'c';
	root[1] = ':';
	root[2] = '\\';
	root[3] = '\0';
}

#else

static void BLI_WINSTUFF_C_IS_EMPTY_FOR_UNIX(void) 
{
  /*intentionally empty*/
}

#endif
