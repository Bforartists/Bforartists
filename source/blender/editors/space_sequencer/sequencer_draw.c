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
 * Contributor(s): Blender Foundation, 2003-2009
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_sequencer/sequencer_draw.c
 *  \ingroup spseq
 */


#include <string.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BLI_utildefines.h"

#include "IMB_imbuf_types.h"

#include "DNA_scene_types.h"
#include "DNA_mask_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_userdef_types.h"
#include "DNA_sound_types.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_sequencer.h"

#include "BKE_sound.h"

#include "IMB_colormanagement.h"
#include "IMB_imbuf.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "ED_anim_api.h"
#include "ED_gpencil.h"
#include "ED_markers.h"
#include "ED_mask.h"
#include "ED_sequencer.h"
#include "ED_types.h"
#include "ED_space_api.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "WM_api.h"
#include "WM_types.h"

/* own include */
#include "sequencer_intern.h"


#define SEQ_LEFTHANDLE   1
#define SEQ_RIGHTHANDLE  2

#define SEQ_HANDLE_SIZE_MIN  7.0f
#define SEQ_HANDLE_SIZE_MAX 40.0f


/* Note, Don't use SEQ_BEGIN/SEQ_END while drawing!
 * it messes up transform, - Campbell */
static void draw_shadedstrip(Sequence *seq, unsigned char col[3], float x1, float y1, float x2, float y2);

static void get_seq_color3ubv(Scene *curscene, Sequence *seq, unsigned char col[3])
{
	unsigned char blendcol[3];
	SolidColorVars *colvars = (SolidColorVars *)seq->effectdata;

	switch (seq->type) {
		case SEQ_TYPE_IMAGE:
			UI_GetThemeColor3ubv(TH_SEQ_IMAGE, col);
			break;

		case SEQ_TYPE_META:
			UI_GetThemeColor3ubv(TH_SEQ_META, col);
			break;

		case SEQ_TYPE_MOVIE:
			UI_GetThemeColor3ubv(TH_SEQ_MOVIE, col);
			break;

		case SEQ_TYPE_MOVIECLIP:
			UI_GetThemeColor3ubv(TH_SEQ_MOVIECLIP, col);
			break;

		case SEQ_TYPE_MASK:
			UI_GetThemeColor3ubv(TH_SEQ_MASK, col); /* TODO */
			break;

		case SEQ_TYPE_SCENE:
			UI_GetThemeColor3ubv(TH_SEQ_SCENE, col);
		
			if (seq->scene == curscene) {
				UI_GetColorPtrShade3ubv(col, col, 20);
			}
			break;
		
		/* transitions */
		case SEQ_TYPE_CROSS:
		case SEQ_TYPE_GAMCROSS:
		case SEQ_TYPE_WIPE:
			UI_GetThemeColor3ubv(TH_SEQ_TRANSITION, col);

			/* slightly offset hue to distinguish different effects */
			if (seq->type == SEQ_TYPE_CROSS)    rgb_byte_set_hue_float_offset(col, 0.04);
			if (seq->type == SEQ_TYPE_GAMCROSS) rgb_byte_set_hue_float_offset(col, 0.08);
			if (seq->type == SEQ_TYPE_WIPE)     rgb_byte_set_hue_float_offset(col, 0.12);
			break;

		/* effects */
		case SEQ_TYPE_TRANSFORM:
		case SEQ_TYPE_SPEED:
		case SEQ_TYPE_ADD:
		case SEQ_TYPE_SUB:
		case SEQ_TYPE_MUL:
		case SEQ_TYPE_ALPHAOVER:
		case SEQ_TYPE_ALPHAUNDER:
		case SEQ_TYPE_OVERDROP:
		case SEQ_TYPE_GLOW:
		case SEQ_TYPE_MULTICAM:
		case SEQ_TYPE_ADJUSTMENT:
			UI_GetThemeColor3ubv(TH_SEQ_EFFECT, col);

			/* slightly offset hue to distinguish different effects */
			if      (seq->type == SEQ_TYPE_ADD)        rgb_byte_set_hue_float_offset(col, 0.04);
			else if (seq->type == SEQ_TYPE_SUB)        rgb_byte_set_hue_float_offset(col, 0.08);
			else if (seq->type == SEQ_TYPE_MUL)        rgb_byte_set_hue_float_offset(col, 0.12);
			else if (seq->type == SEQ_TYPE_ALPHAOVER)  rgb_byte_set_hue_float_offset(col, 0.16);
			else if (seq->type == SEQ_TYPE_ALPHAUNDER) rgb_byte_set_hue_float_offset(col, 0.20);
			else if (seq->type == SEQ_TYPE_OVERDROP)   rgb_byte_set_hue_float_offset(col, 0.24);
			else if (seq->type == SEQ_TYPE_GLOW)       rgb_byte_set_hue_float_offset(col, 0.28);
			else if (seq->type == SEQ_TYPE_TRANSFORM)  rgb_byte_set_hue_float_offset(col, 0.36);
			else if (seq->type == SEQ_TYPE_MULTICAM)   rgb_byte_set_hue_float_offset(col, 0.32);
			else if (seq->type == SEQ_TYPE_ADJUSTMENT) rgb_byte_set_hue_float_offset(col, 0.40);
			break;

		case SEQ_TYPE_COLOR:
			if (colvars->col) {
				rgb_float_to_uchar(col, colvars->col);
			}
			else {
				col[0] = col[1] = col[2] = 128;
			}
			break;

		case SEQ_TYPE_SOUND_RAM:
			UI_GetThemeColor3ubv(TH_SEQ_AUDIO, col);
			blendcol[0] = blendcol[1] = blendcol[2] = 128;
			if (seq->flag & SEQ_MUTE) UI_GetColorPtrBlendShade3ubv(col, blendcol, col, 0.5, 20);
			break;
		
		default:
			col[0] = 10; col[1] = 255; col[2] = 40;
	}
}

