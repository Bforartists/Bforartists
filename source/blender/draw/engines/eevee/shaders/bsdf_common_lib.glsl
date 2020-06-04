
#define M_PI 3.14159265358979323846     /* pi */
#define M_2PI 6.28318530717958647692    /* 2*pi */
#define M_PI_2 1.57079632679489661923   /* pi/2 */
#define M_1_PI 0.318309886183790671538  /* 1/pi */
#define M_1_2PI 0.159154943091895335768 /* 1/(2*pi) */
#define M_1_PI2 0.101321183642337771443 /* 1/(pi^2) */
#define FLT_MAX 3.402823e+38

#define LUT_SIZE 64

/* Buffers */
uniform sampler2D colorBuffer;
uniform sampler2D depthBuffer;
uniform sampler2D maxzBuffer;
uniform sampler2D minzBuffer;
uniform sampler2DArray planarDepth;

#define cameraForward ViewMatrixInverse[2].xyz
#define cameraPos ViewMatrixInverse[3].xyz
#define cameraVec \
  ((ProjectionMatrix[3][3] == 0.0) ? normalize(cameraPos - worldPosition) : cameraForward)
#define viewCameraVec \
  ((ProjectionMatrix[3][3] == 0.0) ? normalize(-viewPosition) : vec3(0.0, 0.0, 1.0))

/* ------- Structures -------- */

/* ------ Lights ----- */
struct LightData {
  vec4 position_influence;     /* w : InfluenceRadius (inversed and squared) */
  vec4 color_spec;             /* w : Spec Intensity */
  vec4 spotdata_radius_shadow; /* x : spot size, y : spot blend, z : radius, w: shadow id */
  vec4 rightvec_sizex;         /* xyz: Normalized up vector, w: area size X or spot scale X */
  vec4 upvec_sizey;            /* xyz: Normalized right vector, w: area size Y or spot scale Y */
  vec4 forwardvec_type;        /* xyz: Normalized forward vector, w: Light Type */
};

/* convenience aliases */
#define l_color color_spec.rgb
#define l_spec color_spec.a
#define l_position position_influence.xyz
#define l_influence position_influence.w
#define l_sizex rightvec_sizex.w
#define l_sizey upvec_sizey.w
#define l_right rightvec_sizex.xyz
#define l_up upvec_sizey.xyz
#define l_forward forwardvec_type.xyz
#define l_type forwardvec_type.w
#define l_spot_size spotdata_radius_shadow.x
#define l_spot_blend spotdata_radius_shadow.y
#define l_radius spotdata_radius_shadow.z
#define l_shadowid spotdata_radius_shadow.w

/* ------ Shadows ----- */
#ifndef MAX_CASCADE_NUM
#  define MAX_CASCADE_NUM 4
#endif

struct ShadowData {
  vec4 near_far_bias_id;
  vec4 contact_shadow_data;
};

struct ShadowCubeData {
  mat4 shadowmat;
  vec4 position;
};

struct ShadowCascadeData {
  mat4 shadowmat[MAX_CASCADE_NUM];
  vec4 split_start_distances;
  vec4 split_end_distances;
  vec4 shadow_vec_id;
};

/* convenience aliases */
#define sh_near near_far_bias_id.x
#define sh_far near_far_bias_id.y
#define sh_bias near_far_bias_id.z
#define sh_data_index near_far_bias_id.w
#define sh_contact_dist contact_shadow_data.x
#define sh_contact_offset contact_shadow_data.y
#define sh_contact_spread contact_shadow_data.z
#define sh_contact_thickness contact_shadow_data.w
#define sh_shadow_vec shadow_vec_id.xyz
#define sh_tex_index shadow_vec_id.w

/* ------ Render Passes ----- */
layout(std140) uniform renderpass_block
{
  bool renderPassDiffuse;
  bool renderPassDiffuseLight;
  bool renderPassGlossy;
  bool renderPassGlossyLight;
  bool renderPassEmit;
  bool renderPassSSSColor;
};

vec3 render_pass_diffuse_mask(vec3 diffuse_color, vec3 diffuse_light)
{
  return renderPassDiffuse ? (renderPassDiffuseLight ? diffuse_light : diffuse_color) : vec3(0.0);
}

vec3 render_pass_sss_mask(vec3 sss_color)
{
  return renderPassSSSColor ? sss_color : vec3(0.0);
}

vec3 render_pass_glossy_mask(vec3 specular_color, vec3 specular_light)
{
  return renderPassGlossy ? (renderPassGlossyLight ? specular_light : specular_color) : vec3(0.0);
}

vec3 render_pass_emission_mask(vec3 emission_light)
{
  return renderPassEmit ? emission_light : vec3(0.0);
}

/* ------- Convenience functions --------- */

