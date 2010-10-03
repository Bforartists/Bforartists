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

#ifndef AUD_PITCHREADER
#define AUD_PITCHREADER

#include "AUD_EffectReader.h"

/**
 * This class reads another reader and changes it's pitch.
 */
class AUD_PitchReader : public AUD_EffectReader
{
private:
	/**
	 * The pitch level.
	 */
	const float m_pitch;

	// hide copy constructor and operator=
	AUD_PitchReader(const AUD_PitchReader&);
	AUD_PitchReader& operator=(const AUD_PitchReader&);

public:
	/**
	 * Creates a new pitch reader.
	 * \param reader The reader to read from.
	 * \param pitch The size of the buffer.
	 */
	AUD_PitchReader(AUD_IReader* reader, float pitch);

	virtual AUD_Specs getSpecs() const;
};

#endif //AUD_PITCHREADER
