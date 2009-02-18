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
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_vec_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_texture_types.h"
#include "DNA_userdef_types.h"

#include "BLI_blenlib.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_node.h"
#include "BKE_screen.h"
#include "BKE_scene.h"
#include "BKE_utildefines.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_screen.h"
#include "ED_screen_types.h"

#include "wm_subwindow.h"

#include "screen_intern.h"	/* own module include */


/* ******************* screen vert, edge, area managing *********************** */

static ScrVert *screen_addvert(bScreen *sc, short x, short y)
{
	ScrVert *sv= MEM_callocN(sizeof(ScrVert), "addscrvert");
	sv->vec.x= x;
	sv->vec.y= y;
	
	BLI_addtail(&sc->vertbase, sv);
	return sv;
}

static void sortscrvert(ScrVert **v1, ScrVert **v2)
{
	ScrVert *tmp;
	
	if (*v1 > *v2) {
		tmp= *v1;
		*v1= *v2;
		*v2= tmp;	
	}
}

static ScrEdge *screen_addedge(bScreen *sc, ScrVert *v1, ScrVert *v2)
{
	ScrEdge *se= MEM_callocN(sizeof(ScrEdge), "addscredge");
	
	sortscrvert(&v1, &v2);
	se->v1= v1;
	se->v2= v2;
	
	BLI_addtail(&sc->edgebase, se);
	return se;
}


ScrEdge *screen_findedge(bScreen *sc, ScrVert *v1, ScrVert *v2)
{
	ScrEdge *se;
	
	sortscrvert(&v1, &v2);
	for (se= sc->edgebase.first; se; se= se->next)
		if(se->v1==v1 && se->v2==v2)
			return se;
	
	return NULL;
}

void removedouble_scrverts(bScreen *sc)
{
	ScrVert *v1, *verg;
	ScrEdge *se;
	ScrArea *sa;
	
	verg= sc->vertbase.first;
	while(verg) {
		if(verg->newv==NULL) {	/* !!! */
			v1= verg->next;
			while(v1) {
				if(v1->newv==NULL) {	/* !?! */
					if(v1->vec.x==verg->vec.x && v1->vec.y==verg->vec.y) {
						/* printf("doublevert\n"); */
						v1->newv= verg;
					}
				}
				v1= v1->next;
			}
		}
		verg= verg->next;
	}

	/* replace pointers in edges and faces */
	se= sc->edgebase.first;
	while(se) {
		if(se->v1->newv) se->v1= se->v1->newv;
		if(se->v2->newv) se->v2= se->v2->newv;
		/* edges changed: so.... */
		sortscrvert(&(se->v1), &(se->v2));
		se= se->next;
	}
	sa= sc->areabase.first;
	while(sa) {
		if(sa->v1->newv) sa->v1= sa->v1->newv;
		if(sa->v2->newv) sa->v2= sa->v2->newv;
		if(sa->v3->newv) sa->v3= sa->v3->newv;
		if(sa->v4->newv) sa->v4= sa->v4->newv;
		sa= sa->next;
	}

	/* remove */
	verg= sc->vertbase.first;
	while(verg) {
		v1= verg->next;
		if(verg->newv) {
			BLI_remlink(&sc->vertbase, verg);
			MEM_freeN(verg);
		}
		verg= v1;
	}

}

void removenotused_scrverts(bScreen *sc)
{
	ScrVert *sv, *svn;
	ScrEdge *se;
	
	/* we assume edges are ok */
	
	se= sc->edgebase.first;
	while(se) {
		se->v1->flag= 1;
		se->v2->flag= 1;
		se= se->next;
	}
	
	sv= sc->vertbase.first;
	while(sv) {
		svn= sv->next;
		if(sv->flag==0) {
			BLI_remlink(&sc->vertbase, sv);
			MEM_freeN(sv);
		}
		else sv->flag= 0;
		sv= svn;
	}
}

void removedouble_scredges(bScreen *sc)
{
	ScrEdge *verg, *se, *sn;
	
	/* compare */
	verg= sc->edgebase.first;
	while(verg) {
		se= verg->next;
		while(se) {
			sn= se->next;
			if(verg->v1==se->v1 && verg->v2==se->v2) {
				BLI_remlink(&sc->edgebase, se);
				MEM_freeN(se);
			}
			se= sn;
		}
		verg= verg->next;
	}
}

void removenotused_scredges(bScreen *sc)
{
	ScrEdge *se, *sen;
	ScrArea *sa;
	int a=0;
	
	/* sets flags when edge is used in area */
	sa= sc->areabase.first;
	while(sa) {
		se= screen_findedge(sc, sa->v1, sa->v2);
		if(se==0) printf("error: area %d edge 1 doesn't exist\n", a);
		else se->flag= 1;
		se= screen_findedge(sc, sa->v2, sa->v3);
		if(se==0) printf("error: area %d edge 2 doesn't exist\n", a);
		else se->flag= 1;
		se= screen_findedge(sc, sa->v3, sa->v4);
		if(se==0) printf("error: area %d edge 3 doesn't exist\n", a);
		else se->flag= 1;
		se= screen_findedge(sc, sa->v4, sa->v1);
		if(se==0) printf("error: area %d edge 4 doesn't exist\n", a);
		else se->flag= 1;
		sa= sa->next;
		a++;
	}
	se= sc->edgebase.first;
	while(se) {
		sen= se->next;
		if(se->flag==0) {
			BLI_remlink(&sc->edgebase, se);
			MEM_freeN(se);
		}
		else se->flag= 0;
		se= sen;
	}
}

int scredge_is_horizontal(ScrEdge *se)
{
	return (se->v1->vec.y == se->v2->vec.y);
}

