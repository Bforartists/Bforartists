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
 */

	/* placed up here because of crappy
	 * winsock stuff.
	 */
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#ifdef WIN32
#include <shlobj.h> /* SHGetSpecialFolderPath, has to be done before BLI_winstuff for some reasons... */
#include "BLI_winstuff.h"
#include <process.h> /* getpid */
#else
#include <unistd.h> /* getpid */
#endif
#include "MEM_guardedalloc.h"
#include "MEM_CacheLimiterC-Api.h"

#include "BMF_Api.h"
#ifdef INTERNATIONAL
#include "BIF_language.h"
#include "FTF_Api.h"
#endif

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_linklist.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "DNA_object_types.h"
#include "DNA_space_types.h"
#include "DNA_userdef_types.h"
#include "DNA_sound_types.h"
#include "DNA_scene_types.h"

#include "BKE_blender.h"
#include "BKE_curve.h"
#include "BKE_displist.h"
#include "BKE_exotic.h"
#include "BKE_font.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_mball.h"
#include "BKE_packedFile.h"
#include "BKE_utildefines.h"

#include "BLI_vfontdata.h"

#include "BIF_fsmenu.h"
#include "BIF_gl.h"
#include "BIF_interface.h"
#include "BIF_usiblender.h"
#include "BIF_drawtext.h"
#include "BIF_editarmature.h"
#include "BIF_editlattice.h"
#include "BIF_editfont.h"
#include "BIF_editmesh.h"
#include "BIF_editmode_undo.h"
#include "BIF_editsound.h"
#include "BIF_poseobject.h"
#include "BIF_previewrender.h"
#include "BIF_renderwin.h"
#include "BIF_resources.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_toolbox.h"
#include "BIF_cursors.h"

#include "BSE_drawview.h"
#include "BSE_edit.h"
#include "BSE_editipo.h"
#include "BSE_filesel.h"
#include "BSE_headerbuttons.h"
#include "BSE_node.h"

#include "BLO_readfile.h"
#include "BLO_writefile.h"

#include "BDR_drawobject.h"
#include "BDR_editobject.h"
#include "BDR_editcurve.h"
#include "BDR_vpaint.h"

#include "BPY_extern.h"

#include "blendef.h"

#include "RE_pipeline.h"		/* RE_ free stuff */

#include "radio.h"
#include "datatoc.h"

#include "SYS_System.h"

#include "PIL_time.h"

/***/

/* define for setting colors in theme below */
#define SETCOL(col, r, g, b, a)  col[0]=r; col[1]=g; col[2]= b; col[3]= a;

/* patching UserDef struct, set globals for UI stuff */
static void init_userdef_file(void)
{
	
	BIF_InitTheme();	// sets default again
	
	mainwindow_set_filename_to_title("");	// empty string re-initializes title to "Blender"
	countall();
	G.save_over = 0;	// start with save preference untitled.blend
	
	/*  disable autoplay in .B.blend... */
	G.fileflags &= ~G_FILE_AUTOPLAY;
	
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
		error(".B.blend is buggy, please consider removing it.\n");
	}
	/* transform widget settings */
	if(U.tw_hotspot==0) {
		U.tw_hotspot= 14;
		U.tw_size= 20;			// percentage of window size
		U.tw_handlesize= 16;	// percentage of widget radius
	}
	
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
				SETCOL(btheme->tnode.syntaxn, 95, 110, 145, 255);	/* in/output */
				SETCOL(btheme->tnode.syntaxb, 135, 125, 120, 255);	/* operator */
				SETCOL(btheme->tnode.syntaxv, 120, 120, 120, 255);	/* generator */
				SETCOL(btheme->tnode.syntaxc, 120, 145, 120, 255);	/* group */
			}
			if(btheme->tv3d.group[3]==0) {
				SETCOL(btheme->tv3d.group, 0x10, 0x40, 0x10, 255);
				SETCOL(btheme->tv3d.group_active, 0x66, 0xFF, 0x66, 255);
			}
		}
	}
	
	if (U.undosteps==0) U.undosteps=32;
	
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
	
	reset_autosave();
	
#ifdef INTERNATIONAL
	read_languagefile();
	
	refresh_interface_font();
#endif // INTERNATIONAL

}

