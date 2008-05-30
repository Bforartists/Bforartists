/**
 * $Id:
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
 * Contributor(s): Martin Poirier
 *
 * ***** END GPL LICENSE BLOCK *****
 * graph.c: Common graph interface and methods
 */

#include <float.h> 
#include <math.h>

#include "MEM_guardedalloc.h"

#include "BLI_graph.h"
#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "BKE_utildefines.h"

static void testRadialSymmetry(BGraph *graph, BNode* root_node, RadialArc* ring, int total, float axis[3], float limit, int group);

static void handleAxialSymmetry(BGraph *graph, BNode *root_node, int depth, float axis[3], float limit);
static void testAxialSymmetry(BGraph *graph, BNode* root_node, BNode* node1, BNode* node2, BArc* arc1, BArc* arc2, float axis[3], float limit, int group);
static void flagAxialSymmetry(BNode *root_node, BNode *end_node, BArc *arc, int group);

void BLI_freeNode(BGraph *graph, BNode *node)
{
	if (node->arcs)
	{
		MEM_freeN(node->arcs);
	}
	
	if (graph->free_node)
	{
		graph->free_node(node);
	}
}

BNode *BLI_otherNode(BArc *arc, BNode *node)
{
	return (arc->head == node) ? arc->tail : arc->head;
}

void BLI_flagNodes(BGraph *graph, int flag)
{
	BNode *node;
	
	for(node = graph->nodes.first; node; node = node->next)
	{
		node->flag = flag;
	}
}

void BLI_flagArcs(BGraph *graph, int flag)
{
	BArc *arc;
	
	for(arc = graph->arcs.first; arc; arc = arc->next)
	{
		arc->flag = flag;
	}
}

static void addArcToNodeAdjacencyList(BNode *node, BArc *arc)
{
	node->arcs[node->degree] = arc;
	node->degree++;
}

void BLI_buildAdjacencyList(BGraph *rg)
{
	BNode *node;
	BArc *arc;

	for(node = rg->nodes.first; node; node = node->next)
	{
		if (node->arcs != NULL)
		{
			MEM_freeN(node->arcs);
		}
		
		node->arcs = MEM_callocN((node->degree) * sizeof(BArc*), "adjacency list");
		
		/* temporary use to indicate the first index available in the lists */
		node->degree = 0;
	}

	for(arc = rg->arcs.first; arc; arc= arc->next)
	{
		addArcToNodeAdjacencyList(arc->head, arc);
		addArcToNodeAdjacencyList(arc->tail, arc);
	}
}

int BLI_hasAdjacencyList(BGraph *rg)
{
	BNode *node;
	
	for(node = rg->nodes.first; node; node = node->next)
	{
		if (node->arcs == NULL)
		{
			return 0;
		}
	}
	
	return 1;
}

void BLI_replaceNode(BGraph *graph, BNode *node_src, BNode *node_replaced)
{
	BArc *arc, *next_arc;
	
	for (arc = graph->arcs.first; arc; arc = next_arc)
	{
		next_arc = arc->next;
		
		if (arc->head == node_replaced)
		{
			arc->head = node_src;
			node_src->degree++;
		}

		if (arc->tail == node_replaced)
		{
			arc->tail = node_src;
			node_src->degree++;
		}
		
		if (arc->head == arc->tail)
		{
			node_src->degree -= 2;
			
			graph->free_arc(arc);
			BLI_freelinkN(&graph->arcs, arc);
		}
	}
}

void BLI_removeDoubleNodes(BGraph *graph, float limit)
{
	BNode *node_src, *node_replaced;
	
	for(node_src = graph->nodes.first; node_src; node_src = node_src->next)
	{
		for(node_replaced = graph->nodes.first; node_replaced; node_replaced = node_replaced->next)
		{
			if (node_replaced != node_src && VecLenf(node_replaced->p, node_src->p) <= limit)
			{
				BLI_replaceNode(graph, node_src, node_replaced);
				
				BLI_freeNode(graph, node_replaced);
				BLI_remlink(&graph->nodes, node_replaced);
			}
		}
	}
	
}

/*************************************** CYCLE DETECTION ***********************************************/

