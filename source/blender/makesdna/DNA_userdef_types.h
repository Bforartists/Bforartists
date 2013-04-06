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

/** \file DNA_userdef_types.h
 *  \ingroup DNA
 *  \since mar-2001
 *  \author nzc
 */

#ifndef __DNA_USERDEF_TYPES_H__
#define __DNA_USERDEF_TYPES_H__

#include "DNA_listBase.h"
#include "DNA_texture_types.h" /* ColorBand */

#ifdef __cplusplus
extern "C" {
#endif

/* themes; defines in BIF_resource.h */
struct ColorBand;

/* ************************ style definitions ******************** */

#define MAX_STYLE_NAME	64

/* default uifont_id offered by Blender */
typedef enum eUIFont_ID {
	UIFONT_DEFAULT	= 0,
/*	UIFONT_BITMAP	= 1 */ /* UNUSED */
	
	/* free slots */
	UIFONT_CUSTOM1	= 2,
	UIFONT_CUSTOM2	= 3
} eUIFont_ID;

/* default fonts to load/initalize */
/* first font is the default (index 0), others optional */
typedef struct uiFont {
	struct uiFont *next, *prev;
	char filename[1024];/* 1024 = FILE_MAX */
	short blf_id;		/* from blfont lib */
	short uifont_id;	/* own id */
	short r_to_l;		/* fonts that read from left to right */
	short hinting;
} uiFont;

/* this state defines appearance of text */
typedef struct uiFontStyle {
	short uifont_id;		/* saved in file, 0 is default */
	short points;			/* actual size depends on 'global' dpi */
	short kerning;			/* unfitted or default kerning value. */
	char pad[6];
	short italic, bold;		/* style hint */
	short shadow;			/* value is amount of pixels blur */
	short shadx, shady;		/* shadow offset in pixels */
	short align;			/* text align hint */
	float shadowalpha;		/* total alpha */
	float shadowcolor;		/* 1 value, typically white or black anyway */
} uiFontStyle;

/* uiFontStyle->align */
typedef enum eFontStyle_Align {
	UI_STYLE_TEXT_LEFT		= 0,
	UI_STYLE_TEXT_CENTER	= 1,
	UI_STYLE_TEXT_RIGHT		= 2
} eFontStyle_Align;


/* this is fed to the layout engine and widget code */

typedef struct uiStyle {
	struct uiStyle *next, *prev;
	
	char name[64];			/* MAX_STYLE_NAME */
	
	uiFontStyle paneltitle;
	uiFontStyle grouplabel;
	uiFontStyle widgetlabel;
	uiFontStyle widget;
	
	float panelzoom;
	
	short minlabelchars;	/* in characters */
	short minwidgetchars;	/* in characters */

	short columnspace;
	short templatespace;
	short boxspace;
	short buttonspacex;
	short buttonspacey;
	short panelspace;
	short panelouter;

	short pad;
} uiStyle;

typedef struct uiWidgetColors {
	char outline[4];
	char inner[4];
	char inner_sel[4];
	char item[4];
	char text[4];
	char text_sel[4];
	short shaded;
	short shadetop, shadedown;
	short alpha_check;
} uiWidgetColors;

typedef struct uiWidgetStateColors {
	char inner_anim[4];
	char inner_anim_sel[4];
	char inner_key[4];
	char inner_key_sel[4];
	char inner_driven[4];
	char inner_driven_sel[4];
	float blend, pad;
} uiWidgetStateColors;

typedef struct uiPanelColors {
	char header[4];
	char back[4];
	short show_header;
	short show_back;
	int pad;
} uiPanelColors;

typedef struct uiGradientColors {
	char gradient[4];
	char high_gradient[4];
	int show_grad;
	int pad2;
} uiGradientColors;

typedef struct ThemeUI {
	/* Interface Elements (buttons, menus, icons) */
	uiWidgetColors wcol_regular, wcol_tool, wcol_text;
	uiWidgetColors wcol_radio, wcol_option, wcol_toggle;
	uiWidgetColors wcol_num, wcol_numslider;
	uiWidgetColors wcol_menu, wcol_pulldown, wcol_menu_back, wcol_menu_item, wcol_tooltip;
	uiWidgetColors wcol_box, wcol_scroll, wcol_progress, wcol_list_item;
	
	uiWidgetStateColors wcol_state;

	uiPanelColors panel; /* depricated, but we keep it for do_versions (2.66.1) */

	/* fac: 0 - 1 for blend factor, width in pixels */
	float menu_shadow_fac;
	short menu_shadow_width;
	
	short pad;
	
	char iconfile[256];	// FILE_MAXFILE length
	float icon_alpha;

	/* Axis Colors */
	char xaxis[4], yaxis[4], zaxis[4];
} ThemeUI;

/* try to put them all in one, if needed a special struct can be created as well
 * for example later on, when we introduce wire colors for ob types or so...
 */
typedef struct ThemeSpace {
	/* main window colors */
	char back[4];
	char title[4]; 	/* panel title */
	char text[4];
	char text_hi[4];
	
	/* header colors */
	char header[4];			/* region background */
	char header_title[4];	/* unused */
	char header_text[4];
	char header_text_hi[4];

	/* button/tool regions */
	char button[4];			/* region background */
	char button_title[4];	/* panel title */
	char button_text[4];
	char button_text_hi[4];
	
	/* listview regions */
	char list[4];			/* region background */
	char list_title[4]; 	/* panel title */
	char list_text[4];
	char list_text_hi[4];
	
	/* float panel */
/*	char panel[4];			unused */
/*	char panel_title[4];	unused */
/*	char panel_text[4];		unused */
/*	char panel_text_hi[4];	unused */
	
	/* note, cannot use name 'panel' because of DNA mapping old files */
	uiPanelColors panelcolors;

	uiGradientColors gradients;

	char shade1[4];
	char shade2[4];
	
	char hilite[4];
	char grid[4]; 
	
	char wire[4], select[4];
	char lamp[4], speaker[4], empty[4], camera[4], pad[8];
	char active[4], group[4], group_active[4], transform[4];
	char vertex[4], vertex_select[4], vertex_unreferenced[4];
	char edge[4], edge_select[4];
	char edge_seam[4], edge_sharp[4], edge_facesel[4], edge_crease[4];
	char face[4], face_select[4];	/* solid faces */
	char face_dot[4];				/*  selected color */
	char extra_edge_len[4], extra_edge_angle[4], extra_face_angle[4], extra_face_area[4];
	char normal[4];
	char vertex_normal[4];
	char bone_solid[4], bone_pose[4], bone_pose_active[4];
	char strip[4], strip_select[4];
	char cframe[4];
	char freestyle_edge_mark[4], freestyle_face_mark[4];
	
	char nurb_uline[4], nurb_vline[4];
	char act_spline[4], nurb_sel_uline[4], nurb_sel_vline[4], lastsel_point[4];
	
	char handle_free[4], handle_auto[4], handle_vect[4], handle_align[4], handle_auto_clamped[4];
	char handle_sel_free[4], handle_sel_auto[4], handle_sel_vect[4], handle_sel_align[4], handle_sel_auto_clamped[4];
	
	char ds_channel[4], ds_subchannel[4]; /* dopesheet */
	
	char console_output[4], console_input[4], console_info[4], console_error[4];
	char console_cursor[4], console_select[4], pad1[4];
	
	char vertex_size, outline_width, facedot_size;
	char noodle_curving;

	/* syntax for textwindow and nodes */
	char syntaxl[4], syntaxs[4];
	char syntaxb[4], syntaxn[4];
	char syntaxv[4], syntaxc[4];
	char syntaxd[4], syntaxr[4];
	
	char movie[4], movieclip[4], mask[4], image[4], scene[4], audio[4];		/* for sequence editor */
	char effect[4], transition[4], meta[4];
	char editmesh_active[4]; 

	char handle_vertex[4];
	char handle_vertex_select[4];
	char pad2[4];
	
	char handle_vertex_size;
	
	char marker_outline[4], marker[4], act_marker[4], sel_marker[4], dis_marker[4], lock_marker[4];
	char bundle_solid[4];
	char path_before[4], path_after[4];
	char camera_path[4];
	char hpad[3];
	
	char preview_back[4];
	char preview_stitch_face[4];
	char preview_stitch_edge[4];
	char preview_stitch_vert[4];
	char preview_stitch_stitchable[4];
	char preview_stitch_unstitchable[4];
	char preview_stitch_active[4];
	
	char match[4];				/* outliner - filter match */
	char selected_highlight[4];	/* outliner - selected item */

	char skin_root[4]; /* Skin modifier root color */
	
	/* NLA */
	char anim_active[4];	 /* Active Action + Summary Channel */
	char anim_non_active[4]; /* Active Action = NULL */
	
	char nla_tweaking[4];   /* NLA 'Tweaking' action/strip */
	char nla_tweakdupli[4]; /* NLA - warning color for duplicate instances of tweaking strip */
	
	char nla_transition[4], nla_transition_sel[4]; /* NLA "Transition" strips */
	char nla_meta[4], nla_meta_sel[4];             /* NLA "Meta" strips */
	char nla_sound[4], nla_sound_sel[4];           /* NLA "Sound" strips */
} ThemeSpace;


/* set of colors for use as a custom color set for Objects/Bones wire drawing */
typedef struct ThemeWireColor {
	char 	solid[4];
	char	select[4];
	char 	active[4];
	
	short 	flag;
	short 	pad;
} ThemeWireColor; 

/* flags for ThemeWireColor */
typedef enum eWireColor_Flags {
	TH_WIRECOLOR_CONSTCOLS	= (1 << 0),
	TH_WIRECOLOR_TEXTCOLS	= (1 << 1),
} eWireColor_Flags;

/* A theme */
typedef struct bTheme {
	struct bTheme *next, *prev;
	char name[32];
	
	ThemeUI tui;
	
	/* Individual Spacetypes */
	ThemeSpace tbuts;
	ThemeSpace tv3d;
	ThemeSpace tfile;
	ThemeSpace tipo;
	ThemeSpace tinfo;
	ThemeSpace tact;
	ThemeSpace tnla;
	ThemeSpace tseq;
	ThemeSpace tima;
	ThemeSpace text;
	ThemeSpace toops;
	ThemeSpace ttime;
	ThemeSpace tnode;
	ThemeSpace tlogic;
	ThemeSpace tuserpref;
	ThemeSpace tconsole;
	ThemeSpace tclip;
	
	/* 20 sets of bone colors for this theme */
	ThemeWireColor tarm[20];
	/*ThemeWireColor tobj[20];*/
	
	int active_theme_area, pad;
} bTheme;

/* for the moment only the name. may want to store options with this later */
typedef struct bAddon {
	struct bAddon *next, *prev;
	char module[64];
	IDProperty *prop;  /* User-Defined Properties on this  Addon (for storing preferences) */
} bAddon;

typedef struct SolidLight {
	int flag, pad;
	float col[4], spec[4], vec[4];
} SolidLight;

typedef struct UserDef {
	/* UserDef has separate do-version handling, and can be read from other files */
	int versionfile, subversionfile;
	
	int flag, dupflag;
	int savetime;
	char tempdir[768];	/* FILE_MAXDIR length */
	char fontdir[768];
	char renderdir[1024]; /* FILE_MAX length */
	char textudir[768];
	char pythondir[768];
	char sounddir[768];
	char i18ndir[768];
	char image_editor[1024];    /* 1024 = FILE_MAX */
	char anim_player[1024];	    /* 1024 = FILE_MAX */
	int anim_player_preset;
	
	short v2d_min_gridsize;		/* minimum spacing between gridlines in View2D grids */
	short timecode_style;		/* style of timecode display */
	
	short versions;
	short dbl_click_time;
	
	short gameflags;
	short wheellinescroll;
	int uiflag, uiflag2;
	int language;
	short userpref, viewzoom;
	
	int mixbufsize;
	int audiodevice;
	int audiorate;
	int audioformat;
	int audiochannels;

	int scrollback; /* console scrollback limit */
	int dpi;		/* range 48-128? */
	short encoding;
	short transopts;
	short menuthreshold1, menuthreshold2;
	
	struct ListBase themes;
	struct ListBase uifonts;
	struct ListBase uistyles;
	struct ListBase keymaps  DNA_DEPRECATED; /* deprecated in favor of user_keymaps */
	struct ListBase user_keymaps;
	struct ListBase addons;
	char keyconfigstr[64];
	
	short undosteps;
	short undomemory;
	short gp_manhattendist, gp_euclideandist, gp_eraser;
	short gp_settings;
	short tb_leftmouse, tb_rightmouse;
	struct SolidLight light[3];
	short tw_hotspot, tw_flag, tw_handlesize, tw_size;
	short textimeout, texcollectrate;
	short wmdrawmethod; /* removed wmpad */
	short dragthreshold;
	int memcachelimit;
	int prefetchframes;
	short frameserverport;
	short pad_rot_angle;	/* control the rotation step of the view when PAD2, PAD4, PAD6&PAD8 is use */
	short obcenter_dia;
	short rvisize;			/* rotating view icon size */
	short rvibright;		/* rotating view icon brightness */
	short recent_files;		/* maximum number of recently used files to remember  */
	short smooth_viewtx;	/* miliseconds to spend spinning the view */
	short glreslimit;
	short curssize;
	short color_picker_type;
	short ipo_new;			/* interpolation mode for newly added F-Curves */
	short keyhandles_new;	/* handle types for newly added keyframes */

	short scrcastfps;		/* frame rate for screencast to be played back */
	short scrcastwait;		/* milliseconds between screencast snapshots */
	
	short widget_unit;		/* private, defaults to 20 for 72 DPI setting */
	short anisotropic_filter;
	short use_16bit_textures, use_gpu_mipmap;

	float ndof_sensitivity;	/* overall sensitivity of 3D mouse */
	float ndof_orbit_sensitivity;
	int ndof_flag;			/* flags for 3D mouse */

	short ogl_multisamples;	/* amount of samples for OpenGL FSA, if zero no FSA */

	short image_gpubuffer_limit; /* If set, amount of mega-pixels to use for texture drawing of images */
	
	float glalphaclip;
	
	short autokey_mode;		/* autokeying mode */
	short autokey_flag;		/* flags for autokeying */
	
	short text_render, pad9;		/* options for text rendering */

	struct ColorBand coba_weight;	/* from texture.h */

	float sculpt_paint_overlay_col[3];

	short tweak_threshold;
	short pad3;

	char author[80];	/* author name for file formats supporting it */

	int compute_device_type;
	int compute_device_id;
	
	float fcu_inactive_alpha;	/* opacity of inactive F-Curves in F-Curve Editor */
	float pixelsize;			/* private, set by GHOST, to multiply DPI with */
} UserDef;

extern UserDef U; /* from blenkernel blender.c */

/* ***************** USERDEF ****************** */

/* userpref/section */
typedef enum eUserPref_Section {
	USER_SECTION_INTERFACE	= 0,
	USER_SECTION_EDIT		= 1,
	USER_SECTION_FILE		= 2,
	USER_SECTION_SYSTEM		= 3,
	USER_SECTION_THEME		= 4,
	USER_SECTION_INPUT		= 5,
	USER_SECTION_ADDONS 	= 6,
} eUserPref_Section;

/* flag */
typedef enum eUserPref_Flag {
	USER_AUTOSAVE			= (1 << 0),
/*	USER_AUTOGRABGRID		= (1 << 1),	deprecated */
/*	USER_AUTOROTGRID		= (1 << 2),	deprecated */
/*	USER_AUTOSIZEGRID		= (1 << 3),	deprecated */
	USER_SCENEGLOBAL		= (1 << 4),
	USER_TRACKBALL			= (1 << 5),
/*	USER_DUPLILINK		= (1 << 6),	deprecated */
/*	USER_FSCOLLUM			= (1 << 7),	deprecated */
	USER_MAT_ON_OB			= (1 << 8),
/*	USER_NO_CAPSLOCK		= (1 << 9), */  /* not used anywhere */
/*	USER_VIEWMOVE			= (1 << 10), */ /* not used anywhere */
	USER_TOOLTIPS			= (1 << 11),
	USER_TWOBUTTONMOUSE		= (1 << 12),
	USER_NONUMPAD			= (1 << 13),
	USER_LMOUSESELECT		= (1 << 14),
	USER_FILECOMPRESS		= (1 << 15),
	USER_SAVE_PREVIEWS		= (1 << 16),
	USER_CUSTOM_RANGE		= (1 << 17),
	USER_ADD_EDITMODE		= (1 << 18),
	USER_ADD_VIEWALIGNED	= (1 << 19),
	USER_RELPATHS			= (1 << 20),
	USER_RELEASECONFIRM		= (1 << 21),
	USER_SCRIPT_AUTOEXEC_DISABLE	= (1 << 22),
	USER_FILENOUI			= (1 << 23),
	USER_NONEGFRAMES		= (1 << 24),
	USER_TXT_TABSTOSPACES_DISABLE	= (1 << 25),
	USER_TOOLTIPS_PYTHON    = (1 << 26),
} eUserPref_Flag;
	
/* helper macro for checking frame clamping */
#define FRAMENUMBER_MIN_CLAMP(cfra)  {                                        \
	if ((U.flag & USER_NONEGFRAMES) && (cfra < 0))                            \
		cfra = 0;                                                             \
	} (void)0