vec3 mul(mat3 m, vec3 v)
{
  return m * v;
}
mat3 mul(mat3 m1, mat3 m2)
{
  return m1 * m2;
}
vec3 transform_direction(mat4 m, vec3 v)
{
  return mat3(m) * v;
}
vec3 transform_point(mat4 m, vec3 v)
{
  return (m * vec4(v, 1.0)).xyz;
}
vec3 project_point(mat4 m, vec3 v)
{
  vec4 tmp = m * vec4(v, 1.0);
  return tmp.xyz / tmp.w;
}

#define min3(a, b, c) min(a, min(b, c))
#define min4(a, b, c, d) min(a, min3(b, c, d))
#define min5(a, b, c, d, e) min(a, min4(b, c, d, e))
#define min6(a, b, c, d, e, f) min(a, min5(b, c, d, e, f))
#define min7(a, b, c, d, e, f, g) min(a, min6(b, c, d, e, f, g))
#define min8(a, b, c, d, e, f, g, h) min(a, min7(b, c, d, e, f, g, h))
#define min9(a, b, c, d, e, f, g, h, i) min(a, min8(b, c, d, e, f, g, h, i))

#define max3(a, b, c) max(a, max(b, c))
#define max4(a, b, c, d) max(a, max3(b, c, d))
#define max5(a, b, c, d, e) max(a, max4(b, c, d, e))
#define max6(a, b, c, d, e, f) max(a, max5(b, c, d, e, f))
#define max7(a, b, c, d, e, f, g) max(a, max6(b, c, d, e, f, g))
#define max8(a, b, c, d, e, f, g, h) max(a, max7(b, c, d, e, f, g, h))
#define max9(a, b, c, d, e, f, g, h, i) max(a, max8(b, c, d, e, f, g, h, i))

#define avg3(a, b, c) (a + b + c) * (1.0 / 3.0)
#define avg4(a, b, c, d) (a + b + c + d) * (1.0 / 4.0)
#define avg5(a, b, c, d, e) (a + b + c + d + e) * (1.0 / 5.0)
#define avg6(a, b, c, d, e, f) (a + b + c + d + e + f) * (1.0 / 6.0)
#define avg7(a, b, c, d, e, f, g) (a + b + c + d + e + f + g) * (1.0 / 7.0)
#define avg8(a, b, c, d, e, f, g, h) (a + b + c + d + e + f + g + h) * (1.0 / 8.0)
#define avg9(a, b, c, d, e, f, g, h, i) (a + b + c + d + e + f + g + h + i) * (1.0 / 9.0)

float min_v2(vec2 v)
{
  return min(v.x, v.y);
}
float min_v3(vec3 v)
{
  return min(v.x, min(v.y, v.z));
}
float min_v4(vec4 v)
{
  return min(min(v.x, v.y), min(v.z, v.w));
}
float max_v2(vec2 v)
{
  return max(v.x, v.y);
}
float max_v3(vec3 v)
{
  return max(v.x, max(v.y, v.z));
}
float max_v4(vec4 v)
{
  return max(max(v.x, v.y), max(v.z, v.w));
}

float sum(vec2 v)
{
  return dot(vec2(1.0), v);
}
float sum(vec3 v)
{
  return dot(vec3(1.0), v);
}
float sum(vec4 v)
{
  return dot(vec4(1.0), v);
}

float avg(vec2 v)
{
  return dot(vec2(1.0 / 2.0), v);
}
float avg(vec3 v)
{
  return dot(vec3(1.0 / 3.0), v);
}
float avg(vec4 v)
{
  return dot(vec4(1.0 / 4.0), v);
}

float saturate(float a)
{
  return clamp(a, 0.0, 1.0);
}
vec2 saturate(vec2 a)
{
  return clamp(a, 0.0, 1.0);
}
vec3 saturate(vec3 a)
{
  return clamp(a, 0.0, 1.0);
}
vec4 saturate(vec4 a)
{
  return clamp(a, 0.0, 1.0);
}

float distance_squared(vec2 a, vec2 b)
{
  a -= b;
  return dot(a, a);
}
float distance_squared(vec3 a, vec3 b)
{
  a -= b;
  return dot(a, a);
}
float len_squared(vec3 a)
{
  return dot(a, a);
}

float inverse_distance(vec3 V)
{
  return max(1 / length(V), 1e-8);
}

vec2 mip_ratio_interp(float mip)
{
  float low_mip = floor(mip);
  return mix(mipRatio[int(low_mip)], mipRatio[int(low_mip + 1.0)], mip - low_mip);
}

/* ------- RNG ------- */

float wang_hash_noise(uint s)
{
  s = (s ^ 61u) ^ (s >> 16u);
  s *= 9u;
  s = s ^ (s >> 4u);
  s *= 0x27d4eb2du;
  s = s ^ (s >> 15u);

  return fract(float(s) / 4294967296.0);
}

