
uniform sampler2DArray shadowTexture;

layout(std140) uniform shadow_block {
	ShadowData        shadows_data[MAX_SHADOW];
	ShadowCubeData    shadows_cube_data[MAX_SHADOW_CUBE];
	ShadowCascadeData shadows_cascade_data[MAX_SHADOW_CASCADE];
};

layout(std140) uniform light_block {
	LightData lights_data[MAX_LIGHT];
};

/* type */
#define POINT    0.0
#define SUN      1.0
#define SPOT     2.0
#define HEMI     3.0
#define AREA     4.0

/* ----------------------------------------------------------- */
/* ----------------------- Shadow tests ---------------------- */
/* ----------------------------------------------------------- */

float shadow_test_esm(float z, float dist, float exponent)
{
	return saturate(exp(exponent * (z - dist)));
}

float shadow_test_pcf(float z, float dist)
{
	return step(0, z - dist);
}

float shadow_test_vsm(vec2 moments, float dist, float bias, float bleed_bias)
{
	float p = 0.0;

	if (dist <= moments.x)
		p = 1.0;

	float variance = moments.y - (moments.x * moments.x);
	variance = max(variance, bias / 10.0);

	float d = moments.x - dist;
	float p_max = variance / (variance + d * d);

	/* Now reduce light-bleeding by removing the [0, x] tail and linearly rescaling (x, 1] */
	p_max = clamp((p_max - bleed_bias) / (1.0 - bleed_bias), 0.0, 1.0);

	return max(p, p_max);
}


/* ----------------------------------------------------------- */
/* ----------------------- Shadow types ---------------------- */
/* ----------------------------------------------------------- */

float shadow_cubemap(ShadowData sd, ShadowCubeData scd, float texid, vec3 W)
{
	vec3 cubevec = W - scd.position.xyz;
	float dist = length(cubevec);

	cubevec /= dist;

#if defined(SHADOW_VSM)
	vec2 moments = texture_octahedron(shadowTexture, vec4(cubevec, texid)).rg;
#else
	float z = texture_octahedron(shadowTexture, vec4(cubevec, texid)).r;
#endif

#if defined(SHADOW_VSM)
	return shadow_test_vsm(moments, dist, sd.sh_bias, sd.sh_bleed);
#elif defined(SHADOW_ESM)
	return shadow_test_esm(z, dist - sd.sh_bias, sd.sh_exp);
#else
	return shadow_test_pcf(z, dist - sd.sh_bias);
#endif
}

float evaluate_cascade(ShadowData sd, mat4 shadowmat, vec3 W, float range, float texid)
{
	vec4 shpos = shadowmat * vec4(W, 1.0);
	float dist = shpos.z * range;

	if (shpos.z > 1.0 || shpos.z < 0.0)
		return 1.0;

#if defined(SHADOW_VSM)
	vec2 moments = texture(shadowTexture, vec3(shpos.xy, texid)).rg;
#else
	float z = texture(shadowTexture, vec3(shpos.xy, texid)).r;
#endif

#if defined(SHADOW_VSM)
	return shadow_test_vsm(moments, dist, sd.sh_bias, sd.sh_bleed);
#elif defined(SHADOW_ESM)
	return shadow_test_esm(z, dist - sd.sh_bias, sd.sh_exp);
#else
	return shadow_test_pcf(z, dist - sd.sh_bias);
#endif
}

float shadow_cascade(ShadowData sd, ShadowCascadeData scd, float texid, vec3 W)
{
	vec4 view_z = vec4(dot(W - cameraPos, cameraForward));
	vec4 weights = smoothstep(scd.split_end_distances, scd.split_start_distances.yzwx, view_z);
	weights.yzw -= weights.xyz;

	vec4 vis = vec4(1.0);
	float range = abs(sd.sh_far - sd.sh_near); /* Same factor as in get_cascade_world_distance(). */
	if (weights.x > 0.0) {
		vis.x = evaluate_cascade(sd, scd.shadowmat[0], W, range, texid + 0);
	}
	if (weights.y > 0.0) {
		vis.y = evaluate_cascade(sd, scd.shadowmat[1], W, range, texid + 1);
	}
	if (weights.z > 0.0) {
		vis.z = evaluate_cascade(sd, scd.shadowmat[2], W, range, texid + 2);
	}
	if (weights.w > 0.0) {
		vis.w = evaluate_cascade(sd, scd.shadowmat[3], W, range, texid + 3);
	}

	float weight_sum = dot(vec4(1.0), weights);
	if (weight_sum > 0.9999) {
		float vis_sum = dot(vec4(1.0), vis * weights);
		return vis_sum / weight_sum;
	}
	else {
		float vis_sum = dot(vec4(1.0), vis * step(0.001, weights));
		return mix(1.0, vis_sum, weight_sum);
	}
}

