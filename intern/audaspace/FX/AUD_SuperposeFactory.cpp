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

/** \file audaspace/FX/AUD_SuperposeFactory.cpp
 *  \ingroup audfx
 */


#include "AUD_SuperposeFactory.h"
#include "AUD_SuperposeReader.h"

AUD_SuperposeFactory::AUD_SuperposeFactory(AUD_IFactory* factory1, AUD_IFactory* factory2) :
		m_factory1(factory1), m_factory2(factory2)
{
}

AUD_IReader* AUD_SuperposeFactory::createReader() const
{
	AUD_IReader* reader1 = m_factory1->createReader();
	AUD_IReader* reader2;
	try
	{
		reader2 = m_factory2->createReader();
	}
	catch(AUD_Exception&)
	{
		delete reader1;
		throw;
	}

	return new AUD_SuperposeReader(reader1, reader2);
}
