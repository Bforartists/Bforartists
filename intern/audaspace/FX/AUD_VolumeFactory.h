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

/** \file audaspace/FX/AUD_VolumeFactory.h
 *  \ingroup audfx
 */


#ifndef AUD_VOLUMEFACTORY
#define AUD_VOLUMEFACTORY

#include "AUD_EffectFactory.h"

/**
 * This factory changes the volume of another factory.
 * The set volume should be a value between 0.0 and 1.0, higher values at your
 * own risk!
 */
class AUD_VolumeFactory : public AUD_EffectFactory
{
private:
	/**
	 * The volume.
	 */
	const float m_volume;

	// hide copy constructor and operator=
	AUD_VolumeFactory(const AUD_VolumeFactory&);
	AUD_VolumeFactory& operator=(const AUD_VolumeFactory&);

public:
	/**
	 * Creates a new volume factory.
	 * \param factory The input factory.
	 * \param volume The desired volume.
	 */
	AUD_VolumeFactory(AUD_Reference<AUD_IFactory> factory, float volume);

	/**
	 * Returns the volume.
	 */
	float getVolume() const;

	virtual AUD_Reference<AUD_IReader> createReader();
};

#endif //AUD_VOLUMEFACTORY
