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
 * Copyright 2011, Blender Foundation.
 */

#ifndef __COM_RENDERLAYERSNODE_H__
#define __COM_RENDERLAYERSNODE_H__

#include "COM_Node.h"
#include "COM_RenderLayersProg.h"
#include "DNA_node_types.h"

struct Render;

/**
 * \brief RenderLayersNode
 * \ingroup Node
 */
class RenderLayersNode : public Node {
 public:
  RenderLayersNode(bNode *editorNode);
  void convertToOperations(NodeConverter &converter, const CompositorContext &context) const;

 private:
  void testSocketLink(NodeConverter &converter,
                      const CompositorContext &context,
                      NodeOutput *output,
                      RenderLayersProg *operation,
                      Scene *scene,
                      int layerId,
                      bool is_preview) const;
  void testRenderLink(NodeConverter &converter,
                      const CompositorContext &context,
                      Render *re) const;

  void missingSocketLink(NodeConverter &converter, NodeOutput *output) const;
  void missingRenderLink(NodeConverter &converter) const;
};

#endif /* __COM_RENDERLAYERSNODE_H__ */
