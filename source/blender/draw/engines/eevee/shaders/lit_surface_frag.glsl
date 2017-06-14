
uniform int light_count;
uniform int probe_count;
uniform mat4 ProjectionMatrix;
uniform mat4 ViewMatrixInverse;

uniform sampler2DArray probeCubes;
uniform float lodMax;
uniform vec3 shCoefs[9];

#ifndef UTIL_TEX
#define UTIL_TEX
uniform sampler2DArray utilTex;
#endif /* UTIL_TEX */

uniform sampler2DArray shadowCubes;
uniform sampler2DArrayShadow shadowCascades;

layout(std140) uniform probe_block {
	ProbeData probes_data[MAX_PROBE];
};

layout(std140) uniform light_block {
	LightData lights_data[MAX_LIGHT];
};

layout(std140) uniform shadow_block {
	ShadowCubeData    shadows_cube_data[MAX_SHADOW_CUBE];
	ShadowMapData     shadows_map_data[MAX_SHADOW_MAP];
	ShadowCascadeData shadows_cascade_data[MAX_SHADOW_CASCADE];
};

in vec3 worldPosition;
in vec3 viewPosition;

#ifdef USE_FLAT_NORMAL
flat in vec3 worldNormal;
flat in vec3 viewNormal;
#else
in vec3 worldNormal;
in vec3 viewNormal;
#endif

#define cameraForward   normalize(ViewMatrixInverse[2].xyz)
#define cameraPos       ViewMatrixInverse[3].xyz

/* type */
#define POINT    0.0
#define SUN      1.0
#define SPOT     2.0
#define HEMI     3.0
#define AREA     4.0

vec2 mapping_octahedron(vec3 cubevec, vec2 texel_size)
{
	/* projection onto octahedron */
	cubevec /= dot( vec3(1), abs(cubevec) );

	/* out-folding of the downward faces */
	if ( cubevec.z < 0.0 ) {
		cubevec.xy = (1.0 - abs(cubevec.yx)) * sign(cubevec.xy);
	}

	/* mapping to [0;1]ˆ2 texture space */
	vec2 uvs = cubevec.xy * (0.5) + 0.5;

	/* edge filtering fix */
	uvs *= 1.0 - 2.0 * texel_size;
	uvs += texel_size;

	return uvs;
}

vec4 textureLod_octahedron(sampler2DArray tex, vec4 cubevec, float lod)
{
	vec2 texelSize = 1.0 / vec2(textureSize(tex, int(lodMax)));

	vec2 uvs = mapping_octahedron(cubevec.xyz, texelSize);

	return textureLod(tex, vec3(uvs, cubevec.w), lod);
}

vec4 texture_octahedron(sampler2DArray tex, vec4 cubevec)
{
	vec2 texelSize = 1.0 / vec2(textureSize(tex, 0));

	vec2 uvs = mapping_octahedron(cubevec.xyz, texelSize);

	return texture(tex, vec3(uvs, cubevec.w));
}
#ifdef HAIR_SHADER
vec3 light_diffuse(LightData ld, ShadingData sd, vec3 albedo)
{
       if (ld.l_type == SUN) {
               return direct_diffuse_sun(ld, sd) * albedo;
       }
       else if (ld.l_type == AREA) {
               return direct_diffuse_rectangle(ld, sd) * albedo;
       }
       else {
               return direct_diffuse_sphere(ld, sd) * albedo;
       }
}

vec3 light_specular(LightData ld, ShadingData sd, float roughness, vec3 f0)
{
       if (ld.l_type == SUN) {
               return direct_ggx_sun(ld, sd, roughness, f0);
       }
       else if (ld.l_type == AREA) {
               return direct_ggx_rectangle(ld, sd, roughness, f0);
       }
       else {
               return direct_ggx_sphere(ld, sd, roughness, f0);
       }
}

