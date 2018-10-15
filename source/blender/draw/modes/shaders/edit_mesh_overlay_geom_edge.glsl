
/* Solid Wirefram implementation
 * Mike Erwin, Clément Foucault */

layout(lines) in;
layout(triangle_strip, max_vertices=4) out;

uniform mat4 ProjectionMatrix;
uniform vec2 viewportSize;

in vec4 pPos[];
in ivec4 vData[];
#ifdef VERTEX_FACING
in float vFacing[];
#endif

/* these are the same for all vertices
 * and does not need interpolation */
flat out vec3 edgesCrease;
flat out vec3 edgesBweight;
flat out vec4 faceColor;
flat out ivec3 flag;
#ifdef VERTEX_SELECTION
out vec3 vertexColor;
#endif
#ifdef VERTEX_FACING
out float facing;
#endif

/* See fragment shader */
flat out vec2 ssPos[3];

/* Some bugged AMD drivers need these global variables. See T55961 */
#ifdef VERTEX_SELECTION
vec3 vertex_color[3];
#endif

#ifdef VERTEX_FACING
float v_facing[3];
#endif

/* project to screen space */
vec2 proj(vec4 pos)
{
	return (0.5 * (pos.xy / pos.w) + 0.5) * viewportSize;
}

void doVertex(int v, vec4 pos)
{
#ifdef VERTEX_SELECTION
	vertexColor = vertex_color[v];
#endif

#ifdef VERTEX_FACING
	facing = v_facing[v];
#endif

	gl_Position = pos;

	EmitVertex();
}

void main()
{
	/* Face */
	faceColor = vec4(0.0);

	/* Proj Vertex */
	vec2 pos[2] = vec2[2](proj(pPos[0]), proj(pPos[1]));

	/* little optimization use a vec4 to vectorize
	 * following operations */
	vec4 dirs1, dirs2;

	/* Edge normalized vector */
	dirs1.xy = normalize(pos[1] - pos[0]);

	/* perpendicular to dir */
	dirs1.zw = vec2(-dirs1.y, dirs1.x);

	/* Make it view independent */
	dirs1 *= sizeEdgeFix / viewportSize.xyxy;

	dirs2 = dirs1;

	/* Perspective */
	if (ProjectionMatrix[3][3] == 0.0) {
		dirs1 *= pPos[0].w;
		dirs2 *= pPos[1].w;
	}

#ifdef VERTEX_SELECTION
	vertex_color[0] = EDIT_MESH_vertex_color(vData[0].x).rgb;
	vertex_color[1] = EDIT_MESH_vertex_color(vData[1].x).rgb;
#endif

#ifdef VERTEX_FACING
	/* Weird but some buggy AMD drivers need this. */
	v_facing[0] = vFacing[0];
	v_facing[1] = vFacing[1];
#endif

	/* Edge / Vert data */
	ssPos[0] = ssPos[2] = pos[0];
	ssPos[1] = pos[1];
	flag[0] = flag[2] = (vData[0].x << 8);
	flag[1] = (vData[1].x << 8);
	doVertex(0, pPos[0] + vec4( dirs1.zw, 0.0, 0.0));
	doVertex(0, pPos[0] + vec4(-dirs1.zw, 0.0, 0.0));

	flag[2] |= vData[0].y;
	edgesCrease[2] = vData[0].z / 255.0;
	edgesBweight[2] = vData[0].w / 255.0;

	doVertex(1, pPos[1] + vec4( dirs2.zw, 0.0, 0.0));
	doVertex(1, pPos[1] + vec4(-dirs2.zw, 0.0, 0.0));

	EndPrimitive();
}