ScrEdge *screen_find_active_scredge(bScreen *sc, int mx, int my)
{
	ScrEdge *se;
	
	for (se= sc->edgebase.first; se; se= se->next) {
		if (scredge_is_horizontal(se)) {
			short min, max;
			min= MIN2(se->v1->vec.x, se->v2->vec.x);
			max= MAX2(se->v1->vec.x, se->v2->vec.x);
			
			if (abs(my-se->v1->vec.y)<=2 && mx>=min && mx<=max)
				return se;
		} 
		else {
			short min, max;
			min= MIN2(se->v1->vec.y, se->v2->vec.y);
			max= MAX2(se->v1->vec.y, se->v2->vec.y);
			
			if (abs(mx-se->v1->vec.x)<=2 && my>=min && my<=max)
				return se;
		}
	}
	
	return NULL;
}



/* adds no space data */
static ScrArea *screen_addarea(bScreen *sc, ScrVert *v1, ScrVert *v2, ScrVert *v3, ScrVert *v4, short headertype, short spacetype)
{
	ScrArea *sa= MEM_callocN(sizeof(ScrArea), "addscrarea");
	sa->v1= v1;
	sa->v2= v2;
	sa->v3= v3;
	sa->v4= v4;
	sa->headertype= headertype;
	sa->spacetype= sa->butspacetype= spacetype;
	
	BLI_addtail(&sc->areabase, sa);
	
	return sa;
}

static void screen_delarea(bContext *C, bScreen *sc, ScrArea *sa)
{
	
	ED_area_exit(C, sa);
	
	BKE_screen_area_free(sa);
	
	BLI_remlink(&sc->areabase, sa);
	MEM_freeN(sa);
}

/* return 0: no split possible */
/* else return (integer) screencoordinate split point */
static short testsplitpoint(wmWindow *win, ScrArea *sa, char dir, float fac)
{
	short x, y;
	
	// area big enough?
	if(dir=='v' && (sa->v4->vec.x- sa->v1->vec.x <= 2*AREAMINX)) return 0;
	if(dir=='h' && (sa->v2->vec.y- sa->v1->vec.y <= 2*AREAMINY)) return 0;
	
	// to be sure
	if(fac<0.0) fac= 0.0;
	if(fac>1.0) fac= 1.0;
	
	if(dir=='h') {
		y= sa->v1->vec.y+ fac*(sa->v2->vec.y- sa->v1->vec.y);
		
		if(y- sa->v1->vec.y < AREAMINY) 
			y= sa->v1->vec.y+ AREAMINY;
		else if(sa->v2->vec.y- y < AREAMINY) 
			y= sa->v2->vec.y- AREAMINY;
		else y-= (y % AREAGRID);
		
		return y;
	}
	else {
		x= sa->v1->vec.x+ fac*(sa->v4->vec.x- sa->v1->vec.x);
		
		if(x- sa->v1->vec.x < AREAMINX) 
			x= sa->v1->vec.x+ AREAMINX;
		else if(sa->v4->vec.x- x < AREAMINX) 
			x= sa->v4->vec.x- AREAMINX;
		else x-= (x % AREAGRID);
		
		return x;
	}
}

ScrArea *area_split(wmWindow *win, bScreen *sc, ScrArea *sa, char dir, float fac)
{
	ScrArea *newa=NULL;
	ScrVert *sv1, *sv2;
	short split;
	
	if(sa==NULL) return NULL;
	
	split= testsplitpoint(win, sa, dir, fac);
	if(split==0) return NULL;
	
	if(dir=='h') {
		/* new vertices */
		sv1= screen_addvert(sc, sa->v1->vec.x, split);
		sv2= screen_addvert(sc, sa->v4->vec.x, split);
		
		/* new edges */
		screen_addedge(sc, sa->v1, sv1);
		screen_addedge(sc, sv1, sa->v2);
		screen_addedge(sc, sa->v3, sv2);
		screen_addedge(sc, sv2, sa->v4);
		screen_addedge(sc, sv1, sv2);
		
		/* new areas: top */
		newa= screen_addarea(sc, sv1, sa->v2, sa->v3, sv2, sa->headertype, sa->spacetype);
		area_copy_data(newa, sa, 0);
		
		/* area below */
		sa->v2= sv1;
		sa->v3= sv2;
		
	}
	else {
		/* new vertices */
		sv1= screen_addvert(sc, split, sa->v1->vec.y);
		sv2= screen_addvert(sc, split, sa->v2->vec.y);
		
		/* new edges */
		screen_addedge(sc, sa->v1, sv1);
		screen_addedge(sc, sv1, sa->v4);
		screen_addedge(sc, sa->v2, sv2);
		screen_addedge(sc, sv2, sa->v3);
		screen_addedge(sc, sv1, sv2);
		
		/* new areas: left */
		newa= screen_addarea(sc, sa->v1, sa->v2, sv2, sv1, sa->headertype, sa->spacetype);
		area_copy_data(newa, sa, 0);
		
		/* area right */
		sa->v1= sv1;
		sa->v2= sv2;
	}
	
	/* remove double vertices en edges */
	removedouble_scrverts(sc);
	removedouble_scredges(sc);
	removenotused_scredges(sc);
	
	return newa;
}

/* empty screen, with 1 dummy area without spacedata */
/* uses window size */
bScreen *screen_add(wmWindow *win, Scene *scene, char *name)
{
	bScreen *sc;
	ScrVert *sv1, *sv2, *sv3, *sv4;
	
	sc= alloc_libblock(&G.main->screen, ID_SCR, name);
	sc->scene= scene;
	sc->do_refresh= 1;
	sc->winid= win->winid;
	
	sv1= screen_addvert(sc, 0, 0);
	sv2= screen_addvert(sc, 0, win->sizey-1);
	sv3= screen_addvert(sc, win->sizex-1, win->sizey-1);
	sv4= screen_addvert(sc, win->sizex-1, 0);
	
	screen_addedge(sc, sv1, sv2);
	screen_addedge(sc, sv2, sv3);
	screen_addedge(sc, sv3, sv4);
	screen_addedge(sc, sv4, sv1);
	
	/* dummy type, no spacedata */
	screen_addarea(sc, sv1, sv2, sv3, sv4, HEADERDOWN, SPACE_EMPTY);
		
	return sc;
}

