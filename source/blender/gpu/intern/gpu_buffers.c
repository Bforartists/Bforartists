/*
 * $Id$
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Brecht Van Lommel.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/gpu/intern/gpu_buffers.c
 *  \ingroup gpu
 */


#include <limits.h>
#include <stddef.h>
#include <string.h>

#include "GL/glew.h"

#include "MEM_guardedalloc.h"

#include "BLI_math.h"
#include "BLI_utildefines.h"
#include "BLI_ghash.h"
#include "BLI_threads.h"

#include "DNA_meshdata_types.h"

#include "BKE_DerivedMesh.h"

#include "DNA_userdef_types.h"

#include "GPU_buffers.h"

typedef enum {
	GPU_BUFFER_VERTEX_STATE = 1,
	GPU_BUFFER_NORMAL_STATE = 2,
	GPU_BUFFER_TEXCOORD_STATE = 4,
	GPU_BUFFER_COLOR_STATE = 8,
	GPU_BUFFER_ELEMENT_STATE = 16,
} GPUBufferState;

#define MAX_GPU_ATTRIB_DATA 32

/* material number is an 16-bit short and the range of short is from -16383 to 16383 (assume material number is non-negative) */
#define MAX_MATERIALS 16384

/* -1 - undefined, 0 - vertex arrays, 1 - VBOs */
static int useVBOs = -1;
static GPUBufferState GLStates = 0;
static GPUAttrib attribData[MAX_GPU_ATTRIB_DATA] = { { -1, 0, 0 } };

/* stores recently-deleted buffers so that new buffers won't have to
   be recreated as often

   only one instance of this pool is created, stored in
   gpu_buffer_pool

   note that the number of buffers in the pool is usually limited to
   MAX_FREE_GPU_BUFFERS, but this limit may be exceeded temporarily
   when a GPUBuffer is released outside the main thread; due to OpenGL
   restrictions it cannot be immediately released
 */
typedef struct GPUBufferPool {
	/* number of allocated buffers stored */
	int totbuf;
	/* actual allocated length of the array */
	int maxsize;
	GPUBuffer **buffers;
} GPUBufferPool;
#define MAX_FREE_GPU_BUFFERS 8

/* create a new GPUBufferPool */
static GPUBufferPool *gpu_buffer_pool_new(void)
{
	GPUBufferPool *pool;

	/* enable VBOs if supported */
	if(useVBOs == -1)
		useVBOs = (GLEW_ARB_vertex_buffer_object ? 1 : 0);

	pool = MEM_callocN(sizeof(GPUBufferPool), "GPUBuffer");

	pool->maxsize = MAX_FREE_GPU_BUFFERS;
	pool->buffers = MEM_callocN(sizeof(GPUBuffer*)*pool->maxsize,
				    "GPUBuffer.buffers");

	return pool;
}

/* remove a GPUBuffer from the pool (does not free the GPUBuffer) */
static void gpu_buffer_pool_remove_index(GPUBufferPool *pool, int index)
{
	int i;

	if(!pool || index < 0 || index >= pool->totbuf)
		return;

	/* shift entries down, overwriting the buffer at `index' */
	for(i = index; i < pool->totbuf - 1; i++)
		pool->buffers[i] = pool->buffers[i+1];

	/* clear the last entry */
	if(pool->totbuf > 0)
		pool->buffers[pool->totbuf - 1] = NULL;

	pool->totbuf--;
}

/* delete the last entry in the pool */
static void gpu_buffer_pool_delete_last(GPUBufferPool *pool)
{
	GPUBuffer *last;

	if(pool->totbuf <= 0)
		return;

	/* get the last entry */
	if(!(last = pool->buffers[pool->totbuf - 1]))
		return;

	/* delete the buffer's data */
	if(useVBOs)
		glDeleteBuffersARB(1, &last->id);
	else
		MEM_freeN(last->pointer);

	/* delete the buffer and remove from pool */
	MEM_freeN(last);
	pool->totbuf--;
	pool->buffers[pool->totbuf] = NULL;
}

/* free a GPUBufferPool; also frees the data in the pool's
   GPUBuffers */
static void gpu_buffer_pool_free(GPUBufferPool *pool)
{
	if(!pool)
		return;
	
	while(pool->totbuf)
		gpu_buffer_pool_delete_last(pool);

	MEM_freeN(pool->buffers);
	MEM_freeN(pool);
}

static GPUBufferPool *gpu_buffer_pool = NULL;
static GPUBufferPool *gpu_get_global_buffer_pool(void)
{
	/* initialize the pool */
	if(!gpu_buffer_pool)
		gpu_buffer_pool = gpu_buffer_pool_new();

	return gpu_buffer_pool;
}

void GPU_global_buffer_pool_free(void)
{
	gpu_buffer_pool_free(gpu_buffer_pool);
	gpu_buffer_pool = NULL;
}

/* get a GPUBuffer of at least `size' bytes; uses one from the buffer
   pool if possible, otherwise creates a new one */
GPUBuffer *GPU_buffer_alloc(int size)
{
	GPUBufferPool *pool;
	GPUBuffer *buf;
	int i, bufsize, bestfit = -1;

	pool = gpu_get_global_buffer_pool();

	/* not sure if this buffer pool code has been profiled much,
	   seems to me that the graphics driver and system memory
	   management might do this stuff anyway. --nicholas
	*/

	/* check the global buffer pool for a recently-deleted buffer
	   that is at least as big as the request, but not more than
	   twice as big */
	for(i = 0; i < pool->totbuf; i++) {
		bufsize = pool->buffers[i]->size;

		/* check for an exact size match */
		if(bufsize == size) {
			bestfit = i;
			break;
		}
		/* smaller buffers won't fit data and buffers at least
		   twice as big are a waste of memory */
		else if(bufsize > size && size > (bufsize / 2)) {
			/* is it closer to the required size than the
			   last appropriate buffer found. try to save
			   memory */
			if(bestfit == -1 || pool->buffers[bestfit]->size > bufsize) {
				bestfit = i;
			}
		}
	}

	/* if an acceptable buffer was found in the pool, remove it
	   from the pool and return it */
	if(bestfit != -1) {
		buf = pool->buffers[bestfit];
		gpu_buffer_pool_remove_index(pool, bestfit);
		return buf;
	}

	/* no acceptable buffer found in the pool, create a new one */
	buf = MEM_callocN(sizeof(GPUBuffer), "GPUBuffer");
	buf->size = size;

	if(useVBOs == 1) {
		/* create a new VBO and initialize it to the requested
		   size */
		glGenBuffersARB(1, &buf->id);
		glBindBufferARB(GL_ARRAY_BUFFER_ARB, buf->id);
		glBufferDataARB(GL_ARRAY_BUFFER_ARB, size, NULL, GL_STATIC_DRAW_ARB);
		glBindBufferARB(GL_ARRAY_BUFFER_ARB, 0);
	}
	else {
		buf->pointer = MEM_mallocN(size, "GPUBuffer.pointer");
		
		/* purpose of this seems to be dealing with
		   out-of-memory errors? looks a bit iffy to me
		   though, at least on Linux I expect malloc() would
		   just overcommit. --nicholas */
		while(!buf->pointer && pool->totbuf > 0) {
			gpu_buffer_pool_delete_last(pool);
			buf->pointer = MEM_mallocN(size, "GPUBuffer.pointer");
		}
		if(!buf->pointer)
			return NULL;
	}

	return buf;
}

