
uniform mat4 ModelViewProjectionMatrix;
uniform float size;

#if __VERSION__ == 120
  attribute vec3 pos;
  varying vec2 radii;
#else
  in vec3 pos;
  out vec2 radii;
#endif

void main() {
	gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0);
	gl_PointSize = size;

	// calculate concentric radii in pixels
	float radius = 0.5 * size;

	// start at the outside and progress toward the center
	radii[0] = radius;
	radii[1] = radius - 1.0;

	// convert to PointCoord units
	radii /= size;
}
