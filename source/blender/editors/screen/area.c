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

#include <string.h>
#include <stdio.h>

#include "MEM_guardedalloc.h"

#include "DNA_screen_types.h"
#include "DNA_userdef_types.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_rand.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_screen.h"
#include "BKE_utildefines.h"

#include "WM_api.h"
#include "WM_types.h"
#include "wm_subwindow.h"

#include "ED_screen.h"
#include "ED_screen_types.h"
#include "ED_types.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"
#include "BLF_api.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#ifndef DISABLE_PYTHON
#include "BPY_extern.h"
#endif

#include "screen_intern.h"

/* general area and region code */

static void region_draw_emboss(ARegion *ar, rcti *scirct)
{
	rcti rect;
	
	/* translate scissor rect to region space */
	rect.xmin= scirct->xmin - ar->winrct.xmin;
	rect.ymin= scirct->ymin - ar->winrct.ymin;
	rect.xmax= scirct->xmax - ar->winrct.xmin;
	rect.ymax= scirct->ymax - ar->winrct.ymin;
	
	/* set transp line */
	glEnable( GL_BLEND );
	glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );
	
	/* right  */
	glColor4ub(0,0,0, 50);
	sdrawline(rect.xmax, rect.ymin, rect.xmax, rect.ymax);
	
	/* bottom  */
	glColor4ub(0,0,0, 80);
	sdrawline(rect.xmin, rect.ymin, rect.xmax, rect.ymin);
	
	/* top  */
	glColor4ub(255,255,255, 60);
	sdrawline(rect.xmin, rect.ymax, rect.xmax, rect.ymax);

	/* left  */
	glColor4ub(255,255,255, 50);
	sdrawline(rect.xmin, rect.ymin, rect.xmin, rect.ymax);
	
	glDisable( GL_BLEND );
}

void ED_region_pixelspace(ARegion *ar)
{
	int width= ar->winrct.xmax-ar->winrct.xmin+1;
	int height= ar->winrct.ymax-ar->winrct.ymin+1;
	
	wmOrtho2(-0.375, (float)width-0.375, -0.375, (float)height-0.375);
	wmLoadIdentity();
}

/* only exported for WM */
void ED_region_do_listen(ARegion *ar, wmNotifier *note)
{
	/* generic notes first */
	switch(note->category) {
		case NC_WM:
			if(note->data==ND_FILEREAD)
				ED_region_tag_redraw(ar);
			break;
		case NC_WINDOW:
			ED_region_tag_redraw(ar);
			break;
		case NC_SCREEN:
			if(note->action==NA_EDITED)
				ED_region_tag_redraw(ar);
			/* pass on */
		default:
			if(ar->type && ar->type->listener)
				ar->type->listener(ar, note);
	}
}

/* only exported for WM */
void ED_area_do_listen(ScrArea *sa, wmNotifier *note)
{
	/* no generic notes? */
	if(sa->type && sa->type->listener) {
		sa->type->listener(sa, note);
	}
}

/* only exported for WM */
void ED_area_do_refresh(bContext *C, ScrArea *sa)
{
	/* no generic notes? */
	if(sa->type && sa->type->refresh) {
		sa->type->refresh(C, sa);
	}
	sa->do_refresh= 0;
}

/* based on screen region draw tags, set draw tags in azones, and future region tabs etc */
/* only exported for WM */
void ED_area_overdraw_flush(bContext *C, ScrArea *sa, ARegion *ar)
{
	AZone *az;
	
	for(az= sa->actionzones.first; az; az= az->next) {
		int xs, ys;
		
		if(az->type==AZONE_AREA) {
			xs= (az->x1+az->x2)/2;
			ys= (az->y1+az->y2)/2;
		}
		else {
			xs= az->x3;
			ys= az->y3;
		}

		/* test if inside */
		if(BLI_in_rcti(&ar->winrct, xs, ys)) {
			az->do_draw= 1;
		}
	}
}

static void area_draw_azone(short x1, short y1, short x2, short y2)
{
	float xmin = x1;
	float xmax = x2-2;
	float ymin = y1-1;
	float ymax = y2-3;
	
	float dx= 0.3f*(xmax-xmin);
	float dy= 0.3f*(ymax-ymin);
	
	glColor4ub(255, 255, 255, 80);
	fdrawline(xmin, ymax, xmax, ymin);
	fdrawline(xmin, ymax-dy, xmax-dx, ymin);
	fdrawline(xmin, ymax-2*dy, xmax-2*dx, ymin);
	
	glColor4ub(0, 0, 0, 150);
	fdrawline(xmin, ymax+1, xmax+1, ymin);
	fdrawline(xmin, ymax-dy+1, xmax-dx+1, ymin);
	fdrawline(xmin, ymax-2*dy+1, xmax-2*dx+1, ymin);
}

static void region_draw_azone(ScrArea *sa, AZone *az)
{
	if(az->ar==NULL) return;
	
	UI_SetTheme(sa->spacetype, az->ar->type->regionid);
	
	UI_ThemeColor(TH_BACK);
	glBegin(GL_TRIANGLES);
	glVertex2s(az->x1, az->y1);
	glVertex2s(az->x2, az->y2);
	glVertex2s(az->x3, az->y3);
	glEnd();
	
	UI_ThemeColorShade(TH_BACK, 50);
	sdrawline(az->x1, az->y1, az->x3, az->y3);
	
	UI_ThemeColorShade(TH_BACK, -50);
	sdrawline(az->x2, az->y2, az->x3, az->y3);

}


