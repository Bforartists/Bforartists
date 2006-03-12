/*
 * ffmpeg-write support
 *
 * Partial Copyright (c) 2006 Peter Schlaile
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 */


#ifdef WITH_FFMPEG
#include <string.h>
#include <stdio.h>

#include <stdint.h>
#include <stdlib.h>
#include <ffmpeg/avformat.h>
#include <ffmpeg/avcodec.h>
#include <ffmpeg/rational.h>

#if LIBAVFORMAT_VERSION_INT < (49 << 16)
#define FFMPEG_OLD_FRAME_RATE 1
#else
#define FFMPEG_CODEC_IS_POINTER 1
#define FFMPEG_CODEC_TIME_BASE  1
#endif

#include "BKE_writeffmpeg.h"

#include "MEM_guardedalloc.h"
#include "BLI_blenlib.h"

#include "BKE_bad_level_calls.h"
#include "BKE_global.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "BSE_seqaudio.h"

#include "DNA_scene_types.h"
#include "blendef.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

extern void makewavstring (char *string);
extern void do_init_ffmpeg();

static int ffmpeg_type = 0;
static int ffmpeg_codec = CODEC_ID_MPEG4;
static int ffmpeg_audio_codec = CODEC_ID_MP2;
static int ffmpeg_video_bitrate = 1150;
static int ffmpeg_audio_bitrate = 128;
static int ffmpeg_gop_size = 12;
static int ffmpeg_multiplex_audio = 1;
static int ffmpeg_autosplit = 0;
static int ffmpeg_autosplit_count = 0;

static AVFormatContext* outfile;
static AVStream* video_stream;
static AVStream* audio_stream;
static AVFrame* current_frame;

static uint8_t* video_buffer = 0;
static int video_buffersize = 0;

static uint8_t* audio_input_buffer = 0;
static int audio_input_frame_size = 0;
static uint8_t* audio_output_buffer = 0;
static int audio_outbuf_size = 0;

static RenderData *ffmpeg_renderdata;

#define FFMPEG_AUTOSPLIT_SIZE 2000000000

/* Delete a picture buffer */

void delete_picture(AVFrame* f)
{
	if (f) {
		if (f->data[0]) MEM_freeN(f->data[0]);
		av_free(f);
	}
}

#ifdef FFMPEG_CODEC_IS_POINTER
static AVCodecContext* get_codec_from_stream(AVStream* stream)
{
	return stream->codec;
}
#else
static AVCodecContext* get_codec_from_stream(AVStream* stream)
{
	return &stream->codec;
}
#endif

int write_audio_frame(void) {
	AVCodecContext* c = NULL;
	AVPacket pkt;

	c = get_codec_from_stream(audio_stream);

	audiostream_fill(audio_input_buffer, 
			 audio_input_frame_size 
			 * sizeof(short) * c->channels);

	av_init_packet(&pkt);

	pkt.size = avcodec_encode_audio(c, audio_output_buffer,
					audio_outbuf_size, 
					(short*) audio_input_buffer);
	pkt.data = audio_output_buffer;
#ifdef FFMPEG_CODEC_TIME_BASE
	pkt.pts = av_rescale_q(c->coded_frame->pts, 
			       c->time_base, audio_stream->time_base);
#else
	pkt.pts = c->coded_frame->pts;
#endif
	pkt.stream_index = audio_stream->index;
	pkt.flags |= PKT_FLAG_KEY;
	if (av_write_frame(outfile, &pkt) != 0) {
		error("Error writing audio packet");
		return -1;
	}
	return 0;
}

/* Allocate a temporary frame */

AVFrame* alloc_picture(int pix_fmt, int width, int height) 
{
	AVFrame* f;
	uint8_t* buf;
	int size;
	
	/* allocate space for the struct */
	f = avcodec_alloc_frame();
	if (!f) return NULL;
	size = avpicture_get_size(pix_fmt, width, height);
	/* allocate the actual picture buffer */
	buf = MEM_mallocN(size, "AVFrame buffer");
	if (!buf) {
		free(f);
		return NULL;
	}
	avpicture_fill((AVPicture*)f, buf, pix_fmt, width, height);
	return f;
}

