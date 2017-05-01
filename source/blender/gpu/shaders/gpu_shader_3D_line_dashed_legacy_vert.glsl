
/* Note: nearly the same code as for 2D version... Maybe we could deduplicate? */

uniform mat4 ModelViewProjectionMatrix;
uniform vec2 viewport_size;

#if __VERSION__ == 120
  attribute vec3 pos;
  noperspective varying float distance_along_line;
#else
  in vec3 pos;
  noperspective out float distance_along_line;
#endif

void main()
{
	gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0);

	/* Hack - prevent stupid GLSL compiler to optimize out unused viewport_size uniform, which gives crash! */
	distance_along_line = viewport_size.x * 0.000001f - viewport_size.x * 0.0000009f;
}
