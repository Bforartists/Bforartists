/**
 * $Id: wm_files.c
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation 2007
 *
 * ***** END GPL LICENSE BLOCK *****
 */

	/* placed up here because of crappy
	 * winsock stuff.
	 */
#include <stdio.h>
#include <string.h>

#ifdef WIN32
#include <windows.h> /* need to include windows.h so _WIN32_IE is defined  */
#ifndef _WIN32_IE
#define _WIN32_IE 0x0400 /* minimal requirements for SHGetSpecialFolderPath on MINGW MSVC has this defined already */
#endif
#include <shlobj.h> /* for SHGetSpecialFolderPath, has to be done before BLI_winstuff because 'near' is disabled through BLI_windstuff */
#include "BLI_winstuff.h"
#include <process.h> /* getpid */
#else
#include <unistd.h> /* getpid */
#endif

#include "MEM_guardedalloc.h"
#include "MEM_CacheLimiterC-Api.h"

#include "BLI_blenlib.h"
#include "BLI_linklist.h"

#include "DNA_anim_types.h"
#include "DNA_ipo_types.h" // XXX old animation system
#include "DNA_object_types.h"
#include "DNA_space_types.h"
#include "DNA_userdef_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_windowmanager_types.h"

#include "BKE_blender.h"
#include "BKE_context.h"
#include "BKE_DerivedMesh.h"
#include "BKE_exotic.h"
#include "BKE_font.h"
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_packedFile.h"
#include "BKE_report.h"
#include "BKE_texture.h"
#include "BKE_utildefines.h"

#include "BLO_readfile.h"
#include "BLO_writefile.h"

#include "ED_datafiles.h"
#include "ED_screen.h"
#include "ED_util.h"

#include "UI_interface.h"

// XXX #include "BPY_extern.h"

#include "WM_api.h"
#include "WM_types.h"
#include "wm.h"

/***/

/* define for setting colors in theme below */
#define SETCOL(col, r, g, b, a)  {col[0]=r; col[1]=g; col[2]= b; col[3]= a;}