void light_shade(
        LightData ld, ShadingData sd, vec3 albedo, float roughness, vec3 f0,
        out vec3 diffuse, out vec3 specular)
{
       const float transmission = 0.3; /* Uniform internal scattering factor */
       ShadingData sd_new = sd;

       vec3 lamp_vec;

      if (ld.l_type == SUN || ld.l_type == AREA) {
               lamp_vec = ld.l_forward;
       }
       else {
               lamp_vec = -sd.l_vector;
       }

       vec3 norm_view = cross(sd.V, sd.N);
       norm_view = normalize(cross(norm_view, sd.N)); /* Normal facing view */

       vec3 norm_lamp = cross(lamp_vec, sd.N);
       norm_lamp = normalize(cross(sd.N, norm_lamp)); /* Normal facing lamp */

       /* Rotate view vector onto the cross(tangent, light) plane */
       vec3 view_vec = normalize(norm_lamp * dot(norm_view, sd.V) + sd.N * dot(sd.N, sd.V));

       float occlusion = (dot(norm_view, norm_lamp) * 0.5 + 0.5);
       float occltrans = transmission + (occlusion * (1.0 - transmission)); /* Includes transmission component */

       sd_new.N = -norm_lamp;

       diffuse = light_diffuse(ld, sd_new, albedo) * occltrans;

       sd_new.V = view_vec;

       specular = light_specular(ld, sd_new, roughness, f0) * occlusion;
}
#else
void light_shade(
        LightData ld, ShadingData sd, vec3 albedo, float roughness, vec3 f0,
        out vec3 diffuse, out vec3 specular)
{
#ifdef USE_LTC
	if (ld.l_type == SUN) {
		/* TODO disk area light */
		diffuse = direct_diffuse_sun(ld, sd) * albedo;
		specular = direct_ggx_sun(ld, sd, roughness, f0);
	}
	else if (ld.l_type == AREA) {
		diffuse =  direct_diffuse_rectangle(ld, sd) * albedo;
		specular =  direct_ggx_rectangle(ld, sd, roughness, f0);
	}
	else {
		diffuse =  direct_diffuse_sphere(ld, sd) * albedo;
		specular =  direct_ggx_sphere(ld, sd, roughness, f0);
	}
#else
	if (ld.l_type == SUN) {
		diffuse = direct_diffuse_sun(ld, sd) * albedo;
		specular = direct_ggx_sun(ld, sd, roughness, f0);
	}
	else {
		diffuse = direct_diffuse_point(ld, sd) * albedo;
		specular = direct_ggx_point(sd, roughness, f0);
	}
#endif
}
#endif

void light_visibility(LightData ld, ShadingData sd, out float vis)
{
	vis = 1.0;

	if (ld.l_type == SPOT) {
		float z = dot(ld.l_forward, sd.l_vector);
		vec3 lL = sd.l_vector / z;
		float x = dot(ld.l_right, lL) / ld.l_sizex;
		float y = dot(ld.l_up, lL) / ld.l_sizey;

		float ellipse = 1.0 / sqrt(1.0 + x * x + y * y);

		float spotmask = smoothstep(0.0, 1.0, (ellipse - ld.l_spot_size) / ld.l_spot_blend);

		vis *= spotmask;
		vis *= step(0.0, -dot(sd.l_vector, ld.l_forward));
	}
	else if (ld.l_type == AREA) {
		vis *= step(0.0, -dot(sd.l_vector, ld.l_forward));
	}

	/* shadowing */
	if (ld.l_shadowid >= (MAX_SHADOW_MAP + MAX_SHADOW_CUBE)) {
		/* Shadow Cascade */
		float shid = ld.l_shadowid - (MAX_SHADOW_CUBE + MAX_SHADOW_MAP);
		ShadowCascadeData smd = shadows_cascade_data[int(shid)];

		/* Finding Cascade index */
		vec4 z = vec4(-dot(cameraPos - worldPosition, cameraForward));
		vec4 comp = step(z, smd.split_distances);
		float cascade = dot(comp, comp);
		mat4 shadowmat;
		float bias;

		/* Manual Unrolling of a loop for better performance.
		 * Doing fetch directly with cascade index leads to
		 * major performance impact. (0.27ms -> 10.0ms for 1 light) */
		if (cascade == 0.0) {
			shadowmat = smd.shadowmat[0];
			bias = smd.bias[0];
		}
		else if (cascade == 1.0) {
			shadowmat = smd.shadowmat[1];
			bias = smd.bias[1];
		}
		else if (cascade == 2.0) {
			shadowmat = smd.shadowmat[2];
			bias = smd.bias[2];
		}
		else {
			shadowmat = smd.shadowmat[3];
			bias = smd.bias[3];
		}

		vec4 shpos = shadowmat * vec4(sd.W, 1.0);
		shpos.z -= bias * shpos.w;
		shpos.xyz /= shpos.w;

		vis *= texture(shadowCascades, vec4(shpos.xy, shid * float(MAX_CASCADE_NUM) + cascade, shpos.z));
	}
	else if (ld.l_shadowid >= 0.0) {
		/* Shadow Cube */
		float shid = ld.l_shadowid;
		ShadowCubeData scd = shadows_cube_data[int(shid)];

		vec3 cubevec = sd.W - ld.l_position;
		float dist = length(cubevec) - scd.sh_cube_bias;

		float z = texture_octahedron(shadowCubes, vec4(cubevec, shid)).r;

		float esm_test = saturate(exp(scd.sh_cube_exp * (z - dist)));
		float sh_test = step(0, z - dist);

		vis *= esm_test;
	}
}

