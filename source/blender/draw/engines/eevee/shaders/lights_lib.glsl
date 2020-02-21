
uniform sampler2DArrayShadow shadowCubeTexture;
uniform sampler2DArrayShadow shadowCascadeTexture;

#define LAMPS_LIB

layout(std140) uniform shadow_block
{
  ShadowData shadows_data[MAX_SHADOW];
  ShadowCubeData shadows_cube_data[MAX_SHADOW_CUBE];
  ShadowCascadeData shadows_cascade_data[MAX_SHADOW_CASCADE];
};

layout(std140) uniform light_block
{
  LightData lights_data[MAX_LIGHT];
};

/* type */
#define POINT 0.0
#define SUN 1.0
#define SPOT 2.0
#define AREA_RECT 4.0
/* Used to define the area light shape, doesn't directly correspond to a Blender light type. */
#define AREA_ELLIPSE 100.0

float cubeFaceIndexEEVEE(vec3 P)
{
  vec3 aP = abs(P);
  if (all(greaterThan(aP.xx, aP.yz))) {
    return (P.x > 0.0) ? 0.0 : 1.0;
  }
  else if (all(greaterThan(aP.yy, aP.xz))) {
    return (P.y > 0.0) ? 2.0 : 3.0;
  }
  else {
    return (P.z > 0.0) ? 4.0 : 5.0;
  }
}

vec2 cubeFaceCoordEEVEE(vec3 P, float face, float scale)
{
  if (face < 2.0) {
    return (P.zy / P.x) * scale * vec2(-0.5, -sign(P.x) * 0.5) + 0.5;
  }
  else if (face < 4.0) {
    return (P.xz / P.y) * scale * vec2(sign(P.y) * 0.5, 0.5) + 0.5;
  }
  else {
    return (P.xy / P.z) * scale * vec2(0.5, -sign(P.z) * 0.5) + 0.5;
  }
}

vec2 cubeFaceCoordEEVEE(vec3 P, float face, sampler2DArray tex)
{
  /* Scaling to compensate the 1px border around the face. */
  float cube_res = float(textureSize(tex, 0).x);
  float scale = (cube_res) / (cube_res + 1.0);
  return cubeFaceCoordEEVEE(P, face, scale);
}

vec2 cubeFaceCoordEEVEE(vec3 P, float face, sampler2DArrayShadow tex)
{
  /* Scaling to compensate the 1px border around the face. */
  float cube_res = float(textureSize(tex, 0).x);
  float scale = (cube_res) / (cube_res + 1.0);
  return cubeFaceCoordEEVEE(P, face, scale);
}

vec4 sample_cube(sampler2DArray tex, vec3 cubevec, float cube)
{
  /* Manual Shadow Cube Layer indexing. */
  float face = cubeFaceIndexEEVEE(cubevec);
  vec2 uv = cubeFaceCoordEEVEE(cubevec, face, tex);

  vec3 coord = vec3(uv, cube * 6.0 + face);
  return texture(tex, coord);
}

vec4 sample_cascade(sampler2DArray tex, vec2 co, float cascade_id)
{
  return texture(tex, vec3(co, cascade_id));
}

/* Some driver poorly optimize this code. Use direct reference to matrices. */
#define sd(x) shadows_data[x]
#define scube(x) shadows_cube_data[x]
#define scascade(x) shadows_cascade_data[x]

float sample_cube_shadow(int shadow_id, vec3 W)
{
  int data_id = int(sd(shadow_id).sh_data_index);
  vec3 cubevec = transform_point(scube(data_id).shadowmat, W);
  float dist = max(sd(shadow_id).sh_near, max_v3(abs(cubevec)) - sd(shadow_id).sh_bias);
  dist = buffer_depth(true, dist, sd(shadow_id).sh_far, sd(shadow_id).sh_near);
  /* Manual Shadow Cube Layer indexing. */
  /* TODO Shadow Cube Array. */
  float face = cubeFaceIndexEEVEE(cubevec);
  vec2 coord = cubeFaceCoordEEVEE(cubevec, face, shadowCubeTexture);
  /* tex_id == data_id for cube shadowmap */
  float tex_id = float(data_id);
  return texture(shadowCubeTexture, vec4(coord, tex_id * 6.0 + face, dist));
}