/* patching UserDef struct and Themes */
static void init_userdef_themes(void)
{
	// sets themes, fonts, .. from userdef
	UI_init_userdef();
	
//	countall();
	
	/* the UserDef struct is not corrected with do_versions() .... ugh! */
	if(U.wheellinescroll == 0) U.wheellinescroll = 3;
	if(U.menuthreshold1==0) {
		U.menuthreshold1= 5;
		U.menuthreshold2= 2;
	}
	if(U.tb_leftmouse==0) {
		U.tb_leftmouse= 5;
		U.tb_rightmouse= 5;
	}
	if(U.mixbufsize==0) U.mixbufsize= 2048;
	if (BLI_streq(U.tempdir, "/")) {
		char *tmp= getenv("TEMP");
		
		strcpy(U.tempdir, tmp?tmp:"/tmp/");
	}
	if (U.savetime <= 0) {
		U.savetime = 1;
// XXX		error(".B.blend is buggy, please consider removing it.\n");
	}
	/* transform widget settings */
	if(U.tw_hotspot==0) {
		U.tw_hotspot= 14;
		U.tw_size= 20;			// percentage of window size
		U.tw_handlesize= 16;	// percentage of widget radius
	}
	if(U.pad_rot_angle==0)
		U.pad_rot_angle= 15;
	
	if(U.flag & USER_CUSTOM_RANGE) 
		vDM_ColorBand_store(&U.coba_weight); /* signal for derivedmesh to use colorband */
	
	if (G.main->versionfile <= 191) {
		strcpy(U.plugtexdir, U.textudir);
		strcpy(U.sounddir, "/");
	}
	
	/* patch to set Dupli Armature */
	if (G.main->versionfile < 220) {
		U.dupflag |= USER_DUP_ARM;
	}
	
	/* userdef new option */
	if (G.main->versionfile <= 222) {
		U.vrmlflag= USER_VRML_LAYERS;
	}
	
	/* added seam, normal color, undo */
	if (G.main->versionfile <= 234) {
		bTheme *btheme;
		
		U.uiflag |= USER_GLOBALUNDO;
		if (U.undosteps==0) U.undosteps=32;
		
		for(btheme= U.themes.first; btheme; btheme= btheme->next) {
			/* check for alpha==0 is safe, then color was never set */
			if(btheme->tv3d.edge_seam[3]==0) {
				SETCOL(btheme->tv3d.edge_seam, 230, 150, 50, 255);
			}
			if(btheme->tv3d.normal[3]==0) {
				SETCOL(btheme->tv3d.normal, 0x22, 0xDD, 0xDD, 255);
			}
			if(btheme->tv3d.face_dot[3]==0) {
				SETCOL(btheme->tv3d.face_dot, 255, 138, 48, 255);
				btheme->tv3d.facedot_size= 4;
			}
		}
	}
	if (G.main->versionfile <= 235) {
		/* illegal combo... */
		if (U.flag & USER_LMOUSESELECT) 
			U.flag &= ~USER_TWOBUTTONMOUSE;
	}
	if (G.main->versionfile <= 236) {
		bTheme *btheme;
		/* new space type */
		for(btheme= U.themes.first; btheme; btheme= btheme->next) {
			/* check for alpha==0 is safe, then color was never set */
			if(btheme->ttime.back[3]==0) {
				btheme->ttime = btheme->tsnd;	// copy from sound
			}
			if(btheme->text.syntaxn[3]==0) {
				SETCOL(btheme->text.syntaxn,	0, 0, 200, 255);	/* Numbers  Blue*/
				SETCOL(btheme->text.syntaxl,	100, 0, 0, 255);	/* Strings  red */
				SETCOL(btheme->text.syntaxc,	0, 100, 50, 255);	/* Comments greenish */
				SETCOL(btheme->text.syntaxv,	95, 95, 0, 255);	/* Special */
				SETCOL(btheme->text.syntaxb,	128, 0, 80, 255);	/* Builtin, red-purple */
			}
		}
	}
	if (G.main->versionfile <= 237) {
		bTheme *btheme;
		/* bone colors */
		for(btheme= U.themes.first; btheme; btheme= btheme->next) {
			/* check for alpha==0 is safe, then color was never set */
			if(btheme->tv3d.bone_solid[3]==0) {
				SETCOL(btheme->tv3d.bone_solid, 200, 200, 200, 255);
				SETCOL(btheme->tv3d.bone_pose, 80, 200, 255, 80);
			}
		}
	}
	if (G.main->versionfile <= 238) {
		bTheme *btheme;
		/* bone colors */
		for(btheme= U.themes.first; btheme; btheme= btheme->next) {
			/* check for alpha==0 is safe, then color was never set */
			if(btheme->tnla.strip[3]==0) {
				SETCOL(btheme->tnla.strip_select, 	0xff, 0xff, 0xaa, 255);
				SETCOL(btheme->tnla.strip, 0xe4, 0x9c, 0xc6, 255);
			}
		}
	}
	if (G.main->versionfile <= 239) {
		bTheme *btheme;
		
		for(btheme= U.themes.first; btheme; btheme= btheme->next) {
			/* Lamp theme, check for alpha==0 is safe, then color was never set */
			if(btheme->tv3d.lamp[3]==0) {
				SETCOL(btheme->tv3d.lamp, 	0, 0, 0, 40);
/* TEMPORAL, remove me! (ton) */				
				U.uiflag |= USER_PLAINMENUS;
			}
			
			/* check for text field selection highlight, set it to text editor highlight by default */
			if(btheme->tui.textfield_hi[3]==0) {
				SETCOL(btheme->tui.textfield_hi, 	
					btheme->text.shade2[0], 
					btheme->text.shade2[1], 
					btheme->text.shade2[2],
					255);
			}
		}
		if(U.obcenter_dia==0) U.obcenter_dia= 6;
	}
	if (G.main->versionfile <= 241) {
		bTheme *btheme;
		for(btheme= U.themes.first; btheme; btheme= btheme->next) {
			/* Node editor theme, check for alpha==0 is safe, then color was never set */
			if(btheme->tnode.syntaxn[3]==0) {
				/* re-uses syntax color storage */
				btheme->tnode= btheme->tv3d;
				SETCOL(btheme->tnode.edge_select, 255, 255, 255, 255);
				SETCOL(btheme->tnode.syntaxl, 150, 150, 150, 255);	/* TH_NODE, backdrop */
				SETCOL(btheme->tnode.syntaxn, 129, 131, 144, 255);	/* in/output */
				SETCOL(btheme->tnode.syntaxb, 127,127,127, 255);	/* operator */
				SETCOL(btheme->tnode.syntaxv, 142, 138, 145, 255);	/* generator */
				SETCOL(btheme->tnode.syntaxc, 120, 145, 120, 255);	/* group */
			}
			/* Group theme colors */
			if(btheme->tv3d.group[3]==0) {
				SETCOL(btheme->tv3d.group, 0x10, 0x40, 0x10, 255);
				SETCOL(btheme->tv3d.group_active, 0x66, 0xFF, 0x66, 255);
			}
			/* Sequence editor theme*/
			if(btheme->tseq.movie[3]==0) {
				SETCOL(btheme->tseq.movie, 	81, 105, 135, 255);
				SETCOL(btheme->tseq.image, 	109, 88, 129, 255);
				SETCOL(btheme->tseq.scene, 	78, 152, 62, 255);
				SETCOL(btheme->tseq.audio, 	46, 143, 143, 255);
				SETCOL(btheme->tseq.effect, 	169, 84, 124, 255);
				SETCOL(btheme->tseq.plugin, 	126, 126, 80, 255);
				SETCOL(btheme->tseq.transition, 162, 95, 111, 255);
				SETCOL(btheme->tseq.meta, 	109, 145, 131, 255);
			}
			if(!(btheme->tui.iconfile)) {
				BLI_strncpy(btheme->tui.iconfile, "", sizeof(btheme->tui.iconfile));
			}
		}
		
		/* set defaults for 3D View rotating axis indicator */ 
		/* since size can't be set to 0, this indicates it's not saved in .B.blend */
		if (U.rvisize == 0) {
			U.rvisize = 15;
			U.rvibright = 8;
			U.uiflag |= USER_SHOW_ROTVIEWICON;
		}
		
	}
	if (G.main->versionfile <= 242) {
		bTheme *btheme;
		
		for(btheme= U.themes.first; btheme; btheme= btheme->next) {
			/* long keyframe color */
			/* check for alpha==0 is safe, then color was never set */
			if(btheme->tact.strip[3]==0) {
				SETCOL(btheme->tv3d.edge_sharp, 255, 32, 32, 255);
				SETCOL(btheme->tact.strip_select, 	0xff, 0xff, 0xaa, 204);
				SETCOL(btheme->tact.strip, 0xe4, 0x9c, 0xc6, 204);
			}
			
			/* IPO-Editor - Vertex Size*/
			if(btheme->tipo.vertex_size == 0) {
				btheme->tipo.vertex_size= 3;
			}
		}
	}
	if (G.main->versionfile <= 243) {
		/* set default number of recently-used files (if not set) */
		if (U.recent_files == 0) U.recent_files = 10;
	}
	if (G.main->versionfile < 245 || (G.main->versionfile == 245 && G.main->subversionfile < 3)) {
		bTheme *btheme;
		for(btheme= U.themes.first; btheme; btheme= btheme->next) {
			SETCOL(btheme->tv3d.editmesh_active, 255, 255, 255, 128);
		}
		if(U.coba_weight.tot==0)
			init_colorband(&U.coba_weight, 1);
	}
	if ((G.main->versionfile < 245) || (G.main->versionfile == 245 && G.main->subversionfile < 11)) {
		bTheme *btheme;
		for (btheme= U.themes.first; btheme; btheme= btheme->next) {
			/* these should all use the same colour */
			SETCOL(btheme->tv3d.cframe, 0x60, 0xc0, 0x40, 255);
			SETCOL(btheme->tipo.cframe, 0x60, 0xc0, 0x40, 255);
			SETCOL(btheme->tact.cframe, 0x60, 0xc0, 0x40, 255);
			SETCOL(btheme->tnla.cframe, 0x60, 0xc0, 0x40, 255);
			SETCOL(btheme->tseq.cframe, 0x60, 0xc0, 0x40, 255);
			SETCOL(btheme->tsnd.cframe, 0x60, 0xc0, 0x40, 255);
			SETCOL(btheme->ttime.cframe, 0x60, 0xc0, 0x40, 255);
		}
	}
	if ((G.main->versionfile < 248) || (G.main->versionfile == 248 && G.main->subversionfile < 3)) {
		bTheme *btheme;
		
		/* adjust themes */
		for (btheme= U.themes.first; btheme; btheme= btheme->next) {
			/* DopeSheet - (Object) Channel color */
			SETCOL(btheme->tact.ds_channel, 0x36, 0x13, 0xca, 255);
			SETCOL(btheme->tact.ds_subchannel, 0x60, 0x43, 0xd2, 255);
		}
		
		/* adjust grease-pencil distances */
		U.gp_manhattendist= 1;
		U.gp_euclideandist= 2;
		
		/* adjust default interpolation for new IPO-curves */
		U.ipo_new= BEZT_IPO_BEZ;
	}
	if (G.main->versionfile < 250) {
		bTheme *btheme;

		/* this was not properly initialized in 2.45 */
		for(btheme= U.themes.first; btheme; btheme= btheme->next) {
			if(btheme->tima.face_dot[3]==0) {
				SETCOL(btheme->tima.editmesh_active, 255, 255, 255, 128);
				SETCOL(btheme->tima.face_dot, 255, 133, 0, 255);
				btheme->tima.facedot_size= 2;
			}
		}
	}
	
	/* GL Texture Garbage Collection (variable abused above!) */
	if (U.textimeout == 0) {
		U.texcollectrate = 60;
		U.textimeout = 120;
	}
	if (U.memcachelimit <= 0) {
		U.memcachelimit = 32;
	}
	if (U.frameserverport == 0) {
		U.frameserverport = 8080;
	}

	MEM_CacheLimiter_set_maximum(U.memcachelimit * 1024 * 1024);
	
	/* funny name, but it is GE stuff, moves userdef stuff to engine */
// XXX	space_set_commmandline_options();
	/* this timer uses U */
// XXX	reset_autosave();

}

