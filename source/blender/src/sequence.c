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

#include <string.h>
#include <math.h>
#include <stdlib.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifdef WIN32
#include "BLI_winstuff.h"
#endif

#include "MEM_guardedalloc.h"
#include "PIL_dynlib.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "DNA_ipo_types.h"
#include "DNA_sequence_types.h"
#include "DNA_view3d_types.h"

#include "BKE_utildefines.h"
#include "BKE_plugin_types.h"
#include "BKE_global.h"
#include "BKE_texture.h"
#include "BKE_image.h"
#include "BKE_main.h"
#include "BKE_scene.h"
#include "BKE_ipo.h"

#include "BSE_filesel.h"
#include "BIF_interface.h"
#include "BSE_headerbuttons.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_toolbox.h"

#include "BSE_sequence.h"

#include "blendef.h"
#include "render.h"

Sequence *seq_arr[MAXSEQ+1];
int seqrectx, seqrecty;

/* support for plugin sequences: */

void open_plugin_seq(PluginSeq *pis, char *seqname)
{
	int (*version)();
	char *cp;

	/* to be sure: (is tested for) */
	pis->doit= 0;
	pis->pname= 0;
	pis->varstr= 0;
	pis->cfra= 0;
	pis->version= 0;

	/* clear the error list */
	PIL_dynlib_get_error_as_string(NULL);

	/* if(pis->handle) PIL_dynlib_close(pis->handle); */
	/* pis->handle= 0; */

	/* open the needed object */
	pis->handle= PIL_dynlib_open(pis->name);
	if(test_dlerr(pis->name, pis->name)) return;

	if (pis->handle != 0) {
		/* find the address of the version function */
		version= (int (*)())PIL_dynlib_find_symbol(pis->handle, "plugin_seq_getversion");
		if (test_dlerr(pis->name, "plugin_seq_getversion")) return;

		if (version != 0) {
			pis->version= version();
			if (pis->version==2 || pis->version==3) {
				int (*info_func)(PluginInfo *);
				PluginInfo *info= (PluginInfo*) MEM_mallocN(sizeof(PluginInfo), "plugin_info");;

				info_func= (int (*)(PluginInfo *))PIL_dynlib_find_symbol(pis->handle, "plugin_getinfo");

				if(info_func == NULL) error("No info func");
				else {
					info_func(info);

					pis->pname= info->name;
					pis->vars= info->nvars;
					pis->cfra= info->cfra;

					pis->varstr= info->varstr;

					pis->doit= (void(*)(void))info->seq_doit;
					if (info->init)
						info->init();
				}
				MEM_freeN(info);

				cp= PIL_dynlib_find_symbol(pis->handle, "seqname");
				if(cp) strcpy(cp, seqname);
			} else {
				printf ("Plugin returned unrecognized version number\n");
				return;
			}
		}
	}
}

PluginSeq *add_plugin_seq(char *str, char *seqname)
{
	PluginSeq *pis;
	VarStruct *varstr;
	int a;

	pis= MEM_callocN(sizeof(PluginSeq), "PluginSeq");

	strcpy(pis->name, str);
	open_plugin_seq(pis, seqname);

	if(pis->doit==0) {
		if(pis->handle==0) error("no plugin: %s", str);
		else error("in plugin: %s", str);
		MEM_freeN(pis);
		return 0;
	}

	/* default values */
	varstr= pis->varstr;
	for(a=0; a<pis->vars; a++, varstr++) {
		if( (varstr->type & FLO)==FLO)
			pis->data[a]= varstr->def;
		else if( (varstr->type & INT)==INT)
			*((int *)(pis->data+a))= (int) varstr->def;
	}

	return pis;
}

void free_plugin_seq(PluginSeq *pis)
{

	if(pis==0) return;

	/* no PIL_dynlib_close: same plugin can be opened multiple times with 1 handle */
	MEM_freeN(pis);
}

/* ***************** END PLUGIN ************************ */

void free_stripdata(int len, StripElem *se)
{
	StripElem *seo;
	int a;

	seo= se;

	for(a=0; a<len; a++, se++) {
		if(se->ibuf && se->ok!=2) IMB_freeImBuf(se->ibuf);
	}

	MEM_freeN(seo);

}

void free_strip(Strip *strip)
{
	strip->us--;
	if(strip->us>0) return;
	if(strip->us<0) {
		printf("error: negative users in strip\n");
		return;
	}

	if(strip->stripdata) {
		free_stripdata(strip->len, strip->stripdata);
	}
	MEM_freeN(strip);
}

void new_stripdata(Sequence *seq)
{

	if(seq->strip) {
		if(seq->strip->stripdata) free_stripdata(seq->strip->len, seq->strip->stripdata);
		seq->strip->stripdata= 0;
		seq->strip->len= seq->len;
		if(seq->len>0) seq->strip->stripdata= MEM_callocN(seq->len*sizeof(StripElem), "stripelems");
	}
}

void free_sequence(Sequence *seq)
{
	extern Sequence *last_seq;

	if(seq->strip) free_strip(seq->strip);
	if(seq->effectdata) MEM_freeN(seq->effectdata);

	if(seq->anim) IMB_free_anim(seq->anim);

	free_plugin_seq(seq->plugin);

	if(seq==last_seq) last_seq= 0;

	MEM_freeN(seq);
}

void do_seq_count(ListBase *seqbase, int *totseq)
{
	Sequence *seq;

	seq= seqbase->first;
	while(seq) {
		(*totseq)++;
		if(seq->seqbase.first) do_seq_count(&seq->seqbase, totseq);
		seq= seq->next;
	}
}

void do_build_seqar(ListBase *seqbase, Sequence ***seqar, int depth)
{
	Sequence *seq;

	seq= seqbase->first;
	while(seq) {
		seq->depth= depth;
		if(seq->seqbase.first) do_build_seqar(&seq->seqbase, seqar, depth+1);
		**seqar= seq;
		(*seqar)++;
		seq= seq->next;
	}
}

void build_seqar(ListBase *seqbase, Sequence  ***seqar, int *totseq)
{
	Sequence **tseqar;

	*totseq= 0;
	do_seq_count(seqbase, totseq);

	if(*totseq==0) {
		*seqar= 0;
		return;
	}
	*seqar= MEM_mallocN(sizeof(void *)* *totseq, "seqar");
	tseqar= *seqar;

	do_build_seqar(seqbase, seqar, 0);
	*seqar= tseqar;
}

void free_editing(Editing *ed)
{
	MetaStack *ms;
	Sequence *seq;

	if(ed==0) return;

	WHILE_SEQ(&ed->seqbase) {
		free_sequence(seq);
	}
	END_SEQ

	while( (ms= ed->metastack.first) ) {
		BLI_remlink(&ed->metastack, ms);
		MEM_freeN(ms);
	}

	MEM_freeN(ed);
}

void calc_sequence(Sequence *seq)
{
	Sequence *seqm;
	int min, max;

	/* check all metas recursively */
	seqm= seq->seqbase.first;
	while(seqm) {
		if(seqm->seqbase.first) calc_sequence(seqm);
		seqm= seqm->next;
	}

	/* effects and meta: automatic start and end */

	if(seq->type & SEQ_EFFECT) {
		/* pointers */
		if(seq->seq2==0) seq->seq2= seq->seq1;
		if(seq->seq3==0) seq->seq3= seq->seq1;

		/* effecten go from seq1 -> seq2: test */

		/* we take the largest start and smallest end */

		// seq->start= seq->startdisp= MAX2(seq->seq1->startdisp, seq->seq2->startdisp);
		// seq->enddisp= MIN2(seq->seq1->enddisp, seq->seq2->enddisp);

		seq->start= seq->startdisp= MAX3(seq->seq1->startdisp, seq->seq2->startdisp, seq->seq3->startdisp);
		seq->enddisp= MIN3(seq->seq1->enddisp, seq->seq2->enddisp, seq->seq3->enddisp);
		seq->len= seq->enddisp - seq->startdisp;

		if(seq->strip && seq->len!=seq->strip->len) {
			new_stripdata(seq);
		}

	}
	else {
		if(seq->type==SEQ_META) {
			seqm= seq->seqbase.first;
			if(seqm) {
				min= 1000000;
				max= -1000000;
				while(seqm) {
					if(seqm->startdisp < min) min= seqm->startdisp;
					if(seqm->enddisp > max) max= seqm->enddisp;
					seqm= seqm->next;
				}
				seq->start= min;
				seq->len= max-min;

				if(seq->strip && seq->len!=seq->strip->len) {
					new_stripdata(seq);
				}
			}
		}


		if(seq->startofs && seq->startstill) seq->startstill= 0;
		if(seq->endofs && seq->endstill) seq->endstill= 0;

		seq->startdisp= seq->start + seq->startofs - seq->startstill;
		seq->enddisp= seq->start+seq->len - seq->endofs + seq->endstill;

		seq->handsize= 10.0;	/* 10 frames */
		if( seq->enddisp-seq->startdisp < 20 ) {
			seq->handsize= (float)(0.5*(seq->enddisp-seq->startdisp));
		}
		else if(seq->enddisp-seq->startdisp > 250) {
			seq->handsize= (float)((seq->enddisp-seq->startdisp)/25);
		}
	}
}