vec3 probe_parallax_correction(vec3 W, vec3 spec_dir, ProbeData pd, inout float roughness)
{
	vec3 localpos = (pd.parallaxmat * vec4(W, 1.0)).xyz;
	vec3 localray = (pd.parallaxmat * vec4(spec_dir, 0.0)).xyz;

	float dist;
	if (pd.p_parallax_type == PROBE_PARALLAX_BOX) {
		dist = line_unit_box_intersect_dist(localpos, localray);
	}
	else {
		dist = line_unit_sphere_intersect_dist(localpos, localray);
	}

	/* Use Distance in WS directly to recover intersection */
	vec3 intersection = W + spec_dir * dist - pd.p_position;

	/* From Frostbite PBR Course
	 * Distance based roughness
	 * http://www.frostbite.com/wp-content/uploads/2014/11/course_notes_moving_frostbite_to_pbr.pdf */
	float original_roughness = roughness;
	float linear_roughness = sqrt(roughness);
	float distance_roughness = saturate(dist * linear_roughness / length(intersection));
	linear_roughness = mix(distance_roughness, linear_roughness, linear_roughness);
	roughness = linear_roughness * linear_roughness;

	float fac = saturate(original_roughness * 2.0 - 1.0);
	return mix(intersection, spec_dir, fac * fac);
}

float probe_attenuation(vec3 W, ProbeData pd)
{
	vec3 localpos = (pd.influencemat * vec4(W, 1.0)).xyz;

	float fac;
	if (pd.p_atten_type == PROBE_ATTENUATION_BOX) {
		vec3 axes_fac = saturate(pd.p_atten_fac - pd.p_atten_fac * abs(localpos));
		fac = min_v3(axes_fac);
	}
	else {
		fac = saturate(pd.p_atten_fac - pd.p_atten_fac * length(localpos));
	}

	return fac;
}

vec3 eevee_surface_lit(vec3 world_normal, vec3 albedo, vec3 f0, float roughness, float ao)
{
	roughness = clamp(roughness, 1e-8, 0.9999);
	float roughnessSquared = roughness * roughness;

	ShadingData sd;
	sd.N = normalize(world_normal);
	sd.V = (ProjectionMatrix[3][3] == 0.0) /* if perspective */
	            ? normalize(cameraPos - worldPosition)
	            : cameraForward;
	sd.W = worldPosition;

	vec3 radiance = vec3(0.0);

#ifdef HAIR_SHADER
       /* View facing normal */
       vec3 norm_view = cross(sd.V, sd.N);
       norm_view = normalize(cross(norm_view, sd.N)); /* Normal facing view */
#endif


	/* Analitic Lights */
	for (int i = 0; i < MAX_LIGHT && i < light_count; ++i) {
		LightData ld = lights_data[i];
		vec3 diff, spec;
		float vis = 1.0;

		sd.l_vector = ld.l_position - worldPosition;

#ifndef HAIR_SHADER
		light_visibility(ld, sd, vis);
#endif
		light_shade(ld, sd, albedo, roughnessSquared, f0, diff, spec);

		radiance += vis * (diff + spec) * ld.l_color;
	}

#ifdef HAIR_SHADER
	sd.N = -norm_view;
#endif

	/* Envmaps */
	vec3 R = reflect(-sd.V, sd.N);
	vec3 spec_dir = get_specular_dominant_dir(sd.N, R, roughnessSquared);
	vec2 uv = lut_coords(dot(sd.N, sd.V), roughness);
	vec2 brdf_lut = texture(utilTex, vec3(uv, 1.0)).rg;

	vec4 spec_accum = vec4(0.0);
	vec4 diff_accum = vec4(0.0);

	/* Specular probes */
	/* Start at 1 because 0 is world probe */
	for (int i = 1; i < MAX_PROBE && i < probe_count; ++i) {
		ProbeData pd = probes_data[i];

		float dist_attenuation = probe_attenuation(sd.W, pd);

		if (dist_attenuation > 0.0) {
			float roughness_copy = roughness;

			vec3 sample_vec = probe_parallax_correction(sd.W, spec_dir, pd, roughness_copy);
			vec4 sample = textureLod_octahedron(probeCubes, vec4(sample_vec, i), roughness_copy * lodMax).rgba;

			float influ_spec = min(dist_attenuation, (1.0 - spec_accum.a));

			spec_accum.rgb += sample.rgb * influ_spec;
			spec_accum.a += influ_spec;
		}
	}

	/* World probe */
	if (spec_accum.a < 1.0 || diff_accum.a < 1.0) {
		ProbeData pd = probes_data[0];

		vec3 spec = textureLod_octahedron(probeCubes, vec4(spec_dir, 0), roughness * lodMax).rgb;
		vec3 diff = spherical_harmonics(sd.N, pd.shcoefs);

		diff_accum.rgb += diff * (1.0 - diff_accum.a);
		spec_accum.rgb += spec * (1.0 - spec_accum.a);
	}

	vec3 indirect_radiance =
	        spec_accum.rgb * F_ibl(f0, brdf_lut) +
	        diff_accum.rgb * albedo;

	return radiance + indirect_radiance * ao;
}
