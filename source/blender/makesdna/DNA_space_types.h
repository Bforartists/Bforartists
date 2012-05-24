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
/** \file DNA_space_types.h
 *  \ingroup DNA
 *  \since mar-2001
 *  \author nzc
 */

#ifndef __DNA_SPACE_TYPES_H__
#define __DNA_SPACE_TYPES_H__

#include "DNA_defs.h"
#include "DNA_listBase.h"
#include "DNA_color_types.h"		/* for Histogram */
#include "DNA_vec_types.h"
#include "DNA_outliner_types.h"		/* for TreeStoreElem */
#include "DNA_image_types.h"	/* ImageUser */
#include "DNA_movieclip_types.h"	/* MovieClipUser */
/* Hum ... Not really nice... but needed for spacebuts. */
#include "DNA_view2d_types.h"

struct ID;
struct Text;
struct Script;
struct bSound;
struct ImBuf;
struct Image;
struct Scopes;
struct Histogram;
struct SpaceIpo;
struct BlendHandle;
struct RenderInfo;
struct bNodeTree;
struct uiBlock;
struct FileList;
struct bGPdata;
struct bDopeSheet;
struct FileSelectParams;
struct FileLayout;
struct bScreen;
struct Scene;
struct wmOperator;
struct wmTimer;
struct MovieClip;
struct MovieClipScopes;

	/**
	 * The base structure all the other spaces
	 * are derived (implicitly) from. Would be
	 * good to make this explicit.
	 */

typedef struct SpaceLink {
	struct SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;
	float blockscale  DNA_DEPRECATED;       /* XXX make deprecated */
	short blockhandler[8]  DNA_DEPRECATED;  /* XXX make deprecated */
} SpaceLink;

typedef struct SpaceInfo {
	SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;
	float blockscale  DNA_DEPRECATED;

	short blockhandler[8]  DNA_DEPRECATED;		/* XXX make deprecated */
	
	char rpt_mask;
	char pad[7];
	
} SpaceInfo;

/* SpaceInfo.rpt_mask */
typedef enum eSpaceInfo_RptMask {
	INFO_RPT_DEBUG	= (1 << 0),
	INFO_RPT_INFO	= (1 << 1),
	INFO_RPT_OP		= (1 << 2),
	INFO_RPT_WARN	= (1 << 3),
	INFO_RPT_ERR	= (1 << 4),
} eSpaceInfo_RptMask;

/* 'Graph' Editor (formerly known as the IPO Editor) */
typedef struct SpaceIpo {
	SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;
	float blockscale  DNA_DEPRECATED;

	short blockhandler[8]  DNA_DEPRECATED;
	View2D v2d  DNA_DEPRECATED; /* deprecated, copied to region */
	
	struct bDopeSheet *ads;	/* settings for filtering animation data (NOTE: we use a pointer due to code-linking issues) */
	
	ListBase ghostCurves;	/* sampled snapshots of F-Curves used as in-session guides */
	
	short mode;				/* mode for the Graph editor (eGraphEdit_Mode) */
	short autosnap;			/* time-transform autosnapping settings for Graph editor (eAnimEdit_AutoSnap in DNA_action_types.h) */
	int flag;				/* settings for Graph editor (eGraphEdit_Flag) */
	
	float cursorVal;		/* cursor value (y-value, x-value is current frame) */
	int around;				/* pivot point for transforms */
} SpaceIpo;

typedef struct SpaceButs {
	SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;
	float blockscale  DNA_DEPRECATED;
	
	short blockhandler[8]  DNA_DEPRECATED;

	View2D v2d  DNA_DEPRECATED;						/* deprecated, copied to region */
	
	short mainb, mainbo, mainbuser;	/* context tabs */
	short re_align, align;			/* align for panels */
	short preview;					/* preview is signal to refresh */
	short texture_context;			/* texture context selector (material, world, brush)*/
	char flag, pad;
	
	void *path;						/* runtime */
	int pathflag, dataicon;			/* runtime */
	ID *pinid;

	void *texuser;
} SpaceButs;

typedef struct SpaceSeq {
	SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;
	float blockscale  DNA_DEPRECATED;

	short blockhandler[8]  DNA_DEPRECATED;

	View2D v2d  DNA_DEPRECATED; /* deprecated, copied to region */
	
	float xof  DNA_DEPRECATED, yof  DNA_DEPRECATED;	/* deprecated: offset for drawing the image preview */
	short mainb;	/* weird name for the sequencer subtype (seq, image, luma... etc) */
	short render_size;
	short chanshown;
	short zebra;
	int flag;
	float zoom  DNA_DEPRECATED; /* deprecated, handled by View2D now */
	int view; /* see SEQ_VIEW_* below */
	int pad;

	struct bGPdata *gpd;		/* grease-pencil data */
} SpaceSeq;