/* only exported for WM */
void ED_area_overdraw(bContext *C)
{
	wmWindow *win= CTX_wm_window(C);
	bScreen *screen= CTX_wm_screen(C);
	ScrArea *sa;
	
	/* Draw AZones, in screenspace */
	wmSubWindowSet(win, screen->mainwin);

	glEnable( GL_BLEND );
	glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );
	
	for(sa= screen->areabase.first; sa; sa= sa->next) {
		AZone *az;
		for(az= sa->actionzones.first; az; az= az->next) {
			if(az->do_draw) {
				if(az->type==AZONE_AREA)
					area_draw_azone(az->x1, az->y1, az->x2, az->y2);
				else if(az->type==AZONE_REGION)
					region_draw_azone(sa, az);
				
				az->do_draw= 0;
			}
		}
	}	
	glDisable( GL_BLEND );
	
}

/* get scissor rect, checking overlapping regions */
static void region_scissor_winrct(ARegion *ar, rcti *winrct)
{
	*winrct= ar->winrct;
	
	if(ELEM(ar->alignment, RGN_OVERLAP_LEFT, RGN_OVERLAP_RIGHT))
		return;

	while(ar->prev) {
		ar= ar->prev;
		
		if(ar->flag & RGN_FLAG_HIDDEN);
		else if(ar->alignment==RGN_OVERLAP_LEFT) {
			winrct->xmin= ar->winrct.xmax + 1;
		}
		else if(ar->alignment==RGN_OVERLAP_RIGHT) {
			winrct->xmax= ar->winrct.xmin - 1;
		}
		else break;
	}
}

/* only exported for WM */
void ED_region_do_draw(bContext *C, ARegion *ar)
{
	wmWindow *win= CTX_wm_window(C);
	ScrArea *sa= CTX_wm_area(C);
	ARegionType *at= ar->type;
	rcti winrct;
	
	/* checks other overlapping regions */
	region_scissor_winrct(ar, &winrct);
	
	/* if no partial draw rect set, full rect */
	if(ar->drawrct.xmin == ar->drawrct.xmax)
		ar->drawrct= winrct;
	else {
		/* extra clip for safety */
		ar->drawrct.xmin= MAX2(winrct.xmin, ar->drawrct.xmin);
		ar->drawrct.ymin= MAX2(winrct.ymin, ar->drawrct.ymin);
		ar->drawrct.xmax= MIN2(winrct.xmax, ar->drawrct.xmax);
		ar->drawrct.ymax= MIN2(winrct.ymax, ar->drawrct.ymax);
	}
	
	/* note; this sets state, so we can use wmOrtho and friends */
	wmSubWindowScissorSet(win, ar->swinid, &ar->drawrct);
	
	UI_SetTheme(sa?sa->spacetype:0, ar->type?ar->type->regionid:0);
	
	/* optional header info instead? */
	if(ar->headerstr) {
		float col[3];
		UI_GetThemeColor3fv(TH_HEADER, col);
		glClearColor(col[0], col[1], col[2], 0.0);
		glClear(GL_COLOR_BUFFER_BIT);
		
		UI_ThemeColor(TH_TEXT);
		BLF_draw_default(20, 6, 0.0f, ar->headerstr);
	}
	else if(at->draw) {
		at->draw(C, ar);
	}
	
	uiFreeInactiveBlocks(C, &ar->uiblocks);
	
	if(sa)
		region_draw_emboss(ar, &winrct);
	
	/* XXX test: add convention to end regions always in pixel space, for drawing of borders/gestures etc */
	ED_region_pixelspace(ar);
	
	ar->do_draw= 0;
	memset(&ar->drawrct, 0, sizeof(ar->drawrct));
}

/* **********************************
   maybe silly, but let's try for now
   to keep these tags protected
   ********************************** */

void ED_region_tag_redraw(ARegion *ar)
{
	if(ar) {
		/* zero region means full region redraw */
		ar->do_draw= 1;
		memset(&ar->drawrct, 0, sizeof(ar->drawrct));
	}
}

void ED_region_tag_redraw_partial(ARegion *ar, rcti *rct)
{
	if(ar) {
		if(!ar->do_draw) {
			/* no redraw set yet, set partial region */
			ar->do_draw= 1;
			ar->drawrct= *rct;
		}
		else if(ar->drawrct.xmin != ar->drawrct.xmax) {
			/* partial redraw already set, expand region */
			ar->drawrct.xmin= MIN2(ar->drawrct.xmin, rct->xmin);
			ar->drawrct.ymin= MIN2(ar->drawrct.ymin, rct->ymin);
			ar->drawrct.xmax= MAX2(ar->drawrct.xmax, rct->xmax);
			ar->drawrct.ymax= MAX2(ar->drawrct.ymax, rct->ymax);
		}
	}
}

void ED_area_tag_redraw(ScrArea *sa)
{
	ARegion *ar;
	
	if(sa)
		for(ar= sa->regionbase.first; ar; ar= ar->next)
			ED_region_tag_redraw(ar);
}

void ED_area_tag_refresh(ScrArea *sa)
{
	if(sa)
		sa->do_refresh= 1;
}

/* *************************************************************** */