void BIF_read_file(char *name)
{
	extern short winqueue_break; /* editscreen.c */

	//here?
	//sound_end_all_sounds();

	// first try to read exotic file formats...
	if (BKE_read_exotic(name) == 0) { /* throws first error box */
		/* we didn't succeed, now try to read Blender file
		   calls readfile, calls toolbox, throws one more,
		   on failure calls the stream, and that is stubbed.... */
		int retval= BKE_read_file(name, NULL);

		mainwindow_set_filename_to_title(G.main->name);
		countall();
		sound_initialize_sounds();

		winqueue_break= 1;	/* leave queues everywhere */

		if(retval==2) init_userdef_file();	// in case a userdef is read from regular .blend
		
		undo_editmode_clear();
		BKE_reset_undo();
		BKE_write_undo("original");	/* save current state */
		refresh_interface_font();
	}
	else BIF_undo_push("Import file");
}

/* only here settings for fullscreen */
int BIF_read_homefile(void)
{
	char tstr[FILE_MAXDIR+FILE_MAXFILE], scestr[FILE_MAXDIR];
	char *home= BLI_gethome();
	int success;
	struct TmpFont *tf;
	
	BLI_clean(home);

	tf= G.ttfdata.first;
	while(tf)
	{
		freePackedFile(tf->pf);
		tf->pf = NULL;
		tf->vfont = NULL;
		tf= tf->next;
	}
	BLI_freelistN(&G.ttfdata);
	
#if 0
//#ifdef _WIN32	// FULLSCREEN
	static int screenmode = -1;
	
	screenmode = U.uiflag & USER_FLIPFULLSCREEN;
#endif
	
	BLI_make_file_string(G.sce, tstr, home, ".B.blend");
	strcpy(scestr, G.sce);	/* temporal store */
	
	/* prevent loading no UI */
	G.fileflags &= ~G_FILE_NO_UI;
	
	if (BLI_exists(tstr)) {
		success = BKE_read_file(tstr, NULL);
	} else {
		success = BKE_read_file_from_memory(datatoc_B_blend, datatoc_B_blend_size, NULL);
	}
	BLI_clean(scestr);
	strcpy(G.sce, scestr);
	
#if 0
//#ifdef _WIN32	// FULLSCREEN
	/* choose window startmode */
	switch (G.windowstate){
		case G_WINDOWSTATE_USERDEF: /* use the usersetting */
			break;
		case G_WINDOWSTATE_FULLSCREEN: /* force fullscreen */
			U.uiflag |= USER_FLIPFULLSCREEN;
			break;
		case G_WINDOWSTATE_BORDER: /* force with borders */
			U.uiflag &= ~USER_FLIPFULLSCREEN;
	}
	
	if(screenmode != (U.uiflag & USER_FLIPFULLSCREEN)) {
		mainwindow_toggle_fullscreen ((U.uiflag & USER_FLIPFULLSCREEN));
		screenmode = (U.uiflag & USER_FLIPFULLSCREEN);
	}
#endif
	
	space_set_commmandline_options();
	
	init_userdef_file();

	undo_editmode_clear();
	BKE_reset_undo();
	BKE_write_undo("original");	/* save current state */
	
	return success;
}


static void get_autosave_location(char buf[FILE_MAXDIR+FILE_MAXFILE])
{
	char pidstr[32];

	sprintf(pidstr, "%d.blend", abs(getpid()));
	BLI_make_file_string("/", buf, U.tempdir, pidstr);
}

void BIF_read_autosavefile(void)
{
	char tstr[FILE_MAXDIR+FILE_MAXFILE], scestr[FILE_MAXDIR];
	int save_over;

	strcpy(scestr, G.sce);	/* temporal store */
	
	get_autosave_location(tstr);

	save_over = G.save_over;
	BKE_read_file(tstr, NULL);
	G.save_over = save_over;
	strcpy(G.sce, scestr);
}

/***/

static void readBlog(void)
{
	char name[FILE_MAXDIR+FILE_MAXFILE], filename[FILE_MAXFILE];
	LinkNode *l, *lines;

	BLI_make_file_string("/", name, BLI_gethome(), ".Blog");
	lines= BLI_read_file_as_lines(name);

	if (lines && !BLI_streq(lines->link, "")) {
		strcpy(G.sce, lines->link);
	} else {
		BLI_make_file_string("/", G.sce, BLI_gethome(), "untitled.blend");
	}

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
				
				fsmenu_insert_entry(tmps, 0);
			}
		}

		/* Adding Desktop and My Documents */
		fsmenu_append_seperator();
		SHGetFolderPath(0, CSIDL_PERSONAL,NULL, 0, folder);
		fsmenu_insert_entry(folder, 0);
		SHGetFolderPath(0, CSIDL_DESKTOPDIRECTORY,NULL, 0, folder);
		fsmenu_insert_entry(folder, 0);

		fsmenu_append_seperator();
	}
