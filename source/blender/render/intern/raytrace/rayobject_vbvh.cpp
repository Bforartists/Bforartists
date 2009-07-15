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
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): André Pinto.
 *
 * ***** END GPL LICENSE BLOCK *****
 */
extern "C"
{
#include <assert.h>
#include "MEM_guardedalloc.h"
#include "BKE_utildefines.h"
#include "BLI_arithb.h"
#include "BLI_memarena.h"
#include "RE_raytrace.h"
#include "rayobject_rtbuild.h"
#include "rayobject.h"
};

#include "bvh.h"
#include <queue>

#define BVHNode VBVHNode
#define BVHTree VBVHTree

#define RAY_BB_TEST_COST (0.2f)
#define DFS_STACK_SIZE	128
#define DYNAMIC_ALLOC

//#define rtbuild_split	rtbuild_mean_split_largest_axis		/* objects mean split on the longest axis, childs BB are allowed to overlap */
//#define rtbuild_split	rtbuild_median_split_largest_axis	/* space median split on the longest axis, childs BB are allowed to overlap */
#define rtbuild_split	rtbuild_heuristic_object_split		/* split objects using heuristic */

struct BVHNode
{
	BVHNode *child;
	BVHNode *sibling;

	float	bb[6];
};

struct BVHTree
{
	RayObject rayobj;

	BVHNode *root;

	MemArena *node_arena;

	float cost;
	RTBuilder *builder;
};


/*
 * Push nodes (used on dfs)
 */
template<class Node>
inline static void bvh_node_push_childs(Node *node, Isect *isec, Node **stack, int &stack_pos)
{
	Node *child = node->child;
	while(child)
	{
		stack[stack_pos++] = child;
		if(RayObject_isAligned(child))
			child = child->sibling;
		else break;
	}
}

/*
 * BVH done
 */
static BVHNode *bvh_new_node(BVHTree *tree)
{
	BVHNode *node = (BVHNode*)BLI_memarena_alloc(tree->node_arena, sizeof(BVHNode));
	node->sibling = NULL;
	node->child   = NULL;

	assert(RayObject_isAligned(node));
	return node;
}

template<class Builder>
float rtbuild_area(Builder *builder)
{
	float min[3], max[3];
	INIT_MINMAX(min, max);
	rtbuild_merge_bb(builder, min, max);
	return bb_area(min, max);	
}

template<class Node>
void bvh_update_bb(Node *node)
{
	INIT_MINMAX(node->bb, node->bb+3);
	Node *child = node->child;
	
	while(child)
	{
		bvh_node_merge_bb(child, node->bb, node->bb+3);
		if(RayObject_isAligned(child))
			child = child->sibling;
		else
			child = 0;
	}
}


static int tot_pushup   = 0;
static int tot_pushdown = 0;
static int tot_hints    = 0;

template<class Node>
void pushdown(Node *parent)
{
	Node **s_child = &parent->child;
	Node * child = parent->child;
	
	while(child && RayObject_isAligned(child))
	{
		Node *next = child->sibling;
		Node **next_s_child = &child->sibling;
		
		//assert(bb_fits_inside(parent->bb, parent->bb+3, child->bb, child->bb+3));
		
		for(Node *i = parent->child; RayObject_isAligned(i) && i; i = i->sibling)
		if(child != i && bb_fits_inside(i->bb, i->bb+3, child->bb, child->bb+3))
		{
//			todo optimize (hsould the one with the smallest area
//			float ia = bb_area(i->bb, i->bb+3)
//			if(child->i)
			*s_child = child->sibling;
			child->sibling = i->child;
			i->child = child;
			next_s_child = s_child;
			
			tot_pushdown++;
			break;
		}
		child = next;
		s_child = next_s_child;
	}
	
	for(Node *i = parent->child; RayObject_isAligned(i) && i; i = i->sibling)
		pushdown( i );	
}