/* release a GPUBuffer; does not free the actual buffer or its data,
   but rather moves it to the pool of recently-free'd buffers for
   possible re-use*/
void GPU_buffer_free(GPUBuffer *buffer)
{
	GPUBufferPool *pool;
	int i;

	if(!buffer)
		return;

	pool = gpu_get_global_buffer_pool();

	/* free the last used buffer in the queue if no more space, but only
	   if we are in the main thread. for e.g. rendering or baking it can
	   happen that we are in other thread and can't call OpenGL, in that
	   case cleanup will be done GPU_buffer_pool_free_unused */
	if(BLI_thread_is_main()) {
		/* in main thread, safe to decrease size of pool back
		   down to MAX_FREE_GPU_BUFFERS */
		while(pool->totbuf >= MAX_FREE_GPU_BUFFERS)
			gpu_buffer_pool_delete_last(pool);
	}
	else {
		/* outside of main thread, can't safely delete the
		   buffer, so increase pool size */
		if(pool->maxsize == pool->totbuf) {
			pool->maxsize += MAX_FREE_GPU_BUFFERS;
			pool->buffers = MEM_reallocN(pool->buffers,
						     sizeof(GPUBuffer*) * pool->maxsize);
		}
	}

	/* shift pool entries up by one */
	for(i = pool->totbuf; i > 0; i--)
		pool->buffers[i] = pool->buffers[i-1];

	/* insert the buffer into the beginning of the pool */
	pool->buffers[0] = buffer;
	pool->totbuf++;
}

typedef struct GPUVertPointLink {
	struct GPUVertPointLink *next;
	/* -1 means uninitialized */
	int point_index;
} GPUVertPointLink;

/* add a new point to the list of points related to a particular
   vertex */
static void gpu_drawobject_add_vert_point(GPUDrawObject *gdo, int vert_index, int point_index)
{
	GPUVertPointLink *lnk;

	lnk = &gdo->vert_points[vert_index];

	/* if first link is in use, add a new link at the end */
	if(lnk->point_index != -1) {
		/* get last link */
		for(; lnk->next; lnk = lnk->next);

		/* add a new link from the pool */
		lnk = lnk->next = &gdo->vert_points_mem[gdo->vert_points_usage];
		gdo->vert_points_usage++;
	}

	lnk->point_index = point_index;
}

/* update the vert_points and triangle_to_mface fields with a new
   triangle */
static void gpu_drawobject_add_triangle(GPUDrawObject *gdo,
					int base_point_index,
					int face_index,
					int v1, int v2, int v3)
{
	int i, v[3] = {v1, v2, v3};
	for(i = 0; i < 3; i++)
		gpu_drawobject_add_vert_point(gdo, v[i], base_point_index + i);
	gdo->triangle_to_mface[base_point_index / 3] = face_index;
}

/* for each vertex, build a list of points related to it; these lists
   are stored in an array sized to the number of vertices */
static void gpu_drawobject_init_vert_points(GPUDrawObject *gdo, MFace *f, int totface)
{
	GPUBufferMaterial *mat;
	int i, mat_orig_to_new[MAX_MATERIALS];

	/* allocate the array and space for links */
	gdo->vert_points = MEM_callocN(sizeof(GPUVertPointLink) * gdo->totvert,
				       "GPUDrawObject.vert_points");
	gdo->vert_points_mem = MEM_callocN(sizeof(GPUVertPointLink) * gdo->tot_triangle_point,
					      "GPUDrawObject.vert_points_mem");
	gdo->vert_points_usage = 0;

	/* build a map from the original material indices to the new
	   GPUBufferMaterial indices */
	for(i = 0; i < gdo->totmaterial; i++)
		mat_orig_to_new[gdo->materials[i].mat_nr] = i;

	/* -1 indicates the link is not yet used */
	for(i = 0; i < gdo->totvert; i++)
		gdo->vert_points[i].point_index = -1;

	for(i = 0; i < totface; i++, f++) {
		mat = &gdo->materials[mat_orig_to_new[f->mat_nr]];

		/* add triangle */
		gpu_drawobject_add_triangle(gdo, mat->start + mat->totpoint,
					    i, f->v1, f->v2, f->v3);
		mat->totpoint += 3;

		/* add second triangle for quads */
		if(f->v4) {
			gpu_drawobject_add_triangle(gdo, mat->start + mat->totpoint,
						    i, f->v3, f->v4, f->v1);
			mat->totpoint += 3;
		}
	}

	/* map any unused vertices to loose points */
	for(i = 0; i < gdo->totvert; i++) {
		if(gdo->vert_points[i].point_index == -1) {
			gdo->vert_points[i].point_index = gdo->tot_triangle_point + gdo->tot_loose_point;
			gdo->tot_loose_point++;
		}
	}
}

/* see GPUDrawObject's structure definition for a description of the
   data being initialized here */
GPUDrawObject *GPU_drawobject_new( DerivedMesh *dm )
{
	GPUDrawObject *gdo;
	MFace *mface;
	int points_per_mat[MAX_MATERIALS];
	int i, curmat, curpoint, totface;

	mface = dm->getFaceArray(dm);
	totface= dm->getNumFaces(dm);

	/* get the number of points used by each material, treating
	   each quad as two triangles */
	memset(points_per_mat, 0, sizeof(int)*MAX_MATERIALS);
	for(i = 0; i < totface; i++)
		points_per_mat[mface[i].mat_nr] += mface[i].v4 ? 6 : 3;

	/* create the GPUDrawObject */
	gdo = MEM_callocN(sizeof(GPUDrawObject),"GPUDrawObject");
	gdo->totvert = dm->getNumVerts(dm);
	gdo->totedge = dm->getNumEdges(dm);

	/* count the number of materials used by this DerivedMesh */
	for(i = 0; i < MAX_MATERIALS; i++) {
		if(points_per_mat[i] > 0)
			gdo->totmaterial++;
	}

	/* allocate an array of materials used by this DerivedMesh */
	gdo->materials = MEM_mallocN(sizeof(GPUBufferMaterial) * gdo->totmaterial,
				     "GPUDrawObject.materials");

	/* initialize the materials array */
	for(i = 0, curmat = 0, curpoint = 0; i < MAX_MATERIALS; i++) {
		if(points_per_mat[i] > 0) {
			gdo->materials[curmat].start = curpoint;
			gdo->materials[curmat].totpoint = 0;
			gdo->materials[curmat].mat_nr = i;

			curpoint += points_per_mat[i];
			curmat++;
		}
	}

	/* store total number of points used for triangles */
	gdo->tot_triangle_point = curpoint;

	gdo->triangle_to_mface = MEM_mallocN(sizeof(int) * (gdo->tot_triangle_point / 3),
				     "GPUDrawObject.triangle_to_mface");

	gpu_drawobject_init_vert_points(gdo, mface, totface);

	return gdo;
}