#endif

	BLI_make_file_string(G.sce, name, BLI_gethome(), ".Bfs");
	lines= BLI_read_file_as_lines(name);

	for (l= lines; l; l= l->next) {
		char *line= l->link;
			
		if (!BLI_streq(line, "")) {
			fsmenu_insert_entry(line, 0);
		}
	}

	fsmenu_append_seperator();
	
	/* add last saved file */
	BLI_split_dirfile(G.sce, name, filename);
	
	fsmenu_insert_entry(name, 0);
	
	BLI_free_file_lines(lines);
}


static void writeBlog(void)
{
	char name[FILE_MAXDIR+FILE_MAXFILE];
	FILE *fp;

	BLI_make_file_string("/", name, BLI_gethome(), ".Blog");

	fp= fopen(name, "w");
	if (fp) {
		fprintf(fp, G.sce);
		fclose(fp);
	}
}

static void do_history(char *name)
{
	char tempname1[FILE_MAXDIR+FILE_MAXFILE], tempname2[FILE_MAXDIR+FILE_MAXFILE];
	int hisnr= U.versions;
	
	if(U.versions==0) return;
	if(strlen(name)<2) return;
		
	while(  hisnr > 1) {
		sprintf(tempname1, "%s%d", name, hisnr-1);
		sprintf(tempname2, "%s%d", name, hisnr);
	
		if(BLI_rename(tempname1, tempname2))
			error("Unable to make version backup");
			
		hisnr--;
	}
		
	/* is needed when hisnr==1 */
	sprintf(tempname1, "%s%d", name, hisnr);
	
	if(BLI_rename(name, tempname1))
		error("Unable to make version backup");
}

void BIF_write_file(char *target)
{
	Library *li;
	int writeflags;
	char di[FILE_MAXDIR];
	char *err;
	
	if (BLI_streq(target, "")) return;
 
	/* send the OnSave event */
	if (G.f & G_DOSCRIPTLINKS) BPY_do_pyscript(&G.scene->id, SCRIPT_ONSAVE);

	for (li= G.main->library.first; li; li= li->id.next) {
		if (BLI_streq(li->name, target)) {
			error("Cannot overwrite used library");
			return;
		}
	}
	
	if (!BLO_has_bfile_extension(target)) {
		sprintf(di, "%s.blend", target);
	} else {
		strcpy(di, target);
	}

	if (BLI_exists(di)) {
		if(!saveover(di))
			return; 
	}
	
	if(G.obedit) {
		exit_editmode(0);	/* 0 = no free data */
	}
	if (G.fileflags & G_AUTOPACK) {
		packAll();
	}
	
	waitcursor(1);	// exit_editmode sets cursor too

	do_history(di);
	
	/* we use the UserDef to define compression flag */
	writeflags= G.fileflags & ~G_FILE_COMPRESS;
	if(U.flag & USER_FILECOMPRESS)
		writeflags |= G_FILE_COMPRESS;
	
	if (BLO_write_file(di, writeflags, &err)) {
		strcpy(G.sce, di);
		strcpy(G.main->name, di);	/* is guaranteed current file */

		mainwindow_set_filename_to_title(G.main->name);

		G.save_over = 1;

		writeBlog();
	} else {
		error("%s", err);
	}

	waitcursor(0);
}

void BIF_write_homefile(void)
{
	char *err, tstr[FILE_MAXDIR+FILE_MAXFILE];
	int write_flags;
	
	BLI_make_file_string("/", tstr, BLI_gethome(), ".B.blend");
		
	/*  force save as regular blend file */
	write_flags = G.fileflags & ~(G_FILE_COMPRESS | G_FILE_LOCK | G_FILE_SIGN);
	BLO_write_file(tstr, write_flags, &err);
}

void BIF_write_autosave(void)
{
	char *err, tstr[FILE_MAXDIR+FILE_MAXFILE];
	int write_flags;
	
	get_autosave_location(tstr);

		/*  force save as regular blend file */
	write_flags = G.fileflags & ~(G_FILE_COMPRESS | G_FILE_LOCK | G_FILE_SIGN);
	BLO_write_file(tstr, write_flags, &err);
}

