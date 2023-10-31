/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "DNA_camera_types.h"
#include "DRW_render.h"
#include "draw_manager.hh"
#include "draw_pass.hh"

#include "workbench_defines.hh"
#include "workbench_enums.hh"
#include "workbench_shader_shared.h"

#include "GPU_capabilities.h"

extern "C" DrawEngineType draw_engine_workbench;

namespace blender::workbench {

using namespace draw;

class ShaderCache {
 public:
  ~ShaderCache();

  GPUShader *prepass_shader_get(ePipelineType pipeline_type,
                                eGeometryType geometry_type,
                                eShaderType shader_type,
                                eLightingType lighting_type,
                                bool clip);

  GPUShader *resolve_shader_get(ePipelineType pipeline_type,
                                eLightingType lighting_type,
                                bool cavity = false,
                                bool curvature = false,
                                bool shadow = false);

 private:
  /* TODO(fclem): We might want to change to a Map since most shader will never be compiled. */
  GPUShader *prepass_shader_cache_[pipeline_type_len][geometry_type_len][shader_type_len]
                                  [lighting_type_len][2 /*clip*/] = {{{{{nullptr}}}}};
  GPUShader *resolve_shader_cache_[pipeline_type_len][lighting_type_len][2 /*cavity*/]
                                  [2 /*curvature*/][2 /*shadow*/] = {{{{{nullptr}}}}};
};

struct Material {
  float3 base_color = float3(0);
  /* Packed data into a int. Decoded in the shader. */
  uint packed_data = 0;

  Material();
  Material(float3 color);
  Material(::Object &ob, bool random = false);
  Material(::Material &mat);

  static uint32_t pack_data(float metallic, float roughness, float alpha);

  bool is_transparent();
};

void get_material_image(Object *ob,
                        int material_index,
                        ::Image *&image,
                        ImageUser *&iuser,
                        GPUSamplerState &sampler_state);

struct SceneState {
  Scene *scene = nullptr;

  Object *camera_object = nullptr;
  Camera *camera = nullptr;
  float4x4 view_projection_matrix = float4x4::identity();
  int2 resolution = int2(0);

  eContextObjectMode object_mode = CTX_MODE_OBJECT;

  View3DShading shading = {};
  eLightingType lighting_type = eLightingType::STUDIO;
  bool xray_mode = false;

  DRWState cull_state = DRW_STATE_NO_DRAW;
  Vector<float4> clip_planes = {};

  float4 background_color = float4(0);

  bool draw_cavity = false;
  bool draw_curvature = false;
  bool draw_shadows = false;
  bool draw_outline = false;
  bool draw_dof = false;
  bool draw_aa = false;

  bool draw_object_id = false;

  int sample = 0;
  int samples_len = 0;
  bool reset_taa_next_sample = false;
  bool render_finished = false;

  bool overlays_enabled = false;

  /* Used when material_type == eMaterialType::SINGLE */
  Material material_override = Material(float3(1.0f));
  /* When r == -1.0 the shader uses the vertex color */
  Material material_attribute_color = Material(float3(-1.0f));

  void init(Object *camera_ob = nullptr);
};

struct ObjectState {
  eV3DShadingColorType color_type = V3D_SHADING_SINGLE_COLOR;
  bool sculpt_pbvh = false;
  ::Image *image_paint_override = nullptr;
  GPUSamplerState override_sampler_state = GPUSamplerState::default_sampler();
  bool draw_shadow = false;
  bool use_per_material_batches = false;

  ObjectState(const SceneState &scene_state, Object *ob);
};

struct SceneResources;

class CavityEffect {
 private:
  /* This value must be kept in sync with the one declared at
   * workbench_composite_info.hh (cavity_samples) */
  static const int max_samples_ = 512;

  UniformArrayBuffer<float4, max_samples_> samples_buf = {};

  int sample_ = 0;
  int sample_count_ = 0;
  bool curvature_enabled_ = false;
  bool cavity_enabled_ = false;