static void drawseqwave(Scene *scene, Sequence *seq, float x1, float y1, float x2, float y2, float stepsize)
{
	/*
	 * x1 is the starting x value to draw the wave,
	 * x2 the end x value, same for y1 and y2
	 * stepsize is width of a pixel.
	 */
	if (seq->flag & SEQ_AUDIO_DRAW_WAVEFORM) {
		int i, j, pos;
		int length = floor((x2 - x1) / stepsize) + 1;
		float ymid = (y1 + y2) / 2;
		float yscale = (y2 - y1) / 2;
		float samplestep;
		float startsample, endsample;
		float value;

		SoundWaveform *waveform;

		if (!seq->sound->waveform)
			sound_read_waveform(seq->sound);

		if (!seq->sound->waveform)
			return;  /* zero length sound */

		waveform = seq->sound->waveform;

		if (!waveform)
			return;

		startsample = floor((seq->startofs + seq->anim_startofs) / FPS * SOUND_WAVE_SAMPLES_PER_SECOND);
		endsample = ceil((seq->startofs + seq->anim_startofs + seq->enddisp - seq->startdisp) / FPS * SOUND_WAVE_SAMPLES_PER_SECOND);
		samplestep = (endsample - startsample) * stepsize / (x2 - x1);

		if (length > floor((waveform->length - startsample) / samplestep))
			length = floor((waveform->length - startsample) / samplestep);

		glBegin(GL_LINE_STRIP);
		for (i = 0; i < length; i++) {
			pos = startsample + i * samplestep;

			value = waveform->data[pos * 3];

			for (j = pos + 1; (j < waveform->length) && (j < pos + samplestep); j++) {
				if (value > waveform->data[j * 3])
					value = waveform->data[j * 3];
			}

			glVertex2f(x1 + i * stepsize, ymid + value * yscale);
		}
		glEnd();

		glBegin(GL_LINE_STRIP);
		for (i = 0; i < length; i++) {
			pos = startsample + i * samplestep;

			value = waveform->data[pos * 3 + 1];

			for (j = pos + 1; (j < waveform->length) && (j < pos + samplestep); j++) {
				if (value < waveform->data[j * 3 + 1])
					value = waveform->data[j * 3 + 1];
			}

			glVertex2f(x1 + i * stepsize, ymid + value * yscale);
		}
		glEnd();
	}
}

static void drawmeta_stipple(int value)
{
	if (value) {
		glEnable(GL_POLYGON_STIPPLE);
		glPolygonStipple(stipple_halftone);
		
		glEnable(GL_LINE_STIPPLE);
		glLineStipple(1, 0x8888);
	}
	else {
		glDisable(GL_POLYGON_STIPPLE);
		glDisable(GL_LINE_STIPPLE);
	}
}

static void drawmeta_contents(Scene *scene, Sequence *seqm, float x1, float y1, float x2, float y2)
{
	/* note: this used to use SEQ_BEGIN/SEQ_END, but it messes up the
	 * seq->depth value, (needed by transform when doing overlap checks)
	 * so for now, just use the meta's immediate children, could be fixed but
	 * its only drawing - campbell */
	Sequence *seq;
	unsigned char col[4];

	int chan_min = MAXSEQ;
	int chan_max = 0;
	int chan_range = 0;
	float draw_range = y2 - y1;
	float draw_height;

	glEnable(GL_BLEND);
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

	if (seqm->flag & SEQ_MUTE)
		drawmeta_stipple(1);

	for (seq = seqm->seqbase.first; seq; seq = seq->next) {
		chan_min = min_ii(chan_min, seq->machine);
		chan_max = max_ii(chan_max, seq->machine);
	}

	chan_range = (chan_max - chan_min) + 1;
	draw_height = draw_range / chan_range;

	col[3] = 196; /* alpha, used for all meta children */

	for (seq = seqm->seqbase.first; seq; seq = seq->next) {
		if ((seq->startdisp > x2 || seq->enddisp < x1) == 0) {
			float y_chan = (seq->machine - chan_min) / (float)(chan_range) * draw_range;
			float x1_chan = seq->startdisp;
			float x2_chan = seq->enddisp;
			float y1_chan, y2_chan;

			if ((seqm->flag & SEQ_MUTE) == 0 && (seq->flag & SEQ_MUTE))
				drawmeta_stipple(1);

			get_seq_color3ubv(scene, seq, col);

			glColor4ubv(col);
			
			/* clamp within parent sequence strip bounds */
			if (x1_chan < x1) x1_chan = x1;
			if (x2_chan > x2) x2_chan = x2;

			y1_chan = y1 + y_chan + (draw_height * SEQ_STRIP_OFSBOTTOM);
			y2_chan = y1 + y_chan + (draw_height * SEQ_STRIP_OFSTOP);

			glRectf(x1_chan,  y1_chan, x2_chan,  y2_chan);

			UI_GetColorPtrShade3ubv(col, col, -30);
			glColor4ubv(col);
			fdrawbox(x1_chan,  y1_chan, x2_chan,  y2_chan);

			if ((seqm->flag & SEQ_MUTE) == 0 && (seq->flag & SEQ_MUTE))
				drawmeta_stipple(0);
		}
	}

	if (seqm->flag & SEQ_MUTE)
		drawmeta_stipple(0);
	
	glDisable(GL_BLEND);
}

/* clamp handles to defined size in pixel space */
static float draw_seq_handle_size_get_clamped(Sequence *seq, const float pixelx)
{
	const float minhandle = pixelx * SEQ_HANDLE_SIZE_MIN;
	const float maxhandle = pixelx * SEQ_HANDLE_SIZE_MAX;
	return CLAMPIS(seq->handsize, minhandle, maxhandle);
}

/* draw a handle, for each end of a sequence strip */
static void draw_seq_handle(View2D *v2d, Sequence *seq, const float handsize_clamped, const short direction)
{
	float v1[2], v2[2], v3[2], rx1 = 0, rx2 = 0; //for triangles and rect
	float x1, x2, y1, y2;
	char numstr[32];
	unsigned int whichsel = 0;
	
	x1 = seq->startdisp;
	x2 = seq->enddisp;
	
	y1 = seq->machine + SEQ_STRIP_OFSBOTTOM;
	y2 = seq->machine + SEQ_STRIP_OFSTOP;

	/* set up co-ordinates/dimensions for either left or right handle */
	if (direction == SEQ_LEFTHANDLE) {
		rx1 = x1;
		rx2 = x1 + handsize_clamped * 0.75f;
		
		v1[0] = x1 + handsize_clamped / 4; v1[1] = y1 + ( ((y1 + y2) / 2.0f - y1) / 2);
		v2[0] = x1 + handsize_clamped / 4; v2[1] = y2 - ( ((y1 + y2) / 2.0f - y1) / 2);
		v3[0] = v2[0] + handsize_clamped / 4; v3[1] = (y1 + y2) / 2.0f;
		
		whichsel = SEQ_LEFTSEL;
	}
	else if (direction == SEQ_RIGHTHANDLE) {
		rx1 = x2 - handsize_clamped * 0.75f;
		rx2 = x2;
		
		v1[0] = x2 - handsize_clamped / 4; v1[1] = y1 + ( ((y1 + y2) / 2.0f - y1) / 2);
		v2[0] = x2 - handsize_clamped / 4; v2[1] = y2 - ( ((y1 + y2) / 2.0f - y1) / 2);
		v3[0] = v2[0] - handsize_clamped / 4; v3[1] = (y1 + y2) / 2.0f;
		
		whichsel = SEQ_RIGHTSEL;
	}
	
	/* draw! */
	if (seq->type < SEQ_TYPE_EFFECT || 
	    BKE_sequence_effect_get_num_inputs(seq->type) == 0)
	{
		glEnable(GL_BLEND);
		
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
		
		if (seq->flag & whichsel) glColor4ub(0, 0, 0, 80);
		else if (seq->flag & SELECT) glColor4ub(255, 255, 255, 30);
		else glColor4ub(0, 0, 0, 22);
		
		glRectf(rx1, y1, rx2, y2);
		
		if (seq->flag & whichsel) glColor4ub(255, 255, 255, 200);
		else glColor4ub(0, 0, 0, 50);
		
		glEnable(GL_POLYGON_SMOOTH);
		glBegin(GL_TRIANGLES);
		glVertex2fv(v1); glVertex2fv(v2); glVertex2fv(v3);
		glEnd();
		
		glDisable(GL_POLYGON_SMOOTH);
		glDisable(GL_BLEND);
	}
	
	if (G.moving || (seq->flag & whichsel)) {
		const char col[4] = {255, 255, 255, 255};
		if (direction == SEQ_LEFTHANDLE) {
			BLI_snprintf(numstr, sizeof(numstr), "%d", seq->startdisp);
			x1 = rx1;
			y1 -= 0.45f;
		}
		else {
			BLI_snprintf(numstr, sizeof(numstr), "%d", seq->enddisp - 1);
			x1 = x2 - handsize_clamped * 0.75f;
			y1 = y2 + 0.05f;
		}
		UI_view2d_text_cache_add(v2d, x1, y1, numstr, col);
	}
}

