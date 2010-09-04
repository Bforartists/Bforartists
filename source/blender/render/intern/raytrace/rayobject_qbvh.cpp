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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
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
#include "MEM_guardedalloc.h"
#include "vbvh.h"
#include "svbvh.h"
#include "reorganize.h"

#ifdef __SSE__

#define DFS_STACK_SIZE	256

struct QBVHTree
{
	RayObject rayobj;

	SVBVHNode *root;
	MemArena *node_arena;

	float cost;
	RTBuilder *builder;
};


template<>
void bvh_done<QBVHTree>(QBVHTree *obj)
{
	rtbuild_done(obj->builder, &obj->rayobj.control);
	
	//TODO find a away to exactly calculate the needed memory
	MemArena *arena1 = BLI_memarena_new(BLI_MEMARENA_STD_BUFSIZE, "qbvh arena");
					   BLI_memarena_use_malloc(arena1);

	MemArena *arena2 = BLI_memarena_new(BLI_MEMARENA_STD_BUFSIZE, "qbvh arena 2");
					   BLI_memarena_use_malloc(arena2);
					   BLI_memarena_use_align(arena2, 16);

	//Build and optimize the tree	
	//TODO do this in 1 pass (half memory usage during building)	
	VBVHNode *root = BuildBinaryVBVH<VBVHNode>(arena1, &obj->rayobj.control).transform(obj->builder);	
	
	if(RE_rayobjectcontrol_test_break(&obj->rayobj.control))
	{
		BLI_memarena_free(arena1);
		BLI_memarena_free(arena2);
		return;
	}
	
	pushup_simd<VBVHNode,4>(root);					   
	obj->root = Reorganize_SVBVH<VBVHNode>(arena2).transform(root);
	
	//Cleanup
	BLI_memarena_free(arena1);	
	
	rtbuild_free( obj->builder );
	obj->builder = NULL;

	obj->node_arena = arena2;
	obj->cost = 1.0;	
}


template<int StackSize>
int intersect(QBVHTree *obj, Isect* isec)
{
	//TODO renable hint support
	if(RE_rayobject_isAligned(obj->root))
		return bvh_node_stack_raycast<SVBVHNode,StackSize,false>( obj->root, isec);
	else
		return RE_rayobject_intersect( (RayObject*) obj->root, isec );
}

template<class Tree>
void bvh_hint_bb(Tree *tree, LCTSHint *hint, float *min, float *max)
{
	//TODO renable hint support
	{
	 	hint->size = 0;
	 	hint->stack[hint->size++] = (RayObject*)tree->root;
	}
}
/* the cast to pointer function is needed to workarround gcc bug: http://gcc.gnu.org/bugzilla/show_bug.cgi?id=11407 */
template<class Tree, int STACK_SIZE>
RayObjectAPI make_api()
{
	static RayObjectAPI api = 
	{
		(RE_rayobject_raycast_callback) ((int(*)(Tree*,Isect*)) &intersect<STACK_SIZE>),
		(RE_rayobject_add_callback)     ((void(*)(Tree*,RayObject*)) &bvh_add<Tree>),
		(RE_rayobject_done_callback)    ((void(*)(Tree*))       &bvh_done<Tree>),
		(RE_rayobject_free_callback)    ((void(*)(Tree*))       &bvh_free<Tree>),
		(RE_rayobject_merge_bb_callback)((void(*)(Tree*,float*,float*)) &bvh_bb<Tree>),
		(RE_rayobject_cost_callback)	((float(*)(Tree*))      &bvh_cost<Tree>),
		(RE_rayobject_hint_bb_callback)	((void(*)(Tree*,LCTSHint*,float*,float*)) &bvh_hint_bb<Tree>)
	};
	
	return api;
}

template<class Tree>
RayObjectAPI* bvh_get_api(int maxstacksize)
{
	static RayObjectAPI bvh_api256 = make_api<Tree,1024>();
	
	if(maxstacksize <= 1024) return &bvh_api256;
	assert(maxstacksize <= 256);
	return 0;
}


RayObject *RE_rayobject_qbvh_create(int size)
{
	return bvh_create_tree<QBVHTree,DFS_STACK_SIZE>(size);
}


#else

RayObject *RE_rayobject_qbvh_create(int size)
{
	puts("WARNING: SSE disabled at compile time\n");
	return NULL;
}

#endif
