/*
 * Copyright 2011, Blender Foundation.
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
 */

#ifndef __KERNEL_TYPES_H__
#define __KERNEL_TYPES_H__

#include "kernel_math.h"

#include "svm/svm_types.h"

CCL_NAMESPACE_BEGIN

#define OBJECT_SIZE 16
#define LIGHT_SIZE	4

#define __SOBOL__
#define __INSTANCING__
#define __DPDU__
#define __UV__
#define __BACKGROUND__
#define __CAUSTICS_TRICKS__
#define __VISIBILITY_FLAG__
#define __RAY_DIFFERENTIALS__
#define __CAMERA_CLIPPING__
#define __INTERSECTION_REFINE__

#ifndef __KERNEL_OPENCL__
#define __SVM__
#define __EMISSION__
#define __TEXTURES__
#define __HOLDOUT__
#define __MULTI_CLOSURE__
//#define __TRANSPARENT_SHADOWS__
//#define __MULTI_LIGHT__
#endif

#ifdef __KERNEL_CPU__
//#define __OSL__
#endif

//#define __SOBOL_FULL_SCREEN__
//#define __MODIFY_TP__
//#define __QBVH__

/* Path Tracing */

enum PathTraceDimension {
	PRNG_FILTER_U = 0,
	PRNG_FILTER_V = 1,
	PRNG_LENS_U = 2,
	PRNG_LENS_V = 3,
	PRNG_BASE_NUM = 4,

	PRNG_BSDF_U = 0,
	PRNG_BSDF_V = 1,
	PRNG_BSDF = 2,
	PRNG_LIGHT = 3,
	PRNG_LIGHT_U = 4,
	PRNG_LIGHT_V = 5,
	PRNG_LIGHT_F = 6,
	PRNG_TERMINATE = 7,
	PRNG_BOUNCE_NUM = 8
};

/* these flag values correspond exactly to OSL defaults, so be careful not to
 * change this, or if you do, set the "raytypes" shading system attribute with
 * your own new ray types and bitflag values */

enum PathRayFlag {
	PATH_RAY_CAMERA = 1,
	PATH_RAY_SHADOW = 2,
	PATH_RAY_REFLECT = 4,
	PATH_RAY_TRANSMIT = 8,
	PATH_RAY_DIFFUSE = 16,
	PATH_RAY_GLOSSY = 32,
	PATH_RAY_SINGULAR = 64,
	PATH_RAY_TRANSPARENT = 128,

	PATH_RAY_ALL = (1|2|4|8|16|32|64|128)
};

/* Closure Label */

typedef enum ClosureLabel {
	LABEL_NONE = 0,
	LABEL_CAMERA = 1,
	LABEL_LIGHT = 2,
	LABEL_BACKGROUND = 4,
	LABEL_TRANSMIT = 8,
	LABEL_REFLECT = 16,
	LABEL_VOLUME = 32,
	LABEL_OBJECT = 64,
	LABEL_DIFFUSE = 128,
	LABEL_GLOSSY = 256,
	LABEL_SINGULAR = 512,
	LABEL_TRANSPARENT = 1024,
	LABEL_STOP = 2048
} ClosureLabel;

/* Shader Flag */

typedef enum ShaderFlag {
	SHADER_SMOOTH_NORMAL = (1 << 31),
	SHADER_CAST_SHADOW = (1 << 30),
	SHADER_AREA_LIGHT = (1 << 29),

	SHADER_MASK = ~(SHADER_SMOOTH_NORMAL|SHADER_CAST_SHADOW|SHADER_AREA_LIGHT)
} ShaderFlag;

/* Light Type */

typedef enum LightType {
	LIGHT_POINT,
	LIGHT_DISTANT,
	LIGHT_AREA
} LightType;

/* Differential */

typedef struct differential3 {
	float3 dx;
	float3 dy;
} differential3;

typedef struct differential {
	float dx;
	float dy;
} differential;

/* Ray */

typedef struct Ray {
	float3 P;
	float3 D;
	float t;

#ifdef __RAY_DIFFERENTIALS__
	differential3 dP;
	differential3 dD;
#endif
} Ray;

/* Intersection */

typedef struct Intersection {
	float t, u, v;
	int prim;
	int object;
} Intersection;

/* Attributes */

typedef enum AttributeElement {
	ATTR_ELEMENT_FACE,
	ATTR_ELEMENT_VERTEX,
	ATTR_ELEMENT_CORNER,
	ATTR_ELEMENT_VALUE,
	ATTR_ELEMENT_NONE
} AttributeElement;

/* Closure data */

#define MAX_CLOSURE 8

typedef struct ShaderClosure {
	ClosureType type;
	float3 weight;

#ifdef __MULTI_CLOSURE__
	float sample_weight;
#endif

#ifdef __OSL__
	void *prim;
#else
	float data0;
	float data1;
#endif

} ShaderClosure;

/* Shader Data
 *
 * Main shader state at a point on the surface or in a volume. All coordinates
 * are in world space. */

