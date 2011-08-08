#include "IMB_indexer.h"
#include "IMB_anim.h"
#include "AVI_avi.h"
#include "imbuf.h"
#include "MEM_guardedalloc.h"
#include "BLI_utildefines.h"
#include "BLI_blenlib.h"
#include "BLI_math_base.h"
#include "BLI_string.h"
#include "MEM_guardedalloc.h"
#include "DNA_userdef_types.h"
#include "BKE_global.h"
#include <stdlib.h>

#ifdef WITH_FFMPEG

#include "ffmpeg_compat.h"

#endif //WITH_FFMPEG


static char magic[] = "BlenMIdx";
static char temp_ext [] = "_part";

static int proxy_sizes[] = { IMB_PROXY_25, IMB_PROXY_50, IMB_PROXY_75 };
static int tc_types[] = { IMB_TC_RECORD_RUN, IMB_TC_FREE_RUN,
			  IMB_TC_INTERPOLATED_REC_DATE_FREE_RUN };
static float proxy_fac[] = { 0.25, 0.50, 0.75 };

#define INDEX_FILE_VERSION 1

/* ---------------------------------------------------------------------- 
   - special indexers
   ---------------------------------------------------------------------- 
 */

extern void IMB_indexer_dv_new(anim_index_builder * idx);


/* ----------------------------------------------------------------------
   - time code index functions
   ---------------------------------------------------------------------- */

anim_index_builder * IMB_index_builder_create(const char * name)
{

	anim_index_builder * rv 
		= MEM_callocN( sizeof(struct anim_index_builder), 
			       "index builder");

	fprintf(stderr, "Starting work on index: %s\n", name);

	BLI_strncpy(rv->name, name, sizeof(rv->name));
	BLI_strncpy(rv->temp_name, name, sizeof(rv->temp_name));

	strcat(rv->temp_name, temp_ext);

	BLI_make_existing_file(rv->temp_name);

	rv->fp = fopen(rv->temp_name, "w");

	if (!rv->fp) {
		fprintf(stderr, "Couldn't open index target: %s! "
			"Index build broken!\n", rv->temp_name);
		MEM_freeN(rv);
		return NULL;
	}

	fprintf(rv->fp, "%s%c%.3d", magic, (ENDIAN_ORDER==B_ENDIAN)?'V':'v',
		INDEX_FILE_VERSION);

	return rv;
}

void IMB_index_builder_add_entry(anim_index_builder * fp, 
				 int frameno,unsigned long long seek_pos,
				 unsigned long long seek_pos_dts,
				 unsigned long long pts)
{
	fwrite(&frameno, sizeof(int), 1, fp->fp);
	fwrite(&seek_pos, sizeof(unsigned long long), 1, fp->fp);
	fwrite(&seek_pos_dts, sizeof(unsigned long long), 1, fp->fp);
	fwrite(&pts, sizeof(unsigned long long), 1, fp->fp);
}

void IMB_index_builder_proc_frame(anim_index_builder * fp, 
				  unsigned char * buffer,
				  int data_size,
				  int frameno, unsigned long long seek_pos,
				  unsigned long long seek_pos_dts,
				  unsigned long long pts)
{
	if (fp->proc_frame) {
		anim_index_entry e;
		e.frameno = frameno;
		e.seek_pos = seek_pos;
		e.seek_pos_dts = seek_pos_dts;
		e.pts = pts;

		fp->proc_frame(fp, buffer, data_size, &e);
	} else {
		IMB_index_builder_add_entry(fp, frameno, seek_pos,
					    seek_pos_dts, pts);
	}
}

void IMB_index_builder_finish(anim_index_builder * fp, int rollback)
{
	if (fp->delete_priv_data) {
		fp->delete_priv_data(fp);
	}

	fclose(fp->fp);
	
	if (rollback) {
		unlink(fp->temp_name);
	} else {
		rename(fp->temp_name, fp->name);
	}

	MEM_freeN(fp);
}

struct anim_index * IMB_indexer_open(const char * name)
{
	char header[13];
	struct anim_index * idx;
	FILE * fp = fopen(name, "rb");
	int i;

	if (!fp) {
		return 0;
	}

