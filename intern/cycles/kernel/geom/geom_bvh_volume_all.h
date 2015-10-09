/*
 * Adapted from code Copyright 2009-2010 NVIDIA Corporation,
 * and code copyright 2009-2012 Intel Corporation
 *
 * Modifications Copyright 2011-2014, Blender Foundation.
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

#ifdef __QBVH__
#include "geom_qbvh_volume_all.h"
#endif

/* This is a template BVH traversal function for volumes, where
 * various features can be enabled/disabled. This way we can compile optimized
 * versions for each case without new features slowing things down.
 *
 * BVH_INSTANCING: object instancing
 * BVH_HAIR: hair curve rendering
 * BVH_MOTION: motion blur rendering
 *
 */

ccl_device uint BVH_FUNCTION_FULL_NAME(BVH)(KernelGlobals *kg,
                                            const Ray *ray,
                                            Intersection *isect_array,
                                            const uint max_hits)
{
	/* todo:
	 * - test if pushing distance on the stack helps (for non shadow rays)
	 * - separate version for shadow rays
	 * - likely and unlikely for if() statements
	 * - test restrict attribute for pointers
	 */

	/* traversal stack in CUDA thread-local memory */
	int traversalStack[BVH_STACK_SIZE];
	traversalStack[0] = ENTRYPOINT_SENTINEL;

	/* traversal variables in registers */
	int stackPtr = 0;
	int nodeAddr = kernel_data.bvh.root;

	/* ray parameters in registers */
	const float tmax = ray->t;
	float3 P = ray->P;
	float3 dir = bvh_clamp_direction(ray->D);
	float3 idir = bvh_inverse_direction(dir);
	int object = OBJECT_NONE;
	float isect_t = tmax;

	const uint visibility = PATH_RAY_ALL_VISIBILITY;

#if BVH_FEATURE(BVH_MOTION)
	Transform ob_itfm;
#endif

#if BVH_FEATURE(BVH_INSTANCING)
	int num_hits_in_instance = 0;
#endif

	uint num_hits = 0;
	isect_array->t = tmax;

#if defined(__KERNEL_SSE2__)
	const shuffle_swap_t shuf_identity = shuffle_swap_identity();
	const shuffle_swap_t shuf_swap = shuffle_swap_swap();
	
	const ssef pn = cast(ssei(0, 0, 0x80000000, 0x80000000));
	ssef Psplat[3], idirsplat[3];
	shuffle_swap_t shufflexyz[3];

	Psplat[0] = ssef(P.x);
	Psplat[1] = ssef(P.y);
	Psplat[2] = ssef(P.z);

	ssef tsplat(0.0f, 0.0f, -isect_t, -isect_t);

	gen_idirsplat_swap(pn, shuf_identity, shuf_swap, idir, idirsplat, shufflexyz);
#endif

	IsectPrecalc isect_precalc;
	triangle_intersect_precalc(dir, &isect_precalc);

	/* traversal loop */
	do {
		do {
			/* traverse internal nodes */
			while(nodeAddr >= 0 && nodeAddr != ENTRYPOINT_SENTINEL) {
				bool traverseChild0, traverseChild1;
				int nodeAddrChild1;

#if !defined(__KERNEL_SSE2__)
				/* Intersect two child bounding boxes, non-SSE version */
				float t = isect_array->t;

				/* fetch node data */
				float4 node0 = kernel_tex_fetch(__bvh_nodes, nodeAddr*BVH_NODE_SIZE+0);
				float4 node1 = kernel_tex_fetch(__bvh_nodes, nodeAddr*BVH_NODE_SIZE+1);
				float4 node2 = kernel_tex_fetch(__bvh_nodes, nodeAddr*BVH_NODE_SIZE+2);
				float4 cnodes = kernel_tex_fetch(__bvh_nodes, nodeAddr*BVH_NODE_SIZE+3);

				/* intersect ray against child nodes */
				NO_EXTENDED_PRECISION float c0lox = (node0.x - P.x) * idir.x;
				NO_EXTENDED_PRECISION float c0hix = (node0.z - P.x) * idir.x;
				NO_EXTENDED_PRECISION float c0loy = (node1.x - P.y) * idir.y;
				NO_EXTENDED_PRECISION float c0hiy = (node1.z - P.y) * idir.y;
				NO_EXTENDED_PRECISION float c0loz = (node2.x - P.z) * idir.z;
				NO_EXTENDED_PRECISION float c0hiz = (node2.z - P.z) * idir.z;
				NO_EXTENDED_PRECISION float c0min = max4(min(c0lox, c0hix), min(c0loy, c0hiy), min(c0loz, c0hiz), 0.0f);
				NO_EXTENDED_PRECISION float c0max = min4(max(c0lox, c0hix), max(c0loy, c0hiy), max(c0loz, c0hiz), t);

				NO_EXTENDED_PRECISION float c1lox = (node0.y - P.x) * idir.x;
				NO_EXTENDED_PRECISION float c1hix = (node0.w - P.x) * idir.x;
				NO_EXTENDED_PRECISION float c1loy = (node1.y - P.y) * idir.y;
				NO_EXTENDED_PRECISION float c1hiy = (node1.w - P.y) * idir.y;
				NO_EXTENDED_PRECISION float c1loz = (node2.y - P.z) * idir.z;
				NO_EXTENDED_PRECISION float c1hiz = (node2.w - P.z) * idir.z;
				NO_EXTENDED_PRECISION float c1min = max4(min(c1lox, c1hix), min(c1loy, c1hiy), min(c1loz, c1hiz), 0.0f);
				NO_EXTENDED_PRECISION float c1max = min4(max(c1lox, c1hix), max(c1loy, c1hiy), max(c1loz, c1hiz), t);

				/* decide which nodes to traverse next */
				traverseChild0 = (c0max >= c0min);
				traverseChild1 = (c1max >= c1min);

#else // __KERNEL_SSE2__
				/* Intersect two child bounding boxes, SSE3 version adapted from Embree */

				/* fetch node data */
				const ssef *bvh_nodes = (ssef*)kg->__bvh_nodes.data + nodeAddr*BVH_NODE_SIZE;
				const float4 cnodes = ((float4*)bvh_nodes)[3];

				/* intersect ray against child nodes */
				const ssef tminmaxx = (shuffle_swap(bvh_nodes[0], shufflexyz[0]) - Psplat[0]) * idirsplat[0];
				const ssef tminmaxy = (shuffle_swap(bvh_nodes[1], shufflexyz[1]) - Psplat[1]) * idirsplat[1];
				const ssef tminmaxz = (shuffle_swap(bvh_nodes[2], shufflexyz[2]) - Psplat[2]) * idirsplat[2];

				/* calculate { c0min, c1min, -c0max, -c1max} */
				ssef minmax = max(max(tminmaxx, tminmaxy), max(tminmaxz, tsplat));
				const ssef tminmax = minmax ^ pn;

				const sseb lrhit = tminmax <= shuffle<2, 3, 0, 1>(tminmax);

				/* decide which nodes to traverse next */
				traverseChild0 = (movemask(lrhit) & 1);
				traverseChild1 = (movemask(lrhit) & 2);
#endif // __KERNEL_SSE2__

				nodeAddr = __float_as_int(cnodes.x);
				nodeAddrChild1 = __float_as_int(cnodes.y);

				if(traverseChild0 && traverseChild1) {
					/* both children were intersected, push the farther one */
#if !defined(__KERNEL_SSE2__)
					bool closestChild1 = (c1min < c0min);
#else
					bool closestChild1 = tminmax[1] < tminmax[0];
#endif

					if(closestChild1) {
						int tmp = nodeAddr;
						nodeAddr = nodeAddrChild1;
						nodeAddrChild1 = tmp;
					}

					++stackPtr;
					kernel_assert(stackPtr < BVH_STACK_SIZE);
					traversalStack[stackPtr] = nodeAddrChild1;
				}
				else {
					/* one child was intersected */
					if(traverseChild1) {
						nodeAddr = nodeAddrChild1;
					}
					else if(!traverseChild0) {
						/* neither child was intersected */
						nodeAddr = traversalStack[stackPtr];
						--stackPtr;
					}
				}
			}

			/* if node is leaf, fetch triangle list */
			if(nodeAddr < 0) {
				float4 leaf = kernel_tex_fetch(__bvh_leaf_nodes, (-nodeAddr-1)*BVH_NODE_LEAF_SIZE);
				int primAddr = __float_as_int(leaf.x);

#if BVH_FEATURE(BVH_INSTANCING)
				if(primAddr >= 0) {
#endif
					const int primAddr2 = __float_as_int(leaf.y);
					const uint type = __float_as_int(leaf.w);
					bool hit;

					/* pop */
					nodeAddr = traversalStack[stackPtr];
					--stackPtr;

					/* primitive intersection */
					switch(type & PRIMITIVE_ALL) {
						case PRIMITIVE_TRIANGLE: {
							/* intersect ray against primitive */
							for(; primAddr < primAddr2; primAddr++) {
								kernel_assert(kernel_tex_fetch(__prim_type, primAddr) == type);
								/* only primitives from volume object */
								uint tri_object = (object == OBJECT_NONE)? kernel_tex_fetch(__prim_object, primAddr): object;
								int object_flag = kernel_tex_fetch(__object_flag, tri_object);
								if((object_flag & SD_OBJECT_HAS_VOLUME) == 0) {
									continue;
								}
								hit = triangle_intersect(kg, &isect_precalc, isect_array, P, visibility, object, primAddr);
								if(hit) {
									/* Move on to next entry in intersections array. */
									isect_array++;
									num_hits++;
#if BVH_FEATURE(BVH_INSTANCING)
									num_hits_in_instance++;
#endif
									isect_array->t = isect_t;
									if(num_hits == max_hits) {
#if BVH_FEATURE(BVH_INSTANCING)
#if BVH_FEATURE(BVH_MOTION)
										float t_fac = 1.0f / len(transform_direction(&ob_itfm, dir));
#else
										Transform itfm = object_fetch_transform(kg, object, OBJECT_INVERSE_TRANSFORM);
										float t_fac = 1.0f / len(transform_direction(&itfm, dir));
#endif
										for(int i = 0; i < num_hits_in_instance; i++) {
											(isect_array-i-1)->t *= t_fac;
										}
#endif  /* BVH_FEATURE(BVH_INSTANCING) */
										return num_hits;
									}
								}
							}
							break;
						}
#if BVH_FEATURE(BVH_MOTION)
						case PRIMITIVE_MOTION_TRIANGLE: {
							/* intersect ray against primitive */
							for(; primAddr < primAddr2; primAddr++) {
								kernel_assert(kernel_tex_fetch(__prim_type, primAddr) == type);
								/* only primitives from volume object */
								uint tri_object = (object == OBJECT_NONE)? kernel_tex_fetch(__prim_object, primAddr): object;
								int object_flag = kernel_tex_fetch(__object_flag, tri_object);
								if((object_flag & SD_OBJECT_HAS_VOLUME) == 0) {
									continue;
								}
								hit = motion_triangle_intersect(kg, isect_array, P, dir, ray->time, visibility, object, primAddr);
								if(hit) {
									/* Move on to next entry in intersections array. */
									isect_array++;
									num_hits++;
#if BVH_FEATURE(BVH_INSTANCING)
									num_hits_in_instance++;
#endif
									isect_array->t = isect_t;
									if(num_hits == max_hits) {
#if BVH_FEATURE(BVH_INSTANCING)
#  if BVH_FEATURE(BVH_MOTION)
										float t_fac = 1.0f / len(transform_direction(&ob_itfm, dir));
#  else
										Transform itfm = object_fetch_transform(kg, object, OBJECT_INVERSE_TRANSFORM);
										float t_fac = 1.0f / len(transform_direction(&itfm, dir));
#endif
										for(int i = 0; i < num_hits_in_instance; i++) {
											(isect_array-i-1)->t *= t_fac;
										}
#endif  /* BVH_FEATURE(BVH_INSTANCING) */
										return num_hits;
									}
								}
							}
							break;
						}
#endif
#if BVH_FEATURE(BVH_HAIR)
						case PRIMITIVE_CURVE:
						case PRIMITIVE_MOTION_CURVE: {
							/* intersect ray against primitive */
							for(; primAddr < primAddr2; primAddr++) {
								kernel_assert(kernel_tex_fetch(__prim_type, primAddr) == type);
								/* only primitives from volume object */
								uint tri_object = (object == OBJECT_NONE)? kernel_tex_fetch(__prim_object, primAddr): object;
								int object_flag = kernel_tex_fetch(__object_flag, tri_object);
								if((object_flag & SD_OBJECT_HAS_VOLUME) == 0) {
									continue;
								}
								if(kernel_data.curve.curveflags & CURVE_KN_INTERPOLATE)
									hit = bvh_cardinal_curve_intersect(kg, isect_array, P, dir, visibility, object, primAddr, ray->time, type, NULL, 0, 0);
								else
									hit = bvh_curve_intersect(kg, isect_array, P, dir, visibility, object, primAddr, ray->time, type, NULL, 0, 0);
								if(hit) {
									/* Move on to next entry in intersections array. */
									isect_array++;
									num_hits++;
#if BVH_FEATURE(BVH_INSTANCING)
									num_hits_in_instance++;
#endif
									isect_array->t = isect_t;
									if(num_hits == max_hits) {
#if BVH_FEATURE(BVH_INSTANCING)
#  if BVH_FEATURE(BVH_MOTION)
										float t_fac = 1.0f / len(transform_direction(&ob_itfm, dir));
#  else
										Transform itfm = object_fetch_transform(kg, object, OBJECT_INVERSE_TRANSFORM);
										float t_fac = 1.0f / len(transform_direction(&itfm, dir));
#endif
										for(int i = 0; i < num_hits_in_instance; i++) {
											(isect_array-i-1)->t *= t_fac;
										}
#endif  /* BVH_FEATURE(BVH_INSTANCING) */
										return num_hits;
									}
								}
							}
							break;
						}
#endif
						default: {
							break;
						}
					}
				}
#if BVH_FEATURE(BVH_INSTANCING)
				else {
					/* instance push */
					object = kernel_tex_fetch(__prim_object, -primAddr-1);
					int object_flag = kernel_tex_fetch(__object_flag, object);

					if(object_flag & SD_OBJECT_HAS_VOLUME) {

#if BVH_FEATURE(BVH_MOTION)
						bvh_instance_motion_push(kg, object, ray, &P, &dir, &idir, &isect_t, &ob_itfm);
#else
						bvh_instance_push(kg, object, ray, &P, &dir, &idir, &isect_t);
#endif

						triangle_intersect_precalc(dir, &isect_precalc);
						num_hits_in_instance = 0;
						isect_array->t = isect_t;

#if defined(__KERNEL_SSE2__)
						Psplat[0] = ssef(P.x);
						Psplat[1] = ssef(P.y);
						Psplat[2] = ssef(P.z);

						tsplat = ssef(0.0f, 0.0f, -isect_t, -isect_t);

						gen_idirsplat_swap(pn, shuf_identity, shuf_swap, idir, idirsplat, shufflexyz);
#endif

						++stackPtr;
						kernel_assert(stackPtr < BVH_STACK_SIZE);
						traversalStack[stackPtr] = ENTRYPOINT_SENTINEL;

						nodeAddr = kernel_tex_fetch(__object_node, object);
					}
					else {
						/* pop */
						object = OBJECT_NONE;
						nodeAddr = traversalStack[stackPtr];
						--stackPtr;
					}
				}
			}
#endif  /* FEATURE(BVH_INSTANCING) */
		} while(nodeAddr != ENTRYPOINT_SENTINEL);

#if BVH_FEATURE(BVH_INSTANCING)
		if(stackPtr >= 0) {
			kernel_assert(object != OBJECT_NONE);

			if(num_hits_in_instance) {
				float t_fac;
#if BVH_FEATURE(BVH_MOTION)
				bvh_instance_motion_pop_factor(kg, object, ray, &P, &dir, &idir, &t_fac, &ob_itfm);
#else
				bvh_instance_pop_factor(kg, object, ray, &P, &dir, &idir, &t_fac);
#endif
				triangle_intersect_precalc(dir, &isect_precalc);
				/* Scale isect->t to adjust for instancing. */
				for(int i = 0; i < num_hits_in_instance; i++) {
					(isect_array-i-1)->t *= t_fac;
				}
			}
			else {
				float ignore_t = FLT_MAX;
#if BVH_FEATURE(BVH_MOTION)
				bvh_instance_motion_pop(kg, object, ray, &P, &dir, &idir, &ignore_t, &ob_itfm);
#else
				bvh_instance_pop(kg, object, ray, &P, &dir, &idir, &ignore_t);
#endif
				triangle_intersect_precalc(dir, &isect_precalc);
			}

			isect_t = tmax;
			isect_array->t = isect_t;

#if defined(__KERNEL_SSE2__)
			Psplat[0] = ssef(P.x);
			Psplat[1] = ssef(P.y);
			Psplat[2] = ssef(P.z);

			tsplat = ssef(0.0f, 0.0f, -isect_t, -isect_t);

			gen_idirsplat_swap(pn, shuf_identity, shuf_swap, idir, idirsplat, shufflexyz);
#endif

			object = OBJECT_NONE;
			nodeAddr = traversalStack[stackPtr];
			--stackPtr;
		}
#endif  /* FEATURE(BVH_MOTION) */
	} while(nodeAddr != ENTRYPOINT_SENTINEL);

	return num_hits;
}

ccl_device_inline uint BVH_FUNCTION_NAME(KernelGlobals *kg,
                                         const Ray *ray,
                                         Intersection *isect_array,
                                         const uint max_hits)
{
#ifdef __QBVH__
	if(kernel_data.bvh.use_qbvh) {
		return BVH_FUNCTION_FULL_NAME(QBVH)(kg,
		                                    ray,
		                                    isect_array,
		                                    max_hits);
	}
	else
#endif
	{
		kernel_assert(kernel_data.bvh.use_qbvh == false);
		return BVH_FUNCTION_FULL_NAME(BVH)(kg,
		                                   ray,
		                                   isect_array,
		                                   max_hits);
	}
}

#undef BVH_FUNCTION_NAME
#undef BVH_FUNCTION_FEATURES
