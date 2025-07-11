/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edsculpt
 */

#include <cmath>
#include <cstdlib>

#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_object_types.h"

#include "DNA_brush_types.h"
#include "DNA_scene_types.h"

#include "BLI_listbase.h"
#include "BLI_math_color.h"
#include "BLI_math_matrix.h"
#include "BLI_math_matrix.hh"
#include "BLI_math_vector.hh"
#include "BLI_rect.h"
#include "BLI_utildefines.h"

#include "BLT_translation.hh"

#include "BKE_brush.hh"
#include "BKE_bvhutils.hh"
#include "BKE_colortools.hh"
#include "BKE_context.hh"
#include "BKE_customdata.hh"
#include "BKE_image.hh"
#include "BKE_layer.hh"
#include "BKE_material.hh"
#include "BKE_mesh.hh"
#include "BKE_mesh_sample.hh"
#include "BKE_object.hh"
#include "BKE_paint.hh"
#include "BKE_report.hh"

#include "DEG_depsgraph.hh"
#include "DEG_depsgraph_query.hh"

#include "RNA_access.hh"
#include "RNA_define.hh"
#include "RNA_prototypes.hh"

#include "IMB_imbuf_types.hh"
#include "IMB_interp.hh"

#include "RE_texture.h"

#include "ED_image.hh"
#include "ED_screen.hh"
#include "ED_select_utils.hh"
#include "ED_view3d.hh"

#include "ED_mesh.hh" /* for face mask functions */

#include "WM_api.hh"
#include "WM_types.hh"

#include "paint_intern.hh"

#include "ED_select_utils.hh" /*bfa - needed to retreive SEL_SELECT */

bool paint_convert_bb_to_rect(rcti *rect,
                              const float bb_min[3],
                              const float bb_max[3],
                              const ARegion &region,
                              const RegionView3D &rv3d,
                              const Object &ob)
{
  int i, j, k;

  BLI_rcti_init_minmax(rect);

  /* return zero if the bounding box has non-positive volume */
  if (bb_min[0] > bb_max[0] || bb_min[1] > bb_max[1] || bb_min[2] > bb_max[2]) {
    return false;
  }

  const blender::float4x4 projection = ED_view3d_ob_project_mat_get(&rv3d, &ob);

  for (i = 0; i < 2; i++) {
    for (j = 0; j < 2; j++) {
      for (k = 0; k < 2; k++) {
        float vec[3];
        int proj_i[2];
        vec[0] = i ? bb_min[0] : bb_max[0];
        vec[1] = j ? bb_min[1] : bb_max[1];
        vec[2] = k ? bb_min[2] : bb_max[2];
        /* convert corner to screen space */
        const blender::float2 proj = ED_view3d_project_float_v2_m4(&region, vec, projection);
        /* expand 2D rectangle */

        /* we could project directly to int? */
        proj_i[0] = proj[0];
        proj_i[1] = proj[1];

        BLI_rcti_do_minmax_v(rect, proj_i);
      }
    }
  }

  /* return false if the rectangle has non-positive area */
  return rect->xmin < rect->xmax && rect->ymin < rect->ymax;
}

void paint_calc_redraw_planes(float planes[4][4],
                              const ARegion &region,
                              const Object &ob,
                              const rcti &screen_rect)
{
  BoundBox bb;
  rcti rect;

  /* use some extra space just in case */
  rect = screen_rect;
  rect.xmin -= 2;
  rect.xmax += 2;
  rect.ymin -= 2;
  rect.ymax += 2;

  ED_view3d_clipping_calc(&bb, planes, &region, &ob, &rect);
}

float paint_calc_object_space_radius(const ViewContext &vc,
                                     const blender::float3 &center,
                                     const float pixel_radius)
{
  Object *ob = vc.obact;
  float delta[3], scale, loc[3];
  const float xy_delta[2] = {pixel_radius, 0.0f};

  mul_v3_m4v3(loc, ob->object_to_world().ptr(), center);

  const float zfac = ED_view3d_calc_zfac(vc.rv3d, loc);
  ED_view3d_win_to_delta(vc.region, xy_delta, zfac, delta);

  scale = fabsf(mat4_to_scale(ob->object_to_world().ptr()));
  scale = (scale == 0.0f) ? 1.0f : scale;

  return len_v3(delta) / scale;
}