static void draw_seq_extensions(Scene *scene, ARegion *ar, Sequence *seq)
{
	float x1, x2, y1, y2, pixely, a;
	unsigned char col[3], blendcol[3];
	View2D *v2d = &ar->v2d;
	
	if (seq->type >= SEQ_TYPE_EFFECT) return;

	x1 = seq->startdisp;
	x2 = seq->enddisp;
	
	y1 = seq->machine + SEQ_STRIP_OFSBOTTOM;
	y2 = seq->machine + SEQ_STRIP_OFSTOP;

	pixely = BLI_rctf_size_y(&v2d->cur) / BLI_rcti_size_y(&v2d->mask);
	
	if (pixely <= 0) return;  /* can happen when the view is split/resized */
	
	blendcol[0] = blendcol[1] = blendcol[2] = 120;

	if (seq->startofs) {
		glEnable(GL_BLEND);
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
		
		get_seq_color3ubv(scene, seq, col);
		
		if (seq->flag & SELECT) {
			UI_GetColorPtrBlendShade3ubv(col, blendcol, col, 0.3, -40);
			glColor4ub(col[0], col[1], col[2], 170);
		}
		else {
			UI_GetColorPtrBlendShade3ubv(col, blendcol, col, 0.6, 0);
			glColor4ub(col[0], col[1], col[2], 110);
		}
		
		glRectf((float)(seq->start), y1 - SEQ_STRIP_OFSBOTTOM, x1, y1);
		
		if (seq->flag & SELECT) glColor4ub(col[0], col[1], col[2], 255);
		else glColor4ub(col[0], col[1], col[2], 160);

		fdrawbox((float)(seq->start), y1 - SEQ_STRIP_OFSBOTTOM, x1, y1);  //outline
		
		glDisable(GL_BLEND);
	}
	if (seq->endofs) {
		glEnable(GL_BLEND);
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
		
		get_seq_color3ubv(scene, seq, col);
		
		if (seq->flag & SELECT) {
			UI_GetColorPtrBlendShade3ubv(col, blendcol, col, 0.3, -40);
			glColor4ub(col[0], col[1], col[2], 170);
		}
		else {
			UI_GetColorPtrBlendShade3ubv(col, blendcol, col, 0.6, 0);
			glColor4ub(col[0], col[1], col[2], 110);
		}
		
		glRectf(x2, y2, (float)(seq->start + seq->len), y2 + SEQ_STRIP_OFSBOTTOM);
		
		if (seq->flag & SELECT) glColor4ub(col[0], col[1], col[2], 255);
		else glColor4ub(col[0], col[1], col[2], 160);

		fdrawbox(x2, y2, (float)(seq->start + seq->len), y2 + SEQ_STRIP_OFSBOTTOM); //outline
		
		glDisable(GL_BLEND);
	}
	if (seq->startstill) {
		get_seq_color3ubv(scene, seq, col);
		UI_GetColorPtrBlendShade3ubv(col, blendcol, col, 0.75, 40);
		glColor3ubv((GLubyte *)col);
		
		draw_shadedstrip(seq, col, x1, y1, (float)(seq->start), y2);
		
		/* feint pinstripes, helps see exactly which is extended and which isn't,
		 * especially when the extension is very small */ 
		if (seq->flag & SELECT) UI_GetColorPtrBlendShade3ubv(col, col, col, 0.0, 24);
		else UI_GetColorPtrShade3ubv(col, col, -16);
		
		glColor3ubv((GLubyte *)col);
		
		for (a = y1; a < y2; a += pixely * 2.0f) {
			fdrawline(x1,  a,  (float)(seq->start),  a);
		}
	}
	if (seq->endstill) {
		get_seq_color3ubv(scene, seq, col);
		UI_GetColorPtrBlendShade3ubv(col, blendcol, col, 0.75, 40);
		glColor3ubv((GLubyte *)col);
		
		draw_shadedstrip(seq, col, (float)(seq->start + seq->len), y1, x2, y2);
		
		/* feint pinstripes, helps see exactly which is extended and which isn't,
		 * especially when the extension is very small */ 
		if (seq->flag & SELECT) UI_GetColorPtrShade3ubv(col, col, 24);
		else UI_GetColorPtrShade3ubv(col, col, -16);
		
		glColor3ubv((GLubyte *)col);
		
		for (a = y1; a < y2; a += pixely * 2.0f) {
			fdrawline((float)(seq->start + seq->len),  a,  x2,  a);
		}
	}
}

