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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "PIL_time.h"
#include "BLI_rand.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#if defined(WIN32) && !defined(FREE_WINDOWS)
typedef unsigned __int64	r_uint64;
#else
typedef unsigned long long	r_uint64;
#endif

#define MULTIPLIER	0x5DEECE66D
#define ADDEND		0xB

#define LOWSEED		0x330E

/***/

struct RNG {
	r_uint64 X;
};

RNG	*rng_new(unsigned int seed)
{
	RNG *rng = MEM_mallocN(sizeof(*rng), "rng");

	rng_seed(rng, seed);

	return rng;
}

void rng_free(RNG* rng)
{
	MEM_freeN(rng);
}

void rng_seed(RNG *rng, unsigned int seed) {
	rng->X= (((r_uint64) seed)<<16) | LOWSEED;
}

int rng_getInt(RNG *rng) {
	rng->X= (MULTIPLIER*rng->X + ADDEND)&0x0000FFFFFFFFFFFF;
	return (int) (rng->X>>17);
}

double rng_getDouble(RNG *rng) {
	return (double) rng_getInt(rng)/0x80000000;
}

float rng_getFloat(RNG *rng) {
	return (float) rng_getInt(rng)/0x80000000;
}

void rng_shuffleArray(RNG *rng, void *data, int elemSize, int numElems)
{
	int i = numElems;
	void *temp = malloc(elemSize);

	while (--i) {
		int j = rng_getInt(rng)%i;
		void *iElem = (unsigned char*)data + i*elemSize;
		void *jElem = (unsigned char*)data + j*elemSize;

		memcpy(temp, iElem, elemSize);
		memcpy(iElem, jElem, elemSize);
		memcpy(jElem, temp, elemSize);
	}

	free(temp);
}

/***/

static RNG theBLI_rng = {0};

void BLI_srand(unsigned int seed) {
	rng_seed(&theBLI_rng, seed);
}

int BLI_rand(void) {
	return rng_getInt(&theBLI_rng);
}

double BLI_drand(void) {
	return rng_getDouble(&theBLI_rng);
}

float BLI_frand(void) {
	return rng_getFloat(&theBLI_rng);
}

void BLI_fillrand(void *addr, int len) {
	RNG rng;
	unsigned char *p= addr;

	rng_seed(&rng, (unsigned int) (PIL_check_seconds_timer()*0x7FFFFFFF));
	while (len--) *p++= rng_getInt(&rng)&0xFF;
}

void BLI_array_randomize(void *data, int elemSize, int numElems, unsigned int seed)
{
	RNG rng;

	rng_seed(&rng, seed);
	rng_shuffleArray(&rng, data, elemSize, numElems);
}

