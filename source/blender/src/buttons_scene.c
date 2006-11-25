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

#include <time.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"
#include "DNA_node_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_sound_types.h"
#include "DNA_userdef_types.h"
#include "DNA_packedFile_types.h"

#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_node.h"
#include "BKE_library.h"
#include "BKE_scene.h"
#include "BKE_sound.h"
#include "BKE_packedFile.h"
#include "BKE_utildefines.h"

#include "BLI_blenlib.h"

#include "BSE_filesel.h"

#include "BIF_gl.h"
#include "BIF_graphics.h"
#include "BIF_glutil.h"
#include "BIF_interface.h"
#include "BIF_keyval.h"
#include "BIF_mainqueue.h"
#include "BIF_mywindow.h"
#include "BIF_resources.h"
#include "BIF_renderwin.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_toolbox.h"

#include "BIF_butspace.h"

#include "mydevice.h"
#include "blendef.h"

/* -----includes for this file specific----- */

#include "DNA_image_types.h"
#include "BKE_writeavi.h"
#include "BKE_writeffmpeg.h"
#include "BKE_image.h"
#include "BIF_writeimage.h"
#include "BIF_writeavicodec.h"
#include "BIF_editsound.h"
#include "BSE_seqaudio.h"
#include "BSE_headerbuttons.h"

#include "butspace.h" // own module

#ifdef WITH_QUICKTIME
#include "quicktime_export.h"
#endif

#ifdef WITH_FFMPEG

#include <ffmpeg/avcodec.h> /* for PIX_FMT_* and CODEC_ID_* */
#include <ffmpeg/avformat.h>

static int ffmpeg_preset_sel = 0;

extern int is_container(int);

extern void makeffmpegstring(char* string);

#endif

/* here the calls for scene buttons
   - render
   - world
   - anim settings, audio
*/

/* prototypes */
void playback_anim(void);

/* ************************ SOUND *************************** */
static void load_new_sample(char *str)	/* called from fileselect */
{
	char name[FILE_MAXDIR+FILE_MAXFILE];
	bSound *sound;
	bSample *sample, *newsample;

	sound = G.buts->lockpoin;

	if (sound) {
		// save values
		sample = sound->sample;
		strcpy(name, sound->sample->name);

		strcpy(sound->name, str);
		sound_set_sample(sound, NULL);
		sound_initialize_sample(sound);

		if (sound->sample->type == SAMPLE_INVALID) {
			error("Not a valid sample: %s", str);

			newsample = sound->sample;

			// restore values
			strcpy(sound->name, name);
			sound_set_sample(sound, sample);

			// remove invalid sample

			sound_free_sample(newsample);
			BLI_remlink(samples, newsample);
			MEM_freeN(newsample);
		}
	}

	BIF_undo_push("Load new audio file");
	allqueue(REDRAWBUTSSCENE, 0);

}


void do_soundbuts(unsigned short event)
{
	char name[FILE_MAXDIR+FILE_MAXFILE];
	bSound *sound;
	bSample *sample;
	bSound* tempsound;
	ID *id;
	
	sound = G.buts->lockpoin;
	
	switch(event) {
	case B_SOUND_REDRAW:
		allqueue(REDRAWBUTSSCENE, 0);
		break;

	case B_SOUND_LOAD_SAMPLE:
		if (sound) strcpy(name, sound->name);
		else strcpy(name, U.sounddir);
			
		activate_fileselect(FILE_SPECIAL, "SELECT WAV FILE", name, load_new_sample);
		break;

	case B_SOUND_PLAY_SAMPLE:
		if (sound) {
			if (sound->sample->type != SAMPLE_INVALID) {
				sound_play_sound(sound);
				allqueue(REDRAWBUTSSCENE, 0);
			}
		}
		break;

	case B_SOUND_MENU_SAMPLE:
		if (G.buts->menunr > 0) {
			sample = BLI_findlink(samples, G.buts->menunr - 1);
			if (sample && sound) {
				BLI_strncpy(sound->name, sample->name, sizeof(sound->name));
				sound_set_sample(sound, sample);
				do_soundbuts(B_SOUND_REDRAW);
			}
		}
			
		break;
	case B_SOUND_NAME_SAMPLE:
		load_new_sample(sound->name);
		break;
	
	case B_SOUND_UNPACK_SAMPLE:
		if(sound && sound->sample) {
			sample = sound->sample;
			
			if (sample->packedfile) {
				if (G.fileflags & G_AUTOPACK) {
					if (okee("Disable AutoPack ?")) {
						G.fileflags &= ~G_AUTOPACK;
					}
				}
				
				if ((G.fileflags & G_AUTOPACK) == 0) {
					unpackSample(sample, PF_ASK);
				}
			} else {
				sound_set_packedfile(sample, newPackedFile(sample->name));
			}
			allqueue(REDRAWHEADERS, 0);
			do_soundbuts(B_SOUND_REDRAW);
		}
		break;

	case B_SOUND_COPY_SOUND:
		if (sound) {
			tempsound = sound_make_copy(sound);
			sound = tempsound;
			id = &sound->id;
			G.buts->lockpoin = (bSound*)id;
			BIF_undo_push("Copy sound");
			do_soundbuts(B_SOUND_REDRAW);
		}
		break;

	case B_SOUND_RECALC:
		waitcursor(1);
		sound = G.main->sound.first;
		while (sound) {
			free(sound->stream);
			sound->stream = 0;
			audio_makestream(sound);
			sound = (bSound *) sound->id.next;
		}
		waitcursor(0);
		allqueue(REDRAWSEQ, 0);
		break;

	case B_SOUND_RATECHANGED:

		allqueue(REDRAWBUTSSCENE, 0);
		allqueue(REDRAWSEQ, 0);
		break;

	case B_SOUND_MIXDOWN:
		audio_mixdown();
		break;

	default: 
		if (G.f & G_DEBUG) {
			printf("do_soundbuts: unhandled event %d\n", event);
		}
	}
}


static void sound_panel_listener(void)
{
	uiBlock *block;
	int xco= 100, yco=100, mixrate;
	char mixrateinfo[256];
	
	block= uiNewBlock(&curarea->uiblocks, "sound_panel_listener", UI_EMBOSS, UI_HELV, curarea->win);
	if(uiNewPanel(curarea, block, "Listener", "Sound", 320, 0, 318, 204)==0) return;

	mixrate = sound_get_mixrate();
	sprintf(mixrateinfo, "Game Mixrate: %d Hz", mixrate);
	uiDefBut(block, LABEL, 0, mixrateinfo, xco,yco,295,20, 0, 0, 0, 0, 0, "");

	yco -= 30;
	uiDefBut(block, LABEL, 0, "Game listener settings:",xco,yco,195,20, 0, 0, 0, 0, 0, "");

	yco -= 30;
	uiDefButF(block, NUMSLI, B_SOUND_CHANGED, "Volume: ",
		xco,yco,195,24,&G.listener->gain, 0.0, 1.0, 1.0, 0, "Sets the maximum volume for the overall sound");
	
	yco -= 30;
	uiDefBut(block, LABEL, 0, "Game Doppler effect settings:",xco,yco,195,20, 0, 0, 0, 0, 0, "");

	yco -= 30;
	uiDefButF(block, NUMSLI, B_SOUND_CHANGED, "Doppler: ",
	xco,yco,195,24,&G.listener->dopplerfactor, 0.0, 10.0, 1.0, 0, "Use this for scaling the doppler effect");
	
	yco -=30;
	uiDefButF(block, NUMSLI, B_SOUND_CHANGED, "Velocity: ",
	xco,yco,195,24,&G.listener->dopplervelocity,0.0,10000.0, 1.0,0, "Sets the propagation speed of sound");

	
}

static void sound_panel_sequencer(void)
{
	uiBlock *block;
	short xco, yco;
	char mixrateinfo[256];
	
	block= uiNewBlock(&curarea->uiblocks, "sound_panel_sequencer", UI_EMBOSS, UI_HELV, curarea->win);
	if(uiNewPanel(curarea, block, "Sequencer", "Sound", 640, 0, 318, 204)==0) return;

	/* audio sequence engine settings ------------------------------------------------------------------ */

	xco = 1010;
	yco = 195;

	uiDefBut(block, LABEL, 0, "Audio sequencer settings", xco,yco,295,20, 0, 0, 0, 0, 0, "");

	yco -= 25;
	sprintf(mixrateinfo, "Mixing/Sync (latency: %d ms)", (int)( (((float)U.mixbufsize)/(float)G.scene->audio.mixrate)*1000.0 ) );
	uiDefBut(block, LABEL, 0, mixrateinfo, xco,yco,295,20, 0, 0, 0, 0, 0, "");

	yco -= 25;		
	uiDefButI(block, ROW, B_SOUND_RATECHANGED, "44.1 kHz",	xco,yco,75,20, &G.scene->audio.mixrate, 2.0, 44100.0, 0, 0, "Mix at 44.1 kHz");
	uiDefButI(block, ROW, B_SOUND_RATECHANGED, "48.0 kHz",		xco+80,yco,75,20, &G.scene->audio.mixrate, 2.0, 48000.0, 0, 0, "Mix at 48 kHz");
	uiDefBut(block, BUT, B_SOUND_RECALC, "Recalc",		xco+160,yco,75,20, 0, 0, 0, 0, 0, "Recalculate samples");

	yco -= 25;
	uiDefButBitS(block, TOG, AUDIO_SYNC, B_SOUND_CHANGED, "Sync",	xco,yco,115,20, &G.scene->audio.flag, 0, 0, 0, 0, "Use sample clock for syncing animation to audio");
	uiDefButBitS(block, TOG, AUDIO_SCRUB, B_SOUND_CHANGED, "Scrub",		xco+120,yco,115,20, &G.scene->audio.flag, 0, 0, 0, 0, "Scrub when changing frames");

	yco -= 25;
	uiDefBut(block, LABEL, 0, "Main mix", xco,yco,295,20, 0, 0, 0, 0, 0, "");

	yco -= 25;		
	uiDefButF(block, NUMSLI, B_SOUND_CHANGED, "Main (dB): ",
		xco,yco,235,24,&G.scene->audio.main, -24.0, 6.0, 0, 0, "Set the audio master gain/attenuation in dB");

	yco -= 25;
	uiDefButBitS(block, TOG, AUDIO_MUTE, 0, "Mute",	xco,yco,235,24, &G.scene->audio.flag, 0, 0, 0, 0, "Mute audio from sequencer");		
	
	yco -= 35;
	uiDefBut(block, BUT, B_SOUND_MIXDOWN, "MIXDOWN",	xco,yco,235,24, 0, 0, 0, 0, 0, "Create WAV file from sequenced audio (output goes to render output dir)");
	
}

static char *make_sample_menu(void)
{
	int len= BLI_countlist(samples);	/* BKE_sound.h */
	
	if(len) {
		bSample *sample;
		char *str;
		int nr, a=0;
		
		str= MEM_callocN(32*len, "menu");
		
		for(nr=1, sample= samples->first; sample; sample= sample->id.next, nr++) {
			a+= sprintf(str+a, "|%s %%x%d", sample->id.name+2, nr);
		}
		return str;
	}
	return NULL;
}

