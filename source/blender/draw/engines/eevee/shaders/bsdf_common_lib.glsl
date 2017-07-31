
#define M_PI        3.14159265358979323846  /* pi */
#define M_2PI       6.28318530717958647692  /* 2*pi */
#define M_PI_2      1.57079632679489661923  /* pi/2 */
#define M_1_PI      0.318309886183790671538  /* 1/pi */
#define M_1_2PI     0.159154943091895335768  /* 1/(2*pi) */
#define M_1_PI2     0.101321183642337771443  /* 1/(pi^2) */

#define LUT_SIZE 64

uniform mat4 ProjectionMatrix;
uniform mat4 ViewProjectionMatrix;
uniform mat4 ViewMatrixInverse;
uniform vec4 viewvecs[2];
#ifndef SHADOW_SHADER
uniform mat4 ViewMatrix;
#else
layout(std140) uniform shadow_render_block {
	mat4 ShadowMatrix[6];
	mat4 FaceViewMatrix[6];
	vec4 lampPosition;
	int layer;
	float exponent;
};

flat in int shFace; /* Shadow layer we are rendering to. */
#define ViewMatrix      FaceViewMatrix[shFace]
#endif

#define cameraForward   normalize(ViewMatrixInverse[2].xyz)
#define cameraPos       ViewMatrixInverse[3].xyz
#define cameraVec      ((ProjectionMatrix[3][3] == 0.0) ? normalize(cameraPos - worldPosition) : cameraForward)
#define viewCameraVec  ((ProjectionMatrix[3][3] == 0.0) ? normalize(-viewPosition) : vec3(0.0, 0.0, 1.0))

/* ------- Structures -------- */
struct LightData {
	vec4 position_influence;      /* w : InfluenceRadius */
	vec4 color_spec;              /* w : Spec Intensity */
	vec4 spotdata_radius_shadow;  /* x : spot size, y : spot blend, z : radius, w: shadow id */
	vec4 rightvec_sizex;          /* xyz: Normalized up vector, w: area size X or spot scale X */
	vec4 upvec_sizey;             /* xyz: Normalized right vector, w: area size Y or spot scale Y */
	vec4 forwardvec_type;         /* xyz: Normalized forward vector, w: Lamp Type */
};

/* convenience aliases */
#define l_color        color_spec.rgb
#define l_spec         color_spec.a
#define l_position     position_influence.xyz
#define l_influence    position_influence.w
#define l_sizex        rightvec_sizex.w
#define l_sizey        upvec_sizey.w
#define l_right        rightvec_sizex.xyz
#define l_up           upvec_sizey.xyz
#define l_forward      forwardvec_type.xyz
#define l_type         forwardvec_type.w
#define l_spot_size    spotdata_radius_shadow.x
#define l_spot_blend   spotdata_radius_shadow.y
#define l_radius       spotdata_radius_shadow.z
#define l_shadowid     spotdata_radius_shadow.w


struct ShadowCubeData {
	vec4 near_far_bias_exp;
};

/* convenience aliases */
#define sh_cube_near   near_far_bias_exp.x
#define sh_cube_far    near_far_bias_exp.y
#define sh_cube_bias   near_far_bias_exp.z
#define sh_cube_exp    near_far_bias_exp.w


struct ShadowMapData {
	mat4 shadowmat;
	vec4 near_far_bias;
};

/* convenience aliases */
#define sh_map_near   near_far_bias.x
#define sh_map_far    near_far_bias.y
#define sh_map_bias   near_far_bias.z

#ifndef MAX_CASCADE_NUM
#define MAX_CASCADE_NUM 4
#endif

struct ShadowCascadeData {
	mat4 shadowmat[MAX_CASCADE_NUM];
	/* arrays of float are not aligned so use vec4 */
	vec4 split_distances;
	vec4 bias;
};

/* ------- Convenience functions --------- */