void sort_seq()
{
	/* all strips together per kind, and in order of y location ("machine") */
	ListBase seqbase, effbase;
	Editing *ed;
	Sequence *seq, *seqt;

	ed= G.scene->ed;
	if(ed==0) return;

	seqbase.first= seqbase.last= 0;
	effbase.first= effbase.last= 0;

	while( (seq= ed->seqbasep->first) ) {
		BLI_remlink(ed->seqbasep, seq);

		if(seq->type & SEQ_EFFECT) {
			seqt= effbase.first;
			while(seqt) {
				if(seqt->machine>=seq->machine) {
					BLI_insertlinkbefore(&effbase, seqt, seq);
					break;
				}
				seqt= seqt->next;
			}
			if(seqt==0) BLI_addtail(&effbase, seq);
		}
		else {
			seqt= seqbase.first;
			while(seqt) {
				if(seqt->machine>=seq->machine) {
					BLI_insertlinkbefore(&seqbase, seqt, seq);
					break;
				}
				seqt= seqt->next;
			}
			if(seqt==0) BLI_addtail(&seqbase, seq);
		}
	}

	addlisttolist(&seqbase, &effbase);
	*(ed->seqbasep)= seqbase;
}


void clear_scene_in_allseqs(Scene *sce)
{
	Scene *sce1;
	Editing *ed;
	Sequence *seq;

	/* when a scene is deleted: test all seqs */

	sce1= G.main->scene.first;
	while(sce1) {
		if(sce1!=sce && sce1->ed) {
			ed= sce1->ed;

			WHILE_SEQ(&ed->seqbase) {

				if(seq->scene==sce) seq->scene= 0;

			}
			END_SEQ
		}

		sce1= sce1->id.next;
	}
}

/* ***************** DO THE SEQUENCE ***************** */

void do_alphaover_effect(float facf0, float facf1, int x, int y, unsigned int *rect1, unsigned int *rect2, unsigned int *out)
{
	int fac2, mfac, fac, fac4;
	int xo, tempc;
	char *rt1, *rt2, *rt;

	xo= x;
	rt1= (char *)rect1;
	rt2= (char *)rect2;
	rt= (char *)out;

	fac2= (int)(256.0*facf0);
	fac4= (int)(256.0*facf1);

	while(y--) {

		x= xo;
		while(x--) {

			/* rt = rt1 over rt2  (alpha from rt1) */

			fac= fac2;
			mfac= 256 - ( (fac2*rt1[3])>>8 );

			if(fac==0) *( (unsigned int *)rt) = *( (unsigned int *)rt2);
			else if(mfac==0) *( (unsigned int *)rt) = *( (unsigned int *)rt1);
			else {
				tempc= ( fac*rt1[0] + mfac*rt2[0])>>8;
				if(tempc>255) rt[0]= 255; else rt[0]= tempc;
				tempc= ( fac*rt1[1] + mfac*rt2[1])>>8;
				if(tempc>255) rt[1]= 255; else rt[1]= tempc;
				tempc= ( fac*rt1[2] + mfac*rt2[2])>>8;
				if(tempc>255) rt[2]= 255; else rt[2]= tempc;
				tempc= ( fac*rt1[3] + mfac*rt2[3])>>8;
				if(tempc>255) rt[3]= 255; else rt[3]= tempc;
			}
			rt1+= 4; rt2+= 4; rt+= 4;
		}

		if(y==0) break;
		y--;

		x= xo;
		while(x--) {

			fac= fac4;
			mfac= 256 - ( (fac4*rt1[3])>>8 );

			if(fac==0) *( (unsigned int *)rt) = *( (unsigned int *)rt2);
			else if(mfac==0) *( (unsigned int *)rt) = *( (unsigned int *)rt1);
			else {
				tempc= ( fac*rt1[0] + mfac*rt2[0])>>8;
				if(tempc>255) rt[0]= 255; else rt[0]= tempc;
				tempc= ( fac*rt1[1] + mfac*rt2[1])>>8;
				if(tempc>255) rt[1]= 255; else rt[1]= tempc;
				tempc= ( fac*rt1[2] + mfac*rt2[2])>>8;
				if(tempc>255) rt[2]= 255; else rt[2]= tempc;
				tempc= ( fac*rt1[3] + mfac*rt2[3])>>8;
				if(tempc>255) rt[3]= 255; else rt[3]= tempc;
			}
			rt1+= 4; rt2+= 4; rt+= 4;
		}
	}
}

void do_alphaunder_effect(float facf0, float facf1, int x, int y, unsigned int *rect1, unsigned int *rect2, unsigned int *out)
{
	int fac2, mfac, fac, fac4;
	int xo;
	char *rt1, *rt2, *rt;

	xo= x;
	rt1= (char *)rect1;
	rt2= (char *)rect2;
	rt= (char *)out;

	fac2= (int)(256.0*facf0);
	fac4= (int)(256.0*facf1);

	while(y--) {

		x= xo;
		while(x--) {

			/* rt = rt1 under rt2  (alpha from rt2) */

			/* this complex optimalisation is because the
			 * 'skybuf' can be crossed in
			 */
			if(rt2[3]==0 && fac2==256) *( (unsigned int *)rt) = *( (unsigned int *)rt1);
			else if(rt2[3]==255) *( (unsigned int *)rt) = *( (unsigned int *)rt2);
			else {
				mfac= rt2[3];
				fac= (fac2*(256-mfac))>>8;

				if(fac==0) *( (unsigned int *)rt) = *( (unsigned int *)rt2);
				else {
					rt[0]= ( fac*rt1[0] + mfac*rt2[0])>>8;
					rt[1]= ( fac*rt1[1] + mfac*rt2[1])>>8;
					rt[2]= ( fac*rt1[2] + mfac*rt2[2])>>8;
					rt[3]= ( fac*rt1[3] + mfac*rt2[3])>>8;
				}
			}
			rt1+= 4; rt2+= 4; rt+= 4;
		}

		if(y==0) break;
		y--;

		x= xo;
		while(x--) {

			if(rt2[3]==0 && fac4==256) *( (unsigned int *)rt) = *( (unsigned int *)rt1);
			else if(rt2[3]==255) *( (unsigned int *)rt) = *( (unsigned int *)rt2);
			else {
				mfac= rt2[3];
				fac= (fac4*(256-mfac))>>8;

				if(fac==0) *( (unsigned int *)rt) = *( (unsigned int *)rt2);
				else {
					rt[0]= ( fac*rt1[0] + mfac*rt2[0])>>8;
					rt[1]= ( fac*rt1[1] + mfac*rt2[1])>>8;
					rt[2]= ( fac*rt1[2] + mfac*rt2[2])>>8;
					rt[3]= ( fac*rt1[3] + mfac*rt2[3])>>8;
				}
			}
			rt1+= 4; rt2+= 4; rt+= 4;
		}
	}
}


void do_cross_effect(float facf0, float facf1, int x, int y, unsigned int *rect1, unsigned int *rect2, unsigned int *out)
{
	int fac1, fac2, fac3, fac4;
	int xo;
	char *rt1, *rt2, *rt;

	xo= x;
	rt1= (char *)rect1;
	rt2= (char *)rect2;
	rt= (char *)out;

	fac2= (int)(256.0*facf0);
	fac1= 256-fac2;
	fac4= (int)(256.0*facf1);
	fac3= 256-fac4;

	while(y--) {

		x= xo;
		while(x--) {

			rt[0]= (fac1*rt1[0] + fac2*rt2[0])>>8;
			rt[1]= (fac1*rt1[1] + fac2*rt2[1])>>8;
			rt[2]= (fac1*rt1[2] + fac2*rt2[2])>>8;
			rt[3]= (fac1*rt1[3] + fac2*rt2[3])>>8;

			rt1+= 4; rt2+= 4; rt+= 4;
		}

		if(y==0) break;
		y--;

		x= xo;
		while(x--) {

			rt[0]= (fac3*rt1[0] + fac4*rt2[0])>>8;
			rt[1]= (fac3*rt1[1] + fac4*rt2[1])>>8;
			rt[2]= (fac3*rt1[2] + fac4*rt2[2])>>8;
			rt[3]= (fac3*rt1[3] + fac4*rt2[3])>>8;

			rt1+= 4; rt2+= 4; rt+= 4;
		}

	}
}

