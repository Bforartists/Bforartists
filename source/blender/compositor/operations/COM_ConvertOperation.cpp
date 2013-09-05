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

#include "COM_ConvertOperation.h"


ConvertBaseOperation::ConvertBaseOperation()
{
	this->m_inputOperation = NULL;
}

void ConvertBaseOperation::initExecution()
{
	this->m_inputOperation = this->getInputSocketReader(0);
}

void ConvertBaseOperation::deinitExecution()
{
	this->m_inputOperation = NULL;
}


/* ******** Value to Color ******** */

ConvertValueToColorOperation::ConvertValueToColorOperation() : ConvertBaseOperation()
{
	this->addInputSocket(COM_DT_VALUE);
	this->addOutputSocket(COM_DT_COLOR);
}

void ConvertValueToColorOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	float inputValue[4];
	this->m_inputOperation->read(inputValue, x, y, sampler);
	output[0] = output[1] = output[2] = inputValue[0];
	output[3] = 1.0f;
}


/* ******** Color to Value ******** */

ConvertColorToValueOperation::ConvertColorToValueOperation() : ConvertBaseOperation()
{
	this->addInputSocket(COM_DT_COLOR);
	this->addOutputSocket(COM_DT_VALUE);
}

void ConvertColorToValueOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	float inputColor[4];
	this->m_inputOperation->read(inputColor, x, y, sampler);
	output[0] = (inputColor[0] + inputColor[1] + inputColor[2]) / 3.0f;
}


/* ******** Color to BW ******** */

ConvertColorToBWOperation::ConvertColorToBWOperation() : ConvertBaseOperation()
{
	this->addInputSocket(COM_DT_COLOR);
	this->addOutputSocket(COM_DT_VALUE);
}

void ConvertColorToBWOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	float inputColor[4];
	this->m_inputOperation->read(inputColor, x, y, sampler);
	output[0] = rgb_to_bw(inputColor);
}


/* ******** Color to Vector ******** */

ConvertColorToVectorOperation::ConvertColorToVectorOperation() : ConvertBaseOperation()
{
	this->addInputSocket(COM_DT_COLOR);
	this->addOutputSocket(COM_DT_VECTOR);
}

void ConvertColorToVectorOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	this->m_inputOperation->read(output, x, y, sampler);
}


/* ******** Value to Vector ******** */

ConvertValueToVectorOperation::ConvertValueToVectorOperation() : ConvertBaseOperation()
{
	this->addInputSocket(COM_DT_VALUE);
	this->addOutputSocket(COM_DT_VECTOR);
}

void ConvertValueToVectorOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	float input[4];
	this->m_inputOperation->read(input, x, y, sampler);
	output[0] = input[0];
	output[1] = input[0];
	output[2] = input[0];
	output[3] = 0.0f;
}


/* ******** Vector to Color ******** */

ConvertVectorToColorOperation::ConvertVectorToColorOperation() : ConvertBaseOperation()
{
	this->addInputSocket(COM_DT_VECTOR);
	this->addOutputSocket(COM_DT_COLOR);
}

void ConvertVectorToColorOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	this->m_inputOperation->read(output, x, y, sampler);
	output[3] = 1.0f;
}


/* ******** Vector to Value ******** */

ConvertVectorToValueOperation::ConvertVectorToValueOperation() : ConvertBaseOperation()
{
	this->addInputSocket(COM_DT_VECTOR);
	this->addOutputSocket(COM_DT_VALUE);
}

void ConvertVectorToValueOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	float input[4];
	this->m_inputOperation->read(input, x, y, sampler);
	output[0] = (input[0] + input[1] + input[2]) / 3.0f;
}


/* ******** RGB to YCC ******** */

ConvertRGBToYCCOperation::ConvertRGBToYCCOperation() : ConvertBaseOperation()
{
	this->addInputSocket(COM_DT_COLOR);
	this->addOutputSocket(COM_DT_COLOR);
}