typedef struct FileSelectParams {
	char title[32]; /* title, also used for the text of the execute button */
	char dir[1056]; /* directory, FILE_MAX_LIBEXTRA, 1024 + 32, this is for extreme case when 1023 length path
	                 * needs to be linked in, where foo.blend/Armature need adding  */
	char file[256]; /* file */
	char renamefile[256];
	char renameedit[256]; /* annoying but the first is only used for initialization */

	char filter_glob[64]; /* list of filetypes to filter */

	int	active_file;
	int sel_first;
	int sel_last;

	/* short */
	short type; /* XXXXX for now store type here, should be moved to the operator */
	short flag; /* settings for filter, hiding dots files,...  */
	short sort; /* sort order */
	short display; /* display mode flag */
	short filter; /* filter when (flags & FILE_FILTER) is true */

	/* XXX --- still unused -- */
	short f_fp; /* show font preview */
	char fp_str[8]; /* string to use for font preview */

	/* XXX --- end unused -- */
} FileSelectParams;


typedef struct SpaceFile {
	SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;
	int scroll_offset;

	struct FileSelectParams *params; /* config and input for file select */
	
	struct FileList *files; /* holds the list of files to show */

	ListBase *folders_prev; /* holds the list of previous directories to show */
	ListBase *folders_next; /* holds the list of next directories (pushed from previous) to show */

	/* operator that is invoking fileselect 
	 * op->exec() will be called on the 'Load' button.
	 * if operator provides op->cancel(), then this will be invoked
	 * on the cancel button.
	 */
	struct wmOperator *op; 

	struct wmTimer *smoothscroll_timer;

	struct FileLayout *layout;
	
	short recentnr, bookmarknr;
	short systemnr, pad2;
} SpaceFile;

typedef struct SpaceOops {
	SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;
	float blockscale  DNA_DEPRECATED;

	short blockhandler[8]  DNA_DEPRECATED;

	View2D v2d  DNA_DEPRECATED; /* deprecated, copied to region */
	
	ListBase tree;
	struct TreeStore *treestore;
	
	/* search stuff */
	char search_string[32];
	struct TreeStoreElem search_tse;

	short flag, outlinevis, storeflag, search_flags;
} SpaceOops;

typedef struct SpaceImage {
	SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;

	int flag;

	struct Image *image;
	struct ImageUser iuser;
	struct CurveMapping *cumap;		
	
	struct Scopes scopes;			/* histogram waveform and vectorscope */
	struct Histogram sample_line_hist;	/* sample line histogram */

	struct bGPdata *gpd;			/* grease pencil data */

	float cursor[2];				/* UV editor 2d cursor */
	float xof, yof;					/* user defined offset, image is centered */
	float zoom;						/* user defined zoom level */
	float centx, centy;				/* storage for offset while render drawing */

	short curtile; /* the currently active tile of the image when tile is enabled, is kept in sync with the active faces tile */
	short pad;
	short lock;
	short pin;
	char dt_uv; /* UV draw type */
	char sticky; /* sticky selection type */
	char dt_uvstretch;
	char around;
} SpaceImage;

typedef struct SpaceNla {
	struct SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;
	float blockscale  DNA_DEPRECATED;

	short blockhandler[8]  DNA_DEPRECATED;

	short autosnap;			/* this uses the same settings as autosnap for Action Editor */
	short flag;
	int pad;
	
	struct bDopeSheet *ads;
	View2D v2d  DNA_DEPRECATED;	 /* deprecated, copied to region */
} SpaceNla;

typedef struct SpaceText {
	SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;
	float blockscale  DNA_DEPRECATED;

	short blockhandler[8]  DNA_DEPRECATED;

	struct Text *text;	

	int top, viewlines;
	short flags, menunr;	

	short lheight;		/* user preference */
	char cwidth, linenrs_tot;		/* runtime computed, character width and the number of chars to use when showing line numbers */
	int left;
	int showlinenrs;
	int tabnumber;

	short showsyntax;
	short line_hlight;
	short overwrite;
	short live_edit; /* run python while editing, evil */
	float pix_per_line;

	struct rcti txtscroll, txtbar;

	int wordwrap, doplugins;

	char findstr[256];		/* ST_MAX_FIND_STR */
	char replacestr[256];	/* ST_MAX_FIND_STR */

	short margin_column; /* column number to show right margin at */
	char pad[6];

	void *drawcache; /* cache for faster drawing */
} SpaceText;