void do_gammacross_effect(float facf0, float facf1, int x, int y, unsigned int *rect1, unsigned int *rect2, unsigned int *out)
{
/*  	extern unsigned short *igamtab1, *gamtab; render.h */
	int fac1, fac2, col;
	int xo;
	char *rt1, *rt2, *rt;

	xo= x;
	rt1= (char *)rect1;
	rt2= (char *)rect2;
	rt= (char *)out;

	fac2= (int)(256.0*facf0);
	fac1= 256-fac2;

	while(y--) {

		x= xo;
		while(x--) {

			col= (fac1*igamtab1[rt1[0]] + fac2*igamtab1[rt2[0]])>>8;
			if(col>65535) rt[0]= 255; else rt[0]= ( (char *)(gamtab+col))[MOST_SIG_BYTE];
			col=(fac1*igamtab1[rt1[1]] + fac2*igamtab1[rt2[1]])>>8;
			if(col>65535) rt[1]= 255; else rt[1]= ( (char *)(gamtab+col))[MOST_SIG_BYTE];
			col= (fac1*igamtab1[rt1[2]] + fac2*igamtab1[rt2[2]])>>8;
			if(col>65535) rt[2]= 255; else rt[2]= ( (char *)(gamtab+col))[MOST_SIG_BYTE];
			col= (fac1*igamtab1[rt1[3]] + fac2*igamtab1[rt2[3]])>>8;
			if(col>65535) rt[3]= 255; else rt[3]= ( (char *)(gamtab+col))[MOST_SIG_BYTE];

			rt1+= 4; rt2+= 4; rt+= 4;
		}

		if(y==0) break;
		y--;

		x= xo;
		while(x--) {

			col= (fac1*igamtab1[rt1[0]] + fac2*igamtab1[rt2[0]])>>8;
			if(col>65535) rt[0]= 255; else rt[0]= ( (char *)(gamtab+col))[MOST_SIG_BYTE];
			col= (fac1*igamtab1[rt1[1]] + fac2*igamtab1[rt2[1]])>>8;
			if(col>65535) rt[1]= 255; else rt[1]= ( (char *)(gamtab+col))[MOST_SIG_BYTE];
			col= (fac1*igamtab1[rt1[2]] + fac2*igamtab1[rt2[2]])>>8;
			if(col>65535) rt[2]= 255; else rt[2]= ( (char *)(gamtab+col))[MOST_SIG_BYTE];
			col= (fac1*igamtab1[rt1[3]] + fac2*igamtab1[rt2[3]])>>8;
			if(col>65535) rt[3]= 255; else rt[3]= ( (char *)(gamtab+col))[MOST_SIG_BYTE];

			rt1+= 4; rt2+= 4; rt+= 4;
		}

	}
}

void do_add_effect(float facf0, float facf1, int x, int y, unsigned int *rect1, unsigned int *rect2, unsigned int *out)
{
	int col, xo, fac1, fac3;
	char *rt1, *rt2, *rt;

	xo= x;
	rt1= (char *)rect1;
	rt2= (char *)rect2;
	rt= (char *)out;

	fac1= (int)(256.0*facf0);
	fac3= (int)(256.0*facf1);

	while(y--) {

		x= xo;
		while(x--) {

			col= rt1[0]+ ((fac1*rt2[0])>>8);
			if(col>255) rt[0]= 255; else rt[0]= col;
			col= rt1[1]+ ((fac1*rt2[1])>>8);
			if(col>255) rt[1]= 255; else rt[1]= col;
			col= rt1[2]+ ((fac1*rt2[2])>>8);
			if(col>255) rt[2]= 255; else rt[2]= col;
			col= rt1[3]+ ((fac1*rt2[3])>>8);
			if(col>255) rt[3]= 255; else rt[3]= col;

			rt1+= 4; rt2+= 4; rt+= 4;
		}

		if(y==0) break;
		y--;

		x= xo;
		while(x--) {

			col= rt1[0]+ ((fac3*rt2[0])>>8);
			if(col>255) rt[0]= 255; else rt[0]= col;
			col= rt1[1]+ ((fac3*rt2[1])>>8);
			if(col>255) rt[1]= 255; else rt[1]= col;
			col= rt1[2]+ ((fac3*rt2[2])>>8);
			if(col>255) rt[2]= 255; else rt[2]= col;
			col= rt1[3]+ ((fac3*rt2[3])>>8);
			if(col>255) rt[3]= 255; else rt[3]= col;

			rt1+= 4; rt2+= 4; rt+= 4;
		}
	}
}

void do_sub_effect(float facf0, float facf1, int x, int y, unsigned int *rect1, unsigned int *rect2, unsigned int *out)
{
	int col, xo, fac1, fac3;
	char *rt1, *rt2, *rt;

	xo= x;
	rt1= (char *)rect1;
	rt2= (char *)rect2;
	rt= (char *)out;

	fac1= (int)(256.0*facf0);
	fac3= (int)(256.0*facf1);

	while(y--) {

		x= xo;
		while(x--) {

			col= rt1[0]- ((fac1*rt2[0])>>8);
			if(col<0) rt[0]= 0; else rt[0]= col;
			col= rt1[1]- ((fac1*rt2[1])>>8);
			if(col<0) rt[1]= 0; else rt[1]= col;
			col= rt1[2]- ((fac1*rt2[2])>>8);
			if(col<0) rt[2]= 0; else rt[2]= col;
			col= rt1[3]- ((fac1*rt2[3])>>8);
			if(col<0) rt[3]= 0; else rt[3]= col;

			rt1+= 4; rt2+= 4; rt+= 4;
		}

		if(y==0) break;
		y--;

		x= xo;
		while(x--) {

			col= rt1[0]- ((fac3*rt2[0])>>8);
			if(col<0) rt[0]= 0; else rt[0]= col;
			col= rt1[1]- ((fac3*rt2[1])>>8);
			if(col<0) rt[1]= 0; else rt[1]= col;
			col= rt1[2]- ((fac3*rt2[2])>>8);
			if(col<0) rt[2]= 0; else rt[2]= col;
			col= rt1[3]- ((fac3*rt2[3])>>8);
			if(col<0) rt[3]= 0; else rt[3]= col;

			rt1+= 4; rt2+= 4; rt+= 4;
		}
	}
}

/* Must be > 0 or add precopy, etc to the function */
#define XOFF	8
#define YOFF	8

void do_drop_effect(float facf0, float facf1, int x, int y, unsigned int *rect2i, unsigned int *rect1i, unsigned int *outi)
{
	int height, width, temp, fac, fac1, fac2;
	char *rt1, *rt2, *out;
	int field= 1;

	width= x;
	height= y;

	fac1= (int)(70.0*facf0);
	fac2= (int)(70.0*facf1);

	rt2= (char*) (rect2i + YOFF*width);
	rt1= (char*) rect1i;
	out= (char*) outi;
	for (y=0; y<height-YOFF; y++) {
		if(field) fac= fac1;
		else fac= fac2;
		field= !field;

		memcpy(out, rt1, sizeof(int)*XOFF);
		rt1+= XOFF*4;
		out+= XOFF*4;

		for (x=XOFF; x<width; x++) {
			temp= ((fac*rt2[3])>>8);

			*(out++)= MAX2(0, *rt1 - temp); rt1++;
			*(out++)= MAX2(0, *rt1 - temp); rt1++;
			*(out++)= MAX2(0, *rt1 - temp); rt1++;
			*(out++)= MAX2(0, *rt1 - temp); rt1++;
			rt2+=4;
		}
		rt2+=XOFF*4;
	}
	memcpy(out, rt1, sizeof(int)*YOFF*width);
}

						/* WATCH:  rect2 and rect1 reversed */
void do_drop_effect2(float facf0, float facf1, int x, int y, unsigned int *rect2, unsigned int *rect1, unsigned int *out)
{
	int col, xo, yo, temp, fac1, fac3;
	int xofs= -8, yofs= 8;
	char *rt1, *rt2, *rt;

	xo= x;
	yo= y;

	rt2= (char *)(rect2 + yofs*x + xofs);

	rt1= (char *)rect1;
	rt= (char *)out;

	fac1= (int)(70.0*facf0);
	fac3= (int)(70.0*facf1);

	while(y-- > 0) {

		temp= y-yofs;
		if(temp > 0 && temp < yo) {

			x= xo;
			while(x--) {

				temp= x+xofs;
				if(temp > 0 && temp < xo) {

					temp= ((fac1*rt2[3])>>8);

					col= rt1[0]- temp;
					if(col<0) rt[0]= 0; else rt[0]= col;
					col= rt1[1]- temp;
					if(col<0) rt[1]= 0; else rt[1]= col;
					col= rt1[2]- temp;
					if(col<0) rt[2]= 0; else rt[2]= col;
					col= rt1[3]- temp;
					if(col<0) rt[3]= 0; else rt[3]= col;
				}
				else *( (unsigned int *)rt) = *( (unsigned int *)rt1);

				rt1+= 4; rt2+= 4; rt+= 4;
			}
		}
		else {
			x= xo;
			while(x--) {
				*( (unsigned int *)rt) = *( (unsigned int *)rt1);
				rt1+= 4; rt2+= 4; rt+= 4;
			}
		}

		if(y==0) break;
		y--;

		temp= y-yofs;
		if(temp > 0 && temp < yo) {

			x= xo;
			while(x--) {

				temp= x+xofs;
				if(temp > 0 && temp < xo) {

					temp= ((fac3*rt2[3])>>8);

					col= rt1[0]- temp;
					if(col<0) rt[0]= 0; else rt[0]= col;
					col= rt1[1]- temp;
					if(col<0) rt[1]= 0; else rt[1]= col;
					col= rt1[2]- temp;
					if(col<0) rt[2]= 0; else rt[2]= col;
					col= rt1[3]- temp;
					if(col<0) rt[3]= 0; else rt[3]= col;
				}
				else *( (unsigned int *)rt) = *( (unsigned int *)rt1);

				rt1+= 4; rt2+= 4; rt+= 4;
			}
		}
		else {
			x= xo;
			while(x--) {
				*( (unsigned int *)rt) = *( (unsigned int *)rt1);
				rt1+= 4; rt2+= 4; rt+= 4;
			}
		}
	}
}