/* use NULL to disable it */
void ED_area_headerprint(ScrArea *sa, const char *str)
{
	ARegion *ar;
	
	for(ar= sa->regionbase.first; ar; ar= ar->next) {
		if(ar->regiontype==RGN_TYPE_HEADER) {
			if(str) {
				if(ar->headerstr==NULL)
					ar->headerstr= MEM_mallocN(256, "headerprint");
				BLI_strncpy(ar->headerstr, str, 256);
			}
			else if(ar->headerstr) {
				MEM_freeN(ar->headerstr);
				ar->headerstr= NULL;
			}
			ED_region_tag_redraw(ar);
		}
	}
}

/* ************************************************************ */


#define AZONESPOT		12
static void area_azone_initialize(ScrArea *sa) 
{
	AZone *az;
	
	/* reinitalize entirely, regions add azones too */
	BLI_freelistN(&sa->actionzones);
	
	/* set area action zones */
	az= (AZone *)MEM_callocN(sizeof(AZone), "actionzone");
	BLI_addtail(&(sa->actionzones), az);
	az->type= AZONE_AREA;
	az->x1= sa->totrct.xmin;
	az->y1= sa->totrct.ymin;
	az->x2= sa->totrct.xmin + AZONESPOT-1;
	az->y2= sa->totrct.ymin + AZONESPOT-1;
	BLI_init_rcti(&az->rect, az->x1, az->x2, az->y1, az->y2);
	
	az= (AZone *)MEM_callocN(sizeof(AZone), "actionzone");
	BLI_addtail(&(sa->actionzones), az);
	az->type= AZONE_AREA;
	az->x1= sa->totrct.xmax+1;
	az->y1= sa->totrct.ymax+1;
	az->x2= sa->totrct.xmax-AZONESPOT+1;
	az->y2= sa->totrct.ymax-AZONESPOT+1;
	BLI_init_rcti(&az->rect, az->x1, az->x2, az->y1, az->y2);
}

static void region_azone_initialize(ScrArea *sa, ARegion *ar, char edge) 
{
	AZone *az, *azt;
	
	az= (AZone *)MEM_callocN(sizeof(AZone), "actionzone");
	BLI_addtail(&(sa->actionzones), az);
	az->type= AZONE_REGION;
	az->ar= ar;
	az->edge= edge;
	
	if(edge=='t') {
		az->x1= ar->winrct.xmin+AZONESPOT;
		az->y1= ar->winrct.ymax;
		az->x2= ar->winrct.xmin+2*AZONESPOT;
		az->y2= ar->winrct.ymax;
		az->x3= (az->x1+az->x2)/2;
		az->y3= az->y2+AZONESPOT/2;
		BLI_init_rcti(&az->rect, az->x1, az->x2, az->y1, az->y3);
	}
	else if(edge=='b') {
		az->x1= ar->winrct.xmin+AZONESPOT;
		az->y1= ar->winrct.ymin;
		az->x2= ar->winrct.xmin+2*AZONESPOT;
		az->y2= ar->winrct.ymin;
		az->x3= (az->x1+az->x2)/2;
		az->y3= az->y2-AZONESPOT/2;
		BLI_init_rcti(&az->rect, az->x1, az->x2, az->y3, az->y1);
	}
	else if(edge=='l') {
		az->x1= ar->winrct.xmin;
		az->y1= ar->winrct.ymax-AZONESPOT;
		az->x2= ar->winrct.xmin;
		az->y2= ar->winrct.ymax-2*AZONESPOT;
		az->x3= az->x2-AZONESPOT/2;
		az->y3= (az->y1+az->y2)/2;
		BLI_init_rcti(&az->rect, az->x3, az->x1, az->y1, az->y2);
	}
	else { // if(edge=='r') {
		az->x1= ar->winrct.xmax;
		az->y1= ar->winrct.ymax-AZONESPOT;
		az->x2= ar->winrct.xmax;
		az->y2= ar->winrct.ymax-2*AZONESPOT;
		az->x3= az->x2+AZONESPOT/2;
		az->y3= (az->y1+az->y2)/2;
		BLI_init_rcti(&az->rect, az->x1, az->x3, az->y1, az->y2);
	}
	
	/* if more azones on 1 spot, set offset */
	for(azt= sa->actionzones.first; azt; azt= azt->next) {
		if(az!=azt) {
			if(az->x1==azt->x1 && az->y1==azt->y1) {
				if(edge=='t' || edge=='b') {
					az->x1+= AZONESPOT;
					az->x2+= AZONESPOT;
					az->x3+= AZONESPOT;
					BLI_init_rcti(&az->rect, az->x1, az->x2, az->y1, az->y3);
				}
				else {
					az->y1-= AZONESPOT;
					az->y2-= AZONESPOT;
					az->y3-= AZONESPOT;
					BLI_init_rcti(&az->rect, az->x1, az->x3, az->y1, az->y2);
				}
			}
		}
	}
	
}


/* *************************************************************** */

static void region_azone_add(ScrArea *sa, ARegion *ar, int alignment)
{
	 /* edge code (t b l r) is where azone will be drawn */
	
	if(alignment==RGN_ALIGN_TOP)
		region_azone_initialize(sa, ar, 'b');
	else if(alignment==RGN_ALIGN_BOTTOM)
		region_azone_initialize(sa, ar, 't');
	else if(ELEM(alignment, RGN_ALIGN_RIGHT, RGN_OVERLAP_RIGHT))
		region_azone_initialize(sa, ar, 'l');
	else if(ELEM(alignment, RGN_ALIGN_LEFT, RGN_OVERLAP_LEFT))
		region_azone_initialize(sa, ar, 'r');
								
}

