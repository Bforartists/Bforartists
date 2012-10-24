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
 * Contributor(s): 
 * - Blender Foundation, 2003-2009
 * - Peter Schlaile <peter [at] schlaile [dot] de> 2005/2006
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/blenkernel/intern/sequencer.c
 *  \ingroup bke
 */

#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "MEM_guardedalloc.h"
#include "MEM_CacheLimiterC-Api.h"

#include "DNA_sequence_types.h"
#include "DNA_movieclip_types.h"
#include "DNA_mask_types.h"
#include "DNA_scene_types.h"
#include "DNA_anim_types.h"
#include "DNA_object_types.h"
#include "DNA_sound_types.h"

#include "BLI_math.h"
#include "BLI_fileops.h"
#include "BLI_listbase.h"
#include "BLI_path_util.h"
#include "BLI_string.h"
#include "BLI_threads.h"
#include "BLI_utildefines.h"

#include "BKE_animsys.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_main.h"
#include "BKE_sequencer.h"
#include "BKE_movieclip.h"
#include "BKE_fcurve.h"
#include "BKE_scene.h"
#include "BKE_mask.h"

#include "RNA_access.h"

#include "RE_pipeline.h"

#include <pthread.h>

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"
#include "IMB_colormanagement.h"

#include "BKE_context.h"
#include "BKE_sound.h"

#ifdef WITH_AUDASPACE
#  include "AUD_C-API.h"
#endif

static ImBuf *seq_render_strip_stack(SeqRenderData context, ListBase *seqbasep, float cfra, int chanshown);
static ImBuf *seq_render_strip(SeqRenderData context, Sequence *seq, float cfra);
static void seq_free_animdata(Scene *scene, Sequence *seq);
static ImBuf *seq_render_mask(SeqRenderData context, Mask *mask, float nr, short make_float);

/* **** XXX ******** */
#define SELECT 1
ListBase seqbase_clipboard;
int seqbase_clipboard_frame;
SequencerDrawView sequencer_view3d_cb = NULL; /* NULL in background mode */

#if 0  /* unused function */
static void printf_strip(Sequence *seq)
{
	fprintf(stderr, "name: '%s', len:%d, start:%d, (startofs:%d, endofs:%d), "
	        "(startstill:%d, endstill:%d), machine:%d, (startdisp:%d, enddisp:%d)\n",
	        seq->name, seq->len, seq->start, seq->startofs, seq->endofs, seq->startstill, seq->endstill, seq->machine,
	        seq->startdisp, seq->enddisp);

	fprintf(stderr, "\tseq_tx_set_final_left: %d %d\n\n", seq_tx_get_final_left(seq, 0),
	        seq_tx_get_final_right(seq, 0));
}
#endif

int BKE_sequencer_base_recursive_apply(ListBase *seqbase, int (*apply_func)(Sequence *seq, void *), void *arg)
{
	Sequence *iseq;
	for (iseq = seqbase->first; iseq; iseq = iseq->next) {
		if (BKE_sequencer_recursive_apply(iseq, apply_func, arg) == -1)
			return -1;  /* bail out */
	}
	return 1;
}

int BKE_sequencer_recursive_apply(Sequence *seq, int (*apply_func)(Sequence *, void *), void *arg)
{
	int ret = apply_func(seq, arg);

	if (ret == -1)
		return -1;  /* bail out */

	if (ret && seq->seqbase.first)
		ret = BKE_sequencer_base_recursive_apply(&seq->seqbase, apply_func, arg);

	return ret;
}

/*********************** alloc / free functions *************************/

/* free */

static void free_proxy_seq(Sequence *seq)
{
	if (seq->strip && seq->strip->proxy && seq->strip->proxy->anim) {
		IMB_free_anim(seq->strip->proxy->anim);
		seq->strip->proxy->anim = NULL;
	}
}

static void seq_free_strip(Strip *strip)
{
	strip->us--;
	if (strip->us > 0)
		return;
	if (strip->us < 0) {
		printf("error: negative users in strip\n");
		return;
	}

	if (strip->stripdata) {
		MEM_freeN(strip->stripdata);
	}

	if (strip->proxy) {
		if (strip->proxy->anim) {
			IMB_free_anim(strip->proxy->anim);
		}

		MEM_freeN(strip->proxy);
	}
	if (strip->crop) {
		MEM_freeN(strip->crop);
	}
	if (strip->transform) {
		MEM_freeN(strip->transform);
	}

	MEM_freeN(strip);
}

/* only give option to skip cache locally (static func) */
static void BKE_sequence_free_ex(Scene *scene, Sequence *seq, const int do_cache)
{
	if (seq->strip)
		seq_free_strip(seq->strip);

	if (seq->anim)
		IMB_free_anim(seq->anim);

	if (seq->type & SEQ_TYPE_EFFECT) {
		struct SeqEffectHandle sh = BKE_sequence_get_effect(seq);

		sh.free(seq);
	}

	if (seq->sound) {
		((ID *)seq->sound)->us--; 
	}

	/* clipboard has no scene and will never have a sound handle or be active */
	if (scene) {
		Editing *ed = scene->ed;

		if (ed->act_seq == seq)
			ed->act_seq = NULL;

		if (seq->scene_sound && ELEM(seq->type, SEQ_TYPE_SOUND_RAM, SEQ_TYPE_SCENE))
			sound_remove_scene_sound(scene, seq->scene_sound);

		seq_free_animdata(scene, seq);
	}

	/* free modifiers */
	BKE_sequence_modifier_clear(seq);

	/* free cached data used by this strip,
	 * also invalidate cache for all dependent sequences
	 *
	 * be _very_ careful here, invalidating cache loops over the scene sequences and
	 * assumes the listbase is valid for all strips, this may not be the case if lists are being freed.
	 * this is optional BKE_sequence_invalidate_cache
	 */
	if (do_cache) {
		if (scene) {
			BKE_sequence_invalidate_cache(scene, seq);
		}
	}

	MEM_freeN(seq);
}

void BKE_sequence_free(Scene *scene, Sequence *seq)
{
	BKE_sequence_free_ex(scene, seq, TRUE);
}

/* cache must be freed before calling this function
 * since it leaves the seqbase in an invalid state */
static void seq_free_sequence_recurse(Scene *scene, Sequence *seq)
{
	Sequence *iseq, *iseq_next;

	for (iseq = seq->seqbase.first; iseq; iseq = iseq_next) {
		iseq_next = iseq->next;
		seq_free_sequence_recurse(scene, iseq);
	}

	BKE_sequence_free_ex(scene, seq, FALSE);
}


Editing *BKE_sequencer_editing_get(Scene *scene, int alloc)
{
	if (alloc) {
		BKE_sequencer_editing_ensure(scene);
	}
	return scene->ed;
}

static void seq_free_clipboard_recursive(Sequence *seq_parent)
{
	Sequence *seq, *nseq;

	for (seq = seq_parent->seqbase.first; seq; seq = nseq) {
		nseq = seq->next;
		seq_free_clipboard_recursive(seq);
	}

	BKE_sequence_free_ex(NULL, seq_parent, FALSE);
}

void BKE_sequencer_free_clipboard(void)
{
	Sequence *seq, *nseq;

	for (seq = seqbase_clipboard.first; seq; seq = nseq) {
		nseq = seq->next;
		seq_free_clipboard_recursive(seq);
	}
	seqbase_clipboard.first = seqbase_clipboard.last = NULL;
}

Editing *BKE_sequencer_editing_ensure(Scene *scene)
{
	if (scene->ed == NULL) {
		Editing *ed;

		ed = scene->ed = MEM_callocN(sizeof(Editing), "addseq");
		ed->seqbasep = &ed->seqbase;
	}

	return scene->ed;
}

void BKE_sequencer_editing_free(Scene *scene)
{
	Editing *ed = scene->ed;
	Sequence *seq;

	if (ed == NULL)
		return;

	/* this may not be the active scene!, could be smarter about this */
	BKE_sequencer_cache_cleanup();

	SEQ_BEGIN (ed, seq)
	{
		/* handle cache freeing above */
		BKE_sequence_free_ex(scene, seq, FALSE);
	}
	SEQ_END

	BLI_freelistN(&ed->metastack);

	MEM_freeN(ed);

	scene->ed = NULL;
}

/*********************** Sequencer color space functions  *************************/

static void sequencer_imbuf_assign_spaces(Scene *scene, ImBuf *ibuf)
{
	IMB_colormanagement_assign_float_colorspace(ibuf, scene->sequencer_colorspace_settings.name);
}

void BKE_sequencer_imbuf_to_sequencer_space(Scene *scene, ImBuf *ibuf, int make_float)
{
	const char *from_colorspace = IMB_colormanagement_role_colorspace_name_get(COLOR_ROLE_SCENE_LINEAR);
	const char *to_colorspace = scene->sequencer_colorspace_settings.name;
	int predivide = ibuf->flags & IB_cm_predivide;

	if (!ibuf->rect_float) {
		if (make_float && ibuf->rect) {
			/* when converting byte buffer to float in sequencer we need to make float
			 * buffer be in sequencer's working space, which is currently only doable
			 * from linear space.
			 *
			 */

			/*
			 * OCIO_TODO: would be nice to support direct single transform from byte to sequencer's
			 */

			IMB_float_from_rect(ibuf);
		}
		else {
			/* if there's only byte buffer in image it's already in compositor's working space,
			 * nothing to do here
			 */

			return;
		}
	}

	if (from_colorspace && from_colorspace[0] != '\0') {
		if (ibuf->rect)
			imb_freerectImBuf(ibuf);

		IMB_colormanagement_transform_threaded(ibuf->rect_float, ibuf->x, ibuf->y, ibuf->channels,
		                                       from_colorspace, to_colorspace, predivide);
	}
}

void BKE_sequencer_imbuf_from_sequencer_space(Scene *scene, ImBuf *ibuf)
{
	const char *from_colorspace = scene->sequencer_colorspace_settings.name;
	const char *to_colorspace = IMB_colormanagement_role_colorspace_name_get(COLOR_ROLE_SCENE_LINEAR);

	if (!ibuf->rect_float)
		return;

	if (to_colorspace && to_colorspace[0] != '\0') {
		int predivide = ibuf->flags & IB_cm_predivide;

		IMB_colormanagement_transform_threaded(ibuf->rect_float, ibuf->x, ibuf->y, ibuf->channels,
		                                       from_colorspace, to_colorspace, predivide);
	}
}

void BKE_sequencer_pixel_from_sequencer_space_v4(struct Scene *scene, float pixel[4])
{
	const char *from_colorspace = scene->sequencer_colorspace_settings.name;
	const char *to_colorspace = IMB_colormanagement_role_colorspace_name_get(COLOR_ROLE_SCENE_LINEAR);

	if (to_colorspace && to_colorspace[0] != '\0') {
		IMB_colormanagement_transform_v4(pixel, from_colorspace, to_colorspace);
	}
	else {
		/* if no color management enables fallback to legacy conversion */
		srgb_to_linearrgb_v4(pixel, pixel);
	}
}

/*********************** sequencer pipeline functions *************************/

SeqRenderData BKE_sequencer_new_render_data(Main *bmain, Scene *scene, int rectx, int recty, int preview_render_size)
{
	SeqRenderData rval;

	rval.bmain = bmain;
	rval.scene = scene;
	rval.rectx = rectx;
	rval.recty = recty;
	rval.preview_render_size = preview_render_size;
	rval.motion_blur_samples = 0;
	rval.motion_blur_shutter = 0;

	return rval;
}

/* ************************* iterator ************************** */
/* *************** (replaces old WHILE_SEQ) ********************* */
/* **************** use now SEQ_BEGIN () SEQ_END ***************** */

/* sequence strip iterator:
 * - builds a full array, recursively into meta strips
 */

static void seq_count(ListBase *seqbase, int *tot)
{
	Sequence *seq;

	for (seq = seqbase->first; seq; seq = seq->next) {
		(*tot)++;

		if (seq->seqbase.first)
			seq_count(&seq->seqbase, tot);
	}
}

static void seq_build_array(ListBase *seqbase, Sequence ***array, int depth)
{
	Sequence *seq;

	for (seq = seqbase->first; seq; seq = seq->next) {
		seq->depth = depth;

		if (seq->seqbase.first)
			seq_build_array(&seq->seqbase, array, depth + 1);

		**array = seq;
		(*array)++;
	}
}

static void seq_array(Editing *ed, Sequence ***seqarray, int *tot, int use_pointer)
{
	Sequence **array;

	*seqarray = NULL;
	*tot = 0;

	if (ed == NULL)
		return;

	if (use_pointer)
		seq_count(ed->seqbasep, tot);
	else
		seq_count(&ed->seqbase, tot);

	if (*tot == 0)
		return;

	*seqarray = array = MEM_mallocN(sizeof(Sequence *) * (*tot), "SeqArray");
	if (use_pointer)
		seq_build_array(ed->seqbasep, &array, 0);
	else
		seq_build_array(&ed->seqbase, &array, 0);
}

void BKE_sequence_iterator_begin(Editing *ed, SeqIterator *iter, int use_pointer)
{
	memset(iter, 0, sizeof(*iter));
	seq_array(ed, &iter->array, &iter->tot, use_pointer);

	if (iter->tot) {
		iter->cur = 0;
		iter->seq = iter->array[iter->cur];
		iter->valid = 1;
	}
}

void BKE_sequence_iterator_next(SeqIterator *iter)
{
	if (++iter->cur < iter->tot)
		iter->seq = iter->array[iter->cur];
	else
		iter->valid = 0;
}

void BKE_sequence_iterator_end(SeqIterator *iter)
{
	if (iter->array)
		MEM_freeN(iter->array);

	iter->valid = 0;
}

static int metaseq_start(Sequence *metaseq)
{
	return metaseq->start + metaseq->startofs;
}

static int metaseq_end(Sequence *metaseq)
{
	return metaseq->start + metaseq->len - metaseq->endofs;
}

static void seq_update_sound_bounds_recursive_rec(Scene *scene, Sequence *metaseq, int start, int end)
{
	Sequence *seq;

	/* for sound we go over full meta tree to update bounds of the sound strips,
	 * since sound is played outside of evaluating the imbufs, */
	for (seq = metaseq->seqbase.first; seq; seq = seq->next) {
		if (seq->type == SEQ_TYPE_META) {
			seq_update_sound_bounds_recursive_rec(scene, seq, max_ii(start, metaseq_start(seq)),
			                                      min_ii(end, metaseq_end(seq)));
		}
		else if (ELEM(seq->type, SEQ_TYPE_SOUND_RAM, SEQ_TYPE_SCENE)) {
			if (seq->scene_sound) {
				int startofs = seq->startofs;
				int endofs = seq->endofs;
				if (seq->startofs + seq->start < start)
					startofs = start - seq->start;

				if (seq->start + seq->len - seq->endofs > end)
					endofs = seq->start + seq->len - end;

				sound_move_scene_sound(scene, seq->scene_sound, seq->start + startofs,
				                       seq->start + seq->len - endofs, startofs);
			}
		}
	}
}

static void seq_update_sound_bounds_recursive(Scene *scene, Sequence *metaseq)
{
	seq_update_sound_bounds_recursive_rec(scene, metaseq, metaseq_start(metaseq), metaseq_end(metaseq));
}

void BKE_sequence_calc_disp(Scene *scene, Sequence *seq)
{
	if (seq->startofs && seq->startstill)
		seq->startstill = 0;
	if (seq->endofs && seq->endstill)
		seq->endstill = 0;
	
	seq->startdisp = seq->start + seq->startofs - seq->startstill;
	seq->enddisp = seq->start + seq->len - seq->endofs + seq->endstill;
	
	seq->handsize = 10.0;  /* 10 frames */
	if (seq->enddisp - seq->startdisp < 10) {
		seq->handsize = (float)(0.5 * (seq->enddisp - seq->startdisp));
	}
	else if (seq->enddisp - seq->startdisp > 250) {
		seq->handsize = (float)((seq->enddisp - seq->startdisp) / 25);
	}

	if (ELEM(seq->type, SEQ_TYPE_SOUND_RAM, SEQ_TYPE_SCENE)) {
		BKE_sequencer_update_sound_bounds(scene, seq);
	}
	else if (seq->type == SEQ_TYPE_META)
		seq_update_sound_bounds_recursive(scene, seq);
}

