
out vec4 FragColor;

uniform sampler2D wireColor;
uniform sampler2D wireDepth;
uniform sampler2D sceneDepth;
uniform float alpha;

void main()
{
	ivec2 co = ivec2(gl_FragCoord.xy);
	float wire_depth = texelFetch(wireDepth, co, 0).r;
	float scene_depth = texelFetch(sceneDepth, co, 0).r;
	vec4 wire_color = texelFetch(wireColor, co, 0).rgba;

	FragColor = wire_color;

	/* this works because not rendered depth is 1.0 and the
	 * following test is always true even when no wires */
	if ((wire_depth > scene_depth) && (wire_color.a > 0)) {
		/* Note : Using wire_color.a * alpha produce unwanted result */
		FragColor.a = alpha;
	}
}
