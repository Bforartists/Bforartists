/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_color.hh"
#include "BLI_index_mask.hh"
#include "BLI_math_base.hh"
#include "BLI_math_matrix.hh"
#include "BLI_math_vector.hh"
#include "BLI_offset_indices.hh"
#include "BLI_rect.h"
#include "BLI_stack.hh"
#include "BLI_task.hh"

#include "BKE_attribute.hh"
#include "BKE_camera.h"
#include "BKE_context.hh"
#include "BKE_crazyspace.hh"
#include "BKE_curves.hh"
#include "BKE_grease_pencil.hh"
#include "BKE_image.h"
#include "BKE_lib_id.hh"
#include "BKE_material.h"
#include "BKE_paint.hh"

#include "DNA_curves_types.h"
#include "DNA_grease_pencil_types.h"
#include "DNA_material_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_view3d_types.h"

#include "DEG_depsgraph_query.hh"

#include "ED_grease_pencil.hh"
#include "ED_view3d.hh"

#include "IMB_imbuf.hh"
#include "IMB_imbuf_types.hh"

#include "GPU_state.hh"

#include <list>
#include <optional>

namespace blender::ed::greasepencil {

/* -------------------------------------------------------------------- */
/** \name Color Values and Flags
 * \{ */

const ColorGeometry4f draw_boundary_color = {1, 0, 0, 1};
const ColorGeometry4f draw_seed_color = {0, 1, 0, 1};

enum ColorFlag {
  Border = (1 << 0),
  Stroke = (1 << 1),
  Fill = (1 << 2),
  Seed = (1 << 3),
  Debug = (1 << 7),
};
ENUM_OPERATORS(ColorFlag, ColorFlag::Seed)

/** \} */

/* -------------------------------------------------------------------- */
/** \name Boundary from Pixel Buffer
 * \{ */

/* Utility class for access to pixel buffer data. */
class ImageBufferAccessor {
 private:
  Image *ima_ = nullptr;
  ImBuf *ibuf_ = nullptr;
  void *lock_ = nullptr;
  MutableSpan<ColorGeometry4b> data_;
  int2 size_ = int2(0);

 public:
  bool has_buffer() const
  {
    return ibuf_ != nullptr;
  }

  ~ImageBufferAccessor()
  {
    BLI_assert(!this->has_buffer());
  }

  void acquire(Image &ima)
  {
    BLI_assert(!this->has_buffer());
    ima_ = &ima;
    ibuf_ = BKE_image_acquire_ibuf(&ima, nullptr, &lock_);
    size_ = {ibuf_->x, ibuf_->y};
    data_ = MutableSpan<ColorGeometry4b>(
        reinterpret_cast<ColorGeometry4b *>(ibuf_->byte_buffer.data), ibuf_->x * ibuf_->y);
  }

  void release()
  {
    BLI_assert(this->has_buffer());
    BKE_image_release_ibuf(ima_, ibuf_, lock_);
    lock_ = nullptr;
    ima_ = nullptr;
    ibuf_ = nullptr;
    data_ = {};
    size_ = int2(0);
  }

  int2 size() const
  {
    return this->size_;
  }

  int width() const
  {
    return this->size_.x;
  }

  int height() const
  {
    return this->size_.y;
  }

  bool is_valid_coord(const int2 &c) const
  {
    return c.x >= 0 && c.x < this->size_.x && c.y >= 0 && c.y < this->size_.y;
  }

  int2 coord_from_index(const int index) const
  {
    const div_t d = div(index, this->size_.x);
    return int2{d.rem, d.quot};
  }

  int index_from_coord(const int2 &c) const
  {
    return c.x + c.y * this->size_.x;
  }

  Span<ColorGeometry4b> pixels() const
  {
    return this->data_;
  }

  MutableSpan<ColorGeometry4b> pixels()
  {
    return this->data_;
  }

  ColorGeometry4b &pixel_from_coord(const int2 &c)
  {
    return this->data_[index_from_coord(c)];
  }

