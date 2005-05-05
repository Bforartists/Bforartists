/**
 * blenlib/DNA_space_types.h (mar-2001 nzc)
 *	
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
#ifndef DNA_SPACE_TYPES_H
#define DNA_SPACE_TYPES_H

#include "DNA_listBase.h"
#include "DNA_vec_types.h"
/* Hum ... Not really nice... but needed for spacebuts. */
#include "DNA_view2d_types.h"

struct Ipo;
struct ID;
struct Text;
struct Script;
struct ImBuf;
struct Image;
struct SpaceIpo;
struct BlendHandle;
struct TreeStore;


	/**
	 * The base structure all the other spaces
	 * are derived (implicitly) from. Would be
	 * good to make this explicit.
	 */
typedef struct SpaceLink SpaceLink;
struct SpaceLink {
	SpaceLink *next, *prev;
	int spacetype;
	float blockscale;
	struct ScrArea *area;
	short blockhandler[8];
};

typedef struct SpaceInfo {
	SpaceLink *next, *prev;
	int spacetype;
	float blockscale;
	struct ScrArea *area;

	short blockhandler[8];
} SpaceInfo;

typedef struct SpaceIpo {
	SpaceLink *next, *prev;
	int spacetype;
	float blockscale;
	struct ScrArea *area;

	short blockhandler[8];
	
	unsigned int rowbut, pad2; 
	View2D v2d;
	
	void *editipo;
	ListBase ipokey;
	struct Ipo *ipo;
	struct ID *from;

	short totipo, pin;
	short butofs, channel;
	short showkey, blocktype;
	short menunr, lock;
	int flag;
	float median[3];
	rctf tot;
} SpaceIpo;

typedef struct SpaceButs {
	SpaceLink *next, *prev;
	int spacetype;
	float blockscale;
	struct ScrArea *area;

	short blockhandler[8];

	short cursens, curact;
	short align, tabo;		/* align for panels, tab is old tab */
	View2D v2d;
	
	short mainb, menunr;	/* texnr and menunr have to remain shorts */
	short pin, mainbo;	
	void *lockpoin;
	
	short texnr;
	char texfrom, showgroup;

	short rectx, recty;		/* preview render */
	unsigned int *rect;
	short cury, modeltype;

	short scriptblock;
	short scaflag;
	short re_align, pad1;
	int pad2;
	
	char texact, tab[7];	/* storing tabs for each context */
		
} SpaceButs;

typedef struct SpaceSeq {
	SpaceLink *next, *prev;
	int spacetype;
	float blockscale;
	struct ScrArea *area;

	short blockhandler[8];

	View2D v2d;
	
	short mainb, zoom;
	int pad2;
	
} SpaceSeq;

typedef struct SpaceFile {
	SpaceLink *next, *prev;
	int spacetype;
	float blockscale;
	struct ScrArea *area;
	
	short blockhandler[8];

	struct direntry *filelist;
	int totfile;
	char title[24];
	char dir[160];
	char file[80];
	short type, ofs, flag, sort;
	short maxnamelen, collums;
	
	struct BlendHandle *libfiledata;
	
	short retval, ipotype;
	short menu, act;

	/* changed type for compiling */
	/* void (*returnfunc)(short); ? used with char* ....*/
	/**
	 * @attention Called in filesel.c: 
	 * @attention returnfunc(this->retval) : short
	 * @attention returnfunc(name)         : char*
	 * @attention Other uses are limited to testing against
	 * @attention the value. How do we resolve this? Two args?
	 * @attention For now, keep the char*, as it seems stable.
	 * @attention Be warned that strange behaviour _has_ been spotted!
	 */
	void (*returnfunc)(char*);
 		
	short *menup;
} SpaceFile;

typedef struct SpaceOops {
	SpaceLink *next, *prev;
	int spacetype;
	float blockscale;
	struct ScrArea *area;

	short blockhandler[8];

	View2D v2d;
	
	ListBase oops;
	short pin, visiflag, flag, rt;
	void *lockpoin;
	
	ListBase tree;
	struct TreeStore *treestore;
	short type, outlinevis, storeflag;
	short deps_flags;
	
} SpaceOops;

typedef struct SpaceImage {
	SpaceLink *next, *prev;
	int spacetype;
	float blockscale;
	struct ScrArea *area;

	short blockhandler[8];

	View2D v2d;
	
	struct Image *image;
	float zoom;
	short mode, pin;
	short imanr, curtile;
	float xof, yof;
	short flag, lock;
	
} SpaceImage;

