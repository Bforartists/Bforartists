
/*
 * Copyright 2013, Blender Foundation.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * Contributor:
 *		Sergey Sharybin
 */

#ifndef _COM_PlaneTrackWarpImageOperation_h
#define _COM_PlaneTrackWarpImageOperation_h

#include <string.h>

#include "COM_PlaneTrackCommonOperation.h"

#include "DNA_movieclip_types.h"
#include "DNA_tracking_types.h"

#include "BLI_listbase.h"
#include "BLI_string.h"

class PlaneTrackWarpImageOperation : public PlaneTrackCommonOperation {
protected:
	SocketReader *m_pixelReader;
	int m_osa;
	float m_jitter[32][2];

public:
	PlaneTrackWarpImageOperation();

	void initExecution();
	void deinitExecution();

	void executePixel(float output[4], float x, float y, PixelSampler sampler);

	bool determineDependingAreaOfInterest(rcti *input, ReadBufferOperation *readOperation, rcti *output);
};

#endif
