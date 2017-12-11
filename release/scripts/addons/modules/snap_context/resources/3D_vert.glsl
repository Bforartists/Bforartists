#version 120

uniform bool use_clip_planes;
uniform vec4 clip_plane[4];
varying vec4 clip_distance;

uniform mat4 MV;
uniform mat4 MVP;

attribute vec3 pos;
attribute float primitive_id;
varying float primitive_id_var;

void main()
{
	if (use_clip_planes) {
		vec4 g_pos = MV * vec4(pos, 1.0);

		for (int i = 0; i != 4; i++) {
			clip_distance[i] = dot(clip_plane[i], g_pos);
		}
	}

	primitive_id_var = primitive_id;
	gl_Position = MVP * vec4(pos, 1.0);
}
