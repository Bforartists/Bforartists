
/* Undefine the macro that avoids compilation errors. */
#undef blender_srgb_to_framebuffer_space

uniform bool srgbTarget = false;

vec4 blender_srgb_to_framebuffer_space(vec4 color)
{
  if (srgbTarget) {
    vec3 c = max(color.rgb, vec3(0.0));
    vec3 c1 = c * (1.0 / 12.92);
    vec3 c2 = pow((c + 0.055) * (1.0 / 1.055), vec3(2.4));
    color.rgb = mix(c1, c2, step(vec3(0.04045), c));
  }
  return color;
}