static void sound_panel_sound(bSound *sound)
{
	static int packdummy=0;
	ID *id, *idfrom;
	uiBlock *block;
	bSample *sample;
	char *strp, ch[256];

	block= uiNewBlock(&curarea->uiblocks, "sound_panel_sound", UI_EMBOSS, UI_HELV, curarea->win);
	if(uiNewPanel(curarea, block, "Sound", "Sound", 0, 0, 318, 204)==0) return;
	
	uiDefBut(block, LABEL, 0, "Blender Sound block",10,180,195,20, 0, 0, 0, 0, 0, "");
	
	// warning: abuse of texnr here! (ton didnt code!)
	buttons_active_id(&id, &idfrom);
	std_libbuttons(block, 10, 160, 0, NULL, B_SOUNDBROWSE2, ID_SO, 0, id, idfrom, &(G.buts->texnr), 1, 0, 0, 0, 0);

	if (sound) {
	
		uiDefBut(block, BUT, B_SOUND_COPY_SOUND, "Copy sound", 220,160,90,20, 0, 0, 0, 0, 0, "Make another copy (duplicate) of the current sound");

		uiSetButLock(sound->id.lib!=0, "Can't edit library data");
		sound_initialize_sample(sound);
		sample = sound->sample;

		/* info string */
		if (sound->sample && sound->sample->len) {
			char *tmp;
			if (sound->sample->channels == 1) tmp= "Mono";
			else if (sound->sample->channels == 2) tmp= "Stereo";
			else tmp= "Unknown";
			
			sprintf(ch, "Sample: %s, %d bit, %d Hz, %d samples", tmp, sound->sample->bits, sound->sample->rate, (sound->sample->len/(sound->sample->bits/8)/sound->sample->channels));
			uiDefBut(block, LABEL, 0, ch, 			35,140,225,20, 0, 0, 0, 0, 0, "");
		}
		else {
			uiDefBut(block, LABEL, 0, "Sample: No sample info available.",35,140,225,20, 0, 0, 0, 0, 0, "");
		}

		/* sample browse buttons */
		uiBlockBeginAlign(block);
		strp= make_sample_menu();
		if (strp) {
			uiDefButS(block, MENU, B_SOUND_MENU_SAMPLE, strp, 10,120,23,20, &(G.buts->menunr), 0, 0, 0, 0, "Select another loaded sample");
			MEM_freeN(strp);
		}
		uiDefBut(block, TEX, B_SOUND_NAME_SAMPLE, "",		35,120,250,20, sound->name, 0.0, 79.0, 0, 0, "The sample file used by this Sound");
		
		if (sound->sample->packedfile) packdummy = 1;
		else packdummy = 0;
		
		uiDefIconButBitI(block, TOG, 1, B_SOUND_UNPACK_SAMPLE, ICON_PACKAGE,
			285, 120,25,20, &packdummy, 0, 0, 0, 0,"Pack/Unpack this sample");
		
		uiBlockBeginAlign(block);
		uiDefBut(block, BUT, B_SOUND_LOAD_SAMPLE, "Load sample", 10, 95,150,24, 0, 0, 0, 0, 0, "Load a different sample file");

		uiDefBut(block, BUT, B_SOUND_PLAY_SAMPLE, "Play", 	160, 95, 150, 24, 0, 0.0, 0, 0, 0, "Playback sample using settings below");
		
		uiBlockBeginAlign(block);
		uiDefButF(block, NUMSLI, B_SOUND_CHANGED, "Volume: ",
			10,70,150,20, &sound->volume, 0.0, 1.0, 0, 0, "Game engine only: Set the volume of this sound");

		uiDefButF(block, NUMSLI, B_SOUND_CHANGED, "Pitch: ",
			160,70,150,20, &sound->pitch, -12.0, 12.0, 0, 0, "Game engine only: Set the pitch of this sound");

		/* looping */
		uiBlockBeginAlign(block);
		uiDefButBitI(block, TOG, SOUND_FLAGS_LOOP, B_SOUND_REDRAW, "Loop",
			10, 50, 95, 20, &sound->flags, 0.0, 0.0, 0, 0, "Game engine only: Toggle between looping on/off");

		if (sound->flags & SOUND_FLAGS_LOOP) {
			uiDefButBitI(block, TOG, SOUND_FLAGS_BIDIRECTIONAL_LOOP, B_SOUND_REDRAW, "Ping Pong",
				105, 50, 95, 20, &sound->flags, 0.0, 0.0, 0, 0, "Game engine only: Toggle between A->B and A->B->A looping");
			
		}
	

		/* 3D settings ------------------------------------------------------------------ */
		uiBlockBeginAlign(block);

		if (sound->sample->channels == 1) {
			uiDefButBitI(block, TOG, SOUND_FLAGS_3D, B_SOUND_REDRAW, "3D Sound",
				10, 10, 90, 20, &sound->flags, 0, 0, 0, 0, "Game engine only: Turns 3D sound on");
			
			if (sound->flags & SOUND_FLAGS_3D) {
				uiDefButF(block, NUMSLI, B_SOUND_CHANGED, "Scale: ",
					100,10,210,20, &sound->attenuation, 0.0, 5.0, 1.0, 0, "Game engine only: Sets the surround scaling factor for this sound");
				
			}
		}
	}
}


/* ************************* SCENE *********************** */


static void output_pic(char *name)
{
	strcpy(G.scene->r.pic, name);
	allqueue(REDRAWBUTSSCENE, 0);
	BIF_undo_push("Change output picture directory");
}

static void backbuf_pic(char *name)
{
	Image *ima;
	
	strcpy(G.scene->r.backbuf, name);
	allqueue(REDRAWBUTSSCENE, 0);

	ima= add_image(name);
	if(ima) {
		free_image_buffers(ima);	/* force read again */
		ima->ok= 1;
	}
	BIF_undo_push("Change background picture");
}

static void ftype_pic(char *name)
{
	strcpy(G.scene->r.ftype, name);
	allqueue(REDRAWBUTSSCENE, 0);
}

static void run_playanim(char *file) 
{
	extern char bprogname[];	/* usiblender.c */
	char str[FILE_MAXDIR+FILE_MAXFILE];
	int pos[2], size[2];

	/* use current settings for defining position of window. it actually should test image size */
	calc_renderwin_rectangle((G.scene->r.xsch*G.scene->r.size)/100, 
							 (G.scene->r.ysch*G.scene->r.size)/100, G.winpos, pos, size);

	sprintf(str, "%s -a -p %d %d \"%s\"", bprogname, pos[0], pos[1], file);
	system(str);
}

void playback_anim(void)
{	
	char file[FILE_MAXDIR+FILE_MAXFILE];

	if(BKE_imtype_is_movie(G.scene->r.imtype)) {
		switch (G.scene->r.imtype) {
#ifdef WITH_QUICKTIME
			case R_QUICKTIME:
				makeqtstring(file);
				break;
#endif
#ifdef WITH_FFMPEG
		case R_FFMPEG:
			makeffmpegstring(file);
			break;
#endif
		default:
			makeavistring(&G.scene->r, file);
			break;
		}
		if(BLI_exist(file)) {
			run_playanim(file);
		}
		else error("Can't find movie: %s", file);
	}
	else {
		BKE_makepicstring(file, G.scene->r.pic, G.scene->r.sfra, G.scene->r.imtype);
		if(BLI_exist(file)) {
			run_playanim(file);
		}
		else error("Can't find image: %s", file);
	}
}

#ifdef WITH_FFMPEG
static void set_ffmpeg_preset(int preset);
#endif

void do_render_panels(unsigned short event)
{
	ScrArea *sa;
	ID *id;

	switch(event) {

	case B_DORENDER:
		BIF_do_render(0);
		break;
	case B_RTCHANGED:
		allqueue(REDRAWALL, 0);
		break;
	case B_SWITCHRENDER:
		/* new panels added, so... */
		G.buts->re_align= 1;
		allqueue(REDRAWBUTSSCENE, 0);
		break;
	case B_PLAYANIM:
		playback_anim();
		break;
		
	case B_DOANIM:
		BIF_do_render(1);
		break;
	
	case B_FS_PIC:
		sa= closest_bigger_area();
		areawinset(sa->win);
		if(G.qual == LR_CTRLKEY)
			activate_imageselect(FILE_SPECIAL, "SELECT OUTPUT PICTURES", G.scene->r.pic, output_pic);
		else
			activate_fileselect(FILE_SPECIAL, "SELECT OUTPUT PICTURES", G.scene->r.pic, output_pic);
		break;

	case B_FS_BACKBUF:
		sa= closest_bigger_area();
		areawinset(sa->win);
		if(G.qual == LR_CTRLKEY)
			activate_imageselect(FILE_SPECIAL, "SELECT BACKBUF PICTURE", G.scene->r.backbuf, backbuf_pic);
		else
			activate_fileselect(FILE_SPECIAL, "SELECT BACKBUF PICTURE", G.scene->r.backbuf, backbuf_pic);
		break;

	case B_FS_FTYPE:
		sa= closest_bigger_area();
		areawinset(sa->win);
		if(G.qual == LR_CTRLKEY)
			activate_imageselect(FILE_SPECIAL, "SELECT FTYPE", G.scene->r.ftype, ftype_pic);
		else
			activate_fileselect(FILE_SPECIAL, "SELECT FTYPE", G.scene->r.ftype, ftype_pic);
		break;
	
	case B_PR_PAL:
		G.scene->r.xsch= 720;
		G.scene->r.ysch= 576;
		G.scene->r.xasp= 54;
		G.scene->r.yasp= 51;
		G.scene->r.size= 100;
		G.scene->r.frs_sec= 25;
		G.scene->r.mode &= ~R_PANORAMA;
		G.scene->r.xparts=  G.scene->r.yparts= 4;
#ifdef WITH_FFMPEG
		G.scene->r.ffcodecdata.gop_size = 15;
#endif		
		BLI_init_rctf(&G.scene->r.safety, 0.1, 0.9, 0.1, 0.9);
		BIF_undo_push("Set PAL");
		allqueue(REDRAWBUTSSCENE, 0);
		allqueue(REDRAWVIEWCAM, 0);
		break;

	case B_FILETYPEMENU:
		allqueue(REDRAWBUTSSCENE, 0);
#ifdef WITH_FFMPEG
                if (G.scene->r.imtype == R_FFMPEG) {
			if (G.scene->r.ffcodecdata.type <= 0 ||
			    G.scene->r.ffcodecdata.codec <= 0 ||
			    G.scene->r.ffcodecdata.audio_codec <= 0 ||
			    G.scene->r.ffcodecdata.video_bitrate <= 1) {
				G.scene->r.ffcodecdata.codec 
					= CODEC_ID_MPEG2VIDEO;
				set_ffmpeg_preset(FFMPEG_PRESET_DVD);
			}

			if (G.scene->r.ffcodecdata.audio_codec <= 0) {
				G.scene->r.ffcodecdata.audio_codec 
					= CODEC_ID_MP2;
				G.scene->r.ffcodecdata.audio_bitrate = 128;
			}
			break;
                }
#endif
#if defined (_WIN32) || defined (__APPLE__)
		// fall through to codec settings if this is the first
		// time R_AVICODEC is selected for this scene.
		if (((G.scene->r.imtype == R_AVICODEC) 
			 && (G.scene->r.avicodecdata == NULL)) ||
			((G.scene->r.imtype == R_QUICKTIME) 
			 && (G.scene->r.qtcodecdata == NULL))) {
		} else {
		  break;
		}
#endif /*_WIN32 || __APPLE__ */

	case B_SELECTCODEC:
#if defined (_WIN32) || defined (__APPLE__)
		if ((G.scene->r.imtype == R_QUICKTIME)) { /* || (G.scene->r.qtcodecdata)) */
#ifdef WITH_QUICKTIME
			get_qtcodec_settings();
#endif /* WITH_QUICKTIME */
		}
#if defined (_WIN32) && !defined(FREE_WINDOWS)
		else
			get_avicodec_settings();
#endif /* _WIN32 && !FREE_WINDOWS */
#endif /* _WIN32 || __APPLE__ */
		break;

	case B_PR_HD:
		G.scene->r.xsch= 1920;
		G.scene->r.ysch= 1080;
		G.scene->r.xasp= 1;
		G.scene->r.yasp= 1;
		G.scene->r.size= 100;
		G.scene->r.mode &= ~R_PANORAMA;
		G.scene->r.xparts=  G.scene->r.yparts= 4;
		
		BLI_init_rctf(&G.scene->r.safety, 0.1, 0.9, 0.1, 0.9);
		BIF_undo_push("Set FULL");
		allqueue(REDRAWBUTSSCENE, 0);
		allqueue(REDRAWVIEWCAM, 0);
		break;
	case B_PR_FULL:
		G.scene->r.xsch= 1280;
		G.scene->r.ysch= 1024;
		G.scene->r.xasp= 1;
		G.scene->r.yasp= 1;
		G.scene->r.size= 100;
		G.scene->r.mode &= ~R_PANORAMA;
		G.scene->r.xparts=  G.scene->r.yparts= 4;

		BLI_init_rctf(&G.scene->r.safety, 0.1, 0.9, 0.1, 0.9);
		BIF_undo_push("Set FULL");
		allqueue(REDRAWBUTSSCENE, 0);
		allqueue(REDRAWVIEWCAM, 0);
		break;
	case B_PR_PRV:
		G.scene->r.xsch= 640;
		G.scene->r.ysch= 512;
		G.scene->r.xasp= 1;
		G.scene->r.yasp= 1;
		G.scene->r.size= 50;
		G.scene->r.mode &= ~R_PANORAMA;
		G.scene->r.xparts=  G.scene->r.yparts= 2;

		BLI_init_rctf(&G.scene->r.safety, 0.1, 0.9, 0.1, 0.9);
		allqueue(REDRAWVIEWCAM, 0);
		allqueue(REDRAWBUTSSCENE, 0);
		break;
	case B_PR_PAL169:
		G.scene->r.xsch= 720;
		G.scene->r.ysch= 576;
		G.scene->r.xasp= 64;
		G.scene->r.yasp= 45;
		G.scene->r.size= 100;
		G.scene->r.frs_sec= 25;
		G.scene->r.mode &= ~R_PANORAMA;
		G.scene->r.xparts=  G.scene->r.yparts= 4;
#ifdef WITH_FFMPEG
		G.scene->r.ffcodecdata.gop_size = 15;
#endif		

		BLI_init_rctf(&G.scene->r.safety, 0.1, 0.9, 0.1, 0.9);
		BIF_undo_push("Set PAL 16/9");
		allqueue(REDRAWVIEWCAM, 0);
		allqueue(REDRAWBUTSSCENE, 0);
		break;
	case B_PR_PC:
		G.scene->r.xsch= 640;
		G.scene->r.ysch= 480;
		G.scene->r.xasp= 100;
		G.scene->r.yasp= 100;
		G.scene->r.size= 100;
		G.scene->r.mode &= ~R_PANORAMA;
		G.scene->r.xparts=  G.scene->r.yparts= 4;

		BLI_init_rctf(&G.scene->r.safety, 0.0, 1.0, 0.0, 1.0);
		BIF_undo_push("Set PC");
		allqueue(REDRAWVIEWCAM, 0);
		allqueue(REDRAWBUTSSCENE, 0);
		break;
	case B_PR_PRESET:
		G.scene->r.xsch= 720;
		G.scene->r.ysch= 576;
		G.scene->r.xasp= 54;
		G.scene->r.yasp= 51;
		G.scene->r.size= 100;
		G.scene->r.mode= R_OSA+R_SHADOW+R_FIELDS;
		G.scene->r.imtype= R_TARGA;
		G.scene->r.xparts=  G.scene->r.yparts= 4;

		BLI_init_rctf(&G.scene->r.safety, 0.1, 0.9, 0.1, 0.9);
		BIF_undo_push("Set Default");
		allqueue(REDRAWVIEWCAM, 0);
		allqueue(REDRAWBUTSSCENE, 0);
		break;
	case B_PR_PANO:
		G.scene->r.xsch= 576;
		G.scene->r.ysch= 176;
		G.scene->r.xasp= 115;
		G.scene->r.yasp= 100;
		G.scene->r.size= 100;
		G.scene->r.mode |= R_PANORAMA;
		G.scene->r.xparts=  16;
		G.scene->r.yparts= 1;

		BLI_init_rctf(&G.scene->r.safety, 0.1, 0.9, 0.1, 0.9);
		BIF_undo_push("Set Panorama");
		allqueue(REDRAWVIEWCAM, 0);
		allqueue(REDRAWBUTSSCENE, 0);
		break;
	case B_PR_NTSC:
		G.scene->r.xsch= 720;
		G.scene->r.ysch= 480;
		G.scene->r.xasp= 10;
		G.scene->r.yasp= 11;
		G.scene->r.size= 100;
		G.scene->r.frs_sec= 30;
		G.scene->r.mode &= ~R_PANORAMA;
		G.scene->r.xparts=  G.scene->r.yparts= 2;
#ifdef WITH_FFMPEG
		G.scene->r.ffcodecdata.gop_size = 18;
#endif		
		
		BLI_init_rctf(&G.scene->r.safety, 0.1, 0.9, 0.1, 0.9);
		BIF_undo_push("Set NTSC");
		allqueue(REDRAWBUTSSCENE, 0);
		allqueue(REDRAWVIEWCAM, 0);
		break;

	case B_SETBROWSE:
		id= (ID*) G.scene->set;
		
		if (G.buts->menunr==-2) {
			 activate_databrowse(id, ID_SCE, 0, B_SETBROWSE, &G.buts->menunr, do_render_panels);
		} 
		else if (G.buts->menunr>0) {
			Scene *newset= (Scene*) BLI_findlink(&G.main->scene, G.buts->menunr-1);
			
			if (newset==G.scene)
				error("Not allowed");
			else if (newset) {
				G.scene->set= newset;
				if (scene_check_setscene(G.scene)==0)
					error("This would create a cycle");

				allqueue(REDRAWBUTSSCENE, 0);
				allqueue(REDRAWVIEW3D, 0);
				BIF_undo_push("Change Set Scene");
			}
		}  
		break;
	case B_CLEARSET:
		G.scene->set= NULL;
		allqueue(REDRAWBUTSSCENE, 0);
		allqueue(REDRAWVIEW3D, 0);
		BIF_undo_push("Clear Set Scene");
		
		break;
	case B_SET_EDGE:
		allqueue(REDRAWBUTSSCENE, 0);
		break;
	case B_SET_ZBLUR:
		G.scene->r.mode &= ~R_EDGE;
		allqueue(REDRAWBUTSSCENE, 0);
		break;
	case B_ADD_RENDERLAYER:
		if(G.scene->r.actlay==32767) {
			scene_add_render_layer(G.scene);
			G.scene->r.actlay= BLI_countlist(&G.scene->r.layers) - 1;
		}
		allqueue(REDRAWBUTSSCENE, 0);
		allqueue(REDRAWNODE, 0);
	}
}

