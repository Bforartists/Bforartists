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

/** \file audaspace/intern/AUD_Mixer.h
 *  \ingroup audaspaceintern
 */


#ifndef AUD_MIXER
#define AUD_MIXER

#include "AUD_ConverterFunctions.h"
#include "AUD_Buffer.h"
#include "AUD_Reference.h"
class AUD_IReader;

/**
 * This abstract class is able to mix audiosignals of different channel count
 * and sample rate and convert it to a specific output format.
 */
class AUD_Mixer
{
protected:
	/**
	 * The output specification.
	 */
	const AUD_DeviceSpecs m_specs;

	/**
	 * The length of the mixing buffer.
	 */
	int m_length;

	/**
	 * The mixing buffer.
	 */
	AUD_Buffer m_buffer;

	/**
	 * Converter function.
	 */
	AUD_convert_f m_convert;

public:
	/**
	 * Creates the mixer.
	 */
	AUD_Mixer(AUD_DeviceSpecs specs);

	/**
	 * Destroys the mixer.
	 */
	virtual ~AUD_Mixer() {}

	/**
	 * Returns the target specification for superposing.
	 * \return The target specification.
	 */
	AUD_DeviceSpecs getSpecs() const;

	/**
	 * Mixes a buffer.
	 * \param buffer The buffer to superpose.
	 * \param start The start sample of the buffer.
	 * \param length The length of the buffer in samples.
	 * \param volume The mixing volume. Must be a value between 0.0 and 1.0.
	 */
	void mix(sample_t* buffer, int start, int length, float volume);

	/**
	 * Writes the mixing buffer into an output buffer.
	 * \param buffer The target buffer for superposing.
	 * \param volume The mixing volume. Must be a value between 0.0 and 1.0.
	 */
	void read(data_t* buffer, float volume);

	/**
	 * Clears the mixing buffer.
	 * \param length The length of the buffer in samples.
	 */
	void clear(int length);
};

#endif //AUD_MIXER
