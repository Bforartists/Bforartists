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
 * (uit traces) maart 95
 */

#include <stdio.h>
#include <math.h>
#include <stdlib.h>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"

#include "BLI_util.h"
#include "DNA_listBase.h"
#include "BLI_editVert.h"
#include "BLI_arithb.h"
#include "BLI_scanfill.h"
#include "BLI_callbacks.h"

/* callbacks for errors and interrupts and some goo */
static void (*BLI_localErrorCallBack)(char*) = NULL;
static int (*BLI_localInterruptCallBack)(void) = NULL;
static void *objectref = NULL;
static char *colourref = NULL;


void BLI_setScanFillObjectRef(void* ob)
{
	objectref = ob;
}

void BLI_setScanFillColourRef(char* c)
{
	colourref = c;
}

void BLI_setErrorCallBack(void (*f)(char*))
{
	BLI_localErrorCallBack = f;
}

void BLI_setInterruptCallBack(int (*f)(void))
{
	BLI_localInterruptCallBack = f;
}

/* just flush the error to /dev/null if the error handler is missing */
void callLocalErrorCallBack(char* msg)
{
	if (BLI_localErrorCallBack) {
		BLI_localErrorCallBack(msg);
	}
}

/* ignore if the interrupt wasn't set */
int callLocalInterruptCallBack(void)
{
	if (BLI_localInterruptCallBack) {
		return BLI_localInterruptCallBack();
	} else {
		return 0;
	}
}


/* local types */
typedef struct PolyFill {
	int edges,verts;
	float min[3],max[3];
	short f,nr;
} PolyFill;

typedef struct ScFillVert {
	EditVert *v1;
	EditEdge *first,*last;
	short f,f1;
} ScFillVert;


/* local funcs */
int vergscdata(const void *a1, const void *a2);
int vergpoly(const void *a1, const void *a2);
void *new_mem_element(int size);
void addfillvlak(EditVert *v1, EditVert *v2, EditVert *v3);
int boundinside(PolyFill *pf1, PolyFill *pf2);
int boundisect(PolyFill *pf2, PolyFill *pf1);
void mergepolysSimp(PolyFill *pf1, PolyFill *pf2)	/* pf2 bij pf1 */;
EditEdge *existfilledge(EditVert *v1, EditVert *v2);
short addedgetoscanvert(ScFillVert *sc, EditEdge *eed);
short testedgeside(float *v1, float *v2, float *v3);
short testedgeside2(float *v1, float *v2, float *v3);
short boundinsideEV(EditEdge *eed, EditVert *eve)	/* is eve binnen boundbox eed */;
void testvertexnearedge(void);
void scanfill(PolyFill *pf);
void fill_mesh(void);
ScFillVert *addedgetoscanlist(EditEdge *eed, int len);
void splitlist(ListBase *tempve, ListBase *temped, short nr);

/* This one is also used in isect.c Keep it here until we know what to do with isect.c */
#define COMPLIMIT	0.0003

ScFillVert *scdata;

ListBase fillvertbase = {0,0};
ListBase filledgebase = {0,0};
ListBase fillvlakbase = {0,0};

short cox, coy;

/* ****  FUNKTIES VOOR QSORT *************************** */


int vergscdata(const void *a1, const void *a2)
{
	const ScFillVert *x1=a1,*x2=a2;
	
	if( x1->v1->co[coy] < x2->v1->co[coy] ) return 1;
	else if( x1->v1->co[coy] > x2->v1->co[coy]) return -1;
	else if( x1->v1->co[cox] > x2->v1->co[cox] ) return 1;
	else if( x1->v1->co[cox] < x2->v1->co[cox]) return -1;

	return 0;
}

int vergpoly(const void *a1, const void *a2)
{
	const PolyFill *x1=a1, *x2=a2;

	if( x1->min[cox] > x2->min[cox] ) return 1;
	else if( x1->min[cox] < x2->min[cox] ) return -1;
	else if( x1->min[coy] > x2->min[coy] ) return 1;
	else if( x1->min[coy] < x2->min[coy] ) return -1;
	
	return 0;
}

/* ************* MEMORY MANAGEMENT ************* */

struct mem_elements {
	struct mem_elements *next, *prev;
	char *data;
};