/* Get an output format based on the menu selection */
AVOutputFormat* ffmpeg_get_format(int format) 
{
	AVOutputFormat* f;
	switch(format) {
		case FFMPEG_DV:
			f = guess_format("dv", NULL, NULL);
			break;
		case FFMPEG_MPEG1:
			f = guess_format("mpeg", NULL, NULL);
			break;
		case FFMPEG_MPEG2:
			f = guess_format("dvd", NULL, NULL);
			break;
		case FFMPEG_MPEG4:
			f = guess_format("mp4", NULL, NULL);
			break;
		case FFMPEG_AVI:
			f = guess_format("avi", NULL, NULL);
			break;
		case FFMPEG_MOV:
			f = guess_format("mov", NULL, NULL);
			break;
		default:
			f = NULL;
	}
	return f;
}

/* Get the correct file extension for the requested format */
void file_extension(int format, char* string) 
{
	int i;
	AVOutputFormat* f;
	const char* ext;
	f= ffmpeg_get_format(format);
	ext = f->extensions;
	for (i = 0; ext[i] != ',' && i < strlen(ext); i++);
	snprintf(string, i+2, ".%s", ext);
}

/* Get the output filename-- similar to the other output formats */
void makeffmpegstring(char* string) {
	
	char txt[FILE_MAXDIR+FILE_MAXFILE];
	char fe[FILE_MAXDIR+FILE_MAXFILE];
	char autosplit[20];

	file_extension(ffmpeg_type, fe);

	if (!string) return;

	strcpy(string, G.scene->r.pic);
	BLI_convertstringcode(string, G.sce, G.scene->r.cfra);

	BLI_make_existing_file(string);

	autosplit[0] = 0;

	if (ffmpeg_autosplit) {
		sprintf(autosplit, "_%03d", ffmpeg_autosplit_count);
	}

	if (BLI_strcasecmp(string + strlen(string) - strlen(fe), fe)) {
		strcat(string, autosplit);
		sprintf(txt, "%04d_%04d%s", (G.scene->r.sfra), 
			(G.scene->r.efra), fe);
		strcat(string, txt);
	} else {
		*(string + strlen(string) - strlen(fe)) = 0;
		strcat(string, autosplit);
		strcat(string, fe);
	}
}

/* Write a frame to the output file */
static void write_video_frame(AVFrame* frame) {
	int outsize = 0;
	int ret;
	AVCodecContext* c = get_codec_from_stream(video_stream);
	frame->pts = G.scene->r.cfra - G.scene->r.sfra;

	outsize = avcodec_encode_video(c, video_buffer, video_buffersize, 
				       frame);
	if (outsize != 0) {
		AVPacket packet;
		av_init_packet(&packet);

#ifdef FFMPEG_CODEC_TIME_BASE
		packet.pts = av_rescale_q(c->coded_frame->pts,
					  c->time_base,
					  video_stream->time_base);
#else
		packet.pts = c->coded_frame->pts;
#endif
		if (c->coded_frame->key_frame)
			packet.flags |= PKT_FLAG_KEY;
		packet.stream_index = video_stream->index;
		packet.data = video_buffer;
		packet.size = outsize;
		ret = av_write_frame(outfile, &packet);
	} else ret = 0;
	if (ret != 0) {
		G.afbreek = 1;
		error("Error writing frame");
	}
}

