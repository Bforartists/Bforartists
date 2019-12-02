
uniform float normalSize;

in vec3 pos;
in vec3 nor;
in vec3 tan;
in float rad;

flat out vec4 finalColor;

void main()
{
  GPU_INTEL_VERTEX_SHADER_WORKAROUND

  vec3 final_pos = pos;

  float flip = (gl_InstanceID != 0) ? -1.0 : 1.0;

  if (gl_VertexID % 2 == 0) {
    final_pos += normalSize * rad * (flip * nor - tan);
  }

  vec3 world_pos = point_object_to_world(final_pos);
  gl_Position = point_world_to_ndc(world_pos);

  finalColor = colorWireEdit;

#ifdef USE_WORLD_CLIP_PLANES
  world_clip_planes_calc_clip_distance(world_pos);
#endif
}
