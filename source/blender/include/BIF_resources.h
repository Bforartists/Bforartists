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

#ifndef BIF_RESOURCES_H
#define BIF_RESOURCES_H

typedef enum {
#define BIFICONID_FIRST		(ICON_VIEW3D)
	ICON_VIEW3D,
	ICON_IPO,
	ICON_OOPS,
	ICON_BUTS,
	ICON_FILESEL,
	ICON_IMAGE_COL,
	ICON_INFO,
	ICON_SEQUENCE,
	ICON_TEXT,
	ICON_IMASEL,
	ICON_SOUND,
	ICON_ACTION,
	ICON_NLA,
	ICON_VIEWZOOM,
	ICON_VIEWMOVE,
	ICON_HOME,
	ICON_CLIPUV_DEHLT,
	ICON_CLIPUV_HLT,
	ICON_SOME_WACKY_VERTS_AND_LINES,
	ICON_A_WACKY_VERT_AND_SOME_LINES,
	ICON_VPAINT_COL,

	ICON_ORTHO,
	ICON_PERSP,
	ICON_CAMERA,
	ICON_BLANK1,
	ICON_BBOX,
	ICON_WIRE,
	ICON_SOLID,
	ICON_SMOOTH,
	ICON_POTATO,
	ICON_BLANK2,
	ICON_NORMALVIEW,
	ICON_LOCALVIEW,
	ICON_UNUSEDVIEW,
	ICON_BLANK3,
	ICON_SORTALPHA,
	ICON_SORTTIME,
	ICON_SORTSIZE,
	ICON_LONGDISPLAY,
	ICON_SHORTDISPLAY,
	ICON_BLANK4,
	ICON_BLANK5,

	ICON_VIEW_AXIS_ALL,
	ICON_VIEW_AXIS_NONE,
	ICON_VIEW_AXIS_NONE2,
	ICON_VIEW_AXIS_TOP,
	ICON_VIEW_AXIS_FRONT,
	ICON_VIEW_AXIS_SIDE,
	ICON_POSE_DEHLT,
	ICON_POSE_HLT,
	ICON_BORDERMOVE,
	ICON_MAYBE_ITS_A_LASSO,
	ICON_BLANK6,
	ICON_ROTATE,
	ICON_CURSOR,
	ICON_ROTATECOLLECTION,
	ICON_ROTATECENTER,
	ICON_BLANK7,
	ICON_BLANK8,
	ICON_BLANK9,
	ICON_BLANK10,
	ICON_BLANK11,
	ICON_BLANK12,
	
	ICON_DOTSUP,
	ICON_DOTSDOWN,
	ICON_MENU_PANEL,
	ICON_AXIS_SIDE,
	ICON_AXIS_FRONT,
	ICON_AXIS_TOP,
	ICON_BLANK14,
	ICON_BLANK15,
	ICON_BLANK16,
	ICON_BLANK17,
	ICON_BLANK18,
	ICON_ENVMAP,
	ICON_TRANSP_HLT,
	ICON_TRANSP_DEHLT,
	ICON_RADIO_DEHLT,
	ICON_RADIO_HLT,
	ICON_TPAINT_DEHLT,
	ICON_TPAINT_HLT,
	ICON_WPAINT_DEHLT,
	ICON_WPAINT_HLT,
	ICON_BLANK21,
	
	ICON_X,
	ICON_GO_LEFT,
	ICON_NO_GO_LEFT,
	ICON_UNLOCKED,
	ICON_LOCKED,
	ICON_PARLIB,
	ICON_DATALIB,
	ICON_AUTO,
	ICON_MATERIAL_DEHLT2,
	ICON_RING,
	ICON_GRID,
	ICON_PROPEDIT,
	ICON_KEEPRECT,
	ICON_DESEL_CUBE_VERTS,
	ICON_EDITMODE_DEHLT,
	ICON_EDITMODE_HLT,
	ICON_VPAINT_DEHLT,
	ICON_VPAINT_HLT,
	ICON_FACESEL_DEHLT,
	ICON_FACESEL_HLT,
	ICON_BLANK22,
	
	ICON_HELP,
	ICON_ERROR,
	ICON_FOLDER_DEHLT,
	ICON_FOLDER_HLT,
	ICON_BLUEIMAGE_DEHLT,
	ICON_BLUEIMAGE_HLT,
	ICON_BPIBFOLDER_DEHLT,
	ICON_BPIBFOLDER_HLT,
	ICON_BPIBFOLDER_ERR,
	ICON_UGLY_GREEN_RING,
	ICON_GHOST,
	ICON_SHARPCURVE,
	ICON_SMOOTHCURVE,
	ICON_BLANK23,
	ICON_BLANK24,
	ICON_BLANK25,
	ICON_BLANK26,
	ICON_BPIBFOLDER_X,
	ICON_BPIBFOLDERGREY,
	ICON_MAGNIFY,
	ICON_INFO2,
	
	ICON_RIGHTARROW,
	ICON_DOWNARROW_HLT,
	ICON_ROUNDBEVELTHING,
	ICON_FULLTEXTURE,
	ICON_REDPUBLISHERHALFTHINGY,
	ICON_PUBLISHER,
	ICON_CKEY,
	ICON_CHECKBOX_DEHLT,
	ICON_CHECKBOX_HLT,
	ICON_LINK,
	ICON_INLINK,
	ICON_BEVELBUT_HLT,
	ICON_BEVELBUT_DEHLT,
	ICON_PASTEDOWN,
	ICON_COPYDOWN,
	ICON_CONSTANT,
	ICON_LINEAR,
	ICON_CYCLIC,
	ICON_KEY_DEHLT,
	ICON_KEY_HLT,
	ICON_GRID2,
	
	ICON_EYE,
	ICON_LAMP,
	ICON_MATERIAL,
	ICON_TEXTURE,
	ICON_ANIM,
	ICON_WORLD,
	ICON_SCENE,
	ICON_EDIT,
	ICON_GAME,
	ICON_PAINT,
	ICON_RADIO,
	ICON_SCRIPT,
	ICON_SPEAKER,
	ICON_PASTEUP,
	ICON_COPYUP,
	ICON_PASTEFLIPUP,
	ICON_PASTEFLIPDOWN,
	ICON_CYCLICLINEAR,
	ICON_PIN_DEHLT,
	ICON_PIN_HLT,
	ICON_LITTLEGRID,
	
	ICON_FULLSCREEN,
	ICON_SPLITSCREEN,
	ICON_RIGHTARROW_THIN,
	ICON_DISCLOSURE_TRI_RIGHT,
	ICON_DISCLOSURE_TRI_DOWN,
	ICON_SCENE_SEPIA,
	ICON_SCENE_DEHLT,
	ICON_OBJECT,
	ICON_MESH,
	ICON_CURVE,
	ICON_MBALL,
	ICON_LATTICE,
	ICON_LAMP_DEHLT,
	ICON_MATERIAL_DEHLT,
	ICON_TEXTURE_DEHLT,
	ICON_IPO_DEHLT,
	ICON_LIBRARY_DEHLT,
	ICON_IMAGE_DEHLT,
	ICON_WINDOW_FULLSCREEN,
	ICON_WINDOW_WINDOW,
	ICON_PANEL_CLOSE,
	
	ICON_BLENDER,
	ICON_PACKAGE,
	ICON_UGLYPACKAGE,
	ICON_MATPLANE,
	ICON_MATSPHERE,
	ICON_MATCUBE,
	ICON_SCENE_HLT,
	ICON_OBJECT_HLT,
	ICON_MESH_HLT,
	ICON_CURVE_HLT,
	ICON_MBALL_HLT,
	ICON_LATTICE_HLT,
	ICON_LAMP_HLT,
	ICON_MATERIAL_HLT,
	ICON_TEXTURE_HLT,
	ICON_IPO_HLT,
	ICON_LIBRARY_HLT,
	ICON_IMAGE_HLT,
	ICON_CONSTRAINT,
	ICON_BLANK32,
	ICON_BLANK33,
#define BIFICONID_LAST		(ICON_BLANK33)
#define BIFNICONIDS			(BIFICONID_LAST-BIFICONID_FIRST + 1)
} BIFIconID;


