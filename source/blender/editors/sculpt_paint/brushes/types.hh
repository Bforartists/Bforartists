/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "BLI_span.hh"

struct Depsgraph;
struct Scene;
struct Sculpt;
struct Object;
namespace blender::bke::pbvh {
class Node;
}

namespace blender::ed::sculpt_paint {

void do_clay_brush(const Depsgraph &depsgraph,
                   const Sculpt &sd,
                   Object &ob,
                   Span<bke::pbvh::Node *> nodes);
void do_clay_strips_brush(const Depsgraph &depsgraph,
                          const Sculpt &sd,
                          Object &ob,
                          Span<bke::pbvh::Node *> nodes);
void do_clay_thumb_brush(const Depsgraph &depsgraph,
                         const Sculpt &sd,
                         Object &ob,
                         Span<bke::pbvh::Node *> nodes);
void do_crease_brush(const Depsgraph &depsgraph,
                     const Scene &scene,
                     const Sculpt &sd,
                     Object &ob,
                     Span<bke::pbvh::Node *> nodes);
void do_blob_brush(const Depsgraph &depsgraph,
                   const Scene &scene,
                   const Sculpt &sd,
                   Object &ob,
                   Span<bke::pbvh::Node *> nodes);
void do_bmesh_topology_rake_brush(const Depsgraph &depsgraph,
                                  const Sculpt &sd,
                                  Object &ob,
                                  Span<bke::pbvh::Node *> nodes,
                                  float strength);
void do_displacement_eraser_brush(const Depsgraph &depsgraph,
                                  const Sculpt &sd,
                                  Object &ob,
                                  Span<bke::pbvh::Node *> nodes);
void do_displacement_smear_brush(const Depsgraph &depsgraph,
                                 const Sculpt &sd,
                                 Object &ob,
                                 Span<bke::pbvh::Node *> nodes);
void do_draw_face_sets_brush(const Depsgraph &depsgraph,
                             const Sculpt &sd,
                             Object &object,
                             Span<bke::pbvh::Node *> nodes);
/** A simple normal-direction displacement. */
void do_draw_brush(const Depsgraph &depsgraph,
                   const Sculpt &sd,
                   Object &object,
                   Span<bke::pbvh::Node *> nodes);
/** A simple normal-direction displacement based on image texture RGB/XYZ values. */
void do_draw_vector_displacement_brush(const Depsgraph &depsgraph,
                                       const Sculpt &sd,
                                       Object &object,
                                       Span<bke::pbvh::Node *> nodes);
void do_draw_sharp_brush(const Depsgraph &depsgraph,
                         const Sculpt &sd,
                         Object &object,
                         Span<bke::pbvh::Node *> nodes);
void do_elastic_deform_brush(const Depsgraph &depsgraph,
                             const Sculpt &sd,
                             Object &object,
                             Span<bke::pbvh::Node *> nodes);
void do_enhance_details_brush(const Depsgraph &depsgraph,
                              const Sculpt &sd,
                              Object &object,
                              Span<bke::pbvh::Node *> nodes);
void do_fill_brush(const Depsgraph &depsgraph,
                   const Sculpt &sd,
                   Object &object,
                   Span<bke::pbvh::Node *> nodes);
void do_flatten_brush(const Depsgraph &depsgraph,
                      const Sculpt &sd,
                      Object &ob,
                      Span<bke::pbvh::Node *> nodes);
void do_grab_brush(const Depsgraph &depsgraph,
                   const Sculpt &sd,
                   Object &ob,
                   Span<bke::pbvh::Node *> nodes);
void do_gravity_brush(const Depsgraph &depsgraph,
                      const Sculpt &sd,
                      Object &ob,
                      Span<bke::pbvh::Node *> nodes);
void do_inflate_brush(const Depsgraph &depsgraph,
                      const Sculpt &sd,
                      Object &ob,
                      Span<bke::pbvh::Node *> nodes);
void do_layer_brush(const Depsgraph &depsgraph,
                    const Sculpt &sd,
                    Object &object,
                    Span<bke::pbvh::Node *> nodes);
/** A brush that modifies mask values instead of position. */
void do_mask_brush(const Depsgraph &depsgraph,
                   const Sculpt &sd,
                   Object &object,
                   Span<bke::pbvh::Node *> nodes);
void do_multiplane_scrape_brush(const Depsgraph &depsgraph,
                                const Sculpt &sd,
                                Object &object,
                                Span<bke::pbvh::Node *> nodes);
void do_pinch_brush(const Depsgraph &depsgraph,
                    const Sculpt &sd,
                    Object &object,
                    Span<bke::pbvh::Node *> nodes);
void do_nudge_brush(const Depsgraph &depsgraph,
                    const Sculpt &sd,
                    Object &object,
                    Span<bke::pbvh::Node *> nodes);
void do_relax_face_sets_brush(const Depsgraph &depsgraph,
                              const Sculpt &sd,
                              Object &object,
                              Span<bke::pbvh::Node *> nodes);
void do_rotate_brush(const Depsgraph &depsgraph,
                     const Sculpt &sd,
                     Object &object,
                     Span<bke::pbvh::Node *> nodes);
void do_scrape_brush(const Depsgraph &depsgraph,
                     const Sculpt &sd,
                     Object &object,
                     Span<bke::pbvh::Node *> nodes);
/** Smooth positions with neighboring vertices. */
void do_smooth_brush(const Depsgraph &depsgraph,
                     const Sculpt &sd,
                     Object &object,
                     Span<bke::pbvh::Node *> nodes,
                     float brush_strength);
/** Smooth mask values with neighboring vertices. */
void do_smooth_mask_brush(const Depsgraph &depsgraph,
                          const Sculpt &sd,
                          Object &object,
                          Span<bke::pbvh::Node *> nodes,
                          float brush_strength);
void do_snake_hook_brush(const Depsgraph &depsgraph,
                         const Sculpt &sd,
                         Object &object,
                         Span<bke::pbvh::Node *> nodes);
void do_surface_smooth_brush(const Depsgraph &depsgraph,
                             const Sculpt &sd,
                             Object &object,
                             Span<bke::pbvh::Node *> nodes);
void do_thumb_brush(const Depsgraph &depsgraph,
                    const Sculpt &sd,
                    Object &object,
                    Span<bke::pbvh::Node *> nodes);
void do_topology_slide_brush(const Depsgraph &depsgraph,
                             const Sculpt &sd,
                             Object &object,
                             Span<bke::pbvh::Node *> nodes);
void do_topology_relax_brush(const Depsgraph &depsgraph,
                             const Sculpt &sd,
                             Object &object,
                             Span<bke::pbvh::Node *> nodes);

}  // namespace blender::ed::sculpt_paint