bool paint_get_tex_pixel(const MTex *mtex,
                         float u,
                         float v,
                         ImagePool *pool,
                         int thread,
                         /* Return arguments. */
                         float *r_intensity,
                         float r_rgba[4])
{
  const float co[3] = {u, v, 0.0f};
  float intensity;
  const bool has_rgb = RE_texture_evaluate(
      mtex, co, thread, pool, false, false, &intensity, r_rgba);
  *r_intensity = intensity;

  if (!has_rgb) {
    r_rgba[0] = intensity;
    r_rgba[1] = intensity;
    r_rgba[2] = intensity;
    r_rgba[3] = 1.0f;
  }

  return has_rgb;
}

void paint_stroke_operator_properties(wmOperatorType *ot)
{
  static const EnumPropertyItem stroke_mode_items[] = {
      {BRUSH_STROKE_NORMAL, "NORMAL", 0, "Regular", "Apply brush normally"},
      {BRUSH_STROKE_INVERT,
       "INVERT",
       0,
       "Invert",
       "Invert action of brush for duration of stroke"},
      {BRUSH_STROKE_SMOOTH,
       "SMOOTH",
       0,
       "Smooth",
       "Switch brush to smooth mode for duration of stroke"},
      {BRUSH_STROKE_ERASE,
       "ERASE",
       0,
       "Erase",
       "Switch brush to erase mode for duration of stroke"},
      {0},
  };

  PropertyRNA *prop;

  prop = RNA_def_collection_runtime(ot->srna, "stroke", &RNA_OperatorStrokeElement, "Stroke", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);

  prop = RNA_def_enum(ot->srna,
                      "mode",
                      stroke_mode_items,
                      BRUSH_STROKE_NORMAL,
                      "Stroke Mode",
                      "Action taken when a paint stroke is made");
  RNA_def_property_translation_context(prop, BLT_I18NCONTEXT_OPERATOR_DEFAULT);
  RNA_def_property_flag(prop, PROP_SKIP_SAVE);

  /* TODO: Pen flip logic should likely be combined into the stroke mode logic instead of being
   * an entirely separate concept. */
  prop = RNA_def_boolean(
      ot->srna, "pen_flip", false, "Pen Flip", "Whether a tablet's eraser mode is being used");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
}

/* 3D Paint */

/* compute uv coordinates of mouse in face */
static blender::float2 imapaint_pick_uv(const Mesh *mesh_eval,
                                        Scene *scene,
                                        Object *ob_eval,
                                        const int tri_index,
                                        const blender::float3 &bary_coord)
{
  using namespace blender;
  const ePaintCanvasSource mode = ePaintCanvasSource(scene->toolsettings->imapaint.mode);

  const Span<int3> tris = mesh_eval->corner_tris();
  const Span<int> tri_faces = mesh_eval->corner_tri_faces();

  const bke::AttributeAccessor attributes = mesh_eval->attributes();
  const VArray<int> material_indices = *attributes.lookup_or_default<int>(
      "material_index", bke::AttrDomain::Face, 0);

  /* face means poly here, not triangle, indeed */
  const int face_i = tri_faces[tri_index];

  VArraySpan<float2> uv_map;

  if (mode == PAINT_CANVAS_SOURCE_MATERIAL) {
    const Material *ma;
    const TexPaintSlot *slot;

    ma = BKE_object_material_get(ob_eval, material_indices[face_i] + 1);
    slot = &ma->texpaintslot[ma->paint_active_slot];
    if (slot && slot->uvname) {
      uv_map = *attributes.lookup<float2>(slot->uvname, bke::AttrDomain::Face);
    }
  }

  if (uv_map.is_empty()) {
    const char *active_name = CustomData_get_active_layer_name(&mesh_eval->corner_data,
                                                               CD_PROP_FLOAT2);
    uv_map = *attributes.lookup<float2>(active_name, bke::AttrDomain::Face);
  }

  return bke::mesh_surface_sample::sample_corner_attribute_with_bary_coords(
      bary_coord, tris[tri_index], uv_map);
}

/* returns 0 if not found, otherwise 1 */
static int imapaint_pick_face(ViewContext *vc,
                              const int mval[2],
                              int *r_tri_index,
                              int *r_face_index,
                              blender::float3 *r_bary_coord,
                              const Mesh &mesh)
{
  using namespace blender;
  if (mesh.faces_num == 0) {
    return 0;
  }

  float3 start_world, end_world;
  ED_view3d_win_to_segment_clipped(
      vc->depsgraph, vc->region, vc->v3d, float2(mval[0], mval[1]), start_world, end_world, true);

  const float4x4 &world_to_object = vc->obact->world_to_object();
  const float3 start_object = math::transform_point(world_to_object, start_world);
  const float3 end_object = math::transform_point(world_to_object, end_world);

  bke::BVHTreeFromMesh mesh_bvh = mesh.bvh_corner_tris();

  BVHTreeRayHit ray_hit;
  ray_hit.dist = FLT_MAX;
  ray_hit.index = -1;
  BLI_bvhtree_ray_cast(mesh_bvh.tree,
                       start_object,
                       math::normalize(end_object - start_object),
                       0.0f,
                       &ray_hit,
                       mesh_bvh.raycast_callback,
                       &mesh_bvh);
  if (ray_hit.index == -1) {
    return 0;
  }

  *r_bary_coord = bke::mesh_surface_sample::compute_bary_coord_in_triangle(
      mesh.vert_positions(), mesh.corner_verts(), mesh.corner_tris()[ray_hit.index], ray_hit.co);

  *r_tri_index = ray_hit.index;
  *r_face_index = mesh.corner_tri_faces()[ray_hit.index];
  return 1;
}