int detectCycle(BNode *node, BArc *src_arc)
{
	int value = 0;
	
	if (node->flag == 0)
	{
		int i;

		/* mark node as visited */
		node->flag = 1;

		for(i = 0; i < node->degree && value == 0; i++)
		{
			BArc *arc = node->arcs[i];
			
			/* don't go back on the source arc */
			if (arc != src_arc)
			{
				value = detectCycle(BLI_otherNode(arc, node), arc);
			}
		}
	}
	else
	{
		value = 1;
	}
	
	return value;
}

int	BLI_isGraphCyclic(BGraph *graph)
{
	BNode *node;
	int value = 0;
	
	/* NEED TO CHECK IF ADJACENCY LIST EXIST */
	
	/* Mark all nodes as not visited */
	BLI_flagNodes(graph, 0);

	/* detectCycles in subgraphs */	
	for(node = graph->nodes.first; node && value == 0; node = node->next)
	{
		/* only for nodes in subgraphs that haven't been visited yet */
		if (node->flag == 0)
		{
			value = value || detectCycle(node, NULL);
		}		
	}
	
	return value;
}

BArc * BLI_findConnectedArc(BGraph *graph, BArc *arc, BNode *v)
{
	BArc *nextArc = arc->next;
	
	for(nextArc = graph->arcs.first; nextArc; nextArc = nextArc->next)
	{
		if (arc != nextArc && (nextArc->head == v || nextArc->tail == v))
		{
			break;
		}
	}
	
	return nextArc;
}

/*********************************** GRAPH AS TREE FUNCTIONS *******************************************/

int BLI_subtreeDepth(BNode *node, BArc *rootArc)
{
	int depth = 0;
	
	/* Base case, no arcs leading away */
	if (node->arcs == NULL || *(node->arcs) == NULL)
	{
		return 0;
	}
	else
	{
		int i;

		for(i = 0; i < node->degree; i++)
		{
			BArc *arc = node->arcs[i];
			
			/* only arcs that go down the tree */
			if (arc != rootArc)
			{
				BNode *newNode = BLI_otherNode(arc, node);
				depth = MAX2(depth, BLI_subtreeDepth(newNode, arc));
			}
		}
	}
	
	return depth + 1; //BLI_countlist(&rootArc->edges);
}

/********************************* SYMMETRY DETECTION **************************************************/

void markdownSymmetryArc(BGraph *graph, BArc *arc, BNode *node, int level, float limit);

void BLI_mirrorAlongAxis(float v[3], float center[3], float axis[3])
{
	float dv[3], pv[3];
	
	VecSubf(dv, v, center);
	Projf(pv, dv, axis);
	VecMulf(pv, -2);
	VecAddf(v, v, pv);
}

static void testRadialSymmetry(BGraph *graph, BNode* root_node, RadialArc* ring, int total, float axis[3], float limit, int group)
{
	int symmetric = 1;
	int i;
	
	/* sort ring by angle */
	for (i = 0; i < total - 1; i++)
	{
		float minAngle = FLT_MAX;
		int minIndex = -1;
		int j;

		for (j = i + 1; j < total; j++)
		{
			float angle = Inpf(ring[i].n, ring[j].n);

			/* map negative values to 1..2 */
			if (angle < 0)
			{
				angle = 1 - angle;
			}

			if (angle < minAngle)
			{
				minIndex = j;
				minAngle = angle;
			}
		}

		/* swap if needed */
		if (minIndex != i + 1)
		{
			RadialArc tmp;
			tmp = ring[i + 1];
			ring[i + 1] = ring[minIndex];
			ring[minIndex] = tmp;
		}
	}

	for (i = 0; i < total && symmetric; i++)
	{
		BNode *node1, *node2;
		float tangent[3];
		float normal[3];
		float p[3];
		int j = (i + 1) % total; /* next arc in the circular list */

		VecAddf(tangent, ring[i].n, ring[j].n);
		Crossf(normal, tangent, axis);
		
		node1 = BLI_otherNode(ring[i].arc, root_node);
		node2 = BLI_otherNode(ring[j].arc, root_node);

		VECCOPY(p, node2->p);
		BLI_mirrorAlongAxis(p, root_node->p, normal);
		
		/* check if it's within limit before continuing */
		if (VecLenf(node1->p, p) > limit)
		{
			symmetric = 0;
		}

	}

	if (symmetric)
	{
		/* mark node as symmetric physically */
		VECCOPY(root_node->symmetry_axis, axis);
		root_node->symmetry_flag |= SYM_PHYSICAL;
		root_node->symmetry_flag |= SYM_RADIAL;
		
		/* FLAG SYMMETRY GROUP */
		for (i = 0; i < total; i++)
		{
			ring[i].arc->symmetry_group = group;
			ring[i].arc->symmetry_flag = i;
		}

		if (graph->radial_symmetry)
		{
			graph->radial_symmetry(root_node, ring, total);
		}
	}
}

