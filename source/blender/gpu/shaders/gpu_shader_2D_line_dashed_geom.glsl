
// Draw dashed lines, perforated in screen space.

/* Make to be used with dynamic batching so no Model Matrix needed */
uniform mat4 ModelViewProjectionMatrix;
uniform vec2 viewport_size;

/* Uniforms from fragment shader, used here to optimize out useless computation in case of solid line. */
uniform float dash_factor;  /* if > 1.0, solid line. */
uniform int num_colors;  /* Enabled if > 0, 1 for solid line. */

layout(lines) in;

layout(line_strip, max_vertices = 2) out;
noperspective out float distance_along_line;

void main()
{
	vec4 v1 = gl_in[0].gl_Position;
	vec4 v2 = gl_in[1].gl_Position;

	gl_Position = v1;
	distance_along_line = 0.0f;
	EmitVertex();

	gl_Position = v2;
	if ((num_colors == 1) || (dash_factor >= 1.0f)) {
		/* Solid line, optimise out distance computation! */
		distance_along_line = 0.0f;
	}
	else {
		vec2 p1 = (v1.xy / v1.w) * 0.5 + 0.5;  // <- device coordinates in [0..1] range.
		p1 = p1 * viewport_size;  // <- 'virtual' screen coordinates.

		vec2 p2 = (v2.xy / v2.w) * 0.5 + 0.5;  // <- device coordinates in [0..1] range.
		p2 = p2 * viewport_size;  // <- 'virtual' screen coordinates.

		distance_along_line = distance(p1, p2);
	}
	EmitVertex();

	EndPrimitive();

	/* Note: we could also use similar approach as diag_stripes_frag, but this would give us dashed 'anchored'
	 * to the screen, and not to one end of the line... */
}
