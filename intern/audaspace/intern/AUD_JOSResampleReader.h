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

/** \file audaspace/intern/AUD_JOSResampleReader.h
 *  \ingroup audaspaceintern
 */


#ifndef AUD_JOSRESAMPLEREADER
#define AUD_JOSRESAMPLEREADER

#include "AUD_ResampleReader.h"
#include "AUD_Buffer.h"

/**
 * This resampling reader uses Julius O. Smith's resampling algorithm.
 */
class AUD_JOSResampleReader : public AUD_ResampleReader
{
private:
	typedef void (AUD_JOSResampleReader::*AUD_resample_f)(double target_factor, int length, sample_t* buffer);

	static const int m_len = 292874;
	static const int m_L = 2048;
	static const float m_coeff[];

	/**
	 * The reader channels.
	 */
	AUD_Channels m_channels;

	/**
	 * The sample position in the cache.
	 */
	unsigned int m_n;

	/**
	 * The subsample position in the cache.
	 */
	double m_P;

	/**
	 * The input data buffer.
	 */
	AUD_Buffer m_buffer;

	/**
	 * Double buffer for the sums.
	 */
	AUD_Buffer m_sums;

	/**
	 * How many samples in the cache are valid.
	 */
	int m_cache_valid;

	/**
	 * Resample function.
	 */
	AUD_resample_f m_resample;

	/**
	 * Last resampling factor.
	 */
	double m_last_factor;

	// hide copy constructor and operator=
	AUD_JOSResampleReader(const AUD_JOSResampleReader&);
	AUD_JOSResampleReader& operator=(const AUD_JOSResampleReader&);

	void reset();

	void updateBuffer(int size, double factor, int samplesize);

	void resample(double target_factor, int length, sample_t* buffer);
	void resample_mono(double target_factor, int length, sample_t* buffer);
	void resample_stereo(double target_factor, int length, sample_t* buffer);

public:
	/**
	 * Creates a resampling reader.
	 * \param reader The reader to mix.
	 * \param specs The target specification.
	 */
	AUD_JOSResampleReader(AUD_Reference<AUD_IReader> reader, AUD_Specs specs);

	virtual void seek(int position);
	virtual int getLength() const;
	virtual int getPosition() const;
	virtual AUD_Specs getSpecs() const;
	virtual void read(int& length, bool& eos, sample_t* buffer);
};

#endif //AUD_JOSRESAMPLEREADER