/* ---------- theme ----------- */

enum {
	TH_AUTO,	/* for buttons, to signal automatic color assignment */
	
// uibutton colors
	TH_BUT_OUTLINE,
	TH_BUT_NEUTRAL,
	TH_BUT_ACTION,
	TH_BUT_SETTING,
	TH_BUT_SETTING1,
	TH_BUT_SETTING2,
	TH_BUT_NUM,
	TH_BUT_TEXTFIELD,
	TH_BUT_POPUP,
	TH_BUT_TEXT,
	TH_BUT_TEXT_HI,
	TH_MENU_BACK,
	TH_MENU_ITEM,
	TH_MENU_HILITE,
	TH_MENU_TEXT,
	TH_MENU_TEXT_HI,
	
	TH_BUT_DRAWTYPE,
	
	TH_REDALERT,
	TH_CUSTOM,
	
	TH_THEMEUI,
// common colors among spaces
	
	TH_BACK,
	TH_TEXT,
	TH_TEXT_HI,
	TH_HEADER,
	TH_HEADERDESEL,
	TH_PANEL,
	TH_SHADE1,
	TH_SHADE2,
	TH_HILITE,

	TH_GRID,
	TH_WIRE,
	TH_SELECT,
	TH_ACTIVE,
	TH_TRANSFORM,
	TH_VERTEX,
	TH_VERTEX_SELECT,
	TH_VERTEX_SIZE,
	TH_EDGE,
	TH_EDGE_SELECT,
	TH_FACE,
	TH_FACE_SELECT
};