/* ------- Fast Math ------- */

/* [Drobot2014a] Low Level Optimizations for GCN */
float fast_sqrt(float v)
{
  return intBitsToFloat(0x1fbd1df5 + (floatBitsToInt(v) >> 1));
}

vec2 fast_sqrt(vec2 v)
{
  return intBitsToFloat(0x1fbd1df5 + (floatBitsToInt(v) >> 1));
}

/* [Eberly2014] GPGPU Programming for Games and Science */
float fast_acos(float v)
{
  float res = -0.156583 * abs(v) + M_PI_2;
  res *= fast_sqrt(1.0 - abs(v));
  return (v >= 0) ? res : M_PI - res;
}

vec2 fast_acos(vec2 v)
{
  vec2 res = -0.156583 * abs(v) + M_PI_2;
  res *= fast_sqrt(1.0 - abs(v));
  v.x = (v.x >= 0) ? res.x : M_PI - res.x;
  v.y = (v.y >= 0) ? res.y : M_PI - res.y;
  return v;
}

float point_plane_projection_dist(vec3 lineorigin, vec3 planeorigin, vec3 planenormal)
{
  return dot(planenormal, planeorigin - lineorigin);
}

float line_plane_intersect_dist(vec3 lineorigin,
                                vec3 linedirection,
                                vec3 planeorigin,
                                vec3 planenormal)
{
  return dot(planenormal, planeorigin - lineorigin) / dot(planenormal, linedirection);
}

float line_plane_intersect_dist(vec3 lineorigin, vec3 linedirection, vec4 plane)
{
  vec3 plane_co = plane.xyz * (-plane.w / len_squared(plane.xyz));
  vec3 h = lineorigin - plane_co;
  return -dot(plane.xyz, h) / dot(plane.xyz, linedirection);
}

vec3 line_plane_intersect(vec3 lineorigin, vec3 linedirection, vec3 planeorigin, vec3 planenormal)
{
  float dist = line_plane_intersect_dist(lineorigin, linedirection, planeorigin, planenormal);
  return lineorigin + linedirection * dist;
}

vec3 line_plane_intersect(vec3 lineorigin, vec3 linedirection, vec4 plane)
{
  float dist = line_plane_intersect_dist(lineorigin, linedirection, plane);
  return lineorigin + linedirection * dist;
}

float line_aligned_plane_intersect_dist(vec3 lineorigin, vec3 linedirection, vec3 planeorigin)
{
  /* aligned plane normal */
  vec3 L = planeorigin - lineorigin;
  float diskdist = length(L);
  vec3 planenormal = -normalize(L);
  return -diskdist / dot(planenormal, linedirection);
}

vec3 line_aligned_plane_intersect(vec3 lineorigin, vec3 linedirection, vec3 planeorigin)
{
  float dist = line_aligned_plane_intersect_dist(lineorigin, linedirection, planeorigin);
  if (dist < 0) {
    /* if intersection is behind we fake the intersection to be
     * really far and (hopefully) not inside the radius of interest */
    dist = 1e16;
  }
  return lineorigin + linedirection * dist;
}

float line_unit_sphere_intersect_dist(vec3 lineorigin, vec3 linedirection)
{
  float a = dot(linedirection, linedirection);
  float b = dot(linedirection, lineorigin);
  float c = dot(lineorigin, lineorigin) - 1;

  float dist = 1e15;
  float determinant = b * b - a * c;
  if (determinant >= 0) {
    dist = (sqrt(determinant) - b) / a;
  }

  return dist;
}

float line_unit_box_intersect_dist(vec3 lineorigin, vec3 linedirection)
{
  /* https://seblagarde.wordpress.com/2012/09/29/image-based-lighting-approaches-and-parallax-corrected-cubemap/
   */
  vec3 firstplane = (vec3(1.0) - lineorigin) / linedirection;
  vec3 secondplane = (vec3(-1.0) - lineorigin) / linedirection;
  vec3 furthestplane = max(firstplane, secondplane);

  return min_v3(furthestplane);
}

/* Return texture coordinates to sample Surface LUT */
vec2 lut_coords(float cosTheta, float roughness)
{
  float theta = acos(cosTheta);
  vec2 coords = vec2(roughness, theta / M_PI_2);

  /* scale and bias coordinates, for correct filtered lookup */
  return coords * (LUT_SIZE - 1.0) / LUT_SIZE + 0.5 / LUT_SIZE;
}

vec2 lut_coords_ltc(float cosTheta, float roughness)
{
  vec2 coords = vec2(roughness, sqrt(1.0 - cosTheta));

  /* scale and bias coordinates, for correct filtered lookup */
  return coords * (LUT_SIZE - 1.0) / LUT_SIZE + 0.5 / LUT_SIZE;
}