void do_mul_effect(float facf0, float facf1, int x, int y, unsigned int *rect1, unsigned int *rect2, unsigned int *out)
{
	int  xo, fac1, fac3;
	char *rt1, *rt2, *rt;

	xo= x;
	rt1= (char *)rect1;
	rt2= (char *)rect2;
	rt= (char *)out;

	fac1= (int)(256.0*facf0);
	fac3= (int)(256.0*facf1);

	/* formula:
	 *		fac*(a*b) + (1-fac)*a  => fac*a*(b-1)+a
	 */

	while(y--) {

		x= xo;
		while(x--) {

			rt[0]= rt1[0] + ((fac1*rt1[0]*(rt2[0]-256))>>16);
			rt[1]= rt1[1] + ((fac1*rt1[1]*(rt2[1]-256))>>16);
			rt[2]= rt1[2] + ((fac1*rt1[2]*(rt2[2]-256))>>16);
			rt[3]= rt1[3] + ((fac1*rt1[3]*(rt2[3]-256))>>16);

			rt1+= 4; rt2+= 4; rt+= 4;
		}

		if(y==0) break;
		y--;

		x= xo;
		while(x--) {

			rt[0]= rt1[0] + ((fac3*rt1[0]*(rt2[0]-256))>>16);
			rt[1]= rt1[1] + ((fac3*rt1[1]*(rt2[1]-256))>>16);
			rt[2]= rt1[2] + ((fac3*rt1[2]*(rt2[2]-256))>>16);
			rt[3]= rt1[3] + ((fac3*rt1[3]*(rt2[3]-256))>>16);

			rt1+= 4; rt2+= 4; rt+= 4;
		}
	}
}

// This function calculates the blur band for the wipe effects
float in_band(float width,float dist, float perc,int side,int dir){
	
	float t1,t2,alpha,percwidth;
	if(width == 0)
		return (float)side;
	if(side == 1)
		percwidth = width * perc;
	else
		percwidth = width * (1 - perc);
	
	if(width < dist)
		return side;
	
	t1 = dist / width;  //percentange of width that is
	t2 = 1 / width;  //amount of alpha per % point
	
	if(side == 1)
		alpha = (t1*t2*100) + (1-perc); // add point's alpha contrib to current position in wipe
	else
		alpha = (1-perc) - (t1*t2*100);
	
	if(dir == 0)
		alpha = 1-alpha;
	return alpha;
}

float check_zone(int x, int y, int xo, int yo, Sequence *seq, float facf0) {

   float posx, posy,hyp,hyp2,angle,hwidth,b1,b2,b3,pointdist;
   /*some future stuff
   float hyp3,hyp4,b4,b5	   
   */
   float temp1,temp2,temp3,temp4; //some placeholder variables
   float halfx = xo/2;
   float halfy = yo/2;
   float widthf,output=0;
   WipeVars *wipe = (WipeVars *)seq->effectdata;
   int width;

 	angle = wipe->angle;
 	if(angle < 0){
 		x = xo-x;
 		//y = yo-y
 		}
 	angle = pow(fabs(angle)/45,log(xo)/log(2));

	posy = facf0 * yo;
	if(wipe->forward){
		posx = facf0 * xo;
		posy = facf0 * yo;
	} else{
		posx = xo - facf0 * xo;
		posy = yo - facf0 * yo;
	}
   switch (wipe->wipetype) {
       case DO_SINGLE_WIPE:
         width = (int)(wipe->edgeWidth*((xo+yo)/2.0));
         hwidth = (float)width/2.0;       
                
         if (angle == 0.0)angle = 0.000001;
         b1 = posy - (-angle)*posx;
         b2 = y - (-angle)*x;
         hyp  = fabs(angle*x+y+(-posy-angle*posx))/sqrt(angle*angle+1);
         if(angle < 0){
         	 temp1 = b1;
         	 b1 = b2;
         	 b2 = temp1;
         }
         if(wipe->forward){	 
		     if(b1 < b2)
				output = in_band(width,hyp,facf0,1,1);
	         else
				output = in_band(width,hyp,facf0,0,1);
		 }
		 else{	 
	         if(b1 < b2)
				output = in_band(width,hyp,facf0,0,1);
	         else
				output = in_band(width,hyp,facf0,1,1);
		 }
		 break;
	 
	 
	  case DO_DOUBLE_WIPE:
		 if(!wipe->forward)facf0 = 1-facf0;   // Go the other direction

	     width = (int)(wipe->edgeWidth*((xo+yo)/2.0));  // calculate the blur width
	     hwidth = (float)width/2.0;       
	     if (angle == 0)angle = 0.000001;
	     b1 = posy/2 - (-angle)*posx/2;
	     b3 = (yo-posy/2) - (-angle)*(xo-posx/2);
	     b2 = y - (-angle)*x;

	     hyp = abs(angle*x+y+(-posy/2-angle*posx/2))/sqrt(angle*angle+1);
	     hyp2 = abs(angle*x+y+(-(yo-posy/2)-angle*(xo-posx/2)))/sqrt(angle*angle+1);
	     
	     temp1 = xo*(1-facf0/2)-xo*facf0/2;
	     temp2 = yo*(1-facf0/2)-yo*facf0/2;
		 pointdist = sqrt(temp1*temp1 + temp2*temp2);

			 if(b2 < b1 && b2 < b3 ){
				if(hwidth < pointdist)
					output = in_band(hwidth,hyp,facf0,0,1);
			}
			 else if(b2 > b1 && b2 > b3 ){
				if(hwidth < pointdist)
					output = in_band(hwidth,hyp2,facf0,0,1);	
			} 
		     else{
		     	 if(  hyp < hwidth && hyp2 > hwidth )
		     	 	 output = in_band(hwidth,hyp,facf0,1,1);
		     	 else if(  hyp > hwidth && hyp2 < hwidth )
				 	 output = in_band(hwidth,hyp2,facf0,1,1);
				 else
				 	 output = in_band(hwidth,hyp2,facf0,1,1) * in_band(hwidth,hyp,facf0,1,1);
		     }
		     if(!wipe->forward)output = 1-output;
	 break;     
	 case DO_CLOCK_WIPE:
	 	 	/*
	 	 		temp1: angle of effect center in rads
	 	 		temp2: angle of line through (halfx,halfy) and (x,y) in rads
	 	 		temp3: angle of low side of blur
	 	 		temp4: angle of high side of blur
	 	 	*/
	  	 	output = 1-facf0;
	 	 	widthf = wipe->edgeWidth*2*3.14159;
	 	 	temp1 = 2 * 3.14159 * facf0;
	 	 	
 	 		if(wipe->forward){
 	 			temp1 = 2*3.14159-temp1;
 	 		}
 	 		
	 	 	x = x - halfx;
	 	 	y = y - halfy;

	 	 	temp2 = asin(abs(y)/sqrt(x*x + y*y));
	 	 	if(x <= 0 && y >= 0)
	 	 		temp2 = 3.14159 - temp2;
	 	 	else if(x<=0 && y <= 0)
	 	 		temp2 += 3.14159;
	 	 	else if(x >= 0 && y <= 0)
	 	 		temp2 = 2*3.14159 - temp2;
	 	  	
 	 		if(wipe->forward){
	 	 		temp3 = temp1-(widthf/2)*facf0;
	 	 		temp4 = temp1+(widthf/2)*(1-facf0);
 	 		}
 	 		else{
	 	 		temp3 = temp1-(widthf/2)*(1-facf0);
	 	 		temp4 = temp1+(widthf/2)*facf0;
			}
 	 		if (temp3 < 0)  temp3 = 0;
 	 		if (temp4 > 2*3.14159) temp4 = 2*3.14159;
 	 		
 	 		
 	 		if(temp2 < temp3)
				output = 0;
 	 		else if (temp2 > temp4)
 	 			output = 1;
 	 		else
 	 			output = (temp2-temp3)/(temp4-temp3);
	 	 	if(x == 0 && y == 0){
	 	 		output = 1;
	 	 	}
			if(output != output)
				output = 1;
			if(wipe->forward)
				output = 1 - output;
  	break;
	/* BOX WIPE IS NOT WORKING YET */
     /* case DO_CROSS_WIPE: */
	/* BOX WIPE IS NOT WORKING YET */
     /* case DO_BOX_WIPE: 
		 if(invert)facf0 = 1-facf0;

	     width = (int)(wipe->edgeWidth*((xo+yo)/2.0));
	     hwidth = (float)width/2.0;       
	     if (angle == 0)angle = 0.000001;
	     b1 = posy/2 - (-angle)*posx/2;
	     b3 = (yo-posy/2) - (-angle)*(xo-posx/2);
	     b2 = y - (-angle)*x;

	     hyp = abs(angle*x+y+(-posy/2-angle*posx/2))/sqrt(angle*angle+1);
	     hyp2 = abs(angle*x+y+(-(yo-posy/2)-angle*(xo-posx/2)))/sqrt(angle*angle+1);
	     
	     temp1 = xo*(1-facf0/2)-xo*facf0/2;
	     temp2 = yo*(1-facf0/2)-yo*facf0/2;
		 pointdist = sqrt(temp1*temp1 + temp2*temp2);

			 if(b2 < b1 && b2 < b3 ){
				if(hwidth < pointdist)
					output = in_band(hwidth,hyp,facf0,0,1);
			}
			 else if(b2 > b1 && b2 > b3 ){
				if(hwidth < pointdist)
					output = in_band(hwidth,hyp2,facf0,0,1);	
			} 
		     else{
		     	 if(  hyp < hwidth && hyp2 > hwidth )
		     	 	 output = in_band(hwidth,hyp,facf0,1,1);
		     	 else if(  hyp > hwidth && hyp2 < hwidth )
				 	 output = in_band(hwidth,hyp2,facf0,1,1);
				 else
				 	 output = in_band(hwidth,hyp2,facf0,1,1) * in_band(hwidth,hyp,facf0,1,1);
		     }
		 if(invert)facf0 = 1-facf0;
	     angle = -1/angle;
	     b1 = posy/2 - (-angle)*posx/2;
	     b3 = (yo-posy/2) - (-angle)*(xo-posx/2);
	     b2 = y - (-angle)*x;

	     hyp = abs(angle*x+y+(-posy/2-angle*posx/2))/sqrt(angle*angle+1);
	     hyp2 = abs(angle*x+y+(-(yo-posy/2)-angle*(xo-posx/2)))/sqrt(angle*angle+1);
	   
	   	 if(b2 < b1 && b2 < b3 ){
				if(hwidth < pointdist)
					output *= in_band(hwidth,hyp,facf0,0,1);
			}
			 else if(b2 > b1 && b2 > b3 ){
				if(hwidth < pointdist)
					output *= in_band(hwidth,hyp2,facf0,0,1);	
			} 
		     else{
		     	 if(  hyp < hwidth && hyp2 > hwidth )
		     	 	 output *= in_band(hwidth,hyp,facf0,1,1);
		     	 else if(  hyp > hwidth && hyp2 < hwidth )
				 	 output *= in_band(hwidth,hyp2,facf0,1,1);
				 else
				 	 output *= in_band(hwidth,hyp2,facf0,1,1) * in_band(hwidth,hyp,facf0,1,1);
		     }
		     
	 break;*/
      case DO_IRIS_WIPE:
      	 if(xo > yo) yo = xo;
      	 else xo = yo;
      	 
		if(!wipe->forward)
			facf0 = 1-facf0;

	     width = (int)(wipe->edgeWidth*((xo+yo)/2.0));
	     hwidth = (float)width/2.0; 
	     
      	 temp1 = (halfx-(halfx)*facf0);     
		 pointdist = sqrt(temp1*temp1 + temp1*temp1);
		 
		 temp2 = sqrt((halfx-x)*(halfx-x)  +  (halfy-y)*(halfy-y));
		 if(temp2 > pointdist)
		 	 output = in_band(hwidth,fabs(temp2-pointdist),facf0,0,1);
		 else
		 	 output = in_band(hwidth,fabs(temp2-pointdist),facf0,1,1);
		 
		if(!wipe->forward)
			output = 1-output;
			
	 break;
   }
   if     (output < 0) output = 0;
   else if(output > 1) output = 1;
   return output;
}