/* if global undo; remove tempsave, otherwise rename */
static void delete_autosave(void)
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

static void initbuttons(void)
{
	uiDefFont(UI_HELVB, 
				BMF_GetFont(BMF_kHelveticaBold14), 
				BMF_GetFont(BMF_kHelveticaBold12), 
				BMF_GetFont(BMF_kHelveticaBold10), 
				BMF_GetFont(BMF_kHelveticaBold8));
	uiDefFont(UI_HELV, 
				BMF_GetFont(BMF_kHelvetica12), 
				BMF_GetFont(BMF_kHelvetica12), 
				BMF_GetFont(BMF_kHelvetica10), 
				BMF_GetFont(BMF_kHelveticaBold8));
	
	BIF_resources_init();

	glClearColor(.7f, .7f, .6f, 0.0);
	
	G.font= BMF_GetFont(BMF_kHelvetica12);
	G.fonts= BMF_GetFont(BMF_kHelvetica10);
	G.fontss= BMF_GetFont(BMF_kHelveticaBold8);

	clear_matcopybuf();
	
	glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);
}


static void sound_init_listener(void)
{
	G.listener = MEM_callocN(sizeof(bSoundListener), "soundlistener");
	G.listener->gain = 1.0;
	G.listener->dopplerfactor = 1.0;
	G.listener->dopplervelocity = 340.29f;
}

void BIF_init(void)
{

	initscreen();	/* for (visuele) speed, this first, then setscreen */
	initbuttons();
	InitCursorData();
	sound_init_listener();
	init_node_butfuncs();
	
	BIF_preview_init_dbase();
	BIF_read_homefile();
	
	init_gl_stuff();	/* drawview.c, after homefile */
	readBlog();
	strcpy(G.lib, G.sce);

}

/***/

extern ListBase editNurb;
extern ListBase editelems;

void exit_usiblender(void)
{
	struct TmpFont *tf;
	tf= G.ttfdata.first;
	while(tf)
	{
		freePackedFile(tf->pf);
		tf->pf= NULL;
		tf->vfont= NULL;
		tf= tf->next;
	}
	BLI_freelistN(&G.ttfdata);

	freeAllRad();
	BKE_freecubetable();

	if (G.background == 0)
		sound_end_all_sounds();

	if(G.obedit) {
		if(G.obedit->type==OB_FONT) {
			free_editText();
		}
		else if(G.obedit->type==OB_MBALL) BLI_freelistN(&editelems);
		free_editMesh(G.editMesh);
	}

	free_editLatt();
	free_editArmature();
	free_posebuf();

	free_blender();	/* blender.c, does entire library */
	free_matcopybuf();
	free_ipocopybuf();
	freefastshade();
	free_vertexpaint();
	
	/* editnurb can remain to exist outside editmode */
	freeNurblist(&editNurb);

	fsmenu_free();
#ifdef INTERNATIONAL
	free_languagemenu();
#endif	
	
	RE_FreeAllRender();
	
	free_txt_data();

	sound_exit_audio();
	if(G.listener) MEM_freeN(G.listener);

	libtiff_exit();

#ifdef WITH_QUICKTIME
	quicktime_exit();
#endif
		
	BPY_end_python();

	if (!G.background) {
		BIF_resources_free();
	
		BIF_close_render_display();
		mainwindow_close();
	}

#ifdef INTERNATIONAL
	FTF_End();
#endif

	if (copybuf) MEM_freeN(copybuf);
	if (copybufinfo) MEM_freeN(copybufinfo);

	/* undo free stuff */
	undo_editmode_clear();
	
	BKE_undo_save_quit();	// saves quit.blend if global undo is on
	BKE_reset_undo(); 
	
	BLI_freelistN(&U.themes);
	BIF_preview_free_dbase();
		
	if(totblock!=0) {
		printf("Error Totblock: %d\n",totblock);
		MEM_printmemlist();
	}
	delete_autosave();
	
	printf("\nBlender quit\n");

#ifdef WIN32   
	/* ask user to press enter when in debug mode */
	if(G.f & G_DEBUG) {
		printf("press enter key to exit...\n\n");
		getchar();
	}
#endif 


	SYS_DeleteSystem(SYS_GetSystem());

	exit(G.afbreek==1);
}