  const ColorGeometry4b &pixel_from_coord(const int2 &c) const
  {
    return this->data_[index_from_coord(c)];
  }
};

static bool get_flag(const ColorGeometry4b &color, const ColorFlag flag)
{
  return (color.r & flag) != 0;
}

static void set_flag(ColorGeometry4b &color, const ColorFlag flag, bool value)
{
  color.r = value ? (color.r | flag) : (color.r & (~flag));
}

/* Set a border to create image limits. */
/* TODO this shouldn't be necessary if drawing could accurately save flag values. */
static void convert_colors_to_flags(ImageBufferAccessor &buffer)
{
  for (ColorGeometry4b &color : buffer.pixels()) {
    const bool is_stroke = color.r > 0.0f;
    const bool is_seed = color.g > 0.0f;
    color.r = (is_stroke ? ColorFlag::Stroke : 0) | (is_seed ? ColorFlag::Seed : 0);
    color.g = 0;
    color.b = 0;
    color.a = 0;
  }
}

/* Set a border to create image limits. */
static void convert_flags_to_colors(ImageBufferAccessor &buffer)
{
  constexpr const ColorGeometry4b output_stroke_color = {255, 0, 0, 255};
  constexpr const ColorGeometry4b output_seed_color = {127, 127, 0, 255};
  constexpr const ColorGeometry4b output_border_color = {0, 0, 255, 255};
  constexpr const ColorGeometry4b output_fill_color = {127, 255, 0, 255};
  // constexpr const ColorGeometry4b output_extend_color = {25, 255, 0, 255};
  // constexpr const ColorGeometry4b output_helper_color = {255, 0, 127, 255};
  constexpr const ColorGeometry4b output_debug_color = {255, 127, 0, 255};

  auto add_colors = [](const ColorGeometry4b &a, const ColorGeometry4b &b) -> ColorGeometry4b {
    return ColorGeometry4b(std::min(int(a.r) + int(b.r), 255),
                           std::min(int(a.g) + int(b.g), 255),
                           std::min(int(a.b) + int(b.b), 255),
                           std::min(int(a.a) + int(b.a), 255));
  };

  for (ColorGeometry4b &color : buffer.pixels()) {
    ColorGeometry4b output_color = ColorGeometry4b(0, 0, 0, 0);
    if (color.r & ColorFlag::Debug) {
      output_color = add_colors(output_color, output_debug_color);
    }
    if (color.r & ColorFlag::Fill) {
      output_color = add_colors(output_color, output_fill_color);
    }
    if (color.r & ColorFlag::Stroke) {
      output_color = add_colors(output_color, output_stroke_color);
    }
    if (color.r & ColorFlag::Border) {
      output_color = add_colors(output_color, output_border_color);
    }
    if (color.r & ColorFlag::Seed) {
      output_color = add_colors(output_color, output_seed_color);
    }
    color = std::move(output_color);
  }
}

/* Set a border to create image limits. */
static void mark_borders(ImageBufferAccessor &buffer)
{
  int row_start = 0;
  /* Fill first row */
  for (const int i : IndexRange(buffer.width())) {
    set_flag(buffer.pixels()[row_start + i], ColorFlag::Border, true);
  }
  row_start += buffer.width();
  /* Fill first and last pixel of middle rows. */
  for ([[maybe_unused]] const int i : IndexRange(buffer.height()).drop_front(1).drop_back(1)) {
    set_flag(buffer.pixels()[row_start], ColorFlag::Border, true);
    set_flag(buffer.pixels()[row_start + buffer.width() - 1], ColorFlag::Border, true);
    row_start += buffer.width();
  }
  /* Fill last row */
  for (const int i : IndexRange(buffer.width())) {
    set_flag(buffer.pixels()[row_start + i], ColorFlag::Border, true);
  }
}

enum class FillResult {
  Success,
  BorderContact,
};

enum FillBorderMode {
  /* Cancel when hitting the border, fill failed. */
  Cancel,
  /* Allow border contact, continue with other pixels. */
  Ignore,
};

template<FillBorderMode border_mode>
FillResult flood_fill(ImageBufferAccessor &buffer, const int leak_filter_width = 0)
{
  const MutableSpan<ColorGeometry4b> pixels = buffer.pixels();
  const int width = buffer.width();
  const int height = buffer.height();

  blender::Stack<int> active_pixels;
  /* Initialize the stack with filled pixels (dot at mouse position). */
  for (const int i : pixels.index_range()) {
    if (get_flag(pixels[i], ColorFlag::Seed)) {
      active_pixels.push(i);
    }
  }

  enum FilterDirection {
    Horizontal = 1,
    Vertical = 2,
  };

  bool border_contact = false;
  while (!active_pixels.is_empty()) {
    const int index = active_pixels.pop();
    const int2 coord = buffer.coord_from_index(index);
    ColorGeometry4b pixel_value = buffer.pixels()[index];

    if constexpr (border_mode == FillBorderMode::Cancel) {
      if (get_flag(pixel_value, ColorFlag::Border)) {
        border_contact = true;
        break;
      }
    }
    else if constexpr (border_mode == FillBorderMode::Ignore) {
      if (get_flag(pixel_value, ColorFlag::Border)) {
        border_contact = true;
      }
    }

    if (get_flag(pixel_value, ColorFlag::Fill)) {
      /* Pixel already filled. */
      continue;
    }

    if (get_flag(pixel_value, ColorFlag::Stroke)) {
      /* Boundary pixel, ignore. */
      continue;
    }

    /* Mark as filled. */
    set_flag(pixels[index], ColorFlag::Fill, true);

    /* Directional box filtering for gap detection. */
    const IndexRange filter_x_neg = IndexRange(1, std::min(coord.x, leak_filter_width));
    const IndexRange filter_x_pos = IndexRange(1,
                                               std::min(width - 1 - coord.x, leak_filter_width));
    const IndexRange filter_y_neg = IndexRange(1, std::min(coord.y, leak_filter_width));
    const IndexRange filter_y_pos = IndexRange(1,
                                               std::min(height - 1 - coord.y, leak_filter_width));
    bool is_boundary_horizontal = false;
    bool is_boundary_vertical = false;
    for (const int filter_i : filter_y_neg) {
      is_boundary_horizontal |= get_flag(buffer.pixel_from_coord(coord - int2(0, filter_i)),
                                         ColorFlag::Stroke);
    }
    for (const int filter_i : filter_y_pos) {
      is_boundary_horizontal |= get_flag(buffer.pixel_from_coord(coord + int2(0, filter_i)),
                                         ColorFlag::Stroke);
    }
    for (const int filter_i : filter_x_neg) {
      is_boundary_vertical |= get_flag(buffer.pixel_from_coord(coord - int2(filter_i, 0)),
                                       ColorFlag::Stroke);
    }
    for (const int filter_i : filter_x_pos) {
      is_boundary_vertical |= get_flag(buffer.pixel_from_coord(coord + int2(filter_i, 0)),
                                       ColorFlag::Stroke);
    }

    /* Activate neighbors */
    if (coord.x > 0 && !is_boundary_horizontal) {
      active_pixels.push(buffer.index_from_coord(coord - int2{1, 0}));
    }
    if (coord.x < width - 1 && !is_boundary_horizontal) {
      active_pixels.push(buffer.index_from_coord(coord + int2{1, 0}));
    }
    if (coord.y > 0 && !is_boundary_vertical) {
      active_pixels.push(buffer.index_from_coord(coord - int2{0, 1}));
    }
    if (coord.y < height - 1 && !is_boundary_vertical) {
      active_pixels.push(buffer.index_from_coord(coord + int2{0, 1}));
    }
  }

  return border_contact ? FillResult::BorderContact : FillResult::Success;
}

/* Turn unfilled areas into filled and vice versa. */
static void invert_fill(ImageBufferAccessor &buffer)
{
  for (ColorGeometry4b &color : buffer.pixels()) {
    const bool is_filled = get_flag(color, ColorFlag::Fill);
    set_flag(color, ColorFlag::Fill, !is_filled);
  }
}

constexpr const int num_directions = 8;
static const int2 offset_by_direction[num_directions] = {
    {-1, -1},
    {0, -1},
    {1, -1},
    {1, 0},
    {1, 1},
    {0, 1},
    {-1, 1},
    {-1, 0},
};

/* Wrap to valid direction, must be less than 3 * num_directions. */
static int wrap_dir_3n(const int dir)
{
  return dir - num_directions * (int(dir >= num_directions) + int(dir >= 2 * num_directions));
}

struct FillBoundary {
  /* Pixel indices making up boundary curves. */
  Vector<int> pixels;
  /* Offset index for each curve. */
  Vector<int> offset_indices;
};

/* Get the outline points of a shape using Moore Neighborhood algorithm
 *
 * This is a Blender customized version of the general algorithm described
 * in https://en.wikipedia.org/wiki/Moore_neighborhood
 */
static FillBoundary build_fill_boundary(const ImageBufferAccessor &buffer)
{
  using BoundarySection = std::list<int>;
  using BoundaryStartMap = Map<int, BoundarySection>;

  const Span<ColorGeometry4b> pixels = buffer.pixels();
  const int width = buffer.width();
  const int height = buffer.height();

  /* Find possible starting points for boundary sections.
   * Direction 3 == (1, 0) is the starting direction. */
  constexpr const uint8_t start_direction = 3;
  auto find_start_coordinates = [&]() -> BoundaryStartMap {
    BoundaryStartMap starts;
    for (const int y : IndexRange(height)) {
      /* Check for empty pixels next to filled pixels. */
      for (const int x : IndexRange(width).drop_back(1)) {
        const int index_left = buffer.index_from_coord({x, y});
        const int index_right = buffer.index_from_coord({x + 1, y});
        const bool filled_left = get_flag(pixels[index_left], ColorFlag::Fill);
        const bool filled_right = get_flag(pixels[index_right], ColorFlag::Fill);
        const bool border_right = get_flag(pixels[index_right], ColorFlag::Border);
        if (!filled_left && filled_right && !border_right) {
          /* Empty index list indicates uninitialized section. */
          starts.add(index_right, {});
        }
      }
    }
    return starts;
  };

  struct NeighborIterator {
    int index;
    int direction;
  };

  /* Find the next filled pixel in clockwise direction from the current. */
  auto find_next_neighbor = [&](NeighborIterator &iter) -> bool {
    const int2 iter_coord = buffer.coord_from_index(iter.index);
    for (const int i : IndexRange(num_directions).drop_front(1)) {
      /* Invert direction (add 4) and start at next direction (add 1..n).
       * This can not be greater than 3*num_directions-1, wrap accordingly. */
      const int neighbor_dir = wrap_dir_3n(iter.direction + 4 + i);
      const int2 neighbor_coord = iter_coord + offset_by_direction[neighbor_dir];
      if (!buffer.is_valid_coord(neighbor_coord)) {
        continue;
      }
      const int neighbor_index = buffer.index_from_coord(neighbor_coord);
      /* Border pixels are not valid. */
      if (get_flag(pixels[neighbor_index], ColorFlag::Border)) {
        continue;
      }
      if (get_flag(pixels[neighbor_index], ColorFlag::Fill)) {
        iter.index = neighbor_index;
        iter.direction = neighbor_dir;
        return true;
      }
    }
    return false;
  };

  BoundaryStartMap boundary_starts = find_start_coordinates();

  /* Find directions and connectivity for all boundary pixels. */
  for (const int start_index : boundary_starts.keys()) {
    /* Boundary map entries may get removed, only handle active starts. */
    if (!boundary_starts.contains(start_index)) {
      continue;
    }
    BoundarySection &section = boundary_starts.lookup(start_index);
    section.push_back(start_index);
    NeighborIterator iter = {start_index, start_direction};
    while (find_next_neighbor(iter)) {
      /* Loop closed when arriving at start again. */
      if (iter.index == start_index) {
        break;
      }

      /* Join existing sections. */
      if (boundary_starts.contains(iter.index)) {
        BoundarySection &next_section = boundary_starts.lookup(iter.index);
        if (next_section.empty()) {
          /* Empty sections are only start indices, remove and continue. */
          boundary_starts.remove(iter.index);
        }
        else {
          /* Merge existing points into the current section. */
          section.splice(section.end(), next_section);
          boundary_starts.remove(iter.index);
          break;
        }
      }

      section.push_back(iter.index);
    }
    /* Discard un-closed boundaries. */
    if (iter.index != start_index) {
      boundary_starts.remove(start_index);
    }
  }

  /* Construct final strokes by tracing the boundary. */
  FillBoundary final_boundary;
  for (const BoundarySection &section : boundary_starts.values()) {
    final_boundary.offset_indices.append(final_boundary.pixels.size());
    for (const int index : section) {
      final_boundary.pixels.append(index);
    }
  }
  final_boundary.offset_indices.append(final_boundary.pixels.size());

  return final_boundary;
}

/* Create curves geometry from boundary positions. */
static bke::CurvesGeometry boundary_to_curves(const Scene &scene,
                                              const ViewContext &view_context,
                                              const Brush &brush,
                                              const FillBoundary &boundary,
                                              const ImageBufferAccessor &buffer,
                                              const ed::greasepencil::DrawingPlacement &placement,
                                              const int material_index,
                                              const float hardness)
{
  /* Curve cannot have 0 points. */
  if (boundary.offset_indices.is_empty() || boundary.pixels.is_empty()) {
    return {};
  }

  bke::CurvesGeometry curves(boundary.pixels.size(), boundary.offset_indices.size() - 1);

  curves.offsets_for_write().copy_from(boundary.offset_indices);
  MutableSpan<float3> positions = curves.positions_for_write();
  bke::MutableAttributeAccessor attributes = curves.attributes_for_write();
  /* Attributes that are defined explicitly and should not be set to default values. */
  Set<std::string> skip_curve_attributes = {"curve_type", "material_index", "cyclic", "hardness"};
  Set<std::string> skip_point_attributes = {"position", "radius", "opacity"};

  curves.curve_types_for_write().fill(CURVE_TYPE_POLY);
  curves.update_curve_types();

  bke::SpanAttributeWriter<int> materials = attributes.lookup_or_add_for_write_span<int>(
      "material_index", bke::AttrDomain::Curve);
  bke::SpanAttributeWriter<bool> cyclic = attributes.lookup_or_add_for_write_span<bool>(
      "cyclic", bke::AttrDomain::Curve);
  bke::SpanAttributeWriter<float> hardnesses = attributes.lookup_or_add_for_write_span<float>(
      "hardness",
      bke::AttrDomain::Curve,
      bke::AttributeInitVArray(VArray<float>::ForSingle(1.0f, curves.curves_num())));
  bke::SpanAttributeWriter<float> radii = attributes.lookup_or_add_for_write_span<float>(
      "radius",
      bke::AttrDomain::Point,
      bke::AttributeInitVArray(VArray<float>::ForSingle(0.01f, curves.points_num())));
  bke::SpanAttributeWriter<float> opacities = attributes.lookup_or_add_for_write_span<float>(
      "opacity",
      bke::AttrDomain::Point,
      bke::AttributeInitVArray(VArray<float>::ForSingle(1.0f, curves.points_num())));

  cyclic.span.fill(true);
  materials.span.fill(material_index);
  hardnesses.span.fill(hardness);

  cyclic.finish();
  materials.finish();
  hardnesses.finish();

  for (const int point_i : curves.points_range()) {
    const int pixel_index = boundary.pixels[point_i];
    const int2 pixel_coord = buffer.coord_from_index(pixel_index);
    const float3 position = placement.project(float2(pixel_coord));
    positions[point_i] = position;

    /* Calculate radius and opacity for the outline as if it was a user stroke with full pressure.
     */
    constexpr const float pressure = 1.0f;
    radii.span[point_i] = ed::greasepencil::radius_from_input_sample(
        pressure, position, view_context, &brush, &scene, brush.gpencil_settings);
    opacities.span[point_i] = ed::greasepencil::opacity_from_input_sample(
        pressure, &brush, &scene, brush.gpencil_settings);
  }

  if (scene.toolsettings->gp_paint->mode == GPPAINT_FLAG_USE_VERTEXCOLOR) {
    ColorGeometry4f vertex_color;
    srgb_to_linearrgb_v3_v3(vertex_color, brush.rgb);
    vertex_color.a = brush.gpencil_settings->vertex_factor;

    if (ELEM(brush.gpencil_settings->vertex_mode, GPPAINT_MODE_FILL, GPPAINT_MODE_BOTH)) {
      skip_curve_attributes.add("fill_color");
      bke::SpanAttributeWriter<ColorGeometry4f> fill_colors =
          attributes.lookup_or_add_for_write_span<ColorGeometry4f>("fill_color",
                                                                   bke::AttrDomain::Curve);
      fill_colors.span.fill(vertex_color);
      fill_colors.finish();
    }
    if (ELEM(brush.gpencil_settings->vertex_mode, GPPAINT_MODE_STROKE, GPPAINT_MODE_BOTH)) {
      skip_point_attributes.add("vertex_color");
      bke::SpanAttributeWriter<ColorGeometry4f> vertex_colors =
          attributes.lookup_or_add_for_write_span<ColorGeometry4f>("vertex_color",
                                                                   bke::AttrDomain::Point);
      vertex_colors.span.fill(vertex_color);
      vertex_colors.finish();
    }
  }

  radii.finish();
  opacities.finish();

  /* Initialize the rest of the attributes with default values. */
  bke::fill_attribute_range_default(
      attributes, bke::AttrDomain::Curve, skip_curve_attributes, curves.curves_range());
  bke::fill_attribute_range_default(
      attributes, bke::AttrDomain::Point, skip_point_attributes, curves.points_range());

  return curves;
}

static bke::CurvesGeometry process_image(Image &ima,
                                         const Scene &scene,
                                         const ViewContext &view_context,
                                         const Brush &brush,
                                         const ed::greasepencil::DrawingPlacement &placement,
                                         const int stroke_material_index,
                                         const float stroke_hardness,
                                         const bool invert,
                                         const bool output_as_colors)
{
  constexpr const int leak_filter_width = 3;

  ImageBufferAccessor buffer;
  buffer.acquire(ima);
  BLI_SCOPED_DEFER([&]() {
    if (output_as_colors) {
      /* For visual output convert bit flags back to colors. */
      convert_flags_to_colors(buffer);
    }
    buffer.release();
  });

  convert_colors_to_flags(buffer);

  /* Set red borders to create a external limit. */
  mark_borders(buffer);

  /* Apply boundary fill */
  if (invert) {
    /* When inverted accept border fill, image borders are valid boundaries. */
    FillResult fill_result = flood_fill<FillBorderMode::Ignore>(buffer, leak_filter_width);
    if (!ELEM(fill_result, FillResult::Success, FillResult::BorderContact)) {
      return {};
    }
    /* Make fills into boundaries and vice versa for finding exterior boundaries. */
    invert_fill(buffer);
  }
  else {
    /* Cancel when encountering a border, counts as failure. */
    FillResult fill_result = flood_fill<FillBorderMode::Cancel>(buffer, leak_filter_width);
    if (fill_result != FillResult::Success) {
      return {};
    }
  }

  const FillBoundary boundary = build_fill_boundary(buffer);

  return boundary_to_curves(scene,
                            view_context,
                            brush,
                            boundary,
                            buffer,
                            placement,
                            stroke_material_index,
                            stroke_hardness);
}

/** \} */

constexpr const char *attr_material_index = "material_index";
constexpr const char *attr_is_boundary = "is_boundary";

static IndexMask get_visible_boundary_strokes(const Object &object,
                                              const DrawingInfo &info,
                                              const bool is_boundary_layer,
                                              IndexMaskMemory &memory)
{
  const bke::CurvesGeometry &strokes = info.drawing.strokes();
  const bke::AttributeAccessor attributes = strokes.attributes();
  const VArray<int> materials = *attributes.lookup<int>(attr_material_index,
                                                        bke::AttrDomain::Curve);

  auto is_visible_curve = [&](const int curve_i) {
    /* Check if stroke can be drawn. */
    const IndexRange points = strokes.points_by_curve()[curve_i];
    if (points.size() < 2) {
      return false;
    }

    /* Check if the material is visible. */
    const Material *material = BKE_object_material_get(const_cast<Object *>(&object),
                                                       materials[curve_i] + 1);
    const MaterialGPencilStyle *gp_style = material ? material->gp_style : nullptr;
    const bool is_hidden_material = (gp_style->flag & GP_MATERIAL_HIDE);
    const bool is_stroke_material = (gp_style->flag & GP_MATERIAL_STROKE_SHOW);
    if (gp_style == nullptr || is_hidden_material || !is_stroke_material) {
      return false;
    }

    return true;
  };

  /* On boundary layers only boundary strokes are rendered. */
  if (is_boundary_layer) {
    const VArray<bool> boundary_strokes = *attributes.lookup_or_default<bool>(
        attr_is_boundary, bke::AttrDomain::Curve, false);

    return IndexMask::from_predicate(
        strokes.curves_range(), GrainSize(512), memory, [&](const int curve_i) {
          if (!is_visible_curve(curve_i)) {
            return false;
          }
          const bool is_boundary_stroke = boundary_strokes[curve_i];
          return is_boundary_stroke;
        });
  }

  return IndexMask::from_predicate(
      strokes.curves_range(), GrainSize(512), memory, is_visible_curve);
}

static VArray<ColorGeometry4f> stroke_colors(const Object &object,
                                             const bke::CurvesGeometry &curves,
                                             const VArray<float> &opacities,
                                             const VArray<int> materials,
                                             const ColorGeometry4f &tint_color,
                                             const float alpha_threshold,
                                             const bool brush_fill_hide)
{
  if (brush_fill_hide) {
    return VArray<ColorGeometry4f>::ForSingle(tint_color, curves.points_num());
  }

  Array<ColorGeometry4f> colors(curves.points_num());
  threading::parallel_for(curves.curves_range(), 512, [&](const IndexRange range) {
    for (const int curve_i : range) {
      const Material *material = BKE_object_material_get(const_cast<Object *>(&object),
                                                         materials[curve_i] + 1);
      const float material_alpha = material && material->gp_style ?
                                       material->gp_style->stroke_rgba[3] :
                                       1.0f;
      const IndexRange points = curves.points_by_curve()[curve_i];
      for (const int point_i : points) {
        const float alpha = (material_alpha * opacities[point_i] > alpha_threshold ? 1.0f : 0.0f);
        colors[point_i] = ColorGeometry4f(tint_color.r, tint_color.g, tint_color.b, alpha);
      }
    }
  });
  return VArray<ColorGeometry4f>::ForContainer(colors);
}

static rctf get_region_bounds(const ARegion &region)
{
  /* Initialize maximum bound-box size. */
  rctf region_bounds;
  BLI_rctf_init(&region_bounds, 0, region.winx, 0, region.winy);
  return region_bounds;
}

/* Helper: Calc the maximum bounding box size of strokes to get the zoom level of the viewport.
 * For each stroke, the 2D projected bounding box is calculated and using this data, the total
 * object bounding box (all strokes) is calculated. */
static rctf get_boundary_bounds(const ARegion &region,
                                const RegionView3D &rv3d,
                                const Object &object,
                                const Object &object_eval,
                                const VArray<bool> &boundary_layers,
                                const Span<DrawingInfo> src_drawings)
{
  using bke::greasepencil::Drawing;
  using bke::greasepencil::Layer;

  rctf bounds;
  BLI_rctf_init_minmax(&bounds);

  BLI_assert(object.type == OB_GREASE_PENCIL);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object.data);

