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
#ifndef KX_SCALARINTERPOLATOR
#define KX_SCALARINTERPOLATOR

#include "MT_Scalar.h"
#include "KX_IInterpolator.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

class KX_IScalarInterpolator;

class KX_ScalarInterpolator : public KX_IInterpolator {
public:
	KX_ScalarInterpolator(MT_Scalar* target, 
						  KX_IScalarInterpolator *ipo) :
		m_target(target),
		m_ipo(ipo)
		{}
	
	virtual ~KX_ScalarInterpolator() {}
	virtual void Execute(float currentTime) const;
	void		SetNewTarget(MT_Scalar* newtarget)
	{
		m_target=newtarget;
	}
	MT_Scalar*	GetTarget()
	{
		return m_target;
	}
private:
	MT_Scalar*               m_target;
	KX_IScalarInterpolator *m_ipo;
};

#endif