/* To be able to read files without windows closing, opening, moving 
   we try to prepare for worst case:
   - active window gets active screen from file 
   - restoring the screens from non-active windows 
   Best case is all screens match, in that case they get assigned to proper window  
*/
static void wm_window_match_init(bContext *C, ListBase *wmlist)
{
	wmWindowManager *wm= G.main->wm.first;
	wmWindow *win;
	
	*wmlist= G.main->wm;
	G.main->wm.first= G.main->wm.last= NULL;
	
	/* first wrap up running stuff */
	/* code copied from wm_init_exit.c */
	for(wm= wmlist->first; wm; wm= wm->id.next) {
		for(win= wm->windows.first; win; win= win->next) {
		
			CTX_wm_window_set(C, win);	/* needed by operator close callbacks */
			ED_screen_exit(C, win, win->screen);
		}
	}
	
	ED_editors_exit(C);
	
return;	
	if(wm==NULL) return;
	if(G.fileflags & G_FILE_NO_UI) return;
	
	/* we take apart the used screens from non-active window */
	for(win= wm->windows.first; win; win= win->next) {
		BLI_strncpy(win->screenname, win->screen->id.name, MAX_ID_NAME);
		if(win!=wm->winactive) {
			BLI_remlink(&G.main->screen, win->screen);
			//BLI_addtail(screenbase, win->screen);
		}
	}
}