void *new_mem_element(int size)
{
	/* Alleen als gedurende het werken duizenden elementen worden aangemaakt en
	 * nooit (tussendoor) vrijgegeven. Op eind is vrijgeven nodig (-1).
	 */
	int blocksize= 16384;
	static int offs= 0;		/* het huidige vrije adres */
	static struct mem_elements *cur= 0;
	static ListBase lb= {0, 0};
	void *adr;
	
	if(size>10000 || size==0) {
		printf("incorrect use of new_mem_element\n");
	}
	else if(size== -1) {
		cur= lb.first;
		while(cur) {
			MEM_freeN(cur->data);
			cur= cur->next;
		}
		BLI_freelistN(&lb);
		
		return NULL;	
	}
	
	size= 4*( (size+3)/4 );
	
	if(cur) {
		if(size+offs < blocksize) {
			adr= (void *) (cur->data+offs);
		 	offs+= size;
			return adr;
		}
	}
	
	cur= MEM_callocN( sizeof(struct mem_elements), "newmem");
	cur->data= MEM_callocN(blocksize, "newmem");
	BLI_addtail(&lb, cur);
	
	offs= size;
	return cur->data;
}

void BLI_end_edgefill(void)
{
	new_mem_element(-1);
	
	fillvertbase.first= fillvertbase.last= 0;
	filledgebase.first= filledgebase.last= 0;
	fillvlakbase.first= fillvlakbase.last= 0;
}

/* ****  FILL ROUTINES *************************** */

EditVert *BLI_addfillvert(float *vec)
{
	EditVert *eve;
	
	eve= new_mem_element(sizeof(EditVert));
	BLI_addtail(&fillvertbase, eve);
	
	if(vec) {
		*(eve->co)     = *(vec);
		*(eve->co + 1) = *(vec + 1);
		*(eve->co + 2) = *(vec + 2);
	}
/*  	VECCOPY(eve->co, vec); */

	return eve;	
}

EditEdge *BLI_addfilledge(EditVert *v1, EditVert *v2)
{
	EditEdge *newed;

	newed= new_mem_element(sizeof(EditEdge));
	BLI_addtail(&filledgebase, newed);
	
	newed->v1= v1;
	newed->v2= v2;

	return newed;
}

void addfillvlak(EditVert *v1, EditVert *v2, EditVert *v3)
{
	/* maakt geen edges aan */
	EditVlak *evl;

	evl= new_mem_element(sizeof(EditVlak));
	BLI_addtail(&fillvlakbase, evl);
	
	evl->v1= v1;
	evl->v2= v2;
	evl->v3= v3;
	evl->f= 2;
	/* G.obedit is Object*, actcol is char */
/*  	if(G.obedit && G.obedit->actcol) evl->mat_nr= G.obedit->actcol-1; */
	if (objectref && colourref && *colourref) {
		evl->mat_nr = *colourref - 1;
	} else {
		evl->mat_nr = 0;
	}
}


int boundinside(PolyFill *pf1, PolyFill *pf2)
{
	/* is pf2 INSIDE pf1 ? met boundingbox */
	/* eerst testen of poly's bestaan */

	if(pf1->edges==0 || pf2->edges==0) return 0;

	if(pf2->max[cox]<pf1->max[cox])
		if(pf2->max[coy]<pf1->max[coy])
			if(pf2->min[cox]>pf1->min[cox])
				if(pf2->min[coy]>pf1->min[coy]) return 1;
	return 0;
}

int boundisect(PolyFill *pf2, PolyFill *pf1)
{
	/* is pf2 aangeraakt door pf1 ? met boundingbox */
	/* eerst testen of poly's bestaan */

	if(pf1->edges==0 || pf2->edges==0) return 0;

	if(pf2->max[cox] < pf1->min[cox] ) return 0;
	if(pf2->max[coy] < pf1->min[coy] ) return 0;

	if(pf2->min[cox] > pf1->max[cox] ) return 0;
	if(pf2->min[coy] > pf1->max[coy] ) return 0;

	/* samenvoegen */
	if(pf2->max[cox]<pf1->max[cox]) pf2->max[cox]= pf1->max[cox];
	if(pf2->max[coy]<pf1->max[coy]) pf2->max[coy]= pf1->max[coy];

	if(pf2->min[cox]>pf1->min[cox]) pf2->min[cox]= pf1->min[cox];
	if(pf2->min[coy]>pf1->min[coy]) pf2->min[coy]= pf1->min[coy];

	return 1;
}





void mergepolysSimp(PolyFill *pf1, PolyFill *pf2)	/* pf2 bij pf1 */
/*  PolyFill *pf1,*pf2; */
{
	EditVert *eve;
	EditEdge *eed;

	/* alle oude polynummers vervangen */
	eve= fillvertbase.first;
	while(eve) {
		if(eve->xs== pf2->nr) eve->xs= pf1->nr;
		eve= eve->next;
	}
	eed= filledgebase.first;
	while(eed) {
		if(eed->f1== pf2->nr) eed->f1= pf1->nr;
		eed= eed->next;
	}

	pf1->verts+= pf2->verts;
	pf1->edges+= pf2->edges;
	pf2->verts= pf2->edges= 0;
	pf1->f= (pf1->f | pf2->f);
}