  BLI_assert(grease_pencil.has_active_layer());

  for (const DrawingInfo &info : src_drawings) {
    const Layer &layer = *grease_pencil.layers()[info.layer_index];
    const float4x4 layer_to_world = layer.to_world_space(object);
    const bke::crazyspace::GeometryDeformation deformation =
        bke::crazyspace::get_evaluated_grease_pencil_drawing_deformation(
            &object_eval, object, info.layer_index, info.frame_number);
    const bool only_boundary_strokes = boundary_layers[info.layer_index];
    const VArray<float> radii = info.drawing.radii();
    const bke::CurvesGeometry &strokes = info.drawing.strokes();
    const bke::AttributeAccessor attributes = strokes.attributes();
    const VArray<int> materials = *attributes.lookup<int>(attr_material_index,
                                                          bke::AttrDomain::Curve);
    const VArray<bool> is_boundary_stroke = *attributes.lookup_or_default<bool>(
        "is_boundary", bke::AttrDomain::Curve, false);

    IndexMaskMemory curve_mask_memory;
    const IndexMask curve_mask = get_visible_boundary_strokes(
        object, info, only_boundary_strokes, curve_mask_memory);

    curve_mask.foreach_index(GrainSize(512), [&](const int curve_i) {
      const IndexRange points = strokes.points_by_curve()[curve_i];
      /* Check if stroke can be drawn. */
      if (points.size() < 2) {
        return;
      }
      /* Check if the color is visible. */
      const int material_index = materials[curve_i];
      Material *mat = BKE_object_material_get(const_cast<Object *>(&object), material_index + 1);
      if (mat == 0 || (mat->gp_style->flag & GP_MATERIAL_HIDE)) {
        return;
      }

      /* In boundary layers only boundary strokes should be rendered. */
      if (only_boundary_strokes && !is_boundary_stroke[curve_i]) {
        return;
      }

      for (const int point_i : points) {
        const float3 pos_world = math::transform_point(layer_to_world,
                                                       deformation.positions[point_i]);
        float2 pos_view;
        eV3DProjStatus result = ED_view3d_project_float_global(
            &region, pos_world, pos_view, V3D_PROJ_TEST_NOP);
        if (result == V3D_PROJ_RET_OK) {
          const float pixels = radii[point_i] / ED_view3d_pixel_size(&rv3d, pos_world);
          rctf point_rect;
          BLI_rctf_init_pt_radius(&point_rect, pos_view, pixels);
          BLI_rctf_union(&bounds, &point_rect);
        }
      }
    });
  }