/* read and encode a frame of audio from the buffer */
static AVFrame* generate_video_frame(uint8_t* pixels) 
{
	uint8_t* rendered_frame;

	AVCodecContext* c = get_codec_from_stream(video_stream);
	int width = c->width;
	int height = c->height;
	AVFrame* rgb_frame;

	if (c->pix_fmt != PIX_FMT_RGBA32) {
		rgb_frame = alloc_picture(PIX_FMT_RGBA32, width, height);
		if (!rgb_frame) {
			G.afbreek=1;
			error("Couldn't allocate temporary frame");
			return NULL;
		}
	} else {
		rgb_frame = current_frame;
	}

	rendered_frame = pixels;

	/* Do RGBA-conversion and flipping in one step depending
	   on CPU-Endianess */

	if (G.order == L_ENDIAN) {
		int y;
		for (y = 0; y < height; y++) {
			uint8_t* target = rgb_frame->data[0]
				+ width * 4 * (height - y - 1);
			uint8_t* src = rendered_frame + width * 4 * y;
			uint8_t* end = src + width * 4;
			while (src != end) {
				target[3] = src[3];
				target[2] = src[0];
				target[1] = src[1];
				target[0] = src[2];

				target += 4;
				src += 4;
			}
		}
	} else {
		int y;
		for (y = 0; y < height; y++) {
			uint8_t* target = rgb_frame->data[0]
				+ width * 4 * (height - y - 1);
			uint8_t* src = rendered_frame + width * 4 * y;
			uint8_t* end = src + width * 4;
			while (src != end) {
				target[3] = src[2];
				target[2] = src[1];
				target[1] = src[0];
				target[0] = src[3];

				target += 4;
				src += 4;
			}
		}
	}

	if (c->pix_fmt != PIX_FMT_RGBA32) {
		img_convert((AVPicture*)current_frame, c->pix_fmt, 
			(AVPicture*)rgb_frame, PIX_FMT_RGBA32, width, height);
		delete_picture(rgb_frame);
	}
	return current_frame;
}

/* prepare a video stream for the output file */

static AVStream* alloc_video_stream(int codec_id, AVFormatContext* of,
				    int rectx, int recty) 
{
	AVStream* st;
	AVCodecContext* c;
	AVCodec* codec;
	st = av_new_stream(of, 0);
	if (!st) return NULL;

	/* Set up the codec context */
	
	c = get_codec_from_stream(st);
	c->codec_id = codec_id;
	c->codec_type = CODEC_TYPE_VIDEO;


	/* Get some values from the current render settings */
	
	c->width = rectx;
	c->height = recty;

#ifdef FFMPEG_CODEC_TIME_BASE
	/* FIXME: Really bad hack (tm) for NTSC support */
	if (ffmpeg_type == FFMPEG_DV && G.scene->r.frs_sec != 25) {
		c->time_base.den = 2997;
		c->time_base.num = 100;
	} else {
		c->time_base.den = G.scene->r.frs_sec;
		c->time_base.num = 1;
	}
#else
	/* FIXME: Really bad hack (tm) for NTSC support */
	if (ffmpeg_type == FFMPEG_DV && G.scene->r.frs_sec != 25) {
		c->frame_rate = 2997;
		c->frame_rate_base = 100;
	} else {
		c->frame_rate = G.scene->r.frs_sec;
		c->frame_rate_base = 1;
	}
#endif
	
	c->gop_size = ffmpeg_gop_size;
	c->bit_rate = ffmpeg_video_bitrate*1000;
	c->rc_max_rate = G.scene->r.ffcodecdata.rc_max_rate*1000;
	c->rc_min_rate = G.scene->r.ffcodecdata.rc_min_rate*1000;
	c->rc_buffer_size = G.scene->r.ffcodecdata.rc_buffer_size * 1024;
	c->rc_initial_buffer_occupancy 
		= G.scene->r.ffcodecdata.rc_buffer_size*3/4;
	c->rc_buffer_aggressivity = 1.0;
	c->me_method = ME_EPZS;
	
	codec = avcodec_find_encoder(c->codec_id);
	if (!codec) return NULL;
	
	/* Be sure to use the correct pixel format(e.g. RGB, YUV) */
	
	if (codec->pix_fmts) {
		c->pix_fmt = codec->pix_fmts[0];
	} else {
		/* makes HuffYUV happy ... */
		c->pix_fmt = PIX_FMT_YUV422P;
	}
	
	if (!strcmp(of->oformat->name, "mp4") || 
	    !strcmp(of->oformat->name, "mov") ||
	    !strcmp(of->oformat->name, "3gp")) {
		fprintf(stderr, "Using global header\n");
		c->flags |= CODEC_FLAG_GLOBAL_HEADER;
	}
	
	/* Determine whether we are encoding interlaced material or not */
	if (G.scene->r.mode & (1 << 6)) {
		fprintf(stderr, "Encoding interlaced video\n");
		c->flags |= CODEC_FLAG_INTERLACED_DCT;
		c->flags |= CODEC_FLAG_INTERLACED_ME;
	}	
	c->sample_aspect_ratio.num = G.scene->r.xasp;
	c->sample_aspect_ratio.den = G.scene->r.yasp;
	
	if (avcodec_open(c, codec) < 0) {
		error("Couldn't initialize codec");
		return NULL;
	}

	video_buffersize = 2000000;
	video_buffer = (uint8_t*)MEM_mallocN(video_buffersize, 
					     "FFMPEG video buffer");
	
	current_frame = alloc_picture(c->pix_fmt, c->width, c->height);
	return st;
}

