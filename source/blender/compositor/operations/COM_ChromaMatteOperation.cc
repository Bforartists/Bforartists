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

#include "COM_ChromaMatteOperation.h"
#include "BLI_math.h"

namespace blender::compositor {

ChromaMatteOperation::ChromaMatteOperation()
{
  addInputSocket(DataType::Color);
  addInputSocket(DataType::Color);
  addOutputSocket(DataType::Value);

  this->m_inputImageProgram = nullptr;
  this->m_inputKeyProgram = nullptr;
  flags.can_be_constant = true;
}

void ChromaMatteOperation::initExecution()
{
  this->m_inputImageProgram = this->getInputSocketReader(0);
  this->m_inputKeyProgram = this->getInputSocketReader(1);
}

void ChromaMatteOperation::deinitExecution()
{
  this->m_inputImageProgram = nullptr;
  this->m_inputKeyProgram = nullptr;
}

void ChromaMatteOperation::executePixelSampled(float output[4],
                                               float x,
                                               float y,
                                               PixelSampler sampler)
{
  float inKey[4];
  float inImage[4];

  const float acceptance = this->m_settings->t1; /* in radians */
  const float cutoff = this->m_settings->t2;     /* in radians */
  const float gain = this->m_settings->fstrength;

  float x_angle, z_angle, alpha;
  float theta, beta;
  float kfg;

  this->m_inputKeyProgram->readSampled(inKey, x, y, sampler);
  this->m_inputImageProgram->readSampled(inImage, x, y, sampler);

  /* Store matte(alpha) value in [0] to go with
   * #COM_SetAlphaMultiplyOperation and the Value output. */

  /* Algorithm from book "Video Demystified", does not include the spill reduction part. */
  /* Find theta, the angle that the color space should be rotated based on key. */

  /* rescale to -1.0..1.0 */
  // inImage[0] = (inImage[0] * 2.0f) - 1.0f;  // UNUSED
  inImage[1] = (inImage[1] * 2.0f) - 1.0f;
  inImage[2] = (inImage[2] * 2.0f) - 1.0f;

  // inKey[0] = (inKey[0] * 2.0f) - 1.0f;  // UNUSED
  inKey[1] = (inKey[1] * 2.0f) - 1.0f;
  inKey[2] = (inKey[2] * 2.0f) - 1.0f;

  theta = atan2(inKey[2], inKey[1]);

  /* Rotate the cb and cr into x/z space. */
  x_angle = inImage[1] * cosf(theta) + inImage[2] * sinf(theta);
  z_angle = inImage[2] * cosf(theta) - inImage[1] * sinf(theta);

  /* If within the acceptance angle. */
  /* If kfg is <0 then the pixel is outside of the key color. */
  kfg = x_angle - (fabsf(z_angle) / tanf(acceptance / 2.0f));

  if (kfg > 0.0f) { /* found a pixel that is within key color */
    alpha = 1.0f - (kfg / gain);

    beta = atan2(z_angle, x_angle);

    /* if beta is within the cutoff angle */
    if (fabsf(beta) < (cutoff / 2.0f)) {
      alpha = 0.0f;
    }

    /* don't make something that was more transparent less transparent */
    if (alpha < inImage[3]) {
      output[0] = alpha;
    }
    else {
      output[0] = inImage[3];
    }
  }
  else {                    /* Pixel is outside key color. */
    output[0] = inImage[3]; /* Make pixel just as transparent as it was before. */
  }
}

void ChromaMatteOperation::update_memory_buffer_partial(MemoryBuffer *output,
                                                        const rcti &area,
                                                        Span<MemoryBuffer *> inputs)
{
  const float acceptance = this->m_settings->t1; /* In radians. */
  const float cutoff = this->m_settings->t2;     /* In radians. */
  const float gain = this->m_settings->fstrength;
  for (BuffersIterator<float> it = output->iterate_with(inputs, area); !it.is_end(); ++it) {
    const float *in_image = it.in(0);
    const float *in_key = it.in(1);

    /* Store matte(alpha) value in [0] to go with
     * #COM_SetAlphaMultiplyOperation and the Value output. */

    /* Algorithm from book "Video Demystified", does not include the spill reduction part. */
    /* Find theta, the angle that the color space should be rotated based on key. */

    /* Rescale to `-1.0..1.0`. */
    // const float image_Y = (in_image[0] * 2.0f) - 1.0f;  // UNUSED
    const float image_cb = (in_image[1] * 2.0f) - 1.0f;
    const float image_cr = (in_image[2] * 2.0f) - 1.0f;

    // const float key_Y = (in_key[0] * 2.0f) - 1.0f;  // UNUSED
    const float key_cb = (in_key[1] * 2.0f) - 1.0f;
    const float key_cr = (in_key[2] * 2.0f) - 1.0f;

    const float theta = atan2(key_cr, key_cb);

    /* Rotate the cb and cr into x/z space. */
    const float x_angle = image_cb * cosf(theta) + image_cr * sinf(theta);
    const float z_angle = image_cr * cosf(theta) - image_cb * sinf(theta);

    /* If within the acceptance angle. */
    /* If kfg is <0 then the pixel is outside of the key color. */
    const float kfg = x_angle - (fabsf(z_angle) / tanf(acceptance / 2.0f));

    if (kfg > 0.0f) { /* Found a pixel that is within key color. */
      const float beta = atan2(z_angle, x_angle);
      float alpha = 1.0f - (kfg / gain);

      /* Ff beta is within the cutoff angle. */
      if (fabsf(beta) < (cutoff / 2.0f)) {
        alpha = 0.0f;
      }

      /* Don't make something that was more transparent less transparent. */
      it.out[0] = alpha < in_image[3] ? alpha : in_image[3];
    }
    else {                     /* Pixel is outside key color. */
      it.out[0] = in_image[3]; /* Make pixel just as transparent as it was before. */
    }
  }
}

}  // namespace blender::compositor