/* match old WM with new, 4 cases:
  1- no current wm, no read wm: make new default
  2- no current wm, but read wm: that's OK, do nothing
  3- current wm, but not in file: try match screen names
  4- current wm, and wm in file: try match ghostwin 

*/
static void wm_window_match_do(bContext *C, ListBase *oldwmlist)
{
	wmWindowManager *oldwm, *wm;
	wmWindow *oldwin, *win;
	
	/* cases 1 and 2 */
	if(oldwmlist->first==NULL) {
		if(G.main->wm.first); /* nothing todo */
		else
			wm_add_default(C);
	}
	else {
		/* cases 3 and 4 */
		
		/* we've read file without wm... */
		if(G.main->wm.first==NULL) {
			/* match oldwm to new dbase, only old files */
			
			for(wm= oldwmlist->first; wm; wm= wm->id.next) {
				for(win= wm->windows.first; win; win= win->next) {
					win->screen= (bScreen *)find_id("SR", win->screenname);

					if(win->screen==NULL)
						win->screen= ED_screen_duplicate(win, CTX_wm_screen(C)); /* active screen */
							
					if(win->screen->winid==0)
						win->screen->winid= win->winid;
				}
			}
			/* XXX still solve, case where multiple windows open */
			
			G.main->wm= *oldwmlist;
		}
		else {
			/* what if old was 3, and loaded 1? */
			/* this code could move to setup_appdata */
			oldwm= oldwmlist->first;
			wm= G.main->wm.first;
			/* only first wm in list has ghostwins */
			for(win= wm->windows.first; win; win= win->next) {
				for(oldwin= oldwm->windows.first; oldwin; oldwin= oldwin->next) {
					
					if(oldwin->winid == win->winid ) {
						win->ghostwin= oldwin->ghostwin;
						oldwin->ghostwin= NULL;
					}
				}
			}
			wm_close_and_free_all(C, oldwmlist);
		}
	}
}