static void screen_copy(bScreen *to, bScreen *from)
{
	ScrVert *s1, *s2;
	ScrEdge *se;
	ScrArea *sa, *saf;
	
	/* free contents of 'to', is from blenkernel screen.c */
	free_screen(to);
	
	BLI_duplicatelist(&to->vertbase, &from->vertbase);
	BLI_duplicatelist(&to->edgebase, &from->edgebase);
	BLI_duplicatelist(&to->areabase, &from->areabase);
	to->regionbase.first= to->regionbase.last= NULL;
	
	s2= to->vertbase.first;
	for(s1= from->vertbase.first; s1; s1= s1->next, s2= s2->next) {
		s1->newv= s2;
	}
	
	for(se= to->edgebase.first; se; se= se->next) {
		se->v1= se->v1->newv;
		se->v2= se->v2->newv;
		sortscrvert(&(se->v1), &(se->v2));
	}
	
	saf= from->areabase.first;
	for(sa= to->areabase.first; sa; sa= sa->next, saf= saf->next) {
		sa->v1= sa->v1->newv;
		sa->v2= sa->v2->newv;
		sa->v3= sa->v3->newv;
		sa->v4= sa->v4->newv;
		
		sa->spacedata.first= sa->spacedata.last= NULL;
		sa->regionbase.first= sa->regionbase.last= NULL;
		sa->actionzones.first= sa->actionzones.last= NULL;
		sa->scriptlink.totscript= 0;
		
		area_copy_data(sa, saf, 0);
	}
	
	/* put at zero (needed?) */
	for(s1= from->vertbase.first; s1; s1= s1->next)
		s1->newv= NULL;

}


/* with sa as center, sb is located at: 0=W, 1=N, 2=E, 3=S */
/* -1 = not valid check */
/* used with join operator */
int area_getorientation(bScreen *screen, ScrArea *sa, ScrArea *sb)
{
	ScrVert *sav1, *sav2, *sav3, *sav4;
	ScrVert *sbv1, *sbv2, *sbv3, *sbv4;

	if(sa==NULL || sb==NULL) return -1;

	sav1= sa->v1;
	sav2= sa->v2;
	sav3= sa->v3;
	sav4= sa->v4;
	sbv1= sb->v1;
	sbv2= sb->v2;
	sbv3= sb->v3;
	sbv4= sb->v4;
	
	if(sav1==sbv4 && sav2==sbv3) { /* sa to right of sb = W */
		return 0;
	}
	else if(sav2==sbv1 && sav3==sbv4) { /* sa to bottom of sb = N */
		return 1;
	}
	else if(sav3==sbv2 && sav4==sbv1) { /* sa to left of sb = E */
		return 2;
	}
	else if(sav1==sbv2 && sav4==sbv3) { /* sa on top of sb = S*/
		return 3;
	}
	
	return -1;
}

/* Helper function to join 2 areas, it has a return value, 0=failed 1=success
* 	used by the split, join operators
*/
int screen_area_join(bContext *C, bScreen* scr, ScrArea *sa1, ScrArea *sa2) 
{
	int dir;
	
	dir = area_getorientation(scr, sa1, sa2);
	/*printf("dir is : %i \n", dir);*/
	
	if (dir < 0)
	{
		if (sa1 ) sa1->flag &= ~AREA_FLAG_DRAWJOINFROM;
		if (sa2 ) sa2->flag &= ~AREA_FLAG_DRAWJOINTO;
		return 0;
	}
	
	if(dir == 0) {
		sa1->v1= sa2->v1;
		sa1->v2= sa2->v2;
		screen_addedge(scr, sa1->v2, sa1->v3);
		screen_addedge(scr, sa1->v1, sa1->v4);
	}
	else if(dir == 1) {
		sa1->v2= sa2->v2;
		sa1->v3= sa2->v3;
		screen_addedge(scr, sa1->v1, sa1->v2);
		screen_addedge(scr, sa1->v3, sa1->v4);
	}
	else if(dir == 2) {
		sa1->v3= sa2->v3;
		sa1->v4= sa2->v4;
		screen_addedge(scr, sa1->v2, sa1->v3);
		screen_addedge(scr, sa1->v1, sa1->v4);
	}
	else if(dir == 3) {
		sa1->v1= sa2->v1;
		sa1->v4= sa2->v4;
		screen_addedge(scr, sa1->v1, sa1->v2);
		screen_addedge(scr, sa1->v3, sa1->v4);
	}
	
	screen_delarea(C, scr, sa2);
	removedouble_scrverts(scr);
	sa1->flag &= ~AREA_FLAG_DRAWJOINFROM;
	
	return 1;
}

void select_connected_scredge(bScreen *sc, ScrEdge *edge)
{
	ScrEdge *se;
	ScrVert *sv;
	int oneselected;
	char dir;
	
	/* select connected, only in the right direction */
	/* 'dir' is the direction of EDGE */
	
	if(edge->v1->vec.x==edge->v2->vec.x) dir= 'v';
	else dir= 'h';
	
	sv= sc->vertbase.first;
	while(sv) {
		sv->flag = 0;
		sv= sv->next;
	}
	
	edge->v1->flag= 1;
	edge->v2->flag= 1;
	
	oneselected= 1;
	while(oneselected) {
		se= sc->edgebase.first;
		oneselected= 0;
		while(se) {
			if(se->v1->flag + se->v2->flag==1) {
				if(dir=='h') if(se->v1->vec.y==se->v2->vec.y) {
					se->v1->flag= se->v2->flag= 1;
					oneselected= 1;
				}
					if(dir=='v') if(se->v1->vec.x==se->v2->vec.x) {
						se->v1->flag= se->v2->flag= 1;
						oneselected= 1;
					}
			}
				se= se->next;
		}
	}
}

