/*
 * Adapted from code copyright 2009-2010 NVIDIA Corporation
 * Modifications Copyright 2011, Blender Foundation.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "bvh_binning.h"
#include "bvh_build.h"
#include "bvh_node.h"
#include "bvh_params.h"
#include "bvh_split.h"

#include "mesh.h"
#include "object.h"
#include "scene.h"
#include "curves.h"

#include "util_debug.h"
#include "util_foreach.h"
#include "util_logging.h"
#include "util_progress.h"
#include "util_time.h"

CCL_NAMESPACE_BEGIN

#if !defined(__KERNEL_SSE2__)
/* TODO(sergey): Move to some generic header so all code
 * can use bitscan on non-SSE processors.
 */
ccl_device_inline int bitscan(int value)
{
	assert(value != 0);
	int bit = 0;
	while(value >>= 1) {
		++bit;
	}
	return bit;
}
#endif

/* BVH Build Task */

class BVHBuildTask : public Task {
public:
	BVHBuildTask(BVHBuild *build, InnerNode *node, int child, BVHObjectBinning& range_, int level)
	: range(range_)
	{
		run = function_bind(&BVHBuild::thread_build_node, build, node, child, &range, level);
	}

	BVHObjectBinning range;
};

/* Constructor / Destructor */

BVHBuild::BVHBuild(const vector<Object*>& objects_,
                   array<int>& prim_type_,
                   array<int>& prim_index_,
                   array<int>& prim_object_,
                   const BVHParams& params_,
                   Progress& progress_)
 : objects(objects_),
   prim_type(prim_type_),
   prim_index(prim_index_),
   prim_object(prim_object_),
   params(params_),
   progress(progress_),
   progress_start_time(0.0)
{
	spatial_min_overlap = 0.0f;
}

BVHBuild::~BVHBuild()
{
}

/* Adding References */

void BVHBuild::add_reference_mesh(BoundBox& root, BoundBox& center, Mesh *mesh, int i)
{
	Attribute *attr_mP = NULL;
	
	if(mesh->has_motion_blur())
		attr_mP = mesh->attributes.find(ATTR_STD_MOTION_VERTEX_POSITION);

	for(uint j = 0; j < mesh->triangles.size(); j++) {
		Mesh::Triangle t = mesh->triangles[j];
		BoundBox bounds = BoundBox::empty;
		PrimitiveType type = PRIMITIVE_TRIANGLE;

		t.bounds_grow(&mesh->verts[0], bounds);

		/* motion triangles */
		if(attr_mP) {
			size_t mesh_size = mesh->verts.size();
			size_t steps = mesh->motion_steps - 1;
			float3 *vert_steps = attr_mP->data_float3();

			for(size_t i = 0; i < steps; i++)
				t.bounds_grow(vert_steps + i*mesh_size, bounds);

			type = PRIMITIVE_MOTION_TRIANGLE;
		}

		if(bounds.valid()) {
			references.push_back(BVHReference(bounds, j, i, type));
			root.grow(bounds);
			center.grow(bounds.center2());
		}
	}

	Attribute *curve_attr_mP = NULL;

	if(mesh->has_motion_blur())
		curve_attr_mP = mesh->curve_attributes.find(ATTR_STD_MOTION_VERTEX_POSITION);

	for(uint j = 0; j < mesh->curves.size(); j++) {
		Mesh::Curve curve = mesh->curves[j];
		PrimitiveType type = PRIMITIVE_CURVE;

		for(int k = 0; k < curve.num_keys - 1; k++) {
			BoundBox bounds = BoundBox::empty;
			curve.bounds_grow(k, &mesh->curve_keys[0], bounds);

			/* motion curve */
			if(curve_attr_mP) {
				size_t mesh_size = mesh->curve_keys.size();
				size_t steps = mesh->motion_steps - 1;
				float4 *key_steps = curve_attr_mP->data_float4();

				for(size_t i = 0; i < steps; i++)
					curve.bounds_grow(k, key_steps + i*mesh_size, bounds);

				type = PRIMITIVE_MOTION_CURVE;
			}

			if(bounds.valid()) {
				int packed_type = PRIMITIVE_PACK_SEGMENT(type, k);
				
				references.push_back(BVHReference(bounds, j, i, packed_type));
				root.grow(bounds);
				center.grow(bounds.center2());
			}
		}
	}
}