void GPU_drawobject_free(DerivedMesh *dm)
{
	GPUDrawObject *gdo;

	if(!dm || !(gdo = dm->drawObject))
		return;

	MEM_freeN(gdo->materials);
	MEM_freeN(gdo->triangle_to_mface);
	MEM_freeN(gdo->vert_points);
	MEM_freeN(gdo->vert_points_mem);
	GPU_buffer_free(gdo->points);
	GPU_buffer_free(gdo->normals);
	GPU_buffer_free(gdo->uv);
	GPU_buffer_free(gdo->colors);
	GPU_buffer_free(gdo->edges);
	GPU_buffer_free(gdo->uvedges);

	MEM_freeN(gdo);
	dm->drawObject = NULL;
}

typedef void (*GPUBufferCopyFunc)(DerivedMesh *dm, float *varray, int *index,
				  int *mat_orig_to_new, void *user_data);

static GPUBuffer *gpu_buffer_setup(DerivedMesh *dm, GPUDrawObject *object,
				   int vector_size, int size, GLenum target,
				   void *user, GPUBufferCopyFunc copy_f)
{
	GPUBufferPool *pool;
	GPUBuffer *buffer;
	float *varray;
	int mat_orig_to_new[MAX_MATERIALS];
	int *cur_index_per_mat;
	int i;
	int success;
	GLboolean uploaded;

	pool = gpu_get_global_buffer_pool();

	/* alloc a GPUBuffer; fall back to legacy mode on failure */
	if(!(buffer = GPU_buffer_alloc(size)))
		dm->drawObject->legacy = 1;

	/* nothing to do for legacy mode */
	if(dm->drawObject->legacy)
		return NULL;

	cur_index_per_mat = MEM_mallocN(sizeof(int)*object->totmaterial,
					"GPU_buffer_setup.cur_index_per_mat");
	for(i = 0; i < object->totmaterial; i++) {
		/* for each material, the current index to copy data to */
		cur_index_per_mat[i] = object->materials[i].start * vector_size;

		/* map from original material index to new
		   GPUBufferMaterial index */
		mat_orig_to_new[object->materials[i].mat_nr] = i;
	}

	if(useVBOs) {
		success = 0;

		while(!success) {
			/* bind the buffer and discard previous data,
			   avoids stalling gpu */
			glBindBufferARB(target, buffer->id);
			glBufferDataARB(target, buffer->size, NULL, GL_STATIC_DRAW_ARB);

			/* attempt to map the buffer */
			if(!(varray = glMapBufferARB(target, GL_WRITE_ONLY_ARB))) {
				/* failed to map the buffer; delete it */
				GPU_buffer_free(buffer);
				gpu_buffer_pool_delete_last(pool);
				buffer= NULL;

				/* try freeing an entry from the pool
				   and reallocating the buffer */
				if(pool->totbuf > 0) {
					gpu_buffer_pool_delete_last(pool);
					buffer = GPU_buffer_alloc(size);
				}

				/* allocation still failed; fall back
				   to legacy mode */
				if(!buffer) {
					dm->drawObject->legacy = 1;
					success = 1;
				}
			}
			else {
				success = 1;
			}
		}

		/* check legacy fallback didn't happen */
		if(dm->drawObject->legacy == 0) {
			uploaded = GL_FALSE;
			/* attempt to upload the data to the VBO */
			while(uploaded == GL_FALSE) {
				(*copy_f)(dm, varray, cur_index_per_mat, mat_orig_to_new, user);
				/* glUnmapBuffer returns GL_FALSE if
				   the data store is corrupted; retry
				   in that case */
				uploaded = glUnmapBufferARB(target);
			}
		}
		glBindBufferARB(target, 0);
	}
	else {
		/* VBO not supported, use vertex array fallback */
		if(buffer->pointer) {
			varray = buffer->pointer;
			(*copy_f)(dm, varray, cur_index_per_mat, mat_orig_to_new, user);
		}
		else {
			dm->drawObject->legacy = 1;
		}
	}

	MEM_freeN(cur_index_per_mat);

	return buffer;
}

static void GPU_buffer_copy_vertex(DerivedMesh *dm, float *varray, int *index, int *mat_orig_to_new, void *UNUSED(user))
{
	MVert *mvert;
	MFace *f;
	int i, j, start, totface;

	mvert = dm->getVertArray(dm);
	f = dm->getFaceArray(dm);

	totface= dm->getNumFaces(dm);
	for(i = 0; i < totface; i++, f++) {
		start = index[mat_orig_to_new[f->mat_nr]];

		/* v1 v2 v3 */
		copy_v3_v3(&varray[start], mvert[f->v1].co);
		copy_v3_v3(&varray[start+3], mvert[f->v2].co);
		copy_v3_v3(&varray[start+6], mvert[f->v3].co);
		index[mat_orig_to_new[f->mat_nr]] += 9;

		if(f->v4) {
			/* v3 v4 v1 */
			copy_v3_v3(&varray[start+9], mvert[f->v3].co);
			copy_v3_v3(&varray[start+12], mvert[f->v4].co);
			copy_v3_v3(&varray[start+15], mvert[f->v1].co);
			index[mat_orig_to_new[f->mat_nr]] += 9;
		}
	}

	/* copy loose points */
	j = dm->drawObject->tot_triangle_point*3;
	for(i = 0; i < dm->drawObject->totvert; i++) {
		if(dm->drawObject->vert_points[i].point_index >= dm->drawObject->tot_triangle_point) {
			copy_v3_v3(&varray[j],mvert[i].co);
			j+=3;
		}
	}
}

static void GPU_buffer_copy_normal(DerivedMesh *dm, float *varray, int *index, int *mat_orig_to_new, void *UNUSED(user))
{
	int i, totface;
	int start;
	float f_no[3];

	float *nors= dm->getFaceDataArray(dm, CD_NORMAL);
	MVert *mvert = dm->getVertArray(dm);
	MFace *f = dm->getFaceArray(dm);

	totface= dm->getNumFaces(dm);
	for(i = 0; i < totface; i++, f++) {
		const int smoothnormal = (f->flag & ME_SMOOTH);

		start = index[mat_orig_to_new[f->mat_nr]];
		index[mat_orig_to_new[f->mat_nr]] += f->v4 ? 18 : 9;

		if(smoothnormal) {
			/* copy vertex normal */
			normal_short_to_float_v3(&varray[start], mvert[f->v1].no);
			normal_short_to_float_v3(&varray[start+3], mvert[f->v2].no);
			normal_short_to_float_v3(&varray[start+6], mvert[f->v3].no);

			if(f->v4) {
				normal_short_to_float_v3(&varray[start+9], mvert[f->v3].no);
				normal_short_to_float_v3(&varray[start+12], mvert[f->v4].no);
				normal_short_to_float_v3(&varray[start+15], mvert[f->v1].no);
			}
		}
		else if(nors) {
			/* copy cached face normal */
			copy_v3_v3(&varray[start], &nors[i*3]);
			copy_v3_v3(&varray[start+3], &nors[i*3]);
			copy_v3_v3(&varray[start+6], &nors[i*3]);

			if(f->v4) {
				copy_v3_v3(&varray[start+9], &nors[i*3]);
				copy_v3_v3(&varray[start+12], &nors[i*3]);
				copy_v3_v3(&varray[start+15], &nors[i*3]);
			}
		}
		else {
			/* calculate face normal */
			if(f->v4)
				normal_quad_v3(f_no, mvert[f->v1].co, mvert[f->v2].co, mvert[f->v3].co, mvert[f->v4].co);
			else
				normal_tri_v3(f_no, mvert[f->v1].co, mvert[f->v2].co, mvert[f->v3].co);

			copy_v3_v3(&varray[start], f_no);
			copy_v3_v3(&varray[start+3], f_no);
			copy_v3_v3(&varray[start+6], f_no);

			if(f->v4) {
				copy_v3_v3(&varray[start+9], f_no);
				copy_v3_v3(&varray[start+12], f_no);
				copy_v3_v3(&varray[start+15], f_no);
			}
		}
	}
}

