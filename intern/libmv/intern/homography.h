/* SPDX-FileCopyrightText: 2011 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#ifndef LIBMV_C_API_HOMOGRAPHY_H_
#define LIBMV_C_API_HOMOGRAPHY_H_

#ifdef __cplusplus
extern "C" {
#endif

void libmv_homography2DFromCorrespondencesEuc(/* const */ double (*x1)[2],
                                              /* const */ double (*x2)[2],
                                              int num_points,
                                              double H[3][3]);

#ifdef __cplusplus
}
#endif

#endif  // LIBMV_C_API_HOMOGRAPHY_H_
