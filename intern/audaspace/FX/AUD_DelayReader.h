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

/** \file audaspace/FX/AUD_DelayReader.h
 *  \ingroup audfx
 */


#ifndef AUD_DELAYREADER
#define AUD_DELAYREADER

#include "AUD_EffectReader.h"
#include "AUD_Buffer.h"

/**
 * This class reads another reader and changes it's delay.
 */
class AUD_DelayReader : public AUD_EffectReader
{
private:
	/**
	 * The playback buffer.
	 */
	AUD_Buffer m_buffer;

	/**
	 * The delay level.
	 */
	const int m_delay;

	/**
	 * The remaining delay for playback.
	 */
	int m_remdelay;

	/**
	 * Whether the buffer is currently filled with zeros.
	 */
	bool m_empty;

	// hide copy constructor and operator=
	AUD_DelayReader(const AUD_DelayReader&);
	AUD_DelayReader& operator=(const AUD_DelayReader&);

public:
	/**
	 * Creates a new delay reader.
	 * \param reader The reader to read from.
	 * \param delay The delay in seconds.
	 */
	AUD_DelayReader(AUD_IReader* reader, float delay);

	virtual void seek(int position);
	virtual int getLength() const;
	virtual int getPosition() const;
	virtual void read(int & length, sample_t* & buffer);
};

#endif //AUD_DELAYREADER
