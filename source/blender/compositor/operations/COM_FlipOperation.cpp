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

#include "COM_FlipOperation.h"

FlipOperation::FlipOperation() : NodeOperation()
{
	this->addInputSocket(COM_DT_COLOR);
	this->addOutputSocket(COM_DT_COLOR);
	this->setResolutionInputSocketIndex(0);
	this->m_inputOperation = NULL;
	this->m_flipX = true;
	this->m_flipY = false;
}
void FlipOperation::initExecution()
{
	this->m_inputOperation = this->getInputSocketReader(0);
}

void FlipOperation::deinitExecution()
{
	this->m_inputOperation = NULL;
}


void FlipOperation::executePixel(float *color, float x, float y, PixelSampler sampler)
{
	float nx = this->m_flipX ? this->getWidth() - 1 - x : x;
	float ny = this->m_flipY ? this->getHeight() - 1 - y : y;
	
	this->m_inputOperation->read(color, nx, ny, sampler);
}

bool FlipOperation::determineDependingAreaOfInterest(rcti *input, ReadBufferOperation *readOperation, rcti *output)
{
	rcti newInput;
	
	if (this->m_flipX) {
		newInput.xmax = (this->getWidth() - 1 - input->xmin) + 1;
		newInput.xmin = (this->getWidth() - 1 - input->xmax) - 1;
	}
	else {
		newInput.xmin = input->xmin;
		newInput.xmax = input->xmax;
	}
	if (this->m_flipY) {
		newInput.ymax = (this->getHeight() - 1 - input->ymin) + 1;
		newInput.ymin = (this->getHeight() - 1 - input->ymax) - 1;
	}
	else {
		newInput.ymin = input->ymin;
		newInput.ymax = input->ymax;
	}
	
	return NodeOperation::determineDependingAreaOfInterest(&newInput, readOperation, output);
}