	if (fread(header, 12, 1, fp) != 1) {
		fclose(fp);
		return 0;
	}

	header[12] = 0;

	if (memcmp(header, magic, 8) != 0) {
		fclose(fp);
		return 0;
	}

	if (atoi(header+9) != INDEX_FILE_VERSION) {
		fclose(fp);
		return 0;
	}

	idx = MEM_callocN( sizeof(struct anim_index), "anim_index");

	BLI_strncpy(idx->name, name, sizeof(idx->name));
	
       	fseek(fp, 0, SEEK_END);

	idx->num_entries = (ftell(fp) - 12) 
		/ (sizeof(int) // framepos
		   + sizeof(unsigned long long) // seek_pos
		   + sizeof(unsigned long long) // seek_pos_dts
		   + sizeof(unsigned long long) // pts
			);
	
	fseek(fp, 12, SEEK_SET);

	idx->entries = MEM_callocN( sizeof(struct anim_index_entry) 
				    * idx->num_entries, "anim_index_entries");

	for (i = 0; i < idx->num_entries; i++) {
		fread(&idx->entries[i].frameno, 
		      sizeof(int), 1, fp);
		fread(&idx->entries[i].seek_pos, 
		      sizeof(unsigned long long), 1, fp);
		fread(&idx->entries[i].seek_pos_dts, 
		      sizeof(unsigned long long), 1, fp);
		fread(&idx->entries[i].pts, 
		      sizeof(unsigned long long), 1, fp);
	}

	if (((ENDIAN_ORDER == B_ENDIAN) != (header[8] == 'V'))) {
		for (i = 0; i < idx->num_entries; i++) {
			SWITCH_INT(idx->entries[i].frameno);
			SWITCH_INT64(idx->entries[i].seek_pos);
			SWITCH_INT64(idx->entries[i].seek_pos_dts);
			SWITCH_INT64(idx->entries[i].pts);
		}
	}

	fclose(fp);

	return idx;
}

unsigned long long IMB_indexer_get_seek_pos(
	struct anim_index * idx, int frame_index)
{
	if (frame_index < 0) {
		frame_index = 0;
	}
	if (frame_index >= idx->num_entries) {
		frame_index = idx->num_entries - 1;
	}
	return idx->entries[frame_index].seek_pos;
}

unsigned long long IMB_indexer_get_seek_pos_dts(
	struct anim_index * idx, int frame_index)
{
	if (frame_index < 0) {
		frame_index = 0;
	}
	if (frame_index >= idx->num_entries) {
		frame_index = idx->num_entries - 1;
	}
	return idx->entries[frame_index].seek_pos_dts;
}

int IMB_indexer_get_frame_index(struct anim_index * idx, int frameno)
{
	int len = idx->num_entries;
	int half;
	int middle;
	int first = 0;

	/* bsearch (lower bound) the right index */
	
	while (len > 0) {
		half = len >> 1;
		middle = first;

		middle += half;

		if (idx->entries[middle].frameno < frameno) {
			first = middle;
			++first;
			len = len - half - 1;
		} else {
			len = half;
		}
	}

	if (first == idx->num_entries) {
		return idx->num_entries - 1;
	} else {
		return first;
	}
}

unsigned long long IMB_indexer_get_pts(struct anim_index * idx, 
				       int frame_index)
{
	if (frame_index < 0) {
		frame_index = 0;
	}
	if (frame_index >= idx->num_entries) {
		frame_index = idx->num_entries - 1;
	}
	return idx->entries[frame_index].pts;
}

int IMB_indexer_get_duration(struct anim_index * idx)
{
	if (idx->num_entries == 0) {
		return 0;
	}
	return idx->entries[idx->num_entries-1].frameno + 1;
}

int IMB_indexer_can_scan(struct anim_index * idx, 
			 int old_frame_index, int new_frame_index)
{
	/* makes only sense, if it is the same I-Frame and we are not
	   trying to run backwards in time... */
	return (IMB_indexer_get_seek_pos(idx, old_frame_index)
		== IMB_indexer_get_seek_pos(idx, new_frame_index) && 
		old_frame_index < new_frame_index);
}

void IMB_indexer_close(struct anim_index * idx)
{
	MEM_freeN(idx->entries);
	MEM_freeN(idx);
}