/* -- Tangent Space conversion -- */
vec3 tangent_to_world(vec3 vector, vec3 N, vec3 T, vec3 B)
{
  return T * vector.x + B * vector.y + N * vector.z;
}

vec3 world_to_tangent(vec3 vector, vec3 N, vec3 T, vec3 B)
{
  return vec3(dot(T, vector), dot(B, vector), dot(N, vector));
}

void make_orthonormal_basis(vec3 N, out vec3 T, out vec3 B)
{
  vec3 UpVector = abs(N.z) < 0.99999 ? vec3(0.0, 0.0, 1.0) : vec3(1.0, 0.0, 0.0);
  T = normalize(cross(UpVector, N));
  B = cross(N, T);
}

/* ---- Opengl Depth conversion ---- */

float linear_depth(bool is_persp, float z, float zf, float zn)
{
  if (is_persp) {
    return (zn * zf) / (z * (zn - zf) + zf);
  }
  else {
    return (z * 2.0 - 1.0) * zf;
  }
}

float buffer_depth(bool is_persp, float z, float zf, float zn)
{
  if (is_persp) {
    return (zf * (zn - z)) / (z * (zn - zf));
  }
  else {
    return (z / (zf * 2.0)) + 0.5;
  }
}

float get_view_z_from_depth(float depth)
{
  if (ProjectionMatrix[3][3] == 0.0) {
    float d = 2.0 * depth - 1.0;
    return -ProjectionMatrix[3][2] / (d + ProjectionMatrix[2][2]);
  }
  else {
    return viewVecs[0].z + depth * viewVecs[1].z;
  }
}

float get_depth_from_view_z(float z)
{
  if (ProjectionMatrix[3][3] == 0.0) {
    float d = (-ProjectionMatrix[3][2] / z) - ProjectionMatrix[2][2];
    return d * 0.5 + 0.5;
  }
  else {
    return (z - viewVecs[0].z) / viewVecs[1].z;
  }
}

vec2 get_uvs_from_view(vec3 view)
{
  vec3 ndc = project_point(ProjectionMatrix, view);
  return ndc.xy * 0.5 + 0.5;
}

vec3 get_view_space_from_depth(vec2 uvcoords, float depth)
{
  if (ProjectionMatrix[3][3] == 0.0) {
    return vec3(viewVecs[0].xy + uvcoords * viewVecs[1].xy, 1.0) * get_view_z_from_depth(depth);
  }
  else {
    return viewVecs[0].xyz + vec3(uvcoords, depth) * viewVecs[1].xyz;
  }
}

vec3 get_world_space_from_depth(vec2 uvcoords, float depth)
{
  return (ViewMatrixInverse * vec4(get_view_space_from_depth(uvcoords, depth), 1.0)).xyz;
}

vec3 get_specular_reflection_dominant_dir(vec3 N, vec3 V, float roughness)
{
  vec3 R = -reflect(V, N);
  float smoothness = 1.0 - roughness;
  float fac = smoothness * (sqrt(smoothness) + roughness);
  return normalize(mix(N, R, fac));
}

float specular_occlusion(float NV, float AO, float roughness)
{
  return saturate(pow(NV + AO, roughness) - 1.0 + AO);
}

/* --- Refraction utils --- */

float ior_from_f0(float f0)
{
  float f = sqrt(f0);
  return (-f - 1.0) / (f - 1.0);
}

float f0_from_ior(float eta)
{
  float A = (eta - 1.0) / (eta + 1.0);
  return A * A;
}

vec3 get_specular_refraction_dominant_dir(vec3 N, vec3 V, float roughness, float ior)
{
  /* TODO: This a bad approximation. Better approximation should fit
   * the refracted vector and roughness into the best prefiltered reflection
   * lobe. */
  /* Correct the IOR for ior < 1.0 to not see the abrupt delimitation or the TIR */
  ior = (ior < 1.0) ? mix(ior, 1.0, roughness) : ior;
  float eta = 1.0 / ior;

  float NV = dot(N, -V);

  /* Custom Refraction. */
  float k = 1.0 - eta * eta * (1.0 - NV * NV);
  k = max(0.0, k); /* Only this changes. */
  vec3 R = eta * -V - (eta * NV + sqrt(k)) * N;

  return R;
}

