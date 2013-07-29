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

#include "COM_MixSoftLightOperation.h"

MixSoftLightOperation::MixSoftLightOperation() : MixBaseOperation()
{
	/* pass */
}

void MixSoftLightOperation::executePixel(float output[4], float x, float y, PixelSampler sampler) \
{
	float inputColor1[4];
	float inputColor2[4];
	float inputValue[4];
	
	this->m_inputValueOperation->read(inputValue, x, y, sampler);
	this->m_inputColor1Operation->read(inputColor1, x, y, sampler);
	this->m_inputColor2Operation->read(inputColor2, x, y, sampler);
	
	float value = inputValue[0];
	if (this->useValueAlphaMultiply()) {
		value *= inputColor2[3];
	}
	float valuem = 1.0f - value;
	float scr, scg, scb;
	
	/* first calculate non-fac based Screen mix */
	scr = 1.0f - (1.0f - inputColor2[0]) * (1.0f - inputColor1[0]);
	scg = 1.0f - (1.0f - inputColor2[1]) * (1.0f - inputColor1[1]);
	scb = 1.0f - (1.0f - inputColor2[2]) * (1.0f - inputColor1[2]);
	
	output[0] = valuem * (inputColor1[0]) + value * (((1.0f - inputColor1[0]) * inputColor2[0] * (inputColor1[0])) + (inputColor1[0] * scr));
	output[1] = valuem * (inputColor1[1]) + value * (((1.0f - inputColor1[1]) * inputColor2[1] * (inputColor1[1])) + (inputColor1[1] * scg));
	output[2] = valuem * (inputColor1[2]) + value * (((1.0f - inputColor1[2]) * inputColor2[2] * (inputColor1[2])) + (inputColor1[2] * scb));
	output[3] = inputColor1[3];

	clampIfNeeded(output);
}