int IMB_proxy_size_to_array_index(IMB_Proxy_Size pr_size)
{
	switch (pr_size) {
	case IMB_PROXY_NONE: /* if we got here, something is broken anyways,
				so sane defaults... */
	case IMB_PROXY_MAX_SLOT:
		return 0;
	case IMB_PROXY_25:
		return 0;
	case IMB_PROXY_50:
		return 1;
	case IMB_PROXY_75:
		return 2;
	};
	return 0;
}

int IMB_timecode_to_array_index(IMB_Timecode_Type tc)
{
	switch (tc) {
	case IMB_TC_NONE: /* if we got here, something is broken anyways,
				so sane defaults... */
	case IMB_TC_MAX_SLOT:
		return 0;
	case IMB_TC_RECORD_RUN:
		return 0;
	case IMB_TC_FREE_RUN:
		return 1;
	case IMB_TC_INTERPOLATED_REC_DATE_FREE_RUN:
		return 2;
	};
	return 0;
}


/* ----------------------------------------------------------------------
   - rebuild helper functions
   ---------------------------------------------------------------------- */

static void get_index_dir(struct anim * anim, char * index_dir)
{
	if (!anim->index_dir[0]) {
		char fname[FILE_MAXFILE];
		BLI_strncpy(index_dir, anim->name, FILE_MAXDIR);
		BLI_splitdirstring(index_dir, fname);
		BLI_join_dirfile(index_dir, FILE_MAXDIR, index_dir,
				 "BL_proxy");
		BLI_join_dirfile(index_dir, FILE_MAXDIR, index_dir,
				 fname);
	} else {
		BLI_strncpy(index_dir, anim->index_dir, FILE_MAXDIR);
	}
}

static void get_proxy_filename(struct anim * anim, IMB_Proxy_Size preview_size,
			       char * fname, int temp)
{
	char index_dir[FILE_MAXDIR];
	int i = IMB_proxy_size_to_array_index(preview_size);

	char * proxy_names[] = { 
		"proxy_25.avi", "proxy_50.avi", "proxy_75.avi" };

	char * proxy_temp_names[] = { 
		"proxy_25_part.avi", "proxy_50_part.avi", "proxy_75_part.avi" };

	get_index_dir(anim, index_dir);

	BLI_join_dirfile(fname, FILE_MAXFILE + FILE_MAXDIR, index_dir, 
			 temp ? proxy_temp_names[i] : proxy_names[i]);
}

static void get_tc_filename(struct anim * anim, IMB_Timecode_Type tc,
			    char * fname)
{
	char index_dir[FILE_MAXDIR];
	int i = IMB_timecode_to_array_index(tc);
	char * index_names[] = {
		"record_run.blen_tc", "free_run.blen_tc",
		"interp_free_run.blen_tc" };

	get_index_dir(anim, index_dir);
	
	BLI_join_dirfile(fname, FILE_MAXFILE + FILE_MAXDIR, 
			 index_dir, index_names[i]);
}

/* ----------------------------------------------------------------------
   - ffmpeg rebuilder
   ---------------------------------------------------------------------- */

#ifdef WITH_FFMPEG

struct proxy_output_ctx {
	AVFormatContext* of;
	AVStream* st;
	AVCodecContext* c;
	AVCodec* codec;
	struct SwsContext * sws_ctx;
	AVFrame* frame;
	uint8_t* video_buffer;
	int video_buffersize;
	int cfra;
	int proxy_size;
	int orig_height;
	struct anim * anim;
};

// work around stupid swscaler 16 bytes alignment bug...

static int round_up(int x, int mod)
{
	return x + ((mod - (x % mod)) % mod);
}