/* test if screen vertices should be scaled */
static void screen_test_scale(bScreen *sc, int winsizex, int winsizey)
{
	ScrVert *sv=NULL;
	ScrArea *sa;
	int sizex, sizey;
	float facx, facy, tempf, min[2], max[2];
	
	/* calculate size */
	min[0]= min[1]= 10000.0f;
	max[0]= max[1]= 0.0f;
	
	for(sv= sc->vertbase.first; sv; sv= sv->next) {
		min[0]= MIN2(min[0], sv->vec.x);
		min[1]= MIN2(min[1], sv->vec.y);
		max[0]= MAX2(max[0], sv->vec.x);
		max[1]= MAX2(max[1], sv->vec.y);
	}
	
	/* always make 0.0 left under */
	for(sv= sc->vertbase.first; sv; sv= sv->next) {
		sv->vec.x -= min[0];
		sv->vec.y -= min[1];
	}
	
	sizex= max[0]-min[0];
	sizey= max[1]-min[1];
	
	if(sizex!= winsizex || sizey!= winsizey) {
		facx= winsizex;
		facx/= (float)sizex;
		facy= winsizey;
		facy/= (float)sizey;
		
		/* make sure it fits! */
		for(sv= sc->vertbase.first; sv; sv= sv->next) {
			tempf= ((float)sv->vec.x)*facx;
			sv->vec.x= (short)(tempf+0.5);
			sv->vec.x+= AREAGRID-1;
			sv->vec.x-=  (sv->vec.x % AREAGRID); 
			
			CLAMP(sv->vec.x, 0, winsizex);
			
			tempf= ((float)sv->vec.y )*facy;
			sv->vec.y= (short)(tempf+0.5);
			sv->vec.y+= AREAGRID-1;
			sv->vec.y-=  (sv->vec.y % AREAGRID); 
			
			CLAMP(sv->vec.y, 0, winsizey);
		}
	}
	
	/* test for collapsed areas. This could happen in some blender version... */
	/* ton: removed option now, it needs Context... */
	
	/* make each window at least HEADERY high */
	for(sa= sc->areabase.first; sa; sa= sa->next) {
		int headery= HEADERY+1;
		
		if(sa->v1->vec.y+headery > sa->v2->vec.y) {
			/* lower edge */
			ScrEdge *se= screen_findedge(sc, sa->v4, sa->v1);
			if(se && sa->v1!=sa->v2 ) {
				int yval;
				
				select_connected_scredge(sc, se);
				
				/* all selected vertices get the right offset */
				yval= sa->v2->vec.y-headery;
				sv= sc->vertbase.first;
				while(sv) {
					/* if is a collapsed area */
					if(sv!=sa->v2 && sv!=sa->v3) {
						if(sv->flag) sv->vec.y= yval;
					}
					sv= sv->next;
				}
			}
		}
	}
	
}

/* *********************** DRAWING **************************************** */


#define SCR_BACK 0.55
#define SCR_ROUND 12

/* draw vertical shape visualising future joining (left as well
 * right direction of future joining) */
static void draw_horizontal_join_shape(ScrArea *sa, char dir)
{
	vec2f points[10];
	short i;
	float w, h;
	float width = sa->v3->vec.x - sa->v1->vec.x;
	float height = sa->v3->vec.y - sa->v1->vec.y;

	if(height<width) {
		h = height/8;
		w = height/4;
	}
	else {
		h = width/8;
		w = width/4;
	}

	points[0].x = sa->v1->vec.x;
	points[0].y = sa->v1->vec.y + height/2;

	points[1].x = sa->v1->vec.x;
	points[1].y = sa->v1->vec.y;

	points[2].x = sa->v4->vec.x - w;
	points[2].y = sa->v4->vec.y;

	points[3].x = sa->v4->vec.x - w;
	points[3].y = sa->v4->vec.y + height/2 - 2*h;

	points[4].x = sa->v4->vec.x - 2*w;
	points[4].y = sa->v4->vec.y + height/2;

	points[5].x = sa->v4->vec.x - w;
	points[5].y = sa->v4->vec.y + height/2 + 2*h;

	points[6].x = sa->v3->vec.x - w;
	points[6].y = sa->v3->vec.y;

	points[7].x = sa->v2->vec.x;
	points[7].y = sa->v2->vec.y;

	points[8].x = sa->v4->vec.x;
	points[8].y = sa->v4->vec.y + height/2 - h;

	points[9].x = sa->v4->vec.x;
	points[9].y = sa->v4->vec.y + height/2 + h;

	if(dir=='l') {
		/* when direction is left, then we flip direction of arrow */
		float cx = sa->v1->vec.x + width;
		for(i=0;i<10;i++) {
			points[i].x -= cx;
			points[i].x = -points[i].x;
			points[i].x += sa->v1->vec.x;
		}
	}

	glBegin(GL_POLYGON);
	for(i=0;i<5;i++)
		glVertex2f(points[i].x, points[i].y);
	glEnd();
	glBegin(GL_POLYGON);
	for(i=4;i<8;i++)
		glVertex2f(points[i].x, points[i].y);
	glVertex2f(points[0].x, points[0].y);
	glEnd();

	glRectf(points[2].x, points[2].y, points[8].x, points[8].y);
	glRectf(points[6].x, points[6].y, points[9].x, points[9].y);
}