/* dir is direction to check, not the splitting edge direction! */
static int rct_fits(rcti *rect, char dir, int size)
{
	if(dir=='h') {
		return rect->xmax-rect->xmin - size;
	}
	else { // 'v'
		return rect->ymax-rect->ymin - size;
	}
}

static void region_rect_recursive(ScrArea *sa, ARegion *ar, rcti *remainder, int quad)
{
	rcti *remainder_prev= remainder;
	int prefsizex, prefsizey;
	int alignment;
	
	if(ar==NULL)
		return;
	
	/* no returns in function, winrct gets set in the end again */
	BLI_init_rcti(&ar->winrct, 0, 0, 0, 0);
	
	/* for test; allow split of previously defined region */
	if(ar->alignment & RGN_SPLIT_PREV)
		if(ar->prev)
			remainder= &ar->prev->winrct;
	
	alignment = ar->alignment & ~RGN_SPLIT_PREV;
	
	/* clear state flags first */
	ar->flag &= ~RGN_FLAG_TOO_SMALL;
	/* user errors */
	if(ar->next==NULL && alignment!=RGN_ALIGN_QSPLIT)
		alignment= RGN_ALIGN_NONE;
	
	prefsizex= ar->type->minsizex;
	prefsizey= ar->type->minsizey;
	
	/* hidden is user flag */
	if(ar->flag & RGN_FLAG_HIDDEN);
	/* XXX floating area region, not handled yet here */
	else if(alignment == RGN_ALIGN_FLOAT);
	/* remainder is too small for any usage */
	else if( rct_fits(remainder, 'v', 1)<0 || rct_fits(remainder, 'h', 1) < 0 ) {
		ar->flag |= RGN_FLAG_TOO_SMALL;
	}
	else if(alignment==RGN_ALIGN_NONE) {
		/* typically last region */
		ar->winrct= *remainder;
		BLI_init_rcti(remainder, 0, 0, 0, 0);
	}
	else if(alignment==RGN_ALIGN_TOP || alignment==RGN_ALIGN_BOTTOM) {
		
		if( rct_fits(remainder, 'v', prefsizey) < 0 ) {
			ar->flag |= RGN_FLAG_TOO_SMALL;
		}
		else {
			int fac= rct_fits(remainder, 'v', prefsizey);

			if(fac < 0 )
				prefsizey += fac;
			
			ar->winrct= *remainder;
			
			if(alignment==RGN_ALIGN_TOP) {
				ar->winrct.ymin= ar->winrct.ymax - prefsizey + 1;
				remainder->ymax= ar->winrct.ymin - 1;
			}
			else {
				ar->winrct.ymax= ar->winrct.ymin + prefsizey - 1;
				remainder->ymin= ar->winrct.ymax + 1;
			}
		}
	}
	else if( ELEM4(alignment, RGN_ALIGN_LEFT, RGN_ALIGN_RIGHT, RGN_OVERLAP_LEFT, RGN_OVERLAP_RIGHT)) {
		
		if( rct_fits(remainder, 'h', prefsizex) < 0 ) {
			ar->flag |= RGN_FLAG_TOO_SMALL;
		}
		else {
			int fac= rct_fits(remainder, 'h', prefsizex);
			
			if(fac < 0 )
				prefsizex += fac;
			
			ar->winrct= *remainder;
			
			if(ELEM(alignment, RGN_ALIGN_RIGHT, RGN_OVERLAP_RIGHT)) {
				ar->winrct.xmin= ar->winrct.xmax - prefsizex + 1;
				if(alignment==RGN_ALIGN_RIGHT)
					remainder->xmax= ar->winrct.xmin - 1;
			}
			else {
				ar->winrct.xmax= ar->winrct.xmin + prefsizex - 1;
				if(alignment==RGN_ALIGN_LEFT)
					remainder->xmin= ar->winrct.xmax + 1;
			}
		}
	}
	else if(alignment==RGN_ALIGN_VSPLIT || alignment==RGN_ALIGN_HSPLIT) {
		/* percentage subdiv*/
		ar->winrct= *remainder;
		
		if(alignment==RGN_ALIGN_HSPLIT) {
			if( rct_fits(remainder, 'h', prefsizex) > 4) {
				ar->winrct.xmax= (remainder->xmin+remainder->xmax)/2;
				remainder->xmin= ar->winrct.xmax+1;
			}
			else {
				BLI_init_rcti(remainder, 0, 0, 0, 0);
			}
		}
		else {
			if( rct_fits(remainder, 'v', prefsizey) > 4) {
				ar->winrct.ymax= (remainder->ymin+remainder->ymax)/2;
				remainder->ymin= ar->winrct.ymax+1;
			}
			else {
				BLI_init_rcti(remainder, 0, 0, 0, 0);
			}
		}
	}
	else if(alignment==RGN_ALIGN_QSPLIT) {
		ar->winrct= *remainder;
		
		/* test if there's still 4 regions left */
		if(quad==0) {
			ARegion *artest= ar->next;
			int count= 1;
			
			while(artest) {
				artest->alignment= RGN_ALIGN_QSPLIT;
				artest= artest->next;
				count++;
			}
			
			if(count!=4) {
				/* let's stop adding regions */
				BLI_init_rcti(remainder, 0, 0, 0, 0);
				printf("region quadsplit failed\n");
			}
			else quad= 1;
		}
		if(quad) {
			if(quad==1) { /* left bottom */
				ar->winrct.xmax = (remainder->xmin + remainder->xmax)/2;
				ar->winrct.ymax = (remainder->ymin + remainder->ymax)/2;
			}
			else if(quad==2) { /* left top */
				ar->winrct.xmax = (remainder->xmin + remainder->xmax)/2;
				ar->winrct.ymin = 1 + (remainder->ymin + remainder->ymax)/2;
			}
			else if(quad==3) { /* right bottom */
				ar->winrct.xmin = 1 + (remainder->xmin + remainder->xmax)/2;
				ar->winrct.ymax = (remainder->ymin + remainder->ymax)/2;
			}
			else {	/* right top */
				ar->winrct.xmin = 1 + (remainder->xmin + remainder->xmax)/2;
				ar->winrct.ymin = 1 + (remainder->ymin + remainder->ymax)/2;
				BLI_init_rcti(remainder, 0, 0, 0, 0);
			}

			quad++;
		}
	}
	
	/* for speedup */
	ar->winx= ar->winrct.xmax - ar->winrct.xmin + 1;
	ar->winy= ar->winrct.ymax - ar->winrct.ymin + 1;
	
	/* restore test exception */
	if(ar->alignment & RGN_SPLIT_PREV) {
		if(ar->prev) {
			remainder= remainder_prev;
			ar->prev->winx= ar->prev->winrct.xmax - ar->prev->winrct.xmin + 1;
			ar->prev->winy= ar->prev->winrct.ymax - ar->prev->winrct.ymin + 1;
		}
	}

	/* set winrect for azones */
	if(ar->flag & (RGN_FLAG_HIDDEN|RGN_FLAG_TOO_SMALL)) {
		ar->winrct= *remainder;
		
		if(alignment==RGN_ALIGN_TOP)
			ar->winrct.ymin= ar->winrct.ymax;
		else if(alignment==RGN_ALIGN_BOTTOM)
			ar->winrct.ymax= ar->winrct.ymin;
		else if(ELEM(alignment, RGN_ALIGN_RIGHT, RGN_OVERLAP_RIGHT))
			ar->winrct.xmin= ar->winrct.xmax;
		else if(ELEM(alignment, RGN_ALIGN_LEFT, RGN_OVERLAP_LEFT))
			ar->winrct.xmax= ar->winrct.xmin;
		else /* prevent winrct to be valid */
			ar->winrct.xmax= ar->winrct.xmin;
	}
	/* in end, add azones, where appropriate */
	region_azone_add(sa, ar, alignment);


	region_rect_recursive(sa, ar->next, remainder, quad);
}