vec3 mul(mat3 m, vec3 v) { return m * v; }
mat3 mul(mat3 m1, mat3 m2) { return m1 * m2; }
vec3 transform_direction(mat4 m, vec3 v) { return mat3(m) * v; }
vec3 transform_point(mat4 m, vec3 v) { return (m * vec4(v, 1.0)).xyz; }
vec3 project_point(mat4 m, vec3 v) {
	vec4 tmp = m * vec4(v, 1.0);
	return tmp.xyz / tmp.w;
}

float min_v3(vec3 v) { return min(v.x, min(v.y, v.z)); }
float max_v2(vec2 v) { return max(v.x, v.y); }

float saturate(float a) { return clamp(a, 0.0, 1.0); }
vec2 saturate(vec2 a) { return clamp(a, 0.0, 1.0); }
vec3 saturate(vec3 a) { return clamp(a, 0.0, 1.0); }
vec4 saturate(vec4 a) { return clamp(a, 0.0, 1.0); }

float distance_squared(vec2 a, vec2 b) { a -= b; return dot(a, a); }
float distance_squared(vec3 a, vec3 b) { a -= b; return dot(a, a); }
float len_squared(vec3 a) { return dot(a, a); }

float inverse_distance(vec3 V) { return max( 1 / length(V), 1e-8); }

/* ------- Fast Math ------- */

/* [Drobot2014a] Low Level Optimizations for GCN */
float fast_sqrt(float x)
{
	return intBitsToFloat(0x1fbd1df5 + (floatBitsToInt(x) >> 1));
}

/* [Eberly2014] GPGPU Programming for Games and Science */
float fast_acos(float x)
{
	float res = -0.156583 * abs(x) + M_PI_2;
	res *= fast_sqrt(1.0 - abs(x));
	return (x >= 0) ? res : M_PI - res;
}

float point_plane_projection_dist(vec3 lineorigin, vec3 planeorigin, vec3 planenormal)
{
	return dot(planenormal, planeorigin - lineorigin);
}

float line_plane_intersect_dist(vec3 lineorigin, vec3 linedirection, vec3 planeorigin, vec3 planenormal)
{
	return dot(planenormal, planeorigin - lineorigin) / dot(planenormal, linedirection);
}

float line_plane_intersect_dist(vec3 lineorigin, vec3 linedirection, vec4 plane)
{
	vec3 plane_co = plane.xyz * (-plane.w / len_squared(plane.xyz));
	vec3 h = lineorigin - plane_co;
	return -dot(plane.xyz, h) / dot(plane.xyz, linedirection);
}

vec3 line_plane_intersect(vec3 lineorigin, vec3 linedirection, vec3 planeorigin, vec3 planenormal)
{
	float dist = line_plane_intersect_dist(lineorigin, linedirection, planeorigin, planenormal);
	return lineorigin + linedirection * dist;
}

vec3 line_plane_intersect(vec3 lineorigin, vec3 linedirection, vec4 plane)
{
	float dist = line_plane_intersect_dist(lineorigin, linedirection, plane);
	return lineorigin + linedirection * dist;
}

float line_aligned_plane_intersect_dist(vec3 lineorigin, vec3 linedirection, vec3 planeorigin)
{
	/* aligned plane normal */
	vec3 L = planeorigin - lineorigin;
	float diskdist = length(L);
	vec3 planenormal = -normalize(L);
	return -diskdist / dot(planenormal, linedirection);
}

vec3 line_aligned_plane_intersect(vec3 lineorigin, vec3 linedirection, vec3 planeorigin)
{
	float dist = line_aligned_plane_intersect_dist(lineorigin, linedirection, planeorigin);
	if (dist < 0) {
		/* if intersection is behind we fake the intersection to be
		 * really far and (hopefully) not inside the radius of interest */
		dist = 1e16;
	}
	return lineorigin + linedirection * dist;
}

