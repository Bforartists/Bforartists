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

#include "AUD_SuperposeFactory.h"
#include "AUD_SuperposeReader.h"

AUD_SuperposeFactory::AUD_SuperposeFactory(AUD_IFactory* factory1, AUD_IFactory* factory2) :
		m_factory1(factory1), m_factory2(factory2) {}

AUD_IReader* AUD_SuperposeFactory::createReader()
{
	AUD_IReader* reader1 = m_factory1->createReader();
	if(!reader1)
		return 0;
	AUD_IReader* reader2;
	try
	{
		reader2 = m_factory2->createReader();
		if(!reader2)
		{
			delete reader1; AUD_DELETE("reader")
			return 0;
		}
	}
	catch(AUD_Exception&)
	{
		delete reader1; AUD_DELETE("reader")
		throw;
	}

	AUD_IReader* reader = new AUD_SuperposeReader(reader1, reader2);
	return reader;
}