static struct proxy_output_ctx * alloc_proxy_output_ffmpeg(
	struct anim * anim,
	AVStream * st, int proxy_size, int width, int height,
	int UNUSED(quality))
{
	struct proxy_output_ctx * rv = MEM_callocN(
		sizeof(struct proxy_output_ctx), "alloc_proxy_output");
	
	char fname[FILE_MAXDIR+FILE_MAXFILE];

	// JPEG requires this
	width = round_up(width, 8);
	height = round_up(height, 8);

	rv->proxy_size = proxy_size;
	rv->anim = anim;

	get_proxy_filename(rv->anim, rv->proxy_size, fname, TRUE);
	BLI_make_existing_file(fname);

	rv->of = avformat_alloc_context();
	rv->of->oformat = av_guess_format("avi", NULL, NULL);
	
	BLI_snprintf(rv->of->filename, sizeof(rv->of->filename), "%s", fname);

	fprintf(stderr, "Starting work on proxy: %s\n", rv->of->filename);

	rv->st = av_new_stream(rv->of, 0);
	rv->c = rv->st->codec;
	rv->c->codec_type = AVMEDIA_TYPE_VIDEO;
	rv->c->codec_id = CODEC_ID_MJPEG;
	rv->c->width = width;
	rv->c->height = height;

	rv->of->oformat->video_codec = rv->c->codec_id;
	rv->codec = avcodec_find_encoder(rv->c->codec_id);

	if (!rv->codec) {
		fprintf(stderr, "No ffmpeg MJPEG encoder available? "
			"Proxy not built!\n");
		av_free(rv->of);
		return NULL;
	}

	if (rv->codec->pix_fmts) {
		rv->c->pix_fmt = rv->codec->pix_fmts[0];
	} else {
		rv->c->pix_fmt = PIX_FMT_YUVJ420P;
	}

	rv->c->sample_aspect_ratio 
		= rv->st->sample_aspect_ratio 
		= st->codec->sample_aspect_ratio;

	rv->c->time_base.den = 25;
	rv->c->time_base.num = 1;
	rv->st->time_base = rv->c->time_base;

	if (rv->of->flags & AVFMT_GLOBALHEADER) {
		rv->c->flags |= CODEC_FLAG_GLOBAL_HEADER;
	}

	if (av_set_parameters(rv->of, NULL) < 0) {
		fprintf(stderr, "Couldn't set output parameters? "
			"Proxy not built!\n");
		av_free(rv->of);
		return 0;
	}

	if (avio_open(&rv->of->pb, fname, AVIO_FLAG_WRITE) < 0) {
		fprintf(stderr, "Couldn't open outputfile! "
			"Proxy not built!\n");
		av_free(rv->of);
		return 0;
	}

	avcodec_open(rv->c, rv->codec);

	rv->video_buffersize = 2000000;
	rv->video_buffer = (uint8_t*)MEM_mallocN(
		rv->video_buffersize, "FFMPEG video buffer");

	rv->frame = avcodec_alloc_frame();
	avpicture_fill((AVPicture*) rv->frame, 
		       MEM_mallocN(avpicture_get_size(
					   rv->c->pix_fmt, 
					   round_up(width, 16), height),
				   "alloc proxy output frame"),
		       rv->c->pix_fmt, round_up(width, 16), height);

	rv->orig_height = st->codec->height;

	rv->sws_ctx = sws_getContext(
		st->codec->width,
		st->codec->height,
		st->codec->pix_fmt,
		width, height,
		rv->c->pix_fmt,
		SWS_FAST_BILINEAR | SWS_PRINT_INFO,
		NULL, NULL, NULL);

	av_write_header(rv->of);

	return rv;
}

static int add_to_proxy_output_ffmpeg(
	struct proxy_output_ctx * ctx, AVFrame * frame)
{
	int outsize = 0;

	if (!ctx) {
		return 0;
	}

	if (frame && (frame->data[0] || frame->data[1] ||
		      frame->data[2] || frame->data[3])) {
		sws_scale(ctx->sws_ctx, (const uint8_t * const*) frame->data,
			  frame->linesize, 0, ctx->orig_height, 
			  ctx->frame->data, ctx->frame->linesize);
	}

	ctx->frame->pts = ctx->cfra++;

	outsize = avcodec_encode_video(
		ctx->c, ctx->video_buffer, ctx->video_buffersize, 
		frame ? ctx->frame : 0);

	if (outsize < 0) {
		fprintf(stderr, "Error encoding proxy frame %d for '%s'\n", 
			ctx->cfra - 1, ctx->of->filename);
		return 0;
	}

