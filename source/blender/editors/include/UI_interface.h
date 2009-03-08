/**
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
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

#ifndef UI_INTERFACE_H
#define UI_INTERFACE_H

/* Struct Declarations */

struct ID;
struct Main;
struct ListBase;
struct ARegion;
struct wmWindow;
struct wmWindowManager;
struct wmOperator;
struct AutoComplete;
struct bContext;
struct PointerRNA;
struct PropertyRNA;
struct ReportList;

typedef struct uiBut uiBut;
typedef struct uiBlock uiBlock;
typedef struct uiPopupBlockHandle uiPopupBlockHandle;

/* Defines */

/* uiBlock->dt */
#define UI_EMBOSS		0	/* use one of the themes for drawing */
#define UI_EMBOSSN		1	/* Nothing */
#define UI_EMBOSSM		2	/* Minimal builtin emboss, also for logic buttons */
#define UI_EMBOSSP		3	/* Pulldown */
#define UI_EMBOSSR		4	/* Rounded */
#define UI_EMBOSST		5	/* Table */

#define UI_EMBOSSX		0	/* for a python file, which i can't change.... duh! */

/* uiBlock->direction */
#define UI_TOP		1
#define UI_DOWN		2
#define UI_LEFT		4
#define UI_RIGHT	8
#define UI_DIRECTION	15
#define UI_CENTER		16
#define UI_SHIFT_FLIPPED	32

/* uiBlock->autofill (not yet used) */
#define UI_BLOCK_COLLUMNS	1
#define UI_BLOCK_ROWS		2

/* uiBlock->flag (controls) */
#define UI_BLOCK_LOOP			1
#define UI_BLOCK_REDRAW			2
#define UI_BLOCK_RET_1			4		/* XXX 2.5 not implemented */
#define UI_BLOCK_NUMSELECT		8
#define UI_BLOCK_ENTER_OK		16
#define UI_BLOCK_NOSHADOW		32
#define UI_BLOCK_NO_HILITE		64		/* XXX 2.5 not implemented */
#define UI_BLOCK_MOVEMOUSE_QUIT	128
#define UI_BLOCK_KEEP_OPEN		256
#define UI_BLOCK_POPUP			512

/* uiPopupBlockHandle->menuretval */
#define UI_RETURN_CANCEL	1       /* cancel all menus cascading */
#define UI_RETURN_OK        2       /* choice made */
#define UI_RETURN_OUT       4       /* left the menu */

	/* block->flag bits 12-15 are identical to but->flag bits */

/* block->font, for now: bold = medium+1 */
#define UI_HELV			0
#define UI_HELVB		1

/* panel controls */
#define UI_PNL_TRANSP	1
#define UI_PNL_SOLID	2

#define UI_PNL_CLOSE	32
#define UI_PNL_STOW		64
#define UI_PNL_TO_MOUSE	128
#define UI_PNL_UNSTOW	256
#define UI_PNL_SCALE	512

/* warning the first 4 flags are internal */
/* but->flag */
#define UI_TEXT_LEFT	16
#define UI_ICON_LEFT	32
#define UI_ICON_RIGHT	64
	/* control for button type block */
#define UI_MAKE_TOP		128
#define UI_MAKE_DOWN	256
#define UI_MAKE_LEFT	512
#define UI_MAKE_RIGHT	1024
	/* dont draw hilite on mouse over */
#define UI_NO_HILITE	2048
	/* button align flag, for drawing groups together */
#define UI_BUT_ALIGN		(15<<12)
#define UI_BUT_ALIGN_TOP	(1<<12)
#define UI_BUT_ALIGN_LEFT	(1<<13)
#define UI_BUT_ALIGN_RIGHT	(1<<14)
#define UI_BUT_ALIGN_DOWN	(1<<15)
#define UI_BUT_DISABLED		(1<<16)