typedef struct SpaceNla{
	struct SpaceLink *next, *prev;
	int spacetype;
	float blockscale;
	struct ScrArea *area;

	short blockhandler[8];

	short menunr, lock;
	int pad;
	
	View2D v2d;	
} SpaceNla;

typedef struct SpaceText {
	SpaceLink *next, *prev;
	int spacetype;
	float blockscale;
	struct ScrArea *area;

	short blockhandler[8];

	struct Text *text;	

	int top, viewlines;
	short flags, menunr;
	
	int font_id;	
	int lheight;
	int left;
	int showlinenrs;
	
	int tabnumber;
	int currtab_set; 
	/* had to make my 64 bits some how */
	
	float pix_per_line;

	struct rcti txtscroll, txtbar;

} SpaceText;

typedef struct SpaceScript {
	SpaceLink *next, *prev;
	int spacetype;
	float blockscale;
	struct ScrArea *area;
	struct Script *script;

	int pad2;
	short flags, menunr;

} SpaceScript;

typedef struct SpaceTime {
	SpaceLink *next, *prev;
	int spacetype;
	float blockscale;
	struct ScrArea *area;
	
	View2D v2d;
	
	int flag, pad;
	
} SpaceTime;



#
#
typedef struct OneSelectableIma {
	int   header;						
	int   ibuf_type;
	struct ImBuf *pict;					
	struct OneSelectableIma *next;		
	struct OneSelectableIma *prev;		
	
	short  cmap, image, draw_me, rt;
	short  sx, sy, ex, ey, dw, dh;				
	short  selectable, selected;		
	int   mtime, disksize;				
	char   file_name[64];
	
	short  orgx, orgy, orgd, anim;		/* same as ibuf->x...*/
	char   dummy[4];					/* 128 */

	char   pict_rect[3968];				/* 4096   (RECT = 64 * 62) */
	
} OneSelectableIma;

#
#
typedef struct ImaDir {
	struct ImaDir *next, *prev;
	int  selected, hilite; 
	int  type,  size;
	int mtime;
	char name[100];
} ImaDir;

typedef struct SpaceImaSel {
	SpaceLink *next, *prev;
	int spacetype;
	float blockscale;
	struct ScrArea *area;
	
	char   title[28];
	
	int   fase; 
	short  mode, subfase;
	short  mouse_move_redraw, imafase;
	short  mx, my;
	
	short  dirsli, dirsli_lines;
	short  dirsli_sx, dirsli_ey , dirsli_ex, dirsli_h;
	short  imasli, fileselmenuitem;
	short  imasli_sx, imasli_ey , imasli_ex, imasli_h;
	
	short  dssx, dssy, dsex, dsey; 
	short  desx, desy, deex, deey; 
	short  fssx, fssy, fsex, fsey; 
	short  dsdh, fsdh; 
	short  fesx, fesy, feex, feey; 
	short  infsx, infsy, infex, infey; 
	short  dnsx, dnsy, dnw, dnh;
	short  fnsx, fnsy, fnw, fnh;

	
	char   fole[128], dor[128];
	char   file[128], dir[128];
	ImaDir *firstdir, *firstfile;
	int    topdir,  totaldirs,  hilite; 
	int    topfile, totalfiles;
	
	float  image_slider;
	float  slider_height;
	float  slider_space;
	short  topima,  totalima;
	short  curimax, curimay;
	OneSelectableIma *first_sel_ima;
	OneSelectableIma *hilite_ima;
	short  total_selected, ima_redraw;
	int pad2;
	
	struct ImBuf  *cmap;

	/* Also fucked. Needs to change so things compile, but breaks sdna
	* ... */	
/*  	void (*returnfunc)(void); */
	void (*returnfunc)(char*);
	void *arg1;
} SpaceImaSel;


/* **************** SPACE ********************* */


/* view3d->flag */ /* Now in DNA_view3d_types.h */
/*
#define V3D_DISPIMAGE		1
#define V3D_DISPBGPIC		2
#define V3D_SETUPBUTS		4
#define V3D_NEEDBACKBUFDRAW	8
#define V3D_MODE			(16+32+64+128)
#define V3D_EDITMODE		16
#define V3D_VERTEXPAINT		32
#define V3D_FACESELECT		64
#define V3D_POSEMODE		128
*/

/* view3d->around */ /* Now in DNA_view3d_types.h */
/*
#define V3D_CENTRE		0
#define V3D_CENTROID	3
#define V3D_CURSOR		1
#define V3D_LOCAL		2
*/

