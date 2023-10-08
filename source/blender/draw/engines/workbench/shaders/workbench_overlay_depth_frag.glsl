/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/* Prepare the Depth Buffer for the Overlay Engine. */

void main()
{
  /* Set the depth to 0 for "In Front" objects,
   * so the Overlay engine doesn't draw on top of them. */
  gl_FragDepth = 0.0;
}