/* NOTE: this is a block-menu, needs 0 events, otherwise the menu closes */
static uiBlock *edge_render_menu(void *arg_unused)
{
	uiBlock *block;
	
	block= uiNewBlock(&curarea->uiblocks, "edge render", UI_EMBOSS, UI_HELV, curarea->win);
		
	/* use this for a fake extra empy space around the buttons */
	uiDefBut(block, LABEL, 0, "",  0, 0, 220, 115, NULL,  0, 0, 0, 0, "");
	
	uiDefButS(block, NUM, 0,"Eint:",  	45,75,175,19,  &G.scene->r.edgeint, 0.0, 255.0, 0, 0,
		  "Sets edge intensity for Toon shading");

	/* colour settings for the toon shading */
	uiDefButF(block, COL, 0, "", 		10, 10,30,60,  &(G.scene->r.edgeR), 0, 0, 0, B_EDGECOLSLI, "");
	
	uiBlockBeginAlign(block);
	uiDefButF(block, NUMSLI, 0, "R ",   45, 50, 175,19,   &G.scene->r.edgeR, 0.0, 1.0, B_EDGECOLSLI, 0,
		  "Colour for edges in toon shading mode.");
	uiDefButF(block, NUMSLI, 0, "G ",  	45, 30, 175,19,  &G.scene->r.edgeG, 0.0, 1.0, B_EDGECOLSLI, 0,
		  "Colour for edges in toon shading mode.");
	uiDefButF(block, NUMSLI, 0, "B ",  	45, 10, 175,19,  &G.scene->r.edgeB, 0.0, 1.0, B_EDGECOLSLI, 0,
		  "Colour for edges in toon shading mode.");

	
	uiBlockSetDirection(block, UI_TOP);
	
	return block;
}

#if 0
/* NOTE: this is a block-menu, needs 0 events, otherwise the menu closes */
static uiBlock *post_render_menu(void *arg_unused)
{
	uiBlock *block;
	
	block= uiNewBlock(&curarea->uiblocks, "post render", UI_EMBOSS, UI_HELV, curarea->win);
		
	/* use this for a fake extra empy space around the buttons */
	uiDefBut(block, LABEL, 0, "",			-10, -10, 200, 120, NULL, 0, 0, 0, 0, "");
	uiBlockBeginAlign(block);
	uiDefButF(block, NUMSLI, 0, "Add:",		0,80,180,19, &G.scene->r.postadd, -1.0, 1.0, 0, 0, "");
	uiDefButF(block, NUMSLI, 0, "Mul:",		0,60,180,19,  &G.scene->r.postmul, 0.01, 4.0, 0, 0, "");
	uiDefButF(block, NUMSLI, 0, "Gamma:",	0,40,180,19,  &G.scene->r.postgamma, 0.1, 4.0, 0, 0, "");
	uiDefButF(block, NUMSLI, 0, "Hue:",		0,20,180,19,  &G.scene->r.posthue, -0.5, 0.5, 0, 0, "");
	uiDefButF(block, NUMSLI, 0, "Sat:",		0, 0,180,19,  &G.scene->r.postsat, 0.0, 4.0, 0, 0, "");

	uiBlockSetDirection(block, UI_TOP);
	
	addqueue(curarea->win, UI_BUT_EVENT, B_FBUF_REDO);
	
	return block;
}
#endif

/* NOTE: this is a block-menu, needs 0 events, otherwise the menu closes */
static uiBlock *framing_render_menu(void *arg_unused)
{
	uiBlock *block;
	short yco = 190, xco = 0;
	int randomcolorindex = 1234;

	block= uiNewBlock(&curarea->uiblocks, "framing_options", UI_EMBOSS, UI_HELV, curarea->win);

	/* use this for a fake extra empy space around the buttons */
	uiDefBut(block, LABEL, 0, "",			-5, -10, 295, 224, NULL, 0, 0, 0, 0, "");

	uiDefBut(block, LABEL, 0, "Framing:", xco, yco, 68,19, 0, 0, 0, 0, 0, "");
	uiBlockBeginAlign(block);
	uiDefButC(block, ROW, 0, "Stretch",	xco += 70, yco, 68, 19, &G.scene->framing.type, 1.0, SCE_GAMEFRAMING_SCALE , 0, 0, "Stretch or squeeze the viewport to fill the display window");
	uiDefButC(block, ROW, 0, "Expose",	xco += 70, yco, 68, 19, &G.scene->framing.type, 1.0, SCE_GAMEFRAMING_EXTEND, 0, 0, "Show the entire viewport in the display window, viewing more horizontally or vertically");
	uiDefButC(block, ROW, 0, "Letterbox",	    xco += 70, yco, 68, 19, &G.scene->framing.type, 1.0, SCE_GAMEFRAMING_BARS  , 0, 0, "Show the entire viewport in the display window, using bar horizontally or vertically");
	uiBlockEndAlign(block);

	yco -= 25;
	xco = 40;

	uiDefButF(block, COL, 0, "",                0, yco - 58 + 18, 33, 58, &G.scene->framing.col[0], 0, 0, 0, randomcolorindex, "");

	uiBlockBeginAlign(block);
	uiDefButF(block, NUMSLI, 0, "R ", xco,yco,243,18, &G.scene->framing.col[0], 0.0, 1.0, randomcolorindex, 0, "Set the red component of the bars");
	yco -= 20;
	uiDefButF(block, NUMSLI, 0, "G ", xco,yco,243,18, &G.scene->framing.col[1], 0.0, 1.0, randomcolorindex, 0, "Set the green component of the bars");
	yco -= 20;
	uiDefButF(block, NUMSLI, 0, "B ", xco,yco,243,18, &G.scene->framing.col[2], 0.0, 1.0, randomcolorindex, 0, "Set the blue component of the bars");
	uiBlockEndAlign(block);
	
	xco = 0;
	uiDefBut(block, LABEL, 0, "Fullscreen:",		xco, yco-=30, 100, 19, 0, 0.0, 0.0, 0, 0, "");
	uiDefButS(block, TOG, 0, "Fullscreen", xco+70, yco, 68, 19, &G.scene->r.fullscreen, 0.0, 0.0, 0, 0, "Starts player in a new fullscreen display");
	uiBlockBeginAlign(block);
	uiDefButS(block, NUM, 0, "X:",		xco+40, yco-=27, 100, 19, &G.scene->r.xplay, 10.0, 2000.0, 0, 0, "Displays current X screen/window resolution. Click to change.");
	uiDefButS(block, NUM, 0, "Y:",		xco+140, yco, 100, 19, &G.scene->r.yplay,    10.0, 2000.0, 0, 0, "Displays current Y screen/window resolution. Click to change.");
	uiDefButS(block, NUM, 0, "Freq:",	xco+40, yco-=21, 100, 19, &G.scene->r.freqplay, 10.0, 2000.0, 0, 0, "Displays clock frequency of fullscreen display. Click to change.");
	uiDefButS(block, NUM, 0, "Bits:",	xco+140, yco, 100, 19, &G.scene->r.depth, 8.0, 32.0, 800.0, 0, "Displays bit depth of full screen display. Click to change.");
	uiBlockEndAlign(block);

	/* stereo settings */
	/* can't use any definition from the game engine here so hardcode it. Change it here when it changes there!
	 * RAS_IRasterizer has definitions:
	 * RAS_STEREO_NOSTEREO		 1
	 * RAS_STEREO_QUADBUFFERED 2
	 * RAS_STEREO_ABOVEBELOW	 3
	 * RAS_STEREO_INTERLACED	 4	 future
	 * RAS_STEREO_ANAGLYPH		5
	 * RAS_STEREO_SIDEBYSIDE	6
	 * RAS_STEREO_VINTERLACE	7
	 */
	uiBlockBeginAlign(block);
	uiDefButS(block, ROW, 0, "No Stereo", xco, yco-=30, 88, 19, &(G.scene->r.stereomode), 7.0, 1.0, 0, 0, "Disables stereo");
	uiDefButS(block, ROW, 0, "Pageflip", xco+=90, yco, 88, 19, &(G.scene->r.stereomode), 7.0, 2.0, 0, 0, "Enables hardware pageflip stereo method");
	uiDefButS(block, ROW, 0, "Syncdouble", xco+=90, yco, 88, 19, &(G.scene->r.stereomode), 7.0, 3.0, 0, 0, "Enables syncdoubling stereo method");
	uiDefButS(block, ROW, 0, "Anaglyph", xco-=180, yco-=21, 88, 19, &(G.scene->r.stereomode), 7.0, 5.0, 0, 0, "Enables anaglyph (Red-Blue) stereo method");
	uiDefButS(block, ROW, 0, "Side by Side", xco+=90, yco, 88, 19, &(G.scene->r.stereomode), 7.0, 6.0, 0, 0, "Enables side by side left and right images");
	uiDefButS(block, ROW, 0, "V Interlace", xco+=90, yco, 88, 19, &(G.scene->r.stereomode), 7.0, 7.0, 0, 0, "Enables interlaced vertical strips for autostereo display");
	
	uiBlockEndAlign(block);

	uiBlockSetDirection(block, UI_TOP);

	return block;
}