float get_btdf_lut(sampler2DArray btdf_lut_tex, float NV, float roughness, float ior)
{
  const vec3 lut_scale_bias_texel_size = vec3((LUT_SIZE - 1.0), 0.5, 1.5) / LUT_SIZE;

  vec3 coords;
  /* Try to compensate for the low resolution and interpolation error. */
  coords.x = (ior > 1.0) ? (0.9 + lut_scale_bias_texel_size.z) +
                               (0.1 - lut_scale_bias_texel_size.z) * f0_from_ior(ior) :
                           (0.9 + lut_scale_bias_texel_size.z) * ior * ior;
  coords.y = 1.0 - saturate(NV);
  coords.xy *= lut_scale_bias_texel_size.x;
  coords.xy += lut_scale_bias_texel_size.y;

  const float lut_lvl_ofs = 4.0;    /* First texture lvl of roughness. */
  const float lut_lvl_scale = 16.0; /* How many lvl of roughness in the lut. */

  float mip = roughness * lut_lvl_scale;
  float mip_floor = floor(mip);

  coords.z = lut_lvl_ofs + mip_floor + 1.0;
  float btdf_high = textureLod(btdf_lut_tex, coords, 0.0).r;

  coords.z -= 1.0;
  float btdf_low = textureLod(btdf_lut_tex, coords, 0.0).r;

  float btdf = (ior == 1.0) ? 1.0 : mix(btdf_low, btdf_high, mip - coords.z);

  return btdf;
}

/* ---- Encode / Decode Normal buffer data ---- */
/* From http://aras-p.info/texts/CompactNormalStorage.html
 * Using Method #4: Spheremap Transform */
vec2 normal_encode(vec3 n, vec3 view)
{
  float p = sqrt(n.z * 8.0 + 8.0);
  return n.xy / p + 0.5;
}

vec3 normal_decode(vec2 enc, vec3 view)
{
  vec2 fenc = enc * 4.0 - 2.0;
  float f = dot(fenc, fenc);
  float g = sqrt(1.0 - f / 4.0);
  vec3 n;
  n.xy = fenc * g;
  n.z = 1 - f / 2;
  return n;
}

/* ---- RGBM (shared multiplier) encoding ---- */
/* From http://iwasbeingirony.blogspot.fr/2010/06/difference-between-rgbm-and-rgbd.html */

/* Higher RGBM_MAX_RANGE gives imprecision issues in low intensity. */
#define RGBM_MAX_RANGE 512.0

vec4 rgbm_encode(vec3 rgb)
{
  float maxRGB = max_v3(rgb);
  float M = maxRGB / RGBM_MAX_RANGE;
  M = ceil(M * 255.0) / 255.0;
  return vec4(rgb / (M * RGBM_MAX_RANGE), M);
}

vec3 rgbm_decode(vec4 data)
{
  return data.rgb * (data.a * RGBM_MAX_RANGE);
}

/* ---- RGBE (shared exponent) encoding ---- */
vec4 rgbe_encode(vec3 rgb)
{
  float maxRGB = max_v3(rgb);
  float fexp = ceil(log2(maxRGB));
  return vec4(rgb / exp2(fexp), (fexp + 128.0) / 255.0);
}

vec3 rgbe_decode(vec4 data)
{
  float fexp = data.a * 255.0 - 128.0;
  return data.rgb * exp2(fexp);
}

#if 1
#  define irradiance_encode rgbe_encode
#  define irradiance_decode rgbe_decode
#else /* No ecoding (when using floating point format) */
#  define irradiance_encode(X) (X).rgbb
#  define irradiance_decode(X) (X).rgb
#endif

/* Irradiance Visibility Encoding */
#if 1
vec4 visibility_encode(vec2 accum, float range)
{
  accum /= range;

  vec4 data;
  data.x = fract(accum.x);
  data.y = floor(accum.x) / 255.0;
  data.z = fract(accum.y);
  data.w = floor(accum.y) / 255.0;

  return data;
}

vec2 visibility_decode(vec4 data, float range)
{
  return (data.xz + data.yw * 255.0) * range;
}
#else /* No ecoding (when using floating point format) */
vec4 visibility_encode(vec2 accum, float range)
{
  return accum.xyxy;
}

vec2 visibility_decode(vec4 data, float range)
{
  return data.xy;
}
#endif

/* Fresnel monochromatic, perfect mirror */
float F_eta(float eta, float cos_theta)
{
  /* compute fresnel reflectance without explicitly computing
   * the refracted direction */
  float c = abs(cos_theta);
  float g = eta * eta - 1.0 + c * c;
  float result;

  if (g > 0.0) {
    g = sqrt(g);
    vec2 g_c = vec2(g) + vec2(c, -c);
    float A = g_c.y / g_c.x;
    A *= A;
    g_c *= c;
    float B = (g_c.y - 1.0) / (g_c.x + 1.0);
    B *= B;
    result = 0.5 * A * (1.0 + B);
  }
  else {
    result = 1.0; /* TIR (no refracted component) */
  }

  return result;
}

