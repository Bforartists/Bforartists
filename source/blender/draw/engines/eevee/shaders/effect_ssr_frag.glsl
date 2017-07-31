
/* Based on Stochastic Screen Space Reflections
 * https://www.ea.com/frostbite/news/stochastic-screen-space-reflections */

#ifndef UTIL_TEX
#define UTIL_TEX
uniform sampler2DArray utilTex;
#endif /* UTIL_TEX */

uniform int rayCount;
uniform float maxRoughness;

#define BRDF_BIAS 0.7

vec3 generate_ray(vec3 V, vec3 N, float a2, vec3 rand, out float pdf)
{
	float NH;
	vec3 T, B;
	make_orthonormal_basis(N, T, B); /* Generate tangent space */

	/* Importance sampling bias */
	rand.x = mix(rand.x, 0.0, BRDF_BIAS);

	/* TODO distribution of visible normals */
	vec3 H = sample_ggx(rand, a2, N, T, B, NH); /* Microfacet normal */
	pdf = min(1024e32, pdf_ggx_reflect(NH, a2)); /* Theoretical limit of 16bit float */
	return reflect(-V, H);
}

#define MAX_MIP 9.0

#ifdef STEP_RAYTRACE

uniform sampler2D normalBuffer;
uniform sampler2D specroughBuffer;

uniform int planar_count;

layout(location = 0) out vec4 hitData0;
layout(location = 1) out vec4 hitData1;
layout(location = 2) out vec4 hitData2;
layout(location = 3) out vec4 hitData3;

bool has_hit_backface(vec3 hit_pos, vec3 R, vec3 V)
{
	vec2 hit_co = project_point(ProjectionMatrix, hit_pos).xy * 0.5 + 0.5;
	vec3 hit_N = normal_decode(textureLod(normalBuffer, hit_co, 0.0).rg, V);
	return (dot(-R, hit_N) < 0.0);
}

vec4 do_planar_ssr(int index, vec3 V, vec3 N, vec3 planeNormal, vec3 viewPosition, float a2, vec3 rand, float ray_nbr)
{
	float pdf;
	vec3 R = generate_ray(V, N, a2, rand, pdf);

	R = reflect(R, planeNormal);
	pdf *= -1.0; /* Tag as planar ray. */

	/* If ray is bad (i.e. going below the plane) do not trace. */
	if (dot(R, planeNormal) > 0.0) {
		vec3 R = generate_ray(V, N, a2, rand * vec3(1.0, -1.0, -1.0), pdf);
	}

	vec3 hit_pos;
	if (abs(dot(-R, V)) < 0.9999) {
		/* Since viewspace hit position can land behind the camera in this case,
		 * we save the reflected view position (visualize it as the hit position
		 * below the reflection plane). This way it's garanted that the hit will
		 * be in front of the camera. That let us tag the bad rays with a negative
		 * sign in the Z component. */
		hit_pos = raycast(index, viewPosition, R, fract(rand.x + (ray_nbr / float(rayCount))), a2);
	}
	else {
		vec2 uvs = project_point(ProjectionMatrix, viewPosition).xy * 0.5 + 0.5;
		float raw_depth = textureLod(planarDepth, vec3(uvs, float(index)), 0.0).r;
		hit_pos = get_view_space_from_depth(uvs, raw_depth);
		hit_pos.z *= (raw_depth < 1.0) ? 1.0 : -1.0;
	}

	return vec4(hit_pos, pdf);
}

vec4 do_ssr(vec3 V, vec3 N, vec3 viewPosition, float a2, vec3 rand, float ray_nbr)
{
	float pdf;
	vec3 R = generate_ray(V, N, a2, rand, pdf);

	vec3 hit_pos = raycast(-1, viewPosition, R, fract(rand.x + (ray_nbr / float(rayCount))), a2);

	return vec4(hit_pos, pdf);
}

