
uniform ivec3 grid_resolution;
uniform vec3 corner;
uniform vec3 increment_x;
uniform vec3 increment_y;
uniform vec3 increment_z;

flat out int objectId;

void main()
{
  vec3 ls_cell_location;
  /* Keep in sync with update_irradiance_probe */
  ls_cell_location.z = float(gl_VertexID % grid_resolution.z);
  ls_cell_location.y = float((gl_VertexID / grid_resolution.z) % grid_resolution.y);
  ls_cell_location.x = float(gl_VertexID / (grid_resolution.z * grid_resolution.y));

  vec3 ws_cell_location = corner +
                          (increment_x * ls_cell_location.x + increment_y * ls_cell_location.y +
                           increment_z * ls_cell_location.z);

  gl_Position = ViewProjectionMatrix * vec4(ws_cell_location, 1.0);
  gl_PointSize = 2.0f;

  /* ID 0 is nothing (background) */
  objectId = resource_handle + 1;

#ifdef USE_WORLD_CLIP_PLANES
  world_clip_planes_calc_clip_distance(ws_cell_location);
#endif
}