void init_wipe_effect(Sequence *seq)
{
	if(seq->effectdata)MEM_freeN(seq->effectdata);
	seq->effectdata = MEM_callocN(sizeof(struct WipeVars), "wipevars");
}

void do_wipe_effect(Sequence *seq, float facf0, float facf1, int x, int y, unsigned int *rect1, unsigned int *rect2, unsigned int *out)
{
	int xo, yo;
	char *rt1, *rt2, *rt;
	rt1 = (char *)rect1;
	rt2 = (char *)rect2;
	rt = (char *)out;

	xo = x;
	yo = y;
	for(y=0;y<yo;y++) {

      for(x=0;x<xo;x++) {
			float check = check_zone(x,y,xo,yo,seq,facf0);
			if (check) {
				if (rt1) {
					rt[0] = (int)(rt1[0]*check)+ (int)(rt2[0]*(1-check));
					rt[1] = (int)(rt1[1]*check)+ (int)(rt2[1]*(1-check));
					rt[2] = (int)(rt1[2]*check)+ (int)(rt2[2]*(1-check));
					rt[3] = (int)(rt1[3]*check)+ (int)(rt2[3]*(1-check));
				} else {
					rt[0] = 0;
					rt[1] = 0;
					rt[2] = 0;
					rt[3] = 255;
				}
			} else {
				if (rt2) {
					rt[0] = rt2[0];
					rt[1] = rt2[1];
					rt[2] = rt2[2];
					rt[3] = rt2[3];
				} else {
					rt[0] = 0;
					rt[1] = 0;
					rt[2] = 0;
					rt[3] = 255;
				}
			}

			rt+=4;
			if(rt1 !=NULL){
				rt1+=4;
			}
			if(rt2 !=NULL){
				rt2+=4;
			}
		}
	}
}

/* Glow Functions */

void RVBlurBitmap2 ( unsigned char* map, int width,int height,float blur,
   int quality)
/*	MUUUCCH better than the previous blur. */
/*	We do the blurring in two passes which is a whole lot faster. */
/*	I changed the math arount to implement an actual Gaussian */
/*	distribution. */
/* */
/*	Watch out though, it tends to misbehaven with large blur values on */
/*	a small bitmap.  Avoid avoid avoid. */
/*=============================== */
{
	unsigned char*	temp=NULL,*swap;
	float	*filter=NULL;
	int	x,y,i,fx,fy;
	int	index, ix, halfWidth;
	float	fval, k, curColor[3], curColor2[3], weight=0;

	/*	If we're not really blurring, bail out */
	if (blur<=0)
		return;

	/*	Allocate memory for the tempmap and the blur filter matrix */
	temp= MEM_mallocN( (width*height*4), "blurbitmaptemp");
	if (!temp)
		return;

	/*	Allocate memory for the filter elements */
	halfWidth = ((quality+1)*blur);
	filter = (float *)MEM_mallocN(sizeof(float)*halfWidth*2, "blurbitmapfilter");
	if (!filter){
		MEM_freeN (temp);
		return;
	}

	/*	Apparently we're calculating a bell curve */
	/*	based on the standard deviation (or radius) */
	/*	This code is based on an example */
	/*	posted to comp.graphics.algorithms by */
	/*	Blancmange (bmange@airdmhor.gen.nz) */

	k = -1.0/(2.0*3.14159*blur*blur);
	fval=0;
	for (ix = 0;ix< halfWidth;ix++){
          	weight = (float)exp(k*(ix*ix));
		filter[halfWidth - ix] = weight;
		filter[halfWidth + ix] = weight;
	}
	filter[0] = weight;

	/*	Normalize the array */
	fval=0;
	for (ix = 0;ix< halfWidth*2;ix++)
		fval+=filter[ix];

	for (ix = 0;ix< halfWidth*2;ix++)
		filter[ix]/=fval;

	/*	Blur the rows */
	for (y=0;y<height;y++){
		/*	Do the left & right strips */
		for (x=0;x<halfWidth;x++){
			index=(x+y*width)*4;
			fx=0;
			curColor[0]=curColor[1]=curColor[2]=0;
			curColor2[0]=curColor2[1]=curColor2[2]=0;

			for (i=x-halfWidth;i<x+halfWidth;i++){
			   if ((i>=0)&&(i<width)){
				curColor[0]+=map[(i+y*width)*4+GlowR]*filter[fx];
				curColor[1]+=map[(i+y*width)*4+GlowG]*filter[fx];
				curColor[2]+=map[(i+y*width)*4+GlowB]*filter[fx];

				curColor2[0]+=map[(width-1-i+y*width)*4+GlowR] *
                                   filter[fx];
				curColor2[1]+=map[(width-1-i+y*width)*4+GlowG] *
                                   filter[fx];
				curColor2[2]+=map[(width-1-i+y*width)*4+GlowB] *
                                   filter[fx];
				}
				fx++;
			}
			temp[index+GlowR]=curColor[0];
			temp[index+GlowG]=curColor[1];
			temp[index+GlowB]=curColor[2];

			temp[((width-1-x+y*width)*4)+GlowR]=curColor2[0];
			temp[((width-1-x+y*width)*4)+GlowG]=curColor2[1];
			temp[((width-1-x+y*width)*4)+GlowB]=curColor2[2];

		}
		/*	Do the main body */
		for (x=halfWidth;x<width-halfWidth;x++){
			index=(x+y*width)*4;
			fx=0;
			curColor[0]=curColor[1]=curColor[2]=0;
			for (i=x-halfWidth;i<x+halfWidth;i++){
				curColor[0]+=map[(i+y*width)*4+GlowR]*filter[fx];
				curColor[1]+=map[(i+y*width)*4+GlowG]*filter[fx];
				curColor[2]+=map[(i+y*width)*4+GlowB]*filter[fx];
				fx++;
			}
			temp[index+GlowR]=curColor[0];
			temp[index+GlowG]=curColor[1];
			temp[index+GlowB]=curColor[2];
		}
	}

	/*	Swap buffers */
	swap=temp;temp=map;map=swap;


	/*	Blur the columns */
	for (x=0;x<width;x++){
		/*	Do the top & bottom strips */
		for (y=0;y<halfWidth;y++){
			index=(x+y*width)*4;
			fy=0;
			curColor[0]=curColor[1]=curColor[2]=0;
			curColor2[0]=curColor2[1]=curColor2[2]=0;
			for (i=y-halfWidth;i<y+halfWidth;i++){
				if ((i>=0)&&(i<height)){
				   /*	Bottom */
				   curColor[0]+=map[(x+i*width)*4+GlowR]*filter[fy];
				   curColor[1]+=map[(x+i*width)*4+GlowG]*filter[fy];
				   curColor[2]+=map[(x+i*width)*4+GlowB]*filter[fy];

				   /*	Top */
				   curColor2[0]+=map[(x+(height-1-i)*width) *
                                      4+GlowR]*filter[fy];
				   curColor2[1]+=map[(x+(height-1-i)*width) *
                                      4+GlowG]*filter[fy];
				   curColor2[2]+=map[(x+(height-1-i)*width) *
                                      4+GlowB]*filter[fy];
				}
				fy++;
			}
			temp[index+GlowR]=curColor[0];
			temp[index+GlowG]=curColor[1];
			temp[index+GlowB]=curColor[2];
			temp[((x+(height-1-y)*width)*4)+GlowR]=curColor2[0];
			temp[((x+(height-1-y)*width)*4)+GlowG]=curColor2[1];
			temp[((x+(height-1-y)*width)*4)+GlowB]=curColor2[2];
		}
		/*	Do the main body */
		for (y=halfWidth;y<height-halfWidth;y++){
			index=(x+y*width)*4;
			fy=0;
			curColor[0]=curColor[1]=curColor[2]=0;
			for (i=y-halfWidth;i<y+halfWidth;i++){
				curColor[0]+=map[(x+i*width)*4+GlowR]*filter[fy];
				curColor[1]+=map[(x+i*width)*4+GlowG]*filter[fy];
				curColor[2]+=map[(x+i*width)*4+GlowB]*filter[fy];
				fy++;
			}
			temp[index+GlowR]=curColor[0];
			temp[index+GlowG]=curColor[1];
			temp[index+GlowB]=curColor[2];
		}
	}


	/*	Swap buffers */
	swap=temp;temp=map;map=swap;

	/*	Tidy up	 */
	MEM_freeN (filter);
	MEM_freeN (temp);
}


