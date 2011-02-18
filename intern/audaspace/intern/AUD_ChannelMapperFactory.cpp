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

#include "AUD_ChannelMapperFactory.h"
#include "AUD_ChannelMapperReader.h"

#include <cstring>

AUD_ChannelMapperFactory::AUD_ChannelMapperFactory(AUD_IFactory* factory,
												   AUD_DeviceSpecs specs) :
		AUD_MixerFactory(factory, specs)
{
	memset(m_mapping, 0, sizeof(m_mapping));
}

AUD_ChannelMapperFactory::~AUD_ChannelMapperFactory()
{
	for(int i = 1; i < 10; i++)
		deleteMapping(i);
}

float** AUD_ChannelMapperFactory::getMapping(int ic)
{
	ic--;
	if(ic > 8 || ic < 0)
		return 0;

	if(m_mapping[ic])
	{
		int channels = -1;
		while(m_mapping[ic][++channels] != 0);
		if(channels != m_specs.channels)
			deleteMapping(ic+1);
	}

	if(!m_mapping[ic])
	{
		int channels = m_specs.channels;

		m_mapping[ic] = new float*[channels+1];
		m_mapping[ic][channels] = 0;

		for(int i = 0; i < channels; i++)
		{
			m_mapping[ic][i] = new float[ic+1];
			for(int j = 0; j <= ic; j++)
				m_mapping[ic][i][j] = ((i == j) || (channels == 1) ||
									   (ic == 0)) ? 1.0f : 0.0f;
		}
	}

	return m_mapping[ic];
}

void AUD_ChannelMapperFactory::deleteMapping(int ic)
{
	ic--;
	if(ic > 8 || ic < 0)
		return;

	if(m_mapping[ic])
	{
		for(int i = 0; 1; i++)
		{
			if(m_mapping[ic][i] != 0)
			{
				delete[] m_mapping[ic][i];
			}
			else
				break;
		}
		delete[] m_mapping[ic];
		m_mapping[ic] = 0;
	}
}

AUD_IReader* AUD_ChannelMapperFactory::createReader() const
{
	AUD_IReader* reader = getReader();
	int ic = reader->getSpecs().channels;

	return new AUD_ChannelMapperReader(reader,
				   const_cast<AUD_ChannelMapperFactory*>(this)->getMapping(ic));
}