#ifdef WITH_FFMPEG

static char* ffmpeg_format_pup(void) 
{
	static char string[2048];
	char formatstring[2048];
#if 0
       int i = 0;
       int stroffs = 0;
       AVOutputFormat* next = first_oformat;
       formatstring = "FFMpeg format: %%t";
      sprintf(string, formatstring);
       formatstring = "|%s %%x%d";
       /* FIXME: This should only be generated once */
       while (next != NULL) {
               if (next->video_codec != CODEC_ID_NONE && !(next->flags & AVFMT_NOFILE)) {
                       sprintf(string+stroffs, formatstring, next->name, i++);
                       stroffs += strlen(string+stroffs);
               }
               next = next->next;
       }
       return string;
#endif
       strcpy(formatstring, "FFMpeg format: %%t|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d");
       sprintf(string, formatstring,
               "MPEG-1", FFMPEG_MPEG1,
               "MPEG-2", FFMPEG_MPEG2,
               "MPEG-4", FFMPEG_MPEG4,
               "AVI",    FFMPEG_AVI,
               "Quicktime", FFMPEG_MOV,
               "DV", FFMPEG_DV,
	       "H264", FFMPEG_H264,
	       "XVid", FFMPEG_XVID);
       return string;
}

static char* ffmpeg_preset_pup(void) 
{
	static char string[2048];
	char formatstring[2048];

       strcpy(formatstring, "FFMpeg preset: %%t|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d");
       sprintf(string, formatstring,
               "", FFMPEG_PRESET_NONE,
               "DVD", FFMPEG_PRESET_DVD,
               "SVCD", FFMPEG_PRESET_SVCD,
               "VCD", FFMPEG_PRESET_VCD,
               "DV", FFMPEG_PRESET_DV);
       return string;
}


static char* ffmpeg_codec_pup(void) {
       static char string[2048];
       char formatstring[2048];
       strcpy(formatstring, "FFMpeg format: %%t|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d");
       sprintf(string, formatstring,
               "MPEG1", CODEC_ID_MPEG1VIDEO,
               "MPEG2", CODEC_ID_MPEG2VIDEO,
               "MPEG4(divx)", CODEC_ID_MPEG4,
               "HuffYUV", CODEC_ID_HUFFYUV,
	       "DV", CODEC_ID_DVVIDEO,
               "H264", CODEC_ID_H264,
	       "XVid", CODEC_ID_XVID);
       return string;

}

static char* ffmpeg_audio_codec_pup(void) {
       static char string[2048];
       char formatstring[2048];
       strcpy(formatstring, "FFMpeg format: %%t|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d");
       sprintf(string, formatstring,
               "MP2", CODEC_ID_MP2,
               "MP3", CODEC_ID_MP3,
               "AC3", CODEC_ID_AC3,
               "AAC", CODEC_ID_AAC,
	       "PCM", CODEC_ID_PCM_S16LE);
       return string;

}

#endif

static char *imagetype_pup(void)
{
	static char string[1024];
	char formatstring[1024];
	char appendstring[1024];

	strcpy(formatstring, "Save image as: %%t|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d|%s %%x%d");

#ifdef __sgi
	strcat(formatstring, "|%s %%x%d");	// add space for Movie
#endif

	strcat(formatstring, "|%s %%x%d");	// add space for PNG
	strcat(formatstring, "|%s %%x%d");	// add space for BMP
	strcat(formatstring, "|%s %%x%d");	// add space for Radiance HDR
	strcat(formatstring, "|%s %%x%d");	// add space for Cineon
	strcat(formatstring, "|%s %%x%d");	// add space for DPX
	
#ifdef _WIN32
	strcat(formatstring, "|%s %%x%d");	// add space for AVI Codec
#endif

#ifdef WITH_FFMPEG
       strcat(formatstring, "|%s %%x%d"); // Add space for ffmpeg
#endif
       strcat(formatstring, "|%s %%x%d"); // Add space for frameserver

#ifdef WITH_QUICKTIME
	if(G.have_quicktime)
		strcat(formatstring, "|%s %%x%d");	// add space for Quicktime
#endif

	if(G.have_quicktime) {
		sprintf(string, formatstring,
			"Frameserver",   R_FRAMESERVER,
#ifdef WITH_FFMPEG
                       "FFMpeg",         R_FFMPEG,
#endif
			"AVI Raw",        R_AVIRAW,
			"AVI Jpeg",       R_AVIJPEG,
#ifdef _WIN32
			"AVI Codec",      R_AVICODEC,
#endif
#ifdef WITH_QUICKTIME
			"QuickTime",      R_QUICKTIME,
#endif
			"Targa",          R_TARGA,
			"Targa Raw",      R_RAWTGA,
			"PNG",            R_PNG,
			"BMP",            R_BMP,
			"Jpeg",           R_JPEG90,
			"HamX",           R_HAMX,
			"Iris",           R_IRIS,
			"Radiance HDR",   R_RADHDR,
			"Cineon",		  R_CINEON,
			"DPX",			  R_DPX
#ifdef __sgi
			,"Movie",          R_MOVIE
#endif
		);
	} else {
		sprintf(string, formatstring,
			"Frameserver",   R_FRAMESERVER,
#ifdef WITH_FFMPEG
                       "FFMpeg",         R_FFMPEG,
#endif
			"AVI Raw",        R_AVIRAW,
			"AVI Jpeg",       R_AVIJPEG,
#ifdef _WIN32
			"AVI Codec",      R_AVICODEC,
#endif
			"Targa",          R_TARGA,
			"Targa Raw",      R_RAWTGA,
			"PNG",            R_PNG,
			"BMP",            R_BMP,
			"Jpeg",           R_JPEG90,
			"HamX",           R_HAMX,
			"Iris",           R_IRIS,
			"Radiance HDR",   R_RADHDR,
			"Cineon",		  R_CINEON,
			"DPX",			  R_DPX
#ifdef __sgi
			,"Movie",          R_MOVIE
#endif
		);
	}

#ifdef WITH_OPENEXR
	strcpy(formatstring, "|%s %%x%d");
	sprintf(appendstring, formatstring, "OpenEXR", R_OPENEXR);
	strcat(string, appendstring);
#endif
	
	if (G.have_libtiff) {
		strcpy(formatstring, "|%s %%x%d");
		sprintf(appendstring, formatstring, "TIFF", R_TIFF);
		strcat(string, appendstring);
	}

	return (string);
}

#ifdef _WIN32
static char *avicodec_str(void)
{
	static char string[1024];

	sprintf(string, "Codec: %s", G.scene->r.avicodecdata->avicodecname);

	return string;
}
#endif

static void render_panel_output(void)
{
	ID *id;
	int a,b;
	uiBlock *block;
	char *strp;


	block= uiNewBlock(&curarea->uiblocks, "render_panel_output", UI_EMBOSS, UI_HELV, curarea->win);
	if(uiNewPanel(curarea, block, "Output", "Render", 0, 0, 318, 204)==0) return;
	
	uiBlockBeginAlign(block);
	uiDefIconBut(block, BUT, B_FS_PIC, ICON_FILESEL,	10, 190, 20, 20, 0, 0, 0, 0, 0, "Open Fileselect to get Pics dir/name");
	uiDefBut(block, TEX,0,"",							31, 190, 279, 20,G.scene->r.pic, 0.0,79.0, 0, 0, "Directory/name to save rendered Pics to");
	uiDefIconBut(block, BUT,B_FS_BACKBUF, ICON_FILESEL, 10, 168, 20, 20, 0, 0, 0, 0, 0, "Open Fileselect to get Backbuf image");
	uiDefBut(block, TEX,0,"",							31, 168, 279, 20,G.scene->r.backbuf, 0.0,79.0, 0, 0, "Image to use as background for rendering");
	uiDefIconBut(block, BUT,B_FS_FTYPE, ICON_FILESEL,	10, 146, 20, 20, 0, 0, 0, 0, 0, "Open Fileselect to get Ftype image");
	uiDefBut(block, TEX,0,"",							31, 146, 279, 20,G.scene->r.ftype,0.0,79.0, 0, 0, "Image to use with FTYPE Image type");
	uiBlockEndAlign(block);
	
	
	/* SET BUTTON */
	uiBlockBeginAlign(block);
	id= (ID *)G.scene->set;
	IDnames_to_pupstring(&strp, NULL, NULL, &(G.main->scene), id, &(G.buts->menunr));
	if(strp[0])
		uiDefButS(block, MENU, B_SETBROWSE, strp, 10, 120, 20, 20, &(G.buts->menunr), 0, 0, 0, 0, "Scene to link as a Set");
	MEM_freeN(strp);

	if(G.scene->set) {
		uiSetButLock(1, NULL);
		uiDefIDPoinBut(block, test_scenepoin_but, ID_SCE, 0, "",	31, 120, 100, 20, &(G.scene->set), "Name of the Set");
		uiClearButLock();
		uiDefIconBut(block, BUT, B_CLEARSET, ICON_X, 		132, 120, 20, 20, 0, 0, 0, 0, 0, "Remove Set link");
	}
	uiBlockEndAlign(block);

	uiBlockSetCol(block, TH_BUT_SETTING1);
	uiDefButBitS(block, TOG, R_BACKBUF, B_NOP,"Backbuf",	10, 94, 80, 20, &G.scene->r.bufflag, 0, 0, 0, 0, "Enable/Disable use of Backbuf image");	
	uiDefButBitI(block, TOG, R_THREADS, B_NOP,"Threads",	10, 68, 80, 20, &G.scene->r.mode, 0, 0, 0, 0, "Enable/Disable render in two threads");	
	uiBlockSetCol(block, TH_AUTO);
		
	uiBlockBeginAlign(block);
	for(b=2; b>=0; b--)
		for(a=0; a<3; a++)
			uiDefButBitS(block, TOG, 1<<(3*b+a), 800,"",	(short)(10+18*a),(short)(10+14*b),16,12, &G.winpos, 0, 0, 0, 0, "Render window placement on screen");
	uiBlockEndAlign(block);

	uiDefButBitS(block, TOG, R_EXR_TILE_FILE, B_NOP, "Save Buffers", 72, 31, 120, 19, &G.scene->r.scemode, 0.0, 0.0, 0, 0, "Save the tiles for all RenderLayers and used SceneNodes to files, to save memory");
	
	uiDefButS(block, MENU, B_REDR, "Render Display %t|Render Window %x1|Image Editor %x0|Full Screen %x2",	
					72, 10, 120, 19, &G.displaymode, 0.0, (float)R_DISPLAYWIN, 0, 0, "Sets render output display");

	uiDefButBitS(block, TOG, R_EXTENSION, B_NOP, "Extensions", 205, 10, 105, 19, &G.scene->r.scemode, 0.0, 0.0, 0, 0, "Adds extensions to the output when rendering animations");

	/* Dither control */
	uiDefButF(block, NUM,B_DIFF, "Dither:",         205,31,105,19, &G.scene->r.dither_intensity, 0.0, 2.0, 0, 0, "The amount of dithering noise present in the output image (0.0 = no dithering)");
	
	/* Toon shading buttons */
	uiBlockBeginAlign(block);
	uiDefButBitI(block, TOG, R_EDGE, B_NOP,"Edge",   100, 94, 70, 20, &G.scene->r.mode, 0, 0, 0, 0, "Enable Toon Edge-enhance");
	uiDefBlockBut(block, edge_render_menu, NULL, "Edge Settings", 170, 94, 140, 20, "Display Edge settings");
	uiBlockEndAlign(block);
	
	uiDefButBitS(block, TOG, R_FREE_IMAGE, B_NOP, "Free Tex Images", 170, 68, 140, 20, &G.scene->r.scemode, 0.0, 0.0, 0, 0, "Frees all Images used by Textures after each render");
}