void WM_read_file(bContext *C, char *name, ReportList *reports)
{
	int retval;

	/* first try to append data from exotic file formats... */
	/* it throws error box when file doesnt exist and returns -1 */
	/* note; it should set some error message somewhere... (ton) */
	retval= BKE_read_exotic(CTX_data_scene(C), name);
	
	/* we didn't succeed, now try to read Blender file */
	if (retval== 0) {
		ListBase wmbase;

		/* put aside screens to match with persistant windows later */
		/* also exit screens and editors */
		wm_window_match_init(C, &wmbase); 
		
		retval= BKE_read_file(C, name, NULL, reports);

		/* match the read WM with current WM */
		wm_window_match_do(C, &wmbase); 
		
// XXX		mainwindow_set_filename_to_title(G.main->name);
//		countall(); <-- will be listener
// XXX		sound_initialize_sounds();

//		winqueue_break= 1;	/* leave queues everywhere */

// XXX		if(retval==2) init_userdef_themes();	// in case a userdef is read from regular .blend
		
		if (retval!=0) G.relbase_valid = 1;

// XXX		undo_editmode_clear();
		BKE_reset_undo();
		BKE_write_undo(C, "original");	/* save current state */

//		refresh_interface_font();
	}
//	else if(retval==1)
// XXX		BIF_undo_push("Import file");
	else if(retval == -1) {
		if(reports && reports->list.first == NULL)
			BKE_report(reports, RPT_ERROR, "Cannot read file.");
	}
}