void paint_sample_color(
    bContext *C, ARegion *region, int x, int y, bool texpaint_proj, bool use_palette)
{
  using namespace blender;
  Scene *scene = CTX_data_scene(C);
  Depsgraph *depsgraph = CTX_data_ensure_evaluated_depsgraph(C);
  Paint *paint = BKE_paint_get_active_from_context(C);
  Palette *palette = BKE_paint_palette(paint);
  PaletteColor *color = nullptr;
  Brush *br = BKE_paint_brush(BKE_paint_get_active_from_context(C));

  CLAMP(x, 0, region->winx);
  CLAMP(y, 0, region->winy);

  if (use_palette) {
    if (!palette) {
      palette = BKE_palette_add(CTX_data_main(C), "Palette");
      BKE_paint_palette_set(paint, palette);
    }

    color = BKE_palette_color_add(palette);
    palette->active_color = BLI_listbase_count(&palette->colors) - 1;
  }

  SpaceImage *sima = CTX_wm_space_image(C);
  const View3D *v3d = CTX_wm_view3d(C);

  if (v3d && texpaint_proj) {
    /* first try getting a color directly from the mesh faces if possible */
    ViewLayer *view_layer = CTX_data_view_layer(C);
    BKE_view_layer_synced_ensure(scene, view_layer);
    Object *ob = BKE_view_layer_active_object_get(view_layer);
    Object *ob_eval = DEG_get_evaluated(depsgraph, ob);
    ImagePaintSettings *imapaint = &scene->toolsettings->imapaint;
    bool use_material = (imapaint->mode == IMAGEPAINT_MODE_MATERIAL);

    if (ob) {
      const Mesh *mesh_eval = BKE_object_get_evaluated_mesh(ob_eval);
      const bke::AttributeAccessor attributes = mesh_eval->attributes();
      const VArray material_indices = *attributes.lookup_or_default<int>(
          "material_index", bke::AttrDomain::Face, 0);

      if (CustomData_has_layer(&mesh_eval->corner_data, CD_PROP_FLOAT2)) {
        ViewContext vc = ED_view3d_viewcontext_init(C, depsgraph);

        const int mval[2] = {x, y};
        int tri_index;
        float3 bary_coord;
        int faceindex;
        const VArray<bool> hide_poly = *mesh_eval->attributes().lookup_or_default<bool>(
            ".hide_poly", bke::AttrDomain::Face, false);
        const bool is_hit = imapaint_pick_face(
                                &vc, mval, &tri_index, &faceindex, &bary_coord, *mesh_eval) &&
                            !hide_poly[faceindex];

        if (is_hit) {
          Image *image = nullptr;
          int interp = SHD_INTERP_LINEAR;

          if (use_material) {
            /* Image and texture interpolation from material. */
            Material *ma = BKE_object_material_get(ob_eval, material_indices[faceindex] + 1);

            /* Force refresh since paint slots are not updated when changing interpolation. */
            BKE_texpaint_slot_refresh_cache(scene, ma, ob);

            if (ma && ma->texpaintslot) {
              image = ma->texpaintslot[ma->paint_active_slot].ima;
              interp = ma->texpaintslot[ma->paint_active_slot].interp;
            }
          }
          else {
            /* Image and texture interpolation from tool settings. */
            image = imapaint->canvas;
            interp = imapaint->interp;
          }

          if (image) {
            /* XXX get appropriate ImageUser instead */
            ImageUser iuser;
            BKE_imageuser_default(&iuser);
            iuser.framenr = image->lastframe;

            float2 uv = imapaint_pick_uv(mesh_eval, scene, ob_eval, tri_index, bary_coord);

            if (image->source == IMA_SRC_TILED) {
              float new_uv[2];
              iuser.tile = BKE_image_get_tile_from_pos(image, uv, new_uv, nullptr);
              uv[0] = new_uv[0];
              uv[1] = new_uv[1];
            }

            ImBuf *ibuf = BKE_image_acquire_ibuf(image, &iuser, nullptr);
            if (ibuf && (ibuf->byte_buffer.data || ibuf->float_buffer.data)) {
              float u = uv[0] * ibuf->x;
              float v = uv[1] * ibuf->y;

              if (ibuf->float_buffer.data) {
                float4 rgba_f = interp == SHD_INTERP_CLOSEST ?
                                    imbuf::interpolate_nearest_wrap_fl(ibuf, u, v) :
                                    imbuf::interpolate_bilinear_wrap_fl(ibuf, u, v);
                rgba_f = math::clamp(rgba_f, 0.0f, 1.0f);
                straight_to_premul_v4(rgba_f);
                if (use_palette) {
                  linearrgb_to_srgb_v3_v3(color->rgb, rgba_f);
                }
                else {
                  linearrgb_to_srgb_v3_v3(rgba_f, rgba_f);
                  BKE_brush_color_set(paint, br, rgba_f);
                }
              }
              else {
                uchar4 rgba = interp == SHD_INTERP_CLOSEST ?
                                  imbuf::interpolate_nearest_wrap_byte(ibuf, u, v) :
                                  imbuf::interpolate_bilinear_wrap_byte(ibuf, u, v);
                if (use_palette) {
                  rgb_uchar_to_float(color->rgb, rgba);
                }
                else {
                  float rgba_f[3];
                  rgb_uchar_to_float(rgba_f, rgba);
                  BKE_brush_color_set(paint, br, rgba_f);
                }
              }
              BKE_image_release_ibuf(image, ibuf, nullptr);
              return;
            }

            BKE_image_release_ibuf(image, ibuf, nullptr);
          }
        }
      }
    }
  }
  else if (sima != nullptr) {
    /* Sample from the active image buffer. The sampled color is in
     * Linear Scene Reference Space. */
    float rgba_f[3];
    bool is_data;
    if (ED_space_image_color_sample(sima, region, blender::int2(x, y), rgba_f, &is_data)) {
      if (!is_data) {
        linearrgb_to_srgb_v3_v3(rgba_f, rgba_f);
      }

      if (use_palette) {
        copy_v3_v3(color->rgb, rgba_f);
      }
      else {
        BKE_brush_color_set(paint, br, rgba_f);
      }
      return;
    }
  }

  /* No sample found; sample directly from the GPU front buffer. */
  {
    float rgb_fl[3];
    WM_window_pixels_read_sample(C,
                                 CTX_wm_window(C),
                                 blender::int2(x + region->winrct.xmin, y + region->winrct.ymin),
                                 rgb_fl);
    if (use_palette) {
      copy_v3_v3(color->rgb, rgb_fl);
    }
    else {
      BKE_brush_color_set(paint, br, rgb_fl);
    }
  }
}

