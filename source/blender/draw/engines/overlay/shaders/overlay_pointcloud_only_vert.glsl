#pragma BLENDER_REQUIRE(common_view_clipping_lib.glsl)
#pragma BLENDER_REQUIRE(common_view_lib.glsl)
#pragma BLENDER_REQUIRE(common_pointcloud_lib.glsl)

void main()
{
  vec3 world_pos = pointcloud_get_pos();
  gl_Position = point_world_to_ndc(world_pos);
}
