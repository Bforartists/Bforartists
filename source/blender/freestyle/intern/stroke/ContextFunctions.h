/*
 * ***** BEGIN GPL LICENSE BLOCK *****
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
 * The Original Code is Copyright (C) 2010 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef __FREESTYLE_CONTEXT_FUNCTIONS_H__
#define __FREESTYLE_CONTEXT_FUNCTIONS_H__

/** \file blender/freestyle/intern/stroke/ContextFunctions.h
 *  \ingroup freestyle
 *  \brief Functions related to context queries
 *  \brief Interface to access the context related information.
 *  \author Stephane Grabli
 *  \date 20/12/2003
 */

#include "Canvas.h"

#include "../image/GaussianFilter.h"
#include "../image/Image.h"

//
// Context Functions definitions
//
///////////////////////////////////////////////////////////
/*! namespace containing all the Context related functions */
namespace ContextFunctions {

// GetTimeStamp
/*! Returns the system time stamp */
LIB_STROKE_EXPORT
unsigned GetTimeStampCF();

// GetCanvasWidth
/*! Returns the canvas width */
LIB_STROKE_EXPORT
unsigned GetCanvasWidthCF();

// GetCanvasHeight
/*! Returns the canvas width */
LIB_STROKE_EXPORT 
unsigned GetCanvasHeightCF();

// Load map
/*! Loads an image map for further reading */
LIB_STROKE_EXPORT 
void LoadMapCF(const char *iFileName, const char *iMapName, unsigned iNbLevels = 4, float iSigma = 1.0f);

// ReadMapPixel
/*! Reads a pixel in a user-defined map 
 *  \return the floating value stored for that pixel
 *  \param iMapName
 *    The name of the map
 *  \param level
 *    The level of the pyramid in which we wish to read the pixel
 *  \param x
 *    The x-coordinate of the pixel we wish to read. The origin is in the lower-left corner.
 *  \param y
 *    The y-coordinate of the pixel we wish to read. The origin is in the lower-left corner.
 */
LIB_STROKE_EXPORT 
float ReadMapPixelCF(const char *iMapName, int level, unsigned x, unsigned y);

// ReadCompleteViewMapPixel
/*! Reads a pixel in the complete view map
 *  \return the floating value stored for that pixel
 *  \param level
 *    The level of the pyramid in which we wish to read the pixel
 *  \param x
 *    The x-coordinate of the pixel we wish to read. The origin is in the lower-left corner.
 *  \param y
 *    The y-coordinate of the pixel we wish to read. The origin is in the lower-left corner.
 */
LIB_STROKE_EXPORT 
float ReadCompleteViewMapPixelCF(int level, unsigned x, unsigned y);

// ReadOrientedViewMapPixel
/*! Reads a pixel in one of the oriented view map images
 *  \return the floating value stored for that pixel
 *  \param iOrientation
 *    The number telling which orientation we want to check
 *  \param level
 *    The level of the pyramid in which we wish to read the pixel
 *  \param x
 *    The x-coordinate of the pixel we wish to read. The origin is in the lower-left corner.
 *  \param y
 *    The y-coordinate of the pixel we wish to read. The origin is in the lower-left corner.
 */
LIB_STROKE_EXPORT 
float ReadDirectionalViewMapPixelCF(int iOrientation, int level, unsigned x, unsigned y);

// DEBUG
LIB_STROKE_EXPORT 
FEdge *GetSelectedFEdgeCF();

} // end of namespace ContextFunctions

#endif // __FREESTYLE_CONTEXT_FUNCTIONS_H__