static wmOperatorStatus brush_curve_preset_exec(bContext *C, wmOperator *op)
{
  Brush *br = BKE_paint_brush(BKE_paint_get_active_from_context(C));

  if (br) {
    Scene *scene = CTX_data_scene(C);
    ViewLayer *view_layer = CTX_data_view_layer(C);
    BKE_brush_curve_preset(br, eCurveMappingPreset(RNA_enum_get(op->ptr, "shape")));
    BKE_paint_invalidate_cursor_overlay(scene, view_layer, br->curve);
  }

  return OPERATOR_FINISHED;
}

static bool brush_curve_preset_poll(bContext *C)
{
  Brush *br = BKE_paint_brush(BKE_paint_get_active_from_context(C));

  return br && br->curve;
}

static const EnumPropertyItem prop_shape_items[] = {
    {CURVE_PRESET_SHARP, "SHARP", 0, "Sharp", ""},
    {CURVE_PRESET_SMOOTH, "SMOOTH", 0, "Smooth", ""},
    {CURVE_PRESET_MAX, "MAX", 0, "Max", ""},
    {CURVE_PRESET_LINE, "LINE", 0, "Line", ""},
    {CURVE_PRESET_ROUND, "ROUND", 0, "Round", ""},
    {CURVE_PRESET_ROOT, "ROOT", 0, "Root", ""},
    {0, nullptr, 0, nullptr, nullptr},
};