/* called on startup,  (context entirely filled with NULLs) */
/* or called for 'Erase All' */
int WM_read_homefile(bContext *C, int from_memory)
{
	ListBase wmbase;
	char tstr[FILE_MAXDIR+FILE_MAXFILE], scestr[FILE_MAXDIR];
	char *home= BLI_gethome();
	int success;
	
	BLI_clean(home);
	
	free_ttfont(); /* still weird... what does it here? */
		
	G.relbase_valid = 0;
	if (!from_memory) BLI_make_file_string(G.sce, tstr, home, ".B.blend");
	strcpy(scestr, G.sce);	/* temporary store */
	
	/* prevent loading no UI */
	G.fileflags &= ~G_FILE_NO_UI;
	
	/* put aside screens to match with persistant windows later */
	wm_window_match_init(C, &wmbase); 
	
	if (!from_memory && BLI_exists(tstr)) {
		success = BKE_read_file(C, tstr, NULL, NULL);
	} else {
		success = BKE_read_file_from_memory(C, datatoc_B_blend, datatoc_B_blend_size, NULL, NULL);
	}
	
	/* match the read WM with current WM */
	wm_window_match_do(C, &wmbase); 
	
	strcpy(G.sce, scestr); /* restore */

	init_userdef_themes();
	
	/* XXX */
	G.save_over = 0;	// start with save preference untitled.blend
	G.fileflags &= ~G_FILE_AUTOPLAY;	/*  disable autoplay in .B.blend... */
//	mainwindow_set_filename_to_title("");	// empty string re-initializes title to "Blender"

#ifdef INTERNATIONAL
// XXX	read_languagefile();
#endif
	
//	refresh_interface_font();
	
//	undo_editmode_clear();
	BKE_reset_undo();
	BKE_write_undo(C, "original");	/* save current state */
	
	return success;
}


static void get_autosave_location(char buf[FILE_MAXDIR+FILE_MAXFILE])
{
	char pidstr[32];
#ifdef WIN32
	char subdir[9];
	char savedir[FILE_MAXDIR];
#endif

	sprintf(pidstr, "%d.blend", abs(getpid()));
	
#ifdef WIN32
	if (!BLI_exists(U.tempdir)) {
		BLI_strncpy(subdir, "autosave", sizeof(subdir));
		BLI_make_file_string("/", savedir, BLI_gethome(), subdir);
		
		/* create a new autosave dir
		 * function already checks for existence or not */
		BLI_recurdir_fileops(savedir);
	
		BLI_make_file_string("/", buf, savedir, pidstr);
		return;
	}
#endif
	
	BLI_make_file_string("/", buf, U.tempdir, pidstr);
}

void WM_read_autosavefile(bContext *C)
{
	char tstr[FILE_MAX], scestr[FILE_MAX];
	int save_over;

	BLI_strncpy(scestr, G.sce, FILE_MAX);	/* temporal store */
	
	get_autosave_location(tstr);

	save_over = G.save_over;
	BKE_read_file(C, tstr, NULL, NULL);
	G.save_over = save_over;
	BLI_strncpy(G.sce, scestr, FILE_MAX);
}


