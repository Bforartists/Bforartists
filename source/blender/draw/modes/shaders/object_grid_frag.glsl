
/* Infinite grid
 * Author: Clément Foucault */

out vec4 FragColor;

uniform mat4 ProjectionMatrix;
uniform vec3 cameraPos;
uniform vec3 planeNormal;
uniform vec3 planeAxes;
uniform vec3 eye;
uniform vec4 gridSettings;
uniform vec2 viewportSize;
uniform vec4 screenvecs[3];
uniform float lineKernel = 0.0;
uniform float gridOneOverLogSubdiv;
uniform sampler2D depthBuffer;

#define gridDistance      gridSettings.x
#define gridResolution    gridSettings.y
#define gridScale         gridSettings.z
#define gridSubdiv        gridSettings.w

uniform int gridFlag;

#define AXIS_X    (1 << 0)
#define AXIS_Y    (1 << 1)
#define AXIS_Z    (1 << 2)
#define GRID      (1 << 3)
#define PLANE_XY  (1 << 4)
#define PLANE_XZ  (1 << 5)
#define PLANE_YZ  (1 << 6)
#define GRID_BACK (1 << 9) /* grid is behind objects */

#define M_1_SQRTPI   0.5641895835477563    /* 1/sqrt(pi) */

/**
 * We want to know how much a pixel is covered by a line.
 * We replace the square pixel with acircle of the same area and try to find the intersection area.
 * The area we search is the circular segment. https://en.wikipedia.org/wiki/Circular_segment
 * The formula for the area uses inverse trig function and is quite complexe.
 * Instead, we approximate it by using the smoothstep function and a 1.05 factor to the disc radius.
 **/
#define DISC_RADIUS (M_1_SQRTPI * 1.05)
#define GRID_LINE_SMOOTH_START (0.5 - DISC_RADIUS)
#define GRID_LINE_SMOOTH_END (0.5 + DISC_RADIUS)

float get_grid(vec2 co, vec2 fwidthCos, float grid_size)
{
	float half_size = grid_size / 2.0;
	/* triangular wave pattern, amplitude is [0, half_size] */
	vec2 grid_domain = abs(mod(co + half_size, grid_size) - half_size);
	/* modulate by the absolute rate of change of the coordinates
	 * (make lines have the same width under perspective) */
	grid_domain /= fwidthCos;

	/* collapse waves */
	float line_dist = min(grid_domain.x, grid_domain.y);

	return 1.0 - smoothstep(GRID_LINE_SMOOTH_START, GRID_LINE_SMOOTH_END, line_dist - lineKernel);
}

vec3 get_axes(vec3 co, vec3 fwidthCos, float line_size)
{
	vec3 axes_domain = abs(co);
	/* modulate by the absolute rate of change of the coordinates
	 * (make line have the same width under perspective) */
	axes_domain /= fwidthCos;

	return 1.0 - smoothstep(GRID_LINE_SMOOTH_START, GRID_LINE_SMOOTH_END, axes_domain - (line_size + lineKernel));
}

vec3 get_floor_pos(vec2 uv, out vec3 wPos)
{
	vec3 camera_vec, camera_pos, corner_pos;
	vec3 floored_pos = planeAxes * floor(screenvecs[2].xyz);
	corner_pos = screenvecs[2].xyz - floored_pos;

	vec3 pixel_pos = corner_pos + uv.x * screenvecs[0].xyz + uv.y * screenvecs[1].xyz;

	/* if perspective */
	if (ProjectionMatrix[3][3] == 0.0) {
		camera_pos = cameraPos - floored_pos;
		camera_vec = normalize(pixel_pos - camera_pos);
	}
	else {
		camera_pos = pixel_pos;
		camera_vec = normalize(eye);
	}

	float plane_normal_dot_camera_vec = dot(planeNormal, camera_vec);
	float p = -dot(planeNormal, camera_pos);
	if (plane_normal_dot_camera_vec != 0) {
		p /= plane_normal_dot_camera_vec;
	}
	vec3 plane = camera_pos + camera_vec * p;

	/* fix residual imprecision */
	plane *= planeAxes;

	/* Recover non-offseted world position */
	wPos = plane + floored_pos;

	return plane;
}