	if (outsize != 0) {
		AVPacket packet;
		av_init_packet(&packet);

		if (ctx->c->coded_frame->pts != AV_NOPTS_VALUE) {
			packet.pts = av_rescale_q(ctx->c->coded_frame->pts,
						  ctx->c->time_base,
						  ctx->st->time_base);
		}
		if (ctx->c->coded_frame->key_frame)
			packet.flags |= AV_PKT_FLAG_KEY;

		packet.stream_index = ctx->st->index;
		packet.data = ctx->video_buffer;
		packet.size = outsize;

		if (av_interleaved_write_frame(ctx->of, &packet) != 0) {
			fprintf(stderr, "Error writing proxy frame %d "
				"into '%s'\n", ctx->cfra - 1, 
				ctx->of->filename);
			return 0;
		}

		return 1;
	} else {
		return 0;
	}
}

static void free_proxy_output_ffmpeg(struct proxy_output_ctx * ctx,
				     int rollback)
{
	int i;
	char fname[FILE_MAXDIR+FILE_MAXFILE];
	char fname_tmp[FILE_MAXDIR+FILE_MAXFILE];

	if (!ctx) {
		return;
	}

	if (!rollback) {
		while (add_to_proxy_output_ffmpeg(ctx, NULL)) ;
	}

	avcodec_flush_buffers(ctx->c);

	av_write_trailer(ctx->of);
	
	avcodec_close(ctx->c);
	
	for (i = 0; i < ctx->of->nb_streams; i++) {
		if (&ctx->of->streams[i]) {
			av_freep(&ctx->of->streams[i]);
		}
	}

	if (ctx->of->oformat) {
		if (!(ctx->of->oformat->flags & AVFMT_NOFILE)) {
			avio_close(ctx->of->pb);
		}
	}
	av_free(ctx->of);

	MEM_freeN(ctx->video_buffer);

	sws_freeContext(ctx->sws_ctx);

	MEM_freeN(ctx->frame->data[0]);
	av_free(ctx->frame);

	get_proxy_filename(ctx->anim, ctx->proxy_size, 
			   fname_tmp, TRUE);

	if (rollback) {
		unlink(fname_tmp);
	} else {
		get_proxy_filename(ctx->anim, ctx->proxy_size, 
				   fname, FALSE);
		rename(fname_tmp, fname);
	}
	
	MEM_freeN(ctx);
}