/* viewzoom */
typedef enum eViewZoom_Style {
	USER_ZOOM_CONT			= 0,
	USER_ZOOM_SCALE			= 1,
	USER_ZOOM_DOLLY			= 2
} eViewZoom_Style;

/* uiflag */
typedef enum eUserpref_UI_Flag {
	/* flags 0 and 1 were old flags (for autokeying) that aren't used anymore */
	USER_WHEELZOOMDIR		= (1 << 2),
	USER_FILTERFILEEXTS		= (1 << 3),
	USER_DRAWVIEWINFO		= (1 << 4),
	USER_PLAINMENUS			= (1 << 5),
	/* flags 6 and 7 were old flags that are no-longer used */
	USER_ALLWINCODECS		= (1 << 8),
	USER_MENUOPENAUTO		= (1 << 9),
	USER_ZBUF_CURSOR		= (1 << 10),
	USER_AUTOPERSP     		= (1 << 11),
	USER_LOCKAROUND     	= (1 << 12),
	USER_GLOBALUNDO     	= (1 << 13),
	USER_ORBIT_SELECTION	= (1 << 14),
	USER_ZBUF_ORBIT			= (1 << 15),
	USER_HIDE_DOT			= (1 << 16),
	USER_SHOW_ROTVIEWICON	= (1 << 17),
	USER_SHOW_VIEWPORTNAME	= (1 << 18),
	USER_CAM_LOCK_NO_PARENT	= (1 << 19),
	USER_ZOOM_TO_MOUSEPOS	= (1 << 20),
	USER_SHOW_FPS			= (1 << 21),
	USER_MMB_PASTE			= (1 << 22),
	USER_MENUFIXEDORDER		= (1 << 23),
	USER_CONTINUOUS_MOUSE	= (1 << 24),
	USER_ZOOM_INVERT		= (1 << 25),
	USER_ZOOM_HORIZ			= (1 << 26), /* for CONTINUE and DOLLY zoom */
	USER_SPLASH_DISABLE		= (1 << 27),
	USER_HIDE_RECENT		= (1 << 28),
	USER_SHOW_THUMBNAILS	= (1 << 29),
	USER_QUIT_PROMPT		= (1 << 30),
	USER_HIDE_SYSTEM_BOOKMARKS = (1 << 31)
} eUserpref_UI_Flag;

