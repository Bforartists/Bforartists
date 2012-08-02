/*
 * Copyright 2011, Blender Foundation.
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
 *		Jeroen Bakker 
 *		Monique Dewanchand
 */

#include "COM_ViewerOperation.h"
#include "COM_SocketConnection.h"
#include "BLI_listbase.h"
#include "BKE_image.h"
#include "WM_api.h"
#include "WM_types.h"
#include "PIL_time.h"
#include "BLI_utildefines.h"
#include "BLI_math_color.h"
#include "BLI_math_vector.h"

extern "C" {
	#include "MEM_guardedalloc.h"
	#include "IMB_imbuf.h"
	#include "IMB_imbuf_types.h"
}


ViewerOperation::ViewerOperation() : ViewerBaseOperation()
{
	this->addInputSocket(COM_DT_COLOR);
	this->addInputSocket(COM_DT_VALUE);
	this->addInputSocket(COM_DT_VALUE);

	this->m_imageInput = NULL;
	this->m_alphaInput = NULL;
	this->m_depthInput = NULL;
}

void ViewerOperation::initExecution()
{
	// When initializing the tree during initial load the width and height can be zero.
	this->m_imageInput = getInputSocketReader(0);
	this->m_alphaInput = getInputSocketReader(1);
	this->m_depthInput = getInputSocketReader(2);
	this->m_doDepthBuffer = (this->m_depthInput != NULL);
	ViewerBaseOperation::initExecution();
}

void ViewerOperation::deinitExecution()
{
	this->m_imageInput = NULL;
	this->m_alphaInput = NULL;
	this->m_depthInput = NULL;
	ViewerBaseOperation::deinitExecution();
}


void ViewerOperation::executeRegion(rcti *rect, unsigned int tileNumber)
{
	float *buffer = this->m_outputBuffer;
	float *depthbuffer = this->m_depthBuffer;
	unsigned char *bufferDisplay = this->m_outputBufferDisplay;
	if (!buffer) return;
	const int x1 = rect->xmin;
	const int y1 = rect->ymin;
	const int x2 = rect->xmax;
	const int y2 = rect->ymax;
	const int offsetadd = (this->getWidth() - (x2 - x1));
	const int offsetadd4 = offsetadd * 4;
	int offset = (y1 * this->getWidth() + x1);
	int offset4 = offset * 4;
	float alpha[4], srgb[4], depth[4];
	int x;
	int y;
	bool breaked = false;

	for (y = y1; y < y2 && (!breaked); y++) {
		for (x = x1; x < x2; x++) {
			this->m_imageInput->read(&(buffer[offset4]), x, y, COM_PS_NEAREST);
			if (this->m_alphaInput != NULL) {
				this->m_alphaInput->read(alpha, x, y, COM_PS_NEAREST);
				buffer[offset4 + 3] = alpha[0];
			}
			if (m_depthInput) {
				this->m_depthInput->read(depth, x, y, COM_PS_NEAREST);
				depthbuffer[offset] = depth[0];
			} 
			if (this->m_doColorManagement) {
				if (this->m_doColorPredivide) {
					linearrgb_to_srgb_predivide_v4(srgb, buffer + offset4);
				}
				else {
					linearrgb_to_srgb_v4(srgb, buffer + offset4);
				}
			}
			else {
				copy_v4_v4(srgb, buffer + offset4);
			}

			rgba_float_to_uchar(bufferDisplay + offset4, srgb);

			offset ++;
			offset4 += 4;
		}
		if (isBreaked()) {
			breaked = true;
		}
		offset += offsetadd;
		offset4 += offsetadd4;
	}
	updateImage(rect);
}