/* Button types, bits stored in 1 value... and a short even!
- bits 0-4:  bitnr (0-31)
- bits 5-7:  pointer type
- bit  8:    for 'bit'
- bit  9-15: button type (now 6 bits, 64 types)
*/

#define CHA	32
#define SHO	64
#define INT	96
#define FLO	128
#define FUN	192
#define BIT	256

#define BUTPOIN	(128+64+32)

#define BUT	(1<<9)
#define ROW	(2<<9)
#define TOG	(3<<9)
#define SLI	(4<<9)
#define	NUM	(5<<9)
#define TEX	(6<<9)
#define TOG3	(7<<9)
#define TOGR	(8<<9)
#define TOGN	(9<<9)
#define LABEL	(10<<9)
#define MENU	(11<<9)
#define ICONROW	(12<<9)
#define ICONTOG	(13<<9)
#define NUMSLI	(14<<9)
#define COL		(15<<9)
#define IDPOIN	(16<<9)
#define HSVSLI 	(17<<9)
#define SCROLL	(18<<9)
#define BLOCK	(19<<9)
#define BUTM	(20<<9)
#define SEPR	(21<<9)
#define LINK	(22<<9)
#define INLINK	(23<<9)
#define KEYEVT	(24<<9)
#define ICONTEXTROW (25<<9)
#define HSVCUBE (26<<9)
#define PULLDOWN (27<<9)
#define ROUNDBOX (28<<9)
#define CHARTAB (29<<9)
#define BUT_COLORBAND (30<<9)
#define BUT_NORMAL (31<<9)
#define BUT_CURVE (32<<9)
#define BUT_TOGDUAL (33<<9)
#define ICONTOGN (34<<9)
#define FTPREVIEW (35<<9)
#define NUMABS	(36<<9)
#define HMENU	(37<<9)
#define BUTTYPE	(63<<9)

/* Drawing
 *
 * Functions to draw various shapes, taking theme settings into account.
 * Used for code that draws its own UI style elements. */

void uiEmboss(float x1, float y1, float x2, float y2, int sel);
void uiRoundBox(float minx, float miny, float maxx, float maxy, float rad);
void uiSetRoundBox(int type);
int uiGetRoundBox(void);
void uiRoundRect(float minx, float miny, float maxx, float maxy, float rad);
void uiDrawMenuBox(float minx, float miny, float maxx, float maxy, short flag, short direction);
void uiDrawBoxShadow(unsigned char alpha, float minx, float miny, float maxx, float maxy);

/* Menus
 *
 * These functions are used by popup menus, toolbox and header menus. They
 * assume uiMenuItem head is already created, which is done by uiMenuButton
 * for header menus, or can be done with uiPupMenuBegin for popups. These
 * functions do not use uiDefBut functions in order to simplify creating
 * them, and to permit other types of menus (radial, ..) in the future. */

typedef struct uiMenuItem uiMenuItem;

typedef void (*uiMenuCreateFunc)(struct bContext *C, uiMenuItem *head, void *arg1);
typedef void (*uiMenuHandleFunc)(struct bContext *C, void *arg, int event);

void uiMenuFunc(uiMenuItem *head, uiMenuHandleFunc handlefunc, void *argv);
void uiMenuContext(uiMenuItem *head, int opcontext);

void uiMenuItemVal(uiMenuItem *head, const char *name, int icon, int argval);

void uiMenuItemEnumO(uiMenuItem *head, const char *name, int icon, char *opname, char *propname, int value);
void uiMenuItemBooleanO(uiMenuItem *head, const char *name, int icon, char *opname, char *propname, int value);
void uiMenuItemsEnumO(uiMenuItem *head, char *opname, char *propname);
void uiMenuItemIntO(uiMenuItem *head, const char *name, int icon, char *opname, char *propname, int value);
void uiMenuItemFloatO(uiMenuItem *head, const char *name, int icon, char *opname, char *propname, float value);
void uiMenuItemStringO(uiMenuItem *head, const char *name, int icon, char *opname, char *propname, char *value);
void uiMenuItemO(uiMenuItem *head, int icon, char *opname);

