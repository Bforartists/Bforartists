/*
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
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
 * The Original Code is Copyright (C) 2006 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */
#ifndef __BKE_COLORTOOLS_H__
#define __BKE_COLORTOOLS_H__

/** \file BKE_colortools.h
 *  \ingroup bke
 */

struct CurveMapping;
struct CurveMap;
struct CurveMapPoint;
struct Scopes;
struct Histogram;
struct ImBuf;
struct rctf;

#if defined _WIN32
#   define DO_INLINE __inline
#elif defined(__sun) || defined(__sun__)
#   define DO_INLINE
#else
#   define DO_INLINE static inline
#endif

void                curvemapping_set_defaults(struct CurveMapping *cumap, int tot, float minx, float miny, float maxx, float maxy);
struct CurveMapping *curvemapping_add(int tot, float minx, float miny, float maxx, float maxy);
void                curvemapping_free_data(struct CurveMapping *cumap);
void                curvemapping_free(struct CurveMapping *cumap);
void                curvemapping_copy_data(struct CurveMapping *target, struct CurveMapping *cumap);
struct CurveMapping *curvemapping_copy(struct CurveMapping *cumap);
void                curvemapping_set_black_white_ex(const float black[3], const float white[3], float r_bwmul[3]);
void                curvemapping_set_black_white(struct CurveMapping *cumap, const float black[3], const float white[3]);

#define CURVEMAP_SLOPE_NEGATIVE 0
#define CURVEMAP_SLOPE_POSITIVE 1
void                    curvemap_reset(struct CurveMap *cuma, struct rctf *clipr, int preset, int slope);
void                    curvemap_remove(struct CurveMap *cuma, const short flag);
void                    curvemap_remove_point(struct CurveMap *cuma, struct CurveMapPoint *cmp);
struct CurveMapPoint    *curvemap_insert(struct CurveMap *cuma, float x, float y);
void                    curvemap_sethandle(struct CurveMap *cuma, int type);

void                curvemapping_changed(struct CurveMapping *cumap, int rem_doubles);
void                curvemapping_changed_all(struct CurveMapping *cumap);

/* call before _all_ evaluation functions */
void                curvemapping_initialize(struct CurveMapping *cumap);

/* keep these (const CurveMap) - to help with thread safety */
/* single curve, no table check */
float               curvemap_evaluateF(const struct CurveMap *cuma, float value);
/* single curve, with table check */
float               curvemapping_evaluateF(const struct CurveMapping *cumap, int cur, float value);
void                curvemapping_evaluate3F(const struct CurveMapping *cumap, float vecout[3], const float vecin[3]);
void                curvemapping_evaluateRGBF(const struct CurveMapping *cumap, float vecout[3], const float vecin[3]);
void                curvemapping_evaluate_premulRGB(const struct CurveMapping *cumap, unsigned char vecout_byte[3], const unsigned char vecin_byte[3]);
void                curvemapping_evaluate_premulRGBF_ex(const struct CurveMapping *cumap, float vecout[3], const float vecin[3],
                                                        const float black[3], const float bwmul[3]);
void                curvemapping_evaluate_premulRGBF(const struct CurveMapping *cumap, float vecout[3], const float vecin[3]);
int                 curvemapping_RGBA_does_something(const struct CurveMapping *cumap);
void                curvemapping_table_RGBA(const struct CurveMapping *cumap, float **array, int *size);

/* non-const, these modify the curve */
void                curvemapping_do_ibuf(struct CurveMapping *cumap, struct ImBuf *ibuf);
void                curvemapping_premultiply(struct CurveMapping *cumap, int restore);


void                BKE_histogram_update_sample_line(struct Histogram *hist, struct ImBuf *ibuf, const short use_color_management);
void                scopes_update(struct Scopes *scopes, struct ImBuf *ibuf, int use_color_management);
void                scopes_free(struct Scopes *scopes);
void                scopes_new(struct Scopes *scopes);

#endif