void BKE_sequence_calc(Scene *scene, Sequence *seq)
{
	Sequence *seqm;
	int min, max;

	/* check all metas recursively */
	seqm = seq->seqbase.first;
	while (seqm) {
		if (seqm->seqbase.first) BKE_sequence_calc(scene, seqm);
		seqm = seqm->next;
	}

	/* effects and meta: automatic start and end */

	if (seq->type & SEQ_TYPE_EFFECT) {
		/* pointers */
		if (seq->seq2 == NULL)
			seq->seq2 = seq->seq1;
		if (seq->seq3 == NULL)
			seq->seq3 = seq->seq1;

		/* effecten go from seq1 -> seq2: test */

		/* we take the largest start and smallest end */

		// seq->start = seq->startdisp = MAX2(seq->seq1->startdisp, seq->seq2->startdisp);
		// seq->enddisp = MIN2(seq->seq1->enddisp, seq->seq2->enddisp);

		if (seq->seq1) {
			/* XXX These resets should not be necessary, but users used to be able to
			 *     edit effect's length, leading to strange results. See [#29190] */
			seq->startofs = seq->endofs = seq->startstill = seq->endstill = 0;
			seq->start = seq->startdisp = MAX3(seq->seq1->startdisp, seq->seq2->startdisp, seq->seq3->startdisp);
			seq->enddisp = MIN3(seq->seq1->enddisp, seq->seq2->enddisp, seq->seq3->enddisp);
			/* we cant help if strips don't overlap, it wont give useful results.
			 * but at least ensure 'len' is never negative which causes bad bugs elsewhere. */
			if (seq->enddisp < seq->startdisp) {
				/* simple start/end swap */
				seq->start = seq->enddisp;
				seq->enddisp = seq->startdisp;
				seq->startdisp = seq->start;
				seq->flag |= SEQ_INVALID_EFFECT;
			}
			else {
				seq->flag &= ~SEQ_INVALID_EFFECT;
			}

			seq->len = seq->enddisp - seq->startdisp;
		}
		else {
			BKE_sequence_calc_disp(scene, seq);
		}
	}
	else {
		if (seq->type == SEQ_TYPE_META) {
			seqm = seq->seqbase.first;
			if (seqm) {
				min =  MAXFRAME * 2;
				max = -MAXFRAME * 2;
				while (seqm) {
					if (seqm->startdisp < min) min = seqm->startdisp;
					if (seqm->enddisp > max) max = seqm->enddisp;
					seqm = seqm->next;
				}
				seq->start = min + seq->anim_startofs;
				seq->len = max - min;
				seq->len -= seq->anim_startofs;
				seq->len -= seq->anim_endofs;
			}
			seq_update_sound_bounds_recursive(scene, seq);
		}
		BKE_sequence_calc_disp(scene, seq);
	}
}

/* note: caller should run calc_sequence(scene, seq) after */
void BKE_sequence_reload_new_file(Scene *scene, Sequence *seq, int lock_range)
{
	char str[FILE_MAX];
	int prev_startdisp = 0, prev_enddisp = 0;
	/* note: don't rename the strip, will break animation curves */

	if (ELEM7(seq->type,
	          SEQ_TYPE_MOVIE, SEQ_TYPE_IMAGE, SEQ_TYPE_SOUND_RAM,
	          SEQ_TYPE_SCENE, SEQ_TYPE_META, SEQ_TYPE_MOVIECLIP, SEQ_TYPE_MASK) == 0)
	{
		return;
	}

	if (lock_range) {
		/* keep so we don't have to move the actual start and end points (only the data) */
		BKE_sequence_calc_disp(scene, seq);
		prev_startdisp = seq->startdisp;
		prev_enddisp = seq->enddisp;
	}

	switch (seq->type) {
		case SEQ_TYPE_IMAGE:
		{
			/* Hack? */
			size_t olen = MEM_allocN_len(seq->strip->stripdata) / sizeof(StripElem);

			seq->len = olen;
			seq->len -= seq->anim_startofs;
			seq->len -= seq->anim_endofs;
			if (seq->len < 0) {
				seq->len = 0;
			}
			break;
		}
		case SEQ_TYPE_MOVIE:
			BLI_join_dirfile(str, sizeof(str), seq->strip->dir,
			                 seq->strip->stripdata->name);
			BLI_path_abs(str, G.main->name);

			if (seq->anim) IMB_free_anim(seq->anim);

			/* OCIO_TODO: support configurable input space for strips */
			seq->anim = openanim(str, IB_rect | ((seq->flag & SEQ_FILTERY) ? IB_animdeinterlace : 0), seq->streamindex, NULL);

			if (!seq->anim) {
				return;
			}

			seq->len = IMB_anim_get_duration(seq->anim, seq->strip->proxy ? seq->strip->proxy->tc : IMB_TC_RECORD_RUN);
	
			seq->anim_preseek = IMB_anim_get_preseek(seq->anim);

			seq->len -= seq->anim_startofs;
			seq->len -= seq->anim_endofs;
			if (seq->len < 0) {
				seq->len = 0;
			}
			break;
		case SEQ_TYPE_MOVIECLIP:
			if (seq->clip == NULL)
				return;

			seq->len = BKE_movieclip_get_duration(seq->clip);

			seq->len -= seq->anim_startofs;
			seq->len -= seq->anim_endofs;
			if (seq->len < 0) {
				seq->len = 0;
			}
			break;
		case SEQ_TYPE_MASK:
			if (seq->mask == NULL)
				return;
			seq->len = BKE_mask_get_duration(seq->mask);
			seq->len -= seq->anim_startofs;
			seq->len -= seq->anim_endofs;
			if (seq->len < 0) {
				seq->len = 0;
			}
			break;
		case SEQ_TYPE_SOUND_RAM:
#ifdef WITH_AUDASPACE
			if (!seq->sound)
				return;
			seq->len = ceil(AUD_getInfo(seq->sound->playback_handle).length * FPS);
			seq->len -= seq->anim_startofs;
			seq->len -= seq->anim_endofs;
			if (seq->len < 0) {
				seq->len = 0;
			}
#else
			return;
#endif
			break;
		case SEQ_TYPE_SCENE:
		{
			seq->len = (seq->scene) ? seq->scene->r.efra - seq->scene->r.sfra + 1 : 0;
			seq->len -= seq->anim_startofs;
			seq->len -= seq->anim_endofs;
			if (seq->len < 0) {
				seq->len = 0;
			}
			break;
		}
	}

	free_proxy_seq(seq);

	if (lock_range) {
		BKE_sequence_tx_set_final_left(seq, prev_startdisp);
		BKE_sequence_tx_set_final_right(seq, prev_enddisp);
		BKE_sequence_single_fix(seq);
	}
	
	BKE_sequence_calc(scene, seq);
}

void BKE_sequencer_sort(Scene *scene)
{
	/* all strips together per kind, and in order of y location ("machine") */
	ListBase seqbase, effbase;
	Editing *ed = BKE_sequencer_editing_get(scene, FALSE);
	Sequence *seq, *seqt;

	
	if (ed == NULL)
		return;

	seqbase.first = seqbase.last = NULL;
	effbase.first = effbase.last = NULL;

	while ( (seq = ed->seqbasep->first) ) {
		BLI_remlink(ed->seqbasep, seq);

		if (seq->type & SEQ_TYPE_EFFECT) {
			seqt = effbase.first;
			while (seqt) {
				if (seqt->machine >= seq->machine) {
					BLI_insertlinkbefore(&effbase, seqt, seq);
					break;
				}
				seqt = seqt->next;
			}
			if (seqt == NULL)
				BLI_addtail(&effbase, seq);
		}
		else {
			seqt = seqbase.first;
			while (seqt) {
				if (seqt->machine >= seq->machine) {
					BLI_insertlinkbefore(&seqbase, seqt, seq);
					break;
				}
				seqt = seqt->next;
			}
			if (seqt == NULL)
				BLI_addtail(&seqbase, seq);
		}
	}

	BLI_movelisttolist(&seqbase, &effbase);
	*(ed->seqbasep) = seqbase;
}

static int clear_scene_in_allseqs_cb(Sequence *seq, void *arg_pt)
{
	if (seq->scene == (Scene *)arg_pt)
		seq->scene = NULL;
	return 1;
}

void BKE_sequencer_clear_scene_in_allseqs(Main *bmain, Scene *scene)
{
	Scene *scene_iter;

	/* when a scene is deleted: test all seqs */
	for (scene_iter = bmain->scene.first; scene_iter; scene_iter = scene_iter->id.next) {
		if (scene_iter != scene && scene_iter->ed) {
			BKE_sequencer_base_recursive_apply(&scene_iter->ed->seqbase, clear_scene_in_allseqs_cb, scene);
		}
	}
}

typedef struct SeqUniqueInfo {
	Sequence *seq;
	char name_src[SEQ_NAME_MAXSTR];
	char name_dest[SEQ_NAME_MAXSTR];
	int count;
	int match;
} SeqUniqueInfo;

static void seqbase_unique_name(ListBase *seqbasep, SeqUniqueInfo *sui)
{
	Sequence *seq;
	for (seq = seqbasep->first; seq; seq = seq->next) {
		if (sui->seq != seq && strcmp(sui->name_dest, seq->name + 2) == 0) {
			/* SEQ_NAME_MAXSTR - 2 for prefix, -1 for \0, -4 for the number */
			BLI_snprintf(sui->name_dest, sizeof(sui->name_dest), "%.59s.%03d",  sui->name_src, sui->count++);
			sui->match = 1; /* be sure to re-scan */
		}
	}
}

static int seqbase_unique_name_recursive_cb(Sequence *seq, void *arg_pt)
{
	if (seq->seqbase.first)
		seqbase_unique_name(&seq->seqbase, (SeqUniqueInfo *)arg_pt);
	return 1;
}

void BKE_sequence_base_unique_name_recursive(ListBase *seqbasep, Sequence *seq)
{
	SeqUniqueInfo sui;
	char *dot;
	sui.seq = seq;
	BLI_strncpy(sui.name_src, seq->name + 2, sizeof(sui.name_src));
	BLI_strncpy(sui.name_dest, seq->name + 2, sizeof(sui.name_dest));

	sui.count = 1;
	sui.match = 1; /* assume the worst to start the loop */

	/* Strip off the suffix */
	if ((dot = strrchr(sui.name_src, '.'))) {
		*dot = '\0';
		dot++;

		if (*dot)
			sui.count = atoi(dot) + 1;
	}

	while (sui.match) {
		sui.match = 0;
		seqbase_unique_name(seqbasep, &sui);
		BKE_sequencer_base_recursive_apply(seqbasep, seqbase_unique_name_recursive_cb, &sui);
	}

	BLI_strncpy(seq->name + 2, sui.name_dest, sizeof(seq->name) - 2);
}

static const char *give_seqname_by_type(int type)
{
	switch (type) {
		case SEQ_TYPE_META:       return "Meta";
		case SEQ_TYPE_IMAGE:      return "Image";
		case SEQ_TYPE_SCENE:      return "Scene";
		case SEQ_TYPE_MOVIE:      return "Movie";
		case SEQ_TYPE_MOVIECLIP:  return "Clip";
		case SEQ_TYPE_MASK:       return "Mask";
		case SEQ_TYPE_SOUND_RAM:  return "Audio";
		case SEQ_TYPE_CROSS:      return "Cross";
		case SEQ_TYPE_GAMCROSS:   return "Gamma Cross";
		case SEQ_TYPE_ADD:        return "Add";
		case SEQ_TYPE_SUB:        return "Sub";
		case SEQ_TYPE_MUL:        return "Mul";
		case SEQ_TYPE_ALPHAOVER:  return "Alpha Over";
		case SEQ_TYPE_ALPHAUNDER: return "Alpha Under";
		case SEQ_TYPE_OVERDROP:   return "Over Drop";
		case SEQ_TYPE_WIPE:       return "Wipe";
		case SEQ_TYPE_GLOW:       return "Glow";
		case SEQ_TYPE_TRANSFORM:  return "Transform";
		case SEQ_TYPE_COLOR:      return "Color";
		case SEQ_TYPE_MULTICAM:   return "Multicam";
		case SEQ_TYPE_ADJUSTMENT: return "Adjustment";
		case SEQ_TYPE_SPEED:      return "Speed";
		default:
			return NULL;
	}
}

const char *BKE_sequence_give_name(Sequence *seq)
{
	const char *name = give_seqname_by_type(seq->type);

	if (!name) {
		if (seq->type < SEQ_TYPE_EFFECT) {
			return seq->strip->dir;
		}
		else {
			return "Effect";
		}
	}
	return name;
}

/*********************** DO THE SEQUENCE *************************/