void uiMenuItemBooleanR(uiMenuItem *head, struct PointerRNA *ptr, char *propname);
void uiMenuItemEnumR(uiMenuItem *head, struct PointerRNA *ptr, char *propname, int value);
void uiMenuItemsEnumR(uiMenuItem *head, struct PointerRNA *ptr, char *propname);

void uiMenuLevel(uiMenuItem *head, const char *name, uiMenuCreateFunc newlevel);
void uiMenuLevelEnumO(uiMenuItem *head, char *opname, char *propname);
void uiMenuLevelEnumR(uiMenuItem *head, struct PointerRNA *ptr, char *propname);

void uiMenuSeparator(uiMenuItem *head);

/* Popup Menus
 *
 * Functions used to create popup menus. For more extended menus the
 * uiPupMenuBegin/End functions can be used to define own items with
 * the uiMenu functions inbetween. If it is a simple confirmation menu
 * or similar, popups can be created with a single function call. */

uiMenuItem *uiPupMenuBegin(const char *title, int icon);
void uiPupMenuEnd(struct bContext *C, struct uiMenuItem *head);

void uiPupMenuOkee(struct bContext *C, char *opname, char *str, ...);
void uiPupMenuSaveOver(struct bContext *C, struct wmOperator *op, char *filename);
void uiPupMenuNotice(struct bContext *C, char *str, ...);
void uiPupMenuError(struct bContext *C, char *str, ...);
void uiPupMenuReports(struct bContext *C, struct ReportList *reports);

void uiPupMenuSetActive(int val);

/* Popup Blocks
 *
 * Functions used to create popup blocks. These are like popup menus
 * but allow using all button types and creating an own layout. */

typedef uiBlock* (*uiBlockCreateFunc)(struct bContext *C, struct ARegion *ar, void *arg1);

void uiPupBlock(struct bContext *C, uiBlockCreateFunc func, void *arg);
void uiPupBlockO(struct bContext *C, uiBlockCreateFunc func, void *arg, char *opname, int opcontext);

/* Blocks
 *
 * Functions for creating, drawing and freeing blocks. A Block is a
 * container of buttons and used for various purposes.
 * 
 * Begin/Define Buttons/End/Draw is the typical order in which these
 * function should be called, though for popup blocks Draw is left out.
 * Freeing blocks is done by the screen/ module automatically.
 *
 * */

uiBlock *uiBeginBlock(const struct bContext *C, struct ARegion *region, char *name, short dt, short font);
void uiEndBlock(const struct bContext *C, uiBlock *block);
void uiDrawBlock(const struct bContext *C, struct uiBlock *block);

uiBlock *uiGetBlock(char *name, struct ARegion *ar);

void uiFreeBlock(const struct bContext *C, uiBlock *block);
void uiFreeBlocks(const struct bContext *C, struct ListBase *lb);
void uiFreeInactiveBlocks(const struct bContext *C, struct ListBase *lb);

void uiBlockSetButLock(uiBlock *block, int val, char *lockstr);
void uiBlockClearButLock(uiBlock *block);

/* Appearance/Cruft
 *
 * These functions should mostly dissappear ideally, or become internal.
 * Font handling could move to blenfont/, and appearance could be dictated
 * better by high level information instead of spread out all over. */

void uiSetCurFont(uiBlock *block, int index);
void *uiSetCurFont_ext(float aspect);
void uiDefFont(unsigned int index, void *xl, void *large, void *medium, void *small);
void *uiBlockGetCurFont	(uiBlock *block);

/* automatic aligning, horiz or verical */
void uiBlockBeginAlign(uiBlock *block);
void uiBlockEndAlign(uiBlock *block);

