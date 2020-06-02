/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2006 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup gpu
 *
 * Manages materials, lights and textures.
 */

#include <math.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "DNA_material_types.h"
#include "DNA_scene_types.h"
#include "DNA_world_types.h"

#include "BLI_ghash.h"
#include "BLI_listbase.h"
#include "BLI_math.h"
#include "BLI_string.h"
#include "BLI_string_utils.h"
#include "BLI_utildefines.h"

#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_node.h"
#include "BKE_scene.h"

#include "GPU_material.h"
#include "GPU_shader.h"
#include "GPU_texture.h"
#include "GPU_uniformbuffer.h"

#include "DRW_engine.h"

#include "gpu_codegen.h"
#include "gpu_node_graph.h"

/* Structs */
#define MAX_COLOR_BAND 128

typedef struct GPUColorBandBuilder {
  float pixels[MAX_COLOR_BAND][CM_TABLE + 1][4];
  int current_layer;
} GPUColorBandBuilder;

struct GPUMaterial {
  Scene *scene; /* DEPRECATED was only useful for lights. */
  Material *ma;

  eGPUMaterialStatus status;

  const void *engine_type; /* attached engine type */
  int options;             /* to identify shader variations (shadow, probe, world background...) */
  bool is_volume_shader;   /* is volumetric shader */

  /* Nodes */
  GPUNodeGraph graph;

  /* for binding the material */
  GPUPass *pass;

  /* XXX: Should be in Material. But it depends on the output node
   * used and since the output selection is different for GPUMaterial...
   */
  bool has_volume_output;
  bool has_surface_output;

  /* Only used by Eevee to know which bsdf are used. */
  int flag;

  /* Used by 2.8 pipeline */
  GPUUniformBuffer *ubo; /* UBOs for shader uniforms. */

  /* Eevee SSS */
  GPUUniformBuffer *sss_profile; /* UBO containing SSS profile. */
  GPUTexture *sss_tex_profile;   /* Texture containing SSS profile. */
  float sss_enabled;
  float sss_radii[3];
  int sss_samples;
  short int sss_falloff;
  float sss_sharpness;
  bool sss_dirty;

  GPUTexture *coba_tex; /* 1D Texture array containing all color bands. */
  GPUColorBandBuilder *coba_builder;

  GSet *used_libraries;

#ifndef NDEBUG
  char name[64];
#endif
};

enum {
  GPU_USE_SURFACE_OUTPUT = (1 << 0),
  GPU_USE_VOLUME_OUTPUT = (1 << 1),
};

/* Functions */

/* Returns the address of the future pointer to coba_tex */
GPUTexture **gpu_material_ramp_texture_row_set(GPUMaterial *mat,
                                               int size,
                                               float *pixels,
                                               float *row)
{
  /* In order to put all the colorbands into one 1D array texture,
   * we need them to be the same size. */
  BLI_assert(size == CM_TABLE + 1);
  UNUSED_VARS_NDEBUG(size);

  if (mat->coba_builder == NULL) {
    mat->coba_builder = MEM_mallocN(sizeof(GPUColorBandBuilder), "GPUColorBandBuilder");
    mat->coba_builder->current_layer = 0;
  }

  int layer = mat->coba_builder->current_layer;
  *row = (float)layer;

  if (*row == MAX_COLOR_BAND) {
    printf("Too many color band in shader! Remove some Curve, Black Body or Color Ramp Node.\n");
  }
  else {
    float *dst = (float *)mat->coba_builder->pixels[layer];
    memcpy(dst, pixels, sizeof(float) * (CM_TABLE + 1) * 4);
    mat->coba_builder->current_layer += 1;
  }

  return &mat->coba_tex;
}

static void gpu_material_ramp_texture_build(GPUMaterial *mat)
{
  if (mat->coba_builder == NULL) {
    return;
  }

  GPUColorBandBuilder *builder = mat->coba_builder;

  mat->coba_tex = GPU_texture_create_1d_array(
      CM_TABLE + 1, builder->current_layer, GPU_RGBA16F, (float *)builder->pixels, NULL);

  MEM_freeN(builder);
  mat->coba_builder = NULL;
}