static int index_rebuild_ffmpeg(struct anim * anim, 
				IMB_Timecode_Type tcs_in_use,
				IMB_Proxy_Size proxy_sizes_in_use,
				int quality,
				short *stop, short *do_update, 
				float *progress)
{
	int            i, videoStream;
	unsigned long long seek_pos = 0;
	unsigned long long last_seek_pos = 0;
	unsigned long long seek_pos_dts = 0;
	unsigned long long seek_pos_pts = 0;
	unsigned long long last_seek_pos_dts = 0;
	unsigned long long start_pts = 0;
	double frame_rate;
	double pts_time_base;
	int frameno = 0;
	int start_pts_set = FALSE;

	AVFormatContext *iFormatCtx;
	AVCodecContext *iCodecCtx;
	AVCodec *iCodec;
	AVStream *iStream;
	AVFrame* in_frame = 0;
	AVPacket next_packet;

	struct proxy_output_ctx * proxy_ctx[IMB_PROXY_MAX_SLOT];
	anim_index_builder * indexer [IMB_TC_MAX_SLOT];

	int num_proxy_sizes = IMB_PROXY_MAX_SLOT;
	int num_indexers = IMB_TC_MAX_SLOT;
	uint64_t stream_size;

	memset(proxy_ctx, 0, sizeof(proxy_ctx));
	memset(indexer, 0, sizeof(indexer));

	if(av_open_input_file(&iFormatCtx, anim->name, NULL, 0, NULL)!=0) {
		return 0;
	}

	if (av_find_stream_info(iFormatCtx)<0) {
		av_close_input_file(iFormatCtx);
		return 0;
	}

	/* Find the first video stream */
	videoStream = -1;
	for (i = 0; i < iFormatCtx->nb_streams; i++)
		if(iFormatCtx->streams[i]->codec->codec_type
		   == AVMEDIA_TYPE_VIDEO) {
			videoStream = i;
			break;
		}

	if (videoStream == -1) {
		av_close_input_file(iFormatCtx);
		return 0;
	}

	iStream = iFormatCtx->streams[videoStream];
	iCodecCtx = iStream->codec;

	iCodec = avcodec_find_decoder(iCodecCtx->codec_id);
	
	if (iCodec == NULL) {
		av_close_input_file(iFormatCtx);
		return 0;
	}

	iCodecCtx->workaround_bugs = 1;

	if (avcodec_open(iCodecCtx, iCodec) < 0) {
		av_close_input_file(iFormatCtx);
		return 0;
	}

	in_frame = avcodec_alloc_frame();

	stream_size = avio_size(iFormatCtx->pb);

	for (i = 0; i < num_proxy_sizes; i++) {
		if (proxy_sizes_in_use & proxy_sizes[i]) {
			proxy_ctx[i] = alloc_proxy_output_ffmpeg(
				anim, iStream, proxy_sizes[i],
				iCodecCtx->width * proxy_fac[i],
				iCodecCtx->height * proxy_fac[i],
				quality);
			if (!proxy_ctx[i]) {
				proxy_sizes_in_use &= ~proxy_sizes[i];
			}
		}
	}

	for (i = 0; i < num_indexers; i++) {
		if (tcs_in_use & tc_types[i]) {
			char fname[FILE_MAXDIR+FILE_MAXFILE];

			get_tc_filename(anim, tc_types[i], fname);

			indexer[i] = IMB_index_builder_create(fname);
			if (!indexer[i]) {
				tcs_in_use &= ~tc_types[i];
			}
		}
	}

	frame_rate = av_q2d(iStream->r_frame_rate);
	pts_time_base = av_q2d(iStream->time_base);

	while(av_read_frame(iFormatCtx, &next_packet) >= 0) {
		int frame_finished = 0;
		float next_progress =  ((int)floor(((double) next_packet.pos) * 100 /
					           ((double) stream_size)+0.5)) / 100;

		if (*progress != next_progress) {
			*progress = next_progress;
			*do_update = 1;
		}

		if (*stop) {
			av_free_packet(&next_packet);
			break;
		}

		if (next_packet.stream_index == videoStream) {
			if (next_packet.flags & AV_PKT_FLAG_KEY) {
				last_seek_pos = seek_pos;
				last_seek_pos_dts = seek_pos_dts;
				seek_pos = next_packet.pos;
				seek_pos_dts = next_packet.dts;
				seek_pos_pts = next_packet.pts;
			}

			avcodec_decode_video2(
				iCodecCtx, in_frame, &frame_finished, 
				&next_packet);
		}

		if (frame_finished) {
			unsigned long long s_pos = seek_pos;
			unsigned long long s_dts = seek_pos_dts;
			unsigned long long pts 
				= av_get_pts_from_frame(iFormatCtx, in_frame);

			for (i = 0; i < num_proxy_sizes; i++) {
				add_to_proxy_output_ffmpeg(
					proxy_ctx[i], in_frame);
			}

			if (!start_pts_set) {
				start_pts = pts;
				start_pts_set = TRUE;
			}

			frameno = (pts - start_pts) 
				* pts_time_base * frame_rate; 

			/* decoding starts *always* on I-Frames,
			   so: P-Frames won't work, even if all the
			   information is in place, when we seek
			   to the I-Frame presented *after* the P-Frame,
			   but located before the P-Frame within
			   the stream */

			if (in_frame->pkt_pts < seek_pos_pts) {
				s_pos = last_seek_pos;
				s_dts = last_seek_pos_dts;
			}

			for (i = 0; i < num_indexers; i++) {
				if (tcs_in_use & tc_types[i]) {
					IMB_index_builder_proc_frame(
						indexer[i], 
						next_packet.data, 
						next_packet.size,
						frameno, s_pos,	s_dts, pts);
				}
			}
		}
		av_free_packet(&next_packet);
	}

	for (i = 0; i < num_indexers; i++) {
		if (tcs_in_use & tc_types[i]) {
			IMB_index_builder_finish(indexer[i], *stop);
		}
	}

	for (i = 0; i < num_proxy_sizes; i++) {
		if (proxy_sizes_in_use & proxy_sizes[i]) {
			free_proxy_output_ffmpeg(proxy_ctx[i], *stop);
		}
	}

	av_free(in_frame);

	return 1;
}