void BVHBuild::add_reference_object(BoundBox& root, BoundBox& center, Object *ob, int i)
{
	references.push_back(BVHReference(ob->bounds, -1, i, 0));
	root.grow(ob->bounds);
	center.grow(ob->bounds.center2());
}

static size_t count_curve_segments(Mesh *mesh)
{
	size_t num = 0, num_curves = mesh->curves.size();

	for(size_t i = 0; i < num_curves; i++)
		num += mesh->curves[i].num_keys - 1;
	
	return num;
}

void BVHBuild::add_references(BVHRange& root)
{
	/* reserve space for references */
	size_t num_alloc_references = 0;

	foreach(Object *ob, objects) {
		if(params.top_level) {
			if(!ob->mesh->is_instanced()) {
				num_alloc_references += ob->mesh->triangles.size();
				num_alloc_references += count_curve_segments(ob->mesh);
			}
			else
				num_alloc_references++;
		}
		else {
			num_alloc_references += ob->mesh->triangles.size();
			num_alloc_references += count_curve_segments(ob->mesh);
		}
	}

	references.reserve(num_alloc_references);

	/* add references from objects */
	BoundBox bounds = BoundBox::empty, center = BoundBox::empty;
	int i = 0;

	foreach(Object *ob, objects) {
		if(params.top_level) {
			if(!ob->mesh->is_instanced())
				add_reference_mesh(bounds, center, ob->mesh, i);
			else
				add_reference_object(bounds, center, ob, i);
		}
		else
			add_reference_mesh(bounds, center, ob->mesh, i);

		i++;

		if(progress.get_cancel()) return;
	}

	/* happens mostly on empty meshes */
	if(!bounds.valid())
		bounds.grow(make_float3(0.0f, 0.0f, 0.0f));

	root = BVHRange(bounds, center, 0, references.size());
}

/* Build */

BVHNode* BVHBuild::run()
{
	BVHRange root;

	/* add references */
	add_references(root);

	if(progress.get_cancel())
		return NULL;

	/* init spatial splits */
	if(params.top_level) {
		/* NOTE: Technically it is supported by the builder but it's not really
		 * optimized for speed yet and not really clear yet if it has measurable
		 * improvement on render time. Needs some extra investigation before
		 * enabling spatial split for top level BVH.
		 */
		params.use_spatial_split = false;
	}

	spatial_min_overlap = root.bounds().safe_area() * params.spatial_split_alpha;
	spatial_right_bounds.clear();
	spatial_right_bounds.resize(max(root.size(), (int)BVHParams::NUM_SPATIAL_BINS) - 1);

	/* init progress updates */
	double build_start_time;
	build_start_time = progress_start_time = time_dt();
	progress_count = 0;
	progress_total = references.size();
	progress_original_total = progress_total;

	prim_type.resize(references.size());
	prim_index.resize(references.size());
	prim_object.resize(references.size());

	/* build recursively */
	BVHNode *rootnode;

	if(params.use_spatial_split) {
		/* singlethreaded spatial split build */
		rootnode = build_node(root, 0);
	}
	else {
		/* multithreaded binning build */
		BVHObjectBinning rootbin(root, (references.size())? &references[0]: NULL);
		rootnode = build_node(rootbin, 0);
		task_pool.wait_work();
	}

	/* delete if we canceled */
	if(rootnode) {
		if(progress.get_cancel()) {
			rootnode->deleteSubtree();
			rootnode = NULL;
			VLOG(1) << "BVH build cancelled.";
		}
		else if(!params.use_spatial_split) {
			/*rotate(rootnode, 4, 5);*/
			rootnode->update_visibility();
		}
		if(rootnode != NULL) {
			VLOG(1) << "BVH build statistics:\n"
			        << "  Build time: " << time_dt() - build_start_time << "\n"
			        << "  Total number of nodes: "
			        << rootnode->getSubtreeSize(BVH_STAT_NODE_COUNT) << "\n"
			        << "  Number of inner nodes: "
			        << rootnode->getSubtreeSize(BVH_STAT_INNER_COUNT)  << "\n"
			        << "  Number of leaf nodes: "
			        << rootnode->getSubtreeSize(BVH_STAT_LEAF_COUNT)  << "\n";
		}
	}


	return rootnode;
}