/* Fresnel color blend base on fresnel factor */
vec3 F_color_blend(float eta, float fresnel, vec3 f0_color)
{
  float f0 = F_eta(eta, 1.0);
  float fac = saturate((fresnel - f0) / max(1e-8, 1.0 - f0));
  return mix(f0_color, vec3(1.0), fac);
}

/* Fresnel */
vec3 F_schlick(vec3 f0, float cos_theta)
{
  float fac = 1.0 - cos_theta;
  float fac2 = fac * fac;
  fac = fac2 * fac2 * fac;

  /* Unreal specular matching : if specular color is below 2% intensity,
   * (using green channel for intensity) treat as shadowning */
  return saturate(50.0 * dot(f0, vec3(0.3, 0.6, 0.1))) * fac + (1.0 - fac) * f0;
}

/* Fresnel approximation for LTC area lights (not MRP) */
vec3 F_area(vec3 f0, vec3 f90, vec2 lut)
{
  /* Unreal specular matching : if specular color is below 2% intensity,
   * treat as shadowning */
  return saturate(50.0 * dot(f0, vec3(0.3, 0.6, 0.1))) * lut.y * f90 + lut.x * f0;
}

/* Fresnel approximation for IBL */
vec3 F_ibl(vec3 f0, vec3 f90, vec2 lut)
{
  /* Unreal specular matching : if specular color is below 2% intensity,
   * treat as shadowning */
  return saturate(50.0 * dot(f0, vec3(0.3, 0.6, 0.1))) * lut.y * f90 + lut.x * f0;
}

/* GGX */
float D_ggx_opti(float NH, float a2)
{
  float tmp = (NH * a2 - NH) * NH + 1.0;
  return M_PI * tmp * tmp; /* Doing RCP and mul a2 at the end */
}

float G1_Smith_GGX(float NX, float a2)
{
  /* Using Brian Karis approach and refactoring by NX/NX
   * this way the (2*NL)*(2*NV) in G = G1(V) * G1(L) gets canceled by the brdf denominator 4*NL*NV
   * Rcp is done on the whole G later
   * Note that this is not convenient for the transmission formula */
  return NX + sqrt(NX * (NX - NX * a2) + a2);
  /* return 2 / (1 + sqrt(1 + a2 * (1 - NX*NX) / (NX*NX) ) ); /* Reference function */
}

float bsdf_ggx(vec3 N, vec3 L, vec3 V, float roughness)
{
  float a = roughness;
  float a2 = a * a;

  vec3 H = normalize(L + V);
  float NH = max(dot(N, H), 1e-8);
  float NL = max(dot(N, L), 1e-8);
  float NV = max(dot(N, V), 1e-8);

  float G = G1_Smith_GGX(NV, a2) * G1_Smith_GGX(NL, a2); /* Doing RCP at the end */
  float D = D_ggx_opti(NH, a2);

  /* Denominator is canceled by G1_Smith */
  /* bsdf = D * G / (4.0 * NL * NV); /* Reference function */
  return NL * a2 / (D * G); /* NL to Fit cycles Equation : line. 345 in bsdf_microfacet.h */
}

void accumulate_light(vec3 light, float fac, inout vec4 accum)
{
  accum += vec4(light, 1.0) * min(fac, (1.0 - accum.a));
}

/* ----------- Cone Aperture Approximation --------- */

/* Return a fitted cone angle given the input roughness */
float cone_cosine(float r)
{
  /* Using phong gloss
   * roughness = sqrt(2/(gloss+2)) */
  float gloss = -2 + 2 / (r * r);
  /* Drobot 2014 in GPUPro5 */
  // return cos(2.0 * sqrt(2.0 / (gloss + 2)));
  /* Uludag 2014 in GPUPro5 */
  // return pow(0.244, 1 / (gloss + 1));
  /* Jimenez 2016 in Practical Realtime Strategies for Accurate Indirect Occlusion*/
  return exp2(-3.32193 * r * r);
}

/* --------- Closure ---------- */

#ifdef VOLUMETRICS

struct Closure {
  vec3 absorption;
  vec3 scatter;
  vec3 emission;
  float anisotropy;
};

Closure nodetree_exec(void); /* Prototype */

#  define CLOSURE_DEFAULT Closure(vec3(0.0), vec3(0.0), vec3(0.0), 0.0)

Closure closure_mix(Closure cl1, Closure cl2, float fac)
{
  Closure cl;
  cl.absorption = mix(cl1.absorption, cl2.absorption, fac);
  cl.scatter = mix(cl1.scatter, cl2.scatter, fac);
  cl.emission = mix(cl1.emission, cl2.emission, fac);
  cl.anisotropy = mix(cl1.anisotropy, cl2.anisotropy, fac);
  return cl;
}