/* draw info text on a sequence strip */
static void draw_seq_text(View2D *v2d, Sequence *seq, float x1, float x2, float y1, float y2, const unsigned char background_col[3])
{
	rctf rect;
	char str[32 + FILE_MAX];
	const char *name = seq->name + 2;
	char col[4];

	/* note, all strings should include 'name' */
	if (name[0] == '\0')
		name = BKE_sequence_give_name(seq);

	if (seq->type == SEQ_TYPE_META || seq->type == SEQ_TYPE_ADJUSTMENT) {
		BLI_snprintf(str, sizeof(str), "%s | %d", name, seq->len);
	}
	else if (seq->type == SEQ_TYPE_SCENE) {
		if (seq->scene) {
			if (seq->scene_camera) {
				BLI_snprintf(str, sizeof(str), "%s: %s (%s) | %d",
				             name, seq->scene->id.name + 2, ((ID *)seq->scene_camera)->name + 2, seq->len);
			}
			else {
				BLI_snprintf(str, sizeof(str), "%s: %s | %d",
				             name, seq->scene->id.name + 2, seq->len);
			}
		}
		else {
			BLI_snprintf(str, sizeof(str), "%s | %d",
			             name, seq->len);
		}
	}
	else if (seq->type == SEQ_TYPE_MOVIECLIP) {
		if (seq->clip && strcmp(name, seq->clip->id.name + 2) != 0) {
			BLI_snprintf(str, sizeof(str), "%s: %s | %d",
			             name, seq->clip->id.name + 2, seq->len);
		}
		else {
			BLI_snprintf(str, sizeof(str), "%s | %d",
			             name, seq->len);
		}
	}
	else if (seq->type == SEQ_TYPE_MASK) {
		if (seq->mask && strcmp(name, seq->mask->id.name + 2) != 0) {
			BLI_snprintf(str, sizeof(str), "%s: %s | %d",
			             name, seq->mask->id.name + 2, seq->len);
		}
		else {
			BLI_snprintf(str, sizeof(str), "%s | %d",
			             name, seq->len);
		}
	}
	else if (seq->type == SEQ_TYPE_MULTICAM) {
		BLI_snprintf(str, sizeof(str), "Cam %s: %d",
		             name, seq->multicam_source);
	}
	else if (seq->type == SEQ_TYPE_IMAGE) {
		BLI_snprintf(str, sizeof(str), "%s: %s%s | %d",
		             name, seq->strip->dir, seq->strip->stripdata->name, seq->len);
	}
	else if (seq->type & SEQ_TYPE_EFFECT) {
		BLI_snprintf(str, sizeof(str), "%s | %d",
			             name, seq->len);
	}
	else if (seq->type == SEQ_TYPE_SOUND_RAM) {
		if (seq->sound)
			BLI_snprintf(str, sizeof(str), "%s: %s | %d",
			             name, seq->sound->name, seq->len);
		else
			BLI_snprintf(str, sizeof(str), "%s | %d",
			             name, seq->len);
	}
	else if (seq->type == SEQ_TYPE_MOVIE) {
		BLI_snprintf(str, sizeof(str), "%s: %s%s | %d",
		             name, seq->strip->dir, seq->strip->stripdata->name, seq->len);
	}
	
	if (seq->flag & SELECT) {
		col[0] = col[1] = col[2] = 255;
	}
	else if ((((int)background_col[0] + (int)background_col[1] + (int)background_col[2]) / 3) < 50) {
		col[0] = col[1] = col[2] = 80; /* use lighter text color for dark background */
	}
	else {
		col[0] = col[1] = col[2] = 0;
	}
	col[3] = 255;

	rect.xmin = x1;
	rect.ymin = y1;
	rect.xmax = x2;
	rect.ymax = y2;
	UI_view2d_text_cache_rectf(v2d, &rect, str, col);
}

/* draws a shaded strip, made from gradient + flat color + gradient */
static void draw_shadedstrip(Sequence *seq, unsigned char col[3], float x1, float y1, float x2, float y2)
{
	float ymid1, ymid2;
	
	if (seq->flag & SEQ_MUTE) {
		glEnable(GL_POLYGON_STIPPLE);
		glPolygonStipple(stipple_halftone);
	}
	
	ymid1 = (y2 - y1) * 0.25f + y1;
	ymid2 = (y2 - y1) * 0.65f + y1;
	
	glShadeModel(GL_SMOOTH);
	glBegin(GL_QUADS);
	
	if (seq->flag & SEQ_INVALID_EFFECT) { col[0] = 255; col[1] = 0; col[2] = 255; }
	else if (seq->flag & SELECT) UI_GetColorPtrShade3ubv(col, col, -50);
	/* else UI_GetColorPtrShade3ubv(col, col, 0); */ /* DO NOTHING */
	
	glColor3ubv(col);
	
	glVertex2f(x1, y1);
	glVertex2f(x2, y1);

	if (seq->flag & SEQ_INVALID_EFFECT) { col[0] = 255; col[1] = 0; col[2] = 255; }
	else if (seq->flag & SELECT) UI_GetColorPtrBlendShade3ubv(col, col, col, 0.0, 5);
	else UI_GetColorPtrShade3ubv(col, col, -5);

	glColor3ubv((GLubyte *)col);
	
	glVertex2f(x2, ymid1);
	glVertex2f(x1, ymid1);
	
	glEnd();
	
	glRectf(x1,  ymid1,  x2,  ymid2);
	
	glBegin(GL_QUADS);
	
	glVertex2f(x1, ymid2);
	glVertex2f(x2, ymid2);
	
	if (seq->flag & SELECT) UI_GetColorPtrShade3ubv(col, col, -15);
	else UI_GetColorPtrShade3ubv(col, col, 25);
	
	glColor3ubv((GLubyte *)col);
	
	glVertex2f(x2, y2);
	glVertex2f(x1, y2);
	
	glEnd();
	
	if (seq->flag & SEQ_MUTE) {
		glDisable(GL_POLYGON_STIPPLE);
	}
}

/*
 * Draw a sequence strip, bounds check already made
 * ARegion is currently only used to get the windows width in pixels
 * so wave file sample drawing precision is zoom adjusted
 */
