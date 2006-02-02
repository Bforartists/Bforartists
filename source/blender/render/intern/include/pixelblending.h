/*
 * $Id$
 *
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * Contributor(s): 2004-2006 Blender Foundation, full recode
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#ifndef PIXELBLENDING_EXT_H
#define PIXELBLENDING_EXT_H 


/**
* add 1 pixel to into filtered three lines 
 * (float vecs to float vec)
 */
void add_filt_fmask(unsigned int mask, float *col, float *rowbuf, int row_w);
void add_filt_fmask_pixsize(unsigned int mask, float *in, float *rowbuf, int row_w, int pixsize);

/**
 * Alpha-over blending for floats.
 */
void addAlphaOverFloat(float *dest, float *source);  

/**
 * Alpha-under blending for floats.
 */
void addAlphaUnderFloat(float *dest, float *source);  


/**
 * Same for floats
 */
void addalphaAddfacFloat(float *dest, float *source, char addfac);

/**
 * dest = dest + source
 */
void addalphaAddFloat(float *dest, float *source);

/**
 * Blend bron under doel, while doing gamma correction
 */
void addalphaUnderGammaFloat(float *doel, float *bron);

/**
* Copy the colour buffer output to R.rectot, to line y.
 */
void transferColourBufferToOutput(float *buf, int y);
/**
* using default transforms for brightness, gamma, hue, saturation etc. 
 */
void std_floatcol_to_charcol(float *buf, char *target);


#endif /* PIXELBLENDING_EXT_H */

