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

/** \file audaspace/FX/AUD_PingPongFactory.h
 *  \ingroup audfx
 */


#ifndef AUD_PINGPONGFACTORY
#define AUD_PINGPONGFACTORY

#include "AUD_EffectFactory.h"

/**
 * This factory plays another factory first normal, then reversed.
 * \note Readers from the underlying factory must be from the buffer type.
 */
class AUD_PingPongFactory : public AUD_EffectFactory
{
private:
	// hide copy constructor and operator=
	AUD_PingPongFactory(const AUD_PingPongFactory&);
	AUD_PingPongFactory& operator=(const AUD_PingPongFactory&);

public:
	/**
	 * Creates a new ping pong factory.
	 * \param factory The input factory.
	 */
	AUD_PingPongFactory(AUD_IFactory* factory);

	virtual AUD_IReader* createReader() const;
};

#endif //AUD_PINGPONGFACTORY