void uiBoundsBlock(struct uiBlock *block, int addval);
void uiTextBoundsBlock(uiBlock *block, int addval);
void uiPopupBoundsBlock(uiBlock *block, int addval, int mx, int my);
void uiMenuPopupBoundsBlock(uiBlock *block, int addvall, int mx, int my);

int		uiBlocksGetYMin		(ListBase *lb);
int		uiBlockGetCol		(uiBlock *block);

void	uiBlockSetCol		(uiBlock *block, int col);
void	uiBlockSetEmboss	(uiBlock *block, int emboss);
void	uiBlockSetDirection	(uiBlock *block, int direction);
void 	uiBlockFlipOrder	(uiBlock *block);
void	uiBlockSetFlag		(uiBlock *block, int flag);
void	uiBlockSetXOfs		(uiBlock *block, int xofs);

int		uiButGetRetVal		(uiBut *but);

void	uiButSetFlag		(uiBut *but, int flag);
void	uiButClearFlag		(uiBut *but, int flag);

void	uiAutoBlock(uiBlock *block, float minx, float miny, float sizex, float sizey, int flag);

/* Buttons
 *
 * Functions to define various types of buttons in a block. Postfixes:
 * - F: float
 * - I: int
 * - S: short
 * - C: char
 * - R: RNA
 * - O: operator */

uiBut *uiDefBut(uiBlock *block, 
					   int type, int retval, char *str, 
					   short x1, short y1, 
					   short x2, short y2, 
					   void *poin, 
					   float min, float max, 
					   float a1, float a2,  char *tip);
