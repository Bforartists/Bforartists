/*
 * $Id$
 *
 * ***** BEGIN LGPL LICENSE BLOCK *****
 *
 * Copyright 2009 Jörg Hermann Müller
 *
 * This file is part of AudaSpace.
 *
 * AudaSpace is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * AudaSpace is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with AudaSpace.  If not, see <http://www.gnu.org/licenses/>.
 *
 * ***** END LGPL LICENSE BLOCK *****
 */

#include "AUD_SDLMixer.h"
#include "AUD_SDLDevice.h"
#include "AUD_IReader.h"

#include <SDL.h>

// this is the callback function for SDL, it only calls the class
void mixAudio(void *data, Uint8* buffer, int length)
{
	AUD_SDLDevice* device = (AUD_SDLDevice*)data;
	device->SDLmix((sample_t *)buffer, length);
}

AUD_SDLDevice::AUD_SDLDevice(AUD_Specs specs, int buffersize)
{
	if(specs.channels == AUD_CHANNELS_INVALID)
		specs.channels = AUD_CHANNELS_STEREO;
	if(specs.format == AUD_FORMAT_INVALID)
		specs.format = AUD_FORMAT_S16;
	if(specs.rate == AUD_RATE_INVALID)
		specs.rate = AUD_RATE_44100;

	m_specs = specs;

	SDL_AudioSpec format, obtained;

	format.freq = m_specs.rate;
	if(m_specs.format == AUD_FORMAT_U8)
		format.format = AUDIO_U8;
	else
		format.format = AUDIO_S16SYS;
	format.channels = m_specs.channels;
	format.samples = buffersize;
	format.callback = &mixAudio;
	format.userdata = this;

	if(SDL_OpenAudio(&format, &obtained) != 0)
		AUD_THROW(AUD_ERROR_SDL);

	m_specs.rate = (AUD_SampleRate)obtained.freq;
	m_specs.channels = (AUD_Channels)obtained.channels;
	if(obtained.format == AUDIO_U8)
		m_specs.format = AUD_FORMAT_U8;
	else if(obtained.format == AUDIO_S16LSB || obtained.format == AUDIO_S16MSB)
		m_specs.format = AUD_FORMAT_S16;
	else
		AUD_THROW(AUD_ERROR_SDL);

	m_mixer = new AUD_SDLMixer(); AUD_NEW("mixer")
	m_mixer->setSpecs(m_specs);

	create();
}

AUD_SDLDevice::~AUD_SDLDevice()
{
	lock();
	SDL_CloseAudio();
	unlock();

	destroy();
}

void AUD_SDLDevice::SDLmix(sample_t* buffer, int length)
{
	mix(buffer, length/AUD_SAMPLE_SIZE(m_specs));
}

void AUD_SDLDevice::playing(bool playing)
{
	SDL_PauseAudio(playing ? 0 : 1);
}