template<class Tree, class Node, class Builder>
Node *bvh_rearrange(Tree *tree, Builder *builder, float *cost)
{
	
	int size = rtbuild_size(builder);
	if(size == 1)
	{
		Node *node = bvh_new_node(tree);
		INIT_MINMAX(node->bb, node->bb+3);
		rtbuild_merge_bb(builder, node->bb, node->bb+3);
		
		node->child = (BVHNode*)builder->begin[0];

		*cost = RE_rayobject_cost((RayObject*)node->child)+RAY_BB_TEST_COST;
		return node;
	}
	else
	{
		Node *node = bvh_new_node(tree);
		float parent_area;
		
		INIT_MINMAX(node->bb, node->bb+3);
		rtbuild_merge_bb(builder, node->bb, node->bb+3);
		
		parent_area = bb_area( node->bb, node->bb+3 );
		Node **child = &node->child;
		
		std::queue<Builder> childs;
		childs.push(*builder);
		
		*cost = 0;
		
		while(!childs.empty())
		{
			Builder b = childs.front();
						childs.pop();
			
			float hit_prob = rtbuild_area(&b) / parent_area;
			if(hit_prob > 1.0f / 2.0f && rtbuild_size(&b) > 1)
			{
				//The expected number of BB test is smaller if we directly add the 2 childs of this node
				int nc = rtbuild_split(&b, 2);
				assert(nc == 2);
				for(int i=0; i<nc; i++)
				{
					Builder tmp;
					rtbuild_get_child(&b, i, &tmp);
					childs.push(tmp);
				}
				tot_pushup++;
				
			}
			else
			{
				float tcost;
				*child = bvh_rearrange<Tree,Node,Builder>(tree, &b, &tcost);
				child = &((*child)->sibling);
				
				*cost += tcost*hit_prob + RAY_BB_TEST_COST;
			}
		}
		assert(child != &node->child);
		*child = 0;

		return node;
	}
}

template<>
void bvh_done<BVHTree>(BVHTree *obj)
{
	int needed_nodes = (rtbuild_size(obj->builder)+1)*2;
	if(needed_nodes > BLI_MEMARENA_STD_BUFSIZE)
		needed_nodes = BLI_MEMARENA_STD_BUFSIZE;

	obj->node_arena = BLI_memarena_new(needed_nodes);
	BLI_memarena_use_malloc(obj->node_arena);

	
	obj->root = bvh_rearrange<BVHTree,BVHNode,RTBuilder>( obj, obj->builder, &obj->cost );
	pushdown(obj->root);
	obj->cost = 1.0;
	
	rtbuild_free( obj->builder );
	obj->builder = NULL;
}

template<int StackSize>
int intersect(BVHTree *obj, Isect* isec)
{
	if(isec->hint)
	{
		LCTSHint *lcts = (LCTSHint*)isec->hint;
		isec->hint = 0;
		
		int hit = 0;
		for(int i=0; i<lcts->size; i++)
		{
			BVHNode *node = (BVHNode*)lcts->stack[i];
			if(RayObject_isAligned(node))
				hit |= bvh_node_stack_raycast<BVHNode,StackSize,true>(node, isec);
			else
				hit |= RE_rayobject_intersect( (RayObject*)node, isec );
			
			if(hit && isec->mode == RE_RAY_SHADOW)
				break;
		}
		isec->hint = (RayHint*)lcts;
		return hit;
	}
	else
	{
		if(RayObject_isAligned(obj->root))
			return bvh_node_stack_raycast<BVHNode,StackSize,false>(obj->root, isec);
		else
			return RE_rayobject_intersect( (RayObject*) obj->root, isec );
	}
}

template<class Node>
void bvh_dfs_make_hint(Node *node, LCTSHint *hint, int reserve_space, float *min, float *max);

template<class Node>
void bvh_dfs_make_hint_push_siblings(Node *node, LCTSHint *hint, int reserve_space, float *min, float *max)
{
	if(!RayObject_isAligned(node))
		hint->stack[hint->size++] = (RayObject*)node;
	else
	{
		if(node->sibling)
			bvh_dfs_make_hint_push_siblings(node->sibling, hint, reserve_space+1, min, max);

		bvh_dfs_make_hint(node, hint, reserve_space, min, max);
	}
		
	
}

