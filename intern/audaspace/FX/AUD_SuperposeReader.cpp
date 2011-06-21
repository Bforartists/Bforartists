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

/** \file audaspace/FX/AUD_SuperposeReader.cpp
 *  \ingroup audfx
 */


#include "AUD_SuperposeReader.h"

#include <cstring>

static const char* specs_error = "AUD_SuperposeReader: Both readers have to "
								 "have the same specs.";

AUD_SuperposeReader::AUD_SuperposeReader(AUD_Reference<AUD_IReader> reader1, AUD_Reference<AUD_IReader> reader2) :
	m_reader1(reader1), m_reader2(reader2)
{
	AUD_Specs s1, s2;
	s1 = reader1->getSpecs();
	s2 = reader2->getSpecs();
	if(memcmp(&s1, &s2, sizeof(AUD_Specs)))
		AUD_THROW(AUD_ERROR_SPECS, specs_error);
}

AUD_SuperposeReader::~AUD_SuperposeReader()
{
}

bool AUD_SuperposeReader::isSeekable() const
{
	return m_reader1->isSeekable() && m_reader2->isSeekable();
}

void AUD_SuperposeReader::seek(int position)
{
	m_reader1->seek(position);
	m_reader2->seek(position);
}

int AUD_SuperposeReader::getLength() const
{
	int len1 = m_reader1->getLength();
	int len2 = m_reader2->getLength();
	if((len1 < 0) || (len2 < 0))
		return -1;
	return AUD_MIN(len1, len2);
}

int AUD_SuperposeReader::getPosition() const
{
	int pos1 = m_reader1->getPosition();
	int pos2 = m_reader2->getPosition();
	return AUD_MAX(pos1, pos2);
}

AUD_Specs AUD_SuperposeReader::getSpecs() const
{
	return m_reader1->getSpecs();
}

void AUD_SuperposeReader::read(int & length, sample_t* buffer)
{
	AUD_Specs specs = m_reader1->getSpecs();
	int samplesize = AUD_SAMPLE_SIZE(specs);

	m_buffer.assureSize(length * samplesize);

	int len1 = length;
	m_reader1->read(len1, buffer);

	if(len1 < length)
		memset(buffer + len1 * specs.channels, 0, (length - len1) * samplesize);

	int len2 = length;
	sample_t* buf = m_buffer.getBuffer();
	m_reader2->read(len2, buf);

	for(int i = 0; i < len2 * specs.channels; i++)
		buffer[i] += buf[i];

	length = AUD_MAX(len1, len2);
}