/* buts defines in BIF_butspace.h */

/* these values need to be hardcoded in blender.h SpaceFile: struct dna does not recognize defines */
#define FILE_MAXDIR			160
#define FILE_MAXFILE		80

/* filesel types */
#define FILE_UNIX			8
#define FILE_BLENDER		8
#define FILE_SPECIAL		9

#define FILE_LOADLIB		1
#define FILE_MAIN			2

/* sfile->flag */
#define FILE_SHOWSHORT		1
#define FILE_STRINGCODE		2
#define FILE_LINK			4
#define FILE_HIDE_DOT		8
#define FILE_AUTOSELECT		16
#define FILE_ACTIVELAY		32
#define FILE_ATCURSOR		64

/* sfile->sort */
#define FILE_SORTALPHA		0
#define FILE_SORTDATE		1
#define FILE_SORTSIZE		2
#define FILE_SORTEXTENS		3

/* files in filesel list: 2=ACTIVE  */
#define HILITE				1
#define BLENDERFILE			4
#define PSXFILE				8
#define IMAGEFILE			16
#define MOVIEFILE			32
#define PYSCRIPTFILE		64
#define FTFONTFILE			128
#define SOUNDFILE			256

#define SCROLLH	16			/* height scrollbar */
#define SCROLLB	16			/* width scrollbar */

/* SpaceImage->mode */
#define SI_TEXTURE		0
#define SI_SHOW			1

/* SpaceImage->flag */
#define SI_BE_SQUARE	1
#define SI_EDITTILE		2
#define SI_CLIP_UV		4
#define SI_DRAWTOOL		8
#define SI_STICKYUVS    16
#define SI_DRAWSHADOW   32
#define SI_SELACTFACE   64
#define SI_NOPIXELSNAP  128
#define SI_LOCALSTICKY  256

/* SpaceText flags (moved from DNA_text_types.h) */

#define ST_SCROLL_SELECT        0x0001 // scrollable
#define ST_CLEAR_NAMESPACE      0x0010 // clear namespace after script
                                       // execution (see BPY_main.c)
/* SpaceOops->type */
#define SO_OOPS			0
#define SO_OUTLINER		1
#define SO_DEPSGRAPH    2

/* SpaceOops->flag */
#define SO_TESTBLOCKS	1
#define SO_NEWSELECTED	2

/* SpaceOops->visiflag */
#define OOPS_SCE	1
#define OOPS_OB		2
#define OOPS_ME		4
#define OOPS_CU		8
#define OOPS_MB		16
#define OOPS_LT		32
#define OOPS_LA		64
#define OOPS_MA		128
#define OOPS_TE		256
#define OOPS_IP		512
#define OOPS_LAY	1024
#define OOPS_LI		2048
#define OOPS_IM		4096

/* SpaceOops->outlinevis */
#define SO_ALL_SCENES	0
#define SO_CUR_SCENE	1
#define SO_VISIBLE		2
#define SO_SELECTED		3
#define SO_ACTIVE		4
#define SO_SAME_TYPE	5

/* SpaceOops->storeflag */
#define SO_TREESTORE_CLEANUP	1

/* headerbuttons: 450-499 */

#define B_IMASELHOME		451
#define B_IMASELREMOVEBIP	452

#define C_BACK  0xBAAAAA
#define C_DARK  0x665656
#define C_DERK  0x766666
#define C_HI	0xCBBBBB
#define C_LO	0x544444

/* queue settings */
#define IMS_KNOW_WIN        1
#define IMS_KNOW_BIP        2
#define IMS_KNOW_DIR        4
#define IMS_DOTHE_INF		8
#define IMS_KNOW_INF	   16
#define IMS_DOTHE_IMA	   32
#define IMS_KNOW_IMA	   64
#define IMS_FOUND_BIP	  128
#define IMS_DOTHE_BIP	  256
#define IMS_WRITE_NO_BIP  512

/* imasel->mode */
#define IMS_NOIMA			0
#define IMS_IMA				1
#define IMS_ANIM			2
#define IMS_DIR				4
#define IMS_FILE			8
#define IMS_STRINGCODE		16

#define IMS_INDIR			1
#define IMS_INDIRSLI		2
#define IMS_INFILE			3
#define IMS_INFILESLI		4

/* time->flag */

#define TIME_DRAWFRAMES		1
#define TIME_CFRA_NUM		2


#endif