/* ----------------------------------------------------------- */
/* --------------------- Light Functions --------------------- */
/* ----------------------------------------------------------- */
#define MAX_MULTI_SHADOW 4

float light_visibility(LightData ld, vec3 W, vec4 l_vector)
{
	float vis = 1.0;

	if (ld.l_type == SPOT) {
		float z = dot(ld.l_forward, l_vector.xyz);
		vec3 lL = l_vector.xyz / z;
		float x = dot(ld.l_right, lL) / ld.l_sizex;
		float y = dot(ld.l_up, lL) / ld.l_sizey;

		float ellipse = 1.0 / sqrt(1.0 + x * x + y * y);

		float spotmask = smoothstep(0.0, 1.0, (ellipse - ld.l_spot_size) / ld.l_spot_blend);

		vis *= spotmask;
		vis *= step(0.0, -dot(l_vector.xyz, ld.l_forward));
	}
	else if (ld.l_type == AREA) {
		vis *= step(0.0, -dot(l_vector.xyz, ld.l_forward));
	}

#if !defined(VOLUMETRICS) || defined(VOLUME_SHADOW)
	/* shadowing */
	if (ld.l_shadowid >= 0.0) {
		ShadowData data = shadows_data[int(ld.l_shadowid)];
		if (ld.l_type == SUN) {
			/* TODO : MSM */
			// for (int i = 0; i < MAX_MULTI_SHADOW; ++i) {
				vis *= shadow_cascade(
					data, shadows_cascade_data[int(data.sh_data_start)],
					data.sh_tex_start, W);
			// }
		}
		else {
			/* TODO : MSM */
			// for (int i = 0; i < MAX_MULTI_SHADOW; ++i) {
				vis *= shadow_cubemap(
					data, shadows_cube_data[int(data.sh_data_start)],
					data.sh_tex_start, W);
			// }
		}
	}
#endif

	return vis;
}

float light_diffuse(LightData ld, vec3 N, vec3 V, vec4 l_vector)
{
#ifdef USE_LTC
	if (ld.l_type == SUN) {
		/* TODO disk area light */
		return direct_diffuse_sun(ld, N);
	}
	else if (ld.l_type == AREA) {
		return direct_diffuse_rectangle(ld, N, V, l_vector);
	}
	else {
		return direct_diffuse_sphere(ld, N, l_vector);
	}
#else
	if (ld.l_type == SUN) {
		return direct_diffuse_sun(ld, N, V);
	}
	else {
		return direct_diffuse_point(N, l_vector);
	}
#endif
}

vec3 light_specular(LightData ld, vec3 N, vec3 V, vec4 l_vector, float roughness, vec3 f0)
{
#ifdef USE_LTC
	if (ld.l_type == SUN) {
		/* TODO disk area light */
		return direct_ggx_sun(ld, N, V, roughness, f0);
	}
	else if (ld.l_type == AREA) {
		return direct_ggx_rectangle(ld, N, V, l_vector, roughness, f0);
	}
	else {
		return direct_ggx_sphere(ld, N, V, l_vector, roughness, f0);
	}
#else
	if (ld.l_type == SUN) {
		return direct_ggx_sun(ld, N, V, roughness, f0);
	}
	else {
		return direct_ggx_point(N, V, l_vector, roughness, f0);
	}
#endif
}

#ifdef HAIR_SHADER
void light_hair_common(
        LightData ld, vec3 N, vec3 V, vec4 l_vector, vec3 norm_view,
        out float occlu_trans, out float occlu,
        out vec3 norm_lamp, out vec3 view_vec)
{
	const float transmission = 0.3; /* Uniform internal scattering factor */

	vec3 lamp_vec;

	if (ld.l_type == SUN || ld.l_type == AREA) {
		lamp_vec = ld.l_forward;
	}
	else {
		lamp_vec = -l_vector.xyz;
	}

	norm_lamp = cross(lamp_vec, N);
	norm_lamp = normalize(cross(N, norm_lamp)); /* Normal facing lamp */

	/* Rotate view vector onto the cross(tangent, light) plane */
	view_vec = normalize(norm_lamp * dot(norm_view, V) + N * dot(N, V));

	occlu = (dot(norm_view, norm_lamp) * 0.5 + 0.5);
	occlu_trans = transmission + (occlu * (1.0 - transmission)); /* Includes transmission component */
}
#endif