float line_unit_sphere_intersect_dist(vec3 lineorigin, vec3 linedirection)
{
	float a = dot(linedirection, linedirection);
	float b = dot(linedirection, lineorigin);
	float c = dot(lineorigin, lineorigin) - 1;

	float dist = 1e15;
	float determinant = b * b - a * c;
	if (determinant >= 0)
		dist = (sqrt(determinant) - b) / a;

	return dist;
}

float line_unit_box_intersect_dist(vec3 lineorigin, vec3 linedirection)
{
	/* https://seblagarde.wordpress.com/2012/09/29/image-based-lighting-approaches-and-parallax-corrected-cubemap/ */
	vec3 firstplane  = (vec3( 1.0) - lineorigin) / linedirection;
	vec3 secondplane = (vec3(-1.0) - lineorigin) / linedirection;
	vec3 furthestplane = max(firstplane, secondplane);

	return min_v3(furthestplane);
}


/* Return texture coordinates to sample Surface LUT */
vec2 lut_coords(float cosTheta, float roughness)
{
	float theta = acos(cosTheta);
	vec2 coords = vec2(roughness, theta / M_PI_2);

	/* scale and bias coordinates, for correct filtered lookup */
	return coords * (LUT_SIZE - 1.0) / LUT_SIZE + 0.5 / LUT_SIZE;
}

/* -- Tangent Space conversion -- */
vec3 tangent_to_world(vec3 vector, vec3 N, vec3 T, vec3 B)
{
	return T * vector.x + B * vector.y + N * vector.z;
}

vec3 world_to_tangent(vec3 vector, vec3 N, vec3 T, vec3 B)
{
	return vec3( dot(T, vector), dot(B, vector), dot(N, vector));
}

void make_orthonormal_basis(vec3 N, out vec3 T, out vec3 B)
{
	vec3 UpVector = abs(N.z) < 0.99999 ? vec3(0.0,0.0,1.0) : vec3(1.0,0.0,0.0);
	T = normalize( cross(UpVector, N) );
	B = cross(N, T);
}

/* ---- Opengl Depth conversion ---- */
float linear_depth(bool is_persp, float z, float zf, float zn)
{
	if (is_persp) {
		return (zn  * zf) / (z * (zn - zf) + zf);
	}
	else {
		return (z * 2.0 - 1.0) * zf;
	}
}

float buffer_depth(bool is_persp, float z, float zf, float zn)
{
	if (is_persp) {
		return (zf * (zn - z)) / (z * (zn - zf));
	}
	else {
		return (z / (zf * 2.0)) + 0.5;
	}
}

float get_view_z_from_depth(float depth)
{
	if (ProjectionMatrix[3][3] == 0.0) {
		float d = 2.0 * depth - 1.0;
		return -ProjectionMatrix[3][2] / (d + ProjectionMatrix[2][2]);
	}
	else {
		return viewvecs[0].z + depth * viewvecs[1].z;
	}
}

vec3 get_view_space_from_depth(vec2 uvcoords, float depth)
{
	if (ProjectionMatrix[3][3] == 0.0) {
		return (viewvecs[0].xyz + vec3(uvcoords, 0.0) * viewvecs[1].xyz) * get_view_z_from_depth(depth);
	}
	else {
		return viewvecs[0].xyz + vec3(uvcoords, depth) * viewvecs[1].xyz;
	}
}

vec3 get_world_space_from_depth(vec2 uvcoords, float depth)
{
	return (ViewMatrixInverse * vec4(get_view_space_from_depth(uvcoords, depth), 1.0)).xyz;
}

vec3 get_specular_dominant_dir(vec3 N, vec3 V, float roughness)
{
	vec3 R = -reflect(V, N);
	float smoothness = 1.0 - roughness;
	float fac = smoothness * (sqrt(smoothness) + roughness);
	return normalize(mix(N, R, fac));
}

float specular_occlusion(float NV, float AO, float roughness)
{
	return saturate(pow(NV + AO, roughness) - 1.0 + AO);
}

/* ---- Encode / Decode Normal buffer data ---- */
/* From http://aras-p.info/texts/CompactNormalStorage.html
 * Using Method #4: Spheremap Transform */