/* uiflag2 */
typedef enum eUserpref_UI_Flag2 {
	USER_KEEP_SESSION		= (1 << 0),
	USER_REGION_OVERLAP		= (1 << 1),
	USER_TRACKPAD_NATURAL	= (1 << 2)
} eUserpref_UI_Flag2;
	
/* Auto-Keying mode */
typedef enum eAutokey_Mode {
	/* AUTOKEY_ON is a bitflag */
	AUTOKEY_ON             = 1,
	
	/* AUTOKEY_ON + 2**n...  (i.e. AUTOKEY_MODE_NORMAL = AUTOKEY_ON + 2) to preserve setting, even when autokey turned off  */
	AUTOKEY_MODE_NORMAL    = 3,
	AUTOKEY_MODE_EDITKEYS  = 5
} eAutokey_Mode;

/* Auto-Keying flag
 * U.autokey_flag (not strictly used when autokeying only - is also used when keyframing these days)
 * note: AUTOKEY_FLAG_* is used with a macro, search for lines like IS_AUTOKEY_FLAG(INSERTAVAIL)
 */
typedef enum eAutokey_Flag {
	AUTOKEY_FLAG_INSERTAVAIL	= (1 << 0),
	AUTOKEY_FLAG_INSERTNEEDED	= (1 << 1),
	AUTOKEY_FLAG_AUTOMATKEY		= (1 << 2),
	AUTOKEY_FLAG_XYZ2RGB		= (1 << 3),
	
	/* toolsettings->autokey_flag */
	AUTOKEY_FLAG_ONLYKEYINGSET	= (1 << 6),
	AUTOKEY_FLAG_NOWARNING		= (1 << 7),
	ANIMRECORD_FLAG_WITHNLA		= (1 << 10),
} eAutokey_Flag;

