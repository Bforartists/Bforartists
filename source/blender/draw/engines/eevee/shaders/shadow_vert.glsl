
in vec3 pos;
in vec3 nor;

#ifdef MESH_SHADER
out vec3 worldPosition;
out vec3 viewPosition;
out vec3 worldNormal;
out vec3 viewNormal;
#endif

#ifdef HAIR_SHADER
out vec3 hairTangent;
out float hairThickTime;
out float hairThickness;
out float hairTime;
flat out int hairStrandID;
#endif

void main()
{
#ifdef GPU_INTEL
  /* Due to some shader compiler bug, we somewhat
   * need to access gl_VertexID to make it work. even
   * if it's actually dead code. */
  gl_Position.x = float(gl_VertexID);
#endif

#ifdef HAIR_SHADER
  hairStrandID = hair_get_strand_id();
  vec3 world_pos, binor;
  hair_get_pos_tan_binor_time((ProjectionMatrix[3][3] == 0.0),
                              ModelMatrixInverse,
                              ViewMatrixInverse[3].xyz,
                              ViewMatrixInverse[2].xyz,
                              world_pos,
                              hairTangent,
                              binor,
                              hairTime,
                              hairThickness,
                              hairThickTime);

  worldNormal = cross(hairTangent, binor);
#else
  vec3 world_pos = point_object_to_world(pos);
#endif

  gl_Position = point_world_to_ndc(world_pos);
#ifdef MESH_SHADER
  worldPosition = world_pos;
  viewPosition = point_world_to_view(worldPosition);

#  ifndef HAIR_SHADER
  worldNormal = normalize(normal_object_to_world(nor));
#  endif

  /* No need to normalize since this is just a rotation. */
  viewNormal = normal_world_to_view(worldNormal);
#  ifdef USE_ATTR
  pass_attr(pos);
#  endif
#endif
}
