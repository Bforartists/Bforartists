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

#ifndef AUD_SDLDEVICE
#define AUD_SDLDEVICE

#include "AUD_SoftwareDevice.h"

/**
 * This device plays back through SDL, the simple direct media layer.
 */
class AUD_SDLDevice : public AUD_SoftwareDevice
{
protected:
	virtual void playing(bool playing);

public:
	/**
	 * Opens the SDL audio device for playback.
	 * \param specs The wanted audio specification.
	 * \param buffersize The size of the internal buffer.
	 * \note The specification really used for opening the device may differ.
	 * \exception AUD_Exception Thrown if the audio device cannot be opened.
	 */
	AUD_SDLDevice(AUD_Specs specs, int buffersize = AUD_DEFAULT_BUFFER_SIZE);

	/**
	 * Closes the SDL audio device.
	 */
	virtual ~AUD_SDLDevice();

	/**
	 * Mixes the next bytes into the buffer.
	 * \param buffer The target buffer.
	 * \param length The length in bytes to be filled.
	 * \warning This function shall not be called from outside!
	 */
	void SDLmix(sample_t* buffer, int length);
};

#endif //AUD_SDLDEVICE