static void area_calc_totrct(ScrArea *sa, int sizex, int sizey)
{
	short rt= CLAMPIS(G.rt, 0, 16);

	if(sa->v1->vec.x>0) sa->totrct.xmin= sa->v1->vec.x+1+rt;
	else sa->totrct.xmin= sa->v1->vec.x;
	if(sa->v4->vec.x<sizex-1) sa->totrct.xmax= sa->v4->vec.x-1-rt;
	else sa->totrct.xmax= sa->v4->vec.x;
	
	if(sa->v1->vec.y>0) sa->totrct.ymin= sa->v1->vec.y+1+rt;
	else sa->totrct.ymin= sa->v1->vec.y;
	if(sa->v2->vec.y<sizey-1) sa->totrct.ymax= sa->v2->vec.y-1-rt;
	else sa->totrct.ymax= sa->v2->vec.y;
	
	/* for speedup */
	sa->winx= sa->totrct.xmax-sa->totrct.xmin+1;
	sa->winy= sa->totrct.ymax-sa->totrct.ymin+1;
}


/* used for area initialize below */
static void region_subwindow(wmWindowManager *wm, wmWindow *win, ARegion *ar)
{
	if(ar->flag & (RGN_FLAG_HIDDEN|RGN_FLAG_TOO_SMALL)) {
		if(ar->swinid)
			wm_subwindow_close(win, ar->swinid);
		ar->swinid= 0;
	}
	else if(ar->swinid==0)
		ar->swinid= wm_subwindow_open(win, &ar->winrct);
	else 
		wm_subwindow_position(win, ar->swinid, &ar->winrct);
}

static void ed_default_handlers(wmWindowManager *wm, ListBase *handlers, int flag)
{
	/* note, add-handler checks if it already exists */
	
	// XXX it would be good to have boundbox checks for some of these...
	if(flag & ED_KEYMAP_UI) {
		UI_add_region_handlers(handlers);
	}
	if(flag & ED_KEYMAP_VIEW2D) {
		ListBase *keymap= WM_keymap_listbase(wm, "View2D", 0, 0);
		WM_event_add_keymap_handler(handlers, keymap);
	}
	if(flag & ED_KEYMAP_MARKERS) {
		ListBase *keymap= WM_keymap_listbase(wm, "Markers", 0, 0);
		WM_event_add_keymap_handler(handlers, keymap);
		// XXX need boundbox check urgently!!!
	}
	if(flag & ED_KEYMAP_ANIMATION) {
		ListBase *keymap= WM_keymap_listbase(wm, "Animation", 0, 0);
		WM_event_add_keymap_handler(handlers, keymap);
	}
	if(flag & ED_KEYMAP_FRAMES) {
		ListBase *keymap= WM_keymap_listbase(wm, "Frames", 0, 0);
		WM_event_add_keymap_handler(handlers, keymap);
	}
}