void read_Blog(void)
{
	char name[FILE_MAX], filename[FILE_MAX];
	LinkNode *l, *lines;
	struct RecentFile *recent;
	char *line;
	int num;

	BLI_make_file_string("/", name, BLI_gethome(), ".Blog");
	lines= BLI_read_file_as_lines(name);

	G.recent_files.first = G.recent_files.last = NULL;

	/* read list of recent opend files from .Blog to memory */
	for (l= lines, num= 0; l && (num<U.recent_files); l= l->next, num++) {
		line = l->link;
		if (!BLI_streq(line, "")) {
			if (num==0) 
				strcpy(G.sce, line);
			
			recent = (RecentFile*)MEM_mallocN(sizeof(RecentFile),"RecentFile");
			BLI_addtail(&(G.recent_files), recent);
			recent->filename = (char*)MEM_mallocN(sizeof(char)*(strlen(line)+1), "name of file");
			recent->filename[0] = '\0';
			
			strcpy(recent->filename, line);
		}
	}

	if(G.sce[0] == 0)
		BLI_make_file_string("/", G.sce, BLI_gethome(), "untitled.blend");
	
	BLI_free_file_lines(lines);

#ifdef WIN32
	/* Add the drive names to the listing */
	{
		__int64 tmp;
		char folder[MAX_PATH];
		char tmps[4];
		int i;
			
		tmp= GetLogicalDrives();
		
		for (i=2; i < 26; i++) {
			if ((tmp>>i) & 1) {
				tmps[0]='a'+i;
				tmps[1]=':';
				tmps[2]='\\';
				tmps[3]=0;
				
// XX				fsmenu_insert_entry(tmps, 0, 0);
			}
		}

		/* Adding Desktop and My Documents */
// XXX		fsmenu_append_separator();

		SHGetSpecialFolderPath(0, folder, CSIDL_PERSONAL, 0);
// XXX		fsmenu_insert_entry(folder, 0, 0);
		SHGetSpecialFolderPath(0, folder, CSIDL_DESKTOPDIRECTORY, 0);
// XXX		fsmenu_insert_entry(folder, 0, 0);

// XXX		fsmenu_append_separator();
	}
#endif

	BLI_make_file_string(G.sce, name, BLI_gethome(), ".Bfs");
	lines= BLI_read_file_as_lines(name);

	for (l= lines; l; l= l->next) {
		char *line= l->link;
			
		if (!BLI_streq(line, "")) {
// XXX			fsmenu_insert_entry(line, 0, 1);
		}
	}

// XXX	fsmenu_append_separator();
	
	/* add last saved file */
	BLI_split_dirfile(G.sce, name, filename); /* G.sce shouldn't be relative */
	
// XXX	fsmenu_insert_entry(name, 0, 0);
	
	BLI_free_file_lines(lines);
}

static void writeBlog(void)
{
	struct RecentFile *recent, *next_recent;
	char name[FILE_MAXDIR+FILE_MAXFILE];
	FILE *fp;
	int i;

	BLI_make_file_string("/", name, BLI_gethome(), ".Blog");

	recent = G.recent_files.first;
	/* refresh .Blog of recent opened files, when current file was changed */
	if(!(recent) || (strcmp(recent->filename, G.sce)!=0)) {
		fp= fopen(name, "w");
		if (fp) {
			/* add current file to the beginning of list */
			recent = (RecentFile*)MEM_mallocN(sizeof(RecentFile),"RecentFile");
			recent->filename = (char*)MEM_mallocN(sizeof(char)*(strlen(G.sce)+1), "name of file");
			recent->filename[0] = '\0';
			strcpy(recent->filename, G.sce);
			BLI_addhead(&(G.recent_files), recent);
			/* write current file to .Blog */
			fprintf(fp, "%s\n", recent->filename);
			recent = recent->next;
			i=1;
			/* write rest of recent opened files to .Blog */
			while((i<U.recent_files) && (recent)){
				/* this prevents to have duplicities in list */
				if (strcmp(recent->filename, G.sce)!=0) {
					fprintf(fp, "%s\n", recent->filename);
					recent = recent->next;
				}
				else {
					next_recent = recent->next;
					MEM_freeN(recent->filename);
					BLI_freelinkN(&(G.recent_files), recent);
					recent = next_recent;
				}
				i++;
			}
			fclose(fp);
		}
	}
}

static void do_history(char *name, ReportList *reports)
{
	char tempname1[FILE_MAXDIR+FILE_MAXFILE], tempname2[FILE_MAXDIR+FILE_MAXFILE];
	int hisnr= U.versions;
	
	if(U.versions==0) return;
	if(strlen(name)<2) return;
		
	while(hisnr > 1) {
		sprintf(tempname1, "%s%d", name, hisnr-1);
		sprintf(tempname2, "%s%d", name, hisnr);
	
		if(BLI_rename(tempname1, tempname2))
			BKE_report(reports, RPT_ERROR, "Unable to make version backup");
			
		hisnr--;
	}
		
	/* is needed when hisnr==1 */
	sprintf(tempname1, "%s%d", name, hisnr);
	
	if(BLI_rename(name, tempname1))
		BKE_report(reports, RPT_ERROR, "Unable to make version backup");
}