 public:
  void init(const SceneState &scene_state, SceneResources &resources);
  void setup_resolve_pass(PassSimple &pass, SceneResources &resources);

 private:
  void load_samples_buf(int ssao_samples);
};

/* Used as a temporary workaround for the lack of texture views support on Windows ARM. */
class StencilViewWorkaround {
 private:
  Texture stencil_copy_tx_ = "stencil_copy_tx";
  GPUShader *stencil_copy_sh_ = nullptr;

 public:
  StencilViewWorkaround()
  {
    stencil_copy_sh_ = GPU_shader_create_from_info_name("workbench_extract_stencil");
  }
  ~StencilViewWorkaround()
  {
    DRW_SHADER_FREE_SAFE(stencil_copy_sh_);
  }

  /** WARNING: Should only be called at render time.
   * When the workaround path is active,
   * the returned texture won't stay in sync with the stencil_src,
   * and will only be valid until the next time this function is called.
   * Note that the output is a binary mask,
   * any stencil value that is not 0x00 will be rendered as 0xFF. */
  GPUTexture *extract(Manager &manager, Texture &stencil_src)
  {
    if (GPU_texture_view_support()) {
      return stencil_src.stencil_view();
    }

    int2 extent = int2(stencil_src.width(), stencil_src.height());
    stencil_copy_tx_.ensure_2d(
        GPU_R8UI, extent, GPU_TEXTURE_USAGE_ATTACHMENT | GPU_TEXTURE_USAGE_SHADER_READ);

    PassSimple ps("Stencil View Workaround");
    ps.init();
    ps.clear_color(float4(0));
    ps.state_set(DRW_STATE_WRITE_COLOR | DRW_STATE_STENCIL_NEQUAL);
    ps.state_stencil(0x00, 0x00, 0xFF);
    ps.shader_set(stencil_copy_sh_);
    ps.draw_procedural(GPU_PRIM_TRIS, 1, 3);

    Framebuffer fb;
    fb.ensure(GPU_ATTACHMENT_TEXTURE(stencil_src), GPU_ATTACHMENT_TEXTURE(stencil_copy_tx_));
    fb.bind();

    manager.submit(ps);

    return stencil_copy_tx_;
  }
};

struct SceneResources {
  static const int jitter_tx_size = 64;

  ShaderCache shader_cache = {};

  StringRefNull current_matcap = {};
  Texture matcap_tx = "matcap_tx";

  TextureFromPool object_id_tx = "wb_object_id_tx";

  TextureRef color_tx;
  TextureRef depth_tx;
  TextureRef depth_in_front_tx;

  Framebuffer clear_fb = {"Clear Main"};
  Framebuffer clear_in_front_fb = {"Clear In Front"};

  StorageVectorBuffer<Material> material_buf = {"material_buf"};
  UniformBuffer<WorldData> world_buf = {};
  UniformArrayBuffer<float4, 6> clip_planes_buf;

  Texture jitter_tx = "wb_jitter_tx";

  CavityEffect cavity = {};

  StencilViewWorkaround stencil_view;

  void init(const SceneState &scene_state);
  void load_jitter_tx(int total_samples);
};

class MeshPass : public PassMain {
 private:
  using TextureSubPassKey = std::pair<GPUTexture *, eGeometryType>;

  Map<TextureSubPassKey, PassMain::Sub *> texture_subpass_map_ = {};

  PassMain::Sub *passes_[geometry_type_len][shader_type_len] = {{nullptr}};

  bool is_empty_ = false;

 public:
  MeshPass(const char *name);

  /* TODO: Move to draw::Pass */
  bool is_empty() const;

  void init_pass(SceneResources &resources, DRWState state, int clip_planes);
  void init_subpasses(ePipelineType pipeline,
                      eLightingType lighting,
                      bool clip,
                      ShaderCache &shaders);

