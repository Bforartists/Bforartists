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

#include "KX_OrientationInterpolator.h"


#include "MT_Matrix3x3.h"
#include "KX_IScalarInterpolator.h"

void KX_OrientationInterpolator::Execute(float currentTime) const {
	MT_Vector3 eul(m_ipos[0]->GetValue(currentTime),
				   m_ipos[1]->GetValue(currentTime),
				   m_ipos[2]->GetValue(currentTime));
	MT_Scalar ci = cos(eul[0]); 
	MT_Scalar cj = cos(eul[1]); 
	MT_Scalar ch = cos(eul[2]);
	MT_Scalar si = sin(eul[0]); 
	MT_Scalar sj = sin(eul[1]); 
	MT_Scalar sh = sin(eul[2]);
	MT_Scalar cc = ci*ch; 
	MT_Scalar cs = ci*sh; 
	MT_Scalar sc = si*ch; 
	MT_Scalar ss = si*sh;

	m_target.setValue(cj*ch, sj*sc-cs, sj*cc+ss,
					  cj*sh, sj*ss+cc, sj*cs-sc, 
					    -sj,    cj*si,    cj*ci);
}
