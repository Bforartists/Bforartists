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
 * Copyright 2022, Blender Foundation.
 */

/** \file
 * \ingroup draw_engine
 */

#pragma once

/**
 * ImageUsage contains data of the image and image user to identify changes that require a rebuild
 * of the texture slots.
 */
struct ImageUsage {
  /** Render pass of the image that is used. */
  short pass = 0;
  /** Layer of the image that is used.*/
  short layer = 0;
  /** View of the image that is used. */
  short view = 0;

  ImageUsage() = default;
  ImageUsage(const struct ImageUser *image_user)
  {
    pass = image_user ? image_user->pass : 0;
    layer = image_user ? image_user->layer : 0;
    view = image_user ? image_user->multi_index : 0;
  }

  bool operator==(const ImageUsage &other) const
  {
    return memcmp(this, &other, sizeof(ImageUsage)) == 0;
  }
  bool operator!=(const ImageUsage &other) const
  {
    return !(*this == other);
  }
};