static void gpu_material_free_single(GPUMaterial *material)
{
  /* Cancel / wait any pending lazy compilation. */
  DRW_deferred_shader_remove(material);

  gpu_node_graph_free(&material->graph);

  if (material->pass != NULL) {
    GPU_pass_release(material->pass);
  }
  if (material->ubo != NULL) {
    GPU_uniformbuffer_free(material->ubo);
  }
  if (material->sss_tex_profile != NULL) {
    GPU_texture_free(material->sss_tex_profile);
  }
  if (material->sss_profile != NULL) {
    GPU_uniformbuffer_free(material->sss_profile);
  }
  if (material->coba_tex != NULL) {
    GPU_texture_free(material->coba_tex);
  }

  BLI_gset_free(material->used_libraries, NULL);
}

void GPU_material_free(ListBase *gpumaterial)
{
  LISTBASE_FOREACH (LinkData *, link, gpumaterial) {
    GPUMaterial *material = link->data;
    gpu_material_free_single(material);
    MEM_freeN(material);
  }
  BLI_freelistN(gpumaterial);
}

Scene *GPU_material_scene(GPUMaterial *material)
{
  return material->scene;
}

GPUPass *GPU_material_get_pass(GPUMaterial *material)
{
  return material->pass;
}

GPUShader *GPU_material_get_shader(GPUMaterial *material)
{
  return material->pass ? GPU_pass_shader_get(material->pass) : NULL;
}

/* Return can be NULL if it's a world material. */
Material *GPU_material_get_material(GPUMaterial *material)
{
  return material->ma;
}

GPUUniformBuffer *GPU_material_uniform_buffer_get(GPUMaterial *material)
{
  return material->ubo;
}

/**
 * Create dynamic UBO from parameters
 *
 * \param inputs: Items are #LinkData, data is #GPUInput (`BLI_genericNodeN(GPUInput)`).
 */
void GPU_material_uniform_buffer_create(GPUMaterial *material, ListBase *inputs)
{
  material->ubo = GPU_uniformbuffer_dynamic_create(inputs, NULL);
}

/* Eevee Subsurface scattering. */
/* Based on Separable SSS. by Jorge Jimenez and Diego Gutierrez */

#define SSS_SAMPLES 65
#define SSS_EXPONENT 2.0f /* Importance sampling exponent */

typedef struct GPUSssKernelData {
  float kernel[SSS_SAMPLES][4];
  float param[3], max_radius;
  int samples;
  int pad[3];
} GPUSssKernelData;

BLI_STATIC_ASSERT_ALIGN(GPUSssKernelData, 16)

static void sss_calculate_offsets(GPUSssKernelData *kd, int count, float exponent)
{
  float step = 2.0f / (float)(count - 1);
  for (int i = 0; i < count; i++) {
    float o = ((float)i) * step - 1.0f;
    float sign = (o < 0.0f) ? -1.0f : 1.0f;
    float ofs = sign * fabsf(powf(o, exponent));
    kd->kernel[i][3] = ofs;
  }
}

#define GAUSS_TRUNCATE 12.46f
static float gaussian_profile(float r, float radius)
{
  const float v = radius * radius * (0.25f * 0.25f);
  const float Rm = sqrtf(v * GAUSS_TRUNCATE);

  if (r >= Rm) {
    return 0.0f;
  }
  return expf(-r * r / (2.0f * v)) / (2.0f * M_PI * v);
}

#define BURLEY_TRUNCATE 16.0f
#define BURLEY_TRUNCATE_CDF 0.9963790093708328f  // cdf(BURLEY_TRUNCATE)
static float burley_profile(float r, float d)
{
  float exp_r_3_d = expf(-r / (3.0f * d));
  float exp_r_d = exp_r_3_d * exp_r_3_d * exp_r_3_d;
  return (exp_r_d + exp_r_3_d) / (4.0f * d);
}

static float cubic_profile(float r, float radius, float sharpness)
{
  float Rm = radius * (1.0f + sharpness);

  if (r >= Rm) {
    return 0.0f;
  }
  /* custom variation with extra sharpness, to match the previous code */
  const float y = 1.0f / (1.0f + sharpness);
  float Rmy, ry, ryinv;

  Rmy = powf(Rm, y);
  ry = powf(r, y);
  ryinv = (r > 0.0f) ? powf(r, y - 1.0f) : 0.0f;

  const float Rmy5 = (Rmy * Rmy) * (Rmy * Rmy) * Rmy;
  const float f = Rmy - ry;
  const float num = f * (f * f) * (y * ryinv);

  return (10.0f * num) / (Rmy5 * M_PI);
}