void main()
{
#ifdef FULLRES
	ivec2 fullres_texel = ivec2(gl_FragCoord.xy);
	ivec2 halfres_texel = fullres_texel;
#else
	ivec2 fullres_texel = ivec2(gl_FragCoord.xy) * 2;
	ivec2 halfres_texel = ivec2(gl_FragCoord.xy);
#endif

	float depth = texelFetch(depthBuffer, fullres_texel, 0).r;

	/* Early out */
	if (depth == 1.0)
		discard;

	vec2 uvs = gl_FragCoord.xy / vec2(textureSize(depthBuffer, 0));
#ifndef FULLRES
	uvs *= 2.0;
#endif

	/* Using view space */
	vec3 viewPosition = get_view_space_from_depth(uvs, depth);
	vec3 V = viewCameraVec;
	vec3 N = normal_decode(texelFetch(normalBuffer, fullres_texel, 0).rg, V);

	/* Retrieve pixel data */
	vec4 speccol_roughness = texelFetch(specroughBuffer, fullres_texel, 0).rgba;

	/* Early out */
	if (dot(speccol_roughness.rgb, vec3(1.0)) == 0.0)
		discard;


	float roughness = speccol_roughness.a;
	float roughnessSquared = max(1e-3, roughness * roughness);
	float a2 = roughnessSquared * roughnessSquared;

	if (roughness > maxRoughness + 0.2) {
		hitData0 = hitData1 = hitData2 = hitData3 = vec4(0.0);
		return;
	}

	vec3 rand = texelFetch(utilTex, ivec3(halfres_texel % LUT_SIZE, 2), 0).rba;

	vec3 worldPosition = transform_point(ViewMatrixInverse, viewPosition);
	vec3 wN = transform_direction(ViewMatrixInverse, N);

	/* Planar Reflections */
	for (int i = 0; i < MAX_PLANAR && i < planar_count; ++i) {
		PlanarData pd = planars_data[i];

		float fade = probe_attenuation_planar(pd, worldPosition, wN, 0.0);

		if (fade > 0.5) {
			/* Find view vector / reflection plane intersection. */
			/* TODO optimize, use view space for all. */
			vec3 tracePosition = line_plane_intersect(worldPosition, cameraVec, pd.pl_plane_eq);
			tracePosition = transform_point(ViewMatrix, tracePosition);
			vec3 planeNormal = transform_direction(ViewMatrix, pd.pl_normal);

			/* TODO : Raytrace together if textureGather is supported. */
			hitData0 = do_planar_ssr(i, V, N, planeNormal, tracePosition, a2, rand, 0.0);
			if (rayCount > 1) hitData1 = do_planar_ssr(i, V, N, planeNormal, tracePosition, a2, rand.xyz * vec3(1.0, -1.0, -1.0), 1.0);
			if (rayCount > 2) hitData2 = do_planar_ssr(i, V, N, planeNormal, tracePosition, a2, rand.xzy * vec3(1.0,  1.0, -1.0), 2.0);
			if (rayCount > 3) hitData3 = do_planar_ssr(i, V, N, planeNormal, tracePosition, a2, rand.xzy * vec3(1.0, -1.0,  1.0), 3.0);
			return;
		}
	}

	/* TODO : Raytrace together if textureGather is supported. */
	hitData0 = do_ssr(V, N, viewPosition, a2, rand, 0.0);
	if (rayCount > 1) hitData1 = do_ssr(V, N, viewPosition, a2, rand.xyz * vec3(1.0, -1.0, -1.0), 1.0);
	if (rayCount > 2) hitData2 = do_ssr(V, N, viewPosition, a2, rand.xzy * vec3(1.0,  1.0, -1.0), 2.0);
	if (rayCount > 3) hitData3 = do_ssr(V, N, viewPosition, a2, rand.xzy * vec3(1.0, -1.0,  1.0), 3.0);
}

#else /* STEP_RESOLVE */

uniform sampler2D colorBuffer; /* previous frame */
uniform sampler2D normalBuffer;
uniform sampler2D specroughBuffer;

uniform sampler2D hitBuffer0;
uniform sampler2D hitBuffer1;
uniform sampler2D hitBuffer2;
uniform sampler2D hitBuffer3;

uniform int probe_count;
uniform int planar_count;

uniform float borderFadeFactor;
uniform float fireflyFactor;

uniform mat4 PastViewProjectionMatrix;

out vec4 fragColor;

void fallback_cubemap(vec3 N, vec3 V, vec3 W, float roughness, float roughnessSquared, inout vec4 spec_accum)
{
	/* Specular probes */
	vec3 spec_dir = get_specular_dominant_dir(N, V, roughnessSquared);

	/* Starts at 1 because 0 is world probe */
	for (int i = 1; i < MAX_PROBE && i < probe_count && spec_accum.a < 0.999; ++i) {
		CubeData cd = probes_data[i];

		float fade = probe_attenuation_cube(cd, W);

		if (fade > 0.0) {
			vec3 spec = probe_evaluate_cube(float(i), cd, W, spec_dir, roughness);
			accumulate_light(spec, fade, spec_accum);
		}
	}

	/* World Specular */
	if (spec_accum.a < 0.999) {
		vec3 spec = probe_evaluate_world_spec(spec_dir, roughness);
		accumulate_light(spec, 1.0, spec_accum);
	}
}

#if 0 /* Finish reprojection with motion vectors */
vec3 get_motion_vector(vec3 pos)
{
}