static void handleRadialSymmetry(BGraph *graph, BNode *root_node, int depth, float axis[3], float limit)
{
	RadialArc *ring = NULL;
	RadialArc *unit;
	int total = 0;
	int group;
	int first;
	int i;

	/* mark topological symmetry */
	root_node->symmetry_flag |= SYM_TOPOLOGICAL;

	/* total the number of arcs in the symmetry ring */
	for (i = 0; i < root_node->degree; i++)
	{
		BArc *connectedArc = root_node->arcs[i];
		
		/* depth is store as a negative in flag. symmetry level is positive */
		if (connectedArc->symmetry_level == -depth)
		{
			total++;
		}
	}

	ring = MEM_callocN(sizeof(RadialArc) * total, "radial symmetry ring");
	unit = ring;

	/* fill in the ring */
	for (unit = ring, i = 0; i < root_node->degree; i++)
	{
		BArc *connectedArc = root_node->arcs[i];
		
		/* depth is store as a negative in flag. symmetry level is positive */
		if (connectedArc->symmetry_level == -depth)
		{
			BNode *otherNode = BLI_otherNode(connectedArc, root_node);
			float vec[3];

			unit->arc = connectedArc;

			/* project the node to node vector on the symmetry plane */
			VecSubf(unit->n, otherNode->p, root_node->p);
			Projf(vec, unit->n, axis);
			VecSubf(unit->n, unit->n, vec);

			Normalize(unit->n);

			unit++;
		}
	}

	/* sort ring by arc length
	 * using a rather bogus insertion sort
	 * butrings will never get too big to matter
	 * */
	for (i = 0; i < total; i++)
	{
		int j;

		for (j = i - 1; j >= 0; j--)
		{
			BArc *arc1, *arc2;
			
			arc1 = ring[j].arc;
			arc2 = ring[j + 1].arc;
			
			if (arc1->length > arc2->length)
			{
				/* swap with smaller */
				RadialArc tmp;
				tmp = ring[j + 1];
				ring[j + 1] = ring[j];
				ring[j] = tmp;
			}
			else
			{
				break;
			}
		}
	}

	/* Dispatch to specific symmetry tests */
	first = 0;
	group = 0;
	
	for (i = 1; i < total; i++)
	{
		int dispatch = 0;
		int last = i - 1;
		
		if (fabs(ring[first].arc->length - ring[i].arc->length) > limit)
		{
			dispatch = 1;
		}

		/* if not dispatching already and on last arc
		 * Dispatch using current arc as last
		 * */		
		if (dispatch == 0 && i == total - 1)
		{
			last = i;
			dispatch = 1;
		} 
		
		if (dispatch)
		{
			int sub_total = last - first + 1; 

			group += 1;

			if (sub_total == 1)
			{
				printf("no dispatch\n");
				/* NOTHING TO DO */
			}
			else if (sub_total == 2)
			{
				BArc *arc1, *arc2;
				BNode *node1, *node2;
				
				printf("dispatch axial\n");

				arc1 = ring[first].arc;
				arc2 = ring[last].arc;
				
				node1 = BLI_otherNode(arc1, root_node);
				node2 = BLI_otherNode(arc2, root_node);
				
				testAxialSymmetry(graph, root_node, node1, node2, arc1, arc2, axis, limit, group);
			}
			else if (sub_total != total) /* allocate a new sub ring if needed */
			{
				RadialArc *sub_ring = MEM_callocN(sizeof(RadialArc) * sub_total, "radial symmetry ring");
				int sub_i;
				
				printf("dispatch radial sub ring\n");

				/* fill in the sub ring */
				for (sub_i = 0; sub_i < sub_total; sub_i++)
				{
					sub_ring[sub_i] = ring[first + sub_i];
				}
				
				testRadialSymmetry(graph, root_node, sub_ring, sub_total, axis, limit, group);
			
				MEM_freeN(sub_ring);
			}
			else if (sub_total == total)
			{
				printf("dispatch radial full ring\n");

				testRadialSymmetry(graph, root_node, ring, total, axis, limit, group);
			}
			
			first = i;
		}
	}


	MEM_freeN(ring);
}