static float eval_profile(float r, short falloff_type, float sharpness, float param)
{
  r = fabsf(r);

  if (falloff_type == SHD_SUBSURFACE_BURLEY || falloff_type == SHD_SUBSURFACE_RANDOM_WALK) {
    return burley_profile(r, param) / BURLEY_TRUNCATE_CDF;
  }
  else if (falloff_type == SHD_SUBSURFACE_CUBIC) {
    return cubic_profile(r, param, sharpness);
  }
  else {
    return gaussian_profile(r, param);
  }
}

/* Resolution for each sample of the precomputed kernel profile */
#define INTEGRAL_RESOLUTION 32
static float eval_integral(float x0, float x1, short falloff_type, float sharpness, float param)
{
  const float range = x1 - x0;
  const float step = range / INTEGRAL_RESOLUTION;
  float integral = 0.0f;

  for (int i = 0; i < INTEGRAL_RESOLUTION; i++) {
    float x = x0 + range * ((float)i + 0.5f) / (float)INTEGRAL_RESOLUTION;
    float y = eval_profile(x, falloff_type, sharpness, param);
    integral += y * step;
  }

  return integral;
}
#undef INTEGRAL_RESOLUTION

static void compute_sss_kernel(
    GPUSssKernelData *kd, const float radii[3], int sample_len, int falloff_type, float sharpness)
{
  float rad[3];
  /* Minimum radius */
  rad[0] = MAX2(radii[0], 1e-15f);
  rad[1] = MAX2(radii[1], 1e-15f);
  rad[2] = MAX2(radii[2], 1e-15f);

  /* Christensen-Burley fitting */
  float l[3], d[3];

  if (falloff_type == SHD_SUBSURFACE_BURLEY || falloff_type == SHD_SUBSURFACE_RANDOM_WALK) {
    mul_v3_v3fl(l, rad, 0.25f * M_1_PI);
    const float A = 1.0f;
    const float s = 1.9f - A + 3.5f * (A - 0.8f) * (A - 0.8f);
    /* XXX 0.6f Out of nowhere to match cycles! Empirical! Can be tweak better. */
    mul_v3_v3fl(d, l, 0.6f / s);
    mul_v3_v3fl(rad, d, BURLEY_TRUNCATE);
    kd->max_radius = MAX3(rad[0], rad[1], rad[2]);

    copy_v3_v3(kd->param, d);
  }
  else if (falloff_type == SHD_SUBSURFACE_CUBIC) {
    copy_v3_v3(kd->param, rad);
    mul_v3_fl(rad, 1.0f + sharpness);
    kd->max_radius = MAX3(rad[0], rad[1], rad[2]);
  }
  else {
    kd->max_radius = MAX3(rad[0], rad[1], rad[2]);

    copy_v3_v3(kd->param, rad);
  }

  /* Compute samples locations on the 1d kernel [-1..1] */
  sss_calculate_offsets(kd, sample_len, SSS_EXPONENT);

  /* Weights sum for normalization */
  float sum[3] = {0.0f, 0.0f, 0.0f};

  /* Compute integral of each sample footprint */
  for (int i = 0; i < sample_len; i++) {
    float x0, x1;

    if (i == 0) {
      x0 = kd->kernel[0][3] - fabsf(kd->kernel[0][3] - kd->kernel[1][3]) / 2.0f;
    }
    else {
      x0 = (kd->kernel[i - 1][3] + kd->kernel[i][3]) / 2.0f;
    }

    if (i == sample_len - 1) {
      x1 = kd->kernel[sample_len - 1][3] +
           fabsf(kd->kernel[sample_len - 2][3] - kd->kernel[sample_len - 1][3]) / 2.0f;
    }
    else {
      x1 = (kd->kernel[i][3] + kd->kernel[i + 1][3]) / 2.0f;
    }

    x0 *= kd->max_radius;
    x1 *= kd->max_radius;

    kd->kernel[i][0] = eval_integral(x0, x1, falloff_type, sharpness, kd->param[0]);
    kd->kernel[i][1] = eval_integral(x0, x1, falloff_type, sharpness, kd->param[1]);
    kd->kernel[i][2] = eval_integral(x0, x1, falloff_type, sharpness, kd->param[2]);

    sum[0] += kd->kernel[i][0];
    sum[1] += kd->kernel[i][1];
    sum[2] += kd->kernel[i][2];
  }

  for (int i = 0; i < 3; i++) {
    if (sum[i] > 0.0f) {
      /* Normalize */
      for (int j = 0; j < sample_len; j++) {
        kd->kernel[j][i] /= sum[i];
      }
    }
    else {
      /* Avoid 0 kernel sum. */
      kd->kernel[sample_len / 2][i] = 1.0f;
    }
  }

  /* Put center sample at the start of the array (to sample first) */
  float tmpv[4];
  copy_v4_v4(tmpv, kd->kernel[sample_len / 2]);
  for (int i = sample_len / 2; i > 0; i--) {
    copy_v4_v4(kd->kernel[i], kd->kernel[i - 1]);
  }
  copy_v4_v4(kd->kernel[0], tmpv);

  kd->samples = sample_len;
}