/* called in screen_refresh, or screens_init, also area size changes */
void ED_area_initialize(wmWindowManager *wm, wmWindow *win, ScrArea *sa)
{
	ARegion *ar;
	rcti rect;
	
	/* set typedefinitions */
	sa->type= BKE_spacetype_from_id(sa->spacetype);
	
	if(sa->type==NULL) {
		sa->butspacetype= sa->spacetype= SPACE_VIEW3D;
		sa->type= BKE_spacetype_from_id(sa->spacetype);
	}
	
	for(ar= sa->regionbase.first; ar; ar= ar->next)
		ar->type= BKE_regiontype_from_id(sa->type, ar->regiontype);
	
	/* area sizes */
	area_calc_totrct(sa, win->sizex, win->sizey);
	
	/* clear all azones, add the area triange widgets */
	area_azone_initialize(sa);

	/* region rect sizes */
	rect= sa->totrct;
	region_rect_recursive(sa, sa->regionbase.first, &rect, 0);
	
	/* default area handlers */
	ed_default_handlers(wm, &sa->handlers, sa->type->keymapflag);
	/* checks spacedata, adds own handlers */
	if(sa->type->init)
		sa->type->init(wm, sa);
	
	/* region windows, default and own handlers */
	for(ar= sa->regionbase.first; ar; ar= ar->next) {
		region_subwindow(wm, win, ar);
		
		if(ar->swinid) {
			/* default region handlers */
			ed_default_handlers(wm, &ar->handlers, ar->type->keymapflag);

			if(ar->type->init)
				ar->type->init(wm, ar);
		}
		else {
			/* prevent uiblocks to run */
			uiFreeBlocks(NULL, &ar->uiblocks);	
		}
		
	}
}

/* externally called for floating regions like menus */
void ED_region_init(bContext *C, ARegion *ar)
{
//	ARegionType *at= ar->type;
	
	/* refresh can be called before window opened */
	region_subwindow(CTX_wm_manager(C), CTX_wm_window(C), ar);
	
	ar->winx= ar->winrct.xmax - ar->winrct.xmin + 1;
	ar->winy= ar->winrct.ymax - ar->winrct.ymin + 1;
	
	/* UI convention */
	wmLoadIdentity();
	wmOrtho2(-0.01f, ar->winx-0.01f, -0.01f, ar->winy-0.01f);
	
}


/* sa2 to sa1, we swap spaces for fullscreen to keep all allocated data */
/* area vertices were set */
void area_copy_data(ScrArea *sa1, ScrArea *sa2, int swap_space)
{
	SpaceType *st;
	ARegion *ar;
	
	sa1->headertype= sa2->headertype;
	sa1->spacetype= sa2->spacetype;
	sa1->butspacetype= sa2->butspacetype;
	
	if(swap_space == 1) {
		SWAP(ListBase, sa1->spacedata, sa2->spacedata);
		/* exception: ensure preview is reset */
//		if(sa1->spacetype==SPACE_VIEW3D)
// XXX			BIF_view3d_previewrender_free(sa1->spacedata.first);
	}
	else if (swap_space == 2) {
		BKE_spacedata_copylist(&sa1->spacedata, &sa2->spacedata);
	}
	else {
		BKE_spacedata_freelist(&sa1->spacedata);
		BKE_spacedata_copylist(&sa1->spacedata, &sa2->spacedata);
	}
	
	/* Note; SPACE_EMPTY is possible on new screens */
	
	/* regions */
	if(swap_space<2) {
		st= BKE_spacetype_from_id(sa1->spacetype);
		for(ar= sa1->regionbase.first; ar; ar= ar->next)
			BKE_area_region_free(st, ar);
		BLI_freelistN(&sa1->regionbase);
	}
	
	st= BKE_spacetype_from_id(sa2->spacetype);
	for(ar= sa2->regionbase.first; ar; ar= ar->next) {
		ARegion *newar= BKE_area_region_copy(st, ar);
		BLI_addtail(&sa1->regionbase, newar);
	}
		
#ifndef DISABLE_PYTHON
	/* scripts */
	BPY_free_scriptlink(&sa1->scriptlink);
	sa1->scriptlink= sa2->scriptlink;
	BPY_copy_scriptlink(&sa1->scriptlink);	/* copies internal pointers */
#endif
}

/* *********** Space switching code *********** */

void ED_area_swapspace(bContext *C, ScrArea *sa1, ScrArea *sa2)
{
	ScrArea *tmp= MEM_callocN(sizeof(ScrArea), "addscrarea");

	ED_area_exit(C, sa1);
	ED_area_exit(C, sa2);

	tmp->spacetype= sa1->spacetype;
	tmp->butspacetype= sa1->butspacetype;
	BKE_spacedata_copyfirst(&tmp->spacedata, &sa1->spacedata);

	area_copy_data(tmp, sa1, 2);
	area_copy_data(sa1, sa2, 0);
	area_copy_data(sa2, tmp, 0);
	ED_area_initialize(CTX_wm_manager(C), CTX_wm_window(C), sa1);
	ED_area_initialize(CTX_wm_manager(C), CTX_wm_window(C), sa2);

	BKE_screen_area_free(tmp);
	MEM_freeN(tmp);

	/* tell WM to refresh, cursor types etc */
	WM_event_add_mousemove(C);
	
	ED_area_tag_redraw(sa1);
	ED_area_tag_refresh(sa1);
	ED_area_tag_redraw(sa2);
	ED_area_tag_refresh(sa2);
}

