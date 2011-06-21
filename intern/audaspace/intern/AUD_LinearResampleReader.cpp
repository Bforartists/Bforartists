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

/** \file audaspace/intern/AUD_LinearResampleReader.cpp
 *  \ingroup audaspaceintern
 */


#include "AUD_LinearResampleReader.h"

#include <cmath>
#include <cstring>

#define CC channels + channel

AUD_LinearResampleReader::AUD_LinearResampleReader(AUD_Reference<AUD_IReader> reader,
												   AUD_Specs specs) :
	AUD_EffectReader(reader),
	m_sspecs(reader->getSpecs()),
	m_factor(float(specs.rate) / float(m_sspecs.rate)),
	m_tspecs(specs),
	m_position(0),
	m_sposition(0)
{
	m_tspecs.channels = m_sspecs.channels;
	m_cache.resize(2 * AUD_SAMPLE_SIZE(m_tspecs));
}

void AUD_LinearResampleReader::seek(int position)
{
	m_position = position;
	m_sposition = floor(position / m_factor);
	m_reader->seek(m_sposition);
}

int AUD_LinearResampleReader::getLength() const
{
	return m_reader->getLength() * m_factor;
}

int AUD_LinearResampleReader::getPosition() const
{
	return m_position;
}

AUD_Specs AUD_LinearResampleReader::getSpecs() const
{
	return m_tspecs;
}

void AUD_LinearResampleReader::read(int & length, sample_t* buffer)
{
	int samplesize = AUD_SAMPLE_SIZE(m_tspecs);
	int size = length * AUD_SAMPLE_SIZE(m_sspecs);

	m_buffer.assureSize(size);

	int need = ceil((m_position + length) / m_factor) + 1 - m_sposition;
	int len = need;
	sample_t* buf = m_buffer.getBuffer();

	m_reader->read(len, buf);

	if(len < need)
		length = floor((m_sposition + len - 1) * m_factor) - m_position;

	float spos;
	sample_t low, high;
	int channels = m_sspecs.channels;

	for(int channel = 0; channel < channels; channel++)
	{
		for(int i = 0; i < length; i++)
		{
			spos = (m_position + i) / m_factor - m_sposition;

			if(floor(spos) < 0)
			{
				low = m_cache.getBuffer()[(int)(floor(spos) + 2) * CC];
				if(ceil(spos) < 0)
					high = m_cache.getBuffer()[(int)(ceil(spos) + 2) * CC];
				else
					high = buf[(int)ceil(spos) * CC];
			}
			else
			{
					low = buf[(int)floor(spos) * CC];
					high = buf[(int)ceil(spos) * CC];
			}
			buffer[i * CC] = low + (spos - floor(spos)) * (high - low);
		}
	}

	if(len > 1)
		memcpy(m_cache.getBuffer(),
			   buf + (len - 2) * channels,
			   2 * samplesize);
	else if(len == 1)
		memcpy(m_cache.getBuffer() + 1 * channels, buf, samplesize);

	m_sposition += len;
	m_position += length;
}