void WM_write_file(bContext *C, char *target, ReportList *reports)
{
	Library *li;
	int writeflags, len;
	char di[FILE_MAX];
	
	len = strlen(target);
	
	if (len == 0) return;
	if (len >= FILE_MAX) {
		BKE_report(reports, RPT_ERROR, "Path too long, cannot save");
		return;
	}
 
	/* send the OnSave event */
// XXX	if (G.f & G_DOSCRIPTLINKS) BPY_do_pyscript(&CTX_data_scene(C)->id, SCRIPT_ONSAVE);

	for (li= G.main->library.first; li; li= li->id.next) {
		if (BLI_streq(li->name, target)) {
			BKE_report(reports, RPT_ERROR, "Cannot overwrite used library");
			return;
		}
	}
	
	if (!BLO_has_bfile_extension(target) && (len+6 < FILE_MAX)) {
		sprintf(di, "%s.blend", target);
	} else {
		strcpy(di, target);
	}

	if (BLI_exists(di)) {
// XXX		if(!saveover(di))
// XXX			return; 
	}
	
	if (G.fileflags & G_AUTOPACK) {
		packAll();
	}
	
// XXX	waitcursor(1);	// exit_editmode sets cursor too

	do_history(di, reports);
	
	/* we use the UserDef to define compression flag */
	writeflags= G.fileflags & ~G_FILE_COMPRESS;
	if(U.flag & USER_FILECOMPRESS)
		writeflags |= G_FILE_COMPRESS;
	
	if (BLO_write_file(CTX_data_main(C), di, writeflags, reports)) {
		strcpy(G.sce, di);
		G.relbase_valid = 1;
		strcpy(G.main->name, di);	/* is guaranteed current file */

// XXX		mainwindow_set_filename_to_title(G.main->name);

		G.save_over = 1;

		writeBlog();
	}

// XXX	waitcursor(0);
}

/* operator entry */
int WM_write_homefile(bContext *C, wmOperator *op)
{
	char tstr[FILE_MAXDIR+FILE_MAXFILE];
	int write_flags;
	
	BLI_make_file_string("/", tstr, BLI_gethome(), ".B.blend");
		
	/*  force save as regular blend file */
	write_flags = G.fileflags & ~(G_FILE_COMPRESS | G_FILE_LOCK | G_FILE_SIGN);

	BLO_write_file(CTX_data_main(C), tstr, write_flags, op->reports);
	
	return OPERATOR_FINISHED;
}

void WM_write_autosave(bContext *C)
{
	char tstr[FILE_MAXDIR+FILE_MAXFILE];
	int write_flags;
	
	get_autosave_location(tstr);

		/*  force save as regular blend file */
	write_flags = G.fileflags & ~(G_FILE_COMPRESS | G_FILE_LOCK | G_FILE_SIGN);

		/* error reporting to console */
	BLO_write_file(CTX_data_main(C), tstr, write_flags, NULL);
}

/* if global undo; remove tempsave, otherwise rename */
void delete_autosave(void)
{
	char tstr[FILE_MAXDIR+FILE_MAXFILE];
	
	get_autosave_location(tstr);

	if (BLI_exists(tstr)) {
		char str[FILE_MAXDIR+FILE_MAXFILE];
		BLI_make_file_string("/", str, U.tempdir, "quit.blend");

		if(U.uiflag & USER_GLOBALUNDO) BLI_delete(tstr, 0, 0);
		else BLI_rename(tstr, str);
	}
}

/***/