#define INTEGRAL_RESOLUTION 512
static void compute_sss_translucence_kernel(const GPUSssKernelData *kd,
                                            int resolution,
                                            short falloff_type,
                                            float sharpness,
                                            float **output)
{
  float(*texels)[4];
  texels = MEM_callocN(sizeof(float) * 4 * resolution, "compute_sss_translucence_kernel");
  *output = (float *)texels;

  /* Last texel should be black, hence the - 1. */
  for (int i = 0; i < resolution - 1; i++) {
    /* Distance from surface. */
    float d = kd->max_radius * ((float)i + 0.00001f) / ((float)resolution);

    /* For each distance d we compute the radiance incoming from an hypothetic parallel plane. */
    /* Compute radius of the footprint on the hypothetic plane */
    float r_fp = sqrtf(kd->max_radius * kd->max_radius - d * d);
    float r_step = r_fp / INTEGRAL_RESOLUTION;
    float area_accum = 0.0f;
    for (float r = 0.0f; r < r_fp; r += r_step) {
      /* Compute distance to the "shading" point through the medium. */
      /* r_step * 0.5f to put sample between the area borders */
      float dist = hypotf(r + r_step * 0.5f, d);

      float profile[3];
      profile[0] = eval_profile(dist, falloff_type, sharpness, kd->param[0]);
      profile[1] = eval_profile(dist, falloff_type, sharpness, kd->param[1]);
      profile[2] = eval_profile(dist, falloff_type, sharpness, kd->param[2]);

      /* Since the profile and configuration are radially symmetrical we
       * can just evaluate it once and weight it accordingly */
      float r_next = r + r_step;
      float disk_area = (M_PI * r_next * r_next) - (M_PI * r * r);

      mul_v3_fl(profile, disk_area);
      add_v3_v3(texels[i], profile);
      area_accum += disk_area;
    }
    /* Normalize over the disk. */
    mul_v3_fl(texels[i], 1.0f / (area_accum));
  }

  /* Normalize */
  for (int j = resolution - 2; j > 0; j--) {
    texels[j][0] /= (texels[0][0] > 0.0f) ? texels[0][0] : 1.0f;
    texels[j][1] /= (texels[0][1] > 0.0f) ? texels[0][1] : 1.0f;
    texels[j][2] /= (texels[0][2] > 0.0f) ? texels[0][2] : 1.0f;
  }

  /* First texel should be white */
  texels[0][0] = (texels[0][0] > 0.0f) ? 1.0f : 0.0f;
  texels[0][1] = (texels[0][1] > 0.0f) ? 1.0f : 0.0f;
  texels[0][2] = (texels[0][2] > 0.0f) ? 1.0f : 0.0f;

  /* dim the last few texels for smoother transition */
  mul_v3_fl(texels[resolution - 2], 0.25f);
  mul_v3_fl(texels[resolution - 3], 0.5f);
  mul_v3_fl(texels[resolution - 4], 0.75f);
}
#undef INTEGRAL_RESOLUTION

void GPU_material_sss_profile_create(GPUMaterial *material,
                                     float radii[3],
                                     short *falloff_type,
                                     float *sharpness)
{
  copy_v3_v3(material->sss_radii, radii);
  material->sss_falloff = (falloff_type) ? *falloff_type : 0.0;
  material->sss_sharpness = (sharpness) ? *sharpness : 0.0;
  material->sss_dirty = true;
  material->sss_enabled = true;

  /* Update / Create UBO */
  if (material->sss_profile == NULL) {
    material->sss_profile = GPU_uniformbuffer_create(sizeof(GPUSssKernelData), NULL, NULL);
  }
}