static void draw_seq_strip(Scene *scene, ARegion *ar, Sequence *seq, int outline_tint, float pixelx)
{
	View2D *v2d = &ar->v2d;
	float x1, x2, y1, y2;
	unsigned char col[3], background_col[3], is_single_image;
	const float handsize_clamped = draw_seq_handle_size_get_clamped(seq, pixelx);

	/* we need to know if this is a single image/color or not for drawing */
	is_single_image = (char)BKE_sequence_single_check(seq);
	
	/* body */
	x1 = (seq->startstill) ? seq->start : seq->startdisp;
	y1 = seq->machine + SEQ_STRIP_OFSBOTTOM;
	x2 = (seq->endstill) ? (seq->start + seq->len) : seq->enddisp;
	y2 = seq->machine + SEQ_STRIP_OFSTOP;


	/* get the correct color per strip type*/
	//get_seq_color3ubv(scene, seq, col);
	get_seq_color3ubv(scene, seq, background_col);
	
	/* draw the main strip body */
	if (is_single_image) {  /* single image */
		draw_shadedstrip(seq, background_col,
		                 BKE_sequence_tx_get_final_left(seq, 0), y1,
		                 BKE_sequence_tx_get_final_right(seq, 0), y2);
	}
	else {  /* normal operation */
		draw_shadedstrip(seq, background_col, x1, y1, x2, y2);
	}
	
	/* draw additional info and controls */
	if (!is_single_image)
		draw_seq_extensions(scene, ar, seq);
	
	draw_seq_handle(v2d, seq, handsize_clamped, SEQ_LEFTHANDLE);
	draw_seq_handle(v2d, seq, handsize_clamped, SEQ_RIGHTHANDLE);
	
	/* draw the strip outline */
	x1 = seq->startdisp;
	x2 = seq->enddisp;
	
	/* draw sound wave */
	if (seq->type == SEQ_TYPE_SOUND_RAM) {
		drawseqwave(scene, seq, x1, y1, x2, y2, BLI_rctf_size_x(&ar->v2d.cur) / ar->winx);
	}

	/* draw lock */
	if (seq->flag & SEQ_LOCK) {
		glEnable(GL_POLYGON_STIPPLE);
		glEnable(GL_BLEND);

		/* light stripes */
		glColor4ub(255, 255, 255, 32);
		glPolygonStipple(stipple_diag_stripes_pos);
		glRectf(x1, y1, x2, y2);

		/* dark stripes */
		glColor4ub(0, 0, 0, 32);
		glPolygonStipple(stipple_diag_stripes_neg);
		glRectf(x1, y1, x2, y2);

		glDisable(GL_POLYGON_STIPPLE);
		glDisable(GL_BLEND);
	}

	if (!BKE_sequence_is_valid_check(seq)) {
		glEnable(GL_POLYGON_STIPPLE);

		/* panic! */
		glColor4ub(255, 0, 0, 255);
		glPolygonStipple(stipple_diag_stripes_pos);
		glRectf(x1, y1, x2, y2);

		glDisable(GL_POLYGON_STIPPLE);
	}

	get_seq_color3ubv(scene, seq, col);
	if (G.moving && (seq->flag & SELECT)) {
		if (seq->flag & SEQ_OVERLAP) {
			col[0] = 255; col[1] = col[2] = 40;
		}
		else
			UI_GetColorPtrShade3ubv(col, col, 120 + outline_tint);
	}
	else
		UI_GetColorPtrShade3ubv(col, col, outline_tint);
	
	glColor3ubv((GLubyte *)col);
	
	if (seq->flag & SEQ_MUTE) {
		glEnable(GL_LINE_STIPPLE);
		glLineStipple(1, 0x8888);
	}
	
	uiDrawBoxShade(GL_LINE_LOOP, x1, y1, x2, y2, 0.0, 0.1, 0.0);
	
	if (seq->flag & SEQ_MUTE) {
		glDisable(GL_LINE_STIPPLE);
	}
	
	if (seq->type == SEQ_TYPE_META) {
		drawmeta_contents(scene, seq, x1, y1, x2, y2);
	}
	
	/* calculate if seq is long enough to print a name */
	x1 = seq->startdisp + handsize_clamped;
	x2 = seq->enddisp   - handsize_clamped;

	/* info text on the strip */
	if (x1 < v2d->cur.xmin) x1 = v2d->cur.xmin;
	else if (x1 > v2d->cur.xmax) x1 = v2d->cur.xmax;
	if (x2 < v2d->cur.xmin) x2 = v2d->cur.xmin;
	else if (x2 > v2d->cur.xmax) x2 = v2d->cur.xmax;

	/* nice text here would require changing the view matrix for texture text */
	if ((x2 - x1) / pixelx > 32) {
		draw_seq_text(v2d, seq, x1, x2, y1, y2, background_col);
	}
}

static Sequence *special_seq_update = NULL;

static void UNUSED_FUNCTION(set_special_seq_update) (int val)
{
//	int x;

	/* if mouse over a sequence && LEFTMOUSE */
	if (val) {
// XXX		special_seq_update = find_nearest_seq(&x);
	}
	else special_seq_update = NULL;
}

ImBuf *sequencer_ibuf_get(struct Main *bmain, Scene *scene, SpaceSeq *sseq, int cfra, int frame_ofs)
{
	SeqRenderData context;
	ImBuf *ibuf;
	int rectx, recty;
	float render_size = 0.0;
	float proxy_size = 100.0;
	short is_break = G.is_break;

	render_size = sseq->render_size;
	if (render_size == 0) {
		render_size = scene->r.size;
	}
	else {
		proxy_size = render_size;
	}

	if (render_size < 0) {
		return NULL;
	}

	rectx = (render_size * (float)scene->r.xsch) / 100.0f + 0.5f;
	recty = (render_size * (float)scene->r.ysch) / 100.0f + 0.5f;

	context = BKE_sequencer_new_render_data(bmain, scene, rectx, recty, proxy_size);

	/* sequencer could start rendering, in this case we need to be sure it wouldn't be canceled
	 * by Esc pressed somewhere in the past
	 */
	G.is_break = FALSE;

	if (special_seq_update)
		ibuf = BKE_sequencer_give_ibuf_direct(context, cfra + frame_ofs, special_seq_update);
	else if (!U.prefetchframes) // XXX || (G.f & G_PLAYANIM) == 0) {
		ibuf = BKE_sequencer_give_ibuf(context, cfra + frame_ofs, sseq->chanshown);
	else
		ibuf = BKE_sequencer_give_ibuf_threaded(context, cfra + frame_ofs, sseq->chanshown);

	/* restore state so real rendering would be canceled (if needed) */
	G.is_break = is_break;

	return ibuf;
}

static void sequencer_check_scopes(SequencerScopes *scopes, ImBuf *ibuf)
{
	if (scopes->reference_ibuf != ibuf) {
		if (scopes->zebra_ibuf) {
			IMB_freeImBuf(scopes->zebra_ibuf);
			scopes->zebra_ibuf = NULL;
		}

		if (scopes->waveform_ibuf) {
			IMB_freeImBuf(scopes->waveform_ibuf);
			scopes->waveform_ibuf = NULL;
		}

		if (scopes->sep_waveform_ibuf) {
			IMB_freeImBuf(scopes->sep_waveform_ibuf);
			scopes->sep_waveform_ibuf = NULL;
		}

		if (scopes->vector_ibuf) {
			IMB_freeImBuf(scopes->vector_ibuf);
			scopes->vector_ibuf = NULL;
		}

		if (scopes->histogram_ibuf) {
			IMB_freeImBuf(scopes->histogram_ibuf);
			scopes->histogram_ibuf = NULL;
		}
	}
}

static ImBuf *sequencer_make_scope(Scene *scene, ImBuf *ibuf, ImBuf *(*make_scope_cb) (ImBuf *ibuf))
{
	ImBuf *display_ibuf = IMB_dupImBuf(ibuf);
	ImBuf *scope;

	if (display_ibuf->rect_float) {
		IMB_colormanagement_imbuf_make_display_space(display_ibuf, &scene->view_settings,
		                                             &scene->display_settings);
	}

	scope = make_scope_cb(display_ibuf);

	IMB_freeImBuf(display_ibuf);

	return scope;
}