#endif

/* ----------------------------------------------------------------------
   - internal AVI (fallback) rebuilder
   ---------------------------------------------------------------------- */

static AviMovie * alloc_proxy_output_avi(
	struct anim * anim, char * filename, int width, int height,
	int quality)
{
	int x, y;
	AviFormat format;
	double framerate;
	AviMovie * avi;
	short frs_sec = 25;      /* it doesn't really matter for proxies,
				    but sane defaults help anyways...*/
	float frs_sec_base = 1.0;

	IMB_anim_get_fps(anim, &frs_sec, &frs_sec_base);
	
	x = width;
	y = height;

	framerate= (double) frs_sec / (double) frs_sec_base;
	
	avi = MEM_mallocN (sizeof(AviMovie), "avimovie");

	format = AVI_FORMAT_MJPEG;

	if (AVI_open_compress (filename, avi, 1, format) != AVI_ERROR_NONE) {
		MEM_freeN(avi);
		return 0;
	}
			
	AVI_set_compress_option (avi, AVI_OPTION_TYPE_MAIN, 0, AVI_OPTION_WIDTH, &x);
	AVI_set_compress_option (avi, AVI_OPTION_TYPE_MAIN, 0, AVI_OPTION_HEIGHT, &y);
	AVI_set_compress_option (avi, AVI_OPTION_TYPE_MAIN, 0, AVI_OPTION_QUALITY, &quality);		
	AVI_set_compress_option (avi, AVI_OPTION_TYPE_MAIN, 0, AVI_OPTION_FRAMERATE, &framerate);

	avi->interlace= 0;
	avi->odd_fields= 0;

	return avi;
}

static void index_rebuild_fallback(struct anim * anim,
				   IMB_Timecode_Type UNUSED(tcs_in_use),
				   IMB_Proxy_Size proxy_sizes_in_use,
				   int quality,
				   short *stop, short *do_update, 
				   float *progress)
{
	int cnt = IMB_anim_get_duration(anim, IMB_TC_NONE);
	int i, pos;
	AviMovie * proxy_ctx[IMB_PROXY_MAX_SLOT];
	char fname[FILE_MAXDIR+FILE_MAXFILE];
	char fname_tmp[FILE_MAXDIR+FILE_MAXFILE];
	
	memset(proxy_ctx, 0, sizeof(proxy_ctx));

	/* since timecode indices only work with ffmpeg right now,
	   don't know a sensible fallback here...

	   so no proxies, no game to play...
	*/
	if (proxy_sizes_in_use == IMB_PROXY_NONE) {
		return;
	}

	for (i = 0; i < IMB_PROXY_MAX_SLOT; i++) {
		if (proxy_sizes_in_use & proxy_sizes[i]) {
			char fname[FILE_MAXDIR+FILE_MAXFILE];

			get_proxy_filename(anim, proxy_sizes[i], fname, TRUE);
			BLI_make_existing_file(fname);

			proxy_ctx[i] = alloc_proxy_output_avi(
				anim, fname,
				anim->x * proxy_fac[i],
				anim->y * proxy_fac[i],
				quality);
		}
	}

	for (pos = 0; pos < cnt; pos++) {
		struct ImBuf * ibuf = IMB_anim_absolute(
			anim, pos, IMB_TC_NONE, IMB_PROXY_NONE);
		int next_progress = (int) ((double) pos / (double) cnt);

		if (*progress != next_progress) {
			*progress = next_progress;
			*do_update = 1;
		}
		
		if (*stop) {
			break;
		}

		IMB_flipy(ibuf);

		for (i = 0; i < IMB_PROXY_MAX_SLOT; i++) {
			if (proxy_sizes_in_use & proxy_sizes[i]) {
				int x = anim->x * proxy_fac[i];
				int y = anim->y * proxy_fac[i];

				struct ImBuf * s_ibuf = IMB_scalefastImBuf(
					ibuf, x, y);

				IMB_convert_rgba_to_abgr(s_ibuf);
	
				AVI_write_frame (proxy_ctx[i], pos, 
						 AVI_FORMAT_RGB32, 
						 s_ibuf->rect, x * y * 4);

				/* note that libavi free's the buffer... */
				s_ibuf->rect = 0;

				IMB_freeImBuf(s_ibuf);
			}
		}
	}

	for (i = 0; i < IMB_PROXY_MAX_SLOT; i++) {
		if (proxy_sizes_in_use & proxy_sizes[i]) {
			AVI_close_compress (proxy_ctx[i]);
			MEM_freeN (proxy_ctx[i]);

			get_proxy_filename(anim, proxy_sizes[i], 
					   fname_tmp, TRUE);
			get_proxy_filename(anim, proxy_sizes[i], 
					   fname, FALSE);

			if (*stop) {
				unlink(fname_tmp);
			} else {
				rename(fname_tmp, fname);
			}
		}
	}
}

