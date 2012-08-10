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

#ifndef _COM_BokehImageOperation_h
#define _COM_BokehImageOperation_h
#include "COM_NodeOperation.h"


class BokehImageOperation : public NodeOperation {
private:
	NodeBokehImage *m_data;

	float m_center[2];
	float m_inverseRounding;
	float m_circularDistance;
	float m_flapRad;
	float m_flapRadAdd;
	
	bool m_deleteData;

	void detemineStartPointOfFlap(float r[2], int flapNumber, float distance);
	float isInsideBokeh(float distance, float x, float y);
public:
	BokehImageOperation();

	/**
	 * the inner loop of this program
	 */
	void executePixel(float *color, float x, float y, PixelSampler sampler);
	
	/**
	 * Initialize the execution
	 */
	void initExecution();
	
	/**
	 * Deinitialize the execution
	 */
	void deinitExecution();
	
	void determineResolution(unsigned int resolution[2], unsigned int preferredResolution[2]);

	void setData(NodeBokehImage *data) { this->m_data = data; }
	void deleteDataOnFinish() { this->m_deleteData = true; }
};
#endif