static void render_panel_render(void)
{
	uiBlock *block;
	char str[256];

	block= uiNewBlock(&curarea->uiblocks, "render_panel_render", UI_EMBOSS, UI_HELV, curarea->win);
	if(uiNewPanel(curarea, block, "Render", "Render", 320, 0, 318, 204)==0) return;

	uiBlockBeginAlign(block);
	uiDefBut(block, BUT,B_DORENDER,"RENDER",	369, 164, 191,37, 0, 0, 0, 0, 0, "Start the rendering");
#ifndef DISABLE_YAFRAY
	/* yafray: on request, render engine menu is back again, and moved to Render panel */
	uiDefButS(block, MENU, B_SWITCHRENDER, "Rendering Engine %t|Blender Internal %x0|YafRay %x1", 
												369, 142, 191, 20, &G.scene->r.renderer, 0, 0, 0, 0, "Choose rendering engine");	
#else
	uiDefButS(block, MENU, B_SWITCHRENDER, "Rendering Engine %t|Blender Internal %x0", 
												369, 142, 191, 20, &G.scene->r.renderer, 0, 0, 0, 0, "Choose rendering engine");	
#endif /* disable yafray */

	uiBlockBeginAlign(block);
	uiDefButBitI(block, TOG, R_OSA, 0, "OSA",		369,109,122,20,&G.scene->r.mode, 0, 0, 0, 0, "Enables Oversampling (Anti-aliasing)");
	uiDefButS(block, ROW,B_DIFF,"5",			369,88,29,20,&G.scene->r.osa,2.0,5.0, 0, 0, "Sets oversample level to 5");
	uiDefButS(block, ROW,B_DIFF,"8",			400,88,29,20,&G.scene->r.osa,2.0,8.0, 0, 0, "Sets oversample level to 8 (Recommended)");
	uiDefButS(block, ROW,B_DIFF,"11",			431,88,29,20,&G.scene->r.osa,2.0,11.0, 0, 0, "Sets oversample level to 11");
	uiDefButS(block, ROW,B_DIFF,"16",			462,88,29,20,&G.scene->r.osa,2.0,16.0, 0, 0, "Sets oversample level to 16");
	uiBlockEndAlign(block);

	uiBlockBeginAlign(block);
	uiDefButBitI(block, TOG, R_MBLUR, 0, "MBLUR",	496,109,64,20,&G.scene->r.mode, 0, 0, 0, 0, "Enables Motion Blur calculation");
	uiDefButF(block, NUM,B_DIFF,"Bf:",			496,88,64,20,&G.scene->r.blurfac, 0.01, 5.0, 10, 2, "Sets motion blur factor");
	uiBlockEndAlign(block);

	uiBlockBeginAlign(block);
	uiDefButS(block, NUM,B_DIFF,"Xparts:",		369,46,95,29,&G.scene->r.xparts,1.0, 512.0, 0, 0, "Sets the number of horizontal parts to render image in (For panorama sets number of camera slices)");
	uiDefButS(block, NUM,B_DIFF,"Yparts:",		465,46,95,29,&G.scene->r.yparts,1.0, 64.0, 0, 0, "Sets the number of vertical parts to render image in");
	uiBlockEndAlign(block);

	uiBlockBeginAlign(block);
	uiDefButS(block, ROW,800,"Sky",		369,13,35,20,&G.scene->r.alphamode,3.0,0.0, 0, 0, "Fill background with sky");
	uiDefButS(block, ROW,800,"Premul",	405,13,50,20,&G.scene->r.alphamode,3.0,1.0, 0, 0, "Multiply alpha in advance");
	uiDefButS(block, ROW,800,"Key",		456,13,35,20,&G.scene->r.alphamode,3.0,2.0, 0, 0, "Alpha and colour values remain unchanged");
	uiBlockEndAlign(block);

	if(G.scene->r.mode & R_RAYTRACE)
		uiDefButS(block, MENU, B_DIFF,"Octree resolution %t|64 %x64|128 %x128|256 %x256|512 %x512",	496,13,64,20,&G.scene->r.ocres,0.0,0.0, 0, 0, "Octree resolution for ray tracing");

	uiBlockBeginAlign(block);
	uiDefButBitI(block, TOG, R_SHADOW, 0,"Shadow",	565,172,60,29, &G.scene->r.mode, 0, 0, 0, 0, "Enable shadow calculation");
	uiDefButBitI(block, TOG, R_ENVMAP, 0,"EnvMap",	627,172,60,29, &G.scene->r.mode, 0, 0, 0, 0, "Enable environment map rendering");
	uiDefButBitI(block, TOG, R_PANORAMA, 0,"Pano",	565,142,40,29, &G.scene->r.mode, 0, 0, 0, 0, "Enable panorama rendering (output width is multiplied by Xparts)");
	uiDefButBitI(block, TOG, R_RAYTRACE, B_REDR,"Ray",606,142,40,29, &G.scene->r.mode, 0, 0, 0, 0, "Enable ray tracing");
	uiDefButBitI(block, TOG, R_RADIO, 0,"Radio",	647,142,40,29, &G.scene->r.mode, 0, 0, 0, 0, "Enable radiosity rendering");
	uiBlockEndAlign(block);
	
	uiBlockBeginAlign(block);
	uiDefButS(block, ROW,B_DIFF,"100%",			565,109,122,20,&G.scene->r.size,1.0,100.0, 0, 0, "Set render size to defined size");
	uiDefButS(block, ROW,B_DIFF,"75%",			565,88,40,20,&G.scene->r.size,1.0,75.0, 0, 0, "Set render size to 3/4 of defined size");
	uiDefButS(block, ROW,B_DIFF,"50%",			606,88,40,20,&G.scene->r.size,1.0,50.0, 0, 0, "Set render size to 1/2 of defined size");
	uiDefButS(block, ROW,B_DIFF,"25%",			647,88,40,20,&G.scene->r.size,1.0,25.0, 0, 0, "Set render size to 1/4 of defined size");
	uiBlockEndAlign(block);

	uiBlockBeginAlign(block);
	uiDefButBitI(block, TOG, R_FIELDS, 0,"Fields",  565,55,60,20,&G.scene->r.mode, 0, 0, 0, 0, "Enables field rendering");
	uiDefButBitI(block, TOG, R_ODDFIELD, 0,"Odd",	627,55,39,20,&G.scene->r.mode, 0, 0, 0, 0, "Enables Odd field first rendering (Default: Even field)");
	uiDefButBitI(block, TOG, R_FIELDSTILL, 0,"X",		668,55,19,20,&G.scene->r.mode, 0, 0, 0, 0, "Disables time difference in field calculations");
	
	sprintf(str, "Filter%%t|Box %%x%d|Tent %%x%d|Quad %%x%d|Cubic %%x%d|Gauss %%x%d|CatRom %%x%d|Mitch %%x%d", R_FILTER_BOX, R_FILTER_TENT, R_FILTER_QUAD, R_FILTER_CUBIC, R_FILTER_GAUSS, R_FILTER_CATROM, R_FILTER_MITCH);
	uiDefButS(block, MENU, B_DIFF,str,		565,34,60,20, &G.scene->r.filtertype, 0, 0, 0, 0, "Set sampling filter for antialiasing");
	uiDefButF(block, NUM,B_DIFF,"",			627,34,60,20,&G.scene->r.gauss,0.5, 1.5, 10, 2, "Sets the filter size");
	
	uiDefButBitI(block, TOG, R_BORDER, REDRAWVIEWCAM, "Border",	565,13,60,20, &G.scene->r.mode, 0, 0, 0, 0, "Render a small cut-out of the image");
	uiDefButBitI(block, TOG, R_GAMMA, B_REDR, "Gamma",	627,13,60,20, &G.scene->r.mode, 0, 0, 0, 0, "Enable gamma correction");
	uiBlockEndAlign(block);

}

static void render_panel_anim(void)
{
	uiBlock *block;


	block= uiNewBlock(&curarea->uiblocks, "render_panel_anim", UI_EMBOSS, UI_HELV, curarea->win);
	if(uiNewPanel(curarea, block, "Anim", "Render", 640, 0, 318, 204)==0) return;


	uiDefBut(block, BUT,B_DOANIM,"ANIM",		692,142,192,47, 0, 0, 0, 0, 0, "Start rendering a sequence");

	uiBlockSetCol(block, TH_BUT_SETTING1);
	uiBlockBeginAlign(block);
	uiDefButBitS(block, TOG, R_DOSEQ, B_NOP, "Do Sequence",692,114,192,20, &G.scene->r.scemode, 0, 0, 0, 0, "Enables sequence output rendering (Default: 3D rendering)");
	uiDefButBitS(block, TOG, R_DOCOMP, B_NOP, "Do Composite",692,90,192,20, &G.scene->r.scemode, 0, 0, 0, 0, "Uses compositing nodes for output rendering");
	uiBlockEndAlign(block);

	uiBlockSetCol(block, TH_AUTO);
	uiDefBut(block, BUT,B_PLAYANIM, "PLAY",692,40,94,33, 0, 0, 0, 0, 0, "Play animation of rendered images/avi (searches Pics: field)");
	uiDefButS(block, NUM, B_RTCHANGED, "rt:",789,40,95,33, &G.rt, -1000.0, 1000.0, 0, 0, "General testing/debug button");

	uiBlockBeginAlign(block);
	uiDefButI(block, NUM,REDRAWSEQ,"Sta:",692,10,94,24, &G.scene->r.sfra,1.0,MAXFRAMEF, 0, 0, "The start frame of the animation");
	uiDefButI(block, NUM,REDRAWSEQ,"End:",789,10,95,24, &G.scene->r.efra,1.0,MAXFRAMEF, 0, 0, "The end  frame of the animation");
	uiBlockEndAlign(block);
}

#ifdef WITH_FFMPEG
static void set_ffmpeg_preset(int preset)
{
	int isntsc = (G.scene->r.frs_sec != 25);
	switch (preset) {
	case FFMPEG_PRESET_VCD:
		G.scene->r.ffcodecdata.type = FFMPEG_MPEG1;
		G.scene->r.ffcodecdata.video_bitrate = 1150;
		G.scene->r.xsch = 352;
		G.scene->r.ysch = isntsc ? 240 : 288;
		G.scene->r.ffcodecdata.gop_size = isntsc ? 18 : 15;
		G.scene->r.ffcodecdata.rc_max_rate = 1150;
		G.scene->r.ffcodecdata.rc_min_rate = 1150;
		G.scene->r.ffcodecdata.rc_buffer_size = 40*8;
		G.scene->r.ffcodecdata.mux_packet_size = 2324;
		G.scene->r.ffcodecdata.mux_rate = 2352 * 75 * 8;
		break;
	case FFMPEG_PRESET_SVCD:
		G.scene->r.ffcodecdata.type = FFMPEG_MPEG2;
		G.scene->r.ffcodecdata.video_bitrate = 2040;
		G.scene->r.xsch = 480;
		G.scene->r.ysch = isntsc ? 480 : 576;
		G.scene->r.ffcodecdata.gop_size = isntsc ? 18 : 15;
		G.scene->r.ffcodecdata.rc_max_rate = 2516;
		G.scene->r.ffcodecdata.rc_min_rate = 0;
		G.scene->r.ffcodecdata.rc_buffer_size = 224*8;
		G.scene->r.ffcodecdata.mux_packet_size = 2324;
		G.scene->r.ffcodecdata.mux_rate = 0;
		
		break;
	case FFMPEG_PRESET_DVD:
		G.scene->r.ffcodecdata.type = FFMPEG_MPEG2;
		G.scene->r.ffcodecdata.video_bitrate = 6000;
		G.scene->r.xsch = 720;
		G.scene->r.ysch = isntsc ? 480 : 576;
		G.scene->r.ffcodecdata.gop_size = isntsc ? 18 : 15;
		G.scene->r.ffcodecdata.rc_max_rate = 9000;
		G.scene->r.ffcodecdata.rc_min_rate = 0;
		G.scene->r.ffcodecdata.rc_buffer_size = 224*8;
		G.scene->r.ffcodecdata.mux_packet_size = 2048;
		G.scene->r.ffcodecdata.mux_rate = 10080000;
		
		break;
	case FFMPEG_PRESET_DV:
		G.scene->r.ffcodecdata.type = FFMPEG_DV;
		G.scene->r.xsch = 720;
		G.scene->r.ysch = isntsc ? 480 : 576;
		break;
	}
}