  PassMain::Sub &get_subpass(eGeometryType geometry_type,
                             ::Image *image = nullptr,
                             GPUSamplerState sampler_state = GPUSamplerState::default_sampler(),
                             ImageUser *iuser = nullptr);
};

enum class StencilBits : uint8_t {
  BACKGROUND = 0,
  OBJECT = 1u << 0,
  OBJECT_IN_FRONT = 1u << 1,
};

class OpaquePass {
 public:
  TextureFromPool gbuffer_normal_tx = {"gbuffer_normal_tx"};
  TextureFromPool gbuffer_material_tx = {"gbuffer_material_tx"};

  Texture shadow_depth_stencil_tx = {"shadow_depth_stencil_tx"};
  GPUTexture *deferred_ps_stencil_tx = nullptr;

  MeshPass gbuffer_ps_ = {"Opaque.Gbuffer"};
  MeshPass gbuffer_in_front_ps_ = {"Opaque.GbufferInFront"};
  PassSimple deferred_ps_ = {"Opaque.Deferred"};

  Framebuffer gbuffer_fb = {"Opaque.Gbuffer"};
  Framebuffer gbuffer_in_front_fb = {"Opaque.GbufferInFront"};
  Framebuffer deferred_fb = {"Opaque.Deferred"};
  Framebuffer clear_fb = {"Opaque.Clear"};

  void sync(const SceneState &scene_state, SceneResources &resources);
  void draw(Manager &manager,
            View &view,
            SceneResources &resources,
            int2 resolution,
            class ShadowPass *shadow_pass);
  bool is_empty() const;
};

class TransparentPass {
 private:
  GPUShader *resolve_sh_ = nullptr;

 public:
  TextureFromPool accumulation_tx = {"accumulation_accumulation_tx"};
  TextureFromPool reveal_tx = {"accumulation_reveal_tx"};
  Framebuffer transparent_fb = {};

  MeshPass accumulation_ps_ = {"Transparent.Accumulation"};
  MeshPass accumulation_in_front_ps_ = {"Transparent.AccumulationInFront"};
  PassSimple resolve_ps_ = {"Transparent.Resolve"};
  Framebuffer resolve_fb = {};

  ~TransparentPass();

  void sync(const SceneState &scene_state, SceneResources &resources);
  void draw(Manager &manager, View &view, SceneResources &resources, int2 resolution);
  bool is_empty() const;
};

class TransparentDepthPass {
 private:
  GPUShader *merge_sh_ = nullptr;

 public:
  MeshPass main_ps_ = {"TransparentDepth.Main"};
  Framebuffer main_fb = {"TransparentDepth.Main"};
  MeshPass in_front_ps_ = {"TransparentDepth.InFront"};
  Framebuffer in_front_fb = {"TransparentDepth.InFront"};
  PassSimple merge_ps_ = {"TransparentDepth.Merge"};
  Framebuffer merge_fb = {"TransparentDepth.Merge"};

  ~TransparentDepthPass();

  void sync(const SceneState &scene_state, SceneResources &resources);
  void draw(Manager &manager, View &view, SceneResources &resources);
  bool is_empty() const;
};

class ShadowPass {
 private:
  enum PassType { PASS = 0, FAIL, FORCED_FAIL, MAX };

  class ShadowView : public View {
    bool force_fail_method_ = false;
    float3 light_direction_ = float3(0);
    UniformBuffer<ExtrudedFrustum> extruded_frustum_ = {};
    ShadowPass::PassType current_pass_type_ = PASS;

    VisibilityBuf pass_visibility_buf_ = {};
    VisibilityBuf fail_visibility_buf_ = {};

    GPUShader *dynamic_pass_type_shader_;
    GPUShader *static_pass_type_shader_;

   public:
    ShadowView();
    ~ShadowView();

    void setup(View &view, float3 light_direction, bool force_fail_method);
    bool debug_object_culling(Object *ob);
    void set_mode(PassType type);

   protected:
    virtual void compute_visibility(ObjectBoundsBuf &bounds,
                                    uint resource_len,
                                    bool debug_freeze) override;
    virtual VisibilityBuf &get_visibility_buffer() override;
  } view_ = {};

  bool enabled_;

  UniformBuffer<ShadowPassData> pass_data_ = {};

