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

#ifndef AUD_LOWPASSFACTORY
#define AUD_LOWPASSFACTORY

#include "AUD_EffectFactory.h"

/**
 * This factory creates a lowpass filter reader.
 */
class AUD_LowpassFactory : public AUD_EffectFactory
{
private:
	/**
	 * The attack value in seconds.
	 */
	const float m_frequency;

	/**
	 * The Q factor.
	 */
	const float m_Q;

	// hide copy constructor and operator=
	AUD_LowpassFactory(const AUD_LowpassFactory&);
	AUD_LowpassFactory& operator=(const AUD_LowpassFactory&);

public:
	/**
	 * Creates a new lowpass factory.
	 * \param factory The input factory.
	 * \param frequency The cutoff frequency.
	 * \param Q The Q factor.
	 */
	AUD_LowpassFactory(AUD_IFactory* factory, float frequency, float Q = 1.0f);

	virtual AUD_IReader* createReader() const;
};

#endif //AUD_LOWPASSFACTORY