static void render_panel_ffmpeg_video(void)
{
       int yofs;
       int xcol1;
       int xcol2;
       uiBlock *block;
       block = uiNewBlock(&curarea->uiblocks, "render_panel_ffmpeg_video", 
			  UI_EMBOSS, UI_HELV, curarea->win);
	   uiNewPanelTabbed("Format", "Render");
       if (uiNewPanel(curarea, block, "Video", "Render", 960, 0, 318, 204) 
	   == 0) return;

       if (ffmpeg_preset_sel != 0) {
	       set_ffmpeg_preset(ffmpeg_preset_sel);
	       ffmpeg_preset_sel = 0;
	       allqueue(REDRAWBUTSSCENE, 0);
       }

       xcol1 = 872;
       xcol2 = 1002;

       yofs = 54;
       uiDefBut(block, LABEL, B_DIFF, "Format", xcol1, yofs+88, 
		110, 20, 0, 0, 0, 0, 0, "");
       uiDefBut(block, LABEL, B_DIFF, "Preset", xcol2, yofs+88, 
		110, 20, 0, 0, 0, 0, 0, "");
       uiDefButI(block, MENU, B_DIFF, ffmpeg_format_pup(), 
		 xcol1, yofs+66, 110, 20, &G.scene->r.ffcodecdata.type, 
		 0,0,0,0, "output file format");
       uiDefButI(block, NUM, B_DIFF, "Bitrate", 
		 xcol1, yofs+44, 110, 20, 
		 &G.scene->r.ffcodecdata.video_bitrate, 
		 1, 14000, 0, 0, "Video bitrate(kb/s)");
       uiDefButI(block, NUM, B_DIFF, "Min Rate", 
		 xcol1, yofs+22, 110, 20, &G.scene->r.ffcodecdata.rc_min_rate, 
		 0, 14000, 0, 0, "Rate control: min rate(kb/s)");
       uiDefButI(block, NUM, B_DIFF, "Max Rate", 
		 xcol1, yofs, 110, 20, &G.scene->r.ffcodecdata.rc_max_rate, 
		 1, 14000, 0, 0, "Rate control: max rate(kb/s)");

       uiDefButI(block, NUM, B_DIFF, "Mux Rate", 
		 xcol1, yofs-22, 110, 20, 
		 &G.scene->r.ffcodecdata.mux_rate, 
		 0, 100000000, 0, 0, "Mux rate (bits/s(!))");


       uiDefButI(block, MENU, B_REDR, ffmpeg_preset_pup(), 
		 xcol2, yofs+66, 110, 20, &ffmpeg_preset_sel, 
		 0,0,0,0, "Output file format preset selection");
       uiDefButI(block, NUM, B_DIFF, "GOP Size", 
		 xcol2, yofs+44, 110, 20, &G.scene->r.ffcodecdata.gop_size, 
		 0, 100, 0, 0, "Distance between key frames");
       uiDefButI(block, NUM, B_DIFF, "Buffersize", 
		 xcol2, yofs+22, 110, 20,
		 &G.scene->r.ffcodecdata.rc_buffer_size, 
		 0, 2000, 0, 0, "Rate control: buffer size (kb)");
       uiDefButI(block, NUM, B_DIFF, "Mux PSize", 
		 xcol2, yofs, 110, 20, 
		 &G.scene->r.ffcodecdata.mux_packet_size, 
		 0, 16384, 0, 0, "Mux packet size (byte)");

       uiDefButBitI(block, TOG, FFMPEG_AUTOSPLIT_OUTPUT, B_NOP,
		    "Autosplit Output", 
		    xcol2, yofs-22, 110, 20, 
		    &G.scene->r.ffcodecdata.flags, 
		    0, 1, 0,0, "Autosplit output at 2GB boundary.");


       if (G.scene->r.ffcodecdata.type == FFMPEG_AVI 
	   || G.scene->r.ffcodecdata.type == FFMPEG_MOV) {
               uiDefBut(block, LABEL, 0, "Codec", 
			xcol1, yofs-44, 110, 20, 0, 0, 0, 0, 0, "");
               uiDefButI(block, MENU,B_REDR, ffmpeg_codec_pup(), 
			 xcol1, yofs-66, 110, 20, 
			 &G.scene->r.ffcodecdata.codec, 
			 0,0,0,0, "FFMpeg codec to use");
       }


}
static void render_panel_ffmpeg_audio(void)
{
       int yofs;
       int xcol;
       uiBlock *block;
       block = uiNewBlock(&curarea->uiblocks, "render_panel_ffmpeg_audio", UI_EMBOSS, UI_HELV, curarea->win);
	   uiNewPanelTabbed("Format", "Render");
       if (uiNewPanel(curarea, block, "Audio", "Render", 960, 0, 318, 204) 
	   == 0) return;
       yofs = 54;
       xcol = 892;

       uiDefButBitI(block, TOG, FFMPEG_MULTIPLEX_AUDIO, B_NOP,
		    "Multiplex audio", xcol, yofs, 225, 20, 
		    &G.scene->r.ffcodecdata.flags, 
		    0, 1, 0,0, "Interleave audio with the output video");
       uiDefBut(block, LABEL, 0, "Codec", 
		xcol, yofs-22, 225, 20, 0, 0, 0, 0, 0, "");
       uiDefButI(block, MENU,B_NOP, ffmpeg_audio_codec_pup(), 
		 xcol, yofs-44, 225, 20, 
		 &G.scene->r.ffcodecdata.audio_codec, 
		 0,0,0,0, "FFMpeg codec to use");
       uiDefButI(block, NUM, B_DIFF, "Bitrate", 
		 xcol, yofs-66, 110, 20, 
		 &G.scene->r.ffcodecdata.audio_bitrate, 
		 32, 384, 0, 0, "Audio bitrate(kb/s)");
}
#endif