Closure closure_add(Closure cl1, Closure cl2)
{
  Closure cl;
  cl.absorption = cl1.absorption + cl2.absorption;
  cl.scatter = cl1.scatter + cl2.scatter;
  cl.emission = cl1.emission + cl2.emission;
  cl.anisotropy = (cl1.anisotropy + cl2.anisotropy) / 2.0; /* Average phase (no multi lobe) */
  return cl;
}

Closure closure_emission(vec3 rgb)
{
  Closure cl = CLOSURE_DEFAULT;
  cl.emission = rgb;
  return cl;
}

#else /* VOLUMETRICS */

struct Closure {
  vec3 radiance;
  vec3 transmittance;
  float holdout;
#  ifdef USE_SSS
  vec3 sss_irradiance;
  vec3 sss_albedo;
  float sss_radius;
#  endif
  vec4 ssr_data;
  vec2 ssr_normal;
  int flag;
};

Closure nodetree_exec(void); /* Prototype */

#  define FLAG_TEST(flag, val) (((flag) & (val)) != 0)

#  define CLOSURE_SSR_FLAG 1
#  define CLOSURE_SSS_FLAG 2
#  define CLOSURE_HOLDOUT_FLAG 4

#  ifdef USE_SSS
#    define CLOSURE_DEFAULT \
      Closure(vec3(0.0), vec3(0.0), 0.0, vec3(0.0), vec3(0.0), 0.0, vec4(0.0), vec2(0.0), 0)
#  else
#    define CLOSURE_DEFAULT Closure(vec3(0.0), vec3(0.0), 0.0, vec4(0.0), vec2(0.0), 0)
#  endif

uniform int outputSsrId = 1;
uniform int outputSssId = 1;

void closure_load_ssr_data(
    vec3 ssr_spec, float roughness, vec3 N, vec3 viewVec, int ssr_id, inout Closure cl)
{
  /* Still encode to avoid artifacts in the SSR pass. */
  vec3 vN = normalize(mat3(ViewMatrix) * N);
  cl.ssr_normal = normal_encode(vN, viewVec);

  if (ssr_id == outputSsrId) {
    cl.ssr_data = vec4(ssr_spec, roughness);
    cl.flag |= CLOSURE_SSR_FLAG;
  }
}

void closure_load_sss_data(
    float radius, vec3 sss_irradiance, vec3 sss_albedo, int sss_id, inout Closure cl)
{
#  ifdef USE_SSS
  if (sss_id == outputSssId) {
    cl.sss_irradiance = sss_irradiance;
    cl.sss_radius = radius;
    cl.sss_albedo = sss_albedo;
    cl.flag |= CLOSURE_SSS_FLAG;
    cl.radiance += render_pass_diffuse_mask(sss_albedo, vec3(0));
  }
  else
#  endif
  {
    cl.radiance += render_pass_diffuse_mask(sss_albedo, sss_irradiance * sss_albedo);
  }
}

Closure closure_mix(Closure cl1, Closure cl2, float fac)
{
  Closure cl;
  cl.holdout = mix(cl1.holdout, cl2.holdout, fac);
  cl.transmittance = mix(cl1.transmittance, cl2.transmittance, fac);
  cl.radiance = mix(cl1.radiance, cl2.radiance, fac);
  cl.flag = cl1.flag | cl2.flag;
  cl.ssr_data = mix(cl1.ssr_data, cl2.ssr_data, fac);
  bool use_cl1_ssr = FLAG_TEST(cl1.flag, CLOSURE_SSR_FLAG);
  /* When mixing SSR don't blend roughness and normals but only specular (ssr_data.xyz).*/
  cl.ssr_data.w = (use_cl1_ssr) ? cl1.ssr_data.w : cl2.ssr_data.w;
  cl.ssr_normal = (use_cl1_ssr) ? cl1.ssr_normal : cl2.ssr_normal;

#  ifdef USE_SSS
  cl.sss_albedo = mix(cl1.sss_albedo, cl2.sss_albedo, fac);
  bool use_cl1_sss = FLAG_TEST(cl1.flag, CLOSURE_SSS_FLAG);
  /* It also does not make sense to mix SSS radius or irradiance. */
  cl.sss_radius = (use_cl1_sss) ? cl1.sss_radius : cl2.sss_radius;
  cl.sss_irradiance = (use_cl1_sss) ? cl1.sss_irradiance : cl2.sss_irradiance;
#  endif
  return cl;
}