static void GPU_buffer_copy_uv(DerivedMesh *dm, float *varray, int *index, int *mat_orig_to_new, void *UNUSED(user))
{
	int start;
	int i, totface;

	MTFace *mtface;
	MFace *f;

	if(!(mtface = DM_get_face_data_layer(dm, CD_MTFACE)))
		return;
	f = dm->getFaceArray(dm);
		
	totface = dm->getNumFaces(dm);
	for(i = 0; i < totface; i++, f++) {
		start = index[mat_orig_to_new[f->mat_nr]];

		/* v1 v2 v3 */
		copy_v2_v2(&varray[start],mtface[i].uv[0]);
		copy_v2_v2(&varray[start+2],mtface[i].uv[1]);
		copy_v2_v2(&varray[start+4],mtface[i].uv[2]);
		index[mat_orig_to_new[f->mat_nr]] += 6;

		if(f->v4) {
			/* v3 v4 v1 */
			copy_v2_v2(&varray[start+6],mtface[i].uv[2]);
			copy_v2_v2(&varray[start+8],mtface[i].uv[3]);
			copy_v2_v2(&varray[start+10],mtface[i].uv[0]);
			index[mat_orig_to_new[f->mat_nr]] += 6;
		}
	}
}


static void GPU_buffer_copy_color3(DerivedMesh *dm, float *varray_, int *index, int *mat_orig_to_new, void *user)
{
	int i, totface;
	unsigned char *varray = (unsigned char *)varray_;
	unsigned char *mcol = (unsigned char *)user;
	MFace *f = dm->getFaceArray(dm);

	totface= dm->getNumFaces(dm);
	for(i=0; i < totface; i++, f++) {
		int start = index[mat_orig_to_new[f->mat_nr]];

		/* v1 v2 v3 */
		VECCOPY(&varray[start], &mcol[i*12]);
		VECCOPY(&varray[start+3], &mcol[i*12+3]);
		VECCOPY(&varray[start+6], &mcol[i*12+6]);
		index[mat_orig_to_new[f->mat_nr]] += 9;

		if(f->v4) {
			/* v3 v4 v1 */
			VECCOPY(&varray[start+9], &mcol[i*12+6]);
			VECCOPY(&varray[start+12], &mcol[i*12+9]);
			VECCOPY(&varray[start+15], &mcol[i*12]);
			index[mat_orig_to_new[f->mat_nr]] += 9;
		}
	}
}

static void copy_mcol_uc3(unsigned char *v, unsigned char *col)
{
	v[0] = col[3];
	v[1] = col[2];
	v[2] = col[1];
}

/* treat varray_ as an array of MCol, four MCol's per face */
static void GPU_buffer_copy_mcol(DerivedMesh *dm, float *varray_, int *index, int *mat_orig_to_new, void *user)
{
	int i, totface;
	unsigned char *varray = (unsigned char *)varray_;
	unsigned char *mcol = (unsigned char *)user;
	MFace *f = dm->getFaceArray(dm);

	totface= dm->getNumFaces(dm);
	for(i=0; i < totface; i++, f++) {
		int start = index[mat_orig_to_new[f->mat_nr]];

		/* v1 v2 v3 */
		copy_mcol_uc3(&varray[start], &mcol[i*16]);
		copy_mcol_uc3(&varray[start+3], &mcol[i*16+4]);
		copy_mcol_uc3(&varray[start+6], &mcol[i*16+8]);
		index[mat_orig_to_new[f->mat_nr]] += 9;

		if(f->v4) {
			/* v3 v4 v1 */
			copy_mcol_uc3(&varray[start+9], &mcol[i*16+8]);
			copy_mcol_uc3(&varray[start+12], &mcol[i*16+12]);
			copy_mcol_uc3(&varray[start+15], &mcol[i*16]);
			index[mat_orig_to_new[f->mat_nr]] += 9;
		}
	}
}

static void GPU_buffer_copy_edge(DerivedMesh *dm, float *varray_, int *UNUSED(index), int *UNUSED(mat_orig_to_new), void *UNUSED(user))
{
	MEdge *medge;
	unsigned int *varray = (unsigned int *)varray_;
	int i, totedge;
 
	medge = dm->getEdgeArray(dm);
	totedge = dm->getNumEdges(dm);

	for(i = 0; i < totedge; i++, medge++) {
		varray[i*2] = dm->drawObject->vert_points[medge->v1].point_index;
		varray[i*2+1] = dm->drawObject->vert_points[medge->v2].point_index;
	}
}

static void GPU_buffer_copy_uvedge(DerivedMesh *dm, float *varray, int *UNUSED(index), int *UNUSED(mat_orig_to_new), void *UNUSED(user))
{
	MTFace *tf = DM_get_face_data_layer(dm, CD_MTFACE);
	int i, j=0;

	if(!tf)
		return;

	for(i = 0; i < dm->numFaceData; i++, tf++) {
		MFace mf;
		dm->getFace(dm,i,&mf);

		copy_v2_v2(&varray[j],tf->uv[0]);
		copy_v2_v2(&varray[j+2],tf->uv[1]);

		copy_v2_v2(&varray[j+4],tf->uv[1]);
		copy_v2_v2(&varray[j+6],tf->uv[2]);

		if(!mf.v4) {
			copy_v2_v2(&varray[j+8],tf->uv[2]);
			copy_v2_v2(&varray[j+10],tf->uv[0]);
			j+=12;
		} else {
			copy_v2_v2(&varray[j+8],tf->uv[2]);
			copy_v2_v2(&varray[j+10],tf->uv[3]);

			copy_v2_v2(&varray[j+12],tf->uv[3]);
			copy_v2_v2(&varray[j+14],tf->uv[0]);
			j+=16;
		}
	}
}

/* get the DerivedMesh's MCols; choose (in decreasing order of
   preference) from CD_ID_MCOL, CD_WEIGHT_MCOL, or CD_MCOL */
static MCol *gpu_buffer_color_type(DerivedMesh *dm)
{
	MCol *c;
	int type;

	type = CD_ID_MCOL;
	c = DM_get_face_data_layer(dm, type);
	if(!c) {
		type = CD_WEIGHT_MCOL;
		c = DM_get_face_data_layer(dm, type);
		if(!c) {
			type = CD_MCOL;
			c = DM_get_face_data_layer(dm, type);
		}
	}

	dm->drawObject->colType = type;
	return c;
}

typedef enum {
	GPU_BUFFER_VERTEX = 0,
	GPU_BUFFER_NORMAL,
	GPU_BUFFER_COLOR,
	GPU_BUFFER_UV,
	GPU_BUFFER_EDGE,
	GPU_BUFFER_UVEDGE,
} GPUBufferType;