EditEdge *existfilledge(EditVert *v1, EditVert *v2)
/*  EditVert *v1,*v2; */
{
	EditEdge *eed;

	eed= filledgebase.first;
	while(eed) {
		if(eed->v1==v1 && eed->v2==v2) return eed;
		if(eed->v2==v1 && eed->v1==v2) return eed;
		eed= eed->next;
	}
	return 0;
}


short testedgeside(float *v1, float *v2, float *v3) /* is v3 rechts van v1-v2 ? Met uizondering: v3==v1 || v3==v2*/
/*  float *v1,*v2,*v3; */
{
	float inp;

	inp= (v2[cox]-v1[cox])*(v1[coy]-v3[coy])
	    +(v1[coy]-v2[coy])*(v1[cox]-v3[cox]);

	if(inp<0.0) return 0;
	else if(inp==0) {
		if(v1[cox]==v3[cox] && v1[coy]==v3[coy]) return 0;
		if(v2[cox]==v3[cox] && v2[coy]==v3[coy]) return 0;
	}
	return 1;
}

short testedgeside2(float *v1, float *v2, float *v3) /* is v3 rechts van v1-v2 ? niet doorsnijden! */
/*  float *v1,*v2,*v3; */
{
	float inp;

	inp= (v2[cox]-v1[cox])*(v1[coy]-v3[coy])
	    +(v1[coy]-v2[coy])*(v1[cox]-v3[cox]);

	if(inp<=0.0) return 0;
	return 1;
}

short addedgetoscanvert(ScFillVert *sc, EditEdge *eed)
/*  ScFillVert *sc; */
/*  EditEdge *eed; */
{
	/* zoek eerste edge die rechts van eed ligt en stop eed daarvoor */
	EditEdge *ed;
	float fac,fac1,x,y;

	if(sc->first==0) {
		sc->first= sc->last= eed;
		eed->prev= eed->next=0;
		return 1;
	}

	x= eed->v1->co[cox];
	y= eed->v1->co[coy];

	fac1= eed->v2->co[coy]-y;
	if(fac1==0.0) {
		fac1= 1.0e10*(eed->v2->co[cox]-x);

	}
	else fac1= (x-eed->v2->co[cox])/fac1;

	ed= sc->first;
	while(ed) {

		if(ed->v2==eed->v2) return 0;

		fac= ed->v2->co[coy]-y;
		if(fac==0.0) {
			fac= 1.0e10*(ed->v2->co[cox]-x);

		}
		else fac= (x-ed->v2->co[cox])/fac;
		if(fac>fac1) break;

		ed= ed->next;
	}
	if(ed) BLI_insertlinkbefore((ListBase *)&(sc->first), ed, eed);
	else BLI_addtail((ListBase *)&(sc->first),eed);

	return 1;
}


ScFillVert *addedgetoscanlist(EditEdge *eed, int len)
/*  EditEdge *eed; */
/*  int len; */
{
	/* voegt edge op juiste plek in ScFillVert list */
	/* geeft sc terug als edge al bestaat */
	ScFillVert *sc,scsearch;
	EditVert *eve;

	/* welke vert is linksboven */
	if(eed->v1->co[coy] == eed->v2->co[coy]) {
		if(eed->v1->co[cox] > eed->v2->co[cox]) {
			eve= eed->v1;
			eed->v1= eed->v2;
			eed->v2= eve;
		}
	}
	else if(eed->v1->co[coy] < eed->v2->co[coy]) {
		eve= eed->v1;
		eed->v1= eed->v2;
		eed->v2= eve;
	}
	/* zoek plek in lijst */
	scsearch.v1= eed->v1;
	sc= (ScFillVert *)bsearch(&scsearch,scdata,len,
	    sizeof(ScFillVert), vergscdata);

	if(sc==0) printf("Error in search edge: %x\n",eed);
	else if(addedgetoscanvert(sc,eed)==0) return sc;

	return 0;
}

short boundinsideEV(EditEdge *eed, EditVert *eve)	/* is eve binnen boundbox eed */
/*  EditEdge *eed; */
/*  EditVert *eve; */
{
	float minx,maxx,miny,maxy;

	if(eed->v1->co[cox]<eed->v2->co[cox]) {
		minx= eed->v1->co[cox];
		maxx= eed->v2->co[cox];
	} else {
		minx= eed->v2->co[cox];
		maxx= eed->v1->co[cox];
	}
	if(eve->co[cox]>=minx && eve->co[cox]<=maxx) {
		if(eed->v1->co[coy]<eed->v2->co[coy]) {
			miny= eed->v1->co[coy];
			maxy= eed->v2->co[coy];
		} else {
			miny= eed->v2->co[coy];
			maxy= eed->v1->co[coy];
		}
		if(eve->co[coy]>=miny && eve->co[coy]<=maxy) return 1;
	}
	return 0;
}


