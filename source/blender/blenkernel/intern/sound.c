/**
 * sound.c (mar-2001 nzc)
 *
 * $Id$
 */

#include <string.h>
#include <stdlib.h>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"

#include "DNA_scene_types.h"
#include "DNA_sound_types.h"
#include "DNA_packedFile_types.h"
#include "DNA_screen_types.h"
#include "DNA_userdef_types.h"

#include "AUD_C-API.h"

#include "BKE_utildefines.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_sound.h"
#include "BKE_context.h"
#include "BKE_library.h"
#include "BKE_packedFile.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

void sound_init()
{
	AUD_Specs specs;
	int device, buffersize, success;

	device = U.audiodevice;
	buffersize = U.mixbufsize;
	specs.channels = U.audiochannels;
	specs.format = U.audioformat;
	specs.rate = U.audiorate;

	if(buffersize < 128)
		buffersize = AUD_DEFAULT_BUFFER_SIZE;

	if(specs.rate < AUD_RATE_8000)
		specs.rate = AUD_RATE_44100;

	if(specs.format <= AUD_FORMAT_INVALID)
		specs.format = AUD_FORMAT_S16;

	if(specs.channels <= AUD_CHANNELS_INVALID)
		specs.channels = AUD_CHANNELS_STEREO;

	if(!AUD_init(device, specs, buffersize)) {
		if(device == AUD_SDL_DEVICE)
			success= AUD_init(AUD_OPENAL_DEVICE, specs, AUD_DEFAULT_BUFFER_SIZE*4);
		else
			success= AUD_init(AUD_SDL_DEVICE, specs, AUD_DEFAULT_BUFFER_SIZE*4);

		if(!success)
			AUD_init(AUD_NULL_DEVICE, specs, buffersize);
	}
}

void sound_exit()
{
	AUD_exit();
}

struct bSound* sound_new_file(struct Main *main, char* filename)
{
	bSound* sound = NULL;

	char str[FILE_MAX];
	int len;

	strcpy(str, filename);
	BLI_convertstringcode(str, G.sce);

	len = strlen(filename);
	while(len > 0 && filename[len-1] != '/' && filename[len-1] != '\\')
		len--;

	sound = alloc_libblock(&main->sound, ID_SO, filename+len);
	strcpy(sound->name, filename);
	sound->type = SOUND_TYPE_FILE;

	sound_load(sound);

	if(!sound->snd_sound)
	{
		free_libblock(&main->sound, sound);
		sound = NULL;
	}

	return sound;
}

// XXX unused currently
#if 0
struct bSound* sound_new_buffer(struct bContext *C, struct bSound *source)
{
	bSound* sound = NULL;

	char name[25];
	strcpy(name, "buf_");
	strcpy(name + 4, source->id.name);

	sound = alloc_libblock(&CTX_data_main(C)->sound, ID_SO, name);

	sound->child_sound = source;
	sound->type = SOUND_TYPE_BUFFER;

	sound_load(sound);

	if(!sound->snd_sound)
	{
		free_libblock(&CTX_data_main(C)->sound, sound);
		sound = NULL;
	}

	return sound;
}

struct bSound* sound_new_limiter(struct bContext *C, struct bSound *source, float start, float end)
{
	bSound* sound = NULL;

	char name[25];
	strcpy(name, "lim_");
	strcpy(name + 4, source->id.name);

	sound = alloc_libblock(&CTX_data_main(C)->sound, ID_SO, name);

	sound->child_sound = source;
	sound->start = start;
	sound->end = end;
	sound->type = SOUND_TYPE_LIMITER;

	sound_load(sound);

	if(!sound->snd_sound)
	{
		free_libblock(&CTX_data_main(C)->sound, sound);
		sound = NULL;
	}

	return sound;
}
#endif

void sound_delete(struct bContext *C, struct bSound* sound)
{
	if(sound)
	{
		sound_free(sound);

		sound_unlink(C, sound);

		free_libblock(&CTX_data_main(C)->sound, sound);
	}
}

void sound_cache(struct bSound* sound, int ignore)
{
	if(sound->cache && !ignore)
		AUD_unload(sound->cache);

	sound->cache = AUD_bufferSound(sound->snd_sound);
}

