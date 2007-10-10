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
 * Contributor(s): Peter Schlaile <peter [at] schlaile [dot] de> 2005/2006
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#include <string.h>
#include <math.h>
#include <stdlib.h>

#include "MEM_guardedalloc.h"
#include "MEM_CacheLimiterC-Api.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "DNA_ipo_types.h"
#include "DNA_scene_types.h"
#include "DNA_sequence_types.h"
#include "DNA_view3d_types.h"

#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_ipo.h"
#include "BKE_main.h"
#include "BKE_scene.h"
#include "BKE_texture.h"
#include "BKE_utildefines.h"

#include "BIF_editsound.h"
#include "BIF_editseq.h"
#include "BSE_filesel.h"
#include "BSE_headerbuttons.h"
#include "BIF_interface.h"
#include "BIF_renderwin.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_toolbox.h"

#include "BSE_sequence.h"
#include "BSE_seqeffects.h"

#include "RE_pipeline.h"		// talks to entire render API

#include "blendef.h"

#include <pthread.h>

int seqrectx, seqrecty;

void free_stripdata(int len, StripElem *se)
{
	StripElem *seo;
	int a;

	seo= se;

	for(a=0; a<len; a++, se++) {
		if(se->ibuf && se->ok!=2) {
			IMB_freeImBuf(se->ibuf);
			se->ibuf = 0;
		}
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
	Sequence *last_seq = get_last_seq();

	if(seq->strip) free_strip(seq->strip);

	if(seq->anim) IMB_free_anim(seq->anim);
	if(seq->hdaudio) sound_close_hdaudio(seq->hdaudio);

	if (seq->type & SEQ_EFFECT) {
		struct SeqEffectHandle sh = get_sequence_effect(seq);

		sh.free(seq);
	}

	if(seq==last_seq) set_last_seq(NULL);

	MEM_freeN(seq);
}

/*
  **********************************************************************
  * build_seqar
  **********************************************************************
  * Build a complete array of _all_ sequencies (including those
  * in metastrips!)
  **********************************************************************
*/

static void do_seq_count(ListBase *seqbase, int *totseq)
{
	Sequence *seq;

	seq= seqbase->first;
	while(seq) {
		(*totseq)++;
		if(seq->seqbase.first) do_seq_count(&seq->seqbase, totseq);
		seq= seq->next;
	}
}

static void do_build_seqar(ListBase *seqbase, Sequence ***seqar, int depth)
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

	if(ed==NULL) return;
	set_last_seq(NULL);	/* clear_last_seq doesnt work, it screws up free_sequence */

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

		if (seq->seq1) {
			seq->start= seq->startdisp= MAX3(seq->seq1->startdisp, seq->seq2->startdisp, seq->seq3->startdisp);
			seq->enddisp= MIN3(seq->seq1->enddisp, seq->seq2->enddisp, seq->seq3->enddisp);
			seq->len= seq->enddisp - seq->startdisp;
		} else {
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

static void make_black_ibuf(ImBuf *ibuf)
{
	unsigned int *rect;
	float *rect_float;
	int tot;

	if(ibuf==0 || (ibuf->rect==0 && ibuf->rect_float==0)) return;

	tot= ibuf->x*ibuf->y;

	rect= ibuf->rect;
	rect_float = ibuf->rect_float;

	if (rect) {
		memset(rect,       0, tot * sizeof(char) * 4);
	}

	if (rect_float) {
		memset(rect_float, 0, tot * sizeof(float) * 4);
	}
}

static void multibuf(ImBuf *ibuf, float fmul)
{
	char *rt;
	float *rt_float;

	int a, mul, icol;

	mul= (int)(256.0*fmul);

	a= ibuf->x*ibuf->y;
	rt= (char *)ibuf->rect;
	rt_float = ibuf->rect_float;

	if (rt) {
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
	if (rt_float) {
		while(a--) {
			rt_float[0] *= fmul;
			rt_float[1] *= fmul;
			rt_float[2] *= fmul;
			rt_float[3] *= fmul;
			
			rt_float += 4;
		}
	}
}

static void do_effect(int cfra, Sequence *seq, StripElem *se)
{
	StripElem *se1, *se2, *se3;
	float fac, facf;
	int x, y;
	int early_out;
	struct SeqEffectHandle sh = get_sequence_effect(seq);

	if (!sh.execute) { /* effect not supported in this version... */
		make_black_ibuf(se->ibuf);
		return;
	}

	if(seq->ipo && seq->ipo->curve.first) {
		do_seq_ipo(seq);
		fac= seq->facf0;
		facf= seq->facf1;
	} else {
		sh.get_default_fac(seq, cfra, &fac, &facf);
	}

	if( !(G.scene->r.mode & R_FIELDS) ) facf = fac;

	early_out = sh.early_out(seq, fac, facf);

	if (early_out == -1) { /* no input needed */
		sh.execute(seq, cfra, fac, facf, se->ibuf->x, se->ibuf->y, 
			   0, 0, 0, se->ibuf);
		return;
	}

	switch (early_out) {
	case 0:
		if (se->se1==0 || se->se2==0 || se->se3==0) {
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

		if (   (se1==0 || se2==0 || se3==0)
		    || (se1->ibuf==0 || se2->ibuf==0 || se3->ibuf==0)) {
			make_black_ibuf(se->ibuf);
			return;
		}

		break;
	case 1:
		if (se->se1 == 0) {
			make_black_ibuf(se->ibuf);
			return;
		}

		/* if metastrip: other se's */
		if(se->se1->ok==2) se1= se->se1->se1;
		else se1= se->se1;

		if (se1 == 0 || se1->ibuf == 0) {
			make_black_ibuf(se->ibuf);
			return;
		}

		if (se->ibuf != se1->ibuf) {
			IMB_freeImBuf(se->ibuf);
			se->ibuf = se1->ibuf;
			IMB_refImBuf(se->ibuf);
		}
		return;
	case 2:
		if (se->se2 == 0) {
			make_black_ibuf(se->ibuf);
			return;
		}

		/* if metastrip: other se's */
		if(se->se2->ok==2) se2= se->se2->se1;
		else se2= se->se2;

		if (se2 == 0 || se2->ibuf == 0) {
			make_black_ibuf(se->ibuf);
			return;
		}
		if (se->ibuf != se2->ibuf) {
			IMB_freeImBuf(se->ibuf);
			se->ibuf = se2->ibuf;
			IMB_refImBuf(se->ibuf);
		}
		return;
	default:
		make_black_ibuf(se->ibuf);
		return;
	}

	x= se2->ibuf->x;
	y= se2->ibuf->y;

	if (!se1->ibuf->rect_float && se->ibuf->rect_float) {
		IMB_float_from_rect(se1->ibuf);
	}
	if (!se2->ibuf->rect_float && se->ibuf->rect_float) {
		IMB_float_from_rect(se2->ibuf);
	}

	if (!se1->ibuf->rect && !se->ibuf->rect_float) {
		IMB_rect_from_float(se1->ibuf);
	}
	if (!se2->ibuf->rect && !se->ibuf->rect_float) {
		IMB_rect_from_float(se2->ibuf);
	}

	sh.execute(seq, cfra, fac, facf, x, y, se1->ibuf, se2->ibuf, se3->ibuf,
		   se->ibuf);
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

	if(seq->flag&SEQ_REVERSE_FRAMES)	{	
		/*reverse frame in this sequence */
		if(cfra <= seq->start) nr= seq->len-1;
		else if(cfra >= seq->start+seq->len-1) nr= 0;
		else nr= (seq->start + seq->len) - cfra;
	} else {
		if(cfra <= seq->start) nr= 0;
		else if(cfra >= seq->start+seq->len-1) nr= seq->len-1;
		else nr= cfra-seq->start;
	}
	if (seq->strobe < 1.0) seq->strobe = 1.0;
	if (seq->strobe > 1.0) {
		nr -= (int)fmod((double)nr, (double)seq->strobe);
	}
	
	se+= nr; /* don't get confused by the increment, this is the same as strip->stripdata[nr], which works on some compilers...*/
	se->nr= nr;
	
	return se;
}

static int evaluate_seq_frame_gen(
	Sequence ** seq_arr, ListBase *seqbase, int cfra)
{
	Sequence *seq;
	int totseq=0;

	memset(seq_arr, 0, sizeof(Sequence*) * MAXSEQ);

	seq= seqbase->first;
	while(seq) {
		if(seq->startdisp <=cfra && seq->enddisp > cfra) {
			seq_arr[seq->machine]= seq;
			totseq++;
		}
		seq= seq->next;
	}

	return totseq;
}

int evaluate_seq_frame(int cfra)
{
       Editing *ed;
       Sequence *seq_arr[MAXSEQ+1];

       ed= G.scene->ed;
       if(ed==0) return 0;
	
       return evaluate_seq_frame_gen(seq_arr, ed->seqbasep, cfra);

}

Sequence *get_shown_sequence(ListBase * seqbasep, int cfra, int chanshown)
{
	Sequence *seq, *seqim, *seqeff;
	Sequence *seq_arr[MAXSEQ+1];
	int b;

	seq = 0;

	if (chanshown > MAXSEQ) {
		return 0;
	}

	if(evaluate_seq_frame_gen(seq_arr, seqbasep, cfra)) {
		if (chanshown > 0) {
			return seq_arr[chanshown];
		}

		/* we take the upper effect strip or 
		   the lowest imagestrip/metastrip */
		seqim= seqeff= 0;

		for(b=1; b<MAXSEQ; b++) {
			if(seq_arr[b]) {
				seq= seq_arr[b];
				if(seq->type & SEQ_EFFECT) {
					if(seqeff==0) seqeff= seq;
					else if(seqeff->machine < seq->machine)
						seqeff= seq;
				} else if (seq->type != SEQ_RAM_SOUND && seq->type != SEQ_HD_SOUND) {
					if(seqim==0) seqim= seq;
					else if(seqim->machine > seq->machine)
						seqim= seq;
				}
			}
		}
		if(seqeff) seq= seqeff;
		else if(seqim) seq= seqim;
		else seq= 0;
	}
	
	return seq;
}
 
static Sequence * get_shown_seq_from_metastrip(Sequence * seqm, int cfra)
{
	return get_shown_sequence(&seqm->seqbase, cfra, 0);
}

void set_meta_stripdata(Sequence *seqm)
{
	Sequence *seq;
	StripElem *se;
	int a, cfra;

	/* sets all ->se1 pointers in stripdata, to read the ibuf from it */

	se= seqm->strip->stripdata;
	for(a=0; a<seqm->len; a++, se++) {
		cfra= a+seqm->start;
		seq = get_shown_seq_from_metastrip(seqm, cfra);
		if (seq) {
			se->se1= give_stripelem(seq, cfra);
		} else { 
			se->se1= 0;
		}
	}
}

static void do_build_seq_ibuf(Sequence * seq, int cfra)
{
	StripElem *se = seq->curelem;
	char name[FILE_MAXDIR+FILE_MAXFILE];

	if(seq->type == SEQ_META) {
		se->ok= 2;
		if(se->se1==0) set_meta_stripdata(seq);
		if(se->se1) {
			se->ibuf= se->se1->ibuf;
		}
	} else if(seq->type == SEQ_RAM_SOUND || seq->type == SEQ_HD_SOUND) {
		se->ok= 2;
	} else if(seq->type & SEQ_EFFECT) {
			
		/* test if image is too small or discarded from cache: reload */
		if(se->ibuf) {
			if(se->ibuf->x < seqrectx || se->ibuf->y < seqrecty || !(se->ibuf->rect || se->ibuf->rect_float)) {
				IMB_freeImBuf(se->ibuf);
				se->ibuf= 0;
			}
		}
			
		/* should the effect be recalculated? */
		
		if(se->ibuf==0 
		   || (seq->seq1 && se->se1 != seq->seq1->curelem) 
		   || (seq->seq2 && se->se2 != seq->seq2->curelem) 
		   || (seq->seq3 && se->se3 != seq->seq3->curelem)) {
			if (seq->seq1) se->se1= seq->seq1->curelem;
			if (seq->seq2) se->se2= seq->seq2->curelem;
			if (seq->seq3) se->se3= seq->seq3->curelem;
			
			if(se->ibuf==NULL) {
				/* if one of two first inputs are rectfloat, output is float too */
				if((se->se1 && se->se1->ibuf && se->se1->ibuf->rect_float) ||
				   (se->se2 && se->se2->ibuf && se->se2->ibuf->rect_float))
					se->ibuf= IMB_allocImBuf((short)seqrectx, (short)seqrecty, 32, IB_rectfloat, 0);
				else
					se->ibuf= IMB_allocImBuf((short)seqrectx, (short)seqrecty, 32, IB_rect, 0);
			}
			
			do_effect(cfra, seq, se);
		}
		
		/* test size */
		if(se->ibuf) {
			if(se->ibuf->x != seqrectx || se->ibuf->y != seqrecty ) {
				if(G.scene->r.mode & R_OSA) {
					IMB_scaleImBuf(se->ibuf, (short)seqrectx, (short)seqrecty);
				} else {
					IMB_scalefastImBuf(se->ibuf, (short)seqrectx, (short)seqrecty);
				}
			}
		}
	} else if(seq->type < SEQ_EFFECT) {
		if(se->ibuf) {
			/* test if image too small 
			   or discarded from cache: reload */
			if(se->ibuf->x < seqrectx || se->ibuf->y < seqrecty || !(se->ibuf->rect || se->ibuf->rect_float)) {
				IMB_freeImBuf(se->ibuf);
				se->ibuf= 0;
				se->ok= 1;
			}
		}
		
		if(seq->type==SEQ_IMAGE) {
			if(se->ok && se->ibuf==0) {
				/* if playanim or render: 
				   no waitcursor */
				if((G.f & G_PLAYANIM)==0) 
					waitcursor(1);
				
				strncpy(name, seq->strip->dir, FILE_MAXDIR-1);
				strncat(name, se->name, FILE_MAXFILE);
				BLI_convertstringcode(name, G.sce, G.scene->r.cfra);
				se->ibuf= IMB_loadiffname(name, IB_rect);
				
				if((G.f & G_PLAYANIM)==0) 
					waitcursor(0);
				
				if(se->ibuf==0) se->ok= 0;
				else {
					if(seq->flag & SEQ_MAKE_PREMUL) {
						if(se->ibuf->depth==32 && se->ibuf->zbuf==0) converttopremul(se->ibuf);
					}
					seq->strip->orx= se->ibuf->x;
					seq->strip->ory= se->ibuf->y;
					if(seq->flag & SEQ_FILTERY) IMB_filtery(se->ibuf);
					if(seq->flag & SEQ_FLIPX) IMB_flipx(se->ibuf);
					if(seq->flag & SEQ_FLIPY) IMB_flipy(se->ibuf);
					if(seq->mul==0.0) seq->mul= 1.0;
					if(seq->mul != 1.0) multibuf(se->ibuf, seq->mul);
				}
			}
		}
		else if(seq->type==SEQ_MOVIE) {
			if(se->ok && se->ibuf==0) {
				if(seq->anim==0) {
					strncpy(name, seq->strip->dir, FILE_MAXDIR-1);
					strncat(name, seq->strip->stripdata->name, FILE_MAXFILE-1);
					BLI_convertstringcode(name, G.sce, G.scene->r.cfra);
					
					seq->anim = openanim(name, IB_rect);
				}
				if(seq->anim) {
					IMB_anim_set_preseek(seq->anim, seq->anim_preseek);
					se->ibuf = IMB_anim_absolute(seq->anim, se->nr);
				}
				
				if(se->ibuf==0) se->ok= 0;
				else {
					if(seq->flag & SEQ_MAKE_PREMUL) {
						if(se->ibuf->depth==32) converttopremul(se->ibuf);
					}
					seq->strip->orx= se->ibuf->x;
					seq->strip->ory= se->ibuf->y;
					if(seq->flag & SEQ_FILTERY) IMB_filtery(se->ibuf);
					if(seq->mul==0.0) seq->mul= 1.0;
					if(seq->mul != 1.0) multibuf(se->ibuf, seq->mul);
				}
			}
		} else if(seq->type==SEQ_SCENE && se->ibuf==NULL && seq->scene) {	// scene can be NULL after deletions
			int oldcfra = CFRA;
			Scene *sce= seq->scene, *oldsce= G.scene;
			Render *re;
			RenderResult rres;
			int doseq, rendering= G.rendering;
			char scenename[64];
			
			waitcursor(1);
			
			/* Hack! This function can be called from do_render_seq(), in that case
			   the seq->scene can already have a Render initialized with same name, 
			   so we have to use a default name. (compositor uses G.scene name to
			   find render).
			   However, when called from within the UI (image preview in sequencer)
			   we do want to use scene Render, that way the render result is defined
			   for display in render/imagewindow */
			if(rendering) {
				BLI_strncpy(scenename, sce->id.name+2, 64);
				strcpy(sce->id.name+2, " do_build_seq_ibuf");
			}
			re= RE_NewRender(sce->id.name);
			
			/* prevent eternal loop */
			doseq= G.scene->r.scemode & R_DOSEQ;
			G.scene->r.scemode &= ~R_DOSEQ;
			
			BIF_init_render_callbacks(re, 0);	/* 0= no display callbacks */
			
			/* hrms, set_scene still needed? work on that... */
			if(sce!=oldsce) set_scene_bg(sce);
			RE_BlenderFrame(re, sce, seq->sfra + se->nr);
			if(sce!=oldsce) set_scene_bg(oldsce);
			
			/* UGLY WARNING, it is set to zero in  RE_BlenderFrame */
			G.rendering= rendering;
			if(rendering)
				BLI_strncpy(sce->id.name+2, scenename, 64);
			
			RE_GetResultImage(re, &rres);
			
			if(rres.rectf) {
				se->ibuf= IMB_allocImBuf(rres.rectx, rres.recty, 32, IB_rectfloat, 0);
				memcpy(se->ibuf->rect_float, rres.rectf, 4*sizeof(float)*rres.rectx*rres.recty);
				if(rres.rectz) {
					addzbuffloatImBuf(se->ibuf);
					memcpy(se->ibuf->zbuf_float, rres.rectz, sizeof(float)*rres.rectx*rres.recty);
				}
			} else if (rres.rect32) {
				se->ibuf= IMB_allocImBuf(rres.rectx, rres.recty, 32, IB_rect, 0);
				memcpy(se->ibuf->rect, rres.rect32, 4*rres.rectx*rres.recty);
			}
			
			BIF_end_render_callbacks();
			
			/* restore */
			G.scene->r.scemode |= doseq;
			
			if((G.f & G_PLAYANIM)==0) /* bad, is set on do_render_seq */
				waitcursor(0);
			CFRA = oldcfra;
		}
		
		/* size test */
		if(se->ibuf) {
			if(se->ibuf->x != seqrectx || se->ibuf->y != seqrecty ) {
				
				if (0) { // G.scene->r.mode & R_FIELDS) {
					
					if (seqrecty > 288) 
						IMB_scalefieldImBuf(se->ibuf, (short)seqrectx, (short)seqrecty);
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
	if (se->ibuf) {
		IMB_cache_limiter_insert(se->ibuf);
		IMB_cache_limiter_ref(se->ibuf);
		IMB_cache_limiter_touch(se->ibuf);
	}
}

static void do_build_seq_recursively(Sequence * seq, int cfra);

static void do_effect_seq_recursively(int cfra, Sequence * seq, StripElem *se)
{
	float fac, facf;
	struct SeqEffectHandle sh = get_sequence_effect(seq);
	int early_out;

	if(seq->ipo && seq->ipo->curve.first) {
		do_seq_ipo(seq);
		fac= seq->facf0;
		facf= seq->facf1;
	} else {
		sh.get_default_fac(seq, cfra, &fac, &facf);
	} 

	if( G.scene->r.mode & R_FIELDS ); else facf= fac;
	
	early_out = sh.early_out(seq, fac, facf);
	switch (early_out) {
	case -1:
		/* no input needed */
		break;
	case 0:
		do_build_seq_recursively(seq->seq1, cfra);
		do_build_seq_recursively(seq->seq2, cfra);
		if (seq->seq3) {
			do_build_seq_recursively(seq->seq3, cfra);
		}
		break;
	case 1:
		do_build_seq_recursively(seq->seq1, cfra);
		break;
	case 2:
		do_build_seq_recursively(seq->seq2, cfra);
		break;
	}


	do_build_seq_ibuf(seq, cfra);

	/* children are not needed anymore ... */

	switch (early_out) {
	case 0:
		if (seq->seq1->curelem && seq->seq1->curelem->ibuf)
			IMB_cache_limiter_unref(seq->seq1->curelem->ibuf);
		if (seq->seq2->curelem && seq->seq2->curelem->ibuf)
			IMB_cache_limiter_unref(seq->seq2->curelem->ibuf);
		if (seq->seq3) {
			if (seq->seq3->curelem && seq->seq3->curelem->ibuf)
				IMB_cache_limiter_unref(
					seq->seq3->curelem->ibuf);
		}
		break;
	case 1:
		if (seq->seq1->curelem && seq->seq1->curelem->ibuf)
			IMB_cache_limiter_unref(seq->seq1->curelem->ibuf);
		break;
	case 2:
		if (seq->seq2->curelem && seq->seq2->curelem->ibuf)
			IMB_cache_limiter_unref(seq->seq2->curelem->ibuf);
		break;
	}
}

static void do_build_seq_recursively_impl(Sequence * seq, int cfra)
{
	StripElem *se;

	se = seq->curelem = give_stripelem(seq, cfra);

	if(se) {
		int unref_meta = FALSE;
		if(seq->seqbase.first) {
			Sequence * seqmshown= get_shown_seq_from_metastrip(seq, cfra);
			if (seqmshown) {
				if(cfra< seq->start) 
					do_build_seq_recursively(seqmshown, seq->start);
				else if(cfra> seq->start+seq->len-1) 
					do_build_seq_recursively(seqmshown, seq->start + seq->len-1);
				else do_build_seq_recursively(seqmshown, cfra);

				unref_meta = TRUE;
			}
		}

		if (seq->type & SEQ_EFFECT) {
			do_effect_seq_recursively(cfra, seq, se);
		} else {
			do_build_seq_ibuf(seq, cfra);
		}

		if(unref_meta && seq->curelem->ibuf) {
			IMB_cache_limiter_unref(seq->curelem->ibuf);
		}
	}
}

/* FIXME:
   
If cfra was float throughout blender (especially in the render
pipeline) one could even _render_ with subframe precision
instead of faking using the blend code below...

*/

static void do_handle_speed_effect(Sequence * seq, int cfra)
{
	SpeedControlVars * s = (SpeedControlVars *)seq->effectdata;
	int nr = cfra - seq->start;
	float f_cfra;
	int cfra_left;
	int cfra_right;
	StripElem * se = 0;
	StripElem * se1 = 0;
	StripElem * se2 = 0;
	
	sequence_effect_speed_rebuild_map(seq, 0);
	
	f_cfra = seq->start + s->frameMap[nr];
	
	cfra_left = (int) floor(f_cfra);
	cfra_right = (int) ceil(f_cfra);

	se = seq->curelem = give_stripelem(seq, cfra);

	if (cfra_left == cfra_right || 
	    (s->flags & SEQ_SPEED_BLEND) == 0) {
		if(se->ibuf) {
			if(se->ibuf->x < seqrectx || se->ibuf->y < seqrecty 
			   || !(se->ibuf->rect || se->ibuf->rect_float)) {
				IMB_freeImBuf(se->ibuf);
				se->ibuf= 0;
			}
		}

		if (se->ibuf == NULL) {
			do_build_seq_recursively_impl(seq->seq1, cfra_left);

			se1 = seq->seq1->curelem;

			if((se1 && se1->ibuf && se1->ibuf->rect_float))
				se->ibuf= IMB_allocImBuf((short)seqrectx, (short)seqrecty, 32, IB_rectfloat, 0);
			else
				se->ibuf= IMB_allocImBuf((short)seqrectx, (short)seqrecty, 32, IB_rect, 0);

			if (se1 == 0 || se1->ibuf == 0) {
				make_black_ibuf(se->ibuf);
			} else {
				if (se->ibuf != se1->ibuf) {
					if (se->ibuf) {
						IMB_freeImBuf(se->ibuf);
					}

					se->ibuf = se1->ibuf;
					IMB_refImBuf(se->ibuf);
				}
			}
		}
	} else {
		struct SeqEffectHandle sh;

		if(se->ibuf) {
			if(se->ibuf->x < seqrectx || se->ibuf->y < seqrecty 
			   || !(se->ibuf->rect || se->ibuf->rect_float)) {
				IMB_freeImBuf(se->ibuf);
				se->ibuf= 0;
			}
		}

		if (se->ibuf == NULL) {
			do_build_seq_recursively_impl(seq->seq1, cfra_left);
			se1 = seq->seq1->curelem;
			do_build_seq_recursively_impl(seq->seq1, cfra_right);
			se2 = seq->seq1->curelem;


			if((se1 && se1->ibuf && se1->ibuf->rect_float))
				se->ibuf= IMB_allocImBuf((short)seqrectx, (short)seqrecty, 32, IB_rectfloat, 0);
			else
				se->ibuf= IMB_allocImBuf((short)seqrectx, (short)seqrecty, 32, IB_rect, 0);
			
			if (!se1 || !se2) {
				make_black_ibuf(se->ibuf);
			} else {
				sh = get_sequence_effect(seq);

				sh.execute(seq, cfra, 
					   f_cfra - (float) cfra_left, 
					   f_cfra - (float) cfra_left, 
					   se->ibuf->x, se->ibuf->y, 
					   se1->ibuf, se2->ibuf, 0, se->ibuf);
			}
		}

	}

	/* caller expects this to be referenced, so do it! */
	if (se->ibuf) {
		IMB_cache_limiter_insert(se->ibuf);
		IMB_cache_limiter_ref(se->ibuf);
		IMB_cache_limiter_touch(se->ibuf);
	}

	/* children are no longer needed */
	if (se1 && se1->ibuf)
		IMB_cache_limiter_unref(se1->ibuf);
	if (se2 && se2->ibuf)
		IMB_cache_limiter_unref(se2->ibuf);
}

/* 
 * build all ibufs recursively
 * 
 * if successfull, seq->curelem->ibuf contains the (referenced!) imbuf
 * that means: you _must_ call 
 *
 * IMB_cache_limiter_unref(seq->curelem->ibuf);
 * 
 * if seq->curelem exists!
 * 
 */

static void do_build_seq_recursively(Sequence * seq, int cfra)
{
	if (seq->type == SEQ_SPEED) {
		do_handle_speed_effect(seq, cfra);
	} else {
		do_build_seq_recursively_impl(seq, cfra);
	}
}

ImBuf *give_ibuf_seq(int rectx, int recty, int cfra, int chanshown)
{
	Sequence *seqfirst=0;
	Editing *ed;
	int count;
	ListBase *seqbasep;

	ed= G.scene->ed;
	if(ed==0) return 0;

	count = BLI_countlist(&ed->metastack);
	if((chanshown < 0) && (count > 0)) {
		count = MAX2(count + chanshown, 0);
		seqbasep= ((MetaStack*)BLI_findlink(&ed->metastack, count))->oldbasep;
	} else {
		seqbasep= ed->seqbasep;
	}

	seqrectx= rectx;	/* bad bad global! */
	seqrecty= recty;

	seqfirst = get_shown_sequence(seqbasep, cfra, chanshown);

	if (!seqfirst) {
		return 0;
	}

	do_build_seq_recursively(seqfirst, cfra);

	if(!seqfirst->curelem) { 
		return 0;
	}

	if (seqfirst->curelem->ibuf) {
		IMB_cache_limiter_unref(seqfirst->curelem->ibuf);
	}

	return seqfirst->curelem->ibuf;

}

/* threading api */

static ListBase running_threads;
static ListBase prefetch_wait;
static ListBase prefetch_done;

static pthread_mutex_t queue_lock          = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t wakeup_lock         = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t  wakeup_cond         = PTHREAD_COND_INITIALIZER;

static pthread_mutex_t prefetch_ready_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t  prefetch_ready_cond = PTHREAD_COND_INITIALIZER;

static pthread_mutex_t frame_done_lock     = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t  frame_done_cond     = PTHREAD_COND_INITIALIZER;

static volatile int seq_thread_shutdown = FALSE;
static volatile int seq_last_given_monoton_cfra = 0;
static int monoton_cfra = 0;

typedef struct PrefetchThread {
	struct PrefetchThread *next, *prev;
	struct PrefetchQueueElem *current;
	pthread_t pthread;
	int running;
} PrefetchThread;

typedef struct PrefetchQueueElem {
	struct PrefetchQueueElem *next, *prev;
	
	int rectx;
	int recty;
	int cfra;
	int chanshown;

	int monoton_cfra;

	struct ImBuf * ibuf;
} PrefetchQueueElem;


static void * seq_prefetch_thread(void * This_)
{
	PrefetchThread * This = This_;

	while (!seq_thread_shutdown) {
		PrefetchQueueElem * e;
		int s_last;

		pthread_mutex_lock(&queue_lock);
		e = prefetch_wait.first;
		if (e) {
			BLI_remlink(&prefetch_wait, e);
		}
		s_last = seq_last_given_monoton_cfra;

		This->current = e;

		pthread_mutex_unlock(&queue_lock);

		if (!e) {
			pthread_mutex_lock(&prefetch_ready_lock);

			This->running = FALSE;

			pthread_cond_signal(&prefetch_ready_cond);
			pthread_mutex_unlock(&prefetch_ready_lock);

			pthread_mutex_lock(&wakeup_lock);
			if (!seq_thread_shutdown) {
				pthread_cond_wait(&wakeup_cond, &wakeup_lock);
			}
			pthread_mutex_unlock(&wakeup_lock);
			continue;
		}

		This->running = TRUE;
		
		if (e->cfra >= s_last) { 
			e->ibuf = give_ibuf_seq(e->rectx, e->recty, e->cfra, 
						e->chanshown);
		}

		if (e->ibuf) {
			IMB_cache_limiter_ref(e->ibuf);
		}

		pthread_mutex_lock(&queue_lock);

		BLI_addtail(&prefetch_done, e);

		for (e = prefetch_wait.first; e; e = e->next) {
			if (s_last > e->monoton_cfra) {
				BLI_remlink(&prefetch_wait, e);
				MEM_freeN(e);
			}
		}

		for (e = prefetch_done.first; e; e = e->next) {
			if (s_last > e->monoton_cfra) {
				if (e->ibuf) {
					IMB_cache_limiter_unref(e->ibuf);
				}
				BLI_remlink(&prefetch_done, e);
				MEM_freeN(e);
			}
		}

		pthread_mutex_unlock(&queue_lock);

		pthread_mutex_lock(&frame_done_lock);
		pthread_cond_signal(&frame_done_cond);
		pthread_mutex_unlock(&frame_done_lock);
	}
	return 0;
}

void seq_start_threads()
{
	int i;

	running_threads.first = running_threads.last = NULL;
	prefetch_wait.first = prefetch_wait.last = NULL;
	prefetch_done.first = prefetch_done.last = NULL;

	seq_thread_shutdown = FALSE;
	seq_last_given_monoton_cfra = monoton_cfra = 0;

	/* since global structures are modified during the processing
	   of one frame, only one render thread is currently possible... 

	   (but we code, in the hope, that we can remove this restriction
	   soon...)
	*/

	fprintf(stderr, "SEQ-THREAD: seq_start_threads\n");

	for (i = 0; i < 1; i++) {
		PrefetchThread *t = MEM_callocN(sizeof(PrefetchThread), 
						"prefetch_thread");
		t->running = TRUE;
		BLI_addtail(&running_threads, t);

		pthread_create(&t->pthread, NULL, seq_prefetch_thread, t);
	}
}

void seq_stop_threads()
{
	PrefetchThread *tslot;
	PrefetchQueueElem * e;

	fprintf(stderr, "SEQ-THREAD: seq_stop_threads()\n");

	if (seq_thread_shutdown) {
		fprintf(stderr, "SEQ-THREAD: ... already stopped\n");
		return;
	}
	
	pthread_mutex_lock(&wakeup_lock);

	seq_thread_shutdown = TRUE;

        pthread_cond_broadcast(&wakeup_cond);
        pthread_mutex_unlock(&wakeup_lock);

	for(tslot = running_threads.first; tslot; tslot= tslot->next) {
		pthread_join(tslot->pthread, NULL);
	}


	for (e = prefetch_wait.first; e; e = e->next) {
		BLI_remlink(&prefetch_wait, e);
		MEM_freeN(e);
	}

	for (e = prefetch_done.first; e; e = e->next) {
		if (e->ibuf) {
			IMB_cache_limiter_unref(e->ibuf);
		}
		BLI_remlink(&prefetch_done, e);
		MEM_freeN(e);
	}

	BLI_freelistN(&running_threads);
}

void give_ibuf_prefetch_request(int rectx, int recty, int cfra, int chanshown)
{
	PrefetchQueueElem * e;
	if (seq_thread_shutdown) {
		return;
	}

	e = MEM_callocN(sizeof(PrefetchQueueElem), "prefetch_queue_elem");
	e->rectx = rectx;
	e->recty = recty;
	e->cfra = cfra;
	e->chanshown = chanshown;
	e->monoton_cfra = monoton_cfra++;

	pthread_mutex_lock(&queue_lock);
	BLI_addtail(&prefetch_wait, e);
	pthread_mutex_unlock(&queue_lock);
	
	pthread_mutex_lock(&wakeup_lock);
	pthread_cond_signal(&wakeup_cond);
	pthread_mutex_unlock(&wakeup_lock);
}

void seq_wait_for_prefetch_ready()
{
	PrefetchThread *tslot;

	if (seq_thread_shutdown) {
		return;
	}

	fprintf(stderr, "SEQ-THREAD: rendering prefetch frames...\n");

	pthread_mutex_lock(&prefetch_ready_lock);

	for(;;) {
		for(tslot = running_threads.first; tslot; tslot= tslot->next) {
			if (tslot->running) {
				break;
			}
		}
		if (!tslot) {
			break;
		}
		pthread_cond_wait(&prefetch_ready_cond, &prefetch_ready_lock);
	}

	pthread_mutex_unlock(&prefetch_ready_lock);

	fprintf(stderr, "SEQ-THREAD: prefetch done\n");
}

ImBuf * give_ibuf_threaded(int rectx, int recty, int cfra, int chanshown)
{
	PrefetchQueueElem * e = 0;
	int found_something = FALSE;

	if (seq_thread_shutdown) {
		return give_ibuf_seq(rectx, recty, cfra, chanshown);
	}

	while (!e) {
		int success = FALSE;
		pthread_mutex_lock(&queue_lock);

		for (e = prefetch_done.first; e; e = e->next) {
			if (cfra == e->cfra &&
			    chanshown == e->chanshown &&
			    rectx == e->rectx && 
			    recty == e->recty) {
				success = TRUE;
				found_something = TRUE;
				break;
			}
		}

		if (!e) {
			for (e = prefetch_wait.first; e; e = e->next) {
				if (cfra == e->cfra &&
				    chanshown == e->chanshown &&
				    rectx == e->rectx && 
				    recty == e->recty) {
					found_something = TRUE;
					break;
				}
			}
		}

		if (!e) {
			PrefetchThread *tslot;

			for(tslot = running_threads.first; 
			    tslot; tslot= tslot->next) {
				if (tslot->current &&
				    cfra == tslot->current->cfra &&
				    chanshown == tslot->current->chanshown &&
				    rectx == tslot->current->rectx && 
				    recty == tslot->current->recty) {
					found_something = TRUE;
					break;
				}
			}
		}

		/* e->ibuf is unrefed by render thread on next round. */

		if (e) {
			seq_last_given_monoton_cfra = e->monoton_cfra;
		}

		pthread_mutex_unlock(&queue_lock);

		if (!success) {
			e = NULL;

			if (!found_something) {
				fprintf(stderr, 
					"SEQ-THREAD: Requested frame "
					"not in queue ???\n");
				break;
			}
			pthread_mutex_lock(&frame_done_lock);
			pthread_cond_wait(&frame_done_cond, &frame_done_lock);
			pthread_mutex_unlock(&frame_done_lock);
		}
	}
	
	return e ? e->ibuf : 0;
}

/* Functions to free imbuf and anim data on changes */

static void free_imbuf_strip_elem(StripElem *se)
{
	if (se->ibuf) {
		if (se->ok != 2)
			IMB_freeImBuf(se->ibuf);
		se->ibuf= 0;
		se->ok= 1;
		se->se1= se->se2= se->se3= 0;
	}
}

static void free_anim_seq(Sequence *seq)
{
	if(seq->anim) {
		IMB_free_anim(seq->anim);
		seq->anim = 0;
	}
}

void free_imbuf_seq_except(int cfra)
{
	Editing *ed= G.scene->ed;
	Sequence *seq;
	StripElem *se;
	int a;

	if(ed==0) return;

	WHILE_SEQ(&ed->seqbase) {
		if(seq->strip) {
			for(a=0, se= seq->strip->stripdata; a<seq->len; a++, se++)
				if(se!=seq->curelem)
					free_imbuf_strip_elem(se);

			if(seq->type==SEQ_MOVIE)
				if(seq->startdisp > cfra || seq->enddisp < cfra)
					free_anim_seq(seq);
		}
	}
	END_SEQ
}

void free_imbuf_seq()
{
	Editing *ed= G.scene->ed;
	Sequence *seq;
	StripElem *se;
	int a;

	if(ed==0) return;

	WHILE_SEQ(&ed->seqbase) {
		if(seq->strip) {
			for(a=0, se= seq->strip->stripdata; a<seq->len; a++, se++)
				free_imbuf_strip_elem(se);

			if(seq->type==SEQ_MOVIE)
				free_anim_seq(seq);
			if(seq->type==SEQ_SPEED) {
				sequence_effect_speed_rebuild_map(seq, 1);
			}
		}
	}
	END_SEQ
}

void free_imbuf_seq_with_ipo(struct Ipo *ipo)
{
	/* force update of all sequences with this ipo, on ipo changes */
	Editing *ed= G.scene->ed;
	Sequence *seq;

	if(ed==0) return;

	WHILE_SEQ(&ed->seqbase) {
		if(seq->ipo == ipo) {
			update_changed_seq_and_deps(seq, 0, 1);
			if(seq->type == SEQ_SPEED) {
				sequence_effect_speed_rebuild_map(seq, 1);
			}
		}
	}
	END_SEQ
}

static int update_changed_seq_recurs(Sequence *seq, Sequence *changed_seq, int len_change, int ibuf_change)
{
	Sequence *subseq;
	int a, free_imbuf = 0;
	StripElem *se;

	/* recurs downwards to see if this seq depends on the changed seq */

	if(seq == NULL)
		return 0;

	if(seq == changed_seq)
		free_imbuf = 1;
	
	for(subseq=seq->seqbase.first; subseq; subseq=subseq->next)
		if(update_changed_seq_recurs(subseq, changed_seq, len_change, ibuf_change))
			free_imbuf = 1;
	
	if(seq->seq1)
		if(update_changed_seq_recurs(seq->seq1, changed_seq, len_change, ibuf_change))
			free_imbuf = 1;
	if(seq->seq2 && (seq->seq2 != seq->seq1))
		if(update_changed_seq_recurs(seq->seq2, changed_seq, len_change, ibuf_change))
			free_imbuf = 1;
	if(seq->seq3 && (seq->seq3 != seq->seq1) && (seq->seq3 != seq->seq2))
		if(update_changed_seq_recurs(seq->seq3, changed_seq, len_change, ibuf_change))
			free_imbuf = 1;
	
	if(free_imbuf) {
		if(ibuf_change) {
			for(a=0, se= seq->strip->stripdata; a<seq->len; a++, se++)
				free_imbuf_strip_elem(se);
		
			if(seq->type==SEQ_MOVIE)
				free_anim_seq(seq);
			if(seq->type == SEQ_SPEED) {
				sequence_effect_speed_rebuild_map(seq, 1);
			}
		}

		if(len_change)
			calc_sequence(seq);
	}
	
	return free_imbuf;
}

void update_changed_seq_and_deps(Sequence *changed_seq, int len_change, int ibuf_change)
{
	Editing *ed= G.scene->ed;
	Sequence *seq;

	if (!ed) return;

	for (seq=ed->seqbase.first; seq; seq=seq->next)
		update_changed_seq_recurs(seq, changed_seq, len_change, ibuf_change);
}

/* bad levell call... */
void do_render_seq(RenderResult *rr, int cfra)
{
	ImBuf *ibuf;

	G.f |= G_PLAYANIM;	/* waitcursor patch */

	ibuf= give_ibuf_seq(rr->rectx, rr->recty, cfra, 0);
	
	if(ibuf) {
		
		if(ibuf->rect_float) {
			if (!rr->rectf)
				rr->rectf= MEM_mallocN(4*sizeof(float)*rr->rectx*rr->recty, "render_seq rectf");
			
			memcpy(rr->rectf, ibuf->rect_float, 4*sizeof(float)*rr->rectx*rr->recty);
			
			/* TSK! Since sequence render doesn't free the *rr render result, the old rect32
			   can hang around when sequence render has rendered a 32 bits one before */
			if(rr->rect32) {
				MEM_freeN(rr->rect32);
				rr->rect32= NULL;
			}
		}
		else if(ibuf->rect) {
			if (!rr->rect32)
				rr->rect32= MEM_mallocN(sizeof(int)*rr->rectx*rr->recty, "render_seq rect");

			memcpy(rr->rect32, ibuf->rect, 4*rr->rectx*rr->recty);

			/* if (ibuf->zbuf) { */
			/* 	if (R.rectz) freeN(R.rectz); */
			/* 	R.rectz = BLI_dupallocN(ibuf->zbuf); */
			/* } */
		}
		
		/* Let the cache limitor take care of this (schlaile) */
		/* While render let's keep all memory available for render 
		   (ton)
		   At least if free memory is tight...
		   This can make a big difference in encoding speed
		   (it is around 4 times(!) faster, if we do not waste time
		   on freeing _all_ buffers every time on long timelines...)
		   (schlaile)
		*/
		{
			extern int mem_in_use;
			extern int mmap_in_use;

			int max = MEM_CacheLimiter_get_maximum();
			if (max != 0 && mem_in_use + mmap_in_use > max) {
				fprintf(stderr, "mem_in_use = %d, max = %d\n",
					mem_in_use + mmap_in_use, max);
				fprintf(stderr, "Cleaning up, please wait...\n"
					"If this happens very often,\n"
					"consider "
					"raising the memcache limit in the "
					"user preferences.\n");
				free_imbuf_seq();
			}
		}
	}
	else {
		/* render result is delivered empty in most cases, nevertheless we handle all cases */
		if (rr->rectf)
			memset(rr->rectf, 0, 4*sizeof(float)*rr->rectx*rr->recty);
		else if (rr->rect32)
			memset(rr->rect32, 0, 4*rr->rectx*rr->recty);
		else
			rr->rect32= MEM_callocN(sizeof(int)*rr->rectx*rr->recty, "render_seq rect");
	}
	
	G.f &= ~G_PLAYANIM;

}