/*	Adds two bitmaps and puts the results into a third map. */
/*	C must have been previously allocated but it may be A or B. */
/*	We clamp values to 255 to prevent weirdness */
/*=============================== */
void RVAddBitmaps (unsigned char* a, unsigned char* b, unsigned char* c, int width, int height)
{
	int	x,y,index;

	for (y=0;y<height;y++){
		for (x=0;x<width;x++){
			index=(x+y*width)*4;
			c[index+GlowR]=MIN2(255,a[index+GlowR]+b[index+GlowR]);
			c[index+GlowG]=MIN2(255,a[index+GlowG]+b[index+GlowG]);
			c[index+GlowB]=MIN2(255,a[index+GlowB]+b[index+GlowB]);
			c[index+GlowA]=MIN2(255,a[index+GlowA]+b[index+GlowA]);
		}
	}
}

/*	For each pixel whose total luminance exceeds the threshold, */
/*	Multiply it's value by BOOST and add it to the output map */
void RVIsolateHighlights (unsigned char* in, unsigned char* out, int width, int height, int threshold, float boost, float clamp)
{
	int x,y,index;
	int	intensity;


	for(y=0;y< height;y++) {
		for (x=0;x< width;x++) {
	 	   index= (x+y*width)*4;

		   /*	Isolate the intensity */
		   intensity=(in[index+GlowR]+in[index+GlowG]+in[index+GlowB]-threshold);
		   if (intensity>0){
			out[index+GlowR]=MIN2(255*clamp, (in[index+GlowR]*boost*intensity)/255);
			out[index+GlowG]=MIN2(255*clamp, (in[index+GlowG]*boost*intensity)/255);
			out[index+GlowB]=MIN2(255*clamp, (in[index+GlowB]*boost*intensity)/255);
			}
			else{
				out[index+GlowR]=0;
				out[index+GlowG]=0;
				out[index+GlowB]=0;
			}
		}
	}
}

void init_glow_effect(Sequence *seq)
{
	GlowVars *glow;

	if(seq->effectdata)MEM_freeN(seq->effectdata);
	seq->effectdata = MEM_callocN(sizeof(struct GlowVars), "glowvars");

	glow = (GlowVars *)seq->effectdata;
	glow->fMini = 0.25;
	glow->fClamp = 1.0;
	glow->fBoost = 0.5;
	glow->dDist = 3.0;
	glow->dQuality = 3;
	glow->bNoComp = 0;
}


//void do_glow_effect(Cast *cast, float facf0, float facf1, int xo, int yo, ImBuf *ibuf1, ImBuf *ibuf2, ImBuf *outbuf, ImBuf *use)
void do_glow_effect(Sequence *seq, float facf0, float facf1, int x, int y, unsigned int *rect1, unsigned int *rect2, unsigned int *out)
{
	unsigned char *outbuf=(unsigned char *)out;
	unsigned char *inbuf=(unsigned char *)rect1;
	GlowVars *glow = (GlowVars *)seq->effectdata;

	RVIsolateHighlights	(inbuf, outbuf , x, y, glow->fMini*765, glow->fBoost, glow->fClamp);
	RVBlurBitmap2 (outbuf, x, y, glow->dDist,glow->dQuality);
	if (!glow->bNoComp)
		RVAddBitmaps (inbuf , outbuf, outbuf, x, y);
}

void make_black_ibuf(ImBuf *ibuf)
{
	unsigned int *rect;
	int tot;

	if(ibuf==0 || ibuf->rect==0) return;

	tot= ibuf->x*ibuf->y;
	rect= ibuf->rect;
	while(tot--) *(rect++)= 0;

}

void multibuf(ImBuf *ibuf, float fmul)
{
	char *rt;
	int a, mul, icol;

	mul= (int)(256.0*fmul);

	a= ibuf->x*ibuf->y;
	rt= (char *)ibuf->rect;
	while(a--) {

		icol= (mul*rt[0])>>8;
		if(icol>254) rt[0]= 255; else rt[0]= icol;
		icol= (mul*rt[1])>>8;
		if(icol>254) rt[1]= 255; else rt[1]= icol;
		icol= (mul*rt[2])>>8;
		if(icol>254) rt[2]= 255; else rt[2]= icol;
		icol= (mul*rt[3])>>8;
		if(icol>254) rt[3]= 255; else rt[3]= icol;

		rt+= 4;
	}
}

void do_effect(int cfra, Sequence *seq, StripElem *se)
{
	StripElem *se1, *se2, *se3;
	float fac, facf;
	int x, y;
	char *cp;

	if(se->se1==0 || se->se2==0 || se->se3==0) {
		make_black_ibuf(se->ibuf);
		return;
	}

	/* if metastrip: other se's */
	if(se->se1->ok==2) se1= se->se1->se1;
	else se1= se->se1;

	if(se->se2->ok==2) se2= se->se2->se1;
	else se2= se->se2;

	if(se->se3->ok==2) se3= se->se3->se1;
	else se3= se->se3;

	if(se1==0 || se2==0 || se3==0 || se1->ibuf==0 || se2->ibuf==0 || se3->ibuf==0) {
		make_black_ibuf(se->ibuf);
		return;
	}

	x= se2->ibuf->x;
	y= se2->ibuf->y;

	if(seq->ipo && seq->ipo->curve.first) {
		do_seq_ipo(seq);
		fac= seq->facf0;
		facf= seq->facf1;
	}
	else if ( seq->type==SEQ_CROSS || seq->type==SEQ_GAMCROSS || seq->type==SEQ_PLUGIN || seq->type==SEQ_WIPE) {
		fac= (float)(cfra - seq->startdisp);
		facf= (float)(fac+0.5);
		fac /= seq->len;
		facf /= seq->len;
	}
	else {
		fac= facf= 1.0;
	}

	if( G.scene->r.mode & R_FIELDS ); else facf= fac;

	switch(seq->type) {
	case SEQ_CROSS:
		do_cross_effect(fac, facf, x, y, se1->ibuf->rect, se2->ibuf->rect, se->ibuf->rect);
		break;
	case SEQ_GAMCROSS:
		do_gammacross_effect(fac, facf, x, y, se1->ibuf->rect, se2->ibuf->rect, se->ibuf->rect);
		break;
	case SEQ_ADD:
		do_add_effect(fac, facf, x, y, se1->ibuf->rect, se2->ibuf->rect, se->ibuf->rect);
		break;
	case SEQ_SUB:
		do_sub_effect(fac, facf, x, y, se1->ibuf->rect, se2->ibuf->rect, se->ibuf->rect);
		break;
	case SEQ_MUL:
		do_mul_effect(fac, facf, x, y, se1->ibuf->rect, se2->ibuf->rect, se->ibuf->rect);
		break;
	case SEQ_ALPHAOVER:
		do_alphaover_effect(fac, facf, x, y, se1->ibuf->rect, se2->ibuf->rect, se->ibuf->rect);
		break;
	case SEQ_OVERDROP:
		do_drop_effect(fac, facf, x, y, se1->ibuf->rect, se2->ibuf->rect, se->ibuf->rect);
		do_alphaover_effect(fac, facf, x, y, se1->ibuf->rect, se->ibuf->rect, se->ibuf->rect);
		break;
	case SEQ_ALPHAUNDER:
		do_alphaunder_effect(fac, facf, x, y, se1->ibuf->rect, se2->ibuf->rect, se->ibuf->rect);
		break;
	case SEQ_WIPE:
		do_wipe_effect(seq, fac, facf, x, y, se1->ibuf->rect, se2->ibuf->rect, se->ibuf->rect);
		break;
	case SEQ_GLOW:
		do_glow_effect(seq, fac, facf, x, y, se1->ibuf->rect, se2->ibuf->rect, se->ibuf->rect);
		break;
	case SEQ_PLUGIN:
		if(seq->plugin && seq->plugin->doit) {

			if((G.f & G_PLAYANIM)==0) waitcursor(1);

			if(seq->plugin->cfra) *(seq->plugin->cfra)= frame_to_float(CFRA);

			cp= PIL_dynlib_find_symbol(seq->plugin->handle, "seqname");
			if(cp) strcpy(cp, seq->name+2);

			if (seq->plugin->version<=2) {
				if(se1->ibuf) IMB_convert_rgba_to_abgr(se1->ibuf->x*se1->ibuf->y, se1->ibuf->rect);
				if(se2->ibuf) IMB_convert_rgba_to_abgr(se2->ibuf->x*se2->ibuf->y, se2->ibuf->rect);
				if(se3->ibuf) IMB_convert_rgba_to_abgr(se3->ibuf->x*se3->ibuf->y, se3->ibuf->rect);
			}

			((SeqDoit)seq->plugin->doit)(seq->plugin->data, fac, facf, x, y,
						se1->ibuf, se2->ibuf, se->ibuf, se3->ibuf);

			if (seq->plugin->version<=2) {
				if(se1->ibuf) IMB_convert_rgba_to_abgr(se1->ibuf->x*se1->ibuf->y, se1->ibuf->rect);
				if(se2->ibuf) IMB_convert_rgba_to_abgr(se2->ibuf->x*se2->ibuf->y, se2->ibuf->rect);
				if(se3->ibuf) IMB_convert_rgba_to_abgr(se3->ibuf->x*se3->ibuf->y, se3->ibuf->rect);
				IMB_convert_rgba_to_abgr(se->ibuf->x*se->ibuf->y, se->ibuf->rect);
			}

			if((G.f & G_PLAYANIM)==0) waitcursor(0);
		}
		break;
	}

}