void testvertexnearedge(void)
{
	/* alleen de vertices met ->h==1 worden getest op
		nabijheid van edge, zo ja invoegen */

	EditVert *eve;
	EditEdge *eed,*ed1;
	float dist,vec1[2],vec2[2],vec3[2];

	eve= fillvertbase.first;
	while(eve) {
		if(eve->h==1) {
			vec3[0]= eve->co[cox];
			vec3[1]= eve->co[coy];
			/* de bewuste edge vinden waar eve aan zit */
			ed1= filledgebase.first;
			while(ed1) {
				if(ed1->v1==eve || ed1->v2==eve) break;
				ed1= ed1->next;
			}
			if(ed1->v1==eve) {
				ed1->v1= ed1->v2;
				ed1->v2= eve;
			}
			eed= filledgebase.first;
			while(eed) {
				if(eve!=eed->v1 && eve!=eed->v2 && eve->xs==eed->f1) {
					if(FloatCompare(eve->co,eed->v1->co, COMPLIMIT)) {
						ed1->v2= eed->v1;
						eed->v1->h++;
						eve->h= 0;
						break;
					}
					else if(FloatCompare(eve->co,eed->v2->co, COMPLIMIT)) {
						ed1->v2= eed->v2;
						eed->v2->h++;
						eve->h= 0;
						break;
					}
					else {
						vec1[0]= eed->v1->co[cox];
						vec1[1]= eed->v1->co[coy];
						vec2[0]= eed->v2->co[cox];
						vec2[1]= eed->v2->co[coy];
						if(boundinsideEV(eed,eve)) {
							dist= DistVL2Dfl(vec1,vec2,vec3);
							if(dist<COMPLIMIT) {
								/* nieuwe edge */
								ed1= BLI_addfilledge(eed->v1, eve);
								
								/* printf("fill: vertex near edge %x\n",eve); */
								ed1->f= ed1->h= 0;
								ed1->f1= eed->f1;
								eed->v1= eve;
								eve->h= 3;
								break;
							}
						}
					}
				}
				eed= eed->next;
			}
		}
		eve= eve->next;
	}
}

void splitlist(ListBase *tempve, ListBase *temped, short nr)
/*  ListBase *tempve,*temped; */
/*  short nr; */
{
	/* alles zit in de templist, alleen poly nr naar fillist schrijven */
	EditVert *eve,*nextve;
	EditEdge *eed,*nexted;

	addlisttolist(tempve,&fillvertbase);
	addlisttolist(temped,&filledgebase);

	eve= tempve->first;
	while(eve) {
		nextve= eve->next;
		if(eve->xs==nr) {
			BLI_remlink(tempve,eve);
			BLI_addtail(&fillvertbase,eve);
		}
		eve= nextve;
	}
	eed= temped->first;
	while(eed) {
		nexted= eed->next;
		if(eed->f1==nr) {
			BLI_remlink(temped,eed);
			BLI_addtail(&filledgebase,eed);
		}
		eed= nexted;
	}
}