float sample_cascade_shadow(int shadow_id, vec3 W)
{
  int data_id = int(sd(shadow_id).sh_data_index);
  float tex_id = scascade(data_id).sh_tex_index;
  vec4 view_z = vec4(dot(W - cameraPos, cameraForward));
  vec4 weights = 1.0 - smoothstep(scascade(data_id).split_end_distances,
                                  scascade(data_id).split_start_distances.yzwx,
                                  view_z);
  float tot_weight = dot(weights.xyz, vec3(1.0));

  int cascade = int(clamp(tot_weight, 0.0, 3.0));
  float blend = fract(tot_weight);
  float vis = weights.w;
  vec4 coord, shpos;
  /* Main cascade. */
  shpos = scascade(data_id).shadowmat[cascade] * vec4(W, 1.0);
  coord = vec4(shpos.xy, tex_id + float(cascade), shpos.z - sd(shadow_id).sh_bias);
  vis += texture(shadowCascadeTexture, coord) * (1.0 - blend);

  cascade = min(3, cascade + 1);
  /* Second cascade. */
  shpos = scascade(data_id).shadowmat[cascade] * vec4(W, 1.0);
  coord = vec4(shpos.xy, tex_id + float(cascade), shpos.z - sd(shadow_id).sh_bias);
  vis += texture(shadowCascadeTexture, coord) * blend;

  return saturate(vis);
}
#undef sd
#undef scube
#undef scsmd

/* ----------------------------------------------------------- */
/* --------------------- Light Functions --------------------- */
/* ----------------------------------------------------------- */

/* From Frostbite PBR Course
 * Distance based attenuation
 * http://www.frostbite.com/wp-content/uploads/2014/11/course_notes_moving_frostbite_to_pbr.pdf */
float distance_attenuation(float dist_sqr, float inv_sqr_influence)
{
  float factor = dist_sqr * inv_sqr_influence;
  float fac = saturate(1.0 - factor * factor);
  return fac * fac;
}

float spot_attenuation(LightData ld, vec3 l_vector)
{
  float z = dot(ld.l_forward, l_vector.xyz);
  vec3 lL = l_vector.xyz / z;
  float x = dot(ld.l_right, lL) / ld.l_sizex;
  float y = dot(ld.l_up, lL) / ld.l_sizey;
  float ellipse = inversesqrt(1.0 + x * x + y * y);
  float spotmask = smoothstep(0.0, 1.0, (ellipse - ld.l_spot_size) / ld.l_spot_blend);
  return spotmask;
}

float light_attenuation(LightData ld, vec4 l_vector)
{
  float vis = 1.0;
  if (ld.l_type == SPOT) {
    vis *= spot_attenuation(ld, l_vector.xyz);
  }
  if (ld.l_type >= SPOT) {
    vis *= step(0.0, -dot(l_vector.xyz, ld.l_forward));
  }
  if (ld.l_type != SUN) {
    vis *= distance_attenuation(l_vector.w * l_vector.w, ld.l_influence);
  }
  return vis;
}

float light_shadowing(LightData ld,
                      vec3 W,
#ifndef VOLUMETRICS
                      vec3 viewPosition,
                      float tracing_depth,
                      vec3 true_normal,
                      float rand_x,
                      const bool use_contact_shadows,
#endif
                      float vis)
{
#if !defined(VOLUMETRICS) || defined(VOLUME_SHADOW)
  /* shadowing */
  if (ld.l_shadowid >= 0.0 && vis > 0.001) {

    if (ld.l_type == SUN) {
      vis *= sample_cascade_shadow(int(ld.l_shadowid), W);
    }
    else {
      vis *= sample_cube_shadow(int(ld.l_shadowid), W);
    }

#  ifndef VOLUMETRICS
    ShadowData sd = shadows_data[int(ld.l_shadowid)];
    /* Only compute if not already in shadow. */
    if (use_contact_shadows && sd.sh_contact_dist > 0.0 && vis > 1e-8) {
      /* Contact Shadows. */
      vec3 ray_ori, ray_dir;
      float trace_distance;

      if (ld.l_type == SUN) {
        trace_distance = sd.sh_contact_dist;
        ray_dir = shadows_cascade_data[int(sd.sh_data_index)].sh_shadow_vec * trace_distance;
      }
      else {
        ray_dir = shadows_cube_data[int(sd.sh_data_index)].position.xyz - W;
        float len = length(ray_dir);
        trace_distance = min(sd.sh_contact_dist, len);
        ray_dir *= trace_distance / len;
      }

      ray_dir = transform_direction(ViewMatrix, ray_dir);
      ray_ori = vec3(viewPosition.xy, tracing_depth) + true_normal * sd.sh_contact_offset;

      vec3 hit_pos = raycast(
          -1, ray_ori, ray_dir, sd.sh_contact_thickness, rand_x, 0.1, 0.001, false);

      if (hit_pos.z > 0.0) {
        hit_pos = get_view_space_from_depth(hit_pos.xy, hit_pos.z);
        float hit_dist = distance(viewPosition, hit_pos);
        float dist_ratio = hit_dist / trace_distance;
        return vis * saturate(dist_ratio * 3.0 - 2.0);
      }
    }
#  endif /* VOLUMETRICS */
  }
#endif

  return vis;
}