void BRUSH_OT_curve_preset(wmOperatorType *ot)
{
  ot->name = "Preset";
  ot->description = "Set brush shape";
  ot->idname = "BRUSH_OT_curve_preset";

  ot->exec = brush_curve_preset_exec;
  ot->poll = brush_curve_preset_poll;

  PropertyRNA *prop;
  prop = RNA_def_enum(ot->srna, "shape", prop_shape_items, CURVE_PRESET_SMOOTH, "Mode", "");
  RNA_def_property_translation_context(prop,
                                       BLT_I18NCONTEXT_ID_CURVE_LEGACY); /* Abusing id_curve :/ */
}

static bool brush_sculpt_curves_falloff_preset_poll(bContext *C)
{
  Brush *br = BKE_paint_brush(BKE_paint_get_active_from_context(C));
  return br && br->curves_sculpt_settings && br->curves_sculpt_settings->curve_parameter_falloff;
}

static wmOperatorStatus brush_sculpt_curves_falloff_preset_exec(bContext *C, wmOperator *op)
{
  Brush *brush = BKE_paint_brush(BKE_paint_get_active_from_context(C));
  CurveMapping *mapping = brush->curves_sculpt_settings->curve_parameter_falloff;
  mapping->preset = RNA_enum_get(op->ptr, "shape");
  CurveMap *map = mapping->cm;
  BKE_curvemap_reset(map, &mapping->clipr, mapping->preset, CURVEMAP_SLOPE_POSITIVE);
  BKE_brush_tag_unsaved_changes(brush);
  return OPERATOR_FINISHED;
}

void BRUSH_OT_sculpt_curves_falloff_preset(wmOperatorType *ot)
{
  ot->name = "Curve Falloff Preset";
  ot->description = "Set Curve Falloff Preset";
  ot->idname = "BRUSH_OT_sculpt_curves_falloff_preset";

  ot->exec = brush_sculpt_curves_falloff_preset_exec;
  ot->poll = brush_sculpt_curves_falloff_preset_poll;

  PropertyRNA *prop;
  prop = RNA_def_enum(ot->srna, "shape", prop_shape_items, CURVE_PRESET_SMOOTH, "Mode", "");
  RNA_def_property_translation_context(prop,
                                       BLT_I18NCONTEXT_ID_CURVE_LEGACY); /* Abusing id_curve :/ */
}

/* face-select ops */
static wmOperatorStatus paint_select_linked_exec(bContext *C, wmOperator * /*op*/)
{
  paintface_select_linked(C, CTX_data_active_object(C), nullptr, true);
  ED_region_tag_redraw(CTX_wm_region(C));
  return OPERATOR_FINISHED;
}

