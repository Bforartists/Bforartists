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
 *		Campbell Barton
 */

#include "COM_GaussianAlphaYBlurOperation.h"
#include "BLI_math.h"

extern "C" {
	#include "RE_pipeline.h"
}

GaussianAlphaYBlurOperation::GaussianAlphaYBlurOperation() : BlurBaseOperation(COM_DT_VALUE)
{
	this->gausstab = NULL;
	this->rad = 0;
}

void *GaussianAlphaYBlurOperation::initializeTileData(rcti *rect, MemoryBuffer **memoryBuffers)
{
	if (!this->sizeavailable) {
		updateGauss(memoryBuffers);
	}
	void *buffer = getInputOperation(0)->initializeTileData(NULL, memoryBuffers);
	return buffer;
}

void GaussianAlphaYBlurOperation::initExecution()
{
	if (this->sizeavailable) {
		float rad = size * this->data->sizey;
		if (rad < 1)
			rad = 1;

		this->rad = rad;
		this->gausstab = BlurBaseOperation::make_gausstab(rad);
		this->distbuf_inv = BlurBaseOperation::make_dist_fac_inverse(rad);
	}
}

void GaussianAlphaYBlurOperation::updateGauss(MemoryBuffer **memoryBuffers)
{
	if (this->gausstab == NULL) {
		updateSize(memoryBuffers);
		float rad = size * this->data->sizey;
		if (rad < 1)
			rad = 1;
		
		this->rad = rad;
		this->gausstab = BlurBaseOperation::make_gausstab(rad);
	}

	if (this->distbuf_inv == NULL) {
		updateSize(memoryBuffers);
		float rad = size * this->data->sizex;
		if (rad < 1)
			rad = 1;

		this->rad = rad;
		this->distbuf_inv = BlurBaseOperation::make_dist_fac_inverse(rad);
	}
}

void GaussianAlphaYBlurOperation::executePixel(float *color, int x, int y, MemoryBuffer *inputBuffers[], void *data)
{
	MemoryBuffer *inputBuffer = (MemoryBuffer *)data;
	float *buffer = inputBuffer->getBuffer();
	int bufferwidth = inputBuffer->getWidth();
	int bufferstartx = inputBuffer->getRect()->xmin;
	int bufferstarty = inputBuffer->getRect()->ymin;

	int miny = y - this->rad;
	int maxy = y + this->rad;
	int minx = x;
	int maxx = x;
	miny = max(miny, inputBuffer->getRect()->ymin);
	minx = max(minx, inputBuffer->getRect()->xmin);
	maxy = min(maxy, inputBuffer->getRect()->ymax);
	maxx = min(maxx, inputBuffer->getRect()->xmax);

	/* *** this is the main part which is different to 'GaussianYBlurOperation'  *** */
	int step = getStep();

	/* gauss */
	float tempColor = 0.0f;
	float overallmultiplyer = 0.0f;

	/* dilate */
	float value_max = buffer[(x * 4) + (y * 4 * bufferwidth)]; /* init with the current color to avoid unneeded lookups */
	float distfacinv_max = 1.0f; /* 0 to 1 */

	for (int ny = miny; ny < maxy; ny += step) {
		int bufferindex = ((minx - bufferstartx) * 4) + ((ny - bufferstarty) * 4 * bufferwidth);

		const int index = (ny - y) + this->rad;
		float value = buffer[bufferindex];
		float multiplyer;

		/* gauss */
		{
			multiplyer = gausstab[index];
			tempColor += value * multiplyer;
			overallmultiplyer += multiplyer;
		}

		/* dilate - find most extreme color */
		if (value > value_max) {
#if 0
			multiplyer = 1.0f - ((fabsf(y - ny)) / (float)this->rad);
#else
			multiplyer = distbuf_inv[index];
#endif
			value *= multiplyer;
			if (value > value_max) {
				value_max = value;
				distfacinv_max = multiplyer;
			}
		}

	}

	/* blend between the max value and gauss blue - gives nice feather */
	const float value_gauss = tempColor / overallmultiplyer;
	const float value_final = (value_max * distfacinv_max) + (value_gauss * (1.0f - distfacinv_max));
	color[0] = value_final;
}

void GaussianAlphaYBlurOperation::deinitExecution()
{
	BlurBaseOperation::deinitExecution();
	delete [] this->gausstab;
	this->gausstab = NULL;
	delete [] this->distbuf_inv;
	this->distbuf_inv = NULL;
}

bool GaussianAlphaYBlurOperation::determineDependingAreaOfInterest(rcti *input, ReadBufferOperation *readOperation, rcti *output)
{
	rcti newInput;
	rcti sizeInput;
	sizeInput.xmin = 0;
	sizeInput.ymin = 0;
	sizeInput.xmax = 5;
	sizeInput.ymax = 5;
	
	NodeOperation *operation = this->getInputOperation(1);
	if (operation->determineDependingAreaOfInterest(&sizeInput, readOperation, output)) {
		return true;
	}
	else {
		if (this->sizeavailable && this->gausstab != NULL) {
			newInput.xmax = input->xmax;
			newInput.xmin = input->xmin;
			newInput.ymax = input->ymax + rad;
			newInput.ymin = input->ymin - rad;
		}
		else {
			newInput.xmax = this->getWidth();
			newInput.xmin = 0;
			newInput.ymax = this->getHeight();
			newInput.ymin = 0;
		}
		return NodeOperation::determineDependingAreaOfInterest(&newInput, readOperation, output);
	}
}
