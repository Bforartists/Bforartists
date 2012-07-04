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

#ifndef _COM_BokehVariableSizeBokehBlurOperation_h
#define _COM_VariableSizeBokehBlurOperation_h
#include "COM_NodeOperation.h"
#include "COM_QualityStepHelper.h"


class VariableSizeBokehBlurOperation : public NodeOperation, public QualityStepHelper {
private:
	int m_maxBlur;
	float m_threshold;
	SocketReader *m_inputProgram;
	SocketReader *m_inputBokehProgram;
	SocketReader *m_inputSizeProgram;
	SocketReader *m_inputDepthProgram;
#ifdef COM_DEFOCUS_SEARCH
	SocketReader *inputSearchProgram;
#endif

public:
	VariableSizeBokehBlurOperation();

	/**
	 * the inner loop of this program
	 */
	void executePixel(float *color, int x, int y, MemoryBuffer * inputBuffers[], void *data);
	
	/**
	 * Initialize the execution
	 */
	void initExecution();
	
	/**
	 * Deinitialize the execution
	 */
	void deinitExecution();
	
	bool determineDependingAreaOfInterest(rcti *input, ReadBufferOperation *readOperation, rcti *output);
	
	void setMaxBlur(int maxRadius) { this->m_maxBlur = maxRadius; }

	void setThreshold(float threshold) { this->m_threshold = threshold; }


};

#ifdef COM_DEFOCUS_SEARCH
class InverseSearchRadiusOperation : public NodeOperation {
private:
	int maxBlur;
	float threshold;
	SocketReader *inputDepth;
	SocketReader *inputRadius;
public:
	static const int DIVIDER = 4;
	
	InverseSearchRadiusOperation();

	/**
	 * the inner loop of this program
	 */
	void executePixel(float *color, int x, int y, MemoryBuffer * inputBuffers[], void *data);
	
	/**
	 * Initialize the execution
	 */
	void initExecution();
	void* initializeTileData(rcti *rect, MemoryBuffer **memoryBuffers);
	void deinitializeTileData(rcti *rect, MemoryBuffer **memoryBuffers, void *data);
	
	/**
	 * Deinitialize the execution
	 */
	void deinitExecution();
	
	bool determineDependingAreaOfInterest(rcti *input, ReadBufferOperation *readOperation, rcti *output);
	void determineResolution(unsigned int resolution[], unsigned int preferredResolution[]);
	
	void setMaxBlur(int maxRadius) { this->maxBlur = maxRadius; }

	void setThreshold(float threshold) { this->threshold = threshold; }
};
#endif
#endif