void BVHBuild::progress_update()
{
	if(time_dt() - progress_start_time < 0.25)
		return;
	
	double progress_start = (double)progress_count/(double)progress_total;
	double duplicates = (double)(progress_total - progress_original_total)/(double)progress_total;

	string msg = string_printf("Building BVH %.0f%%, duplicates %.0f%%",
	                           progress_start * 100.0, duplicates * 100.0);

	progress.set_substatus(msg);
	progress_start_time = time_dt(); 
}

void BVHBuild::thread_build_node(InnerNode *inner, int child, BVHObjectBinning *range, int level)
{
	if(progress.get_cancel())
		return;

	/* build nodes */
	BVHNode *node = build_node(*range, level);

	/* set child in inner node */
	inner->children[child] = node;

	/* update progress */
	if(range->size() < THREAD_TASK_SIZE) {
		/*rotate(node, INT_MAX, 5);*/

		thread_scoped_lock lock(build_mutex);

		progress_count += range->size();
		progress_update();
	}
}

bool BVHBuild::range_within_max_leaf_size(const BVHRange& range)
{
	size_t size = range.size();
	size_t max_leaf_size = max(params.max_triangle_leaf_size, params.max_curve_leaf_size);

	if(size > max_leaf_size)
		return false;
	
	size_t num_triangles = 0;
	size_t num_curves = 0;
	size_t num_motion_curves = 0;

	for(int i = 0; i < size; i++) {
		BVHReference& ref = references[range.start() + i];

		if(ref.prim_type() & PRIMITIVE_CURVE)
			num_curves++;
		if(ref.prim_type() & PRIMITIVE_MOTION_CURVE)
			num_motion_curves++;
		else if(ref.prim_type() & PRIMITIVE_ALL_TRIANGLE)
			num_triangles++;
	}

	return (num_triangles < params.max_triangle_leaf_size) &&
	       (num_curves < params.max_curve_leaf_size) &&
	       (num_motion_curves < params.max_curve_leaf_size);
}

/* multithreaded binning builder */
BVHNode* BVHBuild::build_node(const BVHObjectBinning& range, int level)
{
	size_t size = range.size();
	float leafSAH = params.sah_primitive_cost * range.leafSAH;
	float splitSAH = params.sah_node_cost * range.bounds().half_area() + params.sah_primitive_cost * range.splitSAH;

	/* have at least one inner node on top level, for performance and correct
	 * visibility tests, since object instances do not check visibility flag */
	if(!(range.size() > 0 && params.top_level && level == 0)) {
		/* make leaf node when threshold reached or SAH tells us */
		if(params.small_enough_for_leaf(size, level) || (range_within_max_leaf_size(range) && leafSAH < splitSAH))
			return create_leaf_node(range);
	}

	/* perform split */
	BVHObjectBinning left, right;
	range.split(&references[0], left, right);

	/* create inner node. */
	InnerNode *inner;

	if(range.size() < THREAD_TASK_SIZE) {
		/* local build */
		BVHNode *leftnode = build_node(left, level + 1);
		BVHNode *rightnode = build_node(right, level + 1);

		inner = new InnerNode(range.bounds(), leftnode, rightnode);
	}
	else {
		/* threaded build */
		inner = new InnerNode(range.bounds());

		task_pool.push(new BVHBuildTask(this, inner, 0, left, level + 1), true);
		task_pool.push(new BVHBuildTask(this, inner, 1, right, level + 1), true);
	}

	return inner;
}

/* single threaded spatial split builder */
BVHNode* BVHBuild::build_node(const BVHRange& range, int level)
{
	/* progress update */
	progress_update();
	if(progress.get_cancel())
		return NULL;

	/* small enough or too deep => create leaf. */
	if(!(range.size() > 0 && params.top_level && level == 0)) {
		if(params.small_enough_for_leaf(range.size(), level)) {
			progress_count += range.size();
			return create_leaf_node(range);
		}
	}

	/* splitting test */
	BVHMixedSplit split(this, range, level);

	if(!(range.size() > 0 && params.top_level && level == 0)) {
		if(split.no_split) {
			progress_count += range.size();
			return create_leaf_node(range);
		}
	}
	
	/* do split */
	BVHRange left, right;
	split.split(this, left, right, range);

	progress_total += left.size() + right.size() - range.size();
	size_t total = progress_total;

	/* left node */
	BVHNode *leftnode = build_node(left, level + 1);

	/* right node (modify start for splits) */
	right.set_start(right.start() + progress_total - total);
	BVHNode *rightnode = build_node(right, level + 1);

	/* inner node */
	return new InnerNode(range.bounds(), leftnode, rightnode);
}

