/* DNA_linestyle_types.h
 *
 * $Id$
 *
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
 * The Original Code is Copyright (C) 2010 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef DNA_LINESTYLE_TYPES_H
#define DNA_LINESTYLE_TYPES_H

#include "DNA_listBase.h"
#include "DNA_ID.h"

struct ColorBand;
struct CurveMapping;

typedef struct LineStyleModifier {
	struct LineStyleModifier *next, *prev;

	char name[32];
	int type;
	float influence;
	int flags;
	int pad;
} LineStyleModifier;

/* LineStyleModifier::type */
#define LS_MODIFIER_ALONG_STROKE            1
#define LS_MODIFIER_DISTANCE_FROM_CAMERA    2
#define LS_MODIFIER_DISTANCE_FROM_OBJECT    3
#define LS_MODIFIER_MATERIAL                4
#define LS_MODIFIER_NUM                     5

/* LineStyleModifier::flags */
#define LS_MODIFIER_ENABLED     1
#define LS_MODIFIER_EXPANDED    2

/* flags (for color) */
#define LS_MODIFIER_USE_RAMP  1

/* flags (for alpha & thickness) */
#define LS_MODIFIER_USE_CURVE    1
#define LS_MODIFIER_INVERT       2

/* blend (for alpha & thickness) */
#define LS_VALUE_BLEND  0
#define LS_VALUE_ADD    1
#define LS_VALUE_MULT   2
#define LS_VALUE_SUB    3
#define LS_VALUE_DIV    4
#define LS_VALUE_DIFF   5
#define LS_VALUE_MIN    6
#define LS_VALUE_MAX    7

/* Along Stroke modifiers */

typedef struct LineStyleColorModifier_AlongStroke {
	struct LineStyleModifier modifier;

	struct ColorBand *color_ramp;
	int blend;
	int pad;

} LineStyleColorModifier_AlongStroke;

typedef struct LineStyleAlphaModifier_AlongStroke {
	struct LineStyleModifier modifier;

	struct CurveMapping	*curve;
	int blend;
	int flags;

} LineStyleAlphaModifier_AlongStroke;

typedef struct LineStyleThicknessModifier_AlongStroke {
	struct LineStyleModifier modifier;

	struct CurveMapping	*curve;
	int blend;
	int flags;
	float value_min, value_max;

} LineStyleThicknessModifier_AlongStroke;

/* Distance from Camera modifiers */

typedef struct LineStyleColorModifier_DistanceFromCamera {
	struct LineStyleModifier modifier;

	struct ColorBand *color_ramp;
	int blend;
	float range_min, range_max;
	int pad;

} LineStyleColorModifier_DistanceFromCamera;

typedef struct LineStyleAlphaModifier_DistanceFromCamera {
	struct LineStyleModifier modifier;

	struct CurveMapping	*curve;
	int blend;
	int flags;
	float range_min, range_max;

} LineStyleAlphaModifier_DistanceFromCamera;

typedef struct LineStyleThicknessModifier_DistanceFromCamera {
	struct LineStyleModifier modifier;

	struct CurveMapping	*curve;
	int blend;
	int flags;
	float range_min, range_max;
	float value_min, value_max;

} LineStyleThicknessModifier_DistanceFromCamera;

/* Distance from Object modifiers */

typedef struct LineStyleColorModifier_DistanceFromObject {
	struct LineStyleModifier modifier;

	struct Object *target;
	struct ColorBand *color_ramp;
	int blend;
	float range_min, range_max;
	int pad;

} LineStyleColorModifier_DistanceFromObject;

typedef struct LineStyleAlphaModifier_DistanceFromObject {
	struct LineStyleModifier modifier;

	struct Object *target;
	struct CurveMapping	*curve;
	int blend;
	int flags;
	float range_min, range_max;

} LineStyleAlphaModifier_DistanceFromObject;

typedef struct LineStyleThicknessModifier_DistanceFromObject {
	struct LineStyleModifier modifier;

	struct Object *target;
	struct CurveMapping	*curve;
	int blend;
	int flags;
	float range_min, range_max;
	float value_min, value_max;

} LineStyleThicknessModifier_DistanceFromObject;

/* Material modifiers */

/* mat_attr */
#define LS_MODIFIER_MATERIAL_DIFF       1
#define LS_MODIFIER_MATERIAL_DIFF_R     2
#define LS_MODIFIER_MATERIAL_DIFF_G     3
#define LS_MODIFIER_MATERIAL_DIFF_B     4
#define LS_MODIFIER_MATERIAL_SPEC       5
#define LS_MODIFIER_MATERIAL_SPEC_R     6
#define LS_MODIFIER_MATERIAL_SPEC_G     7
#define LS_MODIFIER_MATERIAL_SPEC_B     8
#define LS_MODIFIER_MATERIAL_SPEC_HARD  9
#define LS_MODIFIER_MATERIAL_ALPHA      10

typedef struct LineStyleColorModifier_Material {
	struct LineStyleModifier modifier;

	struct ColorBand *color_ramp;
	int blend;
	int flags;
	int mat_attr;
	int pad;

} LineStyleColorModifier_Material;

typedef struct LineStyleAlphaModifier_Material {
	struct LineStyleModifier modifier;

	struct CurveMapping	*curve;
	int blend;
	int flags;
	int mat_attr;
	int pad;

} LineStyleAlphaModifier_Material;

typedef struct LineStyleThicknessModifier_Material {
	struct LineStyleModifier modifier;

	struct CurveMapping	*curve;
	int blend;
	int flags;
	float value_min, value_max;
	int mat_attr;
	int pad;

} LineStyleThicknessModifier_Material;

/* FreestyleLineStyle::panel */
#define LS_PANEL_COLOR        1
#define LS_PANEL_ALPHA        2
#define LS_PANEL_THICKNESS    3
#define LS_PANEL_STROKES      4
#define LS_PANEL_DISTORT      5
#define LS_PANEL_MISC         6

/* FreestyleLineStyle::flag */
#define LS_DS_EXPAND          1  /* for animation editors */
#define LS_SAME_OBJECT        2
#define LS_DASHED_LINE        4
#define LS_MATERIAL_BOUNDARY  8

/* FreestyleLineStyle::caps */
#define LS_CAPS_BUTT    1
#define LS_CAPS_ROUND   2
#define LS_CAPS_SQUARE  3

typedef struct FreestyleLineStyle {
	ID id;
	struct AnimData *adt;

	float r, g, b, alpha;
	float thickness;
	int flag, caps;
	unsigned short dash1, gap1, dash2, gap2, dash3, gap3;
	int panel; /* for UI */
	int pad1;

	ListBase color_modifiers;
	ListBase alpha_modifiers;
	ListBase thickness_modifiers;

} FreestyleLineStyle;

#endif
