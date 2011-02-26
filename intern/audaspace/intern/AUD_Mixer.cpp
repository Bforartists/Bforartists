/*
 * $Id$
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * Copyright 2009-2011 Jörg Hermann Müller
 *
 * This file is part of AudaSpace.
 *
 * Audaspace is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * AudaSpace is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Audaspace; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file audaspace/intern/AUD_Mixer.cpp
 *  \ingroup audaspaceintern
 */


#include "AUD_Mixer.h"
#include "AUD_IReader.h"

#include <cstring>

AUD_Mixer::AUD_Mixer(AUD_DeviceSpecs specs) :
	m_specs(specs)
{
	int bigendian = 1;
	bigendian = (((char*)&bigendian)[0]) ? 0: 1; // 1 if Big Endian

	switch(m_specs.format)
	{
	case AUD_FORMAT_U8:
		m_convert = AUD_convert_float_u8;
		break;
	case AUD_FORMAT_S16:
		m_convert = AUD_convert_float_s16;
		break;
	case AUD_FORMAT_S24:
		if(bigendian)
			m_convert = AUD_convert_float_s24_be;
		else
			m_convert = AUD_convert_float_s24_le;
		break;
	case AUD_FORMAT_S32:
		m_convert = AUD_convert_float_s32;
		break;
	case AUD_FORMAT_FLOAT32:
		m_convert = AUD_convert_copy<float>;
		break;
	case AUD_FORMAT_FLOAT64:
		m_convert = AUD_convert_float_double;
		break;
	default:
		break;
	}
}

AUD_DeviceSpecs AUD_Mixer::getSpecs() const
{
	return m_specs;
}

void AUD_Mixer::add(sample_t* buffer, int start, int length, float volume)
{
	AUD_MixerBuffer buf;
	buf.buffer = buffer;
	buf.start = start;
	buf.length = length;
	buf.volume = volume;
	m_buffers.push_back(buf);
}

void AUD_Mixer::superpose(data_t* buffer, int length, float volume)
{
	AUD_MixerBuffer buf;

	int channels = m_specs.channels;

	if(m_buffer.getSize() < length * channels * 4)
		m_buffer.resize(length * channels * 4);

	sample_t* out = m_buffer.getBuffer();
	sample_t* in;

	memset(out, 0, length * channels * 4);

	int end;

	while(!m_buffers.empty())
	{
		buf = m_buffers.front();
		m_buffers.pop_front();

		end = buf.length * channels;
		in = buf.buffer;

		for(int i = 0; i < end; i++)
			out[i + buf.start * channels] += in[i] * buf.volume * volume;
	}

	m_convert(buffer, (data_t*) out, length * channels);
}