vec2 normal_encode(vec3 n, vec3 view)
{
    float p = sqrt(n.z * 8.0 + 8.0);
    return n.xy / p + 0.5;
}

vec3 normal_decode(vec2 enc, vec3 view)
{
    vec2 fenc = enc * 4.0 - 2.0;
    float f = dot(fenc, fenc);
    float g = sqrt(1.0 - f / 4.0);
    vec3 n;
    n.xy = fenc*g;
    n.z = 1 - f / 2;
    return n;
}

/* Fresnel */
vec3 F_schlick(vec3 f0, float cos_theta)
{
	float fac = pow(1.0 - cos_theta, 5);

	/* Unreal specular matching : if specular color is below 2% intensity,
	 * (using green channel for intensity) treat as shadowning */
	return saturate(50.0 * dot(f0, vec3(0.3, 0.6, 0.1))) * fac + (1.0 - fac) * f0;
}

/* Fresnel approximation for LTC area lights (not MRP) */
vec3 F_area(vec3 f0, vec2 lut)
{
	vec2 fac = normalize(lut.xy);

	/* Unreal specular matching : if specular color is below 2% intensity,
	 * treat as shadowning */
	return saturate(50.0 * dot(f0, vec3(0.3, 0.6, 0.1))) * fac.y + fac.x * f0;
}

/* Fresnel approximation for LTC area lights (not MRP) */
vec3 F_ibl(vec3 f0, vec2 lut)
{
	/* Unreal specular matching : if specular color is below 2% intensity,
	 * treat as shadowning */
	return saturate(50.0 * dot(f0, vec3(0.3, 0.6, 0.1))) * lut.y + lut.x * f0;
}

/* GGX */
float D_ggx_opti(float NH, float a2)
{
	float tmp = (NH * a2 - NH) * NH + 1.0;
	return M_PI * tmp*tmp; /* Doing RCP and mul a2 at the end */
}

float G1_Smith_GGX(float NX, float a2)
{
	/* Using Brian Karis approach and refactoring by NX/NX
	 * this way the (2*NL)*(2*NV) in G = G1(V) * G1(L) gets canceled by the brdf denominator 4*NL*NV
	 * Rcp is done on the whole G later
	 * Note that this is not convenient for the transmition formula */
	return NX + sqrt(NX * (NX - NX * a2) + a2);
	/* return 2 / (1 + sqrt(1 + a2 * (1 - NX*NX) / (NX*NX) ) ); /* Reference function */
}

float bsdf_ggx(vec3 N, vec3 L, vec3 V, float roughness)
{
	float a = roughness;
	float a2 = a * a;

	vec3 H = normalize(L + V);
	float NH = max(dot(N, H), 1e-8);
	float NL = max(dot(N, L), 1e-8);
	float NV = max(dot(N, V), 1e-8);

	float G = G1_Smith_GGX(NV, a2) * G1_Smith_GGX(NL, a2); /* Doing RCP at the end */
	float D = D_ggx_opti(NH, a2);

	/* Denominator is canceled by G1_Smith */
	/* bsdf = D * G / (4.0 * NL * NV); /* Reference function */
	return NL * a2 / (D * G); /* NL to Fit cycles Equation : line. 345 in bsdf_microfacet.h */
}

void accumulate_light(vec3 light, float fac, inout vec4 accum)
{
	accum += vec4(light, 1.0) * min(fac, (1.0 - accum.a));
}

/* ----------- Cone Apperture Approximation --------- */

/* Return a fitted cone angle given the input roughness */
float cone_cosine(float r)
{
	/* Using phong gloss
	 * roughness = sqrt(2/(gloss+2)) */
	float gloss = -2 + 2 / (r * r);
	/* Drobot 2014 in GPUPro5 */
	// return cos(2.0 * sqrt(2.0 / (gloss + 2)));
	/* Uludag 2014 in GPUPro5 */
	// return pow(0.244, 1 / (gloss + 1));
	/* Jimenez 2016 in Practical Realtime Strategies for Accurate Indirect Occlusion*/
	return exp2(-3.32193 * r * r);
}

