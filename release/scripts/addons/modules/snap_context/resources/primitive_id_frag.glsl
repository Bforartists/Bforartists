#version 120

uniform bool use_clip_planes;
varying vec4 clip_distance;

uniform float offset;

varying float primitive_id_var;

void main()
{
	if (use_clip_planes &&
	   ((clip_distance[0] < 0) ||
	    (clip_distance[1] < 0) ||
	    (clip_distance[2] < 0) ||
	    (clip_distance[3] < 0)))
	{
		discard;
	}

	gl_FragColor = vec4(offset + primitive_id_var, 0, 0, 0);
}