/* transopts */
typedef enum eUserpref_Translation_Flags {
	USER_TR_TOOLTIPS		= (1 << 0),
	USER_TR_IFACE			= (1 << 1),
/*	USER_TR_MENUS			= (1 << 2),  deprecated */
/*	USER_TR_FILESELECT		= (1 << 3),  deprecated */
/*	USER_TR_TEXTEDIT		= (1 << 4),  deprecated */
	USER_DOTRANSLATE		= (1 << 5),
	USER_USETEXTUREFONT		= (1 << 6),
/*	CONVERT_TO_UTF8			= (1 << 7),  deprecated */
	USER_TR_NEWDATANAME		= (1 << 8),
} eUserpref_Translation_Flags;

/* dupflag */
typedef enum eDupli_ID_Flags {
	USER_DUP_MESH			= (1 << 0),
	USER_DUP_CURVE			= (1 << 1),
	USER_DUP_SURF			= (1 << 2),
	USER_DUP_FONT			= (1 << 3),
	USER_DUP_MBALL			= (1 << 4),
	USER_DUP_LAMP			= (1 << 5),
	USER_DUP_IPO			= (1 << 6),
	USER_DUP_MAT			= (1 << 7),
	USER_DUP_TEX			= (1 << 8),
	USER_DUP_ARM			= (1 << 9),
	USER_DUP_ACT			= (1 << 10),
	USER_DUP_PSYS			= (1 << 11)
} eDupli_ID_Flags;

