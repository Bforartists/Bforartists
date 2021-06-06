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

#include "COM_CompositorContext.h"
#include "COM_defines.h"
#include <cstdio>

#include "BLI_assert.h"
#include "DNA_userdef_types.h"

namespace blender::compositor {

CompositorContext::CompositorContext()
{
  this->m_scene = nullptr;
  this->m_rd = nullptr;
  this->m_quality = eCompositorQuality::High;
  this->m_hasActiveOpenCLDevices = false;
  this->m_fastCalculation = false;
  this->m_viewSettings = nullptr;
  this->m_displaySettings = nullptr;
  this->m_bnodetree = nullptr;
}

int CompositorContext::getFramenumber() const
{
  BLI_assert(m_rd);
  return m_rd->cfra;
}

eExecutionModel CompositorContext::get_execution_model() const
{
  if (U.experimental.use_full_frame_compositor) {
    BLI_assert(m_bnodetree != nullptr);
    switch (m_bnodetree->execution_mode) {
      case 1:
        return eExecutionModel::FullFrame;
      case 0:
        return eExecutionModel::Tiled;
      default:
        BLI_assert(!"Invalid execution mode");
    }
  }
  return eExecutionModel::Tiled;
}

}  // namespace blender::compositor