/* draw vertical shape visualising future joining (up/down direction) */
static void draw_vertical_join_shape(ScrArea *sa, char dir)
{
	vec2f points[10];
	short i;
	float w, h;
	float width = sa->v3->vec.x - sa->v1->vec.x;
	float height = sa->v3->vec.y - sa->v1->vec.y;

	if(height<width) {
		h = height/4;
		w = height/8;
	}
	else {
		h = width/4;
		w = width/8;
	}

	points[0].x = sa->v1->vec.x + width/2;
	points[0].y = sa->v3->vec.y;

	points[1].x = sa->v2->vec.x;
	points[1].y = sa->v2->vec.y;

	points[2].x = sa->v1->vec.x;
	points[2].y = sa->v1->vec.y + h;

	points[3].x = sa->v1->vec.x + width/2 - 2*w;
	points[3].y = sa->v1->vec.y + h;

	points[4].x = sa->v1->vec.x + width/2;
	points[4].y = sa->v1->vec.y + 2*h;

	points[5].x = sa->v1->vec.x + width/2 + 2*w;
	points[5].y = sa->v1->vec.y + h;

	points[6].x = sa->v4->vec.x;
	points[6].y = sa->v4->vec.y + h;
	
	points[7].x = sa->v3->vec.x;
	points[7].y = sa->v3->vec.y;

	points[8].x = sa->v1->vec.x + width/2 - w;
	points[8].y = sa->v1->vec.y;

	points[9].x = sa->v1->vec.x + width/2 + w;
	points[9].y = sa->v1->vec.y;

	if(dir=='u') {
		/* when direction is up, then we flip direction of arrow */
		float cy = sa->v1->vec.y + height;
		for(i=0;i<10;i++) {
			points[i].y -= cy;
			points[i].y = -points[i].y;
			points[i].y += sa->v1->vec.y;
		}
	}

	glBegin(GL_POLYGON);
	for(i=0;i<5;i++)
		glVertex2f(points[i].x, points[i].y);
	glEnd();
	glBegin(GL_POLYGON);
	for(i=4;i<8;i++)
		glVertex2f(points[i].x, points[i].y);
	glVertex2f(points[0].x, points[0].y);
	glEnd();

	glRectf(points[2].x, points[2].y, points[8].x, points[8].y);
	glRectf(points[6].x, points[6].y, points[9].x, points[9].y);
}

/* draw join shape due to direction of joining */
static void draw_join_shape(ScrArea *sa, char dir)
{
	if(dir=='u' || dir=='d')
		draw_vertical_join_shape(sa, dir);
	else
		draw_horizontal_join_shape(sa, dir);
}

/* draw screen area darker with arrow (visualisation of future joining) */
static void scrarea_draw_shape_dark(ScrArea *sa, char dir)
{
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
	glEnable(GL_BLEND);
	glColor4ub(0, 0, 0, 50);
	draw_join_shape(sa, dir);
	glDisable(GL_BLEND);
}

/* draw screen area ligher with arrow shape ("eraser" of previous dark shape) */
static void scrarea_draw_shape_light(ScrArea *sa, char dir)
{
	glBlendFunc(GL_DST_COLOR, GL_SRC_ALPHA);
	glEnable(GL_BLEND);
	/* value 181 was hardly computed: 181~105 */
	glColor4ub(255, 255, 255, 50);		
	/* draw_join_shape(sa, dir); */
	glRecti(sa->v1->vec.x, sa->v1->vec.y, sa->v3->vec.x, sa->v3->vec.y);
	glDisable(GL_BLEND);
}

/** screen edges drawing **/
static void drawscredge_area(ScrArea *sa)
{
	short x1= sa->v1->vec.x;
	short y1= sa->v1->vec.y;
	short x2= sa->v3->vec.x;
	short y2= sa->v3->vec.y;
	
	cpack(0x0);
	
	/* right border area */
	sdrawline(x2, y1, x2, y2);
	
	/* left border area */
	if(x1>0) { /* otherwise it draws the emboss of window over */
		sdrawline(x1, y1, x1, y2);
	}
	
	/* top border area */
	sdrawline(x1, y2, x2, y2);
	
	/* bottom border area */
	sdrawline(x1, y1, x2, y1);
	
}

/* ****************** EXPORTED API TO OTHER MODULES *************************** */

bScreen *ED_screen_duplicate(wmWindow *win, bScreen *sc)
{
	bScreen *newsc;
	
	if(sc->full != SCREENNORMAL) return NULL; /* XXX handle this case! */
	
	/* make new empty screen: */
	newsc= screen_add(win, sc->scene, sc->id.name+2);
	/* copy all data */
	screen_copy(newsc, sc);
	/* set in window */
	win->screen= newsc;
	
	/* store identifier */
	win->screen->winid= win->winid;
	BLI_strncpy(win->screenname, win->screen->id.name+2, 21);

	return newsc;
}

/* screen sets cursor based on swinid */
static void region_cursor_set(wmWindow *win, int swinid)
{
	ScrArea *sa= win->screen->areabase.first;
	
	for(;sa; sa= sa->next) {
		ARegion *ar= sa->regionbase.first;
		for(;ar; ar= ar->next) {
			if(ar->swinid == swinid) {
				if(ar->type && ar->type->cursor)
					ar->type->cursor(win, sa, ar);
				else
					WM_cursor_set(win, CURSOR_STD);
				return;
			}
		}
	}
}

