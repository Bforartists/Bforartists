/**
 * Generate random numbers that can be used by other components. Each
 * generator needs its own generator, so that the seed can be set
 * on a per-generator basis.
 *
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#ifndef __KX_RANDOMNUMBERGENERATOR
#define __KX_RANDOMNUMBERGENERATOR

class SCA_RandomNumberGenerator {

	/** base seed */
	long m_seed;

	/* A bit silly.. The N parameter is a define in the .cpp file */
	/** the array for the state vector  */
	/* unsigned long mt[N]; */
	unsigned long mt[624];

	/** mti==N+1 means mt[KX_MT_VectorLenght] is not initialized */
	int mti; /* initialised in the cpp file */

	/** Calculate a start vector */
	void SetStartVector(void);
 public:
	SCA_RandomNumberGenerator(long seed);
	~SCA_RandomNumberGenerator();
	unsigned long Draw();
	float DrawFloat();
	long GetSeed();
	void SetSeed(long newseed);
};

#endif /* __KX_RANDOMNUMBERGENERATOR */

