
uniform vec4 color;

#if __VERSION__ == 120
  varying vec2 radii;
  #define fragColor gl_FragColor
#else
  in vec2 radii;
  out vec4 fragColor;
#endif

void main() {
	float dist = length(gl_PointCoord - vec2(0.5));

// transparent outside of point
// --- 0 ---
//	smooth transition
// --- 1 ---
// pure point color
// ...
// dist = 0 at center of point

	fragColor.rgb = color.rgb;
	fragColor.a = mix(color.a, 0.0, smoothstep(radii[1], radii[0], dist));
}