void draw_image_seq(const bContext *C, Scene *scene, ARegion *ar, SpaceSeq *sseq, int cfra, int frame_ofs, int draw_overlay)
{
	struct Main *bmain = CTX_data_main(C);
	struct ImBuf *ibuf = NULL;
	struct ImBuf *scope = NULL;
	struct View2D *v2d = &ar->v2d;
	/* int rectx, recty; */ /* UNUSED */
	float viewrectx, viewrecty;
	float render_size = 0.0;
	float proxy_size = 100.0;
	float col[3];
	GLuint texid;
	GLuint last_texid;
	unsigned char *display_buffer;
	void *cache_handle = NULL;
	const int is_imbuf = ED_space_sequencer_check_show_imbuf(sseq);

	if (G.is_rendering == FALSE) {
		/* stop all running jobs, except screen one. currently previews frustrate Render
		 * needed to make so sequencer's rendering doesn't conflict with compositor
		 */
		WM_jobs_kill_type(CTX_wm_manager(C), WM_JOB_TYPE_COMPOSITE);

		if ((scene->r.seq_flag & R_SEQ_GL_PREV) == 0) {
			/* in case of final rendering used for preview, kill all previews,
			 * otherwise threading conflict will happen in rendering module
			 */
			WM_jobs_kill_type(CTX_wm_manager(C), WM_JOB_TYPE_RENDER_PREVIEW);
		}
	}

	render_size = sseq->render_size;
	if (render_size == 0) {
		render_size = scene->r.size;
	}
	else {
		proxy_size = render_size;
	}
	if (render_size < 0) {
		return;
	}

	viewrectx = (render_size * (float)scene->r.xsch) / 100.0f;
	viewrecty = (render_size * (float)scene->r.ysch) / 100.0f;

	/* rectx = viewrectx + 0.5f; */ /* UNUSED */
	/* recty = viewrecty + 0.5f; */ /* UNUSED */

	if (sseq->mainb == SEQ_DRAW_IMG_IMBUF) {
		viewrectx *= scene->r.xasp / scene->r.yasp;
		viewrectx /= proxy_size / 100.0f;
		viewrecty /= proxy_size / 100.0f;
	}

	if (!draw_overlay || sseq->overlay_type == SEQ_DRAW_OVERLAY_REFERENCE) {
		UI_GetThemeColor3fv(TH_SEQ_PREVIEW, col);
		glClearColor(col[0], col[1], col[2], 0.0);
		glClear(GL_COLOR_BUFFER_BIT);
	}

	/* without this colors can flicker from previous opengl state */
	glColor4ub(255, 255, 255, 255);

	UI_view2d_totRect_set(v2d, viewrectx + 0.5f, viewrecty + 0.5f);
	UI_view2d_curRect_validate(v2d);

	/* only initialize the preview if a render is in progress */
	if (G.is_rendering)
		return;

	ibuf = sequencer_ibuf_get(bmain, scene, sseq, cfra, frame_ofs);
	
	if (ibuf == NULL)
		return;

	if (ibuf->rect == NULL && ibuf->rect_float == NULL)
		return;

	if (sseq->mainb != SEQ_DRAW_IMG_IMBUF || sseq->zebra != 0) {
		SequencerScopes *scopes = &sseq->scopes;

		sequencer_check_scopes(scopes, ibuf);

		switch (sseq->mainb) {
			case SEQ_DRAW_IMG_IMBUF:
				if (!scopes->zebra_ibuf) {
					ImBuf *display_ibuf = IMB_dupImBuf(ibuf);

					if (display_ibuf->rect_float) {
						IMB_colormanagement_imbuf_make_display_space(display_ibuf, &scene->view_settings,
						                                             &scene->display_settings);
					}
					scopes->zebra_ibuf = make_zebra_view_from_ibuf(display_ibuf, sseq->zebra);
					IMB_freeImBuf(display_ibuf);
				}
				scope = scopes->zebra_ibuf;
				break;
			case SEQ_DRAW_IMG_WAVEFORM:
				if ((sseq->flag & SEQ_DRAW_COLOR_SEPARATED) != 0) {
					if (!scopes->sep_waveform_ibuf)
						scopes->sep_waveform_ibuf = sequencer_make_scope(scene, ibuf, make_sep_waveform_view_from_ibuf);
					scope = scopes->sep_waveform_ibuf;
				}
				else {
					if (!scopes->waveform_ibuf)
						scopes->waveform_ibuf = sequencer_make_scope(scene, ibuf, make_waveform_view_from_ibuf);
					scope = scopes->waveform_ibuf;
				}
				break;
			case SEQ_DRAW_IMG_VECTORSCOPE:
				if (!scopes->vector_ibuf)
					scopes->vector_ibuf = sequencer_make_scope(scene, ibuf, make_vectorscope_view_from_ibuf);
				scope = scopes->vector_ibuf;
				break;
			case SEQ_DRAW_IMG_HISTOGRAM:
				if (!scopes->histogram_ibuf)
					scopes->histogram_ibuf = sequencer_make_scope(scene, ibuf, make_histogram_view_from_ibuf);
				scope = scopes->histogram_ibuf;
				break;
		}

		scopes->reference_ibuf = ibuf;
	}

	if (scope) {
		IMB_freeImBuf(ibuf);
		ibuf = scope;

		if (ibuf->rect_float && ibuf->rect == NULL) {
			IMB_rect_from_float(ibuf);
		}

		display_buffer = (unsigned char *)ibuf->rect;
	}
	else {
		display_buffer = IMB_display_buffer_acquire_ctx(C, ibuf, &cache_handle);
	}

	/* setting up the view - actual drawing starts here */
	UI_view2d_view_ortho(v2d);

	last_texid = glaGetOneInteger(GL_TEXTURE_2D);
	glEnable(GL_TEXTURE_2D);
	glGenTextures(1, (GLuint *)&texid);

	glBindTexture(GL_TEXTURE_2D, texid);

	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);

	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, ibuf->x, ibuf->y, 0, GL_RGBA, GL_UNSIGNED_BYTE, display_buffer);

	glEnable(GL_BLEND);
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

	glBegin(GL_QUADS);

	if (draw_overlay) {
		if (sseq->overlay_type == SEQ_DRAW_OVERLAY_RECT) {
			rctf tot_clip;
			tot_clip.xmin = v2d->tot.xmin + (fabsf(BLI_rctf_size_x(&v2d->tot)) * scene->ed->over_border.xmin);
			tot_clip.ymin = v2d->tot.ymin + (fabsf(BLI_rctf_size_y(&v2d->tot)) * scene->ed->over_border.ymin);
			tot_clip.xmax = v2d->tot.xmin + (fabsf(BLI_rctf_size_x(&v2d->tot)) * scene->ed->over_border.xmax);
			tot_clip.ymax = v2d->tot.ymin + (fabsf(BLI_rctf_size_y(&v2d->tot)) * scene->ed->over_border.ymax);

			glTexCoord2f(scene->ed->over_border.xmin, scene->ed->over_border.ymin); glVertex2f(tot_clip.xmin, tot_clip.ymin);
			glTexCoord2f(scene->ed->over_border.xmin, scene->ed->over_border.ymax); glVertex2f(tot_clip.xmin, tot_clip.ymax);
			glTexCoord2f(scene->ed->over_border.xmax, scene->ed->over_border.ymax); glVertex2f(tot_clip.xmax, tot_clip.ymax);
			glTexCoord2f(scene->ed->over_border.xmax, scene->ed->over_border.ymin); glVertex2f(tot_clip.xmax, tot_clip.ymin);
		}
		else if (sseq->overlay_type == SEQ_DRAW_OVERLAY_REFERENCE) {
			glTexCoord2f(0.0f, 0.0f); glVertex2f(v2d->tot.xmin, v2d->tot.ymin);
			glTexCoord2f(0.0f, 1.0f); glVertex2f(v2d->tot.xmin, v2d->tot.ymax);
			glTexCoord2f(1.0f, 1.0f); glVertex2f(v2d->tot.xmax, v2d->tot.ymax);
			glTexCoord2f(1.0f, 0.0f); glVertex2f(v2d->tot.xmax, v2d->tot.ymin);
		}
	}
	else {
		glTexCoord2f(0.0f, 0.0f); glVertex2f(v2d->tot.xmin, v2d->tot.ymin);
		glTexCoord2f(0.0f, 1.0f); glVertex2f(v2d->tot.xmin, v2d->tot.ymax);
		glTexCoord2f(1.0f, 1.0f); glVertex2f(v2d->tot.xmax, v2d->tot.ymax);
		glTexCoord2f(1.0f, 0.0f); glVertex2f(v2d->tot.xmax, v2d->tot.ymin);
	}
	glEnd();
	glBindTexture(GL_TEXTURE_2D, last_texid);
	glDisable(GL_TEXTURE_2D);
	glDisable(GL_BLEND);
	glDeleteTextures(1, &texid);

	if (sseq->mainb == SEQ_DRAW_IMG_IMBUF) {

		float x1 = v2d->tot.xmin;
		float y1 = v2d->tot.ymin;
		float x2 = v2d->tot.xmax;
		float y2 = v2d->tot.ymax;

		/* border */
		setlinestyle(3);

		UI_ThemeColorBlendShade(TH_WIRE, TH_BACK, 1.0, 0);

		glBegin(GL_LINE_LOOP);
		glVertex2f(x1 - 0.5f, y1 - 0.5f);
		glVertex2f(x1 - 0.5f, y2 + 0.5f);
		glVertex2f(x2 + 0.5f, y2 + 0.5f);
		glVertex2f(x2 + 0.5f, y1 - 0.5f);
		glEnd();

		/* safety border */
		if ((sseq->flag & SEQ_DRAW_SAFE_MARGINS) != 0) {
			float fac = 0.1;

			float a = fac * (x2 - x1);
			x1 += a;
			x2 -= a;

			a = fac * (y2 - y1);
			y1 += a;
			y2 -= a;

			glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);

			uiSetRoundBox(UI_CNR_ALL);
			uiDrawBox(GL_LINE_LOOP, x1, y1, x2, y2, 12.0);

			glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);

		}

		setlinestyle(0);
	}
	
	if (sseq->flag & SEQ_SHOW_GPENCIL) {
		if (is_imbuf) {
			/* draw grease-pencil (image aligned) */
			draw_gpencil_2dimage(C);
		}
	}

	if (!scope)
		IMB_freeImBuf(ibuf);
	
	/* ortho at pixel level */
	UI_view2d_view_restore(C);
	
	if (sseq->flag & SEQ_SHOW_GPENCIL) {
		if (is_imbuf) {
			/* draw grease-pencil (screen aligned) */
			draw_gpencil_view2d(C, 0);
		}
	}


	/* NOTE: sequencer mask editing isnt finished, the draw code is working but editing not,
	 * for now just disable drawing since the strip frame will likely be offset */

	//if (sc->mode == SC_MODE_MASKEDIT) {
	if (0 && sseq->mainb == SEQ_DRAW_IMG_IMBUF) {
		Mask *mask = BKE_sequencer_mask_get(scene);

		if (mask) {
			int width, height;
			float aspx = 1.0f, aspy = 1.0f;
			// ED_mask_get_size(C, &width, &height);

			//Scene *scene = CTX_data_scene(C);
			width = (scene->r.size * scene->r.xsch) / 100;
			height = (scene->r.size * scene->r.ysch) / 100;

			ED_mask_draw_region(mask, ar,
			                    0, 0,  /* TODO */
			                    width, height,
			                    aspx, aspy,
			                    FALSE, TRUE,
			                    NULL, C);
		}
	}

	if (cache_handle)
		IMB_display_buffer_release(cache_handle);
}