typedef struct {
	GPUBufferCopyFunc copy;
	GLenum gl_buffer_type;
	int vector_size;
} GPUBufferTypeSettings;

const GPUBufferTypeSettings gpu_buffer_type_settings[] = {
	{GPU_buffer_copy_vertex, GL_ARRAY_BUFFER_ARB, 3},
	{GPU_buffer_copy_normal, GL_ARRAY_BUFFER_ARB, 3},
	{GPU_buffer_copy_mcol, GL_ARRAY_BUFFER_ARB, 3},
	{GPU_buffer_copy_uv, GL_ARRAY_BUFFER_ARB, 2},
	{GPU_buffer_copy_edge, GL_ELEMENT_ARRAY_BUFFER_ARB, 2},
	{GPU_buffer_copy_uvedge, GL_ELEMENT_ARRAY_BUFFER_ARB, 4}
};

/* get the GPUDrawObject buffer associated with a type */
static GPUBuffer **gpu_drawobject_buffer_from_type(GPUDrawObject *gdo, GPUBufferType type)
{
	switch(type) {
	case GPU_BUFFER_VERTEX:
		return &gdo->points;
	case GPU_BUFFER_NORMAL:
		return &gdo->normals;
	case GPU_BUFFER_COLOR:
		return &gdo->colors;
	case GPU_BUFFER_UV:
		return &gdo->uv;
	case GPU_BUFFER_EDGE:
		return &gdo->edges;
	case GPU_BUFFER_UVEDGE:
		return &gdo->uvedges;
	default:
		return NULL;
	}
}

/* get the amount of space to allocate for a buffer of a particular type */
static int gpu_buffer_size_from_type(DerivedMesh *dm, GPUBufferType type)
{
	switch(type) {
	case GPU_BUFFER_VERTEX:
		return sizeof(float)*3 * (dm->drawObject->tot_triangle_point + dm->drawObject->tot_loose_point);
	case GPU_BUFFER_NORMAL:
		return sizeof(float)*3*dm->drawObject->tot_triangle_point;
	case GPU_BUFFER_COLOR:
		return sizeof(char)*3*dm->drawObject->tot_triangle_point;
	case GPU_BUFFER_UV:
		return sizeof(float)*2*dm->drawObject->tot_triangle_point;
	case GPU_BUFFER_EDGE:
		return sizeof(int)*2*dm->drawObject->totedge;
	case GPU_BUFFER_UVEDGE:
		/* each face gets 3 points, 3 edges per triangle, and
		   each edge has its own, non-shared coords, so each
		   tri corner needs minimum of 4 floats, quads used
		   less so here we can over allocate and assume all
		   tris. */
		return sizeof(float) * dm->drawObject->tot_triangle_point;
	default:
		return -1;
	}
}

/* call gpu_buffer_setup with settings for a particular type of buffer */
static GPUBuffer *gpu_buffer_setup_type(DerivedMesh *dm, GPUBufferType type)
{
	const GPUBufferTypeSettings *ts;
	void *user_data = NULL;
	GPUBuffer *buf;

	ts = &gpu_buffer_type_settings[type];

	/* special handling for MCol and UV buffers */
	if(type == GPU_BUFFER_COLOR) {
		if(!(user_data = gpu_buffer_color_type(dm)))
			return NULL;
	}
	else if(type == GPU_BUFFER_UV) {
		if(!DM_get_face_data_layer(dm, CD_MTFACE))
			return NULL;
	}

	buf = gpu_buffer_setup(dm, dm->drawObject, ts->vector_size,
			       gpu_buffer_size_from_type(dm, type),
			       ts->gl_buffer_type, user_data, ts->copy);

	return buf;
}

/* get the buffer of `type', initializing the GPUDrawObject and
   buffer if needed */
static GPUBuffer *gpu_buffer_setup_common(DerivedMesh *dm, GPUBufferType type)
{
	GPUBuffer **buf;
	
	if(!dm->drawObject)
		dm->drawObject = GPU_drawobject_new(dm);

	buf = gpu_drawobject_buffer_from_type(dm->drawObject, type);
	if(!(*buf))
		*buf = gpu_buffer_setup_type(dm, type);

	return *buf;
}

void GPU_vertex_setup(DerivedMesh *dm)
{
	if(!gpu_buffer_setup_common(dm, GPU_BUFFER_VERTEX))
		return;

	glEnableClientState(GL_VERTEX_ARRAY);
	if(useVBOs) {
		glBindBufferARB(GL_ARRAY_BUFFER_ARB, dm->drawObject->points->id);
		glVertexPointer(3, GL_FLOAT, 0, 0);
	}
	else {
		glVertexPointer(3, GL_FLOAT, 0, dm->drawObject->points->pointer);
	}
	
	GLStates |= GPU_BUFFER_VERTEX_STATE;
}

void GPU_normal_setup(DerivedMesh *dm)
{
	if(!gpu_buffer_setup_common(dm, GPU_BUFFER_NORMAL))
		return;

	glEnableClientState(GL_NORMAL_ARRAY);
	if(useVBOs) {
		glBindBufferARB(GL_ARRAY_BUFFER_ARB, dm->drawObject->normals->id);
		glNormalPointer(GL_FLOAT, 0, 0);
	}
	else {
		glNormalPointer(GL_FLOAT, 0, dm->drawObject->normals->pointer);
	}

	GLStates |= GPU_BUFFER_NORMAL_STATE;
}

void GPU_uv_setup(DerivedMesh *dm)
{
	if(!gpu_buffer_setup_common(dm, GPU_BUFFER_UV))
		return;

	glEnableClientState(GL_TEXTURE_COORD_ARRAY);
	if(useVBOs) {
		glBindBufferARB(GL_ARRAY_BUFFER_ARB, dm->drawObject->uv->id);
		glTexCoordPointer(2, GL_FLOAT, 0, 0);
	}
	else {
		glTexCoordPointer(2, GL_FLOAT, 0, dm->drawObject->uv->pointer);
	}

	GLStates |= GPU_BUFFER_TEXCOORD_STATE;
}

void GPU_color_setup(DerivedMesh *dm)
{
	if(!gpu_buffer_setup_common(dm, GPU_BUFFER_COLOR))
		return;

	glEnableClientState(GL_COLOR_ARRAY);
	if(useVBOs) {
		glBindBufferARB(GL_ARRAY_BUFFER_ARB, dm->drawObject->colors->id);
		glColorPointer(3, GL_UNSIGNED_BYTE, 0, 0);
	}
	else {
		glColorPointer(3, GL_UNSIGNED_BYTE, 0, dm->drawObject->colors->pointer);
	}

	GLStates |= GPU_BUFFER_COLOR_STATE;
}

void GPU_edge_setup(DerivedMesh *dm)
{
	if(!gpu_buffer_setup_common(dm, GPU_BUFFER_EDGE))
		return;

	if(!gpu_buffer_setup_common(dm, GPU_BUFFER_VERTEX))
		return;

	glEnableClientState(GL_VERTEX_ARRAY);
	if(useVBOs) {
		glBindBufferARB(GL_ARRAY_BUFFER_ARB, dm->drawObject->points->id);
		glVertexPointer(3, GL_FLOAT, 0, 0);
	}
	else {
		glVertexPointer(3, GL_FLOAT, 0, dm->drawObject->points->pointer);
	}
	
	GLStates |= GPU_BUFFER_VERTEX_STATE;

	if(useVBOs)
		glBindBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, dm->drawObject->edges->id);

	GLStates |= GPU_BUFFER_ELEMENT_STATE;
}