void sound_load(struct bSound* sound)
{
	if(sound)
	{
		if(sound->snd_sound)
		{
			AUD_unload(sound->snd_sound);
			sound->snd_sound = NULL;
		}

		switch(sound->type)
		{
		case SOUND_TYPE_FILE:
		{
			char fullpath[FILE_MAX];
			char *path;

			/* load sound */
			PackedFile* pf = sound->packedfile;

			/* dont modify soundact->sound->name, only change a copy */
			BLI_strncpy(fullpath, sound->name, sizeof(fullpath));

			if(sound->id.lib)
				path = sound->id.lib->filename;
			else
				path = G.sce;

			BLI_convertstringcode(fullpath, path);

			/* but we need a packed file then */
			if (pf)
				sound->snd_sound = AUD_loadBuffer((unsigned char*) pf->data, pf->size);
			/* or else load it from disk */
			else
				sound->snd_sound = AUD_load(fullpath);
			break;
		}
		case SOUND_TYPE_BUFFER:
			if(sound->child_sound && sound->child_sound->snd_sound)
				sound->snd_sound = AUD_bufferSound(sound->child_sound->snd_sound);
			break;
		case SOUND_TYPE_LIMITER:
			if(sound->child_sound && sound->child_sound->snd_sound)
				sound->snd_sound = AUD_limitSound(sound->child_sound, sound->start, sound->end);
			break;
		}

		if(sound->cache)
		{

		}
	}
}

void sound_free(struct bSound* sound)
{
	if (sound->packedfile)
	{
		freePackedFile(sound->packedfile);
		sound->packedfile = NULL;
	}

	if(sound->snd_sound)
	{
		AUD_unload(sound->snd_sound);
		sound->snd_sound = NULL;
	}
}

void sound_unlink(struct bContext *C, struct bSound* sound)
{
	bSound *snd;
	Scene *scene;
	SoundHandle *handle;

	for(snd = CTX_data_main(C)->sound.first; snd; snd = snd->id.next)
	{
		if(snd->child_sound == sound)
		{
			snd->child_sound = NULL;
			if(snd->snd_sound)
			{
				AUD_unload(sound->snd_sound);
				snd->snd_sound = NULL;
			}

			sound_unlink(C, snd);
		}
	}

	for(scene = CTX_data_main(C)->scene.first; scene; scene = scene->id.next)
	{
		for(handle = scene->sound_handles.first; handle; handle = handle->next)
		{
			if(handle->source == sound)
			{
				handle->source = NULL;
				if(handle->handle)
					AUD_stop(handle->handle);
			}
		}
	}
}

struct SoundHandle* sound_new_handle(struct Scene *scene, struct bSound* sound, int startframe, int endframe, int frameskip)
{
	ListBase* handles = &scene->sound_handles;

	SoundHandle* handle = MEM_callocN(sizeof(SoundHandle), "sound_handle");
	handle->source = sound;
	handle->startframe = startframe;
	handle->endframe = endframe;
	handle->frameskip = frameskip;
	handle->state = AUD_STATUS_INVALID;
	handle->volume = 1.0f;

	BLI_addtail(handles, handle);

	return handle;
}

void sound_delete_handle(struct Scene *scene, struct SoundHandle *handle)
{
	if(handle == NULL)
		return;

	if(handle->handle)
		AUD_stop(handle->handle);

	BLI_freelinkN(&scene->sound_handles, handle);
}

void sound_stop_all(struct bContext *C)
{
	SoundHandle *handle;

	for(handle = CTX_data_scene(C)->sound_handles.first; handle; handle = handle->next)
	{
		if(handle->state == AUD_STATUS_PLAYING)
		{
			AUD_pause(handle->handle);
			handle->state = AUD_STATUS_PAUSED;
		}
	}
}