  /* Draws are added to both passes and the visibly compute shader selects one of them */
  PassMain pass_ps_ = {"Shadow.Pass"};
  PassMain fail_ps_ = {"Shadow.Fail"};

  /* In some cases, we know beforehand that we need to use the fail technique */
  PassMain forced_fail_ps_ = {"Shadow.ForcedFail"};

  /* [PassType][Is Manifold][Is Cap] */
  PassMain::Sub *passes_[PassType::MAX][2][2] = {{{nullptr}}};
  PassMain::Sub *&get_pass_ptr(PassType type, bool manifold, bool cap = false);

  /* [Is Pass Technique][Is Manifold][Is Cap] */
  GPUShader *shaders_[2][2][2] = {{{nullptr}}};
  GPUShader *get_shader(bool depth_pass, bool manifold, bool cap = false);

  TextureFromPool depth_tx_ = {};
  Framebuffer fb_ = {};

 public:
  ~ShadowPass();

  void init(const SceneState &scene_state, SceneResources &resources);
  void update();
  void sync();
  void object_sync(SceneState &scene_state,
                   ObjectRef &ob_ref,
                   ResourceHandle handle,
                   const bool has_transp_mat);
  void draw(Manager &manager,
            View &view,
            SceneResources &resources,
            GPUTexture &depth_stencil_tx,
            /* Needed when there are opaque "In Front" objects in the scene */
            bool force_fail_method);

  bool is_debug();
};

class VolumePass {
  bool active_ = true;

  PassMain ps_ = {"Volume"};
  Framebuffer fb_ = {"Volume"};

  Texture dummy_shadow_tx_ = {"Volume.Dummy Shadow Tx"};
  Texture dummy_volume_tx_ = {"Volume.Dummy Volume Tx"};
  Texture dummy_coba_tx_ = {"Volume.Dummy Coba Tx"};

  GPUTexture *stencil_tx_ = nullptr;

  GPUShader *shaders_[2 /*slice*/][2 /*coba*/][3 /*interpolation*/][2 /*smoke*/];

 public:
  ~VolumePass();

  void sync(SceneResources &resources);

  void object_sync_volume(Manager &manager,
                          SceneResources &resources,
                          const SceneState &scene_state,
                          ObjectRef &ob_ref,
                          float3 color);

  void object_sync_modifier(Manager &manager,
                            SceneResources &resources,
                            const SceneState &scene_state,
                            ObjectRef &ob_ref,
                            ModifierData *md);

  void draw(Manager &manager, View &view, SceneResources &resources);

 private:
  GPUShader *get_shader(bool slice, bool coba, int interpolation, bool smoke);

  void draw_slice_ps(Manager &manager,
                     PassMain::Sub &ps,
                     ObjectRef &ob_ref,
                     int slice_axis_enum,
                     float slice_depth);

  void draw_volume_ps(Manager &manager,
                      PassMain::Sub &ps,
                      ObjectRef &ob_ref,
                      int taa_sample,
                      float3 slice_count,
                      float3 world_size);
};

class OutlinePass {
 private:
  bool enabled_ = false;

  PassSimple ps_ = PassSimple("Workbench.Outline");
  GPUShader *sh_ = nullptr;
  Framebuffer fb_ = Framebuffer("Workbench.Outline");

 public:
  ~OutlinePass();

  void init(const SceneState &scene_state);
  void sync(SceneResources &resources);
  void draw(Manager &manager, SceneResources &resources);
};

class DofPass {
 private:
  static const int kernel_radius_ = 3;
  static const int samples_len_ = (kernel_radius_ * 2 + 1) * (kernel_radius_ * 2 + 1);

  bool enabled_ = false;

  float offset_ = 0;

  UniformArrayBuffer<float4, samples_len_> samples_buf_ = {};

  Texture source_tx_ = {};
  Texture coc_halfres_tx_ = {};
  TextureFromPool blur_tx_ = {};

