/*
 * $Id: AUD_HighpassFactory.cpp 25643 2010-01-01 05:09:30Z nexyon $
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

#include "AUD_HighpassFactory.h"
#include "AUD_HighpassReader.h"

AUD_HighpassFactory::AUD_HighpassFactory(AUD_IFactory* factory, float frequency,
										 float Q) :
		AUD_EffectFactory(factory),
		m_frequency(frequency),
		m_Q(Q) {}

AUD_HighpassFactory::AUD_HighpassFactory(float frequency, float Q) :
		AUD_EffectFactory(0),
		m_frequency(frequency),
		m_Q(Q) {}

AUD_IReader* AUD_HighpassFactory::createReader()
{
	AUD_IReader* reader = getReader();

	if(reader != 0)
	{
		reader = new AUD_HighpassReader(reader, m_frequency, m_Q);
		AUD_NEW("reader")
	}

	return reader;
}