void PAINT_OT_face_select_linked(wmOperatorType *ot)
{
  ot->name = "Select Linked";
  ot->description = "Select linked faces";
  ot->idname = "PAINT_OT_face_select_linked";

  ot->exec = paint_select_linked_exec;
  ot->poll = facemask_paint_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static wmOperatorStatus paint_select_linked_pick_invoke(bContext *C,
                                                        wmOperator *op,
                                                        const wmEvent *event)
{
  const bool select = !RNA_boolean_get(op->ptr, "deselect");
  view3d_operator_needs_gpu(C);
  paintface_select_linked(C, CTX_data_active_object(C), event->mval, select);
  ED_region_tag_redraw(CTX_wm_region(C));
  return OPERATOR_FINISHED;
}

void PAINT_OT_face_select_linked_pick(wmOperatorType *ot)
{
  ot->name = "Select Linked Pick";
  ot->description = "Select linked faces under the cursor";
  ot->idname = "PAINT_OT_face_select_linked_pick";

  ot->invoke = paint_select_linked_pick_invoke;
  ot->poll = facemask_paint_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_boolean(ot->srna, "deselect", false, "Deselect", "Deselect rather than select items");
}

static wmOperatorStatus face_select_all_exec(bContext *C, wmOperator *op)
{
  Object *ob = CTX_data_active_object(C);
  if (paintface_deselect_all_visible(C, ob, RNA_enum_get(op->ptr, "action"), true)) {
    ED_region_tag_redraw(CTX_wm_region(C));
    return OPERATOR_FINISHED;
  }
  return OPERATOR_CANCELLED;
}

/*bfa - descriptions*/
static std::string paint_ot_face_select_all_get_description(bContext * /*C*/,
                                                            wmOperatorType * /*ot*/,
                                                            PointerRNA *ptr)
{
  /*Select*/
  if (RNA_enum_get(ptr, "action") == SEL_SELECT) {
    return "Select all faces";
  }
  /*Deselect*/
  else if (RNA_enum_get(ptr, "action") == SEL_DESELECT) {
    return "Deselect all faces";
  }
  /*Invert*/
  else if (RNA_enum_get(ptr, "action") == SEL_INVERT) {
    return "Inverts the current selection";
  }
  return "";
}

void PAINT_OT_face_select_all(wmOperatorType *ot)
{
  ot->name = "(De)select All";
  ot->description = "Change selection for all faces";
  ot->idname = "PAINT_OT_face_select_all";

  ot->exec = face_select_all_exec;
  ot->get_description = paint_ot_face_select_all_get_description; /*bfa - descriptions*/
  ot->poll = facemask_paint_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  WM_operator_properties_select_all(ot);
}

static wmOperatorStatus paint_select_more_exec(bContext *C, wmOperator *op)
{
  Object *ob = CTX_data_active_object(C);
  Mesh *mesh = BKE_mesh_from_object(ob);
  if (mesh == nullptr || mesh->faces_num == 0) {
    return OPERATOR_CANCELLED;
  }

  const bool face_step = RNA_boolean_get(op->ptr, "face_step");
  paintface_select_more(mesh, face_step);
  paintface_flush_flags(C, ob, true, false);

  ED_region_tag_redraw(CTX_wm_region(C));
  return OPERATOR_FINISHED;
}

void PAINT_OT_face_select_more(wmOperatorType *ot)
{
  ot->name = "Select More";
  ot->description = "Select Faces connected to existing selection";
  ot->idname = "PAINT_OT_face_select_more";

  ot->exec = paint_select_more_exec;
  ot->poll = facemask_paint_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_boolean(
      ot->srna, "face_step", true, "Face Step", "Also select faces that only touch on a corner");
}

static wmOperatorStatus paint_select_less_exec(bContext *C, wmOperator *op)
{
  Object *ob = CTX_data_active_object(C);
  Mesh *mesh = BKE_mesh_from_object(ob);
  if (mesh == nullptr || mesh->faces_num == 0) {
    return OPERATOR_CANCELLED;
  }

  const bool face_step = RNA_boolean_get(op->ptr, "face_step");
  paintface_select_less(mesh, face_step);
  paintface_flush_flags(C, ob, true, false);

  ED_region_tag_redraw(CTX_wm_region(C));
  return OPERATOR_FINISHED;
}

void PAINT_OT_face_select_less(wmOperatorType *ot)
{
  ot->name = "Select Less";
  ot->description = "Deselect Faces connected to existing selection";
  ot->idname = "PAINT_OT_face_select_less";

  ot->exec = paint_select_less_exec;
  ot->poll = facemask_paint_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_boolean(
      ot->srna, "face_step", true, "Face Step", "Also deselect faces that only touch on a corner");
}

static wmOperatorStatus paintface_select_loop_invoke(bContext *C,
                                                     wmOperator *op,
                                                     const wmEvent *event)
{
  const bool select = RNA_boolean_get(op->ptr, "select");
  const bool extend = RNA_boolean_get(op->ptr, "extend");
  if (!extend) {
    paintface_deselect_all_visible(C, CTX_data_active_object(C), SEL_DESELECT, false);
  }
  view3d_operator_needs_gpu(C);
  paintface_select_loop(C, CTX_data_active_object(C), event->mval, select);
  ED_region_tag_redraw(CTX_wm_region(C));
  return OPERATOR_FINISHED;
}

/*bfa - descriptions*/
static std::string PAINT_OT_face_select_loop_get_descriptions(struct bContext * /*C*/,
                                                              struct wmOperatorType * /*op*/,
                                                              struct PointerRNA *ptr)
{
  const bool select = RNA_boolean_get(ptr, "select");
  const bool extend = RNA_boolean_get(ptr, "extend");

  if (select && !extend) {
    return "Select face loop under the cursor\nMouse Operator, please use the mouse";
  }
  else if (select && extend) {
    return "Select face loop under the cursor and add it to the current selection\nMouse "
           "Operator, please use the mouse";
  }
  else if (!select && extend) {
    return "Remove the face loop under the cursor from the selection\nMouse Operator, please use "
           "the mouse";
  }
  return "";
}

void PAINT_OT_face_select_loop(wmOperatorType *ot)
{
  ot->name = "Select Loop";
  ot->description = "Select face loop under the cursor\nMouse Operator, please use the mouse";
  ot->idname = "PAINT_OT_face_select_loop";

  ot->invoke = paintface_select_loop_invoke;
  ot->get_description = PAINT_OT_face_select_loop_get_descriptions; /*bfa - descriptions*/
  ot->poll = facemask_paint_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_boolean(ot->srna, "select", true, "Select", "If false, faces will be deselected");
  RNA_def_boolean(ot->srna, "extend", false, "Extend", "Extend the selection");
}

static wmOperatorStatus vert_select_all_exec(bContext *C, wmOperator *op)
{
  Object *ob = CTX_data_active_object(C);
  paintvert_deselect_all_visible(ob, RNA_enum_get(op->ptr, "action"), true);
  paintvert_tag_select_update(C, ob);
  ED_region_tag_redraw(CTX_wm_region(C));
  return OPERATOR_FINISHED;
}

/*bfa - descriptions*/
static std::string paint_ot_vert_select_all_get_description(bContext * /*C*/,
                                                            wmOperatorType * /*ot*/,
                                                            PointerRNA *ptr)
{
  /*Select*/
  if (RNA_enum_get(ptr, "action") == SEL_SELECT) {
    return "Select all vertices";
  }
  /*Deselect*/
  else if (RNA_enum_get(ptr, "action") == SEL_DESELECT) {
    return "Deselect all vertices";
  }
  /*Invert*/
  else if (RNA_enum_get(ptr, "action") == SEL_INVERT) {
    return "Inverts the current selection";
  }
  return "";
}

void PAINT_OT_vert_select_all(wmOperatorType *ot)
{
  ot->name = "(De)select All";
  ot->description = "Change selection for all vertices";
  ot->idname = "PAINT_OT_vert_select_all";

  ot->exec = vert_select_all_exec;
  ot->get_description = paint_ot_vert_select_all_get_description; /*bfa - descriptions*/
  ot->poll = vert_paint_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  WM_operator_properties_select_all(ot);
}

static wmOperatorStatus vert_select_ungrouped_exec(bContext *C, wmOperator *op)
{
  Object *ob = CTX_data_active_object(C);
  Mesh *mesh = static_cast<Mesh *>(ob->data);

  if (BLI_listbase_is_empty(&mesh->vertex_group_names) || mesh->deform_verts().is_empty()) {
    BKE_report(op->reports, RPT_ERROR, "No weights/vertex groups on object");
    return OPERATOR_CANCELLED;
  }

  paintvert_select_ungrouped(ob, RNA_boolean_get(op->ptr, "extend"), true);
  paintvert_tag_select_update(C, ob);
  ED_region_tag_redraw(CTX_wm_region(C));
  return OPERATOR_FINISHED;
}

void PAINT_OT_vert_select_ungrouped(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Select Ungrouped";
  ot->idname = "PAINT_OT_vert_select_ungrouped";
  ot->description = "Select vertices without a group";

  /* API callbacks. */
  ot->exec = vert_select_ungrouped_exec;
  ot->poll = vert_paint_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_boolean(ot->srna, "extend", false, "Extend", "Extend the selection");
}

static wmOperatorStatus paintvert_select_linked_exec(bContext *C, wmOperator * /*op*/)
{
  paintvert_select_linked(C, CTX_data_active_object(C));
  ED_region_tag_redraw(CTX_wm_region(C));
  return OPERATOR_FINISHED;
}

void PAINT_OT_vert_select_linked(wmOperatorType *ot)
{
  ot->name = "Select Linked Vertices";
  ot->description = "Select linked vertices";
  ot->idname = "PAINT_OT_vert_select_linked";

  ot->exec = paintvert_select_linked_exec;
  ot->poll = vert_paint_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static wmOperatorStatus paintvert_select_linked_pick_invoke(bContext *C,
                                                            wmOperator *op,
                                                            const wmEvent *event)
{
  const bool select = RNA_boolean_get(op->ptr, "select");
  view3d_operator_needs_gpu(C);

  paintvert_select_linked_pick(C, CTX_data_active_object(C), event->mval, select);
  ED_region_tag_redraw(CTX_wm_region(C));
  return OPERATOR_FINISHED;
}

void PAINT_OT_vert_select_linked_pick(wmOperatorType *ot)
{
  ot->name = "Select Linked Vertices Pick";
  ot->description = "Select linked vertices under the cursor";
  ot->idname = "PAINT_OT_vert_select_linked_pick";

  ot->invoke = paintvert_select_linked_pick_invoke;
  ot->poll = vert_paint_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_boolean(ot->srna,
                  "select",
                  true,
                  "Select",
                  "Whether to select or deselect linked vertices under the cursor");
}

static wmOperatorStatus paintvert_select_more_exec(bContext *C, wmOperator *op)
{
  Object *ob = CTX_data_active_object(C);
  Mesh *mesh = BKE_mesh_from_object(ob);
  if (mesh == nullptr || mesh->faces_num == 0) {
    return OPERATOR_CANCELLED;
  }

  const bool face_step = RNA_boolean_get(op->ptr, "face_step");
  paintvert_select_more(mesh, face_step);

  paintvert_flush_flags(ob);
  paintvert_tag_select_update(C, ob);
  ED_region_tag_redraw(CTX_wm_region(C));

  return OPERATOR_FINISHED;
}

void PAINT_OT_vert_select_more(wmOperatorType *ot)
{
  ot->name = "Select More";
  ot->description = "Select Vertices connected to existing selection";
  ot->idname = "PAINT_OT_vert_select_more";

  ot->exec = paintvert_select_more_exec;
  ot->poll = vert_paint_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_boolean(
      ot->srna, "face_step", true, "Face Step", "Also select faces that only touch on a corner");
}

static wmOperatorStatus paintvert_select_less_exec(bContext *C, wmOperator *op)
{
  Object *ob = CTX_data_active_object(C);
  Mesh *mesh = BKE_mesh_from_object(ob);
  if (mesh == nullptr || mesh->faces_num == 0) {
    return OPERATOR_CANCELLED;
  }

  const bool face_step = RNA_boolean_get(op->ptr, "face_step");
  paintvert_select_less(mesh, face_step);

  paintvert_flush_flags(ob);
  paintvert_tag_select_update(C, ob);
  ED_region_tag_redraw(CTX_wm_region(C));

  return OPERATOR_FINISHED;
}

void PAINT_OT_vert_select_less(wmOperatorType *ot)
{
  ot->name = "Select Less";
  ot->description = "Deselect Vertices connected to existing selection";
  ot->idname = "PAINT_OT_vert_select_less";

  ot->exec = paintvert_select_less_exec;
  ot->poll = vert_paint_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_boolean(
      ot->srna, "face_step", true, "Face Step", "Also deselect faces that only touch on a corner");
}

static wmOperatorStatus face_select_hide_exec(bContext *C, wmOperator *op)
{
  const bool unselected = RNA_boolean_get(op->ptr, "unselected");
  Object *ob = CTX_data_active_object(C);
  paintface_hide(C, ob, unselected);
  ED_region_tag_redraw(CTX_wm_region(C));
  return OPERATOR_FINISHED;
}

void PAINT_OT_face_select_hide(wmOperatorType *ot)
{
  ot->name = "Face Select Hide";
  ot->description = "Hide selected faces";
  ot->idname = "PAINT_OT_face_select_hide";

  ot->exec = face_select_hide_exec;
  ot->poll = facemask_paint_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_boolean(
      ot->srna, "unselected", false, "Unselected", "Hide unselected rather than selected objects");
}

static wmOperatorStatus vert_select_hide_exec(bContext *C, wmOperator *op)
{
  const bool unselected = RNA_boolean_get(op->ptr, "unselected");
  Object *ob = CTX_data_active_object(C);
  paintvert_hide(C, ob, unselected);
  ED_region_tag_redraw(CTX_wm_region(C));
  return OPERATOR_FINISHED;
}

void PAINT_OT_vert_select_hide(wmOperatorType *ot)
{
  ot->name = "Vertex Select Hide";
  ot->description = "Hide selected vertices";
  ot->idname = "PAINT_OT_vert_select_hide";

  ot->exec = vert_select_hide_exec;
  ot->poll = vert_paint_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_boolean(ot->srna,
                  "unselected",
                  false,
                  "Unselected",
                  "Hide unselected rather than selected vertices");
}

static wmOperatorStatus face_vert_reveal_exec(bContext *C, wmOperator *op)
{
  const bool select = RNA_boolean_get(op->ptr, "select");
  Object *ob = CTX_data_active_object(C);

  if (BKE_paint_select_vert_test(ob)) {
    paintvert_reveal(C, ob, select);
  }
  else {
    paintface_reveal(C, ob, select);
  }

  ED_region_tag_redraw(CTX_wm_region(C));
  return OPERATOR_FINISHED;
}

static bool face_vert_reveal_poll(bContext *C)
{
  Object *ob = CTX_data_active_object(C);

  /* Allow using this operator when no selection is enabled but hiding is applied. */
  return BKE_paint_select_elem_test(ob) || BKE_paint_always_hide_test(ob);
}

void PAINT_OT_face_vert_reveal(wmOperatorType *ot)
{
  ot->name = "Reveal Faces/Vertices";
  ot->description = "Reveal hidden faces and vertices";
  ot->idname = "PAINT_OT_face_vert_reveal";

  ot->exec = face_vert_reveal_exec;
  ot->poll = face_vert_reveal_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_boolean(ot->srna,
                  "select",
                  true,
                  "Select",
                  "Specifies whether the newly revealed geometry should be selected");
}