float light_visibility(LightData ld,
                       vec3 W,
#ifndef VOLUMETRICS
                       vec3 viewPosition,
                       float tracing_depth,
                       vec3 true_normal,
                       float rand_x,
                       const bool use_contact_shadows,
#endif
                       vec4 l_vector)
{
  float l_atten = light_attenuation(ld, l_vector);
  return light_shadowing(ld,
                         W,
#ifndef VOLUMETRICS
                         viewPosition,
                         tracing_depth,
                         true_normal,
                         rand_x,
                         use_contact_shadows,
#endif
                         l_atten);
}

#ifdef USE_LTC
float light_diffuse(LightData ld, vec3 N, vec3 V, vec4 l_vector)
{
  if (ld.l_type == AREA_RECT) {
    vec3 corners[4];
    corners[0] = normalize((l_vector.xyz + ld.l_right * -ld.l_sizex) + ld.l_up * ld.l_sizey);
    corners[1] = normalize((l_vector.xyz + ld.l_right * -ld.l_sizex) + ld.l_up * -ld.l_sizey);
    corners[2] = normalize((l_vector.xyz + ld.l_right * ld.l_sizex) + ld.l_up * -ld.l_sizey);
    corners[3] = normalize((l_vector.xyz + ld.l_right * ld.l_sizex) + ld.l_up * ld.l_sizey);

    return ltc_evaluate_quad(corners, N);
  }
  else if (ld.l_type == AREA_ELLIPSE) {
    vec3 points[3];
    points[0] = (l_vector.xyz + ld.l_right * -ld.l_sizex) + ld.l_up * -ld.l_sizey;
    points[1] = (l_vector.xyz + ld.l_right * ld.l_sizex) + ld.l_up * -ld.l_sizey;
    points[2] = (l_vector.xyz + ld.l_right * ld.l_sizex) + ld.l_up * ld.l_sizey;

    return ltc_evaluate_disk(N, V, mat3(1.0), points);
  }
  else {
    float radius = ld.l_radius;
    radius /= (ld.l_type == SUN) ? 1.0 : l_vector.w;
    vec3 L = (ld.l_type == SUN) ? -ld.l_forward : (l_vector.xyz / l_vector.w);

    return ltc_evaluate_disk_simple(radius, dot(N, L));
  }
}

float light_specular(LightData ld, vec4 ltc_mat, vec3 N, vec3 V, vec4 l_vector)
{
  if (ld.l_type == AREA_RECT) {
    vec3 corners[4];
    corners[0] = (l_vector.xyz + ld.l_right * -ld.l_sizex) + ld.l_up * ld.l_sizey;
    corners[1] = (l_vector.xyz + ld.l_right * -ld.l_sizex) + ld.l_up * -ld.l_sizey;
    corners[2] = (l_vector.xyz + ld.l_right * ld.l_sizex) + ld.l_up * -ld.l_sizey;
    corners[3] = (l_vector.xyz + ld.l_right * ld.l_sizex) + ld.l_up * ld.l_sizey;

    ltc_transform_quad(N, V, ltc_matrix(ltc_mat), corners);

    return ltc_evaluate_quad(corners, vec3(0.0, 0.0, 1.0));
  }
  else {
    bool is_ellipse = (ld.l_type == AREA_ELLIPSE);
    float radius_x = is_ellipse ? ld.l_sizex : ld.l_radius;
    float radius_y = is_ellipse ? ld.l_sizey : ld.l_radius;

    vec3 L = (ld.l_type == SUN) ? -ld.l_forward : l_vector.xyz;
    vec3 Px = ld.l_right;
    vec3 Py = ld.l_up;

    if (ld.l_type == SPOT || ld.l_type == POINT) {
      make_orthonormal_basis(l_vector.xyz / l_vector.w, Px, Py);
    }

    vec3 points[3];
    points[0] = (L + Px * -radius_x) + Py * -radius_y;
    points[1] = (L + Px * radius_x) + Py * -radius_y;
    points[2] = (L + Px * radius_x) + Py * radius_y;

    return ltc_evaluate_disk(N, V, ltc_matrix(ltc_mat), points);
  }
}
#endif
