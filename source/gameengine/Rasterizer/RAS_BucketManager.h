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
// this will be put in a class later on

#ifndef __RAS_BUCKETMANAGER
#define __RAS_BUCKETMANAGER

#include "MT_Transform.h"
#include "RAS_MaterialBucket.h"
#include "GEN_Map.h"

#include <vector>

class RAS_BucketManager
{
	//GEN_Map<class RAS_IPolyMaterial,class RAS_MaterialBucket*> m_MaterialBuckets;
	std::vector<class RAS_MaterialBucket*> m_MaterialBuckets;
	std::vector<class RAS_MaterialBucket*> m_AlphaBuckets;

public:
	RAS_BucketManager();
	virtual ~RAS_BucketManager();

	void Renderbuckets(const MT_Transform & cameratrans,
							RAS_IRasterizer* rasty,
							class RAS_IRenderTools* rendertools);

	RAS_MaterialBucket* RAS_BucketManagerFindBucket(RAS_IPolyMaterial * material);
	

private:
	void RAS_BucketManagerClearAll();

};

#endif //__RAS_BUCKETMANAGER