typedef struct Script {
	ID id;

	void *py_draw;
	void *py_event;
	void *py_button;
	void *py_browsercallback;
	void *py_globaldict;

	int flags, lastspace;
	/* store the script file here so we can re-run it on loading blender, if "Enable Scripts" is on */
	char scriptname[1024]; /* 1024 = FILE_MAX */
	char scriptarg[256]; /* 1024 = FILE_MAX */
} Script;
#define SCRIPT_SET_NULL(_script) _script->py_draw = _script->py_event = _script->py_button = _script->py_browsercallback = _script->py_globaldict = NULL; _script->flags = 0

typedef struct SpaceScript {
	SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;
	float blockscale  DNA_DEPRECATED;
	struct Script *script;

	short flags, menunr;
	int pad1;
	
	void *but_refs;
} SpaceScript;

# /* Only store the data array in the cache to avoid constant reallocation. */
# /* No need to store when saved. */
typedef struct SpaceTimeCache {
	struct SpaceTimeCache *next, *prev;
	float *array;
} SpaceTimeCache;

typedef struct SpaceTime {
	SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;
	float blockscale  DNA_DEPRECATED;
	
	View2D v2d  DNA_DEPRECATED; /* deprecated, copied to region */

	ListBase caches;

	int cache_display;
	int flag;
} SpaceTime;

typedef struct SpaceNode {
	SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;
	float blockscale  DNA_DEPRECATED;
	
	short blockhandler[8]  DNA_DEPRECATED;
	
	View2D v2d  DNA_DEPRECATED; /* deprecated, copied to region */
	
	struct ID *id, *from;		/* context, no need to save in file? well... pinning... */
	short flag, pad1;			/* menunr: browse id block in header */
	float aspect;
	
	float xof, yof;		/* offset for drawing the backdrop */
	float zoom, padf;	/* zoom for backdrop */
	float mx, my;		/* mousepos for drawing socketless link */
	
	struct bNodeTree *nodetree, *edittree;
	int treetype;		/* treetype: as same nodetree->type */
	short texfrom;		/* texfrom object, world or brush */
	short shaderfrom;	/* shader from object or world */
	short recalc;		/* currently on 0/1, for auto compo */
	short pad[3];
	ListBase linkdrag;	/* temporary data for modal linking operator */
	
	struct bGPdata *gpd;		/* grease-pencil data */
} SpaceNode;

/* snode->flag */
typedef enum eSpaceNode_Flag {
	SNODE_BACKDRAW     = (1 << 1),
	SNODE_DISPGP       = (1 << 2), /* XXX: Grease Pencil - deprecated? */
	SNODE_USE_ALPHA    = (1 << 3),
	SNODE_SHOW_ALPHA   = (1 << 4),
	SNODE_AUTO_RENDER  = (1 << 5),
} eSpaceNode_Flag;

/* snode->texfrom */
typedef enum eSpaceNode_TexFrom {
	SNODE_TEX_OBJECT   = 0,
	SNODE_TEX_WORLD,
	SNODE_TEX_BRUSH,
} eSpaceNode_TexFrom;

/* snode->shaderfrom */
typedef enum eSpaceNode_ShaderFrom {
	SNODE_SHADER_OBJECT	= 0,
	SNODE_SHADER_WORLD,
} eSpaceNode_ShaderFrom;

/* Logic Editor */
typedef struct SpaceLogic {
	SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;
	float blockscale  DNA_DEPRECATED;
	
	short blockhandler[8]  DNA_DEPRECATED;
	
	short flag, scaflag;
	int pad;
	
	struct bGPdata *gpd;		/* grease-pencil data */
} SpaceLogic;

typedef struct ConsoleLine {
	struct ConsoleLine *next, *prev;
	
	/* keep these 3 vars so as to share free, realloc funcs */
	int len_alloc;	/* allocated length */
	int len;	/* real len - strlen() */
	char *line; 
	
	int cursor;
	int type; /* only for use when in the 'scrollback' listbase */
} ConsoleLine;

/* ConsoleLine.type */
typedef enum eConsoleLine_Type {
	CONSOLE_LINE_OUTPUT=0,
	CONSOLE_LINE_INPUT,
	CONSOLE_LINE_INFO, /* autocomp feedback */
	CONSOLE_LINE_ERROR
} eConsoleLine_Type;

typedef struct SpaceConsole {
	SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;
	float blockscale  DNA_DEPRECATED;			// XXX are these needed?
	
	short blockhandler[8]  DNA_DEPRECATED;		// XXX are these needed?
	
	/* space vars */
	int lheight, pad;

	ListBase scrollback; /* ConsoleLine; output */
	ListBase history; /* ConsoleLine; command history, current edited line is the first */
	char prompt[256];
	char language[32]; /* multiple consoles are possible, not just python */
	
	int sel_start;
	int sel_end;
} SpaceConsole;