/* specific defines per space should have higher define values */

struct bTheme;

// THE CODERS API FOR THEMES:

// sets the color
void 	BIF_ThemeColor(int colorid);

// sets the color plus alpha
void 	BIF_ThemeColor4(int colorid);

// sets color plus offset for shade
void 	BIF_ThemeColorShade(int colorid, int offset);

// sets color plus offset for alpha
void		BIF_ThemeColorShadeAlpha(int colorid, int coloffset, int alphaoffset);

// sets color, which is blend between two theme colors
void 	BIF_ThemeColorBlend(int colorid1, int colorid2, float fac);
// same, with shade offset
void    BIF_ThemeColorBlendShade(int colorid1, int colorid2, float fac, int offset);

// returns one value, not scaled
float 	BIF_GetThemeValuef(int colorid);
int 	BIF_GetThemeValue(int colorid);

// get three color values, scaled to 0.0-1.0 range
void 	BIF_GetThemeColor3fv(int colorid, float *col);

// get the 3 or 4 byte values
void 	BIF_GetThemeColor3ubv(int colorid, char *col);
void 	BIF_GetThemeColor4ubv(int colorid, char *col);

struct ScrArea;

// internal (blender) usage only, for init and set active
void 	BIF_InitTheme(void);
void 	BIF_SetTheme(struct ScrArea *sa);
void	BIF_resources_init		(void);
void	BIF_resources_free		(void);


// icon API
int		BIF_get_icon_width		(BIFIconID icon);
int		BIF_get_icon_height		(BIFIconID icon);
void	BIF_draw_icon			(BIFIconID icon);
void	BIF_draw_icon_blended	(BIFIconID icon, int colorid, int shade);

/* only for buttons in theme editor! */
char 	*BIF_ThemeGetColorPtr(struct bTheme *btheme, int spacetype, int colorid);
char 	*BIF_ThemeColorsPup(int spacetype);


#endif /*  BIF_ICONS_H */
