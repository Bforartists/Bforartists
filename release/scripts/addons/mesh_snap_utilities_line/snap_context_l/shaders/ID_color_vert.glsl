uniform mat4 ModelViewProjectionMatrix;

#ifdef USE_CLIP_PLANES
uniform mat4 ModelMatrix;
uniform bool use_clip_planes;
uniform vec4 WorldClipPlanes[4];
#endif

in vec3 pos;

void main()
{
#ifdef USE_CLIP_PLANES
	if (use_clip_planes) {
		vec4 g_pos = ModelMatrix * vec4(pos, 1.0);

    gl_ClipDistance[0] = dot(WorldClipPlanes[0], g_pos);
    gl_ClipDistance[1] = dot(WorldClipPlanes[1], g_pos);
    gl_ClipDistance[2] = dot(WorldClipPlanes[2], g_pos);
    gl_ClipDistance[3] = dot(WorldClipPlanes[3], g_pos);
	}
#endif

	gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0);
}