typedef struct SpaceUserPref {
	SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;

	int pad;
	
	char filter[64];		/* search term for filtering in the UI */
} SpaceUserPref;

typedef struct SpaceClip {
	SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;

	float xof, yof;				/* user defined offset, image is centered */
	float xlockof, ylockof;		/* user defined offset from locked position */
	float zoom;					/* user defined zoom level */

	struct MovieClipUser user;		/* user of clip */
	struct MovieClip *clip;			/* clip data */
	struct MovieClipScopes scopes;	/* different scoped displayed in space panels */

	int flag;					/* flags */
	short mode;					/* editor mode (editing context being displayed) */
	short view;					/* type of the clip editor view */

	int path_length;			/* length of displaying path, in frames */

	/* current stabilization data */
	float loc[2], scale, angle;	/* pre-composed stabilization data */
	int pad;
	float stabmat[4][4], unistabmat[4][4];  /* current stabilization matrix and the same matrix in unified space,
	                                         * defined when drawing and used for mouse position calculation */

	/* movie postprocessing */
	int postproc_flag, pad2;

	void *draw_context;

	/* dopesheet */
	short dope_sort;		/* sort order in dopesheet view */
	short dope_flag;		/* dopsheet view flags */

	int pad3;
} SpaceClip;

/* view3d  Now in DNA_view3d_types.h */



/* **************** SPACE DEFINES ********************* */

/* button defines (deprecated) */
/* warning: the values of these defines are used in sbuts->tabs[8] */
/* sbuts->mainb new */
#define CONTEXT_SCENE	0
#define CONTEXT_OBJECT	1
#define CONTEXT_TYPES	2
#define CONTEXT_SHADING	3
#define CONTEXT_EDITING	4
#define CONTEXT_SCRIPT	5
#define CONTEXT_LOGIC	6

/* sbuts->mainb old (deprecated) */
#define BUTS_VIEW			0
#define BUTS_LAMP			1
#define BUTS_MAT			2
#define BUTS_TEX			3
#define BUTS_ANIM			4
#define BUTS_WORLD			5
#define BUTS_RENDER			6
#define BUTS_EDIT			7
#define BUTS_GAME			8
#define BUTS_FPAINT			9
#define BUTS_RADIO			10
#define BUTS_SCRIPT			11
#define BUTS_SOUND			12
#define BUTS_CONSTRAINT		13
#define BUTS_EFFECTS		14

/* buts->mainb new */
typedef enum eSpaceButtons_Context {
	BCONTEXT_RENDER = 0,
	BCONTEXT_SCENE,
	BCONTEXT_WORLD,
	BCONTEXT_OBJECT,
	BCONTEXT_DATA,
	BCONTEXT_MATERIAL,
	BCONTEXT_TEXTURE,
	BCONTEXT_PARTICLE,
	BCONTEXT_PHYSICS,
	BCONTEXT_BONE,
	BCONTEXT_MODIFIER,
	BCONTEXT_CONSTRAINT,
	BCONTEXT_BONE_CONSTRAINT,
	
	/* always as last... */
	BCONTEXT_TOT
} eSpaceButtons_Context;

/* sbuts->flag */
#define SB_PRV_OSA			1
#define SB_PIN_CONTEXT		2
//#define SB_WORLD_TEX		4	//not used anymore
//#define SB_BRUSH_TEX		8	//not used anymore	
#define SB_SHADING_CONTEXT	16

/* sbuts->texture_context */
typedef enum eSpaceButtons_Texture_Context {
	SB_TEXC_MAT_OR_LAMP = 0,
	SB_TEXC_WORLD,
	SB_TEXC_BRUSH,
	SB_TEXC_PARTICLES,
} eSpaceButtons_Texture_Context;

/* sbuts->align */
typedef enum eSpaceButtons_Align {
	BUT_FREE = 0,
	BUT_HORIZONTAL,
	BUT_VERTICAL,
	BUT_AUTO,
} eSpaceButtons_Align;

/* sbuts->scaflag */		
#define BUTS_SENS_SEL		1
#define BUTS_SENS_ACT		2
#define BUTS_SENS_LINK		4
#define BUTS_CONT_SEL		8
#define BUTS_CONT_ACT		16
#define BUTS_CONT_LINK		32
#define BUTS_ACT_SEL		64
#define BUTS_ACT_ACT		128
#define BUTS_ACT_LINK		256
#define BUTS_SENS_STATE		512
#define BUTS_ACT_STATE		1024
#define BUTS_CONT_INIT_STATE	2048

