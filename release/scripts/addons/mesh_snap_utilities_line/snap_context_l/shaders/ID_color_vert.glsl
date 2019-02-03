uniform mat4 ModelViewProjectionMatrix;

#ifdef USE_CLIP_PLANES
uniform mat4 ModelViewMatrix;
uniform bool use_clip_planes;
uniform vec4 clip_plane[4];
out vec4 clip_distance;
#endif

in vec3 pos;

void main()
{
#ifdef USE_CLIP_PLANES
	if (use_clip_planes) {
		vec4 g_pos = ModelViewMatrix * vec4(pos, 1.0);

		for (int i = 0; i != 4; i++) {
			clip_distance[i] = dot(clip_plane[i], g_pos);
		}
	}
#endif

	gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0);
}
