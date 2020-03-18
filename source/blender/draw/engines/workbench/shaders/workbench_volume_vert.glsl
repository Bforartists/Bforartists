
#pragma BLENDER_REQUIRE(common_view_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_common_obinfos_lib.glsl)

uniform float slicePosition;
uniform int sliceAxis; /* -1 is no slice, 0 is X, 1 is Y, 2 is Z. */

uniform mat4 volumeTextureToObject;

in vec3 pos;

RESOURCE_ID_VARYING

#ifdef VOLUME_SLICE
in vec3 uvs;

out vec3 localPos;
#endif

void main()
{
#ifdef VOLUME_SLICE
  if (sliceAxis == 0) {
    localPos = vec3(slicePosition * 2.0 - 1.0, pos.xy);
  }
  else if (sliceAxis == 1) {
    localPos = vec3(pos.x, slicePosition * 2.0 - 1.0, pos.y);
  }
  else {
    localPos = vec3(pos.xy, slicePosition * 2.0 - 1.0);
  }
  vec3 final_pos = localPos;
#else
  vec3 final_pos = pos;
#endif

#ifdef VOLUME_SMOKE
  final_pos = ((final_pos * 0.5 + 0.5) - OrcoTexCoFactors[0].xyz) / OrcoTexCoFactors[1].xyz;
#else
  final_pos = (volumeTextureToObject * vec4(final_pos * 0.5 + 0.5, 1.0)).xyz;
#endif
  gl_Position = point_object_to_ndc(final_pos);

  PASS_RESOURCE_ID
}