void main()
{
	vec2 sPos = gl_FragCoord.xy / viewportSize; /* Screen [0,1] position */

	/* To reduce artifacts, use a local version of the positions
	 * to compute derivatives since they are not position dependent.
	 * This gets rid of the blocky artifacts. Unfortunately we still
	 * need the world position for the grid to scale properly from the origin. */
	vec3 gPos, wPos; /* Grid pos., World pos. */
	gPos = get_floor_pos(sPos, wPos);

	vec3 fwidthPos = fwidth(gPos);

	float dist, fade;
	/* if persp */
	if (ProjectionMatrix[3][3] == 0.0) {
		vec3 viewvec = cameraPos - wPos;
		dist = length(viewvec);
		viewvec /= dist;

		float angle;
		if ((gridFlag & PLANE_XZ) != 0) {
			angle = viewvec.y;
		}
		else if ((gridFlag & PLANE_YZ) != 0) {
			angle = viewvec.x;
		}
		else {
			angle = viewvec.z;
		}

		angle = 1.0 - abs(angle);
		angle *= angle;
		fade = 1.0 - angle * angle;
		fade *= 1.0 - smoothstep(0.0, gridDistance, dist - gridDistance);
	}
	else {
		dist = abs(gl_FragCoord.z * 2.0 - 1.0);
		fade = 1.0 - smoothstep(0.0, 0.5, dist - 0.5);
		dist = 1.0; /* avoid branch after */

		if ((gridFlag & PLANE_XY) != 0) {
			float angle = 1.0 - abs(eye.z);
			dist = 1.0 + angle * 2.0;
			angle *= angle;
			fade *= 1.0 - angle * angle;
		}
	}

	if ((gridFlag & GRID) != 0) {
		float grid_res = log(dist * gridResolution) * gridOneOverLogSubdiv;

		float blend = fract(-max(grid_res, 0.0));
		float lvl = floor(grid_res);

		/* from biggest to smallest */
		float scaleA = gridScale * pow(gridSubdiv, max(lvl - 1.0, 0.0));
		float scaleB = gridScale * pow(gridSubdiv, max(lvl + 0.0, 0.0));
		float scaleC = gridScale * pow(gridSubdiv, max(lvl + 1.0, 1.0));

		vec2 grid_pos, grid_fwidth;
		if ((gridFlag & PLANE_XZ) != 0) {
			grid_pos = wPos.xz;
			grid_fwidth = fwidthPos.xz;
		}
		else if ((gridFlag & PLANE_YZ) != 0) {
			grid_pos = wPos.yz;
			grid_fwidth = fwidthPos.yz;
		}
		else {
			grid_pos = wPos.xy;
			grid_fwidth = fwidthPos.xy;
		}

		float gridA = get_grid(grid_pos, grid_fwidth, scaleA);
		float gridB = get_grid(grid_pos, grid_fwidth, scaleB);
		float gridC = get_grid(grid_pos, grid_fwidth, scaleC);

		FragColor = colorGrid;
		FragColor.a *= gridA * blend;
		FragColor = mix(FragColor, mix(colorGrid, colorGridEmphasise, blend), gridB);
		FragColor = mix(FragColor, colorGridEmphasise, gridC);
	}
	else {
		FragColor = vec4(colorGrid.rgb, 0.0);
	}

	if ((gridFlag & (AXIS_X | AXIS_Y | AXIS_Z)) != 0) {
		/* Setup axes 'domains' */
		vec3 axes_dist, axes_fwidth;

		if ((gridFlag & AXIS_X) != 0) {
			axes_dist.x = dot(wPos.yz, planeAxes.yz);
			axes_fwidth.x = dot(fwidthPos.yz, planeAxes.yz);
		}
		if ((gridFlag & AXIS_Y) != 0) {
			axes_dist.y = dot(wPos.xz, planeAxes.xz);
			axes_fwidth.y = dot(fwidthPos.xz, planeAxes.xz);
		}
		if ((gridFlag & AXIS_Z) != 0) {
			axes_dist.z = dot(wPos.xy, planeAxes.xy);
			axes_fwidth.z = dot(fwidthPos.xy, planeAxes.xy);
		}

		/* Computing all axes at once using vec3 */
		vec3 axes = get_axes(axes_dist, axes_fwidth, 0.1);

		if ((gridFlag & AXIS_X) != 0) {
			FragColor.a = max(FragColor.a, axes.x);
			FragColor.rgb = (axes.x < 1e-8) ? FragColor.rgb : colorGridAxisX.rgb;
		}
		if ((gridFlag & AXIS_Y) != 0) {
			FragColor.a = max(FragColor.a, axes.y);
			FragColor.rgb = (axes.y < 1e-8) ? FragColor.rgb : colorGridAxisY.rgb;
		}
		if ((gridFlag & AXIS_Z) != 0) {
			FragColor.a = max(FragColor.a, axes.z);
			FragColor.rgb = (axes.z < 1e-8) ? FragColor.rgb : colorGridAxisZ.rgb;
		}
	}

	/* Add a small bias so the grid will always
	 * be on top of a mesh with the same depth. */
	float grid_depth = gl_FragCoord.z - 6e-8 - fwidth(gl_FragCoord.z);
	float scene_depth = texture(depthBuffer, sPos).r;
	if ((gridFlag & GRID_BACK) != 0) {
		fade *= (scene_depth == 1.0) ? 1.0 : 0.0;
	}
	else {
		/* Manual, non hard, depth test:
		 * Progressively fade the grid below occluders
		 * (avoids popping visuals due to depth buffer precision) */
		/* Harder settings tend to flicker more,
		 * but have less "see through" appearance. */
		const float test_hardness = 1e7;
		fade *= 1.0 - clamp((grid_depth - scene_depth) * test_hardness, 0.0, 1.0);
	}

	FragColor.a *= fade;
}