struct GPUUniformBuffer *GPU_material_sss_profile_get(GPUMaterial *material,
                                                      int sample_len,
                                                      GPUTexture **tex_profile)
{
  if (!material->sss_enabled) {
    return NULL;
  }

  if (material->sss_dirty || (material->sss_samples != sample_len)) {
    GPUSssKernelData kd;

    float sharpness = material->sss_sharpness;

    /* XXX Black magic but it seems to fit. Maybe because we integrate -1..1 */
    sharpness *= 0.5f;

    compute_sss_kernel(&kd, material->sss_radii, sample_len, material->sss_falloff, sharpness);

    /* Update / Create UBO */
    GPU_uniformbuffer_update(material->sss_profile, &kd);

    /* Update / Create Tex */
    float *translucence_profile;
    compute_sss_translucence_kernel(
        &kd, 64, material->sss_falloff, sharpness, &translucence_profile);

    if (material->sss_tex_profile != NULL) {
      GPU_texture_free(material->sss_tex_profile);
    }

    material->sss_tex_profile = GPU_texture_create_1d(64, GPU_RGBA16F, translucence_profile, NULL);

    MEM_freeN(translucence_profile);

    material->sss_samples = sample_len;
    material->sss_dirty = false;
  }

  if (tex_profile != NULL) {
    *tex_profile = material->sss_tex_profile;
  }
  return material->sss_profile;
}

struct GPUUniformBuffer *GPU_material_create_sss_profile_ubo(void)
{
  return GPU_uniformbuffer_create(sizeof(GPUSssKernelData), NULL, NULL);
}

#undef SSS_EXPONENT
#undef SSS_SAMPLES

ListBase GPU_material_attributes(GPUMaterial *material)
{
  return material->graph.attributes;
}

ListBase GPU_material_textures(GPUMaterial *material)
{
  return material->graph.textures;
}

ListBase GPU_material_volume_grids(GPUMaterial *material)
{
  return material->graph.volume_grids;
}

void GPU_material_output_link(GPUMaterial *material, GPUNodeLink *link)
{
  if (!material->graph.outlink) {
    material->graph.outlink = link;
  }
}

GPUNodeGraph *gpu_material_node_graph(GPUMaterial *material)
{
  return &material->graph;
}

GSet *gpu_material_used_libraries(GPUMaterial *material)
{
  return material->used_libraries;
}

/* Return true if the material compilation has not yet begin or begin. */
eGPUMaterialStatus GPU_material_status(GPUMaterial *mat)
{
  return mat->status;
}

/* Code generation */

bool GPU_material_has_surface_output(GPUMaterial *mat)
{
  return mat->has_surface_output;
}

bool GPU_material_has_volume_output(GPUMaterial *mat)
{
  return mat->has_volume_output;
}

bool GPU_material_is_volume_shader(GPUMaterial *mat)
{
  return mat->is_volume_shader;
}

void GPU_material_flag_set(GPUMaterial *mat, eGPUMatFlag flag)
{
  mat->flag |= flag;
}

bool GPU_material_flag_get(GPUMaterial *mat, eGPUMatFlag flag)
{
  return (mat->flag & flag) != 0;
}

GPUMaterial *GPU_material_from_nodetree_find(ListBase *gpumaterials,
                                             const void *engine_type,
                                             int options)
{
  LISTBASE_FOREACH (LinkData *, link, gpumaterials) {
    GPUMaterial *current_material = (GPUMaterial *)link->data;
    if (current_material->engine_type == engine_type && current_material->options == options) {
      return current_material;
    }
  }

  return NULL;
}

/**
 * \note Caller must use #GPU_material_from_nodetree_find to re-use existing materials,
 * This is enforced since constructing other arguments to this function may be expensive
 * so only do this when they are needed.
 */
