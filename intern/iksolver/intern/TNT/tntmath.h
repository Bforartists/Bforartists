/**
 * $Id$
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

/*

*
* Template Numerical Toolkit (TNT): Linear Algebra Module
*
* Mathematical and Computational Sciences Division
* National Institute of Technology,
* Gaithersburg, MD USA
*
*
* This software was developed at the National Institute of Standards and
* Technology (NIST) by employees of the Federal Government in the course
* of their official duties. Pursuant to title 17 Section 105 of the
* United States Code, this software is not subject to copyright protection
* and is in the public domain.  The Template Numerical Toolkit (TNT) is
* an experimental system.  NIST assumes no responsibility whatsoever for
* its use by other parties, and makes no guarantees, expressed or implied,
* about its quality, reliability, or any other characteristic.
*
* BETA VERSION INCOMPLETE AND SUBJECT TO CHANGE
* see http://math.nist.gov/tnt for latest updates.
*
*/



// Header file for scalar math functions

#ifndef TNTMATH_H
#define TNTMATH_H

// conventional functions required by several matrix algorithms



namespace TNT 
{

struct TNTException {
        int i;
};


inline double abs(double t)
{
    return ( t > 0 ? t : -t);
}

inline double min(double a, double b)
{
    return (a < b ? a : b);
}

inline double max(double a, double b)
{
    return (a > b ? a : b);
}

inline float abs(float t)
{
    return ( t > 0 ? t : -t);
}

inline float min(float a, float b)
{
    return (a < b ? a : b);
}

inline int min(int a,int b) {
    return (a < b ? a : b);
}


inline float max(float a, float b)
{
    return (a > b ? a : b);
}

inline double sign(double a)
{
    return (a > 0 ? 1.0 : -1.0);
}

inline double sign(double a,double b) {
	return (b >= 0.0 ? TNT::abs(a) : -TNT::abs(a));
}

inline float sign(float a,float b) {
	return (b >= 0.0f ? TNT::abs(a) : -TNT::abs(a));
}

inline float sign(float a)
{
    return (a > 0.0 ? 1.0f : -1.0f);
}

inline float pythag(float a, float b)
{
	float absa,absb;
	absa = abs(a);
	absb = abs(b);

	if (absa > absb) {
		float sqr = absb/absa;
		sqr *= sqr;
		return absa * float(sqrt(1 + sqr));
	} else {
		if (absb > float(0)) {
			float sqr = absa/absb;
			sqr *= sqr;
			return absb * float(sqrt(1 + sqr));
		} else {
			return float(0);
		}
	}
}

inline double pythag(double a, double b)
{
	double absa,absb;
	absa = abs(a);
	absb = abs(b);

	if (absa > absb) {
		double sqr = absb/absa;
		sqr *= sqr;
		return absa * double(sqrt(1 + sqr));
	} else {

		if (absb > double(0)) {	
			double sqr = absa/absb;
			sqr *= sqr;
			return absb * double(sqrt(1 + sqr));
		} else {
			return double(0);
		}
	}
}


} /* namespace TNT */


#endif
/* TNTMATH_H */