static void flagAxialSymmetry(BNode *root_node, BNode *end_node, BArc *arc, int group)
{
	float vec[3];
	
	arc->symmetry_group = group;
	
	VecSubf(vec, end_node->p, root_node->p);
	
	if (Inpf(vec, root_node->symmetry_axis) < 0)
	{
		arc->symmetry_flag |= SYM_SIDE_NEGATIVE;
	}
	else
	{
		arc->symmetry_flag |= SYM_SIDE_POSITIVE;
	}
}

static void testAxialSymmetry(BGraph *graph, BNode* root_node, BNode* node1, BNode* node2, BArc* arc1, BArc* arc2, float axis[3], float limit, int group)
{
	float nor[3], vec[3], p[3];

	VecSubf(vec, node1->p, root_node->p);
	Normalize(vec);
	VecSubf(p, root_node->p, node2->p);
	Normalize(p);
	VecAddf(p, p, vec);

	Crossf(vec, p, axis);
	Crossf(nor, vec, axis);
	
	/* mirror node2 along axis */
	VECCOPY(p, node2->p);
	BLI_mirrorAlongAxis(p, root_node->p, nor);
	
	/* check if it's within limit before continuing */
	if (VecLenf(node1->p, p) <= limit)
	{
		/* mark node as symmetric physically */
		VECCOPY(root_node->symmetry_axis, nor);
		root_node->symmetry_flag |= SYM_PHYSICAL;
		root_node->symmetry_flag |= SYM_AXIAL;

		/* flag side on arcs */
		flagAxialSymmetry(root_node, node1, arc1, group);
		flagAxialSymmetry(root_node, node2, arc2, group);
		
		if (graph->axial_symmetry)
		{
			graph->axial_symmetry(root_node, node1, node2, arc1, arc2);
		}
	}
}

static void handleAxialSymmetry(BGraph *graph, BNode *root_node, int depth, float axis[3], float limit)
{
	BArc *arc1 = NULL, *arc2 = NULL;
	BNode *node1 = NULL, *node2 = NULL;
	int i;
	
	/* mark topological symmetry */
	root_node->symmetry_flag |= SYM_TOPOLOGICAL;

	for (i = 0; i < root_node->degree; i++)
	{
		BArc *connectedArc = root_node->arcs[i];
		
		/* depth is store as a negative in flag. symmetry level is positive */
		if (connectedArc->symmetry_level == -depth)
		{
			if (arc1 == NULL)
			{
				arc1 = connectedArc;
				node1 = BLI_otherNode(arc1, root_node);
			}
			else
			{
				arc2 = connectedArc;
				node2 = BLI_otherNode(arc2, root_node);
				break; /* Can stop now, the two arcs have been found */
			}
		}
	}
	
	/* shouldn't happen, but just to be sure */
	if (node1 == NULL || node2 == NULL)
	{
		return;
	}
	
	printf("symmetry length %f <> %f\n", arc1->length, arc2->length);
	
	testAxialSymmetry(graph, root_node, node1, node2, arc1, arc2, axis, limit, 1);
}

static void markdownSecondarySymmetry(BGraph *graph, BNode *node, int depth, int level, float limit)
{
	float axis[3] = {0, 0, 0};
	int count = 0;
	int i;

	/* count the number of branches in this symmetry group
	 * and determinte the axis of symmetry
	 *  */	
	for (i = 0; i < node->degree; i++)
	{
		BArc *connectedArc = node->arcs[i];
		
		/* depth is store as a negative in flag. symmetry level is positive */
		if (connectedArc->symmetry_level == -depth)
		{
			count++;
		}
		/* If arc is on the axis */
		else if (connectedArc->symmetry_level == level)
		{
			VecAddf(axis, axis, connectedArc->head->p);
			VecSubf(axis, axis, connectedArc->tail->p);
		}
	}

	Normalize(axis);

	/* Split between axial and radial symmetry */
	if (count == 2)
	{
		handleAxialSymmetry(graph, node, depth, axis, limit);
	}
	else
	{
		handleRadialSymmetry(graph, node, depth, axis, limit);
	}
	
	/* markdown secondary symetries */	
	for (i = 0; i < node->degree; i++)
	{
		BArc *connectedArc = node->arcs[i];
		
		if (connectedArc->symmetry_level == -depth)
		{
			/* markdown symmetry for branches corresponding to the depth */
			markdownSymmetryArc(graph, connectedArc, node, level + 1, limit);
		}
	}
}

