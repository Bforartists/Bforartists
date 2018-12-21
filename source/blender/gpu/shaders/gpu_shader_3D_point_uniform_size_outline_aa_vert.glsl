
uniform mat4 ModelViewProjectionMatrix;
uniform float size;
uniform float outlineWidth;

in vec3 pos;
out vec4 radii;

void main() {
	gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0);
	gl_PointSize = size;

	// calculate concentric radii in pixels
	float radius = 0.5 * size;

	// start at the outside and progress toward the center
	radii[0] = radius;
	radii[1] = radius - 1.0;
	radii[2] = radius - outlineWidth;
	radii[3] = radius - outlineWidth - 1.0;

	// convert to PointCoord units
	radii /= size;
}