  return bounds;
}

static auto fit_strokes_to_view(const ViewContext &view_context,
                                const VArray<bool> &boundary_layers,
                                const Span<DrawingInfo> src_drawings,
                                const FillToolFitMethod fit_method,
                                const float2 fill_point,
                                const bool uniform_zoom,
                                const float max_zoom_factor,
                                const float2 margin)
{
  BLI_assert(max_zoom_factor >= 1.0f);
  const float min_zoom_factor = math::safe_rcp(max_zoom_factor);

  switch (fit_method) {
    case FillToolFitMethod::None:
      return std::make_pair(float2(1.0f), float2(0.0f));

    case FillToolFitMethod::FitToView: {
      const Object &object_eval = *DEG_get_evaluated_object(view_context.depsgraph,
                                                            view_context.obact);
      /* Zoom and offset based on bounds, to fit all strokes within the render. */
      const rctf bounds = get_boundary_bounds(*view_context.region,
                                              *view_context.rv3d,
                                              *view_context.obact,
                                              object_eval,
                                              boundary_layers,
                                              src_drawings);
      const rctf region_bounds = get_region_bounds(*view_context.region);
      UNUSED_VARS(bounds, region_bounds);
      const float2 bounds_max = float2(bounds.xmax, bounds.ymax);
      const float2 bounds_min = float2(bounds.xmin, bounds.ymin);
      /* Include fill point for computing zoom. */
      const float2 fill_bounds_min = math::min(bounds_min, fill_point) - margin;
      const float2 fill_bounds_max = math::max(bounds_max, fill_point) + margin;
      const float2 fill_bounds_center = 0.5f * (fill_bounds_min + fill_bounds_max);
      const float2 fill_bounds_extent = fill_bounds_max - fill_bounds_min;

      const float2 region_max = float2(region_bounds.xmax, region_bounds.ymax);
      const float2 region_min = float2(region_bounds.xmin, region_bounds.ymin);
      const float2 region_center = 0.5f * (region_min + region_max);
      const float2 region_extent = region_max - region_min;

      const float2 zoom_factors = math::clamp(math::safe_divide(fill_bounds_extent, region_extent),
                                              float2(min_zoom_factor),
                                              float2(max_zoom_factor));
      /* Use the most zoomed out factor for uniform scale. */
      const float2 zoom = uniform_zoom ? float2(math::reduce_max(zoom_factors)) : zoom_factors;

      /* Clamp offset to always include the center point. */
      const float2 offset_center = fill_bounds_center - region_center;
      const float2 offset_min = fill_point + 0.5f * fill_bounds_extent - region_center;
      const float2 offset_max = fill_point - 0.5f * fill_bounds_extent - region_center;
      const float2 region_offset = float2(
          fill_point.x < bounds_min.x ?
              offset_min.x :
              (fill_point.x > bounds_max.x ? offset_max.x : offset_center.x),
          fill_point.y < bounds_min.y ?
              offset_min.y :
              (fill_point.y > bounds_max.y ? offset_max.y : offset_center.y));
      const float2 offset = math::safe_divide(region_offset, region_extent);

      return std::make_pair(zoom, offset);
    }
  }

  return std::make_pair(float2(1.0f), float2(0.0f));
}