/* FileSelectParams.display */
enum FileDisplayTypeE {
	FILE_DEFAULTDISPLAY = 0,
	FILE_SHORTDISPLAY,
	FILE_LONGDISPLAY,
	FILE_IMGDISPLAY
};

/* FileSelectParams.sort */
enum FileSortTypeE {
	FILE_SORT_NONE = 0,
	FILE_SORT_ALPHA = 1,
	FILE_SORT_EXTENSION,
	FILE_SORT_TIME,
	FILE_SORT_SIZE
};

/* these values need to be hardcoded in structs, dna does not recognize defines */
/* also defined in BKE */
#define FILE_MAXDIR			768
#define FILE_MAXFILE		256
#define FILE_MAX			1024

#define FILE_MAX_LIBEXTRA   (FILE_MAX + 32)

/* filesel types */
#define FILE_UNIX			8
#define FILE_BLENDER		8 /* don't display relative paths */
#define FILE_SPECIAL		9

#define FILE_LOADLIB		1
#define FILE_MAIN			2
#define FILE_LOADFONT		3

/* filesel op property -> action */
typedef enum eFileSel_Action {
	FILE_OPENFILE = 0,
	FILE_SAVE,
} eFileSel_Action;

/* sfile->params->flag and simasel->flag */
typedef enum eFileSel_Params_Flag {
	FILE_SHOWSHORT      = (1 << 0),
	FILE_RELPATH        = (1 << 1), /* was FILE_STRINGCODE */
	FILE_LINK           = (1 << 2),
	FILE_HIDE_DOT       = (1 << 3),
	FILE_AUTOSELECT     = (1 << 4),
	FILE_ACTIVELAY      = (1 << 5),
/* 	FILE_ATCURSOR       = (1 << 6), */ /* deprecated */
	FILE_DIRSEL_ONLY    = (1 << 7),
	FILE_FILTER         = (1 << 8),
	FILE_BOOKMARKS      = (1 << 9),
	FILE_GROUP_INSTANCE = (1 << 10),
} eFileSel_Params_Flag;


/* files in filesel list: file types */
typedef enum eFileSel_File_Types {
	BLENDERFILE         = (1 << 2),
	BLENDERFILE_BACKUP  = (1 << 3),
	IMAGEFILE           = (1 << 4),
	MOVIEFILE           = (1 << 5),
	PYSCRIPTFILE        = (1 << 6),
	FTFONTFILE          = (1 << 7),
	SOUNDFILE           = (1 << 8),
	TEXTFILE            = (1 << 9),
	MOVIEFILE_ICON      = (1 << 10), /* movie file that preview can't load */
	FOLDERFILE          = (1 << 11), /* represents folders for filtering */
	BTXFILE             = (1 << 12),
	COLLADAFILE         = (1 << 13),
	OPERATORFILE        = (1 << 14), /* from filter_glob operator property */
} eFileSel_File_Types;

/* Selection Flags in filesel: struct direntry, unsigned char selflag */
typedef enum eDirEntry_SelectFlag {
/* 	ACTIVE_FILE         = (1 << 1), */ /* UNUSED */
	HILITED_FILE        = (1 << 2),
	SELECTED_FILE       = (1 << 3),
	EDITING_FILE        = (1 << 4),
} eDirEntry_SelectFlag;

/* SpaceImage->dt_uv */
typedef enum eSpaceImage_UVDT {
	SI_UVDT_OUTLINE = 0,
	SI_UVDT_DASH,
	SI_UVDT_BLACK,
	SI_UVDT_WHITE,
} eSpaceImage_UVDT;

/* SpaceImage->dt_uvstretch */
typedef enum eSpaceImage_UVDT_Stretch {
	SI_UVDT_STRETCH_ANGLE = 0,
	SI_UVDT_STRETCH_AREA,
} eSpaceImage_UVDT_Stretch;

/* SpaceImage->sticky
 * Note DISABLE should be 0, however would also need to re-arrange icon order,
 * also, sticky loc is the default mode so this means we don't need to 'do_versons' */
typedef enum eSpaceImage_Sticky {
	SI_STICKY_LOC      = 0,
	SI_STICKY_DISABLE  = 1,
	SI_STICKY_VERTEX   = 2,
} eSpaceImage_Sticky;