template<class Node>
void bvh_dfs_make_hint(Node *node, LCTSHint *hint, int reserve_space, float *min, float *max)
{
	assert( hint->size - reserve_space + 1 <= RE_RAY_LCTS_MAX_SIZE );
	
	if(hint->size - reserve_space + 1 == RE_RAY_LCTS_MAX_SIZE || !RayObject_isAligned(node))
		hint->stack[hint->size++] = (RayObject*)node;
	else
	{
		/* We are 100% sure the ray will be pass inside this node */
		if(bb_fits_inside(node->bb, node->bb+3, min, max) )
		{
			bvh_dfs_make_hint_push_siblings(node->child, hint, reserve_space, min, max);
		}
		else
		{
			hint->stack[hint->size++] = (RayObject*)node;
		}
	}
}

template<class Tree>
void bvh_hint_bb(Tree *tree, LCTSHint *hint, float *min, float *max)
{
	hint->size = 0;
	bvh_dfs_make_hint( tree->root, hint, 0, min, max );
	tot_hints++;
}

void bfree(BVHTree *tree)
{
	if(tot_pushup + tot_pushdown + tot_hints)
	{
		printf("tot pushups: %d\n", tot_pushup);
		printf("tot pushdowns: %d\n", tot_pushdown);
		printf("tot hints created: %d\n", tot_hints);
		tot_pushup = 0;
		tot_pushdown = 0;
		tot_hints = 0;
	}
	bvh_free(tree);
}

/* the cast to pointer function is needed to workarround gcc bug: http://gcc.gnu.org/bugzilla/show_bug.cgi?id=11407 */
template<int STACK_SIZE>
static RayObjectAPI make_api()
{
	static RayObjectAPI api = 
	{
		(RE_rayobject_raycast_callback) ((int(*)(BVHTree*,Isect*)) &intersect<STACK_SIZE>),
		(RE_rayobject_add_callback)     ((void(*)(BVHTree*,RayObject*)) &bvh_add<BVHTree>),
		(RE_rayobject_done_callback)    ((void(*)(BVHTree*))       &bvh_done<BVHTree>),
//		(RE_rayobject_free_callback)    ((void(*)(BVHTree*))       &bvh_free<BVHTree>),
		(RE_rayobject_free_callback)    ((void(*)(BVHTree*))       &bfree),
		(RE_rayobject_merge_bb_callback)((void(*)(BVHTree*,float*,float*)) &bvh_bb<BVHTree>),
		(RE_rayobject_cost_callback)	((float(*)(BVHTree*))      &bvh_cost<BVHTree>),
		(RE_rayobject_hint_bb_callback)	((void(*)(BVHTree*,LCTSHint*,float*,float*)) &bvh_hint_bb<BVHTree>)
	};
	
	return api;
}

static RayObjectAPI* get_api(int maxstacksize)
{
//	static RayObjectAPI bvh_api16  = make_api<16>();
//	static RayObjectAPI bvh_api32  = make_api<32>();
//	static RayObjectAPI bvh_api64  = make_api<64>();
	static RayObjectAPI bvh_api128 = make_api<128>();
	static RayObjectAPI bvh_api256 = make_api<256>();
	
//	if(maxstacksize <= 16 ) return &bvh_api16;
//	if(maxstacksize <= 32 ) return &bvh_api32;
//	if(maxstacksize <= 64 ) return &bvh_api64;
	if(maxstacksize <= 128) return &bvh_api128;
	if(maxstacksize <= 256) return &bvh_api256;
	assert(maxstacksize <= 256);
	return 0;
}

RayObject *RE_rayobject_vbvh_create(int size)
{
	BVHTree *obj= (BVHTree*)MEM_callocN(sizeof(BVHTree), "BVHTree");
	assert( RayObject_isAligned(obj) ); /* RayObject API assumes real data to be 4-byte aligned */	
	
	obj->rayobj.api = get_api(DFS_STACK_SIZE);
	obj->root = NULL;
	
	obj->node_arena = NULL;
	obj->builder    = rtbuild_create( size );
	
	return RayObject_unalignRayAPI((RayObject*) obj);
}
