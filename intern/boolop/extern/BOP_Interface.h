/**
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
 
#ifndef BOP_INTERFACE_H
#define BOP_INTERFACE_H

#include "../../bsp/intern/BSP_CSGMesh.h"

typedef enum EnumBoolOpState {BOP_OK, BOP_NO_SOLID, BOP_ERROR} BoolOpState;
typedef enum EnumBoolOpType {BOP_INTERSECTION=e_csg_intersection, BOP_UNION=e_csg_union, BOP_DIFFERENCE=e_csg_difference} BoolOpType;

BoolOpState BOP_performBooleanOperation(BoolOpType                   opType,
					BSP_CSGMesh**                outputMesh,
					CSG_FaceIteratorDescriptor   obAFaces,
					CSG_VertexIteratorDescriptor obAVertices,
					CSG_FaceIteratorDescriptor   obBFaces,
					CSG_VertexIteratorDescriptor obBVertices);

#endif