void ED_screen_do_listen(wmWindow *win, wmNotifier *note)
{
	
	/* generic notes */
	switch(note->category) {
		case NC_WM:
			if(note->data==ND_FILEREAD)
				win->screen->do_draw= 1;
			break;
		case NC_WINDOW:
			win->screen->do_draw= 1;
			break;
		case NC_SCREEN:
			if(note->action==NA_EDITED)
				win->screen->do_draw= win->screen->do_refresh= 1;
		case NC_SCENE:
			if(note->data==ND_MODE)
				region_cursor_set(win, note->swinid);				
			break;
	}
}

/* only for edge lines between areas, and the blended join arrows */
void ED_screen_draw(wmWindow *win)
{
	ScrArea *sa;
	ScrArea *sa1=NULL;
	ScrArea *sa2=NULL;
	int dir = -1;
	int dira = -1;

	wmSubWindowSet(win, win->screen->mainwin);
	
	for(sa= win->screen->areabase.first; sa; sa= sa->next) {
		if (sa->flag & AREA_FLAG_DRAWJOINFROM) sa1 = sa;
		if (sa->flag & AREA_FLAG_DRAWJOINTO) sa2 = sa;
		drawscredge_area(sa);
	}

	/* blended join arrow */
	if (sa1 && sa2) {
		dir = area_getorientation(win->screen, sa1, sa2);
		if (dir >= 0) {
			switch(dir) {
				case 0: /* W */
					dir = 'r';
					dira = 'l';
					break;
				case 1: /* N */
					dir = 'd';
					dira = 'u';
					break;
				case 2: /* E */
					dir = 'l';
					dira = 'r';
					break;
				case 3: /* S */
					dir = 'u';
					dira = 'd';
					break;
			}
		}
		scrarea_draw_shape_dark(sa2, dir);
		scrarea_draw_shape_light(sa1, dira);
	}
	
//	if(G.f & G_DEBUG) printf("draw screen\n");
	win->screen->do_draw= 0;
}

/* make this screen usable */
/* for file read and first use, for scaling window, area moves */
void ED_screen_refresh(wmWindowManager *wm, wmWindow *win)
{
	ScrArea *sa;
	rcti winrct= {0, win->sizex-1, 0, win->sizey-1};
	
	screen_test_scale(win->screen, win->sizex, win->sizey);
	
	if(win->screen->mainwin==0)
		win->screen->mainwin= wm_subwindow_open(win, &winrct);
	else
		wm_subwindow_position(win, win->screen->mainwin, &winrct);
	
	for(sa= win->screen->areabase.first; sa; sa= sa->next) {
		/* set spacetype and region callbacks, calls init() */
		/* sets subwindows for regions, adds handlers */
		ED_area_initialize(wm, win, sa);
	}

	/* wake up animtimer */
	if(win->screen->animtimer)
		WM_event_window_timer_sleep(win, win->screen->animtimer, 0);
	
	if(G.f & G_DEBUG) printf("set screen\n");
	win->screen->do_refresh= 0;

	win->screen->context= ed_screen_context;
}

/* file read, set all screens, ... */
void ED_screens_initialize(wmWindowManager *wm)
{
	wmWindow *win;
	
	for(win= wm->windows.first; win; win= win->next) {
		
		if(win->screen==NULL)
			win->screen= G.main->screen.first;
		
		ED_screen_refresh(wm, win);
	}
}


/* *********** exit calls are for closing running stuff ******** */

void ED_region_exit(bContext *C, ARegion *ar)
{
	ARegion *prevar= CTX_wm_region(C);

	CTX_wm_region_set(C, ar);
	WM_event_remove_handlers(C, &ar->handlers);
	if(ar->swinid)
		wm_subwindow_close(CTX_wm_window(C), ar->swinid);
	ar->swinid= 0;
	
	if(ar->headerstr)
		MEM_freeN(ar->headerstr);
	ar->headerstr= NULL;
	
	CTX_wm_region_set(C, prevar);
}

void ED_area_exit(bContext *C, ScrArea *sa)
{
	ScrArea *prevsa= CTX_wm_area(C);
	ARegion *ar;

	CTX_wm_area_set(C, sa);
	for(ar= sa->regionbase.first; ar; ar= ar->next)
		ED_region_exit(C, ar);

	WM_event_remove_handlers(C, &sa->handlers);
	CTX_wm_area_set(C, prevsa);
}

void ED_screen_exit(bContext *C, wmWindow *window, bScreen *screen)
{
	wmWindow *prevwin= CTX_wm_window(C);
	ScrArea *sa;
	ARegion *ar;

	CTX_wm_window_set(C, window);
	
	if(screen->animtimer)
		WM_event_remove_window_timer(window, screen->animtimer);
	screen->animtimer= NULL;
	
	if(screen->mainwin)
		wm_subwindow_close(window, screen->mainwin);
	screen->mainwin= 0;
	screen->subwinactive= 0;
	
	for(ar= screen->regionbase.first; ar; ar= ar->next)
		ED_region_exit(C, ar);

	for(sa= screen->areabase.first; sa; sa= sa->next)
		ED_area_exit(C, sa);

	/* mark it available for use for other windows */
	screen->winid= 0;
	
	CTX_wm_window_set(C, prevwin);
}

/* *********************************** */

/* case when on area-edge or in azones, or outside window */
static void screen_cursor_set(wmWindow *win, wmEvent *event)
{
	ScrArea *sa;
	
	for(sa= win->screen->areabase.first; sa; sa= sa->next)
		if(is_in_area_actionzone(sa, event->x, event->y))
			break;
	
	if(sa) {
		WM_cursor_set(win, CURSOR_EDIT);
	}
	else {
		ScrEdge *actedge= screen_find_active_scredge(win->screen, event->x, event->y);
		
		if (actedge) {
			if(scredge_is_horizontal(actedge))
				WM_cursor_set(win, CURSOR_Y_MOVE);
			else
				WM_cursor_set(win, CURSOR_X_MOVE);
		}
		else
			WM_cursor_set(win, CURSOR_STD);
	} 
}