int evaluate_seq_frame(int cfra)
{
	Sequence *seq;
	Editing *ed;
	int totseq=0;

	memset(seq_arr, 0, 4*MAXSEQ);

	ed= G.scene->ed;
	if(ed==0) return 0;

	seq= ed->seqbasep->first;
	while(seq) {
		if(seq->startdisp <=cfra && seq->enddisp > cfra) {
			seq_arr[seq->machine]= seq;
			totseq++;
		}
		seq= seq->next;
	}

	return totseq;
}

StripElem *give_stripelem(Sequence *seq, int cfra)
{
	Strip *strip;
	StripElem *se;
	int nr;

	strip= seq->strip;
	se= strip->stripdata;

	if(se==0) return 0;
	if(seq->startdisp >cfra || seq->enddisp <= cfra) return 0;

	if(cfra <= seq->start) nr= 0;
	else if(cfra >= seq->start+seq->len-1) nr= seq->len-1;
	else nr= cfra-seq->start;

	se+= nr;
	se->nr= nr;

	return se;
}

void set_meta_stripdata(Sequence *seqm)
{
	Sequence *seq, *seqim, *seqeff;
	Editing *ed;
	ListBase *tempbase;
	StripElem *se;
	int a, cfra, b;

	/* sets all ->se1 pointers in stripdata, to read the ibuf from it */

	ed= G.scene->ed;
	if(ed==0) return;

	tempbase= ed->seqbasep;
	ed->seqbasep= &seqm->seqbase;

	se= seqm->strip->stripdata;
	for(a=0; a<seqm->len; a++, se++) {
		cfra= a+seqm->start;
		if(evaluate_seq_frame(cfra)) {

			/* we take the upper effect strip or the lowest imagestrip/metastrip */
			seqim= seqeff= 0;

			for(b=1; b<MAXSEQ; b++) {
				if(seq_arr[b]) {
					seq= seq_arr[b];
					if(seq->type & SEQ_EFFECT) {
						if(seqeff==0) seqeff= seq;
						else if(seqeff->machine < seq->machine) seqeff= seq;
					}
					else {
						if(seqim==0) seqim= seq;
						else if(seqim->machine > seq->machine) seqim= seq;
					}
				}
			}
			if(seqeff) seq= seqeff;
			else if(seqim) seq= seqim;
			else seq= 0;

			if(seq) {
				se->se1= give_stripelem(seq, cfra);
			}
			else se->se1= 0;
		}
	}

	ed->seqbasep= tempbase;
}



/* HELP FUNCTIONS FOR GIVE_IBUF_SEQ */

void do_seq_count_cfra(ListBase *seqbase, int *totseq, int cfra)
{
	Sequence *seq;

	seq= seqbase->first;
	while(seq) {
		if(seq->startdisp <=cfra && seq->enddisp > cfra) {

			if(seq->seqbase.first) {

				if(cfra< seq->start) do_seq_count_cfra(&seq->seqbase, totseq, seq->start);
				else if(cfra> seq->start+seq->len-1) do_seq_count_cfra(&seq->seqbase, totseq, seq->start+seq->len-1);
				else do_seq_count_cfra(&seq->seqbase, totseq, cfra);
			}

			(*totseq)++;
		}
		seq= seq->next;
	}
}

void do_build_seqar_cfra(ListBase *seqbase, Sequence ***seqar, int cfra)
{
	Sequence *seq;
	StripElem *se;
	Scene *oldsce;
	unsigned int *rectot;
	int oldx, oldy, oldcfra, doseq;
	char name[FILE_MAXDIR];

	seq= seqbase->first;
	while(seq) {

		/* set at zero because free_imbuf_seq... */
		seq->curelem= 0;

		if ((seq->type == SEQ_SOUND) && (seq->ipo)
		  &&(seq->startdisp<=cfra+2) && (seq->enddisp>cfra)) do_seq_ipo(seq);

		if(seq->startdisp <=cfra && seq->enddisp > cfra) {

			if(seq->seqbase.first) {
				if(cfra< seq->start) do_build_seqar_cfra(&seq->seqbase, seqar, seq->start);
				else if(cfra> seq->start+seq->len-1) do_build_seqar_cfra(&seq->seqbase, seqar, seq->start+seq->len-1);
				else do_build_seqar_cfra(&seq->seqbase, seqar, cfra);
			}

			**seqar= seq;
			(*seqar)++;

			se=seq->curelem= give_stripelem(seq, cfra);

			if(se) {
				if(seq->type == SEQ_META) {
					se->ok= 2;
					if(se->se1==0) set_meta_stripdata(seq);
					if(se->se1) {
						se->ibuf= se->se1->ibuf;
					}
				}
				else if(seq->type == SEQ_SOUND) {
					se->ok= 2;
				}
				else if(seq->type & SEQ_EFFECT) {

					/* test if image is too small: reload */
					if(se->ibuf) {
						if(se->ibuf->x < seqrectx || se->ibuf->y < seqrecty) {
							IMB_freeImBuf(se->ibuf);
							se->ibuf= 0;
						}
					}

					/* does the effect should be recalculated? */

					if(se->ibuf==0 || (se->se1 != seq->seq1->curelem) || (se->se2 != seq->seq2->curelem) || (se->se3 != seq->seq3->curelem)) {
						se->se1= seq->seq1->curelem;
						se->se2= seq->seq2->curelem;
						se->se3= seq->seq3->curelem;

						if(se->ibuf==0) se->ibuf= IMB_allocImBuf((short)seqrectx, (short)seqrecty, 32, IB_rect, 0);

						do_effect(cfra, seq, se);
					}

					/* test size */
					if(se->ibuf) {
						if(se->ibuf->x != seqrectx || se->ibuf->y != seqrecty ) {
							if(G.scene->r.mode & R_OSA)
								IMB_scaleImBuf(se->ibuf, (short)seqrectx, (short)seqrecty);
							else
								IMB_scalefastImBuf(se->ibuf, (short)seqrectx, (short)seqrecty);
						}
					}
				}
				else if(seq->type < SEQ_EFFECT) {

					if(se->ibuf) {
						/* test if image too small: reload */
						if(se->ibuf->x < seqrectx || se->ibuf->y < seqrecty) {
							IMB_freeImBuf(se->ibuf);
							se->ibuf= 0;
							se->ok= 1;
						}
					}

					if(seq->type==SEQ_IMAGE) {
						if(se->ok && se->ibuf==0) {

							/* if playanim or render: no waitcursor */
							if((G.f & G_PLAYANIM)==0) waitcursor(1);

							strcpy(name, seq->strip->dir);
							strcat(name, se->name);
							BLI_convertstringcode(name, G.sce, G.scene->r.cfra);
							se->ibuf= IMB_loadiffname(name, IB_rect);

							if((G.f & G_PLAYANIM)==0) waitcursor(0);

							if(se->ibuf==0) se->ok= 0;
							else {
								if(se->ibuf->depth==32 && se->ibuf->zbuf==0) converttopremul(se->ibuf);
								seq->strip->orx= se->ibuf->x;
								seq->strip->ory= se->ibuf->y;
							}
						}
					}
					else if(seq->type==SEQ_MOVIE) {
						if(se->ok && se->ibuf==0) {

							/* if playanim r render: no waitcursor */
							if((G.f & G_PLAYANIM)==0) waitcursor(1);

							if(seq->anim==0) {
								strcpy(name, seq->strip->dir);
								strcat(name, seq->strip->stripdata->name);
								BLI_convertstringcode(name, G.sce, G.scene->r.cfra);

								seq->anim = openanim(name, IB_rect);
							}
							if(seq->anim) {
								se->ibuf = IMB_anim_absolute(seq->anim, se->nr);
							}

							if(se->ibuf==0) se->ok= 0;
							else {
								if(se->ibuf->depth==32) converttopremul(se->ibuf);
								seq->strip->orx= se->ibuf->x;
								seq->strip->ory= se->ibuf->y;
								if(seq->flag & SEQ_FILTERY) IMB_filtery(se->ibuf);
								if(seq->mul==0.0) seq->mul= 1.0;
								if(seq->mul != 1.0) multibuf(se->ibuf, seq->mul);
							}
							if((G.f & G_PLAYANIM)==0) waitcursor(0);
						}
					}
					else if(seq->type==SEQ_SCENE && se->ibuf==0) {
						View3D *vd;

						oldsce= G.scene;
						set_scene_bg(seq->scene);

						/* prevent eternal loop */
						doseq= G.scene->r.scemode & R_DOSEQ;
						G.scene->r.scemode &= ~R_DOSEQ;

						/* store stuffies */
						oldcfra= CFRA; CFRA= seq->sfra + se->nr;
						waitcursor(1);

						rectot= R.rectot; R.rectot= 0;
						oldx= R.rectx; oldy= R.recty;
						/* needed because current 3D window cannot define the layers, like in a background render */
						vd= G.vd;
						G.vd= 0;

						RE_initrender(NULL);
						if (!G.background) {
							mainwindow_make_active();
							if(R.r.mode & R_FIELDS) update_for_newframe_muted();
							R.flag= 0;

							free_filesel_spec(G.scene->r.pic);
						}

						se->ibuf= IMB_allocImBuf(R.rectx, R.recty, 32, IB_rect, 0);
						if(R.rectot) memcpy(se->ibuf->rect, R.rectot, 4*R.rectx*R.recty);
						if(R.rectz) {
							se->ibuf->zbuf= (int *)R.rectz;
							/* make sure ibuf frees it */
							se->ibuf->mall |= IB_zbuf;
							R.rectz= 0;
						}

						/* and restore */
						G.vd= vd;

						if((G.f & G_PLAYANIM)==0) waitcursor(0);
						CFRA= oldcfra;
						if(R.rectot) MEM_freeN(R.rectot);
						R.rectot= rectot;
						R.rectx=oldx; R.recty=oldy;
						G.scene->r.scemode |= doseq;
						set_scene_bg(oldsce);

						/* restore!! */
						R.rectx= seqrectx;
						R.recty= seqrecty;

						/* added because this flag is checked for
						 * movie writing when rendering an anim.
						 * very convoluted. fix. -zr
						 */
						R.r.imtype= G.scene->r.imtype;
					}

					/* size test */
					if(se->ibuf) {
						if(se->ibuf->x != seqrectx || se->ibuf->y != seqrecty ) {

							if (G.scene->r.mode & R_FIELDS) {

								if (seqrecty > 288) IMB_scalefieldImBuf(se->ibuf, (short)seqrectx, (short)seqrecty);
								else {
									IMB_de_interlace(se->ibuf);

									if(G.scene->r.mode & R_OSA)
										IMB_scaleImBuf(se->ibuf, (short)seqrectx, (short)seqrecty);
									else
										IMB_scalefastImBuf(se->ibuf, (short)seqrectx, (short)seqrecty);
								}
							}
							else {
								if(G.scene->r.mode & R_OSA)
									IMB_scaleImBuf(se->ibuf,(short)seqrectx, (short)seqrecty);
								else
									IMB_scalefastImBuf(se->ibuf, (short)seqrectx, (short)seqrecty);
							}
						}
					}
				}
			}
		}

		seq= seq->next;
	}
}