void ConvertRGBToYCCOperation::setMode(int mode)
{
	switch (mode) {
		case 1:
			this->m_mode = BLI_YCC_ITU_BT709;
			break;
		case 2:
			this->m_mode = BLI_YCC_JFIF_0_255;
			break;
		case 0:
		default:
			this->m_mode = BLI_YCC_ITU_BT601;
			break;
	}
}

void ConvertRGBToYCCOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	float inputColor[4];
	float color[3];

	this->m_inputOperation->read(inputColor, x, y, sampler);
	rgb_to_ycc(inputColor[0], inputColor[1], inputColor[2], &color[0], &color[1], &color[2], this->m_mode);

	/* divided by 255 to normalize for viewing in */
	/* R,G,B --> Y,Cb,Cr */
	mul_v3_v3fl(output, color, 1.0f / 255.0f);
	output[3] = inputColor[3];
}

/* ******** YCC to RGB ******** */

ConvertYCCToRGBOperation::ConvertYCCToRGBOperation() : ConvertBaseOperation()
{
	this->addInputSocket(COM_DT_COLOR);
	this->addOutputSocket(COM_DT_COLOR);
}

void ConvertYCCToRGBOperation::setMode(int mode)
{
	switch (mode) {
		case 1:
			this->m_mode = BLI_YCC_ITU_BT709;
			break;
		case 2:
			this->m_mode = BLI_YCC_JFIF_0_255;
			break;
		case 0:
		default:
			this->m_mode = BLI_YCC_ITU_BT601;
			break;
	}
}

void ConvertYCCToRGBOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	float inputColor[4];
	this->m_inputOperation->read(inputColor, x, y, sampler);

	/* need to un-normalize the data */
	/* R,G,B --> Y,Cb,Cr */
	mul_v3_fl(inputColor, 255.0f);

	ycc_to_rgb(inputColor[0], inputColor[1], inputColor[2], &output[0], &output[1], &output[2], this->m_mode);
	output[3] = inputColor[3];
}


/* ******** RGB to YUV ******** */

ConvertRGBToYUVOperation::ConvertRGBToYUVOperation() : ConvertBaseOperation()
{
	this->addInputSocket(COM_DT_COLOR);
	this->addOutputSocket(COM_DT_COLOR);
}

void ConvertRGBToYUVOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	float inputColor[4];
	this->m_inputOperation->read(inputColor, x, y, sampler);
	rgb_to_yuv(inputColor[0], inputColor[1], inputColor[2], &output[0], &output[1], &output[2]);
	output[3] = inputColor[3];
}


/* ******** YUV to RGB ******** */

ConvertYUVToRGBOperation::ConvertYUVToRGBOperation() : ConvertBaseOperation()
{
	this->addInputSocket(COM_DT_COLOR);
	this->addOutputSocket(COM_DT_COLOR);
}

void ConvertYUVToRGBOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	float inputColor[4];
	this->m_inputOperation->read(inputColor, x, y, sampler);
	yuv_to_rgb(inputColor[0], inputColor[1], inputColor[2], &output[0], &output[1], &output[2]);
	output[3] = inputColor[3];
}


/* ******** RGB to HSV ******** */

ConvertRGBToHSVOperation::ConvertRGBToHSVOperation() : ConvertBaseOperation()
{
	this->addInputSocket(COM_DT_COLOR);
	this->addOutputSocket(COM_DT_COLOR);
}

void ConvertRGBToHSVOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	float inputColor[4];
	this->m_inputOperation->read(inputColor, x, y, sampler);
	rgb_to_hsv_v(inputColor, output);
	output[3] = inputColor[3];
}


/* ******** HSV to RGB ******** */

ConvertHSVToRGBOperation::ConvertHSVToRGBOperation() : ConvertBaseOperation()
{
	this->addInputSocket(COM_DT_COLOR);
	this->addOutputSocket(COM_DT_COLOR);
}

void ConvertHSVToRGBOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	float inputColor[4];
	this->m_inputOperation->read(inputColor, x, y, sampler);
	hsv_to_rgb_v(inputColor, output);
	output[3] = inputColor[3];
}


