vec3 background_color(WorldData world_data, float y)
{
  return mix(world_data.background_color_low, world_data.background_color_high, y).xyz +
         (world_data.background_dither_factor * bayer_dither_noise());
}
