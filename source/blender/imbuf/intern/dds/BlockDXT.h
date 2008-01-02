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

#ifndef _DDS_BLOCKDXT_H
#define _DDS_BLOCKDXT_H

#include <Common.h>
#include <Color.h>
#include <ColorBlock.h>
#include <Stream.h>

/// DXT1 block.
struct BlockDXT1
{
	Color16 col0;
	Color16 col1;
	union {
		uint8 row[4];
		uint indices;
	};

	bool isFourColorMode() const;

	uint evaluatePalette(Color32 color_array[4]) const;
	uint evaluatePaletteFast(Color32 color_array[4]) const;
	void evaluatePalette3(Color32 color_array[4]) const;
	void evaluatePalette4(Color32 color_array[4]) const;
	
	void decodeBlock(ColorBlock * block) const;
	
	void setIndices(int * idx);

	void flip4();
	void flip2();
};

/// Return true if the block uses four color mode, false otherwise.
inline bool BlockDXT1::isFourColorMode() const
{
	return col0.u > col1.u;
}


/// DXT3 alpha block with explicit alpha.
struct AlphaBlockDXT3
{
	union {
		struct {
			uint alpha0 : 4;
			uint alpha1 : 4;
			uint alpha2 : 4;
			uint alpha3 : 4;
			uint alpha4 : 4;
			uint alpha5 : 4;
			uint alpha6 : 4;
			uint alpha7 : 4;
			uint alpha8 : 4;
			uint alpha9 : 4;
			uint alphaA : 4;
			uint alphaB : 4;
			uint alphaC : 4;
			uint alphaD : 4;
			uint alphaE : 4;
			uint alphaF : 4;
		};
		uint16 row[4];
	};
	
	void decodeBlock(ColorBlock * block) const;
	
	void flip4();
	void flip2();
};


/// DXT3 block.
struct BlockDXT3
{
	AlphaBlockDXT3 alpha;
	BlockDXT1 color;
	
	void decodeBlock(ColorBlock * block) const;
	
	void flip4();
	void flip2();
};


/// DXT5 alpha block.
struct AlphaBlockDXT5
{
	union {
		struct {
			unsigned int alpha0 : 8;	// 8
			unsigned int alpha1 : 8;	// 16
			unsigned int bits0 : 3;		// 3 - 19
			unsigned int bits1 : 3; 	// 6 - 22
			unsigned int bits2 : 3; 	// 9 - 25
			unsigned int bits3 : 3;		// 12 - 28
			unsigned int bits4 : 3;		// 15 - 31
			unsigned int bits5 : 3;		// 18 - 34
			unsigned int bits6 : 3;		// 21 - 37
			unsigned int bits7 : 3;		// 24 - 40
			unsigned int bits8 : 3;		// 27 - 43
			unsigned int bits9 : 3; 	// 30 - 46
			unsigned int bitsA : 3; 	// 33 - 49
			unsigned int bitsB : 3;		// 36 - 52
			unsigned int bitsC : 3;		// 39 - 55
			unsigned int bitsD : 3;		// 42 - 58
			unsigned int bitsE : 3;		// 45 - 61
			unsigned int bitsF : 3;		// 48 - 64
		};
		uint64 u;
	};
	
	void evaluatePalette(uint8 alpha[8]) const;
	void evaluatePalette8(uint8 alpha[8]) const;
	void evaluatePalette6(uint8 alpha[8]) const;
	void indices(uint8 index_array[16]) const;

	uint index(uint index) const;
	void setIndex(uint index, uint value);
	
	void decodeBlock(ColorBlock * block) const;
	
	void flip4();
	void flip2();
};


/// DXT5 block.
struct BlockDXT5
{
	AlphaBlockDXT5 alpha;
	BlockDXT1 color;
	
	void decodeBlock(ColorBlock * block) const;
	
	void flip4();
	void flip2();
};

/// ATI1 block.
struct BlockATI1
{
	AlphaBlockDXT5 alpha;
	
	void decodeBlock(ColorBlock * block) const;
	
	void flip4();
	void flip2();
};

/// ATI2 block.
struct BlockATI2
{
	AlphaBlockDXT5 x;
	AlphaBlockDXT5 y;
	
	void decodeBlock(ColorBlock * block) const;
	
	void flip4();
	void flip2();
};

/// CTX1 block.
struct BlockCTX1
{
	uint8 col0[2];
	uint8 col1[2];
	union {
		uint8 row[4];
		uint indices;
	};

	void evaluatePalette(Color32 color_array[4]) const;
	void setIndices(int * idx);

	void decodeBlock(ColorBlock * block) const;
	
	void flip4();
	void flip2();
};

void mem_read(Stream & mem, BlockDXT1 & block);
void mem_read(Stream & mem, AlphaBlockDXT3 & block);
void mem_read(Stream & mem, BlockDXT3 & block);
void mem_read(Stream & mem, AlphaBlockDXT5 & block);
void mem_read(Stream & mem, BlockDXT5 & block);
void mem_read(Stream & mem, BlockATI1 & block);
void mem_read(Stream & mem, BlockATI2 & block);
void mem_read(Stream & mem, BlockCTX1 & block);

#endif // _DDS_BLOCKDXT_H
