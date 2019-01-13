
uniform float ImageTransparencyCutoff = 0.1;
uniform sampler2D image;
uniform bool imageSrgb;
uniform bool imageNearest;

uniform mat4 ProjectionMatrix;
uniform mat4 ViewMatrixInverse;
uniform float alpha = 0.5;
uniform vec2 invertedViewportSize;
uniform vec4 viewvecs[3];

uniform vec3 materialDiffuseColor;
uniform vec3 materialSpecularColor;
uniform float materialRoughness;

#ifdef NORMAL_VIEWPORT_PASS_ENABLED
in vec3 normal_viewport;
#endif /* NORMAL_VIEWPORT_PASS_ENABLED */
#ifdef V3D_SHADING_TEXTURE_COLOR
in vec2 uv_interp;
#endif
#ifdef V3D_LIGHTING_MATCAP
uniform sampler2D matcapImage;
#endif

layout(std140) uniform world_block {
	WorldData world_data;
};

layout(location=0) out vec4 transparentAccum;
layout(location=1) out float revealageAccum; /* revealage actually stored in transparentAccum.a */

void main()
{
	vec4 diffuse_color;

#ifdef V3D_SHADING_TEXTURE_COLOR
	diffuse_color = workbench_sample_texture(image, uv_interp, imageSrgb, imageNearest);
	if (diffuse_color.a < ImageTransparencyCutoff) {
		discard;
	}
#else
	diffuse_color = vec4(materialDiffuseColor, 1.0);
#endif /* V3D_SHADING_TEXTURE_COLOR */

	vec2 uv_viewport = gl_FragCoord.xy * invertedViewportSize;
	vec3 I_vs = view_vector_from_screen_uv(uv_viewport, viewvecs, ProjectionMatrix);

#ifdef NORMAL_VIEWPORT_PASS_ENABLED
	vec3 nor = normalize(normal_viewport);
#endif

	/* -------- SHADING --------- */
#ifdef V3D_LIGHTING_FLAT
	vec3 shaded_color = diffuse_color.rgb;

#elif defined(V3D_LIGHTING_MATCAP)
	bool flipped = world_data.matcap_orientation != 0;
	vec2 matcap_uv = matcap_uv_compute(I_vs, nor, flipped);
	vec3 matcap = textureLod(matcapImage, matcap_uv, 0.0).rgb;
	vec3 shaded_color = matcap * diffuse_color.rgb;

#elif defined(V3D_LIGHTING_STUDIO)
	vec3 shaded_color = get_world_lighting(world_data,
	                                       diffuse_color.rgb, materialSpecularColor, materialRoughness,
	                                       nor, I_vs);
#endif

	/* Based on :
	 * McGuire and Bavoil, Weighted Blended Order-Independent Transparency, Journal of
	 * Computer Graphics Techniques (JCGT), vol. 2, no. 2, 122–141, 2013
	 */
	/* Listing 4 */
	float z = linear_zdepth(gl_FragCoord.z, viewvecs, ProjectionMatrix);
	float weight = calculate_transparent_weight(z, alpha);
	transparentAccum = vec4(shaded_color * weight, alpha);
	revealageAccum = weight;
}
