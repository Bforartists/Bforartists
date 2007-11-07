/**
 * $Id: 
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
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
 * Contributor(s): Martin Poirier
 *
 * ***** END GPL LICENSE BLOCK *****
 */
 
#ifndef REEB_H_
#define REEB_H_

#include "DNA_listBase.h"

struct EdgeHash;
struct ReebArc;
struct ReebEdge;
struct ReebNode;

typedef struct ReebGraph {
	ListBase arcs;
	ListBase nodes;
	int totnodes;
	struct EdgeHash *emap;
} ReebGraph;

typedef struct EmbedBucket {
	float val;
	int	  nv;
	float p[3];
} EmbedBucket;

typedef struct ReebNode {
	struct ReebNode *next, *prev;
	struct ReebArc **arcs;
	int index;
	int degree;
	float weight;
	float p[3];
} ReebNode;

typedef struct ReebEdge {
	struct ReebEdge *next, *prev;
	struct ReebArc  *arc;
	struct ReebNode *v1, *v2;
	struct ReebEdge *nextEdge;
} ReebEdge;

typedef struct ReebArc {
	struct ReebArc *next, *prev;
	ListBase edges;
	struct ReebNode *v1, *v2;
	int	bcount;
	struct EmbedBucket *buckets;
} ReebArc;

struct EditMesh;

void weightToHarmonic(struct EditMesh *em);
void weightFromDistance(struct EditMesh *em);
void weightFromLoc(struct EditMesh *me, int axis);
void renormalizeWeight(struct EditMesh *em, float newmax);
void filterReebGraph(ReebGraph *rg, float threshold);
struct ReebGraph * generateReebGraph(struct EditMesh *me, int subdivisions);

#endif /*REEB_H_*/