/* gameflags */
typedef enum eOpenGL_RenderingOptions {
	/* USER_DEPRECATED_FLAG	= (1 << 0), */
	/* USER_DISABLE_SOUND		= (1 << 1), */ /* deprecated, don't use without checking for */
	                                     /* backwards compatibilty in do_versions! */
	USER_DISABLE_MIPMAP		= (1 << 2),
	USER_DISABLE_VBO		= (1 << 3),
	/* USER_DISABLE_AA			= (1 << 4), */ /* DEPRECATED */
} eOpenGL_RenderingOptions;

/* wm draw method */
typedef enum eWM_DrawMethod {
	USER_DRAW_TRIPLE		= 0,
	USER_DRAW_OVERLAP		= 1,
	USER_DRAW_FULL			= 2,
	USER_DRAW_AUTOMATIC		= 3,
	USER_DRAW_OVERLAP_FLIP	= 4,
} eWM_DrawMethod;

/* text draw options */
typedef enum eText_Draw_Options {
	USER_TEXT_DISABLE_AA	= (1 << 0),
} eText_Draw_Options;

/* tw_flag (transform widget) */

/* gp_settings (Grease Pencil Settings) */
typedef enum eGP_UserdefSettings {
	GP_PAINT_DOSMOOTH		= (1 << 0),
	GP_PAINT_DOSIMPLIFY		= (1 << 1),
} eGP_UserdefSettings;