  Framebuffer downsample_fb_ = {};
  Framebuffer blur1_fb_ = {};
  Framebuffer blur2_fb_ = {};
  Framebuffer resolve_fb_ = {};

  GPUShader *prepare_sh_ = nullptr;
  GPUShader *downsample_sh_ = nullptr;
  GPUShader *blur1_sh_ = nullptr;
  GPUShader *blur2_sh_ = nullptr;
  GPUShader *resolve_sh_ = nullptr;

  PassSimple down_ps_ = {"Workbench.DoF.DownSample"};
  PassSimple down2_ps_ = {"Workbench.DoF.DownSample2"};
  PassSimple blur_ps_ = {"Workbench.DoF.Blur"};
  PassSimple blur2_ps_ = {"Workbench.DoF.Blur2"};
  PassSimple resolve_ps_ = {"Workbench.DoF.Resolve"};

  float aperture_size_ = 0;
  float distance_ = 0;
  float invsensor_size_ = 0;
  float near_ = 0;
  float far_ = 0;
  float blades_ = 0;
  float rotation_ = 0;
  float ratio_ = 0;

 public:
  ~DofPass();

  void init(const SceneState &scene_state);
  void sync(SceneResources &resources);
  void draw(Manager &manager, View &view, SceneResources &resources, int2 resolution);
  bool is_enabled();

 private:
  void setup_samples();
};

class AntiAliasingPass {
 private:
  bool enabled_ = false;
  /* Weight accumulated. */
  float weight_accum_ = 0;
  /* Samples weight for this iteration. */
  float weights_[9] = {0};
  /* Sum of weights. */
  float weights_sum_ = 0;

  Texture sample0_depth_tx_ = {"sample0_depth_tx"};
  Texture sample0_depth_in_front_tx_ = {"sample0_depth_in_front_tx"};

  Texture taa_accumulation_tx_ = {"taa_accumulation_tx"};
  Texture smaa_search_tx_ = {"smaa_search_tx"};
  Texture smaa_area_tx_ = {"smaa_area_tx"};
  TextureFromPool smaa_edge_tx_ = {"smaa_edge_tx"};
  TextureFromPool smaa_weight_tx_ = {"smaa_weight_tx"};

  Framebuffer taa_accumulation_fb_ = {"taa_accumulation_fb"};
  Framebuffer smaa_edge_fb_ = {"smaa_edge_fb"};
  Framebuffer smaa_weight_fb_ = {"smaa_weight_fb"};
  Framebuffer smaa_resolve_fb_ = {"smaa_resolve_fb"};
  Framebuffer overlay_depth_fb_ = {"overlay_depth_fb"};

  float4 smaa_viewport_metrics_ = float4(0);
  float smaa_mix_factor_ = 0;

  GPUShader *taa_accumulation_sh_ = nullptr;
  GPUShader *smaa_edge_detect_sh_ = nullptr;
  GPUShader *smaa_aa_weight_sh_ = nullptr;
  GPUShader *smaa_resolve_sh_ = nullptr;
  GPUShader *overlay_depth_sh_ = nullptr;

  PassSimple taa_accumulation_ps_ = {"TAA.Accumulation"};
  PassSimple smaa_edge_detect_ps_ = {"SMAA.EdgeDetect"};
  PassSimple smaa_aa_weight_ps_ = {"SMAA.BlendWeights"};
  PassSimple smaa_resolve_ps_ = {"SMAA.Resolve"};
  PassSimple overlay_depth_ps_ = {"Overlay Depth"};

 public:
  AntiAliasingPass();
  ~AntiAliasingPass();

  void init(const SceneState &scene_state);
  void sync(const SceneState &scene_state, SceneResources &resources);
  void setup_view(View &view, const SceneState &scene_state);
  void draw(
      Manager &manager,
      View &view,
      const SceneState &scene_state,
      SceneResources &resources,
      /** Passed directly since we may need to copy back the results from the first sample,
       * and resources.depth_in_front_tx is only valid when mesh passes have to draw to it. */
      GPUTexture *depth_in_front_tx);
};

}  // namespace blender::workbench