void sound_update_playing(struct bContext *C)
{
	SoundHandle *handle;
	Scene* scene = CTX_data_scene(C);
	int cfra = CFRA;
	float fps = FPS;
	int action;

	AUD_lock();

	for(handle = scene->sound_handles.first; handle; handle = handle->next)
	{
		if(cfra < handle->startframe || cfra >= handle->endframe || handle->mute)
		{
			if(handle->state == AUD_STATUS_PLAYING)
			{
				AUD_pause(handle->handle);
				handle->state = AUD_STATUS_PAUSED;
			}
		}
		else
		{
			action = 0;

			if(handle->changed != handle->source->changed)
			{
				handle->changed = handle->source->changed;
				action = 3;
				if(handle->state != AUD_STATUS_INVALID)
				{
					AUD_stop(handle->handle);
					handle->state = AUD_STATUS_INVALID;
				}
			}
			else
			{
				if(handle->state != AUD_STATUS_PLAYING)
					action = 3;
				else
				{
					handle->state = AUD_getStatus(handle->handle);
					if(handle->state != AUD_STATUS_PLAYING)
						action = 3;
					else
					{
						float diff = AUD_getPosition(handle->handle) * fps - cfra + handle->startframe;
						if(diff < 0.0)
							diff = -diff;
						if(diff > 1.0f)
						{
							action = 2;
						}
					}
				}
			}

			if(action & 1)
			{
				if(handle->state == AUD_STATUS_INVALID)
				{
					if(handle->source && handle->source->snd_sound)
					{
						AUD_Sound* limiter = AUD_limitSound(handle->source->cache ? handle->source->cache : handle->source->snd_sound, handle->frameskip / fps, (handle->frameskip + handle->endframe - handle->startframe)/fps);
						handle->handle = AUD_play(limiter, 1);
						AUD_unload(limiter);
						if(handle->handle)
							handle->state = AUD_STATUS_PLAYING;
						if(cfra == handle->startframe)
							action &= ~2;
					}
				}
				else
					if(AUD_resume(handle->handle))
						handle->state = AUD_STATUS_PLAYING;
					else
						handle->state = AUD_STATUS_INVALID;
			}

			if(action & 2)
				AUD_seek(handle->handle, (cfra - handle->startframe) / fps);
		}
	}

	AUD_unlock();
}

void sound_scrub(struct bContext *C)
{
	SoundHandle *handle;
	Scene* scene = CTX_data_scene(C);
	int cfra = CFRA;
	float fps = FPS;

	if(scene->r.audio.flag & AUDIO_SCRUB && !CTX_wm_screen(C)->animtimer)
	{
		AUD_lock();

		for(handle = scene->sound_handles.first; handle; handle = handle->next)
		{
			if(cfra >= handle->startframe && cfra < handle->endframe && !handle->mute)
			{
				if(handle->source && handle->source->snd_sound)
				{
					int frameskip = handle->frameskip + cfra - handle->startframe;
					AUD_Sound* limiter = AUD_limitSound(handle->source->cache ? handle->source->cache : handle->source->snd_sound, frameskip / fps, (frameskip + 1)/fps);
					AUD_play(limiter, 0);
					AUD_unload(limiter);
				}
			}
		}

		AUD_unlock();
	}
}

AUD_Device* sound_mixdown(struct Scene *scene, AUD_Specs specs, int start, int end)
{
	AUD_Device* mixdown = AUD_openReadDevice(specs);
	SoundHandle *handle;
	float fps = FPS;
	AUD_Sound *limiter, *delayer;
	int frameskip, s, e;

	end++;

	for(handle = scene->sound_handles.first; handle; handle = handle->next)
	{
		if(start < handle->endframe && end > handle->startframe && !handle->mute && handle->source && handle->source->snd_sound)
		{
			frameskip = handle->frameskip;
			s = handle->startframe - start;
			e = handle->frameskip + AUD_MIN(handle->endframe, end) - handle->startframe;

			if(s < 0)
			{
				frameskip -= s;
				s = 0;
			}

			limiter = AUD_limitSound(handle->source->snd_sound, frameskip / fps, e / fps);
			delayer = AUD_delaySound(limiter, s / fps);

			AUD_playDevice(mixdown, delayer);

			AUD_unload(delayer);
			AUD_unload(limiter);
		}
	}

	return mixdown;
}