Closure closure_add(Closure cl1, Closure cl2)
{
  Closure cl;
  cl.transmittance = cl1.transmittance + cl2.transmittance;
  cl.radiance = cl1.radiance + cl2.radiance;
  cl.holdout = cl1.holdout + cl2.holdout;
  cl.flag = cl1.flag | cl2.flag;
  cl.ssr_data = cl1.ssr_data + cl2.ssr_data;
  bool use_cl1_ssr = FLAG_TEST(cl1.flag, CLOSURE_SSR_FLAG);
  /* When mixing SSR don't blend roughness and normals.*/
  cl.ssr_data.w = (use_cl1_ssr) ? cl1.ssr_data.w : cl2.ssr_data.w;
  cl.ssr_normal = (use_cl1_ssr) ? cl1.ssr_normal : cl2.ssr_normal;

#  ifdef USE_SSS
  cl.sss_albedo = cl1.sss_albedo + cl2.sss_albedo;
  bool use_cl1_sss = FLAG_TEST(cl1.flag, CLOSURE_SSS_FLAG);
  /* It also does not make sense to mix SSS radius or irradiance. */
  cl.sss_radius = (use_cl1_sss) ? cl1.sss_radius : cl2.sss_radius;
  cl.sss_irradiance = (use_cl1_sss) ? cl1.sss_irradiance : cl2.sss_irradiance;
#  endif
  return cl;
}

Closure closure_emission(vec3 rgb)
{
  Closure cl = CLOSURE_DEFAULT;
  cl.radiance = rgb;
  return cl;
}

/* Breaking this across multiple lines causes issues for some older GLSL compilers. */
/* clang-format off */
#  if defined(MESH_SHADER) && !defined(DEPTH_SHADER)
/* clang-format on */
#    ifndef USE_ALPHA_BLEND
layout(location = 0) out vec4 outRadiance;
layout(location = 1) out vec2 ssrNormals;
layout(location = 2) out vec4 ssrData;
#      ifdef USE_SSS
layout(location = 3) out vec3 sssIrradiance;
layout(location = 4) out float sssRadius;
layout(location = 5) out vec3 sssAlbedo;
#      endif
#    else  /* USE_ALPHA_BLEND */
/* Use dual source blending to be able to make a whole range of effects. */
layout(location = 0, index = 0) out vec4 outRadiance;
layout(location = 0, index = 1) out vec4 outTransmittance;
#    endif /* USE_ALPHA_BLEND */

#    if defined(USE_ALPHA_BLEND)
/* Prototype because this file is included before volumetric_lib.glsl */
void volumetric_resolve(vec2 frag_uvs,
                        float frag_depth,
                        out vec3 transmittance,
                        out vec3 scattering);
#    endif

#    define NODETREE_EXEC
void main()
{
  Closure cl = nodetree_exec();

  float holdout = 1.0 - saturate(cl.holdout);
  float transmit = saturate(avg(cl.transmittance));
  float alpha = 1.0 - transmit;

#    ifdef USE_ALPHA_BLEND
  vec2 uvs = gl_FragCoord.xy * volCoordScale.zw;
  vec3 vol_transmit, vol_scatter;
  volumetric_resolve(uvs, gl_FragCoord.z, vol_transmit, vol_scatter);

  /* Removes part of the volume scattering that have
   * already been added to the destination pixels.
   * Since we do that using the blending pipeline we need to account for material transmittance. */
  vol_scatter -= vol_scatter * cl.transmittance;

  outRadiance = vec4(cl.radiance * vol_transmit + vol_scatter, alpha * holdout);
  outTransmittance = vec4(cl.transmittance, transmit * holdout);
#    else
  outRadiance = vec4(cl.radiance, holdout);
  ssrNormals = cl.ssr_normal;
  ssrData = cl.ssr_data;
#      ifdef USE_SSS
  sssIrradiance = cl.sss_irradiance;
  sssRadius = cl.sss_radius;
  sssAlbedo = cl.sss_albedo;
#      endif
#    endif

  /* For Probe capture */
#    ifdef USE_SSS
  float fac = float(!sssToggle);

  /* TODO(fclem) we shouldn't need this.
   * Just disable USE_SSS when USE_REFRACTION is enabled. */
#      ifdef USE_REFRACTION
  /* SSRefraction pass is done after the SSS pass.
   * In order to not loose the diffuse light totally we
   * need to merge the SSS radiance to the main radiance. */
  fac = 1.0;
#      endif

  outRadiance.rgb += cl.sss_irradiance.rgb * cl.sss_albedo.rgb * fac;
#    endif

#    ifdef LOOKDEV
  gl_FragDepth = 0.0;
#    endif

#    ifndef USE_ALPHA_BLEND
  float alpha_div = 1.0 / max(1e-8, alpha);
  outRadiance.rgb *= alpha_div;
  ssrData.rgb *= alpha_div;
#      ifdef USE_SSS
  sssAlbedo.rgb *= alpha_div;
#      endif
#    endif
}

#  endif /* MESH_SHADER */

#endif /* VOLUMETRICS */