static void render_panel_format(void)
{
	uiBlock *block;
	int yofs;


	block= uiNewBlock(&curarea->uiblocks, "render_panel_format", UI_EMBOSS, UI_HELV, curarea->win);
	if(uiNewPanel(curarea, block, "Format", "Render", 960, 0, 318, 204)==0) return;
	uiDefBlockBut(block, framing_render_menu, NULL, 
				  "Game framing settings", 
				  892, 169, 227, 20, "Display game framing settings");
	/* uiDefIconTextBlockBut(block, framing_render_menu, NULL, 
						   ICON_BLOCKBUT_CORNER, 
						   "Game framing settings", 
						   892, 169, 227, 20, 
						   "Display game framing settings"); */

	uiBlockBeginAlign(block);
	uiDefButS(block, NUM,REDRAWVIEWCAM,"SizeX:",	892 ,136,112,27, &G.scene->r.xsch, 4.0, 10000.0, 0, 0, "The image width in pixels");
	uiDefButS(block, NUM,REDRAWVIEWCAM,"SizeY:",	1007,136,112,27, &G.scene->r.ysch, 4.0,10000.0, 0, 0, "The image height in scanlines");
	uiDefButS(block, NUM,REDRAWVIEWCAM,"AspX:",	892 ,114,112,20, &G.scene->r.xasp, 1.0,200.0, 0, 0, "The horizontal aspect ratio");
	uiDefButS(block, NUM,REDRAWVIEWCAM,"AspY:",	1007,114,112,20, &G.scene->r.yasp, 1.0,200.0, 0, 0, "The vertical aspect ratio");
	uiBlockEndAlign(block);

	yofs = 54;

#ifdef __sgi
	yofs = 76;
	uiDefButS(block, NUM,B_DIFF,"MaxSize:",			892,32,165,20, &G.scene->r.maximsize, 0.0, 500.0, 0, 0, "Maximum size per frame to save in an SGI movie");
	uiDefButBitI(block, TOG, R_COSMO, 0,"Cosmo",	1059,32,60,20, &G.scene->r.mode, 0, 0, 0, 0, "Attempt to save SGI movies using Cosmo hardware");
#endif

	uiDefButS(block, MENU,B_FILETYPEMENU,imagetype_pup(),	892,yofs,174,20, &G.scene->r.imtype, 0, 0, 0, 0, "Images are saved in this file format");
	uiDefButBitI(block, TOG, R_CROP, B_DIFF, "Crop",        1068,yofs,51,20, &G.scene->r.mode, 0, 0, 0, 0, "When Border render, the resulting image gets cropped");

	yofs -= 22;

	if(G.scene->r.quality==0) G.scene->r.quality= 90;

#ifdef WITH_QUICKTIME
	if (G.scene->r.imtype == R_AVICODEC || G.scene->r.imtype == R_QUICKTIME) {
#else /* WITH_QUICKTIME */
	if (0) {
#endif
		if(G.scene->r.imtype == R_QUICKTIME) {
#ifdef WITH_QUICKTIME
#if defined (_WIN32) || defined (__APPLE__)
			//glColor3f(0.65, 0.65, 0.7);
			//glRecti(892,yofs+46,892+225,yofs+45+20);
			if(G.scene->r.qtcodecdata == NULL)
				uiDefBut(block, LABEL, 0, "Codec: not set",  892,yofs+44,225,20, 0, 0, 0, 0, 0, "");
			else
				uiDefBut(block, LABEL, 0, G.scene->r.qtcodecdata->qtcodecname,  892,yofs+44,225,20, 0, 0, 0, 0, 0, "");
			uiDefBut(block, BUT,B_SELECTCODEC, "Set codec",  892,yofs,112,20, 0, 0, 0, 0, 0, "Set codec settings for Quicktime");
#endif
#endif /* WITH_QUICKTIME */
		} else {
#ifdef _WIN32
			//glColor3f(0.65, 0.65, 0.7);
			//glRecti(892,yofs+46,892+225,yofs+45+20);
			if(G.scene->r.avicodecdata == NULL)
				uiDefBut(block, LABEL, 0, "Codec: not set.",  892,yofs+43,225,20, 0, 0, 0, 0, 0, "");
			else
				uiDefBut(block, LABEL, 0, avicodec_str(),  892,yofs+43,225,20, 0, 0, 0, 0, 0, "");
#endif
			uiDefBut(block, BUT,B_SELECTCODEC, "Set codec",  892,yofs,112,20, 0, 0, 0, 0, 0, "Set codec settings for AVI");
		}
#ifdef WITH_OPENEXR
	} 
	else if (G.scene->r.imtype == R_OPENEXR ) {
		if (G.scene->r.quality > 5) G.scene->r.quality = 0;
		
		uiBlockBeginAlign(block);
		uiDefButBitS(block, TOG, R_OPENEXR_HALF, B_NOP,"Half",	892,yofs+44,60,20, &G.scene->r.subimtype, 0, 0, 0, 0, "Use 16 bits float 'Half' type");
		uiDefButBitS(block, TOG, R_OPENEXR_ZBUF, B_NOP,"Zbuf",	952,yofs+44,60,20, &G.scene->r.subimtype, 0, 0, 0, 0, "Save the zbuffer as 32 bits unsigned int");
		uiBlockEndAlign(block);
		uiDefButBitS(block, TOG, R_PREVIEW_JPG, B_NOP,"Preview",1027,yofs+44,90,20, &G.scene->r.subimtype, 0, 0, 0, 0, "When animation render, save JPG preview images in same directory");
		
		uiDefButS(block, MENU,B_NOP, "Codec %t|None %x0|Pxr24 (lossy) %x1|ZIP (lossless) %x2|PIZ (lossless) %x3|RLE (lossless) %x4",  
															892,yofs,112,20, &G.scene->r.quality, 0, 0, 0, 0, "Set codec settings for OpenEXR");
		
#endif
	} else {
		if(G.scene->r.quality < 5) G.scene->r.quality = 90;	/* restore from openexr */
		
		uiDefButS(block, NUM,B_DIFF, "Quality:",           892,yofs,112,20, &G.scene->r.quality, 10.0, 100.0, 0, 0, "Quality setting for JPEG images, AVI Jpeg and SGI movies");
	}
	uiDefButS(block, NUM,B_FRAMEMAP,"Frs/sec:",   1006,yofs,113,20, &G.scene->r.frs_sec, 1.0, 120.0, 100.0, 0, "Frames per second");


	uiBlockBeginAlign(block);
	uiDefButS(block, ROW,B_DIFF,"BW",			892, 10,74,19, &G.scene->r.planes, 5.0,(float)R_PLANESBW, 0, 0, "Images are saved with BW (grayscale) data");
	uiDefButS(block, ROW,B_DIFF,"RGB",		    968, 10,74,19, &G.scene->r.planes, 5.0,(float)R_PLANES24, 0, 0, "Images are saved with RGB (color) data");
	uiDefButS(block, ROW,B_DIFF,"RGBA",		   1044, 10,75,19, &G.scene->r.planes, 5.0,(float)R_PLANES32, 0, 0, "Images are saved with RGB and Alpha data (if supported)");

	uiBlockBeginAlign(block);
	uiDefBut(block, BUT,B_PR_PAL, "PAL",		1146,170,100,18, 0, 0, 0, 0, 0, "Size preset: Image size - 720x576, Aspect ratio - 54x51, 25 fps");
	uiDefBut(block, BUT,B_PR_NTSC, "NTSC",		1146,150,100,18, 0, 0, 0, 0, 0, "Size preset: Image size - 720x480, Aspect ratio - 10x11, 30 fps");
	uiDefBut(block, BUT,B_PR_PRESET, "Default",	1146,130,100,18, 0, 0, 0, 0, 0, "Same as PAL, with render settings (OSA, Shadows, Fields)");
	uiDefBut(block, BUT,B_PR_PRV, "Preview",	1146,110,100,18, 0, 0, 0, 0, 0, "Size preset: Image size - 640x512, Render size 50%");
	uiDefBut(block, BUT,B_PR_PC, "PC",			1146,90,100,18, 0, 0, 0, 0, 0, "Size preset: Image size - 640x480, Aspect ratio - 100x100");
	uiDefBut(block, BUT,B_PR_PAL169, "PAL 16:9",1146,70,100,18, 0, 0, 0, 0, 0, "Size preset: Image size - 720x576, Aspect ratio - 64x45");
	uiDefBut(block, BUT,B_PR_PANO, "PANO",		1146,50,100,18, 0, 0, 0, 0, 0, "Standard panorama settings");
	uiDefBut(block, BUT,B_PR_FULL, "FULL",		1146,30,100,18, 0, 0, 0, 0, 0, "Size preset: Image size - 1280x1024, Aspect ratio - 1x1");
	uiDefBut(block, BUT,B_PR_HD, "HD",		1146,10,100,18, 0, 0, 0, 0, 0, "Size preset: Image size - 1920x1080, Aspect ratio - 1x1");
	uiBlockEndAlign(block);
}


/* yafray: global illumination options panel */
static void render_panel_yafrayGI()
{
	uiBlock *block;

	block= uiNewBlock(&curarea->uiblocks, "render_panel_yafrayGI", UI_EMBOSS, UI_HELV, curarea->win);
	uiNewPanelTabbed("Render", "Render");
	if(uiNewPanel(curarea, block, "YafRay GI", "Render", 320, 0, 318, 204)==0) return;

	// label to force a boundbox for buttons not to be centered
	uiDefBut(block, LABEL, 0, " ", 305,180,10,10, 0, 0, 0, 0, 0, "");

	uiDefBut(block, LABEL, 0, "Method", 5,175,70,20, 0, 1.0, 0, 0, 0, "");
	uiDefButS(block, MENU, B_REDR, "GiMethod %t|None %x0|SkyDome %x1|Full %x2", 70,175,89,20, &G.scene->r.GImethod, 0, 0, 0, 0, "Global Illumination Method");

	uiDefBut(block, LABEL, 0, "Quality", 5,150,70,20, 0, 1.0, 0, 0, 0, "");
	uiDefButS(block, MENU, B_REDR, "GiQuality %t|None %x0|Low %x1|Medium %x2 |High %x3|Higher %x4|Best %x5|Use Blender AO settings %x6", 70,150,89,20, &G.scene->r.GIquality, 0, 0, 0, 0, "Global Illumination Quality");

	if (G.scene->r.GImethod>0) {
		uiDefButF(block, NUM, B_DIFF, "EmitPwr:", 5,35,154,20, &G.scene->r.GIpower, 0.01, 100.0, 10, 0, "arealight, material emit and background intensity scaling, 1 is normal");
		if (G.scene->r.GImethod==2) uiDefButF(block, NUM, B_DIFF, "GI Pwr:", 5,10,154,20, &G.scene->r.GIindirpower, 0.01, 100.0, 10, 0, "GI indirect lighting intensity scaling, 1 is normal");
	}

	if (G.scene->r.GImethod>0)
	{
		if (G.scene->r.GIdepth==0) G.scene->r.GIdepth=2;

		if (G.scene->r.GImethod==2) {
			uiDefButI(block, NUM, B_DIFF, "Depth:", 180,175,110,20, &G.scene->r.GIdepth, 1.0, 100.0, 10, 10, "Number of bounces of the indirect light");
			uiDefButI(block, NUM, B_DIFF, "CDepth:", 180,150,110,20, &G.scene->r.GIcausdepth, 1.0, 100.0, 10, 10, "Number of bounces inside objects (for caustics)");
			uiDefButBitS(block, TOG, 1,  B_REDR, "Photons",210,125,100,20, &G.scene->r.GIphotons, 0, 0, 0, 0, "Use global photons to help in GI");
		}

		uiDefButBitS(block, TOG, 1, B_REDR, "Cache",6,125,95,20, &G.scene->r.GIcache, 0, 0, 0, 0, "Cache occlusion/irradiance samples (faster)");
		if (G.scene->r.GIcache) 
		{
			uiDefButBitS(block,TOG, 1, B_REDR, "NoBump",108,125,95,20, &G.scene->r.YF_nobump, 0, 0, 0, 0, "Don't use bumpnormals for cache (faster, but no bumpmapping in total indirectly lit areas)");
			uiDefBut(block, LABEL, 0, "Cache parameters:", 5,105,130,20, 0, 1.0, 0, 0, 0, "");
			if (G.scene->r.GIshadowquality==0.0) G.scene->r.GIshadowquality=0.9;
			uiDefButF(block, NUM, B_DIFF,"ShadQu:", 5,85,154,20,	&(G.scene->r.GIshadowquality), 0.01, 1.0 ,1,0, "Sets the shadow quality, keep it under 0.95 :-) ");
			if (G.scene->r.GIpixelspersample==0) G.scene->r.GIpixelspersample=10;
			uiDefButI(block, NUM, B_DIFF, "Prec:",	5,60,75,20, &G.scene->r.GIpixelspersample, 1, 50, 10, 10, "Maximum number of pixels without samples, the lower the better and slower");
			if (G.scene->r.GIrefinement==0) G.scene->r.GIrefinement=1.0;
			uiDefButF(block, NUM, B_DIFF, "Ref:", 84,60,75,20, &G.scene->r.GIrefinement, 0.001, 1.0, 1, 0, "Threshold to refine shadows EXPERIMENTAL. 1 = no refinement");
		}

		if (G.scene->r.GImethod==2) {
			if (G.scene->r.GIphotons)
			{
				uiDefBut(block, LABEL, 0, "Photon parameters:", 170,105,130,20, 0, 1.0, 0, 0, 0, "");
				if(G.scene->r.GIphotoncount==0) G.scene->r.GIphotoncount=100000;
				uiDefButI(block, NUM, B_DIFF, "Count:", 170,85,140,20, &G.scene->r.GIphotoncount, 
						0, 10000000, 10, 10, "Number of photons to shoot");
				if(G.scene->r.GIphotonradius==0.0) G.scene->r.GIphotonradius=1.0;
				uiDefButF(block, NUMSLI, B_DIFF,"Radius:", 170,60,140,20,	&(G.scene->r.GIphotonradius), 
						0.00001, 100.0 ,0,0, "Radius to search for photons to mix (blur)");
				if(G.scene->r.GImixphotons==0) G.scene->r.GImixphotons=100;
				uiDefButI(block, NUM, B_DIFF, "MixCount:", 170,35,140,20, &G.scene->r.GImixphotons, 
						0, 1000, 10, 10, "Number of photons to mix");
				uiDefButBitS(block, TOG, 1, B_REDR, "Tune Photons",170,10,140,20, &G.scene->r.GIdirect, 
						0, 0, 0, 0, "Show the photonmap directly in the render for tuning");
			}
		}

	}
}

/* yafray: global  options panel */
static void render_panel_yafrayGlobal()
{
	uiBlock *block;

	block= uiNewBlock(&curarea->uiblocks, "render_panel_yafrayGlobal", UI_EMBOSS, UI_HELV, curarea->win);
	uiNewPanelTabbed("Render", "Render");
	if(uiNewPanel(curarea, block, "YafRay", "Render", 320, 0, 318, 204)==0) return;

	// label to force a boundbox for buttons not to be centered
	uiDefBut(block, LABEL, 0, " ", 305,180,10,10, 0, 0, 0, 0, 0, "");

	uiDefButBitS(block, TOGN, 1, B_REDR, "xml", 5,180,75,20, &G.scene->r.YFexportxml,
					0, 0, 0, 0, "Export to an xml file and call yafray instead of plugin");

	uiDefButF(block, NUMSLI, B_DIFF,"Bi ", 5,35,150,20,	&(G.scene->r.YF_raybias), 
				0.0, 10.0 ,0,0, "Shadow ray bias to avoid self shadowing");
	uiDefButI(block, NUM, B_DIFF, "Raydepth ", 5,60,150,20,
				&G.scene->r.YF_raydepth, 1.0, 80.0, 10, 10, "Maximum render ray depth from the camera");
	uiDefButF(block, NUMSLI, B_DIFF, "Gam ", 5,10,150,20, &G.scene->r.YF_gamma, 0.001, 5.0, 0, 0, "Gamma correction, 1 is off");
	uiDefButF(block, NUMSLI, B_DIFF, "Exp ", 160,10,150,20,&G.scene->r.YF_exposure, 0.0, 10.0, 0, 0, "Exposure adjustment, 0 is off");
        
	uiDefButI(block, NUM, B_DIFF, "Processors:", 160,60,150,20, &G.scene->r.YF_numprocs, 1.0, 8.0, 10, 10, "Number of processors to use");

	/*AA Settings*/
	uiDefButBitS(block, TOGN, 1, B_REDR, "Auto AA", 5,140,150,20, &G.scene->r.YF_AA, 
					0, 0, 0, 0, "Set AA using OSA and GI quality, disable for manual control");
	uiDefButBitS(block, TOGN, 1, B_DIFF, "Clamp RGB", 160,140,150,20, &G.scene->r.YF_clamprgb, 1.0, 8.0, 10, 10, "For AA on fast high contrast changes. Not advisable for Bokeh! Dulls lens shape detail.");
 	if(G.scene->r.YF_AA){
		uiDefButI(block, NUM, B_DIFF, "AA Passes ", 5,115,150,20, &G.scene->r.YF_AApasses, 0, 64, 10, 10, "Number of AA passes (0 is no AA)");
		uiDefButI(block, NUM, B_DIFF, "AA Samples ", 160,115,150,20, &G.scene->r.YF_AAsamples, 0, 2048, 10, 10, "Number of samples per pass");
		uiDefButF(block, NUMSLI, B_DIFF, "Psz ", 5,90,150,20, &G.scene->r.YF_AApixelsize, 1.0, 2.0, 0, 0, "AA pixel filter size");
		uiDefButF(block, NUMSLI, B_DIFF, "Thr ", 160,90,150,20, &G.scene->r.YF_AAthreshold, 0.000001, 1.0, 0, 0, "AA threshold");
	}
}


static void layer_copy_func(void *lay_v, void *lay_p)
{
	unsigned int *lay= lay_p;
	int laybit= (int)lay_v;

	if(G.qual & LR_SHIFTKEY) {
		if(*lay==0) *lay= 1<<laybit;
	}
	else
		*lay= 1<<laybit;
	
	copy_view3d_lock(REDRAW);
	allqueue(REDRAWBUTSSCENE, 0);
}

static void delete_scene_layer_func(void *srl_v, void *act_i)
{
	if(BLI_countlist(&G.scene->r.layers)>1) {
		long act= (long)act_i;
		
		BLI_remlink(&G.scene->r.layers, srl_v);
		MEM_freeN(srl_v);
		G.scene->r.actlay= 0;
		
		if(G.scene->nodetree) {
			bNode *node;
			for(node= G.scene->nodetree->nodes.first; node; node= node->next) {
				if(node->type==CMP_NODE_R_LAYERS && node->id==NULL) {
					if(node->custom1==act)
						node->custom1= 0;
					else if(node->custom1>act)
						node->custom1--;
				}
			}
		}
		allqueue(REDRAWBUTSSCENE, 0);
		allqueue(REDRAWNODE, 0);
	}
}

static void rename_scene_layer_func(void *srl_v, void *unused_v)
{
	if(G.scene->nodetree) {
		SceneRenderLayer *srl= srl_v;
		bNode *node;
		for(node= G.scene->nodetree->nodes.first; node; node= node->next) {
			if(node->type==CMP_NODE_R_LAYERS && node->id==NULL) {
				if(node->custom1==G.scene->r.actlay)
					BLI_strncpy(node->name, srl->name, NODE_MAXSTR);
			}
		}
	}
	allqueue(REDRAWBUTSSCENE, 0);
	allqueue(REDRAWNODE, 0);
}

static char *scene_layer_menu(void)
{
	SceneRenderLayer *srl;
	int len= 32 + 32*BLI_countlist(&G.scene->r.layers);
	short a, nr;
	char *str= MEM_callocN(len, "menu layers");
	
	strcpy(str, "ADD NEW %x32767");
	a= strlen(str);
	for(nr=0, srl= G.scene->r.layers.first; srl; srl= srl->next, nr++) {
		a+= sprintf(str+a, "|%s %%x%d", srl->name, nr);
	}
	
	return str;
}

static void draw_3d_layer_buttons(uiBlock *block, unsigned int *poin, short xco, short yco, short dx, short dy)
{
	uiBut *bt;
	long a;
	
	uiBlockBeginAlign(block);
	for(a=0; a<5; a++) {
		bt= uiDefButBitI(block, TOG, 1<<a, B_NOP, "",	(short)(xco+a*(dx/2)), yco+dy/2, (short)(dx/2), (short)(dy/2), poin, 0, 0, 0, 0, "");
		uiButSetFunc(bt, layer_copy_func, (void *)a, poin);
	}
	for(a=0; a<5; a++) {
		bt=uiDefButBitI(block, TOG, 1<<(a+10), B_NOP, "",	(short)(xco+a*(dx/2)), yco, (short)(dx/2), (short)(dy/2), poin, 0, 0, 0, 0, "");
		uiButSetFunc(bt, layer_copy_func, (void *)(a+10), poin);
	}
	
	xco+= 7;
	uiBlockBeginAlign(block);
	for(a=5; a<10; a++) {
		bt=uiDefButBitI(block, TOG, 1<<a, B_NOP, "",	(short)(xco+a*(dx/2)), yco+dy/2, (short)(dx/2), (short)(dy/2), poin, 0, 0, 0, 0, "");
		uiButSetFunc(bt, layer_copy_func, (void *)a, poin);
	}
	for(a=5; a<10; a++) {
		bt=uiDefButBitI(block, TOG, 1<<(a+10), B_NOP, "",	(short)(xco+a*(dx/2)), yco, (short)(dx/2), (short)(dy/2), poin, 0, 0, 0, 0, "");
		uiButSetFunc(bt, layer_copy_func, (void *)(a+10), poin);
	}
	
	uiBlockEndAlign(block);
}

static void render_panel_layers(void)
{
	uiBlock *block;
	uiBut *bt;
	SceneRenderLayer *srl= BLI_findlink(&G.scene->r.layers, G.scene->r.actlay);
	char *strp;
	
	if(srl==NULL) {
		G.scene->r.actlay= 0;
		srl= G.scene->r.layers.first;
	}
	
	block= uiNewBlock(&curarea->uiblocks, "render_panel_layers", UI_EMBOSS, UI_HELV, curarea->win);
	uiNewPanelTabbed("Output", "Render");
	if(uiNewPanel(curarea, block, "Render Layers", "Render", 320, 0, 318, 204)==0) return;
	
	/* first, as reminder, the scene layers */
	uiDefBut(block, LABEL, 0, "Scene:",				10,170,100,20, NULL, 0, 0, 0, 0, "");
	
	draw_3d_layer_buttons(block, &G.scene->lay, 130, 170, 35, 30);
	
	/* layer menu, name, delete button */
	uiBlockBeginAlign(block);
	strp= scene_layer_menu();
	uiDefButS(block, MENU, B_ADD_RENDERLAYER, strp, 10,130,23,20, &(G.scene->r.actlay), 0, 0, 0, 0, "Choose Active Render Layer");
	MEM_freeN(strp);
	
	bt= uiDefBut(block, TEX, REDRAWNODE, "",  33,130,192,20, srl->name, 0.0, 31.0, 0, 0, "");
	uiButSetFunc(bt, rename_scene_layer_func, srl, NULL);
	
	uiDefButBitS(block, TOG, R_SINGLE_LAYER, B_NOP, "Single",	230,130,60,20, &G.scene->r.scemode, 0, 0, 0, 0, "Only render this layer");	
	bt=uiDefIconBut(block, BUT, B_NOP, ICON_X,	285, 130, 25, 20, 0, 0, 0, 0, 0, "Deletes current Render Layer");
	uiButSetFunc(bt, delete_scene_layer_func, srl, (void *)(long)G.scene->r.actlay);
	uiBlockEndAlign(block);

	/* RenderLayer visible-layers */
	uiDefBut(block, LABEL, 0, "Layer:",	10,95,100,20, NULL, 0, 0, 0, 0, "");
	draw_3d_layer_buttons(block, &srl->lay,		130, 95, 35, 30);
	
	uiBlockBeginAlign(block);
	uiDefButBitS(block, TOG, SCE_LAY_SKY, B_NOP,"Sky",		10, 70, 40, 20, &srl->layflag, 0, 0, 0, 0, "Render Sky or backbuffer in this Layer");	
	uiDefButBitS(block, TOG, SCE_LAY_SOLID, B_NOP,"Solid",	50, 70, 65, 20, &srl->layflag, 0, 0, 0, 0, "Render Solid faces in this Layer");	
	uiDefButBitS(block, TOG, SCE_LAY_HALO, B_NOP,"Halo",	115, 70, 65, 20, &srl->layflag, 0, 0, 0, 0, "Render Halos in this Layer (on top of Solid)");	
	uiDefButBitS(block, TOG, SCE_LAY_ZTRA, B_NOP,"Ztra",	180, 70, 65, 20, &srl->layflag, 0, 0, 0, 0, "Render Z-Transparent faces in this Layer (On top of Solid and Halos)");	
	uiDefButBitS(block, TOG, SCE_LAY_EDGE, B_NOP,"Edge",	245, 70, 65, 20, &srl->layflag, 0, 0, 0, 0, "Render Edge-enhance in this Layer (only works for Solid faces)");	
	uiDefButBitS(block, TOG, SCE_LAY_ALL_Z, B_NOP,"All Z values",		10, 50, 105, 20, &srl->layflag, 0, 0, 0, 0, "Fill in Z values for all not-rendered faces, for masking");	
	uiBlockEndAlign(block);

	uiDefBut(block, LABEL, 0, "Passes:",					10,30,150,20, NULL, 0, 0, 0, 0, "");
	
	uiBlockBeginAlign(block);
	uiDefButBitS(block, TOG, SCE_PASS_COMBINED, B_NOP,"Combined",	10, 10, 150, 20, &srl->passflag, 0, 0, 0, 0, "Deliver full combined RGBA buffer");	
	uiDefButBitS(block, TOG, SCE_PASS_Z, B_NOP,"Z",			160, 10, 40, 20, &srl->passflag, 0, 0, 0, 0, "Deliver Z values pass");	
	uiDefButBitS(block, TOG, SCE_PASS_VECTOR, B_NOP,"Vec",	200, 10, 55, 20, &srl->passflag, 0, 0, 0, 0, "Deliver Vector pass");	
	uiDefButBitS(block, TOG, SCE_PASS_NORMAL, B_NOP,"Nor",	255, 10, 55, 20, &srl->passflag, 0, 0, 0, 0, "Deliver Normal pass");	
#if 0
	/* bring back after release */
	uiBlockBeginAlign(block);
	uiDefButBitS(block, TOG, SCE_PASS_COMBINED, B_NOP,"Combined",	130, 30, 115, 20, &srl->passflag, 0, 0, 0, 0, "Deliver full combined RGBA buffer");	
	uiDefButBitS(block, TOG, SCE_PASS_Z, B_NOP,"Z",			245, 30, 25, 20, &srl->passflag, 0, 0, 0, 0, "Deliver Z values pass");	
	uiDefButBitS(block, TOG, SCE_PASS_VECTOR, B_NOP,"Vec",	270, 30, 40, 20, &srl->passflag, 0, 0, 0, 0, "Deliver Vector pass");	
	
	uiDefButBitS(block, TOG, SCE_PASS_RGBA, B_NOP,"Col",	10, 10, 45, 20, &srl->passflag, 0, 0, 0, 0, "Deliver shade-less Color pass");	
	uiDefButBitS(block, TOG, SCE_PASS_DIFFUSE, B_NOP,"Diff",55, 10, 45, 20, &srl->passflag, 0, 0, 0, 0, "Deliver Diffuse pass");	
	uiDefButBitS(block, TOG, SCE_PASS_SPEC, B_NOP,"Spec",	100, 10, 45, 20, &srl->passflag, 0, 0, 0, 0, "Deliver Specular pass");	
	uiDefButBitS(block, TOG, SCE_PASS_SHADOW, B_NOP,"Shad",	145, 10, 45, 20, &srl->passflag, 0, 0, 0, 0, "Deliver Shadow pass");	
	uiDefButBitS(block, TOG, SCE_PASS_AO, B_NOP,"AO",		185, 10, 40, 20, &srl->passflag, 0, 0, 0, 0, "Deliver AO pass");	
	uiDefButBitS(block, TOG, SCE_PASS_RAY, B_NOP,"Ray",	225, 10, 45, 20, &srl->passflag, 0, 0, 0, 0, "Deliver Raytraced Mirror and Transparent pass");	
	uiDefButBitS(block, TOG, SCE_PASS_NORMAL, B_NOP,"Nor",	270, 10, 40, 20, &srl->passflag, 0, 0, 0, 0, "Deliver Normal pass");	
#endif
}	

void render_panels()
{

	render_panel_output();
//	render_panel_sfx();
	render_panel_layers();
	render_panel_render();
	render_panel_anim();

	render_panel_format();
#ifdef WITH_FFMPEG
       if (G.scene->r.imtype == R_FFMPEG) {
		   render_panel_ffmpeg_video();
	       render_panel_ffmpeg_audio();
       }
#endif

#ifndef DISABLE_YAFRAY
	/* yafray: GI & Global panel, only available when yafray enabled for rendering */
	if (G.scene->r.renderer==R_YAFRAY) {
		if (G.scene->r.YF_gamma==0.0) G.scene->r.YF_gamma=1.0;
		if (G.scene->r.YF_raybias==0.0) G.scene->r.YF_raybias=0.001;
		if (G.scene->r.YF_raydepth==0) G.scene->r.YF_raydepth=5;
		if (G.scene->r.YF_AApixelsize==0.0) G.scene->r.YF_AApixelsize=1.5;
		if (G.scene->r.YF_AAthreshold==0.0) G.scene->r.YF_AAthreshold=0.05;
		if (G.scene->r.GIpower==0.0) G.scene->r.GIpower=1.0;
		if (G.scene->r.GIindirpower==0.0) G.scene->r.GIindirpower=1.0;
		render_panel_yafrayGlobal();
		render_panel_yafrayGI();
	}
#endif

}

/* --------------------------------------------- */

void anim_panels()
{
	uiBlock *block;

	block= uiNewBlock(&curarea->uiblocks, "anim_panel", UI_EMBOSS, UI_HELV, curarea->win);
	if(uiNewPanel(curarea, block, "Anim", "Anim", 0, 0, 318, 204)==0) return;

	uiBlockBeginAlign(block);
	uiDefButI(block, NUM,B_FRAMEMAP,"Map Old:",	10,160,150,20,&G.scene->r.framapto,1.0,900.0, 0, 0, "Specify old mapping value in frames");
	uiDefButI(block, NUM,B_FRAMEMAP,"Map New:",	160,160,150,20,&G.scene->r.images,1.0,900.0, 0, 0, "Specify how many frames the Map Old will last");

	uiBlockBeginAlign(block);
	uiDefButS(block, NUM,B_FRAMEMAP,"Frs/sec:",  10,130,150,20, &G.scene->r.frs_sec, 1.0, 120.0, 100.0, 0, "Frames per second");
	uiDefButBitS(block, TOG, AUDIO_SYNC, B_SOUND_CHANGED, "Sync",160,130,150,20, &G.scene->audio.flag, 0, 0, 0, 0, "Use sample clock for syncing animation to audio");
	
	uiBlockBeginAlign(block);
	uiDefButI(block, NUM,REDRAWALL,"Sta:",	10,100,150,20,&G.scene->r.sfra,1.0,MAXFRAMEF, 0, 0, "Specify the start frame of the animation");
	uiDefButI(block, NUM,REDRAWALL,"End:",	160,100,150,20,&G.scene->r.efra,1.0,MAXFRAMEF, 0, 0, "Specify the end frame of the animation");

	uiBlockBeginAlign(block);
	uiDefButS(block, NUM, REDRAWTIME, "Steps:",10, 70, 150, 20,&(G.scene->jumpframe), 1, 100, 1, 100, "Set spacing between frames changes with up and down arrow keys");


}

/* --------------------------------------------- */

void sound_panels()
{
	bSound *sound;

	/* paranoia check */
	sound = G.buts->lockpoin;
	if(sound && GS(sound->id.name)!=ID_SO) {
		sound= NULL;
		G.buts->lockpoin= NULL;
	}
	
	sound_panel_sound(sound);
	sound_panel_listener();
	sound_panel_sequencer();
}



