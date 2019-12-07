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

#ifndef __COM_MATHBASEOPERATION_H__
#define __COM_MATHBASEOPERATION_H__
#include "COM_NodeOperation.h"

/**
 * this program converts an input color to an output value.
 * it assumes we are in sRGB color space.
 */
class MathBaseOperation : public NodeOperation {
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

  void clampIfNeeded(float color[4]);

 public:
  /**
   * the inner loop of this program
   */
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) = 0;

  /**
   * Initialize the execution
   */
  void initExecution();

  /**
   * Deinitialize the execution
   */
  void deinitExecution();

  /**
   * Determine resolution
   */
  void determineResolution(unsigned int resolution[2], unsigned int preferredResolution[2]);

  void setUseClamp(bool value)
  {
    this->m_useClamp = value;
  }
};

class MathAddOperation : public MathBaseOperation {
 public:
  MathAddOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathSubtractOperation : public MathBaseOperation {
 public:
  MathSubtractOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathMultiplyOperation : public MathBaseOperation {
 public:
  MathMultiplyOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathDivideOperation : public MathBaseOperation {
 public:
  MathDivideOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathSineOperation : public MathBaseOperation {
 public:
  MathSineOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathCosineOperation : public MathBaseOperation {
 public:
  MathCosineOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathTangentOperation : public MathBaseOperation {
 public:
  MathTangentOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathHyperbolicSineOperation : public MathBaseOperation {
 public:
  MathHyperbolicSineOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathHyperbolicCosineOperation : public MathBaseOperation {
 public:
  MathHyperbolicCosineOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathHyperbolicTangentOperation : public MathBaseOperation {
 public:
  MathHyperbolicTangentOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathArcSineOperation : public MathBaseOperation {
 public:
  MathArcSineOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathArcCosineOperation : public MathBaseOperation {
 public:
  MathArcCosineOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathArcTangentOperation : public MathBaseOperation {
 public:
  MathArcTangentOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathPowerOperation : public MathBaseOperation {
 public:
  MathPowerOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathLogarithmOperation : public MathBaseOperation {
 public:
  MathLogarithmOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathMinimumOperation : public MathBaseOperation {
 public:
  MathMinimumOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathMaximumOperation : public MathBaseOperation {
 public:
  MathMaximumOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathRoundOperation : public MathBaseOperation {
 public:
  MathRoundOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathLessThanOperation : public MathBaseOperation {
 public:
  MathLessThanOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
class MathGreaterThanOperation : public MathBaseOperation {
 public:
  MathGreaterThanOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathModuloOperation : public MathBaseOperation {
 public:
  MathModuloOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathAbsoluteOperation : public MathBaseOperation {
 public:
  MathAbsoluteOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathRadiansOperation : public MathBaseOperation {
 public:
  MathRadiansOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathDegreesOperation : public MathBaseOperation {
 public:
  MathDegreesOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathArcTan2Operation : public MathBaseOperation {
 public:
  MathArcTan2Operation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathFloorOperation : public MathBaseOperation {
 public:
  MathFloorOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathCeilOperation : public MathBaseOperation {
 public:
  MathCeilOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathFractOperation : public MathBaseOperation {
 public:
  MathFractOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathSqrtOperation : public MathBaseOperation {
 public:
  MathSqrtOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathInverseSqrtOperation : public MathBaseOperation {
 public:
  MathInverseSqrtOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathSignOperation : public MathBaseOperation {
 public:
  MathSignOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathExponentOperation : public MathBaseOperation {
 public:
  MathExponentOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathTruncOperation : public MathBaseOperation {
 public:
  MathTruncOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathSnapOperation : public MathBaseOperation {
 public:
  MathSnapOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathWrapOperation : public MathBaseOperation {
 public:
  MathWrapOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathPingpongOperation : public MathBaseOperation {
 public:
  MathPingpongOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathCompareOperation : public MathBaseOperation {
 public:
  MathCompareOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathMultiplyAddOperation : public MathBaseOperation {
 public:
  MathMultiplyAddOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathSmoothMinOperation : public MathBaseOperation {
 public:
  MathSmoothMinOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};

class MathSmoothMaxOperation : public MathBaseOperation {
 public:
  MathSmoothMaxOperation() : MathBaseOperation()
  {
  }
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler);
};
#endif