void GPU_uvedge_setup(DerivedMesh *dm)
{
	if(!gpu_buffer_setup_common(dm, GPU_BUFFER_UVEDGE))
		return;

	glEnableClientState(GL_VERTEX_ARRAY);
	if(useVBOs) {
		glBindBufferARB(GL_ARRAY_BUFFER_ARB, dm->drawObject->uvedges->id);
		glVertexPointer(2, GL_FLOAT, 0, 0);
	}
	else {
		glVertexPointer(2, GL_FLOAT, 0, dm->drawObject->uvedges->pointer);
	}
	
	GLStates |= GPU_BUFFER_VERTEX_STATE;
}

static int GPU_typesize(int type) {
	switch(type) {
	case GL_FLOAT:
		return sizeof(float);
	case GL_INT:
		return sizeof(int);
	case GL_UNSIGNED_INT:
		return sizeof(unsigned int);
	case GL_BYTE:
		return sizeof(char);
	case GL_UNSIGNED_BYTE:
		return sizeof(unsigned char);
	default:
		return 0;
	}
}

int GPU_attrib_element_size(GPUAttrib data[], int numdata) {
	int i, elementsize = 0;

	for(i = 0; i < numdata; i++) {
		int typesize = GPU_typesize(data[i].type);
		if(typesize != 0)
			elementsize += typesize*data[i].size;
	}
	return elementsize;
}

void GPU_interleaved_attrib_setup(GPUBuffer *buffer, GPUAttrib data[], int numdata) {
	int i;
	int elementsize;
	intptr_t offset = 0;

	for(i = 0; i < MAX_GPU_ATTRIB_DATA; i++) {
		if(attribData[i].index != -1) {
			glDisableVertexAttribArrayARB(attribData[i].index);
		}
		else
			break;
	}
	elementsize = GPU_attrib_element_size(data, numdata);

	if(useVBOs) {
		glBindBufferARB(GL_ARRAY_BUFFER_ARB, buffer->id);
		for(i = 0; i < numdata; i++) {
			glEnableVertexAttribArrayARB(data[i].index);
			glVertexAttribPointerARB(data[i].index, data[i].size, data[i].type,
						 GL_FALSE, elementsize, (void *)offset);
			offset += data[i].size*GPU_typesize(data[i].type);

			attribData[i].index = data[i].index;
			attribData[i].size = data[i].size;
			attribData[i].type = data[i].type;
		}
		attribData[numdata].index = -1;
	}
	else {
		for(i = 0; i < numdata; i++) {
			glEnableVertexAttribArrayARB(data[i].index);
			glVertexAttribPointerARB(data[i].index, data[i].size, data[i].type,
						 GL_FALSE, elementsize, (char *)buffer->pointer + offset);
			offset += data[i].size*GPU_typesize(data[i].type);
		}
	}
}


void GPU_buffer_unbind(void)
{
	int i;

	if(GLStates & GPU_BUFFER_VERTEX_STATE)
		glDisableClientState(GL_VERTEX_ARRAY);
	if(GLStates & GPU_BUFFER_NORMAL_STATE)
		glDisableClientState(GL_NORMAL_ARRAY);
	if(GLStates & GPU_BUFFER_TEXCOORD_STATE)
		glDisableClientState(GL_TEXTURE_COORD_ARRAY);
	if(GLStates & GPU_BUFFER_COLOR_STATE)
		glDisableClientState(GL_COLOR_ARRAY);
	if(GLStates & GPU_BUFFER_ELEMENT_STATE) {
		if(useVBOs) {
			glBindBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, 0);
		}
	}
	GLStates &= !(GPU_BUFFER_VERTEX_STATE | GPU_BUFFER_NORMAL_STATE |
		      GPU_BUFFER_TEXCOORD_STATE | GPU_BUFFER_COLOR_STATE |
		      GPU_BUFFER_ELEMENT_STATE);

	for(i = 0; i < MAX_GPU_ATTRIB_DATA; i++) {
		if(attribData[i].index != -1) {
			glDisableVertexAttribArrayARB(attribData[i].index);
		}
		else
			break;
	}

	if(useVBOs)
		glBindBufferARB(GL_ARRAY_BUFFER_ARB, 0);
}

/* confusion: code in cdderivedmesh calls both GPU_color_setup and
   GPU_color3_upload; both of these set the `colors' buffer, so seems
   like it will just needlessly overwrite? --nicholas */
void GPU_color3_upload(DerivedMesh *dm, unsigned char *data)
{
	if(dm->drawObject == 0)
		dm->drawObject = GPU_drawobject_new(dm);
	GPU_buffer_free(dm->drawObject->colors);

	dm->drawObject->colors = gpu_buffer_setup(dm, dm->drawObject, 3,
						  sizeof(char)*3*dm->drawObject->tot_triangle_point,
						  GL_ARRAY_BUFFER_ARB, data, GPU_buffer_copy_color3);
}

/* this is used only in cdDM_drawFacesColored, which I think is no
   longer used, so can probably remove this --nicholas */
void GPU_color4_upload(DerivedMesh *UNUSED(dm), unsigned char *UNUSED(data))
{
	/*if(dm->drawObject == 0)
		dm->drawObject = GPU_drawobject_new(dm);
	GPU_buffer_free(dm->drawObject->colors);
	dm->drawObject->colors = gpu_buffer_setup(dm, dm->drawObject, 3,
						  sizeof(char)*3*dm->drawObject->tot_triangle_point,
						  GL_ARRAY_BUFFER_ARB, data, GPU_buffer_copy_color4);*/
}

void GPU_color_switch(int mode)
{
	if(mode) {
		if(!(GLStates & GPU_BUFFER_COLOR_STATE))
			glEnableClientState(GL_COLOR_ARRAY);
		GLStates |= GPU_BUFFER_COLOR_STATE;
	}
	else {
		if(GLStates & GPU_BUFFER_COLOR_STATE)
			glDisableClientState(GL_COLOR_ARRAY);
		GLStates &= (!GPU_BUFFER_COLOR_STATE);
	}
}

/* return 1 if drawing should be done using old immediate-mode
   code, 0 otherwise */
int GPU_buffer_legacy(DerivedMesh *dm)
{
	int test= (U.gameflags & USER_DISABLE_VBO);
	if(test)
		return 1;

	if(dm->drawObject == 0)
		dm->drawObject = GPU_drawobject_new(dm);
	return dm->drawObject->legacy;
}

void *GPU_buffer_lock(GPUBuffer *buffer)
{
	float *varray;

	if(!buffer)
		return 0;

	if(useVBOs) {
		glBindBufferARB(GL_ARRAY_BUFFER_ARB, buffer->id);
		varray = glMapBufferARB(GL_ARRAY_BUFFER_ARB, GL_WRITE_ONLY_ARB);
		return varray;
	}
	else {
		return buffer->pointer;
	}
}

