/**
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
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef PHY_IGRAPHICCONTROLLER_H
#define PHY_IGRAPHICCONTROLLER_H

#include "PHY_IController.h"



/**
	PHY_IPhysicsController is the abstract simplified Interface to a physical object.
	It contains the IMotionState and IDeformableMesh Interfaces.
*/
class PHY_IGraphicController : public PHY_IController
{

	public:
		
		virtual ~PHY_IGraphicController();
		/**
			SynchronizeMotionStates ynchronizes dynas, kinematic and deformable entities (and do 'late binding')
		*/
		virtual bool SetGraphicTransform()=0;

		virtual PHY_IGraphicController*	GetReplica(class PHY_IMotionState* motionstate) {return 0;}

};

#endif //PHY_IGRAPHICCONTROLLER_H