uiBut *uiDefButF(uiBlock *block, int type, int retval, char *str, short x1, short y1, short x2, short y2, float *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefButBitF(uiBlock *block, int type, int bit, int retval, char *str, short x1, short y1, short x2, short y2, float *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefButI(uiBlock *block, int type, int retval, char *str, short x1, short y1, short x2, short y2, int *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefButBitI(uiBlock *block, int type, int bit, int retval, char *str, short x1, short y1, short x2, short y2, int *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefButS(uiBlock *block, int type, int retval, char *str, short x1, short y1, short x2, short y2, short *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefButBitS(uiBlock *block, int type, int bit, int retval, char *str, short x1, short y1, short x2, short y2, short *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefButC(uiBlock *block, int type, int retval, char *str, short x1, short y1, short x2, short y2, char *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefButBitC(uiBlock *block, int type, int bit, int retval, char *str, short x1, short y1, short x2, short y2, char *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefButR(uiBlock *block, int type, int retval, char *str, short x1, short y1, short x2, short y2, struct PointerRNA *ptr, const char *propname, int index, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefButO(uiBlock *block, int type, char *opname, int opcontext, char *str, short x1, short y1, short x2, short y2, char *tip);

uiBut *uiDefIconBut(uiBlock *block, 
					   int type, int retval, int icon, 
					   short x1, short y1, 
					   short x2, short y2, 
					   void *poin, 
					   float min, float max, 
					   float a1, float a2,  char *tip);
uiBut *uiDefIconButF(uiBlock *block, int type, int retval, int icon, short x1, short y1, short x2, short y2, float *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconButBitF(uiBlock *block, int type, int bit, int retval, int icon, short x1, short y1, short x2, short y2, float *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconButI(uiBlock *block, int type, int retval, int icon, short x1, short y1, short x2, short y2, int *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconButBitI(uiBlock *block, int type, int bit, int retval, int icon, short x1, short y1, short x2, short y2, int *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconButS(uiBlock *block, int type, int retval, int icon, short x1, short y1, short x2, short y2, short *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconButBitS(uiBlock *block, int type, int bit, int retval, int icon, short x1, short y1, short x2, short y2, short *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconButC(uiBlock *block, int type, int retval, int icon, short x1, short y1, short x2, short y2, char *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconButBitC(uiBlock *block, int type, int bit, int retval, int icon, short x1, short y1, short x2, short y2, char *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconButR(uiBlock *block, int type, int retval, int icon, short x1, short y1, short x2, short y2, struct PointerRNA *ptr, const char *propname, int index, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconButO(uiBlock *block, int type, char *opname, int opcontext, int icon, short x1, short y1, short x2, short y2, char *tip);

uiBut *uiDefIconTextBut(uiBlock *block,
						int type, int retval, int icon, char *str, 
						short x1, short y1,
						short x2, short y2,
						void *poin,
						float min, float max,
						float a1, float a2,  char *tip);
uiBut *uiDefIconTextButF(uiBlock *block, int type, int retval, int icon, char *str, short x1, short y1, short x2, short y2, float *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconTextButBitF(uiBlock *block, int type, int bit, int retval, int icon, char *str, short x1, short y1, short x2, short y2, float *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconTextButI(uiBlock *block, int type, int retval, int icon, char *str, short x1, short y1, short x2, short y2, int *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconTextButBitI(uiBlock *block, int type, int bit, int retval, int icon, char *str, short x1, short y1, short x2, short y2, int *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconTextButS(uiBlock *block, int type, int retval, int icon, char *str, short x1, short y1, short x2, short y2, short *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconTextButBitS(uiBlock *block, int type, int bit, int retval, int icon, char *str, short x1, short y1, short x2, short y2, short *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconTextButC(uiBlock *block, int type, int retval, int icon, char *str, short x1, short y1, short x2, short y2, char *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconTextButBitC(uiBlock *block, int type, int bit, int retval, int icon, char *str, short x1, short y1, short x2, short y2, char *poin, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconTextButR(uiBlock *block, int type, int retval, int icon, char *str, short x1, short y1, short x2, short y2, struct PointerRNA *ptr, const char *propname, int index, float min, float max, float a1, float a2,  char *tip);
uiBut *uiDefIconTextButO(uiBlock *block, int type, char *opname, int opcontext, int icon, char *str, short x1, short y1, short x2, short y2, char *tip);

/* for passing inputs to ButO buttons */
struct PointerRNA *uiButGetOperatorPtrRNA(uiBut *but);

/* Special Buttons
 *
 * Butons with a more specific purpose:
 * - IDPoinBut: for creating buttons that work on a pointer to an ID block.
 * - MenuBut: buttons that popup a menu (in headers usually).
 * - PulldownBut: like MenuBut, but creating a uiBlock (for compatibility).
 * - BlockBut: buttons that popup a block with more buttons.
 * - KeyevtBut: buttons that can be used to turn key events into values.
 * - PickerButtons: buttons like the color picker (for code sharing).
 * - AutoButR: RNA property button with type automatically defined. */

#define UI_ID_RENAME		1
#define UI_ID_BROWSE		2
#define UI_ID_ADD_NEW		4
#define UI_ID_OPEN			8
#define UI_ID_ALONE			16
#define UI_ID_DELETE		32
#define UI_ID_LOCAL			64
#define UI_ID_AUTO_NAME		128
#define UI_ID_FAKE_USER		256
#define UI_ID_PIN			512
#define UI_ID_BROWSE_RENDER	1024
#define UI_ID_FULL			(UI_ID_RENAME|UI_ID_BROWSE|UI_ID_ADD_NEW|UI_ID_OPEN|UI_ID_ALONE|UI_ID_DELETE|UI_ID_LOCAL)

typedef void (*uiIDPoinFuncFP)(struct bContext *C, char *str, struct ID **idpp);
typedef void (*uiIDPoinFunc)(struct bContext *C, struct ID *id, int event);

uiBut *uiDefIDPoinBut(uiBlock *block, uiIDPoinFuncFP func, short blocktype, int retval, char *str,
						short x1, short y1, short x2, short y2, void *idpp, char *tip);
int uiDefIDPoinButs(uiBlock *block, struct Main *main, struct ID *parid, struct ID *id, int id_code, short *pin_p, int x, int y, uiIDPoinFunc func, int events);

uiBut *uiDefPulldownBut(uiBlock *block, uiBlockCreateFunc func, void *arg, char *str, short x1, short y1, short x2, short y2, char *tip);
uiBut *uiDefMenuBut(uiBlock *block, uiMenuCreateFunc func, void *arg, char *str, short x1, short y1, short x2, short y2, char *tip);
uiBut *uiDefIconTextMenuBut(uiBlock *block, uiMenuCreateFunc func, void *arg, int icon, char *str, short x1, short y1, short x2, short y2, char *tip);

uiBut *uiDefBlockBut(uiBlock *block, uiBlockCreateFunc func, void *func_arg1, char *str, short x1, short y1, short x2, short y2, char *tip);
uiBut *uiDefIconBlockBut(uiBlock *block, uiBlockCreateFunc func, void *arg, int retval, int icon, short x1, short y1, short x2, short y2, char *tip);
uiBut *uiDefIconTextBlockBut(uiBlock *block, uiBlockCreateFunc func, void *arg, int icon, char *str, short x1, short y1, short x2, short y2, char *tip);

void uiDefKeyevtButS(uiBlock *block, int retval, char *str, short x1, short y1, short x2, short y2, short *spoin, char *tip);

void uiBlockPickerButtons(struct uiBlock *block, float *col, float *hsv, float *old, char *hexcol, char mode, short retval);

uiBut *uiDefAutoButR(uiBlock *block, struct PointerRNA *ptr, struct PropertyRNA *prop, int index, char *name, int x1, int y1, int x2, int y2);
int uiDefAutoButsRNA(uiBlock *block, struct PointerRNA *ptr);

/* Links
 *
 * Game engine logic brick links. Non-functional currently in 2.5,
 * code to handle and draw these is disabled internally. */

void uiSetButLink(struct uiBut *but,  void **poin,  void ***ppoin,  short *tot,  int from, int to);

void uiComposeLinks(uiBlock *block);
uiBut *uiFindInlink(uiBlock *block, void *poin);

/* Callbacks
 *
 * uiBlockSetHandleFunc/ButmFunc are for handling events through a callback.
 * HandleFunc gets the retval passed on, and ButmFunc gets a2. The latter is
 * mostly for compatibility with older code.
 *
 * uiButSetCompleteFunc is for tab completion.
 *
 * uiBlockSetFunc and uiButSetFunc are callbacks run when a button is used,
 * in case events, operators or RNA are not sufficient to handle the button.
 *
 * uiButSetNFunc will free the argument with MEM_freeN. */

typedef void (*uiButHandleFunc)(struct bContext *C, void *arg1, void *arg2);
typedef void (*uiButHandleNFunc)(struct bContext *C, void *argN, void *arg2);
typedef void (*uiButCompleteFunc)(struct bContext *C, char *str, void *arg);
typedef void (*uiBlockHandleFunc)(struct bContext *C, void *arg, int event);

void	uiBlockSetHandleFunc(uiBlock *block,	uiBlockHandleFunc func, void *arg);
void	uiBlockSetButmFunc	(uiBlock *block,	uiMenuHandleFunc func, void *arg);

void	uiBlockSetFunc		(uiBlock *block,	uiButHandleFunc func, void *arg1, void *arg2);
void	uiButSetFunc		(uiBut *but,		uiButHandleFunc func, void *arg1, void *arg2);
void	uiButSetNFunc		(uiBut *but,		uiButHandleNFunc func, void *argN, void *arg2);

void	uiButSetCompleteFunc(uiBut *but,		uiButCompleteFunc func, void *arg);

void 	uiBlockSetDrawExtraFunc(uiBlock *block, void (*func)(struct bContext *C, uiBlock *block));

/* Autocomplete
 *
 * Tab complete helper functions, for use in uiButCompleteFunc callbacks.
 * Call begin once, then multiple times do_name with all possibilities,
 * and finally end to finish and get the completed name. */

typedef struct AutoComplete AutoComplete;

AutoComplete *autocomplete_begin(char *startname, int maxlen);
void autocomplete_do_name(AutoComplete *autocpl, const char *name);
void autocomplete_end(AutoComplete *autocpl, char *autoname);

/* Panels
 *
 * Functions for creating, freeing and drawing panels. The API here
 * could use a good cleanup, though how they will function in 2.5 is
 * not clear yet so we postpone that. */

extern void uiNewPanelTabbed(char *, char *);
extern int uiNewPanel(const struct bContext *C, struct ARegion *ar, uiBlock *block, char *panelname, char *tabname, int ofsx, int ofsy, int sizex, int sizey);
extern void uiFreePanels(struct ListBase *lb);
extern void uiDrawPanels(const struct bContext *C, int re_align);
	
extern void uiSetPanelsView2d(struct ARegion *ar);
extern void uiMatchPanelsView2d(struct ARegion *ar);

extern void uiNewPanelHeight(struct uiBlock *block, int sizey);
extern void uiNewPanelTitle(struct uiBlock *block, char *str);
extern uiBlock *uiFindOpenPanelBlockName(ListBase *lb, char *name);
extern int uiAlignPanelStep(struct ScrArea *sa, struct ARegion *ar, float fac);
extern void uiPanelControl(int);
extern void uiSetPanelHandler(int);

/* Handlers
 *
 * Handlers that can be registered in regions, areas and windows for
 * handling WM events. Mostly this is done automatic by modules such
 * as screen/ if ED_KEYMAP_UI is set, or internally in popup functions. */

void UI_add_region_handlers(struct ListBase *handlers);
void UI_add_area_handlers(struct ListBase *handlers);
void UI_add_popup_handlers(struct ListBase *handlers, uiPopupBlockHandle *menu);

/* Legacy code
 * Callbacks and utils to get 2.48 work */

void test_idbutton_cb(struct bContext *C, void *namev, void *arg2);
void test_scriptpoin_but(struct bContext *C, char *name, ID **idpp);
void test_actionpoin_but(struct bContext *C, char *name, ID **idpp);
void test_obpoin_but(struct bContext *C, char *name, ID **idpp);
void test_meshobpoin_but(struct bContext *C, char *name, ID **idpp);
void test_meshpoin_but(struct bContext *C, char *name, ID **idpp);
void test_matpoin_but(struct bContext *C, char *name, ID **idpp);
void test_scenepoin_but(struct bContext *C, char *name, ID **idpp);
void test_grouppoin_but(struct bContext *C, char *name, ID **idpp);
void test_texpoin_but(struct bContext *C, char *name, ID **idpp);
void test_imapoin_but(struct bContext *C, char *name, ID **idpp);
void autocomplete_bone(struct bContext *C, char *str, void *arg_v);
void autocomplete_vgroup(struct bContext *C, char *str, void *arg_v);

struct CurveMapping;
struct rctf;
void curvemap_buttons(uiBlock *block, struct CurveMapping *cumap, char labeltype, short event, short redraw, struct rctf *rect);


/* Module
 *
 * init and exit should be called before using this module. init_userdef must
 * be used to reinitialize some internal state if user preferences change. */

void UI_init(void);
void UI_init_userdef(void);
void UI_exit(void);

/* XXX hide this */

uiBut *uiDefMenuButO(uiBlock *block, char *opname, char *name);
uiBut *uiDefMenuSep(uiBlock *block);
uiBut *uiDefMenuSub(uiBlock *block, uiBlockCreateFunc func, char *name);
uiBut *uiDefMenuTogR(uiBlock *block, struct PointerRNA *ptr, char *propname, char *propvalue, char *name);

#endif /*  UI_INTERFACE_H */