void *GPU_buffer_lock_stream(GPUBuffer *buffer)
{
	float *varray;

	if(!buffer)
		return 0;

	if(useVBOs) {
		glBindBufferARB(GL_ARRAY_BUFFER_ARB, buffer->id);
		/* discard previous data, avoid stalling gpu */
		glBufferDataARB(GL_ARRAY_BUFFER_ARB, buffer->size, 0, GL_STREAM_DRAW_ARB);
		varray = glMapBufferARB(GL_ARRAY_BUFFER_ARB, GL_WRITE_ONLY_ARB);
		return varray;
	}
	else {
		return buffer->pointer;
	}
}

void GPU_buffer_unlock(GPUBuffer *buffer)
{
	if(useVBOs) {
		if(buffer) {
			/* note: this operation can fail, could return
			   an error code from this function? */
			glUnmapBufferARB(GL_ARRAY_BUFFER_ARB);
		}
		glBindBufferARB(GL_ARRAY_BUFFER_ARB, 0);
	}
}

/* used for drawing edges */
void GPU_buffer_draw_elements(GPUBuffer *elements, unsigned int mode, int start, int count)
{
	glDrawElements(mode, count, GL_UNSIGNED_INT,
		       (useVBOs ?
			(void*)(start * sizeof(unsigned int)) :
			((int*)elements->pointer) + start));
}


/* XXX: the rest of the code in this file is used for optimized PBVH
   drawing and doesn't interact at all with the buffer code above */

/* Convenience struct for building the VBO. */
typedef struct {
	float co[3];
	short no[3];
} VertexBufferFormat;

typedef struct {
	/* opengl buffer handles */
	GLuint vert_buf, index_buf;
	GLenum index_type;

	/* mesh pointers in case buffer allocation fails */
	MFace *mface;
	MVert *mvert;
	int *face_indices;
	int totface;

	/* grid pointers */
	DMGridData **grids;
	int *grid_indices;
	int totgrid;
	int gridsize;

	unsigned int tot_tri, tot_quad;
} GPU_Buffers;

void GPU_update_mesh_buffers(void *buffers_v, MVert *mvert,
			int *vert_indices, int totvert)
{
	GPU_Buffers *buffers = buffers_v;
	VertexBufferFormat *vert_data;
	int i;

	if(buffers->vert_buf) {
		/* Build VBO */
		glBindBufferARB(GL_ARRAY_BUFFER_ARB, buffers->vert_buf);
		glBufferDataARB(GL_ARRAY_BUFFER_ARB,
				 sizeof(VertexBufferFormat) * totvert,
				 NULL, GL_STATIC_DRAW_ARB);
		vert_data = glMapBufferARB(GL_ARRAY_BUFFER_ARB, GL_WRITE_ONLY_ARB);

		if(vert_data) {
			for(i = 0; i < totvert; ++i) {
				MVert *v = mvert + vert_indices[i];
				VertexBufferFormat *out = vert_data + i;

				copy_v3_v3(out->co, v->co);
				memcpy(out->no, v->no, sizeof(short) * 3);
			}

			glUnmapBufferARB(GL_ARRAY_BUFFER_ARB);
		}
		else {
			glDeleteBuffersARB(1, &buffers->vert_buf);
			buffers->vert_buf = 0;
		}

		glBindBufferARB(GL_ARRAY_BUFFER_ARB, 0);
	}

	buffers->mvert = mvert;
}

void *GPU_build_mesh_buffers(GHash *map, MVert *mvert, MFace *mface,
			int *face_indices, int totface,
			int *vert_indices, int tot_uniq_verts,
			int totvert)
{
	GPU_Buffers *buffers;
	unsigned short *tri_data;
	int i, j, k, tottri;

	buffers = MEM_callocN(sizeof(GPU_Buffers), "GPU_Buffers");
	buffers->index_type = GL_UNSIGNED_SHORT;

	/* Count the number of triangles */
	for(i = 0, tottri = 0; i < totface; ++i)
		tottri += mface[face_indices[i]].v4 ? 2 : 1;
	
	if(GLEW_ARB_vertex_buffer_object && !(U.gameflags & USER_DISABLE_VBO))
		glGenBuffersARB(1, &buffers->index_buf);

	if(buffers->index_buf) {
		/* Generate index buffer object */
		glBindBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, buffers->index_buf);
		glBufferDataARB(GL_ELEMENT_ARRAY_BUFFER_ARB,
				 sizeof(unsigned short) * tottri * 3, NULL, GL_STATIC_DRAW_ARB);

		/* Fill the triangle buffer */
		tri_data = glMapBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, GL_WRITE_ONLY_ARB);
		if(tri_data) {
			for(i = 0; i < totface; ++i) {
				MFace *f = mface + face_indices[i];
				int v[3];

				v[0]= f->v1;
				v[1]= f->v2;
				v[2]= f->v3;

				for(j = 0; j < (f->v4 ? 2 : 1); ++j) {
					for(k = 0; k < 3; ++k) {
						void *value, *key = SET_INT_IN_POINTER(v[k]);
						int vbo_index;

						value = BLI_ghash_lookup(map, key);
						vbo_index = GET_INT_FROM_POINTER(value);

						if(vbo_index < 0) {
							vbo_index = -vbo_index +
								tot_uniq_verts - 1;
						}

						*tri_data = vbo_index;
						++tri_data;
					}
					v[0] = f->v4;
					v[1] = f->v1;
					v[2] = f->v3;
				}
			}
			glUnmapBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB);
		}
		else {
			glDeleteBuffersARB(1, &buffers->index_buf);
			buffers->index_buf = 0;
		}

		glBindBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, 0);
	}

	if(buffers->index_buf)
		glGenBuffersARB(1, &buffers->vert_buf);
	GPU_update_mesh_buffers(buffers, mvert, vert_indices, totvert);

	buffers->tot_tri = tottri;

	buffers->mface = mface;
	buffers->face_indices = face_indices;
	buffers->totface = totface;

	return buffers;
}

void GPU_update_grid_buffers(void *buffers_v, DMGridData **grids,
	int *grid_indices, int totgrid, int gridsize, int smooth)
{
	GPU_Buffers *buffers = buffers_v;
	DMGridData *vert_data;
	int i, j, k, totvert;

	totvert= gridsize*gridsize*totgrid;

	/* Build VBO */
	if(buffers->vert_buf) {
		glBindBufferARB(GL_ARRAY_BUFFER_ARB, buffers->vert_buf);
		glBufferDataARB(GL_ARRAY_BUFFER_ARB,
				 sizeof(DMGridData) * totvert,
				 NULL, GL_STATIC_DRAW_ARB);
		vert_data = glMapBufferARB(GL_ARRAY_BUFFER_ARB, GL_WRITE_ONLY_ARB);
		if(vert_data) {
			for(i = 0; i < totgrid; ++i) {
				DMGridData *grid= grids[grid_indices[i]];
				memcpy(vert_data, grid, sizeof(DMGridData)*gridsize*gridsize);

				if(!smooth) {
					/* for flat shading, recalc normals and set the last vertex of
					   each quad in the index buffer to have the flat normal as
					   that is what opengl will use */
					for(j = 0; j < gridsize-1; ++j) {
						for(k = 0; k < gridsize-1; ++k) {
							normal_quad_v3(vert_data[(j+1)*gridsize + (k+1)].no,
								vert_data[(j+1)*gridsize + k].co,
								vert_data[(j+1)*gridsize + k+1].co,
								vert_data[j*gridsize + k+1].co,
								vert_data[j*gridsize + k].co);
						}
					}
				}

				vert_data += gridsize*gridsize;
			}
			glUnmapBufferARB(GL_ARRAY_BUFFER_ARB);
		}
		else {
			glDeleteBuffersARB(1, &buffers->vert_buf);
			buffers->vert_buf = 0;
		}
		glBindBufferARB(GL_ARRAY_BUFFER_ARB, 0);
	}

	buffers->grids = grids;
	buffers->grid_indices = grid_indices;
	buffers->totgrid = totgrid;
	buffers->gridsize = gridsize;

	//printf("node updated %p\n", buffers_v);
}