static void make_black_ibuf(ImBuf *ibuf)
{
	unsigned int *rect;
	float *rect_float;
	int tot;

	if (ibuf == NULL || (ibuf->rect == NULL && ibuf->rect_float == NULL)) {
		return;
	}

	tot = ibuf->x * ibuf->y;

	rect = ibuf->rect;
	rect_float = ibuf->rect_float;

	if (rect) {
		memset(rect, 0, tot * sizeof(char) * 4);
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

	mul = (int)(256.0f * fmul);
	rt = (char *)ibuf->rect;
	rt_float = ibuf->rect_float;

	if (rt) {
		a = ibuf->x * ibuf->y;
		while (a--) {

			icol = (mul * rt[0]) >> 8;
			if (icol > 254) rt[0] = 255; else rt[0] = icol;
			icol = (mul * rt[1]) >> 8;
			if (icol > 254) rt[1] = 255; else rt[1] = icol;
			icol = (mul * rt[2]) >> 8;
			if (icol > 254) rt[2] = 255; else rt[2] = icol;
			icol = (mul * rt[3]) >> 8;
			if (icol > 254) rt[3] = 255; else rt[3] = icol;
			
			rt += 4;
		}
	}
	if (rt_float) {
		a = ibuf->x * ibuf->y;
		while (a--) {
			rt_float[0] *= fmul;
			rt_float[1] *= fmul;
			rt_float[2] *= fmul;
			rt_float[3] *= fmul;
			
			rt_float += 4;
		}
	}
}

static float give_stripelem_index(Sequence *seq, float cfra)
{
	float nr;
	int sta = seq->start;
	int end = seq->start + seq->len - 1;

	if (seq->type & SEQ_TYPE_EFFECT) {
		end = seq->enddisp;
	}

	if (end < sta) {
		return -1;
	}

	if (seq->flag & SEQ_REVERSE_FRAMES) {
		/*reverse frame in this sequence */
		if (cfra <= sta) nr = end - sta;
		else if (cfra >= end) nr = 0;
		else nr = end - cfra;
	}
	else {
		if (cfra <= sta) nr = 0;
		else if (cfra >= end) nr = end - sta;
		else nr = cfra - sta;
	}
	
	if (seq->strobe < 1.0f) seq->strobe = 1.0f;
	
	if (seq->strobe > 1.0f) {
		nr -= fmodf((double)nr, (double)seq->strobe);
	}

	return nr;
}

StripElem *BKE_sequencer_give_stripelem(Sequence *seq, int cfra)
{
	StripElem *se = seq->strip->stripdata;

	if (seq->type == SEQ_TYPE_IMAGE) {
		/* only IMAGE strips use the whole array, MOVIE strips use only the first element,
		 * all other strips don't use this...
		 */

		int nr = (int) give_stripelem_index(seq, cfra);

		if (nr == -1 || se == NULL)
			return NULL;
	
		se += nr + seq->anim_startofs;
	}
	return se;
}

static int evaluate_seq_frame_gen(Sequence **seq_arr, ListBase *seqbase, int cfra)
{
	Sequence *seq;
	int totseq = 0;

	memset(seq_arr, 0, sizeof(Sequence *) * (MAXSEQ + 1));

	seq = seqbase->first;
	while (seq) {
		if (seq->startdisp <= cfra && seq->enddisp > cfra) {
			seq_arr[seq->machine] = seq;
			totseq++;
		}
		seq = seq->next;
	}

	return totseq;
}

int BKE_sequencer_evaluate_frame(Scene *scene, int cfra)
{
	Editing *ed = BKE_sequencer_editing_get(scene, FALSE);
	Sequence *seq_arr[MAXSEQ + 1];

	if (ed == NULL)
		return 0;

	return evaluate_seq_frame_gen(seq_arr, ed->seqbasep, cfra);
}

static int video_seq_is_rendered(Sequence *seq)
{
	return (seq && !(seq->flag & SEQ_MUTE) && seq->type != SEQ_TYPE_SOUND_RAM);
}

static int get_shown_sequences(ListBase *seqbasep, int cfra, int chanshown, Sequence **seq_arr_out)
{
	Sequence *seq_arr[MAXSEQ + 1];
	int b = chanshown;
	int cnt = 0;

	if (b > MAXSEQ) {
		return 0;
	}

	if (evaluate_seq_frame_gen(seq_arr, seqbasep, cfra)) {
		if (b == 0) {
			b = MAXSEQ;
		}
		for (; b > 0; b--) {
			if (video_seq_is_rendered(seq_arr[b])) {
				break;
			}
		}
	}
	
	chanshown = b;

	for (; b > 0; b--) {
		if (video_seq_is_rendered(seq_arr[b])) {
			if (seq_arr[b]->blend_mode == SEQ_BLEND_REPLACE) {
				break;
			}
		}
	}

	for (; b <= chanshown && b >= 0; b++) {
		if (video_seq_is_rendered(seq_arr[b])) {
			seq_arr_out[cnt++] = seq_arr[b];
		}
	}

	return cnt;
}

/*********************** proxy management *************************/

typedef struct SeqIndexBuildContext {
	struct IndexBuildContext *index_context;

	int tc_flags;
	int size_flags;
	int quality;

	Main *bmain;
	Scene *scene;
	Sequence *seq, *orig_seq;
} SeqIndexBuildContext;

#define PROXY_MAXFILE (2 * FILE_MAXDIR + FILE_MAXFILE)

static IMB_Proxy_Size seq_rendersize_to_proxysize(int size)
{
	if (size >= 100) {
		return IMB_PROXY_NONE;
	}
	if (size >= 99) {
		return IMB_PROXY_100;
	}
	if (size >= 75) {
		return IMB_PROXY_75;
	}
	if (size >= 50) {
		return IMB_PROXY_50;
	}
	return IMB_PROXY_25;
}

static double seq_rendersize_to_scale_factor(int size)
{
	if (size >= 99) {
		return 1.0;
	}
	if (size >= 75) {
		return 0.75;
	}
	if (size >= 50) {
		return 0.50;
	}
	return 0.25;
}

static void seq_open_anim_file(Sequence *seq)
{
	char name[FILE_MAX];
	StripProxy *proxy;

	if (seq->anim != NULL) {
		return;
	}

	BLI_join_dirfile(name, sizeof(name),
	                 seq->strip->dir, seq->strip->stripdata->name);
	BLI_path_abs(name, G.main->name);
	
	/* OCIO_TODO: support configurable input space for strips */
	seq->anim = openanim(name, IB_rect | ((seq->flag & SEQ_FILTERY) ? IB_animdeinterlace : 0), seq->streamindex, NULL);

	if (seq->anim == NULL) {
		return;
	}

	proxy = seq->strip->proxy;

	if (proxy == NULL) {
		return;
	}

	if (seq->flag & SEQ_USE_PROXY_CUSTOM_DIR) {
		char dir[FILE_MAX];
		BLI_strncpy(dir, seq->strip->proxy->dir, sizeof(dir));
		BLI_path_abs(dir, G.main->name);

		IMB_anim_set_index_dir(seq->anim, dir);
	}
}


static int seq_proxy_get_fname(Sequence *seq, int cfra, int render_size, char *name)
{
	int frameno;
	char dir[PROXY_MAXFILE];

	if (!seq->strip->proxy) {
		return FALSE;
	}

	/* MOVIE tracks (only exception: custom files) are now handled 
	 * internally by ImBuf module for various reasons: proper time code
	 * support, quicker index build, using one file instead
	 * of a full directory of jpeg files, etc. Trying to support old
	 * and new method at once could lead to funny effects, if people
	 * have both, a directory full of jpeg files and proxy avis, so
	 * sorry folks, please rebuild your proxies... */

	if (seq->flag & (SEQ_USE_PROXY_CUSTOM_DIR | SEQ_USE_PROXY_CUSTOM_FILE)) {
		BLI_strncpy(dir, seq->strip->proxy->dir, sizeof(dir));
	}
	else if (seq->type == SEQ_TYPE_IMAGE) {
		BLI_snprintf(dir, PROXY_MAXFILE, "%s/BL_proxy", seq->strip->dir);
	}
	else {
		return FALSE;
	}

	if (seq->flag & SEQ_USE_PROXY_CUSTOM_FILE) {
		BLI_join_dirfile(name, PROXY_MAXFILE,
		                 dir, seq->strip->proxy->file);
		BLI_path_abs(name, G.main->name);

		return TRUE;
	}

	/* generate a separate proxy directory for each preview size */

	if (seq->type == SEQ_TYPE_IMAGE) {
		BLI_snprintf(name, PROXY_MAXFILE, "%s/images/%d/%s_proxy", dir, render_size,
		             BKE_sequencer_give_stripelem(seq, cfra)->name);
		frameno = 1;
	}
	else {
		frameno = (int)give_stripelem_index(seq, cfra) + seq->anim_startofs;
		BLI_snprintf(name, PROXY_MAXFILE, "%s/proxy_misc/%d/####", dir, render_size);
	}

	BLI_path_abs(name, G.main->name);
	BLI_path_frame(name, frameno, 0);

	strcat(name, ".jpg");

	return TRUE;
}

static ImBuf *seq_proxy_fetch(SeqRenderData context, Sequence *seq, int cfra)
{
	char name[PROXY_MAXFILE];
	IMB_Proxy_Size psize = seq_rendersize_to_proxysize(context.preview_render_size);
	int size_flags;
	int render_size = context.preview_render_size;

	/* dirty hack to distinguish 100% render size from PROXY_100 */
	if (render_size == 99) {
		render_size = 100;
	}

	if (!(seq->flag & SEQ_USE_PROXY)) {
		return NULL;
	}

	size_flags = seq->strip->proxy->build_size_flags;

	/* only use proxies, if they are enabled (even if present!) */
	if (psize == IMB_PROXY_NONE || ((size_flags & psize) != psize)) {
		return NULL;
	}

	if (seq->flag & SEQ_USE_PROXY_CUSTOM_FILE) {
		int frameno = (int)give_stripelem_index(seq, cfra) + seq->anim_startofs;
		if (seq->strip->proxy->anim == NULL) {
			if (seq_proxy_get_fname(seq, cfra, render_size, name) == 0) {
				return NULL;
			}

			/* proxies are generated in default color space */
			seq->strip->proxy->anim = openanim(name, IB_rect, 0, NULL);
		}
		if (seq->strip->proxy->anim == NULL) {
			return NULL;
		}
 
		seq_open_anim_file(seq);

		frameno = IMB_anim_index_get_frame_index(seq->anim, seq->strip->proxy->tc, frameno);

		return IMB_anim_absolute(seq->strip->proxy->anim, frameno, IMB_TC_NONE, IMB_PROXY_NONE);
	}
 
	if (seq_proxy_get_fname(seq, cfra, render_size, name) == 0) {
		return NULL;
	}

	if (BLI_exists(name)) {
		/* OCIO_TODO: support configurable spaces for strips */
		ImBuf *ibuf = IMB_loadiffname(name, IB_rect, NULL);

		if (ibuf)
			sequencer_imbuf_assign_spaces(context.scene, ibuf);

		return ibuf;
	}
	else {
		return NULL;
	}
}

static void seq_proxy_build_frame(SeqRenderData context, Sequence *seq, int cfra, int proxy_render_size)
{
	char name[PROXY_MAXFILE];
	int quality;
	int rectx, recty;
	int ok;
	ImBuf *ibuf;

	if (!seq_proxy_get_fname(seq, cfra, proxy_render_size, name)) {
		return;
	}

	ibuf = seq_render_strip(context, seq, cfra);

	rectx = (proxy_render_size * context.scene->r.xsch) / 100;
	recty = (proxy_render_size * context.scene->r.ysch) / 100;

	if (ibuf->x != rectx || ibuf->y != recty) {
		IMB_scalefastImBuf(ibuf, (short)rectx, (short)recty);
	}

	/* depth = 32 is intentionally left in, otherwise ALPHA channels
	 * won't work... */
	quality = seq->strip->proxy->quality;
	ibuf->ftype = JPG | quality;

	/* unsupported feature only confuses other s/w */
	if (ibuf->planes == 32)
		ibuf->planes = 24;

	BLI_make_existing_file(name);

	/* OCIO_TODO: support per-strip color space settings */
	ok = IMB_saveiff(ibuf, name, IB_rect | IB_zbuf | IB_zbuffloat);
	if (ok == 0) {
		perror(name);
	}

	IMB_freeImBuf(ibuf);
}

SeqIndexBuildContext *BKE_sequencer_proxy_rebuild_context(Main *bmain, Scene *scene, Sequence *seq)
{
	SeqIndexBuildContext *context;
	Sequence *nseq;

	if (!seq->strip || !seq->strip->proxy) {
		return NULL;
	}

	if (!(seq->flag & SEQ_USE_PROXY)) {
		return NULL;
	}

	context = MEM_callocN(sizeof(SeqIndexBuildContext), "seq proxy rebuild context");

	nseq = BKE_sequence_dupli_recursive(scene, scene, seq, 0);

	context->tc_flags   = nseq->strip->proxy->build_tc_flags;
	context->size_flags = nseq->strip->proxy->build_size_flags;
	context->quality    = nseq->strip->proxy->quality;

	context->bmain = bmain;
	context->scene = scene;
	context->orig_seq = seq;
	context->seq = nseq;

	if (nseq->type == SEQ_TYPE_MOVIE) {
		seq_open_anim_file(nseq);

		if (nseq->anim) {
			context->index_context = IMB_anim_index_rebuild_context(nseq->anim,
			        context->tc_flags, context->size_flags, context->quality);
		}
	}

	return context;
}

void BKE_sequencer_proxy_rebuild(SeqIndexBuildContext *context, short *stop, short *do_update, float *progress)
{
	SeqRenderData render_context;
	Sequence *seq = context->seq;
	Scene *scene = context->scene;
	int cfra;

	if (seq->type == SEQ_TYPE_MOVIE) {
		if (context->index_context) {
			IMB_anim_index_rebuild(context->index_context, stop, do_update, progress);
		}

		return;
	}

	if (!(seq->flag & SEQ_USE_PROXY)) {
		return;
	}

	/* that's why it is called custom... */
	if (seq->flag & SEQ_USE_PROXY_CUSTOM_FILE) {
		return;
	}

	/* fail safe code */

	render_context = BKE_sequencer_new_render_data(context->bmain, context->scene,
	                                    (scene->r.size * (float) scene->r.xsch) / 100.0f + 0.5f,
	                                    (scene->r.size * (float) scene->r.ysch) / 100.0f + 0.5f, 100);

	for (cfra = seq->startdisp + seq->startstill;  cfra < seq->enddisp - seq->endstill; cfra++) {
		if (context->size_flags & IMB_PROXY_25) {
			seq_proxy_build_frame(render_context, seq, cfra, 25);
		}
		if (context->size_flags & IMB_PROXY_50) {
			seq_proxy_build_frame(render_context, seq, cfra, 50);
		}
		if (context->size_flags & IMB_PROXY_75) {
			seq_proxy_build_frame(render_context, seq, cfra, 75);
		}
		if (context->size_flags & IMB_PROXY_100) {
			seq_proxy_build_frame(render_context, seq, cfra, 100);
		}

		*progress = (float) cfra / (seq->enddisp - seq->endstill - seq->startdisp + seq->startstill);
		*do_update = TRUE;

		if (*stop || G.is_break)
			break;
	}
}

void BKE_sequencer_proxy_rebuild_finish(SeqIndexBuildContext *context, short stop)
{
	if (context->index_context) {
		IMB_close_anim_proxies(context->seq->anim);
		IMB_close_anim_proxies(context->orig_seq->anim);
		IMB_anim_index_rebuild_finish(context->index_context, stop);
	}

	seq_free_sequence_recurse(context->scene, context->seq);

	MEM_freeN(context);
}

/*********************** color balance *************************/

static StripColorBalance calc_cb(StripColorBalance *cb_)
{
	StripColorBalance cb = *cb_;
	int c;

	for (c = 0; c < 3; c++) {
		cb.lift[c] = 2.0f - cb.lift[c];
	}

	if (cb.flag & SEQ_COLOR_BALANCE_INVERSE_LIFT) {
		for (c = 0; c < 3; c++) {
			/* tweak to give more subtle results
			 * values above 1.0 are scaled */
			if (cb.lift[c] > 1.0f)
				cb.lift[c] = pow(cb.lift[c] - 1.0f, 2.0) + 1.0;

			cb.lift[c] = 2.0f - cb.lift[c];
		}
	}

	if (cb.flag & SEQ_COLOR_BALANCE_INVERSE_GAIN) {
		for (c = 0; c < 3; c++) {
			if (cb.gain[c] != 0.0f) {
				cb.gain[c] = 1.0f / cb.gain[c];
			}
			else {
				cb.gain[c] = 1000000; /* should be enough :) */
			}
		}
	}

	if (!(cb.flag & SEQ_COLOR_BALANCE_INVERSE_GAMMA)) {
		for (c = 0; c < 3; c++) {
			if (cb.gamma[c] != 0.0f) {
				cb.gamma[c] = 1.0f / cb.gamma[c];
			}
			else {
				cb.gamma[c] = 1000000; /* should be enough :) */
			}
		}
	}

	return cb;
}

/* note: lift is actually 2-lift */
MINLINE float color_balance_fl(float in, const float lift, const float gain, const float gamma, const float mul)
{
	float x = (((in - 1.0f) * lift) + 1.0f) * gain;

	/* prevent NaN */
	if (x < 0.f)
		x = 0.f;

	return powf(x, gamma) * mul;
}

static void make_cb_table_byte(float lift, float gain, float gamma,
                               unsigned char *table, float mul)
{
	int y;

	for (y = 0; y < 256; y++) {
		float v = color_balance_fl((float)y * (1.0f / 255.0f), lift, gain, gamma, mul);

		table[y] = FTOCHAR(v);
	}
}

static void make_cb_table_float(float lift, float gain, float gamma,
                                float *table, float mul)
{
	int y;

	for (y = 0; y < 256; y++) {
		float v = color_balance_fl((float)y * (1.0f / 255.0f), lift, gain, gamma, mul);

		table[y] = v;
	}
}

static void color_balance_byte_byte(StripColorBalance *cb_, unsigned char *rect, unsigned char *mask_rect, int width, int height, float mul)
{
	unsigned char cb_tab[3][256];
	int c;
	unsigned char *p = rect;
	unsigned char *e = p + width * 4 * height;
	unsigned char *m = mask_rect;

	StripColorBalance cb = calc_cb(cb_);

	for (c = 0; c < 3; c++) {
		make_cb_table_byte(cb.lift[c], cb.gain[c], cb.gamma[c], cb_tab[c], mul);
	}

	while (p < e) {
		if (m) {
			float t[3] = {m[0] / 255.0f, m[1] / 255.0f, m[2] / 255.0f};

			p[0] = p[0] * (1.0f - t[0]) + t[0] * cb_tab[0][p[0]];
			p[1] = p[1] * (1.0f - t[1]) + t[1] * cb_tab[1][p[1]];
			p[2] = p[2] * (1.0f - t[2]) + t[2] * cb_tab[2][p[2]];

			m += 4;
		}
		else {
			p[0] = cb_tab[0][p[0]];
			p[1] = cb_tab[1][p[1]];
			p[2] = cb_tab[2][p[2]];
		}
		
		p += 4;
	}
}

static void color_balance_byte_float(StripColorBalance *cb_, unsigned char *rect, float *rect_float, unsigned char *mask_rect, int width, int height, float mul)
{
	float cb_tab[4][256];
	int c, i;
	unsigned char *p = rect;
	unsigned char *e = p + width * 4 * height;
	unsigned char *m = mask_rect;
	float *o;
	StripColorBalance cb;

	o = rect_float;

	cb = calc_cb(cb_);

	for (c = 0; c < 3; c++) {
		make_cb_table_float(cb.lift[c], cb.gain[c], cb.gamma[c], cb_tab[c], mul);
	}

	for (i = 0; i < 256; i++) {
		cb_tab[3][i] = ((float)i) * (1.0f / 255.0f);
	}

	while (p < e) {
		if (m) {
			float t[3] = {m[0] / 255.0f, m[1] / 255.0f, m[2] / 255.0f};

			p[0] = p[0] * (1.0f - t[0]) + t[0] * cb_tab[0][p[0]];
			p[1] = p[1] * (1.0f - t[1]) + t[1] * cb_tab[1][p[1]];
			p[2] = p[2] * (1.0f - t[2]) + t[2] * cb_tab[2][p[2]];

			m += 4;
		}
		else {
			o[0] = cb_tab[0][p[0]];
			o[1] = cb_tab[1][p[1]];
			o[2] = cb_tab[2][p[2]];
		}

		o[3] = cb_tab[3][p[3]];

		p += 4; o += 4;
	}
}

static void color_balance_float_float(StripColorBalance *cb_, float *rect_float, float *mask_rect_float, int width, int height, float mul)
{
	float *p = rect_float;
	float *e = rect_float + width * 4 * height;
	float *m = mask_rect_float;
	StripColorBalance cb = calc_cb(cb_);

	while (p < e) {
		int c;
		for (c = 0; c < 3; c++) {
			float t = color_balance_fl(p[c], cb.lift[c], cb.gain[c], cb.gamma[c], mul);

			if (m)
				p[c] = p[c] * (1.0f - m[c]) + t * m[c];
			else
				p[c] = t;
		}

		p += 4;
		if (m)
			m += 4;
	}
}

typedef struct ColorBalanceInitData {
	StripColorBalance *cb;
	ImBuf *ibuf;
	float mul;
	ImBuf *mask;
	short make_float;
} ColorBalanceInitData;

typedef struct ColorBalanceThread {
	StripColorBalance *cb;
	float mul;

	int width, height;

	unsigned char *rect, *mask_rect;
	float *rect_float, *mask_rect_float;

	short make_float;
} ColorBalanceThread;

static void color_balance_init_handle(void *handle_v, int start_line, int tot_line, void *init_data_v)
{
	ColorBalanceThread *handle = (ColorBalanceThread *) handle_v;
	ColorBalanceInitData *init_data = (ColorBalanceInitData *) init_data_v;
	ImBuf *ibuf = init_data->ibuf;
	ImBuf *mask = init_data->mask;

	int offset = 4 * start_line * ibuf->x;

	memset(handle, 0, sizeof(ColorBalanceThread));

	handle->cb = init_data->cb;
	handle->mul = init_data->mul;
	handle->width = ibuf->x;
	handle->height = tot_line;
	handle->make_float = init_data->make_float;

	if (ibuf->rect)
		handle->rect = (unsigned char *) ibuf->rect + offset;

	if (ibuf->rect_float)
		handle->rect_float = ibuf->rect_float + offset;

	if (mask) {
		if (mask->rect)
			handle->mask_rect = (unsigned char *) mask->rect + offset;

		if (mask->rect_float)
			handle->mask_rect_float = mask->rect_float + offset;
	}
	else {
		handle->mask_rect = NULL;
		handle->mask_rect_float = NULL;
	}
}

static void *color_balance_do_thread(void *thread_data_v)
{
	ColorBalanceThread *thread_data = (ColorBalanceThread *) thread_data_v;
	StripColorBalance *cb = thread_data->cb;
	int width = thread_data->width, height = thread_data->height;
	unsigned char *rect = thread_data->rect;
	unsigned char *mask_rect = thread_data->mask_rect;
	float *rect_float = thread_data->rect_float;
	float *mask_rect_float = thread_data->mask_rect_float;
	float mul = thread_data->mul;

	if (rect_float) {
		color_balance_float_float(cb, rect_float, mask_rect_float, width, height, mul);
	}
	else if (thread_data->make_float) {
		color_balance_byte_float(cb, rect, rect_float, mask_rect, width, height, mul);
	}
	else {
		color_balance_byte_byte(cb, rect, mask_rect, width, height, mul);
	}

	return NULL;
}

ImBuf *BKE_sequencer_render_mask_input(SeqRenderData context, int mask_input_type, Sequence *mask_sequence, Mask *mask_id, int cfra, int make_float)
{
	ImBuf *mask_input = NULL;

	if (mask_input_type == SEQUENCE_MASK_INPUT_STRIP) {
		if (mask_sequence) {
			mask_input = seq_render_strip(context, mask_sequence, cfra);

			if (make_float) {
				if (!mask_input->rect_float)
					IMB_float_from_rect(mask_input);
			}
			else {
				if (!mask_input->rect)
					IMB_rect_from_float(mask_input);
			}
		}
	}
	else if (mask_input_type == SEQUENCE_MASK_INPUT_ID) {
		mask_input = seq_render_mask(context, mask_id, cfra, make_float);
	}

	return mask_input;
}

void BKE_sequencer_color_balance_apply(StripColorBalance *cb, ImBuf *ibuf, float mul, short make_float, ImBuf *mask_input)
{
	ColorBalanceInitData init_data;

	if (!ibuf->rect_float && make_float)
		imb_addrectfloatImBuf(ibuf);

	init_data.cb = cb;
	init_data.ibuf = ibuf;
	init_data.mul = mul;
	init_data.mask = NULL;
	init_data.make_float = make_float;
	init_data.mask = mask_input;

	IMB_processor_apply_threaded(ibuf->y, sizeof(ColorBalanceThread), &init_data,
                                 color_balance_init_handle, color_balance_do_thread);

	/* color balance either happens on float buffer or byte buffer, but never on both,
	 * free byte buffer if there's float buffer since float buffer would be used for
	 * color balance in favor of byte buffer
	 */
	if (ibuf->rect_float && ibuf->rect)
		imb_freerectImBuf(ibuf);
}

/*
 *  input preprocessing for SEQ_TYPE_IMAGE, SEQ_TYPE_MOVIE, SEQ_TYPE_MOVIECLIP and SEQ_TYPE_SCENE
 *
 *  Do all the things you can't really do afterwards using sequence effects
 *  (read: before rescaling to render resolution has been done)
 *
 *  Order is important!
 *
 *  - Deinterlace
 *  - Crop and transform in image source coordinate space
 *  - Flip X + Flip Y (could be done afterwards, backward compatibility)
 *  - Promote image to float data (affects pipeline operations afterwards)
 *  - Color balance (is most efficient in the byte -> float
 *    (future: half -> float should also work fine!)
 *    case, if done on load, since we can use lookup tables)
 *  - Premultiply
 */

int BKE_sequencer_input_have_to_preprocess(SeqRenderData UNUSED(context), Sequence *seq, float UNUSED(cfra))
{
	float mul;

	if (seq->flag & (SEQ_FILTERY | SEQ_USE_CROP | SEQ_USE_TRANSFORM | SEQ_FLIPX | SEQ_FLIPY | SEQ_MAKE_PREMUL | SEQ_MAKE_FLOAT)) {
		return TRUE;
	}

	mul = seq->mul;

	if (seq->blend_mode == SEQ_BLEND_REPLACE) {
		mul *= seq->blend_opacity / 100.0f;
	}

	if (mul != 1.0f) {
		return TRUE;
	}

	if (seq->sat != 1.0f) {
		return TRUE;
	}

	if (seq->modifiers.first) {
		return TRUE;
	}
		
	return FALSE;
}

static ImBuf *input_preprocess(SeqRenderData context, Sequence *seq, float cfra, ImBuf *ibuf,
                               int is_proxy_image, int is_preprocessed)
{
	float mul;

	ibuf = IMB_makeSingleUser(ibuf);

	if ((seq->flag & SEQ_FILTERY) &&
	    !ELEM(seq->type, SEQ_TYPE_MOVIE, SEQ_TYPE_MOVIECLIP))
	{
		IMB_filtery(ibuf);
	}

	if (seq->flag & (SEQ_USE_CROP | SEQ_USE_TRANSFORM)) {
		StripCrop c = {0};
		StripTransform t = {0};
		int sx, sy, dx, dy;

		if (is_proxy_image) {
			double f = seq_rendersize_to_scale_factor(context.preview_render_size);

			if (f != 1.0) {
				IMB_scalefastImBuf(ibuf, ibuf->x / f, ibuf->y / f);
			}
		}

		if (seq->flag & SEQ_USE_CROP && seq->strip->crop) {
			c = *seq->strip->crop;
		}
		if (seq->flag & SEQ_USE_TRANSFORM && seq->strip->transform) {
			t = *seq->strip->transform;
		}

		sx = ibuf->x - c.left - c.right;
		sy = ibuf->y - c.top - c.bottom;
		dx = sx;
		dy = sy;

		if (seq->flag & SEQ_USE_TRANSFORM) {
			if (is_preprocessed) {
				dx = context.rectx;
				dy = context.recty;
			}
			else {
				dx = context.scene->r.xsch;
				dy = context.scene->r.ysch;
			}
		}

		if (c.top  + c.bottom >= ibuf->y ||
		    c.left + c.right  >= ibuf->x ||
		    t.xofs >= dx || t.yofs >= dy)
		{
			make_black_ibuf(ibuf);
		}
		else {
			ImBuf *i = IMB_allocImBuf(dx, dy, 32, ibuf->rect_float ? IB_rectfloat : IB_rect);

			IMB_rectcpy(i, ibuf, t.xofs, t.yofs, c.left, c.bottom, sx, sy);
			
			IMB_freeImBuf(ibuf);

			ibuf = i;
		}
	}

	if (seq->flag & SEQ_FLIPX) {
		IMB_flipx(ibuf);
	}
	
	if (seq->flag & SEQ_FLIPY) {
		IMB_flipy(ibuf);
	}

	if (seq->sat != 1.0f) {
		IMB_saturation(ibuf, seq->sat);
	}

	mul = seq->mul;

	if (seq->blend_mode == SEQ_BLEND_REPLACE) {
		mul *= seq->blend_opacity / 100.0f;
	}

	if (seq->flag & SEQ_MAKE_FLOAT) {
		if (!ibuf->rect_float) {
			BKE_sequencer_imbuf_to_sequencer_space(context.scene, ibuf, TRUE);
		}

		if (ibuf->rect) {
			imb_freerectImBuf(ibuf);
		}
	}

	if (mul != 1.0f) {
		multibuf(ibuf, mul);
	}

	if (seq->flag & SEQ_MAKE_PREMUL) {
		if (ibuf->planes == 32 && ibuf->zbuf == NULL) {
			IMB_premultiply_alpha(ibuf);
		}
	}

	if (ibuf->x != context.rectx || ibuf->y != context.recty) {
		if (context.scene->r.mode & R_OSA) {
			IMB_scaleImBuf(ibuf, (short)context.rectx, (short)context.recty);
		}
		else {
			IMB_scalefastImBuf(ibuf, (short)context.rectx, (short)context.recty);
		}
	}

	if (seq->modifiers.first) {
		ImBuf *ibuf_new = BKE_sequence_modifier_apply_stack(context, seq, ibuf, cfra);

		if (ibuf_new != ibuf) {
			IMB_freeImBuf(ibuf);
			ibuf = ibuf_new;
		}
	}

	return ibuf;
}

static ImBuf *copy_from_ibuf_still(SeqRenderData context, Sequence *seq, float nr)
{
	ImBuf *rval = NULL;
	ImBuf *ibuf = NULL;

	if (nr == 0) {
		ibuf = BKE_sequencer_cache_get(context, seq, seq->start, SEQ_STRIPELEM_IBUF_STARTSTILL);
	}
	else if (nr == seq->len - 1) {
		ibuf = BKE_sequencer_cache_get(context, seq, seq->start, SEQ_STRIPELEM_IBUF_ENDSTILL);
	}

	if (ibuf) {
		rval = IMB_dupImBuf(ibuf);
		IMB_freeImBuf(ibuf);
	}

	return rval;
}

static void copy_to_ibuf_still(SeqRenderData context, Sequence *seq, float nr, ImBuf *ibuf)
{
	/* warning: ibuf may be NULL if the video fails to load */
	if (nr == 0 || nr == seq->len - 1) {
		/* we have to store a copy, since the passed ibuf
		 * could be preprocessed afterwards (thereby silently
		 * changing the cached image... */
		ibuf = IMB_dupImBuf(ibuf);

		if (ibuf) {
			sequencer_imbuf_assign_spaces(context.scene, ibuf);
		}

		if (nr == 0) {
			BKE_sequencer_cache_put(context, seq, seq->start, SEQ_STRIPELEM_IBUF_STARTSTILL, ibuf);
		}

		if (nr == seq->len - 1) {
			BKE_sequencer_cache_put(context, seq, seq->start, SEQ_STRIPELEM_IBUF_ENDSTILL, ibuf);
		}

		IMB_freeImBuf(ibuf);
	}
}

/*********************** strip rendering functions  *************************/

typedef struct RenderEffectInitData {
	struct SeqEffectHandle *sh;
	SeqRenderData context;
	Sequence *seq;
	float cfra, facf0, facf1;
	ImBuf *ibuf1, *ibuf2, *ibuf3;

	ImBuf *out;
} RenderEffectInitData;

typedef struct RenderEffectThread {
	struct SeqEffectHandle *sh;
	SeqRenderData context;
	Sequence *seq;
	float cfra, facf0, facf1;
	ImBuf *ibuf1, *ibuf2, *ibuf3;

	ImBuf *out;
	int start_line, tot_line;
} RenderEffectThread;

static void render_effect_execute_init_handle(void *handle_v, int start_line, int tot_line, void *init_data_v)
{
	RenderEffectThread *handle = (RenderEffectThread *) handle_v;
	RenderEffectInitData *init_data = (RenderEffectInitData *) init_data_v;

	handle->sh = init_data->sh;
	handle->context = init_data->context;
	handle->seq = init_data->seq;
	handle->cfra = init_data->cfra;
	handle->facf0 = init_data->facf0;
	handle->facf1 = init_data->facf1;
	handle->ibuf1 = init_data->ibuf1;
	handle->ibuf2 = init_data->ibuf2;
	handle->ibuf3 = init_data->ibuf3;
	handle->out = init_data->out;

	handle->start_line = start_line;
	handle->tot_line = tot_line;
}

static void *render_effect_execute_do_thread(void *thread_data_v)
{
	RenderEffectThread *thread_data = (RenderEffectThread *) thread_data_v;

	thread_data->sh->execute_slice(thread_data->context, thread_data->seq, thread_data->cfra,
	                               thread_data->facf0, thread_data->facf1, thread_data->ibuf1,
	                               thread_data->ibuf2, thread_data->ibuf3, thread_data->start_line,
	                               thread_data->tot_line, thread_data->out);

	return NULL;
}

static ImBuf *seq_render_effect_execute_threaded(struct SeqEffectHandle *sh, SeqRenderData context, Sequence *seq,
                                                 float cfra, float facf0, float facf1,
                                                 ImBuf *ibuf1, ImBuf *ibuf2, ImBuf *ibuf3)
{
	RenderEffectInitData init_data;
	ImBuf *out = sh->init_execution(context, ibuf1, ibuf2, ibuf3);

	init_data.sh = sh;
	init_data.context = context;
	init_data.seq = seq;
	init_data.cfra = cfra;
	init_data.facf0 = facf0;
	init_data.facf1 = facf1;
	init_data.ibuf1 = ibuf1;
	init_data.ibuf2 = ibuf2;
	init_data.ibuf3 = ibuf3;
	init_data.out = out;

	IMB_processor_apply_threaded(out->y, sizeof(RenderEffectThread), &init_data,
                                 render_effect_execute_init_handle, render_effect_execute_do_thread);

	return out;
}

static ImBuf *seq_render_effect_strip_impl(SeqRenderData context, Sequence *seq, float cfra)
{
	float fac, facf;
	int early_out;
	int i;
	struct SeqEffectHandle sh = BKE_sequence_get_effect(seq);
	FCurve *fcu = NULL;
	ImBuf *ibuf[3];
	Sequence *input[3];
	ImBuf *out = NULL;

	ibuf[0] = ibuf[1] = ibuf[2] = NULL;

	input[0] = seq->seq1; input[1] = seq->seq2; input[2] = seq->seq3;

	if (!sh.execute && !(sh.execute_slice && sh.init_execution)) {
		/* effect not supported in this version... */
		out = IMB_allocImBuf(context.rectx, context.recty, 32, IB_rect);
		return out;
	}

	if (seq->flag & SEQ_USE_EFFECT_DEFAULT_FADE) {
		sh.get_default_fac(seq, cfra, &fac, &facf);
		
		if ((context.scene->r.mode & R_FIELDS) == 0)
			facf = fac;
	}
	else {
		fcu = id_data_find_fcurve(&context.scene->id, seq, &RNA_Sequence, "effect_fader", 0, NULL);
		if (fcu) {
			fac = facf = evaluate_fcurve(fcu, cfra);
			if (context.scene->r.mode & R_FIELDS) {
				facf = evaluate_fcurve(fcu, cfra + 0.5f);
			}
		}
		else {
			fac = facf = seq->effect_fader;
		}
	}

	early_out = sh.early_out(seq, fac, facf);

	switch (early_out) {
		case EARLY_NO_INPUT:
			out = sh.execute(context, seq, cfra, fac, facf, NULL, NULL, NULL);
			break;
		case EARLY_DO_EFFECT:
			for (i = 0; i < 3; i++) {
				if (input[i])
					ibuf[i] = seq_render_strip(context, input[i], cfra);
			}

			if (ibuf[0] && ibuf[1]) {
				if (sh.multithreaded)
					out = seq_render_effect_execute_threaded(&sh, context, seq, cfra, fac, facf, ibuf[0], ibuf[1], ibuf[2]);
				else
					out = sh.execute(context, seq, cfra, fac, facf, ibuf[0], ibuf[1], ibuf[2]);
			}
			break;
		case EARLY_USE_INPUT_1:
			if (input[0]) {
				ibuf[0] = seq_render_strip(context, input[0], cfra);
			}
			if (ibuf[0]) {
				if (BKE_sequencer_input_have_to_preprocess(context, seq, cfra)) {
					out = IMB_dupImBuf(ibuf[0]);
				}
				else {
					out = ibuf[0];
					IMB_refImBuf(out);
				}
			}
			break;
		case EARLY_USE_INPUT_2:
			if (input[1]) {
				ibuf[1] = seq_render_strip(context, input[1], cfra);
			}
			if (ibuf[1]) {
				if (BKE_sequencer_input_have_to_preprocess(context, seq, cfra)) {
					out = IMB_dupImBuf(ibuf[1]);
				}
				else {
					out = ibuf[1];
					IMB_refImBuf(out);
				}
			}
			break;
	}

	for (i = 0; i < 3; i++) {
		IMB_freeImBuf(ibuf[i]);
	}

	if (out == NULL) {
		out = IMB_allocImBuf(context.rectx, context.recty, 32, IB_rect);
	}

	return out;
}

static ImBuf *seq_render_movieclip_strip(SeqRenderData context, Sequence *seq, float nr)
{
	ImBuf *ibuf = NULL;
	MovieClipUser user;
	float tloc[2], tscale, tangle;

	if (!seq->clip) {
		return NULL;
	}

	memset(&user, 0, sizeof(MovieClipUser));
	
	BKE_movieclip_user_set_frame(&user, nr + seq->anim_startofs + seq->clip->start_frame);

	user.render_size = MCLIP_PROXY_RENDER_SIZE_FULL;

	switch (seq_rendersize_to_proxysize(context.preview_render_size)) {
		case IMB_PROXY_NONE:
			user.render_size = MCLIP_PROXY_RENDER_SIZE_FULL;
			break;
		case IMB_PROXY_100:
			user.render_size = MCLIP_PROXY_RENDER_SIZE_100;
			break;
		case IMB_PROXY_75:
			user.render_size = MCLIP_PROXY_RENDER_SIZE_75;
			break;
		case IMB_PROXY_50:
			user.render_size = MCLIP_PROXY_RENDER_SIZE_50;
			break;
		case IMB_PROXY_25:
			user.render_size = MCLIP_PROXY_RENDER_SIZE_25;
			break;
	}

	if (seq->clip_flag & SEQ_MOVIECLIP_RENDER_UNDISTORTED) {
		user.render_flag = MCLIP_PROXY_RENDER_UNDISTORT;
	}

	if (seq->clip_flag & SEQ_MOVIECLIP_RENDER_STABILIZED) {
		ibuf = BKE_movieclip_get_stable_ibuf(seq->clip, &user, tloc, &tscale, &tangle, 0);
	}
	else {
		ibuf = BKE_movieclip_get_ibuf_flag(seq->clip, &user, 0, MOVIECLIP_CACHE_SKIP);
	}

	return ibuf;
}


static ImBuf *seq_render_mask(SeqRenderData context, Mask *mask, float nr, short make_float)
{
	/* TODO - add option to rasterize to alpha imbuf? */
	ImBuf *ibuf = NULL;
	float *maskbuf;
	int i;

	if (!mask) {
		return NULL;
	}
	else {
		Mask *mask_temp;
		MaskRasterHandle *mr_handle;

		mask_temp = BKE_mask_copy_nolib(mask);

		BKE_mask_evaluate(mask_temp, mask->sfra + nr, TRUE);

		maskbuf = MEM_mallocN(sizeof(float) * context.rectx * context.recty, __func__);

		mr_handle = BKE_maskrasterize_handle_new();

		BKE_maskrasterize_handle_init(mr_handle, mask_temp, context.rectx, context.recty, TRUE, TRUE, TRUE);

		BKE_mask_free_nolib(mask_temp);
		MEM_freeN(mask_temp);

		BKE_maskrasterize_buffer(mr_handle, context.rectx, context.recty, maskbuf);

		BKE_maskrasterize_handle_free(mr_handle);
	}


	if (make_float) {
		/* pixels */
		float *fp_src;
		float *fp_dst;

		ibuf = IMB_allocImBuf(context.rectx, context.recty, 32, IB_rectfloat);

		fp_src = maskbuf;
		fp_dst = ibuf->rect_float;
		i = context.rectx * context.recty;
		while (--i) {
			fp_dst[0] = fp_dst[1] = fp_dst[2] = *fp_src;
			fp_dst[3] = 1.0f;

			fp_src += 1;
			fp_dst += 4;
		}
	}
	else {
		/* pixels */
		float *fp_src;
		unsigned char *ub_dst;

		ibuf = IMB_allocImBuf(context.rectx, context.recty, 32, IB_rect);

		fp_src = maskbuf;
		ub_dst = (unsigned char *)ibuf->rect;
		i = context.rectx * context.recty;
		while (--i) {
			ub_dst[0] = ub_dst[1] = ub_dst[2] = (unsigned char)(*fp_src * 255.0f); /* already clamped */
			ub_dst[3] = 255;

			fp_src += 1;
			ub_dst += 4;
		}
	}

	MEM_freeN(maskbuf);

	return ibuf;
}

static ImBuf *seq_render_mask_strip(SeqRenderData context, Sequence *seq, float nr)
{
	short make_float = seq->flag & SEQ_MAKE_FLOAT;

	return seq_render_mask(context, seq->mask, nr, make_float);
}

static ImBuf *seq_render_scene_strip(SeqRenderData context, Sequence *seq, float nr)
{
	ImBuf *ibuf = NULL;
	float frame;
	float oldcfra;
	Object *camera;
	ListBase oldmarkers;
	
	/* Old info:
	 * Hack! This function can be called from do_render_seq(), in that case
	 * the seq->scene can already have a Render initialized with same name,
	 * so we have to use a default name. (compositor uses scene name to
	 * find render).
	 * However, when called from within the UI (image preview in sequencer)
	 * we do want to use scene Render, that way the render result is defined
	 * for display in render/imagewindow
	 *
	 * Hmm, don't see, why we can't do that all the time,
	 * and since G.is_rendering is uhm, gone... (Peter)
	 */

	/* New info:
	 * Using the same name for the renders works just fine as the do_render_seq()
	 * render is not used while the scene strips are rendered.
	 *
	 * However rendering from UI (through sequencer_preview_area_draw) can crash in
	 * very many cases since other renders (material preview, an actual render etc.)
	 * can be started while this sequence preview render is running. The only proper
	 * solution is to make the sequencer preview render a proper job, which can be
	 * stopped when needed. This would also give a nice progress bar for the preview
	 * space so that users know there's something happening.
	 *
	 * As a result the active scene now only uses OpenGL rendering for the sequencer
	 * preview. This is far from nice, but is the only way to prevent crashes at this
	 * time.
	 *
	 * -jahka
	 */

	const short is_rendering = G.is_rendering;
	const int do_seq_gl = G.is_rendering ?
	            0 /* (context.scene->r.seq_flag & R_SEQ_GL_REND) */ :
	            (context.scene->r.seq_flag & R_SEQ_GL_PREV);
	int do_seq;
	int have_seq = FALSE;
	Scene *scene;

	/* don't refer to seq->scene above this point!, it can be NULL */
	if (seq->scene == NULL) {
		return NULL;
	}

	scene = seq->scene;
	frame = scene->r.sfra + nr + seq->anim_startofs;

	have_seq = (scene->r.scemode & R_DOSEQ) && scene->ed && scene->ed->seqbase.first;

	oldcfra = scene->r.cfra;
	scene->r.cfra = frame;

	if (seq->scene_camera) {
		camera = seq->scene_camera;
	}
	else {
		BKE_scene_camera_switch_update(scene);
		camera = scene->camera;
	}

	if (have_seq == FALSE && camera == NULL) {
		scene->r.cfra = oldcfra;
		return NULL;
	}

	/* prevent eternal loop */
	do_seq = context.scene->r.scemode & R_DOSEQ;
	context.scene->r.scemode &= ~R_DOSEQ;
	
#ifdef DURIAN_CAMERA_SWITCH
	/* stooping to new low's in hackyness :( */
	oldmarkers = scene->markers;
	scene->markers.first = scene->markers.last = NULL;
#else
	(void)oldmarkers;
#endif

	if ((sequencer_view3d_cb && do_seq_gl && camera) &&
	    (BLI_thread_is_main() == TRUE) &&
	    ((have_seq == FALSE) || (scene == context.scene)))
	{
		char err_out[256] = "unknown";
		/* for old scened this can be uninitialized,
		 * should probably be added to do_versions at some point if the functionality stays */
		if (context.scene->r.seq_prev_type == 0)
			context.scene->r.seq_prev_type = 3 /* == OB_SOLID */;

		/* opengl offscreen render */
		BKE_scene_update_for_newframe(context.bmain, scene, scene->lay);
		ibuf = sequencer_view3d_cb(scene, camera, context.rectx, context.recty,
		                           IB_rect, context.scene->r.seq_prev_type, TRUE, FALSE, err_out);
		if (ibuf == NULL) {
			fprintf(stderr, "seq_render_scene_strip failed to get opengl buffer: %s\n", err_out);
		}
	}
	else {
		Render *re = RE_GetRender(scene->id.name);
		RenderResult rres;

		/* XXX: this if can be removed when sequence preview rendering uses the job system */
		if (is_rendering || context.scene != scene) {
			if (re == NULL)
				re = RE_NewRender(scene->id.name);
			
			RE_BlenderFrame(re, context.bmain, scene, NULL, camera, scene->lay, frame, FALSE);

			/* restore previous state after it was toggled on & off by RE_BlenderFrame */
			G.is_rendering = is_rendering;
		}
		
		RE_AcquireResultImage(re, &rres);
		
		if (rres.rectf) {
			ibuf = IMB_allocImBuf(rres.rectx, rres.recty, 32, IB_rectfloat);
			memcpy(ibuf->rect_float, rres.rectf, 4 * sizeof(float) * rres.rectx * rres.recty);
			if (rres.rectz) {
				addzbuffloatImBuf(ibuf);
				memcpy(ibuf->zbuf_float, rres.rectz, sizeof(float) * rres.rectx * rres.recty);
			}

			/* float buffers in the sequencer are not linear */
			BKE_sequencer_imbuf_to_sequencer_space(context.scene, ibuf, FALSE);
		}
		else if (rres.rect32) {
			ibuf = IMB_allocImBuf(rres.rectx, rres.recty, 32, IB_rect);
			memcpy(ibuf->rect, rres.rect32, 4 * rres.rectx * rres.recty);
		}
		
		RE_ReleaseResultImage(re);
		
		// BIF_end_render_callbacks();
	}
	
	/* restore */
	context.scene->r.scemode |= do_seq;
	
	scene->r.cfra = oldcfra;

	if (frame != oldcfra)
		BKE_scene_update_for_newframe(context.bmain, scene, scene->lay);
	
#ifdef DURIAN_CAMERA_SWITCH
	/* stooping to new low's in hackyness :( */
	scene->markers = oldmarkers;
#endif

	return ibuf;
}

static ImBuf *do_render_strip_uncached(SeqRenderData context, Sequence *seq, float cfra)
{
	ImBuf *ibuf = NULL;
	float nr = give_stripelem_index(seq, cfra);
	int type = (seq->type & SEQ_TYPE_EFFECT && seq->type != SEQ_TYPE_SPEED) ? SEQ_TYPE_EFFECT : seq->type;
	int use_preprocess = BKE_sequencer_input_have_to_preprocess(context, seq, cfra);
	char name[FILE_MAX];

	switch (type) {
		case SEQ_TYPE_META:
		{
			ImBuf *meta_ibuf = NULL;

			if (seq->seqbase.first)
				meta_ibuf = seq_render_strip_stack(context, &seq->seqbase, seq->start + nr, 0);

			if (meta_ibuf) {
				ibuf = meta_ibuf;
				if (ibuf && use_preprocess) {
					ImBuf *i = IMB_dupImBuf(ibuf);

					IMB_freeImBuf(ibuf);

					ibuf = i;
				}
			}

			break;
		}

		case SEQ_TYPE_SPEED:
		{
			ImBuf *child_ibuf = NULL;

			float f_cfra;
			SpeedControlVars *s = (SpeedControlVars *)seq->effectdata;

			BKE_sequence_effect_speed_rebuild_map(context.scene, seq, 0);

			/* weeek! */
			f_cfra = seq->start + s->frameMap[(int)nr];

			child_ibuf = seq_render_strip(context, seq->seq1, f_cfra);

			if (child_ibuf) {
				ibuf = child_ibuf;
				if (ibuf && use_preprocess) {
					ImBuf *i = IMB_dupImBuf(ibuf);

					IMB_freeImBuf(ibuf);

					ibuf = i;
				}
			}
			break;
		}

		case SEQ_TYPE_EFFECT:
		{
			ibuf = seq_render_effect_strip_impl(context, seq, seq->start + nr);
			break;
		}

		case SEQ_TYPE_IMAGE:
		{
			StripElem *s_elem = BKE_sequencer_give_stripelem(seq, cfra);

			if (s_elem) {
				BLI_join_dirfile(name, sizeof(name), seq->strip->dir, s_elem->name);
				BLI_path_abs(name, G.main->name);
			}

			/* OCIO_TODO: support configurable space for image strips */
			if (s_elem && (ibuf = IMB_loadiffname(name, IB_rect, NULL))) {
				/* we don't need both (speed reasons)! */
				if (ibuf->rect_float && ibuf->rect)
					imb_freerectImBuf(ibuf);

				/* all sequencer color is done in SRGB space, linear gives odd crossfades */
				BKE_sequencer_imbuf_to_sequencer_space(context.scene, ibuf, FALSE);

				copy_to_ibuf_still(context, seq, nr, ibuf);

				s_elem->orig_width  = ibuf->x;
				s_elem->orig_height = ibuf->y;
			}
			break;
		}

		case SEQ_TYPE_MOVIE:
		{
			seq_open_anim_file(seq);

			if (seq->anim) {
				IMB_anim_set_preseek(seq->anim, seq->anim_preseek);

				ibuf = IMB_anim_absolute(seq->anim, nr + seq->anim_startofs,
				                         seq->strip->proxy ? seq->strip->proxy->tc : IMB_TC_RECORD_RUN,
				                         seq_rendersize_to_proxysize(context.preview_render_size));

				/* we don't need both (speed reasons)! */
				if (ibuf && ibuf->rect_float && ibuf->rect)
					imb_freerectImBuf(ibuf);
				if (ibuf) {
					seq->strip->stripdata->orig_width = ibuf->x;
					seq->strip->stripdata->orig_height = ibuf->y;
				}
			}
			copy_to_ibuf_still(context, seq, nr, ibuf);
			break;
		}

		case SEQ_TYPE_SCENE:
		{
			/* scene can be NULL after deletions */
			ibuf = seq_render_scene_strip(context, seq, nr);

			/* Scene strips update all animation, so we need to restore original state.*/
			BKE_animsys_evaluate_all_animation(context.bmain, context.scene, cfra);

			copy_to_ibuf_still(context, seq, nr, ibuf);
			break;
		}

		case SEQ_TYPE_MOVIECLIP:
		{
			ibuf = seq_render_movieclip_strip(context, seq, nr);

			if (ibuf) {
				/* duplicate frame so movie cache wouldn't be confused by sequencer's stuff */
				ImBuf *i = IMB_dupImBuf(ibuf);
				IMB_freeImBuf(ibuf);
				ibuf = i;

				if (ibuf->rect_float)
					BKE_sequencer_imbuf_to_sequencer_space(context.scene, ibuf, FALSE);

				copy_to_ibuf_still(context, seq, nr, ibuf);
			}

			break;
		}

		case SEQ_TYPE_MASK:
		{
			/* ibuf is alwats new */
			ibuf = seq_render_mask_strip(context, seq, nr);

			copy_to_ibuf_still(context, seq, nr, ibuf);
			break;
		}
	}

	if (ibuf)
		sequencer_imbuf_assign_spaces(context.scene, ibuf);

	return ibuf;
}

static ImBuf *seq_render_strip(SeqRenderData context, Sequence *seq, float cfra)
{
	ImBuf *ibuf = NULL;
	int use_preprocess = BKE_sequencer_input_have_to_preprocess(context, seq, cfra);
	int is_proxy_image = FALSE;
	float nr = give_stripelem_index(seq, cfra);
	/* all effects are handled similarly with the exception of speed effect */
	int type = (seq->type & SEQ_TYPE_EFFECT && seq->type != SEQ_TYPE_SPEED) ? SEQ_TYPE_EFFECT : seq->type;
	int is_preprocessed = !ELEM3(type, SEQ_TYPE_IMAGE, SEQ_TYPE_MOVIE, SEQ_TYPE_SCENE);

	ibuf = BKE_sequencer_cache_get(context, seq, cfra, SEQ_STRIPELEM_IBUF);

	/* currently, we cache preprocessed images in SEQ_STRIPELEM_IBUF,
	 * but not(!) on SEQ_STRIPELEM_IBUF_ENDSTILL and ..._STARTSTILL */
	if (ibuf)
		use_preprocess = FALSE;

	if (ibuf == NULL)
		ibuf = copy_from_ibuf_still(context, seq, nr);

	if (ibuf == NULL) {
		ibuf = BKE_sequencer_preprocessed_cache_get(context, seq, cfra, SEQ_STRIPELEM_IBUF);

		if (ibuf == NULL) {
			/* MOVIECLIPs have their own proxy management */
			if (ibuf == NULL && seq->type != SEQ_TYPE_MOVIECLIP) {
				ibuf = seq_proxy_fetch(context, seq, cfra);
				is_proxy_image = (ibuf != NULL);
			}

			if (ibuf == NULL)
				ibuf = do_render_strip_uncached(context, seq, cfra);

			if (ibuf)
				BKE_sequencer_preprocessed_cache_put(context, seq, cfra, SEQ_STRIPELEM_IBUF, ibuf);
		}
	}

	if (ibuf == NULL) {
		ibuf = IMB_allocImBuf(context.rectx, context.recty, 32, IB_rect);
		sequencer_imbuf_assign_spaces(context.scene, ibuf);
	}

	if (ibuf->x != context.rectx || ibuf->y != context.recty)
		use_preprocess = TRUE;

	if (use_preprocess)
		ibuf = input_preprocess(context, seq, cfra, ibuf, is_proxy_image, is_preprocessed);

	BKE_sequencer_cache_put(context, seq, cfra, SEQ_STRIPELEM_IBUF, ibuf);

	return ibuf;
}

/*********************** strip stack rendering functions *************************/

static int seq_must_swap_input_in_blend_mode(Sequence *seq)
{
	int swap_input = FALSE;

	/* bad hack, to fix crazy input ordering of 
	 * those two effects */

	if (ELEM3(seq->blend_mode, SEQ_TYPE_ALPHAOVER, SEQ_TYPE_ALPHAUNDER, SEQ_TYPE_OVERDROP)) {
		swap_input = TRUE;
	}
	
	return swap_input;
}

static int seq_get_early_out_for_blend_mode(Sequence *seq)
{
	struct SeqEffectHandle sh = BKE_sequence_get_blend(seq);
	float facf = seq->blend_opacity / 100.0f;
	int early_out = sh.early_out(seq, facf, facf);
	
	if (ELEM(early_out, EARLY_DO_EFFECT, EARLY_NO_INPUT)) {
		return early_out;
	}

	if (seq_must_swap_input_in_blend_mode(seq)) {
		if (early_out == EARLY_USE_INPUT_2) {
			return EARLY_USE_INPUT_1;
		}
		else if (early_out == EARLY_USE_INPUT_1) {
			return EARLY_USE_INPUT_2;
		}
	}
	return early_out;
}

static ImBuf *seq_render_strip_stack(SeqRenderData context, ListBase *seqbasep, float cfra, int chanshown)
{
	Sequence *seq_arr[MAXSEQ + 1];
	int count;
	int i;
	ImBuf *out = NULL;

	count = get_shown_sequences(seqbasep, cfra, chanshown, (Sequence **)&seq_arr);

	if (count == 0) {
		return NULL;
	}

#if 0 /* commentind since this breaks keyframing, since it resets the value on draw */
	if (scene->r.cfra != cfra) {
		/* XXX for prefetch and overlay offset!..., very bad!!! */
		AnimData *adt = BKE_animdata_from_id(&scene->id);
		BKE_animsys_evaluate_animdata(scene, &scene->id, adt, cfra, ADT_RECALC_ANIM);
	}
#endif

	out = BKE_sequencer_cache_get(context, seq_arr[count - 1],  cfra, SEQ_STRIPELEM_IBUF_COMP);

	if (out) {
		return out;
	}
	
	if (count == 1) {
		out = seq_render_strip(context, seq_arr[0], cfra);

		BKE_sequencer_cache_put(context, seq_arr[0], cfra, SEQ_STRIPELEM_IBUF_COMP, out);

		return out;
	}

	for (i = count - 1; i >= 0; i--) {
		int early_out;
		Sequence *seq = seq_arr[i];

		out = BKE_sequencer_cache_get(context, seq, cfra, SEQ_STRIPELEM_IBUF_COMP);

		if (out) {
			break;
		}
		if (seq->blend_mode == SEQ_BLEND_REPLACE) {
			out = seq_render_strip(context, seq, cfra);
			break;
		}

		early_out = seq_get_early_out_for_blend_mode(seq);

		switch (early_out) {
			case EARLY_NO_INPUT:
			case EARLY_USE_INPUT_2:
				out = seq_render_strip(context, seq, cfra);
				break;
			case EARLY_USE_INPUT_1:
				if (i == 0) {
					out = IMB_allocImBuf(context.rectx, context.recty, 32, IB_rect);
				}
				break;
			case EARLY_DO_EFFECT:
				if (i == 0) {
					out = seq_render_strip(context, seq, cfra);
				}

				break;
		}
		if (out) {
			break;
		}
	}

	BKE_sequencer_cache_put(context, seq_arr[i], cfra, SEQ_STRIPELEM_IBUF_COMP, out);

	i++;

	for (; i < count; i++) {
		Sequence *seq = seq_arr[i];

		if (seq_get_early_out_for_blend_mode(seq) == EARLY_DO_EFFECT) {
			struct SeqEffectHandle sh = BKE_sequence_get_blend(seq);
			ImBuf *ibuf1 = out;
			ImBuf *ibuf2 = seq_render_strip(context, seq, cfra);

			float facf = seq->blend_opacity / 100.0f;
			int swap_input = seq_must_swap_input_in_blend_mode(seq);

			if (swap_input) {
				if (sh.multithreaded)
					out = seq_render_effect_execute_threaded(&sh, context, seq, cfra, facf, facf, ibuf2, ibuf1, NULL);
				else
					out = sh.execute(context, seq, cfra, facf, facf, ibuf2, ibuf1, NULL);
			}
			else {
				if (sh.multithreaded)
					out = seq_render_effect_execute_threaded(&sh, context, seq, cfra, facf, facf, ibuf1, ibuf2, NULL);
				else
					out = sh.execute(context, seq, cfra, facf, facf, ibuf1, ibuf2, NULL);
			}
		
			IMB_freeImBuf(ibuf1);
			IMB_freeImBuf(ibuf2);
		}

		BKE_sequencer_cache_put(context, seq_arr[i], cfra, SEQ_STRIPELEM_IBUF_COMP, out);
	}

	return out;
}

/*
 * returned ImBuf is refed!
 * you have to free after usage!
 */

ImBuf *BKE_sequencer_give_ibuf(SeqRenderData context, float cfra, int chanshown)
{
	Editing *ed = BKE_sequencer_editing_get(context.scene, FALSE);
	int count;
	ListBase *seqbasep;
	
	if (ed == NULL) return NULL;

	count = BLI_countlist(&ed->metastack);
	if ((chanshown < 0) && (count > 0)) {
		count = max_ii(count + chanshown, 0);
		seqbasep = ((MetaStack *)BLI_findlink(&ed->metastack, count))->oldbasep;
	}
	else {
		seqbasep = ed->seqbasep;
	}

	return seq_render_strip_stack(context, seqbasep, cfra, chanshown);
}

ImBuf *BKE_sequencer_give_ibuf_seqbase(SeqRenderData context, float cfra, int chanshown, ListBase *seqbasep)
{
	return seq_render_strip_stack(context, seqbasep, cfra, chanshown);
}


ImBuf *BKE_sequencer_give_ibuf_direct(SeqRenderData context, float cfra, Sequence *seq)
{
	return seq_render_strip(context, seq, cfra);
}

/* *********************** threading api ******************* */

static ListBase running_threads;
static ListBase prefetch_wait;
static ListBase prefetch_done;

static pthread_mutex_t queue_lock          = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t wakeup_lock         = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t wakeup_cond          = PTHREAD_COND_INITIALIZER;

//static pthread_mutex_t prefetch_ready_lock = PTHREAD_MUTEX_INITIALIZER;
//static pthread_cond_t  prefetch_ready_cond = PTHREAD_COND_INITIALIZER;

static pthread_mutex_t frame_done_lock     = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t frame_done_cond      = PTHREAD_COND_INITIALIZER;

static volatile int seq_thread_shutdown = TRUE; 
static volatile int seq_last_given_monoton_cfra = 0;
static int monoton_cfra = 0;

typedef struct PrefetchThread {
	struct PrefetchThread *next, *prev;
	
	Scene *scene;
	struct PrefetchQueueElem *current;
	pthread_t pthread;
	int running;
	
} PrefetchThread;

typedef struct PrefetchQueueElem {
	struct PrefetchQueueElem *next, *prev;
	
	int rectx;
	int recty;
	float cfra;
	int chanshown;
	int preview_render_size;

	int monoton_cfra;

	ImBuf *ibuf;
} PrefetchQueueElem;

void BKE_sequencer_give_ibuf_prefetch_request(SeqRenderData context, float cfra, int chanshown)
{
	PrefetchQueueElem *e;
	if (seq_thread_shutdown) {
		return;
	}

	e = MEM_callocN(sizeof(PrefetchQueueElem), "prefetch_queue_elem");
	e->rectx = context.rectx;
	e->recty = context.recty;
	e->cfra = cfra;
	e->chanshown = chanshown;
	e->preview_render_size = context.preview_render_size;
	e->monoton_cfra = monoton_cfra++;

	pthread_mutex_lock(&queue_lock);
	BLI_addtail(&prefetch_wait, e);
	pthread_mutex_unlock(&queue_lock);
	
	pthread_mutex_lock(&wakeup_lock);
	pthread_cond_signal(&wakeup_cond);
	pthread_mutex_unlock(&wakeup_lock);
}

ImBuf *BKE_sequencer_give_ibuf_threaded(SeqRenderData context, float cfra, int chanshown)
{
	PrefetchQueueElem *e = NULL;
	int found_something = FALSE;

	if (seq_thread_shutdown) {
		return BKE_sequencer_give_ibuf(context, cfra, chanshown);
	}

	while (!e) {
		int success = FALSE;
		pthread_mutex_lock(&queue_lock);

		for (e = prefetch_done.first; e; e = e->next) {
			if (cfra == e->cfra &&
			    chanshown == e->chanshown &&
			    context.rectx == e->rectx &&
			    context.recty == e->recty &&
			    context.preview_render_size == e->preview_render_size)
			{
				success = TRUE;
				found_something = TRUE;
				break;
			}
		}

		if (!e) {
			for (e = prefetch_wait.first; e; e = e->next) {
				if (cfra == e->cfra &&
				    chanshown == e->chanshown &&
				    context.rectx == e->rectx &&
				    context.recty == e->recty &&
				    context.preview_render_size == e->preview_render_size)
				{
					found_something = TRUE;
					break;
				}
			}
		}

		if (!e) {
			PrefetchThread *tslot;

			for (tslot = running_threads.first;
			     tslot;
			     tslot = tslot->next)
			{
				if (tslot->current &&
				    cfra == tslot->current->cfra &&
				    chanshown == tslot->current->chanshown &&
				    context.rectx == tslot->current->rectx &&
				    context.recty == tslot->current->recty &&
				    context.preview_render_size == tslot->current->preview_render_size)
				{
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
				fprintf(stderr, "SEQ-THREAD: Requested frame not in queue ???\n");
				break;
			}
			pthread_mutex_lock(&frame_done_lock);
			pthread_cond_wait(&frame_done_cond, &frame_done_lock);
			pthread_mutex_unlock(&frame_done_lock);
		}
	}
	
	return e ? e->ibuf : NULL;
}

/* Functions to free imbuf and anim data on changes */

static void free_anim_seq(Sequence *seq)
{
	if (seq->anim) {
		IMB_free_anim(seq->anim);
		seq->anim = NULL;
	}
}

/* check whether sequence cur depends on seq */
int BKE_sequence_check_depend(Sequence *seq, Sequence *cur)
{
	if (cur->seq1 == seq || cur->seq2 == seq || cur->seq3 == seq)
		return TRUE;

	/* sequences are not intersecting in time, assume no dependency exists between them */
	if (cur->enddisp < seq->startdisp || cur->startdisp > seq->enddisp)
		return FALSE;

	/* checking sequence is below reference one, not dependent on it */
	if (cur->machine < seq->machine)
		return FALSE;

	/* sequence is not blending with lower machines, no dependency here occurs
	 * check for non-effects only since effect could use lower machines as input
	 */
	if ((cur->type & SEQ_TYPE_EFFECT) == 0 &&
		    ((cur->blend_mode == SEQ_BLEND_REPLACE) ||
	         (cur->blend_mode == SEQ_TYPE_CROSS && cur->blend_opacity == 100.0f)))
	{
		return FALSE;
	}

	return TRUE;
}

static void sequence_do_invalidate_dependent(Sequence *seq, ListBase *seqbase)
{
	Sequence *cur;

	for (cur = seqbase->first; cur; cur = cur->next) {
		if (cur == seq)
			continue;

		if (BKE_sequence_check_depend(seq, cur)) {
			BKE_sequencer_cache_cleanup_sequence(cur);
			BKE_sequencer_preprocessed_cache_cleanup_sequence(cur);
		}

		if (cur->seqbase.first)
			sequence_do_invalidate_dependent(seq, &cur->seqbase);
	}
}

static void sequence_invalidate_cache(Scene *scene, Sequence *seq, int invalidate_self, int invalidate_preprocess)
{
	Editing *ed = scene->ed;

	/* invalidate cache for current sequence */
	if (invalidate_self)
		BKE_sequencer_cache_cleanup_sequence(seq);

	/* if invalidation is invoked from sequence free routine, effectdata would be NULL here */
	if (seq->effectdata && seq->type == SEQ_TYPE_SPEED)
		BKE_sequence_effect_speed_rebuild_map(scene, seq, TRUE);

	if (invalidate_preprocess)
		BKE_sequencer_preprocessed_cache_cleanup_sequence(seq);

	/* invalidate cache for all dependent sequences */

	/* NOTE: can not use SEQ_BEGIN/SEQ_END here because that macro will change sequence's depth,
	 *       which makes transformation routines work incorrect
	 */
	sequence_do_invalidate_dependent(seq, &ed->seqbase);
}

void BKE_sequence_invalidate_cache(Scene *scene, Sequence *seq)
{
	sequence_invalidate_cache(scene, seq, TRUE, TRUE);
}

void BKE_sequence_invalidate_dependent(Scene *scene, Sequence *seq)
{
	sequence_invalidate_cache(scene, seq, FALSE, TRUE);
}

void BKE_sequence_invalidate_cache_for_modifier(Scene *scene, Sequence *seq)
{
	sequence_invalidate_cache(scene, seq, TRUE, FALSE);
}

void BKE_sequencer_free_imbuf(Scene *scene, ListBase *seqbase, int for_render)
{
	Sequence *seq;

	BKE_sequencer_cache_cleanup();

	for (seq = seqbase->first; seq; seq = seq->next) {
		if (for_render && CFRA >= seq->startdisp && CFRA <= seq->enddisp) {
			continue;
		}

		if (seq->strip) {
			if (seq->type == SEQ_TYPE_MOVIE) {
				free_anim_seq(seq);
			}
			if (seq->type == SEQ_TYPE_SPEED) {
				BKE_sequence_effect_speed_rebuild_map(scene, seq, 1);
			}
		}
		if (seq->type == SEQ_TYPE_META) {
			BKE_sequencer_free_imbuf(scene, &seq->seqbase, for_render);
		}
		if (seq->type == SEQ_TYPE_SCENE) {
			/* FIXME: recurs downwards, 
			 * but do recurs protection somehow! */
		}
	}
	
}

static int update_changed_seq_recurs(Scene *scene, Sequence *seq, Sequence *changed_seq, int len_change, int ibuf_change)
{
	Sequence *subseq;
	int free_imbuf = 0;
	
	/* recurs downwards to see if this seq depends on the changed seq */
	
	if (seq == NULL)
		return 0;
	
	if (seq == changed_seq)
		free_imbuf = 1;
	
	for (subseq = seq->seqbase.first; subseq; subseq = subseq->next)
		if (update_changed_seq_recurs(scene, subseq, changed_seq, len_change, ibuf_change))
			free_imbuf = TRUE;
	
	if (seq->seq1)
		if (update_changed_seq_recurs(scene, seq->seq1, changed_seq, len_change, ibuf_change))
			free_imbuf = TRUE;
	if (seq->seq2 && (seq->seq2 != seq->seq1))
		if (update_changed_seq_recurs(scene, seq->seq2, changed_seq, len_change, ibuf_change))
			free_imbuf = TRUE;
	if (seq->seq3 && (seq->seq3 != seq->seq1) && (seq->seq3 != seq->seq2))
		if (update_changed_seq_recurs(scene, seq->seq3, changed_seq, len_change, ibuf_change))
			free_imbuf = TRUE;
	
	if (free_imbuf) {
		if (ibuf_change) {
			if (seq->type == SEQ_TYPE_MOVIE)
				free_anim_seq(seq);
			if (seq->type == SEQ_TYPE_SPEED) {
				BKE_sequence_effect_speed_rebuild_map(scene, seq, 1);
			}
		}
		
		if (len_change)
			BKE_sequence_calc(scene, seq);
	}
	
	return free_imbuf;
}

void BKE_sequencer_update_changed_seq_and_deps(Scene *scene, Sequence *changed_seq, int len_change, int ibuf_change)
{
	Editing *ed = BKE_sequencer_editing_get(scene, FALSE);
	Sequence *seq;
	
	if (ed == NULL) return;
	
	for (seq = ed->seqbase.first; seq; seq = seq->next)
		update_changed_seq_recurs(scene, seq, changed_seq, len_change, ibuf_change);
}

/* seq funcs's for transforming internally
 * notice the difference between start/end and left/right.
 *
 * left and right are the bounds at which the sequence is rendered,
 * start and end are from the start and fixed length of the sequence.
 */
static int seq_tx_get_start(Sequence *seq)
{
	return seq->start;
}
static int seq_tx_get_end(Sequence *seq)
{
	return seq->start + seq->len;
}

int BKE_sequence_tx_get_final_left(Sequence *seq, int metaclip)
{
	if (metaclip && seq->tmp) {
		/* return the range clipped by the parents range */
		return max_ii(BKE_sequence_tx_get_final_left(seq, 0), BKE_sequence_tx_get_final_left((Sequence *)seq->tmp, TRUE));
	}
	else {
		return (seq->start - seq->startstill) + seq->startofs;
	}

}
int BKE_sequence_tx_get_final_right(Sequence *seq, int metaclip)
{
	if (metaclip && seq->tmp) {
		/* return the range clipped by the parents range */
		return min_ii(BKE_sequence_tx_get_final_right(seq, 0), BKE_sequence_tx_get_final_right((Sequence *)seq->tmp, TRUE));
	}
	else {
		return ((seq->start + seq->len) + seq->endstill) - seq->endofs;
	}
}

void BKE_sequence_tx_set_final_left(Sequence *seq, int val)
{
	if (val < (seq)->start) {
		seq->startstill = abs(val - (seq)->start);
		seq->startofs = 0;
	}
	else {
		seq->startofs = abs(val - (seq)->start);
		seq->startstill = 0;
	}
}

void BKE_sequence_tx_set_final_right(Sequence *seq, int val)
{
	if (val > (seq)->start + (seq)->len) {
		seq->endstill = abs(val - (seq->start + (seq)->len));
		seq->endofs = 0;
	}
	else {
		seq->endofs = abs(val - ((seq)->start + (seq)->len));
		seq->endstill = 0;
	}
}

/* used so we can do a quick check for single image seq
 * since they work a bit differently to normal image seq's (during transform) */
int BKE_sequence_single_check(Sequence *seq)
{
	return ((seq->len == 1) &&
	        (seq->type == SEQ_TYPE_IMAGE ||
	         ((seq->type & SEQ_TYPE_EFFECT) &&
	          BKE_sequence_effect_get_num_inputs(seq->type) == 0)));
}

/* check if the selected seq's reference unselected seq's */
int BKE_sequence_base_isolated_sel_check(ListBase *seqbase)
{
	Sequence *seq;
	/* is there more than 1 select */
	int ok = FALSE;

	for (seq = seqbase->first; seq; seq = seq->next) {
		if (seq->flag & SELECT) {
			ok = TRUE;
			break;
		}
	}

	if (ok == FALSE)
		return FALSE;

	/* test relationships */
	for (seq = seqbase->first; seq; seq = seq->next) {
		if ((seq->type & SEQ_TYPE_EFFECT) == 0)
			continue;

		if (seq->flag & SELECT) {
			if ( (seq->seq1 && (seq->seq1->flag & SELECT) == 0) ||
			     (seq->seq2 && (seq->seq2->flag & SELECT) == 0) ||
			     (seq->seq3 && (seq->seq3->flag & SELECT) == 0) )
			{
				return FALSE;
			}
		}
		else {
			if ( (seq->seq1 && (seq->seq1->flag & SELECT)) ||
			     (seq->seq2 && (seq->seq2->flag & SELECT)) ||
			     (seq->seq3 && (seq->seq3->flag & SELECT)) )
			{
				return FALSE;
			}
		}
	}

	return TRUE;
}

/* use to impose limits when dragging/extending - so impossible situations don't happen
 * Cant use the SEQ_LEFTSEL and SEQ_LEFTSEL directly because the strip may be in a metastrip */
void BKE_sequence_tx_handle_xlimits(Sequence *seq, int leftflag, int rightflag)
{
	if (leftflag) {
		if (BKE_sequence_tx_get_final_left(seq, 0) >= BKE_sequence_tx_get_final_right(seq, 0)) {
			BKE_sequence_tx_set_final_left(seq, BKE_sequence_tx_get_final_right(seq, 0) - 1);
		}

		if (BKE_sequence_single_check(seq) == 0) {
			if (BKE_sequence_tx_get_final_left(seq, 0) >= seq_tx_get_end(seq)) {
				BKE_sequence_tx_set_final_left(seq, seq_tx_get_end(seq) - 1);
			}

			/* dosnt work now - TODO */
#if 0
			if (seq_tx_get_start(seq) >= seq_tx_get_final_right(seq, 0)) {
				int ofs;
				ofs = seq_tx_get_start(seq) - seq_tx_get_final_right(seq, 0);
				seq->start -= ofs;
				seq_tx_set_final_left(seq, seq_tx_get_final_left(seq, 0) + ofs);
			}
#endif
		}
	}

	if (rightflag) {
		if (BKE_sequence_tx_get_final_right(seq, 0) <= BKE_sequence_tx_get_final_left(seq, 0)) {
			BKE_sequence_tx_set_final_right(seq, BKE_sequence_tx_get_final_left(seq, 0) + 1);
		}

		if (BKE_sequence_single_check(seq) == 0) {
			if (BKE_sequence_tx_get_final_right(seq, 0) <= seq_tx_get_start(seq)) {
				BKE_sequence_tx_set_final_right(seq, seq_tx_get_start(seq) + 1);
			}
		}
	}

	/* sounds cannot be extended past their endpoints */
	if (seq->type == SEQ_TYPE_SOUND_RAM) {
		seq->startstill = 0;
		seq->endstill = 0;
	}
}

void BKE_sequence_single_fix(Sequence *seq)
{
	int left, start, offset;
	if (!BKE_sequence_single_check(seq))
		return;

	/* make sure the image is always at the start since there is only one,
	 * adjusting its start should be ok */
	left = BKE_sequence_tx_get_final_left(seq, 0);
	start = seq->start;
	if (start != left) {
		offset = left - start;
		BKE_sequence_tx_set_final_left(seq, BKE_sequence_tx_get_final_left(seq, 0) - offset);
		BKE_sequence_tx_set_final_right(seq, BKE_sequence_tx_get_final_right(seq, 0) - offset);
		seq->start += offset;
	}
}

int BKE_sequence_tx_test(Sequence *seq)
{
	return (seq->type < SEQ_TYPE_EFFECT) || (BKE_sequence_effect_get_num_inputs(seq->type) == 0);
}

static int seq_overlap(Sequence *seq1, Sequence *seq2)
{
	return (seq1 != seq2 && seq1->machine == seq2->machine &&
	        ((seq1->enddisp <= seq2->startdisp) || (seq1->startdisp >= seq2->enddisp)) == 0);
}

int BKE_sequence_test_overlap(ListBase *seqbasep, Sequence *test)
{
	Sequence *seq;

	seq = seqbasep->first;
	while (seq) {
		if (seq_overlap(test, seq))
			return 1;

		seq = seq->next;
	}
	return 0;
}


void BKE_sequence_translate(Scene *evil_scene, Sequence *seq, int delta)
{
	BKE_sequencer_offset_animdata(evil_scene, seq, delta);
	seq->start += delta;

	if (seq->type == SEQ_TYPE_META) {
		Sequence *seq_child;
		for (seq_child = seq->seqbase.first; seq_child; seq_child = seq_child->next) {
			BKE_sequence_translate(evil_scene, seq_child, delta);
		}
	}

	BKE_sequence_calc_disp(evil_scene, seq);
}

void BKE_sequence_sound_init(Scene *scene, Sequence *seq)
{
	if (seq->type == SEQ_TYPE_META) {
		Sequence *seq_child;
		for (seq_child = seq->seqbase.first; seq_child; seq_child = seq_child->next) {
			BKE_sequence_sound_init(scene, seq_child);
		}
	}
	else {
		if (seq->sound) {
			seq->scene_sound = sound_add_scene_sound_defaults(scene, seq);
		}
		if (seq->scene) {
			sound_scene_add_scene_sound_defaults(scene, seq);
		}
	}
}

Sequence *BKE_sequencer_foreground_frame_get(Scene *scene, int frame)
{
	Editing *ed = BKE_sequencer_editing_get(scene, FALSE);
	Sequence *seq, *best_seq = NULL;
	int best_machine = -1;
	
	if (!ed) return NULL;
	
	for (seq = ed->seqbasep->first; seq; seq = seq->next) {
		if (seq->flag & SEQ_MUTE || seq->startdisp > frame || seq->enddisp <= frame)
			continue;
		/* only use elements you can see - not */
		if (ELEM5(seq->type, SEQ_TYPE_IMAGE, SEQ_TYPE_META, SEQ_TYPE_SCENE, SEQ_TYPE_MOVIE, SEQ_TYPE_COLOR)) {
			if (seq->machine > best_machine) {
				best_seq = seq;
				best_machine = seq->machine;
			}
		}
	}
	return best_seq;
}

/* return 0 if there werent enough space */
int BKE_sequence_base_shuffle(ListBase *seqbasep, Sequence *test, Scene *evil_scene)
{
	int orig_machine = test->machine;
	test->machine++;
	BKE_sequence_calc(evil_scene, test);
	while (BKE_sequence_test_overlap(seqbasep, test) ) {
		if (test->machine >= MAXSEQ) {
			break;
		}
		test->machine++;
		BKE_sequence_calc(evil_scene, test); // XXX - I don't think this is needed since were only moving vertically, Campbell.
	}

	
	if (test->machine >= MAXSEQ) {
		/* Blender 2.4x would remove the strip.
		 * nicer to move it to the end */

		Sequence *seq;
		int new_frame = test->enddisp;

		for (seq = seqbasep->first; seq; seq = seq->next) {
			if (seq->machine == orig_machine)
				new_frame = max_ii(new_frame, seq->enddisp);
		}

		test->machine = orig_machine;
		new_frame = new_frame + (test->start - test->startdisp); /* adjust by the startdisp */
		BKE_sequence_translate(evil_scene, test, new_frame - test->start);

		BKE_sequence_calc(evil_scene, test);
		return 0;
	}
	else {
		return 1;
	}
}

static int shuffle_seq_time_offset_test(ListBase *seqbasep, char dir)
{
	int offset = 0;
	Sequence *seq, *seq_other;

	for (seq = seqbasep->first; seq; seq = seq->next) {
		if (seq->tmp) {
			for (seq_other = seqbasep->first; seq_other; seq_other = seq_other->next) {
				if (!seq_other->tmp && seq_overlap(seq, seq_other)) {
					if (dir == 'L') {
						offset = min_ii(offset, seq_other->startdisp - seq->enddisp);
					}
					else {
						offset = max_ii(offset, seq_other->enddisp - seq->startdisp);
					}
				}
			}
		}
	}
	return offset;
}

static int shuffle_seq_time_offset(Scene *scene, ListBase *seqbasep, char dir)
{
	int ofs = 0;
	int tot_ofs = 0;
	Sequence *seq;
	while ( (ofs = shuffle_seq_time_offset_test(seqbasep, dir)) ) {
		for (seq = seqbasep->first; seq; seq = seq->next) {
			if (seq->tmp) {
				/* seq_test_overlap only tests display values */
				seq->startdisp +=   ofs;
				seq->enddisp +=     ofs;
			}
		}

		tot_ofs += ofs;
	}

	for (seq = seqbasep->first; seq; seq = seq->next) {
		if (seq->tmp)
			BKE_sequence_calc_disp(scene, seq);  /* corrects dummy startdisp/enddisp values */
	}

	return tot_ofs;
}

int BKE_sequence_base_shuffle_time(ListBase *seqbasep, Scene *evil_scene)
{
	/* note: seq->tmp is used to tag strips to move */

	Sequence *seq;

	int offset_l = shuffle_seq_time_offset(evil_scene, seqbasep, 'L');
	int offset_r = shuffle_seq_time_offset(evil_scene, seqbasep, 'R');
	int offset = (-offset_l < offset_r) ?  offset_l : offset_r;

	if (offset) {
		for (seq = seqbasep->first; seq; seq = seq->next) {
			if (seq->tmp) {
				BKE_sequence_translate(evil_scene, seq, offset);
				seq->flag &= ~SEQ_OVERLAP;
			}
		}
	}

	return offset ? 0 : 1;
}

void BKE_sequencer_update_sound_bounds_all(Scene *scene)
{
	Editing *ed = scene->ed;

	if (ed) {
		Sequence *seq;

		for (seq = ed->seqbase.first; seq; seq = seq->next) {
			if (seq->type == SEQ_TYPE_META) {
				seq_update_sound_bounds_recursive(scene, seq);
			}
			else if (ELEM(seq->type, SEQ_TYPE_SOUND_RAM, SEQ_TYPE_SCENE)) {
				BKE_sequencer_update_sound_bounds(scene, seq);
			}
		}
	}
}

void BKE_sequencer_update_sound_bounds(Scene *scene, Sequence *seq)
{
	sound_move_scene_sound_defaults(scene, seq);
	/* mute is set in seq_update_muting_recursive */
}

static void seq_update_muting_recursive(ListBase *seqbasep, Sequence *metaseq, int mute)
{
	Sequence *seq;
	int seqmute;

	/* for sound we go over full meta tree to update muted state,
	 * since sound is played outside of evaluating the imbufs, */
	for (seq = seqbasep->first; seq; seq = seq->next) {
		seqmute = (mute || (seq->flag & SEQ_MUTE));

		if (seq->type == SEQ_TYPE_META) {
			/* if this is the current meta sequence, unmute because
			 * all sequences above this were set to mute */
			if (seq == metaseq)
				seqmute = 0;

			seq_update_muting_recursive(&seq->seqbase, metaseq, seqmute);
		}
		else if (ELEM(seq->type, SEQ_TYPE_SOUND_RAM, SEQ_TYPE_SCENE)) {
			if (seq->scene_sound) {
				sound_mute_scene_sound(seq->scene_sound, seqmute);
			}
		}
	}
}

void BKE_sequencer_update_muting(Editing *ed)
{
	if (ed) {
		/* mute all sounds up to current metastack list */
		MetaStack *ms = ed->metastack.last;

		if (ms)
			seq_update_muting_recursive(&ed->seqbase, ms->parseq, 1);
		else
			seq_update_muting_recursive(&ed->seqbase, NULL, 0);
	}
}

static void seq_update_sound_recursive(Scene *scene, ListBase *seqbasep, bSound *sound)
{
	Sequence *seq;

	for (seq = seqbasep->first; seq; seq = seq->next) {
		if (seq->type == SEQ_TYPE_META) {
			seq_update_sound_recursive(scene, &seq->seqbase, sound);
		}
		else if (seq->type == SEQ_TYPE_SOUND_RAM) {
			if (seq->scene_sound && sound == seq->sound) {
				sound_update_scene_sound(seq->scene_sound, sound);
			}
		}
	}
}

void BKE_sequencer_update_sound(Scene *scene, bSound *sound)
{
	if (scene->ed) {
		seq_update_sound_recursive(scene, &scene->ed->seqbase, sound);
	}
}

/* in cases where we done know the sequence's listbase */
ListBase *BKE_sequence_seqbase(ListBase *seqbase, Sequence *seq)
{
	Sequence *iseq;
	ListBase *lb = NULL;

	for (iseq = seqbase->first; iseq; iseq = iseq->next) {
		if (seq == iseq) {
			return seqbase;
		}
		else if (iseq->seqbase.first && (lb = BKE_sequence_seqbase(&iseq->seqbase, seq))) {
			return lb;
		}
	}

	return NULL;
}

Sequence *BKE_sequence_metastrip(ListBase *seqbase, Sequence *meta, Sequence *seq)
{
	Sequence *iseq;

	for (iseq = seqbase->first; iseq; iseq = iseq->next) {
		Sequence *rval;

		if (seq == iseq) {
			return meta;
		}
		else if (iseq->seqbase.first &&
		         (rval = BKE_sequence_metastrip(&iseq->seqbase, iseq, seq)))
		{
			return rval;
		}
	}

	return NULL;
}

int BKE_sequence_swap(Sequence *seq_a, Sequence *seq_b, const char **error_str)
{
	char name[sizeof(seq_a->name)];

	if (seq_a->len != seq_b->len) {
		*error_str = "Strips must be the same length";
		return 0;
	}

	/* type checking, could be more advanced but disalow sound vs non-sound copy */
	if (seq_a->type != seq_b->type) {
		if (seq_a->type == SEQ_TYPE_SOUND_RAM || seq_b->type == SEQ_TYPE_SOUND_RAM) {
			*error_str = "Strips were not compatible";
			return 0;
		}

		/* disallow effects to swap with non-effects strips */
		if ((seq_a->type & SEQ_TYPE_EFFECT) != (seq_b->type & SEQ_TYPE_EFFECT)) {
			*error_str = "Strips were not compatible";
			return 0;
		}

		if ((seq_a->type & SEQ_TYPE_EFFECT) && (seq_b->type & SEQ_TYPE_EFFECT)) {
			if (BKE_sequence_effect_get_num_inputs(seq_a->type) != BKE_sequence_effect_get_num_inputs(seq_b->type)) {
				*error_str = "Strips must have the same number of inputs";
				return 0;
			}
		}
	}

	SWAP(Sequence, *seq_a, *seq_b);

	/* swap back names so animation fcurves don't get swapped */
	BLI_strncpy(name, seq_a->name + 2, sizeof(name));
	BLI_strncpy(seq_a->name + 2, seq_b->name + 2, sizeof(seq_b->name) - 2);
	BLI_strncpy(seq_b->name + 2, name, sizeof(seq_b->name) - 2);

	/* swap back opacity, and overlay mode */
	SWAP(int, seq_a->blend_mode, seq_b->blend_mode);
	SWAP(float, seq_a->blend_opacity, seq_b->blend_opacity);


	SWAP(Sequence *, seq_a->prev, seq_b->prev);
	SWAP(Sequence *, seq_a->next, seq_b->next);
	SWAP(int, seq_a->start, seq_b->start);
	SWAP(int, seq_a->startofs, seq_b->startofs);
	SWAP(int, seq_a->endofs, seq_b->endofs);
	SWAP(int, seq_a->startstill, seq_b->startstill);
	SWAP(int, seq_a->endstill, seq_b->endstill);
	SWAP(int, seq_a->machine, seq_b->machine);
	SWAP(int, seq_a->startdisp, seq_b->startdisp);
	SWAP(int, seq_a->enddisp, seq_b->enddisp);

	return 1;
}

/* XXX - hackish function needed for transforming strips! TODO - have some better solution */
void BKE_sequencer_offset_animdata(Scene *scene, Sequence *seq, int ofs)
{
	char str[SEQ_NAME_MAXSTR + 3];
	FCurve *fcu;

	if (scene->adt == NULL || ofs == 0 || scene->adt->action == NULL)
		return;

	BLI_snprintf(str, sizeof(str), "[\"%s\"]", seq->name + 2);

	for (fcu = scene->adt->action->curves.first; fcu; fcu = fcu->next) {
		if (strstr(fcu->rna_path, "sequence_editor.sequences_all[") && strstr(fcu->rna_path, str)) {
			unsigned int i;
			for (i = 0; i < fcu->totvert; i++) {
				BezTriple *bezt = &fcu->bezt[i];
				bezt->vec[0][0] += ofs;
				bezt->vec[1][0] += ofs;
				bezt->vec[2][0] += ofs;
			}
		}
	}
}

void BKE_sequencer_dupe_animdata(Scene *scene, const char *name_src, const char *name_dst)
{
	char str_from[SEQ_NAME_MAXSTR + 3];
	FCurve *fcu;
	FCurve *fcu_last;
	FCurve *fcu_cpy;
	ListBase lb = {NULL, NULL};

	if (scene->adt == NULL || scene->adt->action == NULL)
		return;

	BLI_snprintf(str_from, sizeof(str_from), "[\"%s\"]", name_src);

	fcu_last = scene->adt->action->curves.last;

	for (fcu = scene->adt->action->curves.first; fcu && fcu->prev != fcu_last; fcu = fcu->next) {
		if (strstr(fcu->rna_path, "sequence_editor.sequences_all[") && strstr(fcu->rna_path, str_from)) {
			fcu_cpy = copy_fcurve(fcu);
			BLI_addtail(&lb, fcu_cpy);
		}
	}

	/* notice validate is 0, keep this because the seq may not be added to the scene yet */
	BKE_animdata_fix_paths_rename(&scene->id, scene->adt, NULL, "sequence_editor.sequences_all", name_src, name_dst, 0, 0, 0);

	/* add the original fcurves back */
	BLI_movelisttolist(&scene->adt->action->curves, &lb);
}

/* XXX - hackish function needed to remove all fcurves belonging to a sequencer strip */
static void seq_free_animdata(Scene *scene, Sequence *seq)
{
	char str[SEQ_NAME_MAXSTR + 3];
	FCurve *fcu;

	if (scene->adt == NULL || scene->adt->action == NULL)
		return;

	BLI_snprintf(str, sizeof(str), "[\"%s\"]", seq->name + 2);

	fcu = scene->adt->action->curves.first;

	while (fcu) {
		if (strstr(fcu->rna_path, "sequence_editor.sequences_all[") && strstr(fcu->rna_path, str)) {
			FCurve *next_fcu = fcu->next;
			
			BLI_remlink(&scene->adt->action->curves, fcu);
			free_fcurve(fcu);

			fcu = next_fcu;
		}
		else {
			fcu = fcu->next;
		}
	}
}

Sequence *BKE_sequence_get_by_name(ListBase *seqbase, const char *name, int recursive)
{
	Sequence *iseq = NULL;
	Sequence *rseq = NULL;

	for (iseq = seqbase->first; iseq; iseq = iseq->next) {
		if (strcmp(name, iseq->name + 2) == 0)
			return iseq;
		else if (recursive && (iseq->seqbase.first) && (rseq = BKE_sequence_get_by_name(&iseq->seqbase, name, 1))) {
			return rseq;
		}
	}

	return NULL;
}


Sequence *BKE_sequencer_active_get(Scene *scene)
{
	Editing *ed = BKE_sequencer_editing_get(scene, FALSE);

	if (ed == NULL)
		return NULL;

	return ed->act_seq;
}

void BKE_sequencer_active_set(Scene *scene, Sequence *seq)
{
	Editing *ed = BKE_sequencer_editing_get(scene, FALSE);

	if (ed == NULL)
		return;

	ed->act_seq = seq;
}

int BKE_sequencer_active_get_pair(Scene *scene, Sequence **seq_act, Sequence **seq_other)
{
	Editing *ed = BKE_sequencer_editing_get(scene, FALSE);

	*seq_act = BKE_sequencer_active_get(scene);

	if (*seq_act == NULL) {
		return 0;
	}
	else {
		Sequence *seq;

		*seq_other = NULL;

		for (seq = ed->seqbasep->first; seq; seq = seq->next) {
			if (seq->flag & SELECT && (seq != (*seq_act))) {
				if (*seq_other) {
					return 0;
				}
				else {
					*seq_other = seq;
				}
			}
		}

		return (*seq_other != NULL);
	}
}

Mask *BKE_sequencer_mask_get(Scene *scene)
{
	Sequence *seq_act = BKE_sequencer_active_get(scene);

	if (seq_act && seq_act->type == SEQ_TYPE_MASK) {
		return seq_act->mask;
	}
	else {
		return NULL;
	}
}

/* api like funcs for adding */

static void seq_load_apply(Scene *scene, Sequence *seq, SeqLoadInfo *seq_load)
{
	if (seq) {
		BLI_strncpy(seq->name + 2, seq_load->name, sizeof(seq->name) - 2);
		BKE_sequence_base_unique_name_recursive(&scene->ed->seqbase, seq);

		if (seq_load->flag & SEQ_LOAD_FRAME_ADVANCE) {
			seq_load->start_frame += (seq->enddisp - seq->startdisp);
		}

		if (seq_load->flag & SEQ_LOAD_REPLACE_SEL) {
			seq_load->flag |= SELECT;
			BKE_sequencer_active_set(scene, seq);
		}

		if (seq_load->flag & SEQ_LOAD_SOUND_CACHE) {
			if (seq->sound)
				sound_cache(seq->sound);
		}

		seq_load->tot_success++;
	}
	else {
		seq_load->tot_error++;
	}
}

Sequence *BKE_sequence_alloc(ListBase *lb, int cfra, int machine)
{
	Sequence *seq;

	seq = MEM_callocN(sizeof(Sequence), "addseq");
	BLI_addtail(lb, seq);

	*( (short *)seq->name) = ID_SEQ;
	seq->name[2] = 0;

	seq->flag = SELECT;
	seq->start = cfra;
	seq->machine = machine;
	seq->sat = 1.0;
	seq->mul = 1.0;
	seq->blend_opacity = 100.0;
	seq->volume = 1.0f;
	seq->pitch = 1.0f;
	seq->scene_sound = NULL;

	return seq;
}

/* NOTE: this function doesn't fill in image names */
Sequence *BKE_sequencer_add_image_strip(bContext *C, ListBase *seqbasep, SeqLoadInfo *seq_load)
{
	Scene *scene = CTX_data_scene(C); /* only for active seq */
	Sequence *seq;
	Strip *strip;

	seq = BKE_sequence_alloc(seqbasep, seq_load->start_frame, seq_load->channel);
	seq->type = SEQ_TYPE_IMAGE;
	seq->blend_mode = SEQ_TYPE_CROSS; /* so alpha adjustment fade to the strip below */
	
	/* basic defaults */
	seq->strip = strip = MEM_callocN(sizeof(Strip), "strip");

	seq->len = seq_load->len ? seq_load->len : 1;
	strip->us = 1;
	strip->stripdata = MEM_callocN(seq->len * sizeof(StripElem), "stripelem");
	BLI_strncpy(strip->dir, seq_load->path, sizeof(strip->dir));

	seq_load_apply(scene, seq, seq_load);

	return seq;
}

#ifdef WITH_AUDASPACE
Sequence *BKE_sequencer_add_sound_strip(bContext *C, ListBase *seqbasep, SeqLoadInfo *seq_load)
{
	Main *bmain = CTX_data_main(C);
	Scene *scene = CTX_data_scene(C); /* only for sound */
	Editing *ed = BKE_sequencer_editing_get(scene, TRUE);
	bSound *sound;

	Sequence *seq;  /* generic strip vars */
	Strip *strip;
	StripElem *se;

	AUD_SoundInfo info;

	sound = sound_new_file(bmain, seq_load->path); /* handles relative paths */

	if (sound == NULL || sound->playback_handle == NULL) {
#if 0
		 if (op)
			BKE_report(op->reports, RPT_ERROR, "Unsupported audio format");
#endif

		return NULL;
	}

	info = AUD_getInfo(sound->playback_handle);

	if (info.specs.channels == AUD_CHANNELS_INVALID) {
		sound_delete(bmain, sound);
#if 0
		if (op)
			BKE_report(op->reports, RPT_ERROR, "Unsupported audio format");
#endif
		return NULL;
	}

	seq = BKE_sequence_alloc(seqbasep, seq_load->start_frame, seq_load->channel);

	seq->type = SEQ_TYPE_SOUND_RAM;
	seq->sound = sound;
	BLI_strncpy(seq->name + 2, "Sound", SEQ_NAME_MAXSTR - 2);
	BKE_sequence_base_unique_name_recursive(&scene->ed->seqbase, seq);

	/* basic defaults */
	seq->strip = strip = MEM_callocN(sizeof(Strip), "strip");
	seq->len = ceil(info.length * FPS);
	strip->us = 1;

	/* we only need 1 element to store the filename */
	strip->stripdata = se = MEM_callocN(sizeof(StripElem), "stripelem");

	BLI_split_dirfile(seq_load->path, strip->dir, se->name, sizeof(strip->dir), sizeof(se->name));

	seq->scene_sound = sound_add_scene_sound(scene, seq, seq_load->start_frame, seq_load->start_frame + seq->len, 0);

	BKE_sequence_calc_disp(scene, seq);

	/* last active name */
	BLI_strncpy(ed->act_sounddir, strip->dir, FILE_MAXDIR);

	seq_load_apply(scene, seq, seq_load);

	return seq;
}
#else // WITH_AUDASPACE
Sequence *BKE_sequencer_add_sound_strip(bContext *C, ListBase *seqbasep, SeqLoadInfo *seq_load)
{
	(void) C;
	(void) seqbasep;
	(void) seq_load;
	return NULL;
}
#endif // WITH_AUDASPACE

Sequence *BKE_sequencer_add_movie_strip(bContext *C, ListBase *seqbasep, SeqLoadInfo *seq_load)
{
	Scene *scene = CTX_data_scene(C); /* only for sound */
	char path[sizeof(seq_load->path)];

	Sequence *seq;  /* generic strip vars */
	Strip *strip;
	StripElem *se;

	struct anim *an;

	BLI_strncpy(path, seq_load->path, sizeof(path));
	BLI_path_abs(path, G.main->name);

	/* OCIO_TODO: support configurable input space for strips */
	an = openanim(path, IB_rect, 0, NULL);

	if (an == NULL)
		return NULL;

	seq = BKE_sequence_alloc(seqbasep, seq_load->start_frame, seq_load->channel);
	seq->type = SEQ_TYPE_MOVIE;
	seq->blend_mode = SEQ_TYPE_CROSS; /* so alpha adjustment fade to the strip below */

	seq->anim = an;
	seq->anim_preseek = IMB_anim_get_preseek(an);
	BLI_strncpy(seq->name + 2, "Movie", SEQ_NAME_MAXSTR - 2);
	BKE_sequence_base_unique_name_recursive(&scene->ed->seqbase, seq);

	/* basic defaults */
	seq->strip = strip = MEM_callocN(sizeof(Strip), "strip");
	seq->len = IMB_anim_get_duration(an, IMB_TC_RECORD_RUN);
	strip->us = 1;

	/* we only need 1 element for MOVIE strips */
	strip->stripdata = se = MEM_callocN(sizeof(StripElem), "stripelem");

	BLI_split_dirfile(seq_load->path, strip->dir, se->name, sizeof(strip->dir), sizeof(se->name));

	BKE_sequence_calc_disp(scene, seq);


	if (seq_load->flag & SEQ_LOAD_MOVIE_SOUND) {
		int start_frame_back = seq_load->start_frame;
		seq_load->channel++;

		BKE_sequencer_add_sound_strip(C, seqbasep, seq_load);

		seq_load->start_frame = start_frame_back;
		seq_load->channel--;
	}

	if (seq_load->name[0] == '\0')
		BLI_strncpy(seq_load->name, se->name, sizeof(seq_load->name));

	/* can be NULL */
	seq_load_apply(scene, seq, seq_load);

	return seq;
}

static Sequence *seq_dupli(Scene *scene, Scene *scene_to, Sequence *seq, int dupe_flag)
{
	Scene *sce_audio = scene_to ? scene_to : scene;
	Sequence *seqn = MEM_dupallocN(seq);

	seq->tmp = seqn;
	seqn->strip = MEM_dupallocN(seq->strip);

	/* XXX: add F-Curve duplication stuff? */

	if (seq->strip->crop) {
		seqn->strip->crop = MEM_dupallocN(seq->strip->crop);
	}

	if (seq->strip->transform) {
		seqn->strip->transform = MEM_dupallocN(seq->strip->transform);
	}

	if (seq->strip->proxy) {
		seqn->strip->proxy = MEM_dupallocN(seq->strip->proxy);
		seqn->strip->proxy->anim = NULL;
	}

	if (seqn->modifiers.first) {
		seqn->modifiers.first = seqn->modifiers.last = NULL;

		BKE_sequence_modifier_list_copy(seqn, seq);
	}

	if (seq->type == SEQ_TYPE_META) {
		seqn->strip->stripdata = NULL;

		seqn->seqbase.first = seqn->seqbase.last = NULL;
		/* WATCH OUT!!! - This metastrip is not recursively duplicated here - do this after!!! */
		/* - seq_dupli_recursive(&seq->seqbase,&seqn->seqbase);*/
	}
	else if (seq->type == SEQ_TYPE_SCENE) {
		seqn->strip->stripdata = NULL;
		if (seq->scene_sound)
			seqn->scene_sound = sound_scene_add_scene_sound_defaults(sce_audio, seqn);
	}
	else if (seq->type == SEQ_TYPE_MOVIE) {
		seqn->strip->stripdata =
		        MEM_dupallocN(seq->strip->stripdata);
		seqn->anim = NULL;
	}
	else if (seq->type == SEQ_TYPE_SOUND_RAM) {
		seqn->strip->stripdata =
		        MEM_dupallocN(seq->strip->stripdata);
		if (seq->scene_sound)
			seqn->scene_sound = sound_add_scene_sound_defaults(sce_audio, seqn);

		seqn->sound->id.us++;
	}
	else if (seq->type == SEQ_TYPE_IMAGE) {
		seqn->strip->stripdata =
		        MEM_dupallocN(seq->strip->stripdata);
	}
	else if (seq->type >= SEQ_TYPE_EFFECT) {
		if (seq->seq1 && seq->seq1->tmp) seqn->seq1 = seq->seq1->tmp;
		if (seq->seq2 && seq->seq2->tmp) seqn->seq2 = seq->seq2->tmp;
		if (seq->seq3 && seq->seq3->tmp) seqn->seq3 = seq->seq3->tmp;

		if (seq->type & SEQ_TYPE_EFFECT) {
			struct SeqEffectHandle sh;
			sh = BKE_sequence_get_effect(seq);
			if (sh.copy)
				sh.copy(seq, seqn);
		}

		seqn->strip->stripdata = NULL;

	}
	else {
		fprintf(stderr, "Aiiiiekkk! sequence type not handled in duplicate!\nExpect a crash now...\n");
	}

	if (dupe_flag & SEQ_DUPE_UNIQUE_NAME)
		BKE_sequence_base_unique_name_recursive(&scene->ed->seqbase, seqn);

	if (dupe_flag & SEQ_DUPE_ANIM)
		BKE_sequencer_dupe_animdata(scene, seq->name + 2, seqn->name + 2);

	return seqn;
}

Sequence *BKE_sequence_dupli_recursive(Scene *scene, Scene *scene_to, Sequence *seq, int dupe_flag)
{
	Sequence *seqn = seq_dupli(scene, scene_to, seq, dupe_flag);
	if (seq->type == SEQ_TYPE_META) {
		Sequence *s;
		for (s = seq->seqbase.first; s; s = s->next) {
			Sequence *n = BKE_sequence_dupli_recursive(scene, scene_to, s, dupe_flag);
			if (n) {
				BLI_addtail(&seqn->seqbase, n);
			}
		}
	}
	return seqn;
}

void BKE_sequence_base_dupli_recursive(Scene *scene, Scene *scene_to, ListBase *nseqbase, ListBase *seqbase, int dupe_flag)
{
	Sequence *seq;
	Sequence *seqn = NULL;
	Sequence *last_seq = BKE_sequencer_active_get(scene);

	for (seq = seqbase->first; seq; seq = seq->next) {
		seq->tmp = NULL;
		if ((seq->flag & SELECT) || (dupe_flag & SEQ_DUPE_ALL)) {
			seqn = seq_dupli(scene, scene_to, seq, dupe_flag);
			if (seqn) { /*should never fail */
				if (dupe_flag & SEQ_DUPE_CONTEXT) {
					seq->flag &= ~SEQ_ALLSEL;
					seqn->flag &= ~(SEQ_LEFTSEL + SEQ_RIGHTSEL + SEQ_LOCK);
				}

				BLI_addtail(nseqbase, seqn);
				if (seq->type == SEQ_TYPE_META)
					BKE_sequence_base_dupli_recursive(scene, scene_to, &seqn->seqbase, &seq->seqbase, dupe_flag);

				if (dupe_flag & SEQ_DUPE_CONTEXT) {
					if (seq == last_seq) {
						BKE_sequencer_active_set(scene, seqn);
					}
				}
			}
		}
	}
}

/* called on draw, needs to be fast,
 * we could cache and use a flag if we want to make checks for file paths resolving for eg. */
int BKE_sequence_is_valid_check(Sequence *seq)
{
	switch (seq->type) {
		case SEQ_TYPE_MASK:
			return (seq->mask != NULL);
		case SEQ_TYPE_MOVIECLIP:
			return (seq->clip != NULL);
		case SEQ_TYPE_SCENE:
			return (seq->scene != NULL);
		case SEQ_TYPE_SOUND_RAM:
			return (seq->sound != NULL);
	}

	return TRUE;
}