/* called in wm_event_system.c. sets state vars in screen, cursors */
/* event type is mouse move */
void ED_screen_set_subwinactive(wmWindow *win, wmEvent *event)
{
	if(win->screen) {
		bScreen *scr= win->screen;
		ScrArea *sa;
		ARegion *ar;
		int oldswin= scr->subwinactive;

		for(sa= scr->areabase.first; sa; sa= sa->next) {
			if(event->x > sa->totrct.xmin && event->x < sa->totrct.xmax)
				if(event->y > sa->totrct.ymin && event->y < sa->totrct.ymax)
					if(NULL==is_in_area_actionzone(sa, event->x, event->y))
						break;
		}
		if(sa) {
			for(ar= sa->regionbase.first; ar; ar= ar->next) {
				if(BLI_in_rcti(&ar->winrct, event->x, event->y))
					scr->subwinactive= ar->swinid;
			}
		}
		else
			scr->subwinactive= scr->mainwin;
		
		/* check for redraw headers */
		if(oldswin!=scr->subwinactive) {

			for(sa= scr->areabase.first; sa; sa= sa->next) {
				int do_draw= 0;
				
				for(ar= sa->regionbase.first; ar; ar= ar->next)
					if(ar->swinid==oldswin || ar->swinid==scr->subwinactive)
						do_draw= 1;
				
				if(do_draw) {
					for(ar= sa->regionbase.first; ar; ar= ar->next)
						if(ar->regiontype==RGN_TYPE_HEADER)
							ED_region_tag_redraw(ar);
				}
			}
		}
		
		/* cursors, for time being set always on edges, otherwise aregion doesnt switch */
		if(scr->subwinactive==scr->mainwin) {
			screen_cursor_set(win, event);
		}
		else if(oldswin!=scr->subwinactive) {
			region_cursor_set(win, scr->subwinactive);
		}
	}
}

int ED_screen_area_active(const bContext *C)
{
	bScreen *sc= CTX_wm_screen(C);
	ScrArea *sa= CTX_wm_area(C);

	if(sc && sa) {
		ARegion *ar;
		for(ar= sa->regionbase.first; ar; ar= ar->next)
			if(ar->swinid == sc->subwinactive)
				return 1;
	}	
	return 0;
}

/* operator call, WM + Window + screen already existed before */
/* Do NOT call in area/region queues! */
void ED_screen_set(bContext *C, bScreen *sc)
{
	wmWindow *win= CTX_wm_window(C);
	bScreen *oldscreen= CTX_wm_screen(C);
	ID *id;
	
	/* validate screen, it's called with notifier reference */
	for(id= CTX_data_main(C)->screen.first; id; id= id->next)
		if(sc == (bScreen *)id)
			break;
	if(id==NULL) 
		return;
	
	/* check for valid winid */
	if(sc->winid!=0 && sc->winid!=win->winid)
		return;
	
	if(sc->full) {				/* find associated full */
		bScreen *sc1;
		for(sc1= CTX_data_main(C)->screen.first; sc1; sc1= sc1->id.next) {
			ScrArea *sa= sc1->areabase.first;
			if(sa->full==sc) {
				sc= sc1;
				break;
			}
		}
	}
	
	if (oldscreen != sc) {
		wmTimer *wt= oldscreen->animtimer;
		
		/* we put timer to sleep, so screen_exit has to think there's no timer */
		oldscreen->animtimer= NULL;
		if(wt)
			WM_event_window_timer_sleep(win, wt, 1);
		
		ED_screen_exit(C, win, oldscreen);
		oldscreen->animtimer= wt;
		
		win->screen= sc;
		CTX_wm_window_set(C, win);	// stores C->wm.screen... hrmf
		
		/* prevent multiwin errors */
		sc->winid= win->winid;
		
		ED_screen_refresh(CTX_wm_manager(C), CTX_wm_window(C));
		WM_event_add_notifier(C, NC_WINDOW, NULL);
	}
}

/* only call outside of area/region loops */
void ED_screen_set_scene(bContext *C, Scene *scene)
{
	bScreen *sc;
	bScreen *curscreen= CTX_wm_screen(C);
	
	for(sc= CTX_data_main(C)->screen.first; sc; sc= sc->id.next) {
		if((U.flag & USER_SCENEGLOBAL) || sc==curscreen) {
			
			if(scene != sc->scene) {
				/* all areas endlocalview */
			// XXX	ScrArea *sa= sc->areabase.first;
			//	while(sa) {
			//		endlocalview(sa);
			//		sa= sa->next;
			//	}		
				sc->scene= scene;
			}
			
		}
	}
	
	//  copy_view3d_lock(0);	/* space.c */
	
	/* are there cameras in the views that are not in the scene? */
	for(sc= CTX_data_main(C)->screen.first; sc; sc= sc->id.next) {
		if( (U.flag & USER_SCENEGLOBAL) || sc==curscreen) {
			ScrArea *sa= sc->areabase.first;
			while(sa) {
				SpaceLink *sl= sa->spacedata.first;
				while(sl) {
					if(sl->spacetype==SPACE_VIEW3D) {
						View3D *v3d= (View3D*) sl;
						if (!v3d->camera || !object_in_scene(v3d->camera, scene)) {
							v3d->camera= scene_find_camera(sc->scene);
							// XXX if (sc==curscreen) handle_view3d_lock();
							if (!v3d->camera && v3d->persp==V3D_CAMOB) 
								v3d->persp= V3D_PERSP;
						}
					}
					sl= sl->next;
				}
				sa= sa->next;
			}
		}
	}
	
	CTX_data_scene_set(C, scene);
	set_scene_bg(scene);
	
	ED_update_for_newframe(C, 1);
	
//	set_radglobal();
	
	/* complete redraw */
	WM_event_add_notifier(C, NC_WINDOW, NULL);
	
}