/* color picker types */
typedef enum eColorPicker_Types {
	USER_CP_CIRCLE		= 0,
	USER_CP_SQUARE_SV	= 1,
	USER_CP_SQUARE_HS	= 2,
	USER_CP_SQUARE_HV	= 3,
} eColorPicker_Types;

/* timecode display styles */
typedef enum eTimecodeStyles {
	/* as little info as is necessary to show relevant info
	 * with '+' to denote the frames 
	 * i.e. HH:MM:SS+FF, MM:SS+FF, SS+FF, or MM:SS
	 */
	USER_TIMECODE_MINIMAL		= 0,
	
	/* reduced SMPTE - (HH:)MM:SS:FF */
	USER_TIMECODE_SMPTE_MSF		= 1,
	
	/* full SMPTE - HH:MM:SS:FF */
	USER_TIMECODE_SMPTE_FULL	= 2,
	
	/* milliseconds for sub-frames - HH:MM:SS.sss */
	USER_TIMECODE_MILLISECONDS	= 3,
	
	/* seconds only */
	USER_TIMECODE_SECONDS_ONLY	= 4,
} eTimecodeStyles;

/* theme drawtypes */
/* XXX: These are probably only for the old UI engine? */
typedef enum eTheme_DrawTypes {
	TH_MINIMAL  	= 0,
	TH_ROUNDSHADED	= 1,
	TH_ROUNDED  	= 2,
	TH_OLDSKOOL 	= 3,
	TH_SHADED   	= 4
} eTheme_DrawTypes;

