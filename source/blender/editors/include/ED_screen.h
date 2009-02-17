/**
 * $Id:
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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef ED_SCREEN_H
#define ED_SCREEN_H

#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_view2d_types.h"
#include "DNA_view3d_types.h"

struct wmWindowManager;
struct wmWindow;
struct wmNotifier;
struct wmEvent;
struct bContext;
struct SpaceType;
struct Scene;
struct bScreen;
struct ARegion;
struct uiBlock;
struct rcti;

/* regions */
void	ED_region_do_listen(struct ARegion *ar, struct wmNotifier *note);
void	ED_region_do_draw(struct bContext *C, struct ARegion *ar);
void	ED_region_exit(struct bContext *C, struct ARegion *ar);
void	ED_region_pixelspace(struct ARegion *ar);
void	ED_region_init(struct bContext *C, struct ARegion *ar);
void	ED_region_tag_redraw(struct ARegion *ar);
void	ED_region_tag_redraw_partial(struct ARegion *ar, struct rcti *rct);

/* spaces */
void	ED_spacetypes_init(void);
void	ED_spacetypes_keymap(struct wmWindowManager *wm);
int		ED_area_header_standardbuttons(const struct bContext *C, struct uiBlock *block, int yco);
void	ED_area_overdraw(struct bContext *C);
void	ED_area_overdraw_flush(struct bContext *C, struct ScrArea *sa, struct ARegion *ar);


/* areas */
void	ED_area_initialize(struct wmWindowManager *wm, struct wmWindow *win, struct ScrArea *sa);
void	ED_area_exit(struct bContext *C, struct ScrArea *sa);
int		ED_screen_area_active(const struct bContext *C);
void	ED_area_do_listen(ScrArea *sa, struct wmNotifier *note);
void	ED_area_tag_redraw(ScrArea *sa);
void	ED_area_tag_refresh(ScrArea *sa);
void	ED_area_do_refresh(struct bContext *C, ScrArea *sa);
void	ED_area_headerprint(ScrArea *sa, const char *str);
void	ED_area_newspace(struct bContext *C, ScrArea *sa, int type);
void	ED_area_prevspace(struct bContext *C);

/* screens */
void	ED_screens_initialize(struct wmWindowManager *wm);
void	ED_screen_draw(struct wmWindow *win);
void	ED_screen_refresh(struct wmWindowManager *wm, struct wmWindow *win);
void	ED_screen_do_listen(struct wmWindow *win, struct wmNotifier *note);
bScreen *ED_screen_duplicate(struct wmWindow *win, struct bScreen *sc);
void	ED_screen_set(struct bContext *C, struct bScreen *sc);
void	ED_screen_set_scene(struct bContext *C, struct Scene *scene);
void	ED_screen_set_subwinactive(struct wmWindow *win, struct wmEvent *event);
void	ED_screen_exit(struct bContext *C, struct wmWindow *window, struct bScreen *screen);
void	ED_screen_animation_timer(struct bContext *C, int enable);
int		ED_screen_full_newspace(struct bContext *C, ScrArea *sa, int type);
void	ED_screen_full_prevspace(struct bContext *C);

/* anim */
void	ED_update_for_newframe(const struct bContext *C, int mute);
unsigned int ED_screen_view3d_layers(struct bScreen *screen);

void	ED_operatortypes_screen(void);
void	ED_keymap_screen(struct wmWindowManager *wm);

/* operators; context poll callbacks */
int		ED_operator_screenactive(struct bContext *C);
int		ED_operator_screen_mainwinactive(struct bContext *C);
int		ED_operator_areaactive(struct bContext *C);

int		ED_operator_scene_editable(struct bContext *C);

int		ED_operator_view3d_active(struct bContext *C);
int		ED_operator_timeline_active(struct bContext *C);
int		ED_operator_outliner_active(struct bContext *C);
int		ED_operator_file_active(struct bContext *C);
int		ED_operator_action_active(struct bContext *C);
int		ED_operator_buttons_active(struct bContext *C);
int		ED_operator_node_active(struct bContext *C);
int		ED_operator_ipo_active(struct bContext *C);
int		ED_operator_sequencer_active(struct bContext *C);
int		ED_operator_image_active(struct bContext *C);

int		ED_operator_object_active(struct bContext *C);
int		ED_operator_editmesh(struct bContext *C);
int		ED_operator_editarmature(struct bContext *C);
int		ED_operator_editcurve(struct bContext *C);
int		ED_operator_editsurf(struct bContext *C);
int		ED_operator_editsurfcurve(struct bContext *C);
int		ED_operator_editfont(struct bContext *C);
int		ED_operator_uvedit(struct bContext *C);
int		ED_operator_uvmap(struct bContext *C);
int		ED_operator_posemode(struct bContext *C);


/* default keymaps, bitflags */
#define ED_KEYMAP_UI		1
#define ED_KEYMAP_VIEW2D	2
#define ED_KEYMAP_MARKERS	4
#define ED_KEYMAP_ANIMATION	8
#define ED_KEYMAP_FRAMES	16

#endif /* ED_SCREEN_H */

