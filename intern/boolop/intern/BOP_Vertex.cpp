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
 
#include "BOP_Vertex.h"

/**
 * Constructs a new vertex with the specified coordinates.
 * @param x X-axis coordinate
 * @param y Y-axis coordinate
 * @param z Z-axis coordinate
 */
BOP_Vertex::BOP_Vertex(double x, double y, double z) 
{
	m_point.setValue(x,y,z);
	m_tag = UNCLASSIFIED;   
}

/**
 * Constructs a new vertex with the specified point.
 * @param p point XYZ
 */
BOP_Vertex::BOP_Vertex(MT_Point3 p) 
{
	m_point = p;
	m_tag = UNCLASSIFIED;   
}

/**
 * Adds a new edge index to this vertex.
 * @param i edge index
 */
void BOP_Vertex::addEdge(BOP_Index i) 
{
  if (!containsEdge(i))
    m_edges.push_back(i);
}

/**
 * Removes an edge index from this vertex.
 * @param i edge index
 */
void BOP_Vertex::removeEdge(BOP_Index i) 
{
	for(BOP_IT_Indexs it = m_edges.begin();it!=m_edges.end();it++) {
		if ((*it)==i) {
			m_edges.erase(it);
			return;
		}
	}
}

/**
 * Returns if this vertex contains the specified edge index.
 * @param i edge index
 * @return true if this vertex contains the specified edge index, false otherwise
 */
bool BOP_Vertex::containsEdge(BOP_Index i)
{
	int pos=0;
	for(BOP_IT_Indexs it = m_edges.begin();it!=m_edges.end();pos++,it++) {
	  if ((*it)==i){
	    return true;
	  }
	}
	
	return false;
}