/* --------- Closure ---------- */
#ifdef VOLUMETRICS

struct Closure {
	vec3 absorption;
	vec3 scatter;
	vec3 emission;
	float anisotropy;
};

#define CLOSURE_DEFAULT Closure(vec3(0.0), vec3(0.0), vec3(0.0), 0.0)

Closure closure_mix(Closure cl1, Closure cl2, float fac)
{
	Closure cl;
	cl.absorption = mix(cl1.absorption, cl2.absorption, fac);
	cl.scatter = mix(cl1.scatter, cl2.scatter, fac);
	cl.emission = mix(cl1.emission, cl2.emission, fac);
	cl.anisotropy = mix(cl1.anisotropy, cl2.anisotropy, fac);
	return cl;
}

Closure closure_add(Closure cl1, Closure cl2)
{
	Closure cl;
	cl.absorption = cl1.absorption + cl2.absorption;
	cl.scatter = cl1.scatter + cl2.scatter;
	cl.emission = cl1.emission + cl2.emission;
	cl.anisotropy = (cl1.anisotropy + cl2.anisotropy) / 2.0; /* Average phase (no multi lobe) */
	return cl;
}
#else

struct Closure {
	vec3 radiance;
	float opacity;
	vec4 ssr_data;
	vec2 ssr_normal;
	int ssr_id;
};

#define CLOSURE_DEFAULT Closure(vec3(0.0), 1.0, vec4(0.0), vec2(0.0), -1)

uniform int outputSsrId;

Closure closure_mix(Closure cl1, Closure cl2, float fac)
{
	Closure cl;
	if (cl1.ssr_id == outputSsrId) {
		cl.ssr_data = mix(cl1.ssr_data.xyzw, vec4(vec3(0.0), cl1.ssr_data.w), fac); /* do not blend roughness */
		cl.ssr_normal = cl1.ssr_normal;
		cl.ssr_id = cl1.ssr_id;
	}
	else {
		cl.ssr_data = mix(vec4(vec3(0.0), cl2.ssr_data.w), cl2.ssr_data.xyzw, fac); /* do not blend roughness */
		cl.ssr_normal = cl2.ssr_normal;
		cl.ssr_id = cl2.ssr_id;
	}
	cl.radiance = mix(cl1.radiance, cl2.radiance, fac);
	cl.opacity = mix(cl1.opacity, cl2.opacity, fac);
	return cl;
}

Closure closure_add(Closure cl1, Closure cl2)
{
	Closure cl = (cl1.ssr_id == outputSsrId) ? cl1 : cl2;
	cl.radiance = cl1.radiance + cl2.radiance;
	cl.opacity = cl1.opacity + cl2.opacity;
	return cl;
}

#if defined(MESH_SHADER) && !defined(USE_ALPHA_HASH) && !defined(USE_ALPHA_CLIP) && !defined(SHADOW_SHADER)
layout(location = 0) out vec4 fragColor;
layout(location = 1) out vec4 ssrNormals;
layout(location = 2) out vec4 ssrData;

Closure nodetree_exec(void); /* Prototype */

#define NODETREE_EXEC
void main()
{
	Closure cl = nodetree_exec();
	fragColor = vec4(cl.radiance, cl.opacity);
	ssrNormals = cl.ssr_normal.xyyy;
	ssrData = cl.ssr_data;
}

#endif /* MESH_SHADER && !SHADOW_SHADER */

#endif /* VOLUMETRICS */

Closure nodetree_exec(void); /* Prototype */

/* TODO find a better place */
#ifdef USE_MULTIPLY

out vec4 fragColor;

#define NODETREE_EXEC
void main()
{
	Closure cl = nodetree_exec();
	fragColor = vec4(mix(vec3(1.0), cl.radiance, cl.opacity), 1.0);
}
#endif