void ED_area_newspace(bContext *C, ScrArea *sa, int type)
{
	if(sa->spacetype != type) {
		SpaceType *st;
		SpaceLink *slold;
		SpaceLink *sl;

		ED_area_exit(C, sa);

		st= BKE_spacetype_from_id(type);
		slold= sa->spacedata.first;

		sa->spacetype= type;
		sa->butspacetype= type;
		sa->type= st;
		
		/* check previously stored space */
		for (sl= sa->spacedata.first; sl; sl= sl->next)
			if(sl->spacetype==type)
				break;
		
		/* old spacedata... happened during work on 2.50, remove */
		if(sl && sl->regionbase.first==NULL) {
			st->free(sl);
			BLI_freelinkN(&sa->spacedata, sl);
			sl= NULL;
		}
		
		if (sl) {
			
			/* swap regions */
			slold->regionbase= sa->regionbase;
			sa->regionbase= sl->regionbase;
			sl->regionbase.first= sl->regionbase.last= NULL;
			
			/* put in front of list */
			BLI_remlink(&sa->spacedata, sl);
			BLI_addhead(&sa->spacedata, sl);
		} 
		else {
			/* new space */
			if(st) {
				sl= st->new(C);
				BLI_addhead(&sa->spacedata, sl);
				
				/* swap regions */
				if(slold)
					slold->regionbase= sa->regionbase;
				sa->regionbase= sl->regionbase;
				sl->regionbase.first= sl->regionbase.last= NULL;
			}
		}
		
		ED_area_initialize(CTX_wm_manager(C), CTX_wm_window(C), sa);
		
		/* tell WM to refresh, cursor types etc */
		WM_event_add_mousemove(C);
		
		ED_area_tag_redraw(sa);
		ED_area_tag_refresh(sa);
	}
}

void ED_area_prevspace(bContext *C)
{
	SpaceLink *sl= CTX_wm_space_data(C);
	ScrArea *sa= CTX_wm_area(C);

	/* cleanup */
#if 0 // XXX needs to be space type specific
	if(sfile->spacetype==SPACE_FILE) {
		if(sfile->pupmenu) {
			MEM_freeN(sfile->pupmenu);
			sfile->pupmenu= NULL;
		}
	}
#endif

	if(sl->next) {

#if 0 // XXX check whether this is still needed
		if (sfile->spacetype == SPACE_SCRIPT) {
			SpaceScript *sc = (SpaceScript *)sfile;
			if (sc->script) sc->script->flags &=~SCRIPT_FILESEL;
		}
#endif

		ED_area_newspace(C, sa, sl->next->spacetype);
	}
	else {
		ED_area_newspace(C, sa, SPACE_INFO);
	}
	ED_area_tag_redraw(sa);
}

static char *windowtype_pup(void)
{
	return(
		   "Window type:%t" //14
		   "|3D View %x1" //30
		   
		   "|%l" // 33
		   
		   "|Graph Editor %x2" //54
		   "|DopeSheet %x12" //73
		   "|NLA Editor %x13" //94
		   
		   "|%l" //97
		   
		   "|UV/Image Editor %x6" //117
		   
		   "|Video Sequence Editor %x8" //143
		   "|Timeline %x15" //163
		   "|Audio Window %x11" //163
		   "|Text Editor %x9" //179
		   
		   "|%l" //192
		   
		   
		   "|User Preferences %x7" //213
		   "|Outliner %x3" //232
		   "|Buttons Window %x4" //251
		   "|Node Editor %x16"
		   "|%l" //254
		   
		   "|File Browser %x5" //290
		   
		   "|%l" //293
		   
		   "|Scripts Window %x14"//313
		   );
}

static void spacefunc(struct bContext *C, void *arg1, void *arg2)
{
	ED_area_newspace(C, CTX_wm_area(C), CTX_wm_area(C)->butspacetype);
	ED_area_tag_redraw(CTX_wm_area(C));
}

/* returns offset for next button in header */
int ED_area_header_standardbuttons(const bContext *C, uiBlock *block, int yco)
{
	ScrArea *sa= CTX_wm_area(C);
	uiBut *but;
	int xco= 8;
	
	but= uiDefIconTextButC(block, ICONTEXTROW, 0, ICON_VIEW3D, 
						   windowtype_pup(), xco, yco, XIC+10, YIC, 
						   &(sa->butspacetype), 1.0, SPACEICONMAX, 0, 0, 
						   "Displays Current Window Type. "
						   "Click for menu of available types.");
	uiButSetFunc(but, spacefunc, NULL, NULL);
	
	xco += XIC + 14;
	
	uiBlockSetEmboss(block, UI_EMBOSSN);
	if (sa->flag & HEADER_NO_PULLDOWN) {
		uiDefIconButBitS(block, TOG, HEADER_NO_PULLDOWN, 0, 
						 ICON_DISCLOSURE_TRI_RIGHT,
						 xco,yco,XIC,YIC-2,
						 &(sa->flag), 0, 0, 0, 0, 
						 "Show pulldown menus");
	}
	else {
		uiDefIconButBitS(block, TOG, HEADER_NO_PULLDOWN, 0, 
						 ICON_DISCLOSURE_TRI_DOWN,
						 xco,yco,XIC,YIC-2,
						 &(sa->flag), 0, 0, 0, 0, 
						 "Hide pulldown menus");
	}
	xco+=XIC;
	
	uiBlockSetEmboss(block, UI_EMBOSS);
	
	return xco;
}

/************************ standard UI regions ************************/