/* SpaceImage->flag */
typedef enum eSpaceImage_Flag {
	SI_BE_SQUARE	      = (1 << 0),
	SI_EDITTILE		      = (1 << 1),
	SI_CLIP_UV		      = (1 << 2),
	SI_DRAWTOOL		      = (1 << 3),
	SI_NO_DRAWFACES	      = (1 << 4),
	SI_DRAWSHADOW         = (1 << 5),
/* 	SI_SELACTFACE         = (1 << 6), */ /* deprecated */
	SI_DEPRECATED2        = (1 << 7),
	SI_DEPRECATED3        = (1 << 8),	/* stick UV selection to mesh vertex (UVs wont always be touching) */
	SI_COORDFLOATS        = (1 << 9),
	SI_PIXELSNAP          = (1 << 10),
	SI_LIVE_UNWRAP        = (1 << 11),
	SI_USE_ALPHA          = (1 << 12),
	SI_SHOW_ALPHA         = (1 << 13),
	SI_SHOW_ZBUF          = (1 << 14),
	
		/* next two for render window display */
	SI_PREVSPACE          = (1 << 15),
	SI_FULLWINDOW         = (1 << 16),
	
	SI_DEPRECATED4        = (1 << 17),
	SI_DEPRECATED5        = (1 << 18),
	
		/* this means that the image is drawn until it reaches the view edge,
		 * in the image view, its unrelated to the 'tile' mode for texface 
		 */
	SI_DRAW_TILE          = (1 << 19),
	SI_SMOOTH_UV          = (1 << 20),
	SI_DRAW_STRETCH       = (1 << 21),
	SI_DISPGP             = (1 << 22), /* DEPRECATED */
	SI_DRAW_OTHER         = (1 << 23),

	SI_COLOR_CORRECTION   = (1 << 24),
} eSpaceImage_Flag;

/* SpaceIpo->flag (Graph Editor Settings) */
typedef enum eGraphEdit_Flag {
	/* OLD DEPRECEATED SETTING */
	/* SIPO_LOCK_VIEW            = (1 << 0), */
	
	/* don't merge keyframes on the same frame after a transform */
	SIPO_NOTRANSKEYCULL       = (1 << 1),
	/* don't show any keyframe handles at all */
	SIPO_NOHANDLES            = (1 << 2),
	/* don't show current frame number beside indicator line */
	SIPO_NODRAWCFRANUM        = (1 << 3),
	/* show timing in seconds instead of frames */
	SIPO_DRAWTIME             = (1 << 4),
	/* only show keyframes for selected F-Curves */
	SIPO_SELCUVERTSONLY       = (1 << 5),
	/* draw names of F-Curves beside the respective curves */
	/* NOTE: currently not used */
	SIPO_DRAWNAMES            = (1 << 6),
	/* show sliders in channels list */
	SIPO_SLIDERS              = (1 << 7),
	/* don't show the horizontal component of the cursor */
	SIPO_NODRAWCURSOR         = (1 << 8),
	/* only show handles of selected keyframes */
	SIPO_SELVHANDLESONLY      = (1 << 9),
	/* temporary flag to force channel selections to be synced with main */
	SIPO_TEMP_NEEDCHANSYNC    = (1 << 10),
	/* don't perform realtime updates */
	SIPO_NOREALTIMEUPDATES    = (1 << 11),
	/* don't draw curves with AA ("beauty-draw") for performance */
	SIPO_BEAUTYDRAW_OFF       = (1 << 12),
	/* draw grouped channels with colors set in group */
	SIPO_NODRAWGCOLORS        = (1 << 13),
} eGraphEdit_Flag;

/* SpaceIpo->mode (Graph Editor Mode) */
typedef enum eGraphEdit_Mode {
		/* all animation curves (from all over Blender) */
	SIPO_MODE_ANIMATION	= 0,
		/* drivers only */
	SIPO_MODE_DRIVERS,
} eGraphEdit_Mode;

/* SpaceText flags (moved from DNA_text_types.h) */
typedef enum eSpaceText_Flags {
	/* scrollable */
	ST_SCROLL_SELECT        = (1 << 0),
	/* clear namespace after script execution (BPY_main.c) */
	ST_CLEAR_NAMESPACE      = (1 << 4), 
	
	ST_FIND_WRAP            = (1 << 5),
	ST_FIND_ALL             = (1 << 6),
	ST_SHOW_MARGIN          = (1 << 7),
	ST_MATCH_CASE           = (1 << 8),
} eSpaceText_Flags;

/* stext->findstr/replacestr */
#define ST_MAX_FIND_STR		256


/* SpaceOops->flag */
typedef enum eSpaceOutliner_Flag {
	SO_TESTBLOCKS           = (1 << 0),
	SO_NEWSELECTED          = (1 << 1),
	SO_HIDE_RESTRICTCOLS    = (1 << 2),
	SO_HIDE_KEYINGSETINFO   = (1 << 3),
} eSpaceOutliner_Flag;

