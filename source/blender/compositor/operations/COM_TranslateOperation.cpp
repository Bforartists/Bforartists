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

#include "COM_TranslateOperation.h"

TranslateOperation::TranslateOperation() : NodeOperation()
{
	this->addInputSocket(COM_DT_COLOR);
	this->addInputSocket(COM_DT_VALUE);
	this->addInputSocket(COM_DT_VALUE);
	this->addOutputSocket(COM_DT_COLOR);
	this->setResolutionInputSocketIndex(0);
	this->m_inputOperation = NULL;
	this->m_inputXOperation = NULL;
	this->m_inputYOperation = NULL;
	this->m_isDeltaSet = false;
}
void TranslateOperation::initExecution()
{
	this->m_inputOperation = this->getInputSocketReader(0);
	this->m_inputXOperation = this->getInputSocketReader(1);
	this->m_inputYOperation = this->getInputSocketReader(2);

}

void TranslateOperation::deinitExecution()
{
	this->m_inputOperation = NULL;
	this->m_inputXOperation = NULL;
	this->m_inputYOperation = NULL;
}


void TranslateOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	ensureDelta();
	this->m_inputOperation->read(output, x - this->getDeltaX(), y - this->getDeltaY(), sampler);
}

bool TranslateOperation::determineDependingAreaOfInterest(rcti *input, ReadBufferOperation *readOperation, rcti *output)
{
	ensureDelta();
	rcti newInput;
	
	newInput.xmax = input->xmax - this->getDeltaX();
	newInput.xmin = input->xmin - this->getDeltaX();
	newInput.ymax = input->ymax - this->getDeltaY();
	newInput.ymin = input->ymin - this->getDeltaY();
	
	return NodeOperation::determineDependingAreaOfInterest(&newInput, readOperation, output);
}