void scanfill(PolyFill *pf)
{
	ScFillVert *sc = NULL, *sc1;
	EditVert *eve,*v1,*v2,*v3;
	EditEdge *eed,*nexted,*ed1,*ed2,*ed3;
	float miny = 0.0;
	int a,b,verts, maxvlak, totvlak;
	short nr, test, twoconnected=0;

	nr= pf->nr;
	verts= pf->verts;

	/* PRINTS
	eve= fillvertbase.first;
	while(eve) {
		printf("vert: %x co: %f %f\n",eve,eve->co[cox],eve->co[coy]);
		eve= eve->next;
	}	
	eed= filledgebase.first;
	while(eed) {
		printf("edge: %x  verts: %x %x\n",eed,eed->v1,eed->v2);
		eed= eed->next;
	} */

	/* STAP 0: alle nul lange edges eruit */
	eed= filledgebase.first;
	while(eed) {
		if(eed->v1->co[cox]==eed->v2->co[cox]) {
			if(eed->v1->co[coy]==eed->v2->co[coy]) {
				if(eed->v1->f==255 && eed->v2->f!=255) {
					eed->v2->f= 255;
					eed->v2->vn= eed->v1->vn;
				}
				else if(eed->v2->f==255 && eed->v1->f!=255) {
					eed->v1->f= 255;
					eed->v1->vn= eed->v2->vn;
				}
				else if(eed->v2->f==255 && eed->v1->f==255) {
					eed->v1->vn= eed->v2->vn;
				}
				else {
					eed->v2->f= 255;
					eed->v2->vn= eed->v1;
				}
			}
		}
		eed= eed->next;
	}

	/* STAP 1: maak ahv van FillVert en FillEdge lijsten een gesorteerde
		ScFillVert lijst
	*/
	sc= scdata= (ScFillVert *)MEM_callocN(pf->verts*sizeof(ScFillVert),"Scanfill1");
	eve= fillvertbase.first;
	verts= 0;
	while(eve) {
		if(eve->xs==nr) {
			if(eve->f!= 255) {
				verts++;
				eve->f= 0;	/* vlag later voor connectedges */
				sc->v1= eve;
				sc++;
			}
		}
		eve= eve->next;
	}

	qsort(scdata, verts, sizeof(ScFillVert), vergscdata);

	sc= scdata;
	eed= filledgebase.first;
	while(eed) {
		nexted= eed->next;
		eed->f= 0;
		BLI_remlink(&filledgebase,eed);
		if(eed->v1->f==255) {
			v1= eed->v1;
			while(eed->v1->f==255 && eed->v1->vn!=v1) eed->v1= eed->v1->vn;
		}
		if(eed->v2->f==255) {
			v2= eed->v2;
			while(eed->v2->f==255 && eed->v2->vn!=v2) eed->v2= eed->v2->vn;
		}
		if(eed->v1!=eed->v2) addedgetoscanlist(eed,verts);

		eed= nexted;
	}
	/*
	sc= scdata;
	for(a=0;a<verts;a++) {
		printf("\nscvert: %x\n",sc->v1);
		eed= sc->first;
		while(eed) {
			printf(" ed %x %x %x\n",eed,eed->v1,eed->v2);
			eed= eed->next;
		}
		sc++;
	}*/


	/* STAP 2: FILL LUS */

	if(pf->f==0) twoconnected= 1;

	/* (tijdelijke) beveiliging: nooit veel meer vlakken dan vertices */
	totvlak= 0;
	maxvlak= 2*verts;		/* 2*verts: cirkel in driehoek, beide gevuld */

	sc= scdata;
	for(a=0;a<verts;a++) {
		/* printf("VERTEX %d %x\n",a,sc->v1); */
		ed1= sc->first;
		while(ed1) {	/* connectflags zetten */
			nexted= ed1->next;
			if(ed1->v1->h==1 || ed1->v2->h==1) {
				BLI_remlink((ListBase *)&(sc->first),ed1);
				BLI_addtail(&filledgebase,ed1);
				if(ed1->v1->h>1) ed1->v1->h--;
				if(ed1->v2->h>1) ed1->v2->h--;
			}
			else ed1->v2->f= 1;

			ed1= nexted;
		}
		while(sc->first) {	/* zolang er edges zijn */
			ed1= sc->first;
			ed2= ed1->next;

			if(callLocalInterruptCallBack()) break;
			if(totvlak>maxvlak) {
				/* printf("Fill error: endless loop. Escaped at vert %d,  tot: %d.\n", a, verts); */
				a= verts;
				break;
			}
			if(ed2==0) {
				sc->first=sc->last= 0;
				/* printf("maar 1 edge aan vert\n"); */
				BLI_addtail(&filledgebase,ed1);
				ed1->v2->f= 0;
				ed1->v1->h--; 
				ed1->v2->h--;
			} else {
				/* test rest vertices */
				v1= ed1->v2;
				v2= ed1->v1;
				v3= ed2->v2;
				/* hieronder komt voor bij serie overlappende edges */
				if(v1==v2 || v2==v3) break;
				/* printf("test verts %x %x %x\n",v1,v2,v3); */
				miny = ( (v1->co[coy])<(v3->co[coy]) ? (v1->co[coy]) : (v3->co[coy]) );
/*  				miny= MIN2(v1->co[coy],v3->co[coy]); */
				sc1= sc+1;
				test= 0;

				for(b=a+1;b<verts;b++) {
					if(sc1->v1->f==0) {
						if(sc1->v1->co[coy] <= miny) break;

						if(testedgeside(v1->co,v2->co,sc1->v1->co))
							if(testedgeside(v2->co,v3->co,sc1->v1->co))
								if(testedgeside(v3->co,v1->co,sc1->v1->co)) {
									/* punt in driehoek */
								
									test= 1;
									break;
								}
					}
					sc1++;
				}
				if(test) {
					/* nieuwe edge maken en overnieuw beginnen */
					/* printf("add new edge %x %x and start again\n",v2,sc1->v1); */

					ed3= BLI_addfilledge(v2, sc1->v1);
					BLI_remlink(&filledgebase, ed3);
					BLI_insertlinkbefore((ListBase *)&(sc->first), ed2, ed3);
					ed3->v2->f= 1;
					ed3->f= 2;
					ed3->v1->h++; 
					ed3->v2->h++;
				}
				else {
					/* nieuwe driehoek */
					/* printf("add vlak %x %x %x\n",v1,v2,v3); */
					addfillvlak(v1, v2, v3);
					totvlak++;
					BLI_remlink((ListBase *)&(sc->first),ed1);
					BLI_addtail(&filledgebase,ed1);
					ed1->v2->f= 0;
					ed1->v1->h--; 
					ed1->v2->h--;
					/* ed2 mag ook weg als het een oude is */
					if(ed2->f==0 && twoconnected) {
						BLI_remlink((ListBase *)&(sc->first),ed2);
						BLI_addtail(&filledgebase,ed2);
						ed2->v2->f= 0;
						ed2->v1->h--; 
						ed2->v2->h--;
					}

					/* nieuwe edge */
					ed3= BLI_addfilledge(v1, v3);
					BLI_remlink(&filledgebase, ed3);
					ed3->f= 2;
					ed3->v1->h++; 
					ed3->v2->h++;
					
					/* printf("add new edge %x %x\n",v1,v3); */
					sc1= addedgetoscanlist(ed3, verts);
					
					if(sc1) {	/* ed3 bestaat al: verwijderen*/
						/* printf("Edge bestaat al\n"); */
						ed3->v1->h--; 
						ed3->v2->h--;

						if(twoconnected) ed3= sc1->first;
						else ed3= 0;
						while(ed3) {
							if( (ed3->v1==v1 && ed3->v2==v3) || (ed3->v1==v3 && ed3->v2==v1) ) {
								BLI_remlink((ListBase *)&(sc1->first),ed3);
								BLI_addtail(&filledgebase,ed3);
								ed3->v1->h--; 
								ed3->v2->h--;
								break;
							}
							ed3= ed3->next;
						}
					}

				}
			}
			/* test op loze edges */
			ed1= sc->first;
			while(ed1) {
				nexted= ed1->next;
				if(ed1->v1->h<2 || ed1->v2->h<2) {
					BLI_remlink((ListBase *)&(sc->first),ed1);
					BLI_addtail(&filledgebase,ed1);
					if(ed1->v1->h>1) ed1->v1->h--;
					if(ed1->v2->h>1) ed1->v2->h--;
				}

				ed1= nexted;
			}
		}
		sc++;
	}

	MEM_freeN(scdata);
}