/* Create Nodes */

BVHNode *BVHBuild::create_object_leaf_nodes(const BVHReference *ref, int start, int num)
{
	if(num == 0) {
		BoundBox bounds = BoundBox::empty;
		return new LeafNode(bounds, 0, 0, 0);
	}
	else if(num == 1) {
		assert(start < prim_type.size());
		prim_type[start] = ref->prim_type();
		prim_index[start] = ref->prim_index();
		prim_object[start] = ref->prim_object();

		uint visibility = objects[ref->prim_object()]->visibility;
		return new LeafNode(ref->bounds(), visibility, start, start+1);
	}
	else {
		int mid = num/2;
		BVHNode *leaf0 = create_object_leaf_nodes(ref, start, mid); 
		BVHNode *leaf1 = create_object_leaf_nodes(ref+mid, start+mid, num-mid); 

		BoundBox bounds = BoundBox::empty;
		bounds.grow(leaf0->m_bounds);
		bounds.grow(leaf1->m_bounds);

		return new InnerNode(bounds, leaf0, leaf1);
	}
}

BVHNode *BVHBuild::create_primitive_leaf_node(const int *p_type,
                                              const int *p_index,
                                              const int *p_object,
                                              const BoundBox& bounds,
                                              uint visibility,
                                              int start,
                                              int num)
{
	for(int i = 0; i < num; ++i) {
		prim_type[start + i] = p_type[i];
		prim_index[start + i] = p_index[i];
		prim_object[start + i] = p_object[i];
	}
	return new LeafNode(bounds, visibility, start, start + num);
}

BVHNode* BVHBuild::create_leaf_node(const BVHRange& range)
{
	/* TODO(sergey): Consider writing own allocator which would
	 * not do heap allocation if number of elements is relatively small.
	 */
	vector<int> p_type[PRIMITIVE_NUM_TOTAL];
	vector<int> p_index[PRIMITIVE_NUM_TOTAL];
	vector<int> p_object[PRIMITIVE_NUM_TOTAL];
	uint visibility[PRIMITIVE_NUM_TOTAL] = {0};
	/* NOTE: Keep initializtion in sync with actual number of primitives. */
	BoundBox bounds[PRIMITIVE_NUM_TOTAL] = {BoundBox::empty,
	                                        BoundBox::empty,
	                                        BoundBox::empty,
	                                        BoundBox::empty};
	int ob_num = 0;

	/* Fill in per-type type/index array. */
	for(int i = 0; i < range.size(); i++) {
		BVHReference& ref = references[range.start() + i];
		if(ref.prim_index() != -1) {
			int type_index = bitscan(ref.prim_type() & PRIMITIVE_ALL);
			p_type[type_index].push_back(ref.prim_type());
			p_index[type_index].push_back(ref.prim_index());
			p_object[type_index].push_back(ref.prim_object());

			bounds[type_index].grow(ref.bounds());
			visibility[type_index] |= objects[ref.prim_object()]->visibility;
		}
		else {
			if(ob_num < i) {
				references[range.start() + ob_num] = ref;
			}
			ob_num++;
		}
	}

	/* Extend an array when needed. */
	if(prim_type.size() < range.end()) {
		assert(params.use_spatial_split);
		prim_type.reserve(references.size());
		prim_index.reserve(references.size());
		prim_object.reserve(references.size());
		prim_type.resize(range.end());
		prim_index.resize(range.end());
		prim_object.resize(range.end());
	}

	/* Create leaf nodes for every existing primitive. */
	BVHNode *leaves[PRIMITIVE_NUM_TOTAL + 1] = {NULL};
	int num_leaves = 0;
	int start = range.start();
	for(int i = 0; i < PRIMITIVE_NUM_TOTAL; ++i) {
		int num = (int)p_type[i].size();
		if(num != 0) {
			assert(p_type[i].size() == p_index[i].size());
			assert(p_type[i].size() == p_object[i].size());
			leaves[num_leaves] = create_primitive_leaf_node(&p_type[i][0],
			                                                &p_index[i][0],
			                                                &p_object[i][0],
			                                                bounds[i],
			                                                visibility[i],
			                                                start,
			                                                num);
			++num_leaves;
			start += num;
		}
	}

	/* Create leaf node for object. */
	if(num_leaves == 0 || ob_num) {
		/* Only create object leaf nodes if there are objects or no other
		 * nodes created.
		 */
		const BVHReference *ref = (ob_num)? &references[range.start()]: NULL;
		leaves[num_leaves] = create_object_leaf_nodes(ref, start, ob_num);
		++num_leaves;
	}

	if(num_leaves == 1) {
		/* Simplest case: single leaf, just return it.
		 * In all the rest cases we'll be creating intermediate inner node with
		 * an appropriate bounding box.
		 */
		return leaves[0];
	}
	else if(num_leaves == 2) {
		return new InnerNode(range.bounds(), leaves[0], leaves[1]);
	}
	else if(num_leaves == 3) {
		BoundBox inner_bounds = merge(leaves[1]->m_bounds, leaves[2]->m_bounds);
		BVHNode *inner = new InnerNode(inner_bounds, leaves[1], leaves[2]);
		return new InnerNode(range.bounds(), leaves[0], inner);
	} else {
		/* Shpuld be doing more branches if more primitive types added. */
		assert(num_leaves <= 5);
		BoundBox inner_bounds_a = merge(leaves[0]->m_bounds, leaves[1]->m_bounds);
		BoundBox inner_bounds_b = merge(leaves[2]->m_bounds, leaves[3]->m_bounds);
		BVHNode *inner_a = new InnerNode(inner_bounds_a, leaves[0], leaves[1]);
		BVHNode *inner_b = new InnerNode(inner_bounds_b, leaves[2], leaves[3]);
		BoundBox inner_bounds_c = merge(inner_a->m_bounds, inner_b->m_bounds);
		BVHNode *inner_c = new InnerNode(inner_bounds_c, inner_a, inner_b);
		if(num_leaves == 5) {
			return new InnerNode(range.bounds(), inner_c, leaves[4]);
		}
		return inner_c;
	}
}