/* http://bitsquid.blogspot.fr/2017/06/reprojecting-reflections_22.html */
vec3 find_reflection_incident_point(vec3 cam, vec3 hit, vec3 pos, vec3 N)
{
	float d_cam = point_plane_projection_dist(cam, pos, N);
	float d_hit = point_plane_projection_dist(hit, pos, N);

	if (d_hit < d_cam) {
		/* Swap */
		float tmp = d_cam;
		d_cam = d_hit;
		d_hit = tmp;
	}

	vec3 proj_cam = cam - (N * d_cam);
	vec3 proj_hit = hit - (N * d_hit);

	return (proj_hit - proj_cam) * d_cam / (d_cam + d_hit) + proj_cam;
}
#endif

float brightness(vec3 c)
{
	return max(max(c.r, c.g), c.b);
}

float screen_border_mask(vec2 hit_co)
{
	const float margin = 0.003;
	float atten = borderFadeFactor + margin; /* Screen percentage */
	hit_co = smoothstep(margin, atten, hit_co) * (1 - smoothstep(1.0 - atten, 1.0 - margin, hit_co));

	float screenfade = hit_co.x * hit_co.y;

	return screenfade;
}

vec2 get_reprojected_reflection(vec3 hit, vec3 pos, vec3 N)
{
	/* TODO real reprojection with motion vectors, etc... */
	return project_point(PastViewProjectionMatrix, hit).xy * 0.5 + 0.5;
}

vec4 get_ssr_sample(
        sampler2D hitBuffer, PlanarData pd, float planar_index, vec3 worldPosition, vec3 N, vec3 V, float roughnessSquared,
        float cone_tan, vec2 source_uvs, vec2 texture_size, ivec2 target_texel,
        inout float weight_acc)
{
	vec4 hit_co_pdf = texelFetch(hitBuffer, target_texel, 0).rgba;
	bool has_hit = (hit_co_pdf.z < 0.0);
	bool is_planar = (hit_co_pdf.w < 0.0);
	hit_co_pdf.z = -abs(hit_co_pdf.z);
	hit_co_pdf.w = abs(hit_co_pdf.w);

	/* Hit position in world space. */
	vec3 hit_pos = transform_point(ViewMatrixInverse, hit_co_pdf.xyz);

	vec2 ref_uvs;
	vec3 L;
	float mask = 1.0;
	float cone_footprint;
	if (is_planar) {
		/* Reflect back the hit position to have it in non-reflected world space */
		vec3 trace_pos = line_plane_intersect(worldPosition, V, pd.pl_plane_eq);
		vec3 hit_vec = hit_pos - trace_pos;
		hit_vec = reflect(hit_vec, pd.pl_normal);
		hit_pos = hit_vec + trace_pos;
		L = normalize(hit_vec);
		ref_uvs = project_point(ProjectionMatrix, hit_co_pdf.xyz).xy * 0.5 + 0.5;
		vec2 uvs = gl_FragCoord.xy / texture_size;

		/* Compute cone footprint in screen space. */
		float homcoord = ProjectionMatrix[2][3] * hit_co_pdf.z + ProjectionMatrix[3][3];
		cone_footprint = length(hit_vec) * cone_tan * ProjectionMatrix[0][0] / homcoord;
	}
	else {
		/* Find hit position in previous frame. */
		ref_uvs = get_reprojected_reflection(hit_pos, worldPosition, N);
		L = normalize(hit_pos - worldPosition);
		vec2 uvs = gl_FragCoord.xy / vec2(textureSize(depthBuffer, 0));
		mask *= screen_border_mask(uvs);

		/* Compute cone footprint Using UV distance because we are using screen space filtering. */
		cone_footprint = cone_tan * distance(ref_uvs, source_uvs);
	}
	mask = min(mask, screen_border_mask(ref_uvs));
	mask *= float(has_hit);

	/* Estimate a cone footprint to sample a corresponding mipmap level. */
	float mip = BRDF_BIAS * clamp(log2(cone_footprint * max(texture_size.x, texture_size.y)), 0.0, MAX_MIP) - 1.0;

	/* Slide 54 */
	float bsdf = bsdf_ggx(N, L, V, roughnessSquared);
	float weight = step(1e-8, hit_co_pdf.w) * bsdf / max(1e-8, hit_co_pdf.w);
	weight_acc += weight;

	vec3 sample;
	if (is_planar) {
		sample = textureLod(probePlanars, vec3(ref_uvs, planar_index), mip).rgb;
	}
	else {
		sample = textureLod(colorBuffer, ref_uvs, mip).rgb;
	}

	/* Clamped brightness. */
	float luma = max(1e-8, brightness(sample));
	sample *= 1.0 - max(0.0, luma - fireflyFactor) / luma;

	/* Do not add light if ray has failed. */
	sample *= float(has_hit);

	return vec4(sample, mask) * weight;
}

#define NUM_NEIGHBORS 4

