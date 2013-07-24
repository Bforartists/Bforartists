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

#include "COM_MixDodgeOperation.h"

MixDodgeOperation::MixDodgeOperation() : MixBaseOperation()
{
	/* pass */
}

void MixDodgeOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	float inputColor1[4];
	float inputColor2[4];
	float inputValue[4];
	float tmp;

	this->m_inputValueOperation->read(inputValue, x, y, sampler);
	this->m_inputColor1Operation->read(inputColor1, x, y, sampler);
	this->m_inputColor2Operation->read(inputColor2, x, y, sampler);

	float value = inputValue[0];
	if (this->useValueAlphaMultiply()) {
		value *= inputColor2[3];
	}
	
	if (inputColor1[0] != 0.0f) {
		tmp = 1.0f - value * inputColor2[0];
		if (tmp <= 0.0f)
			output[0] = 1.0f;
		else {
			tmp = inputColor1[0] / tmp;
			if (tmp > 1.0f)
				output[0] = 1.0f;
			else
				output[0] = tmp;
		}
	}
	else
		output[0] = 0.0f;
	
	if (inputColor1[1] != 0.0f) {
		tmp = 1.0f - value * inputColor2[1];
		if (tmp <= 0.0f)
			output[1] = 1.0f;
		else {
			tmp = inputColor1[1] / tmp;
			if (tmp > 1.0f)
				output[1] = 1.0f;
			else
				output[1] = tmp;
		}
	}
	else
		output[1] = 0.0f;
	
	if (inputColor1[2] != 0.0f) {
		tmp = 1.0f - value * inputColor2[2];
		if (tmp <= 0.0f)
			output[2] = 1.0f;
		else {
			tmp = inputColor1[2] / tmp;
			if (tmp > 1.0f)
				output[2] = 1.0f;
			else
				output[2] = tmp;
		}
	}
	else
		output[2] = 0.0f;
	
	output[3] = inputColor1[3];

	clampIfNeeded(output);
}

