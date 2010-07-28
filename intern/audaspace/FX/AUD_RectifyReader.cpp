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

#include "AUD_RectifyReader.h"

#include <cmath>

AUD_RectifyReader::AUD_RectifyReader(AUD_IReader* reader) :
		AUD_EffectReader(reader)
{
}

void AUD_RectifyReader::read(int & length, sample_t* & buffer)
{
	sample_t* buf;
	AUD_Specs specs = m_reader->getSpecs();

	m_reader->read(length, buf);
	if(m_buffer.getSize() < length * AUD_SAMPLE_SIZE(specs))
		m_buffer.resize(length * AUD_SAMPLE_SIZE(specs));

	buffer = m_buffer.getBuffer();

	for(int i = 0; i < length * specs.channels; i++)
		buffer[i] = fabs(buf[i]);
}