void *GPU_build_grid_buffers(DMGridData **UNUSED(grids), int *UNUSED(grid_indices),
				int totgrid, int gridsize)
{
	GPU_Buffers *buffers;
	int i, j, k, totquad, offset= 0;

	buffers = MEM_callocN(sizeof(GPU_Buffers), "GPU_Buffers");

	/* Count the number of quads */
	totquad= (gridsize-1)*(gridsize-1)*totgrid;

	/* Generate index buffer object */
	if(GLEW_ARB_vertex_buffer_object && !(U.gameflags & USER_DISABLE_VBO))
		glGenBuffersARB(1, &buffers->index_buf);

	if(buffers->index_buf) {
		glBindBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, buffers->index_buf);

		if(totquad < USHRT_MAX) {
			unsigned short *quad_data;

			buffers->index_type = GL_UNSIGNED_SHORT;
			glBufferDataARB(GL_ELEMENT_ARRAY_BUFFER_ARB,
					 sizeof(unsigned short) * totquad * 4, NULL, GL_STATIC_DRAW_ARB);

			/* Fill the quad buffer */
			quad_data = glMapBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, GL_WRITE_ONLY_ARB);
			if(quad_data) {
				for(i = 0; i < totgrid; ++i) {
					for(j = 0; j < gridsize-1; ++j) {
						for(k = 0; k < gridsize-1; ++k) {
							*(quad_data++)= offset + j*gridsize + k+1;
							*(quad_data++)= offset + j*gridsize + k;
							*(quad_data++)= offset + (j+1)*gridsize + k;
							*(quad_data++)= offset + (j+1)*gridsize + k+1;
						}
					}

					offset += gridsize*gridsize;
				}
				glUnmapBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB);
			}
			else {
				glDeleteBuffersARB(1, &buffers->index_buf);
				buffers->index_buf = 0;
			}
		}
		else {
			unsigned int *quad_data;

			buffers->index_type = GL_UNSIGNED_INT;
			glBufferDataARB(GL_ELEMENT_ARRAY_BUFFER_ARB,
					 sizeof(unsigned int) * totquad * 4, NULL, GL_STATIC_DRAW_ARB);

			/* Fill the quad buffer */
			quad_data = glMapBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, GL_WRITE_ONLY_ARB);

			if(quad_data) {
				for(i = 0; i < totgrid; ++i) {
					for(j = 0; j < gridsize-1; ++j) {
						for(k = 0; k < gridsize-1; ++k) {
							*(quad_data++)= offset + j*gridsize + k+1;
							*(quad_data++)= offset + j*gridsize + k;
							*(quad_data++)= offset + (j+1)*gridsize + k;
							*(quad_data++)= offset + (j+1)*gridsize + k+1;
						}
					}

					offset += gridsize*gridsize;
				}
				glUnmapBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB);
			}
			else {
				glDeleteBuffersARB(1, &buffers->index_buf);
				buffers->index_buf = 0;
			}
		}

		glBindBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, 0);
	}

	/* Build VBO */
	if(buffers->index_buf)
		glGenBuffersARB(1, &buffers->vert_buf);

	buffers->tot_quad = totquad;

	return buffers;
}

void GPU_draw_buffers(void *buffers_v)
{
	GPU_Buffers *buffers = buffers_v;

	if(buffers->vert_buf && buffers->index_buf) {
		glEnableClientState(GL_VERTEX_ARRAY);
		glEnableClientState(GL_NORMAL_ARRAY);

		glBindBufferARB(GL_ARRAY_BUFFER_ARB, buffers->vert_buf);
		glBindBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, buffers->index_buf);

		if(buffers->tot_quad) {
			glVertexPointer(3, GL_FLOAT, sizeof(DMGridData), (void*)offsetof(DMGridData, co));
			glNormalPointer(GL_FLOAT, sizeof(DMGridData), (void*)offsetof(DMGridData, no));

			glDrawElements(GL_QUADS, buffers->tot_quad * 4, buffers->index_type, 0);
		}
		else {
			glVertexPointer(3, GL_FLOAT, sizeof(VertexBufferFormat), (void*)offsetof(VertexBufferFormat, co));
			glNormalPointer(GL_SHORT, sizeof(VertexBufferFormat), (void*)offsetof(VertexBufferFormat, no));

			glDrawElements(GL_TRIANGLES, buffers->tot_tri * 3, buffers->index_type, 0);
		}

		glBindBufferARB(GL_ARRAY_BUFFER_ARB, 0);
		glBindBufferARB(GL_ELEMENT_ARRAY_BUFFER_ARB, 0);

		glDisableClientState(GL_VERTEX_ARRAY);
		glDisableClientState(GL_NORMAL_ARRAY);
	}
	else if(buffers->totface) {
		/* fallback if we are out of memory */
		int i;

		for(i = 0; i < buffers->totface; ++i) {
			MFace *f = buffers->mface + buffers->face_indices[i];

			glBegin((f->v4)? GL_QUADS: GL_TRIANGLES);
			glNormal3sv(buffers->mvert[f->v1].no);
			glVertex3fv(buffers->mvert[f->v1].co);
			glNormal3sv(buffers->mvert[f->v2].no);
			glVertex3fv(buffers->mvert[f->v2].co);
			glNormal3sv(buffers->mvert[f->v3].no);
			glVertex3fv(buffers->mvert[f->v3].co);
			if(f->v4) {
				glNormal3sv(buffers->mvert[f->v4].no);
				glVertex3fv(buffers->mvert[f->v4].co);
			}
			glEnd();
		}
	}
	else if(buffers->totgrid) {
		int i, x, y, gridsize = buffers->gridsize;

		for(i = 0; i < buffers->totgrid; ++i) {
			DMGridData *grid = buffers->grids[buffers->grid_indices[i]];

			for(y = 0; y < gridsize-1; y++) {
				glBegin(GL_QUAD_STRIP);
				for(x = 0; x < gridsize; x++) {
					DMGridData *a = &grid[y*gridsize + x];
					DMGridData *b = &grid[(y+1)*gridsize + x];

					glNormal3fv(a->no);
					glVertex3fv(a->co);
					glNormal3fv(b->no);
					glVertex3fv(b->co);
				}
				glEnd();
			}
		}
	}
}

void GPU_free_buffers(void *buffers_v)
{
	if(buffers_v) {
		GPU_Buffers *buffers = buffers_v;
		
		if(buffers->vert_buf)
			glDeleteBuffersARB(1, &buffers->vert_buf);
		if(buffers->index_buf)
			glDeleteBuffersARB(1, &buffers->index_buf);

		MEM_freeN(buffers);
	}
}