/* SpaceOops->outlinevis */
typedef enum eSpaceOutliner_Mode {
	SO_ALL_SCENES = 0,
	SO_CUR_SCENE,
	SO_VISIBLE,
	SO_SELECTED,
	SO_ACTIVE,
	SO_SAME_TYPE,
	SO_GROUPS,
	SO_LIBRARIES,
	SO_VERSE_SESSION,
	SO_VERSE_MS,
	SO_SEQUENCE,
	SO_DATABLOCKS,
	SO_USERDEF,
	SO_KEYMAP,
} eSpaceOutliner_Mode;

/* SpaceOops->storeflag */
typedef enum eSpaceOutliner_StoreFlag {
		/* rebuild tree */
	SO_TREESTORE_CLEANUP    = (1 << 0),
		/* if set, it allows redraws. gets set for some allqueue events */
	SO_TREESTORE_REDRAW     = (1 << 1),
} eSpaceOutliner_StoreFlag;

/* outliner search flags (SpaceOops->search_flags) */
typedef enum eSpaceOutliner_Search_Flags {
	SO_FIND_CASE_SENSITIVE  = (1 << 0),
	SO_FIND_COMPLETE        = (1 << 1),
	SO_SEARCH_RECURSIVE     = (1 << 2),
} eSpaceOutliner_Search_Flags;

/* headerbuttons: 450-499 */

#define B_IMASELHOME		451
#define B_IMASELREMOVEBIP	452

/* nla->flag */
typedef enum eSpaceNla_Flag {
	/* flags (1<<0), (1<<1), and (1<<3) are depreceated flags from old verisons */

	/* draw timing in seconds instead of frames */
	SNLA_DRAWTIME          = (1 << 2),
	/* don't draw frame number beside frame indicator */
	SNLA_NODRAWCFRANUM     = (1 << 4),
	/* don't draw influence curves on strips */
	SNLA_NOSTRIPCURVES     = (1 << 5),
	/* don't perform realtime updates */
	SNLA_NOREALTIMEUPDATES = (1 << 6),
} eSpaceNla_Flag;

/* time->flag */
typedef enum eTimeline_Flag {
	/* show timing in frames instead of in seconds */
	TIME_DRAWFRAMES    = (1 << 0),
	/* show time indicator box beside the frame number */
	TIME_CFRA_NUM      = (1 << 1),
	/* only keyframes from active/selected channels get shown */
	TIME_ONLYACTSEL    = (1 << 2),
} eTimeline_Flag;

/* time->redraws (now screen->redraws_flag) */
typedef enum eScreen_Redraws_Flag {
	TIME_REGION            = (1 << 0),
	TIME_ALL_3D_WIN        = (1 << 1),
	TIME_ALL_ANIM_WIN      = (1 << 2),
	TIME_ALL_BUTS_WIN      = (1 << 3),
	TIME_WITH_SEQ_AUDIO    = (1 << 4), /* DEPRECATED */
	TIME_SEQ               = (1 << 5),
	TIME_ALL_IMAGE_WIN     = (1 << 6),
	TIME_CONTINUE_PHYSICS  = (1 << 7),
	TIME_NODES             = (1 << 8),
	TIME_CLIPS             = (1 << 9),
} eScreen_Redraws_Flag;

/* time->cache */
typedef enum eTimeline_Cache_Flag {
	TIME_CACHE_DISPLAY       = (1 << 0),
	TIME_CACHE_SOFTBODY      = (1 << 1),
	TIME_CACHE_PARTICLES     = (1 << 2),
	TIME_CACHE_CLOTH         = (1 << 3),
	TIME_CACHE_SMOKE         = (1 << 4),
	TIME_CACHE_DYNAMICPAINT  = (1 << 5),
} eTimeline_Cache_Flag;

/* sseq->mainb */
typedef enum eSpaceSeq_RegionType {
	SEQ_DRAW_SEQUENCE = 0,
	SEQ_DRAW_IMG_IMBUF,
	SEQ_DRAW_IMG_WAVEFORM,
	SEQ_DRAW_IMG_VECTORSCOPE,
	SEQ_DRAW_IMG_HISTOGRAM,
} eSpaceSeq_RegionType;

