
flat in int finalFlag;
out vec4 fragColor;

#define VERTEX_SELECTED (1 << 0)
#define VERTEX_HIDE     (1 << 4)

void main()
{
	if (bool(finalFlag & VERTEX_HIDE)) {
		discard;
	}

	vec2 centered = gl_PointCoord - vec2(0.5);
	float dist_squared = dot(centered, centered);
	const float rad_squared = 0.25;
	const vec4 colSel = vec4(1.0, 1.0, 1.0, 1.0);
	const vec4 colUnsel = vec4(0.5, 0.5, 0.5, 1.0);

	// round point with jaggy edges
	if (dist_squared > rad_squared) {
		discard;
	}

	fragColor = bool(finalFlag & VERTEX_SELECTED) ? colSel : colUnsel;
}
