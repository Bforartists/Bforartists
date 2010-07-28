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

#ifndef AUD_HIGHPASSREADER
#define AUD_HIGHPASSREADER

#include "AUD_EffectReader.h"
#include "AUD_Buffer.h"

#define AUD_HIGHPASS_ORDER 3

/**
 * This class represents a highpass filter.
 */
class AUD_HighpassReader : public AUD_EffectReader
{
private:
	/**
	 * The playback buffer.
	 */
	AUD_Buffer m_buffer;

	/**
	 * The last out values buffer.
	 */
	AUD_Buffer m_outvalues;

	/**
	 * The last in values buffer.
	 */
	AUD_Buffer m_invalues;

	/**
	 * The position for buffer cycling.
	 */
	int m_position;

	/**
	 * Filter coefficients.
	 */
	float m_coeff[2][AUD_HIGHPASS_ORDER];

	// hide copy constructor and operator=
	AUD_HighpassReader(const AUD_HighpassReader&);
	AUD_HighpassReader& operator=(const AUD_HighpassReader&);

public:
	/**
	 * Creates a new highpass reader.
	 * \param reader The reader to read from.
	 * \param frequency The cutoff frequency.
	 * \param Q The Q factor.
	 */
	AUD_HighpassReader(AUD_IReader* reader, float frequency, float Q);

	virtual void read(int & length, sample_t* & buffer);
};

#endif //AUD_HIGHPASSREADER