/* ndof_flag (3D mouse options) */
typedef enum eNdof_Flag {
	NDOF_SHOW_GUIDE     = (1 << 0),
	NDOF_FLY_HELICOPTER = (1 << 1),
	NDOF_LOCK_HORIZON   = (1 << 2),

	/* the following might not need to be saved between sessions,
	 * but they do need to live somewhere accessible... */
	NDOF_SHOULD_PAN     = (1 << 3),
	NDOF_SHOULD_ZOOM    = (1 << 4),
	NDOF_SHOULD_ROTATE  = (1 << 5),

	/* orbit navigation modes
	 * only two options, so it's sort of a hybrid bool/enum
	 * if ((U.ndof_flag & NDOF_ORBIT_MODE) == NDOF_OM_OBJECT)... */

	// NDOF_ORBIT_MODE     = (1 << 6),
	// #define NDOF_OM_TARGETCAMERA 0
	// #define NDOF_OM_OBJECT      NDOF_ORBIT_MODE

	/* actually... users probably don't care about what the mode
	 * is called, just that it feels right */
	/* zoom is up/down if this flag is set (otherwise forward/backward) */
	NDOF_ZOOM_UPDOWN        = (1 << 7),
	NDOF_ZOOM_INVERT        = (1 << 8),
	NDOF_ROTATE_INVERT_AXIS = (1 << 9),
	NDOF_TILT_INVERT_AXIS   = (1 << 10),
	NDOF_ROLL_INVERT_AXIS   = (1 << 11),
	NDOF_PANX_INVERT_AXIS   = (1 << 12),
	NDOF_PANY_INVERT_AXIS   = (1 << 13),
	NDOF_PANZ_INVERT_AXIS   = (1 << 14),
	NDOF_TURNTABLE          = (1 << 15),
} eNdof_Flag;

/* compute_device_type */
typedef enum eCompute_Device_Type {
	USER_COMPUTE_DEVICE_NONE	= 0,
	USER_COMPUTE_DEVICE_OPENCL	= 1,
	USER_COMPUTE_DEVICE_CUDA	= 2,
} eCompute_Device_Type;

	
typedef enum eMultiSample_Type {
	USER_MULTISAMPLE_NONE	= 0,
	USER_MULTISAMPLE_2	= 2,
	USER_MULTISAMPLE_4	= 4,
	USER_MULTISAMPLE_8	= 8,
	USER_MULTISAMPLE_16	= 16,
} eMultiSample_Type;
	
	

#ifdef __cplusplus
}
#endif

#endif
