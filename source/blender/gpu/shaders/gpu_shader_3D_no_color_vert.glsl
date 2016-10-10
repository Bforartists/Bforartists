
uniform mat4 ModelViewProjectionMatrix;

#if __VERSION__ == 120
  attribute vec3 pos;
#else
  in vec3 pos;
#endif

void main()
{
	gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0);
}
