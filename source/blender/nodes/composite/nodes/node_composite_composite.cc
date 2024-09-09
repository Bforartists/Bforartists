/* SPDX-FileCopyrightText: 2006 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup cmpnodes
 */

#include "BLI_bounds_types.hh"
#include "BLI_math_vector_types.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "GPU_shader.hh"
#include "GPU_texture.hh"

#include "COM_node_operation.hh"
#include "COM_utilities.hh"

#include "node_composite_util.hh"

/* **************** COMPOSITE ******************** */

namespace blender::nodes::node_composite_composite_cc {

static void cmp_node_composite_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Color>("Image").default_value({0.0f, 0.0f, 0.0f, 1.0f});
  b.add_input<decl::Float>("Alpha").default_value(1.0f).min(0.0f).max(1.0f);
}

static void node_composit_buts_composite(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiItemR(layout, ptr, "use_alpha", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
}

using namespace blender::realtime_compositor;

class CompositeOperation : public NodeOperation {
 public:
  using NodeOperation::NodeOperation;

  void execute() override
  {
    if (!context().is_valid_compositing_region()) {
      return;
    }

    const Result &image = get_input("Image");
    const Result &alpha = get_input("Alpha");
    if (image.is_single_value() && alpha.is_single_value()) {
      execute_clear();
    }
    else if (ignore_alpha()) {
      execute_ignore_alpha();
    }
    else if (!node().input_by_identifier("Alpha")->is_logically_linked()) {
      execute_copy();
    }
    else {
      execute_set_alpha();
    }
  }

  /* Executes when all inputs are single values, in which case, the output texture can just be
   * cleared to the appropriate color. */
  void execute_clear()
  {
    const Result &image = get_input("Image");
    const Result &alpha = get_input("Alpha");

    float4 color = image.get_color_value();
    if (ignore_alpha()) {
      color.w = 1.0f;
    }
    else if (node().input_by_identifier("Alpha")->is_logically_linked()) {
      color.w = alpha.get_float_value();
    }

    const Domain domain = compute_domain();
    Result output = context().get_output_result();
    if (this->context().use_gpu()) {
      GPU_texture_clear(output, GPU_DATA_FLOAT, color);
    }
    else {
      parallel_for(domain.size, [&](const int2 texel) { output.store_pixel(texel, color); });
    }
  }

  /* Executes when the alpha channel of the image is ignored. */
  void execute_ignore_alpha()
  {
    if (context().use_gpu()) {
      this->execute_ignore_alpha_gpu();
    }
    else {
      this->execute_ignore_alpha_cpu();
    }
  }

  void execute_ignore_alpha_gpu()
  {
    const Result &image = get_input("Image");
    const Domain domain = compute_domain();
    Result output = context().get_output_result();

    GPUShader *shader = context().get_shader("compositor_write_output_opaque", output.precision());
    GPU_shader_bind(shader);

    const Bounds<int2> bounds = get_output_bounds();
    GPU_shader_uniform_2iv(shader, "lower_bound", bounds.min);
    GPU_shader_uniform_2iv(shader, "upper_bound", bounds.max);

    image.bind_as_texture(shader, "input_tx");

    output.bind_as_image(shader, "output_img");

    compute_dispatch_threads_at_least(shader, domain.size);

    image.unbind_as_texture();
    output.unbind_as_image();
    GPU_shader_unbind();
  }

  void execute_ignore_alpha_cpu()
  {
    const Domain domain = compute_domain();
    const Result &image = get_input("Image");
    Result output = context().get_output_result();

    const Bounds<int2> bounds = get_output_bounds();
    parallel_for(domain.size, [&](const int2 texel) {
      const int2 output_texel = texel + bounds.min;
      if (output_texel.x > bounds.max.x || output_texel.y > bounds.max.y) {
        return;
      }
      output.store_pixel(texel + bounds.min, float4(image.load_pixel(texel).xyz(), 1.0f));
    });
  }

  /* Executes when the image texture is written with no adjustments and can thus be copied directly
   * to the output. */
  void execute_copy()
  {
    if (context().use_gpu()) {
      this->execute_copy_gpu();
    }
    else {
      this->execute_copy_cpu();
    }
  }

  void execute_copy_gpu()
  {
    const Result &image = get_input("Image");
    const Domain domain = compute_domain();
    Result output = context().get_output_result();

    GPUShader *shader = context().get_shader("compositor_write_output", output.precision());
    GPU_shader_bind(shader);

    const Bounds<int2> bounds = get_output_bounds();
    GPU_shader_uniform_2iv(shader, "lower_bound", bounds.min);
    GPU_shader_uniform_2iv(shader, "upper_bound", bounds.max);

    image.bind_as_texture(shader, "input_tx");

    output.bind_as_image(shader, "output_img");

    compute_dispatch_threads_at_least(shader, domain.size);

    image.unbind_as_texture();
    output.unbind_as_image();
    GPU_shader_unbind();
  }

  void execute_copy_cpu()
  {
    const Domain domain = compute_domain();
    const Result &image = get_input("Image");
    Result output = context().get_output_result();

    const Bounds<int2> bounds = get_output_bounds();
    parallel_for(domain.size, [&](const int2 texel) {
      const int2 output_texel = texel + bounds.min;
      if (output_texel.x > bounds.max.x || output_texel.y > bounds.max.y) {
        return;
      }
      output.store_pixel(texel + bounds.min, image.load_pixel(texel));
    });
  }

  /* Executes when the alpha channel of the image is set as the value of the input alpha. */
  void execute_set_alpha()
  {
    if (context().use_gpu()) {
      execute_set_alpha_gpu();
    }
    else {
      execute_set_alpha_cpu();
    }
  }

  void execute_set_alpha_gpu()
  {
    const Result &image = get_input("Image");
    const Domain domain = compute_domain();
    Result output = context().get_output_result();

    GPUShader *shader = context().get_shader("compositor_write_output_alpha", output.precision());
    GPU_shader_bind(shader);

    const Bounds<int2> bounds = get_output_bounds();
    GPU_shader_uniform_2iv(shader, "lower_bound", bounds.min);
    GPU_shader_uniform_2iv(shader, "upper_bound", bounds.max);

    image.bind_as_texture(shader, "input_tx");

    const Result &alpha = get_input("Alpha");
    alpha.bind_as_texture(shader, "alpha_tx");

    output.bind_as_image(shader, "output_img");

    compute_dispatch_threads_at_least(shader, domain.size);

    image.unbind_as_texture();
    alpha.unbind_as_texture();
    output.unbind_as_image();
    GPU_shader_unbind();
  }

  void execute_set_alpha_cpu()
  {
    const Domain domain = compute_domain();
    const Result &image = get_input("Image");
    const Result &alpha = get_input("Alpha");
    Result output = context().get_output_result();

    const Bounds<int2> bounds = get_output_bounds();
    parallel_for(domain.size, [&](const int2 texel) {
      const int2 output_texel = texel + bounds.min;
      if (output_texel.x > bounds.max.x || output_texel.y > bounds.max.y) {
        return;
      }
      output.store_pixel(texel + bounds.min,
                         float4(image.load_pixel(texel).xyz(), alpha.load_pixel(texel).x));
    });
  }

  /* Returns the bounds of the area of the compositing region. Only write into the compositing
   * region, which might be limited to a smaller region of the output result. */
  Bounds<int2> get_output_bounds()
  {
    const rcti compositing_region = context().get_compositing_region();
    return Bounds<int2>(int2(compositing_region.xmin, compositing_region.ymin),
                        int2(compositing_region.xmax, compositing_region.ymax));
  }

  /* If true, the alpha channel of the image is set to 1, that is, it becomes opaque. If false, the
   * alpha channel of the image is retained, but only if the alpha input is not linked. If the
   * alpha input is linked, it the value of that input will be used as the alpha of the image. */
  bool ignore_alpha()
  {
    return bnode().custom2 & CMP_NODE_OUTPUT_IGNORE_ALPHA;
  }

  /* The operation domain has the same size as the compositing region without any transformations
   * applied. */
  Domain compute_domain() override
  {
    return Domain(context().get_compositing_region_size());
  }
};

static NodeOperation *get_compositor_operation(Context &context, DNode node)
{
  return new CompositeOperation(context, node);
}

}  // namespace blender::nodes::node_composite_composite_cc

void register_node_type_cmp_composite()
{
  namespace file_ns = blender::nodes::node_composite_composite_cc;

  static blender::bke::bNodeType ntype;

  cmp_node_type_base(&ntype, CMP_NODE_COMPOSITE, "Composite", NODE_CLASS_OUTPUT);
  ntype.declare = file_ns::cmp_node_composite_declare;
  ntype.draw_buttons = file_ns::node_composit_buts_composite;
  ntype.get_compositor_operation = file_ns::get_compositor_operation;
  ntype.no_muting = true;

  blender::bke::node_register_type(&ntype);
}