GPUMaterial *GPU_material_from_nodetree(Scene *scene,
                                        struct Material *ma,
                                        struct bNodeTree *ntree,
                                        ListBase *gpumaterials,
                                        const void *engine_type,
                                        const int options,
                                        const bool is_volume_shader,
                                        const char *vert_code,
                                        const char *geom_code,
                                        const char *frag_lib,
                                        const char *defines,
                                        const char *name)
{
  LinkData *link;
  bool has_volume_output, has_surface_output;

  /* Caller must re-use materials. */
  BLI_assert(GPU_material_from_nodetree_find(gpumaterials, engine_type, options) == NULL);

  /* HACK: Eevee assume this to create Ghash keys. */
  BLI_assert(sizeof(GPUPass) > 16);

  /* allocate material */
  GPUMaterial *mat = MEM_callocN(sizeof(GPUMaterial), "GPUMaterial");
  mat->ma = ma;
  mat->scene = scene;
  mat->engine_type = engine_type;
  mat->options = options;
  mat->is_volume_shader = is_volume_shader;
#ifndef NDEBUG
  BLI_snprintf(mat->name, sizeof(mat->name), "%s", name);
#else
  UNUSED_VARS(name);
#endif

  mat->used_libraries = BLI_gset_new(
      BLI_ghashutil_ptrhash, BLI_ghashutil_ptrcmp, "GPUMaterial.used_libraries");

  /* localize tree to create links for reroute and mute */
  bNodeTree *localtree = ntreeLocalize(ntree);
  ntreeGPUMaterialNodes(localtree, mat, &has_surface_output, &has_volume_output);

  gpu_material_ramp_texture_build(mat);

  mat->has_surface_output = has_surface_output;
  mat->has_volume_output = has_volume_output;

  if (mat->graph.outlink) {
    /* HACK: this is only for eevee. We add the define here after the nodetree evaluation. */
    if (GPU_material_flag_get(mat, GPU_MATFLAG_SSS)) {
      defines = BLI_string_joinN(defines,
                                 "#ifndef USE_ALPHA_BLEND\n"
                                 "#  define USE_SSS\n"
                                 "#endif\n");
    }
    /* Create source code and search pass cache for an already compiled version. */
    mat->pass = GPU_generate_pass(mat, &mat->graph, vert_code, geom_code, frag_lib, defines);

    if (GPU_material_flag_get(mat, GPU_MATFLAG_SSS)) {
      MEM_freeN((char *)defines);
    }

    if (mat->pass == NULL) {
      /* We had a cache hit and the shader has already failed to compile. */
      mat->status = GPU_MAT_FAILED;
      gpu_node_graph_free(&mat->graph);
    }
    else {
      GPUShader *sh = GPU_pass_shader_get(mat->pass);
      if (sh != NULL) {
        /* We had a cache hit and the shader is already compiled. */
        mat->status = GPU_MAT_SUCCESS;
        gpu_node_graph_free_nodes(&mat->graph);
      }
      else {
        mat->status = GPU_MAT_QUEUED;
      }
    }
  }
  else {
    mat->status = GPU_MAT_FAILED;
    gpu_node_graph_free(&mat->graph);
  }

  /* Only free after GPU_pass_shader_get where GPUUniformBuffer
   * read data from the local tree. */
  ntreeFreeLocalTree(localtree);
  MEM_freeN(localtree);

  /* note that even if building the shader fails in some way, we still keep
   * it to avoid trying to compile again and again, and simply do not use
   * the actual shader on drawing */

  link = MEM_callocN(sizeof(LinkData), "GPUMaterialLink");
  link->data = mat;
  BLI_addtail(gpumaterials, link);

  return mat;
}

void GPU_material_compile(GPUMaterial *mat)
{
  bool success;

  BLI_assert(mat->status == GPU_MAT_QUEUED);
  BLI_assert(mat->pass);

  /* NOTE: The shader may have already been compiled here since we are
   * sharing GPUShader across GPUMaterials. In this case it's a no-op. */
#ifndef NDEBUG
  success = GPU_pass_compile(mat->pass, mat->name);
#else
  success = GPU_pass_compile(mat->pass, __func__);
#endif

  if (success) {
    GPUShader *sh = GPU_pass_shader_get(mat->pass);
    if (sh != NULL) {
      mat->status = GPU_MAT_SUCCESS;
      gpu_node_graph_free_nodes(&mat->graph);
    }
  }
  else {
    mat->status = GPU_MAT_FAILED;
    GPU_pass_release(mat->pass);
    mat->pass = NULL;
    gpu_node_graph_free(&mat->graph);
  }
}

void GPU_materials_free(Main *bmain)
{
  Material *ma;
  World *wo;

  for (ma = bmain->materials.first; ma; ma = ma->id.next) {
    GPU_material_free(&ma->gpumaterial);
  }

  for (wo = bmain->worlds.first; wo; wo = wo->id.next) {
    GPU_material_free(&wo->gpumaterial);
  }

  BKE_material_defaults_free_gpu();
}
