
uniform mat4 ModelViewProjectionMatrix;

#ifdef UV_POS
in vec2 u;
#  define pos u
#else
in vec2 pos;
#endif

void main()
{
  gl_Position = ModelViewProjectionMatrix * vec4(pos, 0.0, 1.0);
}