/* ----------------------------------------------------------------------
   - public API
   ---------------------------------------------------------------------- */

void IMB_anim_index_rebuild(struct anim * anim, IMB_Timecode_Type tcs_in_use,
			    IMB_Proxy_Size proxy_sizes_in_use,
			    int quality,
			    short *stop, short *do_update, float *progress)
{
	switch (anim->curtype) {
#ifdef WITH_FFMPEG
	case ANIM_FFMPEG:
		index_rebuild_ffmpeg(anim, tcs_in_use, proxy_sizes_in_use,
				     quality, stop, do_update, progress);
		break;
#endif
	default:
		index_rebuild_fallback(anim, tcs_in_use, proxy_sizes_in_use,
				       quality, stop, do_update, progress);
		break;
	}
}

void IMB_free_indices(struct anim * anim)
{
	int i;

	for (i = 0; i < IMB_PROXY_MAX_SLOT; i++) {
		if (anim->proxy_anim[i]) {
			IMB_close_anim(anim->proxy_anim[i]);
			anim->proxy_anim[i] = 0;
		}
	}

	for (i = 0; i < IMB_TC_MAX_SLOT; i++) {
		if (anim->curr_idx[i]) {
			IMB_indexer_close(anim->curr_idx[i]);
			anim->curr_idx[i] = 0;
		}
	}


	anim->proxies_tried = 0;
	anim->indices_tried = 0;
}

void IMB_anim_set_index_dir(struct anim * anim, const char * dir)
{
	if (strcmp(anim->index_dir, dir) == 0) {
		return;
	}
	BLI_strncpy(anim->index_dir, dir, sizeof(anim->index_dir));

	IMB_free_indices(anim);
}

struct anim * IMB_anim_open_proxy(
	struct anim * anim, IMB_Proxy_Size preview_size)
{
	char fname[FILE_MAXDIR+FILE_MAXFILE];
	int i = IMB_proxy_size_to_array_index(preview_size);

	if (anim->proxy_anim[i]) {
		return anim->proxy_anim[i];
	}

	if (anim->proxies_tried & preview_size) {
		return NULL;
	}

	get_proxy_filename(anim, preview_size, fname, FALSE);

	anim->proxy_anim[i] = IMB_open_anim(fname, 0);
	
	anim->proxies_tried |= preview_size;

	return anim->proxy_anim[i];
}

struct anim_index * IMB_anim_open_index(
	struct anim * anim, IMB_Timecode_Type tc)
{
	char fname[FILE_MAXDIR+FILE_MAXFILE];
	int i = IMB_timecode_to_array_index(tc);

	if (anim->curr_idx[i]) {
		return anim->curr_idx[i];
	}

	if (anim->indices_tried & tc) {
		return 0;
	}

	get_tc_filename(anim, tc, fname);

	anim->curr_idx[i] = IMB_indexer_open(fname);
	
	anim->indices_tried |= tc;

	return anim->curr_idx[i];
}

int IMB_anim_index_get_frame_index(struct anim * anim, IMB_Timecode_Type tc,
				   int position)
{
	struct anim_index * idx = IMB_anim_open_index(anim, tc);

	if (!idx) {
		return position;
	}

	return IMB_indexer_get_frame_index(idx, position);
}

