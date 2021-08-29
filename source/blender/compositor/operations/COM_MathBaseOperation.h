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

#include "COM_MultiThreadedOperation.h"

namespace blender::compositor {

/**
 * this program converts an input color to an output value.
 * it assumes we are in sRGB color space.
 */
class MathBaseOperation : public MultiThreadedOperation {
 protected:
  /**
   * Prefetched reference to the inputProgram
   */
  SocketReader *m_inputValue1Operation;
  SocketReader *m_inputValue2Operation;
  SocketReader *m_inputValue3Operation;

  bool m_useClamp;

 protected:
  /**
   * Default constructor
   */
  MathBaseOperation();

  /* TODO(manzanilla): to be removed with tiled implementation. */
  void clampIfNeeded(float color[4]);

  float clamp_when_enabled(float value)
  {
    if (this->m_useClamp) {
      return CLAMPIS(value, 0.0f, 1.0f);
    }
    return value;
  }

  void clamp_when_enabled(float *out)
  {
    if (this->m_useClamp) {
      CLAMP(*out, 0.0f, 1.0f);
    }
  }

 public:
  /**
   * Initialize the execution
   */
  void initExecution() override;

  /**
   * Deinitialize the execution
   */
  void deinitExecution() override;

  /**
   * Determine resolution
   */
  void determineResolution(unsigned int resolution[2],
                           unsigned int preferredResolution[2]) override;

  void setUseClamp(bool value)
  {
    this->m_useClamp = value;
  }

  void update_memory_buffer_partial(MemoryBuffer *output,
                                    const rcti &area,
                                    Span<MemoryBuffer *> inputs) final;

 protected:
  virtual void update_memory_buffer_partial(BuffersIterator<float> &it) = 0;
};

template<template<typename> typename TFunctor>
class MathFunctor2Operation : public MathBaseOperation {
  void update_memory_buffer_partial(BuffersIterator<float> &it) final
  {
    TFunctor functor;
    for (; !it.is_end(); ++it) {
      *it.out = functor(*it.in(0), *it.in(1));
      clamp_when_enabled(it.out);
    }
  }
};

class MathAddOperation : public MathFunctor2Operation<std::plus> {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;
};
class MathSubtractOperation : public MathFunctor2Operation<std::minus> {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;
};
class MathMultiplyOperation : public MathFunctor2Operation<std::multiplies> {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;
};
class MathDivideOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};
class MathSineOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};
class MathCosineOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};
class MathTangentOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathHyperbolicSineOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};
class MathHyperbolicCosineOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};
class MathHyperbolicTangentOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathArcSineOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};
class MathArcCosineOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};
class MathArcTangentOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};
class MathPowerOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};
class MathLogarithmOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};
class MathMinimumOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};
class MathMaximumOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};
class MathRoundOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};
class MathLessThanOperation : public MathFunctor2Operation<std::less> {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;
};
class MathGreaterThanOperation : public MathFunctor2Operation<std::greater> {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;
};

class MathModuloOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathAbsoluteOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathRadiansOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathDegreesOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathArcTan2Operation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathFloorOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathCeilOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathFractOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathSqrtOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathInverseSqrtOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathSignOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathExponentOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathTruncOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathSnapOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathWrapOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathPingpongOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathCompareOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathMultiplyAddOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathSmoothMinOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

class MathSmoothMaxOperation : public MathBaseOperation {
 public:
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

 protected:
  void update_memory_buffer_partial(BuffersIterator<float> &it) override;
};

}  // namespace blender::compositor