/* sseq->flag */
typedef enum eSpaceSeq_Flag {
	SEQ_DRAWFRAMES              = (1 << 0),
	SEQ_MARKER_TRANS            = (1 << 1),
	SEQ_DRAW_COLOR_SEPARATED    = (1 << 2),
	SEQ_DRAW_SAFE_MARGINS       = (1 << 3),
	SEQ_DRAW_GPENCIL            = (1 << 4),	/* DEPRECATED */
	SEQ_NO_DRAW_CFRANUM         = (1 << 5),
} eSpaceSeq_Flag;

/* sseq->view */
typedef enum eSpaceSeq_Displays {
	SEQ_VIEW_SEQUENCE = 1,
	SEQ_VIEW_PREVIEW,
	SEQ_VIEW_SEQUENCE_PREVIEW,
} eSpaceSeq_Dispays;

/* sseq->render_size */
typedef enum eSpaceSeq_Proxy_RenderSize {
	SEQ_PROXY_RENDER_SIZE_NONE      =  -1,
	SEQ_PROXY_RENDER_SIZE_SCENE     =   0,
	SEQ_PROXY_RENDER_SIZE_25        =  25,
	SEQ_PROXY_RENDER_SIZE_50        =  50,
	SEQ_PROXY_RENDER_SIZE_75        =  75,
	SEQ_PROXY_RENDER_SIZE_100       =  99,
	SEQ_PROXY_RENDER_SIZE_FULL      = 100
} eSpaceSeq_Proxy_RenderSize;

/* SpaceClip->flag */
typedef enum eSpaceClip_Flag {
	SC_SHOW_MARKER_PATTERN = (1 << 0),
	SC_SHOW_MARKER_SEARCH  = (1 << 1),
	SC_LOCK_SELECTION      = (1 << 2),
	SC_SHOW_TINY_MARKER    = (1 << 3),
	SC_SHOW_TRACK_PATH     = (1 << 4),
	SC_SHOW_BUNDLES        = (1 << 5),
	SC_MUTE_FOOTAGE        = (1 << 6),
	SC_HIDE_DISABLED       = (1 << 7),
	SC_SHOW_NAMES          = (1 << 8),
	SC_SHOW_GRID           = (1 << 9),
	SC_SHOW_STABLE         = (1 << 10),
	SC_MANUAL_CALIBRATION  = (1 << 11),
/*	SC_SHOW_GPENCIL        = (1 << 12),*/	/* UNUSED */
	SC_SHOW_FILTERS        = (1 << 13),
	SC_SHOW_GRAPH_FRAMES   = (1 << 14),
	SC_SHOW_GRAPH_TRACKS   = (1 << 15),
/*	SC_SHOW_PYRAMID_LEVELS = (1 << 16), */	/* UNUSED */
	SC_LOCK_TIMECURSOR     = (1 << 17),
	SC_SHOW_SECONDS        = (1 << 18),
} eSpaceClip_Flag;

/* SpaceClip->mode */
typedef enum eSpaceClip_Mode {
	SC_MODE_TRACKING = 0,
	SC_MODE_RECONSTRUCTION,
	SC_MODE_DISTORTION,
} eSpaceClip_Mode;

/* SpaceClip->view */
typedef enum eSpaceClip_View {
	SC_VIEW_CLIP = 0,
	SC_VIEW_GRAPH,
	SC_VIEW_DOPESHEET,
} eSpaceClip_View;

/* SpaceClip->dope_sort */
typedef enum eSpaceClip_Dopesheet_Sort {
	SC_DOPE_SORT_NAME = 0,
	SC_DOPE_SORT_LONGEST,
	SC_DOPE_SORT_TOTAL,
} eSpaceClip_Dopesheet_Sort;

/* SpaceClip->dope_flag */
typedef enum eSpaceClip_Dopesheet_Flag {
	SC_DOPE_SORT_INVERSE    = (1 << 0),
} eSpaceClip_Dopesheet_Flag;

/* space types, moved from DNA_screen_types.h */
/* Do NOT change order, append on end. types are hardcoded needed */
typedef enum eSpace_Type {
	SPACE_EMPTY,
	SPACE_VIEW3D,
	SPACE_IPO,
	SPACE_OUTLINER,
	SPACE_BUTS,
	SPACE_FILE,
	SPACE_IMAGE,		
	SPACE_INFO,
	SPACE_SEQ,
	SPACE_TEXT,
	SPACE_IMASEL, /* deprecated */
	SPACE_SOUND, /* Deprecated */
	SPACE_ACTION,
	SPACE_NLA,
	SPACE_SCRIPT, /* Deprecated */
	SPACE_TIME,
	SPACE_NODE,
	SPACE_LOGIC,
	SPACE_CONSOLE,
	SPACE_USERPREF,
	SPACE_CLIP,
	
	SPACEICONMAX = SPACE_CLIP
} eSpace_Type;

#endif