/* Prepare an audio stream for the output file */

AVStream* alloc_audio_stream(int codec_id, AVFormatContext* of) 
{
	AVStream* st;
	AVCodecContext* c;
	AVCodec* codec;

	st = av_new_stream(of, 1);
	if (!st) return NULL;

	c = get_codec_from_stream(st);
	c->codec_id = codec_id;
	c->codec_type = CODEC_TYPE_AUDIO;

	c->sample_rate = G.scene->audio.mixrate;
	c->bit_rate = ffmpeg_audio_bitrate*1000;
	c->channels = 2;
	codec = avcodec_find_encoder(c->codec_id);
	if (!codec) {
		error("Couldn't find a valid audio codec");
		return NULL;
	}
	if (avcodec_open(c, codec) < 0) {
		error("Couldn't initialize audio codec");
		return NULL;
	}

	/* FIXME: Should be user configurable */
	audio_outbuf_size = 10000;
	audio_output_buffer = (uint8_t*)MEM_mallocN(
		audio_outbuf_size, "FFMPEG audio encoder input buffer");

       /* ugly hack for PCM codecs */

	if (c->frame_size <= 1) {
		audio_input_frame_size = audio_outbuf_size / c->channels;
		switch(c->codec_id) {
		case CODEC_ID_PCM_S16LE:
		case CODEC_ID_PCM_S16BE:
		case CODEC_ID_PCM_U16LE:
		case CODEC_ID_PCM_U16BE:
			audio_input_frame_size >>= 1;
			break;
		default:
			break;
		}
	} else {
		audio_input_frame_size = c->frame_size;
	}

	audio_input_buffer = (uint8_t*)MEM_mallocN(
		audio_input_frame_size * sizeof(short) * c->channels, 
		"FFMPEG audio encoder output buffer");

	return st;
}
/* essential functions -- start, append, end */

void start_ffmpeg_impl(RenderData *rd, int rectx, int recty)
{
	/* Handle to the output file */
	AVFormatContext* of;
	AVOutputFormat* fmt;

	ffmpeg_type = rd->ffcodecdata.type;
	ffmpeg_codec = rd->ffcodecdata.codec;
	ffmpeg_audio_codec = rd->ffcodecdata.audio_codec;
	ffmpeg_video_bitrate = rd->ffcodecdata.video_bitrate;
	ffmpeg_audio_bitrate = rd->ffcodecdata.audio_bitrate;
	ffmpeg_gop_size = rd->ffcodecdata.gop_size;
	ffmpeg_multiplex_audio = rd->ffcodecdata.flags
		& FFMPEG_MULTIPLEX_AUDIO;
	ffmpeg_autosplit = rd->ffcodecdata.flags
		& FFMPEG_AUTOSPLIT_OUTPUT;
	
	do_init_ffmpeg();

	/* Determine the correct filename */
	char name[256];
	makeffmpegstring(name);
	fprintf(stderr, "Starting output to %s(ffmpeg)...\n", name);
	
	fmt = guess_format(NULL, name, NULL);
	if (!fmt) {
		G.afbreek = 1; /* Abort render */
		error("No vaild formats found");
		return;
	}

	of = av_alloc_format_context();
	if (!of) {
		G.afbreek = 1;
		error("Error opening output file");
		return;
	}
	
	of->oformat = fmt;
	of->packet_size= G.scene->r.ffcodecdata.mux_packet_size;
	if (ffmpeg_multiplex_audio) {
		of->mux_rate = G.scene->r.ffcodecdata.mux_rate;
	} else {
		of->mux_rate = 0;
	}

	of->preload = (int)(0.5*AV_TIME_BASE);
	of->max_delay = (int)(0.7*AV_TIME_BASE);
	
	snprintf(of->filename, sizeof(of->filename), "%s", name);
	/* set the codec to the user's selection */
	switch(ffmpeg_type) {
		case FFMPEG_AVI:
		case FFMPEG_MOV:
			fmt->video_codec = ffmpeg_codec;
			break;
		case FFMPEG_DV:
			fmt->video_codec = CODEC_ID_DVVIDEO;
			break;
		case FFMPEG_MPEG1:
			fmt->video_codec = CODEC_ID_MPEG1VIDEO;
			break;
		case FFMPEG_MPEG2:
			fmt->video_codec = CODEC_ID_MPEG2VIDEO;
			break;
		case FFMPEG_MPEG4:
		default:
			fmt->video_codec = CODEC_ID_MPEG4;
			break;
	}
	if (ffmpeg_type == FFMPEG_DV) {
		fmt->audio_codec = CODEC_ID_PCM_S16LE;
	} else {
		fmt->audio_codec = ffmpeg_audio_codec;
	}
	
	video_stream = alloc_video_stream(fmt->video_codec, of, rectx, recty);
	if (!video_stream) {
		G.afbreek = 1;
		error("Error initializing video stream");
		return;
	}
	
	if (ffmpeg_multiplex_audio) {
		audio_stream = alloc_audio_stream(fmt->audio_codec, of);
		if (!audio_stream) {
			G.afbreek = 1;
			error("Error initializing audio stream");
			return;
		}
		audiostream_play(SFRA, 0, 1);
	}
	if (av_set_parameters(of, NULL) < 0) {
		G.afbreek = 1;
		error("Error setting output parameters");
		return;
	}
	if (!(fmt->flags & AVFMT_NOFILE)) {
		if (url_fopen(&of->pb, name, URL_WRONLY) < 0) {
			G.afbreek = 1;
			error("Could not open file for writing");
			return;
		}
	}

	av_write_header(of);
	outfile = of;
	dump_format(of, 0, name, 1);
}