#if 0
void drawprefetchseqspace(Scene *scene, ARegion *UNUSED(ar), SpaceSeq *sseq)
{
	int rectx, recty;
	int render_size = sseq->render_size;
	int proxy_size = 100.0; 
	if (render_size == 0) {
		render_size = scene->r.size;
	}
	else {
		proxy_size = render_size;
	}
	if (render_size < 0) {
		return;
	}

	rectx = (render_size * scene->r.xsch) / 100;
	recty = (render_size * scene->r.ysch) / 100;

	if (sseq->mainb != SEQ_DRAW_SEQUENCE) {
		give_ibuf_prefetch_request(
		    rectx, recty, (scene->r.cfra), sseq->chanshown,
		    proxy_size);
	}
}
#endif

/* draw backdrop of the sequencer strips view */
static void draw_seq_backdrop(View2D *v2d)
{
	int i;
	
	/* darker gray overlay over the view backdrop */
	UI_ThemeColorShade(TH_BACK, -20);
	glRectf(v2d->cur.xmin,  -1.0,  v2d->cur.xmax,  1.0);

	/* Alternating horizontal stripes */
	i = max_ii(1, ((int)v2d->cur.ymin) - 1);

	glBegin(GL_QUADS);
	while (i < v2d->cur.ymax) {
		if (((int)i) & 1)
			UI_ThemeColorShade(TH_BACK, -15);
		else
			UI_ThemeColorShade(TH_BACK, -25);
			
		glVertex2f(v2d->cur.xmax, i);
		glVertex2f(v2d->cur.xmin, i);
		glVertex2f(v2d->cur.xmin, i + 1);
		glVertex2f(v2d->cur.xmax, i + 1);

		i += 1.0;
	}
	glEnd();
	
	/* Darker lines separating the horizontal bands */
	i = max_ii(1, ((int)v2d->cur.ymin) - 1);
	UI_ThemeColor(TH_GRID);
	
	glBegin(GL_LINES);
	while (i < v2d->cur.ymax) {
		glVertex2f(v2d->cur.xmax, i);
		glVertex2f(v2d->cur.xmin, i);
			
		i += 1.0;
	}
	glEnd();
}

