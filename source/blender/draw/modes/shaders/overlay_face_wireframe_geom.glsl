
/* This shader is only used for intel GPU where the Geom shader is faster
 * than doing everything thrice in the vertex shader. */

layout(triangles) in;
layout(triangle_strip, max_vertices = 3) out;

uniform vec2 wireStepParam;

in vec2 ssPos[];
in float facingOut[];

flat out vec3 ssVec0;
flat out vec3 ssVec1;
flat out vec3 ssVec2;
out float facing;

#ifdef LIGHT_EDGES
in vec3 obPos[];
in vec3 vNor[];
in float forceEdge[];

flat out vec3 edgeSharpness;
#endif

#define NO_EDGE vec3(10000.0);

/* TODO(fclem) remove code duplication. */
vec3 compute_vec(vec2 v0, vec2 v1)
{
	vec2 v = normalize(v1 - v0);
	v = vec2(-v.y, v.x);
	return vec3(v, -dot(v, v0));
}

vec3 get_edge_normal(vec3 n1, vec3 n2, vec3 edge)
{
	edge = normalize(edge);
	vec3 n = n1 + n2;
	float p = dot(edge, n);
	return normalize(n - p * edge);
}

float get_edge_sharpness(vec3 fnor, vec3 vnor)
{
	float sharpness = abs(dot(fnor, vnor));
	return smoothstep(wireStepParam.x, wireStepParam.y, sharpness);
}

void main(void)
{
	vec3 facings = vec3(facingOut[0], facingOut[1], facingOut[2]);
	bvec3 do_edge = greaterThan(abs(facings), vec3(1.0));
	facings = fract(facings) - clamp(-sign(facings), 0.0, 1.0);

	ssVec0 = do_edge.x ? compute_vec(ssPos[0], ssPos[1]) : NO_EDGE;
	ssVec1 = do_edge.y ? compute_vec(ssPos[1], ssPos[2]) : NO_EDGE;
	ssVec2 = do_edge.z ? compute_vec(ssPos[2], ssPos[0]) : NO_EDGE;

#ifdef LIGHT_EDGES
	vec3 edges[3];
	edges[0] = obPos[1] - obPos[0];
	edges[1] = obPos[2] - obPos[1];
	edges[2] = obPos[0] - obPos[2];
	vec3 fnor = normalize(cross(edges[0], -edges[2]));

	edgeSharpness.x = get_edge_sharpness(fnor, get_edge_normal(vNor[0], vNor[1], edges[0]));
	edgeSharpness.y = get_edge_sharpness(fnor, get_edge_normal(vNor[1], vNor[2], edges[1]));
	edgeSharpness.z = get_edge_sharpness(fnor, get_edge_normal(vNor[2], vNor[0], edges[2]));
	edgeSharpness.x = (forceEdge[0] == 1.0) ? 1.0 : edgeSharpness.x;
	edgeSharpness.y = (forceEdge[1] == 1.0) ? 1.0 : edgeSharpness.y;
	edgeSharpness.z = (forceEdge[2] == 1.0) ? 1.0 : edgeSharpness.z;
#endif
	gl_Position = gl_in[0].gl_Position;
	facing = facings.x;
	EmitVertex();

	gl_Position = gl_in[1].gl_Position;
	facing = facings.y;
	EmitVertex();

	gl_Position = gl_in[2].gl_Position;
	facing = facings.z;
	EmitVertex();
	EndPrimitive();
}