void markdownSymmetryArc(BGraph *graph, BArc *arc, BNode *node, int level, float limit)
{
	int i;
	arc->symmetry_level = level;
	
	node = BLI_otherNode(arc, node);
	
	for (i = 0; i < node->degree; i++)
	{
		BArc *connectedArc = node->arcs[i];
		
		if (connectedArc != arc)
		{
			BNode *connectedNode = BLI_otherNode(connectedArc, node);
			
			/* symmetry level is positive value, negative values is subtree depth */
			connectedArc->symmetry_level = -BLI_subtreeDepth(connectedNode, connectedArc);
		}
	}

	arc = NULL;

	for (i = 0; i < node->degree; i++)
	{
		int issymmetryAxis = 0;
		BArc *connectedArc = node->arcs[i];
		
		/* only arcs not already marked as symetric */
		if (connectedArc->symmetry_level < 0)
		{
			int j;
			
			/* true by default */
			issymmetryAxis = 1;
			
			for (j = 0; j < node->degree && issymmetryAxis == 1; j++)
			{
				BArc *otherArc = node->arcs[j];
				
				/* different arc, same depth */
				if (otherArc != connectedArc && otherArc->symmetry_level == connectedArc->symmetry_level)
				{
					/* not on the symmetry axis */
					issymmetryAxis = 0;
				} 
			}
		}
		
		/* arc could be on the symmetry axis */
		if (issymmetryAxis == 1)
		{
			/* no arc as been marked previously, keep this one */
			if (arc == NULL)
			{
				arc = connectedArc;
			}
			else
			{
				/* there can't be more than one symmetry arc */
				arc = NULL;
				break;
			}
		}
	}
	
	/* go down the arc continuing the symmetry axis */
	if (arc)
	{
		markdownSymmetryArc(graph, arc, node, level, limit);
	}

	
	/* secondary symmetry */
	for (i = 0; i < node->degree; i++)
	{
		BArc *connectedArc = node->arcs[i];
		
		/* only arcs not already marked as symetric and is not the next arc on the symmetry axis */
		if (connectedArc->symmetry_level < 0)
		{
			/* subtree depth is store as a negative value in the symmetry */
			markdownSecondarySymmetry(graph, node, -connectedArc->symmetry_level, level, limit);
		}
	}
}

void BLI_markdownSymmetry(BGraph *graph, BNode *root_node, float limit)
{
	BNode *node;
	BArc *arc;
	
	if (BLI_isGraphCyclic(graph))
	{
		return;
	}
	
	/* mark down all arcs as non-symetric */
	BLI_flagArcs(graph, 0);
	
	/* mark down all nodes as not on the symmetry axis */
	BLI_flagNodes(graph, 0);

	node = root_node;
	
	/* only work on acyclic graphs and if only one arc is incident on the first node */
	if (node->degree == 1)
	{
		arc = node->arcs[0];
		
		markdownSymmetryArc(graph, arc, node, 1, limit);

		/* mark down non-symetric arcs */
		for (arc = graph->arcs.first; arc; arc = arc->next)
		{
			if (arc->symmetry_level < 0)
			{
				arc->symmetry_level = 0;
			}
			else
			{
				/* mark down nodes with the lowest level symmetry axis */
				if (arc->head->symmetry_level == 0 || arc->head->symmetry_level > arc->symmetry_level)
				{
					arc->head->symmetry_level = arc->symmetry_level;
				}
				if (arc->tail->symmetry_level == 0 || arc->tail->symmetry_level > arc->symmetry_level)
				{
					arc->tail->symmetry_level = arc->symmetry_level;
				}
			}
		}
	}
}