/* this function toggles: if area is full then the parent will be restored */
void ed_screen_fullarea(bContext *C, ScrArea *sa)
{
	bScreen *sc, *oldscreen;
	
	if(sa==NULL) {
		return;
	}
	else if(sa->full) {
		short fulltype;
		
		sc= sa->full;		/* the old screen to restore */
		oldscreen= CTX_wm_screen(C);	/* the one disappearing */
		
		fulltype = sc->full;
		
		/* refuse to go out of SCREENAUTOPLAY as long as G_FLAGS_AUTOPLAY
		   is set */
		
		if (fulltype != SCREENAUTOPLAY || (G.flags & G_FILE_AUTOPLAY) == 0) {
			ScrArea *old;
			
			sc->full= 0;
			
			/* find old area */
			for(old= sc->areabase.first; old; old= old->next) 
				if(old->full) break;
			if(old==NULL) {
				printf("something wrong in areafullscreen\n"); 
				return;
			}
			    // old feature described below (ton)
				// in autoplay screens the headers are disabled by 
				// default. So use the old headertype instead
			
			area_copy_data(old, sa, 1);	/*  1 = swap spacelist */
			
			old->full= NULL;
			
			/* animtimer back */
			sc->animtimer= oldscreen->animtimer;
			oldscreen->animtimer= NULL;
			
			ED_screen_set(C, sc);
			
			free_screen(oldscreen);
			free_libblock(&CTX_data_main(C)->screen, oldscreen);
		}
	}
	else {
		ScrArea *newa;
		
		oldscreen= CTX_wm_screen(C);

		/* is there only 1 area? */
		if(oldscreen->areabase.first==oldscreen->areabase.last) return;
		
		oldscreen->full = SCREENFULL;
		
		sc= screen_add(CTX_wm_window(C), CTX_data_scene(C), "temp");
		sc->full = SCREENFULL; // XXX
		
		/* timer */
		sc->animtimer= oldscreen->animtimer;
		oldscreen->animtimer= NULL;
		
		/* returns the top small area */
		newa= area_split(CTX_wm_window(C), sc, (ScrArea *)sc->areabase.first, 'h', 0.99f);
		ED_area_newspace(C, newa, SPACE_INFO);

		/* copy area */
		newa= newa->prev;
		area_copy_data(newa, sa, 1);	/* 1 = swap spacelist */

		sa->full= oldscreen;
		newa->full= oldscreen;
		newa->next->full= oldscreen; // XXX

		ED_screen_set(C, sc);
	}

	/* XXX bad code: setscreen() ends with first area active. fullscreen render assumes this too */
	CTX_wm_area_set(C, sc->areabase.first);

	/* XXX retopo_force_update(); */

}

int ED_screen_full_newspace(bContext *C, ScrArea *sa, int type)
{
	if(sa==NULL)
		return 0;
	
	if(sa->full==0)
		ed_screen_fullarea(C, sa);

	/* CTX_wm_area(C) is new area */
	ED_area_newspace(C, CTX_wm_area(C), type);
	
	return 1;
}

void ED_screen_full_prevspace(bContext *C)
{
	ScrArea *sa= CTX_wm_area(C);
	
	ED_area_prevspace(C);
	
	if(sa->full)
		ed_screen_fullarea(C, sa);
}

void ED_screen_animation_timer(bContext *C, int enable)
{
	bScreen *screen= CTX_wm_screen(C);
	wmWindow *win= CTX_wm_window(C);
	Scene *scene= CTX_data_scene(C);
	
	if(screen->animtimer)
		WM_event_remove_window_timer(win, screen->animtimer);
	screen->animtimer= NULL;
	
	if(enable)
		screen->animtimer= WM_event_add_window_timer(win, TIMER0, (1.0/FPS));
}

unsigned int ED_screen_view3d_layers(bScreen *screen)
{
	if(screen) {
		unsigned int layer= screen->scene->lay;	/* as minimum this */
		ScrArea *sa;
		
		/* get all used view3d layers */
		for(sa= screen->areabase.first; sa; sa= sa->next) {
			if(sa->spacetype==SPACE_VIEW3D)
				layer |= ((View3D *)sa->spacedata.first)->lay;
		}
		return layer;
	}
	return 0;
}


/* results in fully updated anim system */
/* in future sound should be on WM level, only 1 sound can play! */
void ED_update_for_newframe(const bContext *C, int mute)
{
	bScreen *screen= CTX_wm_screen(C);
	Scene *scene= screen->scene;
	
	//extern void audiostream_scrub(unsigned int frame);	/* seqaudio.c */
	
	/* this function applies the changes too */
	/* XXX future: do all windows */
	scene_update_for_newframe(scene, ED_screen_view3d_layers(screen)); /* BKE_scene.h */
	
	//if ( (CFRA>1) && (!mute) && (scene->audio.flag & AUDIO_SCRUB)) 
	//	audiostream_scrub( CFRA );
	
	/* 3d window, preview */
	//BIF_view3d_previewrender_signal(curarea, PR_DBASE|PR_DISPRECT);
	
	/* all movie/sequence images */
	//BIF_image_update_frame();
	
	/* composite */
	if(scene->use_nodes && scene->nodetree)
		ntreeCompositTagAnimated(scene->nodetree);
	
	/* update animated texture nodes */
	{
		Tex *tex;
		for(tex= CTX_data_main(C)->tex.first; tex; tex= tex->id.next)
			if( tex->use_nodes && tex->nodetree ) {
				ntreeTexTagAnimated( tex->nodetree );
			}
	}
}