/* Tree Rotations */

void BVHBuild::rotate(BVHNode *node, int max_depth, int iterations)
{
	/* in tested scenes, this resulted in slightly slower raytracing, so disabled
	 * it for now. could be implementation bug, or depend on the scene */
	if(node)
		for(int i = 0; i < iterations; i++)
			rotate(node, max_depth);
}

void BVHBuild::rotate(BVHNode *node, int max_depth)
{
	/* nothing to rotate if we reached a leaf node. */
	if(node->is_leaf() || max_depth < 0)
		return;
	
	InnerNode *parent = (InnerNode*)node;

	/* rotate all children first */
	for(size_t c = 0; c < 2; c++)
		rotate(parent->children[c], max_depth-1);

	/* compute current area of all children */
	BoundBox bounds0 = parent->children[0]->m_bounds;
	BoundBox bounds1 = parent->children[1]->m_bounds;

	float area0 = bounds0.half_area();
	float area1 = bounds1.half_area();
	float4 child_area = make_float4(area0, area1, 0.0f, 0.0f);

	/* find best rotation. we pick a target child of a first child, and swap
	 * this with an other child. we perform the best such swap. */
	float best_cost = FLT_MAX;
	int best_child = -1, best_target = -1, best_other = -1;

	for(size_t c = 0; c < 2; c++) {
		/* ignore leaf nodes as we cannot descent into */
		if(parent->children[c]->is_leaf())
			continue;

		InnerNode *child = (InnerNode*)parent->children[c];
		BoundBox& other = (c == 0)? bounds1: bounds0;

		/* transpose child bounds */
		BoundBox target0 = child->children[0]->m_bounds;
		BoundBox target1 = child->children[1]->m_bounds;

		/* compute cost for both possible swaps */
		float cost0 = merge(other, target1).half_area() - child_area[c];
		float cost1 = merge(target0, other).half_area() - child_area[c];

		if(min(cost0,cost1) < best_cost) {
			best_child = (int)c;
			best_other = (int)(1-c);

			if(cost0 < cost1) {
				best_cost = cost0;
				best_target = 0;
			}
			else {
				best_cost = cost0;
				best_target = 1;
			}
		}
	}

	/* if we did not find a swap that improves the SAH then do nothing */
	if(best_cost >= 0)
		return;

	assert(best_child == 0 || best_child == 1);
	assert(best_target != -1);

	/* perform the best found tree rotation */
	InnerNode *child = (InnerNode*)parent->children[best_child];

	swap(parent->children[best_other], child->children[best_target]);
	child->m_bounds = merge(child->children[0]->m_bounds, child->children[1]->m_bounds);
}

CCL_NAMESPACE_END