bke::CurvesGeometry fill_strokes(const ViewContext &view_context,
                                 const Brush &brush,
                                 const Scene &scene,
                                 const bke::greasepencil::Layer &layer,
                                 const VArray<bool> &boundary_layers,
                                 const Span<DrawingInfo> src_drawings,
                                 const bool invert,
                                 const float2 &fill_point,
                                 const FillToolFitMethod fit_method,
                                 const int stroke_material_index,
                                 const bool keep_images)
{
  using bke::greasepencil::Layer;

  ARegion &region = *view_context.region;
  View3D &view3d = *view_context.v3d;
  RegionView3D &rv3d = *view_context.rv3d;
  Depsgraph &depsgraph = *view_context.depsgraph;
  Object &object = *view_context.obact;

  BLI_assert(object.type == OB_GREASE_PENCIL);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object.data);
  const Object &object_eval = *DEG_get_evaluated_object(&depsgraph, &object);

  // TODO based on the fill_factor (aka "Precision") setting.
  constexpr const int min_window_size = 128;
  const float pixel_scale = 1.0f;
  const int2 win_size = math::max(int2(region.winx, region.winy) * pixel_scale,
                                  int2(min_window_size));
  const float2 win_center = 0.5f * float2(win_size);

  /* Zoom and offset based on bounds, to fit all strokes within the render. */
  const bool uniform_zoom = true;
  const float max_zoom_factor = 5.0f;
  const float2 margin = float2(20);
  const auto [zoom, offset] = fit_strokes_to_view(view_context,
                                                  boundary_layers,
                                                  src_drawings,
                                                  fit_method,
                                                  fill_point,
                                                  uniform_zoom,
                                                  max_zoom_factor,
                                                  margin);
  /* Fill point needs to be inverse transformed to stay relative to the view. */
  const float2 fill_point_view = math::safe_divide(
                                     fill_point - win_center - offset * float2(win_size), zoom) +
                                 win_center;

  image_render::RegionViewData region_view_data = image_render::region_init(region, win_size);

  GPUOffScreen *offscreen_buffer = image_render::image_render_begin(win_size);
  GPU_blend(GPU_BLEND_ALPHA);
  GPU_depth_mask(true);
  image_render::set_viewmat(view_context, scene, win_size, zoom, offset);

  const eGP_FillDrawModes fill_draw_mode = GP_FILL_DMODE_BOTH;
  const float alpha_threshold = 0.2f;
  const bool brush_fill_hide = false;
  const bool use_xray = false;

  const float4x4 layer_to_world = layer.to_world_space(object);
  ed::greasepencil::DrawingPlacement placement(scene, region, view3d, object_eval, layer);
  const float3 fill_point_world = math::transform_point(layer_to_world,
                                                        placement.project(fill_point_view));

  /* Draw blue point where click with mouse. */
  const float mouse_dot_size = 4.0f;
  image_render::draw_dot(fill_point_world, mouse_dot_size, draw_seed_color);

  for (const DrawingInfo &info : src_drawings) {
    const Layer &layer = *grease_pencil.layers()[info.layer_index];
    if (!layer.is_visible()) {
      continue;
    }
    const float4x4 layer_to_world = layer.to_world_space(object);
    const bool is_boundary_layer = boundary_layers[info.layer_index];
    const bke::CurvesGeometry &strokes = info.drawing.strokes();
    const bke::AttributeAccessor attributes = strokes.attributes();
    const VArray<float> opacities = info.drawing.opacities();
    const VArray<int> materials = *attributes.lookup<int>(attr_material_index,
                                                          bke::AttrDomain::Curve);

    IndexMaskMemory curve_mask_memory;
    const IndexMask curve_mask = get_visible_boundary_strokes(
        object, info, is_boundary_layer, curve_mask_memory);

    const VArray<ColorGeometry4f> colors = stroke_colors(object,
                                                         info.drawing.strokes(),
                                                         opacities,
                                                         materials,
                                                         draw_boundary_color,
                                                         alpha_threshold,
                                                         brush_fill_hide);

    image_render::draw_grease_pencil_strokes(rv3d,
                                             win_size,
                                             object,
                                             info.drawing,
                                             curve_mask,
                                             colors,
                                             layer_to_world,
                                             fill_draw_mode,
                                             use_xray);
  }

  image_render::clear_viewmat();
  GPU_depth_mask(false);
  GPU_blend(GPU_BLEND_NONE);
  Image *ima = image_render::image_render_end(*view_context.bmain, offscreen_buffer);
  if (!ima) {
    return {};
  }

  /* TODO should use the same hardness as the paint tool. */
  const float stroke_hardness = 1.0f;

  bke::CurvesGeometry fill_curves = process_image(*ima,
                                                  scene,
                                                  view_context,
                                                  brush,
                                                  placement,
                                                  stroke_material_index,
                                                  stroke_hardness,
                                                  invert,
                                                  keep_images);

  /* Note: Region view reset has to happen after final curve construction, otherwise the curve
   * placement, used to re-project from the 2D pixel coordinates, will have the wrong view
   * transform. */
  image_render::region_reset(region, region_view_data);

  if (!keep_images) {
    BKE_id_free(view_context.bmain, ima);
  }

  return fill_curves;
}

}  // namespace blender::ed::greasepencil
