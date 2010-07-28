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

#ifndef AUD_BUTTERWORTHREADER
#define AUD_BUTTERWORTHREADER

#include "AUD_EffectReader.h"
#include "AUD_Buffer.h"

/**
 * This class represents a butterworth filter.
 */
class AUD_ButterworthReader : public AUD_EffectReader
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
	float m_coeff[2][5];

	// hide copy constructor and operator=
	AUD_ButterworthReader(const AUD_ButterworthReader&);
	AUD_ButterworthReader& operator=(const AUD_ButterworthReader&);

public:
	/**
	 * Creates a new butterworth reader.
	 * \param reader The reader to read from.
	 * \param attack The attack value in seconds.
	 * \param release The release value in seconds.
	 * \param threshold The threshold value.
	 * \param arthreshold The attack/release threshold value.
	 */
	AUD_ButterworthReader(AUD_IReader* reader, float frequency);

	virtual void read(int & length, sample_t* & buffer);
};

#endif //AUD_BUTTERWORTHREADER
