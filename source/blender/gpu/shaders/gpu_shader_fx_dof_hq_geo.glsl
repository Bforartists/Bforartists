uniform ivec2 rendertargetdim;
uniform sampler2D colorbuffer;

uniform vec2 layerselection;

uniform sampler2D cocbuffer;

layout(points) in;
layout(triangle_strip, max_vertices = 4) out;

#define POS gl_in[0].gl_Position

in vec2 uvcoord[];
out vec2 particlecoord;
flat out vec4 color;

#define M_PI 3.1415926535897932384626433832795

void main()
{
	vec4 coc = textureLod(cocbuffer, uvcoord[0], 0.0);

	float offset_val = dot(coc.rg, layerselection);
	if (offset_val < 1.0)
		return;

	vec4 colortex = textureLod(colorbuffer, uvcoord[0], 0.0);

	/* find the area the pixel will cover and divide the color by it */
	float alpha = 1.0 / (offset_val * offset_val * M_PI);
	colortex *= alpha;
	colortex.a = alpha;

	vec2 offset_far = vec2(offset_val * 0.5) / vec2(rendertargetdim.x, rendertargetdim.y);

	color = colortex;

	gl_Position = POS + vec4(-offset_far.x, -offset_far.y, 0.0, 0.0);
	particlecoord = vec2(-1.0, -1.0);
	EmitVertex();

	gl_Position = POS + vec4(-offset_far.x, offset_far.y, 0.0, 0.0);
	particlecoord = vec2(-1.0, 1.0);
	EmitVertex();

	gl_Position = POS + vec4(offset_far.x, -offset_far.y, 0.0, 0.0);
	particlecoord = vec2(1.0, -1.0);
	EmitVertex();

	gl_Position = POS + vec4(offset_far.x, offset_far.y, 0.0, 0.0);
	particlecoord = vec2(1.0, 1.0);
	EmitVertex();

	EndPrimitive();
}