void ED_region_panels(const bContext *C, ARegion *ar, int vertical, char *context)
{
	uiStyle *style= U.uistyles.first;
	uiBlock *block;
	PanelType *pt;
	Panel *panel;
	View2D *v2d= &ar->v2d;
	float col[3];
	int xco, yco, x, y, miny=0, w, em, header, triangle, open;

	if(vertical) {
		w= v2d->cur.xmax - v2d->cur.xmin;
		em= (ar->type->minsizex)? 10: 20;
	}
	else {
		w= UI_PANEL_WIDTH;
		em= (ar->type->minsizex)? 10: 20;
	}

	header= 20; // XXX
	triangle= 22;
	x= 0;
	y= -style->panelouter;

	/* create panels */
	uiBeginPanels(C, ar);

	/* set view2d view matrix for scrolling (without scrollers) */
	UI_view2d_view_ortho(C, v2d);

	for(pt= ar->type->paneltypes.first; pt; pt= pt->next) {
		/* verify context */
		if(context)
			if(!pt->context || strcmp(context, pt->context) != 0)
				continue;

		/* draw panel */
		if(pt->draw && (!pt->poll || pt->poll(C, pt))) {
			block= uiBeginBlock(C, ar, pt->idname, UI_EMBOSS);
			panel= uiBeginPanel(ar, block, pt, &open);

			if(vertical)
				y -= header;

			if(pt->draw_header && (open || vertical)) {
				/* for enabled buttons */
				panel->layout= uiBlockLayout(block, UI_LAYOUT_HORIZONTAL, UI_LAYOUT_HEADER,
					triangle, header+style->panelspace, header, 1, style);

				pt->draw_header(C, panel);

				uiBlockLayoutResolve(C, block, &xco, &yco);
				panel->labelofs= xco - triangle;
				panel->layout= NULL;
			}

			if(open) {
				panel->type= pt;
				panel->layout= uiBlockLayout(block, UI_LAYOUT_VERTICAL, UI_LAYOUT_PANEL,
					style->panelspace, 0, w-2*style->panelspace, em, style);

				pt->draw(C, panel);

				uiBlockLayoutResolve(C, block, &xco, &yco);
				panel->layout= NULL;

				yco -= 2*style->panelspace;
				uiEndPanel(block, w, -yco);
			}
			else
				yco= 0;

			uiEndBlock(C, block);

			if(vertical) {
				y += yco-style->panelouter;
			}
			else {
				x += w;
				miny= MIN2(y, yco-style->panelouter-header);
			}
		}
	}

	if(vertical)
		x += w;
	else
		y= miny;
	
	/* in case there are no panels */
	if(x == 0 || y == 0) {
		x= UI_PANEL_WIDTH;
		y= UI_PANEL_WIDTH;
	}

	/* clear */
	UI_GetThemeColor3fv(TH_BACK, col);
	glClearColor(col[0], col[1], col[2], 0.0);
	glClear(GL_COLOR_BUFFER_BIT);

	/* before setting the view */
	if(vertical) {
		v2d->keepofs |= V2D_LOCKOFS_X;
		v2d->keepofs &= ~V2D_LOCKOFS_Y;
	}
	else {
		v2d->keepofs &= ~V2D_LOCKOFS_X;
		v2d->keepofs |= V2D_LOCKOFS_Y;
	}

	UI_view2d_totRect_set(v2d, x, -y);

	/* set the view */
	UI_view2d_view_ortho(C, v2d);

	/* this does the actual drawing! */
	uiEndPanels(C, ar);
	
	/* restore view matrix */
	UI_view2d_view_restore(C);
}

void ED_region_panels_init(wmWindowManager *wm, ARegion *ar)
{
	ListBase *keymap;

	UI_view2d_region_reinit(&ar->v2d, V2D_COMMONVIEW_PANELS_UI, ar->winx, ar->winy);

	keymap= WM_keymap_listbase(wm, "View2D Buttons List", 0, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
}

void ED_region_header(const bContext *C, ARegion *ar)
{
	uiStyle *style= U.uistyles.first;
	uiBlock *block;
	uiLayout *layout;
	HeaderType *ht;
	Header header = {0};
	float col[3];
	int xco, yco;

	/* clear */
	if(ED_screen_area_active(C))
		UI_GetThemeColor3fv(TH_HEADER, col);
	else
		UI_GetThemeColor3fv(TH_HEADERDESEL, col);
	
	glClearColor(col[0], col[1], col[2], 0.0);
	glClear(GL_COLOR_BUFFER_BIT);
	
	/* set view2d view matrix for scrolling (without scrollers) */
	UI_view2d_view_ortho(C, &ar->v2d);

	xco= 8;
	yco= HEADERY-3;

	/* draw all headers types */
	for(ht= ar->type->headertypes.first; ht; ht= ht->next) {
		block= uiBeginBlock(C, ar, "header buttons", UI_EMBOSS);
		layout= uiBlockLayout(block, UI_LAYOUT_HORIZONTAL, UI_LAYOUT_HEADER, xco, yco, HEADERY-6, 1, style);

		if(ht->draw) {
			header.type= ht;
			header.layout= layout;
			ht->draw(C, &header);
		}

		uiBlockLayoutResolve(C, block, &xco, &yco);
		uiEndBlock(C, block);
		uiDrawBlock(C, block);
	}

	/* always as last  */
	UI_view2d_totRect_set(&ar->v2d, xco+XIC+80, ar->v2d.tot.ymax-ar->v2d.tot.ymin);

	/* restore view matrix? */
	UI_view2d_view_restore(C);
}

void ED_region_header_init(ARegion *ar)
{
	UI_view2d_region_reinit(&ar->v2d, V2D_COMMONVIEW_HEADER, ar->winx, ar->winy);
}

