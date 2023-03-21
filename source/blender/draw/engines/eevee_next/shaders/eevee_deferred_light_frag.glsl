
/**
 * Compute light objects lighting contribution using Gbuffer data.
 *
 * Output light either directly to the radiance buffers or to temporary radiance accumulation
 * buffer that will be processed by other deferred lighting passes.
 */

#pragma BLENDER_REQUIRE(eevee_gbuffer_lib.glsl)
#pragma BLENDER_REQUIRE(common_view_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_light_eval_lib.glsl)

void main()
{
  ivec2 texel = ivec2(gl_FragCoord.xy);

  float depth = texelFetch(hiz_tx, ivec2(gl_FragCoord.xy), 0).r;
  vec3 P = get_world_space_from_depth(uvcoordsvar.xy, depth);

  /* TODO(fclem): High precision derivative. */
  vec3 Ng = safe_normalize(cross(dFdx(P), dFdy(P)));
  vec3 V = cameraVec(P);
  float vP_z = dot(cameraForward, P) - dot(cameraForward, cameraPos);

  vec4 gbuffer_0_packed = texelFetch(gbuffer_closure_tx, ivec3(texel, 0), 0);
  vec4 gbuffer_1_packed = texelFetch(gbuffer_closure_tx, ivec3(texel, 1), 0);

  ClosureReflection reflection_data;
  reflection_data.N = gbuffer_normal_unpack(gbuffer_0_packed.xy);
  reflection_data.roughness = gbuffer_0_packed.z;

  ClosureDiffuse diffuse_data;
  diffuse_data.N = gbuffer_normal_unpack(gbuffer_1_packed.xy);
  /* These are only set for SSS case. */
  diffuse_data.sss_radius = vec3(0.0);
  diffuse_data.sss_id = 0u;
  float thickness = 0.0;

  bool is_refraction = gbuffer_is_refraction(gbuffer_1_packed);
  if (is_refraction) {
    /* Still evaluate the diffuse light so that dithered SSS / Refraction combination still
     * produces a complete diffuse light buffer that will be correctly convolved by the SSSS.
     * The refraction pixels will just set the diffuse radiance to 0. */
  }
  else if (false /* TODO */) {
    vec4 gbuffer_2_packed = texelFetch(gbuffer_closure_tx, ivec3(texel, 2), 0);
    diffuse_data.sss_radius = gbuffer_sss_radii_unpack(gbuffer_2_packed.xyz);
    diffuse_data.sss_id = gbuffer_object_id_unorm16_unpack(gbuffer_2_packed.w);
    thickness = gbuffer_thickness_pack(gbuffer_1_packed.z);
  }

  vec3 diffuse_light = vec3(0.0);
  vec3 reflection_light = vec3(0.0);

  light_eval(
      diffuse_data, reflection_data, P, Ng, V, vP_z, thickness, diffuse_light, reflection_light);

  if (is_last_eval_pass) {
    /* Apply color and output lighting to render-passes. */
    vec4 color_0_packed = texelFetch(gbuffer_color_tx, ivec3(texel, 0), 0);
    vec4 color_1_packed = texelFetch(gbuffer_color_tx, ivec3(texel, 1), 0);

    reflection_data.color = gbuffer_color_unpack(color_0_packed);
    diffuse_data.color = gbuffer_color_unpack(color_1_packed);

    if (is_refraction) {
      diffuse_data.color = vec3(0.0);
    }

    reflection_light *= reflection_data.color;
    diffuse_light *= diffuse_data.color;
    /* Add radiance to light pass. */
    imageStore(
        rp_light_img, ivec3(texel, RENDER_PASS_LAYER_DIFFUSE_LIGHT), vec4(diffuse_light, 1.0));
    imageStore(
        rp_light_img, ivec3(texel, RENDER_PASS_LAYER_SPECULAR_LIGHT), vec4(reflection_light, 1.0));
    /* Add radiance to combined pass. */
    out_radiance = vec4(diffuse_light + reflection_light, 0.0);
    out_transmittance = vec4(1.0);
  }
  else {
    /* Store lighting for next deferred pass. */

    /* Output diffuse light along with object ID for sub-surface screen space processing. */
    vec4 diffuse_radiance;
    diffuse_radiance.xyz = diffuse_light;
    diffuse_radiance.w = gbuffer_object_id_f16_pack(diffuse_data.sss_id);
    imageStore(out_diffuse_light_img, texel, diffuse_radiance);

    imageStore(out_specular_light_img, texel, vec4(reflection_light, 0.0));

    /* Final radiance will be amended by the last pass.
     * This should do nothing as color write should be disabled in this case. */
    out_radiance = vec4(0.0);
    out_transmittance = vec4(0.0);
  }
}
