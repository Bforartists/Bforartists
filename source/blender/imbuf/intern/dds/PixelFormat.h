/**
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * Contributors: Amorilia (amorilia@gamebox.net)
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

/*
 * This file is based on a similar file from the NVIDIA texture tools
 * (http://nvidia-texture-tools.googlecode.com/)
 *
 * Original license from NVIDIA follows.
 */

// Copyright NVIDIA Corporation 2007 -- Ignacio Castano <icastano@nvidia.com>
// 
// Permission is hereby granted, free of charge, to any person
// obtaining a copy of this software and associated documentation
// files (the "Software"), to deal in the Software without
// restriction, including without limitation the rights to use,
// copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the
// Software is furnished to do so, subject to the following
// conditions:
// 
// The above copyright notice and this permission notice shall be
// included in all copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
// EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
// OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
// NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
// HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
// WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
// FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
// OTHER DEALINGS IN THE SOFTWARE.

#ifndef _DDS_PIXELFORMAT_H
#define _DDS_PIXELFORMAT_H

#include <Common.h>

	namespace PixelFormat
	{

		// Convert component @a c having @a inbits to the returned value having @a outbits.
		inline uint convert(uint c, uint inbits, uint outbits)
		{
			if (inbits == 0)
			{
				return 0;
			}
			else if (inbits >= outbits)
			{
				// truncate
				return c >> (inbits - outbits);
			}
			else
			{
				// bitexpand
				return (c << (outbits - inbits)) | convert(c, inbits, outbits - inbits);
			}
		}

		// Get pixel component shift and size given its mask.
		inline void maskShiftAndSize(uint mask, uint * shift, uint * size)
		{
			if (!mask)
			{
				*shift = 0;
				*size = 0;
				return;
			}

			*shift = 0;
			while((mask & 1) == 0) {
				++(*shift);
				mask >>= 1;
			}
			
			*size = 0;
			while((mask & 1) == 1) {
				++(*size);
				mask >>= 1;
			}
		}

	} // PixelFormat namespace

#endif // _DDS_IMAGE_PIXELFORMAT_H