void start_ffmpeg(RenderData *rd, int rectx, int recty)
{
	ffmpeg_autosplit_count = 0;

	ffmpeg_renderdata = rd;

	start_ffmpeg_impl(rd, rectx, recty);
}

void end_ffmpeg(void);

void append_ffmpeg(int frame, int *pixels, int rectx, int recty) 
{
	fprintf(stderr, "Writing frame %i\n", frame);
	while (ffmpeg_multiplex_audio && 
	       (((double)audio_stream->pts.val 
		 * audio_stream->time_base.num / audio_stream->time_base.den)
		< 
		((double)video_stream->pts.val 
		 * video_stream->time_base.num / video_stream->time_base.den)
		       )) {
		write_audio_frame();
	}
	write_video_frame(generate_video_frame((unsigned char*) pixels));

	if (ffmpeg_autosplit) {
		if (url_ftell(&outfile->pb) > FFMPEG_AUTOSPLIT_SIZE) {
			end_ffmpeg();
			ffmpeg_autosplit_count++;
			start_ffmpeg_impl(ffmpeg_renderdata,
					  rectx, recty);
		}
	}
}


void end_ffmpeg(void)
{
	int i;
	
	fprintf(stderr, "Closing ffmpeg...\n");

	if (outfile) {
		av_write_trailer(outfile);
	}
	
	/* Close the video codec */

	if (video_stream && get_codec_from_stream(video_stream)) {
		avcodec_close(get_codec_from_stream(video_stream));
	}

	
	/* Close the output file */
	if (outfile) {
		for (i = 0; i < outfile->nb_streams; i++) {
			if (&outfile->streams[i]) {
				av_freep(&outfile->streams[i]);
			}
		}
	}
	/* free the temp buffer */
	if (current_frame) {
		delete_picture(current_frame);
	}
	if (outfile && outfile->oformat) {
		if (!(outfile->oformat->flags & AVFMT_NOFILE)) {
			url_fclose(&outfile->pb);
		}
	}
	if (outfile) {
		av_free(outfile);
		outfile = 0;
	}
	if (video_buffer) {
		MEM_freeN(video_buffer);
		video_buffer = 0;
	}
	if (audio_output_buffer) {
		MEM_freeN(audio_output_buffer);
		audio_output_buffer = 0;
	}
	if (audio_input_buffer) {
		MEM_freeN(audio_input_buffer);
		audio_input_buffer = 0;
	}
}
#endif

