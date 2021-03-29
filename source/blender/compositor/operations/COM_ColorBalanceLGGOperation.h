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

#pragma once

#include "COM_NodeOperation.h"

namespace blender::compositor {

/**
 * this program converts an input color to an output value.
 * it assumes we are in sRGB color space.
 */
class ColorBalanceLGGOperation : public NodeOperation {
 protected:
  /**
   * Prefetched reference to the inputProgram
   */
  SocketReader *m_inputValueOperation;
  SocketReader *m_inputColorOperation;

  float m_gain[3];
  float m_lift[3];
  float m_gamma_inv[3];

 public:
  /**
   * Default constructor
   */
  ColorBalanceLGGOperation();

  /**
   * The inner loop of this operation.
   */
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

  /**
   * Initialize the execution
   */
  void initExecution() override;

  /**
   * Deinitialize the execution
   */
  void deinitExecution() override;

  void setGain(const float gain[3])
  {
    copy_v3_v3(this->m_gain, gain);
  }
  void setLift(const float lift[3])
  {
    copy_v3_v3(this->m_lift, lift);
  }
  void setGammaInv(const float gamma_inv[3])
  {
    copy_v3_v3(this->m_gamma_inv, gamma_inv);
  }
};

}  // namespace blender::compositor