ImBuf *give_ibuf_seq(int cfra)
{
	Sequence **tseqar, **seqar;
	Sequence *seq, *seqfirst=0;/*  , *effirst=0; */
	Editing *ed;
	StripElem *se;
	int seqnr, totseq;

	/* we make recursively a 'stack' of sequences, these are
	 * sorted nicely as well.
	 * this method has been developed especially for stills before or after metas
	 */

	totseq= 0;
	ed= G.scene->ed;
	if(ed==0) return 0;
	do_seq_count_cfra(ed->seqbasep, &totseq, cfra);

	if(totseq==0) return 0;

	seqrectx= (G.scene->r.size*G.scene->r.xsch)/100;
	if(G.scene->r.mode & R_PANORAMA) seqrectx*= G.scene->r.xparts;
	seqrecty= (G.scene->r.size*G.scene->r.ysch)/100;


	/* tseqar is neede because in do_build_... the pointer changes */
	seqar= tseqar= MEM_callocN(sizeof(void *)*totseq, "seqar");

	/* this call loads and makes the ibufs */
	do_build_seqar_cfra(ed->seqbasep, &seqar, cfra);
	seqar= tseqar;

	for(seqnr=0; seqnr<totseq; seqnr++) {
		seq= seqar[seqnr];

		se= seq->curelem;
		if((seq->type != SEQ_SOUND) && (se)) {
			if(seq->type==SEQ_META) {

				/* bottom strip! */
				if(seqfirst==0) seqfirst= seq;
				else if(seqfirst->depth > seq->depth) seqfirst= seq;
				else if(seqfirst->machine > seq->machine) seqfirst= seq;

			}
			else if(seq->type & SEQ_EFFECT) {

				/* top strip! */
				if(seqfirst==0) seqfirst= seq;
				else if(seqfirst->depth > seq->depth) seqfirst= seq;
				else if(seqfirst->machine < seq->machine) seqfirst= seq;


			}
			else if(seq->type < SEQ_EFFECT) {	/* images */

				/* bottom strip! a feature that allows you to store junk in locations above */

				if(seqfirst==0) seqfirst= seq;
				else if(seqfirst->depth > seq->depth) seqfirst= seq;
				else if(seqfirst->machine > seq->machine) seqfirst= seq;

			}
		}
	}

	MEM_freeN(seqar);

	if(!seqfirst) return 0;
	if(!seqfirst->curelem) return 0;
	return seqfirst->curelem->ibuf;

}

void free_imbuf_effect_spec(int cfra)
{
	Sequence *seq;
	StripElem *se;
	Editing *ed;
	int a;

	ed= G.scene->ed;
	if(ed==0) return;

	WHILE_SEQ(&ed->seqbase) {

		if(seq->strip) {

			if(seq->type & SEQ_EFFECT) {
				se= seq->strip->stripdata;
				for(a=0; a<seq->len; a++, se++) {
					if(se==seq->curelem && se->ibuf) {
						IMB_freeImBuf(se->ibuf);
						se->ibuf= 0;
						se->ok= 1;
						se->se1= se->se2= se->se3= 0;
					}
				}
			}
		}
	}
	END_SEQ
}

void free_imbuf_seq_except(int cfra)
{
	Sequence *seq;
	StripElem *se;
	Editing *ed;
	int a;

	ed= G.scene->ed;
	if(ed==0) return;

	WHILE_SEQ(&ed->seqbase) {

		if(seq->strip) {

			if( seq->type==SEQ_META ) {
				;
			}
			else {
				se= seq->strip->stripdata;
				for(a=0; a<seq->len; a++, se++) {
					if(se!=seq->curelem && se->ibuf) {
						IMB_freeImBuf(se->ibuf);
						se->ibuf= 0;
						se->ok= 1;
						se->se1= se->se2= se->se3= 0;
					}
				}
			}

			if(seq->type==SEQ_MOVIE) {
				if(seq->startdisp > cfra || seq->enddisp < cfra) {
					if(seq->anim) {
						IMB_free_anim(seq->anim);
						seq->anim = 0;
					}
				}
			}
		}
	}
	END_SEQ
}

void free_imbuf_seq()
{
	Sequence *seq;
	StripElem *se;
	Editing *ed;
	int a;

	ed= G.scene->ed;
	if(ed==0) return;

	WHILE_SEQ(&ed->seqbase) {

		if(seq->strip) {

			if( seq->type==SEQ_META ) {
				;
			}
			else {
				se= seq->strip->stripdata;
				for(a=0; a<seq->len; a++, se++) {
					if(se->ibuf) {
						IMB_freeImBuf(se->ibuf);
						se->ibuf= 0;
						se->ok= 1;
						se->se1= se->se2= se->se3= 0;
					}
				}
			}

			if(seq->type==SEQ_MOVIE) {
				if(seq->anim) {
					IMB_free_anim(seq->anim);
					seq->anim = 0;
				}
			}
		}
	}
	END_SEQ
}

void do_render_seq()
{
/*  	static ImBuf *lastibuf=0; */
	ImBuf *ibuf;

	/* copy image into R.rectot */

	G.f |= G_PLAYANIM;	/* waitcursor patch */

	ibuf= give_ibuf_seq(CFRA);
	if(ibuf) {

		memcpy(R.rectot, ibuf->rect, 4*R.rectx*R.recty);

		/* if (ibuf->zbuf) { */
		/* 	if (R.rectz) freeN(R.rectz); */
		/* 	R.rectz = BLI_dupallocN(ibuf->zbuf); */
		/* } */

		free_imbuf_seq_except(CFRA);
	}
	G.f &= ~G_PLAYANIM;

}
