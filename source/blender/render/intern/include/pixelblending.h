/*
 *    pixelblending_ext.h
 * external interface for pixelblending 
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

#ifndef PIXELBLENDING_EXT_H
#define PIXELBLENDING_EXT_H 

/* local includes */
#include "vanillaRenderPipe_types.h"

/**
 * Halo-add pixel, bring your own R.osa setting, and add factor
 */
void addAddSampColF(float *s, float *d, int m, int osa, char add);

/**
 * Alpha undersamples pixel, bring your own R.osa setting
 */
int addUnderSampColF(float *sampcol, float *dest, int mask, int osaNr);

/**
 * Alpha oversample pixel, bring your own R.osa setting
 */
void addOverSampColF(float *sampcol, float *dest, int mask, int osaNr);

/**
* add 1 pixel to into filtered three lines 
 * (float vecs to float vec)
 */
void add_filt_fmask(unsigned int mask, float *col, float *rb1, float *rb2, float *rb3);

/**
 * Convert a series of oversampled pixels into filtered three lines 
 * (float vecs to float vec)
 */
void sampleFloatColV2FloatColVFilter(float *sample, float *dest1, float *dest2, float *dest3, int osaNr);

/**
 * Convert a series of oversampled pixels into a single pixel. Uses R.osa to
 * count the length! (short vecs to short vec)
 */
void sampleShortColV2ShortColV(unsigned short *sample, unsigned short *dest, int osaNr);

/**
 * Alpha-over blending for floats.
 */
void addAlphaOverFloat(float *dest, float *source);  

/**
 * Alpha-under blending for floats.
 */
void addAlphaUnderFloat(float *dest, float *source);  

/**
 * Write a 16-bit-colour colour vector to a 8-bit-colour colour vector. 
 */
void cpShortColV2CharColV(unsigned short *source, char *dest);

/**
 * Write a 8-bit-colour colour vector to a 16-bit-colour colour vector. 
 */
void cpCharColV2ShortColV(char *source, unsigned short *dest);

/**
 * Write a 32-bit-colour colour vector to a 8-bit-colour colour vector. 
 */
void cpIntColV2CharColV(unsigned int *source, char *dest);

/**
 * Write a floating-point-colour colour vector to a 8-bit-colour colour 
 * vector. Clip colours to [0, 1].
 */
void cpFloatColV2CharColV(float *source, char *dest);

/**
 * Cpoy a 8-bit-colour vector to floating point colour vector.
 */
void cpCharColV2FloatColV(char *source, float *dest);
/**
 * Cpoy a 16-bit-colour vector to floating point colour vector.
 */
void cpShortColV2FloatColV(unsigned short *source, float *dest);

/**
 * Copy a float-colour colour vector.
 */
void cpFloatColV(float *source, float *dest);

/**
 * Copy a 16-bit-colour colour vector.
 */
void cpShortColV(unsigned short *source, unsigned short *dest);

/**
 * Copy an 8-bit-colour colour vector.
 */
void cpCharColV(char *source, char *dest);

/**
 * Same for floats
 */
void addalphaAddfacFloat(float *dest, float *source, char addfac);

/**
 * dest = dest + source
 */
void addalphaAddFloat(float *dest, float *source);

/** ols functions: side effects?
void addalphaUnderFloat(char *doel, char *bron); think this already exists...
void addalphaUnderGammaFloat(char *doel, char *bron);
*/
/**
 * Blend bron under doel, while doing gamma correction
 */
void addalphaUnderGammaFloat(float *doel, float *bron);

/**
 * Transform an premul-alpha 32-bit colour into a key-alpha 32-bit colour.
 */
void applyKeyAlphaCharCol(char* target);

/* Old blending functions */
void keyalpha(char *doel);   /* maakt premul 255 */
void addalphaUnder(char *doel, char *bron);
void addalphaUnderGamma(char *doel, char *bron);
void addalphaOver(char *doel, char *bron);
void addalphaAdd(char *doel, char *bron);

#endif /* PIXELBLENDING_EXT_H */