int BLI_edgefill(int mode)  /* DE HOOFD FILL ROUTINE */
{
	/*
	  - fill werkt met eigen lijsten, eerst aanmaken dus (geen vlakken)
	  - geef vertices in ->vn de oude pointer mee
	  - alleen xs en ys worden hier niet gebruikt: daar kan je iets in verstoppen
	  - edge flag ->f wordt 2 als het nieuwe edge betreft
	  - mode: & 1 is kruispunten testen, edges maken  (NOG DOEN )
	*/
	ListBase tempve, temped;
	EditVert *eve;
	EditEdge *eed,*nexted;
	PolyFill *pflist,*pf;
	float *minp, *maxp, *v1, *v2, norm[3], len;
	short a,c,poly=0,ok=0,toggle=0;

	/* variabelen resetten*/
	eve= fillvertbase.first;
	while(eve) {
		eve->f= 0;
		eve->xs= 0;
		eve->h= 0;
		eve= eve->next;
	}

	/* eerst de vertices testen op aanwezigheid in edges */
	/* plus flaggen resetten */
	eed= filledgebase.first;
	while(eed) {
		eed->f= eed->f1= eed->h= 0;
		eed->v1->f= 1;
		eed->v2->f= 1;

		eed= eed->next;
	}

	eve= fillvertbase.first;
	while(eve) {
		if(eve->f & 1) {
			ok=1; 
			break;
		}
		eve= eve->next;
	}

	if(ok==0) return 0;

	/* NEW NEW! projektie bepalen: met beste normaal */
	/* pak de eerste drie verschillende verts */
	
	/* DIT STUK IS NOG STEEDS TAMELIJK ZWAK! */
	
	eve= fillvertbase.last;
	len= 0.0;
	v1= eve->co;
	v2= 0;
	eve= fillvertbase.first;
	while(eve) {
		if(v2) {
			if( FloatCompare(v2, eve->co,  0.0003)==0) {
				len= CalcNormFloat(v1, v2, eve->co, norm);
				if(len != 0.0) break;
			}
		}
		else if(FloatCompare(v1, eve->co,  0.0003)==0) {
			v2= eve->co;
		}
		eve= eve->next;
	}

	if(len==0.0) return 0;	/* geen fill mogelijk */

	norm[0]= fabs(norm[0]);
	norm[1]= fabs(norm[1]);
	norm[2]= fabs(norm[2]);
	
	if(norm[2]>=norm[0] && norm[2]>=norm[1]) {
		cox= 0; coy= 1;
	}
	else if(norm[1]>=norm[0] && norm[1]>=norm[2]) {
		cox= 0; coy= 2;
	}
	else {
		cox= 1; coy= 2;
	}

	/* STAP 1: AANTAL POLY'S TELLEN */
	eve= fillvertbase.first;
	while(eve) {
		/* pak eerste vertex zonder polynummer */
		if(eve->xs==0) {
			poly++;
			/* nu een soort select connected */
			ok= 1;
			eve->xs= poly;
			
			while(ok) {
				
				ok= 0;
				toggle++;
				if(toggle & 1) eed= filledgebase.first;
				else eed= filledgebase.last;

				while(eed) {
					if(eed->v1->xs==0 && eed->v2->xs==poly) {
						eed->v1->xs= poly;
						eed->f1= poly;
						ok= 1;
					}
					else if(eed->v2->xs==0 && eed->v1->xs==poly) {
						eed->v2->xs= poly;
						eed->f1= poly;
						ok= 1;
					}
					else if(eed->f1==0) {
						if(eed->v1->xs==poly && eed->v2->xs==poly) {
							eed->f1= poly;
							ok= 1;
						}
					}
					if(toggle & 1) eed= eed->next;
					else eed= eed->prev;
				}
			}
		}
		eve= eve->next;
	}
	/* printf("aantal poly's: %d\n",poly); */

	/* STAP 2: LOSSE EDGES EN SLIERTEN VERWIJDEREN */
	eed= filledgebase.first;
	while(eed) {
		if(eed->v1->h++ >250) break;
		if(eed->v2->h++ >250) break;
		eed= eed->next;
	}
	if(eed) {
		/* anders kan hierna niet met zekerheid vertices worden gewist */
		callLocalErrorCallBack("No vertices with 250 edges allowed!");
		return 0;
	}
	
	/* doet alleen vertices met ->h==1 */
	testvertexnearedge();

	ok= 1;
	while(ok) {
		ok= 0;
		toggle++;
		if(toggle & 1) eed= filledgebase.first;
		else eed= filledgebase.last;
		while(eed) {
			if(toggle & 1) nexted= eed->next;
			else nexted= eed->prev;
			if(eed->v1->h==1) {
				eed->v2->h--;
				BLI_remlink(&fillvertbase,eed->v1); 
				BLI_remlink(&filledgebase,eed); 
				ok= 1;
			}
			else if(eed->v2->h==1) {
				eed->v1->h--;
				BLI_remlink(&fillvertbase,eed->v2); 
				BLI_remlink(&filledgebase,eed); 
				ok= 1;
			}
			eed= nexted;
		}
	}
	if(filledgebase.first==0) {
		/* printf("All edges removed\n"); */
		return 0;
	}


	/* STAND VAN ZAKEN:
	- eve->f  :1= aanwezig in edges
	- eve->xs :polynummer
	- eve->h  :aantal edges aan vertex
	- eve->vn :bewaren! oorspronkelijke vertexnummer

	- eed->f  :
	- eed->f1 :polynummer
*/


	/* STAP 3: POLYFILL STRUCT MAKEN */
	pflist= (PolyFill *)MEM_callocN(poly*sizeof(PolyFill),"edgefill");
	pf= pflist;
	for(a=1;a<=poly;a++) {
		pf->nr= a;
		pf->min[0]=pf->min[1]=pf->min[2]= 1.0e20;
		pf->max[0]=pf->max[1]=pf->max[2]= -1.0e20;
		pf++;
	}
	eed= filledgebase.first;
	while(eed) {
		pflist[eed->f1-1].edges++;
		eed= eed->next;
	}

	eve= fillvertbase.first;
	while(eve) {
		pflist[eve->xs-1].verts++;
		minp= pflist[eve->xs-1].min;
		maxp= pflist[eve->xs-1].max;

		minp[cox]= (minp[cox])<(eve->co[cox]) ? (minp[cox]) : (eve->co[cox]);
		minp[coy]= (minp[coy])<(eve->co[coy]) ? (minp[coy]) : (eve->co[coy]);
		maxp[cox]= (maxp[cox])>(eve->co[cox]) ? (maxp[cox]) : (eve->co[cox]);
		maxp[coy]= (maxp[coy])>(eve->co[coy]) ? (maxp[coy]) : (eve->co[coy]);
		if(eve->h>2) pflist[eve->xs-1].f= 1;

		eve= eve->next;
	}

	/* STAP 4: GATEN OF BOUNDS VINDEN EN SAMENVOEGEN
	 *  ( bounds alleen om grote hoeveelheden een beetje in stukjes te verdelen, 
	 *    de edgefill heeft van zichzelf een adequate autogat!!!
	 * LET OP: WERKT ALLEEN ALS POLY'S GESORTEERD ZIJN!!! */
	
	if(poly>1) {
		short *polycache, *pc;

		/* dus: eerst sorteren */
		qsort(pflist, poly, sizeof(PolyFill), vergpoly);
		
		/*pf= pflist;
		for(a=1;a<=poly;a++) {
			printf("poly:%d edges:%d verts:%d flag: %d\n",a,pf->edges,pf->verts,pf->f);
			PRINT2(f, f, pf->min[0], pf->min[1]);
			pf++;
		}*/
	
		polycache= pc= MEM_callocN(sizeof(short)*poly, "polycache");
		pf= pflist;
		for(a=0; a<poly; a++, pf++) {
			for(c=a+1;c<poly;c++) {
				
				/* als 'a' inside 'c': samenvoegen (ook bbox)
				 * Pas Op: 'a' kan ook inside andere poly zijn.
				 */
				if(boundisect(pf, pflist+c)) {
					*pc= c;
					pc++;
				}
				/* alleen voor opt! */
				/* else if(pf->max[cox] < (pflist+c)->min[cox]) break; */
				
			}
			while(pc!=polycache) {
				pc--;
				mergepolysSimp(pf, pflist+ *pc);
			}
		}
		MEM_freeN(polycache);
	}
	
	pf= pflist;
	/* printf("na merge\n");
	for(a=1;a<=poly;a++) {
		printf("poly:%d edges:%d verts:%d flag: %d\n",a,pf->edges,pf->verts,pf->f);
		pf++;
	} */

	/* STAP 5: DRIEHOEKEN MAKEN */

	tempve.first= fillvertbase.first;
	tempve.last= fillvertbase.last;
	temped.first= filledgebase.first;
	temped.last= filledgebase.last;
	fillvertbase.first=fillvertbase.last= 0;
	filledgebase.first=filledgebase.last= 0;

	pf= pflist;
	for(a=0;a<poly;a++) {
		if(pf->edges>1) {
			splitlist(&tempve,&temped,pf->nr);
			scanfill(pf);
		}
		pf++;
	}
	addlisttolist(&fillvertbase,&tempve);
	addlisttolist(&filledgebase,&temped);

	/* evl= fillvlakbase.first;	
	while(evl) {
		printf("nieuw vlak %x %x %x\n",evl->v1,evl->v2,evl->v3);
		evl= evl->next;
	}*/


	/*  VRIJGEVEN */

	MEM_freeN(pflist);
	return 1;

}