void main()
{
	ivec2 fullres_texel = ivec2(gl_FragCoord.xy);
#ifdef FULLRES
	ivec2 halfres_texel = fullres_texel;
#else
	ivec2 halfres_texel = ivec2(gl_FragCoord.xy / 2.0);
#endif
	vec2 texture_size = vec2(textureSize(depthBuffer, 0));
	vec2 uvs = gl_FragCoord.xy / texture_size;
	vec3 rand = texelFetch(utilTex, ivec3(fullres_texel % LUT_SIZE, 2), 0).rba;

	float depth = textureLod(depthBuffer, uvs, 0.0).r;

	/* Early out */
	if (depth == 1.0)
		discard;

	/* Using world space */
	vec3 viewPosition = get_view_space_from_depth(uvs, depth); /* Needed for viewCameraVec */
	vec3 worldPosition = transform_point(ViewMatrixInverse, viewPosition);
	vec3 V = cameraVec;
	vec3 vN = normal_decode(texelFetch(normalBuffer, fullres_texel, 0).rg, viewCameraVec);
	vec3 N = transform_direction(ViewMatrixInverse, vN);
	vec4 speccol_roughness = texelFetch(specroughBuffer, fullres_texel, 0).rgba;

	/* Early out */
	if (dot(speccol_roughness.rgb, vec3(1.0)) == 0.0)
		discard;

	/* Find Planar Reflections affecting this pixel */
	PlanarData pd;
	float planar_index;
	for (int i = 0; i < MAX_PLANAR && i < planar_count; ++i) {
		pd = planars_data[i];

		float fade = probe_attenuation_planar(pd, worldPosition, N, 0.0);

		if (fade > 0.5) {
			planar_index = float(i);
			break;
		}
	}

	float roughness = speccol_roughness.a;
	float roughnessSquared = max(1e-3, roughness * roughness);

	vec4 spec_accum = vec4(0.0);

	/* Resolve SSR */
	float cone_cos = cone_cosine(roughnessSquared);
	float cone_tan = sqrt(1 - cone_cos * cone_cos) / cone_cos;
	cone_tan *= mix(saturate(dot(N, V) * 2.0), 1.0, roughness); /* Elongation fit */

	vec2 source_uvs = project_point(PastViewProjectionMatrix, worldPosition).xy * 0.5 + 0.5;

	vec4 ssr_accum = vec4(0.0);
	float weight_acc = 0.0;
	const ivec2 neighbors[9] = ivec2[9](
		ivec2(0, 0),

		               ivec2(0,  1),
		ivec2(-1, -1),               ivec2(1, -1),

		ivec2(-1,  1),               ivec2(1,  1),
		               ivec2(0, -1),

		ivec2(-1,  0),               ivec2(1,  0)
	);
	ivec2 invert_neighbor;
	invert_neighbor.x = ((fullres_texel.x & 0x1) == 0) ? 1 : -1;
	invert_neighbor.y = ((fullres_texel.y & 0x1) == 0) ? 1 : -1;

	if (roughness < maxRoughness + 0.2) {
		for (int i = 0; i < NUM_NEIGHBORS; i++) {
			ivec2 target_texel = halfres_texel + neighbors[i] * invert_neighbor;

			ssr_accum += get_ssr_sample(hitBuffer0, pd, planar_index, worldPosition, N, V,
			                            roughnessSquared, cone_tan, source_uvs,
			                            texture_size, target_texel, weight_acc);
			if (rayCount > 1) {
				ssr_accum += get_ssr_sample(hitBuffer1, pd, planar_index, worldPosition, N, V,
				                            roughnessSquared, cone_tan, source_uvs,
				                            texture_size, target_texel, weight_acc);
			}
			if (rayCount > 2) {
				ssr_accum += get_ssr_sample(hitBuffer2, pd, planar_index, worldPosition, N, V,
				                            roughnessSquared, cone_tan, source_uvs,
				                            texture_size, target_texel, weight_acc);
			}
			if (rayCount > 3) {
				ssr_accum += get_ssr_sample(hitBuffer3, pd, planar_index, worldPosition, N, V,
				                            roughnessSquared, cone_tan, source_uvs,
				                            texture_size, target_texel, weight_acc);
			}
		}
	}

	/* Compute SSR contribution */
	if (weight_acc > 0.0) {
		ssr_accum /= weight_acc;
		/* fade between 0.5 and 1.0 roughness */
		ssr_accum.a *= smoothstep(maxRoughness + 0.2, maxRoughness, roughness); 
		accumulate_light(ssr_accum.rgb, ssr_accum.a, spec_accum);
	}

	/* If SSR contribution is not 1.0, blend with cubemaps */
	if (spec_accum.a < 1.0) {
		fallback_cubemap(N, V, worldPosition, roughness, roughnessSquared, spec_accum);
	}

	fragColor = vec4(spec_accum.rgb * speccol_roughness.rgb, 1.0);
}

#endif