/* ******** Premul to Straight ******** */

ConvertPremulToStraightOperation::ConvertPremulToStraightOperation() : ConvertBaseOperation()
{
	this->addInputSocket(COM_DT_COLOR);
	this->addOutputSocket(COM_DT_COLOR);
}

void ConvertPremulToStraightOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	float inputValue[4];
	float alpha;

	this->m_inputOperation->read(inputValue, x, y, sampler);
	alpha = inputValue[3];

	if (fabsf(alpha) < 1e-5f) {
		zero_v3(output);
	}
	else {
		mul_v3_v3fl(output, inputValue, 1.0f / alpha);
	}

	/* never touches the alpha */
	output[3] = alpha;
}


/* ******** Straight to Premul ******** */

ConvertStraightToPremulOperation::ConvertStraightToPremulOperation() : ConvertBaseOperation()
{
	this->addInputSocket(COM_DT_COLOR);
	this->addOutputSocket(COM_DT_COLOR);
}

void ConvertStraightToPremulOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	float inputValue[4];
	float alpha;

	this->m_inputOperation->read(inputValue, x, y, sampler);
	alpha = inputValue[3];

	mul_v3_v3fl(output, inputValue, alpha);

	/* never touches the alpha */
	output[3] = alpha;
}


/* ******** Separate Channels ******** */

SeparateChannelOperation::SeparateChannelOperation() : NodeOperation()
{
	this->addInputSocket(COM_DT_COLOR);
	this->addOutputSocket(COM_DT_VALUE);
	this->m_inputOperation = NULL;
}
void SeparateChannelOperation::initExecution()
{
	this->m_inputOperation = this->getInputSocketReader(0);
}

void SeparateChannelOperation::deinitExecution()
{
	this->m_inputOperation = NULL;
}


void SeparateChannelOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	float input[4];
	this->m_inputOperation->read(input, x, y, sampler);
	output[0] = input[this->m_channel];
}


/* ******** Combine Channels ******** */

CombineChannelsOperation::CombineChannelsOperation() : NodeOperation()
{
	this->addInputSocket(COM_DT_VALUE);
	this->addInputSocket(COM_DT_VALUE);
	this->addInputSocket(COM_DT_VALUE);
	this->addInputSocket(COM_DT_VALUE);
	this->addOutputSocket(COM_DT_COLOR);
	this->setResolutionInputSocketIndex(0);
	this->m_inputChannel1Operation = NULL;
	this->m_inputChannel2Operation = NULL;
	this->m_inputChannel3Operation = NULL;
	this->m_inputChannel4Operation = NULL;
}

void CombineChannelsOperation::initExecution()
{
	this->m_inputChannel1Operation = this->getInputSocketReader(0);
	this->m_inputChannel2Operation = this->getInputSocketReader(1);
	this->m_inputChannel3Operation = this->getInputSocketReader(2);
	this->m_inputChannel4Operation = this->getInputSocketReader(3);
}

void CombineChannelsOperation::deinitExecution()
{
	this->m_inputChannel1Operation = NULL;
	this->m_inputChannel2Operation = NULL;
	this->m_inputChannel3Operation = NULL;
	this->m_inputChannel4Operation = NULL;
}


void CombineChannelsOperation::executePixel(float output[4], float x, float y, PixelSampler sampler)
{
	float input[4];
	if (this->m_inputChannel1Operation) {
		this->m_inputChannel1Operation->read(input, x, y, sampler);
		output[0] = input[0];
	}
	if (this->m_inputChannel2Operation) {
		this->m_inputChannel2Operation->read(input, x, y, sampler);
		output[1] = input[0];
	}
	if (this->m_inputChannel3Operation) {
		this->m_inputChannel3Operation->read(input, x, y, sampler);
		output[2] = input[0];
	}
	if (this->m_inputChannel4Operation) {
		this->m_inputChannel4Operation->read(input, x, y, sampler);
		output[3] = input[0];
	}
}