/* draw the contents of the sequencer strips view */
static void draw_seq_strips(const bContext *C, Editing *ed, ARegion *ar)
{
	Scene *scene = CTX_data_scene(C);
	View2D *v2d = &ar->v2d;
	Sequence *last_seq = BKE_sequencer_active_get(scene);
	int sel = 0, j;
	float pixelx = BLI_rctf_size_x(&v2d->cur) / BLI_rcti_size_x(&v2d->mask);
	
	/* loop through twice, first unselected, then selected */
	for (j = 0; j < 2; j++) {
		Sequence *seq;
		int outline_tint = (j) ? -60 : -150; /* highlighting around strip edges indicating selection */
		
		/* loop through strips, checking for those that are visible */
		for (seq = ed->seqbasep->first; seq; seq = seq->next) {
			/* boundbox and selection tests for NOT drawing the strip... */
			if ((seq->flag & SELECT) != sel) continue;
			else if (seq == last_seq) continue;
			else if (min_ii(seq->startdisp, seq->start) > v2d->cur.xmax) continue;
			else if (max_ii(seq->enddisp, seq->start + seq->len) < v2d->cur.xmin) continue;
			else if (seq->machine + 1.0f < v2d->cur.ymin) continue;
			else if (seq->machine > v2d->cur.ymax) continue;
			
			/* strip passed all tests unscathed... so draw it now */
			draw_seq_strip(scene, ar, seq, outline_tint, pixelx);
		}
		
		/* draw selected next time round */
		sel = SELECT;
	}
	
	/* draw the last selected last (i.e. 'active' in other parts of Blender), removes some overlapping error */
	if (last_seq)
		draw_seq_strip(scene, ar, last_seq, 120, pixelx);
}

static void seq_draw_sfra_efra(Scene *scene, View2D *v2d)
{	
	glEnable(GL_BLEND);
	
	/* draw darkened area outside of active timeline 
	 * frame range used is preview range or scene range */
	UI_ThemeColorShadeAlpha(TH_BACK, -25, -100);

	if (PSFRA < PEFRA) {
		glRectf(v2d->cur.xmin, v2d->cur.ymin, (float)PSFRA, v2d->cur.ymax);
		glRectf((float)PEFRA, v2d->cur.ymin, v2d->cur.xmax, v2d->cur.ymax);
	}
	else {
		glRectf(v2d->cur.xmin, v2d->cur.ymin, v2d->cur.xmax, v2d->cur.ymax);
	}

	UI_ThemeColorShade(TH_BACK, -60);
	/* thin lines where the actual frames are */
	fdrawline((float)PSFRA, v2d->cur.ymin, (float)PSFRA, v2d->cur.ymax);
	fdrawline((float)PEFRA, v2d->cur.ymin, (float)PEFRA, v2d->cur.ymax);
	
	glDisable(GL_BLEND);
}

/* Draw Timeline/Strip Editor Mode for Sequencer */
void draw_timeline_seq(const bContext *C, ARegion *ar)
{
	Scene *scene = CTX_data_scene(C);
	Editing *ed = BKE_sequencer_editing_get(scene, FALSE);
	SpaceSeq *sseq = CTX_wm_space_seq(C);
	View2D *v2d = &ar->v2d;
	View2DScrollers *scrollers;
	short unit = 0, flag = 0;
	float col[3];
	
	/* clear and setup matrix */
	UI_GetThemeColor3fv(TH_BACK, col);
	if (ed && ed->metastack.first) 
		glClearColor(col[0], col[1], col[2] - 0.1f, 0.0f);
	else 
		glClearColor(col[0], col[1], col[2], 0.0f);
	glClear(GL_COLOR_BUFFER_BIT);

	UI_view2d_view_ortho(v2d);
	
	
	/* calculate extents of sequencer strips/data 
	 * NOTE: needed for the scrollers later
	 */
	boundbox_seq(scene, &v2d->tot);
	
	
	/* draw backdrop */
	draw_seq_backdrop(v2d);
	
	/* regular grid-pattern over the rest of the view (i.e. 25-frame grid lines) */
	// NOTE: the gridlines are currently spaced every 25 frames, which is only fine for 25 fps, but maybe not for 30...
	UI_view2d_constant_grid_draw(v2d);
	
	seq_draw_sfra_efra(scene, v2d);

	/* sequence strips (if there is data available to be drawn) */
	if (ed) {
		/* draw the data */
		draw_seq_strips(C, ed, ar);
		
		/* text draw cached (for sequence names), in pixelspace now */
		UI_view2d_text_cache_draw(ar);
	}
	
	/* current frame */
	UI_view2d_view_ortho(v2d);
	if ((sseq->flag & SEQ_DRAWFRAMES) == 0)      flag |= DRAWCFRA_UNIT_SECONDS;
	if ((sseq->flag & SEQ_NO_DRAW_CFRANUM) == 0) flag |= DRAWCFRA_SHOW_NUMBOX;
	ANIM_draw_cfra(C, v2d, flag);
	
	/* markers */
	UI_view2d_view_orthoSpecial(ar, v2d, 1);
	draw_markers_time(C, DRAW_MARKERS_LINES);
	
	/* preview range */
	UI_view2d_view_ortho(v2d);
	ANIM_draw_previewrange(C, v2d);

	/* overlap playhead */
	if (scene->ed && scene->ed->over_flag & SEQ_EDIT_OVERLAY_SHOW) {
		int cfra_over = (scene->ed->over_flag & SEQ_EDIT_OVERLAY_ABS) ? scene->ed->over_cfra : scene->r.cfra + scene->ed->over_ofs;
		glColor3f(0.2, 0.2, 0.2);
		// glRectf(cfra_over, v2d->cur.ymin, scene->ed->over_ofs + scene->r.cfra + 1, v2d->cur.ymax);

		glBegin(GL_LINES);
		glVertex2f(cfra_over, v2d->cur.ymin);
		glVertex2f(cfra_over, v2d->cur.ymax);
		glEnd();

	}
	
	/* reset view matrix */
	UI_view2d_view_restore(C);

	/* scrollers */
	unit = (sseq->flag & SEQ_DRAWFRAMES) ? V2D_UNIT_FRAMES : V2D_UNIT_SECONDSSEQ;
	scrollers = UI_view2d_scrollers_calc(C, v2d, unit, V2D_GRID_CLAMP, V2D_UNIT_VALUES, V2D_GRID_CLAMP);
	UI_view2d_scrollers_draw(C, v2d, scrollers);
	UI_view2d_scrollers_free(scrollers);
}


