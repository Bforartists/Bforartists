
void main()
{
  vert_iface.vPos = vec4(pos, 1.0);
  vert_iface.face = gl_InstanceID;
}