enum ShaderDataFlag {
	/* runtime flags */
	SD_BACKFACING = 1,		/* backside of surface? */
	SD_EMISSION = 2,		/* have emissive closure? */
	SD_BSDF = 4,			/* have bsdf closure? */
	SD_BSDF_HAS_EVAL = 8,	/* have non-singular bsdf closure? */
	SD_BSDF_GLOSSY = 16,	/* have glossy bsdf */
	SD_HOLDOUT = 32,		/* have holdout closure? */
	SD_VOLUME = 64,			/* have volume closure? */

	/* shader flags */
	SD_SAMPLE_AS_LIGHT = 128,			/* direct light sample */
	SD_HAS_SURFACE_TRANSPARENT = 256,	/* has surface transparency */
	SD_HAS_VOLUME = 512,				/* has volume shader */
	SD_HOMOGENEOUS_VOLUME = 1024		/* has homogeneous volume */
};

typedef struct ShaderData {
	/* position */
	float3 P;
	/* smooth normal for shading */
	float3 N;
	/* true geometric normal */
	float3 Ng;
	/* view/incoming direction */
	float3 I;
	/* shader id */
	int shader;	
	/* booleans describing shader, see ShaderDataFlag */
	int flag;

	/* primitive id if there is one, ~0 otherwise */
	int prim;
	/* parametric coordinates
	 * - barycentric weights for triangles */
	float u, v;
	/* object id if there is one, ~0 otherwise */
	int object;

#ifdef __RAY_DIFFERENTIALS__
	/* differential of P. these are orthogonal to Ng, not N */
	differential3 dP;
	/* differential of I */
	differential3 dI;
	/* differential of u, v */
	differential du;
	differential dv;
#endif
#ifdef __DPDU__
	/* differential of P w.r.t. parametric coordinates. note that dPdu is
	 * not readily suitable as a tangent for shading on triangles. */
	float3 dPdu, dPdv;
#endif

#ifdef __MULTI_CLOSURE__
	/* Closure data, we store a fixed array of closures */
	ShaderClosure closure[MAX_CLOSURE];
	int num_closure;
	float randb_closure;
#else
	/* Closure data, with a single sampled closure for low memory usage */
	ShaderClosure closure;
#endif

#ifdef __OSL__
	/* OSL context */
	void *osl_ctx;
#endif
} ShaderData;

/* Constrant Kernel Data */

typedef struct KernelCamera {
	/* type */
	int ortho;
	int pad;

	/* size */
	int width, height;

	/* matrices */
	Transform cameratoworld;
	Transform rastertocamera;

	/* differentials */
	float3 dx;
#ifndef WITH_OPENCL
	float pad1;
#endif
	float3 dy;
#ifndef WITH_OPENCL
	float pad2;
#endif

	/* depth of field */
	float aperturesize;
	float blades;
	float bladesrotation;
	float focaldistance;

	/* motion blur */
	float shutteropen;
	float shutterclose;

	/* clipping */
	float nearclip;
	float cliplength;

	/* more matrices */
	Transform screentoworld;
	Transform rastertoworld;
	Transform ndctoworld;
	Transform worldtoscreen;
	Transform worldtoraster;
	Transform worldtondc;
	Transform worldtocamera;
} KernelCamera;

typedef struct KernelFilm {
	float exposure;
	int pad1, pad2, pad3;
} KernelFilm;

typedef struct KernelBackground {
	/* only shader index */
	int shader;
	int transparent;
	int pad1, pad2;
} KernelBackground;

typedef struct KernelSunSky {
	/* sun direction in spherical and cartesian */
	float theta, phi, pad3, pad4;
	float3 dir;
#ifndef WITH_OPENCL
	float pad;
#endif

	/* perez function parameters */
	float zenith_Y, zenith_x, zenith_y, pad2;
	float perez_Y[5], perez_x[5], perez_y[5];
	float pad5;
} KernelSunSky;

typedef struct KernelIntegrator {
	/* emission */
	int use_direct_light;
	int num_distribution;
	int num_all_lights;
	float pdf_triangles;
	float pdf_lights;
	float pdf_pad;

	/* bounces */
	int min_bounce;
	int max_bounce;

    int max_diffuse_bounce;
    int max_glossy_bounce;
    int max_transmission_bounce;

	/* transparent */
    int transparent_min_bounce;
    int transparent_max_bounce;
	int transparent_shadows;

	/* caustics */
	int no_caustics;
	float blur_caustics;
} KernelIntegrator;

typedef struct KernelBVH {
	/* root node */
	int root;
	int attributes_map_stride;
	int pad1, pad2;
} KernelBVH;

typedef struct KernelData {
	KernelCamera cam;
	KernelFilm film;
	KernelBackground background;
	KernelSunSky sunsky;
	KernelIntegrator integrator;
	KernelBVH bvh;
} KernelData;

CCL_NAMESPACE_END

#endif /*  __KERNEL_TYPES_H__ */