/*
  MOVED TO EDITMESH.C since it's really bad to leave it here
  
void fill_mesh(void)
{
	EditVert *eve,*v1;
	EditEdge *eed,*e1,*nexted;
	EditVlak *evl,*nextvl;
	short ok;

	if(G.obedit==0 || (G.obedit->type!=OB_MESH)) return;

	waitcursor(1);

	/ * alle selected vertices kopieeren * /
	eve= G.edve.first;
	while(eve) {
		if(eve->f & 1) {
			v1= addfillvert(eve->co);
			eve->vn= v1;
			v1->vn= eve;
			v1->h= 0;
		}
		eve= eve->next;
	}
	/ * alle selected edges kopieeren * /
	eed= G.eded.first;
	while(eed) {
		if( (eed->v1->f & 1) && (eed->v2->f & 1) ) {
			e1= addfilledge(eed->v1->vn, eed->v2->vn);
			e1->v1->h++; 
			e1->v2->h++;
		}
		eed= eed->next;
	}
	/ * van alle selected vlakken vertices en edges verwijderen om dubbels te voorkomen * /
	/ * alle edges tellen punten op, vlakken trekken af,
	   edges met vertices ->h<2 verwijderen * /
	evl= G.edvl.first;
	ok= 0;
	while(evl) {
		nextvl= evl->next;
		if( vlakselectedAND(evl, 1) ) {
			evl->v1->vn->h--;
			evl->v2->vn->h--;
			evl->v3->vn->h--;
			if(evl->v4) evl->v4->vn->h--;
			ok= 1;
			
		}
		evl= nextvl;
	}
	if(ok) {	/ * er zijn vlakken geselecteerd * /
		eed= filledgebase.first;
		while(eed) {
			nexted= eed->next;
			if(eed->v1->h<2 || eed->v2->h<2) {
				remlink(&filledgebase,eed);
			}
			eed= nexted;
		}
	}

	/ * tijd=clock(); * /

	ok= edgefill(0);

	/ * printf("time: %d\n",(clock()-tijd)/1000); * /

	if(ok) {
		evl= fillvlakbase.first;
		while(evl) {
			addvlaklist(evl->v1->vn, evl->v2->vn, evl->v3->vn, 0, evl);
			evl= evl->next;
		}
	}
	/ * else printf("fill error\n"); * /

	end_edgefill();

	waitcursor(0);

	countall();
	allqueue(REDRAWVIEW3D, 0);
}

MOVED TO editmesh.c !!!!! (you bastards!)

 */
