
/* Non-geometry shader equivalent for eevee_legacy_lightprobe_vert + eevee_legacy_lightprobe_geom.
 * generates geometry instance per cubeface for multi-layered rendering. */
void main()
{

  const vec3 maj_axes[6] = vec3[6](vec3(1.0, 0.0, 0.0),
                                   vec3(-1.0, 0.0, 0.0),
                                   vec3(0.0, 1.0, 0.0),
                                   vec3(0.0, -1.0, 0.0),
                                   vec3(0.0, 0.0, 1.0),
                                   vec3(0.0, 0.0, -1.0));
  const vec3 x_axis[6] = vec3[6](vec3(0.0, 0.0, -1.0),
                                 vec3(0.0, 0.0, 1.0),
                                 vec3(1.0, 0.0, 0.0),
                                 vec3(1.0, 0.0, 0.0),
                                 vec3(1.0, 0.0, 0.0),
                                 vec3(-1.0, 0.0, 0.0));
  const vec3 y_axis[6] = vec3[6](vec3(0.0, -1.0, 0.0),
                                 vec3(0.0, -1.0, 0.0),
                                 vec3(0.0, 0.0, 1.0),
                                 vec3(0.0, 0.0, -1.0),
                                 vec3(0.0, -1.0, 0.0),
                                 vec3(0.0, -1.0, 0.0));
  geom_iface.fFace = gl_InstanceID;
  gl_Position = vec4(pos.xyz, 1.0);
  geom_iface.worldPosition = x_axis[geom_iface.fFace] * pos.x + y_axis[geom_iface.fFace] * pos.y +
                             maj_axes[geom_iface.fFace];

#ifdef GPU_METAL
  /* In the Metal API, gl_Layer equivalent is specified in the vertex shader for multilayered
   * rendering support. */
  MTLRenderTargetArrayIndex = Layer + geom_iface.fFace;
#endif
}
